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

    def test_create_conference(self, client, helpers):

        now = datetime.datetime.utcnow()
        due_date = now + datetime.timedelta(days=3)

        # Post the request form note
        pc_client=helpers.create_user('pc@neurips.cc', 'Program', 'NeurIPSChair')

        helpers.create_user('sac1@google.com', 'SeniorArea', 'GoogleChair', institution='google.com')
        helpers.create_user('sac2@gmail.com', 'SeniorArea', 'NeurIPSChair')
        helpers.create_user('ac1@mit.edu', 'Area', 'IBMChair', institution='ibm.com')
        helpers.create_user('ac2@gmail.com', 'Area', 'GoogleChair', institution='google.com')
        helpers.create_user('ac3@umass.edu', 'Area', 'UMassChair', institution='umass.edu')
        helpers.create_user('reviewer1@umass.edu', 'Reviewer', 'UMass', institution='umass.edu')
        helpers.create_user('reviewer2@mit.edu', 'Reviewer', 'MIT', institution='mit.edu')

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
                'Abbreviated Venue Name': 'NeurIPS 2021',
                'Official Website URL': 'https://neurips.cc',
                'program_chair_emails': ['pc@neurips.cc'],
                'contact_email': 'pc@neurips.cc',
                'Area Chairs (Metareviewers)': 'Yes, our venue has Area Chairs',
                'senior_area_chairs': 'Yes, our venue has Senior Area Chairs',
                'Venue Start Date': '2021/12/01',
                'Submission Deadline': due_date.strftime('%Y/%m/%d'),
                'Location': 'Virtual',
                'Paper Matching': [
                    'Reviewer Bid Scores',
                    'Reviewer Recommendation Scores'],
                'Author and Reviewer Anonymity': 'Double-blind',
                'Open Reviewing Policy': 'Submissions and reviews should both be private.',
                'How did you hear about us?': 'ML conferences',
                'Expected Submissions': '100'
            }))

        helpers.await_queue()

        # Post a deploy note
        client.post_note(openreview.Note(
            content={'venue_id': 'NeurIPS.cc/2021/Conference'},
            forum=request_form_note.forum,
            invitation='openreview.net/Support/-/Request{}/Deploy'.format(request_form_note.number),
            readers=['openreview.net/Support'],
            referent=request_form_note.forum,
            replyto=request_form_note.forum,
            signatures=['openreview.net/Support'],
            writers=['openreview.net/Support']
        ))

        helpers.await_queue()

        assert client.get_group('NeurIPS.cc/2021/Conference')

    def test_recruit_senior_area_chairs(self, client, selenium, request_page, helpers):

        pc_client=openreview.Client(username='pc@neurips.cc', password='1234')
        request_form=pc_client.get_notes(invitation='openreview.net/Support/-/Request_Form')[0]

        # Test Reviewer Recruitment
        request_page(selenium, 'http://localhost:3030/forum?id={}'.format(request_form.id), pc_client.token)
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
                'invitee_role': 'senior area chair',
                'invitee_details': reviewer_details,
                'invitation_email_subject': '[' + request_form.content['Abbreviated Venue Name'] + '] Invitation to serve as {invitee_role}',
                'invitation_email_content': 'Dear {name},\n\nYou have been nominated by the program chair committee of Theoretical Foundations of RL Workshop @ ICML 2020 to serve as {invitee_role}.\n\nACCEPT LINK:\n\n{accept_url}\n\nDECLINE LINK:\n\n{decline_url}\n\nCheers!\n\nProgram Chairs'
            },
            forum=request_form.forum,
            replyto=request_form.forum,
            invitation='openreview.net/Support/-/Request{}/Recruitment'.format(request_form.number),
            readers=['NeurIPS.cc/2021/Conference/Program_Chairs', 'openreview.net/Support'],
            signatures=['~Program_NeurIPSChair1'],
            writers=[]
        ))
        assert recruitment_note

        helpers.await_queue()
        process_logs = client.get_process_logs(id=recruitment_note.id)
        assert len(process_logs) == 1
        assert process_logs[0]['status'] == 'ok'
        assert process_logs[0]['invitation'] == 'openreview.net/Support/-/Request{}/Recruitment'.format(request_form.number)

        messages = client.get_messages(to='sac1@google.com', subject='[NeurIPS 2021] Invitation to serve as senior area chair')
        assert messages and len(messages) == 1
        assert messages[0]['content']['subject'] == '[NeurIPS 2021] Invitation to serve as senior area chair'
        assert messages[0]['content']['text'].startswith('Dear SAC One,\n\nYou have been nominated by the program chair committee of Theoretical Foundations of RL Workshop @ ICML 2020 to serve as senior area chair.')
        accept_url = re.search('https://.*response=Yes', messages[0]['content']['text']).group(0).replace('https://openreview.net', 'http://localhost:3030')
        request_page(selenium, accept_url, alert=True)

        messages = client.get_messages(to='sac2@gmail.com', subject='[NeurIPS 2021] Invitation to serve as senior area chair')
        assert messages and len(messages) == 1
        assert messages[0]['content']['subject'] == '[NeurIPS 2021] Invitation to serve as senior area chair'
        assert messages[0]['content']['text'].startswith('Dear SAC Two,\n\nYou have been nominated by the program chair committee of Theoretical Foundations of RL Workshop @ ICML 2020 to serve as senior area chair.')
        accept_url = re.search('https://.*response=Yes', messages[0]['content']['text']).group(0).replace('https://openreview.net', 'http://localhost:3030')
        request_page(selenium, accept_url, alert=True)

        helpers.await_queue()
        assert client.get_group('NeurIPS.cc/2021/Conference/Senior_Area_Chairs').members == ['sac1@google.com', 'sac2@gmail.com']

    def test_recruit_area_chairs(self, client, selenium, request_page, helpers):

        pc_client=openreview.Client(username='pc@neurips.cc', password='1234')
        pc_client.add_members_to_group('NeurIPS.cc/2021/Conference/Area_Chairs', ['~Area_IBMChair1', '~Area_GoogleChair1', '~Area_UMassChair1'])

    def test_sac_bidding(self, client, helpers):

        pc_client=openreview.Client(username='pc@neurips.cc', password='1234')
        request_form=pc_client.get_notes(invitation='openreview.net/Support/-/Request_Form')[0]

        conference=openreview.helpers.get_conference(pc_client, request_form.id)

        conference.setup_matching(committee_id='NeurIPS.cc/2021/Conference/Senior_Area_Chairs', build_conflicts=True, affinity_score_file=os.path.join(os.path.dirname(__file__), 'data/sac_affinity_scores.csv'))
        now = datetime.datetime.utcnow()
        conference.set_bid_stage(openreview.BidStage(due_date=now + datetime.timedelta(days=3), committee_id='NeurIPS.cc/2021/Conference/Senior_Area_Chairs', score_ids=['NeurIPS.cc/2021/Conference/Senior_Area_Chairs/-/Affinity_Score']))

        edges=pc_client.get_edges(invitation='NeurIPS.cc/2021/Conference/Senior_Area_Chairs/-/Conflict')
        assert len(edges) == 1
        assert edges[0].head == '~Area_GoogleChair1'
        assert edges[0].tail == '~SeniorArea_GoogleChair1'

        edges=pc_client.get_edges(invitation='NeurIPS.cc/2021/Conference/Senior_Area_Chairs/-/Affinity_Score')
        assert len(edges) == 6

        invitation=pc_client.get_invitation('NeurIPS.cc/2021/Conference/Senior_Area_Chairs/-/Assignment_Configuration')
        assert invitation
        assert invitation.reply['content']['paper_invitation']['value-regex'] == 'NeurIPS.cc/2021/Conference/Area_Chairs'
        assert invitation.reply['content']['paper_invitation']['default'] == 'NeurIPS.cc/2021/Conference/Area_Chairs'


    def test_recruit_reviewers(self, client, selenium, request_page, helpers):

        pc_client=openreview.Client(username='pc@neurips.cc', password='1234')
        request_form=pc_client.get_notes(invitation='openreview.net/Support/-/Request_Form')[0]

        # Test Reviewer Recruitment
        request_page(selenium, 'http://localhost:3030/forum?id={}'.format(request_form.id), pc_client.token)
        recruitment_div = selenium.find_element_by_id('note_{}'.format(request_form.id))
        assert recruitment_div
        reply_row = recruitment_div.find_element_by_class_name('reply_row')
        assert reply_row
        buttons = reply_row.find_elements_by_class_name('btn-xs')
        assert [btn for btn in buttons if btn.text == 'Recruitment']


        reviewer_details = '''reviewer1@umass.edu, Reviewer UMass\nreviewer2@mit.edu, Reviewer MIT'''
        recruitment_note = pc_client.post_note(openreview.Note(
            content={
                'title': 'Recruitment',
                'invitee_role': 'reviewer',
                'invitee_reduced_load': ['2', '3', '4'],
                'invitee_details': reviewer_details,
                'invitation_email_subject': '[' + request_form.content['Abbreviated Venue Name'] + '] Invitation to serve as {invitee_role}',
                'invitation_email_content': 'Dear {name},\n\nYou have been nominated by the program chair committee of Theoretical Foundations of RL Workshop @ ICML 2020 to serve as {invitee_role}.\n\nACCEPT LINK:\n\n{accept_url}\n\nDECLINE LINK:\n\n{decline_url}\n\nCheers!\n\nProgram Chairs'
            },
            forum=request_form.forum,
            replyto=request_form.forum,
            invitation='openreview.net/Support/-/Request{}/Recruitment'.format(request_form.number),
            readers=['NeurIPS.cc/2021/Conference/Program_Chairs', 'openreview.net/Support'],
            signatures=['~Program_NeurIPSChair1'],
            writers=[]
        ))
        assert recruitment_note

        helpers.await_queue()
        process_logs = client.get_process_logs(id=recruitment_note.id)
        assert len(process_logs) == 1
        assert process_logs[0]['status'] == 'ok'
        assert process_logs[0]['invitation'] == 'openreview.net/Support/-/Request{}/Recruitment'.format(request_form.number)

        messages = client.get_messages(to='reviewer1@umass.edu', subject='[NeurIPS 2021] Invitation to serve as reviewer')
        assert messages and len(messages) == 1
        assert messages[0]['content']['subject'] == '[NeurIPS 2021] Invitation to serve as reviewer'
        assert messages[0]['content']['text'].startswith('Dear Reviewer UMass,\n\nYou have been nominated by the program chair committee of Theoretical Foundations of RL Workshop @ ICML 2020 to serve as reviewer.')
        reject_url = re.search('https://.*response=No', messages[0]['content']['text']).group(0).replace('https://openreview.net', 'http://localhost:3030')
        request_page(selenium, reject_url, alert=True)
        notes = selenium.find_element_by_id("notes")
        assert notes
        messages = notes.find_elements_by_tag_name("h3")
        assert messages
        assert 'You have declined the invitation from Conference on Neural Information Processing Systems.' == messages[0].text
        assert 'In case you only declined because you think you cannot handle the maximum load of papers, you can reduce your load slightly. Be aware that this will decrease your overall score for an outstanding reviewer award, since all good reviews will accumulate a positive score. You can request a reduced reviewer load by clicking here: Request reduced load' == messages[1].text

        assert len(client.get_group('NeurIPS.cc/2021/Conference/Reviewers').members) == 0

        group = client.get_group('NeurIPS.cc/2021/Conference/Reviewers/Declined')
        assert group
        assert len(group.members) == 1
        assert 'reviewer1@umass.edu' in group.members

        messages = client.get_messages(to='reviewer1@umass.edu', subject='[NeurIPS 2021] Reviewer Invitation declined')
        assert messages
        assert len(messages)
        assert messages[0]['content']['text'].startswith('You have declined the invitation to become a Reviewer for NeurIPS 2021.\n\nIf you would like to change your decision, please click the Accept link in the previous invitation email.\n\nIn case you only declined because you think you cannot handle the maximum load of papers, you can reduce your load slightly. Be aware that this will decrease your overall score for an outstanding reviewer award, since all good reviews will accumulate a positive score. You can request a reduced reviewer load by clicking here:')

        notes = client.get_notes(invitation='NeurIPS.cc/2021/Conference/-/Recruit_Reviewers', content={'user': 'reviewer1@umass.edu'})
        assert notes
        assert len(notes) == 1

        client.post_note(openreview.Note(
            invitation='NeurIPS.cc/2021/Conference/-/Reduced_Load',
            readers=['NeurIPS.cc/2021/Conference', 'reviewer1@umass.edu'],
            writers=['NeurIPS.cc/2021/Conference'],
            signatures=['(anonymous)'],
            content={
                'user': 'reviewer1@umass.edu',
                'key': notes[0].content['key'],
                'response': 'Yes',
                'reviewer_load': '4'
            }
        ))

        helpers.await_queue()

        reviewers_group=client.get_group('NeurIPS.cc/2021/Conference/Reviewers')
        assert len(reviewers_group.members) == 1
        assert 'reviewer1@umass.edu' in reviewers_group.members

        ## Remind reviewers
        recruitment_note = pc_client.post_note(openreview.Note(
            content={
                'title': 'Remind Recruitment',
                'invitee_role': 'reviewer',
                'invitee_reduced_load': ['2', '3', '4'],
                'invitation_email_subject': '[' + request_form.content['Abbreviated Venue Name'] + '] Invitation to serve as {invitee_role}',
                'invitation_email_content': 'Dear {name},\n\nYou have been nominated by the program chair committee of Theoretical Foundations of RL Workshop @ ICML 2020 to serve as {invitee_role}.\n\nACCEPT LINK:\n\n{accept_url}\n\nDECLINE LINK:\n\n{decline_url}\n\nCheers!\n\nProgram Chairs'
            },
            forum=request_form.forum,
            replyto=request_form.forum,
            invitation='openreview.net/Support/-/Request{}/Remind_Recruitment'.format(request_form.number),
            readers=['NeurIPS.cc/2021/Conference/Program_Chairs', 'openreview.net/Support'],
            signatures=['~Program_NeurIPSChair1'],
            writers=[]
        ))

        helpers.await_queue()

        messages = client.get_messages(to='reviewer2@mit.edu', subject='Reminder: [NeurIPS 2021] Invitation to serve as reviewer')
        assert messages and len(messages) == 1
        assert messages[0]['content']['subject'] == 'Reminder: [NeurIPS 2021] Invitation to serve as reviewer'
        assert messages[0]['content']['text'].startswith('Dear invitee,\n\nYou have been nominated by the program chair committee of Theoretical Foundations of RL Workshop @ ICML 2020 to serve as reviewer.')
        reject_url = re.search('https://.*response=No', messages[0]['content']['text']).group(0).replace('https://openreview.net', 'http://localhost:3030')
        request_page(selenium, reject_url, alert=True)

        helpers.await_queue()

        group = client.get_group('NeurIPS.cc/2021/Conference/Reviewers/Declined')
        assert group
        assert len(group.members) == 1
        assert 'reviewer2@mit.edu' in group.members

        messages = client.get_messages(to='reviewer2@mit.edu', subject='[NeurIPS 2021] Reviewer Invitation declined')
        assert messages
        assert len(messages)
        assert messages[0]['content']['text'].startswith('You have declined the invitation to become a Reviewer for NeurIPS 2021.\n\nIf you would like to change your decision, please click the Accept link in the previous invitation email.\n\nIn case you only declined because you think you cannot handle the maximum load of papers, you can reduce your load slightly. Be aware that this will decrease your overall score for an outstanding reviewer award, since all good reviews will accumulate a positive score. You can request a reduced reviewer load by clicking here:')



