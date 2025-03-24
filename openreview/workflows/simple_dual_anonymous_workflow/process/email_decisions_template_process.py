def process(client, edit, invitation):

    support_user = f'{invitation.domain}/Support'
    domain = client.get_group(edit.domain)
    meta_invitation_id = domain.content.get('meta_invitation_id', {}).get('value')

    stage_name = edit.content['name']['value']

    edit_invitations_builder = openreview.workflows.EditInvitationsBuilder(client, domain.id)
    invitation_id = f'{domain.id}/-/{stage_name}'
    edit_invitations_builder.set_edit_email_date_invitation(invitation_id)
    edit_invitations_builder.set_edit_email_template_invitation(invitation_id)