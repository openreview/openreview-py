def process(client, edit, invitation):

    domain = client.get_group(edit.domain)
    stage_name = edit.content['name']['value']

    edit_invitations_builder = openreview.workflows.EditInvitationsBuilder(client, domain.id)
    edit_invitations_builder.set_edit_dates_invitation(f'{domain.id}/-/{stage_name}', include_expiration_date=False)
