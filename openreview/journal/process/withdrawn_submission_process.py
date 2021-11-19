def process(client, edit, invitation):

    note = client.get_note(edit.note.id)

    journal = openreview.journal.Journal()

    invitations = client.get_invitations(replyForum=edit.note.id)

    print(f'Expire invitations: {[i.id for i in invitations]}')

    for invitation in invitations:
        if f'/Paper{note.number}/' in invitation.id:
            journal.invitation_builder.expire_invitation(journal, invitation.id)