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

class TestNeurIPSConference():

    def test_create_conference(self, client, openreview_client, helpers):

        now = datetime.datetime.utcnow()
        due_date = now + datetime.timedelta(days=3)
        first_date = now + datetime.timedelta(days=1)

        # Post the request form note
        pc_client=helpers.create_user('pc@neurips.cc', 'Program', 'NeurIPSChair')

        helpers.create_user('another_andrew@mit.edu', 'Another', 'Andrew')
        helpers.create_user('sac1@google.com', 'SeniorArea', 'GoogleChair', institution='google.com')
        helpers.create_user('sac2@gmail.com', 'SeniorArea', 'NeurIPSChair', institution='fb.com')
        helpers.create_user('ac1@mit.edu', 'Area', 'IBMChair', institution='ibm.com')
        helpers.create_user('ac2@gmail.com', 'Area', 'GoogleChair', institution='google.com')
        helpers.create_user('ac3@umass.edu', 'Area', 'UMassChair', institution='umass.edu')
        helpers.create_user('reviewer1@umass.edu', 'Reviewer', 'UMass', institution='umass.edu')
        helpers.create_user('reviewer2@mit.edu', 'Reviewer', 'MIT', institution='mit.edu')
        helpers.create_user('reviewer3@ibm.com', 'Reviewer', 'IBM', institution='ibm.com')
        helpers.create_user('reviewer4@fb.com', 'Reviewer', 'Facebook', institution='fb.com')
        helpers.create_user('reviewer5@google.com', 'Reviewer', 'Google', institution='google.com')
        helpers.create_user('reviewer6@amazon.com', 'Reviewer', 'Amazon', institution='amazon.com')
        helpers.create_user('external_reviewer1@amazon.com', 'External Reviewer', 'Amazon', institution='amazon.com')
        helpers.create_user('external_reviewer2@mit.edu', 'External Reviewer', 'MIT', institution='mit.edu')
        helpers.create_user('external_reviewer3@adobe.com', 'External Reviewer', 'Adobe', institution='adobe.com')

        request_form_note = pc_client.post_note(openreview.Note(
            invitation='openreview.net/Support/-/Request_Form',
            signatures=['~Program_NeurIPSChair1'],
            readers=[
                'openreview.net/Support',
                '~Program_NeurIPSChair1'
            ],
            writers=[],
            content={
                'title': 'Conference on Neural Information Processing Systems',
                'Official Venue Name': 'Conference on Neural Information Processing Systems',
                'Abbreviated Venue Name': 'NeurIPS 2023',
                'Official Website URL': 'https://neurips.cc',
                'program_chair_emails': ['pc@neurips.cc'],
                'contact_email': 'pc@neurips.cc',
                'Area Chairs (Metareviewers)': 'Yes, our venue has Area Chairs',
                'senior_area_chairs': 'Yes, our venue has Senior Area Chairs',
                'Venue Start Date': '2023/12/01',
                'Submission Deadline': due_date.strftime('%Y/%m/%d'),
                'abstract_registration_deadline': first_date.strftime('%Y/%m/%d'),
                'Location': 'Virtual',
                'submission_reviewer_assignment': 'Automatic',
                'Author and Reviewer Anonymity': 'Double-blind',
                'reviewer_identity': ['Program Chairs', 'Assigned Senior Area Chair', 'Assigned Area Chair', 'Assigned Reviewers'],
                'area_chair_identity': ['Program Chairs', 'Assigned Senior Area Chair', 'Assigned Area Chair', 'Assigned Reviewers'],
                'senior_area_chair_identity': ['Program Chairs', 'Assigned Senior Area Chair', 'Assigned Area Chair', 'Assigned Reviewers'],
                'Open Reviewing Policy': 'Submissions and reviews should both be private.',
                'submission_readers': 'Program chairs and paper authors only',
                'hide_fields': ['keywords'],
                'How did you hear about us?': 'ML conferences',
                'Expected Submissions': '100',
                'api_version': '2'
            }))

        helpers.await_queue()

        # Post a deploy note
        client.post_note(openreview.Note(
            content={'venue_id': 'NeurIPS.cc/2023/Conference'},
            forum=request_form_note.forum,
            invitation='openreview.net/Support/-/Request{}/Deploy'.format(request_form_note.number),
            readers=['openreview.net/Support'],
            referent=request_form_note.forum,
            replyto=request_form_note.forum,
            signatures=['openreview.net/Support'],
            writers=['openreview.net/Support']
        ))

        helpers.await_queue()

        assert openreview_client.get_group('NeurIPS.cc/2023/Conference')
        assert openreview_client.get_group('NeurIPS.cc/2023/Conference/Senior_Area_Chairs')
        acs=openreview_client.get_group('NeurIPS.cc/2023/Conference/Area_Chairs')
        assert acs
        assert 'NeurIPS.cc/2023/Conference/Senior_Area_Chairs' in acs.readers
        reviewers=openreview_client.get_group('NeurIPS.cc/2023/Conference/Reviewers')
        assert reviewers
        assert 'NeurIPS.cc/2023/Conference/Senior_Area_Chairs' in reviewers.readers
        assert 'NeurIPS.cc/2023/Conference/Area_Chairs' in reviewers.readers

        assert openreview_client.get_group('NeurIPS.cc/2023/Conference/Authors')

        post_submission =  openreview_client.get_invitation('NeurIPS.cc/2023/Conference/-/Post_Submission')
        assert 'authors' in post_submission.edit['note']['content']
        assert 'authorids' in post_submission.edit['note']['content']
        assert 'keywords' in post_submission.edit['note']['content']

    def test_recruit_senior_area_chairs(self, client, openreview_client, selenium, request_page, helpers):

        pc_client=openreview.Client(username='pc@neurips.cc', password=helpers.strong_password)
        request_form=pc_client.get_notes(invitation='openreview.net/Support/-/Request_Form')[0]

        # Test Reviewer Recruitment
        request_page(selenium, 'http://localhost:3030/forum?id={}'.format(request_form.id), pc_client.token, by=By.CLASS_NAME, wait_for_element='reply_row')
        recruitment_div = selenium.find_element_by_id('note_{}'.format(request_form.id))
        assert recruitment_div
        reply_row = recruitment_div.find_element_by_class_name('reply_row')
        assert reply_row
        buttons = reply_row.find_elements_by_class_name('btn-xs')
        assert [btn for btn in buttons if btn.text == 'Recruitment']

        reviewer_details = '''sac1@google.com, SAC One\nsac2@gmail.com, SAC Two'''
        recruitment_note = pc_client.post_note(openreview.Note(
            content={
                'title': 'Recruitment',
                'invitee_role': 'Senior_Area_Chairs',
                'invitee_details': reviewer_details,
                'invitation_email_subject': '[' + request_form.content['Abbreviated Venue Name'] + '] Invitation to serve as {{invitee_role}}',
                'invitation_email_content': 'Dear {{fullname}},\n\nYou have been nominated by the program chair committee of NeurIPS 2023 to serve as {{invitee_role}}.\n\n{{invitation_url}}\n\nCheers!\n\nProgram Chairs'
            },
            forum=request_form.forum,
            replyto=request_form.forum,
            invitation='openreview.net/Support/-/Request{}/Recruitment'.format(request_form.number),
            readers=['NeurIPS.cc/2023/Conference/Program_Chairs', 'openreview.net/Support'],
            signatures=['~Program_NeurIPSChair1'],
            writers=[]
        ))
        assert recruitment_note

        helpers.await_queue()
        process_logs = client.get_process_logs(id=recruitment_note.id)
        assert len(process_logs) == 1
        assert process_logs[0]['status'] == 'ok'
        assert process_logs[0]['invitation'] == 'openreview.net/Support/-/Request{}/Recruitment'.format(request_form.number)

        messages = client.get_messages(to='sac1@google.com', subject='[NeurIPS 2023] Invitation to serve as Senior Area Chair')
        assert messages and len(messages) == 1
        assert messages[0]['content']['subject'] == '[NeurIPS 2023] Invitation to serve as Senior Area Chair'
        assert messages[0]['content']['text'].startswith('Dear SAC One,\n\nYou have been nominated by the program chair committee of NeurIPS 2023 to serve as Senior Area Chair.')
        invitation_url = re.search('https://.*\n', messages[0]['content']['text']).group(0).replace('https://openreview.net', 'http://localhost:3030').replace('&amp;', '&')[:-1]
        print('invitation_url', invitation_url)
        helpers.respond_invitation(selenium, request_page, invitation_url, accept=True)

        helpers.await_queue_edit(openreview_client, invitation='NeurIPS.cc/2023/Conference/Senior_Area_Chairs/-/Recruitment', count=1)

        messages = client.get_messages(to='sac1@google.com', subject='[NeurIPS 2023] Senior Area Chair Invitation accepted')
        assert messages and len(messages) == 1
        assert messages[0]['content']['text'] == '''Thank you for accepting the invitation to be a Senior Area Chair for NeurIPS 2023.

The NeurIPS 2023 program chairs will be contacting you with more information regarding next steps soon. In the meantime, please add noreply@openreview.net to your email contacts to ensure that you receive all communications.

If you would like to change your decision, please follow the link in the previous invitation email and click on the "Decline" button.'''
        
        messages = client.get_messages(to='sac2@gmail.com', subject='[NeurIPS 2023] Invitation to serve as Senior Area Chair')
        assert messages and len(messages) == 1
        assert messages[0]['content']['subject'] == '[NeurIPS 2023] Invitation to serve as Senior Area Chair'
        assert messages[0]['content']['text'].startswith('Dear SAC Two,\n\nYou have been nominated by the program chair committee of NeurIPS 2023 to serve as Senior Area Chair.')
        invitation_url = re.search('https://.*\n', messages[0]['content']['text']).group(0).replace('https://openreview.net', 'http://localhost:3030').replace('&amp;', '&')[:-1]
        helpers.respond_invitation(selenium, request_page, invitation_url, accept=True)

        helpers.await_queue_edit(openreview_client, invitation='NeurIPS.cc/2023/Conference/Senior_Area_Chairs/-/Recruitment', count=2)

        sac_group = client.get_group('NeurIPS.cc/2023/Conference/Senior_Area_Chairs')
        assert len(sac_group.members) == 2
        assert 'sac1@google.com' in sac_group.members
        assert 'sac2@gmail.com' in sac_group.members

        sac_client = openreview.api.OpenReviewClient(username='sac1@google.com', password=helpers.strong_password)
        request_page(selenium, "http://localhost:3030/group?id=NeurIPS.cc/2023/Conference", sac_client.token, wait_for_element='notes')
        notes_panel = selenium.find_element_by_id('notes')
        assert notes_panel
        tabs = notes_panel.find_element_by_class_name('tabs-container')
        assert tabs.find_element(By.LINK_TEXT, "Senior Area Chair Console")

    def test_recruit_area_chairs(self, client, openreview_client, selenium, request_page, helpers):

        pc_client=openreview.Client(username='pc@neurips.cc', password=helpers.strong_password)
        request_form=pc_client.get_notes(invitation='openreview.net/Support/-/Request_Form')[0]

        reviewer_details = '''ac1@mit.edu\n'''
        recruitment_note = pc_client.post_note(openreview.Note(
            content={
                'title': 'Recruitment',
                'invitee_role': 'Area_Chairs',
                'invitee_details': reviewer_details,
                'invitee_reduced_load': ["2", "3", "4"],
                'invitation_email_subject': '[' + request_form.content['Abbreviated Venue Name'] + '] Invitation to serve as {{invitee_role}}',
                'invitation_email_content': 'Dear {{fullname}},\n\nYou have been nominated by the program chair committee of NeurIPS 2023 to serve as {{invitee_role}}.\n\n{{invitation_url}}\n\nCheers!\n\nProgram Chairs'
            },
            forum=request_form.forum,
            replyto=request_form.forum,
            invitation='openreview.net/Support/-/Request{}/Recruitment'.format(request_form.number),
            readers=['NeurIPS.cc/2023/Conference/Program_Chairs', 'openreview.net/Support'],
            signatures=['~Program_NeurIPSChair1'],
            writers=[]
        ))
        assert recruitment_note

        helpers.await_queue()

        messages = client.get_messages(to = 'ac1@mit.edu', subject = '[NeurIPS 2023] Invitation to serve as Area Chair')
        assert len(messages) == 1   
        text = messages[0]['content']['text']
        assert 'Dear invitee,' in text
        assert 'You have been nominated by the program chair committee of NeurIPS 2023 to serve as Area Chair' in text

        invitation_url = re.search('https://.*\n', messages[0]['content']['text']).group(0).replace('https://openreview.net', 'http://localhost:3030').replace('&amp;', '&')[:-1]
        helpers.respond_invitation(selenium, request_page, invitation_url, accept=True, quota=2)

        accepted_group = client.get_group(id='NeurIPS.cc/2023/Conference/Area_Chairs')
        assert len(accepted_group.members) == 1
        assert 'ac1@mit.edu' in accepted_group.members

        rejected_group = client.get_group(id='NeurIPS.cc/2023/Conference/Area_Chairs/Declined')
        assert len(rejected_group.members) == 0

        notes = openreview_client.get_notes(invitation='NeurIPS.cc/2023/Conference/Area_Chairs/-/Recruitment', sort='tcdate:desc')
        assert notes
        assert len(notes) == 2
        assert notes[0].content['reduced_load']['value'] == '2'

        messages = client.get_messages(to = 'ac1@mit.edu', subject = '[NeurIPS 2023] Area Chair Invitation accepted with reduced load')
        assert len(messages) == 1
        assert messages[0]['content']['text'] == '''Thank you for accepting the invitation to be a Area Chair for NeurIPS 2023.
You have selected a reduced load of 2 submissions to review.

The NeurIPS 2023 program chairs will be contacting you with more information regarding next steps soon. In the meantime, please add noreply@openreview.net to your email contacts to ensure that you receive all communications.

If you would like to change your decision, please follow the link in the previous invitation email and click on the "Decline" button.'''

    def test_ac_registration(self, client, openreview_client, helpers):

        pc_client=openreview.Client(username='pc@neurips.cc', password=helpers.strong_password)
        request_form=pc_client.get_notes(invitation='openreview.net/Support/-/Request_Form')[0]

        now = datetime.datetime.utcnow()
        due_date  = now.replace(hour=0, minute=0, second=0, microsecond=0) + datetime.timedelta(days=2)
        expdate = now.replace(hour=0, minute=0, second=0, microsecond=0) + datetime.timedelta(days=5)

        registration_stage_note = pc_client.post_note(openreview.Note(
            content={
                'AC_registration_deadline': due_date.strftime('%Y/%m/%d'),
                'AC_registration_expiration_date': expdate.strftime('%Y/%m/%d'),
                'AC_registration_name': 'Registration',
                'AC_form_title': 'NeurIPS 2023 - Area Chair Registration',
                'AC_form_instructions': "NeurIPS 2023 employs [OpenReview](https://openreview.net/) as our paper submission and peer review system. To match papers to reviewers (including conflict handling and computation of affinity scores), OpenReview requires carefully populated and up-to-date OpenReview profiles. To this end, we require every reviewer to **create (if nonexistent) and update their OpenReview profile** (Section A) and to complete the **Expertise Selection** (Section B) and **Reviewer Registration** (Section C) tasks."
            },
            forum=request_form.forum,
            replyto=request_form.forum,
            referent=request_form.forum,
            invitation='openreview.net/Support/-/Request{}/Area_Chair_Registration'.format(request_form.number),
            readers=['NeurIPS.cc/2023/Conference/Program_Chairs', 'openreview.net/Support'],
            signatures=['~Program_NeurIPSChair1'],
            writers=[]
        ))
        assert registration_stage_note
        helpers.await_queue()
        process_logs = client.get_process_logs(id=registration_stage_note.id)
        assert len(process_logs) == 1
        assert process_logs[0]['status'] == 'ok'
        assert process_logs[0]['invitation'] == 'openreview.net/Support/-/Request{}/Area_Chair_Registration'.format(request_form.number)

        registration_notes = openreview_client.get_notes(invitation='NeurIPS.cc/2023/Conference/Area_Chairs/-/Registration_Form')
        assert registration_notes and len(registration_notes) == 1
        assert registration_notes[0].content['title']['value'] == 'NeurIPS 2023 - Area Chair Registration'
        invitation = openreview_client.get_invitation('NeurIPS.cc/2023/Conference/Area_Chairs/-/Registration')
        assert invitation
        assert 'profile_confirmed' in invitation.edit['note']['content']
        assert 'expertise_confirmed' in invitation.edit['note']['content']
        assert 'NeurIPS.cc/2023/Conference/Area_Chairs' in invitation.invitees
        assert invitation.duedate == openreview.tools.datetime_millis(due_date)
        assert invitation.expdate == openreview.tools.datetime_millis(due_date + datetime.timedelta(days = 3))

    def test_sac_matching(self, client, openreview_client, helpers, request_page, selenium):

        #remove SACs from group
        openreview_client.remove_members_from_group('NeurIPS.cc/2023/Conference/Senior_Area_Chairs', ['sac1@google.com','sac2@gmail.com'])

        #remove AC from AC group
        openreview_client.remove_members_from_group('NeurIPS.cc/2023/Conference/Area_Chairs', 'ac1@mit.edu')

        pc_client=openreview.Client(username='pc@neurips.cc', password=helpers.strong_password)
        request_form=pc_client.get_notes(invitation='openreview.net/Support/-/Request_Form')[0]

        venue = openreview.get_conference(client, request_form.id, support_user='openreview.net/Support')

        #setup matching for SACs with empty SAC group
        with pytest.raises(openreview.OpenReviewException, match=r'The match group is empty'):
            venue.setup_committee_matching(committee_id=venue.get_senior_area_chairs_id(), compute_conflicts=True)

        openreview_client.add_members_to_group('NeurIPS.cc/2023/Conference/Senior_Area_Chairs', ['sac1@google.com','sac2@gmail.com'])

        #setup matching for SACs with empty AC group
        with pytest.raises(openreview.OpenReviewException, match=r'The alternate match group is empty'):
            venue.setup_committee_matching(committee_id=venue.get_senior_area_chairs_id(), compute_conflicts=True)

        openreview_client.add_members_to_group('NeurIPS.cc/2023/Conference/Area_Chairs', ['~Area_IBMChair1', '~Area_GoogleChair1', '~Area_UMassChair1', 'ac1@mit.edu'])

    def test_sac_bidding(self, client, openreview_client, helpers, request_page, selenium):

        pc_client=openreview.Client(username='pc@neurips.cc', password=helpers.strong_password)
        request_form=pc_client.get_notes(invitation='openreview.net/Support/-/Request_Form')[0]

        venue = openreview.get_conference(client, request_form.id, support_user='openreview.net/Support')

        venue.setup_committee_matching(committee_id='NeurIPS.cc/2023/Conference/Senior_Area_Chairs', compute_conflicts=False, compute_affinity_scores=os.path.join(os.path.dirname(__file__), 'data/sac_affinity_scores.csv'))
        now = datetime.datetime.utcnow()
        venue.bid_stages = [openreview.stages.BidStage(due_date=now + datetime.timedelta(days=3), committee_id='NeurIPS.cc/2023/Conference/Senior_Area_Chairs', score_ids=['NeurIPS.cc/2023/Conference/Senior_Area_Chairs/-/Affinity_Score'])]
        venue.create_bid_stages()

        edges=pc_client.get_edges_count(invitation='NeurIPS.cc/2023/Conference/Senior_Area_Chairs/-/Affinity_Score')
        assert edges == 6

        pc_client=openreview.api.OpenReviewClient(username='pc@neurips.cc', password=helpers.strong_password)
        invitation=pc_client.get_invitation('NeurIPS.cc/2023/Conference/Senior_Area_Chairs/-/Assignment_Configuration')
        assert invitation
        assert invitation.edit['note']['content']['paper_invitation']['value']['param']['regex'] == 'NeurIPS.cc/2023/Conference/Area_Chairs'
        assert invitation.edit['note']['content']['paper_invitation']['value']['param']['default'] == 'NeurIPS.cc/2023/Conference/Area_Chairs'

        sac_client=openreview.api.OpenReviewClient(username='sac1@google.com', password=helpers.strong_password)
        assert sac_client.get_group(id='NeurIPS.cc/2023/Conference/Area_Chairs')

        edges=sac_client.get_edges_count(invitation='NeurIPS.cc/2023/Conference/Senior_Area_Chairs/-/Affinity_Score', tail='~SeniorArea_GoogleChair1')
        assert edges == 3

        tasks_url = 'http://localhost:3030/group?id=NeurIPS.cc/2023/Conference/Senior_Area_Chairs#senior-areachair-tasks'
        request_page(selenium, tasks_url, sac_client.token, by=By.LINK_TEXT, wait_for_element='Senior Area Chair Bid')

        task_panel = selenium.find_element(By.LINK_TEXT, "Senior Area Chair Tasks")
        task_panel.click()

        assert selenium.find_element(By.LINK_TEXT, "Senior Area Chair Bid")

        bid_url = 'http://localhost:3030/invitation?id=NeurIPS.cc/2023/Conference/Senior_Area_Chairs/-/Bid'
        request_page(selenium, bid_url, sac_client.token, wait_for_element='notes')

        notes = selenium.find_element_by_id('all-area-chairs')
        assert notes
        assert len(notes.find_elements_by_class_name('bid-container')) == 3

        header = selenium.find_element_by_id('header')
        instruction = header.find_element_by_tag_name('li')
        assert 'Please indicate your level of interest in the list of Area Chairs below, on a scale from "Very Low" interest to "Very High" interest. Area Chairs were automatically pre-ranked using the expertise information in your profile.' == instruction.text

        sac_client.post_edge(openreview.api.Edge(
            invitation='NeurIPS.cc/2023/Conference/Senior_Area_Chairs/-/Bid',
            signatures = ['~SeniorArea_GoogleChair1'],
            head = '~Area_IBMChair1',
            tail = '~SeniorArea_GoogleChair1',
            label = 'Very High'
        ))

        sac_client.post_edge(openreview.api.Edge(
            invitation='NeurIPS.cc/2023/Conference/Senior_Area_Chairs/-/Bid',
            signatures = ['~SeniorArea_GoogleChair1'],
            head = '~Area_GoogleChair1',
            tail = '~SeniorArea_GoogleChair1',
            label = 'High'
        ))

        sac_client.post_edge(openreview.api.Edge(
            invitation='NeurIPS.cc/2023/Conference/Senior_Area_Chairs/-/Bid',
            signatures = ['~SeniorArea_GoogleChair1'],
            head = '~Area_UMassChair1',
            tail = '~SeniorArea_GoogleChair1',
            label = 'Very Low'
        ))

        sac2_client=openreview.api.OpenReviewClient(username='sac2@gmail.com', password=helpers.strong_password)

        sac2_client.post_edge(openreview.api.Edge(
            invitation='NeurIPS.cc/2023/Conference/Senior_Area_Chairs/-/Bid',
            signatures = ['~SeniorArea_NeurIPSChair1'],
            head = '~Area_IBMChair1',
            tail = '~SeniorArea_NeurIPSChair1',
            label = 'Very Low'
        ))

        sac2_client.post_edge(openreview.api.Edge(
            invitation='NeurIPS.cc/2023/Conference/Senior_Area_Chairs/-/Bid',
            signatures = ['~SeniorArea_NeurIPSChair1'],
            head = '~Area_GoogleChair1',
            tail = '~SeniorArea_NeurIPSChair1',
            label = 'Very High'
        ))

        sac2_client.post_edge(openreview.api.Edge(
            invitation='NeurIPS.cc/2023/Conference/Senior_Area_Chairs/-/Bid',
            signatures = ['~SeniorArea_NeurIPSChair1'],
            head = '~Area_UMassChair1',
            tail = '~SeniorArea_NeurIPSChair1',
            label = 'Very Low'
        ))

        ## SAC assignments
        pc_client.post_edge(openreview.api.Edge(
            invitation='NeurIPS.cc/2023/Conference/Senior_Area_Chairs/-/Proposed_Assignment',
            signatures = ['NeurIPS.cc/2023/Conference'],
            head = '~Area_IBMChair1',
            tail = '~SeniorArea_GoogleChair1',
            label = 'sac-matching',
            weight = 0.94
        ))
        pc_client.post_edge(openreview.api.Edge(
            invitation='NeurIPS.cc/2023/Conference/Senior_Area_Chairs/-/Proposed_Assignment',
            signatures = ['NeurIPS.cc/2023/Conference'],
            head = '~Area_GoogleChair1',
            tail = '~SeniorArea_NeurIPSChair1',
            label = 'sac-matching',
            weight = 0.94
        ))
        pc_client.post_edge(openreview.api.Edge(
            invitation='NeurIPS.cc/2023/Conference/Senior_Area_Chairs/-/Proposed_Assignment',
            signatures = ['NeurIPS.cc/2023/Conference'],
            head = '~Area_UMassChair1',
            tail = '~SeniorArea_GoogleChair1',
            label = 'sac-matching',
            weight = 0.94
        ))

        venue.set_assignments(assignment_title='sac-matching', committee_id='NeurIPS.cc/2023/Conference/Senior_Area_Chairs', overwrite=True)

        edges=pc_client.get_edges_count(invitation='NeurIPS.cc/2023/Conference/Senior_Area_Chairs/-/Assignment')
        assert edges == 3


    def test_recruit_reviewers(self, client, openreview_client, selenium, request_page, helpers):

        pc_client=openreview.Client(username='pc@neurips.cc', password=helpers.strong_password)
        request_form=pc_client.get_notes(invitation='openreview.net/Support/-/Request_Form')[0]

        # Test Reviewer Recruitment
        request_page(selenium, 'http://localhost:3030/forum?id={}'.format(request_form.id), pc_client.token, by=By.ID, wait_for_element='note_{}'.format(request_form.id))
        recruitment_div = selenium.find_element_by_id('note_{}'.format(request_form.id))
        assert recruitment_div
        reply_row = recruitment_div.find_element_by_class_name('reply_row')
        assert reply_row
        buttons = reply_row.find_elements_by_class_name('btn-xs')
        assert [btn for btn in buttons if btn.text == 'Recruitment']

        reviewer_details = '''reviewer1@umass.edu, Reviewer UMass\nreviewer2@mit.edu, Reviewer MIT\nsac1@google.com, SAC One\nsac2@gmail.com, SAC Two'''
        recruitment_note = pc_client.post_note(openreview.Note(
            content={
                'title': 'Recruitment',
                'invitee_role': 'Reviewers',
                'invitee_reduced_load': ['2', '3', '4'],
                'invitee_details': reviewer_details,
                'invitation_email_subject': '[' + request_form.content['Abbreviated Venue Name'] + '] Invitation to serve as {{invitee_role}}',
                'invitation_email_content': 'Dear {{fullname}},\n\nYou have been nominated by the program chair committee of NeurIPS 2023 to serve as {{invitee_role}}.\n\n{{invitation_url}}\n\nIf you have any questions, please contact {{contact_info}}.\n\nCheers!\n\nProgram Chairs'
            },
            forum=request_form.forum,
            replyto=request_form.forum,
            invitation='openreview.net/Support/-/Request{}/Recruitment'.format(request_form.number),
            readers=['NeurIPS.cc/2023/Conference/Program_Chairs', 'openreview.net/Support'],
            signatures=['~Program_NeurIPSChair1'],
            writers=[]
        ))
        assert recruitment_note

        helpers.await_queue()
        process_logs = client.get_process_logs(id=recruitment_note.id)
        assert len(process_logs) == 1
        assert process_logs[0]['status'] == 'ok'
        assert process_logs[0]['invitation'] == 'openreview.net/Support/-/Request{}/Recruitment'.format(request_form.number)

        recruitment_status_notes=client.get_notes(forum=recruitment_note.forum, replyto=recruitment_note.id)
        assert len(recruitment_status_notes) == 1
        assert {'NeurIPS.cc/2023/Conference/Senior_Area_Chairs/Invited': ['sac1@google.com', 'sac2@gmail.com']} == recruitment_status_notes[0].content['already_invited']

        messages = client.get_messages(to='reviewer1@umass.edu', subject='[NeurIPS 2023] Invitation to serve as Reviewer')
        assert messages and len(messages) == 1
        assert messages[0]['content']['subject'] == '[NeurIPS 2023] Invitation to serve as Reviewer'
        assert messages[0]['content']['text'].startswith('Dear Reviewer UMass,\n\nYou have been nominated by the program chair committee of NeurIPS 2023 to serve as Reviewer.')
        assert 'pc@neurips.cc' in messages[0]['content']['text']
        invitation_url = re.search('https://.*\n', messages[0]['content']['text']).group(0).replace('https://openreview.net', 'http://localhost:3030').replace('&amp;', '&')[:-1]

        helpers.respond_invitation(selenium, request_page, invitation_url, accept=False)
        notes = selenium.find_element_by_class_name("note_editor")
        assert notes        
        messages = notes.find_elements_by_tag_name("h4")
        assert messages
        assert 'You have declined the invitation from NeurIPS 2023.' == messages[0].text
        messages = notes.find_elements_by_tag_name("p")
        assert 'If you chose to decline the invitation because the paper load is too high, you can request to reduce your load. You can request a reduced reviewer load below:' == messages[0].text

        helpers.await_queue_edit(openreview_client, invitation='NeurIPS.cc/2023/Conference/Reviewers/-/Recruitment', count=1) 
        
        assert len(client.get_group('NeurIPS.cc/2023/Conference/Reviewers').members) == 0

        group = client.get_group('NeurIPS.cc/2023/Conference/Reviewers/Declined')
        assert group
        assert len(group.members) == 1
        assert 'reviewer1@umass.edu' in group.members

        messages = client.get_messages(to='reviewer1@umass.edu', subject='[NeurIPS 2023] Reviewer Invitation declined')
        assert messages
        assert len(messages)
        assert messages[0]['content']['text'] == 'You have declined the invitation to become a Reviewer for NeurIPS 2023.\n\nIf you would like to change your decision, please follow the link in the previous invitation email and click on the "Accept" button.'

        notes = openreview_client.get_notes(invitation='NeurIPS.cc/2023/Conference/Reviewers/-/Recruitment', content={'user': 'reviewer1@umass.edu'})
        assert notes
        assert len(notes) == 1

        ## Accept with reduced load
        link = selenium.find_element_by_class_name('reduced-load-link')
        link.click()
        time.sleep(0.5)
        dropdown = selenium.find_element_by_class_name('dropdown-select__input-container')
        dropdown.click()
        time.sleep(0.5)
        values = selenium.find_elements_by_class_name('dropdown-select__option')
        assert len(values) > 0
        values[2].click()
        time.sleep(0.5)
        button = selenium.find_element_by_xpath('//button[text()="Submit"]')
        button.click()
        time.sleep(0.5)
        helpers.await_queue_edit(openreview_client, invitation='NeurIPS.cc/2023/Conference/Reviewers/-/Recruitment', count=2)        

        reviewers_group=openreview_client.get_group('NeurIPS.cc/2023/Conference/Reviewers')
        assert len(reviewers_group.members) == 1
        assert 'reviewer1@umass.edu' in reviewers_group.members

        messages = client.get_messages(to = 'reviewer1@umass.edu', subject = '[NeurIPS 2023] Reviewer Invitation accepted with reduced load')
        assert len(messages) == 1
        assert messages[0]['content']['text'] == '''Thank you for accepting the invitation to be a Reviewer for NeurIPS 2023.
You have selected a reduced load of 4 submissions to review.

The NeurIPS 2023 program chairs will be contacting you with more information regarding next steps soon. In the meantime, please add noreply@openreview.net to your email contacts to ensure that you receive all communications.

If you would like to change your decision, please follow the link in the previous invitation email and click on the "Decline" button.'''        

        ## Check reviewers console load
        reviewer_client=openreview.api.OpenReviewClient(username='reviewer1@umass.edu', password=helpers.strong_password)
        request_page(selenium, 'http://localhost:3030/group?id=NeurIPS.cc/2023/Conference/Reviewers', reviewer_client.token, by=By.ID, wait_for_element='header')
        header = selenium.find_element_by_id('header')
        strong_elements = header.find_elements_by_tag_name('strong')
        assert len(strong_elements) == 1
        assert strong_elements[0].text == '4 papers'
        
        ## Remind reviewers
        recruitment_note = pc_client.post_note(openreview.Note(
            content={
                'title': 'Remind Recruitment',
                'invitee_role': 'Reviewers',
                'invitee_reduced_load': ['2', '3', '4'],
                'invitation_email_subject': '[' + request_form.content['Abbreviated Venue Name'] + '] Invitation to serve as {{invitee_role}}',
                'invitation_email_content': 'Dear {{fullname}},\n\nYou have been nominated by the program chair committee of NeurIPS 2023 to serve as {{invitee_role}}.\n\n{{invitation_url}}\n\nCheers!\n\nProgram Chairs'
            },
            forum=request_form.forum,
            replyto=request_form.forum,
            invitation='openreview.net/Support/-/Request{}/Remind_Recruitment'.format(request_form.number),
            readers=['NeurIPS.cc/2023/Conference/Program_Chairs', 'openreview.net/Support'],
            signatures=['~Program_NeurIPSChair1'],
            writers=[]
        ))

        helpers.await_queue()

        messages = client.get_messages(to='reviewer2@mit.edu', subject='Reminder: [NeurIPS 2023] Invitation to serve as Reviewer')
        assert messages and len(messages) == 1
        assert messages[0]['content']['subject'] == 'Reminder: [NeurIPS 2023] Invitation to serve as Reviewer'
        assert messages[0]['content']['text'].startswith('Dear invitee,\n\nYou have been nominated by the program chair committee of NeurIPS 2023 to serve as Reviewer.')
        invitation_url = re.search('https://.*\n', messages[0]['content']['text']).group(0).replace('https://openreview.net', 'http://localhost:3030').replace('&amp;', '&')[:-1]
        helpers.respond_invitation(selenium, request_page, invitation_url, accept=False)

        helpers.await_queue()

        group = openreview_client.get_group('NeurIPS.cc/2023/Conference/Reviewers/Declined')
        assert group
        assert len(group.members) == 1
        assert 'reviewer2@mit.edu' in group.members

        messages = client.get_messages(to='reviewer2@mit.edu', subject='[NeurIPS 2023] Reviewer Invitation declined')
        assert messages
        assert len(messages)
        assert messages[0]['content']['text'] =='You have declined the invitation to become a Reviewer for NeurIPS 2023.\n\nIf you would like to change your decision, please follow the link in the previous invitation email and click on the "Accept" button.'

        openreview_client.add_members_to_group('NeurIPS.cc/2023/Conference/Reviewers', ['reviewer2@mit.edu', 'reviewer3@ibm.com', 'reviewer4@fb.com', 'reviewer5@google.com', 'reviewer6@amazon.com'])

    def test_enable_ethics_reviewers(self, client, helpers):

        pc_client=openreview.Client(username='pc@neurips.cc', password=helpers.strong_password)
        request_form=pc_client.get_notes(invitation='openreview.net/Support/-/Request_Form')[0] 

        now = datetime.datetime.utcnow()
        due_date = now + datetime.timedelta(days=3)
        first_date = now + datetime.timedelta(days=1)               

        venue_revision_note = pc_client.post_note(openreview.Note(
            content={
                'title': 'Conference on Neural Information Processing Systems',
                'Official Venue Name': 'Conference on Neural Information Processing Systems',
                'Abbreviated Venue Name': 'NeurIPS 2023',
                'Official Website URL': 'https://neurips.cc',
                'program_chair_emails': ['pc@neurips.cc'],
                'contact_email': 'pc@neurips.cc',
                'ethics_chairs_and_reviewers': 'Yes, our venue has Ethics Chairs and Reviewers',
                'Venue Start Date': '2023/12/01',
                'Submission Deadline': due_date.strftime('%Y/%m/%d'),
                'abstract_registration_deadline': first_date.strftime('%Y/%m/%d'),
                'Location': 'Virtual',
                'submission_reviewer_assignment': 'Automatic',
                'How did you hear about us?': 'ML conferences',
                'Expected Submissions': '100'
            },
            forum=request_form.forum,
            invitation='openreview.net/Support/-/Request{}/Revision'.format(request_form.number),
            readers=['{}/Program_Chairs'.format('NeurIPS.cc/2023/Conference'), 'openreview.net/Support'],
            referent=request_form.forum,
            replyto=request_form.forum,
            signatures=['~Program_NeurIPSChair1'],
            writers=[]
        ))
        
        helpers.await_queue()

        assert pc_client.get_group('NeurIPS.cc/2023/Conference/Ethics_Chairs')      
        assert pc_client.get_group('NeurIPS.cc/2023/Conference/Ethics_Reviewers')

        assert pc_client.get_invitation('openreview.net/Support/-/Request{}/Ethics_Review_Stage'.format(request_form.number))
    
    def test_recruit_ethics_reviewers(self, client, request_page, selenium, helpers):

        ## Need super user permission to add the venue to the active_venues group
        pc_client=openreview.Client(username='pc@neurips.cc', password=helpers.strong_password)
        request_form=client.get_notes(invitation='openreview.net/Support/-/Request_Form', sort='tmdate')[0]
        conference=openreview.helpers.get_conference(client, request_form.id)

        # result = conference.recruit_reviewers(invitees = ['reviewer2@mit.edu'], title = 'Ethics Review invitation', message = '{accept_url}, {decline_url}', reviewers_name = 'Ethics_Reviewers')
        # assert result['invited'] == ['reviewer2@mit.edu']

        reviewer_details = '''reviewer2@mit.edu, Reviewer MIT'''
        recruitment_note = pc_client.post_note(openreview.Note(
            content={
                'title': 'Recruitment',
                'invitee_role': 'Ethics_Reviewers',
                'invitee_reduced_load': ['2', '3', '4'],
                'invitee_details': reviewer_details,
                'invitation_email_subject': '[' + request_form.content['Abbreviated Venue Name'] + '] Invitation to serve as {{invitee_role}}',
                'invitation_email_content': 'Dear {{fullname}},\n\nYou have been nominated by the program chair committee of NeurIPS 2023 to serve as {{invitee_role}}.\n\n{{invitation_url}}\n\nIf you have any questions, please contact {{contact_info}}.\n\nCheers!\n\nProgram Chairs'
            },
            forum=request_form.forum,
            replyto=request_form.forum,
            invitation='openreview.net/Support/-/Request{}/Recruitment'.format(request_form.number),
            readers=['NeurIPS.cc/2023/Conference/Program_Chairs', 'openreview.net/Support'],
            signatures=['~Program_NeurIPSChair1'],
            writers=[]
        ))
        assert recruitment_note
        helpers.await_queue()        
              
        assert client.get_group('NeurIPS.cc/2023/Conference/Ethics_Reviewers')
        assert client.get_group('NeurIPS.cc/2023/Conference/Ethics_Reviewers/Declined')
        group = client.get_group('NeurIPS.cc/2023/Conference/Ethics_Reviewers/Invited')
        assert group
        assert len(group.members) == 1
        assert 'reviewer2@mit.edu' in group.members

        messages = client.get_messages(to='reviewer2@mit.edu', subject='[NeurIPS 2023] Invitation to serve as Ethics Reviewer')
        assert messages and len(messages) == 1
        invitation_url = re.search('https://.*\n', messages[0]['content']['text']).group(0).replace('https://openreview.net', 'http://localhost:3030').replace('&amp;', '&')[:-1]
        helpers.respond_invitation(selenium, request_page, invitation_url, accept=True)

        helpers.await_queue()

        group = client.get_group('NeurIPS.cc/2023/Conference/Ethics_Reviewers')
        assert group
        assert len(group.members) == 1
        assert 'reviewer2@mit.edu' in group.members

        result = conference.recruit_reviewers(invitees = ['reviewer2@mit.edu'], title = 'Ethics Review invitation', message = '{accept_url}, {decline_url}', reviewers_name = 'Ethics_Reviewers')
        assert result['invited'] == []
        assert result['already_invited'] == {
            'NeurIPS.cc/2023/Conference/Ethics_Reviewers/Invited': ['reviewer2@mit.edu']
        }

    def test_update_submission_invitation(self, client, helpers, openreview_client):

        # add pre-process to submission invitation
        submission_inv = openreview_client.get_invitation('NeurIPS.cc/2023/Conference/-/Submission')
        openreview_client.post_invitation_edit(
            invitations ='NeurIPS.cc/2023/Conference/-/Edit',
            signatures=['NeurIPS.cc/2023/Conference'],
            invitation=openreview.api.Invitation(id=submission_inv.id,
                preprocess = 'def process(client, edit, invitation):\n    domain = client.get_group(invitation.domain)\n  \n    note = edit.note\n    \n    if note.ddate:\n        return\n\n'
            )
        )
        
        # use revision button
        pc_client=openreview.Client(username='pc@neurips.cc', password=helpers.strong_password)
        request_form=client.get_notes(invitation='openreview.net/Support/-/Request_Form', sort='tmdate')[0]

        venue_revision_note = pc_client.post_note(openreview.Note(
            content={
                'title': 'Conference on Neural Information Processing Systems',
                'Official Venue Name': 'Conference on Neural Information Processing Systems',
                'Abbreviated Venue Name': 'NeurIPS 2023',
                'Official Website URL': 'https://neurips.cc',
                'program_chair_emails': ['pc@neurips.cc'],
                'contact_email': 'pc@neurips.cc',
                'submission_reviewer_assignment': 'Automatic',
                'ethics_chairs_and_reviewers': 'Yes, our venue has Ethics Chairs and Reviewers',
                'Venue Start Date': '2023/12/12',
                'Submission Deadline': request_form.content['Submission Deadline'],
                'abstract_registration_deadline': request_form.content['abstract_registration_deadline'],
                'Location': 'Virtual',
                'How did you hear about us?': 'ML conferences',
                'Expected Submissions': '100'
            },
            forum=request_form.forum,
            invitation='openreview.net/Support/-/Request{}/Revision'.format(request_form.number),
            readers=['{}/Program_Chairs'.format('NeurIPS.cc/2023/Conference'), 'openreview.net/Support'],
            referent=request_form.forum,
            replyto=request_form.forum,
            signatures=['~Program_NeurIPSChair1'],
            writers=[]
        ))
        
        helpers.await_queue()

        submission_inv = openreview_client.get_invitation('NeurIPS.cc/2023/Conference/-/Submission')
        assert submission_inv.preprocess
        assert 'def process(client, edit, invitation):' in submission_inv.preprocess

        assert submission_inv.edit['readers'] == [
            'NeurIPS.cc/2023/Conference',
            '${2/note/content/authorids/value}'
            ]
        assert submission_inv.edit['writers'] == [
            'NeurIPS.cc/2023/Conference',
            '${2/note/content/authorids/value}'
            ]
        assert submission_inv.signatures == ['NeurIPS.cc/2023/Conference/Program_Chairs']

    def test_submit_papers(self, test_client, client, helpers, openreview_client):

        pc_client=openreview.Client(username='pc@neurips.cc', password=helpers.strong_password)
        request_form=client.get_notes(invitation='openreview.net/Support/-/Request_Form', sort='tmdate')[0]

        test_client = openreview.api.OpenReviewClient(username='test@mail.com', password=helpers.strong_password)

        domains = ['umass.edu', 'amazon.com', 'fb.com', 'cs.umass.edu', 'google.com', 'mit.edu']
        for i in range(1,6):
            note = openreview.api.Note(
                content = {
                    'title': { 'value': 'Paper title ' + str(i) },
                    'abstract': { 'value': 'This is an abstract ' + str(i) },
                    'authorids': { 'value': ['test@mail.com', 'peter@mail.com', 'andrew@' + domains[i]] },
                    'authors': { 'value': ['SomeFirstName User', 'Peter SomeLastName', 'Andrew Mc'] },
                    'keywords': { 'value': ['machine learning', 'nlp'] },
                }
            )
            if i == 1:
                note.content['authors']['value'].append('SeniorArea GoogleChair')
                note.content['authorids']['value'].append('~SeniorArea_GoogleChair1')
                print(note)

            test_client.post_note_edit(invitation='NeurIPS.cc/2023/Conference/-/Submission',
                signatures=['~SomeFirstName_User1'],
                note=note)            


        ## finish submission deadline
        now = datetime.datetime.utcnow()
        due_date = now + datetime.timedelta(days=3)
        first_date = now - datetime.timedelta(minutes=28)               

        venue_revision_note = pc_client.post_note(openreview.Note(
            content={
                'title': 'Conference on Neural Information Processing Systems',
                'Official Venue Name': 'Conference on Neural Information Processing Systems',
                'Abbreviated Venue Name': 'NeurIPS 2023',
                'Official Website URL': 'https://neurips.cc',
                'program_chair_emails': ['pc@neurips.cc'],
                'contact_email': 'pc@neurips.cc',
                'ethics_chairs_and_reviewers': 'Yes, our venue has Ethics Chairs and Reviewers',
                'Venue Start Date': '2023/12/01',
                'Submission Deadline': due_date.strftime('%Y/%m/%d %H:%M'),
                'abstract_registration_deadline': first_date.strftime('%Y/%m/%d %H:%M'),
                'Location': 'Virtual',
                'submission_reviewer_assignment': 'Automatic',
                'How did you hear about us?': 'ML conferences',
                'Expected Submissions': '100'
            },
            forum=request_form.forum,
            invitation='openreview.net/Support/-/Request{}/Revision'.format(request_form.number),
            readers=['{}/Program_Chairs'.format('NeurIPS.cc/2023/Conference'), 'openreview.net/Support'],
            referent=request_form.forum,
            replyto=request_form.forum,
            signatures=['~Program_NeurIPSChair1'],
            writers=[]
        ))
        
        helpers.await_queue()
        helpers.await_queue_edit(openreview_client, 'NeurIPS.cc/2023/Conference/-/Post_Submission-0-0')
        helpers.await_queue_edit(openreview_client, 'NeurIPS.cc/2023/Conference/-/Withdrawal-0-0')
        helpers.await_queue_edit(openreview_client, 'NeurIPS.cc/2023/Conference/-/Desk_Rejection-0-0')
        helpers.await_queue_edit(openreview_client, 'NeurIPS.cc/2023/Conference/-/Revision-0-0')

        notes = test_client.get_notes(content= { 'venueid': 'NeurIPS.cc/2023/Conference/Submission' }, sort='number:desc')
        assert len(notes) == 5

        assert notes[0].readers == ['NeurIPS.cc/2023/Conference', 'NeurIPS.cc/2023/Conference/Submission5/Authors']

        assert test_client.get_invitation('NeurIPS.cc/2023/Conference/Submission5/-/Withdrawal')
        assert test_client.get_invitation('NeurIPS.cc/2023/Conference/Submission5/-/Desk_Rejection')
        assert test_client.get_invitation('NeurIPS.cc/2023/Conference/Submission5/-/Revision')

        ## update submission
        revision_note = test_client.post_note_edit(invitation='NeurIPS.cc/2023/Conference/Submission4/-/Revision',
            signatures=['NeurIPS.cc/2023/Conference/Submission4/Authors'],
            note=openreview.api.Note(
                content={
                    'title': { 'value': 'Paper title 4 Updated' },
                    'abstract': { 'value': 'This is an abstract 4 updated' },
                    'authorids': { 'value': ['test@mail.com', 'andrew@google.com', 'peter@mail.com' ] },
                    'authors': { 'value': ['SomeFirstName User',  'Andrew Mc', 'Peter SomeLastName'] },
                    'keywords': { 'value': ['machine learning', 'nlp'] },
                }
            ))
        helpers.await_queue_edit(openreview_client, edit_id=revision_note['id'])

        ## withdraw submission
        withdraw_note = test_client.post_note_edit(invitation='NeurIPS.cc/2023/Conference/Submission5/-/Withdrawal',
            signatures=['NeurIPS.cc/2023/Conference/Submission5/Authors'],
            note=openreview.api.Note(
                content={
                    'withdrawal_confirmation': { 'value': 'I have read and agree with the venue\'s withdrawal policy on behalf of myself and my co-authors.' },
                }
            ))

        helpers.await_queue_edit(openreview_client, edit_id=withdraw_note['id'])
        helpers.await_queue_edit(openreview_client, invitation='NeurIPS.cc/2023/Conference/-/Withdrawn_Submission')

        note = test_client.get_note(withdraw_note['note']['forum'])
        assert note
        assert note.invitations == ['NeurIPS.cc/2023/Conference/-/Submission', 'NeurIPS.cc/2023/Conference/-/Post_Submission', 'NeurIPS.cc/2023/Conference/-/Withdrawn_Submission']
        assert note.readers == ['NeurIPS.cc/2023/Conference', 'NeurIPS.cc/2023/Conference/Submission5/Authors']
        assert note.writers == ['NeurIPS.cc/2023/Conference', 'NeurIPS.cc/2023/Conference/Submission5/Authors']
        assert note.signatures == ['NeurIPS.cc/2023/Conference/Submission5/Authors']
        assert note.content['venue']['value'] == 'NeurIPS 2023 Conference Withdrawn Submission'
        assert note.content['venueid']['value'] == 'NeurIPS.cc/2023/Conference/Withdrawn_Submission'
        assert 'readers' in note.content['authors']
        assert 'readers' in note.content['authorids'] 

        messages = client.get_messages(subject='[NeurIPS 2023]: Paper #5 withdrawn by paper authors')
        assert len(messages) == 3

        due_date = now - datetime.timedelta(minutes=30)

        venue_revision_note = pc_client.post_note(openreview.Note(
            content={
                'title': 'Conference on Neural Information Processing Systems',
                'Official Venue Name': 'Conference on Neural Information Processing Systems',
                'Abbreviated Venue Name': 'NeurIPS 2023',
                'Official Website URL': 'https://neurips.cc',
                'program_chair_emails': ['pc@neurips.cc'],
                'contact_email': 'pc@neurips.cc',
                'ethics_chairs_and_reviewers': 'Yes, our venue has Ethics Chairs and Reviewers',
                'Venue Start Date': '2023/12/01',
                'Submission Deadline': due_date.strftime('%Y/%m/%d %H:%M'),
                'abstract_registration_deadline': first_date.strftime('%Y/%m/%d %H:%M'),
                'Location': 'Virtual',
                'submission_reviewer_assignment': 'Automatic',
                'How did you hear about us?': 'ML conferences',
                'Expected Submissions': '100'
            },
            forum=request_form.forum,
            invitation='openreview.net/Support/-/Request{}/Revision'.format(request_form.number),
            readers=['{}/Program_Chairs'.format('NeurIPS.cc/2023/Conference'), 'openreview.net/Support'],
            referent=request_form.forum,
            replyto=request_form.forum,
            signatures=['~Program_NeurIPSChair1'],
            writers=[]
        ))

        helpers.await_queue()
        helpers.await_queue_edit(openreview_client, 'NeurIPS.cc/2023/Conference/-/Revision-0-1', count=3)

        with pytest.raises(openreview.OpenReviewException, match=r'The Invitation NeurIPS.cc/2023/Conference/Submission5/-/Revision has expired'):
            assert test_client.get_invitation('NeurIPS.cc/2023/Conference/Submission5/-/Revision')

        notes = test_client.get_notes(content= { 'venueid': 'NeurIPS.cc/2023/Conference/Submission' }, sort='number:desc')
        assert len(notes) == 4

        reply_invitations = test_client.get_invitations(replyForum=notes[0].id)
        assert len(reply_invitations) == 1
        assert 'NeurIPS.cc/2023/Conference/Submission4/-/Withdrawal' == reply_invitations[0].id

        now = datetime.datetime.utcnow()
        start_date = now
        due_date = now + datetime.timedelta(days=3)
        revision_stage_note = pc_client.post_note(openreview.Note(
            content={
                'submission_revision_name': 'Supplementary_Material',
                'submission_revision_start_date': start_date.strftime('%Y/%m/%d'),
                'submission_revision_deadline': due_date.strftime('%Y/%m/%d'),
                'accepted_submissions_only': 'Enable revision for all submissions',
                'submission_author_edition': 'Allow addition and removal of authors',
                'submission_revision_additional_options': {
                    "supplementary_material": {
                        "value": {
                            "param": {
                                "type": "file",
                                "extensions": [
                                    "zip",
                                    "pdf",
                                    "tgz",
                                    "gz"
                                ],
                                "maxSize": 100,
                                "deletable": True
                            }
                        },
                        "description": "All supplementary material must be self-contained and zipped into a single file. Note that supplementary material will be visible to reviewers and the public throughout and after the review period, and ensure all material is anonymized. The maximum file size is 100MB.",
                        "order": 1
                    },            
                },
                'submission_revision_remove_options': ['title', 'authors', 'authorids', 'TLDR', 'abstract', 'pdf', 'keywords']
            },
            forum=request_form.forum,
            invitation='openreview.net/Support/-/Request{}/Submission_Revision_Stage'.format(request_form.number),
            readers=['{}/Program_Chairs'.format('NeurIPS.cc/2023/Conference'), 'openreview.net/Support'],
            referent=request_form.forum,
            replyto=request_form.forum,
            signatures=['~Program_NeurIPSChair1'],
            writers=[]
        ))
        assert revision_stage_note

        helpers.await_queue()
        helpers.await_queue_edit(openreview_client, 'NeurIPS.cc/2023/Conference/-/Supplementary_Material-0-1', count=1)

        assert len(test_client.get_invitations(invitation='NeurIPS.cc/2023/Conference/-/Supplementary_Material')) == 4

        revision_note = test_client.post_note_edit(invitation='NeurIPS.cc/2023/Conference/Submission4/-/Supplementary_Material',
            signatures=['NeurIPS.cc/2023/Conference/Submission4/Authors'],
            note=openreview.api.Note(
                content={
                    'supplementary_material': { 'value': '/attachment/' + 's' * 40 +'.zip' }
                }
            ))
        helpers.await_queue_edit(openreview_client, edit_id=revision_note['id'])



    def test_post_submission_stage(self, helpers, openreview_client, client, request_page, selenium):

        pc_client=openreview.Client(username='pc@neurips.cc', password=helpers.strong_password)
        request_form=pc_client.get_notes(invitation='openreview.net/Support/-/Request_Form')[0]

        post_submission_note=pc_client.post_note(openreview.Note(
            content= {
                'force': 'Yes',
                'hide_fields': ['keywords'],
                'submission_readers': 'All program committee (all reviewers, all area chairs, all senior area chairs if applicable)'
            },
            forum= request_form.id,
            invitation= f'openreview.net/Support/-/Request{request_form.number}/Post_Submission',
            readers= ['NeurIPS.cc/2023/Conference/Program_Chairs', 'openreview.net/Support'],
            referent= request_form.id,
            replyto= request_form.id,
            signatures= ['~Program_NeurIPSChair1'],
            writers= [],
        ))

        helpers.await_queue()

        notes = openreview_client.get_notes(content= { 'venueid': 'NeurIPS.cc/2023/Conference/Submission' }, sort='number:desc')
        assert len(notes) == 4

        assert 'readers' in notes[0].content['keywords']

        assert notes[0].readers == ['NeurIPS.cc/2023/Conference',
            'NeurIPS.cc/2023/Conference/Senior_Area_Chairs',
            'NeurIPS.cc/2023/Conference/Area_Chairs',
            'NeurIPS.cc/2023/Conference/Reviewers',
            'NeurIPS.cc/2023/Conference/Submission4/Authors']

        # assert client.get_group('NeurIPS.cc/2023/Conference/Paper5/Senior_Area_Chairs').readers == ['NeurIPS.cc/2023/Conference',
        #     'NeurIPS.cc/2023/Conference/Program_Chairs',
        #     'NeurIPS.cc/2023/Conference/Paper5/Senior_Area_Chairs',
        #     'NeurIPS.cc/2023/Conference/Paper5/Area_Chairs',
        #     'NeurIPS.cc/2023/Conference/Paper5/Reviewers']
        # assert client.get_group('NeurIPS.cc/2023/Conference/Paper5/Senior_Area_Chairs').nonreaders == ['NeurIPS.cc/2023/Conference/Paper5/Authors']

        # assert client.get_group('NeurIPS.cc/2023/Conference/Paper5/Area_Chairs').readers == ['NeurIPS.cc/2023/Conference',
        #     'NeurIPS.cc/2023/Conference/Program_Chairs',
        #     'NeurIPS.cc/2023/Conference/Paper5/Senior_Area_Chairs',
        #     'NeurIPS.cc/2023/Conference/Paper5/Area_Chairs',
        #     'NeurIPS.cc/2023/Conference/Paper5/Reviewers']

        # assert client.get_group('NeurIPS.cc/2023/Conference/Paper5/Area_Chairs').deanonymizers == ['NeurIPS.cc/2023/Conference',
        #     'NeurIPS.cc/2023/Conference/Program_Chairs',
        #     'NeurIPS.cc/2023/Conference/Paper5/Senior_Area_Chairs',
        #     'NeurIPS.cc/2023/Conference/Paper5/Area_Chairs',
        #     'NeurIPS.cc/2023/Conference/Paper5/Reviewers']

        # assert client.get_group('NeurIPS.cc/2023/Conference/Paper5/Area_Chairs').nonreaders == ['NeurIPS.cc/2023/Conference/Paper5/Authors']

        # assert client.get_group('NeurIPS.cc/2023/Conference/Paper5/Reviewers').readers == ['NeurIPS.cc/2023/Conference',
        #     'NeurIPS.cc/2023/Conference/Paper5/Senior_Area_Chairs',
        #     'NeurIPS.cc/2023/Conference/Paper5/Area_Chairs',
        #     'NeurIPS.cc/2023/Conference/Paper5/Reviewers']

        # assert client.get_group('NeurIPS.cc/2023/Conference/Paper5/Reviewers').deanonymizers == ['NeurIPS.cc/2023/Conference',
        #     'NeurIPS.cc/2023/Conference/Program_Chairs',
        #     'NeurIPS.cc/2023/Conference/Paper5/Senior_Area_Chairs',
        #     'NeurIPS.cc/2023/Conference/Paper5/Area_Chairs',
        #     'NeurIPS.cc/2023/Conference/Paper5/Reviewers']

        # assert client.get_group('NeurIPS.cc/2023/Conference/Paper5/Reviewers').nonreaders == ['NeurIPS.cc/2023/Conference/Paper5/Authors']

