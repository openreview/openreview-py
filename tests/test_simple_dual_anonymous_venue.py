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
        helpers.await_queue_edit(openreview_client, invitation='openreview.net/Support/Simple_Dual_Anonymous/Venue_Configuration_Request/-/Post_Submission')

        group = openreview.tools.get_group(openreview_client, 'ABCD.cc/2025/Conference')
        assert group.domain == 'ABCD.cc/2025/Conference'
        assert group.members == ['openreview.net/Support', 'ABCD.cc/2025/Conference/Program_Chairs']
                                 
        group = openreview.tools.get_group(openreview_client, 'ABCD.cc/2025')
        assert group.domain == 'ABCD.cc/2025'
        group = openreview.tools.get_group(openreview_client, 'ABCD.cc')
        assert group.domain == 'ABCD.cc'

        group = openreview.tools.get_group(openreview_client, 'ABCD.cc/2025/Conference/Program_Chairs')
        assert group.members == ['programchair@abcd.cc']
        assert group.domain == 'ABCD.cc/2025/Conference'

        group = openreview.tools.get_group(openreview_client, 'ABCD.cc/2025/Conference/Reviewers')
        assert group.domain == 'ABCD.cc/2025/Conference'

        group = openreview.tools.get_group(openreview_client, 'ABCD.cc/2025/Conference/Authors')
        assert group.domain == 'ABCD.cc/2025/Conference'

        invitation = openreview_client.get_invitation('ABCD.cc/2025/Conference/-/Edit')
        assert 'group_edit_script' in invitation.content
        assert 'invitation_edit_script' in invitation.content

        submission_inv = openreview_client.get_invitation('ABCD.cc/2025/Conference/-/Submission')
        assert submission_inv and submission_inv.cdate == openreview.tools.datetime_millis(now)
        assert submission_inv.duedate == openreview.tools.datetime_millis(due_date)
        assert submission_inv.expdate == submission_inv.duedate + (30*60*1000)
        submission_deadline_inv = openreview_client.get_invitation('ABCD.cc/2025/Conference/-/Submission/Deadlines')
        assert submission_deadline_inv and submission_inv.id in submission_deadline_inv.edit['invitation']['id']
        assert openreview_client.get_invitation('ABCD.cc/2025/Conference/-/Submission/Form_Fields')
        assert openreview_client.get_invitation('ABCD.cc/2025/Conference/-/Submission/Notifications')
        post_submission_inv = openreview_client.get_invitation('ABCD.cc/2025/Conference/-/Post_Submission')
        assert post_submission_inv and post_submission_inv.cdate == submission_inv.expdate
        assert openreview_client.get_invitation('ABCD.cc/2025/Conference/-/Post_Submission/Submission_Readers')
        assert openreview_client.get_invitation('ABCD.cc/2025/Conference/-/Post_Submission/Restrict_Field_Visibility')
        assert openreview_client.get_invitation('ABCD.cc/2025/Conference/-/Official_Review')
        assert openreview_client.get_invitation('ABCD.cc/2025/Conference/-/Decision')

        # extend submission deadline
        now = datetime.datetime.utcnow()
        new_cdate = openreview.tools.datetime_millis(now - datetime.timedelta(days=3))
        new_duedate = openreview.tools.datetime_millis(now + datetime.timedelta(days=3))

        # extend Submission duedate with Submission/Deadline invitation
        pc_client.post_invitation_edit(
            invitations=submission_deadline_inv.id,
            content={
                'activation_date': { 'value': new_cdate },
                'deadline': { 'value': new_duedate }
            }
        )
        helpers.await_queue_edit(openreview_client, invitation='ABCD.cc/2025/Conference/-/Submission/Deadlines')
        helpers.await_queue_edit(openreview_client, edit_id='ABCD.cc/2025/Conference/-/Post_Submission-0-1', count=1)

        # assert submission deadline and expdate get updated, as well as post submission cdate
        submission_inv = openreview.tools.get_invitation(openreview_client, 'ABCD.cc/2025/Conference/-/Submission')
        assert submission_inv and submission_inv.cdate == new_cdate
        assert submission_inv.duedate == new_duedate
        assert submission_inv.expdate == new_duedate + 1800000
        post_submission_inv = openreview.tools.get_invitation(openreview_client, 'ABCD.cc/2025/Conference/-/Post_Submission')
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
                'note_content': {
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
                'note_license': {
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
        assert 'email_pcs' in submission_inv.content and submission_inv.content['email_pcs']['value'] == False

        ## edit Submission invitation content with Submission/Notifications invitation
        pc_client.post_invitation_edit(
            invitations=notifications_inv.id,
            content = {
                'email_authors': { 'value': True },
                'email_pcs': { 'value': True }
            }
        )

        submission_inv = openreview.tools.get_invitation(openreview_client, 'ABCD.cc/2025/Conference/-/Submission')
        assert 'email_authors' in submission_inv.content and submission_inv.content['email_authors']['value'] == True
        assert 'email_pcs' in submission_inv.content and submission_inv.content['email_pcs']['value'] == True

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

        submission_field_readers_inv = openreview.tools.get_invitation(openreview_client, 'ABCD.cc/2025/Conference/-/Post_Submission/Restrict_Field_Visibility')
        assert submission_field_readers_inv

        pc_client=openreview.api.OpenReviewClient(username='programchair@abcd.cc', password=helpers.strong_password)

        # expire submission deadline
        now = datetime.datetime.utcnow()
        new_cdate = openreview.tools.datetime_millis(now - datetime.timedelta(days=1))
        new_duedate = openreview.tools.datetime_millis(now - datetime.timedelta(minutes=31))

        pc_client.post_invitation_edit(
            invitations='ABCD.cc/2025/Conference/-/Submission/Deadlines',
            content={
                'activation_date': { 'value': new_cdate },
                'deadline': { 'value': new_duedate }
            }
        )
        helpers.await_queue_edit(openreview_client, invitation='ABCD.cc/2025/Conference/-/Submission/Deadlines')
        helpers.await_queue_edit(openreview_client, edit_id='ABCD.cc/2025/Conference/-/Post_Submission-0-1', count=2)

        submissions = openreview_client.get_notes(invitation='ABCD.cc/2025/Conference/-/Submission', sort='number:asc')
        assert len(submissions) == 10
        assert submissions[0].readers == ['ABCD.cc/2025/Conference', 'ABCD.cc/2025/Conference/Submission/1/Reviewers', 'ABCD.cc/2025/Conference/Submission/1/Authors']
        assert submissions[0].content['authors']['readers'] == ['ABCD.cc/2025/Conference', 'ABCD.cc/2025/Conference/Submission/1/Authors']
        assert submissions[0].content['authorids']['readers'] == ['ABCD.cc/2025/Conference', 'ABCD.cc/2025/Conference/Submission/1/Authors']
        assert submissions[0].content['venueid']['value'] == 'ABCD.cc/2025/Conference/Submission'
        assert submissions[0].content['venue']['value'] == 'ABCD 2025 Conference'

         # allow reviewers to see pdf
        pc_client.post_invitation_edit(
            invitations=submission_field_readers_inv.id,
            content = {
                'author_readers': { 'value': ['ABCD.cc/2025/Conference', 'ABCD.cc/2025/Conference/Submission/${{4/id}/number}/Authors'] },
                'pdf_readers': { 'value': ['ABCD.cc/2025/Conference', 'ABCD.cc/2025/Conference/Submission/${{4/id}/number}/Reviewers', 'ABCD.cc/2025/Conference/Submission/${{4/id}/number}/Authors'] }
            }
        )
        helpers.await_queue_edit(openreview_client, edit_id='ABCD.cc/2025/Conference/-/Post_Submission-0-1', count=3)

        submissions = openreview_client.get_notes(invitation='ABCD.cc/2025/Conference/-/Submission', sort='number:asc')
        assert len(submissions) == 10
        assert submissions[0].content['pdf']['readers'] == ['ABCD.cc/2025/Conference', 'ABCD.cc/2025/Conference/Submission/1/Reviewers', 'ABCD.cc/2025/Conference/Submission/1/Authors']

    def test_review_stage(self, openreview_client, helpers):

        pc_client = openreview.api.OpenReviewClient(username='programchair@abcd.cc', password=helpers.strong_password)
        assert pc_client.get_invitation('ABCD.cc/2025/Conference/-/Official_Review')
        assert pc_client.get_invitation('ABCD.cc/2025/Conference/-/Official_Review/Deadlines')
        assert pc_client.get_invitation('ABCD.cc/2025/Conference/-/Official_Review/Form_Fields')
        assert pc_client.get_invitation('ABCD.cc/2025/Conference/-/Official_Review/Readers')

    def test_decision_stage(self, openreview_client, helpers):

        pc_client = openreview.api.OpenReviewClient(username='programchair@abcd.cc', password=helpers.strong_password)

        assert pc_client.get_invitation('ABCD.cc/2025/Conference/-/Decision')
        assert pc_client.get_invitation('ABCD.cc/2025/Conference/-/Decision/Deadlines')
        assert pc_client.get_invitation('ABCD.cc/2025/Conference/-/Decision/Readers')
