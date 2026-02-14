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
from arr_v2_test_bootstrap import ensure_prior_methods
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

WORKFLOW_TEST_ORDER = [
    'test_august_cycle',
    'test_june_cycle',
    'test_ac_recruitment',
    'test_reviewer_recruitment',
    'test_submission_preprocess',
    'test_no_assignment_preprocess',
    'test_copy_members',
    'test_unavailability_process_functions',
    'test_reviewer_tasks',
    'test_submissions',
    'test_submitted_author_form',
    'test_post_submission',
    'test_metadata_edit',
    'test_setup_matching',
    'test_resubmission_and_track_matching_data',
    'test_sae_ae_assignments',
]
WORKFLOW_COMPLETED_METHODS = set()

@pytest.fixture(autouse=True)
def _ensure_workflow_prerequisites(request, client, openreview_client, helpers, test_client, request_page, selenium):
    current_method = request.function.__name__
    if request.instance and current_method in WORKFLOW_TEST_ORDER:
        ensure_prior_methods(
            instance=request.instance,
            ordered_methods=WORKFLOW_TEST_ORDER,
            completed_methods=WORKFLOW_COMPLETED_METHODS,
            current_method=current_method,
            fixture_values={
                'client': client,
                'openreview_client': openreview_client,
                'helpers': helpers,
                'test_client': test_client,
                'request_page': request_page,
                'selenium': selenium
            }
        )
    yield
    if current_method in WORKFLOW_TEST_ORDER:
        WORKFLOW_COMPLETED_METHODS.add(current_method)

