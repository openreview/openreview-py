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
from openreview.stages.arr_content import arr_submission_content, hide_fields

# API2 template from ICML
class TestARRVenueV2():


    @pytest.fixture(scope="class")
    def profile_management(self, client):
        profile_management = ProfileManagement(client, 'openreview.net')
        profile_management.setup()
        return profile_management


    def test_create_conference(self, client, openreview_client, helpers, profile_management):

        now = datetime.datetime.utcnow()
        due_date = now + datetime.timedelta(days=3)

        # Post the request form note
        pc_client=helpers.create_user('pc@aclrollingreview.org', 'Program', 'ARRChair')

        sac_client = helpers.create_user('sac1@aclrollingreview.com', 'SAC', 'ARROne')
        helpers.create_user('sac2@aclrollingreview.com', 'SAC', 'ARRTwo')
        helpers.create_user('ac1@aclrollingreview.com', 'AC', 'ARROne')
        helpers.create_user('ac2@aclrollingreview.com', 'AC', 'ARRTwo')
        helpers.create_user('reviewer1@aclrollingreview.com', 'Reviewer', 'ARROne')
        helpers.create_user('reviewer2@aclrollingreview.com', 'Reviewer', 'ARRTwo')
        helpers.create_user('reviewer3@aclrollingreview.com', 'Reviewer', 'ARRThree')
        helpers.create_user('reviewer4@aclrollingreview.com', 'Reviewer', 'ARRFour')
        helpers.create_user('reviewer5@aclrollingreview.com', 'Reviewer', 'ARRFive')
        helpers.create_user('reviewer6@aclrollingreview.com', 'Reviewer', 'ARRSix')
        helpers.create_user('reviewerethics@aclrollingreview.com', 'Reviewer', 'ARRSeven')

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
                'api_version': '2'
            }))

        helpers.await_queue()

        # Post a deploy note
        client.post_note(openreview.Note(
            content={'venue_id': 'aclweb.org/ACL/ARR/2023/August'},
            forum=request_form_note.forum,
            invitation='openreview.net/Support/-/Request{}/Deploy'.format(request_form_note.number),
            readers=['openreview.net/Support'],
            referent=request_form_note.forum,
            replyto=request_form_note.forum,
            signatures=['openreview.net/Support'],
            writers=['openreview.net/Support']
        ))

        helpers.await_queue()

        assert openreview_client.get_group('aclweb.org/ACL/ARR/2023/August')
        assert openreview_client.get_group('aclweb.org/ACL/ARR/2023/August/Senior_Area_Chairs')
        assert openreview_client.get_group('aclweb.org/ACL/ARR/2023/August/Area_Chairs')
        assert openreview_client.get_group('aclweb.org/ACL/ARR/2023/August/Reviewers')
        assert openreview_client.get_group('aclweb.org/ACL/ARR/2023/August/Authors')

        submission_invitation = openreview_client.get_invitation('aclweb.org/ACL/ARR/2023/August/-/Submission')
        assert submission_invitation
        assert submission_invitation.duedate

        assert openreview_client.get_invitation('aclweb.org/ACL/ARR/2023/August/Reviewers/-/Expertise_Selection')

        sac_client.post_note(openreview.Note(
            invitation='openreview.net/Archive/-/Direct_Upload',
            readers = ['everyone'],
            signatures = ['~SAC_ARROne1'],
            writers = ['~SAC_ARROne1'],
            content = {
                'title': 'Paper title 1',
                'abstract': 'Paper abstract 1',
                'authors': ['SAC ARR', 'Test2 Client'],
                'authorids': ['~SAC_ARROne1', 'test2@mail.com']
            }
        ))

        sac_client.post_note(openreview.Note(
            invitation='openreview.net/Archive/-/Direct_Upload',
            readers = ['everyone'],
            signatures = ['~SAC_ARROne1'],
            writers = ['~SAC_ARROne1'],
            content = {
                'title': 'Paper title 2',
                'abstract': 'Paper abstract 2',
                'authors': ['SAC ARR', 'Test2 Client'],
                'authorids': ['~SAC_ARROne1', 'test2@mail.com']
            }
        ))

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

        submission_invitation = openreview_client.get_invitation('aclweb.org/ACL/ARR/2023/August/-/Submission')
        assert submission_invitation
        assert 'responsible_NLP_research' in submission_invitation.edit['note']['content']
        assert 'keywords' not in submission_invitation.edit['note']['content']

        domain = openreview_client.get_group('aclweb.org/ACL/ARR/2023/August')
        assert 'recommendation' == domain.content['meta_review_recommendation']['value']

        venue = openreview.helpers.get_conference(client, request_form_note.id, 'openreview.net/Support')
        invitation_builder = openreview.arr.InvitationBuilder(venue)
        invitation_builder.set_preprint_release_submission_invitation()

        assert openreview_client.get_invitation('aclweb.org/ACL/ARR/2023/August/-/Preprint_Release_Submission')

    def test_copy_members(self, client, openreview_client, helpers):
        # Create a previous cycle (2023/June) and test the script that copies all roles
        # (reviewers/ACs/SACs/ethics reviewers/ethics chairs) into the current cycle (2023/August)
        pass

    def test_unavailability_and_registration_tasks(self, client, openreview_client, helpers):
        # Set up the forms for max load and tracks for reviewers/ACs/SACs
        # Also copy expertise edges and registration notes into the current cycle
        pass

    def test_unavailability_process_functions(self, client, openreview_client, helpers):
        # Update the process functions for each of the unavailability forms, set up the custom max papers
        # invitations and test that each note posts an edge
        pass

    def test_submission_preprocess(self, client, openreview_client, helpers):
        # Update the submission preprocess function and test validation for combinations
        # of previous_URL/reassignment_request_action_editor/reassignment_request_reviewers
        pass

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
        request_form=pc_client.get_notes(invitation='openreview.net/Support/-/Request_Form')[0]

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
        pc_client_v2.post_invitation_edit(
            invitations='aclweb.org/ACL/ARR/2023/August/-/Edit',
            signatures=['aclweb.org/ACL/ARR/2023/August'],
            invitation=openreview.api.Invitation(id='aclweb.org/ACL/ARR/2023/August/-/Preprint_Release_Submission',
                cdate=openreview.tools.datetime_millis(datetime.datetime.utcnow() - datetime.timedelta(minutes=1)),
                signatures=['aclweb.org/ACL/ARR/2023/August']
            )
        )

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
