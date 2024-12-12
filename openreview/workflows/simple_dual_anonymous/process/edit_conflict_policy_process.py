def process(client, edit, invitation):

    domain = client.get_group(edit.domain)
    venue_id = domain.id
    meta_invitation_id = domain.get_content_value('meta_invitation_id')
    conflict_policy = edit.content['conflict_policy']['value']
    conflict_n_years = edit.content['conflict_n_years']['value']

    client.post_group_edit(
        invitation = meta_invitation_id,
        signatures = [venue_id],
        group = openreview.api.Group(
            id = venue_id,
            content = {
                'reviewers_conflict_policy': {
                    'value': conflict_policy
                },
                'reviewers_conflict_n_years': {
                    'value': conflict_n_years
                }
            }
        )
    )