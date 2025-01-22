def process(client, edit, invitation):
    # Get paper number
    note = edit.note
    forum = client.get_note(note.id)
    volunteers = note.content.get('reviewing_volunteers', {}).get('value', [])
    authorids = forum.content.get('authorids').get('value')

    for v in volunteers:
        if v not in authorids:
            raise openreview.OpenReviewException(f'Volunteer {v} is not an author of this submission')