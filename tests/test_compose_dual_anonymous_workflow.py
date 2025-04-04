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
from openreview.workflows import compose_dual_anonymous_workflow

class TestComposeDualAnonymousWithAreaChairs():

    def test_setup(self, openreview_client, helpers):
        super_id = 'openreview.net'
        support_group_id = super_id + '/Support'

        helpers.create_user('programchair@abcd.cc', 'ProgramChair', 'ABCD')
        helpers.create_user('areachair@abcd.cc', 'AreaChair', 'ABCD')
        helpers.create_user('areachair2@abcd.cc', 'AreaChair2', 'ABCD')
        helpers.create_user('reviewer_one@abcd.cc', 'ReviewerOne', 'ABCD')
        helpers.create_user('reviewer_two@abcd.cc', 'ReviewerTwo', 'ABCD')
        helpers.create_user('reviewer_three@abcd.cc', 'ReviewerThree', 'ABCD')
        pc_client=openreview.api.OpenReviewClient(username='programchair@abcd.cc', password=helpers.strong_password)

        workflow_setup = compose_dual_anonymous_workflow.Compose_Dual_Anonymous_Workflow(openreview_client, support_group_id, super_id)
        workflow_setup.setup()

        assert openreview_client.get_invitation('openreview.net/-/Edit')
        assert openreview_client.get_invitation('openreview.net/Support/Compose_Dual_Anonymous/-/Venue_Configuration_Request')
        assert openreview_client.get_invitation('openreview.net/Support/-/Deployment')

        now = datetime.datetime.now()
        due_date = now + datetime.timedelta(days=2)

        request = pc_client.post_note_edit(invitation='openreview.net/Support/Compose_Dual_Anonymous/-/Venue_Configuration_Request',
            signatures=['~ProgramChair_ABCD1'],
            note=openreview.api.Note(
                content={
                    'official_venue_name': { 'value': 'The ABCD Conference' },
                    'abbreviated_venue_name': { 'value': 'ABCD 2025' },
                    'venue_website_url': { 'value': 'https://abcd.cc/Conferences/2025' },
                    'location': { 'value': 'Amherst, Massachusetts' },
                    'venue_start_date': { 'value': openreview.tools.datetime_millis(now + datetime.timedelta(weeks=52)) },
                    'program_chair_emails': { 'value': ['programchair@abcd.cc'] },
                    'contact_email': { 'value': 'abcd2025.programchairs@gmail.com' },
                    'submission_start_date': { 'value': openreview.tools.datetime_millis(now) },
                    'submission_deadline': { 'value': openreview.tools.datetime_millis(due_date) },
                    'submission_license': {
                        'value':  ['CC BY 4.0']
                    }
                }
            ))
        
        helpers.await_queue_edit(openreview_client, edit_id=request['id'])

        request = openreview_client.get_note(request['note']['id'])
        assert openreview_client.get_invitation(f'openreview.net/Support/Venue_Configuration_Request{request.number}/-/Comment')
        assert openreview_client.get_invitation(f'openreview.net/Support/Compose_Dual_Anonymous/Venue_Configuration_Request{request.number}/-/Deploy')
        assert openreview.tools.get_group(openreview_client, 'ABCD.cc/2025/Conference/Program_Chairs') is None

        # deploy the venue
        edit = openreview_client.post_note_edit(invitation=f'openreview.net/Support/Compose_Dual_Anonymous/Venue_Configuration_Request{request.number}/-/Deploy',
            signatures=[support_group_id],
            note=openreview.api.Note(
                id=request.id,
                content={
                    'venue_id': { 'value': 'ABCD.cc/2025/Conference' }
                }
            ))
        
        helpers.await_queue_edit(openreview_client, edit_id=edit['id'])
        helpers.await_queue_edit(openreview_client, invitation='openreview.net/Support/Compose_Dual_Anonymous/Venue_Configuration_Request/-/Submission_Template')
        helpers.await_queue_edit(openreview_client, invitation='openreview.net/Support/Compose_Dual_Anonymous/Venue_Configuration_Request/-/Submission_Change_Before_Bidding_Template')
        helpers.await_queue_edit(openreview_client, invitation='openreview.net/Support/Compose_Dual_Anonymous/Venue_Configuration_Request/-/Submission_Change_Before_Reviewing_Template')
        helpers.await_queue_edit(openreview_client, invitation='openreview.net/Support/Compose_Dual_Anonymous/Venue_Configuration_Request/-/Reviewer_Bid_Template')

        helpers.await_queue_edit(openreview_client, 'ABCD.cc/2025/Conference/-/Withdrawal_Request-0-1', count=1)
        helpers.await_queue_edit(openreview_client, 'ABCD.cc/2025/Conference/-/Desk_Rejection-0-1', count=1)
        helpers.await_queue_edit(openreview_client, 'ABCD.cc/2025/Conference/Reviewers/-/Submission_Group-0-1', count=1)
        helpers.await_queue_edit(openreview_client, 'ABCD.cc/2025/Conference/-/Submission_Change_Before_Bidding-0-1', count=1)

        group = openreview.tools.get_group(openreview_client, 'ABCD.cc/2025/Conference')
        assert group.domain == 'ABCD.cc/2025/Conference'
        assert group.members == ['openreview.net/Support', 'ABCD.cc/2025/Conference/Program_Chairs', 'ABCD.cc/2025/Conference/Automated_Administrator']
        assert 'request_form_id' in group.content and group.content['request_form_id']['value'] == request.id
                                
        group = openreview.tools.get_group(openreview_client, 'ABCD.cc/2025')
        assert group.domain == 'ABCD.cc/2025'
        group = openreview.tools.get_group(openreview_client, 'ABCD.cc')
        assert group.domain == 'ABCD.cc'

        group = openreview.tools.get_group(openreview_client, 'ABCD.cc/2025/Conference/Program_Chairs')
        assert group.members == ['programchair@abcd.cc']
        assert group.domain == 'ABCD.cc/2025/Conference'

        group = openreview.tools.get_group(openreview_client, 'ABCD.cc/2025/Conference/Automated_Administrator')
        assert not group.members
        assert group.domain == 'ABCD.cc/2025/Conference'

        # Check Area Chairs group
        group = openreview.tools.get_group(openreview_client, 'ABCD.cc/2025/Conference/Area_Chairs')
        assert group.domain == 'ABCD.cc/2025/Conference'
        assert not group.members
        
        group = openreview.tools.get_group(openreview_client, 'ABCD.cc/2025/Conference/Reviewers')
        assert group.domain == 'ABCD.cc/2025/Conference'

        group = openreview.tools.get_group(openreview_client, 'ABCD.cc/2025/Conference/Reviewers_Invited')
        assert group.domain == 'ABCD.cc/2025/Conference'        

        group = openreview.tools.get_group(openreview_client, 'ABCD.cc/2025/Conference/Reviewers_Invited/Declined')
        assert group.domain == 'ABCD.cc/2025/Conference'        

        group = openreview.tools.get_group(openreview_client, 'ABCD.cc/2025/Conference/Authors')
        assert group.domain == 'ABCD.cc/2025/Conference'

        group = openreview.tools.get_group(openreview_client, 'ABCD.cc/2025/Conference/Authors/Accepted')
        assert group.domain == 'ABCD.cc/2025/Conference'

        invitation = openreview_client.get_invitation('ABCD.cc/2025/Conference/-/Edit')
        assert 'group_edit_script' in invitation.content
        assert 'invitation_edit_script' in invitation.content

        submission_inv = openreview_client.get_invitation('ABCD.cc/2025/Conference/-/Submission')
        assert submission_inv and submission_inv.cdate == openreview.tools.datetime_millis(now)
        assert submission_inv.duedate == openreview.tools.datetime_millis(due_date)
        assert submission_inv.expdate == submission_inv.duedate + (30*60*1000)

        # Check Meta Review invitation
        assert openreview_client.get_invitation('ABCD.cc/2025/Conference/-/Meta_Review')

    def test_recruit_area_chairs(self, openreview_client, helpers, selenium, request_page):
        # Use invitation to recruit area chairs
        edit = openreview_client.post_group_edit(
                invitation='ABCD.cc/2025/Conference/Area_Chairs/-/Members',
                content={
                    'invitee_details': { 'value':  'areachair@abcd.cc, Area Chair ABCDOne\nareachair2@abcd.cc, Area Chair ABCDTwo' },
                    'invite_message_subject_template': { 'value': '[ABCD 2025] Invitation to serve as Area Chair' },
                    'invite_message_body_template': { 'value': 'Dear {{fullname}},\n\nWe are pleased to invite you to serve as an Area Chair for the ABCD 2025 Conference.\n\nPlease accept or decline the invitation using the link below:\n\n{{invitation_url}}\n\nBest regards,\nABCD 2025 Program Chairs' },
                },
                group=openreview.api.Group()
            )
        helpers.await_queue_edit(openreview_client, edit_id=edit['id'])

        assert set(openreview_client.get_group('ABCD.cc/2025/Conference/Area_Chairs').members) == {'areachair@abcd.cc', 'areachair2@abcd.cc'}

    def test_recruit_reviewers(self, openreview_client, helpers, selenium, request_page):
        # Use invitation to recruit reviewers
        edit = openreview_client.post_group_edit(
                invitation='ABCD.cc/2025/Conference/Reviewers/-/Members',
                content={
                    'invitee_details': { 'value':  'reviewer_one@abcd.cc, Reviewer ABCDOne\nreviewer_two@abcd.cc, Reviewer ABCDTwo\nreviewer_three@abcd.cc, Reviewer ABCDThree' },
                    'invite_message_subject_template': { 'value': '[ABCD 2025] Invitation to serve as Reviewer' },
                    'invite_message_body_template': { 'value': 'Dear Reviewer {{fullname}},\n\nWe are pleased to invite you to serve as a reviewer for the ABCD 2025 Conference.\n\nPlease accept or decline the invitation using the link below:\n\n{{invitation_url}}\n\nBest regards,\nABCD 2025 Program Chairs' },
                },
                group=openreview.api.Group()
            )
        helpers.await_queue_edit(openreview_client, edit_id=edit['id'])

        assert set(openreview_client.get_group('ABCD.cc/2025/Conference/Reviewers').members) == {'reviewer_one@abcd.cc', 'reviewer_two@abcd.cc', 'reviewer_three@abcd.cc'}

    def test_post_submissions(self, openreview_client, test_client, helpers):
        test_client = openreview.api.OpenReviewClient(token=test_client.token)

        domains = ['umass.edu', 'amazon.com', 'fb.com', 'cs.umass.edu', 'google.com', 'mit.edu', 'deepmind.com', 'co.ux', 'apple.com', 'nvidia.com']
        for i in range(1,6):
            note = openreview.api.Note(
                license = 'CC BY 4.0',
                content = {
                    'title': { 'value': 'Paper title ' + str(i) },
                    'abstract': { 'value': 'This is an abstract ' + str(i) },
                    'authorids': { 'value': ['~SomeFirstName_User1', 'andrew@' + domains[i % 10]] },
                    'authors': { 'value': ['SomeFirstName User', 'Andrew Mc'] },
                    'pdf': {'value': '/pdf/' + 'p' * 40 +'.pdf' },
                }
            )

            test_client.post_note_edit(invitation='ABCD.cc/2025/Conference/-/Submission',
                signatures=['~SomeFirstName_User1'],
                note=note)

        helpers.await_queue_edit(openreview_client, invitation='ABCD.cc/2025/Conference/-/Submission', count=5)

        submissions = openreview_client.get_notes(invitation='ABCD.cc/2025/Conference/-/Submission', sort='number:asc')
        assert len(submissions) == 5
        assert submissions[-1].readers == ['ABCD.cc/2025/Conference', '~SomeFirstName_User1', 'andrew@cs.umass.edu']

        # expire submission deadline
        pc_client=openreview.api.OpenReviewClient(username='programchair@abcd.cc', password=helpers.strong_password)
        now = datetime.datetime.now()
        new_cdate = openreview.tools.datetime_millis(now - datetime.timedelta(days=1))
        new_duedate = openreview.tools.datetime_millis(now - datetime.timedelta(minutes=31))

        pc_client.post_invitation_edit(
            invitations='ABCD.cc/2025/Conference/-/Submission/Dates',
            content={
                'activation_date': { 'value': new_cdate },
                'due_date': { 'value': new_duedate }
            }
        )
        helpers.await_queue_edit(openreview_client, invitation='ABCD.cc/2025/Conference/-/Submission/Dates')
        helpers.await_queue_edit(openreview_client, edit_id='ABCD.cc/2025/Conference/-/Submission_Change_Before_Bidding-0-1', count=3)
        helpers.await_queue_edit(openreview_client, edit_id='ABCD.cc/2025/Conference/Reviewers/-/Submission_Group-0-1', count=3)
        helpers.await_queue_edit(openreview_client, edit_id='ABCD.cc/2025/Conference/-/Withdrawal_Request-0-1', count=3)
        helpers.await_queue_edit(openreview_client, edit_id='ABCD.cc/2025/Conference/-/Desk_Rejection-0-1', count=3)

        submissions = openreview_client.get_notes(invitation='ABCD.cc/2025/Conference/-/Submission', sort='number:asc')
        assert len(submissions) == 5
        assert submissions[0].readers == ['ABCD.cc/2025/Conference', 'ABCD.cc/2025/Conference/Reviewers', 'ABCD.cc/2025/Conference/Area_Chairs', 'ABCD.cc/2025/Conference/Submission1/Authors']
        assert submissions[0].content['authors']['readers'] == ['ABCD.cc/2025/Conference', 'ABCD.cc/2025/Conference/Submission1/Authors']
        assert submissions[0].content['authorids']['readers'] == ['ABCD.cc/2025/Conference', 'ABCD.cc/2025/Conference/Submission1/Authors']
        assert 'readers' not in submissions[0].content['pdf']
        assert submissions[0].content['venueid']['value'] == 'ABCD.cc/2025/Conference/Submission'

    def test_paper_matching(self, openreview_client, helpers):
        # Assign area chairs to papers
        submissions = openreview_client.get_notes(invitation='ABCD.cc/2025/Conference/-/Submission', sort='number:asc')
        
        # Assign first paper to area chair
        openreview_client.post_edge(openreview.api.Edge(
            invitation='ABCD.cc/2025/Conference/Area_Chairs/-/Assignment',
            signatures=['ABCD.cc/2025/Conference'],
            head=submissions[0].id,
            tail='areachair@abcd.cc',
            weight=1
        ))

        # Create submission-specific area chair group
        openreview_client.post_group(openreview.api.Group(
            id=f'ABCD.cc/2025/Conference/Submission1/Area_Chairs',
            readers=['ABCD.cc/2025/Conference'],
            writers=['ABCD.cc/2025/Conference'],
            signatures=['ABCD.cc/2025/Conference'],
            members=['areachair@abcd.cc']
        ))

        # Assign reviewers to papers
        for i in range(3):
            reviewer_email = f'reviewer_{["one", "two", "three"][i]}@abcd.cc'
            openreview_client.post_edge(openreview.api.Edge(
                invitation='ABCD.cc/2025/Conference/Reviewers/-/Assignment',
                signatures=['ABCD.cc/2025/Conference'],
                head=submissions[0].id,
                tail=reviewer_email,
                weight=1
            ))

        # Create submission-specific reviewers group
        openreview_client.post_group(openreview.api.Group(
            id=f'ABCD.cc/2025/Conference/Submission1/Reviewers',
            readers=['ABCD.cc/2025/Conference'],
            writers=['ABCD.cc/2025/Conference'],
            signatures=['ABCD.cc/2025/Conference'],
            members=['reviewer_one@abcd.cc', 'reviewer_two@abcd.cc', 'reviewer_three@abcd.cc']
        ))

    def test_review_meta_review_stage(self, openreview_client, helpers):
        # Create review invitation for first paper
        now = datetime.datetime.now()
        due_date = now + datetime.timedelta(days=3)

        review_invitation = openreview.api.Invitation(
            id='ABCD.cc/2025/Conference/Submission1/-/Review',
            invitees=['ABCD.cc/2025/Conference/Submission1/Reviewers'],
            readers=['ABCD.cc/2025/Conference', 'ABCD.cc/2025/Conference/Submission1/Reviewers'],
            writers=['ABCD.cc/2025/Conference'],
            signatures=['ABCD.cc/2025/Conference'],
            duedate=openreview.tools.datetime_millis(due_date),
            edit={
                'signatures': {'param': {'items': [{'prefix': 'ABCD.cc/2025/Conference/Submission1/Reviewer_.*'}]}},
                'readers': ['ABCD.cc/2025/Conference', 'ABCD.cc/2025/Conference/Submission1/Area_Chairs', 'ABCD.cc/2025/Conference/Program_Chairs', '${2/signatures}'],
                'note': {
                    'forum': {'param': {'withInvitation': 'ABCD.cc/2025/Conference/-/Submission'}},
                    'replyto': {'param': {'withInvitation': 'ABCD.cc/2025/Conference/-/Submission'}},
                    'signatures': ['${3/signatures}'],
                    'readers': ['ABCD.cc/2025/Conference', 'ABCD.cc/2025/Conference/Submission1/Area_Chairs', 'ABCD.cc/2025/Conference/Program_Chairs', '${3/signatures}'],
                    'writers': ['ABCD.cc/2025/Conference', '${3/signatures}'],
                    'content': {
                        'title': {'value': {'param': {'type': 'string'}}},
                        'review': {'value': {'param': {'type': 'string', 'maxLength': 200000, 'markdown': True}}},
                        'rating': {'value': {'param': {'type': 'integer', 'enum': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]}}},
                        'confidence': {'value': {'param': {'type': 'integer', 'enum': [1, 2, 3, 4, 5]}}}
                    }
                }
            }
        )
        openreview_client.post_invitation(review_invitation)

        # Create meta review invitation for first paper
        meta_review_invitation = openreview.api.Invitation(
            id='ABCD.cc/2025/Conference/Submission1/-/Meta_Review',
            invitees=['ABCD.cc/2025/Conference/Submission1/Area_Chairs'],
            readers=['ABCD.cc/2025/Conference', 'ABCD.cc/2025/Conference/Submission1/Area_Chairs'],
            writers=['ABCD.cc/2025/Conference'],
            signatures=['ABCD.cc/2025/Conference'],
            duedate=openreview.tools.datetime_millis(due_date),
            edit={
                'signatures': {'param': {'items': [{'prefix': 'ABCD.cc/2025/Conference/Submission1/Area_Chair_.*'}]}},
                'readers': ['ABCD.cc/2025/Conference', 'ABCD.cc/2025/Conference/Program_Chairs', 'ABCD.cc/2025/Conference/Submission1/Area_Chairs', 'ABCD.cc/2025/Conference/Submission1/Reviewers', '${2/signatures}'],
                'note': {
                    'forum': {'param': {'withInvitation': 'ABCD.cc/2025/Conference/-/Submission'}},
                    'replyto': {'param': {'withInvitation': 'ABCD.cc/2025/Conference/-/Submission'}},
                    'signatures': ['${3/signatures}'],
                    'readers': ['ABCD.cc/2025/Conference', 'ABCD.cc/2025/Conference/Program_Chairs', 'ABCD.cc/2025/Conference/Submission1/Area_Chairs', 'ABCD.cc/2025/Conference/Submission1/Reviewers', '${3/signatures}'],
                    'writers': ['ABCD.cc/2025/Conference', '${3/signatures}'],
                    'content': {
                        'title': {'value': {'param': {'type': 'string'}}},
                        'metareview': {'value': {'param': {'type': 'string', 'maxLength': 200000, 'markdown': True}}},
                        'recommendation': {'value': {'param': {'type': 'string', 'enum': ['Accept', 'Reject'], 'optional': True}}},
                        'confidence': {'value': {'param': {'type': 'string', 'enum': [
                            '5: The area chair is absolutely certain',
                            '4: The area chair is confident but not absolutely certain',
                            '3: The area chair is somewhat confident',
                            '2: The area chair is not very confident',
                            '1: The area chair is not at all confident'
                        ], 'optional': True}}}
                    }
                }
            }
        )
        openreview_client.post_invitation(meta_review_invitation)

        # Post a review as reviewer
        anon_groups = openreview_client.get_groups(prefix='ABCD.cc/2025/Conference/Submission1/Reviewer_', member='reviewer_one@abcd.cc')
        anon_group_id = anon_groups[0].id if anon_groups else None
        
        if not anon_group_id:
            # Create a reviewer anonymous group if it doesn't exist
            anon_group = openreview.api.Group(
                id=f'ABCD.cc/2025/Conference/Submission1/Reviewer_1',
                readers=['ABCD.cc/2025/Conference', 'ABCD.cc/2025/Conference/Submission1/Area_Chairs'],
                writers=['ABCD.cc/2025/Conference'],
                signatures=['ABCD.cc/2025/Conference'],
                signatories=[f'ABCD.cc/2025/Conference/Submission1/Reviewer_1'],
                members=['reviewer_one@abcd.cc']
            )
            openreview_client.post_group(anon_group)
            anon_group_id = anon_group.id

        # Post the review
        reviewer_client = openreview.api.OpenReviewClient(username='reviewer_one@abcd.cc', password=helpers.strong_password)
        
        submission = openreview_client.get_notes(invitation='ABCD.cc/2025/Conference/-/Submission', number=1)[0]
        
        review = openreview.api.Note(
            forum=submission.id,
            replyto=submission.id,
            invitation='ABCD.cc/2025/Conference/Submission1/-/Review',
            signatures=[anon_group_id],
            writers=['ABCD.cc/2025/Conference', anon_group_id],
            readers=['ABCD.cc/2025/Conference', 'ABCD.cc/2025/Conference/Program_Chairs', 'ABCD.cc/2025/Conference/Submission1/Area_Chairs', anon_group_id],
            content={
                'title': {'value': 'Review of Paper 1'},
                'review': {'value': 'This paper is very interesting and well-written.'},
                'rating': {'value': 8},
                'confidence': {'value': 4}
            }
        )
        reviewer_client.post_note(review)

        # Post a meta review as area chair
        anon_groups = openreview_client.get_groups(prefix='ABCD.cc/2025/Conference/Submission1/Area_Chair_', member='areachair@abcd.cc')
        anon_group_id = anon_groups[0].id if anon_groups else None
        
        if not anon_group_id:
            # Create an area chair anonymous group if it doesn't exist
            anon_group = openreview.api.Group(
                id=f'ABCD.cc/2025/Conference/Submission1/Area_Chair_1',
                readers=['ABCD.cc/2025/Conference', 'ABCD.cc/2025/Conference/Program_Chairs'],
                writers=['ABCD.cc/2025/Conference'],
                signatures=['ABCD.cc/2025/Conference'],
                signatories=[f'ABCD.cc/2025/Conference/Submission1/Area_Chair_1'],
                members=['areachair@abcd.cc']
            )
            openreview_client.post_group(anon_group)
            anon_group_id = anon_group.id

        # Post the meta review
        ac_client = openreview.api.OpenReviewClient(username='areachair@abcd.cc', password=helpers.strong_password)
        
        meta_review = openreview.api.Note(
            forum=submission.id,
            replyto=submission.id,
            invitation='ABCD.cc/2025/Conference/Submission1/-/Meta_Review',
            signatures=[anon_group_id],
            writers=['ABCD.cc/2025/Conference', anon_group_id],
            readers=['ABCD.cc/2025/Conference', 'ABCD.cc/2025/Conference/Program_Chairs', 'ABCD.cc/2025/Conference/Submission1/Area_Chairs', 'ABCD.cc/2025/Conference/Submission1/Reviewers', anon_group_id],
            content={
                'title': {'value': 'Meta Review of Paper 1'},
                'metareview': {'value': 'Based on the review, this paper should be accepted.'},
                'recommendation': {'value': 'Accept'},
                'confidence': {'value': '5: The area chair is absolutely certain'}
            }
        )
        ac_client.post_note(meta_review)

        # Check that reviews and meta reviews exist
        reviews = openreview_client.get_notes(invitation='ABCD.cc/2025/Conference/Submission1/-/Review')
        assert len(reviews) == 1
        assert reviews[0].content['rating']['value'] == 8
        
        meta_reviews = openreview_client.get_notes(invitation='ABCD.cc/2025/Conference/Submission1/-/Meta_Review')
        assert len(meta_reviews) == 1
        assert meta_reviews[0].content['recommendation']['value'] == 'Accept'

    def test_decision_stage(self, openreview_client, helpers):
        # Create decision invitation
        decision_invitation = openreview.api.Invitation(
            id='ABCD.cc/2025/Conference/Submission1/-/Decision',
            invitees=['ABCD.cc/2025/Conference/Program_Chairs'],
            readers=['ABCD.cc/2025/Conference', 'ABCD.cc/2025/Conference/Program_Chairs'],
            writers=['ABCD.cc/2025/Conference'],
            signatures=['ABCD.cc/2025/Conference'],
            edit={
                'signatures': {'param': {'items': [{'value': 'ABCD.cc/2025/Conference/Program_Chairs'}]}},
                'readers': ['ABCD.cc/2025/Conference/Program_Chairs', 'ABCD.cc/2025/Conference/Submission1/Area_Chairs'],
                'note': {
                    'forum': {'param': {'withInvitation': 'ABCD.cc/2025/Conference/-/Submission'}},
                    'replyto': {'param': {'withInvitation': 'ABCD.cc/2025/Conference/-/Submission'}},
                    'signatures': ['ABCD.cc/2025/Conference/Program_Chairs'],
                    'readers': ['ABCD.cc/2025/Conference/Program_Chairs', 'ABCD.cc/2025/Conference/Submission1/Area_Chairs'],
                    'writers': ['ABCD.cc/2025/Conference/Program_Chairs'],
                    'content': {
                        'title': {'value': {'param': {'type': 'string'}}},
                        'decision': {'value': {'param': {'type': 'string', 'enum': ['Accept', 'Reject']}}},
                        'comment': {'value': {'param': {'type': 'string', 'maxLength': 200000, 'markdown': True}}}
                    }
                }
            }
        )
        openreview_client.post_invitation(decision_invitation)

        # Post a decision
        pc_client = openreview.api.OpenReviewClient(username='programchair@abcd.cc', password=helpers.strong_password)
        
        submission = openreview_client.get_notes(invitation='ABCD.cc/2025/Conference/-/Submission', number=1)[0]
        
        decision = openreview.api.Note(
            forum=submission.id,
            replyto=submission.id,
            invitation='ABCD.cc/2025/Conference/Submission1/-/Decision',
            signatures=['ABCD.cc/2025/Conference/Program_Chairs'],
            writers=['ABCD.cc/2025/Conference/Program_Chairs'],
            readers=['ABCD.cc/2025/Conference/Program_Chairs', 'ABCD.cc/2025/Conference/Submission1/Area_Chairs'],
            content={
                'title': {'value': 'Decision for Paper #1'},
                'decision': {'value': 'Accept'},
                'comment': {'value': 'The paper is accepted based on the positive meta review and reviewer recommendations.'}
            }
        )
        pc_client.post_note(decision)

        # Check that decision exists
        decisions = openreview_client.get_notes(invitation='ABCD.cc/2025/Conference/Submission1/-/Decision')
        assert len(decisions) == 1
        assert decisions[0].content['decision']['value'] == 'Accept'