#     def test_recruit_reviewer(self, conference, client, helpers, selenium, request_page):

#         result = conference.recruit_reviewers(['iclr2021_one@mail.com',
#         'iclr2021_two@mail.com',
#         'iclr2021_three@mail.com',
#         'iclr2021_four@mail.com',
#         'iclr2021_five@mail.com',
#         'iclr2021_six@mail.com',
#         'iclr2021_seven@mail.com',
#         'iclr2021_one_alternate@mail.com'])

#         assert result
#         assert result.id == 'ICLR.cc/2021/Conference/Reviewers/Invited'
#         assert len(result.members) == 7
#         assert 'iclr2021_one@mail.com' in result.members
#         assert 'iclr2021_two@mail.com' in result.members
#         assert 'iclr2021_three@mail.com' in result.members
#         assert 'iclr2021_four@mail.com' in result.members
#         assert 'iclr2021_five@mail.com' in result.members
#         assert 'iclr2021_six@mail.com' in result.members
#         assert 'iclr2021_seven@mail.com' in result.members
#         assert 'iclr2021_one_alternate@mail.com' not in result.members

#         messages = client.get_messages(to = 'iclr2021_one@mail.com', subject = '[ICLR 2021]: Invitation to serve as Reviewer')
#         text = messages[0]['content']['text']
#         assert 'Dear invitee,' in text
#         assert 'You have been nominated by the program chair committee of ICLR 2021 to serve as reviewer' in text

