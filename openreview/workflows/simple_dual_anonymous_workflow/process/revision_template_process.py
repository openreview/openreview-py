def process(client, edit, invitation):

    domain = client.get_group(edit.domain)

    stage_name = edit.content['name']['value']

    edit_invitations_builder = openreview.workflows.EditInvitationsBuilder(client, domain.id)
    revision_invitation_id = f'{domain.id}/-/{stage_name}'

    content = {
        'source': {
            'value': {
                'param': {
                    'type': 'string',
                    'enum': [
                        'all_submissions',
                        'accepted_submissions'
                    ],
                    'input': 'select'
                }
            }
        }
    }
    edit_invitations_builder.set_edit_content_invitation(revision_invitation_id, content)
    edit_invitations_builder.set_edit_dates_invitation(revision_invitation_id)

