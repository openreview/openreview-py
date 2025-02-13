def process(client, edit, invitation):

    support_user = f'{invitation.domain}/Support'

    note = client.get_note(edit.note.id)
    print(note.forum)

    # post deploy invitation
    inv = client.post_invitation_edit(
        invitations=f'{support_user}/-/Deployment',
        signatures=[support_user],
        content = {
            'noteNumber': { 'value': note.number},
            'noteId': { 'value': note.id }
        }
    )

    # post comment invitation
    inv = client.post_invitation_edit(
        invitations=f'{support_user}/Venue_Configuration_Request/-/Comment',
        signatures=[support_user],
        content = {
            'noteNumber': { 'value': note.number},
            'noteId': { 'value': note.id }
        }
    )