def process(client, edit, invitation):

    domain = client.get_group(edit.domain)
    venue_id = domain.id
    short_name = domain.content['subtitle']['value']
    desk_rejection_reversion_id = domain.content['desk_rejection_reversion_id']['value']
    desk_reject_expiration_id = domain.content['desk_reject_expiration_id']['value']
    desk_reject_committee = domain.content['desk_reject_committee']['value']
    desk_rejection_name = domain.content['desk_rejection_name']['value']
    submission_name = domain.content['submission_name']['value']    

    submission = client.get_note(edit.note.id)
    paper_group_id=f'{venue_id}/{submission_name}{submission.number}'

    invitations = client.get_invitations(replyForum=submission.id, prefix=paper_group_id)

    now = openreview.tools.datetime_millis(datetime.datetime.utcnow())

    for invitation in invitations:
        print(f'Expiring invitation {invitation.id}')
        client.post_invitation_edit(
            invitations=desk_reject_expiration_id,
            invitation=openreview.api.Invitation(id=invitation.id,
                expdate=now
            )
        )

    formatted_committee = [committee.format(number=submission.number) for committee in desk_reject_committee]
    email_subject = f'''[{short_name}]: Paper #{submission.number} desk-rejected by program chairs'''
    email_body = f'''The {short_name} paper "{submission.content.get('title', {}).get('value', '#'+str(submission.number))}" has been desk-rejected by the program chairs.

For more information, click here https://openreview.net/forum?id={submission.id}
'''

    client.post_message(email_subject, formatted_committee, email_body)

    desk_rejection_notes = client.get_notes(forum=submission.id, invitation=f'{paper_group_id}/-/{desk_rejection_name}')
    if desk_rejection_notes:
        print(f'Create desk-rejection reversion invitation')
        client.post_invitation_edit(
            invitations=desk_rejection_reversion_id,
            content={
                'noteId': {
                    'value': submission.id
                },
                'deskRejectionId': {
                    'value': desk_rejection_notes[0].id
                }
            }
        )