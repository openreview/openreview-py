import time
import openreview
import pytest
import datetime
import re
import random
import os
import csv
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException

class TestAAAIConference():

    def test_create_conference(self, client, openreview_client, helpers):

        now = datetime.datetime.utcnow()
        due_date = now + datetime.timedelta(days=3)

        # Post the request form note
        helpers.create_user('pc@aaai.org', 'Program', 'AAAIChair')
        pc_client = openreview.Client(username='pc@aaai.org', password=helpers.strong_password)


        helpers.create_user('ac1@aaai.org', 'AC', 'AAAIOne')
        helpers.create_user('ac2@aaai.org', 'AC', 'AAAITwo')
        helpers.create_user('senior_program_committee1@aaai.org', 'Senior Program Committee', 'AAAIOne')
        helpers.create_user('senior_program_committee2@aaai.org', 'Senior Program Committee', 'AAAITwo')
        helpers.create_user('program_committee1@aaai.org', 'Program Committee', 'AAAIOne')
        helpers.create_user('program_committee2@aaai.org', 'Program Committee', 'AAAITwo')
        helpers.create_user('program_committee3@aaai.org', 'Program Committee', 'AAAIThree')

        request_form_note = pc_client.post_note(openreview.Note(
            invitation='openreview.net/Support/-/Request_Form',
            signatures=['~Program_AAAIChair1'],
            readers=[
                'openreview.net/Support',
                '~Program_AAAIChair1'
            ],
            writers=[],
            content={
                'title': 'The 39th Annual AAAI Conference on Artificial Intelligence',
                'Official Venue Name': 'The 39th Annual AAAI Conference on Artificial Intelligence',
                'Abbreviated Venue Name': 'AAAI 2025',
                'Official Website URL': 'https://aaai.org/conference/aaai-25/',
                'program_chair_emails': ['pc@aaai.org'],
                'contact_email': 'pc@aaai.org',
                'publication_chairs':'No, our venue does not have Publication Chairs',
                'Area Chairs (Metareviewers)': 'Yes, our venue has Area Chairs',
                'senior_area_chairs': 'Yes, our venue has Senior Area Chairs',
                'senior_area_chairs_assignment': 'Area Chairs',
                'ethics_chairs_and_reviewers': 'No, our venue does not have Ethics Chairs and Reviewers',
                'Venue Start Date': '2025/07/01',
                'Submission Deadline': due_date.strftime('%Y/%m/%d'),
                'Location': 'Philadelphia, PA',
                'submission_reviewer_assignment': 'Automatic',
                'Author and Reviewer Anonymity': 'Double-blind',
                'reviewer_identity': ['Program Chairs', 'Assigned Senior Area Chair', 'Assigned Area Chair'],
                'area_chair_identity': ['Program Chairs', 'Assigned Senior Area Chair', 'Assigned Area Chair', 'Assigned Reviewers'],
                'senior_area_chair_identity': ['Program Chairs', 'Assigned Senior Area Chair', 'Assigned Area Chair'],
                'submission_readers': 'Program chairs and paper authors only',
                'How did you hear about us?': 'ML conferences',
                'Expected Submissions': '10000',
                'use_recruitment_template': 'Yes',
                'api_version': '2',
                'submission_license': ['CC BY 4.0']
            }))

        helpers.await_queue()

        # Use super user to update the roles
        request_form_note.content['reviewer_roles'] = ['Program_Committee']
        request_form_note.content['area_chair_roles'] = ['Senior_Program_Committee']
        request_form_note.content['senior_area_chair_roles'] = ['Area_Chairs']
        client.post_note(request_form_note)

        helpers.await_queue()

        # Post a deploy note
        client.post_note(openreview.Note(
            content={'venue_id': 'AAAI.org/2025/Conference'},
            forum=request_form_note.forum,
            invitation='openreview.net/Support/-/Request{}/Deploy'.format(request_form_note.number),
            readers=['openreview.net/Support'],
            referent=request_form_note.forum,
            replyto=request_form_note.forum,
            signatures=['openreview.net/Support'],
            writers=['openreview.net/Support']
        ))

        helpers.await_queue()

        assert openreview_client.get_group('AAAI.org/2025/Conference')
        assert openreview_client.get_group('AAAI.org/2025/Conference/Area_Chairs')
        assert openreview_client.get_group('AAAI.org/2025/Conference/Senior_Program_Committee')
        assert openreview_client.get_group('AAAI.org/2025/Conference/Program_Committee')
        assert openreview_client.get_group('AAAI.org/2025/Conference/Authors')

        submission_invitation = openreview_client.get_invitation('AAAI.org/2025/Conference/-/Submission')
        assert submission_invitation
        assert submission_invitation.duedate

        assert openreview_client.get_invitation('AAAI.org/2025/Conference/Program_Committee/-/Expertise_Selection')
        assert openreview_client.get_invitation('AAAI.org/2025/Conference/Senior_Program_Committee/-/Expertise_Selection')
        assert openreview_client.get_invitation('AAAI.org/2025/Conference/Area_Chairs/-/Expertise_Selection')


    def test_sac_recruitment(self, client, openreview_client, helpers, request_page, selenium):

        pc_client=openreview.Client(username='pc@aaai.org', password=helpers.strong_password)
        request_form=pc_client.get_notes(invitation='openreview.net/Support/-/Request_Form')[0]

        reviewer_details = '''ac1@aaai.org, AC AAAIOne\nac2@aaai.org, AC AAAITwo'''
        pc_client.post_note(openreview.Note(
            content={
                'title': 'Recruitment',
                'invitee_role': 'Area_Chairs',
                'invitee_details': reviewer_details,
                'invitation_email_subject': '[AAAI 2025] Invitation to serve as {{invitee_role}}',
                'invitation_email_content': 'Dear {{fullname}},\n\nYou have been nominated by the program chair committee of AAAI to serve as {{invitee_role}}.\n\n{{invitation_url}}\n\nCheers!\n\nProgram Chairs'
            },
            forum=request_form.forum,
            replyto=request_form.forum,
            invitation='openreview.net/Support/-/Request{}/Recruitment'.format(request_form.number),
            readers=['AAAI.org/2025/Conference/Program_Chairs', 'openreview.net/Support'],
            signatures=['~Program_AAAIChair1'],
            writers=[]
        ))

        helpers.await_queue()

        assert len(openreview_client.get_group('AAAI.org/2025/Conference/Area_Chairs').members) == 0
        group = openreview_client.get_group('AAAI.org/2025/Conference/Area_Chairs/Invited')
        assert len(group.members) == 2
        assert group.readers == ['AAAI.org/2025/Conference', 'AAAI.org/2025/Conference/Area_Chairs/Invited']

        messages = openreview_client.get_messages(subject = '[AAAI 2025] Invitation to serve as Area Chair')
        assert len(messages) == 2

        for message in messages:
            text = message['content']['text']

            invitation_url = re.search('https://.*\n', text).group(0).replace('https://openreview.net', 'http://localhost:3030').replace('&amp;', '&')[:-1]
            helpers.respond_invitation(selenium, request_page, invitation_url, accept=True)

        helpers.await_queue_edit(openreview_client, invitation='AAAI.org/2025/Conference/Area_Chairs/-/Recruitment', count=2)

        messages = client.get_messages(subject='[AAAI 2025] Area Chair Invitation accepted')
        assert len(messages) == 2

        assert len(openreview_client.get_group('AAAI.org/2025/Conference/Area_Chairs').members) == 2
        assert len(openreview_client.get_group('AAAI.org/2025/Conference/Area_Chairs/Invited').members) == 2

    def test_ac_recruitment(self, client, openreview_client, helpers, request_page, selenium):

        pc_client=openreview.Client(username='pc@aaai.org', password=helpers.strong_password)
        request_form=pc_client.get_notes(invitation='openreview.net/Support/-/Request_Form')[0]

        reviewer_details = '''senior_program_committee1@aaai.org, Senior Program Committee AAAIOne\nsenior_program_committee2@aaai.org, Senior Program Committee AAAITwo'''
        pc_client.post_note(openreview.Note(
            content={
                'title': 'Recruitment',
                'invitee_role': 'Senior_Program_Committee',
                'invitee_details': reviewer_details,
                'invitation_email_subject': '[AAAI 2025] Invitation to serve as {{invitee_role}}',
                'invitation_email_content': 'Dear {{fullname}},\n\nYou have been nominated by the program chair committee of AAAI to serve as {{invitee_role}}.\n\n{{invitation_url}}\n\nCheers!\n\nProgram Chairs'
            },
            forum=request_form.forum,
            replyto=request_form.forum,
            invitation='openreview.net/Support/-/Request{}/Recruitment'.format(request_form.number),
            readers=['AAAI.org/2025/Conference/Program_Chairs', 'openreview.net/Support'],
            signatures=['~Program_AAAIChair1'],
            writers=[]
        ))

        helpers.await_queue()

        assert len(openreview_client.get_group('AAAI.org/2025/Conference/Senior_Program_Committee').members) == 0
        assert len(openreview_client.get_group('AAAI.org/2025/Conference/Senior_Program_Committee/Invited').members) == 2

        messages = openreview_client.get_messages(subject = '[AAAI 2025] Invitation to serve as Senior Program Committee')
        assert len(messages) == 2

        for message in messages:
            text = message['content']['text']

            invitation_url = re.search('https://.*\n', text).group(0).replace('https://openreview.net', 'http://localhost:3030').replace('&amp;', '&')[:-1]
            helpers.respond_invitation(selenium, request_page, invitation_url, accept=True)

        helpers.await_queue_edit(openreview_client, invitation='AAAI.org/2025/Conference/Senior_Program_Committee/-/Recruitment', count=2)

        messages = client.get_messages(subject='[AAAI 2025] Senior Program Committee Invitation accepted')
        assert len(messages) == 2

        assert len(openreview_client.get_group('AAAI.org/2025/Conference/Senior_Program_Committee').members) == 2
        assert len(openreview_client.get_group('AAAI.org/2025/Conference/Senior_Program_Committee/Invited').members) == 2

    def test_reviewer_recruitment(self, client, openreview_client, helpers, request_page, selenium):

        pc_client=openreview.Client(username='pc@aaai.org', password=helpers.strong_password)
        request_form=pc_client.get_notes(invitation='openreview.net/Support/-/Request_Form')[0]

        reviewer_details = '''program_committee1@aaai.org, Program Committee AAAIOne
program_committee2@aaai.org, Program Committee AAAITwo
program_committee3@aaai.org, Program Committee AAAIThree
program_committee4@yahoo.com, Program Committee AAAIFour
'''
        pc_client.post_note(openreview.Note(
            content={
                'title': 'Recruitment',
                'invitee_role': 'Program_Committee',
                'invitee_details': reviewer_details,
                'invitee_reduced_load': ["1", "2", "3"],
                'invitation_email_subject': '[AAAI 2025] Invitation to serve as {{invitee_role}}',
                'invitation_email_content': 'Dear {{fullname}},\n\nYou have been nominated by the program chair committee of AAAI to serve as {{invitee_role}}.\n\n{{invitation_url}}\n\nCheers!\n\nProgram Chairs'
            },
            forum=request_form.forum,
            replyto=request_form.forum,
            invitation='openreview.net/Support/-/Request{}/Recruitment'.format(request_form.number),
            readers=['AAAI.org/2025/Conference/Program_Chairs', 'openreview.net/Support'],
            signatures=['~Program_AAAIChair1'],
            writers=[]
        ))

        helpers.await_queue()

        assert len(openreview_client.get_group('AAAI.org/2025/Conference/Program_Committee').members) == 0
        assert len(openreview_client.get_group('AAAI.org/2025/Conference/Program_Committee/Invited').members) == 4
        assert len(openreview_client.get_group('AAAI.org/2025/Conference/Program_Committee/Declined').members) == 0

        messages = openreview_client.get_messages(subject = '[AAAI 2025] Invitation to serve as Program Committee')
        assert len(messages) == 4

        for message in messages:
            text = message['content']['text']

            invitation_url = re.search('https://.*\n', text).group(0).replace('https://openreview.net', 'http://localhost:3030').replace('&amp;', '&')[:-1]
            helpers.respond_invitation(selenium, request_page, invitation_url, accept=True, quota=3)

        helpers.await_queue_edit(openreview_client, invitation='AAAI.org/2025/Conference/Program_Committee/-/Recruitment', count=8)

        messages = client.get_messages(subject='[AAAI 2025] Program Committee Invitation accepted with reduced load')
        assert len(messages) == 4

        assert len(openreview_client.get_group('AAAI.org/2025/Conference/Program_Committee').members) == 4
        assert len(openreview_client.get_group('AAAI.org/2025/Conference/Program_Committee/Invited').members) == 4
        assert len(openreview_client.get_group('AAAI.org/2025/Conference/Program_Committee/Declined').members) == 0

        messages = openreview_client.get_messages(to = 'program_committee4@yahoo.com', subject = '[AAAI 2025] Invitation to serve as Program Committee')
        invitation_url = re.search('https://.*\n', messages[0]['content']['text']).group(0).replace('https://openreview.net', 'http://localhost:3030').replace('&amp;', '&')[:-1]
        helpers.respond_invitation(selenium, request_page, invitation_url, accept=False)

        helpers.await_queue_edit(openreview_client, invitation='AAAI.org/2025/Conference/Program_Committee/-/Recruitment', count=9)

        assert len(openreview_client.get_group('AAAI.org/2025/Conference/Program_Committee').members) == 3
        assert len(openreview_client.get_group('AAAI.org/2025/Conference/Program_Committee/Invited').members) == 4
        assert len(openreview_client.get_group('AAAI.org/2025/Conference/Program_Committee/Declined').members) == 1

        reviewer_client = openreview.api.OpenReviewClient(username='program_committee1@aaai.org', password=helpers.strong_password)

        request_page(selenium, "http://localhost:3030/group?id=AAAI.org/2025/Conference/Program_Committee", reviewer_client.token, wait_for_element='header')
        header = selenium.find_element(By.ID, 'header')
        assert 'You have agreed to review up to 1 submission' in header.text