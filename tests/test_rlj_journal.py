import openreview
import pytest
import re
from openreview.api import OpenReviewClient
from openreview.api import Note
from openreview.journal import Journal
from openreview.journal import JournalRequest

class TestRLJJournal():

    @pytest.fixture(scope="class")
    def journal(self, openreview_client, helpers):

        eic_client=OpenReviewClient(username='paula@rlj.org', password=helpers.strong_password)
        eic_client.impersonate('RLJ')

        requests = openreview_client.get_notes(invitation='openreview.net/Support/-/Journal_Request', content={ 'venue_id': 'RLJ' })

        return JournalRequest.get_journal(eic_client, requests[0].id)

    def get_reviews(self, client, forum):
        return [note for note in client.get_notes(forum=forum) if 'RLJ/Paper1/-/Review' in note.invitations]

    def test_setup(self, openreview_client, helpers, journal_request):

        helpers.create_user('paula@rlj.org', 'Paula', 'Torres')

        with pytest.raises(openreview.OpenReviewException, match=r'Invalid review_release setting: decision. Valid values are: all_reviews_posted, decision_posted'):
            Journal(openreview_client, 'RLJ', None, 'editors@rlj.org', 'Reinforcement Learning Journal', 'RLJ', settings={ 'review_release': 'decision' }).setup('~Paula_Torres1')

        with pytest.raises(openreview.OpenReviewException, match=r'The review_release setting decision_posted requires skip_official_recommendation'):
            Journal(openreview_client, 'RLJ', None, 'editors@rlj.org', 'Reinforcement Learning Journal', 'RLJ', settings={ 'review_release': 'decision_posted' }).setup('~Paula_Torres1')

        request_form = openreview_client.post_note_edit(invitation= 'openreview.net/Support/-/Journal_Request',
            signatures = ['openreview.net/Support'],
            note = Note(
                signatures = ['openreview.net/Support'],
                content = {
                    'official_venue_name': {'value': 'Reinforcement Learning Journal'},
                    'abbreviated_venue_name' : {'value': 'RLJ'},
                    'contact_info': {'value': 'editors@rlj.org'},
                    'support_role': {'value': '~Paula_Torres1' },
                    'editors': {'value': ['~Paula_Torres1'] },
                    'website': {'value': 'rlj.org' },
                    'settings': {
                        'value': {
                            'submission_public': False,
                            'release_submission_after_acceptance': True,
                            'author_anonymity': True,
                            'assignment_delay': 0,
                            'submission_name': 'Submission',
                            'issn': 'XXXX-XXXX',
                            'submission_license': 'CC BY 4.0',
                            'eic_submission_notification': True,
                            'website_urls': {
                                'editorial_board': 'https://rlj.org/',
                                'submission_info_for_authors': 'https://rlj.org/',
                                'reviewer_guide': 'https://rlj.org/',
                                'editorial_policies': 'https://rlj.org/',
                                'evaluation_criteria': 'https://rlj.org/',
                                'faq': 'https://rlj.org/',
                                'stats': 'https://rlj.org/'
                            },
                            'editors_email': 'editors@rlj.org',
                            'skip_ac_recommendation': False,
                            'skip_official_recommendation': True,
                            'skip_reviewer_responsibility_acknowledgement': False,
                            'skip_reviewer_assignment_acknowledgement': False,
                            'number_of_reviewers': 2,
                            'reviewers_max_papers': 6,
                            'action_editors_max_papers': 6,
                            'ae_max_active_submissions': 6,
                            'ae_recommendation_period': 1,
                            'under_review_approval_period': 1,
                            'reviewer_assignment_period': 1,
                            'review_period': 3,
                            'decision_period': 1,
                            'camera_ready_period': 4,
                            'camera_ready_verification_period': 1,
                            'archived_action_editors': True,
                            'archived_reviewers': True,
                            'expert_reviewers': False,
                            'external_reviewers': False,
                            'expertise_model': 'specter2+scincl',
                            'reviewer_roles': ['Technical Reviewer', 'Senior Reviewer'],
                            'review_release': 'decision_posted',
                            'release_reviews_to_authors_when_posted': False,
                            'submission_additional_fields': {
                                'is_revision': {
                                    'order': 8,
                                    'description': 'Is this a revision of a previous RLJ submission? Answer Yes only if a previous RLJ submission received a Revisions decision and this is your response to it. If Yes, both fields below are required.',
                                    'value': {
                                        'param': {
                                            'type': 'string',
                                            'enum': [
                                                'Yes',
                                                'No'
                                            ],
                                            'input': 'radio'
                                        }
                                    }
                                },
                                'previous_RLJ_submission_url': {
                                    'order': 9,
                                    'description': 'Required if this is a revision. Please provide a link to the previous submission (its OpenReview URL).',
                                    'value': {
                                        'param': {
                                            'type': 'string',
                                            'regex': 'https://.*openreview.net/forum.*',
                                            'optional': True,
                                            'deletable': True
                                        }
                                    }
                                },
                                'human_subjects_reporting': {
                                    'order': 13,
                                    'description': 'If the submission reports experiments involving human subjects, provide information available on the approval of these experiments, such as from an Institutional Review Board (IRB). Enter "N/A" if this question isn\'t applicable to your situation.',
                                    'value': {
                                        'param': {
                                            'type': 'string',
                                            'maxLength': 5000,
                                            'input': 'textarea'
                                        }
                                    },
                                    'readers': [
                                        'RLJ',
                                        'RLJ/Paper${4/number}/Action_Editors',
                                        'RLJ/Paper${4/number}/Authors'
                                    ]
                                },
                                'competing_interests': None,
                                'changes_since_last_submission': None,
                                'letter_to_the_editor': {
                                    'order': 11,
                                    'description': 'For revisions only. Upload the letter to the Editor here as a PDF: list all the changes since the last submission and address any concern raised by the Editor. This file is only visible to the Editor and the Editors-in-Chief.',
                                    'value': {
                                        'param': {
                                            'type': 'file',
                                            'extensions': [
                                                'pdf'
                                            ],
                                            'maxSize': 50,
                                            'optional': True,
                                            'deletable': True
                                        }
                                    },
                                    'readers': [
                                        'RLJ',
                                        'RLJ/Paper${4/number}/Action_Editors',
                                        'RLJ/Paper${4/number}/Authors'
                                    ]
                                },
                                'disclosure_of_funding': {
                                    'order': 12,
                                    'description': 'Beyond those reflected in the authors\' OpenReview profile, disclose relationships (notably financial) of any author with entities that could potentially be perceived to influence what you wrote in the submitted work, during the last 36 months prior to this submission. This would include engagements with commercial companies or startups (sabbaticals, employments, stipends), honorariums, donations of hardware or cloud computing services. Enter "N/A" if this question isn\'t applicable to your situation.',
                                    'value': {
                                        'param': {
                                            'type': 'string',
                                            'maxLength': 5000,
                                            'input': 'textarea'
                                        }
                                    },
                                    'readers': [
                                        'RLJ',
                                        'RLJ/Paper${4/number}/Action_Editors',
                                        'RLJ/Paper${4/number}/Authors'
                                    ]
                                }
                            },
                            'review_additional_fields': {
                                'summary_of_contributions': None,
                                'strengths_and_weaknesses': None,
                                'requested_changes': None,
                                'broader_impact_concerns': None,
                                'claims_and_evidence': None,
                                'audience': None,
                                'recommendation': {
                                    'order': 5,
                                    'description': 'For senior reviewers only. Your overall recommendation.',
                                    'value': {
                                        'param': {
                                            'type': 'string',
                                            'enum': [
                                                'Accept',
                                                'Reject'
                                            ],
                                            'input': 'radio',
                                            'optional': True,
                                            'deletable': True
                                        }
                                    }
                                },
                                'for_technical_reviewer_claimed_contributions': {
                                    'order': 1,
                                    'description': 'For technical reviewers only. State the claimed contributions of the paper.',
                                    'value': {
                                        'param': {
                                            'type': 'string',
                                            'maxLength': 200000,
                                            'input': 'textarea',
                                            'markdown': True,
                                            'optional': True,
                                            'deletable': True,
                                            'default': 'For each claimed contribution: state the claim in your own words, state what evidence the paper provided for the claim, state whether the evidence was sufficient to establish the claim, and explain why the evidence was or was not sufficient.'
                                        }
                                    }
                                },
                                'for_technical_reviewer_polish_and_presentation': {
                                    'order': 2,
                                    'description': 'For technical reviewers only. Comment on the polish and presentation of the paper.',
                                    'value': {
                                        'param': {
                                            'type': 'string',
                                            'maxLength': 200000,
                                            'input': 'textarea',
                                            'markdown': True,
                                            'optional': True,
                                            'deletable': True,
                                            'default': 'Comment on the paper\'s structure, readability, notation consistency, figure readability, references, etc.'
                                        }
                                    }
                                },
                                'for_technical_reviewer_additional_comments': {
                                    'order': 3,
                                    'description': 'For technical reviewers only. List any additional errors or comments.',
                                    'value': {
                                        'param': {
                                            'type': 'string',
                                            'maxLength': 200000,
                                            'input': 'textarea',
                                            'markdown': True,
                                            'optional': True,
                                            'deletable': True,
                                            'default': 'List minor errors that do not affect the decision but should be fixed.'
                                        }
                                    }
                                },
                                'for_senior_reviewer_general_review': {
                                    'order': 4,
                                    'description': 'For senior reviewers only. Please write a general review of the paper.',
                                    'value': {
                                        'param': {
                                            'type': 'string',
                                            'maxLength': 200000,
                                            'input': 'textarea',
                                            'markdown': True,
                                            'optional': True,
                                            'deletable': True,
                                            'default': 'Review the paper\'s claimed contributions and their evidence, consider whether the results are of interest to a subset of RLJ readers, and reflect on your overall assessment of the paper.'
                                        }
                                    }
                                }
                            },
                            'decision_additional_fields': {
                                'claims_and_evidence': None,
                                'audience': None,
                                'rlj_decision': {
                                    'order': 1,
                                    'description': 'Accept: the paper is accepted in its current form and only minor changes are required, to the point that no response to the Editor is needed. Revisions: you provide a list of questions or proposed changes; authors are encouraged to respond within 3 months with a modified version of the manuscript and a letter to the editor. Reject: authors may not resubmit similar versions for 6 months unless you state otherwise below. Then set the Recommendation field to \'Accept as is\' for Accept, or \'Reject\' for both Revisions and Reject.',
                                    'value': {
                                        'param': {
                                            'type': 'string',
                                            'enum': [
                                                'Accept',
                                                'Revisions',
                                                'Reject'
                                            ],
                                            'input': 'radio'
                                        }
                                    }
                                },
                                'meta_review': {
                                    'order': 2,
                                    'description': 'Phrase the meta-review primarily in terms of the contributions claimed on the cover page: whether their scope is appropriate, whether they are properly contextualized, and whether the evidence supports them. It need not be a full-length review.',
                                    'value': {
                                        'param': {
                                            'type': 'string',
                                            'maxLength': 200000,
                                            'input': 'textarea',
                                            'markdown': True
                                        }
                                    }
                                },
                                'required_changes': {
                                    'order': 3,
                                    'description': 'For revision only. The list of questions and proposed changes the authors must address. State clearly what must change for the work to be accepted - the authors\' letter to the editor will respond to this list.',
                                    'value': {
                                        'param': {
                                            'type': 'string',
                                            'maxLength': 200000,
                                            'input': 'textarea',
                                            'markdown': True,
                                            'optional': True,
                                            'deletable': True
                                        }
                                    }
                                },
                                'resubmission_waiver': {
                                    'order': 4,
                                    'description': 'Reject only. Leave blank to apply the standard 6-month wait. Fill in only if the notice of rejection specifies otherwise.',
                                    'value': {
                                        'param': {
                                            'type': 'string',
                                            'maxLength': 5000,
                                            'input': 'textarea',
                                            'optional': True,
                                            'deletable': True
                                        }
                                    }
                                }
                            }
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
                    'venue_id': {'value': 'RLJ'}
                }
            ))

        helpers.await_queue_edit(openreview_client, deployment_edit['id'])

        invitation = openreview_client.get_invitation('RLJ/Reviewers/-/Role')
        assert invitation.invitees == ['RLJ', 'RLJ/Editors_In_Chief']
        assert invitation.readers == ['RLJ', 'RLJ/Action_Editors', 'RLJ/Action_Editors/Archived']
        assert invitation.edit['readers'] == ['RLJ', 'RLJ/Action_Editors', 'RLJ/Action_Editors/Archived']
        assert invitation.edit['head']['param']['const'] == 'RLJ/Reviewers'
        assert invitation.edit['label']['param']['enum'] == ['Technical Reviewer', 'Senior Reviewer']

        assert "var REVIEWERS_ROLE_ID = 'RLJ/Reviewers/-/Role';" in openreview_client.get_group('RLJ/Action_Editors').web
        assert "var REVIEWERS_ROLE_ID = 'RLJ/Reviewers/-/Role';" in openreview_client.get_group('RLJ/Action_Editors/Archived').web
        assert "var REVIEWERS_ROLE_ID = 'RLJ/Reviewers/-/Role';" in openreview_client.get_group('RLJ/Editors_In_Chief').web

        assert not openreview.tools.get_invitation(openreview_client, 'RLJ/Reviewers/-/Invite_Assignment')

        request_note = openreview_client.get_note(request_form['note']['id'])
        invitation = openreview_client.get_invitation(f'openreview.net/Support/Journal_Request{request_note.number}/-/Reviewer_Recruitment')
        assert invitation.edit['note']['content']['reviewer_role']['value']['param']['enum'] == ['Technical Reviewer', 'Senior Reviewer']
        invitation = openreview_client.get_invitation(f'openreview.net/Support/Journal_Request{request_note.number}/-/Action_Editor_Recruitment')
        assert 'reviewer_role' not in invitation.edit['note']['content']

        helpers.create_user('mateo@rljone.com', 'Mateo', 'Rivas')
        openreview_client.add_members_to_group('RLJ/Action_Editors', '~Mateo_Rivas1')

        helpers.create_user('mia@rljsix.com', 'Mia', 'Grant')

    def test_reviewer_recruitment(self, journal, openreview_client, helpers):

        eic_client = OpenReviewClient(username='paula@rlj.org', password=helpers.strong_password)
        request_note = openreview_client.get_notes(invitation='openreview.net/Support/-/Journal_Request', content={ 'venue_id': 'RLJ' })[0]
        comment_invitation_id = f'openreview.net/Support/Journal_Request{request_note.number}/-/Comment'

        helpers.create_user('tomas@rljtwo.com', 'Tomas', 'Lind')
        helpers.create_user('tara@rljthree.com', 'Tara', 'Novak')
        helpers.create_user('elena@rljfour.com', 'Elena', 'Moss')
        helpers.create_user('ethan@rljfive.com', 'Ethan', 'Park')
        helpers.create_user('omar@rljeight.com', 'Omar', 'Haddad')

        def recruit(invitee_details, reviewer_role):
            recruitment_note = eic_client.post_note_edit(
                invitation = f'openreview.net/Support/Journal_Request{request_note.number}/-/Reviewer_Recruitment',
                signatures = ['~Paula_Torres1'],
                note = Note(
                    content = {
                        'title': { 'value': 'Recruitment' },
                        'reviewer_role': { 'value': reviewer_role },
                        'invitee_details': { 'value': invitee_details },
                        'email_subject': { 'value': '[RLJ] Invitation to serve as Reviewer for RLJ' },
                        'email_content': { 'value': 'Dear {{fullname}},\n\nYou have been nominated by the Editors-in-Chief of RLJ to serve as reviewer.\n\n{{invitation_url}}\n\nCheers!' }
                    },
                    forum = request_note.id,
                    replyto = request_note.id
                ))
            helpers.await_queue_edit(openreview_client, recruitment_note['id'])
            return openreview_client.get_notes(invitation=comment_invitation_id, replyto=recruitment_note['note']['id'])[0].content['comment']['value']

        recruitment_status = recruit('tomas@rljtwo.com, Tomas Lind\n~Tara_Novak1\nnora@rljseven.com, Nora Quinn', 'Technical Reviewer')
        assert '**Invited**: 3 Reviewer(s).' in recruitment_status
        assert '**Reviewer role**: Technical Reviewer.' in recruitment_status

        recruitment_status = recruit('~Elena_Moss1\n~Ethan_Park1\n~Omar_Haddad1', 'Senior Reviewer')
        assert '**Invited**: 3 Reviewer(s).' in recruitment_status
        assert '**Reviewer role**: Senior Reviewer.' in recruitment_status

        role_edges = openreview_client.get_all_edges(invitation='RLJ/Reviewers/-/Role')
        assert { edge.tail: edge.label for edge in role_edges } == {
            '~Tomas_Lind1': 'Technical Reviewer',
            '~Tara_Novak1': 'Technical Reviewer',
            'nora@rljseven.com': 'Technical Reviewer',
            '~Elena_Moss1': 'Senior Reviewer',
            '~Ethan_Park1': 'Senior Reviewer',
            '~Omar_Haddad1': 'Senior Reviewer'
        }
        for edge in role_edges:
            assert edge.head == 'RLJ/Reviewers'
            assert edge.readers == ['RLJ', 'RLJ/Action_Editors', 'RLJ/Action_Editors/Archived']
            assert edge.signatures == ['RLJ']

        for email in ['tomas@rljtwo.com', 'tara@rljthree.com', 'elena@rljfour.com', 'ethan@rljfive.com', 'omar@rljeight.com']:
            messages = openreview_client.get_messages(to=email, subject='[RLJ] Invitation to serve as Reviewer for RLJ')
            assert len(messages) == 1
            invitation_url = re.search('https://.*\n', messages[0]['content']['text']).group(0).replace('&amp;', '&')[:-1]
            helpers.respond_invitation_fast(invitation_url, accept=True)

        assert sorted(openreview_client.get_group('RLJ/Reviewers').members) == ['~Elena_Moss1', '~Ethan_Park1', '~Omar_Haddad1', '~Tara_Novak1', '~Tomas_Lind1']
        assert sorted(openreview_client.get_group('RLJ/Reviewers/Invited').members) == ['nora@rljseven.com', '~Elena_Moss1', '~Ethan_Park1', '~Omar_Haddad1', '~Tara_Novak1', '~Tomas_Lind1']

        recruitment_status = recruit('~Tara_Novak1', 'Senior Reviewer')
        assert '**Invited**: 0 Reviewer(s).' in recruitment_status
        assert '**Reviewer role**: Senior Reviewer.' in recruitment_status
        assert "No recruitment invitation was sent to the following users because they are already members of the Reviewer group:\n['~Tara_Novak1']" in recruitment_status
        assert len(openreview_client.get_messages(to='tara@rljthree.com', subject='[RLJ] Invitation to serve as Reviewer for RLJ')) == 1

        tara_edges = openreview_client.get_edges(invitation='RLJ/Reviewers/-/Role', tail='~Tara_Novak1')
        assert len(tara_edges) == 1
        assert tara_edges[0].label == 'Senior Reviewer'

        omar_edge = eic_client.get_edges(invitation='RLJ/Reviewers/-/Role', tail='~Omar_Haddad1')[0]
        omar_edge.label = 'Technical Reviewer'
        omar_edge.signatures = ['RLJ/Editors_In_Chief']
        eic_client.post_edge(omar_edge)

        with pytest.raises(openreview.OpenReviewException, match=r'label must be equal to one of the allowed values: Technical Reviewer, Senior Reviewer'):
            omar_edge.label = 'Expert Reviewer'
            eic_client.post_edge(omar_edge)

        mateo_client = OpenReviewClient(username='mateo@rljone.com', password=helpers.strong_password)
        omar_edges = mateo_client.get_edges(invitation='RLJ/Reviewers/-/Role', tail='~Omar_Haddad1')
        assert len(omar_edges) == 1
        assert omar_edges[0].label == 'Technical Reviewer'

        with pytest.raises(openreview.OpenReviewException, match=r'Mateo Rivas is not an invitee of RLJ/Reviewers/-/Role'):
            omar_edge = omar_edges[0]
            omar_edge.label = 'Senior Reviewer'
            omar_edge.signatures = ['~Mateo_Rivas1']
            mateo_client.post_edge(omar_edge)

        assert openreview_client.get_edges(invitation='RLJ/Reviewers/-/Role', tail='~Omar_Haddad1')[0].label == 'Technical Reviewer'

    def test_submission(self, journal, openreview_client, test_client, helpers):

        test_client = OpenReviewClient(username='test@mail.com', password=helpers.strong_password)
        eic_client = OpenReviewClient(username='paula@rlj.org', password=helpers.strong_password)
        mateo_client = OpenReviewClient(username='mateo@rljone.com', password=helpers.strong_password)

        submission_note_1 = test_client.post_note_edit(invitation='RLJ/-/Submission',
            signatures=['~SomeFirstName_User1'],
            note=Note(
                content={
                    'title': { 'value': 'Paper title' },
                    'abstract': { 'value': 'Paper abstract' },
                    'authors': { 'value': ['SomeFirstName User', 'Mia Grant']},
                    'authorids': { 'value': ['~SomeFirstName_User1', '~Mia_Grant1']},
                    'pdf': {'value': '/pdf/' + 'p' * 40 +'.pdf' },
                    'supplementary_material': { 'value': '/attachment/' + 's' * 40 +'.zip'},
                    'is_revision': { 'value': 'No' },
                    'human_subjects_reporting': { 'value': 'N/A' },
                    'disclosure_of_funding': { 'value': 'N/A' }
                }
            ))

        helpers.await_queue_edit(openreview_client, edit_id=submission_note_1['id'])
        note_id_1 = submission_note_1['note']['id']

        note = openreview_client.get_note(note_id_1)
        assert note.readers == ['RLJ', 'RLJ/Paper1/Action_Editors', 'RLJ/Paper1/Authors']
        assert note.content['disclosure_of_funding']['readers'] == ['RLJ', 'RLJ/Paper1/Action_Editors', 'RLJ/Paper1/Authors']
        assert 'competing_interests' not in note.content

        paper_assignment_edge = eic_client.post_edge(openreview.api.Edge(invitation='RLJ/Action_Editors/-/Assignment',
            readers=['RLJ', 'RLJ/Editors_In_Chief', '~Mateo_Rivas1'],
            writers=['RLJ', 'RLJ/Editors_In_Chief'],
            signatures=['RLJ/Editors_In_Chief'],
            head=note_id_1,
            tail='~Mateo_Rivas1',
            weight=1
        ))

        helpers.await_queue_edit(openreview_client, edit_id=paper_assignment_edge.id)

        mateo_paper1_anon_groups = mateo_client.get_groups(prefix='RLJ/Paper1/Action_Editor_.*', signatory='~Mateo_Rivas1')
        assert len(mateo_paper1_anon_groups) == 1
        mateo_paper1_anon_group = mateo_paper1_anon_groups[0]

        under_review_note = mateo_client.post_note_edit(invitation= 'RLJ/Paper1/-/Review_Approval',
                                    signatures=[mateo_paper1_anon_group.id],
                                    note=Note(content={
                                        'under_review': { 'value': 'Appropriate for Review' }
                                    }))

        helpers.await_queue_edit(openreview_client, edit_id=under_review_note['id'])

        edits = openreview_client.get_note_edits(note_id_1, invitation='RLJ/-/Under_Review')
        helpers.await_queue_edit(openreview_client, edit_id=edits[0].id)

        note = openreview_client.get_note(note_id_1)
        assert note.readers == ['RLJ', 'RLJ/Action_Editors', 'RLJ/Paper1/Reviewers', 'RLJ/Paper1/Authors']
        assert note.content['venueid']['value'] == 'RLJ/Under_Review'

        invitation = mateo_client.get_invitation('RLJ/Paper1/Reviewers/-/Assignment')
        assert 'RLJ/Reviewers/-/Role,head:ignore' in invitation.web
        assert 'Invite_Assignment' not in invitation.web

        assert not openreview.tools.get_invitation(openreview_client, 'RLJ/Paper1/-/Official_Recommendation_Enabling')

    def test_review(self, journal, openreview_client, helpers):

        test_client = OpenReviewClient(username='test@mail.com', password=helpers.strong_password)
        mateo_client = OpenReviewClient(username='mateo@rljone.com', password=helpers.strong_password)
        mateo_paper1_anon_group = mateo_client.get_groups(prefix='RLJ/Paper1/Action_Editor_.*', signatory='~Mateo_Rivas1')[0]
        note_id_1 = openreview_client.get_notes(invitation='RLJ/-/Submission')[0].id

        for reviewer in ['~Tomas_Lind1', '~Elena_Moss1']:
            paper_assignment_edge = mateo_client.post_edge(openreview.api.Edge(invitation='RLJ/Reviewers/-/Assignment',
                readers=['RLJ', 'RLJ/Paper1/Action_Editors', reviewer],
                nonreaders=['RLJ/Paper1/Authors'],
                writers=['RLJ', 'RLJ/Paper1/Action_Editors'],
                signatures=[mateo_paper1_anon_group.id],
                head=note_id_1,
                tail=reviewer,
                weight=1
            ))

            helpers.await_queue_edit(openreview_client, edit_id=paper_assignment_edge.id)

        reviewer_roles = { edge.tail: edge.label for edge in mateo_client.get_all_edges(invitation='RLJ/Reviewers/-/Role') }
        assigned_reviewers = openreview_client.get_group('RLJ/Paper1/Reviewers').members
        assert sorted(reviewer_roles[reviewer] for reviewer in assigned_reviewers) == ['Senior Reviewer', 'Technical Reviewer']

        messages = openreview_client.get_messages(to='tomas@rljtwo.com', subject='[RLJ] Assignment to review new RLJ submission 1: Paper title')
        assert len(messages) == 1
        assert 'Once submitted, your review will become privately visible to the AE. Then, as soon as the AE posts a decision, all reviews will become visible to all the reviewers.' in messages[0]['content']['text']

        tomas_client = OpenReviewClient(username='tomas@rljtwo.com', password=helpers.strong_password)
        tomas_anon_group = tomas_client.get_groups(prefix='RLJ/Paper1/Reviewer_.*', signatory='~Tomas_Lind1')[0]

        review_note = tomas_client.post_note_edit(invitation='RLJ/Paper1/-/Review',
            signatures=[tomas_anon_group.id],
            note=Note(
                content={
                    'for_technical_reviewer_claimed_contributions': { 'value': 'The paper claims a new exploration bonus and the experiments support the claim.' },
                    'for_technical_reviewer_polish_and_presentation': { 'value': 'The paper is well written.' },
                    'for_technical_reviewer_additional_comments': { 'value': 'A few typos in the appendix.' }
                }
            )
        )

        helpers.await_queue_edit(openreview_client, edit_id=review_note['id'], process_index=0)
        helpers.await_queue_edit(openreview_client, edit_id=review_note['id'], process_index=1)

        review = openreview_client.get_note(review_note['note']['id'])
        assert review.readers == ['RLJ/Editors_In_Chief', 'RLJ/Paper1/Action_Editors', tomas_anon_group.id]
        assert review.nonreaders == ['RLJ/Paper1/Authors']

        elena_client = OpenReviewClient(username='elena@rljfour.com', password=helpers.strong_password)
        assert len(self.get_reviews(mateo_client, note_id_1)) == 1
        assert len(self.get_reviews(tomas_client, note_id_1)) == 1
        assert len(self.get_reviews(elena_client, note_id_1)) == 0
        assert len(self.get_reviews(test_client, note_id_1)) == 0

        assert len(openreview_client.get_messages(to='mateo@rljone.com', subject='[RLJ] Review posted on submission 1: Paper title')) == 1
        assert len(openreview_client.get_messages(to='test@mail.com', subject='[RLJ] Review posted on submission 1: Paper title')) == 0

        elena_anon_group = elena_client.get_groups(prefix='RLJ/Paper1/Reviewer_.*', signatory='~Elena_Moss1')[0]

        review_note = elena_client.post_note_edit(invitation='RLJ/Paper1/-/Review',
            signatures=[elena_anon_group.id],
            note=Note(
                content={
                    'for_senior_reviewer_general_review': { 'value': 'The results are of interest to the RLJ readers.' },
                    'recommendation': { 'value': 'Accept' }
                }
            )
        )

        helpers.await_queue_edit(openreview_client, edit_id=review_note['id'], process_index=0)
        helpers.await_queue_edit(openreview_client, edit_id=review_note['id'], process_index=1)

        reviews = openreview_client.get_notes(invitation='RLJ/Paper1/-/Review', sort='number:asc')
        assert len(reviews) == 2
        for review in reviews:
            assert review.readers == ['RLJ/Editors_In_Chief', 'RLJ/Paper1/Action_Editors', review.signatures[0]]
            assert review.nonreaders == ['RLJ/Paper1/Authors']

        assert len(self.get_reviews(mateo_client, note_id_1)) == 2
        assert len(self.get_reviews(tomas_client, note_id_1)) == 1
        assert len(self.get_reviews(elena_client, note_id_1)) == 1
        assert len(self.get_reviews(test_client, note_id_1)) == 0
        assert not openreview.tools.get_invitation(openreview_client, 'RLJ/Paper1/-/Review_Release')

        assert not openreview.tools.get_invitation(openreview_client, 'RLJ/Paper1/-/Official_Recommendation')
        for review in reviews:
            assert mateo_client.get_invitation(f'{review.signatures[0]}/-/Rating')

        messages = openreview_client.get_messages(to='mateo@rljone.com', subject='[RLJ] Evaluate reviewers and submit decision for RLJ submission 1: Paper title')
        assert len(messages) == 1
        assert f'To do so, please follow this link: https://openreview.net/forum?id={note_id_1}&invitationId=RLJ/Paper1/-/Decision' in messages[0]['content']['text']

    def test_decision(self, journal, openreview_client, helpers):

        test_client = OpenReviewClient(username='test@mail.com', password=helpers.strong_password)
        eic_client = OpenReviewClient(username='paula@rlj.org', password=helpers.strong_password)
        mateo_client = OpenReviewClient(username='mateo@rljone.com', password=helpers.strong_password)
        tomas_client = OpenReviewClient(username='tomas@rljtwo.com', password=helpers.strong_password)
        mateo_paper1_anon_group = mateo_client.get_groups(prefix='RLJ/Paper1/Action_Editor_.*', signatory='~Mateo_Rivas1')[0]
        note_id_1 = openreview_client.get_notes(invitation='RLJ/-/Submission')[0].id

        reviews = openreview_client.get_notes(invitation='RLJ/Paper1/-/Review', sort='number:asc')
        for review in reviews:
            rating_note = mateo_client.post_note_edit(invitation=f'{review.signatures[0]}/-/Rating',
                signatures=[mateo_paper1_anon_group.id],
                note=Note(
                    content={
                        'rating': { 'value': 'Exceeds expectations' }
                    }
                )
            )
            helpers.await_queue_edit(openreview_client, edit_id=rating_note['id'])

        decision_note = mateo_client.post_note_edit(invitation='RLJ/Paper1/-/Decision',
            signatures=[mateo_paper1_anon_group.id],
            note=Note(
                content={
                    'rlj_decision': { 'value': 'Accept' },
                    'meta_review': { 'value': 'The technical and the senior reviewers agree that the evidence supports the claimed contributions.' },
                    'recommendation': { 'value': 'Accept as is' }
                }
            )
        )

        helpers.await_queue_edit(openreview_client, edit_id=decision_note['id'])

        decision = openreview_client.get_note(decision_note['note']['id'])
        assert decision.readers == ['RLJ/Editors_In_Chief', 'RLJ/Paper1/Action_Editors']
        assert openreview_client.get_note(note_id_1).content['venueid']['value'] == 'RLJ/Decision_Pending'

        reviews = openreview_client.get_notes(invitation='RLJ/Paper1/-/Review', sort='number:asc')
        assert len(reviews) == 2
        for review in reviews:
            assert review.readers == ['RLJ/Editors_In_Chief', 'RLJ/Action_Editors', 'RLJ/Paper1/Reviewers', 'RLJ/Paper1/Authors']
            assert review.nonreaders == []

        assert len(self.get_reviews(test_client, note_id_1)) == 2
        assert len(self.get_reviews(tomas_client, note_id_1)) == 2

        invitation = openreview_client.get_invitation('RLJ/Paper1/-/Review')
        assert invitation.edit['note']['readers'] == ['RLJ/Editors_In_Chief', 'RLJ/Action_Editors', 'RLJ/Paper1/Reviewers', 'RLJ/Paper1/Authors']
        assert invitation.edit['note']['nonreaders'] == []

        approval_note = eic_client.post_note_edit(invitation='RLJ/Paper1/-/Decision_Approval',
            signatures=['RLJ/Editors_In_Chief'],
            note=Note(
                content= {
                    'approval': { 'value': 'I approve the AE\'s decision.' }
                }
            ))

        helpers.await_queue_edit(openreview_client, edit_id=approval_note['id'])

        decision = openreview_client.get_note(decision_note['note']['id'])
        assert decision.readers == ['RLJ/Editors_In_Chief', 'RLJ/Action_Editors', 'RLJ/Paper1/Reviewers', 'RLJ/Paper1/Authors']
        assert decision.nonreaders == []

        messages = openreview_client.get_messages(to='test@mail.com', subject='[RLJ] Decision for your RLJ submission 1: Paper title')
        assert len(messages) == 1

        revision_note = test_client.post_note_edit(invitation='RLJ/Paper1/-/Camera_Ready_Revision',
            signatures=['RLJ/Paper1/Authors'],
            note=Note(
                content={
                    'title': { 'value': 'Paper title' },
                    'abstract': { 'value': 'Paper abstract' },
                    'authors': { 'value': ['SomeFirstName User', 'Mia Grant']},
                    'authorids': { 'value': ['~SomeFirstName_User1', '~Mia_Grant1']},
                    'pdf': {'value': '/pdf/' + 'p' * 40 +'.pdf' },
                    'supplementary_material': { 'value': '/attachment/' + 's' * 40 +'.zip'},
                    'is_revision': { 'value': 'No' },
                    'human_subjects_reporting': { 'value': 'N/A' },
                    'disclosure_of_funding': { 'value': 'N/A' }
                }
            )
        )

        helpers.await_queue_edit(openreview_client, edit_id=revision_note['id'])

        verification_note = mateo_client.post_note_edit(invitation='RLJ/Paper1/-/Camera_Ready_Verification',
            signatures=[mateo_paper1_anon_group.id],
            note=Note(
                signatures=[mateo_paper1_anon_group.id],
                content= {
                    'verification': { 'value': 'I confirm that camera ready manuscript complies with the RLJ stylefile and, if appropriate, includes the minor revisions that were requested.' }
                }
            ))

        helpers.await_queue_edit(openreview_client, edit_id=verification_note['id'])
        helpers.await_queue_edit(openreview_client, invitation='RLJ/-/Accepted')

        note = openreview_client.get_note(note_id_1)
        assert note.readers == ['everyone']
        assert note.content['venueid']['value'] == 'RLJ'

        reviews = openreview_client.get_notes(invitation='RLJ/Paper1/-/Review', sort='number:asc')
        assert len(reviews) == 2
        for review in reviews:
            assert review.readers == ['everyone']
            assert review.nonreaders == []