#     def test_update_withdraw_desk_reject_invitations(self, conference, client, helpers):
#         pc_client = openreview.Client(username='pc@neurips.cc', password=helpers.strong_password)
#         request_form = pc_client.get_notes(invitation='openreview.net/Support/-/Request_Form')[0]

#         now = datetime.datetime.utcnow()
#         due_date = now + datetime.timedelta(days=-1)
#         first_date = now + datetime.timedelta(days=-2)

#         # expire submission deadlne
#         venue_revision_note = pc_client.post_note(openreview.Note(
#             content={
#                 'title': 'Conference on Neural Information Processing Systems',
#                 'Official Venue Name': 'Conference on Neural Information Processing Systems',
#                 'Abbreviated Venue Name': 'NeurIPS 2023',
#                 'Official Website URL': 'https://neurips.cc',
#                 'program_chair_emails': ['pc@neurips.cc'],
#                 'contact_email': 'pc@neurips.cc',
#                 'ethics_chairs_and_reviewers': 'Yes, our venue has Ethics Chairs and Reviewers',
#                 'Venue Start Date': '2023/12/01',
#                 'Submission Deadline': due_date.strftime('%Y/%m/%d'),
#                 'abstract_registration_deadline': first_date.strftime('%Y/%m/%d'),
#                 'Location': 'Virtual',
#                 'How did you hear about us?': 'ML conferences',
#                 'Expected Submissions': '100',
#                 'withdrawn_submissions_author_anonymity': 'Yes, author identities of withdrawn submissions should be revealed.',
#                 'desk_rejected_submissions_author_anonymity': 'Yes, author identities of desk rejected submissions should be revealed.',
#                 'email_pcs_for_withdrawn_submissions': 'No, do not email PCs.',
#                 'withdrawn_submissions_visibility': 'No, withdrawn submissions should not be made public.',
#                 'desk_rejected_submissions_visibility': 'No, desk rejected submissions should not be made public.'

