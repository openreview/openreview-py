def process(client, edit, invitation):

    support_user = 'openreview.net/Support'
    domain = client.get_group(edit.domain)
    meta_invitation_id = domain.content.get('meta_invitation_id', {}).get('value')

    stage_name = edit.content['name']['value']

    client.post_group_edit(
        invitation=meta_invitation_id,
        signatures=[support_user],
        group=openreview.api.Group(
            id=domain.id,
            content={
                'decision_name': { 'value': stage_name },
                'decision_field_name': { 'value': 'decision' }
            }
        )
    )

    edit_invitations_builder = openreview.workflows.EditInvitationsBuilder(client, domain.id)
    decision_invitation_id = f'{domain.id}/-/{stage_name}'
    edit_invitations_builder.set_edit_dates_invitation(decision_invitation_id)
    content = {
        'rating_field_name': {
            'value': {
                'param': {
                    'type': 'string',
                    'regex': '.*',
                    'default': 'rating'
                }
            }
        },
        'confidence_field_name': {
            'value': {
                'param': {
                    'type': 'string',
                    'regex': '.*',
                    'default': 'confidence'
                }
            }
        }
    }
    edit_invitations_builder.set_edit_reply_readers_invitation(decision_invitation_id)
    edit_invitations_builder.set_edit_decisions_file_invitation(decision_invitation_id)