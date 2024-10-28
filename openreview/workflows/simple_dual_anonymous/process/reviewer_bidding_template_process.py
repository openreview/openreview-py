def process(client, edit, invitation):

    support_user = f'{invitation.domain}/Support'
    domain = client.get_group(edit.domain)
    meta_invitation_id = domain.content.get('meta_invitation_id', {}).get('value')

    stage_name = edit.content['name']['value']

    edit_invitations_builder = openreview.workflows.EditInvitationsBuilder(client, domain.id)
    bidding_invitation_id = f'{domain.id}/-/{stage_name}'
    edit_invitations_builder.set_edit_dates_one_level_invitation(bidding_invitation_id)
    edit_invitations_builder.set_edit_bidding_settings_invitation(bidding_invitation_id)

