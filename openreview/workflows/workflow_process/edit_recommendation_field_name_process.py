def process(client, edit, invitation):

    domain = client.get_group(edit.domain)
    venue_id = domain.id
    meta_invitation_id = domain.get_content_value('meta_invitation_id')
    meta_review_recommendation = edit.content['recommendation_field_name']['value']
    meta_review_name = domain.get_content_value('meta_review_name')

    client.post_group_edit(
        invitation = meta_invitation_id,
        signatures = [venue_id],
        group = openreview.api.Group(
            id = venue_id,
            content = {
                'meta_review_recommendation': {
                    'value': meta_review_recommendation
                }
            }
        )
    )

    senior_area_chairs_name = domain.get_content_value('senior_area_chairs_name')
    if senior_area_chairs_name:
        sac_acronym = ''.join([s[0].upper() for s in senior_area_chairs_name.split('_')])
        content = edit.content['content']['value']

        sac_revision_invitation_id = f'{venue_id}/-/{meta_review_name}_{sac_acronym}_Revision'
        invitation = client.get_invitation(sac_revision_invitation_id)
        if invitation:
            client.post_invitation_edit(
                invitations = meta_invitation_id,
                signatures = [venue_id],
                invitation = openreview.api.Invitation(
                    id = sac_revision_invitation_id,
                    edit = {
                        'invitation': {
                            'edit': {
                                'note': {
                                    'content': content
                                }
                            }
                        }
                    }
                )
            )