def process(client, note, invitation):

    venue_id = note.content.get('venue_id', '')

    baseurl_v1, baseurl_v2 = openreview.tools.get_base_urls(client)
    api2_client = openreview.api.OpenReviewClient(baseurl=baseurl_v2, token=client.token)

    venue_group = openreview.tools.get_group(api2_client, id=venue_id)
    if venue_group:
        request_form = venue_group.content.get('request_form_id', {}).get('value')
        if request_form != note.forum:
            raise openreview.OpenReviewException(f"The venue id {venue_id} has already been used for request '{request_form}'")