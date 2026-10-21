def process(client, edit, invitation):

    venue_id = edit.note.content['venue_id']['value']
    alternate_venue_id = edit.note.content['alternate_venue_id']['value']

    if venue_id == alternate_venue_id:
        raise openreview.OpenReviewException('The other venue must be different from your venue.')

    venues = client.get_group('venues').members
    for id in [venue_id, alternate_venue_id]:
        if id not in venues:
            raise openreview.OpenReviewException(f'{id} is not a venue.')

        ## journals don't have this field and their submissions are selected differently
        venue_group = client.get_group(id)
        if 'submission_venue_id' not in (venue_group.content or {}):
            raise openreview.OpenReviewException(f'{id} is not supported yet: the dual submission check only works with conferences and workshops, not journals.')