#         reject_url = re.search('https://.*response=No', text).group(0).replace('https://openreview.net', 'http://localhost:3030')
#         accept_url = re.search('https://.*response=Yes', text).group(0).replace('https://openreview.net', 'http://localhost:3030')

#         request_page(selenium, reject_url, alert=True)
#         time.sleep(2)
#         declined_group = client.get_group(id='ICLR.cc/2021/Conference/Reviewers/Declined')
#         assert len(declined_group.members) == 1
#         accepted_group = client.get_group(id='ICLR.cc/2021/Conference/Reviewers')
#         assert len(accepted_group.members) == 0

#         request_page(selenium, accept_url, alert=True)
#         time.sleep(2)
#         declined_group = client.get_group(id='ICLR.cc/2021/Conference/Reviewers/Declined')
#         assert len(declined_group.members) == 0
#         accepted_group = client.get_group(id='ICLR.cc/2021/Conference/Reviewers')
#         assert len(accepted_group.members) == 1

#         messages = client.get_messages(to = 'iclr2021_two@mail.com', subject = '[ICLR 2021]: Invitation to serve as Reviewer')
#         text = messages[0]['content']['text']
#         assert 'Dear invitee,' in text
#         assert 'You have been nominated by the program chair committee of ICLR 2021 to serve as reviewer' in text

