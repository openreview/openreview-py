def process(client, edit, invitation):

    domain = client.get_group(edit.domain)
    venue_id = domain.id
    meta_invitation_id = domain.get_content_value('meta_invitation_id')
    cdate = edit.invitation.cdate
    submission_name = domain.get_content_value('submission_name', 'Submission')


    # update desk rejected submission cdate
    client.post_invitation_edit(
        invitations=meta_invitation_id,
        signatures=[venue_id],
        invitation=openreview.api.Invitation(
            id=f'{venue_id}/-/Desk_Rejected_{submission_name}',
            signatures=[venue_id],
            cdate=cdate
        )
    )