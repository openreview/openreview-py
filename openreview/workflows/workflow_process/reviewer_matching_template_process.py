def process(client, edit, invitation):

    domain = client.get_group(edit.domain)
    meta_invitation_id = domain.content.get('meta_invitation_id', {}).get('value')

    stage_name = edit.content['name']['value']

    edit_invitations_builder = openreview.workflows.EditInvitationsBuilder(client, domain.id)
    assignment_invitation_id = f'{domain.id}/-/{stage_name}'
    edit_invitations_builder.set_edit_assignment_match_settings_invitation(assignment_invitation_id)