#             },
#             forum=request_form.forum,
#             invitation='openreview.net/Support/-/Request{}/Revision'.format(request_form.number),
#             readers=['{}/Program_Chairs'.format('NeurIPS.cc/2023/Conference'), 'openreview.net/Support'],
#             referent=request_form.forum,
#             replyto=request_form.forum,
#             signatures=['~Program_NeurIPSChair1'],
#             writers=[]
#         ))

#         helpers.await_queue()

#         withdraw_super_invitation = client.get_invitation(conference.get_invitation_id('Withdraw'))
#         assert 'REVEAL_AUTHORS_ON_WITHDRAW = True' in withdraw_super_invitation.process
#         assert 'REVEAL_SUBMISSIONS_ON_WITHDRAW = False' in withdraw_super_invitation.process

#         # update withdraw submissions author anonymity
#         venue_revision_note.content['withdrawn_submissions_author_anonymity'] = 'No, author identities of withdrawn submissions should not be revealed.'

#         pc_client.post_note(openreview.Note(
#             content={
#                 'title': 'Conference on Neural Information Processing Systems',
#                 'Official Venue Name': 'Conference on Neural Information Processing Systems',
#                 'Abbreviated Venue Name': 'NeurIPS 2023',
#                 'Official Website URL': 'https://neurips.cc',
#                 'program_chair_emails': ['pc@neurips.cc'],
#                 'contact_email': 'pc@neurips.cc',
#                 'ethics_chairs_and_reviewers': 'Yes, our venue has Ethics Chairs and Reviewers',
#                 'Venue Start Date': '2023/12/01',
#                 'Submission Deadline': due_date.strftime('%Y/%m/%d'),
#                 'abstract_registration_deadline': first_date.strftime('%Y/%m/%d'),
#                 'Location': 'Virtual',
#                 'How did you hear about us?': 'ML conferences',
#                 'Expected Submissions': '100',
#                 'withdrawn_submissions_author_anonymity': 'No, author identities of withdrawn submissions should not be revealed.',
#                 'desk_rejected_submissions_author_anonymity': 'Yes, author identities of desk rejected submissions should be revealed.',
#                 'email_pcs_for_withdrawn_submissions': 'No, do not email PCs.',
#                 'withdrawn_submissions_visibility': 'No, withdrawn submissions should not be made public.',
#                 'desk_rejected_submissions_visibility': 'No, desk rejected submissions should not be made public.'

#             },
#             forum=request_form.forum,
#             invitation='openreview.net/Support/-/Request{}/Revision'.format(request_form.number),
#             readers=['{}/Program_Chairs'.format('NeurIPS.cc/2023/Conference'), 'openreview.net/Support'],
#             referent=request_form.forum,
#             replyto=request_form.forum,
#             signatures=['~Program_NeurIPSChair1'],
#             writers=[]
#         ))
#         helpers.await_queue()

#         withdraw_super_invitation = client.get_invitation(conference.get_invitation_id('Withdraw'))
#         assert 'REVEAL_AUTHORS_ON_WITHDRAW = False' in withdraw_super_invitation.process

#     def test_setup_matching(self, conference, client, helpers):

#         now = datetime.datetime.utcnow()

#         pc_client=openreview.Client(username='pc@neurips.cc', password=helpers.strong_password)
#         request_form = pc_client.get_notes(invitation='openreview.net/Support/-/Request_Form')[0]
#         submissions=conference.get_submissions(sort='tmdate')

#         with open(os.path.join(os.path.dirname(__file__), 'data/reviewer_affinity_scores.csv'), 'w') as file_handle:
#             writer = csv.writer(file_handle)
#             for submission in submissions:
#                 writer.writerow([submission.id, '~Area_IBMChair1', round(random.random(), 2)])
#                 writer.writerow([submission.id, '~Area_GoogleChair1', round(random.random(), 2)])
#                 writer.writerow([submission.id, '~Area_UMassChair1', round(random.random(), 2)])

#         conference.setup_matching(committee_id=conference.get_area_chairs_id(), build_conflicts='NeurIPS', affinity_score_file=os.path.join(os.path.dirname(__file__), 'data/reviewer_affinity_scores.csv'))
        
#         conflicts = client.get_edges_count(invitation='NeurIPS.cc/2023/Conference/Area_Chairs/-/Conflict')
#         assert conflicts == 3

#         ## Paper 4 conflicts
#         conflicts = client.get_edges(invitation='NeurIPS.cc/2023/Conference/Area_Chairs/-/Conflict', head=submissions[1].id)
#         assert len(conflicts) == 1
#         assert '~Area_GoogleChair1' == conflicts[0].tail ## reviewer and one author are from google

#         conference.set_matching_alternate_conflicts(committee_id=conference.get_area_chairs_id(), source_committee_id=conference.get_senior_area_chairs_id(), source_assignment_title='sac-matching', conflict_label='SAC Conflict')
        
#         conflicts = client.get_edges_count(invitation='NeurIPS.cc/2023/Conference/Area_Chairs/-/Conflict')
#         assert conflicts == 13

#         conflicts = client.get_edges(invitation='NeurIPS.cc/2023/Conference/Area_Chairs/-/Conflict', head=submissions[1].id)
#         assert len(conflicts) == 3
#         tails = [c.tail for c in conflicts]
#         assert '~Area_GoogleChair1' in tails ## reviewer and one author are from google
#         assert '~Area_IBMChair1' in tails ## assgined SAC is from google
#         assert '~Area_UMassChair1' in tails ## assigned SAC is from google


#         with open(os.path.join(os.path.dirname(__file__), 'data/reviewer_affinity_scores.csv'), 'w') as file_handle:
#             writer = csv.writer(file_handle)
#             for submission in submissions:
#                 writer.writerow([submission.id, '~Reviewer_UMass1', round(random.random(), 2)])
#                 writer.writerow([submission.id, '~Reviewer_MIT1', round(random.random(), 2)])
#                 writer.writerow([submission.id, '~Reviewer_IBM1', round(random.random(), 2)])
#                 writer.writerow([submission.id, '~Reviewer_Facebook1', round(random.random(), 2)])
#                 writer.writerow([submission.id, '~Reviewer_Google1', round(random.random(), 2)])


#         conference.setup_matching(committee_id=conference.get_reviewers_id(), build_conflicts='NeurIPS', affinity_score_file=os.path.join(os.path.dirname(__file__), 'data/reviewer_affinity_scores.csv'))

#         conference.bid_stages['NeurIPS.cc/2023/Conference/Area_Chairs'] = openreview.stages.BidStage(due_date=now + datetime.timedelta(days=3), committee_id='NeurIPS.cc/2023/Conference/Area_Chairs', score_ids=['NeurIPS.cc/2023/Conference/Area_Chairs/-/Affinity_Score'], allow_conflicts_bids=True)
#         conference.bid_stages['NeurIPS.cc/2023/Conference/Reviewers'] = openreview.stages.BidStage(due_date=now + datetime.timedelta(days=3), committee_id='NeurIPS.cc/2023/Conference/Reviewers', score_ids=['NeurIPS.cc/2023/Conference/Reviewers/-/Affinity_Score'], allow_conflicts_bids=True)
#         conference.create_bid_stages()

#         assert client.get_edges_count(invitation='NeurIPS.cc/2023/Conference/Reviewers/-/Custom_Max_Papers') == 1
#         ac_quotas=client.get_edges(invitation='NeurIPS.cc/2023/Conference/Area_Chairs/-/Custom_Max_Papers', head='NeurIPS.cc/2023/Conference/Area_Chairs')
#         assert len(ac_quotas) == 1
#         assert ac_quotas[0].weight == 3
#         assert ac_quotas[0].head == 'NeurIPS.cc/2023/Conference/Area_Chairs'
#         assert ac_quotas[0].tail == '~Area_IBMChair1'


