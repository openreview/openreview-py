def process(client, edit, invitation):

    EXPIRE_INVITATION_ID = ''
    WITHDRAWN_INVITATION_ID = ''

    now = openreview.tools.datetime_millis(datetime.datetime.utcnow())
    submission = client.get_note(edit.note.forum)

    submission_edits = client.get_note_edits(note_id=submission.id, invitation=WITHDRAWN_INVITATION_ID)
    for submission_edit in submission_edits:
        print(f'remove edit {submission_edit.id}')
        submission_edit.ddate = now
        submission_edit.note.mdate = None
        client.post_edit(submission_edit)             
    
    invitations = client.get_invitations(replyForum=submission.id, invitation=EXPIRE_INVITATION_ID, expired=True)

    for expired_invitation in invitations:
        print(f'Remove expiration invitation {expired_invitation.id}')
        invitation_edits = client.get_invitation_edits(invitation_id=expired_invitation.id, invitation=EXPIRE_INVITATION_ID)
        for invitation_edit in invitation_edits:
            print(f'remove edit {edit.id}')
            invitation_edit.ddate = now
            client.post_edit(invitation_edit)    

