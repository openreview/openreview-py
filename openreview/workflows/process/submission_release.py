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

    def get_all_notes():
        submissions = client.get_all_notes(content={ 'venueid': submission_venue_id }, sort='number:asc', details='directReplies')
        if not submissions:
            submissions = client.get_all_notes(content={ 'venueid': ','.join([venue_id, rejected_venue_id]) }, sort='number:asc', details='directReplies')

        return submissions

    def get_source_submission_tuples(all_submissions):
        source = invitation.content.get('source', {}).get('value', 'all_submissions') if invitation.content else False

        if source == 'all_submissions':
            source_submissions = [(submission, openreview.api.Note.from_json(reply)) for submission in all_submissions for reply in submission.details['directReplies'] if f'{venue_id}/{submission_name}{submission.number}/-/{decision_name}' in reply['invitations']]
        elif source == 'accepted_submissions':
            source_submissions = [(submission, openreview.api.Note.from_json(reply)) for submission in all_submissions for reply in submission.details['directReplies'] if f'{venue_id}/{submission_name}{submission.number}/-/{decision_name}' in reply['invitations'] and openreview.tools.is_accept_decision(reply['content'][decision_field_name]['value'], accept_options)]
        return source_submissions


    def edit_submission(submission_tuple):
        submission, decision = submission_tuple
        note_accepted = decision and openreview.tools.is_accept_decision(decision.content[decision_field_name]['value'], accept_options)

        updated_note = openreview.api.Note(
            id=submission.id,
            content={
                'authors': {
                    'readers': { 'delete': True }
                },
                'authorids': {
                    'readers': { 'delete': True }
                }
            }
        )

        if submission.odate is None:
            updated_note.odate = now
        # only if note is accepted
        if submission.pdate is None and note_accepted:
            updated_note.pdate = now

        client.post_note_edit(
            invitation=invitation.id,
            note=updated_note,
            signatures=[venue_id]
        )
    
    ## Release the submissions to specified readers if venueid is still submission
    submissions = get_all_notes()
    source_submissions = get_source_submission_tuples(submissions)

    if not source_submissions:
        print('No submissions were updated since there are no active submissions')
        return
    
    print(f'update {len(submissions)} submissions')
    openreview.tools.concurrent_requests(edit_submission, source_submissions, desc='post_submission_edit')

    print(f'{len(source_submissions)} submissions updated successfully')