#         ## Reviewer quotas
#         client.post_edge(openreview.Edge(
#             invitation='NeurIPS.cc/2023/Conference/Reviewers/-/Custom_Max_Papers',
#             readers = [conference.id, 'NeurIPS.cc/2023/Conference/Senior_Area_Chairs', 'NeurIPS.cc/2023/Conference/Area_Chairs', '~Reviewer_MIT1'],
#             writers = [conference.id],
#             signatures = [conference.id],
#             head = 'NeurIPS.cc/2023/Conference/Reviewers',
#             tail = '~Reviewer_MIT1',
#             weight = 4
#         ))

#         client.post_edge(openreview.Edge(
#             invitation='NeurIPS.cc/2023/Conference/Reviewers/-/Custom_Max_Papers',
#             readers = [conference.id, 'NeurIPS.cc/2023/Conference/Senior_Area_Chairs', 'NeurIPS.cc/2023/Conference/Area_Chairs', '~Reviewer_IBM1'],
#             writers = [conference.id],
#             signatures = [conference.id],
#             head = 'NeurIPS.cc/2023/Conference/Reviewers',
#             tail = '~Reviewer_IBM1',
#             weight = 1
#         ))

#         client.post_edge(openreview.Edge(
#             invitation='NeurIPS.cc/2023/Conference/Reviewers/-/Custom_Max_Papers',
#             readers = [conference.id, 'NeurIPS.cc/2023/Conference/Senior_Area_Chairs', 'NeurIPS.cc/2023/Conference/Area_Chairs', '~Reviewer_Facebook1'],
#             writers = [conference.id],
#             signatures = [conference.id],
#             head = 'NeurIPS.cc/2023/Conference/Reviewers',
#             tail = '~Reviewer_Facebook1',
#             weight = 6
#         ))

#         client.post_edge(openreview.Edge(
#             invitation='NeurIPS.cc/2023/Conference/Reviewers/-/Custom_Max_Papers',
#             readers = [conference.id, 'NeurIPS.cc/2023/Conference/Senior_Area_Chairs', 'NeurIPS.cc/2023/Conference/Area_Chairs', '~Reviewer_Google1'],
#             writers = [conference.id],
#             signatures = [conference.id],
#             head = 'NeurIPS.cc/2023/Conference/Reviewers',
#             tail = '~Reviewer_Google1',
#             weight = 6
#         ))

#         ## AC assignments
#         client.post_edge(openreview.Edge(
#             invitation='NeurIPS.cc/2023/Conference/Area_Chairs/-/Proposed_Assignment',
#             readers = [conference.id, f'NeurIPS.cc/2023/Conference/Paper{submissions[0].number}/Senior_Area_Chairs', '~Area_IBMChair1'],
#             writers = [conference.id, f'NeurIPS.cc/2023/Conference/Paper{submissions[0].number}/Senior_Area_Chairs'],
#             nonreaders = [f'NeurIPS.cc/2023/Conference/Paper{submissions[0].number}/Authors'],
#             signatures = [conference.id],
#             head = submissions[0].id,
#             tail = '~Area_IBMChair1',
#             label = 'ac-matching',
#             weight = 0.94
#         ))
#         client.post_edge(openreview.Edge(
#             invitation='NeurIPS.cc/2023/Conference/Area_Chairs/-/Proposed_Assignment',
#             readers = [conference.id, f'NeurIPS.cc/2023/Conference/Paper{submissions[1].number}/Senior_Area_Chairs', '~Area_IBMChair1'],
#             writers = [conference.id, f'NeurIPS.cc/2023/Conference/Paper{submissions[1].number}/Senior_Area_Chairs'],
#             nonreaders = [f'NeurIPS.cc/2023/Conference/Paper{submissions[1].number}/Authors'],
#             signatures = [conference.id],
#             head = submissions[1].id,
#             tail = '~Area_IBMChair1',
#             label = 'ac-matching',
#             weight = 0.94
#         ))
#         client.post_edge(openreview.Edge(
#             invitation='NeurIPS.cc/2023/Conference/Area_Chairs/-/Proposed_Assignment',
#             readers = [conference.id, f'NeurIPS.cc/2023/Conference/Paper{submissions[2].number}/Senior_Area_Chairs', '~Area_UMassChair1'],
#             writers = [conference.id, f'NeurIPS.cc/2023/Conference/Paper{submissions[2].number}/Senior_Area_Chairs'],
#             nonreaders = [f'NeurIPS.cc/2023/Conference/Paper{submissions[2].number}/Authors'],
#             signatures = [conference.id],
#             head = submissions[2].id,
#             tail = '~Area_UMassChair1',
#             label = 'ac-matching',
#             weight = 0.94
#         ))
#         client.post_edge(openreview.Edge(
#             invitation='NeurIPS.cc/2023/Conference/Area_Chairs/-/Proposed_Assignment',
#             readers = [conference.id, f'NeurIPS.cc/2023/Conference/Paper{submissions[3].number}/Senior_Area_Chairs', '~Area_GoogleChair1'],
#             writers = [conference.id, f'NeurIPS.cc/2023/Conference/Paper{submissions[3].number}/Senior_Area_Chairs'],
#             nonreaders = [f'NeurIPS.cc/2023/Conference/Paper{submissions[3].number}/Authors'],
#             signatures = [conference.id],
#             head = submissions[3].id,
#             tail = '~Area_GoogleChair1',
#             label = 'ac-matching',
#             weight = 0.94
#         ))
#         client.post_edge(openreview.Edge(
#             invitation='NeurIPS.cc/2023/Conference/Area_Chairs/-/Proposed_Assignment',
#             readers = [conference.id, f'NeurIPS.cc/2023/Conference/Paper{submissions[4].number}/Senior_Area_Chairs', '~Area_GoogleChair1'],
#             writers = [conference.id, f'NeurIPS.cc/2023/Conference/Paper{submissions[4].number}/Senior_Area_Chairs'],
#             nonreaders = [f'NeurIPS.cc/2023/Conference/Paper{submissions[4].number}/Authors'],
#             signatures = [conference.id],
#             head = submissions[4].id,
#             tail = '~Area_GoogleChair1',
#             label = 'ac-matching',
#             weight = 0.94
#         ))


#         ## Deploy assignments
#         with pytest.raises(openreview.OpenReviewException, match=r'AC assignments must be deployed first'):
#             conference.set_assignments(assignment_title='sac-matching', committee_id='NeurIPS.cc/2023/Conference/Senior_Area_Chairs', overwrite=True)

#         conference.set_assignments(assignment_title='ac-matching', committee_id='NeurIPS.cc/2023/Conference/Area_Chairs', overwrite=True)
#         conference.set_assignments(assignment_title='sac-matching', committee_id='NeurIPS.cc/2023/Conference/Senior_Area_Chairs', overwrite=True)

#         helpers.await_queue()

#         assert ['~Area_IBMChair1'] == pc_client.get_group('NeurIPS.cc/2023/Conference/Paper5/Area_Chairs').members
#         assert ['~Area_IBMChair1'] ==  pc_client.get_group('NeurIPS.cc/2023/Conference/Paper4/Area_Chairs').members
#         assert ['~Area_UMassChair1'] ==  pc_client.get_group('NeurIPS.cc/2023/Conference/Paper3/Area_Chairs').members
#         assert ['~Area_GoogleChair1'] == pc_client.get_group('NeurIPS.cc/2023/Conference/Paper2/Area_Chairs').members
#         assert ['~Area_GoogleChair1'] == pc_client.get_group('NeurIPS.cc/2023/Conference/Paper1/Area_Chairs').members

#         assert pc_client.get_edges_count(invitation='NeurIPS.cc/2023/Conference/Area_Chairs/-/Assignment') == 5

#         assert ['~SeniorArea_GoogleChair1'] == pc_client.get_group('NeurIPS.cc/2023/Conference/Paper5/Senior_Area_Chairs').members
#         assert ['~SeniorArea_GoogleChair1'] == pc_client.get_group('NeurIPS.cc/2023/Conference/Paper4/Senior_Area_Chairs').members
#         assert ['~SeniorArea_GoogleChair1'] == pc_client.get_group('NeurIPS.cc/2023/Conference/Paper3/Senior_Area_Chairs').members
#         assert ['~SeniorArea_NeurIPSChair1'] == pc_client.get_group('NeurIPS.cc/2023/Conference/Paper2/Senior_Area_Chairs').members
#         assert ['~SeniorArea_NeurIPSChair1'] == pc_client.get_group('NeurIPS.cc/2023/Conference/Paper1/Senior_Area_Chairs').members

#         assert pc_client.get_edges_count(invitation='NeurIPS.cc/2023/Conference/Senior_Area_Chairs/-/Assignment') == 3

#         ## Check if the SAC can edit the AC assignments
#         post_submission_note=pc_client.post_note(openreview.Note(
#             content= {
#                 'force': 'Yes',
#                 'hide_fields': ['keywords'],
#                 'submission_readers': 'Assigned program committee (assigned reviewers, assigned area chairs, assigned senior area chairs if applicable)'
#             },
#             forum= request_form.id,
#             invitation= f'openreview.net/Support/-/Request{request_form.number}/Post_Submission',
#             readers= ['NeurIPS.cc/2023/Conference/Program_Chairs', 'openreview.net/Support'],
#             referent= request_form.id,
#             replyto= request_form.id,
#             signatures= ['~Program_NeurIPSChair1'],
#             writers= [],
#         ))

#         helpers.await_queue()        
#         print('http://localhost:3030/edges/browse?traverse=NeurIPS.cc/2023/Conference/Area_Chairs/-/Assignment&edit=NeurIPS.cc/2023/Conference/Area_Chairs/-/Assignment&browse=NeurIPS.cc/2023/Conference/Area_Chairs/-/Affinity_Score&hide=NeurIPS.cc/2023/Conference/Area_Chairs/-/Conflict&maxColumns=2')
#         #assert False

#         ## Reviewer assignments
#         # Paper 5
#         helpers.create_reviewer_edge(client, conference, 'Proposed_Assignment', submissions[0], '~Reviewer_UMass1', label='reviewer-matching', weight=None)
#         helpers.create_reviewer_edge(client, conference, 'Proposed_Assignment', submissions[0], '~Reviewer_Google1', label='reviewer-matching', weight=None)
#         helpers.create_reviewer_edge(client, conference, 'Aggregate_Score', submissions[0], '~Reviewer_UMass1', label='reviewer-matching', weight=0.98)
#         helpers.create_reviewer_edge(client, conference, 'Aggregate_Score', submissions[0], '~Reviewer_MIT1', label='reviewer-matching', weight=0.87)
#         helpers.create_reviewer_edge(client, conference, 'Aggregate_Score', submissions[0], '~Reviewer_IBM1', label='reviewer-matching', weight=0.56)
#         helpers.create_reviewer_edge(client, conference, 'Aggregate_Score', submissions[0], '~Reviewer_Facebook1', label='reviewer-matching', weight=0.45)
#         helpers.create_reviewer_edge(client, conference, 'Aggregate_Score', submissions[0], '~Reviewer_Google1', label='reviewer-matching', weight=0.33)

#         # Paper 4
#         helpers.create_reviewer_edge(client, conference, 'Proposed_Assignment', submissions[1], '~Reviewer_UMass1', label='reviewer-matching', weight=None)
#         helpers.create_reviewer_edge(client, conference, 'Proposed_Assignment', submissions[1], '~Reviewer_Facebook1', label='reviewer-matching', weight=None)
#         helpers.create_reviewer_edge(client, conference, 'Aggregate_Score', submissions[1], '~Reviewer_UMass1', label='reviewer-matching', weight=0.98)
#         helpers.create_reviewer_edge(client, conference, 'Aggregate_Score', submissions[1], '~Reviewer_MIT1', label='reviewer-matching', weight=0.87)
#         helpers.create_reviewer_edge(client, conference, 'Aggregate_Score', submissions[1], '~Reviewer_IBM1', label='reviewer-matching', weight=0.56)
#         helpers.create_reviewer_edge(client, conference, 'Aggregate_Score', submissions[1], '~Reviewer_Facebook1', label='reviewer-matching', weight=0.89)
#         helpers.create_reviewer_edge(client, conference, 'Aggregate_Score', submissions[1], '~Reviewer_Google1', label='reviewer-matching', weight=0.33)

#         # Paper 3
#         helpers.create_reviewer_edge(client, conference, 'Proposed_Assignment', submissions[2], '~Reviewer_UMass1', label='reviewer-matching', weight=None)
#         helpers.create_reviewer_edge(client, conference, 'Proposed_Assignment', submissions[2], '~Reviewer_Google1', label='reviewer-matching', weight=None)
#         helpers.create_reviewer_edge(client, conference, 'Aggregate_Score', submissions[2], '~Reviewer_UMass1', label='reviewer-matching', weight=0.33)
#         helpers.create_reviewer_edge(client, conference, 'Aggregate_Score', submissions[2], '~Reviewer_MIT1', label='reviewer-matching', weight=0.87)
#         helpers.create_reviewer_edge(client, conference, 'Aggregate_Score', submissions[2], '~Reviewer_IBM1', label='reviewer-matching', weight=0.56)
#         helpers.create_reviewer_edge(client, conference, 'Aggregate_Score', submissions[2], '~Reviewer_Facebook1', label='reviewer-matching', weight=0.89)
#         helpers.create_reviewer_edge(client, conference, 'Aggregate_Score', submissions[2], '~Reviewer_Google1', label='reviewer-matching', weight=0.98)

#         # Paper 4
#         helpers.create_reviewer_edge(client, conference, 'Proposed_Assignment', submissions[3], '~Reviewer_Facebook1', label='reviewer-matching', weight=None)
#         helpers.create_reviewer_edge(client, conference, 'Proposed_Assignment', submissions[3], '~Reviewer_IBM1', label='reviewer-matching', weight=None)
#         helpers.create_reviewer_edge(client, conference, 'Aggregate_Score', submissions[3], '~Reviewer_UMass1', label='reviewer-matching', weight=0.33)
#         helpers.create_reviewer_edge(client, conference, 'Aggregate_Score', submissions[3], '~Reviewer_MIT1', label='reviewer-matching', weight=0.87)
#         helpers.create_reviewer_edge(client, conference, 'Aggregate_Score', submissions[3], '~Reviewer_IBM1', label='reviewer-matching', weight=0.56)
#         helpers.create_reviewer_edge(client, conference, 'Aggregate_Score', submissions[3], '~Reviewer_Facebook1', label='reviewer-matching', weight=0.89)
#         helpers.create_reviewer_edge(client, conference, 'Aggregate_Score', submissions[3], '~Reviewer_Google1', label='reviewer-matching', weight=0.98)

#         # Paper 1
#         helpers.create_reviewer_edge(client, conference, 'Proposed_Assignment', submissions[4], '~Reviewer_UMass1', label='reviewer-matching', weight=None)
#         helpers.create_reviewer_edge(client, conference, 'Proposed_Assignment', submissions[4], '~Reviewer_MIT1', label='reviewer-matching', weight=None)
#         helpers.create_reviewer_edge(client, conference, 'Aggregate_Score', submissions[4], '~Reviewer_UMass1', label='reviewer-matching', weight=0.33)
#         helpers.create_reviewer_edge(client, conference, 'Aggregate_Score', submissions[4], '~Reviewer_MIT1', label='reviewer-matching', weight=0.87)
#         helpers.create_reviewer_edge(client, conference, 'Aggregate_Score', submissions[4], '~Reviewer_IBM1', label='reviewer-matching', weight=0.56)
#         helpers.create_reviewer_edge(client, conference, 'Aggregate_Score', submissions[4], '~Reviewer_Facebook1', label='reviewer-matching', weight=0.89)
#         helpers.create_reviewer_edge(client, conference, 'Aggregate_Score', submissions[4], '~Reviewer_Google1', label='reviewer-matching', weight=0.98)

#         # start='NeurIPS.cc/2023/Conference/Area_Chairs/-/Proposed_Assignment,label:ac-matching,tail:~Area_IBMChair1'
#         # traverse='NeurIPS.cc/2023/Conference/Reviewers/-/Proposed_Assignment,label:reviewer-matching'
#         # browse='NeurIPS.cc/2023/Conference/Reviewers/-/Aggregate_Score,label:reviewer-matching;NeurIPS.cc/2023/Conference/Reviewers/-/Affinity_Score;NeurIPS.cc/2023/Conference/Reviewers/-/Conflict'
#         # hide='NeurIPS.cc/2023/Conference/Reviewers/-/Conflict'
#         # url=f'http://localhost:3030/edges/browse?start={start}&traverse={traverse}&edit={traverse}&browse={browse}&maxColumns=2'

#         # print(url)
#         # assert False

#     def test_ac_reassignment(self, conference, helpers, client):

#         pc_client=openreview.Client(username='pc@neurips.cc', password=helpers.strong_password)
#         submissions=conference.get_submissions(sort='tmdate')

#         assert pc_client.get_edges_count(invitation='NeurIPS.cc/2023/Conference/Senior_Area_Chairs/-/Assignment') == 3
#         assert pc_client.get_edges_count(invitation='NeurIPS.cc/2023/Conference/Area_Chairs/-/Assignment') == 5

#         ac_assignment = pc_client.get_edges(invitation='NeurIPS.cc/2023/Conference/Area_Chairs/-/Assignment', head=submissions[0].id)[0]

#         ## Remove AC assignment
#         ac_assignment.ddate = openreview.tools.datetime_millis(datetime.datetime.utcnow())
#         pc_client.post_edge(ac_assignment)

#         helpers.await_queue()

#         assert pc_client.get_edges_count(invitation='NeurIPS.cc/2023/Conference/Senior_Area_Chairs/-/Assignment') == 3
#         assert pc_client.get_edges_count(invitation='NeurIPS.cc/2023/Conference/Area_Chairs/-/Assignment') == 4

#         assert [] == pc_client.get_group('NeurIPS.cc/2023/Conference/Paper5/Area_Chairs').members
#         assert [] == pc_client.get_group('NeurIPS.cc/2023/Conference/Paper5/Senior_Area_Chairs').members

#         ## Add AC assignment
#         ac_assignment.ddate = None
#         pc_client.post_edge(ac_assignment)

#         helpers.await_queue()

#         assert pc_client.get_edges_count(invitation='NeurIPS.cc/2023/Conference/Senior_Area_Chairs/-/Assignment') == 3
#         assert pc_client.get_edges_count(invitation='NeurIPS.cc/2023/Conference/Area_Chairs/-/Assignment') == 5

#         assert ['~Area_IBMChair1'] == pc_client.get_group('NeurIPS.cc/2023/Conference/Paper5/Area_Chairs').members
#         assert ['~SeniorArea_GoogleChair1'] == pc_client.get_group('NeurIPS.cc/2023/Conference/Paper5/Senior_Area_Chairs').members

#         sac_assignment = pc_client.get_edges(invitation='NeurIPS.cc/2023/Conference/Senior_Area_Chairs/-/Assignment', head='~Area_IBMChair1')[0]
#         assert sac_assignment.tail == '~SeniorArea_GoogleChair1'

#         ## Add SAC assignment
#         sac_assignment.ddate = openreview.tools.datetime_millis(datetime.datetime.utcnow())
#         pc_client.post_edge(sac_assignment)

#         helpers.await_queue()

#         assert pc_client.get_edges_count(invitation='NeurIPS.cc/2023/Conference/Senior_Area_Chairs/-/Assignment') == 2
#         assert pc_client.get_edges_count(invitation='NeurIPS.cc/2023/Conference/Area_Chairs/-/Assignment') == 5

#         assert ['~Area_IBMChair1'] == pc_client.get_group('NeurIPS.cc/2023/Conference/Paper5/Area_Chairs').members
#         assert [] == pc_client.get_group('NeurIPS.cc/2023/Conference/Paper5/Senior_Area_Chairs').members

#         assert ['~Area_IBMChair1'] == pc_client.get_group('NeurIPS.cc/2023/Conference/Paper4/Area_Chairs').members
#         assert [] == pc_client.get_group('NeurIPS.cc/2023/Conference/Paper4/Senior_Area_Chairs').members

#         ## Add SAC assignment
#         sac_assignment.ddate = None
#         pc_client.post_edge(sac_assignment)

#         helpers.await_queue()

#         assert pc_client.get_edges_count(invitation='NeurIPS.cc/2023/Conference/Senior_Area_Chairs/-/Assignment') == 3
#         assert pc_client.get_edges_count(invitation='NeurIPS.cc/2023/Conference/Area_Chairs/-/Assignment') == 5

#         assert ['~Area_IBMChair1'] == pc_client.get_group('NeurIPS.cc/2023/Conference/Paper5/Area_Chairs').members
#         assert ['~SeniorArea_GoogleChair1'] == pc_client.get_group('NeurIPS.cc/2023/Conference/Paper5/Senior_Area_Chairs').members

#         assert ['~Area_IBMChair1'] == pc_client.get_group('NeurIPS.cc/2023/Conference/Paper4/Area_Chairs').members
#         assert ['~SeniorArea_GoogleChair1'] == pc_client.get_group('NeurIPS.cc/2023/Conference/Paper4/Senior_Area_Chairs').members


#     def test_reassignment_stage(self, conference, helpers, client, selenium, request_page):

#         now = datetime.datetime.utcnow()
#         pc_client=openreview.Client(username='pc@neurips.cc', password=helpers.strong_password)
#         email_template='''
# As an Area Chair for NeurIPS 2023, I'd like to ask for your expert review of a submission, titled: {title}:

# {abstract}

# If you accept, you will not be added to the general list of NeurIPS reviewers and will not be assigned additional submissions unless you explicitly agree to review them.

# To respond this request, please follow this link: {invitation_url}

# If you accept, I would need the review by Friday, July 16.

# If you don’t have an OpenReview account, you will be asked to create one using the email address at which you received this message.  Once you sign up, you will receive a separate email with instructions for accessing the paper within a few days.

# I really hope you can help out with reviewing this paper!

# Thank you,
# {inviter_id}
# {inviter_name}({inviter_email})
#         '''

#         conference.setup_assignment_recruitment(conference.get_reviewers_id(), '12345678', now + datetime.timedelta(days=3), assignment_title='reviewer-matching', invitation_labels={ 'Invite': 'Invitation Sent', 'Invited': 'Invitation Sent' }, email_template=email_template)

