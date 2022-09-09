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
from openreview.api import Group
from openreview.api import Invitation
from openreview.api import Edge

from openreview.venue import Venue

class TestVenueSubmission():

    def test_setup(self, openreview_client, selenium, request_page, helpers):
        conference_id = 'TestVenue.cc'

        venue = Venue(openreview_client, conference_id)
        venue.use_area_chairs = True
        venue.name = 'Test 2030 Venue V2'
        venue.short_name = 'TV 22'
        venue.website = 'testvenue.org'
        venue.contact = 'testvenue@contact.com'
        venue.reviewer_identity_readers = [openreview.Conference.IdentityReaders.PROGRAM_CHAIRS, openreview.Conference.IdentityReaders.AREA_CHAIRS_ASSIGNED]
        venue.setup()

        assert openreview_client.get_group('TestVenue.cc')
        assert openreview_client.get_group('TestVenue.cc/Authors')

        venue.set_submission_stage(openreview.builder.SubmissionStage(double_blind=True, readers=[openreview.builder.SubmissionStage.Readers.REVIEWERS_ASSIGNED, openreview.builder.SubmissionStage.Readers.AREA_CHAIRS_ASSIGNED]))

        assert openreview_client.get_invitation('TestVenue.cc/-/Submission')

        helpers.create_user('celeste@maileleven.com', 'Celeste', 'MartinezEleven')
        author_client = OpenReviewClient(username='celeste@maileleven.com', password='1234')

        submission_note_1 = author_client.post_note_edit(
            invitation=f'{conference_id}/-/Submission',
            signatures= ['~Celeste_MartinezEleven1'],
            note=Note(
                content={
                    'title': { 'value': 'Paper 1 Title' },
                    'abstract': { 'value': 'Paper abstract' },
                    'authors': { 'value': ['Celeste MartinezEleven']},
                    'authorids': { 'value': ['~Celeste_MartinezEleven1']},
                    'pdf': {'value': '/pdf/' + 'p' * 40 +'.pdf' },
                    'submission_length': {'value': 'Regular submission (no more than 12 pages of main content)' }
                }
            ))

        helpers.await_queue_edit(openreview_client, edit_id=submission_note_1['id']) 

        submission = openreview_client.get_note(submission_note_1['note']['id'])
        assert len(submission.readers) == 2
        assert 'TestVenue.cc' in submission.readers
        assert 'TestVenue.cc/Paper1/Authors' in submission.readers
                
        venue.setup_post_submission_stage()
        assert openreview_client.get_group('TestVenue.cc/Paper1/Authors')
        assert openreview_client.get_group('TestVenue.cc/Paper1/Reviewers')
        assert openreview_client.get_group('TestVenue.cc/Paper1/Area_Chairs')

        submission = openreview_client.get_note(submission.id)
        assert len(submission.readers) == 4
        assert 'TestVenue.cc' in submission.readers
        assert 'TestVenue.cc/Paper1/Authors' in submission.readers        
        assert 'TestVenue.cc/Paper1/Reviewers' in submission.readers
        assert 'TestVenue.cc/Paper1/Area_Chairs' in submission.readers

        now = datetime.datetime.utcnow()
        venue.review_stage = openreview.ReviewStage(due_date=now + datetime.timedelta(minutes = 40))
        venue.create_review_stage()

        assert openreview_client.get_invitation('TestVenue.cc/-/Official_Review')
        assert openreview_client.get_invitation('TestVenue.cc/Paper1/-/Official_Review')

        #recruit reviewers and area chairs to create groups
        message = 'Dear {{fullname}},\n\nYou have been nominated by the program chair committee of Test 2030 Venue V2 to serve as {{invitee_role}}.\n\nTo respond to the invitation, please click on the following link:\n\n{{invitation_url}}\n\nCheers!\n\nProgram Chairs'
        
        helpers.create_user('reviewer_venue_one@mail.com', 'Reviewer Venue', 'One')
        reviewer_client = OpenReviewClient(username='reviewer_venue_one@mail.com', password='1234')

        venue.recruit_reviewers(title='[TV 22] Invitation to serve as Reviewer',
            message=message,
            invitees = ['~Reviewer_Venue_One1'],
            contact_info='testvenue@contact.com',
            reduced_load_on_decline = ['1','2','3'])

        venue.recruit_reviewers(title='[TV 22] Invitation to serve as Area Chair',
            message=message,
            invitees = ['~Reviewer_Venue_One1'],
            reviewers_name = 'Area_Chairs',
            contact_info='testvenue@contact.com',
            allow_overlap_official_committee = True)

        messages = openreview_client.get_messages(to='reviewer_venue_one@mail.com')
        assert messages
        invitation_url = re.search('https://.*\n', messages[1]['content']['text']).group(0).replace('https://openreview.net', 'http://localhost:3030')[:-1]
        print('invitation_url', invitation_url)
        helpers.respond_invitation(selenium, request_page, invitation_url, accept=True)

        reviewer_group = openreview_client.get_group('TestVenue.cc/Reviewers')
        assert reviewer_group
        assert '~Reviewer_Venue_One1' in reviewer_group.members
        
        #bid stages
        now = datetime.datetime.utcnow()
        bid_stages = [
            openreview.BidStage(due_date=now + datetime.timedelta(minutes = 30), committee_id=venue.get_reviewers_id()),
            openreview.BidStage(due_date=now + datetime.timedelta(minutes = 30), committee_id=venue.get_area_chairs_id())
        ]
        venue.bid_stages = bid_stages
        venue.create_bid_stages()

        assert openreview_client.get_invitation(venue.id + '/Reviewers/-/Bid')
        assert openreview_client.get_invitation(venue.id + '/Area_Chairs/-/Bid')

        #test posting a bid edge
        openreview_client.add_members_to_group(venue.id + '/Paper1/Reviewers', '~Reviewer_Venue_One1')

        bid_edge = reviewer_client.post_edge(Edge(invitation = venue.id + '/Reviewers/-/Bid',
            head = submission.id,
            tail = '~Reviewer_Venue_One1',
            readers = ['TestVenue.cc', 'TestVenue.cc/Area_Chairs', '~Reviewer_Venue_One1'],
            writers = ['TestVenue.cc', '~Reviewer_Venue_One1'],
            signatures = ['~Reviewer_Venue_One1'],
            label = 'High'
        ))

        bid_edges = openreview_client.get_edges(invitation=venue.id + '/Reviewers/-/Bid')
        assert len(bid_edges) == 1

        #post recruitment note with reduced load to test custom load edge
        recruitment_note = openreview_client.post_note_edit(
            invitation=f'{conference_id}/Reviewers/-/Recruitment',
            signatures= ['(anonymous)'],
            note=Note(
                content={
                    'title': { 'value': 'Recruit response' },
                    'user': { 'value': '~Reviewer_Venue_One1' },
                    'key': { 'value': '62b25fec293218c0b0986204b80beaee080f86c9a308c34ef8beb296b7c62188'},
                    'response': { 'value': 'Yes'},
                    'reduced_load': {'value': '1' },
                }
            ))

        helpers.await_queue_edit(openreview_client, edit_id=recruitment_note['id']) 

        venue.setup_committee_matching()

        # #test posting proposed assignment edge
        proposed_assignment_edge = openreview_client.post_edge(Edge(
            invitation = venue.id + '/Reviewers/-/Proposed_Assignment',
            # signatures = ['TestVenue.cc'],
            signatures = ['TestVenue.cc/Paper1/Area_Chairs'],
            head = submission.id,
            tail = '~Reviewer_Venue_One1',
            readers = ['TestVenue.cc','TestVenue.cc/Paper1/Area_Chairs','~Reviewer_Venue_One1'],
            writers = ['TestVenue.cc','TestVenue.cc/Paper1/Area_Chairs'],
            weight = 0.92,
            label = 'test-matching-1'
        ))

        assert proposed_assignment_edge
        assert proposed_assignment_edge.nonreaders == ['TestVenue.cc/Paper1/Authors']

        custom_load_edges = openreview_client.get_edges(invitation=f'{conference_id}/Reviewers/-/Custom_Max_Papers')
        assert (len(custom_load_edges)) == 1

        now = datetime.datetime.utcnow()
        venue.meta_review_stage = openreview.MetaReviewStage(due_date=now + datetime.timedelta(minutes = 40))
        venue.create_meta_review_stage()

        helpers.create_user('ac_venue_one@mail.com', 'Area Chair', 'Venue One')
        ac_client = OpenReviewClient(username='ac_venue_one@mail.com', password='1234')

        assert openreview_client.get_invitation('TestVenue.cc/-/Meta_Review')
        assert openreview_client.get_invitation('TestVenue.cc/Paper1/-/Meta_Review')

        openreview_client.add_members_to_group(conference_id+'/Area_Chairs', '~Area_Chair_Venue_One1')
        openreview_client.add_members_to_group(conference_id+'/Paper1/Area_Chairs', '~Area_Chair_Venue_One1')