def process(client, note, invitation):

    client_v2 = openreview.api.OpenReviewClient(
        baseurl=openreview.tools.get_base_urls(client)[1],
        token=client.token
    )

    forum_note = client.get_note(note.forum)

    venue_id = forum_note.content.get('venue_id')
    domain = client_v2.get_group(venue_id)
    request_form_id = domain.content['request_form_id']['value']
    request_form = client.get_note(request_form_id)
    support_group = request_form.invitation.split('/-/')[0]
    venue = openreview.helpers.get_conference(client, request_form_id, support_group)

    venue.set_arr_stages(note)