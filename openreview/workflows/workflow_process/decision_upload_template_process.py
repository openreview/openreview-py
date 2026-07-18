def process(client, edit, invitation):

    domain = client.get_group(edit.domain)

    stage_name = edit.content['name']['value']

    edit_invitations_builder = openreview.workflows.EditInvitationsBuilder(client, domain.id)
    decision_upload_invitation_id = f'{domain.id}/-/{stage_name}'
    edit_invitations_builder.set_edit_decisions_file_invitation(decision_upload_invitation_id)
    edit_invitations_builder.set_edit_dates_one_level_invitation(decision_upload_invitation_id)
