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

class TestChangeVenueEmail():

    def test_setup(self, openreview_client, helpers):
        super_id = 'openreview.net'
        support_group_id = super_id + '/Support'

        helpers.create_user('programchair@venueemail.cc', 'ProgramChair', 'VenueEmail')
        pc_client=openreview.api.OpenReviewClient(username='programchair@venueemail.cc', password=helpers.strong_password)

        assert openreview_client.get_invitation('openreview.net/-/Edit')
        assert openreview_client.get_group('openreview.net/Support/Venue_Request')
        assert openreview_client.get_invitation('openreview.net/Support/Venue_Request/-/Conference_Review_Workflow')
        assert openreview_client.get_invitation('openreview.net/Support/Venue_Request/Conference_Review_Workflow/-/Comment')
        assert openreview_client.get_invitation('openreview.net/Support/Venue_Request/Conference_Review_Workflow/-/Deployment')
        assert openreview_client.get_invitation('openreview.net/Support/Venue_Request/Conference_Review_Workflow/-/Status')

        now = datetime.datetime.now()
        start_date = now + datetime.timedelta(minutes=40)
        due_date = now + datetime.timedelta(days=2)

        request = pc_client.post_note_edit(invitation='openreview.net/Support/Venue_Request/-/Conference_Review_Workflow',
            signatures=['~ProgramChair_VenueEmail1'],
            note=openreview.api.Note(
                content={
                    'official_venue_name': { 'value': 'The Venue Email Conference' },
                    'abbreviated_venue_name': { 'value': 'VenueEmail 2025' },
                    'venue_website_url': { 'value': 'https://venueemail.cc/Conferences/2025' },
                    'location': { 'value': 'Amherst, Massachusetts' },
                    'venue_start_date': { 'value': openreview.tools.datetime_millis(now + datetime.timedelta(weeks=52)) },
                    'program_chair_emails': { 'value': ['programchair@venueemail.cc'] },
                    'contact_email': { 'value': 'venueemail2025.programchairs@gmail.com' },
                    'submission_start_date': { 'value': openreview.tools.datetime_millis(start_date) },
                    'submission_deadline': { 'value': openreview.tools.datetime_millis(due_date) },
                    'reviewer_groups_names': { 'value': ['Reviewers'] },
                    'area_chair_groups_names': { 'value': ['Area_Chairs'] },
                    'colocated': { 'value': 'Independent' },
                    'previous_venue': { 'value': 'VenueEmail.cc/2024/Conference' },
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

        messages = openreview_client.get_messages(to='programchair@venueemail.cc', subject='Your request for OpenReview service has been received.')
        assert len(messages) == 1

        request = openreview_client.get_note(request['note']['id'])
        assert openreview_client.get_invitation(f'openreview.net/Support/Venue_Request/Conference_Review_Workflow{request.number}/-/Comment')
        assert openreview.tools.get_group(openreview_client, 'VenueEmail.cc/2025/Conference/Program_Chairs') is None
        assert request.domain == 'openreview.net/Support'

        # deploy the venue
        edit = openreview_client.post_note_edit(invitation=f'openreview.net/Support/Venue_Request/Conference_Review_Workflow/-/Deployment',
            signatures=[support_group_id],
            note=openreview.api.Note(
                id=request.id,
                content={
                    'venue_id': { 'value': 'VenueEmail.cc/2025/Conference' }
                }
            ))

        helpers.await_queue_edit(openreview_client, edit_id=edit['id'])
        helpers.await_queue_edit(openreview_client, invitation=f'openreview.net/Support/Venue_Request/Conference_Review_Workflow{request.number}/-/Comment', count=1)

        messages = openreview_client.get_messages(subject='Your venue, VenueEmail 2025, is available in OpenReview')
        assert len(messages) == 1
        assert messages[0]['content']['to'] == 'programchair@venueemail.cc'

        helpers.await_queue_edit(openreview_client, 'VenueEmail.cc/2025/Conference/-/Withdrawal-0-1', count=1)
        helpers.await_queue_edit(openreview_client, 'VenueEmail.cc/2025/Conference/-/Desk_Rejection-0-1', count=1)
        helpers.await_queue_edit(openreview_client, 'VenueEmail.cc/2025/Conference/Reviewers/-/Submission_Group-0-1', count=1)
        helpers.await_queue_edit(openreview_client, 'VenueEmail.cc/2025/Conference/-/Submission_Change_Before_Bidding-0-1', count=1)

        venue_group = openreview.tools.get_group(openreview_client, 'VenueEmail.cc/2025/Conference')
        assert venue_group and venue_group.content['reviewers_recruitment_id']['value'] == 'VenueEmail.cc/2025/Conference/Reviewers/-/Recruitment_Response'
        assert openreview_client.get_group('VenueEmail.cc/2025/Conference/Reviewers/Invited')
        assert openreview_client.get_group('VenueEmail.cc/2025/Conference/Reviewers/Declined')

        request_note = openreview_client.get_note(request.id)
        assert request_note.domain == 'openreview.net/Support'

        review_notification_inv = openreview_client.get_invitation('VenueEmail.cc/2025/Conference/-/Author_Reviews_Notification')
        assert review_notification_inv.message['replyTo']['param']['regex'] == r'~.*|([a-z0-9_\-\.]{2,}@[a-z0-9_\-\.]{2,}\.[a-z]{2,},){0,}([a-z0-9_\-\.]{2,}@[a-z0-9_\-\.]{2,}\.[a-z]{2,})'

        decision_notification_inv = openreview_client.get_invitation('VenueEmail.cc/2025/Conference/-/Author_Decision_Notification')
        assert decision_notification_inv.message['replyTo']['param']['regex'] == r'~.*|([a-z0-9_\-\.]{2,}@[a-z0-9_\-\.]{2,}\.[a-z]{2,},){0,}([a-z0-9_\-\.]{2,}@[a-z0-9_\-\.]{2,}\.[a-z]{2,})'

    def test_change_venue_email(self, openreview_client, helpers):

        pc_client = openreview.api.OpenReviewClient(username='programchair@venueemail.cc', password=helpers.strong_password)

        venue_group = openreview.tools.get_group(openreview_client, 'VenueEmail.cc/2025/Conference')
        assert venue_group.content['contact']['value'] == 'venueemail2025.programchairs@gmail.com'

        # PCs update the venue contact email using Venue_Information invitation
        edit = pc_client.post_group_edit(
            invitation='VenueEmail.cc/2025/Conference/-/Venue_Information',
            signatures=['VenueEmail.cc/2025/Conference'],
            content={
                'title': { 'value': venue_group.content['title']['value'] },
                'subtitle': { 'value': venue_group.content['subtitle']['value'] },
                'website': { 'value': venue_group.content['website']['value'] },
                'location': { 'value': venue_group.content['location']['value'] },
                'start_date': { 'value': venue_group.content['start_date']['value'] },
                'contact': { 'value': 'new-contact@venueemail.cc' }
            }
        )

        # Verify the venue group contact was updated
        venue_group = openreview.tools.get_group(openreview_client, 'VenueEmail.cc/2025/Conference')
        assert venue_group.content['contact']['value'] == 'new-contact@venueemail.cc'

        review_notification_inv = openreview_client.get_invitation('VenueEmail.cc/2025/Conference/-/Author_Reviews_Notification')
        assert review_notification_inv.message['replyTo']['param']['regex'] == r'~.*|([a-z0-9_\-\.]{2,}@[a-z0-9_\-\.]{2,}\.[a-z]{2,},){0,}([a-z0-9_\-\.]{2,}@[a-z0-9_\-\.]{2,}\.[a-z]{2,})'

        decision_notification_inv = openreview_client.get_invitation('VenueEmail.cc/2025/Conference/-/Author_Decision_Notification')
        assert decision_notification_inv.message['replyTo']['param']['regex'] == r'~.*|([a-z0-9_\-\.]{2,}@[a-z0-9_\-\.]{2,}\.[a-z]{2,},){0,}([a-z0-9_\-\.]{2,}@[a-z0-9_\-\.]{2,}\.[a-z]{2,})'

    def test_recruitment_invitations(self, openreview_client, helpers):

        recruitment_request_inv = openreview_client.get_invitation('VenueEmail.cc/2025/Conference/Reviewers/-/Recruitment_Request')
        assert recruitment_request_inv.edit['content']['invite_message_body_template']['value']['param']['default'] == '''Dear {{fullname}},

You have been nominated by the program chair committee of VenueEmail 2025 to serve as Reviewer. As a respected researcher in the area, we hope you will accept and help us make VenueEmail 2025 a success.

You are also welcome to submit papers, so please also consider submitting to VenueEmail 2025.

We will be using OpenReview.net with the intention of have an engaging reviewing process inclusive of the whole community.

To respond the invitation, please click on the following link:

{{invitation_url}}

Please answer within 10 days.

If you accept, please make sure that your OpenReview account is updated and lists all the emails you are using.  Visit http://openreview.net/profile after logging in.

If you have any questions, please contact {{venue_email}}.

Cheers!

Program Chairs'''

        # test recruitment emails are sent with correct replyto email
        pc_client = openreview.api.OpenReviewClient(username='programchair@venueemail.cc', password=helpers.strong_password)

        edit = pc_client.post_group_edit(
            invitation='VenueEmail.cc/2025/Conference/Reviewers/-/Recruitment_Request',
            content={
                'invitee_details': { 'value': 'reviewer_one@venueemail.cc, ReviewerOne VenueEmail\nreviewer_two@venueemail.cc, ReviewerTwo VenueEmail' },
                'invite_message_subject_template': { 'value': '[VenueEmail 2025] Invitation to serve as Reviewer' },
                'invite_message_body_template': { 'value': 'Dear {{fullname}},\n\nYou have been nominated by the program chair committee of VenueEmail 2025 to serve as Reviewer.\n\nTo respond the invitation, please click on the following link:\n\n{{invitation_url}}\n\nIf you have any questions, please contact {{venue_email}}.\n\nCheers!\nProgram Chairs' },
            },
            group=openreview.api.Group()
        )
        helpers.await_queue_edit(openreview_client, edit_id=edit['id'])
        helpers.await_queue_edit(openreview_client, edit_id=edit['id'], process_index=1)

        messages = openreview_client.get_messages(to='reviewer_one@venueemail.cc', subject='[VenueEmail 2025] Invitation to serve as Reviewer')
        assert len(messages) == 1
        assert 'new-contact@venueemail.cc' in messages[0]['content']['text']
        assert messages[0]['content']['replyTo'] == 'new-contact@venueemail.cc'

        messages = openreview_client.get_messages(to='reviewer_two@venueemail.cc', subject='[VenueEmail 2025] Invitation to serve as Reviewer')
        assert len(messages) == 1
        assert 'new-contact@venueemail.cc' in messages[0]['content']['text']
        assert messages[0]['content']['replyTo'] == 'new-contact@venueemail.cc'

        # check reminder email is sent with correct replyto email
        messages = openreview_client.get_messages(to='reviewer_one@venueemail.cc', subject='[Reminder][VenueEmail 2025] Invitation to serve as Reviewer')
        assert len(messages) == 1
        assert 'new-contact@venueemail.cc' in messages[0]['content']['text']
        assert messages[0]['content']['replyTo'] == 'new-contact@venueemail.cc'

        messages = openreview_client.get_messages(to='reviewer_two@venueemail.cc', subject='[Reminder][VenueEmail 2025] Invitation to serve as Reviewer')
        assert len(messages) == 1
        assert 'new-contact@venueemail.cc' in messages[0]['content']['text']
        assert messages[0]['content']['replyTo'] == 'new-contact@venueemail.cc'

    def test_check_message_invitations(self, openreview_client, helpers):

        authors_message_inv = openreview_client.get_invitation('VenueEmail.cc/2025/Conference/Authors/-/Message')
        assert authors_message_inv.message['replyTo']['param']['regex'] == r'~.*|([a-z0-9_\-\.]{2,}@[a-z0-9_\-\.]{2,}\.[a-z]{2,},){0,}([a-z0-9_\-\.]{2,}@[a-z0-9_\-\.]{2,}\.[a-z]{2,})'

        authors_accepted_message_inv = openreview_client.get_invitation('VenueEmail.cc/2025/Conference/Authors/Accepted/-/Message')
        assert authors_accepted_message_inv.message['replyTo']['param']['regex'] ==r'~.*|([a-z0-9_\-\.]{2,}@[a-z0-9_\-\.]{2,}\.[a-z]{2,},){0,}([a-z0-9_\-\.]{2,}@[a-z0-9_\-\.]{2,}\.[a-z]{2,})'

        reviewers_message_inv = openreview_client.get_invitation('VenueEmail.cc/2025/Conference/Reviewers/-/Message')
        assert reviewers_message_inv.message['replyTo']['param']['regex'] == r'~.*|([a-z0-9_\-\.]{2,}@[a-z0-9_\-\.]{2,}\.[a-z]{2,},){0,}([a-z0-9_\-\.]{2,}@[a-z0-9_\-\.]{2,}\.[a-z]{2,})'

        reviewers_invited_message_inv = openreview_client.get_invitation('VenueEmail.cc/2025/Conference/Reviewers/Invited/-/Message')
        assert reviewers_invited_message_inv.message['replyTo']['param']['regex'] == r'~.*|([a-z0-9_\-\.]{2,}@[a-z0-9_\-\.]{2,}\.[a-z]{2,},){0,}([a-z0-9_\-\.]{2,}@[a-z0-9_\-\.]{2,}\.[a-z]{2,})'

        venue_message_inv = openreview_client.get_invitation('VenueEmail.cc/2025/Conference/-/Message')
        assert venue_message_inv.message['replyTo']['param']['regex'] == r'~.*|([a-z0-9_\-\.]{2,}@[a-z0-9_\-\.]{2,}\.[a-z]{2,},){0,}([a-z0-9_\-\.]{2,}@[a-z0-9_\-\.]{2,}\.[a-z]{2,})'