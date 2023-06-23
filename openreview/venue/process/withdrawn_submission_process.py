def process(client, edit, invitation):

    domain = client.get_group(edit.domain)
    venue_id = domain.id
    short_name = domain.content['subtitle']['value']
    withdraw_reversion_id = domain.content['withdraw_reversion_id']['value']
    withdraw_expiration_id = domain.content['withdraw_expiration_id']['value']
    withdraw_committee = domain.content['withdraw_committee']['value']
    withdrawal_name = domain.content['withdrawal_name']['value']
    submission_name = domain.content['submission_name']['value']
    authors_name = domain.content['authors_name']['value']
    withdrawal_email_pcs = domain.content.get('withdrawal_email_pcs', {}).get('value')
    program_chairs_id = domain.content['program_chairs_id']['value']

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

    print(f'Remove {paper_group_id}/{authors_name} from {venue_id}/{authors_name}')
    client.remove_members_from_group(f'{venue_id}/{authors_name}', f'{paper_group_id}/{authors_name}')

    formatted_committee = [committee.format(number=submission.number) for committee in withdraw_committee]
    final_committee = []
    for group in formatted_committee:
        if openreview.tools.get_group(client, group):
            final_committee.append(group)

    ignoreRecipients = [program_chairs_id] if not withdrawal_email_pcs else []
    
    email_subject = f'''[{short_name}]: Paper #{submission.number} withdrawn by paper authors'''
    email_body = f'''The {short_name} paper "{submission.content.get('title', {}).get('value', '#'+str(submission.number))}" has been withdrawn by the paper authors.

For more information, click here https://openreview.net/forum?id={submission.id}&noteId={withdrawal_notes[0].id}
'''

    client.post_message(email_subject, final_committee, email_body, ignoreRecipients=ignoreRecipients)
