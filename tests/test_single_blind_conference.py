from __future__ import absolute_import, division, print_function, unicode_literals
import openreview
import pytest
import requests
import datetime
import os

class TestSingleBlindConference():

    def test_create_single_blind_conference(self, client, selenium, request_page) :

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

        request_page(selenium, "http://localhost:3000/group?id=NIPS.cc/2018/Workshop/MLITS")

        assert "NIPS 2018 Workshop MLITS | OpenReview" in selenium.title
        header = selenium.find_element_by_id('header')
        assert header
        assert "2018 NIPS MLITS Workshop" == header.find_element_by_tag_name("h1").text
        assert "Machine Learning for Intelligent Transportation Systems" == header.find_element_by_tag_name("h3").text
        assert "Montreal, Canada" == header.find_element_by_xpath(".//span[@class='venue-location']").text
        assert "December 3-8, 2018" == header.find_element_by_xpath(".//span[@class='venue-date']").text
        assert "https://sites.google.com/site/nips2018mlits/home" == header.find_element_by_xpath(".//span[@class='venue-website']/a").text
        invitation_panel = selenium.find_element_by_id('invitation')
        assert invitation_panel
        assert len(invitation_panel.find_elements_by_tag_name('div')) == 0
        notes_panel = selenium.find_element_by_id('notes')
        assert notes_panel

    def test_enable_submissions(self, client, selenium, request_page):


        builder = openreview.conference.ConferenceBuilder(client)
        assert builder, 'builder is None'

        builder.set_conference_id('NIPS.cc/2018/Workshop/MLITS')
        conference = builder.get_result()
        assert conference, 'conference is None'

        invitation = conference.open_submissions(due_date = datetime.datetime(2019, 10, 5, 18, 00), public = True)
        assert invitation
        assert invitation.duedate == 1570298400000

        posted_invitation = client.get_invitation(id = 'NIPS.cc/2018/Workshop/MLITS/-/Submission')
        assert posted_invitation
        assert posted_invitation.duedate == 1570298400000

        request_page(selenium, "http://localhost:3000/group?id=NIPS.cc/2018/Workshop/MLITS")

        assert "NIPS 2018 Workshop MLITS | OpenReview" in selenium.title
        invitation_panel = selenium.find_element_by_id('invitation')
        assert invitation_panel
        assert len(invitation_panel.find_elements_by_tag_name('div')) == 1
        assert 'NIPS 2018 Workshop MLITS Submission' == invitation_panel.find_element_by_class_name('btn').text
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

        builder.set_conference_id('NIPS.cc/2018/Workshop/MLITS')
        conference = builder.get_result()
        invitation = conference.open_submissions(due_date = datetime.datetime(2019, 10, 5, 18, 00), public = True)

        note = openreview.Note(invitation = invitation.id,
            readers = ['everyone'],
            writers = ['~Test_User1', 'peter@mail.com', 'andrew@mail.com'],
            signatures = ['~Test_User1'],
            content = {
                'title': 'Paper title',
                'abstract': 'This is an abstract',
                'authorids': ['test@mail.com', 'peter@mail.com', 'andrew@mail.com'],
                'authors': ['Test User', 'Peter Test', 'Andrew Mc']
            }
        )
        url = test_client.put_pdf(os.path.join(os.path.dirname(__file__), 'data/paper.pdf'))
        note.content['pdf'] = url
        test_client.post_note(note)

        # Author user
        request_page(selenium, "http://localhost:3000/group?id=NIPS.cc/2018/Workshop/MLITS", test_client.token)
        invitation_panel = selenium.find_element_by_id('invitation')
        assert invitation_panel
        assert len(invitation_panel.find_elements_by_tag_name('div')) == 1
        assert 'NIPS 2018 Workshop MLITS Submission' == invitation_panel.find_element_by_class_name('btn').text
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
        allsubmissions_tab = tabs.find_element_by_id('all-submissions')
        assert allsubmissions_tab
        assert len(allsubmissions_tab.find_element_by_class_name('submissions-list').find_elements_by_tag_name('li')) == 2

        request_page(selenium, "http://localhost:3000/group?id=NIPS.cc/2018/Workshop/MLITS/Authors", test_client.token)
        tabs = selenium.find_element_by_class_name('tabs-container')
        assert tabs
        assert tabs.find_element_by_id('author-schedule')
        assert tabs.find_element_by_id('author-tasks')
        assert tabs.find_element_by_id('your-submissions')
        papers = tabs.find_element_by_id('your-submissions').find_element_by_class_name('submissions-list')
        assert len(papers.find_elements_by_class_name('note')) == 1

        # Guest user
        request_page(selenium, "http://localhost:3000/group?id=NIPS.cc/2018/Workshop/MLITS")
        invitation_panel = selenium.find_element_by_id('invitation')
        assert invitation_panel
        assert len(invitation_panel.find_elements_by_tag_name('div')) == 1
        assert 'NIPS 2018 Workshop MLITS Submission' == invitation_panel.find_element_by_class_name('btn').text
        notes_panel = selenium.find_element_by_id('notes')
        assert notes_panel
        tabs = notes_panel.find_element_by_class_name('tabs-container')
        assert tabs
        assert tabs.find_element_by_id('your-consoles')
        assert len(tabs.find_element_by_id('your-consoles').find_elements_by_tag_name('ul')) == 0
        assert tabs.find_element_by_id('recent-activity')
        assert len(tabs.find_element_by_id('recent-activity').find_elements_by_class_name('activity-list')) == 0
        allsubmissions_tab = tabs.find_element_by_id('all-submissions')
        assert allsubmissions_tab
        assert len(allsubmissions_tab.find_element_by_class_name('submissions-list').find_elements_by_tag_name('li')) == 2

        # Co-author user
        request_page(selenium, "http://localhost:3000/group?id=NIPS.cc/2018/Workshop/MLITS", peter_client.token)
        invitation_panel = selenium.find_element_by_id('invitation')
        assert invitation_panel
        assert len(invitation_panel.find_elements_by_tag_name('div')) == 1
        assert 'NIPS 2018 Workshop MLITS Submission' == invitation_panel.find_element_by_class_name('btn').text
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
        allsubmissions_tab = tabs.find_element_by_id('all-submissions')
        assert allsubmissions_tab
        assert len(allsubmissions_tab.find_element_by_class_name('submissions-list').find_elements_by_tag_name('li')) == 2

        request_page(selenium, "http://localhost:3000/group?id=NIPS.cc/2018/Workshop/MLITS/Authors", peter_client.token)
        tabs = selenium.find_element_by_class_name('tabs-container')
        assert tabs
        assert tabs.find_element_by_id('author-schedule')
        assert tabs.find_element_by_id('author-tasks')
        assert tabs.find_element_by_id('your-submissions')
        papers = tabs.find_element_by_id('your-submissions').find_element_by_class_name('submissions-list')
        assert len(papers.find_elements_by_class_name('note')) == 1
