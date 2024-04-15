def process(client, note, invitation):
    _, baseurl_v2 = openreview.tools.get_base_urls(client)
    client_v2 = openreview.api.OpenReviewClient(baseurl=baseurl_v2, token=client.token)
    forum_note = client.get_note(note.forum)
    venue_id = forum_note.content.get('venue_id', '')
    domain = client_v2.get_group(venue_id)
    compute_conflicts = note.content.get('compute_conflicts') != 'No'
    compute_affinity_scores = note.content.get('compute_affinity_scores') != 'No'

    if compute_affinity_scores and 'upload_affinity_scores' in note.content:
        raise openreview.OpenReviewException('Either upload your own affinity scores or select affinity scores computed by OpenReview')

    matching_group = note.content['matching_group']
    matching_notes = client.get_all_notes(invitation=invitation.id, sort='tmdate:desc')
    matching_group_notes = [matching_note for matching_note in matching_notes if matching_note.content['matching_group'] == matching_group]
    
    if matching_group_notes:
        status_note = client.get_all_notes(invitation=invitation.id.replace('Paper_Matching_Setup', 'Paper_Matching_Setup_Status'), replyto=matching_group_notes[0].id)
        if not status_note:
            raise openreview.OpenReviewException('Paper matching is already being run for this group. Please wait for a status reply in the forum.')

    if forum_note.content.get('api_version', '1') == '2':
        senior_area_chairs_id = domain.get_content_value('senior_area_chairs_id')
        sac_paper_assignments = domain.get_content_value('sac_paper_assignments')
        if senior_area_chairs_id and matching_group == senior_area_chairs_id and not sac_paper_assignments:
            if compute_conflicts:
                raise openreview.OpenReviewException('Conflicts are not computed between SACs and ACs. Please select "No" for Compute Conflicts.')
            return

        submission_venue_id = domain.get_content_value('submission_venue_id')
        _, num_submissions = client_v2.get_notes(content={ 'venueid':submission_venue_id }, limit=1, with_count=True)
        if compute_affinity_scores and num_submissions >= 2000:
            raise openreview.OpenReviewException(f'Can not compute affinity scores for venues with 2000+ papers. Please contact us at info@openreview.net to compute your scores.')

        area_chairs_id = domain.get_content_value('area_chairs_id')
        if compute_conflicts and senior_area_chairs_id and area_chairs_id and matching_group == area_chairs_id and not sac_paper_assignments:
            senior_area_chairs_assignment_id = domain.get_content_value('senior_area_chairs_assignment_id')
            num_edges = client_v2.get_edges_count(invitation=senior_area_chairs_assignment_id)
            if not num_edges:
                raise openreview.OpenReviewException(f'Please deploy SAC-AC assignments first. SAC-submission conflicts must be transferred to assigned ACs before computing AC-submission conflicts.')
