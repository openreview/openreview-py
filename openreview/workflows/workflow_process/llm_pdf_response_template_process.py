def process(client, edit, invitation):

    domain = client.get_group(edit.domain)
    meta_invitation_id = domain.content.get('meta_invitation_id', {}).get('value')

    stage_name = edit.content['name']['value']

    edit_invitations_builder = openreview.workflows.EditInvitationsBuilder(client, domain.id)
    llm_pdf_response_invitation_id = f'{domain.id}/-/{stage_name}'

    edit_invitations_builder.set_edit_dates_invitation(llm_pdf_response_invitation_id, include_due_date=False, include_expiration_date=False)
    edit_invitations_builder.set_edit_email_settings_invitation(llm_pdf_response_invitation_id)
    edit_invitations_builder.set_edit_prompt_invitation(llm_pdf_response_invitation_id)
    edit_invitations_builder.set_edit_reply_readers_invitation(llm_pdf_response_invitation_id, include_signatures=False)