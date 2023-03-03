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

class TestTACLJournal():


    @pytest.fixture(scope="class")
    def journal(self, openreview_client):

        eic_client=OpenReviewClient(username='brian@mail.com', password='1234')
        eic_client.impersonate('TACL/Editors_In_Chief')

        requests = openreview_client.get_notes(invitation='openreview.net/Support/-/Journal_Request', content={ 'venue_id': 'TACL' })

        return JournalRequest.get_journal(eic_client, requests[0].id)

    def test_setup(self, openreview_client, request_page, selenium, helpers, journal_request):

        ## Editors in Chief
        helpers.create_user('brian@mail.com', 'Brian', 'Roark')

        #post journal request form
        request_form = openreview_client.post_note_edit(invitation= 'openreview.net/Support/-/Journal_Request',
            signatures = ['openreview.net/Support'],
            note = Note(
                signatures = ['openreview.net/Support'],
                content = {
                    'official_venue_name': {'value': 'Transactions of the Association for Computational Linguistics'},
                    'abbreviated_venue_name' : {'value': 'TACL'},
                    'venue_id': {'value': 'TACL'},
                    'contact_info': {'value': 'tacl@venue.org'},
                    'secret_key': {'value': '4567'},
                    'support_role': {'value': '~Brian_Roark1' },
                    'editors': {'value': ['tacl@editor.org', '~Brian_Roark1'] },
                    'website': {'value': 'transacl.org' },
                    'settings': {
                        'value': {
                            'submission_public': False,
                            'assignment_delay': 0,
                            'certifications': [
                                'Featured Certification',
                                'Reproducibility Certification',
                                'Survey Certification'
                            ]
                        }
                    }
                }
            ))

        helpers.await_queue_edit(openreview_client, request_form['id'])

        ## Action Editors
        helpers.create_user('graham@mailseven.com', 'Graham', 'Neubig')

        openreview_client.add_members_to_group('TACL/Action_Editors', '~Graham_Neubig1')

        ## Reviewers
        david_client=helpers.create_user('david@taclone.com', 'David', 'Bensusan')
        javier_client=helpers.create_user('javier@tacltwo.com', 'Javier', 'Barden')
        carlos_client=helpers.create_user('carlos@taclthree.com', 'Carlos', 'Gardel')

        ## Authors
        melisa_client=helpers.create_user('melisa@taclfour.com', 'Melisa', 'Andersen')

        openreview_client.add_members_to_group('TACL/Reviewers', ['~David_Bensusan1', '~Carlos_Gardel1', '~Javier_Barden1'])


    def test_submission(self, journal, openreview_client, test_client, helpers):

        test_client = OpenReviewClient(username='test@mail.com', password='1234')

        ## Post the submission 1
        submission_note_1 = test_client.post_note_edit(invitation='TACL/-/Submission',
            signatures=['~SomeFirstName_User1'],
            note=Note(
                content={
                    'title': { 'value': 'Paper title' },
                    'abstract': { 'value': 'Paper abstract' },
                    'authors': { 'value': ['SomeFirstName User', 'Melisa Andersen']},
                    'authorids': { 'value': ['~SomeFirstName_User1', '~Melisa_Andersen1']},
                    'pdf': {'value': '/pdf/' + 'p' * 40 +'.pdf' },
                    'supplementary_material': { 'value': '/attachment/' + 's' * 40 +'.zip'},
                    'competing_interests': { 'value': 'None beyond the authors normal conflict of interests'},
                    'human_subjects_reporting': { 'value': 'Not applicable'}
                }
            ))

        helpers.await_queue_edit(openreview_client, edit_id=submission_note_1['id'])
        note_id_1=submission_note_1['note']['id']

        messages = journal.client.get_messages(to = 'test@mail.com', subject = '[TACL] Suggest candidate Action Editor for your new TACL submission')
        assert len(messages) == 1
        assert messages[0]['content']['text'] == '''Hi SomeFirstName User,

Thank you for submitting your work titled "Paper title" to TACL.

Before the review process starts, you need to submit one or more recommendations for an Action Editor that you believe has the expertise to oversee the evaluation of your work.

To do so, please follow this link: https://openreview.net/invitation?id=TACL/Paper1/Action_Editors/-/Recommendation or check your tasks in the Author Console: https://openreview.net/group?id=TACL/Authors

For more details and guidelines on the TACL review process, visit transacl.org.

The TACL Editors-in-Chief
'''

        author_group=openreview_client.get_group("TACL/Paper1/Authors")
        assert author_group
        assert author_group.members == ['~SomeFirstName_User1', '~Melisa_Andersen1']
        assert openreview_client.get_group("TACL/Paper1/Reviewers")
        assert openreview_client.get_group("TACL/Paper1/Action_Editors")

        note = openreview_client.get_note(note_id_1)
        assert note
        assert note.invitations == ['TACL/-/Submission']
        assert note.readers == ['TACL', 'TACL/Paper1/Action_Editors', 'TACL/Paper1/Authors']
        assert note.writers == ['TACL', 'TACL/Paper1/Authors']
        assert note.signatures == ['TACL/Paper1/Authors']
        assert note.content['authorids']['value'] == ['~SomeFirstName_User1', '~Melisa_Andersen1']
        assert note.content['venue']['value'] == 'Submitted to TACL'
        assert note.content['venueid']['value'] == 'TACL/Submitted'


        ## Update submission 1
        updated_submission_note_1 = test_client.post_note_edit(invitation='TACL/Paper1/-/Revision',
            signatures=['TACL/Paper1/Authors'],
            note=Note(
                content={
                    'title': { 'value': 'Paper title UPDATED' },
                    'supplementary_material': { 'value': '/attachment/' + 'z' * 40 +'.zip'},
                    'competing_interests': { 'value': 'None beyond the authors normal conflict of interests'},
                    'human_subjects_reporting': { 'value': 'Not applicable'},
                    'pdf': { 'value': '/pdf/22234qweoiuweroi22234qweoiuweroi12345678.pdf' }
                }
            ))
        helpers.await_queue_edit(openreview_client, edit_id=updated_submission_note_1['id'])

        note = openreview_client.get_note(note_id_1)
        assert note
        assert note.number == 1
        assert note.invitations == ['TACL/-/Submission', 'TACL/Paper1/-/Revision']
        assert note.readers == ['TACL', 'TACL/Paper1/Action_Editors', 'TACL/Paper1/Authors']
        assert note.writers == ['TACL', 'TACL/Paper1/Authors']
        assert note.signatures == ['TACL/Paper1/Authors']
        assert note.content['title']['value'] == 'Paper title UPDATED'
        assert note.content['venue']['value'] == 'Submitted to TACL'
        assert note.content['venueid']['value'] == 'TACL/Submitted'
        assert note.content['supplementary_material']['value'] == '/attachment/zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz.zip'
        assert note.content['authorids']['value'] == ['~SomeFirstName_User1', '~Melisa_Andersen1']
        assert note.content['authorids']['readers'] == ['TACL', 'TACL/Paper1/Action_Editors', 'TACL/Paper1/Authors']

    def test_review_approval(self, journal, openreview_client, helpers):

        brian_client = OpenReviewClient(username='brian@mail.com', password='1234')
        graham_client = OpenReviewClient(username='graham@mailseven.com', password='1234')
        note_id_1 = openreview_client.get_notes(invitation='TACL/-/Submission')[0].id

        # Assign Action Editor
        paper_assignment_edge = brian_client.post_edge(openreview.Edge(invitation='TACL/Action_Editors/-/Assignment',
            readers=['TACL', 'TACL/Editors_In_Chief', '~Graham_Neubig1'],
            writers=['TACL', 'TACL/Editors_In_Chief'],
            signatures=['TACL/Editors_In_Chief'],
            head=note_id_1,
            tail='~Graham_Neubig1',
            weight=1
        ))

        helpers.await_queue_edit(openreview_client, edit_id=paper_assignment_edge.id)

        ae_group = brian_client.get_group('TACL/Paper1/Action_Editors')
        assert ae_group.members == ['~Graham_Neubig1']

        messages = journal.client.get_messages(to = 'graham@mailseven.com', subject = '[TACL] Assignment to new TACL submission Paper title UPDATED')
        assert len(messages) == 1
        assert messages[0]['content']['text'] == f'''Hi Graham Neubig,

With this email, we request that you manage the review process for a new TACL submission titled "Paper title UPDATED".

As a reminder, TACL Action Editors (AEs) are **expected to accept all AE requests** to manage submissions that fall within your expertise and quota. Reasonable exceptions are 1) situations where exceptional personal circumstances (e.g. vacation, health problems) render you incapable of fully performing your AE duties or 2) you have a conflict of interest with one of the authors. If any such exception applies to you, contact us at tacl@venue.org.

Your first task is to make sure the submitted preprint is appropriate for TACL and respects our submission guidelines. Clear cases of desk rejection include submissions that are not anonymized, submissions that do not use the unmodified TACL stylefile and submissions that clearly overlap with work already published in proceedings (or currently under review for publication). If you suspect but are unsure about whether a submission might need to be desk rejected for any other reasons (e.g. lack of fit with the scope of TACL or lack of technical depth), please email us.

Please follow this link to perform this task: https://openreview.net/forum?id={note_id_1}&invitationId=TACL/Paper1/-/Review_Approval

If you think the submission can continue through TACL's review process, click the button "Under Review". Otherwise, click on "Desk Reject". Once the submission has been confirmed, then the review process will begin, and your next step will be to assign 3 reviewers to the paper. You will get a follow up email when OpenReview is ready for you to assign these 3 reviewers.

We thank you for your essential contribution to TACL!

The TACL Editors-in-Chief
'''

        ## Accept the submission 1
        under_review_note = graham_client.post_note_edit(invitation= 'TACL/Paper1/-/Review_Approval',
                                    signatures=['TACL/Paper1/Action_Editors'],
                                    note=Note(content={
                                        'under_review': { 'value': 'Appropriate for Review' }
                                    }))

        helpers.await_queue_edit(openreview_client, edit_id=under_review_note['id'])

        note = graham_client.get_note(note_id_1)
        assert note
        assert note.invitations == ['TACL/-/Submission', 'TACL/Paper1/-/Revision', 'TACL/-/Under_Review']
        assert note.readers == ['TACL', 'TACL/Paper1/Action_Editors', 'TACL/Paper1/Reviewers', 'TACL/Paper1/Authors']
        assert note.writers == ['TACL', 'TACL/Paper1/Authors']
        assert note.signatures == ['TACL/Paper1/Authors']
        assert note.content['authorids']['value'] == ['~SomeFirstName_User1', '~Melisa_Andersen1']
        assert note.content['venue']['value'] == 'Under review for TACL'
        assert note.content['venueid']['value'] == 'TACL/Under_Review'
        assert note.content['assigned_action_editor']['value'] == '~Graham_Neubig1'
        assert note.content['_bibtex']['value'] == '''@article{
anonymous''' + str(datetime.datetime.fromtimestamp(note.cdate/1000).year) + '''paper,
title={Paper title {UPDATED}},
author={Anonymous},
journal={Submitted to Transactions of the Association for Computational Linguistics},
year={''' + str(datetime.datetime.today().year) + '''},
url={https://openreview.net/forum?id=''' + note_id_1 + '''},
note={Under review}
}'''

        edits = openreview_client.get_note_edits(note.id, invitation='TACL/-/Under_Review')
        helpers.await_queue_edit(openreview_client, edit_id=edits[0].id)

        invitations = openreview_client.get_invitations(prefix='TACL/Paper', replyForum=note_id_1)
        assert "TACL/Paper1/-/Revision"  in [i.id for i in invitations]
        assert "TACL/Paper1/-/Withdrawal"  in [i.id for i in invitations]
        assert "TACL/Paper1/-/Review" in [i.id for i in invitations]
        assert "TACL/Paper1/-/Volunteer_to_Review" not in [i.id for i in invitations]
        assert "TACL/Paper1/-/Public_Comment" not in [i.id for i in invitations]
        assert "TACL/Paper1/-/Official_Comment" in [i.id for i in invitations]
        assert "TACL/Paper1/-/Moderation" not in [i.id for i in invitations]

        edits = openreview_client.get_note_edits(note.id)
        assert len(edits) == 3
        for edit in edits:
            assert edit.readers == ['TACL', 'TACL/Paper1/Action_Editors', 'TACL/Paper1/Reviewers', 'TACL/Paper1/Authors']

    def test_review(self, journal, openreview_client, helpers):

        brian_client = OpenReviewClient(username='brian@mail.com', password='1234')
        graham_client = OpenReviewClient(username='graham@mailseven.com', password='1234')
        note_id_1 = openreview_client.get_notes(invitation='TACL/-/Submission')[0].id

        david_client = OpenReviewClient(username='david@taclone.com', password='1234')
        carlos_client = OpenReviewClient(username='carlos@taclthree.com', password='1234')
        javier_client = OpenReviewClient(username='javier@tacltwo.com', password='1234')

        # add David Belanger again
        paper_assignment_edge = graham_client.post_edge(openreview.Edge(invitation='TACL/Reviewers/-/Assignment',
            readers=["TACL", "TACL/Paper1/Action_Editors", '~David_Bensusan1'],
            nonreaders=["TACL/Paper1/Authors"],
            writers=["TACL", "TACL/Paper1/Action_Editors"],
            signatures=["TACL/Paper1/Action_Editors"],
            head=note_id_1,
            tail='~David_Bensusan1',
            weight=1
        ))

         # wait for process function delay (5 seconds) and check email has been sent
        time.sleep(6)
        messages = journal.client.get_messages(to = 'david@taclone.com', subject = '[TACL] Assignment to review new TACL submission Paper title UPDATED')
        assert len(messages) == 1
        assert messages[0]['content']['text'] == f'''Hi David Bensusan,

With this email, we request that you submit, within 2 weeks ({(datetime.datetime.utcnow() + datetime.timedelta(weeks = 2)).strftime("%b %d")}) a review for your newly assigned TACL submission "Paper title UPDATED". If the submission is longer than 12 pages (excluding any appendix), you may request more time to the AE.

Please acknowledge on OpenReview that you have received this review assignment by following this link: https://openreview.net/forum?id={note_id_1}&invitationId=TACL/Paper1/Reviewers/-/~David_Bensusan1/Assignment/Acknowledgement

As a reminder, reviewers are **expected to accept all assignments** for submissions that fall within their expertise and annual quota (6 papers). Acceptable exceptions are 1) if you have an active, unsubmitted review for another TACL submission or 2) situations where exceptional personal circumstances (e.g. vacation, health problems) render you incapable of performing your reviewing duties. Based on the above, if you think you should not review this submission, contact your AE directly (you can do so by leaving a comment on OpenReview, with only the Action Editor as Reader).

To submit your review, please follow this link: https://openreview.net/forum?id={note_id_1}&invitationId=TACL/Paper1/-/Review or check your tasks in the Reviewers Console: https://openreview.net/group?id=TACL/Reviewers#reviewer-tasks

Once submitted, your review will become privately visible to the authors and AE. Then, as soon as 3 reviews have been submitted, all reviews will become publicly visible. For more details and guidelines on performing your review, visit transacl.org.

We thank you for your essential contribution to TACL!

The TACL Editors-in-Chief
note: replies to this email will go to the AE, Graham Neubig.
'''
        assert messages[0]['content']['replyTo'] == 'graham@mailseven.com'

        ## Carlos Gardel
        paper_assignment_edge = graham_client.post_edge(openreview.Edge(invitation='TACL/Reviewers/-/Assignment',
            readers=["TACL", "TACL/Paper1/Action_Editors", '~Carlos_Gardel1'],
            nonreaders=["TACL/Paper1/Authors"],
            writers=["TACL", "TACL/Paper1/Action_Editors"],
            signatures=["TACL/Paper1/Action_Editors"],
            head=note_id_1,
            tail='~Carlos_Gardel1',
            weight=1
        ))

        ## Javier Barden
        paper_assignment_edge = graham_client.post_edge(openreview.Edge(invitation='TACL/Reviewers/-/Assignment',
            readers=["TACL", "TACL/Paper1/Action_Editors", '~Javier_Barden1'],
            nonreaders=["TACL/Paper1/Authors"],
            writers=["TACL", "TACL/Paper1/Action_Editors"],
            signatures=["TACL/Paper1/Action_Editors"],
            head=note_id_1,
            tail='~Javier_Barden1',
            weight=1
        ))

        helpers.await_queue_edit(openreview_client, edit_id=paper_assignment_edge.id)

        reviewerrs_group = brian_client.get_group('TACL/Paper1/Reviewers')
        assert reviewerrs_group.members == ['~David_Bensusan1', '~Carlos_Gardel1', '~Javier_Barden1']

        david_anon_groups=david_client.get_groups(prefix='TACL/Paper1/Reviewer_.*', signatory='~David_Bensusan1')
        assert len(david_anon_groups) == 1

        ## Post a review edit
        david_review_note = david_client.post_note_edit(invitation='TACL/Paper1/-/Review',
            signatures=[david_anon_groups[0].id],
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

        helpers.await_queue_edit(openreview_client, edit_id=david_review_note['id'])

        carlos_anon_groups=carlos_client.get_groups(prefix='TACL/Paper1/Reviewer_.*', signatory='~Carlos_Gardel1')
        assert len(carlos_anon_groups) == 1

        ## Post a review edit
        carlos_review_note = carlos_client.post_note_edit(invitation='TACL/Paper1/-/Review',
            signatures=[carlos_anon_groups[0].id],
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

        helpers.await_queue_edit(openreview_client, edit_id=carlos_review_note['id'])

        javier_anon_groups=javier_client.get_groups(prefix='TACL/Paper1/Reviewer_.*', signatory='~Javier_Barden1')
        assert len(javier_anon_groups) == 1

        ## Post a review edit
        javier_review_note = javier_client.post_note_edit(invitation='TACL/Paper1/-/Review',
            signatures=[javier_anon_groups[0].id],
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

        helpers.await_queue_edit(openreview_client, edit_id=javier_review_note['id'])

        ## All the reviewes should be visible to all the reviewers now
        reviews=openreview_client.get_notes(forum=note_id_1, invitation='TACL/Paper1/-/Review', sort= 'number:asc')
        assert len(reviews) == 3
        assert reviews[0].readers == ['TACL/Editors_In_Chief', 'TACL/Paper1/Action_Editors', 'TACL/Paper1/Reviewers', 'TACL/Paper1/Authors']
        assert reviews[0].signatures == [david_anon_groups[0].id]
        assert reviews[1].readers == ['TACL/Editors_In_Chief', 'TACL/Paper1/Action_Editors', 'TACL/Paper1/Reviewers', 'TACL/Paper1/Authors']
        assert reviews[1].signatures == [carlos_anon_groups[0].id]
        assert reviews[2].readers == ['TACL/Editors_In_Chief', 'TACL/Paper1/Action_Editors', 'TACL/Paper1/Reviewers', 'TACL/Paper1/Authors']
        assert reviews[2].signatures == [javier_anon_groups[0].id]

        invitations = openreview_client.get_invitations(replyForum=note_id_1, prefix='TACL/Paper1')
        assert len(invitations) == 6
        assert "TACL/Paper1/-/Official_Comment" in [i.id for i in invitations]
        assert "TACL/Paper1/-/Review" in [i.id for i in invitations]
        assert "TACL/Paper1/-/Revision" in [i.id for i in invitations]
        assert "TACL/Paper1/-/Withdrawal" in [i.id for i in invitations]
        assert "TACL/Paper1/-/Desk_Rejection" in [i.id for i in invitations]
        assert "TACL/Paper1/-/Official_Recommendation" in [i.id for i in invitations]

        official_comment_invitation = openreview_client.get_invitation("TACL/Paper1/-/Official_Comment")
        assert 'everyone' not in official_comment_invitation.edit['note']['readers']['param']['enum']


    def test_official_recommendation(self, journal, openreview_client, helpers):

        brian_client = OpenReviewClient(username='brian@mail.com', password='1234')
        graham_client = OpenReviewClient(username='graham@mailseven.com', password='1234')
        note_id_1 = openreview_client.get_notes(invitation='TACL/-/Submission')[0].id

        david_client = OpenReviewClient(username='david@taclone.com', password='1234')
        carlos_client = OpenReviewClient(username='carlos@taclthree.com', password='1234')
        javier_client = OpenReviewClient(username='javier@tacltwo.com', password='1234')

        invitation = brian_client.get_invitation('TACL/Paper1/-/Official_Recommendation')
        assert invitation.cdate > openreview.tools.datetime_millis(datetime.datetime.utcnow())

        brian_client.post_invitation_edit(
            invitations='TACL/-/Edit',
            readers=['TACL'],
            writers=['TACL'],
            signatures=['TACL'],
            invitation=openreview.api.Invitation(id=f'TACL/Paper1/-/Official_Recommendation',
                cdate=openreview.tools.datetime_millis(datetime.datetime.utcnow()) + 1000,
                signatures=['TACL/Editors_In_Chief']
            )
        )

        time.sleep(5) ## wait until the process function runs

        ## Check emails being sent to Reviewers and AE
        messages = journal.client.get_messages(subject = '[TACL] Submit official recommendation for TACL submission Paper title UPDATED')
        assert len(messages) == 3
        messages = journal.client.get_messages(to= 'david@taclone.com', subject = '[TACL] Submit official recommendation for TACL submission Paper title UPDATED')
        assert messages[0]['content']['text'] == f'''Hi David Bensusan,

Thank you for submitting your review and engaging with the authors of TACL submission "Paper title UPDATED".

You may now submit your official recommendation for the submission. Before doing so, make sure you have sufficiently discussed with the authors (and possibly the other reviewers and AE) any concerns you may have about the submission.

We ask that you submit your recommendation within 2 weeks ({(datetime.datetime.utcnow() + datetime.timedelta(weeks = 4)).strftime("%b %d")}). To do so, please follow this link: https://openreview.net/forum?id={note_id_1}&invitationId=TACL/Paper1/-/Official_Recommendation

For more details and guidelines on performing your review, visit transacl.org.

We thank you for your essential contribution to TACL!

The TACL Editors-in-Chief
note: replies to this email will go to the AE, Graham Neubig.
'''
        messages = journal.client.get_messages(subject = '[TACL] Reviewers must submit official recommendation for TACL submission Paper title UPDATED')
        assert len(messages) == 1

        david_anon_groups=david_client.get_groups(prefix='TACL/Paper1/Reviewer_.*', signatory='~David_Bensusan1')

        official_recommendation_note = david_client.post_note_edit(invitation='TACL/Paper1/-/Official_Recommendation',
            signatures=[david_anon_groups[0].id],
            note=Note(
                content={
                    'decision_recommendation': { 'value': 'Leaning Accept' },
                    'certification_recommendations': { 'value': ['Survey Certification'] },
                    'claims_and_evidence': { 'value': 'Yes' },
                    'audience': { 'value': 'Yes' }
                }
            )
        )

        helpers.await_queue_edit(openreview_client, edit_id=official_recommendation_note['id'])

        carlos_anon_groups=carlos_client.get_groups(prefix='TACL/Paper1/Reviewer_.*', signatory='~Carlos_Gardel1')

        official_recommendation_note = carlos_client.post_note_edit(invitation='TACL/Paper1/-/Official_Recommendation',
            signatures=[carlos_anon_groups[0].id],
            note=Note(
                content={
                    'decision_recommendation': { 'value': 'Leaning Accept' },
                    'certification_recommendations': { 'value': ['Survey Certification'] },
                    'claims_and_evidence': { 'value': 'Yes' },
                    'audience': { 'value': 'Yes' }
                }
            )
        )

        helpers.await_queue_edit(openreview_client, edit_id=official_recommendation_note['id'])

        javier_anon_groups=javier_client.get_groups(prefix='TACL/Paper1/Reviewer_.*', signatory='~Javier_Barden1')

        official_recommendation_note = javier_client.post_note_edit(invitation='TACL/Paper1/-/Official_Recommendation',
            signatures=[javier_anon_groups[0].id],
            note=Note(
                content={
                    'decision_recommendation': { 'value': 'Leaning Accept' },
                    'certification_recommendations': { 'value': ['Survey Certification'] },
                    'claims_and_evidence': { 'value': 'Yes' },
                    'audience': { 'value': 'Yes' }
                }
            )
        )

        helpers.await_queue_edit(openreview_client, edit_id=official_recommendation_note['id'])

        reviews=openreview_client.get_notes(forum=note_id_1, invitation='TACL/Paper1/-/Official_Recommendation', sort= 'number:asc')
        assert len(reviews) == 3
        assert reviews[0].readers == ['TACL/Editors_In_Chief', 'TACL/Paper1/Action_Editors', david_anon_groups[0].id]
        assert reviews[0].signatures == [david_anon_groups[0].id]
        assert reviews[1].readers == ['TACL/Editors_In_Chief', 'TACL/Paper1/Action_Editors', carlos_anon_groups[0].id]
        assert reviews[1].signatures == [carlos_anon_groups[0].id]
        assert reviews[2].readers == ['TACL/Editors_In_Chief', 'TACL/Paper1/Action_Editors', javier_anon_groups[0].id]
        assert reviews[2].signatures == [javier_anon_groups[0].id]


    def test_decision(self, journal, openreview_client, helpers):

        brian_client = OpenReviewClient(username='brian@mail.com', password='1234')
        graham_client = OpenReviewClient(username='graham@mailseven.com', password='1234')
        note_id_1 = openreview_client.get_notes(invitation='TACL/-/Submission')[0].id
        reviews=openreview_client.get_notes(forum=note_id_1, invitation='TACL/Paper1/-/Review', sort= 'number:asc')

        for review in reviews:
            signature=review.signatures[0]
            rating_note=graham_client.post_note_edit(invitation=f'{signature}/-/Rating',
                signatures=["TACL/Paper1/Action_Editors"],
                note=Note(
                    content={
                        'rating': { 'value': 'Exceeds expectations' }
                    }
                )
            )
            helpers.await_queue_edit(openreview_client, edit_id=rating_note['id'])

        decision_note = graham_client.post_note_edit(invitation='TACL/Paper1/-/Decision',
            signatures=["TACL/Paper1/Action_Editors"],
            note=Note(
                content={
                    'claims_and_evidence': { 'value': 'Accept as is' },
                    'audience': { 'value': 'Accept as is' },
                    'recommendation': { 'value': 'Accept as is' },
                    'comment': { 'value': 'This is a nice paper!' },
                    'certifications': { 'value': ['Featured Certification', 'Reproducibility Certification'] }
                }
            )
        )

        helpers.await_queue_edit(openreview_client, edit_id=decision_note['id'])

        decision_note = graham_client.get_note(decision_note['note']['id'])
        assert decision_note.readers == ["TACL/Editors_In_Chief", "TACL/Paper1/Action_Editors"]

        ## EIC approves the decision
        approval_note = brian_client.post_note_edit(invitation='TACL/Paper1/-/Decision_Approval',
                            signatures=['TACL/Editors_In_Chief'],
                            note=Note(
                                content= {
                                    'approval': { 'value': 'I approve the AE\'s decision.' },
                                    'comment_to_the_AE': { 'value': 'I agree with the AE' }
                                }
                            ))

        helpers.await_queue_edit(openreview_client, edit_id=approval_note['id'])


        decision_note = brian_client.get_note(decision_note.id)
        assert decision_note.readers == ['TACL/Editors_In_Chief', 'TACL/Paper1/Action_Editors', 'TACL/Paper1/Reviewers', 'TACL/Paper1/Authors']
        assert decision_note.nonreaders == []

    def test_camera_ready_revision(self, journal, openreview_client, helpers):

        test_client = OpenReviewClient(username='test@mail.com', password='1234')
        graham_client = OpenReviewClient(username='graham@mailseven.com', password='1234')
        note_id_1 = openreview_client.get_notes(invitation='TACL/-/Submission')[0].id
        assert openreview_client.get_invitation("TACL/Paper1/-/Camera_Ready_Revision")

        ## post a revision
        revision_note = test_client.post_note_edit(invitation='TACL/Paper1/-/Camera_Ready_Revision',
            signatures=["TACL/Paper1/Authors"],
            note=Note(
                content={
                    'title': { 'value': 'Paper title VERSION 2' },
                    'authors': { 'value': ['Melisa Andersen', 'SomeFirstName User'] },
                    'authorids': { 'value': ['~Melisa_Andersen1', '~SomeFirstName_User1'] },
                    'abstract': { 'value': 'Paper abstract' },
                    'pdf': {'value': '/pdf/' + 'p' * 40 +'.pdf' },
                    'supplementary_material': { 'value': '/attachment/' + 's' * 40 +'.zip'},
                    'competing_interests': { 'value': 'None beyond the authors normal conflict of interests'},
                    'human_subjects_reporting': { 'value': 'Not applicable'},
                    'video': { 'value': 'https://youtube.com/dfenxkw'}
                }
            )
        )

        helpers.await_queue_edit(openreview_client, edit_id=revision_note['id'])

        note = openreview_client.get_note(note_id_1)
        assert note
        assert note.forum == note_id_1
        assert note.replyto is None
        assert note.invitations == ['TACL/-/Submission', 'TACL/Paper1/-/Revision', 'TACL/-/Under_Review', 'TACL/-/Edit', 'TACL/Paper1/-/Camera_Ready_Revision']
        assert note.readers == ['TACL', 'TACL/Paper1/Action_Editors', 'TACL/Paper1/Reviewers', 'TACL/Paper1/Authors']
        assert note.writers == ['TACL', 'TACL/Paper1/Authors']
        assert note.signatures == ['TACL/Paper1/Authors']
        assert note.content['authorids']['value'] == ['~Melisa_Andersen1', '~SomeFirstName_User1']
        assert note.content['authors']['value'] == ['Melisa Andersen', 'SomeFirstName User']
        assert note.content['venue']['value'] == 'Decision pending for TACL'
        assert note.content['venueid']['value'] == 'TACL/Decision_Pending'
        assert note.content['title']['value'] == 'Paper title VERSION 2'
        assert note.content['abstract']['value'] == 'Paper abstract'

        ## AE verifies the camera ready revision
        verification_note = graham_client.post_note_edit(invitation='TACL/Paper1/-/Camera_Ready_Verification',
                            signatures=["TACL/Paper1/Action_Editors"],
                            note=Note(
                                signatures=["TACL/Paper1/Action_Editors"],
                                content= {
                                    'verification': { 'value': 'I confirm that camera ready manuscript complies with the TACL stylefile and, if appropriate, includes the minor revisions that were requested.' }
                                 }
                            ))

        helpers.await_queue_edit(openreview_client, edit_id=verification_note['id'])

        note = openreview_client.get_note(note_id_1)
        assert note
        assert note.forum == note_id_1
        assert note.replyto is None
        assert note.invitations == ['TACL/-/Submission', 'TACL/Paper1/-/Revision', 'TACL/-/Under_Review', 'TACL/-/Edit', 'TACL/Paper1/-/Camera_Ready_Revision', 'TACL/-/Accepted']
        assert note.readers == ['TACL', 'TACL/Paper1/Action_Editors', 'TACL/Paper1/Reviewers', 'TACL/Paper1/Authors']
        assert note.writers == ['TACL']
        assert note.signatures == ['TACL/Paper1/Authors']
        assert note.content['authorids']['value'] == ['~Melisa_Andersen1', '~SomeFirstName_User1']
        assert note.content['authors']['value'] == ['Melisa Andersen', 'SomeFirstName User']
        # Check with cArlos
        assert note.content['authorids'].get('readers') == ['TACL', 'TACL/Paper1/Action_Editors', 'TACL/Paper1/Authors']
        assert note.content['authors'].get('readers') == ['TACL', 'TACL/Paper1/Action_Editors', 'TACL/Paper1/Authors']
        assert note.content['venue']['value'] == 'Accepted by TACL'
        assert note.content['venueid']['value'] == 'TACL'
        assert note.content['title']['value'] == 'Paper title VERSION 2'
        assert note.content['abstract']['value'] == 'Paper abstract'
        assert note.content['_bibtex']['value'] == '''@article{
anonymous''' + str(datetime.datetime.fromtimestamp(note.cdate/1000).year) + '''paper,
title={Paper title {VERSION} 2},
author={Anonymous},
journal={Transactions of the Association for Computational Linguistics},
year={''' + str(datetime.datetime.today().year) + '''},
url={https://openreview.net/forum?id=''' + note_id_1 + '''},
note={Featured Certification, Reproducibility Certification}
}'''

        edits = openreview_client.get_note_edits(note.id)
        assert len(edits) == 6
        for edit in edits:
            assert edit.readers == ['TACL', 'TACL/Paper1/Action_Editors', 'TACL/Paper1/Reviewers', 'TACL/Paper1/Authors']

    def test_withdrawn_submission(self, journal, openreview_client, test_client, helpers):

        test_client = OpenReviewClient(username='test@mail.com', password='1234')
        brian_client = OpenReviewClient(username='brian@mail.com', password='1234')
        graham_client = OpenReviewClient(username='graham@mailseven.com', password='1234')


        ## Post the submission 2
        submission_note_2 = test_client.post_note_edit(invitation='TACL/-/Submission',
            signatures=['~SomeFirstName_User1'],
            note=Note(
                content={
                    'title': { 'value': 'Paper title 2' },
                    'abstract': { 'value': 'Paper abstract' },
                    'authors': { 'value': ['SomeFirstName User', 'Melisa Andersen']},
                    'authorids': { 'value': ['~SomeFirstName_User1', '~Melisa_Andersen1']},
                    'pdf': {'value': '/pdf/' + 'p' * 40 +'.pdf' },
                    'supplementary_material': { 'value': '/attachment/' + 's' * 40 +'.zip'},
                    'competing_interests': { 'value': 'None beyond the authors normal conflict of interests'},
                    'human_subjects_reporting': { 'value': 'Not applicable'}
                }
            ))

        helpers.await_queue_edit(openreview_client, edit_id=submission_note_2['id'])
        note_id_2=submission_note_2['note']['id']

        # Assign Action Editor
        paper_assignment_edge = brian_client.post_edge(openreview.Edge(invitation='TACL/Action_Editors/-/Assignment',
            readers=['TACL', 'TACL/Editors_In_Chief', '~Graham_Neubig1'],
            writers=['TACL', 'TACL/Editors_In_Chief'],
            signatures=['TACL/Editors_In_Chief'],
            head=note_id_2,
            tail='~Graham_Neubig1',
            weight=1
        ))

        helpers.await_queue_edit(openreview_client, edit_id=paper_assignment_edge.id)

        ## Accept the submission 2
        under_review_note = graham_client.post_note_edit(invitation= 'TACL/Paper2/-/Review_Approval',
                                    signatures=['TACL/Paper2/Action_Editors'],
                                    note=Note(content={
                                        'under_review': { 'value': 'Appropriate for Review' }
                                    }))

        helpers.await_queue_edit(openreview_client, edit_id=under_review_note['id'])

        ## Withdraw the submission 2
        withdraw_note = test_client.post_note_edit(invitation='TACL/Paper2/-/Withdrawal',
                                    signatures=['TACL/Paper2/Authors'],
                                    note=Note(
                                        content={
                                            'withdrawal_confirmation': { 'value': 'I have read and agree with the venue\'s withdrawal policy on behalf of myself and my co-authors.' },
                                        }
                                    ))

        helpers.await_queue_edit(openreview_client, edit_id=withdraw_note['id'])

        note = test_client.get_note(note_id_2)
        assert note
        assert note.invitations == ['TACL/-/Submission', 'TACL/-/Under_Review', 'TACL/-/Withdrawn']
        assert note.readers == ['TACL', 'TACL/Paper2/Action_Editors', 'TACL/Paper2/Reviewers', 'TACL/Paper2/Authors']
        assert note.writers == ['TACL', 'TACL/Paper2/Authors']
        assert note.signatures == ['TACL/Paper2/Authors']
        assert note.content['authorids']['value'] == ['~SomeFirstName_User1', '~Melisa_Andersen1']
        assert note.content['venue']['value'] == 'Withdrawn by Authors'
        assert note.content['venueid']['value'] == 'TACL/Withdrawn_Submission'
        assert note.content['_bibtex']['value'] == '''@article{
anonymous''' + str(datetime.datetime.fromtimestamp(note.cdate/1000).year) + '''paper,
title={Paper title 2},
author={Anonymous},
journal={Submitted to Transactions of the Association for Computational Linguistics},
year={''' + str(datetime.datetime.today().year) + '''},
url={https://openreview.net/forum?id=''' + note_id_2 + '''},
note={Withdrawn}
}'''

        helpers.await_queue_edit(openreview_client, invitation='TACL/-/Withdrawn')

        edits = openreview_client.get_note_edits(note.id)
        assert len(edits) == 3
        for edit in edits:
            assert edit.readers == ['TACL', 'TACL/Paper2/Action_Editors', 'TACL/Paper2/Reviewers', 'TACL/Paper2/Authors']

        invitations = openreview_client.get_invitations(replyForum=note_id_2, prefix='TACL/Paper2')
        assert len(invitations) == 1
        assert "TACL/Paper2/-/Official_Comment" in [i.id for i in invitations]
