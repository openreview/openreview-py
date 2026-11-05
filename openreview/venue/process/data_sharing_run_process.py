def process(client, edit, invitation):

    SUPPORT_GROUP = ''
    GROUP_ID = ''

    import os
    import datetime
    import tempfile

    def get_venue_info(venue_id):
        venue_group = client.get_group(venue_id)
        short_name = venue_group.content.get('subtitle', {}).get('value') or venue_id
        program_chairs_id = venue_group.content.get('program_chairs_id', {}).get('value', f'{venue_id}/Program_Chairs')
        return short_name, program_chairs_id

    def get_submission_venue_ids(venue, statuses):
        ## each status is a venue id of the domain group, e.g. withdrawn submissions have the withdrawn venue id
        content = client.get_group(venue.venue_id).content
        venue_ids_by_status = {
            'Active': content.get('submission_venue_id', {}).get('value'),
            'Accepted': venue.venue_id,
            'Rejected': content.get('rejected_venue_id', {}).get('value'),
            'Withdrawn': content.get('withdrawn_venue_id', {}).get('value'),
            'Desk Rejected': content.get('desk_rejected_venue_id', {}).get('value')
        }
        ## the API matches any of comma separated values, and the expertise service queries the notes with it
        venue_ids = ','.join([venue_ids_by_status[status] for status in statuses if venue_ids_by_status.get(status)])
        print(f'{venue.short_name}: submissions with venue ids {venue_ids}')
        return venue_ids

    def post_message(recipients, subject, message):
        client.post_message(subject=subject, recipients=recipients, message=message, invitation=f'{SUPPORT_GROUP}/-/Edit', signature=SUPPORT_GROUP)

    def post_status(status, status_message=None):
        client.post_note_edit(
            invitation=f'{SUPPORT_GROUP}/-/Edit',
            readers=[SUPPORT_GROUP],
            writers=[SUPPORT_GROUP],
            signatures=[SUPPORT_GROUP],
            note=openreview.api.Note(
                id=request.id,
                content={
                    'status': { 'value': status },
                    ## remove the message of a previous failed run
                    'status_message': { 'value': status_message, 'readers': [SUPPORT_GROUP] } if status_message else { 'delete': True }
                }
            )
        )

    ## this process runs as the super user, so it can read the submissions of both venues
    request = client.get_note(edit.note.id)
    job_id = edit.note.content.get('job_id', {}).get('value')
    venue_id = request.content['venue_id']['value']
    alternate_venue_id = request.content['alternate_venue_id']['value']
    top_percent_cutoff = request.content['top_percent_cutoff']['value']
    author_overlap_only = request.content['author_overlap_only']['value']
    forum_url = f'{openreview.tools.get_site_url(client)}/forum?id={request.id}'

    ## used in the failure email when the venue lookups fail
    short_name = venue_id
    alternate_short_name = alternate_venue_id

    try:
        short_name, program_chairs_id = get_venue_info(venue_id)
        alternate_short_name, alternate_program_chairs_id = get_venue_info(alternate_venue_id)

        ## the other venue chooses its submissions and its results recipients when it approves
        approvals = client.get_notes(invitation=f'{GROUP_ID}/Dual_Submission_Check{request.number}/-/Approval')
        if not approvals or approvals[0].content['status']['value'] != 'Approved':
            raise openreview.OpenReviewException(f'{alternate_short_name} has not approved the request.')
        approval = approvals[0]

        recipients = request.content.get('results_recipients', {}).get('value')
        alternate_recipients = approval.content.get('results_recipients', {}).get('value')
        ## without recipients, the results are shared with all the program chairs of the venue
        results_readers = [SUPPORT_GROUP] + (recipients or [venue_id]) + (alternate_recipients or [alternate_venue_id])
        results_emails = [SUPPORT_GROUP] + (recipients or [program_chairs_id]) + (alternate_recipients or [alternate_program_chairs_id])

        ## the approval can not change once the data is being shared
        client.post_invitation_edit(
            invitations=f'{SUPPORT_GROUP}/-/Edit',
            readers=[SUPPORT_GROUP],
            writers=[SUPPORT_GROUP],
            signatures=[SUPPORT_GROUP],
            invitation=openreview.api.Invitation(
                id=f'{GROUP_ID}/Dual_Submission_Check{request.number}/-/Approval',
                expdate=openreview.tools.datetime_millis(datetime.datetime.now())
            )
        )

        venue = openreview.venue.helpers.get_venue(client, venue_id, support_user=SUPPORT_GROUP)
        alternate_venue = openreview.venue.helpers.get_venue(client, alternate_venue_id, support_user=SUPPORT_GROUP)

        venue_ids = get_submission_venue_ids(venue, request.content.get('submission_statuses', {}).get('value') or ['Active'])
        alternate_venue_ids = get_submission_venue_ids(alternate_venue, approval.content.get('submission_statuses', {}).get('value') or ['Active'])

        post_message(
            recipients=[program_chairs_id, alternate_program_chairs_id],
            subject=f'Dual submission check started: {short_name} and {alternate_short_name}',
            message=f'''The OpenReview support team started the dual submission check between {short_name} and {alternate_short_name}.

Computing the similarity between the submissions of both venues can take several hours. The results recipients of both venues will receive another email when the results are available.

You can view the request here: {forum_url}

The OpenReview Team'''
        )

        if not job_id:
            ## compute_dual_submission_metadata only compares the active submissions, so start the job with the selected ones
            job = client.request_paper_similarity(
                name=f'{venue.short_name}--{alternate_venue.short_name}-Paper-Similarity',
                venue_id=venue_ids,
                alternate_venue_id=alternate_venue_ids,
                model='specter2+scincl',
                sparse_value=5
            )
            job_id = job['jobId']
            print('Similarity job id:', job_id)
            ## keep the job id so a failed run can be retried without computing the scores again
            client.post_note_edit(
                invitation=f'{SUPPORT_GROUP}/-/Edit',
                readers=[SUPPORT_GROUP],
                writers=[SUPPORT_GROUP],
                signatures=[SUPPORT_GROUP],
                note=openreview.api.Note(
                    id=request.id,
                    content={
                        'job_id': { 'value': job_id, 'readers': [SUPPORT_GROUP] }
                    }
                )
            )

        results_invitation_id = f'{GROUP_ID}/Dual_Submission_Check{request.number}/-/Results'
        with tempfile.TemporaryDirectory() as output_dir:
            venue.compute_dual_submission_metadata(
                alternate_venue,
                output_dir,
                top_percent_cutoff=top_percent_cutoff,
                job_id=job_id,
                author_overlap_only=author_overlap_only
            )
            ## the output directory only contains the CSV file
            csv_path = os.path.join(output_dir, os.listdir(output_dir)[0])
            ## only users with a profile can upload files and the token of a process function
            ## has none, impersonating the support group gives a token with a profile
            upload_client = openreview.api.OpenReviewClient(baseurl=client.baseurl, token=client.token)
            upload_client.impersonate(SUPPORT_GROUP)
            results_url = upload_client.put_attachment(csv_path, results_invitation_id, 'results')

        results_edit = client.post_note_edit(
            invitation=results_invitation_id,
            signatures=[SUPPORT_GROUP],
            note=openreview.api.Note(
                readers=results_readers,
                content={
                    'results': { 'value': results_url }
                }
            )
        )
        post_status('Completed')

    except Exception as e:
        post_status('Failed', status_message=repr(e))
        post_message(
            recipients=[SUPPORT_GROUP],
            subject=f'Dual submission check failed: {short_name} and {alternate_short_name}',
            message=f'''The dual submission check between {short_name} and {alternate_short_name} failed with the following error:

{repr(e)}

Check the process logs of the request, then run it again: {forum_url}'''
        )
        raise e

    post_message(
        recipients=results_emails,
        subject=f'Dual submission check completed: {short_name} and {alternate_short_name}',
        message=f'''The dual submission check between {short_name} and {alternate_short_name} has completed.

You can download the results here: {forum_url}&noteId={results_edit['note']['id']}

The OpenReview Team'''
    )
