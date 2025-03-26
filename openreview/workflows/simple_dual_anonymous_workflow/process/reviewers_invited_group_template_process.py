def process(client, edit, invitation):

    venue_id = edit.content['venue_id']['value']

    domain = client.get_group(venue_id)
    support_user = f'{invitation.domain}/Support'

    client.post_group_edit(
        invitation=domain.content['meta_invitation_id']['value'],
        signatures=['~Super_User1'],
        group=openreview.api.Group(
            id=venue_id,
            content={
                'reviewers_invited_id': { 'value': edit.group.id }
            }
        )
    )

    client.post_invitation_edit(
        invitations=f'{support_user}/Simple_Dual_Anonymous/Venue_Configuration_Request/-/Reviewers_Invited_Members_Template',
        signatures=[support_user],
        content={
            'venue_id': { 'value': venue_id },
            'reviewers_invited_id': { 'value': edit.group.id },
            'reminder_delay': { 'value': 3000 if (invitation.domain == 'openreview.net') else (1000 * 60 * 60 * 24 * 7)  }
        },
        invitation=openreview.api.Invitation(),
        await_process=True
    )

    client.post_invitation_edit(
        invitations=f'{support_user}/Simple_Dual_Anonymous/Venue_Configuration_Request/-/Reviewers_Invited_Reminder_Template',
        signatures=[support_user],
        content={
            'venue_id': { 'value': venue_id },
            'reviewers_invited_id': { 'value': edit.group.id }
        },
        invitation=openreview.api.Invitation(),
        await_process=True
    )    

    client.post_invitation_edit(
        invitations=f'{support_user}/Simple_Dual_Anonymous/Venue_Configuration_Request/-/Reviewers_Invited_Emails_Template',
        signatures=[support_user],
        content={
            'venue_id': { 'value': venue_id },
            'reviewers_invited_id': { 'value': edit.group.id }
        },
        invitation=openreview.api.Invitation(),
        await_process=True
    )    

    invitation_edit = client.post_invitation_edit(
        invitations=f'{support_user}/Simple_Dual_Anonymous/Venue_Configuration_Request/-/Reviewers_Invited_Response_Template',
        signatures=[support_user],
        content={
            'venue_id': { 'value': venue_id },
            'reviewers_invited_id': { 'value': edit.group.id },
            'due_date': { 'value': openreview.tools.datetime_millis(datetime.datetime.now() + datetime.timedelta(weeks=12)) },
            'hash_seed': { 'value': openreview.tools.create_hash_seed() }
        },
        invitation=openreview.api.Invitation(),
        await_process=True
    )

    client.post_group_edit(
        invitation=domain.content['meta_invitation_id']['value'],
        signatures=['~Super_User1'],
        group=openreview.api.Group(
            id=venue_id,
            content={
                'reviewers_invited_response_id': { 'value': invitation_edit['invitation']['id'] },
            }
        )
    )    

    invitation_edit = client.post_invitation_edit(
        invitations=f'{support_user}/Simple_Dual_Anonymous/Venue_Configuration_Request/-/Group_Message_Template',
        signatures=[support_user],
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

    client.post_group_edit(
        invitation=domain.content['meta_invitation_id']['value'],
        signatures=['~Super_User1'],
        group=openreview.api.Group(
            id=venue_id,
            content={
                'reviewers_invited_message_id': { 'value': invitation_edit['invitation']['id'] },
            }
        )
    )

    client.post_group_edit(
        invitation=f'{support_user}/Simple_Dual_Anonymous/Venue_Configuration_Request/-/Reviewers_Invited_Declined_Group_Template',
        signatures=[support_user],
        content={
            'venue_id': { 'value': venue_id },
            'reviewers_invited_id': { 'value': edit.group.id },
        },
        await_process=True
    )          