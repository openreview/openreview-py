def process_update(client, note, invitation, existing_note):

    MANDATORY_READERS = []

    if note.ddate:
        return

    if note.readers == ['everyone']:
        return

    forum=client.get_note(id=note.forum)

    for m in MANDATORY_READERS:
        reader=m.replace('{number}', str(forum.number))
        if reader not in note.readers:
            raise openreview.OpenReviewException(f'{openreview.tools.pretty_id(reader)} must be readers of the comment')
