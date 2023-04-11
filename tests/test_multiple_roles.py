from __future__ import absolute_import, division, print_function, unicode_literals
import openreview
import pytest
import requests
import datetime
import time
import os
import re
import csv
import random
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import NoSuchElementException

class TestMultipleRoles():

    @pytest.fixture(scope="class")
    def conference(self, client):
        pc_client=openreview.Client(username='pc@lifelong-ml.cc', password='1234')
        request_form=client.get_notes(invitation='openreview.net/Support/-/Request_Form', sort='tmdate')[0]

        conference=openreview.helpers.get_conference(pc_client, request_form.id)
        return conference


    def test_create_conference(self, client, helpers):

        now = datetime.datetime.utcnow()
        due_date = now + datetime.timedelta(days=3)
        first_date = now + datetime.timedelta(days=1)

        # Post the request form note
        pc_client=helpers.create_user('pc@lifelong-ml.cc', 'Program', 'CoLLAsChair')

        helpers.create_user('reviewer1@lifelong-ml.cc', 'Reviewer', 'CoLLAsUMass', institution='umass.edu')
        helpers.create_user('reviewer2@lifelong-ml.cc', 'Reviewer', 'CoLLAsMIT', institution='mit.edu')
        helpers.create_user('reviewer3@lifelong-ml.cc', 'Reviewer', 'CoLLAsIBM', institution='ibm.com')
        helpers.create_user('reviewer4@lifelong-ml.cc', 'Reviewer', 'CoLLAsFacebook', institution='fb.com')

        request_form_note = pc_client.post_note(openreview.Note(
            invitation='openreview.net/Support/-/Request_Form',
            signatures=['~Program_CoLLAsChair1'],
            readers=[
                'openreview.net/Support',
                '~Program_CoLLAsChair1'
            ],
            writers=[],
            content={
                'title': 'First Conference on Lifelong Learning Agents',
                'Official Venue Name': 'First Conference on Lifelong Learning Agents',
                'Abbreviated Venue Name': 'CoLLAs 2022',
                'Official Website URL': 'https://lifelong-ml.cc/',
                'program_chair_emails': ['pc@lifelong-ml.cc'],
                'contact_email': 'pc@lifelong-ml.cc',
                'Area Chairs (Metareviewers)': 'Yes, our venue has Area Chairs',
                'senior_area_chairs': 'No, our venue does not have Senior Area Chairs',
                'Venue Start Date': '2021/12/01',
                'Submission Deadline': due_date.strftime('%Y/%m/%d'),
                'Location': 'Virtual',
                'submission_reviewer_assignment': 'Automatic',
                'Author and Reviewer Anonymity': 'Double-blind',
                'reviewer_identity': ['Program Chairs', 'Assigned Reviewers', 'Assigned Area Chair'],
                'Open Reviewing Policy': 'Submissions and reviews should both be private.',
                'submission_readers': 'All program committee (all reviewers, all area chairs, all senior area chairs if applicable)',
                'How did you hear about us?': 'ML conferences',
                'Expected Submissions': '100',
                'reviewer_roles': ['Program_Committee', 'Senior_Program_Committee'],
                'area_chair_roles': ['First_Group_AC', 'Second_Group_AC']
            }))

        helpers.await_queue()

        # Post a deploy note
        client.post_note(openreview.Note(
            content={'venue_id': 'lifelong-ml.cc/CoLLAs/2022/Conference'},
            forum=request_form_note.forum,
            invitation='openreview.net/Support/-/Request{}/Deploy'.format(request_form_note.number),
            readers=['openreview.net/Support'],
            referent=request_form_note.forum,
            replyto=request_form_note.forum,
            signatures=['openreview.net/Support'],
            writers=['openreview.net/Support']
        ))

        helpers.await_queue()

        assert client.get_group('lifelong-ml.cc/CoLLAs/2022/Conference')
        reviewers=client.get_group('lifelong-ml.cc/CoLLAs/2022/Conference/Reviewers')
        assert reviewers
        assert client.get_group('lifelong-ml.cc/CoLLAs/2022/Conference/Authors')


    def test_recruit_reviewers(self, client, selenium, request_page, helpers):

        pc_client=openreview.Client(username='pc@lifelong-ml.cc', password='1234')
        request_form=pc_client.get_notes(invitation='openreview.net/Support/-/Request_Form', sort='tmdate')[0]

        # Test Reviewer Recruitment
        request_page(selenium, 'http://localhost:3030/forum?id={}'.format(request_form.id), pc_client.token, by=By.CLASS_NAME, wait_for_element='reply_row')
        recruitment_div = selenium.find_element_by_id('note_{}'.format(request_form.id))
        assert recruitment_div
        reply_row = recruitment_div.find_element_by_class_name('reply_row')
        assert reply_row
        buttons = reply_row.find_elements_by_class_name('btn-xs')
        assert [btn for btn in buttons if btn.text == 'Recruitment']

        reviewer_details = '''reviewer1@lifelong-ml.cc, Reviewer UMass\nreviewer2@lifelong-ml.cc, reviewer3@lifelong-ml.cc, Reviewer UMass\nreviewer4@lifelong-ml.cc'''
        recruitment_note = pc_client.post_note(openreview.Note(
            content={
                'title': 'Recruitment',
                'invitee_role': 'Program_Committee',
                'invitee_reduced_load': ['2', '3', '4'],
                'invitee_details': reviewer_details,
                'invitation_email_subject': '[' + request_form.content['Abbreviated Venue Name'] + '] Invitation to serve as {{invitee_role}}',
                'invitation_email_content': 'Dear {{fullname}},\n\nYou have been nominated by the program chair committee of Theoretical Foundations of RL Workshop @ ICML 2020 to serve as {{invitee_role}}.\n\nACCEPT LINK:\n\n{{accept_url}}\n\nDECLINE LINK:\n\n{{decline_url}}\n\nIf you have any questions, please contact {{contact_info}}.\n\nCheers!\n\nProgram Chairs'
            },
            forum=request_form.forum,
            replyto=request_form.forum,
            invitation='openreview.net/Support/-/Request{}/Recruitment'.format(request_form.number),
            readers=['lifelong-ml.cc/CoLLAs/2022/Conference/Program_Chairs', 'openreview.net/Support'],
            signatures=['~Program_CoLLAsChair1'],
            writers=[]
        ))
        assert recruitment_note

        reviewer_details = '''reviewer1@lifelong-ml.cc, Reviewer UMass\nreviewer2@lifelong-ml.cc, reviewer3@lifelong-ml.cc, Reviewer UMass\nreviewer4@lifelong-ml.cc'''
        recruitment_note = pc_client.post_note(openreview.Note(
            content={
                'title': 'Recruitment',
                'invitee_role': 'Senior_Program_Committee',
                'invitee_reduced_load': ['2', '3', '4'],
                'invitee_details': reviewer_details,
                'invitation_email_subject': '[' + request_form.content['Abbreviated Venue Name'] + '] Invitation to serve as {{invitee_role}}',
                'invitation_email_content': 'Dear {{fullname}},\n\nYou have been nominated by the program chair committee of Theoretical Foundations of RL Workshop @ ICML 2020 to serve as {{invitee_role}}.\n\nACCEPT LINK:\n\n{{accept_url}}\n\nDECLINE LINK:\n\n{{decline_url}}\n\nIf you have any questions, please contact {{contact_info}}.\n\nCheers!\n\nProgram Chairs'
            },
            forum=request_form.forum,
            replyto=request_form.forum,
            invitation='openreview.net/Support/-/Request{}/Recruitment'.format(request_form.number),
            readers=['lifelong-ml.cc/CoLLAs/2022/Conference/Program_Chairs', 'openreview.net/Support'],
            signatures=['~Program_CoLLAsChair1'],
            writers=[]
        ))
        assert recruitment_note

        helpers.await_queue()
        client.add_members_to_group('lifelong-ml.cc/CoLLAs/2022/Conference/Program_Committee', ['reviewer1@lifelong-ml.cc', 'reviewer2@lifelong-ml.cc'])
        client.add_members_to_group('lifelong-ml.cc/CoLLAs/2022/Conference/Senior_Program_Committee', ['reviewer3@lifelong-ml.cc', 'reviewer4@lifelong-ml.cc'])

    def test_submit_papers(self, test_client, client, helpers):

        ## Need super user permission to add the venue to the active_venues group
        pc_client=openreview.Client(username='pc@lifelong-ml.cc', password='1234')
        request_form=client.get_notes(invitation='openreview.net/Support/-/Request_Form', sort='tmdate')[0]
        conference=openreview.helpers.get_conference(client, request_form.id)

        domains = ['umass.edu', 'amazon.com', 'fb.com', 'cs.umass.edu', 'google.com', 'mit.edu']
        for i in range(1,6):
            note = openreview.Note(invitation = 'lifelong-ml.cc/CoLLAs/2022/Conference/-/Submission',
                readers = ['lifelong-ml.cc/CoLLAs/2022/Conference', 'test@mail.com', 'peter@mail.com', 'andrew@' + domains[i], '~SomeFirstName_User1'],
                writers = [conference.id, '~SomeFirstName_User1', 'peter@mail.com', 'andrew@' + domains[i]],
                signatures = ['~SomeFirstName_User1'],
                content = {
                    'title': 'Paper title ' + str(i) ,
                    'abstract': 'This is an abstract ' + str(i),
                    'authorids': ['test@mail.com', 'peter@mail.com', 'andrew@' + domains[i]],
                    'authors': ['SomeFirstName User', 'Peter SomeLastName', 'Andrew Mc'],
                    'keywords': ['machine learning', 'nlp'],
                    'pdf': '/pdf/22234qweoiuweroi22234qweoiuweroi12345678.pdf'
                }
            )
            note = test_client.post_note(note)

        post_submission_note=pc_client.post_note(openreview.Note(
            content= {
                'force': 'Yes',
                'hide_fields': ['keywords'],
                'submission_readers': 'All program committee (all reviewers, all area chairs, all senior area chairs if applicable)'
            },
            forum= request_form.id,
            invitation= f'openreview.net/Support/-/Request{request_form.number}/Post_Submission',
            readers= ['lifelong-ml.cc/CoLLAs/2022/Conference/Program_Chairs', 'openreview.net/Support'],
            referent= request_form.id,
            replyto= request_form.id,
            signatures= ['~Program_CoLLAsChair1'],
            writers= [],
        ))

        helpers.await_queue()

        blinded_notes = test_client.get_notes(invitation='lifelong-ml.cc/CoLLAs/2022/Conference/-/Blind_Submission')
        assert len(blinded_notes) == 5

    def test_ac_assignment_invitation(self, test_client, client, helpers):
        pc_client=openreview.Client(username='pc@lifelong-ml.cc', password='1234')
        request_form=pc_client.get_notes(invitation='openreview.net/Support/-/Request_Form', sort='tmdate')[0]
        ac_details = '''ac1@lifelong-ml.cc, AreaChair UMass\nac2@lifelong-ml.cc, ac3@lifelong-ml.cc, AreaChair UMass\nac4@lifelong-ml.cc'''
        recruitment_note = client.post_note(openreview.Note(
            content={
                'title': 'Recruitment',
                'invitee_role': 'First_Group_AC',
                'invitee_reduced_load': ['2', '3', '4'],
                'invitee_details': ac_details,
                'invitation_email_subject': '[' + request_form.content['Abbreviated Venue Name'] + '] Invitation to serve as {{invitee_role}}',
                'invitation_email_content': 'Dear {{fullname}},\n\nYou have been nominated by the program chair committee of Theoretical Foundations of RL Workshop @ ICML 2020 to serve as {{invitee_role}}.\n\nACCEPT LINK:\n\n{{accept_url}}\n\nDECLINE LINK:\n\n{{decline_url}}\n\nIf you have any questions, please contact {{contact_info}}.\n\nCheers!\n\nProgram Chairs'
            },
            forum=request_form.forum,
            replyto=request_form.forum,
            invitation='openreview.net/Support/-/Request{}/Recruitment'.format(request_form.number),
            readers=['lifelong-ml.cc/CoLLAs/2022/Conference/Program_Chairs', 'openreview.net/Support'],
            signatures=['~Program_CoLLAsChair1'],
            writers=[]
        ))
        assert recruitment_note

        helpers.await_queue()

        client.add_members_to_group('lifelong-ml.cc/CoLLAs/2022/Conference/First_Group_AC', ['ac1@lifelong-ml.cc', 'ac2@lifelong-ml.cc', 'ac3@lifelong-ml.cc', 'ac4@lifelong-ml.cc'])

        ## Setup Matching for Program Committee
        matching_setup_note = client.post_note(openreview.Note(
            content={
                'title': 'Paper Matching Setup',
                'matching_group': 'lifelong-ml.cc/CoLLAs/2022/Conference/First_Group_AC',
                'compute_conflicts': 'Yes',
                'compute_affinity_scores': 'No'
            },
            forum=request_form.id,
            replyto=request_form.id,
            invitation=f'openreview.net/Support/-/Request{request_form.number}/Paper_Matching_Setup',
            readers=['lifelong-ml.cc/CoLLAs/2022/Conference/Program_Chairs', 'openreview.net/Support'],
            signatures=['~Program_CoLLAsChair1'],
            writers=[]
        ))
        assert matching_setup_note
        helpers.await_queue()

        invitation = client.get_invitation("lifelong-ml.cc/CoLLAs/2022/Conference/First_Group_AC/-/Assignment")
        assert invitation
        assert "PAPER_GROUP_ID = 'lifelong-ml.cc/CoLLAs/2022/Conference/Paper{number}/Area_Chairs'" in invitation.process

    def test_setup_matching(self, conference, client, helpers):

        pc_client=openreview.Client(username='pc@lifelong-ml.cc', password='1234')
        request_form=client.get_notes(invitation='openreview.net/Support/-/Request_Form', sort='tmdate')[0]

        ## Setup Matching for Program Committee
        matching_setup_note = client.post_note(openreview.Note(
            content={
                'title': 'Paper Matching Setup',
                'matching_group': 'lifelong-ml.cc/CoLLAs/2022/Conference/Program_Committee',
                'compute_conflicts': 'Yes',
                'compute_affinity_scores': 'No'
            },
            forum=request_form.id,
            replyto=request_form.id,
            invitation=f'openreview.net/Support/-/Request{request_form.number}/Paper_Matching_Setup',
            readers=['lifelong-ml.cc/CoLLAs/2022/Conference/Program_Chairs', 'openreview.net/Support'],
            signatures=['~Program_CoLLAsChair1'],
            writers=[]
        ))
        assert matching_setup_note
        helpers.await_queue()

        ## Setup Matching for Senior Program Committee
        matching_setup_note = client.post_note(openreview.Note(
            content={
                'title': 'Paper Matching Setup',
                'matching_group': 'lifelong-ml.cc/CoLLAs/2022/Conference/Senior_Program_Committee',
                'compute_conflicts': 'Yes',
                'compute_affinity_scores': 'No'
            },
            forum=request_form.id,
            replyto=request_form.id,
            invitation=f'openreview.net/Support/-/Request{request_form.number}/Paper_Matching_Setup',
            readers=['lifelong-ml.cc/CoLLAs/2022/Conference/Program_Chairs', 'openreview.net/Support'],
            signatures=['~Program_CoLLAsChair1'],
            writers=[]
        ))
        assert matching_setup_note
        helpers.await_queue()

        submissions=conference.get_submissions(sort='tmdate')

        ## Program Committee
        client.post_edge(openreview.Edge(
            invitation='lifelong-ml.cc/CoLLAs/2022/Conference/Program_Committee/-/Proposed_Assignment',
            readers = [conference.id, '~Reviewer_CoLLAsUMass1'],
            writers = [conference.id],
            nonreaders = [f'lifelong-ml.cc/CoLLAs/2022/Conference/Paper{submissions[0].number}/Authors'],
            signatures = [conference.id],
            head = submissions[0].id,
            tail = '~Reviewer_CoLLAsUMass1',
            label = 'program-committee-matching',
            weight = 0.94
        ))

        client.post_edge(openreview.Edge(
            invitation='lifelong-ml.cc/CoLLAs/2022/Conference/Program_Committee/-/Proposed_Assignment',
            readers = [conference.id, '~Reviewer_CoLLAsUMass1'],
            writers = [conference.id],
            nonreaders = [f'lifelong-ml.cc/CoLLAs/2022/Conference/Paper{submissions[1].number}/Authors'],
            signatures = [conference.id],
            head = submissions[1].id,
            tail = '~Reviewer_CoLLAsUMass1',
            label = 'program-committee-matching',
            weight = 0.94
        ))

        client.post_edge(openreview.Edge(
            invitation='lifelong-ml.cc/CoLLAs/2022/Conference/Program_Committee/-/Proposed_Assignment',
            readers = [conference.id, '~Reviewer_CoLLAsUMass1'],
            writers = [conference.id],
            nonreaders = [f'lifelong-ml.cc/CoLLAs/2022/Conference/Paper{submissions[2].number}/Authors'],
            signatures = [conference.id],
            head = submissions[2].id,
            tail = '~Reviewer_CoLLAsUMass1',
            label = 'program-committee-matching',
            weight = 0.94
        ))

        client.post_edge(openreview.Edge(
            invitation='lifelong-ml.cc/CoLLAs/2022/Conference/Program_Committee/-/Proposed_Assignment',
            readers = [conference.id, '~Reviewer_CoLLAsMIT1'],
            writers = [conference.id],
            nonreaders = [f'lifelong-ml.cc/CoLLAs/2022/Conference/Paper{submissions[3].number}/Authors'],
            signatures = [conference.id],
            head = submissions[3].id,
            tail = '~Reviewer_CoLLAsMIT1',
            label = 'program-committee-matching',
            weight = 0.94
        ))


        client.post_edge(openreview.Edge(
            invitation='lifelong-ml.cc/CoLLAs/2022/Conference/Program_Committee/-/Proposed_Assignment',
            readers = [conference.id, '~Reviewer_CoLLAsMIT1'],
            writers = [conference.id],
            nonreaders = [f'lifelong-ml.cc/CoLLAs/2022/Conference/Paper{submissions[4].number}/Authors'],
            signatures = [conference.id],
            head = submissions[4].id,
            tail = '~Reviewer_CoLLAsMIT1',
            label = 'program-committee-matching',
            weight = 0.94
        ))

        ## Senior Program Committee
        client.post_edge(openreview.Edge(
            invitation='lifelong-ml.cc/CoLLAs/2022/Conference/Senior_Program_Committee/-/Proposed_Assignment',
            readers = [conference.id, '~Reviewer_CoLLAsIBM1'],
            writers = [conference.id],
            nonreaders = [f'lifelong-ml.cc/CoLLAs/2022/Conference/Paper{submissions[0].number}/Authors'],
            signatures = [conference.id],
            head = submissions[0].id,
            tail = '~Reviewer_CoLLAsIBM1',
            label = 'senior-program-committee-matching',
            weight = 0.94
        ))

        client.post_edge(openreview.Edge(
            invitation='lifelong-ml.cc/CoLLAs/2022/Conference/Senior_Program_Committee/-/Proposed_Assignment',
            readers = [conference.id, '~Reviewer_CoLLAsIBM1'],
            writers = [conference.id],
            nonreaders = [f'lifelong-ml.cc/CoLLAs/2022/Conference/Paper{submissions[1].number}/Authors'],
            signatures = [conference.id],
            head = submissions[1].id,
            tail = '~Reviewer_CoLLAsIBM1',
            label = 'senior-program-committee-matching',
            weight = 0.94
        ))

        client.post_edge(openreview.Edge(
            invitation='lifelong-ml.cc/CoLLAs/2022/Conference/Senior_Program_Committee/-/Proposed_Assignment',
            readers = [conference.id, '~Reviewer_CoLLAsFacebook1'],
            writers = [conference.id],
            nonreaders = [f'lifelong-ml.cc/CoLLAs/2022/Conference/Paper{submissions[2].number}/Authors'],
            signatures = [conference.id],
            head = submissions[2].id,
            tail = '~Reviewer_CoLLAsFacebook1',
            label = 'senior-program-committee-matching',
            weight = 0.94
        ))

        client.post_edge(openreview.Edge(
            invitation='lifelong-ml.cc/CoLLAs/2022/Conference/Senior_Program_Committee/-/Proposed_Assignment',
            readers = [conference.id, '~Reviewer_CoLLAsFacebook1'],
            writers = [conference.id],
            nonreaders = [f'lifelong-ml.cc/CoLLAs/2022/Conference/Paper{submissions[3].number}/Authors'],
            signatures = [conference.id],
            head = submissions[3].id,
            tail = '~Reviewer_CoLLAsFacebook1',
            label = 'senior-program-committee-matching',
            weight = 0.94
        ))

        client.post_edge(openreview.Edge(
            invitation='lifelong-ml.cc/CoLLAs/2022/Conference/Senior_Program_Committee/-/Proposed_Assignment',
            readers = [conference.id, '~Reviewer_CoLLAsFacebook1'],
            writers = [conference.id],
            nonreaders = [f'lifelong-ml.cc/CoLLAs/2022/Conference/Paper{submissions[4].number}/Authors'],
            signatures = [conference.id],
            head = submissions[4].id,
            tail = '~Reviewer_CoLLAsFacebook1',
            label = 'senior-program-committee-matching',
            weight = 0.94
        ))

        conference.set_assignments('program-committee-matching', 'lifelong-ml.cc/CoLLAs/2022/Conference/Program_Committee', enable_reviewer_reassignment=True, overwrite=True)
        conference.set_assignments('senior-program-committee-matching', 'lifelong-ml.cc/CoLLAs/2022/Conference/Senior_Program_Committee', enable_reviewer_reassignment=True, overwrite=True)

        reviewers = client.get_group('lifelong-ml.cc/CoLLAs/2022/Conference/Paper1/Reviewers')
        assert '~Reviewer_CoLLAsMIT1' in reviewers.members
        assert '~Reviewer_CoLLAsFacebook1' in reviewers.members

