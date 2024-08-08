def process(client, edit, invitation):

    support_user = 'openreview.net/Support'
    domain = client.get_group(edit.domain)
    meta_invitation_id = domain.content.get('meta_invitation_id', {}).get('value')

    client.post_group_edit(
        invitation=meta_invitation_id,
        signatures=[support_user],
        group=openreview.api.Group(
            id=domain.id,
            content={
                'review_name': { 'value': edit.content['name']['value'] },
                'review_rating': { 'value': 'rating' },
                'review_confidence': { 'value': 'confidence' }
            }
        )
    )