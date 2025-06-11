def process(client, edit, invitation):

    venue_id = edit.content['venue_id']['value']

    domain = client.get_group(venue_id)

    committee_id = edit.content['committee_id']['value']
    committee_group = client.get_group(committee_id)
    committee_role = committee_group.content['committee_role']['value']
    committee_pretty_name = committee_group.content['committee_pretty_name']['value']

    edit_invitations_builder = openreview.workflows.EditInvitationsBuilder(client, domain.id)

    content = {
        f'{committee_role}_invited_id': { 'value': edit.group.id }
    }

    declined_group_edit = client.post_group_edit(
        invitation=f'{invitation.domain}/-/Committee_Invited_Declined_Group',
        signatures=[invitation.domain],
        content={
            'venue_id': { 'value': venue_id },
            'committee_id': { 'value': committee_id },
        },
        await_process=True
    )     

    content[f'{committee_role}_declined_id'] = { 'value': declined_group_edit['group']['id'] }

    client.post_invitation_edit(
        invitations=f'{invitation.domain}/-/Committee_Invited_Recruitment',
        signatures=[invitation.domain],
        content={
            'venue_id': { 'value': venue_id },
            'committee_invited_id': { 'value': edit.group.id },
            'reminder_delay': { 'value': 3000 if (invitation.domain.startswith('openreview.net')) else (1000 * 60 * 60 * 24 * 7)  }
        },
        invitation=openreview.api.Invitation(),
        await_process=True
    )

    client.post_invitation_edit(
        invitations=f'{invitation.domain}/-/Committee_Invited_Recruitment_Reminder',
        signatures=[invitation.domain],
        content={
            'venue_id': { 'value': venue_id },
            'committee_invited_id': { 'value': edit.group.id }
        },
        invitation=openreview.api.Invitation(),
        await_process=True
    )    

    client.post_invitation_edit(
        invitations=f'{invitation.domain}/-/Committee_Invited_Recruitment_Emails',
        signatures=[invitation.domain],
        content={
            'venue_id': { 'value': venue_id },
            'committee_invited_id': { 'value': edit.group.id }
        },
        invitation=openreview.api.Invitation(),
        await_process=True
    )    

    invitation_edit = client.post_invitation_edit(
        invitations=f'{invitation.domain}/-/Committee_Invited_Recruitment_Response',
        signatures=[invitation.domain],
        content={
            'venue_id': { 'value': venue_id },
            'committee_id': { 'value': committee_id },
            'committee_pretty_name': { 'value': committee_pretty_name },
            'due_date': { 'value': openreview.tools.datetime_millis(datetime.datetime.now() + datetime.timedelta(weeks=12)) },
            'hash_seed': { 'value': openreview.tools.create_hash_seed() },
        },
        invitation=openreview.api.Invitation(),
        await_process=True
    )

    edit_invitations_builder.set_edit_dates_one_level_invitation(invitation_edit['invitation']['id'], include_due_date=True, include_exp_date=True)


    content[f'{committee_role}_recruitment_id'] = { 'value': invitation_edit['invitation']['id'] }

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

    content[f'{committee_role}_invited_message_id'] = { 'value': invitation_edit['invitation']['id'] }

    client.post_group_edit(
        invitation=domain.content['meta_invitation_id']['value'],
        signatures=[invitation.domain],
        group=openreview.api.Group(
            id=venue_id,
            content=content
        )
    )          