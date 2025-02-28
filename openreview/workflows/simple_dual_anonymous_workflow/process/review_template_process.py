def process(client, edit, invitation):

    support_user = f'{invitation.domain}/Support'
    domain = client.get_group(edit.domain)
    meta_invitation_id = domain.content.get('meta_invitation_id', {}).get('value')

    stage_name = edit.content['name']['value']
    client.post_group_edit(
        invitation=meta_invitation_id,
        signatures=[support_user],
        group=openreview.api.Group(
            id=domain.id,
            content={
                'review_name': { 'value': stage_name },
                'review_rating': { 'value': 'rating' },
                'review_confidence': { 'value': 'confidence' }
            }
        )
    )

    edit_invitations_builder = openreview.workflows.EditInvitationsBuilder(client, domain.id)
    review_invitation_id = f'{domain.id}/-/{stage_name}'
    edit_invitations_builder.set_edit_dates_invitation(review_invitation_id)
    content = {
        'review_rating': {
            'value': {
                'param': {
                    'type': 'string',
                    'regex': '.*',
                    'default': 'rating'
                }
            }
        },
        'review_confidence': {
            'value': {
                'param': {
                    'type': 'string',
                    'regex': '.*',
                    'default': 'confidence'
                }
            }
        }
    }
    edit_invitations_builder.set_edit_content_invitation(review_invitation_id, content, 'simple_dual_anonymous_workflow/process/edit_review_field_names_process.py')
    edit_invitations_builder.set_edit_reply_readers_invitation(review_invitation_id)
    edit_invitations_builder.set_edit_email_settings_invitation(review_invitation_id, email_pcs=True)