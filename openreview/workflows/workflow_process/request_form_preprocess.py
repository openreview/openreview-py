def process(client, edit, invitation):

    request_note = edit.note
    venue_agreement = request_note.content['venue_organizer_agreement']['value']

    if len(venue_agreement) != 9:
        raise openreview.OpenReviewException('Please be sure to acknowledge and agree to all terms in the Venue Organizer Agreement.')
    
    submission_deadline = request_note.content['submission_deadline']['value']
    if submission_deadline < openreview.tools.datetime_millis(datetime.datetime.now()):
        raise openreview.OpenReviewException('The submission deadline must be in the future.')

    submission_start_date = request_note.content['submission_start_date']['value']
    if submission_start_date > submission_deadline:
        raise openreview.OpenReviewException('The submission start date must be before the submission deadline.')
    
    full_submission_deadline = request_note.content.get('full_submission_deadline', {}).get('value')
    if full_submission_deadline and full_submission_deadline < submission_deadline:
        raise openreview.OpenReviewException('The full submission deadline must be after the submission deadline.')

    reviewer_role_name = request_note.content.get('reviewer_role_name', {}).get('value', 'Reviewers')
    area_chair_role_name = request_note.content.get('area_chair_role_name', {}).get('value', 'Area_Chairs')
    if reviewer_role_name == area_chair_role_name:
        raise openreview.OpenReviewException('The reviewer role name and area chair role name must be different.')