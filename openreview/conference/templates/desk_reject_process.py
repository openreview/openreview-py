def process(client, note, invitation):
    DESK_REJECTED_SUBMISSION_ID = ''
    REVEAL_AUTHORS_ON_DESK_REJECT = False
    blind_note = client.get_note(note.forum)
    blind_note.invitation = DESK_REJECTED_SUBMISSION_ID
    if REVEAL_AUTHORS_ON_DESK_REJECT:
        original_note = client.get_note(id = blind_note.original)
        blind_note.content['authors'] = original_note.content['authors']
        blind_note.content['authorids'] = original_note.content['authorids']
    client.post_note(blind_note)
