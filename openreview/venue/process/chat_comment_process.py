def process(client, edit, invitation):

    domain = client.get_group(edit.domain)
    venue_id = domain.id
    short_name = domain.get_content_value('subtitle')
    contact = domain.get_content_value('contact')
    meta_invitation_id = domain.get_content_value('meta_invitation_id')

    submission = client.get_note(edit.note.forum)
    comment = client.get_note(edit.note.id)

    if comment.number == 1:
        print('Send initial comment email')

        client.post_message(
            subject = f'[{short_name}] New conversation in comittee members chat for submission {submission.number}: {submission.content["title"]["value"]}',
            recipients = comment.readers,
            message = f'''Hi {{{{fullname}}}},
            
A new conversation has been started in the {short_name} forum for submission {submission.number}: {submission.content['title']['value']}

You can view the conversation here: https://openreview.net/forum?id={submission.id}&noteId={comment.id}#committee-chat
''',
            replyTo = contact,
            ignoreRecipients = comment.signatures
        )

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

    else:

        print('Send follow up comment email')

        last_notified_id = invitation.content.get('last_notified_id', {}).get('value') if invitation.content else None

        last_notified_comment = client.get_note(last_notified_id) if last_notified_id else comment

        new_comments = client.get_notes(invitation=invitation.id, forum=submission.id, mintcdate=last_notified_comment.tcdate, sort='tcdate:asc')

        print(f'New comments: {len(new_comments)}')
        if len(new_comments) < 5:
            return
        
        client.post_message(
            subject = f'[{short_name}] New messages in comittee members chat for submission {submission.number}: {submission.content["title"]["value"]}',
            recipients = comment.readers,
            message = f'''Hi {{{{fullname}}}},
            
New comments have been posted for the conversation in the {short_name} forum for submission {submission.number}: {submission.content['title']['value']}

You can view the conversation here: https://openreview.net/forum?id={submission.id}&noteId={new_comments[0].id}#committee-chat
''',
            replyTo = contact,
            ignoreRecipients = comment.signatures
        )

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