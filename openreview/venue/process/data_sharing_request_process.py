def process(client, edit, invitation):

    SUPPORT_GROUP = ''

    data_sharing = openreview.venue.VenueDataSharing(client, SUPPORT_GROUP)

    request = client.get_note(edit.note.id)
    venue_id = request.content['venue_id']['value']
    alternate_venue_id = request.content['alternate_venue_id']['value']
    top_percent_cutoff = request.content['top_percent_cutoff']['value']
    author_overlap_only = request.content['author_overlap_only']['value']
    comment = request.content.get('comment', {}).get('value')
    forum_url = data_sharing.get_forum_url(request.id)

    data_sharing.create_request_invitations(request)

    short_name, program_chairs_id = data_sharing.get_venue_info(venue_id)
    alternate_short_name, alternate_program_chairs_id = data_sharing.get_venue_info(alternate_venue_id)

    comment_text = f'''

Comment from the program chairs of {short_name}:

{comment}''' if comment else ''

    data_sharing.post_message(
        recipients=[alternate_program_chairs_id],
        subject=f'{short_name} requests a dual submission check with {alternate_short_name}',
        message=f'''The program chairs of {short_name} ({venue_id}) request a dual submission check with {alternate_short_name} ({alternate_venue_id}).

If you approve, the OpenReview support team will compute the similarity between the submissions of both venues and share a CSV file with the program chairs of both venues. The file contains the ids, titles, abstracts and authors of the {top_percent_cutoff}% most similar pairs of submissions{', only for pairs that share at least one author' if author_overlap_only else ''}.{comment_text}

To approve or reject the request, or to ask the program chairs of {short_name} a question, go to: {forum_url}

The OpenReview Team'''
    )

    data_sharing.post_message(
        recipients=[program_chairs_id],
        subject=f'Your dual submission check request with {alternate_short_name} has been sent',
        message=f'''We sent your dual submission check request to the program chairs of {alternate_short_name} ({alternate_venue_id}). You will receive an email when they approve or reject it.

You can view the request and comment on it here: {forum_url}

The OpenReview Team'''
    )
