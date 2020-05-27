import openreview
import pytest
import time
from selenium.common.exceptions import NoSuchElementException
from venue_request import VenueRequest

class TestVenueRequest():

    def test_venue_request_setup(self, client):
        
        venue = VenueRequest(client, 'openreview.net/Support', 'openreview.net')

        assert venue.support_group
        assert venue.bid_stage_super_invitation
        assert venue.decision_stage_super_invitation
        assert venue.meta_review_stage_super_invitation
        assert venue.review_stage_super_invitation
        assert venue.meta_review_stage_super_invitation

        assert venue.deploy_super_invitation
        assert venue.comment_super_invitation
        assert venue.recruitment_super_invitation

    def test_post_venue_request(self, client, selenium, request_page):
        
        venue = VenueRequest(client, 'openreview.net/Support', 'openreview.net')
        request_page(selenium, "http://localhost:3000/group?id=" + venue.support_group.id, client.token)

        header_div = selenium.find_element_by_id('header')
        assert header_div
        assert header_div.find_element_by_tag_name("h1").text == 'Host a Venue'

        request_invitation_div = selenium.find_element_by_id('invitation')
        assert request_invitation_div
        request_button_panel = request_invitation_div.find_element_by_tag_name('div')
        request_button = request_button_panel.find_element_by_class_name('btn')
        assert request_button.text == 'Support Request Form'

        request_button.click()

        request_form_div = selenium.find_element_by_class_name('note_editor')
        assert request_form_div
