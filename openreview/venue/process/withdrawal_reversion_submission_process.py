def process(client, edit, invitation):

    domain = client.get_group(edit.domain)
    short_name = domain.content['subtitle']['value']
    withdrawn_submission_id = domain.content['withdrawn_submission_id']['value']
    withdraw_expiration_id = domain.content['withdraw_expiration_id']['value']
    withdraw_committee = domain.content['withdraw_committee']['value']

    now = openreview.tools.datetime_millis(datetime.datetime.utcnow())
    submission = client.get_note(edit.note.forum)

    submission_edits = client.get_note_edits(note_id=submission.id, invitation=withdrawn_submission_id)
    for submission_edit in submission_edits:
        print(f'remove edit {submission_edit.id}')
        submission_edit.ddate = now
        submission_edit.note.mdate = None
        submission_edit.note.forum = None
        client.post_edit(submission_edit)             
    
    invitations = client.get_invitations(replyForum=submission.id, invitation=withdraw_expiration_id, expired=True)

    for expired_invitation in invitations:
        print(f'Remove expiration invitation {expired_invitation.id}')
        invitation_edits = client.get_invitation_edits(invitation_id=expired_invitation.id, invitation=withdraw_expiration_id)
        for invitation_edit in invitation_edits:
            print(f'remove edit {edit.id}')
            invitation_edit.ddate = now
            client.post_edit(invitation_edit)

    formatted_committee = [committee.format(number=submission.number) for committee in withdraw_committee]
    email_subject = f'''[{short_name}]: Paper #{submission.number} restored by venue organizers'''
    email_body = f'''The {short_name} paper "{submission.content.get('title', {}).get('value', '#'+str(submission.number))}" has been restored by the venue organizers.

For more information, click here https://openreview.net/forum?id={submission.id}
'''

    client.post_message(email_subject, formatted_committee, email_body)               

