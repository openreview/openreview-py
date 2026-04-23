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

class TestRegistrationStep():

    def test_setup(self, openreview_client, helpers):
        super_id = 'openreview.net'
        support_group_id = super_id + '/Support'

        helpers.create_user('programchair@wxyz.cc', 'ProgramChair', 'WXYZ')
        helpers.create_user('reviewer_one@wxyz.cc', 'ReviewerOne', 'WXYZ')
        helpers.create_user('reviewer_two@wxyz.cc', 'ReviewerTwo', 'WXYZ')
        helpers.create_user('reviewer_three@wxyz.cc', 'ReviewerThree', 'WXYZ')
        helpers.create_user('areachair_one@wxyz.cc', 'ACOne', 'WXYZ')
        helpers.create_user('areachair_two@wxyz.cc', 'ACTwo', 'WXYZ')
        helpers.create_user('areachair_three@wxyz.cc', 'ACThree', 'WXYZ')
        pc_client=openreview.api.OpenReviewClient(username='programchair@wxyz.cc', password=helpers.strong_password)

        assert openreview_client.get_invitation('openreview.net/-/Edit')
        assert openreview_client.get_group('openreview.net/Support/Venue_Request')
        assert openreview_client.get_invitation('openreview.net/Support/Venue_Request/-/Conference_Review_Workflow')
        assert openreview_client.get_invitation('openreview.net/Support/Venue_Request/Conference_Review_Workflow/-/Deployment')
        assert openreview_client.get_invitation('openreview.net/Support/Venue_Request/Conference_Review_Workflow/-/Comment')

        now = datetime.datetime.now()
        due_date = now + datetime.timedelta(days=2)

        request = pc_client.post_note_edit(invitation='openreview.net/Support/Venue_Request/-/Conference_Review_Workflow',
            signatures=['~ProgramChair_WXYZ1'],
            note=openreview.api.Note(
                content={
                    'official_venue_name': { 'value': 'The WXYZ Conference' },
                    'abbreviated_venue_name': { 'value': 'WXYZ 2025' },
                    'venue_website_url': { 'value': 'https://wxyz.cc/Conferences/2025' },
                    'location': { 'value': 'Minnetonka, Minnesota' },
                    'venue_start_date': { 'value': openreview.tools.datetime_millis(now + datetime.timedelta(weeks=52)) },
                    'program_chair_emails': { 'value': ['programchair@wxyz.cc'] },
                    'contact_email': { 'value': 'wxyz2025.programchairs@gmail.com' },
                    'submission_start_date': { 'value': openreview.tools.datetime_millis(now) },
                    'submission_deadline': { 'value': openreview.tools.datetime_millis(due_date) },
                    'reviewer_groups_names': { 'value': ['Reviewers'] },
                    'area_chairs_support': { 'value': True },
                    'area_chair_groups_names': { 'value': ['Action_Editors'] },
                    'expected_submissions': { 'value': 500 },
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
        assert request.domain == 'openreview.net/Support'
        assert openreview_client.get_invitation(f'openreview.net/Support/Venue_Request/Conference_Review_Workflow{request.number}/-/Comment')
        assert openreview.tools.get_group(openreview_client, 'WXYZ.cc/2025/Conference/Program_Chairs') is None

        # deploy the venue
        edit = openreview_client.post_note_edit(invitation=f'openreview.net/Support/Venue_Request/Conference_Review_Workflow/-/Deployment',
            signatures=[support_group_id],
            note=openreview.api.Note(
                id=request.id,
                content={
                    'venue_id': { 'value': 'WXYZ.cc/2025/Conference' }
                }
            ))

        helpers.await_queue_edit(openreview_client, edit_id=edit['id'])

        helpers.await_queue_edit(openreview_client, 'WXYZ.cc/2025/Conference/-/Withdrawal-0-1', count=1)
        helpers.await_queue_edit(openreview_client, 'WXYZ.cc/2025/Conference/-/Desk_Rejection-0-1', count=1)
        helpers.await_queue_edit(openreview_client, 'WXYZ.cc/2025/Conference/Reviewers/-/Submission_Group-0-1', count=1)
        helpers.await_queue_edit(openreview_client, 'WXYZ.cc/2025/Conference/Action_Editors/-/Submission_Group-0-1', count=1)
        helpers.await_queue_edit(openreview_client, 'WXYZ.cc/2025/Conference/-/Submission_Change_Before_Bidding-0-1', count=1)

        #after deployment, check domain hasn't changed
        request_note = openreview_client.get_note(request.id)
        assert request_note.domain == 'openreview.net/Support'

        openreview_client.flush_members_cache('~ProgramChair_WXYZ1')
        group = openreview.tools.get_group(openreview_client, 'WXYZ.cc/2025/Conference')
        assert group.members == ['openreview.net/Template', 'WXYZ.cc/2025/Conference/Program_Chairs', 'WXYZ.cc/2025/Conference/Automated_Administrator']
        assert 'request_form_id' in group.content and group.content['request_form_id']['value'] == request.id

    def test_enable_registration_step(self, openreview_client, helpers):

        venue = openreview.helpers.get_venue(openreview_client, 'WXYZ.cc/2025/Conference', 'openreview.net/Support')

        committee_id = venue.get_area_chairs_id()
        committee_name = venue.get_committee_name(committee_id, pretty=True)

        venue.registration_stages = [openreview.stages.RegistrationStage(
            committee_id = committee_id,
            name='Registration',
            title=f'{committee_name} Registration',
            instructions='To complete your registration, please click the button below and fill out the form.',
        )]

        venue.create_registration_stages()

        inv = openreview_client.get_invitation('WXYZ.cc/2025/Conference/Action_Editors/-/Registration_Form')
        assert inv

        inv = openreview_client.get_invitation(f'WXYZ.cc/2025/Conference/Action_Editors/-/Registration')
        assert inv

    def test_edit_registration_dates_and_fields(self, openreview_client, helpers):

        pc_client = openreview.api.OpenReviewClient(username='programchair@wxyz.cc', password=helpers.strong_password)

        # check Dates and Form_Fields invitations exist
        assert pc_client.get_invitation('WXYZ.cc/2025/Conference/Action_Editors/-/Registration/Dates')
        assert pc_client.get_invitation('WXYZ.cc/2025/Conference/Action_Editors/-/Registration/Form_Fields')

        # edit due date and exp date using Dates invitation
        registration_inv = pc_client.get_invitation('WXYZ.cc/2025/Conference/Action_Editors/-/Registration')
        assert not registration_inv.duedate
        assert not registration_inv.expdate

        activation_date = registration_inv.cdate
        now = datetime.datetime.now()
        new_due_date = openreview.tools.datetime_millis(now + datetime.timedelta(days=10))
        new_exp_date = openreview.tools.datetime_millis(now + datetime.timedelta(days=13))

        edit = pc_client.post_invitation_edit(
            invitations='WXYZ.cc/2025/Conference/Action_Editors/-/Registration/Dates',
            content={
                'activation_date': { 'value': activation_date },
                'due_date': { 'value': new_due_date },
                'expiration_date': { 'value': new_exp_date }
            }
        )

        registration_inv = openreview_client.get_invitation('WXYZ.cc/2025/Conference/Action_Editors/-/Registration')
        assert registration_inv.duedate == new_due_date
        assert registration_inv.expdate == new_exp_date

        # edit form fields using Form_Fields invitation
        edit = pc_client.post_invitation_edit(
            invitations='WXYZ.cc/2025/Conference/Action_Editors/-/Registration/Form_Fields',
            content={
                'content': {
                    'value': {
                        'statement': {
                            'order': 3,
                            'description': 'Please write a short statement about why you think peer review is important.',
                            'value': {
                                'param': {
                                    'type': 'string',
                                    'input': 'textarea',
                                    'maxLength': 200000
                                }
                            }
                        }
                    }
                }
            }
        )

        registration_inv = openreview_client.get_invitation('WXYZ.cc/2025/Conference/Action_Editors/-/Registration')
        assert 'profile_confirmed' in registration_inv.edit['note']['content']
        assert 'expertise_confirmed' in registration_inv.edit['note']['content']
        assert 'statement' in registration_inv.edit['note']['content']
