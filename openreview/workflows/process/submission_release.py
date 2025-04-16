def process(client, invitation):

    domain = client.get_group(invitation.domain)
    venue_id = domain.id

    submission_venue_id = domain.content['submission_venue_id']['value']
    submission_name = domain.content['submission_name']['value']
    decision_name = domain.content.get('decision_name', {}).get('value')
    rejected_venue_id = domain.content['rejected_venue_id']['value']
    decision_field_name = domain.content.get('decision_field_name', {}).get('value', 'decision')
    accept_options = domain.content.get('accept_decision_options', {}).get('value')

    now = openreview.tools.datetime_millis(datetime.datetime.now())
    cdate = invitation.cdate

    if cdate > now:
        ## invitation is in the future, do not process
        print('invitation is not yet active', cdate)
        return

    def get_notes():
        source = invitation.content.get('source', {}).get('value', 'all_submissions') if invitation.content else False

        if source == 'accepted_submissions':
            source_submissions = client.get_all_notes(content={ 'venueid': venue_id }, sort='number:asc', details='replies')
            if not source_submissions and decision_name:
                under_review_submissions = client.get_all_notes(content={ 'venueid': submission_venue_id }, sort='number:asc', details='replies')
                source_submissions = [s for s in under_review_submissions if len([r for r in s.details['replies'] if f'{venue_id}/{submission_name}{s.number}/-/{decision_name}' in r['invitations'] and openreview.tools.is_accept_decision(r['content'][decision_field_name]['value'], accept_options) ]) > 0]
        else:
            source_submissions = client.get_all_notes(content={ 'venueid': submission_venue_id }, sort='number:asc', details='replies')
            if not source_submissions:
                source_submissions = client.get_all_notes(content={ 'venueid': ','.join([venue_id, rejected_venue_id]) }, sort='number:asc', details='replies')

        return source_submissions

    def edit_submission(submission):

        updated_note = openreview.api.Note(
            id=submission.id
        )

        if submission.odate is None:
            updated_note.odate = now
        if submission.pdate is None:
            updated_note.pdate = now

        client.post_note_edit(
            invitation=invitation.id,
            note=updated_note,
            signatures=[venue_id]
        )
    
    ## Release the submissions to specified readers if venueid is still submission
    submissions = get_notes()

    if not submissions:
        print('No submissions were updated since there are no active submissions')
        return
    
    print(f'update {len(submissions)} submissions')
    openreview.tools.concurrent_requests(edit_submission, submissions, desc='post_submission_edit')

    print(f'{len(submissions)} submissions updated successfully')