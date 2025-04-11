def process(client, invitation):

    now = openreview.tools.datetime_millis(datetime.datetime.utcnow())
    cdate = invitation.cdate

    if cdate > now:
        ## invitation is in the future, do not process
        print('invitation is not yet active', cdate)
        return
    
    client.post_invitation_edit(
        invitations=invitation.id,
        invitation=openreview.api.Invitation()
    )
