def process(client, edit, invitation):

    SUPPORT_GROUP = ''
    forum = client.get_note(edit.note.forum)

    full_name = forum.content['official_venue_name']['value']
    editors = forum.content['editors']['value']

    if edit.note.content['title']['value'] == 'New Recruitment Response':
        subject = f'A new recruitment response has been posted to your journal request: {full_name}'
        message = f'''Comment: {edit.note.content['comment']['value']}
        
    To view the comment, click here: https://openreview.net/forum?id={edit.note.forum}&noteId={edit.note.id}'''

        client.post_message(subject, edit.note.readers, message)

    else:
        subject_eic = f'Comment posted to your journal request: {full_name}'
        message_eic = f'''A comment was posted to your journal request.

    Comment title {edit.note.content['title']['value']}

    Comment: {edit.note.content['comment']['value']}

    To view the comment, click here: https://openreview.net/forum?id={edit.note.forum}&noteId={edit.note.id}'''

        client.post_message(subject_eic, editors, message_eic)

        subject_support = f'Comment posted to a journal request: {full_name}'
        message_support = f'''A comment was posted to a journal request.

    Comment title {edit.note.content['title']['value']}

    Comment: {edit.note.content['comment']['value']}

    To view the comment, click here: https://openreview.net/forum?id={edit.note.forum}&noteId={edit.note.id}'''

        client.post_message(subject_eic, [SUPPORT_GROUP], message_eic)
