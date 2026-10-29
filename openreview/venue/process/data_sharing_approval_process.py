def process(client, edit, invitation):

    SUPPORT_GROUP = ''

    def get_venue_info(venue_id):
        venue_group = client.get_group(venue_id)
        short_name = venue_group.content.get('subtitle', {}).get('value') or venue_id
        program_chairs_id = venue_group.content.get('program_chairs_id', {}).get('value', f'{venue_id}/Program_Chairs')
        return short_name, program_chairs_id

    def post_message(recipients, subject, message):
        client.post_message(subject=subject, recipients=recipients, message=message, invitation=f'{SUPPORT_GROUP}/-/Edit', signature=SUPPORT_GROUP)

    approval = client.get_note(edit.note.id)
    request = client.get_note(approval.forum)
    venue_id = request.content['venue_id']['value']
    alternate_venue_id = request.content['alternate_venue_id']['value']
    status = approval.content['status']['value']
    approval_comment = approval.content.get('approval_comment', {}).get('value')
    submission_statuses = approval.content.get('submission_statuses', {}).get('value') or ['Active']
    results_recipients = approval.content.get('results_recipients', {}).get('value')
    forum_url = f'{openreview.tools.get_site_url(client)}/forum?id={request.id}'

    ## copy the decision to the status of the request
    client.post_note_edit(
        invitation=f'{SUPPORT_GROUP}/-/Edit',
        readers=[SUPPORT_GROUP],
        writers=[SUPPORT_GROUP],
        signatures=[SUPPORT_GROUP],
        note=openreview.api.Note(
            id=request.id,
            content={
                'status': { 'value': status }
            }
        )
    )

    short_name, program_chairs_id = get_venue_info(venue_id)
    alternate_short_name, alternate_program_chairs_id = get_venue_info(alternate_venue_id)

    comment_text = f'''

Comment from the program chairs of {alternate_short_name}:

{approval_comment}''' if approval_comment else ''

    if status == 'Approved':
        post_message(
            recipients=[program_chairs_id],
            subject=f'{alternate_short_name} approved your dual submission check request',
            message=f'''The program chairs of {alternate_short_name} ({alternate_venue_id}) approved your dual submission check request.

Submissions of {alternate_short_name} to compare: {', '.join(submission_statuses)}
Results recipients of {alternate_short_name}: {', '.join(results_recipients) if results_recipients else f'all the program chairs of {alternate_short_name}'}{comment_text}

The OpenReview support team will run the check, and the results recipients of both venues will receive an email when the results are available.

You can view the request here: {forum_url}

The OpenReview Team'''
        )

        post_message(
            recipients=[SUPPORT_GROUP],
            subject=f'Dual submission check ready to run: {short_name} and {alternate_short_name}',
            message=f'''The program chairs of {alternate_short_name} ({alternate_venue_id}) approved the dual submission check requested by {short_name} ({venue_id}).

Run the check from the request: {forum_url}'''
        )
        return

    post_message(
        recipients=[program_chairs_id],
        subject=f'{alternate_short_name} rejected your dual submission check request',
        message=f'''The program chairs of {alternate_short_name} ({alternate_venue_id}) rejected your dual submission check request.{comment_text}

A request can't be edited. If the program chairs of {alternate_short_name} suggested different settings, submit a new request with them.

You can view the request here: {forum_url}

The OpenReview Team'''
    )
