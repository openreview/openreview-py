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
        helpers.create_user('janis@joplin.com', 'Janis', 'Joplin')
        helpers.create_user('diego@armando.com', 'Diego', 'Armando')
        helpers.create_user('ken@beck.com', 'Ken', 'Beck')

        ## Authors
        helpers.create_user('sigur@ros.com', 'Sigur', 'Ros')
        helpers.create_user('john@travolta.com', 'John', 'Travolta')

        journal=Journal(openreview_client, venue_id, '1234', contact_info='tmlr@jmlr.org', full_name='CARP Journal', short_name='CARP', submission_name='Submission')
        journal.setup(support_role='manuel@mail.com', editors=['~Emily_Dickinson1'])

        openreview_client.add_members_to_group('CARP/Action_Editors', ['~Ana_Prada1', '~Paul_McCartney1', '~John_Lennon1', '~Janis_Joplin1', '~Diego_Armando1', '~Ken_Beck1'])


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
       
        submissions = openreview_client.get_notes(invitation='CARP/-/Submission', sort='number:asc')

        ### Post AE affinity scores
        for submission in submissions:
            for ae in openreview_client.get_group('CARP/Action_Editors').members:
                openreview_client.post_edge(openreview.api.Edge(invitation='CARP/Action_Editors/-/Affinity_Score',
                    head=submission.id,
                    tail=ae,
                    weight=0.5
                ))

        ### Post AE conflicts
        openreview_client.post_edge(openreview.api.Edge(invitation='CARP/Action_Editors/-/Conflict',
            head=submissions[0].id,
            tail='~Janis_Joplin1',
            weight=-1,
            label='Conflict'
        ))         
        openreview_client.post_edge(openreview.api.Edge(invitation='CARP/Action_Editors/-/Conflict',
            head=submissions[1].id,
            tail='~Ana_Prada1',
            weight=-1,
            label='Conflict'
        ))         
        openreview_client.post_edge(openreview.api.Edge(invitation='CARP/Action_Editors/-/Conflict',
            head=submissions[2].id,
            tail='~Ana_Prada1',
            weight=-1,
            label='Conflict'
        )) 


        ### Post AE recommendations
        ## Paper 1
        test_client.post_edge(openreview.api.Edge(invitation='CARP/Action_Editors/-/Recommendation',
            head=submissions[0].id,
            tail='~Ana_Prada1',
            weight=1
        ))    


        test_client.post_edge(openreview.api.Edge(invitation='CARP/Action_Editors/-/Recommendation',
            head=submissions[0].id,
            tail='~Paul_McCartney1',
            weight=1
        ))    

        test_client.post_edge(openreview.api.Edge(invitation='CARP/Action_Editors/-/Recommendation',
            head=submissions[0].id,
            tail='~John_Lennon1',
            weight=1
        ))    

        ## Paper 2
        test_client.post_edge(openreview.api.Edge(invitation='CARP/Action_Editors/-/Recommendation',
            head=submissions[1].id,
            tail='~Janis_Joplin1',
            weight=1
        ))    


        test_client.post_edge(openreview.api.Edge(invitation='CARP/Action_Editors/-/Recommendation',
            head=submissions[1].id,
            tail='~Paul_McCartney1',
            weight=1
        ))    

        test_client.post_edge(openreview.api.Edge(invitation='CARP/Action_Editors/-/Recommendation',
            head=submissions[1].id,
            tail='~John_Lennon1',
            weight=1
        ))    

        ## Paper 3
        test_client.post_edge(openreview.api.Edge(invitation='CARP/Action_Editors/-/Recommendation',
            head=submissions[2].id,
            tail='~Janis_Joplin1',
            weight=1
        ))    


        test_client.post_edge(openreview.api.Edge(invitation='CARP/Action_Editors/-/Recommendation',
            head=submissions[2].id,
            tail='~Paul_McCartney1',
            weight=1
        ))    

        test_client.post_edge(openreview.api.Edge(invitation='CARP/Action_Editors/-/Recommendation',
            head=submissions[2].id,
            tail='~John_Lennon1',
            weight=1
        )) 

        ### Setup matching
        journal.setup_ae_matching()

        ## Post a configuration note
        emily_client=OpenReviewClient(username='emily@mail.com', password='1234')
        
        emily_client.post_note_edit(invitation='CARP/Action_Editors/-/Assignment_Configuration',
                signatures=['CARP'],
                note=Note(
                    content={
                        'title': { 'value': 'test-1' },
                        'min_papers': { 'value': '0' },
                        'max_papers': { 'value': '1' },
                        'user_demand': { 'value': '1' },
                        'alternates': { 'value': '2' },
                        'scores_specification': { 'value': {
                            'CARP/Action_Editors/-/Affinity_Score': {'weight': 1, 'default': 0},
                            'CARP/Action_Editors/-/Recommendation': {'weight': 1, 'default': 0}
                        } },
                        'solver': { 'value': 'MinMax' },
                        'allow_zero_score_assignments': { 'value': 'No' },
                        'status': { 'value': 'Initialized' },
                    }
                ))

