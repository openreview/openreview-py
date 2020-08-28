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

class TestICLRConference():

    @pytest.fixture(scope="class")
    def conference(self, client):
        now = datetime.datetime.utcnow()
        #pc_client = openreview.Client(username='pc@eccv.org', password='1234')
        builder = openreview.conference.ConferenceBuilder(client)
        assert builder, 'builder is None'

        builder.set_conference_id('ICLR.cc/2021/Conference')
        builder.set_conference_short_name('ICLR 2021')
        builder.set_override_homepage(True)
        builder.has_area_chairs(True)
        builder.set_homepage_header({
            'title': 'International Conference on Learning Representations',
            'subtitle': 'ICLR 2021',
            'deadline': '',
            'date': 'May 04 2021',
            'website': 'https://iclr.cc/',
            'location': 'SEC, Glasgow',
            'instructions': '''<p class='dark'>Please see the venue website for more information.<br>
            <p class='dark'><strong>Abstract Submission End:</strong> Sep 28 2020 03:00PM UTC-0</p>
            <p class='dark'><strong>Paper Submission End:</strong> Oct 2 2020 03:00PM UTC-0</p>''',
            'contact': 'iclr2021programchairs@googlegroups.com'
        })

        # Reviewers
        reviewer_registration_tasks = {
            'profile_confirmed': {
                'required': True,
                'description': 'I confirm that I updated my OpenReview profile.',
                'value-checkbox': 'Yes',
                'order': 1
            },
            'expertise_confirmed': {
                'required': True,
                'description': 'I confirm that I verified my expertise.',
                'value-checkbox': 'Yes',
                'order': 1
            },
            'TPMS_registration_confirmed' : {
                'required': True,
                'description': 'I confirm that I updated my TPMS account.',
                'value-checkbox': 'Yes',
                'order': 3
            },
            'reviewer_instructions_confirm' : {
                'required': True,
                'description': 'I confirm that I will adhere to the reviewer instructions and will do my best to provide the agreed upon number of reviews in time.',
                'value-checkbox': 'Yes',
                'order': 4
            },
            'emergency_review_count' : {
                'required': True,
                'description': 'Decide whether you can and want to serve as emergency reviewer. Select how many reviews you can volunteer as emergency reviewer.',
                'value-radio': ['0', '1', '2', '3', '4'],
                'order': 5,
                'default': '0'
            }
        }

        ac_registration_tasks = {
            'profile_confirmed': {
                'required': True,
                'description': 'I confirm that I updated my OpenReview profile.',
                'value-checkbox': 'Yes',
                'order': 1
            },
            'expertise_confirmed': {
                'required': True,
                'description': 'I confirm that I verified my expertise.',
                'value-checkbox': 'Yes',
                'order': 1
            },
            'TPMS_registration_confirmed' : {
                'required': True,
                'description': 'I confirm that I updated my TPMP account',
                'value-checkbox': 'Yes',
                'order': 3}
        }

        reviewer_instructions = '''
1. In order to avoid conflicts of interest in reviewing, we ask that all reviewers take a moment to update their OpenReview profiles with their latest information regarding email addresses, work history and professional relationships: https://openreview.net/profile?mode=edit

2. We automatically populated your profile with your published papers. These represent your expertise and will be used to match submissions to you. Please take a moment to verify if the selection of papers is representative of your expertise and modify it if necessary: https://openreview.net/invitation?id=ICLR.cc/2021/Conference/-/Expertise_Selection

3. Paper matching will be done via the Toronto paper matching system (TPMS). Please update your TPMS profile so that it represents your expertise well: http://torontopapermatching.org/webapp/profileBrowser/login/
If you don't have a TPMS account yet, you can create one here: http://torontopapermatching.org/webapp/profileBrowser/register/
Ensure that the email you use for your TPMS profile is listed as one of the emails in your OpenReview profile.

4. Please check the reviewer instructions: https://iclr.cc/Conferences/2021/ReviewerGuide

5. Emergency reviewers are important to ensure that all papers receive 3 reviews even if some reviewers cannot submit their reviews in time (e.g. due to sickness). If you know for sure that you will be able to review 1 or 2 papers within 72-96 hours in the time from Oct 29 to Nov 9, you can volunteer as emergency reviewer. We will reduce your normal load by the number of papers you agree to handle as emergency reviewer. Every emergency review will increase your reviewer score in addition to the score assigned by the area chair.
        '''

        ac_instructions = '''
1. In order to avoid conflicts of interest in reviewing, we ask that all reviewers take a moment to update their OpenReview profiles with their latest information regarding email addresses, work history and professional relationships: https://openreview.net/profile?mode=edit

2. We automatically populated your profile with your published papers. These represent your expertise and will be used to match submissions to you. Please take a moment to verify if the selection of papers is representative of your expertise and modify it if necessary: https://openreview.net/invitation?id=ICLR.cc/2021/Conference/-/Expertise_Selection

3. Paper matching will be done via the Toronto paper matching system (TPMS). Please update your TPMS profile so that it represents your expertise well: http://torontopapermatching.org/webapp/profileBrowser/login/
If you don't have a TPMS account yet, you can create one here: http://torontopapermatching.org/webapp/profileBrowser/register/
Ensure that the email you use for your TPMS profile is listed as one of the emails in your OpenReview profile.
        '''
        builder.set_registration_stage(
        additional_fields = reviewer_registration_tasks,
        due_date = now + datetime.timedelta(minutes = 40),
        ac_additional_fields=ac_registration_tasks,
        instructions=reviewer_instructions,
        ac_instructions=ac_instructions
        )
        builder.set_expertise_selection_stage(due_date = now + datetime.timedelta(minutes = 10))
        builder.set_submission_stage(double_blind = True,
            public = False,
            due_date = now + datetime.timedelta(minutes = 10),
            withdrawn_submission_public=False,
            withdrawn_submission_author_anonymous=True,
            email_pcs_on_withdraw=True,
            desk_rejected_submission_public=False,
            desk_rejected_submission_author_anonymous=True)


        conference = builder.get_result()
        conference.set_program_chairs(['pc@iclr.cc'])
        return conference

    def test_create_conference(self, client, conference, helpers):

        pc_client = helpers.create_user('pc@iclr.cc', 'Program', 'ICLRChair')

        group = pc_client.get_group('ICLR.cc/2021/Conference')
        assert group
        assert group.web

        pc_group = pc_client.get_group('ICLR.cc/2021/Conference/Program_Chairs')
        assert pc_group
        assert pc_group.web

    def test_recruit_reviewer(self, conference, client, helpers, selenium, request_page):

        result = conference.recruit_reviewers(['iclr2021_one@mail.com', 'iclr2021_two@mail.com', 'iclr2021_three@mail.com'])
        assert result
        assert result.id == 'ICLR.cc/2021/Conference/Reviewers/Invited'
        assert 'iclr2021_one@mail.com' in result.members
        assert 'iclr2021_two@mail.com' in result.members
        assert 'iclr2021_three@mail.com' in result.members

        messages = client.get_messages(to = 'iclr2021_one@mail.com', subject = 'ICLR.cc/2021/Conference: Invitation to Review')
        text = messages[0]['content']['text']
        assert 'Dear invitee,' in text
        assert 'You have been nominated by the program chair committee of ICLR 2021 to serve as a reviewer' in text

        reject_url = re.search('https://.*response=No', text).group(0).replace('https://openreview.net', 'http://localhost:3000')
        accept_url = re.search('https://.*response=Yes', text).group(0).replace('https://openreview.net', 'http://localhost:3000')

        request_page(selenium, reject_url, alert=True)
        declined_group = client.get_group(id='ICLR.cc/2021/Conference/Reviewers/Declined')
        assert len(declined_group.members) == 1
        accepted_group = client.get_group(id='ICLR.cc/2021/Conference/Reviewers')
        assert len(accepted_group.members) == 0

        request_page(selenium, accept_url, alert=True)
        declined_group = client.get_group(id='ICLR.cc/2021/Conference/Reviewers/Declined')
        assert len(declined_group.members) == 0
        accepted_group = client.get_group(id='ICLR.cc/2021/Conference/Reviewers')
        assert len(accepted_group.members) == 1

        messages = client.get_messages(to = 'iclr2021_two@mail.com', subject = 'ICLR.cc/2021/Conference: Invitation to Review')
        text = messages[0]['content']['text']
        assert 'Dear invitee,' in text
        assert 'You have been nominated by the program chair committee of ICLR 2021 to serve as a reviewer' in text

        reject_url = re.search('https://.*response=No', text).group(0).replace('https://openreview.net', 'http://localhost:3000')
        accept_url = re.search('https://.*response=Yes', text).group(0).replace('https://openreview.net', 'http://localhost:3000')

        request_page(selenium, reject_url, alert=True)
        declined_group = client.get_group(id='ICLR.cc/2021/Conference/Reviewers/Declined')
        assert len(declined_group.members) == 1
        accepted_group = client.get_group(id='ICLR.cc/2021/Conference/Reviewers')
        assert len(accepted_group.members) == 1

    def test_registration(self, conference, helpers, selenium, request_page):

        reviewer_client = helpers.create_user('iclr2021_one@mail.com', 'ReviewerOne', 'ICLR')
        reviewer_tasks_url = 'http://localhost:3030/group?id=ICLR.cc/2021/Conference/Reviewers#reviewer-tasks'
        request_page(selenium, reviewer_tasks_url, reviewer_client.token)

        assert selenium.find_element_by_link_text('Reviewer Registration')
        assert selenium.find_element_by_link_text('Expertise Selection')

        registration_notes = reviewer_client.get_notes(invitation = 'ICLR.cc/2021/Conference/Reviewers/-/Form')
        assert registration_notes
        assert len(registration_notes) == 1

        registration_forum = registration_notes[0].forum

        registration_note = reviewer_client.post_note(
            openreview.Note(
                invitation = 'ICLR.cc/2021/Conference/Reviewers/-/Registration',
                forum = registration_forum,
                replyto = registration_forum,
                content = {
                    'profile_confirmed': 'Yes',
                    'expertise_confirmed': 'Yes',
                    'TPMS_registration_confirmed': 'Yes',
                    'reviewer_instructions_confirm': 'Yes',
                    'emergency_review_count': '0'
                },
                signatures = [
                    '~ReviewerOne_ICLR1'
                ],
                readers = [
                    conference.get_id(),
                    '~ReviewerOne_ICLR1'
                ],
                writers = [
                    conference.get_id(),
                    '~ReviewerOne_ICLR1'
                ]
            ))
        assert registration_note


        request_page(selenium, 'http://localhost:3030/group?id=ICLR.cc/2021/Conference/Reviewers', reviewer_client.token)
        header = selenium.find_element_by_id('header')
        assert header
        notes = header.find_elements_by_class_name("description")
        assert notes
        assert len(notes) == 1
        assert notes[0].text == 'This page provides information and status updates for the ICLR 2021. It will be regularly updated as the conference progresses, so please check back frequently.'

        request_page(selenium, reviewer_tasks_url, reviewer_client.token)

        assert selenium.find_element_by_link_text('Reviewer Registration')
        assert selenium.find_element_by_link_text('Expertise Selection')
        tasks = selenium.find_element_by_id('reviewer-tasks')
        assert tasks
        assert len(tasks.find_elements_by_class_name('note')) == 2
        assert len(tasks.find_elements_by_class_name('completed')) == 2