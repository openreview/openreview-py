def process(client, edit, invitation):

    support_user = f'{invitation.domain}/Support'
    domain = client.get_group(edit.domain)
    meta_invitation_id = domain.content.get('meta_invitation_id', {}).get('value')

    stage_name = edit.content['name']['value']

    client.post_group_edit(
        invitation=meta_invitation_id,
        signatures=[support_user],
        group=openreview.api.Group(
            id=domain.id,
            content={
                'reviewers_affinity_score_id': { 'value': f'{domain.id}/-/{stage_name}' }
            }
        )
    )

    edit_invitations_builder = openreview.workflows.EditInvitationsBuilder(client, domain.id)
    scores_invitation_id = f'{domain.id}/-/{stage_name}'
    edit_invitations_builder.set_edit_dates_one_level_invitation(scores_invitation_id, include_due_date=False)
    edit_invitations_builder.set_edit_affinities_settings_invitation(scores_invitation_id)
    edit_invitations_builder.set_edit_affinities_file_invitation(scores_invitation_id)