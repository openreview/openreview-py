import openreview
import datetime
import json

def get_conference(client, request_form_id):

    builder = get_conference_builder(client, request_form_id)
    return builder.get_result()

def get_conference_builder(client, request_form_id):

    note = client.get_note(request_form_id)

    if note.invitation not in 'OpenReview.net/Support/-/Request_Form':
        raise openreview.OpenReviewException('Invalid request form invitation')

    if not note.content.get('venue_id') and not note.content.get('conference_id'):
        raise openreview.OpenReviewException('venue_id is not set')

    builder = openreview.conference.ConferenceBuilder(client)
    builder.set_request_form_id(request_form_id)

    conference_start_date_str = 'TBD'
    conference_start_date = None
    start_date = note.content.get('Venue Start Date', note.content.get('Conference Start Date', '')).strip()
    if start_date:
        try:
            conference_start_date = datetime.datetime.strptime(start_date, '%Y/%m/%d %H:%M')
        except ValueError:
            conference_start_date = datetime.datetime.strptime(start_date, '%Y/%m/%d')
        conference_start_date_str = conference_start_date.strftime('%b %d %Y')

    submission_start_date_str = ''
    submission_start_date = note.content.get('Submission Start Date', '').strip()
    if submission_start_date:
        try:
            submission_start_date = datetime.datetime.strptime(submission_start_date, '%Y/%m/%d %H:%M')
        except ValueError:
            submission_start_date = datetime.datetime.strptime(submission_start_date, '%Y/%m/%d')
        submission_start_date_str = submission_start_date.strftime('%b %d %Y %I:%M%p')
    else:
        submission_start_date = None

    submission_due_date_str = 'TBD'
    submission_due_date = note.content.get('Submission Deadline', '').strip()
    if submission_due_date:
        try:
            submission_due_date = datetime.datetime.strptime(submission_due_date, '%Y/%m/%d %H:%M')
        except ValueError:
            submission_due_date = datetime.datetime.strptime(submission_due_date, '%Y/%m/%d')
        submission_due_date_str = submission_due_date.strftime('%b %d %Y %I:%M%p')
    else:
        submission_due_date = None

    builder.set_conference_id(note.content.get('venue_id') if note.content.get('venue_id', None) else note.content.get('conference_id'))
    builder.set_conference_name(note.content.get('Official Venue Name', note.content.get('Official Conference Name')))
    builder.set_conference_short_name(note.content.get('Abbreviated Venue Name', note.content.get('Abbreviated Conference Name')))
    if conference_start_date:
        builder.set_conference_year(conference_start_date.year)

    homepage_header = {
        'title': note.content['title'],
        'subtitle': note.content.get('Abbreviated Venue Name', note.content.get('Abbreviated Conference Name')),
        'deadline': 'Submission Start: ' + submission_start_date_str + ' UTC-0, End: ' + submission_due_date_str + ' UTC-0',
        'date': conference_start_date_str,
        'website': note.content['Official Website URL'],
        'location': note.content.get('Location'),
        'contact': note.content.get('contact_email')
    }
    override_header = note.content.get('homepage_override', '')
    if override_header:
        for key in override_header.keys():
            homepage_header[key] = override_header[key]

    builder.set_homepage_header(homepage_header)

    if note.content.get('Area Chairs (Metareviewers)', '') in ['Yes, our venue has Area Chairs', 'Yes, our conference has Area Chairs']:
        builder.has_area_chairs(True)

    double_blind = (note.content.get('Author and Reviewer Anonymity', None) == 'Double-blind')

    public = (note.content.get('Open Reviewing Policy', '') in ['Submissions and reviews should both be public.', 'Submissions should be public, but reviews should be private.'])

    builder.set_override_homepage(True)

    submission_additional_options = note.content.get('Additional Submission Options', {})
    if isinstance(submission_additional_options, str):
        submission_additional_options = json.loads(submission_additional_options.strip())

    submission_remove_options = note.content.get('remove_submission_options', [])

    # Create review invitation during submission process function only when the venue is public, single blind and the review stage is setup.
    create_review_invitation = (not double_blind) and note.content.get('Open Reviewing Policy', '') == 'Submissions and reviews should both be public.' and note.content.get('make_reviews_public', None)

    builder.set_submission_stage(
        double_blind = double_blind,
        public = public,
        start_date = submission_start_date,
        due_date = submission_due_date,
        additional_fields = submission_additional_options,
        remove_fields = submission_remove_options,
        email_pcs=False, ## Need to add this setting to the form
        create_groups=(not double_blind),
        create_review_invitation=create_review_invitation
        )

    paper_matching_options = note.content.get('Paper Matching', [])
    if 'OpenReview Affinity' in paper_matching_options:
        builder.set_expertise_selection_stage(due_date = submission_due_date)

    if 'Organizers will assign papers manually' in paper_matching_options:
        builder.enable_reviewer_reassignment(enable = True)

    ## Contact Emails is deprecated
    program_chair_ids = note.content.get('Contact Emails', []) + note.content.get('program_chair_emails', [])
    builder.set_conference_program_chairs_ids(program_chair_ids)

    return builder

