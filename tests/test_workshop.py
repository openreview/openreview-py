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

class TestWorkshop():

    def test_create_conference(self, client):

        builder = openreview.conference.ConferenceBuilder(client)
        assert builder, 'builder is None'

        builder.set_conference_id('icaps-conference.org/ICAPS/2019/Workshop/HSDIP')
        builder.set_conference_name('Heuristics and Search for Domain-independent Planning')
        builder.set_conference_short_name('ICAPS HSDIP 2019')
        builder.set_homepage_header({
        'title': 'Heuristics and Search for Domain-independent Planning',
        'subtitle': 'ICAPS 2019 Workshop',
        'deadline': 'Submission Deadline: March 17, 2019 midnight AoE',
        'date': 'July 11-15, 2019',
        'website': 'https://icaps19.icaps-conference.org/workshops/HSDIP/index.html',
        'location': 'Berkeley, CA, USA'
        })
        builder.set_double_blind(True)
        builder.set_submission_public(True)
        conference = builder.get_result()
        assert conference, 'conference is None'

        resp = requests.get('http://localhost:3000/groups?id=icaps-conference.org/ICAPS/2019/Workshop/HSDIP')
        assert resp.status_code == 200

    def test_enable_submissions(self, client, selenium, request_page):


        builder = openreview.conference.ConferenceBuilder(client)
        assert builder, 'builder is None'

        builder.set_conference_id('icaps-conference.org/ICAPS/2019/Workshop/HSDIP')
        builder.set_conference_name('Heuristics and Search for Domain-independent Planning')
        builder.set_conference_short_name('ICAPS HSDIP 2019')
        builder.set_homepage_header({
        'title': 'Heuristics and Search for Domain-independent Planning',
        'subtitle': 'ICAPS 2019 Workshop',
        'deadline': 'Submission Deadline: March 17, 2019 midnight AoE',
        'date': 'July 11-15, 2019',
        'website': 'https://icaps19.icaps-conference.org/workshops/HSDIP/index.html',
        'location': 'Berkeley, CA, USA'
        })
        builder.set_double_blind(True)
        builder.set_submission_public(True)
        conference = builder.get_result()

        now = datetime.datetime.utcnow()
        invitation = conference.open_submissions(due_date = now + datetime.timedelta(minutes = 10))
        assert invitation
        assert invitation.duedate == openreview.tools.datetime_millis(now + datetime.timedelta(minutes = 10))
        assert invitation.expdate == openreview.tools.datetime_millis(now + datetime.timedelta(minutes = 40))

        posted_invitation = client.get_invitation(id = 'icaps-conference.org/ICAPS/2019/Workshop/HSDIP/-/Submission')
        assert posted_invitation
        assert posted_invitation.duedate == openreview.tools.datetime_millis(now + datetime.timedelta(minutes = 10))
        assert posted_invitation.expdate == openreview.tools.datetime_millis(now + datetime.timedelta(minutes = 40))

        request_page(selenium, "http://localhost:3000/group?id=icaps-conference.org/ICAPS/2019/Workshop/HSDIP")

        assert "ICAPS 2019 Workshop HSDIP | OpenReview" in selenium.title
        header = selenium.find_element_by_id('header')
        assert header
        assert "Heuristics and Search for Domain-independent Planning" == header.find_element_by_tag_name("h1").text
        assert "ICAPS 2019 Workshop" == header.find_element_by_tag_name("h3").text
        assert "Berkeley, CA, USA" == header.find_element_by_xpath(".//span[@class='venue-location']").text
        assert "July 11-15, 2019" == header.find_element_by_xpath(".//span[@class='venue-date']").text
        assert "https://icaps19.icaps-conference.org/workshops/HSDIP/index" in header.find_element_by_xpath(".//span[@class='venue-website']/a").text
        invitation_panel = selenium.find_element_by_id('invitation')
        assert invitation_panel
        assert len(invitation_panel.find_elements_by_tag_name('div')) == 1
        assert 'ICAPS 2019 Workshop HSDIP Submission' == invitation_panel.find_element_by_class_name('btn').text
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

        builder.set_conference_id('icaps-conference.org/ICAPS/2019/Workshop/HSDIP')
        builder.set_conference_name('Heuristics and Search for Domain-independent Planning')
        builder.set_conference_short_name('ICAPS HSDIP 2019')
        builder.set_homepage_header({
        'title': 'Heuristics and Search for Domain-independent Planning',
        'subtitle': 'ICAPS 2019 Workshop',
        'deadline': 'Submission Deadline: March 17, 2019 midnight AoE',
        'date': 'July 11-15, 2019',
        'website': 'https://icaps19.icaps-conference.org/workshops/HSDIP/index.html',
        'location': 'Berkeley, CA, USA'
        })
        builder.set_double_blind(True)
        builder.set_submission_public(True)
        conference = builder.get_result()

        now = datetime.datetime.utcnow()
        invitation = conference.open_submissions(due_date = now + datetime.timedelta(minutes = 10))
        assert invitation        

        note = openreview.Note(invitation = invitation.id,
            readers = ['~Test_User1', 'peter@mail.com', 'andrew@mail.com', 'icaps-conference.org/ICAPS/2019/Workshop/HSDIP/Program_Chairs'],
            writers = ['~Test_User1', 'peter@mail.com', 'andrew@mail.com'],
            signatures = ['~Test_User1'],
            content = {
                'title': 'Paper title',
                'abstract': 'This is an abstract',
                'authorids': ['test@mail.com', 'peter@mail.com', 'andrew@mail.com'],
                'authors': ['Test User', 'Peter User', 'Andrew Mc']
            }
        )
        url = test_client.put_pdf(os.path.join(os.path.dirname(__file__), 'data/paper.pdf'))
        note.content['pdf'] = url
        test_client.post_note(note)

        # Author user
        request_page(selenium, "http://localhost:3000/group?id=icaps-conference.org/ICAPS/2019/Workshop/HSDIP", test_client.token)
        invitation_panel = selenium.find_element_by_id('invitation')
        assert invitation_panel
        assert len(invitation_panel.find_elements_by_tag_name('div')) == 1
        assert 'ICAPS 2019 Workshop HSDIP Submission' == invitation_panel.find_element_by_class_name('btn').text
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

        request_page(selenium, "http://localhost:3000/group?id=icaps-conference.org/ICAPS/2019/Workshop/HSDIP/Authors", test_client.token)
        tabs = selenium.find_element_by_class_name('tabs-container')
        assert tabs
        assert tabs.find_element_by_id('author-schedule')
        assert tabs.find_element_by_id('author-tasks')
        assert tabs.find_element_by_id('your-submissions')
        papers = tabs.find_element_by_id('your-submissions').find_element_by_class_name('submissions-list')
        assert len(papers.find_elements_by_class_name('note')) == 1

        # Guest user
        request_page(selenium, "http://localhost:3000/group?id=icaps-conference.org/ICAPS/2019/Workshop/HSDIP")
        invitation_panel = selenium.find_element_by_id('invitation')
        assert invitation_panel
        assert len(invitation_panel.find_elements_by_tag_name('div')) == 1
        assert 'ICAPS 2019 Workshop HSDIP Submission' == invitation_panel.find_element_by_class_name('btn').text
        notes_panel = selenium.find_element_by_id('notes')
        assert notes_panel
        tabs = notes_panel.find_element_by_class_name('tabs-container')
        assert tabs
        assert tabs.find_element_by_id('your-consoles')
        assert len(tabs.find_element_by_id('your-consoles').find_elements_by_tag_name('ul')) == 0
        assert tabs.find_element_by_id('recent-activity')
        assert len(tabs.find_element_by_id('recent-activity').find_elements_by_class_name('activity-list')) == 0

        # Co-author user
        request_page(selenium, "http://localhost:3000/group?id=icaps-conference.org/ICAPS/2019/Workshop/HSDIP", peter_client.token)
        invitation_panel = selenium.find_element_by_id('invitation')
        assert invitation_panel
        assert len(invitation_panel.find_elements_by_tag_name('div')) == 1
        assert 'ICAPS 2019 Workshop HSDIP Submission' == invitation_panel.find_element_by_class_name('btn').text
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

        request_page(selenium, "http://localhost:3000/group?id=icaps-conference.org/ICAPS/2019/Workshop/HSDIP/Authors", peter_client.token)
        tabs = selenium.find_element_by_class_name('tabs-container')
        assert tabs
        assert tabs.find_element_by_id('author-schedule')
        assert tabs.find_element_by_id('author-tasks')
        assert tabs.find_element_by_id('your-submissions')
        papers = tabs.find_element_by_id('your-submissions').find_element_by_class_name('submissions-list')
        assert len(papers.find_elements_by_class_name('note')) == 1


    def test_create_blind_submissions(self, client):

        builder = openreview.conference.ConferenceBuilder(client)
        assert builder, 'builder is None'

        builder.set_conference_id('icaps-conference.org/ICAPS/2019/Workshop/HSDIP')
        builder.set_conference_name('Heuristics and Search for Domain-independent Planning')
        builder.set_conference_short_name('ICAPS HSDIP 2019')
        builder.set_homepage_header({
        'title': 'Heuristics and Search for Domain-independent Planning',
        'subtitle': 'ICAPS 2019 Workshop',
        'deadline': 'Submission Deadline: March 17, 2019 midnight AoE',
        'date': 'July 11-15, 2019',
        'website': 'https://icaps19.icaps-conference.org/workshops/HSDIP/index.html',
        'location': 'Berkeley, CA, USA'
        })
        builder.set_double_blind(True)
        builder.set_submission_public(False)
        builder.has_area_chairs(False)
        conference = builder.get_result()

        blind_submissions = conference.create_blind_submissions()
        assert blind_submissions
        assert len(blind_submissions) == 1

        blind_submissions_2 = conference.create_blind_submissions()
        assert blind_submissions_2
        assert len(blind_submissions_2) == 1
        assert blind_submissions[0].id == blind_submissions_2[0].id
        assert blind_submissions_2[0].readers == ['icaps-conference.org/ICAPS/2019/Workshop/HSDIP/Program_Chairs',
         'icaps-conference.org/ICAPS/2019/Workshop/HSDIP/Reviewers', 
         'icaps-conference.org/ICAPS/2019/Workshop/HSDIP/Paper1/Authors']

        builder.set_submission_public(True)
        conference = builder.get_result()
        blind_submissions_3 = conference.create_blind_submissions()
        assert blind_submissions_3
        assert len(blind_submissions_3) == 1
        assert blind_submissions[0].id == blind_submissions_3[0].id
        assert blind_submissions_3[0].readers == ['everyone']       


    def test_open_reviews(self, client, test_client, selenium, request_page, helpers):

        builder = openreview.conference.ConferenceBuilder(client)
        assert builder, 'builder is None'

        builder.set_conference_id('icaps-conference.org/ICAPS/2019/Workshop/HSDIP')
        builder.set_conference_name('Heuristics and Search for Domain-independent Planning')
        builder.set_conference_short_name('ICAPS HSDIP 2019')
        builder.set_homepage_header({
        'title': 'Heuristics and Search for Domain-independent Planning',
        'subtitle': 'ICAPS 2019 Workshop',
        'deadline': 'Submission Deadline: March 17, 2019 midnight AoE',
        'date': 'July 11-15, 2019',
        'website': 'https://icaps19.icaps-conference.org/workshops/HSDIP/index.html',
        'location': 'Berkeley, CA, USA'
        })
        builder.set_double_blind(True)
        builder.set_submission_public(False)
        builder.has_area_chairs(False)
        conference = builder.get_result()
        conference.set_authors()
        conference.set_reviewers(emails = ['reviewer3@mail.com'])

        notes = test_client.get_notes(invitation='icaps-conference.org/ICAPS/2019/Workshop/HSDIP/-/Blind_Submission')
        submission = notes[0]

        conference.set_assignment('reviewer3@mail.com', submission.number)
        conference.open_reviews('Official_Review', due_date = datetime.datetime(2019, 10, 5, 18, 00))

        # Reviewer
        reviewer_client = helpers.create_user('reviewer3@mail.com', 'Reviewer', 'Three')
        request_page(selenium, "http://localhost:3000/forum?id=" + submission.id, reviewer_client.token)

        reply_row = selenium.find_element_by_class_name('reply_row')
        assert len(reply_row.find_elements_by_class_name('btn')) == 1
        assert 'Official Review' == reply_row.find_elements_by_class_name('btn')[0].text

        # Author
        request_page(selenium, "http://localhost:3000/forum?id=" + submission.id, test_client.token)

        reply_row = selenium.find_element_by_class_name('reply_row')
        assert len(reply_row.find_elements_by_class_name('btn')) == 0

        note = openreview.Note(invitation = 'icaps-conference.org/ICAPS/2019/Workshop/HSDIP/-/Paper1/Official_Review',
            forum = submission.id,
            replyto = submission.id,
            readers = ['icaps-conference.org/ICAPS/2019/Workshop/HSDIP/Program_Chairs', 
            'icaps-conference.org/ICAPS/2019/Workshop/HSDIP/Paper1/Reviewers/Submitted'],
            nonreaders = ['icaps-conference.org/ICAPS/2019/Workshop/HSDIP/Paper1/Authors'],
            writers = ['icaps-conference.org/ICAPS/2019/Workshop/HSDIP/Paper1/AnonReviewer1'],
            signatures = ['icaps-conference.org/ICAPS/2019/Workshop/HSDIP/Paper1/AnonReviewer1'],
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

        messages = client.get_messages(subject = '[ICAPS HSDIP 2019] Review posted to your submission: "New paper title"')
        assert len(messages) == 0
 
        messages = client.get_messages(subject = '[ICAPS HSDIP 2019] Review posted to your assigned paper: "New paper title"')
        assert len(messages) == 0
 
        ## Check review visibility
        notes = reviewer_client.get_notes(invitation='icaps-conference.org/ICAPS/2019/Workshop/HSDIP/-/Paper1/Official_Review')
        assert len(notes) == 1

        notes = test_client.get_notes(invitation='icaps-conference.org/ICAPS/2019/Workshop/HSDIP/-/Paper1/Official_Review')
        assert len(notes) == 0      

