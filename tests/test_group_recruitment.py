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
        venue.short_name = 'V 24'
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
        assert openreview_client.get_invitation('Venue.cc/Reviewers/Invited/-/Recruitment_Settings')

        helpers.create_user('reviewer3@venue.cc', 'Reviewer', 'VenueThree')
        
        # use invitation to edit group content
        openreview_client.post_group_edit(
                invitation='Venue.cc/Reviewers/Invited/-/Recruitment_Settings',
                group=openreview.api.Group(
                    content = {
                        'reduced_load': { 'value': [1,2,3] },
                        'recruitment_template': { 'value': '''Dear {{fullname}},

You have been nominated by the program chair committee of V 24 to serve as Reviewer. As a respected researcher in the area, we hope you will accept and help us make V 24 a success.

You are also welcome to submit papers, so please also consider submitting to V 24.

We will be using OpenReview.net and a reviewing process that we hope will be engaging and inclusive of the whole community.

To respond the invitation, please click on the following link:

{{invitation_url}}

Please answer within 10 days.

If you accept, please make sure that your OpenReview account is updated and lists all the emails you are using. Visit http://openreview.net/profile after logging in.

If you have any questions, please contact us at info@openreview.net.

Cheers!

Program Chairs
''' },
                        'recruitment_subject': { 'value': '[V 24] Invitation to serve as Reviewer' },
                        'allow_overlap': { 'value': False }
                    }
                )
            )
        
        invitee_details = '''~Reviewer_VenueThree1\nreviewer1@venue.cc, Reviewer VenueOne\nreviewer2@venue.cc, Reviewer VenueTwo'''

        # use invitation to recruit reviewers
        edit = openreview_client.post_group_edit(
                invitation='Venue.cc/Reviewers/Invited/-/Recruitment',
                content={
                    'inviteeDetails': { 'value':  invitee_details }
                },
                group=openreview.api.Group()
            )
        helpers.await_queue_edit(openreview_client, invitation='Venue.cc/Reviewers/Invited/-/Recruitment')

        invited_group = openreview_client.get_group('Venue.cc/Reviewers/Invited')
        assert len(invited_group.members) == 3
        assert 'reviewer1@venue.cc' in invited_group.members
        assert 'reviewer2@venue.cc' in invited_group.members
        assert '~Reviewer_VenueThree1' in invited_group.members

        messages = openreview_client.get_messages(subject = '[V 24] Invitation to serve as Reviewer')
        assert len(messages) == 3

        edit = openreview_client.get_group_edit(edit['id'])
        assert 'invitedStatus' in edit.content
        assert 'reviewer1@venue.cc' in edit.content['invitedStatus']['value']
        assert 'reviewer2@venue.cc' in edit.content['invitedStatus']['value']
        assert '~Reviewer_VenueThree1' in edit.content['invitedStatus']['value']
        assert 'alreadyInvitedStatus' not in edit.content
        assert 'alreadyMemberStatus' not in edit.content
        assert 'errorStatus' not in edit.content