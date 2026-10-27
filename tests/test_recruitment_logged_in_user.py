import re
import datetime
import openreview
from openreview.api import Note


class TestRecruitmentLoggedInUser():
    '''Recruitment_Response allows guest posting and takes the invitee from the edit signature.
    A logged-in user responds signed with their tilde id, so the pre-process must reject users
    that are not in the invited group, e.g. a PC that opens a link sent to another email.'''

    venue_id = 'RLIP.cc/2026/Conference'
    recruitment_response_id = 'RLIP.cc/2026/Conference/Reviewers/-/Recruitment_Response'
    recruitment_title = '[RLIP 2026] Invitation to serve as Reviewer'
    pc_email = 'pc_rlip@mail.cc'
    pc_id = '~ProgramChair_RLIP1'

    def get_recruitment_url(self, openreview_client, email):
        messages = openreview_client.get_messages(to=email, subject=self.recruitment_title)
        assert len(messages) == 1
        text = messages[0]['content']['text']
        return re.search('https://.*\n', text).group(0).replace('https://openreview.net', 'http://localhost:3030').replace('&amp;', '&')[:-1]

    def test_setup(self, openreview_client, helpers):

        helpers.create_user(self.pc_email, 'ProgramChair', 'RLIP')
        pc_client = helpers.get_user(self.pc_email)

        now = datetime.datetime.now()
        due_date = now + datetime.timedelta(days=2)

        request = pc_client.post_note_edit(
            invitation='openreview.net/Support/Venue_Request/-/Conference_Review_Workflow',
            signatures=[self.pc_id],
            note=Note(
                content={
                    'official_venue_name': { 'value': 'The RLIP Conference' },
                    'abbreviated_venue_name': { 'value': 'RLIP 2026' },
                    'venue_website_url': { 'value': 'https://rlip.cc/Conferences/2026' },
                    'location': { 'value': 'Amherst, Massachusetts' },
                    'venue_start_date': { 'value': openreview.tools.datetime_millis(now + datetime.timedelta(weeks=52)) },
                    'program_chair_emails': { 'value': [self.pc_email] },
                    'contact_email': { 'value': self.pc_email },
                    'submission_start_date': { 'value': openreview.tools.datetime_millis(now) },
                    'submission_deadline': { 'value': openreview.tools.datetime_millis(due_date) },
                    'reviewer_groups_names': { 'value': ['Reviewers'] },
                    'colocated': { 'value': 'Independent' },
                    'previous_venue': { 'value': 'RLIP.cc/2025/Conference' },
                    'expected_submissions': { 'value': 100 },
                    'how_did_you_hear_about_us': { 'value': 'We have used OpenReview for our previous conferences.' },
                    'venue_organizer_agreement': {
                        'value': [
                            'OpenReview natively supports a wide variety of reviewing workflow configurations. However, if we want significant reviewing process customizations or experiments, we will detail these requests to the OpenReview staff at least three months in advance.',
                            'We will ask authors and reviewers to create an OpenReview Profile well in advance of the paper submission deadlines.',
                            'When assembling our group of reviewers, we will only include email addresses or OpenReview Profile IDs of people we know to have authored publications relevant to our venue.  (We will not solicit new reviewers using an open web form, because unfortunately some malicious actors sometimes try to create "fake ids" aiming to be assigned to review their own paper submissions.)',
                            'We acknowledge that, if our venue\'s reviewing workflow is non-standard, or if our venue is expecting more than a few hundred submissions for any one deadline, we should designate our own Workflow Chair, who will read the OpenReview documentation and manage our workflow configurations throughout the reviewing process.',
                            'We acknowledge that OpenReview staff work Monday-Friday during standard business hours US Eastern time, and we cannot expect support responses outside those times.  For this reason, we recommend setting submission and reviewing deadlines Monday through Thursday.',
                            'We will treat the OpenReview staff with kindness and consideration.',
                            'We acknowledge that authors and reviewers will be required to share their preferred email.',
                            'We acknowledge that certain metadata for accepted papers, specifically the paper title, abstract and author list, will be publicly released on OpenReview.',
                        ]
                    }
                }
            ))

        helpers.await_queue_edit(openreview_client, edit_id=request['id'])

        request = openreview_client.get_note(request['note']['id'])

        edit = openreview_client.post_note_edit(
            invitation='openreview.net/Support/Venue_Request/Conference_Review_Workflow/-/Deployment',
            signatures=['openreview.net/Support'],
            note=Note(
                id=request.id,
                content={
                    'venue_id': { 'value': self.venue_id }
                }
            ))

        helpers.await_queue_edit(openreview_client, edit_id=edit['id'])
        helpers.await_queue_edit(openreview_client, invitation=f'openreview.net/Support/Venue_Request/Conference_Review_Workflow{request.number}/-/Comment', count=1)
        helpers.await_queue_edit(openreview_client, f'{self.venue_id}/-/Withdrawal-0-1', count=1)
        helpers.await_queue_edit(openreview_client, f'{self.venue_id}/-/Desk_Rejection-0-1', count=1)
        helpers.await_queue_edit(openreview_client, f'{self.venue_id}/-/Submission_Change_Before_Bidding-0-1', count=1)

        assert self.pc_email in openreview_client.get_group(f'{self.venue_id}/Program_Chairs').members
        assert openreview_client.get_invitation(self.recruitment_response_id).guestPosting == True

        edit = pc_client.post_group_edit(
            invitation=f'{self.venue_id}/Reviewers/-/Recruitment_Request',
            content={
                'invitee_details': { 'value': 'rlip_guest@mail.cc, Guest Invitee\nrlip_other@mail.cc, Other Invitee\nrlip_invitee@mail.cc, Logged In Invitee' },
                'invite_message_subject_template': { 'value': self.recruitment_title },
                'invite_message_body_template': { 'value': 'Dear {{fullname}},\n\nYou are invited to serve as a reviewer for RLIP 2026.\n\nPlease accept or decline using the link below:\n\n{{invitation_url}}\n\nBest regards,\nRLIP 2026 Program Chairs' },
            },
            group=openreview.api.Group()
        )
        helpers.await_queue_edit(openreview_client, edit_id=edit['id'])
        helpers.await_queue_edit(openreview_client, edit_id=edit['id'], process_index=1)

        assert sorted(openreview_client.get_group(f'{self.venue_id}/Reviewers/Invited').members) == ['rlip_guest@mail.cc', 'rlip_invitee@mail.cc', 'rlip_other@mail.cc']
        assert openreview_client.get_group(f'{self.venue_id}/Reviewers').members == []

    def test_guest_accepts(self, openreview_client, helpers, selenium, request_page):

        url = self.get_recruitment_url(openreview_client, 'rlip_guest@mail.cc')
        helpers.respond_invitation(selenium, request_page, url, accept=True)

        edits = openreview_client.get_note_edits(invitation=self.recruitment_response_id, sort='tcdate:desc')
        assert len(edits) == 1
        assert edits[0].signatures == ['rlip_guest@mail.cc']
        helpers.await_queue_edit(openreview_client, edit_id=edits[0].id)

        assert openreview_client.get_group(f'{self.venue_id}/Reviewers').members == ['rlip_guest@mail.cc']

    def test_logged_in_user_not_invited_can_not_respond(self, openreview_client, helpers, selenium, request_page):

        # the PC, whose profile does not have rlip_other@mail.cc, opens the link while logged in
        url = self.get_recruitment_url(openreview_client, 'rlip_other@mail.cc')
        pc_client = helpers.get_user(self.pc_email)
        helpers.respond_invitation(selenium, request_page, url, accept=True, client=pc_client, expected_error_message='Error: User not in invited group, please accept the invitation using the email address you were invited with')

        assert len(openreview_client.get_note_edits(invitation=self.recruitment_response_id)) == 1
        assert openreview_client.get_group(f'{self.venue_id}/Reviewers').members == ['rlip_guest@mail.cc']
        assert openreview_client.get_group(f'{self.venue_id}/Reviewers/Declined').members == []

    def test_logged_in_invitee_accepts(self, openreview_client, helpers, selenium, request_page):

        # the invitee creates a profile with the invited email and responds while logged in
        helpers.create_user('rlip_invitee@mail.cc', 'Invitee', 'RLIP')
        invitee_client = helpers.get_user('rlip_invitee@mail.cc')

        url = self.get_recruitment_url(openreview_client, 'rlip_invitee@mail.cc')
        helpers.respond_invitation(selenium, request_page, url, accept=True, client=invitee_client)

        edits = openreview_client.get_note_edits(invitation=self.recruitment_response_id, sort='tcdate:desc')
        assert len(edits) == 2
        assert edits[0].signatures == ['~Invitee_RLIP1']
        helpers.await_queue_edit(openreview_client, edit_id=edits[0].id)

        assert sorted(openreview_client.get_group(f'{self.venue_id}/Reviewers').members) == ['rlip_guest@mail.cc', '~Invitee_RLIP1']

        messages = [m for m in openreview_client.get_messages(to='rlip_invitee@mail.cc') if m['content']['subject'].endswith('Invitation accepted')]
        assert len(messages) == 1
