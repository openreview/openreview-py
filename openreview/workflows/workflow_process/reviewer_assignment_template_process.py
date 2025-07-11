def process(client, edit, invitation):

    domain = client.get_group(edit.domain)
    meta_invitation_id = domain.content.get('meta_invitation_id', {}).get('value')

    stage_name = edit.content['name']['value']
    reviewers_name = edit.content['reviewers_name']['value']

    edit_invitations_builder = openreview.workflows.EditInvitationsBuilder(client, domain.id)
    assignment_invitation_id = f'{domain.id}/{reviewers_name}/-/{stage_name}'
    edit_invitations_builder.set_edit_dates_one_level_invitation(assignment_invitation_id, include_exp_date=True)

    # add link to assignments page in Assignment invitation description
    baseurl = client.baseurl.replace('devapi2.', 'dev.').replace('api2.', '').replace('3001', '3030')
    link = f'{baseurl}/assignments?group={domain.id}/{reviewers_name}'
    description = f'<span>Create draft reviewer assignments <a href={link}>here</a>.</span>'

    client.post_invitation_edit(
        invitations=meta_invitation_id,
        signatures=[domain.id],
        invitation=openreview.api.Invitation(
            id=assignment_invitation_id,
            description=description
        )
    )