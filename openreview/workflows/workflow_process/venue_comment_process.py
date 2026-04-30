def process(client, edit, invitation):

    support_user = invitation.domain

    comment = client.get_note(edit.note.id)
    forum_note = client.get_note(comment.forum)
    venue_id = forum_note.content.get('venue_id', {}).get('value', '')

    if comment.tcdate != comment.tmdate:
        return

    note_signature = comment.signatures[0]
    signature = openreview.tools.pretty_id(note_signature) if note_signature.startswith('~') else 'Support'

    if invitation.id.endswith('/-/Comment') or invitation.id.endswith('/-/Status'):

        comment_title = comment.content['title']['value'] if 'title' in comment.content else f'Comment by {signature}'

        comment_content = f'''Comment title: {comment_title}

Comment: {comment.content['comment']['value']}

To view the comment, click here: https://openreview.net/forum?id={forum_note.id}&noteId={comment.id}'''

        # send message to PCs
        if comment_title == 'Your venue is available in OpenReview':

            client.post_message(
                invitation=f'{support_user}/-/Edit',
                signature=support_user,
                recipients=comment.readers,
                ignoreRecipients = [support_user],
                subject=f'''Your venue, {forum_note.content['abbreviated_venue_name']['value']}, is available in OpenReview''',
                message=f'''A comment was posted to your service request.

{comment_content}

Please note that with the exception of urgent issues, requests made on weekends or US holidays can expect to receive a response on the following business day. Thank you for your patience!'''
            )
        else:
            client.post_message(
                invitation=f'{support_user}/-/Edit',
                signature=support_user,
                recipients=comment.readers,
                ignoreRecipients = [support_user],
                subject=f'''Comment posted to your request for service: {forum_note.content['title']['value']}''',
                message=f'''A comment was posted to your service request.

{comment_content}

Please note that with the exception of urgent issues, requests made on weekends or US holidays can expect to receive a response on the following business day. Thank you for your patience!'''
            )

        # send email to support if comment comes from PCs
        if comment.signatures[0].startswith('~'):
            print('Sending email to support')
            if venue_id:
                subject = f'''[{venue_id}] Comment posted to a request for service: {forum_note.content['title']['value']}'''
                message = f'''A comment was posted to a service request.

{comment_content}

Workflow timeline: https://openreview.net/group/edit?id={venue_id}'''
            else:
                subject = f'''Comment posted to a request for service: {forum_note.content['title']['value']}'''
                message = f'''A comment was posted to a service request.

{comment_content}'''

            client.post_message(
                invitation=f'{support_user}/-/Edit',
                signature=support_user,
                recipients=[f'{support_user}/Recipients'],
                subject=subject,
                message=message
            )
        else:
            print('Comment from support, no email sent to support')

    elif invitation.id.endswith('/-/Feedback'):

        # send message to PCs
        client.post_message(
            invitation=f'{support_user}/-/Edit',
            signature=support_user,
            recipients=forum_note.readers,
            ignoreRecipients = [support_user],
            subject=f'''Feedback received for your venue: {forum_note.content['abbreviated_venue_name']['value']}''',
            message=f'''Thank you for providing feedback on the new venue management UI. We appreciate you taking the time to share your thoughts and will use your input to continue improving the experience for program chairs.

To view the feedback, click here: https://openreview.net/forum?id={forum_note.id}&noteId={comment.id}'''
        )

        feedback_content = f'''Overall rating: {comment.content['overall_rating']['value']}

**Comparison to previous experience:** {comment.content['comparison_to_previous_experience']['value']}

**Likelihood to recommend:** {comment.content['recommendation_likelihood']['value']}

**Strengths:** {comment.content.get('strengths', {}).get('value', '')}

**Pain points:** {comment.content.get('pain_points', {}).get('value', '')}

**Other comments:** {comment.content.get('other_comments', {}).get('value', '')}
'''

        # send feedback to support
        subject = f'''Feedback received for venue: {forum_note.content['abbreviated_venue_name']['value']}'''
        message = f'''Feedback was posted to a service request.

{feedback_content}

Workflow timeline: https://openreview.net/group/edit?id={venue_id}'''

        client.post_message(
            invitation=f'{support_user}/-/Edit',
            signature=support_user,
            recipients=[f'{support_user}/Recipients'],
            subject=subject,
            message=message
        )