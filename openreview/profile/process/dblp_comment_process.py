def process(client, edit, invitation):

    submission = client.get_note(edit.note.forum)
    comment = client.get_note(edit.note.id)

    ### TODO: Fix this, we should notify the use when the review is updated
    if comment.tcdate != comment.tmdate:
        return    

    signature = comment.signatures[0].split('/')[-1]
    pretty_signature = openreview.tools.pretty_id(signature)

    content = f'''
    
Paper Title: {submission.content['title']['value']}

Comment: {comment.content['comment']['value']}

To view the comment, click here: https://openreview.net/forum?id={submission.id}&noteId={comment.id}'''

    #send email to publication authors
    client.post_message(
        invitation=f'{submission.domain}/-/Edit',
        recipients=[ a for a in submission.content['authorids']['value'] if a.startswith('~') ],
        ignoreRecipients=[edit.tauthor],
        subject=f'''[OpenReview] {pretty_signature} commented on your publication with title: "{submission.content['title']['value']}"''',
        message=f'''{pretty_signature} commented on your publication.{content}''',
        signature=submission.domain
    )

    #send email to publication subscribers
    client.post_message(
        invitation=f'{submission.domain}/-/Edit',
        recipients=comment.signatures,
        subject=f'''[OpenReview] {pretty_signature} commented on a publication with title: "{submission.content['title']['value']}"''',
        message=f'''{pretty_signature} commented on a publication where you are subscribed to receive email notifications.{content}''',
        signature=submission.domain
    )