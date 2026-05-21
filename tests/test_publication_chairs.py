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

class TestPublicationChairs():

    def test_setup(self, openreview_client, helpers):
        super_id = 'openreview.net'
        support_group_id = super_id + '/Support'

        helpers.create_user('programchair@pubchairs.cc', 'ProgramChair', 'PubChairs')
        helpers.create_user('publicationchair@pubchairs.cc', 'PublicationChair', 'PubChairs')
        pc_client=openreview.api.OpenReviewClient(username='programchair@pubchairs.cc', password=helpers.strong_password)

        helpers.create_user('author_one@pubchairs.cc', 'AuthorOne', 'PubChairs')

        assert openreview_client.get_invitation('openreview.net/-/Edit')
        assert openreview_client.get_group('openreview.net/Support/Venue_Request')
        assert openreview_client.get_invitation('openreview.net/Support/Venue_Request/-/Conference_Review_Workflow')
        assert openreview_client.get_invitation('openreview.net/Support/Venue_Request/Conference_Review_Workflow/-/Comment')
        assert openreview_client.get_invitation('openreview.net/Support/Venue_Request/Conference_Review_Workflow/-/Deployment')
        assert openreview_client.get_invitation('openreview.net/Support/Venue_Request/Conference_Review_Workflow/-/Status')

        now = datetime.datetime.now()
        start_date = now - datetime.timedelta(days=1)
        due_date = now + datetime.timedelta(days=2)

        request = pc_client.post_note_edit(invitation='openreview.net/Support/Venue_Request/-/Conference_Review_Workflow',
            signatures=['~ProgramChair_PubChairs1'],
            note=openreview.api.Note(
                content={
                    'official_venue_name': { 'value': 'The Publication Chairs Conference' },
                    'abbreviated_venue_name': { 'value': 'PubChairs 2025' },
                    'venue_website_url': { 'value': 'https://pubchairs.cc/Conferences/2025' },
                    'location': { 'value': 'Amherst, Massachusetts' },
                    'venue_start_date': { 'value': openreview.tools.datetime_millis(now + datetime.timedelta(weeks=52)) },
                    'program_chair_emails': { 'value': ['programchair@pubchairs.cc'] },
                    'contact_email': { 'value': 'pubchairs2025.programchairs@gmail.com' },
                    'submission_start_date': { 'value': openreview.tools.datetime_millis(start_date) },
                    'submission_deadline': { 'value': openreview.tools.datetime_millis(due_date) },
                    'reviewer_groups_names': { 'value': ['Program_Committee'] },
                    'area_chair_groups_names': { 'value': ['Area_Chairs'] },
                    'senior_area_chair_groups_names': { 'value': ['Senior_Area_Chairs'] },
                    'publication_chairs_support': { 'value': True },
                    'colocated': { 'value': 'Independent' },
                    'previous_venue': { 'value': 'PubChairs.cc/2024/Conference' },
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

        messages = openreview_client.get_messages(to='programchair@pubchairs.cc', subject='Your request for OpenReview service has been received.')
        assert len(messages) == 1

        request = openreview_client.get_note(request['note']['id'])
        assert openreview_client.get_invitation(f'openreview.net/Support/Venue_Request/Conference_Review_Workflow{request.number}/-/Comment')
        assert openreview.tools.get_group(openreview_client, 'PubChairs.cc/2025/Conference/Program_Chairs') is None
        assert request.domain == 'openreview.net/Support'

        # deploy the venue
        edit = openreview_client.post_note_edit(invitation=f'openreview.net/Support/Venue_Request/Conference_Review_Workflow/-/Deployment',
            signatures=[support_group_id],
            note=openreview.api.Note(
                id=request.id,
                content={
                    'venue_id': { 'value': 'PubChairs.cc/2025/Conference' }
                }
            ))

        helpers.await_queue_edit(openreview_client, edit_id=edit['id'])
        helpers.await_queue_edit(openreview_client, invitation=f'openreview.net/Support/Venue_Request/Conference_Review_Workflow{request.number}/-/Comment', count=1)

        assert openreview_client.get_invitation(f'openreview.net/Support/Venue_Request/Conference_Review_Workflow{request.number}/-/Feedback')

        messages = openreview_client.get_messages(subject='Your venue, PubChairs 2025, is available in OpenReview')
        assert len(messages) == 1
        assert messages[0]['content']['to'] == 'programchair@pubchairs.cc'

        helpers.await_queue_edit(openreview_client, 'PubChairs.cc/2025/Conference/-/Withdrawal-0-1', count=1)
        helpers.await_queue_edit(openreview_client, 'PubChairs.cc/2025/Conference/-/Desk_Rejection-0-1', count=1)
        helpers.await_queue_edit(openreview_client, 'PubChairs.cc/2025/Conference/Program_Committee/-/Submission_Group-0-1', count=1)
        helpers.await_queue_edit(openreview_client, 'PubChairs.cc/2025/Conference/-/Submission_Change_Before_Bidding-0-1', count=1)

        venue_group = openreview.tools.get_group(openreview_client, 'PubChairs.cc/2025/Conference')
        assert venue_group and venue_group.content['reviewers_recruitment_id']['value'] == 'PubChairs.cc/2025/Conference/Program_Committee/-/Recruitment_Response'
        assert all(key in venue_group.content for key in ['reviewers_declined_id', 'reviewers_invited_id', 'reviewers_invited_message_id'])

        request_note = openreview_client.get_note(request.id)
        assert request_note.domain == 'openreview.net/Support'

        group = openreview.tools.get_group(openreview_client, 'PubChairs.cc/2025/Conference')
        assert group.members == ['openreview.net/Template', 'PubChairs.cc/2025/Conference/Program_Chairs', 'PubChairs.cc/2025/Conference/Automated_Administrator']
        assert 'request_form_id' in group.content and group.content['request_form_id']['value'] == request.id

        # publication chairs group id is registered in the venue group content
        assert 'publication_chairs_id' in group.content
        assert group.content['publication_chairs_id']['value'] == 'PubChairs.cc/2025/Conference/Publication_Chairs'

        # publication chairs are included in the preferred emails groups
        assert 'preferred_emails_groups' in group.content and group.content['preferred_emails_groups']['value'] == [
            'PubChairs.cc/2025/Conference/Program_Committee',
            'PubChairs.cc/2025/Conference/Authors',
            'PubChairs.cc/2025/Conference/Publication_Chairs'
        ]

        group = openreview.tools.get_group(openreview_client, 'PubChairs.cc/2025/Conference/Program_Chairs')
        assert group.members == ['programchair@pubchairs.cc']
        assert group.domain == 'PubChairs.cc/2025/Conference'

        # publication chairs group is created during deployment
        group = openreview.tools.get_group(openreview_client, 'PubChairs.cc/2025/Conference/Publication_Chairs')
        assert group
        assert group.domain == 'PubChairs.cc/2025/Conference'
        assert group.readers == ['everyone']
        assert group.writers == ['PubChairs.cc/2025/Conference', 'PubChairs.cc/2025/Conference/Publication_Chairs']
        assert group.signatories == ['PubChairs.cc/2025/Conference/Publication_Chairs', 'PubChairs.cc/2025/Conference']
        assert not group.members
        assert group.web

        openreview_client.add_members_to_group('PubChairs.cc/2025/Conference/Publication_Chairs', '~PublicationChair_PubChairs1')

        group = openreview.tools.get_group(openreview_client, 'PubChairs.cc/2025/Conference/Automated_Administrator')
        assert not group.members
        assert group.domain == 'PubChairs.cc/2025/Conference'

        group = openreview.tools.get_group(openreview_client, 'PubChairs.cc/2025/Conference/Program_Committee')
        assert group.domain == 'PubChairs.cc/2025/Conference'
        assert group.readers == ['PubChairs.cc/2025/Conference', 'PubChairs.cc/2025/Conference/Program_Committee']

        group = openreview.tools.get_group(openreview_client, 'PubChairs.cc/2025/Conference/Authors')
        assert group.domain == 'PubChairs.cc/2025/Conference'

        group = openreview.tools.get_group(openreview_client, 'PubChairs.cc/2025/Conference/Authors/Accepted')
        assert group.domain == 'PubChairs.cc/2025/Conference'
        # accepted authors group is readable by the publication chairs
        assert 'PubChairs.cc/2025/Conference/Publication_Chairs' in group.readers

        # the publication chair role invitation is created during deployment
        role_invitation = openreview_client.get_invitation('PubChairs.cc/2025/Conference/-/Publication_Chair')
        assert role_invitation

    def test_submissions(self, openreview_client, helpers):

        # post 5 submissions to the deployed venue
        author_client = openreview.api.OpenReviewClient(username='author_one@pubchairs.cc', password=helpers.strong_password)

        for i in range(1, 6):
            submission_edit = author_client.post_note_edit(
                invitation='PubChairs.cc/2025/Conference/-/Submission',
                signatures=['~AuthorOne_PubChairs1'],
                note=openreview.api.Note(
                    license='CC BY 4.0',
                    content={
                        'title': { 'value': f'Test Submission {i}' },
                        'abstract': { 'value': f'This is an abstract for submission {i}' },
                        'authors': { 'value': ['AuthorOne PubChairs'] },
                        'authorids': { 'value': ['~AuthorOne_PubChairs1'] },
                        'keywords': { 'value': ['machine learning', 'artificial intelligence'] },
                        'email_sharing': { 'value': 'We authorize the sharing of all author emails with Program Chairs.' },
                        'data_release': { 'value': 'We authorize the release of our submission and author names to the public in the event of acceptance.' },
                        'pdf': {'value': '/pdf/' + 'p' * 40 +'.pdf' },
                    }
                )
            )
            helpers.await_queue_edit(openreview_client, edit_id=submission_edit['id'])

        helpers.await_queue_edit(openreview_client, invitation='PubChairs.cc/2025/Conference/-/Submission', count=5)

        submissions = openreview_client.get_notes(invitation='PubChairs.cc/2025/Conference/-/Submission', sort='number:asc')
        assert len(submissions) == 5
        assert [s.content['title']['value'] for s in submissions] == [f'Test Submission {i}' for i in range(1, 6)]

    def test_decision_stage(self, openreview_client, helpers):

        pc_client = openreview.api.OpenReviewClient(username='programchair@pubchairs.cc', password=helpers.strong_password)

        assert pc_client.get_invitation('PubChairs.cc/2025/Conference/-/Decision')
        assert pc_client.get_invitation('PubChairs.cc/2025/Conference/-/Decision/Dates')

        now = datetime.datetime.now()
        new_cdate = openreview.tools.datetime_millis(now)
        new_duedate = openreview.tools.datetime_millis(now + datetime.timedelta(days=3))

        # move the decision stage dates to the present so per-submission decision invitations are created
        pc_client.post_invitation_edit(
            invitations='PubChairs.cc/2025/Conference/-/Decision/Dates',
            content={
                'activation_date': { 'value': new_cdate },
                'due_date': { 'value': new_duedate },
                'expiration_date': { 'value': new_duedate }
            }
        )
        helpers.await_queue_edit(openreview_client, edit_id='PubChairs.cc/2025/Conference/-/Decision-0-1', count=2)

        decision_invitations = openreview_client.get_invitations(invitation='PubChairs.cc/2025/Conference/-/Decision')
        assert len(decision_invitations) == 5

        submissions = openreview_client.get_notes(invitation='PubChairs.cc/2025/Conference/-/Submission', sort='number:asc')
        assert len(submissions) == 5

        # accept odd numbered submissions, reject even numbered submissions
        for submission in submissions:
            decision = 'Accept (Oral)' if submission.number % 2 == 1 else 'Reject'
            decision_edit = pc_client.post_note_edit(
                invitation=f'PubChairs.cc/2025/Conference/Submission{submission.number}/-/Decision',
                signatures=['PubChairs.cc/2025/Conference/Program_Chairs'],
                note=openreview.api.Note(
                    content={
                        'decision': { 'value': decision }
                    }
                )
            )
            helpers.await_queue_edit(openreview_client, edit_id=decision_edit['id'])

        for submission in submissions:
            decision_notes = openreview_client.get_notes(invitation=f'PubChairs.cc/2025/Conference/Submission{submission.number}/-/Decision')
            assert len(decision_notes) == 1
            expected_decision = 'Accept (Oral)' if submission.number % 2 == 1 else 'Reject'
            assert decision_notes[0].content['decision']['value'] == expected_decision