#         start='NeurIPS.cc/2023/Conference/Area_Chairs/-/Assignment,tail:~Area_IBMChair1'
#         traverse='NeurIPS.cc/2023/Conference/Reviewers/-/Proposed_Assignment,label:reviewer-matching'
#         edit='NeurIPS.cc/2023/Conference/Reviewers/-/Proposed_Assignment,label:reviewer-matching;NeurIPS.cc/2023/Conference/Reviewers/-/Invite_Assignment;NeurIPS.cc/2023/Conference/Reviewers/-/Custom_Max_Papers,head:ignore'
#         browse='NeurIPS.cc/2023/Conference/Reviewers/-/Aggregate_Score,label:reviewer-matching;NeurIPS.cc/2023/Conference/Reviewers/-/Affinity_Score;NeurIPS.cc/2023/Conference/Reviewers/-/Conflict'
#         hide='NeurIPS.cc/2023/Conference/Reviewers/-/Conflict'
#         url=f'http://localhost:3030/edges/browse?start={start}&traverse={traverse}&edit={edit}&browse={browse}&maxColumns=2'

#         print(url)

#         ac_client=openreview.Client(username='ac1@mit.edu', password=helpers.strong_password)
#         submission=conference.get_submissions(sort='tmdate')[0]
#         signatory_group=ac_client.get_groups(regex='NeurIPS.cc/2023/Conference/Paper5/Area_Chair_')[0]

#         ## Invite external reviewer 1
#         posted_edge=ac_client.post_edge(openreview.Edge(
#             invitation='NeurIPS.cc/2023/Conference/Reviewers/-/Invite_Assignment',
#             readers = [conference.id, 'NeurIPS.cc/2023/Conference/Paper5/Senior_Area_Chairs', 'NeurIPS.cc/2023/Conference/Paper5/Area_Chairs', 'external_reviewer1@amazon.com'],
#             nonreaders = ['NeurIPS.cc/2023/Conference/Paper5/Authors'],
#             writers = [conference.id],
#             signatures = [signatory_group.id],
#             head = submission.id,
#             tail = 'external_reviewer1@amazon.com',
#             label = 'Invitation Sent'
#         ))

#         helpers.await_queue()

#         process_logs = client.get_process_logs(id=posted_edge.id)
#         assert len(process_logs) == 1
#         assert process_logs[0]['status'] == 'ok'

#         ## External reviewer is invited
#         invite_edges=pc_client.get_edges(invitation='NeurIPS.cc/2023/Conference/Reviewers/-/Invite_Assignment', head=submission.id)
#         assert len(invite_edges) == 1
#         assert invite_edges[0].tail == '~External_Reviewer_Amazon1'
#         assert invite_edges[0].label == 'Invitation Sent'

#         assert client.get_groups('NeurIPS.cc/2023/Conference/Paper5/External_Reviewers/Invited', member='~External_Reviewer_Amazon1')
#         assert client.get_groups('NeurIPS.cc/2023/Conference/External_Reviewers/Invited', member='~External_Reviewer_Amazon1')

#         assert not client.get_groups('NeurIPS.cc/2023/Conference/Paper5/External_Reviewers', member='~External_Reviewer_Amazon1')
#         assert not client.get_groups('NeurIPS.cc/2023/Conference/External_Reviewers', member='~External_Reviewer_Amazon1')
#         assert not client.get_groups('NeurIPS.cc/2023/Conference/Reviewers', member='~External_Reviewer_Amazon1')

#         ## External reviewer accepts the invitation
#         messages = client.get_messages(to='external_reviewer1@amazon.com', subject='[NeurIPS 2023] Invitation to review paper titled Paper title 5')
#         assert messages and len(messages) == 1
#         invitation_message=messages[0]['content']['text']

#         invalid_accept_url = re.search('https://.*\n', messages[0]['content']['text']).group(0).replace('https://openreview.net', 'http://localhost:3030').replace('&amp;', '&')[:-1].replace('user=~External_Reviewer_Amazon1', 'user=~External_Reviewer_Amazon2').replace('&amp;', '&')
#         helpers.respond_invitation(selenium, request_page, invalid_accept_url, accept=True)
#         error_message = selenium.find_element_by_class_name('important_message')
#         assert 'Wrong key, please refer back to the recruitment email' == error_message.text

#         invitation_url = re.search('https://.*\n', messages[0]['content']['text']).group(0).replace('https://openreview.net', 'http://localhost:3030').replace('&amp;', '&')[:-1]

#         helpers.respond_invitation(selenium, request_page, invitation_url, accept=True)
#         notes = selenium.find_element_by_class_name("note_editor")
#         assert notes
#         messages = notes.find_elements_by_tag_name("h4")
#         assert messages
#         assert 'Thank you for accepting this invitation from Conference on Neural Information Processing Systems.' == messages[0].text

#         helpers.await_queue()

#         process_logs = client.get_process_logs(invitation='NeurIPS.cc/2023/Conference/Reviewers/-/Proposed_Assignment_Recruitment')
#         assert len(process_logs) == 1
#         assert process_logs[0]['status'] == 'ok'

#         ## Externel reviewer is assigned to the paper 5
#         invite_edges=pc_client.get_edges(invitation='NeurIPS.cc/2023/Conference/Reviewers/-/Invite_Assignment', head=submission.id)
#         assert len(invite_edges) == 1
#         assert invite_edges[0].tail == '~External_Reviewer_Amazon1'
#         assert invite_edges[0].label == 'Accepted'

#         assert client.get_groups('NeurIPS.cc/2023/Conference/Paper5/External_Reviewers/Invited', member='~External_Reviewer_Amazon1')
#         assert client.get_groups('NeurIPS.cc/2023/Conference/External_Reviewers/Invited', member='~External_Reviewer_Amazon1')

#         assert client.get_groups('NeurIPS.cc/2023/Conference/Paper5/External_Reviewers', member='~External_Reviewer_Amazon1')
#         assert client.get_groups('NeurIPS.cc/2023/Conference/External_Reviewers', member='~External_Reviewer_Amazon1')
#         assert not client.get_groups('NeurIPS.cc/2023/Conference/Reviewers', member='~External_Reviewer_Amazon1')

#         assignment_edges=pc_client.get_edges(invitation='NeurIPS.cc/2023/Conference/Reviewers/-/Proposed_Assignment', label='reviewer-matching', head=submission.id)
#         assert len(assignment_edges) == 3
#         assert '~External_Reviewer_Amazon1' in [e.tail for e in assignment_edges]

#         # Confirmation email to the reviewer
#         messages = client.get_messages(to='external_reviewer1@amazon.com', subject='[NeurIPS 2023] Reviewer Invitation accepted for paper 5')
#         assert messages and len(messages) == 1
#         assert messages[0]['content']['text'] == '''Hi External Reviewer Amazon,
# Thank you for accepting the invitation to review the paper number: 5, title: Paper title 5.

# The NeurIPS 2023 program chairs will be contacting you with more information regarding next steps soon. In the meantime, please add noreply@openreview.net to your email contacts to ensure that you receive all communications.

# If you would like to change your decision, please follow the link in the previous invitation email and click on the "Decline" button.

# OpenReview Team'''

#         # Confirmation email to the ac
#         messages = client.get_messages(to='ac1@mit.edu', subject='[NeurIPS 2023] Reviewer External Reviewer Amazon accepted to review paper 5')
#         assert messages and len(messages) == 1
#         assert messages[0]['content']['text'] == '''Hi Area IBMChair,
# The Reviewer External Reviewer Amazon(external_reviewer1@amazon.com) that you invited to review paper 5 has accepted the invitation and is now assigned to the paper 5.

# OpenReview Team'''


#         ## External reviewer declines the invitation, assignment rollback
#         invitation_url = re.search('https://.*\n', invitation_message).group(0).replace('https://openreview.net', 'http://localhost:3030').replace('&amp;', '&')[:-1]
#         helpers.respond_invitation(selenium, request_page, invitation_url, accept=False)
#         notes = selenium.find_element_by_class_name("note_editor")
#         assert notes
#         messages = notes.find_elements_by_tag_name("h4")
#         assert messages
#         assert 'You have declined the invitation from Conference on Neural Information Processing Systems.' == messages[0].text

#         helpers.await_queue()

#         process_logs = client.get_process_logs(invitation='NeurIPS.cc/2023/Conference/Reviewers/-/Proposed_Assignment_Recruitment')
#         assert len(process_logs) == 2
#         assert process_logs[0]['status'] == 'ok'
#         assert process_logs[1]['status'] == 'ok'

#         ## Externel reviewer is not assigned to the paper 5
#         invite_edges=pc_client.get_edges(invitation='NeurIPS.cc/2023/Conference/Reviewers/-/Invite_Assignment', head=submission.id)
#         assert len(invite_edges) == 1
#         assert invite_edges[0].tail == '~External_Reviewer_Amazon1'
#         assert invite_edges[0].label == 'Declined'

#         assignment_edges=pc_client.get_edges(invitation='NeurIPS.cc/2023/Conference/Reviewers/-/Proposed_Assignment', label='reviewer-matching', head=submission.id)
#         assert len(assignment_edges) == 2
#         assert '~External_Reviewer_Amazon1' not in [e.tail for e in assignment_edges]

#         messages = client.get_messages(to='external_reviewer1@amazon.com', subject='[NeurIPS 2023] Reviewer Invitation declined for paper 5')
#         assert messages and len(messages) == 1
#         assert messages[0]['content']['text'] == '''Hi External Reviewer Amazon,
# You have declined the invitation to review the paper number: 5, title: Paper title 5.

# If you would like to change your decision, please follow the link in the previous invitation email and click on the "Accept" button.

# OpenReview Team'''

#         response_note=client.get_notes(invitation='NeurIPS.cc/2023/Conference/Reviewers/-/Proposed_Assignment_Recruitment', content={ 'submission_id': submission.id, 'user': '~External_Reviewer_Amazon1', 'response': 'No'})[0]
#         messages = client.get_messages(to='ac1@mit.edu', subject='[NeurIPS 2023] Reviewer External Reviewer Amazon declined to review paper 5')
#         assert messages and len(messages) == 1
#         assert messages[0]['content']['text'] == f'''Hi Area IBMChair,
# The Reviewer External Reviewer Amazon(external_reviewer1@amazon.com) that you invited to review paper 5 has declined the invitation.

# To read their response, please click here: https://openreview.net/forum?id={response_note.id}

# OpenReview Team'''

#         assert client.get_groups('NeurIPS.cc/2023/Conference/Paper5/External_Reviewers/Invited', member='~External_Reviewer_Amazon1')
#         assert client.get_groups('NeurIPS.cc/2023/Conference/External_Reviewers/Invited', member='~External_Reviewer_Amazon1')

#         assert not client.get_groups('NeurIPS.cc/2023/Conference/Paper5/External_Reviewers', member='~External_Reviewer_Amazon1')
#         assert client.get_groups('NeurIPS.cc/2023/Conference/External_Reviewers', member='~External_Reviewer_Amazon1')
#         assert not client.get_groups('NeurIPS.cc/2023/Conference/Reviewers', member='~External_Reviewer_Amazon1')


#         ## External reviewer accepts the invitation again
#         invitation_url = re.search('https://.*\n', invitation_message).group(0).replace('https://openreview.net', 'http://localhost:3030').replace('&amp;', '&')[:-1]
#         helpers.respond_invitation(selenium, request_page, invitation_url, accept=True)
#         notes = selenium.find_element_by_class_name("note_editor")
#         assert notes
#         messages = notes.find_elements_by_tag_name("h4")
#         assert messages
#         assert 'Thank you for accepting this invitation from Conference on Neural Information Processing Systems.' == messages[0].text

#         helpers.await_queue()

#         process_logs = client.get_process_logs(invitation='NeurIPS.cc/2023/Conference/Reviewers/-/Proposed_Assignment_Recruitment')
#         assert len(process_logs) == 3
#         assert process_logs[0]['status'] == 'ok'
#         assert process_logs[1]['status'] == 'ok'
#         assert process_logs[2]['status'] == 'ok'

#         ## Externel reviewer is assigned to the paper 5
#         invite_edges=pc_client.get_edges(invitation='NeurIPS.cc/2023/Conference/Reviewers/-/Invite_Assignment', head=submission.id)
#         assert len(invite_edges) == 1
#         assert invite_edges[0].tail == '~External_Reviewer_Amazon1'
#         assert invite_edges[0].label == 'Accepted'

#         assignment_edges=pc_client.get_edges(invitation='NeurIPS.cc/2023/Conference/Reviewers/-/Proposed_Assignment', label='reviewer-matching', head=submission.id)
#         assert len(assignment_edges) == 3
#         assert '~External_Reviewer_Amazon1' in [e.tail for e in assignment_edges]

#         messages = client.get_messages(to='external_reviewer1@amazon.com', subject='[NeurIPS 2023] Reviewer Invitation accepted for paper 5')
#         assert messages and len(messages) == 2

#         assert client.get_groups('NeurIPS.cc/2023/Conference/Paper5/External_Reviewers/Invited', member='~External_Reviewer_Amazon1')
#         assert client.get_groups('NeurIPS.cc/2023/Conference/External_Reviewers/Invited', member='~External_Reviewer_Amazon1')

#         assert client.get_groups('NeurIPS.cc/2023/Conference/Paper5/External_Reviewers', member='~External_Reviewer_Amazon1')
#         assert client.get_groups('NeurIPS.cc/2023/Conference/External_Reviewers', member='~External_Reviewer_Amazon1')
#         assert not client.get_groups('NeurIPS.cc/2023/Conference/Reviewers', member='~External_Reviewer_Amazon1')

#         ## Invite external reviewer 2
#         with pytest.raises(openreview.OpenReviewException, match=r'Conflict detected for External Reviewer MIT'):
#             posted_edge=ac_client.post_edge(openreview.Edge(
#                 invitation='NeurIPS.cc/2023/Conference/Reviewers/-/Invite_Assignment',
#                 readers = [conference.id, 'NeurIPS.cc/2023/Conference/Paper5/Senior_Area_Chairs', 'NeurIPS.cc/2023/Conference/Paper5/Area_Chairs', 'external_reviewer2@mit.edu'],
#                 nonreaders = ['NeurIPS.cc/2023/Conference/Paper5/Authors'],
#                 writers = [conference.id],
#                 signatures = [signatory_group.id],
#                 head = submission.id,
#                 tail = 'external_reviewer2@mit.edu',
#                 label = 'Invitation Sent'
#             ))

#         ## Invite external reviewer 3
#         posted_edge=ac_client.post_edge(openreview.Edge(
#             invitation='NeurIPS.cc/2023/Conference/Reviewers/-/Invite_Assignment',
#             readers = [conference.id, 'NeurIPS.cc/2023/Conference/Paper5/Senior_Area_Chairs', 'NeurIPS.cc/2023/Conference/Paper5/Area_Chairs', 'external_reviewer3@adobe.com'],
#             nonreaders = ['NeurIPS.cc/2023/Conference/Paper5/Authors'],
#             writers = [conference.id],
#             signatures = [signatory_group.id],
#             head = submission.id,
#             tail = 'external_reviewer3@adobe.com',
#             label = 'Invitation Sent'
#         ))

#         helpers.await_queue()

#         process_logs = client.get_process_logs(id=posted_edge.id)
#         assert len(process_logs) == 1
#         assert process_logs[0]['status'] == 'ok'

#         ## External reviewer is invited
#         invite_edges=pc_client.get_edges(invitation='NeurIPS.cc/2023/Conference/Reviewers/-/Invite_Assignment', head=submission.id, tail='~External_Reviewer_Adobe1')
#         assert len(invite_edges) == 1
#         assert invite_edges[0].tail == '~External_Reviewer_Adobe1'
#         assert invite_edges[0].label == 'Invitation Sent'

#         assert client.get_groups('NeurIPS.cc/2023/Conference/Paper5/External_Reviewers/Invited', member='~External_Reviewer_Adobe1')
#         assert client.get_groups('NeurIPS.cc/2023/Conference/External_Reviewers/Invited', member='~External_Reviewer_Adobe1')

#         assert not client.get_groups('NeurIPS.cc/2023/Conference/Paper5/External_Reviewers', member='~External_Reviewer_Adobe1')
#         assert not client.get_groups('NeurIPS.cc/2023/Conference/External_Reviewers', member='~External_Reviewer_Adobe1')
#         assert not client.get_groups('NeurIPS.cc/2023/Conference/Reviewers', member='~External_Reviewer_Adobe1')

#         ## External reviewer declines the invitation
#         messages = client.get_messages(to='external_reviewer3@adobe.com', subject='[NeurIPS 2023] Invitation to review paper titled Paper title 5')
#         assert messages and len(messages) == 1
#         invitation_url = re.search('https://.*\n', messages[0]['content']['text']).group(0).replace('https://openreview.net', 'http://localhost:3030').replace('&amp;', '&')[:-1]
#         helpers.respond_invitation(selenium, request_page, invitation_url, accept=False)
#         notes = selenium.find_element_by_class_name("note_editor")
#         assert notes
#         messages = notes.find_elements_by_tag_name("h4")
#         assert messages
#         assert 'You have declined the invitation from Conference on Neural Information Processing Systems.' == messages[0].text

#         helpers.await_queue()

#         process_logs = client.get_process_logs(invitation='NeurIPS.cc/2023/Conference/Reviewers/-/Proposed_Assignment_Recruitment')
#         assert len(process_logs) == 4
#         assert process_logs[0]['status'] == 'ok'

#         invite_edges=pc_client.get_edges(invitation='NeurIPS.cc/2023/Conference/Reviewers/-/Invite_Assignment', head=submission.id, tail='~External_Reviewer_Adobe1')
#         assert len(invite_edges) == 1
#         assert invite_edges[0].label == 'Declined'

#         assignment_edges=pc_client.get_edges(invitation='NeurIPS.cc/2023/Conference/Reviewers/-/Proposed_Assignment', label='reviewer-matching', head=submission.id)
#         assert len(assignment_edges) == 3

#         messages = client.get_messages(to='external_reviewer3@adobe.com', subject='[NeurIPS 2023] Reviewer Invitation declined for paper 5')
#         assert messages and len(messages) == 1
#         assert messages[0]['content']['text'] == '''Hi External Reviewer Adobe,
# You have declined the invitation to review the paper number: 5, title: Paper title 5.

# If you would like to change your decision, please follow the link in the previous invitation email and click on the "Accept" button.

# OpenReview Team'''

#         assert client.get_groups('NeurIPS.cc/2023/Conference/Paper5/External_Reviewers/Invited', member='~External_Reviewer_Adobe1')
#         assert client.get_groups('NeurIPS.cc/2023/Conference/External_Reviewers/Invited', member='~External_Reviewer_Adobe1')

#         assert not client.get_groups('NeurIPS.cc/2023/Conference/Paper5/External_Reviewers', member='~External_Reviewer_Adobe1')
#         assert not client.get_groups('NeurIPS.cc/2023/Conference/External_Reviewers', member='~External_Reviewer_Adobe1')
#         assert not client.get_groups('NeurIPS.cc/2023/Conference/Reviewers', member='~External_Reviewer_Adobe1')

#         ## Invite external reviewer 4 with no profile
#         posted_edge=ac_client.post_edge(openreview.Edge(
#             invitation='NeurIPS.cc/2023/Conference/Reviewers/-/Invite_Assignment',
#             readers = [conference.id, 'NeurIPS.cc/2023/Conference/Paper5/Senior_Area_Chairs', 'NeurIPS.cc/2023/Conference/Paper5/Area_Chairs', 'external_reviewer4@gmail.com'],
#             nonreaders = ['NeurIPS.cc/2023/Conference/Paper5/Authors'],
#             writers = [conference.id],
#             signatures = [signatory_group.id],
#             head = submission.id,
#             tail = 'external_reviewer4@gmail.com',
#             label = 'Invitation Sent'
#         ))

#         helpers.await_queue()

#         process_logs = client.get_process_logs(id=posted_edge.id)
#         assert len(process_logs) == 1
#         assert process_logs[0]['status'] == 'ok'

#         ## External reviewer is invited
#         invite_edges=pc_client.get_edges(invitation='NeurIPS.cc/2023/Conference/Reviewers/-/Invite_Assignment', head=submission.id, tail='external_reviewer4@gmail.com')
#         assert len(invite_edges) == 1
#         assert invite_edges[0].tail == 'external_reviewer4@gmail.com'
#         assert invite_edges[0].label == 'Invitation Sent'

#         assert client.get_groups('NeurIPS.cc/2023/Conference/Paper5/External_Reviewers/Invited', member='external_reviewer4@gmail.com')
#         assert client.get_groups('NeurIPS.cc/2023/Conference/External_Reviewers/Invited', member='external_reviewer4@gmail.com')

#         assert not client.get_groups('NeurIPS.cc/2023/Conference/Paper5/External_Reviewers', member='external_reviewer4@gmail.com')
#         assert not client.get_groups('NeurIPS.cc/2023/Conference/External_Reviewers', member='external_reviewer4@gmail.com')
#         assert not client.get_groups('NeurIPS.cc/2023/Conference/Reviewers', member='external_reviewer4@gmail.com')

#         ## External reviewer accepts the invitation
#         messages = client.get_messages(to='external_reviewer4@gmail.com', subject='[NeurIPS 2023] Invitation to review paper titled Paper title 5')
#         assert messages and len(messages) == 1
#         invitation_url = re.search('https://.*\n', messages[0]['content']['text']).group(0).replace('https://openreview.net', 'http://localhost:3030').replace('&amp;', '&')[:-1]
#         helpers.respond_invitation(selenium, request_page, invitation_url, accept=True)
#         notes = selenium.find_element_by_class_name("note_editor")
#         assert notes
#         messages = notes.find_elements_by_tag_name("h4")
#         assert messages
#         assert 'Thank you for accepting this invitation from Conference on Neural Information Processing Systems.' == messages[0].text

#         helpers.await_queue()

#         ## Externel reviewer is set pending profile creation
#         invite_edges=pc_client.get_edges(invitation='NeurIPS.cc/2023/Conference/Reviewers/-/Invite_Assignment', head=submission.id, tail='external_reviewer4@gmail.com')
#         assert len(invite_edges) == 1
#         assert invite_edges[0].label == 'Pending Sign Up'

#         assignment_edges=pc_client.get_edges(invitation='NeurIPS.cc/2023/Conference/Reviewers/-/Proposed_Assignment', label='reviewer-matching', head=submission.id)
#         assert len(assignment_edges) == 3

#         messages = client.get_messages(to='external_reviewer4@gmail.com', subject='[NeurIPS 2023] Reviewer Invitation accepted for paper 5, assignment pending')
#         assert messages and len(messages) == 1
#         assert messages[0]['content']['text'] == '''Hi external_reviewer4@gmail.com,
# Thank you for accepting the invitation to review the paper number: 5, title: Paper title 5.

# Please signup in OpenReview using the email address external_reviewer4@gmail.com and complete your profile.
# Confirmation of the assignment is pending until your profile is active and no conflicts of interest are detected.

# If you would like to change your decision, please follow the link in the previous invitation email and click on the "Decline" button.

# OpenReview Team'''

