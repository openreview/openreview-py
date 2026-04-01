def process(client, invitation):

    domain = client.get_group(invitation.domain)
    venue_id = domain.id
    submission_id = domain.content['submission_id']['value']
    submission_name = domain.content['submission_name']['value']
    venue_name = domain.content['title']['value']

    now = openreview.tools.datetime_millis(datetime.datetime.now())
    cdate = invitation.cdate

    if cdate > now:
        ## invitation is in the future, do not process
        print('invitation is not yet active', cdate)
        return

    def post_submission_edit(submission):

        updated_note = openreview.api.Note(
            id=submission.id
        )

        if invitation.edit['note']['readers'] == ['everyone'] and submission.odate is None:
            updated_note.odate = now
            updated_note.content = {
                '_bibtex': {
                    'value': openreview.tools.generate_bibtex(
                        note=submission,
                        venue_fullname=venue_name,
                        year=str(datetime.datetime.now().year),
                        url_forum=submission.forum,
                        paper_status='under review',
                        anonymous='readers' in submission.content['authors'] or 'readers' in invitation.edit.get('note', {}).get('content', {}).get('authors', {})
                    )
                }
            }

        client.post_note_edit(
            invitation=invitation.id,
            note=updated_note,
            signatures=[venue_id]
        )
    
    ## Release the submissions to specified readers if venueid is still submission
    all_submissions = client.get_all_notes(invitation=submission_id, sort='number:asc', domain=venue_id)

    filtered_submissions = [paper for paper in all_submissions if openreview.tools.should_match_invitation_source(client, invitation, paper, domain=domain)]

    if not filtered_submissions:
        print('No submissions were updated since there are no active submissions')
        return

    print(f'update {len(filtered_submissions)} submissions')
    openreview.tools.concurrent_requests(post_submission_edit, filtered_submissions, desc='post_submission_edit')

    print(f'{len(filtered_submissions)} submissions updated successfully')