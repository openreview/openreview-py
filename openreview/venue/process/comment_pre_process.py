def process(client, edit, invitation):

    domain = client.get_group(invitation.domain)

    note = edit.note
    
    if note.ddate:
        return

    if note.readers == ['everyone']:
        return

    forum=client.get_note(id=note.forum)

    comment_mandatory_readers = domain.get_content_value('comment_mandatory_readers', [])
    for m in comment_mandatory_readers:
        reader=m.replace('{number}', str(forum.number))
        if reader not in note.readers:
            raise openreview.OpenReviewException(f'{openreview.tools.pretty_id(reader)} must be readers of the comment')
