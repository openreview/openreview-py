def process(client, edit, invitation):

    domain = client.get_group(edit.domain)
    invitation_id = edit.invitation.id
    meta_invitation_id = domain.content.get('meta_invitation_id', {}).get('value')
    rejected_venue_id = domain.content.get('rejected_venue_id', {}).get('value')
    submission_venue_id = domain.content.get('submission_venue_id', {}).get('value')

    with_decision_accept = edit.content['decision_option']['value'] == 'Accepted'

    client.post_invitation_edit(
        invitations=meta_invitation_id,
        signatures = [domain.id],
        invitation=openreview.api.Invitation(
            id=invitation_id,
            content={
                'source': {
                    'value': {
                        'venueid': [submission_venue_id, domain.id, rejected_venue_id],
                        'with_decision_accept': with_decision_accept
                    }
                }
            }
        )
    )

    edit_invitations_builder = openreview.workflows.EditInvitationsBuilder(client, domain.id)
    edit_invitations_builder.set_edit_dates_one_level_invitation(invitation_id)
    content = {
        'reveal_author_identities': {
            'description': 'Select whether you want to reveal the author identities to the readers of the submissions. If you select False, author identities will remain visible only to the program chairs and the paper authors.',
            'value': {
                'param': {
                    'type': 'boolean'
                }
            }
        }
    }
    edit_invitations_builder.set_edit_submission_readers_invitation(invitation_id, True, content)
    # edit_invitations_builder.set_edit_reveal_authors(invitation_id)