#         reject_url = re.search('https://.*response=No', text).group(0).replace('https://openreview.net', 'http://localhost:3030')
#         accept_url = re.search('https://.*response=Yes', text).group(0).replace('https://openreview.net', 'http://localhost:3030')

#         request_page(selenium, reject_url, alert=True)
#         declined_group = client.get_group(id='ICLR.cc/2021/Conference/Reviewers/Declined')
#         assert len(declined_group.members) == 1
#         accepted_group = client.get_group(id='ICLR.cc/2021/Conference/Reviewers')
#         assert len(accepted_group.members) == 1

#         messages = client.get_messages(to = 'iclr2021_four@mail.com', subject = '[ICLR 2021]: Invitation to serve as Reviewer')
#         text = messages[0]['content']['text']
#         assert 'Dear invitee,' in text
#         assert 'You have been nominated by the program chair committee of ICLR 2021 to serve as reviewer' in text

#         reject_url = re.search('https://.*response=No', text).group(0).replace('https://openreview.net', 'http://localhost:3030')
#         accept_url = re.search('https://.*response=Yes', text).group(0).replace('https://openreview.net', 'http://localhost:3030')

#         request_page(selenium, accept_url, alert=True)
#         declined_group = client.get_group(id='ICLR.cc/2021/Conference/Reviewers/Declined')
#         assert len(declined_group.members) == 1
#         accepted_group = client.get_group(id='ICLR.cc/2021/Conference/Reviewers')
#         assert len(accepted_group.members) == 2

