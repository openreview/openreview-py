def process_update(client, note, invitation, existing_note):

    CONFERENCE_ID = ''
    SHORT_PHRASE = ''
    AUTHORS_NAME = ''

    action = 'posted'
    if existing_note:
        action = 'deleted' if note.ddate else 'updated'

    forum = client.get_note(note.forum)

    title = note.content.get('title', forum.content.get('title', ''))
    authorids = note.content.get('authorids', forum.content.get('authorids', []))
    abstract = note.content.get('abstract', forum.content.get('abstract', ''))

    subject = '{} has received a new revision of your submission titled {}'.format(SHORT_PHRASE, title)
    message = '''Your new revision of the submission to {} has been {}.

Title: {}

Abstract: {}

To view your submission, click here: https://openreview.net/forum?id={}'''.format(SHORT_PHRASE, action, title, abstract, forum.id)

    client.post_message(subject=subject, recipients=authorids, message=message)

    if note.content.get('authorids'):
        author_group = openreview.tools.get_group(client, '{}/Paper{}/{}'.format(CONFERENCE_ID, forum.number, AUTHORS_NAME))
        if author_group:
            author_group.members = authorids
            client.post_group(author_group)

