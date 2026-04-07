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

class TestSimpleDualAnonymous():

    def test_setup(self, openreview_client, helpers):
        super_id = 'openreview.net'
        support_group_id = super_id + '/Support'

        helpers.create_user('programchair@iclr.cc', 'ProgramChair', 'ICLROne')
        helpers.create_user('reviewer_one@iclr.cc', 'Reviewer', 'ICLROne')
        helpers.create_user('reviewer_two@iclr.cc', 'Reviewer', 'ICLRTwo')
        helpers.create_user('reviewer_three@iclr.cc', 'Reviewer', 'ICLRThree')
        helpers.create_user('areachair_one@iclr.cc', 'AC', 'ICLROne')
        helpers.create_user('areachair_two@iclr.cc', 'AC', 'ICLRTwo')
        helpers.create_user('seniorareachair_one@iclr.cc', 'SAC', 'ICLROne')
        helpers.create_user('seniorareachair_two@iclr.cc', 'SAC', 'ICLRTwo')
        pc_client=openreview.api.OpenReviewClient(username='programchair@iclr.cc', password=helpers.strong_password)

        assert openreview_client.get_invitation('openreview.net/-/Edit')
        assert openreview_client.get_group('openreview.net/Support/Venue_Request')
        assert openreview_client.get_invitation('openreview.net/Support/Venue_Request/-/Conference_Review_Workflow')
        assert openreview_client.get_invitation('openreview.net/Support/Venue_Request/Conference_Review_Workflow/-/Deployment')
        assert openreview_client.get_invitation('openreview.net/Support/Venue_Request/Conference_Review_Workflow/-/Comment')

        now = datetime.datetime.now()
        due_date = now + datetime.timedelta(days=2)

        request = pc_client.post_note_edit(invitation='openreview.net/Support/Venue_Request/-/Conference_Review_Workflow',
            signatures=['~ProgramChair_ICLROne1'],
            note=openreview.api.Note(
                content={
                    'official_venue_name': { 'value': 'International Conference on Learning Representations' },
                    'abbreviated_venue_name': { 'value': 'ICLR 2026' },
                    'venue_website_url': { 'value': 'https://iclr.cc/Conferences/2026' },
                    'location': { 'value': 'Minnetonka, Minnesota' },
                    'venue_start_date': { 'value': openreview.tools.datetime_millis(now + datetime.timedelta(weeks=52)) },
                    'program_chair_emails': { 'value': ['programchair@iclr.cc'] },
                    'contact_email': { 'value': 'iclr2026.programchairs@gmail.com' },
                    'submission_start_date': { 'value': openreview.tools.datetime_millis(now) },
                    'submission_deadline': { 'value': openreview.tools.datetime_millis(due_date) },
                    'reviewers_name': { 'value': 'Reviewers' },
                    'area_chairs_support': { 'value': True },
                    'area_chairs_name': { 'value': 'Action_Editors' },
                    'senior_area_chairs_support': { 'value': True },
                    'senior_area_chairs_name': { 'value': 'Senior_Action_Editors' },
                    'expected_submissions': { 'value': 12000 },
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

        # deploy the venue
        edit = openreview_client.post_note_edit(invitation=f'openreview.net/Support/Venue_Request/Conference_Review_Workflow/-/Deployment',
            signatures=[support_group_id],
            note=openreview.api.Note(
                id=request['note']['id'],
                content={
                    'venue_id': { 'value': 'ICLR.cc/2026/Conference' }
                }
            ))
        
        helpers.await_queue_edit(openreview_client, edit_id=edit['id'])

        group = openreview.tools.get_group(openreview_client, 'ICLR.cc/2026/Conference')

        assert 'preferred_emails_groups' in group.content and group.content['preferred_emails_groups']['value'] == [
            'ICLR.cc/2026/Conference/Reviewers',
            'ICLR.cc/2026/Conference/Authors',
            'ICLR.cc/2026/Conference/Action_Editors',
            'ICLR.cc/2026/Conference/Senior_Action_Editors'
        ]
        assert 'preferred_emails_id' in group.content and group.content['preferred_emails_id']['value'] == 'ICLR.cc/2026/Conference/-/Preferred_Emails'
        invitation = openreview_client.get_invitation('ICLR.cc/2026/Conference/-/Preferred_Emails')
        assert invitation

        assert group.content['senior_area_chair_roles']['value'] == ['Senior_Action_Editors']
        assert group.content['senior_area_chairs_id']['value'] == 'ICLR.cc/2026/Conference/Senior_Action_Editors'
        assert group.content['senior_area_chairs_assignment_id']['value'] == 'ICLR.cc/2026/Conference/Senior_Action_Editors/-/Assignment'
        assert group.content['senior_area_chairs_affinity_score_id']['value'] == 'ICLR.cc/2026/Conference/Senior_Action_Editors/-/Affinity_Score'
        assert group.content['senior_area_chairs_name']['value'] == 'Senior_Action_Editors'
        assert group.content['sac_paper_assignments']['value'] == False
        assert group.content['senior_area_chairs_conflict_id']['value'] == 'ICLR.cc/2026/Conference/Senior_Action_Editors/-/Conflict'

        group = openreview.tools.get_group(openreview_client, 'ICLR.cc/2026/Conference/Senior_Action_Editors')
        assert group.readers == [
            'ICLR.cc/2026/Conference',
            'ICLR.cc/2026/Conference/Senior_Action_Editors'
        ]
        assert group.domain == 'ICLR.cc/2026/Conference'

        group = openreview.tools.get_group(openreview_client, 'ICLR.cc/2026/Conference/Senior_Action_Editors/Invited')
        assert group.readers == [
            'ICLR.cc/2026/Conference',
            'ICLR.cc/2026/Conference/Senior_Action_Editors/Invited'
        ]
        assert group.domain == 'ICLR.cc/2026/Conference'

        group = openreview.tools.get_group(openreview_client, 'ICLR.cc/2026/Conference/Senior_Action_Editors/Declined')
        assert group.readers == [
            'ICLR.cc/2026/Conference',
            'ICLR.cc/2026/Conference/Senior_Action_Editors/Declined'
        ]
        assert group.domain == 'ICLR.cc/2026/Conference'

        assert openreview.tools.get_invitation(openreview_client, 'ICLR.cc/2026/Conference/Senior_Action_Editors/-/Message')
        assert openreview.tools.get_invitation(openreview_client, 'ICLR.cc/2026/Conference/Senior_Action_Editors/-/Members')

        submission_invitation = openreview_client.get_invitation('ICLR.cc/2026/Conference/-/Submission')
        assert submission_invitation
        assert submission_invitation.duedate

        assert openreview_client.get_invitation('ICLR.cc/2026/Conference/Reviewers/-/Expertise_Selection')
        assert openreview_client.get_invitation('ICLR.cc/2026/Conference/Action_Editors/-/Expertise_Selection')
        assert openreview_client.get_invitation('ICLR.cc/2026/Conference/Senior_Action_Editors/-/Expertise_Selection')