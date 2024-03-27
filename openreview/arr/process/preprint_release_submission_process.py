def process(client, invitation):

    domain = client.get_group(invitation.domain)
    venue_id = domain.id
    submission_venue_id = domain.content['submission_venue_id']['value']
    venue_name = domain.content['title']['value']

    now = openreview.tools.datetime_millis(datetime.datetime.utcnow())
    cdate = invitation.cdate

    if cdate > now:
        ## invitation is in the future, do not process
        print('invitation is not yet active', cdate)
        return

    def post_submission_edit(submission):

        updated_note = openreview.api.Note(
            id=submission.id,
            odate = now,
            content = {
                '_bibtex': {
                    'value': openreview.tools.generate_bibtex(
                        note=submission,
                        venue_fullname=venue_name,
                        year=str(datetime.datetime.utcnow().year),
                        url_forum=submission.forum,
                        paper_status='under review',
                        anonymous=True
                    )
                }                
            }
        )

        client.post_note_edit(
            invitation=invitation.id,
            note=updated_note,
            signatures=[venue_id]
        )
    
    ## Release the submissions to the public when the value for preprint is yes
    submissions = [s for s in client.get_all_notes(content= { 'venueid': submission_venue_id }) if s.content.get('preprint', {}).get('value') == 'yes']
    print(f'update {len(submissions)} submissions')
    openreview.tools.concurrent_requests(post_submission_edit, submissions, desc='post_submission_edit')    