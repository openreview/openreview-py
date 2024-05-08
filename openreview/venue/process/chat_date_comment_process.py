def process(client, invitation):

    domain = client.get_group(invitation.domain)
    venue_id = domain.id
    short_name = domain.get_content_value('subtitle')
    contact = domain.get_content_value('contact')
    meta_invitation_id = domain.get_content_value('meta_invitation_id')
    sender = domain.get_content_value('message_sender')


    last_notified_id = invitation.content.get('last_notified_id', {}).get('value') if invitation.content else None

    last_notified_comment = client.get_note(last_notified_id) if last_notified_id else None

    if not last_notified_comment:
        print('No last notified comment found')
        return

    submission = client.get_note(last_notified_comment.forum)
    new_comments = client.get_notes(invitation=invitation.id, forum=submission.id, mintcdate=last_notified_comment.tcdate, sort='tcdate:asc')

    print(f'New comments: {len(new_comments)}')
    if len(new_comments) == 0:
        return
    
    client.post_message(
        invitation = meta_invitation_id,
        subject = f'[{short_name}] New message{"s" if len(new_comments) > 1 else ""} in committee members chat for submission {submission.number}: {submission.content["title"]["value"]}',
        recipients = new_comments[-1].readers,
        message = f'''Hi {{{{fullname}}}},
        
New comment{"s have" if len(new_comments) > 1 else " has"} been posted for the conversation in the {short_name} forum for submission {submission.number}: {submission.content['title']['value']}

You can view the conversation here: https://openreview.net/forum?id={submission.id}&noteId={new_comments[0].id}#committee-chat
''',
        replyTo = contact,
        ignoreRecipients = new_comments[-1].signatures,
        signature=venue_id,
        sender = sender
    )

    ## Update the last notified id
    client.post_invitation_edit (
        invitations=meta_invitation_id,
        signatures=[venue_id],
        invitation=openreview.api.Invitation(
            id=invitation.id,
            content={
                'last_notified_id': { 'value': new_comments[-1].id }
            }
        )
    )    


