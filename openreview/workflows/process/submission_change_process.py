def process(client, invitation):

    domain = client.get_group(invitation.domain)
    venue_id = domain.id

    submission_venue_id = domain.content['submission_venue_id']['value']
    venue = openreview.helpers.get_venue(client, venue_id)
    venue_name = domain.content['title']['value']

    now = openreview.tools.datetime_millis(datetime.datetime.now())
    cdate = invitation.cdate

    if cdate > now:
        ## invitation is in the future, do not process
        print('invitation is not yet active', cdate)
        return

    def post_submission_edit(submission):
        # if submission matches invitation source, update submission
        if openreview.tools.should_match_invitation_source(client, invitation, submission):
            print(f'posting edit for submission {submission.id}, number {submission.number}')
            note_edit = client.post_note_edit(
                invitation=invitation.id,
                note=openreview.api.Note(
                    id=submission.id
                ),
                signatures=[venue_id]
            )
            return note_edit

    
    ## Release the submissions to specified readers if venueid is still submission
    source = openreview.tools.get_invitation_source(invitation, domain)
    print('source', source)
    venue_ids = source.get('venueid', [submission_venue_id])
    submissions = client.get_all_notes(content= { 'venueid': ','.join([venue_ids] if isinstance(venue_ids, str) else venue_ids)}, sort='number:asc', domain=venue_id)

    if not submissions:
        print('No submissions were updated since there are no active submissions')
        return

    print(f'update {len(submissions)} submissions')
    all_edits = openreview.tools.concurrent_requests(post_submission_edit, submissions, desc='post_submission_edit')

    print(f'{len(all_edits)} submissions updated successfully')