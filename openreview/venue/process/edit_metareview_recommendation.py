def process(client, edit, invitation):

    domain = client.get_group(edit.domain)
    venue_id = domain.id
    meta_invitation_id = domain.get_content_value('meta_invitation_id')
    recommendation_field_name = edit.content['recommendation_field_name']['value']

    client.post_group_edit(
        invitation = meta_invitation_id,
        signatures = [venue_id],
        group = openreview.api.Group(
            id = venue_id,
            content = {
                'meta_review_recommendation': {
                    'value': recommendation_field_name
                }
            }
        )
    )

