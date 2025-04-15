def process(client, edit, invitation):

    submission = client.get_note(edit.note.forum)
    comment = client.get_note(edit.note.id)

    ### TODO: Fix this, we should notify the use when the review is updated
    if comment.tcdate != comment.tmdate:
        return
    
    email_subscription_invitation = f'{submission.domain}/-/Notification_Subscription'
    ## Subscribe signature if it is not subscribed
    subscribers = [t.signature for t in client.get_all_tags(invitation=email_subscription_invitation, note=comment.forum)]
    print('Found subscribers:', len(subscribers))
    print('Found subscribers:', subscribers)

    authors = [ a for a in submission.content['authorids']['value'] if a.startswith('~') ]

    ## First comment, subscribe all the authors
    forum_replies = client.get_notes(forum=submission.id, invitation=invitation.id)
    if (len(forum_replies) == 1):
        for author in authors:
            if author not in subscribers:
                print('Subscribing author:', author)
                client.post_tag(
                    openreview.api.Tag(
                        invitation=email_subscription_invitation,
                        signature=author,
                        forum=submission.id,
                        note=submission.id,
                    )
                )
                subscribers.append(author)

    signature = comment.signatures[0]
    signature_subscribed = False 
    if signature not in authors and signature not in subscribers:
        print('Subscribing signature:', signature)
        signature_subscribed = True
        client.post_tag(
            openreview.api.Tag(
                invitation=email_subscription_invitation,
                signature=signature,
                forum=submission.id,
                note=submission.id,
            )
        )
        subscribers.append(signature)
    
    
    pretty_signature = openreview.tools.pretty_id(signature.split('/')[-1])
    footer = '''To unsubscribe from email notifications, click on the link above and remove the "Subscribe" label.'''

    content = f'''
    
Paper Title: {submission.content['title']['value']}

Comment: {comment.content['comment']['value']}

To view the comment, click here: https://openreview.net/forum?id={submission.id}&noteId={comment.id}

{footer}'''

    #send email to publication authors
    subscribed_authors = [a for a in authors if a in subscribers]
    if subscribed_authors:
        client.post_message(
            invitation=f'{submission.domain}/-/Edit',
            recipients=subscribed_authors,
            subject=f'''[OpenReview] {pretty_signature} commented on your publication with title: "{submission.content['title']['value']}"''',
            message=f'''{pretty_signature} commented on your publication.{content}''',
            signature=submission.domain
        )

    #send email to publication subscribers
    if subscribers:
        client.post_message(
            invitation=f'{submission.domain}/-/Edit',
            recipients=subscribers,
            ignoreRecipients=authors + edit.signatures,
            subject=f'''[OpenReview] {pretty_signature} commented on a publication with title: "{submission.content['title']['value']}"''',
            message=f'''{pretty_signature} commented on a publication where you are subscribed to receive email notifications.{content}''',
            signature=submission.domain
        )

    #send email to comment signature
    if signature_subscribed:
        footer = '''You were automatically subscribed to receive email notifications for this publication. To unsubscribe, click on the link above and remove the "Subscribe" label.'''

    client.post_message(
        invitation=f'{submission.domain}/-/Edit',
        recipients=edit.signatures,
        subject=f'''[OpenReview] Your comment was received on a publication with title: "{submission.content['title']['value']}"''',
        message=f'''Your comment was received.
        
Paper Title: {submission.content['title']['value']}

Comment: {comment.content['comment']['value']}

To view the comment, click here: https://openreview.net/forum?id={submission.id}&noteId={comment.id}

{footer}''',
        signature=submission.domain
    )        