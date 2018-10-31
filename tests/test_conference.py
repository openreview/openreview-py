from __future__ import absolute_import, division, print_function, unicode_literals
import openreview
import pytest
import requests
import datetime

class TestConference():

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



    def test_enable_submissions(self, client):


        builder = openreview.conference.ConferenceBuilder(client)
        assert builder, 'builder is None'

        builder.set_conference_id('AKBC.ws/2019/Conference')
        conference = builder.get_result()
        invitation = conference.open_submissions(mode = 'blind', due_date = datetime.datetime(2019, 10, 5, 18, 00), subject_areas = [])
        assert invitation
        assert invitation.duedate == 1570298400000

        posted_invitation = client.get_invitation(id = 'AKBC.ws/2019/Conference/-/Submission')
        assert posted_invitation
        assert posted_invitation.duedate == 1570298400000

        #Test the submission paper


    def test_recruit_reviewers(self, client):

        builder = openreview.conference.ConferenceBuilder(client)
        assert builder, 'builder is None'

        builder.set_conference_id('AKBC.ws/2019/Conference')
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

    def test_create_single_blind_conference(self, client):

        builder = openreview.conference.ConferenceBuilder(client)
        assert builder, 'builder is None'

        builder.set_conference_id('NIPS.cc/2018/Workshop/MLITS')
        builder.set_conference_name('2018 NIPS MLITS Workshop')
        builder.set_homepage_header({
        'title': '2018 NIPS MLITS Workshop',
        'subtitle': 'Machine Learning for Intelligent Transportation Systems',
        'deadline': 'October 12, 2018, 11:59 pm UTC',
        'date': 'December 3-8, 2018',
        'website': 'https://sites.google.com/site/nips2018mlits/home',
        'location': 'Montreal, Canada',
        'instructions': ''
        })
        builder.set_conference_type(openreview.builder.SingleBlindConferenceType)

        conference = builder.get_result()
        assert conference, 'conference is None'

        groups = conference.get_conference_groups()
        assert groups
        assert groups[0].id == 'NIPS.cc'
        assert groups[0].readers == ['everyone']
        assert groups[0].nonreaders == []
        assert groups[0].writers == ['NIPS.cc']
        assert groups[0].signatures == ['~Super_User1']
        assert groups[0].signatories == ['NIPS.cc']
        assert groups[0].members == []
        assert groups[1].id == 'NIPS.cc/2018'
        assert groups[1].readers == ['everyone']
        assert groups[1].nonreaders == []
        assert groups[1].writers == ['NIPS.cc/2018']
        assert groups[1].signatures == ['~Super_User1']
        assert groups[1].signatories == ['NIPS.cc/2018']
        assert groups[1].members == []
        assert groups[2].id == 'NIPS.cc/2018/Workshop'
        assert groups[2].readers == ['everyone']
        assert groups[2].nonreaders == []
        assert groups[2].writers == ['NIPS.cc/2018/Workshop']
        assert groups[2].signatures == ['~Super_User1']
        assert groups[2].signatories == ['NIPS.cc/2018/Workshop']
        assert groups[2].members == []
        assert groups[3].id == 'NIPS.cc/2018/Workshop/MLITS'
        assert groups[3].readers == ['everyone']
        assert groups[3].nonreaders == []
        assert groups[3].writers == ['NIPS.cc/2018/Workshop/MLITS']
        assert groups[3].signatures == ['~Super_User1']
        assert groups[3].signatories == ['NIPS.cc/2018/Workshop/MLITS']
        assert groups[3].members == []
        assert '"title": "2018 NIPS MLITS Workshop"' in groups[3].web
        assert '"subtitle": "Machine Learning for Intelligent Transportation Systems"' in groups[3].web
        assert '"location": "Montreal, Canada"' in groups[3].web
        assert '"date": "December 3-8, 2018"' in groups[3].web
        assert '"website": "https://sites.google.com/site/nips2018mlits/home"' in groups[3].web
        assert '"deadline": "October 12, 2018, 11:59 pm UTC"' in groups[3].web
        assert 'BLIND_SUBMISSION_ID' not in groups[3].web
