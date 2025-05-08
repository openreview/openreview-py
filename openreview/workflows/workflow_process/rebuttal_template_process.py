def process(client, edit, invitation):

    domain = client.get_group(edit.domain)
    meta_invitation_id = domain.content.get('meta_invitation_id', {}).get('value')

    stage_name = edit.content['name']['value']

    edit_invitations_builder = openreview.workflows.EditInvitationsBuilder(client, domain.id)
    rebuttal_invitation_id = f'{domain.id}/-/{stage_name}'
    edit_invitations_builder.set_edit_content_invitation(rebuttal_invitation_id)
    edit_invitations_builder.set_edit_reply_readers_invitation(rebuttal_invitation_id, include_signatures=False)
    edit_invitations_builder.set_edit_email_settings_invitation(rebuttal_invitation_id, email_pcs=True, email_authors=True, email_reviewers=True)
    edit_invitations_builder.set_edit_dates_invitation(rebuttal_invitation_id)