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
        eic_client.impersonate('JMLR/Editors_In_Chief')

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
                            'assignment_delay': 0
                        }
                    }
                }
            ))

        helpers.await_queue_edit(openreview_client, request_form['id'])

        ## Authors
        celeste_client=helpers.create_user('celeste@jmlrone.com', 'Celeste', 'Azul')

    
    
    def test_submission(self, journal, openreview_client, test_client, helpers):

        test_client = OpenReviewClient(username='test@mail.com', password=helpers.strong_password)

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

        author_group=openreview_client.get_group("JMLR/Paper1/Authors")
        assert author_group
        assert author_group.members == ['~SomeFirstName_User1', '~Celeste_Azul1']
        assert openreview_client.get_group("JMLR/Paper1/Reviewers")
        assert openreview_client.get_group("JMLR/Paper1/Action_Editors")

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


