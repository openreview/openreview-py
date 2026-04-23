def process(client, edit, invitation):

    venue_id = edit.content['venue_id']['value']

    domain = client.get_group(venue_id)

    committee_role = edit.content['committee_role']['value']
    committee_name = edit.content['committee_name']['value']
    committee_pretty_name = edit.content['committee_pretty_name']['value']
    committee_anon_name = edit.content.get('committee_anon_name', {}).get('value', False)
    committee_submitted_name = edit.content.get('committee_submitted_name', {}).get('value', False)

    venue_short_name = domain.content['subtitle']['value']
    venue_from_email = f"{venue_short_name.replace(' ', '').replace(':', '-').replace('@', '').replace('(', '').replace(')', '').replace(',', '-').lower()}-notifications@openreview.net"

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
            'venue_short_name': { 'value': venue_short_name },
            'venue_from_email': { 'value': venue_from_email }
        },
        invitation=openreview.api.Invitation()
    )

    client.post_invitation_edit(
        invitations=f'{invitation.domain}/-/Group_Members',
        signatures=[invitation.domain],
        content={
            'venue_id': { 'value': venue_id },
            'group_id': { 'value': edit.group.id },
        },
        invitation=openreview.api.Invitation()
    )

    ## Enable recruitment?

    invited_group_edit = client.post_group_edit(
        invitation=f'{invitation.domain}/-/Committee_Invited_Group',
        signatures=[invitation.domain],
        content={
            'venue_id': { 'value': venue_id },
            'committee_id': { 'value': edit.group.id }
        }
    )

    invited_group_id = invited_group_edit['group']['id']

    invited_message_invitation_edit = client.post_invitation_edit(
        invitations=f'{invitation.domain}/-/Group_Message',
        signatures=[invitation.domain],
        content={
            'venue_id': { 'value': venue_id },
            'group_id': { 'value': invited_group_id },
            'venue_short_name': { 'value': venue_short_name },
            'venue_from_email': { 'value': venue_from_email }
        },
        invitation=openreview.api.Invitation()
    )

    declined_group_edit = client.post_group_edit(
        invitation=f'{invitation.domain}/-/Committee_Declined_Group',
        signatures=[invitation.domain],
        content={
            'venue_id': { 'value': venue_id },
            'committee_id': { 'value': edit.group.id },
        }
    )

    content[f'{committee_role}_declined_id'] = { 'value': declined_group_edit['group']['id'] }
    content[f'{committee_role}_invited_id'] = { 'value': invited_group_id }
    content[f'{committee_role}_invited_message_id'] = { 'value': invited_message_invitation_edit['invitation']['id'] }

    invitation_edit = client.post_invitation_edit(
        invitations=f'{invitation.domain}/-/Committee_Recruitment_Request',
        signatures=[invitation.domain],
        content={
            'venue_id': { 'value': venue_id },
            'committee_id': { 'value': edit.group.id },
            'committee_pretty_name': { 'value': committee_pretty_name },
            'venue_short_name': { 'value': venue_short_name },
            'reminder_delay': { 'value': 3000 if (invitation.domain.startswith('openreview.net')) else (1000 * 60 * 60 * 24 * 7)  }
        },
        invitation=openreview.api.Invitation()
    )

    edit_invitations_builder = openreview.workflows.EditInvitationsBuilder(client, domain.id)
    edit_invitations_builder.set_edit_dates_one_level_invitation(invitation_edit['invitation']['id'], include_due_date=True, include_exp_date=True)
    edit_invitations_builder.set_edit_committee_recruitment_request_invitation(invitation_edit['invitation']['id'])

    client.post_invitation_edit(
        invitations=f'{invitation.domain}/-/Committee_Recruitment_Request_Reminder',
        signatures=[invitation.domain],
        content={
            'venue_id': { 'value': venue_id },
            'committee_id': { 'value': edit.group.id },
            'committee_pretty_name': { 'value': committee_pretty_name },
            'venue_short_name': { 'value': venue_short_name }
        },
        invitation=openreview.api.Invitation()
    )

    invitation_edit = client.post_invitation_edit(
        invitations=f'{invitation.domain}/-/Committee_Recruitment_Response',
        signatures=[invitation.domain],
        content={
            'venue_id': { 'value': venue_id },
            'venue_short_name': { 'value': venue_short_name },
            'committee_id': { 'value': edit.group.id },
            'committee_pretty_name': { 'value': committee_pretty_name },
            'due_date': { 'value': openreview.tools.datetime_millis(datetime.datetime.now() + datetime.timedelta(weeks=12)) }
        },
        invitation=openreview.api.Invitation()
    )

    edit_invitations_builder.set_edit_dates_one_level_invitation(invitation_edit['invitation']['id'], include_due_date=True, include_exp_date=True)
    edit_invitations_builder.set_edit_committee_recruitment_invitation(invitation_edit['invitation']['id'])

    content[f'{committee_role}_recruitment_id'] = { 'value': invitation_edit['invitation']['id'] }

    client.post_group_edit(
        invitation=domain.content['meta_invitation_id']['value'],
        signatures=[invitation.domain],
        group=openreview.api.Group(
            id=venue_id,
            content=content
        )
    )
