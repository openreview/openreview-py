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
from selenium.common.exceptions import NoSuchElementException

class TestReviewersConference():

    def test_set_reviewers_name(self, client, test_client, selenium, request_page):

        builder = openreview.conference.ConferenceBuilder(client)
        assert builder, 'builder is None'

        builder.set_conference_id('learningtheory.org/COLT/2019/Conference')
        builder.set_conference_name('Computational Learning Theory')
        builder.set_conference_short_name('COLT 2019')
        builder.set_homepage_header({
        'title': 'COLT 2019',
        'subtitle': 'Computational Learning Theory',
        'deadline': 'Submission Deadline: 11:00pm Pacific Standard Time, February 1, 2019',
        'date': 'June 25 - June 28, 2019',
        'website': 'http://learningtheory.org/colt2019/',
        'location': 'Phoenix, Arizona, United States'
        })
        builder.set_conference_reviewers_name('Program_Committee')
        conference = builder.get_result()
        assert conference

        conference.set_reviewers(emails=['test@mail.com'])

        # Reviewer user
        request_page(selenium, "http://localhost:3000/group?id=learningtheory.org/COLT/2019/Conference", test_client.token)
        invitation_panel = selenium.find_element_by_id('invitation')
        assert invitation_panel
        assert len(invitation_panel.find_elements_by_tag_name('div')) == 0
        notes_panel = selenium.find_element_by_id('notes')
        assert notes_panel
        tabs = notes_panel.find_element_by_class_name('tabs-container')
        assert tabs
        assert tabs.find_element_by_id('your-consoles')
        assert len(tabs.find_element_by_id('your-consoles').find_elements_by_tag_name('ul')) == 1
        console = tabs.find_element_by_id('your-consoles').find_elements_by_tag_name('ul')[0]
        assert 'Program Committee Console' == console.find_element_by_tag_name('a').text
        assert tabs.find_element_by_id('recent-activity')
        assert len(tabs.find_element_by_id('recent-activity').find_elements_by_class_name('activity-list')) == 0

        # Guest user
        request_page(selenium, "http://localhost:3000/group?id=learningtheory.org/COLT/2019/Conference")
        invitation_panel = selenium.find_element_by_id('invitation')
        assert invitation_panel
        assert len(invitation_panel.find_elements_by_tag_name('div')) == 0
        notes_panel = selenium.find_element_by_id('notes')
        assert notes_panel
        tabs = notes_panel.find_element_by_class_name('tabs-container')
        assert tabs
        assert tabs.find_element_by_id('your-consoles')
        assert len(tabs.find_element_by_id('your-consoles').find_elements_by_tag_name('ul')) == 0
        assert tabs.find_element_by_id('recent-activity')
        assert len(tabs.find_element_by_id('recent-activity').find_elements_by_class_name('activity-list')) == 0

        # Reviewer console
        request_page(selenium, "http://localhost:3000/group?id=learningtheory.org/COLT/2019/Conference/Program_Committee", test_client.token)
        tabs = selenium.find_element_by_class_name('tabs-container')
        assert tabs
        assert tabs.find_element_by_id('reviewer-schedule')


    def test_allow_review_de_anonymization(self, client, test_client, helpers, selenium, request_page):

        builder = openreview.conference.ConferenceBuilder(client)

        builder.set_conference_id('eswc-conferences.org/ESWC/2019/Workshop/KGB')
        builder.set_conference_name('Knowledge Graph Building Workshop')
        builder.set_conference_short_name('KGB 2019')
        builder.set_homepage_header({
        'title': 'Knowledge Graph Building Workshop',
        'subtitle': 'Co-located with the Extended Semantic Web Conference 2019',
        'deadline': 'Submission Deadline: 11th of March, 2019, 23:59 Hawaii time',
        'date': '3 June 2019',
        'website': 'http://kgb-workshop.org/',
        'location': 'Portoroz, Slovenia',
        'instructions': ' '
        })
        builder.set_conference_submission_name('Submission')
        builder.set_submission_public(True)
        builder.set_override_homepage(True)
        conference = builder.get_result()

        now = datetime.datetime.utcnow()
        invitation = conference.open_submissions(due_date = now + datetime.timedelta(minutes = 10))

        note = openreview.Note(invitation = invitation.id,
            readers = ['everyone'],
            writers = ['~Test_User1', 'author@mail.com', 'author2@mail.com'],
            signatures = ['~Test_User1'],
            content = {
                'title': 'Paper title',
                'abstract': 'This is an abstract',
                'authorids': ['test@mail.com', 'author@mail.com', 'author2@mail.com'],
                'authors': ['Test User', 'Melisa Bok', 'Andrew Mc'],
                'pdf': '/pdf/sdfskdls.pdf'
            }
        )

        note = test_client.post_note(note)
        assert note

        conference.set_authors()
        conference.set_reviewers(['reviewer_kgb@mail.com', 'reviewer_kgb2@mail.com'])
        conference.set_program_chairs([])
        conference.set_assignment(number = 1, user = 'reviewer_kgb@mail.com')
        conference.set_assignment(number = 1, user = 'reviewer_kgb2@mail.com')

        invitations = conference.open_reviews(due_date = now + datetime.timedelta(minutes = 10), allow_de_anonymization = True)
        assert invitations

        request_page(selenium, "http://localhost:3000/group?id=eswc-conferences.org/ESWC/2019/Workshop/KGB/Program_Chairs", client.token)
        reviews = selenium.find_elements_by_class_name('reviewer-progress')
        assert reviews
        assert len(reviews) == 5
        headers = reviews[0].find_elements_by_tag_name('h4')
        assert headers
        assert headers[0].text == '0 of 2 Reviews Submitted'

        note = openreview.Note(invitation = 'eswc-conferences.org/ESWC/2019/Workshop/KGB/-/Paper1/Official_Review',
            forum = note.id,
            replyto = note.id,
            readers = ['eswc-conferences.org/ESWC/2019/Workshop/KGB/Program_Chairs', 'eswc-conferences.org/ESWC/2019/Workshop/KGB/Paper1/Reviewers/Submitted'],
            nonreaders = ['eswc-conferences.org/ESWC/2019/Workshop/KGB/Paper1/Authors'],
            writers = ['~Reviewer_KGBTwo1'],
            signatures = ['~Reviewer_KGBTwo1'],
            content = {
                'title': 'Review title',
                'review': 'Paper is very good!',
                'rating': '2: Strong rejection',
                'confidence': '4: The reviewer is confident but not absolutely certain that the evaluation is correct'
            }
        )
        reviewer_client = helpers.create_user('reviewer_kgb2@mail.com', 'Reviewer', 'KGBTwo')
        review_note = reviewer_client.post_note(note)
        assert review_note

        request_page(selenium, "http://localhost:3000/group?id=eswc-conferences.org/ESWC/2019/Workshop/KGB/Program_Chairs", client.token)
        reviews = selenium.find_elements_by_class_name('reviewer-progress')
        assert reviews
        assert len(reviews) == 5
        headers = reviews[0].find_elements_by_tag_name('h4')
        assert headers
        assert headers[0].text == '1 of 2 Reviews Submitted'

        assert selenium.find_element_by_link_text('Paper Status')
        try:
            selenium.find_element_by_link_text('Area Chair Status')
        except NoSuchElementException as e:
            assert e

        assert selenium.find_element_by_link_text('Reviewer Status')



