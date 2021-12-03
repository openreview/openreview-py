def process(client, edit, invitation):

    journal = openreview.journal.Journal()

    venue_id = journal.venue_id

    return client.post_note_edit(invitation= journal.get_withdrawn_id(),
                            signatures=[venue_id],
                            note=openreview.api.Note(id=edit.note.forum))