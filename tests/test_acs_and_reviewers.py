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

        helpers.create_user('programchair@efgh.cc', 'ProgramChair', 'EFGH')
        helpers.create_user('reviewer_one@efgh.cc', 'ReviewerOne', 'EFGH')
        helpers.create_user('reviewer_two@efgh.cc', 'ReviewerTwo', 'EFGH')
        helpers.create_user('reviewer_three@efgh.cc', 'ReviewerThree', 'EFGH')
        helpers.create_user('areachair_one@efgh.cc', 'ACOne', 'EFGH')
        helpers.create_user('areachair_two@efgh.cc', 'ACTwo', 'EFGH')
        helpers.create_user('areachair_three@efgh.cc', 'ACThree', 'EFGH')
        pc_client=openreview.api.OpenReviewClient(username='programchair@efgh.cc', password=helpers.strong_password)

        assert openreview_client.get_invitation('openreview.net/-/Edit')
        assert openreview_client.get_group('openreview.net/Support/Venue_Request')
        assert openreview_client.get_invitation('openreview.net/Support/Venue_Request/-/Conference_Review_Workflow')
        assert openreview_client.get_invitation('openreview.net/Support/Venue_Request/Conference_Review_Workflow/-/Deployment')
        assert openreview_client.get_invitation('openreview.net/Support/Venue_Request/Conference_Review_Workflow/-/Comment')

        now = datetime.datetime.now()
        due_date = now + datetime.timedelta(days=2)

        request = pc_client.post_note_edit(invitation='openreview.net/Support/Venue_Request/-/Conference_Review_Workflow',
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
                    'reviewers_name': { 'value': 'Reviewers' },
                    'area_chairs_name': { 'value': 'Action_Editors' },
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
        assert openreview.tools.get_group(openreview_client, 'EFGH.cc/2025/Conference/Program_Chairs') is None

        # deploy the venue
        edit = openreview_client.post_note_edit(invitation=f'openreview.net/Support/Venue_Request/Conference_Review_Workflow/-/Deployment',
            signatures=[support_group_id],
            note=openreview.api.Note(
                id=request.id,
                content={
                    'venue_id': { 'value': 'EFGH.cc/2025/Conference' }
                }
            ))
        
        helpers.await_queue_edit(openreview_client, edit_id=edit['id'])

        helpers.await_queue_edit(openreview_client, 'EFGH.cc/2025/Conference/-/Withdrawal-0-1', count=1)
        helpers.await_queue_edit(openreview_client, 'EFGH.cc/2025/Conference/-/Desk_Rejection-0-1', count=1)
        helpers.await_queue_edit(openreview_client, 'EFGH.cc/2025/Conference/Reviewers/-/Submission_Group-0-1', count=1)
        helpers.await_queue_edit(openreview_client, 'EFGH.cc/2025/Conference/Action_Editors/-/Submission_Group-0-1', count=1)
        helpers.await_queue_edit(openreview_client, 'EFGH.cc/2025/Conference/-/Submission_Change_Before_Bidding-0-1', count=1)

        #after deployment, check domain hasn't changed
        request_note = openreview_client.get_note(request.id)
        assert request_note.domain == 'openreview.net/Support'

        openreview_client.flush_members_cache('~ProgramChair_EFGH1')
        group = openreview.tools.get_group(openreview_client, 'EFGH.cc/2025/Conference')
        assert group.members == ['openreview.net/Template', 'EFGH.cc/2025/Conference/Program_Chairs', 'EFGH.cc/2025/Conference/Automated_Administrator']
        assert 'request_form_id' in group.content and group.content['request_form_id']['value'] == request.id

        assert 'preferred_emails_groups' in group.content and group.content['preferred_emails_groups']['value'] == [
            'EFGH.cc/2025/Conference/Reviewers',
            'EFGH.cc/2025/Conference/Authors',
            'EFGH.cc/2025/Conference/Action_Editors'
        ]
        assert 'preferred_emails_id' in group.content and group.content['preferred_emails_id']['value'] == 'EFGH.cc/2025/Conference/-/Preferred_Emails'
        invitation = openreview_client.get_invitation('EFGH.cc/2025/Conference/-/Preferred_Emails')
        assert invitation

        group = openreview.tools.get_group(openreview_client, 'EFGH.cc/2025')
        group = openreview.tools.get_group(openreview_client, 'EFGH.cc')

        group = openreview.tools.get_group(openreview_client, 'EFGH.cc/2025/Conference/Program_Chairs')
        assert group.members == ['programchair@efgh.cc']
        assert group.domain == 'EFGH.cc/2025/Conference'

        group = openreview.tools.get_group(openreview_client, 'EFGH.cc/2025/Conference/Automated_Administrator')
        assert not group.members
        assert group.domain == 'EFGH.cc/2025/Conference'

        group = openreview.tools.get_group(openreview_client, 'EFGH.cc/2025/Conference/Reviewers')
        assert group.domain == 'EFGH.cc/2025/Conference'
        assert group.readers == [
            'EFGH.cc/2025/Conference',
            'EFGH.cc/2025/Conference/Reviewers',
            'EFGH.cc/2025/Conference/Action_Editors'
        ]

        group = openreview.tools.get_group(openreview_client, 'EFGH.cc/2025/Conference/Reviewers/Invited')
        assert group.domain == 'EFGH.cc/2025/Conference'
        assert group.readers == [
            'EFGH.cc/2025/Conference',
            'EFGH.cc/2025/Conference/Reviewers/Invited'
        ]

        group = openreview.tools.get_group(openreview_client, 'EFGH.cc/2025/Conference/Reviewers/Declined')
        assert group.domain == 'EFGH.cc/2025/Conference'
        assert group.readers == [
            'EFGH.cc/2025/Conference',
            'EFGH.cc/2025/Conference/Reviewers/Declined'
        ]

        group = openreview.tools.get_group(openreview_client, 'EFGH.cc/2025/Conference/Authors')
        assert group.domain == 'EFGH.cc/2025/Conference'

        group = openreview.tools.get_group(openreview_client, 'EFGH.cc/2025/Conference/Authors/Accepted')
        assert group.domain == 'EFGH.cc/2025/Conference'

        group = openreview.tools.get_group(openreview_client, 'EFGH.cc/2025/Conference/Action_Editors')
        assert group.readers == [
            'EFGH.cc/2025/Conference',
            'EFGH.cc/2025/Conference/Action_Editors'
        ]
        assert group.domain == 'EFGH.cc/2025/Conference'

        group = openreview.tools.get_group(openreview_client, 'EFGH.cc/2025/Conference/Action_Editors/Invited')
        assert group.readers == [
            'EFGH.cc/2025/Conference',
            'EFGH.cc/2025/Conference/Action_Editors/Invited'
        ]
        assert group.domain == 'EFGH.cc/2025/Conference'

        group = openreview.tools.get_group(openreview_client, 'EFGH.cc/2025/Conference/Action_Editors/Declined')
        assert group.readers == [
            'EFGH.cc/2025/Conference',
            'EFGH.cc/2025/Conference/Action_Editors/Declined'
        ]
        assert group.domain == 'EFGH.cc/2025/Conference'

        assert openreview.tools.get_invitation(openreview_client, 'EFGH.cc/2025/Conference/Action_Editors/-/Message')
        assert openreview.tools.get_invitation(openreview_client, 'EFGH.cc/2025/Conference/Action_Editors/-/Members')

        domain_content = openreview.tools.get_group(openreview_client, 'EFGH.cc/2025/Conference').content
        assert domain_content['reviewers_invited_id']['value'] == 'EFGH.cc/2025/Conference/Reviewers/Invited'
        assert domain_content['reviewers_declined_id']['value'] == 'EFGH.cc/2025/Conference/Reviewers/Declined'
        assert domain_content['reviewers_id']['value'] == 'EFGH.cc/2025/Conference/Reviewers'
        assert domain_content['reviewers_name']['value'] == 'Reviewers'
        assert domain_content['reviewers_anon_name']['value'] == 'Reviewer_'
        assert domain_content['reviewers_submitted_name']['value'] == 'Submitted'
        assert domain_content['reviewers_recruitment_id']['value'] == 'EFGH.cc/2025/Conference/Reviewers/-/Recruitment_Response'
        assert domain_content['reviewers_invited_message_id']['value'] == 'EFGH.cc/2025/Conference/Reviewers/Invited/-/Message' 

        assert domain_content['area_chairs_invited_id']['value'] == 'EFGH.cc/2025/Conference/Action_Editors/Invited'
        assert domain_content['area_chairs_declined_id']['value'] == 'EFGH.cc/2025/Conference/Action_Editors/Declined'
        assert domain_content['area_chairs_id']['value'] == 'EFGH.cc/2025/Conference/Action_Editors'
        assert domain_content['area_chairs_name']['value'] == 'Action_Editors'
        assert domain_content['area_chairs_anon_name']['value'] == 'Action_Editor_'
        assert domain_content.get('area_chairs_submitted_name') is None
        assert domain_content['area_chairs_recruitment_id']['value'] == 'EFGH.cc/2025/Conference/Action_Editors/-/Recruitment_Response'
        assert domain_content['area_chairs_invited_message_id']['value'] == 'EFGH.cc/2025/Conference/Action_Editors/Invited/-/Message'

        assert openreview.tools.get_invitation(openreview_client, 'EFGH.cc/2025/Conference/-/Submission')
        invitation = openreview.tools.get_invitation(openreview_client, 'EFGH.cc/2025/Conference/-/Submission_Change_Before_Bidding')
        assert invitation.edit['note']['readers'] == [
            'EFGH.cc/2025/Conference',
            'EFGH.cc/2025/Conference/Action_Editors',
            'EFGH.cc/2025/Conference/Reviewers',
            'EFGH.cc/2025/Conference/Submission${{2/id}/number}/Authors'
        ]
        invitation = openreview.tools.get_invitation(openreview_client, 'EFGH.cc/2025/Conference/-/Submission_Change_Before_Reviewing')
        assert invitation.edit['note']['readers'] == [
            'EFGH.cc/2025/Conference',
            'EFGH.cc/2025/Conference/Submission${{2/id}/number}/Action_Editors',
            'EFGH.cc/2025/Conference/Submission${{2/id}/number}/Reviewers',
            'EFGH.cc/2025/Conference/Submission${{2/id}/number}/Authors'
        ]

        invitation = openreview_client.get_invitation('EFGH.cc/2025/Conference/Reviewers/-/Submission_Group')
        assert invitation and invitation.edit['group']['deanonymizers'] == ['EFGH.cc/2025/Conference']
        assert openreview_client.get_invitation('EFGH.cc/2025/Conference/Reviewers/-/Submission_Group/Dates')
        assert openreview_client.get_invitation('EFGH.cc/2025/Conference/Reviewers/-/Submission_Group/Deanonymizers')
        invitation =  openreview_client.get_invitation('EFGH.cc/2025/Conference/Reviewers/-/Recruitment_Request')

        invitation = openreview_client.get_invitation('EFGH.cc/2025/Conference/Action_Editors/-/Submission_Group')
        assert invitation and invitation.edit['group']['deanonymizers'] == ['EFGH.cc/2025/Conference']
        assert openreview_client.get_invitation('EFGH.cc/2025/Conference/Action_Editors/-/Submission_Group/Dates')
        assert openreview_client.get_invitation('EFGH.cc/2025/Conference/Action_Editors/-/Submission_Group/Deanonymizers')
        invitation =  openreview_client.get_invitation('EFGH.cc/2025/Conference/Action_Editors/-/Recruitment_Request')

         # check domain object
        domain_content = openreview_client.get_group('EFGH.cc/2025/Conference').content
        assert domain_content['reviewers_invited_id']['value'] == 'EFGH.cc/2025/Conference/Reviewers/Invited'
        assert domain_content['reviewers_declined_id']['value'] == 'EFGH.cc/2025/Conference/Reviewers/Declined'
        assert domain_content['reviewers_id']['value'] == 'EFGH.cc/2025/Conference/Reviewers'
        assert domain_content['reviewers_name']['value'] == 'Reviewers'
        assert domain_content['reviewers_anon_name']['value'] == 'Reviewer_'
        assert domain_content['reviewers_submitted_name']['value'] == 'Submitted'
        assert domain_content['reviewers_recruitment_id']['value'] == 'EFGH.cc/2025/Conference/Reviewers/-/Recruitment_Response'
        assert domain_content['reviewers_invited_message_id']['value'] == 'EFGH.cc/2025/Conference/Reviewers/Invited/-/Message'

        assert domain_content['area_chairs_invited_id']['value'] == 'EFGH.cc/2025/Conference/Action_Editors/Invited'
        assert domain_content['area_chairs_declined_id']['value'] == 'EFGH.cc/2025/Conference/Action_Editors/Declined'
        assert domain_content['area_chairs_id']['value'] == 'EFGH.cc/2025/Conference/Action_Editors'
        assert domain_content['area_chairs_name']['value'] == 'Action_Editors'
        assert domain_content['area_chairs_anon_name']['value'] == 'Action_Editor_'
        assert 'area_chairs_submitted_name' not in domain_content
        assert domain_content['area_chairs_recruitment_id']['value'] == 'EFGH.cc/2025/Conference/Action_Editors/-/Recruitment_Response'
        assert domain_content['area_chairs_invited_message_id']['value'] == 'EFGH.cc/2025/Conference/Action_Editors/Invited/-/Message'

    def test_recruit_area_chairs(self, openreview_client, selenium, request_page, helpers):

        # use invitation to recruit reviewers
        edit = openreview_client.post_group_edit(

                invitation='EFGH.cc/2025/Conference/Action_Editors/-/Recruitment_Request',
                content={
                    'invitee_details': { 'value':  'areachair_one@efgh.cc, ActionEditor EFGHOne\nareachair_two@efgh.cc, ActionEditor EFGHTwo\nareachair_three@efgh.cc, ActionEditor EFGHThree' },
                    'invite_message_subject_template': { 'value': '[EFGH 2025] Invitation to serve as Action Editor' },
                    'invite_message_body_template': { 'value': 'Dear Action Editor {{fullname}},\n\nWe are pleased to invite you to serve as an Action Editor for the EFGH 2025 Conference.\n\nPlease accept or decline the invitation using the link below:\n\n{{invitation_url}}\n\nBest regards,\nEFGH 2025 Program Chairs' },
                },
                group=openreview.api.Group()
            )
        helpers.await_queue_edit(openreview_client, edit_id=edit['id'])
        helpers.await_queue_edit(openreview_client, edit_id=edit['id'], process_index=1)

        invited_group = openreview_client.get_group('EFGH.cc/2025/Conference/Action_Editors/Invited')
        assert set(invited_group.members) == {'areachair_one@efgh.cc', 'areachair_two@efgh.cc', 'areachair_three@efgh.cc'}
        assert openreview_client.get_group('EFGH.cc/2025/Conference/Action_Editors/Declined').members == []
        assert openreview_client.get_group('EFGH.cc/2025/Conference/Action_Editors').members == []

        edits = openreview_client.get_group_edits(group_id='EFGH.cc/2025/Conference/Action_Editors/Invited', sort='tcdate:desc')

        messages = openreview_client.get_messages(to='programchair@efgh.cc', subject = 'Recruitment request status for EFGH 2025 Action Editor Group')
        assert len(messages) == 1
        assert messages[0]['content']['text'] == f'''The recruitment request process for the Action Editor Group has been completed.

Invited: 3
Already invited: 0
Already member: 0
Errors: 0

For more details, please check the following links:

- [recruitment request details](https://openreview.net/group/revisions?id=EFGH.cc/2025/Conference/Action_Editors&editId={edit['id']})
- [invited list](https://openreview.net/group/revisions?id=EFGH.cc/2025/Conference/Action_Editors/Invited&editId={edits[0].id})
- [all invited list](https://openreview.net/group/edit?id=EFGH.cc/2025/Conference/Action_Editors/Invited)'''

        messages = openreview_client.get_messages(to='areachair_one@efgh.cc', subject = '[EFGH 2025] Invitation to serve as Action Editor')
        assert len(messages) == 1

        text = messages[0]['content']['text']

        ## Accept invitation
        invitation_url = re.search('https://.*\n', text).group(0).replace('https://openreview.net', 'http://localhost:3030').replace('&amp;', '&')[:-1]        
        helpers.respond_invitation(selenium, request_page, invitation_url, accept=True)

        edits = openreview_client.get_note_edits(invitation='EFGH.cc/2025/Conference/Action_Editors/-/Recruitment_Response')
        assert len(edits) == 1
        helpers.await_queue_edit(openreview_client, edit_id=edits[0].id)

        assert set(openreview_client.get_group('EFGH.cc/2025/Conference/Action_Editors/Invited').members) == {'areachair_one@efgh.cc', 'areachair_two@efgh.cc', 'areachair_three@efgh.cc'}
        assert openreview_client.get_group('EFGH.cc/2025/Conference/Action_Editors/Declined').members == []
        assert openreview_client.get_group('EFGH.cc/2025/Conference/Action_Editors').members == ['areachair_one@efgh.cc']

        messages = openreview_client.get_messages(to='areachair_one@efgh.cc', subject = '[EFGH 2025] Action Editor Invitation accepted')
        assert len(messages) == 1

        ## Remind action editors to respond the invitation
        edit = openreview_client.post_group_edit(
                invitation='EFGH.cc/2025/Conference/Action_Editors/-/Recruitment_Request_Reminder',
                content={
                    'invite_reminder_message_subject_template': { 'value': '[EFGH 2025] Reminder: Invitation to serve as Action Editor' },
                    'invite_reminder_message_body_template': { 'value': 'Dear Action Editor {{fullname}},\n\nWe are pleased to invite you to serve as an Action Editor for the EFGH 2025 Conference.\n\nPlease accept or decline the invitation using the link below:\n\n{{invitation_url}}\n\nBest regards,\nEFGH 2025 Program Chairs' },
                },
                group=openreview.api.Group()
            )
        helpers.await_queue_edit(openreview_client, edit_id=edit['id'])

        assert openreview_client.get_messages(to='areachair_two@efgh.cc', subject = '[EFGH 2025] Reminder: Invitation to serve as Action Editor')
        assert openreview_client.get_messages(to='areachair_three@efgh.cc', subject = '[EFGH 2025] Reminder: Invitation to serve as Action Editor')

    def test_post_submissions(self, openreview_client, test_client, helpers):

        test_client = openreview.api.OpenReviewClient(token=test_client.token)

        domains = ['cs.umass.edu', 'google.com', 'mit.edu', 'deepmind.com', 'co.ux', 'apple.com', 'nvidia.com']
        for i in range(1,11):
            note = openreview.api.Note(
                license = 'CC BY 4.0',
                content = {
                    'title': { 'value': 'Paper title ' + str(i) },
                    'abstract': { 'value': 'This is an abstract ' + str(i) },
                    'authorids': { 'value': ['~SomeFirstName_User1', 'andrew@' + domains[i % 7]] },
                    'authors': { 'value': ['SomeFirstName User', 'Andrew Mc'] },
                    'keywords': { 'value': ['computer vision'] },
                    'pdf': {'value': '/pdf/' + 'p' * 40 +'.pdf' },
                    'email_sharing': { 'value': 'We authorize the sharing of all author emails with Program Chairs.' },
                    'data_release': { 'value': 'We authorize the release of our submission and author names to the public in the event of acceptance.' },
                }
            )

            if i == 5:
                note.content['authors']['value'].append('ReviewerOne EFGH')
                note.content['authorids']['value'].append('~ReviewerOne_EFGH1')

            if i == 7:
                note.content['authors']['value'].append('ACOne EFGH')
                note.content['authorids']['value'].append('~ACOne_EFGH1')

            test_client.post_note_edit(invitation='EFGH.cc/2025/Conference/-/Submission',
                signatures=['~SomeFirstName_User1'],
                note=note)

        helpers.await_queue_edit(openreview_client, invitation='EFGH.cc/2025/Conference/-/Submission', count=10)

        submissions = openreview_client.get_notes(invitation='EFGH.cc/2025/Conference/-/Submission', sort='number:asc')
        assert len(submissions) == 10
        assert submissions[0].readers == ['EFGH.cc/2025/Conference', '~SomeFirstName_User1', 'andrew@google.com']

        pc_client=openreview.api.OpenReviewClient(username='programchair@efgh.cc', password=helpers.strong_password)

        # expire submission deadline
        now = datetime.datetime.now()
        new_cdate = openreview.tools.datetime_millis(now - datetime.timedelta(days=1))
        new_duedate = openreview.tools.datetime_millis(now - datetime.timedelta(minutes=31))

        edit = pc_client.post_invitation_edit(
            invitations='EFGH.cc/2025/Conference/-/Submission/Dates',
            content={
                'activation_date': { 'value': new_cdate },
                'due_date': { 'value': new_duedate }
            }
        )

        helpers.await_queue_edit(openreview_client, edit_id=edit['id'])

        # hide fields from reviewers and ACs
        pc_client.post_invitation_edit(
            invitations='EFGH.cc/2025/Conference/-/Submission_Change_Before_Bidding/Restrict_Field_Visibility',
            content = {
                'content_readers': {
                    'value': {
                        'authors': {
                            'readers': [
                                'EFGH.cc/2025/Conference',
                                'EFGH.cc/2025/Conference/Submission${{4/id}/number}/Authors'
                            ]
                        },
                        'authorids': {
                            'readers': [
                                'EFGH.cc/2025/Conference',
                                'EFGH.cc/2025/Conference/Submission${{4/id}/number}/Authors'
                            ]
                        },
                        'pdf': {
                            'readers': [
                                'EFGH.cc/2025/Conference',
                                'EFGH.cc/2025/Conference/Submission${{4/id}/number}/Authors'
                            ]
                        },
                        'data_release': {
                            'readers': [
                                'EFGH.cc/2025/Conference',
                                'EFGH.cc/2025/Conference/Submission${{4/id}/number}/Authors'
                            ]
                        },
                        'email_sharing': {
                            'readers': [
                                'EFGH.cc/2025/Conference',
                                'EFGH.cc/2025/Conference/Submission${{4/id}/number}/Authors'
                            ]
                        }
                    }
                }
            }
        )
        helpers.await_queue_edit(openreview_client, edit_id='EFGH.cc/2025/Conference/-/Submission_Change_Before_Bidding-0-1', count=2)

        # manually update cdate of post submission invitations
        pc_client.post_invitation_edit(
            invitations='EFGH.cc/2025/Conference/-/Submission_Change_Before_Bidding/Dates',
            content={
                'activation_date': { 'value': openreview.tools.datetime_millis(now - datetime.timedelta(minutes=30)) }
            }
        )
        helpers.await_queue_edit(openreview_client, edit_id='EFGH.cc/2025/Conference/-/Submission_Change_Before_Bidding-0-1', count=3)

        edit = pc_client.post_invitation_edit(
            invitations='EFGH.cc/2025/Conference/-/Withdrawal/Dates',
            content={
                'activation_date': { 'value': openreview.tools.datetime_millis(now - datetime.timedelta(minutes=30)) },
                'expiration_date': { 'value': openreview.tools.datetime_millis(now + datetime.timedelta(days=31)) }
            }
        )

        helpers.await_queue_edit(openreview_client, edit_id=edit['id'])
        helpers.await_queue_edit(openreview_client, edit_id='EFGH.cc/2025/Conference/-/Withdrawal-0-1', count=2)

        edit = pc_client.post_invitation_edit(
            invitations='EFGH.cc/2025/Conference/-/Desk_Rejection/Dates',
            content={
                'activation_date': { 'value': openreview.tools.datetime_millis(now - datetime.timedelta(minutes=30)) },
                'expiration_date': { 'value': openreview.tools.datetime_millis(now + datetime.timedelta(days=31)) }
            }
        )

        helpers.await_queue_edit(openreview_client, edit_id=edit['id'])
        helpers.await_queue_edit(openreview_client, edit_id='EFGH.cc/2025/Conference/-/Desk_Rejection-0-1', count=2)

        pc_client.post_invitation_edit(
            invitations='EFGH.cc/2025/Conference/Reviewers/-/Submission_Group/Dates',
            content={
                'activation_date': { 'value': openreview.tools.datetime_millis(now - datetime.timedelta(minutes=30)) }
            }
        )

        helpers.await_queue_edit(openreview_client, edit_id='EFGH.cc/2025/Conference/Reviewers/-/Submission_Group-0-1', count=2)

        pc_client.post_invitation_edit(
            invitations='EFGH.cc/2025/Conference/Action_Editors/-/Submission_Group/Dates',
            content={
                'activation_date': { 'value': openreview.tools.datetime_millis(now - datetime.timedelta(minutes=30)) }
            }
        )

        helpers.await_queue_edit(openreview_client, edit_id='EFGH.cc/2025/Conference/Action_Editors/-/Submission_Group-0-1', count=2)

        submissions = openreview_client.get_notes(invitation='EFGH.cc/2025/Conference/-/Submission', sort='number:asc')
        assert len(submissions) == 10
        assert submissions[0].readers == ['EFGH.cc/2025/Conference', 'EFGH.cc/2025/Conference/Action_Editors', 'EFGH.cc/2025/Conference/Reviewers', 'EFGH.cc/2025/Conference/Submission1/Authors']
        assert submissions[0].content['authors']['readers'] == ['EFGH.cc/2025/Conference', 'EFGH.cc/2025/Conference/Submission1/Authors']
        assert submissions[0].content['authorids']['readers'] == ['EFGH.cc/2025/Conference', 'EFGH.cc/2025/Conference/Submission1/Authors']
        assert submissions[0].content['email_sharing']['readers'] == ['EFGH.cc/2025/Conference', 'EFGH.cc/2025/Conference/Submission1/Authors']
        assert submissions[0].content['data_release']['readers'] == ['EFGH.cc/2025/Conference', 'EFGH.cc/2025/Conference/Submission1/Authors']
        assert submissions[0].content['pdf']['readers'] == ['EFGH.cc/2025/Conference', 'EFGH.cc/2025/Conference/Submission1/Authors']

        submission_groups = openreview_client.get_all_groups(prefix='EFGH.cc/2025/Conference/Submission')
        reviewer_groups = [group for group in submission_groups if group.id.endswith('/Reviewers')]
        assert len(reviewer_groups) == 10
        action_editor_groups = [group for group in submission_groups if group.id.endswith('/Action_Editors')]
        assert len(action_editor_groups) == 10

        withdrawal_invitations = openreview_client.get_all_invitations(invitation='EFGH.cc/2025/Conference/-/Withdrawal')
        assert len(withdrawal_invitations) == 10

        desk_rejection_invitations = openreview_client.get_all_invitations(invitation='EFGH.cc/2025/Conference/-/Desk_Rejection')
        assert len(desk_rejection_invitations) == 10

    def test_ac_bidding(self, openreview_client, selenium, request_page, helpers):

        pc_client=openreview.api.OpenReviewClient(username='programchair@efgh.cc', password=helpers.strong_password)

        bid_invitation = openreview_client.get_invitation('EFGH.cc/2025/Conference/Action_Editors/-/Bid')
        assert bid_invitation
        assert bid_invitation.edit['label']['param']['enum'] == ['Very High', 'High', 'Neutral', 'Low', 'Very Low']
        assert bid_invitation.minReplies == 50

        #open bidding
        now = datetime.datetime.now()
        new_cdate = openreview.tools.datetime_millis(now)
        new_duedate = openreview.tools.datetime_millis(now + datetime.timedelta(days=5))

        pc_client.post_invitation_edit(
            invitations='EFGH.cc/2025/Conference/Action_Editors/-/Bid/Dates',
            content={
                'activation_date': { 'value': new_cdate },
                'due_date': { 'value': new_duedate },
                'expiration_date': { 'value': new_duedate }
            }
        )

        # change bidding options
        pc_client.post_invitation_edit(
            invitations='EFGH.cc/2025/Conference/Action_Editors/-/Bid/Settings',
            content={
                'bid_count': { 'value': 20 },
                'labels': { 'value': ['Very High', 'High', 'Low', 'Conflict'] }
            }
        )

        bid_invitation = openreview_client.get_invitation('EFGH.cc/2025/Conference/Action_Editors/-/Bid')
        assert bid_invitation
        assert bid_invitation.duedate == new_duedate
        assert bid_invitation.expdate == new_duedate
        assert bid_invitation.edit['label']['param']['enum'] == ['Very High', 'High', 'Low', 'Conflict']
        assert bid_invitation.minReplies == 20

        ac_client = OpenReviewClient(username='areachair_one@efgh.cc', password=helpers.strong_password)

        submissions = ac_client.get_all_notes(content={'venueid': 'EFGH.cc/2025/Conference/Submission'}, sort='number:asc')
        assert len(submissions) == 10

        invitation = openreview_client.get_invitation('EFGH.cc/2025/Conference/Action_Editors/-/Bid')
        assert invitation.edit['tail']['param']['options']['group'] == 'EFGH.cc/2025/Conference/Action_Editors'

        # Check that ac bid console loads
        request_page(selenium, f'http://localhost:3030/invitation?id={invitation.id}', ac_client.token, wait_for_element='header')
        header = selenium.find_element(By.ID, 'header')
        assert 'Action Editor Bidding Console' in header.text

    def test_ac_setup_matching(self, openreview_client, helpers):

        pc_client=openreview.api.OpenReviewClient(username='programchair@efgh.cc', password=helpers.strong_password)

        openreview_client.add_members_to_group('EFGH.cc/2025/Conference/Action_Editors', ['areachair_two@efgh.cc', 'areachair_three@efgh.cc'])

        #upload affinity scores file
        submissions = openreview_client.get_all_notes(content={'venueid': 'EFGH.cc/2025/Conference/Submission'})
        with open(os.path.join(os.path.dirname(__file__), 'data/ac_scores_venue.csv'), 'w') as file_handle:
            writer = csv.writer(file_handle)
            for submission in submissions:
                for rev in openreview_client.get_group('EFGH.cc/2025/Conference/Action_Editors').members:
                    writer.writerow([submission.id, rev, round(random.random(), 2)])

        conflicts_invitation = openreview_client.get_invitation('EFGH.cc/2025/Conference/Action_Editors/-/Conflict')
        assert conflicts_invitation
        domain_content = openreview_client.get_group('EFGH.cc/2025/Conference').content
        assert domain_content['area_chairs_conflict_id']['value'] == 'EFGH.cc/2025/Conference/Action_Editors/-/Conflict'
        assert domain_content['area_chairs_affinity_score_id']['value'] == 'EFGH.cc/2025/Conference/Action_Editors/-/Affinity_Score'
        assert domain_content['area_chairs_custom_max_papers_id']['value'] == 'EFGH.cc/2025/Conference/Action_Editors/-/Custom_Max_Papers'
        assert openreview_client.get_invitation('EFGH.cc/2025/Conference/Action_Editors/-/Conflict/Dates')
        assert openreview_client.get_invitation('EFGH.cc/2025/Conference/Action_Editors/-/Conflict/Policy')
        assert domain_content['area_chairs_conflict_policy']['value'] == 'Default'
        assert domain_content['area_chairs_conflict_n_years']['value'] == 0

        # trigger date process
        now = datetime.datetime.now()
        new_cdate = openreview.tools.datetime_millis(now)
        pc_client.post_invitation_edit(
            invitations='EFGH.cc/2025/Conference/Action_Editors/-/Conflict/Dates',
            content={
                'activation_date': { 'value': new_cdate }
            }
        )
        helpers.await_queue_edit(openreview_client, 'EFGH.cc/2025/Conference/Action_Editors/-/Conflict-0-1', count=2)

        conflicts = pc_client.get_edges_count(invitation='EFGH.cc/2025/Conference/Action_Editors/-/Conflict')
        assert conflicts == 14

        openreview_client.add_members_to_group('EFGH.cc/2025/Conference/Reviewers', ['reviewer_one@efgh.cc', 'reviewer_two@efgh.cc', 'reviewer_three@efgh.cc'])

        # trigger date process for reviewer conflicts
        now = datetime.datetime.now()
        new_cdate = openreview.tools.datetime_millis(now)
        pc_client.post_invitation_edit(
            invitations='EFGH.cc/2025/Conference/Reviewers/-/Conflict/Dates',
            content={
                'activation_date': { 'value': new_cdate }
            }
        )
        helpers.await_queue_edit(openreview_client, 'EFGH.cc/2025/Conference/Reviewers/-/Conflict-0-1', count=2)

        conflicts = pc_client.get_edges_count(invitation='EFGH.cc/2025/Conference/Reviewers/-/Conflict')
        assert conflicts == 14

        submissions = openreview_client.get_all_notes(content={'venueid': 'EFGH.cc/2025/Conference/Submission'}, sort='number:asc')

        paper_conflicts = openreview_client.get_edges(invitation='EFGH.cc/2025/Conference/Reviewers/-/Conflict', head=submissions[0].id)
        assert 'EFGH.cc/2025/Conference/Action_Editors' in paper_conflicts[0].readers
        assert paper_conflicts[0].readers == ['EFGH.cc/2025/Conference', 'EFGH.cc/2025/Conference/Action_Editors',  paper_conflicts[0].tail]

    def test_review_stage(self, openreview_client, helpers):

        pc_client=openreview.api.OpenReviewClient(username='programchair@efgh.cc', password=helpers.strong_password)

        now = datetime.datetime.now()
        # manually trigger Submission_Chage_Before_Reviewing
        openreview_client.post_invitation_edit(
            invitations='EFGH.cc/2025/Conference/-/Edit',
            signatures=['EFGH.cc/2025/Conference'],
            invitation=openreview.api.Invitation(
                id='EFGH.cc/2025/Conference/-/Submission_Change_Before_Reviewing',
                cdate=openreview.tools.datetime_millis(now),
                signatures=['EFGH.cc/2025/Conference']
            )
        )
        helpers.await_queue_edit(openreview_client, 'EFGH.cc/2025/Conference/-/Submission_Change_Before_Reviewing-0-1', count=2)

        submissions = openreview_client.get_notes(invitation='EFGH.cc/2025/Conference/-/Submission', sort='number:asc')
        assert submissions[0].readers == ['EFGH.cc/2025/Conference','EFGH.cc/2025/Conference/Submission1/Action_Editors', 'EFGH.cc/2025/Conference/Submission1/Reviewers', 'EFGH.cc/2025/Conference/Submission1/Authors']

        # create child invitations
        now = datetime.datetime.now()
        new_cdate = openreview.tools.datetime_millis(now)
        new_duedate = openreview.tools.datetime_millis(now + datetime.timedelta(days=3))

        pc_client.post_invitation_edit(
            invitations='EFGH.cc/2025/Conference/-/Official_Review/Dates',
            content={
                'activation_date': { 'value': new_cdate },
                'due_date': { 'value': new_duedate },
                'expiration_date': { 'value': new_duedate }
            }
        )
        helpers.await_queue_edit(openreview_client, edit_id='EFGH.cc/2025/Conference/-/Official_Review-0-1', count=2)

        invitations = openreview_client.get_invitations(invitation='EFGH.cc/2025/Conference/-/Official_Review')
        assert len(invitations) == 10

        invitation  = openreview_client.get_invitation('EFGH.cc/2025/Conference/Submission1/-/Official_Review')
        assert invitation and invitation.edit['note']['readers'] == [
            'EFGH.cc/2025/Conference/Program_Chairs',
            'EFGH.cc/2025/Conference/Submission1/Action_Editors', ## ACs are added by default as readers of reviews
            '${3/signatures}'
        ]

    def test_comment_stage(self, openreview_client, helpers):

        pc_client=openreview.api.OpenReviewClient(username='programchair@efgh.cc', password=helpers.strong_password)

        assert pc_client.get_invitation('EFGH.cc/2025/Conference/-/Official_Comment')
        assert pc_client.get_invitation('EFGH.cc/2025/Conference/-/Official_Comment/Dates')
        assert pc_client.get_invitation('EFGH.cc/2025/Conference/-/Official_Comment/Form_Fields')
        assert pc_client.get_invitation('EFGH.cc/2025/Conference/-/Official_Comment/Writers_and_Readers')
        assert pc_client.get_invitation('EFGH.cc/2025/Conference/-/Official_Comment/Notifications')

        # create child invitations
        now = datetime.datetime.now()
        new_cdate = openreview.tools.datetime_millis(now)
        new_duedate = openreview.tools.datetime_millis(now + datetime.timedelta(days=4))

        pc_client.post_invitation_edit(
            invitations='EFGH.cc/2025/Conference/-/Official_Comment/Dates',
            content={
                'activation_date': { 'value': new_cdate },
                'expiration_date': { 'value': new_duedate }
            }
        )
        helpers.await_queue_edit(openreview_client, edit_id='EFGH.cc/2025/Conference/-/Official_Comment-0-1', count=2)

        invitations = openreview_client.get_invitations(invitation='EFGH.cc/2025/Conference/-/Official_Comment')
        assert len(invitations) == 10

        invitation  = openreview_client.get_invitation('EFGH.cc/2025/Conference/Submission1/-/Official_Comment')
        assert invitation.invitees == [
            'EFGH.cc/2025/Conference',
            'openreview.net/Support',
            'EFGH.cc/2025/Conference/Submission1/Action_Editors',
            'EFGH.cc/2025/Conference/Submission1/Reviewers',
            'EFGH.cc/2025/Conference/Submission1/Authors'
        ]
        assert invitation and invitation.edit['note']['readers']['param']['items'] == [
          {
            "value": "EFGH.cc/2025/Conference/Program_Chairs",
            "optional": False
          },
          {
            "value": "EFGH.cc/2025/Conference/Submission1/Action_Editors",
            "optional": True
          },
          {
            "value": "EFGH.cc/2025/Conference/Submission1/Reviewers",
            "optional": True
          },
          {
            "inGroup": "EFGH.cc/2025/Conference/Submission1/Reviewers",
            "optional": True
          },
          {
            "value": "EFGH.cc/2025/Conference/Submission1/Authors",
            "optional": True
          }
        ]

    def test_review_release_stage(self, openreview_client, helpers):

        pc_client=openreview.api.OpenReviewClient(username='programchair@efgh.cc', password=helpers.strong_password)
        assert pc_client.get_invitation('EFGH.cc/2025/Conference/-/Official_Review_Release')
        assert pc_client.get_invitation('EFGH.cc/2025/Conference/-/Official_Review_Release/Dates')
        assert pc_client.get_invitation('EFGH.cc/2025/Conference/-/Official_Review_Release/Readers')

        review_release_inv = openreview.tools.get_invitation(openreview_client, 'EFGH.cc/2025/Conference/-/Official_Review_Release')
        assert review_release_inv.edit['invitation']['edit']['invitation']['edit']['note']['readers'] == [
            'EFGH.cc/2025/Conference/Program_Chairs',
            'EFGH.cc/2025/Conference/Submission${5/content/noteNumber/value}/Action_Editors',
            'EFGH.cc/2025/Conference/Submission${5/content/noteNumber/value}/Reviewers',
            'EFGH.cc/2025/Conference/Submission${5/content/noteNumber/value}/Authors'
        ]

    def test_rebuttal_stage(self, openreview_client, helpers):

        pc_client=openreview.api.OpenReviewClient(username='programchair@efgh.cc', password=helpers.strong_password)
        assert pc_client.get_invitation('EFGH.cc/2025/Conference/-/Author_Rebuttal')
        assert pc_client.get_invitation('EFGH.cc/2025/Conference/-/Author_Rebuttal/Dates')
        assert pc_client.get_invitation('EFGH.cc/2025/Conference/-/Author_Rebuttal/Form_Fields')
        assert pc_client.get_invitation('EFGH.cc/2025/Conference/-/Author_Rebuttal/Readers')

        # create child invitations
        now = datetime.datetime.now()
        new_cdate = openreview.tools.datetime_millis(now)
        new_duedate = openreview.tools.datetime_millis(now + datetime.timedelta(days=4))

        pc_client.post_invitation_edit(
            invitations='EFGH.cc/2025/Conference/-/Author_Rebuttal/Dates',
            content={
                'activation_date': { 'value': new_cdate },
                'due_date': { 'value': new_duedate },
                'expiration_date': { 'value': new_duedate }
            }
        )
        helpers.await_queue_edit(openreview_client, edit_id='EFGH.cc/2025/Conference/-/Author_Rebuttal-0-1', count=2)

        invitations = openreview_client.get_invitations(invitation='EFGH.cc/2025/Conference/-/Author_Rebuttal')
        assert len(invitations) == 10

        invitation  = openreview_client.get_invitation('EFGH.cc/2025/Conference/Submission1/-/Author_Rebuttal')
        assert invitation.invitees == [
            'EFGH.cc/2025/Conference',
            'EFGH.cc/2025/Conference/Submission1/Authors'
        ]

        assert invitation and invitation.edit['readers'] == [
            'EFGH.cc/2025/Conference/Program_Chairs',
            'EFGH.cc/2025/Conference/Submission1/Action_Editors',
            'EFGH.cc/2025/Conference/Submission1/Reviewers',
            'EFGH.cc/2025/Conference/Submission1/Authors'
        ]

    def test_metareview_stage(self, openreview_client, helpers):

        pc_client=openreview.api.OpenReviewClient(username='programchair@efgh.cc', password=helpers.strong_password)
        assert pc_client.get_invitation('EFGH.cc/2025/Conference/-/Meta_Review')
        assert pc_client.get_invitation('EFGH.cc/2025/Conference/-/Meta_Review/Dates')
        assert pc_client.get_invitation('EFGH.cc/2025/Conference/-/Meta_Review/Form_Fields')
        assert pc_client.get_invitation('EFGH.cc/2025/Conference/-/Meta_Review/Readers')

        # create child invitations
        now = datetime.datetime.now()
        new_cdate = openreview.tools.datetime_millis(now)
        new_duedate = openreview.tools.datetime_millis(now + datetime.timedelta(days=4))

        pc_client.post_invitation_edit(
            invitations='EFGH.cc/2025/Conference/-/Meta_Review/Dates',
            content={
                'activation_date': { 'value': new_cdate },
                'due_date': { 'value': new_duedate },
                'expiration_date': { 'value': new_duedate }
            }
        )
        helpers.await_queue_edit(openreview_client, edit_id='EFGH.cc/2025/Conference/-/Meta_Review-0-1', count=2)

        invitations = openreview_client.get_invitations(invitation='EFGH.cc/2025/Conference/-/Meta_Review')
        assert len(invitations) == 10

        invitation  = openreview_client.get_invitation('EFGH.cc/2025/Conference/Submission1/-/Meta_Review')
        assert invitation.invitees == [
            'EFGH.cc/2025/Conference',
            'EFGH.cc/2025/Conference/Submission1/Action_Editors'
        ]

        assert invitation and invitation.edit['readers'] == [
            'EFGH.cc/2025/Conference/Submission1/Action_Editors',
            'EFGH.cc/2025/Conference/Program_Chairs'
        ]

    def test_decision_stage(self, openreview_client, helpers):

        pc_client = openreview.api.OpenReviewClient(username='programchair@efgh.cc', password=helpers.strong_password)

        invitation =  pc_client.get_invitation('EFGH.cc/2025/Conference/-/Decision')
        assert invitation
        assert pc_client.get_invitation('EFGH.cc/2025/Conference/-/Decision/Dates')
        assert pc_client.get_invitation('EFGH.cc/2025/Conference/-/Decision/Readers')
        assert pc_client.get_invitation('EFGH.cc/2025/Conference/-/Decision/Decision_Options')
        assert pc_client.get_invitation('EFGH.cc/2025/Conference/-/Decision_Upload')
        assert pc_client.get_invitation('EFGH.cc/2025/Conference/-/Decision_Upload/Decision_CSV')

        # create child invitations
        now = datetime.datetime.now()
        new_cdate = openreview.tools.datetime_millis(now)
        new_duedate = openreview.tools.datetime_millis(now + datetime.timedelta(days=4))

        pc_client.post_invitation_edit(
            invitations='EFGH.cc/2025/Conference/-/Decision/Dates',
            content={
                'activation_date': { 'value': new_cdate },
                'due_date': { 'value': new_duedate },
                'expiration_date': { 'value': new_duedate }
            }
        )
        helpers.await_queue_edit(openreview_client, edit_id='EFGH.cc/2025/Conference/-/Decision-0-1', count=2)

        invitations = openreview_client.get_invitations(invitation='EFGH.cc/2025/Conference/-/Decision')
        assert len(invitations) == 10

        invitation  = openreview_client.get_invitation('EFGH.cc/2025/Conference/Submission1/-/Decision')

        assert invitation and invitation.edit['readers'] == [
            'EFGH.cc/2025/Conference/Program_Chairs'
        ]

        submissions = openreview_client.get_notes(invitation='EFGH.cc/2025/Conference/-/Submission', sort='number:asc')

        decisions = ['Accept (Oral)', 'Accept (Poster)', 'Reject']
        comment = {
            'Accept (Oral)': 'Congratulations on your oral acceptance.',
            'Accept (Poster)': 'Congratulations on your poster acceptance.',
            'Reject': 'We regret to inform you...'
        }

        with open(os.path.join(os.path.dirname(__file__), 'data/EFGH_decisions.csv'), 'w') as file_handle:
            writer = csv.writer(file_handle)
            writer.writerow([submissions[0].number, 'Accept (Oral)', comment['Accept (Oral)']])
            writer.writerow([submissions[1].number, 'Accept (Poster)', comment['Accept (Poster)']])
            writer.writerow([submissions[2].number, 'Reject', comment['Reject']])
            for submission in submissions[3:]:
                decision = random.choice(decisions)
                writer.writerow([submission.number, decision, comment[decision]])

        url = pc_client.put_attachment(os.path.join(os.path.dirname(__file__), 'data/EFGH_decisions.csv'),
                                         'EFGH.cc/2025/Conference/-/Decision_Upload/Decision_CSV', 'decision_CSV')

        now = datetime.datetime.now()

        pc_client.post_invitation_edit(
            invitations='EFGH.cc/2025/Conference/-/Decision_Upload/Decision_CSV',

            content={
                'upload_date': { 'value': openreview.tools.datetime_millis(now) },
                'decision_CSV': { 'value': url }
            }
        )
        helpers.await_queue_edit(openreview_client, edit_id='EFGH.cc/2025/Conference/-/Decision_Upload-0-1', count=2)

        helpers.await_queue_edit(openreview_client, invitation='EFGH.cc/2025/Conference/Submission1/-/Decision')

        decision_note = openreview_client.get_notes(invitation='EFGH.cc/2025/Conference/Submission1/-/Decision')[0]
        assert decision_note and decision_note.content['decision']['value'] == 'Accept (Oral)'
        assert decision_note.readers == ['EFGH.cc/2025/Conference/Program_Chairs']

    def test_decision_release_stage(self, openreview_client, helpers):

        pc_client = openreview.api.OpenReviewClient(username='programchair@efgh.cc', password=helpers.strong_password)
        assert pc_client.get_invitation('EFGH.cc/2025/Conference/-/Decision_Release')
        assert pc_client.get_invitation('EFGH.cc/2025/Conference/-/Decision_Release/Dates')
        assert pc_client.get_invitation('EFGH.cc/2025/Conference/-/Decision_Release/Readers')

        # assert reviews are visible only to PCs
        decision = openreview_client.get_notes(invitation='EFGH.cc/2025/Conference/Submission1/-/Decision', sort='number:asc')
        assert len(decision) == 1
        assert decision[0].readers == [
            'EFGH.cc/2025/Conference/Program_Chairs'
        ]
        assert decision[0].nonreaders == ['EFGH.cc/2025/Conference/Submission1/Authors']

        decision_release_inv = openreview.tools.get_invitation(openreview_client, 'EFGH.cc/2025/Conference/-/Decision_Release')
        assert decision_release_inv.edit['invitation']['edit']['invitation']['edit']['note']['readers'] == [
            'EFGH.cc/2025/Conference/Program_Chairs',
            'EFGH.cc/2025/Conference/Submission${5/content/noteNumber/value}/Action_Editors',
            'EFGH.cc/2025/Conference/Submission${5/content/noteNumber/value}/Reviewers',
            'EFGH.cc/2025/Conference/Submission${5/content/noteNumber/value}/Authors'
        ]
        assert decision_release_inv.edit['invitation']['edit']['invitation']['edit']['note']['nonreaders'] == []

        # change decision readers to ACs and authors
        pc_client.post_invitation_edit(
            invitations='EFGH.cc/2025/Conference/-/Decision_Release/Readers',
            content = {
                'readers': {
                    'value':  [
                        'EFGH.cc/2025/Conference/Program_Chairs',
                        'EFGH.cc/2025/Conference/Submission${5/content/noteNumber/value}/Action_Editors',
                        'EFGH.cc/2025/Conference/Submission${5/content/noteNumber/value}/Authors'
                    ]
                }
            }
        )

        helpers.await_queue_edit(openreview_client, edit_id='EFGH.cc/2025/Conference/-/Decision_Release-0-1', count=2)

        decision_release_inv = openreview.tools.get_invitation(openreview_client, 'EFGH.cc/2025/Conference/-/Decision_Release')
        assert decision_release_inv.edit['invitation']['edit']['invitation']['edit']['note']['readers'] == [
            'EFGH.cc/2025/Conference/Program_Chairs',
            'EFGH.cc/2025/Conference/Submission${5/content/noteNumber/value}/Action_Editors',
            'EFGH.cc/2025/Conference/Submission${5/content/noteNumber/value}/Authors'
        ]
        assert decision_release_inv.edit['invitation']['edit']['invitation']['edit']['note']['nonreaders'] == []

        # release decisions
        now = datetime.datetime.now()
        pc_client.post_invitation_edit(
            invitations='EFGH.cc/2025/Conference/-/Decision_Release/Dates',
            content={
                'activation_date': { 'value': openreview.tools.datetime_millis(now) }
            }
        )
        helpers.await_queue_edit(openreview_client, edit_id='EFGH.cc/2025/Conference/-/Decision_Release-0-1', count=3)
        helpers.await_queue_edit(openreview_client, edit_id='EFGH.cc/2025/Conference/-/Decision-0-1', count=3)

        # assert decisions are visible to PCs, paper ACs and paper authors
        decisions = openreview_client.get_notes(invitation='EFGH.cc/2025/Conference/Submission1/-/Decision', sort='number:asc')
        assert len(decisions) == 1
        assert decisions[0].readers == [
            'EFGH.cc/2025/Conference/Program_Chairs',
            'EFGH.cc/2025/Conference/Submission1/Action_Editors',
            'EFGH.cc/2025/Conference/Submission1/Authors'
        ]
        assert decisions[0].nonreaders == []

    def test_release_submissions(self, openreview_client, helpers):

        pc_client = openreview.api.OpenReviewClient(username='programchair@efgh.cc', password=helpers.strong_password)
        submissions = openreview_client.get_notes(invitation='EFGH.cc/2025/Conference/-/Submission', sort='number:asc')
        assert submissions[0].readers == [
            'EFGH.cc/2025/Conference',
            'EFGH.cc/2025/Conference/Submission1/Action_Editors',
            'EFGH.cc/2025/Conference/Submission1/Reviewers',
            'EFGH.cc/2025/Conference/Submission1/Authors'
        ]
        assert not submissions[0].pdate
        assert submissions[0].content['authors']['readers'] == [
            'EFGH.cc/2025/Conference',
            'EFGH.cc/2025/Conference/Submission1/Authors'
        ]
        assert submissions[0].content['venueid']['value'] == 'EFGH.cc/2025/Conference/Submission'
        assert submissions[0].content['venue']['value'] == 'EFGH 2025 Conference Submission'
        inv = pc_client.get_invitation('EFGH.cc/2025/Conference/-/Submission_Release')
        assert inv and inv.content['source']['value'] == 'accepted_submissions'
        assert pc_client.get_invitation('EFGH.cc/2025/Conference/-/Submission_Release/Dates')
        assert pc_client.get_invitation('EFGH.cc/2025/Conference/-/Submission_Release/Which_Submissions')
        now = datetime.datetime.now()
        new_cdate = openreview.tools.datetime_millis(now)

        pc_client.post_invitation_edit(
            invitations='EFGH.cc/2025/Conference/-/Submission_Release/Dates',
            content={
                'activation_date': { 'value': new_cdate }
            }
        )
        helpers.await_queue_edit(openreview_client, edit_id='EFGH.cc/2025/Conference/-/Submission_Release-0-1', count=2)

        submissions = openreview_client.get_notes(invitation='EFGH.cc/2025/Conference/-/Submission', sort='number:asc')

        assert submissions[0].readers == ['everyone']
        assert submissions[0].pdate
        assert 'readers' not in submissions[0].content['authors']
        assert submissions[0].content['venueid']['value'] == 'EFGH.cc/2025/Conference'
        assert submissions[0].content['venue']['value'] == 'EFGH 2025 Oral'

        assert submissions[1].readers == ['everyone']
        assert submissions[1].pdate
        assert 'readers' not in submissions[1].content['authors']

        assert submissions[1].content['venueid']['value'] == 'EFGH.cc/2025/Conference'
        assert submissions[1].content['venue']['value'] == 'EFGH 2025 Poster'

        assert submissions[2].readers == [
            'EFGH.cc/2025/Conference',
            'EFGH.cc/2025/Conference/Submission3/Action_Editors',
            'EFGH.cc/2025/Conference/Submission3/Reviewers',
            'EFGH.cc/2025/Conference/Submission3/Authors'
        ]
        assert not submissions[2].pdate
        assert submissions[2].content['authors']['readers'] == [
            'EFGH.cc/2025/Conference',
            'EFGH.cc/2025/Conference/Submission3/Authors'
        ]
        assert submissions[2].content['venueid']['value'] == 'EFGH.cc/2025/Conference/Rejected_Submission'
        assert submissions[2].content['venue']['value'] == 'Submitted to EFGH 2025'

        endorsement_tags = openreview_client.get_tags(invitation='EFGH.cc/2025/Conference/-/Article_Endorsement')
        assert endorsement_tags
        tags = openreview_client.get_tags(invitation='EFGH.cc/2025/Conference/-/Article_Endorsement', forum=submissions[0].id)
        assert len(tags) == 1 and tags[0].label == 'Oral'
        tags = openreview_client.get_tags(invitation='EFGH.cc/2025/Conference/-/Article_Endorsement', forum=submissions[1].id)
        assert len(tags) == 1 and tags[0].label == 'Poster'
        endorsement_tags = openreview_client.get_tags(parent_invitations='openreview.net/-/Article_Endorsement', stream=True)
        assert endorsement_tags