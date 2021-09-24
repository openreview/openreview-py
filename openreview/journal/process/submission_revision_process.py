def process(client, edit, invitation):

    note=client.get_note(edit.note.id)
    paper_group_id=edit.invitation.split('/-/')[0]
    authors_group_id=f'{paper_group_id}/Authors'
    authors_group=openreview.tools.get_group(client, authors_group_id)
    if authors_group:
        authors_group.members=note.content['authorids']['value']
        client.post_group(authors_group)