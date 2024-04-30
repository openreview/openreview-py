def process(client, edit, invitation):
   
    submission_id = edit.invitation.id
    duedate = edit.invitation.duedate

    expdate = duedate + (30*60*1000)

    # should we update expdate when we update duedate
    client.post_invitation_edit(
        invitations=f'{submission_id}/Expiration',
        invitation=openreview.api.Invitation(id=submission_id,
            expdate=expdate
        )
    )