import time
import openreview
import pytest
import datetime
import re
import random
import os
import csv
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from openreview import ProfileManagement

class TestICLRConference():


    @pytest.fixture(scope="class")
    def profile_management(self, client):
        profile_management = ProfileManagement(client, 'openreview.net')
        profile_management.setup()
        return profile_management


    def test_create_conference(self, client, openreview_client, helpers, profile_management):

        now = datetime.datetime.utcnow()
        abstract_date = now + datetime.timedelta(days=1)
        due_date = now + datetime.timedelta(days=3)

        # Post the request form note
        pc_client=helpers.create_user('pc@iclr.cc', 'Program', 'ICLRChair')

        sac_client = helpers.create_user('sac10@gmail.com', 'SAC', 'ICLROne')
        helpers.create_user('sac2@iclr.cc', 'SAC', 'ICLRTwo')
        helpers.create_user('ac1@iclr.cc', 'AC', 'ICLROne')
        helpers.create_user('ac2@iclr.cc', 'AC', 'ICLRTwo')
        helpers.create_user('reviewer1@iclr.cc', 'Reviewer', 'ICLROne')
        helpers.create_user('reviewer2@iclr.cc', 'Reviewer', 'ICLRTwo')
        helpers.create_user('reviewer3@iclr.cc', 'Reviewer', 'ICLRThree')
        helpers.create_user('reviewer4@gmail.com', 'Reviewer', 'ICLRFour')
        helpers.create_user('reviewer5@gmail.com', 'Reviewer', 'ICLRFive')
        helpers.create_user('reviewer6@gmail.com', 'Reviewer', 'ICLRSix')
        helpers.create_user('reviewerethics@gmail.com', 'Reviewer', 'ICLRSeven')

        request_form_note = pc_client.post_note(openreview.Note(
            invitation='openreview.net/Support/-/Request_Form',
            signatures=['~Program_ICLRChair1'],
            readers=[
                'openreview.net/Support',
                '~Program_ICLRChair1'
            ],
            writers=[],
            content={
                'title': 'International Conference on Learning Representations',
                'Official Venue Name': 'International Conference on Learning Representations',
                'Abbreviated Venue Name': 'ICLR 2024',
                'Official Website URL': 'https://iclr.cc',
                'program_chair_emails': ['pc@iclr.cc'],
                'contact_email': 'pc@iclr.cc',
                'Area Chairs (Metareviewers)': 'Yes, our venue has Area Chairs',
                'senior_area_chairs': 'Yes, our venue has Senior Area Chairs',
                'ethics_chairs_and_reviewers': 'Yes, our venue has Ethics Chairs and Reviewers',
                'Venue Start Date': '2024/07/01',
                'abstract_registration_deadline': abstract_date.strftime('%Y/%m/%d'),
                'Submission Deadline': due_date.strftime('%Y/%m/%d'),
                'Location': 'Virtual',
                'submission_reviewer_assignment': 'Automatic',
                'Author and Reviewer Anonymity': 'Double-blind',
                'reviewer_identity': ['Program Chairs', 'Assigned Senior Area Chair', 'Assigned Area Chair', 'Assigned Reviewers'],
                'area_chair_identity': ['Program Chairs', 'Assigned Senior Area Chair', 'Assigned Area Chair', 'Assigned Reviewers'],
                'senior_area_chair_identity': ['Program Chairs', 'Assigned Senior Area Chair', 'Assigned Area Chair', 'Assigned Reviewers'],
                'Open Reviewing Policy': 'Submissions and reviews should both be public.',
                'submission_readers': 'Everyone (submissions are public)',
                'How did you hear about us?': 'ML conferences',
                'Expected Submissions': '100',
                'use_recruitment_template': 'Yes',
                'api_version': '2'
            }))

        helpers.await_queue()

        # Post a deploy note
        client.post_note(openreview.Note(
            content={'venue_id': 'ICLR.cc/2024/Conference'},
            forum=request_form_note.forum,
            invitation='openreview.net/Support/-/Request{}/Deploy'.format(request_form_note.number),
            readers=['openreview.net/Support'],
            referent=request_form_note.forum,
            replyto=request_form_note.forum,
            signatures=['openreview.net/Support'],
            writers=['openreview.net/Support']
        ))

        helpers.await_queue()

        venue_group = openreview_client.get_group('ICLR.cc/2024/Conference')
        assert venue_group
        assert venue_group.content['date']['value'] == f'Abstract Registration: {abstract_date.strftime("%b %d %Y %I:%M%p")} UTC-0, Submission Deadline: {due_date.strftime("%b %d %Y")} UTC-0'
        assert openreview_client.get_group('ICLR.cc/2024/Conference/Senior_Area_Chairs')
        assert openreview_client.get_group('ICLR.cc/2024/Conference/Area_Chairs')
        assert openreview_client.get_group('ICLR.cc/2024/Conference/Reviewers')
        assert openreview_client.get_group('ICLR.cc/2024/Conference/Authors')

        submission_invitation = openreview_client.get_invitation('ICLR.cc/2024/Conference/-/Submission')
        assert submission_invitation
        assert submission_invitation.duedate

        assert openreview_client.get_invitation('ICLR.cc/2024/Conference/Reviewers/-/Expertise_Selection')
        assert openreview_client.get_invitation('ICLR.cc/2024/Conference/Area_Chairs/-/Expertise_Selection')
        assert openreview_client.get_invitation('ICLR.cc/2024/Conference/Senior_Area_Chairs/-/Expertise_Selection')

    def test_submissions(self, client, openreview_client, helpers, test_client):

        test_client = openreview.api.OpenReviewClient(token=test_client.token)

        domains = ['umass.edu', 'amazon.com', 'fb.com', 'cs.umass.edu', 'google.com', 'mit.edu', 'deepmind.com', 'co.ux', 'apple.com', 'nvidia.com']
        for i in range(1,12):
            note = openreview.api.Note(
                content = {
                    'title': { 'value': 'Paper title ' + str(i) },
                    'abstract': { 'value': 'This is an abstract ' + str(i) },
                    'authorids': { 'value': ['~SomeFirstName_User1', 'peter@mail.com', 'andrew@' + domains[i % 10]] },
                    'authors': { 'value': ['SomeFirstName User', 'Peter SomeLastName', 'Andrew Mc'] },
                    'keywords': { 'value': ['machine learning', 'nlp'] },
                    'pdf': {'value': '/pdf/' + 'p' * 40 +'.pdf' },
                }
            )
            if i == 1 or i == 11:
                note.content['authors']['value'].append('SAC ICLROne')
                note.content['authorids']['value'].append('~SAC_ICLROne1')

            test_client.post_note_edit(invitation='ICLR.cc/2024/Conference/-/Submission',
                signatures=['~SomeFirstName_User1'],
                note=note)

        helpers.await_queue_edit(openreview_client, invitation='ICLR.cc/2024/Conference/-/Submission', count=11)

        submissions = openreview_client.get_notes(invitation='ICLR.cc/2024/Conference/-/Submission', sort='number:asc')
        assert len(submissions) == 11
        assert ['ICLR.cc/2024/Conference', '~SomeFirstName_User1', 'peter@mail.com', 'andrew@amazon.com', '~SAC_ICLROne1'] == submissions[0].readers
        assert ['~SomeFirstName_User1', 'peter@mail.com', 'andrew@amazon.com', '~SAC_ICLROne1'] == submissions[0].content['authorids']['value']

        authors_group = openreview_client.get_group(id='ICLR.cc/2024/Conference/Authors')

        for i in range(1,12):
            assert f'ICLR.cc/2024/Conference/Submission{i}/Authors' in authors_group.members

    def test_post_submission(self, client, openreview_client, helpers):

        pc_client=openreview.Client(username='pc@iclr.cc', password=helpers.strong_password)
        request_form=pc_client.get_notes(invitation='openreview.net/Support/-/Request_Form')[0]
        venue = openreview.get_conference(client, request_form.id, support_user='openreview.net/Support')

        ## close the submissions
        now = datetime.datetime.utcnow()
        due_date = now - datetime.timedelta(minutes=28)
        pc_client.post_note(openreview.Note(
            content={
                'title': 'International Conference on Learning Representations',
                'Official Venue Name': 'International Conference on Learning Representations',
                'Abbreviated Venue Name': 'ICLR 2024',
                'Official Website URL': 'https://iclr.cc',
                'program_chair_emails': ['pc@iclr.cc', 'pc3@iclr.cc'],
                'contact_email': 'pc@iclr.cc',
                'Venue Start Date': '2024/07/01',
                'Submission Deadline': due_date.strftime('%Y/%m/%d'),
                'Location': 'Virtual',
                'submission_reviewer_assignment': 'Automatic',
                'How did you hear about us?': 'ML conferences',
                'Expected Submissions': '100',
            },
            forum=request_form.forum,
            invitation='openreview.net/Support/-/Request{}/Revision'.format(request_form.number),
            readers=['ICLR.cc/2024/Conference/Program_Chairs', 'openreview.net/Support'],
            referent=request_form.forum,
            replyto=request_form.forum,
            signatures=['~Program_ICLRChair1'],
            writers=[]
        ))

        helpers.await_queue()
        helpers.await_queue_edit(openreview_client, 'ICLR.cc/2024/Conference/-/Post_Submission-0-1', count=2)
        helpers.await_queue_edit(openreview_client, 'ICLR.cc/2024/Conference/-/Withdrawal-0-1', count=2)
        helpers.await_queue_edit(openreview_client, 'ICLR.cc/2024/Conference/-/Desk_Rejection-0-1', count=2)

        pc_client_v2=openreview.api.OpenReviewClient(username='pc@iclr.cc', password=helpers.strong_password)
        submission_invitation = pc_client_v2.get_invitation('ICLR.cc/2024/Conference/-/Submission')
        assert submission_invitation.expdate < openreview.tools.datetime_millis(now)

        submissions = pc_client_v2.get_notes(invitation='ICLR.cc/2024/Conference/-/Submission', sort='number:asc')
        assert len(submissions) == 11
        assert submissions[0].readers == ['everyone']
        assert '_bibtex' in submissions[0].content
        assert 'author={Anonymous}' in submissions[0].content['_bibtex']['value']