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
        helpers.create_user('areachair_one_two@efgh.cc', 'ACTwo', 'EFGH')
        helpers.create_user('areachair_one_three@efgh.cc', 'ACThree', 'EFGH')
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
        helpers.await_queue_edit(openreview_client, invitation='openreview.net/Template/-/Submission_Change_Before_Bidding')
        helpers.await_queue_edit(openreview_client, invitation='openreview.net/Template/-/Submission_Change_Before_Reviewing')

        helpers.await_queue_edit(openreview_client, 'EFGH.cc/2025/Conference/-/Withdrawal-0-1', count=1)
        helpers.await_queue_edit(openreview_client, 'EFGH.cc/2025/Conference/-/Desk_Rejection-0-1', count=1)
        helpers.await_queue_edit(openreview_client, 'EFGH.cc/2025/Conference/Reviewers/-/Submission_Group-0-1', count=1)
        helpers.await_queue_edit(openreview_client, 'EFGH.cc/2025/Conference/Action_Editors/-/Submission_Group-0-1', count=1)
        helpers.await_queue_edit(openreview_client, 'EFGH.cc/2025/Conference/-/Submission_Change_Before_Bidding-0-1', count=1)

        openreview_client.flush_members_cache('~ProgramChair_EFGH1')
        group = openreview.tools.get_group(openreview_client, 'EFGH.cc/2025/Conference')
        assert group.members == ['openreview.net/Template', 'EFGH.cc/2025/Conference/Program_Chairs', 'EFGH.cc/2025/Conference/Automated_Administrator']
        assert 'request_form_id' in group.content and group.content['request_form_id']['value'] == request.id

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

        messages = openreview_client.get_messages(to='programchair@efgh.cc', subject = 'Recruitment request status for EFGH 2025 Action Editors Group')
        assert len(messages) == 1
        assert messages[0]['content']['text'] == f'''The recruitment request process for the Action Editors Group has been completed.

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
