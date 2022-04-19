def process(client, edit, invitation):

    journal = openreview.journal.Journal()
    venue_id = journal.venue_id

    ## On update or delete return
    if edit.note.tcdate != edit.note.tmdate:
        return

    submission = client.get_note(edit.note.forum)
    decisions = client.get_notes(invitation=journal.get_ae_decision_id(number=submission.number))

    if not decisions:
        return

    decision = decisions[0]
    certifications = decision.content.get('certifications', {}).get('value', [])

    acceptance_note = client.post_note_edit(invitation=journal.get_accepted_id(),
                        signatures=[venue_id],
                        note=openreview.api.Note(id=submission.id,
                            content= {
                                '_bibtex': {
                                    'value': journal.get_bibtex(submission, journal.accepted_venue_id, certifications=certifications)
                                },
                                'certifications': { 'value': certifications }
                            }
                        )
                    )

    ## Send email to Authors
    print('Send email to Authors')
    client.post_message(
        recipients=[journal.get_authors_id(number=submission.number)],
        subject=f'''[{journal.short_name}] Camera ready version accepted for your {journal.short_name} submission {submission.content['title']['value']}''',
        message=f'''Hi {{{{fullname}}}},

This is to inform you that your submitted camera ready version of your paper {submission.content['title']['value']} has been verified and confirmed by the Action Editor.

We thank you again for your contribution to {journal.short_name} and congratulate you for your successful submission!

The {journal.short_name} Editors-in-Chief

''',
        replyTo=journal.contact_info
    )
