def process(client, edit, invitation):

    domain = client.get_group(edit.domain)
    venue_id = domain.id
    short_name = domain.content['subtitle']['value']
    withdraw_reversion_id = domain.content['withdraw_reversion_id']['value']
    withdraw_expiration_id = domain.content['withdraw_expiration_id']['value']
    withdraw_committee = domain.content['withdraw_committee']['value']
    withdrawal_name = domain.content['withdrawal_name']['value']
    submission_name = domain.content['submission_name']['value']

    submission = client.get_note(edit.note.id)
    paper_group_id=f'{venue_id}/{submission_name}{submission.number}'    

    invitations = client.get_invitations(replyForum=submission.id, prefix=paper_group_id)

    now = openreview.tools.datetime_millis(datetime.datetime.utcnow())

    for invitation in invitations:
        print(f'Expiring invitation {invitation.id}')
        client.post_invitation_edit(
            invitations=withdraw_expiration_id,
            invitation=openreview.api.Invitation(id=invitation.id,
                expdate=now
            )            
        )

    formatted_committee = [committee.format(number=submission.number) for committee in withdraw_committee]
    email_subject = f'''[{short_name}]: Paper #{submission.number} withdrawn by paper authors'''
    email_body = f'''The {short_name} paper "{submission.content.get('title', {}).get('value', '#'+str(submission.number))}" has been withdrawn by the paper authors.

For more information, click here https://openreview.net/forum?id={submission.id}
'''

    client.post_message(email_subject, formatted_committee, email_body)    

    withdrawal_notes = client.get_notes(forum=submission.id, invitation=f'{paper_group_id}/-/{withdrawal_name}')
    if withdrawal_notes:
        print(f'Create withdrawal reversion invitation')
        client.post_invitation_edit(
            invitations=withdraw_reversion_id,
            content={
                'noteId': {
                    'value': submission.id
                },                
                'withdrawalId': {
                    'value': withdrawal_notes[0].id
                }
            }
        )