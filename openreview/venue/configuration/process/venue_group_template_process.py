def process(client, edit, invitation):

    support_user = 'openreview.net/Support'
    venue_id = edit.group.id

    invitation_edit = client.post_invitation_edit(invitations=f'{support_user}/-/Edit_Template',
        signatures=['~Super_User1'],
        domain=venue_id
    )

    client.add_members_to_group('venues', venue_id)
    client.add_members_to_group('active_venues', venue_id)
    
    path_components = venue_id.split('/')
    paths = ['/'.join(path_components[0:index+1]) for index, path in enumerate(path_components)]    
    for group in paths[:-1]:
        client.post_group_edit(
            invitation=f'{support_user}/-/Venue_Inner_Group_Template',
            signatures=['~Super_User1'],
            group=openreview.api.Group(
                id=group,
           )
        )
    root_id = paths[0]
    if root_id == root_id.lower():
        root_id = paths[1]       
    client.add_members_to_group('host', root_id)

    client.post_group_edit(
        invitation=invitation_edit['invitation']['id'],
        signatures=['~Super_User1'],
        group=openreview.api.Group(
            id=venue_id,
            content={
                'meta_invitation_id': { 'value': invitation_edit['invitation']['id'] },
                'rejected_venue_id': { 'value': f'{venue_id}/Rejected' }, ## Move this to the Rejected invitation process         
            }
        )
    )