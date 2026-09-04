def process(client, edit, invitation):

    domain = client.get_group(edit.domain)
    venue_id = domain.id
    meta_invitation_id = domain.get_content_value('meta_invitation_id')
    
    submission_content = edit.content['content']['value']
    submission_license = edit.content['license']['value']

    ## a 'track' field on the submission form lets each committee group be restricted to one track
    track_options = submission_content.get('track', {}).get('value', {}).get('param', {}).get('enum')
    if track_options:
        edit_invitations_builder = openreview.workflows.EditInvitationsBuilder(client, venue_id)
        committee_roles = domain.get_content_value('reviewer_roles', []) + domain.get_content_value('area_chair_roles', []) + domain.get_content_value('senior_area_chair_roles', [])
        for role in committee_roles:
            edit_invitations_builder.set_edit_track_invitation(f'{venue_id}/{role}', track_options=track_options)

    pc_submission_revision_id = domain.get_content_value('pc_submission_revision_id')
    if pc_submission_revision_id:
        client.post_invitation_edit(
            invitations=meta_invitation_id,
            signatures=[venue_id],
            invitation=openreview.api.Invitation(
                id=pc_submission_revision_id,
                signatures=[venue_id],
                edit={
                    'note': {
                        'content': submission_content,
                        'license': {
                            'param': {
                                'enum': submission_license
                            }
                        }
                    }
                }
            )
        )