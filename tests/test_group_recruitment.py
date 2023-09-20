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

class TestGroupRecruitment():

    @pytest.fixture(scope="class")
    def venue(self, openreview_client):
        conference_id = 'Venue.cc'

        venue = Venue(openreview_client, conference_id, 'openreview.net/Support')
        venue.invitation_builder.update_wait_time = 2000
        venue.invitation_builder.update_date_string = "#{4/mdate} + 2000"
        venue.automatic_reviewer_assignment = True 
        venue.use_area_chairs = True
        venue.name = 'Venue V2'
        venue.short_name = 'V 23'
        venue.website = 'venue.org'
        venue.contact = 'venue@contact.com'
        venue.reviewer_identity_readers = [openreview.stages.IdentityReaders.PROGRAM_CHAIRS, openreview.stages.IdentityReaders.AREA_CHAIRS_ASSIGNED]

        now = datetime.datetime.utcnow()
        venue.submission_stage = SubmissionStage(
            double_blind=True,
            due_date=now + datetime.timedelta(minutes = 30),
            readers=[SubmissionStage.Readers.EVERYONE], 
            withdrawn_submission_public=True, 
            withdrawn_submission_reveal_authors=True, 
            desk_rejected_submission_public=True,
            force_profiles=False 
        )

        return venue
    
    def test_recruitment(self, venue, openreview_client, helpers):

        venue.setup(program_chair_ids=['pc_venue23@mail.com'])
        venue.create_submission_stage()
        venue.group_builder.create_recruitment_committee_groups('Reviewers')

        assert openreview_client.get_group('Venue.cc')
        assert openreview_client.get_group('Venue.cc/Authors')
        assert openreview_client.get_group('Venue.cc/Reviewers')
        assert openreview_client.get_group('Venue.cc/Reviewers/Invited')
        assert openreview_client.get_group('Venue.cc/Reviewers/Declined')
        assert openreview_client.get_invitation('Venue.cc/Reviewers/Invited/-/Recruitment')
        assert openreview_client.get_invitation('Venue.cc/Reviewers/Invited/-/Edit')

        helpers.create_user('reviewer3@venue.cc', 'Reviewer', 'VenueThree')
        
        # use invitation to edit group content
        openreview_client.post_group_edit(
                invitation='Venue.cc/Reviewers/Invited/-/Edit',
                group=openreview.api.Group(
                    content = {
                        'reduced_load': { 'value': [1,2,3] },
                        'recruitment_template': { 'value': 'This is a recruitment template.' },
                        'allow_overlap': { 'value': False }
                    }
                )
            )
        
        invitee_details = '''reviewer1@venue.cc, Reviewer VenueOne\nreviewer2@venue.cc, Reviewer VenueTwo\n~Reviewer_VenueThree1'''

        # use invitation to recriut reviewers
        openreview_client.post_group_edit(
                invitation='Venue.cc/Reviewers/Invited/-/Recruitment',
                content={
                    'inviteeDetails': { 'value':  invitee_details }
                },
                group=openreview.api.Group()
            )

        # invited_group = openreview_client.get_group('Venue.cc/Reviewers/Invited')
        # assert len(invited_group.members) == 2
        # assert 'celestemartinez@mail.com' in invited_group.members
        # assert 'emiliarubio@mail.com' in invited_group.members

        # openreview_client.post_group_edit(
        #         invitation='Venue.cc/Reviewers/Invited/-/Recruitment',
        #         group=openreview.api.Group(
        #             members = ['anagomez@mail.com']
        #         )
        #     )