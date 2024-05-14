def process(client, edit, invitation):

    support_user = 'openreview.net/Support'

    note = client.get_note(edit.note.id)
    venue = openreview.helpers.get_venue(client, note.id, support_user)
    venue.create_submission_stage()
    venue.create_submission_edit_invitations()
    venue.create_review_edit_invitations()

    # remove PC access to editing the note
    client.post_note_edit(
        invitation=venue.get_meta_invitation_id(),
        signatures=[venue.id],
        note = openreview.api.Note(
            id = note.id,
            writers = []
        )
    )