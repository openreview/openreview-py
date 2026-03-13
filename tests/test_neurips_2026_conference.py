from __future__ import absolute_import, division, print_function, unicode_literals
import openreview
import pytest
import datetime
import time
from selenium.webdriver.common.by import By


class TestNeurIPS2026Conference():

    def test_create_conference(self, client, openreview_client, helpers):

        now = datetime.datetime.now()
        due_date = now + datetime.timedelta(days=3)
        first_date = now + datetime.timedelta(days=1)

        helpers.create_user('pc2026@neurips.cc', 'Program', 'NeurIPSLLMChair')
        pc_client = openreview.Client(username='pc2026@neurips.cc', password=helpers.strong_password)

        helpers.create_user('llm_reviewer1@neurips.cc', 'LLM', 'ReviewerFirst')
        helpers.create_user('llm_reviewer2@neurips.cc', 'LLM', 'ReviewerSecond')
        helpers.create_user('llm_reviewer3@neurips.cc', 'LLM', 'ReviewerThird')

        request_form_note = pc_client.post_note(openreview.Note(
            invitation='openreview.net/Support/-/Request_Form',
            signatures=['~Program_NeurIPSLLMChair1'],
            readers=[
                'openreview.net/Support',
                '~Program_NeurIPSLLMChair1'
            ],
            writers=[],
            content={
                'title': 'Conference on Neural Information Processing Systems',
                'Official Venue Name': 'Conference on Neural Information Processing Systems',
                'Abbreviated Venue Name': 'NeurIPS 2026',
                'Official Website URL': 'https://neurips.cc',
                'program_chair_emails': ['pc2026@neurips.cc'],
                'contact_email': 'pc2026@neurips.cc',
                'publication_chairs': 'No, our venue does not have Publication Chairs',
                'Area Chairs (Metareviewers)': 'No, our venue does not have Area Chairs',
                'senior_area_chairs': 'No, our venue does not have Senior Area Chairs',
                'Venue Start Date': '2026/12/01',
                'Submission Deadline': due_date.strftime('%Y/%m/%d'),
                'abstract_registration_deadline': first_date.strftime('%Y/%m/%d'),
                'Location': 'Virtual',
                'submission_reviewer_assignment': 'Manual',
                'Author and Reviewer Anonymity': 'Double-blind',
                'reviewer_identity': ['Program Chairs', 'Assigned Reviewers'],
                'Open Reviewing Policy': 'Submissions and reviews should both be private.',
                'submission_readers': 'Program chairs and paper authors only',
                'How did you hear about us?': 'ML conferences',
                'Expected Submissions': '100',
                'api_version': '2',
                'submission_license': ['CC BY 4.0'],
                'venue_organizer_agreement': [
                    'OpenReview natively supports a wide variety of reviewing workflow configurations. However, if we want significant reviewing process customizations or experiments, we will detail these requests to the OpenReview staff at least three months in advance.',
                    'We will ask authors and reviewers to create an OpenReview Profile at least two weeks in advance of the paper submission deadlines.',
                    'When assembling our group of reviewers and meta-reviewers, we will only include email addresses or OpenReview Profile IDs of people we know to have authored publications relevant to our venue.  (We will not solicit new reviewers using an open web form, because unfortunately some malicious actors sometimes try to create "fake ids" aiming to be assigned to review their own paper submissions.)',
                    'We acknowledge that, if our venue\'s reviewing workflow is non-standard, or if our venue is expecting more than a few hundred submissions for any one deadline, we should designate our own Workflow Chair, who will read the OpenReview documentation and manage our workflow configurations throughout the reviewing process.',
                    'We acknowledge that OpenReview staff work Monday-Friday during standard business hours US Eastern time, and we cannot expect support responses outside those times.  For this reason, we recommend setting submission and reviewing deadlines Monday through Thursday.',
                    'We will treat the OpenReview staff with kindness and consideration.'
                ]
            }
        ))

        helpers.await_queue()

        # Post a deploy note
        client.post_note(openreview.Note(
            content={'venue_id': 'NeurIPS.cc/2026/Conference'},
            forum=request_form_note.forum,
            invitation='openreview.net/Support/-/Request{}/Deploy'.format(request_form_note.number),
            readers=['openreview.net/Support'],
            referent=request_form_note.forum,
            replyto=request_form_note.forum,
            signatures=['openreview.net/Support'],
            writers=['openreview.net/Support']
        ))

        helpers.await_queue()

        venue_group = openreview_client.get_group('NeurIPS.cc/2026/Conference')
        assert venue_group
        assert venue_group.host == 'NeurIPS.cc'
        reviewers_group = openreview_client.get_group('NeurIPS.cc/2026/Conference/Reviewers')
        assert reviewers_group
        assert openreview_client.get_group('NeurIPS.cc/2026/Conference/Authors')

        post_submission = openreview_client.get_invitation('NeurIPS.cc/2026/Conference/-/Post_Submission')
        assert 'authors' in post_submission.edit['note']['content']
        assert 'authorids' in post_submission.edit['note']['content']

        # Add reviewers to the Reviewers group
        openreview_client.add_members_to_group(
            'NeurIPS.cc/2026/Conference/Reviewers',
            ['~LLM_ReviewerFirst1', '~LLM_ReviewerSecond1', '~LLM_ReviewerThird1']
        )

        reviewers_group = openreview_client.get_group('NeurIPS.cc/2026/Conference/Reviewers')
        assert '~LLM_ReviewerFirst1' in reviewers_group.members
        assert '~LLM_ReviewerSecond1' in reviewers_group.members
        assert '~LLM_ReviewerThird1' in reviewers_group.members

    def test_submit_paper(self, test_client, helpers, openreview_client):

        test_client = openreview.api.OpenReviewClient(username='test@mail.com', password=helpers.strong_password)

        note = openreview.api.Note(
            content={
                'title': {'value': 'NeurIPS 2026 Test Paper'},
                'abstract': {'value': 'This is a test abstract for NeurIPS 2026.'},
                'authorids': {'value': ['test@mail.com']},
                'authors': {'value': ['SomeFirstName User']},
                'keywords': {'value': ['machine learning', 'deep learning']},
            }
        )

        note_edit = test_client.post_note_edit(
            invitation='NeurIPS.cc/2026/Conference/-/Submission',
            signatures=['~SomeFirstName_User1'],
            note=note
        )

        helpers.await_queue_edit(openreview_client, edit_id=note_edit['id'])

        submissions = openreview_client.get_notes(invitation='NeurIPS.cc/2026/Conference/-/Submission')
        assert len(submissions) == 1
        assert submissions[0].number == 1

    def test_post_submission(self, helpers, openreview_client, client):

        pc_client = openreview.Client(username='pc2026@neurips.cc', password=helpers.strong_password)
        request_form = pc_client.get_notes(invitation='openreview.net/Support/-/Request_Form')[0]

        now = datetime.datetime.now()

        # Close the submission by setting both deadlines to the past
        pc_client.post_note(openreview.Note(
            content={
                'title': 'Conference on Neural Information Processing Systems',
                'Official Venue Name': 'Conference on Neural Information Processing Systems',
                'Abbreviated Venue Name': 'NeurIPS 2026',
                'Official Website URL': 'https://neurips.cc',
                'program_chair_emails': ['pc2026@neurips.cc'],
                'contact_email': 'pc2026@neurips.cc',
                'publication_chairs': 'No, our venue does not have Publication Chairs',
                'Venue Start Date': '2026/12/01',
                'Submission Deadline': (now - datetime.timedelta(minutes=30)).strftime('%Y/%m/%d %H:%M'),
                'abstract_registration_deadline': (now - datetime.timedelta(hours=1)).strftime('%Y/%m/%d %H:%M'),
                'Location': 'Virtual',
                'submission_reviewer_assignment': 'Manual',
                'How did you hear about us?': 'ML conferences',
                'Expected Submissions': '100',
            },
            forum=request_form.forum,
            invitation=f'openreview.net/Support/-/Request{request_form.number}/Revision',
            readers=['NeurIPS.cc/2026/Conference/Program_Chairs', 'openreview.net/Support'],
            referent=request_form.forum,
            replyto=request_form.forum,
            signatures=['~Program_NeurIPSLLMChair1'],
            writers=[],
        ))

        helpers.await_queue()
        helpers.await_queue_edit(openreview_client, 'NeurIPS.cc/2026/Conference/-/Post_Submission-0-1', count=2)

        # Run the Post_Submission stage
        pc_client.post_note(openreview.Note(
            content={
                'force': 'Yes',
                'submission_readers': 'Assigned program committee (assigned reviewers, assigned area chairs, assigned senior area chairs if applicable)'
            },
            forum=request_form.id,
            invitation=f'openreview.net/Support/-/Request{request_form.number}/Post_Submission',
            readers=['NeurIPS.cc/2026/Conference/Program_Chairs', 'openreview.net/Support'],
            referent=request_form.id,
            replyto=request_form.id,
            signatures=['~Program_NeurIPSLLMChair1'],
            writers=[],
        ))

        helpers.await_queue()
        helpers.await_queue_edit(openreview_client, 'NeurIPS.cc/2026/Conference/-/Post_Submission-0-1', count=3)

        submissions = openreview_client.get_notes(content={'venueid': 'NeurIPS.cc/2026/Conference/Submission'})
        assert len(submissions) == 1
        assert 'NeurIPS.cc/2026/Conference/Submission1/Reviewers' in submissions[0].readers

    def test_assign_reviewers(self, helpers, openreview_client):

        openreview_client.add_members_to_group(
            'NeurIPS.cc/2026/Conference/Submission1/Reviewers',
            ['~LLM_ReviewerFirst1', '~LLM_ReviewerSecond1', '~LLM_ReviewerThird1']
        )

        reviewer_group = openreview_client.get_group('NeurIPS.cc/2026/Conference/Submission1/Reviewers')
        assert len(reviewer_group.members) == 3
        assert '~LLM_ReviewerFirst1' in reviewer_group.members
        assert '~LLM_ReviewerSecond1' in reviewer_group.members
        assert '~LLM_ReviewerThird1' in reviewer_group.members

    def test_llm_interaction_test(self, helpers, openreview_client, selenium, request_page):

        # Get anon group IDs for reviewer1 and reviewer2
        reviewer1_client = openreview.api.OpenReviewClient(
            username='llm_reviewer1@neurips.cc', password=helpers.strong_password
        )
        anon_groups_1 = reviewer1_client.get_groups(
            prefix='NeurIPS.cc/2026/Conference/Submission1/Reviewer_',
            signatory='~LLM_ReviewerFirst1'
        )
        assert anon_groups_1, 'No anon group found for reviewer1'
        anon_group_id_1 = anon_groups_1[0].id

        reviewer2_client = openreview.api.OpenReviewClient(
            username='llm_reviewer2@neurips.cc', password=helpers.strong_password
        )
        anon_groups_2 = reviewer2_client.get_groups(
            prefix='NeurIPS.cc/2026/Conference/Submission1/Reviewer_',
            signatory='~LLM_ReviewerSecond1'
        )
        assert anon_groups_2, 'No anon group found for reviewer2'
        anon_group_id_2 = anon_groups_2[0].id

        # Create the NeurIPS.cc/2026/Conference/LLM group
        openreview_client.post_group_edit(
            invitation='NeurIPS.cc/2026/Conference/-/Edit',
            signatures=['NeurIPS.cc/2026/Conference'],
            group=openreview.api.Group(
                id='NeurIPS.cc/2026/Conference/LLM',
                readers=['NeurIPS.cc/2026/Conference', 'NeurIPS.cc/2026/Conference/LLM'],
                writers=['NeurIPS.cc/2026/Conference'],
                signatures=['NeurIPS.cc/2026/Conference'],
                signatories=['NeurIPS.cc/2026/Conference'],
                members=[]
            )
        )

        llm_group = openreview_client.get_group('NeurIPS.cc/2026/Conference/LLM')
        assert llm_group
        assert llm_group.id == 'NeurIPS.cc/2026/Conference/LLM'

        # Create the NeurIPS.cc/2026/Conference/Submission1/LLM_Interactive_Reviewers group
        # with the anon IDs of reviewer1 and reviewer2 as members
        openreview_client.post_group_edit(
            invitation='NeurIPS.cc/2026/Conference/-/Edit',
            signatures=['NeurIPS.cc/2026/Conference'],
            group=openreview.api.Group(
                id='NeurIPS.cc/2026/Conference/Submission1/LLM_Interactive_Reviewers',
                readers=[
                    'NeurIPS.cc/2026/Conference',
                    'NeurIPS.cc/2026/Conference/LLM',
                    'NeurIPS.cc/2026/Conference/Submission1/LLM_Interactive_Reviewers'
                ],
                writers=['NeurIPS.cc/2026/Conference'],
                signatures=['NeurIPS.cc/2026/Conference'],
                members=[anon_group_id_1, anon_group_id_2]
            )
        )

        llm_interactive_reviewers_group = openreview_client.get_group(
            'NeurIPS.cc/2026/Conference/Submission1/LLM_Interactive_Reviewers'
        )
        assert llm_interactive_reviewers_group
        assert anon_group_id_1 in llm_interactive_reviewers_group.members
        assert anon_group_id_2 in llm_interactive_reviewers_group.members

        # Get the submission forum id
        submissions = openreview_client.get_notes(invitation='NeurIPS.cc/2026/Conference/-/Submission')
        assert len(submissions) == 1
        submission = submissions[0]

        # Create the super 'NeurIPS.cc/2026/Conference/-/LLM_Interaction' invitation
        # that creates a per-anon-group child invitation when instantiated
        openreview_client.post_invitation_edit(
            invitations='NeurIPS.cc/2026/Conference/-/Edit',
            readers=['NeurIPS.cc/2026/Conference'],
            writers=['NeurIPS.cc/2026/Conference'],
            signatures=['NeurIPS.cc/2026/Conference'],
            invitation=openreview.api.Invitation(
                id='NeurIPS.cc/2026/Conference/-/LLM_Interaction',
                invitees=['NeurIPS.cc/2026/Conference'],
                readers=['NeurIPS.cc/2026/Conference'],
                writers=['NeurIPS.cc/2026/Conference'],
                signatures=['NeurIPS.cc/2026/Conference'],
                edit={
                    'signatures': ['NeurIPS.cc/2026/Conference'],
                    'readers': ['NeurIPS.cc/2026/Conference'],
                    'writers': ['NeurIPS.cc/2026/Conference'],
                    'content': {
                        'note_id': {
                            'value': {
                                'param': {
                                    'type': 'string'
                                }
                            }
                        },
                        'note_number': {
                            'value': {
                                'param': {
                                    'type': 'integer'
                                }
                            }
                        },
                        'anon_group_id': {
                            'value': {
                                'param': {
                                    'type': 'string'
                                }
                            }
                        }
                    },
                    'invitation': {
                        'id': '${2/content/anon_group_id/value}/-/LLM_Interaction',
                        'process': '''def process(client, edit, invitation):

    domain = client.get_group(edit.domain)

    if edit.signatures[0] == domain.id + '/LLM' or edit.signatures[0] == domain.id:
        return

    ## post a reply
    replied_edit = client.post_note_edit(
        invitation=invitation.id,
        signatures=[domain.id + '/LLM'],
        note=openreview.api.Note(
            replyto=edit.note.id,
            content={
                'message': {
                    'value': 'Thinking...'
                }
            }
        )
    )
    import time

    time.sleep(5)

    replied_edit = client.get_note_edit(replied_edit['id'])

    replied_edit.note.content['message']['value'] = f'Preparing response...'
    replied_edit.note.id = None
    client.post_edit(replied_edit)

    time.sleep(5)

    replied_edit.note.content['message']['value'] = f'Response from LLM to message {edit.note.content["message"]["value"]}'
    replied_edit.note.id = None
    client.post_edit(replied_edit)


''',
                        'invitees': [
                            'NeurIPS.cc/2026/Conference/LLM',
                            '${3/content/anon_group_id/value}'
                        ],
                        'readers': [
                            'NeurIPS.cc/2026/Conference',
                            'NeurIPS.cc/2026/Conference/LLM',
                            '${3/content/anon_group_id/value}'
                        ],
                        'writers': ['NeurIPS.cc/2026/Conference'],
                        'signatures': ['NeurIPS.cc/2026/Conference'],
                        'edit': {
                            'signatures': {
                                'param': {
                                    'items': [
                                        {'value': '${7/content/anon_group_id/value}', 'optional': True},
                                        {'value': 'NeurIPS.cc/2026/Conference/LLM', 'optional': True}
                                    ]
                                }
                            },
                            'readers': [
                                'NeurIPS.cc/2026/Conference',
                                'NeurIPS.cc/2026/Conference/LLM',
                                '${4/content/anon_group_id/value}'
                            ],
                            'writers': ['NeurIPS.cc/2026/Conference'],
                            'note': {
                                'forum': '${4/content/note_id/value}',
                                'replyto': {
                                    'param': {
                                        'withForum': '${6/content/note_id/value}'
                                    }
                                },
                                'signatures': ['${3/signatures}'],
                                'readers': [
                                    'NeurIPS.cc/2026/Conference',
                                    'NeurIPS.cc/2026/Conference/LLM',
                                    '${5/content/anon_group_id/value}'
                                ],
                                'writers': ['NeurIPS.cc/2026/Conference'],
                                'content': {
                                    'message': {
                                        'order': 1,
                                        'description': 'Message',
                                        'value': {
                                            'param': {
                                                'type': 'string',
                                                'input': 'textarea'
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            )
        )

        # Verify the super invitation was created
        llm_super_invitation = openreview_client.get_invitation('NeurIPS.cc/2026/Conference/-/LLM_Interaction')
        assert llm_super_invitation

        # Instantiate the super invitation for anon_group_id_1
        openreview_client.post_invitation_edit(
            invitations='NeurIPS.cc/2026/Conference/-/LLM_Interaction',
            readers=['NeurIPS.cc/2026/Conference'],
            writers=['NeurIPS.cc/2026/Conference'],
            signatures=['NeurIPS.cc/2026/Conference'],
            content={
                'note_id': {'value': submission.id},
                'note_number': {'value': submission.number},
                'anon_group_id': {'value': anon_group_id_1}
            }
        )

        # Instantiate the super invitation for anon_group_id_2
        openreview_client.post_invitation_edit(
            invitations='NeurIPS.cc/2026/Conference/-/LLM_Interaction',
            readers=['NeurIPS.cc/2026/Conference'],
            writers=['NeurIPS.cc/2026/Conference'],
            signatures=['NeurIPS.cc/2026/Conference'],
            content={
                'note_id': {'value': submission.id},
                'note_number': {'value': submission.number},
                'anon_group_id': {'value': anon_group_id_2}
            }
        )

        # Verify both child invitations were created
        llm_invitation_1 = openreview_client.get_invitation(f'{anon_group_id_1}/-/LLM_Interaction')
        assert llm_invitation_1

        llm_invitation_2 = openreview_client.get_invitation(f'{anon_group_id_2}/-/LLM_Interaction')
        assert llm_invitation_2

        openreview_client.post_invitation_edit(
            invitations='NeurIPS.cc/2026/Conference/-/Edit',
            signatures = ['NeurIPS.cc/2026/Conference'],
            invitation = openreview.api.Invitation(
                id = 'NeurIPS.cc/2026/Conference/-/Submission',
                reply_forum_views = [
                    {
                        'id': 'discussion',
                        'label': 'Discussion',
                        'filter': '-invitations:NeurIPS.cc/2026/Conference/Submission${note.number}/Reviewer_.*/-/LLM_Interaction',
                        'nesting': 3,
                        'sort': 'date-desc',
                        'layout': 'default',
                        'live': True
                    },
                    {
                        'id': 'llm_interaction',
                        'label': 'LLM Interaction Chat',
                        'filter': 'invitations:NeurIPS.cc/2026/Conference/Submission${note.number}/Reviewer_.*/-/LLM_Interaction',
                        'nesting': 1,
                        'sort': 'date-asc',
                        'layout': 'chat',
                        'live': True,
                        'expandedInvitations': ['NeurIPS.cc/2026/Conference/Submission${note.number}/Reviewer_.*/-/LLM_Interaction']
                    }
                ]
            )
        )

        # Selenium: login as reviewer1 and verify the LLM Interaction Chat tab is visible
        request_page(
            selenium,
            'http://localhost:3030/forum?id=' + submission.id,
            reviewer1_client,
            by=By.LINK_TEXT,
            wait_for_element='LLM Interaction Chat'
        )
        llm_tab = selenium.find_element(By.LINK_TEXT, 'LLM Interaction Chat')
        assert llm_tab

        # Selenium: login as reviewer2 and verify the LLM Interaction Chat tab is visible
        request_page(
            selenium,
            'http://localhost:3030/forum?id=' + submission.id,
            reviewer2_client,
            by=By.LINK_TEXT,
            wait_for_element='LLM Interaction Chat'
        )
        llm_tab = selenium.find_element(By.LINK_TEXT, 'LLM Interaction Chat')
        assert llm_tab
