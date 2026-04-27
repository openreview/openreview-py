def process(client, edit, invitation):

    domain = client.get_group(edit.domain)
    invitation_id = edit.invitation.id
    meta_invitation_id = domain.content.get('meta_invitation_id', {}).get('value')


    with_decision_accept = edit.content['decision_option']['value'] == 'Accepted'

    client.post_invitation_edit(
        invitations=meta_invitation_id,
        signatures = [domain.id],
        invitation=openreview.api.Invitation(
            id=invitation_id,
            content={
                'source': {
                    'value': {
                        'with_decision_accept': with_decision_accept
                    }
                }
            }
        )
    )

    edit_invitations_builder = openreview.workflows.EditInvitationsBuilder(client, domain.id)
    edit_invitations_builder.set_edit_dates_one_level_invitation(invitation_id)
    edit_invitations_builder.set_edit_submission_readers_invitation(invitation_id, True)
    edit_invitations_builder.set_edit_reveal_authors(invitation_id)