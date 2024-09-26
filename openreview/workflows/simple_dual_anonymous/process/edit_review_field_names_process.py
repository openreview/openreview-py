def process(client, edit, invitation):

    domain = client.get_group(edit.domain)
    venue_id = domain.id
    meta_invitation_id = domain.get_content_value('meta_invitation_id')
    review_rating = edit.content['review_rating']['value']
    review_confidence = edit.content['review_confidence']['value']

    client.post_group_edit(
        invitation = meta_invitation_id,
        signatures = [venue_id],
        group = openreview.api.Group(
            id = venue_id,
            content = {
                'review_rating': {
                    'value': review_rating
                },
                'review_confidence': {
                    'value': review_confidence
                }
            }
        )
    )