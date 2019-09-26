def process(client, note, invitation):
    WITHDRAWN_SUBMISSION_ID = ''
    REVEAL_AUTHORS_ON_WITHDRAW = False
    blind_note = client.get_note(note.forum)
    blind_note.invitation = WITHDRAWN_SUBMISSION_ID
    if REVEAL_AUTHORS_ON_WITHDRAW:
        original_note = client.get_note(id = blind_note.original)
        blind_note.content['authors'] = original_note.content['authors']
        blind_note.content['authorids'] = original_note.content['authorids']
    client.post_note(blind_note)