#         messages = client.get_messages(to='ac1@mit.edu', subject='[NeurIPS 2023] Reviewer external_reviewer4@gmail.com accepted to review paper 5, assignment pending')
#         assert messages and len(messages) == 1
#         assert messages[0]['content']['text'] == '''Hi Area IBMChair,
# The Reviewer external_reviewer4@gmail.com that you invited to review paper 5 has accepted the invitation.

# Confirmation of the assignment is pending until the invited reviewer creates a profile in OpenReview and no conflicts of interest are detected.

# OpenReview Team'''

#         assert client.get_groups('NeurIPS.cc/2023/Conference/Paper5/External_Reviewers/Invited', member='external_reviewer4@gmail.com')
#         assert client.get_groups('NeurIPS.cc/2023/Conference/External_Reviewers/Invited', member='external_reviewer4@gmail.com')

#         assert not client.get_groups('NeurIPS.cc/2023/Conference/Paper5/External_Reviewers', member='external_reviewer4@gmail.com')
#         assert not client.get_groups('NeurIPS.cc/2023/Conference/External_Reviewers', member='external_reviewer4@gmail.com')
#         assert not client.get_groups('NeurIPS.cc/2023/Conference/Reviewers', member='external_reviewer4@gmail.com')

#         ## External reviewer creates a profile and accepts the invitation again
#         external_reviewer=helpers.create_user('external_reviewer4@gmail.com', 'Reviewer', 'External')

#         helpers.respond_invitation(selenium, request_page, invitation_url, accept=True)
#         notes = selenium.find_element_by_class_name("note_editor")
#         assert notes
#         messages = notes.find_elements_by_tag_name("h4")
#         assert messages
#         assert 'Thank you for accepting this invitation from Conference on Neural Information Processing Systems.' == messages[0].text

#         helpers.await_queue()

#         invite_edges=pc_client.get_edges(invitation='NeurIPS.cc/2023/Conference/Reviewers/-/Invite_Assignment', head=submission.id, tail='external_reviewer4@gmail.com')
#         assert len(invite_edges) == 0
#         invite_edges=pc_client.get_edges(invitation='NeurIPS.cc/2023/Conference/Reviewers/-/Invite_Assignment', head=submission.id, tail='~Reviewer_External1')
#         assert len(invite_edges) == 1
#         assert invite_edges[0].label == 'Accepted'

#         helpers.respond_invitation(selenium, request_page, invitation_url, accept=False)

#         helpers.await_queue()

#         invite_edges=pc_client.get_edges(invitation='NeurIPS.cc/2023/Conference/Reviewers/-/Invite_Assignment', head=submission.id, tail='external_reviewer4@gmail.com')
#         assert len(invite_edges) == 0
#         invite_edges=pc_client.get_edges(invitation='NeurIPS.cc/2023/Conference/Reviewers/-/Invite_Assignment', head=submission.id, tail='~Reviewer_External1')
#         assert len(invite_edges) == 1
#         assert invite_edges[0].label == 'Declined'

#         ## Invite external reviewer 5 with no profile
#         posted_edge=ac_client.post_edge(openreview.Edge(
#             invitation='NeurIPS.cc/2023/Conference/Reviewers/-/Invite_Assignment',
#             readers = [conference.id, 'NeurIPS.cc/2023/Conference/Paper5/Senior_Area_Chairs', 'NeurIPS.cc/2023/Conference/Paper5/Area_Chairs', 'external_reviewer5@gmail.com'],
#             nonreaders = ['NeurIPS.cc/2023/Conference/Paper5/Authors'],
#             writers = [conference.id],
#             signatures = [signatory_group.id],
#             head = submission.id,
#             tail = 'external_reviewer5@gmail.com',
#             label = 'Invitation Sent'
#         ))

#         helpers.await_queue()

#         process_logs = client.get_process_logs(id=posted_edge.id)
#         assert len(process_logs) == 1
#         assert process_logs[0]['status'] == 'ok'

#         ## External reviewer is invited
#         invite_edges=pc_client.get_edges(invitation='NeurIPS.cc/2023/Conference/Reviewers/-/Invite_Assignment', head=submission.id, tail='external_reviewer5@gmail.com')
#         assert len(invite_edges) == 1
#         assert invite_edges[0].tail == 'external_reviewer5@gmail.com'
#         assert invite_edges[0].label == 'Invitation Sent'

#         ## External reviewer declines the invitation
#         messages = client.get_messages(to='external_reviewer5@gmail.com', subject='[NeurIPS 2023] Invitation to review paper titled Paper title 5')
#         assert messages and len(messages) == 1
#         invitation_url = re.search('https://.*\n', messages[0]['content']['text']).group(0).replace('https://openreview.net', 'http://localhost:3030').replace('&amp;', '&')[:-1]
#         helpers.respond_invitation(selenium, request_page, invitation_url, accept=False)
#         notes = selenium.find_element_by_class_name("note_editor")
#         assert notes
#         messages = notes.find_elements_by_tag_name("h4")
#         assert messages
#         assert 'You have declined the invitation from Conference on Neural Information Processing Systems.' == messages[0].text

#         helpers.await_queue()

#         ## Externel reviewer is set pending profile creation
#         invite_edges=pc_client.get_edges(invitation='NeurIPS.cc/2023/Conference/Reviewers/-/Invite_Assignment', head=submission.id, tail='external_reviewer5@gmail.com')
#         assert len(invite_edges) == 1
#         assert invite_edges[0].label == 'Declined'

#         assignment_edges=pc_client.get_edges(invitation='NeurIPS.cc/2023/Conference/Reviewers/-/Proposed_Assignment', label='reviewer-matching', head=submission.id)
#         assert len(assignment_edges) == 3

#         messages = client.get_messages(to='external_reviewer5@gmail.com', subject='[NeurIPS 2023] Reviewer Invitation declined for paper 5')
#         assert messages and len(messages) == 1
#         assert messages[0]['content']['text'] == '''Hi external_reviewer5@gmail.com,
# You have declined the invitation to review the paper number: 5, title: Paper title 5.

# If you would like to change your decision, please follow the link in the previous invitation email and click on the "Accept" button.

# OpenReview Team'''
#         ## Invite external reviewer with wrong tilde id
#         with pytest.raises(openreview.OpenReviewException) as openReviewError:
#             posted_edge=ac_client.post_edge(openreview.Edge(
#                 invitation='NeurIPS.cc/2023/Conference/Reviewers/-/Invite_Assignment',
#                 readers = [conference.id, 'NeurIPS.cc/2023/Conference/Paper5/Senior_Area_Chairs', 'NeurIPS.cc/2023/Conference/Paper5/Area_Chairs', '~External_Melisa1'],
#                 nonreaders = ['NeurIPS.cc/2023/Conference/Paper5/Authors'],
#                 writers = [conference.id],
#                 signatures = [signatory_group.id],
#                 head = submission.id,
#                 tail = '~External_Melisa1',
#                 label = 'Invitation Sent'
#             ))
#         assert openReviewError.value.args[0].get('name') == 'Not Found'
#         assert openReviewError.value.args[0].get('message') == '~External_Melisa1 was not found'

#         ## Invite an official reviewer and get an error
#         with pytest.raises(openreview.OpenReviewException) as openReviewError:
#             posted_edge=ac_client.post_edge(openreview.Edge(
#                 invitation='NeurIPS.cc/2023/Conference/Reviewers/-/Invite_Assignment',
#                 readers = [conference.id, 'NeurIPS.cc/2023/Conference/Paper5/Senior_Area_Chairs', 'NeurIPS.cc/2023/Conference/Paper5/Area_Chairs', 'reviewer4@fb.com'],
#                 nonreaders = ['NeurIPS.cc/2023/Conference/Paper5/Authors'],
#                 writers = [conference.id],
#                 signatures = [signatory_group.id],
#                 head = submission.id,
#                 tail = 'reviewer4@fb.com',
#                 label = 'Invitation Sent'
#             ))
#         assert openReviewError.value.args[0].get('name') == 'Error'
#         assert openReviewError.value.args[0].get('message') == 'Reviewer Reviewer Facebook is an official reviewer, please use the "Assign" button to make the assignment.'

#         ## Invite an official conflicted reviewer and get a conflict error
#         with pytest.raises(openreview.OpenReviewException, match=r'Conflict detected for Reviewer MIT'):
#             posted_edge=ac_client.post_edge(openreview.Edge(
#                 invitation='NeurIPS.cc/2023/Conference/Reviewers/-/Invite_Assignment',
#                 readers = [conference.id, 'NeurIPS.cc/2023/Conference/Paper5/Senior_Area_Chairs', 'NeurIPS.cc/2023/Conference/Paper5/Area_Chairs', 'reviewer2@mit.edu'],
#                 nonreaders = ['NeurIPS.cc/2023/Conference/Paper5/Authors'],
#                 writers = [conference.id],
#                 signatures = [signatory_group.id],
#                 head = submission.id,
#                 tail = 'reviewer2@mit.edu',
#                 label = 'Invitation Sent'
#             ))

#         ## Propose a reviewer that reached the quota
#         with pytest.raises(openreview.OpenReviewException, match=r'Max Papers allowed reached for Reviewer IBM'):
#             posted_edge=ac_client.post_edge(openreview.Edge(
#                 invitation='NeurIPS.cc/2023/Conference/Reviewers/-/Proposed_Assignment',
#                 readers = [conference.id, 'NeurIPS.cc/2023/Conference/Paper5/Senior_Area_Chairs', 'NeurIPS.cc/2023/Conference/Paper5/Area_Chairs', '~Reviewer_IBM1'],
#                 nonreaders = ['NeurIPS.cc/2023/Conference/Paper5/Authors'],
#                 writers = [conference.id, 'NeurIPS.cc/2023/Conference/Paper5/Senior_Area_Chairs', 'NeurIPS.cc/2023/Conference/Paper5/Area_Chairs'],
#                 signatures = [signatory_group.id],
#                 head = submission.id,
#                 tail = '~Reviewer_IBM1',
#                 label = 'reviewer-matching'
#             ))


#     def test_deployment_stage(self, conference, client, helpers):

#         pc_client=openreview.Client(username='pc@neurips.cc', password=helpers.strong_password)
#         submissions=conference.get_submissions(sort='tmdate')

#         conference.set_assignments(assignment_title='reviewer-matching', committee_id='NeurIPS.cc/2023/Conference/Reviewers', overwrite=True, enable_reviewer_reassignment=True)

#         helpers.await_queue()

#         paper_reviewers=pc_client.get_group('NeurIPS.cc/2023/Conference/Paper5/Reviewers').members
#         assert len(paper_reviewers) == 3
#         assert '~Reviewer_UMass1' in paper_reviewers
#         assert '~Reviewer_Google1' in paper_reviewers
#         assert '~External_Reviewer_Amazon1' in paper_reviewers

#         paper_reviewers=pc_client.get_group('NeurIPS.cc/2023/Conference/Paper4/Reviewers').members
#         assert len(paper_reviewers) == 2
#         assert '~Reviewer_UMass1' in paper_reviewers
#         assert '~Reviewer_Facebook1' in paper_reviewers

#         paper_reviewers=pc_client.get_group('NeurIPS.cc/2023/Conference/Paper3/Reviewers').members
#         assert len(paper_reviewers) == 2
#         assert '~Reviewer_UMass1' in paper_reviewers
#         assert '~Reviewer_Google1' in paper_reviewers

#         paper_reviewers=pc_client.get_group('NeurIPS.cc/2023/Conference/Paper2/Reviewers').members
#         assert len(paper_reviewers) == 2
#         assert '~Reviewer_Facebook1' in paper_reviewers
#         assert '~Reviewer_IBM1' in paper_reviewers

#         paper_reviewers=pc_client.get_group('NeurIPS.cc/2023/Conference/Paper1/Reviewers').members
#         assert len(paper_reviewers) == 2
#         assert '~Reviewer_UMass1' in paper_reviewers
#         assert '~Reviewer_MIT1' in paper_reviewers

#         assignments=pc_client.get_edges_count(invitation='NeurIPS.cc/2023/Conference/Reviewers/-/Assignment')
#         assert assignments == 11

#         assignments=pc_client.get_edges(invitation='NeurIPS.cc/2023/Conference/Reviewers/-/Assignment', tail='~Reviewer_UMass1')
#         assert len(assignments) == 4

#         assignments=pc_client.get_edges(invitation='NeurIPS.cc/2023/Conference/Reviewers/-/Assignment', tail='~Reviewer_UMass1', head=submissions[0].id)
#         assert len(assignments) == 1

#         assert assignments[0].readers == ["NeurIPS.cc/2023/Conference",
#             "NeurIPS.cc/2023/Conference/Paper5/Senior_Area_Chairs",
#             "NeurIPS.cc/2023/Conference/Paper5/Area_Chairs",
#             "~Reviewer_UMass1"]

#         assert assignments[0].writers == ["NeurIPS.cc/2023/Conference",
#             "NeurIPS.cc/2023/Conference/Paper5/Senior_Area_Chairs",
#             "NeurIPS.cc/2023/Conference/Paper5/Area_Chairs"]

#         assert client.get_groups('NeurIPS.cc/2023/Conference/Paper5/External_Reviewers/Invited', member='~External_Reviewer_Amazon1')
#         assert client.get_groups('NeurIPS.cc/2023/Conference/External_Reviewers/Invited', member='~External_Reviewer_Amazon1')
#         assert not client.get_groups('NeurIPS.cc/2023/Conference/Reviewers', member='~External_Reviewer_Amazon1')


#     def test_review_stage(self, conference, helpers, test_client, client):

#         ## make submissions visible to assigned commmittee
#         invitation = client.get_invitation('NeurIPS.cc/2023/Conference/-/Submission')
#         invitation.reply['readers'] = {
#             'values-regex': '.*'
#         }
#         client.post_invitation(invitation)

#         invitation2 = client.get_invitation('NeurIPS.cc/2023/Conference/-/Blind_Submission')
#         invitation2.reply_forum_views = [
#             {
#                 "id": "authors",
#                 "label": "Author Discussion",
#                 "filter": "readers:NeurIPS.cc/2023/Conference/Paper${note.number}/Authors"
#             },
#             {
#                 "id": "committee",
#                 "label": "Committee Discussion",
#                 "filter": "-readers:NeurIPS.cc/2023/Conference/Paper${note.number}/Authors"
#             },
#             {
#                 "id": "all",
#                 "label": "All",
#                 "filter": ""
#             }
#         ]
#         client.post_invitation(invitation2)

#         original_notes=client.get_notes(invitation='NeurIPS.cc/2023/Conference/-/Submission')
#         for note in original_notes:
#             note.readers = note.readers + [f'NeurIPS.cc/2023/Conference/Paper{note.number}/Senior_Area_Chairs']
#             client.post_note(note)

#         blind_notes=client.get_notes(invitation='NeurIPS.cc/2023/Conference/-/Blind_Submission')
#         for note in blind_notes:
#             note.content = {
#                 'authors': ['Anonymous'],
#                 'authorids': [f'NeurIPS.cc/2023/Conference/Paper{note.number}/Authors']
#             }
#             note.readers = [
#                 'NeurIPS.cc/2023/Conference',
#                 f'NeurIPS.cc/2023/Conference/Paper{note.number}/Senior_Area_Chairs',
#                 f'NeurIPS.cc/2023/Conference/Paper{note.number}/Area_Chairs',
#                 f'NeurIPS.cc/2023/Conference/Paper{note.number}/Reviewers',
#                 f'NeurIPS.cc/2023/Conference/Paper{note.number}/Authors'
#             ]
#             client.post_note(note)

#         now = datetime.datetime.utcnow()
#         due_date = now + datetime.timedelta(days=3)

#         pc_client=openreview.Client(username='pc@neurips.cc', password=helpers.strong_password)
#         request_form=pc_client.get_notes(invitation='openreview.net/Support/-/Request_Form')[0]
#         stage_note=client.post_note(openreview.Note(
#             content={
#                 'review_deadline': due_date.strftime('%Y/%m/%d'),
#                 'make_reviews_public': 'No, reviews should NOT be revealed publicly when they are posted',
#                 'release_reviews_to_authors': 'No, reviews should NOT be revealed when they are posted to the paper\'s authors',
#                 'release_reviews_to_reviewers': 'Review should not be revealed to any reviewer, except to the author of the review',
#                 'email_program_chairs_about_reviews': 'No, do not email program chairs about received reviews',
#                 'remove_review_form_options': 'title',
#                 'additional_review_form_options': {
#                     "summary_and_contributions": {
#                         "order": 1,
#                         "value-regex": "[\\S\\s]{1,200000}",
#                         "description": "Briefly summarize the paper and its contributions.",
#                         "required": True
#                     },
#                     "review": {
#                         "order": 2,
#                         "value-regex": "[\\S\\s]{1,200000}",
#                         "description": "Please provide a thorough review of the submission, including its originality, quality, clarity, and significance. See https://neurips.cc/Conferences/2023/Review-Form for guidance on questions to address in your review, and https://openreview.net/faq for how to incorporate Markdown and LaTeX into your review.",
#                         "required": True,
#                         "markdown": True
#                     },
#                     "societal_impact": {
#                         "description": "Have the authors adequately addressed the limitations and potential negative societal impact of their work? (If not, please include constructive suggestions for improvement)",
#                         "order": 3,
#                         "value-regex": "[\\S\\s]{1,200000}",
#                         "required": True
#                     },
#                     "needs_ethical_review": {
#                         "description": "Would the paper benefit from further ethical review?",
#                         "order": 4,
#                         "value-radio": [
#                             "Yes",
#                             "No"
#                         ],
#                         "required": True
#                     },
#                     "ethical_issues": {
#                         "description": "Please elaborate on the ethical issues raised by this paper and the extent to which the issues have been acknowledged or addressed.",
#                         "order": 5,
#                         "value-regex": "[\\S\\s]{1,200000}",
#                         "required": False
#                     },
#                     "ethical_expertise": {
#                         "order": 6,
#                         "values-checkbox": [
#                             "Discrimination / Bias / Fairness Concerns",
#                             "Inadequate Data and Algorithm Evaluation",
#                             "Inappropriate Potential Applications & Impact  (e.g., human rights concerns)",
#                             "Privacy and Security (e.g., consent)",
#                             "Legal Compliance (e.g., GDPR, copyright, terms of use)",
#                             "Research Integrity Issues (e.g., plagiarism)",
#                             "Responsible Research Practice (e.g., IRB, documentation, research ethics)",
#                             "I don’t know"
#                         ],
#                         "description": "What kind of expertise do you think is required to review this paper for the ethical concerns raised?. Please click all that apply.",
#                         "required": False
#                     },
#                     "previously_reviewed": {
#                         "order": 7,
#                         "value-radio": [
#                             "Yes",
#                             "No"
#                         ],
#                         "required": True,
#                         "description": "Have you previously reviewed or area chaired (a version of) this work for another archival venue?",
#                     },
#                     "reviewing_time": {
#                         "order": 8,
#                         "value-regex": ".{1,500}",
#                         "required": True,
#                         "description": "How much time did you spend reviewing this paper (in_hours)?"
#                     },
#                     "rating": {
#                         "order": 9,
#                         "value-radio": [
#                             "10: Top 5% of accepted NeurIPS papers, seminal paper",
#                             "9: Top 15% of accepted NeurIPS papers, strong accept",
#                             "8: Top 50% of accepted NeurIPS papers, clear accept",
#                             "7: Good paper, accept",
#                             "6: Marginally above the acceptance threshold",
#                             "5: Marginally below the acceptance threshold",
#                             "4: An okay paper, but not good enough; rejection",
#                             "3: Clear rejection",
#                             "2: Strong rejection",
#                             "1: Trivial or wrong"
#                         ],
#                         "description": "Please provide an \"overall score\" for this submission.",
#                         "required": True
#                     },
#                     "confidence": {
#                         "order": 10,
#                         "value-radio": [
#                             "5: You are absolutely certain about your assessment. You are very familiar with the related work and checked the math/other details carefully.",
#                             "4: You are confident in your assessment, but not absolutely certain. It is unlikely, but not impossible, that you did not understand some parts of the submission or that you are unfamiliar with some pieces of related work.",
#                             "3: You are fairly confident in your assessment. It is possible that you did not understand some parts of the submission or that you are unfamiliar with some pieces of related work. Math/other details were not carefully checked.",
#                             "2: You are willing to defend your assessment, but it is quite likely that you did not understand central parts of the submission or that you are unfamiliar with some pieces of related work. Math/other details were not carefully checked.",
#                             "1: Your assessment is an educated guess. The submission is not in your area or the submission was difficult to understand. Math/other details were not carefully checked."
#                         ],
#                         "description": "Please provide a \"confidence score\" for your assessment of this submission.",
#                         "required": True
#                     },
#                     "code_of_conduct": {
#                         "order": 11,
#                         "value-checkbox": "While performing my duties as a reviewer (including writing reviews and participating in discussions), I have and will continue to abide by the NeurIPS code of conduct (https://neurips.cc/public/CodeOfConduct).",
#                         "required": True
#                     }
#                 }
#             },
#             forum=request_form.forum,
#             invitation='openreview.net/Support/-/Request{}/Review_Stage'.format(request_form.number),
#             readers=['NeurIPS.cc/2023/Conference/Program_Chairs', 'openreview.net/Support'],
#             referent=request_form.forum,
#             replyto=request_form.forum,
#             signatures=['~Program_NeurIPSChair1'],
#             writers=[]
#         ))

#         helpers.await_queue()

#         process_logs = client.get_process_logs(id=stage_note.id)
#         assert len(process_logs) == 1
#         assert process_logs[0]['status'] == 'ok'

#         ac_group=client.get_groups(regex='NeurIPS.cc/2023/Conference/Paper5/Area_Chair_')[0]
#         assert ac_group.readers == ['NeurIPS.cc/2023/Conference',
#             'NeurIPS.cc/2023/Conference/Program_Chairs',
#             'NeurIPS.cc/2023/Conference/Paper5/Senior_Area_Chairs',
#             'NeurIPS.cc/2023/Conference/Paper5/Area_Chairs',
#             'NeurIPS.cc/2023/Conference/Paper5/Reviewers',
#             ac_group.id]

#         reviewer_group=client.get_groups(regex='NeurIPS.cc/2023/Conference/Paper5/Reviewer_')[0]
#         assert reviewer_group.readers == ['NeurIPS.cc/2023/Conference',
#             'NeurIPS.cc/2023/Conference/Program_Chairs',
#             'NeurIPS.cc/2023/Conference/Paper5/Senior_Area_Chairs',
#             'NeurIPS.cc/2023/Conference/Paper5/Area_Chairs',
#             'NeurIPS.cc/2023/Conference/Paper5/Reviewers',
#             reviewer_group.id]

#         anon_groups=client.get_groups('NeurIPS.cc/2023/Conference/Paper5/Area_Chair_.*')
#         assert len(anon_groups) == 1

