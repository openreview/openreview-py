def process(client, invitation):
    VENUE_ID = ''
    SUBMISSION_ID = ''

    def post_invitation(note):
        return client.post_invitation_edit(invitations=invitation.id,
            readers=[VENUE_ID],
            writers=[VENUE_ID],
            signatures=[VENUE_ID],
            content={
                'noteId': {
                    'value': note.id
                },
                'noteNumber': {
                    'value': note.number
                }
            },
            invitation=openreview.api.Invitation()
        )

    notes = client.get_all_notes(invitation=SUBMISSION_ID, sort='number:asc')
    invitations = openreview.tools.concurrent_requests(post_invitation, notes, desc='invitation_start_process')        
