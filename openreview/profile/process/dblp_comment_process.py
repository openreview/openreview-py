def process(client, edit, invitation):

    submission = client.get_note(edit.note.forum)
    comment = client.get_note(edit.note.id)

    ### TODO: Fix this, we should notify the use when the review is updated
    if comment.tcdate != comment.tmdate:
        return

    
    signature_profile_usernames = client.get_profile(comment.signatures[0]).get_usernames()
    signature_subscription_status = None
    
    email_subscription_invitation = f'{submission.domain}/-/Email_Subscription'
    tags = client.get_all_tags(invitation=email_subscription_invitation, note=comment.forum)
    print('Found tags:', len(tags))

    subscribers = []
    unsubscribers = []
    for tag in tags:
        if tag.label == 'Subscribe':
            subscribers.append(tag.signature)
        if tag.label == 'Unsubscribe':
            unsubscribers.append(tag.signature)
        if tag.signature in signature_profile_usernames:
            signature_subscription_status = tag.label

    print('Found subscribers:', subscribers)
    print('Found unsubscribers:', unsubscribers)
    print('Signature subscription status:', signature_subscription_status)

    signature = comment.signatures[0]
    pretty_signature = openreview.tools.pretty_id(signature.split('/')[-1])

    content = f'''
    
Paper Title: {submission.content['title']['value']}

Comment: {comment.content['comment']['value']}

To view the comment, click here: https://openreview.net/forum?id={submission.id}&noteId={comment.id}

To unsubscribe from email notifications, click here: https://openreview.net/forum?id={submission.id}&invitation={email_subscription_invitation}&label=Unsubscribe&signature={signature}'''

    #send email to publication authors
    client.post_message(
        invitation=f'{submission.domain}/-/Edit',
        recipients=[ a for a in submission.content['authorids']['value'] if a.startswith('~') ],
        ignoreRecipients=[edit.tauthor] + unsubscribers,
        subject=f'''[OpenReview] {pretty_signature} commented on your publication with title: "{submission.content['title']['value']}"''',
        message=f'''{pretty_signature} commented on your publication.{content}''',
        signature=submission.domain
    )

    #send email to publication subscribers
    if subscribers:
        client.post_message(
            invitation=f'{submission.domain}/-/Edit',
            recipients=subscribers,
            ignoreRecipients=[edit.tauthor] + unsubscribers,
            subject=f'''[OpenReview] {pretty_signature} commented on a publication with title: "{submission.content['title']['value']}"''',
            message=f'''{pretty_signature} commented on a publication where you are subscribed to receive email notifications.{content}''',
            signature=submission.domain
        )

    footer = f'To subscribe to email notifications, click here: https://openreview.net/forum?id={submission.id}&invitation={email_subscription_invitation}&label=Subscribe&signature={signature}'
    if signature_subscription_status == 'Unsubscribe':
        footer = f'To resubscribe to email notifications, click here: https://openreview.net/forum?id={submission.id}&invitation={email_subscription_invitation}&label=Subscribe&signature={signature}'
    if signature_subscription_status == 'Subscribe':
        footer = f'To unsubscribe from email notifications, click here: https://openreview.net/forum?id={submission.id}&invitation={email_subscription_invitation}&label=Unsubscribe&signature={signature}'
    
    #send email to comment signature
    client.post_message(
        invitation=f'{submission.domain}/-/Edit',
        recipients=[edit.tauthor],
        subject=f'''[OpenReview] Your comment was received on a publication with title: "{submission.content['title']['value']}"''',
        message=f'''Your comment was received.
        
Paper Title: {submission.content['title']['value']}

Comment: {comment.content['comment']['value']}

To view the comment, click here: https://openreview.net/forum?id={submission.id}&noteId={comment.id}

{footer}''',
        signature=submission.domain
    )