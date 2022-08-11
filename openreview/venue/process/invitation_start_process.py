def process(client, invitation):
    VENUE_ID = ''
    SUBMISSION_ID = ''
    for submission in client.get_all_notes(invitation=SUBMISSION_ID, sort='number:asc'):
        client.post_invitation_edit(invitations=invitation.id,
            readers=[VENUE_ID],
            writers=[VENUE_ID],
            signatures=[VENUE_ID],
            content={
                'noteId': {
                    'value': submission.id
                },
                'noteNumber': {
                    'value': submission.number
                }
            },
            invitation=openreview.api.Invitation()
        )
