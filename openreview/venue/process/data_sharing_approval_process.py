def process(client, edit, invitation):

    SUPPORT_GROUP = ''

    data_sharing = openreview.venue.VenueDataSharing(client, SUPPORT_GROUP)

    approval = client.get_note(edit.note.id)
    request = client.get_note(approval.forum)
    venue_id = request.content['venue_id']['value']
    alternate_venue_id = request.content['alternate_venue_id']['value']
    status = approval.content['status']['value']
    approval_comment = approval.content.get('approval_comment', {}).get('value')
    forum_url = data_sharing.get_forum_url(request.id)

    data_sharing.post_status(request.id, status)

    short_name, program_chairs_id = data_sharing.get_venue_info(venue_id)
    alternate_short_name, alternate_program_chairs_id = data_sharing.get_venue_info(alternate_venue_id)

    comment_text = f'''

Comment from the program chairs of {alternate_short_name}:

{approval_comment}''' if approval_comment else ''

    if status == 'Approved':
        data_sharing.post_message(
            recipients=[program_chairs_id],
            subject=f'{alternate_short_name} approved your dual submission check request',
            message=f'''The program chairs of {alternate_short_name} ({alternate_venue_id}) approved your dual submission check request.{comment_text}

The OpenReview support team will run the check, and you will receive an email when the results are available.

You can view the request here: {forum_url}

The OpenReview Team'''
        )

        data_sharing.post_message(
            recipients=[SUPPORT_GROUP],
            subject=f'Dual submission check ready to run: {short_name} and {alternate_short_name}',
            message=f'''The program chairs of {alternate_short_name} ({alternate_venue_id}) approved the dual submission check requested by {short_name} ({venue_id}).

Run the check from the request: {forum_url}'''
        )
        return

    data_sharing.post_message(
        recipients=[program_chairs_id],
        subject=f'{alternate_short_name} rejected your dual submission check request',
        message=f'''The program chairs of {alternate_short_name} ({alternate_venue_id}) rejected your dual submission check request.{comment_text}

You can view the request here: {forum_url}

The OpenReview Team'''
    )
