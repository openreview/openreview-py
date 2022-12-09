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
    def journal(self, openreview_client):

        eic_client=OpenReviewClient(username='adalca@mit.edu', password='1234')
        eic_client.impersonate('MELBA/Editors_In_Chief')

        requests = openreview_client.get_notes(invitation='openreview.net/Support/-/Journal_Request', content={ 'venue_id': 'MELBA' })

        return JournalRequest.get_journal(eic_client, requests[0].id)      

    def test_setup(self, openreview_client, request_page, selenium, helpers, journal_request):

        ## Support Role
        helpers.create_user('adalca@mit.edu', 'Adrian', 'Dalca')

        ## Editors in Chief
        helpers.create_user('msabuncu@cornell.edu', 'Mert', 'Sabuncu')

        ## Action Editors
        hoel_client = helpers.create_user('hoel@mail.com', 'Hoel', 'Hervadec')
        aasa_client = helpers.create_user('aasa@mailtwo.com', 'Aasa', 'Feragen')
        xukun_client = helpers.create_user('xukun@mail.com', 'Xukun', 'Liu')
        melisa_client = helpers.create_user('ana@mail.com', 'Ana', 'Martinez')
        celeste_client = helpers.create_user('celesste@mail.com', 'Celeste', 'Martinez')

        ## Reviewers
        david_client=helpers.create_user('rev1@mailone.com', 'MELBARev', 'One')
        javier_client=helpers.create_user('rev2@mailtwo.com', 'MELBARev', 'Two')
        carlos_client=helpers.create_user('rev3@mailthree.com', 'MELBARev', 'Three')
        andrew_client = helpers.create_user('rev4@mailfour.com', 'MELBARev', 'Four')
        hugo_client = helpers.create_user('rev5@mailfive.com', 'MELBARev', 'Five')

        #post journal request form
        request_form = openreview_client.post_note_edit(invitation= 'openreview.net/Support/-/Journal_Request',
            signatures = ['openreview.net/Support'],
            note = Note(
                signatures = ['openreview.net/Support'],
                content = {
                    'official_venue_name': {'value': 'The Journal of Machine Learning for Biomedical Imaging'},
                    'abbreviated_venue_name' : {'value': 'MELBA'},
                    'venue_id': {'value': 'MELBA'},
                    'contact_info': {'value': 'editors@melba-journal.org'},
                    'secret_key': {'value': '1234'},
                    'support_role': {'value': '~Adrian_Dalca1' },
                    'editors': {'value': ['~Mert_Sabuncu1', '~Adrian_Dalca1'] },
                    'website': {'value': 'melba-journal.org' },
                    'settings': {
                        'value': {
                            'submission_public': False,
                            'author_anonymity': True,
                            'assignment_delay': 0,
                            'show_conflict_details': True
                        }
                    }
                }
            ))

        helpers.await_queue_edit(openreview_client, request_form['id'])


    def test_invite_action_editors(self, journal, openreview_client, request_page, selenium, helpers):

        venue_id = 'MELBA'

        request_notes = openreview_client.get_notes(invitation='openreview.net/Support/-/Journal_Request', content= { 'venue_id': 'MELBA' })
        request_note_id = request_notes[0].id
        journal = JournalRequest.get_journal(openreview_client, request_note_id)
        
        journal.invite_action_editors(message='Test {{fullname}},  {{accept_url}}, {{decline_url}}', subject='[MELBA] Invitation to be an Action Editor', invitees=['new_user@mail.com', 'hoel@mail.com', '~Xukun_Liu1', 'aasa@mailtwo.com', '~Ana_Martinez1'])
        invited_group = openreview_client.get_group(f'{venue_id}/Action_Editors/Invited')
        assert invited_group.members == ['new_user@mail.com', '~Hoel_Hervadec1', '~Xukun_Liu1', '~Aasa_Feragen1', '~Ana_Martinez1']

        messages = openreview_client.get_messages(subject = '[MELBA] Invitation to be an Action Editor')
        assert len(messages) == 5

        for message in messages:
            text = message['content']['text']
            accept_url = re.search('https://.*response=Yes', text).group(0).replace('https://openreview.net', 'http://localhost:3030').replace('&amp;', '&')
            request_page(selenium, accept_url, alert=True)

        helpers.await_queue_edit(openreview_client, invitation = 'MELBA/Action_Editors/-/Recruitment')


        group = openreview_client.get_group(f'{venue_id}/Action_Editors')
        assert len(group.members) == 5
        assert '~Aasa_Feragen1' in group.members

    def test_invite_reviewers(self, journal, openreview_client, request_page, selenium, helpers):

        venue_id = 'MELBA'
        request_notes = openreview_client.get_notes(invitation='openreview.net/Support/-/Journal_Request', content= { 'venue_id': 'MELBA' })
        request_note_id = request_notes[0].id
        journal = JournalRequest.get_journal(openreview_client, request_note_id)

        journal.invite_reviewers(message='Test {{fullname}},  {{accept_url}}, {{decline_url}}', subject='[MELBA] Invitation to be a Reviewer', invitees=['rev1@mailone.com', 'rev4@mailfour.com', 'rev3@mailthree.com', 'rev2@mailtwo.com', 'rev5@mailfive.com'])
        invited_group = openreview_client.get_group(f'{venue_id}/Reviewers/Invited')
        assert invited_group.members == ['~MELBARev_One1', '~MELBARev_Four1', '~MELBARev_Three1', '~MELBARev_Two1', '~MELBARev_Five1']

        messages = openreview_client.get_messages(subject = '[MELBA] Invitation to be a Reviewer')
        assert len(messages) == 5

        for message in messages:
            text = message['content']['text']
            accept_url = re.search('https://.*response=Yes', text).group(0).replace('https://openreview.net', 'http://localhost:3030').replace('&amp;', '&')
            request_page(selenium, accept_url, alert=True)

        helpers.await_queue_edit(openreview_client, invitation = 'MELBA/Reviewers/-/Recruitment')

        group = openreview_client.get_group(f'{venue_id}/Reviewers/Invited')
        assert len(group.members) == 5
        assert '~MELBARev_One1' in group.members

        status = journal.invite_reviewers(message='Test {{fullname}},  {{accept_url}}, {{decline_url}}', subject='[MELBA] Invitation to be a Reviewer', invitees=['rev1@mailone.com'])
        messages = openreview_client.get_messages(to = 'rev1@mailone.com', subject = '[MELBA] Invitation to be a Reviewer')
        assert len(messages) == 1

        assert status.get('already_member')
        assert 'rev1@mailone.com' in status.get('already_member')

    def test_submission(self, journal, openreview_client, test_client, helpers):

        venue_id = journal.venue_id
        test_client = OpenReviewClient(username='test@mail.com', password='1234')

        ## Post the submission 1
        submission_note_1 = test_client.post_note_edit(invitation=f'{venue_id}/-/Submission',
            signatures=['~SomeFirstName_User1'],
            note=Note(
                content={
                    'title': { 'value': 'Paper title' },
                    'abstract': { 'value': 'Paper abstract' },
                    'authors': { 'value': ['Test User', 'Celeste Martinez']},
                    'authorids': { 'value': ['~SomeFirstName_User1', '~Celeste_Martinez1']},
                    'pdf': {'value': '/pdf/' + 'p' * 40 +'.pdf' },
                    'competing_interests': { 'value': 'None beyond the authors normal conflict of interests'},
                    'human_subjects_reporting': { 'value': 'Not applicable'},
                    'submission_length': { 'value': 'Regular submission (no more than 12 pages of main content)'}
                }
            ))

        helpers.await_queue_edit(openreview_client, edit_id=submission_note_1['id'])
        note_id_1 = submission_note_1['note']['id']

        messages = journal.client.get_messages(to = 'test@mail.com', subject = '[MELBA] Suggest candidate Action Editor for your new MELBA submission')
        assert len(messages) == 1
        assert messages[0]['content']['text'] == '''Hi SomeFirstName User,

Thank you for submitting your work titled "Paper title" to MELBA.

Before the review process starts, you need to submit one or more recommendations for an Action Editor that you believe has the expertise to oversee the evaluation of your work.

To do so, please follow this link: https://openreview.net/invitation?id=MELBA/Paper1/Action_Editors/-/Recommendation or check your tasks in the Author Console: https://openreview.net/group?id=MELBA/Authors

For more details and guidelines on the MELBA review process, visit melba-journal.org.

The MELBA Editors-in-Chief
'''

    def test_ae_assignment(self, journal, openreview_client, test_client, helpers):

        venue_id = journal.venue_id
        
        aasa_client = OpenReviewClient(username='aasa@mailtwo.com', password='1234')
        eic_client = OpenReviewClient(username='adalca@mit.edu', password='1234')
        
        note = openreview_client.get_notes(invitation='MELBA/-/Submission')[0]
        note_id_1 = note.id
        #journal.invitation_builder.expire_paper_invitations(note)

        journal.setup_ae_assignment(note)

        conflicts = openreview_client.get_edges(invitation='MELBA/Action_Editors/-/Conflict')
        assert conflicts
        assert conflicts[0].label == 'mail.com'

        # Assign Action Editor
        editor_in_chief_group_id = 'MELBA/Editors_In_Chief'
        paper_assignment_edge = eic_client.post_edge(openreview.Edge(invitation='MELBA/Action_Editors/-/Assignment',
            readers=[venue_id, editor_in_chief_group_id, '~Aasa_Feragen1'],
            writers=[venue_id, editor_in_chief_group_id],
            signatures=[editor_in_chief_group_id],
            head=note_id_1,
            tail='~Aasa_Feragen1',
            weight=1
        ))

        helpers.await_queue_edit(openreview_client, edit_id=paper_assignment_edge.id)

        ## Accept the submission 1
        under_review_note = aasa_client.post_note_edit(invitation= 'MELBA/Paper1/-/Review_Approval',
                                    signatures=[f'{venue_id}/Paper1/Action_Editors'],
                                    note=Note(content={
                                        'under_review': { 'value': 'Appropriate for Review' }
                                    }))

        helpers.await_queue_edit(openreview_client, edit_id=under_review_note['id'])

        # Assign reviewer 1
        paper_assignment_edge = aasa_client.post_edge(openreview.Edge(invitation='MELBA/Reviewers/-/Assignment',
            readers=[venue_id, f"{venue_id}/Paper1/Action_Editors", '~MELBARev_One1'],
            nonreaders=[f"{venue_id}/Paper1/Authors"],
            writers=[venue_id, f"{venue_id}/Paper1/Action_Editors"],
            signatures=[f"{venue_id}/Paper1/Action_Editors"],
            head=note_id_1,
            tail='~MELBARev_One1',
            weight=1
        ))
        
        # Assign reviewer 2
        paper_assignment_edge = aasa_client.post_edge(openreview.Edge(invitation='MELBA/Reviewers/-/Assignment',
            readers=[venue_id, f"{venue_id}/Paper1/Action_Editors", '~MELBARev_Two1'],
            nonreaders=[f"{venue_id}/Paper1/Authors"],
            writers=[venue_id, f"{venue_id}/Paper1/Action_Editors"],
            signatures=[f"{venue_id}/Paper1/Action_Editors"],
            head=note_id_1,
            tail='~MELBARev_Two1',
            weight=1
        ))

        # Assign reviewer 3
        paper_assignment_edge = aasa_client.post_edge(openreview.Edge(invitation='MELBA/Reviewers/-/Assignment',
            readers=[venue_id, f"{venue_id}/Paper1/Action_Editors", '~MELBARev_Three1'],
            nonreaders=[f"{venue_id}/Paper1/Authors"],
            writers=[venue_id, f"{venue_id}/Paper1/Action_Editors"],
            signatures=[f"{venue_id}/Paper1/Action_Editors"],
            head=note_id_1,
            tail='~MELBARev_Three1',
            weight=1
        ))

        ## Post a review edit
        reviewer_one_client = OpenReviewClient(username='rev1@mailone.com', password='1234')
        reviewer_one_anon_groups=reviewer_one_client.get_groups(prefix=f'{venue_id}/Paper1/Reviewer_.*', signatory='~MELBARev_One1')
        
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

        helpers.await_queue_edit(openreview_client, edit_id=review_note['id'])

        reviewer_two_client = OpenReviewClient(username='rev2@mailtwo.com', password='1234')
        reviewer_two_anon_groups=reviewer_two_client.get_groups(prefix=f'{venue_id}/Paper1/Reviewer_.*', signatory='~MELBARev_Two1')
    
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

        helpers.await_queue_edit(openreview_client, edit_id=review_note['id'])

        reviewer_three_client = OpenReviewClient(username='rev3@mailthree.com', password='1234')
        reviewer_three_anon_groups=reviewer_two_client.get_groups(prefix=f'{venue_id}/Paper1/Reviewer_.*', signatory='~MELBARev_Three1')

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

        helpers.await_queue_edit(openreview_client, edit_id=review_note['id'])

        reviews=openreview_client.get_notes(forum=note_id_1, invitation=f'{venue_id}/Paper1/-/Review', sort='number:desc')
        assert len(reviews) == 3
        assert reviews[0].readers == [f"{venue_id}/Editors_In_Chief", f"{venue_id}/Paper1/Action_Editors", f"{venue_id}/Paper1/Reviewers", f"{venue_id}/Paper1/Authors"]
        assert reviews[1].readers == [f"{venue_id}/Editors_In_Chief", f"{venue_id}/Paper1/Action_Editors", f"{venue_id}/Paper1/Reviewers", f"{venue_id}/Paper1/Authors"]
        assert reviews[2].readers == [f"{venue_id}/Editors_In_Chief", f"{venue_id}/Paper1/Action_Editors", f"{venue_id}/Paper1/Reviewers", f"{venue_id}/Paper1/Authors"]

        invitation = eic_client.get_invitation(f'{venue_id}/Paper1/-/Official_Recommendation')
        assert invitation.cdate > openreview.tools.datetime_millis(datetime.datetime.utcnow())

        eic_client.post_invitation_edit(
            invitations='MELBA/-/Edit',
            readers=[venue_id],
            writers=[venue_id],
            signatures=[venue_id],
            invitation=openreview.api.Invitation(id=f'{venue_id}/Paper1/-/Official_Recommendation',
                cdate=openreview.tools.datetime_millis(datetime.datetime.utcnow()) + 1000,
                signatures=['MELBA/Editors_In_Chief']
            )
        )

        time.sleep(5) ## wait until the process function runs

        ## Post a review recommendation
        official_recommendation_note = reviewer_one_client.post_note_edit(invitation=f'{venue_id}/Paper1/-/Official_Recommendation',
            signatures=[reviewer_one_anon_groups[0].id],
            note=Note(
                content={
                    'decision_recommendation': { 'value': 'Accept' },
                    'claims_and_evidence': { 'value': 'Yes' },
                    'audience': { 'value': 'Yes' }                  
                }
            )
        )

        helpers.await_queue_edit(openreview_client, edit_id=official_recommendation_note['id'])

        official_recommendation_note = reviewer_two_client.post_note_edit(invitation=f'{venue_id}/Paper1/-/Official_Recommendation',
            signatures=[reviewer_two_anon_groups[0].id],
            note=Note(
                content={
                    'decision_recommendation': { 'value': 'Accept' },
                    'claims_and_evidence': { 'value': 'Yes' },
                    'audience': { 'value': 'Yes' }                  
                }
            )
        )

        helpers.await_queue_edit(openreview_client, edit_id=official_recommendation_note['id']) 

        official_recommendation_note = reviewer_three_client.post_note_edit(invitation=f'{venue_id}/Paper1/-/Official_Recommendation',
            signatures=[reviewer_three_anon_groups[0].id],
            note=Note(
                content={
                    'decision_recommendation': { 'value': 'Accept' },
                    'claims_and_evidence': { 'value': 'Yes' },
                    'audience': { 'value': 'Yes' }                  
                }
            )
        )

        helpers.await_queue_edit(openreview_client, edit_id=official_recommendation_note['id'])                
