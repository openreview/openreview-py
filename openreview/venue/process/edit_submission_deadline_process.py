def process(client, edit, invitation):

    domain = client.get_group(edit.domain)
    venue_id = domain.id
    meta_invitation_id = domain.get_content_value('meta_invitation_id')
    submission_id = edit.invitation.id
    duedate = edit.invitation.duedate

    expdate = duedate + (30*60*1000)

    # update submission expdate
    client.post_invitation_edit(
        invitations=meta_invitation_id,
        signatures=[venue_id],
        invitation=openreview.api.Invitation(
            id=submission_id,
            expdate=expdate
        )
    )

    # update post submission cdate