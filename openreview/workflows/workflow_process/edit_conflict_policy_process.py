def process(client, edit, invitation):

    domain = client.get_group(edit.domain)
    venue_id = domain.id
    meta_invitation_id = domain.get_content_value('meta_invitation_id')
    committee_id = invitation.id.split('/-/')[0]
    committee_group = client.get_group(committee_id)
    committee_role = committee_group.content['committee_role']['value']
    conflict_policy = edit.content['conflict_policy']['value']
    conflict_n_years = edit.content['conflict_n_years']['value']

    client.post_group_edit(
        invitation = meta_invitation_id,
        signatures = [venue_id],
        group = openreview.api.Group(
            id = venue_id,
            content = {
                f'{committee_role}_conflict_policy': {
                    'value': conflict_policy
                },
                f'{committee_role}_conflict_n_years': {
                    'value': conflict_n_years
                }
            }
        )
    )