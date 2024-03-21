import time
import openreview
import pytest
import datetime
import re
import random
import os
import csv
import sys
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from openreview import ProfileManagement
from openreview.venue import matching
from openreview.stages.arr_content import (
    arr_submission_content,
    hide_fields,
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
class TestARRVenueV2():
    @pytest.fixture(scope="class")
    def profile_management(self, openreview_client):
        profile_management = ProfileManagement(openreview_client, 'openreview.net')
        profile_management.setup()
        return profile_management
    def test_august_cycle(self, client, openreview_client, helpers, test_client, profile_management):

        now = datetime.datetime.utcnow()
        due_date = now + datetime.timedelta(days=3)

        # Post the request form note
        helpers.create_user('pc@aclrollingreview.org', 'Program', 'ARRChair')
        pc_client = openreview.Client(username='pc@aclrollingreview.org', password=helpers.strong_password)
        pc_client_v2 = openreview.api.OpenReviewClient(username='pc@aclrollingreview.org', password=helpers.strong_password)

        sac_client = helpers.create_user('sac1@aclrollingreview.com', 'SAC', 'ARROne')
        helpers.create_user('sac2@aclrollingreview.com', 'SAC', 'ARRTwo')
        helpers.create_user('ec1@aclrollingreview.com', 'EthicsChair', 'ARROne')
        helpers.create_user('ac1@aclrollingreview.com', 'AC', 'ARROne')
        helpers.create_user('ac2@aclrollingreview.com', 'AC', 'ARRTwo')
        helpers.create_user('ac3@aclrollingreview.com', 'AC', 'ARRThree')
        helpers.create_user('reviewer1@aclrollingreview.com', 'Reviewer', 'ARROne')
        helpers.create_user('reviewer2@aclrollingreview.com', 'Reviewer', 'ARRTwo')
        helpers.create_user('reviewer3@aclrollingreview.com', 'Reviewer', 'ARRThree')
        helpers.create_user('reviewer4@aclrollingreview.com', 'Reviewer', 'ARRFour')
        helpers.create_user('reviewer5@aclrollingreview.com', 'Reviewer', 'ARRFive')
        helpers.create_user('reviewer6@aclrollingreview.com', 'Reviewer', 'ARRSix')
        helpers.create_user('reviewerethics@aclrollingreview.com', 'EthicsReviewer', 'ARROne')

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
                'submission_license': ['CC BY-SA 4.0']
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

        assert openreview_client.get_group('aclweb.org/ACL/ARR/2023/August')
        assert openreview_client.get_group('aclweb.org/ACL/ARR/2023/August/Senior_Area_Chairs')
        assert openreview_client.get_group('aclweb.org/ACL/ARR/2023/August/Area_Chairs')
        assert openreview_client.get_group('aclweb.org/ACL/ARR/2023/August/Reviewers')
        assert openreview_client.get_group('aclweb.org/ACL/ARR/2023/August/Authors')

        submission_invitation = openreview_client.get_invitation('aclweb.org/ACL/ARR/2023/August/-/Submission')
        assert submission_invitation
        assert submission_invitation.duedate

        assert openreview_client.get_invitation('aclweb.org/ACL/ARR/2023/August/Reviewers/-/Expertise_Selection')

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
                'hide_fields': hide_fields
            }
        ))

        helpers.await_queue_edit(client, invitation=f'openreview.net/Support/-/Request{request_form_note.number}/Revision')

        submission_invitation = openreview_client.get_invitation('aclweb.org/ACL/ARR/2023/August/-/Submission')
        assert submission_invitation
        assert 'responsible_NLP_research' in submission_invitation.edit['note']['content']
        assert 'keywords' not in submission_invitation.edit['note']['content']

        domain = openreview_client.get_group('aclweb.org/ACL/ARR/2023/August')
        assert 'recommendation' == domain.content['meta_review_recommendation']['value']

        # Build current cycle invitations
        venue = openreview.helpers.get_conference(client, request_form_note.id, 'openreview.net/Support')
        invitation_builder = openreview.arr.InvitationBuilder(venue)

        assert client.get_invitation(f'openreview.net/Support/-/Request{request_form_note.number}/ARR_Configuration')
        assert openreview_client.get_invitation('aclweb.org/ACL/ARR/2023/August/-/Preprint_Release_Submission')
        assert openreview_client.get_invitation('aclweb.org/ACL/ARR/2023/August/-/ARR_Scheduler')

        now = datetime.datetime.utcnow()

        registration_name = 'Registration'
        max_load_name = 'Max_Load_And_Unavailability_Request'
        pc_client.post_note(
            openreview.Note(
                content={
                    'form_expiration_date': (due_date).strftime('%Y/%m/%d %H:%M:%S'),
                    'author_consent_due_date': (due_date).strftime('%Y/%m/%d %H:%M:%S'),
                    'maximum_load_due_date': (due_date).strftime('%Y/%m/%d %H:%M:%S'),
                    'maximum_load_exp_date': (due_date).strftime('%Y/%m/%d %H:%M:%S'),
                    'ae_checklist_due_date': (due_date).strftime('%Y/%m/%d %H:%M:%S'),
                    'ae_checklist_exp_date': (due_date).strftime('%Y/%m/%d %H:%M:%S'),
                    'reviewer_checklist_due_date': (due_date).strftime('%Y/%m/%d %H:%M:%S'),
                    'reviewer_checklist_exp_date': (due_date).strftime('%Y/%m/%d %H:%M:%S'),
                    'ethics_reviewing_start_date': (now).strftime('%Y/%m/%d %H:%M:%S'),
                    'ethics_reviewing_due_date': (now).strftime('%Y/%m/%d %H:%M:%S'),
                    'ethics_reviewing_exp_date': (now).strftime('%Y/%m/%d %H:%M:%S'),
                    'emergency_reviewing_start_date': (due_date).strftime('%Y/%m/%d %H:%M:%S'),
                    'emergency_reviewing_due_date': (due_date).strftime('%Y/%m/%d %H:%M:%S'),
                    'emergency_reviewing_exp_date': (due_date).strftime('%Y/%m/%d %H:%M:%S'),
                    'emergency_metareviewing_start_date': (due_date).strftime('%Y/%m/%d %H:%M:%S'),
                    'emergency_metareviewing_due_date': (due_date).strftime('%Y/%m/%d %H:%M:%S'),
                    'emergency_metareviewing_exp_date': (due_date).strftime('%Y/%m/%d %H:%M:%S'),
                    'comment_start_date': (now - datetime.timedelta(days=2)).strftime('%Y/%m/%d %H:%M:%S'),
                    'comment_end_date': (now + datetime.timedelta(days=365)).strftime('%Y/%m/%d %H:%M:%S')
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
                                            "input": "radio",
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

    def test_june_cycle(self, client, openreview_client, helpers, test_client, profile_management):
        # Build the previous cycle
        pc_client=openreview.Client(username='pc@aclrollingreview.org', password=helpers.strong_password)
        pc_client_v2 = openreview.api.OpenReviewClient(username='pc@aclrollingreview.org', password=helpers.strong_password)

        now = datetime.datetime.utcnow()
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
                'submission_license': ['CC BY-SA 4.0']
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
                f"~Reviewer_ARR{num}1" for num in ['One', 'Two', 'Three', 'Four', 'Five', 'Six']
            ]
        )
        openreview_client.add_members_to_group(
            venue.get_area_chairs_id(), [
                f"~AC_ARR{num}1" for num in ['One', 'Two', 'Three']
            ]
        )
        openreview_client.add_members_to_group(
            venue.get_senior_area_chairs_id(), [
                f"~SAC_ARR{num}1" for num in ['One', 'Two']
            ]
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

        ## Post a submission to get Ethics Stage to work
        test_client = openreview.api.OpenReviewClient(token=test_client.token)

        note = openreview.api.Note(
            content = {
                'title': { 'value': 'Paper title ' + str(1) },
                'abstract': { 'value': 'This is an abstract ' + str(1) },
                'keywords': { 'value': ['keyword1']},
                'authorids': { 'value': ['~SomeFirstName_User1', 'peter@mail.com', 'andrew@umass.edu']},
                'authors': { 'value': ['SomeFirstName User', 'Peter SomeLastName', 'Andrew Mc'] },
                'TLDR': { 'value': 'This is a tldr ' + str(1) },
                'pdf': {'value': '/pdf/' + 'p' * 40 +'.pdf' }
            }
        )

        test_client.post_note_edit(invitation='aclweb.org/ACL/ARR/2023/June/-/Submission',
            signatures=['~SomeFirstName_User1'],
            note=note)

        helpers.await_queue_edit(openreview_client, invitation='aclweb.org/ACL/ARR/2023/June/-/Submission', count=1)

        # Create ethics review stage to add values into domain
        now = datetime.datetime.utcnow()
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
                'release_submissions_to_ethics_reviewers': 'We confirm we want to release the submissions and reviews to the ethics reviewers'
            },
            forum=request_form_note.forum,
            referent=request_form_note.forum,
            invitation='openreview.net/Support/-/Request{}/Ethics_Review_Stage'.format(request_form_note.number),
            readers=[venue.get_program_chairs_id(), 'openreview.net/Support'],
            signatures=['~Program_ARRChair1'],
            writers=[]
        ))
        
        helpers.await_queue_edit(client, invitation=f'openreview.net/Support/-/Request{request_form_note.number}/Ethics_Review_Stage')

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
        reviewer_three_client = openreview.api.OpenReviewClient(username = 'reviewer3@aclrollingreview.com', password=helpers.strong_password)
        reviewer_four_client = openreview.api.OpenReviewClient(username = 'reviewer4@aclrollingreview.com', password=helpers.strong_password)
        reviewer_five_client = openreview.api.OpenReviewClient(username = 'reviewer5@aclrollingreview.com', password=helpers.strong_password)
        ac_client = openreview.api.OpenReviewClient(username = 'ac1@aclrollingreview.com', password=helpers.strong_password)
        sac_client = openreview.api.OpenReviewClient(username = 'sac1@aclrollingreview.com', password=helpers.strong_password)
        reviewer_client.post_note_edit(
            invitation=f'{venue.get_reviewers_id()}/-/{registration_name}',
            signatures=['~Reviewer_ARROne1'],
            note=openreview.api.Note(
                content = {
                    'profile_confirmed': { 'value': 'Yes' },
                    'expertise_confirmed': { 'value': 'Yes' },
                    'domains': { 'value': 'Yes' },
                    'emails': { 'value': 'Yes' },
                    'DBLP': { 'value': 'Yes' },
                    'semantic_scholar': { 'value': 'Yes' },
                    'research_area': { 'value': ['Generation', 'Information Extraction'] },
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
                    'research_area': { 'value': ['Summarization', 'Generation'] },
                }
            )
        )
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
                    'research_area': { 'value': ['Generation', 'NLP Applications'] },
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
                    'research_area': { 'value': ['Generation', 'Summarization', 'NLP Applications'] },
                }
            )
        )

        # Post past unavailability notes
        reviewer_client.post_note_edit( ## Reviewer should be available - next available date is now
            invitation=f'{venue.get_reviewers_id()}/-/{max_load_name}',
            signatures=['~Reviewer_ARROne1'],
            note=openreview.api.Note(
                content = {
                    'maximum_load': { 'value': '0' },
                    'maximum_load_resubmission': { 'value': 'No' },
                    'next_available_month': { 'value': 'August'},
                    'next_available_year': { 'value':  2023}
                }
            )
        )
        with pytest.raises(openreview.OpenReviewException, match=r'Please provide both your next available year and month'):
            reviewer_two_client.post_note_edit(
                invitation=f'{venue.get_reviewers_id()}/-/{max_load_name}',
                signatures=['~Reviewer_ARRTwo1'],
                note=openreview.api.Note(
                    content = {
                        'maximum_load': { 'value': '0' },
                        'maximum_load_resubmission': { 'value': 'No' },
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
                        'maximum_load': { 'value': '0' },
                        'maximum_load_resubmission': { 'value': 'No' },
                        'next_available_year': { 'value': 2024}
                    }
                )
            )
        reviewer_two_client.post_note_edit( ## Reviewer should not be available - 1 month past next cycle
                invitation=f'{venue.get_reviewers_id()}/-/{max_load_name}',
                signatures=['~Reviewer_ARRTwo1'],
                note=openreview.api.Note(
                    content = {
                        'maximum_load': { 'value': '0' },
                        'maximum_load_resubmission': { 'value': 'No' },
                        'next_available_month': { 'value': 'September'},
                        'next_available_year': { 'value':  2023}
                    }
                )
            )
        reviewer_three_client.post_note_edit( ## Reviewer should be available - 1 month in the past
                invitation=f'{venue.get_reviewers_id()}/-/{max_load_name}',
                signatures=['~Reviewer_ARRThree1'],
                note=openreview.api.Note(
                    content = {
                        'maximum_load': { 'value': '0' },
                        'maximum_load_resubmission': { 'value': 'No' },
                        'next_available_month': { 'value': 'July'},
                        'next_available_year': { 'value':  2023}
                    }
                )
            )
        reviewer_four_client.post_note_edit( ## Reviewer should be available - 1 year in the past
                invitation=f'{venue.get_reviewers_id()}/-/{max_load_name}',
                signatures=['~Reviewer_ARRFour1'],
                note=openreview.api.Note(
                    content = {
                        'maximum_load': { 'value': '0' },
                        'maximum_load_resubmission': { 'value': 'No' },
                        'next_available_month': { 'value': 'August'},
                        'next_available_year': { 'value':  2022}
                    }
                )
            )
        reviewer_five_client.post_note_edit( ## Reviewer should be available - 1 year in the past + 1 month in the past
                invitation=f'{venue.get_reviewers_id()}/-/{max_load_name}',
                signatures=['~Reviewer_ARRFive1'],
                note=openreview.api.Note(
                    content = {
                        'maximum_load': { 'value': '0' },
                        'maximum_load_resubmission': { 'value': 'No' },
                        'next_available_month': { 'value': 'July'},
                        'next_available_year': { 'value':  2022}
                    }
                )
            ) 
        ac_client.post_note_edit( ## AC should not be available - 1 year into future
            invitation=f'{venue.get_area_chairs_id()}/-/{max_load_name}',
            signatures=['~AC_ARROne1'],
            note=openreview.api.Note(
                content = {
                    'maximum_load': { 'value': '0' },
                    'maximum_load_resubmission': { 'value': 'No' },
                    'next_available_month': { 'value': 'August'},
                    'next_available_year': { 'value':  2024}
                }
            )
        )
        sac_client.post_note_edit( ## SAC should not be available - 1 month + 1 year into future
            invitation=f'{venue.get_senior_area_chairs_id()}/-/{max_load_name}',
            signatures=['~SAC_ARROne1'],
            note=openreview.api.Note(
                content = {
                    'maximum_load': { 'value': '0' },
                    'maximum_load_resubmission': { 'value': 'Yes' },
                    'next_available_month': { 'value': 'September'},
                    'next_available_year': { 'value':  2024}
                }
            )
        )

        # Create past expertise edges
        user_client = openreview.api.OpenReviewClient(username='reviewer1@aclrollingreview.com', password=helpers.strong_password)
        archive_note = user_client.post_note_edit(
            invitation='openreview.net/Archive/-/Direct_Upload',
            signatures=['~Reviewer_ARROne1'],
            note = openreview.api.Note(
                pdate = openreview.tools.datetime_millis(datetime.datetime(2019, 4, 30)),
                content = {
                    'title': { 'value': 'Paper title 2' },
                    'abstract': { 'value': 'Paper abstract 2' },
                    'authors': { 'value': ['Reviewer ARR', 'Test2 Client'] },
                    'authorids': { 'value': ['~Reviewer_ARROne1', 'test2@mail.com'] },
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
                    "agreement": { "value": "I agree"}
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

    
    def test_submission_preprocess(self, client, openreview_client, test_client, helpers):
        # Update the submission preprocess function and test validation for combinations
        # of previous_URL/reassignment_request_action_editor/reassignment_request_reviewers
        pc_client=openreview.Client(username='pc@aclrollingreview.org', password=helpers.strong_password)
        pc_client_v2=openreview.api.OpenReviewClient(username='pc@aclrollingreview.org', password=helpers.strong_password)
        request_form=pc_client.get_notes(invitation='openreview.net/Support/-/Request_Form')[0]
        june_venue = openreview.helpers.get_conference(client, request_form.id, 'openreview.net/Support')
        test_client = openreview.api.OpenReviewClient(token=test_client.token)

        generic_note_content = {
            'title': { 'value': 'Paper title '},
            'abstract': { 'value': 'This is an abstract ' },
            'authorids': { 'value': ['~SomeFirstName_User1', 'peter@mail.com', 'andrew@meta.com']},
            'authors': { 'value': ['SomeFirstName User', 'Peter SomeLastName', 'Andrew Mc'] },
            'TLDR': { 'value': 'This is a tldr '},
            'pdf': {'value': '/pdf/' + 'p' * 40 +'.pdf' },
            'responsible_NLP_research': {'value': '/pdf/' + 'p' * 40 +'.pdf' },
            'paper_type': { 'value': 'short' },
            'research_area': { 'value': 'Generation' },
            'software': {'value': '/pdf/' + 'p' * 40 +'.zip' },
            'data': {'value': '/pdf/' + 'p' * 40 +'.zip' },
            'preprint': { 'value': 'yes'},
            'existing_preprints': { 'value': 'existing_preprints' },
            'preferred_venue': { 'value': 'ACL Conference' },
            'consent_to_share_data': { 'value': 'yes' },
            'consent_to_review': { 'value': 'yes' }
        }

        now = datetime.datetime.utcnow()
        due_date = now + datetime.timedelta(days=3)

        invitation_builder = openreview.arr.InvitationBuilder(june_venue)

        assert openreview_client.get_invitation('aclweb.org/ACL/ARR/2023/June/-/ARR_Scheduler')

        pc_client.post_note(
            openreview.Note(
                content={
                    'form_expiration_date': (due_date).strftime('%Y/%m/%d %H:%M:%S'),
                    'maximum_load_due_date': (due_date).strftime('%Y/%m/%d %H:%M:%S'),
                    'maximum_load_exp_date': (due_date).strftime('%Y/%m/%d %H:%M:%S'),
                    'ae_checklist_due_date': (due_date).strftime('%Y/%m/%d %H:%M:%S'),
                    'ae_checklist_exp_date': (due_date).strftime('%Y/%m/%d %H:%M:%S'),
                    'reviewer_checklist_due_date': (due_date).strftime('%Y/%m/%d %H:%M:%S'),
                    'reviewer_checklist_exp_date': (due_date).strftime('%Y/%m/%d %H:%M:%S'),
                },
                invitation=f'openreview.net/Support/-/Request{request_form.number}/ARR_Configuration',
                forum=request_form.id,
                readers=['aclweb.org/ACL/ARR/2023/June/Program_Chairs', 'openreview.net/Support'],
                referent=request_form.id,
                replyto=request_form.id,
                signatures=['~Program_ARRChair1'],
                writers=[],
            )
        )

        helpers.await_queue()

        # Update submission fields
        pc_client.post_note(openreview.Note(
            invitation=f'openreview.net/Support/-/Request{request_form.number}/Revision',
            forum=request_form.id,
            readers=['aclweb.org/ACL/ARR/2023/June/Program_Chairs', 'openreview.net/Support'],
            referent=request_form.id,
            replyto=request_form.id,
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
                },
                'hide_fields': hide_fields
            }
        ))

        helpers.await_queue_edit(client, invitation=f'openreview.net/Support/-/Request{request_form.number}/Revision')

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
                    'previous_URL': { 'value': f"http://localhost:3030/forum?id={allowed_note['note']['id']}" },
                    'reassignment_request_action_editor': {'value': 'No, I want the same action editor from our previous submission and understand that a new action editor may be assigned if the previous one is unavailable' },
                    'reassignment_request_reviewers': { 'value': 'Yes, I want a different set of reviewers' },
                    'justification_for_not_keeping_action_editor_or_reviewers': { 'value': 'We would like to keep the same reviewers and action editor because they are experts in the field and have provided valuable feedback on our previous submission.' }
                }
        )

        allowed_note_second = test_client.post_note_edit(invitation='aclweb.org/ACL/ARR/2023/June/-/Submission',
            signatures=['~SomeFirstName_User1'],
            note=note)
        
        helpers.await_queue_edit(openreview_client, edit_id=allowed_note_second['id'])

        # Not allowed: submission with invalid previous URL
        with pytest.raises(openreview.OpenReviewException, match=r'Provided paper link does not correspond to a submission in OpenReview'):
            test_client.post_note_edit(invitation='aclweb.org/ACL/ARR/2023/June/-/Submission',
                signatures=['~SomeFirstName_User1'],
                note=openreview.api.Note(
                content = {
                    **generic_note_content,
                    'previous_URL': { 'value': 'https://arxiv.org/abs/1234.56789' },
                    'reassignment_request_action_editor': {'value': 'No, I want the same action editor from our previous submission and understand that a new action editor may be assigned if the previous one is unavailable' },
                    'reassignment_request_reviewers': { 'value': 'Yes, I want a different set of reviewers' },
                    'justification_for_not_keeping_action_editor_or_reviewers': { 'value': 'We would like to keep the same reviewers and action editor because they are experts in the field and have provided valuable feedback on our previous submission.' },
                }
            )
        )

        # Not allowed: submission with reassignment requests and no previous URL
        with pytest.raises(openreview.OpenReviewException, match=r'You have selected a reassignment request with no previous URL. Please enter a URL or close and re-open the submission form to clear your reassignment request'):
            test_client.post_note_edit(invitation='aclweb.org/ACL/ARR/2023/June/-/Submission',
                signatures=['~SomeFirstName_User1'],
                note=openreview.api.Note(
                content = {
                    **generic_note_content,
                    'reassignment_request_action_editor': {'value': 'No, I want the same action editor from our previous submission and understand that a new action editor may be assigned if the previous one is unavailable' },
                    'reassignment_request_reviewers': { 'value': 'Yes, I want a different set of reviewers' },
                    'justification_for_not_keeping_action_editor_or_reviewers': { 'value': 'We would like to keep the same reviewers and action editor because they are experts in the field and have provided valuable feedback on our previous submission.' },
                }
            )
        )

        # Not allowed: submission with reviewer reassignment request and no previous URL
        with pytest.raises(openreview.OpenReviewException, match=r'You have selected a reassignment request with no previous URL. Please enter a URL or close and re-open the submission form to clear your reassignment request'):
            test_client.post_note_edit(invitation='aclweb.org/ACL/ARR/2023/June/-/Submission',
                signatures=['~SomeFirstName_User1'],
                note=openreview.api.Note(
                content = {
                    **generic_note_content,
                    'reassignment_request_reviewers': { 'value': 'Yes, I want a different set of reviewers' },
                    'justification_for_not_keeping_action_editor_or_reviewers': { 'value': 'We would like to keep the same reviewers and action editor because they are experts in the field and have provided valuable feedback on our previous submission.' },
                }
            )
        )

        # Not allowed: submission with AE reassignment request and no previous URL
        with pytest.raises(openreview.OpenReviewException, match=r'You have selected a reassignment request with no previous URL. Please enter a URL or close and re-open the submission form to clear your reassignment request'):
            test_client.post_note_edit(invitation='aclweb.org/ACL/ARR/2023/June/-/Submission',
                signatures=['~SomeFirstName_User1'],
                note=openreview.api.Note(
                content = {
                    **generic_note_content,
                    'reassignment_request_action_editor': {'value': 'No, I want the same action editor from our previous submission and understand that a new action editor may be assigned if the previous one is unavailable' },
                    'justification_for_not_keeping_action_editor_or_reviewers': { 'value': 'We would like to keep the same reviewers and action editor because they are experts in the field and have provided valuable feedback on our previous submission.' },
                }
            )
        )

        # Not allowed: submission with previous URL and no reassignment requests
        with pytest.raises(openreview.OpenReviewException, match=r'Since you are re-submitting, please indicate if you would like the same editors/reviewers as your indicated previous submission'):
            test_client.post_note_edit(invitation='aclweb.org/ACL/ARR/2023/June/-/Submission',
                signatures=['~SomeFirstName_User1'],
                note=openreview.api.Note(
                content = {
                    **generic_note_content,
                    'previous_URL': { 'value': f"http://localhost:3030/forum?id={allowed_note['note']['id']}" },
                    'justification_for_not_keeping_action_editor_or_reviewers': { 'value': 'We would like to keep the same reviewers and action editor because they are experts in the field and have provided valuable feedback on our previous submission.' },
                }
            )
        )

        # Not allowed: submission with previous URL and only reviewer reassignment request
        with pytest.raises(openreview.OpenReviewException, match=r'Since you are re-submitting, please indicate if you would like the same editors/reviewers as your indicated previous submission'):
            test_client.post_note_edit(invitation='aclweb.org/ACL/ARR/2023/June/-/Submission',
                signatures=['~SomeFirstName_User1'],
                note=openreview.api.Note(
                content = {
                    **generic_note_content,
                    'previous_URL': { 'value': f"http://localhost:3030/forum?id={allowed_note['note']['id']}" },
                    'reassignment_request_reviewers': { 'value': 'Yes, I want a different set of reviewers' },
                    'justification_for_not_keeping_action_editor_or_reviewers': { 'value': 'We would like to keep the same reviewers and action editor because they are experts in the field and have provided valuable feedback on our previous submission.' },
                }
            )
        )

        # Not allowed: submission with previous URL and only AE reassignment request
        with pytest.raises(openreview.OpenReviewException, match=r'Since you are re-submitting, please indicate if you would like the same editors/reviewers as your indicated previous submission'):
            test_client.post_note_edit(invitation='aclweb.org/ACL/ARR/2023/June/-/Submission',
                signatures=['~SomeFirstName_User1'],
                note=openreview.api.Note(
                content = {
                    **generic_note_content,
                    'previous_URL': { 'value': f"http://localhost:3030/forum?id={allowed_note['note']['id']}" },
                    'reassignment_request_action_editor': {'value': 'No, I want the same action editor from our previous submission and understand that a new action editor may be assigned if the previous one is unavailable' },
                    'justification_for_not_keeping_action_editor_or_reviewers': { 'value': 'We would like to keep the same reviewers and action editor because they are experts in the field and have provided valuable feedback on our previous submission.' },
                }
            )
        )

        # Call post submission to setup for reassignment tests
        pc_client.post_note(openreview.Note(
            invitation=f'openreview.net/Support/-/Request{request_form.number}/Revision',
            forum=request_form.id,
            readers=['aclweb.org/ACL/ARR/2023/June/Program_Chairs', 'openreview.net/Support'],
            referent=request_form.id,
            replyto=request_form.id,
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
                },
                'hide_fields': hide_fields
            }
        ))

        helpers.await_queue()

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

        now = datetime.datetime.utcnow()

        pc_client.post_note(
            openreview.Note(
                content={
                    'previous_cycle': 'aclweb.org/ACL/ARR/2023/June',
                    'setup_shared_data_date': (openreview.tools.datetime.datetime.utcnow() + datetime.timedelta(seconds=10)).strftime('%Y/%m/%d %H:%M:%S')
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

        helpers.await_queue_edit(openreview_client, 'aclweb.org/ACL/ARR/2023/August/-/ARR_Scheduler-0-0', count=1)

        # Call twice to ensure data only gets copied once
        pc_client.post_note(
            openreview.Note(
                content={
                    'previous_cycle': 'aclweb.org/ACL/ARR/2023/June',
                    'setup_shared_data_date': (openreview.tools.datetime.datetime.utcnow() + datetime.timedelta(seconds=3)).strftime('%Y/%m/%d %H:%M:%S')
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

        helpers.await_queue_edit(openreview_client, 'aclweb.org/ACL/ARR/2023/August/-/ARR_Scheduler-0-0', count=2)

        # Find August in readers of groups and registration notes
        assert set(pc_client_v2.get_group(june_venue.get_reviewers_id()).members).difference({'~AC_ARROne1', '~SAC_ARROne1'}) == set(pc_client_v2.get_group(august_venue.get_reviewers_id()).members)
        assert set(pc_client_v2.get_group(june_venue.get_area_chairs_id()).members).difference({'~SAC_ARROne1'}) == set(pc_client_v2.get_group(august_venue.get_area_chairs_id()).members)
        assert set(pc_client_v2.get_group(june_venue.get_senior_area_chairs_id()).members) == set(pc_client_v2.get_group(august_venue.get_senior_area_chairs_id()).members)
        assert set(pc_client_v2.get_group(june_venue.get_ethics_reviewers_id()).members) == set(pc_client_v2.get_group(august_venue.get_ethics_reviewers_id()).members)
        assert set(pc_client_v2.get_group(june_venue.get_ethics_chairs_id()).members) == set(pc_client_v2.get_group(august_venue.get_ethics_chairs_id()).members)

        june_reviewer_registration_notes = pc_client_v2.get_all_notes(invitation=f"{june_venue.get_reviewers_id()}/-/Registration")
        august_reviewer_registration_notes = pc_client_v2.get_all_notes(invitation=f"{august_venue.get_reviewers_id()}/-/Registration")
        august_reviewer_signatures = [a.signatures[0] for a in august_reviewer_registration_notes]
        assert all(j.signatures[0] in august_reviewer_signatures for j in june_reviewer_registration_notes)

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
        now = datetime.datetime.utcnow()
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
        assert all(note.content['maximum_load']['value'] == '0' for note in august_reviewer_notes)

        migrated_acs = {'~AC_ARROne1'}
        august_ac_notes = pc_client_v2.get_all_notes(invitation=f"{august_venue.get_area_chairs_id()}/-/{max_load_name}")
        assert len(august_ac_notes) == len(migrated_acs)
        assert set([note.signatures[0] for note in august_ac_notes]) == migrated_acs
        assert all(note.content['maximum_load']['value'] == '0' for note in august_ac_notes)

        migrated_sacs = {'~SAC_ARROne1'}
        august_sacs_notes = pc_client_v2.get_all_notes(invitation=f"{august_venue.get_senior_area_chairs_id()}/-/{max_load_name}")
        assert len(august_sacs_notes) == len(migrated_sacs)
        assert set([note.signatures[0] for note in august_sacs_notes]) == migrated_sacs
        assert all(note.content['maximum_load']['value'] == '0' for note in august_sacs_notes)

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
        reviewer_client = openreview.api.OpenReviewClient(username = 'reviewer1@aclrollingreview.com', password=helpers.strong_password)
        ac_client = openreview.api.OpenReviewClient(username = 'ac2@aclrollingreview.com', password=helpers.strong_password)
        sac_client = openreview.api.OpenReviewClient(username = 'sac2@aclrollingreview.com', password=helpers.strong_password)

        reviewer_note_edit = reviewer_client.post_note_edit(
                invitation=f'{august_venue.get_reviewers_id()}/-/{max_load_name}',
                signatures=['~Reviewer_ARROne1'],
                note=openreview.api.Note(
                    content = {
                        'maximum_load': { 'value': '4' },
                        'maximum_load_resubmission': { 'value': 'No' }
                    }
                )
            ) 
        ac_note_edit = ac_client.post_note_edit(
            invitation=f'{august_venue.get_area_chairs_id()}/-/{max_load_name}',
            signatures=['~AC_ARRTwo1'],
            note=openreview.api.Note(
                content = {
                    'maximum_load': { 'value': '6' },
                    'maximum_load_resubmission': { 'value': 'Yes' }
                }
            )
        )
        sac_note_edit = sac_client.post_note_edit(
            invitation=f'{august_venue.get_senior_area_chairs_id()}/-/{max_load_name}',
            signatures=['~SAC_ARRTwo1'],
            note=openreview.api.Note(
                content = {
                    'maximum_load': { 'value': '10' },
                    'maximum_load_resubmission': { 'value': 'Yes' }
                }
            )
        )

        helpers.await_queue_edit(openreview_client, edit_id=reviewer_note_edit['id'])
        helpers.await_queue_edit(openreview_client, edit_id=ac_note_edit['id'])
        helpers.await_queue_edit(openreview_client, edit_id=sac_note_edit['id'])

        august_reviewer_edges = {o['id']['tail']: [j['weight'] for j in o['values']] for o in pc_client_v2.get_grouped_edges(invitation=f"{august_venue.get_reviewers_id()}/-/Custom_Max_Papers", groupby='tail', select='weight')}
        august_ac_edges = {o['id']['tail']: [j['weight'] for j in o['values']] for o in pc_client_v2.get_grouped_edges(invitation=f"{august_venue.get_area_chairs_id()}/-/Custom_Max_Papers", groupby='tail', select='weight')}
        august_sac_edges = {o['id']['tail']: [j['weight'] for j in o['values']] for o in pc_client_v2.get_grouped_edges(invitation=f"{august_venue.get_senior_area_chairs_id()}/-/Custom_Max_Papers", groupby='tail', select='weight')}
        assert '~Reviewer_ARROne1' in august_reviewer_edges
        assert len(august_reviewer_edges['~Reviewer_ARROne1']) == 1 and set(august_reviewer_edges['~Reviewer_ARROne1']) == {4}
        assert '~AC_ARRTwo1' in august_ac_edges
        assert len(august_ac_edges['~AC_ARRTwo1']) == 1 and set(august_ac_edges['~AC_ARRTwo1']) == {6}
        assert '~SAC_ARRTwo1' in august_sac_edges
        assert len(august_sac_edges['~SAC_ARRTwo1']) == 1 and set(august_sac_edges['~SAC_ARRTwo1']) == {10}

        # Test editing
        reviewer_note_edit = reviewer_client.post_note_edit(
                invitation=f'{august_venue.get_reviewers_id()}/-/{max_load_name}',
                signatures=['~Reviewer_ARROne1'],
                note=openreview.api.Note(
                    id = reviewer_note_edit['note']['id'],
                    content = {
                        'maximum_load': { 'value': '5' },
                        'maximum_load_resubmission': { 'value': 'No' }
                    }
                )
            ) 
        ac_note_edit = ac_client.post_note_edit(
            invitation=f'{august_venue.get_area_chairs_id()}/-/{max_load_name}',
            signatures=['~AC_ARRTwo1'],
            note=openreview.api.Note(
                id = ac_note_edit['note']['id'],
                content = {
                    'maximum_load': { 'value': '7' },
                    'maximum_load_resubmission': { 'value': 'Yes' }
                }
            )
        )
        sac_note_edit = sac_client.post_note_edit(
            invitation=f'{august_venue.get_senior_area_chairs_id()}/-/{max_load_name}',
            signatures=['~SAC_ARRTwo1'],
            note=openreview.api.Note(
                id = sac_note_edit['note']['id'],
                content = {
                    'maximum_load': { 'value': '11' },
                    'maximum_load_resubmission': { 'value': 'Yes' }
                }
            )
        )

        helpers.await_queue_edit(openreview_client, edit_id=reviewer_note_edit['id'])
        helpers.await_queue_edit(openreview_client, edit_id=ac_note_edit['id'])
        helpers.await_queue_edit(openreview_client, edit_id=sac_note_edit['id'])

        august_reviewer_edges = {o['id']['tail']: [j['weight'] for j in o['values']] for o in pc_client_v2.get_grouped_edges(invitation=f"{august_venue.get_reviewers_id()}/-/Custom_Max_Papers", groupby='tail', select='weight')}
        august_ac_edges = {o['id']['tail']: [j['weight'] for j in o['values']] for o in pc_client_v2.get_grouped_edges(invitation=f"{august_venue.get_area_chairs_id()}/-/Custom_Max_Papers", groupby='tail', select='weight')}
        august_sac_edges = {o['id']['tail']: [j['weight'] for j in o['values']] for o in pc_client_v2.get_grouped_edges(invitation=f"{august_venue.get_senior_area_chairs_id()}/-/Custom_Max_Papers", groupby='tail', select='weight')}
        assert '~Reviewer_ARROne1' in august_reviewer_edges
        assert len(august_reviewer_edges['~Reviewer_ARROne1']) == 1 and set(august_reviewer_edges['~Reviewer_ARROne1']) == {5}
        assert '~AC_ARRTwo1' in august_ac_edges
        assert len(august_ac_edges['~AC_ARRTwo1']) == 1 and set(august_ac_edges['~AC_ARRTwo1']) == {7}
        assert '~SAC_ARRTwo1' in august_sac_edges
        assert len(august_sac_edges['~SAC_ARRTwo1']) == 1 and set(august_sac_edges['~SAC_ARRTwo1']) == {11}

        # Test deleting
        reviewer_note_edit = reviewer_client.post_note_edit(
                invitation=f'{august_venue.get_reviewers_id()}/-/{max_load_name}',
                signatures=['~Reviewer_ARROne1'],
                note=openreview.api.Note(
                    id = reviewer_note_edit['note']['id'],
                    ddate = openreview.tools.datetime_millis(now),
                    content = {
                        'maximum_load': { 'value': '5' },
                        'maximum_load_resubmission': { 'value': 'No' }
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
                    'maximum_load': { 'value': '7' },
                    'maximum_load_resubmission': { 'value': 'Yes' }
                }
            )
        )
        sac_note_edit = sac_client.post_note_edit(
            invitation=f'{august_venue.get_senior_area_chairs_id()}/-/{max_load_name}',
            signatures=['~SAC_ARRTwo1'],
            note=openreview.api.Note(
                id = sac_note_edit['note']['id'],
                ddate = openreview.tools.datetime_millis(now),
                content = {
                    'maximum_load': { 'value': '11' },
                    'maximum_load_resubmission': { 'value': 'Yes' }
                }
            )
        )

        helpers.await_queue_edit(openreview_client, edit_id=reviewer_note_edit['id'])
        helpers.await_queue_edit(openreview_client, edit_id=ac_note_edit['id'])
        helpers.await_queue_edit(openreview_client, edit_id=sac_note_edit['id'])

        august_reviewer_edges = {o['id']['tail']: [j['weight'] for j in o['values']] for o in pc_client_v2.get_grouped_edges(invitation=f"{august_venue.get_reviewers_id()}/-/Custom_Max_Papers", groupby='tail', select='weight')}
        august_ac_edges = {o['id']['tail']: [j['weight'] for j in o['values']] for o in pc_client_v2.get_grouped_edges(invitation=f"{august_venue.get_area_chairs_id()}/-/Custom_Max_Papers", groupby='tail', select='weight')}
        august_sac_edges = {o['id']['tail']: [j['weight'] for j in o['values']] for o in pc_client_v2.get_grouped_edges(invitation=f"{august_venue.get_senior_area_chairs_id()}/-/Custom_Max_Papers", groupby='tail', select='weight')}
        assert '~Reviewer_ARROne1' not in august_reviewer_edges
        assert '~AC_ARRTwo1' not in august_ac_edges
        assert '~SAC_ARRTwo1' not in august_sac_edges

        # Set data for resubmission unavailability
        reviewer_five_client = openreview.api.OpenReviewClient(username = 'reviewer5@aclrollingreview.com', password=helpers.strong_password)
        ac_three_client = openreview.api.OpenReviewClient(username = 'ac3@aclrollingreview.com', password=helpers.strong_password)

        reviewer_five_client.post_note_edit(
            invitation=f'{august_venue.get_reviewers_id()}/-/{max_load_name}',
            signatures=['~Reviewer_ARRFive1'],
            note=openreview.api.Note(
                content = {
                    'maximum_load': { 'value': '0' },
                    'maximum_load_resubmission': { 'value': 'Yes' }
                }
            )
        ) 
        ac_three_client.post_note_edit(
            invitation=f'{august_venue.get_area_chairs_id()}/-/{max_load_name}',
            signatures=['~AC_ARRThree1'],
            note=openreview.api.Note(
                content = {
                    'maximum_load': { 'value': '0' },
                    'maximum_load_resubmission': { 'value': 'Yes' }
                }
            )
        )
        
    def test_reviewer_tasks(self, client, openreview_client, helpers):
        reviewer_client = openreview.api.OpenReviewClient(username = 'reviewer1@aclrollingreview.com', password=helpers.strong_password)
        ac_client = openreview.api.OpenReviewClient(username = 'ac1@aclrollingreview.com', password=helpers.strong_password)

        # Recognition tasks
        recognition_edit = reviewer_client.post_note_edit(
            invitation='aclweb.org/ACL/ARR/2023/August/Reviewers/-/Recognition_Request',
            signatures=['~Reviewer_ARROne1'],
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
            signatures=['~Reviewer_ARROne1'],
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

    def test_submissions(self, client, openreview_client, helpers, test_client):

        test_client = openreview.api.OpenReviewClient(token=test_client.token)

        domains = ['umass.edu', 'amazon.com', 'fb.com', 'cs.umass.edu', 'google.com', 'mit.edu', 'deepmind.com', 'co.ux', 'apple.com', 'nvidia.com']
        for i in range(1,102):
            note = openreview.api.Note(
                content = {
                    'title': { 'value': 'Paper title ' + str(i) },
                    'abstract': { 'value': 'This is an abstract ' + str(i) },
                    'authorids': { 'value': ['~SomeFirstName_User1', 'peter@mail.com', 'andrew@' + domains[i % 10]] },
                    'authors': { 'value': ['SomeFirstName User', 'Peter SomeLastName', 'Andrew Mc'] },
                    'TLDR': { 'value': 'This is a tldr ' + str(i) },
                    'pdf': {'value': '/pdf/' + 'p' * 40 +'.pdf' },
                    'responsible_NLP_research': {'value': '/pdf/' + 'p' * 40 +'.pdf' },
                    'paper_type': { 'value': 'short' },
                    'research_area': { 'value': 'Generation' },
                    'previous_URL': { 'value': 'https://arxiv.org/abs/1234.56789' },
                    'previous_PDF': {'value': '/pdf/' + 'p' * 40 +'.pdf' },
                    'response_PDF': {'value': '/pdf/' + 'p' * 40 +'.pdf' },
                    'reassignment_request_action_editor': {'value': 'No, I want the same action editor from our previous submission and understand that a new action editor may be assigned if the previous one is unavailable' },
                    'reassignment_request_reviewers': { 'value': 'Yes, I want a different set of reviewers' },
                    'justification_for_not_keeping_action_editor_or_reviewers': { 'value': 'We would like to keep the same reviewers and action editor because they are experts in the field and have provided valuable feedback on our previous submission.' },
                    'software': {'value': '/pdf/' + 'p' * 40 +'.zip' },
                    'data': {'value': '/pdf/' + 'p' * 40 +'.zip' },
                    'preprint': { 'value': 'yes' if i % 2 == 0 else 'no' },
                    'existing_preprints': { 'value': 'existing_preprints' },
                    'preferred_venue': { 'value': 'ACL Conference' },
                    'consent_to_share_data': { 'value': 'yes' },
                    'consent_to_review': { 'value': 'yes' }
                }
            )
            if i == 1 or i == 101:
                note.content['authors']['value'].append('SAC ARROne')
                note.content['authorids']['value'].append('~SAC_ARROne1')

            test_client.post_note_edit(invitation='aclweb.org/ACL/ARR/2023/August/-/Submission',
                signatures=['~SomeFirstName_User1'],
                note=note)

        helpers.await_queue_edit(openreview_client, invitation='aclweb.org/ACL/ARR/2023/August/-/Submission', count=101)

        submissions = openreview_client.get_notes(invitation='aclweb.org/ACL/ARR/2023/August/-/Submission', sort='number:asc')
        assert len(submissions) == 101
        assert ['aclweb.org/ACL/ARR/2023/August', '~SomeFirstName_User1', 'peter@mail.com', 'andrew@amazon.com', '~SAC_ARROne1'] == submissions[0].readers
        assert ['~SomeFirstName_User1', 'peter@mail.com', 'andrew@amazon.com', '~SAC_ARROne1'] == submissions[0].content['authorids']['value']

        authors_group = openreview_client.get_group(id='aclweb.org/ACL/ARR/2023/August/Authors')

        for i in range(1,102):
            assert f'aclweb.org/ACL/ARR/2023/August/Submission{i}/Authors' in authors_group.members

    def test_post_submission(self, client, openreview_client, helpers):

        pc_client=openreview.Client(username='pc@aclrollingreview.org', password=helpers.strong_password)
        request_form=pc_client.get_notes(invitation='openreview.net/Support/-/Request_Form')[1]

        ## close the submissions
        now = datetime.datetime.utcnow()
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
                'hide_fields': hide_fields
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

        # Open comments
        now = datetime.datetime.utcnow()

        pc_client.post_note(
            openreview.Note(
                content={
                    'comment_start_date': (now - datetime.timedelta(days=1)).strftime('%Y/%m/%d %H:%M:%S'),
                    'comment_end_date': (now + datetime.timedelta(days=365)).strftime('%Y/%m/%d %H:%M:%S')
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
        helpers.await_queue_edit(openreview_client, 'aclweb.org/ACL/ARR/2023/August/-/Official_Comment-0-1', count=1)

        pc_client_v2=openreview.api.OpenReviewClient(username='pc@aclrollingreview.org', password=helpers.strong_password)
        submission_invitation = pc_client_v2.get_invitation('aclweb.org/ACL/ARR/2023/August/-/Submission')
        assert submission_invitation.expdate < openreview.tools.datetime_millis(now)

        assert len(pc_client_v2.get_all_invitations(invitation='aclweb.org/ACL/ARR/2023/August/-/Withdrawal')) == 101
        assert len(pc_client_v2.get_all_invitations(invitation='aclweb.org/ACL/ARR/2023/August/-/Desk_Rejection')) == 101
        assert pc_client_v2.get_invitation('aclweb.org/ACL/ARR/2023/August/-/PC_Revision')

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
        assert submissions[0].content['consent_to_review']['readers'] == ['aclweb.org/ACL/ARR/2023/August', 'aclweb.org/ACL/ARR/2023/August/Submission1/Authors']
        assert submissions[0].content['consent_to_share_data']['readers'] == ['aclweb.org/ACL/ARR/2023/August', 'aclweb.org/ACL/ARR/2023/August/Submission1/Authors']
        assert 'readers' not in submissions[0].content['software']
        assert 'readers' not in submissions[0].content['responsible_NLP_research']
        assert 'readers' not in submissions[0].content['previous_URL']
        assert 'readers' not in submissions[0].content['previous_PDF']
        assert 'readers' not in submissions[0].content['response_PDF']
        assert 'readers' not in submissions[0].content['reassignment_request_action_editor']
        assert 'readers' not in submissions[0].content['reassignment_request_reviewers']
        assert 'readers' not in submissions[0].content['justification_for_not_keeping_action_editor_or_reviewers']

        ## release preprint submissions
        pc_client.post_note(
            openreview.Note(
                content={
                    'preprint_release_submission_date': (openreview.tools.datetime.datetime.utcnow() + datetime.timedelta(seconds=3)).strftime('%Y/%m/%d %H:%M:%S')
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

        helpers.await_queue_edit(openreview_client, 'aclweb.org/ACL/ARR/2023/August/-/ARR_Scheduler-1-0', count=1)

        helpers.await_queue_edit(openreview_client, 'aclweb.org/ACL/ARR/2023/August/-/Preprint_Release_Submission-0-1', count=2)

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
        assert submissions[0].content['consent_to_review']['readers'] == ['aclweb.org/ACL/ARR/2023/August', 'aclweb.org/ACL/ARR/2023/August/Submission1/Authors']
        assert submissions[0].content['consent_to_share_data']['readers'] == ['aclweb.org/ACL/ARR/2023/August', 'aclweb.org/ACL/ARR/2023/August/Submission1/Authors']
        assert 'readers' not in submissions[0].content['software']
        assert 'readers' not in submissions[0].content['responsible_NLP_research']
        assert 'readers' not in submissions[0].content['previous_URL']
        assert 'readers' not in submissions[0].content['previous_PDF']
        assert 'readers' not in submissions[0].content['response_PDF']
        assert 'readers' not in submissions[0].content['reassignment_request_action_editor']
        assert 'readers' not in submissions[0].content['reassignment_request_reviewers']
        assert 'readers' not in submissions[0].content['justification_for_not_keeping_action_editor_or_reviewers']


        assert submissions[1].readers == ['everyone']
        assert submissions[1].content['TLDR']['readers'] == ['aclweb.org/ACL/ARR/2023/August', 'aclweb.org/ACL/ARR/2023/August/Submission2/Authors']
        assert submissions[1].content['preprint']['readers'] == ['aclweb.org/ACL/ARR/2023/August', 'aclweb.org/ACL/ARR/2023/August/Submission2/Authors']
        assert submissions[1].content['existing_preprints']['readers'] == ['aclweb.org/ACL/ARR/2023/August', 'aclweb.org/ACL/ARR/2023/August/Submission2/Authors']
        assert submissions[1].content['preferred_venue']['readers'] == ['aclweb.org/ACL/ARR/2023/August', 'aclweb.org/ACL/ARR/2023/August/Submission2/Authors']
        assert submissions[1].content['consent_to_review']['readers'] == ['aclweb.org/ACL/ARR/2023/August', 'aclweb.org/ACL/ARR/2023/August/Submission2/Authors']
        assert submissions[1].content['consent_to_share_data']['readers'] == ['aclweb.org/ACL/ARR/2023/August', 'aclweb.org/ACL/ARR/2023/August/Submission2/Authors']
        assert submissions[1].content['software']['readers'] == [
            "aclweb.org/ACL/ARR/2023/August/Program_Chairs",
            "aclweb.org/ACL/ARR/2023/August/Submission2/Senior_Area_Chairs",
            "aclweb.org/ACL/ARR/2023/August/Submission2/Area_Chairs",
            "aclweb.org/ACL/ARR/2023/August/Submission2/Reviewers",
            "aclweb.org/ACL/ARR/2023/August/Submission2/Authors"
        ]
        assert submissions[1].content['data']['readers'] == [
            "aclweb.org/ACL/ARR/2023/August/Program_Chairs",
            "aclweb.org/ACL/ARR/2023/August/Submission2/Senior_Area_Chairs",
            "aclweb.org/ACL/ARR/2023/August/Submission2/Area_Chairs",
            "aclweb.org/ACL/ARR/2023/August/Submission2/Reviewers",
            "aclweb.org/ACL/ARR/2023/August/Submission2/Authors"
        ]
        assert submissions[1].content['responsible_NLP_research']['readers'] == [
            "aclweb.org/ACL/ARR/2023/August/Program_Chairs",
            "aclweb.org/ACL/ARR/2023/August/Submission2/Senior_Area_Chairs",
            "aclweb.org/ACL/ARR/2023/August/Submission2/Area_Chairs",
            "aclweb.org/ACL/ARR/2023/August/Submission2/Reviewers",
            "aclweb.org/ACL/ARR/2023/August/Submission2/Authors"
        ]
        assert submissions[1].content['previous_URL']['readers'] == [
            "aclweb.org/ACL/ARR/2023/August/Program_Chairs",
            "aclweb.org/ACL/ARR/2023/August/Submission2/Senior_Area_Chairs",
            "aclweb.org/ACL/ARR/2023/August/Submission2/Area_Chairs",
            "aclweb.org/ACL/ARR/2023/August/Submission2/Reviewers",
            "aclweb.org/ACL/ARR/2023/August/Submission2/Authors"
        ]
        assert submissions[1].content['previous_PDF']['readers'] == [
            "aclweb.org/ACL/ARR/2023/August/Program_Chairs",
            "aclweb.org/ACL/ARR/2023/August/Submission2/Senior_Area_Chairs",
            "aclweb.org/ACL/ARR/2023/August/Submission2/Area_Chairs",
            "aclweb.org/ACL/ARR/2023/August/Submission2/Reviewers",
            "aclweb.org/ACL/ARR/2023/August/Submission2/Authors"
        ]
        assert submissions[1].content['response_PDF']['readers'] == [
            "aclweb.org/ACL/ARR/2023/August/Program_Chairs",
            "aclweb.org/ACL/ARR/2023/August/Submission2/Senior_Area_Chairs",
            "aclweb.org/ACL/ARR/2023/August/Submission2/Area_Chairs",
            "aclweb.org/ACL/ARR/2023/August/Submission2/Reviewers",
            "aclweb.org/ACL/ARR/2023/August/Submission2/Authors"
        ]  
        assert submissions[1].content['reassignment_request_action_editor']['readers'] == [
            "aclweb.org/ACL/ARR/2023/August/Program_Chairs",
            "aclweb.org/ACL/ARR/2023/August/Submission2/Senior_Area_Chairs",
            "aclweb.org/ACL/ARR/2023/August/Submission2/Area_Chairs",
            "aclweb.org/ACL/ARR/2023/August/Submission2/Reviewers",
            "aclweb.org/ACL/ARR/2023/August/Submission2/Authors"
        ]  
        assert submissions[1].content['reassignment_request_reviewers']['readers'] == [
            "aclweb.org/ACL/ARR/2023/August/Program_Chairs",
            "aclweb.org/ACL/ARR/2023/August/Submission2/Senior_Area_Chairs",
            "aclweb.org/ACL/ARR/2023/August/Submission2/Area_Chairs",
            "aclweb.org/ACL/ARR/2023/August/Submission2/Reviewers",
            "aclweb.org/ACL/ARR/2023/August/Submission2/Authors"
        ]  
        assert submissions[1].content['justification_for_not_keeping_action_editor_or_reviewers']['readers'] == [
            "aclweb.org/ACL/ARR/2023/August/Program_Chairs",
            "aclweb.org/ACL/ARR/2023/August/Submission2/Senior_Area_Chairs",
            "aclweb.org/ACL/ARR/2023/August/Submission2/Area_Chairs",
            "aclweb.org/ACL/ARR/2023/August/Submission2/Reviewers",
            "aclweb.org/ACL/ARR/2023/August/Submission2/Authors"
        ]

        # Post comment as PCs to all submissions
        for submission in submissions:
            pc_client_v2.post_note_edit(
                invitation=f"aclweb.org/ACL/ARR/2023/August/Submission{submission.number}/-/Official_Comment",
                writers=['aclweb.org/ACL/ARR/2023/August'],
                signatures=['aclweb.org/ACL/ARR/2023/August/Program_Chairs'],
                note=openreview.api.Note(
                    replyto=submission.id,
                    readers=[
                        'aclweb.org/ACL/ARR/2023/August/Program_Chairs',
                        f'aclweb.org/ACL/ARR/2023/August/Submission{submission.number}/Senior_Area_Chairs',
                        f'aclweb.org/ACL/ARR/2023/August/Submission{submission.number}/Area_Chairs'
                    ],
                    content={
                        "comment": { "value": "This is a comment"}
                    }
                )
            )


    def test_setup_matching(self, client, openreview_client, helpers, test_client, request_page, selenium):

        pc_client=openreview.Client(username='pc@aclrollingreview.org', password=helpers.strong_password)
        pc_client_v2=openreview.api.OpenReviewClient(username='pc@aclrollingreview.org', password=helpers.strong_password)
        request_form=pc_client.get_notes(invitation='openreview.net/Support/-/Request_Form')[1]
        august_venue = openreview.helpers.get_conference(client, request_form.id, 'openreview.net/Support')
        test_client = openreview.api.OpenReviewClient(token=test_client.token)

        # Create review stages
        now = datetime.datetime.utcnow()
        due_date = now + datetime.timedelta(days=3)
        pc_client.post_note(
            openreview.Note(
                content={
                    'ae_checklist_due_date': (now).strftime('%Y/%m/%d %H:%M:%S'),
                    'ae_checklist_exp_date': (due_date).strftime('%Y/%m/%d %H:%M:%S'),
                    'reviewer_checklist_due_date': (now).strftime('%Y/%m/%d %H:%M:%S'),
                    'reviewer_checklist_exp_date': (due_date).strftime('%Y/%m/%d %H:%M:%S'),
                    'reviewing_start_date': (now).strftime('%Y/%m/%d %H:%M:%S'),
                    'reviewing_due_date': (due_date).strftime('%Y/%m/%d %H:%M:%S'),
                    'reviewing_exp_date': (due_date).strftime('%Y/%m/%d %H:%M:%S'),
                    'metareviewing_start_date': (now).strftime('%Y/%m/%d %H:%M:%S'),
                    'metareviewing_due_date': (due_date).strftime('%Y/%m/%d %H:%M:%S'),
                    'metareviewing_exp_date': (due_date).strftime('%Y/%m/%d %H:%M:%S'),
                    'ethics_reviewing_start_date': (now).strftime('%Y/%m/%d %H:%M:%S'),
                    'ethics_reviewing_due_date': (due_date).strftime('%Y/%m/%d %H:%M:%S'),
                    'ethics_reviewing_exp_date': (due_date).strftime('%Y/%m/%d %H:%M:%S'),
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

        with open(os.path.join(os.path.dirname(__file__), 'data/rev_scores_venue.csv'), 'w') as file_handle:
            writer = csv.writer(file_handle)
            for submission in submissions:
                for sac in openreview_client.get_group('aclweb.org/ACL/ARR/2023/August/Senior_Area_Chairs').members:
                    writer.writerow([submission.id, sac, round(random.random(), 2)])

        affinity_scores_url = client.put_attachment(os.path.join(os.path.dirname(__file__), 'data/rev_scores_venue.csv'), f'openreview.net/Support/-/Request{request_form.number}/ARR_Configuration', 'sae_affinity_scores')

        pc_client.post_note(
            openreview.Note(
                content={
                    'setup_sae_matching_date': (openreview.tools.datetime.datetime.utcnow() + datetime.timedelta(seconds=3)).strftime('%Y/%m/%d %H:%M:%S'),
                    'sae_affinity_scores': affinity_scores_url
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

        helpers.await_queue_edit(openreview_client, 'aclweb.org/ACL/ARR/2023/August/-/ARR_Scheduler-2-0', count=1)

        assert openreview_client.get_invitation('aclweb.org/ACL/ARR/2023/August/Senior_Area_Chairs/-/Conflict')
        assert openreview_client.get_invitation('aclweb.org/ACL/ARR/2023/August/Senior_Area_Chairs/-/Affinity_Score')
        assert openreview_client.get_invitation('aclweb.org/ACL/ARR/2023/August/Senior_Area_Chairs/-/Proposed_Assignment')
        assert openreview_client.get_invitation('aclweb.org/ACL/ARR/2023/August/Senior_Area_Chairs/-/Assignment')

        affinity_score_count =  openreview_client.get_edges_count(invitation='aclweb.org/ACL/ARR/2023/August/Senior_Area_Chairs/-/Affinity_Score')
        assert affinity_score_count == 101 * 2 ## submissions * ACs

        assert openreview_client.get_edges_count(invitation='aclweb.org/ACL/ARR/2023/August/Senior_Area_Chairs/-/Conflict') == 103 # Share publication with co-author of test user + SAC2 shares institution with submission 1 and 101 via SAC1

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

        assert openreview_client.get_edges_count(invitation='aclweb.org/ACL/ARR/2023/August/Reviewers/-/Conflict') == 12 # All 6 reviewers will conflict with submissions 1/101 because of domain of SAC

        affinity_scores =  openreview_client.get_grouped_edges(invitation='aclweb.org/ACL/ARR/2023/August/Reviewers/-/Affinity_Score', groupby='id')
        assert affinity_scores
        assert len(affinity_scores) == 101 * 6 ## submissions * reviewers

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
        for reviewer in reviewers:
            for edge in openreview_client.get_all_edges(invitation='aclweb.org/ACL/ARR/2023/August/Reviewers/-/Affinity_Score', tail=reviewer):
                reviewer_edges_to_post.append(
                    openreview.api.Edge(
                        invitation='aclweb.org/ACL/ARR/2023/August/Reviewers/-/Aggregate_Score',
                        readers=edge.readers,
                        writers=edge.writers,
                        signatures=edge.signatures,
                        nonreaders=edge.nonreaders,
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
                ac_edges_to_post.append(
                    openreview.api.Edge(
                        invitation='aclweb.org/ACL/ARR/2023/August/Area_Chairs/-/Aggregate_Score',
                        readers=edge.readers,
                        writers=edge.writers,
                        signatures=edge.signatures,
                        nonreaders=edge.nonreaders,
                        head=edge.head,
                        tail=edge.tail,
                        weight=edge.weight,
                        label='ae-assignments'
                    )
                )
        openreview.tools.post_bulk_edges(openreview_client, ac_edges_to_post)

        assert openreview_client.get_edges_count(invitation='aclweb.org/ACL/ARR/2023/August/Area_Chairs/-/Aggregate_Score', label='ae-assignments') == 101 * 3
        assert openreview_client.get_edges_count(invitation='aclweb.org/ACL/ARR/2023/August/Reviewers/-/Aggregate_Score', label='reviewer-assignments') == 101 * 6


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
        now = datetime.datetime.utcnow()
        start_date = now - datetime.timedelta(days=2)
        due_date = now + datetime.timedelta(days=3)
        pc_client.post_note(
            openreview.Note(
                content={
                    'reviewing_start_date': (now).strftime('%Y/%m/%d %H:%M:%S'),
                    'reviewing_due_date': (due_date).strftime('%Y/%m/%d %H:%M:%S'),
                    'reviewing_exp_date': (due_date).strftime('%Y/%m/%d %H:%M:%S'),
                    'metareviewing_start_date': (now).strftime('%Y/%m/%d %H:%M:%S'),
                    'metareviewing_due_date': (due_date).strftime('%Y/%m/%d %H:%M:%S'),
                    'metareviewing_exp_date': (due_date).strftime('%Y/%m/%d %H:%M:%S'),
                    'ethics_reviewing_start_date': (now).strftime('%Y/%m/%d %H:%M:%S'),
                    'ethics_reviewing_due_date': (due_date).strftime('%Y/%m/%d %H:%M:%S'),
                    'ethics_reviewing_exp_date': (due_date).strftime('%Y/%m/%d %H:%M:%S'),
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

        # Remove resubmission information from all but submissions 2 and 3
        for submission in submissions:
            if submission.number in [2, 3]:
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
                        'reassignment_request_action_editor': { 'delete': True },
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

        reviewer_client_1.post_note_edit(
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
                    "overall_assessment": { "value": 1 },
                    "best_paper": { "value": "No" },
                    "ethical_concerns": { "value": "N/A" },
                    "reproducibility": { "value": 1 },
                    "datasets": { "value": 1 },
                    "software": { "value": 1 },
                    "Knowledge_of_or_educated_guess_at_author_identity": {"value": "No"},
                    "Knowledge_of_paper": {"value": "After the review process started"},
                    "Knowledge_of_paper_source": {"value": ["A research talk"]},
                    "impact_of_knowledge_of_paper": {"value": "A lot"},
                    "reviewer_certification": {"value": "A Name"}
                }
            )
        )

        reviewer_client_2.post_note_edit(
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
                    "overall_assessment": { "value": 1 },
                    "best_paper": { "value": "No" },
                    "ethical_concerns": { "value": "N/A" },
                    "reproducibility": { "value": 1 },
                    "datasets": { "value": 1 },
                    "software": { "value": 1 },
                    "Knowledge_of_or_educated_guess_at_author_identity": {"value": "No"},
                    "Knowledge_of_paper": {"value": "After the review process started"},
                    "Knowledge_of_paper_source": {"value": ["A research talk"]},
                    "impact_of_knowledge_of_paper": {"value": "A lot"},
                    "reviewer_certification": {"value": "A Name"}
                }
            )
        )

        reviewer_client_5.post_note_edit(
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
                    "overall_assessment": { "value": 1 },
                    "best_paper": { "value": "No" },
                    "ethical_concerns": { "value": "N/A" },
                    "reproducibility": { "value": 1 },
                    "datasets": { "value": 1 },
                    "software": { "value": 1 },
                    "Knowledge_of_or_educated_guess_at_author_identity": {"value": "No"},
                    "Knowledge_of_paper": {"value": "After the review process started"},
                    "Knowledge_of_paper_source": {"value": ["A research talk"]},
                    "impact_of_knowledge_of_paper": {"value": "A lot"},
                    "reviewer_certification": {"value": "A Name"}
                }
            )
        )

        ac_client_3.post_note_edit(
            invitation='aclweb.org/ACL/ARR/2023/June/Submission2/-/Meta_Review',
            signatures=[anon_group_id_ac],
            note=openreview.api.Note(
                content={
                    "metareview": { "value": 'a metareview' },
                    "summary_of_reasons_to_publish": { "value": 'some summary' },
                    "summary_of_suggested_revisions": { "value": 'some strengths' },
                    "best_paper_ae": { "value": 'Yes' },
                    "overall_assessment": { "value": 1 },
                    "ethical_concerns": { "value": "There are no concerns with this submission" },
                    "author_identity_guess": { "value": 1 },
                    "needs_ethics_review": {'value': 'No'}
                }
            )
        )

        helpers.await_queue(openreview_client)

        # Point August submissions idx 1 and 2 to June papers and set submission reassignment requests
        # Let 1 = same and 2 = not same
        review_edit_1 = openreview_client.post_note_edit(
            invitation=august_venue.get_meta_invitation_id(),
            readers=[august_venue.id],
            writers=[august_venue.id],
            signatures=[august_venue.id],
            note=openreview.api.Note(
                id=submissions[1].id,
                content={
                    'previous_URL': {'value': f'http://localhost:3030/forum?id={june_submissions[1].id}'},
                    'reassignment_request_action_editor': {'value': 'No, I want the same action editor from our previous submission and understand that a new action editor may be assigned if the previous one is unavailable' },
                    'reassignment_request_reviewers': { 'value': 'No, I want the same set of reviewers from our previous submission and understand that new reviewers may be assigned if any of the previous ones are unavailable' },
                }
            )
        )
        review_edit_2 = openreview_client.post_note_edit(
            invitation=august_venue.get_meta_invitation_id(),
            readers=[august_venue.id],
            writers=[august_venue.id],
            signatures=[august_venue.id],
            note=openreview.api.Note(
                id=submissions[2].id,
                content={
                    'previous_URL': {'value': f'http://localhost:3030/forum?id={june_submissions[2].id}'},
                    'reassignment_request_action_editor': {'value': 'Yes, I want a different action editor for our submission' },
                    'reassignment_request_reviewers': { 'value': 'Yes, I want a different set of reviewers' },
                }
            )
        )

        helpers.await_queue()
        helpers.await_queue(openreview_client)

        # Call the stage
        pc_client.post_note(
            openreview.Note(
                content={
                    'setup_tracks_and_reassignment_date': (openreview.tools.datetime.datetime.utcnow() + datetime.timedelta(seconds=3)).strftime('%Y/%m/%d %H:%M:%S')
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

        helpers.await_queue_edit(openreview_client, 'aclweb.org/ACL/ARR/2023/August/-/ARR_Scheduler-3-0', count=1)
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
        assert 'aclweb.org/ACL/ARR/2023/August/Submission2/Reviewers/Submitted' in pc_client_v2.get_group('aclweb.org/ACL/ARR/2023/June/Submission2/Reviewers/Submitted').members

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
        assert len(track_edges['~Reviewer_ARROne1']) == 101
        assert '~Reviewer_ARRTwo1' in track_edges
        assert len(track_edges['~Reviewer_ARRTwo1']) == 100 ## One less edge posted

        track_edges = {
            g['id']['tail'] : g['values']
            for g in pc_client_v2.get_grouped_edges(invitation=f'aclweb.org/ACL/ARR/2023/August/Area_Chairs/-/Research_Area', select='head,id,weight', groupby='tail')
        }
        assert len(track_edges.keys()) == 1
        assert '~AC_ARROne1' in track_edges
        assert len(track_edges['~AC_ARROne1']) == 101

        track_edges = {
            g['id']['tail'] : g['values']
            for g in pc_client_v2.get_grouped_edges(invitation=f'aclweb.org/ACL/ARR/2023/August/Senior_Area_Chairs/-/Research_Area', select='head,id,weight', groupby='tail')
        }
        assert len(track_edges.keys()) == 1
        assert '~SAC_ARROne1' in track_edges
        assert len(track_edges['~SAC_ARROne1']) == 101

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
            for g in pc_client_v2.get_grouped_edges(invitation=f'aclweb.org/ACL/ARR/2023/August/Reviewers/-/Available', select='head,id,weight,label', groupby='tail')
        }
        assert set(available_edges.keys()) == {'~Reviewer_ARRFive1'}
        assert available_edges['~Reviewer_ARRFive1']['label'] == 'For resubmissions only'

        available_edges = {
            g['id']['tail'] : g['values'][0]
            for g in pc_client_v2.get_grouped_edges(invitation=f'aclweb.org/ACL/ARR/2023/August/Area_Chairs/-/Available', select='head,id,weight,label', groupby='tail')
        }
        assert set(available_edges.keys()) == {'~AC_ARRThree1'}
        assert available_edges['~AC_ARRThree1']['label'] == 'For resubmissions only'

        # Check integrity of custom max papers
        cmp_edges = {
            g['id']['tail'] : g['values'][0]
            for g in pc_client_v2.get_grouped_edges(invitation=f'aclweb.org/ACL/ARR/2023/August/Reviewers/-/Custom_Max_Papers', select='head,id,weight,label', groupby='tail')
        }
        load_notes = pc_client_v2.get_all_notes(invitation='aclweb.org/ACL/ARR/2023/August/Reviewers/-/Max_Load_And_Unavailability_Request')
        for note in load_notes:
            if note.signatures[0] == '~Reviewer_ARRFive1':
                assert cmp_edges[note.signatures[0]]['weight'] == int(note.content['maximum_load']['value']) + 1
                continue
            assert cmp_edges[note.signatures[0]]['weight'] == int(note.content['maximum_load']['value'])

        cmp_edges = {
            g['id']['tail'] : g['values'][0]
            for g in pc_client_v2.get_grouped_edges(invitation=f'aclweb.org/ACL/ARR/2023/August/Area_Chairs/-/Custom_Max_Papers', select='head,id,weight,label', groupby='tail')
        }
        load_notes = pc_client_v2.get_all_notes(invitation='aclweb.org/ACL/ARR/2023/August/Area_Chairs/-/Max_Load_And_Unavailability_Request')
        for note in load_notes:
            if note.signatures[0] == '~AC_ARRThree1':
                assert cmp_edges[note.signatures[0]]['weight'] == int(note.content['maximum_load']['value']) + 1
                continue
            assert cmp_edges[note.signatures[0]]['weight'] == int(note.content['maximum_load']['value'])
            

    def test_sae_ae_assignments(self, client, openreview_client, helpers, test_client, request_page, selenium):

        pc_client=openreview.Client(username='pc@aclrollingreview.org', password=helpers.strong_password)
        pc_client_v2=openreview.api.OpenReviewClient(username='pc@aclrollingreview.org', password=helpers.strong_password)
        request_form=pc_client.get_notes(invitation='openreview.net/Support/-/Request_Form')[1]
        august_venue = openreview.helpers.get_conference(client, request_form.id, 'openreview.net/Support')
        test_client = openreview.api.OpenReviewClient(token=test_client.token)

        submissions = pc_client_v2.get_notes(invitation='aclweb.org/ACL/ARR/2023/August/-/Submission', sort='number:asc')

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

        pc_client.post_note(
            openreview.Note(
                content={
                    'setup_sae_ae_assignment_date': (openreview.tools.datetime.datetime.utcnow() + datetime.timedelta(seconds=3)).strftime('%Y/%m/%d %H:%M:%S')
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

        helpers.await_queue_edit(openreview_client, 'aclweb.org/ACL/ARR/2023/August/-/ARR_Scheduler-4-0', count=1)

        assert openreview_client.get_group('aclweb.org/ACL/ARR/2023/August/Emergency_Area_Chairs')
        assert openreview_client.get_invitation('aclweb.org/ACL/ARR/2023/August/Area_Chairs/-/Assignment').content['sync_sac_id']['value'] == ''

        # Remove an AC and replace
        sac_client = openreview.api.OpenReviewClient(username = 'sac2@aclrollingreview.com', password=helpers.strong_password)
        assert len(sac_client.get_edges(invitation = 'aclweb.org/ACL/ARR/2023/August/Area_Chairs/-/Assignment', head=submissions[1].id, tail='~AC_ARRTwo1')) == 1
        ac_edge = sac_client.get_edges(invitation = 'aclweb.org/ACL/ARR/2023/August/Area_Chairs/-/Assignment', head=submissions[1].id, tail='~AC_ARRTwo1')[0]
        ac_edge.ddate = openreview.tools.datetime_millis(openreview.tools.datetime.datetime.utcnow())
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

    def test_checklists(self, client, openreview_client, helpers, test_client, request_page, selenium):
        pc_client=openreview.Client(username='pc@aclrollingreview.org', password=helpers.strong_password)
        pc_client_v2=openreview.api.OpenReviewClient(username='pc@aclrollingreview.org', password=helpers.strong_password)
        request_form=pc_client.get_notes(invitation='openreview.net/Support/-/Request_Form')[1]
        venue = openreview.helpers.get_conference(client, request_form.id, 'openreview.net/Support')
        submissions = pc_client_v2.get_notes(invitation='aclweb.org/ACL/ARR/2023/August/-/Submission', sort='number:asc')
        violation_fields = ['appropriateness', 'formatting', 'length', 'anonymity', 'responsible_checklist', 'limitations'] # TODO: move to domain or somewhere?
        format_field = {
            'appropriateness': 'Appropriateness',
            'formatting': 'Formatting',
            'length': 'Length',
            'anonymity': 'Anonymity',
            'responsible_checklist': 'Responsible Checklist',
            'limitations': 'Limitations'
        }
        only_required_fields = ['number_of_assignments', 'diversity']

        default_fields = {field: True for field in violation_fields + only_required_fields}
        default_fields['need_ethics_review'] = False
        test_submission = submissions[1]

        reviewer_client = openreview.api.OpenReviewClient(username = 'reviewer1@aclrollingreview.com', password=helpers.strong_password)
        reviewer_two_client = openreview.api.OpenReviewClient(username = 'reviewer2@aclrollingreview.com', password=helpers.strong_password)
        ac_client = openreview.api.OpenReviewClient(username = 'ac1@aclrollingreview.com', password=helpers.strong_password)

        # Add reviewers to submission 2
        openreview_client.add_members_to_group(venue.get_reviewers_id(number=2), ['~Reviewer_ARROne1', '~Reviewer_ARRTwo1'])

        test_data_templates = {
            'aclweb.org/ACL/ARR/2023/August/Reviewers': {
                'checklist_invitation': 'aclweb.org/ACL/ARR/2023/August/Submission2/-/Reviewer_Checklist',
                'user': reviewer_client.get_groups(prefix='aclweb.org/ACL/ARR/2023/August/Submission2/Reviewer_', signatory='~Reviewer_ARROne1')[0].id,
                'client': reviewer_client
            },
            'aclweb.org/ACL/ARR/2023/August/Area_Chairs': {
                'checklist_invitation': 'aclweb.org/ACL/ARR/2023/August/Submission2/-/Action_Editor_Checklist',
                'user': ac_client.get_groups(prefix='aclweb.org/ACL/ARR/2023/August/Submission2/Area_Chair_', signatory='~AC_ARROne1')[0].id,
                'client': ac_client
            }
        }

        def post_checklist(chk_client, chk_inv, user, tested_field=None, ddate=None, existing_note=None, override_fields=None):
            def generate_checklist_content(tested_field=None):
                ret_content = {field: {'value':'Yes'} if default_fields[field] else {'value':'No'} for field in default_fields}
                ret_content['potential_violation_justification'] = {'value': 'There are no violations with this submission'}
                ret_content['ethics_review_justification'] = {'value': 'N/A (I answered no to the previous question)'}

                if tested_field:
                    ret_content[tested_field] = {'value':'Yes'} if not default_fields[tested_field] else {'value':'No'}
                    ret_content['ethics_review_justification'] = {'value': 'There is an issue'}
                    ret_content['potential_violation_justification'] = {'value': 'There are violations with this submission'}

                if 'Reviewer' in chk_inv:
                    for field in only_required_fields:
                        del ret_content[field]

                return ret_content
            
            if not existing_note:
                content = generate_checklist_content(tested_field=tested_field)
            if existing_note:
                content = existing_note['content']
                if tested_field:
                    content[tested_field] = {'value':'Yes'} if not default_fields[tested_field] else {'value':'No'}
                    content['ethics_review_justification'] = {'value': 'There is an issue'}
                    content['potential_violation_justification'] = {'value': 'There are violations with this submission'}

            if override_fields:
                for field in override_fields.keys():
                    content[field] = override_fields[field]
            
            chk_edit = chk_client.post_note_edit(
                invitation=chk_inv,
                signatures=[user],
                note=openreview.api.Note(
                    id=None if not existing_note else existing_note['id'],
                    content = content,
                    ddate=ddate
                )
            )

            helpers.await_queue(openreview_client)

            return chk_edit, pc_client_v2.get_note(test_submission.id)
        
        def now():
            return openreview.tools.datetime_millis(datetime.datetime.utcnow())

        checklist_inv = test_data_templates[venue.get_reviewers_id()]['checklist_invitation']
        user = test_data_templates[venue.get_reviewers_id()]['user']
        user_client = test_data_templates[venue.get_reviewers_id()]['client']

        # Test checklist pre-process
        force_justifications = {
                'potential_violation_justification': {'value': 'There are no violations with this submission'},
                'ethics_review_justification': {'value': 'N/A (I answered no to the previous question)'}
        }
        with pytest.raises(openreview.OpenReviewException, match=r'You have indicated that this submission needs an ethics review. Please enter a brief justification for your flagging.'):
            post_checklist(user_client, checklist_inv, user, tested_field='need_ethics_review', override_fields=force_justifications)
        for field in violation_fields:
            with pytest.raises(openreview.OpenReviewException, match=rf'You have indicated a potential violation with the following fields: {format_field[field]}. Please enter a brief explanation under \"Potential Violation Justification\"'):
                post_checklist(user_client, checklist_inv, user, tested_field=field, override_fields=force_justifications)
                
        # Post checklist with no ethics flag and no violation field - check that flags are not there
        edit, test_submission = post_checklist(user_client, checklist_inv, user)
        assert 'flagged_for_ethics_review' not in test_submission.content
        assert 'flagged_for_desk_reject_verification' not in test_submission.content
        _, test_submission = post_checklist(user_client, checklist_inv, user, ddate=now(), existing_note=edit['note'])

        # Post checklist with no ethics flag and a violation field - check for DSV flag
        edit, test_submission = post_checklist(user_client, checklist_inv, user, tested_field=violation_fields[0])
        assert 'flagged_for_ethics_review' not in test_submission.content
        assert 'flagged_for_desk_reject_verification' in test_submission.content
        assert test_submission.content['flagged_for_desk_reject_verification']['value']
        assert openreview_client.get_invitation('aclweb.org/ACL/ARR/2023/August/Submission2/-/Desk_Reject_Verification').expdate > now()

        # Delete checklist - check DSV flag is False, invitation is expired
        _, test_submission = post_checklist(user_client, checklist_inv, user, ddate=now(), existing_note=edit['note'])
        assert 'flagged_for_ethics_review' not in test_submission.content
        assert 'flagged_for_desk_reject_verification' in test_submission.content
        assert not test_submission.content['flagged_for_desk_reject_verification']['value']
        assert openreview_client.get_invitation('aclweb.org/ACL/ARR/2023/August/Submission2/-/Desk_Reject_Verification').expdate < now()

        # Re-post with no ethics flag and a violation field - check DSV flag is True
        violation_edit, test_submission = post_checklist(user_client, checklist_inv, user, tested_field=violation_fields[1])
        assert 'flagged_for_ethics_review' not in test_submission.content
        assert 'flagged_for_desk_reject_verification' in test_submission.content
        assert test_submission.content['flagged_for_desk_reject_verification']['value']
        assert openreview_client.get_invitation('aclweb.org/ACL/ARR/2023/August/Submission2/-/Desk_Reject_Verification').expdate > now()

        # Edit with no ethics flag and no violation field - check DSV flag is False
        violation_edit['note']['content'][violation_fields[1]]['value'] = 'Yes'
        _, test_submission = post_checklist(user_client, checklist_inv, user, existing_note=violation_edit['note'])
        assert 'flagged_for_ethics_review' not in test_submission.content
        assert 'flagged_for_desk_reject_verification' in test_submission.content
        assert not test_submission.content['flagged_for_desk_reject_verification']['value']
        assert openreview_client.get_invitation('aclweb.org/ACL/ARR/2023/August/Submission2/-/Desk_Reject_Verification').expdate < now()

        # Edit with ethics flag and no violation field - check DSV flag is false and ethics flag exists and is True
        _, test_submission = post_checklist(user_client, checklist_inv, user, tested_field='need_ethics_review', existing_note=violation_edit['note'])
        assert 'flagged_for_ethics_review' in test_submission.content
        assert 'flagged_for_desk_reject_verification' in test_submission.content
        assert not test_submission.content['flagged_for_desk_reject_verification']['value']
        assert test_submission.content['flagged_for_ethics_review']['value']
        assert openreview_client.get_invitation('aclweb.org/ACL/ARR/2023/August/Submission2/-/Desk_Reject_Verification').expdate < now()

        # Delete checklist - check both flags False
        _, test_submission = post_checklist(user_client, checklist_inv, user, ddate=now(), existing_note=violation_edit['note'])
        assert 'flagged_for_ethics_review' in test_submission.content
        assert 'flagged_for_desk_reject_verification' in test_submission.content
        assert not test_submission.content['flagged_for_desk_reject_verification']['value']
        assert not test_submission.content['flagged_for_ethics_review']['value']

        # Re-post with no flag - check both flags false
        reviewer_edit, test_submission = post_checklist(user_client, checklist_inv, user)
        assert 'flagged_for_ethics_review' in test_submission.content
        assert 'flagged_for_desk_reject_verification' in test_submission.content
        assert not test_submission.content['flagged_for_desk_reject_verification']['value']
        assert not test_submission.content['flagged_for_ethics_review']['value']
        assert openreview_client.get_invitation('aclweb.org/ACL/ARR/2023/August/Submission2/-/Desk_Reject_Verification').expdate < now()


        # Test checklists for AEs
        checklist_inv = test_data_templates[venue.get_area_chairs_id()]['checklist_invitation']
        user = test_data_templates[venue.get_area_chairs_id()]['user']
        user_client = test_data_templates[venue.get_area_chairs_id()]['client']
        # Post checklist with no ethics flag and no violation field - check that flags are not there
        edit, test_submission = post_checklist(user_client, checklist_inv, user)
        assert not test_submission.content['flagged_for_desk_reject_verification']['value']
        assert not test_submission.content['flagged_for_ethics_review']['value']
        _, test_submission = post_checklist(user_client, checklist_inv, user, ddate=now(), existing_note=edit['note'])

        # Post checklist with no ethics flag and a violation field - check for DSV flag
        edit, test_submission = post_checklist(user_client, checklist_inv, user, tested_field=violation_fields[2])
        assert test_submission.content['flagged_for_desk_reject_verification']['value']
        assert not test_submission.content['flagged_for_ethics_review']['value']
        assert openreview_client.get_invitation('aclweb.org/ACL/ARR/2023/August/Submission2/-/Desk_Reject_Verification').expdate > now()

        # Delete checklist - check DSV flag is False, invitation is expired
        _, test_submission = post_checklist(user_client, checklist_inv, user, ddate=now(), existing_note=edit['note'])
        assert not test_submission.content['flagged_for_desk_reject_verification']['value']
        assert not test_submission.content['flagged_for_ethics_review']['value']
        assert openreview_client.get_invitation('aclweb.org/ACL/ARR/2023/August/Submission2/-/Desk_Reject_Verification').expdate < now()

        # Re-post with no ethics flag and a violation field - check DSV flag is True
        violation_edit, test_submission = post_checklist(user_client, checklist_inv, user, tested_field=violation_fields[3])
        assert test_submission.content['flagged_for_desk_reject_verification']['value']
        assert not test_submission.content['flagged_for_ethics_review']['value']
        assert openreview_client.get_invitation('aclweb.org/ACL/ARR/2023/August/Submission2/-/Desk_Reject_Verification').expdate > now()

        # Edit with no ethics flag and no violation field - check DSV flag is False
        violation_edit['note']['content'][violation_fields[3]]['value'] = 'Yes'
        _, test_submission = post_checklist(user_client, checklist_inv, user, existing_note=violation_edit['note'])
        assert not test_submission.content['flagged_for_desk_reject_verification']['value']
        assert not test_submission.content['flagged_for_ethics_review']['value']
        assert openreview_client.get_invitation('aclweb.org/ACL/ARR/2023/August/Submission2/-/Desk_Reject_Verification').expdate < now()

        # Edit with ethics flag and no violation field - check DSV flag is false and ethics flag exists and is True
        _, test_submission = post_checklist(user_client, checklist_inv, user, tested_field='need_ethics_review', existing_note=violation_edit['note'])
        assert not test_submission.content['flagged_for_desk_reject_verification']['value']
        assert test_submission.content['flagged_for_ethics_review']['value']
        assert openreview_client.get_invitation('aclweb.org/ACL/ARR/2023/August/Submission2/-/Desk_Reject_Verification').expdate < now()

        # Delete checklist - check both flags False
        _, test_submission = post_checklist(user_client, checklist_inv, user, ddate=now(), existing_note=violation_edit['note'])
        assert not test_submission.content['flagged_for_desk_reject_verification']['value']
        assert not test_submission.content['flagged_for_ethics_review']['value']

        # Re-post with no flag - check both flags false
        ae_edit, test_submission = post_checklist(user_client, checklist_inv, user)
        assert not test_submission.content['flagged_for_desk_reject_verification']['value']
        assert not test_submission.content['flagged_for_ethics_review']['value']
        assert openreview_client.get_invitation('aclweb.org/ACL/ARR/2023/August/Submission2/-/Desk_Reject_Verification').expdate < now()

        # Test un_flagged consensus
        reviewer_inv = test_data_templates[venue.get_reviewers_id()]['checklist_invitation']
        reviewer = test_data_templates[venue.get_reviewers_id()]['user']
        reviewer_client = test_data_templates[venue.get_reviewers_id()]['client']

        # First set both flags, then unflag 1, then unflag both
        ae_edit, test_submission = post_checklist(user_client, checklist_inv, user, tested_field='need_ethics_review', existing_note=ae_edit['note'])
        reviewer_edit, test_submission = post_checklist(reviewer_client, reviewer_inv, reviewer, tested_field='need_ethics_review', existing_note=reviewer_edit['note'])
        assert not test_submission.content['flagged_for_desk_reject_verification']['value']
        assert test_submission.content['flagged_for_ethics_review']['value']

        reviewer_edit, test_submission = post_checklist(reviewer_client, reviewer_inv, reviewer, existing_note=reviewer_edit['note'], override_fields={'need_ethics_review': {'value': 'No'}})
        assert not test_submission.content['flagged_for_desk_reject_verification']['value']
        assert test_submission.content['flagged_for_ethics_review']['value']

        ae_edit, test_submission = post_checklist(user_client, checklist_inv, user, existing_note=ae_edit['note'], override_fields={'need_ethics_review': {'value': 'No'}})
        assert not test_submission.content['flagged_for_desk_reject_verification']['value']
        assert not test_submission.content['flagged_for_ethics_review']['value']

        # Repeat for desk reject verification
        ae_edit, test_submission = post_checklist(user_client, checklist_inv, user, tested_field=violation_fields[4], existing_note=ae_edit['note'])
        reviewer_edit, test_submission = post_checklist(reviewer_client, reviewer_inv, reviewer, tested_field=violation_fields[4], existing_note=reviewer_edit['note'])
        assert test_submission.content['flagged_for_desk_reject_verification']['value']
        assert not test_submission.content['flagged_for_ethics_review']['value']

        reviewer_edit, test_submission = post_checklist(reviewer_client, reviewer_inv, reviewer, existing_note=reviewer_edit['note'], override_fields={violation_fields[4]: {'value': 'Yes'}})
        assert test_submission.content['flagged_for_desk_reject_verification']['value']
        assert not test_submission.content['flagged_for_ethics_review']['value']

        ae_edit, test_submission = post_checklist(user_client, checklist_inv, user, existing_note=ae_edit['note'], override_fields={violation_fields[4]: {'value': 'Yes'}})
        assert not test_submission.content['flagged_for_desk_reject_verification']['value']
        assert not test_submission.content['flagged_for_ethics_review']['value']

        # Check readers
        ae_chk = openreview_client.get_note(ae_edit['note']['id'])
        ae_chk_inv = openreview_client.get_invitation('aclweb.org/ACL/ARR/2023/August/Submission2/-/Action_Editor_Checklist')
        rev_chk = openreview_client.get_note(reviewer_edit['note']['id'])
        rev_chk_inv = openreview_client.get_invitation('aclweb.org/ACL/ARR/2023/August/Submission2/-/Reviewer_Checklist')

        assert 'aclweb.org/ACL/ARR/2023/August/Submission2/Ethics_Reviewers' in ae_chk.readers
        assert 'aclweb.org/ACL/ARR/2023/August/Submission2/Ethics_Reviewers' in rev_chk.readers
        assert 'aclweb.org/ACL/ARR/2023/August/Submission2/Ethics_Reviewers' in ae_chk_inv.edit['readers']
        assert 'aclweb.org/ACL/ARR/2023/August/Submission2/Ethics_Reviewers' in ae_chk_inv.edit['note']['readers']
        assert 'aclweb.org/ACL/ARR/2023/August/Submission2/Ethics_Reviewers' in rev_chk_inv.edit['readers']
        assert 'aclweb.org/ACL/ARR/2023/August/Submission2/Ethics_Reviewers' in rev_chk_inv.edit['note']['readers']

    def test_official_review_flagging(self, client, openreview_client, helpers, test_client, request_page, selenium):
        pc_client=openreview.Client(username='pc@aclrollingreview.org', password=helpers.strong_password)
        pc_client_v2=openreview.api.OpenReviewClient(username='pc@aclrollingreview.org', password=helpers.strong_password)
        request_form=pc_client.get_notes(invitation='openreview.net/Support/-/Request_Form')[1]
        venue = openreview.helpers.get_conference(client, request_form.id, 'openreview.net/Support')
        submissions = pc_client_v2.get_notes(invitation='aclweb.org/ACL/ARR/2023/August/-/Submission', sort='number:asc')
        violation_fields = ['Knowledge_of_or_educated_guess_at_author_identity']

        default_fields = {}
        default_fields['Knowledge_of_or_educated_guess_at_author_identity'] = False
        default_fields['needs_ethics_review'] = False
        test_submission = submissions[2]

        openreview_client.add_members_to_group(venue.get_reviewers_id(number=3), ['~Reviewer_ARROne1'])

        reviewer_client = openreview.api.OpenReviewClient(username = 'reviewer1@aclrollingreview.com', password=helpers.strong_password)

        test_data_templates = {
            'aclweb.org/ACL/ARR/2023/August/Reviewers': {
                'review_invitation': 'aclweb.org/ACL/ARR/2023/August/Submission3/-/Official_Review',
                'user': reviewer_client.get_groups(prefix='aclweb.org/ACL/ARR/2023/August/Submission3/Reviewer_', signatory='~Reviewer_ARROne1')[0].id,
                'client': reviewer_client
            }
        }

        def post_official_review(rev_client, rev_inv, user, tested_field=None, ddate=None, existing_note=None, override_fields=None):
            def generate_official_review_content(tested_field=None):
                ret_content = {
                    "confidence": { "value": 5 },
                    "paper_summary": { "value": 'some summary' },
                    "summary_of_strengths": { "value": 'some strengths' },
                    "summary_of_weaknesses": { "value": 'some weaknesses' },
                    "comments_suggestions_and_typos": { "value": 'some comments' },
                    "soundness": { "value": 1 },
                    "overall_assessment": { "value": 1 },
                    "best_paper": { "value": "No" },
                    "ethical_concerns": { "value": "N/A" },
                    "reproducibility": { "value": 1 },
                    "datasets": { "value": 1 },
                    "software": { "value": 1 },
                    "needs_ethics_review": {'value': 'No'},
                    "Knowledge_of_or_educated_guess_at_author_identity": {"value": "No"},
                    "Knowledge_of_paper": {"value": "After the review process started"},
                    "Knowledge_of_paper_source": {"value": ["A research talk"]},
                    "impact_of_knowledge_of_paper": {"value": "A lot"},
                    "reviewer_certification": {"value": "A Name"}
                }
                ret_content['ethical_concerns'] = {'value': 'There are no concerns with this submission'}

                if tested_field:
                    ret_content[tested_field] = {'value':'Yes'}
                    ret_content['ethical_concerns'] = {'value': 'There are concerns with this submission'}

                return ret_content
            
            if not existing_note:
                content = generate_official_review_content(tested_field=tested_field)
            if existing_note:
                content = existing_note['content']
                if tested_field:
                    content[tested_field] = {'value':'Yes'}
                    content['ethical_concerns'] = {'value': 'There are concerns with this submission'}

            if override_fields:
                for field in override_fields.keys():
                    content[field] = override_fields[field]
            
            rev_edit = rev_client.post_note_edit(
                invitation=rev_inv,
                signatures=[user],
                note=openreview.api.Note(
                    id=None if not existing_note else existing_note['id'],
                    content = content,
                    ddate=ddate
                )
            )

            helpers.await_queue(openreview_client)

            return rev_edit, pc_client_v2.get_note(test_submission.id)
        
        def now():
            return openreview.tools.datetime_millis(datetime.datetime.utcnow())

        review_inv = test_data_templates[venue.get_reviewers_id()]['review_invitation']
        user = test_data_templates[venue.get_reviewers_id()]['user']
        user_client = test_data_templates[venue.get_reviewers_id()]['client']

        # Test checklist pre-process
        force_justifications = {
                'ethical_concerns': {'value': 'There are no concerns with this submission'}
        }
        with pytest.raises(openreview.OpenReviewException, match=r'You have indicated that this submission needs an ethics review. Please enter a brief justification for your flagging.'):
            post_official_review(user_client, review_inv, user, tested_field='needs_ethics_review', override_fields=force_justifications)
                
        # Post checklist with no ethics flag and no violation field - check that flags are not there
        edit, test_submission = post_official_review(user_client, review_inv, user)
        assert 'flagged_for_ethics_review' not in test_submission.content
        assert 'flagged_for_desk_reject_verification' not in test_submission.content
        _, test_submission = post_official_review(user_client, review_inv, user, ddate=now(), existing_note=edit['note'])

        # Check for existence of rebuttal invitation
        assert user_client.get_invitation('aclweb.org/ACL/ARR/2023/August/Submission3/Official_Review1/-/Consent')
        consent_edit = user_client.post_note_edit(
                invitation='aclweb.org/ACL/ARR/2023/August/Submission3/Official_Review1/-/Consent',
                signatures=[user],
                note=openreview.api.Note(
                    content = {
                        'consent': {'value': 'Yes, I consent to donating anonymous metadata of my review for research.'}
                    }
                )
            )

        # Post checklist with no ethics flag and a violation field - check for DSV flag
        edit, test_submission = post_official_review(user_client, review_inv, user, tested_field=violation_fields[0])
        assert 'flagged_for_ethics_review' not in test_submission.content
        assert 'flagged_for_desk_reject_verification' in test_submission.content
        assert test_submission.content['flagged_for_desk_reject_verification']['value']
        assert openreview_client.get_invitation('aclweb.org/ACL/ARR/2023/August/Submission3/-/Desk_Reject_Verification').expdate > now()

        # Delete checklist - check DSV flag is False, invitation is expired
        _, test_submission = post_official_review(user_client, review_inv, user, ddate=now(), existing_note=edit['note'])
        assert 'flagged_for_ethics_review' not in test_submission.content
        assert 'flagged_for_desk_reject_verification' in test_submission.content
        assert not test_submission.content['flagged_for_desk_reject_verification']['value']
        assert openreview_client.get_invitation('aclweb.org/ACL/ARR/2023/August/Submission3/-/Desk_Reject_Verification').expdate < now()

        # Re-post with no ethics flag and a violation field - check DSV flag is True
        violation_edit, test_submission = post_official_review(user_client, review_inv, user, tested_field=violation_fields[0])
        assert 'flagged_for_ethics_review' not in test_submission.content
        assert 'flagged_for_desk_reject_verification' in test_submission.content
        assert test_submission.content['flagged_for_desk_reject_verification']['value']
        assert openreview_client.get_invitation('aclweb.org/ACL/ARR/2023/August/Submission3/-/Desk_Reject_Verification').expdate > now()

        # Edit with no ethics flag and no violation field - check DSV flag is False
        violation_edit['note']['content'][violation_fields[0]]['value'] = 'No'
        _, test_submission = post_official_review(user_client, review_inv, user, existing_note=violation_edit['note'])
        assert 'flagged_for_ethics_review' not in test_submission.content
        assert 'flagged_for_desk_reject_verification' in test_submission.content
        assert not test_submission.content['flagged_for_desk_reject_verification']['value']
        assert openreview_client.get_invitation('aclweb.org/ACL/ARR/2023/August/Submission3/-/Desk_Reject_Verification').expdate < now()

        # Edit with ethics flag and no violation field - check DSV flag is false and ethics flag exists and is True
        _, test_submission = post_official_review(user_client, review_inv, user, tested_field='needs_ethics_review', existing_note=violation_edit['note'])
        assert 'flagged_for_ethics_review' in test_submission.content
        assert 'flagged_for_desk_reject_verification' in test_submission.content
        assert not test_submission.content['flagged_for_desk_reject_verification']['value']
        assert test_submission.content['flagged_for_ethics_review']['value']
        assert openreview_client.get_invitation('aclweb.org/ACL/ARR/2023/August/Submission3/-/Desk_Reject_Verification').expdate < now()

        # Delete checklist - check both flags False
        _, test_submission = post_official_review(user_client, review_inv, user, ddate=now(), existing_note=violation_edit['note'])
        assert 'flagged_for_ethics_review' in test_submission.content
        assert 'flagged_for_desk_reject_verification' in test_submission.content
        assert not test_submission.content['flagged_for_desk_reject_verification']['value']
        assert not test_submission.content['flagged_for_ethics_review']['value']

        # Re-post with no flag - check both flags false
        reviewer_edit, test_submission = post_official_review(user_client, review_inv, user)
        assert 'flagged_for_ethics_review' in test_submission.content
        assert 'flagged_for_desk_reject_verification' in test_submission.content
        assert not test_submission.content['flagged_for_desk_reject_verification']['value']
        assert not test_submission.content['flagged_for_ethics_review']['value']
        assert openreview_client.get_invitation('aclweb.org/ACL/ARR/2023/August/Submission3/-/Desk_Reject_Verification').expdate < now()

        # Make reviews public
        pc_client.post_note(
            openreview.Note(
                content={
                    'setup_review_release_date': (openreview.tools.datetime.datetime.utcnow() + datetime.timedelta(seconds=3)).strftime('%Y/%m/%d %H:%M:%S')
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

        time.sleep(5)

        helpers.await_queue_edit(openreview_client, 'aclweb.org/ACL/ARR/2023/August/-/ARR_Scheduler-5-0', count=1)
        helpers.await_queue_edit(openreview_client, 'aclweb.org/ACL/ARR/2023/August/-/Official_Review-0-1', count=4)

        review = openreview_client.get_note(reviewer_edit['note']['id'])
        assert 'aclweb.org/ACL/ARR/2023/August/Submission3/Authors' in review.readers

    def test_author_response(self, client, openreview_client, helpers, test_client, request_page, selenium):
        pc_client=openreview.Client(username='pc@aclrollingreview.org', password=helpers.strong_password)
        pc_client_v2=openreview.api.OpenReviewClient(username='pc@aclrollingreview.org', password=helpers.strong_password)
        request_form=pc_client.get_notes(invitation='openreview.net/Support/-/Request_Form')[1]
        venue = openreview.helpers.get_conference(client, request_form.id, 'openreview.net/Support')
        submissions = venue.get_submissions()

        # Open author response
        pc_client.post_note(
            openreview.Note(
                content={
                    'setup_author_response_date': (datetime.datetime.utcnow() + datetime.timedelta(seconds=3)).strftime('%Y/%m/%d %H:%M:%S')
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
        time.sleep(3)
        helpers.await_queue_edit(openreview_client, 'aclweb.org/ACL/ARR/2023/August/-/ARR_Scheduler-7-0', count=1)
        helpers.await_queue_edit(openreview_client, 'aclweb.org/ACL/ARR/2023/August/-/Official_Comment-0-1', count=3)

        for s in submissions:
            comment_invitees = openreview_client.get_invitation(f"aclweb.org/ACL/ARR/2023/August/Submission{s.number}/-/Official_Comment").invitees
            comment_readers = openreview_client.get_invitation(f"aclweb.org/ACL/ARR/2023/August/Submission{s.number}/-/Official_Comment").edit['note']['readers']['param']['enum']

            assert f"aclweb.org/ACL/ARR/2023/August/Submission{s.number}/Authors" in comment_invitees
            assert f"aclweb.org/ACL/ARR/2023/August/Submission{s.number}/Authors" in comment_readers

        # Close author response
        pc_client.post_note(
            openreview.Note(
                content={
                    'close_author_response_date': (datetime.datetime.utcnow() + datetime.timedelta(seconds=6)).strftime('%Y/%m/%d %H:%M:%S')
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
        time.sleep(6)
        helpers.await_queue_edit(openreview_client, 'aclweb.org/ACL/ARR/2023/August/-/ARR_Scheduler-8-0', count=1)
        helpers.await_queue_edit(openreview_client, 'aclweb.org/ACL/ARR/2023/August/-/Official_Comment-0-1', count=4)

        for s in submissions:
            comment_invitees = openreview_client.get_invitation(f"aclweb.org/ACL/ARR/2023/August/Submission{s.number}/-/Official_Comment").invitees
            comment_readers = openreview_client.get_invitation(f"aclweb.org/ACL/ARR/2023/August/Submission{s.number}/-/Official_Comment").edit['note']['readers']['param']['enum']

            assert f"aclweb.org/ACL/ARR/2023/August/Submission{s.number}/Authors" not in comment_invitees
            assert f"aclweb.org/ACL/ARR/2023/August/Submission{s.number}/Authors" not in comment_readers

    def test_changing_deadlines(self, client, openreview_client, helpers, test_client, request_page, selenium):
        pc_client=openreview.Client(username='pc@aclrollingreview.org', password=helpers.strong_password)
        pc_client_v2=openreview.api.OpenReviewClient(username='pc@aclrollingreview.org', password=helpers.strong_password)
        request_form_note=pc_client.get_notes(invitation='openreview.net/Support/-/Request_Form')[1]
        venue = openreview.helpers.get_conference(client, request_form_note.id, 'openreview.net/Support')
        registration_name = 'Registration'
        max_load_name = 'Max_Load_And_Unavailability_Request'

        now = datetime.datetime.utcnow()
        due_date = now + datetime.timedelta(days=5)

        # Original due dates were at +3, now at +5
        reviewer_max_load_due_date = openreview_client.get_invitation(f'aclweb.org/ACL/ARR/2023/August/Reviewers/-/{max_load_name}').duedate
        ac_max_load_due_date = openreview_client.get_invitation(f'aclweb.org/ACL/ARR/2023/August/Area_Chairs/-/{max_load_name}').duedate
        sac_max_load_due_date = openreview_client.get_invitation(f'aclweb.org/ACL/ARR/2023/August/Senior_Area_Chairs/-/{max_load_name}').duedate

        reviewer_max_load_exp_date = openreview_client.get_invitation(f'aclweb.org/ACL/ARR/2023/August/Reviewers/-/{max_load_name}').expdate
        ac_max_load_exp_date = openreview_client.get_invitation(f'aclweb.org/ACL/ARR/2023/August/Area_Chairs/-/{max_load_name}').expdate
        sac_max_load_exp_date = openreview_client.get_invitation(f'aclweb.org/ACL/ARR/2023/August/Senior_Area_Chairs/-/{max_load_name}').expdate

        reviewer_checklist_due_date = openreview_client.get_invitation(f'aclweb.org/ACL/ARR/2023/August/-/Reviewer_Checklist').edit['invitation']['duedate']
        reviewer_checklist_exp_date = openreview_client.get_invitation(f'aclweb.org/ACL/ARR/2023/August/-/Reviewer_Checklist').edit['invitation']['expdate']

        ae_checklist_due_date = openreview_client.get_invitation(f'aclweb.org/ACL/ARR/2023/August/-/Action_Editor_Checklist').edit['invitation']['duedate']
        ae_checklist_exp_date = openreview_client.get_invitation(f'aclweb.org/ACL/ARR/2023/August/-/Action_Editor_Checklist').edit['invitation']['expdate']

        reviewing_due_date = openreview_client.get_invitation(f'aclweb.org/ACL/ARR/2023/August/-/Official_Review').edit['invitation']['duedate']
        reviewing_exp_date = openreview_client.get_invitation(f'aclweb.org/ACL/ARR/2023/August/-/Official_Review').edit['invitation']['expdate']

        meta_reviewing_due_date = openreview_client.get_invitation(f'aclweb.org/ACL/ARR/2023/August/-/Meta_Review').edit['invitation']['duedate']
        meta_reviewing_exp_date = openreview_client.get_invitation(f'aclweb.org/ACL/ARR/2023/August/-/Meta_Review').edit['invitation']['expdate']

        pc_client.post_note(
            openreview.Note(
                content={
                    'form_expiration_date': (due_date).strftime('%Y/%m/%d %H:%M:%S'),
                    'author_consent_due_date': (due_date).strftime('%Y/%m/%d %H:%M:%S'),
                    'maximum_load_due_date': (due_date).strftime('%Y/%m/%d %H:%M:%S'),
                    'maximum_load_exp_date': (due_date).strftime('%Y/%m/%d %H:%M:%S'),
                    'ae_checklist_due_date': (due_date).strftime('%Y/%m/%d %H:%M:%S'),
                    'ae_checklist_exp_date': (due_date).strftime('%Y/%m/%d %H:%M:%S'),
                    'reviewer_checklist_due_date': (due_date).strftime('%Y/%m/%d %H:%M:%S'),
                    'reviewer_checklist_exp_date': (due_date).strftime('%Y/%m/%d %H:%M:%S'),
                    'reviewing_start_date': (now).strftime('%Y/%m/%d %H:%M:%S'),
                    'reviewing_due_date': (due_date).strftime('%Y/%m/%d %H:%M:%S'),
                    'reviewing_exp_date': (due_date).strftime('%Y/%m/%d %H:%M:%S'),
                    'metareviewing_start_date': (now).strftime('%Y/%m/%d %H:%M:%S'),
                    'metareviewing_due_date': (due_date).strftime('%Y/%m/%d %H:%M:%S'),
                    'metareviewing_exp_date': (due_date).strftime('%Y/%m/%d %H:%M:%S'),
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

        assert openreview_client.get_invitation(f'aclweb.org/ACL/ARR/2023/August/Reviewers/-/{max_load_name}').duedate > reviewer_max_load_due_date
        assert openreview_client.get_invitation(f'aclweb.org/ACL/ARR/2023/August/Reviewers/-/{max_load_name}').expdate > reviewer_max_load_exp_date
        
        assert openreview_client.get_invitation(f'aclweb.org/ACL/ARR/2023/August/Area_Chairs/-/{max_load_name}').duedate > ac_max_load_due_date
        assert openreview_client.get_invitation(f'aclweb.org/ACL/ARR/2023/August/Area_Chairs/-/{max_load_name}').expdate > ac_max_load_exp_date

        assert openreview_client.get_invitation(f'aclweb.org/ACL/ARR/2023/August/Senior_Area_Chairs/-/{max_load_name}').duedate > sac_max_load_due_date
        assert openreview_client.get_invitation(f'aclweb.org/ACL/ARR/2023/August/Senior_Area_Chairs/-/{max_load_name}').expdate > sac_max_load_exp_date

        assert openreview_client.get_invitation(f'aclweb.org/ACL/ARR/2023/August/-/Reviewer_Checklist').edit['invitation']['duedate'] > reviewer_checklist_due_date
        assert openreview_client.get_invitation(f'aclweb.org/ACL/ARR/2023/August/-/Reviewer_Checklist').edit['invitation']['expdate'] > reviewer_checklist_exp_date

        assert openreview_client.get_invitation(f'aclweb.org/ACL/ARR/2023/August/-/Action_Editor_Checklist').edit['invitation']['duedate'] > ae_checklist_due_date
        assert openreview_client.get_invitation(f'aclweb.org/ACL/ARR/2023/August/-/Action_Editor_Checklist').edit['invitation']['expdate'] > ae_checklist_exp_date
        
        assert openreview_client.get_invitation(f'aclweb.org/ACL/ARR/2023/August/-/Official_Review').edit['invitation']['duedate'] > reviewing_due_date
        assert openreview_client.get_invitation(f'aclweb.org/ACL/ARR/2023/August/-/Official_Review').edit['invitation']['expdate'] > reviewing_exp_date

        assert openreview_client.get_invitation(f'aclweb.org/ACL/ARR/2023/August/-/Meta_Review').edit['invitation']['duedate'] > meta_reviewing_due_date
        assert openreview_client.get_invitation(f'aclweb.org/ACL/ARR/2023/August/-/Meta_Review').edit['invitation']['expdate'] > meta_reviewing_exp_date

    def test_meta_review_flagging_and_ethics_review(self, client, openreview_client, helpers, test_client, request_page, selenium):
        pc_client=openreview.Client(username='pc@aclrollingreview.org', password=helpers.strong_password)
        pc_client_v2=openreview.api.OpenReviewClient(username='pc@aclrollingreview.org', password=helpers.strong_password)
        request_form=pc_client.get_notes(invitation='openreview.net/Support/-/Request_Form')[1]
        venue = openreview.helpers.get_conference(client, request_form.id, 'openreview.net/Support')
        submissions = pc_client_v2.get_notes(invitation='aclweb.org/ACL/ARR/2023/August/-/Submission', sort='number:asc')
        violation_fields = ['author_identity_guess']

        default_fields = {}
        default_fields['author_identity_guess'] = 1
        default_fields['needs_ethics_review'] = False
        test_submission = submissions[3]

        openreview_client.add_members_to_group(venue.get_area_chairs_id(number=4), ['~AC_ARROne1'])
        openreview_client.add_members_to_group(venue.get_ethics_reviewers_id(number=4), ['~EthicsReviewer_ARROne1'])

        ac_client = openreview.api.OpenReviewClient(username = 'ac1@aclrollingreview.com', password=helpers.strong_password)
        ethics_client = openreview.api.OpenReviewClient(username = 'reviewerethics@aclrollingreview.com', password=helpers.strong_password)

        test_data_templates = {
            'aclweb.org/ACL/ARR/2023/August/Area_Chairs': {
                'review_invitation': 'aclweb.org/ACL/ARR/2023/August/Submission4/-/Meta_Review',
                'user': ac_client.get_groups(prefix='aclweb.org/ACL/ARR/2023/August/Submission4/Area_Chair_', signatory='~AC_ARROne1')[0].id,
                'client': ac_client
            }
        }

        def post_meta_review(rev_client, rev_inv, user, tested_field=None, ddate=None, existing_note=None, override_fields=None):
            def generate_official_review_content(tested_field=None):
                ret_content = {
                    "metareview": { "value": 'a metareview' },
                    "summary_of_reasons_to_publish": { "value": 'some summary' },
                    "summary_of_suggested_revisions": { "value": 'some strengths' },
                    "best_paper_ae": { "value": 'Yes' },
                    "overall_assessment": { "value": 1 },
                    "ethical_concerns": { "value": "There are no concerns with this submission" },
                    "author_identity_guess": { "value": 1 },
                    "needs_ethics_review": {'value': 'No'}
                }
                ret_content['ethical_concerns'] = {'value': 'There are no concerns with this submission'}

                if tested_field:
                    ret_content[tested_field] = {'value':'Yes'}
                    ret_content['ethical_concerns'] = {'value': 'There are concerns with this submission'}

                return ret_content
            
            if not existing_note:
                content = generate_official_review_content(tested_field=tested_field)
            if existing_note:
                content = existing_note['content']
                if tested_field:
                    content[tested_field] = {'value':'Yes'}
                    content['ethical_concerns'] = {'value': 'There are concerns with this submission'}

            if override_fields:
                for field in override_fields.keys():
                    content[field] = override_fields[field]
            
            rev_edit = rev_client.post_note_edit(
                invitation=rev_inv,
                signatures=[user],
                note=openreview.api.Note(
                    id=None if not existing_note else existing_note['id'],
                    content = content,
                    ddate=ddate
                )
            )

            helpers.await_queue(openreview_client)

            return rev_edit, pc_client_v2.get_note(test_submission.id)
        
        def now():
            return openreview.tools.datetime_millis(datetime.datetime.utcnow())

        review_inv = test_data_templates[venue.get_area_chairs_id()]['review_invitation']
        user = test_data_templates[venue.get_area_chairs_id()]['user']
        user_client = test_data_templates[venue.get_area_chairs_id()]['client']

        # Test checklist pre-process
        force_justifications = {
                'ethical_concerns': {'value': 'There are no concerns with this submission'}
        }
        with pytest.raises(openreview.OpenReviewException, match=r'You have indicated that this submission needs an ethics review. Please enter a brief justification for your flagging.'):
            post_meta_review(user_client, review_inv, user, tested_field='needs_ethics_review', override_fields=force_justifications)
                
        # Post checklist with no ethics flag and no violation field - check that flags are not there
        edit, test_submission = post_meta_review(user_client, review_inv, user)
        assert 'flagged_for_ethics_review' not in test_submission.content
        assert 'flagged_for_desk_reject_verification' not in test_submission.content
        _, test_submission = post_meta_review(user_client, review_inv, user, ddate=now(), existing_note=edit['note'])

        # Post checklist with no ethics flag and a violation field - check for DSV flag
        edit, test_submission = post_meta_review(user_client, review_inv, user, override_fields={'author_identity_guess': {'value': 5}})
        assert 'flagged_for_ethics_review' not in test_submission.content
        assert 'flagged_for_desk_reject_verification' in test_submission.content
        assert test_submission.content['flagged_for_desk_reject_verification']['value']
        assert openreview_client.get_invitation('aclweb.org/ACL/ARR/2023/August/Submission4/-/Desk_Reject_Verification').expdate > now()

        # Delete checklist - check DSV flag is False, invitation is expired
        _, test_submission = post_meta_review(user_client, review_inv, user, ddate=now(), existing_note=edit['note'])
        assert 'flagged_for_ethics_review' not in test_submission.content
        assert 'flagged_for_desk_reject_verification' in test_submission.content
        assert not test_submission.content['flagged_for_desk_reject_verification']['value']
        assert openreview_client.get_invitation('aclweb.org/ACL/ARR/2023/August/Submission4/-/Desk_Reject_Verification').expdate < now()

        # Re-post with no ethics flag and a violation field - check DSV flag is True
        violation_edit, test_submission = post_meta_review(user_client, review_inv, user, override_fields={'author_identity_guess': {'value': 5}})
        assert 'flagged_for_ethics_review' not in test_submission.content
        assert 'flagged_for_desk_reject_verification' in test_submission.content
        assert test_submission.content['flagged_for_desk_reject_verification']['value']
        assert openreview_client.get_invitation('aclweb.org/ACL/ARR/2023/August/Submission4/-/Desk_Reject_Verification').expdate > now()

        # Edit with no ethics flag and no violation field - check DSV flag is False
        violation_edit['note']['content'][violation_fields[0]]['value'] = 1
        _, test_submission = post_meta_review(user_client, review_inv, user, existing_note=violation_edit['note'])
        assert 'flagged_for_ethics_review' not in test_submission.content
        assert 'flagged_for_desk_reject_verification' in test_submission.content
        assert not test_submission.content['flagged_for_desk_reject_verification']['value']
        assert openreview_client.get_invitation('aclweb.org/ACL/ARR/2023/August/Submission4/-/Desk_Reject_Verification').expdate < now()

        # Check that ethics reviewing is not available
        with pytest.raises(openreview.OpenReviewException, match=r'The Invitation aclweb.org/ACL/ARR/2023/August/Submission4/-/Ethics_Review has expired'):
            ethics_client.get_invitation('aclweb.org/ACL/ARR/2023/August/Submission4/-/Ethics_Review')

        # Edit with ethics flag and no violation field - check DSV flag is false and ethics flag exists and is True
        _, test_submission = post_meta_review(user_client, review_inv, user, tested_field='needs_ethics_review', existing_note=violation_edit['note'])
        assert 'flagged_for_ethics_review' in test_submission.content
        assert 'flagged_for_desk_reject_verification' in test_submission.content
        assert not test_submission.content['flagged_for_desk_reject_verification']['value']
        assert test_submission.content['flagged_for_ethics_review']['value']
        assert openreview_client.get_invitation('aclweb.org/ACL/ARR/2023/August/Submission4/-/Desk_Reject_Verification').expdate < now()

        # Post an ethics review
        ethics_anon_id = ethics_client.get_groups(prefix='aclweb.org/ACL/ARR/2023/August/Submission4/Ethics_Reviewer_', signatory='~EthicsReviewer_ARROne1')[0].id
        assert ethics_client.get_invitation('aclweb.org/ACL/ARR/2023/August/Submission4/-/Ethics_Review')
        ethics_client.post_note_edit(
            invitation='aclweb.org/ACL/ARR/2023/August/Submission4/-/Ethics_Review',
            signatures=[ethics_anon_id],
            note=openreview.api.Note(
                content={
                    'recommendation': {'value': 'a recommendation'},
                    'issues': {'value': ['1.2 Avoid harm']},
                    'explanation': {'value': 'an explanation'}
                }
            )
        )

        # Delete checklist - check both flags False
        _, test_submission = post_meta_review(user_client, review_inv, user, ddate=now(), existing_note=violation_edit['note'])
        assert 'flagged_for_ethics_review' in test_submission.content
        assert 'flagged_for_desk_reject_verification' in test_submission.content
        assert not test_submission.content['flagged_for_desk_reject_verification']['value']
        assert not test_submission.content['flagged_for_ethics_review']['value']

        # Ethics reviewing disabled
        with pytest.raises(openreview.OpenReviewException, match=r'The Invitation aclweb.org/ACL/ARR/2023/August/Submission4/-/Ethics_Review has expired'):
            ethics_client.get_invitation('aclweb.org/ACL/ARR/2023/August/Submission4/-/Ethics_Review')

        # Re-post with no flag - check both flags false
        reviewer_edit, test_submission = post_meta_review(user_client, review_inv, user)
        assert 'flagged_for_ethics_review' in test_submission.content
        assert 'flagged_for_desk_reject_verification' in test_submission.content
        assert not test_submission.content['flagged_for_desk_reject_verification']['value']
        assert not test_submission.content['flagged_for_ethics_review']['value']
        assert openreview_client.get_invitation('aclweb.org/ACL/ARR/2023/August/Submission4/-/Desk_Reject_Verification').expdate < now()

        # Make reviews public
        pc_client.post_note(
            openreview.Note(
                content={
                    'setup_meta_review_release_date': (openreview.tools.datetime.datetime.utcnow() + datetime.timedelta(seconds=6)).strftime('%Y/%m/%d %H:%M:%S')
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

        helpers.await_queue_edit(openreview_client, 'aclweb.org/ACL/ARR/2023/August/-/ARR_Scheduler-6-0', count=1)
        helpers.await_queue()
        helpers.await_queue(openreview_client)

        review = openreview_client.get_note(reviewer_edit['note']['id'])
        assert len(review.readers) - len(reviewer_edit['note']['readers']) == 1
        assert 'aclweb.org/ACL/ARR/2023/August/Submission4/Authors' in review.readers

    def test_emergency_reviewing_forms(self, client, openreview_client, helpers):
        # Update the process functions for each of the unavailability forms, set up the custom max papers
        # invitations and test that each note posts an edge

        # Load the venues
        now = datetime.datetime.utcnow()
        pc_client=openreview.Client(username='pc@aclrollingreview.org', password=helpers.strong_password)
        pc_client_v2=openreview.api.OpenReviewClient(username='pc@aclrollingreview.org', password=helpers.strong_password)
        request_form=pc_client.get_notes(invitation='openreview.net/Support/-/Request_Form')[1]
        venue = openreview.helpers.get_conference(client, request_form.id, 'openreview.net/Support')
        invitation_builder = openreview.arr.InvitationBuilder(venue)

        now = datetime.datetime.utcnow()
        due_date = now + datetime.timedelta(days=3)

        pc_client.post_note(
            openreview.Note(
                content={
                    'emergency_reviewing_start_date': (now).strftime('%Y/%m/%d %H:%M:%S'),
                    'emergency_reviewing_due_date': (due_date).strftime('%Y/%m/%d %H:%M:%S'),
                    'emergency_reviewing_exp_date': (due_date).strftime('%Y/%m/%d %H:%M:%S'),
                    'emergency_metareviewing_start_date': (now).strftime('%Y/%m/%d %H:%M:%S'),
                    'emergency_metareviewing_due_date': (due_date).strftime('%Y/%m/%d %H:%M:%S'),
                    'emergency_metareviewing_exp_date': (due_date).strftime('%Y/%m/%d %H:%M:%S'),
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

        assert openreview_client.get_invitation('aclweb.org/ACL/ARR/2023/August/Reviewers/-/Registered_Load')
        assert openreview_client.get_invitation('aclweb.org/ACL/ARR/2023/August/Reviewers/-/Emergency_Load')
        assert openreview_client.get_invitation('aclweb.org/ACL/ARR/2023/August/Reviewers/-/Emergency_Area')
        assert openreview_client.get_invitation('aclweb.org/ACL/ARR/2023/August/Area_Chairs/-/Registered_Load')
        assert openreview_client.get_invitation('aclweb.org/ACL/ARR/2023/August/Area_Chairs/-/Emergency_Load')
        assert openreview_client.get_invitation('aclweb.org/ACL/ARR/2023/August/Area_Chairs/-/Emergency_Area')
        
        # Test posting new notes and finding the edges
        reviewer_client = openreview.api.OpenReviewClient(username = 'reviewer1@aclrollingreview.com', password=helpers.strong_password)
        ac_client = openreview.api.OpenReviewClient(username = 'ac2@aclrollingreview.com', password=helpers.strong_password)

        reviewer_note_edit = reviewer_client.post_note_edit( ## Reviewer 1 will have an original load
            invitation=f'{venue.get_reviewers_id()}/-/{invitation_builder.MAX_LOAD_AND_UNAVAILABILITY_NAME}',
            signatures=['~Reviewer_ARROne1'],
            note=openreview.api.Note(
                content = {
                    'maximum_load': { 'value': '4' },
                    'maximum_load_resubmission': { 'value': 'No' }
                }
            )
        )
        helpers.await_queue_edit(openreview_client, edit_id=reviewer_note_edit['id'])
        assert len(openreview_client.get_all_edges(invitation='aclweb.org/ACL/ARR/2023/August/Reviewers/-/Custom_Max_Papers', tail='~Reviewer_ARROne1')) == 1
        assert openreview_client.get_all_edges(invitation='aclweb.org/ACL/ARR/2023/August/Reviewers/-/Custom_Max_Papers', tail='~Reviewer_ARROne1')[0].weight == 4

        test_cases = [
            {   
                'role': venue.get_reviewers_id(),
                'invitation_name': invitation_builder.EMERGENCY_REVIEWING_NAME,
                'client': reviewer_client,
                'user': '~Reviewer_ARROne1'
            },
            {   
                'role': venue.get_area_chairs_id(),
                'invitation_name': invitation_builder.EMERGENCY_METAREVIEWING_NAME,
                'client': ac_client,
                'user': '~AC_ARRTwo1'
            }
        ]
        for case in test_cases:
            role, inv_name, user_client, user = case['role'], case['invitation_name'], case['client'], case['user']

            # Test preprocess
            with pytest.raises(openreview.OpenReviewException, match=r'You have agreed to emergency reviewing, please enter the additional load that you want to be assigned.'):
                user_note_edit = user_client.post_note_edit(
                    invitation=f'{role}/-/{inv_name}',
                    signatures=[user],
                    note=openreview.api.Note(
                        content = {
                            'emergency_reviewing_agreement': { 'value': 'Yes' },
                            'research_area': { 'value': 'Generation' }
                        }
                    )
                )
            with pytest.raises(openreview.OpenReviewException, match=r'You have agreed to emergency reviewing, please enter your closest relevant research area.'):
                user_note_edit = user_client.post_note_edit(
                    invitation=f'{role}/-/{inv_name}',
                    signatures=[user],
                    note=openreview.api.Note(
                        content = {
                            'emergency_reviewing_agreement': { 'value': 'Yes' },
                            'emergency_load': { 'value': '2' },
                        }
                    )
                )

            # Test valid note and check for edges
            user_note_edit = user_client.post_note_edit(
                invitation=f'{role}/-/{inv_name}',
                signatures=[user],
                note=openreview.api.Note(
                    content = {
                        'emergency_reviewing_agreement': { 'value': 'Yes' },
                        'emergency_load': { 'value': '2' },
                        'research_area': { 'value': 'Generation' }
                    }
                )
            )
            
            helpers.await_queue_edit(openreview_client, edit_id=user_note_edit['id'])

            cmp_edges = {o['id']['tail']: [j['weight'] for j in o['values']] for o in pc_client_v2.get_grouped_edges(invitation=f"{role}/-/Custom_Max_Papers", groupby='tail', select='weight')}
            reg_edges = {o['id']['tail']: [j['weight'] for j in o['values']] for o in pc_client_v2.get_grouped_edges(invitation=f"{role}/-/Registered_Load", groupby='tail', select='weight')}
            emg_edges = {o['id']['tail']: [j['weight'] for j in o['values']] for o in pc_client_v2.get_grouped_edges(invitation=f"{role}/-/Emergency_Load", groupby='tail', select='weight')}
            area_edges = {o['id']['tail']: [j['label'] for j in o['values']] for o in pc_client_v2.get_grouped_edges(invitation=f"{role}/-/Emergency_Area", groupby='tail', select='label')}

            assert all(user in edges for edges in [cmp_edges, reg_edges, emg_edges, area_edges])
            assert all(len(edges[user]) == 1 for edges in [cmp_edges, reg_edges, emg_edges, area_edges])
            cmp_original, reg_original, emg_original = cmp_edges[user][0], reg_edges[user][0], emg_edges[user][0]
    
            if 'Reviewer' in user:
                assert cmp_edges[user][0] == 6
            assert cmp_original == reg_original + emg_original
            assert area_edges[user][0] == 'Generation'

            score_edges = {o['id']['tail']: [j['weight'] for j in o['values']] for o in pc_client_v2.get_grouped_edges(invitation=f"{role}/-/Aggregate_Score", groupby='tail', select='weight')}
            assert all(weight >= 10 for weight in score_edges[user])

            # Test editing note
            user_note_edit = user_client.post_note_edit(
                invitation=f'{role}/-/{inv_name}',
                signatures=[user],
                note=openreview.api.Note(
                    id=user_note_edit['note']['id'],
                    content = {
                        'emergency_reviewing_agreement': { 'value': 'Yes' },
                        'emergency_load': { 'value': '4' },
                        'research_area': { 'value': 'Machine Translation' }
                    }
                )
            )
            
            helpers.await_queue_edit(openreview_client, edit_id=user_note_edit['id'])

            cmp_edges = {o['id']['tail']: [j['weight'] for j in o['values']] for o in pc_client_v2.get_grouped_edges(invitation=f"{role}/-/Custom_Max_Papers", groupby='tail', select='weight')}
            reg_edges = {o['id']['tail']: [j['weight'] for j in o['values']] for o in pc_client_v2.get_grouped_edges(invitation=f"{role}/-/Registered_Load", groupby='tail', select='weight')}
            emg_edges = {o['id']['tail']: [j['weight'] for j in o['values']] for o in pc_client_v2.get_grouped_edges(invitation=f"{role}/-/Emergency_Load", groupby='tail', select='weight')}
            area_edges = {o['id']['tail']: [j['label'] for j in o['values']] for o in pc_client_v2.get_grouped_edges(invitation=f"{role}/-/Emergency_Area", groupby='tail', select='label')}

            assert all(user in edges for edges in [cmp_edges, reg_edges, emg_edges, area_edges])
            assert all(len(edges[user]) == 1 for edges in [cmp_edges, reg_edges, emg_edges, area_edges])
            if 'Reviewer' in user:
                assert cmp_edges[user][0] == 10
            assert cmp_edges[user][0] != cmp_original
            assert reg_edges[user][0] != reg_original
            assert emg_edges[user][0] != emg_original
            assert cmp_edges[user][0] == reg_edges[user][0] + emg_edges[user][0]
            assert area_edges[user][0] == 'Machine Translation'

            score_edges = {o['id']['tail']: [j['weight'] for j in o['values']] for o in pc_client_v2.get_grouped_edges(invitation=f"{role}/-/Aggregate_Score", groupby='tail', select='weight')}
            assert all(weight >= 10 for weight in score_edges[user])

            # Test deleting note
            user_note_edit = user_client.post_note_edit(
                invitation=f'{role}/-/{inv_name}',
                signatures=[user],
                note=openreview.api.Note(
                    id=user_note_edit['note']['id'],
                    ddate=openreview.tools.datetime_millis(now),
                    content = {
                        'emergency_reviewing_agreement': { 'value': 'Yes' },
                        'emergency_load': { 'value': '4' },
                        'research_area': { 'value': 'Machine Translation' }
                    }
                )
            )
            
            helpers.await_queue_edit(openreview_client, edit_id=user_note_edit['id'])

            assert pc_client_v2.get_edges_count(invitation=f"{role}/-/Custom_Max_Papers", tail=user) == 1
            cmp_edges = {o['id']['tail']: [j['weight'] for j in o['values']] for o in pc_client_v2.get_grouped_edges(invitation=f"{role}/-/Custom_Max_Papers", groupby='tail', select='weight')}
            assert cmp_edges[user][0] == reg_edges[user][0] ## New custom max papers should just be what was registered with
            assert pc_client_v2.get_edges_count(invitation=f"{role}/-/Registered_Load", tail=user) == 0
            assert pc_client_v2.get_edges_count(invitation=f"{role}/-/Emergency_Load", tail=user) == 0
            assert pc_client_v2.get_edges_count(invitation=f"{role}/-/Emergency_Area", tail=user) == 0

            score_edges = {o['id']['tail']: [j['weight'] for j in o['values']] for o in pc_client_v2.get_grouped_edges(invitation=f"{role}/-/Aggregate_Score", groupby='tail', select='weight')}
            assert all(weight < 10 for weight in score_edges[user])

    def test_review_rating_forms(self, client, openreview_client, helpers, test_client):
        now = datetime.datetime.utcnow()
        pc_client=openreview.Client(username='pc@aclrollingreview.org', password=helpers.strong_password)
        pc_client_v2=openreview.api.OpenReviewClient(username='pc@aclrollingreview.org', password=helpers.strong_password)
        request_form=pc_client.get_notes(invitation='openreview.net/Support/-/Request_Form')[1]
        venue = openreview.helpers.get_conference(client, request_form.id, 'openreview.net/Support')
        invitation_builder = openreview.arr.InvitationBuilder(venue)
        test_client = openreview.api.OpenReviewClient(token=test_client.token)

        now = datetime.datetime.utcnow()
        due_date = now + datetime.timedelta(days=3)

        pc_client.post_note(
            openreview.Note(
                content={
                    'review_rating_start_date': (now).strftime('%Y/%m/%d %H:%M:%S'),
                    'review_rating_exp_date': (due_date).strftime('%Y/%m/%d %H:%M:%S')
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

        assert openreview_client.get_invitation('aclweb.org/ACL/ARR/2023/August/-/Review_Rating')

        helpers.await_queue_edit(openreview_client, 'aclweb.org/ACL/ARR/2023/August/-/Review_Rating-0-1')

        assert openreview_client.get_invitation('aclweb.org/ACL/ARR/2023/August/Submission3/Official_Review4/-/Review_Rating')

        rating_edit = test_client.post_note_edit(
            invitation='aclweb.org/ACL/ARR/2023/August/Submission3/Official_Review4/-/Review_Rating',
            signatures=['aclweb.org/ACL/ARR/2023/August/Submission3/Authors'],
            note=openreview.api.Note(
                content = {
                    "overall_review_rating": {"value": 5},
                    "aspect_understanding": {"value": 4},
                    "aspect_substantiation": {"value": 3},
                    "aspect_correctness": {"value": 2},
                    "aspect_constructiveness": {"value": 1},
                    "scope_impact_or_importance": {"value": "Sufficiently"},
                    "scope_originality_or_novelty": {"value": "Insufficiently"},
                    "scope_correctness": {"value": "Not at all"},
                    "scope_substance": {"value": "Yes"},
                    "scope_meaningful_comparison": {"value": "Yes"},
                    "scope_organization_or_presentation": {"value": "No"},
                    "additional_comments": {"value": "Some comments"}
                }
            )
        )

        assert test_client.get_note(rating_edit['note']['id'])