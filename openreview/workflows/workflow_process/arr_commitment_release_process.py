def process(client, invitation):

    venue_id = invitation.content['venue_id']['value']
    venue_group = client.get_group(venue_id)

    additional_readers = []
    area_chairs_name = venue_group.content.get('area_chairs_name', {}).get('value')
    if area_chairs_name:
        additional_readers.append(area_chairs_name)

    openreview.arr.ARR.process_commitment_venue(
        client,
        venue_id,
        invitation_reply_ids=['Official_Review', 'Meta_Review'],
        additional_readers=additional_readers
    )
