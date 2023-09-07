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

    def test_create_conference(self, client, openreview_client, helpers, selenium, request_page):

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
        helpers.create_user('reviewerethics@neurips.com', 'Ethics', 'ReviewerNeurIPS')

        helpers.create_user('melisatest@neuirps.cc', 'Melisa', 'Gilbert')
        helpers.create_user('melisatest2@neurips.cc', 'Melisa', 'Gilbert')

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
                'How did you hear about us?': 'ML conferences',
                'Expected Submissions': '100',
                'api_version': '2',
                'submission_deadline_author_reorder': 'Yes'
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

        venue_group = openreview_client.get_group('NeurIPS.cc/2023/Conference')
        assert venue_group
        assert venue_group.host == 'NeurIPS.cc'
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

    def test_revision(self, client, openreview_client, selenium, request_page, helpers):

        pc_client=openreview.Client(username='pc@neurips.cc', password=helpers.strong_password)
        request_form=pc_client.get_notes(invitation='openreview.net/Support/-/Request_Form')[0]

        now = datetime.datetime.utcnow()
        due_date = now + datetime.timedelta(days=3)
        first_date = now + datetime.timedelta(days=1)

        pc_client.post_note(openreview.Note(
            invitation=f'openreview.net/Support/-/Request{request_form.number}/Revision',
            forum=request_form.id,
            readers=['NeurIPS.cc/2023/Conference/Program_Chairs', 'openreview.net/Support'],
            referent=request_form.id,
            replyto=request_form.id,
            signatures=['~Program_NeurIPSChair1'],
            writers=[],
            content={
                'title': 'Conference on Neural Information Processing Systems',
                'Official Venue Name': 'Conference on Neural Information Processing Systems',
                'Abbreviated Venue Name': 'NeurIPS 2023',
                'Official Website URL': 'https://neurips.cc',
                'program_chair_emails': ['pc@neurips.cc'],
                'contact_email': 'pc@neurips.cc',
                'Venue Start Date': '2023/12/01',
                'Submission Deadline': due_date.strftime('%Y/%m/%d'),
                'abstract_registration_deadline': first_date.strftime('%Y/%m/%d'),
                'Location': 'Virtual',
                'submission_reviewer_assignment': 'Automatic',
                'How did you hear about us?': 'ML conferences',
                'Expected Submissions': '100',
                'use_recruitment_template': 'Yes',
                'homepage_override': {
                    'instructions': '''**Authors**
Please see our [call for papers](https://nips.cc/Conferences/2023/CallForPapers) and read the [ethics guidelines](https://nips.cc/public/EthicsGuidelines)'''
                }
            }
        ))
        helpers.await_queue()

        request_page(selenium, 'http://localhost:3030/group?id=NeurIPS.cc/2023/Conference', pc_client.token, wait_for_element='header')
        header_div = selenium.find_element(By.ID, 'header')
        assert header_div
        location_tag = header_div.find_element(By.CLASS_NAME, 'venue-location')
        assert location_tag and location_tag.text == request_form.content['Location']
        description = header_div.find_element(By.CLASS_NAME, 'description')
        assert description and 'Authors' in description.text

    def test_recruit_senior_area_chairs(self, client, openreview_client, selenium, request_page, helpers):

        pc_client=openreview.Client(username='pc@neurips.cc', password=helpers.strong_password)
        request_form=pc_client.get_notes(invitation='openreview.net/Support/-/Request_Form')[0]

        # Test Reviewer Recruitment
        request_page(selenium, 'http://localhost:3030/forum?id={}'.format(request_form.id), pc_client.token, by=By.CLASS_NAME, wait_for_element='reply_row')
        recruitment_div = selenium.find_element(By.ID, 'note_{}'.format(request_form.id))
        assert recruitment_div
        reply_row = recruitment_div.find_element(By.CLASS_NAME, 'reply_row')
        assert reply_row
        buttons = reply_row.find_elements(By.CLASS_NAME, 'btn-xs')
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
        notes_panel = selenium.find_element(By.ID, 'notes')
        assert notes_panel
        tabs = notes_panel.find_element(By.CLASS_NAME, 'tabs-container')
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

        tasks_url = 'http://localhost:3030/group?id=NeurIPS.cc/2023/Conference/Senior_Area_Chairs#seniorareachair-tasks'
        request_page(selenium, tasks_url, sac_client.token, by=By.LINK_TEXT, wait_for_element='Senior Area Chair Bid')

        task_panel = selenium.find_element(By.LINK_TEXT, "Senior Area Chair Tasks")
        task_panel.click()

        assert selenium.find_element(By.LINK_TEXT, "Senior Area Chair Bid")

        bid_url = 'http://localhost:3030/invitation?id=NeurIPS.cc/2023/Conference/Senior_Area_Chairs/-/Bid'
        request_page(selenium, bid_url, sac_client.token, wait_for_element='notes')

        notes = selenium.find_element(By.ID, 'all-area-chairs')
        assert notes
        assert len(notes.find_elements(By.CLASS_NAME, 'bid-container')) == 3

        header = selenium.find_element(By.ID, 'header')
        instruction = header.find_element(By.TAG_NAME, 'li')
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
        recruitment_div = selenium.find_element(By.ID, 'note_{}'.format(request_form.id))
        assert recruitment_div
        reply_row = recruitment_div.find_element(By.CLASS_NAME, 'reply_row')
        assert reply_row
        buttons = reply_row.find_elements(By.CLASS_NAME, 'btn-xs')
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
        notes = selenium.find_element(By.CLASS_NAME, "note_editor")
        assert notes
        messages = notes.find_elements(By.TAG_NAME, 'h4')
        assert messages
        assert 'You have declined the invitation from NeurIPS 2023.' == messages[0].text
        messages = notes.find_elements(By.TAG_NAME, 'p')
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
        link = selenium.find_element(By.CLASS_NAME, 'reduced-load-link')
        link.click()
        time.sleep(0.5)
        dropdown = selenium.find_element(By.CLASS_NAME, 'dropdown-select__input-container')
        dropdown.click()
        time.sleep(0.5)
        values = selenium.find_elements(By.CLASS_NAME, 'dropdown-select__option')
        assert len(values) > 0
        values[2].click()
        time.sleep(0.5)
        button = selenium.find_element(By.XPATH, '//button[text()="Submit"]')
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
        header = selenium.find_element(By.ID, 'header')
        strong_elements = header.find_elements(By.TAG_NAME, 'strong')
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

        reviewer_details = '''reviewerethics@neurips.com, Ethics Reviewer'''
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
        assert 'reviewerethics@neurips.com' in group.members

        messages = client.get_messages(to='reviewerethics@neurips.com', subject='[NeurIPS 2023] Invitation to serve as Ethics Reviewer')
        assert messages and len(messages) == 1
        invitation_url = re.search('https://.*\n', messages[0]['content']['text']).group(0).replace('https://openreview.net', 'http://localhost:3030').replace('&amp;', '&')[:-1]
        helpers.respond_invitation(selenium, request_page, invitation_url, accept=True)

        helpers.await_queue()

        group = client.get_group('NeurIPS.cc/2023/Conference/Ethics_Reviewers')
        assert group
        assert len(group.members) == 1
        assert 'reviewerethics@neurips.com' in group.members

        result = conference.recruit_reviewers(invitees = ['reviewerethics@neurips.com'], title = 'Ethics Review invitation', message = '{accept_url}, {decline_url}', reviewers_name = 'Ethics_Reviewers')
        assert result['invited'] == []
        assert result['already_invited'] == {
            'NeurIPS.cc/2023/Conference/Ethics_Reviewers/Invited': ['reviewerethics@neurips.com']
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
                'Expected Submissions': '100',
                'Additional Submission Options': {
                    'corresponding_author': {
                        'value': {
                        'param': {
                            'type': 'string',
                            'regex': '~.*|([a-z0-9_\\-\\.]{1,}@[a-z0-9_\\-\\.]{2,}\\.[a-z]{2,},){0,}([a-z0-9_\\-\\.]{1,}@[a-z0-9_\\-\\.]{2,}\\.[a-z]{2,})',
                            'optional': True
                        }
                        },
                        'description': 'Select which author should be the primary corresponding author for this submission. Please enter an email address or an OpenReview ID that exactly matches one of the authors.',
                        'order': 11
                    }
                }
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
        assert submission_inv.signatures == ['NeurIPS.cc/2023/Conference']

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

            if i == 2:
                note.content['authors']['value'].append('Melisa Gilbert')
                note.content['authors']['value'].append('Melisa Gilbert')
                note.content['authorids']['value'].append('~Melisa_Gilbert1')
                note.content['authorids']['value'].append('~Melisa_Gilbert2')
                print(note)

            test_client.post_note_edit(invitation='NeurIPS.cc/2023/Conference/-/Submission',
                signatures=['~SomeFirstName_User1'],
                note=note)


        ## finish submission deadline
        now = datetime.datetime.utcnow()
        due_date = now + datetime.timedelta(days=3)
        first_date = now - datetime.timedelta(minutes=28)

        venue_revision_note = openreview.Note(
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
                'Expected Submissions': '100',
                'hide_fields': ['keywords', 'financial_support']
            },
            forum=request_form.forum,
            invitation='openreview.net/Support/-/Request{}/Revision'.format(request_form.number),
            readers=['{}/Program_Chairs'.format('NeurIPS.cc/2023/Conference'), 'openreview.net/Support'],
            referent=request_form.forum,
            replyto=request_form.forum,
            signatures=['~Program_NeurIPSChair1'],
            writers=[]
        )

        with pytest.raises(openreview.OpenReviewException, match=r'Invalid field to hide: financial_support'):
            pc_client.post_note(venue_revision_note)

        venue_revision_note.content['hide_fields'] = ['keywords']
        pc_client.post_note(venue_revision_note)

        helpers.await_queue()
        helpers.await_queue_edit(openreview_client, 'NeurIPS.cc/2023/Conference/-/Post_Submission-0-0')
        helpers.await_queue_edit(openreview_client, 'NeurIPS.cc/2023/Conference/-/Withdrawal-0-0')
        helpers.await_queue_edit(openreview_client, 'NeurIPS.cc/2023/Conference/-/Desk_Rejection-0-0')
        helpers.await_queue_edit(openreview_client, 'NeurIPS.cc/2023/Conference/-/Revision-0-0')

        notes = test_client.get_notes(content= { 'venueid': 'NeurIPS.cc/2023/Conference/Submission' }, sort='number:desc')
        assert len(notes) == 5

        assert notes[0].readers == ['NeurIPS.cc/2023/Conference', 'NeurIPS.cc/2023/Conference/Submission5/Authors']
        assert notes[0].content['keywords']['readers'] == ['NeurIPS.cc/2023/Conference', 'NeurIPS.cc/2023/Conference/Submission5/Authors']

        assert test_client.get_invitation('NeurIPS.cc/2023/Conference/Submission5/-/Withdrawal')
        assert test_client.get_invitation('NeurIPS.cc/2023/Conference/Submission5/-/Desk_Rejection')
        assert test_client.get_invitation('NeurIPS.cc/2023/Conference/Submission5/-/Revision')

        post_submission =  openreview_client.get_invitation('NeurIPS.cc/2023/Conference/-/Post_Submission')
        assert 'authors' in post_submission.edit['note']['content']
        assert 'authorids' in post_submission.edit['note']['content']
        assert 'keywords' in post_submission.edit['note']['content']

        pc_client_v2=openreview.api.OpenReviewClient(username='pc@neurips.cc', password=helpers.strong_password)

        ## try to edit a submission as a PC and check revision invitation is updated
        submissions = pc_client_v2.get_notes(invitation='NeurIPS.cc/2023/Conference/-/Submission', sort='number:asc')
        submission = submissions[3]

        pc_revision = pc_client_v2.post_note_edit(invitation='NeurIPS.cc/2023/Conference/-/PC_Revision',
            signatures=['NeurIPS.cc/2023/Conference/Program_Chairs'],
            note=openreview.api.Note(
                id = submission.id,
                content = {
                    'title': { 'value': submission.content['title']['value'] + ' Version 2' },
                    'abstract': submission.content['abstract'],
                    'authorids': { 'value': submission.content['authorids']['value'] + ['celeste@yahoo.com'] },
                    'authors': { 'value': submission.content['authors']['value'] + ['Celeste NeurIPS'] },
                    'keywords': { 'value': ['machine learning', 'nlp'] }
                }
            ))

        helpers.await_queue_edit(openreview_client, edit_id=pc_revision['id'])

        revision_inv =  test_client.get_invitation('NeurIPS.cc/2023/Conference/Submission4/-/Revision')
        assert revision_inv.edit['note']['content']['authors']['value'] == [
          'SomeFirstName User',
          'Peter SomeLastName',
          'Andrew Mc',
          'Celeste NeurIPS'
        ]
        assert revision_inv.edit['note']['content']['authorids']['value'] == [
          'test@mail.com',
          'peter@mail.com',
          'andrew@google.com',
          'celeste@yahoo.com'
        ]

        revision_inv = test_client.get_invitation('NeurIPS.cc/2023/Conference/Submission2/-/Revision')
        assert revision_inv.edit['note']['content']['authors']['value'] == [
          'SomeFirstName User',
          'Peter SomeLastName',
          'Andrew Mc',
          'Melisa Gilbert',
          'Melisa Gilbert'
        ]
        assert revision_inv.edit['note']['content']['authorids']['value'] == [
          'test@mail.com',
          'peter@mail.com',
          'andrew@fb.com',
          '~Melisa_Gilbert1',
          '~Melisa_Gilbert2'
        ]

        revision_note = test_client.post_note_edit(invitation='NeurIPS.cc/2023/Conference/Submission2/-/Revision',
            signatures=['NeurIPS.cc/2023/Conference/Submission2/Authors'],
            note=openreview.api.Note(
                content={
                    'title': { 'value': 'Paper title 2 Updated' },
                    'abstract': { 'value': 'This is an abstract 2 updated' },
                    'authorids': { 'value': ['test@mail.com', '~Melisa_Gilbert2', 'andrew@fb.com', 'peter@mail.com', '~Melisa_Gilbert1' ] },
                    'authors': { 'value': ['SomeFirstName User',  'Melisa Gilbert', 'Andrew Mc', 'Peter SomeLastName', 'Melisa Gilbert' ] },
                    'keywords': { 'value': ['machine learning', 'nlp'] },
                }
            ))
        helpers.await_queue_edit(openreview_client, edit_id=revision_note['id'])

        ## update submission
        revision_note = test_client.post_note_edit(invitation='NeurIPS.cc/2023/Conference/Submission4/-/Revision',
            signatures=['NeurIPS.cc/2023/Conference/Submission4/Authors'],
            note=openreview.api.Note(
                content={
                    'title': { 'value': 'Paper title 4 Updated' },
                    'abstract': { 'value': 'This is an abstract 4 updated' },
                    'authorids': { 'value': ['test@mail.com', 'andrew@google.com', 'peter@mail.com', 'celeste@yahoo.com' ] },
                    'authors': { 'value': ['SomeFirstName User',  'Andrew Mc', 'Peter SomeLastName', 'Celeste NeurIPS' ] },
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

        post_submission_invitation = client.get_invitation(f'openreview.net/Support/-/Request{request_form.number}/Post_Submission')
        assert post_submission_invitation
        assert 'values-dropdown' in post_submission_invitation.reply['content']['hide_fields']
        assert ['keywords', 'TLDR', 'abstract', 'pdf', 'corresponding_author'] == post_submission_invitation.reply['content']['hide_fields']['values-dropdown']

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

        assert client.get_group('NeurIPS.cc/2023/Conference/Submission4/Senior_Area_Chairs').readers == ['NeurIPS.cc/2023/Conference',
            'NeurIPS.cc/2023/Conference/Program_Chairs',
            'NeurIPS.cc/2023/Conference/Submission4/Senior_Area_Chairs',
            'NeurIPS.cc/2023/Conference/Submission4/Area_Chairs',
            'NeurIPS.cc/2023/Conference/Submission4/Reviewers']
        assert client.get_group('NeurIPS.cc/2023/Conference/Submission4/Senior_Area_Chairs').nonreaders == ['NeurIPS.cc/2023/Conference/Submission4/Authors']

        assert client.get_group('NeurIPS.cc/2023/Conference/Submission4/Area_Chairs').readers == ['NeurIPS.cc/2023/Conference',
            'NeurIPS.cc/2023/Conference/Program_Chairs',
            'NeurIPS.cc/2023/Conference/Submission4/Senior_Area_Chairs',
            'NeurIPS.cc/2023/Conference/Submission4/Area_Chairs',
            'NeurIPS.cc/2023/Conference/Submission4/Reviewers']

        assert client.get_group('NeurIPS.cc/2023/Conference/Submission4/Area_Chairs').deanonymizers == ['NeurIPS.cc/2023/Conference',
            'NeurIPS.cc/2023/Conference/Program_Chairs',
            'NeurIPS.cc/2023/Conference/Submission4/Senior_Area_Chairs',
            'NeurIPS.cc/2023/Conference/Submission4/Area_Chairs',
            'NeurIPS.cc/2023/Conference/Submission4/Reviewers']

        assert client.get_group('NeurIPS.cc/2023/Conference/Submission4/Area_Chairs').nonreaders == ['NeurIPS.cc/2023/Conference/Submission4/Authors']

        assert client.get_group('NeurIPS.cc/2023/Conference/Submission4/Reviewers').readers == ['NeurIPS.cc/2023/Conference',
            'NeurIPS.cc/2023/Conference/Submission4/Senior_Area_Chairs',
            'NeurIPS.cc/2023/Conference/Submission4/Area_Chairs',
            'NeurIPS.cc/2023/Conference/Submission4/Reviewers']

        assert client.get_group('NeurIPS.cc/2023/Conference/Submission4/Reviewers').deanonymizers == ['NeurIPS.cc/2023/Conference',
            'NeurIPS.cc/2023/Conference/Program_Chairs',
            'NeurIPS.cc/2023/Conference/Submission4/Senior_Area_Chairs',
            'NeurIPS.cc/2023/Conference/Submission4/Area_Chairs',
            'NeurIPS.cc/2023/Conference/Submission4/Reviewers']

        assert client.get_group('NeurIPS.cc/2023/Conference/Submission4/Reviewers').nonreaders == ['NeurIPS.cc/2023/Conference/Submission4/Authors']

    def test_setup_matching(self, client, openreview_client, helpers):

        pc_client=openreview.Client(username='pc@neurips.cc', password=helpers.strong_password)
        pc_client_v2=openreview.api.OpenReviewClient(username='pc@neurips.cc', password=helpers.strong_password)
        request_form=pc_client.get_notes(invitation='openreview.net/Support/-/Request_Form')[0]

        ## setup matching ACs to take into account the SAC conflicts
        client.post_note(openreview.Note(
            content={
                'title': 'Paper Matching Setup',
                'matching_group': 'NeurIPS.cc/2023/Conference/Area_Chairs',
                'compute_conflicts': 'NeurIPS',
                'compute_conflicts_N_years': '3',
                'compute_affinity_scores': 'No'

            },
            forum=request_form.id,
            replyto=request_form.id,
            invitation=f'openreview.net/Support/-/Request{request_form.number}/Paper_Matching_Setup',
            readers=['NeurIPS.cc/2023/Conference/Program_Chairs', 'openreview.net/Support'],
            signatures=['~Program_NeurIPSChair1'],
            writers=[]
        ))
        helpers.await_queue()

        submissions = pc_client_v2.get_notes(content= { 'venueid': 'NeurIPS.cc/2023/Conference/Submission'}, sort='number:asc')

        client.post_note(openreview.Note(
            content={
                'title': 'Paper Matching Setup',
                'matching_group': 'NeurIPS.cc/2023/Conference/Reviewers',
                'compute_conflicts': 'NeurIPS',
                'compute_conflicts_N_years': '3',
                'compute_affinity_scores': 'No'
            },
            forum=request_form.id,
            replyto=request_form.id,
            invitation=f'openreview.net/Support/-/Request{request_form.number}/Paper_Matching_Setup',
            readers=['NeurIPS.cc/2023/Conference/Program_Chairs', 'openreview.net/Support'],
            signatures=['~Program_NeurIPSChair1'],
            writers=[]
        ))
        helpers.await_queue()

        reviewers_proposed_edges = []
        for i in range(0,4):
            for r in ['~Reviewer_UMass1', '~Reviewer_MIT1', '~Reviewer_Google1']:
                reviewers_proposed_edges.append(openreview.api.Edge(
                    invitation = 'NeurIPS.cc/2023/Conference/Reviewers/-/Proposed_Assignment',
                    head = submissions[i].id,
                    tail = r,
                    signatures = ['NeurIPS.cc/2023/Conference/Program_Chairs'],
                    weight = 1,
                    label = 'reviewer-matching',
                    readers = ["NeurIPS.cc/2023/Conference", f"NeurIPS.cc/2023/Conference/Submission{submissions[i].number}/Senior_Area_Chairs", f"NeurIPS.cc/2023/Conference/Submission{submissions[i].number}/Area_Chairs", r],
                    nonreaders = [f"NeurIPS.cc/2023/Conference/Submission{submissions[i].number}/Authors"],
                    writers = ["NeurIPS.cc/2023/Conference", f"NeurIPS.cc/2023/Conference/Submission{submissions[i].number}/Senior_Area_Chairs", f"NeurIPS.cc/2023/Conference/Submission{submissions[i].number}/Area_Chairs"]
                ))

            openreview_client.post_edge(openreview.api.Edge(
                invitation = 'NeurIPS.cc/2023/Conference/Area_Chairs/-/Proposed_Assignment',
                head = submissions[i].id,
                tail = '~Area_GoogleChair1',
                signatures = ['NeurIPS.cc/2023/Conference/Program_Chairs'],
                weight = 1,
                label = 'ac-matching'
            ))

        openreview.tools.post_bulk_edges(client=openreview_client, edges=reviewers_proposed_edges)

        venue = openreview.helpers.get_conference(pc_client, request_form.id, setup=False)
        venue.set_assignments(assignment_title='ac-matching', committee_id='NeurIPS.cc/2023/Conference/Area_Chairs')
        venue.set_assignments(assignment_title='reviewer-matching', committee_id='NeurIPS.cc/2023/Conference/Reviewers', enable_reviewer_reassignment=True)

        ac_group = pc_client_v2.get_group('NeurIPS.cc/2023/Conference/Submission1/Area_Chairs')
        assert ['~Area_GoogleChair1'] == ac_group.members

        ac_group = pc_client_v2.get_group('NeurIPS.cc/2023/Conference/Submission4/Area_Chairs')
        assert ['~Area_GoogleChair1'] == ac_group.members

        sac_group = pc_client_v2.get_group('NeurIPS.cc/2023/Conference/Submission1/Senior_Area_Chairs')
        assert ['~SeniorArea_NeurIPSChair1'] == sac_group.members

        sac_group = pc_client_v2.get_group('NeurIPS.cc/2023/Conference/Submission4/Senior_Area_Chairs')
        assert ['~SeniorArea_NeurIPSChair1'] == sac_group.members

    def test_review_stage(self, helpers, openreview_client, test_client, client):

        pc_client=openreview.Client(username='pc@neurips.cc', password=helpers.strong_password)
        request_form=pc_client.get_notes(invitation='openreview.net/Support/-/Request_Form')[0]

        ## Show the pdf and supplementary material to assigned reviewers
        pc_client.post_note(openreview.Note(
            content= {
                'force': 'Yes',
                'submission_readers': 'Assigned program committee (assigned reviewers, assigned area chairs, assigned senior area chairs if applicable)'
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

        now = datetime.datetime.utcnow()
        due_date = now + datetime.timedelta(days=3)

        pc_client=openreview.Client(username='pc@neurips.cc', password=helpers.strong_password)
        request_form=pc_client.get_notes(invitation='openreview.net/Support/-/Request_Form')[0]
        review_stage_note=pc_client.post_note(openreview.Note(
            content={
                'review_deadline': due_date.strftime('%Y/%m/%d'),
                'make_reviews_public': 'No, reviews should NOT be revealed publicly when they are posted',
                'release_reviews_to_authors': 'No, reviews should NOT be revealed when they are posted to the paper\'s authors',
                'release_reviews_to_reviewers': 'Review should not be revealed to any reviewer, except to the author of the review',
                'email_program_chairs_about_reviews': 'No, do not email program chairs about received reviews',
                'remove_review_form_options': 'title,review',
                'additional_review_form_options': {
                    "summary": {
                        "order": 1,
                        "description": "Briefly summarize the paper and its contributions. This is not the place to critique the paper; the authors should generally agree with a well-written summary.",
                        "value": {
                            "param": {
                                "maxLength": 200000,
                                "type": "string",
                                "input": "textarea",
                                "markdown": True
                            }
                        }
                    },
                    "soundness": {
                        "order": 2,
                        "description": "Please assign the paper a numerical rating on the following scale to indicate the soundness of the technical claims, experimental and research methodology and on whether the central claims of the paper are adequately supported with evidence.",
                        "value": {
                            "param": {
                                "type": "string",
                                "enum": [
                                    "4 excellent",
                                    "3 good",
                                    "2 fair",
                                    "1 poor"
                                ],
                                "input": "radio"
                            }
                        }
                    },
                    "presentation": {
                        "order": 3,
                        "description": "Please assign the paper a numerical rating on the following scale to indicate the quality of the presentation. This should take into account the writing style and clarity, as well as contextualization relative to prior work.",
                        "value": {
                            "param": {
                                "type": "string",
                                "enum": [
                                    "4 excellent",
                                    "3 good",
                                    "2 fair",
                                    "1 poor"
                                ],
                                "input": "radio"
                            }
                        }
                    },
                    "contribution": {
                        "order": 4,
                        "description": "Please assign the paper a numerical rating on the following scale to indicate the quality of the overall contribution this paper makes to the research area being studied. Are the questions being asked important? Does the paper bring a significant originality of ideas and/or execution? Are the results valuable to share with the broader NeurIPS community?",
                        "value": {
                            "param": {
                                "type": "string",
                                "enum": [
                                    "4 excellent",
                                    "3 good",
                                    "2 fair",
                                    "1 poor"
                                ],
                                "input": "radio"
                            }
                        }
                    },
                    "strengths": {
                        "order": 5,
                        "description": "A substantive assessment of the strengths of the paper, touching on each of the following dimensions: originality, quality, clarity, and significance. We encourage reviewers to be broad in their definitions of originality and significance. For example, originality may arise from a new definition or problem formulation, creative combinations of existing ideas, application to a new domain, or removing limitations from prior results. You can incorporate Markdown and Latex into your review. See https://openreview.net/faq.",
                        "value": {
                            "param": {
                                "maxLength": 200000,
                                "type": "string",
                                "input": "textarea",
                                "markdown": True
                            }
                        }
                    },
                    "weaknesses": {
                        "order": 6,
                        "description": "A substantive assessment of the weaknesses of the paper. Focus on constructive and actionable insights on how the work could improve towards its stated goals. Be specific, avoid generic remarks. For example, if you believe the contribution lacks novelty, provide references and an explanation as evidence; if you believe experiments are insufficient, explain why and exactly what is missing, etc.",
                        "value": {
                            "param": {
                                "maxLength": 200000,
                                "type": "string",
                                "input": "textarea",
                                "markdown": True
                            }
                        }
                    },
                    "questions": {
                        "order": 7,
                        "description": "Please list up and carefully describe any questions and suggestions for the authors. Think of the things where a response from the author can change your opinion, clarify a confusion or address a limitation. This is important for a productive rebuttal and discussion phase with the authors.",
                        "value": {
                            "param": {
                                "maxLength": 200000,
                                "type": "string",
                                "input": "textarea",
                                "markdown": True
                            }
                        }
                    },
                    "limitations": {
                        "order": 8,
                        "description": " Have the authors adequately addressed the limitations and, if applicable, potential negative societal impact of their work (refer to the checklist guidelines on limitations and broader societal impacts: https://neurips.cc/public/guides/PaperChecklist)? If not, please include constructive suggestions for improvement. Authors should be rewarded rather than punished for being up front about the limitations of their work and any potential negative societal impact.",
                        "value": {
                            "param": {
                                "maxLength": 200000,
                                "type": "string",
                                "input": "textarea",
                                "markdown": True
                            }
                        }
                    },
                    "flag_for_ethics_review": {
                        "order": 10,
                        "description": "If there are ethical issues with this paper, please flag the paper for an ethics review and select area of expertise that would be most useful for the ethics reviewer to have. Please click all that apply. For guidance on when this is appropriate, please review the NeurIPS Code of Ethics (https://neurips.cc/public/EthicsGuidelines) and the Ethics Reviewer Guidelines (https://neurips.cc/Conferences/2023/EthicsGuidelinesForReviewers).",
                        "value": {
                            "param": {
                                "type": "string[]",
                                "enum": [
                                    "No ethics review needed.",
                                    "Ethics review needed: Discrimination / Bias / Fairness Concerns",
                                    "Ethics review needed: Inadequate Data and Algorithm Evaluation",
                                    "Ethics review needed: Inappropriate Potential Applications & Impact  (e.g., human rights concerns)",
                                    "Ethics review needed: Privacy and Security (e.g., consent, surveillance, data storage concern)",
                                    "Ethics review needed: Compliance (e.g., GDPR, copyright, license, terms of use)",
                                    "Ethics review needed: Research Integrity Issues (e.g., plagiarism)",
                                    "Ethics review needed: Responsible Research Practice (e.g., IRB, documentation, research ethics)",
                                    "Ethics review needed: Failure to comply with NeurIPS Code of Ethics (lack of required documentation, safeguards, disclosure, licenses, legal compliance)"
                                ],
                                "input": "checkbox"
                            }
                        }
                    },
                    "rating": {
                        "order": 11,
                        "description": "Please provide an \"overall score\" for this submission.",
                        "value": {
                            "param": {
                                "type": "string",
                                "enum": [
                                    "10: Award quality: Technically flawless paper with groundbreaking impact, with exceptionally strong evaluation, reproducibility, and resources, and no unaddressed ethical considerations.",
                                    "9: Very Strong Accept: Technically flawless paper with groundbreaking impact on at least one area of AI/ML and excellent impact on multiple areas of AI/ML, with flawless evaluation, resources, and reproducibility, and no unaddressed ethical considerations.",
                                    "8: Strong Accept: Technically strong paper, with novel ideas, excellent impact on at least one area, or high-to-excellent impact on multiple areas, with excellent evaluation, resources, and reproducibility, and no unaddressed ethical considerations.",
                                    "7: Accept: Technically solid paper, with high impact on at least one sub-area, or moderate-to-high impact on more than one areas, with good-to-excellent evaluation, resources, reproducibility, and no unaddressed ethical considerations.",
                                    "6: Weak Accept: Technically solid, moderate-to-high impact paper, with no major concerns with respect to evaluation, resources, reproducibility, ethical considerations.",
                                    "5: Borderline accept: Technically solid paper where reasons to accept outweigh reasons to reject, e.g., limited evaluation. Please use sparingly.",
                                    "4: Borderline reject: Technically solid paper where reasons to reject, e.g., limited evaluation, outweigh reasons to accept, e.g., good evaluation. Please use sparingly.",
                                    "3: Reject: For instance, a paper with technical flaws, weak evaluation, inadequate reproducibility and incompletely addressed ethical considerations.",
                                    "2: Strong Reject: For instance, a paper with major technical flaws, and/or poor evaluation, limited impact, poor reproducibility and mostly unaddressed ethical considerations.",
                                    "1: Very Strong Reject: For instance, a paper with trivial results or unaddressed ethical considerations"
                                ],
                                "input": "radio"
                            }
                        }
                    },
                    "confidence": {
                        "order": 12,
                        "description": "Please provide a \"confidence score\" for your assessment of this submission to indicate how confident you are in your evaluation.",
                        "value": {
                            "param": {
                                "type": "string",
                                "enum": [
                                    "5: You are absolutely certain about your assessment. You are very familiar with the related work and checked the math/other details carefully.",
                                    "4: You are confident in your assessment, but not absolutely certain. It is unlikely, but not impossible, that you did not understand some parts of the submission or that you are unfamiliar with some pieces of related work.",
                                    "3: You are fairly confident in your assessment. It is possible that you did not understand some parts of the submission or that you are unfamiliar with some pieces of related work. Math/other details were not carefully checked.",
                                    "2: You are willing to defend your assessment, but it is quite likely that you did not understand the central parts of the submission or that you are unfamiliar with some pieces of related work. Math/other details were not carefully checked.",
                                    "1: Your assessment is an educated guess. The submission is not in your area or the submission was difficult to understand. Math/other details were not carefully checked."
                                ],
                                "input": "radio"
                            }
                        }
                    },
                    "code_of_conduct": {
                        "description": "While performing my duties as a reviewer (including writing reviews and participating in discussions), I have and will continue to abide by the NeurIPS code of conduct (https://nips.cc/public/CodeOfConduct).",
                        "order": 13,
                        "value": {
                            "param": {
                                "type": "string",
                                "enum": [
                                    "Yes"
                                ],
                                "input": "checkbox"
                            }
                        }
                    },
                    "first_time_reviewer": {
                        "description": "Is this your first time reviewing for NeurIPS?",
                        "order": 14,
                        "value": {
                            "param": {
                                "type": "string",
                                "enum": [
                                    "Yes"
                                ],
                                "input": "checkbox",
                                "optional": True
                            }
                        }
                    }
                }
            },
            forum=request_form.forum,
            invitation='openreview.net/Support/-/Request{}/Review_Stage'.format(request_form.number),
            readers=['NeurIPS.cc/2023/Conference/Program_Chairs', 'openreview.net/Support'],
            referent=request_form.forum,
            replyto=request_form.forum,
            signatures=['~Program_NeurIPSChair1'],
            writers=[]
        ))

        helpers.await_queue()

        assert len(openreview_client.get_invitations(invitation='NeurIPS.cc/2023/Conference/-/Official_Review')) == 4
        invitation = openreview_client.get_invitation('NeurIPS.cc/2023/Conference/Submission1/-/Official_Review')
        assert 'first_time_reviewer' in invitation.edit['note']['content']

        reviewer_client=openreview.api.OpenReviewClient(username='reviewer1@umass.edu', password=helpers.strong_password)

        anon_groups = reviewer_client.get_groups(prefix='NeurIPS.cc/2023/Conference/Submission1/Reviewer_', signatory='~Reviewer_UMass1')
        anon_group_id = anon_groups[0].id

        review_edit = reviewer_client.post_note_edit(
            invitation='NeurIPS.cc/2023/Conference/Submission1/-/Official_Review',
            signatures=[anon_group_id],
            note=openreview.api.Note(
                content={
                    'summary': { 'value': 'good paper' },
                    'strengths': { 'value': '7: Good paper, accept'},
                    'weaknesses': { 'value': 'No weaknesses'},
                    'questions': { 'value': '7: Good paper, accept'},
                    'limitations': { 'value': '7: Good paper, accept'},
                    'flag_for_ethics_review': { 'value': ['Ethics review needed: Discrimination / Bias / Fairness Concerns']},
                    'soundness': { 'value': '3 good'},
                    'presentation': { 'value': '3 good'},
                    'contribution': { 'value': '3 good'},
                    'rating': { 'value': '10: Award quality: Technically flawless paper with groundbreaking impact, with exceptionally strong evaluation, reproducibility, and resources, and no unaddressed ethical considerations.'},
                    'confidence': { 'value': '5: You are absolutely certain about your assessment. You are very familiar with the related work and checked the math/other details carefully.'},
                    'code_of_conduct': { 'value': 'Yes'},
                    'first_time_reviewer': { 'value': 'Yes'}
                }
            )
        )

        helpers.await_queue(openreview_client)

        reviewer_client_2 = openreview.api.OpenReviewClient(username='reviewer2@mit.edu', password=helpers.strong_password)
        anon_groups = reviewer_client.get_groups(prefix='NeurIPS.cc/2023/Conference/Submission1/Reviewer_', signatory='~Reviewer_MIT1')
        anon_group_id = anon_groups[0].id
        review_edit = reviewer_client_2.post_note_edit(
            invitation='NeurIPS.cc/2023/Conference/Submission1/-/Official_Review',
            signatures=[anon_group_id],
            note=openreview.api.Note(
                content={
                    'summary': { 'value': 'bad paper' },
                    'strengths': { 'value': '2: Bad paper, reject'},
                    'weaknesses': { 'value': 'many weaknesses'},
                    'questions': { 'value': '2: Bad paper, reject'},
                    'limitations': { 'value': '2: Bad paper, reject'},
                    'flag_for_ethics_review': { 'value': ['No ethics review needed.']},
                    'soundness': { 'value': '1 poor'},
                    'presentation': { 'value': '1 poor'},
                    'contribution': { 'value': '1 poor'},
                    'rating': { 'value': '1: Very Strong Reject: For instance, a paper with trivial results or unaddressed ethical considerations'},
                    'confidence': { 'value': '5: You are absolutely certain about your assessment. You are very familiar with the related work and checked the math/other details carefully.'},
                    'code_of_conduct': { 'value': 'Yes'},
                }
            )
        )

        helpers.await_queue(openreview_client)

    def test_comment_stage(self, helpers, openreview_client):

        pc_client=openreview.Client(username='pc@neurips.cc', password=helpers.strong_password)
        request_form=pc_client.get_notes(invitation='openreview.net/Support/-/Request_Form')[0]

        # Post an official comment stage note
        now = datetime.datetime.utcnow()
        start_date = now - datetime.timedelta(days=2)
        end_date = now + datetime.timedelta(days=3)
        comment_stage_note = pc_client.post_note(openreview.Note(
            content={
                'commentary_start_date': start_date.strftime('%Y/%m/%d'),
                'commentary_end_date': end_date.strftime('%Y/%m/%d'),
                'participants': ['Program Chairs', 'Assigned Senior Area Chairs', 'Assigned Area Chairs', 'Assigned Reviewers'],
                'additional_readers': ['Program Chairs'],
                'email_program_chairs_about_official_comments': 'No, do not email PCs for each official comment made in the venue'
            },
            forum=request_form.forum,
            invitation=f'openreview.net/Support/-/Request{request_form.number}/Comment_Stage',
            readers=['NeurIPS.cc/2023/Conference/Program_Chairs', 'openreview.net/Support'],
            replyto=request_form.forum,
            referent=request_form.forum,
            signatures=['~Program_NeurIPSChair1'],
            writers=[]
        ))

        helpers.await_queue()

        invitation = openreview_client.get_invitation('NeurIPS.cc/2023/Conference/Submission1/-/Official_Comment')
        assert invitation
        assert invitation.invitees == [
            'NeurIPS.cc/2023/Conference',
            'openreview.net/Support',
            'NeurIPS.cc/2023/Conference/Submission1/Senior_Area_Chairs',
            'NeurIPS.cc/2023/Conference/Submission1/Area_Chairs',
            'NeurIPS.cc/2023/Conference/Submission1/Reviewers'
        ]

        rev_client_v2=openreview.api.OpenReviewClient(username='reviewer5@google.com', password=helpers.strong_password)
        anon_groups = rev_client_v2.get_groups(prefix='NeurIPS.cc/2023/Conference/Submission1/Reviewer_', signatory='~Reviewer_Google1')
        anon_group_id = anon_groups[0].id

        submissions = openreview_client.get_notes(invitation='NeurIPS.cc/2023/Conference/-/Submission', sort='number:asc')

        comment_edit = rev_client_v2.post_note_edit(
            invitation='NeurIPS.cc/2023/Conference/Submission1/-/Official_Comment',
            signatures=[anon_group_id],
            note=openreview.api.Note(
                replyto = submissions[0].id,
                readers = [
                    'NeurIPS.cc/2023/Conference/Program_Chairs',
                    'NeurIPS.cc/2023/Conference/Submission1/Senior_Area_Chairs',
                    'NeurIPS.cc/2023/Conference/Submission1/Area_Chairs',
                    'NeurIPS.cc/2023/Conference/Submission1/Reviewers',
                ],
                content={
                    'comment': { 'value': 'Sorry, I can\'t review this paper' },
                }
            )
        )

        helpers.await_queue(openreview_client)

    def test_ethics_review_stage(self, helpers, openreview_client, request_page, selenium):

        pc_client=openreview.Client(username='pc@neurips.cc', password=helpers.strong_password)
        request_form=pc_client.get_notes(invitation='openreview.net/Support/-/Request_Form')[0]

        assert openreview_client.get_group('NeurIPS.cc/2023/Conference/Ethics_Reviewers')
        assert openreview_client.get_group('NeurIPS.cc/2023/Conference/Ethics_Reviewers/Declined')
        group = openreview_client.get_group('NeurIPS.cc/2023/Conference/Ethics_Reviewers/Invited')
        assert group
        assert len(group.members) == 1
        assert 'reviewerethics@neurips.com' in group.members

        now = datetime.datetime.utcnow()
        start_date = now - datetime.timedelta(days=2)
        due_date = now + datetime.timedelta(days=3)
        stage_note = pc_client.post_note(openreview.Note(
            content={
                'ethics_review_start_date': start_date.strftime('%Y/%m/%d'),
                'ethics_review_deadline': due_date.strftime('%Y/%m/%d'),
                'make_ethics_reviews_public': 'No, ethics reviews should NOT be revealed publicly when they are posted',
                'release_ethics_reviews_to_authors': "No, ethics reviews should NOT be revealed when they are posted to the paper\'s authors",
                'release_ethics_reviews_to_reviewers': 'Ethics Review should not be revealed to any reviewer, except to the author of the ethics review',
                'remove_ethics_review_form_options': 'ethics_review',
                'additional_ethics_review_form_options': {
                    "ethical_issues": {
                        "order": 1,
                        "description": "Does this paper raise ethical issues? Please refer to the NeurIPS Ethical guidelines(https://neurips.cc/Conferences/2023/EthicsGuidelinesForReviewers) for reference.",
                        "value": {
                            "param": {
                                "type": "string",
                                "enum": [
                                    "Yes",
                                    "No"
                                ],
                                "input": "radio"
                            }
                        }
                    },
                    "ethics_review": {
                        "order": 2,
                        "description": "Please elaborate (max 200000 characters). Add formatting using Markdown and formulas using LaTeX.",
                        "value": {
                            "param": {
                                "maxLength": 200000,
                                "type": "string",
                                "input": "textarea",
                                "markdown": True
                            }
                        }
                    },
                    "issues_acknowledged": {
                        "order": 3,
                        "description": "Have these issues been addressed or acknowledged?",
                        "value": {
                            "param": {
                                "type": "string",
                                "enum": [
                                    "Yes",
                                    "No"
                                ],
                                "input": "radio"
                            }
                        }
                    },
                    "issues_acknowledged_description": {
                        "order": 4,
                        "description": "Please elaborate (max 200000 characters). Add formatting using Markdown and formulas using LaTeX.",
                        "value": {
                            "param": {
                                "maxLength": 200000,
                                "type": "string",
                                "input": "textarea",
                                "markdown": True
                            }
                        }
                    },
                    "recommendation": {
                        "order": 5,
                        "description": "If there are concerns identified, do you think it is possible to address them in the current version of the paper? If so, how do you recommend that they should be addressed? (max 200000 characters). Add formatting using Markdown and formulas using LaTeX.",
                        "value": {
                            "param": {
                                "maxLength": 200000,
                                "type": "string",
                                "input": "textarea",
                                "markdown": True
                            }
                        }
                    }
                },
                'release_submissions_to_ethics_reviewers': 'We confirm we want to release the submissions and reviews to the ethics reviewers'
            },
            forum=request_form.forum,
            referent=request_form.forum,
            invitation='openreview.net/Support/-/Request{}/Ethics_Review_Stage'.format(request_form.number),
            readers=['NeurIPS.cc/2023/Conference/Program_Chairs', 'openreview.net/Support'],
            signatures=['~Program_NeurIPSChair1'],
            writers=[]
        ))

        helpers.await_queue()
        helpers.await_queue(openreview_client)

        pc_client_v2=openreview.api.OpenReviewClient(username='pc@neurips.cc', password=helpers.strong_password)
        note = openreview_client.get_notes(invitation='NeurIPS.cc/2023/Conference/-/Submission', number=1)[0]

        note_edit = pc_client_v2.post_note_edit(
            invitation='NeurIPS.cc/2023/Conference/-/Ethics_Review_Flag',
            note=openreview.api.Note(
                id=note.id,
                content = {
                    'flagged_for_ethics_review': { 'value': True },
                    'ethics_comments': { 'value': 'These are ethics comments visible to ethics chairs and ethics reviewers' }
                }
            ),
            signatures=['NeurIPS.cc/2023/Conference']
        )

        helpers.await_queue()
        helpers.await_queue_edit(openreview_client, edit_id=note_edit['id'])

        openreview_client.add_members_to_group('NeurIPS.cc/2023/Conference/Submission1/Ethics_Reviewers', '~Ethics_ReviewerNeurIPS1')

        submissions = openreview_client.get_notes(content= { 'venueid': 'NeurIPS.cc/2023/Conference/Submission'}, sort='number:asc')
        assert submissions and len(submissions) == 4
        assert 'flagged_for_ethics_review' in submissions[0].content and submissions[0].content['flagged_for_ethics_review']['value']
        assert 'ethics_comments' in submissions[0].content
        assert submissions[0].content['flagged_for_ethics_review']['readers'] == [
            'NeurIPS.cc/2023/Conference',
            'NeurIPS.cc/2023/Conference/Ethics_Chairs',
            'NeurIPS.cc/2023/Conference/Submission1/Ethics_Reviewers',
            'NeurIPS.cc/2023/Conference/Submission1/Senior_Area_Chairs',
            'NeurIPS.cc/2023/Conference/Submission1/Area_Chairs',
            'NeurIPS.cc/2023/Conference/Submission1/Reviewers'
        ]
        ethics_group = openreview.tools.get_group(openreview_client, 'NeurIPS.cc/2023/Conference/Submission1/Ethics_Reviewers')
        assert ethics_group and '~Ethics_ReviewerNeurIPS1' in ethics_group.members
        assert submissions[0].readers == [
            "NeurIPS.cc/2023/Conference",
            "NeurIPS.cc/2023/Conference/Submission1/Senior_Area_Chairs",
            "NeurIPS.cc/2023/Conference/Submission1/Area_Chairs",
            "NeurIPS.cc/2023/Conference/Submission1/Reviewers",
            "NeurIPS.cc/2023/Conference/Submission1/Authors",
            "NeurIPS.cc/2023/Conference/Submission1/Ethics_Reviewers"
        ]
        assert submissions[1].readers == [
            "NeurIPS.cc/2023/Conference",
            "NeurIPS.cc/2023/Conference/Submission2/Senior_Area_Chairs",
            "NeurIPS.cc/2023/Conference/Submission2/Area_Chairs",
            "NeurIPS.cc/2023/Conference/Submission2/Reviewers",
            "NeurIPS.cc/2023/Conference/Submission2/Authors"
        ]

        reviews = openreview_client.get_notes(invitation='NeurIPS.cc/2023/Conference/Submission1/-/Official_Review')
        assert reviews and len(reviews) == 2
        for review in reviews:
            assert 'NeurIPS.cc/2023/Conference/Submission1/Ethics_Reviewers' in review.readers

        invitations = openreview_client.get_invitations(invitation='NeurIPS.cc/2023/Conference/-/Ethics_Review')
        assert len(invitations) == 1
        invitation = openreview_client.get_invitations(id='NeurIPS.cc/2023/Conference/Submission1/-/Ethics_Review')[0]
        assert invitation
        assert 'NeurIPS.cc/2023/Conference/Submission1/Ethics_Reviewers' in invitation.invitees

    def test_release_reviews(self, helpers, openreview_client, request_page, selenium):

        now = datetime.datetime.utcnow()
        due_date = now + datetime.timedelta(days=3)

        pc_client=openreview.Client(username='pc@neurips.cc', password=helpers.strong_password)
        request_form=pc_client.get_notes(invitation='openreview.net/Support/-/Request_Form')[0]
        review_stage_note=pc_client.post_note(openreview.Note(
            content={
                'review_deadline': due_date.strftime('%Y/%m/%d'),
                'make_reviews_public': 'No, reviews should NOT be revealed publicly when they are posted',
                'release_reviews_to_authors': 'Yes, reviews should be revealed when they are posted to the paper\'s authors',
                'release_reviews_to_reviewers': 'Reviews should be immediately revealed to the paper\'s reviewers who have already submitted their review',
                'email_program_chairs_about_reviews': 'No, do not email program chairs about received reviews',
                'remove_review_form_options': 'title,review',
                'additional_review_form_options': {
                    "summary": {
                        "order": 1,
                        "description": "Briefly summarize the paper and its contributions. This is not the place to critique the paper; the authors should generally agree with a well-written summary.",
                        "value": {
                            "param": {
                                "maxLength": 200000,
                                "type": "string",
                                "input": "textarea",
                                "markdown": True
                            }
                        }
                    },
                    "soundness": {
                        "order": 2,
                        "description": "Please assign the paper a numerical rating on the following scale to indicate the soundness of the technical claims, experimental and research methodology and on whether the central claims of the paper are adequately supported with evidence.",
                        "value": {
                            "param": {
                                "type": "string",
                                "enum": [
                                    "4 excellent",
                                    "3 good",
                                    "2 fair",
                                    "1 poor"
                                ],
                                "input": "radio"
                            }
                        }
                    },
                    "presentation": {
                        "order": 3,
                        "description": "Please assign the paper a numerical rating on the following scale to indicate the quality of the presentation. This should take into account the writing style and clarity, as well as contextualization relative to prior work.",
                        "value": {
                            "param": {
                                "type": "string",
                                "enum": [
                                    "4 excellent",
                                    "3 good",
                                    "2 fair",
                                    "1 poor"
                                ],
                                "input": "radio"
                            }
                        }
                    },
                    "contribution": {
                        "order": 4,
                        "description": "Please assign the paper a numerical rating on the following scale to indicate the quality of the overall contribution this paper makes to the research area being studied. Are the questions being asked important? Does the paper bring a significant originality of ideas and/or execution? Are the results valuable to share with the broader NeurIPS community?",
                        "value": {
                            "param": {
                                "type": "string",
                                "enum": [
                                    "4 excellent",
                                    "3 good",
                                    "2 fair",
                                    "1 poor"
                                ],
                                "input": "radio"
                            }
                        }
                    },
                    "strengths": {
                        "order": 5,
                        "description": "A substantive assessment of the strengths of the paper, touching on each of the following dimensions: originality, quality, clarity, and significance. We encourage reviewers to be broad in their definitions of originality and significance. For example, originality may arise from a new definition or problem formulation, creative combinations of existing ideas, application to a new domain, or removing limitations from prior results. You can incorporate Markdown and Latex into your review. See https://openreview.net/faq.",
                        "value": {
                            "param": {
                                "maxLength": 200000,
                                "type": "string",
                                "input": "textarea",
                                "markdown": True
                            }
                        }
                    },
                    "weaknesses": {
                        "order": 6,
                        "description": "A substantive assessment of the weaknesses of the paper. Focus on constructive and actionable insights on how the work could improve towards its stated goals. Be specific, avoid generic remarks. For example, if you believe the contribution lacks novelty, provide references and an explanation as evidence; if you believe experiments are insufficient, explain why and exactly what is missing, etc.",
                        "value": {
                            "param": {
                                "maxLength": 200000,
                                "type": "string",
                                "input": "textarea",
                                "markdown": True
                            }
                        }
                    },
                    "questions": {
                        "order": 7,
                        "description": "Please list up and carefully describe any questions and suggestions for the authors. Think of the things where a response from the author can change your opinion, clarify a confusion or address a limitation. This is important for a productive rebuttal and discussion phase with the authors.",
                        "value": {
                            "param": {
                                "maxLength": 200000,
                                "type": "string",
                                "input": "textarea",
                                "markdown": True
                            }
                        }
                    },
                    "limitations": {
                        "order": 8,
                        "description": " Have the authors adequately addressed the limitations and, if applicable, potential negative societal impact of their work (refer to the checklist guidelines on limitations and broader societal impacts: https://neurips.cc/public/guides/PaperChecklist)? If not, please include constructive suggestions for improvement. Authors should be rewarded rather than punished for being up front about the limitations of their work and any potential negative societal impact.",
                        "value": {
                            "param": {
                                "maxLength": 200000,
                                "type": "string",
                                "input": "textarea",
                                "markdown": True
                            }
                        }
                    },
                    "flag_for_ethics_review": {
                        "order": 10,
                        "description": "If there are ethical issues with this paper, please flag the paper for an ethics review and select area of expertise that would be most useful for the ethics reviewer to have. Please click all that apply. For guidance on when this is appropriate, please review the NeurIPS Code of Ethics (https://neurips.cc/public/EthicsGuidelines) and the Ethics Reviewer Guidelines (https://neurips.cc/Conferences/2023/EthicsGuidelinesForReviewers).",
                        "value": {
                            "param": {
                                "type": "string[]",
                                "enum": [
                                    "No ethics review needed.",
                                    "Ethics review needed: Discrimination / Bias / Fairness Concerns",
                                    "Ethics review needed: Inadequate Data and Algorithm Evaluation",
                                    "Ethics review needed: Inappropriate Potential Applications & Impact  (e.g., human rights concerns)",
                                    "Ethics review needed: Privacy and Security (e.g., consent, surveillance, data storage concern)",
                                    "Ethics review needed: Compliance (e.g., GDPR, copyright, license, terms of use)",
                                    "Ethics review needed: Research Integrity Issues (e.g., plagiarism)",
                                    "Ethics review needed: Responsible Research Practice (e.g., IRB, documentation, research ethics)",
                                    "Ethics review needed: Failure to comply with NeurIPS Code of Ethics (lack of required documentation, safeguards, disclosure, licenses, legal compliance)"
                                ],
                                "input": "checkbox"
                            }
                        }
                    },
                    "rating": {
                        "order": 11,
                        "description": "Please provide an \"overall score\" for this submission.",
                        "value": {
                            "param": {
                                "type": "string",
                                "enum": [
                                    "10: Award quality: Technically flawless paper with groundbreaking impact, with exceptionally strong evaluation, reproducibility, and resources, and no unaddressed ethical considerations.",
                                    "9: Very Strong Accept: Technically flawless paper with groundbreaking impact on at least one area of AI/ML and excellent impact on multiple areas of AI/ML, with flawless evaluation, resources, and reproducibility, and no unaddressed ethical considerations.",
                                    "8: Strong Accept: Technically strong paper, with novel ideas, excellent impact on at least one area, or high-to-excellent impact on multiple areas, with excellent evaluation, resources, and reproducibility, and no unaddressed ethical considerations.",
                                    "7: Accept: Technically solid paper, with high impact on at least one sub-area, or moderate-to-high impact on more than one areas, with good-to-excellent evaluation, resources, reproducibility, and no unaddressed ethical considerations.",
                                    "6: Weak Accept: Technically solid, moderate-to-high impact paper, with no major concerns with respect to evaluation, resources, reproducibility, ethical considerations.",
                                    "5: Borderline accept: Technically solid paper where reasons to accept outweigh reasons to reject, e.g., limited evaluation. Please use sparingly.",
                                    "4: Borderline reject: Technically solid paper where reasons to reject, e.g., limited evaluation, outweigh reasons to accept, e.g., good evaluation. Please use sparingly.",
                                    "3: Reject: For instance, a paper with technical flaws, weak evaluation, inadequate reproducibility and incompletely addressed ethical considerations.",
                                    "2: Strong Reject: For instance, a paper with major technical flaws, and/or poor evaluation, limited impact, poor reproducibility and mostly unaddressed ethical considerations.",
                                    "1: Very Strong Reject: For instance, a paper with trivial results or unaddressed ethical considerations"
                                ],
                                "input": "radio"
                            }
                        }
                    },
                    "confidence": {
                        "order": 12,
                        "description": "Please provide a \"confidence score\" for your assessment of this submission to indicate how confident you are in your evaluation.",
                        "value": {
                            "param": {
                                "type": "string",
                                "enum": [
                                    "5: You are absolutely certain about your assessment. You are very familiar with the related work and checked the math/other details carefully.",
                                    "4: You are confident in your assessment, but not absolutely certain. It is unlikely, but not impossible, that you did not understand some parts of the submission or that you are unfamiliar with some pieces of related work.",
                                    "3: You are fairly confident in your assessment. It is possible that you did not understand some parts of the submission or that you are unfamiliar with some pieces of related work. Math/other details were not carefully checked.",
                                    "2: You are willing to defend your assessment, but it is quite likely that you did not understand the central parts of the submission or that you are unfamiliar with some pieces of related work. Math/other details were not carefully checked.",
                                    "1: Your assessment is an educated guess. The submission is not in your area or the submission was difficult to understand. Math/other details were not carefully checked."
                                ],
                                "input": "radio"
                            }
                        }
                    },
                    "code_of_conduct": {
                        "description": "While performing my duties as a reviewer (including writing reviews and participating in discussions), I have and will continue to abide by the NeurIPS code of conduct (https://nips.cc/public/CodeOfConduct).",
                        "order": 13,
                        "value": {
                            "param": {
                                "type": "string",
                                "enum": [
                                    "Yes"
                                ],
                                "input": "checkbox"
                            }
                        }
                    },
                    "first_time_reviewer": {
                        "description": "Is this your first time reviewing for NeurIPS?",
                        "order": 14,
                        "value": {
                            "param": {
                                "type": "string",
                                "enum": [
                                    "Yes"
                                ],
                                "input": "checkbox",
                                "optional": True
                            }
                        }
                    }
                }
            },
            forum=request_form.forum,
            invitation='openreview.net/Support/-/Request{}/Review_Stage'.format(request_form.number),
            readers=['NeurIPS.cc/2023/Conference/Program_Chairs', 'openreview.net/Support'],
            referent=request_form.forum,
            replyto=request_form.forum,
            signatures=['~Program_NeurIPSChair1'],
            writers=[]
        ))

        helpers.await_queue()

        reviewer_client=openreview.api.OpenReviewClient(username='reviewer1@umass.edu', password=helpers.strong_password)
        anon_groups = reviewer_client.get_groups(prefix='NeurIPS.cc/2023/Conference/Submission1/Reviewer_', signatory='~Reviewer_UMass1')
        anon_group_id = anon_groups[0].id

        reviews = openreview_client.get_notes(invitation='NeurIPS.cc/2023/Conference/Submission1/-/Official_Review', sort='number:asc')
        assert len(reviews) == 2
        assert reviews[0].readers == [
            'NeurIPS.cc/2023/Conference/Program_Chairs',
            'NeurIPS.cc/2023/Conference/Submission1/Senior_Area_Chairs',
            'NeurIPS.cc/2023/Conference/Submission1/Area_Chairs',
            'NeurIPS.cc/2023/Conference/Submission1/Reviewers/Submitted',
            'NeurIPS.cc/2023/Conference/Submission1/Authors',
            'NeurIPS.cc/2023/Conference/Submission1/Ethics_Reviewers',
            reviews[0].signatures[0]
        ]

    def test_rebuttal_stage(self, helpers, test_client, openreview_client, client, selenium, request_page):

        pc_client=openreview.Client(username='pc@neurips.cc', password=helpers.strong_password)
        pc_client_v2=openreview.api.OpenReviewClient(username='pc@neurips.cc', password=helpers.strong_password)
        request_form=pc_client.get_notes(invitation='openreview.net/Support/-/Request_Form')[0]

        invitation = client.get_invitation(f'openreview.net/Support/-/Request{request_form.number}/Rebuttal_Stage')
        invitation.cdate = openreview.tools.datetime_millis(datetime.datetime.utcnow())
        client.post_invitation(invitation)

        # post a rebuttal stage note to enbale one rebuttal per review
        now = datetime.datetime.utcnow()
        start_date = now - datetime.timedelta(days=2)
        due_date = now + datetime.timedelta(days=3)
        pc_client.post_note(openreview.Note(
            content={
                'rebuttal_start_date': start_date.strftime('%Y/%m/%d'),
                'rebuttal_deadline': due_date.strftime('%Y/%m/%d'),
                'number_of_rebuttals': 'One author rebuttal per posted review',
                'rebuttal_readers': ['Assigned Senior Area Chairs', 'Assigned Area Chairs'],
                'additional_rebuttal_form_options': {
                    'rebuttal': {
                        'order': 1,
                        'description': 'Rebuttals can include Markdown formatting and LaTeX forumulas, for more information see https://openreview.net/faq , max length: 1500',
                        'value': {
                            'param': {
                                'type': 'string',
                                'maxLength': 5000,
                                'markdown': True,
                                'input': 'textarea'
                            }
                        }
                    }
                },
                'email_program_chairs_about_rebuttals': 'No, do not email program chairs about received rebuttals'
            },
            forum=request_form.forum,
            invitation=f'openreview.net/Support/-/Request{request_form.number}/Rebuttal_Stage',
            readers=['NeurIPS.cc/2023/Conference/Program_Chairs', 'openreview.net/Support'],
            replyto=request_form.forum,
            referent=request_form.forum,
            signatures=['~Program_NeurIPSChair1'],
            writers=[]
        ))

        helpers.await_queue()

        submissions = openreview_client.get_notes(invitation='NeurIPS.cc/2023/Conference/-/Submission', sort='number:asc')
        reviews = pc_client_v2.get_notes(invitation='NeurIPS.cc/2023/Conference/Submission1/-/Official_Review')
        review = reviews[0]

        assert len(openreview_client.get_invitations(invitation='NeurIPS.cc/2023/Conference/-/Rebuttal')) == 2
        invitation = openreview_client.get_invitation(f'{review.signatures[0]}/-/Rebuttal')
        assert invitation.maxReplies == 1
        assert invitation.edit['note']['replyto'] == review.id

        test_client = openreview.api.OpenReviewClient(username='test@mail.com', password=helpers.strong_password)

        rebuttal_edit = test_client.post_note_edit(
            invitation=f'{review.signatures[0]}/-/Rebuttal',
            signatures=['NeurIPS.cc/2023/Conference/Submission1/Authors'],
            note=openreview.api.Note(
                replyto = review.id,
                content={
                    'rebuttal': { 'value': 'This is a rebuttal reply to an official review.' }
                }
            )
        )

        helpers.await_queue(openreview_client)

        rebuttal = openreview_client.get_note(rebuttal_edit['note']['id'])
        assert rebuttal.readers == [
            'NeurIPS.cc/2023/Conference/Program_Chairs',
            'NeurIPS.cc/2023/Conference/Submission1/Senior_Area_Chairs',
            'NeurIPS.cc/2023/Conference/Submission1/Area_Chairs',
            'NeurIPS.cc/2023/Conference/Submission1/Authors'
        ]

        with pytest.raises(openreview.OpenReviewException, match=r'.*You have reached the maximum number \(1\) of replies for this Invitation.*'):
            rebuttal_edit = test_client.post_note_edit(
                invitation=f'{review.signatures[0]}/-/Rebuttal',
                signatures=['NeurIPS.cc/2023/Conference/Submission1/Authors'],
                note=openreview.api.Note(
                    replyto = review.id,
                    content={
                        'rebuttal': { 'value': 'This is another rebuttal reply to the same official review.' }
                    }
                )
            )

        # use custom stage to enable one author rebuttal per paper
        venue = openreview.get_conference(client, request_form.id, support_user='openreview.net/Support')

        now = datetime.datetime.utcnow()
        due_date = now + datetime.timedelta(days=3)
        venue.custom_stage = openreview.stages.CustomStage(name='Author_Rebuttal',
            reply_to=openreview.stages.CustomStage.ReplyTo.FORUM,
            source=openreview.stages.CustomStage.Source.ALL_SUBMISSIONS,
            due_date=due_date,
            exp_date=due_date + datetime.timedelta(days=1),
            invitees=[openreview.stages.CustomStage.Participants.AUTHORS],
            readers=[openreview.stages.CustomStage.Participants.SENIOR_AREA_CHAIRS_ASSIGNED, openreview.stages.CustomStage.Participants.AREA_CHAIRS_ASSIGNED, openreview.stages.CustomStage.Participants.AUTHORS],
            content={
                'rebuttal': {
                    'order': 1,
                    'description': 'Rebuttals can include Markdown formatting and LaTeX forumulas, for more information see https://openreview.net/faq , max length: 2500',
                    'value': {
                        'param': {
                            'type': 'string',
                            'maxLength': 5000,
                            'markdown': True,
                            'input': 'textarea'
                        }
                    }
                },
                'pdf': {
                    'order': 2,
                    'description': 'Upload a PDF file that ends with .pdf.',
                    'value': {
                        'param': {
                            'type': 'file',
                            'maxSize': 50,
                            'extensions': ['pdf'],
                            'optional': True
                        }
                    }
                }
            },
            notify_readers=False,
            email_sacs=False)

        venue.create_custom_stage()

        invitations = openreview_client.get_all_invitations(invitation='NeurIPS.cc/2023/Conference/-/Author_Rebuttal')
        assert len(invitations) == 4
        invitation = openreview_client.get_invitation('NeurIPS.cc/2023/Conference/Submission1/-/Author_Rebuttal')
        assert invitation.maxReplies == 1
        assert invitation.edit['note']['replyto'] == submissions[0].id

        rebuttal_edit = test_client.post_note_edit(
            invitation='NeurIPS.cc/2023/Conference/Submission1/-/Author_Rebuttal',
            signatures=['NeurIPS.cc/2023/Conference/Submission1/Authors'],
            note=openreview.api.Note(
                replyto = submissions[0].id,
                content={
                    'rebuttal': { 'value': 'This is a rebuttal reply to a submission.' },
                    'pdf': { 'value': '/attachment/' + 's' * 40 +'.pdf' }
                }
            )
        )

        helpers.await_queue(openreview_client)

        rebuttal = openreview_client.get_note(rebuttal_edit['note']['id'])
        assert rebuttal.readers == [
            'NeurIPS.cc/2023/Conference/Program_Chairs',
            'NeurIPS.cc/2023/Conference/Submission1/Senior_Area_Chairs',
            'NeurIPS.cc/2023/Conference/Submission1/Area_Chairs',
            'NeurIPS.cc/2023/Conference/Submission1/Authors'
        ]

        forum_url = 'http://localhost:3030/forum?id=' + submissions[0].id
        request_page(selenium, forum_url, test_client.token, wait_for_element='5-metareview-status')

        note_panel = selenium.find_element(By.XPATH, f'//div[@data-id="{rebuttal.id}"]')
        fields = note_panel.find_elements(By.CLASS_NAME, 'note-content-field')
        assert len(fields) == 2
        assert fields[0].text == 'Rebuttal:'
        assert fields[1].text == 'PDF:'

        with pytest.raises(openreview.OpenReviewException, match=r'.*You have reached the maximum number \(1\) of replies for this Invitation.*'):
            rebuttal_edit = test_client.post_note_edit(
                invitation='NeurIPS.cc/2023/Conference/Submission1/-/Author_Rebuttal',
                signatures=['NeurIPS.cc/2023/Conference/Submission1/Authors'],
                note=openreview.api.Note(
                    replyto = submissions[0].id,
                    content={
                        'rebuttal': { 'value': 'This is a another reply to a submission.' }
                    }
                )
            )

    def test_release_rebuttals(self, helpers, test_client, openreview_client, client):

        pc_client=openreview.Client(username='pc@neurips.cc', password=helpers.strong_password)
        pc_client_v2=openreview.api.OpenReviewClient(username='pc@neurips.cc', password=helpers.strong_password)
        request_form=pc_client.get_notes(invitation='openreview.net/Support/-/Request_Form')[0]

        # release rebuttals to reviewers
        now = datetime.datetime.utcnow()
        start_date = now - datetime.timedelta(days=2)
        due_date = now + datetime.timedelta(days=3)
        pc_client.post_note(openreview.Note(
            content={
                'rebuttal_start_date': start_date.strftime('%Y/%m/%d'),
                'rebuttal_deadline': due_date.strftime('%Y/%m/%d'),
                'number_of_rebuttals': 'One author rebuttal per posted review',
                'rebuttal_readers': ['Assigned Senior Area Chairs', 'Assigned Area Chairs', 'Assigned Reviewers who already submitted their review'],
                'additional_rebuttal_form_options': {
                    'rebuttal': {
                        'order': 1,
                        'description': 'Rebuttals can include Markdown formatting and LaTeX forumulas, for more information see https://openreview.net/faq , max length: 1500',
                        'value': {
                            'param': {
                                'type': 'string',
                                'maxLength': 5000,
                                'markdown': True,
                                'input': 'textarea'
                            }
                        }
                    }
                },
                'email_program_chairs_about_rebuttals': 'No, do not email program chairs about received rebuttals'
            },
            forum=request_form.forum,
            invitation=f'openreview.net/Support/-/Request{request_form.number}/Rebuttal_Stage',
            readers=['NeurIPS.cc/2023/Conference/Program_Chairs', 'openreview.net/Support'],
            replyto=request_form.forum,
            referent=request_form.forum,
            signatures=['~Program_NeurIPSChair1'],
            writers=[]
        ))

        helpers.await_queue()


        reviews = pc_client_v2.get_notes(invitation='NeurIPS.cc/2023/Conference/Submission1/-/Official_Review')
        review = reviews[0]

        rebuttal = openreview_client.get_notes(invitation=f'{review.signatures[0]}/-/Rebuttal')[0]
        assert rebuttal.readers == [
            'NeurIPS.cc/2023/Conference/Program_Chairs',
            'NeurIPS.cc/2023/Conference/Submission1/Senior_Area_Chairs',
            'NeurIPS.cc/2023/Conference/Submission1/Area_Chairs',
            'NeurIPS.cc/2023/Conference/Submission1/Reviewers/Submitted',
            'NeurIPS.cc/2023/Conference/Submission1/Authors'
        ]

        venue = openreview.get_conference(client, request_form.id, support_user='openreview.net/Support')

        # release author rebuttals with custom stage
        now = datetime.datetime.utcnow()
        due_date = now + datetime.timedelta(days=3)
        venue.custom_stage = openreview.stages.CustomStage(name='Author_Rebuttal',
            reply_to=openreview.stages.CustomStage.ReplyTo.FORUM,
            source=openreview.stages.CustomStage.Source.ALL_SUBMISSIONS,
            due_date=due_date,
            exp_date=due_date + datetime.timedelta(days=1),
            invitees=[openreview.stages.CustomStage.Participants.AUTHORS],
            readers=[openreview.stages.CustomStage.Participants.SENIOR_AREA_CHAIRS_ASSIGNED, openreview.stages.CustomStage.Participants.AREA_CHAIRS_ASSIGNED, openreview.stages.CustomStage.Participants.REVIEWERS_SUBMITTED, openreview.stages.CustomStage.Participants.AUTHORS],
            content={
                'rebuttal': {
                    'order': 1,
                    'description': 'Rebuttals can include Markdown formatting and LaTeX forumulas, for more information see https://openreview.net/faq , max length: 2500',
                    'value': {
                        'param': {
                            'type': 'string',
                            'maxLength': 5000,
                            'markdown': True,
                            'input': 'textarea'
                        }
                    }
                },
                'pdf': {
                    'order': 2,
                    'description': 'Upload a PDF file that ends with .pdf.',
                    'value': {
                        'param': {
                            'type': 'file',
                            'maxSize': 50,
                            'extensions': ['pdf'],
                            'optional': True
                        }
                    }
                }
            },
            notify_readers=False,
            email_sacs=False)

        venue.create_custom_stage()

        rebuttal = openreview_client.get_notes(invitation='NeurIPS.cc/2023/Conference/Submission1/-/Author_Rebuttal')[0]
        assert rebuttal.readers == [
            'NeurIPS.cc/2023/Conference/Program_Chairs',
            'NeurIPS.cc/2023/Conference/Submission1/Senior_Area_Chairs',
            'NeurIPS.cc/2023/Conference/Submission1/Area_Chairs',
            'NeurIPS.cc/2023/Conference/Submission1/Reviewers/Submitted',
            'NeurIPS.cc/2023/Conference/Submission1/Authors'
        ]

    def test_discussion_stage(self, helpers, test_client, openreview_client):

        pc_client=openreview.Client(username='pc@neurips.cc', password=helpers.strong_password)
        request_form=pc_client.get_notes(invitation='openreview.net/Support/-/Request_Form')[0]

        # Post an official comment stage note
        now = datetime.datetime.utcnow()
        start_date = now - datetime.timedelta(days=2)
        end_date = now + datetime.timedelta(days=3)
        comment_stage_note = pc_client.post_note(openreview.Note(
            content={
                'commentary_start_date': start_date.strftime('%Y/%m/%d'),
                'commentary_end_date': end_date.strftime('%Y/%m/%d'),
                'participants': ['Program Chairs', 'Assigned Senior Area Chairs', 'Assigned Area Chairs', 'Assigned Reviewers', 'Authors'],
                'additional_readers': ['Program Chairs'],
                'email_program_chairs_about_official_comments': 'No, do not email PCs for each official comment made in the venue'
            },
            forum=request_form.forum,
            invitation=f'openreview.net/Support/-/Request{request_form.number}/Comment_Stage',
            readers=['NeurIPS.cc/2023/Conference/Program_Chairs', 'openreview.net/Support'],
            replyto=request_form.forum,
            referent=request_form.forum,
            signatures=['~Program_NeurIPSChair1'],
            writers=[]
        ))

        helpers.await_queue()

        invitation = openreview_client.get_invitation('NeurIPS.cc/2023/Conference/Submission1/-/Official_Comment')
        assert invitation
        assert invitation.invitees == [
            'NeurIPS.cc/2023/Conference',
            'openreview.net/Support',
            'NeurIPS.cc/2023/Conference/Submission1/Senior_Area_Chairs',
            'NeurIPS.cc/2023/Conference/Submission1/Area_Chairs',
            'NeurIPS.cc/2023/Conference/Submission1/Reviewers',
            'NeurIPS.cc/2023/Conference/Submission1/Authors'
        ]

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

#         status = selenium.find_element(By.ID, '5-metareview-status')
#         assert status

#         assert not status.find_elements(By.CLASS_NAME, 'tag-widget')

#         reviewer_client=openreview.Client(username='reviewer1@umass.edu', password=helpers.strong_password)

#         signatory_groups=client.get_groups(regex='NeurIPS.cc/2023/Conference/Paper5/Reviewer_', signatory='reviewer1@umass.edu')
#         assert len(signatory_groups) == 1
#         reviewer_anon_id=signatory_groups[0].id

#         reviewer_url = 'http://localhost:3030/group?id=NeurIPS.cc/2023/Conference/Reviewers'
#         request_page(selenium, reviewer_url, reviewer_client.token)

#         assert not selenium.find_elements(By.CLASS_NAME, 'tag-widget')

#         now = datetime.datetime.utcnow()
#         conference.open_paper_ranking(conference.get_area_chairs_id(), due_date=now + datetime.timedelta(minutes = 40))
#         conference.open_paper_ranking(conference.get_reviewers_id(), due_date=now + datetime.timedelta(minutes = 40))

#         ac_url = 'http://localhost:3030/group?id=NeurIPS.cc/2023/Conference/Area_Chairs'
#         request_page(selenium, ac_url, ac_client.token, by=By.ID, wait_for_element='5-metareview-status')

#         status = selenium.find_element(By.ID, '5-metareview-status')
#         assert status

#         tag = status.find_element(By.CLASS_NAME, 'tag-widget')
#         assert tag

#         options = tag.find_elements(By.TAG_NAME, 'li')
#         assert options
#         assert len(options) == 3

#         options = tag.find_elements(By.TAG_NAME, 'a')
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

#         tags = selenium.find_elements(By.CLASS_NAME, 'tag-widget')
#         assert tags

#         options = tags[0].find_elements(By.TAG_NAME, 'li')
#         assert options
#         assert len(options) == 5

#         options = tags[0].find_elements(By.TAG_NAME, 'a')
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
#         notes_panel = selenium.find_element(By.ID, 'notes')
#         assert notes_panel
#         tabs = notes_panel.find_element(By.CLASS_NAME, 'tabs-container')
#         assert tabs
#         assert tabs.find_element(By.ID, 'venue-configuration')
#         assert tabs.find_element(By.ID, 'paper-status')
#         assert tabs.find_element(By.ID, 'reviewer-status')
#         assert tabs.find_element(By.ID, 'areachair-status')

#         assert '#' == tabs.find_element(By.ID, 'paper-status').find_element(By.CLASS_NAME, 'row-1').text
#         assert 'Paper Summary' == tabs.find_element(By.ID, 'paper-status').find_element(By.CLASS_NAME, 'row-2').text
#         assert 'Review Progress' == tabs.find_element(By.ID, 'paper-status').find_element(By.CLASS_NAME, 'row-3').text
#         assert 'Status' == tabs.find_element(By.ID, 'paper-status').find_element(By.CLASS_NAME, 'row-4').text
#         assert 'Decision' == tabs.find_element(By.ID, 'paper-status').find_element(By.CLASS_NAME, 'row-5').text

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
