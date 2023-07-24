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

class TestNonAnonymousVenue():

    @pytest.fixture(scope="class")
    def venue(self, openreview_client):
        conference_id = 'TestNonAnonymousVenue.cc'

        venue = Venue(openreview_client, conference_id, 'openreview.net/Support')
        venue.invitation_builder.update_wait_time = 2000
        venue.invitation_builder.update_date_string = "#{4/mdate} + 2000"
        venue.automatic_reviewer_assignment = True 
        venue.use_area_chairs = True
        venue.name = 'Non Anonymous Venue V2'
        venue.short_name = 'Non Anonymous Venue 22'
        venue.website = 'testvenue.org'
        venue.contact = 'testvenue@contact.com'
        venue.reviewer_identity_readers = [openreview.stages.IdentityReaders.PROGRAM_CHAIRS]

        now = datetime.datetime.utcnow()
        venue.submission_stage = SubmissionStage(
            double_blind=False,
            due_date=now + datetime.timedelta(minutes = 30),
            readers=[SubmissionStage.Readers.EVERYONE], 
            withdrawn_submission_public=True, 
            withdrawn_submission_reveal_authors=True, 
            desk_rejected_submission_public=True,
            force_profiles=True,
            remove_fields=['abstract']
        )

        venue.review_stage = openreview.stages.ReviewStage(start_date=now + datetime.timedelta(minutes = 4), due_date=now + datetime.timedelta(minutes = 40), allow_de_anonymization=True)

        return venue

    def test_setup(self, venue, openreview_client, helpers):

        venue.setup(program_chair_ids=['venue_pc@mail.com'])
        venue.create_submission_stage()
        venue.create_review_stage()
        assert openreview_client.get_group('TestNonAnonymousVenue.cc')
        assert openreview_client.get_group('TestNonAnonymousVenue.cc/Authors')

        helpers.create_user('venue_pc@mail.com', 'PC Venue', 'One')

    def test_submission_stage(self, venue, openreview_client, helpers):

        assert openreview_client.get_invitation('TestNonAnonymousVenue.cc/-/Submission')

        helpers.create_user('celeste@maileleven.com', 'Celeste', 'MartinezEleven')
        author_client = OpenReviewClient(username='celeste@maileleven.com', password=helpers.strong_password)

        submission_note_1 = author_client.post_note_edit(
            invitation='TestNonAnonymousVenue.cc/-/Submission',
            signatures= ['~Celeste_MartinezEleven1'],
            note=Note(
                content={
                    'title': { 'value': 'Paper 1 Title' },
                    'authors': { 'value': ['Celeste MartinezEleven']},
                    'authorids': { 'value': ['~Celeste_MartinezEleven1']},
                    'pdf': {'value': '/pdf/' + 'p' * 40 +'.pdf' },
                    'keywords': {'value': ['aa'] }
                }
            ))

        helpers.await_queue_edit(openreview_client, edit_id=submission_note_1['id']) 

        submission = openreview_client.get_note(submission_note_1['note']['id'])
        assert len(submission.readers) == 2
        assert 'TestNonAnonymousVenue.cc' in submission.readers
        assert ['TestNonAnonymousVenue.cc', '~Celeste_MartinezEleven1'] == submission.readers

    def test_post_submission_stage(self, venue, openreview_client, helpers):
                
        venue.submission_stage.readers = [SubmissionStage.Readers.REVIEWERS, SubmissionStage.Readers.AREA_CHAIRS]
        venue.submission_stage.exp_date = datetime.datetime.utcnow() + datetime.timedelta(seconds = 60)
        venue.create_submission_stage()

        helpers.await_queue_edit(openreview_client, 'TestNonAnonymousVenue.cc/-/Post_Submission-0-0')
        helpers.await_queue_edit(openreview_client, 'TestNonAnonymousVenue.cc/Reviewers/-/Submission_Group-0-0')
        helpers.await_queue_edit(openreview_client, 'TestNonAnonymousVenue.cc/Area_Chairs/-/Submission_Group-0-0')

        assert openreview_client.get_group('TestNonAnonymousVenue.cc/Submission1/Authors')
        assert openreview_client.get_group('TestNonAnonymousVenue.cc/Submission1/Reviewers')
        assert openreview_client.get_group('TestNonAnonymousVenue.cc/Submission1/Area_Chairs')

        submissions = venue.get_submissions(sort='number:asc')
        assert len(submissions) == 1
        submission = submissions[0]
        assert len(submission.readers) == 4
        assert 'TestNonAnonymousVenue.cc' in submission.readers
        assert 'TestNonAnonymousVenue.cc/Submission1/Authors' in submission.readers        
        assert 'TestNonAnonymousVenue.cc/Reviewers' in submission.readers
        assert 'TestNonAnonymousVenue.cc/Area_Chairs' in submission.readers
        assert 'readers' not in submission.content['authors']
        assert 'readers' not in submission.content['authorids']



    def test_review_stage(self, venue, openreview_client, helpers):

        assert openreview_client.get_invitation('TestNonAnonymousVenue.cc/-/Official_Review')
        with pytest.raises(openreview.OpenReviewException, match=r'The Invitation TestNonAnonymousVenue.cc/Submission1/-/Official_Review was not found'):
            assert openreview_client.get_invitation('TestNonAnonymousVenue.cc/Submission1/-/Official_Review')

        new_cdate = openreview.tools.datetime_millis(datetime.datetime.utcnow()) + 2000
        openreview_client.post_invitation_edit(
            invitations='TestNonAnonymousVenue.cc/-/Edit',
            readers=['TestNonAnonymousVenue.cc'],
            writers=['TestNonAnonymousVenue.cc'],
            signatures=['TestNonAnonymousVenue.cc'],
            invitation=openreview.api.Invitation(id='TestNonAnonymousVenue.cc/-/Official_Review',
                signatures=['TestNonAnonymousVenue.cc'],
                edit = {
                    'invitation': {
                        'cdate': new_cdate
                    }
                }
            )
        )

        helpers.await_queue_edit(openreview_client, 'TestNonAnonymousVenue.cc/-/Official_Review-0-0')
        helpers.await_queue_edit(openreview_client, 'TestNonAnonymousVenue.cc/-/Official_Review-0-1', count=2)

        invitations = openreview_client.get_invitations(invitation='TestNonAnonymousVenue.cc/-/Official_Review')
        assert len(invitations) == 1

        invitation = openreview_client.get_invitation('TestNonAnonymousVenue.cc/Submission1/-/Official_Review')
        assert '~.*' == invitation.edit['signatures']['param']['regex']

