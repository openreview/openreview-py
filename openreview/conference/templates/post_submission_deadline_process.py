def process_update(client, note, invitation, existing_note):
    CONFERENCE_ID = ''
    AUTHORS_NAME = ''

    forum = client.get_note(note.forum)

    authorids = note.content.get('authorids', [])

    if authorids:
        author_group = openreview.tools.get_group(client, '{}/Paper{}/{}'.format(CONFERENCE_ID, forum.number, AUTHORS_NAME))
        if author_group:
            author_group.members = authorids
            client.post_group(author_group)
