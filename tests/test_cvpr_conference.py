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

class TestCVPRSConference():

    @pytest.fixture(scope="class")
    def conference(self, client):
        pc_client=openreview.Client(username='pc@cvpr.cc', password='1234')
        request_form=client.get_notes(invitation='openreview.net/Support/-/Request_Form', sort='tmdate')[0]

        conference=openreview.helpers.get_conference(pc_client, request_form.id)
        return conference


    def test_create_conference(self, client, helpers):

        now = datetime.datetime.utcnow()
        due_date = now + datetime.timedelta(days=3)
        first_date = now + datetime.timedelta(days=1)

        # Post the request form note
        pc_client=helpers.create_user('pc@cvpr.cc', 'Program', 'CVPRChair')

        request_form_note = pc_client.post_note(openreview.Note(
            invitation='openreview.net/Support/-/Request_Form',
            signatures=['~Program_CVPRChair1'],
            readers=[
                'openreview.net/Support',
                '~Program_CVPRChair1'
            ],
            writers=[],
            content={
                'title': 'Conference on Computer Vision and Pattern Recognition 2023',
                'Official Venue Name': 'Conference on Computer Vision and Pattern Recognition 2023',
                'Abbreviated Venue Name': 'CVPR 2023',
                'Official Website URL': 'https://cvpr.cc',
                'program_chair_emails': ['pc@cvpr.cc'],
                'contact_email': 'pc@cvpr.cc',
                'Area Chairs (Metareviewers)': 'Yes, our venue has Area Chairs',
                'senior_area_chairs': 'Yes, our venue has Senior Area Chairs',
                'Venue Start Date': '2023/12/01',
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
            content={'venue_id': 'thecvf.com/CVPR/2023/Conference'},
            forum=request_form_note.forum,
            invitation='openreview.net/Support/-/Request{}/Deploy'.format(request_form_note.number),
            readers=['openreview.net/Support'],
            referent=request_form_note.forum,
            replyto=request_form_note.forum,
            signatures=['openreview.net/Support'],
            writers=['openreview.net/Support']
        ))

        helpers.await_queue()

        assert client.get_group('thecvf.com/CVPR/2023/Conference')
        assert client.get_group('thecvf.com/CVPR/2023/Conference/Senior_Area_Chairs')
        acs=client.get_group('thecvf.com/CVPR/2023/Conference/Area_Chairs')
        assert acs
        assert 'thecvf.com/CVPR/2023/Conference/Senior_Area_Chairs' in acs.readers
        reviewers=client.get_group('thecvf.com/CVPR/2023/Conference/Reviewers')
        assert reviewers
        assert 'thecvf.com/CVPR/2023/Conference/Senior_Area_Chairs' in reviewers.readers
        assert 'thecvf.com/CVPR/2023/Conference/Area_Chairs' in reviewers.readers

        assert client.get_group('thecvf.com/CVPR/2023/Conference/Authors')

    def test_submit_papers(self, test_client, client, helpers):

        ## Need super user permission to add the venue to the active_venues group
        request_form=client.get_notes(invitation='openreview.net/Support/-/Request_Form', sort='tmdate')[0]
        conference=openreview.helpers.get_conference(client, request_form.id)

        domains = ['umass.edu', 'amazon.com', 'fb.com', 'cs.umass.edu', 'google.com', 'mit.edu']
        for i in range(1,6):
            note = openreview.Note(invitation = 'thecvf.com/CVPR/2023/Conference/-/Submission',
                readers = ['thecvf.com/CVPR/2023/Conference', 'test@mail.com', 'peter@mail.com', 'andrew@' + domains[i], '~SomeFirstName_User1'],
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
            note = test_client.post_note(note)

        conference.setup_first_deadline_stage(force=True)

        blinded_notes = test_client.get_notes(invitation='thecvf.com/CVPR/2023/Conference/-/Blind_Submission', sort='tmdate')
        assert len(blinded_notes) == 5

        assert blinded_notes[0].readers == ['thecvf.com/CVPR/2023/Conference', 'thecvf.com/CVPR/2023/Conference/Paper5/Authors']

        assert client.get_invitation('thecvf.com/CVPR/2023/Conference/Paper5/-/Withdraw')
        assert client.get_invitation('thecvf.com/CVPR/2023/Conference/Paper5/-/Desk_Reject')
        assert client.get_invitation('thecvf.com/CVPR/2023/Conference/Paper5/-/Revision')


    def test_post_submission_stage(self, conference, helpers, test_client, client, request_page, selenium):

        #conference.setup_final_deadline_stage(force=True)
        pc_client=openreview.Client(username='pc@cvpr.cc', password='1234')
        request_form=pc_client.get_notes(invitation='openreview.net/Support/-/Request_Form')[0]

        post_submission_note=pc_client.post_note(openreview.Note(
            content= {
                'force': 'Yes',
                'hide_fields': ['keywords'],
                'submission_readers': 'Assigned program committee (assigned reviewers, assigned area chairs, assigned senior area chairs if applicable)'
            },
            forum= request_form.id,
            invitation= f'openreview.net/Support/-/Request{request_form.number}/Post_Submission',
            readers= ['thecvf.com/CVPR/2023/Conference/Program_Chairs', 'openreview.net/Support'],
            referent= request_form.id,
            replyto= request_form.id,
            signatures= ['~Program_CVPRChair1'],
            writers= [],
        ))

        helpers.await_queue()


    def test_rebuttal_stage(self, conference, helpers, test_client, client):

        now = datetime.datetime.utcnow()

        conference.set_review_rebuttal_stage(openreview.ReviewRebuttalStage(
            due_date=now + datetime.timedelta(minutes = 40),
            single_rebuttal=True,
            additional_fields={
                'pdf': {
                    'description': 'Upload a PDF file that ends with .pdf',
                    'order': 9,
                    'value-file': {
                        'fileTypes': ['pdf'],
                        'size': 50
                    },
                    'required':True
                }                
            }
        ))

        assert client.get_invitation('thecvf.com/CVPR/2023/Conference/Paper5/-/Rebuttal')

        submissions=conference.get_submissions(number=5)
        assert len(submissions) == 1

        rebuttal_note=test_client.post_note(openreview.Note(
            invitation='thecvf.com/CVPR/2023/Conference/Paper5/-/Rebuttal',
            forum=submissions[0].id,
            replyto=submissions[0].id,
            readers=[
                'thecvf.com/CVPR/2023/Conference/Program_Chairs',
                'thecvf.com/CVPR/2023/Conference/Paper5/Authors'
            ],
            writers=['thecvf.com/CVPR/2023/Conference', 'thecvf.com/CVPR/2023/Conference/Paper5/Authors'],
            signatures=['thecvf.com/CVPR/2023/Conference/Paper5/Authors'],
            content={
                'rebuttal': 'Thanks for the detailed review!',
                'pdf': '/pdf/22234qweoiuweroi22234qweoiuweroi12345678.pdf'
            }
        ))

        helpers.await_queue()

        ## release the rebuttals
        conference.set_review_rebuttal_stage(openreview.ReviewRebuttalStage(
            due_date=now + datetime.timedelta(minutes = 40),
            single_rebuttal=True,
            additional_fields={
                'pdf': {
                    'description': 'Upload a PDF file that ends with .pdf',
                    'order': 9,
                    'value-file': {
                        'fileTypes': ['pdf'],
                        'size': 50
                    },
                    'required':True
                }                
            },
            readers=[
                openreview.conference.ReviewRebuttalStage.Readers.SENIOR_AREA_CHAIRS_ASSIGNED,
                openreview.conference.ReviewRebuttalStage.Readers.AREA_CHAIRS_ASSIGNED,
                openreview.conference.ReviewRebuttalStage.Readers.REVIEWERS_ASSIGNED
            ]
        ))

        rebuttals = client.get_notes(invitation='thecvf.com/CVPR/2023/Conference/Paper5/-/Rebuttal')
        assert len(rebuttals) == 1

        assert rebuttals[0].readers == [
            'thecvf.com/CVPR/2023/Conference/Program_Chairs',
            'thecvf.com/CVPR/2023/Conference/Paper5/Senior_Area_Chairs',
            'thecvf.com/CVPR/2023/Conference/Paper5/Area_Chairs',
            'thecvf.com/CVPR/2023/Conference/Paper5/Reviewers',
            'thecvf.com/CVPR/2023/Conference/Paper5/Authors'
        ]
