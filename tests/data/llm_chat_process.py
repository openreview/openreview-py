def process(client, edit, invitation):

    domain = client.get_group(edit.domain)

    if edit.signatures[0] == domain.id + '/LLM' or edit.signatures[0] == domain.id:
        return

    ## post a reply
    client.post_note_edit(
        invitation=invitation.id,
        signatures=[domain.id + '/LLM'],
        note=openreview.api.Note(
            replyto=edit.note.id,
            content={
                'message': {
                    'value': f'''This is a reply to the comment: {edit.note.content['message']['value']}'''
                }
            }
        )
    )