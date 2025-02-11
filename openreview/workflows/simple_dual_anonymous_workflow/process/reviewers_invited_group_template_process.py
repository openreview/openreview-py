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
                'reviewers_invited_id': { 'value': edit.group.id },
            }
        )
    )

    client.post_invitation_edit(
        invitations=f'{support_user}/Simple_Dual_Anonymous/Venue_Configuration_Request/-/Reviewers_Invited_Members_Template',
        signatures=[support_user],
        content={
            'venue_id': { 'value': venue_id },
            'reviewers_invited_id': { 'value': edit.group.id },
        },
        invitation=openreview.api.Invitation(),
        await_process=True
    )

    client.post_invitation_edit(
        invitations=f'{support_user}/Simple_Dual_Anonymous/Venue_Configuration_Request/-/Reviewers_Invited_Response_Template',
        signatures=[support_user],
        content={
            'venue_id': { 'value': venue_id },
            'reviewers_invited_id': { 'value': edit.group.id },
        },
        invitation=openreview.api.Invitation(),
        await_process=True
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