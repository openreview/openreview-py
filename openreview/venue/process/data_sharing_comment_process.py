def process(client, edit, invitation):

    SUPPORT_GROUP = ''

    def get_venue_info(venue_id):
        venue_group = client.get_group(venue_id)
        short_name = venue_group.content.get('subtitle', {}).get('value') or venue_id
        program_chairs_id = venue_group.content.get('program_chairs_id', {}).get('value', f'{venue_id}/Program_Chairs')
        return short_name, program_chairs_id

    comment = client.get_note(edit.note.id)
    request = client.get_note(comment.forum)
    venue_id = request.content['venue_id']['value']
    alternate_venue_id = request.content['alternate_venue_id']['value']
    signature = comment.signatures[0]
    forum_url = f'{openreview.tools.get_site_url(client)}/forum?id={request.id}'

    short_name, program_chairs_id = get_venue_info(venue_id)
    alternate_short_name, alternate_program_chairs_id = get_venue_info(alternate_venue_id)

    names = {
        venue_id: f'the program chairs of {short_name}',
        alternate_venue_id: f'the program chairs of {alternate_short_name}',
        SUPPORT_GROUP: 'the OpenReview support team'
    }

    ## notify everybody in the forum except the group that posted the comment
    recipients = {
        venue_id: program_chairs_id,
        alternate_venue_id: alternate_program_chairs_id,
        SUPPORT_GROUP: SUPPORT_GROUP
    }
    recipients.pop(signature, None)

    client.post_message(
        subject=f'New comment on the dual submission check request: {short_name} and {alternate_short_name}',
        recipients=list(recipients.values()),
        message=f'''A comment was posted by {names.get(signature, signature)} on the dual submission check request between {short_name} and {alternate_short_name}.

Comment: {comment.content['comment']['value']}

To view the comment and reply, click here: {forum_url}&noteId={comment.id}''',
        invitation=f'{SUPPORT_GROUP}/-/Edit',
        signature=SUPPORT_GROUP
    )
