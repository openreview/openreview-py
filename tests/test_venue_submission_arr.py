import csv
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
from openreview.stages import SubmissionStage, BidStage

class TestVenueSubmission():

    @pytest.fixture(scope="class")
    def venue(self, openreview_client):
        conference_id = 'TestVenue.cc'

        venue = Venue(openreview_client, conference_id, 'openreview.net/Support')
        venue.use_area_chairs = True
        venue.name = 'Test Venue V2'
        venue.short_name = 'TV 22'
        venue.website = 'testvenue.org'
        venue.contact = 'testvenue@contact.com'
        venue.reviewer_identity_readers = [openreview.stages.IdentityReaders.PROGRAM_CHAIRS, openreview.stages.IdentityReaders.AREA_CHAIRS_ASSIGNED]

        now = datetime.datetime.utcnow()
        venue.submission_stage = SubmissionStage(double_blind=True, readers=[SubmissionStage.Readers.EVERYONE], withdrawn_submission_public=True, withdrawn_submission_reveal_authors=True, desk_rejected_submission_public=True)

        venue.bid_stages = [
            BidStage(due_date=now + datetime.timedelta(minutes = 30), committee_id=venue.get_reviewers_id()),
            BidStage(due_date=now + datetime.timedelta(minutes = 30), committee_id=venue.get_area_chairs_id())
        ]        
        venue.review_stage = openreview.stages.ReviewStage(start_date=now + datetime.timedelta(minutes = 4), due_date=now + datetime.timedelta(minutes = 40))
        venue.meta_review_stage = openreview.stages.MetaReviewStage(start_date=now + datetime.timedelta(minutes = 10), due_date=now + datetime.timedelta(minutes = 40))
        venue.submission_revision_stage = openreview.SubmissionRevisionStage(
            name='Camera_Ready_Revision',
            due_date=now + datetime.timedelta(minutes = 40),
            only_accepted=True
        )

        return venue

    def test_setup(self, venue, openreview_client, helpers):

        venue.setup(program_chair_ids=['venue_pc@mail.com'])
        venue.create_submission_stage()
        venue.create_review_stage()
        venue.create_meta_review_stage()
        venue.create_submission_revision_stage()
        assert openreview_client.get_group('TestVenue.cc')
        assert openreview_client.get_group('TestVenue.cc/Authors')

        helpers.create_user('venue_pc@mail.com', 'PC Venue', 'One')

    def test_recruitment_stage(self, venue, openreview_client, selenium, request_page, helpers):

        #recruit reviewers and area chairs to create groups
        message = 'Dear {{fullname}},\n\nYou have been nominated by the program chair committee of Test Venue V2 to serve as {{invitee_role}}.\n\nTo respond to the invitation, please click on the following link:\n\n{{invitation_url}}\n\nCheers!\n\nProgram Chairs'
        
        helpers.create_user('reviewer_venue_one@mail.com', 'Reviewer Venue', 'One')
        
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
        helpers.respond_invitation(selenium, request_page, invitation_url, accept=True, quota=1)

        reviewer_group = openreview_client.get_group('TestVenue.cc/Reviewers')
        assert reviewer_group
        assert '~Reviewer_Venue_One1' in reviewer_group.members    
    
    def test_submission_stage(self, venue, openreview_client, helpers):

        assert openreview_client.get_invitation('TestVenue.cc/-/Submission')

        helpers.create_user('celeste@maileleven.com', 'Celeste', 'MartinezEleven')
        author_client = OpenReviewClient(username='celeste@maileleven.com', password='1234')

        submission_note_1 = author_client.post_note_edit(
            invitation='TestVenue.cc/-/Submission',
            signatures= ['~Celeste_MartinezEleven1'],
            note=Note(
                content={
                    'title': { 'value': 'Paper 1 Title' },
                    'abstract': { 'value': 'Paper abstract' },
                    'authors': { 'value': ['Celeste MartinezEleven']},
                    'authorids': { 'value': ['~Celeste_MartinezEleven1']},
                    'pdf': {'value': '/pdf/' + 'p' * 40 +'.pdf' },
                    'keywords': {'value': ['aa'] }
                }
            ))

        helpers.await_queue_edit(openreview_client, edit_id=submission_note_1['id']) 

        submission = openreview_client.get_note(submission_note_1['note']['id'])
        assert len(submission.readers) == 2
        assert 'TestVenue.cc' in submission.readers
        assert 'TestVenue.cc/Submission1/Authors' in submission.readers

        #TODO: check emails, check author console

        submission_note_2 = author_client.post_note_edit(
            invitation='TestVenue.cc/-/Submission',
            signatures= ['~Celeste_MartinezEleven1'],
            note=Note(
                content={
                    'title': { 'value': 'Paper 2 Title' },
                    'abstract': { 'value': 'Paper abstract' },
                    'authors': { 'value': ['Celeste MartinezEleven']},
                    'authorids': { 'value': ['~Celeste_MartinezEleven1']},
                    'pdf': {'value': '/pdf/' + 'p' * 40 +'.pdf' },
                    'keywords': {'value': ['aa'] }
                }
            ))

        helpers.await_queue_edit(openreview_client, edit_id=submission_note_2['id']) 

    def test_post_submission_stage(self, venue, openreview_client):
                
        venue.submission_stage.readers = [SubmissionStage.Readers.REVIEWERS, SubmissionStage.Readers.AREA_CHAIRS]
        venue.setup_post_submission_stage()
        assert openreview_client.get_group('TestVenue.cc/Submission1/Authors')
        assert openreview_client.get_group('TestVenue.cc/Submission1/Reviewers')
        assert openreview_client.get_group('TestVenue.cc/Submission1/Area_Chairs')

        submissions = venue.get_submissions(sort='number:asc')
        assert len(submissions) == 2
        submission = submissions[0]
        assert len(submission.readers) == 4
        assert 'TestVenue.cc' in submission.readers
        assert 'TestVenue.cc/Submission1/Authors' in submission.readers        
        assert 'TestVenue.cc/Reviewers' in submission.readers
        assert 'TestVenue.cc/Area_Chairs' in submission.readers

        assert openreview_client.get_invitation('TestVenue.cc/Submission1/-/Withdrawal')
        assert openreview_client.get_invitation('TestVenue.cc/Submission2/-/Withdrawal')

        assert openreview_client.get_invitation('TestVenue.cc/Submission1/-/Desk_Rejection')
        assert openreview_client.get_invitation('TestVenue.cc/Submission2/-/Desk_Rejection')

    def test_review_stage(self, venue, openreview_client, helpers):

        assert openreview_client.get_invitation('TestVenue.cc/-/Official_Review')
        with pytest.raises(openreview.OpenReviewException, match=r'The Invitation TestVenue.cc/Submission1/-/Official_Review was not found'):
            assert openreview_client.get_invitation('TestVenue.cc/Submission1/-/Official_Review')

        openreview_client.post_invitation_edit(
            invitations='TestVenue.cc/-/Edit',
            readers=['TestVenue.cc'],
            writers=['TestVenue.cc'],
            signatures=['TestVenue.cc'],
            invitation=openreview.api.Invitation(id='TestVenue.cc/-/Official_Review',
                cdate=openreview.tools.datetime_millis(datetime.datetime.utcnow()) + 2000,
                signatures=['TestVenue.cc']
            )
        )

        helpers.await_queue_edit(openreview_client, 'TestVenue.cc/-/Official_Review-0-0')

        assert openreview_client.get_invitation('TestVenue.cc/-/Official_Review')
        assert openreview_client.get_invitation('TestVenue.cc/Submission1/-/Official_Review')

    def test_meta_review_stage(self, venue, openreview_client, helpers):

        assert openreview_client.get_invitation('TestVenue.cc/-/Meta_Review')
        with pytest.raises(openreview.OpenReviewException, match=r'The Invitation TestVenue.cc/Submission1/-/Meta_Review was not found'):
            assert openreview_client.get_invitation('TestVenue.cc/Submission1/-/Meta_Review')

        openreview_client.post_invitation_edit(
            invitations='TestVenue.cc/-/Edit',
            readers=['TestVenue.cc'],
            writers=['TestVenue.cc'],
            signatures=['TestVenue.cc'],
            invitation=openreview.api.Invitation(id='TestVenue.cc/-/Meta_Review',
                cdate=openreview.tools.datetime_millis(datetime.datetime.utcnow()) + 2000,
                signatures=['TestVenue.cc']
            )
        )

        helpers.await_queue_edit(openreview_client, 'TestVenue.cc/-/Meta_Review-0-0')
        
        assert openreview_client.get_invitation('TestVenue.cc/-/Meta_Review')
        assert openreview_client.get_invitation('TestVenue.cc/Submission1/-/Meta_Review')