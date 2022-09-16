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

class TestJournalMatching():


    @pytest.fixture(scope="class")
    def journal(self, openreview_client):

        manuel_client=OpenReviewClient(username='manuel@mail.com', password='1234')
        manuel_client.impersonate('CARP/Editors_In_Chief')

        requests = openreview_client.get_notes(invitation='openreview.net/Support/-/Journal_Request', content={ 'venue_id': 'CARP' })

        return JournalRequest.get_journal(manuel_client, requests[0].id)

    def test_setup(self, openreview_client, request_page, selenium, helpers, journal_request):

        ## Support Role
        helpers.create_user('manuel@mail.com', 'Manuel', 'Puig')

        ## Editors in Chief
        helpers.create_user('emily@mail.com', 'Emily', 'Dickinson')

        request_form = openreview_client.post_note_edit(invitation= 'openreview.net/Support/-/Journal_Request',
            signatures = ['openreview.net/Support'],
            note = Note(
                signatures = ['openreview.net/Support'],
                content = {
                    'official_venue_name': {'value': 'CARP Journal'},
                    'abbreviated_venue_name' : {'value': 'CARP'},
                    'venue_id': {'value': 'CARP'},
                    'contact_info': {'value': 'carp@venue.org'},
                    'secret_key': {'value': '4567'},
                    'support_role': {'value': 'manuel@mail.com' },
                    'editors': {'value': ['~Emily_Dickinson1'] },
                    'website': {'value': 'testjournal.org' }
                }
            ))

        helpers.await_queue_edit(openreview_client, request_form['id'])

        JournalRequest.get_journal(openreview_client, request_form['note']['id'], setup=True)

        ## Action Editors
        helpers.create_user('ana@prada.com', 'Ana', 'Prada')
        helpers.create_user('paul@mc.com', 'Paul', 'McCartney')
        helpers.create_user('john@lennon.com', 'John', 'Lennon')
        helpers.create_user('janis@joplin.com', 'Janis', 'Joplin')
        helpers.create_user('diego@armando.com', 'Diego', 'Armando')
        helpers.create_user('ken@beck.com', 'Ken', 'Beck')

        ## Authors
        helpers.create_user('sigur@ros.com', 'Sigur', 'Ros')
        helpers.create_user('john@travolta.com', 'John', 'Travolta')

        openreview_client.add_members_to_group('CARP/Action_Editors', ['~Ana_Prada1', '~Paul_McCartney1', '~John_Lennon1', '~Janis_Joplin1', '~Diego_Armando1', '~Ken_Beck1'])


    def test_submission(self, journal, openreview_client, test_client, helpers):

        venue_id = journal.venue_id
        test_client = OpenReviewClient(username='test@mail.com', password='1234')
        ana_client = OpenReviewClient(username='ana@prada.com', password='1234')
        ken_client = OpenReviewClient(username='ken@beck.com', password='1234')

        ## Set a max quota
        ana_client.post_edge(openreview.Edge(invitation='CARP/Action_Editors/-/Custom_Max_Papers',
            readers=[venue_id, '~Ana_Prada1'],
            writers=[venue_id, '~Ana_Prada1'],
            signatures=['~Ana_Prada1'],
            head='CARP/Action_Editors',
            tail='~Ana_Prada1',
            weight=3
        ))

        ## Set unavailable
        ken_client.post_edge(openreview.Edge(invitation='CARP/Action_Editors/-/Assignment_Availability',
            readers=[venue_id, '~Ken_Beck1'],
            writers=[venue_id, '~Ken_Beck1'],
            signatures=['~Ken_Beck1'],
            head='CARP/Action_Editors',
            tail='~Ken_Beck1',
            label='Unavailable'
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

        helpers.await_queue_edit(openreview_client, invitation='CARP/-/Submission')
       
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
        journal.setup_ae_matching(label='1234')

        assigning_submissions = openreview_client.get_notes(content={ 'venueid': 'CARP/Assigning_AE' })
        assert len(assigning_submissions) == 3

        assert openreview_client.get_edges(invitation='CARP/Action_Editors/-/Local_Custom_Max_Papers',  tail='~Ana_Prada1')[0].weight == 3
        assert openreview_client.get_edges(invitation='CARP/Action_Editors/-/Local_Custom_Max_Papers',  tail='~Paul_McCartney1')[0].weight == 12
        assert openreview_client.get_edges(invitation='CARP/Action_Editors/-/Local_Custom_Max_Papers',  tail='~John_Lennon1')[0].weight == 12
        assert openreview_client.get_edges(invitation='CARP/Action_Editors/-/Local_Custom_Max_Papers',  tail='~Janis_Joplin1')[0].weight == 12
        assert openreview_client.get_edges(invitation='CARP/Action_Editors/-/Local_Custom_Max_Papers',  tail='~Diego_Armando1')[0].weight == 12
        assert not openreview_client.get_edges(invitation='CARP/Action_Editors/-/Local_Custom_Max_Papers', tail='~Ken_Beck1')

        #assert False
        ## Run the matching and get proposed assignments
        edge = openreview_client.post_edge(openreview.api.Edge(invitation='CARP/Action_Editors/-/Proposed_Assignment',
            head=submissions[0].id,
            tail='~Ana_Prada1',
            label='matching-1234',
            weight=1
        ))

        assert edge.readers == ['CARP', '~Ana_Prada1']

        openreview_client.post_edge(openreview.api.Edge(invitation='CARP/Action_Editors/-/Proposed_Assignment',
            head=submissions[1].id,
            tail='~John_Lennon1',
            label='matching-1234',
            weight=1
        )) 

        openreview_client.post_edge(openreview.api.Edge(invitation='CARP/Action_Editors/-/Proposed_Assignment',
            head=submissions[2].id,
            tail='~Paul_McCartney1',
            label='matching-1234',
            weight=1
        )) 

        ## Deploy assignments                
        journal.set_assignments(assignment_title='matching-1234')

        assignments = openreview_client.get_edges(invitation='CARP/Action_Editors/-/Assignment')
        assert len(assignments) == 3

        helpers.await_queue_edit(openreview_client, edit_id=assignments[0].id)
        helpers.await_queue_edit(openreview_client, edit_id=assignments[1].id)
        helpers.await_queue_edit(openreview_client, edit_id=assignments[2].id)

        messages = openreview_client.get_messages(to = 'ana@prada.com', subject = '[CARP] Assignment to new CARP submission Paper title 1')

        assert openreview_client.get_note(submissions[0].id).content['venueid']['value'] == 'CARP/Assigned_AE'
        assert openreview_client.get_note(submissions[1].id).content['venueid']['value'] == 'CARP/Assigned_AE'
        assert openreview_client.get_note(submissions[2].id).content['venueid']['value'] == 'CARP/Assigned_AE'

        assigning_submissions = openreview_client.get_notes(content={ 'venueid': 'CARP/Assigning_AE' })
        assert len(assigning_submissions) == 0

        ### Setup matching again
        journal.setup_ae_matching(label='12345')

        assigning_submissions = openreview_client.get_notes(content={ 'venueid': 'CARP/Assigning_AE' })
        assert len(assigning_submissions) == 0

        assigning_submissions = openreview_client.get_notes(content={ 'venueid': 'CARP/Assigned_AE' })
        assert len(assigning_submissions) == 3

        ## Paper 4
        test_client.post_edge(openreview.api.Edge(invitation='CARP/Action_Editors/-/Recommendation',
            head=submissions[3].id,
            tail='~Janis_Joplin1',
            weight=1
        ))    


        test_client.post_edge(openreview.api.Edge(invitation='CARP/Action_Editors/-/Recommendation',
            head=submissions[3].id,
            tail='~Paul_McCartney1',
            weight=1
        ))    

        test_client.post_edge(openreview.api.Edge(invitation='CARP/Action_Editors/-/Recommendation',
            head=submissions[3].id,
            tail='~John_Lennon1',
            weight=1
        ))

        assert openreview_client.get_edges(invitation='CARP/Action_Editors/-/Local_Custom_Max_Papers',  tail='~Ana_Prada1')[0].weight == 2
        assert openreview_client.get_edges(invitation='CARP/Action_Editors/-/Local_Custom_Max_Papers',  tail='~Paul_McCartney1')[0].weight == 11
        assert openreview_client.get_edges(invitation='CARP/Action_Editors/-/Local_Custom_Max_Papers',  tail='~John_Lennon1')[0].weight == 11
        assert openreview_client.get_edges(invitation='CARP/Action_Editors/-/Local_Custom_Max_Papers',  tail='~Janis_Joplin1')[0].weight == 12
        assert openreview_client.get_edges(invitation='CARP/Action_Editors/-/Local_Custom_Max_Papers',  tail='~Diego_Armando1')[0].weight == 12
        assert not openreview_client.get_edges(invitation='CARP/Action_Editors/-/Local_Custom_Max_Papers', tail='~Ken_Beck1')

        ### Setup matching again
        journal.setup_ae_matching(label='123456')

        assigning_submissions = openreview_client.get_notes(content={ 'venueid': 'CARP/Assigning_AE' })
        assert len(assigning_submissions) == 1

        assigning_submissions = openreview_client.get_notes(content={ 'venueid': 'CARP/Assigned_AE' })
        assert len(assigning_submissions) == 3               

        assert openreview_client.get_edges(invitation='CARP/Action_Editors/-/Local_Custom_Max_Papers',  tail='~Ana_Prada1')[0].weight == 2
        assert openreview_client.get_edges(invitation='CARP/Action_Editors/-/Local_Custom_Max_Papers',  tail='~Paul_McCartney1')[0].weight == 11
        assert openreview_client.get_edges(invitation='CARP/Action_Editors/-/Local_Custom_Max_Papers',  tail='~John_Lennon1')[0].weight == 11
        assert openreview_client.get_edges(invitation='CARP/Action_Editors/-/Local_Custom_Max_Papers',  tail='~Janis_Joplin1')[0].weight == 12
        assert openreview_client.get_edges(invitation='CARP/Action_Editors/-/Local_Custom_Max_Papers',  tail='~Diego_Armando1')[0].weight == 12
        assert not openreview_client.get_edges(invitation='CARP/Action_Editors/-/Local_Custom_Max_Papers', tail='~Ken_Beck1')

        edge = openreview_client.post_edge(openreview.api.Edge(invitation='CARP/Action_Editors/-/Proposed_Assignment',
            head=submissions[3].id,
            tail='~Ana_Prada1',
            label='matching-123456',
            weight=1
        ))

        ## Deploy assignments                
        journal.set_assignments(assignment_title='matching-123456')

        assignments = openreview_client.get_edges(invitation='CARP/Action_Editors/-/Assignment')
        assert len(assignments) == 4

        helpers.await_queue_edit(openreview_client, edit_id=assignments[-1].id)

        ### Setup matching again
        journal.setup_ae_matching(label='1234567')

        assigning_submissions = openreview_client.get_notes(content={ 'venueid': 'CARP/Assigning_AE' })
        assert len(assigning_submissions) == 0

        assigning_submissions = openreview_client.get_notes(content={ 'venueid': 'CARP/Assigned_AE' })
        assert len(assigning_submissions) == 4               

        assert not openreview_client.get_edges(invitation='CARP/Action_Editors/-/Local_Custom_Max_Papers',  tail='~Ana_Prada1')
        assert openreview_client.get_edges(invitation='CARP/Action_Editors/-/Local_Custom_Max_Papers',  tail='~Paul_McCartney1')[0].weight == 11
        assert openreview_client.get_edges(invitation='CARP/Action_Editors/-/Local_Custom_Max_Papers',  tail='~John_Lennon1')[0].weight == 11
        assert openreview_client.get_edges(invitation='CARP/Action_Editors/-/Local_Custom_Max_Papers',  tail='~Janis_Joplin1')[0].weight == 12
        assert openreview_client.get_edges(invitation='CARP/Action_Editors/-/Local_Custom_Max_Papers',  tail='~Diego_Armando1')[0].weight == 12
        assert not openreview_client.get_edges(invitation='CARP/Action_Editors/-/Local_Custom_Max_Papers', tail='~Ken_Beck1')                                                                       