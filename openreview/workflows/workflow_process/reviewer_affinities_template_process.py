def process(client, edit, invitation):

    domain = client.get_group(edit.domain)
    meta_invitation_id = domain.content.get('meta_invitation_id', {}).get('value')
    reviewers_name = domain.get_content_value('reviewers_name')

    stage_name = edit.content['name']['value']

    client.post_group_edit(
        invitation=meta_invitation_id,
        signatures=[invitation.domain],
        group=openreview.api.Group(
            id=domain.id,
            content={
                'reviewers_affinity_score_id': { 'value': f'{domain.id}/{reviewers_name}/-/{stage_name}' },
                'reviewers_custom_max_papers_id': { 'value': f'{domain.id}/{reviewers_name}/-/Custom_Max_Papers' }
            }
        )
    )

    edit_invitations_builder = openreview.workflows.EditInvitationsBuilder(client, domain.id)
    scores_invitation_id = f'{domain.id}/{reviewers_name}/-/{stage_name}'
    edit_invitations_builder.set_edit_affinities_settings_invitation(scores_invitation_id)
    edit_invitations_builder.set_edit_dates_one_level_invitation(scores_invitation_id)