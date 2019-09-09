def process(client, note, invitation):
    WITHDRAWN_SUBMISSION_ID = ''
    blind_note = client.get_note(note.forum)
    blind_note.invitation = WITHDRAWN_SUBMISSION_ID
    client.post_note(note)
