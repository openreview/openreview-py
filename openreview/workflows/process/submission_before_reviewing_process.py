def process(client, invitation):

    domain = client.get_group(invitation.domain)
    venue_id = domain.id

    submission_venue_id = domain.content['submission_venue_id']['value']
    venue_name = domain.content['title']['value']

    now = openreview.tools.datetime_millis(datetime.datetime.now())
    cdate = invitation.cdate

    if cdate > now:
        ## invitation is in the future, do not process
        print('invitation is not yet active', cdate)
        return

    def edit_submission(submission):

        updated_note = openreview.api.Note(
            id=submission.id
        )

        if invitation.edit['note']['readers'] == ['everyone'] and submission.odate is None:
            updated_note.odate = now

        client.post_note_edit(
            invitation=invitation.id,
            note=updated_note,
            signatures=[venue_id]
        )
    
    ## Release the submissions to specified readers if venueid is still submission
    submissions = client.get_all_notes(content= { 'venueid': submission_venue_id })

    if not submissions:
        print('No submissions were updated since there are no active submissions')
        return
    
    print(f'update {len(submissions)} submissions')
    openreview.tools.concurrent_requests(edit_submission, submissions, desc='post_submission_edit')

    print(f'{len(submissions)} submissions updated successfully')