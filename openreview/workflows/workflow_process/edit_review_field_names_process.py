def process(client, edit, invitation):

    domain = client.get_group(edit.domain)
    venue_id = domain.id
    meta_invitation_id = domain.get_content_value('meta_invitation_id')
    review_rating = edit.content['rating_field_name']['value']
    review_confidence = edit.content['confidence_field_name']['value']
    review_name = domain.get_content_value('review_name')

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

    review_invitation = client.get_invitation(f'{venue_id}/-/{review_name}')
    fields = list(review_invitation.edit['invitation']['edit']['note']['content'].keys())

    client.post_invitation_edit(
        invitations=meta_invitation_id,
        signatures=[venue_id],
        invitation=openreview.api.Invitation(
            id=f'{venue_id}/-/Author_Reviews_Notification/Fields_to_Include',
            edit = {
                'content': {
                    'fields': {
                        'value': {
                            'param': {
                                'type': 'string[]',
                                'enum': fields
                            }
                        }
                    }
                }
            }
        )
    )