#         anon_groups=client.get_groups('NeurIPS.cc/2023/Conference/Paper5/Reviewer_.*')
#         assert len(anon_groups) == 3

#         reviewer_client=openreview.Client(username='reviewer1@umass.edu', password=helpers.strong_password)

#         signatory_groups=client.get_groups(regex='NeurIPS.cc/2023/Conference/Paper5/Reviewer_', signatory='reviewer1@umass.edu')
#         assert len(signatory_groups) == 1

#         submissions=conference.get_submissions(number=5)
#         assert len(submissions) == 1

#         review_note=reviewer_client.post_note(openreview.Note(
#             invitation='NeurIPS.cc/2023/Conference/Paper5/-/Official_Review',
#             forum=submissions[0].id,
#             replyto=submissions[0].id,
#             readers=['NeurIPS.cc/2023/Conference/Program_Chairs', 'NeurIPS.cc/2023/Conference/Paper5/Senior_Area_Chairs', 'NeurIPS.cc/2023/Conference/Paper5/Area_Chairs', signatory_groups[0].id],
#             nonreaders=['NeurIPS.cc/2023/Conference/Paper5/Authors'],
#             writers=[signatory_groups[0].id],
#             signatures=[signatory_groups[0].id],
#             content={
#                 'summary_and_contributions': 'TEst data',
#                 'review': 'Paper is very good!Paper is very good!Paper is very good!Paper is very good!Paper is very good!Paper is very good!Paper is very good!Paper is very good!',
#                 'societal_impact': 'TESSSTTTTTTESSSTTTTTTESSSTTTTTTESSSTTTTTTESSSTTTTTTESSSTTTTT',
#                 'needs_ethical_review': 'No',
#                 'previously_reviewed': 'No',
#                 'reviewing_time': '3',
#                 'rating': '10: Top 5% of accepted NeurIPS papers, seminal paper',
#                 'confidence': '5: You are absolutely certain about your assessment. You are very familiar with the related work and checked the math/other details carefully.',
#                 'code_of_conduct': 'While performing my duties as a reviewer (including writing reviews and participating in discussions), I have and will continue to abide by the NeurIPS code of conduct (https://neurips.cc/public/CodeOfConduct).'
#             }
#         ))

#         helpers.await_queue()

#         process_logs = client.get_process_logs(id=review_note.id)
#         assert len(process_logs) == 1
#         assert process_logs[0]['status'] == 'ok'

#         messages = client.get_messages(to='reviewer1@umass.edu', subject='[NeurIPS 2023] Your review has been received on your assigned Paper number: 5, Paper title: \"Paper title 5\"')
#         assert messages and len(messages) == 1

#         messages = client.get_messages(to='ac1@mit.edu', subject='[NeurIPS 2023] Review posted to your assigned Paper number: 5, Paper title: \"Paper title 5\"')
#         assert messages and len(messages) == 1

#         ## TODO: should we send emails to Senior Area Chairs?

#     def test_emergency_reviewer_stage(self, conference, helpers, client, request_page, selenium):

#         now = datetime.datetime.utcnow()
#         pc_client=openreview.Client(username='pc@neurips.cc', password=helpers.strong_password)

#         start='NeurIPS.cc/2023/Conference/Area_Chairs/-/Assignment,tail:~Area_IBMChair1'
#         traverse='NeurIPS.cc/2023/Conference/Reviewers/-/Assignment'
#         edit='NeurIPS.cc/2023/Conference/Reviewers/-/Assignment;NeurIPS.cc/2023/Conference/Reviewers/-/Invite_Assignment'
#         browse='NeurIPS.cc/2023/Conference/Reviewers/-/Aggregate_Score,label:reviewer-matching;NeurIPS.cc/2023/Conference/Reviewers/-/Affinity_Score;NeurIPS.cc/2023/Conference/Reviewers/-/Conflict'
#         hide='NeurIPS.cc/2023/Conference/Reviewers/-/Conflict'
#         url=f'http://localhost:3030/edges/browse?start={start}&traverse={traverse}&edit={edit}&browse={browse}&maxColumns=2'

#         print(url)

#         ac_client=openreview.Client(username='ac1@mit.edu', password=helpers.strong_password)
#         submission=conference.get_submissions(sort='tmdate')[1]
#         signatory_group=ac_client.get_groups(regex='NeurIPS.cc/2023/Conference/Paper4/Area_Chair_')[0]

#         ## Invite external reviewer 1
#         posted_edge=ac_client.post_edge(openreview.Edge(
#             invitation='NeurIPS.cc/2023/Conference/Reviewers/-/Invite_Assignment',
#             readers = [conference.id, 'NeurIPS.cc/2023/Conference/Paper4/Senior_Area_Chairs', 'NeurIPS.cc/2023/Conference/Paper4/Area_Chairs', 'external_reviewer2@mit.edu'],
#             nonreaders = ['NeurIPS.cc/2023/Conference/Paper4/Authors'],
#             writers = [conference.id],
#             signatures = [signatory_group.id],
#             head = submission.id,
#             tail = 'external_reviewer2@mit.edu',
#             label = 'Invitation Sent'
#         ))

#         helpers.await_queue()

#         process_logs = client.get_process_logs(id=posted_edge.id)
#         assert len(process_logs) == 1
#         assert process_logs[0]['status'] == 'ok'

#         ## External reviewer is invited
#         invite_edges=pc_client.get_edges(invitation='NeurIPS.cc/2023/Conference/Reviewers/-/Invite_Assignment', head=submission.id)
#         assert len(invite_edges) == 1
#         assert invite_edges[0].tail == '~External_Reviewer_MIT1'
#         assert invite_edges[0].label == 'Invitation Sent' ## figure out how to enable this in the deployment

#         assert client.get_groups('NeurIPS.cc/2023/Conference/Emergency_Reviewers/Invited', member='~External_Reviewer_MIT1')

#         assert not client.get_groups('NeurIPS.cc/2023/Conference/Emergency_Reviewers', member='~External_Reviewer_MIT1')
#         assert not client.get_groups('NeurIPS.cc/2023/Conference/Reviewers', member='~External_Reviewer_MIT1')


#         ## External reviewer accepts the invitation
#         messages = client.get_messages(to='external_reviewer2@mit.edu', subject='[NeurIPS 2023] Invitation to review paper titled Paper title 4')
#         assert messages and len(messages) == 1
#         invitation_url = re.search('https://.*\n', messages[0]['content']['text']).group(0).replace('https://openreview.net', 'http://localhost:3030').replace('&amp;', '&')[:-1]
#         helpers.respond_invitation(selenium, request_page, invitation_url, accept=True)
#         notes = selenium.find_element_by_class_name("note_editor")
#         assert notes
#         messages = notes.find_elements_by_tag_name("h4")
#         assert messages
#         assert 'Thank you for accepting this invitation from Conference on Neural Information Processing Systems.' == messages[0].text

#         helpers.await_queue()

#         process_logs = client.get_process_logs(invitation='NeurIPS.cc/2023/Conference/Reviewers/-/Assignment_Recruitment')
#         assert len(process_logs) == 1
#         assert process_logs[0]['status'] == 'ok'

#         ## Externel reviewer is assigned to the paper 5
#         invite_edges=pc_client.get_edges(invitation='NeurIPS.cc/2023/Conference/Reviewers/-/Invite_Assignment', head=submission.id)
#         assert len(invite_edges) == 1
#         assert invite_edges[0].tail == '~External_Reviewer_MIT1'
#         assert invite_edges[0].label == 'Accepted'

#         assignment_edges=pc_client.get_edges(invitation='NeurIPS.cc/2023/Conference/Reviewers/-/Assignment', head=submission.id)
#         assert len(assignment_edges) == 3
#         assert '~External_Reviewer_MIT1' in [e.tail for e in assignment_edges]

#         assert '~External_Reviewer_MIT1' in pc_client.get_group('NeurIPS.cc/2023/Conference/Paper4/Reviewers').members

#         assert len(pc_client.get_groups(regex='NeurIPS.cc/2023/Conference/Paper4/Reviewer_', signatory='~External_Reviewer_MIT1')) == 1

#         messages = client.get_messages(to='external_reviewer2@mit.edu', subject='[NeurIPS 2023] Reviewer Invitation accepted for paper 4')
#         assert messages and len(messages) == 1
#         assert messages[0]['content']['text'] == '''Hi External Reviewer MIT,
# Thank you for accepting the invitation to review the paper number: 4, title: Paper title 4.

# Please go to the NeurIPS 2023 Reviewers Console and check your pending tasks: https://openreview.net/group?id=NeurIPS.cc/2023/Conference/Reviewers

# If you would like to change your decision, please follow the link in the previous invitation email and click on the "Decline" button.

# OpenReview Team'''

#         messages = client.get_messages(to='external_reviewer2@mit.edu', subject='[NeurIPS 2023] You have been assigned as a Reviewer for paper number 4')
#         assert messages and len(messages) == 1
#         assert messages[0]['content']['text'] == f'''This is to inform you that you have been assigned as a Reviewer for paper number 4 for NeurIPS 2023.

# To review this new assignment, please login to OpenReview and go to https://openreview.net/forum?id={submission.id}.

# To check all of your assigned papers, go to https://openreview.net/group?id=NeurIPS.cc/2023/Conference/Reviewers.

# Thank you,

# NeurIPS 2023 Conference Program Chairs'''

#         assert client.get_groups('NeurIPS.cc/2023/Conference/Emergency_Reviewers/Invited', member='~External_Reviewer_MIT1')

#         assert client.get_groups('NeurIPS.cc/2023/Conference/Emergency_Reviewers', member='~External_Reviewer_MIT1')
#         assert client.get_groups('NeurIPS.cc/2023/Conference/Reviewers', member='~External_Reviewer_MIT1')



#         ## Invite the same reviewer again
#         with pytest.raises(openreview.OpenReviewException) as openReviewError:
#             posted_edge=ac_client.post_edge(openreview.Edge(
#                 invitation='NeurIPS.cc/2023/Conference/Reviewers/-/Invite_Assignment',
#                 readers = [conference.id, 'NeurIPS.cc/2023/Conference/Paper4/Senior_Area_Chairs', 'NeurIPS.cc/2023/Conference/Paper4/Area_Chairs', 'external_reviewer2@mit.edu'],
#                 nonreaders = ['NeurIPS.cc/2023/Conference/Paper4/Authors'],
#                 writers = [conference.id],
#                 signatures = [signatory_group.id],
#                 head = submission.id,
#                 tail = '~External_Reviewer_MIT1',
#                 label = 'Invitation Sent'
#             ))
#         assert openReviewError.value.args[0].get('name') == 'TooManyError'

#         ## Invite the same reviewer again
#         with pytest.raises(openreview.OpenReviewException, match=r'Already invited as ~External_Reviewer_MIT1'):
#             posted_edge=ac_client.post_edge(openreview.Edge(
#                 invitation='NeurIPS.cc/2023/Conference/Reviewers/-/Invite_Assignment',
#                 readers = [conference.id, 'NeurIPS.cc/2023/Conference/Paper4/Senior_Area_Chairs', 'NeurIPS.cc/2023/Conference/Paper4/Area_Chairs', 'external_reviewer2@mit.edu'],
#                 nonreaders = ['NeurIPS.cc/2023/Conference/Paper4/Authors'],
#                 writers = [conference.id],
#                 signatures = [signatory_group.id],
#                 head = submission.id,
#                 tail = 'external_reviewer2@mit.edu',
#                 label = 'Invitation Sent'
#             ))

#         ## Invite reviewer already assigned
#         with pytest.raises(openreview.OpenReviewException, match=r'Already assigned as ~Reviewer_UMass1'):
#             posted_edge=ac_client.post_edge(openreview.Edge(
#                 invitation='NeurIPS.cc/2023/Conference/Reviewers/-/Invite_Assignment',
#                 readers = [conference.id, 'NeurIPS.cc/2023/Conference/Paper4/Senior_Area_Chairs', 'NeurIPS.cc/2023/Conference/Paper4/Area_Chairs', '~Reviewer_UMass1'],
#                 nonreaders = ['NeurIPS.cc/2023/Conference/Paper4/Authors'],
#                 writers = [conference.id],
#                 signatures = [signatory_group.id],
#                 head = submission.id,
#                 tail = '~Reviewer_UMass1',
#                 label = 'Invitation Sent'
#             ))

#         ## Official reviewer accepts the invitation
#         posted_edge=ac_client.post_edge(openreview.Edge(
#             invitation='NeurIPS.cc/2023/Conference/Reviewers/-/Invite_Assignment',
#             readers = [conference.id, 'NeurIPS.cc/2023/Conference/Paper4/Senior_Area_Chairs', 'NeurIPS.cc/2023/Conference/Paper4/Area_Chairs', '~Reviewer_Amazon1'],
#             nonreaders = ['NeurIPS.cc/2023/Conference/Paper4/Authors'],
#             writers = [conference.id],
#             signatures = [signatory_group.id],
#             head = submission.id,
#             tail = '~Reviewer_Amazon1',
#             label = 'Invitation Sent'
#         ))

#         helpers.await_queue()

#         messages = client.get_messages(to='reviewer6@amazon.com', subject='[NeurIPS 2023] Invitation to review paper titled Paper title 4')
#         assert messages and len(messages) == 1
#         invitation_url = re.search('https://.*\n', messages[0]['content']['text']).group(0).replace('https://openreview.net', 'http://localhost:3030').replace('&amp;', '&')[:-1]
#         helpers.respond_invitation(selenium, request_page, invitation_url, accept=True)
#         notes = selenium.find_element_by_class_name("note_editor")
#         assert notes
#         messages = notes.find_elements_by_tag_name("h4")
#         assert messages
#         assert 'Thank you for accepting this invitation from Conference on Neural Information Processing Systems.' == messages[0].text

#         helpers.await_queue()

#         invite_edges=pc_client.get_edges(invitation='NeurIPS.cc/2023/Conference/Reviewers/-/Invite_Assignment', head=submission.id, tail='~Reviewer_Amazon1')
#         assert len(invite_edges) == 1
#         assert invite_edges[0].label == 'Accepted'

#         assignment_edges=pc_client.get_edges(invitation='NeurIPS.cc/2023/Conference/Reviewers/-/Assignment', head=submission.id)
#         assert len(assignment_edges) == 4
#         assert '~Reviewer_Amazon1' in [e.tail for e in assignment_edges]

#         assert '~Reviewer_Amazon1' in pc_client.get_group('NeurIPS.cc/2023/Conference/Paper4/Reviewers').members

#         assert len(pc_client.get_groups(regex='NeurIPS.cc/2023/Conference/Paper4/Reviewer_', signatory='~Reviewer_Amazon1')) == 1

#         messages = client.get_messages(to='reviewer6@amazon.com', subject='[NeurIPS 2023] Reviewer Invitation accepted for paper 4')
#         assert messages and len(messages) == 1
#         assert messages[0]['content']['text'] == '''Hi Reviewer Amazon,
# Thank you for accepting the invitation to review the paper number: 4, title: Paper title 4.

# Please go to the NeurIPS 2023 Reviewers Console and check your pending tasks: https://openreview.net/group?id=NeurIPS.cc/2023/Conference/Reviewers

# If you would like to change your decision, please follow the link in the previous invitation email and click on the "Decline" button.

# OpenReview Team'''

#         assert client.get_groups('NeurIPS.cc/2023/Conference/Emergency_Reviewers/Invited', member='~Reviewer_Amazon1')
#         assert client.get_groups('NeurIPS.cc/2023/Conference/Emergency_Reviewers', member='~Reviewer_Amazon1')
#         assert client.get_groups('NeurIPS.cc/2023/Conference/Reviewers', member='~Reviewer_Amazon1')

#         messages = client.get_messages(to='reviewer6@amazon.com', subject='[NeurIPS 2023] You have been assigned as a Reviewer for paper number 4')
#         assert messages and len(messages) == 1
#         assert messages[0]['content']['text'] == f'''This is to inform you that you have been assigned as a Reviewer for paper number 4 for NeurIPS 2023.

# To review this new assignment, please login to OpenReview and go to https://openreview.net/forum?id={submission.id}.

# To check all of your assigned papers, go to https://openreview.net/group?id=NeurIPS.cc/2023/Conference/Reviewers.

# Thank you,

# NeurIPS 2023 Conference Program Chairs'''

#         ## Delete assignment when there is a review should throw an error
#         submission=conference.get_submissions(number=5)[0]
#         assignment_edge=client.get_edges(invitation='NeurIPS.cc/2023/Conference/Reviewers/-/Assignment', head=submission.id, tail='~Reviewer_UMass1')[0]
#         assignment_edge.ddate=openreview.tools.datetime_millis(datetime.datetime.utcnow())
#         with pytest.raises(openreview.OpenReviewException, match=r'Can not remove assignment, the user ~Reviewer_UMass1 already posted a review.'):
#             client.post_edge(assignment_edge)


#     def test_comment_stage(self, conference, helpers, test_client, client):

#         now = datetime.datetime.utcnow()
#         due_date = now + datetime.timedelta(days=3)
#         comment_invitees = [openreview.stages.CommentStage.Readers.REVIEWERS_ASSIGNED, openreview.stages.CommentStage.Readers.AREA_CHAIRS_ASSIGNED,
#                             openreview.stages.CommentStage.Readers.SENIOR_AREA_CHAIRS_ASSIGNED]
#         conference.comment_stage = openreview.stages.CommentStage(reader_selection=True, check_mandatory_readers=True, invitees=comment_invitees, readers=comment_invitees)
#         conference.create_comment_stage()

#         reviewer_client=openreview.Client(username='reviewer1@umass.edu', password=helpers.strong_password)

#         signatory_groups=client.get_groups(regex='NeurIPS.cc/2023/Conference/Paper5/Reviewer_', signatory='reviewer1@umass.edu')
#         assert len(signatory_groups) == 1

#         submissions=conference.get_submissions(number=5)
#         assert len(submissions) == 1

#         review_note=reviewer_client.post_note(openreview.Note(
#             invitation='NeurIPS.cc/2023/Conference/Paper5/-/Official_Comment',
#             forum=submissions[0].id,
#             replyto=submissions[0].id,
#             readers=['NeurIPS.cc/2023/Conference/Program_Chairs', 'NeurIPS.cc/2023/Conference/Paper5/Senior_Area_Chairs', 'NeurIPS.cc/2023/Conference/Paper5/Area_Chairs', signatory_groups[0].id],
#             #nonreaders=['NeurIPS.cc/2023/Conference/Paper5/Authors'],
#             writers=[signatory_groups[0].id],
#             signatures=[signatory_groups[0].id],
#             content={
#                 'title': 'Test comment',
#                 'comment': 'This is a comment'
#             }
#         ))

#         helpers.await_queue()

#         process_logs = client.get_process_logs(id=review_note.id)
#         assert len(process_logs) == 1
#         assert process_logs[0]['status'] == 'ok'

#         messages = client.get_messages(to='reviewer1@umass.edu', subject='[NeurIPS 2023] Your comment was received on Paper Number: 5, Paper Title: \"Paper title 5\"')
#         assert messages and len(messages) == 1

#         messages = client.get_messages(to='ac1@mit.edu', subject='\[NeurIPS 2023\] Reviewer .* commented on a paper in your area. Paper Number: 5, Paper Title: \"Paper title 5\"')
#         assert messages and len(messages) == 1

#         messages = client.get_messages(to='sac1@google.com', subject='\[NeurIPS 2023\] Reviewer .* commented on a paper in your area. Paper Number: 5, Paper Title: \"Paper title 5\"')
#         assert not messages

#         ac_client=openreview.Client(username='ac1@mit.edu', password=helpers.strong_password)

#         signatory_groups=client.get_groups(regex='NeurIPS.cc/2023/Conference/Paper5/Area_Chair_', signatory='ac1@mit.edu')
#         assert len(signatory_groups) == 1

#         comment_note=ac_client.post_note(openreview.Note(
#             invitation='NeurIPS.cc/2023/Conference/Paper5/-/Official_Comment',
#             forum=submissions[0].id,
#             replyto=submissions[0].id,
#             readers=['NeurIPS.cc/2023/Conference/Program_Chairs', 'NeurIPS.cc/2023/Conference/Paper5/Senior_Area_Chairs', 'NeurIPS.cc/2023/Conference/Paper5/Area_Chairs'],
#             #nonreaders=['NeurIPS.cc/2023/Conference/Paper5/Authors'],
#             writers=[signatory_groups[0].id],
#             signatures=[signatory_groups[0].id],
#             content={
#                 'title': 'Test an AC comment',
#                 'comment': 'This is an AC comment'
#             }
#         ))

#         helpers.await_queue()

#         process_logs = client.get_process_logs(id=comment_note.id)
#         assert len(process_logs) == 1
#         assert process_logs[0]['status'] == 'ok'

#         messages = client.get_messages(to='ac1@mit.edu', subject='[NeurIPS 2023] Your comment was received on Paper Number: 5, Paper Title: \"Paper title 5\"')
#         assert messages and len(messages) == 1

#         messages = client.get_messages(to='sac1@google.com', subject='\[NeurIPS 2023\] Area Chair .* commented on a paper in your area. Paper Number: 5, Paper Title: \"Paper title 5\"')
#         assert messages and len(messages) == 1

#         sac_client=openreview.Client(username='sac1@google.com', password=helpers.strong_password)

#         comment_note=sac_client.post_note(openreview.Note(
#             invitation='NeurIPS.cc/2023/Conference/Paper5/-/Official_Comment',
#             forum=submissions[0].id,
#             replyto=submissions[0].id,
#             readers=['NeurIPS.cc/2023/Conference/Program_Chairs', 'NeurIPS.cc/2023/Conference/Paper5/Senior_Area_Chairs', 'NeurIPS.cc/2023/Conference/Paper5/Area_Chairs'],
#             writers=['NeurIPS.cc/2023/Conference/Paper5/Senior_Area_Chairs'],
#             signatures=['NeurIPS.cc/2023/Conference/Paper5/Senior_Area_Chairs'],
#             content={
#                 'title': 'Test an SAC comment',
#                 'comment': 'This is an SAC comment'
#             }
#         ))

#         helpers.await_queue()

#         process_logs = client.get_process_logs(id=comment_note.id)
#         assert len(process_logs) == 1
#         assert process_logs[0]['status'] == 'ok'

#         messages = client.get_messages(to='sac1@google.com', subject='[NeurIPS 2023] Your comment was received on Paper Number: 5, Paper Title: \"Paper title 5\"')
#         assert messages and len(messages) == 1

#     def test_rebuttal_stage(self, conference, helpers, test_client, client):

#         now = datetime.datetime.utcnow()
#         due_date = now + datetime.timedelta(days=3)

