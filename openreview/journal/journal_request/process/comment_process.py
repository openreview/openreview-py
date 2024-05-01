def process(client, edit, invitation):

    SUPPORT_GROUP = ''
    VENUE_ID = ''
    forum = client.get_note(edit.note.forum)

    full_name = forum.content['official_venue_name']['value']
    editors = forum.content['editors']['value']

    if edit.note.content['title']['value'] == 'New Recruitment Response':
        #if response did not change, return
        references = client.get_note_edits(note_id=edit.note.id)
        if len(references) > 1 :
            previous_reference = references[1]
            if edit.note.content['comment']['value'] == previous_reference.note.content['comment']['value']:
                return


        subject = f'A new recruitment response has been posted to your journal request: {full_name}'
        message = f'''Comment: {edit.note.content['comment']['value']}
        
To view the comment, click here: https://openreview.net/forum?id={edit.note.forum}&noteId={edit.note.id}'''

        recruitment_note = client.get_note(edit.note.replyto)
        client.post_message(subject, recruitment_note.signatures, message, invitation=f'{VENUE_ID}/-/Edit', signature=VENUE_ID)

    else:
        subject_eic = f'Comment posted to your journal request: {full_name}'
        message_eic = f'''A comment was posted to your journal request.

Comment title {edit.note.content['title']['value']}

Comment: {edit.note.content['comment']['value']}

To view the comment, click here: https://openreview.net/forum?id={edit.note.forum}&noteId={edit.note.id}'''

        client.post_message(subject_eic, editors, message_eic, invitation=f'{VENUE_ID}/-/Edit', signature=VENUE_ID)
