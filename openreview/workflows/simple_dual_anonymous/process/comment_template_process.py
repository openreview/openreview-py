def process(client, edit, invitation):

    support_user = 'openreview.net/Support'
    domain = client.get_group(edit.domain)
    meta_invitation_id = domain.content.get('meta_invitation_id', {}).get('value')

    stage_name = edit.content['name']['value']

    edit_invitations_builder = openreview.workflows.EditInvitationsBuilder(client, domain.id)
    comment_invitation_id = f'{domain.id}/-/{stage_name}'
    edit_invitations_builder.set_edit_deadlines_invitation(comment_invitation_id, include_due_date=False)
    
    edit_invitations_builder.set_edit_content_invitation(comment_invitation_id)
    # edit_invitations_builder.set_edit_reply_readers_invitation(comment_invitation_id)
    edit_invitations_builder.set_edit_email_settings_invitation(comment_invitation_id, email_pcs=True, email_authors=False)