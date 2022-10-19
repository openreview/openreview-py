import openreview
import pytest
import datetime
import re
from selenium.webdriver.common.by import By

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

        submission_invitation = openreview_client.get_invitation('ICML.cc/2023/Conference/-/Submission')
        assert submission_invitation
        ##assert submission_invitation.duedate == openreview.tools.datetime_millis(due_date)


    def test_sac_recruitment(self, client, openreview_client, helpers, request_page, selenium):

        pc_client=openreview.Client(username='pc@icml.cc', password='1234')
        request_form=pc_client.get_notes(invitation='openreview.net/Support/-/Request_Form')[0]

        reviewer_details = '''sac1@icml.cc, SAC ICMLOne\nsac2@icml.cc, SAC ICMLTwo'''
        pc_client.post_note(openreview.Note(
            content={
                'title': 'Recruitment',
                'invitee_role': 'Senior_Area_Chairs',
                'invitee_details': reviewer_details,
                'invitation_email_subject': '[ICML 2023] Invitation to serve as {{invitee_role}}',
                'invitation_email_content': 'Dear {{fullname}},\n\nYou have been nominated by the program chair committee of Theoretical Foundations of RL Workshop @ ICML 2020 to serve as {{invitee_role}}.\n\n{{invitation_url}}\n\nCheers!\n\nProgram Chairs'
            },
            forum=request_form.forum,
            replyto=request_form.forum,
            invitation='openreview.net/Support/-/Request{}/Recruitment'.format(request_form.number),
            readers=['ICML.cc/2023/Conference/Program_Chairs', 'openreview.net/Support'],
            signatures=['~Program_ICMLChair1'],
            writers=[]
        ))

        helpers.await_queue()

        assert len(openreview_client.get_group('ICML.cc/2023/Conference/Senior_Area_Chairs').members) == 0
        assert len(openreview_client.get_group('ICML.cc/2023/Conference/Senior_Area_Chairs/Invited').members) == 2

        messages = openreview_client.get_messages(subject = '[ICML 2023] Invitation to serve as Senior Area Chair')
        assert len(messages) == 2

        for message in messages:
            text = message['content']['text']
            
            invitation_url = re.search('https://.*\n', text).group(0).replace('https://openreview.net', 'http://localhost:3030').replace('&amp;', '&')[:-1]
            print('invitation_url', invitation_url)
            helpers.respond_invitation(selenium, request_page, invitation_url, accept=True)

        helpers.await_queue()

        messages = client.get_messages(subject='[ICML 2023] Senior Area Chair Invitation accepted')
        assert len(messages) == 2

        assert len(openreview_client.get_group('ICML.cc/2023/Conference/Senior_Area_Chairs').members) == 2
        assert len(openreview_client.get_group('ICML.cc/2023/Conference/Senior_Area_Chairs/Invited').members) == 2 