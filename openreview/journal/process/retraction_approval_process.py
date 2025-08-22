def process(client, edit, invitation):

    journal = openreview.journal.Journal()

    venue_id = journal.venue_id

    submission = client.get_note(edit.note.forum)

    ## Make the retraction public
    print('Make retraction public')
    invitation = journal.invitation_builder.set_note_retraction_release_invitation(submission)
    author_readers = submission.content['authors'].get('readers', [])

    if edit.note.content['approval']['value'] == 'Yes':
        client.post_note_edit(invitation= journal.get_retracted_id(),
                                signatures=[venue_id],
                                note=openreview.api.Note(id=submission.id,
                                content= {
                                    '_bibtex': {
                                        'value': journal.get_bibtex(submission, journal.retracted_venue_id, anonymous=(author_readers and author_readers != ['everyone']))
                                    }
                                }
        ))

    ## Send email to Authors
    print('Send email to authors')
    client.post_message(
        invitation=journal.get_meta_invitation_id(),
        recipients=[journal.get_authors_id(number=submission.number)],
        subject=f'''[{journal.short_name}] Decision available for retraction request of {journal.short_name} submission {submission.number}: {submission.content['title']['value']}''',
        message=f'''Hi {{{{fullname}}}},

As {journal.short_name} Editors-in-Chief, we have submitted our decision on your request to retract your accepted paper at {journal.short_name} "{submission.number}: {submission.content['title']['value']}".

To view our decision, follow this link: https://openreview.net/forum?id={edit.note.forum}&noteId={edit.note.id}

The {journal.short_name} Editors-in-Chief
''',
        replyTo=journal.contact_info,
        signature=venue_id,
        sender=journal.get_message_sender()
    )