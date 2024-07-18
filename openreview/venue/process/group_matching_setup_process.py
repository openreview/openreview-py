def process(client, edit, invitation):

    support_user = 'openreview.net/Support'
    domain = client.get_group(invitation.domain)
    venue_id = domain.id
    meta_invitation_id = domain.content['meta_invitation_id']['value']
    request_form_id = domain.get_content_value('request_form_id')

    venue = openreview.helpers.get_venue(client, request_form_id, support_user)
    venue.automatic_reviewer_assignment = edit.group.content.get('assignment_mode', {}).get('value', 'Manual') == 'Automatic'

    if edit.group.id == venue.get_senior_area_chairs_id() and edit.group.content.get('assignment_target', {}).get('value') == 'submissions':
        venue.sac_paper_assignments = True

    ## syncronize the venue group settings
    content = {
        'automatic_reviewer_assignment': { 'value': venue.automatic_reviewer_assignment },
        'sac_paper_assignments': { 'value': venue.sac_paper_assignments }
    }
    if edit.group.id == venue.get_reviewers_id():
        if 'conflict_policy' in edit.group.content:
            content['reviewers_conflict_policy'] = { 'value': edit.group.content.get('conflict_policy', {}).get('value') }
        if 'conflict_n_years' in edit.group.content:
            content['reviewers_conflict_n_years'] = { 'value': edit.group.content.get('conflict_n_years', {}).get('value') }
    elif edit.group.id == venue.get_area_chairs_id():
        if 'conflict_policy' in edit.group.content:
            content['area_chairs_conflict_policy'] = { 'value': edit.group.content.get('conflict_policy', {}).get('value') }
        if 'conflict_n_years' in edit.group.content:
            content['area_chairs_conflict_n_years'] = { 'value': edit.group.content.get('conflict_n_years', {}).get('value') }

    client.post_group_edit(
        invitation=meta_invitation_id,
        signatures=[venue_id],
        readers=[venue_id],
        group=openreview.api.Group(
            id=venue_id,
            content=content
        )
    )

    attachment_url = edit.group.content.get('affinity_score_upload', {}).get('value')
    scores_from_file = None
    if attachment_url:
        scores_from_file = client.get_attachment(id=edit.group.id, field_name='affinity_score_upload')

    ## run setup matching
    result = venue.setup_committee_matching(
        committee_id=edit.group.id, 
        compute_affinity_scores=edit.group.content.get('affinity_score_model', {}).get('value', scores_from_file), 
        compute_conflicts=edit.group.content.get('conflict_policy', {}).get('value'), 
        compute_conflicts_n_years=edit.group.content.get('conflict_n_years', {}).get('value'), 
        alternate_matching_group=None, 
        submission_track=None
    )

    print('Result', result)