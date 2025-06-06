def process(client, edit, invitation):

    domain = client.get_group(edit.domain)
    venue_id = domain.id
    meta_invitation_id = domain.get_content_value('meta_invitation_id')
    cdate = edit.invitation.cdate
    desk_rejected_submission_id = domain.get_content_value('desk_rejected_submission_id')

    # update desk rejected submission cdate
    client.post_invitation_edit(
        invitations=meta_invitation_id,
        signatures=[venue_id],
        invitation=openreview.api.Invitation(
            id=desk_rejected_submission_id,
            signatures=[venue_id],
            cdate=cdate
        )
    )