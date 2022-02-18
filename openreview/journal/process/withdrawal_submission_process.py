def process(client, edit, invitation):

    journal = openreview.journal.Journal()

    venue_id = journal.venue_id

    submission = client.get_note(edit.note.forum)

    return client.post_note_edit(invitation= journal.get_withdrawn_id(),
                            signatures=[venue_id],
                            note=openreview.api.Note(id=submission.id,
                            content= {
                                '_bibtex': {
                                    'value': journal.get_bibtex(submission, journal.withdrawn_venue_id, anonymous=True)
                                }
                            }
    ))