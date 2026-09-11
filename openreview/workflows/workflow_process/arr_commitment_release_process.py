def process(client, edit, invitation):

    support_user = invitation.domain

    note = client.get_note(edit.note.id)
    venue_id = note.content.get('venue_id', {}).get('value')

    if not venue_id:
        raise openreview.OpenReviewException('The venue must be deployed before releasing the ARR submissions')

    reply_invitation_names = note.content.get('arr_reply_invitation_names', {}).get('value', ['Official_Review', 'Meta_Review'])
    additional_readers = note.content.get('arr_additional_readers', {}).get('value', [])

    # only grant access to roles the venue actually has
    additional_readers = [role for role in additional_readers if openreview.tools.get_group(client, f'{venue_id}/{role}')]

    openreview.arr.ARR.process_commitment_venue(
        client,
        venue_id,
        invitation_reply_ids=reply_invitation_names,
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
