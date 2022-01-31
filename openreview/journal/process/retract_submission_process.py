def process(client, edit, invitation):

    journal = openreview.journal.Journal()

    note = edit.note

    submission = client.get_note(edit.note.forum)

    journal.invitation_builder.set_retraction_approval_invitation(journal, submission, note)