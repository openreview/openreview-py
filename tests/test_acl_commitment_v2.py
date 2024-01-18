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

class TestACLCommitment():

    def test_create_conference(self, client, openreview_client, helpers):

        now = datetime.datetime.utcnow()
        due_date = now + datetime.timedelta(days=3)

        # Post the request form note
        helpers.create_user('pc@aclweb.org', 'Program', 'ACLChair')
        pc_client = openreview.Client(username='pc@aclweb.org', password=helpers.strong_password)

        request_form_note = pc_client.post_note(openreview.Note(
            invitation='openreview.net/Support/-/Request_Form',
            signatures=['~Program_ACLChair1'],
            readers=[
                'openreview.net/Support',
                '~Program_ACLChair1'
            ],
            writers=[],
            content={
                'title': '60th Annual Meeting of the Association for Computational Linguistics',
                'Official Venue Name': '60th Annual Meeting of the Association for Computational Linguistics',
                'Abbreviated Venue Name': 'ACL 2024',
                'Official Website URL': 'https://2024.aclweb.org',
                'program_chair_emails': ['pc@aclweb.org'],
                'contact_email': 'pc@aclweb.org',
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
                'commitments_venue': 'Yes'
            }))

        helpers.await_queue()

        # Post a deploy note
        client.post_note(openreview.Note(
            content={'venue_id': 'aclweb.org/ACL/2024/Conference'},
            forum=request_form_note.forum,
            invitation='openreview.net/Support/-/Request{}/Deploy'.format(request_form_note.number),
            readers=['openreview.net/Support'],
            referent=request_form_note.forum,
            replyto=request_form_note.forum,
            signatures=['openreview.net/Support'],
            writers=['openreview.net/Support']
        ))

        helpers.await_queue()

        assert openreview_client.get_group('aclweb.org/ACL/2024/Conference')
        assert openreview_client.get_group('aclweb.org/ACL/2024/Conference/Senior_Area_Chairs')
        assert openreview_client.get_group('aclweb.org/ACL/2024/Conference/Area_Chairs')
        assert openreview_client.get_group('aclweb.org/ACL/2024/Conference/Reviewers')
        assert openreview_client.get_group('aclweb.org/ACL/2024/Conference/Authors')

        submission_invitation = openreview_client.get_invitation('aclweb.org/ACL/2024/Conference/-/Submission')
        assert submission_invitation
        assert submission_invitation.duedate
        assert submission_invitation.signatures == ['~Super_User1']
        assert 'paper_link' in submission_invitation.edit['note']['content']
        assert submission_invitation.preprocess

        assert openreview_client.get_invitation('aclweb.org/ACL/2024/Conference/Reviewers/-/Expertise_Selection')
        assert openreview_client.get_invitation('aclweb.org/ACL/2024/Conference/Area_Chairs/-/Expertise_Selection')
        assert openreview_client.get_invitation('aclweb.org/ACL/2024/Conference/Senior_Area_Chairs/-/Expertise_Selection')

        pc_client.post_note(openreview.Note(
            invitation=f'openreview.net/Support/-/Request{request_form_note.number}/Revision',
            forum=request_form_note.id,
            readers=['aclweb.org/ACL/2024/Conference/Program_Chairs', 'openreview.net/Support'],
            referent=request_form_note.id,
            replyto=request_form_note.id,
            signatures=['~Program_ACLChair1'],
            writers=[],
            content={
                'title': '60th Annual Meeting of the Association for Computational Linguistics',
                'Official Venue Name': '60th Annual Meeting of the Association for Computational Linguistics',
                'Abbreviated Venue Name': 'ACL 2024',
                'Official Website URL': 'https://2024.aclweb.org',
                'program_chair_emails': ['pc@aclweb.org'],
                'contact_email': 'pc@aclweb.org',
                'publication_chairs':'No, our venue does not have Publication Chairs',
                'Venue Start Date': '2024/07/01',
                'Submission Deadline': due_date.strftime('%Y/%m/%d'),
                'Location': 'Virtual',
                'submission_reviewer_assignment': 'Automatic',
                'How did you hear about us?': 'ML conferences',
                'Expected Submissions': '100',
                'use_recruitment_template': 'Yes',
                'Additional Submission Options': {
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
                'remove_submission_options': ['TL;DR']
            }
        ))
        helpers.await_queue()

        submission_invitation = openreview_client.get_invitation('aclweb.org/ACL/2024/Conference/-/Submission')
        assert submission_invitation
        assert submission_invitation.signatures == ['~Super_User1']
        assert 'supplementary_material' in submission_invitation.edit['note']['content']
        assert 'TLDR' not in submission_invitation.edit['note']['content']
        assert 'paper_link' in submission_invitation.edit['note']['content']
        assert submission_invitation.preprocess