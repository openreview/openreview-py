def process(client, edit, invitation):

    venue_id = edit.content['venue_id']['value']

    domain = client.get_group(venue_id)
    support_user = f'{invitation.domain}/Support'    

    reviewers_name = edit.content['reviewers_name']['value']
    reviewers_anon_name = f'{reviewers_name[:-1] if reviewers_name.endswith("s") else reviewers_name}_'

    client.post_group_edit(
        invitation=domain.content['meta_invitation_id']['value'],
        signatures=['~Super_User1'],
        group=openreview.api.Group(
            id=venue_id,
            content={
                'reviewers_id': { 'value': edit.group.id },
                'reviewers_name': { 'value': reviewers_name },
                'reviewers_anon_name': { 'value': reviewers_anon_name },
                'reviewers_submitted_name': { 'value': 'Submitted' },
            }
        )
    )

    client.post_invitation_edit(
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

    client.post_invitation_edit(
        invitations=f'{support_user}/Simple_Dual_Anonymous/Venue_Configuration_Request/-/Group_Members_Template',
        signatures=[support_user],
        content={
            'venue_id': { 'value': venue_id },
            'group_id': { 'value': edit.group.id },
        },
        invitation=openreview.api.Invitation(),
        await_process=True
    )        