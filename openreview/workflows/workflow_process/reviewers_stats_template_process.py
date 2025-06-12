def process(client, edit, invitation):

    domain = client.get_group(edit.domain)

    edit_invitations_builder = openreview.workflows.EditInvitationsBuilder(client, domain.id)
    print('edit', edit.invitation.id)
    edit_invitations_builder.set_edit_dates_one_level_invitation(edit.invitation.id, include_due_date=False, include_exp_date=False)