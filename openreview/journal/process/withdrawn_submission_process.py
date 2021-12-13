def process(client, edit, invitation):

    note = client.get_note(edit.note.id)

    journal = openreview.journal.Journal()

    invitations = client.get_invitations(replyForum=edit.note.id)

    print(f'Expire invitations: {[i.id for i in invitations]}')

    for invitation in invitations:
        if f'/Paper{note.number}/' in invitation.id:
            journal.invitation_builder.expire_invitation(journal, invitation.id)

    print('Send email to AE and Reviewers')
    client.post_message(
        recipients=[journal.get_action_editors_id(number=note.number), journal.get_reviewers_id(number=note.number)],
        subject=f'''[{journal.short_name}] Authors have withdrawn TMLR submission {note.content['title']['value']}''',
        message=f'''Hi {{{{fullname}}}},

This is to inform you that the paper {note.content['title']['value']}, for which you were involved in the review process, has been withdrawn by the authors. Your help is therefore no longer needed.

We thank you for your involvement with TMLR!

The TMLR Editors-in-Chief

''',
        replyTo=journal.contact_info
    )