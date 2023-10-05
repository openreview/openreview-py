def process(client, edit, invitation):

    journal = openreview.journal.Journal()
    
    venue_id = journal.venue_id
    submission=client.get_note(edit.note.id)
    authors_group_id=journal.get_authors_id(submission.number)

    client.post_group_edit(
        invitation = journal.get_meta_invitation_id(),
        readers = [venue_id],
        writers = [venue_id],
        signatures = [venue_id],
        group = openreview.api.Group(
            id = authors_group_id,
            members = submission.content['authorids']['value']
        )
    )

    client.post_note_edit(invitation=journal.get_meta_invitation_id(),
        signatures=[venue_id],
        note=openreview.api.Note(id=submission.id,
            content= {
                '_bibtex': {
                    'value': journal.get_bibtex(submission, journal.accepted_venue_id, certifications=submission.content.get('certifications', {}).get('value',[]))
                }
            }
        )
    )        
