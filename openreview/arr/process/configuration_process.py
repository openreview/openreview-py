def process(client, note, invitation):
    import datetime
    import traceback
    import json

    client_v2 = openreview.api.OpenReviewClient(
        baseurl=openreview.tools.get_base_urls(client)[1],
        token=client.token
    )

    SUPPORT_GROUP = invitation.id.split('/-/')[0]
    invitation_type = invitation.id.split('/')[-1]
    forum_note = client.get_note(note.forum)

    comment_readers = [forum_note.content.get('venue_id') + '/Program_Chairs', SUPPORT_GROUP]
    venue_id = forum_note.content.get('venue_id')
    domain = client_v2.get_group(venue_id)
    meta_invitation_id = domain.content['meta_invitation_id']['value']

    invitation_content = {}
    for field, raw_value in note.content.items():
        if 'date' in field:
            value = openreview.tools.datetime_millis(
                datetime.datetime.strptime(raw_value.strip(), '%Y/%m/%d %H:%M:%S')
            )
            invitation_content[field] = { 'value' : value}
        else:
            invitation_content[field] = { 'value' : raw_value}
    
    if len(note.content.keys()) > 0:
        client_v2.post_invitation_edit(
            invitations=meta_invitation_id,
            readers=[venue_id],
            writers=[venue_id],
            signatures=[venue_id],
            invitation=openreview.api.Invitation(
                id=f'{venue_id}/-/ARR_Scheduler',
                content=invitation_content
            )
        )