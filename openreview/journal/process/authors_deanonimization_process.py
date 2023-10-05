def process(client, edit, invitation):

    journal = openreview.journal.Journal()
    venue_id = journal.venue_id

    ## On update or delete return
    note = client.get_note(edit.note.id)
    if note.tcdate != note.tmdate:
        return

    submission = client.get_note(note.forum)

    print('Release authors')

    release_note = client.post_note_edit(invitation=journal.get_authors_release_id(),
                        signatures=[venue_id],
                        note=openreview.api.Note(id=submission.id,
                            content={
                                '_bibtex': {
                                    'value': journal.get_bibtex(submission, submission.content.get('venueid', {}).get('value'), anonymous=False)
                                }
                            }
                        )
                    )