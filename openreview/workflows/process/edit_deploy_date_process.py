def process(client, edit, invitation):

    domain = client.get_group(edit.domain)
    venue_id = domain.id
    meta_invitation_id = domain.get_content_value('meta_invitation_id')
    reviewers_name = domain.get_content_value('reviewers_name')

    invitation_id = invitation.id
    cdate = edit.content['deploy_date']['value']

    # edit cdate when activation date is set
    client.post_invitation_edit(
        invitations=meta_invitation_id,
        signatures=[venue_id],
        invitation=openreview.api.Invitation(
            id=f'{venue_id}/-/{reviewers_name}_Assignment_Deployment',
            cdate= cdate
        )
    )