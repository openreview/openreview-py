def process(client, edit, invitation):

    journal = openreview.journal.Journal()
    venue_id = journal.venue_id

    submission = client.get_note(edit.note.forum)
    decisions = client.get_notes(invitation=journal.get_ae_decision_id(number=submission.number))

    if not decisions:
        return

    decision = decisions[0]

    acceptance_note = client.post_note_edit(invitation=journal.get_acceptance_id(),
                        signatures=[venue_id],
                        note=openreview.api.Note(id=submission.id,
                            content= {
                                'certifications': { 'value': decision.content.get('certifications', {}).get('value', []) }
                            }
                        )
                    )
