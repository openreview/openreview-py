def process(client, edit, invitation):

    domain = client.get_group(edit.domain)
    venue_id = domain.id
    short_name = domain.get_content_value('subtitle')
    contact = domain.get_content_value('contact')
    meta_invitation_id = domain.get_content_value('meta_invitation_id')
    sender = domain.get_content_value('message_sender')
    submission_name = domain.get_content_value('submission_name')
    comment_email_pcs = domain.get_content_value('comment_email_pcs')
    comment_email_sacs = domain.get_content_value('comment_email_sacs')
    program_chairs_id = domain.get_content_value('program_chairs_id')
    senior_area_chairs_name = domain.get_content_value('senior_area_chairs_name')

    submission = client.get_note(edit.note.forum)
    comment = client.get_note(edit.note.id)

    ignore_recipients = comment.signatures + ([program_chairs_id] if not comment_email_pcs else [])
    if not comment_email_sacs and senior_area_chairs_name:
        ignore_recipients.append(f'{venue_id}/{submission_name}{submission.number}/{senior_area_chairs_name}')

    final_recipients = []
    for group in comment.readers:
        if openreview.tools.get_group(client, group):
            final_recipients.append(group)

    invitation = client.get_invitation(invitation.id)
    if invitation.date_processes[0].get('cron') is None:
        ## Activate date process to run every 4 hours
        print('update cron job tu run every 4 hours')
        client.post_invitation_edit (
            invitations=meta_invitation_id,
            signatures=[venue_id],
            invitation=openreview.api.Invitation(
                id=invitation.id,
                date_processes = [{
                    'cron': '0 */4 * * *',
                    'script': invitation.date_processes[0].get('script')
                }]
            )
        )      

    if comment.number == 1:
        print('Send initial comment email')

        client.post_message(
            invitation=meta_invitation_id,
            subject = f'[{short_name}] New conversation in committee members chat for submission {submission.number}: {submission.content["title"]["value"]}',
            recipients = final_recipients,
            message = f'''Hi {{{{fullname}}}},
            
A new conversation has been started in the {short_name} forum for submission {submission.number}: {submission.content['title']['value']}

You can view the conversation here: https://openreview.net/forum?id={submission.id}&noteId={comment.id}#committee-chat
''',
            replyTo = contact,
            ignoreRecipients = ignore_recipients,
            signature=venue_id,
            sender=sender            
        )

        ## Update the last notified id
        print('Set last notified id', comment.id)
        client.post_invitation_edit (
            invitations=meta_invitation_id,
            signatures=[venue_id],
            invitation=openreview.api.Invitation(
                id=invitation.id,
                content={
                    'last_notified_id': { 'value': comment.id }
                }
            )
        )

        return

    last_notified_id = invitation.content.get('last_notified_id', {}).get('value') if invitation.content else None

    if not last_notified_id:
        ## Update the last notified id
        print('Set the last notified id, it was not set before', comment.id)
        client.post_invitation_edit (
            invitations=meta_invitation_id,
            signatures=[venue_id],
            invitation=openreview.api.Invitation(
                id=invitation.id,
                content={
                    'last_notified_id': { 'value': comment.id }
                }
            )
        )
        last_notified_id = comment.id               

    print('Send follow up comment email')
    last_notified_comment = client.get_note(last_notified_id)
    new_comments = client.get_notes(invitation=invitation.id, forum=submission.id, mintcdate=last_notified_comment.tcdate, sort='tcdate:asc')

    print(f'New comments: {len(new_comments)}')
    if len(new_comments) >= 5:
        client.post_message(
            invitation=meta_invitation_id,
            subject = f'[{short_name}] New messages in committee members chat for submission {submission.number}: {submission.content["title"]["value"]}',
            recipients = final_recipients,
            message = f'''Hi {{{{fullname}}}},
            
New comments have been posted for the conversation in the {short_name} forum for submission {submission.number}: {submission.content['title']['value']}

You can view the conversation here: https://openreview.net/forum?id={submission.id}&noteId={new_comments[0].id}#committee-chat
''',
            replyTo = contact,
            ignoreRecipients = ignore_recipients,
            signature=venue_id,
            sender=sender            
        )

        print('Update the last notified id', comment.id)
        client.post_invitation_edit (
            invitations=meta_invitation_id,
            signatures=[venue_id],
            invitation=openreview.api.Invitation(
                id=invitation.id,
                content={
                    'last_notified_id': { 'value': comment.id }
                }
            )
        )