def get_bid_stage(client, request_forum):
    bid_start_date = request_forum.content.get('bid_start_date', '').strip()
    if bid_start_date:
        try:
            bid_start_date = datetime.datetime.strptime(bid_start_date, '%Y/%m/%d %H:%M')
        except ValueError:
            bid_start_date = datetime.datetime.strptime(bid_start_date, '%Y/%m/%d')
    else:
        bid_start_date = None

    bid_due_date = request_forum.content.get('bid_due_date', '').strip()
    if bid_due_date:
        try:
            bid_due_date = datetime.datetime.strptime(bid_due_date, '%Y/%m/%d %H:%M')
        except ValueError:
            bid_due_date = datetime.datetime.strptime(bid_due_date, '%Y/%m/%d')
    else:
        bid_due_date = None

    return openreview.BidStage(start_date = bid_start_date, due_date = bid_due_date, request_count = int(request_forum.content.get('bid_count', 50)))

def get_review_stage(client, request_forum):
    review_start_date = request_forum.content.get('review_start_date', '').strip()
    if review_start_date:
        try:
            review_start_date = datetime.datetime.strptime(review_start_date, '%Y/%m/%d %H:%M')
        except ValueError:
            review_start_date = datetime.datetime.strptime(review_start_date, '%Y/%m/%d')
    else:
        review_start_date = None

    review_due_date = request_forum.content.get('review_deadline', '').strip()
    if review_due_date:
        try:
            review_due_date = datetime.datetime.strptime(review_due_date, '%Y/%m/%d %H:%M')
        except ValueError:
            review_due_date = datetime.datetime.strptime(review_due_date, '%Y/%m/%d')
    else:
        review_due_date = None

    review_form_additional_options = request_forum.content.get('additional_review_form_options', {})

    review_form_remove_options = request_forum.content.get('remove_review_form_options', '')
    if ',' in review_form_remove_options:
        review_form_remove_options = [field.strip() for field in review_form_remove_options.strip().split(',') if field.strip()]
    if not isinstance(review_form_remove_options, list):
        review_form_remove_options = []

    readers_map = {
        'Reviews should be immediately revealed to all reviewers': openreview.ReviewStage.Readers.REVIEWERS,
        'Reviews should be immediately revealed to the paper\'s reviewers': openreview.ReviewStage.Readers.REVIEWERS_ASSIGNED,
        'Reviews should be immediately revealed to the paper\'s reviewers who have already submitted their review': openreview.ReviewStage.Readers.REVIEWERS_SUBMITTED,
        'Review should not be revealed to any reviewer, except to the author of the review': openreview.ReviewStage.Readers.REVIEWER_SIGNATURE
    }
    reviewer_readers= request_forum.content.get('release_reviews_to_reviewers', '')

    #Deprecated
    if reviewer_readers.startswith('Yes'):
        release_to_reviewers = openreview.ReviewStage.Readers.REVIEWERS_ASSIGNED
    else:
        release_to_reviewers = readers_map.get(reviewer_readers, openreview.ReviewStage.Readers.REVIEWER_SIGNATURE)

    return openreview.ReviewStage(
        start_date = review_start_date,
        due_date = review_due_date,
        allow_de_anonymization = (request_forum.content.get('Author and Reviewer Anonymity', None) == 'No anonymity'),
        public = (request_forum.content.get('make_reviews_public', None) == 'Yes, reviews should be revealed publicly when they are posted'),
        release_to_authors = (request_forum.content.get('release_reviews_to_authors', '').startswith('Yes')),
        release_to_reviewers = release_to_reviewers,
        email_pcs = (request_forum.content.get('email_program_chairs_about_reviews', '').startswith('Yes')),
        additional_fields = review_form_additional_options,
        remove_fields = review_form_remove_options
    )

