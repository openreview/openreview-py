def process(client, edit, invitation):

    domain = client.get_group(edit.domain)
    venue_id = domain.id
    meta_invitation_id = domain.get_content_value('meta_invitation_id')
    accept_decision_options = edit.content['accept_decision_options']['value']

    client.post_group_edit(
        invitation = meta_invitation_id,
        signatures = [venue_id],
        group = openreview.api.Group(
            id = venue_id,
            content = {
                'accept_decision_options': {
                    'value': accept_decision_options
                }
            }
        )
    )

    endorsement_invitation_id = f'{venue_id}/-/Article_Endorsement'
    endorsement_invitation = client.get_invitation(endorsement_invitation_id)
    endorsement_invitation.edit['label']['param']['enum'] = accept_decision_options
    client.post_invitation_edit(
        invitations = meta_invitation_id,
        signatures = [venue_id],
        invitation = endorsement_invitation
    )