def process(client, edit, invitation):

    journal = openreview.journal.Journal()

    venue_id = journal.venue_id

    submission = client.get_note(edit.note.forum)

    return client.post_note_edit(invitation= journal.get_desk_rejected_id(),
                            signatures=[venue_id],
                            note=openreview.api.Note(id=submission.id
    ))