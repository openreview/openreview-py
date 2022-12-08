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
        aasa_client = helpers.create_user('aasa@mail.com', 'Aasa', 'Feragen')
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
                            'assignment_delay': 0
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
        
        journal.invite_action_editors(message='Test {{fullname}},  {{accept_url}}, {{decline_url}}', subject='[MELBA] Invitation to be an Action Editor', invitees=['new_user@mail.com', 'hoel@mail.com', '~Xukun_Liu1', 'aasa@mail.com', '~Ana_Martinez1'])
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

        messages = journal.client.get_messages(to = 'test@mail.com', subject = '[MELBA] Suggest candidate Action Editor for your new MELBA submission')
        assert len(messages) == 1
        assert messages[0]['content']['text'] == '''Hi SomeFirstName User,

Thank you for submitting your work titled "Paper title" to MELBA.

Before the review process starts, you need to submit one or more recommendations for an Action Editor that you believe has the expertise to oversee the evaluation of your work.

To do so, please follow this link: https://openreview.net/invitation?id=MELBA/Paper1/Action_Editors/-/Recommendation or check your tasks in the Author Console: https://openreview.net/group?id=MELBA/Authors

For more details and guidelines on the MELBA review process, visit melba-journal.org.

The MELBA Editors-in-Chief
'''

        note = openreview_client.get_note(submission_note_1['note']['id'])
        journal.invitation_builder.expire_paper_invitations(note)