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

class TestJournalMatching():


    @pytest.fixture(scope="class")
    def journal(self):
        venue_id = 'CARP'
        manuel_client=OpenReviewClient(username='manuel@mail.com', password='1234')
        manuel_client.impersonate('CARP/Editors_In_Chief')
        journal=Journal(manuel_client, venue_id, '1234', contact_info='tmlr@jmlr.org', full_name='CARP Journal', short_name='CARP', submission_name='Submission')
        return journal

    def test_setup(self, openreview_client, request_page, selenium, helpers):

        venue_id = 'CARP'

        ## Support Role
        helpers.create_user('manuel@mail.com', 'Manuel', 'Puig')

        ## Editors in Chief
        helpers.create_user('emily@mail.com', 'Emily', 'Dickinson')

        ## Action Editors
        helpers.create_user('ana@prada.com', 'Ana', 'Prada')
        helpers.create_user('paul@mail.com', 'Paul', 'McCartney')
        helpers.create_user('john@lennon.com', 'John', 'Lennon')
        helpers.create_user('janis@joplin.com', 'Janin', 'Joplin')

        ## Authors
        helpers.create_user('sigur@ros.com', 'Sigur', 'Ros')
        helpers.create_user('john@travolta.com', 'John', 'Travolta')

        journal=Journal(openreview_client, venue_id, '1234', contact_info='tmlr@jmlr.org', full_name='CARP Journal', short_name='CARP', submission_name='Submission')
        journal.setup(support_role='manuel@mail.com', editors=['~Emiliy_Dickinson1'])

        openreview_client.add_members_to_group('CARP/Action_Editors', ['ana@prada.com', 'paul@mail.com', 'john@lennon.com', 'janis@joplin.com'])


    def test_submission(self, journal, openreview_client, test_client, helpers):

        venue_id = journal.venue_id
        test_client = OpenReviewClient(username='test@mail.com', password='1234')
        ana_client = OpenReviewClient(username='ana@prada.com', password='1234')

        ## Set a max quota
        ana_client.post_edge(openreview.Edge(invitation='CARP/Action_Editors/-/Custom_Max_Papers',
            readers=[venue_id, '~Ana_Prada1'],
            writers=[venue_id, '~Ana_Prada1'],
            signatures=['~Ana_Prada1'],
            head='CARP/Action_Editors',
            tail='~Ana_Prada1',
            weight=3
        ))

        for i in range(1,6):
            test_client.post_note_edit(invitation='CARP/-/Submission',
                signatures=['~SomeFirstName_User1'],
                note=Note(
                    content={
                        'title': { 'value': f'Paper title {i}' },
                        'abstract': { 'value': 'Paper abstract' },
                        'authors': { 'value': ['SomeFirstName User', 'Sigur Ros', 'John Travolta']},
                        'authorids': { 'value': ['~SomeFirstName_User1', '~Sigur_Ros1', '~John_Travolta1']},
                        'pdf': {'value': '/pdf/' + 'p' * 40 +'.pdf' },
                        'competing_interests': { 'value': 'None beyond the authors normal conflict of interests'},
                        'human_subjects_reporting': { 'value': 'Not applicable'},
                        'submission_length': { 'value': 'Regular submission (no more than 12 pages of main content)'}
                    }
                ))
       
       ### Post AE recommendations
       ### Post AE affinity scores
       ### Post AE conflicts

       ### Setup matching
       

