def process_update(client, note, invitation, existing_note):
    CONFERENCE_ID = ''
    SHORT_PHRASE = ''
    AUTHORS_NAME = ''
    CONFERENCE_NAME = ''
    CONFERENCE_YEAR = ''
    REVISION_INVITATION = ''

    action = 'posted'
    if existing_note:
        action = 'deleted' if note.ddate else 'updated'

    forum = client.get_note(note.forum)

    title = note.content.get('title', forum.content.get('title', ''))
    if note.ddate:
        authorids = forum.content.get('authorids', [])
    else:
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

    if CONFERENCE_NAME and CONFERENCE_YEAR and note.content.get('title') and note.content.get('authors'):
        bibtex_note=forum
        notes=client.get_notes(original=forum.id)
        anonymous_note=False
        if notes:
            bibtex_note=notes[0]
            anonymous_note = bibtex_note.content.get('authors') == ['Anonymous']

        bibtex = openreview.tools.generate_bibtex(
            forum,
            venue_fullname=CONFERENCE_NAME,
            year=CONFERENCE_YEAR,
            url_forum=bibtex_note.id,
            paper_status='accepted',
            anonymous=anonymous_note
        )

        revision_note = client.post_note(openreview.Note(
            invitation = f'{REVISION_INVITATION}',
            forum = forum.id,
            referent = forum.id,
            readers = ['everyone'],
            writers = [CONFERENCE_ID],
            signatures = [CONFERENCE_ID],
            content = {
                'venue': forum.content.get('venue'),
                'venueid': forum.content.get('venueid'),
                '_bibtex': bibtex
            }
        ))
