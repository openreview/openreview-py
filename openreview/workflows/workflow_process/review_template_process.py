def process(client, edit, invitation):

    domain = client.get_group(edit.domain)
    meta_invitation_id = domain.content.get('meta_invitation_id', {}).get('value')

    stage_name = edit.content['name']['value']
    client.post_group_edit(
        invitation=meta_invitation_id,
        signatures=[invitation.domain],
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

    cdate = edit.content['activation_date']['value']-1800000 # 30 min before cdate

    edit_invitations_builder.set_edit_content_invitation(review_invitation_id, content, 'workflow_process/edit_review_field_names_process.py', due_date=cdate)
    edit_invitations_builder.set_edit_reply_readers_invitation(review_invitation_id, due_date=cdate)
    edit_invitations_builder.set_edit_email_settings_invitation(review_invitation_id, email_pcs=True, due_date=cdate)
    edit_invitations_builder.set_edit_dates_invitation(review_invitation_id, due_date=cdate)