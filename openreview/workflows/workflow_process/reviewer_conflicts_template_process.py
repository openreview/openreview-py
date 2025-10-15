def process(client, edit, invitation):

    domain = client.get_group(edit.domain)
    meta_invitation_id = domain.content.get('meta_invitation_id', {}).get('value')
    committee_name = edit.content['committee_name']['value']
    committee_id = f'{domain.id}/{committee_name}'
    committee_group = client.get_group(committee_id)
    committee_role = committee_group.content['committee_role']['value']

    stage_name = edit.content['name']['value']
    conflicts_invitation_id = f'{committee_id}/-/{stage_name}'

    client.post_group_edit(
        invitation=meta_invitation_id,
        signatures=[invitation.domain],
        group=openreview.api.Group(
            id=domain.id,
            content={
                f'{committee_role}_conflict_id': { 'value': conflicts_invitation_id },
                f'{committee_role}_conflict_policy': { 'value': 'Default' },
                f'{committee_role}_conflict_n_years': { 'value': 0 }
            }
        )
    )

    edit_invitations_builder = openreview.workflows.EditInvitationsBuilder(client, domain.id)
    print('Set up conflicts invitation:', conflicts_invitation_id)
    edit_invitations_builder.set_edit_conflict_settings_invitation(conflicts_invitation_id)
    edit_invitations_builder.set_edit_dates_one_level_invitation(conflicts_invitation_id)