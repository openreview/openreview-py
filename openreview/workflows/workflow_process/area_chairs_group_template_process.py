def process(client, edit, invitation):

    venue_id = edit.content['venue_id']['value']

    domain = client.get_group(venue_id)

    area_chairs_name = edit.content['area_chairs_name']['value']
    area_chairs_anon_name = f'{area_chairs_name[:-1] if area_chairs_name.endswith("s") else area_chairs_name}_'

    client.post_group_edit(
        invitation=domain.content['meta_invitation_id']['value'],
        signatures=[invitation.domain],
        group=openreview.api.Group(
            id=venue_id,
            content={
                'area_chairs_id': { 'value': edit.group.id },
                'area_chairs_name': { 'value': area_chairs_name },
                'area_chairs_anon_name': { 'value': area_chairs_anon_name }
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

    client.post_invitation_edit(
        invitations=f'{invitation.domain}/-/Group_Members',
        signatures=[invitation.domain],
        content={
            'venue_id': { 'value': venue_id },
            'group_id': { 'value': edit.group.id },
        },
        invitation=openreview.api.Invitation(),
        await_process=True
    )

    client.post_group_edit(
        invitation=f'{invitation.domain}/-/Area_Chairs_Invited_Declined_Group',
        signatures=[invitation.domain],
        content={
            'venue_id': { 'value': venue_id },
            'area_chairs_id': { 'value': edit.group.id },
        },
        await_process=True
    )   