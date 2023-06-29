def process(client, edit, invitation):

    domain = client.get_group(edit.domain)
    venue_id = domain.id
    short_name = domain.content['subtitle']['value']
    desk_rejection_reversion_id = domain.content['desk_rejection_reversion_id']['value']
    desk_reject_expiration_id = domain.content['desk_reject_expiration_id']['value']
    desk_reject_committee = domain.content['desk_reject_committee']['value']
    desk_rejection_name = domain.content['desk_rejection_name']['value']
    submission_name = domain.content['submission_name']['value']
    authors_name = domain.content['authors_name']['value']

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

    signature = desk_rejection_notes[0].signatures[0].split('/')[-1]
    pretty_signature = openreview.tools.pretty_id(signature)

    print(f'Remove {paper_group_id}/{authors_name} from {venue_id}/{authors_name}')
    client.remove_members_from_group(f'{venue_id}/{authors_name}', f'{paper_group_id}/{authors_name}')

    formatted_committee = [committee.format(number=submission.number) for committee in desk_reject_committee]
    final_committee = []
    for group in formatted_committee:
        if openreview.tools.get_group(client, group):
            final_committee.append(group)
    email_subject = f'''[{short_name}]: Paper #{submission.number} desk-rejected by {pretty_signature}'''
    email_body = f'''The {short_name} paper "{submission.content.get('title', {}).get('value', '#'+str(submission.number))}" has been desk-rejected by {pretty_signature}.

For more information, click here https://openreview.net/forum?id={submission.id}
'''

    client.post_message(email_subject, final_committee, email_body)