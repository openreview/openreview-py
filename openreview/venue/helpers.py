import openreview

def get_venue(client, venue_id, support_user='OpenReview.net/Support'):
    """
    Build a Venue object from the venue domain group.

    Args:
        client: openreview.api.OpenReviewClient (API v2 client)
        venue_id: the venue group ID
        support_user: support group identifier

    Returns:
        openreview.venue.Venue instance
    """
    domain = client.get_group(venue_id)
    venue = openreview.venue.Venue(client, venue_id, support_user)

    venue.name = domain.content['title']['value']
    venue.short_name = domain.content['subtitle']['value']
    venue.website = domain.content['website']['value']
    venue.contact = domain.content['contact']['value']
    venue.location = domain.content['location']['value']
    venue.request_form_id = domain.content.get('request_form_id', {}).get('value')
    venue.request_form_invitation = domain.content.get('request_form_invitation', {}).get('value')
    venue.use_area_chairs = 'area_chairs_id' in domain.content
    venue.use_senior_area_chairs = 'senior_area_chairs_id' in domain.content
    venue.use_secondary_area_chairs = 'secondary_area_chairs_name' in domain.content
    venue.use_ethics_chairs = 'ethics_chairs_id' in domain.content
    venue.use_ethics_reviewers = 'ethics_reviewers_id' in domain.content or 'ethics_reviewers_name' in domain.content
    venue.use_publication_chairs = 'publication_chairs_id' in domain.content
    venue.automatic_reviewer_assignment = domain.content.get('automatic_reviewer_assignment', {}).get('value')
    venue.senior_area_chair_roles = domain.content.get('senior_area_chair_roles', {}).get('value', ['Senior_Area_Chairs'])
    venue.senior_area_chairs_name = domain.content.get('senior_area_chairs_name', {}).get('value', venue.senior_area_chair_roles[0])
    venue.area_chair_roles = domain.content.get('area_chair_roles', {}).get('value', ['Area_Chairs'])
    venue.area_chairs_name = domain.content.get('area_chairs_name', {}).get('value', venue.area_chair_roles[0])
    venue.reviewer_roles = domain.content.get('reviewer_roles', {}).get('value', ['Reviewers'])
    venue.reviewers_name = domain.content.get('reviewers_name', {}).get('value', venue.reviewer_roles[0])
    venue.allow_gurobi_solver = domain.content.get('allow_gurobi_solver', {}).get('value', False)

    # Get preferred_emails_groups from domain, or build default with all enabled participants
    venue.preferred_emails_groups = domain.content.get('preferred_emails_groups', {}).get('value')
    if not venue.preferred_emails_groups:
        preferred_emails_groups = [venue.get_authors_id(), venue.get_reviewers_id()]
        if venue.use_area_chairs:
            preferred_emails_groups.append(venue.get_area_chairs_id())
        if venue.use_senior_area_chairs:
            preferred_emails_groups.append(venue.get_senior_area_chairs_id())
        if venue.use_ethics_reviewers:
            preferred_emails_groups.append(venue.get_ethics_reviewers_id())
        if venue.use_ethics_chairs:
            preferred_emails_groups.append(venue.get_ethics_chairs_id())
        if venue.use_publication_chairs:
            preferred_emails_groups.append(venue.get_publication_chairs_id())
        venue.preferred_emails_groups = preferred_emails_groups

    venue.submission_stage = openreview.stages.SubmissionStage(
        name=domain.content.get('submission_name', {}).get('value', 'Submission'),
    )
    return venue
