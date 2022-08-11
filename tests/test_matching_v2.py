from __future__ import absolute_import, division, print_function, unicode_literals
import openreview
import pytest
import requests
import datetime
import time
import os
import re
import csv
import io
import random
from openreview.api import OpenReviewClient
from openreview.venue import Venue
from openreview.api import Note
from openreview.api import Edge
from openreview.api import Group


class TestMatching():

    @pytest.fixture(scope="class")
    def pc_client(self):
        return OpenReviewClient(username='pc1_venue@mail.com', password='1234')

    @pytest.fixture(scope="class")
    def venue(self, openreview_client, helpers):
        pc_client = helpers.create_user('pc1_venue@mail.com', 'PCFirstName', 'UAI')
        venue_id = 'VenueV2.cc'
        venue = Venue(openreview_client, venue_id)
        venue.short_name = 'VV2 2022'
        venue.use_area_chairs = True
        venue.area_chairs_name = 'Senior_Program_Committee'
        venue.area_chair_roles = ['Senior_Program_Committee']
        venue.reviewers_name = 'Program_Committee'
        venue.reviewer_roles = ['Program_Committee']
        venue.setup(program_chair_ids=['pc1_venue@mail.com', 'pc3_venue@mail.com'])

        now = datetime.datetime.utcnow()
        venue.set_submission_stage(openreview.builder.SubmissionStage(
            due_date = now + datetime.timedelta(minutes = 40),
            double_blind=True, 
            readers=[openreview.SubmissionStage.Readers.SENIOR_AREA_CHAIRS, openreview.SubmissionStage.Readers.AREA_CHAIRS, openreview.SubmissionStage.Readers.REVIEWERS]))

        assert openreview_client.get_invitation('VenueV2.cc/-/Submission')

        message = 'Dear {{fullname}},\n\nYou have been nominated by the program chair committee of VV2 2022 to serve as {{invitee_role}}.\n\nTo respond to the invitation, please click on the following link:\n\n{{invitation_url}}\n\nCheers!\n\nProgram Chairs'
        venue.recruit_reviewers(title='[VV2 2022] Invitation to serve as Reviewer',
            message=message,
            invitees = ['r1_venue@mit.edu'],
            reviewers_name = 'Program_Committee',
            contact_info='testvenue@contact.com',
            reduced_load_on_decline = ['1','2','3'])

        venue.recruit_reviewers(title='[VV2 2022] Invitation to serve as Action Editor',
            message=message,
            invitees = ['r1_venue@mit.edu'],
            reviewers_name = 'Senior_Program_Committee',
            contact_info='testvenue@contact.com',
            allow_overlap_official_committee = True)

        bid_stages = [
            openreview.BidStage(due_date=now + datetime.timedelta(minutes = 30), committee_id=venue.get_reviewers_id()),
            openreview.BidStage(due_date=now + datetime.timedelta(minutes = 30), committee_id=venue.get_area_chairs_id())
        ]
        venue.bid_stages = bid_stages
        venue.create_bid_stages()

        assert openreview_client.get_invitation(venue.id + '/Program_Committee/-/Bid')
        assert openreview_client.get_invitation(venue.id + '/Senior_Program_Committee/-/Bid')

        return venue

    def test_setup_matching(self, venue, openreview_client, pc_client, helpers):

        ## setup matching with no reviewers
        with pytest.raises(openreview.OpenReviewException, match=r'The match group is empty'):
            venue.setup_committee_matching(committee_id=venue.get_reviewers_id(), compute_conflicts=True)

        ## setup matching with no area chairs
        with pytest.raises(openreview.OpenReviewException, match=r'The match group is empty'):
            venue.setup_committee_matching(committee_id=venue.get_area_chairs_id(), compute_conflicts=True)

        ## Set committee
        reviewer_group = openreview_client.get_group(venue.id + '/Program_Committee')
        openreview_client.add_members_to_group(reviewer_group, ['r1_venue@mit.edu', 'r2_venue@google.com', 'r3_venue@fb.com'])
        ac_group = openreview_client.get_group(venue.id + '/Senior_Program_Committee')
        openreview_client.add_members_to_group(ac_group, ['ac1_venue@cmu.edu', 'ac2_venue@umass.edu'])
        helpers.create_user('ac1_venue@cmu.edu', 'AreaChair', 'Venue')
        ac1_client = OpenReviewClient(username='ac1_venue@cmu.edu', password='1234')
        helpers.create_user('r1_venue@mit.edu', 'Reviewer', 'Venue')
        r1_client = OpenReviewClient(username='r1_venue@mit.edu', password='1234')

        helpers.create_user('celeste@mailten.com', 'Celeste', 'Martinez')
        helpers.create_user('a1_venue@cmu.edu', 'Author', 'A')
        helpers.create_user('a2_venue@mit.edu', 'Author', 'B')
        helpers.create_user('a3_venue@umass.edu', 'Author', 'C')
        helpers.create_user('pc3_venue@mail.com', 'PC', 'Author')
        author_client = OpenReviewClient(username='celeste@mailten.com', password='1234')

        ## setup matching with no submissions
        with pytest.raises(openreview.OpenReviewException, match=r'Submissions not found'):
            venue.setup_committee_matching(committee_id=venue.get_reviewers_id(), compute_conflicts=True)

        ## Paper 1
        note_1 = author_client.post_note_edit(
            invitation=f'{venue.id}/-/Submission',
            signatures= ['~Celeste_Martinez1'],
            note=Note(
                content={
                    'title': { 'value': 'Paper title 1' },
                    'abstract': { 'value': 'This is an abstract' },
                    'authors': { 'value': ['Celeste Martinez', 'Author A']},
                    'authorids': { 'value': ['~Celeste_Martinez1', '~Author_A1']},
                    'pdf': {'value': '/pdf/' + 'p' * 40 +'.pdf' },
                    'submission_length': {'value': 'Regular submission (no more than 12 pages of main content)' }
                }
            ))

        helpers.await_queue_edit(openreview_client, edit_id=note_1['id'])

        ## Paper 2
        note_2 = author_client.post_note_edit(
            invitation=f'{venue.id}/-/Submission',
            signatures= ['~Celeste_Martinez1'],
            note=Note(
                content={
                    'title': { 'value': 'Paper title 2' },
                    'abstract': { 'value': 'This is an abstract' },
                    'authors': { 'value': ['Celeste Martinez', 'Author B']},
                    'authorids': { 'value': ['~Celeste_Martinez1', '~Author_B1']},
                    'pdf': {'value': '/pdf/' + 'p' * 40 +'.pdf' },
                    'submission_length': {'value': 'Regular submission (no more than 12 pages of main content)' }
                }
            ))

        helpers.await_queue_edit(openreview_client, edit_id=note_2['id'])

        ## Paper 3
        note_3 = author_client.post_note_edit(
            invitation=f'{venue.id}/-/Submission',
            signatures= ['~Celeste_Martinez1'],
            note=Note(
                content={
                    'title': { 'value': 'Paper title 3' },
                    'abstract': { 'value': 'This is an abstract' },
                    'authors': { 'value': ['Celeste Martinez', 'Author C', 'PC author']},
                    'authorids': { 'value': ['~Celeste_Martinez1', '~Author_C1', '~PC_Author1']},
                    'pdf': {'value': '/pdf/' + 'p' * 40 +'.pdf' },
                    'submission_length': {'value': 'Regular submission (no more than 12 pages of main content)' }
                }
            ))

        helpers.await_queue_edit(openreview_client, edit_id=note_3['id'])

        venue.setup_post_submission_stage()
        # Set up reviewer matching
        venue.setup_committee_matching(committee_id=venue.get_area_chairs_id())
        venue.setup_committee_matching(committee_id=venue.get_reviewers_id(), compute_conflicts=True)

        #check assignment process is set when invitation is created
        assignment_inv = openreview_client.get_invitation(venue.get_paper_assignment_id(committee_id=venue.get_reviewers_id(), deployed=True))
        assert assignment_inv
    #     assert assignment_inv.process
    #     assert 'def process_update(client, edge, invitation, existing_edge):' in assignment_inv.process

        notes = venue.get_submissions(sort='number:asc')

        ac1_client.post_edge(Edge(invitation = venue.get_bid_id(venue.get_area_chairs_id()),
            readers = [venue.id, '~AreaChair_Venue1'],
            writers = [venue.id, '~AreaChair_Venue1'],
            signatures = ['~AreaChair_Venue1'],
            head = notes[0].id,
            tail = '~AreaChair_Venue1',
            label = 'High'
        ))
        ac1_client.post_edge(Edge(invitation = venue.get_bid_id(venue.get_area_chairs_id()),
            readers = [venue.id, '~AreaChair_Venue1'],
            writers = [venue.id, '~AreaChair_Venue1'],
            signatures = ['~AreaChair_Venue1'],
            head = notes[1].id,
            tail = '~AreaChair_Venue1',
            label = 'Low'
        ))
        ac1_client.post_edge(Edge(invitation = venue.get_bid_id(venue.get_area_chairs_id()),
            readers = [venue.id, '~AreaChair_Venue1'],
            writers = [venue.id, '~AreaChair_Venue1'],
            signatures = ['~AreaChair_Venue1'],
            head = notes[2].id,
            tail = '~AreaChair_Venue1',
            label = 'Very Low'
        ))

        r1_client.post_edge(Edge(invitation = venue.get_bid_id(venue.get_reviewers_id()),
            readers = [venue.id, 'VenueV2.cc/Senior_Program_Committee', '~Reviewer_Venue1'],
            writers = [venue.id, '~Reviewer_Venue1'],
            signatures = ['~Reviewer_Venue1'],
            head = notes[0].id,
            tail = '~Reviewer_Venue1',
            label = 'Neutral'
        ))
        r1_client.post_edge(Edge(invitation = venue.get_bid_id(venue.get_reviewers_id()),
            readers = [venue.id, 'VenueV2.cc/Senior_Program_Committee', '~Reviewer_Venue1'],
            writers = [venue.id, '~Reviewer_Venue1'],
            signatures = ['~Reviewer_Venue1'],
            head = notes[1].id,
            tail = '~Reviewer_Venue1',
            label = 'Very High'
        ))
        r1_client.post_edge(Edge(invitation = venue.get_bid_id(venue.get_reviewers_id()),
            readers = [venue.id, 'VenueV2.cc/Senior_Program_Committee', '~Reviewer_Venue1'],
            writers = [venue.id, '~Reviewer_Venue1'],
            signatures = ['~Reviewer_Venue1'],
            head = notes[2].id,
            tail = '~Reviewer_Venue1',
            label = 'Low'
        ))

        invitation = pc_client.get_invitation(id=f'{venue.id}/Program_Committee/-/Assignment_Configuration')
        assert invitation
        assert 'scores_specification' in invitation.edit['note']['content']
        assert f'{venue.id}/Program_Committee/-/Bid' in invitation.edit['note']['content']['scores_specification']['value']['param']['default']
        assert pc_client.get_invitation(id=f'{venue.id}/Program_Committee/-/Custom_Max_Papers')
        assert pc_client.get_invitation(id=f'{venue.id}/Program_Committee/-/Conflict')
        assert pc_client.get_invitation(id=f'{venue.id}/Program_Committee/-/Aggregate_Score')
        assert pc_client.get_invitation(id=f'{venue.id}/Program_Committee/-/Assignment')
        assert pc_client.get_invitation(id=f'{venue.id}/Program_Committee/-/Proposed_Assignment')

        # Set up AC matching
        venue.setup_committee_matching(committee_id=venue.get_area_chairs_id(), compute_conflicts=True)

        invitation = pc_client.get_invitation(id=f'{venue.id}/Senior_Program_Committee/-/Assignment_Configuration')
        assert invitation
        assert 'scores_specification' in invitation.edit['note']['content']
        assert f'{venue.id}/Senior_Program_Committee/-/Bid' in invitation.edit['note']['content']['scores_specification']['value']['param']['default']
        assert pc_client.get_invitation(id=f'{venue.id}/Senior_Program_Committee/-/Custom_Max_Papers')
        assert pc_client.get_invitation(id=f'{venue.id}/Senior_Program_Committee/-/Conflict')
        assert pc_client.get_invitation(id=f'{venue.id}/Senior_Program_Committee/-/Aggregate_Score')
        assert pc_client.get_invitation(id=f'{venue.id}/Senior_Program_Committee/-/Assignment')

        bids = pc_client.get_edges(invitation = venue.get_bid_id(venue.get_area_chairs_id()))
        assert bids
        assert 3 == len(bids)

        bids = pc_client.get_edges(invitation = venue.get_bid_id(venue.get_reviewers_id()))
        assert bids
        assert 3 == len(bids)

        reviewer_custom_loads = pc_client.get_edges(
            invitation=f'{venue.id}/Program_Committee/-/Custom_Max_Papers')
        assert not reviewer_custom_loads

        ac_custom_loads = pc_client.get_edges(
            invitation=f'{venue.id}/Senior_Program_Committee/-/Custom_Max_Papers')
        assert not ac_custom_loads

        reviewer_conflicts = pc_client.get_edges(
            invitation=f'{venue.id}/Program_Committee/-/Conflict')
        assert 1 == len(reviewer_conflicts)

        ac_conflicts = pc_client.get_edges(
            invitation=f'{venue.id}/Senior_Program_Committee/-/Conflict')
        assert 2 == len(ac_conflicts)

        ac1_conflicts = pc_client.get_edges(
            invitation=f'{venue.id}/Senior_Program_Committee/-/Conflict',
            tail='~AreaChair_Venue1')
        assert ac1_conflicts
        assert len(ac1_conflicts)
        assert ac1_conflicts[0].label == 'Conflict'

        r1_conflicts = pc_client.get_edges(
            invitation=f'{venue.id}/Program_Committee/-/Conflict',
            tail='~Reviewer_Venue1')
        assert r1_conflicts
        assert len(r1_conflicts)
        assert r1_conflicts[0].label == 'Conflict'

        ac2_conflicts = pc_client.get_edges(
            invitation=f'{venue.id}/Senior_Program_Committee/-/Conflict',
            tail='ac2_venue@umass.edu')
        assert ac2_conflicts
        assert len(ac2_conflicts)
        assert ac2_conflicts[0].label == 'Conflict'


    # def test_setup_matching_with_recommendations(self, conference, pc_client, test_client, helpers):

    #     notes = list(venue.get_submissions(sort='tmdate'))

    #     ## Open reviewer recommendations
    #     now = datetime.datetime.utcnow()
    #     venue.open_recommendations(assignment_title='', due_date = now + datetime.timedelta(minutes = 40))

    #     ## Recommend reviewers
    #     ac1_client = helpers.get_user('ac1_venue@cmu.edu')
    #     ac1_client.post_edge(Edge(invitation = venue.get_recommendation_id(),
    #         readers = [f'{venue.id}', '~AreaChair_One1'],
    #         signatures = ['~AreaChair_One1'],
    #         writers = ['~AreaChair_One1'],
    #         head = notes[0].id,
    #         tail = '~Reviewer_Venue1',
    #         weight = 1
    #     ))
    #     ac1_client.post_edge(Edge(invitation = venue.get_recommendation_id(),
    #         readers = [f'{venue.id}', '~AreaChair_One1'],
    #         signatures = ['~AreaChair_One1'],
    #         writers = ['~AreaChair_One1'],
    #         head = notes[1].id,
    #         tail = 'r2_venue@google.com',
    #         weight = 2
    #     ))
    #     ac1_client.post_edge(Edge(invitation = venue.get_recommendation_id(),
    #         readers = [f'{venue.id}', '~AreaChair_One1'],
    #         signatures = ['~AreaChair_One1'],
    #         writers = ['~AreaChair_One1'],
    #         head = notes[1].id,
    #         tail = 'r3_venue@fb.com',
    #         weight = 3
    #     ))

    #    # Set up reviewer matching
    #     venue.setup_matching(tpms_score_file=os.path.join(os.path.dirname(__file__), 'data/reviewer_tpms_scores.csv'), build_conflicts=True)

    #     print(venue.get_reviewers_id())

    #     invitation = pc_client.get_invitation(id=f'{venue.id}/Program_Committee/-/Assignment_Configuration')
    #     assert invitation
    #     assert 'scores_specification' in invitation.reply['content']
    #     assert f'{venue.id}/Program_Committee/-/Bid' in invitation.reply['content']['scores_specification']['default']
    #     assert f'{venue.id}/Program_Committee/-/TPMS_Score' in invitation.reply['content']['scores_specification']['default']
    #     assert f'{venue.id}/Program_Committee/-/Subject_Areas_Score' in invitation.reply['content']['scores_specification']['default']
    #     assert pc_client.get_invitation(id=f'{venue.id}/Program_Committee/-/Custom_Max_Papers')
    #     assert pc_client.get_invitation(id=f'{venue.id}/Program_Committee/-/Conflict')

    #     # Set up ac matching
    #     venue.setup_matching(
    #         committee_id=venue.get_area_chairs_id(),
    #         tpms_score_file=os.path.join(os.path.dirname(__file__), 'data/ac_tpms_scores.csv'),
    #         build_conflicts=True)

    #     invitation = pc_client.get_invitation(id=f'{venue.id}/Senior_Program_Committee/-/Assignment_Configuration')
    #     assert invitation
    #     assert 'scores_specification' in invitation.reply['content']
    #     assert f'{venue.id}/Senior_Program_Committee/-/Bid' in invitation.reply['content']['scores_specification']['default']
    #     assert f'{venue.id}/Senior_Program_Committee/-/TPMS_Score' in invitation.reply['content']['scores_specification']['default']
    #     assert f'{venue.id}/Senior_Program_Committee/-/Subject_Areas_Score' in invitation.reply['content']['scores_specification']['default']
    #     assert f'{venue.id}/Program_Committee/-/Recommendation' in invitation.reply['content']['scores_specification']['default']

    #     assert pc_client.get_invitation(id=f'{venue.id}/Senior_Program_Committee/-/Custom_Max_Papers')
    #     assert pc_client.get_invitation(id=f'{venue.id}/Senior_Program_Committee/-/Conflict')

    #     bids = pc_client.get_edges(invitation = venue.get_bid_id(venue.get_area_chairs_id()))
    #     assert bids
    #     assert 3 == len(bids)

    #     bids = pc_client.get_edges(invitation = venue.get_bid_id(venue.get_reviewers_id()))
    #     assert bids
    #     assert 3 == len(bids)

    #     recommendations = pc_client.get_edges(invitation = venue.get_recommendation_id())
    #     assert recommendations
    #     assert 3 == len(recommendations)

    #     reviewer_custom_loads = pc_client.get_edges(
    #         invitation=f'{venue.id}/Program_Committee/-/Custom_Max_Papers')
    #     assert not reviewer_custom_loads

    #     ac_custom_loads = pc_client.get_edges(
    #         invitation=f'{venue.id}/Senior_Program_Committee/-/Custom_Max_Papers')
    #     assert not ac_custom_loads

    #     reviewer_conflicts = pc_client.get_edges(
    #         invitation=f'{venue.id}/Program_Committee/-/Conflict')
    #     assert 1 == len(reviewer_conflicts)

    #     ac_conflicts = pc_client.get_edges(
    #         invitation=f'{venue.id}/Senior_Program_Committee/-/Conflict')
    #     assert 2 == len(ac_conflicts)

    #     ac1_conflicts = pc_client.get_edges(
    #         invitation=f'{venue.id}/Senior_Program_Committee/-/Conflict', tail='~AreaChair_One1')
    #     assert ac1_conflicts
    #     assert len(ac1_conflicts)
    #     assert ac1_conflicts[0].label == 'Conflict'

    #     r1_conflicts = pc_client.get_edges(
    #         invitation=f'{venue.id}/Program_Committee/-/Conflict', tail='~Reviewer_Venue1')
    #     assert r1_conflicts
    #     assert len(r1_conflicts)
    #     assert r1_conflicts[0].label == 'Conflict'

    #     ac2_conflicts = pc_client.get_edges(
    #         invitation=f'{venue.id}/Senior_Program_Committee/-/Conflict', tail='ac2_venue@umass.edu')
    #     assert ac2_conflicts
    #     assert len(ac2_conflicts)
    #     assert ac2_conflicts[0].label == 'Conflict'

    #     submissions = venue.get_submissions(sort='tmdate')
    #     assert submissions
    #     assert 3 == len(submissions)

    #     reviewer_tpms_scores = pc_client.get_edges(
    #         invitation=f'{venue.id}/Program_Committee/-/TPMS_Score')
    #     assert 9 == len(reviewer_tpms_scores)

    #     ac_tpms_scores = pc_client.get_edges(
    #         invitation=f'{venue.id}/Senior_Program_Committee/-/TPMS_Score')
    #     assert 6 == len(ac_tpms_scores)

    #     r3_s0_tpms_scores = pc_client.get_edges(
    #         invitation=f'{venue.id}/Program_Committee/-/TPMS_Score',
    #         tail='r3_venue@fb.com',
    #         head=submissions[0].id)
    #     assert r3_s0_tpms_scores
    #     assert 1 == len(r3_s0_tpms_scores)
    #     assert r3_s0_tpms_scores[0].weight == 0.21

    #     r3_s1_tpms_scores = pc_client.get_edges(
    #         invitation=f'{venue.id}/Program_Committee/-/TPMS_Score',
    #         tail='r3_venue@fb.com',
    #         head=submissions[1].id)
    #     assert r3_s1_tpms_scores
    #     assert 1 == len(r3_s1_tpms_scores)
    #     assert r3_s1_tpms_scores[0].weight == 0.31

    #     r3_s2_tpms_scores = pc_client.get_edges(
    #         invitation=f'{venue.id}/Program_Committee/-/TPMS_Score',
    #         tail='r3_venue@fb.com',
    #         head=submissions[2].id)
    #     assert r3_s2_tpms_scores
    #     assert 1 == len(r3_s2_tpms_scores)
    #     assert r3_s2_tpms_scores[0].weight == 0.51


    def test_set_assigments(self, venue, openreview_client, pc_client, test_client, helpers):

        venue.client = pc_client

        notes = venue.get_submissions(sort='number:asc')

        edges = pc_client.get_edges(
            invitation=f'{venue.id}/Program_Committee/-/Proposed_Assignment',
            label='rev-matching'
        )
        assert 0 == len(edges)

        #Reviewer assignments
        pc_client.post_edge(Edge(invitation = venue.get_paper_assignment_id(venue.get_reviewers_id()),
            readers = [venue.id, f'{venue.id}/Paper{notes[0].number}/Senior_Program_Committee', '~Reviewer_Venue1'],
            nonreaders = [f'{venue.id}/Paper{notes[0].number}/Authors'],
            writers = [venue.id, f'{venue.id}/Paper{notes[0].number}/Senior_Program_Committee'],
            signatures = [venue.id],
            head = notes[0].id,
            tail = '~Reviewer_Venue1',
            label = 'rev-matching',
            weight = 0.98
        ))

        pc_client.post_edge(Edge(invitation = venue.get_paper_assignment_id(venue.get_reviewers_id()),
            readers = [venue.id, f'{venue.id}/Paper{notes[0].number}/Senior_Program_Committee', 'r2_venue@google.com'],
            nonreaders = [f'{venue.id}/Paper{notes[0].number}/Authors'],
            writers = [venue.id, f'{venue.id}/Paper{notes[0].number}/Senior_Program_Committee'],
            signatures = [venue.id],
            head = notes[0].id,
            tail = 'r2_venue@google.com',
            label = 'rev-matching',
            weight = 0.87
        ))

        pc_client.post_edge(Edge(invitation = venue.get_paper_assignment_id(venue.get_reviewers_id()),
            readers = [venue.id, f'{venue.id}/Paper{notes[1].number}/Senior_Program_Committee', 'r2_venue@google.com'],
            nonreaders = [f'{venue.id}/Paper{notes[1].number}/Authors'],
            writers = [venue.id, f'{venue.id}/Paper{notes[1].number}/Senior_Program_Committee'],
            signatures = [venue.id],
            head = notes[1].id,
            tail = 'r2_venue@google.com',
            label = 'rev-matching',
            weight = 0.87
        ))

        pc_client.post_edge(Edge(invitation = venue.get_paper_assignment_id(venue.get_reviewers_id()),
            readers = [venue.id, f'{venue.id}/Paper{notes[1].number}/Senior_Program_Committee', 'r3_venue@fb.com'],
            nonreaders = [f'{venue.id}/Paper{notes[1].number}/Authors'],
            writers = [venue.id, f'{venue.id}/Paper{notes[1].number}/Senior_Program_Committee'],
            signatures = [venue.id],
            head = notes[1].id,
            tail = 'r3_venue@fb.com',
            label = 'rev-matching',
            weight = 0.94
        ))

        pc_client.post_edge(Edge(invitation = venue.get_paper_assignment_id(venue.get_reviewers_id()),
            readers = [venue.id, f'{venue.id}/Paper{notes[2].number}/Senior_Program_Committee', 'r3_venue@fb.com'],
            nonreaders = [f'{venue.id}/Paper{notes[2].number}/Authors'],
            writers = [venue.id, f'{venue.id}/Paper{notes[2].number}/Senior_Program_Committee'],
            signatures = [venue.id],
            head = notes[2].id,
            tail = 'r3_venue@fb.com',
            label = 'rev-matching',
            weight = 0.94
        ))

        pc_client.post_edge(Edge(invitation = venue.get_paper_assignment_id(venue.get_reviewers_id()),
            readers = [venue.id, f'{venue.id}/Paper{notes[2].number}/Senior_Program_Committee', '~Reviewer_Venue1'],
            nonreaders = [f'{venue.id}/Paper{notes[2].number}/Authors'],
            writers = [venue.id, f'{venue.id}/Paper{notes[2].number}/Senior_Program_Committee'],
            signatures = [venue.id],
            head = notes[2].id,
            tail = '~Reviewer_Venue1',
            label = 'rev-matching',
            weight = 0.98
        ))

        edges = pc_client.get_edges(
            invitation=f'{venue.id}/Program_Committee/-/Proposed_Assignment',
            label='rev-matching'
        )
        assert 6 == len(edges)

        venue.set_assignments(assignment_title='rev-matching', committee_id=f'{venue.id}/Program_Committee')

        revs_paper0 = pc_client.get_group(venue.get_id()+'/Paper{x}/Program_Committee'.format(x=notes[0].number))
        assert 2 == len(revs_paper0.members)
        assert '~Reviewer_Venue1' in revs_paper0.members
        assert 'r2_venue@google.com' in revs_paper0.members
        assert pc_client.get_groups(regex=venue.get_id()+'/Paper{x}/Program_Committee.*'.format(x=notes[0].number), member='~Reviewer_Venue1')
        assert pc_client.get_groups(regex=venue.get_id()+'/Paper{x}/Program_Committee.*'.format(x=notes[0].number), member='r2_venue@google.com')

        revs_paper1 = pc_client.get_group(venue.get_id()+'/Paper{x}/Program_Committee'.format(x=notes[1].number))
        assert 2 == len(revs_paper1.members)
        assert revs_paper1.members[0] == 'r2_venue@google.com'
        assert revs_paper1.members[1] == 'r3_venue@fb.com'
        assert pc_client.get_groups(regex=venue.get_id()+'/Paper{x}/Program_Committee.*'.format(x=notes[1].number), member='r3_venue@fb.com')
        assert pc_client.get_groups(regex=venue.get_id()+'/Paper{x}/Program_Committee.*'.format(x=notes[1].number), member='r2_venue@google.com')

        revs_paper2 = pc_client.get_group(venue.get_id()+'/Paper{x}/Program_Committee'.format(x=notes[2].number))
        assert 2 == len(revs_paper2.members)
        assert 'r3_venue@fb.com' in revs_paper2.members
        assert '~Reviewer_Venue1' in revs_paper2.members
        assert pc_client.get_groups(regex=venue.get_id()+'/Paper{x}/Program_Committee.*'.format(x=notes[2].number), member='~Reviewer_Venue1')
        assert pc_client.get_groups(regex=venue.get_id()+'/Paper{x}/Program_Committee.*'.format(x=notes[2].number), member='r3_venue@fb.com')

        # venue.setup_matching(committee_id=venue.get_reviewers_id(), build_conflicts=True)

        # #check assignment process is still set after deployment and setting up matching again
        # assignment_inv = openreview_client.get_invitation(venue.get_paper_assignment_id(committee_id=venue.get_reviewers_id(), deployed=True))
        # assert assignment_inv
        # assert assignment_inv.process
        # assert 'def process_update(client, edge, invitation, existing_edge):' in assignment_inv.process

    def test_redeploy_assigments(self, venue, openreview_client, pc_client, helpers):

        notes = venue.get_submissions(sort='number:asc')

        #Reviewer assignments
        pc_client.post_edge(Edge(invitation = venue.get_paper_assignment_id(venue.get_reviewers_id()),
            readers = [venue.id, f'{venue.id}/Paper{notes[0].number}/Senior_Program_Committee', 'r3_venue@fb.com'],
            nonreaders = [f'{venue.id}/Paper{notes[0].number}/Authors'],
            writers = [venue.id, f'{venue.id}/Paper{notes[0].number}/Senior_Program_Committee'],
            signatures = [venue.id],
            head = notes[0].id,
            tail = 'r3_venue@fb.com',
            label = 'rev-matching-new',
            weight = 0.98
        ))

        pc_client.post_edge(Edge(invitation = venue.get_paper_assignment_id(venue.get_reviewers_id()),
            readers = [venue.id, f'{venue.id}/Paper{notes[1].number}/Senior_Program_Committee', '~Reviewer_Venue1'],
            nonreaders = [f'{venue.id}/Paper{notes[1].number}/Authors'],
            writers = [venue.id, f'{venue.id}/Paper{notes[1].number}/Senior_Program_Committee'],
            signatures = [venue.id],
            head = notes[1].id,
            tail = '~Reviewer_Venue1',
            label = 'rev-matching-new',
            weight = 0.98
        ))

        pc_client.post_edge(Edge(invitation = venue.get_paper_assignment_id(venue.get_reviewers_id()),
            readers = [venue.id, f'{venue.id}/Paper{notes[2].number}/Senior_Program_Committee', 'r2_venue@google.com'],
            nonreaders = [f'{venue.id}/Paper{notes[2].number}/Authors'],
            writers = [venue.id, f'{venue.id}/Paper{notes[2].number}/Senior_Program_Committee'],
            signatures = [venue.id],
            head = notes[2].id,
            tail = 'r2_venue@google.com',
            label = 'rev-matching-new',
            weight = 0.98
        ))

        edges = pc_client.get_edges(
            invitation=f'{venue.id}/Program_Committee/-/Proposed_Assignment',
            label='rev-matching-new'
        )
        assert 3 == len(edges)

        venue.set_assignments(assignment_title='rev-matching-new', overwrite=True, committee_id=f'{venue.id}/Program_Committee')

        revs_paper0 = pc_client.get_group(venue.get_id()+'/Paper{x}/Program_Committee'.format(x=notes[0].number))
        assert ['r3_venue@fb.com'] == revs_paper0.members
        assert pc_client.get_groups(regex=venue.get_id()+'/Paper{x}/Program_Committee.*'.format(x=notes[0].number), member=['r3_venue@fb.com'])

        revs_paper1 = pc_client.get_group(venue.get_id()+'/Paper{x}/Program_Committee'.format(x=notes[1].number))
        assert ['~Reviewer_Venue1'] == revs_paper1.members
        assert pc_client.get_groups(regex=venue.get_id()+'/Paper{x}/Program_Committee.*'.format(x=notes[1].number), member=['~Reviewer_Venue1'])

        revs_paper2 = pc_client.get_group(venue.get_id()+'/Paper{x}/Program_Committee'.format(x=notes[2].number))
        assert ['r2_venue@google.com'] == revs_paper2.members
        assert pc_client.get_groups(regex=venue.get_id()+'/Paper{x}/Program_Committee.*'.format(x=notes[2].number), member=['r2_venue@google.com'])


        ## Emergency reviewers, append reviewers
        reviewer_group = openreview_client.get_group(venue.id + '/Program_Committee')
        openreview_client.add_members_to_group(reviewer_group, ['r2_venue@mit.edu'])

        pc_client.post_edge(Edge(invitation = venue.get_paper_assignment_id(venue.get_reviewers_id()),
            readers = [venue.id, f'{venue.id}/Paper{notes[0].number}/Senior_Program_Committee', '~Reviewer_Venue1'],
            nonreaders = [f'{venue.id}/Paper{notes[0].number}/Authors'],
            writers = [venue.id, f'{venue.id}/Paper{notes[0].number}/Senior_Program_Committee'],
            signatures = [venue.id],
            head = notes[0].id,
            tail = '~Reviewer_Venue1',
            label = 'rev-matching-emergency',
            weight = 0.98
        ))

        pc_client.post_edge(Edge(invitation = venue.get_paper_assignment_id(venue.get_reviewers_id()),
            readers = [venue.id, f'{venue.id}/Paper{notes[0].number}/Senior_Program_Committee', 'r2_venue@mit.edu'],
            nonreaders = [f'{venue.id}/Paper{notes[0].number}/Authors'],
            writers = [venue.id, f'{venue.id}/Paper{notes[0].number}/Senior_Program_Committee'],
            signatures = [venue.id],
            head = notes[0].id,
            tail = 'r2_venue@mit.edu',
            label = 'rev-matching-emergency',
            weight = 0.98
        ))

        pc_client.post_edge(Edge(invitation = venue.get_paper_assignment_id(venue.get_reviewers_id()),
            readers = [venue.id, f'{venue.id}/Paper{notes[1].number}/Senior_Program_Committee', 'r2_venue@google.com'],
            nonreaders = [f'{venue.id}/Paper{notes[1].number}/Authors'],
            writers = [venue.id, f'{venue.id}/Paper{notes[1].number}/Senior_Program_Committee'],
            signatures = [venue.id],
            head = notes[1].id,
            tail = 'r2_venue@google.com',
            label = 'rev-matching-emergency',
            weight = 0.98
        ))

        venue.set_assignments(assignment_title='rev-matching-emergency', committee_id=f'{venue.id}/Program_Committee')

        revs_paper0 = pc_client.get_group(venue.get_id()+'/Paper{x}/Program_Committee'.format(x=notes[0].number))
        assert ['r3_venue@fb.com', '~Reviewer_Venue1', 'r2_venue@mit.edu'] == revs_paper0.members

        revs_paper1 = pc_client.get_group(venue.get_id()+'/Paper{x}/Program_Committee'.format(x=notes[1].number))
        assert ['~Reviewer_Venue1', 'r2_venue@google.com'] == revs_paper1.members

        revs_paper2 = pc_client.get_group(venue.get_id()+'/Paper{x}/Program_Committee'.format(x=notes[2].number))
        assert ['r2_venue@google.com'] == revs_paper2.members

    #     pc_client.remove_members_from_group(f'{venue.id}/Paper3/AnonReviewer2', ['~Reviewer_Venue1'])
        pc_client.remove_members_from_group(f'{venue.id}/Paper1/Program_Committee', ['~Reviewer_Venue1'])

        pc_client.post_edge(Edge(invitation = venue.get_paper_assignment_id(venue.get_reviewers_id()),
            readers = [venue.id, f'{venue.id}/Paper{notes[0].number}/Senior_Program_Committee', 'r2_venue@google.com'],
            nonreaders = [f'{venue.id}/Paper{notes[0].number}/Authors'],
            writers = [venue.id, f'{venue.id}/Paper{notes[0].number}/Senior_Program_Committee'],
            signatures = [venue.id],
            head = notes[0].id,
            tail = 'r2_venue@google.com',
            label = 'rev-matching-emergency-2',
            weight = 0.98
        ))

        venue.set_assignments(assignment_title='rev-matching-emergency-2', committee_id=f'{venue.id}/Program_Committee')

        revs_paper0 = pc_client.get_group(venue.get_id()+'/Paper{x}/Program_Committee'.format(x=notes[0].number))
        assert ['r3_venue@fb.com', 'r2_venue@mit.edu', 'r2_venue@google.com'] == revs_paper0.members

        revs_paper1 = pc_client.get_group(venue.get_id()+'/Paper{x}/Program_Committee'.format(x=notes[1].number))
        assert ['~Reviewer_Venue1', 'r2_venue@google.com'] == revs_paper1.members

        revs_paper2 = pc_client.get_group(venue.get_id()+'/Paper{x}/Program_Committee'.format(x=notes[2].number))
        assert ['r2_venue@google.com'] == revs_paper2.members

        pc_client.post_edge(Edge(invitation = venue.get_paper_assignment_id(venue.get_reviewers_id()),
            readers = [venue.id, f'{venue.id}/Paper{notes[2].number}/Senior_Program_Committee', 'r2_venue@google.com'],
            nonreaders = [f'{venue.id}/Paper{notes[2].number}/Authors'],
            writers = [venue.id, f'{venue.id}/Paper{notes[2].number}/Senior_Program_Committee'],
            signatures = [venue.id],
            head = notes[2].id,
            tail = 'r2_venue@google.com',
            label = 'rev-matching-emergency-3',
            weight = 0.98
        ))

        venue.set_assignments(assignment_title='rev-matching-emergency-3', overwrite=True, committee_id=f'{venue.id}/Program_Committee')

        revs_paper0 = pc_client.get_group(venue.get_id()+'/Paper{x}/Program_Committee'.format(x=notes[0].number))
        assert [] == revs_paper0.members

        revs_paper1 = pc_client.get_group(venue.get_id()+'/Paper{x}/Program_Committee'.format(x=notes[1].number))
        assert [] == revs_paper1.members

        revs_paper2 = pc_client.get_group(venue.get_id()+'/Paper{x}/Program_Committee'.format(x=notes[2].number))
        assert ['r2_venue@google.com'] == revs_paper2.members

    #     now = datetime.datetime.now()
    #     venue.set_review_stage(openreview.ReviewStage(start_date = now))

    #     invitation = pc_client.get_invitation(id=f'{venue.id}/-/Official_Review')
    #     assert invitation

    #     venue.set_assignments(assignment_title='rev-matching-emergency-3', overwrite=True, committee_id=f'{venue.id}/Program_Committee')

    #     revs_paper0 = pc_client.get_group(venue.get_id()+'/Paper{x}/Program_Committee'.format(x=notes[0].number))
    #     assert [] == revs_paper0.members
    #     with pytest.raises(openreview.OpenReviewException, match=r'Group Not Found'):
    #         assert pc_client.get_group(venue.get_id()+'/Paper{x}/AnonReviewer1'.format(x=notes[0].number))
    #     with pytest.raises(openreview.OpenReviewException, match=r'Group Not Found'):
    #         assert pc_client.get_group(venue.get_id()+'/Paper{x}/AnonReviewer2'.format(x=notes[0].number))
    #     with pytest.raises(openreview.OpenReviewException, match=r'Group Not Found'):
    #         assert pc_client.get_group(venue.get_id()+'/Paper{x}/AnonReviewer3'.format(x=notes[0].number))


    #     revs_paper1 = pc_client.get_group(venue.get_id()+'/Paper{x}/Program_Committee'.format(x=notes[1].number))
    #     assert [] == revs_paper1.members
    #     with pytest.raises(openreview.OpenReviewException, match=r'Group Not Found'):
    #         assert pc_client.get_group(venue.get_id()+'/Paper{x}/AnonReviewer1'.format(x=notes[1].number))
    #     with pytest.raises(openreview.OpenReviewException, match=r'Group Not Found'):
    #         assert pc_client.get_group(venue.get_id()+'/Paper{x}/AnonReviewer2'.format(x=notes[1].number))

    #     revs_paper2 = pc_client.get_group(venue.get_id()+'/Paper{x}/Program_Committee'.format(x=notes[2].number))
    #     assert ['r2_venue@google.com'] == revs_paper2.members
    #     assert pc_client.get_group(venue.get_id()+'/Paper{x}/AnonReviewer1'.format(x=notes[2].number)).members == ['r2_venue@google.com']
    #     with pytest.raises(openreview.OpenReviewException, match=r'Group Not Found'):
    #         assert pc_client.get_group(venue.get_id()+'/Paper{x}/AnonReviewer2'.format(x=notes[2].number))

    #     reviewer_client = helpers.create_user('r2_venue@google.com', 'Reviewer', 'Two')
    #     venue.set_assignment('ac1_venue@cmu.edu', 1, is_area_chair = True)

    #     review_note = reviewer_client.post_note(openreview.Note(
    #         invitation=f'{venue.id}/Paper1/-/Official_Review',
    #         forum=notes[2].id,
    #         replyto=notes[2].id,
    #         content={
    #             'title': 'review',
    #             'review': 'this is a good paper',
    #             'rating': '1: Trivial or wrong',
    #             'confidence': "1: The reviewer's evaluation is an educated guess"
    #         },
    #         readers=[
    #             "auai.org/UAI/2019/Conference/Program_Chairs",
    #             "auai.org/UAI/2019/Conference/Paper1/Senior_Program_Committee",
    #             f'{venue.id}/Paper1/AnonReviewer1'
    #         ],
    #         nonreaders=["auai.org/UAI/2019/Conference/Paper1/Authors"],
    #         writers=[
    #             "auai.org/UAI/2019/Conference",
    #             f'{venue.id}/Paper1/AnonReviewer1'
    #         ],
    #         signatures=[f'{venue.id}/Paper1/AnonReviewer1']
    #     ))

    #     helpers.await_queue()
    #     process_logs = client.get_process_logs(id = review_note.id)
    #     assert len(process_logs) == 1
    #     assert process_logs[0]['status'] == 'ok'

    #     pc_client.post_edge(Edge(invitation = venue.get_paper_assignment_id(venue.get_reviewers_id()),
    #         readers = [venue.id, '~Reviewer_Venue1'],
    #         nonreaders = [f'{venue.id}/Paper{notes[2].number}/Authors'],
    #         writers = [venue.id, f'{venue.id}/Paper{notes[2].number}/Senior_Program_Committee'],
    #         signatures = [venue.id],
    #         head = notes[2].id,
    #         tail = '~Reviewer_Venue1',
    #         label = 'rev-matching-emergency-4',
    #         weight = 0.98
    #     ))

    #     with pytest.raises(openreview.OpenReviewException, match=r'Can not overwrite assignments when there are reviews posted.'):
    #         venue.set_assignments(assignment_title='rev-matching-emergency-4', overwrite=True, committee_id=f'{venue.id}/Program_Committee')

    def test_set_reviewers_assignments_as_author(self, venue, pc_client, helpers):

        pc3_client = OpenReviewClient(username='pc3_venue@mail.com', password='1234')
        # pc3_client.impersonate(venue.id) #ForbiddenError

        venue.client = pc3_client

        notes = venue.get_submissions(sort='number:asc')

        pc3_client.post_edge(Edge(invitation = venue.get_paper_assignment_id(venue.get_reviewers_id()),
            readers = [venue.id, f'{venue.id}/Paper{notes[1].number}/Senior_Program_Committee', '~Reviewer_Venue1'],
            nonreaders = [f'{venue.id}/Paper{notes[1].number}/Authors'],
            writers = [venue.id, f'{venue.id}/Paper{notes[1].number}/Senior_Program_Committee'],
            signatures = [venue.id],
            head = notes[1].id,
            tail = '~Reviewer_Venue1',
            label = 'rev-matching-emergency-6',
            weight = 0.98
        ))

        pc3_client.post_edge(Edge(invitation = venue.get_paper_assignment_id(venue.get_reviewers_id()),
            readers = [venue.id, f'{venue.id}/Paper{notes[0].number}/Senior_Program_Committee', 'r3_venue@fb.com'],
            nonreaders = [f'{venue.id}/Paper{notes[0].number}/Authors'],
            writers = [venue.id, f'{venue.id}/Paper{notes[0].number}/Senior_Program_Committee'],
            signatures = [venue.id],
            head = notes[0].id,
            tail = 'r3_venue@fb.com',
            label = 'rev-matching-emergency-6',
            weight = 0.98
        ))

        venue.set_assignments(assignment_title='rev-matching-emergency-6', committee_id=f'{venue.id}/Program_Committee')

        revs_paper0 = pc_client.get_group(venue.get_id()+'/Paper{x}/Program_Committee'.format(x=notes[0].number))
        assert ['r3_venue@fb.com'] == revs_paper0.members

        revs_paper1 = pc_client.get_group(venue.get_id()+'/Paper{x}/Program_Committee'.format(x=notes[1].number))
        assert ['~Reviewer_Venue1'] == revs_paper1.members

        revs_paper2 = pc_client.get_group(venue.get_id()+'/Paper{x}/Program_Committee'.format(x=notes[2].number))
        assert ['r2_venue@google.com'] == revs_paper2.members


    def test_set_ac_assigments(self, venue, openreview_client, pc_client, test_client, helpers):

        notes = venue.get_submissions(sort='number:asc')
        venue.client = openreview_client

        edges = pc_client.get_edges(
            invitation=f'{venue.id}/Senior_Program_Committee/-/Proposed_Assignment',
            label='ac-matching'
        )
        assert 0 == len(edges)

        #AC assignments
        pc_client.post_edge(Edge(invitation = f'{venue.id}/Senior_Program_Committee/-/Proposed_Assignment',
            readers = [venue.id, 'ac1_venue@cmu.edu'],
            nonreaders = [venue.get_authors_id(number=notes[0].number)],
            writers = [venue.id],
            signatures = [venue.id],
            head = notes[0].id,
            tail = 'ac1_venue@cmu.edu',
            label = 'ac-matching',
            weight = 0.98
        ))

        pc_client.post_edge(Edge(invitation = f'{venue.id}/Senior_Program_Committee/-/Proposed_Assignment',
            readers = [venue.id, 'ac2_venue@umass.edu'],
            nonreaders = [venue.get_authors_id(number=notes[1].number)],
            writers = [venue.id],
            signatures = [venue.id],
            head = notes[1].id,
            tail = 'ac2_venue@umass.edu',
            label = 'ac-matching',
            weight = 0.87
        ))

        pc_client.post_edge(Edge(invitation = f'{venue.id}/Senior_Program_Committee/-/Proposed_Assignment',
            readers = [venue.id, 'ac2_venue@umass.edu'],
            nonreaders = [venue.get_authors_id(number=notes[2].number)],
            writers = [venue.id],
            signatures = [venue.id],
            head = notes[2].id,
            tail = 'ac2_venue@umass.edu',
            label = 'ac-matching',
            weight = 0.87
        ))

        edges = pc_client.get_edges(
            invitation=f'{venue.id}/Senior_Program_Committee/-/Proposed_Assignment',
            label='ac-matching'
        )
        assert 3 == len(edges)

        venue.set_assignments(assignment_title='ac-matching', committee_id=f'{venue.id}/Senior_Program_Committee')

        assert pc_client.get_group(f'{venue.id}/Paper1/Senior_Program_Committee').members == ['ac1_venue@cmu.edu']

        assert pc_client.get_group(f'{venue.id}/Paper2/Senior_Program_Committee').members == ['ac2_venue@umass.edu']

        assert pc_client.get_group(f'{venue.id}/Paper3/Senior_Program_Committee').members == ['ac2_venue@umass.edu']

        pc_client.post_edge(Edge(invitation = f'{venue.id}/Senior_Program_Committee/-/Proposed_Assignment',
            readers = [venue.id, 'ac1_venue@cmu.edu'],
            nonreaders = [venue.get_authors_id(number=notes[1].number)],
            writers = [venue.id],
            signatures = [venue.id],
            head = notes[1].id,
            tail = 'ac1_venue@cmu.edu',
            label = 'ac-matching-2',
            weight = 0.98
        ))

        pc_client.post_edge(Edge(invitation = f'{venue.id}/Senior_Program_Committee/-/Proposed_Assignment',
            readers = [venue.id, 'ac2_venue@umass.edu'],
            nonreaders = [venue.get_authors_id(number=notes[0].number)],
            writers = [venue.id],
            signatures = [venue.id],
            head = notes[0].id,
            tail = 'ac2_venue@umass.edu',
            label = 'ac-matching-2',
            weight = 0.87
        ))

        venue.set_assignments(assignment_title='ac-matching-2', overwrite=True, committee_id=f'{venue.id}/Senior_Program_Committee')

        assert pc_client.get_group(f'{venue.id}/Paper1/Senior_Program_Committee').members == ['ac2_venue@umass.edu']

        assert pc_client.get_group(f'{venue.id}/Paper2/Senior_Program_Committee').members == ['ac1_venue@cmu.edu']

        assert pc_client.get_group(f'{venue.id}/Paper3/Senior_Program_Committee').members == []

    def test_setup_matching_with_mentors(self, venue, pc_client, helpers):

        mentors=pc_client.post_group(Group(id=venue.id + '/Reviewers_Mentors',
            readers = [venue.id],
            writers = [venue.id],
            signatures = [venue.id],
            signatories = [venue.id],
            members = ['ac1_venue@cmu.edu', 'ac2_venue@umass.edu']
        ))

        mentees=pc_client.post_group(Group(id=venue.id + '/Reviewers_Mentees',
            readers = [venue.id],
            writers = [venue.id],
            signatures = [venue.id],
            signatories = [venue.id],
            members = ['~Reviewer_Venue1', 'r2_venue@google.com', 'r3_venue@fb.com']
        ))

        with open(os.path.join(os.path.dirname(__file__), 'data/mentors_affinity_scores.csv'), 'w') as file_handle:
            writer = csv.writer(file_handle)
            for mentor in mentors.members:
                for mentee in mentees.members:
                    writer.writerow([mentee, mentor, round(random.random(), 2)])

        with open(os.path.join(os.path.dirname(__file__), 'data/mentors_affinity_scores.csv'), 'r') as file:
            data = file.read()
        byte_stream = data.encode()
        venue.setup_committee_matching(committee_id=venue.id + '/Reviewers_Mentors',
        compute_affinity_scores=byte_stream,
        alternate_matching_group=venue.id + '/Reviewers_Mentees')

        affinity_scores = pc_client.get_edges(invitation=venue.id + '/Reviewers_Mentors/-/Affinity_Score')
        assert len(affinity_scores) == 6

    # def test_desk_reject_expire_edges(self, conference, client, pc_client, helpers):
    #     note = venue.get_submissions()[0]

    #     desk_reject_note = openreview.Note(
    #         invitation=f'{venue.id}/Paper{note.number}/-/Desk_Reject',
    #         forum=note.forum,
    #         replyto=note.forum,
    #         readers=[venue.id,
    #                  venue.get_authors_id(note.number),
    #                  venue.get_reviewers_id(note.number),
    #                  venue.get_area_chairs_id(note.number),
    #                  venue.get_program_chairs_id()],
    #         writers=[venue.get_id(), venue.get_program_chairs_id()],
    #         signatures=[venue.get_program_chairs_id()],
    #         content={
    #             'desk_reject_comments': 'PC has decided to reject this submission.',
    #             'title': 'Submission Desk Rejected by Program Chairs'
    #         }
    #     )

    #     desk_reject_note = pc_client.post_note(desk_reject_note)

    #     helpers.await_queue()

    #     process_logs = client.get_process_logs(id=desk_reject_note.id)
    #     assert len(process_logs) == 1
    #     assert process_logs[0]['status'] == 'ok'

    #     note_proposed_assignment_edges = client.get_edges(
    #         invitation=venue.get_id() + '/.*/-/Proposed_Assignment',
    #         head=desk_reject_note.forum)
    #     assert not note_proposed_assignment_edges

    #     note_assignment_edges = client.get_edges(
    #         invitation=venue.get_id() + '/.*/-/Assignment',
    #         head=desk_reject_note.forum)
    #     assert not note_assignment_edges
