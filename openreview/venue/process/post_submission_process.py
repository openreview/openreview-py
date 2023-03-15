def process(client, invitation):

    domain = client.get_group(invitation.domain)
    venue_id = domain.id
    submission_venue_id = domain.content['submission_venue_id']['value']

    def post_submission_edit(submission):

        client.post_note_edit(
            invitation=invitation.id,
            note=openreview.api.Note(
                id=submission.id
            ),
            signatures=[venue_id]
        )
    
    ## Release the submissions to specified readers if venueid is still submission
    submissions = client.get_all_notes(content= { 'venueid': submission_venue_id })
    openreview.tools.concurrent_requests(post_submission_edit, submissions, desc='post_submission_edit')    