def process(client, edit, invitation):

    domain = client.get_group(edit.domain)
    venue_id = domain.id
    meta_invitation_id = domain.content['meta_invitation_id']['value']
    short_name = domain.content['subtitle']['value']
    contact = domain.content['contact']['value']
    desk_rejection_reversion_id = domain.content['desk_rejection_reversion_id']['value']
    desk_reject_expiration_id = domain.content['desk_reject_expiration_id']['value']
    desk_reject_committee = domain.content['desk_reject_committee']['value']
    desk_rejection_name = domain.content['desk_rejection_name']['value']
    submission_name = domain.content['submission_name']['value']
    authors_name = domain.content['authors_name']['value']
    desk_rejection_email_pcs = domain.content.get('desk_rejection_email_pcs', {}).get('value')
    program_chairs_id = domain.content['program_chairs_id']['value']
    sender = domain.get_content_value('message_sender')
    authors_accepted_id = domain.get_content_value('authors_accepted_id')
    release_to_ethics_chairs = domain.get_content_value('release_submissions_to_ethics_chairs')

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
    client.remove_members_from_group(authors_accepted_id, f'{paper_group_id}/{authors_name}')

    formatted_committee = [committee.format(number=submission.number) for committee in desk_reject_committee]
    final_committee = []
    for group in formatted_committee:
        if openreview.tools.get_group(client, group):
            final_committee.append(group)

    ignoreRecipients = [program_chairs_id] if not desk_rejection_email_pcs else []

    email_subject = f'''[{short_name}]: Paper #{submission.number} desk-rejected by {pretty_signature}'''
    email_body = f'''The {short_name} paper "{submission.content.get('title', {}).get('value', '#'+str(submission.number))}" has been desk-rejected by {pretty_signature}.

For more information, click here https://openreview.net/forum?id={submission.id}
'''

    client.post_message(email_subject, final_committee, email_body, invitation=meta_invitation_id, signature=venue_id, ignoreRecipients=ignoreRecipients, replyTo=contact, sender=sender)

    if submission.content.get('flagged_for_ethics_review', {}).get('value'):

        if release_to_ethics_chairs and 'everyone' not in submission.readers:
            ethics_chairs_id = domain.get_content_value('ethics_chairs_id')

            client.post_note_edit(invitation=meta_invitation_id,
                signatures=[venue_id],
                note=openreview.api.Note(
                    id=submission.id,
                    readers={
                        'append': [ethics_chairs_id]
                    }
                )
            )

        # email ethics chairs
        client.post_message(email_subject, [ethics_chairs_id], email_body, invitation=meta_invitation_id, signature=venue_id, ignoreRecipients=ignoreRecipients, replyTo=contact, sender=sender)