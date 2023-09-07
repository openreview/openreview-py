def process(client, edit, invitation):

    domain = client.get_group(edit.domain)
    venue_id = domain.id
    short_name = domain.content['subtitle']['value']
    desk_rejected_submission_id = domain.content['desk_rejected_submission_id']['value']
    desk_reject_expiration_id = domain.content['desk_reject_expiration_id']['value']
    desk_reject_committee = domain.content['desk_reject_committee']['value']
    submission_name = domain.content['submission_name']['value']
    authors_name = domain.content['authors_name']['value']

    now = openreview.tools.datetime_millis(datetime.datetime.utcnow())
    submission = client.get_note(edit.note.forum)
    paper_group_id=f'{venue_id}/{submission_name}{submission.number}'    

    submission_edits = client.get_note_edits(note_id=submission.id, invitation=desk_rejected_submission_id)
    for submission_edit in submission_edits:
        print(f'remove edit {submission_edit.id}')
        submission_edit.ddate = now
        submission_edit.note.mdate = None
        submission_edit.note.cdate = None
        submission_edit.note.forum = None
        client.post_edit(submission_edit)

    invitations = client.get_invitations(replyForum=submission.id, invitation=desk_reject_expiration_id, expired=True)

    for expired_invitation in invitations:
        print(f'Remove expiration invitation {expired_invitation.id}')
        invitation_edits = client.get_invitation_edits(invitation_id=expired_invitation.id, invitation=desk_reject_expiration_id)
        for invitation_edit in invitation_edits:
            print(f'remove edit {edit.id}')
            invitation_edit.ddate = now
            invitation_edit.invitation.expdate = None
            invitation_edit.invitation.cdate = None
            client.post_edit(invitation_edit)

    formatted_committee = [committee.format(number=submission.number) for committee in desk_reject_committee]
    final_committee = []
    for group in formatted_committee:
        if openreview.tools.get_group(client, group):
            final_committee.append(group)

    email_subject = f'''[{short_name}]: Paper #{submission.number} restored by venue organizers'''
    email_body = f'''The desk-rejected {short_name} paper "{submission.content.get('title', {}).get('value', '#'+str(submission.number))}" has been restored by the venue organizers.

For more information, click here https://openreview.net/forum?id={submission.id}
'''

    client.post_message(email_subject, final_committee, email_body)

    print(f'Add {paper_group_id}/{authors_name} to {venue_id}/{authors_name}')
    client.add_members_to_group(f'{venue_id}/{authors_name}', f'{paper_group_id}/{authors_name}')