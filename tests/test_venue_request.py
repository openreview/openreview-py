import openreview
import pytest
import time
from selenium.common.exceptions import NoSuchElementException
from venue_request import VenueRequest

class TestVenueRequest():

    def test_venue_request_setup(self, client):
        
        super_id = 'openreview.net'
        support_group_id = super_id + '/Support'
        venue = VenueRequest(client, support_group_id=support_group_id, super_user='openreview.net')

        assert venue.support_group.id == support_group_id
        assert venue.bid_stage_super_invitation
        assert venue.decision_stage_super_invitation
        assert venue.meta_review_stage_super_invitation
        assert venue.review_stage_super_invitation
        assert venue.meta_review_stage_super_invitation

        assert venue.deploy_super_invitation
        assert venue.comment_super_invitation
        assert venue.recruitment_super_invitation

    def test_venue_request_post_deploy_revise(self, client, selenium, request_page, helpers):
        
        super_id = 'openreview.net'
        support_group_id = super_id + '/Support'
        VenueRequest(client, support_group_id, super_id)
        
        time.sleep(5)
        request_page(selenium, 'http://localhost:3000/group?id={}&mode=default'.format(support_group_id), client.token)

        time.sleep(2)
        header_div = selenium.find_element_by_id('header')
        assert header_div
        assert header_div.find_element_by_tag_name("h1").text == 'Host a Venue'

        request_invitation_div = selenium.find_element_by_id('invitation')
        assert request_invitation_div
        request_button_panel = request_invitation_div.find_element_by_tag_name('div')
        request_button = request_button_panel.find_element_by_class_name('btn')
        assert request_button.text == 'Support Request Form'

        request_button.click()

        time.sleep(2)

        request_form_div = selenium.find_element_by_class_name('note_editor')
        assert request_form_div

        helpers.create_user('new_test_user@mail.com', 'Newtest', 'User')
        request_form_note = client.post_note(openreview.Note(
            invitation=support_group_id +'/-/Request_Form',
            signatures=['~Newtest_User1'],
            readers=[
                support_group_id,
                '~Newtest_User1',
                'new_test_user@mail.com',
                'tom@mail.com'
            ],
            writers=[],
            content={
                'title': 'Test 2021 Venue',
                'Official Venue Name': 'Test 2021 Venue',
                'Abbreviated Venue Name': 'TestVenue@OR2021',
                'Official Website URL': 'https://testvenue2021.gitlab.io/venue/',
                'program_chair_emails': [
                    'new_test_user@mail.com',
                    'tom@mail.com'],
                'contact_email': 'new_test_user@mail.com',
                'Area Chairs (Metareviewers)': 'No, our venue does not have Area Chairs',
                'Venue Start Date': '2020/02/01',
                'Submission Deadline': '2025/09/30',
                'Location': 'Virtual',
                'Paper Matching': [
                    'Reviewer Bid Scores',
                    'Reviewer Recommendation Scores'],
                'Author and Reviewer Anonymity': 'Single-blind (Reviewers are anonymous)',
                'Open Reviewing Policy': 'Submissions and reviews should both be private.',
                'Public Commentary': 'Yes, allow members of the public to comment non-anonymously.',
                'How did you hear about us?': 'ML conferences',
                'Expected Submissions': '100'
            }))
        
        assert request_form_note
        request_page(selenium, 'http://localhost:3000/forum?id=' + request_form_note.forum, client.token)

        # Test Deploy
        deploy_note = client.post_note(openreview.Note(
            content={'venue_id': 'TEST.cc/2021/Conference'},
            forum=request_form_note.forum,
            invitation='{}/-/Request{}/Deploy'.format(support_group_id, request_form_note.number),
            readers=[support_group_id],
            referent=request_form_note.forum,
            replyto=request_form_note.forum,
            signatures=[support_group_id],
            writers=['~Super_User1']
        ))
        assert deploy_note

        # Test Revision
        time.sleep(2)
        request_page(selenium, 'http://localhost:3000/group?id=TEST.cc/2021/Conference', client.token)
        header_div = selenium.find_element_by_id('header')
        assert header_div
        title_tag = header_div.find_element_by_tag_name('h1')
        assert title_tag
        assert title_tag.text == 'Test 2021 Venue'

        revision_note = client.post_note(openreview.Note(
            content={
                'title': 'Test 2021 Venue Updated',
                'Official Venue Name': 'Test 2021 Venue Updated',
                'Abbreviated Venue Name': 'TestVenue@OR2021',
                'Official Website URL': 'https://testvenue2021.gitlab.io/venue/',
                'program_chair_emails': [
                    'new_test_user@mail.com',
                    'tom@mail.com'],
                'Expected Submissions': '100',
                'How did you hear about us?': 'ML conferences',
                'Location': 'Virtual',
                'Submission Deadline': '2025/09/30',
                'Venue Start Date': '2020/02/01',
                'contact_email': 'new_test_user@mail.com',
                'remove_submission_options': []
            },
            forum=request_form_note.forum,
            invitation='{}/-/Request{}/Revision'.format(support_group_id, request_form_note.number),
            readers=['TEST.cc/2021/Conference/Program_Chairs', support_group_id],
            referent=request_form_note.forum,
            replyto=request_form_note.forum,
            signatures=['~Super_User1'],
            writers=['~Super_User1']
        ))
        assert revision_note

        time.sleep(2)
        request_page(selenium, 'http://localhost:3000/group?id=TEST.cc/2021/Conference', client.token)
        header_div = selenium.find_element_by_id('header')
        assert header_div
        title_tag = header_div.find_element_by_tag_name('h1')
        assert title_tag
        assert title_tag.text == 'Test 2021 Venue Updated'
