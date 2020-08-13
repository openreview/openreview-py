def process(client, note, invitation):
    from datetime import datetime
    CONFERENCE_ID = ''
    PROGRAM_CHAIRS_ID = ''
    SHORT_NAME = ''

    comment_note = client.get_note(note.referent)
    comment_author = comment_note.signatures[0]

    moderated_comment_invitation_id = CONFERENCE_ID+'/-/Moderated_Comment'

    comment_note.readers = [PROGRAM_CHAIRS_ID, comment_note.signatures[0]]
    comment_note.writers = [PROGRAM_CHAIRS_ID]
    comment_note.signatures = [PROGRAM_CHAIRS_ID]
    comment_note.invitation = moderated_comment_invitation_id

    client.post_note(comment_note)

    message = '''Your comment https://openreview.net/forum?id={}&noteId={} has been moderated by the Program Committee. If you wish to appeal against it, please reach out to the committee.'''.format(comment_note.forum, comment_note.id)

    client.post_message(
        subject='[{}]: Your comment has been moderated by the Program Committee'.format(SHORT_NAME),
        recipients=[comment_author],
        message=message)
