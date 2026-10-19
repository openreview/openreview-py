def process(client, edit, invitation):

    venue_id = edit.note.content['venue_id']['value']
    alternate_venue_id = edit.note.content['alternate_venue_id']['value']

    if venue_id == alternate_venue_id:
        raise openreview.OpenReviewException('The other venue must be different from your venue.')

    venues = client.get_group('venues').members
    for id in [venue_id, alternate_venue_id]:
        if id not in venues:
            raise openreview.OpenReviewException(f'{id} is not a venue.')
