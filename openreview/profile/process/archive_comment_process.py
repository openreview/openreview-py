def process(client, edit, invitation):

    submission = client.get_note(edit.note.forum)
    comment = client.get_note(edit.note.id)

    ### TODO: Fix this, we should notify the use when the review is updated
    if comment.tcdate != comment.tmdate:
        return    

    signature = comment.signatures[0].split('/')[-1]
    pretty_signature = openreview.tools.pretty_id(signature)

    content = f'''
    
Paper number: {submission.number}

Paper title: {submission.content['title']['value']}

Comment: {comment.content['comment']['value']}

To view the comment, click here: https://openreview.net/forum?id={submission.id}&noteId={comment.id}'''

    #send email to paper authors
    client.post_message(
        invitation=f'{submission.domain}/-/Edit',
        recipients=submission.content['authorids']['value'],
        ignoreRecipients=[edit.tauthor],
        subject=f'''[OpenReview Archive] {pretty_signature} commented on your submission. Paper Title: "{submission.content['title']['value']}"''',
        message=f'''{pretty_signature} commented on your submission.{content}''',
        signature=submission.domain
    )
