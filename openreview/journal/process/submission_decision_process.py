def process(client, edit, invitation):

    journal = openreview.journal.Journal()

    ## Notify readers
    journal.notify_readers(edit)

    note=edit.note

    ## On update or delete return
    if note.tcdate != note.tmdate:
        return

    submission = client.get_note(note.forum)
    journal.invitation_builder.set_note_decision_approval_invitation(submission, note, journal.get_due_date(days = 7))
