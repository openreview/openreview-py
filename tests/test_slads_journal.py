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

class TestSLADSJournal():


    @pytest.fixture(scope="class")
    def journal(self, openreview_client, helpers):

        eic_client=OpenReviewClient(username='ruiyan@mail.com', password=helpers.strong_password)
        eic_client.impersonate('SLADS/Editors_In_Chief')

        requests = openreview_client.get_notes(invitation='openreview.net/Support/-/Journal_Request', content={ 'venue_id': 'SLADS' })

        return JournalRequest.get_journal(eic_client, requests[0].id)

    def test_setup(self, openreview_client, request_page, selenium, helpers, journal_request):

        ## Editors in Chief
        helpers.create_user('ruiyan@mail.com', 'Ruiyan', 'Zhang')
        ce_client = helpers.create_user('ce@mailseven.com', 'Ce', 'Zhang')

        #post journal request form
        request_form = openreview_client.post_note_edit(invitation= 'openreview.net/Support/-/Journal_Request',
            signatures = ['openreview.net/Support'],
            note = Note(
                signatures = ['openreview.net/Support'],
                content = {
                    'official_venue_name': {'value': 'Statistical Learning and Data Science'},
                    'abbreviated_venue_name' : {'value': 'SLADS'},
                    'venue_id': {'value': 'SLADS'},
                    'contact_info': {'value': 'slads@scichina.com'},
                    'secret_key': {'value': '4567'},
                    'support_role': {'value': '~Ruiyan_Zhang1' },
                    'editors': {'value': ['~Ruiyan_Zhang1', '~Ce_Zhang1'] },
                    'website': {'value': 'data.mlr.press' },
                    'settings': {
                        'value': {
                            "submission_public": True,
                            "author_anonymity": True,
                            "eic_submission_notification": True,
                            "AE_anonymity": True,
                            "assignment_delay": 5,
                            "submission_name": "Submission",
                            "issn": "3051-3901",
                            "website_urls": {
                                "editorial_board": "http://slads.scichina.com/index.html",
                                "evaluation_criteria": "http://slads.scichina.com",
                                "reviewer_guide": "http://slads.scichina.com/referees_guideline.html",
                                "editorial_policies": "http://slads.scichina.com",
                                "faq": "http://slads.scichina.com"
                            },
                            "editors_email": "slads@scichina.com",
                            "skip_ac_recommendation": True,
                            "number_of_reviewers": 2,
                            "reviewers_max_papers": 6,
                            "ae_recommendation_period": 1,
                            "under_review_approval_period": 1,
                            "reviewer_assignment_period": 1,
                            "review_period": 6,
                            "discussion_period": 2,
                            "recommendation_period": 2,
                            "decision_period": 1,
                            "camera_ready_period": 4,
                            "camera_ready_verification_period": 1,
                            "archived_action_editors": True,
                            "expert_reviewers": False,
                            "submission_additional_fields": {
                                "submission_type": {
                                "order": 11,
                                "description": "Please select a category.",
                                "value": {
                                    "param": {
                                    "type": "string",
                                    "enum": [
                                        "Research Article",
                                        "Review",
                                        "Short Communication",
                                        "Perspective",
                                        "Special Issue on Frontiers in Statistical Learning: Data, Networks, and Knowledge Transfer"
                                    ],
                                    "input": "select"
                                    }
                                }
                                }
                            }
                            }
                    }
                }
            ))

        helpers.await_queue_edit(openreview_client, request_form['id'])


        ## Action Editors
        helpers.create_user('andrew@sladszero.com', 'Jiashun', 'Jin')

        openreview_client.add_members_to_group('SLADS/Action_Editors', '~Jiashun_Jin1')

        ## Reviewers
        helpers.create_user('david@sladsone.com', 'David', 'Box')
        helpers.create_user('javier@sladstwo.com', 'Javier', 'Bax')
        helpers.create_user('carlos@sladsthree.com', 'Carlos', 'Gex')

        ## Authors
        helpers.create_user('melisa@sladsfour.com', 'Melisa', 'Amex')

        openreview_client.add_members_to_group('SLADS/Reviewers', ['~David_Box1', '~Carlos_Gex1', '~Javier_Bax1'])


    def test_submission(self, journal, openreview_client, test_client, helpers):

        test_client = OpenReviewClient(username='test@mail.com', password=helpers.strong_password)

        ## Post the submission 1
        submission_note_1 = test_client.post_note_edit(invitation='SLADS/-/Submission',
            signatures=['~SomeFirstName_User1'],
            note=Note(
                content={
                    'title': { 'value': 'Paper title' },
                    'abstract': { 'value': 'Paper abstract' },
                    'authors': { 'value': ['SomeFirstName User', 'Melisa Amex']},
                    'authorids': { 'value': ['~SomeFirstName_User1', '~Melisa_Amex1']},
                    'pdf': {'value': '/pdf/' + 'p' * 40 +'.pdf' },
                    'supplementary_material': { 'value': '/attachment/' + 's' * 40 +'.zip'},
                    'competing_interests': { 'value': 'None beyond the authors normal conflict of interests'},
                    'human_subjects_reporting': { 'value': 'Not applicable'},
                    'submission_type': { 'value': 'Research Article' }
                }
            ))

        helpers.await_queue_edit(openreview_client, edit_id=submission_note_1['id'])
        note_id_1=submission_note_1['note']['id']

        messages = openreview_client.get_messages(to = 'melisa@sladsfour.com', subject = '[SLADS] New submission to SLADS: Paper title')
        assert len(messages) == 1
        assert messages[0]['content']['text'] == f'''Hi Melisa Amex,\n\nYour submission to SLADS has been received.\n\nSubmission Number: 1\n\nTitle: Paper title\n\nTo view the submission, click here: https://openreview.net/forum?id={note_id_1}\n\n\nPlease note that responding to this email will direct your reply to slads@scichina.com.\n'''
        
        messages = openreview_client.get_messages(to = 'test@mail.com', subject = '[SLADS] New submission to SLADS: Paper title')
        assert len(messages) == 1
        assert messages[0]['content']['text'] == f'''Hi SomeFirstName User,\n\nYour submission to SLADS has been received.\n\nSubmission Number: 1\n\nTitle: Paper title\n\nTo view the submission, click here: https://openreview.net/forum?id={note_id_1}\n\n\nPlease note that responding to this email will direct your reply to slads@scichina.com.\n'''

        messages = openreview_client.get_messages(to = 'ce@mailseven.com', subject = '[SLADS] New submission to SLADS: Paper title')
        assert len(messages) == 1
        assert messages[0]['content']['text'] == f'''Hi Ce Zhang,\n\nA new submission has been received for SLADS.\n\nTo view the submission, click here: https://openreview.net/forum?id={note_id_1}\n\n\nPlease note that responding to this email will direct your reply to slads@scichina.com.\n'''


        Journal.update_affinity_scores(openreview.api.OpenReviewClient(username='openreview.net', password=helpers.strong_password), support_group_id='openreview.net/Support')

        messages = openreview_client.get_messages(to = 'test@mail.com', subject = '[SLADS] Suggest candidate Action Editor for your new SLADS submission')
        assert len(messages) == 0
        assert not openreview.tools.get_invitation(openreview_client, 'SLADS/Paper1/Action_Editors/-/Recommendation')

        author_group=openreview_client.get_group("SLADS/Paper1/Authors")
        assert author_group
        assert author_group.members == ['~SomeFirstName_User1', '~Melisa_Amex1']
        assert openreview_client.get_group("SLADS/Paper1/Reviewers")
        ae_group = openreview_client.get_group("SLADS/Paper1/Action_Editors")
        assert ae_group.readers == ['SLADS', 'SLADS/Paper1/Action_Editors', 'SLADS/Paper1/Reviewers']

        note = openreview_client.get_note(note_id_1)
        assert note
        assert note.invitations == ['SLADS/-/Submission']
        assert note.readers == ['SLADS', 'SLADS/Paper1/Action_Editors', 'SLADS/Paper1/Authors']
        assert note.writers == ['SLADS', 'SLADS/Paper1/Authors']
        assert note.signatures == ['SLADS/Paper1/Authors']
        assert note.content['authorids']['value'] == ['~SomeFirstName_User1', '~Melisa_Amex1']
        assert note.content['venue']['value'] == 'Submitted to SLADS'
        assert note.content['venueid']['value'] == 'SLADS/Submitted'


    def test_review_approval(self, journal, openreview_client, helpers):

        ce_client = OpenReviewClient(username='ce@mailseven.com', password=helpers.strong_password)
        andrew_client = OpenReviewClient(username='andrew@sladszero.com', password=helpers.strong_password)
        note_id_1 = openreview_client.get_notes(invitation='SLADS/-/Submission')[0].id

        # Assign Action Editor
        paper_assignment_edge = ce_client.post_edge(openreview.Edge(invitation='SLADS/Action_Editors/-/Assignment',
            readers=['SLADS', 'SLADS/Editors_In_Chief', '~Jiashun_Jin1'],
            writers=['SLADS', 'SLADS/Editors_In_Chief'],
            signatures=['SLADS/Editors_In_Chief'],
            head=note_id_1,
            tail='~Jiashun_Jin1',
            weight=1
        ))

        helpers.await_queue_edit(openreview_client, edit_id=paper_assignment_edge.id)

        ae_group = ce_client.get_group('SLADS/Paper1/Action_Editors')
        assert ae_group.members == ['~Jiashun_Jin1']

        messages = journal.client.get_messages(to = 'andrew@sladszero.com', subject = '[SLADS] Assignment to new SLADS submission 1: Paper title')
        assert len(messages) == 1
        assert messages[0]['content']['text'] == f'''Hi Jiashun Jin,

With this email, we request that you manage the review process for a new SLADS submission "1: Paper title".

As a reminder, SLADS Action Editors (AEs) are **expected to accept all AE requests** to manage submissions that fall within your expertise and quota. Reasonable exceptions are 1) situations where exceptional personal circumstances (e.g. vacation, health problems) render you incapable of fully performing your AE duties or 2) you have a conflict of interest with one of the authors. If any such exception applies to you, contact us at slads@scichina.com.

Your first task is to make sure the submitted preprint is appropriate for SLADS and respects our submission guidelines. Clear cases of desk rejection include submissions that are not anonymized, submissions that do not use the unmodified SLADS stylefile and submissions that clearly overlap with work already published in proceedings (or currently under review for publication). If you suspect but are unsure about whether a submission might need to be desk rejected for any other reasons (e.g. lack of fit with the scope of SLADS or lack of technical depth), please email us.

Please follow this link to perform this task: https://openreview.net/forum?id={note_id_1}&invitationId=SLADS/Paper1/-/Review_Approval

If you think the submission can continue through SLADS's review process, click the button "Under Review". Otherwise, click on "Desk Reject". Once the submission has been confirmed, then the review process will begin, and your next step will be to assign 2 reviewers to the paper. You will get a follow up email when OpenReview is ready for you to assign these 2 reviewers.

We thank you for your essential contribution to SLADS!

The SLADS Editors-in-Chief


Please note that responding to this email will direct your reply to slads@scichina.com.
'''

        andrew_paper1_anon_groups = andrew_client.get_groups(prefix=f'SLADS/Paper1/Action_Editor_.*', signatory='~Jiashun_Jin1')
        assert len(andrew_paper1_anon_groups) == 1
        graham_paper1_anon_group = andrew_paper1_anon_groups[0]         

        ## Accept the submission 1
        under_review_note = andrew_client.post_note_edit(invitation= 'SLADS/Paper1/-/Review_Approval',
                                    signatures=[graham_paper1_anon_group.id],
                                    note=Note(content={
                                        'under_review': { 'value': 'Appropriate for Review' }
                                    }))

        helpers.await_queue_edit(openreview_client, edit_id=under_review_note['id'])

        note = andrew_client.get_note(note_id_1)
        assert note
        assert note.invitations == ['SLADS/-/Submission', 'SLADS/-/Edit', 'SLADS/-/Under_Review']
        assert note.readers == ['everyone']
        assert note.writers == ['SLADS', 'SLADS/Paper1/Authors']
        assert note.signatures == ['SLADS/Paper1/Authors']
        assert note.content['authorids']['value'] == ['~SomeFirstName_User1', '~Melisa_Amex1']
        assert note.content['venue']['value'] == 'Under review for SLADS'
        assert note.content['venueid']['value'] == 'SLADS/Under_Review'
        assert note.content['assigned_action_editor']['value'] == '~Jiashun_Jin1'
        assert note.content['assigned_action_editor']['readers'] == ['SLADS', 'SLADS/Paper1/Action_Editors', 'SLADS/Paper1/Reviewers']
        assert note.content['_bibtex']['value'] == '''@article{
anonymous''' + str(datetime.datetime.fromtimestamp(note.cdate/1000).year) + '''paper,
title={Paper title},
author={Anonymous},
journal={Submitted to Statistical Learning and Data Science},
year={''' + str(datetime.datetime.today().year) + '''},
url={https://openreview.net/forum?id=''' + note_id_1 + '''},
note={Under review}
}'''

        edits = openreview_client.get_note_edits(note.id, invitation='SLADS/-/Under_Review')
        helpers.await_queue_edit(openreview_client, edit_id=edits[0].id)

        invitations = openreview_client.get_invitations(prefix='SLADS/Paper', replyForum=note_id_1)
        assert "SLADS/Paper1/-/Revision"  in [i.id for i in invitations]
        assert "SLADS/Paper1/-/Withdrawal"  in [i.id for i in invitations]
        assert "SLADS/Paper1/-/Review" in [i.id for i in invitations]
        assert "SLADS/Paper1/-/Volunteer_to_Review" in [i.id for i in invitations]
        assert "SLADS/Paper1/-/Public_Comment" in [i.id for i in invitations]
        assert "SLADS/Paper1/-/Official_Comment" in [i.id for i in invitations]
        assert "SLADS/Paper1/-/Moderation" in [i.id for i in invitations]

        edits = openreview_client.get_note_edits(note.id)
        assert len(edits) == 3
        for edit in edits:
            assert edit.readers == ['everyone']

    def test_review(self, journal, openreview_client, helpers):

        ce_client = OpenReviewClient(username='ce@mailseven.com', password=helpers.strong_password)
        andrew_client = OpenReviewClient(username='andrew@sladszero.com', password=helpers.strong_password)
        note_id_1 = openreview_client.get_notes(invitation='SLADS/-/Submission')[0].id

        david_client = OpenReviewClient(username='david@sladsone.com', password=helpers.strong_password)
        carlos_client = OpenReviewClient(username='carlos@sladsthree.com', password=helpers.strong_password)

        andrew_paper1_anon_groups = andrew_client.get_groups(prefix=f'SLADS/Paper1/Action_Editor_.*', signatory='~Jiashun_Jin1')
        assert len(andrew_paper1_anon_groups) == 1
        graham_paper1_anon_group = andrew_paper1_anon_groups[0]

        # add David Belanger again
        paper_assignment_edge = paper_assignment_edge = andrew_client.post_edge(openreview.Edge(invitation='SLADS/Reviewers/-/Assignment',
            readers=["SLADS", "SLADS/Paper1/Action_Editors", '~David_Box1'],
            nonreaders=["SLADS/Paper1/Authors"],
            writers=["SLADS", "SLADS/Paper1/Action_Editors"],
            signatures=[graham_paper1_anon_group.id],
            head=note_id_1,
            tail='~David_Box1',
            weight=1
        ))

        helpers.await_queue_edit(openreview_client, edit_id=paper_assignment_edge.id)

        ## Carlos Gardel
        paper_assignment_edge = andrew_client.post_edge(openreview.Edge(invitation='SLADS/Reviewers/-/Assignment',
            readers=["SLADS", "SLADS/Paper1/Action_Editors", '~Carlos_Gex1'],
            nonreaders=["SLADS/Paper1/Authors"],
            writers=["SLADS", "SLADS/Paper1/Action_Editors"],
            signatures=[graham_paper1_anon_group.id],
            head=note_id_1,
            tail='~Carlos_Gex1',
            weight=1
        ))

        helpers.await_queue_edit(openreview_client, edit_id=paper_assignment_edge.id)

        david_anon_groups=david_client.get_groups(prefix='SLADS/Paper1/Reviewer_.*', signatory='~David_Box1')
        assert len(david_anon_groups) == 1

        ## Post a review edit
        david_review_note = david_client.post_note_edit(invitation='SLADS/Paper1/-/Review',
            signatures=[david_anon_groups[0].id],
            note=Note(
                content={
                    'summary_of_contributions': { 'value': 'summary_of_contributions' },
                    'strengths_and_weaknesses': { 'value': 'strengths_and_weaknesses' },
                    'requested_changes': { 'value': 'requested_changes' },
                    'broader_impact_concerns': { 'value': 'broader_impact_concerns' },
                    'claims_and_evidence': { 'value': 'Yes' },
                    'audience': { 'value': 'Yes' },
                }
            )
        )

        helpers.await_queue_edit(openreview_client, edit_id=david_review_note['id'], process_index=0) ## process and post process
        helpers.await_queue_edit(openreview_client, edit_id=david_review_note['id'], process_index=1) ## process and post process

        carlos_anon_groups=carlos_client.get_groups(prefix='SLADS/Paper1/Reviewer_.*', signatory='~Carlos_Gex1')
        assert len(carlos_anon_groups) == 1

        ## Post a review edit
        carlos_review_note = carlos_client.post_note_edit(invitation='SLADS/Paper1/-/Review',
            signatures=[carlos_anon_groups[0].id],
            note=Note(
                content={
                    'summary_of_contributions': { 'value': 'summary_of_contributions' },
                    'strengths_and_weaknesses': { 'value': 'strengths_and_weaknesses' },
                    'requested_changes': { 'value': 'requested_changes' },
                    'broader_impact_concerns': { 'value': 'broader_impact_concerns' },
                    'claims_and_evidence': { 'value': 'Yes' },
                    'audience': { 'value': 'Yes' },
                }
            )
        )

        helpers.await_queue_edit(openreview_client, edit_id=carlos_review_note['id'], process_index=0) ## process and post process
        helpers.await_queue_edit(openreview_client, edit_id=carlos_review_note['id'], process_index=1) ## process and post process


        messages = openreview_client.get_messages(to = 'test@mail.com', subject = '[SLADS] Reviewer responses and discussion for your SLADS submission')
        assert len(messages) == 1
        assert messages[0]['content']['text'] ==f'''Hi SomeFirstName User,\n\nNow that 2 reviews have been submitted for your submission  1: Paper title, all reviews have been made public. If you haven't already, please read the reviews and start engaging with the reviewers to attempt to address any concern they may have about your submission.\n\nYou will have 2 weeks to interact with the reviewers, including uploading any revisions. To maximize the period of interaction and discussion, please respond as soon as possible. Additionally, revising the submission PDF in light of reviewer feedback is possible and encouraged (consider making changes in a different color to help reviewers), in order to give reviewers maximum confidence that their concerns are addressed. The reviewers will be using this time period to hear from you and gather all the information they need. In about 2 weeks ({(datetime.datetime.now() + datetime.timedelta(weeks = 2)).strftime("%b %d")}), and no later than 4 weeks ({(datetime.datetime.now() + datetime.timedelta(weeks = 4)).strftime("%b %d")}), reviewers will submit their formal decision recommendation to the Action Editor in charge of your submission.\n\nVisit the following link to respond to the reviews: https://openreview.net/forum?id={note_id_1}\n\nFor more details and guidelines on the SLADS review process, visit data.mlr.press.\n\nThe SLADS Editors-in-Chief\n\n\nPlease note that responding to this email will direct your reply to slads@scichina.com.\n'''
        assert messages[0]['content']['replyTo'] == 'slads@scichina.com'


        ce_client.post_invitation_edit(
            invitations='SLADS/-/Edit',
            signatures=['SLADS'],
            invitation=openreview.api.Invitation(id='SLADS/Paper1/-/Official_Recommendation',
                cdate=openreview.tools.datetime_millis(datetime.datetime.now()) + 1000,
                signatures=['SLADS/Editors_In_Chief']
            )
        )

        helpers.await_queue_edit(openreview_client, edit_id='SLADS/Paper1/-/Official_Recommendation-0-0')

        ## Check emails being sent to Reviewers and AE
        messages = journal.client.get_messages(to='test@mail.com', subject = '[SLADS] Discussion period ended for SLADS submission 1: Paper title')
        assert len(messages) == 1
        assert messages[0]['content']['replyTo'] == 'slads@scichina.com'
        assert messages[0]['content']['text'] == f'''Hi SomeFirstName User,\n\nThe discussion period has ended and the reviewers will submit their recommendations, after which the AE will enter their final recommendation.\n\nThe SLADS Editors-in-Chief\n\n\nPlease note that responding to this email will direct your reply to slads@scichina.com.\n'''