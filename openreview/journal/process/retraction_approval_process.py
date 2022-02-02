def process(client, edit, invitation):

    journal = openreview.journal.Journal()

    venue_id = journal.venue_id

    submission = client.get_note(edit.note.forum)

    if edit.note.content['approval']['value'] == 'Yes':
        client.post_note_edit(invitation= journal.get_retracted_id(),
                                signatures=[venue_id],
                                note=openreview.api.Note(id=submission.id,
                                content= {
                                    '_bibtex': {
                                        'value': journal.get_bibtex(submission, journal.retracted_venue_id, anonymous=submission.content['authors'].get('readers', []) != ['everyone'])
                                    }
                                }
        ))

    ## Send email to Authors
    print('Send email to authors')
    client.post_message(
        recipients=[journal.get_authors_id(number=submission.number)],
        subject=f'''[{journal.short_name}] Decision available for retraction request of TMLR submission {submission.content['title']['value']}''',
        message=f'''Hi {{{{fullname}}}},

As TMLR Editors-in-Chief, we have submitted our decision on your request to retract your accepted paper at TMLR titled "{submission.content['title']['value']}".

To view our decision, follow this link: https://openreview.net/forum?id={edit.note.forum}&noteId={edit.note.id}

The TMLR Editors-in-Chief

''',
        replyTo=journal.contact_info
    )