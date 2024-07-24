def process(client, edit, invitation):

    venue_id = edit.group.id
    client.post_invitation_edit(invitations=None,
        readers=[venue_id],
        writers=[venue_id],
        signatures=['~Super_User1'],
        invitation=openreview.api.Invitation(id=f'{venue_id}/-/Edit',
            invitees=[venue_id],
            readers=[venue_id],
            signatures=['~Super_User1'],
            content={
                'invitation_edit_script': {
                    'value': '' ## TODO add this script
                },
                'group_edit_script': {
                    'value': '' ## TODO add this script
                }
            },
            edit=True
        )
    )

    client.add_members_to_group('venues', venue_id)
    client.add_members_to_group('active_venues', venue_id)
    # TODO: create host group if doesn't exist
    # groups = venue_id.split('/')
    # root_id = groups[0]
    # if root_id == root_id.lower():
    #     root_id = groups[1]       
    # client.add_members_to_group('host', root_id)

    client.post_group_edit(
        invitation=f'{venue_id}/-/Edit',
        signatures=['~Super_User1'],
        group=openreview.api.Group(
            id=venue_id,
            content={
                'meta_invitation_id': { 'value': f'{venue_id}/-/Edit' }
            }
        )
    )