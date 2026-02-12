import openreview
import pytest
import time
import json
import datetime
import random
import os
import re
from openreview.api import OpenReviewClient
from openreview.api import Note
from openreview.journal import Journal
from openreview.journal import JournalRequest

class TestJMLRJournal():


    @pytest.fixture(scope="class")
    def journal(self, openreview_client, helpers):

        eic_client=OpenReviewClient(username='rajarshi@mail.com', password=helpers.strong_password)

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
                    'venue_id': {'value': 'JMLR'},
                    'contact_info': {'value': 'editor@jmlr.org'},
                    'secret_key': {'value': '4567'},
                    'support_role': {'value': '~Rajarshi_Das1' },
                    'editors': {'value': ['editor@jmlr.org', '~Rajarshi_Das1'] },
                    'website': {'value': 'jmlr.org' },
                    'settings': {
                        'value': {
                            'submission_public': False,
                            'author_anonymity': False,
                            'assignment_delay': 0,
                            'skip_official_recommendation': True
                        }
                    }
                }
            ))

        helpers.await_queue_edit(openreview_client, request_form['id'])

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

    def test_submission(self, journal, openreview_client, test_client, helpers):

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

        celeste_client = OpenReviewClient(username='celeste@jmlr.com', password=helpers.strong_password)

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
        assert note.invitations == ['JMLR/-/Submission', 'JMLR/-/Edit', 'JMLR/-/Under_Review']

        edits = openreview_client.get_note_edits(note.id, invitation='JMLR/-/Under_Review')
        helpers.await_queue_edit(openreview_client, edit_id=edits[0].id)

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
        assert reviews[0].readers == [f"{venue_id}/Editors_In_Chief", f"{venue_id}/Action_Editors", f"{venue_id}/Paper1/Reviewers", f"{venue_id}/Paper1/Authors"]
        assert reviews[1].readers == [f"{venue_id}/Editors_In_Chief", f"{venue_id}/Action_Editors", f"{venue_id}/Paper1/Reviewers", f"{venue_id}/Paper1/Authors"]
        assert reviews[2].readers == [f"{venue_id}/Editors_In_Chief", f"{venue_id}/Action_Editors", f"{venue_id}/Paper1/Reviewers", f"{venue_id}/Paper1/Authors"]

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
