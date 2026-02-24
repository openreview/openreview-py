def process(client, invitation):

    domain = client.get_group(invitation.domain)
    venue_id = domain.id

    submission_venue_id = domain.content['submission_venue_id']['value']
    support_user = domain.content['request_form_invitation']['value'].split('/Venue_Request')[0]
    status_invitation_id = domain.get_content_value('status_invitation_id')
    request_form_id = domain.get_content_value('request_form_id')

    now = openreview.tools.datetime_millis(datetime.datetime.now())
    cdate = invitation.cdate

    if cdate > now:
        ## invitation is in the future, do not process
        print('invitation is not yet active', cdate)
        return

    def post_submission_edit(submission):

        client.post_note_edit(
            invitation=invitation.id,
            note=openreview.api.Note(
                id=submission.id
            ),
            signatures=[venue_id]
        )
    
    ## Release the submissions to specified readers if venueid is still submission
    submissions = client.get_all_notes(content= { 'venueid': submission_venue_id }, domain=venue_id)

    if not submissions:
        print('No submissions were updated since there are no active submissions')
        # post status to request form
        client.post_note_edit(
            invitation=status_invitation_id,
            signatures=[venue_id],
            readers=[venue_id, support_user],
            note=openreview.api.Note(
                forum=request_form_id,
                signatures=[venue_id],
                content={
                    'title': { 'value': f'{invitation.id.split("/-/")[-1].replace("_", " ")} Completed' },
                    'comment': { 'value': f'The process "{invitation.id.split("/-/")[-1].replace("_", " ")}" has successfully completed. No submissions were updated since there are no active submissions.' }
                }
            )
        )
        return

    print(f'update {len(submissions)} submissions')
    openreview.tools.concurrent_requests(post_submission_edit, submissions, desc='post_submission_edit')

    print(f'{len(submissions)} submissions updated successfully')

    comment = f'The process "{invitation.id.split("/-/")[-1].replace("_", " ")}" has successfully completed. {len(submissions)} submissions were updated.'

    # post status to request form
    client.post_note_edit(
        invitation=status_invitation_id,
        signatures=[venue_id],
        readers=[venue_id, support_user],
        note=openreview.api.Note(
            forum=request_form_id,
            signatures=[venue_id],
            content={
                'title': { 'value': f'{invitation.id.split("/-/")[-1].replace("_", " ")} Completed' },
                'comment': { 'value': comment }
            }
        )
    )