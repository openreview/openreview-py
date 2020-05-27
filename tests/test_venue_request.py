import openreview
import pytest
import time
from selenium.common.exceptions import NoSuchElementException
from venue_request import VenueRequest

class TestVenueRequest():

    def test_venue_request_setup(self, client):
        
        venue = VenueRequest(client)

        assert venue.support_group
        assert venue.bid_stage_super_invitation
        assert venue.decision_stage_super_invitation
        assert venue.meta_review_stage_super_invitation
        assert venue.review_stage_super_invitation
        assert venue.meta_review_stage_super_invitation

        assert venue.deploy_super_invitation
        assert venue.comment_super_invitation
        assert venue.recruitment_super_invitation

    def test_post_venue_request(self, client):
        pass