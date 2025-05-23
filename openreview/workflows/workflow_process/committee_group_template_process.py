def process(client, edit, invitation):

    venue_id = edit.content['venue_id']['value']

    domain = client.get_group(venue_id)

    committee_role = edit.content['committee_role']['value']
    committee_name = edit.content['committee_name']['value']
    committee_pretty_name = edit.content['committee_pretty_name']['value']
    committee_anon_name = edit.content.get('committee_anon_name', {}).get('value', False)
    committee_submitted_name = edit.content.get('committee_submitted_name', {}).get('value', False)

    content = {
        f'{committee_role}_id': { 'value': edit.group.id },
        f'{committee_role}_name': { 'value': committee_name },
    }

    if committee_anon_name:
        content[f'{committee_role}_anon_name'] = { 'value': committee_anon_name }

    if committee_submitted_name:
        content[f'{committee_role}_submitted_name'] = { 'value': committee_submitted_name }

    client.post_group_edit(
        invitation=domain.content['meta_invitation_id']['value'],
        signatures=[invitation.domain],
        group=openreview.api.Group(
            id=venue_id,
            content=content
        )
    )

    client.post_group_edit(
        invitation=domain.content['meta_invitation_id']['value'],
        signatures=[invitation.domain],
        group=openreview.api.Group(
            id=edit.group.id,
            web=invitation.content[f'{committee_role}_web']['value'],
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
        invitation=f'{invitation.domain}/-/Committee_Invited_Group',
        signatures=[invitation.domain],
        content={
            'venue_id': { 'value': venue_id },
            'committee_id': { 'value': edit.group.id },
            'committee_pretty_name': { 'value': committee_pretty_name },
            'venue_short_name': { 'value': domain.content['subtitle']['value'] },
            'venue_contact': { 'value': domain.content['contact']['value'] }
        },
        await_process=True
    )