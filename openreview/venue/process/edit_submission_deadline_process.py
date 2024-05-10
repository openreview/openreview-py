def process(client, edit, invitation):

    domain = client.get_group(edit.domain)
    venue_id = domain.id
    meta_invitation_id = domain.get_content_value('meta_invitation_id')
    submission_name = domain.get_content_value('submission_name')
    expdate = edit.invitation.expdate

    # update post submission cdate
    client.post_invitation_edit(
        invitations=meta_invitation_id,
        signatures=[venue_id],
        invitation=openreview.api.Invitation(
            id=f'{venue_id}/-/Post_{submission_name}',
            cdate=expdate
        )
    )