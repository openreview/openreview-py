def process(client, note, invitation):
    from datetime import datetime
    CONFERENCE_ID = ''

    if 'justification' not in note.content:
        client.post_note(openreview.Note(
            referent=note.referent,
            forum=note.forum,
            replyto=note.replyto,
            invitation=note.invitation,
            content={
                'justification': ''
            },
            signatures=note.signatures,
            readers=note.readers,
            writers=note.writers
        ))
    else:
        comment_note = client.get_note(note.referent)
        forum_note = client.get_note(note.forum)

        comment_invitation_id = '{}/Paper{}/-/Public_Comment'.format(CONFERENCE_ID, forum_note.number)

        comment_author = ''
        for reader in comment_note.readers:
            if 'Program_Chairs' not in reader:
                comment_author = reader
                break

        comment_note.readers = ['everyone']
        comment_note.signatures = [comment_author]
        comment_note.writers = [CONFERENCE_ID, comment_author]
        comment_note.invitation = comment_invitation_id
        comment_note.content = {
            'title': comment_note.content['title'],
            'comment': comment_note.content['comment']
        }

        client.post_note(comment_note)
