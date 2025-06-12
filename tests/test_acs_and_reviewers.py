import os
import re
import csv
import pytest
import random
import datetime
import re
import openreview
from openreview.api import Note
from selenium.webdriver.common.by import By
from openreview.api import OpenReviewClient
from openreview.workflows import templates
from openreview.workflows import workflows

class TestSimpleDualAnonymous():

    def test_setup(self, openreview_client, helpers):
        super_id = 'openreview.net'
        support_group_id = super_id + '/Support'

        helpers.create_user('programchair@efgh.cc', 'ProgramChair', 'EFGH')
        helpers.create_user('reviewer_one@efgh.cc', 'ReviewerOne', 'EFGH')
        helpers.create_user('reviewer_two@efgh.cc', 'ReviewerTwo', 'EFGH')
        helpers.create_user('reviewer_three@efgh.cc', 'ReviewerThree', 'EFGH')
        helpers.create_user('areachair_one@efgh.cc', 'ACOne', 'EFGH')
        helpers.create_user('areachair_one_two@efgh.cc', 'ACTwo', 'EFGH')
        helpers.create_user('areachair_one_three@efgh.cc', 'ACThree', 'EFGH')
        pc_client=openreview.api.OpenReviewClient(username='programchair@efgh.cc', password=helpers.strong_password)

        workflows_setup = workflows.Workflows(openreview_client, support_group_id, super_id)
        workflows_setup.setup()

        templates_invitations = templates.Templates(openreview_client, support_group_id, super_id)
        templates_invitations.setup()

        assert openreview_client.get_invitation('openreview.net/-/Edit')
        assert openreview_client.get_group('openreview.net/Support/Venue_Request')
        assert openreview_client.get_invitation('openreview.net/Support/Venue_Request/-/ACs_and_Reviewers')
        assert openreview_client.get_invitation('openreview.net/Support/Venue_Request/ACs_and_Reviewers/-/Deployment')
        assert openreview_client.get_invitation('openreview.net/Support/Venue_Request/ACs_and_Reviewers/-/Comment')

        now = datetime.datetime.now()
        due_date = now + datetime.timedelta(days=2)

        request = pc_client.post_note_edit(invitation='openreview.net/Support/Venue_Request/-/ACs_and_Reviewers',
            signatures=['~ProgramChair_EFGH1'],
            note=openreview.api.Note(
                content={
                    'official_venue_name': { 'value': 'The EFGH Conference' },
                    'abbreviated_venue_name': { 'value': 'EFGH 2025' },
                    'venue_website_url': { 'value': 'https://efgh.cc/Conferences/2025' },
                    'location': { 'value': 'Minnetonka, Minnesota' },
                    'venue_start_date': { 'value': openreview.tools.datetime_millis(now + datetime.timedelta(weeks=52)) },
                    'program_chair_emails': { 'value': ['programchair@efgh.cc'] },
                    'contact_email': { 'value': 'efgh2025.programchairs@gmail.com' },
                    'submission_start_date': { 'value': openreview.tools.datetime_millis(now) },
                    'submission_deadline': { 'value': openreview.tools.datetime_millis(due_date) },
                    'submission_license': {
                        'value':  ['CC BY-ND 4.0']
                    },
                    'reviewers_name': { 'value': 'Reviewers' },
                    'area_chairs_name': { 'value': 'Action_Editors' },
                    'venue_organizer_agreement': { 
                        'value': [
                            'OpenReview natively supports a wide variety of reviewing workflow configurations. However, if we want significant reviewing process customizations or experiments, we will detail these requests to the OpenReview staff at least three months in advance.',
                            'We will ask authors and reviewers to create an OpenReview Profile at least two weeks in advance of the paper submission deadlines.',
                            'When assembling our group of reviewers, we will only include email addresses or OpenReview Profile IDs of people we know to have authored publications relevant to our venue.  (We will not solicit new reviewers using an open web form, because unfortunately some malicious actors sometimes try to create "fake ids" aiming to be assigned to review their own paper submissions.)',
                            'We acknowledge that, if our venue\'s reviewing workflow is non-standard, or if our venue is expecting more than a few hundred submissions for any one deadline, we should designate our own Workflow Chair, who will read the OpenReview documentation and manage our workflow configurations throughout the reviewing process.',
                            'We acknowledge that OpenReview staff work Monday-Friday during standard business hours US Eastern time, and we cannot expect support responses outside those times.  For this reason, we recommend setting submission and reviewing deadlines Monday through Thursday.',
                            'We will treat the OpenReview staff with kindness and consideration.',
                            'We acknowledge that authors and reviewers will be required to share their preferred email.',
                            'We acknowledge that review counts will be collected for all the reviewers and publicly available in OpenReview.',
                            'We acknowledge that metadata for accepted papers will be publicly released in OpenReview.'
                            ]
                    }
                }
            ))
        
        helpers.await_queue_edit(openreview_client, edit_id=request['id'])

        request = openreview_client.get_note(request['note']['id'])
        assert openreview_client.get_invitation(f'openreview.net/Support/Venue_Request/ACs_and_Reviewers{request.number}/-/Comment')
        assert openreview.tools.get_group(openreview_client, 'EFGH.cc/2025/Conference/Program_Chairs') is None

        # deploy the venue
        edit = openreview_client.post_note_edit(invitation=f'openreview.net/Support/Venue_Request/ACs_and_Reviewers/-/Deployment',
            signatures=[support_group_id],
            note=openreview.api.Note(
                id=request.id,
                content={
                    'venue_id': { 'value': 'EFGH.cc/2025/Conference' }
                }
            ))
        
        helpers.await_queue_edit(openreview_client, edit_id=edit['id'])
        helpers.await_queue_edit(openreview_client, invitation='openreview.net/Template/-/Submission_Change_Before_Bidding')

        reviewers_group = openreview.tools.get_group(openreview_client, 'EFGH.cc/2025/Conference/Reviewers')
        assert len(reviewers_group.readers) == 3
        assert 'EFGH.cc/2025/Conference' in reviewers_group.readers
        assert 'EFGH.cc/2025/Conference/Action_Editors' in reviewers_group.readers
        assert 'EFGH.cc/2025/Conference/Reviewers' in reviewers_group.readers
        reviewers_invited_group = openreview.tools.get_group(openreview_client, 'EFGH.cc/2025/Conference/Reviewers/Invited')
        assert reviewers_invited_group.readers == ['EFGH.cc/2025/Conference', 'EFGH.cc/2025/Conference/Reviewers/Invited']
        reviewers_declined_group = openreview.tools.get_group(openreview_client, 'EFGH.cc/2025/Conference/Reviewers/Declined')
        assert reviewers_declined_group.readers == ['EFGH.cc/2025/Conference', 'EFGH.cc/2025/Conference/Reviewers/Declined']
        assert openreview.tools.get_group(openreview_client, 'EFGH.cc/2025/Conference/Action_Editors')
        assert openreview.tools.get_group(openreview_client, 'EFGH.cc/2025/Conference/Action_Editors/Invited')
        assert openreview.tools.get_group(openreview_client, 'EFGH.cc/2025/Conference/Action_Editors/Declined')
        pc_group =  openreview.tools.get_group(openreview_client, 'EFGH.cc/2025/Conference/Program_Chairs')
        assert pc_group and pc_group.members == ['programchair@efgh.cc']
        assert openreview.tools.get_group(openreview_client, 'EFGH.cc/2025/Conference/Automated_Administrator')

        assert openreview.tools.get_invitation(openreview_client, 'EFGH.cc/2025/Conference/Action_Editors/-/Message')
        assert openreview.tools.get_invitation(openreview_client, 'EFGH.cc/2025/Conference/Action_Editors/-/Members')

        domain_content = openreview.tools.get_group(openreview_client, 'EFGH.cc/2025/Conference').content
        assert domain_content['reviewers_invited_id']['value'] == 'EFGH.cc/2025/Conference/Reviewers/Invited'
        assert domain_content['reviewers_declined_id']['value'] == 'EFGH.cc/2025/Conference/Reviewers/Declined'
        assert domain_content['reviewers_id']['value'] == 'EFGH.cc/2025/Conference/Reviewers'
        assert domain_content['reviewers_name']['value'] == 'Reviewers'
        assert domain_content['reviewers_anon_name']['value'] == 'Reviewer_'
        assert domain_content['reviewers_submitted_name']['value'] == 'Submitted'
        assert domain_content['reviewers_recruitment_id']['value'] == 'EFGH.cc/2025/Conference/Reviewers/-/Recruitment'
        assert domain_content['reviewers_invited_message_id']['value'] == 'EFGH.cc/2025/Conference/Reviewers/Invited/-/Message' 

        assert domain_content['area_chairs_invited_id']['value'] == 'EFGH.cc/2025/Conference/Action_Editors/Invited'
        assert domain_content['area_chairs_declined_id']['value'] == 'EFGH.cc/2025/Conference/Action_Editors/Declined'
        assert domain_content['area_chairs_id']['value'] == 'EFGH.cc/2025/Conference/Action_Editors'
        assert domain_content['area_chairs_name']['value'] == 'Action_Editors'
        assert domain_content['area_chairs_anon_name']['value'] == 'Action_Editor_'
        assert domain_content.get('area_chairs_submitted_name') is None
        assert domain_content['area_chairs_recruitment_id']['value'] == 'EFGH.cc/2025/Conference/Action_Editors/-/Recruitment'
        assert domain_content['area_chairs_invited_message_id']['value'] == 'EFGH.cc/2025/Conference/Action_Editors/Invited/-/Message'                

        assert openreview.tools.get_invitation(openreview_client, 'EFGH.cc/2025/Conference/-/Submission')
        assert openreview.tools.get_invitation(openreview_client,'EFGH.cc/2025/Conference/-/Submission/Dates')
        assert openreview.tools.get_invitation(openreview_client,'EFGH.cc/2025/Conference/-/Submission/Form_Fields')
        assert openreview.tools.get_invitation(openreview_client,'EFGH.cc/2025/Conference/-/Submission/Notifications')
        invitation = openreview.tools.get_invitation(openreview_client, 'EFGH.cc/2025/Conference/-/Submission_Change_Before_Bidding')
        assert invitation.edit['note']['readers'] == [
            'EFGH.cc/2025/Conference',
            'EFGH.cc/2025/Conference/Action_Editors',
            'EFGH.cc/2025/Conference/Reviewers',
            'EFGH.cc/2025/Conference/Submission${{2/id}/number}/Authors'
        ]
        assert openreview.tools.get_invitation(openreview_client, 'EFGH.cc/2025/Conference/-/Submission_Change_Before_Bidding/Dates')
        assert openreview.tools.get_invitation(openreview_client, 'EFGH.cc/2025/Conference/-/Submission_Change_Before_Bidding/Restrict_Field_Visibility')
