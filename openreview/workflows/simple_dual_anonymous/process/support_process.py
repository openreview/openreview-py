def process(client, edit, invitation):

    note = client.get_note(edit.note.id)
    print(note.forum)

    # post deploy invitation
    inv = client.post_invitation_edit(
        invitations='openreview.net/Support/-/Deployment',
        signatures=['openreview.net/Support'],
        content = {
            'noteNumber': { 'value': note.number},
            'noteId': { 'value': note.id }
        }
    )