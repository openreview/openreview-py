import openreview
import datetime
import json

def get_conference(client, request_form_id):

    note = client.get_note(request_form_id)

    if note.invitation not in 'OpenReview.net/Support/-/Request_Form':
        raise openreview.OpenReviewException('Invalid request form invitation')

    if not note.content.get('venue_id') and not note.content.get('conference_id'):
        raise openreview.OpenReviewException('venue_id is not set')

    builder = openreview.conference.ConferenceBuilder(client)
    builder.set_request_form_id(request_form_id)

    conference_start_date_str = 'TBD'
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
    builder.set_homepage_header({
    'title': note.content['title'],
    'subtitle': note.content.get('Abbreviated Venue Name', note.content.get('Abbreviated Conference Name')),
    'deadline': 'Submission Start: ' + submission_start_date_str + ', End: ' + submission_due_date_str,
    'date': conference_start_date_str,
    'website': note.content['Official Website URL'],
    'location': note.content.get('Location')
    })

    if note.content.get('Area Chairs (Metareviewers)', '') in ['Yes, our venue has Area Chairs', 'Yes, our conference has Area Chairs']:
        builder.has_area_chairs(True)

    double_blind = (note.content.get('Author and Reviewer Anonymity', None) == 'Double-blind')

    public = (note.content.get('Open Reviewing Policy', '') in ['Submissions and reviews should both be public.', 'Submissions should be public, but reviews should be private.'])

    builder.set_override_homepage(True)

    submission_additional_options = note.content.get('Additional Submission Options', {})
    if submission_additional_options:
            submission_additional_options = json.loads(submission_additional_options)

    builder.set_submission_stage(double_blind = double_blind, public = public, start_date = submission_start_date, due_date = submission_due_date, additional_fields = submission_additional_options)

    conference = builder.get_result()
    conference.set_program_chairs(emails = note.content['Contact Emails'])
    return conference

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

    return openreview.BidStage(start_date = bid_start_date, due_date = bid_due_date, request_count = request_forum.content.get('bid_count', 50))

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

    return openreview.ReviewStage(start_date = review_start_date, due_date = review_due_date, allow_de_anonymization = (request_forum.content.get('Author and Reviewer Anonymity', None) == 'No anonymity'), public = (request_forum.content.get('Open Reviewing Policy', None) == 'Submissions and reviews should both be public.'), release_to_authors = (request_forum.content.get('release_reviews_to_authors', False) == 'Yes'), release_to_reviewers = (request_forum.content.get('release_reviews_to_reviewers', False) == 'Yes'), email_pcs = (request_forum.content.get('email_program_Chairs_about_reviews', False) == 'Yes'))

def get_meta_review_stage(client, request_forum):
    meta_review_start_date = request_forum.content.get('meta_review_start_date', None)
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

    return openreview.MetaReviewStage(start_date = meta_review_start_date, due_date = meta_review_due_date, public = (request_forum.content.get('make_meta_reviews_public', None) == 'Yes'))

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
        return openreview.DecisionStage(options = decision_options, start_date = decision_start_date, due_date = decision_due_date, public = (request_forum.content.get('make_decisions_public', None) == 'Yes'), release_to_authors = (request_forum.content.get('release_decisions_to_authors', None) == 'Yes'), release_to_reviewers = (request_forum.content.get('release_decisions_to_reviewers', None) == 'Yes'))
    else:
        return openreview.DecisionStage(start_date = decision_start_date, due_date = decision_due_date, public = (request_forum.content.get('make_decisions_public', None) == 'Yes'), release_to_authors = (request_forum.content.get('release_decisions_to_authors', None) == 'Yes'), release_to_reviewers = (request_forum.content.get('release_decisions_to_reviewers', None) == 'Yes'))