#         messages = client.get_messages(to = 'iclr2021_five@mail.com', subject = '[ICLR 2021]: Invitation to serve as Reviewer')
#         text = messages[0]['content']['text']
#         accept_url = re.search('https://.*response=Yes', text).group(0).replace('https://openreview.net', 'http://localhost:3030')
#         request_page(selenium, accept_url, alert=True)
#         declined_group = client.get_group(id='ICLR.cc/2021/Conference/Reviewers/Declined')
#         assert len(declined_group.members) == 1
#         accepted_group = client.get_group(id='ICLR.cc/2021/Conference/Reviewers')
#         assert len(accepted_group.members) == 3

#         messages = client.get_messages(to = 'iclr2021_six_alternate@mail.com', subject = '[ICLR 2021]: Invitation to serve as Reviewer')
#         text = messages[0]['content']['text']
#         accept_url = re.search('https://.*response=Yes', text).group(0).replace('https://openreview.net', 'http://localhost:3030')
#         request_page(selenium, accept_url, alert=True)
#         declined_group = client.get_group(id='ICLR.cc/2021/Conference/Reviewers/Declined')
#         assert len(declined_group.members) == 1
#         accepted_group = client.get_group(id='ICLR.cc/2021/Conference/Reviewers')
#         assert len(accepted_group.members) == 4

#     def test_registration(self, conference, helpers, selenium, request_page):

#         reviewer_client = openreview.Client(username='iclr2021_one@mail.com', password='1234')
#         reviewer_tasks_url = 'http://localhost:3030/group?id=ICLR.cc/2021/Conference/Reviewers#reviewer-tasks'
#         request_page(selenium, reviewer_tasks_url, reviewer_client.token)

#         assert selenium.find_element_by_link_text('Reviewer Registration')
#         assert selenium.find_element_by_link_text('Expertise Selection')

#         registration_notes = reviewer_client.get_notes(invitation = 'ICLR.cc/2021/Conference/Reviewers/-/Form')
#         assert registration_notes
#         assert len(registration_notes) == 1

#         registration_forum = registration_notes[0].forum

#         registration_note = reviewer_client.post_note(
#             openreview.Note(
#                 invitation = 'ICLR.cc/2021/Conference/Reviewers/-/Registration',
#                 forum = registration_forum,
#                 replyto = registration_forum,
#                 content = {
#                     'profile_confirmed': 'Yes',
#                     'expertise_confirmed': 'Yes',
#                     'TPMS_registration_confirmed': 'Yes',
#                     'reviewer_instructions_confirm': 'Yes',
#                     'emergency_review_count': '0'
#                 },
#                 signatures = [
#                     '~ReviewerOne_ICLR1'
#                 ],
#                 readers = [
#                     conference.get_id(),
#                     '~ReviewerOne_ICLR1'
#                 ],
#                 writers = [
#                     conference.get_id(),
#                     '~ReviewerOne_ICLR1'
#                 ]
#             ))
#         assert registration_note


#         request_page(selenium, 'http://localhost:3030/group?id=ICLR.cc/2021/Conference/Reviewers', reviewer_client.token)
#         header = selenium.find_element_by_id('header')
#         assert header
#         notes = header.find_elements_by_class_name("description")
#         assert notes
#         assert len(notes) == 1
#         assert notes[0].text == 'This page provides information and status updates for the ICLR 2021. It will be regularly updated as the conference progresses, so please check back frequently.'

#         request_page(selenium, reviewer_tasks_url, reviewer_client.token)

#         assert selenium.find_element_by_link_text('Reviewer Registration')
#         assert selenium.find_element_by_link_text('Expertise Selection')
#         tasks = selenium.find_element_by_id('reviewer-tasks')
#         assert tasks
#         assert len(tasks.find_elements_by_class_name('note')) == 2
#         assert len(tasks.find_elements_by_class_name('completed')) == 2

#     def test_remind_registration(self, conference, helpers, client):

#         five_reviewer_client = openreview.Client(username='iclr2021_five@mail.com', password='1234')
#         six_reviewer_client = openreview.Client(username='iclr2021_six_alternate@mail.com', password='1234')

#         subject = '[ICLR 2021] Please complete your profile'
#         message = '''
# Dear Reviewer,


# Thank you for accepting our invitation to serve on the program committee for ICLR 2021. The first task we ask of you is to complete your profile, which is essential in order for us to:

# - Assign you relevant submissions.

# - Identify gaps in reviewer expertise.


# To complete your profile, please log into OpenReview and navigate to the reviewer console(https://openreview.net/group?id=ICLR.cc/2021/Conference/Reviewers).
# There you will see a task to "Reviewer Registration". This task should not take more than 10-15 minutes.
# Please complete it by September 4th. Note that you will have to create an OpenReview account if you don’t already have one.


