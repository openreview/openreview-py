def process(client, note, invitation):
    from datetime import datetime
    CONFERENCE_ID = ''
    PROGRAM_CHAIRS_ID = ''

    comment_note = client.get_note(note.replyto)
    comment_note.readers = [CONFERENCE_ID, PROGRAM_CHAIRS_ID]
    comment_note.writers = [CONFERENCE_ID, PROGRAM_CHAIRS_ID]
    client.post_note(comment_note)
