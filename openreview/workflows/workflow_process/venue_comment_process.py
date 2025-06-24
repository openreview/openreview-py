def process(client, edit, invitation):

    domain = invitation.domain
    support_user = f'{domain}/Support'

    comment = client.get_note(edit.note.id)
    forum_note = client.get_note(comment.forum)

    if comment.tcdate != comment.tmdate:
        return

    note_signature = comment.signatures[0]
    signature = openreview.tools.pretty_id(note_signature) if note_signature.startswith('~') else 'Support'

    comment_title = comment.content['title']['value'] if 'title' in comment.content else f'Comment by {signature}'

    comment_content = f'''

Comment title: {comment_title}

Comment: {comment.content['comment']['value']}

To view the comment, click here: https://openreview.net/forum?id={forum_note.id}&noteId={comment.id}'''
    
    # send message to PCs
    if comment_title == 'Your venue is available in OpenReview':

        client.post_message(
            invitation=f'{domain}/-/Edit',
            recipients=comment.readers,
            ignoreRecipients = [support_user],
            subject=f'''Your venue, {forum_note.content['abbreviated_venue_name']['value']}, is available in OpenReview''',
            message=f'''A comment was posted to your service request.{comment_content}

Please note that with the exception of urgent issues, requests made on weekends or US holidays can expect to receive a response on the following business day. Thank you for your patience!'''
        )
    else:
        client.post_message(
            invitation=f'{domain}/-/Edit',
            recipients=comment.readers,
            ignoreRecipients = [support_user],
            subject=f'''Comment posted to your request for service: {forum_note.content['title']['value']}''',
            message=f'''A comment was posted to your service request.{comment_content}

Please note that with the exception of urgent issues, requests made on weekends or US holidays can expect to receive a response on the following business day. Thank you for your patience!'''
        )

    #send email to support
    client.post_message(
        invitation=f'{domain}/-/Edit',
        recipients=[support_user],
        subject=f'''Comment posted to a request for service: {forum_note.content['title']['value']}''',
        message=f'''A comment was posted to a service request.{comment_content}'''
    )