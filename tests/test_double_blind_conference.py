from __future__ import absolute_import, division, print_function, unicode_literals
import openreview
import pytest
import requests
import datetime
import time
import os
import re
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import NoSuchElementException

class TestDoubleBlindConference():

    def test_create_conference(self, client):

        builder = openreview.conference.ConferenceBuilder(client)
        assert builder, 'builder is None'

        builder.set_conference_id('AKBC.ws/2019/Conference')
        builder.set_double_blind(True)
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
        assert groups[2].signatures == ['AKBC.ws/2019/Conference']
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
        builder.set_override_homepage(True)
        builder.set_double_blind(True)

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
        assert groups[2].signatures == ['AKBC.ws/2019/Conference']
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

    def test_create_conference_with_headers(self, client, selenium, request_page):

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
        builder.set_override_homepage(True)
        builder.set_double_blind(True)

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
        assert groups[2].signatures == ['AKBC.ws/2019/Conference']
        assert groups[2].signatories == ['AKBC.ws/2019/Conference']
        assert groups[2].members == []
        assert '"title": "AKBC 2019"' in groups[2].web
        assert '"subtitle": "Automated Knowledge Base Construction"' in groups[2].web
        assert '"location": "Amherst, Massachusetts, United States"' in groups[2].web
        assert '"date": "May 20 - May 21, 2019"' in groups[2].web
        assert '"website": "http://www.akbc.ws/2019/"' in groups[2].web
        assert 'Important Information' in groups[2].web
        assert '"deadline": "Submission Deadline: Midnight Pacific Time, Friday, November 16, 2018"' in groups[2].web
        assert "var BLIND_SUBMISSION_ID = 'AKBC.ws/2019/Conference/-/Blind_Submission';" in groups[2].web

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
        assert len(invitation_panel.find_elements_by_tag_name('div')) == 0
        notes_panel = selenium.find_element_by_id('notes')
        assert notes_panel
        tabs = notes_panel.find_element_by_class_name('tabs-container')
        assert tabs
        with pytest.raises(NoSuchElementException):
            notes_panel.find_element_by_class_name('spinner-container')

    def test_enable_submissions(self, client, selenium, request_page):

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
        builder.set_double_blind(True)
        conference = builder.get_result()

        now = datetime.datetime.utcnow()
        invitation = conference.open_submissions(due_date = now + datetime.timedelta(minutes = 10))
        assert invitation
        assert invitation.duedate == openreview.tools.datetime_millis(now + datetime.timedelta(minutes = 10))
        assert invitation.expdate == openreview.tools.datetime_millis(now + datetime.timedelta(minutes = 40))

        posted_invitation = client.get_invitation(id = 'AKBC.ws/2019/Conference/-/Submission')
        assert posted_invitation
        assert posted_invitation.duedate == openreview.tools.datetime_millis(now + datetime.timedelta(minutes = 10))
        assert posted_invitation.expdate == openreview.tools.datetime_millis(now + datetime.timedelta(minutes = 40))

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

    def test_post_submissions(self, client, test_client, peter_client, selenium, request_page):

        builder = openreview.conference.ConferenceBuilder(client)
        assert builder, 'builder is None'

        builder.set_conference_id('AKBC.ws/2019/Conference')
        builder.set_conference_short_name('AKBC 2019')
        builder.set_authorpage_header({
            'title': 'Author Console',
            'instructions': 'Instructions for author console',
            'schedule': 'This is the author schedule'
        })
        builder.set_double_blind(True)
        builder.set_subject_areas(['Machine Learning',
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
            'Other'])
        conference = builder.get_result()

        now = datetime.datetime.utcnow()
        invitation = conference.open_submissions(due_date = now + datetime.timedelta(minutes = 10), additional_fields = {
                'archival_status': {
                    'description': 'Authors can change the archival/non-archival status up until the decision deadline',
                    'value-radio': [
                        'Archival',
                        'Non-Archival'
                    ],
                    'required': True
                }
            })
        assert invitation
        assert 'subject_areas' in invitation.reply['content']
        assert 'Question Answering' in invitation.reply['content']['subject_areas']['values-dropdown']
        assert 'archival_status' in invitation.reply['content']
        assert 10 == invitation.reply['content']['archival_status']['order']

        note = openreview.Note(invitation = invitation.id,
            readers = ['~Test_User1', 'peter@mail.com', 'andrew@mail.com'],
            writers = [conference.id, '~Test_User1', 'peter@mail.com', 'andrew@mail.com'],
            signatures = ['~Test_User1'],
            content = {
                'title': 'Paper title',
                'abstract': 'This is an abstract',
                'authorids': ['test@mail.com', 'peter@mail.com', 'andrew@mail.com'],
                'authors': ['Test User', 'Peter User', 'Andrew Mc'],
                'archival_status': 'Archival',
                'subject_areas': [
                    'Databases',
                    'Information Integration',
                    'Knowledge Representation',
                    'Semantic Web'
                ]
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
        request_page(selenium, "http://localhost:3000/group?id=AKBC.ws/2019/Conference", peter_client.token)
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

        request_page(selenium, "http://localhost:3000/group?id=AKBC.ws/2019/Conference/Authors", peter_client.token)
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
        builder.set_conference_short_name('AKBC 2019')
        builder.set_double_blind(True)
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

        messages = client.get_messages(to = 'mbok@mail.com', subject = 'AKBC.ws/2019/Conference: Invitation to Review')
        assert messages
        assert len(messages) == 1

        text = messages[0]['content']['text']
        assert 'You have been nominated by the program chair committee of AKBC 2019' in text

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
        messages = client.get_messages(to = 'mbok@mail.com', subject = 'AKBC.ws/2019/Conference: Invitation to Review')
        assert messages
        assert len(messages) == 1

        # Remind reviewers
        invited = result = conference.recruit_reviewers(emails = ['another@mail.com'], remind = True)
        assert invited
        assert len(invited.members) == 5

        group = client.get_group('AKBC.ws/2019/Conference/Reviewers')
        assert group
        assert len(group.members) == 0

        group = client.get_group('AKBC.ws/2019/Conference/Reviewers/Declined')
        assert group
        assert len(group.members) == 1
        assert 'mbok@mail.com' in group.members

        messages = client.get_messages(subject = 'Reminder: AKBC.ws/2019/Conference: Invitation to Review')
        assert messages
        assert len(messages) == 3
        tos = [ m['content']['to'] for m in messages]
        assert 'michael@mail.com' in tos
        assert 'mohit@mail.com' in tos
        assert 'other@mail.com' in tos

    def test_set_program_chairs(self, client, selenium, request_page):

        builder = openreview.conference.ConferenceBuilder(client)
        assert builder, 'builder is None'

        builder.set_conference_id('AKBC.ws/2019/Conference')
        builder.set_double_blind(True)
        builder.has_area_chairs(True)
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
        assert len(group.members) == 5

        group = pc_client.get_group(id = 'AKBC.ws/2019/Conference/Reviewers/Declined')
        assert group
        assert len(group.members) == 1

        request_page(selenium, "http://localhost:3000/group?id=AKBC.ws/2019/Conference/Program_Chairs", client.token)
        assert selenium.find_element_by_link_text('Paper Status')
        assert selenium.find_element_by_link_text('Area Chair Status')
        assert selenium.find_element_by_link_text('Reviewer Status')

    def test_close_submission(self, client, test_client, selenium, request_page):

        builder = openreview.conference.ConferenceBuilder(client)
        assert builder, 'builder is None'

        builder.set_conference_id('AKBC.ws/2019/Conference')
        builder.set_double_blind(True)
        conference = builder.get_result()

        notes = test_client.get_notes(invitation='AKBC.ws/2019/Conference/-/Submission')
        submission = notes[0]
        submission.content['title'] = 'New paper title'
        test_client.post_note(submission)

        notes = test_client.get_notes(invitation='AKBC.ws/2019/Conference/-/Submission')
        assert 'New paper title' == notes[0].content['title']
        assert '~Test_User1' in notes[0].writers
        assert 'peter@mail.com' in notes[0].writers
        assert 'andrew@mail.com' in notes[0].writers

        request_page(selenium, "http://localhost:3000/forum?id=" + submission.id, test_client.token)

        assert len(selenium.find_elements_by_class_name('edit_button')) == 1
        assert len(selenium.find_elements_by_class_name('trash_button')) == 1

        conference.close_submissions()
        notes = test_client.get_notes(invitation='AKBC.ws/2019/Conference/-/Submission')
        submission = notes[0]
        assert [conference.id, '~Test_User1', 'peter@mail.com', 'andrew@mail.com'] == submission.writers

        request_page(selenium, "http://localhost:3000/forum?id=" + submission.id, test_client.token)

        assert len(selenium.find_elements_by_class_name('edit_button')) == 0
        assert len(selenium.find_elements_by_class_name('trash_button')) == 0

    def test_create_blind_submissions(self, client):

        builder = openreview.conference.ConferenceBuilder(client)
        assert builder, 'builder is None'

        builder.set_conference_id('AKBC.ws/2019/Conference')
        builder.set_submission_public(False)
        builder.has_area_chairs(True)
        conference = builder.get_result()

        with pytest.raises(openreview.OpenReviewException, match=r'Conference is not double blind'):
            conference.create_blind_submissions()

        builder.set_double_blind(True)
        conference = builder.get_result()

        blind_submissions = conference.create_blind_submissions()
        assert blind_submissions
        assert len(blind_submissions) == 1

        blind_submissions_2 = conference.create_blind_submissions()
        assert blind_submissions_2
        assert len(blind_submissions_2) == 1
        assert blind_submissions[0].id == blind_submissions_2[0].id
        assert blind_submissions_2[0].readers == ['AKBC.ws/2019/Conference/Program_Chairs',
         'AKBC.ws/2019/Conference/Area_Chairs',
         'AKBC.ws/2019/Conference/Reviewers',
         'AKBC.ws/2019/Conference/Paper1/Authors']

        builder.set_submission_public(True)
        conference = builder.get_result()
        blind_submissions_3 = conference.create_blind_submissions()
        assert blind_submissions_3
        assert len(blind_submissions_3) == 1
        assert blind_submissions[0].id == blind_submissions_3[0].id
        assert blind_submissions_3[0].readers == ['everyone']

    def test_open_comments(self, client, test_client, selenium, request_page):

        builder = openreview.conference.ConferenceBuilder(client)
        assert builder, 'builder is None'

        builder.set_conference_id('AKBC.ws/2019/Conference')
        builder.set_double_blind(True)
        conference = builder.get_result()
        conference.set_authors()

        conference.open_comments('Official_Comment', public = False, anonymous = True)

        notes = test_client.get_notes(invitation='AKBC.ws/2019/Conference/-/Blind_Submission')
        submission = notes[0]
        request_page(selenium, "http://localhost:3000/forum?id=" + submission.id, test_client.token)

        reply_row = selenium.find_element_by_class_name('reply_row')
        assert len(reply_row.find_elements_by_class_name('btn')) == 1
        assert 'Official Comment' == reply_row.find_elements_by_class_name('btn')[0].text

    def test_close_comments(self, client, test_client, selenium, request_page):

        builder = openreview.conference.ConferenceBuilder(client)
        assert builder, 'builder is None'

        builder.set_conference_id('AKBC.ws/2019/Conference')
        builder.set_double_blind(True)
        conference = builder.get_result()

        conference.close_comments('Official_Comment')

        notes = test_client.get_notes(invitation='AKBC.ws/2019/Conference/-/Submission')
        submission = notes[0]
        request_page(selenium, "http://localhost:3000/forum?id=" + submission.id, test_client.token)

        reply_row = selenium.find_element_by_class_name('reply_row')
        assert len(reply_row.find_elements_by_class_name('btn')) == 0

    def test_open_bids(self, client, test_client, selenium, request_page):

        reviewer_client = openreview.Client(baseurl = 'http://localhost:3000')
        assert reviewer_client is not None, "Client is none"
        res = reviewer_client.register_user(email = 'reviewer2@mail.com', first = 'Reviewer', last = 'DoubleBlind', password = '1234')
        assert res, "Res i none"
        res = reviewer_client.activate_user('reviewer2@mail.com', {
            'names': [
                    {
                        'first': 'Reviewer',
                        'last': 'DoubleBlind',
                        'username': '~Reviewer_DoubleBlind1'
                    }
                ],
            'emails': ['reviewer2@mail.com'],
            'preferredEmail': 'reviewer2@mail.com'
            })
        assert res, "Res i none"
        group = reviewer_client.get_group(id = 'reviewer2@mail.com')
        assert group
        assert group.members == ['~Reviewer_DoubleBlind1']

        builder = openreview.conference.ConferenceBuilder(client)
        assert builder, 'builder is None'

        builder.set_conference_id('AKBC.ws/2019/Conference')
        builder.set_double_blind(True)
        builder.has_area_chairs(True)
        conference = builder.get_result()
        conference.set_authors()
        conference.set_area_chairs(emails = ['ac@mail.com'])
        conference.set_reviewers(emails = ['reviewer2@mail.com'])
        now = datetime.datetime.utcnow()
        invitation = conference.open_bids(due_date =  now + datetime.timedelta(minutes = 10), request_count = 50, with_area_chairs = False)
        assert invitation

        request_page(selenium, "http://localhost:3000/invitation?id=AKBC.ws/2019/Conference/-/Bid", reviewer_client.token)
        tabs = selenium.find_element_by_class_name('tabs-container')
        assert tabs

    def test_open_reviews(self, client, test_client, selenium, request_page, helpers):

        now = datetime.datetime.utcnow()
        reviewer_client = openreview.Client(baseurl = 'http://localhost:3000', username='reviewer2@mail.com', password='1234')

        builder = openreview.conference.ConferenceBuilder(client)
        assert builder, 'builder is None'

        builder.set_conference_id('AKBC.ws/2019/Conference')
        builder.set_double_blind(True)
        builder.has_area_chairs(True)
        builder.set_conference_short_name('AKBC 2019')
        builder.set_review_stage(due_date = now + datetime.timedelta(minutes = 10), release_to_authors = True, release_to_reviewers = True)
        conference = builder.get_result()
        conference.set_authors()
        conference.set_area_chairs(emails = ['ac@mail.com'])
        conference.set_reviewers(emails = ['reviewer2@mail.com'])

        notes = test_client.get_notes(invitation='AKBC.ws/2019/Conference/-/Blind_Submission')
        submission = notes[0]

        conference.set_assignment('ac@mail.com', submission.number, is_area_chair = True)
        conference.set_assignment('reviewer2@mail.com', submission.number)

        # Reviewer
        request_page(selenium, "http://localhost:3000/forum?id=" + submission.id, reviewer_client.token)

        reply_row = selenium.find_element_by_class_name('reply_row')
        assert len(reply_row.find_elements_by_class_name('btn')) == 1
        assert 'Official Review' == reply_row.find_elements_by_class_name('btn')[0].text

        # Author
        request_page(selenium, "http://localhost:3000/forum?id=" + submission.id, test_client.token)

        reply_row = selenium.find_element_by_class_name('reply_row')
        assert len(reply_row.find_elements_by_class_name('btn')) == 0

        note = openreview.Note(invitation = 'AKBC.ws/2019/Conference/Paper1/-/Official_Review',
            forum = submission.id,
            replyto = submission.id,
            readers = ['AKBC.ws/2019/Conference/Program_Chairs',
            'AKBC.ws/2019/Conference/Paper1/Area_Chairs',
            'AKBC.ws/2019/Conference/Paper1/Reviewers',
            'AKBC.ws/2019/Conference/Paper1/Authors'],
            writers = ['AKBC.ws/2019/Conference/Paper1/AnonReviewer1'],
            signatures = ['AKBC.ws/2019/Conference/Paper1/AnonReviewer1'],
            content = {
                'title': 'Review title',
                'review': 'Paper is very good!',
                'rating': '9: Top 15% of accepted papers, strong accept',
                'confidence': '4: The reviewer is confident but not absolutely certain that the evaluation is correct'
            }
        )
        review_note = reviewer_client.post_note(note)
        assert review_note

        process_logs = client.get_process_logs(id = review_note.id)
        assert len(process_logs) == 1
        assert process_logs[0]['status'] == 'ok'

        messages = client.get_messages(subject = '[AKBC 2019] Review posted to your submission: "New paper title"')
        assert len(messages) == 3
        recipients = [m['content']['to'] for m in messages]
        assert 'test@mail.com' in recipients
        assert 'peter@mail.com' in recipients
        assert 'andrew@mail.com' in recipients

        messages = client.get_messages(subject = '[AKBC 2019] Review posted to your assigned paper: "New paper title"')
        assert len(messages) == 1
        recipients = [m['content']['to'] for m in messages]
        assert 'ac@mail.com' in recipients

        messages = client.get_messages(subject = '[AKBC 2019] Your review has been received on your assigned paper: "New paper title"')
        assert len(messages) == 1
        recipients = [m['content']['to'] for m in messages]
        assert 'reviewer2@mail.com' in recipients

        ## Check review visibility
        notes = reviewer_client.get_notes(invitation='AKBC.ws/2019/Conference/Paper1/-/Official_Review')
        assert len(notes) == 1

        notes = test_client.get_notes(invitation='AKBC.ws/2019/Conference/Paper1/-/Official_Review')
        assert len(notes) == 1

    def test_open_revise_reviews(self, client, test_client, selenium, request_page, helpers):

        now = datetime.datetime.utcnow()
        reviewer_client = openreview.Client(baseurl = 'http://localhost:3000', username='reviewer2@mail.com', password='1234')

        builder = openreview.conference.ConferenceBuilder(client)
        assert builder, 'builder is None'

        builder.set_conference_id('AKBC.ws/2019/Conference')
        builder.set_double_blind(True)
        builder.has_area_chairs(True)
        builder.set_conference_short_name('AKBC 2019')
        conference = builder.get_result()
        conference.set_authors()
        conference.set_area_chairs(emails = ['ac@mail.com'])
        conference.set_reviewers(emails = ['reviewer2@mail.com'])

        notes = test_client.get_notes(invitation='AKBC.ws/2019/Conference/-/Blind_Submission')
        submission = notes[0]

        reviews = test_client.get_notes(invitation='AKBC.ws/2019/Conference/Paper.*/-/Official_Review')
        assert reviews
        review = reviews[0]

        now = datetime.datetime.utcnow()
        conference.open_revise_reviews(due_date = now + datetime.timedelta(minutes = 100))

        note = openreview.Note(invitation = 'AKBC.ws/2019/Conference/Paper1/-/Official_Review/AnonReviewer1/Revision',
            forum = submission.id,
            referent = review.id,
            readers = ['AKBC.ws/2019/Conference/Program_Chairs',
            'AKBC.ws/2019/Conference/Paper1/Area_Chairs',
            'AKBC.ws/2019/Conference/Paper1/Reviewers',
            'AKBC.ws/2019/Conference/Paper1/Authors'],
            writers = ['AKBC.ws/2019/Conference/Paper1/AnonReviewer1'],
            signatures = ['AKBC.ws/2019/Conference/Paper1/AnonReviewer1'],
            content = {
                'title': 'UPDATED Review title',
                'review': 'Paper is very good!',
                'rating': '9: Top 15% of accepted papers, strong accept',
                'confidence': '4: The reviewer is confident but not absolutely certain that the evaluation is correct'
            }
        )
        review_note = reviewer_client.post_note(note)
        assert review_note

        process_logs = client.get_process_logs(id = review_note.id)
        assert len(process_logs) == 1
        assert process_logs[0]['status'] == 'ok'

        messages = client.get_messages(subject = '[AKBC 2019] Revised review posted to your submission: "New paper title"')
        assert len(messages) == 3
        recipients = [m['content']['to'] for m in messages]
        assert 'test@mail.com' in recipients
        assert 'peter@mail.com' in recipients
        assert 'andrew@mail.com' in recipients

        messages = client.get_messages(subject = '[AKBC 2019] Revised review posted to your assigned paper: "New paper title"')
        assert len(messages) == 2
        recipients = [m['content']['to'] for m in messages]
        assert 'ac@mail.com' in recipients
        assert 'reviewer2@mail.com' in recipients

    def test_open_meta_reviews(self, client, test_client, selenium, request_page):

        ac_client = openreview.Client(baseurl = 'http://localhost:3000')
        assert ac_client is not None, "Client is none"
        res = ac_client.register_user(email = 'ac@mail.com', first = 'AreaChair', last = 'DoubleBlind', password = '1234')
        assert res, "Res i none"
        res = ac_client.activate_user('ac@mail.com', {
            'names': [
                    {
                        'first': 'AreaChair',
                        'last': 'DoubleBlind',
                        'username': '~AreaChair_DoubleBlind1'
                    }
                ],
            'emails': ['ac@mail.com'],
            'preferredEmail': 'ac@mail.com'
            })
        assert res, "Res i none"
        group = ac_client.get_group(id = 'ac@mail.com')
        assert group
        assert group.members == ['~AreaChair_DoubleBlind1']

        builder = openreview.conference.ConferenceBuilder(client)
        assert builder, 'builder is None'

        builder.set_conference_id('AKBC.ws/2019/Conference')
        builder.set_double_blind(True)
        builder.has_area_chairs(True)
        builder.set_conference_short_name('AKBC 2019')
        conference = builder.get_result()

        conference.open_meta_reviews(due_date = datetime.datetime(2019, 10, 5, 18, 00))

        notes = test_client.get_notes(invitation='AKBC.ws/2019/Conference/-/Blind_Submission')
        submission = notes[0]

        note = openreview.Note(invitation = 'AKBC.ws/2019/Conference/Paper1/-/Meta_Review',
            forum = submission.id,
            replyto = submission.id,
            readers = ['AKBC.ws/2019/Conference/Paper1/Area_Chairs', 'AKBC.ws/2019/Conference/Program_Chairs'],
            writers = ['AKBC.ws/2019/Conference/Paper1/Area_Chair1'],
            signatures = ['AKBC.ws/2019/Conference/Paper1/Area_Chair1'],
            content = {
                'title': 'Meta review title',
                'metareview': 'Paper is very good!',
                'recommendation': 'Accept (Oral)',
                'confidence': '4: The area chair is confident but not absolutely certain'
            }
        )
        meta_review_note = ac_client.post_note(note)
        assert meta_review_note

    def test_open_meta_reviews_additional_options(self, client, test_client, selenium, request_page, helpers):

        ac_client = helpers.create_user('meta_additional@mail.com', 'TestMetaAdditional', 'User')
        assert ac_client is not None, "Client is none"

        builder = openreview.conference.ConferenceBuilder(client)
        assert builder, 'builder is None'

        builder.set_conference_id('AKBC.ws/2019/Conference')
        builder.set_double_blind(True)
        builder.has_area_chairs(True)
        builder.set_conference_short_name('AKBC 2019')
        conference = builder.get_result()

        conference.open_meta_reviews(due_date = datetime.datetime(2019, 10, 5, 18, 00), additional_fields = {
            'best paper' : {
                'description' : 'Nominate as best paper?',
                'value-radio' : ['Yes', 'No'],
                'required' : True
            }
        })

        notes = test_client.get_notes(invitation='AKBC.ws/2019/Conference/-/Blind_Submission')
        submission = notes[0]

        conference.set_assignment('meta_additional@mail.com', submission.number, is_area_chair = True)

        note = openreview.Note(invitation = 'AKBC.ws/2019/Conference/Paper1/-/Meta_Review',
            forum = submission.id,
            replyto = submission.id,
            readers = ['AKBC.ws/2019/Conference/Paper1/Area_Chairs', 'AKBC.ws/2019/Conference/Program_Chairs'],
            writers = ['AKBC.ws/2019/Conference/Paper1/Area_Chair2'],
            signatures = ['AKBC.ws/2019/Conference/Paper1/Area_Chair2'],
            content = {
                'title': 'Meta review title',
                'metareview': 'Excellent Paper!',
                'recommendation': 'Accept (Oral)',
                'confidence': '4: The area chair is confident but not absolutely certain'
            }
        )
        with pytest.raises(openreview.OpenReviewException, match=r'missing'):
            meta_review_note = ac_client.post_note(note)
        note.content['best paper'] = 'Yes'
        meta_review_note = ac_client.post_note(note)
        assert meta_review_note
        assert meta_review_note.content['best paper'] == 'Yes', 'Additional field not initialized'

    def test_open_decisions(self, client, helpers):

        builder = openreview.conference.ConferenceBuilder(client)
        assert builder, 'builder is None'

        builder.set_conference_id('AKBC.ws/2019/Conference')
        builder.set_double_blind(True)
        builder.set_conference_short_name('AKBC 2019')
        conference = builder.get_result()

        conference.set_program_chairs(emails = ['akbc_pc@mail.com'])
        conference.open_decisions()

        pc_client = helpers.create_user('akbc_pc@mail.com', 'AKBC', 'Pc')

        notes = pc_client.get_notes(invitation='AKBC.ws/2019/Conference/-/Blind_Submission')
        submission = notes[0]

        note = openreview.Note(invitation = 'AKBC.ws/2019/Conference/Paper1/-/Decision',
            forum = submission.id,
            replyto = submission.id,
            readers = ['AKBC.ws/2019/Conference/Program_Chairs'],
            nonreaders = ['AKBC.ws/2019/Conference/Paper' + str(submission.number) + '/Authors'],
            writers = ['AKBC.ws/2019/Conference/Program_Chairs'],
            signatures = ['AKBC.ws/2019/Conference/Program_Chairs'],
            content = {
                'title': 'Paper Decision',
                'decision': 'Accept (Oral)',
                'comment': 'Great!',
            }
        )

        meta_review_note = pc_client.post_note(note)
        assert meta_review_note

        conference.open_decisions(public=True)

        note = openreview.Note(invitation = 'AKBC.ws/2019/Conference/Paper1/-/Decision',
            forum = submission.id,
            replyto = submission.id,
            readers = ['everyone'],
            writers = ['AKBC.ws/2019/Conference/Program_Chairs'],
            signatures = ['AKBC.ws/2019/Conference/Program_Chairs'],
            content = {
                'title': 'Paper Decision',
                'decision': 'Accept (Oral)',
                'comment': 'Great!',
            }
        )

        meta_review_note = pc_client.post_note(note)
        assert meta_review_note

        conference.open_decisions(release_to_authors=True)

        note = openreview.Note(invitation = 'AKBC.ws/2019/Conference/Paper1/-/Decision',
            forum = submission.id,
            replyto = submission.id,
            readers = ['AKBC.ws/2019/Conference/Program_Chairs',
            'AKBC.ws/2019/Conference/Paper' + str(submission.number) + '/Authors'],
            writers = ['AKBC.ws/2019/Conference/Program_Chairs'],
            signatures = ['AKBC.ws/2019/Conference/Program_Chairs'],
            content = {
                'title': 'Paper Decision',
                'decision': 'Accept (Oral)',
                'comment': 'Great!',
            }
        )

        meta_review_note = pc_client.post_note(note)
        assert meta_review_note

    def test_consoles(self, client, test_client, selenium, request_page):

        builder = openreview.conference.ConferenceBuilder(client)
        assert builder, 'builder is None'

        builder.set_conference_id('AKBC.ws/2019/Conference')
        builder.set_double_blind(True)
        builder.set_conference_short_name('AKBC 2019')
        conference = builder.get_result()

        #Program chair user
        pc_client = openreview.Client(baseurl = 'http://localhost:3000', username='pc@mail.com', password='1234')


        request_page(selenium, "http://localhost:3000/group?id=AKBC.ws/2019/Conference", pc_client.token)
        notes_panel = selenium.find_element_by_id('notes')
        assert notes_panel
        tabs = notes_panel.find_element_by_class_name('tabs-container')
        assert tabs
        assert tabs.find_element_by_id('your-consoles')
        assert len(tabs.find_element_by_id('your-consoles').find_elements_by_tag_name('ul')) == 1
        console = tabs.find_element_by_id('your-consoles').find_elements_by_tag_name('ul')[0]
        assert 'Program Chair Console' == console.find_element_by_tag_name('a').text
