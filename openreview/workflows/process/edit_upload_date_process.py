def process(client, edit, invitation):

    domain = client.get_group(edit.domain)
    venue_id = domain.id
    meta_invitation_id = domain.get_content_value('meta_invitation_id')

    invitation_id = invitation.id
    cdate = edit.content['upload_date']['value']

    # edit cdate when activation date is set
    client.post_invitation_edit(
        invitations=meta_invitation_id,
        signatures=[venue_id],
        invitation=openreview.api.Invitation(
            id=f'{venue_id}/-/Decision_Upload',
            cdate= cdate
        )
    )