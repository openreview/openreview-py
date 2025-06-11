def process(client, edit, invitation):

    domain = client.get_group(edit.domain)
    meta_invitation_id = domain.content.get('meta_invitation_id', {}).get('value')

    stage_name = edit.content['name']['value']
    reviewers_name = edit.content['reviewers_name']['value']

    edit_invitations_builder = openreview.workflows.EditInvitationsBuilder(client, domain.id)
    bidding_invitation_id = f'{domain.id}/{reviewers_name}/-/{stage_name}'
    edit_invitations_builder.set_edit_bidding_settings_invitation(bidding_invitation_id)
    edit_invitations_builder.set_edit_dates_one_level_invitation(bidding_invitation_id, include_due_date=True, include_exp_date=True)