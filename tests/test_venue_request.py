import openreview
import pytest
import time
import datetime
from selenium.common.exceptions import NoSuchElementException
from openreview import VenueRequest

class TestVenueRequest():

    @pytest.fixture(scope="class")
    def venue(self, client, support_client, test_client):
        super_id = 'openreview.net'
        support_group_id = super_id + '/Support'
        VenueRequest(client, support_group_id, super_id)
        
        time.sleep(2)
        
        support_group = client.get_group(support_group_id)
        client.add_members_to_group(group=support_group, members=['~Support_User1'])

        now = datetime.datetime.utcnow()
        due_date = now + datetime.timedelta(minutes = 30)
        
        request_form_note = test_client.post_note(openreview.Note(
            invitation=support_group_id +'/-/Request_Form',
            signatures=['~Test_User1'],
            readers=[
                support_group_id,
                '~Test_User1',
                'test_user@mail.com',
                'tom@mail.com'
            ],
            writers=[],
            content={
                'title': 'Test 2030 Venue',
                'Official Venue Name': 'Test 2030 Venue',
                'Abbreviated Venue Name': 'TestVenue@OR2030',
                'Official Website URL': 'https://testvenue2030.gitlab.io/venue/',
                'program_chair_emails': [
                    'test_user@mail.com',
                    'tom@mail.com'],
                'contact_email': 'test_user@mail.com',
                'Area Chairs (Metareviewers)': 'Yes, our venue has Area Chairs',
                'Venue Start Date': now.strftime("%Y/%m/%d"),
                'Submission Deadline': due_date.strftime("%Y/%m/%d"),
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
        time.sleep(2)

        client.post_note(openreview.Note(
            content={'venue_id': 'TEST.cc/2030/Conference'},
            forum=request_form_note.forum,
            invitation='{}/-/Request{}/Deploy'.format(support_group_id, request_form_note.number),
            readers=[support_group_id],
            referent=request_form_note.forum,
            replyto=request_form_note.forum,
            signatures=[support_group_id],
            writers=['~Support_User1']
        ))

        venue_details = {
            'request_form_note': request_form_note,
            'support_group_id': support_group_id,
            'venue_id': 'TEST.cc/2030/Conference'
        }
        return venue_details

    def test_venue_setup(self, client):
        
        super_id = 'openreview.net'
        support_group_id = super_id + '/Support'
        venue = VenueRequest(client, support_group_id=support_group_id, super_user='openreview.net')

        assert venue.support_group.id == support_group_id
        assert venue.bid_stage_super_invitation
        assert venue.decision_stage_super_invitation
        assert venue.meta_review_stage_super_invitation
        assert venue.review_stage_super_invitation
        assert venue.meta_review_stage_super_invitation
        assert venue.submission_revision_invitation

        assert venue.deploy_super_invitation
        assert venue.comment_super_invitation
        assert venue.recruitment_super_invitation

    def test_venue_deployment(self, client, selenium, request_page, helpers, support_client):
        
        super_id = 'openreview.net'
        support_group_id = super_id + '/Support'
        VenueRequest(client, support_group_id, super_id)
        
        time.sleep(2)
        request_page(selenium, 'http://localhost:3000/group?id={}&mode=default'.format(support_group_id), client.token)

        helpers.create_user('new_test_user@mail.com', 'Newtest', 'User')

        support_group = client.get_group(support_group_id)
        client.add_members_to_group(group=support_group, members=['~Support_User1'])

        support_members = client.get_group(support_group_id).members
        assert support_members and len(support_members) == 1
        
        now = datetime.datetime.utcnow()
        due_date = now + datetime.timedelta(minutes = 30)
        
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
                'Venue Start Date': now.strftime("%Y/%m/%d"),
                'Submission Deadline': due_date.strftime("%Y/%m/%d"),
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

        messages = client.get_messages(
            to='new_test_user@mail.com',
            subject='Your request for OpenReview service has been received.')
        assert messages and len(messages) == 1
        assert messages[0]['content']['text'] == 'Thank you for choosing OpenReview to host your upcoming venue. We are reviewing your request and will post a comment on the request forum when the venue is deployed. You can access the request forum here: https://openreview.net/forum?id=' + request_form_note.forum

        messages = client.get_messages(
            to='support_user@mail.com',
            subject='A request for service has been submitted'
        )
        assert messages and len(messages) == 1
        assert messages[0]['content']['text'].startswith('A request for service has been submitted. Check it here')

        # Test Deploy
        deploy_note = client.post_note(openreview.Note(
            content={'venue_id': 'TEST.cc/2021/Conference'},
            forum=request_form_note.forum,
            invitation='{}/-/Request{}/Deploy'.format(support_group_id, request_form_note.number),
            readers=[support_group_id],
            referent=request_form_note.forum,
            replyto=request_form_note.forum,
            signatures=[support_group_id],
            writers=['~Support_User1']
        ))
        assert deploy_note

        time.sleep(2)
        process_logs = client.get_process_logs(id = deploy_note.id)
        assert len(process_logs) == 1
        assert process_logs[0]['status'] == 'ok'
        assert process_logs[0]['invitation'] == '{}/-/Request{}/Deploy'.format(support_group_id, request_form_note.number)

    def test_venue_revision(self, client, test_client, selenium, request_page, helpers, venue):

        # Test Revision
        request_page(selenium, 'http://localhost:3000/group?id={}'.format(venue['venue_id']), test_client.token)
        header_div = selenium.find_element_by_id('header')
        assert header_div
        title_tag = header_div.find_element_by_tag_name('h1')
        assert title_tag
        assert title_tag.text == venue['request_form_note'].content['title']

        messages = client.get_messages(subject='Comment posted to your request for service: {}'.format(venue['request_form_note'].content['title']))
        assert messages and len(messages) == 2
        recipients = [msg['content']['to'] for msg in messages]
        assert 'test_user@mail.com' in recipients
        assert 'tom@mail.com' in recipients

        now = datetime.datetime.utcnow()
        due_date = now + datetime.timedelta(minutes = 30)

        revision_note = test_client.post_note(openreview.Note(
            content={
                'title': '{} Updated'.format(venue['request_form_note'].content['title']),
                'Official Venue Name': '{} Updated'.format(venue['request_form_note'].content['title']),
                'Abbreviated Venue Name': venue['request_form_note'].content['Abbreviated Venue Name'],
                'Official Website URL': venue['request_form_note'].content['Official Website URL'],
                'program_chair_emails': venue['request_form_note'].content['program_chair_emails'],
                'Expected Submissions': '100',
                'How did you hear about us?': 'ML conferences',
                'Location': 'Virtual',
                'Submission Deadline': due_date.strftime("%Y/%m/%d"),
                'Venue Start Date': now.strftime("%Y/%m/%d"),
                'contact_email': venue['request_form_note'].content['contact_email'],
                'remove_submission_options': []
            },
            forum=venue['request_form_note'].forum,
            invitation='{}/-/Request{}/Venue_Revision'.format(venue['support_group_id'], venue['request_form_note'].number),
            readers=['{}/Program_Chairs'.format(venue['venue_id']), venue['support_group_id']],
            referent=venue['request_form_note'].forum,
            replyto=venue['request_form_note'].forum,
            signatures=['~Test_User1'],
            writers=['~Test_User1']
        ))
        assert revision_note

        time.sleep(2)
        process_logs = client.get_process_logs(id = revision_note.id)
        assert len(process_logs) == 1
        assert process_logs[0]['status'] == 'ok'
        assert process_logs[0]['invitation'] == '{}/-/Request{}/Venue_Revision'.format(venue['support_group_id'], venue['request_form_note'].number)

        request_page(selenium, 'http://localhost:3000/group?id={}'.format(venue['venue_id']), test_client.token)
        header_div = selenium.find_element_by_id('header')
        assert header_div
        title_tag = header_div.find_element_by_tag_name('h1')
        assert title_tag
        assert title_tag.text == '{} Updated'.format(venue['request_form_note'].content['title'])

    def test_venue_bid_stage(self, client, test_client, selenium, request_page, helpers, venue):

        reviewer_client = helpers.create_user('venue_reviewer1@mail.com', 'Venue', 'Reviewer')

        reviewer_group_id = '{}/Reviewers'.format(venue['venue_id'])
        reviewer_group = client.get_group(reviewer_group_id)
        client.add_members_to_group(reviewer_group, '~Venue_Reviewer1')

        reviewer_url = 'http://localhost:3000/group?id={}#reviewer-tasks'.format(reviewer_group_id)
        request_page(selenium, reviewer_url, reviewer_client.token)
        with pytest.raises(NoSuchElementException):
            assert selenium.find_element_by_link_text('Reviewer Bid')

        now = datetime.datetime.utcnow()
        due_date = now + datetime.timedelta(days = 3)

        bid_revision_note = test_client.post_note(openreview.Note(
            content={
                'bid_start_date': now.strftime("%Y/%m/%d"),
                'bid_due_date': due_date.strftime("%Y/%m/%d")
            },
            forum=venue['request_form_note'].forum,
            replyto=venue['request_form_note'].forum,
            referent=venue['request_form_note'].forum,
            invitation='{}/-/Request{}/Bid_Stage'.format(venue['support_group_id'], venue['request_form_note'].number),
            readers=['{}/Program_Chairs'.format(venue['venue_id']), venue['support_group_id']],
            signatures=['~Test_User1'],
            writers=['~Test_User1']
        ))
        assert bid_revision_note

        time.sleep(2)
        process_logs = client.get_process_logs(id=bid_revision_note.id)
        assert len(process_logs) == 1
        assert process_logs[0]['invitation'] == '{}/-/Request{}/Bid_Stage'.format(venue['support_group_id'], venue['request_form_note'].number)
        assert process_logs[0]['status'] == 'ok'

        request_page(selenium, reviewer_url, reviewer_client.token)
        assert selenium.find_element_by_link_text('Reviewer Bid')
