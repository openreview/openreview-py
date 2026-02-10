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

class TestAbstractDeadline():

    def test_setup(self, openreview_client, helpers):

        super_id = 'openreview.net'
        support_group_id = super_id + '/Support'

        helpers.create_user('programchair@emas.cc', 'ProgramChair', 'EMAS')
        helpers.create_user('author_one@emas.cc', 'AuthorOne', 'EMAS')
        pc_client=openreview.api.OpenReviewClient(username='programchair@emas.cc', password=helpers.strong_password)

        now = datetime.datetime.now()
        due_date = now + datetime.timedelta(days=2)
        full_submission_due_date = due_date + datetime.timedelta(days=4)

        request = pc_client.post_note_edit(invitation='openreview.net/Support/Venue_Request/-/Conference_Review_Workflow',
            signatures=['~ProgramChair_EMAS1'],
            note=openreview.api.Note(
                content={
                    'official_venue_name': { 'value': '14th International Workshop on Engineering Multi-Agent Systems' },
                    'abbreviated_venue_name': { 'value': 'EMAS 2026' },
                    'venue_website_url': { 'value': 'https://emas.cc/Conferences/2026' },
                    'location': { 'value': 'Paphos, Cyprus' },
                    'venue_start_date': { 'value': openreview.tools.datetime_millis(now + datetime.timedelta(weeks=52)) },
                    'program_chair_emails': { 'value': ['programchair@emas.cc'] },
                    'contact_email': { 'value': 'emas2026.programchairs@gmail.com' },
                    'submission_start_date': { 'value': openreview.tools.datetime_millis(now - datetime.timedelta(days=1)) },
                    'submission_deadline': { 'value': openreview.tools.datetime_millis(due_date) },
                    'full_submission_deadline': { 'value': openreview.tools.datetime_millis(full_submission_due_date) },
                    'reviewers_name': { 'value': 'Reviewers' },
                    'area_chairs_name': { 'value': 'Area_Chairs' },
                    'expected_submissions': { 'value': 20 },
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
                    'venue_id': { 'value': 'ifaamas.org/AAMAS/2026/Workshop/EMAS' }
                }
            ))

        helpers.await_queue_edit(openreview_client, edit_id=edit['id'])

        helpers.await_queue_edit(openreview_client, 'ifaamas.org/AAMAS/2026/Workshop/EMAS/-/Withdrawal-0-1', count=1)
        helpers.await_queue_edit(openreview_client, 'ifaamas.org/AAMAS/2026/Workshop/EMAS/-/Desk_Rejection-0-1', count=1)
        helpers.await_queue_edit(openreview_client, 'ifaamas.org/AAMAS/2026/Workshop/EMAS/-/Full_Submission-0-1', count=1)
        helpers.await_queue_edit(openreview_client, 'ifaamas.org/AAMAS/2026/Workshop/EMAS/Reviewers/-/Submission_Group-0-1', count=1)
        helpers.await_queue_edit(openreview_client, 'ifaamas.org/AAMAS/2026/Workshop/EMAS/-/Submission_Change_Before_Bidding-0-1', count=1)

        group = openreview.tools.get_group(openreview_client, 'ifaamas.org/AAMAS/2026/Workshop/EMAS/Program_Chairs')
        assert group.members == ['programchair@emas.cc']
        assert group.domain == 'ifaamas.org/AAMAS/2026/Workshop/EMAS'

        domain_group = openreview_client.get_group('ifaamas.org/AAMAS/2026/Workshop/EMAS')
        assert 'full_submission_invitation_id' in domain_group.content and domain_group.content['full_submission_invitation_id']['value'] == 'ifaamas.org/AAMAS/2026/Workshop/EMAS/-/Full_Submission'

        submission_inv = openreview_client.get_invitation('ifaamas.org/AAMAS/2026/Workshop/EMAS/-/Submission')
        assert submission_inv and submission_inv.cdate == openreview.tools.datetime_millis(now - datetime.timedelta(days=1))
        assert submission_inv.duedate == openreview.tools.datetime_millis(due_date)
        assert submission_inv.expdate == submission_inv.duedate + (30*60*1000)
        submission_deadline_inv = openreview_client.get_invitation('ifaamas.org/AAMAS/2026/Workshop/EMAS/-/Submission/Dates')
        assert submission_deadline_inv and submission_inv.id in submission_deadline_inv.edit['invitation']['id']
        assert openreview_client.get_invitation('ifaamas.org/AAMAS/2026/Workshop/EMAS/-/Submission/Form_Fields')
        assert openreview_client.get_invitation('ifaamas.org/AAMAS/2026/Workshop/EMAS/-/Submission/Notifications')

        full_submission_inv = openreview_client.get_invitation('ifaamas.org/AAMAS/2026/Workshop/EMAS/-/Full_Submission')
        assert full_submission_inv and full_submission_inv.edit['invitation']['cdate'] == submission_inv.expdate
        assert full_submission_inv.edit['invitation']['duedate'] == openreview.tools.datetime_millis(full_submission_due_date)
        assert full_submission_inv.edit['invitation']['expdate'] == full_submission_inv.edit['invitation']['duedate'] + (30*60*1000)

        deletion_invitation = openreview_client.get_invitation('ifaamas.org/AAMAS/2026/Workshop/EMAS/-/Deletion')
        assert deletion_invitation and deletion_invitation.edit['invitation']['cdate'] == submission_inv.expdate
        assert not 'duedate' in deletion_invitation.edit['invitation']
        assert deletion_invitation.edit['invitation']['expdate'] == full_submission_inv.edit['invitation']['duedate'] + (30*60*1000)

        post_submission_inv = openreview_client.get_invitation('ifaamas.org/AAMAS/2026/Workshop/EMAS/-/Submission_Change_Before_Bidding')
        assert post_submission_inv and post_submission_inv.cdate == full_submission_inv.edit['invitation']['expdate']
        assert post_submission_inv.edit['note']['readers'] == [
            'ifaamas.org/AAMAS/2026/Workshop/EMAS',
            'ifaamas.org/AAMAS/2026/Workshop/EMAS/Reviewers',
            'ifaamas.org/AAMAS/2026/Workshop/EMAS/Submission${{2/id}/number}/Authors'
        ]

        invitation = openreview_client.get_invitation('ifaamas.org/AAMAS/2026/Workshop/EMAS/Reviewers/-/Submission_Group')
        assert invitation and invitation.edit['group']['deanonymizers'] == ['ifaamas.org/AAMAS/2026/Workshop/EMAS']
        assert invitation.cdate == full_submission_inv.edit['invitation']['expdate']
        assert openreview_client.get_invitation('ifaamas.org/AAMAS/2026/Workshop/EMAS/Reviewers/-/Submission_Group/Dates')
        assert openreview_client.get_invitation('ifaamas.org/AAMAS/2026/Workshop/EMAS/Reviewers/-/Submission_Group/Deanonymizers')

        assert openreview_client.get_invitation('ifaamas.org/AAMAS/2026/Workshop/EMAS/-/Submission_Change_Before_Bidding')
        assert openreview_client.get_invitation('ifaamas.org/AAMAS/2026/Workshop/EMAS/-/Submission_Change_Before_Reviewing')
        assert openreview_client.get_invitation('ifaamas.org/AAMAS/2026/Workshop/EMAS/-/Official_Review')
        assert openreview_client.get_invitation('ifaamas.org/AAMAS/2026/Workshop/EMAS/-/Official_Review_Release')
        assert openreview_client.get_invitation('ifaamas.org/AAMAS/2026/Workshop/EMAS/-/Decision')
        assert openreview_client.get_invitation('ifaamas.org/AAMAS/2026/Workshop/EMAS/-/Decision_Release')
        assert openreview_client.get_invitation('ifaamas.org/AAMAS/2026/Workshop/EMAS/-/Camera_Ready_Revision')
        assert openreview_client.get_invitation('ifaamas.org/AAMAS/2026/Workshop/EMAS/-/Withdrawal')
        assert openreview_client.get_invitation('ifaamas.org/AAMAS/2026/Workshop/EMAS/-/Withdrawn_Submission')
        assert openreview_client.get_invitation('ifaamas.org/AAMAS/2026/Workshop/EMAS/-/Withdraw_Expiration')
        assert openreview_client.get_invitation('ifaamas.org/AAMAS/2026/Workshop/EMAS/-/Withdrawal_Reversion')
        assert openreview_client.get_invitation('ifaamas.org/AAMAS/2026/Workshop/EMAS/-/Desk_Rejection')
        assert openreview_client.get_invitation('ifaamas.org/AAMAS/2026/Workshop/EMAS/-/Desk_Rejected_Submission')
        assert openreview_client.get_invitation('ifaamas.org/AAMAS/2026/Workshop/EMAS/-/Desk_Reject_Expiration')
        assert openreview_client.get_invitation('ifaamas.org/AAMAS/2026/Workshop/EMAS/-/Desk_Rejection_Reversion')
        assert openreview_client.get_invitation('ifaamas.org/AAMAS/2026/Workshop/EMAS/Reviewers/-/Bid')
        assert openreview_client.get_invitation('ifaamas.org/AAMAS/2026/Workshop/EMAS/-/Venue_Information')
        assert openreview_client.get_invitation('ifaamas.org/AAMAS/2026/Workshop/EMAS/-/Author_Reviews_Notification')
        assert openreview_client.get_invitation('ifaamas.org/AAMAS/2026/Workshop/EMAS/-/Author_Decision_Notification')

    def test_update_submission_deadline(self, openreview_client, helpers):

        pc_client=openreview.api.OpenReviewClient(username='programchair@emas.cc', password=helpers.strong_password)

        # extend submission deadline
        now = datetime.datetime.now()
        new_duedate = openreview.tools.datetime_millis(now + datetime.timedelta(days=3))

        submission_inv = pc_client.get_invitation('ifaamas.org/AAMAS/2026/Workshop/EMAS/-/Submission')

        # extend Submission duedate with Submission/Deadline invitation
        edit = pc_client.post_invitation_edit(
            invitations='ifaamas.org/AAMAS/2026/Workshop/EMAS/-/Submission/Dates',
            content={
                'activation_date': { 'value': submission_inv.cdate },
                'due_date': { 'value': new_duedate }
            }
        )

        helpers.await_queue_edit(openreview_client, edit_id=edit['id'])
        helpers.await_queue_edit(openreview_client, 'ifaamas.org/AAMAS/2026/Workshop/EMAS/-/Full_Submission-0-1', count=2)

        full_submission_inv = pc_client.get_invitation('ifaamas.org/AAMAS/2026/Workshop/EMAS/-/Full_Submission')
        assert full_submission_inv.edit['invitation']['cdate'] == new_duedate + (30*60*1000)

        # assert other invitations were not changed
        withdrawal_invitation = pc_client.get_invitation('ifaamas.org/AAMAS/2026/Workshop/EMAS/-/Withdrawal')
        assert withdrawal_invitation.edit['invitation']['cdate'] == full_submission_inv.edit['invitation']['expdate']

        desk_rejection_invitation = pc_client.get_invitation('ifaamas.org/AAMAS/2026/Workshop/EMAS/-/Desk_Rejection')
        assert desk_rejection_invitation.edit['invitation']['cdate'] == full_submission_inv.edit['invitation']['expdate']

        submission_group_invitation = pc_client.get_invitation('ifaamas.org/AAMAS/2026/Workshop/EMAS/Reviewers/-/Submission_Group')
        assert submission_group_invitation.cdate == full_submission_inv.edit['invitation']['expdate']

        post_submission_inv = pc_client.get_invitation('ifaamas.org/AAMAS/2026/Workshop/EMAS/-/Submission_Change_Before_Bidding')
        assert post_submission_inv.cdate == full_submission_inv.edit['invitation']['expdate']

        deletion_invitation = pc_client.get_invitation('ifaamas.org/AAMAS/2026/Workshop/EMAS/-/Deletion')
        assert deletion_invitation.edit['invitation']['cdate'] == full_submission_inv.edit['invitation']['cdate']
        assert deletion_invitation.edit['invitation']['expdate'] == full_submission_inv.edit['invitation']['expdate']

    def test_update_full_submission_deadline(self, openreview_client, helpers):

        pc_client=openreview.api.OpenReviewClient(username='programchair@emas.cc', password=helpers.strong_password)

        # extend full submission deadline
        now = datetime.datetime.now()
        new_duedate = openreview.tools.datetime_millis(now + datetime.timedelta(days=6))
        new_expdate = new_duedate + (30*60*1000)

        edit = pc_client.post_invitation_edit(
            invitations='ifaamas.org/AAMAS/2026/Workshop/EMAS/-/Full_Submission/Dates',
            content={
                'due_date': { 'value': new_duedate },
                'expiration_date': { 'value': new_expdate }
            }
        )

        helpers.await_queue_edit(openreview_client, edit_id=edit['id'])
        helpers.await_queue_edit(openreview_client, 'ifaamas.org/AAMAS/2026/Workshop/EMAS/-/Full_Submission-0-1', count=3)
        helpers.await_queue_edit(openreview_client, 'ifaamas.org/AAMAS/2026/Workshop/EMAS/-/Withdrawal-0-1', count=2)
        helpers.await_queue_edit(openreview_client, 'ifaamas.org/AAMAS/2026/Workshop/EMAS/-/Desk_Rejection-0-1', count=2)
        helpers.await_queue_edit(openreview_client, 'ifaamas.org/AAMAS/2026/Workshop/EMAS/Reviewers/-/Submission_Group-0-1', count=2)
        helpers.await_queue_edit(openreview_client, 'ifaamas.org/AAMAS/2026/Workshop/EMAS/-/Submission_Change_Before_Bidding-0-1', count=2)
        helpers.await_queue_edit(openreview_client, 'ifaamas.org/AAMAS/2026/Workshop/EMAS/-/Deletion-0-1', count=2)

        withdrawal_invitation = pc_client.get_invitation('ifaamas.org/AAMAS/2026/Workshop/EMAS/-/Withdrawal')
        assert withdrawal_invitation.edit['invitation']['cdate'] == new_expdate
        desk_rejection_invitation = pc_client.get_invitation('ifaamas.org/AAMAS/2026/Workshop/EMAS/-/Desk_Rejection')
        assert desk_rejection_invitation.edit['invitation']['cdate'] == new_expdate
        submission_group_invitation = pc_client.get_invitation('ifaamas.org/AAMAS/2026/Workshop/EMAS/Reviewers/-/Submission_Group')
        assert submission_group_invitation.cdate == new_expdate
        post_submission_inv = pc_client.get_invitation('ifaamas.org/AAMAS/2026/Workshop/EMAS/-/Submission_Change_Before_Bidding')
        assert post_submission_inv.cdate == new_expdate
        deletion_invitation = pc_client.get_invitation('ifaamas.org/AAMAS/2026/Workshop/EMAS/-/Deletion')
        assert deletion_invitation.edit['invitation']['expdate'] == new_expdate

    def test_post_submissions(self, openreview_client, test_client, helpers):

        test_client = openreview.api.OpenReviewClient(token=test_client.token)

        test_client.post_note_edit(
            invitation='ifaamas.org/AAMAS/2026/Workshop/EMAS/-/Submission',
            signatures=['~SomeFirstName_User1'],
            note = openreview.api.Note(
                license = 'CC BY 4.0',
                content = {
                    'title': { 'value': 'Test Submission 1' },
                    'abstract': { 'value': 'This is an abstract for submission 1' },
                    'authors': { 'value': ['SomeFirstName User', 'AuthorOne EMAS'] },
                    'authorids': { 'value': ['~SomeFirstName_User1', '~AuthorOne_EMAS1'] },
                    'keywords': { 'value': ['machine learning', 'artificial intelligence'] },
                    'email_sharing': { 'value': 'We authorize the sharing of all author emails with Program Chairs.' },
                    'data_release': { 'value': 'We authorize the release of our submission and author names to the public in the event of acceptance.' },
                }
            )
        )

        helpers.await_queue_edit(openreview_client, invitation='ifaamas.org/AAMAS/2026/Workshop/EMAS/-/Submission', count=1)

        submissions = openreview_client.get_notes(invitation='ifaamas.org/AAMAS/2026/Workshop/EMAS/-/Submission', sort='number:asc')
        assert len(submissions) == 1
        assert submissions[0].readers == ['ifaamas.org/AAMAS/2026/Workshop/EMAS', '~SomeFirstName_User1', '~AuthorOne_EMAS1']

        pc_client=openreview.api.OpenReviewClient(username='programchair@emas.cc', password=helpers.strong_password)

        now = datetime.datetime.now()
        new_duedate = openreview.tools.datetime_millis(now - datetime.timedelta(minutes=30))

        submission_inv = pc_client.get_invitation('ifaamas.org/AAMAS/2026/Workshop/EMAS/-/Submission')

        # extend Submission duedate with Submission/Deadline invitation
        edit = pc_client.post_invitation_edit(
            invitations='ifaamas.org/AAMAS/2026/Workshop/EMAS/-/Submission/Dates',
            content={
                'activation_date': { 'value': submission_inv.cdate },
                'due_date': { 'value': new_duedate }
            }
        )

        helpers.await_queue_edit(openreview_client, edit_id=edit['id'])
        helpers.await_queue_edit(openreview_client, 'ifaamas.org/AAMAS/2026/Workshop/EMAS/-/Full_Submission-0-1', count=4)

        full_submission_invitations = pc_client.get_invitations(invitation='ifaamas.org/AAMAS/2026/Workshop/EMAS/-/Full_Submission')
        assert len(full_submission_invitations) == 1

        deletion_invitations = pc_client.get_invitations(invitation='ifaamas.org/AAMAS/2026/Workshop/EMAS/-/Deletion')
        assert len(deletion_invitations) == 1

        withdrawal_invitations = pc_client.get_invitations(invitation='ifaamas.org/AAMAS/2026/Workshop/EMAS/-/Withdrawal')
        assert len(withdrawal_invitations) == 0

        desk_rejection_invitations = pc_client.get_invitations(invitation='ifaamas.org/AAMAS/2026/Workshop/EMAS/-/Desk_Rejection')
        assert len(desk_rejection_invitations) == 0
