def process(client, edit, invitation):

    journal = openreview.journal.Journal()

    members = edit.group.members.get('append', [])

    print('Add expert reviewers', members)

    for member in members:
        ## find TMLR publications for member
        tmlr_notes = client.get_notes(content= { 'venueid': journal.venue_id, 'authorids': member })
        for note in tmlr_notes:
            client.post_note_edit(
                invitation=journal.get_meta_invitation_id(),
                signatures=[journal.venue_id],
                note=openreview.api.Note(
                    id=note.id,
                    content={
                        'certifications': {
                            'value': {
                                'append': [journal.get_expert_reviewer_certification()]
                            }
                        },
                        'expert_reviewers': {
                            'value': {
                                'append': [member]
                            }
                        },                        
                        '_bibtex': {
                            'value': journal.get_bibtex(note, journal.accepted_venue_id, certifications=note.content.get('certifications', {}).get('value', []) + [journal.get_expert_reviewer_certification()])
                        }
                    }
                )
            )