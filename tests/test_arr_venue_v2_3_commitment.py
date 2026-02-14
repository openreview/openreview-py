import time
import openreview
import pytest
import datetime
import re
import random
import os
import csv
import sys
from copy import deepcopy
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from openreview.venue import matching
from openreview.stages.arr_content import (
    arr_submission_content,
    arr_withdrawal_content,
    hide_fields,
    hide_fields_from_public,
    arr_registration_task_forum,
    arr_registration_task,
    arr_content_license_task_forum,
    arr_content_license_task,
    arr_max_load_task_forum,
    arr_reviewer_max_load_task,
    arr_ac_max_load_task,
    arr_sac_max_load_task
)
# API2 template from ICML
class TestARRVenueV2Commitment():

    def test_commitment_venue(self, client, test_client, openreview_client, helpers):

        now = datetime.datetime.now()
        due_date = now + datetime.timedelta(days=3)

        # Post the request form note
        helpers.create_user('pc@c3nlp.org', 'Program', 'NLPChair')
        pc_client = openreview.Client(username='pc@c3nlp.org', password=helpers.strong_password)

        request_form_note = pc_client.post_note(openreview.Note(
            invitation='openreview.net/Support/-/Request_Form',
            signatures=['~Program_NLPChair1'],
            readers=[
                'openreview.net/Support',
                '~Program_NLPChair1'
            ],
            writers=[],
            content={
                'title': '60th Annual Meeting of the Association for Computational Linguistics',
                'Official Venue Name': '60th Annual Meeting of the Association for Computational Linguistics',
                'Abbreviated Venue Name': 'ACL 2024',
                'Official Website URL': 'https://2024.aclweb.org',
                'program_chair_emails': ['pc@c3nlp.org'],
                'contact_email': 'pc@c3nlp.org',
                'publication_chairs':'No, our venue does not have Publication Chairs',
                'Area Chairs (Metareviewers)': 'Yes, our venue has Area Chairs',
                'senior_area_chairs': 'Yes, our venue has Senior Area Chairs',
                'ethics_chairs_and_reviewers': 'No, our venue does not have Ethics Chairs and Reviewers',
                'Venue Start Date': '2024/07/01',
                'Submission Deadline': due_date.strftime('%Y/%m/%d'),
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
                'use_recruitment_template': 'Yes',
                'api_version': '2',
                'submission_license': ['CC BY 4.0'],
                'commitments_venue': 'Yes',
                'venue_organizer_agreement': [
                    'OpenReview natively supports a wide variety of reviewing workflow configurations. However, if we want significant reviewing process customizations or experiments, we will detail these requests to the OpenReview staff at least three months in advance.',
                    'We will ask authors and reviewers to create an OpenReview Profile at least two weeks in advance of the paper submission deadlines.',
                    'When assembling our group of reviewers and meta-reviewers, we will only include email addresses or OpenReview Profile IDs of people we know to have authored publications relevant to our venue.  (We will not solicit new reviewers using an open web form, because unfortunately some malicious actors sometimes try to create "fake ids" aiming to be assigned to review their own paper submissions.)',
                    'We acknowledge that, if our venue\'s reviewing workflow is non-standard, or if our venue is expecting more than a few hundred submissions for any one deadline, we should designate our own Workflow Chair, who will read the OpenReview documentation and manage our workflow configurations throughout the reviewing process.',
                    'We acknowledge that OpenReview staff work Monday-Friday during standard business hours US Eastern time, and we cannot expect support responses outside those times.  For this reason, we recommend setting submission and reviewing deadlines Monday through Thursday.',
                    'We will treat the OpenReview staff with kindness and consideration.'
                ]
            }))

        helpers.await_queue()

        # Post a deploy note
        client.post_note(openreview.Note(
            content={'venue_id': 'aclweb.org/ACL/2024/Workshop/C3NLP_ARR_Commitment'},
            forum=request_form_note.forum,
            invitation='openreview.net/Support/-/Request{}/Deploy'.format(request_form_note.number),
            readers=['openreview.net/Support'],
            referent=request_form_note.forum,
            replyto=request_form_note.forum,
            signatures=['openreview.net/Support'],
            writers=['openreview.net/Support']
        ))

        helpers.await_queue()

        assert openreview_client.get_group('aclweb.org/ACL/2024/Workshop/C3NLP_ARR_Commitment')
        assert openreview_client.get_group('aclweb.org/ACL/2024/Workshop/C3NLP_ARR_Commitment/Senior_Area_Chairs')
        assert openreview_client.get_group('aclweb.org/ACL/2024/Workshop/C3NLP_ARR_Commitment/Area_Chairs')
        assert openreview_client.get_group('aclweb.org/ACL/2024/Workshop/C3NLP_ARR_Commitment/Reviewers')
        assert openreview_client.get_group('aclweb.org/ACL/2024/Workshop/C3NLP_ARR_Commitment/Authors')

        submission_invitation = openreview_client.get_invitation('aclweb.org/ACL/2024/Workshop/C3NLP_ARR_Commitment/-/Submission')
        assert submission_invitation
        assert submission_invitation.duedate
        assert submission_invitation.signatures == ['~Super_User1']
        assert 'paper_link' in submission_invitation.edit['note']['content']
        assert submission_invitation.preprocess

        assert openreview_client.get_invitation('aclweb.org/ACL/2024/Workshop/C3NLP_ARR_Commitment/Reviewers/-/Expertise_Selection')
        assert openreview_client.get_invitation('aclweb.org/ACL/2024/Workshop/C3NLP_ARR_Commitment/Area_Chairs/-/Expertise_Selection')
        assert openreview_client.get_invitation('aclweb.org/ACL/2024/Workshop/C3NLP_ARR_Commitment/Senior_Area_Chairs/-/Expertise_Selection')

        pc_client.post_note(openreview.Note(
            invitation=f'openreview.net/Support/-/Request{request_form_note.number}/Revision',
            forum=request_form_note.id,
            readers=['aclweb.org/ACL/2024/Workshop/C3NLP_ARR_Commitment/Program_Chairs', 'openreview.net/Support'],
            referent=request_form_note.id,
            replyto=request_form_note.id,
            signatures=['~Program_NLPChair1'],
            writers=[],
            content={
                'title': '60th Annual Meeting of the Association for Computational Linguistics',
                'Official Venue Name': '60th Annual Meeting of the Association for Computational Linguistics',
                'Abbreviated Venue Name': 'ACL 2024',
                'Official Website URL': 'https://2024.aclweb.org',
                'program_chair_emails': ['pc@c3nlp.org'],
                'contact_email': 'pc@c3nlp.org',
                'publication_chairs':'No, our venue does not have Publication Chairs',
                'Venue Start Date': '2024/07/01',
                'Submission Deadline': due_date.strftime('%Y/%m/%d'),
                'Location': 'Virtual',
                'submission_reviewer_assignment': 'Automatic',
                'How did you hear about us?': 'ML conferences',
                'Expected Submissions': '100',
                'use_recruitment_template': 'Yes',
                'Additional Submission Options': {
                    "paper_link": {
                        'value': {
                        'param': {
                            'type': 'string',
                            'regex': 'https:\/\/openreview\.net\/forum\?id=.*',
                            'mismatchError': 'must be a valid link to an OpenReview submission: https://openreview.net/forum?id=...'
                        }
                    },
                        'description': 'This is a different description.',
                        'order': 7
                    },
                    "supplementary_material": {
                        "value": {
                            "param": {
                                "type": "file",
                                "extensions": [
                                    "zip",
                                    "pdf",
                                    "tgz",
                                    "gz"
                                ],
                                "maxSize": 100,
                                "optional": True,
                                "deletable": True
                            }
                        },
                        "description": "All supplementary material must be self-contained and zipped into a single file. Note that supplementary material will be visible to reviewers and the public throughout and after the review period, and ensure all material is anonymized. The maximum file size is 100MB.",
                        "order": 8
                    }
                },
                'remove_submission_options': ['TL;DR', 'pdf']
            }
        ))
        helpers.await_queue()

        submission_invitation = openreview_client.get_invitation('aclweb.org/ACL/2024/Workshop/C3NLP_ARR_Commitment/-/Submission')
        assert submission_invitation
        assert submission_invitation.signatures == ['~Super_User1']
        assert 'supplementary_material' in submission_invitation.edit['note']['content']
        assert 'TLDR' not in submission_invitation.edit['note']['content']
        assert 'paper_link' in submission_invitation.edit['note']['content']
        assert submission_invitation.edit['note']['content']['paper_link']['description'] == 'This is a different description.'
        assert submission_invitation.preprocess

        ## post ARR august submissions
        august_submissions = openreview_client.get_notes(invitation='aclweb.org/ACL/ARR/2023/August/-/Submission')

        test_client = openreview.api.OpenReviewClient(token=test_client.token)
        for submission in august_submissions:
            test_client.post_note_edit(invitation='aclweb.org/ACL/2024/Workshop/C3NLP_ARR_Commitment/-/Submission',
                    signatures=['~SomeFirstName_User1'],
                    note=openreview.api.Note(
                    content = {
                        'title': { 'value': submission.content['title']['value'] },
                        'abstract': { 'value': submission.content['abstract']['value'] },
                        'authorids': { 'value': submission.content['authorids']['value'] },
                        'authors': { 'value': submission.content['authors']['value'] },
                        'keywords': { 'value': ['machine learning'] },
                        'paper_link': { 'value': 'https://openreview.net/forum?id=' + submission.id },
                    }
                ))
        
        pc_client_v2 = openreview.api.OpenReviewClient(username='pc@c3nlp.org', password=helpers.strong_password)
        notes = pc_client_v2.get_notes(invitation='aclweb.org/ACL/ARR/2023/August/-/Submission', number=3)
        assert len(notes) == 0

        openreview.arr.ARR.process_commitment_venue(openreview_client, 'aclweb.org/ACL/2024/Workshop/C3NLP_ARR_Commitment', get_previous_url_submission=True)
        
        openreview_client.flush_members_cache('pc@c3nlp.org')
        
        august_submissions = openreview_client.get_notes(invitation='aclweb.org/ACL/ARR/2023/August/-/Submission', sort='number:asc')
        june_submissions = openreview_client.get_notes(invitation='aclweb.org/ACL/ARR/2023/June/-/Submission', sort='number:asc')

        # Submission # 1
        assert 'aclweb.org/ACL/ARR/2023/August/Submission1/Commitment_Readers' in august_submissions[0].readers
        assert 'aclweb.org/ACL/ARR/2023/June/Submission1/Commitment_Readers' in june_submissions[0].readers
        assert 'aclweb.org/ACL/2024/Workshop/C3NLP_ARR_Commitment' in openreview_client.get_group('aclweb.org/ACL/ARR/2023/August/Submission1/Commitment_Readers').members
        assert 'aclweb.org/ACL/2024/Workshop/C3NLP_ARR_Commitment' in openreview_client.get_group('aclweb.org/ACL/ARR/2023/June/Submission1/Commitment_Readers').members
        assert 'aclweb.org/ACL/2024/Workshop/C3NLP_ARR_Commitment' not in openreview_client.get_group('aclweb.org/ACL/ARR/2023/August/Submission1/Reviewers').deanonymizers
        assert 'aclweb.org/ACL/2024/Workshop/C3NLP_ARR_Commitment' not in openreview_client.get_group('aclweb.org/ACL/ARR/2023/August/Submission1/Area_Chairs').deanonymizers
        assert 'aclweb.org/ACL/2024/Workshop/C3NLP_ARR_Commitment' not in openreview_client.get_group('aclweb.org/ACL/ARR/2023/June/Submission1/Reviewers').deanonymizers
        assert 'aclweb.org/ACL/2024/Workshop/C3NLP_ARR_Commitment' not in openreview_client.get_group('aclweb.org/ACL/ARR/2023/June/Submission1/Area_Chairs').deanonymizers

        # Submission # 2
        assert august_submissions[1].readers == ['everyone']
        assert 'aclweb.org/ACL/ARR/2023/June/Submission2/Commitment_Readers' in june_submissions[1].readers
        assert 'aclweb.org/ACL/2024/Workshop/C3NLP_ARR_Commitment' in openreview_client.get_group('aclweb.org/ACL/ARR/2023/August/Submission2/Commitment_Readers').members
        assert 'aclweb.org/ACL/2024/Workshop/C3NLP_ARR_Commitment' in openreview_client.get_group('aclweb.org/ACL/ARR/2023/June/Submission2/Commitment_Readers').members
        assert 'aclweb.org/ACL/2024/Workshop/C3NLP_ARR_Commitment' not in openreview_client.get_group('aclweb.org/ACL/ARR/2023/August/Submission2/Reviewers').deanonymizers
        assert 'aclweb.org/ACL/2024/Workshop/C3NLP_ARR_Commitment' not in openreview_client.get_group('aclweb.org/ACL/ARR/2023/August/Submission2/Area_Chairs').deanonymizers
        assert 'aclweb.org/ACL/2024/Workshop/C3NLP_ARR_Commitment' not in openreview_client.get_group('aclweb.org/ACL/ARR/2023/June/Submission2/Reviewers').deanonymizers
        assert 'aclweb.org/ACL/2024/Workshop/C3NLP_ARR_Commitment' not in openreview_client.get_group('aclweb.org/ACL/ARR/2023/June/Submission2/Area_Chairs').deanonymizers

        # Check June reviews
        june_reviews = openreview_client.get_notes(invitation='aclweb.org/ACL/ARR/2023/June/Submission2/-/Official_Review')
        assert len(june_reviews) == 2
        assert 'aclweb.org/ACL/ARR/2023/June/Submission2/Commitment_Readers' in june_reviews[0].readers
        assert 'aclweb.org/ACL/ARR/2023/June/Submission2/Commitment_Readers' in june_reviews[1].readers
        # Check June meta review
        june_meta_reviews = openreview_client.get_notes(invitation='aclweb.org/ACL/ARR/2023/June/Submission2/-/Meta_Review')
        assert len(june_meta_reviews) == 1
        assert 'aclweb.org/ACL/ARR/2023/June/Submission2/Commitment_Readers' in june_meta_reviews[0].readers
        
        # Submission # 3
        assert 'aclweb.org/ACL/ARR/2023/August/Submission3/Commitment_Readers' in august_submissions[2].readers
        assert 'aclweb.org/ACL/ARR/2023/June/Submission3/Commitment_Readers' in june_submissions[2].readers
        assert 'aclweb.org/ACL/2024/Workshop/C3NLP_ARR_Commitment' in openreview_client.get_group('aclweb.org/ACL/ARR/2023/August/Submission3/Commitment_Readers').members
        assert 'aclweb.org/ACL/2024/Workshop/C3NLP_ARR_Commitment' in openreview_client.get_group('aclweb.org/ACL/ARR/2023/June/Submission3/Commitment_Readers').members
        assert 'aclweb.org/ACL/2024/Workshop/C3NLP_ARR_Commitment' not in openreview_client.get_group('aclweb.org/ACL/ARR/2023/August/Submission3/Reviewers').deanonymizers
        assert 'aclweb.org/ACL/2024/Workshop/C3NLP_ARR_Commitment' not in openreview_client.get_group('aclweb.org/ACL/ARR/2023/August/Submission3/Area_Chairs').deanonymizers
        assert 'aclweb.org/ACL/2024/Workshop/C3NLP_ARR_Commitment' not in openreview_client.get_group('aclweb.org/ACL/ARR/2023/June/Submission3/Reviewers').deanonymizers
        assert 'aclweb.org/ACL/2024/Workshop/C3NLP_ARR_Commitment' not in openreview_client.get_group('aclweb.org/ACL/ARR/2023/June/Submission3/Area_Chairs').deanonymizers
        # Check August reviews
        august_reviews = openreview_client.get_notes(invitation='aclweb.org/ACL/ARR/2023/August/Submission3/-/Official_Review')
        assert len(august_reviews) == 1
        assert 'aclweb.org/ACL/ARR/2023/August/Submission3/Commitment_Readers' in august_reviews[0].readers
        # Check June reviews
        june_reviews = openreview_client.get_notes(invitation='aclweb.org/ACL/ARR/2023/June/Submission3/-/Official_Review')
        assert len(june_reviews) == 1
        assert 'aclweb.org/ACL/ARR/2023/June/Submission3/Commitment_Readers' in june_reviews[0].readers        

        notes = pc_client_v2.get_notes(invitation='aclweb.org/ACL/ARR/2023/August/-/Submission', number=3)
        assert len(notes) == 1
        submssion3 = notes[0]

        notes = pc_client_v2.get_notes(invitation='aclweb.org/ACL/ARR/2023/August/Submission3/-/Official_Review')
        assert len(notes) == 1

        notes = pc_client_v2.get_notes(forum=submssion3.id, domain='aclweb.org/ACL/ARR/2023/August')
        assert len(notes) == 5 # submission + review + 3 reports
        
        venue = openreview.helpers.get_conference(client, request_form_note.forum)
        venue.invitation_builder.expire_invitation('aclweb.org/ACL/2024/Workshop/C3NLP_ARR_Commitment/Senior_Area_Chairs/-/Submission_Group')
        venue.invitation_builder.expire_invitation('aclweb.org/ACL/2024/Workshop/C3NLP_ARR_Commitment/Area_Chairs/-/Submission_Group')
        venue.invitation_builder.expire_invitation('aclweb.org/ACL/2024/Workshop/C3NLP_ARR_Commitment/Reviewers/-/Submission_Group')        
        venue.invitation_builder.expire_invitation('aclweb.org/ACL/2024/Workshop/C3NLP_ARR_Commitment/-/Post_Submission')
        venue.invitation_builder.expire_invitation('aclweb.org/ACL/2024/Workshop/C3NLP_ARR_Commitment/-/Desk_Rejection')                
        venue.invitation_builder.expire_invitation('aclweb.org/ACL/2024/Workshop/C3NLP_ARR_Commitment/-/Withdrawal')        
