def process(client, edit, invitation):

    journal = openreview.journal.Journal()

    note=edit.note

    duedate = openreview.tools.datetime_millis(datetime.datetime.utcnow() + datetime.timedelta(days = 7))
    submission = client.get_note(note.forum)
    journal.invitation_builder.set_decision_approval_invitation(journal, submission, note, duedate)