#         pc_client=openreview.Client(username='pc@neurips.cc', password=helpers.strong_password)
#         request_form=pc_client.get_notes(invitation='openreview.net/Support/-/Request_Form')[0]
#         stage_note=client.post_note(openreview.Note(
#             content={
#                 'review_deadline': due_date.strftime('%Y/%m/%d'),
#                 'make_reviews_public': 'No, reviews should NOT be revealed publicly when they are posted',
#                 'release_reviews_to_authors': 'Yes, reviews should be revealed when they are posted to the paper\'s authors',
#                 'release_reviews_to_reviewers': 'Reviews should be immediately revealed to the paper\'s reviewers who have already submitted their review',
#                 'email_program_chairs_about_reviews': 'No, do not email program chairs about received reviews'
#             },
#             forum=request_form.forum,
#             invitation='openreview.net/Support/-/Request{}/Review_Stage'.format(request_form.number),
#             readers=['NeurIPS.cc/2023/Conference/Program_Chairs', 'openreview.net/Support'],
#             referent=request_form.forum,
#             replyto=request_form.forum,
#             signatures=['~Program_NeurIPSChair1'],
#             writers=[]
#         ))

#         helpers.await_queue()

#         reviews=client.get_notes(invitation='NeurIPS.cc/2023/Conference/Paper5/-/Official_Review', sort='tmdate')
#         assert len(reviews) == 1
#         reviews[0].readers = [
#             'NeurIPS.cc/2023/Conference/Program_Chairs',
#             'NeurIPS.cc/2023/Conference/Paper5/Senior_Area_Chairs',
#             'NeurIPS.cc/2023/Conference/Paper5/Area_Chairs',
#             'NeurIPS.cc/2023/Conference/Paper5/Reviewers/Submitted',
#             'NeurIPS.cc/2023/Conference/Paper5/Authors'
#         ]

#         now = datetime.datetime.utcnow()
#         due_date = now + datetime.timedelta(days=3)
#         comment_invitees = [openreview.stages.CommentStage.Readers.REVIEWERS_SUBMITTED, openreview.stages.CommentStage.Readers.AREA_CHAIRS_ASSIGNED,
#                             openreview.stages.CommentStage.Readers.SENIOR_AREA_CHAIRS_ASSIGNED, openreview.stages.CommentStage.Readers.AUTHORS]
#         conference.comment_stage = openreview.stages.CommentStage(reader_selection=True, invitees=comment_invitees, readers=comment_invitees)
#         conference.create_comment_stage()

#         submissions=conference.get_submissions(number=5)
#         assert len(submissions) == 1

#         rebuttal_note=test_client.post_note(openreview.Note(
#             invitation='NeurIPS.cc/2023/Conference/Paper5/-/Official_Comment',
#             forum=submissions[0].id,
#             replyto=reviews[0].id,
#             readers=[
#                 'NeurIPS.cc/2023/Conference/Program_Chairs',
#                 'NeurIPS.cc/2023/Conference/Paper5/Senior_Area_Chairs',
#                 'NeurIPS.cc/2023/Conference/Paper5/Area_Chairs',
#                 'NeurIPS.cc/2023/Conference/Paper5/Reviewers/Submitted',
#                 'NeurIPS.cc/2023/Conference/Paper5/Authors'
#             ],
#             #nonreaders=['NeurIPS.cc/2023/Conference/Paper5/Authors'],
#             writers=['NeurIPS.cc/2023/Conference/Paper5/Authors'],
#             signatures=['NeurIPS.cc/2023/Conference/Paper5/Authors'],
#             content={
#                 'title': 'Thanks for your review',
#                 'comment': 'Thanks for the detailed review!'
#             }
#         ))

#         helpers.await_queue()


#     def test_meta_review_stage(self, conference, helpers, test_client, client):

#         now = datetime.datetime.utcnow()
#         due_date = now + datetime.timedelta(days=3)
#         conference.meta_review_stage = openreview.stages.MetaReviewStage(due_date=due_date)
#         conference.create_meta_review_stage()

#         ac_client=openreview.Client(username='ac1@mit.edu', password=helpers.strong_password)

#         signatory_groups=client.get_groups(regex='NeurIPS.cc/2023/Conference/Paper5/Area_Chair_', signatory='ac1@mit.edu')
#         assert len(signatory_groups) == 1

#         submissions=conference.get_submissions(number=5)
#         assert len(submissions) == 1

#         meta_review_note=ac_client.post_note(openreview.Note(
#             invitation='NeurIPS.cc/2023/Conference/Paper5/-/Meta_Review',
#             forum=submissions[0].id,
#             replyto=submissions[0].id,
#             readers=['NeurIPS.cc/2023/Conference/Program_Chairs', 'NeurIPS.cc/2023/Conference/Paper5/Senior_Area_Chairs', 'NeurIPS.cc/2023/Conference/Paper5/Area_Chairs'],
#             nonreaders = ['NeurIPS.cc/2023/Conference/Paper5/Authors'],
#             writers=['NeurIPS.cc/2023/Conference/Program_Chairs', 'NeurIPS.cc/2023/Conference/Paper5/Area_Chairs'],
#             signatures=[signatory_groups[0].id],
#             content={
#                 'metareview': 'Paper is very good!',
#                 'recommendation': 'Accept (Oral)',
#                 'confidence': '4: The area chair is confident but not absolutely certain'
#             }
#         ))

#     def test_paper_ranking_stage(self, conference, client, test_client, selenium, request_page):

#         ac_client=openreview.Client(username='ac1@mit.edu', password=helpers.strong_password)
#         signatory_groups=client.get_groups(regex='NeurIPS.cc/2023/Conference/Paper5/Area_Chair_', signatory='ac1@mit.edu')
#         assert len(signatory_groups) == 1
#         ac_anon_id=signatory_groups[0].id

#         ac_url = 'http://localhost:3030/group?id=NeurIPS.cc/2023/Conference/Area_Chairs'
#         request_page(selenium, ac_url, ac_client.token, wait_for_element='5-metareview-status')

#         status = selenium.find_element_by_id("5-metareview-status")
#         assert status

#         assert not status.find_elements_by_class_name('tag-widget')

#         reviewer_client=openreview.Client(username='reviewer1@umass.edu', password=helpers.strong_password)

#         signatory_groups=client.get_groups(regex='NeurIPS.cc/2023/Conference/Paper5/Reviewer_', signatory='reviewer1@umass.edu')
#         assert len(signatory_groups) == 1
#         reviewer_anon_id=signatory_groups[0].id

#         reviewer_url = 'http://localhost:3030/group?id=NeurIPS.cc/2023/Conference/Reviewers'
#         request_page(selenium, reviewer_url, reviewer_client.token)

#         assert not selenium.find_elements_by_class_name('tag-widget')

#         now = datetime.datetime.utcnow()
#         conference.open_paper_ranking(conference.get_area_chairs_id(), due_date=now + datetime.timedelta(minutes = 40))
#         conference.open_paper_ranking(conference.get_reviewers_id(), due_date=now + datetime.timedelta(minutes = 40))

#         ac_url = 'http://localhost:3030/group?id=NeurIPS.cc/2023/Conference/Area_Chairs'
#         request_page(selenium, ac_url, ac_client.token, by=By.ID, wait_for_element='5-metareview-status')

#         status = selenium.find_element_by_id("5-metareview-status")
#         assert status

#         tag = status.find_element_by_class_name('tag-widget')
#         assert tag

#         options = tag.find_elements_by_tag_name("li")
#         assert options
#         assert len(options) == 3

#         options = tag.find_elements_by_tag_name("a")
#         assert options
#         assert len(options) == 3

#         blinded_notes = conference.get_submissions(sort='number:asc')

#         ac_client.post_tag(openreview.Tag(invitation = 'NeurIPS.cc/2023/Conference/Area_Chairs/-/Paper_Ranking',
#             forum = blinded_notes[-1].id,
#             tag = '1 of 3',
#             readers = ['NeurIPS.cc/2023/Conference', ac_anon_id],
#             signatures = [ac_anon_id])
#         )

#         reviewer_url = 'http://localhost:3030/group?id=NeurIPS.cc/2023/Conference/Reviewers'
#         request_page(selenium, reviewer_url, reviewer_client.token, by=By.CLASS_NAME, wait_for_element='tag-widget')

#         tags = selenium.find_elements_by_class_name('tag-widget')
#         assert tags

#         options = tags[0].find_elements_by_tag_name("li")
#         assert options
#         assert len(options) == 5

#         options = tags[0].find_elements_by_tag_name("a")
#         assert options
#         assert len(options) == 5

#         reviewer_client.post_tag(openreview.Tag(invitation = 'NeurIPS.cc/2023/Conference/Reviewers/-/Paper_Ranking',
#             forum = blinded_notes[-1].id,
#             tag = '2 of 5',
#             readers = ['NeurIPS.cc/2023/Conference', 'NeurIPS.cc/2023/Conference/Paper1/Area_Chairs', reviewer_anon_id],
#             signatures = [reviewer_anon_id])
#         )

#         reviewer2_client = openreview.Client(username='reviewer2@mit.edu', password=helpers.strong_password)
#         signatory_groups=client.get_groups(regex='NeurIPS.cc/2023/Conference/Paper1/Reviewer_', signatory='reviewer2@mit.edu')
#         assert len(signatory_groups) == 1
#         reviewer2_anon_id=signatory_groups[0].id

#         reviewer2_client.post_tag(openreview.Tag(invitation = 'NeurIPS.cc/2023/Conference/Reviewers/-/Paper_Ranking',
#             forum = blinded_notes[0].id,
#             tag = '1 of 5',
#             readers = ['NeurIPS.cc/2023/Conference', 'NeurIPS.cc/2023/Conference/Paper1/Area_Chairs', reviewer2_anon_id],
#             signatures = [reviewer2_anon_id])
#         )

#         with pytest.raises(openreview.OpenReviewException) as openReviewError:
#             reviewer2_client.post_tag(openreview.Tag(invitation = 'NeurIPS.cc/2023/Conference/Reviewers/-/Paper_Ranking',
#                 forum = blinded_notes[0].id,
#                 tag = '1 of 5',
#                 readers = ['NeurIPS.cc/2023/Conference', 'NeurIPS.cc/2023/Conference/Paper1/Area_Chairs', reviewer2_anon_id],
#                 signatures = [reviewer2_anon_id])
#             )
#         assert  openReviewError.value.args[0].get('name') == 'TooManyError'

#     def test_review_rating_stage(self, conference, helpers, test_client, client):

#         now = datetime.datetime.utcnow()
#         conference.set_review_rating_stage(openreview.ReviewRatingStage(due_date = now + datetime.timedelta(minutes = 40)))

#         ac_client = openreview.Client(username='ac1@mit.edu', password=helpers.strong_password)
#         signatory_groups=client.get_groups(regex='NeurIPS.cc/2023/Conference/Paper5/Area_Chair_', signatory='ac1@mit.edu')
#         assert len(signatory_groups) == 1
#         ac_anon_id=signatory_groups[0].id

#         submissions = conference.get_submissions(number=5)

#         reviews = ac_client.get_notes(forum=submissions[0].id, invitation='NeurIPS.cc/2023/Conference/Paper5/-/Official_Review')
#         assert len(reviews) == 1

#         review_rating_note = ac_client.post_note(openreview.Note(
#             forum=submissions[0].id,
#             replyto=reviews[0].id,
#             invitation=reviews[0].signatures[0] + '/-/Review_Rating',
#             readers=['NeurIPS.cc/2023/Conference/Program_Chairs',
#             ac_anon_id],
#             writers=[ac_anon_id],
#             signatures=[ac_anon_id],
#             content={
#                 'review_quality': 'Good'
#             }
#         ))
#         assert review_rating_note

#     def test_add_impersonator(self, client, request_page, selenium):
#         ## Need super user permission to add the venue to the active_venues group
#         request_form=client.get_notes(invitation='openreview.net/Support/-/Request_Form', sort='tmdate')[0]
#         conference=openreview.helpers.get_conference(client, request_form.id)

#         conference.set_impersonators(group_ids=['pc@neurips.cc'])

#         pc_client = openreview.Client(username='pc@neurips.cc', password=helpers.strong_password)
#         reviewers_id = conference.get_reviewers_id()
#         reviewers = client.get_group(reviewers_id).members
#         assert len(reviewers) > 0
#         result = pc_client.impersonate(reviewers[0])

#         assert result.get('token') is not None
#         assert result.get('user', {}).get('id') == reviewers[0]

#     def test_withdraw_after_review(self, conference, helpers, test_client, client, selenium, request_page):

#         submissions = test_client.get_notes(invitation='NeurIPS.cc/2023/Conference/-/Blind_Submission', sort='tmdate')
#         assert len(submissions) == 5

#         withdrawn_note = test_client.post_note(openreview.Note(
#             forum=submissions[0].id,
#             replyto=submissions[0].id,
#             invitation=f'NeurIPS.cc/2023/Conference/Paper5/-/Withdraw',
#             readers = [
#                 'NeurIPS.cc/2023/Conference',
#                 'NeurIPS.cc/2023/Conference/Paper5/Authors',
#                 'NeurIPS.cc/2023/Conference/Paper5/Reviewers',
#                 'NeurIPS.cc/2023/Conference/Paper5/Area_Chairs',
#                 'NeurIPS.cc/2023/Conference/Paper5/Senior_Area_Chairs',
#                 'NeurIPS.cc/2023/Conference/Program_Chairs'],
#             writers = [conference.get_id(), conference.get_program_chairs_id()],
#             signatures = ['NeurIPS.cc/2023/Conference/Paper5/Authors'],
#             content = {
#                 'title': 'Submission Withdrawn by the Authors',
#                 'withdrawal confirmation': 'I have read and agree with the venue\'s withdrawal policy on behalf of myself and my co-authors.'
#             }
#         ))
#         helpers.await_queue()

#         process_logs = client.get_process_logs(id=withdrawn_note.id)
#         assert len(process_logs) == 1
#         assert process_logs[0]['status'] == 'ok'

#         withdrawn_submission=client.get_note(submissions[0].id)
#         assert withdrawn_submission.invitation == 'NeurIPS.cc/2023/Conference/-/Withdrawn_Submission'
#         assert withdrawn_submission.readers == [
#                 'NeurIPS.cc/2023/Conference/Paper5/Authors',
#                 'NeurIPS.cc/2023/Conference/Paper5/Reviewers',
#                 'NeurIPS.cc/2023/Conference/Paper5/Area_Chairs',
#                 'NeurIPS.cc/2023/Conference/Paper5/Senior_Area_Chairs',
#                 'NeurIPS.cc/2023/Conference/Program_Chairs']
#         assert withdrawn_submission.content['keywords'] == ''

#         pc_client=openreview.Client(username='pc@neurips.cc', password=helpers.strong_password)

#         request_page(selenium, "http://localhost:3030/group?id=NeurIPS.cc/2023/Conference/Program_Chairs#paper-status", pc_client.token, wait_for_element='notes')
#         assert "NeurIPS 2023 Conference Program Chairs | OpenReview" in selenium.title
#         notes_panel = selenium.find_element_by_id('notes')
#         assert notes_panel
#         tabs = notes_panel.find_element_by_class_name('tabs-container')
#         assert tabs
#         assert tabs.find_element_by_id('venue-configuration')
#         assert tabs.find_element_by_id('paper-status')
#         assert tabs.find_element_by_id('reviewer-status')
#         assert tabs.find_element_by_id('areachair-status')

#         assert '#' == tabs.find_element_by_id('paper-status').find_element_by_class_name('row-1').text
#         assert 'Paper Summary' == tabs.find_element_by_id('paper-status').find_element_by_class_name('row-2').text
#         assert 'Review Progress' == tabs.find_element_by_id('paper-status').find_element_by_class_name('row-3').text
#         assert 'Status' == tabs.find_element_by_id('paper-status').find_element_by_class_name('row-4').text
#         assert 'Decision' == tabs.find_element_by_id('paper-status').find_element_by_class_name('row-5').text

#     def test_desk_reject_after_review(self, conference, helpers, test_client, client, selenium, request_page):

#         submissions = test_client.get_notes(invitation='NeurIPS.cc/2023/Conference/-/Blind_Submission', sort='tmdate')
#         assert len(submissions) == 4

#         pc_client=openreview.Client(username='pc@neurips.cc', password=helpers.strong_password)

#         desk_reject_note = pc_client.post_note(openreview.Note(
#             forum=submissions[0].id,
#             replyto=submissions[0].id,
#             invitation=f'NeurIPS.cc/2023/Conference/Paper4/-/Desk_Reject',
#             readers = [
#                 'NeurIPS.cc/2023/Conference',
#                 'NeurIPS.cc/2023/Conference/Paper4/Authors',
#                 'NeurIPS.cc/2023/Conference/Paper4/Reviewers',
#                 'NeurIPS.cc/2023/Conference/Paper4/Area_Chairs',
#                 'NeurIPS.cc/2023/Conference/Paper4/Senior_Area_Chairs',
#                 'NeurIPS.cc/2023/Conference/Program_Chairs'],
#             writers = [conference.get_id(), 'NeurIPS.cc/2023/Conference/Program_Chairs'],
#             signatures = ['NeurIPS.cc/2023/Conference/Program_Chairs'],
#             content = {
#                 'title': 'Submission Desk Rejected by Program Chairs',
#                 'desk_reject_comments': 'Wrong PDF.'
#             }
#         ))
#         helpers.await_queue()

#         desk_rejected_submission=client.get_note(submissions[0].id)
#         assert desk_rejected_submission.invitation == 'NeurIPS.cc/2023/Conference/-/Desk_Rejected_Submission'
#         assert desk_rejected_submission.readers == [
#                 'NeurIPS.cc/2023/Conference/Paper4/Authors',
#                 'NeurIPS.cc/2023/Conference/Paper4/Reviewers',
#                 'NeurIPS.cc/2023/Conference/Paper4/Area_Chairs',
#                 'NeurIPS.cc/2023/Conference/Paper4/Senior_Area_Chairs',
#                 'NeurIPS.cc/2023/Conference/Program_Chairs']
#         assert desk_rejected_submission.content['keywords'] == ''

#         desk_reject_note.ddate = openreview.tools.datetime_millis(datetime.datetime.now())
#         pc_client.post_note(desk_reject_note)

#         helpers.await_queue()

#         submission_note = client.get_note(desk_reject_note.forum)
#         assert submission_note.invitation == 'NeurIPS.cc/2023/Conference/-/Blind_Submission'
#         assert submission_note.readers == [
#                 'NeurIPS.cc/2023/Conference',
#                 'NeurIPS.cc/2023/Conference/Paper4/Senior_Area_Chairs',
#                 'NeurIPS.cc/2023/Conference/Paper4/Area_Chairs',
#                 'NeurIPS.cc/2023/Conference/Paper4/Reviewers',
#                 'NeurIPS.cc/2023/Conference/Paper4/Authors'
#                 ]
#         assert submission_note.content['keywords'] == ''

#     def test_submission_revision_deadline(self, conference, helpers, test_client, client, selenium, request_page):
#         pc_client = openreview.Client(username='pc@neurips.cc', password=helpers.strong_password)
#         request_form = pc_client.get_notes(invitation='openreview.net/Support/-/Request_Form')[0]

#         now = datetime.datetime.utcnow()
#         due_date = now + datetime.timedelta(days=-1)
#         first_date = now + datetime.timedelta(days=-1)

#         # expire submission deadlne
#         venue_revision_note = pc_client.post_note(openreview.Note(
#             content={
#                 'title': 'Conference on Neural Information Processing Systems',
#                 'Official Venue Name': 'Conference on Neural Information Processing Systems',
#                 'Abbreviated Venue Name': 'NeurIPS 2023',
#                 'Official Website URL': 'https://neurips.cc',
#                 'program_chair_emails': ['pc@neurips.cc'],
#                 'contact_email': 'pc@neurips.cc',
#                 'ethics_chairs_and_reviewers': 'Yes, our venue has Ethics Chairs and Reviewers',
#                 'Venue Start Date': '2023/12/01',
#                 'Submission Deadline': due_date.strftime('%Y/%m/%d'),
#                 'abstract_registration_deadline': first_date.strftime('%Y/%m/%d'),
#                 'Location': 'Virtual',
#                 'How did you hear about us?': 'ML conferences',
#                 'Expected Submissions': '100'
#             },
#             forum=request_form.forum,
#             invitation='openreview.net/Support/-/Request{}/Revision'.format(request_form.number),
#             readers=['{}/Program_Chairs'.format('NeurIPS.cc/2023/Conference'), 'openreview.net/Support'],
#             referent=request_form.forum,
#             replyto=request_form.forum,
#             signatures=['~Program_NeurIPSChair1'],
#             writers=[]
#         ))

#         helpers.await_queue()

#         revision_invitation = client.get_invitation(conference.get_invitation_id('Revision'))
#         assert revision_invitation.duedate == openreview.tools.datetime_millis(due_date.replace(hour=0, minute=0, second=0, microsecond=0))

#         # Post a submission revision stage note
#         now = datetime.datetime.utcnow()
#         start_date = now - datetime.timedelta(days=1)
#         due_date = now + datetime.timedelta(days=3)
#         revision_stage_note = pc_client.post_note(openreview.Note(
#             content={
#                 'submission_revision_name': 'Revision',
#                 'submission_revision_start_date': start_date.strftime('%Y/%m/%d'),
#                 'submission_revision_deadline': due_date.strftime('%Y/%m/%d'),
#                 'accepted_submissions_only': 'Enable revision for all submissions',
#                 'submission_author_edition': 'Allow addition and removal of authors',
#                 'submission_revision_remove_options': ['keywords']
#             },
#             forum=request_form.forum,
#             invitation='openreview.net/Support/-/Request{}/Submission_Revision_Stage'.format(request_form.number),
#             readers=['{}/Program_Chairs'.format('NeurIPS.cc/2023/Conference'), 'openreview.net/Support'],
#             referent=request_form.forum,
#             replyto=request_form.forum,
#             signatures=['~Program_NeurIPSChair1'],
#             writers=[]
#         ))
#         assert revision_stage_note

#         helpers.await_queue()

#         revision_invitation = client.get_invitation(conference.get_invitation_id('Revision'))
#         assert revision_invitation.duedate == openreview.tools.datetime_millis(due_date.replace(hour=0, minute=0, second=0, microsecond=0))

#         # Update revision note and test revision invitation duedate is not updated
#         venue_revision_note.content['Location'] = 'Amherst, MA'
#         pc_client.post_note(revision_stage_note)

#         revision_invitation = client.get_invitation(conference.get_invitation_id('Revision'))
#         assert revision_invitation.duedate == openreview.tools.datetime_millis(due_date.replace(hour=0, minute=0, second=0, microsecond=0))
