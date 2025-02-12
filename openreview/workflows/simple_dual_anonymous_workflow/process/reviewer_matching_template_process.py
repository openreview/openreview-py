def process(client, edit, invitation):

    domain = client.get_group(edit.domain)
    meta_invitation_id = domain.content.get('meta_invitation_id', {}).get('value')

    stage_name = edit.content['name']['value']

    edit_invitations_builder = openreview.workflows.EditInvitationsBuilder(client, domain.id)
    assignment_invitation_id = f'{domain.id}/-/{stage_name}'
    edit_invitations_builder.set_edit_assignment_match_settings_invitation(assignment_invitation_id)

    # add link to assignments page in invitation description
    link = f'https://openreview.net/assignments?group={domain.id}/Reviewers'
    description = f'<span class="text-muted">First create draft reviewer assignments <a href={link}>here</a>. Once assignments have been finalized, deploy them.</span>'

    client.post_invitation_edit(
        invitations=meta_invitation_id,
        signatures=[domain.id],
        invitation=openreview.api.Invitation(
            id=assignment_invitation_id,
            description=description
        )
    )