def process(client, edit, invitation):

    domain = client.get_group(edit.domain)
    venue_id = domain.id
    meta_invitation_id = domain.get_content_value('meta_invitation_id')
    rating_field_name = edit.content['rating_field_name']['value']
    confidence_field_name = edit.content['confidence_field_name']['value']

    client.post_group_edit(
        invitation = meta_invitation_id,
        signatures = [venue_id],
        group = openreview.api.Group(
            id = venue_id,
            content = {
                'review_rating': {
                    'value': rating_field_name
                },
                'review_confidence': {
                    'value': confidence_field_name
                }
            }
        )
    )

