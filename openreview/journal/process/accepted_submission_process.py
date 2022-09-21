def process(client, edit, invitation):

    note = client.get_note(edit.note.id)

    journal = openreview.journal.Journal()

    journal.invitation_builder.expire_paper_invitations(note)

    journal.invitation_builder.set_note_retraction_invitation(note)

    journal.invitation_builder.set_note_eic_revision_invitation(note)


