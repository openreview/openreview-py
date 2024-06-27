def process(client, edit, invitation):

    journal = openreview.journal.Journal()
    
    venue_id = journal.venue_id
    note=client.get_note(edit.note.id)
    paper_group_id=edit.invitation.split('/-/')[0]
    authors_group_id=f'{paper_group_id}/Authors'

    journal.notify_readers(edit, content_fields=[])

    client.post_group_edit(
        invitation = journal.get_meta_invitation_id(),
        readers = [venue_id],
        writers = [venue_id],
        signatures = [venue_id],
        group = openreview.api.Group(
            id = authors_group_id,
            members = note.content['authorids']['value']
        )
    )