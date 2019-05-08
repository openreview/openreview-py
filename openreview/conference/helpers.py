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

    conference_start_date_str = 'TBD'
    if note.content.get('Venue Start Date'):
        try:
            conference_start_date = datetime.datetime.strptime(note.content.get('Venue Start Date'), '%Y/%m/%d %H:%M')
        except ValueError:
            conference_start_date = datetime.datetime.strptime(note.content.get('Venue Start Date'), '%Y/%m/%d')
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
    builder.set_conference_name(note.content['Official Venue Name'])
    builder.set_conference_short_name(note.content['Abbreviated Venue Name'])
    builder.set_homepage_header({
    'title': note.content['title'],
    'subtitle': note.content['Abbreviated Venue Name'],
    'deadline': 'Submission Start: ' + submission_start_date_str + ', End: ' + submission_due_date_str,
    'date': conference_start_date_str,
    'website': note.content['Official Website URL'],
    'location': note.content.get('Location')
    })

    if 'Yes, our venue has Area Chairs' == note.content.get('Area Chairs (Metareviewers)', ''):
        builder.has_area_chairs(True)

    if 'Double-blind' == note.content.get('Author and Reviewer Anonymity', ''):
        builder.set_double_blind(True)

    if 'Submissions and reviews should both be public.' == note.content.get('Open Reviewing Policy', '') or \
        'Submissions should be public, but reviews should be private.' == note.content.get('Open Reviewing Policy', '') :
        builder.set_submission_public(True)


    builder.set_override_homepage(True)
    conference = builder.get_result()

    submission_additional_options = note.content.get('Additional Submission Options', {})
    if submission_additional_options:
            submission_additional_options = json.loads(submission_additional_options)

    conference.open_submissions(start_date = submission_start_date, due_date = submission_due_date, additional_fields = submission_additional_options)
    conference.set_program_chairs(emails = note.content['Contact Emails'])
    return conference