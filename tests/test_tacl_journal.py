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

class TestJournal():


    @pytest.fixture(scope="class")
    def journal(self, openreview_client, helpers):
        super_id = 'openreview.net'
        support_group_id = super_id + '/Support'
        journal_request = JournalRequest(openreview_client, support_group_id)
        journal_request.setup_journal_request()

        ## Editors in Chief
        helpers.create_user('brian@mail.com', 'Brian', 'Roark')

        #post journal request form
        request_form = openreview_client.post_note_edit(invitation= support_group_id + '/-/Journal_Request',
            signatures = [support_group_id],
            note = Note(
                signatures = [support_group_id],
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
                            'assignment_delay': 0
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

        openreview_client.add_members_to_group('TACL/Reviewers', ['~David_Bensusan1', '~Carlos_Gardel1', '~Javier_Barden1'])

        return JournalRequest.get_journal(openreview_client, request_form['note']['id'])

    def test_submission(self, journal, openreview_client, test_client, helpers):

        test_client = OpenReviewClient(username='test@mail.com', password='1234')

        ## Post the submission 1
        submission_note_1 = test_client.post_note_edit(invitation='TACL/-/Submission',
            signatures=['~SomeFirstName_User1'],
            note=Note(
                content={
                    'title': { 'value': 'Paper title' },
                    'abstract': { 'value': 'Paper abstract' },
                    'authors': { 'value': ['SomeFirstName User', 'Melissa Bok']},
                    'authorids': { 'value': ['~SomeFirstName_User1', '~Melissa_Bok1']},
                    'pdf': {'value': '/pdf/' + 'p' * 40 +'.pdf' },
                    'supplementary_material': { 'value': '/attachment/' + 's' * 40 +'.zip'},
                    'competing_interests': { 'value': 'None beyond the authors normal conflict of interests'},
                    'human_subjects_reporting': { 'value': 'Not applicable'},
                    'submission_length': { 'value': 'Regular submission (no more than 12 pages of main content)'}
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
        assert author_group.members == ['~SomeFirstName_User1', '~Melissa_Bok1']
        assert openreview_client.get_group("TACL/Paper1/Reviewers")
        assert openreview_client.get_group("TACL/Paper1/Action_Editors")

        note = openreview_client.get_note(note_id_1)
        assert note
        assert note.invitations == ['TACL/-/Submission']
        assert note.readers == ['TACL', 'TACL/Paper1/Action_Editors', 'TACL/Paper1/Authors']
        assert note.writers == ['TACL', 'TACL/Paper1/Authors']
        assert note.signatures == ['TACL/Paper1/Authors']
        assert note.content['authorids']['value'] == ['~SomeFirstName_User1', '~Melissa_Bok1']
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
                    'pdf': { 'value': '/pdf/22234qweoiuweroi22234qweoiuweroi12345678.pdf' },
                    'submission_length': { 'value': 'Regular submission (no more than 12 pages of main content)'}
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
        assert note.content['authorids']['value'] == ['~SomeFirstName_User1', '~Melissa_Bok1']
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
        assert note.content['authorids']['value'] == ['~SomeFirstName_User1', '~Melissa_Bok1']
        assert note.content['venue']['value'] == 'Under review for TACL'
        assert note.content['venueid']['value'] == 'TACL/Under_Review'
        assert note.content['assigned_action_editor']['value'] == '~Graham_Neubig1'
        assert note.content['_bibtex']['value'] == '''@article{
anonymous''' + str(datetime.datetime.fromtimestamp(note.cdate/1000).year) + '''paper,
title={Paper title {UPDATED}},
author={Anonymous},
journal={Submitted to Transactions of the Association for Computational Linguistics},
year={2022},
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
                    'broader_impact_concerns': { 'value': 'broader_impact_concerns' }
                }
            )
        )        
