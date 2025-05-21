def process(client, edit, invitation):

    venue_id = edit.content['venue_id']['value']

    domain = client.get_group(venue_id)

    committee_id = edit.content['committee_id']['value']
    committee_group = client.get_group(committee_id)
    committee_role = committee_group.content['committee_role']['value']
    
    client.post_group_edit(
        invitation=domain.content['meta_invitation_id']['value'],
        signatures=[invitation.domain],
        group=openreview.api.Group(
            id=venue_id,
            content={
                f'{committee_role}_declined_id': { 'value': edit.group.id },
            }
        )
    )    