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
    def pc_client(self, openreview_client, helpers):
        return OpenReviewClient(username='pc1_venue@mail.com', password=helpers.strong_password)

    @pytest.fixture(scope="class")
    def venue(self, openreview_client, helpers):
        helpers.create_user('pc1_venue@mail.com', 'PCFirstName', 'UAI')
        venue_id = 'VenueV2.cc'
        venue = Venue(openreview_client, venue_id, 'openreview.net/Support')
        venue.invitation_builder.update_wait_time = 2000
        venue.invitation_builder.update_date_string = "#{4/mdate} + 2000"        
        venue.automatic_reviewer_assignment = True
        venue.short_name = 'VV2 2022'
        venue.website = 'www.venuev2.com'
        venue.contact = 'pc_venue@mail.com'
        venue.use_area_chairs = True
        venue.area_chairs_name = 'Senior_Program_Committee'
        venue.area_chair_roles = ['Senior_Program_Committee']
        venue.reviewers_name = 'Program_Committee'
        venue.reviewer_roles = ['Program_Committee']
        now = datetime.datetime.now()
        venue.submission_stage = openreview.stages.SubmissionStage(
            due_date = now + datetime.timedelta(minutes = 40),
            double_blind=True, 
            readers=[openreview.stages.SubmissionStage.Readers.SENIOR_AREA_CHAIRS, openreview.stages.SubmissionStage.Readers.AREA_CHAIRS, openreview.stages.SubmissionStage.Readers.REVIEWERS])
        venue.setup(program_chair_ids=['pc1_venue@mail.com', 'pc3_venue@mail.com'])
        venue.create_submission_stage()
        assert openreview_client.get_invitation('VenueV2.cc/-/Submission')

        message = 'Dear {{fullname}},\n\nYou have been nominated by the program chair committee of VV2 2022 to serve as {{invitee_role}}.\n\nTo respond to the invitation, please click on the following link:\n\n{{invitation_url}}\n\nCheers!\n\nProgram Chairs'
        venue.recruit_reviewers(title='[VV2 2022] Invitation to serve as Program Committee',
            message=message.replace('{{invitee_role}}', 'Program Committee'),
            invitees = ['r1_venue@mit.edu'],
            reviewers_name = 'Program_Committee',
            contact_info='testvenue@contact.com',
            reduced_load_on_decline = ['1','2','3'])

        venue.recruit_reviewers(title='[VV2 2022] Invitation to serve as Senior Program Committee',
            message=message.replace('{{invitee_role}}', 'Senior Program Committee'),
            invitees = ['r1_venue@mit.edu'],
            reviewers_name = 'Senior_Program_Committee',
            contact_info='testvenue@contact.com',
            allow_overlap_official_committee = True)

        bid_stages = [
            openreview.stages.BidStage(due_date=now + datetime.timedelta(minutes = 30), committee_id=venue.get_reviewers_id()),
            openreview.stages.BidStage(due_date=now + datetime.timedelta(minutes = 30), committee_id=venue.get_area_chairs_id())
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
        ac1_client = OpenReviewClient(username='ac1_venue@cmu.edu', password=helpers.strong_password)
        helpers.create_user('r1_venue@mit.edu', 'Reviewer', 'Venue')
        r1_client = OpenReviewClient(username='r1_venue@mit.edu', password=helpers.strong_password)

        helpers.create_user('celeste@mailten.com', 'Celeste', 'MartinezG')
        helpers.create_user('a1_venue@cmu.edu', 'Author', 'A')
        helpers.create_user('a2_venue@mit.edu', 'Author', 'B')
        helpers.create_user('a3_venue@umass.edu', 'Author', 'C')
        helpers.create_user('pc3_venue@mail.com', 'PC', 'Author')
        author_client = OpenReviewClient(username='celeste@mailten.com', password=helpers.strong_password)

        ## setup matching with no submissions
        with pytest.raises(openreview.OpenReviewException, match=r'Submissions not found'):
            venue.setup_committee_matching(committee_id=venue.get_reviewers_id(), compute_conflicts=True)

        ## Paper 1
        note_1 = author_client.post_note_edit(
            invitation=f'{venue.id}/-/Submission',
            signatures= ['~Celeste_MartinezG1'],
            note=Note(
                content={
                    'title': { 'value': 'Paper title 1' },
                    'abstract': { 'value': 'This is an abstract' },
                    'authors': { 'value': ['Celeste MartinezG', 'Author A']},
                    'authorids': { 'value': ['~Celeste_MartinezG1', '~Author_A1']},
                    'pdf': {'value': '/pdf/' + 'p' * 40 +'.pdf' },
                    'keywords': {'value': ['aa'] }
                }
            ))

        helpers.await_queue_edit(openreview_client, edit_id=note_1['id'])

        ## Paper 2
        note_2 = author_client.post_note_edit(
            invitation=f'{venue.id}/-/Submission',
            signatures= ['~Celeste_MartinezG1'],
            note=Note(
                content={
                    'title': { 'value': 'Paper title 2' },
                    'abstract': { 'value': 'This is an abstract' },
                    'authors': { 'value': ['Celeste Martinez', 'Author B']},
                    'authorids': { 'value': ['~Celeste_MartinezG1', '~Author_B1']},
                    'pdf': {'value': '/pdf/' + 'p' * 40 +'.pdf' },
                    'keywords': {'value': ['aa'] }
                }
            ))

        helpers.await_queue_edit(openreview_client, edit_id=note_2['id'])

        ## Paper 3
        note_3 = author_client.post_note_edit(
            invitation=f'{venue.id}/-/Submission',
            signatures= ['~Celeste_MartinezG1'],
            note=Note(
                content={
                    'title': { 'value': 'Paper title 3' },
                    'abstract': { 'value': 'This is an abstract' },
                    'authors': { 'value': ['Celeste Martinez', 'Author C', 'PC author']},
                    'authorids': { 'value': ['~Celeste_MartinezG1', '~Author_C1', '~PC_Author1']},
                    'pdf': {'value': '/pdf/' + 'p' * 40 +'.pdf' },
                    'keywords': {'value': ['aa'] }
                }
            ))

        helpers.await_queue_edit(openreview_client, edit_id=note_3['id'])

        venue.submission_stage.start_date = datetime.datetime.now() - datetime.timedelta(seconds=90)
        venue.submission_stage.due_date = datetime.datetime.now()
        venue.submission_stage.exp_date = datetime.datetime.now() + datetime.timedelta(seconds = 90)
        venue.create_submission_stage()
        helpers.await_queue_edit(openreview_client, f'{venue.id}/-/Post_Submission-0-0')
        # Set up reviewer matching
        venue.setup_committee_matching(committee_id=venue.get_area_chairs_id())
        venue.setup_committee_matching(committee_id=venue.get_reviewers_id(), compute_conflicts=True)

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
        invitation = pc_client.get_invitation(id=f'{venue.id}/Program_Committee/-/Custom_Max_Papers')
        assert invitation.responseArchiveDate > openreview.tools.datetime_millis(datetime.datetime.now())
        invitation = pc_client.get_invitation(id=f'{venue.id}/Program_Committee/-/Conflict')
        assert invitation.responseArchiveDate > openreview.tools.datetime_millis(datetime.datetime.now())
        invitation = pc_client.get_invitation(id=f'{venue.id}/Program_Committee/-/Aggregate_Score')
        assert invitation.responseArchiveDate > openreview.tools.datetime_millis(datetime.datetime.now())
        with pytest.raises(openreview.OpenReviewException, match=r'The Invitation VenueV2.cc/Program_Committee/-/Assignment was not found'):
            assert pc_client.get_invitation(id=f'{venue.id}/Program_Committee/-/Assignment')
        invitation = pc_client.get_invitation(id=f'{venue.id}/Program_Committee/-/Proposed_Assignment')
        assert invitation.responseArchiveDate > openreview.tools.datetime_millis(datetime.datetime.now())

        # Set up AC matching
        venue.setup_committee_matching(committee_id=venue.get_area_chairs_id(), compute_conflicts=True)

        invitation = pc_client.get_invitation(id=f'{venue.id}/Senior_Program_Committee/-/Assignment_Configuration')
        assert invitation
        assert 'scores_specification' in invitation.edit['note']['content']
        assert f'{venue.id}/Senior_Program_Committee/-/Bid' in invitation.edit['note']['content']['scores_specification']['value']['param']['default']
        assert pc_client.get_invitation(id=f'{venue.id}/Senior_Program_Committee/-/Custom_Max_Papers')
        assert pc_client.get_invitation(id=f'{venue.id}/Senior_Program_Committee/-/Conflict')
        assert pc_client.get_invitation(id=f'{venue.id}/Senior_Program_Committee/-/Aggregate_Score')
        with pytest.raises(openreview.OpenReviewException, match=r'The Invitation VenueV2.cc/Senior_Program_Committee/-/Assignment was not found'):
            assert pc_client.get_invitation(id=f'{venue.id}/Senior_Program_Committee/-/Assignment')

        bids = pc_client.get_edges_count(invitation = venue.get_bid_id(venue.get_area_chairs_id()))
        assert bids
        assert 3 == bids

        bids = pc_client.get_edges_count(invitation = venue.get_bid_id(venue.get_reviewers_id()))
        assert bids
        assert 3 == bids

        reviewer_custom_loads = pc_client.get_edges_count(
            invitation=f'{venue.id}/Program_Committee/-/Custom_Max_Papers')
        assert not reviewer_custom_loads

        ac_custom_loads = pc_client.get_edges_count(
            invitation=f'{venue.id}/Senior_Program_Committee/-/Custom_Max_Papers')
        assert not ac_custom_loads

        reviewer_conflicts = pc_client.get_edges_count(
            invitation=f'{venue.id}/Program_Committee/-/Conflict')
        assert 1 == reviewer_conflicts

        ac_conflicts = pc_client.get_edges_count(
            invitation=f'{venue.id}/Senior_Program_Committee/-/Conflict')
        assert 2 == ac_conflicts

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


    def test_set_assigments(self, venue, openreview_client, pc_client, test_client, helpers):

        venue.client = pc_client

        notes = venue.get_submissions(sort='number:asc')

        edges = pc_client.get_edges_count(
            invitation=f'{venue.id}/Program_Committee/-/Proposed_Assignment',
            label='rev-matching'
        )
        assert 0 == edges

        #Reviewer assignments
        pc_client.post_edge(Edge(invitation = venue.get_assignment_id(venue.get_reviewers_id()),
            readers = [venue.id, f'{venue.id}/Submission{notes[0].number}/Senior_Program_Committee', '~Reviewer_Venue1'],
            nonreaders = [f'{venue.id}/Submission{notes[0].number}/Authors'],
            writers = [venue.id, f'{venue.id}/Submission{notes[0].number}/Senior_Program_Committee'],
            signatures = [venue.id],
            head = notes[0].id,
            tail = '~Reviewer_Venue1',
            label = 'rev-matching',
            weight = 0.98
        ))

        pc_client.post_edge(Edge(invitation = venue.get_assignment_id(venue.get_reviewers_id()),
            readers = [venue.id, f'{venue.id}/Submission{notes[0].number}/Senior_Program_Committee', 'r2_venue@google.com'],
            nonreaders = [f'{venue.id}/Submission{notes[0].number}/Authors'],
            writers = [venue.id, f'{venue.id}/Submission{notes[0].number}/Senior_Program_Committee'],
            signatures = [venue.id],
            head = notes[0].id,
            tail = 'r2_venue@google.com',
            label = 'rev-matching',
            weight = 0.87
        ))

        pc_client.post_edge(Edge(invitation = venue.get_assignment_id(venue.get_reviewers_id()),
            readers = [venue.id, f'{venue.id}/Submission{notes[1].number}/Senior_Program_Committee', 'r2_venue@google.com'],
            nonreaders = [f'{venue.id}/Submission{notes[1].number}/Authors'],
            writers = [venue.id, f'{venue.id}/Submission{notes[1].number}/Senior_Program_Committee'],
            signatures = [venue.id],
            head = notes[1].id,
            tail = 'r2_venue@google.com',
            label = 'rev-matching',
            weight = 0.87
        ))

        pc_client.post_edge(Edge(invitation = venue.get_assignment_id(venue.get_reviewers_id()),
            readers = [venue.id, f'{venue.id}/Submission{notes[1].number}/Senior_Program_Committee', 'r3_venue@fb.com'],
            nonreaders = [f'{venue.id}/Submission{notes[1].number}/Authors'],
            writers = [venue.id, f'{venue.id}/Submission{notes[1].number}/Senior_Program_Committee'],
            signatures = [venue.id],
            head = notes[1].id,
            tail = 'r3_venue@fb.com',
            label = 'rev-matching',
            weight = 0.94
        ))

        pc_client.post_edge(Edge(invitation = venue.get_assignment_id(venue.get_reviewers_id()),
            readers = [venue.id, f'{venue.id}/Submission{notes[2].number}/Senior_Program_Committee', 'r3_venue@fb.com'],
            nonreaders = [f'{venue.id}/Submission{notes[2].number}/Authors'],
            writers = [venue.id, f'{venue.id}/Submission{notes[2].number}/Senior_Program_Committee'],
            signatures = [venue.id],
            head = notes[2].id,
            tail = 'r3_venue@fb.com',
            label = 'rev-matching',
            weight = 0.94
        ))

        pc_client.post_edge(Edge(invitation = venue.get_assignment_id(venue.get_reviewers_id()),
            readers = [venue.id, f'{venue.id}/Submission{notes[2].number}/Senior_Program_Committee', '~Reviewer_Venue1'],
            nonreaders = [f'{venue.id}/Submission{notes[2].number}/Authors'],
            writers = [venue.id, f'{venue.id}/Submission{notes[2].number}/Senior_Program_Committee'],
            signatures = [venue.id],
            head = notes[2].id,
            tail = '~Reviewer_Venue1',
            label = 'rev-matching',
            weight = 0.98
        ))

        edges = pc_client.get_edges_count(
            invitation=f'{venue.id}/Program_Committee/-/Proposed_Assignment',
            label='rev-matching'
        )
        assert 6 == edges

        venue.create_post_submission_stage()

        venue.set_assignments(assignment_title='rev-matching', committee_id=f'{venue.id}/Program_Committee', enable_reviewer_reassignment=True)

        revs_paper0 = pc_client.get_group(venue.get_id()+'/Submission{x}/Program_Committee'.format(x=notes[0].number))
        assert 2 == len(revs_paper0.members)
        assert '~Reviewer_Venue1' in revs_paper0.members
        assert 'r2_venue@google.com' in revs_paper0.members
        assert pc_client.get_groups(prefix=venue.get_id()+'/Submission{x}/Program_Committee.*'.format(x=notes[0].number), member='~Reviewer_Venue1')
        assert pc_client.get_groups(prefix=venue.get_id()+'/Submission{x}/Program_Committee.*'.format(x=notes[0].number), member='r2_venue@google.com')

        revs_paper1 = pc_client.get_group(venue.get_id()+'/Submission{x}/Program_Committee'.format(x=notes[1].number))
        assert 2 == len(revs_paper1.members)
        assert 'r2_venue@google.com' in revs_paper1.members
        assert 'r3_venue@fb.com' in revs_paper1.members
        assert pc_client.get_groups(prefix=venue.get_id()+'/Submission{x}/Program_Committee.*'.format(x=notes[1].number), member='r3_venue@fb.com')
        assert pc_client.get_groups(prefix=venue.get_id()+'/Submission{x}/Program_Committee.*'.format(x=notes[1].number), member='r2_venue@google.com')

        revs_paper2 = pc_client.get_group(venue.get_id()+'/Submission{x}/Program_Committee'.format(x=notes[2].number))
        assert 2 == len(revs_paper2.members)
        assert 'r3_venue@fb.com' in revs_paper2.members
        assert '~Reviewer_Venue1' in revs_paper2.members
        assert pc_client.get_groups(prefix=venue.get_id()+'/Submission{x}/Program_Committee.*'.format(x=notes[2].number), member='~Reviewer_Venue1')
        assert pc_client.get_groups(prefix=venue.get_id()+'/Submission{x}/Program_Committee.*'.format(x=notes[2].number), member='r3_venue@fb.com')

        #check assignment process is set when invitation is created
        assignment_inv = openreview_client.get_invitation(venue.get_assignment_id(committee_id=venue.get_reviewers_id(), deployed=True))
        assert assignment_inv
        assert assignment_inv.process
        assert 'def process_update(client, edge, invitation, existing_edge):' in assignment_inv.process

        invitation = pc_client.get_invitation(id=f'{venue.id}/Program_Committee/-/Assignment')
        assert invitation.responseArchiveDate > openreview.tools.datetime_millis(datetime.datetime.now())

        invitation = pc_client.get_invitation(id=f'{venue.id}/Program_Committee/-/Proposed_Assignment')
        assert invitation.expdate < openreview.tools.datetime_millis(datetime.datetime.now())

        venue.unset_assignments(assignment_title='rev-matching', committee_id=f'{venue.id}/Program_Committee')

        revs_paper0 = pc_client.get_group(venue.get_id()+'/Submission{x}/Program_Committee'.format(x=notes[0].number))
        assert 0 == len(revs_paper0.members)

        revs_paper1 = pc_client.get_group(venue.get_id()+'/Submission{x}/Program_Committee'.format(x=notes[1].number))
        assert 0 == len(revs_paper1.members)

        revs_paper2 = pc_client.get_group(venue.get_id()+'/Submission{x}/Program_Committee'.format(x=notes[2].number))
        assert 0 == len(revs_paper2.members)

        assert openreview_client.get_edges_count(f'{venue.id}/Program_Committee/-/Assignment') == 0

        invitation = pc_client.get_invitation(id=f'{venue.id}/Program_Committee/-/Assignment')
        assert invitation.expdate < openreview.tools.datetime_millis(datetime.datetime.now())

        invitation = pc_client.get_invitation(id=f'{venue.id}/Program_Committee/-/Proposed_Assignment')
        assert invitation.expdate == None

        ## Set the assignments again
        venue.set_assignments(assignment_title='rev-matching', committee_id=f'{venue.id}/Program_Committee', enable_reviewer_reassignment=True)

        revs_paper0 = pc_client.get_group(venue.get_id()+'/Submission{x}/Program_Committee'.format(x=notes[0].number))
        assert 2 == len(revs_paper0.members)
        assert '~Reviewer_Venue1' in revs_paper0.members
        assert 'r2_venue@google.com' in revs_paper0.members
        assert pc_client.get_groups(prefix=venue.get_id()+'/Submission{x}/Program_Committee.*'.format(x=notes[0].number), member='~Reviewer_Venue1')
        assert pc_client.get_groups(prefix=venue.get_id()+'/Submission{x}/Program_Committee.*'.format(x=notes[0].number), member='r2_venue@google.com')

        revs_paper1 = pc_client.get_group(venue.get_id()+'/Submission{x}/Program_Committee'.format(x=notes[1].number))
        assert 2 == len(revs_paper1.members)
        assert 'r2_venue@google.com' in revs_paper1.members
        assert 'r3_venue@fb.com' in revs_paper1.members
        assert pc_client.get_groups(prefix=venue.get_id()+'/Submission{x}/Program_Committee.*'.format(x=notes[1].number), member='r3_venue@fb.com')
        assert pc_client.get_groups(prefix=venue.get_id()+'/Submission{x}/Program_Committee.*'.format(x=notes[1].number), member='r2_venue@google.com')

        revs_paper2 = pc_client.get_group(venue.get_id()+'/Submission{x}/Program_Committee'.format(x=notes[2].number))
        assert 2 == len(revs_paper2.members)
        assert 'r3_venue@fb.com' in revs_paper2.members
        assert '~Reviewer_Venue1' in revs_paper2.members
        assert pc_client.get_groups(prefix=venue.get_id()+'/Submission{x}/Program_Committee.*'.format(x=notes[2].number), member='~Reviewer_Venue1')
        assert pc_client.get_groups(prefix=venue.get_id()+'/Submission{x}/Program_Committee.*'.format(x=notes[2].number), member='r3_venue@fb.com')

        #check assignment process is set when invitation is created
        assignment_inv = openreview_client.get_invitation(venue.get_assignment_id(committee_id=venue.get_reviewers_id(), deployed=True))
        assert assignment_inv
        assert assignment_inv.process
        assert 'def process_update(client, edge, invitation, existing_edge):' in assignment_inv.process

        invitation = pc_client.get_invitation(id=f'{venue.id}/Program_Committee/-/Assignment')
        assert invitation.responseArchiveDate > openreview.tools.datetime_millis(datetime.datetime.now())

        invitation = pc_client.get_invitation(id=f'{venue.id}/Program_Committee/-/Proposed_Assignment')
        assert invitation.expdate < openreview.tools.datetime_millis(datetime.datetime.now())

        ## Set the review stage and try to undo the assignments
        venue.review_stage = openreview.stages.ReviewStage(due_date = datetime.datetime.now() + datetime.timedelta(minutes = 10))
        venue.create_review_stage()

        helpers.await_queue_edit(openreview_client, 'VenueV2.cc/-/Official_Review-0-1', count=1)

        reviewer_client = OpenReviewClient(username='r1_venue@mit.edu', password=helpers.strong_password) 

        anon_groups = reviewer_client.get_groups(prefix='VenueV2.cc/Submission1/Program_Committee.*', signatory='~Reviewer_Venue1')
        anon_group_id = anon_groups[0].id

        review_edit = reviewer_client.post_note_edit(
            invitation='VenueV2.cc/Submission1/-/Official_Review',
            signatures=[anon_group_id],
            note=openreview.api.Note(
                content={
                    'title': { 'value': 'Review title'},
                    'review': { 'value': 'good paper' },
                    'rating': { 'value': 10 },
                    'confidence': { 'value': 5 },
                }
            )
        )

        with pytest.raises(openreview.OpenReviewException, match=r'Can not delete assignments when there are reviews posted.'):
            venue.unset_assignments(assignment_title='rev-matching', committee_id=f'{venue.id}/Program_Committee')

        with pytest.raises(openreview.OpenReviewException, match=r'Can not overwrite assignments when there are reviews posted.'):
            venue.set_assignments(assignment_title='rev-matching', committee_id=f'{venue.id}/Program_Committee', enable_reviewer_reassignment=True, overwrite=True)            

        ## Delete review so the other tests can run
        reviewer_client.post_note_edit(
            invitation='VenueV2.cc/Submission1/-/Official_Review',
            signatures=[anon_group_id],
            note=openreview.api.Note(
                id = review_edit['note']['id'],
                ddate = openreview.tools.datetime_millis(datetime.datetime.now()),
                content={
                    'title': { 'value': 'Review title'},
                    'review': { 'value': 'good paper' },
                    'rating': { 'value': 10 },
                    'confidence': { 'value': 5 },
                }
            )
        )        
    
    def test_redeploy_assigments(self, venue, openreview_client, pc_client, helpers):

        notes = venue.get_submissions(sort='number:asc')

        venue.setup_committee_matching(committee_id=venue.get_reviewers_id(), compute_conflicts=True)

        #Reviewer assignments
        pc_client.post_edge(Edge(invitation = venue.get_assignment_id(venue.get_reviewers_id()),
            readers = [venue.id, f'{venue.id}/Submission{notes[0].number}/Senior_Program_Committee', 'r3_venue@fb.com'],
            nonreaders = [f'{venue.id}/Submission{notes[0].number}/Authors'],
            writers = [venue.id, f'{venue.id}/Submission{notes[0].number}/Senior_Program_Committee'],
            signatures = [venue.id],
            head = notes[0].id,
            tail = 'r3_venue@fb.com',
            label = 'rev-matching-new',
            weight = 0.98
        ))

        pc_client.post_edge(Edge(invitation = venue.get_assignment_id(venue.get_reviewers_id()),
            readers = [venue.id, f'{venue.id}/Submission{notes[1].number}/Senior_Program_Committee', '~Reviewer_Venue1'],
            nonreaders = [f'{venue.id}/Submission{notes[1].number}/Authors'],
            writers = [venue.id, f'{venue.id}/Submission{notes[1].number}/Senior_Program_Committee'],
            signatures = [venue.id],
            head = notes[1].id,
            tail = '~Reviewer_Venue1',
            label = 'rev-matching-new',
            weight = 0.98
        ))

        pc_client.post_edge(Edge(invitation = venue.get_assignment_id(venue.get_reviewers_id()),
            readers = [venue.id, f'{venue.id}/Submission{notes[2].number}/Senior_Program_Committee', 'r2_venue@google.com'],
            nonreaders = [f'{venue.id}/Submission{notes[2].number}/Authors'],
            writers = [venue.id, f'{venue.id}/Submission{notes[2].number}/Senior_Program_Committee'],
            signatures = [venue.id],
            head = notes[2].id,
            tail = 'r2_venue@google.com',
            label = 'rev-matching-new',
            weight = 0.98
        ))

        edges = pc_client.get_edges_count(
            invitation=f'{venue.id}/Program_Committee/-/Proposed_Assignment',
            label='rev-matching-new'
        )
        assert 3 == edges

        venue.set_assignments(assignment_title='rev-matching-new', overwrite=True, committee_id=f'{venue.id}/Program_Committee')

        revs_paper0 = pc_client.get_group(venue.get_id()+'/Submission{x}/Program_Committee'.format(x=notes[0].number))
        assert ['r3_venue@fb.com'] == revs_paper0.members
        assert pc_client.get_groups(prefix=venue.get_id()+'/Submission{x}/Program_Committee.*'.format(x=notes[0].number), member=['r3_venue@fb.com'])

        revs_paper1 = pc_client.get_group(venue.get_id()+'/Submission{x}/Program_Committee'.format(x=notes[1].number))
        assert ['~Reviewer_Venue1'] == revs_paper1.members
        assert pc_client.get_groups(prefix=venue.get_id()+'/Submission{x}/Program_Committee.*'.format(x=notes[1].number), member=['~Reviewer_Venue1'])

        revs_paper2 = pc_client.get_group(venue.get_id()+'/Submission{x}/Program_Committee'.format(x=notes[2].number))
        assert ['r2_venue@google.com'] == revs_paper2.members
        assert pc_client.get_groups(prefix=venue.get_id()+'/Submission{x}/Program_Committee.*'.format(x=notes[2].number), member=['r2_venue@google.com'])


        ## Emergency reviewers, append reviewers
        reviewer_group = openreview_client.get_group(venue.id + '/Program_Committee')
        openreview_client.add_members_to_group(reviewer_group, ['r2_venue@mit.edu'])

        venue.setup_committee_matching(committee_id=venue.get_reviewers_id(), compute_conflicts=True)

        pc_client.post_edge(Edge(invitation = venue.get_assignment_id(venue.get_reviewers_id()),
            readers = [venue.id, f'{venue.id}/Submission{notes[0].number}/Senior_Program_Committee', '~Reviewer_Venue1'],
            nonreaders = [f'{venue.id}/Submission{notes[0].number}/Authors'],
            writers = [venue.id, f'{venue.id}/Submission{notes[0].number}/Senior_Program_Committee'],
            signatures = [venue.id],
            head = notes[0].id,
            tail = '~Reviewer_Venue1',
            label = 'rev-matching-emergency',
            weight = 0.98
        ))

        pc_client.post_edge(Edge(invitation = venue.get_assignment_id(venue.get_reviewers_id()),
            readers = [venue.id, f'{venue.id}/Submission{notes[0].number}/Senior_Program_Committee', 'r2_venue@mit.edu'],
            nonreaders = [f'{venue.id}/Submission{notes[0].number}/Authors'],
            writers = [venue.id, f'{venue.id}/Submission{notes[0].number}/Senior_Program_Committee'],
            signatures = [venue.id],
            head = notes[0].id,
            tail = 'r2_venue@mit.edu',
            label = 'rev-matching-emergency',
            weight = 0.98
        ))

        pc_client.post_edge(Edge(invitation = venue.get_assignment_id(venue.get_reviewers_id()),
            readers = [venue.id, f'{venue.id}/Submission{notes[1].number}/Senior_Program_Committee', 'r2_venue@google.com'],
            nonreaders = [f'{venue.id}/Submission{notes[1].number}/Authors'],
            writers = [venue.id, f'{venue.id}/Submission{notes[1].number}/Senior_Program_Committee'],
            signatures = [venue.id],
            head = notes[1].id,
            tail = 'r2_venue@google.com',
            label = 'rev-matching-emergency',
            weight = 0.98
        ))

        venue.set_assignments(assignment_title='rev-matching-emergency', committee_id=f'{venue.id}/Program_Committee')

        revs_paper0 = pc_client.get_group(venue.get_id()+'/Submission{x}/Program_Committee'.format(x=notes[0].number))
        assert len(revs_paper0.members) == 3
        assert 'r3_venue@fb.com' in revs_paper0.members
        assert '~Reviewer_Venue1' in revs_paper0.members
        assert 'r2_venue@mit.edu' in revs_paper0.members

        revs_paper1 = pc_client.get_group(venue.get_id()+'/Submission{x}/Program_Committee'.format(x=notes[1].number))
        assert len(revs_paper1.members) == 2
        assert '~Reviewer_Venue1' in revs_paper1.members
        assert 'r2_venue@google.com' in revs_paper1.members

        revs_paper2 = pc_client.get_group(venue.get_id()+'/Submission{x}/Program_Committee'.format(x=notes[2].number))
        assert ['r2_venue@google.com'] == revs_paper2.members

        ## Un deploy the first assignment
        venue.unset_assignments(assignment_title='rev-matching-new', committee_id=f'{venue.id}/Program_Committee')

        revs_paper0 = pc_client.get_group(venue.get_id()+'/Submission{x}/Program_Committee'.format(x=notes[0].number))
        assert len(revs_paper0.members) == 2
        assert '~Reviewer_Venue1' in revs_paper0.members
        assert 'r2_venue@mit.edu' in revs_paper0.members

        revs_paper1 = pc_client.get_group(venue.get_id()+'/Submission{x}/Program_Committee'.format(x=notes[1].number))
        assert len(revs_paper1.members) == 1
        assert 'r2_venue@google.com' in revs_paper1.members

        revs_paper2 = pc_client.get_group(venue.get_id()+'/Submission{x}/Program_Committee'.format(x=notes[2].number))
        assert len(revs_paper2.members) == 0
        
        ## Deploy again
        venue.set_assignments(assignment_title='rev-matching-new', committee_id=f'{venue.id}/Program_Committee')

        revs_paper0 = pc_client.get_group(venue.get_id()+'/Submission{x}/Program_Committee'.format(x=notes[0].number))
        assert len(revs_paper0.members) == 3
        assert 'r3_venue@fb.com' in revs_paper0.members
        assert '~Reviewer_Venue1' in revs_paper0.members
        assert 'r2_venue@mit.edu' in revs_paper0.members

        revs_paper1 = pc_client.get_group(venue.get_id()+'/Submission{x}/Program_Committee'.format(x=notes[1].number))
        assert len(revs_paper1.members) == 2
        assert 'r2_venue@google.com' in revs_paper1.members
        assert '~Reviewer_Venue1' in revs_paper1.members

        revs_paper2 = pc_client.get_group(venue.get_id()+'/Submission{x}/Program_Committee'.format(x=notes[2].number))
        assert len(revs_paper2.members) == 1        
        assert 'r2_venue@google.com' in revs_paper2.members 
        
        pc_client.remove_members_from_group(f'{venue.id}/Submission1/Program_Committee', ['~Reviewer_Venue1'])

        venue.setup_committee_matching(committee_id=venue.get_reviewers_id(), compute_conflicts=True)
        
        pc_client.post_edge(Edge(invitation = venue.get_assignment_id(venue.get_reviewers_id()),
            readers = [venue.id, f'{venue.id}/Submission{notes[0].number}/Senior_Program_Committee', 'r2_venue@google.com'],
            nonreaders = [f'{venue.id}/Submission{notes[0].number}/Authors'],
            writers = [venue.id, f'{venue.id}/Submission{notes[0].number}/Senior_Program_Committee'],
            signatures = [venue.id],
            head = notes[0].id,
            tail = 'r2_venue@google.com',
            label = 'rev-matching-emergency-2',
            weight = 0.98
        ))

        venue.set_assignments(assignment_title='rev-matching-emergency-2', committee_id=f'{venue.id}/Program_Committee')

        revs_paper0 = pc_client.get_group(venue.get_id()+'/Submission{x}/Program_Committee'.format(x=notes[0].number))
        assert len(revs_paper0.members) == 3
        assert 'r3_venue@fb.com' in revs_paper0.members
        assert 'r2_venue@mit.edu' in revs_paper0.members
        assert 'r2_venue@google.com' in revs_paper0.members

        revs_paper1 = pc_client.get_group(venue.get_id()+'/Submission{x}/Program_Committee'.format(x=notes[1].number))
        assert len(revs_paper1.members) == 2
        assert '~Reviewer_Venue1' in revs_paper1.members
        assert 'r2_venue@google.com' in revs_paper1.members

        revs_paper2 = pc_client.get_group(venue.get_id()+'/Submission{x}/Program_Committee'.format(x=notes[2].number))
        assert ['r2_venue@google.com'] == revs_paper2.members

        venue.setup_committee_matching(committee_id=venue.get_reviewers_id(), compute_conflicts=True)

        pc_client.post_edge(Edge(invitation = venue.get_assignment_id(venue.get_reviewers_id()),
            readers = [venue.id, f'{venue.id}/Submission{notes[2].number}/Senior_Program_Committee', 'r2_venue@google.com'],
            nonreaders = [f'{venue.id}/Submission{notes[2].number}/Authors'],
            writers = [venue.id, f'{venue.id}/Submission{notes[2].number}/Senior_Program_Committee'],
            signatures = [venue.id],
            head = notes[2].id,
            tail = 'r2_venue@google.com',
            label = 'rev-matching-emergency-3',
            weight = 0.98
        ))

        venue.set_assignments(assignment_title='rev-matching-emergency-3', overwrite=True, committee_id=f'{venue.id}/Program_Committee')

        revs_paper0 = pc_client.get_group(venue.get_id()+'/Submission{x}/Program_Committee'.format(x=notes[0].number))
        assert [] == revs_paper0.members

        revs_paper1 = pc_client.get_group(venue.get_id()+'/Submission{x}/Program_Committee'.format(x=notes[1].number))
        assert [] == revs_paper1.members

        revs_paper2 = pc_client.get_group(venue.get_id()+'/Submission{x}/Program_Committee'.format(x=notes[2].number))
        assert ['r2_venue@google.com'] == revs_paper2.members

    def test_set_reviewers_assignments_as_author(self, venue, pc_client, helpers):

        pc3_client = OpenReviewClient(username='pc3_venue@mail.com', password=helpers.strong_password)
        # pc3_client.impersonate(venue.id) #ForbiddenError

        venue.client = pc3_client

        notes = venue.get_submissions(sort='number:asc')

        venue.setup_committee_matching(committee_id=venue.get_reviewers_id(), compute_conflicts=True)

        pc3_client.post_edge(Edge(invitation = venue.get_assignment_id(venue.get_reviewers_id()),
            readers = [venue.id, f'{venue.id}/Submission{notes[1].number}/Senior_Program_Committee', '~Reviewer_Venue1'],
            nonreaders = [f'{venue.id}/Submission{notes[1].number}/Authors'],
            writers = [venue.id, f'{venue.id}/Submission{notes[1].number}/Senior_Program_Committee'],
            signatures = [venue.id],
            head = notes[1].id,
            tail = '~Reviewer_Venue1',
            label = 'rev-matching-emergency-6',
            weight = 0.98
        ))

        pc3_client.post_edge(Edge(invitation = venue.get_assignment_id(venue.get_reviewers_id()),
            readers = [venue.id, f'{venue.id}/Submission{notes[0].number}/Senior_Program_Committee', 'r3_venue@fb.com'],
            nonreaders = [f'{venue.id}/Submission{notes[0].number}/Authors'],
            writers = [venue.id, f'{venue.id}/Submission{notes[0].number}/Senior_Program_Committee'],
            signatures = [venue.id],
            head = notes[0].id,
            tail = 'r3_venue@fb.com',
            label = 'rev-matching-emergency-6',
            weight = 0.98
        ))

        venue.set_assignments(assignment_title='rev-matching-emergency-6', committee_id=f'{venue.id}/Program_Committee')

        revs_paper0 = pc_client.get_group(venue.get_id()+'/Submission{x}/Program_Committee'.format(x=notes[0].number))
        assert ['r3_venue@fb.com'] == revs_paper0.members

        revs_paper1 = pc_client.get_group(venue.get_id()+'/Submission{x}/Program_Committee'.format(x=notes[1].number))
        assert ['~Reviewer_Venue1'] == revs_paper1.members

        revs_paper2 = pc_client.get_group(venue.get_id()+'/Submission{x}/Program_Committee'.format(x=notes[2].number))
        assert ['r2_venue@google.com'] == revs_paper2.members


    def test_set_ac_assigments(self, venue, openreview_client, pc_client, test_client, helpers):

        notes = venue.get_submissions(sort='number:asc')
        venue.client = openreview_client

        edges = pc_client.get_edges_count(
            invitation=f'{venue.id}/Senior_Program_Committee/-/Proposed_Assignment',
            label='ac-matching'
        )
        assert 0 == edges

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

        edges = pc_client.get_edges_count(
            invitation=f'{venue.id}/Senior_Program_Committee/-/Proposed_Assignment',
            label='ac-matching'
        )
        assert 3 == edges

        venue.set_assignments(assignment_title='ac-matching', committee_id=f'{venue.id}/Senior_Program_Committee')

        assert pc_client.get_group(f'{venue.id}/Submission1/Senior_Program_Committee').members == ['ac1_venue@cmu.edu']

        assert pc_client.get_group(f'{venue.id}/Submission2/Senior_Program_Committee').members == ['ac2_venue@umass.edu']

        assert pc_client.get_group(f'{venue.id}/Submission3/Senior_Program_Committee').members == ['ac2_venue@umass.edu']

        venue.setup_committee_matching(committee_id=venue.get_area_chairs_id(), compute_conflicts=True)
        
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

        assert pc_client.get_group(f'{venue.id}/Submission1/Senior_Program_Committee').members == ['ac2_venue@umass.edu']

        assert pc_client.get_group(f'{venue.id}/Submission2/Senior_Program_Committee').members == ['ac1_venue@cmu.edu']

        assert pc_client.get_group(f'{venue.id}/Submission3/Senior_Program_Committee').members == []

        # delete AC Assignment edge
        edge = pc_client.get_edges(invitation=f'{venue.id}/Senior_Program_Committee/-/Assignment', head=notes[0].id, tail='ac2_venue@umass.edu')[0]
        assert edge
        edge.ddate = openreview.tools.datetime_millis(datetime.datetime.now())
        pc_client.post_edge(edge)

        helpers.await_queue_edit(openreview_client, edge.id)

    def test_setup_matching_with_mentors(self, venue, pc_client, helpers):

        mentors=venue.group_builder.post_group(Group(id=venue.id + '/Reviewers_Mentors',
            readers = [venue.id],
            writers = [venue.id],
            signatures = [venue.id],
            signatories = [venue.id],
            members = ['ac1_venue@cmu.edu', 'ac2_venue@umass.edu']
        ))

        mentees=venue.group_builder.post_group(Group(id=venue.id + '/Reviewers_Mentees',
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

        affinity_scores = pc_client.get_edges_count(invitation=venue.id + '/Reviewers_Mentors/-/Affinity_Score')
        assert affinity_scores == 6

