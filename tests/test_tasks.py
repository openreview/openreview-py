import os
import re
import csv
import pytest
import random
import datetime
import openreview
from openreview.api import Note
from selenium.webdriver.common.by import By
from openreview.api import OpenReviewClient

class TestTasks():

    def test_setup(self, openreview_client, helpers):
        super_id = 'openreview.net'
        support_group_id = super_id + '/Support'

        helpers.create_user('programchair@tasks.cc', 'ProgramChair', 'Tasks')
        helpers.create_user('reviewer_one@tasks.cc', 'ReviewerOne', 'Tasks')
        helpers.create_user('reviewer_two@tasks.cc', 'ReviewerTwo', 'Tasks')
        helpers.create_user('reviewer_three@tasks.cc', 'ReviewerThree', 'Tasks')
        pc_client=openreview.api.OpenReviewClient(username='programchair@tasks.cc', password=helpers.strong_password)

        assert openreview_client.get_invitation('openreview.net/-/Edit')
        assert openreview_client.get_group('openreview.net/Support/Venue_Request')
        assert openreview_client.get_invitation('openreview.net/Support/Venue_Request/-/Conference_Review_Workflow')
        assert openreview_client.get_invitation('openreview.net/Support/Venue_Request/Conference_Review_Workflow/-/Comment')
        assert openreview_client.get_invitation('openreview.net/Support/Venue_Request/Conference_Review_Workflow/-/Deployment')
        assert openreview_client.get_invitation('openreview.net/Support/Venue_Request/Conference_Review_Workflow/-/Status')

        now = datetime.datetime.now()
        start_date = now + datetime.timedelta(minutes=40)
        due_date = now + datetime.timedelta(days=2)

        request = pc_client.post_note_edit(invitation='openreview.net/Support/Venue_Request/-/Conference_Review_Workflow',
            signatures=['~ProgramChair_Tasks1'],
            note=openreview.api.Note(
                content={
                    'official_venue_name': { 'value': 'The Tasks Conference' },
                    'abbreviated_venue_name': { 'value': 'Tasks 2025' },
                    'venue_website_url': { 'value': 'https://tasks.cc/Conferences/2025' },
                    'location': { 'value': 'Amherst, Massachusetts' },
                    'venue_start_date': { 'value': openreview.tools.datetime_millis(now + datetime.timedelta(weeks=52)) },
                    'program_chair_emails': { 'value': ['programchair@tasks.cc'] },
                    'contact_email': { 'value': 'tasks2025.programchairs@gmail.com' },
                    'submission_start_date': { 'value': openreview.tools.datetime_millis(start_date) },
                    'submission_deadline': { 'value': openreview.tools.datetime_millis(due_date) },
                    'reviewers_name': { 'value': 'Program_Committee' },
                    'area_chairs_name': { 'value': 'Area_Chairs' },
                    'senior_area_chairs_name': { 'value': 'Senior_Area_Chairs' },
                    'colocated': { 'value': 'Independent' },
                    'previous_venue': { 'value': 'Tasks.cc/2024/Conference' },
                    'expected_submissions': { 'value': 1000 },
                    'how_did_you_hear_about_us': { 'value': 'We have used OpenReview for our previous conferences.' },
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

        messages = openreview_client.get_messages(to='programchair@tasks.cc', subject='Your request for OpenReview service has been received.')
        assert len(messages) == 1

        request = openreview_client.get_note(request['note']['id'])
        assert openreview_client.get_invitation(f'openreview.net/Support/Venue_Request/Conference_Review_Workflow{request.number}/-/Comment')
        assert openreview.tools.get_group(openreview_client, 'Tasks.cc/2025/Conference/Program_Chairs') is None
        assert request.domain == 'openreview.net/Support'

        # deploy the venue
        edit = openreview_client.post_note_edit(invitation=f'openreview.net/Support/Venue_Request/Conference_Review_Workflow/-/Deployment',
            signatures=[support_group_id],
            note=openreview.api.Note(
                id=request.id,
                content={
                    'venue_id': { 'value': 'Tasks.cc/2025/Conference' }
                }
            ))

        helpers.await_queue_edit(openreview_client, edit_id=edit['id'])
        helpers.await_queue_edit(openreview_client, invitation=f'openreview.net/Support/Venue_Request/Conference_Review_Workflow{request.number}/-/Comment', count=1)

        messages = openreview_client.get_messages(subject='Your venue, Tasks 2025, is available in OpenReview')
        assert len(messages) == 1
        assert messages[0]['content']['to'] == 'programchair@tasks.cc'

        helpers.await_queue_edit(openreview_client, 'Tasks.cc/2025/Conference/-/Withdrawal-0-1', count=1)
        helpers.await_queue_edit(openreview_client, 'Tasks.cc/2025/Conference/-/Desk_Rejection-0-1', count=1)
        helpers.await_queue_edit(openreview_client, 'Tasks.cc/2025/Conference/Program_Committee/-/Submission_Group-0-1', count=1)
        helpers.await_queue_edit(openreview_client, 'Tasks.cc/2025/Conference/-/Submission_Change_Before_Bidding-0-1', count=1)

        venue_group = openreview.tools.get_group(openreview_client, 'Tasks.cc/2025/Conference')
        assert venue_group and venue_group.content['reviewers_recruitment_id']['value'] == 'Tasks.cc/2025/Conference/Program_Committee/-/Recruitment_Response'
        assert all(key in venue_group.content for key in ['reviewers_declined_id', 'reviewers_invited_id', 'reviewers_invited_message_id'])

        request_note = openreview_client.get_note(request.id)
        assert request_note.domain == 'openreview.net/Support'

        group = openreview.tools.get_group(openreview_client, 'Tasks.cc/2025/Conference')
        assert group.members == ['openreview.net/Template', 'Tasks.cc/2025/Conference/Program_Chairs', 'Tasks.cc/2025/Conference/Automated_Administrator']
        assert 'request_form_id' in group.content and group.content['request_form_id']['value'] == request.id

        assert 'preferred_emails_groups' in group.content and group.content['preferred_emails_groups']['value'] == [
            'Tasks.cc/2025/Conference/Program_Committee',
            'Tasks.cc/2025/Conference/Authors'
        ]

        group = openreview.tools.get_group(openreview_client, 'Tasks.cc/2025/Conference/Program_Chairs')
        assert group.members == ['programchair@tasks.cc']
        assert group.domain == 'Tasks.cc/2025/Conference'

        group = openreview.tools.get_group(openreview_client, 'Tasks.cc/2025/Conference/Automated_Administrator')
        assert not group.members
        assert group.domain == 'Tasks.cc/2025/Conference'

        group = openreview.tools.get_group(openreview_client, 'Tasks.cc/2025/Conference/Program_Committee')
        assert group.domain == 'Tasks.cc/2025/Conference'
        assert group.readers == ['Tasks.cc/2025/Conference', 'Tasks.cc/2025/Conference/Program_Committee']

        group = openreview.tools.get_group(openreview_client, 'Tasks.cc/2025/Conference/Program_Committee/Invited')
        assert group.domain == 'Tasks.cc/2025/Conference'

        group = openreview.tools.get_group(openreview_client, 'Tasks.cc/2025/Conference/Program_Committee/Declined')
        assert group.domain == 'Tasks.cc/2025/Conference'

        group = openreview.tools.get_group(openreview_client, 'Tasks.cc/2025/Conference/Area_Chairs')
        assert not group

        group = openreview.tools.get_group(openreview_client, 'Tasks.cc/2025/Conference/Authors')
        assert group.domain == 'Tasks.cc/2025/Conference'

        group = openreview.tools.get_group(openreview_client, 'Tasks.cc/2025/Conference/Authors/Accepted')
        assert group.domain == 'Tasks.cc/2025/Conference'

        invitation = openreview_client.get_invitation('Tasks.cc/2025/Conference/-/Edit')
        assert 'group_edit_script' in invitation.content
        assert 'invitation_edit_script' in invitation.content

        submission_inv = openreview_client.get_invitation('Tasks.cc/2025/Conference/-/Submission')
        assert submission_inv and submission_inv.cdate == openreview.tools.datetime_millis(start_date)
        assert submission_inv.duedate == openreview.tools.datetime_millis(due_date)
        assert submission_inv.expdate == submission_inv.duedate + (30*60*1000)

        form_fields_inv = openreview_client.get_invitation('Tasks.cc/2025/Conference/-/Submission/Form_Fields')
        assert form_fields_inv.duedate == submission_inv.cdate - (30*60*1000)

        assert openreview_client.get_invitation('Tasks.cc/2025/Conference/-/Official_Review')
        assert openreview_client.get_invitation('Tasks.cc/2025/Conference/-/Decision')
        assert openreview_client.get_invitation('Tasks.cc/2025/Conference/-/Withdrawal')
        assert openreview_client.get_invitation('Tasks.cc/2025/Conference/-/Desk_Rejection')

    def test_redeploy_with_past_dates(self, openreview_client, helpers):

        submission_inv = openreview_client.get_invitation('Tasks.cc/2025/Conference/-/Submission')
        start_date = submission_inv.cdate

        super_id = 'openreview.net'
        support_group_id = super_id + '/Support'

        venue_group = openreview.tools.get_group(openreview_client, 'Tasks.cc/2025/Conference')
        request_id = venue_group.content['request_form_id']['value']
        request = openreview_client.get_note(request_id)

        # edit invitation to allow redeployment
        openreview_client.post_invitation_edit(
            invitations='openreview.net/Support/-/Edit',
            signatures=['~Super_User1'],
            invitation=openreview.api.Invitation(
                id = 'openreview.net/Support/Venue_Request/Conference_Review_Workflow/-/Deployment',
                edit = {
                    'note': {
                        'content': {
                            'redeployment': {
                                'value': {
                                    'param':{
                                        'type': 'boolean',
                                        'enum': [True, False],
                                        'input': 'radio',
                                        'optional': True
                                    }
                                }
                            }
                        }
                    }
                }
            )
        )

        # update request form with past dates
        now = datetime.datetime.now()
        past_start_date = now - datetime.timedelta(days=5)
        past_due_date = now - datetime.timedelta(days=1)

        openreview_client.post_note_edit(
            invitation='openreview.net/Support/-/Edit',
            signatures=['~Super_User1'],
            note=openreview.api.Note(
                id=request.id,
                content={
                    'submission_start_date': { 'value': openreview.tools.datetime_millis(past_start_date) },
                    'submission_deadline': { 'value': openreview.tools.datetime_millis(past_due_date) },
                }
            ))

        # re-deploy the venue with past dates
        edit = openreview_client.post_note_edit(
            invitation=f'openreview.net/Support/Venue_Request/Conference_Review_Workflow/-/Deployment',
            signatures=[support_group_id],
            note=openreview.api.Note(
                id=request.id,
                content={
                    'venue_id': { 'value': 'Tasks.cc/2025/Conference' },
                    'redeployment': { 'value': True }
                }
            ))

        helpers.await_queue_edit(openreview_client, edit_id=edit['id'])

        venue_group = openreview.tools.get_group(openreview_client, 'Tasks.cc/2025/Conference')
        assert venue_group and venue_group.content['reviewers_recruitment_id']['value'] == 'Tasks.cc/2025/Conference/Program_Committee/-/Recruitment_Response'

        submission_inv = openreview_client.get_invitation('Tasks.cc/2025/Conference/-/Submission')
        assert submission_inv and submission_inv.cdate == openreview.tools.datetime_millis(past_start_date)
        assert submission_inv.duedate == openreview.tools.datetime_millis(past_due_date)
        assert submission_inv.expdate == submission_inv.duedate + (30*60*1000)

        # duedate should still be based on the original submission start date, not the updated one
        original_form_fields_duedate = openreview.tools.datetime_millis(start_date) - (30*60*1000)
        form_fields_inv = openreview_client.get_invitation('Tasks.cc/2025/Conference/-/Submission/Form_Fields')
        assert form_fields_inv.duedate != submission_inv.cdate - (30*60*1000)
        assert form_fields_inv.duedate == original_form_fields_duedate
