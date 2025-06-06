def process(client, edit, invitation):

    domain = client.get_group(edit.domain)
    meta_invitation_id = domain.content.get('meta_invitation_id', {}).get('value')
    reviewers_name = domain.content.get('reviewers_name', {}).get('value')

    stage_name = edit.content['name']['value']

    client.post_group_edit(
        invitation=meta_invitation_id,
        signatures=[invitation.domain],
        group=openreview.api.Group(
            id=domain.id,
            content={
                'reviewers_conflict_id': { 'value': f'{domain.id}/{reviewers_name}/-/{stage_name}' },
                'reviewers_conflict_policy': { 'value': 'Default' },
                'reviewers_conflict_n_years': { 'value': 0 }
            }
        )
    )

    edit_invitations_builder = openreview.workflows.EditInvitationsBuilder(client, domain.id)
    conflicts_invitation_id = f'{domain.id}/{reviewers_name}/-/{stage_name}'
    edit_invitations_builder.set_edit_conflict_settings_invitation(conflicts_invitation_id)
    edit_invitations_builder.set_edit_dates_one_level_invitation(conflicts_invitation_id)