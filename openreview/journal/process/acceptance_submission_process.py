def process(client, edit, invitation):

    note = client.get_note(edit.note.id)

    journal = openreview.journal.Journal()

    journal.invitation_builder.expire_paper_invitations(journal, note)

    journal.invitation_builder.set_retract_invitation(journal, note)


