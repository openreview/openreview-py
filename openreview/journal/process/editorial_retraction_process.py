def process(client, edit, invitation):

    journal = openreview.journal.Journal()

    submission = client.get_note(edit.note.forum)

    journal.post_retracted_submission(submission, journal.retracted_by_editors_venue)

    ## Send email to Authors
    print('Send email to authors')
    client.post_message(
        invitation=journal.get_meta_invitation_id(),
        recipients=[journal.get_authors_id(number=submission.number)],
        subject=f'''[{journal.short_name}] {journal.short_name} submission {submission.number} has been retracted: {submission.content['title']['value']}''',
        message=f'''Hi {{{{fullname}}}},

As {journal.short_name} Editors-in-Chief, we have retracted your accepted paper at {journal.short_name} "{submission.number}: {submission.content['title']['value']}".

To view the retraction, follow this link: https://openreview.net/forum?id={edit.note.forum}&noteId={edit.note.id}

The {journal.short_name} Editors-in-Chief
''',
        replyTo=journal.contact_info,
        signature=journal.venue_id,
        sender=journal.get_message_sender()
    )
