from __future__ import absolute_import, division, print_function, unicode_literals
import openreview
import pytest
import requests
import datetime
import os
import re
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

class TestDoubleBlindConference():

    def test_create_conference(self, client):

        builder = openreview.conference.ConferenceBuilder(client)
        assert builder, 'builder is None'

        builder.set_conference_id('AKBC.ws/2019/Conference')

        conference = builder.get_result()
        assert conference, 'conference is None'

        groups = conference.get_conference_groups()
        assert groups
        assert groups[0].id == 'AKBC.ws'
        assert groups[0].readers == ['everyone']
        assert groups[0].nonreaders == []
        assert groups[0].writers == ['AKBC.ws']
        assert groups[0].signatures == ['~Super_User1']
        assert groups[0].signatories == ['AKBC.ws']
        assert groups[0].members == []
        assert groups[1].id == 'AKBC.ws/2019'
        assert groups[1].readers == ['everyone']
        assert groups[1].nonreaders == []
        assert groups[1].writers == ['AKBC.ws/2019']
        assert groups[1].signatures == ['~Super_User1']
        assert groups[1].signatories == ['AKBC.ws/2019']
        assert groups[1].members == []
        assert groups[2].id == 'AKBC.ws/2019/Conference'
        assert groups[2].readers == ['everyone']
        assert groups[2].nonreaders == []
        assert groups[2].writers == ['AKBC.ws/2019/Conference']
        assert groups[2].signatures == ['~Super_User1']
        assert groups[2].signatories == ['AKBC.ws/2019/Conference']
        assert groups[2].members == []
        assert '"title": "AKBC.ws/2019/Conference"' in groups[2].web

        assert client.get_group(id = 'AKBC.ws')
        assert client.get_group(id = 'AKBC.ws/2019')
        assert client.get_group(id = 'AKBC.ws/2019/Conference')

        resp = requests.get('http://localhost:3000/group?id=AKBC.ws')
        assert resp.status_code == 200

        resp = requests.get('http://localhost:3000/group?id=AKBC.ws/2019')
        assert resp.status_code == 200

        resp = requests.get('http://localhost:3000/group?id=AKBC.ws/2019/Conference')
        assert resp.status_code == 200

    def test_create_conference_with_name(self, client):

        builder = openreview.conference.ConferenceBuilder(client)
        assert builder, 'builder is None'

        builder.set_conference_id('AKBC.ws/2019/Conference')
        builder.set_conference_name('Automated Knowledge Base Construction')

        conference = builder.get_result()
        assert conference, 'conference is None'

        groups = conference.get_conference_groups()
        assert groups
        assert groups[0].id == 'AKBC.ws'
        assert groups[0].readers == ['everyone']
        assert groups[0].nonreaders == []
        assert groups[0].writers == ['AKBC.ws']
        assert groups[0].signatures == ['~Super_User1']
        assert groups[0].signatories == ['AKBC.ws']
        assert groups[0].members == []
        assert groups[1].id == 'AKBC.ws/2019'
        assert groups[1].readers == ['everyone']
        assert groups[1].nonreaders == []
        assert groups[1].writers == ['AKBC.ws/2019']
        assert groups[1].signatures == ['~Super_User1']
        assert groups[1].signatories == ['AKBC.ws/2019']
        assert groups[1].members == []
        assert groups[2].id == 'AKBC.ws/2019/Conference'
        assert groups[2].readers == ['everyone']
        assert groups[2].nonreaders == []
        assert groups[2].writers == ['AKBC.ws/2019/Conference']
        assert groups[2].signatures == ['~Super_User1']
        assert groups[2].signatories == ['AKBC.ws/2019/Conference']
        assert groups[2].members == []
        assert '"title": "AKBC.ws/2019/Conference"' in groups[2].web
        assert '"subtitle": "Automated Knowledge Base Construction"' in groups[2].web

        assert client.get_group(id = 'AKBC.ws')
        assert client.get_group(id = 'AKBC.ws/2019')
        assert client.get_group(id = 'AKBC.ws/2019/Conference')

        resp = requests.get('http://localhost:3000/group?id=AKBC.ws')
        assert resp.status_code == 200

        resp = requests.get('http://localhost:3000/group?id=AKBC.ws/2019')
        assert resp.status_code == 200

        resp = requests.get('http://localhost:3000/group?id=AKBC.ws/2019/Conference')
        assert resp.status_code == 200

    def test_create_conference_with_headers(self, client):

        builder = openreview.conference.ConferenceBuilder(client)
        assert builder, 'builder is None'

        builder.set_conference_id('AKBC.ws/2019/Conference')
        builder.set_conference_name('Automated Knowledge Base Construction')
        builder.set_homepage_header({
            'title': 'AKBC 2019',
            'subtitle': 'Automated Knowledge Base Construction',
            'location': 'Amherst, Massachusetts, United States',
            'date': 'May 20 - May 21, 2019',
            'website': 'http://www.akbc.ws/2019/',
            'instructions': '<p><strong>Important Information</strong>\
                <ul>\
                <li>Note to Authors, Reviewers and Area Chairs: Please update your OpenReview profile to have all your recent emails.</li>\
                <li>AKBC 2019 Conference submissions are now open.</li>\
                <li>For more details refer to the <a href="http://www.akbc.ws/2019/cfp/">AKBC 2019 - Call for Papers</a>.</li>\
                </ul></p> \
                <p><strong>Questions or Concerns</strong></p>\
                <p><ul>\
                <li>Please contact the AKBC 2019 Program Chairs at \
                <a href="mailto:info@akbc.ws">info@akbc.ws</a> with any questions or concerns about conference administration or policy.</li>\
                <li>Please contact the OpenReview support team at \
                <a href="mailto:info@openreview.net">info@openreview.net</a> with any questions or concerns about the OpenReview platform.</li>\
                </ul></p>',
            'deadline': 'Submission Deadline: Midnight Pacific Time, Friday, November 16, 2018'
        })
        builder.set_conference_type(openreview.conference.DoubleBlindConferenceType)

        conference = builder.get_result()
        assert conference, 'conference is None'

        groups = conference.get_conference_groups()
        assert groups
        assert groups[0].id == 'AKBC.ws'
        assert groups[0].readers == ['everyone']
        assert groups[0].nonreaders == []
        assert groups[0].writers == ['AKBC.ws']
        assert groups[0].signatures == ['~Super_User1']
        assert groups[0].signatories == ['AKBC.ws']
        assert groups[0].members == []
        assert groups[1].id == 'AKBC.ws/2019'
        assert groups[1].readers == ['everyone']
        assert groups[1].nonreaders == []
        assert groups[1].writers == ['AKBC.ws/2019']
        assert groups[1].signatures == ['~Super_User1']
        assert groups[1].signatories == ['AKBC.ws/2019']
        assert groups[1].members == []
        assert groups[2].id == 'AKBC.ws/2019/Conference'
        assert groups[2].readers == ['everyone']
        assert groups[2].nonreaders == []
        assert groups[2].writers == ['AKBC.ws/2019/Conference']
        assert groups[2].signatures == ['~Super_User1']
        assert groups[2].signatories == ['AKBC.ws/2019/Conference']
        assert groups[2].members == []
        assert '"title": "AKBC 2019"' in groups[2].web
        assert '"subtitle": "Automated Knowledge Base Construction"' in groups[2].web
        assert '"location": "Amherst, Massachusetts, United States"' in groups[2].web
        assert '"date": "May 20 - May 21, 2019"' in groups[2].web
        assert '"website": "http://www.akbc.ws/2019/"' in groups[2].web
        assert 'Important Information' in groups[2].web
        assert '"deadline": "Submission Deadline: Midnight Pacific Time, Friday, November 16, 2018"' in groups[2].web
        assert 'BLIND_SUBMISSION_ID' in groups[2].web



    def test_enable_submissions(self, client, selenium, request_page):


        builder = openreview.conference.ConferenceBuilder(client)
        assert builder, 'builder is None'

        builder.set_conference_id('AKBC.ws/2019/Conference')
        builder.set_conference_type(openreview.conference.DoubleBlindConferenceType)
        builder.set_conference_name('Automated Knowledge Base Construction')
        builder.set_homepage_header({
            'title': 'AKBC 2019',
            'subtitle': 'Automated Knowledge Base Construction',
            'location': 'Amherst, Massachusetts, United States',
            'date': 'May 20 - May 21, 2019',
            'website': 'http://www.akbc.ws/2019/',
            'instructions': '<p><strong>Important Information</strong>\
                <ul>\
                <li>Note to Authors, Reviewers and Area Chairs: Please update your OpenReview profile to have all your recent emails.</li>\
                <li>AKBC 2019 Conference submissions are now open.</li>\
                <li>For more details refer to the <a href="http://www.akbc.ws/2019/cfp/">AKBC 2019 - Call for Papers</a>.</li>\
                </ul></p> \
                <p><strong>Questions or Concerns</strong></p>\
                <p><ul>\
                <li>Please contact the AKBC 2019 Program Chairs at \
                <a href="mailto:info@akbc.ws">info@akbc.ws</a> with any questions or concerns about conference administration or policy.</li>\
                <li>Please contact the OpenReview support team at \
                <a href="mailto:info@openreview.net">info@openreview.net</a> with any questions or concerns about the OpenReview platform.</li>\
                </ul></p>',
            'deadline': 'Submission Deadline: Midnight Pacific Time, Friday, November 16, 2018'
        })
        conference = builder.get_result()
        invitation = conference.open_submissions(due_date = datetime.datetime(2019, 10, 5, 18, 00), subject_areas = ['Machine Learning',
            'Natural Language Processing',
            'Information Extraction',
            'Question Answering',
            'Reasoning',
            'Databases',
            'Information Integration',
            'Knowledge Representation',
            'Semantic Web',
            'Search',
            'Applications: Science',
            'Applications: Biomedicine',
            'Applications: Other',
            'Relational AI',
            'Fairness',
            'Human computation',
            'Crowd-sourcing',
            'Other'], additional_fields = [{
                'name': 'archival status',
                'definition': {
                    'description': 'Authors can change the archival/non-archival status up until the decision deadline',
                    'value-radio': [
                        'Archival',
                        'Non-Archival'
                    ],
                    'required': True
                }
            }])
        assert invitation
        assert invitation.duedate == 1570298400000
        assert 'subject areas' in invitation.reply['content']
        assert 'Question Answering' in invitation.reply['content']['subject areas']['values-dropdown']
        assert 'archival status' in invitation.reply['content']
        assert 10 == invitation.reply['content']['archival status']['order']

        posted_invitation = client.get_invitation(id = 'AKBC.ws/2019/Conference/-/Submission')
        assert posted_invitation
        assert posted_invitation.duedate == 1570298400000

        request_page(selenium, "http://localhost:3000/group?id=AKBC.ws/2019/Conference")

        assert "AKBC 2019 Conference | OpenReview" in selenium.title
        header = selenium.find_element_by_id('header')
        assert header
        assert "AKBC 2019" == header.find_element_by_tag_name("h1").text
        assert "Automated Knowledge Base Construction" == header.find_element_by_tag_name("h3").text
        assert "Amherst, Massachusetts, United States" == header.find_element_by_xpath(".//span[@class='venue-location']").text
        assert "May 20 - May 21, 2019" == header.find_element_by_xpath(".//span[@class='venue-date']").text
        assert "http://www.akbc.ws/2019/" == header.find_element_by_xpath(".//span[@class='venue-website']/a").text
        invitation_panel = selenium.find_element_by_id('invitation')
        assert invitation_panel
        assert len(invitation_panel.find_elements_by_tag_name('div')) == 1
        assert 'AKBC 2019 Conference Submission' == invitation_panel.find_element_by_class_name('btn').text
        notes_panel = selenium.find_element_by_id('notes')
        assert notes_panel
        tabs = notes_panel.find_element_by_class_name('tabs-container')
        assert tabs
        assert tabs.find_element_by_id('your-consoles')
        assert len(tabs.find_element_by_id('your-consoles').find_elements_by_tag_name('ul')) == 0
        assert tabs.find_element_by_id('recent-activity')
        assert len(tabs.find_element_by_id('recent-activity').find_elements_by_tag_name('ul')) == 0

    def test_post_submissions(self, client, test_client, selenium, request_page):

        builder = openreview.conference.ConferenceBuilder(client)
        assert builder, 'builder is None'

        builder.set_conference_id('AKBC.ws/2019/Conference')
        builder.set_conference_type(openreview.conference.DoubleBlindConferenceType)
        conference = builder.get_result()
        invitation = conference.open_submissions(due_date = datetime.datetime(2019, 10, 5, 18, 00), subject_areas = [])
        assert invitation

        note = openreview.Note(invitation = invitation.id,
            readers = ['~Test_User1', 'mbok@mail.com', 'andrew@mail.com'],
            writers = ['~Test_User1', 'mbok@mail.com', 'andrew@mail.com'],
            signatures = ['~Test_User1'],
            content = {
                'title': 'Paper title',
                'abstract': 'This is an abstract',
                'authorids': ['test@mail.com', 'mbok@mail.com', 'andrew@mail.com'],
                'authors': ['Test User', 'Melisa Bok', 'Andrew Mc']
            }
        )
        url = test_client.put_pdf(os.path.join(os.path.dirname(__file__), 'data/paper.pdf'))
        note.content['pdf'] = url
        test_client.post_note(note)

        # Author user
        request_page(selenium, "http://localhost:3000/group?id=AKBC.ws/2019/Conference", test_client.token)
        invitation_panel = selenium.find_element_by_id('invitation')
        assert invitation_panel
        assert len(invitation_panel.find_elements_by_tag_name('div')) == 1
        assert 'AKBC 2019 Conference Submission' == invitation_panel.find_element_by_class_name('btn').text
        notes_panel = selenium.find_element_by_id('notes')
        assert notes_panel
        tabs = notes_panel.find_element_by_class_name('tabs-container')
        assert tabs
        assert tabs.find_element_by_id('your-consoles')
        assert len(tabs.find_element_by_id('your-consoles').find_elements_by_tag_name('ul')) == 1
        console = tabs.find_element_by_id('your-consoles').find_elements_by_tag_name('ul')[0]
        assert 'Author Console' == console.find_element_by_tag_name('a').text
        assert tabs.find_element_by_id('recent-activity')
        assert len(tabs.find_element_by_id('recent-activity').find_elements_by_class_name('activity-list')) == 1

        request_page(selenium, "http://localhost:3000/group?id=AKBC.ws/2019/Conference/Authors", test_client.token)
        tabs = selenium.find_element_by_class_name('tabs-container')
        assert tabs
        assert tabs.find_element_by_id('author-schedule')
        assert tabs.find_element_by_id('author-tasks')
        assert tabs.find_element_by_id('your-submissions')
        papers = tabs.find_element_by_id('your-submissions').find_element_by_class_name('submissions-list')
        assert len(papers.find_elements_by_class_name('note')) == 1

        # Guest user
        request_page(selenium, "http://localhost:3000/group?id=AKBC.ws/2019/Conference")
        invitation_panel = selenium.find_element_by_id('invitation')
        assert invitation_panel
        assert len(invitation_panel.find_elements_by_tag_name('div')) == 1
        assert 'AKBC 2019 Conference Submission' == invitation_panel.find_element_by_class_name('btn').text
        notes_panel = selenium.find_element_by_id('notes')
        assert notes_panel
        tabs = notes_panel.find_element_by_class_name('tabs-container')
        assert tabs
        assert tabs.find_element_by_id('your-consoles')
        assert len(tabs.find_element_by_id('your-consoles').find_elements_by_tag_name('ul')) == 0
        assert tabs.find_element_by_id('recent-activity')
        assert len(tabs.find_element_by_id('recent-activity').find_elements_by_class_name('activity-list')) == 0

        # Co-author user
        co_author_client = openreview.Client(username='mbok@mail.com', password='1234')
        request_page(selenium, "http://localhost:3000/group?id=AKBC.ws/2019/Conference", co_author_client.token)
        invitation_panel = selenium.find_element_by_id('invitation')
        assert invitation_panel
        assert len(invitation_panel.find_elements_by_tag_name('div')) == 1
        assert 'AKBC 2019 Conference Submission' == invitation_panel.find_element_by_class_name('btn').text
        notes_panel = selenium.find_element_by_id('notes')
        assert notes_panel
        tabs = notes_panel.find_element_by_class_name('tabs-container')
        assert tabs
        assert tabs.find_element_by_id('your-consoles')
        assert len(tabs.find_element_by_id('your-consoles').find_elements_by_tag_name('ul')) == 1
        console = tabs.find_element_by_id('your-consoles').find_elements_by_tag_name('ul')[0]
        assert 'Author Console' == console.find_element_by_tag_name('a').text
        assert tabs.find_element_by_id('recent-activity')
        assert len(tabs.find_element_by_id('recent-activity').find_elements_by_class_name('activity-list')) == 1

        request_page(selenium, "http://localhost:3000/group?id=AKBC.ws/2019/Conference/Authors", co_author_client.token)
        tabs = selenium.find_element_by_class_name('tabs-container')
        assert tabs
        assert tabs.find_element_by_id('author-schedule')
        assert tabs.find_element_by_id('author-tasks')
        assert tabs.find_element_by_id('your-submissions')
        papers = tabs.find_element_by_id('your-submissions').find_element_by_class_name('submissions-list')
        assert len(papers.find_elements_by_class_name('note')) == 1


    def test_recruit_reviewers(self, client, selenium, request_page):

        builder = openreview.conference.ConferenceBuilder(client)
        assert builder, 'builder is None'

        builder.set_conference_id('AKBC.ws/2019/Conference')
        builder.set_conference_type(openreview.conference.DoubleBlindConferenceType)
        conference = builder.get_result()

        result = conference.recruit_reviewers(['mbok@mail.com', 'mohit@mail.com'])
        assert result
        assert result.id == 'AKBC.ws/2019/Conference/Reviewers/Invited'
        assert 'mbok@mail.com' in result.members
        assert 'mohit@mail.com' in result.members

        group = client.get_group('AKBC.ws/2019/Conference/Reviewers')
        assert group
        assert len(group.members) == 0

        group = client.get_group('AKBC.ws/2019/Conference/Reviewers/Invited')
        assert group
        assert len(group.members) == 2

        group = client.get_group('AKBC.ws/2019/Conference/Reviewers/Declined')
        assert group
        assert len(group.members) == 0

        result = conference.recruit_reviewers(['michael@mail.com'])
        assert result
        assert result.id == 'AKBC.ws/2019/Conference/Reviewers/Invited'
        assert 'mbok@mail.com' in result.members
        assert 'mohit@mail.com' in result.members
        assert 'michael@mail.com' in result.members

        group = client.get_group('AKBC.ws/2019/Conference/Reviewers')
        assert group
        assert len(group.members) == 0

        group = client.get_group('AKBC.ws/2019/Conference/Reviewers/Invited')
        assert group
        assert len(group.members) == 3

        group = client.get_group('AKBC.ws/2019/Conference/Reviewers/Declined')
        assert group
        assert len(group.members) == 0

        invitation = client.get_invitation('AKBC.ws/2019/Conference/-/Recruit_Reviewers')
        assert invitation
        assert invitation.process
        assert invitation.web

        response = client.get_messages(to = 'mbok@mail.com', subject = 'AKBC.ws/2019/Conference: Invitation to Review')
        assert response
        assert len(response['messages']) == 1

        text = response['messages'][0]['content']['text']

        # Accept invitation
        accept_url = re.search('http://.*response=Yes', text).group(0)
        request_page(selenium, accept_url)

        group = client.get_group('AKBC.ws/2019/Conference/Reviewers')
        assert group
        assert len(group.members) == 1
        assert 'mbok@mail.com' in group.members

        group = client.get_group('AKBC.ws/2019/Conference/Reviewers/Declined')
        assert group
        assert len(group.members) == 0

        # Reject invitation
        reject_url = re.search('http://.*response=No', text).group(0)
        request_page(selenium, reject_url)

        group = client.get_group('AKBC.ws/2019/Conference/Reviewers')
        assert group
        assert len(group.members) == 0

        group = client.get_group('AKBC.ws/2019/Conference/Reviewers/Declined')
        assert group
        assert len(group.members) == 1
        assert 'mbok@mail.com' in group.members

        # Recruit more reviewers
        result = conference.recruit_reviewers(['mbok@mail.com', 'other@mail.com'])
        assert result
        assert result.id == 'AKBC.ws/2019/Conference/Reviewers/Invited'
        assert 'mbok@mail.com' in result.members
        assert 'mohit@mail.com' in result.members
        assert 'michael@mail.com' in result.members
        assert 'other@mail.com' in result.members

        # Don't send the invitation twice
        response = client.get_messages(to = 'mbok@mail.com', subject = 'AKBC.ws/2019/Conference: Invitation to Review')
        assert response
        assert len(response['messages']) == 1

    def test_set_program_chairs(self, client):

        builder = openreview.conference.ConferenceBuilder(client)
        assert builder, 'builder is None'

        builder.set_conference_id('AKBC.ws/2019/Conference')
        builder.set_conference_type(openreview.conference.DoubleBlindConferenceType)
        conference = builder.get_result()

        result = conference.set_program_chairs(['pc@mail.com', 'pc2@mail.com'])
        assert result
        assert result.members
        assert ['pc@mail.com', 'pc2@mail.com'] == result.members

        #Sign up as Program Chair
        pc_client = openreview.Client(baseurl = 'http://localhost:3000')
        assert pc_client is not None, "Client is none"
        res = pc_client.register_user(email = 'pc@mail.com', first = 'Pc', last = 'Chair', password = '1234')
        assert res, "Res i none"
        res = pc_client.activate_user('pc@mail.com', {
            'names': [
                    {
                        'first': 'Pc',
                        'last': 'Chair',
                        'username': '~Pc_Chair1'
                    }
                ],
            'emails': ['pc@mail.com'],
            'preferredEmail': 'pc@mail.com'
            })
        assert res, "Res i none"
        group = pc_client.get_group(id = 'pc@mail.com')
        assert group
        assert group.members == ['~Pc_Chair1']

        group = pc_client.get_group(id = 'AKBC.ws/2019/Conference/Reviewers')
        assert group
        assert len(group.members) == 0

        group = pc_client.get_group(id = 'AKBC.ws/2019/Conference/Reviewers/Invited')
        assert group
        assert len(group.members) == 4

        group = pc_client.get_group(id = 'AKBC.ws/2019/Conference/Reviewers/Declined')
        assert group
        assert len(group.members) == 1

    def test_close_submission(self, client, test_client, selenium, request_page):

        builder = openreview.conference.ConferenceBuilder(client)
        assert builder, 'builder is None'

        builder.set_conference_id('AKBC.ws/2019/Conference')
        builder.set_conference_type(openreview.conference.DoubleBlindConferenceType)
        conference = builder.get_result()

        notes = test_client.get_notes(invitation='AKBC.ws/2019/Conference/-/Submission')
        submission = notes[0]
        submission.content['title'] = 'New paper title'
        test_client.post_note(submission)

        notes = test_client.get_notes(invitation='AKBC.ws/2019/Conference/-/Submission')
        assert 'New paper title' == notes[0].content['title']
        assert '~Test_User1' in notes[0].writers
        assert 'mbok@mail.com' in notes[0].writers
        assert 'andrew@mail.com' in notes[0].writers

        request_page(selenium, "http://localhost:3000/forum?id=" + submission.id, test_client.token)

        assert len(selenium.find_elements_by_class_name('edit_button')) == 1
        assert len(selenium.find_elements_by_class_name('trash_button')) == 1

        conference.close_submissions()
        notes = test_client.get_notes(invitation='AKBC.ws/2019/Conference/-/Submission')
        submission = notes[0]
        assert ['AKBC.ws/2019/Conference'] == submission.writers

        request_page(selenium, "http://localhost:3000/forum?id=" + submission.id, test_client.token)

        assert len(selenium.find_elements_by_class_name('edit_button')) == 0
        assert len(selenium.find_elements_by_class_name('trash_button')) == 0