def get_meta_review_stage(client, request_forum):
    meta_review_start_date = request_forum.content.get('meta_review_start_date', '').strip()
    if meta_review_start_date:
        try:
            meta_review_start_date = datetime.datetime.strptime(meta_review_start_date, '%Y/%m/%d %H:%M')
        except ValueError:
            meta_review_start_date = datetime.datetime.strptime(meta_review_start_date, '%Y/%m/%d')
    else:
        meta_review_start_date = None

    meta_review_due_date = request_forum.content.get('meta_review_deadline', '').strip()
    if meta_review_due_date:
        try:
            meta_review_due_date = datetime.datetime.strptime(meta_review_due_date, '%Y/%m/%d %H:%M')
        except ValueError:
            meta_review_due_date = datetime.datetime.strptime(meta_review_due_date, '%Y/%m/%d')
    else:
        meta_review_due_date = None

    additional_fields = {}
    options = request_forum.content.get('recommendation_options', '').strip()
    if options:
        additional_fields = {'recommendation': {
            'value-dropdown':[s.translate(str.maketrans('', '', '"\'')).strip() for s in options.split(',')]},
            'required': True}

    return openreview.MetaReviewStage(
        start_date = meta_review_start_date,
        due_date = meta_review_due_date,
        public = request_forum.content.get('make_meta_reviews_public', '').startswith('Yes'),
        additional_fields = additional_fields
    )

def get_decision_stage(client, request_forum):
    decision_start_date = request_forum.content.get('decision_start_date', '').strip()
    if decision_start_date:
        try:
            decision_start_date = datetime.datetime.strptime(decision_start_date, '%Y/%m/%d %H:%M')
        except ValueError:
            decision_start_date = datetime.datetime.strptime(decision_start_date, '%Y/%m/%d')
    else:
        decision_start_date = None

    decision_due_date = request_forum.content.get('decision_deadline', '').strip()
    if decision_due_date:
        try:
            decision_due_date = datetime.datetime.strptime(decision_due_date, '%Y/%m/%d %H:%M')
        except ValueError:
            decision_due_date = datetime.datetime.strptime(decision_due_date, '%Y/%m/%d')
    else:
        decision_due_date = None

    decision_options = request_forum.content.get('decision_options', '').strip()
    if decision_options:
        decision_options = [s.translate(str.maketrans('', '', '"\'')).strip() for s in decision_options.split(',')]
        return openreview.DecisionStage(
            options = decision_options,
            start_date = decision_start_date,
            due_date = decision_due_date,
            public = request_forum.content.get('make_decisions_public', '').startswith('Yes'),
            release_to_authors = request_forum.content.get('release_decisions_to_authors', '').startswith('Yes'),
            release_to_reviewers = request_forum.content.get('release_decisions_to_reviewers', '').startswith('Yes'),
            email_authors = request_forum.content.get('notify_to_authors', '').startswith('Yes'))
    else:
        return openreview.DecisionStage(
            start_date = decision_start_date,
            due_date = decision_due_date,
            public = request_forum.content.get('make_decisions_public', '').startswith('Yes'),
            release_to_authors = request_forum.content.get('release_decisions_to_authors', '').startswith('Yes'),
            release_to_reviewers = request_forum.content.get('release_decisions_to_reviewers', '').startswith('Yes'),
            email_authors = request_forum.content.get('notify_to_authors', '').startswith('Yes'))