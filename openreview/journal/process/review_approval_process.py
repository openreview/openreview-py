def process(client, edit, invitation):

    journal = openreview.journal.Journal()
    venue_id = journal.venue_id

    if edit.note.content['under_review']['value'] == 'Appropriate for review':
        return client.post_note_edit(invitation= journal.get_under_review_id(),
                                signatures=[venue_id],
                                note=openreview.api.Note(id=edit.note.forum))

    if edit.note.content['under_review']['value'] == 'Desk Reject':
        client.post_note_edit(invitation= journal.get_desk_rejection_id(),
                                signatures=[venue_id],
                                note=openreview.api.Note(id=edit.note.forum))