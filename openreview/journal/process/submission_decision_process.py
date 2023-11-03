def process(client, edit, invitation):

    journal = openreview.journal.Journal()

    ## Notify readers
    journal.notify_readers(edit)

    note=client.get_note(edit.note.id)

    ## On update or delete return
    if note.tcdate != note.tmdate:
        return

    submission = client.get_note(note.forum)
    
    ## Update submission and set the decision submitted status
    client.post_note_edit(
        invitation = journal.get_meta_invitation_id(),
        readers = journal.get_under_review_submission_readers(submission.number),
        writers = [journal.venue_id],
        signatures = [journal.venue_id],
        note = openreview.api.Note(
            id = submission.id,
            content = {
                'venue': {
                    'value': f'Decision pending for {journal.short_name}'
                },
                'venueid': {
                    'value': journal.decision_pending_venue_id
                }
            }

        )

    )
    
    journal.invitation_builder.set_note_decision_approval_invitation(submission, note, journal.get_due_date(days = 7))
