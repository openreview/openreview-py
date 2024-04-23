def process(client, edit, invitation):

    note = client.get_note(edit.note.id)

    journal = openreview.journal.Journal()

    journal.invitation_builder.expire_paper_invitations(note)

    print('Send email to AE and Reviewers')
    client.post_message(
        invitation=journal.get_meta_invitation_id(),
        recipients=[journal.get_action_editors_id(number=note.number), journal.get_reviewers_id(number=note.number)],
        subject=f'''[{journal.short_name}] Authors have withdrawn {journal.short_name} submission {note.number}: {note.content['title']['value']}''',
        message=f'''Hi {{{{fullname}}}},

This is to inform you that the paper {note.number}: {note.content['title']['value']}, for which you were involved in the review process, has been withdrawn by the authors. Your help is therefore no longer needed.

We thank you for your involvement with {journal.short_name}!

The {journal.short_name} Editors-in-Chief
''',
        replyTo=journal.contact_info,
        signature=journal.venue_id,
        sender=journal.get_message_sender()
    )

    print('Enable Author deanonymize')
    journal.invitation_builder.set_note_authors_deanonymization_invitation(note)