# Thanks again for your ongoing service to our community.


# ICLR2021 Programme Chairs,

# Naila, Katja, Alice, and Ivan
#         '''

#         reminders = conference.remind_registration_stage(subject, message, 'ICLR.cc/2021/Conference/Reviewers')
#         assert reminders
#         assert reminders == ['iclr2021_four@mail.com', 'iclr2021_five@mail.com', 'iclr2021_six@mail.com']

#         registration_notes = six_reviewer_client.get_notes(invitation = 'ICLR.cc/2021/Conference/Reviewers/-/Form')
#         assert registration_notes
#         assert len(registration_notes) == 1

#         registration_forum = registration_notes[0].forum

#         registration_note = six_reviewer_client.post_note(
#             openreview.Note(
#                 invitation = 'ICLR.cc/2021/Conference/Reviewers/-/Registration',
#                 forum = registration_forum,
#                 replyto = registration_forum,
#                 content = {
#                     'profile_confirmed': 'Yes',
#                     'expertise_confirmed': 'Yes',
#                     'TPMS_registration_confirmed': 'Yes',
#                     'reviewer_instructions_confirm': 'Yes',
#                     'emergency_review_count': '0'
#                 },
#                 signatures = [
#                     '~ReviewerSix_ICLR1'
#                 ],
#                 readers = [
#                     conference.get_id(),
#                     '~ReviewerSix_ICLR1'
#                 ],
#                 writers = [
#                     conference.get_id(),
#                     '~ReviewerSix_ICLR1'
#                 ]
#             ))

#         reminders = conference.remind_registration_stage(subject, message, 'ICLR.cc/2021/Conference/Reviewers')
#         assert reminders
#         assert reminders == ['iclr2021_four@mail.com', 'iclr2021_five@mail.com']


#     def test_retry_declined_reviewers(self, conference, helpers, client, selenium, request_page):

#         title = '[ICLR 2021] Please reconsider serving as a reviewer'
#         message = '''
# Dear Reviewer,


# Thank you for responding to our invitation to serve as a reviewer for ICLR 2021. We would still very much benefit from your expertise and wonder whether you would reconsider our invitation in light of the fact that we will guarantee you a maximum load of 3 papers.


# If you would now like to ACCEPT the invitation, please click on the following link:


# {accept_url}


# We would appreciate an answer by Friday September 4th (in 7 days).


# If you have any questions, please don’t hesitate to reach out to us at iclr2021programchairs@googlegroups.com.


# We do hope you will reconsider and we thank you as always for your ongoing service to our community.


# ICLR2021 Programme Chairs,

# Naila, Katja, Alice, and Ivan
#         '''

#         result = conference.recruit_reviewers(title=title, message=message, retry_declined=True)

#         messages = client.get_messages(subject = '[ICLR 2021] Please reconsider serving as a reviewer')
#         assert len(messages) == 1
#         assert messages[0]['content']['to'] == 'iclr2021_two@mail.com'
#         text = messages[0]['content']['text']

#         accept_url = re.search('https://.*response=Yes', text).group(0).replace('https://openreview.net', 'http://localhost:3030')

#         request_page(selenium, accept_url, alert=True)
#         declined_group = client.get_group(id='ICLR.cc/2021/Conference/Reviewers/Declined')
#         assert len(declined_group.members) == 0
#         accepted_group = client.get_group(id='ICLR.cc/2021/Conference/Reviewers')
#         assert len(accepted_group.members) == 5

#     def test_invite_suggested_reviewers(self, conference, helpers, client, selenium, request_page):

#         result = conference.recruit_reviewers(['iclr2021_one@mail.com',
#         'iclr2021_two@mail.com',
#         'iclr2021_three@mail.com',
#         'iclr2021_four@mail.com',
#         'iclr2021_five@mail.com',
#         'iclr2021_six@mail.com',
#         'iclr2021_seven@mail.com',
#         'iclr2021_eight@mail.com',
#         'iclr2021_nine@mail.com',
#         'iclr2021_six_alternate@mail.com'], invitee_names=['', '', '', '', '', '', '', '', 'Melisa Bok', ''])

#         messages = client.get_messages(subject = '[ICLR 2021]: Invitation to serve as Reviewer')
#         assert len(messages) == 9

#         assert 'Melisa Bok' in messages[8]['content']['text']


#     def test_submit_papers(self, conference, helpers, test_client, client):

#         domains = ['umass.edu', 'umass.edu', 'fb.com', 'umass.edu', 'google.com', 'mit.edu']
#         for i in range(1,6):
#             note = openreview.Note(invitation = 'ICLR.cc/2021/Conference/-/Submission',
#                 readers = ['ICLR.cc/2021/Conference', 'test@mail.com', 'peter@mail.com', 'andrew@' + domains[i], '~Test_User1'],
#                 writers = [conference.id, '~Test_User1', 'peter@mail.com', 'andrew@' + domains[i]],
#                 signatures = ['~Test_User1'],
#                 content = {
#                     'title': 'Paper title ' + str(i) ,
#                     'abstract': 'This is an abstract ' + str(i),
#                     'authorids': ['test@mail.com', 'peter@mail.com', 'andrew@' + domains[i]],
#                     'authors': ['Test User', 'Peter Test', 'Andrew Mc'],
#                     'code_of_ethics': 'I acknowledge that I and all co-authors of this work have read and commit to adhering to the ICLR Code of Ethics'
#                 }
#             )
#             note = test_client.post_note(note)

