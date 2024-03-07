def process(client, note, invitation):
    _, baseurl_v2 = openreview.tools.get_base_urls(client)
    client_v2 = openreview.api.OpenReviewClient(baseurl=baseurl_v2, token=client.token)
    forum_note = client.get_note(note.forum)
    venue_id = forum_note.content.get('venue_id', '')
    domain = client_v2.get_group(venue_id)
    submission_name = domain.content.get('submission_name', '').get('value')
    senior_area_chairs_name = domain.content.get('senior_area_chairs_name', {}).get('value')

    submissions_over_2000 = client_v2.get_notes(invitation=f'{venue_id}/-/{submission_name}', offset=2000)
    compute_affinity_scores = note.content.get('compute_affinity_scores') == 'Yes'

    matching_group = note.content['matching_group']
    role_name = matching_group.split('/')[-1]
    pretty_role = role_name.replace('_', ' ')

    if compute_affinity_scores and 'upload_affinity_scores' in note.content:
        raise openreview.OpenReviewException('Either upload your own affinity scores or select affinity scores computed by OpenReview')

    if compute_affinity_scores and len(submissions_over_2000) and role_name != senior_area_chairs_name:
        raise openreview.OpenReviewException(f'Can not compute affinity scores between {pretty_role} and 2000+ papers. Please contact us at info@openreview.net to compute your scores.')
