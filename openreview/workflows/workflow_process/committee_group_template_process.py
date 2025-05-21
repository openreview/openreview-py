def process(client, edit, invitation):

    venue_id = edit.content['venue_id']['value']

    domain = client.get_group(venue_id)

    committee_key = edit.content['committee_role']['value']
    committee_name = edit.content['committee_name']['value']
    singular_committee_name = committee_name[:-1] if committee_name.endswith('s') else committee_name
    committee_anon_name = f'{singular_committee_name}_'
    committee_pretty_name = singular_committee_name.replace('_', ' ')
    is_anon = edit.content.get('is_anon', {}).get('value', False)
    has_submitted = edit.content.get('has_submitted', {}).get('value', False)

    content = {
        f'{committee_key}_id': { 'value': edit.group.id },
        f'{committee_key}_name': { 'value': committee_name },
    }

    if is_anon:
        content[f'{committee_key}_anon_name'] = { 'value': committee_anon_name }

    if has_submitted:
        content[f'{committee_key}_submitted_name'] = { 'value': 'Submitted' }

    client.post_group_edit(
        invitation=domain.content['meta_invitation_id']['value'],
        signatures=[invitation.domain],
        group=openreview.api.Group(
            id=venue_id,
            content=content
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

    client.post_group_edit(
        invitation=f'{invitation.domain}/-/Committee_Invited_Declined_Group',
        signatures=[invitation.domain],
        content={
            'venue_id': { 'value': venue_id },
            'committee_id': { 'value': edit.group.id },
        },
        await_process=True
    )            