#         conference.setup_first_deadline_stage(force=True)

#         blinded_notes = test_client.get_notes(invitation='ICLR.cc/2021/Conference/-/Blind_Submission')
#         assert len(blinded_notes) == 5

#         invitations = test_client.get_invitations(replyForum=blinded_notes[0].id)
#         assert len(invitations) == 1
#         assert invitations[0].id == 'ICLR.cc/2021/Conference/Paper5/-/Withdraw'

#         invitations = test_client.get_invitations(replyForum=blinded_notes[0].original)
#         assert len(invitations) == 1
#         assert invitations[0].id == 'ICLR.cc/2021/Conference/Paper5/-/Revision'

#         invitations = client.get_invitations(replyForum=blinded_notes[0].id)
#         assert len(invitations) == 2
#         assert invitations[0].id == 'ICLR.cc/2021/Conference/Paper5/-/Desk_Reject'
#         assert invitations[1].id == 'ICLR.cc/2021/Conference/Paper5/-/Withdraw'

#         # Add a revision
#         pdf_url = test_client.put_attachment(
#             os.path.join(os.path.dirname(__file__), 'data/paper.pdf'),
#             'ICLR.cc/2021/Conference/Paper5/-/Revision',
#             'pdf'
#         )

#         supplementary_material_url = test_client.put_attachment(
#             os.path.join(os.path.dirname(__file__), 'data/paper.pdf.zip'),
#             'ICLR.cc/2021/Conference/Paper5/-/Revision',
#             'supplementary_material'
#         )

#         note = openreview.Note(referent=blinded_notes[0].original,
#             forum=blinded_notes[0].original,
#             invitation = 'ICLR.cc/2021/Conference/Paper5/-/Revision',
#             readers = ['ICLR.cc/2021/Conference', 'ICLR.cc/2021/Conference/Paper5/Authors'],
#             writers = ['ICLR.cc/2021/Conference', 'ICLR.cc/2021/Conference/Paper5/Authors'],
#             signatures = ['ICLR.cc/2021/Conference/Paper5/Authors'],
#             content = {
#                 'title': 'EDITED Paper title 5',
#                 'abstract': 'This is an abstract 5',
#                 'authorids': ['test@mail.com', 'peter@mail.com', 'melisa@mail.com'],
#                 'authors': ['Test User', 'Peter Test', 'Melisa Bok'],
#                 'code_of_ethics': 'I acknowledge that I and all co-authors of this work have read and commit to adhering to the ICLR Code of Ethics',
#                 'pdf': pdf_url,
#                 'supplementary_material': supplementary_material_url
#             }
#         )

#         test_client.post_note(note)

#         helpers.await_queue()

#         author_group = client.get_group('ICLR.cc/2021/Conference/Paper5/Authors')
#         assert len(author_group.members) == 3
#         assert 'melisa@mail.com' in author_group.members
#         assert 'test@mail.com' in author_group.members
#         assert 'peter@mail.com' in author_group.members

#         messages = client.get_messages(subject='ICLR 2021 has received a new revision of your submission titled EDITED Paper title 5')
#         assert len(messages) == 3
#         recipients = [m['content']['to'] for m in messages]
#         assert 'melisa@mail.com' in recipients
#         assert 'test@mail.com' in recipients
#         assert 'peter@mail.com' in recipients
#         assert messages[0]['content']['text'] == '''Your new revision of the submission to ICLR 2021 has been posted.\n\nTitle: EDITED Paper title 5\n\nAbstract: This is an abstract 5\n\nTo view your submission, click here: https://openreview.net/forum?id=''' + note.forum

#         ## Edit revision
#         references = client.get_references(invitation='ICLR.cc/2021/Conference/Paper5/-/Revision')
#         assert len(references) == 1
#         revision_note = references[0]
#         revision_note.content['title'] = 'EDITED Rev 2 Paper title 5'
#         test_client.post_note(revision_note)

#         helpers.await_queue()

#         messages = client.get_messages(subject='ICLR 2021 has received a new revision of your submission titled EDITED Rev 2 Paper title 5')
#         assert len(messages) == 3
#         recipients = [m['content']['to'] for m in messages]
#         assert 'melisa@mail.com' in recipients
#         assert 'test@mail.com' in recipients
#         assert 'peter@mail.com' in recipients

#         assert messages[0]['content']['text'] == '''Your new revision of the submission to ICLR 2021 has been updated.\n\nTitle: EDITED Rev 2 Paper title 5\n\nAbstract: This is an abstract 5\n\nTo view your submission, click here: https://openreview.net/forum?id=''' + note.forum

