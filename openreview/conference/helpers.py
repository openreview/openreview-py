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
    start_date = note.content.get('Venue Start Date', note.content.get('Conference Start Date'))
    if start_date:
        try:
            conference_start_date = datetime.datetime.strptime(start_date, '%Y/%m/%d %H:%M')
        except ValueError:
            conference_start_date = datetime.datetime.strptime(start_date, '%Y/%m/%d')
        conference_start_date_str = conference_start_date.strftime('%b %d %Y')

    submission_start_date_str = ''
    submission_start_date = None
    if note.content.get('Submission Start Date'):
        try:
            submission_start_date = datetime.datetime.strptime(note.content.get('Submission Start Date'), '%Y/%m/%d %H:%M')
        except ValueError:
            submission_start_date = datetime.datetime.strptime(note.content.get('Submission Start Date'), '%Y/%m/%d')
        submission_start_date_str = submission_start_date.strftime('%b %d %Y %I:%M%p')

    submission_due_date_str = 'TBD'
    submission_due_date = None
    if note.content.get('Submission Deadline'):
        try:
            submission_due_date = datetime.datetime.strptime(note.content.get('Submission Deadline'), '%Y/%m/%d %H:%M')
        except ValueError:
            submission_due_date = datetime.datetime.strptime(note.content.get('Submission Deadline'), '%Y/%m/%d')
        submission_due_date_str = submission_due_date.strftime('%b %d %Y %I:%M%p')

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

    builder.set_submission_stage(double_blind=double_blind, public=public, start_date = submission_start_date, due_date = submission_due_date, additional_fields = submission_additional_options)

    conference = builder.get_result()
    conference.set_program_chairs(emails = note.content['Contact Emails'])
    return conference

def get_bid_stage(client, request_form_id):
    note = client.get_note(request_form_id)
    bid_start_date = None
    if note.content.get('bid_start_date', None):
        try:
            bid_start_date = datetime.datetime.strptime(note.content.get('bid_start_date', None), '%Y/%m/%d %H:%M')
        except ValueError:
            bid_start_date = datetime.datetime.strptime(note.content.get('bid_start_date', None), '%Y/%m/%d')

    bid_due_date = None
    if note.content.get('bid_due_date', None):
        try:
            bid_due_date = datetime.datetime.strptime(note.content.get('bid_due_date'), '%Y/%m/%d %H:%M')
        except ValueError:
            bid_due_date = datetime.datetime.strptime(note.content.get('bid_due_date'), '%Y/%m/%d')

    return openreview.BidStage(start_date = bid_start_date, due_date = bid_due_date, request_count = note.content.get('bid_count', 50))

def get_review_stage(client, request_form_id):
    note = client.get_note(request_form_id)
    review_start_date = None
    if note.content.get('review_start_date', None):
        try:
            review_start_date = datetime.datetime.strptime(note.content.get('review_start_date', None), '%Y/%m/%d %H:%M')
        except ValueError:
            review_start_date = datetime.datetime.strptime(note.content.get('review_start_date', None), '%Y/%m/%d')

    review_due_date = None
    if note.content.get('review_deadline', None):
        try:
            review_due_date = datetime.datetime.strptime(note.content.get('review_deadline', None), '%Y/%m/%d %H:%M')
        except ValueError:
            review_due_date = datetime.datetime.strptime(note.content.get('review_deadline', None), '%Y/%m/%d')

    review_additional_fields = note.content.get('additional_review_options', {})
    if review_additional_fields:
        review_additional_fields = json.loads(review_additional_fields)

    return openreview.ReviewStage(start_date = review_start_date, due_date = review_due_date, allow_de_anonymization = (note.content.get('Author and Reviewer Anonymity', None) == 'No anonymity'), public = (note.content.get('Open Reviewing Policy', None) == 'Submissions and reviews should both be public.'), release_to_authors = (note.content.get('release_reviews_to_authors', False) == 'Yes'), release_to_reviewers = (note.content.get('release_reviews_to_reviewers', False) == 'Yes'), email_pcs = (note.content.get('email_program_Chairs_about_reviews', False) == 'Yes'), additional_fields = review_additional_fields)

def get_meta_review_stage(client, request_form_id):
    note = client.get_note(request_form_id)
    meta_review_start_date = None
    if note.content.get('meta_review_start_date', None):
        try:
            meta_review_start_date = datetime.datetime.strptime(note.content.get('meta_review_start_date', None), '%Y/%m/%d %H:%M')
        except ValueError:
            meta_review_start_date = datetime.datetime.strptime(note.content.get('meta_review_start_date', None), '%Y/%m/%d')

    meta_review_due_date = None
    if note.content.get('meta_review_deadline', None):
        try:
            meta_review_due_date = datetime.datetime.strptime(note.content.get('meta_review_deadline', None), '%Y/%m/%d %H:%M')
        except ValueError:
            meta_review_due_date = datetime.datetime.strptime(note.content.get('meta_review_deadline', None), '%Y/%m/%d')

    meta_review_additional_fields = note.content.get('additional_meta_review_options', {})
    if meta_review_additional_fields:
        meta_review_additional_fields = json.loads(meta_review_additional_fields)

    return openreview.MetaReviewStage(start_date = meta_review_start_date, due_date = meta_review_due_date, public = (note.content.get('make_meta_reviews_public', None) == 'Yes'), additional_fields = meta_review_additional_fields)

def get_decision_stage(client, request_form_id):
    note = client.get_note(request_form_id)
    decision_start_date = None
    if note.content.get('decision_start_date', None):
        try:
            decision_start_date = datetime.datetime.strptime(note.content.get('decision_start_date', None), '%Y/%m/%d %H:%M')
        except ValueError:
            decision_start_date = datetime.datetime.strptime(note.content.get('decision_start_date', None), '%Y/%m/%d')

    decision_due_date = None
    if note.content.get('decision_deadline', None):
        try:
            decision_due_date = datetime.datetime.strptime(note.content.get('decision_deadline', None), '%Y/%m/%d %H:%M')
        except ValueError:
            decision_due_date = datetime.datetime.strptime(note.content.get('decision_deadline', None), '%Y/%m/%d')

    decision_options = note.content.get('decision_options', None)
    if decision_options:
        decision_options = [s.translate(str.maketrans('', '', '"\'')).strip() for s in decision_options.split(',')]
        return openreview.DecisionStage(options = decision_options, start_date = decision_start_date, due_date = decision_due_date, public = (note.content.get('make_decisions_public', None) == 'Yes'), release_to_authors = (note.content.get('release_decisions_to_authors', None) == 'Yes'), release_to_reviewers = (note.content.get('release_decisions_to_reviewers', None) == 'Yes'))
    else:
        return openreview.DecisionStage(start_date = decision_start_date, due_date = decision_due_date, public = (note.content.get('make_decisions_public', None) == 'Yes'))