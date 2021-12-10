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

    acceptance_note = client.post_note_edit(invitation=journal.get_acceptance_id(),
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