#         ## Withdraw paper
#         test_client.post_note(openreview.Note(invitation='ICLR.cc/2021/Conference/Paper1/-/Withdraw',
#             forum = blinded_notes[4].forum,
#             replyto = blinded_notes[4].forum,
#             readers = [
#                 'ICLR.cc/2021/Conference',
#                 'ICLR.cc/2021/Conference/Paper1/Authors',
#                 'ICLR.cc/2021/Conference/Paper1/Reviewers',
#                 'ICLR.cc/2021/Conference/Paper1/Area_Chairs',
#                 'ICLR.cc/2021/Conference/Program_Chairs'],
#             writers = [conference.get_id(), 'ICLR.cc/2021/Conference/Paper1/Authors'],
#             signatures = ['ICLR.cc/2021/Conference/Paper1/Authors'],
#             content = {
#                 'title': 'Submission Withdrawn by the Authors',
#                 'withdrawal confirmation': 'I have read and agree with the venue\'s withdrawal policy on behalf of myself and my co-authors.'
#             }
#         ))

#         helpers.await_queue()

#         withdrawn_notes = client.get_notes(invitation='ICLR.cc/2021/Conference/-/Withdrawn_Submission')
#         assert len(withdrawn_notes) == 1
#         withdrawn_notes[0].readers == [
#             'ICLR.cc/2021/Conference/Paper1/Authors',
#             'ICLR.cc/2021/Conference/Paper1/Reviewers',
#             'ICLR.cc/2021/Conference/Paper1/Area_Chairs',
#             'ICLR.cc/2021/Conference/Program_Chairs'
#         ]
#         assert len(conference.get_submissions()) == 4

#     def test_post_submission_stage(self, conference, helpers, test_client, client):

#         conference.setup_final_deadline_stage(force=True)

#         submissions = conference.get_submissions()
#         assert len(submissions) == 4
#         assert submissions[0].readers == ['everyone']
#         assert submissions[1].readers == ['everyone']
#         assert submissions[2].readers == ['everyone']
#         assert submissions[3].readers == ['everyone']

#         ## Withdraw paper
#         test_client.post_note(openreview.Note(invitation='ICLR.cc/2021/Conference/Paper2/-/Withdraw',
#             forum = submissions[3].forum,
#             replyto = submissions[3].forum,
#             readers = [
#                 'everyone'],
#             writers = [conference.get_id(), 'ICLR.cc/2021/Conference/Paper2/Authors'],
#             signatures = ['ICLR.cc/2021/Conference/Paper2/Authors'],
#             content = {
#                 'title': 'Submission Withdrawn by the Authors',
#                 'withdrawal confirmation': 'I have read and agree with the venue\'s withdrawal policy on behalf of myself and my co-authors.'
#             }
#         ))

#         helpers.await_queue()

#         withdrawn_notes = client.get_notes(invitation='ICLR.cc/2021/Conference/-/Withdrawn_Submission')
#         assert len(withdrawn_notes) == 2
#         withdrawn_notes[0].readers == [
#             'everyone'
#         ]
#         withdrawn_notes[1].readers == [
#             'ICLR.cc/2021/Conference/Paper1/Authors',
#             'ICLR.cc/2021/Conference/Paper1/Reviewers',
#             'ICLR.cc/2021/Conference/Paper1/Area_Chairs',
#             'ICLR.cc/2021/Conference/Program_Chairs'
#         ]


#     def test_revision_stage(self, conference, helpers, test_client, client):

#         now = datetime.datetime.utcnow()
#         conference.set_submission_revision_stage(openreview.SubmissionRevisionStage(due_date=now + datetime.timedelta(minutes = 40), allow_author_reorder=True))

#         submissions = conference.get_submissions()

#         print(submissions[0])

#         test_client.post_note(openreview.Note(
#             invitation='ICLR.cc/2021/Conference/Paper5/-/Revision',
#             referent=submissions[0].original,
#             forum=submissions[0].original,
#             readers=['ICLR.cc/2021/Conference', 'ICLR.cc/2021/Conference/Paper5/Authors'],
#             writers=['ICLR.cc/2021/Conference', 'ICLR.cc/2021/Conference/Paper5/Authors'],
#             signatures=['ICLR.cc/2021/Conference/Paper5/Authors'],
#             content={
#                 'title': 'EDITED V3 Paper title 5',
#                 'abstract': 'This is an abstract 5',
#                 'authorids': ['peter@mail.com', 'test@mail.com', 'melisa@mail.com'],
#                 'authors': ['Peter Test', 'Test User', 'Melisa Bok'],
#                 'code_of_ethics': 'I acknowledge that I and all co-authors of this work have read and commit to adhering to the ICLR Code of Ethics',
#                 'pdf': submissions[0].content['pdf'],
#                 'supplementary_material': submissions[0].content['supplementary_material']
#             }

#         ))
