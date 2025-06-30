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

    client.post_invitation_edit(
        invitations=f'{invitation.domain}/-/Group_Message',
        signatures=[invitation.domain],
        content={
            'venue_id': { 'value': venue_id },
            'group_id': { 'value': edit.group.id },
            'message_reply_to': { 'value': domain.content['contact']['value'] },
            'venue_short_name': { 'value': domain.content['subtitle']['value'] },
            'venue_from_email': { 'value': f"{domain.content['subtitle']['value'].replace(' ', '').replace(':', '-').replace('@', '').replace('(', '').replace(')', '').replace(',', '-').lower()}-notifications@openreview.net" }
        },
        invitation=openreview.api.Invitation(),
        await_process=True
    )     