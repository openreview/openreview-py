import openreview
import pytest
import time
import json
import datetime
import random
import os
import re
from urllib.parse import urlparse, parse_qs
from openreview.api import OpenReviewClient
from openreview.api import Note
from openreview.journal import Journal
from openreview.journal import JournalRequest

def assert_submission_hidden(client, note_id):
    with pytest.raises(openreview.OpenReviewException) as caught:
        client.get_note(note_id)
    details = caught.value.args[0]
    assert isinstance(details, dict), details
    assert (details.get('status') in (403, 404) or
            details.get('name') in ('ForbiddenError', 'NotFoundError')), details


class TestJMLRJournal():


    @pytest.fixture(scope="class")
    def journal(self, openreview_client, helpers):

        eic_client=OpenReviewClient(username='rajarshi@mail.com', password=helpers.strong_password)
        eic_client.impersonate('JMLR')

        requests = openreview_client.get_notes(invitation='openreview.net/Support/-/Journal_Request', content={ 'venue_id': 'JMLR' })

        return JournalRequest.get_journal(eic_client, requests[0].id)

    def test_setup(self, openreview_client, request_page, selenium, helpers, journal_request):

        ## Editors in Chief
        helpers.create_user('rajarshi@mail.com', 'Rajarshi', 'Das')

        #post journal request form
        request_form = openreview_client.post_note_edit(invitation= 'openreview.net/Support/-/Journal_Request',
            signatures = ['openreview.net/Support'],
            note = Note(
                signatures = ['openreview.net/Support'],
                content = {
                    'official_venue_name': {'value': 'Journal of Machine Learning Research'},
                    'abbreviated_venue_name' : {'value': 'JMLR'},
                    'contact_info': {'value': 'editor@jmlr.org'},
                    'support_role': {'value': '~Rajarshi_Das1' },
                    'editors': {'value': ['editor@jmlr.org', '~Rajarshi_Das1'] },
                    'website': {'value': 'jmlr.org' },
                    'settings': {
                        'value': {
                            'submission_public': False,
                            'action_editor_paper_visibility': 'assigned_only',
                            'author_anonymity': False,
                            'assignment_delay': 0,
                            'skip_official_recommendation': True
                        }
                    }
                }
            ))

        helpers.await_queue_edit(openreview_client, request_form['id'])

        deployment_edit = openreview_client.post_note_edit(invitation='openreview.net/Support/-/Journal_Request_Deployment',
            signatures = ['openreview.net/Support'],
            note = Note(
                id = request_form['note']['id'],
                content = {
                    'venue_id': {'value': 'JMLR'}
                }
            ))

        helpers.await_queue_edit(openreview_client, deployment_edit['id'])

        ## Authors
        helpers.create_user('celeste@jmlrone.com', 'Celeste', 'Azul')

        #action editors
        helpers.create_user('xukun@jmlrone.com', 'Xukun', 'JMLR')
        helpers.create_user('melisa@jmlr.com', 'Melisa', 'JMLR')
        helpers.create_user('celeste@jmlr.com', 'Celeste', 'JMLR')

        # reviewers
        helpers.create_user('carlos@jmlrone.com', 'Carlos', 'JMLR')
        helpers.create_user('andrew@jmlr.com', 'Andrew', 'JMLR')
        helpers.create_user('hugo@jmlr.com', 'Hugo', 'JMLR')
        helpers.create_user('rachel@jmlr.com', 'Rachel', 'JMLR')

        openreview_client.add_members_to_group('JMLR/Action_Editors', ['~Xukun_JMLR1', '~Melisa_JMLR1', '~Celeste_JMLR1'])
        openreview_client.add_members_to_group('JMLR/Reviewers', ['~Carlos_JMLR1', '~Andrew_JMLR1', '~Hugo_JMLR1', '~Rachel_JMLR1'])

    def test_submission(self, journal, openreview_client, test_client, helpers, selenium, request_page):

        venue_id = journal.venue_id
        test_client = OpenReviewClient(username='test@mail.com', password=helpers.strong_password)
        eic_client = OpenReviewClient(username='rajarshi@mail.com', password=helpers.strong_password)

        ## Post the submission 1
        submission_note_1 = test_client.post_note_edit(invitation='JMLR/-/Submission',
            signatures=['~SomeFirstName_User1'],
            note=Note(
                content={
                    'title': { 'value': 'Paper title' },
                    'abstract': { 'value': 'Paper abstract' },
                    'authors': { 'value': ['SomeFirstName User', 'Celeste Azul']},
                    'authorids': { 'value': ['~SomeFirstName_User1', '~Celeste_Azul1']},
                    'pdf': {'value': '/pdf/' + 'p' * 40 +'.pdf' },
                    'supplementary_material': { 'value': '/attachment/' + 's' * 40 +'.zip'},
                    'competing_interests': { 'value': 'None beyond the authors normal conflict of interests'},
                    'human_subjects_reporting': { 'value': 'Not applicable'}
                }
            ))

        helpers.await_queue_edit(openreview_client, edit_id=submission_note_1['id'])
        note_id_1=submission_note_1['note']['id']

        Journal.update_affinity_scores(openreview.api.OpenReviewClient(username='openreview.net', password=helpers.strong_password), support_group_id='openreview.net/Support')

        author_group=openreview_client.get_group("JMLR/Paper1/Authors")
        assert author_group
        assert author_group.members == ['~SomeFirstName_User1', '~Celeste_Azul1']
        assert openreview_client.get_group("JMLR/Paper1/Reviewers")
        assert openreview_client.get_group("JMLR/Paper1/Action_Editors")
        assert openreview_client.get_invitation('JMLR/Paper1/Action_Editors/-/Recommendation')

        note = openreview_client.get_note(note_id_1)
        assert note
        assert note.invitations == ['JMLR/-/Submission']
        assert note.readers == ['JMLR', 'JMLR/Paper1/Action_Editors', 'JMLR/Paper1/Authors']
        celeste_client = helpers.get_user('celeste@jmlr.com')
        unassigned_ae_client = helpers.get_user('melisa@jmlr.com')
        assert_submission_hidden(celeste_client, note_id_1)
        assert_submission_hidden(unassigned_ae_client, note_id_1)
        assert note.writers == ['JMLR', 'JMLR/Paper1/Authors']
        assert note.signatures == ['JMLR/Paper1/Authors']
        assert note.content['authorids']['value'] == ['~SomeFirstName_User1', '~Celeste_Azul1']
        assert 'readers' not in note.content['authorids']
        assert 'readers' not in note.content['authors']
        assert note.content['venue']['value'] == 'Submitted to JMLR'
        assert note.content['venueid']['value'] == 'JMLR/Submitted'

        journal.invitation_builder.expire_paper_invitations(note)
        journal.invitation_builder.expire_reviewer_responsibility_invitations()
        journal.invitation_builder.expire_assignment_availability_invitations()

        # Assign Action Editor
        editor_in_chief_group_id = 'JMLR/Editors_In_Chief'
        paper_assignment_edge = eic_client.post_edge(openreview.Edge(invitation='JMLR/Action_Editors/-/Assignment',
            readers=[venue_id, editor_in_chief_group_id, '~Celeste_JMLR1'],
            writers=[venue_id, editor_in_chief_group_id],
            signatures=[editor_in_chief_group_id],
            head=note_id_1,
            tail='~Celeste_JMLR1',
            weight=1
        ))

        helpers.await_queue_edit(openreview_client, edit_id=paper_assignment_edge.id)

        # Assignment grants the handling AE access; other board members stay excluded.
        assert celeste_client.get_note(note_id_1).id == note_id_1
        assert_submission_hidden(unassigned_ae_client, note_id_1)
        assert test_client.get_note(note_id_1).id == note_id_1
        assert eic_client.get_note(note_id_1).id == note_id_1
        persisted = openreview_client.get_note(note_id_1)
        assert 'assigned_action_editor' not in persisted.content
        assert journal.get_assigned_action_editor(persisted) == '~Celeste_JMLR1'

        celeste_paper1_anon_groups = celeste_client.get_groups(prefix=f'JMLR/Paper1/Action_Editor_.*', signatory='~Celeste_JMLR1')
        assert len(celeste_paper1_anon_groups) == 1
        celeste_paper1_anon_group = celeste_paper1_anon_groups[0]

        ## Accept the submission 1
        under_review_note = celeste_client.post_note_edit(invitation= 'JMLR/Paper1/-/Review_Approval',
                                    signatures=[celeste_paper1_anon_group.id],
                                    note=Note(content={
                                        'under_review': { 'value': 'Appropriate for Review' }
                                    }))

        helpers.await_queue_edit(openreview_client, edit_id=under_review_note['id'])

        note = celeste_client.get_note(note_id_1)
        assert note
        assert note.invitations == ['JMLR/-/Submission', 'JMLR/-/Under_Review']

        edits = openreview_client.get_note_edits(note.id, invitation='JMLR/-/Under_Review')
        helpers.await_queue_edit(openreview_client, edit_id=edits[0].id)

        # Shared JMLR settings keep under-review submissions scoped to the assigned AE.
        note = openreview_client.get_note(note_id_1)
        assert note.readers == ['JMLR', 'JMLR/Paper1/Action_Editors',
                                'JMLR/Paper1/Reviewers', 'JMLR/Paper1/Authors']
        assert celeste_client.get_note(note_id_1).id == note_id_1
        assert_submission_hidden(unassigned_ae_client, note_id_1)
        assert test_client.get_note(note_id_1).id == note_id_1
        assert eic_client.get_note(note_id_1).id == note_id_1
        persisted = openreview_client.get_note(note_id_1)
        assert 'assigned_action_editor' not in persisted.content
        assert journal.get_assigned_action_editor(persisted) == '~Celeste_JMLR1'

        assert celeste_client.get_invitation('JMLR/Paper1/Reviewers/-/Assignment')

        # Assign reviewer 1
        paper_assignment_edge = celeste_client.post_edge(openreview.Edge(invitation='JMLR/Reviewers/-/Assignment',
            readers=[venue_id, f"{venue_id}/Paper1/Action_Editors", '~Rachel_JMLR1'],
            nonreaders=[f"{venue_id}/Paper1/Authors"],
            writers=[venue_id, f"{venue_id}/Paper1/Action_Editors"],
            signatures=[celeste_paper1_anon_group.id],
            head=note_id_1,
            tail='~Rachel_JMLR1',
            weight=1
        ))

        helpers.await_queue_edit(openreview_client, edit_id=paper_assignment_edge.id)

        # Assign reviewer 2
        paper_assignment_edge = celeste_client.post_edge(openreview.Edge(invitation='JMLR/Reviewers/-/Assignment',
            readers=[venue_id, f"{venue_id}/Paper1/Action_Editors", '~Andrew_JMLR1'],
            nonreaders=[f"{venue_id}/Paper1/Authors"],
            writers=[venue_id, f"{venue_id}/Paper1/Action_Editors"],
            signatures=[celeste_paper1_anon_group.id],
            head=note_id_1,
            tail='~Andrew_JMLR1',
            weight=1
        ))

        helpers.await_queue_edit(openreview_client, edit_id=paper_assignment_edge.id)

        # Assign reviewer 3
        paper_assignment_edge = celeste_client.post_edge(openreview.Edge(invitation='JMLR/Reviewers/-/Assignment',
            readers=[venue_id, f"{venue_id}/Paper1/Action_Editors", '~Hugo_JMLR1'],
            nonreaders=[f"{venue_id}/Paper1/Authors"],
            writers=[venue_id, f"{venue_id}/Paper1/Action_Editors"],
            signatures=[celeste_paper1_anon_group.id],
            head=note_id_1,
            tail='~Hugo_JMLR1',
            weight=1
        ))

        helpers.await_queue_edit(openreview_client, edit_id=paper_assignment_edge.id)

        # invite reviewers to paper
        paper_assignment_edge = celeste_client.post_edge(openreview.api.Edge(invitation='JMLR/Reviewers/-/Invite_Assignment',
            signatures=[celeste_paper1_anon_group.id],
            head=note_id_1,
            tail='outside_reviewer@gmail.com',
            weight=1,
            label='Invitation Sent'
        ))

        helpers.await_queue_edit(openreview_client, edit_id=paper_assignment_edge.id)

        # accept invitation
        messages = openreview_client.get_messages(to = 'outside_reviewer@gmail.com', subject = '[JMLR] Invitation to review paper titled "Paper title"')
        assert len(messages) == 1
        url_match = re.search(r'https://openreview\.net/invitation\?[^\s]+', messages[0]['content']['text'])

        if url_match:
            url = url_match.group(0)
            parsed_url = urlparse(url)
            params = parse_qs(parsed_url.query)
            key_value = params['key'][0]
        assert messages[0]['content']['text'] == f'''Hi outside_reviewer@gmail.com,

You were invited to review the paper number: {note.number}, title: "Paper title".

Abstract: Paper abstract

Please respond the invitation clicking the following link:

https://openreview.net/invitation?id=JMLR/Reviewers/-/Assignment_Recruitment&user=outside_reviewer@gmail.com&key={key_value}&submission_id={note_id_1}&inviter=~Celeste_JMLR1

Thanks,

JMLR Paper{note.number} Action Editor {celeste_paper1_anon_group.id.split('_')[-1]}
Celeste JMLR

Please note that responding to this email will direct your reply to celeste@jmlr.com.
'''

        invitation_url = re.search('https://.*\n', messages[0]['content']['text']).group(0).replace('https://openreview.net', 'http://localhost:3030').replace('&amp;', '&')[:-1]
        helpers.respond_invitation(selenium, request_page, invitation_url, accept=True)

        helpers.await_queue_edit(openreview_client, invitation='JMLR/Reviewers/-/Assignment_Recruitment', count=1)

        # edge is labeled as 'Pending Signup'
        invite_edges=openreview_client.get_edges(invitation='JMLR/Reviewers/-/Invite_Assignment', head=note_id_1, tail='outside_reviewer@gmail.com')
        assert len(invite_edges) == 1
        assert invite_edges[0].label == 'Pending Sign Up'

        helpers.create_user('outside_reviewer@gmail.com', 'Outside', 'Reviewer')

        # add user to reviewers group
        openreview_client.add_members_to_group('JMLR/Reviewers', ['~Outside_Reviewer1'])

        ## Run Job
        openreview.journal.Journal.check_new_profiles(openreview_client, support_group_id = 'openreview.net/Support')

        # error email is sent to the reviewer because they are already an official reviewer
        error_messages = openreview_client.get_messages(to = 'outside_reviewer@gmail.com', subject = f'[JMLR] Invitation to review paper number {note.number} cannot be accepted')
        assert len(error_messages) == 1
        assert error_messages[0]['content']['text'] == f'''Hi Outside Reviewer,

The invitation to review the paper number: {note.number}, title: "Paper title" cannot be accepted. Only external reviewers can be invited to review papers, and you have been added as an official reviewer for JMLR.

Please contact the person who invited you if you have any questions.

Thank you,
OpenReview Team

Please note that responding to this email will direct your reply to editor@jmlr.org.
'''

        # post reviews
        reviewer_one_client = OpenReviewClient(username='rachel@jmlr.com', password=helpers.strong_password)
        reviewer_one_anon_groups=reviewer_one_client.get_groups(prefix=f'{venue_id}/Paper1/Reviewer_.*', signatory='~Rachel_JMLR1')

        review_note = reviewer_one_client.post_note_edit(invitation=f'{venue_id}/Paper1/-/Review',
            signatures=[reviewer_one_anon_groups[0].id],
            note=Note(
                content={
                    'summary_of_contributions': { 'value': 'summary_of_contributions' },
                    'strengths_and_weaknesses': { 'value': 'strengths_and_weaknesses' },
                    'requested_changes': { 'value': 'requested_changes' },
                    'broader_impact_concerns': { 'value': 'broader_impact_concerns' },
                    'claims_and_evidence': { 'value': 'Yes' },
                    'audience': { 'value': 'Yes' }
                }
            )
        )

        helpers.await_queue_edit(openreview_client, edit_id=review_note['id'], process_index=0)
        helpers.await_queue_edit(openreview_client, edit_id=review_note['id'], process_index=1)

        reviewer_two_client = OpenReviewClient(username='hugo@jmlr.com', password=helpers.strong_password)
        reviewer_two_anon_groups=reviewer_two_client.get_groups(prefix=f'{venue_id}/Paper1/Reviewer_.*', signatory='~Hugo_JMLR1')

        review_note = reviewer_two_client.post_note_edit(invitation=f'{venue_id}/Paper1/-/Review',
            signatures=[reviewer_two_anon_groups[0].id],
            note=Note(
                content={
                    'summary_of_contributions': { 'value': 'summary_of_contributions' },
                    'strengths_and_weaknesses': { 'value': 'strengths_and_weaknesses' },
                    'requested_changes': { 'value': 'requested_changes' },
                    'broader_impact_concerns': { 'value': 'broader_impact_concerns' },
                    'claims_and_evidence': { 'value': 'Yes' },
                    'audience': { 'value': 'Yes' }
                }
            )
        )

        helpers.await_queue_edit(openreview_client, edit_id=review_note['id'], process_index=0)
        helpers.await_queue_edit(openreview_client, edit_id=review_note['id'], process_index=1)

        reviewer_three_client = OpenReviewClient(username='andrew@jmlr.com', password=helpers.strong_password)
        reviewer_three_anon_groups=reviewer_three_client.get_groups(prefix=f'{venue_id}/Paper1/Reviewer_.*', signatory='~Andrew_JMLR1')

        review_note = reviewer_three_client.post_note_edit(invitation=f'{venue_id}/Paper1/-/Review',
            signatures=[reviewer_three_anon_groups[0].id],
            note=Note(
                content={
                    'summary_of_contributions': { 'value': 'summary_of_contributions' },
                    'strengths_and_weaknesses': { 'value': 'strengths_and_weaknesses' },
                    'requested_changes': { 'value': 'requested_changes' },
                    'broader_impact_concerns': { 'value': 'broader_impact_concerns' },
                    'claims_and_evidence': { 'value': 'Yes' },
                    'audience': { 'value': 'Yes' }
                }
            )
        )

        helpers.await_queue_edit(openreview_client, edit_id=review_note['id'], process_index=0)
        helpers.await_queue_edit(openreview_client, edit_id=review_note['id'], process_index=1)

        reviews=openreview_client.get_notes(forum=note_id_1, invitation=f'{venue_id}/Paper1/-/Review', sort='number:desc')
        assert len(reviews) == 3
        assert reviews[0].readers == [f"{venue_id}/Editors_In_Chief", f"{venue_id}/Paper1/Action_Editors", f"{venue_id}/Paper1/Reviewers", f"{venue_id}/Paper1/Authors"]
        assert reviews[1].readers == [f"{venue_id}/Editors_In_Chief", f"{venue_id}/Paper1/Action_Editors", f"{venue_id}/Paper1/Reviewers", f"{venue_id}/Paper1/Authors"]
        assert reviews[2].readers == [f"{venue_id}/Editors_In_Chief", f"{venue_id}/Paper1/Action_Editors", f"{venue_id}/Paper1/Reviewers", f"{venue_id}/Paper1/Authors"]
        for review in reviews:
            for role, actor in [('assigned AE', celeste_client), ('author', test_client),
                                ('reviewer', reviewer_three_client), ('EIC', eic_client)]:
                assert actor.get_note(review.id).id == review.id, role
            assert_submission_hidden(unassigned_ae_client, review.id)

        with pytest.raises(openreview.OpenReviewException, match=r'The Invitation JMLR/Paper1/-/Official_Recommendation was not found'):
            invitation = eic_client.get_invitation(f'{venue_id}/Paper1/-/Official_Recommendation')

        # check review rating invitation is active
        invitation = eic_client.get_invitation(f'{reviewer_one_anon_groups[0].id}/-/Rating')
        assert invitation
        invitation = eic_client.get_invitation(f'{reviewer_two_anon_groups[0].id}/-/Rating')
        assert invitation
        invitation = eic_client.get_invitation(f'{reviewer_three_anon_groups[0].id}/-/Rating')
        assert invitation

        messages = journal.client.get_messages(to = 'celeste@jmlr.com', subject = '[JMLR] Evaluate reviewers and submit decision for JMLR submission 1: Paper title')
        assert len(messages) == 1
        assert messages[0]['content']['text'] == f'''Hi Celeste JMLR,

Thank you for overseeing the review process for JMLR submission "1: Paper title".

All reviewers have submitted their reviews for the submission. Therefore it is now time for you to determine a decision for the submission. Before doing so:

- Make sure you have sufficiently discussed with the authors (and possibly the reviewers) any concern you may have about the submission.
- Rate the quality of the reviews submitted by the reviewers. **You will not be able to submit your decision until these ratings have been submitted**. To rate a review, go on the submission's page and click on button "Rating" for each of the reviews.

We ask that you submit your decision **within 1 week** ({(datetime.datetime.now() + datetime.timedelta(weeks = 1)).strftime("%b %d")}). To do so, please follow this link: https://openreview.net/forum?id={note_id_1}&invitationId=JMLR/Paper1/-/Decision

The possible decisions are:
- **Accept as is**: once its camera ready version is submitted, the manuscript will be marked as accepted.
- **Accept with minor revision**: to use if you wish to request some specific revisions to the manuscript, to be specified explicitly in your decision comments. These revisions will be expected from the authors when they submit their camera ready version.
- **Reject**: the paper is rejected, but you may indicate whether you would be willing to consider a significantly revised version of the manuscript. Such a revised submission will need to be entered as a new submission, that will also provide a link to this rejected submission as well as a description of the changes made since.

Your decision may also include certification(s) recommendations for the submission (in case of an acceptance).

For more details and guidelines on performing your review, visit jmlr.org.

We thank you for your essential contribution to JMLR!

The JMLR Editors-in-Chief


Please note that responding to this email will direct your reply to editor@jmlr.org.
'''
        # assert Decision invitation is not active yet
        with pytest.raises(openreview.OpenReviewException, match=r'The Invitation JMLR/Paper1/-/Decision was not found'):
            invitation = celeste_client.get_invitation(f'{venue_id}/Paper1/-/Decision')

        reviews=openreview_client.get_notes(forum=note_id_1, invitation=f'{venue_id}/Paper1/-/Review', sort= 'number:asc')
        for review in reviews:
            signature=review.signatures[0]

            rating_note=celeste_client.post_note_edit(invitation=f'{signature}/-/Rating',
                signatures=[celeste_paper1_anon_group.id],
                note=Note(
                    content={
                        'rating': { 'value': 'Exceeds expectations' }
                    }
                )
            )
            helpers.await_queue_edit(openreview_client, edit_id=rating_note['id'])
            process_logs = openreview_client.get_process_logs(id = rating_note['id'])
            assert len(process_logs) == 1
            assert process_logs[0]['status'] == 'ok'

        last_rating_invitation = openreview_client.get_invitation(rating_note['invitation'])

        # check decision invitation is now active
        invitation = celeste_client.get_invitation(f'{venue_id}/Paper1/-/Decision')
        assert invitation.cdate == last_rating_invitation.cdate
        assert invitation.duedate == last_rating_invitation.duedate
        assert not invitation.expdate

        decision_note = celeste_client.post_note_edit(invitation=f'{venue_id}/Paper1/-/Decision',
                signatures=[celeste_paper1_anon_group.id],
                note=Note(
                    content={
                        'claims_and_evidence': { 'value': 'Yes' },
                        'audience': { 'value': 'Yes' },
                        'recommendation': { 'value': 'Accept as is' },
                        'comment': { 'value': 'Great paper!' },
                    }
                )
            )

        helpers.await_queue_edit(openreview_client, edit_id=decision_note['id'])
        pending_decision = openreview_client.get_note(decision_note['note']['id'])
        assert pending_decision.readers == [f'{venue_id}/Editors_In_Chief',
                                           f'{venue_id}/Paper1/Action_Editors']
        assert eic_client.get_note(pending_decision.id).id == pending_decision.id
        assert_submission_hidden(test_client, pending_decision.id)
        assert_submission_hidden(unassigned_ae_client, pending_decision.id)
        approval = eic_client.post_note_edit(
            invitation=journal.get_decision_approval_id(1),
            signatures=[journal.get_editors_in_chief_id()],
            note=Note(content={
                'approval': {'value': "I approve the AE's decision."},
                'comment_to_the_AE': {'value': 'I agree with the AE'},
            }))
        helpers.await_queue_edit(openreview_client, edit_id=approval['id'])
        released_decision = openreview_client.get_note(decision_note['note']['id'])
        assert released_decision.readers == [f'{venue_id}/Editors_In_Chief',
                                            f'{venue_id}/Paper1/Action_Editors',
                                            f'{venue_id}/Paper1/Reviewers',
                                            f'{venue_id}/Paper1/Authors']
        for role, actor in [('assigned AE', celeste_client), ('author', test_client),
                            ('reviewer', reviewer_three_client), ('EIC', eic_client)]:
            assert actor.get_note(released_decision.id).id == released_decision.id, role
        assert_submission_hidden(unassigned_ae_client, released_decision.id)
        assert_submission_hidden(unassigned_ae_client, note_id_1)


    @pytest.mark.parametrize('visibility', [None, 'assigned_only', 'all'],
                             ids=['default', 'assigned-only', 'all-aes'])
    def test_submission_visibility_after_review_approval(
            self, visibility, openreview_client, helpers, journal_request):
        """Omitted and explicit scoped modes agree; explicit all expands under review."""
        venue_id = {None: 'JMLRVisibilityDefault', 'assigned_only': 'JMLRVisibilityAssignedOnly',
                    'all': 'JMLRVisibilityAll'}[visibility]
        # Use private nonanonymous submissions, varying only the readership policy.
        settings = {
            'submission_public': False,
            'author_anonymity': False,
            'assignment_delay': 0,
            'skip_official_recommendation': True,
        }
        if visibility is not None:
            settings['action_editor_paper_visibility'] = visibility
        request = openreview_client.post_note_edit(
            invitation='openreview.net/Support/-/Journal_Request',
            signatures=['openreview.net/Support'],
            note=Note(content={
                'official_venue_name': {'value': 'JMLR Visibility Test'},
                'abbreviated_venue_name': {'value': venue_id},
                'contact_info': {'value': 'editor@jmlr.org'},
                'support_role': {'value': '~Rajarshi_Das1'},
                'editors': {'value': ['editor@jmlr.org', '~Rajarshi_Das1']},
                'website': {'value': 'jmlr.org'},
                'settings': {'value': settings},
            }))
        helpers.await_queue_edit(openreview_client, request['id'])
        deployment = openreview_client.post_note_edit(
            invitation='openreview.net/Support/-/Journal_Request_Deployment',
            signatures=['openreview.net/Support'],
            note=Note(id=request['note']['id'], content={'venue_id': {'value': venue_id}}))
        helpers.await_queue_edit(openreview_client, deployment['id'])
        backend = helpers.get_user('rajarshi@mail.com')
        backend.impersonate(venue_id)
        journal = JournalRequest.get_journal(backend, request['note']['id'])
        openreview_client.add_members_to_group(
            journal.get_action_editors_id(), ['~Celeste_JMLR1', '~Melisa_JMLR1'])
        author = helpers.get_user('test@mail.com')
        assigned_ae = helpers.get_user('celeste@jmlr.com')
        unassigned_ae = helpers.get_user('melisa@jmlr.com')
        eic = helpers.get_user('rajarshi@mail.com')
        submission = author.post_note_edit(
            invitation=journal.get_author_submission_id(), signatures=['~SomeFirstName_User1'],
            note=Note(content={
                'title': {'value': 'JMLR visibility lifecycle'},
                'abstract': {'value': 'Assigned and unassigned AE readership.'},
                'authors': {'value': ['SomeFirstName User']},
                'authorids': {'value': ['~SomeFirstName_User1']},
                'pdf': {'value': '/pdf/' + 'p' * 40 + '.pdf'},
                'competing_interests': {'value': 'None'},
                'human_subjects_reporting': {'value': 'Not applicable'},
            }))
        helpers.await_queue_edit(openreview_client, submission['id'])
        note_id = submission['note']['id']
        note = openreview_client.get_note(note_id)
        number = note.number
        paper_aes = journal.get_action_editors_id(number)
        authors = journal.get_authors_id(number)
        assert note.readers == [venue_id, paper_aes, authors]
        assert_submission_hidden(assigned_ae, note_id)
        assert_submission_hidden(unassigned_ae, note_id)

        assignment = eic.post_edge(openreview.api.Edge(
            invitation=journal.get_ae_assignment_id(),
            signatures=[journal.get_editors_in_chief_id()],
            head=note_id, tail='~Celeste_JMLR1', weight=1))
        helpers.await_queue_edit(openreview_client, assignment.id)
        assert assigned_ae.get_note(note_id).id == note_id
        assert_submission_hidden(unassigned_ae, note_id)
        assert author.get_note(note_id).id == note_id
        assert eic.get_note(note_id).id == note_id

        anon_groups = assigned_ae.get_groups(
            prefix=journal.get_action_editors_id(number, anon=True), signatory='~Celeste_JMLR1')
        assert len(anon_groups) == 1
        approval = assigned_ae.post_note_edit(
            invitation=journal.get_review_approval_id(number), signatures=[anon_groups[0].id],
            note=Note(content={'under_review': {'value': 'Appropriate for Review'}}))
        helpers.await_queue_edit(openreview_client, approval['id'])
        transitions = openreview_client.get_note_edits(
            note_id=note_id, invitation=journal.get_under_review_id())
        assert len(transitions) == 1
        helpers.await_queue_edit(openreview_client, transitions[0].id)
        note = openreview_client.get_note(note_id)
        assert note.content['venueid']['value'] == journal.under_review_venue_id
        ae_reader = journal.get_action_editors_id() if visibility == 'all' else paper_aes
        assert note.readers == [venue_id, ae_reader, journal.get_reviewers_id(number), authors]
        assert assigned_ae.get_note(note_id).id == note_id
        assert author.get_note(note_id).id == note_id
        assert eic.get_note(note_id).id == note_id
        if visibility != 'all':
            assert_submission_hidden(unassigned_ae, note_id)
        else:
            assert unassigned_ae.get_note(note_id).id == note_id
