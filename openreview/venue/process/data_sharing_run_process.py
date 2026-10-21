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

        post_message(
            recipients=[program_chairs_id, alternate_program_chairs_id],
            subject=f'Dual submission check started: {short_name} and {alternate_short_name}',
            message=f'''The OpenReview support team started the dual submission check between {short_name} and {alternate_short_name}.

Computing the similarity between the submissions of both venues can take several hours. You will receive another email when the results are available.

You can view the request here: {forum_url}

The OpenReview Team'''
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
        recipients=[program_chairs_id, alternate_program_chairs_id, SUPPORT_GROUP],
        subject=f'Dual submission check completed: {short_name} and {alternate_short_name}',
        message=f'''The dual submission check between {short_name} and {alternate_short_name} has completed.

You can download the results here: {forum_url}&noteId={results_edit['note']['id']}

The OpenReview Team'''
    )
