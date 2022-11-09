def process(client, edit, invitation):
    VENUE_ID = ''
    META_INVITATION_ID = ''
    AUTHORS_GROUP_ID = ''
    venue_id = VENUE_ID
    note = client.get_note(edit.note.id)
    submission_name = invitation.id.split('/-/')[-1]
    authors_name = 'Authors'
    
    paper_group_id=f'{venue_id}/{submission_name}{note.number}'
    paper_group=openreview.tools.get_group(client, paper_group_id)
    if not paper_group:
        client.post_group_edit(
            invitation = META_INVITATION_ID,
            readers = [venue_id],
            writers = [venue_id],
            signatures = [venue_id],
            group = openreview.api.Group(
                id = paper_group_id,
                readers=[venue_id],
                writers=[venue_id],
                signatures=[venue_id],
                signatories=[venue_id]
            )
        )        

    authors_group_id=f'{paper_group_id}/{authors_name}'
    client.post_group_edit(
        invitation = META_INVITATION_ID,
        readers = [venue_id],
        writers = [venue_id],
        signatures = [venue_id],
        group = openreview.api.Group(
            id = authors_group_id,
            readers=[venue_id, authors_group_id],
            writers=[venue_id],
            signatures=[venue_id],
            signatories=[venue_id, authors_group_id],
            members=note.content['authorids']['value'] ## always update authors
        )
    )    
    client.add_members_to_group(AUTHORS_GROUP_ID, authors_group_id)