# API2 template from ICML
class TestARRVenueV2Workflow():

    def test_august_cycle(self, client, openreview_client, helpers, test_client, request_page, selenium):

        now = datetime.datetime.now()
        due_date = now + datetime.timedelta(days=3)

        # Post the request form note
        helpers.create_user('pc@aclrollingreview.org', 'Program', 'ARRChair')
        pc_client = openreview.Client(username='pc@aclrollingreview.org', password=helpers.strong_password)
        pc_client_v2 = openreview.api.OpenReviewClient(username='pc@aclrollingreview.org', password=helpers.strong_password)

        sac_client = helpers.create_user('sac1@aclrollingreview.com', 'SAC', 'ARROne')
        helpers.create_user('sac2@aclrollingreview.com', 'SAC', 'ARRTwo')
        helpers.create_user('sac3@aclrollingreview.com', 'SAC', 'ARRThree')
        helpers.create_user('ec1@aclrollingreview.com', 'EthicsChair', 'ARROne')
        helpers.create_user('ac1@aclrollingreview.com', 'AC', 'ARROne')
        helpers.create_user('ac2@aclrollingreview.com', 'AC', 'ARRTwo')
        helpers.create_user('ac3@aclrollingreview.com', 'AC', 'ARRThree')
        #helpers.create_user('reviewer2@aclrollingreview.com', 'Reviewer', 'ARRTwo')
        helpers.create_user('reviewer2-1@aclrollingreview.com', 'Reviewer', 'ARRTwoMerge')
        helpers.create_user('reviewer3@aclrollingreview.com', 'Reviewer', 'ARRThree')
        helpers.create_user('reviewer4@aclrollingreview.com', 'Reviewer', 'ARRFour')
        helpers.create_user('reviewer5@aclrollingreview.com', 'Reviewer', 'ARRFive')
        helpers.create_user('reviewer6@aclrollingreview.com', 'Reviewer', 'ARRSix')
        helpers.create_user('reviewer7@aclrollingreview.com', 'Reviewer', 'ARRSeven') # User with conflict
        helpers.create_user('reviewerna@aclrollingreview.com', 'Reviewer', 'ARRNA') ## User for unavailability with N/A
        helpers.create_user('reviewerethics@aclrollingreview.com', 'EthicsReviewer', 'ARROne')

        # Manually create Reviewer ARROne as having more than 5 *CL main publications and full professor
        fullname = f'Reviewer ARROne'
        res = openreview_client.register_user(email = 'reviewer1@aclrollingreview.com', fullname = fullname, password = helpers.strong_password)
        username = res.get('id')
        profile_content={
            'names': [
                    {
                        'fullname': fullname,
                        'username': username,
                        'preferred': False
                    },
                    {
                        'fullname': 'Reviewer Alternate ARROne',
                        'preferred': True
                    }
                ],
            'emails': ['reviewer1@aclrollingreview.com'],
            'preferredEmail': 'reviewer1@aclrollingreview.com',
            'homepage': f"https://{fullname.replace(' ', '')}{int(time.time())}.openreview.net",
        }
        profile_content['history'] = [{
            'position': 'Full Professor',
            'start': 2017,
            'end': None,
            'institution': {
                'country': 'US',
                'domain': 'aclrollingreview.com',
            }
        }]
        rev_client = openreview.api.OpenReviewClient(baseurl = 'http://localhost:3001')
        rev_client.activate_user('reviewer1@aclrollingreview.com', profile_content)

        profile = rev_client.get_profile('~Reviewer_ARROne1')
        assert profile.content['names'][0]['username'] == '~Reviewer_ARROne1'
        assert profile.content['names'][1]['username'] == '~Reviewer_Alternate_ARROne1'

        for i in range(1, 9):
            edit = rev_client.post_note_edit(
                invitation='openreview.net/Archive/-/Direct_Upload',
                signatures=['~Reviewer_ARROne1'],
                note = openreview.api.Note(
                    pdate = openreview.tools.datetime_millis(datetime.datetime(2019, 4, 30)),
                    content = {
                        'title': { 'value': f'Paper title {i}' },
                        'abstract': { 'value': f'Paper abstract {i}' },
                        'authors': { 'value': ['Reviewer ARROne', 'Test2 Client'] },
                        'authorids': { 'value': ['~Reviewer_ARROne1', 'test2@mail.com'] },
                        'venue': { 'value': 'EMNLP 2024 Main' }
                    },
                    license = 'CC BY-SA 4.0'
            ))
            openreview_client.post_note_edit(
                invitation='openreview.net/-/Edit',
                readers=['openreview.net'],
                writers=['openreview.net'],
                signatures=['openreview.net'],
                note=openreview.api.Note(
                    id = edit['note']['id'],
                    content = {
                        'venueid': { 'value': 'EMNLP/2024/Conference' }
                    }
                )
            )

        # Manually create Reviewer ARRTwo as having more than 5 non-*CL main publications
        fullname = f'Reviewer ARRTwo'
        res = openreview_client.register_user(email = 'reviewer2@aclrollingreview.com', fullname = fullname, password = helpers.strong_password)
        username = res.get('id')
        profile_content={
            'names': [
                    {
                        'fullname': fullname,
                        'username': username,
                        'preferred': False
                    },
                    {
                        'fullname': 'Reviewer Alternate ARRTwo',
                        'preferred': True
                    }
                ],
            'emails': ['reviewer2@aclrollingreview.com'],
            'preferredEmail': 'reviewer2@aclrollingreview.com',
            'homepage': f"https://{fullname.replace(' ', '')}{int(time.time())}.openreview.net",
        }
        profile_content['history'] = [{
            'position': 'Full Professor',
            'start': 2017,
            'end': None,
            'institution': {
                'country': 'US',
                'domain': 'aclrollingreview.com',
            }
        }]
        rev_client = openreview.api.OpenReviewClient(baseurl = 'http://localhost:3001')
        rev_client.activate_user('reviewer2@aclrollingreview.com', profile_content)

        profile = rev_client.get_profile('~Reviewer_ARRTwo1')
        assert profile.content['names'][0]['username'] == '~Reviewer_ARRTwo1'
        assert profile.content['names'][1]['username'] == '~Reviewer_Alternate_ARRTwo1'

        for i in range(1, 9):
            rev_client.post_note_edit(
                invitation='openreview.net/Archive/-/Direct_Upload',
                signatures=['~Reviewer_ARRTwo1'],
                note = openreview.api.Note(
                    pdate = openreview.tools.datetime_millis(datetime.datetime(2019, 4, 30)),
                    content = {
                        'title': { 'value': f'Paper title {i}' },
                        'abstract': { 'value': f'Paper abstract {i}' },
                        'authors': { 'value': ['Reviewer ARRTwo', 'Test2 Client'] },
                        'authorids': { 'value': ['~Reviewer_ARRTwo1', 'test2@mail.com'] },
                        'venue': { 'value': 'Arxiv' }
                    },
                    license = 'CC BY-SA 4.0'
            ))

        request_form_note = pc_client.post_note(openreview.Note(
            invitation='openreview.net/Support/-/Request_Form',
            signatures=['~Program_ARRChair1'],
            readers=[
                'openreview.net/Support',
                '~Program_ARRChair1'
            ],
            writers=[],
            content={
                'title': 'ACL Rolling Review 2023 - August',
                'Official Venue Name': 'ACL Rolling Review 2023 - August',
                'Abbreviated Venue Name': 'ARR - August 2023',
                'Official Website URL': 'http://aclrollingreview.org',
                'program_chair_emails': ['editors@aclrollingreview.org', 'pc@aclrollingreview.org'],
                'contact_email': 'editors@aclrollingreview.org',
                'Area Chairs (Metareviewers)': 'Yes, our venue has Area Chairs',
                'senior_area_chairs': 'Yes, our venue has Senior Area Chairs',
                'senior_area_chairs_assignment': 'Submissions',
                'ethics_chairs_and_reviewers': 'Yes, our venue has Ethics Chairs and Reviewers',
                'publication_chairs':'No, our venue does not have Publication Chairs',
                'Venue Start Date': '2023/08/01',
                'Submission Deadline': due_date.strftime('%Y/%m/%d'),
                'Location': 'Virtual',
                'submission_reviewer_assignment': 'Automatic',
                'Author and Reviewer Anonymity': 'Double-blind',
                'reviewer_identity': ['Program Chairs', 'Assigned Senior Area Chair', 'Assigned Area Chair', 'Assigned Reviewers'],
                'area_chair_identity': ['Program Chairs', 'Assigned Senior Area Chair', 'Assigned Area Chair', 'Assigned Reviewers'],
                'senior_area_chair_identity': ['Program Chairs', 'Assigned Senior Area Chair', 'Assigned Area Chair', 'Assigned Reviewers'],
                'Open Reviewing Policy': 'Submissions and reviews should both be private.',
                'submission_readers': 'Assigned program committee (assigned reviewers, assigned area chairs, assigned senior area chairs if applicable)',
                'How did you hear about us?': 'ML conferences',
                'Expected Submissions': '100',
                'use_recruitment_template': 'Yes',
                'api_version': '2',
                'submission_license': ['CC BY-SA 4.0'],
                "preferred_emails_groups": [
                    "aclweb.org/ACL/ARR/2023/August/Senior_Area_Chairs",
                    "aclweb.org/ACL/ARR/2023/August/Area_Chairs",
                    "aclweb.org/ACL/ARR/2023/August/Reviewers"
                ],
                'comment_notification_threshold': '3',
                'venue_organizer_agreement': [
                    'OpenReview natively supports a wide variety of reviewing workflow configurations. However, if we want significant reviewing process customizations or experiments, we will detail these requests to the OpenReview staff at least three months in advance.',
                    'We will ask authors and reviewers to create an OpenReview Profile at least two weeks in advance of the paper submission deadlines.',
                    'When assembling our group of reviewers and meta-reviewers, we will only include email addresses or OpenReview Profile IDs of people we know to have authored publications relevant to our venue.  (We will not solicit new reviewers using an open web form, because unfortunately some malicious actors sometimes try to create "fake ids" aiming to be assigned to review their own paper submissions.)',
                    'We acknowledge that, if our venue\'s reviewing workflow is non-standard, or if our venue is expecting more than a few hundred submissions for any one deadline, we should designate our own Workflow Chair, who will read the OpenReview documentation and manage our workflow configurations throughout the reviewing process.',
                    'We acknowledge that OpenReview staff work Monday-Friday during standard business hours US Eastern time, and we cannot expect support responses outside those times.  For this reason, we recommend setting submission and reviewing deadlines Monday through Thursday.',
                    'We will treat the OpenReview staff with kindness and consideration.'
                ],
                'senior_area_chair_roles': ['Senior_Area_Chairs'],
                'area_chair_roles': ['Area_Chairs'],
                'reviewer_roles': ['Reviewers'],
            }))

        helpers.await_queue()

        # Post a deploy note
        august_deploy_edit = client.post_note(openreview.Note(
            content={'venue_id': 'aclweb.org/ACL/ARR/2023/August'},
            forum=request_form_note.forum,
            invitation='openreview.net/Support/-/Request{}/Deploy'.format(request_form_note.number),
            readers=['openreview.net/Support'],
            referent=request_form_note.forum,
            replyto=request_form_note.forum,
            signatures=['openreview.net/Support'],
            writers=['openreview.net/Support']
        ))

        helpers.await_queue_edit(client, invitation='openreview.net/Support/-/Request{}/Deploy'.format(request_form_note.number))

        group = openreview_client.get_group('aclweb.org/ACL/ARR/2023/August')
        assert group
        assert 'submission_assignment_max_reviewers' not in group.content
        assert openreview_client.get_group('aclweb.org/ACL/ARR/2023/August/Senior_Area_Chairs')
        assert openreview_client.get_group('aclweb.org/ACL/ARR/2023/August/Area_Chairs')
        assert openreview_client.get_group('aclweb.org/ACL/ARR/2023/August/Reviewers')
        assert openreview_client.get_group('aclweb.org/ACL/ARR/2023/August/Authors')
        assert openreview_client.get_group('aclweb.org/ACL/ARR/2023/August/Preferred_Emails_Readers')

        assert 'Emergency_Score' in openreview_client.get_group('aclweb.org/ACL/ARR/2023/August/Program_Chairs').web
        assert 'Emergency_Score' in openreview_client.get_group('aclweb.org/ACL/ARR/2023/August/Senior_Area_Chairs').web
        assert 'Emergency_Score' in openreview_client.get_group('aclweb.org/ACL/ARR/2023/August/Area_Chairs').web

        assert '~Program_ARRChair1' in openreview_client.get_group('aclweb.org/ACL/ARR/2023/August').impersonators

        submission_invitation = openreview_client.get_invitation('aclweb.org/ACL/ARR/2023/August/-/Submission')
        assert submission_invitation
        assert submission_invitation.duedate

        withdrawal_invitation = pc_client_v2.get_invitation('aclweb.org/ACL/ARR/2023/August/-/Withdrawal')
        assert withdrawal_invitation.edit['invitation']['edit']['note']['content'] == arr_withdrawal_content
        assert 'confirm_need_to_withdraw' in withdrawal_invitation.edit['invitation']['edit']['note']['content']
        assert 'confirm_penalty_rules' in withdrawal_invitation.edit['invitation']['edit']['note']['content']        

        assert openreview_client.get_invitation('aclweb.org/ACL/ARR/2023/August/Reviewers/-/Expertise_Selection')

        post_submission_invitation = openreview_client.get_invitation('aclweb.org/ACL/ARR/2023/August/-/Post_Submission')
        assert 'TLDR' in post_submission_invitation.edit['note']['content']
        assert 'preprint' in post_submission_invitation.edit['note']['content']
        assert 'existing_preprints' in post_submission_invitation.edit['note']['content']
        assert 'consent_to_share_data' in post_submission_invitation.edit['note']['content']
        assert 'consent_to_share_submission_details' in post_submission_invitation.edit['note']['content']
        assert 'Association_for_Computational_Linguistics_-_Blind_Submission_License_Agreement' in post_submission_invitation.edit['note']['content']
        assert 'preprint_status' in post_submission_invitation.edit['note']['content']

        request_page(selenium, 'http://localhost:3030/group?id=aclweb.org/ACL/ARR/2023/August', pc_client, wait_for_element='header')
        header_div = selenium.find_element(By.ID, 'header')
        assert header_div
        location_tag = header_div.find_element(By.CLASS_NAME, 'venue-location')
        assert location_tag and location_tag.text == 'Virtual'
        description = header_div.find_element(By.CLASS_NAME, 'description')
        assert description and 'Please see the venue website for more information.' in description.text        

        sac_client.post_note_edit(
            invitation='openreview.net/Archive/-/Direct_Upload',
            signatures=['~SAC_ARROne1'],
            note = openreview.api.Note(
                pdate = openreview.tools.datetime_millis(datetime.datetime(2019, 4, 30)),
                content = {
                    'title': { 'value': 'Paper title 1' },
                    'abstract': { 'value': 'Paper abstract 1' },
                    'authors': { 'value': ['SAC ARR', 'Test2 Client'] },
                    'authorids': { 'value': ['~SAC_ARROne1', 'test2@mail.com'] },
                    'venue': { 'value': 'Arxiv' }
                },
                license = 'CC BY-SA 4.0'
        ))

        archive_note = sac_client.post_note_edit(
            invitation='openreview.net/Archive/-/Direct_Upload',
            signatures=['~SAC_ARROne1'],
            note = openreview.api.Note(
                pdate = openreview.tools.datetime_millis(datetime.datetime(2019, 4, 30)),
                content = {
                    'title': { 'value': 'Paper title 2' },
                    'abstract': { 'value': 'Paper abstract 2' },
                    'authors': { 'value': ['SAC ARR', 'Test2 Client'] },
                    'authorids': { 'value': ['~SAC_ARROne1', 'test2@mail.com'] },
                    'venue': { 'value': 'Arxiv' }
                },
                license = 'CC BY-SA 4.0'
        ))

        # Update submission fields
        ## override file size for tests
        arr_submission_content['software']['value']['param']['maxSize'] = 50
        pc_client.post_note(openreview.Note(
            invitation=f'openreview.net/Support/-/Request{request_form_note.number}/Revision',
            forum=request_form_note.id,
            readers=['aclweb.org/ACL/ARR/2023/August/Program_Chairs', 'openreview.net/Support'],
            referent=request_form_note.id,
            replyto=request_form_note.id,
            signatures=['~Program_ARRChair1'],
            writers=[],
            content={
                'title': 'ACL Rolling Review 2023 - August',
                'Official Venue Name': 'ACL Rolling Review 2023 - August',
                'Abbreviated Venue Name': 'ARR - August 2023',
                'Official Website URL': 'http://aclrollingreview.org',
                'program_chair_emails': ['editors@aclrollingreview.org', 'pc@aclrollingreview.org'],
                'contact_email': 'editors@aclrollingreview.org',
                'Venue Start Date': '2023/08/01',
                'Submission Deadline': due_date.strftime('%Y/%m/%d'),
                'publication_chairs':'No, our venue does not have Publication Chairs',  
                'Location': 'Virtual',
                'submission_reviewer_assignment': 'Automatic',
                'How did you hear about us?': 'ML conferences',
                'Expected Submissions': '100',
                'use_recruitment_template': 'Yes',
                'Additional Submission Options': arr_submission_content,
                'remove_submission_options': ['keywords'],
                'homepage_override': { #TODO: Update
                    'location': 'Hawaii, USA',
                    'instructions': 'For author guidelines, please click [here](https://icml.cc/Conferences/2023/StyleAuthorInstructions)'
                },
                'submission_assignment_max_reviewers': '3'
            }
        ))
        helpers.await_queue_edit(client, invitation=f'openreview.net/Support/-/Request{request_form_note.number}/Revision')

        post_submission_invitation = openreview_client.get_invitation('aclweb.org/ACL/ARR/2023/August/-/Post_Submission')
        assert 'TLDR' in post_submission_invitation.edit['note']['content']
        assert 'preprint' in post_submission_invitation.edit['note']['content']
        assert 'existing_preprints' in post_submission_invitation.edit['note']['content']
        assert 'consent_to_share_data' in post_submission_invitation.edit['note']['content']
        assert 'consent_to_share_submission_details' in post_submission_invitation.edit['note']['content']
        assert 'Association_for_Computational_Linguistics_-_Blind_Submission_License_Agreement' in post_submission_invitation.edit['note']['content']
        assert 'preprint_status' in post_submission_invitation.edit['note']['content']

        request_page(selenium, 'http://localhost:3030/group?id=aclweb.org/ACL/ARR/2023/August', pc_client, wait_for_element='header')
        header_div = selenium.find_element(By.ID, 'header')
        assert header_div
        location_tag = header_div.find_element(By.CLASS_NAME, 'venue-location')
        assert location_tag and location_tag.text == 'Hawaii, USA'
        description = header_div.find_element(By.CLASS_NAME, 'description')
        assert description and 'For author guidelines, please click ' in description.text          

        submission_invitation = openreview_client.get_invitation('aclweb.org/ACL/ARR/2023/August/-/Submission')
        assert submission_invitation
        assert 'existing_preprints' in submission_invitation.edit['note']['content']
        assert 'A1_limitations_section' in submission_invitation.edit['note']['content']
        assert 'paper_type' in submission_invitation.edit['note']['content']
        assert 'keywords' not in submission_invitation.edit['note']['content']

        domain = openreview_client.get_group('aclweb.org/ACL/ARR/2023/August')
        assert 'recommendation' == domain.content['meta_review_recommendation']['value']

        # Build current cycle invitations
        venue = openreview.helpers.get_conference(client, request_form_note.id, 'openreview.net/Support')
        invitation_builder = openreview.arr.InvitationBuilder(venue)

        domain = openreview_client.get_group('aclweb.org/ACL/ARR/2023/August')
        assert domain.content['ethics_chairs_id']['value'] == venue.get_ethics_chairs_id()
        assert domain.content['ethics_chairs_name']['value'] == venue.ethics_chairs_name
        assert domain.content['ethics_reviewers_name']['value'] == venue.ethics_reviewers_name
        assert domain.content['anon_ethics_reviewer_name']['value'] == venue.anon_ethics_reviewers_name()
        assert domain.content['submission_assignment_max_reviewers']['value'] == 3

        assert client.get_invitation(f'openreview.net/Support/-/Request{request_form_note.number}/ARR_Configuration')

        now = datetime.datetime.now()

        registration_name = 'Registration'
        max_load_name = 'Max_Load_And_Unavailability_Request'
        pc_client.post_note(
            openreview.Note(
                content={
                    'form_expiration_date': (due_date).strftime('%Y/%m/%d %H:%M'),
                    'author_consent_start_date': (now).strftime('%Y/%m/%d %H:%M'),
                    'author_consent_end_date': (due_date).strftime('%Y/%m/%d %H:%M'),
                    'registration_due_date': (due_date).strftime('%Y/%m/%d %H:%M'),
                    'maximum_load_due_date': (due_date).strftime('%Y/%m/%d %H:%M'),
                    'maximum_load_exp_date': (due_date).strftime('%Y/%m/%d %H:%M'),
                    'recognition_form_due_date': (due_date).strftime('%Y/%m/%d %H:%M'),
                    'license_agreement_due_date': (due_date).strftime('%Y/%m/%d %H:%M'),
                    'ae_checklist_start_date': (now).strftime('%Y/%m/%d %H:%M'),
                    'ae_checklist_due_date': (due_date).strftime('%Y/%m/%d %H:%M'),
                    'ae_checklist_exp_date': (due_date).strftime('%Y/%m/%d %H:%M'),
                    'reviewer_checklist_start_date': (now).strftime('%Y/%m/%d %H:%M'),
                    'reviewer_checklist_due_date': (due_date).strftime('%Y/%m/%d %H:%M'),
                    'reviewer_checklist_exp_date': (due_date).strftime('%Y/%m/%d %H:%M'),
                    'ethics_review_start_date': (now).strftime('%Y/%m/%d %H:%M'),
                    'ethics_review_deadline': (now + datetime.timedelta(minutes=10)).strftime('%Y/%m/%d %H:%M'),
                    'ethics_review_expiration_date': (now + datetime.timedelta(minutes=10)).strftime('%Y/%m/%d %H:%M'),
                    'emergency_reviewing_start_date': (due_date).strftime('%Y/%m/%d %H:%M'),
                    'emergency_reviewing_due_date': (due_date).strftime('%Y/%m/%d %H:%M'),
                    'emergency_reviewing_exp_date': (due_date).strftime('%Y/%m/%d %H:%M'),
                    'emergency_metareviewing_start_date': (due_date).strftime('%Y/%m/%d %H:%M'),
                    'emergency_metareviewing_due_date': (due_date).strftime('%Y/%m/%d %H:%M'),
                    'emergency_metareviewing_exp_date': (due_date).strftime('%Y/%m/%d %H:%M'),
                    'commentary_start_date': (now - datetime.timedelta(days=2)).strftime('%Y/%m/%d %H:%M'),
                    'commentary_end_date': (now + datetime.timedelta(days=365)).strftime('%Y/%m/%d %H:%M')
                },
                invitation=f'openreview.net/Support/-/Request{request_form_note.number}/ARR_Configuration',
                forum=request_form_note.id,
                readers=['aclweb.org/ACL/ARR/2023/August/Program_Chairs', 'openreview.net/Support'],
                referent=request_form_note.id,
                replyto=request_form_note.id,
                signatures=['~Program_ARRChair1'],
                writers=[],
            )
        )

        helpers.await_queue()

        # Check duedates for registration stages
        assert openreview_client.get_invitation('aclweb.org/ACL/ARR/2023/August/Reviewers/-/Registration').duedate > 0
        assert openreview_client.get_invitation('aclweb.org/ACL/ARR/2023/August/Area_Chairs/-/Registration').duedate > 0
        assert openreview_client.get_invitation('aclweb.org/ACL/ARR/2023/August/Senior_Area_Chairs/-/Registration').duedate > 0
        assert openreview_client.get_invitation('aclweb.org/ACL/ARR/2023/August/Reviewers/-/Recognition_Request').duedate > 0
        assert openreview_client.get_invitation('aclweb.org/ACL/ARR/2023/August/Area_Chairs/-/Recognition_Request').duedate > 0
        assert openreview_client.get_invitation('aclweb.org/ACL/ARR/2023/August/Reviewers/-/License_Agreement').duedate > 0
        assert openreview_client.get_invitation('aclweb.org/ACL/ARR/2023/August/Area_Chairs/-/Metareview_License_Agreement').duedate > 0

        # Pin 2023 and 2024 into next available year
        task_array = [
            arr_reviewer_max_load_task,
            arr_ac_max_load_task,
            arr_sac_max_load_task,
        ]
        venue_roles = [
            venue.get_reviewers_id(),
            venue.get_area_chairs_id(),
            venue.get_senior_area_chairs_id()
        ]

        assert openreview_client.get_invitation('aclweb.org/ACL/ARR/2023/August/Reviewers/-/Max_Load_And_Unavailability_Request')
        assert openreview_client.get_invitation('aclweb.org/ACL/ARR/2023/August/Area_Chairs/-/Max_Load_And_Unavailability_Request')
        assert openreview_client.get_invitation('aclweb.org/ACL/ARR/2023/August/Senior_Area_Chairs/-/Max_Load_And_Unavailability_Request')

        for role, task_field in zip(venue_roles, task_array):
            m = matching.Matching(venue, venue.client.get_group(role), None, None)
            m._create_edge_invitation(venue.get_custom_max_papers_id(m.match_group.id))

            openreview_client.post_invitation_edit(
                invitations=venue.get_meta_invitation_id(),
                readers=[venue.id],
                writers=[venue.id],
                signatures=[venue.id],
                invitation=openreview.api.Invitation(
                    id=f"{role}/-/{max_load_name}",
                    edit={
                        'note': {
                            'content':{
                                'next_available_year': {
                                    'value': {
                                        'param': {
                                            "input": "checkbox",
                                            "optional": True,
                                            "type": "integer",
                                            'enum' : list(set([2022, 2023, 2024] + task_field['next_available_year']['value']['param']['enum']))
                                        }
                                    }
                                }
                            }
                        }
                    }
                )
            )

    def test_june_cycle(self, client, openreview_client, helpers, test_client):
        # Build the previous cycle
        pc_client=openreview.Client(username='pc@aclrollingreview.org', password=helpers.strong_password)
        pc_client_v2 = openreview.api.OpenReviewClient(username='pc@aclrollingreview.org', password=helpers.strong_password)

        now = datetime.datetime.now()
        due_date = now + datetime.timedelta(days=3)

        request_form_note = pc_client.post_note(openreview.Note(
            invitation='openreview.net/Support/-/Request_Form',
            signatures=['~Program_ARRChair1'],
            readers=[
                'openreview.net/Support',
                '~Program_ARRChair1'
            ],
            writers=[],
            content={
                'title': 'ACL Rolling Review 2023 - June',
                'Official Venue Name': 'ACL Rolling Review 2023 - June',
                'Abbreviated Venue Name': 'ARR - June 2023',
                'Official Website URL': 'http://aclrollingreview.org',
                'program_chair_emails': ['editors@aclrollingreview.org', 'pc@aclrollingreview.org'],
                'contact_email': 'editors@aclrollingreview.org',
                'Area Chairs (Metareviewers)': 'Yes, our venue has Area Chairs',
                'senior_area_chairs': 'Yes, our venue has Senior Area Chairs',
                'senior_area_chairs_assignment': 'Submissions',
                'ethics_chairs_and_reviewers': 'Yes, our venue has Ethics Chairs and Reviewers',
                'publication_chairs':'No, our venue does not have Publication Chairs',
                'Venue Start Date': '2023/06/01',
                'Submission Deadline': due_date.strftime('%Y/%m/%d'),
                'Location': 'Virtual',
                'submission_reviewer_assignment': 'Automatic',
                'Author and Reviewer Anonymity': 'Double-blind',
                'reviewer_identity': ['Program Chairs', 'Assigned Senior Area Chair', 'Assigned Area Chair', 'Assigned Reviewers'],
                'area_chair_identity': ['Program Chairs', 'Assigned Senior Area Chair', 'Assigned Area Chair', 'Assigned Reviewers'],
                'senior_area_chair_identity': ['Program Chairs', 'Assigned Senior Area Chair', 'Assigned Area Chair', 'Assigned Reviewers'],
                'Open Reviewing Policy': 'Submissions and reviews should both be private.',
                'submission_readers': 'Assigned program committee (assigned reviewers, assigned area chairs, assigned senior area chairs if applicable)',
                'How did you hear about us?': 'ML conferences',
                'Expected Submissions': '100',
                'use_recruitment_template': 'Yes',
                'api_version': '2',
                'submission_license': ['CC BY-SA 4.0'],
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
        june_deploy_edit = client.post_note(openreview.Note(
            content={'venue_id': 'aclweb.org/ACL/ARR/2023/June'},
            forum=request_form_note.forum,
            invitation='openreview.net/Support/-/Request{}/Deploy'.format(request_form_note.number),
            readers=['openreview.net/Support'],
            referent=request_form_note.forum,
            replyto=request_form_note.forum,
            signatures=['openreview.net/Support'],
            writers=['openreview.net/Support']
        ))

        helpers.await_queue_edit(client, invitation='openreview.net/Support/-/Request{}/Deploy'.format(request_form_note.number))

        assert openreview_client.get_group('aclweb.org/ACL/ARR/2023/June')
        assert openreview_client.get_group('aclweb.org/ACL/ARR/2023/June/Senior_Area_Chairs')
        assert openreview_client.get_group('aclweb.org/ACL/ARR/2023/June/Area_Chairs')
        assert openreview_client.get_group('aclweb.org/ACL/ARR/2023/June/Ethics_Chairs')
        assert openreview_client.get_group('aclweb.org/ACL/ARR/2023/June/Reviewers')
        assert openreview_client.get_group('aclweb.org/ACL/ARR/2023/June/Ethics_Reviewers')
        assert openreview_client.get_group('aclweb.org/ACL/ARR/2023/June/Authors')

        venue = openreview.helpers.get_conference(client, request_form_note.id, 'openreview.net/Support')

        # Populate past groups
        openreview_client.add_members_to_group(
            venue.get_reviewers_id(), [
                f"~Reviewer_ARR{num}1" for num in ['One', 'Two', 'Three', 'Four', 'Five', 'Six', 'NA']
            ]
        )
        openreview_client.add_members_to_group(
            venue.get_area_chairs_id(), [
                f"~AC_ARR{num}1" for num in ['One', 'Two', 'Three']
            ]
        )
        openreview_client.add_members_to_group(
            venue.get_senior_area_chairs_id(), [
                f"~SAC_ARR{num}1" for num in ['One', 'Two', 'Three']
            ]
        )
        openreview_client.add_members_to_group(
            venue.get_reviewers_id(), ["~Reviewer_ARRTwoMerge1"]
        )
        openreview_client.add_members_to_group(venue.get_ethics_chairs_id(), ['~EthicsChair_ARROne1'])
        openreview_client.add_members_to_group(venue.get_ethics_reviewers_id(), ['~EthicsReviewer_ARROne1'])

        ## Add overlap for deduplication test
        openreview_client.add_members_to_group(
            venue.get_reviewers_id(),
            ['~AC_ARROne1', '~SAC_ARROne1']
        )
        openreview_client.add_members_to_group(
            venue.get_area_chairs_id(),
            ['~SAC_ARROne1']
        )

        # Update submission fields
        ## override file size for tests
        arr_submission_content['software']['value']['param']['maxSize'] = 50
        pc_client.post_note(openreview.Note(
            invitation=f'openreview.net/Support/-/Request{request_form_note.number}/Revision',
            forum=request_form_note.id,
            readers=['aclweb.org/ACL/ARR/2023/June/Program_Chairs', 'openreview.net/Support'],
            referent=request_form_note.id,
            replyto=request_form_note.id,
            signatures=['~Program_ARRChair1'],
            writers=[],
            content={
                'title': 'ACL Rolling Review 2023 - June',
                'Official Venue Name': 'ACL Rolling Review 2023 - June',
                'Abbreviated Venue Name': 'ARR - June 2023',
                'Official Website URL': 'http://aclrollingreview.org',
                'program_chair_emails': ['editors@aclrollingreview.org', 'pc@aclrollingreview.org'],
                'contact_email': 'editors@aclrollingreview.org',
                'Venue Start Date': '2023/08/01',
                'Submission Deadline': due_date.strftime('%Y/%m/%d'),
                'publication_chairs':'No, our venue does not have Publication Chairs',  
                'Location': 'Virtual',
                'submission_reviewer_assignment': 'Automatic',
                'How did you hear about us?': 'ML conferences',
                'Expected Submissions': '100',
                'use_recruitment_template': 'Yes',
                'Additional Submission Options': arr_submission_content,
                'remove_submission_options': ['keywords'],
                'homepage_override': { #TODO: Update
                    'location': 'Hawaii, USA',
                    'instructions': 'For author guidelines, please click [here](https://icml.cc/Conferences/2023/StyleAuthorInstructions)'
                }
            }
        ))

        helpers.await_queue()

        helpers.await_queue_edit(client, invitation=f'openreview.net/Support/-/Request{request_form_note.number}/Revision')

        ## Post a submission to get Ethics Stage to work
        test_client = openreview.api.OpenReviewClient(token=test_client.token)

        note = openreview.api.Note(
            content = {
                'title': { 'value': 'Paper title '},
                'abstract': { 'value': 'This is an abstract ' },
                'authorids': { 'value': ['~SomeFirstName_User1', 'peter@mail.com', 'andrew@meta.com']},
                'authors': { 'value': ['SomeFirstName User', 'Peter SomeLastName', 'Andrew Mc'] },
                'TLDR': { 'value': 'This is a tldr '},
                'pdf': {'value': '/pdf/' + 'p' * 40 +'.pdf' },
                'paper_type': { 'value': 'Short' },
                'research_area': { 'value': 'Code Models' },
                'research_area_keywords': { 'value': 'A keyword' },
                'languages_studied': { 'value': 'A language' },
                'reassignment_request_area_chair': { 'value': 'This is not a resubmission' },
                'reassignment_request_reviewers': { 'value': 'This is not a resubmission' },
                'software': {'value': '/pdf/' + 'p' * 40 +'.zip' },
                'data': {'value': '/pdf/' + 'p' * 40 +'.zip' },
                'preprint': { 'value': 'yes'},
                'preprint_status': { 'value': 'There is no non-anonymous preprint and we do not intend to release one. (this option is binding)'},
                'existing_preprints': { 'value': 'existing_preprints' },
                'preferred_venue': { 'value': 'ACL' },
                'consent_to_share_data': { 'value': 'yes' },
                'consent_to_share_submission_details': { 'value': 'On behalf of all authors, we agree to the terms above to share our submission details.' },
                "A1_limitations_section": { 'value': 'This paper has a limitations section.' },
                "A2_potential_risks": { 'value': 'Yes' },
                "B_use_or_create_scientific_artifacts": { 'value': 'Yes' },
                "B1_cite_creators_of_artifacts": { 'value': 'Yes' },
                "B2_discuss_the_license_for_artifacts": { 'value': 'Yes' },
                "B3_artifact_use_consistent_with_intended_use": { 'value': 'Yes' },
                "B4_data_contains_personally_identifying_info_or_offensive_content": { 'value': 'Yes' },
                "B5_documentation_of_artifacts": { 'value': 'Yes' },
                "B6_statistics_for_data": { 'value': 'Yes' },
                "C_computational_experiments": { 'value': 'Yes' },
                "C1_model_size_and_budget": { 'value': 'Yes' },
                "C2_experimental_setup_and_hyperparameters": { 'value': 'Yes' },
                "C3_descriptive_statistics": { 'value': 'Yes' },
                "C4_parameters_for_packages": { 'value': 'Yes' },
                "D_human_subjects_including_annotators": { 'value': 'Yes' },
                "D1_instructions_given_to_participants": { 'value': 'Yes' },
                "D2_recruitment_and_payment": { 'value': 'Yes' },
                "D3_data_consent": { 'value': 'Yes' },
                "D4_ethics_review_board_approval": { 'value': 'Yes' },
                "D5_characteristics_of_annotators": { 'value': 'Yes' },
                "E_ai_assistants_in_research_or_writing": { 'value': 'Yes' },
                "E1_information_about_use_of_ai_assistants": { 'value': 'Yes' },
                "author_submission_checklist": { 'value': 'yes' },
                "Association_for_Computational_Linguistics_-_Blind_Submission_License_Agreement": { 'value': "On behalf of all authors, I do not agree" }
            }
        )

        test_client.post_note_edit(invitation='aclweb.org/ACL/ARR/2023/June/-/Submission',
            signatures=['~SomeFirstName_User1'],
            note=note)

        helpers.await_queue_edit(openreview_client, invitation='aclweb.org/ACL/ARR/2023/June/-/Submission', count=1)

        # Create ethics review stage to add values into domain
        now = datetime.datetime.now()
        start_date = now - datetime.timedelta(days=2)
        due_date = now + datetime.timedelta(days=3)
        stage_note = pc_client.post_note(openreview.Note(
            content={
                'ethics_review_start_date': start_date.strftime('%Y/%m/%d'),
                'ethics_review_deadline': (start_date + datetime.timedelta(seconds=3)).strftime('%Y/%m/%d'),
                'make_ethics_reviews_public': 'No, ethics reviews should NOT be revealed publicly when they are posted',
                'release_ethics_reviews_to_authors': "No, ethics reviews should NOT be revealed when they are posted to the paper\'s authors",
                'release_ethics_reviews_to_reviewers': 'Ethics Review should not be revealed to any reviewer, except to the author of the ethics review',
                'remove_ethics_review_form_options': 'ethics_review',
                'additional_ethics_review_form_options': {
                    "ethics_concerns": {
                        'order': 1,
                        'description': 'Briefly summarize the ethics concerns.',
                        'value': {
                            'param': {
                                'type': 'string',
                                'maxLength': 200000,
                                'markdown': True,
                                'input': 'textarea'
                            }
                        }
                    }
                },
                'release_submissions_to_ethics_reviewers': 'We confirm we want to release the submissions and reviews to the ethics reviewers',
                'release_submissions_to_ethics_chairs': 'Yes, release flagged submissions to the ethics chairs.',
                'compute_affinity_scores': 'No'
            },
            forum=request_form_note.forum,
            referent=request_form_note.forum,
            invitation='openreview.net/Support/-/Request{}/Ethics_Review_Stage'.format(request_form_note.number),
            readers=[venue.get_program_chairs_id(), 'openreview.net/Support'],
            signatures=['~Program_ARRChair1'],
            writers=[]
        ))

        helpers.await_queue()
        
        helpers.await_queue_edit(client, invitation=f'openreview.net/Support/-/Request{request_form_note.number}/Ethics_Review_Stage')

        helpers.await_queue_edit(openreview_client, edit_id='aclweb.org/ACL/ARR/2023/June/Ethics_Reviewers/-/Submission_Group-0-1', count=1)

        ethics_review_invitations = openreview_client.get_all_invitations(invitation='aclweb.org/ACL/ARR/2023/August/-/Ethics_Review')
        assert len(ethics_review_invitations) == 0

        flag_invitation = openreview_client.get_invitation('aclweb.org/ACL/ARR/2023/August/-/Ethics_Review_Flag')
        assert flag_invitation.process
        assert 'for invitation_name in [review_name, ae_checklist_name, reviewer_checklist_name]:' in flag_invitation.process
        assert 'ae_checklist_name' in flag_invitation.content
        assert 'reviewer_checklist_name' in flag_invitation.content

        venue = openreview.helpers.get_conference(client, request_form_note.id, 'openreview.net/Support')
        venue.create_ethics_review_stage()

        # Create past registration stages

        # Pin 2023 and 2024 into next available year
        for content in [
            arr_reviewer_max_load_task,
            arr_ac_max_load_task,
            arr_sac_max_load_task,
        ]:
            content['next_available_year']['value']['param']['enum'] = list(set([2022, 2023, 2024] + content['next_available_year']['value']['param']['enum']))
        
        registration_name = 'Registration'
        max_load_name = 'Max_Load_And_Unavailability_Request'
        venue.registration_stages.append(
            openreview.stages.RegistrationStage(committee_id = venue.get_reviewers_id(),
            name = registration_name,
            start_date = None,
            due_date = due_date,
            instructions = arr_registration_task_forum['instructions'],
            title = venue.get_reviewers_name() + ' ' + arr_registration_task_forum['title'],
            additional_fields=arr_registration_task)
        )
        venue.registration_stages.append(
            openreview.stages.RegistrationStage(committee_id = venue.get_reviewers_id(),
            name = max_load_name,
            start_date = None,
            due_date = due_date,
            instructions = arr_max_load_task_forum['instructions'],
            title = venue.get_reviewers_name() + ' ' + arr_max_load_task_forum['title'],
            additional_fields=arr_reviewer_max_load_task,
            remove_fields=['profile_confirmed', 'expertise_confirmed'])
        )
        venue.registration_stages.append(
            openreview.stages.RegistrationStage(committee_id = venue.get_reviewers_id(),
            name = 'License_Agreement',
            start_date = None,
            due_date = due_date,
            instructions = arr_content_license_task_forum['instructions'],
            title = arr_content_license_task_forum['title'],
            additional_fields=arr_content_license_task,
            remove_fields=['profile_confirmed', 'expertise_confirmed'])
        )

        venue.registration_stages.append(
            openreview.stages.RegistrationStage(committee_id = venue.get_area_chairs_id(),
            name = registration_name,
            start_date = None,
            due_date = due_date,
            instructions = arr_registration_task_forum['instructions'],
            title = venue.get_area_chairs_name() + ' ' + arr_registration_task_forum['title'],
            additional_fields=arr_registration_task)
        )
        venue.registration_stages.append(
            openreview.stages.RegistrationStage(committee_id = venue.get_area_chairs_id(),
            name = max_load_name,
            start_date = None,
            due_date = due_date,
            instructions = arr_max_load_task_forum['instructions'],
            title = venue.get_area_chairs_name() + ' ' + arr_max_load_task_forum['title'],
            additional_fields=arr_ac_max_load_task,
            remove_fields=['profile_confirmed', 'expertise_confirmed'])
        )

        venue.registration_stages.append(
            openreview.stages.RegistrationStage(committee_id = venue.get_senior_area_chairs_id(),
            name = registration_name,
            start_date = None,
            due_date = due_date,
            instructions = arr_registration_task_forum['instructions'],
            title = venue.senior_area_chairs_name.replace('_', ' ') + ' ' + arr_registration_task_forum['title'],
            additional_fields=arr_registration_task)
        )
        venue.registration_stages.append(
            openreview.stages.RegistrationStage(committee_id = venue.get_senior_area_chairs_id(),
            name = max_load_name,
            start_date = None,
            due_date = due_date,
            instructions = arr_max_load_task_forum['instructions'],
            title = venue.senior_area_chairs_name.replace('_', ' ') + ' ' + arr_max_load_task_forum['title'],
            additional_fields=arr_sac_max_load_task,
            remove_fields=['profile_confirmed', 'expertise_confirmed'])
        )
        venue.create_registration_stages()

        # Add max load preprocess validation
        invitation_builder = openreview.arr.InvitationBuilder(venue)
        venue_roles = [
            venue.get_reviewers_id(),
            venue.get_area_chairs_id(),
            venue.get_senior_area_chairs_id()
        ]
        for role in venue_roles:
            openreview_client.post_invitation_edit(
                invitations=venue.get_meta_invitation_id(),
                readers=[venue.id],
                writers=[venue.id],
                signatures=[venue.id],
                invitation=openreview.api.Invitation(
                    id=f"{role}/-/{max_load_name}",
                    preprocess=invitation_builder.get_process_content('process/max_load_preprocess.py')
                )
            )

        # Post some past registration notes
        reviewer_client = openreview.api.OpenReviewClient(username = 'reviewer1@aclrollingreview.com', password=helpers.strong_password)
        reviewer_two_client = openreview.api.OpenReviewClient(username = 'reviewer2@aclrollingreview.com', password=helpers.strong_password)
        reviewer_two_merge_client = openreview.api.OpenReviewClient(username = 'reviewer2-1@aclrollingreview.com', password=helpers.strong_password)
        reviewer_three_client = openreview.api.OpenReviewClient(username = 'reviewer3@aclrollingreview.com', password=helpers.strong_password)
        reviewer_four_client = openreview.api.OpenReviewClient(username = 'reviewer4@aclrollingreview.com', password=helpers.strong_password)
        reviewer_five_client = openreview.api.OpenReviewClient(username = 'reviewer5@aclrollingreview.com', password=helpers.strong_password)
        reviewer_na_client = openreview.api.OpenReviewClient(username = 'reviewerna@aclrollingreview.com', password=helpers.strong_password)
        ac_client = openreview.api.OpenReviewClient(username = 'ac1@aclrollingreview.com', password=helpers.strong_password)
        sac_client = openreview.api.OpenReviewClient(username = 'sac1@aclrollingreview.com', password=helpers.strong_password)
        sac_two_client = openreview.api.OpenReviewClient(username = 'sac2@aclrollingreview.com', password=helpers.strong_password)
        sac_three_client = openreview.api.OpenReviewClient(username = 'sac3@aclrollingreview.com', password=helpers.strong_password)
        reviewer_client.post_note_edit(
            invitation=f'{venue.get_reviewers_id()}/-/{registration_name}',
            signatures=['~Reviewer_Alternate_ARROne1'],
            note=openreview.api.Note(
                content = {
                    'profile_confirmed': { 'value': 'Yes' },
                    'expertise_confirmed': { 'value': 'Yes' },
                    'domains': { 'value': 'Yes' },
                    'emails': { 'value': 'Yes' },
                    'DBLP': { 'value': 'Yes' },
                    'semantic_scholar': { 'value': 'Yes' },
                    'research_area': { 'value': ['Code Models', 'Information Extraction and Retrieval'] },
                }
            )
        )
        reviewer_two_client.post_note_edit(
            invitation=f'{venue.get_reviewers_id()}/-/{registration_name}',
            signatures=['~Reviewer_ARRTwo1'],
            note=openreview.api.Note(
                content = {
                    'profile_confirmed': { 'value': 'Yes' },
                    'expertise_confirmed': { 'value': 'Yes' },
                    'domains': { 'value': 'Yes' },
                    'emails': { 'value': 'Yes' },
                    'DBLP': { 'value': 'Yes' },
                    'semantic_scholar': { 'value': 'Yes' },
                    'research_area': { 'value': ['Safety and Alignment in LLMs', 'Code Models', 'Dialogue and Interactive Systems'] },
                }
            )
        )

        # Post duplicate and merge profiles
        reviewer_two_merge_client.post_note_edit(
            invitation=f'{venue.get_reviewers_id()}/-/{registration_name}',
            signatures=['~Reviewer_ARRTwoMerge1'],
            note=openreview.api.Note(
                content = {
                    'profile_confirmed': { 'value': 'Yes' },
                    'expertise_confirmed': { 'value': 'Yes' },
                    'domains': { 'value': 'Yes' },
                    'emails': { 'value': 'Yes' },
                    'DBLP': { 'value': 'Yes' },
                    'semantic_scholar': { 'value': 'Yes' },
                    'research_area': { 'value': ['Safety and Alignment in LLMs', 'Code Models'] },
                }
            )
        )
        # Merge profiles
        openreview_client.merge_profiles('~Reviewer_ARRTwo1', '~Reviewer_ARRTwoMerge1')
        profile = openreview_client.get_profile('~Reviewer_ARRTwo1')
        assert len(profile.content['names']) == 3
        profile.content['names'][0]['username'] == '~Reviewer_ARRTwo1'
        profile.content['names'][1]['preferred'] == True
        profile.content['names'][1]['username'] == '~Reviewer_Alternate_ARRTwo1'
        profile.content['names'][2]['username'] == '~Reviewer_ARRTwoMerge1'

        ac_client.post_note_edit(
            invitation=f'{venue.get_area_chairs_id()}/-/{registration_name}',
            signatures=['~AC_ARROne1'],
            note=openreview.api.Note(
                content = {
                    'profile_confirmed': { 'value': 'Yes' },
                    'expertise_confirmed': { 'value': 'Yes' },
                    'domains': { 'value': 'Yes' },
                    'emails': { 'value': 'Yes' },
                    'DBLP': { 'value': 'Yes' },
                    'semantic_scholar': { 'value': 'Yes' },
                    'research_area': { 'value': ['Code Models', 'NLP Applications'] },
                }
            )
        )
        sac_client.post_note_edit(
            invitation=f'{venue.get_senior_area_chairs_id()}/-/{registration_name}',
            signatures=['~SAC_ARROne1'],
            note=openreview.api.Note(
                content = {
                    'profile_confirmed': { 'value': 'Yes' },
                    'expertise_confirmed': { 'value': 'Yes' },
                    'domains': { 'value': 'Yes' },
                    'emails': { 'value': 'Yes' },
                    'DBLP': { 'value': 'Yes' },
                    'semantic_scholar': { 'value': 'Yes' },
                    'research_area': { 'value': ['Code Models', 'Safety and Alignment in LLMs', 'NLP Applications'] },
                }
            )
        )
        sac_two_client.post_note_edit(
            invitation=f'{venue.get_senior_area_chairs_id()}/-/{registration_name}',
            signatures=['~SAC_ARRTwo1'],
            note=openreview.api.Note(
                content = {
                    'profile_confirmed': { 'value': 'Yes' },
                    'expertise_confirmed': { 'value': 'Yes' },
                    'domains': { 'value': 'Yes' },
                    'emails': { 'value': 'Yes' },
                    'DBLP': { 'value': 'Yes' },
                    'semantic_scholar': { 'value': 'Yes' },
                    'research_area': { 'value': ['Code Models', 'Safety and Alignment in LLMs', 'NLP Applications'] },
                }
            )
        )
        sac_three_client.post_note_edit(
            invitation=f'{venue.get_senior_area_chairs_id()}/-/{registration_name}',
            signatures=['~SAC_ARRThree1'],
            note=openreview.api.Note(
                content = {
                    'profile_confirmed': { 'value': 'Yes' },
                    'expertise_confirmed': { 'value': 'Yes' },
                    'domains': { 'value': 'Yes' },
                    'emails': { 'value': 'Yes' },
                    'DBLP': { 'value': 'Yes' },
                    'semantic_scholar': { 'value': 'Yes' },
                    'research_area': { 'value': ['Code Models', 'Safety and Alignment in LLMs', 'NLP Applications'] },
                }
            )
        )


        # Post past unavailability notes
        reviewer_client.post_note_edit( ## Reviewer should be available - next available date is now
            invitation=f'{venue.get_reviewers_id()}/-/{max_load_name}',
            signatures=['~Reviewer_Alternate_ARROne1'],
            note=openreview.api.Note(
                content = {
                    'maximum_load_this_cycle': { 'value': 0 },
                    'maximum_load_this_cycle_for_resubmissions': { 'value': 'No' },
                    'meta_data_donation': { 'value': 'Yes, I consent to donating anonymous metadata of my review for research.' },
                    'next_available_month': { 'value': 'August'},
                    'next_available_year': { 'value': 2023}
                }
            )
        )
        with pytest.raises(openreview.OpenReviewException, match=r'Please provide both your next available year and month'):
            reviewer_two_client.post_note_edit(
                invitation=f'{venue.get_reviewers_id()}/-/{max_load_name}',
                signatures=['~Reviewer_ARRTwo1'],
                note=openreview.api.Note(
                    content = {
                        'maximum_load_this_cycle': { 'value': 0 },
                        'maximum_load_this_cycle_for_resubmissions': { 'value': 'No' },
                        'meta_data_donation': { 'value': 'Yes, I consent to donating anonymous metadata of my review for research.' },
                        'next_available_month': { 'value': 'August'}
                    }
                )
            )
        with pytest.raises(openreview.OpenReviewException, match=r'Please provide both your next available year and month'):
            reviewer_two_client.post_note_edit(
                invitation=f'{venue.get_reviewers_id()}/-/{max_load_name}',
                signatures=['~Reviewer_ARRTwo1'],
                note=openreview.api.Note(
                    content = {
                        'maximum_load_this_cycle': { 'value': 0 },
                        'maximum_load_this_cycle_for_resubmissions': { 'value': 'No' },
                        'meta_data_donation': { 'value': 'Yes, I consent to donating anonymous metadata of my review for research.' },
                        'next_available_year': { 'value': 2024}
                    }
                )
            )
        with pytest.raises(openreview.OpenReviewException, match="Please only provide your next available year and month if you are unavailable this cycle. Click Cancel to reset these fields and fill out the form again."):
            reviewer_two_client.post_note_edit(
                invitation=f'{venue.get_reviewers_id()}/-/{max_load_name}',
                signatures=['~Reviewer_ARRTwo1'],
                note=openreview.api.Note(
                    content = {
                        'maximum_load_this_cycle': { 'value': 4 },
                        'maximum_load_this_cycle_for_resubmissions': { 'value': 'No' },
                        'meta_data_donation': { 'value': 'Yes, I consent to donating anonymous metadata of my review for research.' },
                        'next_available_year': { 'value': 2024}
                    }
                )
            )
        with pytest.raises(openreview.OpenReviewException, match="Please only provide your next available year and month if you are unavailable this cycle. Click Cancel to reset these fields and fill out the form again."):
            reviewer_two_client.post_note_edit(
                invitation=f'{venue.get_reviewers_id()}/-/{max_load_name}',
                signatures=['~Reviewer_ARRTwo1'],
                note=openreview.api.Note(
                    content = {
                        'maximum_load_this_cycle': { 'value': 4 },
                        'maximum_load_this_cycle_for_resubmissions': { 'value': 'No' },
                        'meta_data_donation': { 'value': 'Yes, I consent to donating anonymous metadata of my review for research.' },
                        'next_available_month': { 'value': 'August'}
                    }
                )
            )
            
        reviewer_two_client.post_note_edit( ## Reviewer should not be available - 1 month past next cycle
                invitation=f'{venue.get_reviewers_id()}/-/{max_load_name}',
                signatures=['~Reviewer_ARRTwo1'],
                note=openreview.api.Note(
                    content = {
                        'maximum_load_this_cycle': { 'value': 0 },
                        'maximum_load_this_cycle_for_resubmissions': { 'value': 'No' },
                        'meta_data_donation': { 'value': 'Yes, I consent to donating anonymous metadata of my review for research.' },
                        'next_available_month': { 'value': 'September'},
                        'next_available_year': { 'value': 2023}
                    }
                )
            )
        reviewer_three_client.post_note_edit( ## Reviewer should be available - 1 month in the past
                invitation=f'{venue.get_reviewers_id()}/-/{max_load_name}',
                signatures=['~Reviewer_ARRThree1'],
                note=openreview.api.Note(
                    content = {
                        'maximum_load_this_cycle': { 'value': 0 },
                        'maximum_load_this_cycle_for_resubmissions': { 'value': 'No' },
                        'meta_data_donation': { 'value': 'No, I do not consent to donating anonymous metadata of my review for research.' },
                        'next_available_month': { 'value': 'July'},
                        'next_available_year': { 'value': 2023}
                    }
                )
            )
        reviewer_four_client.post_note_edit( ## Reviewer should be available - 1 year in the past
                invitation=f'{venue.get_reviewers_id()}/-/{max_load_name}',
                signatures=['~Reviewer_ARRFour1'],
                note=openreview.api.Note(
                    content = {
                        'maximum_load_this_cycle': { 'value': 0 },
                        'maximum_load_this_cycle_for_resubmissions': { 'value': 'No' },
                        'meta_data_donation': { 'value': 'Yes, I consent to donating anonymous metadata of my review for research.' },
                        'next_available_month': { 'value': 'August'},
                        'next_available_year': { 'value': 2022}
                    }
                )
            )
        reviewer_five_client.post_note_edit( ## Reviewer should be available - 1 year in the past + 1 month in the past
                invitation=f'{venue.get_reviewers_id()}/-/{max_load_name}',
                signatures=['~Reviewer_ARRFive1'],
                note=openreview.api.Note(
                    content = {
                        'maximum_load_this_cycle': { 'value': 0 },
                        'maximum_load_this_cycle_for_resubmissions': { 'value': 'No' },
                        'meta_data_donation': { 'value': 'Yes, I consent to donating anonymous metadata of my review for research.' },
                        'next_available_month': { 'value': 'July'},
                        'next_available_year': { 'value': 2022}
                    }
                )
            ) 
        ac_client.post_note_edit( ## AC should not be available - 1 year into future
            invitation=f'{venue.get_area_chairs_id()}/-/{max_load_name}',
            signatures=['~AC_ARROne1'],
            note=openreview.api.Note(
                content = {
                    'maximum_load_this_cycle': { 'value': 0 },
                    'maximum_load_this_cycle_for_resubmissions': { 'value': 'No' },
                    'next_available_month': { 'value': 'August'},
                    'next_available_year': { 'value': 2024}
                }
            )
        )
        sac_client.post_note_edit( ## SAC should not be available - 1 month + 1 year into future
            invitation=f'{venue.get_senior_area_chairs_id()}/-/{max_load_name}',
            signatures=['~SAC_ARROne1'],
            note=openreview.api.Note(
                content = {
                    'availability_this_cycle': { 'value': "I confirm that I will serve as SAC in this cycle, with the review load shared equally with other SACs (computed per track in conference-associated cycles)." },
                    'next_available_month': { 'value': 'September'},
                    'next_available_year': { 'value': 2024}
                }
            )
        )
        sac_two_client.post_note_edit( ## SAC should be available
            invitation=f'{venue.get_senior_area_chairs_id()}/-/{max_load_name}',
            signatures=['~SAC_ARRTwo1'],
            note=openreview.api.Note(
                content = {
                    'availability_this_cycle': { 'value': "I confirm that I will serve as SAC in this cycle, with the review load shared equally with other SACs (computed per track in conference-associated cycles)." }
                }
            )
        )

        # Create past expertise edges
        user_client = openreview.api.OpenReviewClient(username='reviewer1@aclrollingreview.com', password=helpers.strong_password)
        archive_note = user_client.post_note_edit(
            invitation='openreview.net/Archive/-/Direct_Upload',
            signatures=['~Reviewer_Alternate_ARROne1'],
            note = openreview.api.Note(
                pdate = openreview.tools.datetime_millis(datetime.datetime(2019, 4, 30)),
                content = {
                    'title': { 'value': 'Paper title 2' },
                    'abstract': { 'value': 'Paper abstract 2' },
                    'authors': { 'value': ['Reviewer ARR', 'Test2 Client'] },
                    'authorids': { 'value': ['~Reviewer_Alternate_ARROne1', 'test2@mail.com'] },
                    'venue': { 'value': 'Arxiv' }
                },
                license = 'CC BY-SA 4.0'
        ))
        user_client.post_edge(
            openreview.api.Edge(
                invitation = venue.get_expertise_selection_id(committee_id = venue.get_reviewers_id()),
                readers = [venue.id, '~Reviewer_ARROne1'],
                writers = [venue.id, '~Reviewer_ARROne1'],
                signatures = ['~Reviewer_ARROne1'],
                head = archive_note['note']['id'],
                tail = '~Reviewer_ARROne1',
                label = 'Exclude'
        ))
        user_client = openreview.api.OpenReviewClient(username='ac1@aclrollingreview.com', password=helpers.strong_password)
        user_client.post_edge(
            openreview.api.Edge(
                invitation = venue.get_expertise_selection_id(committee_id = venue.get_area_chairs_id()),
                readers = [venue.id, '~AC_ARROne1'],
                writers = [venue.id, '~AC_ARROne1'],
                signatures = ['~AC_ARROne1'],
                head = archive_note['note']['id'],
                tail = '~AC_ARROne1',
                label = 'Exclude'
        ))
        user_client = openreview.api.OpenReviewClient(username='sac1@aclrollingreview.com', password=helpers.strong_password)
        user_client.post_edge(
            openreview.api.Edge(
                invitation = venue.get_expertise_selection_id(committee_id = venue.get_senior_area_chairs_id()),
                readers = [venue.id, '~SAC_ARROne1'],
                writers = [venue.id, '~SAC_ARROne1'],
                signatures = ['~SAC_ARROne1'],
                head = archive_note['note']['id'],
                tail = '~SAC_ARROne1',
                label = 'Exclude'
        ))

        # Create past reviewer license
        license_edit = reviewer_four_client.post_note_edit(
            invitation='aclweb.org/ACL/ARR/2023/June/Reviewers/-/License_Agreement',
            signatures=['~Reviewer_ARRFour1'],
            note=openreview.api.Note(
                content = {
                    "attribution": { "value": "Yes, I wish to be attributed."},
                    "agreement": { "value": "I agree for this cycle and all future cycles until I explicitly revoke my decision"}
                }    
            )
        )

        assert reviewer_four_client.get_note(license_edit['note']['id'])

        license_edit = reviewer_five_client.post_note_edit(
            invitation='aclweb.org/ACL/ARR/2023/June/Reviewers/-/License_Agreement',
            signatures=['~Reviewer_ARRFive1'],
            note=openreview.api.Note(
                content = {
                    "agreement": { "value": "I do not agree"}
                }    
            )
        )

        assert reviewer_five_client.get_note(license_edit['note']['id'])

    def test_ac_recruitment(self, client, openreview_client, helpers, request_page, selenium):

        pc_client = openreview.Client(username='pc@aclrollingreview.org', password=helpers.strong_password)
        request_form=pc_client.get_notes(invitation='openreview.net/Support/-/Request_Form')[1]

        reviewer_details = '''acextra1@aclrollingreview.com, AC ARRExtraOne\nacextra2@aclrollingreview.com, AC ARRExtraOne'''
        pc_client.post_note(openreview.Note(
            content={
                'title': 'Recruitment',
                'invitee_role': 'Area_Chairs',
                'invitee_details': reviewer_details,
                'invitation_email_subject': '[ARR August 2023] Invitation to serve as {{invitee_role}}',
                'invitation_email_content': 'Dear {{fullname}},\n\nYou have been nominated by the program chair committee of ACL ARR 2023 August to serve as {{invitee_role}}.\n\n{{invitation_url}}\n\nCheers!\n\nProgram Chairs'
            },
            forum=request_form.forum,
            replyto=request_form.forum,
            invitation='openreview.net/Support/-/Request{}/Recruitment'.format(request_form.number),
            readers=['aclweb.org/ACL/ARR/2023/August/Program_Chairs', 'openreview.net/Support'],
            signatures=['~Program_ARRChair1'],
            writers=[]
        ))

        helpers.await_queue()

        assert len(openreview_client.get_group('aclweb.org/ACL/ARR/2023/August/Area_Chairs').members) == 0
        assert len(openreview_client.get_group('aclweb.org/ACL/ARR/2023/August/Area_Chairs/Invited').members) == 2

        messages = openreview_client.get_messages(subject = '[ARR August 2023] Invitation to serve as Area Chair')
        assert len(messages) == 2

        for message in messages:
            text = message['content']['text']

            invitation_url = re.search('https://.*\n', text).group(0).replace('https://openreview.net', 'http://localhost:3030').replace('&amp;', '&')[:-1]
            helpers.respond_invitation(selenium, request_page, invitation_url, accept=True)

        helpers.await_queue_edit(openreview_client, invitation='aclweb.org/ACL/ARR/2023/August/Area_Chairs/-/Recruitment', count=2)

        messages = openreview_client.get_messages(subject='[ARR - August 2023] Area Chair Invitation accepted')
        assert len(messages) == 2

        assert 'acextra1@aclrollingreview.com' in openreview_client.get_group('aclweb.org/ACL/ARR/2023/August/Area_Chairs').members
        assert 'acextra2@aclrollingreview.com' in openreview_client.get_group('aclweb.org/ACL/ARR/2023/August/Area_Chairs').members

        openreview_client.remove_members_from_group(
            'aclweb.org/ACL/ARR/2023/August/Area_Chairs',
            [
                'acextra1@aclrollingreview.com',
                'acextra2@aclrollingreview.com'
            ]
        )

    def test_reviewer_recruitment(self, client, openreview_client, helpers, request_page, selenium):

        pc_client = openreview.Client(username='pc@aclrollingreview.org', password=helpers.strong_password)
        request_form=pc_client.get_notes(invitation='openreview.net/Support/-/Request_Form')[1]

        reviewer_details = '''reviewerextra1@aclrollingreview.com, Reviewer ARRExtraOne
reviewerextra2@aclrollingreview.com, Reviewer ARRExtraTwo
'''
        pc_client.post_note(openreview.Note(
            content={
                'title': 'Recruitment',
                'invitee_role': 'Reviewers',
                'invitee_details': reviewer_details,
                'invitation_email_subject': '[ARR August 2023] Invitation to serve as {{invitee_role}}',
                'invitation_email_content': 'Dear {{fullname}},\n\nYou have been nominated by the program chair committee of ACL ARR 2023 August to serve as {{invitee_role}}.\n\n{{invitation_url}}\n\nCheers!\n\nProgram Chairs'
            },
            forum=request_form.forum,
            replyto=request_form.forum,
            invitation='openreview.net/Support/-/Request{}/Recruitment'.format(request_form.number),
            readers=['aclweb.org/ACL/ARR/2023/August/Program_Chairs', 'openreview.net/Support'],
            signatures=['~Program_ARRChair1'],
            writers=[]
        ))

        helpers.await_queue()

        assert len(openreview_client.get_group('aclweb.org/ACL/ARR/2023/August/Reviewers/Invited').members) == 2
        assert len(openreview_client.get_group('aclweb.org/ACL/ARR/2023/August/Reviewers/Declined').members) == 0

        messages = openreview_client.get_messages(subject = '[ARR August 2023] Invitation to serve as Reviewer')
        assert len(messages) == 2

        for idx, message in enumerate(messages):
            text = message['content']['text']

            invitation_url = re.search('https://.*\n', text).group(0).replace('https://openreview.net', 'http://localhost:3030').replace('&amp;', '&')[:-1]
            if idx == 0:
                helpers.respond_invitation(selenium, request_page, invitation_url, accept=True)
            else:
                helpers.respond_invitation(selenium, request_page, invitation_url, accept=False)

        helpers.await_queue_edit(openreview_client, invitation='aclweb.org/ACL/ARR/2023/August/Reviewers/-/Recruitment', count=2)

        messages = openreview_client.get_messages(subject='[ARR - August 2023] Reviewer Invitation accepted')
        assert len(messages) == 1
        messages = openreview_client.get_messages(subject='[ARR - August 2023] Reviewer Invitation declined')
        assert len(messages) == 1

        assert len(openreview_client.get_group('aclweb.org/ACL/ARR/2023/August/Reviewers/Invited').members) == 2
        assert len(openreview_client.get_group('aclweb.org/ACL/ARR/2023/August/Reviewers/Declined').members) == 1

        assert 'reviewerextra1@aclrollingreview.com' in openreview_client.get_group('aclweb.org/ACL/ARR/2023/August/Reviewers').members

        openreview_client.remove_members_from_group(
            'aclweb.org/ACL/ARR/2023/August/Reviewers',
            ['reviewerextra1@aclrollingreview.com']
        )

    
    def test_submission_preprocess(self, client, openreview_client, test_client, helpers):
        # Update the submission preprocess function and test validation for combinations
        # of previous_URL/reassignment_request_area_chair/reassignment_request_reviewers
        pc_client=openreview.Client(username='pc@aclrollingreview.org', password=helpers.strong_password)
        pc_client_v2=openreview.api.OpenReviewClient(username='pc@aclrollingreview.org', password=helpers.strong_password)
        june_request_form=pc_client.get_notes(invitation='openreview.net/Support/-/Request_Form')[0]
        june_venue = openreview.helpers.get_conference(client, june_request_form.id, 'openreview.net/Support')
        test_client = openreview.api.OpenReviewClient(token=test_client.token)
        request_form=pc_client.get_notes(invitation='openreview.net/Support/-/Request_Form')[1]
        august_venue = openreview.helpers.get_conference(client, request_form.id, 'openreview.net/Support')

        generic_note_content = {
            'title': { 'value': 'Paper title '},
            'abstract': { 'value': 'This is an abstract ' },
            'authorids': { 'value': ['~SomeFirstName_User1', 'peter@mail.com', 'andrew@meta.com']},
            'authors': { 'value': ['SomeFirstName User', 'Peter SomeLastName', 'Andrew Mc'] },
            'TLDR': { 'value': 'This is a tldr '},
            'pdf': {'value': '/pdf/' + 'p' * 40 +'.pdf' },
            'paper_type': { 'value': 'Short' },
            'research_area': { 'value': 'Code Models' },
            'research_area_keywords': { 'value': 'A keyword' },
            'languages_studied': { 'value': 'A language' },
            'reassignment_request_area_chair': { 'value': 'This is not a resubmission' },
            'reassignment_request_reviewers': { 'value': 'This is not a resubmission' },
            'software': {'value': '/pdf/' + 'p' * 40 +'.zip' },
            'data': {'value': '/pdf/' + 'p' * 40 +'.zip' },
            'preprint': { 'value': 'yes'},
            'preprint_status': { 'value': 'There is no non-anonymous preprint and we do not intend to release one. (this option is binding)'},
            'existing_preprints': { 'value': 'existing_preprints' },
            'preferred_venue': { 'value': 'ACL' },
            'consent_to_share_data': { 'value': 'yes' },
            'consent_to_share_submission_details': { 'value': 'On behalf of all authors, we agree to the terms above to share our submission details.' },
            "A1_limitations_section": { 'value': 'This paper has a limitations section.' },
            "A2_potential_risks": { 'value': 'Yes' },
            "B_use_or_create_scientific_artifacts": { 'value': 'Yes' },
            "B1_cite_creators_of_artifacts": { 'value': 'Yes' },
            "B2_discuss_the_license_for_artifacts": { 'value': 'Yes' },
            "B3_artifact_use_consistent_with_intended_use": { 'value': 'Yes' },
            "B4_data_contains_personally_identifying_info_or_offensive_content": { 'value': 'Yes' },
            "B5_documentation_of_artifacts": { 'value': 'Yes' },
            "B6_statistics_for_data": { 'value': 'Yes' },
            "C_computational_experiments": { 'value': 'Yes' },
            "C1_model_size_and_budget": { 'value': 'Yes' },
            "C2_experimental_setup_and_hyperparameters": { 'value': 'Yes' },
            "C3_descriptive_statistics": { 'value': 'Yes' },
            "C4_parameters_for_packages": { 'value': 'Yes' },
            "D_human_subjects_including_annotators": { 'value': 'Yes' },
            "D1_instructions_given_to_participants": { 'value': 'Yes' },
            "D2_recruitment_and_payment": { 'value': 'Yes' },
            "D3_data_consent": { 'value': 'Yes' },
            "D4_ethics_review_board_approval": { 'value': 'Yes' },
            "D5_characteristics_of_annotators": { 'value': 'Yes' },
            "E_ai_assistants_in_research_or_writing": { 'value': 'Yes' },
            "E1_information_about_use_of_ai_assistants": { 'value': 'Yes' },
            "author_submission_checklist": { 'value': 'yes' },
            "Association_for_Computational_Linguistics_-_Blind_Submission_License_Agreement": { 'value': "On behalf of all authors, I do not agree" }
        }

        now = datetime.datetime.now()
        due_date = now + datetime.timedelta(days=3)

        invitation_builder = openreview.arr.InvitationBuilder(june_venue)

        pc_client.post_note(
            openreview.Note(
                content={
                    'form_expiration_date': (due_date).strftime('%Y/%m/%d %H:%M'),
                    'author_consent_start_date': (now).strftime('%Y/%m/%d %H:%M'),
                    'author_consent_end_date': (due_date).strftime('%Y/%m/%d %H:%M'),
                    'maximum_load_due_date': (due_date).strftime('%Y/%m/%d %H:%M'),
                    'maximum_load_exp_date': (due_date).strftime('%Y/%m/%d %H:%M'),
                    'ae_checklist_start_date': (now).strftime('%Y/%m/%d %H:%M'),
                    'ae_checklist_due_date': (due_date).strftime('%Y/%m/%d %H:%M'),
                    'ae_checklist_exp_date': (due_date).strftime('%Y/%m/%d %H:%M'),
                    'reviewer_checklist_start_date': (now).strftime('%Y/%m/%d %H:%M'),
                    'reviewer_checklist_due_date': (due_date).strftime('%Y/%m/%d %H:%M'),
                    'reviewer_checklist_exp_date': (due_date).strftime('%Y/%m/%d %H:%M'),
                },
                invitation=f'openreview.net/Support/-/Request{june_request_form.number}/ARR_Configuration',
                forum=june_request_form.id,
                readers=['aclweb.org/ACL/ARR/2023/June/Program_Chairs', 'openreview.net/Support'],
                referent=june_request_form.id,
                replyto=june_request_form.id,
                signatures=['~Program_ARRChair1'],
                writers=[],
            )
        )

        helpers.await_queue()

        # Allow: submission with no previous URL
        note = openreview.api.Note(
            content = generic_note_content
        )

        allowed_note = test_client.post_note_edit(invitation='aclweb.org/ACL/ARR/2023/June/-/Submission',
            signatures=['~SomeFirstName_User1'],
            note=note)
        
        helpers.await_queue_edit(openreview_client, edit_id=allowed_note['id'])

        # Allow: submission with valid previous URL
        note = openreview.api.Note(
            content = {
                    **generic_note_content,
                    'previous_URL': { 'value': f"https://openreview.net/forum?id={allowed_note['note']['id']}" },
                    'reassignment_request_area_chair': {'value': 'No, I want the same area chair from our previous submission (subject to their availability).' },
                    'reassignment_request_reviewers': { 'value': 'Yes, I want a different set of reviewers' },
                    'justification_for_not_keeping_action_editor_or_reviewers': { 'value': 'We would like to keep the same reviewers and area chair because they are experts in the field and have provided valuable feedback on our previous submission.' }
                }
        )

        allowed_note_second = test_client.post_note_edit(invitation='aclweb.org/ACL/ARR/2023/June/-/Submission',
            signatures=['~SomeFirstName_User1'],
            note=openreview.api.Note(
                content = {**generic_note_content}
            )
        )
        
        helpers.await_queue_edit(openreview_client, edit_id=allowed_note_second['id'])

        with pytest.raises(openreview.OpenReviewException, match=r'previous_URL value must be a valid link to an OpenReview submission'):
            test_client.post_note_edit(invitation='aclweb.org/ACL/ARR/2023/August/-/Submission',
                    signatures=['~SomeFirstName_User1'],
                    note=openreview.api.Note(
                    content = {
                        **generic_note_content,
                        'previous_URL': { 'value': f"https://openreview.net//forum?id={allowed_note['note']['id']}" },
                        'reassignment_request_area_chair': {'value': 'No, I want the same area chair from our previous submission (subject to their availability).' },
                        'reassignment_request_reviewers': { 'value': 'Yes, I want a different set of reviewers' },
                        'justification_for_not_keeping_action_editor_or_reviewers': { 'value': 'We would like to keep the same reviewers and area chair because they are experts in the field and have provided valuable feedback on our previous submission.' }
                    }
                ))

        with pytest.raises(openreview.OpenReviewException, match=r'previous_URL value must be a valid link to an OpenReview submission'):
            test_client.post_note_edit(invitation='aclweb.org/ACL/ARR/2023/August/-/Submission',
                    signatures=['~SomeFirstName_User1'],
                    note=openreview.api.Note(
                    content = {
                        **generic_note_content,
                        'previous_URL': { 'value': 'https://openreview.net/pdf?id=1234' },
                        'reassignment_request_area_chair': {'value': 'No, I want the same area chair from our previous submission (subject to their availability).' },
                        'reassignment_request_reviewers': { 'value': 'Yes, I want a different set of reviewers' },
                        'justification_for_not_keeping_action_editor_or_reviewers': { 'value': 'We would like to keep the same reviewers and area chair because they are experts in the field and have provided valuable feedback on our previous submission.' }
                    }
                ))
        
        with pytest.raises(openreview.OpenReviewException, match=r'previous_URL value must be a valid link to an OpenReview submission'):
            test_client.post_note_edit(invitation='aclweb.org/ACL/ARR/2023/August/-/Submission',
                    signatures=['~SomeFirstName_User1'],
                    note=openreview.api.Note(
                    content = {
                        **generic_note_content,
                        'previous_URL': { 'value': 'https://openreview.net/forum?id=1234&replyto=4567' },
                        'reassignment_request_area_chair': {'value': 'No, I want the same area chair from our previous submission (subject to their availability).' },
                        'reassignment_request_reviewers': { 'value': 'Yes, I want a different set of reviewers' },
                        'justification_for_not_keeping_action_editor_or_reviewers': { 'value': 'We would like to keep the same reviewers and area chair because they are experts in the field and have provided valuable feedback on our previous submission.' }
                    }
                ))

        with pytest.raises(openreview.OpenReviewException, match=r'previous_URL value must be a valid link to an OpenReview submission'):
            test_client.post_note_edit(invitation='aclweb.org/ACL/ARR/2023/August/-/Submission',
                    signatures=['~SomeFirstName_User1'],
                    note=openreview.api.Note(
                    content = {
                        **generic_note_content,
                        'previous_URL': { 'value': f'https://openreview.net/forum?id=1234&referrer=[Author%20Console](/group?id=aclweb.org/ACL/ARR/2023/June)' },
                        'reassignment_request_area_chair': {'value': 'No, I want the same area chair from our previous submission (subject to their availability).' },
                        'reassignment_request_reviewers': { 'value': 'Yes, I want a different set of reviewers' },
                        'justification_for_not_keeping_action_editor_or_reviewers': { 'value': 'We would like to keep the same reviewers and area chair because they are experts in the field and have provided valuable feedback on our previous submission.' }
                    }
                ))
                
        # Test with comma-separated URLs
        with pytest.raises(openreview.OpenReviewException, match=r'previous_URL value must be a valid link to an OpenReview submission with the exact format:'):
            test_client.post_note_edit(invitation='aclweb.org/ACL/ARR/2023/August/-/Submission',
                    signatures=['~SomeFirstName_User1'],
                    note=openreview.api.Note(
                    content = {
                        **generic_note_content,
                        'previous_URL': { 'value': f'https://openreview.net/forum?id={allowed_note["note"]["id"]}, https://openreview.net/forum?id=1234' },
                        'reassignment_request_area_chair': {'value': 'No, I want the same area chair from our previous submission (subject to their availability).' },
                        'reassignment_request_reviewers': { 'value': 'Yes, I want a different set of reviewers' },
                        'justification_for_not_keeping_action_editor_or_reviewers': { 'value': 'We would like to keep the same reviewers and area chair because they are experts in the field and have provided valuable feedback on our previous submission.' }
                    }
                ))
                
        # Test with URLs separated by "AND"
        with pytest.raises(openreview.OpenReviewException, match=r'previous_URL value must be a valid link to an OpenReview submission with the exact format:'):
            test_client.post_note_edit(invitation='aclweb.org/ACL/ARR/2023/August/-/Submission',
                    signatures=['~SomeFirstName_User1'],
                    note=openreview.api.Note(
                    content = {
                        **generic_note_content,
                        'previous_URL': { 'value': f'https://openreview.net/forum?id={allowed_note["note"]["id"]} AND https://openreview.net/forum?id=1234' },
                        'reassignment_request_area_chair': {'value': 'No, I want the same area chair from our previous submission (subject to their availability).' },
                        'reassignment_request_reviewers': { 'value': 'Yes, I want a different set of reviewers' },
                        'justification_for_not_keeping_action_editor_or_reviewers': { 'value': 'We would like to keep the same reviewers and area chair because they are experts in the field and have provided valuable feedback on our previous submission.' }
                    }
                ))
                
        # Test with lowercase "and" separator
        with pytest.raises(openreview.OpenReviewException, match=r'previous_URL value must be a valid link to an OpenReview submission with the exact format:'):
            test_client.post_note_edit(invitation='aclweb.org/ACL/ARR/2023/August/-/Submission',
                    signatures=['~SomeFirstName_User1'],
                    note=openreview.api.Note(
                    content = {
                        **generic_note_content,
                        'previous_URL': { 'value': f'https://openreview.net/forum?id={allowed_note["note"]["id"]} and https://openreview.net/forum?id=1234' },
                        'reassignment_request_area_chair': {'value': 'No, I want the same area chair from our previous submission (subject to their availability).' },
                        'reassignment_request_reviewers': { 'value': 'Yes, I want a different set of reviewers' },
                        'justification_for_not_keeping_action_editor_or_reviewers': { 'value': 'We would like to keep the same reviewers and area chair because they are experts in the field and have provided valuable feedback on our previous submission.' }
                    }
                ))

        # Not allowed: submission with invalid previous URL
        with pytest.raises(openreview.OpenReviewException, match=r'previous_URL value must be a valid link to an OpenReview submission'):
            test_client.post_note_edit(invitation='aclweb.org/ACL/ARR/2023/August/-/Submission',
                signatures=['~SomeFirstName_User1'],
                note=openreview.api.Note(
                content = {
                    **generic_note_content,
                    'previous_URL': { 'value': 'https://arxiv.org/abs/1234.56789' },
                    'reassignment_request_area_chair': {'value': 'No, I want the same area chair from our previous submission (subject to their availability).' },
                    'reassignment_request_reviewers': { 'value': 'Yes, I want a different set of reviewers' },
                    'justification_for_not_keeping_action_editor_or_reviewers': { 'value': 'We would like to keep the same reviewers and area chair because they are experts in the field and have provided valuable feedback on our previous submission.' },
                }
            )
        )

        # Not allowed: submission with reassignment requests and no previous URL
        with pytest.raises(openreview.OpenReviewException, match=r'You have selected a reassignment request with no previous URL. Please enter a URL or close and re-open the submission form to clear your reassignment request'):
            test_client.post_note_edit(invitation='aclweb.org/ACL/ARR/2023/August/-/Submission',
                signatures=['~SomeFirstName_User1'],
                note=openreview.api.Note(
                content = {
                    **generic_note_content,
                    'reassignment_request_area_chair': {'value': 'No, I want the same area chair from our previous submission (subject to their availability).' },
                    'reassignment_request_reviewers': { 'value': 'Yes, I want a different set of reviewers' },
                    'justification_for_not_keeping_action_editor_or_reviewers': { 'value': 'We would like to keep the same reviewers and area chair because they are experts in the field and have provided valuable feedback on our previous submission.' },
                }
            )
        )

        # Not allowed: submission with reviewer reassignment request and no previous URL
        with pytest.raises(openreview.OpenReviewException, match=r'You have selected a reassignment request with no previous URL. Please enter a URL or close and re-open the submission form to clear your reassignment request'):
            test_client.post_note_edit(invitation='aclweb.org/ACL/ARR/2023/August/-/Submission',
                signatures=['~SomeFirstName_User1'],
                note=openreview.api.Note(
                content = {
                    **generic_note_content,
                    'reassignment_request_reviewers': { 'value': 'Yes, I want a different set of reviewers' },
                    'justification_for_not_keeping_action_editor_or_reviewers': { 'value': 'We would like to keep the same reviewers and area chair because they are experts in the field and have provided valuable feedback on our previous submission.' },
                }
            )
        )

        # Not allowed: submission with AE reassignment request and no previous URL
        with pytest.raises(openreview.OpenReviewException, match=r'You have selected a reassignment request with no previous URL. Please enter a URL or close and re-open the submission form to clear your reassignment request'):
            test_client.post_note_edit(invitation='aclweb.org/ACL/ARR/2023/August/-/Submission',
                signatures=['~SomeFirstName_User1'],
                note=openreview.api.Note(
                content = {
                    **generic_note_content,
                    'reassignment_request_area_chair': {'value': 'No, I want the same area chair from our previous submission (subject to their availability).' },
                    'justification_for_not_keeping_action_editor_or_reviewers': { 'value': 'We would like to keep the same reviewers and area chair because they are experts in the field and have provided valuable feedback on our previous submission.' },
                }
            )
        )

        # Not allowed: submission with previous URL and no reassignment requests
        with pytest.raises(openreview.OpenReviewException, match=r'Since you are re-submitting, please indicate if you would like the same editors/reviewers as your indicated previous submission'):
            test_client.post_note_edit(invitation='aclweb.org/ACL/ARR/2023/August/-/Submission',
                signatures=['~SomeFirstName_User1'],
                note=openreview.api.Note(
                content = {
                    **generic_note_content,
                    'previous_URL': { 'value': f"https://openreview.net/forum?id={allowed_note['note']['id']}" },
                    'justification_for_not_keeping_action_editor_or_reviewers': { 'value': 'We would like to keep the same reviewers and area chair because they are experts in the field and have provided valuable feedback on our previous submission.' },
                }
            )
        )

        # Not allowed: submission with previous URL and only reviewer reassignment request
        with pytest.raises(openreview.OpenReviewException, match=r'Since you are re-submitting, please indicate if you would like the same editors/reviewers as your indicated previous submission'):
            test_client.post_note_edit(invitation='aclweb.org/ACL/ARR/2023/August/-/Submission',
                signatures=['~SomeFirstName_User1'],
                note=openreview.api.Note(
                content = {
                    **generic_note_content,
                    'previous_URL': { 'value': f"https://openreview.net/forum?id={allowed_note['note']['id']}" },
                    'reassignment_request_reviewers': { 'value': 'Yes, I want a different set of reviewers' },
                    'justification_for_not_keeping_action_editor_or_reviewers': { 'value': 'We would like to keep the same reviewers and area chair because they are experts in the field and have provided valuable feedback on our previous submission.' },
                }
            )
        )

        # Not allowed: submission with previous URL and only AE reassignment request
        with pytest.raises(openreview.OpenReviewException, match=r'Since you are re-submitting, please indicate if you would like the same editors/reviewers as your indicated previous submission'):
            test_client.post_note_edit(invitation='aclweb.org/ACL/ARR/2023/August/-/Submission',
                signatures=['~SomeFirstName_User1'],
                note=openreview.api.Note(
                content = {
                    **generic_note_content,
                    'previous_URL': { 'value': f"https://openreview.net/forum?id={allowed_note['note']['id']}" },
                    'reassignment_request_area_chair': {'value': 'No, I want the same area chair from our previous submission (subject to their availability).' },
                    'justification_for_not_keeping_action_editor_or_reviewers': { 'value': 'We would like to keep the same reviewers and area chair because they are experts in the field and have provided valuable feedback on our previous submission.' },
                }
            )
        )

        # Call post submission to setup for reassignment tests
        pc_client.post_note(openreview.Note(
            invitation=f'openreview.net/Support/-/Request{june_request_form.number}/Revision',
            forum=june_request_form.id,
            readers=['aclweb.org/ACL/ARR/2023/June/Program_Chairs', 'openreview.net/Support'],
            referent=june_request_form.id,
            replyto=june_request_form.id,
            signatures=['~Program_ARRChair1'],
            writers=[],
            content={
                'title': 'ACL Rolling Review 2023 - June',
                'Official Venue Name': 'ACL Rolling Review 2023 - June',
                'Abbreviated Venue Name': 'ARR - June 2023',
                'Official Website URL': 'http://aclrollingreview.org',
                'program_chair_emails': ['editors@aclrollingreview.org', 'pc@aclrollingreview.org'],
                'contact_email': 'editors@aclrollingreview.org',
                'Venue Start Date': '2023/08/01',
                'Submission Start Date': (now - datetime.timedelta(days=10)).strftime('%Y/%m/%d'),
                'Submission Deadline': (now + datetime.timedelta(seconds=10)).strftime('%Y/%m/%d'),
                'publication_chairs':'No, our venue does not have Publication Chairs',  
                'Location': 'Virtual',
                'submission_reviewer_assignment': 'Automatic',
                'How did you hear about us?': 'ML conferences',
                'Expected Submissions': '100',
                'use_recruitment_template': 'Yes',
                'Additional Submission Options': arr_submission_content,
                'remove_submission_options': ['keywords'],
                'homepage_override': { #TODO: Update
                    'location': 'Hawaii, USA',
                    'instructions': 'For author guidelines, please click [here](https://icml.cc/Conferences/2023/StyleAuthorInstructions)'
                }
            }
        ))

        helpers.await_queue()
        helpers.await_queue_edit(openreview_client, 'aclweb.org/ACL/ARR/2023/June/Reviewers/-/Submission_Group-0-1', count=2)
        helpers.await_queue_edit(openreview_client, 'aclweb.org/ACL/ARR/2023/June/Area_Chairs/-/Submission_Group-0-1', count=2)

    def test_no_assignment_preprocess(self, client, openreview_client, test_client, helpers):
        # If reviewer assignment quota is not set, check that pre-processes don't fail
        pc_client=openreview.Client(username='pc@aclrollingreview.org', password=helpers.strong_password)
        pc_client_v2=openreview.api.OpenReviewClient(username='pc@aclrollingreview.org', password=helpers.strong_password)
        request_form=pc_client.get_notes(invitation='openreview.net/Support/-/Request_Form')[0]
        june_venue = openreview.helpers.get_conference(client, request_form.id, 'openreview.net/Support')
        test_client = openreview.api.OpenReviewClient(token=test_client.token)
        submissions = june_venue.get_submissions(sort='number:asc')
        assert len(submissions) == 3
        assert pc_client_v2.get_group('aclweb.org/ACL/ARR/2023/June/Submission1/Reviewers')
        assert pc_client_v2.get_group('aclweb.org/ACL/ARR/2023/June/Submission2/Reviewers')
        assert pc_client_v2.get_group('aclweb.org/ACL/ARR/2023/June/Submission3/Reviewers')

        assert pc_client_v2.get_group('aclweb.org/ACL/ARR/2023/June/Submission1/Area_Chairs')
        assert pc_client_v2.get_group('aclweb.org/ACL/ARR/2023/June/Submission2/Area_Chairs')
        assert pc_client_v2.get_group('aclweb.org/ACL/ARR/2023/June/Submission3/Area_Chairs')


        client.post_note(openreview.Note(
            content={
                'title': 'Paper Matching Setup',
                'matching_group': 'aclweb.org/ACL/ARR/2023/June/Reviewers',
                'compute_conflicts': 'NeurIPS',
                'compute_conflicts_N_years': '3',
                'compute_affinity_scores': 'No'
            },
            forum=request_form.id,
            replyto=request_form.id,
            invitation=f'openreview.net/Support/-/Request{request_form.number}/Paper_Matching_Setup',
            readers=['aclweb.org/ACL/ARR/2023/June/Program_Chairs', 'openreview.net/Support'],
            signatures=['~Program_ARRChair1'],
            writers=[]
        ))
        helpers.await_queue()

        openreview_client.post_note_edit(
            invitation='aclweb.org/ACL/ARR/2023/June/Reviewers/-/Assignment_Configuration',
            readers=[june_venue.id],
            writers=[june_venue.id],
            signatures=[june_venue.id],
            note=openreview.api.Note(
                content={
                    "title": { "value": 'rev-matching'},
                    "user_demand": { "value": '3'},
                    "max_papers": { "value": '6'},
                    "min_papers": { "value": '0'},
                    "alternates": { "value": '10'},
                    "paper_invitation": { "value": 'aclweb.org/ACL/ARR/2023/June/-/Submission&content.venueid=aclweb.org/ACL/ARR/2023/June/Submission'},
                    "match_group": { "value": 'aclweb.org/ACL/ARR/2023/June/Reviewers'},
                    "aggregate_score_invitation": { "value": 'aclweb.org/ACL/ARR/2023/June/Reviewers/-/Aggregate_Score'},
                    "conflicts_invitation": { "value": 'aclweb.org/ACL/ARR/2023/June/Reviewers/-/Conflict'},
                    "solver": { "value": 'FairFlow'},
                    "status": { "value": 'Deployed'},
                }
            )
        )

        for reviewer_id in [
            '~Reviewer_ARROne1',
            '~Reviewer_ARRTwo1',
            '~Reviewer_ARRThree1',
            '~Reviewer_ARRFour1',
            '~Reviewer_ARRFive1',
        ]:
            assert openreview_client.post_edge(openreview.api.Edge(
                invitation = 'aclweb.org/ACL/ARR/2023/June/Reviewers/-/Proposed_Assignment',
                head = submissions[0].id,
                tail = reviewer_id,
                signatures = ['aclweb.org/ACL/ARR/2023/June/Program_Chairs'],
                weight = 1,
                label = 'rev-matching'
            ))
        assert len(openreview_client.get_all_edges(
            invitation='aclweb.org/ACL/ARR/2023/June/Reviewers/-/Proposed_Assignment',
            head=submissions[0].id
        )) == 5

        june_venue.set_assignments(assignment_title='rev-matching', committee_id='aclweb.org/ACL/ARR/2023/June/Reviewers', overwrite=True, enable_reviewer_reassignment=True)
        
        #Check that the right max papers is set
        max_load_name = june_venue.get_custom_max_papers_id('Reviewers')
        max_paper_invitation = openreview_client.get_invitation(id=f"{june_venue.id}/{max_load_name}")
        assert max_paper_invitation.edit['weight']['param']['default'] == 6

        ## Break quotas
        assert openreview_client.post_edge(openreview.api.Edge(
            invitation = 'aclweb.org/ACL/ARR/2023/June/Reviewers/-/Assignment',
            head = submissions[0].id,
            tail = '~Reviewer_ARRSix1',
            signatures = ['aclweb.org/ACL/ARR/2023/June/Program_Chairs'],
            weight = 1
        ))
        assert openreview_client.post_edge(openreview.api.Edge(
            invitation = 'aclweb.org/ACL/ARR/2023/June/Reviewers/-/Invite_Assignment',
            head = submissions[0].id,
            tail = 'invitereviewerjune@aclrollingreview.org',
            signatures = ['aclweb.org/ACL/ARR/2023/June/Program_Chairs'],
            weight = 0,
            label = "Invitation Sent"
        ))





    def test_copy_members(self, client, openreview_client, helpers):
        # Create a previous cycle (2023/June) and test the script that copies all roles
        # (reviewers/ACs/SACs/ethics reviewers/ethics chairs) into the current cycle (2023/August)

        # Create groups for previous cycle
        pc_client=openreview.Client(username='pc@aclrollingreview.org', password=helpers.strong_password)
        pc_client_v2=openreview.api.OpenReviewClient(username='pc@aclrollingreview.org', password=helpers.strong_password)
        request_form=pc_client.get_notes(invitation='openreview.net/Support/-/Request_Form')[0]
        june_venue = openreview.helpers.get_conference(client, request_form.id, 'openreview.net/Support')
        request_form=pc_client.get_notes(invitation='openreview.net/Support/-/Request_Form')[1]
        august_venue = openreview.helpers.get_conference(client, request_form.id, 'openreview.net/Support')

        now = datetime.datetime.now()

        pc_client.post_note(
            openreview.Note(
                content={
                    'previous_cycle': 'aclweb.org/ACL/ARR/2023/June',
                    'setup_shared_data_date': (openreview.tools.datetime.datetime.now() - datetime.timedelta(minutes=10)).strftime('%Y/%m/%d %H:%M')
                },
                invitation=f'openreview.net/Support/-/Request{request_form.number}/ARR_Configuration',
                forum=request_form.id,
                readers=['aclweb.org/ACL/ARR/2023/August/Program_Chairs', 'openreview.net/Support'],
                referent=request_form.id,
                replyto=request_form.id,
                signatures=['~Program_ARRChair1'],
                writers=[],
            )
        )

        helpers.await_queue_edit(openreview_client, 'aclweb.org/ACL/ARR/2023/August/-/Share_Data-0-1', count=1)

        # Call twice to ensure data only gets copied once
        pc_client.post_note(
            openreview.Note(
                content={
                    'previous_cycle': 'aclweb.org/ACL/ARR/2023/June',
                    'setup_shared_data_date': (openreview.tools.datetime.datetime.now() - datetime.timedelta(minutes=3)).strftime('%Y/%m/%d %H:%M')
                },
                invitation=f'openreview.net/Support/-/Request{request_form.number}/ARR_Configuration',
                forum=request_form.id,
                readers=['aclweb.org/ACL/ARR/2023/August/Program_Chairs', 'openreview.net/Support'],
                referent=request_form.id,
                replyto=request_form.id,
                signatures=['~Program_ARRChair1'],
                writers=[],
            )
        )

        helpers.await_queue_edit(openreview_client, 'aclweb.org/ACL/ARR/2023/August/-/Share_Data-0-1', count=2)

        # Find August in readers of groups and registration notes
        assert set(pc_client_v2.get_group(june_venue.get_reviewers_id()).members).difference({'~AC_ARROne1', '~SAC_ARROne1'}) == set(pc_client_v2.get_group(august_venue.get_reviewers_id()).members)
        assert set(pc_client_v2.get_group(june_venue.get_area_chairs_id()).members).difference({'~SAC_ARROne1'}) == set(pc_client_v2.get_group(august_venue.get_area_chairs_id()).members)
        assert set(pc_client_v2.get_group(june_venue.get_senior_area_chairs_id()).members) == set(pc_client_v2.get_group(august_venue.get_senior_area_chairs_id()).members)
        assert set(pc_client_v2.get_group(june_venue.get_ethics_reviewers_id()).members) == set(pc_client_v2.get_group(august_venue.get_ethics_reviewers_id()).members)
        assert set(pc_client_v2.get_group(june_venue.get_ethics_chairs_id()).members) == set(pc_client_v2.get_group(august_venue.get_ethics_chairs_id()).members)

        june_reviewer_registration_notes = pc_client_v2.get_all_notes(invitation=f"{june_venue.get_reviewers_id()}/-/Registration")
        august_reviewer_registration_notes = pc_client_v2.get_all_notes(invitation=f"{august_venue.get_reviewers_id()}/-/Registration")
        august_reviewer_signatures = [a.signatures[0] for a in august_reviewer_registration_notes]
        assert set(august_reviewer_signatures) == set([
          '~Reviewer_ARRTwo1',
          '~Reviewer_Alternate_ARROne1'
        ])

        ## Check that signatures only have 1 from Reviewer 2
        assert '~Reviewer_ARRTwoMerge1' not in august_reviewer_signatures

        june_ac_registration_notes = pc_client_v2.get_all_notes(invitation=f"{june_venue.get_area_chairs_id()}/-/Registration")
        august_ac_registration_notes = pc_client_v2.get_all_notes(invitation=f"{august_venue.get_area_chairs_id()}/-/Registration")
        august_ac_signatures = [a.signatures[0] for a in august_ac_registration_notes]
        assert all(j.signatures[0] in august_ac_signatures for j in june_ac_registration_notes)

        june_sac_registration_notes = pc_client_v2.get_all_notes(invitation=f"{june_venue.get_senior_area_chairs_id()}/-/Registration")
        august_sac_registration_notes = pc_client_v2.get_all_notes(invitation=f"{august_venue.get_senior_area_chairs_id()}/-/Registration")
        august_sac_signatures = [a.signatures[0] for a in august_sac_registration_notes]
        assert all(j.signatures[0] in august_sac_signatures for j in june_sac_registration_notes)

        # Load and check for August in readers of edges
        june_reviewers_with_edges = {o['id']['tail']: o['values'][0]['head'] for o in pc_client_v2.get_grouped_edges(invitation=f"{june_venue.get_reviewers_id()}/-/Expertise_Selection", groupby='tail', select='head')}
        june_acs_with_edges = {o['id']['tail']: o['values'][0]['head'] for o in pc_client_v2.get_grouped_edges(invitation=f"{june_venue.get_area_chairs_id()}/-/Expertise_Selection", groupby='tail', select='head')}
        june_sacs_with_edges = {o['id']['tail']: o['values'][0]['head'] for o in pc_client_v2.get_grouped_edges(invitation=f"{june_venue.get_senior_area_chairs_id()}/-/Expertise_Selection", groupby='tail', select='head')}

        august_reviewers_with_edges = {o['id']['tail']: o['values'][0]['head'] for o in pc_client_v2.get_grouped_edges(invitation=f"{august_venue.get_reviewers_id()}/-/Expertise_Selection", groupby='tail', select='head')}
        august_acs_with_edges = {o['id']['tail']: o['values'][0]['head'] for o in pc_client_v2.get_grouped_edges(invitation=f"{august_venue.get_area_chairs_id()}/-/Expertise_Selection", groupby='tail', select='head')}
        august_sacs_with_edges = {o['id']['tail']: o['values'][0]['head'] for o in pc_client_v2.get_grouped_edges(invitation=f"{august_venue.get_senior_area_chairs_id()}/-/Expertise_Selection", groupby='tail', select='head')}
    
        for reviewer, edges in june_reviewers_with_edges.items():
            assert reviewer in august_reviewers_with_edges
            assert set(edges) == set(august_reviewers_with_edges[reviewer])

        for ac, edges in june_acs_with_edges.items():
            assert ac in august_acs_with_edges
            assert set(edges) == set(august_acs_with_edges[ac])

        for sac, edges in june_sacs_with_edges.items():
            assert sac in august_sacs_with_edges
            assert set(edges) == set(august_sacs_with_edges[sac])

        ## Add overlap for deduplication test
        assert all(overlap not in openreview_client.get_group(august_venue.get_reviewers_id()).members for overlap in ['~AC_ARROne1', '~SAC_ARROne1'])
        assert all(overlap not in openreview_client.get_group(august_venue.get_area_chairs_id()).members for overlap in ['~SAC_ARROne1'])

        # Check reviewer license notes
        june_reviewer_license_notes = pc_client_v2.get_all_notes(invitation=f"{june_venue.get_reviewers_id()}/-/License_Agreement")
        august_reviewer_license_notes = pc_client_v2.get_all_notes(invitation=f"{august_venue.get_reviewers_id()}/-/License_Agreement")
        assert len(june_reviewer_license_notes) > len(august_reviewer_license_notes) ## One June reviewer did not agree
        assert '~Reviewer_ARRFour1' in [note.signatures[0] for note in august_reviewer_license_notes]
        assert '~Reviewer_ARRFive1' not in [note.signatures[0] for note in august_reviewer_license_notes]

    def test_unavailability_process_functions(self, client, openreview_client, helpers):
        # Update the process functions for each of the unavailability forms, set up the custom max papers
        # invitations and test that each note posts an edge

        # Load the venues
        now = datetime.datetime.now()
        pc_client=openreview.Client(username='pc@aclrollingreview.org', password=helpers.strong_password)
        pc_client_v2=openreview.api.OpenReviewClient(username='pc@aclrollingreview.org', password=helpers.strong_password)
        request_form=pc_client.get_notes(invitation='openreview.net/Support/-/Request_Form')[0]
        june_venue = openreview.helpers.get_conference(client, request_form.id, 'openreview.net/Support')
        request_form=pc_client.get_notes(invitation='openreview.net/Support/-/Request_Form')[1]
        august_venue = openreview.helpers.get_conference(client, request_form.id, 'openreview.net/Support')
        
        registration_name = 'Registration'
        max_load_name = 'Max_Load_And_Unavailability_Request'
        # r1 r3 r4 r5 should have no notes + edges | r2 ac1 sac1 should have notes + edges (unavailable)
        migrated_reviewers = {'~Reviewer_ARRTwo1'}
        august_reviewer_notes = pc_client_v2.get_all_notes(invitation=f"{august_venue.get_reviewers_id()}/-/{max_load_name}")
        assert len(august_reviewer_notes) == len(migrated_reviewers)
        assert set([note.signatures[0] for note in august_reviewer_notes]) == migrated_reviewers
        assert all(note.content['maximum_load_this_cycle']['value'] == 0 for note in august_reviewer_notes)

        migrated_acs = {'~AC_ARROne1'}
        august_ac_notes = pc_client_v2.get_all_notes(invitation=f"{august_venue.get_area_chairs_id()}/-/{max_load_name}")
        assert len(august_ac_notes) == len(migrated_acs)
        assert set([note.signatures[0] for note in august_ac_notes]) == migrated_acs
        assert all(note.content['maximum_load_this_cycle']['value'] == 0 for note in august_ac_notes)

        migrated_sacs = {'~SAC_ARROne1'}
        august_sacs_notes = pc_client_v2.get_all_notes(invitation=f"{august_venue.get_senior_area_chairs_id()}/-/{max_load_name}")
        assert len(august_sacs_notes) == len(migrated_sacs)
        assert set([note.signatures[0] for note in august_sacs_notes]) == migrated_sacs
        assert all('will NOT be able to serve' in note.content['availability_this_cycle']['value'] for note in august_sacs_notes)

        august_reviewer_edges = {o['id']['tail']: [j['weight'] for j in o['values']] for o in pc_client_v2.get_grouped_edges(invitation=f"{august_venue.get_reviewers_id()}/-/Custom_Max_Papers", groupby='tail', select='weight')}
        august_ac_edges = {o['id']['tail']: [j['weight'] for j in o['values']] for o in pc_client_v2.get_grouped_edges(invitation=f"{august_venue.get_area_chairs_id()}/-/Custom_Max_Papers", groupby='tail', select='weight')}
        august_sac_edges = {o['id']['tail']: [j['weight'] for j in o['values']] for o in pc_client_v2.get_grouped_edges(invitation=f"{august_venue.get_senior_area_chairs_id()}/-/Custom_Max_Papers", groupby='tail', select='weight')}

        assert migrated_reviewers == set(august_reviewer_edges.keys())
        assert migrated_acs == set(august_ac_edges.keys())
        assert migrated_sacs == set(august_sac_edges.keys())
        assert all(len(weight_list) == 1 for weight_list in august_reviewer_edges.values())
        assert all(len(weight_list) == 1 for weight_list in august_ac_edges.values())
        assert all(len(weight_list) == 1 for weight_list in august_sac_edges.values())
        assert all(
            all(value == 0 for value in weight_list) 
            for weight_list in august_reviewer_edges.values()
        )
        assert all(
            all(value == 0 for value in weight_list)
            for weight_list in august_ac_edges.values()
        )
        assert all(
            all(value == 0 for value in weight_list)
            for weight_list in august_sac_edges.values()
        )

        # Test posting new notes and finding the edges
        ethics_reviewer_client = openreview.api.OpenReviewClient(username = 'reviewerethics@aclrollingreview.com', password=helpers.strong_password)
        reviewer_client = openreview.api.OpenReviewClient(username = 'reviewer1@aclrollingreview.com', password=helpers.strong_password)
        ac_client = openreview.api.OpenReviewClient(username = 'ac2@aclrollingreview.com', password=helpers.strong_password)
        sac_client = openreview.api.OpenReviewClient(username = 'sac2@aclrollingreview.com', password=helpers.strong_password)

        ethics_reviewer_note_edit = ethics_reviewer_client.post_note_edit(
                invitation=f'{august_venue.get_ethics_reviewers_id()}/-/{max_load_name}',
                signatures=['~EthicsReviewer_ARROne1'],
                note=openreview.api.Note(
                    content = {
                        'maximum_load_this_cycle': { 'value': 4 },
                        'maximum_load_this_cycle_for_resubmissions': { 'value': 'No' },
                    }
                )
            ) 
        reviewer_note_edit = reviewer_client.post_note_edit(
                invitation=f'{august_venue.get_reviewers_id()}/-/{max_load_name}',
                signatures=['~Reviewer_Alternate_ARROne1'],
                note=openreview.api.Note(
                    content = {
                        'maximum_load_this_cycle': { 'value': 4 },
                        'maximum_load_this_cycle_for_resubmissions': { 'value': 'No' },
                        'meta_data_donation': { 'value': 'Yes, I consent to donating anonymous metadata of my review for research.' },
                    }
                )
            ) 
        ac_note_edit = ac_client.post_note_edit(
            invitation=f'{august_venue.get_area_chairs_id()}/-/{max_load_name}',
            signatures=['~AC_ARRTwo1'],
            note=openreview.api.Note(
                content = {
                    'maximum_load_this_cycle': { 'value': 6 },
                    'maximum_load_this_cycle_for_resubmissions': { 'value': 'Yes' },
                }
            )
        )
        sac_note_edit = sac_client.post_note_edit(
            invitation=f'{august_venue.get_senior_area_chairs_id()}/-/{max_load_name}',
            signatures=['~SAC_ARRTwo1'],
            note=openreview.api.Note(
                content = {
                    'availability_this_cycle': { 'value': 'I confirm that I will serve as SAC in this cycle, with the review load shared equally with other SACs (computed per track in conference-associated cycles).' },
                }
            )
        )

        helpers.await_queue_edit(openreview_client, edit_id=ethics_reviewer_note_edit['id'])
        helpers.await_queue_edit(openreview_client, edit_id=reviewer_note_edit['id'])
        helpers.await_queue_edit(openreview_client, edit_id=ac_note_edit['id'])
        helpers.await_queue_edit(openreview_client, edit_id=sac_note_edit['id'])

        august_ethics_reviewer_edges = {o['id']['tail']: [j['weight'] for j in o['values']] for o in pc_client_v2.get_grouped_edges(invitation=f"{august_venue.get_ethics_reviewers_id()}/-/Custom_Max_Papers", groupby='tail', select='weight')}
        august_reviewer_edges = {o['id']['tail']: [j['weight'] for j in o['values']] for o in pc_client_v2.get_grouped_edges(invitation=f"{august_venue.get_reviewers_id()}/-/Custom_Max_Papers", groupby='tail', select='weight')}
        august_ac_edges = {o['id']['tail']: [j['weight'] for j in o['values']] for o in pc_client_v2.get_grouped_edges(invitation=f"{august_venue.get_area_chairs_id()}/-/Custom_Max_Papers", groupby='tail', select='weight')}
        assert '~EthicsReviewer_ARROne1' in august_ethics_reviewer_edges
        assert len(august_ethics_reviewer_edges['~EthicsReviewer_ARROne1']) == 1 and set(august_ethics_reviewer_edges['~EthicsReviewer_ARROne1']) == {4}
        assert '~Reviewer_ARROne1' in august_reviewer_edges
        assert len(august_reviewer_edges['~Reviewer_ARROne1']) == 1 and set(august_reviewer_edges['~Reviewer_ARROne1']) == {4}
        assert '~AC_ARRTwo1' in august_ac_edges
        assert len(august_ac_edges['~AC_ARRTwo1']) == 1 and set(august_ac_edges['~AC_ARRTwo1']) == {6}

        # Test editing
        ethics_reviewer_note_edit = ethics_reviewer_client.post_note_edit(
                invitation=f'{august_venue.get_ethics_reviewers_id()}/-/{max_load_name}',
                signatures=['~EthicsReviewer_ARROne1'],
                note=openreview.api.Note(
                    id = ethics_reviewer_note_edit['note']['id'],
                    content = {
                        'maximum_load_this_cycle': { 'value': 5 },
                        'maximum_load_this_cycle_for_resubmissions': { 'value': 'No' },
                    }
                )
            )
        reviewer_note_edit = reviewer_client.post_note_edit(
                invitation=f'{august_venue.get_reviewers_id()}/-/{max_load_name}',
                signatures=['~Reviewer_Alternate_ARROne1'],
                note=openreview.api.Note(
                    id = reviewer_note_edit['note']['id'],
                    content = {
                        'maximum_load_this_cycle': { 'value': 5 },
                        'maximum_load_this_cycle_for_resubmissions': { 'value': 'No' },
                        'meta_data_donation': { 'value': 'Yes, I consent to donating anonymous metadata of my review for research.' },
                    }
                )
            ) 
        ac_note_edit = ac_client.post_note_edit(
            invitation=f'{august_venue.get_area_chairs_id()}/-/{max_load_name}',
            signatures=['~AC_ARRTwo1'],
            note=openreview.api.Note(
                id = ac_note_edit['note']['id'],
                content = {
                    'maximum_load_this_cycle': { 'value': 7 },
                    'maximum_load_this_cycle_for_resubmissions': { 'value': 'Yes' }
                }
            )
        )

        helpers.await_queue_edit(openreview_client, edit_id=ethics_reviewer_note_edit['id'])
        helpers.await_queue_edit(openreview_client, edit_id=reviewer_note_edit['id'])
        helpers.await_queue_edit(openreview_client, edit_id=ac_note_edit['id'])

        august_ethics_reviewer_edges = {o['id']['tail']: [j['weight'] for j in o['values']] for o in pc_client_v2.get_grouped_edges(invitation=f"{august_venue.get_ethics_reviewers_id()}/-/Custom_Max_Papers", groupby='tail', select='weight')}
        august_reviewer_edges = {o['id']['tail']: [j['weight'] for j in o['values']] for o in pc_client_v2.get_grouped_edges(invitation=f"{august_venue.get_reviewers_id()}/-/Custom_Max_Papers", groupby='tail', select='weight')}
        august_ac_edges = {o['id']['tail']: [j['weight'] for j in o['values']] for o in pc_client_v2.get_grouped_edges(invitation=f"{august_venue.get_area_chairs_id()}/-/Custom_Max_Papers", groupby='tail', select='weight')}
        assert '~EthicsReviewer_ARROne1' in august_ethics_reviewer_edges
        assert len(august_ethics_reviewer_edges['~EthicsReviewer_ARROne1']) == 1 and set(august_ethics_reviewer_edges['~EthicsReviewer_ARROne1']) == {5}
        assert '~Reviewer_ARROne1' in august_reviewer_edges
        assert len(august_reviewer_edges['~Reviewer_ARROne1']) == 1 and set(august_reviewer_edges['~Reviewer_ARROne1']) == {5}
        assert '~AC_ARRTwo1' in august_ac_edges
        assert len(august_ac_edges['~AC_ARRTwo1']) == 1 and set(august_ac_edges['~AC_ARRTwo1']) == {7}

        # Test deleting
        ethics_reviewer_note_edit = ethics_reviewer_client.post_note_edit(
                invitation=f'{august_venue.get_ethics_reviewers_id()}/-/{max_load_name}',
                signatures=['~EthicsReviewer_ARROne1'],
                note=openreview.api.Note(
                    id = ethics_reviewer_note_edit['note']['id'],
                    ddate = openreview.tools.datetime_millis(now),
                    content = {
                        'maximum_load_this_cycle': { 'value': 5 },
                        'maximum_load_this_cycle_for_resubmissions': { 'value': 'No' },
                    }
                )
            )
        reviewer_note_edit = reviewer_client.post_note_edit(
                invitation=f'{august_venue.get_reviewers_id()}/-/{max_load_name}',
                signatures=['~Reviewer_Alternate_ARROne1'],
                note=openreview.api.Note(
                    id = reviewer_note_edit['note']['id'],
                    ddate = openreview.tools.datetime_millis(now),
                    content = {
                        'maximum_load_this_cycle': { 'value': 5 },
                        'maximum_load_this_cycle_for_resubmissions': { 'value': 'No' },
                        'meta_data_donation': { 'value': 'Yes, I consent to donating anonymous metadata of my review for research.' },
                    }
                )
            ) 
        ac_note_edit = ac_client.post_note_edit(
            invitation=f'{august_venue.get_area_chairs_id()}/-/{max_load_name}',
            signatures=['~AC_ARRTwo1'],
            note=openreview.api.Note(
                id = ac_note_edit['note']['id'],
                ddate = openreview.tools.datetime_millis(now),
                content = {
                    'maximum_load_this_cycle': { 'value': 7 },
                    'maximum_load_this_cycle_for_resubmissions': { 'value': 'Yes' }
                }
            )
        )
        helpers.await_queue_edit(openreview_client, edit_id=ethics_reviewer_note_edit['id'])
        helpers.await_queue_edit(openreview_client, edit_id=reviewer_note_edit['id'])
        helpers.await_queue_edit(openreview_client, edit_id=ac_note_edit['id'])

        august_ethics_reviewer_edges = {o['id']['tail']: [j['weight'] for j in o['values']] for o in pc_client_v2.get_grouped_edges(invitation=f"{august_venue.get_ethics_reviewers_id()}/-/Custom_Max_Papers", groupby='tail', select='weight')}
        august_reviewer_edges = {o['id']['tail']: [j['weight'] for j in o['values']] for o in pc_client_v2.get_grouped_edges(invitation=f"{august_venue.get_reviewers_id()}/-/Custom_Max_Papers", groupby='tail', select='weight')}
        august_ac_edges = {o['id']['tail']: [j['weight'] for j in o['values']] for o in pc_client_v2.get_grouped_edges(invitation=f"{august_venue.get_area_chairs_id()}/-/Custom_Max_Papers", groupby='tail', select='weight')}
        assert '~EthicsReviewer_ARROne1' not in august_ethics_reviewer_edges
        assert '~Reviewer_ARROne1' not in august_reviewer_edges
        assert '~AC_ARRTwo1' not in august_ac_edges

        # Set data for resubmission unavailability
        reviewer_five_client = openreview.api.OpenReviewClient(username = 'reviewer5@aclrollingreview.com', password=helpers.strong_password)
        ac_three_client = openreview.api.OpenReviewClient(username = 'ac3@aclrollingreview.com', password=helpers.strong_password)

        reviewer_five_client.post_note_edit(
            invitation=f'{august_venue.get_reviewers_id()}/-/{max_load_name}',
            signatures=['~Reviewer_ARRFive1'],
            note=openreview.api.Note(
                content = {
                    'maximum_load_this_cycle': { 'value': 0 },
                    'maximum_load_this_cycle_for_resubmissions': { 'value': 'Yes' },
                    'meta_data_donation': { 'value': 'Yes, I consent to donating anonymous metadata of my review for research.' },
                }
            )
        ) 
        ac_three_client.post_note_edit(
            invitation=f'{august_venue.get_area_chairs_id()}/-/{max_load_name}',
            signatures=['~AC_ARRThree1'],
            note=openreview.api.Note(
                content = {
                    'maximum_load_this_cycle': { 'value': 0 },
                    'maximum_load_this_cycle_for_resubmissions': { 'value': 'Yes' }
                }
            )
        )

        # Increase load again for AC2
        ac_note_edit = ac_client.post_note_edit(
            invitation=f'{august_venue.get_area_chairs_id()}/-/{max_load_name}',
            signatures=['~AC_ARRTwo1'],
            note=openreview.api.Note(
                content = {
                    'maximum_load_this_cycle': { 'value': 6 },
                    'maximum_load_this_cycle_for_resubmissions': { 'value': 'Yes' }
                }
            )
        )
        
    def test_reviewer_tasks(self, client, openreview_client, helpers):
        reviewer_client = openreview.api.OpenReviewClient(username = 'reviewer1@aclrollingreview.com', password=helpers.strong_password)
        ac_client = openreview.api.OpenReviewClient(username = 'ac1@aclrollingreview.com', password=helpers.strong_password)

        # Recognition tasks
        recognition_edit = reviewer_client.post_note_edit(
            invitation='aclweb.org/ACL/ARR/2023/August/Reviewers/-/Recognition_Request',
            signatures=['~Reviewer_Alternate_ARROne1'],
            note=openreview.api.Note(
                content = {
                    "request_a_letter_of_recognition":{
                        "value": "Yes, please send me a letter of recognition for my service as a reviewer / AE"
                    }
                }    
            )
        )

        assert reviewer_client.get_note(recognition_edit['note']['id'])

        recognition_edit = ac_client.post_note_edit(
            invitation='aclweb.org/ACL/ARR/2023/August/Area_Chairs/-/Recognition_Request',
            signatures=['~AC_ARROne1'],
            note=openreview.api.Note(
                content = {
                    "request_a_letter_of_recognition":{
                        "value": "Yes, please send me a letter of recognition for my service as a reviewer / AE"
                    }
                }    
            )
        )

        assert ac_client.get_note(recognition_edit['note']['id'])

        # License task
        license_edit = reviewer_client.post_note_edit(
            invitation='aclweb.org/ACL/ARR/2023/August/Reviewers/-/License_Agreement',
            signatures=['~Reviewer_Alternate_ARROne1'],
            note=openreview.api.Note(
                content = {
                    "attribution": { "value": "Yes, I wish to be attributed."},
                    "agreement": { "value": "I agree"}
                }    
            )
        )

        assert reviewer_client.get_note(license_edit['note']['id'])

        reviewer_two_client = openreview.api.OpenReviewClient(username = 'reviewer2@aclrollingreview.com', password=helpers.strong_password)
        license_edit = reviewer_two_client.post_note_edit(
            invitation='aclweb.org/ACL/ARR/2023/August/Reviewers/-/License_Agreement',
            signatures=['~Reviewer_ARRTwo1'],
            note=openreview.api.Note(
                content = {
                    "agreement": { "value": "I do not agree"}
                }    
            )
        )

        assert reviewer_two_client.get_note(license_edit['note']['id'])

        license_edit = ac_client.post_note_edit(
            invitation='aclweb.org/ACL/ARR/2023/August/Area_Chairs/-/Metareview_License_Agreement',
            signatures=['~AC_ARROne1'],
            note=openreview.api.Note(
                content = {
                    "agreement":{
                        "value": "I agree"
                    }
                }    
            )
        )

        assert ac_client.get_note(license_edit['note']['id'])

    def test_submissions(self, client, openreview_client, helpers, test_client):

        def _generate_valid_content(i, domains, submission):
            content =  {
                'title': { 'value': 'Paper title ' + str(i) },
                'abstract': { 'value': 'This is an abstract ' + str(i) },
                'authorids': { 'value': ['~SomeFirstName_User1', 'peter@mail.com', 'andrew@' + domains[i % 10]] },
                'authors': { 'value': ['SomeFirstName User', 'Peter SomeLastName', 'Andrew Mc'] },
                'TLDR': { 'value': 'This is a tldr ' + str(i) },
                'pdf': {'value': '/pdf/' + 'p' * 40 +'.pdf' },
                'paper_type': { 'value': 'Short' },
                'research_area': { 'value': 'Code Models' },
                'research_area_keywords': { 'value': 'A keyword' },
                'languages_studied': { 'value': 'A language' },
                'reassignment_request_area_chair': { 'value': 'This is not a resubmission' },
                'reassignment_request_reviewers': { 'value': 'This is not a resubmission' },
                'previous_URL': { 'value': f'https://openreview.net/forum?id={submission.id}' },
                'explanation_of_revisions_PDF': {'value': '/pdf/' + 'p' * 40 +'.pdf' },
                'reassignment_request_area_chair': {'value': 'No, I want the same area chair from our previous submission (subject to their availability).' },
                'reassignment_request_reviewers': { 'value': 'Yes, I want a different set of reviewers' },
                'justification_for_not_keeping_action_editor_or_reviewers': { 'value': 'We would like to keep the same reviewers and area chair because they are experts in the field and have provided valuable feedback on our previous submission.' },
                'software': {'value': '/pdf/' + 'p' * 40 +'.zip' },
                'data': {'value': '/pdf/' + 'p' * 40 +'.zip' },
                'preprint': { 'value': 'yes' if i % 2 == 0 else 'no' },
                'preprint_status': { 'value': 'There is no non-anonymous preprint and we do not intend to release one. (this option is binding)'},
                'existing_preprints': { 'value': 'existing_preprints' },
                'preferred_venue': { 'value': 'ACL' },
                'consent_to_share_data': { 'value': 'yes' },
                'consent_to_share_submission_details': { 'value': 'On behalf of all authors, we agree to the terms above to share our submission details.' },
                "A1_limitations_section": { 'value': 'This paper has a limitations section.' },
                "A2_potential_risks": { 'value': 'Yes' },
                "B_use_or_create_scientific_artifacts": { 'value': 'Yes' },
                "B1_cite_creators_of_artifacts": { 'value': 'Yes' },
                "B2_discuss_the_license_for_artifacts": { 'value': 'Yes' },
                "B3_artifact_use_consistent_with_intended_use": { 'value': 'Yes' },
                "B4_data_contains_personally_identifying_info_or_offensive_content": { 'value': 'Yes' },
                "B5_documentation_of_artifacts": { 'value': 'Yes' },
                "B6_statistics_for_data": { 'value': 'Yes' },
                "C_computational_experiments": { 'value': 'Yes' },
                "C1_model_size_and_budget": { 'value': 'Yes' },
                "C2_experimental_setup_and_hyperparameters": { 'value': 'Yes' },
                "C3_descriptive_statistics": { 'value': 'Yes' },
                "C4_parameters_for_packages": { 'value': 'Yes' },
                "D_human_subjects_including_annotators": { 'value': 'Yes' },
                "D1_instructions_given_to_participants": { 'value': 'Yes' },
                "D2_recruitment_and_payment": { 'value': 'Yes' },
                "D3_data_consent": { 'value': 'Yes' },
                "D4_ethics_review_board_approval": { 'value': 'Yes' },
                "D5_characteristics_of_annotators": { 'value': 'Yes' },
                "E_ai_assistants_in_research_or_writing": { 'value': 'Yes' },
                "E1_information_about_use_of_ai_assistants": { 'value': 'Yes' },
                "author_submission_checklist": { 'value': 'yes' },
                "Association_for_Computational_Linguistics_-_Blind_Submission_License_Agreement": { 'value': "On behalf of all authors, I agree" if i % 2 == 0 else 'On behalf of all authors, I do not agree' }
            }
            return content

        test_client = openreview.api.OpenReviewClient(token=test_client.token)

        pc_client=openreview.Client(username='pc@aclrollingreview.org', password=helpers.strong_password)
        request_form_note=pc_client.get_notes(invitation='openreview.net/Support/-/Request_Form')[1]
        now = datetime.datetime.now()
        due_date = now + datetime.timedelta(days=3)

        june_submission = openreview_client.get_all_notes(invitation='aclweb.org/ACL/ARR/2023/June/-/Submission')[0]

        pc_client.post_note(openreview.Note(
            invitation=f'openreview.net/Support/-/Request{request_form_note.number}/Revision',
            forum=request_form_note.id,
            readers=['aclweb.org/ACL/ARR/2023/August/Program_Chairs', 'openreview.net/Support'],
            referent=request_form_note.id,
            replyto=request_form_note.id,
            signatures=['~Program_ARRChair1'],
            writers=[],
            content={
                'title': 'ACL Rolling Review 2023 - August',
                'Official Venue Name': 'ACL Rolling Review 2023 - August',
                'Abbreviated Venue Name': 'ARR - August 2023',
                'Official Website URL': 'http://aclrollingreview.org',
                'program_chair_emails': ['editors@aclrollingreview.org', 'pc@aclrollingreview.org'],
                'contact_email': 'editors@aclrollingreview.org',
                'Venue Start Date': '2023/08/01',
                'Submission Deadline': due_date.strftime('%Y/%m/%d'),
                'publication_chairs':'No, our venue does not have Publication Chairs',  
                'Location': 'Virtual',
                'submission_reviewer_assignment': 'Automatic',
                'How did you hear about us?': 'ML conferences',
                'Expected Submissions': '100',
                'use_recruitment_template': 'Yes',
                'Additional Submission Options': arr_submission_content,
                'remove_submission_options': ['keywords'],
                'homepage_override': { #TODO: Update
                    'location': 'Hawaii, USA',
                    'instructions': 'For author guidelines, please click [here](https://icml.cc/Conferences/2023/StyleAuthorInstructions)'
                }
            }
        ))

        helpers.await_queue()

        domains = ['umass.edu', 'amazon.com', 'fb.com', 'cs.umass.edu', 'google.com', 'mit.edu', 'deepmind.com', 'co.ux', 'apple.com', 'nvidia.com']
        for i in range(1,102):
            note = openreview.api.Note(
                content = _generate_valid_content(i, domains, june_submission)
            )

            # Reduce SAC load
            if i % 3 == 0: ## Skip first one for testing track not posted to reassignment
                note.content['research_area']['value'] = 'Dialogue and Interactive Systems'

            if i == 1 or i == 101:
                note.content['authors']['value'].append('SAC ARROne')
                note.content['authorids']['value'].append('~SAC_ARROne1')

            if i == 6: ## Remove resubmission information from content
                del note.content['previous_URL']
                del note.content['explanation_of_revisions_PDF']
                note.content['reassignment_request_reviewers']['value'] = 'This is not a resubmission'
                note.content['reassignment_request_area_chair']['value'] = 'This is not a resubmission'
                del note.content['justification_for_not_keeping_action_editor_or_reviewers']

            test_client.post_note_edit(invitation='aclweb.org/ACL/ARR/2023/August/-/Submission',
                signatures=['~SomeFirstName_User1'],
                note=note)

        helpers.await_queue_edit(openreview_client, invitation='aclweb.org/ACL/ARR/2023/August/-/Submission', count=101)

        submissions = openreview_client.get_notes(invitation='aclweb.org/ACL/ARR/2023/August/-/Submission', sort='number:asc', details='replies')
        assert len(submissions) == 101
        assert ['aclweb.org/ACL/ARR/2023/August', '~SomeFirstName_User1', 'peter@mail.com', 'andrew@amazon.com', '~SAC_ARROne1'] == submissions[0].readers
        assert ['~SomeFirstName_User1', 'peter@mail.com', 'andrew@amazon.com', '~SAC_ARROne1'] == submissions[0].content['authorids']['value']

        # Try additional submission posting with August paper
        note = openreview.api.Note(content = _generate_valid_content(0, domains, june_submission))
        with pytest.raises(openreview.OpenReviewException, match=r'The provided URL points to a submission in the current cycle. Please provide a link to a previous ARR submission.'):
            note.content['previous_URL']['value'] = f'https://openreview.net/forum?id={submissions[0].id}'
            test_client.post_note_edit(invitation='aclweb.org/ACL/ARR/2023/August/-/Submission',
                signatures=['~SomeFirstName_User1'],
                note=note
            )

        authors_group = openreview_client.get_group(id='aclweb.org/ACL/ARR/2023/August/Authors')

        for i in range(1,102):
            assert f'aclweb.org/ACL/ARR/2023/August/Submission{i}/Authors' in authors_group.members

        # Post comment as authors to chairs
        test_client = openreview.api.OpenReviewClient(token=test_client.token)
        comment_edit = test_client.post_note_edit(
            invitation=f"aclweb.org/ACL/ARR/2023/August/Submission{submissions[0].number}/-/Author-Editor_Confidential_Comment",
            writers=['aclweb.org/ACL/ARR/2023/August', f'aclweb.org/ACL/ARR/2023/August/Submission{submissions[0].number}/Authors'],
            signatures=[f'aclweb.org/ACL/ARR/2023/August/Submission{submissions[0].number}/Authors'],
            note=openreview.api.Note(
                replyto=submissions[0].id,
                readers=[
                    'aclweb.org/ACL/ARR/2023/August/Program_Chairs',
                    f'aclweb.org/ACL/ARR/2023/August/Submission{submissions[0].number}/Senior_Area_Chairs',
                    f'aclweb.org/ACL/ARR/2023/August/Submission{submissions[0].number}/Area_Chairs',
                    f'aclweb.org/ACL/ARR/2023/August/Submission{submissions[0].number}/Authors'
                ],
                content={
                    "comment": { "value": "This is a comment"}
                }
            )
        )

        helpers.await_queue_edit(openreview_client, edit_id=comment_edit['id'])

        for submission in submissions:
            if submission.number % 2 == 0:# "On behalf of all authors, I agree"
                assert openreview_client.get_invitation(
                    f'aclweb.org/ACL/ARR/2023/August/Submission{submission.number}/-/Blind_Submission_License_Agreement'
                ).duedate == None

            # Add check for counters
            assert submission.content['number_of_reviewer_checklists']['value'] == 0
            assert submission.content['number_of_action_editor_checklists']['value'] == 0

    def test_submitted_author_form(self, client, openreview_client, helpers, test_client, request_page, selenium):
        pc_client=openreview.Client(username='pc@aclrollingreview.org', password=helpers.strong_password)
        pc_client_v2=openreview.api.OpenReviewClient(username='pc@aclrollingreview.org', password=helpers.strong_password)
        request_form=pc_client.get_notes(invitation='openreview.net/Support/-/Request_Form')[1]
        august_venue = openreview.helpers.get_conference(client, request_form.id, 'openreview.net/Support')
        submissions = pc_client_v2.get_notes(invitation='aclweb.org/ACL/ARR/2023/August/-/Submission', sort='number:asc')
        test_client = openreview.api.OpenReviewClient(token=test_client.token)

        # Create registration form
        now = datetime.datetime.now()
        due_date = now + datetime.timedelta(days=3)
        pc_client.post_note(
            openreview.Note(
                content={
                    'reviewer_nomination_start_date': (now).strftime('%Y/%m/%d %H:%M'),
                    'reviewer_nomination_end_date': (due_date).strftime('%Y/%m/%d %H:%M')
                },
                invitation=f'openreview.net/Support/-/Request{request_form.number}/ARR_Configuration',
                forum=request_form.id,
                readers=['aclweb.org/ACL/ARR/2023/August/Program_Chairs', 'openreview.net/Support'],
                referent=request_form.id,
                replyto=request_form.id,
                signatures=['~Program_ARRChair1'],
                writers=[],
            )
        )

        helpers.await_queue()
        assert openreview_client.get_invitation('aclweb.org/ACL/ARR/2023/August/Authors/-/Submitted_Author_Form')

        test_client.post_note_edit(
            invitation=f"aclweb.org/ACL/ARR/2023/August/Authors/-/Submitted_Author_Form",
            signatures=['~SomeFirstName_User1'],
            note=openreview.api.Note(
                content={
                    'confirm_you_are_willing_to_serve_as_a_reviewer_or_ac': {'value': "I will serve as a reviewer or area chair (AC) in this cycle if ARR considers me qualified."},
                    'details_of_reason_for_being_unavailable_to_serve': {'value': ""},
                    'serving_as_a_regular_or_emergency_reviewer_or_ac': {'value': "Yes, I am willing to serve as an emergency reviewer or AC."},
                    'indicate_emergency_reviewer_load': {'value': "3"},
                    'confirm_you_are_qualified_to_review': {'value': "Yes, I meet the ARR requirements to be a reviewer."},
                    'are_you_a_student': {'value': "Yes, I am a Masters student."},
                    'what_is_your_highest_level_of_completed_education': {'value': "Doctorate"},
                    'confirm_your_profile_has_past_domains': {'value': "Yes"},
                    'confirm_your_profile_has_all_email_addresses': {'value': "Yes"},
                    'meta_data_donation': {'value': "Yes, If selected as a reviewer, I consent to donating anonymous metadata of my review for research."},
                    'indicate_your_research_areas': {'value': ["Code Models"]},
                    'indicate_languages_you_study': {'value': "English"},
                    'confirm_your_openreview_profile_contains_a_dblp_link': {'value': "Yes, my OpenReview profile contains a link to a DBLP profile with just my papers."},
                    'provide_your_dblp_url': {'value': "https://dblp.uni-trier.de/pid/84/9011.html"},
                    'confirm_your_openreview_profile_contains_a_semantic_scholar_link': {'value': "Yes, my OpenReview profile contains a link to a Semantic Scholar profile with just my papers."},
                    'provide_your_semantic_scholar_url': {'value': "https://www.semanticscholar.org/author/Jonathan-K.-Kummerfeld/1727211"},
                    'provide_your_acl_anthology_url': {'value': "https://aclanthology.org/people/j/jonathan-k-kummerfeld/"},
                    'attribution': {'value': "Yes, I wish to be attributed."},
                    'agreement': {'value': "I agree"},
                }
            )
        )
        
        # Change dates
        updated_now = datetime.datetime.now()
        pc_client.post_note(
            openreview.Note(
                content={
                    'reviewer_nomination_start_date': (now).strftime('%Y/%m/%d %H:%M'),
                    'reviewer_nomination_end_date': (updated_now).strftime('%Y/%m/%d %H:%M')
                },
                invitation=f'openreview.net/Support/-/Request{request_form.number}/ARR_Configuration',
                forum=request_form.id,
                readers=['aclweb.org/ACL/ARR/2023/August/Program_Chairs', 'openreview.net/Support'],
                referent=request_form.id,
                replyto=request_form.id,
                signatures=['~Program_ARRChair1'],
                writers=[],
            )
        )
        helpers.await_queue()

        # Test that the form is closed "The Invitation aclweb.org/ACL/ARR/2023/August/Authors/-/Submitted_Author_Form has expired"
        with pytest.raises(openreview.OpenReviewException, match=r'The Invitation aclweb.org/ACL/ARR/2023/August/Authors/-/Submitted_Author_Form has expired'):
            test_client.post_note_edit(
                invitation=f"aclweb.org/ACL/ARR/2023/August/Authors/-/Submitted_Author_Form",
                signatures=['~SomeFirstName_User1'],
                note=openreview.api.Note(
                    content={
                        'confirm_you_are_willing_to_serve_as_a_reviewer_or_ac': {'value': "I will serve as a reviewer or area chair (AC) in this cycle if ARR considers me qualified."},
                        'details_of_reason_for_being_unavailable_to_serve': {'value': ""},
                        'serving_as_a_regular_or_emergency_reviewer_or_ac': {'value': "Yes, I am willing to serve as an emergency reviewer or AC."},
                        'indicate_emergency_reviewer_load': {'value': '3'},
                        'confirm_you_are_qualified_to_review': {'value': "Yes, I meet the ARR requirements to be a reviewer."},
                        'are_you_a_student': {'value': "Yes, I am a Masters student."},
                        'what_is_your_highest_level_of_completed_education': {'value': "Doctorate"},
                        'confirm_your_profile_has_past_domains': {'value': "Yes"},
                        'confirm_your_profile_has_all_email_addresses': {'value': "Yes"},
                        'meta_data_donation': {'value': "Yes, If selected as a reviewer, I consent to donating anonymous metadata of my review for research."},
                        'indicate_your_research_areas': {'value': ["Generation"]},
                        'indicate_languages_you_study': {'value': "English"},
                        'confirm_your_openreview_profile_contains_a_dblp_link': {'value': "Yes, my OpenReview profile contains a link to a DBLP profile with just my papers."},
                        'provide_your_dblp_url': {'value': "https://dblp.uni-trier.de/pid/84/9011.html"},
                        'confirm_your_openreview_profile_contains_a_semantic_scholar_link': {'value': "Yes, my OpenReview profile contains a link to a Semantic Scholar profile with just my papers."},
                        'provide_your_semantic_scholar_url': {'value': "https://www.semanticscholar.org/author/Jonathan-K.-Kummerfeld/1727211"},
                        'provide_your_acl_anthology_url': {'value': "https://aclanthology.org/people/j/jonathan-k-kummerfeld/"},
                        'attribution': {'value': "Yes, I wish to be attributed."},
                        'agreement': {'value': "I agree"},
                    }
                )
            )
        
        # Manually add new field
        openreview_client.post_invitation_edit(
            invitations='aclweb.org/ACL/ARR/2023/August/-/Edit',
            readers=['aclweb.org/ACL/ARR/2023/August'],
            writers=['aclweb.org/ACL/ARR/2023/August'],
            signatures=['aclweb.org/ACL/ARR/2023/August'],
            invitation=openreview.api.Invitation(
                id = f"aclweb.org/ACL/ARR/2023/August/Authors/-/Submitted_Author_Form",
                edit = {
                    'note': {
                        'content': {
                            "paper_type": {
                                "value": {
                                    "param": {
                                        "input": "radio",
                                        "enum": [
                                            "Long",
                                            "Short"
                                        ],
                                        "optional": False,
                                        "type": "string"
                                    }
                                },
                                "description": "Long or short. See the CFP for the requirements for long and short papers.",
                                "order": 11
                            }
                        }
                    }
                }
            )
        )
        # Change dates and check that field is in invitation
        pc_client.post_note(
            openreview.Note(
                content={
                    'reviewer_nomination_start_date': (now).strftime('%Y/%m/%d %H:%M'),
                    'reviewer_nomination_end_date': (due_date).strftime('%Y/%m/%d %H:%M')
                },
                invitation=f'openreview.net/Support/-/Request{request_form.number}/ARR_Configuration',
                forum=request_form.id,
                readers=['aclweb.org/ACL/ARR/2023/August/Program_Chairs', 'openreview.net/Support'],
                referent=request_form.id,
                replyto=request_form.id,
                signatures=['~Program_ARRChair1'],
                writers=[],
            )
        )
        helpers.await_queue()

        invitation = openreview_client.get_invitation(f"aclweb.org/ACL/ARR/2023/August/Authors/-/Submitted_Author_Form")
        assert 'paper_type' in invitation.edit['note']['content']

    def test_post_submission(self, client, openreview_client, helpers, test_client, request_page, selenium):

        pc_client=openreview.Client(username='pc@aclrollingreview.org', password=helpers.strong_password)
        pc_client_v2=openreview.api.OpenReviewClient(username='pc@aclrollingreview.org', password=helpers.strong_password)
        request_form=pc_client.get_notes(invitation='openreview.net/Support/-/Request_Form')[1]

        ## assert that no readers exist for any submission
        submissions = pc_client_v2.get_notes(invitation='aclweb.org/ACL/ARR/2023/August/-/Submission', sort='number:asc')
        for submission in submissions:
            assert 'readers' not in submission.content['authors']
            assert 'readers' not in submission.content['authorids']

        ## release preprint submissions
        pc_client.post_note(
            openreview.Note(
                content={
                    'preprint_release_submission_date': (openreview.tools.datetime.datetime.now() - datetime.timedelta(minutes=2)).strftime('%Y/%m/%d %H:%M')
                },
                invitation=f'openreview.net/Support/-/Request{request_form.number}/ARR_Configuration',
                forum=request_form.id,
                readers=['aclweb.org/ACL/ARR/2023/August/Program_Chairs', 'openreview.net/Support'],
                referent=request_form.id,
                replyto=request_form.id,
                signatures=['~Program_ARRChair1'],
                writers=[],
            )
        )

        helpers.await_queue()
        helpers.await_queue_edit(openreview_client, 'aclweb.org/ACL/ARR/2023/August/-/Preprint_Release_Submission-0-1', count=1)
        ## Assert released preprints have hidden authors and authorids
        ## check index 3 and 5 (even paper numbers) specifically
        ## check index 4 has no author readers since they were not released

        submissions = pc_client_v2.get_notes(invitation='aclweb.org/ACL/ARR/2023/August/-/Submission', sort='number:asc')
        assert 'everyone' in submissions[3].readers
        assert 'readers' in submissions[3].content['authors']
        assert 'readers' in submissions[3].content['authorids']
        assert submissions[3].content['authors']['readers'] == [
            'aclweb.org/ACL/ARR/2023/August',
            f"aclweb.org/ACL/ARR/2023/August/Submission4/Authors"
        ]
        assert submissions[3].content['authorids']['readers'] == [
            'aclweb.org/ACL/ARR/2023/August',
            f"aclweb.org/ACL/ARR/2023/August/Submission4/Authors"
        ]
        assert submissions[3].content['justification_for_author_changes']['readers'] == [
            'aclweb.org/ACL/ARR/2023/August',
            f"aclweb.org/ACL/ARR/2023/August/Submission4/Authors"
        ]
        assert submissions[3].content['preprint_status']['readers'] == [
            'aclweb.org/ACL/ARR/2023/August',
            f"aclweb.org/ACL/ARR/2023/August/Submission4/Authors"
        ]
        assert submissions[3].content['preferred_venue']['readers'] == [
            'aclweb.org/ACL/ARR/2023/August',
            f"aclweb.org/ACL/ARR/2023/August/Submission4/Authors"
        ]


        assert 'readers' not in submissions[4].content['authors']
        assert 'readers' not in submissions[4].content['authorids']

        assert 'everyone' in submissions[5].readers
        assert 'readers' in submissions[5].content['authors']
        assert 'readers' in submissions[5].content['authorids']
        assert submissions[5].content['authors']['readers'] == [
            'aclweb.org/ACL/ARR/2023/August',
            f"aclweb.org/ACL/ARR/2023/August/Submission6/Authors"
        ]
        assert submissions[5].content['authorids']['readers'] == [
            'aclweb.org/ACL/ARR/2023/August',
            f"aclweb.org/ACL/ARR/2023/August/Submission6/Authors"
        ]
        assert submissions[5].content['justification_for_author_changes']['readers'] == [
            'aclweb.org/ACL/ARR/2023/August',
            f"aclweb.org/ACL/ARR/2023/August/Submission6/Authors"
        ]
        assert submissions[5].content['preprint_status']['readers'] == [
            'aclweb.org/ACL/ARR/2023/August',
            f"aclweb.org/ACL/ARR/2023/August/Submission6/Authors"
        ]
        assert submissions[5].content['preferred_venue']['readers'] == [
            'aclweb.org/ACL/ARR/2023/August',
            f"aclweb.org/ACL/ARR/2023/August/Submission6/Authors"
        ]

        ## close the submissions
        now = datetime.datetime.now()
        due_date = now - datetime.timedelta(days=1)
        pc_client.post_note(openreview.Note(
            content={
                'title': 'ACL Rolling Review 2023 - August',
                'Official Venue Name': 'ACL Rolling Review 2023 - August',
                'Abbreviated Venue Name': 'ARR - August 2023',
                'Official Website URL': 'http://aclrollingreview.org',
                'program_chair_emails': ['editors@aclrollingreview.org', 'pc@aclrollingreview.org'],
                'contact_email': 'editors@aclrollingreview.org',
                'Venue Start Date': '2023/08/01',
                'Submission Deadline': due_date.strftime('%Y/%m/%d'),
                'Submission Start Date': (now - datetime.timedelta(days=30)).strftime('%Y/%m/%d'),
                'publication_chairs':'No, our venue does not have Publication Chairs',  
                'Location': 'Virtual',
                'submission_reviewer_assignment': 'Automatic',
                'How did you hear about us?': 'ML conferences',
                'Expected Submissions': '100',
                'use_recruitment_template': 'Yes',
                'Additional Submission Options': arr_submission_content,
                'remove_submission_options': ['keywords'],
                'homepage_override': { #TODO: Update
                    'location': 'Hawaii, USA',
                    'instructions': 'For author guidelines, please click [here](https://icml.cc/Conferences/2023/StyleAuthorInstructions)'
                }
            },
            forum=request_form.forum,
            invitation='openreview.net/Support/-/Request{}/Revision'.format(request_form.number),
            readers=['aclweb.org/ACL/ARR/2023/August/Program_Chairs', 'openreview.net/Support'],
            referent=request_form.forum,
            replyto=request_form.forum,
            signatures=['~Program_ARRChair1'],
            writers=[]
        ))

        helpers.await_queue()
        helpers.await_queue_edit(openreview_client, 'aclweb.org/ACL/ARR/2023/August/-/Post_Submission-0-1', count=2)

        withdrawal_invitation = pc_client_v2.get_invitation('aclweb.org/ACL/ARR/2023/August/-/Withdrawal')
        assert withdrawal_invitation.edit['invitation']['edit']['note']['content'] == arr_withdrawal_content
        assert 'confirm_need_to_withdraw' in withdrawal_invitation.edit['invitation']['edit']['note']['content']
        assert 'confirm_penalty_rules' in withdrawal_invitation.edit['invitation']['edit']['note']['content']


        assert len(pc_client_v2.get_all_invitations(invitation='aclweb.org/ACL/ARR/2023/August/-/Withdrawal')) == 101
        assert len(pc_client_v2.get_all_invitations(invitation='aclweb.org/ACL/ARR/2023/August/-/Desk_Rejection')) == 101
        # Discuss with Harold
        #assert len(pc_client_v2.get_all_invitations(invitation='aclweb.org/ACL/ARR/2023/August/-/Reviewer_Checklist')) == 101
        #assert len(pc_client_v2.get_all_invitations(invitation='aclweb.org/ACL/ARR/2023/August/-/Action_Editor_Checklist')) == 101        
        #assert len(pc_client_v2.get_all_invitations(invitation='aclweb.org/ACL/ARR/2023/August/-/Desk_Reject_Verification')) == 101        

        # Open comments
        now = datetime.datetime.now()

        pc_client.post_note(
            openreview.Note(
                content={
                    'commentary_start_date': (now - datetime.timedelta(days=1)).strftime('%Y/%m/%d %H:%M'),
                    'commentary_end_date': (now + datetime.timedelta(days=365)).strftime('%Y/%m/%d %H:%M')
                },
                invitation=f'openreview.net/Support/-/Request{request_form.number}/ARR_Configuration',
                forum=request_form.id,
                readers=['aclweb.org/ACL/ARR/2023/August/Program_Chairs', 'openreview.net/Support'],
                referent=request_form.id,
                replyto=request_form.id,
                signatures=['~Program_ARRChair1'],
                writers=[],
            )
        )

        helpers.await_queue()
        helpers.await_queue_edit(openreview_client, 'aclweb.org/ACL/ARR/2023/August/-/Official_Comment-0-1', count=3)

        submission_invitation = pc_client_v2.get_invitation('aclweb.org/ACL/ARR/2023/August/-/Submission')
        assert submission_invitation.expdate < openreview.tools.datetime_millis(now)

        assert len(pc_client_v2.get_all_invitations(invitation='aclweb.org/ACL/ARR/2023/August/-/Withdrawal')) == 101
        assert len(pc_client_v2.get_all_invitations(invitation='aclweb.org/ACL/ARR/2023/August/-/Desk_Rejection')) == 101
        #assert len(pc_client_v2.get_all_invitations(invitation='aclweb.org/ACL/ARR/2023/August/-/Reviewer_Checklist')) == 101
        #assert len(pc_client_v2.get_all_invitations(invitation='aclweb.org/ACL/ARR/2023/August/-/Action_Editor_Checklist')) == 101
        assert pc_client_v2.get_invitation('aclweb.org/ACL/ARR/2023/August/-/PC_Revision')

        submissions = pc_client_v2.get_notes(invitation='aclweb.org/ACL/ARR/2023/August/-/Submission', sort='number:asc')

        # Check that tasks do not have a duedate still
        for submission in submissions:
            if submission.number % 2 == 0:# "On behalf of all authors, I agree"
                assert openreview_client.get_invitation(
                    f'aclweb.org/ACL/ARR/2023/August/Submission{submission.number}/-/Blind_Submission_License_Agreement'
                ).duedate == None

        assert submissions[0].readers == ['aclweb.org/ACL/ARR/2023/August', 
                                          'aclweb.org/ACL/ARR/2023/August/Submission1/Senior_Area_Chairs',
                                          'aclweb.org/ACL/ARR/2023/August/Submission1/Area_Chairs',
                                          'aclweb.org/ACL/ARR/2023/August/Submission1/Reviewers',
                                          'aclweb.org/ACL/ARR/2023/August/Submission1/Authors']
        assert submissions[0].content['TLDR']['readers'] == ['aclweb.org/ACL/ARR/2023/August', 'aclweb.org/ACL/ARR/2023/August/Submission1/Authors']
        assert submissions[0].content['preprint']['readers'] == ['aclweb.org/ACL/ARR/2023/August', 'aclweb.org/ACL/ARR/2023/August/Submission1/Authors']
        assert submissions[0].content['existing_preprints']['readers'] == ['aclweb.org/ACL/ARR/2023/August', 'aclweb.org/ACL/ARR/2023/August/Submission1/Authors']
        assert submissions[0].content['preferred_venue']['readers'] == ['aclweb.org/ACL/ARR/2023/August', 'aclweb.org/ACL/ARR/2023/August/Submission1/Authors']
        assert submissions[0].content['consent_to_share_data']['readers'] == ['aclweb.org/ACL/ARR/2023/August', 'aclweb.org/ACL/ARR/2023/August/Submission1/Authors']
        assert 'readers' not in submissions[0].content['software']
        assert 'readers' not in submissions[0].content['previous_URL']
        assert 'readers' not in submissions[0].content['explanation_of_revisions_PDF']
        assert 'readers' not in submissions[0].content['reassignment_request_area_chair']
        assert 'readers' not in submissions[0].content['reassignment_request_reviewers']
        assert 'readers' not in submissions[0].content['justification_for_not_keeping_action_editor_or_reviewers']
        
        ## release preprint submissions
        pc_client.post_note(
            openreview.Note(
                content={
                    'preprint_release_submission_date': (openreview.tools.datetime.datetime.now() + datetime.timedelta(seconds=5)).strftime('%Y/%m/%d %H:%M')
                },
                invitation=f'openreview.net/Support/-/Request{request_form.number}/ARR_Configuration',
                forum=request_form.id,
                readers=['aclweb.org/ACL/ARR/2023/August/Program_Chairs', 'openreview.net/Support'],
                referent=request_form.id,
                replyto=request_form.id,
                signatures=['~Program_ARRChair1'],
                writers=[],
            )
        )

        # Release them again
        helpers.await_queue()
        helpers.await_queue_edit(openreview_client, 'aclweb.org/ACL/ARR/2023/August/-/Preprint_Release_Submission-0-1', count=2)

        request_page(selenium, 'http://localhost:3030/group?id=aclweb.org/ACL/ARR/2023/August', None, wait_for_element='header')
        
        tabs = selenium.find_element(By.CLASS_NAME, 'nav-tabs').find_elements(By.TAG_NAME, 'li')
        assert len(tabs) == 2
        assert tabs[0].text == 'Anonymous Pre-prints'
        assert tabs[1].text == 'Recent Activity'

        notes = selenium.find_element(By.ID, 'anonymous-pre-prints').find_elements(By.CLASS_NAME, 'note')
        assert len(notes) == 50
        assert notes[0].find_element(By.TAG_NAME, 'h4').text == 'Paper title 100'

        submissions = pc_client_v2.get_notes(invitation='aclweb.org/ACL/ARR/2023/August/-/Submission', sort='number:asc')       

        assert submissions[0].readers == ['aclweb.org/ACL/ARR/2023/August', 
                                          'aclweb.org/ACL/ARR/2023/August/Submission1/Senior_Area_Chairs',
                                          'aclweb.org/ACL/ARR/2023/August/Submission1/Area_Chairs',
                                          'aclweb.org/ACL/ARR/2023/August/Submission1/Reviewers',
                                          'aclweb.org/ACL/ARR/2023/August/Submission1/Authors']
        assert submissions[0].content['TLDR']['readers'] == ['aclweb.org/ACL/ARR/2023/August', 'aclweb.org/ACL/ARR/2023/August/Submission1/Authors']
        assert submissions[0].content['preprint']['readers'] == ['aclweb.org/ACL/ARR/2023/August', 'aclweb.org/ACL/ARR/2023/August/Submission1/Authors']
        assert submissions[0].content['existing_preprints']['readers'] == ['aclweb.org/ACL/ARR/2023/August', 'aclweb.org/ACL/ARR/2023/August/Submission1/Authors']
        assert submissions[0].content['preferred_venue']['readers'] == ['aclweb.org/ACL/ARR/2023/August', 'aclweb.org/ACL/ARR/2023/August/Submission1/Authors']
        assert submissions[0].content['consent_to_share_data']['readers'] == ['aclweb.org/ACL/ARR/2023/August', 'aclweb.org/ACL/ARR/2023/August/Submission1/Authors']
        assert submissions[0].content['consent_to_share_submission_details']['readers'] == ['aclweb.org/ACL/ARR/2023/August', 'aclweb.org/ACL/ARR/2023/August/Submission1/Authors']
        assert submissions[0].content['Association_for_Computational_Linguistics_-_Blind_Submission_License_Agreement']['readers'] == ['aclweb.org/ACL/ARR/2023/August', 'aclweb.org/ACL/ARR/2023/August/Submission1/Authors']
        assert submissions[0].content['preprint_status']['readers'] == ['aclweb.org/ACL/ARR/2023/August', 'aclweb.org/ACL/ARR/2023/August/Submission1/Authors']
        assert 'readers' not in submissions[0].content['software']
        assert 'readers' not in submissions[0].content['previous_URL']
        assert 'readers' not in submissions[0].content['explanation_of_revisions_PDF']
        assert 'readers' not in submissions[0].content['reassignment_request_area_chair']
        assert 'readers' not in submissions[0].content['reassignment_request_reviewers']
        assert 'readers' not in submissions[0].content['justification_for_not_keeping_action_editor_or_reviewers']


        assert submissions[1].readers == ['everyone']
        assert submissions[1].content['TLDR']['readers'] == ['aclweb.org/ACL/ARR/2023/August', 'aclweb.org/ACL/ARR/2023/August/Submission2/Authors']
        assert submissions[1].content['preprint']['readers'] == ['aclweb.org/ACL/ARR/2023/August', 'aclweb.org/ACL/ARR/2023/August/Submission2/Authors']
        assert submissions[1].content['existing_preprints']['readers'] == ['aclweb.org/ACL/ARR/2023/August', 'aclweb.org/ACL/ARR/2023/August/Submission2/Authors']
        assert submissions[1].content['preferred_venue']['readers'] == ['aclweb.org/ACL/ARR/2023/August', 'aclweb.org/ACL/ARR/2023/August/Submission2/Authors']
        assert submissions[1].content['consent_to_share_data']['readers'] == ['aclweb.org/ACL/ARR/2023/August', 'aclweb.org/ACL/ARR/2023/August/Submission2/Authors']
        assert submissions[1].content['consent_to_share_submission_details']['readers'] == ['aclweb.org/ACL/ARR/2023/August', 'aclweb.org/ACL/ARR/2023/August/Submission2/Authors']
        assert submissions[1].content['Association_for_Computational_Linguistics_-_Blind_Submission_License_Agreement']['readers'] == ['aclweb.org/ACL/ARR/2023/August', 'aclweb.org/ACL/ARR/2023/August/Submission2/Authors']
        assert submissions[1].content['preprint_status']['readers'] == ['aclweb.org/ACL/ARR/2023/August', 'aclweb.org/ACL/ARR/2023/August/Submission2/Authors']

        assert set(submissions[1].content['software']['readers']) == {
            "aclweb.org/ACL/ARR/2023/August/Program_Chairs",
            "aclweb.org/ACL/ARR/2023/August/Submission2/Senior_Area_Chairs",
            "aclweb.org/ACL/ARR/2023/August/Submission2/Area_Chairs",
            "aclweb.org/ACL/ARR/2023/August/Submission2/Reviewers",
            "aclweb.org/ACL/ARR/2023/August/Submission2/Authors"
        }
        assert set(submissions[1].content['data']['readers']) == {
            "aclweb.org/ACL/ARR/2023/August/Program_Chairs",
            "aclweb.org/ACL/ARR/2023/August/Submission2/Senior_Area_Chairs",
            "aclweb.org/ACL/ARR/2023/August/Submission2/Area_Chairs",
            "aclweb.org/ACL/ARR/2023/August/Submission2/Reviewers",
            "aclweb.org/ACL/ARR/2023/August/Submission2/Authors"
        }
        assert set(submissions[1].content['previous_URL']['readers']) == {
            "aclweb.org/ACL/ARR/2023/August/Program_Chairs",
            "aclweb.org/ACL/ARR/2023/August/Submission2/Senior_Area_Chairs",
            "aclweb.org/ACL/ARR/2023/August/Submission2/Area_Chairs",
            "aclweb.org/ACL/ARR/2023/August/Submission2/Reviewers",
            "aclweb.org/ACL/ARR/2023/August/Submission2/Authors"
        }
        assert set(submissions[1].content['explanation_of_revisions_PDF']['readers']) == {
            "aclweb.org/ACL/ARR/2023/August/Program_Chairs",
            "aclweb.org/ACL/ARR/2023/August/Submission2/Senior_Area_Chairs",
            "aclweb.org/ACL/ARR/2023/August/Submission2/Area_Chairs",
            "aclweb.org/ACL/ARR/2023/August/Submission2/Reviewers/Submitted",
            "aclweb.org/ACL/ARR/2023/August/Submission2/Authors"
        }  
        assert set(submissions[1].content['reassignment_request_area_chair']['readers']) == {
            "aclweb.org/ACL/ARR/2023/August/Program_Chairs",
            "aclweb.org/ACL/ARR/2023/August/Submission2/Senior_Area_Chairs",
            "aclweb.org/ACL/ARR/2023/August/Submission2/Area_Chairs",
            "aclweb.org/ACL/ARR/2023/August/Submission2/Reviewers",
            "aclweb.org/ACL/ARR/2023/August/Submission2/Authors"
        }  
        assert set(submissions[1].content['reassignment_request_reviewers']['readers']) == {
            "aclweb.org/ACL/ARR/2023/August/Program_Chairs",
            "aclweb.org/ACL/ARR/2023/August/Submission2/Senior_Area_Chairs",
            "aclweb.org/ACL/ARR/2023/August/Submission2/Area_Chairs",
            "aclweb.org/ACL/ARR/2023/August/Submission2/Reviewers",
            "aclweb.org/ACL/ARR/2023/August/Submission2/Authors"
        }  
        assert set(submissions[1].content['justification_for_not_keeping_action_editor_or_reviewers']['readers']) == {
            "aclweb.org/ACL/ARR/2023/August/Program_Chairs",
            "aclweb.org/ACL/ARR/2023/August/Submission2/Senior_Area_Chairs",
            "aclweb.org/ACL/ARR/2023/August/Submission2/Area_Chairs",
            "aclweb.org/ACL/ARR/2023/August/Submission2/Reviewers",
            "aclweb.org/ACL/ARR/2023/August/Submission2/Authors"
        }

        responsible_checklist_fields = [field for field in hide_fields_from_public if len(field.split('_')[0]) <= 2] ## Any field that looks like A_, A1_, etc.
        for field in responsible_checklist_fields:
            assert set(submissions[1].content[field]['readers']) == {
                "aclweb.org/ACL/ARR/2023/August/Program_Chairs",
                "aclweb.org/ACL/ARR/2023/August/Submission2/Senior_Area_Chairs",
                "aclweb.org/ACL/ARR/2023/August/Submission2/Area_Chairs",
                "aclweb.org/ACL/ARR/2023/August/Submission2/Reviewers",
                "aclweb.org/ACL/ARR/2023/August/Submission2/Authors"
            }

        assert submissions[5].readers is not None
        assert submissions[5].readers == ['everyone']
        assert submissions[5].content['authors']['readers'] == [
            'aclweb.org/ACL/ARR/2023/August', 
            'aclweb.org/ACL/ARR/2023/August/Submission6/Authors'
        ]
        assert submissions[5].content['authorids']['readers'] == [
            'aclweb.org/ACL/ARR/2023/August', 
            'aclweb.org/ACL/ARR/2023/August/Submission6/Authors'
        ]

        # Post comment as PCs for the first submission
        comment_edit = pc_client_v2.post_note_edit(
            invitation=f"aclweb.org/ACL/ARR/2023/August/Submission{submissions[0].number}/-/Official_Comment",
            writers=['aclweb.org/ACL/ARR/2023/August'],
            signatures=['aclweb.org/ACL/ARR/2023/August/Program_Chairs'],
            note=openreview.api.Note(
                replyto=submissions[0].id,
                readers=[
                    'aclweb.org/ACL/ARR/2023/August/Program_Chairs',
                    f'aclweb.org/ACL/ARR/2023/August/Submission{submissions[0].number}/Senior_Area_Chairs',
                    f'aclweb.org/ACL/ARR/2023/August/Submission{submissions[0].number}/Area_Chairs'
                ],
                content={
                    "comment": { "value": "This is a comment"}
                }
            )
        )

        helpers.await_queue_edit(openreview_client, edit_id=comment_edit['id'])

        # Post comment as authors to chairs
        test_client = openreview.api.OpenReviewClient(token=test_client.token)
        comment_edit = test_client.post_note_edit(
            invitation=f"aclweb.org/ACL/ARR/2023/August/Submission{submissions[0].number}/-/Author-Editor_Confidential_Comment",
            writers=['aclweb.org/ACL/ARR/2023/August', f'aclweb.org/ACL/ARR/2023/August/Submission{submissions[0].number}/Authors'],
            signatures=[f'aclweb.org/ACL/ARR/2023/August/Submission{submissions[0].number}/Authors'],
            note=openreview.api.Note(
                replyto=submissions[0].id,
                readers=[
                    'aclweb.org/ACL/ARR/2023/August/Program_Chairs',
                    f'aclweb.org/ACL/ARR/2023/August/Submission{submissions[0].number}/Senior_Area_Chairs',
                    f'aclweb.org/ACL/ARR/2023/August/Submission{submissions[0].number}/Area_Chairs',
                    f'aclweb.org/ACL/ARR/2023/August/Submission{submissions[0].number}/Authors'
                ],
                content={
                    "comment": { "value": "This is a comment"}
                }
            )
        )

        helpers.await_queue_edit(openreview_client, edit_id=comment_edit['id'])

        assert openreview_client.get_messages(subject=f'[ARR - August 2023] An author-editor confidential comment has been received on your Paper Number: {submissions[0].number}, Paper Title: "Paper title {submissions[0].number}"')
    
        comment_edit = pc_client_v2.post_note_edit(
            invitation=f"aclweb.org/ACL/ARR/2023/August/Submission{submissions[0].number}/-/Author-Editor_Confidential_Comment",
            writers=['aclweb.org/ACL/ARR/2023/August', f'aclweb.org/ACL/ARR/2023/August/Program_Chairs'],
            signatures=[f'aclweb.org/ACL/ARR/2023/August/Program_Chairs'],
            note=openreview.api.Note(
                replyto=submissions[0].id,
                readers=[
                    'aclweb.org/ACL/ARR/2023/August/Program_Chairs',
                    f'aclweb.org/ACL/ARR/2023/August/Submission{submissions[0].number}/Senior_Area_Chairs',
                    f'aclweb.org/ACL/ARR/2023/August/Submission{submissions[0].number}/Area_Chairs',
                    f'aclweb.org/ACL/ARR/2023/August/Submission{submissions[0].number}/Authors'
                ],
                content={
                    "comment": { "value": "This is a comment from the PCs"}
                }
            )
        )

        helpers.await_queue_edit(openreview_client, edit_id=comment_edit['id'])

        assert "This is a comment from the PCs" in openreview_client.get_note(comment_edit['note']['id']).content['comment']['value']

    def test_metadata_edit(self, client, openreview_client, helpers, test_client, request_page, selenium):
        pc_client=openreview.Client(username='pc@aclrollingreview.org', password=helpers.strong_password)
        pc_client_v2=openreview.api.OpenReviewClient(username='pc@aclrollingreview.org', password=helpers.strong_password)
        request_form=pc_client.get_notes(invitation='openreview.net/Support/-/Request_Form')[1]
        august_venue = openreview.helpers.get_conference(client, request_form.id, 'openreview.net/Support')
        submissions = pc_client_v2.get_notes(invitation='aclweb.org/ACL/ARR/2023/August/-/Submission', sort='number:asc')
        test_client = openreview.api.OpenReviewClient(token=test_client.token)

        # Create metadata edit stage
        now = datetime.datetime.now()
        due_date = now + datetime.timedelta(days=3)
        pc_client.post_note(
            openreview.Note(
                content={
                    'metadata_edit_start_date': (now).strftime('%Y/%m/%d %H:%M'),
                    'metadata_edit_end_date': (due_date).strftime('%Y/%m/%d %H:%M')
                },
                invitation=f'openreview.net/Support/-/Request{request_form.number}/ARR_Configuration',
                forum=request_form.id,
                readers=['aclweb.org/ACL/ARR/2023/August/Program_Chairs', 'openreview.net/Support'],
                referent=request_form.id,
                replyto=request_form.id,
                signatures=['~Program_ARRChair1'],
                writers=[],
            )
        )

        helpers.await_queue()
        helpers.await_queue_edit(openreview_client, invitation='aclweb.org/ACL/ARR/2023/August/-/Submission_Metadata_Revision', count=1)

        paper_metadata_invitation = openreview_client.get_invitation('aclweb.org/ACL/ARR/2023/August/Submission1/-/Submission_Metadata_Revision')
        # Round to the nearest minute
        rounded = datetime.datetime.strptime(due_date.strftime('%Y/%m/%d %H:%M'), '%Y/%m/%d %H:%M')
        assert paper_metadata_invitation.duedate is None
        assert paper_metadata_invitation.expdate == openreview.tools.datetime_millis(rounded)

        fields_to_remove = [
            'paperhash',
            'number_of_action_editor_checklists',
            'number_of_reviewer_checklists',
            'venue',
            'venueid'
        ]
        current_content = deepcopy(submissions[0].content)
        for field in fields_to_remove:
            current_content.pop(field)

        # Cannot edit author lists
        current_content['authorids'] = {'value': ['~Not_AnAuthor1']}
        current_content['authors'] = {'value': ['Not An Author']}
        with pytest.raises(openreview.OpenReviewException, match=r'property authorids must NOT be present'):
            test_client.post_note_edit(
                invitation=f"aclweb.org/ACL/ARR/2023/August/Submission1/-/Submission_Metadata_Revision",
                signatures=['aclweb.org/ACL/ARR/2023/August/Submission1/Authors'],
                note=openreview.api.Note(
                    content=current_content
                )
            )
        with pytest.raises(openreview.OpenReviewException, match=r'property authors must NOT be present'):
            test_client.post_note_edit(
                invitation=f"aclweb.org/ACL/ARR/2023/August/Submission1/-/Submission_Metadata_Revision",
                signatures=['aclweb.org/ACL/ARR/2023/August/Submission1/Authors'],
                note=openreview.api.Note(
                    content=current_content
                )
            )
        with pytest.raises(openreview.OpenReviewException, match=r'property pdf must NOT be present'):
            test_client.post_note_edit(
                invitation=f"aclweb.org/ACL/ARR/2023/August/Submission1/-/Submission_Metadata_Revision",
                signatures=['aclweb.org/ACL/ARR/2023/August/Submission1/Authors'],
                note=openreview.api.Note(
                    content=current_content
                )
            )
        
        # Change some fields
        current_content = deepcopy(submissions[0].content)
        for field in fields_to_remove:
            current_content.pop(field)
        current_content.pop('pdf')
        current_content.pop('authorids')
        current_content.pop('authors')
        new_content = {
            'title': { 'value': 'metadata edit title' },
            'abstract': { 'value': 'metadata edit abstract' },
            'paper_type': { 'value': 'Long' },
            'research_area_keywords': { 'value': 'A keyword, another keyword' },
            'justification_for_not_keeping_action_editor_or_reviewers': { 'value': 'metadata edit justification' }
        }
        current_content.update(new_content)
        test_client.post_note_edit(
                invitation=f"aclweb.org/ACL/ARR/2023/August/Submission1/-/Submission_Metadata_Revision",
                signatures=['aclweb.org/ACL/ARR/2023/August/Submission1/Authors'],
                note=openreview.api.Note(
                    content=current_content
                )
            )
        
        # Change dates
        past_start = now - datetime.timedelta(days=2)
        past_end = now - datetime.timedelta(days=1)
        pc_client.post_note(
            openreview.Note(
                content={
                    'metadata_edit_start_date': (past_start).strftime('%Y/%m/%d %H:%M'),
                    'metadata_edit_end_date': (past_end).strftime('%Y/%m/%d %H:%M')
                },
                invitation=f'openreview.net/Support/-/Request{request_form.number}/ARR_Configuration',
                forum=request_form.id,
                readers=['aclweb.org/ACL/ARR/2023/August/Program_Chairs', 'openreview.net/Support'],
                referent=request_form.id,
                replyto=request_form.id,
                signatures=['~Program_ARRChair1'],
                writers=[],
            )
        )

        helpers.await_queue()
        helpers.await_queue_edit(openreview_client, invitation='aclweb.org/ACL/ARR/2023/August/-/Submission_Metadata_Revision', count=2)

        updated_metadata_invitation = openreview_client.get_invitation('aclweb.org/ACL/ARR/2023/August/Submission1/-/Submission_Metadata_Revision')
        assert updated_metadata_invitation.duedate is None

        # Test that the form is closed "The Invitation aclweb.org/ACL/ARR/2023/August/Submission1/-/Submission_Metadata_Revision has expired"
        with pytest.raises(openreview.OpenReviewException, match=r'The Invitation aclweb.org/ACL/ARR/2023/August/Submission1/-/Submission_Metadata_Revision has expired'):
            test_client.post_note_edit(
                invitation=f"aclweb.org/ACL/ARR/2023/August/Submission1/-/Submission_Metadata_Revision",
                signatures=['aclweb.org/ACL/ARR/2023/August/Submission1/Authors'],
                note=openreview.api.Note(
                    content=current_content
                )
            )

    def test_setup_matching(self, client, openreview_client, helpers, test_client, request_page, selenium):

        pc_client=openreview.Client(username='pc@aclrollingreview.org', password=helpers.strong_password)
        pc_client_v2=openreview.api.OpenReviewClient(username='pc@aclrollingreview.org', password=helpers.strong_password)
        request_form=pc_client.get_notes(invitation='openreview.net/Support/-/Request_Form')[1]
        august_venue = openreview.helpers.get_conference(client, request_form.id, 'openreview.net/Support')
        test_client = openreview.api.OpenReviewClient(token=test_client.token)

        # Create review stages
        now = datetime.datetime.now()
        due_date = now + datetime.timedelta(days=3)
        pc_client.post_note(
            openreview.Note(
                content={
                    'ae_checklist_start_date': (now).strftime('%Y/%m/%d %H:%M'),
                    'ae_checklist_due_date': (now).strftime('%Y/%m/%d %H:%M'),
                    'ae_checklist_exp_date': (due_date).strftime('%Y/%m/%d %H:%M'),
                    'reviewer_checklist_start_date': (now).strftime('%Y/%m/%d %H:%M'),
                    'reviewer_checklist_due_date': (now).strftime('%Y/%m/%d %H:%M'),
                    'reviewer_checklist_exp_date': (due_date).strftime('%Y/%m/%d %H:%M'),
                    'review_start_date': (now).strftime('%Y/%m/%d %H:%M'),
                    'review_deadline': (due_date).strftime('%Y/%m/%d %H:%M'),
                    'review_expiration_date': (due_date).strftime('%Y/%m/%d %H:%M'),
                    'meta_review_start_date': (now).strftime('%Y/%m/%d %H:%M'),
                    'meta_review_deadline': (due_date).strftime('%Y/%m/%d %H:%M'),
                    'meta_review_expiration_date': (due_date).strftime('%Y/%m/%d %H:%M'),
                    'ethics_review_start_date': (now).strftime('%Y/%m/%d %H:%M'),
                    'ethics_review_deadline': (due_date).strftime('%Y/%m/%d %H:%M'),
                    'ethics_review_expiration_date': (due_date).strftime('%Y/%m/%d %H:%M'),
                },
                invitation=f'openreview.net/Support/-/Request{request_form.number}/ARR_Configuration',
                forum=request_form.id,
                readers=['aclweb.org/ACL/ARR/2023/August/Program_Chairs', 'openreview.net/Support'],
                referent=request_form.id,
                replyto=request_form.id,
                signatures=['~Program_ARRChair1'],
                writers=[],
            )
        )

        helpers.await_queue()

        submissions = pc_client_v2.get_notes(invitation='aclweb.org/ACL/ARR/2023/August/-/Submission', sort='number:asc')

        checklist_start_dt = datetime.datetime.strptime(now.strftime('%Y/%m/%d %H:%M'), '%Y/%m/%d %H:%M')
        expected_checklist_cdate = openreview.tools.datetime_millis(checklist_start_dt)
        first_submission_number = submissions[0].number
        ae_checklist_invitation = openreview_client.get_invitation(f'aclweb.org/ACL/ARR/2023/August/Submission{first_submission_number}/-/Action_Editor_Checklist')
        reviewer_checklist_invitation = openreview_client.get_invitation(f'aclweb.org/ACL/ARR/2023/August/Submission{first_submission_number}/-/Reviewer_Checklist')
        assert ae_checklist_invitation.cdate == expected_checklist_cdate
        assert reviewer_checklist_invitation.cdate == expected_checklist_cdate

        with open(os.path.join(os.path.dirname(__file__), 'data/rev_scores_venue.csv'), 'w') as file_handle:
            writer = csv.writer(file_handle)
            for submission in submissions:
                for sac in openreview_client.get_group('aclweb.org/ACL/ARR/2023/August/Senior_Area_Chairs').members:
                    writer.writerow([submission.id, sac, round(random.random(), 2)])

        affinity_scores_url = client.put_attachment(os.path.join(os.path.dirname(__file__), 'data/rev_scores_venue.csv'), f'openreview.net/Support/-/Request{request_form.number}/Paper_Matching_Setup', 'upload_affinity_scores')

        client.post_note(openreview.Note(
            content={
                'title': 'Paper Matching Setup',
                'matching_group': 'aclweb.org/ACL/ARR/2023/August/Senior_Area_Chairs',
                'compute_conflicts': 'Default',
                'compute_affinity_scores': 'No',
                'upload_affinity_scores': affinity_scores_url
            },
            forum=request_form.id,
            replyto=request_form.id,
            invitation=f'openreview.net/Support/-/Request{request_form.number}/Paper_Matching_Setup',
            readers=['aclweb.org/ACL/ARR/2023/August/Program_Chairs', 'openreview.net/Support'],
            signatures=['~Program_ARRChair1'],
            writers=[]
        ))
        helpers.await_queue()

        assert openreview_client.get_invitation('aclweb.org/ACL/ARR/2023/August/Senior_Area_Chairs/-/Conflict')
        assert openreview_client.get_invitation('aclweb.org/ACL/ARR/2023/August/Senior_Area_Chairs/-/Affinity_Score')
        proposed_inv = openreview_client.get_invitation('aclweb.org/ACL/ARR/2023/August/Senior_Area_Chairs/-/Proposed_Assignment')
        assert proposed_inv
        assert proposed_inv.edit['head']['param']['type'] == 'note'
        assert proposed_inv.edit['head']['param']['withVenueid'] == 'aclweb.org/ACL/ARR/2023/August/Submission'

        affinity_score_count =  openreview_client.get_edges_count(invitation='aclweb.org/ACL/ARR/2023/August/Senior_Area_Chairs/-/Affinity_Score')
        assert affinity_score_count == 101 * 3 ## submissions * SACs

        assert openreview_client.get_edges_count(invitation='aclweb.org/ACL/ARR/2023/August/Senior_Area_Chairs/-/Conflict') == 105 # Share publication with co-author of test user + SAC2 shares institution with submission 1 and 101 via SAC1 (and SAC3)

        openreview.tools.replace_members_with_ids(openreview_client, openreview_client.get_group('aclweb.org/ACL/ARR/2023/August/Area_Chairs'))

        with open(os.path.join(os.path.dirname(__file__), 'data/rev_scores_venue.csv'), 'w') as file_handle:
            writer = csv.writer(file_handle)
            for submission in submissions:
                for ac in openreview_client.get_group('aclweb.org/ACL/ARR/2023/August/Area_Chairs').members:
                    writer.writerow([submission.id, ac, round(random.random(), 2)])

        affinity_scores_url = client.put_attachment(os.path.join(os.path.dirname(__file__), 'data/rev_scores_venue.csv'), f'openreview.net/Support/-/Request{request_form.number}/Paper_Matching_Setup', 'upload_affinity_scores')

        client.post_note(openreview.Note(
            content={
                'title': 'Paper Matching Setup',
                'matching_group': 'aclweb.org/ACL/ARR/2023/August/Area_Chairs',
                'compute_conflicts': 'NeurIPS',
                'compute_conflicts_N_years': '3',
                'compute_affinity_scores': 'No',
                'upload_affinity_scores': affinity_scores_url
            },
            forum=request_form.id,
            replyto=request_form.id,
            invitation=f'openreview.net/Support/-/Request{request_form.number}/Paper_Matching_Setup',
            readers=['aclweb.org/ACL/ARR/2023/August/Program_Chairs', 'openreview.net/Support'],
            signatures=['~Program_ARRChair1'],
            writers=[]
        ))
        helpers.await_queue()

        assert openreview_client.get_invitation('aclweb.org/ACL/ARR/2023/August/Area_Chairs/-/Conflict')
        assert openreview_client.get_invitation('aclweb.org/ACL/ARR/2023/August/Area_Chairs/-/Affinity_Score')

        affinity_score_count =  openreview_client.get_edges_count(invitation='aclweb.org/ACL/ARR/2023/August/Area_Chairs/-/Affinity_Score')
        assert affinity_score_count == 101 * 3 ## submissions * ACs

        assert openreview_client.get_edges_count(invitation='aclweb.org/ACL/ARR/2023/August/Area_Chairs/-/Conflict') == 6

        openreview.tools.replace_members_with_ids(openreview_client, openreview_client.get_group('aclweb.org/ACL/ARR/2023/August/Reviewers'))

        with open(os.path.join(os.path.dirname(__file__), 'data/rev_scores_venue.csv'), 'w') as file_handle:
            writer = csv.writer(file_handle)
            for submission in submissions:
                for ac in openreview_client.get_group('aclweb.org/ACL/ARR/2023/August/Reviewers').members:
                    writer.writerow([submission.id, ac, round(random.random(), 2)])

        affinity_scores_url = client.put_attachment(os.path.join(os.path.dirname(__file__), 'data/rev_scores_venue.csv'), f'openreview.net/Support/-/Request{request_form.number}/Paper_Matching_Setup', 'upload_affinity_scores')

        client.post_note(openreview.Note(
            content={
                'title': 'Paper Matching Setup',
                'matching_group': 'aclweb.org/ACL/ARR/2023/August/Reviewers',
                'compute_conflicts': 'NeurIPS',
                'compute_conflicts_N_years': '3',
                'compute_affinity_scores': 'No',
                'upload_affinity_scores': affinity_scores_url
            },
            forum=request_form.id,
            replyto=request_form.id,
            invitation=f'openreview.net/Support/-/Request{request_form.number}/Paper_Matching_Setup',
            readers=['aclweb.org/ACL/ARR/2023/August/Program_Chairs', 'openreview.net/Support'],
            signatures=['~Program_ARRChair1'],
            writers=[]
        ))
        helpers.await_queue()

        assert openreview_client.get_invitation('aclweb.org/ACL/ARR/2023/August/Reviewers/-/Conflict')

        assert openreview_client.get_edges_count(invitation='aclweb.org/ACL/ARR/2023/August/Reviewers/-/Conflict') == 14 # All 7 reviewers will conflict with submissions 1/101 because of domain of SAC
        ## Extra 101 conflicts from new reviewer which is an author of all submissions

        affinity_scores =  openreview_client.get_grouped_edges(invitation='aclweb.org/ACL/ARR/2023/August/Reviewers/-/Affinity_Score', groupby='id')
        assert affinity_scores
        assert len(affinity_scores) == 101 * 7 ## submissions * reviewers

        # Post assignment configuration notes
        openreview_client.post_note_edit(
            invitation='aclweb.org/ACL/ARR/2023/August/Reviewers/-/Assignment_Configuration',
            readers=[august_venue.id],
            writers=[august_venue.id],
            signatures=[august_venue.id],
            note=openreview.api.Note(
                content={
                    "title": { "value": 'reviewer-assignments'},
                    "user_demand": { "value": '3'},
                    "max_papers": { "value": '6'},
                    "min_papers": { "value": '0'},
                    "alternates": { "value": '10'},
                    "paper_invitation": { "value": 'aclweb.org/ACL/ARR/2023/August/-/Submission&content.venueid=aclweb.org/ACL/ARR/2023/August/Submission'},
                    "match_group": { "value": 'aclweb.org/ACL/ARR/2023/August/Reviewers'},
                    "aggregate_score_invitation": { "value": 'aclweb.org/ACL/ARR/2023/August/Reviewers/-/Aggregate_Score'},
                    "conflicts_invitation": { "value": 'aclweb.org/ACL/ARR/2023/August/Reviewers/-/Conflict'},
                    "solver": { "value": 'FairFlow'},
                    "status": { "value": 'Deployed'},
                }
            )
        )
        openreview_client.post_note_edit(
            invitation='aclweb.org/ACL/ARR/2023/August/Area_Chairs/-/Assignment_Configuration',
            readers=[august_venue.id],
            writers=[august_venue.id],
            signatures=[august_venue.id],
            note=openreview.api.Note(
                content={
                    "title": { "value": 'ae-assignments'},
                    "user_demand": { "value": '3'},
                    "max_papers": { "value": '6'},
                    "min_papers": { "value": '0'},
                    "alternates": { "value": '10'},
                    "paper_invitation": { "value": 'aclweb.org/ACL/ARR/2023/August/-/Submission&content.venueid=aclweb.org/ACL/ARR/2023/August/Submission'},
                    "match_group": { "value": 'aclweb.org/ACL/ARR/2023/August/Area_Chairs'},
                    "aggregate_score_invitation": { "value": 'aclweb.org/ACL/ARR/2023/August/Area_Chairs/-/Aggregate_Score'},
                    "conflicts_invitation": { "value": 'aclweb.org/ACL/ARR/2023/August/Area_Chairs/-/Conflict'},
                    "solver": { "value": 'FairFlow'},
                    "status": { "value": 'Deployed'},
                }
            )
        )

        # Copy affinity scores into aggregate scores
        reviewer_edges_to_post = []
        reviewers = openreview_client.get_group('aclweb.org/ACL/ARR/2023/August/Reviewers').members
        submissions_by_id = { submission.id: submission for submission in submissions }
        for reviewer in reviewers:
            for edge in openreview_client.get_all_edges(invitation='aclweb.org/ACL/ARR/2023/August/Reviewers/-/Affinity_Score', tail=reviewer):
                submission = submissions_by_id[edge.head]
                reviewer_edges_to_post.append(
                    openreview.api.Edge(
                        invitation='aclweb.org/ACL/ARR/2023/August/Reviewers/-/Aggregate_Score',
                        readers=[
                            "aclweb.org/ACL/ARR/2023/August",
                            f"aclweb.org/ACL/ARR/2023/August/Submission{submission.number}/Senior_Area_Chairs",
                            f"aclweb.org/ACL/ARR/2023/August/Submission{submission.number}/Area_Chairs",
                            edge.tail
                        ],
                        writers=[
                            "aclweb.org/ACL/ARR/2023/August",
                            f"aclweb.org/ACL/ARR/2023/August/Submission{submission.number}/Senior_Area_Chairs",
                            f"aclweb.org/ACL/ARR/2023/August/Submission{submission.number}/Area_Chairs",
                        ],
                        signatures=edge.signatures,
                        nonreaders=[
                            f"aclweb.org/ACL/ARR/2023/August/Submission{submission.number}/Authors",
                        ],
                        head=edge.head,
                        tail=edge.tail,
                        weight=edge.weight,
                        label='reviewer-assignments'
                    )
                )
        openreview.tools.post_bulk_edges(openreview_client, reviewer_edges_to_post)

        ac_edges_to_post = []
        acs = openreview_client.get_group('aclweb.org/ACL/ARR/2023/August/Area_Chairs').members
        for ac in acs:
            for edge in openreview_client.get_all_edges(invitation='aclweb.org/ACL/ARR/2023/August/Area_Chairs/-/Affinity_Score', tail=ac):
                submission = submissions_by_id[edge.head]
                ac_edges_to_post.append(
                    openreview.api.Edge(
                        invitation='aclweb.org/ACL/ARR/2023/August/Area_Chairs/-/Aggregate_Score',
                        readers=[
                            "aclweb.org/ACL/ARR/2023/August",
                            f"aclweb.org/ACL/ARR/2023/August/Submission{submission.number}/Senior_Area_Chairs",
                            edge.tail
                        ],
                        writers=[
                            "aclweb.org/ACL/ARR/2023/August",
                            f"aclweb.org/ACL/ARR/2023/August/Submission{submission.number}/Senior_Area_Chairs",
                        ],
                        signatures=edge.signatures,
                        nonreaders=[
                            f"aclweb.org/ACL/ARR/2023/August/Submission{submission.number}/Authors",
                        ],
                        head=edge.head,
                        tail=edge.tail,
                        weight=edge.weight,
                        label='ae-assignments'
                    )
                )
        openreview.tools.post_bulk_edges(openreview_client, ac_edges_to_post)

        assert openreview_client.get_edges_count(invitation='aclweb.org/ACL/ARR/2023/August/Area_Chairs/-/Aggregate_Score', label='ae-assignments') == 101 * 3
        assert openreview_client.get_edges_count(invitation='aclweb.org/ACL/ARR/2023/August/Reviewers/-/Aggregate_Score', label='reviewer-assignments') == 101 * 7


    def test_resubmission_and_track_matching_data(self, client, openreview_client, helpers, test_client, request_page, selenium):
        # Create groups for previous cycle
        pc_client=openreview.Client(username='pc@aclrollingreview.org', password=helpers.strong_password)
        pc_client_v2=openreview.api.OpenReviewClient(username='pc@aclrollingreview.org', password=helpers.strong_password)
        june_request_form=pc_client.get_notes(invitation='openreview.net/Support/-/Request_Form')[0]
        june_venue = openreview.helpers.get_conference(client, june_request_form.id, 'openreview.net/Support')
        request_form=pc_client.get_notes(invitation='openreview.net/Support/-/Request_Form')[1]
        august_venue = openreview.helpers.get_conference(client, request_form.id, 'openreview.net/Support')
        june_submissions = pc_client_v2.get_notes(invitation='aclweb.org/ACL/ARR/2023/June/-/Submission', sort='number:asc')
        submissions = pc_client_v2.get_notes(invitation='aclweb.org/ACL/ARR/2023/August/-/Submission', sort='number:asc')

        ## Create June review stages
        now = datetime.datetime.now()
        start_date = now - datetime.timedelta(days=2)
        due_date = now + datetime.timedelta(days=3)
        pc_client.post_note(
            openreview.Note(
                content={
                    'review_start_date': (now).strftime('%Y/%m/%d %H:%M'),
                    'review_deadline': (due_date).strftime('%Y/%m/%d %H:%M'),
                    'review_expiration_date': (due_date).strftime('%Y/%m/%d %H:%M'),
                    'meta_review_start_date': (now).strftime('%Y/%m/%d %H:%M'),
                    'meta_review_deadline': (due_date).strftime('%Y/%m/%d %H:%M'),
                    'meta_review_expiration_date': (due_date).strftime('%Y/%m/%d %H:%M'),
                    'ethics_review_start_date': (now).strftime('%Y/%m/%d %H:%M'),
                    'ethics_review_deadline': (due_date).strftime('%Y/%m/%d %H:%M'),
                    'ethics_review_expiration_date': (due_date).strftime('%Y/%m/%d %H:%M'),
                },
                invitation=f"openreview.net/Support/-/Request{june_request_form.number}/ARR_Configuration",
                forum=june_request_form.id,
                readers=['aclweb.org/ACL/ARR/2023/June/Program_Chairs', 'openreview.net/Support'],
                referent=june_request_form.id,
                replyto=june_request_form.id,
                signatures=['~Program_ARRChair1'],
                writers=[],
            )
        )

        helpers.await_queue()

        # Getting resubmissions should pass
        previous_url_field = 'previous_URL'
        resubmissions = openreview.arr.helpers.get_resubmissions(submissions, previous_url_field)
        assert 6 not in [submission.number for submission in resubmissions]

        # Remove resubmission information from all but submissions 2, 3, and 1
        for submission in submissions:
            if submission.number in [1, 2, 3]:
                continue
            openreview_client.post_note_edit(
                invitation=august_venue.get_meta_invitation_id(),
                readers=[august_venue.id],
                writers=[august_venue.id],
                signatures=[august_venue.id],
                note=openreview.api.Note(
                    id=submission.id,
                    content={
                        'previous_URL': { 'delete': True },
                        'reassignment_request_area_chair': { 'delete': True },
                        'reassignment_request_reviewers': { 'delete': True },
                        'justification_for_not_keeping_action_editor_or_reviewers': { 'delete': True },
                    }
                )
            )


        # Set up June reviewer and area chair groups (for simplicity, map idx 1-to-1 and 2-to-2)
        openreview_client.add_members_to_group(june_venue.get_reviewers_id(number=2), '~Reviewer_ARROne1')
        openreview_client.add_members_to_group(june_venue.get_reviewers_id(number=3), '~Reviewer_ARRTwo1')
        openreview_client.add_members_to_group(june_venue.get_reviewers_id(number=2), '~Reviewer_ARRFive1')
        openreview_client.add_members_to_group(june_venue.get_area_chairs_id(number=2), '~AC_ARROne1')
        openreview_client.add_members_to_group(june_venue.get_area_chairs_id(number=3), '~AC_ARRTwo1')
        openreview_client.add_members_to_group(june_venue.get_area_chairs_id(number=2), '~AC_ARRThree1')

        reviewer_client_1 = openreview.api.OpenReviewClient(username='reviewer1@aclrollingreview.com', password=helpers.strong_password)
        reviewer_client_2 = openreview.api.OpenReviewClient(username='reviewer2@aclrollingreview.com', password=helpers.strong_password)
        reviewer_client_5 = openreview.api.OpenReviewClient(username='reviewer5@aclrollingreview.com', password=helpers.strong_password)
        ac_client_3 = openreview.api.OpenReviewClient(username='ac3@aclrollingreview.com', password=helpers.strong_password)

        anon_groups = reviewer_client_1.get_groups(prefix='aclweb.org/ACL/ARR/2023/June/Submission2/Reviewer_', signatory='~Reviewer_ARROne1')
        anon_group_id_1 = anon_groups[0].id
        anon_groups = reviewer_client_2.get_groups(prefix='aclweb.org/ACL/ARR/2023/June/Submission3/Reviewer_', signatory='~Reviewer_ARRTwo1')
        anon_group_id_2 = anon_groups[0].id
        anon_groups = reviewer_client_5.get_groups(prefix='aclweb.org/ACL/ARR/2023/June/Submission2/Reviewer_', signatory='~Reviewer_ARRFive1')
        anon_group_id_5 = anon_groups[0].id
        anon_groups = ac_client_3.get_groups(prefix='aclweb.org/ACL/ARR/2023/June/Submission2/Area_Chair_', signatory='~AC_ARRThree1')
        anon_group_id_ac = anon_groups[0].id

        review_edit = reviewer_client_1.post_note_edit(
            invitation='aclweb.org/ACL/ARR/2023/June/Submission2/-/Official_Review',
            signatures=[anon_group_id_1],
            note=openreview.api.Note(
                content={
                    "confidence": { "value": 5 },
                    "paper_summary": { "value": 'some summary' },
                    "summary_of_strengths": { "value": 'some strengths' },
                    "summary_of_weaknesses": { "value": 'some weaknesses' },
                    "comments_suggestions_and_typos": { "value": 'some comments' },
                    "soundness": { "value": 1 },
                    "excitement": { "value": 1.5 },
                    "overall_assessment": { "value": 1 },
                    "ethical_concerns": { "value": "N/A" },
                    "reproducibility": { "value": 1 },
                    "datasets": { "value": 1 },
                    "software": { "value": 1 },
                    "Knowledge_of_or_educated_guess_at_author_identity": {"value": "No"},
                    "Knowledge_of_paper": {"value": "After the review process started"},
                    "Knowledge_of_paper_source": {"value": ["A research talk"]},
                    "impact_of_knowledge_of_paper": {"value": "A lot"},
                    "reviewer_certification": {"value": "Yes"},
                    "secondary_reviewer": {"value": ["~Reviewer_ARRTwo1"]},
                    "publication_ethics_policy_compliance": {"value": "I did not use any generative AI tools for this review"}
                }
            )
        )
        reviewer_client_1.post_note_edit(
            invitation='aclweb.org/ACL/ARR/2023/June/Submission2/-/Official_Review',
            signatures=[anon_group_id_1],
            note=openreview.api.Note(
                id = review_edit['note']['id'],
                content={
                    "confidence": { "value": 5 },
                    "paper_summary": { "value": 'some summaryyyyyyyyy version 2' },
                    "summary_of_strengths": { "value": 'some strengths' },
                    "summary_of_weaknesses": { "value": 'some weaknesses' },
                    "comments_suggestions_and_typos": { "value": 'some comments' },
                    "soundness": { "value": 1 },
                    "excitement": { "value": 1.5 },
                    "overall_assessment": { "value": 1 },
                    "ethical_concerns": { "value": "N/A" },
                    "reproducibility": { "value": 1 },
                    "datasets": { "value": 1 },
                    "software": { "value": 1 },
                    "Knowledge_of_or_educated_guess_at_author_identity": {"value": "No"},
                    "Knowledge_of_paper": {"value": "After the review process started"},
                    "Knowledge_of_paper_source": {"value": ["A research talk"]},
                    "impact_of_knowledge_of_paper": {"value": "A lot"},
                    "reviewer_certification": {"value": "Yes"},
                    "secondary_reviewer": {"value": ["~Reviewer_ARRTwo1"]},
                    "publication_ethics_policy_compliance": {"value": "I did not use any generative AI tools for this review"}
                }
            )
        )        
        helpers.await_queue_edit(openreview_client, invitation='aclweb.org/ACL/ARR/2023/June/Submission2/-/Official_Review', count=2)

        assert anon_group_id_1 in openreview_client.get_group('aclweb.org/ACL/ARR/2023/June/Submission2/Reviewers/Submitted').members

        messages = openreview_client.get_messages(to='reviewer1@aclrollingreview.com', subject='[ARR - June 2023] Your official review has been received on your assigned Paper number: 2, Paper title: "Paper title "')
        assert len(messages) == 1
        

        review_edit = reviewer_client_2.post_note_edit(
            invitation='aclweb.org/ACL/ARR/2023/June/Submission3/-/Official_Review',
            signatures=[anon_group_id_2],
            note=openreview.api.Note(
                content={
                    "confidence": { "value": 5 },
                    "paper_summary": { "value": 'some summary' },
                    "summary_of_strengths": { "value": 'some strengths' },
                    "summary_of_weaknesses": { "value": 'some weaknesses' },
                    "comments_suggestions_and_typos": { "value": 'some comments' },
                    "soundness": { "value": 1 },
                    "excitement": { "value": 1.5 },
                    "overall_assessment": { "value": 1 },
                    "ethical_concerns": { "value": "N/A" },
                    "reproducibility": { "value": 1 },
                    "datasets": { "value": 1 },
                    "software": { "value": 1 },
                    "Knowledge_of_or_educated_guess_at_author_identity": {"value": "No"},
                    "Knowledge_of_paper": {"value": "After the review process started"},
                    "Knowledge_of_paper_source": {"value": ["A research talk"]},
                    "impact_of_knowledge_of_paper": {"value": "A lot"},
                    "reviewer_certification": {"value": "Yes"},
                    "secondary_reviewer": {"value": ["~Reviewer_ARRTwo1"]},
                    "publication_ethics_policy_compliance": {"value": "I did not use any generative AI tools for this review"}
                }
            )
        )
        helpers.await_queue_edit(openreview_client, edit_id=review_edit['id'])

        assert anon_group_id_2 in openreview_client.get_group('aclweb.org/ACL/ARR/2023/June/Submission3/Reviewers/Submitted').members

        review_edit = reviewer_client_5.post_note_edit(
            invitation='aclweb.org/ACL/ARR/2023/June/Submission2/-/Official_Review',
            signatures=[anon_group_id_5],
            note=openreview.api.Note(
                content={
                    "confidence": { "value": 5 },
                    "paper_summary": { "value": 'some summary' },
                    "summary_of_strengths": { "value": 'some strengths' },
                    "summary_of_weaknesses": { "value": 'some weaknesses' },
                    "comments_suggestions_and_typos": { "value": 'some comments' },
                    "soundness": { "value": 1 },
                    "excitement": { "value": 1.5 },
                    "overall_assessment": { "value": 1 },
                    "ethical_concerns": { "value": "N/A" },
                    "reproducibility": { "value": 1 },
                    "datasets": { "value": 1 },
                    "software": { "value": 1 },
                    "Knowledge_of_or_educated_guess_at_author_identity": {"value": "No"},
                    "Knowledge_of_paper": {"value": "After the review process started"},
                    "Knowledge_of_paper_source": {"value": ["A research talk"]},
                    "impact_of_knowledge_of_paper": {"value": "A lot"},
                    "reviewer_certification": {"value": "Yes"},
                    "secondary_reviewer": {"value": ["~Reviewer_ARRTwo1"]},
                    "publication_ethics_policy_compliance": {"value": "I did not use any generative AI tools for this review"}
                }
            )
        )
        helpers.await_queue_edit(openreview_client, edit_id=review_edit['id'])

        ac_edit = ac_client_3.post_note_edit(
            invitation='aclweb.org/ACL/ARR/2023/June/Submission2/-/Meta_Review',
            signatures=[anon_group_id_ac],
            note=openreview.api.Note(
                content={
                    "metareview": { "value": 'a metareview' },
                    "summary_of_reasons_to_publish": { "value": 'some summary' },
                    "summary_of_suggested_revisions": { "value": 'some strengths' },
                    "overall_assessment": { "value": 1 },
                    "ethical_concerns": { "value": "There are no concerns with this submission" },
                    "author_identity_guess": { "value": 1 },
                    "needs_ethics_review": {'value': 'No'},
                    "reported_issues": {'value': ['No']},
                    "note_to_authors": {'value': 'No'},
                    "great_reviews": {'value': 'ABCD'},
                    "poor_reviews": {'value': 'EFGH'},
                    "best_paper_ae_justification": {'value': 'Great and poor reviews'},
                    "publication_ethics_policy_compliance": {"value": "I did not use any generative AI tools for this review"},
                }
            )
        )

        helpers.await_queue_edit(openreview_client, edit_id=ac_edit['id'])

        june_submissions = pc_client_v2.get_notes(invitation='aclweb.org/ACL/ARR/2023/June/-/Submission', sort='number:asc', details='replies')
        meta_review = [reply for reply in june_submissions[1].details['replies'] if reply['invitations'][0].endswith('/-/Meta_Review')][0]

        assert meta_review['content']['reported_issues']['readers'] == ['aclweb.org/ACL/ARR/2023/June/Program_Chairs', 'aclweb.org/ACL/ARR/2023/June/Submission2/Senior_Area_Chairs', 'aclweb.org/ACL/ARR/2023/June/Submission2/Area_Chairs', 'aclweb.org/ACL/ARR/2023/June/Submission2/Authors']
        assert meta_review['content']['note_to_authors']['readers'] == ['aclweb.org/ACL/ARR/2023/June/Program_Chairs', 'aclweb.org/ACL/ARR/2023/June/Submission2/Senior_Area_Chairs', 'aclweb.org/ACL/ARR/2023/June/Submission2/Area_Chairs', 'aclweb.org/ACL/ARR/2023/June/Submission2/Authors']
        assert meta_review['content']['best_paper_ae_justification']['readers'] == ['aclweb.org/ACL/ARR/2023/June/Program_Chairs', 'aclweb.org/ACL/ARR/2023/June/Submission2/Senior_Area_Chairs', 'aclweb.org/ACL/ARR/2023/June/Submission2/Area_Chairs']
        assert meta_review['content']['ethical_concerns']['readers'] == ['aclweb.org/ACL/ARR/2023/June/Program_Chairs', 'aclweb.org/ACL/ARR/2023/June/Submission2/Senior_Area_Chairs', 'aclweb.org/ACL/ARR/2023/June/Submission2/Area_Chairs']
        assert meta_review['content']['needs_ethics_review']['readers'] == ['aclweb.org/ACL/ARR/2023/June/Program_Chairs', 'aclweb.org/ACL/ARR/2023/June/Submission2/Senior_Area_Chairs', 'aclweb.org/ACL/ARR/2023/June/Submission2/Area_Chairs']
        assert meta_review['content']['author_identity_guess']['readers'] == ['aclweb.org/ACL/ARR/2023/June/Program_Chairs', 'aclweb.org/ACL/ARR/2023/June/Submission2/Senior_Area_Chairs', 'aclweb.org/ACL/ARR/2023/June/Submission2/Area_Chairs']
        assert meta_review['content']['great_reviews']['readers'] == ['aclweb.org/ACL/ARR/2023/June/Program_Chairs', 'aclweb.org/ACL/ARR/2023/June/Submission2/Senior_Area_Chairs', 'aclweb.org/ACL/ARR/2023/June/Submission2/Area_Chairs']
        assert meta_review['content']['poor_reviews']['readers'] == ['aclweb.org/ACL/ARR/2023/June/Program_Chairs', 'aclweb.org/ACL/ARR/2023/June/Submission2/Senior_Area_Chairs', 'aclweb.org/ACL/ARR/2023/June/Submission2/Area_Chairs']
        assert meta_review['content']['explanation']['readers'] == ['aclweb.org/ACL/ARR/2023/June/Program_Chairs', 'aclweb.org/ACL/ARR/2023/June/Submission2/Senior_Area_Chairs', 'aclweb.org/ACL/ARR/2023/June/Submission2/Area_Chairs']

        # Point August submissions idx 1 and 2 to June papers and set submission reassignment requests
        # Let 1 = same and 2 = not same and 0 = same but no reviews
        sub_edit_1 = openreview_client.post_note_edit(
            invitation=august_venue.get_meta_invitation_id(),
            readers=[august_venue.id],
            writers=[august_venue.id],
            signatures=[august_venue.id],
            note=openreview.api.Note(
                id=submissions[1].id,
                content={
                    'previous_URL': {'value': f'https://openreview.net/forum?id={june_submissions[1].id}'},
                    'reassignment_request_area_chair': {'value': 'No, I want the same area chair from our previous submission (subject to their availability).' },
                    'reassignment_request_reviewers': { 'value': 'No, I want the same set of reviewers from our previous submission and understand that new reviewers may be assigned if any of the previous ones are unavailable' },
                }
            )
        )
        sub_edit_2 = openreview_client.post_note_edit(
            invitation=august_venue.get_meta_invitation_id(),
            readers=[august_venue.id],
            writers=[august_venue.id],
            signatures=[august_venue.id],
            note=openreview.api.Note(
                id=submissions[2].id,
                content={
                    'previous_URL': {'value': f'https://openreview.net/forum?id={june_submissions[2].id}'},
                    'reassignment_request_area_chair': {'value': 'Yes, I want a different area chair for our submission' },
                    'reassignment_request_reviewers': { 'value': 'Yes, I want a different set of reviewers' },
                }
            )
        )
        sub_edit_0 = openreview_client.post_note_edit(
            invitation=august_venue.get_meta_invitation_id(),
            readers=[august_venue.id],
            writers=[august_venue.id],
            signatures=[august_venue.id],
            note=openreview.api.Note(
                id=submissions[0].id,
                content={
                    'previous_URL': {'value': f'https://openreview.net/forum?id={june_submissions[0].id}'},
                    'reassignment_request_area_chair': {'value': 'Yes, I want a different area chair for our submission' },
                    'reassignment_request_reviewers': { 'value': 'Yes, I want a different set of reviewers' },
                }
            )
        )

        # Zero out affinity score for reviewer
        openreview_client.delete_edges(
            invitation='aclweb.org/ACL/ARR/2023/August/Reviewers/-/Affinity_Score',
            head=submissions[1].id,
            tail='~Reviewer_ARROne1'
        )

        # Call the stage
        matching_invitations = ['Setup_SAE_Matching', 'Setup_AE_Matching', 'Setup_Reviewer_Matching']
        for matching_invitation in matching_invitations:
            openreview_client.post_invitation_edit(
                invitations='aclweb.org/ACL/ARR/2023/August/-/Edit',
                readers=['aclweb.org/ACL/ARR/2023/August'],
                writers=['aclweb.org/ACL/ARR/2023/August'],
                signatures=['aclweb.org/ACL/ARR/2023/August'],
                invitation=openreview.api.Invitation(
                    id = f"aclweb.org/ACL/ARR/2023/August/-/{matching_invitation}",
                    content = {
                        'count': {'value': 1}
                    }
                )
            )

            helpers.await_queue_edit(openreview_client, f'aclweb.org/ACL/ARR/2023/August/-/{matching_invitation}-0-1', count=2)

        cmp_edges_5 = openreview_client.get_all_edges(invitation='aclweb.org/ACL/ARR/2023/August/Reviewers/-/Custom_Max_Papers', tail='~Reviewer_ARRFive1')
        assert len(cmp_edges_5) == 1
        assert cmp_edges_5[0].weight == 1
        time.sleep(5)  ## Give Mongo time to process edges

        # Call the stage a second time
        matching_invitations = ['Setup_SAE_Matching', 'Setup_AE_Matching', 'Setup_Reviewer_Matching']
        for matching_invitation in matching_invitations:
            openreview_client.post_invitation_edit(
                invitations='aclweb.org/ACL/ARR/2023/August/-/Edit',
                readers=['aclweb.org/ACL/ARR/2023/August'],
                writers=['aclweb.org/ACL/ARR/2023/August'],
                signatures=['aclweb.org/ACL/ARR/2023/August'],
                invitation=openreview.api.Invitation(
                    id = f"aclweb.org/ACL/ARR/2023/August/-/{matching_invitation}",
                    content = {
                        'count': {'value': 2}
                    }
                )
            )

            helpers.await_queue_edit(openreview_client, f'aclweb.org/ACL/ARR/2023/August/-/{matching_invitation}-0-1', count=3)

        cmp_edges_5 = openreview_client.get_all_edges(invitation='aclweb.org/ACL/ARR/2023/August/Reviewers/-/Custom_Max_Papers', tail='~Reviewer_ARRFive1')
        assert len(cmp_edges_5) == 1
        assert cmp_edges_5[0].weight == 1
        time.sleep(5)  ## Give Mongo time to process edges

        # Check reviewers groups
        assert 'aclweb.org/ACL/ARR/2023/August/Submission2/Reviewers' in openreview_client.get_group('aclweb.org/ACL/ARR/2023/June/Submission2/Reviewers').members
        assert 'aclweb.org/ACL/ARR/2023/August/Submission2/Reviewers' in openreview_client.get_group('aclweb.org/ACL/ARR/2023/June/Submission2/Reviewers/Submitted').members
        assert 'aclweb.org/ACL/ARR/2023/August/Submission3/Reviewers/Submitted' in openreview_client.get_group('aclweb.org/ACL/ARR/2023/June/Submission3/Reviewers').members
        assert 'aclweb.org/ACL/ARR/2023/August/Submission3/Reviewers/Submitted' in openreview_client.get_group('aclweb.org/ACL/ARR/2023/June/Submission3/Reviewers/Submitted').members
        
        # For 1, assert that the affinity scores on June reviewers/aes is 3
        ac_scores = {
            g['id']['tail'] : g['values'][0]
            for g in pc_client_v2.get_grouped_edges(invitation='aclweb.org/ACL/ARR/2023/August/Area_Chairs/-/Affinity_Score', head=submissions[1].id, select='tail,id,weight', groupby='tail')
        }
        rev_scores = {
            g['id']['tail'] : g['values'][0]
            for g in pc_client_v2.get_grouped_edges(invitation='aclweb.org/ACL/ARR/2023/August/Reviewers/-/Affinity_Score', head=submissions[1].id, select='tail,id,weight', groupby='tail')
        }
        assert ac_scores['~AC_ARROne1']['weight'] == 3
        assert rev_scores['~Reviewer_ARROne1']['weight'] == 3
        assert 'aclweb.org/ACL/ARR/2023/August/Submission2/Area_Chairs' in pc_client_v2.get_group('aclweb.org/ACL/ARR/2023/June/Submission2/Area_Chairs').members
        assert 'aclweb.org/ACL/ARR/2023/August/Submission2/Reviewers' in pc_client_v2.get_group('aclweb.org/ACL/ARR/2023/June/Submission2/Reviewers/Submitted').members

        # For 2, assert that the affinity scores on June reviewers/aes is 0
        ac_scores = {
            g['id']['tail'] : g['values'][0]
            for g in pc_client_v2.get_grouped_edges(invitation='aclweb.org/ACL/ARR/2023/August/Area_Chairs/-/Affinity_Score', head=submissions[2].id, select='tail,id,weight', groupby='tail')
        }
        rev_scores = {
            g['id']['tail'] : g['values'][0]
            for g in pc_client_v2.get_grouped_edges(invitation='aclweb.org/ACL/ARR/2023/August/Reviewers/-/Affinity_Score', head=submissions[2].id, select='tail,id,weight', groupby='tail')
        }
        assert ac_scores['~AC_ARRTwo1']['weight'] == 0
        assert rev_scores['~Reviewer_ARRTwo1']['weight'] == 0
        assert 'aclweb.org/ACL/ARR/2023/August/Submission3/Area_Chairs' in pc_client_v2.get_group('aclweb.org/ACL/ARR/2023/June/Submission3/Area_Chairs').members
        assert 'aclweb.org/ACL/ARR/2023/August/Submission3/Reviewers/Submitted' in pc_client_v2.get_group('aclweb.org/ACL/ARR/2023/June/Submission3/Reviewers/Submitted').members

        # Check for existence of track information
        track_edges = {
            g['id']['tail'] : g['values']
            for g in pc_client_v2.get_grouped_edges(invitation=f'aclweb.org/ACL/ARR/2023/August/Reviewers/-/Research_Area', select='head,id,weight', groupby='tail')
        }
        assert len(track_edges.keys()) == 2
        assert '~Reviewer_ARROne1' in track_edges
        assert len(track_edges['~Reviewer_ARROne1']) == 68
        assert '~Reviewer_ARRTwo1' in track_edges
        r2_edges = track_edges['~Reviewer_ARRTwo1']
        assert len(r2_edges) == 100
        assert not any(edge['head'] == submissions[2].id for edge in r2_edges), f"{submissions[2].id} in {[e['head'] for e in r2_edges]}" # No track information for submission 2

        track_edges = {
            g['id']['tail'] : g['values']
            for g in pc_client_v2.get_grouped_edges(invitation=f'aclweb.org/ACL/ARR/2023/August/Area_Chairs/-/Research_Area', select='head,id,weight', groupby='tail')
        }
        assert len(track_edges.keys()) == 1
        assert '~AC_ARROne1' in track_edges
        assert len(track_edges['~AC_ARROne1']) == 68

        track_edges = {
            g['id']['tail'] : g['values']
            for g in pc_client_v2.get_grouped_edges(invitation=f'aclweb.org/ACL/ARR/2023/August/Senior_Area_Chairs/-/Research_Area', select='head,id,weight', groupby='tail')
        }
        assert len(track_edges.keys()) == 1
        # SAC with no response and SAC with available response should have edges
        assert '~SAC_ARROne1' not in track_edges
        assert '~SAC_ARRTwo1' in track_edges
        assert '~SAC_ARRThree1' not in track_edges
        assert len(track_edges['~SAC_ARRTwo1']) == 68

        # Check for status and available edges
        status_edges = {
            g['id']['tail'] : g['values'][0]
            for g in pc_client_v2.get_grouped_edges(invitation=f'aclweb.org/ACL/ARR/2023/August/Reviewers/-/Status', select='head,id,weight,label', groupby='tail')
        }
        assert set(status_edges.keys()) == {'~Reviewer_ARROne1', '~Reviewer_ARRTwo1', '~Reviewer_ARRFive1'}
        assert status_edges['~Reviewer_ARROne1']['label'] == 'Requested'
        assert status_edges['~Reviewer_ARRTwo1']['label'] == 'Reassigned'
        assert status_edges['~Reviewer_ARRFive1']['label'] == 'Requested'

        status_edges = {
            g['id']['tail'] : g['values'][0]
            for g in pc_client_v2.get_grouped_edges(invitation=f'aclweb.org/ACL/ARR/2023/August/Area_Chairs/-/Status', select='head,id,weight,label', groupby='tail')
        }
        assert set(status_edges.keys()) == {'~AC_ARROne1', '~AC_ARRTwo1', '~AC_ARRThree1'}
        assert status_edges['~AC_ARROne1']['label'] == 'Requested'
        assert status_edges['~AC_ARRTwo1']['label'] == 'Reassigned'
        assert status_edges['~AC_ARRThree1']['label'] == 'Requested'

        available_edges = {
            g['id']['tail'] : g['values'][0]
            for g in pc_client_v2.get_grouped_edges(invitation=f'aclweb.org/ACL/ARR/2023/August/Reviewers/-/Reviewing_Resubmissions', select='head,id,weight,label', groupby='tail')
        }
        assert set(available_edges.keys()) == {'~Reviewer_ARRTwo1', '~Reviewer_ARRFive1'}
        assert available_edges['~Reviewer_ARRTwo1']['label'] == 'No'
        assert available_edges['~Reviewer_ARRFive1']['label'] == 'Only Reviewing Resubmissions'

        available_edges = {
            g['id']['tail'] : g['values'][0]
            for g in pc_client_v2.get_grouped_edges(invitation=f'aclweb.org/ACL/ARR/2023/August/Area_Chairs/-/Reviewing_Resubmissions', select='head,id,weight,label', groupby='tail')
        }
        assert set(available_edges.keys()) == {'~AC_ARROne1','~AC_ARRThree1', '~AC_ARRTwo1'}
        assert available_edges['~AC_ARRThree1']['label'] == 'Only Reviewing Resubmissions'
        assert available_edges['~AC_ARRTwo1']['label'] == 'Yes'
        assert available_edges['~AC_ARROne1']['label'] == 'No'

        # Check integrity of custom max papers
        cmp_edges = {
            g['id']['tail'] : g['values'][0]
            for g in pc_client_v2.get_grouped_edges(invitation=f'aclweb.org/ACL/ARR/2023/August/Reviewers/-/Custom_Max_Papers', select='head,id,weight,label', groupby='tail')
        }
        load_notes = pc_client_v2.get_all_notes(invitation='aclweb.org/ACL/ARR/2023/August/Reviewers/-/Max_Load_And_Unavailability_Request')
        for note in load_notes:
            if note.signatures[0] == '~Reviewer_ARRFive1':
                assert cmp_edges[note.signatures[0]]['weight'] == note.content['maximum_load_this_cycle']['value'] + 1
                continue
            assert cmp_edges[note.signatures[0]]['weight'] == note.content['maximum_load_this_cycle']['value']

        cmp_edges = {
            g['id']['tail'] : g['values'][0]
            for g in pc_client_v2.get_grouped_edges(invitation=f'aclweb.org/ACL/ARR/2023/August/Area_Chairs/-/Custom_Max_Papers', select='head,id,weight,label', groupby='tail')
        }
        load_notes = pc_client_v2.get_all_notes(invitation='aclweb.org/ACL/ARR/2023/August/Area_Chairs/-/Max_Load_And_Unavailability_Request')
        for note in load_notes:
            if note.signatures[0] == '~AC_ARRThree1':
                assert cmp_edges[note.signatures[0]]['weight'] == note.content['maximum_load_this_cycle']['value'] + 1
                continue
            assert cmp_edges[note.signatures[0]]['weight'] == note.content['maximum_load_this_cycle']['value']

        cmp_edges = {
            g['id']['tail'] : g['values'][0]
            for g in pc_client_v2.get_grouped_edges(invitation=f'aclweb.org/ACL/ARR/2023/August/Senior_Area_Chairs/-/Custom_Max_Papers', select='head,id,weight,label', groupby='tail')
        }
        assert '~SAC_ARROne1' not in cmp_edges
        assert '~SAC_ARRTwo1' in cmp_edges
        assert cmp_edges['~SAC_ARRTwo1']['weight'] == 68

        # Check for seniority edges
        seniority_edges = {
            g['id']['tail'] : g['values'][0]
            for g in pc_client_v2.get_grouped_edges(invitation=f'aclweb.org/ACL/ARR/2023/August/Reviewers/-/Seniority', select='head,id,weight,label', groupby='tail')
        }
        assert set(seniority_edges.keys()) == {'~Reviewer_ARROne1'}
        assert seniority_edges['~Reviewer_ARROne1']['label'] == 'Senior'

        # Check that Reviewers/Previous groups are created for resubmissions

        # Check that explanation_of_revisions_PDF readers are set correctly for resubmissions
        submissions_after_matching = pc_client_v2.get_notes(invitation='aclweb.org/ACL/ARR/2023/August/-/Submission', sort='number:asc')
        submission_2 = submissions_after_matching[1]
        submission_3 = submissions_after_matching[2]
        
        assert set(submission_2.content['explanation_of_revisions_PDF']['readers']) == {
            "aclweb.org/ACL/ARR/2023/August/Program_Chairs",
            "aclweb.org/ACL/ARR/2023/August/Submission2/Senior_Area_Chairs",
            "aclweb.org/ACL/ARR/2023/August/Submission2/Area_Chairs",
            "aclweb.org/ACL/ARR/2023/August/Submission2/Reviewers",
            "aclweb.org/ACL/ARR/2023/August/Submission2/Authors"
        }

        assert set(submission_3.content['explanation_of_revisions_PDF']['readers']) == {
            "aclweb.org/ACL/ARR/2023/August/Program_Chairs",
            "aclweb.org/ACL/ARR/2023/August/Submission3/Senior_Area_Chairs",
            "aclweb.org/ACL/ARR/2023/August/Submission3/Area_Chairs",
            "aclweb.org/ACL/ARR/2023/August/Submission3/Reviewers/Submitted",
            "aclweb.org/ACL/ARR/2023/August/Submission3/Authors"
        }

        # Verify that previous reviewers can access explanation_of_revisions_PDF field
        # reviewer_client_1 (~Reviewer_ARROne1) was a previous reviewer for submission 2
        openreview_client.add_members_to_group('aclweb.org/ACL/ARR/2023/August/Submission2/Reviewers', '~Reviewer_ARROne1')
        submission_2_as_reviewer_1 = reviewer_client_1.get_note(submission_2.id)
        assert 'explanation_of_revisions_PDF' in submission_2_as_reviewer_1.content
        assert 'value' in submission_2_as_reviewer_1.content['explanation_of_revisions_PDF']
        assert len(submission_2_as_reviewer_1.content['explanation_of_revisions_PDF']['value']) > 0


    def test_sae_ae_assignments(self, client, openreview_client, helpers, test_client, request_page, selenium):

        pc_client=openreview.Client(username='pc@aclrollingreview.org', password=helpers.strong_password)
        pc_client_v2=openreview.api.OpenReviewClient(username='pc@aclrollingreview.org', password=helpers.strong_password)
        request_form=pc_client.get_notes(invitation='openreview.net/Support/-/Request_Form')[1]
        august_venue = openreview.helpers.get_conference(client, request_form.id, 'openreview.net/Support')
        test_client = openreview.api.OpenReviewClient(token=test_client.token)

        submissions = pc_client_v2.get_notes(invitation='aclweb.org/ACL/ARR/2023/August/-/Submission', sort='number:asc')
        june_submissions = pc_client_v2.get_notes(invitation='aclweb.org/ACL/ARR/2023/June/-/Submission', sort='number:asc')

        # Post some proposed assignment edges and deploy
        openreview_client.post_edge(openreview.api.Edge(
            invitation = 'aclweb.org/ACL/ARR/2023/August/Senior_Area_Chairs/-/Proposed_Assignment',
            head = submissions[1].id,
            tail = '~SAC_ARRTwo1',
            signatures = ['aclweb.org/ACL/ARR/2023/August/Program_Chairs'],
            weight = 1,
            label = 'sac-matching'
        ))

        openreview_client.post_edge(openreview.api.Edge(
            invitation = 'aclweb.org/ACL/ARR/2023/August/Senior_Area_Chairs/-/Proposed_Assignment',
            head = submissions[2].id,
            tail = '~SAC_ARRTwo1',
            signatures = ['aclweb.org/ACL/ARR/2023/August/Program_Chairs'],
            weight = 1,
            label = 'sac-matching'
        ))

        august_venue.set_assignments(assignment_title='sac-matching', committee_id='aclweb.org/ACL/ARR/2023/August/Senior_Area_Chairs')

        sac2_group = openreview_client.get_group('aclweb.org/ACL/ARR/2023/August/Submission2/Senior_Area_Chairs')
        assert sac2_group.members == ['~SAC_ARRTwo1']

        sac3_group = openreview_client.get_group('aclweb.org/ACL/ARR/2023/August/Submission3/Senior_Area_Chairs')
        assert sac3_group.members == ['~SAC_ARRTwo1']

        openreview_client.post_edge(openreview.api.Edge(
            invitation = 'aclweb.org/ACL/ARR/2023/August/Area_Chairs/-/Proposed_Assignment',
            head = submissions[1].id,
            tail = '~AC_ARRTwo1',
            signatures = ['aclweb.org/ACL/ARR/2023/August/Program_Chairs'],
            weight = 1,
            label = 'ac-matching'
        ))

        openreview_client.post_edge(openreview.api.Edge(
            invitation = 'aclweb.org/ACL/ARR/2023/August/Area_Chairs/-/Proposed_Assignment',
            head = submissions[2].id,
            tail = '~AC_ARRTwo1',
            signatures = ['aclweb.org/ACL/ARR/2023/August/Program_Chairs'],
            weight = 1,
            label = 'ac-matching'
        ))

        august_venue.set_assignments(assignment_title='ac-matching', committee_id='aclweb.org/ACL/ARR/2023/August/Area_Chairs')

        openreview_client.post_edge(openreview.api.Edge(
            invitation = 'aclweb.org/ACL/ARR/2023/August/Reviewers/-/Custom_Max_Papers',
            head = 'aclweb.org/ACL/ARR/2023/August/Reviewers',
            tail = '~Reviewer_ARRFour1',
            signatures = ['aclweb.org/ACL/ARR/2023/August/Program_Chairs'],
            weight = 1,
        ))

        openreview_client.post_edge(openreview.api.Edge(
            invitation = 'aclweb.org/ACL/ARR/2023/August/Reviewers/-/Proposed_Assignment',
            head = submissions[0].id,
            tail = '~Reviewer_ARRFour1',
            signatures = ['aclweb.org/ACL/ARR/2023/August/Program_Chairs'],
            weight = 1,
            label = 'reviewer-assignments'
        ))

        rev_2_edge = openreview_client.post_edge(openreview.api.Edge(
            invitation = 'aclweb.org/ACL/ARR/2023/August/Reviewers/-/Proposed_Assignment',
            head = submissions[0].id,
            tail = '~Reviewer_ARRTwo1',
            signatures = ['aclweb.org/ACL/ARR/2023/August/Program_Chairs'],
            weight = 1,
            label = 'reviewer-assignments'
        ))

        rev_3_edge = openreview_client.post_edge(openreview.api.Edge(
            invitation = 'aclweb.org/ACL/ARR/2023/August/Reviewers/-/Proposed_Assignment',
            head = submissions[0].id,
            tail = '~Reviewer_ARRThree1',
            signatures = ['aclweb.org/ACL/ARR/2023/August/Program_Chairs'],
            weight = 1,
            label = 'reviewer-assignments'
        ))

        with pytest.raises(openreview.OpenReviewException, match=r'You cannot assign more than 3 reviewers to this paper'):
            openreview_client.post_edge(openreview.api.Edge(
                invitation = 'aclweb.org/ACL/ARR/2023/August/Reviewers/-/Proposed_Assignment',
                head = submissions[0].id,
                tail = '~Reviewer_ARRFive1',
                signatures = ['aclweb.org/ACL/ARR/2023/August/Program_Chairs'],
                weight = 1,
                label = 'reviewer-assignments'
            ))

        # Revert the data to preserve the rest of the tests
        now = datetime.datetime.now()
        rev_2_edge.ddate = openreview.tools.datetime_millis(now)
        rev_3_edge.ddate = openreview.tools.datetime_millis(now)
        openreview_client.post_edge(
            rev_2_edge
        )
        openreview_client.post_edge(
            rev_3_edge
        )

        august_venue.set_assignments(assignment_title='reviewer-assignments', committee_id='aclweb.org/ACL/ARR/2023/August/Reviewers', overwrite=True, enable_reviewer_reassignment=True)

        pc_client.post_note(
            openreview.Note(
                content={
                    'setup_sae_ae_assignment_date': (openreview.tools.datetime.datetime.now() - datetime.timedelta(minutes=3)).strftime('%Y/%m/%d %H:%M')
                },
                invitation=f'openreview.net/Support/-/Request{request_form.number}/ARR_Configuration',
                forum=request_form.id,
                readers=['aclweb.org/ACL/ARR/2023/August/Program_Chairs', 'openreview.net/Support'],
                referent=request_form.id,
                replyto=request_form.id,
                signatures=['~Program_ARRChair1'],
                writers=[],
            )
        )

        helpers.await_queue_edit(openreview_client, 'aclweb.org/ACL/ARR/2023/August/-/Enable_SAE_AE_Assignments-0-1', count=1)

        assert openreview_client.get_group('aclweb.org/ACL/ARR/2023/August/Emergency_Area_Chairs')
        assert openreview_client.get_invitation('aclweb.org/ACL/ARR/2023/August/Area_Chairs/-/Invite_Assignment')
        assignment_invitation = openreview_client.get_invitation('aclweb.org/ACL/ARR/2023/August/Area_Chairs/-/Assignment')
        assert 'sync_sac_id' not in assignment_invitation.content

        # Remove an AC and replace
        sac_client = openreview.api.OpenReviewClient(username = 'sac2@aclrollingreview.com', password=helpers.strong_password)
        assert len(sac_client.get_edges(invitation = 'aclweb.org/ACL/ARR/2023/August/Area_Chairs/-/Assignment', head=submissions[1].id, tail='~AC_ARRTwo1')) == 1
        ac_edge = sac_client.get_edges(invitation = 'aclweb.org/ACL/ARR/2023/August/Area_Chairs/-/Assignment', head=submissions[1].id, tail='~AC_ARRTwo1')[0]
        ac_edge.ddate = openreview.tools.datetime_millis(openreview.tools.datetime.datetime.now())
        openreview_client.post_edge(ac_edge)

        helpers.await_queue_edit(openreview_client, invitation='aclweb.org/ACL/ARR/2023/August/Area_Chairs/-/Assignment')

        edge = openreview_client.post_edge(openreview.api.Edge(
            invitation = 'aclweb.org/ACL/ARR/2023/August/Area_Chairs/-/Assignment',
            head = submissions[1].id,
            tail = '~AC_ARROne1',
            signatures = ['aclweb.org/ACL/ARR/2023/August/Submission2/Senior_Area_Chairs'],
            weight = 1
        ))

        helpers.await_queue_edit(openreview_client, edit_id=edge.id)

        assert len(sac_client.get_edges(invitation = 'aclweb.org/ACL/ARR/2023/August/Area_Chairs/-/Assignment', head=submissions[1].id, tail='~AC_ARROne1')) == 1
        assert len(sac_client.get_group('aclweb.org/ACL/ARR/2023/August/Submission2/Area_Chairs').members) == 1
        assert sac_client.get_group('aclweb.org/ACL/ARR/2023/August/Submission2/Area_Chairs').members[0] == '~AC_ARROne1'

        pc_client.post_note(
            openreview.Note(
                content={
                    'setup_proposed_assignments_date': (openreview.tools.datetime.datetime.now() - datetime.timedelta(minutes=3)).strftime('%Y/%m/%d %H:%M'),
                    'reviewer_assignments_title': 'reviewer-assignments'
                },
                invitation=f'openreview.net/Support/-/Request{request_form.number}/ARR_Configuration',
                forum=request_form.id,
                readers=['aclweb.org/ACL/ARR/2023/August/Program_Chairs', 'openreview.net/Support'],
                referent=request_form.id,
                replyto=request_form.id,
                signatures=['~Program_ARRChair1'],
                writers=[],
            )
        )

        helpers.await_queue_edit(openreview_client, 'aclweb.org/ACL/ARR/2023/August/-/Share_Proposed_Assignments-0-1', count=1)

        # Test quota limits on reviewer assignments
        test_reviewers = [
            '~Reviewer_ARROne1',
            '~Reviewer_ARRTwo1'
        ]
        existing_edges = []
        for idx, reviewer_id in enumerate(test_reviewers):
            inv_ending = 'Invite_Assignment'
            label = 'Invitation Sent'
            existing_edges.append(
                openreview_client.post_edge(openreview.api.Edge(
                    invitation = f'aclweb.org/ACL/ARR/2023/August/Reviewers/-/{inv_ending}',
                    head = submissions[1].id,
                    tail = reviewer_id,
                    signatures = ['aclweb.org/ACL/ARR/2023/August/Program_Chairs'],
                    weight = 1,
                    label = label
                ))
            )
            helpers.await_queue_edit(openreview_client, edit_id=existing_edges[-1].id)

        ## Temporarily increase quota
        ## breaking quota so doing it manually
        ## issue being reproduced: (both pre-processes only see 2 out of 3 edges)
        ## allowing both edges to be posted
        openreview_client.post_group_edit(
            invitation='aclweb.org/ACL/ARR/2023/August/-/Edit',
            readers=['aclweb.org/ACL/ARR/2023/August'],
            writers=['aclweb.org/ACL/ARR/2023/August'],
            signatures=['aclweb.org/ACL/ARR/2023/August'],
            group=openreview.api.Group(
                id='aclweb.org/ACL/ARR/2023/August',
                content={
                    'submission_assignment_max_reviewers': {
                        'value': 4
                    }
                }
            )
        )

        existing_edges.append(
            openreview_client.post_edge(openreview.api.Edge(
                invitation = f'aclweb.org/ACL/ARR/2023/August/Reviewers/-/Invite_Assignment',
                head = submissions[1].id,
                tail = '~Reviewer_ARRThree1',
                signatures = ['aclweb.org/ACL/ARR/2023/August/Program_Chairs'],
                weight = 1,
                label = 'Invitation Sent'
            ))
        )

        existing_edges.append(
            openreview_client.post_edge(openreview.api.Edge(
                invitation = f'aclweb.org/ACL/ARR/2023/August/Reviewers/-/Invite_Assignment',
                head = submissions[1].id,
                tail = '~Reviewer_ARRFour1',
                signatures = ['aclweb.org/ACL/ARR/2023/August/Program_Chairs'],
                weight = 1,
                label = 'Invitation Sent'
            ))
        )

        ## Reset quota back down to 3 - there are 4 edges which will cause
        ## the post_edge() call in the process function to fail
        openreview_client.post_group_edit(
            invitation='aclweb.org/ACL/ARR/2023/August/-/Edit',
            readers=['aclweb.org/ACL/ARR/2023/August'],
            writers=['aclweb.org/ACL/ARR/2023/August'],
            signatures=['aclweb.org/ACL/ARR/2023/August'],
            group=openreview.api.Group(
                id='aclweb.org/ACL/ARR/2023/August',
                content={
                    'submission_assignment_max_reviewers': {
                        'value': 3
                    }
                }
            )
        )
        helpers.await_queue_edit(openreview_client, edit_id=existing_edges[-1].id)

        all_edges = openreview_client.get_edges(
            invitation=f'aclweb.org/ACL/ARR/2023/August/Reviewers/-/Invite_Assignment',
            head=submissions[1].id
        )

        print(f"Total edges in database: {len(all_edges)}")
        assert len(all_edges) == 4 ## Allows both edges to be posted

        ## Test errors - check that preprocess limits are still obeyed
        with pytest.raises(openreview.OpenReviewException, match=r'Can not make assignment, total assignments and invitations must not exceed 3'):
            openreview_client.post_edge(openreview.api.Edge(
                invitation = 'aclweb.org/ACL/ARR/2023/August/Reviewers/-/Assignment',
                head = submissions[1].id,
                tail = '~Reviewer_ARRFive1',
                signatures = ['aclweb.org/ACL/ARR/2023/August/Program_Chairs'],
                weight = 1
            ))
        with pytest.raises(openreview.OpenReviewException, match=r'Can not invite assignment, total assignments and invitations must not exceed 3'):
            openreview_client.post_edge(openreview.api.Edge(
                invitation = 'aclweb.org/ACL/ARR/2023/August/Reviewers/-/Invite_Assignment',
                head = submissions[1].id,
                tail = 'invitereviewer@aclrollingreview.org',
                signatures = ['aclweb.org/ACL/ARR/2023/August/Program_Chairs'],
                weight = 0,
                label = "Invitation Sent"
            ))

        # Decline as reviewer two with reason
        messages = openreview_client.get_messages(to='reviewer2@aclrollingreview.com', subject=f'''[ARR - August 2023] Invitation to review paper titled "{submissions[1].content['title']['value']}"''')
        assert len(messages) == 1

        for idx, message in enumerate(messages):
            text = message['content']['text']

            invitation_url = re.search('https://.*\n', text).group(0).replace('https://openreview.net', 'http://localhost:3030').replace('&amp;', '&')[:-1]
            helpers.respond_invitation(selenium, request_page, invitation_url, accept=False, comment='I am busy')
        helpers.await_queue_edit(openreview_client, invitation='aclweb.org/ACL/ARR/2023/August/Reviewers/-/Assignment_Recruitment', count=1)

        reviewer_two_edge = client.get_all_edges(invitation='aclweb.org/ACL/ARR/2023/August/Reviewers/-/Invite_Assignment', tail='~Reviewer_ARRTwo1', head=submissions[1].id)
        assert reviewer_two_edge[0].label == 'Declined: I am too busy.'

        # Assignment for reviewer 4 should post
        existing_edges.append(
            openreview_client.post_edge(openreview.api.Edge(
                invitation = 'aclweb.org/ACL/ARR/2023/August/Reviewers/-/Assignment',
                head = submissions[1].id,
                tail = '~Reviewer_ARRFour1',
                signatures = ['aclweb.org/ACL/ARR/2023/August/Program_Chairs'],
                weight = 1
            ))
        )

        # Invitation for reviewer 5 should NOT post
        with pytest.raises(openreview.OpenReviewException, match=r'Can not make assignment, total assignments and invitations must not exceed 3'):
            openreview_client.post_edge(openreview.api.Edge(
                invitation = 'aclweb.org/ACL/ARR/2023/August/Reviewers/-/Assignment',
                head = submissions[1].id,
                tail = '~Reviewer_ARRFive1',
                signatures = ['aclweb.org/ACL/ARR/2023/August/Program_Chairs'],
                weight = 1
            ))
        with pytest.raises(openreview.OpenReviewException, match=r'Can not invite assignment, total assignments and invitations must not exceed 3'):
            openreview_client.post_edge(openreview.api.Edge(
                invitation = 'aclweb.org/ACL/ARR/2023/August/Reviewers/-/Invite_Assignment',
                head = submissions[1].id,
                tail = 'invitereviewer@aclrollingreview.org',
                signatures = ['aclweb.org/ACL/ARR/2023/August/Program_Chairs'],
                weight = 0,
                label = "Invitation Sent"
            ))
        # Add conflict to profile, invite user
        reviewer_client = openreview.api.OpenReviewClient(username='reviewer7@aclrollingreview.com', password=helpers.strong_password)
        profile = reviewer_client.get_profile()
        profile.content['history'].append(
            {
                'position': 'Engineer', 
                'start': 2018, 
                'end': now.year-1, 
                'institution': {
                    'country': 'US',
                    'domain': 'cs.umass.edu'
                }
            }
        )
        reviewer_client.post_profile(profile)

        with pytest.raises(openreview.OpenReviewException, match=r'Can not invite ~Reviewer_ARRSeven1, the user has a conflict'):
            edge = openreview_client.post_edge(openreview.api.Edge(
                invitation = 'aclweb.org/ACL/ARR/2023/August/Reviewers/-/Invite_Assignment',
                head = submissions[2].id,
                tail = 'reviewer7@aclrollingreview.com',
                signatures = ['aclweb.org/ACL/ARR/2023/August/Program_Chairs'],
                weight = 0,
                label = "Invitation Sent"
            ))
        
        # Accept reviewer 3 invitation
        # Update year to outside range of conflict_N_years
        profile = reviewer_client.get_profile()
        profile.content['history'][1]['end'] = now.year-5
        reviewer_client.post_profile(profile)

        edge = openreview_client.post_edge(openreview.api.Edge(
            invitation = 'aclweb.org/ACL/ARR/2023/August/Reviewers/-/Invite_Assignment',
            head = submissions[2].id,
            tail = 'reviewer7@aclrollingreview.com',
            signatures = ['aclweb.org/ACL/ARR/2023/August/Program_Chairs'],
            weight = 0,
            label = "Invitation Sent"
        ))
        helpers.await_queue_edit(openreview_client, edge.id)

        all_edges = openreview_client.get_edges(
            invitation=f'aclweb.org/ACL/ARR/2023/August/Reviewers/-/Invite_Assignment',
            head=submissions[2].id
        )

        print(f"Total edges in database to paper {submissions[2].id}: {len(all_edges)}")
        assert len(all_edges) == 1 ## Allows both edges to be posted

        ## Assert that recruitment process function works with broken quota
        messages = openreview_client.get_messages(to='reviewer3@aclrollingreview.com', subject=f'''[ARR - August 2023] Invitation to review paper titled "{submissions[1].content['title']['value']}"''')
        assert len(messages) == 1

        for idx, message in enumerate(messages):
            text = message['content']['text']

            invitation_url = re.search('https://.*\n', text).group(0).replace('https://openreview.net', 'http://localhost:3030').replace('&amp;', '&')[:-1]
            helpers.respond_invitation(selenium, request_page, invitation_url, accept=True)

        helpers.await_queue_edit(openreview_client, invitation='aclweb.org/ACL/ARR/2023/August/Reviewers/-/Assignment_Recruitment', count=1)

        edge = openreview_client.get_all_edges(invitation='aclweb.org/ACL/ARR/2023/August/Reviewers/-/Assignment', tail='~Reviewer_ARRThree1', head=submissions[1].id)
        assert len(edge) == 1

        helpers.await_queue_edit(openreview_client, edit_id=edge[0].id)        
        ## Current state: Reviewer 1 (invite), Reviewer 3 (accepted invite + assignment), Reviewer 4 (invite + assignment)
        ## Count should be: 1 invite (Reviewer 1) + 2 assignments (Reviewer 3, Reviewer 4) = 3 (at quota)

        ## Additional quota manipulation test
        ## Increase quota to 4 to allow testing edge manipulation
        openreview_client.post_group_edit(
            invitation='aclweb.org/ACL/ARR/2023/August/-/Edit',
            readers=['aclweb.org/ACL/ARR/2023/August'],
            writers=['aclweb.org/ACL/ARR/2023/August'],
            signatures=['aclweb.org/ACL/ARR/2023/August'],
            group=openreview.api.Group(
                id='aclweb.org/ACL/ARR/2023/August',
                content={
                    'submission_assignment_max_reviewers': {
                        'value': 4
                    }
                }
            )
        )
        
        ## Post a new assignment edge (should succeed with quota = 4)
        test_assignment_edge = openreview_client.post_edge(openreview.api.Edge(
            invitation = 'aclweb.org/ACL/ARR/2023/August/Reviewers/-/Assignment',
            head = submissions[1].id,
            tail = '~Reviewer_ARRFive1',
            signatures = ['aclweb.org/ACL/ARR/2023/August/Program_Chairs'],
            weight = 1
        ))
        helpers.await_queue_edit(openreview_client, edit_id=test_assignment_edge.id)
        
        ## Delete that assignment edge
        test_assignment_edge.ddate = openreview.tools.datetime_millis(now)
        openreview_client.post_edge(test_assignment_edge)
        helpers.await_queue_edit(openreview_client, edit_id=test_assignment_edge.id)
        
        ## Post a new invite assignment edge (should succeed with quota = 4)
        test_invite_edge = openreview_client.post_edge(openreview.api.Edge(
            invitation = 'aclweb.org/ACL/ARR/2023/August/Reviewers/-/Invite_Assignment',
            head = submissions[1].id,
            tail = 'invitereviewer2@aclrollingreview.org',
            signatures = ['aclweb.org/ACL/ARR/2023/August/Program_Chairs'],
            weight = 0,
            label = "Invitation Sent"
        ))
        helpers.await_queue_edit(openreview_client, edit_id=test_invite_edge.id)
        
        ## Delete that invite assignment edge
        test_invite_edge.ddate = openreview.tools.datetime_millis(now)
        openreview_client.post_edge(test_invite_edge)
        helpers.await_queue_edit(openreview_client, edit_id=test_invite_edge.id)
        
        ## Reset quota back to 3
        openreview_client.post_group_edit(
            invitation='aclweb.org/ACL/ARR/2023/August/-/Edit',
            readers=['aclweb.org/ACL/ARR/2023/August'],
            writers=['aclweb.org/ACL/ARR/2023/August'],
            signatures=['aclweb.org/ACL/ARR/2023/August'],
            group=openreview.api.Group(
                id='aclweb.org/ACL/ARR/2023/August',
                content={
                    'submission_assignment_max_reviewers': {
                        'value': 3
                    }
                }
            )
        )

        openreview_client.remove_members_from_group(
            'aclweb.org/ACL/ARR/2023/August/Submission2/Reviewers',
            ['~Reviewer_ARRThree1']
        )

        ## Assert that recruitment process function works with > 3 reviewers (assignment can be broken by quota + 1)
        messages = openreview_client.get_messages(to='reviewer4@aclrollingreview.com', subject=f'''[ARR - August 2023] Invitation to review paper titled "{submissions[1].content['title']['value']}"''')
        assert len(messages) == 1

        for idx, message in enumerate(messages):
            text = message['content']['text']

            invitation_url = re.search('https://.*\n', text).group(0).replace('https://openreview.net', 'http://localhost:3030').replace('&amp;', '&')[:-1]
            helpers.respond_invitation(selenium, request_page, invitation_url, accept=True)

        ## Assert that recruitment process function works with quota+1
        helpers.await_queue_edit(openreview_client, invitation='aclweb.org/ACL/ARR/2023/August/Reviewers/-/Assignment_Recruitment', count=2)

        edge = openreview_client.get_all_edges(invitation='aclweb.org/ACL/ARR/2023/August/Reviewers/-/Assignment', tail='~Reviewer_ARRFour1', head=submissions[1].id)
        assert len(edge) == 1 

        helpers.await_queue_edit(openreview_client, edit_id=edge[0].id)       

        openreview_client.remove_members_from_group(
            'aclweb.org/ACL/ARR/2023/August/Submission2/Reviewers',
            ['~Reviewer_ARRThree1', '~Reviewer_ARRFour1']
        )

        ## Clean up data
        for edge in existing_edges:
            ## Cannot delete invites when already assigned
            if edge.tail == '~Reviewer_ARRThree1' or edge.tail == '~Reviewer_ARRFour1':
                continue
            edge.ddate = openreview.tools.datetime_millis(now)
            openreview_client.post_edge(edge)

        ## Can only delete assignments, invites are accepted
        edge = openreview_client.get_all_edges(invitation='aclweb.org/ACL/ARR/2023/August/Reviewers/-/Assignment', tail='~Reviewer_ARRThree1', head=submissions[1].id)
        assert len(edge) == 1
        edge = edge[0]
        edge.ddate = openreview.tools.datetime_millis(now)
        openreview_client.post_edge(edge)
        edge = openreview_client.get_all_edges(invitation='aclweb.org/ACL/ARR/2023/August/Reviewers/-/Assignment', tail='~Reviewer_ARRFour1', head=submissions[1].id)
        assert len(edge) == 1
        edge = edge[0]
        edge.ddate = openreview.tools.datetime_millis(now)
        openreview_client.post_edge(edge)

        # Test resubmission visiblity on new reviewers
        ## Post new edge from ~Reviewer_ARRSix1 to submissions 1 (same) and 2 (not same)
        existing_edges = []
        reviewer_six_client = openreview.api.OpenReviewClient(username='reviewer6@aclrollingreview.com', password=helpers.strong_password)
        existing_edges.append(openreview_client.post_edge(openreview.api.Edge(
            invitation = 'aclweb.org/ACL/ARR/2023/August/Reviewers/-/Assignment',
            head = submissions[1].id,
            tail = '~Reviewer_ARRSix1',
            signatures = ['aclweb.org/ACL/ARR/2023/August/Program_Chairs'],
            weight = 1
        )))
        
        helpers.await_queue_edit(openreview_client, edit_id=existing_edges[-1].id)

        assert '~Reviewer_ARRSix1' in openreview_client.get_group('aclweb.org/ACL/ARR/2023/August/Submission2/Reviewers').members
        reviewer_six_client.get_note(june_submissions[1].id, details='replies')

        existing_edges.append(openreview_client.post_edge(openreview.api.Edge(
            invitation = 'aclweb.org/ACL/ARR/2023/August/Reviewers/-/Assignment',
            head = submissions[2].id,
            tail = '~Reviewer_ARRSix1',
            signatures = ['aclweb.org/ACL/ARR/2023/August/Program_Chairs'],
            weight = 1
        )))
        helpers.await_queue_edit(openreview_client, edit_id=existing_edges[-1].id)

        assert '~Reviewer_ARRSix1' in openreview_client.get_group('aclweb.org/ACL/ARR/2023/August/Submission3/Reviewers').members
        with pytest.raises(openreview.OpenReviewException, match=r'User Reviewer ARRSix does not have permission to see Note ' + june_submissions[2].id):
            reviewer_six_client.get_note(june_submissions[2].id, details='replies')


        ## Clean up data
        for edge in existing_edges:
            edge.ddate = openreview.tools.datetime_millis(now)
            openreview_client.post_edge(edge)
            helpers.await_queue_edit(openreview_client, edit_id=edge.id, count=2)
