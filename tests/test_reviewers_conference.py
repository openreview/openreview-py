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

        builder = openreview.conference.ConferenceBuilder(client, support_user='openreview.net/Support')
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
        request_page(selenium, "http://localhost:3030/group?id=learningtheory.org/COLT/2019/Conference", test_client.token, wait_for_element='invitation')
        invitation_panel = selenium.find_element(By.ID, 'invitation')
        assert invitation_panel
        assert len(invitation_panel.find_elements(By.TAG_NAME, 'div')) == 0
        notes_panel = selenium.find_element(By.ID, 'notes')
        assert notes_panel
        tabs = notes_panel.find_element(By.CLASS_NAME, 'tabs-container')
        assert tabs
        assert tabs.find_element(By.ID, 'your-consoles')
        assert len(tabs.find_element(By.ID, 'your-consoles').find_elements(By.TAG_NAME, 'ul')) == 1
        console = tabs.find_element(By.ID, 'your-consoles').find_elements(By.TAG_NAME, 'ul')[0]
        assert 'Program Committee Console' == console.find_element(By.TAG_NAME, 'a').text
        assert tabs.find_elements(By.ID, 'recent-activity')
        assert len(tabs.find_element(By.ID, 'recent-activity').find_elements(By.CLASS_NAME, 'activity-list')) == 0

        # Guest user
        request_page(selenium, "http://localhost:3030/group?id=learningtheory.org/COLT/2019/Conference", wait_for_element='invitation')
        invitation_panel = selenium.find_element(By.ID, 'invitation')
        assert invitation_panel
        assert len(invitation_panel.find_elements(By.TAG_NAME, 'div')) == 0
        notes_panel = selenium.find_element(By.ID, 'notes')
        assert notes_panel
        tabs = notes_panel.find_element(By.CLASS_NAME, 'tabs-container')
        assert tabs
        assert tabs.find_element(By.ID, 'your-consoles')
        assert len(tabs.find_element(By.ID, 'your-consoles').find_elements(By.TAG_NAME, 'ul')) == 0
        assert tabs.find_element(By.ID, 'recent-activity')
        assert len(tabs.find_element(By.ID, 'recent-activity').find_elements(By.CLASS_NAME, 'activity-list')) == 0

        # Reviewer console
        request_page(selenium, "http://localhost:3030/group?id=learningtheory.org/COLT/2019/Conference/Program_Committee", test_client.token, by=By.CLASS_NAME, wait_for_element='tabs-container')
        tabs = selenium.find_element(By.CLASS_NAME, 'tabs-container')
        assert tabs

    def test_allow_review_de_anonymization(self, client, test_client, helpers, selenium, request_page):

        builder = openreview.conference.ConferenceBuilder(client, support_user='openreview.net/Support')

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
        now = datetime.datetime.utcnow()
        builder.set_submission_stage(due_date = now + datetime.timedelta(minutes = 40), public=True, withdrawn_submission_reveal_authors=True, desk_rejected_submission_reveal_authors=True)
        builder.set_review_stage(openreview.stages.ReviewStage(due_date = now + datetime.timedelta(minutes = 10), allow_de_anonymization = True, release_to_reviewers=openreview.stages.ReviewStage.Readers.REVIEWERS_SUBMITTED))
        conference = builder.get_result()
        conference.create_review_stage()

        note = openreview.Note(invitation = conference.get_submission_id(),
            readers = [conference.id, '~SomeFirstName_User1', 'author@mail.com', 'author2@mail.com'],
            writers = [conference.id, '~SomeFirstName_User1', 'author@mail.com', 'author2@mail.com'],
            signatures = ['~SomeFirstName_User1'],
            content = {
                'title': 'Paper title',
                'abstract': 'This is an abstract',
                'authorids': ['test@mail.com', 'author@mail.com', 'author2@mail.com'],
                'authors': ['SomeFirstName User', 'Melisa Bok', 'Andrew Mc'],
                'pdf': '/pdf/22234qweoiuweroi22234qweoiuweroi12345678.pdf'
            }
        )

        note = test_client.post_note(note)
        assert note

        conference.setup_post_submission_stage(force=True)
        conference.set_reviewers(['reviewer_kgb@mail.com', 'reviewer_kgb2@mail.com'])
        conference.set_program_chairs([])
        conference.set_assignment(number = 1, user = 'reviewer_kgb@mail.com')
        conference.set_assignment(number = 1, user = 'reviewer_kgb2@mail.com')

        conference.create_review_stage()

        request_page(selenium, "http://localhost:3030/group?id=eswc-conferences.org/ESWC/2019/Workshop/KGB/Program_Chairs#paper-status", client.token, by=By.CLASS_NAME, wait_for_element='reviewer-progress')
        reviews = selenium.find_elements(By.CLASS_NAME, 'reviewer-progress')
        assert reviews
        assert len(reviews) == 1
        headers = reviews[0].find_elements(By.TAG_NAME, 'h4')
        assert headers
        assert headers[0].text == '0 of 2 Reviews Submitted'

        request_page(selenium, "http://localhost:3030/group?id=eswc-conferences.org/ESWC/2019/Workshop/KGB/Program_Chairs#reviewer-status", client.token, by=By.CLASS_NAME, wait_for_element='reviewer-progress')
        reviews = selenium.find_elements(By.CLASS_NAME, 'reviewer-progress')
        assert reviews
        # assert len(reviews) == 5 temporally disable assert

        note = openreview.Note(invitation = 'eswc-conferences.org/ESWC/2019/Workshop/KGB/Paper1/-/Official_Review',
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

        request_page(selenium, "http://localhost:3030/group?id=eswc-conferences.org/ESWC/2019/Workshop/KGB/Program_Chairs#paper-status", client.token, by=By.CLASS_NAME, wait_for_element='reviewer-progress')
        reviews = selenium.find_elements(By.CLASS_NAME, 'reviewer-progress')
        assert reviews
        assert len(reviews) == 1
        headers = reviews[0].find_elements(By.TAG_NAME, 'h4')
        assert headers
        assert headers[0].text == '1 of 2 Reviews Submitted'

        assert selenium.find_element(By.LINK_TEXT, 'Paper Status')
        try:
            selenium.find_element(By.LINK_TEXT, 'Area Chair Status')
        except NoSuchElementException as e:
            assert e

        assert selenium.find_element(By.LINK_TEXT, 'Reviewer Status')



