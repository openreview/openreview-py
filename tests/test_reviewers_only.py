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

class TestReviewersOnly():

    def test_setup(self, openreview_client, helpers):
        super_id = 'openreview.net'
        support_group_id = super_id + '/Support'

        helpers.create_user('programchair@abcd.cc', 'ProgramChair', 'ABCD')
        helpers.create_user('reviewer_one@abcd.cc', 'ReviewerOne', 'ABCD')
        helpers.create_user('reviewer_two@abcd.cc', 'ReviewerTwo', 'ABCD')
        helpers.create_user('reviewer_three@abcd.cc', 'ReviewerThree', 'ABCD')
        pc_client=openreview.api.OpenReviewClient(username='programchair@abcd.cc', password=helpers.strong_password)

        workflows_setup = workflows.Workflows(openreview_client, support_group_id, super_id)
        workflows_setup.setup()

        templates_invitations = templates.Templates(openreview_client, support_group_id, super_id)
        templates_invitations.setup()

        assert openreview_client.get_invitation('openreview.net/-/Edit')
        assert openreview_client.get_group('openreview.net/Support/Venue_Request')
        assert openreview_client.get_invitation('openreview.net/Support/Venue_Request/-/Reviewers_Only')
        assert openreview_client.get_invitation('openreview.net/Support/Venue_Request/Reviewers_Only/-/Deployment')

        assert openreview_client.get_invitation('openreview.net/Template/-/Reviewers_Invited_Group')
        assert openreview_client.get_invitation('openreview.net/Template/-/Reviewers_Invited_Recruitment')
        assert openreview_client.get_invitation('openreview.net/Template/-/Reviewers_Invited_Recruitment_Response')
        assert openreview_client.get_invitation('openreview.net/Template/-/Reviewers_Invited_Recruitment_Reminder')
        assert openreview_client.get_invitation('openreview.net/Template/-/Reviewers_Invited_Recruitment_Emails')
        assert openreview_client.get_invitation('openreview.net/Template/-/Reviewers_Invited_Declined_Group')
        assert openreview_client.get_invitation('openreview.net/Template/-/Group_Message')
        assert openreview_client.get_invitation('openreview.net/Template/-/Venue_Message')
        assert openreview_client.get_invitation('openreview.net/-/Article_Endorsement')
        assert openreview_client.get_invitation('openreview.net/-/Reviewers_Review_Count')
        assert openreview_client.get_invitation('openreview.net/-/Reviewers_Review_Assignment_Count')
        assert openreview_client.get_invitation('openreview.net/-/Reviewers_Review_Days_Late')

        now = datetime.datetime.now()
        due_date = now + datetime.timedelta(days=2)

        request = pc_client.post_note_edit(invitation='openreview.net/Support/Venue_Request/-/Reviewers_Only',
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
                    },
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
        assert openreview_client.get_invitation(f'openreview.net/Support/Venue_Request/Reviewers_Only{request.number}/-/Comment')
        assert openreview_client.get_invitation(f'openreview.net/Support/Venue_Request/Reviewers_Only{request.number}/-/Deployment')
        assert openreview.tools.get_group(openreview_client, 'ABCD.cc/2025/Conference/Program_Chairs') is None

        # deploy the venue
        edit = openreview_client.post_note_edit(invitation=f'openreview.net/Support/Venue_Request/Reviewers_Only{request.number}/-/Deployment',
            signatures=[support_group_id],
            note=openreview.api.Note(
                id=request.id,
                content={
                    'venue_id': { 'value': 'ABCD.cc/2025/Conference' }
                }
            ))
        
        helpers.await_queue_edit(openreview_client, edit_id=edit['id'])
        helpers.await_queue_edit(openreview_client, invitation='openreview.net/Template/-/Submission')
        helpers.await_queue_edit(openreview_client, invitation='openreview.net/Template/-/Submission_Change_Before_Bidding')
        helpers.await_queue_edit(openreview_client, invitation='openreview.net/Template/-/Submission_Change_Before_Reviewing')
        helpers.await_queue_edit(openreview_client, invitation='openreview.net/Template/-/Reviewer_Bid')

        helpers.await_queue_edit(openreview_client, 'ABCD.cc/2025/Conference/-/Withdrawal_Request-0-1', count=1)
        helpers.await_queue_edit(openreview_client, 'ABCD.cc/2025/Conference/-/Desk_Rejection-0-1', count=1)
        helpers.await_queue_edit(openreview_client, 'ABCD.cc/2025/Conference/Reviewers/-/Submission_Group-0-1', count=1)
        helpers.await_queue_edit(openreview_client, 'ABCD.cc/2025/Conference/-/Submission_Change_Before_Bidding-0-1', count=1)

        group = openreview.tools.get_group(openreview_client, 'ABCD.cc/2025/Conference')
        assert group.domain == 'ABCD.cc/2025/Conference'
        assert group.members == ['openreview.net/Template', 'ABCD.cc/2025/Conference/Program_Chairs', 'ABCD.cc/2025/Conference/Automated_Administrator']
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

        group = openreview.tools.get_group(openreview_client, 'ABCD.cc/2025/Conference/Reviewers')
        assert group.domain == 'ABCD.cc/2025/Conference'

        group = openreview.tools.get_group(openreview_client, 'ABCD.cc/2025/Conference/Reviewers/Invited')
        assert group.domain == 'ABCD.cc/2025/Conference'        

        group = openreview.tools.get_group(openreview_client, 'ABCD.cc/2025/Conference/Reviewers/Declined')
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
        post_submission_inv = openreview_client.get_invitation('ABCD.cc/2025/Conference/-/Submission_Change_Before_Bidding')
        assert post_submission_inv and post_submission_inv.cdate == submission_inv.expdate
        assert openreview_client.get_invitation('ABCD.cc/2025/Conference/-/Submission_Change_Before_Bidding/Restrict_Field_Visibility')
        assert openreview_client.get_invitation('ABCD.cc/2025/Conference/-/Submission_Change_Before_Reviewing')
        assert openreview_client.get_invitation('ABCD.cc/2025/Conference/-/Submission_Change_Before_Reviewing/Restrict_Field_Visibility')
        assert openreview_client.get_invitation('ABCD.cc/2025/Conference/-/Review')
        assert openreview_client.get_invitation('ABCD.cc/2025/Conference/-/Review_Release')
        assert openreview_client.get_invitation('ABCD.cc/2025/Conference/-/Review_Release/Dates')
        assert openreview_client.get_invitation('ABCD.cc/2025/Conference/-/Review_Release/Readers')
        assert openreview_client.get_invitation('ABCD.cc/2025/Conference/-/Decision')
        assert openreview_client.get_invitation('ABCD.cc/2025/Conference/-/Withdrawal_Request')
        assert openreview_client.get_invitation('ABCD.cc/2025/Conference/-/Withdrawal_Request/Dates')
        assert openreview_client.get_invitation('ABCD.cc/2025/Conference/-/Withdrawal')
        assert openreview_client.get_invitation('ABCD.cc/2025/Conference/-/Withdrawal/Readers')
        assert openreview_client.get_invitation('ABCD.cc/2025/Conference/-/Withdraw_Expiration')
        assert openreview_client.get_invitation('ABCD.cc/2025/Conference/-/Unwithdrawal')
        assert openreview_client.get_invitation('ABCD.cc/2025/Conference/-/Desk_Rejection')
        assert openreview_client.get_invitation('ABCD.cc/2025/Conference/-/Desk_Rejected_Submission')
        assert openreview_client.get_invitation('ABCD.cc/2025/Conference/-/Desk_Rejected_Submission/Readers')
        assert openreview_client.get_invitation('ABCD.cc/2025/Conference/-/Desk_Reject_Expiration')
        assert openreview_client.get_invitation('ABCD.cc/2025/Conference/-/Desk_Rejection_Reversion')
        assert openreview_client.get_invitation('ABCD.cc/2025/Conference/Reviewers/-/Bid')
        assert openreview_client.get_invitation('ABCD.cc/2025/Conference/Reviewers/-/Bid/Dates')
        assert openreview_client.get_invitation('ABCD.cc/2025/Conference/Reviewers/-/Bid/Settings')
        assert openreview_client.get_invitation('ABCD.cc/2025/Conference/-/Venue_Information')
        assert openreview_client.get_invitation('ABCD.cc/2025/Conference/-/Email_Reviews_to_Authors')
        assert openreview_client.get_invitation('ABCD.cc/2025/Conference/-/Email_Decisions_to_Authors')
        assert openreview_client.get_invitation('ABCD.cc/2025/Conference/Reviewers/-/Submission_Group')
        invitation =  openreview_client.get_invitation('ABCD.cc/2025/Conference/Reviewers/Invited/-/Recruitment')
        assert 3000 == invitation.post_processes[0]['delay']
        assert openreview_client.get_invitation('ABCD.cc/2025/Conference/Reviewers/Invited/-/Recruitment_Response')
        assert openreview_client.get_invitation('ABCD.cc/2025/Conference/Reviewers/Invited/-/Recruitment_Response/Dates')
        assert openreview_client.get_invitation('ABCD.cc/2025/Conference/Reviewers/Invited/-/Message')
        assert openreview_client.get_invitation('ABCD.cc/2025/Conference/-/Message')
        assert openreview_client.get_invitation('ABCD.cc/2025/Conference/Authors/-/Message')
        assert openreview_client.get_invitation('ABCD.cc/2025/Conference/Reviewers/-/Message')
        assert openreview_client.get_invitation('ABCD.cc/2025/Conference/Reviewers/-/Members')
        assert openreview_client.get_invitation('ABCD.cc/2025/Conference/Program_Chairs/-/Members')

        # check domain object
        domain_content = openreview_client.get_group('ABCD.cc/2025/Conference').content
        assert domain_content['reviewers_invited_id']['value'] == 'ABCD.cc/2025/Conference/Reviewers/Invited'
        
        request_form = pc_client.get_note(request.id)
        assert request_form
        assert any(field not in request_form.content for field in ['venue_start_date', 'program_chair_emails', 'contact_email', 'submission_start_date', 'submission_deadline', 'submission_license'])
        assert 'program_chair_console' in request_form.content and request_form.content['program_chair_console']['value'] == 'https://openreview.net/group?id=ABCD.cc/2025/Conference/Program_Chairs'
        assert 'workflow_timeline' in request_form.content and request_form.content['workflow_timeline']['value'] == 'https://openreview.net/group/info?id=ABCD.cc/2025/Conference'

        # extend submission deadline
        now = datetime.datetime.now()
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
        helpers.await_queue_edit(openreview_client, 'ABCD.cc/2025/Conference/-/Withdrawal_Request-0-1', count=2)
        helpers.await_queue_edit(openreview_client, 'ABCD.cc/2025/Conference/-/Desk_Rejection-0-1', count=2)
        helpers.await_queue_edit(openreview_client, 'ABCD.cc/2025/Conference/Reviewers/-/Submission_Group-0-1', count=2)
        helpers.await_queue_edit(openreview_client, 'ABCD.cc/2025/Conference/-/Submission_Change_Before_Bidding-0-1', count=2)

        # assert submission deadline and expdate get updated, as well as post submission cdate
        submission_inv = openreview.tools.get_invitation(openreview_client, 'ABCD.cc/2025/Conference/-/Submission')
        assert submission_inv and submission_inv.cdate == new_cdate
        assert submission_inv.duedate == new_duedate
        assert submission_inv.expdate == new_duedate + 1800000
        post_submission_inv = openreview.tools.get_invitation(openreview_client, 'ABCD.cc/2025/Conference/-/Submission_Change_Before_Bidding')
        assert post_submission_inv and post_submission_inv.cdate == submission_inv.expdate

        content_inv = openreview.tools.get_invitation(openreview_client, 'ABCD.cc/2025/Conference/-/Submission/Form_Fields')
        assert content_inv
        assert 'subject_area' not in submission_inv.edit['note']['content']
        assert 'keywords' in submission_inv.edit['note']['content']
        assert submission_inv.edit['note']['license']['param']['enum'] == [{'value': 'CC BY 4.0', 'optional': True, 'description': 'CC BY 4.0'}]

        ## edit Submission content with Submission/Form_Fields invitation
        pc_client.post_invitation_edit(
            invitations=content_inv.id,
            content = {
                'content': {
                    'value': {
                        'subject_area': {
                            'order': 10,
                            'description': 'Select one subject area.',
                            'value': {
                                'param': {
                                    'type': 'string',
                                    'enum': [
                                        '3D from multi-view and sensors',
                                        '3D from single images',
                                        'Adversarial attack and defense',
                                        'Autonomous driving',
                                        'Biometrics',
                                        'Computational imaging',
                                        'Computer vision for social good',
                                        'Computer vision theory',
                                        'Datasets and evaluation'
                                    ],
                                    'input': 'select'
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

        helpers.await_queue_edit(openreview_client, invitation=f'ABCD.cc/2025/Conference/-/Submission/Form_Fields')
        helpers.await_queue_edit(openreview_client, edit_id='ABCD.cc/2025/Conference/-/Camera_Ready_Revision-0-1', count=2)

        submission_inv = openreview.tools.get_invitation(openreview_client, 'ABCD.cc/2025/Conference/-/Submission')
        assert submission_inv and 'subject_area' in submission_inv.edit['note']['content']
        assert 'keywords' not in submission_inv.edit['note']['content']
        content_keys = submission_inv.edit['note']['content'].keys()
        assert all(field in content_keys for field in ['title', 'authors', 'authorids', 'TLDR', 'abstract', 'pdf'])
        assert submission_inv.edit['note']['license']['param']['enum'] == [
            {
            'value': 'CC BY-NC-ND 4.0',
            'optional': True,
            'description': 'CC BY-NC-ND 4.0'
          },
          {
            'value': 'CC BY-NC-SA 4.0',
            'optional': True,
            'description': 'CC BY-NC-SA 4.0'
          }
        ]

        # assert camera-ready revision invitation has been updated
        revision_inv = openreview.tools.get_invitation(openreview_client, 'ABCD.cc/2025/Conference/-/Camera_Ready_Revision')
        invitation_content = revision_inv.edit['invitation']['edit']['note']['content']
        assert revision_inv and 'subject_area' in invitation_content
        assert 'keywords' not in invitation_content
        content_keys = invitation_content.keys()
        assert all(field in content_keys for field in ['title', 'authors', 'authorids', 'TLDR', 'abstract', 'pdf'])

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

    def test_recruit_reviewers(self, openreview_client, helpers, selenium, request_page):

        # use invitation to recruit reviewers
        edit = openreview_client.post_group_edit(
                invitation='ABCD.cc/2025/Conference/Reviewers/Invited/-/Recruitment',
                content={
                    'invitee_details': { 'value':  'reviewer_one@abcd.cc, Reviewer ABCDOne\nreviewer_two@abcd.cc, Reviewer ABCDTwo\nreviewer@mail.com' },
                    'invite_message_subject_template': { 'value': '[ABCD 2025] Invitation to serve as expert Reviewer' },
                    'invite_message_body_template': { 'value': 'Dear Reviewer {{fullname}},\n\nWe are pleased to invite you to serve as a reviewer for the ABCD 2025 Conference.\n\nPlease accept or decline the invitation using the link below:\n\n{{invitation_url}}\n\nBest regards,\nABCD 2025 Program Chairs' },
                },
                group=openreview.api.Group()
            )
        helpers.await_queue_edit(openreview_client, edit_id=edit['id'])

        invited_group = openreview_client.get_group('ABCD.cc/2025/Conference/Reviewers/Invited')
        assert set(invited_group.members) == {'reviewer_one@abcd.cc', 'reviewer_two@abcd.cc', 'reviewer@mail.com'}
        assert '[ABCD 2025] Invitation to serve as Reviewer'  == invited_group.content['invite_message_subject_template']['value']
        assert openreview_client.get_group('ABCD.cc/2025/Conference/Reviewers/Declined').members == []
        assert openreview_client.get_group('ABCD.cc/2025/Conference/Reviewers').members == []

        messages = openreview_client.get_messages(to='reviewer_one@abcd.cc', subject = '[ABCD 2025] Invitation to serve as expert Reviewer')
        assert len(messages) == 1

        text = messages[0]['content']['text']

        ## Accept invitation
        invitation_url = re.search('https://.*\n', text).group(0).replace('https://openreview.net', 'http://localhost:3030').replace('&amp;', '&')[:-1]        
        helpers.respond_invitation(selenium, request_page, invitation_url, accept=True)

        edits = openreview_client.get_note_edits(invitation='ABCD.cc/2025/Conference/Reviewers/Invited/-/Recruitment_Response')
        assert len(edits) == 1
        helpers.await_queue_edit(openreview_client, edit_id=edits[0].id)
        
        assert set(openreview_client.get_group('ABCD.cc/2025/Conference/Reviewers/Invited').members) == {'reviewer_one@abcd.cc', 'reviewer_two@abcd.cc', 'reviewer@mail.com'}
        assert openreview_client.get_group('ABCD.cc/2025/Conference/Reviewers/Declined').members == []
        assert openreview_client.get_group('ABCD.cc/2025/Conference/Reviewers').members == ['reviewer_one@abcd.cc']

        messages = openreview_client.get_messages(to='reviewer_one@abcd.cc', subject = '[ABCD 2025] Reviewers Invitation accepted')
        assert len(messages) == 1        

        ## Accept invitation with invalid key
        invalid_accept_url = 'http://localhost:3030/invitation?id=ABCD.cc/2025/Conference/Reviewers/Invited/-/Recruitment_Response&user=reviewer_one@abcd.cc&key=1234'
        helpers.respond_invitation(selenium, request_page, invalid_accept_url, accept=True)
        error_message = selenium.find_element(By.CLASS_NAME, 'important_message')
        assert 'Wrong key, please refer back to the recruitment email' == error_message.text
    
        ## Accept invitation with non invited email
        openreview_client.remove_members_from_group('ABCD.cc/2025/Conference/Reviewers/Invited', ['reviewer_one@abcd.cc'])
        helpers.respond_invitation(selenium, request_page, invitation_url, accept=True)
        error_message = selenium.find_element(By.CLASS_NAME, 'important_message')
        assert 'User not in invited group, please accept the invitation using the email address you were invited with' == error_message.text
        
        ## Decline invitation
        openreview_client.add_members_to_group('ABCD.cc/2025/Conference/Reviewers/Invited', ['reviewer_one@abcd.cc'])
        helpers.respond_invitation(selenium, request_page, invitation_url, accept=False)

        edits = openreview_client.get_note_edits(invitation='ABCD.cc/2025/Conference/Reviewers/Invited/-/Recruitment_Response', sort='tcdate:desc')
        assert len(edits) == 2
        helpers.await_queue_edit(openreview_client, edit_id=edits[0].id)
        
        assert set(openreview_client.get_group('ABCD.cc/2025/Conference/Reviewers/Invited').members) == {'reviewer_one@abcd.cc', 'reviewer_two@abcd.cc', 'reviewer@mail.com'}
        assert openreview_client.get_group('ABCD.cc/2025/Conference/Reviewers/Declined').members == ['reviewer_one@abcd.cc']
        assert openreview_client.get_group('ABCD.cc/2025/Conference/Reviewers').members == []

        messages = openreview_client.get_messages(to='reviewer_one@abcd.cc', subject = '[ABCD 2025] Reviewers Invitation declined')
        assert len(messages) == 1         

        ## Accept invitation again
        invitation_url = re.search('https://.*\n', text).group(0).replace('https://openreview.net', 'http://localhost:3030').replace('&amp;', '&')[:-1]        
        helpers.respond_invitation(selenium, request_page, invitation_url, accept=True)

        edits = openreview_client.get_note_edits(invitation='ABCD.cc/2025/Conference/Reviewers/Invited/-/Recruitment_Response', sort='tcdate:desc')
        assert len(edits) == 3
        helpers.await_queue_edit(openreview_client, edit_id=edits[0].id)
        
        assert set(openreview_client.get_group('ABCD.cc/2025/Conference/Reviewers/Invited').members) == {'reviewer_one@abcd.cc', 'reviewer_two@abcd.cc', 'reviewer@mail.com'}
        assert openreview_client.get_group('ABCD.cc/2025/Conference/Reviewers/Declined').members == []
        assert openreview_client.get_group('ABCD.cc/2025/Conference/Reviewers').members == ['reviewer_one@abcd.cc']

        messages = openreview_client.get_messages(to='reviewer_one@abcd.cc', subject = '[ABCD 2025] Reviewers Invitation accepted')
        assert len(messages) == 2

        ## Remind reviewers to respond the invitation
        edit = openreview_client.post_group_edit(
                invitation='ABCD.cc/2025/Conference/Reviewers/Invited/-/Recruitment_Reminder',
                content={
                    'invite_reminder_message_subject_template': { 'value': '[ABCD 2025] Reminder: Invitation to serve as expert Reviewer' },
                    'invite_reminder_message_body_template': { 'value': 'Dear Reviewer {{fullname}},\n\nWe are pleased to invite you to serve as a reviewer for the ABCD 2025 Conference.\n\nPlease accept or decline the invitation using the link below:\n\n{{invitation_url}}\n\nBest regards,\nABCD 2025 Program Chairs' },
                },
                group=openreview.api.Group()
            )
        helpers.await_queue_edit(openreview_client, edit_id=edit['id'])
    
        messages = openreview_client.get_messages(subject = '[ABCD 2025] Reminder: Invitation to serve as expert Reviewer')
        assert len(messages) == 2

        assert openreview_client.get_messages(to='reviewer@mail.com', subject = '[ABCD 2025] Reminder: Invitation to serve as expert Reviewer')
        assert openreview_client.get_messages(to='reviewer_two@abcd.cc', subject = '[ABCD 2025] Reminder: Invitation to serve as expert Reviewer')

        ## Invite more reviewers and wait for the auto reminder
        edit = openreview_client.post_group_edit(
                invitation='ABCD.cc/2025/Conference/Reviewers/Invited/-/Recruitment',
                content={
                    'invitee_details': { 'value':  'reviewer@yahoo.com\nprogramchair@abcd.cc' },
                    'invite_message_subject_template': { 'value': '[ABCD 2025] Invitation to serve as senior Reviewer' },
                    'invite_message_body_template': { 'value': 'Dear Reviewer {{fullname}},\n\nWe are pleased to invite you to serve as a reviewer for the ABCD 2025 Conference.\n\nPlease accept or decline the invitation using the link below:\n\n{{invitation_url}}\n\nBest regards,\nABCD 2025 Program Chairs' },
                },
                group=openreview.api.Group()
            )
        helpers.await_queue_edit(openreview_client, edit_id=edit['id'], count=1)

        invited_group = openreview_client.get_group('ABCD.cc/2025/Conference/Reviewers/Invited')
        assert set(invited_group.members) == {'reviewer_one@abcd.cc', 'reviewer_two@abcd.cc', 'reviewer@mail.com', 'reviewer@yahoo.com', 'programchair@abcd.cc'}        

        helpers.await_queue_edit(openreview_client, edit_id=edit['id'], count=2) # wait for the reminder to be sent
        messages = openreview_client.get_messages(subject = '[ABCD 2025] Reminder: Invitation to serve as expert Reviewer')
        assert len(messages) == 2


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
                    'email_sharing': { 'value': 'We authorize the sharing of all author emails with Program Chairs.' },
                    'data_release': { 'value': 'We authorize the release of our submission and author names to the public in the event of acceptance.' },
                }
            )

            if i == 5:
                note.content['authors']['value'].append('ReviewerOne ABCD')
                note.content['authorids']['value'].append('~ReviewerOne_ABCD1')

            test_client.post_note_edit(invitation='ABCD.cc/2025/Conference/-/Submission',
                signatures=['~SomeFirstName_User1'],
                note=note)

        helpers.await_queue_edit(openreview_client, invitation='ABCD.cc/2025/Conference/-/Submission', count=10)

        submissions = openreview_client.get_notes(invitation='ABCD.cc/2025/Conference/-/Submission', sort='number:asc')
        assert len(submissions) == 10
        assert submissions[-1].readers == ['ABCD.cc/2025/Conference', '~SomeFirstName_User1', 'andrew@umass.edu']
        assert submissions[0].parent_invitations == 'openreview.net/Template/-/Submission'

        messages = openreview_client.get_messages(to='test@mail.com', subject='ABCD 2025 has received your submission titled Paper title .*')
        assert messages and len(messages) == 10
        messages = openreview_client.get_messages(to='test@mail.com', subject='ABCD 2025 has received your submission titled Paper title 1')
        assert messages[0]['content']['text'] == f'Your submission to ABCD 2025 has been posted.\n\nSubmission Number: 1\n\nTitle: Paper title 1 \n\nAbstract: This is an abstract 1\n\nTo view your submission, click here: https://openreview.net/forum?id={submissions[0].id}\n\nPlease note that responding to this email will direct your reply to abcd2025.programchairs@gmail.com.\n'

        messages = openreview_client.get_messages(to='programchair@abcd.cc', subject='ABCD 2025 has received a new submission titled Paper title .*')
        assert messages and len(messages) == 10

        submission_field_readers_inv = openreview.tools.get_invitation(openreview_client, 'ABCD.cc/2025/Conference/-/Submission_Change_Before_Bidding/Restrict_Field_Visibility')
        assert submission_field_readers_inv

        pc_client=openreview.api.OpenReviewClient(username='programchair@abcd.cc', password=helpers.strong_password)

        # expire submission deadline
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
        assert len(submissions) == 10
        assert submissions[0].readers == ['ABCD.cc/2025/Conference', 'ABCD.cc/2025/Conference/Reviewers', 'ABCD.cc/2025/Conference/Submission1/Authors']
        assert submissions[0].content['authors']['readers'] == ['ABCD.cc/2025/Conference', 'ABCD.cc/2025/Conference/Submission1/Authors']
        assert submissions[0].content['authorids']['readers'] == ['ABCD.cc/2025/Conference', 'ABCD.cc/2025/Conference/Submission1/Authors']
        assert 'readers' not in submissions[0].content['pdf']
        assert submissions[0].content['venueid']['value'] == 'ABCD.cc/2025/Conference/Submission'
        assert submissions[0].content['venue']['value'] == 'ABCD 2025 Conference Submission'

        submission_groups = openreview_client.get_all_groups(prefix='ABCD.cc/2025/Conference/Submission')
        reviewer_groups = [group for group in submission_groups if group.id.endswith('/Reviewers')]
        assert len(reviewer_groups) == 10

         # hide pdf from reviewers
        pc_client.post_invitation_edit(
            invitations=submission_field_readers_inv.id,
            content = {
                'content_readers': {
                    'value': {
                        'authors': {
                            'readers': [
                                'ABCD.cc/2025/Conference',
                                'ABCD.cc/2025/Conference/Submission${{4/id}/number}/Authors'
                            ]
                        },
                        'authorids': {
                            'readers': [
                                'ABCD.cc/2025/Conference',
                                'ABCD.cc/2025/Conference/Submission${{4/id}/number}/Authors'
                            ]
                        },
                        'pdf': {
                            'readers': [
                                'ABCD.cc/2025/Conference',
                                'ABCD.cc/2025/Conference/Submission${{4/id}/number}/Authors'
                            ]
                        }
                    }
                }
            }
        )
        helpers.await_queue_edit(openreview_client, edit_id='ABCD.cc/2025/Conference/-/Submission_Change_Before_Bidding-0-1', count=4)

        submissions = openreview_client.get_notes(invitation='ABCD.cc/2025/Conference/-/Submission', sort='number:asc')
        assert len(submissions) == 10
        assert submissions[0].content['pdf']['readers'] == ['ABCD.cc/2025/Conference', 'ABCD.cc/2025/Conference/Submission1/Authors']

        withdrawal_invitations = openreview_client.get_all_invitations(invitation='ABCD.cc/2025/Conference/-/Withdrawal_Request')
        assert len(withdrawal_invitations) == 10

        desk_rejection_invitations = openreview_client.get_all_invitations(invitation='ABCD.cc/2025/Conference/-/Desk_Rejection')
        assert len(desk_rejection_invitations) == 10


        ## test message all authors
        pc_client.post_message(
            invitation='ABCD.cc/2025/Conference/-/Message',
            recipients=['ABCD.cc/2025/Conference/Authors'], 
            subject='Test message to all authors', 
            message='Test message to all authors')
        
        messages = openreview_client.get_messages(subject='Test message to all authors')
        assert len(messages) == 12

    def test_reviewer_bidding(self, openreview_client, helpers, request_page, selenium):

        pc_client=openreview.api.OpenReviewClient(username='programchair@abcd.cc', password=helpers.strong_password)

        bid_invitation = openreview_client.get_invitation('ABCD.cc/2025/Conference/Reviewers/-/Bid')
        assert bid_invitation
        assert bid_invitation.edit['label']['param']['enum'] == ['Very High', 'High', 'Neutral', 'Low', 'Very Low']
        assert bid_invitation.minReplies == 50

        #open bidding
        now = datetime.datetime.now()
        new_cdate = openreview.tools.datetime_millis(now)
        new_duedate = openreview.tools.datetime_millis(now + datetime.timedelta(days=5))

        pc_client.post_invitation_edit(
            invitations='ABCD.cc/2025/Conference/Reviewers/-/Bid/Dates',
            content={
                'activation_date': { 'value': new_cdate },
                'due_date': { 'value': new_duedate },
                'expiration_date': { 'value': new_duedate }
            }
        )

        # change bidding options
        pc_client.post_invitation_edit(
            invitations='ABCD.cc/2025/Conference/Reviewers/-/Bid/Settings',
            content={
                'bid_count': { 'value': 25 },
                'labels': { 'value': ['High', 'Low', 'Conflict'] }
            }
        )

        bid_invitation = openreview_client.get_invitation('ABCD.cc/2025/Conference/Reviewers/-/Bid')
        assert bid_invitation
        assert bid_invitation.duedate == new_duedate
        assert bid_invitation.expdate == new_duedate
        assert bid_invitation.edit['label']['param']['enum'] == ['High', 'Low', 'Conflict']
        assert bid_invitation.minReplies == 25

        # openreview_client.add_members_to_group('ABCD.cc/2025/Conference/Reviewers', ['reviewer_one@abcd.cc'])

        reviewer_client = OpenReviewClient(username='reviewer_one@abcd.cc', password=helpers.strong_password)

        submissions = reviewer_client.get_all_notes(content={'venueid': 'ABCD.cc/2025/Conference/Submission'}, sort='number:asc')
        assert len(submissions) == 10

        invitation = openreview_client.get_invitation('ABCD.cc/2025/Conference/Reviewers/-/Bid')
        assert invitation.edit['tail']['param']['options']['group'] == 'ABCD.cc/2025/Conference/Reviewers'

        # Check that reviewers bid console loads
        request_page(selenium, f'http://localhost:3030/invitation?id={invitation.id}', reviewer_client.token, wait_for_element='header')
        header = selenium.find_element(By.ID, 'header')
        assert 'Reviewer Bidding Console' in header.text

    def test_reviewers_setup_matching(self, openreview_client, helpers):

        openreview_client.add_members_to_group('ABCD.cc/2025/Conference/Reviewers', ['reviewer_two@abcd.cc', 'reviewer_three@abcd.cc'])

        #upload affinity scores file
        submissions = openreview_client.get_all_notes(content={'venueid': 'ABCD.cc/2025/Conference/Submission'})
        with open(os.path.join(os.path.dirname(__file__), 'data/rev_scores_venue.csv'), 'w') as file_handle:
            writer = csv.writer(file_handle)
            for submission in submissions:
                for rev in openreview_client.get_group('ABCD.cc/2025/Conference/Reviewers').members:
                    writer.writerow([submission.id, rev, round(random.random(), 2)])

        openreview_client.add_members_to_group('ABCD.cc/2025/Conference/Reviewers', 'reviewer_noprofile@iccv.cc')

        conflicts_invitation = openreview_client.get_invitation('ABCD.cc/2025/Conference/Reviewers/-/Conflict')
        assert conflicts_invitation
        assert conflicts_invitation.content['reviewers_conflict_policy']['value'] == 'Default'
        assert conflicts_invitation.content['reviewers_conflict_n_years']['value'] == 0
        domain_content = openreview_client.get_group('ABCD.cc/2025/Conference').content
        assert domain_content['reviewers_conflict_policy']['value'] == 'Default'
        assert domain_content['reviewers_conflict_n_years']['value'] == 0
        assert openreview_client.get_invitation('ABCD.cc/2025/Conference/Reviewers/-/Conflict/Dates')
        assert openreview_client.get_invitation('ABCD.cc/2025/Conference/Reviewers/-/Conflict/Policy')

        # edit conflict policy
        pc_client = openreview.api.OpenReviewClient(username='programchair@abcd.cc', password=helpers.strong_password)

        pc_client.post_invitation_edit(
            invitations='ABCD.cc/2025/Conference/Reviewers/-/Conflict/Policy',
            content={
                'conflict_policy': { 'value': 'NeurIPS' },
                'conflict_n_years': { 'value': 3 }
            }
        )
        helpers.await_queue_edit(openreview_client, invitation=f'ABCD.cc/2025/Conference/Reviewers/-/Conflict/Policy')

        conflicts_inv = pc_client.get_invitation('ABCD.cc/2025/Conference/Reviewers/-/Conflict')
        assert conflicts_inv
        assert conflicts_inv.content['reviewers_conflict_policy']['value'] == 'NeurIPS'
        assert conflicts_inv.content['reviewers_conflict_n_years']['value'] == 3
        domain_content = openreview_client.get_group('ABCD.cc/2025/Conference').content
        assert domain_content['reviewers_conflict_policy']['value'] == 'NeurIPS'
        assert domain_content['reviewers_conflict_n_years']['value'] == 3

        # trigger date process
        now = datetime.datetime.now()
        new_cdate = openreview.tools.datetime_millis(now)
        pc_client.post_invitation_edit(
            invitations='ABCD.cc/2025/Conference/Reviewers/-/Conflict/Dates',
            content={
                'activation_date': { 'value': new_cdate }
            }
        )
        helpers.await_queue_edit(openreview_client, 'ABCD.cc/2025/Conference/Reviewers/-/Conflict-0-1', count=2)

        conflicts = pc_client.get_edges_count(invitation='ABCD.cc/2025/Conference/Reviewers/-/Conflict')
        assert conflicts == 12

        scores_invitation = openreview_client.get_invitation('ABCD.cc/2025/Conference/Reviewers/-/Affinity_Score')
        assert scores_invitation
        assert openreview_client.get_invitation('ABCD.cc/2025/Conference/Reviewers/-/Affinity_Score/Dates')
        assert openreview_client.get_invitation('ABCD.cc/2025/Conference/Reviewers/-/Affinity_Score/Model')
        # assert openreview_client.get_invitation('ABCD.cc/2025/Conference/Reviewers/-/Affinity_Score/Upload_Scores')

        # affinity_scores_url = openreview_client.put_attachment(os.path.join(os.path.dirname(__file__), 'data/rev_scores_venue.csv'), 'ABCD.cc/2025/Conference/Reviewers/-/Affinity_Score/Upload_Scores', 'upload_affinity_scores')

        # pc_client.post_invitation_edit(
        #     invitations='ABCD.cc/2025/Conference/Reviewers/-/Affinity_Score/Upload_Scores',
        #     content={
        #         'upload_affinity_scores': { 'value': affinity_scores_url }
        #     }
        # )

        # # trigger affinity score upload
        # now = datetime.datetime.now()
        # new_cdate = openreview.tools.datetime_millis(now)
        # pc_client.post_invitation_edit(
        #     invitations='ABCD.cc/2025/Conference/Reviewers/-/Affinity_Score/Dates',
        #     content={
        #         'activation_date': { 'value': new_cdate }
        #     }
        # )
        # helpers.await_queue_edit(openreview_client, 'ABCD.cc/2025/Conference/Reviewers/-/Affinity_Score-0-1', count=2)

        # affinity_score_count =  openreview_client.get_edges_count(invitation='ABCD.cc/2025/Conference/Reviewers/-/Affinity_Score')
        # assert affinity_score_count == 10 * 3 ## submissions * reviewers

    def test_reviewers_deployment(self, openreview_client, helpers):

        pc_client = openreview.api.OpenReviewClient(username='programchair@abcd.cc', password=helpers.strong_password)

        assert openreview_client.get_invitation('ABCD.cc/2025/Conference/Reviewers/-/Affinity_Score')
        assert openreview_client.get_invitation('ABCD.cc/2025/Conference/Reviewers/-/Bid')
        assert openreview_client.get_invitation('ABCD.cc/2025/Conference/Reviewers/-/Conflict')
        assert openreview_client.get_invitation('ABCD.cc/2025/Conference/Reviewers/-/Assignment')
        assert openreview_client.get_invitation('ABCD.cc/2025/Conference/Reviewers/-/Proposed_Assignment')
        assert openreview_client.get_invitation('ABCD.cc/2025/Conference/Reviewers/-/Aggregate_Score')
        assert openreview_client.get_invitation('ABCD.cc/2025/Conference/Reviewers/-/Proposed_Assignment')
        assert openreview_client.get_invitation('ABCD.cc/2025/Conference/Reviewers/-/Custom_Max_Papers')
        assert openreview_client.get_invitation('ABCD.cc/2025/Conference/Reviewers/-/Custom_User_Demands')
        assert openreview_client.get_invitation('ABCD.cc/2025/Conference/Reviewers/-/Assignment_Configuration')
        assert openreview_client.get_invitation('ABCD.cc/2025/Conference/-/Deploy_Reviewer_Assignment')
        assert openreview_client.get_invitation('ABCD.cc/2025/Conference/-/Deploy_Reviewer_Assignment/Match')

        #submit Assignment_Configuration
        config_note = openreview_client.post_note_edit(
            invitation='ABCD.cc/2025/Conference/Reviewers/-/Assignment_Configuration',
            readers=['ABCD.cc/2025/Conference'],
            writers=['ABCD.cc/2025/Conference'],
            signatures=['ABCD.cc/2025/Conference'],
            note=openreview.api.Note(
                content={
                    'title': { 'value': 'rev-matching-1'},
                    'user_demand': { 'value': '2'},
                    'max_papers': { 'value': '10'},
                    'min_papers': { 'value': '5'},
                    'alternates': { 'value': '2'},
                    'paper_invitation': { 'value': 'ABCD.cc/2025/Conference/-/Submission&content.venueid=ABCD.cc/2025/Conference/Submission'},
                    'match_group': { 'value': 'ABCD.cc/2025/Conference/Reviewers'},
                    'scores_specification': {
                        'value': {
                            'ABCD.cc/2025/Conference/Reviewers/-/Affinity_Score': {
                                'weight': 1,
                                'default': 0
                            },
                            'ABCD.cc/2025/Conference/Reviewers/-/Bid': {
                                'weight': 1,
                                'default': 0,
                                'translate_map': {
                                    'Very High': 1.0,
                                    'High': 0.5,
                                    'Neutral': 0.0,
                                    'Low': -0.5,
                                    'Very Low': -1.0
                                }
                            }
                        }
                    },
                    'aggregate_score_invitation': { 'value': 'ABCD.cc/2025/Conference/Reviewers/-/Aggregate_Score'},
                    'conflicts_invitation': { 'value': 'ABCD.cc/2025/Conference/Reviewers/-/Conflict'},
                    'solver': { 'value': 'FairFlow'},
                    'status': { 'value': 'Initialized'},
                }
            )
        )
        helpers.await_queue_edit(openreview_client, invitation=f'ABCD.cc/2025/Conference/Reviewers/-/Assignment_Configuration')

        match_invitation = openreview_client.get_invitation('ABCD.cc/2025/Conference/-/Deploy_Reviewer_Assignment/Match')
        assert match_invitation.edit['content']['match_name']['value']['param']['enum'] == ['rev-matching-1']

        now = datetime.datetime.now()
        now = openreview.tools.datetime_millis(now)

        # try to deploy initialized configuration and get an error
        with pytest.raises(openreview.OpenReviewException, match=r'The matching configuration with title "rev-matching-1" does not have status "Complete".'):
            pc_client.post_invitation_edit(
                invitations='ABCD.cc/2025/Conference/-/Deploy_Reviewer_Assignment/Match',
                content = {
                    'match_name': { 'value': 'rev-matching-1' },
                    'deploy_date': { 'value': now }
                }
            )

        # post proposed assignments to test deployment process
        submissions = pc_client.get_all_notes(content={'venueid': 'ABCD.cc/2025/Conference/Submission'}, sort='number:asc')
        assert len(submissions) == 10

        for reviewer in ['~ReviewerOne_ABCD1', '~ReviewerTwo_ABCD1']:
            openreview_client.post_edge(openreview.api.Edge(
                    invitation = 'ABCD.cc/2025/Conference/Reviewers/-/Proposed_Assignment',
                    head = submissions[0].id,
                    tail = reviewer,
                    signatures = ['ABCD.cc/2025/Conference/Program_Chairs'],
                    weight = 1,
                    label = 'rev-matching-1'
                ))

        for reviewer in ['~ReviewerTwo_ABCD1', '~ReviewerThree_ABCD1']:
            openreview_client.post_edge(openreview.api.Edge(
                    invitation = 'ABCD.cc/2025/Conference/Reviewers/-/Proposed_Assignment',
                    head = submissions[1].id,
                    tail = reviewer,
                    signatures = ['ABCD.cc/2025/Conference/Program_Chairs'],
                    weight = 1,
                    label = 'rev-matching-1'
                ))

        for reviewer in ['~ReviewerOne_ABCD1', '~ReviewerThree_ABCD1']:
            openreview_client.post_edge(openreview.api.Edge(
                    invitation = 'ABCD.cc/2025/Conference/Reviewers/-/Proposed_Assignment',
                    head = submissions[2].id,
                    tail = reviewer,
                    signatures = ['ABCD.cc/2025/Conference/Program_Chairs'],
                    weight = 1,
                    label = 'rev-matching-1'
                ))

        assert len(openreview_client.get_grouped_edges(
            invitation='ABCD.cc/2025/Conference/Reviewers/-/Proposed_Assignment',
            groupby='id'
        )) == 6

        assert len(openreview_client.get_grouped_edges(
            invitation='ABCD.cc/2025/Conference/Reviewers/-/Assignment',
            groupby='id'
        )) == 0

        #change status of configuration to complete
        openreview_client.post_note_edit(
            invitation='ABCD.cc/2025/Conference/-/Edit',
            signatures=['ABCD.cc/2025/Conference'],
            note=openreview.api.Note(
                id=config_note['note']['id'],
                content = {
                    'status': {
                        'value': 'Complete'
                    }
                }
            )
        )

        # deploy assignments
        now = datetime.datetime.now()
        cdate = openreview.tools.datetime_millis(now)
        openreview_client.post_invitation_edit(
            invitations='ABCD.cc/2025/Conference/-/Deploy_Reviewer_Assignment/Match',
            content = {
                'match_name': { 'value': 'rev-matching-1' },
                'deploy_date': { 'value': cdate }
            }
        )
        helpers.await_queue_edit(openreview_client,  edit_id=f'ABCD.cc/2025/Conference/-/Deploy_Reviewer_Assignment-0-1', count=2)

        grouped_edges = openreview_client.get_grouped_edges(invitation='ABCD.cc/2025/Conference/Reviewers/-/Assignment', groupby='id')
        assert len(grouped_edges) == 6

        for edges in grouped_edges:
            for edge in edges['values']:
                regex = 'ABCD.cc/2025/Conference/Submission.*[0-9]/Authors'
                assert re.match(regex, edge['nonreaders'][0])

        reviewers_one_group = openreview_client.get_group('ABCD.cc/2025/Conference/Submission1/Reviewers')
        assert '~ReviewerOne_ABCD1' in reviewers_one_group.members
        assert '~ReviewerTwo_ABCD1' in reviewers_one_group.members

        config_note = openreview_client.get_note(config_note['note']['id'])
        assert config_note.content['status']['value'] == 'Deployed'

    def test_review_stage(self, openreview_client, helpers):
        
        now = datetime.datetime.now()
        # manually trigger Submission_Chage_Before_Reviewing
        openreview_client.post_invitation_edit(
            invitations='ABCD.cc/2025/Conference/-/Edit',
            signatures=['ABCD.cc/2025/Conference'],
            invitation=openreview.api.Invitation(
                id='ABCD.cc/2025/Conference/-/Submission_Change_Before_Reviewing',
                cdate=openreview.tools.datetime_millis(now),
                signatures=['ABCD.cc/2025/Conference']
            )
        )
        helpers.await_queue_edit(openreview_client, 'ABCD.cc/2025/Conference/-/Submission_Change_Before_Reviewing-0-1', count=2)

        submissions = openreview_client.get_notes(invitation='ABCD.cc/2025/Conference/-/Submission', sort='number:asc')
        assert submissions[0].readers == ['ABCD.cc/2025/Conference', 'ABCD.cc/2025/Conference/Submission1/Reviewers', 'ABCD.cc/2025/Conference/Submission1/Authors']

        pc_client = openreview.api.OpenReviewClient(username='programchair@abcd.cc', password=helpers.strong_password)
        assert pc_client.get_invitation('ABCD.cc/2025/Conference/-/Review')
        assert pc_client.get_invitation('ABCD.cc/2025/Conference/-/Review/Dates')
        assert pc_client.get_invitation('ABCD.cc/2025/Conference/-/Review/Form_Fields')
        assert pc_client.get_invitation('ABCD.cc/2025/Conference/-/Review/Readers')
        assert pc_client.get_invitation('ABCD.cc/2025/Conference/-/Review/Notifications')

        # edit review stage fields
        pc_client.post_invitation_edit(
            invitations='ABCD.cc/2025/Conference/-/Review/Form_Fields',
            content = {
                'content': {
                    'value': {
                        'review': {
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
                        'review_rating': {
                            'order': 2,
                            'value': {
                            'param': {
                                'type': 'integer',
                                'enum': [
                                    {'value': 1, 'description': '1: strong reject'},
                                    {'value': 2, 'description': '2: reject, not good enough'},
                                    {'value': 3, 'description': '3: exactly at acceptance threshold'},
                                    {'value': 4, 'description': '4: accept, good paper'},
                                    {'value': 5, 'description': '5: strong accept, should be highlighted at the conference'}
                                ],
                                'input': 'radio'
                            }
                            },
                            'description': 'Please provide an \'overall score\' for this submission.'
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
                        'first_time_reviewer': {
                            'description': 'Is this your first time reviewing for ABCD?',
                            'order': 4,
                            'value': {
                                'param': {
                                    'type': 'string',
                                    'enum': [
                                        'Yes',
                                        'No'
                                    ],
                                    'input': 'checkbox'
                                }
                            },
                            'readers': [
                                'ABCD.cc/2025/Conference/Program_Chairs',
                                '${5/signatures}'
                            ]
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

        helpers.await_queue_edit(openreview_client, invitation=f'ABCD.cc/2025/Conference/-/Review/Form_Fields')

        review_inv = openreview.tools.get_invitation(openreview_client, 'ABCD.cc/2025/Conference/-/Review')
        assert 'title' not in review_inv.edit['invitation']['edit']['note']['content']
        assert 'rating' not in review_inv.edit['invitation']['edit']['note']['content']
        assert 'confidence' not in review_inv.edit['invitation']['edit']['note']['content']
        assert 'review' in review_inv.edit['invitation']['edit']['note']['content']
        assert 'review_rating' in review_inv.edit['invitation']['edit']['note']['content'] and review_inv.edit['invitation']['edit']['note']['content']['review_rating']['value']['param']['enum'][0] == {'value': 1, 'description': '1: strong reject'}
        assert 'review_confidence' in review_inv.edit['invitation']['edit']['note']['content']
        assert 'first_time_reviewer' in review_inv.edit['invitation']['edit']['note']['content']

        group = openreview_client.get_group('ABCD.cc/2025/Conference')
        assert 'review_rating' in group.content and group.content['review_rating']['value'] == 'review_rating'
        assert 'review_confidence' in group.content and group.content['review_confidence']['value'] == 'review_confidence'

        review_email = openreview.tools.get_invitation(openreview_client, 'ABCD.cc/2025/Conference/-/Email_Reviews_to_Authors/Fields_to_Include')
        assert review_email.edit['content']['fields']['value']['param']['enum'] == ['review', 'review_rating', 'review_confidence', 'first_time_reviewer']

        ## edit Official Review readers to include Reviewers/Submitted
        pc_client.post_invitation_edit(
            invitations='ABCD.cc/2025/Conference/-/Review/Readers',
            content = {
                'readers': {
                    'value':  [
                        'ABCD.cc/2025/Conference/Program_Chairs',
                        'ABCD.cc/2025/Conference/Submission${5/content/noteNumber/value}/Reviewers/Submitted'
                    ]
                }
            }
        )

        review_inv = openreview.tools.get_invitation(openreview_client, 'ABCD.cc/2025/Conference/-/Review')
        assert review_inv.edit['invitation']['edit']['note']['readers'] == [
            'ABCD.cc/2025/Conference/Program_Chairs',
            'ABCD.cc/2025/Conference/Submission${5/content/noteNumber/value}/Reviewers/Submitted'
        ]

        # create child invitations
        now = datetime.datetime.now()
        new_cdate = openreview.tools.datetime_millis(now)
        new_duedate = openreview.tools.datetime_millis(now + datetime.timedelta(days=3))

        pc_client.post_invitation_edit(
            invitations='ABCD.cc/2025/Conference/-/Review/Dates',
            content={
                'activation_date': { 'value': new_cdate },
                'due_date': { 'value': new_duedate },
                'expiration_date': { 'value': new_duedate }
            }
        )
        helpers.await_queue_edit(openreview_client, edit_id='ABCD.cc/2025/Conference/-/Review-0-1', count=2)

        invitations = openreview_client.get_invitations(invitation='ABCD.cc/2025/Conference/-/Review')
        assert len(invitations) == 10

        invitation  = openreview_client.get_invitation('ABCD.cc/2025/Conference/Submission1/-/Review')
        assert invitation and invitation.edit['readers'] == [
            'ABCD.cc/2025/Conference/Program_Chairs',
            'ABCD.cc/2025/Conference/Submission1/Reviewers/Submitted'
        ]

        reviewer_client=openreview.api.OpenReviewClient(username='reviewer_one@abcd.cc', password=helpers.strong_password)

        anon_groups = reviewer_client.get_groups(prefix='ABCD.cc/2025/Conference/Submission1/Reviewer_', signatory='~ReviewerOne_ABCD1')
        anon_group_id = anon_groups[0].id

        review_edit = reviewer_client.post_note_edit(
            invitation='ABCD.cc/2025/Conference/Submission1/-/Review',
            signatures=[anon_group_id],
            note=openreview.api.Note(
                content={
                    'review': { 'value': 'This is a good paper' },
                    'review_rating': { 'value': 5 },
                    'review_confidence': { 'value': 3 },
                    'first_time_reviewer': { 'value': 'Yes' }
                }
            )
        )

        helpers.await_queue_edit(openreview_client, edit_id=review_edit['id'])

        reviews = openreview_client.get_notes(parent_invitations='openreview.net/Template/-/Review.*')
        assert len(reviews) == 1
        assert reviews[0].parent_invitations == 'openreview.net/Template/-/Review:ABCD.cc/2025/Conference/-/Review'

        #post another review
        reviewer_client=openreview.api.OpenReviewClient(username='reviewer_two@abcd.cc', password=helpers.strong_password)

        anon_groups = reviewer_client.get_groups(prefix='ABCD.cc/2025/Conference/Submission1/Reviewer_', signatory='~ReviewerTwo_ABCD1')
        anon_group_id = anon_groups[0].id

        review_edit = reviewer_client.post_note_edit(
            invitation='ABCD.cc/2025/Conference/Submission1/-/Review',
            signatures=[anon_group_id],
            note=openreview.api.Note(
                content={
                    'review': { 'value': 'This is a poor paper' },
                    'review_rating': { 'value': 1 },
                    'review_confidence': { 'value': 1 },
                    'first_time_reviewer': { 'value': 'No' }
                }
            )
        )

        helpers.await_queue_edit(openreview_client, edit_id=review_edit['id'])

    def test_comment_stage(self, openreview_client, helpers):

        pc_client = openreview.api.OpenReviewClient(username='programchair@abcd.cc', password=helpers.strong_password)

        assert pc_client.get_invitation('ABCD.cc/2025/Conference/-/Comment')
        assert pc_client.get_invitation('ABCD.cc/2025/Conference/-/Comment/Dates')
        assert pc_client.get_invitation('ABCD.cc/2025/Conference/-/Comment/Form_Fields')
        assert pc_client.get_invitation('ABCD.cc/2025/Conference/-/Comment/Writers_and_Readers')
        assert pc_client.get_invitation('ABCD.cc/2025/Conference/-/Comment/Notifications')

        # edit comment stage fields
        pc_client.post_invitation_edit(
            invitations='ABCD.cc/2025/Conference/-/Comment/Form_Fields',
            content = {
                'content': {
                    'value': {
                        'confidential_comment_to_PC': {
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
                            'readers': ['ABCD.cc/2025/Conference/Program_Chairs', '${5/signatures}']
                        }
                    }
                }
            }
        )
        helpers.await_queue_edit(openreview_client, edit_id='ABCD.cc/2025/Conference/-/Comment-0-1', count=2)

        # create child invitations
        now = datetime.datetime.now()
        new_cdate = openreview.tools.datetime_millis(now)
        new_duedate = openreview.tools.datetime_millis(now + datetime.timedelta(days=3))

        pc_client.post_invitation_edit(
            invitations='ABCD.cc/2025/Conference/-/Comment/Dates',
            content={
                'activation_date': { 'value': new_cdate },
                'expiration_date': { 'value': new_duedate }
            }
        )
        helpers.await_queue_edit(openreview_client, edit_id='ABCD.cc/2025/Conference/-/Comment-0-1', count=3)

        invitations = openreview_client.get_invitations(invitation='ABCD.cc/2025/Conference/-/Comment')
        assert len(invitations) == 10
        inv = openreview_client.get_invitation('ABCD.cc/2025/Conference/Submission1/-/Comment')

        assert inv
        assert 'confidential_comment_to_PC' in inv.edit['note']['content'] and 'readers' in inv.edit['note']['content']['confidential_comment_to_PC']

        ## edit Confidential_Comment participants and readers, remove authors as participants
        pc_client.post_invitation_edit(
            invitations='ABCD.cc/2025/Conference/-/Comment/Writers_and_Readers',
            content = {
                'writers': {
                    'value':  [
                        'ABCD.cc/2025/Conference/Program_Chairs',
                        'ABCD.cc/2025/Conference/Submission${3/content/noteNumber/value}/Reviewers'
                    ]
                },
                'readers': {
                    'value':  [
                        {'value': 'ABCD.cc/2025/Conference/Program_Chairs', 'optional': False},
                        {'value': 'ABCD.cc/2025/Conference/Submission${8/content/noteNumber/value}/Reviewers', 'optional': True},
                        {'value': 'ABCD.cc/2025/Conference/Submission${8/content/noteNumber/value}/Authors', 'optional': True},
                    ]
                }
            }
        )
        helpers.await_queue_edit(openreview_client, edit_id='ABCD.cc/2025/Conference/-/Comment-0-1', count=4)

        invitation = openreview_client.get_invitation('ABCD.cc/2025/Conference/Submission1/-/Comment')

        assert invitation.invitees == ['ABCD.cc/2025/Conference/Program_Chairs', 'ABCD.cc/2025/Conference/Submission1/Reviewers']
        assert invitation.edit['note']['readers']['param']['items'] == [
          {
            'value': 'ABCD.cc/2025/Conference/Program_Chairs',
            'optional': False
          },
          {
            'value': 'ABCD.cc/2025/Conference/Submission1/Reviewers',
            'optional': True
          },
          {
            'value': 'ABCD.cc/2025/Conference/Submission1/Authors',
            'optional': True
          }
        ]

    def test_review_release_stage(self, openreview_client, helpers):

        pc_client = openreview.api.OpenReviewClient(username='programchair@abcd.cc', password=helpers.strong_password)
        assert pc_client.get_invitation('ABCD.cc/2025/Conference/-/Review_Release')
        assert pc_client.get_invitation('ABCD.cc/2025/Conference/-/Review_Release/Dates')
        assert pc_client.get_invitation('ABCD.cc/2025/Conference/-/Review_Release/Readers')

        # assert reviews are visible only to PCs and reviewers submittes
        reviews = openreview_client.get_notes(invitation='ABCD.cc/2025/Conference/Submission1/-/Review', sort='number:asc')
        assert len(reviews) == 2
        assert reviews[0].readers == [
            'ABCD.cc/2025/Conference/Program_Chairs',
            'ABCD.cc/2025/Conference/Submission1/Reviewers/Submitted'
        ]

        review_release_inv = openreview.tools.get_invitation(openreview_client, 'ABCD.cc/2025/Conference/-/Review_Release')
        assert review_release_inv.edit['invitation']['edit']['invitation']['edit']['note']['readers'] == [
            'ABCD.cc/2025/Conference/Program_Chairs',
            'ABCD.cc/2025/Conference/Submission${5/content/noteNumber/value}/Reviewers',
            'ABCD.cc/2025/Conference/Submission${5/content/noteNumber/value}/Authors'
        ]

        # edit review readers
        pc_client.post_invitation_edit(
            invitations='ABCD.cc/2025/Conference/-/Review_Release/Readers',
            content = {
                'readers': {
                    'value':  [
                        'ABCD.cc/2025/Conference/Program_Chairs',
                        'ABCD.cc/2025/Conference/Submission${5/content/noteNumber/value}/Reviewers/Submitted',
                        'ABCD.cc/2025/Conference/Submission${5/content/noteNumber/value}/Authors'
                    ]
                }
            }
        )

        helpers.await_queue_edit(openreview_client, edit_id='ABCD.cc/2025/Conference/-/Review_Release-0-1', count=2)

        review_release_inv = openreview.tools.get_invitation(openreview_client, 'ABCD.cc/2025/Conference/-/Review_Release')
        assert review_release_inv.edit['invitation']['edit']['invitation']['edit']['note']['readers'] == [
            'ABCD.cc/2025/Conference/Program_Chairs',
            'ABCD.cc/2025/Conference/Submission${5/content/noteNumber/value}/Reviewers/Submitted',
            'ABCD.cc/2025/Conference/Submission${5/content/noteNumber/value}/Authors'
        ]

        # release reviews
        now = datetime.datetime.now()
        pc_client.post_invitation_edit(
            invitations='ABCD.cc/2025/Conference/-/Review_Release/Dates',
            content={
                'activation_date': { 'value': openreview.tools.datetime_millis(now) }
            }
        )
        helpers.await_queue_edit(openreview_client, edit_id='ABCD.cc/2025/Conference/-/Review_Release-0-1', count=3)
        helpers.await_queue_edit(openreview_client, edit_id='ABCD.cc/2025/Conference/-/Review-0-1', count=3)

        review_inv = openreview.tools.get_invitation(openreview_client, 'ABCD.cc/2025/Conference/-/Review')
        assert review_inv.edit['invitation']['edit']['note']['readers'] == [
            'ABCD.cc/2025/Conference/Program_Chairs',
            'ABCD.cc/2025/Conference/Submission${5/content/noteNumber/value}/Reviewers/Submitted',
            'ABCD.cc/2025/Conference/Submission${5/content/noteNumber/value}/Authors'
        ]

        # assert reviews are visible to PCs, assigned reviewers submitted and paper authors
        reviews = openreview_client.get_notes(invitation='ABCD.cc/2025/Conference/Submission1/-/Review', sort='number:asc')
        assert len(reviews) == 2
        assert reviews[0].readers == [
            'ABCD.cc/2025/Conference/Program_Chairs',
            'ABCD.cc/2025/Conference/Submission1/Reviewers/Submitted',
            'ABCD.cc/2025/Conference/Submission1/Authors'
        ]
        reviewer_client=openreview.api.OpenReviewClient(username='reviewer_one@abcd.cc', password=helpers.strong_password)

        anon_groups = reviewer_client.get_groups(prefix='ABCD.cc/2025/Conference/Submission1/Reviewer_', signatory='~ReviewerOne_ABCD1')
        anon_group_id = anon_groups[0].id

        assert reviews[0].content['first_time_reviewer']['readers'] == [
            'ABCD.cc/2025/Conference/Program_Chairs',
            anon_group_id
        ]

    def test_email_reviews(self, openreview_client, helpers):

        pc_client = openreview.api.OpenReviewClient(username='programchair@abcd.cc', password=helpers.strong_password)
        submissions = openreview_client.get_notes(invitation='ABCD.cc/2025/Conference/-/Submission', sort='number:asc')

        assert pc_client.get_invitation('ABCD.cc/2025/Conference/-/Email_Reviews_to_Authors')
        assert pc_client.get_invitation('ABCD.cc/2025/Conference/-/Email_Reviews_to_Authors/Dates')
        assert pc_client.get_invitation('ABCD.cc/2025/Conference/-/Email_Reviews_to_Authors/Fields_to_Include')
        assert pc_client.get_invitation('ABCD.cc/2025/Conference/-/Email_Reviews_to_Authors/Message')

        pc_client.post_invitation_edit(
            invitations='ABCD.cc/2025/Conference/-/Email_Reviews_to_Authors/Fields_to_Include',
            content={
                'fields': { 'value': ['review', 'review_rating', 'review_confidence'] }
            }
        )
        helpers.await_queue_edit(openreview_client, edit_id='ABCD.cc/2025/Conference/-/Email_Reviews_to_Authors-0-1', count=2)

        now = datetime.datetime.now()
        new_cdate = openreview.tools.datetime_millis(now)

        pc_client.post_invitation_edit(
            invitations='ABCD.cc/2025/Conference/-/Email_Reviews_to_Authors/Dates',
            content={
                'activation_date': { 'value': new_cdate }
            }
        )
        helpers.await_queue_edit(openreview_client, edit_id='ABCD.cc/2025/Conference/-/Email_Reviews_to_Authors-0-1', count=3)

        messages = openreview_client.get_messages(to='test@mail.com', subject='[ABCD 2025] The reviews for your submission #1, titled \"Paper title 1\" are now available')
        assert messages and len(messages) == 1
        assert messages[0]['content']['text'] == f'''Hi SomeFirstName User,

This is to inform you that the reviews for your submission #1, "Paper title 1", to ABCD 2025 are now available.

**review**: This is a good paper
**review_rating**: 5
**review_confidence**: 3

**review**: This is a poor paper
**review_rating**: 1
**review_confidence**: 1


To view this paper, please go to https://openreview.net/forum?id={submissions[0].id}

Please note that responding to this email will direct your reply to abcd2025.programchairs@gmail.com.
'''

    def test_rebuttal_stage(self, openreview_client, test_client, helpers):

        pc_client = openreview.api.OpenReviewClient(username='programchair@abcd.cc', password=helpers.strong_password)
        assert pc_client.get_invitation('ABCD.cc/2025/Conference/-/Author_Rebuttal')
        assert pc_client.get_invitation('ABCD.cc/2025/Conference/-/Author_Rebuttal/Dates')
        assert pc_client.get_invitation('ABCD.cc/2025/Conference/-/Author_Rebuttal/Form_Fields')
        assert pc_client.get_invitation('ABCD.cc/2025/Conference/-/Author_Rebuttal/Readers')
        assert pc_client.get_invitation('ABCD.cc/2025/Conference/-/Author_Rebuttal/Notifications')

        # edit rebuttal stage fields
        pc_client.post_invitation_edit(
            invitations='ABCD.cc/2025/Conference/-/Author_Rebuttal/Form_Fields',
            content = {
                'content': {
                    'value': {
                        'rebuttal': {
                            'order': 1,
                            'description': 'Rebuttals can include Markdown formatting and LaTeX forumulas, for more information see https://openreview.net/faq, max length: 6000',
                            'value': {
                            'param': {
                                'type': 'string',
                                'maxLength': 6000,
                                'markdown': True,
                                'input': 'textarea'
                            }
                            }
                        },
                        'pdf': {
                            'order': 2,
                            'description': 'Optional: Upload a PDF file that ends with .pdf (should be one page and contain only Figures and Tables)',
                            'value': {
                            'param': {
                                'type': 'file',
                                'maxSize': 50,
                                'extensions': [
                                'pdf'
                                ],
                                'optional': True
                            }
                            }
                        }
                    }
                }
            }
        )

        rebuttal_inv = openreview.tools.get_invitation(openreview_client, 'ABCD.cc/2025/Conference/-/Author_Rebuttal')
        assert 'rebuttal' in rebuttal_inv.edit['invitation']['edit']['note']['content']
        assert 'pdf' in rebuttal_inv.edit['invitation']['edit']['note']['content']

        ## edit readers to include only authors
        pc_client.post_invitation_edit(
            invitations='ABCD.cc/2025/Conference/-/Author_Rebuttal/Readers',
            content = {
                'readers': {
                    'value':  [
                        'ABCD.cc/2025/Conference/Program_Chairs',
                        'ABCD.cc/2025/Conference/Submission${5/content/noteNumber/value}/Authors'
                    ]
                }
            }
        )

        review_inv = openreview.tools.get_invitation(openreview_client, 'ABCD.cc/2025/Conference/-/Author_Rebuttal')
        assert review_inv.edit['invitation']['edit']['note']['readers'] == [
            'ABCD.cc/2025/Conference/Program_Chairs',
            'ABCD.cc/2025/Conference/Submission${5/content/noteNumber/value}/Authors'
        ]

        # create child invitations
        now = datetime.datetime.now()
        new_cdate = openreview.tools.datetime_millis(now)
        new_duedate = openreview.tools.datetime_millis(now + datetime.timedelta(days=3))

        pc_client.post_invitation_edit(
            invitations='ABCD.cc/2025/Conference/-/Author_Rebuttal/Dates',
            content={
                'activation_date': { 'value': new_cdate },
                'due_date': { 'value': new_duedate },
                'expiration_date': { 'value': new_duedate }
            }
        )
        helpers.await_queue_edit(openreview_client, edit_id='ABCD.cc/2025/Conference/-/Author_Rebuttal-0-1', count=2)

        invitations = openreview_client.get_invitations(invitation='ABCD.cc/2025/Conference/-/Author_Rebuttal')
        assert len(invitations) == 10

        invitation  = openreview_client.get_invitation('ABCD.cc/2025/Conference/Submission1/-/Author_Rebuttal')
        assert invitation and invitation.edit['readers'] == [
            'ABCD.cc/2025/Conference/Program_Chairs',
            'ABCD.cc/2025/Conference/Submission1/Authors'
        ]

        author_client = openreview.api.OpenReviewClient(token=test_client.token)

        rebuttal_edit = author_client.post_note_edit(
            invitation='ABCD.cc/2025/Conference/Submission1/-/Author_Rebuttal',
            signatures=['ABCD.cc/2025/Conference/Submission1/Authors'],
            note=openreview.api.Note(
                content={
                    'rebuttal': { 'value': 'This is an author rebuttal' }
                }
            )
        )

        helpers.await_queue_edit(openreview_client, edit_id=rebuttal_edit['id'])

    def test_decision_stage(self, openreview_client, helpers):

        pc_client = openreview.api.OpenReviewClient(username='programchair@abcd.cc', password=helpers.strong_password)

        invitation =  pc_client.get_invitation('ABCD.cc/2025/Conference/-/Decision')
        assert invitation
        assert pc_client.get_invitation('ABCD.cc/2025/Conference/-/Decision/Dates')
        assert pc_client.get_invitation('ABCD.cc/2025/Conference/-/Decision/Readers')
        assert pc_client.get_invitation('ABCD.cc/2025/Conference/-/Decision/Decision_Options')
        assert pc_client.get_invitation('ABCD.cc/2025/Conference/-/Decision_Upload')
        assert pc_client.get_invitation('ABCD.cc/2025/Conference/-/Decision_Upload/Decision_CSV')
        assert pc_client.get_invitation('ABCD.cc/2025/Conference/-/Article_Endorsement')
        assert pc_client.get_invitation('ABCD.cc/2025/Conference/Reviewers/-/Review_Count')
        assert pc_client.get_invitation('ABCD.cc/2025/Conference/Reviewers/-/Review_Assignment_Count')
        assert pc_client.get_invitation('ABCD.cc/2025/Conference/Reviewers/-/Review_Days_Late')

        assert 'accept_decision_options' in invitation.content and invitation.content['accept_decision_options']['value'] == ['Accept (Oral)', 'Accept (Poster)']

        now = datetime.datetime.now()
        new_cdate = openreview.tools.datetime_millis(now)
        new_duedate = openreview.tools.datetime_millis(now + datetime.timedelta(days=3))

        pc_client.post_invitation_edit(
            invitations='ABCD.cc/2025/Conference/-/Decision/Dates',
            content={
                'activation_date': { 'value': new_cdate },
                'due_date': { 'value': new_duedate },
                'expiration_date': { 'value': new_duedate }
            }
        )
        helpers.await_queue_edit(openreview_client, edit_id='ABCD.cc/2025/Conference/-/Decision-0-1', count=2)

        # edit decision options
        edit = pc_client.post_invitation_edit(
            invitations='ABCD.cc/2025/Conference/-/Decision/Decision_Options',
            content={
                'decision_options': { 'value': ['Accept', 'Revision Needed', 'Reject'] },
                'accept_decision_options': { 'value': ['Accept'] }
            }
        )
        helpers.await_queue_edit(openreview_client, edit_id=edit['id'])
        helpers.await_queue_edit(openreview_client, edit_id='ABCD.cc/2025/Conference/-/Decision-0-1', count=3)

        invitation = openreview_client.get_invitation('ABCD.cc/2025/Conference/-/Decision')
        assert 'accept_decision_options' in invitation.content and invitation.content['accept_decision_options']['value'] == ['Accept']

        venue_group = openreview_client.get_group('ABCD.cc/2025/Conference')
        assert 'accept_decision_options' in venue_group.content and venue_group.content['accept_decision_options']['value'] == ['Accept']

        submissions = openreview_client.get_notes(invitation='ABCD.cc/2025/Conference/-/Submission', sort='number:asc')

        decisions = ['Accept', 'Revision Needed', 'Reject']
        comment = {
            'Accept': 'Congratulations on your acceptance.',
            'Revision Needed': 'Your paper must be revised.',
            'Reject': 'We regret to inform you...'
        }

        with open(os.path.join(os.path.dirname(__file__), 'data/ABCD_decisions.csv'), 'w') as file_handle:
            writer = csv.writer(file_handle)
            writer.writerow([submissions[0].number, 'Accept', comment['Accept']])
            writer.writerow([submissions[1].number, 'Revision Needed', comment['Revision Needed']])
            writer.writerow([submissions[2].number, 'Reject', comment['Reject']])
            for submission in submissions[3:]:
                decision = random.choice(decisions)
                writer.writerow([submission.number, decision, comment[decision]])

        url = pc_client.put_attachment(os.path.join(os.path.dirname(__file__), 'data/ABCD_decisions.csv'),
                                         'ABCD.cc/2025/Conference/-/Decision_Upload/Decision_CSV', 'decision_CSV')

        now = datetime.datetime.now()

        pc_client.post_invitation_edit(
            invitations='ABCD.cc/2025/Conference/-/Decision_Upload/Decision_CSV',

            content={
                'upload_date': { 'value': openreview.tools.datetime_millis(now) },
                'decision_CSV': { 'value': url }
            }
        )
        helpers.await_queue_edit(openreview_client, edit_id='ABCD.cc/2025/Conference/-/Decision_Upload-0-1', count=2)

        helpers.await_queue_edit(openreview_client, invitation='ABCD.cc/2025/Conference/Submission1/-/Decision')

        decision_note = openreview_client.get_notes(invitation='ABCD.cc/2025/Conference/Submission1/-/Decision')[0]
        assert decision_note and decision_note.content['decision']['value'] == 'Accept'
        assert decision_note.readers == ['ABCD.cc/2025/Conference/Program_Chairs']

        endorsement_tags = openreview_client.get_tags(invitation='ABCD.cc/2025/Conference/-/Article_Endorsement')
        assert len(endorsement_tags) == 0

    def test_decision_release_stage(self, openreview_client, helpers):

        pc_client = openreview.api.OpenReviewClient(username='programchair@abcd.cc', password=helpers.strong_password)
        assert pc_client.get_invitation('ABCD.cc/2025/Conference/-/Decision_Release')
        assert pc_client.get_invitation('ABCD.cc/2025/Conference/-/Decision_Release/Dates')
        assert pc_client.get_invitation('ABCD.cc/2025/Conference/-/Decision_Release/Readers')

        # assert reviews are visible only to PCs and reviewers submittes
        decision = openreview_client.get_notes(invitation='ABCD.cc/2025/Conference/Submission1/-/Decision', sort='number:asc')
        assert len(decision) == 1
        assert decision[0].readers == [
            'ABCD.cc/2025/Conference/Program_Chairs'
        ]

        decision_release_inv = openreview.tools.get_invitation(openreview_client, 'ABCD.cc/2025/Conference/-/Decision_Release')
        assert decision_release_inv.edit['invitation']['edit']['invitation']['edit']['note']['readers'] == [
            'ABCD.cc/2025/Conference/Program_Chairs',
            'ABCD.cc/2025/Conference/Submission${5/content/noteNumber/value}/Reviewers',
            'ABCD.cc/2025/Conference/Submission${5/content/noteNumber/value}/Authors'
        ]

        # edit decision readers
        pc_client.post_invitation_edit(
            invitations='ABCD.cc/2025/Conference/-/Decision_Release/Readers',
            content = {
                'readers': {
                    'value':  [
                        'ABCD.cc/2025/Conference/Program_Chairs',
                        'ABCD.cc/2025/Conference/Submission${5/content/noteNumber/value}/Authors'
                    ]
                }
            }
        )

        helpers.await_queue_edit(openreview_client, edit_id='ABCD.cc/2025/Conference/-/Decision_Release-0-1', count=2)

        decision_release_inv = openreview.tools.get_invitation(openreview_client, 'ABCD.cc/2025/Conference/-/Decision_Release')
        assert decision_release_inv.edit['invitation']['edit']['invitation']['edit']['note']['readers'] == [
            'ABCD.cc/2025/Conference/Program_Chairs',
            'ABCD.cc/2025/Conference/Submission${5/content/noteNumber/value}/Authors'
        ]

        # release decisions
        now = datetime.datetime.now()
        pc_client.post_invitation_edit(
            invitations='ABCD.cc/2025/Conference/-/Decision_Release/Dates',
            content={
                'activation_date': { 'value': openreview.tools.datetime_millis(now) }
            }
        )
        helpers.await_queue_edit(openreview_client, edit_id='ABCD.cc/2025/Conference/-/Decision_Release-0-1', count=3)
        helpers.await_queue_edit(openreview_client, edit_id='ABCD.cc/2025/Conference/-/Decision-0-1', count=4)

        decision_inv = openreview.tools.get_invitation(openreview_client, 'ABCD.cc/2025/Conference/-/Decision')
        assert decision_inv.edit['invitation']['edit']['note']['readers'] == [
            'ABCD.cc/2025/Conference/Program_Chairs',
            'ABCD.cc/2025/Conference/Submission${5/content/noteNumber/value}/Authors'
        ]

        # assert decisions are visible to PCs and paper authors
        decisions = openreview_client.get_notes(invitation='ABCD.cc/2025/Conference/Submission1/-/Decision', sort='number:asc')
        assert len(decisions) == 1
        assert decisions[0].readers == [
            'ABCD.cc/2025/Conference/Program_Chairs',
            'ABCD.cc/2025/Conference/Submission1/Authors'
        ]

    def test_email_decisions(self, openreview_client, helpers):

        pc_client = openreview.api.OpenReviewClient(username='programchair@abcd.cc', password=helpers.strong_password)
        submissions = openreview_client.get_notes(invitation='ABCD.cc/2025/Conference/-/Submission', sort='number:asc')

        assert pc_client.get_invitation('ABCD.cc/2025/Conference/-/Email_Decisions_to_Authors')
        assert pc_client.get_invitation('ABCD.cc/2025/Conference/-/Email_Decisions_to_Authors/Dates')
        assert pc_client.get_invitation('ABCD.cc/2025/Conference/-/Email_Decisions_to_Authors/Message')

        now = datetime.datetime.now()
        new_cdate = openreview.tools.datetime_millis(now)

        pc_client.post_invitation_edit(
            invitations='ABCD.cc/2025/Conference/-/Email_Decisions_to_Authors/Dates',
            content={
                'activation_date': { 'value': new_cdate }
            }
        )
        helpers.await_queue_edit(openreview_client, edit_id='ABCD.cc/2025/Conference/-/Email_Decisions_to_Authors-0-1', count=2)

        messages = openreview_client.get_messages(to='test@mail.com', subject='[ABCD 2025] The decision for your submission #1, titled \"Paper title 1\" is now available')
        assert messages and len(messages) == 1
        assert messages[0]['content']['text'] == f'''Hi SomeFirstName User,

This is to inform you that the decision for your submission #1, "Paper title 1", to ABCD 2025 is now available.

Decision: Accept 

Comment: Congratulations on your acceptance.

To view this paper, please go to https://openreview.net/forum?id={submissions[0].id}

Please note that responding to this email will direct your reply to abcd2025.programchairs@gmail.com.
'''

    def test_camera_ready_revisions(self, openreview_client, helpers):

        pc_client = openreview.api.OpenReviewClient(username='programchair@abcd.cc', password=helpers.strong_password)
        submissions = openreview_client.get_notes(invitation='ABCD.cc/2025/Conference/-/Submission', sort='number:asc', details='directReplies')

        assert pc_client.get_invitation('ABCD.cc/2025/Conference/-/Camera_Ready_Revision')
        assert pc_client.get_invitation('ABCD.cc/2025/Conference/-/Camera_Ready_Revision/Dates')
        assert pc_client.get_invitation('ABCD.cc/2025/Conference/-/Camera_Ready_Revision/Form_Fields')

        now = datetime.datetime.now()
        new_cdate = openreview.tools.datetime_millis(now)

        pc_client.post_invitation_edit(
            invitations='ABCD.cc/2025/Conference/-/Camera_Ready_Revision/Dates',
            content={
                'activation_date': { 'value': new_cdate },
                'due_date': { 'value': openreview.tools.datetime_millis(now + datetime.timedelta(days=3))},
                'expiration_date': { 'value': openreview.tools.datetime_millis(now + datetime.timedelta(days=3)) }
            }
        )
        helpers.await_queue_edit(openreview_client, edit_id='ABCD.cc/2025/Conference/-/Camera_Ready_Revision-0-1', count=3)

        decisions = [openreview.Note.from_json(reply) for note in submissions for reply in note.details['directReplies'] if '/-/Decision' in reply['invitations'][0]]
        accept_decisions = [note for note in decisions if 'Accept' in note.content['decision']['value']]

        invitations = openreview_client.get_invitations(invitation='ABCD.cc/2025/Conference/-/Camera_Ready_Revision')
        assert len(invitations) == len(accept_decisions)

    def test_release_submissions(self, openreview_client, helpers):

        pc_client = openreview.api.OpenReviewClient(username='programchair@abcd.cc', password=helpers.strong_password)
        submissions = openreview_client.get_notes(invitation='ABCD.cc/2025/Conference/-/Submission', sort='number:asc')
        assert submissions[0].readers == [
            'ABCD.cc/2025/Conference',
            'ABCD.cc/2025/Conference/Submission1/Reviewers',
            'ABCD.cc/2025/Conference/Submission1/Authors'
        ]
        assert not submissions[0].pdate
        assert submissions[0].content['authors']['readers'] == [
            'ABCD.cc/2025/Conference',
            'ABCD.cc/2025/Conference/Submission1/Authors'
        ]
        assert submissions[0].content['venueid']['value'] == 'ABCD.cc/2025/Conference/Submission'
        assert submissions[0].content['venue']['value'] == 'ABCD 2025 Conference Submission'

        inv = pc_client.get_invitation('ABCD.cc/2025/Conference/-/Submission_Release')
        assert inv and inv.content['source']['value'] == 'accepted_submissions'
        assert pc_client.get_invitation('ABCD.cc/2025/Conference/-/Submission_Release/Dates')
        assert pc_client.get_invitation('ABCD.cc/2025/Conference/-/Submission_Release/Which_Submissions')
        now = datetime.datetime.now()
        new_cdate = openreview.tools.datetime_millis(now)

        pc_client.post_invitation_edit(
            invitations='ABCD.cc/2025/Conference/-/Submission_Release/Dates',
            content={
                'activation_date': { 'value': new_cdate }
            }
        )
        helpers.await_queue_edit(openreview_client, edit_id='ABCD.cc/2025/Conference/-/Submission_Release-0-1', count=2)

        submissions = openreview_client.get_notes(invitation='ABCD.cc/2025/Conference/-/Submission', sort='number:asc')

        assert submissions[0].readers == ['everyone']
        assert submissions[0].pdate
        assert 'readers' not in submissions[0].content['authors']
        assert submissions[0].content['venueid']['value'] == 'ABCD.cc/2025/Conference'
        assert submissions[0].content['venue']['value'] == 'ABCD 2025'

        assert submissions[1].readers == [
            'ABCD.cc/2025/Conference',
            'ABCD.cc/2025/Conference/Submission2/Reviewers',
            'ABCD.cc/2025/Conference/Submission2/Authors'
        ]
        assert not submissions[1].pdate
        assert submissions[1].content['authors']['readers'] == [
            'ABCD.cc/2025/Conference',
            'ABCD.cc/2025/Conference/Submission2/Authors'
        ]
        assert submissions[1].content['venueid']['value'] == 'ABCD.cc/2025/Conference/Submission'
        assert submissions[1].content['venue']['value'] == 'ABCD 2025 Conference Submission'

        endorsement_tags = openreview_client.get_tags(invitation='ABCD.cc/2025/Conference/-/Article_Endorsement')
        assert endorsement_tags
        assert endorsement_tags[0].label is None
        assert len(openreview_client.get_tags(invitation='ABCD.cc/2025/Conference/-/Article_Endorsement', forum=submissions[0].id))== 1

        endorsement_tags = openreview_client.get_tags(parent_invitations='openreview.net/-/Article_Endorsement', stream=True)
        assert endorsement_tags


    def test_reviewer_stats_computation(self, openreview_client, helpers):

        pc_client = openreview.api.OpenReviewClient(username='programchair@abcd.cc', password=helpers.strong_password)
        submissions = openreview_client.get_notes(invitation='ABCD.cc/2025/Conference/-/Submission', sort='number:asc', details='directReplies')

        assert pc_client.get_invitation('ABCD.cc/2025/Conference/Reviewers/-/Review_Count')
        assert pc_client.get_invitation('ABCD.cc/2025/Conference/Reviewers/-/Review_Count/Dates')
        assert pc_client.get_invitation('ABCD.cc/2025/Conference/Reviewers/-/Review_Assignment_Count')
        assert pc_client.get_invitation('ABCD.cc/2025/Conference/Reviewers/-/Review_Assignment_Count/Dates')
        assert pc_client.get_invitation('ABCD.cc/2025/Conference/Reviewers/-/Review_Days_Late')
        assert pc_client.get_invitation('ABCD.cc/2025/Conference/Reviewers/-/Review_Days_Late/Dates')

        now = datetime.datetime.now()
        new_cdate = openreview.tools.datetime_millis(now)

        pc_client.post_invitation_edit(
            invitations='ABCD.cc/2025/Conference/Reviewers/-/Review_Count/Dates',
            content={
                'activation_date': { 'value': new_cdate },
            }
        )
        helpers.await_queue_edit(openreview_client, edit_id='ABCD.cc/2025/Conference/Reviewers/-/Review_Count-0-1', count=2)

        tags = openreview_client.get_tags(invitation='ABCD.cc/2025/Conference/Reviewers/-/Review_Count')
        assert len(tags) == 2

        assert openreview_client.get_tags(profile='~ReviewerOne_ABCD1')[0].weight == 1
        assert openreview_client.get_tags(profile='~ReviewerTwo_ABCD1')[0].weight == 1
        assert len(openreview_client.get_tags(profile='~ReviewerThree_ABCD1')) == 0

        tags = openreview_client.get_tags(parent_invitations='openreview.net/-/Reviewers_Review_Count')
        assert len(tags) == 2

