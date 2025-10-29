def process(client, edit, invitation):

    venue_id = edit.content['venue_id']['value']

    domain = client.get_group(venue_id)

    committee_id = edit.content['committee_id']['value']
    committee_group = client.get_group(committee_id)
    committee_role = committee_group.content['committee_role']['value']

    invitation_edit = client.post_invitation_edit(
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

    content = {}
    content[f'{committee_role}_invited_message_id'] = { 'value': invitation_edit['invitation']['id'] }

    client.post_group_edit(
        invitation=domain.content['meta_invitation_id']['value'],
        signatures=[invitation.domain],
        group=openreview.api.Group(
            id=venue_id,
            content=content
        )
    )          