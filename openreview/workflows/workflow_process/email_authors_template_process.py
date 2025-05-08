def process(client, edit, invitation):

    domain = client.get_group(edit.domain)
    meta_invitation_id = domain.content.get('meta_invitation_id', {}).get('value')

    stage_name = edit.content['name']['value']

    cdate = edit.content['activation_date']['value']-1800000 # 30 min before cdate

    edit_invitations_builder = openreview.workflows.EditInvitationsBuilder(client, domain.id)
    invitation_id = f'{domain.id}/-/{stage_name}'
    edit_invitations_builder.set_edit_email_template_invitation(invitation_id)
    if 'Reviews' in stage_name:
        edit_invitations_builder.set_edit_fields_email_template_invitation(invitation_id, due_date=cdate)
    edit_invitations_builder.set_edit_email_date_invitation(invitation_id, due_date=cdate)