def process(client, edit, invitation):

    domain = client.get_group(edit.domain)
    invitation_id = edit.invitation.id

    cdate = edit.content['activation_date']['value']-1800000 # 30 min before cdate

    edit_invitations_builder = openreview.workflows.EditInvitationsBuilder(client, domain.id)
    edit_invitations_builder.set_edit_submission_release_source_invitation(invitation_id)
    edit_invitations_builder.set_edit_dates_one_level_invitation(invitation_id)