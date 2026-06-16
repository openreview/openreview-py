import openreview
import pytest
import datetime
from openreview.api import OpenReviewClient
from openreview.api import Note
from openreview.journal import JournalRequest


class TestTMLRExperiment():

    @pytest.fixture(scope="class")
    def journal(self, openreview_client, helpers):
        venue_id = 'TMLRE'
        percy_client = OpenReviewClient(username='percy@expmail.com', password=helpers.strong_password)
        percy_client.impersonate('TMLRE')
        requests = openreview_client.get_notes(invitation='openreview.net/Support/-/Journal_Request', content={'venue_id': venue_id})
        return JournalRequest.get_journal(percy_client, requests[0].id)

    def test_setup(self, openreview_client, request_page, selenium, helpers, journal_request):
        ## Support Role
        helpers.create_user('percy@expmail.com', 'Percy', 'Liang')

        ## Editors in Chief
        helpers.create_user('sarah@expmail.com', 'Sarah', 'Miller')
        helpers.create_user('thomas@expmail.com', 'Thomas', 'Brown')

        ## Action Editor
        helpers.create_user('alice@expmailseven.com', 'Alice', 'Johnson')

        ## Reviewers
        helpers.create_user('bob@expmailone.com', 'Bob', 'Williams')
        helpers.create_user('carol@expmailtwo.com', 'Carol', 'Davis')
        helpers.create_user('dan@expmailthree.com', 'Dan', 'Lee')

        ## Author
        helpers.create_user('eve@expmaileight.com', 'Eve', 'Garcia')

        request_form = openreview_client.post_note_edit(
            invitation='openreview.net/Support/-/Journal_Request',
            signatures=['openreview.net/Support'],
            note=Note(
                signatures=['openreview.net/Support'],
                content={
                    'official_venue_name': {'value': 'Transactions on Machine Learning Research Experiment'},
                    'abbreviated_venue_name': {'value': 'TMLRE'},
                    'venue_id': {'value': 'TMLRE'},
                    'contact_info': {'value': 'tmlre@jmlr.org'},
                    'secret_key': {'value': openreview.tools.create_hash_seed()},
                    'support_role': {'value': '~Percy_Liang1'},
                    'editors': {'value': ['~Sarah_Miller1', '~Thomas_Brown1']},
                    'website': {'value': 'jmlr.org/tmlre'},
                    'settings': {
                        'value': {
                            'submission_public': True,
                            'assignment_delay': 5,
                            'submission_name': 'Submission',
                            'submission_license': 'CC BY-SA 4.0',
                            'eic_submission_notification': False,
                            'certifications': [
                                'Featured Certification',
                                'Reproducibility Certification',
                                'Survey Certification'
                            ],
                            'eic_certifications': ['Outstanding Certification'],
                            'submission_length': [
                                'Regular submission (no more than 12 pages of main content)',
                                'Long submission (more than 12 pages of main content)',
                            ],
                            'issn': '2835-8856',
                            'website_urls': {
                                'editorial_board': 'https://jmlr.org/tmlr/editorial-board.html',
                                'evaluation_criteria': 'https://jmlr.org/tmlr/editorial-policies.html#evaluation',
                                'reviewer_guide': 'https://jmlr.org/tmlr/reviewer-guide.html',
                                'editorial_policies': 'https://jmlr.org/tmlr/editorial-policies.html',
                                'faq': 'https://jmlr.org/tmlr/contact.html',
                            },
                            'editors_email': 'tmlre-editors@jmlr.org',
                            'skip_ac_recommendation': False,
                            'number_of_reviewers': 3,
                            'reviewers_max_papers': 6,
                            'ae_recommendation_period': 1,
                            'under_review_approval_period': 1,
                            'reviewer_assignment_period': 1,
                            'review_period': 2,
                            'discussion_period': 2,
                            'recommendation_period': 2,
                            'decision_period': 1,
                            'camera_ready_period': 4,
                            'camera_ready_verification_period': 1,
                            'archived_action_editors': True,
                            'archived_reviewers': True,
                            'expert_reviewers': True,
                            'external_reviewers': True,
                            'expertise_model': 'specter2+scincl',
                            'review_additional_fields': {
                                'strengths_and_weaknesses': False,
                                'summary_of_contributions': {
                                    'order': 1,
                                    'value': {
                                        'param': {
                                            'maxLength': 200000,
                                            'input': 'textarea',
                                            'type': 'string',
                                            'markdown': True
                                        }
                                    }
                                },
                                'claims_and_evidence': {
                                    'order': 2,
                                    'value': {
                                        'param': {
                                            'type': 'string',
                                            'enum': ['Yes', 'No'],
                                            'input': 'radio'
                                        }
                                    }
                                },
                                'claims_explanation': {
                                    'order': 3,
                                    'value': {
                                        'param': {
                                            'type': 'string',
                                            'maxLength': 200000,
                                            'input': 'textarea',
                                            'markdown': True
                                        }
                                    }
                                },
                                'audience': {
                                    'order': 4,
                                    'value': {
                                        'param': {
                                            'type': 'string',
                                            'enum': ['Yes', 'No'],
                                            'input': 'radio'
                                        }
                                    }
                                },
                                'audience_explanation': {
                                    'order': 5,
                                    'value': {
                                        'param': {
                                            'type': 'string',
                                            'maxLength': 200000,
                                            'input': 'textarea',
                                            'markdown': True
                                        }
                                    }
                                },
                                'requested_changes': {
                                    'order': 6,
                                    'value': {
                                        'param': {
                                            'maxLength': 200000,
                                            'input': 'textarea',
                                            'type': 'string',
                                            'markdown': True
                                        }
                                    }
                                },
                                'broader_impact_concerns': {
                                    'order': 7,
                                    'value': {
                                        'param': {
                                            'maxLength': 200000,
                                            'input': 'textarea',
                                            'type': 'string',
                                            'markdown': True
                                        }
                                    }
                                },
                            },
                            'official_recommendation_additional_validation': (
                                "if edit.note.content.get('claims_and_evidence', {}).get('value') == 'Yes'"
                                " and edit.note.content.get('audience', {}).get('value') == 'Yes':\n"
                                "    if 'Reject' in edit.note.content.get('decision_recommendation', {}).get('value', ''):\n"
                                "        raise openreview.OpenReviewException("
                                "'Decision recommendation should be \"Accept\" or \"Leaning Accept\" if you answered"
                                " \"Yes\" to both TMLR criteria.')\n"
                                "if edit.note.content.get('claims_and_evidence', {}).get('value') == 'No'"
                                " or edit.note.content.get('audience', {}).get('value') == 'No':\n"
                                "    if 'Accept' in edit.note.content.get('decision_recommendation', {}).get('value', ''):\n"
                                "        raise openreview.OpenReviewException("
                                "'Decision recommendation should not be \"Accept\" nor \"Leaning Accept\" if you answered"
                                " \"No\" to either of the two TMLR criteria.')"
                            ),
                            'decision_additional_fields': {
                                'claims_and_evidence': {
                                    'order': 2,
                                    'value': {
                                        'param': {
                                            'type': 'string',
                                            'enum': ['Yes', 'No'],
                                            'input': 'radio'
                                        }
                                    }
                                },
                                'claims_explanation': {
                                    'order': 3,
                                    'value': {
                                        'param': {
                                            'type': 'string',
                                            'maxLength': 200000,
                                            'input': 'textarea',
                                            'markdown': True
                                        }
                                    }
                                },
                                'audience': {
                                    'order': 4,
                                    'value': {
                                        'param': {
                                            'type': 'string',
                                            'enum': ['Yes', 'No'],
                                            'input': 'radio'
                                        }
                                    }
                                },
                                'audience_explanation': {
                                    'order': 5,
                                    'value': {
                                        'param': {
                                            'type': 'string',
                                            'maxLength': 200000,
                                            'input': 'textarea',
                                            'markdown': True
                                        }
                                    }
                                },
                                'comment': False,
                                'additional_comments': {
                                    'order': 10,
                                    'value': {
                                        'param': {
                                            'type': 'string',
                                            'maxLength': 200000,
                                            'input': 'textarea',
                                            'markdown': True,
                                            'optional': True
                                        }
                                    }
                                },
                            },
                            'assignment_delay_after_submitted_review': 0.0001,
                            'max_solicit_review_per_month': 3,
                            'enable_blocked_authors': True,
                        }
                    }
                }
            ))

        helpers.await_queue_edit(openreview_client, request_form['id'])

        tmlre = openreview_client.get_group('TMLRE')
        assert tmlre
        assert tmlre.members == ['~Percy_Liang1', 'TMLRE/Editors_In_Chief']

    def test_invite_action_editors(self, journal, openreview_client, helpers):
        openreview_client.add_members_to_group('TMLRE/Action_Editors', ['~Alice_Johnson1'])
        group = openreview_client.get_group('TMLRE/Action_Editors')
        assert '~Alice_Johnson1' in group.members

    def test_invite_reviewers(self, journal, openreview_client, helpers):
        openreview_client.add_members_to_group('TMLRE/Reviewers', ['~Bob_Williams1', '~Carol_Davis1', '~Dan_Lee1'])
        group = openreview_client.get_group('TMLRE/Reviewers')
        assert len(group.members) == 3

    def test_submission(self, journal, openreview_client, test_client, helpers):
        venue_id = journal.venue_id
        test_client = OpenReviewClient(username='test@mail.com', password=helpers.strong_password)
        sarah_client = OpenReviewClient(username='sarah@expmail.com', password=helpers.strong_password)
        alice_client = OpenReviewClient(username='alice@expmailseven.com', password=helpers.strong_password)

        submission_note = test_client.post_note_edit(invitation='TMLRE/-/Submission',
            signatures=['~SomeFirstName_User1'],
            note=Note(content={
                'title': {'value': 'Experiment Paper Title'},
                'abstract': {'value': 'Experiment paper abstract'},
                'authors': {'value': ['SomeFirstName User', 'Eve Garcia']},
                'authorids': {'value': ['~SomeFirstName_User1', '~Eve_Garcia1']},
                'pdf': {'value': '/pdf/' + 'p' * 40 + '.pdf'},
                'competing_interests': {'value': 'None beyond the authors normal conflict of interests'},
                'human_subjects_reporting': {'value': 'Not applicable'},
                'submission_length': {'value': 'Regular submission (no more than 12 pages of main content)'}
            }))

        helpers.await_queue_edit(openreview_client, edit_id=submission_note['id'])
        note_id = submission_note['note']['id']

        note = openreview_client.get_note(note_id)
        assert note.readers == ['TMLRE', 'TMLRE/Paper1/Action_Editors', 'TMLRE/Paper1/Authors']
        assert note.content['venue']['value'] == 'Submitted to TMLRE'
        assert note.content['venueid']['value'] == 'TMLRE/Submitted'
        assert note.content['authorids']['value'] == ['~SomeFirstName_User1', '~Eve_Garcia1']

        author_group = openreview_client.get_group(f'{venue_id}/Paper1/Authors')
        assert author_group.members == ['~SomeFirstName_User1', '~Eve_Garcia1']

        # Author recommends AE
        test_client.post_edge(openreview.api.Edge(
            invitation='TMLRE/Action_Editors/-/Recommendation',
            head=note_id,
            tail='~Alice_Johnson1',
            weight=1
        ))

        # EIC assigns AE
        editor_in_chief_group_id = f'{venue_id}/Editors_In_Chief'
        paper_assignment_edge = sarah_client.post_edge(openreview.api.Edge(
            invitation='TMLRE/Action_Editors/-/Assignment',
            readers=[venue_id, editor_in_chief_group_id, '~Alice_Johnson1'],
            writers=[venue_id, editor_in_chief_group_id],
            signatures=[editor_in_chief_group_id],
            head=note_id,
            tail='~Alice_Johnson1',
            weight=1
        ))
        helpers.await_queue_edit(openreview_client, edit_id=paper_assignment_edge.id)

        ae_group = openreview_client.get_group(f'{venue_id}/Paper1/Action_Editors')
        assert ae_group.members == ['~Alice_Johnson1']

        alice_paper1_anon_groups = alice_client.get_groups(
            prefix=f'{venue_id}/Paper1/Action_Editor_.*', signatory='~Alice_Johnson1')
        assert len(alice_paper1_anon_groups) == 1
        alice_paper1_anon_group = alice_paper1_anon_groups[0]

        messages = openreview_client.get_messages(
            to='alice@expmailseven.com',
            subject='[TMLRE] Assignment to new TMLRE submission 1: Experiment Paper Title')
        assert len(messages) == 1

        # AE approves submission for review
        under_review_note = alice_client.post_note_edit(invitation='TMLRE/Paper1/-/Review_Approval',
            signatures=[alice_paper1_anon_group.id],
            note=Note(content={'under_review': {'value': 'Appropriate for Review'}}))
        helpers.await_queue_edit(openreview_client, edit_id=under_review_note['id'])
        helpers.await_queue_edit(openreview_client, invitation='TMLRE/-/Under_Review')

        note = openreview_client.get_note(note_id)
        assert note.readers == ['everyone']
        assert note.content['venue']['value'] == 'Under review for TMLRE'
        assert note.content['venueid']['value'] == 'TMLRE/Under_Review'
        assert note.content['assigned_action_editor']['value'] == '~Alice_Johnson1'

    def test_review_process(self, journal, openreview_client, test_client, helpers):
        venue_id = journal.venue_id
        sarah_client = OpenReviewClient(username='sarah@expmail.com', password=helpers.strong_password)
        alice_client = OpenReviewClient(username='alice@expmailseven.com', password=helpers.strong_password)
        bob_client = OpenReviewClient(username='bob@expmailone.com', password=helpers.strong_password)
        carol_client = OpenReviewClient(username='carol@expmailtwo.com', password=helpers.strong_password)
        dan_client = OpenReviewClient(username='dan@expmailthree.com', password=helpers.strong_password)

        submissions = openreview_client.get_notes(invitation='TMLRE/-/Submission')
        note_id = submissions[0].id

        alice_paper1_anon_groups = alice_client.get_groups(
            prefix=f'{venue_id}/Paper1/Action_Editor_.*', signatory='~Alice_Johnson1')
        alice_paper1_anon_group = alice_paper1_anon_groups[0]

        # Assign 3 reviewers
        for reviewer in ['~Bob_Williams1', '~Carol_Davis1', '~Dan_Lee1']:
            edge = alice_client.post_edge(openreview.api.Edge(
                invitation='TMLRE/Reviewers/-/Assignment',
                readers=[venue_id, f'{venue_id}/Paper1/Action_Editors', reviewer],
                nonreaders=[f'{venue_id}/Paper1/Authors'],
                writers=[venue_id, f'{venue_id}/Paper1/Action_Editors'],
                signatures=[alice_paper1_anon_group.id],
                head=note_id,
                tail=reviewer,
                weight=1
            ))
            helpers.await_queue_edit(openreview_client, edit_id=edge.id)

        reviewers_group = openreview_client.get_group(f'{venue_id}/Paper1/Reviewers')
        assert len(reviewers_group.members) == 3

        # All 3 reviewers post reviews
        for reviewer_client, reviewer_id in [
            (bob_client, '~Bob_Williams1'),
            (carol_client, '~Carol_Davis1'),
            (dan_client, '~Dan_Lee1'),
        ]:
            anon_groups = reviewer_client.get_groups(
                prefix=f'{venue_id}/Paper1/Reviewer_.*', signatory=reviewer_id)
            review_note = reviewer_client.post_note_edit(invitation=f'{venue_id}/Paper1/-/Review',
                signatures=[anon_groups[0].id],
                note=Note(content={
                    'summary_of_contributions': {'value': 'Good contributions.'},
                    'claims_and_evidence': {'value': 'Yes'},
                    'claims_explanation': {'value': 'Claims are well supported.'},
                    'audience': {'value': 'Yes'},
                    'audience_explanation': {'value': 'Broad ML audience.'},
                    'requested_changes': {'value': 'None.'},
                    'broader_impact_concerns': {'value': 'None.'},
                }))
            helpers.await_queue_edit(openreview_client, edit_id=review_note['id'])

        reviews = openreview_client.get_notes(forum=note_id, invitation=f'{venue_id}/Paper1/-/Review')
        assert len(reviews) == 3
        for review in reviews:
            assert review.readers == ['everyone']

        # Move recommendation cdate to now since the discussion period hasn't elapsed
        sarah_client.post_invitation_edit(
            invitations='TMLRE/-/Edit',
            readers=[venue_id],
            writers=[venue_id],
            signatures=[venue_id],
            invitation=openreview.api.Invitation(
                id=f'{venue_id}/Paper1/-/Official_Recommendation',
                cdate=openreview.tools.datetime_millis(datetime.datetime.now()) + 1000,
                signatures=['TMLRE/Editors_In_Chief']
            )
        )
        helpers.await_queue_edit(openreview_client, edit_id=f'{venue_id}/Paper1/-/Official_Recommendation-0-0')

        # Post official recommendations
        for reviewer_client, reviewer_id in [
            (bob_client, '~Bob_Williams1'),
            (carol_client, '~Carol_Davis1'),
            (dan_client, '~Dan_Lee1'),
        ]:
            anon_groups = reviewer_client.get_groups(
                prefix=f'{venue_id}/Paper1/Reviewer_.*', signatory=reviewer_id)
            rec_note = reviewer_client.post_note_edit(invitation=f'{venue_id}/Paper1/-/Official_Recommendation',
                signatures=[anon_groups[0].id],
                note=Note(content={
                    'decision_recommendation': {'value': 'Accept'},
                    'certification_recommendations': {'value': ['Featured Certification']},
                    'claims_and_evidence': {'value': 'Yes'},
                    'audience': {'value': 'Yes'},
                }))
            helpers.await_queue_edit(openreview_client, edit_id=rec_note['id'])

        messages = openreview_client.get_messages(
            to='alice@expmailseven.com',
            subject='[TMLRE] Evaluate reviewers and submit decision for TMLRE submission 1: Experiment Paper Title')
        assert len(messages) == 1

        # Rate all reviewer submissions
        reviews = openreview_client.get_notes(forum=note_id, invitation=f'{venue_id}/Paper1/-/Review')
        for review in reviews:
            signature = review.signatures[0]
            openreview_client.post_invitation_edit(
                invitations='TMLRE/-/Edit',
                signatures=['TMLRE'],
                invitation=openreview.api.Invitation(
                    id=f'{signature}/-/Rating',
                    cdate=openreview.tools.datetime_millis(datetime.datetime.now() - datetime.timedelta(days=1)),
                    duedate=openreview.tools.datetime_millis(datetime.datetime.now() - datetime.timedelta(minutes=30))
                )
            )
            rating_note = alice_client.post_note_edit(invitation=f'{signature}/-/Rating',
                signatures=[alice_paper1_anon_group.id],
                note=Note(content={'rating': {'value': 'Exceeds expectations'}}))
            helpers.await_queue_edit(openreview_client, edit_id=rating_note['id'])

        # AE posts decision
        decision_note = alice_client.post_note_edit(invitation=f'{venue_id}/Paper1/-/Decision',
            signatures=[alice_paper1_anon_group.id],
            note=Note(content={
                'claims_and_evidence': {'value': 'Yes'},
                'claims_explanation': {'value': 'Claims are well supported.'},
                'audience': {'value': 'Yes'},
                'audience_explanation': {'value': 'Broad ML audience.'},
                'recommendation': {'value': 'Accept as is'},
                'certifications': {'value': ['Featured Certification']},
                'additional_comments': {'value': 'Great paper!'},
            }))
        helpers.await_queue_edit(openreview_client, edit_id=decision_note['id'])

        submission = openreview_client.get_note(note_id)
        assert submission.content['venueid']['value'] == 'TMLRE/Decision_Pending'

        decision_note_obj = alice_client.get_note(decision_note['note']['id'])
        assert decision_note_obj.readers == [f'{venue_id}/Editors_In_Chief', f'{venue_id}/Paper1/Action_Editors']

        # EIC approves decision
        approval_note = sarah_client.post_note_edit(invitation='TMLRE/Paper1/-/Decision_Approval',
            signatures=['TMLRE/Editors_In_Chief'],
            note=Note(content={'approval': {'value': "I approve the AE's decision."}}))
        helpers.await_queue_edit(openreview_client, edit_id=approval_note['id'])

        decision_note_obj = sarah_client.get_note(decision_note['note']['id'])
        assert decision_note_obj.readers == ['everyone']

        messages = openreview_client.get_messages(
            to='test@mail.com',
            subject='[TMLRE] Decision for your TMLRE submission 1: Experiment Paper Title')
        assert len(messages) == 1

        assert openreview_client.get_invitation(f'{venue_id}/Paper1/-/Camera_Ready_Revision')

    def test_camera_ready(self, journal, openreview_client, test_client, helpers):
        venue_id = journal.venue_id
        test_client = OpenReviewClient(username='test@mail.com', password=helpers.strong_password)
        alice_client = OpenReviewClient(username='alice@expmailseven.com', password=helpers.strong_password)

        submissions = openreview_client.get_notes(invitation='TMLRE/-/Submission')
        note_id = submissions[0].id

        alice_paper1_anon_groups = alice_client.get_groups(
            prefix=f'{venue_id}/Paper1/Action_Editor_.*', signatory='~Alice_Johnson1')
        alice_paper1_anon_group = alice_paper1_anon_groups[0]

        # Authors submit camera ready version
        revision_note = test_client.post_note_edit(invitation=f'{venue_id}/Paper1/-/Camera_Ready_Revision',
            signatures=[f'{venue_id}/Paper1/Authors'],
            note=Note(content={
                'title': {'value': 'Experiment Paper Title Camera Ready'},
                'authors': {'value': ['SomeFirstName User', 'Eve Garcia']},
                'authorids': {'value': ['~SomeFirstName_User1', '~Eve_Garcia1']},
                'abstract': {'value': 'Experiment paper abstract'},
                'pdf': {'value': '/pdf/' + 'p' * 40 + '.pdf'},
                'competing_interests': {'value': 'None beyond the authors normal conflict of interests'},
                'human_subjects_reporting': {'value': 'Not applicable'},
            }))
        helpers.await_queue_edit(openreview_client, edit_id=revision_note['id'])

        messages = openreview_client.get_messages(
            to='alice@expmailseven.com',
            subject='[TMLRE] Review camera ready version for TMLRE paper 1: Experiment Paper Title Camera Ready')
        assert len(messages) == 1

        # AE verifies camera ready
        verification_note = alice_client.post_note_edit(invitation='TMLRE/Paper1/-/Camera_Ready_Verification',
            signatures=[alice_paper1_anon_group.id],
            note=Note(content={
                'verification': {
                    'value': 'I confirm that camera ready manuscript complies with the TMLRE stylefile and, if appropriate, includes the minor revisions that were requested.'
                }
            }))
        helpers.await_queue_edit(openreview_client, edit_id=verification_note['id'])

        note = openreview_client.get_note(note_id)
        assert note.pdate
        assert 'TMLRE/-/Accepted' in note.invitations
        assert note.readers == ['everyone']
        assert note.writers == ['TMLRE']
        assert note.content['venue']['value'] == 'Accepted by TMLRE'
        assert note.content['venueid']['value'] == 'TMLRE'
        assert note.content['title']['value'] == 'Experiment Paper Title Camera Ready'
        assert note.content['authorids']['value'] == ['~SomeFirstName_User1', '~Eve_Garcia1']
        assert note.content['certifications']['value'] == ['Featured Certification']

        messages = openreview_client.get_messages(
            to='test@mail.com',
            subject='[TMLRE] Camera ready version accepted for your TMLRE submission 1: Experiment Paper Title Camera Ready')
        assert len(messages) == 1
