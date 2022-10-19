import openreview
import pytest
import datetime

class TestICMLConference():


    def test_create_conference(self, client, openreview_client, helpers):

        now = datetime.datetime.utcnow()
        due_date = now + datetime.timedelta(days=3)

        # Post the request form note
        pc_client=helpers.create_user('pc@icml.cc', 'Program', 'ICMLChair')


        request_form_note = pc_client.post_note(openreview.Note(
            invitation='openreview.net/Support/-/Request_Form',
            signatures=['~Program_ICMLChair1'],
            readers=[
                'openreview.net/Support',
                '~Program_ICMLChair1'
            ],
            writers=[],
            content={
                'title': 'Thirty-ninth International Conference on Machine Learning',
                'Official Venue Name': 'Thirty-ninth International Conference on Machine Learning',
                'Abbreviated Venue Name': 'ICML 2023',
                'Official Website URL': 'https://icml.cc',
                'program_chair_emails': ['pc@icml.cc'],
                'contact_email': 'pc@icml.cc',
                'Area Chairs (Metareviewers)': 'Yes, our venue has Area Chairs',
                'senior_area_chairs': 'Yes, our venue has Senior Area Chairs',
                'Venue Start Date': '2023/07/01',
                'Submission Deadline': due_date.strftime('%Y/%m/%d'),
                'Location': 'Virtual',
                'Paper Matching': [
                    'Reviewer Bid Scores',
                    'OpenReview Affinity'],
                'Author and Reviewer Anonymity': 'Double-blind',
                'reviewer_identity': ['Program Chairs', 'Assigned Senior Area Chair', 'Assigned Area Chair', 'Assigned Reviewers'],
                'area_chair_identity': ['Program Chairs', 'Assigned Senior Area Chair', 'Assigned Area Chair', 'Assigned Reviewers'],
                'senior_area_chair_identity': ['Program Chairs', 'Assigned Senior Area Chair', 'Assigned Area Chair', 'Assigned Reviewers'],
                'Open Reviewing Policy': 'Submissions and reviews should both be private.',
                'submission_readers': 'Program chairs and paper authors only',
                'How did you hear about us?': 'ML conferences',
                'Expected Submissions': '100',
                'use_recruitment_template': 'Yes',
                'api_version': '2'
            }))

        helpers.await_queue()

        # Post a deploy note
        client.post_note(openreview.Note(
            content={'venue_id': 'ICML.cc/2023/Conference'},
            forum=request_form_note.forum,
            invitation='openreview.net/Support/-/Request{}/Deploy'.format(request_form_note.number),
            readers=['openreview.net/Support'],
            referent=request_form_note.forum,
            replyto=request_form_note.forum,
            signatures=['openreview.net/Support'],
            writers=['openreview.net/Support']
        ))

        helpers.await_queue()

        assert openreview_client.get_group('ICML.cc/2023/Conference')
        assert openreview_client.get_group('ICML.cc/2023/Conference/Senior_Area_Chairs')
        assert openreview_client.get_group('ICML.cc/2023/Conference/Area_Chairs')
        assert openreview_client.get_group('ICML.cc/2023/Conference/Reviewers')
        assert openreview_client.get_group('ICML.cc/2023/Conference/Authors')
