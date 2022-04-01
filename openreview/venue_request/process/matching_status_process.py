def process(client, note, invitation):
    GROUP_PREFIX = ''
    SUPPORT_GROUP = GROUP_PREFIX + '/Support'

    forum_note = client.get_note(note.forum)
    subject = f'''{note.content['title']} for service: {forum_note.content['title']}'''
    error = f'''\n\nError: {note.content['error']}''' if note.content.get('error') else ''
    comment = f'''\n\nComment: {note.content['comment']}''' if note.content.get('comment') else ''
    message = f'''A comment was posted to your service request. 
\n\nComment title: {note.content['title']} 
{comment}
{error} 
\n\nTo view the comment, click here: https://openreview.net/forum?id={note.forum}&noteId={note.id}
'''

    client.post_message(subject=subject, message=message, recipients=note.readers, ignoreRecipients=[note.tauthor, SUPPORT_GROUP])
