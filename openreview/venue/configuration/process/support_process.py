def process(client, edit, invitation):

    note = client.get_note(edit.note.id)
    print(note.forum)

    # post deploy invitation
    inv = client.post_invitation_edit(
        invitations='openreview.net/-/Deploy',
        signatures=['openreview.net/Support'],
        content = {
            'noteNumber': { 'value': note.number},
            'noteId': { 'value': note.id }
        }
    )
    print(inv['invitation']['id'])

    # post comment invitation
    inv = client.post_invitation_edit(
        invitations='openreview.net/-/Comment',
        signatures=['openreview.net/Support'],
        content = {
            'noteNumber': { 'value': note.number},
            'noteId': { 'value': note.id }
        }
    )
    print(inv['invitation']['id'])