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

class TestDMLRJournal():


    @pytest.fixture(scope="class")
    def journal(self, openreview_client, helpers):

        eic_client=OpenReviewClient(username='merve@mail.com', password=helpers.strong_password)
        eic_client.impersonate('DMLR/Editors_In_Chief')

        requests = openreview_client.get_notes(invitation='openreview.net/Support/-/Journal_Request', content={ 'venue_id': 'DMLR' })

        return JournalRequest.get_journal(eic_client, requests[0].id)

    def test_setup(self, openreview_client, request_page, selenium, helpers, journal_request):

        ## Editors in Chief
        helpers.create_user('merve@mail.com', 'Merve', 'Gürel')
        ce_client = helpers.create_user('ce@mailseven.com', 'Ce', 'Zhang')

        #post journal request form
        request_form = openreview_client.post_note_edit(invitation= 'openreview.net/Support/-/Journal_Request',
            signatures = ['openreview.net/Support'],
            note = Note(
                signatures = ['openreview.net/Support'],
                content = {
                    'official_venue_name': {'value': 'Journal of Data-centric Machine Learning Research'},
                    'abbreviated_venue_name' : {'value': 'DMLR'},
                    'venue_id': {'value': 'DMLR'},
                    'contact_info': {'value': 'dmlr@jmlr.org'},
                    'secret_key': {'value': '4567'},
                    'support_role': {'value': '~Merve_Gürel1' },
                    'editors': {'value': ['dmlr@jmlr.org', '~Ce_Zhang1'] },
                    'website': {'value': 'data.mlr.press' },
                    'settings': {
                        'value': {
                            "submission_public": False,
                            "author_anonymity": False,
                            "eic_submission_notification": True,
                            "assignment_delay": 5,
                            "submission_name": "Submission",
                            "certifications": [
                                "Featured Certification",
                                "Reproducibility Certification",
                                "Survey Certification"
                            ],
                            "eic_certifications": [
                                "Outstanding Certification"
                            ],
                            "issn": "XXXX-XXXX",
                            "website_urls": {
                                "evaluation_criteria": "https://data.mlr.press/acceptance-criteria",
                                "reviewer_guide": "https://data.mlr.press/reviewer-guidelines",
                                "editorial_policies": "https://data.mlr.press/editor-guidelines",
                                "faq": "https://data.mlr.press/"
                            },
                            "editors_email": "dmlr@jmlr.org",
                            "skip_ac_recommendation": True,
                            "number_of_reviewers": 3,
                            "reviewers_max_papers": 6,
                            "ae_recommendation_period": 1,
                            "under_review_approval_period": 2,
                            "reviewer_assignment_period": 2,
                            "review_period": 4,
                            "discussion_period": 2,
                            "recommendation_period": 2,
                            "decision_period": 2,
                            "camera_ready_period": 2,
                            "camera_ready_verification_period": 1,
                            "archived_action_editors": True,
                            "expert_reviewers": True,
                            "submission_additional_fields": {
                                "keywords": {
                                "value": {
                                    "param": {
                                    "type": "string",
                                    "regex": "(^$)|[^;,\\n]+(,[^,\\n]+)*",
                                    "optional": True,
                                    "deletable": True
                                    }
                                },
                                "description": "Comma separated list of keywords.",
                                "order": 6
                                }
                            },
                            "review_additional_fields": {
                                "summary_of_contributions": {
                                "order": 1,
                                "description": "Brief description, in the reviewer's words, of the contributions and new knowledge presented by the submission. Add formatting using Markdown and formulas using LaTeX. For more information see https://openreview.net/faq.",
                                "value": {
                                    "param": {
                                    "maxLength": 200000,
                                    "input": "textarea",
                                    "type": "string",
                                    "markdown": True
                                    }
                                }
                                },
                                "strengths_and_weaknesses": {
                                "order": 2,
                                "description": "Describe the strengths of the submission, considering significance of the contribution, relation to prior work, relevance to the broader research community, quality of the research, clarity of paper, and ethical and social implications. Add formatting using Markdown and formulas using LaTeX. For more information see https://openreview.net/faq.",
                                "value": {
                                    "param": {
                                    "maxLength": 200000,
                                    "input": "textarea",
                                    "type": "string",
                                    "markdown": True,
                                    "fieldName": "Strengths"
                                    }
                                }
                                },
                                "limitations": {
                                "order": 3,
                                "description": "List of weaknesses and limitations (if any) that you think require attention from the authors. Add formatting using Markdown and formulas using LaTeX. For more information see https://openreview.net/faq.",
                                "value": {
                                    "param": {
                                    "maxLength": 200000,
                                    "input": "textarea",
                                    "type": "string",
                                    "markdown": True
                                    }
                                }
                                },
                                "claims_and_evidence": {
                                "order": 4,
                                "description": "Are the claims made in the submission supported by accurate, convincing and clear evidence? (see DMLR's acceptance criteria at https://data.mlr.press/acceptance-criteria)",
                                "value": {
                                    "param": {
                                    "maxLength": 200000,
                                    "input": "textarea",
                                    "type": "string",
                                    "markdown": True
                                    }
                                }
                                },
                                "extended_submissions": {
                                "order": 5,
                                "description": "If the submission is extended version of a previously published work, comment whether it meets the eligibility criteria at https://data.mlr.press/acceptance-criteria.",
                                "value": {
                                    "param": {
                                    "maxLength": 200000,
                                    "input": "textarea",
                                    "type": "string",
                                    "markdown": True
                                    }
                                }
                                },
                                "datasets_and_benchmarks": {
                                "order": 7,
                                "description": "For datasets, is there sufficient detail on data collection and organization, availability and maintenance, and ethical and responsible use? Note that dataset submissions should include documentation and intended uses; a URL for reviewer access to the dataset; and a hosting, licensing and maintenance plan. For benchmarks, is there sufficient detail to support reproducibility?",
                                "value": {
                                    "param": {
                                    "maxLength": 200000,
                                    "input": "textarea",
                                    "type": "string",
                                    "markdown": True
                                    }
                                }
                                },
                                "recommendation": {
                                "order": 9,
                                "value": {
                                    "param": {
                                    "type": "string",
                                    "enum": [
                                        "4: Accept.",
                                        "3: Leaning to Accept.",
                                        "2: Leaning to Reject",
                                        "1: Reject."
                                    ],
                                    "input": "radio"
                                    }
                                }
                                },
                                "confidence": {
                                "order": 10,
                                "value": {
                                    "param": {
                                    "type": "string",
                                    "enum": [
                                        "3: You are very confident in your assessment.",
                                        "2: You are fairly confident in your assessment.",
                                        "1: You are willing to defend your assessment, but it is quite likely that you did not understand central parts of the submission or that you are unfamiliar with some pieces of related work."
                                    ],
                                    "input": "radio"
                                    }
                                }
                                }
                            },
                            "official_recommendation_additional_fields": {
                                "claims_and_evidence": None,
                                "audience": None,
                                "decision_recommendation": None,
                                "certification_recommendations": None,
                                "recommendation_confirmation": {
                                    "order": 1,
                                    "description": "Confirm you updated your review after rebuttal",
                                    "value": {
                                        "param": {
                                            "type": "string",
                                            "enum": ["Yes"],
                                            "input": "checkbox"
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
        helpers.create_user('andrew@dmlrzero.com', 'Andrew', 'Ng')

        openreview_client.add_members_to_group('DMLR/Action_Editors', '~Andrew_Ng1')

        ## Reviewers
        helpers.create_user('david@dmlrone.com', 'David', 'Bo')
        helpers.create_user('javier@dmlrtwo.com', 'Javier', 'Ba')
        helpers.create_user('carlos@dmlrthree.com', 'Carlos', 'Ge')

        ## Authors
        helpers.create_user('melisa@dmlrfour.com', 'Melisa', 'Ane')

        openreview_client.add_members_to_group('DMLR/Reviewers', ['~David_Bo1', '~Carlos_Ge1', '~Javier_Ba1'])

        ce_client.post_group_edit(
            invitation='DMLR/-/Edit',
            signatures=['DMLR/Editors_In_Chief'],
            group=openreview.api.Group(
                id='DMLR/Reviewers',
                content={
                    "official_recommendation_starts_email_template_script": {
                        'value': '''Hi {{{{fullname}}}},

Thank you for submitting your review and engaging with the authors of {short_name} submission "{submission_number}: {submission_title}".

You may now submit your official recommendation for the submission confirming you updated the review. Before doing so, make sure you have sufficiently discussed with the authors (and possibly the other reviewers and AE) any concerns you may have about the submission.

We ask that you submit your recommendation within {recommendation_period_length} weeks ({recommendation_duedate}). To do so, please follow this link: {invitation_url}

For more details and guidelines on performing your review, visit {website}.

We thank you for your essential contribution to {short_name}!

The {short_name} Editors-in-Chief
note: replies to this email will go to the AE, {assigned_action_editor}.
'''
                    }
                }
            )
        )


    def test_submission(self, journal, openreview_client, test_client, helpers):

        test_client = OpenReviewClient(username='test@mail.com', password=helpers.strong_password)

        ## Post the submission 1
        submission_note_1 = test_client.post_note_edit(invitation='DMLR/-/Submission',
            signatures=['~SomeFirstName_User1'],
            note=Note(
                content={
                    'title': { 'value': 'Paper title' },
                    'abstract': { 'value': 'Paper abstract' },
                    'authors': { 'value': ['SomeFirstName User', 'Melisa Ane']},
                    'authorids': { 'value': ['~SomeFirstName_User1', '~Melisa_Ane1']},
                    'pdf': {'value': '/pdf/' + 'p' * 40 +'.pdf' },
                    'supplementary_material': { 'value': '/attachment/' + 's' * 40 +'.zip'},
                    'competing_interests': { 'value': 'None beyond the authors normal conflict of interests'},
                    'human_subjects_reporting': { 'value': 'Not applicable'}
                }
            ))

        helpers.await_queue_edit(openreview_client, edit_id=submission_note_1['id'])
        note_id_1=submission_note_1['note']['id']

        messages = openreview_client.get_messages(to = 'ce@mailseven.com', subject = '[DMLR] New submission to DMLR: Paper title')
        assert len(messages) == 1
        assert messages[0]['content']['text'] == f'''Hi Ce Zhang,\n\nA new submission has been received for DMLR.\n\nTo view the submission, click here: https://openreview.net/forum?id={note_id_1}\n'''


        Journal.update_affinity_scores(openreview.api.OpenReviewClient(username='openreview.net', password=helpers.strong_password), support_group_id='openreview.net/Support')

        messages = openreview_client.get_messages(to = 'test@mail.com', subject = '[DMLR] Suggest candidate Action Editor for your new DMLR submission')
        assert len(messages) == 0
        assert not openreview.tools.get_invitation(openreview_client, 'DMLR/Paper1/Action_Editors/-/Recommendation')

        author_group=openreview_client.get_group("DMLR/Paper1/Authors")
        assert author_group
        assert author_group.members == ['~SomeFirstName_User1', '~Melisa_Ane1']
        assert openreview_client.get_group("DMLR/Paper1/Reviewers")
        assert openreview_client.get_group("DMLR/Paper1/Action_Editors")

        note = openreview_client.get_note(note_id_1)
        assert note
        assert note.invitations == ['DMLR/-/Submission']
        assert note.readers == ['DMLR', 'DMLR/Paper1/Action_Editors', 'DMLR/Paper1/Authors']
        assert note.writers == ['DMLR', 'DMLR/Paper1/Authors']
        assert note.signatures == ['DMLR/Paper1/Authors']
        assert note.content['authorids']['value'] == ['~SomeFirstName_User1', '~Melisa_Ane1']
        assert note.content['venue']['value'] == 'Submitted to DMLR'
        assert note.content['venueid']['value'] == 'DMLR/Submitted'


    def test_review_approval(self, journal, openreview_client, helpers):

        ce_client = OpenReviewClient(username='ce@mailseven.com', password=helpers.strong_password)
        andrew_client = OpenReviewClient(username='andrew@dmlrzero.com', password=helpers.strong_password)
        note_id_1 = openreview_client.get_notes(invitation='DMLR/-/Submission')[0].id

        # Assign Action Editor
        paper_assignment_edge = ce_client.post_edge(openreview.Edge(invitation='DMLR/Action_Editors/-/Assignment',
            readers=['DMLR', 'DMLR/Editors_In_Chief', '~Andrew_Ng1'],
            writers=['DMLR', 'DMLR/Editors_In_Chief'],
            signatures=['DMLR/Editors_In_Chief'],
            head=note_id_1,
            tail='~Andrew_Ng1',
            weight=1
        ))

        helpers.await_queue_edit(openreview_client, edit_id=paper_assignment_edge.id)

        ae_group = ce_client.get_group('DMLR/Paper1/Action_Editors')
        assert ae_group.members == ['~Andrew_Ng1']

        messages = journal.client.get_messages(to = 'andrew@dmlrzero.com', subject = '[DMLR] Assignment to new DMLR submission 1: Paper title')
        assert len(messages) == 1
        assert messages[0]['content']['text'] == f'''Hi Andrew Ng,

With this email, we request that you manage the review process for a new DMLR submission "1: Paper title".

As a reminder, DMLR Action Editors (AEs) are **expected to accept all AE requests** to manage submissions that fall within your expertise and quota. Reasonable exceptions are 1) situations where exceptional personal circumstances (e.g. vacation, health problems) render you incapable of fully performing your AE duties or 2) you have a conflict of interest with one of the authors. If any such exception applies to you, contact us at dmlr@jmlr.org.

Your first task is to make sure the submitted preprint is appropriate for DMLR and respects our submission guidelines. Clear cases of desk rejection include submissions that are not anonymized, submissions that do not use the unmodified DMLR stylefile and submissions that clearly overlap with work already published in proceedings (or currently under review for publication). If you suspect but are unsure about whether a submission might need to be desk rejected for any other reasons (e.g. lack of fit with the scope of DMLR or lack of technical depth), please email us.

Please follow this link to perform this task: https://openreview.net/forum?id={note_id_1}&invitationId=DMLR/Paper1/-/Review_Approval

If you think the submission can continue through DMLR's review process, click the button "Under Review". Otherwise, click on "Desk Reject". Once the submission has been confirmed, then the review process will begin, and your next step will be to assign 3 reviewers to the paper. You will get a follow up email when OpenReview is ready for you to assign these 3 reviewers.

We thank you for your essential contribution to DMLR!

The DMLR Editors-in-Chief
'''

        andrew_paper1_anon_groups = andrew_client.get_groups(prefix=f'DMLR/Paper1/Action_Editor_.*', signatory='~Andrew_Ng1')
        assert len(andrew_paper1_anon_groups) == 1
        graham_paper1_anon_group = andrew_paper1_anon_groups[0]         

        ## Accept the submission 1
        under_review_note = andrew_client.post_note_edit(invitation= 'DMLR/Paper1/-/Review_Approval',
                                    signatures=[graham_paper1_anon_group.id],
                                    note=Note(content={
                                        'under_review': { 'value': 'Appropriate for Review' }
                                    }))

        helpers.await_queue_edit(openreview_client, edit_id=under_review_note['id'])

        note = andrew_client.get_note(note_id_1)
        assert note
        assert note.invitations == ['DMLR/-/Submission', 'DMLR/-/Under_Review']
        assert note.readers == ['DMLR', 'DMLR/Action_Editors', 'DMLR/Paper1/Reviewers', 'DMLR/Paper1/Authors']
        assert note.writers == ['DMLR', 'DMLR/Paper1/Authors']
        assert note.signatures == ['DMLR/Paper1/Authors']
        assert note.content['authorids']['value'] == ['~SomeFirstName_User1', '~Melisa_Ane1']
        assert note.content['venue']['value'] == 'Under review for DMLR'
        assert note.content['venueid']['value'] == 'DMLR/Under_Review'
        assert note.content['assigned_action_editor']['value'] == '~Andrew_Ng1'
        assert note.content['_bibtex']['value'] == '''@article{
anonymous''' + str(datetime.datetime.fromtimestamp(note.cdate/1000).year) + '''paper,
title={Paper title},
author={Anonymous},
journal={Submitted to Journal of Data-centric Machine Learning Research},
year={''' + str(datetime.datetime.today().year) + '''},
url={https://openreview.net/forum?id=''' + note_id_1 + '''},
note={Under review}
}'''

        edits = openreview_client.get_note_edits(note.id, invitation='DMLR/-/Under_Review')
        helpers.await_queue_edit(openreview_client, edit_id=edits[0].id)

        invitations = openreview_client.get_invitations(prefix='DMLR/Paper', replyForum=note_id_1)
        assert "DMLR/Paper1/-/Revision"  in [i.id for i in invitations]
        assert "DMLR/Paper1/-/Withdrawal"  in [i.id for i in invitations]
        assert "DMLR/Paper1/-/Review" in [i.id for i in invitations]
        assert "DMLR/Paper1/-/Volunteer_to_Review" not in [i.id for i in invitations]
        assert "DMLR/Paper1/-/Public_Comment" not in [i.id for i in invitations]
        assert "DMLR/Paper1/-/Official_Comment" in [i.id for i in invitations]
        assert "DMLR/Paper1/-/Moderation" not in [i.id for i in invitations]

        edits = openreview_client.get_note_edits(note.id)
        assert len(edits) == 2
        for edit in edits:
            assert edit.readers == ['DMLR', 'DMLR/Action_Editors', 'DMLR/Paper1/Reviewers', 'DMLR/Paper1/Authors']

    def test_review(self, journal, openreview_client, helpers):

        ce_client = OpenReviewClient(username='ce@mailseven.com', password=helpers.strong_password)
        andrew_client = OpenReviewClient(username='andrew@dmlrzero.com', password=helpers.strong_password)
        note_id_1 = openreview_client.get_notes(invitation='DMLR/-/Submission')[0].id

        david_client = OpenReviewClient(username='david@dmlrone.com', password=helpers.strong_password)
        carlos_client = OpenReviewClient(username='carlos@dmlrthree.com', password=helpers.strong_password)
        javier_client = OpenReviewClient(username='javier@dmlrtwo.com', password=helpers.strong_password)

        andrew_paper1_anon_groups = andrew_client.get_groups(prefix=f'DMLR/Paper1/Action_Editor_.*', signatory='~Andrew_Ng1')
        assert len(andrew_paper1_anon_groups) == 1
        graham_paper1_anon_group = andrew_paper1_anon_groups[0]

        # add David Belanger again
        paper_assignment_edge = andrew_client.post_edge(openreview.Edge(invitation='DMLR/Reviewers/-/Assignment',
            readers=["DMLR", "DMLR/Paper1/Action_Editors", '~David_Bo1'],
            nonreaders=["DMLR/Paper1/Authors"],
            writers=["DMLR", "DMLR/Paper1/Action_Editors"],
            signatures=[graham_paper1_anon_group.id],
            head=note_id_1,
            tail='~David_Bo1',
            weight=1
        ))

         # wait for process function delay (5 seconds) and check email has been sent
        time.sleep(6)
        messages = journal.client.get_messages(to = 'david@dmlrone.com', subject = '[DMLR] Assignment to review new DMLR submission 1: Paper title')
        assert len(messages) == 1
        assert messages[0]['content']['text'] == f'''Hi David Bo,

With this email, we request that you submit, within 4 weeks ({(datetime.datetime.utcnow() + datetime.timedelta(weeks = 4)).strftime("%b %d")}) a review for your newly assigned DMLR submission "1: Paper title".

Please acknowledge on OpenReview that you have received this review assignment by following this link: https://openreview.net/forum?id={note_id_1}&invitationId=DMLR/Paper1/Reviewers/-/~David_Bo1/Assignment/Acknowledgement

As a reminder, reviewers are **expected to accept all assignments** for submissions that fall within their expertise and annual quota (6 papers). Acceptable exceptions are 1) if you have an active, unsubmitted review for another DMLR submission or 2) situations where exceptional personal circumstances (e.g. vacation, health problems) render you incapable of performing your reviewing duties. Based on the above, if you think you should not review this submission, contact your AE directly (you can do so by leaving a comment on OpenReview, with only the Action Editor as Reader).

To submit your review, please follow this link: https://openreview.net/forum?id={note_id_1}&invitationId=DMLR/Paper1/-/Review or check your tasks in the Reviewers Console: https://openreview.net/group?id=DMLR/Reviewers#reviewer-tasks

Once submitted, your review will become privately visible to the authors and AE. Then, as soon as 3 reviews have been submitted, all reviews will become visible to all the reviewers. For more details and guidelines on performing your review, visit data.mlr.press.

We thank you for your essential contribution to DMLR!

The DMLR Editors-in-Chief
note: replies to this email will go to the AE, Andrew Ng.
'''
        assert messages[0]['content']['replyTo'] == 'andrew@dmlrzero.com'

        assert openreview.tools.get_invitation(openreview_client, 'DMLR/Reviewers/-/~David_Bo1/Responsibility/Acknowledgement')

        ## Carlos Gardel
        paper_assignment_edge = andrew_client.post_edge(openreview.Edge(invitation='DMLR/Reviewers/-/Assignment',
            readers=["DMLR", "DMLR/Paper1/Action_Editors", '~Carlos_Ge1'],
            nonreaders=["DMLR/Paper1/Authors"],
            writers=["DMLR", "DMLR/Paper1/Action_Editors"],
            signatures=[graham_paper1_anon_group.id],
            head=note_id_1,
            tail='~Carlos_Ge1',
            weight=1
        ))

        ## Javier Barden
        paper_assignment_edge = andrew_client.post_edge(openreview.Edge(invitation='DMLR/Reviewers/-/Assignment',
            readers=["DMLR", "DMLR/Paper1/Action_Editors", '~Javier_Ba1'],
            nonreaders=["DMLR/Paper1/Authors"],
            writers=["DMLR", "DMLR/Paper1/Action_Editors"],
            signatures=[graham_paper1_anon_group.id],
            head=note_id_1,
            tail='~Javier_Ba1',
            weight=1
        ))

        helpers.await_queue_edit(openreview_client, edit_id=paper_assignment_edge.id)

        reviewerrs_group = ce_client.get_group('DMLR/Paper1/Reviewers')
        assert reviewerrs_group.members == ['~David_Bo1', '~Carlos_Ge1', '~Javier_Ba1']

        david_anon_groups=david_client.get_groups(prefix='DMLR/Paper1/Reviewer_.*', signatory='~David_Bo1')
        assert len(david_anon_groups) == 1

        ## Post a review edit
        david_review_note = david_client.post_note_edit(invitation='DMLR/Paper1/-/Review',
            signatures=[david_anon_groups[0].id],
            note=Note(
                content={
                    'summary_of_contributions': { 'value': 'summary_of_contributions' },
                    'strengths_and_weaknesses': { 'value': 'strengths_and_weaknesses' },
                    'requested_changes': { 'value': 'requested_changes' },
                    'limitations': { 'value': 'limitations' },
                    'broader_impact_concerns': { 'value': 'broader_impact_concerns' },
                    'claims_and_evidence': { 'value': 'Yes' },
                    'extended_submissions': { 'value': 'extended_submissions' },
                    'audience': { 'value': 'Yes' },
                    'datasets_and_benchmarks': { 'value': 'datasets_and_benchmarks' },
                    'recommendation': { 'value': '4: Accept.' },
                    'confidence': { 'value': '3: You are very confident in your assessment.' }
                }
            )
        )

        helpers.await_queue_edit(openreview_client, edit_id=david_review_note['id'])

        carlos_anon_groups=carlos_client.get_groups(prefix='DMLR/Paper1/Reviewer_.*', signatory='~Carlos_Ge1')
        assert len(carlos_anon_groups) == 1

        ## Post a review edit
        carlos_review_note = carlos_client.post_note_edit(invitation='DMLR/Paper1/-/Review',
            signatures=[carlos_anon_groups[0].id],
            note=Note(
                content={
                    'summary_of_contributions': { 'value': 'summary_of_contributions' },
                    'strengths_and_weaknesses': { 'value': 'strengths_and_weaknesses' },
                    'requested_changes': { 'value': 'requested_changes' },
                    'limitations': { 'value': 'limitations' },
                    'broader_impact_concerns': { 'value': 'broader_impact_concerns' },
                    'claims_and_evidence': { 'value': 'Yes' },
                    'extended_submissions': { 'value': 'extended_submissions' },
                    'audience': { 'value': 'Yes' },
                    'datasets_and_benchmarks': { 'value': 'datasets_and_benchmarks' },
                    'recommendation': { 'value': '4: Accept.' },
                    'confidence': { 'value': '3: You are very confident in your assessment.' }
                }
            )
        )

        helpers.await_queue_edit(openreview_client, edit_id=carlos_review_note['id'])

        javier_anon_groups=javier_client.get_groups(prefix='DMLR/Paper1/Reviewer_.*', signatory='~Javier_Ba1')
        assert len(javier_anon_groups) == 1

        ## Post a review edit
        javier_review_note = javier_client.post_note_edit(invitation='DMLR/Paper1/-/Review',
            signatures=[javier_anon_groups[0].id],
            note=Note(
                content={
                    'summary_of_contributions': { 'value': 'summary_of_contributions' },
                    'strengths_and_weaknesses': { 'value': 'strengths_and_weaknesses' },
                    'requested_changes': { 'value': 'requested_changes' },
                    'limitations': { 'value': 'limitations' },
                    'broader_impact_concerns': { 'value': 'broader_impact_concerns' },
                    'claims_and_evidence': { 'value': 'Yes' },
                    'extended_submissions': { 'value': 'extended_submissions' },
                    'audience': { 'value': 'Yes' },
                    'datasets_and_benchmarks': { 'value': 'datasets_and_benchmarks' },
                    'recommendation': { 'value': '4: Accept.' },
                    'confidence': { 'value': '3: You are very confident in your assessment.' }
                }
            )
        )

        helpers.await_queue_edit(openreview_client, edit_id=javier_review_note['id'])

        ## All the reviewes should be visible to all the reviewers now
        reviews=openreview_client.get_notes(forum=note_id_1, invitation='DMLR/Paper1/-/Review', sort= 'number:asc')
        assert len(reviews) == 3
        assert reviews[0].readers == ['DMLR/Editors_In_Chief', 'DMLR/Action_Editors', 'DMLR/Paper1/Reviewers', 'DMLR/Paper1/Authors']
        assert reviews[0].signatures == [david_anon_groups[0].id]
        assert reviews[1].readers == ['DMLR/Editors_In_Chief', 'DMLR/Action_Editors', 'DMLR/Paper1/Reviewers', 'DMLR/Paper1/Authors']
        assert reviews[1].signatures == [carlos_anon_groups[0].id]
        assert reviews[2].readers == ['DMLR/Editors_In_Chief', 'DMLR/Action_Editors', 'DMLR/Paper1/Reviewers', 'DMLR/Paper1/Authors']
        assert reviews[2].signatures == [javier_anon_groups[0].id]

        invitations = openreview_client.get_invitations(replyForum=note_id_1, prefix='DMLR/Paper1')
        assert len(invitations) == 6
        assert "DMLR/Paper1/-/Official_Comment" in [i.id for i in invitations]
        assert "DMLR/Paper1/-/Review" in [i.id for i in invitations]
        assert "DMLR/Paper1/-/Revision" in [i.id for i in invitations]
        assert "DMLR/Paper1/-/Withdrawal" in [i.id for i in invitations]
        assert "DMLR/Paper1/-/Desk_Rejection" in [i.id for i in invitations]
        assert "DMLR/Paper1/-/Official_Recommendation" in [i.id for i in invitations]

        official_comment_invitation = openreview_client.get_invitation("DMLR/Paper1/-/Official_Comment")
        assert 'everyone' not in official_comment_invitation.edit['note']['readers']['param']['enum']

        assert openreview.tools.get_invitation(openreview_client, 'DMLR/Paper1/-/Official_Recommendation')

    def test_official_recommendation(self, journal, openreview_client, helpers):

        venue_id = 'DMLR'
        andrew_client = OpenReviewClient(username='andrew@dmlrzero.com', password=helpers.strong_password)
        ce_client = OpenReviewClient(username='ce@mailseven.com', password=helpers.strong_password)
        david_client = OpenReviewClient(username='david@dmlrone.com', password=helpers.strong_password)
        carlos_client = OpenReviewClient(username='carlos@dmlrthree.com', password=helpers.strong_password)
        javier_client = OpenReviewClient(username='javier@dmlrtwo.com', password=helpers.strong_password)        
        note_id_1 = openreview_client.get_notes(invitation='DMLR/-/Submission')[0].id
        
        ce_client.post_invitation_edit(
            invitations='DMLR/-/Edit',
            readers=[venue_id],
            writers=[venue_id],
            signatures=[venue_id],
            invitation=openreview.api.Invitation(id=f'{venue_id}/Paper1/-/Official_Recommendation',
                cdate=openreview.tools.datetime_millis(datetime.datetime.utcnow()) + 1000,
                signatures=['DMLR/Editors_In_Chief']
            )
        )

        time.sleep(5) ## wait until the process function runs

        messages = openreview_client.get_messages(to = 'david@dmlrone.com', subject = '[DMLR] Submit official recommendation for DMLR submission 1: Paper title')
        assert len(messages) == 1
        assert 'You may now submit your official recommendation for the submission confirming you updated the review' in messages[0]['content']['text']

        david_anon_groups=david_client.get_groups(prefix='DMLR/Paper1/Reviewer_.*', signatory='~David_Bo1')
        assert len(david_anon_groups) == 1

        ## Post a review recommendation
        official_recommendation_note = david_client.post_note_edit(invitation=f'{venue_id}/Paper1/-/Official_Recommendation',
            signatures=[david_anon_groups[0].id],
            note=Note(
                content={
                    'recommendation_confirmation': { 'value': 'Yes' }
                }
            )
        )

        helpers.await_queue_edit(openreview_client, edit_id=official_recommendation_note['id'])

        carlos_anon_groups=carlos_client.get_groups(prefix='DMLR/Paper1/Reviewer_.*', signatory='~Carlos_Ge1')
        assert len(carlos_anon_groups) == 1

        official_recommendation_note = carlos_client.post_note_edit(invitation=f'{venue_id}/Paper1/-/Official_Recommendation',
            signatures=[carlos_anon_groups[0].id],
            note=Note(
                content={
                    'recommendation_confirmation': { 'value': 'Yes' }
                }
            )
        )

        helpers.await_queue_edit(openreview_client, edit_id=official_recommendation_note['id']) 

        javier_anon_groups=javier_client.get_groups(prefix='DMLR/Paper1/Reviewer_.*', signatory='~Javier_Ba1')
        assert len(javier_anon_groups) == 1

        official_recommendation_note = javier_client.post_note_edit(invitation=f'{venue_id}/Paper1/-/Official_Recommendation',
            signatures=[javier_anon_groups[0].id],
            note=Note(
                content={
                    'recommendation_confirmation': { 'value': 'Yes' }
                }
            )
        )

        helpers.await_queue_edit(openreview_client, edit_id=official_recommendation_note['id'])                                     
    
    def test_decision(self, journal, openreview_client, helpers):

        ce_client = OpenReviewClient(username='ce@mailseven.com', password=helpers.strong_password)
        andrew_client = OpenReviewClient(username='andrew@dmlrzero.com', password=helpers.strong_password)
        note_id_1 = openreview_client.get_notes(invitation='DMLR/-/Submission')[0].id
        reviews=openreview_client.get_notes(forum=note_id_1, invitation='DMLR/Paper1/-/Review', sort= 'number:asc')

        andrew_paper1_anon_groups = andrew_client.get_groups(prefix=f'DMLR/Paper1/Action_Editor_.*', signatory='~Andrew_Ng1')
        assert len(andrew_paper1_anon_groups) == 1
        andrew_paper1_anon_group = andrew_paper1_anon_groups[0]

        for review in reviews:
            signature=review.signatures[0]
            rating_note=andrew_client.post_note_edit(invitation=f'{signature}/-/Rating',
                signatures=[andrew_paper1_anon_group.id],
                note=Note(
                    content={
                        'rating': { 'value': 'Exceeds expectations' }
                    }
                )
            )
            helpers.await_queue_edit(openreview_client, edit_id=rating_note['id'])

        decision_note = andrew_client.post_note_edit(invitation='DMLR/Paper1/-/Decision',
            signatures=[andrew_paper1_anon_group.id],
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

        decision_note = andrew_client.get_note(decision_note['note']['id'])
        assert decision_note.readers == ["DMLR/Editors_In_Chief", "DMLR/Paper1/Action_Editors"]

        ## EIC approves the decision
        approval_note = ce_client.post_note_edit(invitation='DMLR/Paper1/-/Decision_Approval',
                            signatures=['DMLR/Editors_In_Chief'],
                            note=Note(
                                content= {
                                    'approval': { 'value': 'I approve the AE\'s decision.' },
                                    'comment_to_the_AE': { 'value': 'I agree with the AE' }
                                }
                            ))

        helpers.await_queue_edit(openreview_client, edit_id=approval_note['id'])


        decision_note = ce_client.get_note(decision_note.id)
        assert decision_note.readers == ['DMLR/Editors_In_Chief', 'DMLR/Action_Editors', 'DMLR/Paper1/Reviewers', 'DMLR/Paper1/Authors']
        assert decision_note.nonreaders == []

