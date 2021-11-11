def process(client, edit, invitation):

    journal = openreview.journal.Journal()

    note = edit.note

    submission = client.get_note(note.forum)

    ## If yes then assign the reviewer to the papers
    journal.invitation_builder.set_solicit_review_approval_invitation(journal, submission, note)