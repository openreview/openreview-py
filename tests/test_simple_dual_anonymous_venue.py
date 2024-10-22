import os
import pytest
import datetime
import openreview
from openreview.api import Note
from openreview.api import OpenReviewClient
from openreview.workflows import simple_dual_anonymous

class TestSimpleDualAnonymous():

    def test_setup(self, openreview_client, helpers):
        super_id = 'openreview.net'
        support_group_id = super_id + '/Support'

        helpers.create_user('programchair@abcd.cc', 'ProgramChair', 'ABCD')
        helpers.create_user('reviewer_one@abcd.cc', 'ReviewerOne', 'ABCD')
        pc_client=openreview.api.OpenReviewClient(username='programchair@abcd.cc', password=helpers.strong_password)

        workflow_setup = simple_dual_anonymous.Simple_Dual_Anonymous_Workflow(openreview_client, support_group_id, super_id)
        workflow_setup.setup()

        assert openreview_client.get_invitation('openreview.net/-/Edit')
        assert openreview_client.get_invitation('openreview.net/Support/Simple_Dual_Anonymous/-/Venue_Configuration_Request')
        assert openreview_client.get_invitation('openreview.net/Support/-/Deployment')

        now = datetime.datetime.utcnow()
        due_date = now + datetime.timedelta(days=1)

        request = pc_client.post_note_edit(invitation='openreview.net/Support/Simple_Dual_Anonymous/-/Venue_Configuration_Request',
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
                    'submission_license': { 'value': ['CC BY-NC 4.0'] }
                }
            ))
        
        helpers.await_queue_edit(openreview_client, edit_id=request['id'])

        request = openreview_client.get_note(request['note']['id'])
        # assert openreview_client.get_invitation(f'openreview.net/Venue_Configuration_Request{request.number}/-/Comment')
        assert openreview_client.get_invitation(f'openreview.net/Support/Simple_Dual_Anonymous/Venue_Configuration_Request{request.number}/-/Deployment')

        # deploy the venue
        edit = openreview_client.post_note_edit(invitation=f'openreview.net/Support/Simple_Dual_Anonymous/Venue_Configuration_Request{request.number}/-/Deployment',
            signatures=[support_group_id],
            note=openreview.api.Note(
                id=request.id,
                content={
                    'venue_id': { 'value': 'ABCD.cc/2025/Conference' }
                }
            ))
        
        helpers.await_queue_edit(openreview_client, edit_id=edit['id'])
        helpers.await_queue_edit(openreview_client, invitation='openreview.net/Support/Simple_Dual_Anonymous/Venue_Configuration_Request/-/Submission')
        helpers.await_queue_edit(openreview_client, invitation='openreview.net/Support/Simple_Dual_Anonymous/Venue_Configuration_Request/-/Submission_Change_After_Deadline')

        group = openreview.tools.get_group(openreview_client, 'ABCD.cc/2025/Conference')
        assert group.domain == 'ABCD.cc/2025/Conference'
        assert group.members == ['openreview.net/Support', 'ABCD.cc/2025/Conference/Program_Chairs', 'ABCD.cc/2025/Conference/Automated_Administrator']
                                 
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

        group = openreview.tools.get_group(openreview_client, 'ABCD.cc/2025/Conference/Reviewers')
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
        submission_deadline_inv = openreview_client.get_invitation('ABCD.cc/2025/Conference/-/Submission/Dates')
        assert submission_deadline_inv and submission_inv.id in submission_deadline_inv.edit['invitation']['id']
        assert openreview_client.get_invitation('ABCD.cc/2025/Conference/-/Submission/Form_Fields')
        assert openreview_client.get_invitation('ABCD.cc/2025/Conference/-/Submission/Notifications')
        post_submission_inv = openreview_client.get_invitation('ABCD.cc/2025/Conference/-/Submission_Change_After_Deadline')
        assert post_submission_inv and post_submission_inv.cdate == submission_inv.expdate
        assert openreview_client.get_invitation('ABCD.cc/2025/Conference/-/Submission_Change_After_Deadline/Submission_Readers')
        assert openreview_client.get_invitation('ABCD.cc/2025/Conference/-/Submission_Change_After_Deadline/Restrict_Field_Visibility')
        assert openreview_client.get_invitation('ABCD.cc/2025/Conference/-/Official_Review')
        assert openreview_client.get_invitation('ABCD.cc/2025/Conference/-/Decision')
        assert openreview_client.get_invitation('ABCD.cc/2025/Conference/-/Withdrawal')
        assert openreview_client.get_invitation('ABCD.cc/2025/Conference/-/Withdrawn_Submission')
        assert openreview_client.get_invitation('ABCD.cc/2025/Conference/-/Withdraw_Expiration')
        assert openreview_client.get_invitation('ABCD.cc/2025/Conference/-/Withdrawal_Reversion')
        assert openreview_client.get_invitation('ABCD.cc/2025/Conference/-/Desk_Rejection')
        assert openreview_client.get_invitation('ABCD.cc/2025/Conference/-/Desk_Rejected_Submission')
        assert openreview_client.get_invitation('ABCD.cc/2025/Conference/-/Desk_Reject_Expiration')
        assert openreview_client.get_invitation('ABCD.cc/2025/Conference/-/Desk_Rejection_Reversion')

        assert openreview_client.get_invitation('ABCD.cc/2025/Conference/Reviewers/-/Submission_Group')

        # extend submission deadline
        now = datetime.datetime.utcnow()
        new_cdate = openreview.tools.datetime_millis(now - datetime.timedelta(days=3))
        new_duedate = openreview.tools.datetime_millis(now + datetime.timedelta(days=3))

        # extend Submission duedate with Submission/Deadline invitation
        pc_client.post_invitation_edit(
            invitations=submission_deadline_inv.id,
            content={
                'activation_date': { 'value': new_cdate },
                'due_date': { 'value': new_duedate }
            }
        )
        helpers.await_queue_edit(openreview_client, invitation='ABCD.cc/2025/Conference/-/Submission/Dates')
        helpers.await_queue_edit(openreview_client, edit_id='ABCD.cc/2025/Conference/-/Submission_Change_After_Deadline-0-1', count=1)
        helpers.await_queue_edit(openreview_client, edit_id='ABCD.cc/2025/Conference/Reviewers/-/Submission_Group-0-1', count=1)

        # assert submission deadline and expdate get updated, as well as post submission cdate
        submission_inv = openreview.tools.get_invitation(openreview_client, 'ABCD.cc/2025/Conference/-/Submission')
        assert submission_inv and submission_inv.cdate == new_cdate
        assert submission_inv.duedate == new_duedate
        assert submission_inv.expdate == new_duedate + 1800000
        post_submission_inv = openreview.tools.get_invitation(openreview_client, 'ABCD.cc/2025/Conference/-/Submission_Change_After_Deadline')
        assert post_submission_inv and post_submission_inv.cdate == submission_inv.expdate

        content_inv = openreview.tools.get_invitation(openreview_client, 'ABCD.cc/2025/Conference/-/Submission/Form_Fields')
        assert content_inv
        assert 'subject_area' not in submission_inv.edit['note']['content']
        assert 'keywords' in submission_inv.edit['note']['content']
        assert submission_inv.edit['note']['license'] == 'CC BY 4.0'

        ## edit Submission content with Submission/Form_Fields invitation
        pc_client.post_invitation_edit(
            invitations=content_inv.id,
            content = {
                'content': {
                    'value': {
                        'subject_area': {
                            'order': 10,
                            "description": "Select one subject area.",
                            'value': {
                                'param': {
                                    'type': 'string',
                                    'enum': [
                                        "3D from multi-view and sensors",
                                        "3D from single images",
                                        "Adversarial attack and defense",
                                        "Autonomous driving",
                                        "Biometrics",
                                        "Computational imaging",
                                        "Computer vision for social good",
                                        "Computer vision theory",
                                        "Datasets and evaluation"
                                    ],
                                    "input": "select"
                                }
                            }
                        },
                        'keywords': {
                            'delete': True
                        }
                    }
                },
                'license': {
                    'value':  [
                        {'value': 'CC BY-NC-ND 4.0', 'optional': True, 'description': 'CC BY-NC-ND 4.0'},
                        {'value': 'CC BY-NC-SA 4.0', 'optional': True, 'description': 'CC BY-NC-SA 4.0'}
                    ]
                }
            }
        )

        submission_inv = openreview.tools.get_invitation(openreview_client, 'ABCD.cc/2025/Conference/-/Submission')
        assert submission_inv and 'subject_area' in submission_inv.edit['note']['content']
        assert 'keywords' not in submission_inv.edit['note']['content']
        content_keys = submission_inv.edit['note']['content'].keys()
        assert all(field in content_keys for field in ['title', 'authors', 'authorids', 'TLDR', 'abstract', 'pdf'])
        assert submission_inv.edit['note']['license']['param']['enum'] == [
            {
            "value": "CC BY-NC-ND 4.0",
            "optional": True,
            "description": "CC BY-NC-ND 4.0"
          },
          {
            "value": "CC BY-NC-SA 4.0",
            "optional": True,
            "description": "CC BY-NC-SA 4.0"
          }
        ]

        notifications_inv = openreview.tools.get_invitation(openreview_client, 'ABCD.cc/2025/Conference/-/Submission/Notifications')
        assert notifications_inv
        assert 'email_authors' in submission_inv.content and submission_inv.content['email_authors']['value'] == True
        assert 'email_program_chairs' in submission_inv.content and submission_inv.content['email_program_chairs']['value'] == False

        ## edit Submission invitation content with Submission/Notifications invitation
        pc_client.post_invitation_edit(
            invitations=notifications_inv.id,
            content = {
                'email_authors': { 'value': True },
                'email_program_chairs': { 'value': True }
            }
        )

        submission_inv = openreview.tools.get_invitation(openreview_client, 'ABCD.cc/2025/Conference/-/Submission')
        assert 'email_authors' in submission_inv.content and submission_inv.content['email_authors']['value'] == True
        assert 'email_program_chairs' in submission_inv.content and submission_inv.content['email_program_chairs']['value'] == True

    def test_post_submissions(self, openreview_client, test_client, helpers):

        test_client = openreview.api.OpenReviewClient(token=test_client.token)

        domains = ['umass.edu', 'amazon.com', 'fb.com', 'cs.umass.edu', 'google.com', 'mit.edu', 'deepmind.com', 'co.ux', 'apple.com', 'nvidia.com']
        for i in range(1,11):
            note = openreview.api.Note(
                license = 'CC BY-NC-SA 4.0',
                content = {
                    'title': { 'value': 'Paper title ' + str(i) },
                    'abstract': { 'value': 'This is an abstract ' + str(i) },
                    'authorids': { 'value': ['~SomeFirstName_User1', 'andrew@' + domains[i % 10]] },
                    'authors': { 'value': ['SomeFirstName User', 'Andrew Mc'] },
                    'subject_area': { 'value': '3D from multi-view and sensors' },
                    'pdf': {'value': '/pdf/' + 'p' * 40 +'.pdf' },
                }
            )

            test_client.post_note_edit(invitation='ABCD.cc/2025/Conference/-/Submission',
                signatures=['~SomeFirstName_User1'],
                note=note)

        helpers.await_queue_edit(openreview_client, invitation='ABCD.cc/2025/Conference/-/Submission', count=10)

        submissions = openreview_client.get_notes(invitation='ABCD.cc/2025/Conference/-/Submission', sort='number:asc')
        assert len(submissions) == 10
        assert submissions[-1].readers == ['ABCD.cc/2025/Conference', '~SomeFirstName_User1', 'andrew@umass.edu']

        messages = openreview_client.get_messages(to='test@mail.com', subject='ABCD 2025 has received your submission titled Paper title .*')
        assert messages and len(messages) == 10
        assert messages[0]['content']['text'] == f"Your submission to ABCD 2025 has been posted.\n\nSubmission Number: 1\n\nTitle: Paper title 1 \n\nAbstract: This is an abstract 1\n\nTo view your submission, click here: https://openreview.net/forum?id={submissions[0].id}\n\nPlease note that responding to this email will direct your reply to abcd2025.programchairs@gmail.com.\n"

        messages = openreview_client.get_messages(to='programchair@abcd.cc', subject='ABCD 2025 has received a new submission titled Paper title .*')
        assert messages and len(messages) == 10

        submission_field_readers_inv = openreview.tools.get_invitation(openreview_client, 'ABCD.cc/2025/Conference/-/Submission_Change_After_Deadline/Restrict_Field_Visibility')
        assert submission_field_readers_inv

        pc_client=openreview.api.OpenReviewClient(username='programchair@abcd.cc', password=helpers.strong_password)

        # expire submission deadline
        now = datetime.datetime.utcnow()
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
        helpers.await_queue_edit(openreview_client, edit_id='ABCD.cc/2025/Conference/-/Submission_Change_After_Deadline-0-1', count=2)
        helpers.await_queue_edit(openreview_client, edit_id='ABCD.cc/2025/Conference/Reviewers/-/Submission_Group-0-1', count=2)
        helpers.await_queue_edit(openreview_client, edit_id='ABCD.cc/2025/Conference/-/Withdrawal-0-1', count=2)
        helpers.await_queue_edit(openreview_client, edit_id='ABCD.cc/2025/Conference/-/Desk_Rejection-0-1', count=2)

        submissions = openreview_client.get_notes(invitation='ABCD.cc/2025/Conference/-/Submission', sort='number:asc')
        assert len(submissions) == 10
        assert submissions[0].readers == ['ABCD.cc/2025/Conference', 'ABCD.cc/2025/Conference/Submission/1/Reviewers', 'ABCD.cc/2025/Conference/Submission/1/Authors']
        assert submissions[0].content['authors']['readers'] == ['ABCD.cc/2025/Conference', 'ABCD.cc/2025/Conference/Submission/1/Authors']
        assert submissions[0].content['authorids']['readers'] == ['ABCD.cc/2025/Conference', 'ABCD.cc/2025/Conference/Submission/1/Authors']
        assert submissions[0].content['venueid']['value'] == 'ABCD.cc/2025/Conference/Submission'
        assert submissions[0].content['venue']['value'] == 'ABCD 2025 Conference'

        submission_groups = openreview_client.get_all_groups(prefix='ABCD.cc/2025/Conference/Submission/')
        reviewer_groups = [group for group in submission_groups if group.id.endswith('/Reviewers')]
        assert len(reviewer_groups) == 10

         # allow reviewers to see pdf
        pc_client.post_invitation_edit(
            invitations=submission_field_readers_inv.id,
            content = {
                'author_readers': { 'value': ['ABCD.cc/2025/Conference', 'ABCD.cc/2025/Conference/Submission/${{4/id}/number}/Authors'] },
                'pdf_readers': { 'value': ['ABCD.cc/2025/Conference', 'ABCD.cc/2025/Conference/Submission/${{4/id}/number}/Reviewers', 'ABCD.cc/2025/Conference/Submission/${{4/id}/number}/Authors'] }
            }
        )
        helpers.await_queue_edit(openreview_client, edit_id='ABCD.cc/2025/Conference/-/Submission_Change_After_Deadline-0-1', count=3)

        submissions = openreview_client.get_notes(invitation='ABCD.cc/2025/Conference/-/Submission', sort='number:asc')
        assert len(submissions) == 10
        assert submissions[0].content['pdf']['readers'] == ['ABCD.cc/2025/Conference', 'ABCD.cc/2025/Conference/Submission/1/Reviewers', 'ABCD.cc/2025/Conference/Submission/1/Authors']

        withdrawal_invitations = openreview_client.get_all_invitations(invitation='ABCD.cc/2025/Conference/-/Withdrawal')
        assert len(withdrawal_invitations) == 10

        desk_rejection_invitations = openreview_client.get_all_invitations(invitation='ABCD.cc/2025/Conference/-/Desk_Rejection')
        assert len(desk_rejection_invitations) == 10

    def test_review_stage(self, openreview_client, helpers):

        pc_client = openreview.api.OpenReviewClient(username='programchair@abcd.cc', password=helpers.strong_password)
        assert pc_client.get_invitation('ABCD.cc/2025/Conference/-/Official_Review')
        assert pc_client.get_invitation('ABCD.cc/2025/Conference/-/Official_Review/Dates')
        assert pc_client.get_invitation('ABCD.cc/2025/Conference/-/Official_Review/Form_Fields')
        assert pc_client.get_invitation('ABCD.cc/2025/Conference/-/Official_Review/Readers')
        assert pc_client.get_invitation('ABCD.cc/2025/Conference/-/Official_Review/Notifications')

        # edit review stage fields
        pc_client.post_invitation_edit(
            invitations='ABCD.cc/2025/Conference/-/Official_Review/Form_Fields',
            content = {
                'content': {
                    'value': {
                        "review": {
                            'order': 1,
                            'description': 'Please provide an evaluation of the quality, clarity, originality and significance of this work, including a list of its pros and cons (max 200000 characters). Add formatting using Markdown and formulas using LaTeX. For more information see https://openreview.net/faq',
                            'value': {
                                'param': {
                                    'type': 'string',
                                    'maxLength': 200000,
                                    'markdown': True,
                                    'input': 'textarea'
                                }
                            }
                        },
                        "review_rating": {
                            "order": 2,
                            "value": {
                            "param": {
                                "type": "integer",
                                "enum": [
                                    {'value': 1, 'description': '1: strong reject'},
                                    {'value': 2, 'description': '2: reject, not good enough'},
                                    {'value': 3, 'description': '3: exactly at acceptance threshold'},
                                    {'value': 4, 'description': '4: accept, good paper'},
                                    {'value': 5, 'description': '5: strong accept, should be highlighted at the conference'}
                                ],
                                "input": "radio"
                            }
                            },
                            "description": "Please provide an \"overall score\" for this submission."
                        },
                        'review_confidence': {
                            'order': 3,
                            'value': {
                                'param': {
                                    'type': 'integer',
                                    'enum': [
                                        { 'value': 5, 'description': '5: The reviewer is absolutely certain that the evaluation is correct and very familiar with the relevant literature' },
                                        { 'value': 4, 'description': '4: The reviewer is confident but not absolutely certain that the evaluation is correct' },
                                        { 'value': 3, 'description': '3: The reviewer is fairly confident that the evaluation is correct' },
                                        { 'value': 2, 'description': '2: The reviewer is willing to defend the evaluation, but it is quite likely that the reviewer did not understand central parts of the paper' },
                                        { 'value': 1, 'description': '1: The reviewer\'s evaluation is an educated guess' }
                                    ],
                                    'input': 'radio'
                                }
                            }
                        },
                        'title': {
                            'delete': True
                        },
                        'rating': {
                            'delete': True
                        },
                        'confidence': {
                            'delete': True
                        }
                    }
                },
                'review_rating': {
                    'value': 'review_rating'
                },
                'review_confidence': {
                    'value': 'review_confidence'
                }
            }
        )

        helpers.await_queue_edit(openreview_client, invitation=f'ABCD.cc/2025/Conference/-/Official_Review/Form_Fields')

        review_inv = openreview.tools.get_invitation(openreview_client, 'ABCD.cc/2025/Conference/-/Official_Review')
        assert 'title' not in review_inv.edit['invitation']['edit']['note']['content']
        assert 'rating' not in review_inv.edit['invitation']['edit']['note']['content']
        assert 'confidence' not in review_inv.edit['invitation']['edit']['note']['content']
        assert 'review' in review_inv.edit['invitation']['edit']['note']['content']
        assert 'review_rating' in review_inv.edit['invitation']['edit']['note']['content'] and review_inv.edit['invitation']['edit']['note']['content']['review_rating']['value']['param']['enum'][0] == {'value': 1, 'description': '1: strong reject'}
        assert 'review_confidence' in review_inv.edit['invitation']['edit']['note']['content']

        group = openreview_client.get_group('ABCD.cc/2025/Conference')
        assert 'review_rating' in group.content and group.content['review_rating']['value'] == 'review_rating'
        assert 'review_confidence' in group.content and group.content['review_confidence']['value'] == 'review_confidence'

        ## edit Official Review readers to include Reviewers/Submitted
        pc_client.post_invitation_edit(
            invitations='ABCD.cc/2025/Conference/-/Official_Review/Readers',
            content = {
                'readers': {
                    'value':  [
                        'ABCD.cc/2025/Conference/Program_Chairs',
                        'ABCD.cc/2025/Conference/Submission/${5/content/noteNumber/value}/Reviewers/Submitted'
                    ]
                }
            }
        )

        review_inv = openreview.tools.get_invitation(openreview_client, 'ABCD.cc/2025/Conference/-/Official_Review')
        assert review_inv.edit['invitation']['edit']['note']['readers'] == [
            'ABCD.cc/2025/Conference/Program_Chairs',
            'ABCD.cc/2025/Conference/Submission/${5/content/noteNumber/value}/Reviewers/Submitted'
        ]

        # create child invitations
        now = datetime.datetime.utcnow()
        new_cdate = openreview.tools.datetime_millis(now)
        new_duedate = openreview.tools.datetime_millis(now + datetime.timedelta(days=3))

        pc_client.post_invitation_edit(
            invitations='ABCD.cc/2025/Conference/-/Official_Review/Dates',
            content={
                'activation_date': { 'value': new_cdate },
                'due_date': { 'value': new_duedate },
                'expiration_date': { 'value': new_duedate }
            }
        )
        helpers.await_queue_edit(openreview_client, edit_id='ABCD.cc/2025/Conference/-/Official_Review-0-1', count=2)

        invitations = openreview_client.get_invitations(invitation='ABCD.cc/2025/Conference/-/Official_Review')
        assert len(invitations) == 10

        invitation  = openreview_client.get_invitation('ABCD.cc/2025/Conference/Submission/1/-/Official_Review')
        assert invitation and invitation.edit['readers'] == [
            'ABCD.cc/2025/Conference/Program_Chairs',
            'ABCD.cc/2025/Conference/Submission/1/Reviewers/Submitted'
        ]

        openreview_client.add_members_to_group('ABCD.cc/2025/Conference/Submission/1/Reviewers', '~ReviewerOne_ABCD1')
        reviewer_client=openreview.api.OpenReviewClient(username='reviewer_one@abcd.cc', password=helpers.strong_password)

        anon_groups = reviewer_client.get_groups(prefix='ABCD.cc/2025/Conference/Submission/1/Reviewer_', signatory='~ReviewerOne_ABCD1')
        anon_group_id = anon_groups[0].id

        review_edit = reviewer_client.post_note_edit(
            invitation='ABCD.cc/2025/Conference/Submission/1/-/Official_Review',
            signatures=[anon_group_id],
            note=openreview.api.Note(
                content={
                    'review': { 'value': 'This is a good paper' },
                    'review_rating': { 'value': 5 },
                    'review_confidence': { 'value': 3 }
                }
            )
        )

        helpers.await_queue_edit(openreview_client, edit_id=review_edit['id'])

    def test_comment_stage(self, openreview_client, helpers):

        pc_client = openreview.api.OpenReviewClient(username='programchair@abcd.cc', password=helpers.strong_password)

        assert pc_client.get_invitation('ABCD.cc/2025/Conference/-/Official_Comment')
        assert pc_client.get_invitation('ABCD.cc/2025/Conference/-/Official_Comment/Dates')
        assert pc_client.get_invitation('ABCD.cc/2025/Conference/-/Official_Comment/Form_Fields')
        assert pc_client.get_invitation('ABCD.cc/2025/Conference/-/Official_Comment/Writers_and_Readers')
        assert pc_client.get_invitation('ABCD.cc/2025/Conference/-/Official_Comment/Notifications')

        # edit comment stage fields
        pc_client.post_invitation_edit(
            invitations='ABCD.cc/2025/Conference/-/Official_Comment/Form_Fields',
            content = {
                'content': {
                    'value': {
                        "confidential_comment_to_PC": {
                            'order': 3,
                            'description': '(Optionally) Leave a private comment to the organizers of the venue. Add formatting using Markdown and formulas using LaTeX. For more information see https://openreview.net/faq',
                            'value': {
                                'param': {
                                    'type': 'string',
                                    'maxLength': 200000,
                                    'markdown': True,
                                    'input': 'textarea',
                                    'optional': True
                                }
                            },
                            'readers': ['ABCD.cc/2025/Conference/Program_Chairs']
                        }
                    }
                }
            }
        )
        helpers.await_queue_edit(openreview_client, edit_id='ABCD.cc/2025/Conference/-/Official_Comment-0-1', count=2)

        # create child invitations
        now = datetime.datetime.utcnow()
        new_cdate = openreview.tools.datetime_millis(now)
        new_duedate = openreview.tools.datetime_millis(now + datetime.timedelta(days=3))

        pc_client.post_invitation_edit(
            invitations='ABCD.cc/2025/Conference/-/Official_Comment/Dates',
            content={
                'activation_date': { 'value': new_cdate },
                'expiration_date': { 'value': new_duedate }
            }
        )
        helpers.await_queue_edit(openreview_client, edit_id='ABCD.cc/2025/Conference/-/Official_Comment-0-1', count=3)

        invitations = openreview_client.get_invitations(invitation='ABCD.cc/2025/Conference/-/Official_Comment')
        assert len(invitations) == 10
        inv = openreview_client.get_invitation('ABCD.cc/2025/Conference/Submission/1/-/Official_Comment')

        assert inv
        assert 'confidential_comment_to_PC' in inv.edit['note']['content'] and 'readers' in inv.edit['note']['content']['confidential_comment_to_PC']

        ## edit Confidential_Comment participants and readers, remove authors as participants
        pc_client.post_invitation_edit(
            invitations='ABCD.cc/2025/Conference/-/Official_Comment/Writers_and_Readers',
            content = {
                'writers': {
                    'value':  [
                        'ABCD.cc/2025/Conference/Program_Chairs',
                        'ABCD.cc/2025/Conference/Submission/${3/content/noteNumber/value}/Reviewers'
                    ]
                },
                'readers': {
                    'value':  [
                        {'value': 'ABCD.cc/2025/Conference/Program_Chairs', 'optional': False},
                        {'value': 'ABCD.cc/2025/Conference/Submission/${8/content/noteNumber/value}/Reviewers', 'optional': True},
                        {'value': 'ABCD.cc/2025/Conference/Submission/${8/content/noteNumber/value}/Authors', 'optional': True},
                    ]
                }
            }
        )
        helpers.await_queue_edit(openreview_client, edit_id='ABCD.cc/2025/Conference/-/Official_Comment-0-1', count=4)

        invitation = openreview_client.get_invitation('ABCD.cc/2025/Conference/Submission/1/-/Official_Comment')

        assert invitation.invitees == ['ABCD.cc/2025/Conference/Program_Chairs', 'ABCD.cc/2025/Conference/Submission/1/Reviewers']
        assert invitation.edit['note']['readers']['param']['items'] == [
          {
            "value": "ABCD.cc/2025/Conference/Program_Chairs",
            "optional": False
          },
          {
            "value": "ABCD.cc/2025/Conference/Submission/1/Reviewers",
            "optional": True
          },
          {
            "value": "ABCD.cc/2025/Conference/Submission/1/Authors",
            "optional": True
          }
        ]

    def test_decision_stage(self, openreview_client, helpers):

        pc_client = openreview.api.OpenReviewClient(username='programchair@abcd.cc', password=helpers.strong_password)

        assert pc_client.get_invitation('ABCD.cc/2025/Conference/-/Decision')
        assert pc_client.get_invitation('ABCD.cc/2025/Conference/-/Decision/Dates')
        assert pc_client.get_invitation('ABCD.cc/2025/Conference/-/Decision/Readers')
