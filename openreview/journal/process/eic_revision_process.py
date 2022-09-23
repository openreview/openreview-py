def process(client, edit, invitation):

    journal = openreview.journal.Journal()
    
    venue_id = journal.venue_id
    submission=client.get_note(edit.note.id)
    authors_group_id=journal.get_authors_id(submission.number)
    authors_group=openreview.tools.get_group(client, authors_group_id)
    if authors_group:
        authors_group.members=submission.content['authorids']['value']
        client.post_group(authors_group)

    client.post_note_edit(invitation=journal.get_meta_invitation_id(),
        signatures=[venue_id],
        note=openreview.api.Note(id=submission.id,
            content= {
                '_bibtex': {
                    'value': journal.get_bibtex(submission, journal.accepted_venue_id, certifications=submission.content.get('certifications', {}).get('value'))
                }
            }
        )
    )        