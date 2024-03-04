def process(client, invitation):
    import datetime

    domain = client.get_group(invitation.domain)
    venue_id = domain.id
    submission_venue_id = domain.content['submission_venue_id']['value']
    meta_invitation_id = domain.content['meta_invitation_id']['value']
    venue_name = domain.content['title']['value']
    request_form_id = domain.content['request_form_id']['value']

    client.post_invitation_edit(
        invitations=meta_invitation_id,
        signatures=[venue_id],
        invitation=openreview.api.Invitation(id=f'{venue_id}/-/Preprint_Release_Submission',
            cdate=invitation.content['preprint_release_submission_date']['value'],
            signatures=[venue_id]
        )
    )