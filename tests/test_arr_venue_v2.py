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
        invitation_builder.set_arr_configuration_invitation()
        invitation_builder.set_arr_scheduler_invitation()
        invitation_builder.set_preprint_release_submission_invitation()

        assert client.get_invitation(f'openreview.net/Support/-/Request{request_form_note.number}/ARR_Configuration')
        assert openreview_client.get_invitation('aclweb.org/ACL/ARR/2023/August/-/Preprint_Release_Submission')
        assert openreview_client.get_invitation('aclweb.org/ACL/ARR/2023/August/-/ARR_Scheduler')

        now = datetime.datetime.utcnow()

        pc_client.post_note(
            openreview.Note(
                content={
                    'setup_venue_stages_date': (openreview.tools.datetime.datetime.utcnow() + datetime.timedelta(seconds=3)).strftime('%Y/%m/%d %H:%M:%S')
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

        helpers.await_queue_edit(openreview_client, 'aclweb.org/ACL/ARR/2023/August/-/ARR_Scheduler-0-0', count=1)

        # Create ethics review stage to add values into domain
        now = datetime.datetime.utcnow()
        start_date = now - datetime.timedelta(days=2)
        due_date = now + datetime.timedelta(days=3)
        stage_note = pc_client.post_note(openreview.Note(
            content={
                'ethics_review_start_date': start_date.strftime('%Y/%m/%d'),
                'ethics_review_deadline': due_date.strftime('%Y/%m/%d'),
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
        
        venue = openreview.helpers.get_conference(client, request_form_note.id, 'openreview.net/Support')
        venue.create_ethics_review_stage()

        # Pin 2023 and 2024 into next available year
        for content in [
            arr_reviewer_max_load_task,
            arr_ac_max_load_task,
            arr_sac_max_load_task,
        ]:
            content['next_available_year']['value']['param']['enum'] = list(set([2022, 2023, 2024] + content['next_available_year']['value']['param']['enum']))

        # Create current registration stages
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

        # Create custom max papers invitations early
        venue_roles = [
            venue.get_reviewers_id(),
            venue.get_area_chairs_id(),
            venue.get_senior_area_chairs_id()
        ]
        for role in venue_roles:
            m = matching.Matching(venue, venue.client.get_group(role), None, None)
            m._create_edge_invitation(venue.get_custom_max_papers_id(m.match_group.id))

            openreview_client.post_invitation_edit(
                invitations=venue.get_meta_invitation_id(),
                readers=[venue.id],
                writers=[venue.id],
                signatures=[venue.id],
                invitation=openreview.api.Invitation(
                    id=f"{role}/-/{max_load_name}",
                    process=invitation_builder.get_process_content('process/max_load_process.py'),
                    preprocess=invitation_builder.get_process_content('process/max_load_preprocess.py')
                )
            )
        # TODO: Move max load setup into an ARR invitation


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
                f"~AC_ARR{num}1" for num in ['One', 'Two']
            ]
        )
        openreview_client.add_members_to_group(
            venue.get_senior_area_chairs_id(), [
                f"~SAC_ARR{num}1" for num in ['One', 'Two']
            ]
        )
        openreview_client.add_members_to_group(venue.get_ethics_chairs_id(), ['~EthicsChair_ARROne1'])
        openreview_client.add_members_to_group(venue.get_ethics_reviewers_id(), ['~EthicsReviewer_ARROne1'])

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
                'ethics_review_deadline': due_date.strftime('%Y/%m/%d'),
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
                    'research_area': { 'value': ['Summarization', 'NLP Applications'] },
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
                    'maximum_load_resubmission': { 'value': 'Yes' },
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
        invitation_builder.set_arr_configuration_invitation()
        invitation_builder.set_arr_scheduler_invitation()

        assert openreview_client.get_invitation('aclweb.org/ACL/ARR/2023/June/-/ARR_Scheduler')

        pc_client.post_note(
            openreview.Note(
                content={
                    'setup_venue_stages_date': (openreview.tools.datetime.datetime.utcnow() + datetime.timedelta(seconds=3)).strftime('%Y/%m/%d %H:%M:%S')
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

        helpers.await_queue_edit(openreview_client, 'aclweb.org/ACL/ARR/2023/June/-/ARR_Scheduler-0-0', count=1)

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

        helpers.await_queue_edit(openreview_client, 'aclweb.org/ACL/ARR/2023/August/-/ARR_Scheduler-1-0', count=1)

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

        helpers.await_queue_edit(openreview_client, 'aclweb.org/ACL/ARR/2023/August/-/ARR_Scheduler-1-0', count=2)

        # Find August in readers of groups and registration notes
        assert set(pc_client_v2.get_group(june_venue.get_reviewers_id()).members) == set(pc_client_v2.get_group(august_venue.get_reviewers_id()).members)
        assert set(pc_client_v2.get_group(june_venue.get_area_chairs_id()).members) == set(pc_client_v2.get_group(august_venue.get_area_chairs_id()).members)
        assert set(pc_client_v2.get_group(june_venue.get_senior_area_chairs_id()).members) == set(pc_client_v2.get_group(august_venue.get_senior_area_chairs_id()).members)
        assert set(pc_client_v2.get_group(june_venue.get_ethics_reviewers_id()).members) == set(pc_client_v2.get_group(august_venue.get_ethics_reviewers_id()).members)
        assert set(pc_client_v2.get_group(june_venue.get_ethics_chairs_id()).members) == set(pc_client_v2.get_group(august_venue.get_ethics_chairs_id()).members)

        june_reviewer_registration_notes = pc_client.get_all_notes(invitation=f"{june_venue.get_reviewers_id()}/-/Registration")
        august_reviewer_registration_notes = pc_client.get_all_notes(invitation=f"{august_venue.get_reviewers_id()}/-/Registration")
        assert all(j.signatures[0] == a.signatures[0] for a, j in zip(june_reviewer_registration_notes, august_reviewer_registration_notes))
        june_ac_registration_notes = pc_client.get_all_notes(invitation=f"{june_venue.get_area_chairs_id()}/-/Registration")
        august_ac_registration_notes = pc_client.get_all_notes(invitation=f"{august_venue.get_area_chairs_id()}/-/Registration")
        assert all(j.signatures[0] == a.signatures[0] for a, j in zip(june_ac_registration_notes, august_ac_registration_notes))
        june_sac_registration_notes = pc_client.get_all_notes(invitation=f"{june_venue.get_senior_area_chairs_id()}/-/Registration")
        august_sac_registration_notes = pc_client.get_all_notes(invitation=f"{august_venue.get_senior_area_chairs_id()}/-/Registration")
        assert all(j.signatures[0] == a.signatures[0] for a, j in zip(june_sac_registration_notes, august_sac_registration_notes))

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
        

    def test_supplementary_materials_and_preprints(self, client, openreview_client, helpers):
        # After the submission deadline, opt-in papers have their readers set to everyone
        # and a subset of the blinded fields are re-posted as supplementary material
        # Check that the submissions are publicly visible on the homepage
        pass

    def test_reviewer_tasks(self, client, openreview_client, helpers):
        # Setup reviewer licensing and recognition tasks (registration forms) and consent forms
        # (replies to reviews)
        pass

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

        helpers.await_queue_edit(openreview_client, 'aclweb.org/ACL/ARR/2023/August/-/ARR_Scheduler-2-0', count=1)

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
