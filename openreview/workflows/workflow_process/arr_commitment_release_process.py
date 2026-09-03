def process(client, edit, invitation):

    support_user = invitation.domain

    note = client.get_note(edit.note.id)
    venue_id = note.content.get('venue_id', {}).get('value')

    if not venue_id:
        raise openreview.OpenReviewException('The venue must be deployed before releasing the ARR submissions')

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

    client.post_note_edit(
        invitation=f'{support_user}/Venue_Request/ARR_Commitment_Workflow{note.number}/-/Comment',
        signatures=[support_user],
        note=openreview.api.Note(
            replyto=note.id,
            content={
                'title': { 'value': 'ARR submissions released' },
                'comment': { 'value': 'The venue has been given read access to the committed ARR submissions and their reviews and meta reviews.' }
            }
        )
    )
