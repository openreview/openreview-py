import openreview
import pytest
import time
import json
import datetime
import random
import os
import re
from string import ascii_lowercase as alc
from openreview.api import OpenReviewClient
from openreview.api import Note
from openreview.journal import Journal
from openreview.journal import JournalRequest
from selenium.webdriver.common.by import By
from urllib.parse import urlparse, parse_qs

class TestJournalActiveProfiles():

    @pytest.fixture(scope="class")
    def journal(self, openreview_client, helpers):

        venue_id = 'JAPR'
        marco_client=OpenReviewClient(username='marco@mail.com', password=helpers.strong_password)
        marco_client.impersonate('JAPR')

        requests = openreview_client.get_notes(invitation='openreview.net/Support/-/Journal_Request', content={ 'venue_id': venue_id })

        return JournalRequest.get_journal(marco_client, requests[0].id)

    def test_setup(self, openreview_client, request_page, selenium, helpers, journal_request):

        venue_id = 'JAPR'

        ## Support Role
        helpers.create_user('marco@mail.com', 'Marco', 'Support')

        ## Editors in Chief
        helpers.create_user('lucia@mail.com', 'Lucia', 'EIC')
        helpers.create_user('tomoko@mail.com', 'Tomoko', 'EIC')

        ## Action Editors
        helpers.create_user('amara@mailseven.com', 'Amara', 'AEditor')
        helpers.create_user('nikolai@mail.com', 'Nikolai', 'AEditor')
        helpers.create_user('priya@sharma.com', 'Priya', 'AEditor')
        helpers.create_user('henrik@mail.com', 'Henrik', 'AEditor')
        helpers.create_user('elena@mail.com', 'Elena', 'AEditor')
        helpers.create_user('kenji@mail.com', 'Kenji', 'AEditor')
        helpers.create_user('fatima@mail.com', 'Fatima', 'AEditor')
        helpers.create_user('ingrid@apple.com', 'Ingrid', 'AEditor')

        ## Reviewers
        helpers.create_user('omar@mailone.com', 'Omar', 'Reviewer')
        helpers.create_user('yuki@mailtwo.com', 'Yuki', 'Reviewer')
        helpers.create_user('lena@mailthree.com', 'Lena', 'Reviewer')
        helpers.create_user('sofia@mailfour.com', 'Sofia', 'Reviewer')
        helpers.create_user('wei@mailsix.com', 'Wei', 'Reviewer')
        helpers.create_user('omar@mailone.com', 'Omar', 'Reviewer')

        ## External Reviewers
        helpers.create_user('anika@mailten.com', 'Anika', 'ExtReviewer')

        ## Authors
        helpers.create_user('jonas@maileight.com', 'Jonas', 'Author')
        helpers.create_user('rosa@mailnine.com', 'Rosa', 'Author')
        helpers.create_user('grace@mailseven.com', 'Grace', 'Author')

        #post journal request form
        request_form = openreview_client.post_note_edit(invitation= 'openreview.net/Support/-/Journal_Request',
            signatures = ['openreview.net/Support'],
            note = Note(
                signatures = ['openreview.net/Support'],
                content = {
                    'official_venue_name': {'value': 'Journal of Active Profiles Research'},
                    'abbreviated_venue_name' : {'value': 'JAPR'},
                    'venue_id': {'value': 'JAPR'},
                    'contact_info': {'value': 'tmlr@jmlr.org'},
                    'secret_key': {'value': openreview.tools.create_hash_seed()},
                    'support_role': {'value': '~Marco_Support1' },
                    'editors': {'value': ['~Lucia_EIC1', '~Tomoko_EIC1'] },
                    'website': {'value': 'jmlr.org/tmlr' },
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
                            'eic_certifications': [
                                'Outstanding Certification'
                            ],
                            'event_certifications': [
                                'lifelong-ml.cc/CoLLAs/2023/Journal_Track'
                            ],
                            'submission_length': [
                                'Regular submission (no more than 12 pages of main content)',
                                'Long submission (more than 12 pages of main content)',
                                'Beyond PDF submission (pageless, webpage-style content)'
                            ],
                            'issn': '2835-8856',
                            'website_urls': {
                                'editorial_board': 'https://jmlr.org/tmlr/editorial-board.html',
                                'evaluation_criteria': 'https://jmlr.org/tmlr/editorial-policies.html#evaluation',
                                'reviewer_guide': 'https://jmlr.org/tmlr/reviewer-guide.html',
                                'editorial_policies': 'https://jmlr.org/tmlr/editorial-policies.html',
                                'faq': 'https://jmlr.org/tmlr/contact.html',
                                'videos': 'https://tmlr.infinite-conf.org',
                                'certifications_criteria': 'https://jmlr.org/tmlr/editorial-policies.html#certifications'
                            },
                            'editors_email': 'tmlr-editors@jmlr.org',
                            'skip_ac_recommendation': False,
                            'number_of_reviewers': 3,
                            'reviewers_max_papers': 6,
                            'ae_recommendation_period': 1,
                            'under_review_approval_period': 1,
                            'reviewer_assignment_period': 1,
                            'review_period': 2,
                            'discussion_period' : 2,
                            'recommendation_period': 2,
                            'decision_period': 1,
                            'camera_ready_period': 4,
                            'camera_ready_verification_period': 1,
                            'archived_action_editors': True,
                            'archived_reviewers': True,
                            'expert_reviewers': True,
                            'external_reviewers': True,
                            'expertise_model': 'specter2+scincl',
                            'assignment_delay_after_submitted_review': 0.0001,   # ~ 1 minute
                            'max_solicit_review_per_month': 3,
                            'enable_blocked_authors': True,
                            'force_active_profiles': True
                        }
                    }
                }
            ))

        helpers.await_queue_edit(openreview_client, request_form['id'])

        openreview_client.add_members_to_group('JAPR/Expert_Reviewers', ['~Sofia_Reviewer1'])

        japr =  openreview_client.get_group('JAPR')
        assert japr
        assert japr.members == ['~Marco_Support1', 'JAPR/Editors_In_Chief']
        assert japr.content['submission_id']['value'] == 'JAPR/-/Submission'
        assert japr.content['certifications']['value'] == ['Featured Certification', 'Reproducibility Certification', 'Survey Certification']
        assert japr.content['eic_certifications']['value'] == ['Outstanding Certification']
        assert japr.content['expert_reviewer_certification']['value'] == 'Expert Certification'
        assert japr.content['event_certifications']['value'] == ['lifelong-ml.cc/CoLLAs/2023/Journal_Track']

        invitation = openreview_client.get_invitation('JAPR/-/Accepted')

        assert 'expert_reviewers' in invitation.edit['note']['content']
        assert openreview_client.get_group('JAPR/Reviewers/Archived')

        openreview_client.post_group_edit(
            invitation='JAPR/-/Edit',
            signatures=['JAPR'],
            group=openreview.api.Group(
                id='JAPR/Authors',
                content={
                    'new_submission_email_template_script': { 'delete': True },
                    'official_recommendation_starts_email_template_script': { 'delete': True }
                }
            )
        )

        assert openreview.tools.get_invitation(openreview_client, 'JAPR/-/Preferred_Emails')
        assert openreview_client.get_edges_count(invitation='JAPR/-/Preferred_Emails') == 0

        invitation = openreview_client.get_invitation('JAPR/-/Submission')

        assert invitation.post_processes

        openreview_client.add_members_to_group('JAPR/Submission_Banned_Users', ['rosa@mailnine.com'])

    def test_post_submissions(self, openreview_client, journal, helpers):

        venue_id = 'JAPR'

        ## Create author client
        jonas_client = OpenReviewClient(username='jonas@maileight.com', password=helpers.strong_password)

        ## Post submission 1
        submission_note_1 = jonas_client.post_note_edit(invitation='JAPR/-/Submission',
            signatures=['~Jonas_Author1'],
            note=Note(
                content={
                    'title': { 'value': 'Active Profile Detection in Large Networks' },
                    'abstract': { 'value': 'We propose a method for detecting active profiles in large-scale networks.' },
                    'authors': { 'value': ['Jonas Author', 'Rosa Author']},
                    'authorids': { 'value': ['~Jonas_Author1', '~Rosa_Author1']},
                    'pdf': {'value': '/pdf/' + 'p' * 40 +'.pdf' },
                    'competing_interests': { 'value': 'None beyond the authors normal conflict of interests'},
                    'human_subjects_reporting': { 'value': 'Not applicable'},
                    'submission_length': { 'value': 'Regular submission (no more than 12 pages of main content)'}
                }
            ))

        helpers.await_queue_edit(openreview_client, edit_id=submission_note_1['id'])
        note_id_1 = submission_note_1['note']['id']

        note = openreview_client.get_note(note_id_1)
        assert note
        assert note.invitations == ['JAPR/-/Submission']
        assert note.readers == ['JAPR', 'JAPR/Paper1/Action_Editors', 'JAPR/Paper1/Authors']
        assert note.writers == ['JAPR', 'JAPR/Paper1/Authors']
        assert note.signatures == ['JAPR/Paper1/Authors']
        assert note.content['authorids']['value'] == ['~Jonas_Author1', '~Rosa_Author1']
        assert note.content['venue']['value'] == 'Submitted to JAPR'
        assert note.content['venueid']['value'] == 'JAPR/Submitted'

        author_group = openreview_client.get_group(f'{venue_id}/Paper1/Authors')
        assert author_group
        assert author_group.members == ['~Jonas_Author1', '~Rosa_Author1']
        assert openreview_client.get_group(f'{venue_id}/Paper1/Reviewers')
        assert openreview_client.get_group(f'{venue_id}/Paper1/Action_Editors')

        ## Post submission 2
        submission_note_2 = jonas_client.post_note_edit(invitation='JAPR/-/Submission',
            signatures=['~Jonas_Author1'],
            note=Note(
                content={
                    'title': { 'value': 'Profile Clustering with Graph Neural Networks' },
                    'abstract': { 'value': 'A novel approach to clustering user profiles using graph neural networks.' },
                    'authors': { 'value': ['Jonas Author']},
                    'authorids': { 'value': ['~Jonas_Author1']},
                    'pdf': {'value': '/pdf/' + 'q' * 40 +'.pdf' },
                    'competing_interests': { 'value': 'None beyond the authors normal conflict of interests'},
                    'human_subjects_reporting': { 'value': 'Not applicable'},
                    'submission_length': { 'value': 'Regular submission (no more than 12 pages of main content)'}
                }
            ))

        helpers.await_queue_edit(openreview_client, edit_id=submission_note_2['id'])
        note_id_2 = submission_note_2['note']['id']

        note = openreview_client.get_note(note_id_2)
        assert note
        assert note.invitations == ['JAPR/-/Submission']
        assert note.content['venue']['value'] == 'Submitted to JAPR'
        assert note.content['venueid']['value'] == 'JAPR/Submitted'

        # Reject author profile
        openreview_client.moderate_profile('~Grace_Author1', 'reject')

        with pytest.raises(openreview.OpenReviewException, match=r'authorids value/1 ~Grace_Author1 has "Rejected" state which does not meet the minimum required state of Active'):
            ## Post submission 3
            submission_note_3 = jonas_client.post_note_edit(invitation='JAPR/-/Submission',
                signatures=['~Jonas_Author1'],
                note=Note(
                    content={
                        'title': { 'value': 'Temporal Analysis of Profile Activity Patterns' },
                        'abstract': { 'value': 'We study temporal patterns in user profile activity across social platforms.' },
                        'authors': { 'value': ['Jonas Author', 'Grace Author']},
                        'authorids': { 'value': ['~Jonas_Author1', '~Grace_Author1']},
                        'pdf': {'value': '/pdf/' + 'r' * 40 +'.pdf' },
                        'competing_interests': { 'value': 'None beyond the authors normal conflict of interests'},
                        'human_subjects_reporting': { 'value': 'Not applicable'},
                        'submission_length': { 'value': 'Long submission (more than 12 pages of main content)'}
                    }
                ))