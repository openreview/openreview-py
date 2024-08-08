def process(client, edit, invitation):

    venue_id = edit.content['venue_id']['value']

    domain = client.get_group(venue_id)

    client.add_members_to_group(venue_id, edit.group.id)

    client.post_group_edit(
        invitation=domain.content['meta_invitation_id']['value'],
        signatures=['~Super_User1'],
        group=openreview.api.Group(
            id=venue_id,
            content={
                'program_chairs_id': { 'value': edit.group.id }
            }
        )
    )

    ## Hack to change the domain id to the venue_id, remove when type: domain is supported
    client.post_group_edit(
        invitation=domain.content['meta_invitation_id']['value'],
        signatures=[venue_id],
        group=openreview.api.Group(
            id=edit.group.id,
            content={
                'program_chairs_name': { 'value': 'Program_Chairs' },
            }
        )
    )     