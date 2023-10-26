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

class TestNeurIPSTrackConference():

    def test_create_conference(self, client, openreview_client, helpers, selenium, request_page):

        now = datetime.datetime.utcnow()
        due_date = now + datetime.timedelta(days=3)
        first_date = now + datetime.timedelta(days=1)

        # Post the request form note
        pc_client=helpers.create_user('pc@neurips.cc', 'Program', 'NeurIPSChair')

        helpers.create_user('another_andrew@mit.edu', 'Another', 'Andrew')
        helpers.create_user('sac1@google.com', 'SeniorArea', 'GoogleChair', institution='google.com')
        helpers.create_user('sac2@gmail.com', 'SeniorArea', 'NeurIPSChair', institution='fb.com')
        helpers.create_user('ac1@mit.edu', 'Area', 'IBMChair', institution='ibm.com')
        helpers.create_user('ac2@gmail.com', 'Area', 'GoogleChair', institution='google.com')
        helpers.create_user('ac3@umass.edu', 'Area', 'UMassChair', institution='umass.edu')
        helpers.create_user('reviewer1@umass.edu', 'Reviewer', 'UMass', institution='umass.edu')
        helpers.create_user('reviewer2@mit.edu', 'Reviewer', 'MIT', institution='mit.edu')
        helpers.create_user('reviewer3@ibm.com', 'Reviewer', 'IBM', institution='ibm.com')
        helpers.create_user('reviewer4@fb.com', 'Reviewer', 'Facebook', institution='fb.com')
        helpers.create_user('reviewer5@google.com', 'Reviewer', 'Google', institution='google.com')
        helpers.create_user('reviewer6@amazon.com', 'Reviewer', 'Amazon', institution='amazon.com')
        helpers.create_user('external_reviewer1@amazon.com', 'External Reviewer', 'Amazon', institution='amazon.com')
        helpers.create_user('external_reviewer2@mit.edu', 'External Reviewer', 'MIT', institution='mit.edu')
        helpers.create_user('external_reviewer3@adobe.com', 'External Reviewer', 'Adobe', institution='adobe.com')

        helpers.create_user('melisatest@neuirps.cc', 'Melisa', 'Gilbert')
        helpers.create_user('melisatest2@neurips.cc', 'Melisa', 'Gilbert')

        request_form_note = pc_client.post_note(openreview.Note(
            invitation='openreview.net/Support/-/Request_Form',
            signatures=['~Program_NeurIPSChair1'],
            readers=[
                'openreview.net/Support',
                '~Program_NeurIPSChair1'
            ],
            writers=[],
            content={
                'title': 'Thirty-seventh Conference on Neural Information Processing Systems Datasets and Benchmarks Track',
                'Official Venue Name': 'Thirty-seventh Conference on Neural Information Processing Systems Datasets and Benchmarks Track',
                'Abbreviated Venue Name': 'NeurIPS 2023 Datasets and Benchmarks',
                'Official Website URL': 'https://neurips.cc',
                'program_chair_emails': ['pc@neurips.cc'],
                'contact_email': 'pc@neurips.cc',
                'publication_chairs':'No, our venue does not have Publication Chairs',
                'Area Chairs (Metareviewers)': 'Yes, our venue has Area Chairs',
                'senior_area_chairs': 'No, our venue does not have Senior Area Chairs',
                'Venue Start Date': '2023/12/01',
                'Submission Deadline': due_date.strftime('%Y/%m/%d'),
                'abstract_registration_deadline': first_date.strftime('%Y/%m/%d'),
                'Location': 'Virtual',
                'submission_reviewer_assignment': 'Automatic',
                'Author and Reviewer Anonymity': 'Double-blind',
                'reviewer_identity': ['Program Chairs', 'Assigned Senior Area Chair', 'Assigned Area Chair', 'Assigned Reviewers'],
                'area_chair_identity': ['Program Chairs', 'Assigned Senior Area Chair', 'Assigned Area Chair', 'Assigned Reviewers'],
                'senior_area_chair_identity': ['Program Chairs', 'Assigned Senior Area Chair', 'Assigned Area Chair', 'Assigned Reviewers'],
                'Open Reviewing Policy': 'Submissions and reviews should both be private.',
                'submission_readers': 'Program chairs and paper authors only',
                'How did you hear about us?': 'ML conferences',
                'Expected Submissions': '100',
                'api_version': '2',
                'submission_deadline_author_reorder': 'No'
            }))

        helpers.await_queue()

        # Post a deploy note
        client.post_note(openreview.Note(
            content={'venue_id': 'NeurIPS.cc/2023/Track/Datasets_and_Benchmarks'},
            forum=request_form_note.forum,
            invitation='openreview.net/Support/-/Request{}/Deploy'.format(request_form_note.number),
            readers=['openreview.net/Support'],
            referent=request_form_note.forum,
            replyto=request_form_note.forum,
            signatures=['openreview.net/Support'],
            writers=['openreview.net/Support']
        ))

        helpers.await_queue()

        venue_group = openreview_client.get_group('NeurIPS.cc/2023/Track/Datasets_and_Benchmarks')
        assert venue_group
        assert venue_group.host == 'NeurIPS.cc'
        assert openreview_client.get_group('NeurIPS.cc/2023/Track/Datasets_and_Benchmarks/Area_Chairs')
        reviewers=openreview_client.get_group('NeurIPS.cc/2023/Track/Datasets_and_Benchmarks/Reviewers')
        assert reviewers
        assert 'NeurIPS.cc/2023/Track/Datasets_and_Benchmarks/Area_Chairs' in reviewers.readers

        assert openreview_client.get_group('NeurIPS.cc/2023/Track/Datasets_and_Benchmarks/Authors')
        post_submission =  openreview_client.get_invitation('NeurIPS.cc/2023/Track/Datasets_and_Benchmarks/-/Post_Submission')
        assert 'authors' in post_submission.edit['note']['content']
        assert 'authorids' in post_submission.edit['note']['content']


    def test_submit_papers(self, test_client, client, helpers, openreview_client):

        pc_client=openreview.Client(username='pc@neurips.cc', password=helpers.strong_password)
        request_form=client.get_notes(invitation='openreview.net/Support/-/Request_Form', sort='tmdate')[0]

        test_client = openreview.api.OpenReviewClient(username='test@mail.com', password=helpers.strong_password)

        domains = ['umass.edu', 'amazon.com', 'fb.com', 'cs.umass.edu', 'google.com', 'mit.edu']
        for i in range(1,6):
            note = openreview.api.Note(
                content = {
                    'title': { 'value': 'Paper title ' + str(i) },
                    'abstract': { 'value': 'This is an abstract ' + str(i) },
                    'authorids': { 'value': ['test@mail.com', 'peter@mail.com', 'andrew@' + domains[i]] },
                    'authors': { 'value': ['SomeFirstName User', 'Peter SomeLastName', 'Andrew Mc'] },
                    'keywords': { 'value': ['machine learning', 'nlp'] },
                }
            )
            if i == 1:
                note.content['authors']['value'].append('SeniorArea GoogleChair')
                note.content['authorids']['value'].append('~SeniorArea_GoogleChair1')
                print(note)

            if i == 2:
                note.content['authors']['value'].append('Melisa Gilbert')
                note.content['authors']['value'].append('Melisa Gilbert')
                note.content['authorids']['value'].append('~Melisa_Gilbert1')
                note.content['authorids']['value'].append('~Melisa_Gilbert2')
                print(note)

            test_client.post_note_edit(invitation='NeurIPS.cc/2023/Track/Datasets_and_Benchmarks/-/Submission',
                signatures=['~SomeFirstName_User1'],
                note=note)            


        ## finish submission deadline
        now = datetime.datetime.utcnow()
        due_date = now + datetime.timedelta(days=3)
        first_date = now - datetime.timedelta(minutes=28)               

        venue_revision_note = openreview.Note(
            content={
                'title': 'Thirty-seventh Conference on Neural Information Processing Systems Datasets and Benchmarks Track',
                'Official Venue Name': 'Thirty-seventh Conference on Neural Information Processing Systems Datasets and Benchmarks Track',
                'Abbreviated Venue Name': 'NeurIPS 2023',
                'Official Website URL': 'https://neurips.cc',
                'program_chair_emails': ['pc@neurips.cc'],
                'contact_email': 'pc@neurips.cc',
                'publication_chairs':'No, our venue does not have Publication Chairs',
                'ethics_chairs_and_reviewers': 'Yes, our venue has Ethics Chairs and Reviewers',
                'Venue Start Date': '2023/12/01',
                'Submission Deadline': due_date.strftime('%Y/%m/%d %H:%M'),
                'abstract_registration_deadline': first_date.strftime('%Y/%m/%d %H:%M'),
                'Location': 'Virtual',
                'submission_reviewer_assignment': 'Automatic',
                'How did you hear about us?': 'ML conferences',
                'Expected Submissions': '100',
                'hide_fields': ['keywords'],
                'submission_deadline_author_reorder': 'No'
            },
            forum=request_form.forum,
            invitation='openreview.net/Support/-/Request{}/Revision'.format(request_form.number),
            readers=['{}/Program_Chairs'.format('NeurIPS.cc/2023/Track/Datasets_and_Benchmarks'), 'openreview.net/Support'],
            referent=request_form.forum,
            replyto=request_form.forum,
            signatures=['~Program_NeurIPSChair1'],
            writers=[]
        )

        pc_client.post_note(venue_revision_note)
        
        helpers.await_queue()
        helpers.await_queue_edit(openreview_client, 'NeurIPS.cc/2023/Track/Datasets_and_Benchmarks/-/Post_Submission-0-0')
        helpers.await_queue_edit(openreview_client, 'NeurIPS.cc/2023/Track/Datasets_and_Benchmarks/-/Withdrawal-0-0')
        helpers.await_queue_edit(openreview_client, 'NeurIPS.cc/2023/Track/Datasets_and_Benchmarks/-/Desk_Rejection-0-0')
        helpers.await_queue_edit(openreview_client, 'NeurIPS.cc/2023/Track/Datasets_and_Benchmarks/-/Revision-0-0')

        notes = test_client.get_notes(content= { 'venueid': 'NeurIPS.cc/2023/Track/Datasets_and_Benchmarks/Submission' }, sort='number:desc')
        assert len(notes) == 5

        assert notes[0].readers == ['NeurIPS.cc/2023/Track/Datasets_and_Benchmarks', 'NeurIPS.cc/2023/Track/Datasets_and_Benchmarks/Submission5/Authors']
        assert notes[0].content['keywords']['readers'] == ['NeurIPS.cc/2023/Track/Datasets_and_Benchmarks', 'NeurIPS.cc/2023/Track/Datasets_and_Benchmarks/Submission5/Authors']

        assert test_client.get_invitation('NeurIPS.cc/2023/Track/Datasets_and_Benchmarks/Submission5/-/Withdrawal')
        assert test_client.get_invitation('NeurIPS.cc/2023/Track/Datasets_and_Benchmarks/Submission5/-/Desk_Rejection')
        assert test_client.get_invitation('NeurIPS.cc/2023/Track/Datasets_and_Benchmarks/Submission5/-/Revision')

        post_submission =  openreview_client.get_invitation('NeurIPS.cc/2023/Track/Datasets_and_Benchmarks/-/Post_Submission')
        assert 'authors' in post_submission.edit['note']['content']
        assert 'authorids' in post_submission.edit['note']['content']
        assert 'keywords' in post_submission.edit['note']['content']

        revision_inv =  test_client.get_invitation('NeurIPS.cc/2023/Track/Datasets_and_Benchmarks/Submission4/-/Revision')

        assert 'param' in revision_inv.edit['note']['content']['authorids']['value']
        assert 'regex' in revision_inv.edit['note']['content']['authorids']['value']['param']

        assert 'param' in revision_inv.edit['note']['content']['authors']['value']
        assert 'regex' in revision_inv.edit['note']['content']['authors']['value']['param']


        ## update submission
        revision_note = test_client.post_note_edit(invitation='NeurIPS.cc/2023/Track/Datasets_and_Benchmarks/Submission4/-/Revision',
            signatures=['NeurIPS.cc/2023/Track/Datasets_and_Benchmarks/Submission4/Authors'],
            note=openreview.api.Note(
                content={
                    'title': { 'value': 'Paper title 4 Updated' },
                    'abstract': { 'value': 'This is an abstract 4 updated' },
                    'authorids': { 'value': ['test@mail.com', 'andrew@google.com', 'peter@mail.com', 'melisa@google.com' ] },
                    'authors': { 'value': ['SomeFirstName User',  'Andrew Mc', 'Peter SomeLastName', 'Melisa Google' ] },
                    'keywords': { 'value': ['machine learning', 'nlp'] },
                }
            ))
        helpers.await_queue_edit(openreview_client, edit_id=revision_note['id'])

        author_group = openreview_client.get_group('NeurIPS.cc/2023/Track/Datasets_and_Benchmarks/Submission4/Authors')
        assert ['test@mail.com', 'andrew@google.com', 'peter@mail.com', 'melisa@google.com' ] == author_group.members

        pc_client_v2=openreview.api.OpenReviewClient(username='pc@neurips.cc', password=helpers.strong_password)

        ## try to edit a submission as a PC and check revision invitation is updated
        submissions = pc_client_v2.get_notes(invitation='NeurIPS.cc/2023/Track/Datasets_and_Benchmarks/-/Submission', sort='number:asc')
        submission = submissions[3]

        pc_revision = pc_client_v2.post_note_edit(invitation='NeurIPS.cc/2023/Track/Datasets_and_Benchmarks/-/PC_Revision',
            signatures=['NeurIPS.cc/2023/Track/Datasets_and_Benchmarks/Program_Chairs'],
            note=openreview.api.Note(
                id = submission.id,
                content = {
                    'title': { 'value': submission.content['title']['value'] + ' Version 2' },
                    'abstract': submission.content['abstract'],
                    'authorids': { 'value': submission.content['authorids']['value'] + ['celeste@yahoo.com'] },
                    'authors': { 'value': submission.content['authors']['value'] + ['Celeste NeurIPS'] },
                    'keywords': { 'value': ['machine learning', 'nlp'] }
                }
            ))

        helpers.await_queue_edit(openreview_client, edit_id=pc_revision['id'])        

        author_group = openreview_client.get_group('NeurIPS.cc/2023/Track/Datasets_and_Benchmarks/Submission4/Authors')
        assert ['test@mail.com', 'andrew@google.com', 'peter@mail.com', 'melisa@google.com', 'celeste@yahoo.com' ] == author_group.members

        revision_inv =  test_client.get_invitation('NeurIPS.cc/2023/Track/Datasets_and_Benchmarks/Submission4/-/Revision')

        assert 'param' in revision_inv.edit['note']['content']['authorids']['value']
        assert 'regex' in revision_inv.edit['note']['content']['authorids']['value']['param']

        assert 'param' in revision_inv.edit['note']['content']['authors']['value']
        assert 'regex' in revision_inv.edit['note']['content']['authors']['value']['param']        



