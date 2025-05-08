def process(client, edit, invitation):

    domain = client.get_group(edit.domain)
    meta_invitation_id = domain.content.get('meta_invitation_id', {}).get('value')

    reviewers_name = edit.content['reviewers_name']['value']
    submission_name = edit.content['submission_name']['value']

    submission_group_invitation_id = f'{domain.id}/{reviewers_name}/-/{submission_name}_Group'
    edit_invitations_builder = openreview.workflows.EditInvitationsBuilder(client, domain.id)
    edit_invitations_builder.set_edit_group_deanonymizers_invitation(submission_group_invitation_id)
    edit_invitations_builder.set_edit_dates_one_level_invitation(submission_group_invitation_id)