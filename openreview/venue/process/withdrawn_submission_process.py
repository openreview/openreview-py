def process(client, edit, invitation):

    VENUE_ID = ''
    PAPER_INVITATION_PREFIX = ''
    EXPIRE_INVITATION_ID = ''

    submission = client.get_note(edit.note.id)

    invitations = client.get_invitations(replyForum=submission.id, prefix=PAPER_INVITATION_PREFIX)

    now = openreview.tools.datetime_millis(datetime.datetime.utcnow())

    for invitation in invitations:
        print(f'Expiring invitation {invitation.id}')
        invitation.id = 'TestVenue.cc/Submission2/-/Official_Review'
        client.post_invitation_edit(
            invitations=EXPIRE_INVITATION_ID,
            invitation=openreview.api.Invitation(id=invitation.id,
                expdate=now
            )            
        )

    ## TODO: send emails to all the readers of the submission