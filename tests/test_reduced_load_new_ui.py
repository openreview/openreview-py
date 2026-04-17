import re
import pytest
import datetime
import openreview
from openreview.api import Note
from selenium.webdriver.common.by import By
from openreview.api import OpenReviewClient


class TestReducedLoadNewUI():

    def test_setup(self, openreview_client, helpers):
        super_id = 'openreview.net'
        support_group_id = super_id + '/Support'

        helpers.create_user('pc_rl@mail.cc', 'ProgramChair', 'RL')
        helpers.create_user('reviewer_rl@mail.cc', 'Reviewer', 'RL')

        pc_client = openreview.api.OpenReviewClient(username='pc_rl@mail.cc', password=helpers.strong_password)

        now = datetime.datetime.now()
        due_date = now + datetime.timedelta(days=2)

        request = pc_client.post_note_edit(
            invitation='openreview.net/Support/Venue_Request/-/Conference_Review_Workflow',
            signatures=['~ProgramChair_RL1'],
            note=openreview.api.Note(
                content={
                    'official_venue_name': { 'value': 'The RL Conference' },
                    'abbreviated_venue_name': { 'value': 'RL 2025' },
                    'venue_website_url': { 'value': 'https://rl.cc/Conferences/2025' },
                    'location': { 'value': 'Amherst, Massachusetts' },
                    'venue_start_date': { 'value': openreview.tools.datetime_millis(now + datetime.timedelta(weeks=52)) },
                    'program_chair_emails': { 'value': ['pc_rl@mail.cc'] },
                    'contact_email': { 'value': 'pc_rl@mail.cc' },
                    'submission_start_date': { 'value': openreview.tools.datetime_millis(now) },
                    'submission_deadline': { 'value': openreview.tools.datetime_millis(due_date) },
                    'reviewer_role_name': { 'value': 'Program_Committee' },
                    'area_chair_role_name': { 'value': 'Area_Chairs' },
                    'colocated': { 'value': 'Independent' },
                    'previous_venue': { 'value': 'RL.cc/2024/Conference' },
                    'expected_submissions': { 'value': 100 },
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

        request = openreview_client.get_note(request['note']['id'])

        # Deploy the venue
        edit = openreview_client.post_note_edit(
            invitation='openreview.net/Support/Venue_Request/Conference_Review_Workflow/-/Deployment',
            signatures=[support_group_id],
            note=openreview.api.Note(
                id=request.id,
                content={
                    'venue_id': { 'value': 'RL.cc/2025/Conference' }
                }
            ))

        helpers.await_queue_edit(openreview_client, edit_id=edit['id'])
        helpers.await_queue_edit(openreview_client, invitation=f'openreview.net/Support/Venue_Request/Conference_Review_Workflow{request.number}/-/Comment', count=1)
        helpers.await_queue_edit(openreview_client, 'RL.cc/2025/Conference/-/Withdrawal-0-1', count=1)
        helpers.await_queue_edit(openreview_client, 'RL.cc/2025/Conference/-/Desk_Rejection-0-1', count=1)
        helpers.await_queue_edit(openreview_client, 'RL.cc/2025/Conference/-/Submission_Change_Before_Bidding-0-1', count=1)

        messages = openreview_client.get_messages(subject='Your venue, RL 2025, is available in OpenReview')
        assert len(messages) == 1
        assert messages[0]['content']['to'] == 'pc_rl@mail.cc'

        assert openreview_client.get_group('RL.cc/2025/Conference/Program_Committee')
        assert openreview_client.get_invitation('RL.cc/2025/Conference/Program_Committee/-/Recruitment_Request')
        assert openreview_client.get_invitation('RL.cc/2025/Conference/Program_Committee/-/Recruitment_Response')
        assert openreview_client.get_invitation('RL.cc/2025/Conference/Program_Committee/-/Recruitment_Response/Reduced_Load')

    def test_recruit_reviewer_with_reduced_load(self, openreview_client, helpers, selenium, request_page):

        pc_client = openreview.api.OpenReviewClient(username='pc_rl@mail.cc', password=helpers.strong_password)

        # Configure reduced load options - allow reviewers to accept the invitation with a reduced load
        pc_client.post_invitation_edit(
            invitations='RL.cc/2025/Conference/Program_Committee/-/Recruitment_Response/Reduced_Load',
            signatures=['RL.cc/2025/Conference'],
            content={
                'reduced_load_options': { 'value': ['1', '2', '3'] },
                'allow_accept_with_reduced_load': { 'value': True }
            },
            invitation=openreview.api.Invitation()
        )

        # Verify the invitation was updated
        recruitment_inv = openreview_client.get_invitation('RL.cc/2025/Conference/Program_Committee/-/Recruitment_Response')
        assert recruitment_inv.content['allow_accept_with_reduced_load']['value'] == True
        assert recruitment_inv.edit['note']['content']['reduced_load']['value']['param']['enum'] == ['1', '2', '3']

        # Recruit one reviewer
        edit = openreview_client.post_group_edit(
            invitation='RL.cc/2025/Conference/Program_Committee/-/Recruitment_Request',
            content={
                'invitee_details': { 'value': 'reviewer_rl@mail.cc, Reviewer RL' },
                'invite_message_subject_template': { 'value': '[RL 2025] Invitation to serve as Reviewer' },
                'invite_message_body_template': { 'value': 'Dear Reviewer {{fullname}},\n\nYou are invited to serve as a reviewer for RL 2025.\n\nPlease accept or decline using the link below:\n\n{{invitation_url}}\n\nBest regards,\nRL 2025 Program Chairs' },
            },
            group=openreview.api.Group()
        )
        helpers.await_queue_edit(openreview_client, edit_id=edit['id'])
        helpers.await_queue_edit(openreview_client, edit_id=edit['id'], process_index=1)

        invited_group = openreview_client.get_group('RL.cc/2025/Conference/Program_Committee/Invited')
        assert '~Reviewer_RL1' in invited_group.members
        assert openreview_client.get_group('RL.cc/2025/Conference/Program_Committee').members == []

        # Get invitation URL from email
        messages = openreview_client.get_messages(to='reviewer_rl@mail.cc', subject='[RL 2025] Invitation to serve as Reviewer')
        assert len(messages) == 1

        text = messages[0]['content']['text']
        invitation_url = re.search('https://.*\n', text).group(0).replace('https://openreview.net', 'http://localhost:3030').replace('&amp;', '&')[:-1]

        # Accept the invitation with a reduced load using selenium.
        # With allow_accept_with_reduced_load=True the UI shows 3 buttons:
        # [Accept, Accept with reduced load, Decline]. quota=2 triggers the
        # "Accept with reduced load" flow and selects the first dropdown option ('1').
        helpers.respond_invitation(selenium, request_page, invitation_url, accept=True, quota=2)

        edits = openreview_client.get_note_edits(invitation='RL.cc/2025/Conference/Program_Committee/-/Recruitment_Response', sort='tcdate:desc')
        assert len(edits) >= 1
        helpers.await_queue_edit(openreview_client, edit_id=edits[0].id)

        assert edits[0].note.content['response']['value'] == 'Yes'
        assert edits[0].note.content['reduced_load']['value'] == '1'  # first option selected by selenium

        assert '~Reviewer_RL1' in openreview_client.get_group('RL.cc/2025/Conference/Program_Committee').members

        messages = openreview_client.get_messages(to='reviewer_rl@mail.cc', subject='[RL 2025] Program Committee Invitation accepted with reduced load')
        assert len(messages) == 1

        # Check reviewer console shows the reduced load information
        reviewer_client = openreview.api.OpenReviewClient(username='reviewer_rl@mail.cc', password=helpers.strong_password)

        request_page(selenium, 'http://localhost:3030/group?id=RL.cc/2025/Conference/Program_Committee', reviewer_client, wait_for_element='header')
        header = selenium.find_element(By.ID, 'header')
        assert 'You have agreed to review up to 1 submission' in header.text

    def test_post_submission(self, openreview_client, helpers):

        helpers.create_user('author_rl@mail.cc', 'Author', 'RL')
        author_client = openreview.api.OpenReviewClient(username='author_rl@mail.cc', password=helpers.strong_password)

        note = openreview.api.Note(
            license='CC BY 4.0',
            content={
                'title': { 'value': 'Test Paper for RL Conference' },
                'abstract': { 'value': 'This is a test abstract for the RL Conference submission.' },
                'authorids': { 'value': ['~Author_RL1'] },
                'authors': { 'value': ['Author RL'] },
                'pdf': { 'value': '/pdf/' + 'p' * 40 + '.pdf' },
                'keywords': { 'value': ['Reinforcement Learning', 'Artificial Intelligence'] },
                'email_sharing': { 'value': 'We authorize the sharing of all author emails with Program Chairs.' },
                'data_release': { 'value': 'We authorize the release of our submission and author names to the public in the event of acceptance.' },                
            }
        )

        author_client.post_note_edit(
            invitation='RL.cc/2025/Conference/-/Submission',
            signatures=['~Author_RL1'],
            note=note
        )

        helpers.await_queue_edit(openreview_client, invitation='RL.cc/2025/Conference/-/Submission', count=1)

        submissions = openreview_client.get_notes(invitation='RL.cc/2025/Conference/-/Submission', sort='number:asc')
        assert len(submissions) == 1

        # Expire the submission deadline so matching setup can proceed
        pc_client = openreview.api.OpenReviewClient(username='pc_rl@mail.cc', password=helpers.strong_password)
        now = datetime.datetime.now()

        edit = pc_client.post_invitation_edit(
            invitations='RL.cc/2025/Conference/-/Submission/Dates',
            content={
                'activation_date': { 'value': openreview.tools.datetime_millis(now - datetime.timedelta(days=1)) },
                'due_date': { 'value': openreview.tools.datetime_millis(now - datetime.timedelta(minutes=31)) }
            }
        )
        helpers.await_queue_edit(openreview_client, edit_id=edit['id'])

        # Activate post submission process
        pc_client.post_invitation_edit(
            invitations='RL.cc/2025/Conference/-/Submission_Change_Before_Bidding/Dates',
            content={
                'activation_date': { 'value': openreview.tools.datetime_millis(now - datetime.timedelta(minutes=30)) }
            }
        )
        helpers.await_queue_edit(openreview_client, edit_id='RL.cc/2025/Conference/-/Submission_Change_Before_Bidding-0-1', count=2)

    def test_setup_matching(self, openreview_client, helpers):

        pc_client = openreview.api.OpenReviewClient(username='pc_rl@mail.cc', password=helpers.strong_password)

        # Verify conflict and affinity score invitations exist
        assert openreview_client.get_invitation('RL.cc/2025/Conference/Program_Committee/-/Conflict')
        assert openreview_client.get_invitation('RL.cc/2025/Conference/Program_Committee/-/Conflict/Dates')
        assert openreview_client.get_invitation('RL.cc/2025/Conference/Program_Committee/-/Conflict/Policy')

        now = datetime.datetime.now()

        # Set conflict policy
        pc_client.post_invitation_edit(
            invitations='RL.cc/2025/Conference/Program_Committee/-/Conflict/Policy',
            content={
                'conflict_policy': { 'value': 'NeurIPS' },
                'conflict_n_years': { 'value': 3 }
            }
        )
        helpers.await_queue_edit(openreview_client, invitation='RL.cc/2025/Conference/Program_Committee/-/Conflict/Policy')
        helpers.await_queue_edit(openreview_client, 'RL.cc/2025/Conference/Program_Committee/-/Conflict-0-1', count=2)

        conflicts_inv = pc_client.get_invitation('RL.cc/2025/Conference/Program_Committee/-/Conflict')
        assert conflicts_inv.content['conflict_policy']['value'] == 'NeurIPS'
        assert conflicts_inv.content['conflict_n_years']['value'] == 3

        pc_client.post_invitation_edit(
            invitations='RL.cc/2025/Conference/Program_Committee/-/Conflict/Dates',
            content={
                'activation_date': { 'value': openreview.tools.datetime_millis(datetime.datetime.now()) }
            }
        )
        helpers.await_queue_edit(openreview_client, 'RL.cc/2025/Conference/Program_Committee/-/Conflict-0-1', count=3)                

        # Verify Custom_Max_Papers invitation exists
        assert openreview_client.get_invitation('RL.cc/2025/Conference/Program_Committee/-/Custom_Max_Papers')

        # Check Custom_Max_Papers edge for the reviewer who accepted with reduced_load=1
        custom_max_papers_edges = openreview_client.get_edges(
            invitation='RL.cc/2025/Conference/Program_Committee/-/Custom_Max_Papers',
            tail='~Reviewer_RL1'
        )
        assert len(custom_max_papers_edges) == 1
        assert custom_max_papers_edges[0].weight == 1
