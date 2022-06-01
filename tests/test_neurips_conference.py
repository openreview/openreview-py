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

    @pytest.fixture(scope="class")
    def conference(self, client):
        pc_client=openreview.Client(username='pc@neurips.cc', password='1234')
        request_form=client.get_notes(invitation='openreview.net/Support/-/Request_Form', sort='tmdate')[0]

        conference=openreview.helpers.get_conference(pc_client, request_form.id)
        return conference


    def test_create_conference(self, client, helpers):

        now = datetime.datetime.utcnow()
        due_date = now + datetime.timedelta(days=3)
        first_date = now + datetime.timedelta(days=1)

        # Post the request form note
        pc_client=helpers.create_user('pc@neurips.cc', 'Program', 'NeurIPSChair')

        helpers.create_user('another_andrew@mit.edu', 'Another', 'Andrew')
        helpers.create_user('sac1@google.com', 'SeniorArea', 'GoogleChair', institution='google.com')
        helpers.create_user('sac2@gmail.com', 'SeniorArea', 'NeurIPSChair')
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
                'Abbreviated Venue Name': 'NeurIPS 2021',
                'Official Website URL': 'https://neurips.cc',
                'program_chair_emails': ['pc@neurips.cc'],
                'contact_email': 'pc@neurips.cc',
                'Area Chairs (Metareviewers)': 'Yes, our venue has Area Chairs',
                'senior_area_chairs': 'Yes, our venue has Senior Area Chairs',
                'Venue Start Date': '2021/12/01',
                'Submission Deadline': due_date.strftime('%Y/%m/%d'),
                'abstract_registration_deadline': first_date.strftime('%Y/%m/%d'),
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
                'use_recruitment_template': 'Yes'
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
        assert client.get_group('NeurIPS.cc/2021/Conference/Senior_Area_Chairs')
        acs=client.get_group('NeurIPS.cc/2021/Conference/Area_Chairs')
        assert acs
        assert 'NeurIPS.cc/2021/Conference/Senior_Area_Chairs' in acs.readers
        reviewers=client.get_group('NeurIPS.cc/2021/Conference/Reviewers')
        assert reviewers
        assert 'NeurIPS.cc/2021/Conference/Senior_Area_Chairs' in reviewers.readers
        assert 'NeurIPS.cc/2021/Conference/Area_Chairs' in reviewers.readers

        assert client.get_group('NeurIPS.cc/2021/Conference/Authors')

    def test_recruit_senior_area_chairs(self, client, selenium, request_page, helpers):

        pc_client=openreview.Client(username='pc@neurips.cc', password='1234')
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
                'invitation_email_content': 'Dear {{fullname}},\n\nYou have been nominated by the program chair committee of Theoretical Foundations of RL Workshop @ ICML 2020 to serve as {{invitee_role}}.\n\n{{invitation_url}}\n\nCheers!\n\nProgram Chairs'
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

        messages = client.get_messages(to='sac1@google.com', subject='[NeurIPS 2021] Invitation to serve as Senior Area Chair')
        assert messages and len(messages) == 1
        assert messages[0]['content']['subject'] == '[NeurIPS 2021] Invitation to serve as Senior Area Chair'
        assert messages[0]['content']['text'].startswith('<p>Dear SAC One,</p>\n<p>You have been nominated by the program chair committee of Theoretical Foundations of RL Workshop @ ICML 2020 to serve as Senior Area Chair.')
        invitation_url = re.search('href="https://.*">', messages[0]['content']['text']).group(0)[6:-1].replace('https://openreview.net', 'http://localhost:3030').replace('&amp;', '&')[:-1]
        print('invitation_url', invitation_url)
        helpers.respond_invitation(selenium, request_page, invitation_url, accept=True)

        messages = client.get_messages(to='sac1@google.com', subject='[NeurIPS 2021] Senior Area Chair Invitation accepted')
        assert messages and len(messages) == 1
        assert messages[0]['content']['text'] == '''<p>Thank you for accepting the invitation to be a Senior Area Chair for NeurIPS 2021.</p>
<p>The NeurIPS 2021 program chairs will be contacting you with more information regarding next steps soon. In the meantime, please add <a href=\"mailto:noreply@openreview.net\">noreply@openreview.net</a> to your email contacts to ensure that you receive all communications.</p>
<p>If you would like to change your decision, please follow link in the previous invitation email and click on the &quot;Decline&quot; button.</p>
'''
        
        messages = client.get_messages(to='sac2@gmail.com', subject='[NeurIPS 2021] Invitation to serve as Senior Area Chair')
        assert messages and len(messages) == 1
        assert messages[0]['content']['subject'] == '[NeurIPS 2021] Invitation to serve as Senior Area Chair'
        assert messages[0]['content']['text'].startswith('<p>Dear SAC Two,</p>\n<p>You have been nominated by the program chair committee of Theoretical Foundations of RL Workshop @ ICML 2020 to serve as Senior Area Chair.')
        invitation_url = re.search('href="https://.*">', messages[0]['content']['text']).group(0)[6:-1].replace('https://openreview.net', 'http://localhost:3030').replace('&amp;', '&')[:-1]
        helpers.respond_invitation(selenium, request_page, invitation_url, accept=True)

        sac_group = client.get_group('NeurIPS.cc/2021/Conference/Senior_Area_Chairs')
        assert len(sac_group.members) == 2
        assert 'sac1@google.com' in sac_group.members
        assert 'sac2@gmail.com' in sac_group.members

        sac_client = openreview.Client(username='sac1@google.com', password='1234')
        request_page(selenium, "http://localhost:3030/group?id=NeurIPS.cc/2021/Conference", sac_client.token, wait_for_element='notes')
        notes_panel = selenium.find_element_by_id('notes')
        assert notes_panel
        tabs = notes_panel.find_element_by_class_name('tabs-container')
        assert tabs
        assert tabs.find_element_by_id('your-consoles')
        assert len(tabs.find_element_by_id('your-consoles').find_elements_by_tag_name('ul')) == 1
        console = tabs.find_element_by_id('your-consoles').find_elements_by_tag_name('ul')[0]
        assert 'Senior Area Chair Console' == console.find_element_by_tag_name('a').text

    def test_recruit_area_chairs(self, client, selenium, request_page, helpers):

        pc_client=openreview.Client(username='pc@neurips.cc', password='1234')
        request_form=pc_client.get_notes(invitation='openreview.net/Support/-/Request_Form')[0]

        conference=openreview.helpers.get_conference(client, request_form.id)

        result = conference.recruit_reviewers(['ac1@mit.edu'], reviewers_name='Area_Chairs', reduced_load_on_decline=['2', '3', '4'])
        assert result
        assert len(result['invited']) == 1
        assert len(result['reminded']) == 0
        assert not result['already_invited']
        assert 'ac1@mit.edu' in result['invited']

        messages = client.get_messages(to = 'ac1@mit.edu', subject = '[NeurIPS 2021]: Invitation to serve as Area Chair')
        text = messages[0]['content']['text']
        assert 'Dear invitee,' in text
        assert 'You have been nominated by the program chair committee of NeurIPS 2021 to serve as Area Chair' in text

        invitation_url = re.search('href="https://.*">', messages[0]['content']['text']).group(0)[6:-1].replace('https://openreview.net', 'http://localhost:3030').replace('&amp;', '&')[:-1]

        helpers.respond_invitation(selenium, request_page, invitation_url, accept=True)
        accepted_group = client.get_group(id='NeurIPS.cc/2021/Conference/Area_Chairs')
        assert len(accepted_group.members) == 1
        assert 'ac1@mit.edu' in accepted_group.members

        openreview.tools.replace_members_with_ids(client, accepted_group)
        accepted_group = client.get_group(id='NeurIPS.cc/2021/Conference/Area_Chairs')
        assert len(accepted_group.members) == 1
        assert '~Area_IBMChair1' in accepted_group.members

        rejected_group = client.get_group(id='NeurIPS.cc/2021/Conference/Area_Chairs/Declined')
        assert len(rejected_group.members) == 0

        helpers.respond_invitation(selenium, request_page, invitation_url, accept=False)
        notes = selenium.find_element_by_class_name("note_editor")
        assert notes
        messages = notes.find_elements_by_tag_name("h3")
        assert messages
        assert 'You have declined the invitation from Conference on Neural Information Processing Systems.' == messages[0].text
        assert 'In case you only declined because you think you cannot handle the maximum load of papers, you can reduce your load slightly. Be aware that this will decrease your overall score for an outstanding reviewer award, since all good reviews will accumulate a positive score. You can request a reduced reviewer load by clicking the option below:' == messages[1].text
        
        rejected_group = client.get_group(id='NeurIPS.cc/2021/Conference/Area_Chairs/Declined')
        assert len(rejected_group.members) == 1
        assert 'ac1@mit.edu' in rejected_group.members

        accepted_group = client.get_group(id='NeurIPS.cc/2021/Conference/Area_Chairs')
        assert len(accepted_group.members) == 0

        ## Accept with reduced quota
        dropdown = selenium.find_element_by_class_name('dropdown-select__input-container')
        dropdown.click()
        time.sleep(0.5)
        values = selenium.find_elements_by_class_name('dropdown-select__option')
        assert len(values) > 0
        values[1].click()
        time.sleep(0.5)
        button = selenium.find_element_by_xpath('//button[text()="Accept with Reduced Quota"]')
        button.click()
        time.sleep(0.5)
        helpers.await_queue()

        area_chairs=client.get_group('NeurIPS.cc/2021/Conference/Area_Chairs')
        assert len(area_chairs.members) == 1
        assert 'ac1@mit.edu' in area_chairs.members

        notes = client.get_notes(invitation='NeurIPS.cc/2021/Conference/Area_Chairs/-/Recruitment', content={'user': 'ac1@mit.edu', 'response': 'Yes'}, sort='tcdate:desc')
        assert notes
        assert len(notes) == 2
        assert notes[0].content['reduced_quota'] == '3'

        messages = client.get_messages(to = 'ac1@mit.edu', subject = '[NeurIPS 2021] Area Chair Invitation accepted with reduced quota')
        assert len(messages) == 1
        messages[0]['content']['text'] == '''<p>Thank you for accepting the invitation to be a Area Chair for NeurIPS 2021.<br>
You have selected a reduced quota of 3 submissions to review.</p>
<p>The NeurIPS 2021 program chairs will be contacting you with more information regarding next steps soon. In the meantime, please add <a href=\"mailto:noreply@openreview.net\">noreply@openreview.net</a> to your email contacts to ensure that you receive all communications.</p>
<p>If you would like to change your decision, please follow link in the previous invitation email and click on the &quot;Decline&quot; button.</p>
'''


    def test_sac_matching(self, client, conference, helpers, request_page, selenium):

        #remove SACs from group
        client.remove_members_from_group('NeurIPS.cc/2021/Conference/Senior_Area_Chairs', ['sac1@google.com','sac2@gmail.com'])

        #remove AC from AC group
        client.remove_members_from_group('NeurIPS.cc/2021/Conference/Area_Chairs', 'ac1@mit.edu')

        pc_client=openreview.Client(username='pc@neurips.cc', password='1234')
        request_form=pc_client.get_notes(invitation='openreview.net/Support/-/Request_Form')[0]

        conference=openreview.helpers.get_conference(pc_client, request_form.id)

        #setup matching for SACs with empty SAC group
        with pytest.raises(openreview.OpenReviewException, match=r'The match group is empty'):
            conference.setup_committee_matching(committee_id=conference.get_senior_area_chairs_id(), compute_conflicts=True)

        client.add_members_to_group('NeurIPS.cc/2021/Conference/Senior_Area_Chairs', ['sac1@google.com','sac2@gmail.com'])

        #setup matching for SACs with empty AC group
        with pytest.raises(openreview.OpenReviewException, match=r'The alternate match group is empty'):
            conference.setup_committee_matching(committee_id=conference.get_senior_area_chairs_id(), compute_conflicts=True)

        client.add_members_to_group('NeurIPS.cc/2021/Conference/Area_Chairs', ['~Area_IBMChair1', '~Area_GoogleChair1', '~Area_UMassChair1', 'ac1@mit.edu'])

    def test_sac_bidding(self, conference, helpers, request_page, selenium):

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

        sac_client=openreview.Client(username='sac1@google.com', password='1234')
        assert sac_client.get_group(id='NeurIPS.cc/2021/Conference/Area_Chairs')

        tasks_url = 'http://localhost:3030/group?id=NeurIPS.cc/2021/Conference/Senior_Area_Chairs#senior-areachair-tasks'
        request_page(selenium, tasks_url, sac_client.token, by=By.LINK_TEXT, wait_for_element='Senior Area Chair Bid')

        assert selenium.find_element_by_link_text('Senior Area Chair Bid')


        bid_url = 'http://localhost:3030/invitation?id=NeurIPS.cc/2021/Conference/Senior_Area_Chairs/-/Bid'
        request_page(selenium, bid_url, sac_client.token, wait_for_element='notes')

        assert selenium.find_element_by_id('notes')

        sac_client.post_edge(openreview.Edge(
            invitation='NeurIPS.cc/2021/Conference/Senior_Area_Chairs/-/Bid',
            readers = [conference.id, '~SeniorArea_GoogleChair1'],
            writers = ['~SeniorArea_GoogleChair1'],
            signatures = ['~SeniorArea_GoogleChair1'],
            head = '~Area_IBMChair1',
            tail = '~SeniorArea_GoogleChair1',
            label = 'Very High'
        ))

        sac_client.post_edge(openreview.Edge(
            invitation='NeurIPS.cc/2021/Conference/Senior_Area_Chairs/-/Bid',
            readers = [conference.id, '~SeniorArea_GoogleChair1'],
            writers = ['~SeniorArea_GoogleChair1'],
            signatures = ['~SeniorArea_GoogleChair1'],
            head = '~Area_GoogleChair1',
            tail = '~SeniorArea_GoogleChair1',
            label = 'High'
        ))

        sac_client.post_edge(openreview.Edge(
            invitation='NeurIPS.cc/2021/Conference/Senior_Area_Chairs/-/Bid',
            readers = [conference.id, '~SeniorArea_GoogleChair1'],
            writers = ['~SeniorArea_GoogleChair1'],
            signatures = ['~SeniorArea_GoogleChair1'],
            head = '~Area_UMassChair1',
            tail = '~SeniorArea_GoogleChair1',
            label = 'Very Low'
        ))

        sac2_client=openreview.Client(username='sac2@gmail.com', password='1234')

        sac2_client.post_edge(openreview.Edge(
            invitation='NeurIPS.cc/2021/Conference/Senior_Area_Chairs/-/Bid',
            readers = [conference.id, '~SeniorArea_NeurIPSChair1'],
            writers = ['~SeniorArea_NeurIPSChair1'],
            signatures = ['~SeniorArea_NeurIPSChair1'],
            head = '~Area_IBMChair1',
            tail = '~SeniorArea_NeurIPSChair1',
            label = 'Very Low'
        ))

        sac2_client.post_edge(openreview.Edge(
            invitation='NeurIPS.cc/2021/Conference/Senior_Area_Chairs/-/Bid',
            readers = [conference.id, '~SeniorArea_NeurIPSChair1'],
            writers = ['~SeniorArea_NeurIPSChair1'],
            signatures = ['~SeniorArea_NeurIPSChair1'],
            head = '~Area_GoogleChair1',
            tail = '~SeniorArea_NeurIPSChair1',
            label = 'Very High'
        ))

        sac2_client.post_edge(openreview.Edge(
            invitation='NeurIPS.cc/2021/Conference/Senior_Area_Chairs/-/Bid',
            readers = [conference.id, '~SeniorArea_NeurIPSChair1'],
            writers = ['~SeniorArea_NeurIPSChair1'],
            signatures = ['~SeniorArea_NeurIPSChair1'],
            head = '~Area_UMassChair1',
            tail = '~SeniorArea_NeurIPSChair1',
            label = 'Very Low'
        ))

        ## SAC assignments
        pc_client.post_edge(openreview.Edge(
            invitation='NeurIPS.cc/2021/Conference/Senior_Area_Chairs/-/Proposed_Assignment',
            readers = [conference.id, '~SeniorArea_GoogleChair1', '~Area_IBMChair1'],
            writers = [conference.id],
            signatures = [conference.id],
            head = '~Area_IBMChair1',
            tail = '~SeniorArea_GoogleChair1',
            label = 'sac-matching',
            weight = 0.94
        ))
        pc_client.post_edge(openreview.Edge(
            invitation='NeurIPS.cc/2021/Conference/Senior_Area_Chairs/-/Proposed_Assignment',
            readers = [conference.id, '~SeniorArea_NeurIPSChair1', '~Area_GoogleChair1'],
            writers = [conference.id],
            signatures = [conference.id],
            head = '~Area_GoogleChair1',
            tail = '~SeniorArea_NeurIPSChair1',
            label = 'sac-matching',
            weight = 0.94
        ))
        pc_client.post_edge(openreview.Edge(
            invitation='NeurIPS.cc/2021/Conference/Senior_Area_Chairs/-/Proposed_Assignment',
            readers = [conference.id, '~SeniorArea_GoogleChair1', '~Area_UMassChair1'],
            writers = [conference.id],
            signatures = [conference.id],
            head = '~Area_UMassChair1',
            tail = '~SeniorArea_GoogleChair1',
            label = 'sac-matching',
            weight = 0.94
        ))

        url='http://localhost:3030/edges/browse?traverse=NeurIPS.cc/2021/Conference/Senior_Area_Chairs/-/Proposed_Assignment,label:sac-matching&edit=NeurIPS.cc/2021/Conference/Senior_Area_Chairs/-/Proposed_Assignment,label:sac-matching&browse=NeurIPS.cc/2021/Conference/Senior_Area_Chairs/-/Aggregate_Score,label:sac-matching;NeurIPS.cc/2021/Conference/Senior_Area_Chairs/-/Affinity_Score;NeurIPS.cc/2021/Conference/Senior_Area_Chairs/-/Conflict'

        print(url)

        with pytest.raises(openreview.OpenReviewException, match=r'No submissions to deploy SAC assignment'):
            conference.set_assignments(assignment_title='sac-matching', committee_id='NeurIPS.cc/2021/Conference/Senior_Area_Chairs', overwrite=True)

    def test_recruit_reviewers(self, client, selenium, request_page, helpers):

        pc_client=openreview.Client(username='pc@neurips.cc', password='1234')
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
                'invitation_email_content': 'Dear {{fullname}},\n\nYou have been nominated by the program chair committee of Theoretical Foundations of RL Workshop @ ICML 2020 to serve as {{invitee_role}}.\n\n{{invitation_url}}\n\nIf you have any questions, please contact {{contact_info}}.\n\nCheers!\n\nProgram Chairs'
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

        recruitment_status_notes=client.get_notes(forum=recruitment_note.forum, replyto=recruitment_note.id)
        assert len(recruitment_status_notes) == 1
        assert {'NeurIPS.cc/2021/Conference/Senior_Area_Chairs/Invited': ['sac1@google.com', 'sac2@gmail.com']} == recruitment_status_notes[0].content['already_invited']

        messages = client.get_messages(to='reviewer1@umass.edu', subject='[NeurIPS 2021] Invitation to serve as Reviewer')
        assert messages and len(messages) == 1
        assert messages[0]['content']['subject'] == '[NeurIPS 2021] Invitation to serve as Reviewer'
        assert messages[0]['content']['text'].startswith('<p>Dear Reviewer UMass,</p>\n<p>You have been nominated by the program chair committee of Theoretical Foundations of RL Workshop @ ICML 2020 to serve as Reviewer.')
        assert 'pc@neurips.cc' in messages[0]['content']['text']
        invitation_url = re.search('href="https://.*">', messages[0]['content']['text']).group(0)[6:-1].replace('https://openreview.net', 'http://localhost:3030').replace('&amp;', '&')[:-1]

        helpers.respond_invitation(selenium, request_page, invitation_url, accept=False)
        notes = selenium.find_element_by_class_name("note_editor")
        assert notes        
        messages = notes.find_elements_by_tag_name("h3")
        assert messages
        assert 'You have declined the invitation from Conference on Neural Information Processing Systems.' == messages[0].text
        assert 'In case you only declined because you think you cannot handle the maximum load of papers, you can reduce your load slightly. Be aware that this will decrease your overall score for an outstanding reviewer award, since all good reviews will accumulate a positive score. You can request a reduced reviewer load by clicking the option below:' == messages[1].text

        assert len(client.get_group('NeurIPS.cc/2021/Conference/Reviewers').members) == 0

        group = client.get_group('NeurIPS.cc/2021/Conference/Reviewers/Declined')
        assert group
        assert len(group.members) == 1
        assert 'reviewer1@umass.edu' in group.members

        messages = client.get_messages(to='reviewer1@umass.edu', subject='[NeurIPS 2021] Reviewer Invitation declined')
        assert messages
        assert len(messages)
        assert messages[0]['content']['text'] == '<p>You have declined the invitation to become a Reviewer for NeurIPS 2021.</p>\n<p>If you would like to change your decision, please follow link in the previous invitation email and click on the &quot;Accept&quot; button.</p>\n'

        notes = client.get_notes(invitation='NeurIPS.cc/2021/Conference/Reviewers/-/Recruitment', content={'user': 'reviewer1@umass.edu'})
        assert notes
        assert len(notes) == 1

        ## Accept with reduced quota
        dropdown = selenium.find_element_by_class_name('dropdown-select__input-container')
        dropdown.click()
        time.sleep(0.5)
        values = selenium.find_elements_by_class_name('dropdown-select__option')
        assert len(values) > 0
        values[2].click()
        time.sleep(0.5)
        button = selenium.find_element_by_xpath('//button[text()="Accept with Reduced Quota"]')
        button.click()
        time.sleep(0.5)
        helpers.await_queue()        

        reviewers_group=client.get_group('NeurIPS.cc/2021/Conference/Reviewers')
        assert len(reviewers_group.members) == 1
        assert 'reviewer1@umass.edu' in reviewers_group.members

        messages = client.get_messages(to = 'reviewer1@umass.edu', subject = '[NeurIPS 2021] Reviewer Invitation accepted with reduced quota')
        assert len(messages) == 1
        messages[0]['content']['text'] == '''<p>Thank you for accepting the invitation to be a Reviewer for NeurIPS 2021.<br>
You have selected a reduced quota of 3 submissions to review.</p>
<p>The NeurIPS 2021 program chairs will be contacting you with more information regarding next steps soon. In the meantime, please add <a href=\"mailto:noreply@openreview.net\">noreply@openreview.net</a> to your email contacts to ensure that you receive all communications.</p>
<p>If you would like to change your decision, please follow link in the previous invitation email and click on the &quot;Decline&quot; button.</p>
'''        

        ## Remind reviewers
        recruitment_note = pc_client.post_note(openreview.Note(
            content={
                'title': 'Remind Recruitment',
                'invitee_role': 'Reviewers',
                'invitee_reduced_load': ['2', '3', '4'],
                'invitation_email_subject': '[' + request_form.content['Abbreviated Venue Name'] + '] Invitation to serve as {{invitee_role}}',
                'invitation_email_content': 'Dear {{fullname}},\n\nYou have been nominated by the program chair committee of Theoretical Foundations of RL Workshop @ ICML 2020 to serve as {{invitee_role}}.\n\n{{invitation_url}}\n\nCheers!\n\nProgram Chairs'
            },
            forum=request_form.forum,
            replyto=request_form.forum,
            invitation='openreview.net/Support/-/Request{}/Remind_Recruitment'.format(request_form.number),
            readers=['NeurIPS.cc/2021/Conference/Program_Chairs', 'openreview.net/Support'],
            signatures=['~Program_NeurIPSChair1'],
            writers=[]
        ))

        helpers.await_queue()

        messages = client.get_messages(to='reviewer2@mit.edu', subject='Reminder: [NeurIPS 2021] Invitation to serve as Reviewer')
        assert messages and len(messages) == 1
        assert messages[0]['content']['subject'] == 'Reminder: [NeurIPS 2021] Invitation to serve as Reviewer'
        assert messages[0]['content']['text'].startswith('<p>Dear invitee,</p>\n<p>You have been nominated by the program chair committee of Theoretical Foundations of RL Workshop @ ICML 2020 to serve as Reviewer.')
        invitation_url = re.search('href="https://.*">', messages[0]['content']['text']).group(0)[6:-1].replace('https://openreview.net', 'http://localhost:3030').replace('&amp;', '&')[:-1]
        helpers.respond_invitation(selenium, request_page, invitation_url, accept=False)

        helpers.await_queue()

        group = client.get_group('NeurIPS.cc/2021/Conference/Reviewers/Declined')
        assert group
        assert len(group.members) == 1
        assert 'reviewer2@mit.edu' in group.members

        messages = client.get_messages(to='reviewer2@mit.edu', subject='[NeurIPS 2021] Reviewer Invitation declined')
        assert messages
        assert len(messages)
        assert messages[0]['content']['text'] =='<p>You have declined the invitation to become a Reviewer for NeurIPS 2021.</p>\n<p>If you would like to change your decision, please follow link in the previous invitation email and click on the &quot;Accept&quot; button.</p>\n'

        client.add_members_to_group('NeurIPS.cc/2021/Conference/Reviewers', ['reviewer2@mit.edu', 'reviewer3@ibm.com', 'reviewer4@fb.com', 'reviewer5@google.com', 'reviewer6@amazon.com'])

    def test_enable_ethics_reviewers(self, client, helpers):

        pc_client=openreview.Client(username='pc@neurips.cc', password='1234')
        request_form=pc_client.get_notes(invitation='openreview.net/Support/-/Request_Form')[0] 

        now = datetime.datetime.utcnow()
        due_date = now + datetime.timedelta(days=3)
        first_date = now + datetime.timedelta(days=1)               

        venue_revision_note = pc_client.post_note(openreview.Note(
            content={
                'title': 'Conference on Neural Information Processing Systems',
                'Official Venue Name': 'Conference on Neural Information Processing Systems',
                'Abbreviated Venue Name': 'NeurIPS 2021',
                'Official Website URL': 'https://neurips.cc',
                'program_chair_emails': ['pc@neurips.cc'],
                'contact_email': 'pc@neurips.cc',
                'ethics_chairs_and_reviewers': 'Yes, our venue has Ethics Chairs and Reviewers',
                'Venue Start Date': '2021/12/01',
                'Submission Deadline': due_date.strftime('%Y/%m/%d'),
                'abstract_registration_deadline': first_date.strftime('%Y/%m/%d'),
                'Location': 'Virtual',
                'How did you hear about us?': 'ML conferences',
                'Expected Submissions': '100'
            },
            forum=request_form.forum,
            invitation='openreview.net/Support/-/Request{}/Revision'.format(request_form.number),
            readers=['{}/Program_Chairs'.format('NeurIPS.cc/2021/Conference'), 'openreview.net/Support'],
            referent=request_form.forum,
            replyto=request_form.forum,
            signatures=['~Program_NeurIPSChair1'],
            writers=[]
        ))
        
        helpers.await_queue()

        assert pc_client.get_group('NeurIPS.cc/2021/Conference/Ethics_Chairs')      
        assert pc_client.get_group('NeurIPS.cc/2021/Conference/Ethics_Reviewers')

        assert pc_client.get_invitation('openreview.net/Support/-/Request{}/Ethics_Review_Stage'.format(request_form.number))
    
    def test_recruit_ethics_reviewers(self, client, request_page, selenium, helpers):

        ## Need super user permission to add the venue to the active_venues group
        pc_client=openreview.Client(username='pc@neurips.cc', password='1234')
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
                'invitation_email_content': 'Dear {{fullname}},\n\nYou have been nominated by the program chair committee of Theoretical Foundations of RL Workshop @ ICML 2020 to serve as {{invitee_role}}.\n\n{{invitation_url}}\n\nIf you have any questions, please contact {{contact_info}}.\n\nCheers!\n\nProgram Chairs'
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
              
        assert client.get_group('NeurIPS.cc/2021/Conference/Ethics_Reviewers')
        assert client.get_group('NeurIPS.cc/2021/Conference/Ethics_Reviewers/Declined')
        group = client.get_group('NeurIPS.cc/2021/Conference/Ethics_Reviewers/Invited')
        assert group
        assert len(group.members) == 1
        assert 'reviewer2@mit.edu' in group.members

        messages = client.get_messages(to='reviewer2@mit.edu', subject='[NeurIPS 2021] Invitation to serve as Ethics Reviewer')
        assert messages and len(messages) == 1
        invitation_url = re.search('href="https://.*">', messages[0]['content']['text']).group(0)[6:-1].replace('https://openreview.net', 'http://localhost:3030').replace('&amp;', '&')[:-1]
        helpers.respond_invitation(selenium, request_page, invitation_url, accept=True)

        helpers.await_queue()

        group = client.get_group('NeurIPS.cc/2021/Conference/Ethics_Reviewers')
        assert group
        assert len(group.members) == 1
        assert 'reviewer2@mit.edu' in group.members

        result = conference.recruit_reviewers(invitees = ['reviewer2@mit.edu'], title = 'Ethics Review invitation', message = '{accept_url}, {decline_url}', reviewers_name = 'Ethics_Reviewers')
        assert result['invited'] == []
        assert result['already_invited'] == {
            'NeurIPS.cc/2021/Conference/Ethics_Reviewers/Invited': ['reviewer2@mit.edu']
        }


    def test_submit_papers(self, test_client, client, helpers):

        ## Need super user permission to add the venue to the active_venues group
        request_form=client.get_notes(invitation='openreview.net/Support/-/Request_Form', sort='tmdate')[0]
        conference=openreview.helpers.get_conference(client, request_form.id)

        domains = ['umass.edu', 'amazon.com', 'fb.com', 'cs.umass.edu', 'google.com', 'mit.edu']
        for i in range(1,6):
            note = openreview.Note(invitation = 'NeurIPS.cc/2021/Conference/-/Submission',
                readers = ['NeurIPS.cc/2021/Conference', 'test@mail.com', 'peter@mail.com', 'andrew@' + domains[i], '~SomeFirstName_User1'],
                writers = [conference.id, '~SomeFirstName_User1', 'peter@mail.com', 'andrew@' + domains[i]],
                signatures = ['~SomeFirstName_User1'],
                content = {
                    'title': 'Paper title ' + str(i) ,
                    'abstract': 'This is an abstract ' + str(i),
                    'authorids': ['test@mail.com', 'peter@mail.com', 'andrew@' + domains[i]],
                    'authors': ['SomeFirstName User', 'Peter SomeLastName', 'Andrew Mc'],
                    'keywords': ['machine learning', 'nlp']
                }
            )
            if i == 1:
                note.readers = note.readers[:-1] + ['~SeniorArea_GoogleChair1', '~SomeFirstName_User1']
                note.writers = note.writers[:-1] + ['~SeniorArea_GoogleChair1', '~SomeFirstName_User1']
                note.content['authors'].append('SeniorArea GoogleChair')
                note.content['authorids'].append('~SeniorArea_GoogleChair1')
                print(note)
            note = test_client.post_note(note)

        conference.setup_first_deadline_stage(force=True)

        blinded_notes = test_client.get_notes(invitation='NeurIPS.cc/2021/Conference/-/Blind_Submission', sort='tmdate')
        assert len(blinded_notes) == 5

        assert blinded_notes[0].readers == ['NeurIPS.cc/2021/Conference', 'NeurIPS.cc/2021/Conference/Paper5/Authors']

        assert client.get_invitation('NeurIPS.cc/2021/Conference/Paper5/-/Withdraw')
        assert client.get_invitation('NeurIPS.cc/2021/Conference/Paper5/-/Desk_Reject')
        assert client.get_invitation('NeurIPS.cc/2021/Conference/Paper5/-/Revision')

        # expire the abstract submission deadline
        pc_client = openreview.Client(username='pc@neurips.cc', password='1234')
        request_form = pc_client.get_notes(invitation='openreview.net/Support/-/Request_Form')[0]

        now = datetime.datetime.utcnow()
        due_date = now + datetime.timedelta(days=3)
        first_date = now + datetime.timedelta(days=-1)

        venue_revision_note = pc_client.post_note(openreview.Note(
            content={
                'title': 'Conference on Neural Information Processing Systems',
                'Official Venue Name': 'Conference on Neural Information Processing Systems',
                'Abbreviated Venue Name': 'NeurIPS 2021',
                'Official Website URL': 'https://neurips.cc',
                'program_chair_emails': ['pc@neurips.cc'],
                'contact_email': 'pc@neurips.cc',
                'ethics_chairs_and_reviewers': 'Yes, our venue has Ethics Chairs and Reviewers',
                'Venue Start Date': '2021/12/01',
                'Submission Deadline': due_date.strftime('%Y/%m/%d'),
                'abstract_registration_deadline': first_date.strftime('%Y/%m/%d'),
                'Location': 'Virtual',
                'How did you hear about us?': 'ML conferences',
                'Expected Submissions': '100'
            },
            forum=request_form.forum,
            invitation='openreview.net/Support/-/Request{}/Revision'.format(request_form.number),
            readers=['{}/Program_Chairs'.format('NeurIPS.cc/2021/Conference'), 'openreview.net/Support'],
            referent=request_form.forum,
            replyto=request_form.forum,
            signatures=['~Program_NeurIPSChair1'],
            writers=[]
        ))

        helpers.await_queue()

        ## Add supplementary material
        submissions=conference.get_submissions(details='original')
        for submission in submissions:
            id = conference.get_invitation_id('Supplementary_Material', submission.number)
            invitation = openreview.Invitation(
                id = id,
                expdate = openreview.tools.datetime_millis(datetime.datetime(2021, 6, 2, 20, 0)),
                readers = [conference.id, conference.get_authors_id(number=submission.number)],
                writers = [conference.id],
                signatures = [conference.id],
                invitees = [conference.get_authors_id(number=submission.number)],
                multiReply = False,
                reply = {
                    'forum': submission.details['original']['id'],
                    'referent': submission.details['original']['id'],
                    'readers': {
                        'values': [
                            conference.id, conference.get_authors_id(number=submission.number)
                        ]
                    },
                    'writers': {
                        'values': [
                            conference.id, conference.get_authors_id(number=submission.number)
                        ]
                    },
                    'signatures': {
                        'values-regex': '~.*'
                    },
                    'content': {
                        'supplementary_material': {
                            'order': 1,
                            'required': True,
                            'description': 'You can upload a single ZIP or a single PDF or a single MP4 file. Make sure that you do not use specialized codecs and the video runs on all computers. The maximum file size is 100MB.',
                            'value-file': {
                                'fileTypes': [
                                    'pdf',
                                    'zip',
                                    'mp4'
                                ],
                                'size': 100
                            }
                        }
                    }
                }
            )
            client.post_invitation(invitation)

        assert client.get_invitation('NeurIPS.cc/2021/Conference/Paper5/-/Supplementary_Material')

        ## Post a revision, add an author and check the permissions
        submissions=test_client.get_notes(invitation='NeurIPS.cc/2021/Conference/-/Submission', sort='number:desc')
        note = openreview.Note(referent=submissions[0].id,
            forum = submissions[0].id,
            invitation = 'NeurIPS.cc/2021/Conference/Paper5/-/Revision',
            readers = ['NeurIPS.cc/2021/Conference', 'NeurIPS.cc/2021/Conference/Paper5/Authors'],
            writers = [conference.id, 'NeurIPS.cc/2021/Conference/Paper5/Authors'],
            signatures = ['NeurIPS.cc/2021/Conference/Paper5/Authors'],
            content = {
                'title': 'Paper title 5' ,
                'abstract': 'This is an abstract 5 Rev',
                'authorids': ['test@mail.com', 'peter@mail.com', 'another_andrew@mit.edu'],
                'authors': ['SomeFirstName User', 'Peter SomeLastName', 'Another Andrew']
            }
        )
        note = test_client.post_note(note)

        updated_note=test_client.get_note(submissions[0].id)
        assert updated_note
        assert updated_note.readers == ['NeurIPS.cc/2021/Conference', 'test@mail.com', 'peter@mail.com', 'another_andrew@mit.edu', '~SomeFirstName_User1']
        assert updated_note.writers == ['NeurIPS.cc/2021/Conference', 'test@mail.com', 'peter@mail.com', 'another_andrew@mit.edu', '~SomeFirstName_User1']

        helpers.await_queue()

        author_group=test_client.get_group('NeurIPS.cc/2021/Conference/Paper5/Authors')
        assert author_group
        assert author_group.members == ['test@mail.com', 'peter@mail.com', 'another_andrew@mit.edu']

        sac_client = openreview.Client(username='another_andrew@mit.edu', password='1234')
        sac_notes = sac_client.get_notes(invitation='NeurIPS.cc/2021/Conference/-/Submission')
        assert len(sac_notes) == 1
        assert sac_notes[0].id == note.forum


    def test_post_submission_stage(self, conference, helpers, test_client, client, request_page, selenium):

        #conference.setup_final_deadline_stage(force=True)
        pc_client=openreview.Client(username='pc@neurips.cc', password='1234')
        request_form=pc_client.get_notes(invitation='openreview.net/Support/-/Request_Form')[0]

        post_submission_note=pc_client.post_note(openreview.Note(
            content= {
                'force': 'Yes',
                'hide_fields': ['keywords'],
                'submission_readers': 'All program committee (all reviewers, all area chairs, all senior area chairs if applicable)'
            },
            forum= request_form.id,
            invitation= f'openreview.net/Support/-/Request{request_form.number}/Post_Submission',
            readers= ['NeurIPS.cc/2021/Conference/Program_Chairs', 'openreview.net/Support'],
            referent= request_form.id,
            replyto= request_form.id,
            signatures= ['~Program_NeurIPSChair1'],
            writers= [],
        ))

        helpers.await_queue()

        process_logs = client.get_process_logs(id=post_submission_note.id)
        assert len(process_logs) == 1
        assert process_logs[0]['status'] == 'ok'

        submissions = conference.get_submissions(sort='tmdate')
        assert len(submissions) == 5

        assert submissions[0].content['keywords'] == ''

        assert submissions[0].readers == ['NeurIPS.cc/2021/Conference',
            'NeurIPS.cc/2021/Conference/Senior_Area_Chairs',
            'NeurIPS.cc/2021/Conference/Area_Chairs',
            'NeurIPS.cc/2021/Conference/Reviewers',
            'NeurIPS.cc/2021/Conference/Paper5/Authors']

        assert client.get_group('NeurIPS.cc/2021/Conference/Paper5/Senior_Area_Chairs').readers == ['NeurIPS.cc/2021/Conference',
            'NeurIPS.cc/2021/Conference/Program_Chairs',
            'NeurIPS.cc/2021/Conference/Paper5/Senior_Area_Chairs',
            'NeurIPS.cc/2021/Conference/Paper5/Area_Chairs',
            'NeurIPS.cc/2021/Conference/Paper5/Reviewers']
        assert client.get_group('NeurIPS.cc/2021/Conference/Paper5/Senior_Area_Chairs').nonreaders == ['NeurIPS.cc/2021/Conference/Paper5/Authors']

        assert client.get_group('NeurIPS.cc/2021/Conference/Paper5/Area_Chairs').readers == ['NeurIPS.cc/2021/Conference',
            'NeurIPS.cc/2021/Conference/Program_Chairs',
            'NeurIPS.cc/2021/Conference/Paper5/Senior_Area_Chairs',
            'NeurIPS.cc/2021/Conference/Paper5/Area_Chairs',
            'NeurIPS.cc/2021/Conference/Paper5/Reviewers']

        assert client.get_group('NeurIPS.cc/2021/Conference/Paper5/Area_Chairs').deanonymizers == ['NeurIPS.cc/2021/Conference',
            'NeurIPS.cc/2021/Conference/Program_Chairs',
            'NeurIPS.cc/2021/Conference/Paper5/Senior_Area_Chairs',
            'NeurIPS.cc/2021/Conference/Paper5/Area_Chairs',
            'NeurIPS.cc/2021/Conference/Paper5/Reviewers']

        assert client.get_group('NeurIPS.cc/2021/Conference/Paper5/Area_Chairs').nonreaders == ['NeurIPS.cc/2021/Conference/Paper5/Authors']

        assert client.get_group('NeurIPS.cc/2021/Conference/Paper5/Reviewers').readers == ['NeurIPS.cc/2021/Conference',
            'NeurIPS.cc/2021/Conference/Paper5/Senior_Area_Chairs',
            'NeurIPS.cc/2021/Conference/Paper5/Area_Chairs',
            'NeurIPS.cc/2021/Conference/Paper5/Reviewers']

        assert client.get_group('NeurIPS.cc/2021/Conference/Paper5/Reviewers').deanonymizers == ['NeurIPS.cc/2021/Conference',
            'NeurIPS.cc/2021/Conference/Program_Chairs',
            'NeurIPS.cc/2021/Conference/Paper5/Senior_Area_Chairs',
            'NeurIPS.cc/2021/Conference/Paper5/Area_Chairs',
            'NeurIPS.cc/2021/Conference/Paper5/Reviewers']

        assert client.get_group('NeurIPS.cc/2021/Conference/Paper5/Reviewers').nonreaders == ['NeurIPS.cc/2021/Conference/Paper5/Authors']

        ## Open Author paper ranking
        now = datetime.datetime.utcnow()
        conference.open_paper_ranking(committee_id=conference.get_authors_id(), due_date=now + datetime.timedelta(days=3))

        authors_url = 'http://localhost:3030/group?id=NeurIPS.cc/2021/Conference/Authors'
        request_page(selenium, authors_url, test_client.token, by=By.CLASS_NAME, wait_for_element='tag-widget')

        assert selenium.find_elements_by_class_name('tag-widget')

        client.post_invitation(openreview.Invitation(id=f'{conference.get_authors_id()}/-/Perceived_Likelihood',
            invitees=[conference.get_authors_id()],
            readers=[conference.get_authors_id()],
            signatures=[conference.id],
            writers=[conference.id],
            multiReply=False,
            reply={
                'invitation': f'{conference.id}/-/Blind_Submission',
                'readers': {
                    'values-copied': ['{signatures}']
                },
                'writers': {
                    'values-copied': ['{signatures}']
                },
                'signatures': {
                    'values-regex': '~.*'
                },
                'content': {
                    'percent_chance': {
                        'description': 'What is your best estimate of the percent chance that this submission will be accepted?  Please use a scale of 0 to 100, where 0 = “no chance” and 100 = “certain to be accepted',
                        'value-regex': '^(0|[1-9][0-9]?|100)$',
                        'required': True
                    }
                }

            }))

    def test_setup_matching(self, conference, client, helpers):

        now = datetime.datetime.utcnow()

        pc_client=openreview.Client(username='pc@neurips.cc', password='1234')
        submissions=conference.get_submissions(sort='tmdate')

        with open(os.path.join(os.path.dirname(__file__), 'data/reviewer_affinity_scores.csv'), 'w') as file_handle:
            writer = csv.writer(file_handle)
            for submission in submissions:
                writer.writerow([submission.id, '~Area_IBMChair1', round(random.random(), 2)])
                writer.writerow([submission.id, '~Area_GoogleChair1', round(random.random(), 2)])
                writer.writerow([submission.id, '~Area_UMassChair1', round(random.random(), 2)])

        conference.setup_matching(committee_id=conference.get_area_chairs_id(), build_conflicts='neurips', affinity_score_file=os.path.join(os.path.dirname(__file__), 'data/reviewer_affinity_scores.csv'))

        with open(os.path.join(os.path.dirname(__file__), 'data/reviewer_affinity_scores.csv'), 'w') as file_handle:
            writer = csv.writer(file_handle)
            for submission in submissions:
                writer.writerow([submission.id, '~Reviewer_UMass1', round(random.random(), 2)])
                writer.writerow([submission.id, '~Reviewer_MIT1', round(random.random(), 2)])
                writer.writerow([submission.id, '~Reviewer_IBM1', round(random.random(), 2)])
                writer.writerow([submission.id, '~Reviewer_Facebook1', round(random.random(), 2)])
                writer.writerow([submission.id, '~Reviewer_Google1', round(random.random(), 2)])


        conference.setup_matching(committee_id=conference.get_reviewers_id(), build_conflicts='neurips', affinity_score_file=os.path.join(os.path.dirname(__file__), 'data/reviewer_affinity_scores.csv'))

        conference.set_bid_stage(openreview.BidStage(due_date=now + datetime.timedelta(days=3), committee_id='NeurIPS.cc/2021/Conference/Area_Chairs', score_ids=['NeurIPS.cc/2021/Conference/Area_Chairs/-/Affinity_Score'], allow_conflicts_bids=True))
        conference.set_bid_stage(openreview.BidStage(due_date=now + datetime.timedelta(days=3), committee_id='NeurIPS.cc/2021/Conference/Reviewers', score_ids=['NeurIPS.cc/2021/Conference/Reviewers/-/Affinity_Score'], allow_conflicts_bids=True))

        assert len(client.get_edges(invitation='NeurIPS.cc/2021/Conference/Reviewers/-/Custom_Max_Papers')) == 1
        ac_quotas=client.get_edges(invitation='NeurIPS.cc/2021/Conference/Area_Chairs/-/Custom_Max_Papers')
        assert len(ac_quotas) == 1
        assert ac_quotas[0].weight == 3
        assert ac_quotas[0].head == 'NeurIPS.cc/2021/Conference/Area_Chairs'
        assert ac_quotas[0].tail == '~Area_IBMChair1'


        ## Reviewer quotas
        client.post_edge(openreview.Edge(
            invitation='NeurIPS.cc/2021/Conference/Reviewers/-/Custom_Max_Papers',
            readers = [conference.id, 'NeurIPS.cc/2021/Conference/Senior_Area_Chairs', 'NeurIPS.cc/2021/Conference/Area_Chairs', '~Reviewer_MIT1'],
            writers = [conference.id],
            signatures = [conference.id],
            head = 'NeurIPS.cc/2021/Conference/Reviewers',
            tail = '~Reviewer_MIT1',
            weight = 4
        ))

        client.post_edge(openreview.Edge(
            invitation='NeurIPS.cc/2021/Conference/Reviewers/-/Custom_Max_Papers',
            readers = [conference.id, 'NeurIPS.cc/2021/Conference/Senior_Area_Chairs', 'NeurIPS.cc/2021/Conference/Area_Chairs', '~Reviewer_IBM1'],
            writers = [conference.id],
            signatures = [conference.id],
            head = 'NeurIPS.cc/2021/Conference/Reviewers',
            tail = '~Reviewer_IBM1',
            weight = 1
        ))

        client.post_edge(openreview.Edge(
            invitation='NeurIPS.cc/2021/Conference/Reviewers/-/Custom_Max_Papers',
            readers = [conference.id, 'NeurIPS.cc/2021/Conference/Senior_Area_Chairs', 'NeurIPS.cc/2021/Conference/Area_Chairs', '~Reviewer_Facebook1'],
            writers = [conference.id],
            signatures = [conference.id],
            head = 'NeurIPS.cc/2021/Conference/Reviewers',
            tail = '~Reviewer_Facebook1',
            weight = 6
        ))

        client.post_edge(openreview.Edge(
            invitation='NeurIPS.cc/2021/Conference/Reviewers/-/Custom_Max_Papers',
            readers = [conference.id, 'NeurIPS.cc/2021/Conference/Senior_Area_Chairs', 'NeurIPS.cc/2021/Conference/Area_Chairs', '~Reviewer_Google1'],
            writers = [conference.id],
            signatures = [conference.id],
            head = 'NeurIPS.cc/2021/Conference/Reviewers',
            tail = '~Reviewer_Google1',
            weight = 6
        ))

        ## AC assignments
        client.post_edge(openreview.Edge(
            invitation='NeurIPS.cc/2021/Conference/Area_Chairs/-/Proposed_Assignment',
            readers = [conference.id, f'NeurIPS.cc/2021/Conference/Paper{submissions[0].number}/Senior_Area_Chairs', '~Area_IBMChair1'],
            writers = [conference.id, f'NeurIPS.cc/2021/Conference/Paper{submissions[0].number}/Senior_Area_Chairs'],
            nonreaders = [f'NeurIPS.cc/2021/Conference/Paper{submissions[0].number}/Authors'],
            signatures = [conference.id],
            head = submissions[0].id,
            tail = '~Area_IBMChair1',
            label = 'ac-matching',
            weight = 0.94
        ))
        client.post_edge(openreview.Edge(
            invitation='NeurIPS.cc/2021/Conference/Area_Chairs/-/Proposed_Assignment',
            readers = [conference.id, f'NeurIPS.cc/2021/Conference/Paper{submissions[1].number}/Senior_Area_Chairs', '~Area_IBMChair1'],
            writers = [conference.id, f'NeurIPS.cc/2021/Conference/Paper{submissions[1].number}/Senior_Area_Chairs'],
            nonreaders = [f'NeurIPS.cc/2021/Conference/Paper{submissions[1].number}/Authors'],
            signatures = [conference.id],
            head = submissions[1].id,
            tail = '~Area_IBMChair1',
            label = 'ac-matching',
            weight = 0.94
        ))
        client.post_edge(openreview.Edge(
            invitation='NeurIPS.cc/2021/Conference/Area_Chairs/-/Proposed_Assignment',
            readers = [conference.id, f'NeurIPS.cc/2021/Conference/Paper{submissions[2].number}/Senior_Area_Chairs', '~Area_UMassChair1'],
            writers = [conference.id, f'NeurIPS.cc/2021/Conference/Paper{submissions[2].number}/Senior_Area_Chairs'],
            nonreaders = [f'NeurIPS.cc/2021/Conference/Paper{submissions[2].number}/Authors'],
            signatures = [conference.id],
            head = submissions[2].id,
            tail = '~Area_UMassChair1',
            label = 'ac-matching',
            weight = 0.94
        ))
        client.post_edge(openreview.Edge(
            invitation='NeurIPS.cc/2021/Conference/Area_Chairs/-/Proposed_Assignment',
            readers = [conference.id, f'NeurIPS.cc/2021/Conference/Paper{submissions[3].number}/Senior_Area_Chairs', '~Area_GoogleChair1'],
            writers = [conference.id, f'NeurIPS.cc/2021/Conference/Paper{submissions[3].number}/Senior_Area_Chairs'],
            nonreaders = [f'NeurIPS.cc/2021/Conference/Paper{submissions[3].number}/Authors'],
            signatures = [conference.id],
            head = submissions[3].id,
            tail = '~Area_GoogleChair1',
            label = 'ac-matching',
            weight = 0.94
        ))
        client.post_edge(openreview.Edge(
            invitation='NeurIPS.cc/2021/Conference/Area_Chairs/-/Proposed_Assignment',
            readers = [conference.id, f'NeurIPS.cc/2021/Conference/Paper{submissions[4].number}/Senior_Area_Chairs', '~Area_GoogleChair1'],
            writers = [conference.id, f'NeurIPS.cc/2021/Conference/Paper{submissions[4].number}/Senior_Area_Chairs'],
            nonreaders = [f'NeurIPS.cc/2021/Conference/Paper{submissions[4].number}/Authors'],
            signatures = [conference.id],
            head = submissions[4].id,
            tail = '~Area_GoogleChair1',
            label = 'ac-matching',
            weight = 0.94
        ))


        ## Deploy assignments
        with pytest.raises(openreview.OpenReviewException, match=r'AC assignments must be deployed first'):
            conference.set_assignments(assignment_title='sac-matching', committee_id='NeurIPS.cc/2021/Conference/Senior_Area_Chairs', overwrite=True)

        conference.set_assignments(assignment_title='ac-matching', committee_id='NeurIPS.cc/2021/Conference/Area_Chairs', overwrite=True)
        conference.set_assignments(assignment_title='sac-matching', committee_id='NeurIPS.cc/2021/Conference/Senior_Area_Chairs', overwrite=True)

        helpers.await_queue()

        assert ['~Area_IBMChair1'] == pc_client.get_group('NeurIPS.cc/2021/Conference/Paper5/Area_Chairs').members
        assert ['~Area_IBMChair1'] ==  pc_client.get_group('NeurIPS.cc/2021/Conference/Paper4/Area_Chairs').members
        assert ['~Area_UMassChair1'] ==  pc_client.get_group('NeurIPS.cc/2021/Conference/Paper3/Area_Chairs').members
        assert ['~Area_GoogleChair1'] == pc_client.get_group('NeurIPS.cc/2021/Conference/Paper2/Area_Chairs').members
        assert ['~Area_GoogleChair1'] == pc_client.get_group('NeurIPS.cc/2021/Conference/Paper1/Area_Chairs').members

        assert len(pc_client.get_edges(invitation='NeurIPS.cc/2021/Conference/Area_Chairs/-/Assignment')) == 5

        assert ['~SeniorArea_GoogleChair1'] == pc_client.get_group('NeurIPS.cc/2021/Conference/Paper5/Senior_Area_Chairs').members
        assert ['~SeniorArea_GoogleChair1'] == pc_client.get_group('NeurIPS.cc/2021/Conference/Paper4/Senior_Area_Chairs').members
        assert ['~SeniorArea_GoogleChair1'] == pc_client.get_group('NeurIPS.cc/2021/Conference/Paper3/Senior_Area_Chairs').members
        assert ['~SeniorArea_NeurIPSChair1'] == pc_client.get_group('NeurIPS.cc/2021/Conference/Paper2/Senior_Area_Chairs').members
        assert ['~SeniorArea_NeurIPSChair1'] == pc_client.get_group('NeurIPS.cc/2021/Conference/Paper1/Senior_Area_Chairs').members

        assert len(pc_client.get_edges(invitation='NeurIPS.cc/2021/Conference/Senior_Area_Chairs/-/Assignment')) == 3

        ## Check if the SAC can edit the AC assignments
        print('http://localhost:3030/edges/browse?traverse=NeurIPS.cc/2021/Conference/Area_Chairs/-/Assignment&edit=NeurIPS.cc/2021/Conference/Area_Chairs/-/Assignment&browse=NeurIPS.cc/2021/Conference/Area_Chairs/-/Affinity_Score&hide=NeurIPS.cc/2021/Conference/Area_Chairs/-/Conflict&maxColumns=2')
        #assert False

        ## Reviewer assignments
        # Paper 5
        helpers.create_reviewer_edge(client, conference, 'Proposed_Assignment', submissions[0], '~Reviewer_UMass1', label='reviewer-matching', weight=None)
        helpers.create_reviewer_edge(client, conference, 'Proposed_Assignment', submissions[0], '~Reviewer_Google1', label='reviewer-matching', weight=None)
        helpers.create_reviewer_edge(client, conference, 'Aggregate_Score', submissions[0], '~Reviewer_UMass1', label='reviewer-matching', weight=0.98)
        helpers.create_reviewer_edge(client, conference, 'Aggregate_Score', submissions[0], '~Reviewer_MIT1', label='reviewer-matching', weight=0.87)
        helpers.create_reviewer_edge(client, conference, 'Aggregate_Score', submissions[0], '~Reviewer_IBM1', label='reviewer-matching', weight=0.56)
        helpers.create_reviewer_edge(client, conference, 'Aggregate_Score', submissions[0], '~Reviewer_Facebook1', label='reviewer-matching', weight=0.45)
        helpers.create_reviewer_edge(client, conference, 'Aggregate_Score', submissions[0], '~Reviewer_Google1', label='reviewer-matching', weight=0.33)

        # Paper 4
        helpers.create_reviewer_edge(client, conference, 'Proposed_Assignment', submissions[1], '~Reviewer_UMass1', label='reviewer-matching', weight=None)
        helpers.create_reviewer_edge(client, conference, 'Proposed_Assignment', submissions[1], '~Reviewer_Facebook1', label='reviewer-matching', weight=None)
        helpers.create_reviewer_edge(client, conference, 'Aggregate_Score', submissions[1], '~Reviewer_UMass1', label='reviewer-matching', weight=0.98)
        helpers.create_reviewer_edge(client, conference, 'Aggregate_Score', submissions[1], '~Reviewer_MIT1', label='reviewer-matching', weight=0.87)
        helpers.create_reviewer_edge(client, conference, 'Aggregate_Score', submissions[1], '~Reviewer_IBM1', label='reviewer-matching', weight=0.56)
        helpers.create_reviewer_edge(client, conference, 'Aggregate_Score', submissions[1], '~Reviewer_Facebook1', label='reviewer-matching', weight=0.89)
        helpers.create_reviewer_edge(client, conference, 'Aggregate_Score', submissions[1], '~Reviewer_Google1', label='reviewer-matching', weight=0.33)

        # Paper 3
        helpers.create_reviewer_edge(client, conference, 'Proposed_Assignment', submissions[2], '~Reviewer_UMass1', label='reviewer-matching', weight=None)
        helpers.create_reviewer_edge(client, conference, 'Proposed_Assignment', submissions[2], '~Reviewer_Google1', label='reviewer-matching', weight=None)
        helpers.create_reviewer_edge(client, conference, 'Aggregate_Score', submissions[2], '~Reviewer_UMass1', label='reviewer-matching', weight=0.33)
        helpers.create_reviewer_edge(client, conference, 'Aggregate_Score', submissions[2], '~Reviewer_MIT1', label='reviewer-matching', weight=0.87)
        helpers.create_reviewer_edge(client, conference, 'Aggregate_Score', submissions[2], '~Reviewer_IBM1', label='reviewer-matching', weight=0.56)
        helpers.create_reviewer_edge(client, conference, 'Aggregate_Score', submissions[2], '~Reviewer_Facebook1', label='reviewer-matching', weight=0.89)
        helpers.create_reviewer_edge(client, conference, 'Aggregate_Score', submissions[2], '~Reviewer_Google1', label='reviewer-matching', weight=0.98)

        # Paper 4
        helpers.create_reviewer_edge(client, conference, 'Proposed_Assignment', submissions[3], '~Reviewer_Facebook1', label='reviewer-matching', weight=None)
        helpers.create_reviewer_edge(client, conference, 'Proposed_Assignment', submissions[3], '~Reviewer_IBM1', label='reviewer-matching', weight=None)
        helpers.create_reviewer_edge(client, conference, 'Aggregate_Score', submissions[3], '~Reviewer_UMass1', label='reviewer-matching', weight=0.33)
        helpers.create_reviewer_edge(client, conference, 'Aggregate_Score', submissions[3], '~Reviewer_MIT1', label='reviewer-matching', weight=0.87)
        helpers.create_reviewer_edge(client, conference, 'Aggregate_Score', submissions[3], '~Reviewer_IBM1', label='reviewer-matching', weight=0.56)
        helpers.create_reviewer_edge(client, conference, 'Aggregate_Score', submissions[3], '~Reviewer_Facebook1', label='reviewer-matching', weight=0.89)
        helpers.create_reviewer_edge(client, conference, 'Aggregate_Score', submissions[3], '~Reviewer_Google1', label='reviewer-matching', weight=0.98)

        # Paper 1
        helpers.create_reviewer_edge(client, conference, 'Proposed_Assignment', submissions[4], '~Reviewer_UMass1', label='reviewer-matching', weight=None)
        helpers.create_reviewer_edge(client, conference, 'Proposed_Assignment', submissions[4], '~Reviewer_MIT1', label='reviewer-matching', weight=None)
        helpers.create_reviewer_edge(client, conference, 'Aggregate_Score', submissions[4], '~Reviewer_UMass1', label='reviewer-matching', weight=0.33)
        helpers.create_reviewer_edge(client, conference, 'Aggregate_Score', submissions[4], '~Reviewer_MIT1', label='reviewer-matching', weight=0.87)
        helpers.create_reviewer_edge(client, conference, 'Aggregate_Score', submissions[4], '~Reviewer_IBM1', label='reviewer-matching', weight=0.56)
        helpers.create_reviewer_edge(client, conference, 'Aggregate_Score', submissions[4], '~Reviewer_Facebook1', label='reviewer-matching', weight=0.89)
        helpers.create_reviewer_edge(client, conference, 'Aggregate_Score', submissions[4], '~Reviewer_Google1', label='reviewer-matching', weight=0.98)

        # start='NeurIPS.cc/2021/Conference/Area_Chairs/-/Proposed_Assignment,label:ac-matching,tail:~Area_IBMChair1'
        # traverse='NeurIPS.cc/2021/Conference/Reviewers/-/Proposed_Assignment,label:reviewer-matching'
        # browse='NeurIPS.cc/2021/Conference/Reviewers/-/Aggregate_Score,label:reviewer-matching;NeurIPS.cc/2021/Conference/Reviewers/-/Affinity_Score;NeurIPS.cc/2021/Conference/Reviewers/-/Conflict'
        # hide='NeurIPS.cc/2021/Conference/Reviewers/-/Conflict'
        # url=f'http://localhost:3030/edges/browse?start={start}&traverse={traverse}&edit={traverse}&browse={browse}&maxColumns=2'

        # print(url)
        # assert False

    def test_ac_reassignment(self, conference, helpers, client):

        pc_client=openreview.Client(username='pc@neurips.cc', password='1234')
        submissions=conference.get_submissions(sort='tmdate')

        assert len(pc_client.get_edges(invitation='NeurIPS.cc/2021/Conference/Senior_Area_Chairs/-/Assignment')) == 3
        assert len(pc_client.get_edges(invitation='NeurIPS.cc/2021/Conference/Area_Chairs/-/Assignment')) == 5

        ac_assignment = pc_client.get_edges(invitation='NeurIPS.cc/2021/Conference/Area_Chairs/-/Assignment', head=submissions[0].id)[0]

        ## Remove AC assignment
        ac_assignment.ddate = openreview.tools.datetime_millis(datetime.datetime.utcnow())
        pc_client.post_edge(ac_assignment)

        helpers.await_queue()

        assert len(pc_client.get_edges(invitation='NeurIPS.cc/2021/Conference/Senior_Area_Chairs/-/Assignment')) == 3
        assert len(pc_client.get_edges(invitation='NeurIPS.cc/2021/Conference/Area_Chairs/-/Assignment')) == 4

        assert [] == pc_client.get_group('NeurIPS.cc/2021/Conference/Paper5/Area_Chairs').members
        assert [] == pc_client.get_group('NeurIPS.cc/2021/Conference/Paper5/Senior_Area_Chairs').members

        ## Add AC assignment
        ac_assignment.ddate = None
        pc_client.post_edge(ac_assignment)

        helpers.await_queue()

        assert len(pc_client.get_edges(invitation='NeurIPS.cc/2021/Conference/Senior_Area_Chairs/-/Assignment')) == 3
        assert len(pc_client.get_edges(invitation='NeurIPS.cc/2021/Conference/Area_Chairs/-/Assignment')) == 5

        assert ['~Area_IBMChair1'] == pc_client.get_group('NeurIPS.cc/2021/Conference/Paper5/Area_Chairs').members
        assert ['~SeniorArea_GoogleChair1'] == pc_client.get_group('NeurIPS.cc/2021/Conference/Paper5/Senior_Area_Chairs').members

        sac_assignment = pc_client.get_edges(invitation='NeurIPS.cc/2021/Conference/Senior_Area_Chairs/-/Assignment', head='~Area_IBMChair1')[0]
        assert sac_assignment.tail == '~SeniorArea_GoogleChair1'

        ## Add SAC assignment
        sac_assignment.ddate = openreview.tools.datetime_millis(datetime.datetime.utcnow())
        pc_client.post_edge(sac_assignment)

        helpers.await_queue()

        assert len(pc_client.get_edges(invitation='NeurIPS.cc/2021/Conference/Senior_Area_Chairs/-/Assignment')) == 2
        assert len(pc_client.get_edges(invitation='NeurIPS.cc/2021/Conference/Area_Chairs/-/Assignment')) == 5

        assert ['~Area_IBMChair1'] == pc_client.get_group('NeurIPS.cc/2021/Conference/Paper5/Area_Chairs').members
        assert [] == pc_client.get_group('NeurIPS.cc/2021/Conference/Paper5/Senior_Area_Chairs').members

        assert ['~Area_IBMChair1'] == pc_client.get_group('NeurIPS.cc/2021/Conference/Paper4/Area_Chairs').members
        assert [] == pc_client.get_group('NeurIPS.cc/2021/Conference/Paper4/Senior_Area_Chairs').members

        ## Add SAC assignment
        sac_assignment.ddate = None
        pc_client.post_edge(sac_assignment)

        helpers.await_queue()

        assert len(pc_client.get_edges(invitation='NeurIPS.cc/2021/Conference/Senior_Area_Chairs/-/Assignment')) == 3
        assert len(pc_client.get_edges(invitation='NeurIPS.cc/2021/Conference/Area_Chairs/-/Assignment')) == 5

        assert ['~Area_IBMChair1'] == pc_client.get_group('NeurIPS.cc/2021/Conference/Paper5/Area_Chairs').members
        assert ['~SeniorArea_GoogleChair1'] == pc_client.get_group('NeurIPS.cc/2021/Conference/Paper5/Senior_Area_Chairs').members

        assert ['~Area_IBMChair1'] == pc_client.get_group('NeurIPS.cc/2021/Conference/Paper4/Area_Chairs').members
        assert ['~SeniorArea_GoogleChair1'] == pc_client.get_group('NeurIPS.cc/2021/Conference/Paper4/Senior_Area_Chairs').members


    def test_reassignment_stage(self, conference, helpers, client, selenium, request_page):

        now = datetime.datetime.utcnow()
        pc_client=openreview.Client(username='pc@neurips.cc', password='1234')
        email_template='''
As an Area Chair for NeurIPS 2021, I'd like to ask for your expert review of a submission, titled: {title}:

{abstract}

If you accept, you will not be added to the general list of NeurIPS reviewers and will not be assigned additional submissions unless you explicitly agree to review them.

To respond this request, please follow this link: {invitation_url}

If you accept, I would need the review by Friday, July 16.

If you don’t have an OpenReview account, you will be asked to create one using the email address at which you received this message.  Once you sign up, you will receive a separate email with instructions for accessing the paper within a few days.

I really hope you can help out with reviewing this paper!

Thank you,
{inviter_id}
{inviter_name}({inviter_email})
        '''

        conference.setup_assignment_recruitment(conference.get_reviewers_id(), '12345678', now + datetime.timedelta(days=3), assignment_title='reviewer-matching', invitation_labels={ 'Invite': 'Invitation Sent', 'Invited': 'Invitation Sent' }, email_template=email_template)

        start='NeurIPS.cc/2021/Conference/Area_Chairs/-/Assignment,tail:~Area_IBMChair1'
        traverse='NeurIPS.cc/2021/Conference/Reviewers/-/Proposed_Assignment,label:reviewer-matching'
        edit='NeurIPS.cc/2021/Conference/Reviewers/-/Proposed_Assignment,label:reviewer-matching;NeurIPS.cc/2021/Conference/Reviewers/-/Invite_Assignment;NeurIPS.cc/2021/Conference/Reviewers/-/Custom_Max_Papers,head:ignore'
        browse='NeurIPS.cc/2021/Conference/Reviewers/-/Aggregate_Score,label:reviewer-matching;NeurIPS.cc/2021/Conference/Reviewers/-/Affinity_Score;NeurIPS.cc/2021/Conference/Reviewers/-/Conflict'
        hide='NeurIPS.cc/2021/Conference/Reviewers/-/Conflict'
        url=f'http://localhost:3030/edges/browse?start={start}&traverse={traverse}&edit={edit}&browse={browse}&maxColumns=2'

        print(url)

        ac_client=openreview.Client(username='ac1@mit.edu', password='1234')
        submission=conference.get_submissions(sort='tmdate')[0]
        signatory_group=ac_client.get_groups(regex='NeurIPS.cc/2021/Conference/Paper5/Area_Chair_')[0]

        ## Invite external reviewer 1
        posted_edge=ac_client.post_edge(openreview.Edge(
            invitation='NeurIPS.cc/2021/Conference/Reviewers/-/Invite_Assignment',
            readers = [conference.id, 'NeurIPS.cc/2021/Conference/Paper5/Senior_Area_Chairs', 'NeurIPS.cc/2021/Conference/Paper5/Area_Chairs', 'external_reviewer1@amazon.com'],
            nonreaders = ['NeurIPS.cc/2021/Conference/Paper5/Authors'],
            writers = [conference.id],
            signatures = [signatory_group.id],
            head = submission.id,
            tail = 'external_reviewer1@amazon.com',
            label = 'Invitation Sent'
        ))

        helpers.await_queue()

        process_logs = client.get_process_logs(id=posted_edge.id)
        assert len(process_logs) == 1
        assert process_logs[0]['status'] == 'ok'

        ## External reviewer is invited
        invite_edges=pc_client.get_edges(invitation='NeurIPS.cc/2021/Conference/Reviewers/-/Invite_Assignment', head=submission.id)
        assert len(invite_edges) == 1
        assert invite_edges[0].tail == '~External_Reviewer_Amazon1'
        assert invite_edges[0].label == 'Invitation Sent'

        assert client.get_groups('NeurIPS.cc/2021/Conference/Paper5/External_Reviewers/Invited', member='~External_Reviewer_Amazon1')
        assert client.get_groups('NeurIPS.cc/2021/Conference/External_Reviewers/Invited', member='~External_Reviewer_Amazon1')

        assert not client.get_groups('NeurIPS.cc/2021/Conference/Paper5/External_Reviewers', member='~External_Reviewer_Amazon1')
        assert not client.get_groups('NeurIPS.cc/2021/Conference/External_Reviewers', member='~External_Reviewer_Amazon1')
        assert not client.get_groups('NeurIPS.cc/2021/Conference/Reviewers', member='~External_Reviewer_Amazon1')

        ## External reviewer accepts the invitation
        messages = client.get_messages(to='external_reviewer1@amazon.com', subject='[NeurIPS 2021] Invitation to review paper titled Paper title 5')
        assert messages and len(messages) == 1
        invitation_message=messages[0]['content']['text']

        invalid_accept_url = re.search('href="https://.*">', messages[0]['content']['text']).group(0)[6:-1].replace('https://openreview.net', 'http://localhost:3030').replace('&amp;', '&')[:-1].replace('user=~External_Reviewer_Amazon1', 'user=~External_Reviewer_Amazon2').replace('&amp;', '&')
        helpers.respond_invitation(selenium, request_page, invalid_accept_url, accept=True)
        error_message = selenium.find_element_by_class_name('important_message')
        assert 'Wrong key, please refer back to the recruitment email' == error_message.text

        invitation_url = re.search('href="https://.*">', messages[0]['content']['text']).group(0)[6:-1].replace('https://openreview.net', 'http://localhost:3030').replace('&amp;', '&')[:-1]

        helpers.respond_invitation(selenium, request_page, invitation_url, accept=True)
        notes = selenium.find_element_by_class_name("note_editor")
        assert notes
        messages = notes.find_elements_by_tag_name("h3")
        assert messages
        assert 'Thank you for accepting this invitation from Conference on Neural Information Processing Systems.' == messages[0].text

        helpers.await_queue()

        process_logs = client.get_process_logs(invitation='NeurIPS.cc/2021/Conference/Reviewers/-/Proposed_Assignment_Recruitment')
        assert len(process_logs) == 1
        assert process_logs[0]['status'] == 'ok'

        ## Externel reviewer is assigned to the paper 5
        invite_edges=pc_client.get_edges(invitation='NeurIPS.cc/2021/Conference/Reviewers/-/Invite_Assignment', head=submission.id)
        assert len(invite_edges) == 1
        assert invite_edges[0].tail == '~External_Reviewer_Amazon1'
        assert invite_edges[0].label == 'Accepted'

        assert client.get_groups('NeurIPS.cc/2021/Conference/Paper5/External_Reviewers/Invited', member='~External_Reviewer_Amazon1')
        assert client.get_groups('NeurIPS.cc/2021/Conference/External_Reviewers/Invited', member='~External_Reviewer_Amazon1')

        assert client.get_groups('NeurIPS.cc/2021/Conference/Paper5/External_Reviewers', member='~External_Reviewer_Amazon1')
        assert client.get_groups('NeurIPS.cc/2021/Conference/External_Reviewers', member='~External_Reviewer_Amazon1')
        assert not client.get_groups('NeurIPS.cc/2021/Conference/Reviewers', member='~External_Reviewer_Amazon1')

        assignment_edges=pc_client.get_edges(invitation='NeurIPS.cc/2021/Conference/Reviewers/-/Proposed_Assignment', label='reviewer-matching', head=submission.id)
        assert len(assignment_edges) == 3
        assert '~External_Reviewer_Amazon1' in [e.tail for e in assignment_edges]

        # Confirmation email to the reviewer
        messages = client.get_messages(to='external_reviewer1@amazon.com', subject='[NeurIPS 2021] Reviewer Invitation accepted for paper 5')
        assert messages and len(messages) == 1
        assert messages[0]['content']['text'] == '<p>Hi External Reviewer Amazon,<br>\nThank you for accepting the invitation to review the paper number: 5, title: Paper title 5.</p>\n<p>The NeurIPS 2021 program chairs will be contacting you with more information regarding next steps soon. In the meantime, please add <a href=\"mailto:noreply@openreview.net\">noreply@openreview.net</a> to your email contacts to ensure that you receive all communications.</p>\n<p>If you would like to change your decision, please click the Decline link in the previous invitation email.</p>\n<p>OpenReview Team</p>\n'

        # Confirmation email to the ac
        messages = client.get_messages(to='ac1@mit.edu', subject='[NeurIPS 2021] Reviewer External Reviewer Amazon accepted to review paper 5')
        assert messages and len(messages) == 1
        assert messages[0]['content']['text'] == '<p>Hi Area IBMChair,<br>\nThe Reviewer External Reviewer Amazon(<a href=\"mailto:external_reviewer1@amazon.com\">external_reviewer1@amazon.com</a>) that you invited to review paper 5 has accepted the invitation and is now assigned to the paper 5.</p>\n<p>OpenReview Team</p>\n'


        ## External reviewer declines the invitation, assignment rollback
        invitation_url = re.search('href="https://.*">', invitation_message).group(0)[6:-1].replace('https://openreview.net', 'http://localhost:3030').replace('&amp;', '&')[:-1]
        helpers.respond_invitation(selenium, request_page, invitation_url, accept=False)
        notes = selenium.find_element_by_class_name("note_editor")
        assert notes
        messages = notes.find_elements_by_tag_name("h3")
        assert messages
        assert 'You have declined the invitation from Conference on Neural Information Processing Systems.' == messages[0].text

        helpers.await_queue()

        process_logs = client.get_process_logs(invitation='NeurIPS.cc/2021/Conference/Reviewers/-/Proposed_Assignment_Recruitment')
        assert len(process_logs) == 2
        assert process_logs[0]['status'] == 'ok'
        assert process_logs[1]['status'] == 'ok'

        ## Externel reviewer is not assigned to the paper 5
        invite_edges=pc_client.get_edges(invitation='NeurIPS.cc/2021/Conference/Reviewers/-/Invite_Assignment', head=submission.id)
        assert len(invite_edges) == 1
        assert invite_edges[0].tail == '~External_Reviewer_Amazon1'
        assert invite_edges[0].label == 'Declined'

        assignment_edges=pc_client.get_edges(invitation='NeurIPS.cc/2021/Conference/Reviewers/-/Proposed_Assignment', label='reviewer-matching', head=submission.id)
        assert len(assignment_edges) == 2
        assert '~External_Reviewer_Amazon1' not in [e.tail for e in assignment_edges]

        messages = client.get_messages(to='external_reviewer1@amazon.com', subject='[NeurIPS 2021] Reviewer Invitation declined for paper 5')
        assert messages and len(messages) == 1
        assert messages[0]['content']['text'] == '<p>Hi External Reviewer Amazon,<br>\nYou have declined the invitation to review the paper number: 5, title: Paper title 5.</p>\n<p>If you would like to change your decision, please click the Accept link in the previous invitation email.</p>\n<p>OpenReview Team</p>\n'

        response_note=client.get_notes(invitation='NeurIPS.cc/2021/Conference/Reviewers/-/Proposed_Assignment_Recruitment', content={ 'submission_id': submission.id, 'user': '~External_Reviewer_Amazon1', 'response': 'No'})[0]
        messages = client.get_messages(to='ac1@mit.edu', subject='[NeurIPS 2021] Reviewer External Reviewer Amazon declined to review paper 5')
        assert messages and len(messages) == 1
        assert messages[0]['content']['text'] == f'<p>Hi Area IBMChair,<br>\nThe Reviewer External Reviewer Amazon(<a href=\"mailto:external_reviewer1@amazon.com\">external_reviewer1@amazon.com</a>) that you invited to review paper 5 has declined the invitation.</p>\n<p>To read their response, please click here: <a href=\"https://openreview.net/forum?id={response_note.id}\">https://openreview.net/forum?id={response_note.id}</a></p>\n<p>OpenReview Team</p>\n'

        assert client.get_groups('NeurIPS.cc/2021/Conference/Paper5/External_Reviewers/Invited', member='~External_Reviewer_Amazon1')
        assert client.get_groups('NeurIPS.cc/2021/Conference/External_Reviewers/Invited', member='~External_Reviewer_Amazon1')

        assert not client.get_groups('NeurIPS.cc/2021/Conference/Paper5/External_Reviewers', member='~External_Reviewer_Amazon1')
        assert client.get_groups('NeurIPS.cc/2021/Conference/External_Reviewers', member='~External_Reviewer_Amazon1')
        assert not client.get_groups('NeurIPS.cc/2021/Conference/Reviewers', member='~External_Reviewer_Amazon1')


        ## External reviewer accepts the invitation again
        invitation_url = re.search('href="https://.*">', invitation_message).group(0)[6:-1].replace('https://openreview.net', 'http://localhost:3030').replace('&amp;', '&')[:-1]
        helpers.respond_invitation(selenium, request_page, invitation_url, accept=True)
        notes = selenium.find_element_by_class_name("note_editor")
        assert notes
        messages = notes.find_elements_by_tag_name("h3")
        assert messages
        assert 'Thank you for accepting this invitation from Conference on Neural Information Processing Systems.' == messages[0].text

        helpers.await_queue()

        process_logs = client.get_process_logs(invitation='NeurIPS.cc/2021/Conference/Reviewers/-/Proposed_Assignment_Recruitment')
        assert len(process_logs) == 3
        assert process_logs[0]['status'] == 'ok'
        assert process_logs[1]['status'] == 'ok'
        assert process_logs[2]['status'] == 'ok'

        ## Externel reviewer is assigned to the paper 5
        invite_edges=pc_client.get_edges(invitation='NeurIPS.cc/2021/Conference/Reviewers/-/Invite_Assignment', head=submission.id)
        assert len(invite_edges) == 1
        assert invite_edges[0].tail == '~External_Reviewer_Amazon1'
        assert invite_edges[0].label == 'Accepted'

        assignment_edges=pc_client.get_edges(invitation='NeurIPS.cc/2021/Conference/Reviewers/-/Proposed_Assignment', label='reviewer-matching', head=submission.id)
        assert len(assignment_edges) == 3
        assert '~External_Reviewer_Amazon1' in [e.tail for e in assignment_edges]

        messages = client.get_messages(to='external_reviewer1@amazon.com', subject='[NeurIPS 2021] Reviewer Invitation accepted for paper 5')
        assert messages and len(messages) == 2

        assert client.get_groups('NeurIPS.cc/2021/Conference/Paper5/External_Reviewers/Invited', member='~External_Reviewer_Amazon1')
        assert client.get_groups('NeurIPS.cc/2021/Conference/External_Reviewers/Invited', member='~External_Reviewer_Amazon1')

        assert client.get_groups('NeurIPS.cc/2021/Conference/Paper5/External_Reviewers', member='~External_Reviewer_Amazon1')
        assert client.get_groups('NeurIPS.cc/2021/Conference/External_Reviewers', member='~External_Reviewer_Amazon1')
        assert not client.get_groups('NeurIPS.cc/2021/Conference/Reviewers', member='~External_Reviewer_Amazon1')

        ## Invite external reviewer 2
        with pytest.raises(openreview.OpenReviewException, match=r'Conflict detected for External Reviewer MIT'):
            posted_edge=ac_client.post_edge(openreview.Edge(
                invitation='NeurIPS.cc/2021/Conference/Reviewers/-/Invite_Assignment',
                readers = [conference.id, 'NeurIPS.cc/2021/Conference/Paper5/Senior_Area_Chairs', 'NeurIPS.cc/2021/Conference/Paper5/Area_Chairs', 'external_reviewer2@mit.edu'],
                nonreaders = ['NeurIPS.cc/2021/Conference/Paper5/Authors'],
                writers = [conference.id],
                signatures = [signatory_group.id],
                head = submission.id,
                tail = 'external_reviewer2@mit.edu',
                label = 'Invitation Sent'
            ))

        ## Invite external reviewer 3
        posted_edge=ac_client.post_edge(openreview.Edge(
            invitation='NeurIPS.cc/2021/Conference/Reviewers/-/Invite_Assignment',
            readers = [conference.id, 'NeurIPS.cc/2021/Conference/Paper5/Senior_Area_Chairs', 'NeurIPS.cc/2021/Conference/Paper5/Area_Chairs', 'external_reviewer3@adobe.com'],
            nonreaders = ['NeurIPS.cc/2021/Conference/Paper5/Authors'],
            writers = [conference.id],
            signatures = [signatory_group.id],
            head = submission.id,
            tail = 'external_reviewer3@adobe.com',
            label = 'Invitation Sent'
        ))

        helpers.await_queue()

        process_logs = client.get_process_logs(id=posted_edge.id)
        assert len(process_logs) == 1
        assert process_logs[0]['status'] == 'ok'

        ## External reviewer is invited
        invite_edges=pc_client.get_edges(invitation='NeurIPS.cc/2021/Conference/Reviewers/-/Invite_Assignment', head=submission.id, tail='~External_Reviewer_Adobe1')
        assert len(invite_edges) == 1
        assert invite_edges[0].tail == '~External_Reviewer_Adobe1'
        assert invite_edges[0].label == 'Invitation Sent'

        assert client.get_groups('NeurIPS.cc/2021/Conference/Paper5/External_Reviewers/Invited', member='~External_Reviewer_Adobe1')
        assert client.get_groups('NeurIPS.cc/2021/Conference/External_Reviewers/Invited', member='~External_Reviewer_Adobe1')

        assert not client.get_groups('NeurIPS.cc/2021/Conference/Paper5/External_Reviewers', member='~External_Reviewer_Adobe1')
        assert not client.get_groups('NeurIPS.cc/2021/Conference/External_Reviewers', member='~External_Reviewer_Adobe1')
        assert not client.get_groups('NeurIPS.cc/2021/Conference/Reviewers', member='~External_Reviewer_Adobe1')

        ## External reviewer declines the invitation
        messages = client.get_messages(to='external_reviewer3@adobe.com', subject='[NeurIPS 2021] Invitation to review paper titled Paper title 5')
        assert messages and len(messages) == 1
        invitation_url = re.search('href="https://.*">', messages[0]['content']['text']).group(0)[6:-1].replace('https://openreview.net', 'http://localhost:3030').replace('&amp;', '&')[:-1]
        helpers.respond_invitation(selenium, request_page, invitation_url, accept=False)
        notes = selenium.find_element_by_class_name("note_editor")
        assert notes
        messages = notes.find_elements_by_tag_name("h3")
        assert messages
        assert 'You have declined the invitation from Conference on Neural Information Processing Systems.' == messages[0].text

        helpers.await_queue()

        process_logs = client.get_process_logs(invitation='NeurIPS.cc/2021/Conference/Reviewers/-/Proposed_Assignment_Recruitment')
        assert len(process_logs) == 4
        assert process_logs[0]['status'] == 'ok'

        invite_edges=pc_client.get_edges(invitation='NeurIPS.cc/2021/Conference/Reviewers/-/Invite_Assignment', head=submission.id, tail='~External_Reviewer_Adobe1')
        assert len(invite_edges) == 1
        assert invite_edges[0].label == 'Declined'

        assignment_edges=pc_client.get_edges(invitation='NeurIPS.cc/2021/Conference/Reviewers/-/Proposed_Assignment', label='reviewer-matching', head=submission.id)
        assert len(assignment_edges) == 3

        messages = client.get_messages(to='external_reviewer3@adobe.com', subject='[NeurIPS 2021] Reviewer Invitation declined for paper 5')
        assert messages and len(messages) == 1
        assert messages[0]['content']['text'] == '<p>Hi External Reviewer Adobe,<br>\nYou have declined the invitation to review the paper number: 5, title: Paper title 5.</p>\n<p>If you would like to change your decision, please click the Accept link in the previous invitation email.</p>\n<p>OpenReview Team</p>\n'

        assert client.get_groups('NeurIPS.cc/2021/Conference/Paper5/External_Reviewers/Invited', member='~External_Reviewer_Adobe1')
        assert client.get_groups('NeurIPS.cc/2021/Conference/External_Reviewers/Invited', member='~External_Reviewer_Adobe1')

        assert not client.get_groups('NeurIPS.cc/2021/Conference/Paper5/External_Reviewers', member='~External_Reviewer_Adobe1')
        assert not client.get_groups('NeurIPS.cc/2021/Conference/External_Reviewers', member='~External_Reviewer_Adobe1')
        assert not client.get_groups('NeurIPS.cc/2021/Conference/Reviewers', member='~External_Reviewer_Adobe1')

        ## Invite external reviewer 4 with no profile
        posted_edge=ac_client.post_edge(openreview.Edge(
            invitation='NeurIPS.cc/2021/Conference/Reviewers/-/Invite_Assignment',
            readers = [conference.id, 'NeurIPS.cc/2021/Conference/Paper5/Senior_Area_Chairs', 'NeurIPS.cc/2021/Conference/Paper5/Area_Chairs', 'external_reviewer4@gmail.com'],
            nonreaders = ['NeurIPS.cc/2021/Conference/Paper5/Authors'],
            writers = [conference.id],
            signatures = [signatory_group.id],
            head = submission.id,
            tail = 'external_reviewer4@gmail.com',
            label = 'Invitation Sent'
        ))

        helpers.await_queue()

        process_logs = client.get_process_logs(id=posted_edge.id)
        assert len(process_logs) == 1
        assert process_logs[0]['status'] == 'ok'

        ## External reviewer is invited
        invite_edges=pc_client.get_edges(invitation='NeurIPS.cc/2021/Conference/Reviewers/-/Invite_Assignment', head=submission.id, tail='external_reviewer4@gmail.com')
        assert len(invite_edges) == 1
        assert invite_edges[0].tail == 'external_reviewer4@gmail.com'
        assert invite_edges[0].label == 'Invitation Sent'

        assert client.get_groups('NeurIPS.cc/2021/Conference/Paper5/External_Reviewers/Invited', member='external_reviewer4@gmail.com')
        assert client.get_groups('NeurIPS.cc/2021/Conference/External_Reviewers/Invited', member='external_reviewer4@gmail.com')

        assert not client.get_groups('NeurIPS.cc/2021/Conference/Paper5/External_Reviewers', member='external_reviewer4@gmail.com')
        assert not client.get_groups('NeurIPS.cc/2021/Conference/External_Reviewers', member='external_reviewer4@gmail.com')
        assert not client.get_groups('NeurIPS.cc/2021/Conference/Reviewers', member='external_reviewer4@gmail.com')

        ## External reviewer accepts the invitation
        messages = client.get_messages(to='external_reviewer4@gmail.com', subject='[NeurIPS 2021] Invitation to review paper titled Paper title 5')
        assert messages and len(messages) == 1
        invitation_url = re.search('href="https://.*">', messages[0]['content']['text']).group(0)[6:-1].replace('https://openreview.net', 'http://localhost:3030').replace('&amp;', '&')[:-1]
        helpers.respond_invitation(selenium, request_page, invitation_url, accept=True)
        notes = selenium.find_element_by_class_name("note_editor")
        assert notes
        messages = notes.find_elements_by_tag_name("h3")
        assert messages
        assert 'Thank you for accepting this invitation from Conference on Neural Information Processing Systems.' == messages[0].text

        helpers.await_queue()

        ## Externel reviewer is set pending profile creation
        invite_edges=pc_client.get_edges(invitation='NeurIPS.cc/2021/Conference/Reviewers/-/Invite_Assignment', head=submission.id, tail='external_reviewer4@gmail.com')
        assert len(invite_edges) == 1
        assert invite_edges[0].label == 'Pending Sign Up'

        assignment_edges=pc_client.get_edges(invitation='NeurIPS.cc/2021/Conference/Reviewers/-/Proposed_Assignment', label='reviewer-matching', head=submission.id)
        assert len(assignment_edges) == 3

        messages = client.get_messages(to='external_reviewer4@gmail.com', subject='[NeurIPS 2021] Reviewer Invitation accepted for paper 5, assignment pending')
        assert messages and len(messages) == 1
        assert messages[0]['content']['text'] == '<p>Hi <a href=\"mailto:external_reviewer4@gmail.com\">external_reviewer4@gmail.com</a>,<br>\nThank you for accepting the invitation to review the paper number: 5, title: Paper title 5.</p>\n<p>Please signup in OpenReview using the email address <a href=\"mailto:external_reviewer4@gmail.com\">external_reviewer4@gmail.com</a> and complete your profile.<br>\nConfirmation of the assignment is pending until your profile is active and no conflicts of interest are detected.</p>\n<p>If you would like to change your decision, please click the Decline link in the previous invitation email.</p>\n<p>OpenReview Team</p>\n'

        messages = client.get_messages(to='ac1@mit.edu', subject='[NeurIPS 2021] Reviewer external_reviewer4@gmail.com accepted to review paper 5, assignment pending')
        assert messages and len(messages) == 1
        assert messages[0]['content']['text'] == '<p>Hi Area IBMChair,<br>\nThe Reviewer <a href=\"mailto:external_reviewer4@gmail.com\">external_reviewer4@gmail.com</a> that you invited to review paper 5 has accepted the invitation.</p>\n<p>Confirmation of the assignment is pending until the invited reviewer creates a profile in OpenReview and no conflicts of interest are detected.</p>\n<p>OpenReview Team</p>\n'

        assert client.get_groups('NeurIPS.cc/2021/Conference/Paper5/External_Reviewers/Invited', member='external_reviewer4@gmail.com')
        assert client.get_groups('NeurIPS.cc/2021/Conference/External_Reviewers/Invited', member='external_reviewer4@gmail.com')

        assert not client.get_groups('NeurIPS.cc/2021/Conference/Paper5/External_Reviewers', member='external_reviewer4@gmail.com')
        assert not client.get_groups('NeurIPS.cc/2021/Conference/External_Reviewers', member='external_reviewer4@gmail.com')
        assert not client.get_groups('NeurIPS.cc/2021/Conference/Reviewers', member='external_reviewer4@gmail.com')

        ## External reviewer creates a profile and accepts the invitation again
        external_reviewer=helpers.create_user('external_reviewer4@gmail.com', 'Reviewer', 'External')

        helpers.respond_invitation(selenium, request_page, invitation_url, accept=True)
        notes = selenium.find_element_by_class_name("note_editor")
        assert notes
        messages = notes.find_elements_by_tag_name("h3")
        assert messages
        assert 'Thank you for accepting this invitation from Conference on Neural Information Processing Systems.' == messages[0].text

        helpers.await_queue()

        invite_edges=pc_client.get_edges(invitation='NeurIPS.cc/2021/Conference/Reviewers/-/Invite_Assignment', head=submission.id, tail='external_reviewer4@gmail.com')
        assert len(invite_edges) == 0
        invite_edges=pc_client.get_edges(invitation='NeurIPS.cc/2021/Conference/Reviewers/-/Invite_Assignment', head=submission.id, tail='~Reviewer_External1')
        assert len(invite_edges) == 1
        assert invite_edges[0].label == 'Accepted'

        helpers.respond_invitation(selenium, request_page, invitation_url, accept=False)

        helpers.await_queue()

        invite_edges=pc_client.get_edges(invitation='NeurIPS.cc/2021/Conference/Reviewers/-/Invite_Assignment', head=submission.id, tail='external_reviewer4@gmail.com')
        assert len(invite_edges) == 0
        invite_edges=pc_client.get_edges(invitation='NeurIPS.cc/2021/Conference/Reviewers/-/Invite_Assignment', head=submission.id, tail='~Reviewer_External1')
        assert len(invite_edges) == 1
        assert invite_edges[0].label == 'Declined'

        ## Invite external reviewer 5 with no profile
        posted_edge=ac_client.post_edge(openreview.Edge(
            invitation='NeurIPS.cc/2021/Conference/Reviewers/-/Invite_Assignment',
            readers = [conference.id, 'NeurIPS.cc/2021/Conference/Paper5/Senior_Area_Chairs', 'NeurIPS.cc/2021/Conference/Paper5/Area_Chairs', 'external_reviewer5@gmail.com'],
            nonreaders = ['NeurIPS.cc/2021/Conference/Paper5/Authors'],
            writers = [conference.id],
            signatures = [signatory_group.id],
            head = submission.id,
            tail = 'external_reviewer5@gmail.com',
            label = 'Invitation Sent'
        ))

        helpers.await_queue()

        process_logs = client.get_process_logs(id=posted_edge.id)
        assert len(process_logs) == 1
        assert process_logs[0]['status'] == 'ok'

        ## External reviewer is invited
        invite_edges=pc_client.get_edges(invitation='NeurIPS.cc/2021/Conference/Reviewers/-/Invite_Assignment', head=submission.id, tail='external_reviewer5@gmail.com')
        assert len(invite_edges) == 1
        assert invite_edges[0].tail == 'external_reviewer5@gmail.com'
        assert invite_edges[0].label == 'Invitation Sent'

        ## External reviewer declines the invitation
        messages = client.get_messages(to='external_reviewer5@gmail.com', subject='[NeurIPS 2021] Invitation to review paper titled Paper title 5')
        assert messages and len(messages) == 1
        invitation_url = re.search('href="https://.*">', messages[0]['content']['text']).group(0)[6:-1].replace('https://openreview.net', 'http://localhost:3030').replace('&amp;', '&')[:-1]
        helpers.respond_invitation(selenium, request_page, invitation_url, accept=False)
        notes = selenium.find_element_by_class_name("note_editor")
        assert notes
        messages = notes.find_elements_by_tag_name("h3")
        assert messages
        assert 'You have declined the invitation from Conference on Neural Information Processing Systems.' == messages[0].text

        helpers.await_queue()

        ## Externel reviewer is set pending profile creation
        invite_edges=pc_client.get_edges(invitation='NeurIPS.cc/2021/Conference/Reviewers/-/Invite_Assignment', head=submission.id, tail='external_reviewer5@gmail.com')
        assert len(invite_edges) == 1
        assert invite_edges[0].label == 'Declined'

        assignment_edges=pc_client.get_edges(invitation='NeurIPS.cc/2021/Conference/Reviewers/-/Proposed_Assignment', label='reviewer-matching', head=submission.id)
        assert len(assignment_edges) == 3

        messages = client.get_messages(to='external_reviewer5@gmail.com', subject='[NeurIPS 2021] Reviewer Invitation declined for paper 5')
        assert messages and len(messages) == 1
        assert messages[0]['content']['text'] == '<p>Hi <a href=\"mailto:external_reviewer5@gmail.com\">external_reviewer5@gmail.com</a>,<br>\nYou have declined the invitation to review the paper number: 5, title: Paper title 5.</p>\n<p>If you would like to change your decision, please click the Accept link in the previous invitation email.</p>\n<p>OpenReview Team</p>\n'
        ## Invite external reviewer with wrong tilde id
        with pytest.raises(openreview.OpenReviewException) as openReviewError:
            posted_edge=ac_client.post_edge(openreview.Edge(
                invitation='NeurIPS.cc/2021/Conference/Reviewers/-/Invite_Assignment',
                readers = [conference.id, 'NeurIPS.cc/2021/Conference/Paper5/Senior_Area_Chairs', 'NeurIPS.cc/2021/Conference/Paper5/Area_Chairs', '~External_Melisa1'],
                nonreaders = ['NeurIPS.cc/2021/Conference/Paper5/Authors'],
                writers = [conference.id],
                signatures = [signatory_group.id],
                head = submission.id,
                tail = '~External_Melisa1',
                label = 'Invitation Sent'
            ))
        assert openReviewError.value.args[0].get('name') == 'Not Found'
        assert openReviewError.value.args[0].get('message') == '~External_Melisa1 was not found'

        ## Invite an official reviewer and get an error
        with pytest.raises(openreview.OpenReviewException) as openReviewError:
            posted_edge=ac_client.post_edge(openreview.Edge(
                invitation='NeurIPS.cc/2021/Conference/Reviewers/-/Invite_Assignment',
                readers = [conference.id, 'NeurIPS.cc/2021/Conference/Paper5/Senior_Area_Chairs', 'NeurIPS.cc/2021/Conference/Paper5/Area_Chairs', 'reviewer4@fb.com'],
                nonreaders = ['NeurIPS.cc/2021/Conference/Paper5/Authors'],
                writers = [conference.id],
                signatures = [signatory_group.id],
                head = submission.id,
                tail = 'reviewer4@fb.com',
                label = 'Invitation Sent'
            ))
        assert openReviewError.value.args[0].get('name') == 'Error'
        assert openReviewError.value.args[0].get('message') == 'Reviewer Reviewer Facebook is an official reviewer, please use the "Assign" button to make the assignment.'

        ## Invite an official conflicted reviewer and get a conflict error
        with pytest.raises(openreview.OpenReviewException, match=r'Conflict detected for Reviewer MIT'):
            posted_edge=ac_client.post_edge(openreview.Edge(
                invitation='NeurIPS.cc/2021/Conference/Reviewers/-/Invite_Assignment',
                readers = [conference.id, 'NeurIPS.cc/2021/Conference/Paper5/Senior_Area_Chairs', 'NeurIPS.cc/2021/Conference/Paper5/Area_Chairs', 'reviewer2@mit.edu'],
                nonreaders = ['NeurIPS.cc/2021/Conference/Paper5/Authors'],
                writers = [conference.id],
                signatures = [signatory_group.id],
                head = submission.id,
                tail = 'reviewer2@mit.edu',
                label = 'Invitation Sent'
            ))

        ## Propose a reviewer that reached the quota
        with pytest.raises(openreview.OpenReviewException, match=r'Max Papers allowed reached for Reviewer IBM'):
            posted_edge=ac_client.post_edge(openreview.Edge(
                invitation='NeurIPS.cc/2021/Conference/Reviewers/-/Proposed_Assignment',
                readers = [conference.id, 'NeurIPS.cc/2021/Conference/Paper5/Senior_Area_Chairs', 'NeurIPS.cc/2021/Conference/Paper5/Area_Chairs', '~Reviewer_IBM1'],
                nonreaders = ['NeurIPS.cc/2021/Conference/Paper5/Authors'],
                writers = [conference.id, 'NeurIPS.cc/2021/Conference/Paper5/Senior_Area_Chairs', 'NeurIPS.cc/2021/Conference/Paper5/Area_Chairs'],
                signatures = [signatory_group.id],
                head = submission.id,
                tail = '~Reviewer_IBM1',
                label = 'reviewer-matching'
            ))


    def test_deployment_stage(self, conference, client, helpers):

        pc_client=openreview.Client(username='pc@neurips.cc', password='1234')
        submissions=conference.get_submissions(sort='tmdate')

        conference.set_assignments(assignment_title='reviewer-matching', committee_id='NeurIPS.cc/2021/Conference/Reviewers', overwrite=True, enable_reviewer_reassignment=True)

        helpers.await_queue()

        paper_reviewers=pc_client.get_group('NeurIPS.cc/2021/Conference/Paper5/Reviewers').members
        assert len(paper_reviewers) == 3
        assert '~Reviewer_UMass1' in paper_reviewers
        assert '~Reviewer_Google1' in paper_reviewers
        assert '~External_Reviewer_Amazon1' in paper_reviewers

        paper_reviewers=pc_client.get_group('NeurIPS.cc/2021/Conference/Paper4/Reviewers').members
        assert len(paper_reviewers) == 2
        assert '~Reviewer_UMass1' in paper_reviewers
        assert '~Reviewer_Facebook1' in paper_reviewers

        paper_reviewers=pc_client.get_group('NeurIPS.cc/2021/Conference/Paper3/Reviewers').members
        assert len(paper_reviewers) == 2
        assert '~Reviewer_UMass1' in paper_reviewers
        assert '~Reviewer_Google1' in paper_reviewers

        paper_reviewers=pc_client.get_group('NeurIPS.cc/2021/Conference/Paper2/Reviewers').members
        assert len(paper_reviewers) == 2
        assert '~Reviewer_Facebook1' in paper_reviewers
        assert '~Reviewer_IBM1' in paper_reviewers

        paper_reviewers=pc_client.get_group('NeurIPS.cc/2021/Conference/Paper1/Reviewers').members
        assert len(paper_reviewers) == 2
        assert '~Reviewer_UMass1' in paper_reviewers
        assert '~Reviewer_MIT1' in paper_reviewers

        assignments=pc_client.get_edges(invitation='NeurIPS.cc/2021/Conference/Reviewers/-/Assignment')
        assert len(assignments) == 11

        assignments=pc_client.get_edges(invitation='NeurIPS.cc/2021/Conference/Reviewers/-/Assignment', tail='~Reviewer_UMass1')
        assert len(assignments) == 4

        assignments=pc_client.get_edges(invitation='NeurIPS.cc/2021/Conference/Reviewers/-/Assignment', tail='~Reviewer_UMass1', head=submissions[0].id)
        assert len(assignments) == 1

        assert assignments[0].readers == ["NeurIPS.cc/2021/Conference",
            "NeurIPS.cc/2021/Conference/Paper5/Senior_Area_Chairs",
            "NeurIPS.cc/2021/Conference/Paper5/Area_Chairs",
            "~Reviewer_UMass1"]

        assert assignments[0].writers == ["NeurIPS.cc/2021/Conference",
            "NeurIPS.cc/2021/Conference/Paper5/Senior_Area_Chairs",
            "NeurIPS.cc/2021/Conference/Paper5/Area_Chairs"]

        assert client.get_groups('NeurIPS.cc/2021/Conference/Paper5/External_Reviewers/Invited', member='~External_Reviewer_Amazon1')
        assert client.get_groups('NeurIPS.cc/2021/Conference/External_Reviewers/Invited', member='~External_Reviewer_Amazon1')
        assert not client.get_groups('NeurIPS.cc/2021/Conference/Reviewers', member='~External_Reviewer_Amazon1')


    def test_review_stage(self, conference, helpers, test_client, client):

        ## make submissions visible to assigned commmittee
        invitation = client.get_invitation('NeurIPS.cc/2021/Conference/-/Submission')
        invitation.reply['readers'] = {
            'values-regex': '.*'
        }
        client.post_invitation(invitation)

        invitation2 = client.get_invitation('NeurIPS.cc/2021/Conference/-/Blind_Submission')
        invitation2.reply_forum_views = [
            {
                "id": "authors",
                "label": "Author Discussion",
                "filter": "readers:NeurIPS.cc/2021/Conference/Paper${note.number}/Authors"
            },
            {
                "id": "committee",
                "label": "Committee Discussion",
                "filter": "-readers:NeurIPS.cc/2021/Conference/Paper${note.number}/Authors"
            },
            {
                "id": "all",
                "label": "All",
                "filter": ""
            }
        ]
        client.post_invitation(invitation2)

        original_notes=client.get_notes(invitation='NeurIPS.cc/2021/Conference/-/Submission')
        for note in original_notes:
            note.readers = note.readers + [f'NeurIPS.cc/2021/Conference/Paper{note.number}/Senior_Area_Chairs']
            client.post_note(note)

        blind_notes=client.get_notes(invitation='NeurIPS.cc/2021/Conference/-/Blind_Submission')
        for note in blind_notes:
            note.content = {
                'authors': ['Anonymous'],
                'authorids': [f'NeurIPS.cc/2021/Conference/Paper{note.number}/Authors']
            }
            note.readers = [
                'NeurIPS.cc/2021/Conference',
                f'NeurIPS.cc/2021/Conference/Paper{note.number}/Senior_Area_Chairs',
                f'NeurIPS.cc/2021/Conference/Paper{note.number}/Area_Chairs',
                f'NeurIPS.cc/2021/Conference/Paper{note.number}/Reviewers',
                f'NeurIPS.cc/2021/Conference/Paper{note.number}/Authors'
            ]
            client.post_note(note)

        now = datetime.datetime.utcnow()
        due_date = now + datetime.timedelta(days=3)

        pc_client=openreview.Client(username='pc@neurips.cc', password='1234')
        request_form=pc_client.get_notes(invitation='openreview.net/Support/-/Request_Form')[0]
        stage_note=client.post_note(openreview.Note(
            content={
                'review_deadline': due_date.strftime('%Y/%m/%d'),
                'make_reviews_public': 'No, reviews should NOT be revealed publicly when they are posted',
                'release_reviews_to_authors': 'No, reviews should NOT be revealed when they are posted to the paper\'s authors',
                'release_reviews_to_reviewers': 'Review should not be revealed to any reviewer, except to the author of the review',
                'email_program_chairs_about_reviews': 'No, do not email program chairs about received reviews',
                'remove_review_form_options': 'title',
                'additional_review_form_options': {
                    "summary_and_contributions": {
                        "order": 1,
                        "value-regex": "[\\S\\s]{1,200000}",
                        "description": "Briefly summarize the paper and its contributions.",
                        "required": True
                    },
                    "review": {
                        "order": 2,
                        "value-regex": "[\\S\\s]{1,200000}",
                        "description": "Please provide a thorough review of the submission, including its originality, quality, clarity, and significance. See https://neurips.cc/Conferences/2021/Review-Form for guidance on questions to address in your review, and https://openreview.net/faq for how to incorporate Markdown and LaTeX into your review.",
                        "required": True,
                        "markdown": True
                    },
                    "societal_impact": {
                        "description": "Have the authors adequately addressed the limitations and potential negative societal impact of their work? (If not, please include constructive suggestions for improvement)",
                        "order": 3,
                        "value-regex": "[\\S\\s]{1,200000}",
                        "required": True
                    },
                    "needs_ethical_review": {
                        "description": "Would the paper benefit from further ethical review?",
                        "order": 4,
                        "value-radio": [
                            "Yes",
                            "No"
                        ],
                        "required": True
                    },
                    "ethical_issues": {
                        "description": "Please elaborate on the ethical issues raised by this paper and the extent to which the issues have been acknowledged or addressed.",
                        "order": 5,
                        "value-regex": "[\\S\\s]{1,200000}",
                        "required": False
                    },
                    "ethical_expertise": {
                        "order": 6,
                        "values-checkbox": [
                            "Discrimination / Bias / Fairness Concerns",
                            "Inadequate Data and Algorithm Evaluation",
                            "Inappropriate Potential Applications & Impact  (e.g., human rights concerns)",
                            "Privacy and Security (e.g., consent)",
                            "Legal Compliance (e.g., GDPR, copyright, terms of use)",
                            "Research Integrity Issues (e.g., plagiarism)",
                            "Responsible Research Practice (e.g., IRB, documentation, research ethics)",
                            "I don’t know"
                        ],
                        "description": "What kind of expertise do you think is required to review this paper for the ethical concerns raised?. Please click all that apply.",
                        "required": False
                    },
                    "previously_reviewed": {
                        "order": 7,
                        "value-radio": [
                            "Yes",
                            "No"
                        ],
                        "required": True,
                        "description": "Have you previously reviewed or area chaired (a version of) this work for another archival venue?",
                    },
                    "reviewing_time": {
                        "order": 8,
                        "value-regex": ".{1,500}",
                        "required": True,
                        "description": "How much time did you spend reviewing this paper (in_hours)?"
                    },
                    "rating": {
                        "order": 9,
                        "value-radio": [
                            "10: Top 5% of accepted NeurIPS papers, seminal paper",
                            "9: Top 15% of accepted NeurIPS papers, strong accept",
                            "8: Top 50% of accepted NeurIPS papers, clear accept",
                            "7: Good paper, accept",
                            "6: Marginally above the acceptance threshold",
                            "5: Marginally below the acceptance threshold",
                            "4: An okay paper, but not good enough; rejection",
                            "3: Clear rejection",
                            "2: Strong rejection",
                            "1: Trivial or wrong"
                        ],
                        "description": "Please provide an \"overall score\" for this submission.",
                        "required": True
                    },
                    "confidence": {
                        "order": 10,
                        "value-radio": [
                            "5: You are absolutely certain about your assessment. You are very familiar with the related work and checked the math/other details carefully.",
                            "4: You are confident in your assessment, but not absolutely certain. It is unlikely, but not impossible, that you did not understand some parts of the submission or that you are unfamiliar with some pieces of related work.",
                            "3: You are fairly confident in your assessment. It is possible that you did not understand some parts of the submission or that you are unfamiliar with some pieces of related work. Math/other details were not carefully checked.",
                            "2: You are willing to defend your assessment, but it is quite likely that you did not understand central parts of the submission or that you are unfamiliar with some pieces of related work. Math/other details were not carefully checked.",
                            "1: Your assessment is an educated guess. The submission is not in your area or the submission was difficult to understand. Math/other details were not carefully checked."
                        ],
                        "description": "Please provide a \"confidence score\" for your assessment of this submission.",
                        "required": True
                    },
                    "code_of_conduct": {
                        "order": 11,
                        "value-checkbox": "While performing my duties as a reviewer (including writing reviews and participating in discussions), I have and will continue to abide by the NeurIPS code of conduct (https://neurips.cc/public/CodeOfConduct).",
                        "required": True
                    }
                }
            },
            forum=request_form.forum,
            invitation='openreview.net/Support/-/Request{}/Review_Stage'.format(request_form.number),
            readers=['NeurIPS.cc/2021/Conference/Program_Chairs', 'openreview.net/Support'],
            referent=request_form.forum,
            replyto=request_form.forum,
            signatures=['~Program_NeurIPSChair1'],
            writers=[]
        ))

        helpers.await_queue()

        process_logs = client.get_process_logs(id=stage_note.id)
        assert len(process_logs) == 1
        assert process_logs[0]['status'] == 'ok'

        ac_group=client.get_groups(regex='NeurIPS.cc/2021/Conference/Paper5/Area_Chair_')[0]
        assert ac_group.readers == ['NeurIPS.cc/2021/Conference',
            'NeurIPS.cc/2021/Conference/Program_Chairs',
            'NeurIPS.cc/2021/Conference/Paper5/Senior_Area_Chairs',
            'NeurIPS.cc/2021/Conference/Paper5/Area_Chairs',
            'NeurIPS.cc/2021/Conference/Paper5/Reviewers',
            ac_group.id]

        reviewer_group=client.get_groups(regex='NeurIPS.cc/2021/Conference/Paper5/Reviewer_')[0]
        assert reviewer_group.readers == ['NeurIPS.cc/2021/Conference',
            'NeurIPS.cc/2021/Conference/Program_Chairs',
            'NeurIPS.cc/2021/Conference/Paper5/Senior_Area_Chairs',
            'NeurIPS.cc/2021/Conference/Paper5/Area_Chairs',
            'NeurIPS.cc/2021/Conference/Paper5/Reviewers',
            reviewer_group.id]

        anon_groups=client.get_groups('NeurIPS.cc/2021/Conference/Paper5/Area_Chair_.*')
        assert len(anon_groups) == 1

        anon_groups=client.get_groups('NeurIPS.cc/2021/Conference/Paper5/Reviewer_.*')
        assert len(anon_groups) == 3

        reviewer_client=openreview.Client(username='reviewer1@umass.edu', password='1234')

        signatory_groups=client.get_groups(regex='NeurIPS.cc/2021/Conference/Paper5/Reviewer_', signatory='reviewer1@umass.edu')
        assert len(signatory_groups) == 1

        submissions=conference.get_submissions(number=5)
        assert len(submissions) == 1

        review_note=reviewer_client.post_note(openreview.Note(
            invitation='NeurIPS.cc/2021/Conference/Paper5/-/Official_Review',
            forum=submissions[0].id,
            replyto=submissions[0].id,
            readers=['NeurIPS.cc/2021/Conference/Program_Chairs', 'NeurIPS.cc/2021/Conference/Paper5/Senior_Area_Chairs', 'NeurIPS.cc/2021/Conference/Paper5/Area_Chairs', signatory_groups[0].id],
            nonreaders=['NeurIPS.cc/2021/Conference/Paper5/Authors'],
            writers=[signatory_groups[0].id],
            signatures=[signatory_groups[0].id],
            content={
                'summary_and_contributions': 'TEst data',
                'review': 'Paper is very good!Paper is very good!Paper is very good!Paper is very good!Paper is very good!Paper is very good!Paper is very good!Paper is very good!',
                'societal_impact': 'TESSSTTTTTTESSSTTTTTTESSSTTTTTTESSSTTTTTTESSSTTTTTTESSSTTTTT',
                'needs_ethical_review': 'No',
                'previously_reviewed': 'No',
                'reviewing_time': '3',
                'rating': '10: Top 5% of accepted NeurIPS papers, seminal paper',
                'confidence': '5: You are absolutely certain about your assessment. You are very familiar with the related work and checked the math/other details carefully.',
                'code_of_conduct': 'While performing my duties as a reviewer (including writing reviews and participating in discussions), I have and will continue to abide by the NeurIPS code of conduct (https://neurips.cc/public/CodeOfConduct).'
            }
        ))

        helpers.await_queue()

        process_logs = client.get_process_logs(id=review_note.id)
        assert len(process_logs) == 1
        assert process_logs[0]['status'] == 'ok'

        messages = client.get_messages(to='reviewer1@umass.edu', subject='[NeurIPS 2021] Your review has been received on your assigned Paper number: 5, Paper title: \"Paper title 5\"')
        assert messages and len(messages) == 1

        messages = client.get_messages(to='ac1@mit.edu', subject='[NeurIPS 2021] Review posted to your assigned Paper number: 5, Paper title: \"Paper title 5\"')
        assert messages and len(messages) == 1

        ## TODO: should we send emails to Senior Area Chairs?

    def test_emergency_reviewer_stage(self, conference, helpers, client, request_page, selenium):

        now = datetime.datetime.utcnow()
        pc_client=openreview.Client(username='pc@neurips.cc', password='1234')

        start='NeurIPS.cc/2021/Conference/Area_Chairs/-/Assignment,tail:~Area_IBMChair1'
        traverse='NeurIPS.cc/2021/Conference/Reviewers/-/Assignment'
        edit='NeurIPS.cc/2021/Conference/Reviewers/-/Assignment;NeurIPS.cc/2021/Conference/Reviewers/-/Invite_Assignment'
        browse='NeurIPS.cc/2021/Conference/Reviewers/-/Aggregate_Score,label:reviewer-matching;NeurIPS.cc/2021/Conference/Reviewers/-/Affinity_Score;NeurIPS.cc/2021/Conference/Reviewers/-/Conflict'
        hide='NeurIPS.cc/2021/Conference/Reviewers/-/Conflict'
        url=f'http://localhost:3030/edges/browse?start={start}&traverse={traverse}&edit={edit}&browse={browse}&maxColumns=2'

        print(url)

        ac_client=openreview.Client(username='ac1@mit.edu', password='1234')
        submission=conference.get_submissions(sort='tmdate')[1]
        signatory_group=ac_client.get_groups(regex='NeurIPS.cc/2021/Conference/Paper4/Area_Chair_')[0]

        ## Invite external reviewer 1
        posted_edge=ac_client.post_edge(openreview.Edge(
            invitation='NeurIPS.cc/2021/Conference/Reviewers/-/Invite_Assignment',
            readers = [conference.id, 'NeurIPS.cc/2021/Conference/Paper4/Senior_Area_Chairs', 'NeurIPS.cc/2021/Conference/Paper4/Area_Chairs', 'external_reviewer2@mit.edu'],
            nonreaders = ['NeurIPS.cc/2021/Conference/Paper4/Authors'],
            writers = [conference.id],
            signatures = [signatory_group.id],
            head = submission.id,
            tail = 'external_reviewer2@mit.edu',
            label = 'Invitation Sent'
        ))

        helpers.await_queue()

        process_logs = client.get_process_logs(id=posted_edge.id)
        assert len(process_logs) == 1
        assert process_logs[0]['status'] == 'ok'

        ## External reviewer is invited
        invite_edges=pc_client.get_edges(invitation='NeurIPS.cc/2021/Conference/Reviewers/-/Invite_Assignment', head=submission.id)
        assert len(invite_edges) == 1
        assert invite_edges[0].tail == '~External_Reviewer_MIT1'
        assert invite_edges[0].label == 'Invitation Sent' ## figure out how to enable this in the deployment

        assert client.get_groups('NeurIPS.cc/2021/Conference/Emergency_Reviewers/Invited', member='~External_Reviewer_MIT1')

        assert not client.get_groups('NeurIPS.cc/2021/Conference/Emergency_Reviewers', member='~External_Reviewer_MIT1')
        assert not client.get_groups('NeurIPS.cc/2021/Conference/Reviewers', member='~External_Reviewer_MIT1')


        ## External reviewer accepts the invitation
        messages = client.get_messages(to='external_reviewer2@mit.edu', subject='[NeurIPS 2021] Invitation to review paper titled Paper title 4')
        assert messages and len(messages) == 1
        invitation_url = re.search('href="https://.*">', messages[0]['content']['text']).group(0)[6:-1].replace('https://openreview.net', 'http://localhost:3030').replace('&amp;', '&')[:-1]
        helpers.respond_invitation(selenium, request_page, invitation_url, accept=True)
        notes = selenium.find_element_by_class_name("note_editor")
        assert notes
        messages = notes.find_elements_by_tag_name("h3")
        assert messages
        assert 'Thank you for accepting this invitation from Conference on Neural Information Processing Systems.' == messages[0].text

        helpers.await_queue()

        process_logs = client.get_process_logs(invitation='NeurIPS.cc/2021/Conference/Reviewers/-/Assignment_Recruitment')
        assert len(process_logs) == 1
        assert process_logs[0]['status'] == 'ok'

        ## Externel reviewer is assigned to the paper 5
        invite_edges=pc_client.get_edges(invitation='NeurIPS.cc/2021/Conference/Reviewers/-/Invite_Assignment', head=submission.id)
        assert len(invite_edges) == 1
        assert invite_edges[0].tail == '~External_Reviewer_MIT1'
        assert invite_edges[0].label == 'Accepted'

        assignment_edges=pc_client.get_edges(invitation='NeurIPS.cc/2021/Conference/Reviewers/-/Assignment', head=submission.id)
        assert len(assignment_edges) == 3
        assert '~External_Reviewer_MIT1' in [e.tail for e in assignment_edges]

        assert '~External_Reviewer_MIT1' in pc_client.get_group('NeurIPS.cc/2021/Conference/Paper4/Reviewers').members

        assert len(pc_client.get_groups(regex='NeurIPS.cc/2021/Conference/Paper4/Reviewer_', signatory='~External_Reviewer_MIT1')) == 1

        messages = client.get_messages(to='external_reviewer2@mit.edu', subject='[NeurIPS 2021] Reviewer Invitation accepted for paper 4')
        assert messages and len(messages) == 1
        assert messages[0]['content']['text'] == '<p>Hi External Reviewer MIT,<br>\nThank you for accepting the invitation to review the paper number: 4, title: Paper title 4.</p>\n<p>Please go to the NeurIPS 2021 Reviewers Console and check your pending tasks: <a href=\"https://openreview.net/group?id=NeurIPS.cc/2021/Conference/Reviewers\">https://openreview.net/group?id=NeurIPS.cc/2021/Conference/Reviewers</a></p>\n<p>If you would like to change your decision, please click the Decline link in the previous invitation email.</p>\n<p>OpenReview Team</p>\n'

        messages = client.get_messages(to='external_reviewer2@mit.edu', subject='[NeurIPS 2021] You have been assigned as a Reviewer for paper number 4')
        assert messages and len(messages) == 1
        assert messages[0]['content']['text'] == f'<p>This is to inform you that you have been assigned as a Reviewer for paper number 4 for NeurIPS 2021.</p>\n<p>To review this new assignment, please login to OpenReview and go to <a href=\"https://openreview.net/forum?id={submission.id}\">https://openreview.net/forum?id={submission.id}</a>.</p>\n<p>To check all of your assigned papers, go to <a href=\"https://openreview.net/group?id=NeurIPS.cc/2021/Conference/Reviewers\">https://openreview.net/group?id=NeurIPS.cc/2021/Conference/Reviewers</a>.</p>\n<p>Thank you,</p>\n<p>NeurIPS 2021 Conference Program Chairs</p>\n'

        assert client.get_groups('NeurIPS.cc/2021/Conference/Emergency_Reviewers/Invited', member='~External_Reviewer_MIT1')

        assert client.get_groups('NeurIPS.cc/2021/Conference/Emergency_Reviewers', member='~External_Reviewer_MIT1')
        assert client.get_groups('NeurIPS.cc/2021/Conference/Reviewers', member='~External_Reviewer_MIT1')



        ## Invite the same reviewer again
        with pytest.raises(openreview.OpenReviewException) as openReviewError:
            posted_edge=ac_client.post_edge(openreview.Edge(
                invitation='NeurIPS.cc/2021/Conference/Reviewers/-/Invite_Assignment',
                readers = [conference.id, 'NeurIPS.cc/2021/Conference/Paper4/Senior_Area_Chairs', 'NeurIPS.cc/2021/Conference/Paper4/Area_Chairs', 'external_reviewer2@mit.edu'],
                nonreaders = ['NeurIPS.cc/2021/Conference/Paper4/Authors'],
                writers = [conference.id],
                signatures = [signatory_group.id],
                head = submission.id,
                tail = '~External_Reviewer_MIT1',
                label = 'Invitation Sent'
            ))
        assert openReviewError.value.args[0].get('name') == 'TooManyError'

        ## Invite the same reviewer again
        with pytest.raises(openreview.OpenReviewException, match=r'Already invited as ~External_Reviewer_MIT1'):
            posted_edge=ac_client.post_edge(openreview.Edge(
                invitation='NeurIPS.cc/2021/Conference/Reviewers/-/Invite_Assignment',
                readers = [conference.id, 'NeurIPS.cc/2021/Conference/Paper4/Senior_Area_Chairs', 'NeurIPS.cc/2021/Conference/Paper4/Area_Chairs', 'external_reviewer2@mit.edu'],
                nonreaders = ['NeurIPS.cc/2021/Conference/Paper4/Authors'],
                writers = [conference.id],
                signatures = [signatory_group.id],
                head = submission.id,
                tail = 'external_reviewer2@mit.edu',
                label = 'Invitation Sent'
            ))

        ## Invite reviewer already assigned
        with pytest.raises(openreview.OpenReviewException, match=r'Already assigned as ~Reviewer_UMass1'):
            posted_edge=ac_client.post_edge(openreview.Edge(
                invitation='NeurIPS.cc/2021/Conference/Reviewers/-/Invite_Assignment',
                readers = [conference.id, 'NeurIPS.cc/2021/Conference/Paper4/Senior_Area_Chairs', 'NeurIPS.cc/2021/Conference/Paper4/Area_Chairs', '~Reviewer_UMass1'],
                nonreaders = ['NeurIPS.cc/2021/Conference/Paper4/Authors'],
                writers = [conference.id],
                signatures = [signatory_group.id],
                head = submission.id,
                tail = '~Reviewer_UMass1',
                label = 'Invitation Sent'
            ))

        ## Official reviewer accepts the invitation
        posted_edge=ac_client.post_edge(openreview.Edge(
            invitation='NeurIPS.cc/2021/Conference/Reviewers/-/Invite_Assignment',
            readers = [conference.id, 'NeurIPS.cc/2021/Conference/Paper4/Senior_Area_Chairs', 'NeurIPS.cc/2021/Conference/Paper4/Area_Chairs', '~Reviewer_Amazon1'],
            nonreaders = ['NeurIPS.cc/2021/Conference/Paper4/Authors'],
            writers = [conference.id],
            signatures = [signatory_group.id],
            head = submission.id,
            tail = '~Reviewer_Amazon1',
            label = 'Invitation Sent'
        ))

        helpers.await_queue()

        messages = client.get_messages(to='reviewer6@amazon.com', subject='[NeurIPS 2021] Invitation to review paper titled Paper title 4')
        assert messages and len(messages) == 1
        invitation_url = re.search('href="https://.*">', messages[0]['content']['text']).group(0)[6:-1].replace('https://openreview.net', 'http://localhost:3030').replace('&amp;', '&')[:-1]
        helpers.respond_invitation(selenium, request_page, invitation_url, accept=True)
        notes = selenium.find_element_by_class_name("note_editor")
        assert notes
        messages = notes.find_elements_by_tag_name("h3")
        assert messages
        assert 'Thank you for accepting this invitation from Conference on Neural Information Processing Systems.' == messages[0].text

        helpers.await_queue()

        invite_edges=pc_client.get_edges(invitation='NeurIPS.cc/2021/Conference/Reviewers/-/Invite_Assignment', head=submission.id, tail='~Reviewer_Amazon1')
        assert len(invite_edges) == 1
        assert invite_edges[0].label == 'Accepted'

        assignment_edges=pc_client.get_edges(invitation='NeurIPS.cc/2021/Conference/Reviewers/-/Assignment', head=submission.id)
        assert len(assignment_edges) == 4
        assert '~Reviewer_Amazon1' in [e.tail for e in assignment_edges]

        assert '~Reviewer_Amazon1' in pc_client.get_group('NeurIPS.cc/2021/Conference/Paper4/Reviewers').members

        assert len(pc_client.get_groups(regex='NeurIPS.cc/2021/Conference/Paper4/Reviewer_', signatory='~Reviewer_Amazon1')) == 1

        messages = client.get_messages(to='reviewer6@amazon.com', subject='[NeurIPS 2021] Reviewer Invitation accepted for paper 4')
        assert messages and len(messages) == 1
        assert messages[0]['content']['text'] == '<p>Hi Reviewer Amazon,<br>\nThank you for accepting the invitation to review the paper number: 4, title: Paper title 4.</p>\n<p>Please go to the NeurIPS 2021 Reviewers Console and check your pending tasks: <a href=\"https://openreview.net/group?id=NeurIPS.cc/2021/Conference/Reviewers\">https://openreview.net/group?id=NeurIPS.cc/2021/Conference/Reviewers</a></p>\n<p>If you would like to change your decision, please click the Decline link in the previous invitation email.</p>\n<p>OpenReview Team</p>\n'

        assert client.get_groups('NeurIPS.cc/2021/Conference/Emergency_Reviewers/Invited', member='~Reviewer_Amazon1')
        assert client.get_groups('NeurIPS.cc/2021/Conference/Emergency_Reviewers', member='~Reviewer_Amazon1')
        assert client.get_groups('NeurIPS.cc/2021/Conference/Reviewers', member='~Reviewer_Amazon1')

        messages = client.get_messages(to='reviewer6@amazon.com', subject='[NeurIPS 2021] You have been assigned as a Reviewer for paper number 4')
        assert messages and len(messages) == 1
        assert messages[0]['content']['text'] == f'<p>This is to inform you that you have been assigned as a Reviewer for paper number 4 for NeurIPS 2021.</p>\n<p>To review this new assignment, please login to OpenReview and go to <a href=\"https://openreview.net/forum?id={submission.id}\">https://openreview.net/forum?id={submission.id}</a>.</p>\n<p>To check all of your assigned papers, go to <a href=\"https://openreview.net/group?id=NeurIPS.cc/2021/Conference/Reviewers\">https://openreview.net/group?id=NeurIPS.cc/2021/Conference/Reviewers</a>.</p>\n<p>Thank you,</p>\n<p>NeurIPS 2021 Conference Program Chairs</p>\n'

        ## Delete assignment when there is a review should throw an error
        submission=conference.get_submissions(number=5)[0]
        assignment_edge=client.get_edges(invitation='NeurIPS.cc/2021/Conference/Reviewers/-/Assignment', head=submission.id, tail='~Reviewer_UMass1')[0]
        assignment_edge.ddate=openreview.tools.datetime_millis(datetime.datetime.utcnow())
        with pytest.raises(openreview.OpenReviewException, match=r'Can not remove assignment, the user ~Reviewer_UMass1 already posted a review.'):
            client.post_edge(assignment_edge)


    def test_comment_stage(self, conference, helpers, test_client, client):

        now = datetime.datetime.utcnow()
        due_date = now + datetime.timedelta(days=3)
        conference.set_comment_stage(openreview.CommentStage(reader_selection=True, unsubmitted_reviewers=True, check_mandatory_readers=True))

        reviewer_client=openreview.Client(username='reviewer1@umass.edu', password='1234')

        signatory_groups=client.get_groups(regex='NeurIPS.cc/2021/Conference/Paper5/Reviewer_', signatory='reviewer1@umass.edu')
        assert len(signatory_groups) == 1

        submissions=conference.get_submissions(number=5)
        assert len(submissions) == 1

        review_note=reviewer_client.post_note(openreview.Note(
            invitation='NeurIPS.cc/2021/Conference/Paper5/-/Official_Comment',
            forum=submissions[0].id,
            replyto=submissions[0].id,
            readers=['NeurIPS.cc/2021/Conference/Program_Chairs', 'NeurIPS.cc/2021/Conference/Paper5/Senior_Area_Chairs', 'NeurIPS.cc/2021/Conference/Paper5/Area_Chairs', signatory_groups[0].id],
            #nonreaders=['NeurIPS.cc/2021/Conference/Paper5/Authors'],
            writers=[signatory_groups[0].id],
            signatures=[signatory_groups[0].id],
            content={
                'title': 'Test comment',
                'comment': 'This is a comment'
            }
        ))

        helpers.await_queue()

        process_logs = client.get_process_logs(id=review_note.id)
        assert len(process_logs) == 1
        assert process_logs[0]['status'] == 'ok'

        messages = client.get_messages(to='reviewer1@umass.edu', subject='[NeurIPS 2021] Your comment was received on Paper Number: 5, Paper Title: \"Paper title 5\"')
        assert messages and len(messages) == 1

        messages = client.get_messages(to='ac1@mit.edu', subject='\[NeurIPS 2021\] Reviewer .* commented on a paper in your area. Paper Number: 5, Paper Title: \"Paper title 5\"')
        assert messages and len(messages) == 1

        messages = client.get_messages(to='sac1@google.com', subject='\[NeurIPS 2021\] Reviewer .* commented on a paper in your area. Paper Number: 5, Paper Title: \"Paper title 5\"')
        assert not messages

        ac_client=openreview.Client(username='ac1@mit.edu', password='1234')

        signatory_groups=client.get_groups(regex='NeurIPS.cc/2021/Conference/Paper5/Area_Chair_', signatory='ac1@mit.edu')
        assert len(signatory_groups) == 1

        comment_note=ac_client.post_note(openreview.Note(
            invitation='NeurIPS.cc/2021/Conference/Paper5/-/Official_Comment',
            forum=submissions[0].id,
            replyto=submissions[0].id,
            readers=['NeurIPS.cc/2021/Conference/Program_Chairs', 'NeurIPS.cc/2021/Conference/Paper5/Senior_Area_Chairs', 'NeurIPS.cc/2021/Conference/Paper5/Area_Chairs'],
            #nonreaders=['NeurIPS.cc/2021/Conference/Paper5/Authors'],
            writers=[signatory_groups[0].id],
            signatures=[signatory_groups[0].id],
            content={
                'title': 'Test an AC comment',
                'comment': 'This is an AC comment'
            }
        ))

        helpers.await_queue()

        process_logs = client.get_process_logs(id=comment_note.id)
        assert len(process_logs) == 1
        assert process_logs[0]['status'] == 'ok'

        messages = client.get_messages(to='ac1@mit.edu', subject='[NeurIPS 2021] Your comment was received on Paper Number: 5, Paper Title: \"Paper title 5\"')
        assert messages and len(messages) == 1

        messages = client.get_messages(to='sac1@google.com', subject='\[NeurIPS 2021\] Area Chair .* commented on a paper in your area. Paper Number: 5, Paper Title: \"Paper title 5\"')
        assert messages and len(messages) == 1

        sac_client=openreview.Client(username='sac1@google.com', password='1234')

        comment_note=sac_client.post_note(openreview.Note(
            invitation='NeurIPS.cc/2021/Conference/Paper5/-/Official_Comment',
            forum=submissions[0].id,
            replyto=submissions[0].id,
            readers=['NeurIPS.cc/2021/Conference/Program_Chairs', 'NeurIPS.cc/2021/Conference/Paper5/Senior_Area_Chairs', 'NeurIPS.cc/2021/Conference/Paper5/Area_Chairs'],
            writers=['NeurIPS.cc/2021/Conference/Paper5/Senior_Area_Chairs'],
            signatures=['NeurIPS.cc/2021/Conference/Paper5/Senior_Area_Chairs'],
            content={
                'title': 'Test an SAC comment',
                'comment': 'This is an SAC comment'
            }
        ))

        helpers.await_queue()

        process_logs = client.get_process_logs(id=comment_note.id)
        assert len(process_logs) == 1
        assert process_logs[0]['status'] == 'ok'

        messages = client.get_messages(to='sac1@google.com', subject='[NeurIPS 2021] Your comment was received on Paper Number: 5, Paper Title: \"Paper title 5\"')
        assert messages and len(messages) == 1

    def test_rebuttal_stage(self, conference, helpers, test_client, client):

        now = datetime.datetime.utcnow()
        due_date = now + datetime.timedelta(days=3)

        pc_client=openreview.Client(username='pc@neurips.cc', password='1234')
        request_form=pc_client.get_notes(invitation='openreview.net/Support/-/Request_Form')[0]
        stage_note=client.post_note(openreview.Note(
            content={
                'review_deadline': due_date.strftime('%Y/%m/%d'),
                'make_reviews_public': 'No, reviews should NOT be revealed publicly when they are posted',
                'release_reviews_to_authors': 'Yes, reviews should be revealed when they are posted to the paper\'s authors',
                'release_reviews_to_reviewers': 'Reviews should be immediately revealed to the paper\'s reviewers who have already submitted their review',
                'email_program_chairs_about_reviews': 'No, do not email program chairs about received reviews'
            },
            forum=request_form.forum,
            invitation='openreview.net/Support/-/Request{}/Review_Stage'.format(request_form.number),
            readers=['NeurIPS.cc/2021/Conference/Program_Chairs', 'openreview.net/Support'],
            referent=request_form.forum,
            replyto=request_form.forum,
            signatures=['~Program_NeurIPSChair1'],
            writers=[]
        ))

        helpers.await_queue()

        reviews=client.get_notes(invitation='NeurIPS.cc/2021/Conference/Paper.*/-/Official_Review', sort='tmdate')
        assert len(reviews) == 1
        reviews[0].readers = [
            'NeurIPS.cc/2021/Conference/Program_Chairs',
            'NeurIPS.cc/2021/Conference/Paper5/Senior_Area_Chairs',
            'NeurIPS.cc/2021/Conference/Paper5/Area_Chairs',
            'NeurIPS.cc/2021/Conference/Paper5/Reviewers/Submitted',
            'NeurIPS.cc/2021/Conference/Paper5/Authors'
        ]

        now = datetime.datetime.utcnow()
        due_date = now + datetime.timedelta(days=3)
        conference.set_comment_stage(openreview.CommentStage(reader_selection=True, unsubmitted_reviewers=False, authors=True))

        submissions=conference.get_submissions(number=5)
        assert len(submissions) == 1

        rebuttal_note=test_client.post_note(openreview.Note(
            invitation='NeurIPS.cc/2021/Conference/Paper5/-/Official_Comment',
            forum=submissions[0].id,
            replyto=reviews[0].id,
            readers=[
                'NeurIPS.cc/2021/Conference/Program_Chairs',
                'NeurIPS.cc/2021/Conference/Paper5/Senior_Area_Chairs',
                'NeurIPS.cc/2021/Conference/Paper5/Area_Chairs',
                'NeurIPS.cc/2021/Conference/Paper5/Reviewers/Submitted',
                'NeurIPS.cc/2021/Conference/Paper5/Authors'
            ],
            #nonreaders=['NeurIPS.cc/2021/Conference/Paper5/Authors'],
            writers=['NeurIPS.cc/2021/Conference/Paper5/Authors'],
            signatures=['NeurIPS.cc/2021/Conference/Paper5/Authors'],
            content={
                'title': 'Thanks for your review',
                'comment': 'Thanks for the detailed review!'
            }
        ))

        helpers.await_queue()


    def test_meta_review_stage(self, conference, helpers, test_client, client):

        now = datetime.datetime.utcnow()
        due_date = now + datetime.timedelta(days=3)
        conference.set_meta_review_stage(openreview.MetaReviewStage(due_date=due_date))

        ac_client=openreview.Client(username='ac1@mit.edu', password='1234')

        signatory_groups=client.get_groups(regex='NeurIPS.cc/2021/Conference/Paper5/Area_Chair_', signatory='ac1@mit.edu')
        assert len(signatory_groups) == 1

        submissions=conference.get_submissions(number=5)
        assert len(submissions) == 1

        meta_review_note=ac_client.post_note(openreview.Note(
            invitation='NeurIPS.cc/2021/Conference/Paper5/-/Meta_Review',
            forum=submissions[0].id,
            replyto=submissions[0].id,
            readers=['NeurIPS.cc/2021/Conference/Program_Chairs', 'NeurIPS.cc/2021/Conference/Paper5/Senior_Area_Chairs', 'NeurIPS.cc/2021/Conference/Paper5/Area_Chairs'],
            nonreaders = ['NeurIPS.cc/2021/Conference/Paper5/Authors'],
            writers=['NeurIPS.cc/2021/Conference/Program_Chairs', 'NeurIPS.cc/2021/Conference/Paper5/Area_Chairs'],
            signatures=[signatory_groups[0].id],
            content={
                'metareview': 'Paper is very good!',
                'recommendation': 'Accept (Oral)',
                'confidence': '4: The area chair is confident but not absolutely certain'
            }
        ))

    def test_paper_ranking_stage(self, conference, client, test_client, selenium, request_page):

        ac_client=openreview.Client(username='ac1@mit.edu', password='1234')
        signatory_groups=client.get_groups(regex='NeurIPS.cc/2021/Conference/Paper5/Area_Chair_', signatory='ac1@mit.edu')
        assert len(signatory_groups) == 1
        ac_anon_id=signatory_groups[0].id

        ac_url = 'http://localhost:3030/group?id=NeurIPS.cc/2021/Conference/Area_Chairs'
        request_page(selenium, ac_url, ac_client.token, wait_for_element='5-metareview-status')

        status = selenium.find_element_by_id("5-metareview-status")
        assert status

        assert not status.find_elements_by_class_name('tag-widget')

        reviewer_client=openreview.Client(username='reviewer1@umass.edu', password='1234')

        signatory_groups=client.get_groups(regex='NeurIPS.cc/2021/Conference/Paper5/Reviewer_', signatory='reviewer1@umass.edu')
        assert len(signatory_groups) == 1
        reviewer_anon_id=signatory_groups[0].id

        reviewer_url = 'http://localhost:3030/group?id=NeurIPS.cc/2021/Conference/Reviewers'
        request_page(selenium, reviewer_url, reviewer_client.token)

        assert not selenium.find_elements_by_class_name('tag-widget')

        now = datetime.datetime.utcnow()
        conference.open_paper_ranking(conference.get_area_chairs_id(), due_date=now + datetime.timedelta(minutes = 40))
        conference.open_paper_ranking(conference.get_reviewers_id(), due_date=now + datetime.timedelta(minutes = 40))

        ac_url = 'http://localhost:3030/group?id=NeurIPS.cc/2021/Conference/Area_Chairs'
        request_page(selenium, ac_url, ac_client.token, by=By.ID, wait_for_element='5-metareview-status')

        status = selenium.find_element_by_id("5-metareview-status")
        assert status

        tag = status.find_element_by_class_name('tag-widget')
        assert tag

        options = tag.find_elements_by_tag_name("li")
        assert options
        assert len(options) == 3

        options = tag.find_elements_by_tag_name("a")
        assert options
        assert len(options) == 3

        blinded_notes = conference.get_submissions(sort='number:asc')

        ac_client.post_tag(openreview.Tag(invitation = 'NeurIPS.cc/2021/Conference/Area_Chairs/-/Paper_Ranking',
            forum = blinded_notes[-1].id,
            tag = '1 of 3',
            readers = ['NeurIPS.cc/2021/Conference', ac_anon_id],
            signatures = [ac_anon_id])
        )

        reviewer_url = 'http://localhost:3030/group?id=NeurIPS.cc/2021/Conference/Reviewers'
        request_page(selenium, reviewer_url, reviewer_client.token, by=By.CLASS_NAME, wait_for_element='tag-widget')

        tags = selenium.find_elements_by_class_name('tag-widget')
        assert tags

        options = tags[0].find_elements_by_tag_name("li")
        assert options
        assert len(options) == 5

        options = tags[0].find_elements_by_tag_name("a")
        assert options
        assert len(options) == 5

        reviewer_client.post_tag(openreview.Tag(invitation = 'NeurIPS.cc/2021/Conference/Reviewers/-/Paper_Ranking',
            forum = blinded_notes[-1].id,
            tag = '2 of 5',
            readers = ['NeurIPS.cc/2021/Conference', 'NeurIPS.cc/2021/Conference/Paper1/Area_Chairs', reviewer_anon_id],
            signatures = [reviewer_anon_id])
        )

        reviewer2_client = openreview.Client(username='reviewer2@mit.edu', password='1234')
        signatory_groups=client.get_groups(regex='NeurIPS.cc/2021/Conference/Paper1/Reviewer_', signatory='reviewer2@mit.edu')
        assert len(signatory_groups) == 1
        reviewer2_anon_id=signatory_groups[0].id

        reviewer2_client.post_tag(openreview.Tag(invitation = 'NeurIPS.cc/2021/Conference/Reviewers/-/Paper_Ranking',
            forum = blinded_notes[0].id,
            tag = '1 of 5',
            readers = ['NeurIPS.cc/2021/Conference', 'NeurIPS.cc/2021/Conference/Paper1/Area_Chairs', reviewer2_anon_id],
            signatures = [reviewer2_anon_id])
        )

        with pytest.raises(openreview.OpenReviewException) as openReviewError:
            reviewer2_client.post_tag(openreview.Tag(invitation = 'NeurIPS.cc/2021/Conference/Reviewers/-/Paper_Ranking',
                forum = blinded_notes[0].id,
                tag = '1 of 5',
                readers = ['NeurIPS.cc/2021/Conference', 'NeurIPS.cc/2021/Conference/Paper1/Area_Chairs', reviewer2_anon_id],
                signatures = [reviewer2_anon_id])
            )
        assert  openReviewError.value.args[0].get('name') == 'TooManyError'

    def test_review_rating_stage(self, conference, helpers, test_client, client):

        now = datetime.datetime.utcnow()
        conference.set_review_rating_stage(openreview.ReviewRatingStage(due_date = now + datetime.timedelta(minutes = 40)))

        ac_client = openreview.Client(username='ac1@mit.edu', password='1234')
        signatory_groups=client.get_groups(regex='NeurIPS.cc/2021/Conference/Paper5/Area_Chair_', signatory='ac1@mit.edu')
        assert len(signatory_groups) == 1
        ac_anon_id=signatory_groups[0].id

        submissions = conference.get_submissions(number=5)

        reviews = ac_client.get_notes(forum=submissions[0].id, invitation='NeurIPS.cc/2021/Conference/Paper.*/-/Official_Review')
        assert len(reviews) == 1

        review_rating_note = ac_client.post_note(openreview.Note(
            forum=submissions[0].id,
            replyto=reviews[0].id,
            invitation=reviews[0].signatures[0] + '/-/Review_Rating',
            readers=['NeurIPS.cc/2021/Conference/Program_Chairs',
            ac_anon_id],
            writers=[ac_anon_id],
            signatures=[ac_anon_id],
            content={
                'review_quality': 'Good'
            }
        ))
        assert review_rating_note

    def test_add_impersonator(self, client, request_page, selenium):
        ## Need super user permission to add the venue to the active_venues group
        request_form=client.get_notes(invitation='openreview.net/Support/-/Request_Form', sort='tmdate')[0]
        conference=openreview.helpers.get_conference(client, request_form.id)

        conference.set_impersonators(group_ids=['pc@neurips.cc'])

        pc_client = openreview.Client(username='pc@neurips.cc', password='1234')
        reviewers_id = conference.get_reviewers_id()
        reviewers = client.get_group(reviewers_id).members
        assert len(reviewers) > 0
        result = pc_client.impersonate(reviewers[0])

        assert result.get('token') is not None
        assert result.get('user', {}).get('id') == reviewers[0]

    def test_withdraw_after_review(self, conference, helpers, test_client, client, selenium, request_page):

        submissions = test_client.get_notes(invitation='NeurIPS.cc/2021/Conference/-/Blind_Submission', sort='tmdate')
        assert len(submissions) == 5

        withdrawn_note = test_client.post_note(openreview.Note(
            forum=submissions[0].id,
            replyto=submissions[0].id,
            invitation=f'NeurIPS.cc/2021/Conference/Paper5/-/Withdraw',
            readers = [
                'NeurIPS.cc/2021/Conference',
                'NeurIPS.cc/2021/Conference/Paper5/Authors',
                'NeurIPS.cc/2021/Conference/Paper5/Reviewers',
                'NeurIPS.cc/2021/Conference/Paper5/Area_Chairs',
                'NeurIPS.cc/2021/Conference/Paper5/Senior_Area_Chairs',
                'NeurIPS.cc/2021/Conference/Program_Chairs'],
            writers = [conference.get_id(), 'NeurIPS.cc/2021/Conference/Paper5/Authors'],
            signatures = ['NeurIPS.cc/2021/Conference/Paper5/Authors'],
            content = {
                'title': 'Submission Withdrawn by the Authors',
                'withdrawal confirmation': 'I have read and agree with the venue\'s withdrawal policy on behalf of myself and my co-authors.'
            }
        ))
        helpers.await_queue()

        process_logs = client.get_process_logs(id=withdrawn_note.id)
        assert len(process_logs) == 1
        assert process_logs[0]['status'] == 'ok'

        withdrawn_submission=client.get_note(submissions[0].id)
        assert withdrawn_submission.invitation == 'NeurIPS.cc/2021/Conference/-/Withdrawn_Submission'
        assert withdrawn_submission.readers == [
                'NeurIPS.cc/2021/Conference/Paper5/Authors',
                'NeurIPS.cc/2021/Conference/Paper5/Reviewers',
                'NeurIPS.cc/2021/Conference/Paper5/Area_Chairs',
                'NeurIPS.cc/2021/Conference/Paper5/Senior_Area_Chairs',
                'NeurIPS.cc/2021/Conference/Program_Chairs']
        assert withdrawn_submission.content['keywords'] == ''

        pc_client=openreview.Client(username='pc@neurips.cc', password='1234')

        request_page(selenium, "http://localhost:3030/group?id=NeurIPS.cc/2021/Conference/Program_Chairs#paper-status", pc_client.token, wait_for_element='notes')
        assert "NeurIPS 2021 Conference Program Chairs | OpenReview" in selenium.title
        notes_panel = selenium.find_element_by_id('notes')
        assert notes_panel
        tabs = notes_panel.find_element_by_class_name('tabs-container')
        assert tabs
        assert tabs.find_element_by_id('venue-configuration')
        assert tabs.find_element_by_id('paper-status')
        assert tabs.find_element_by_id('reviewer-status')
        assert tabs.find_element_by_id('areachair-status')

        assert '#' == tabs.find_element_by_id('paper-status').find_element_by_class_name('row-1').text
        assert 'Paper Summary' == tabs.find_element_by_id('paper-status').find_element_by_class_name('row-2').text
        assert 'Review Progress' == tabs.find_element_by_id('paper-status').find_element_by_class_name('row-3').text
        assert 'Status' == tabs.find_element_by_id('paper-status').find_element_by_class_name('row-4').text
        assert 'Decision' == tabs.find_element_by_id('paper-status').find_element_by_class_name('row-5').text

    def test_desk_reject_after_review(self, conference, helpers, test_client, client, selenium, request_page):

        submissions = test_client.get_notes(invitation='NeurIPS.cc/2021/Conference/-/Blind_Submission', sort='tmdate')
        assert len(submissions) == 4

        pc_client=openreview.Client(username='pc@neurips.cc', password='1234')

        desk_reject_note = pc_client.post_note(openreview.Note(
            forum=submissions[0].id,
            replyto=submissions[0].id,
            invitation=f'NeurIPS.cc/2021/Conference/Paper4/-/Desk_Reject',
            readers = [
                'NeurIPS.cc/2021/Conference',
                'NeurIPS.cc/2021/Conference/Paper4/Authors',
                'NeurIPS.cc/2021/Conference/Paper4/Reviewers',
                'NeurIPS.cc/2021/Conference/Paper4/Area_Chairs',
                'NeurIPS.cc/2021/Conference/Paper4/Senior_Area_Chairs',
                'NeurIPS.cc/2021/Conference/Program_Chairs'],
            writers = [conference.get_id(), 'NeurIPS.cc/2021/Conference/Program_Chairs'],
            signatures = ['NeurIPS.cc/2021/Conference/Program_Chairs'],
            content = {
                'title': 'Submission Desk Rejected by Program Chairs',
                'desk_reject_comments': 'Wrong PDF.'
            }
        ))
        helpers.await_queue()

        desk_rejected_submission=client.get_note(submissions[0].id)
        assert desk_rejected_submission.invitation == 'NeurIPS.cc/2021/Conference/-/Desk_Rejected_Submission'
        assert desk_rejected_submission.readers == [
                'NeurIPS.cc/2021/Conference/Paper4/Authors',
                'NeurIPS.cc/2021/Conference/Paper4/Reviewers',
                'NeurIPS.cc/2021/Conference/Paper4/Area_Chairs',
                'NeurIPS.cc/2021/Conference/Paper4/Senior_Area_Chairs',
                'NeurIPS.cc/2021/Conference/Program_Chairs']
        assert desk_rejected_submission.content['keywords'] == ''

        desk_reject_note.ddate = openreview.tools.datetime_millis(datetime.datetime.now())
        pc_client.post_note(desk_reject_note)

        helpers.await_queue()

        submission_note = client.get_note(desk_reject_note.forum)
        assert submission_note.invitation == 'NeurIPS.cc/2021/Conference/-/Blind_Submission'
        assert submission_note.readers == [
                'NeurIPS.cc/2021/Conference',
                'NeurIPS.cc/2021/Conference/Senior_Area_Chairs',
                'NeurIPS.cc/2021/Conference/Area_Chairs',
                'NeurIPS.cc/2021/Conference/Reviewers',
                'NeurIPS.cc/2021/Conference/Paper4/Authors'
                ]
        assert submission_note.content['keywords'] == ''