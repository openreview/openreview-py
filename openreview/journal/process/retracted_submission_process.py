def process(client, edit, invitation):

    note = client.get_note(edit.note.id)

    journal = openreview.journal.Journal()

    journal.invitation_builder.expire_paper_invitations(journal, note)

    print('Send email to Authors')
    client.post_message(
        recipients=[journal.get_reviewers_id(number=note.number)],
        subject=f'''[{journal.short_name}] Authors have retracted {journal.short_name} submission {note.content['title']['value']}''',
        message=f'''Hi {{{{fullname}}}},

TODO

The {journal.short_name} Editors-in-Chief

''',
        replyTo=journal.contact_info
    )