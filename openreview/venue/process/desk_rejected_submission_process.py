def process(client, edit, invitation):

    VENUE_ID = ''
    SHORT_NAME = ''
    PAPER_INVITATION_PREFIX = ''
    EXPIRE_INVITATION_ID = ''
    COMMITTEE = []

    submission = client.get_note(edit.note.id)

    invitations = client.get_invitations(replyForum=submission.id, prefix=PAPER_INVITATION_PREFIX)

    now = openreview.tools.datetime_millis(datetime.datetime.utcnow())

    for invitation in invitations:
        print(f'Expiring invitation {invitation.id}')
        client.post_invitation_edit(
            invitations=EXPIRE_INVITATION_ID,
            invitation=openreview.api.Invitation(id=invitation.id,
                expdate=now
            )
        )

    formatted_committee = [committee.format(number=submission.number) for committee in COMMITTEE]
    email_subject = f'''[{SHORT_NAME}]: Paper #{submission.number} desk-rejected by program chairs'''
    email_body = f'''The {SHORT_NAME} paper "{submission.content.get('title', {}).get('value', '#'+str(submission.number))}" has been desk-rejected by the program chairs.

For more information, click here https://openreview.net/forum?id={submission.id}
'''

    client.post_message(email_subject, formatted_committee, email_body)

    desk_rejection_notes = client.get_notes(forum=submission.id, invitation=PAPER_INVITATION_PREFIX + f'{submission.number}/-/Desk_Rejection')
    if desk_rejection_notes:
        print(f'Create desk-rejection reversion invitation')
        client.post_invitation_edit(
            invitations=VENUE_ID + '/-/Desk_Rejection_Reversion',
            content={
                'noteId': {
                    'value': submission.id
                },
                'deskRejectionId': {
                    'value': desk_rejection_notes[0].id
                }
            }
        )