def process(client, note, invitation):
    WITHDRAWN_SUBMISSION_ID = ''
    REVEAL_AUTHORS_ON_WITHDRAW = ''
    blind_note = client.get_note(note.forum)
    blind_note.invitation = WITHDRAWN_SUBMISSION_ID
    client.post_note(blind_note)
