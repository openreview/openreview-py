def process(client, edit, invitation):

    venue_id = edit.content['venue_id']['value']

    domain = client.get_group(venue_id)

    authors_name = edit.content['authors_name']['value']

    client.post_group_edit(
        invitation=domain.content['meta_invitation_id']['value'],
        signatures=[venue_id],
        group=openreview.api.Group(
            id=venue_id,
            content={
                'authors_id': { 'value': edit.group.id },
                'authors_accepted_id': { 'value': f'{edit.group.id}/Accepted' },
                'authors_name': { 'value': authors_name },
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
                'authors_name': { 'value': authors_name },
            }
        )
    )    