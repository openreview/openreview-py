import json
import re

import openreview
from openreview import venue_request
import pytest
import time
import datetime
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from openreview import VenueRequest
import csv
import os
import random

class TestVenueRequest():

    @pytest.fixture(scope='class')
    def venue(self, client, test_client, helpers):
        super_id = 'openreview.net'
        support_group_id = super_id + '/Support'
        VenueRequest(client, support_group_id, super_id)

        helpers.await_queue()

        # Add support group user to the support group object
        support_group = client.get_group(support_group_id)
        client.add_members_to_group(group=support_group, members=['~Support_User1'])

        now = datetime.datetime.utcnow()
        due_date = now + datetime.timedelta(days=3)
        withdraw_exp_date = due_date + datetime.timedelta(days=1)

        # Post the request form note
        request_form_note = openreview.Note(
            invitation=support_group_id +'/-/Request_Form',
            signatures=['~SomeFirstName_User1'],
            readers=[
                support_group_id,
                '~SomeFirstName_User1',
                'test@mail.com',
                'tom@mail.com'
            ],
            writers=[],
            content={
                'title': "Test 2030' Venue",
                'Official Venue Name': "Test 2030' Venue",
                'Abbreviated Venue Name': "TestVenue@OR'2030",
                'Official Website URL': 'https://testvenue2030.gitlab.io/venue/',
                'program_chair_emails': [
                    'test@mail.com',
                    'tom@mail.com'],
                'contact_email': 'test@mail.com',
                'Area Chairs (Metareviewers)': 'Yes, our venue has Area Chairs',
                'senior_area_chairs': 'Yes, our venue has Senior Area Chairs',
                'Venue Start Date': now.strftime('%Y/%m/%d'),
                'Submission Deadline': due_date.strftime('%Y/%m/%d'),
                'Location': 'Virtual',
                'Paper Matching': [
                    'Reviewer Bid Scores',
                    'Reviewer Recommendation Scores'],
                'Author and Reviewer Anonymity': 'Double-blind',
                'Open Reviewing Policy': 'Submissions and reviews should both be private.',
                'submission_readers': 'Assigned program committee (assigned reviewers, assigned area chairs, assigned senior area chairs if applicable)',
                'How did you hear about us?': 'ML conferences',
                'Expected Submissions': '100',
                'email_pcs_for_new_submissions': 'Yes, email PCs for every new submission.',
                'reviewer_identity': ['Program Chairs'],
                'area_chair_identity': ['Program Chairs', 'Assigned Senior Area Chair', 'Assigned Area Chair'],
                'senior_area_chair_identity': ['Program Chairs', 'Assigned Senior Area Chair'],
                'withdraw_submission_expiration': withdraw_exp_date.strftime('%Y/%m/%d'),
                'use_recruitment_template': 'No'
            })

        with pytest.raises(openreview.OpenReviewException, match=r'Assigned area chairs must see the reviewer identity'):
            request_form_note=test_client.post_note(request_form_note)

        request_form_note.content['reviewer_identity'] = ['Program Chairs', 'Assigned Area Chair', 'Assigned Senior Area Chair']

        with pytest.raises(openreview.OpenReviewException, match=r'Papers should be visible to all program committee if bidding is enabled'):
            request_form_note=test_client.post_note(request_form_note)

        request_form_note.content['submission_readers'] = 'All program committee (all reviewers, all area chairs, all senior area chairs if applicable)'
        request_form_note=test_client.post_note(request_form_note)

        helpers.await_queue()

        # Post a deploy note
        client.post_note(openreview.Note(
            content={'venue_id': 'TEST.cc/2030/Conference'},
            forum=request_form_note.forum,
            invitation='{}/-/Request{}/Deploy'.format(support_group_id, request_form_note.number),
            readers=[support_group_id],
            referent=request_form_note.forum,
            replyto=request_form_note.forum,
            signatures=[support_group_id],
            writers=[support_group_id]
        ))

        # Return venue details as a dict
        venue_details = {
            'request_form_note': request_form_note,
            'support_group_id': support_group_id,
            'venue_id': 'TEST.cc/2030/Conference'
        }
        return venue_details

    def test_venue_setup(self, client, helpers):

        super_id = 'openreview.net'
        support_group_id = super_id + '/Support'
        venue = VenueRequest(client, support_group_id=support_group_id, super_user='openreview.net')

        assert venue.support_group.id == support_group_id
        assert venue.bid_stage_super_invitation
        assert venue.decision_stage_super_invitation
        assert venue.meta_review_stage_super_invitation
        assert venue.review_stage_super_invitation
        assert venue.submission_revision_stage_super_invitation
        assert venue.comment_stage_super_invitation

        assert venue.deploy_super_invitation
        assert venue.comment_super_invitation
        assert venue.recruitment_super_invitation
        assert venue.venue_revision_invitation
        assert venue.matching_setup_super_invitation
        assert venue.matching_status_super_invitation
        assert venue.recruitment_status_process
        assert venue.error_status_super_invitation

    def test_venue_deployment(self, client, selenium, request_page, helpers):

        super_id = 'openreview.net'
        support_group_id = super_id + '/Support'
        venue = VenueRequest(client, support_group_id, super_id)

        helpers.await_queue()
        request_page(selenium, 'http://localhost:3030/group?id={}&mode=default'.format(support_group_id), client.token)
        header_div = selenium.find_element_by_id('header')
        assert header_div
        title_tag = header_div.find_element_by_tag_name('h1')
        assert title_tag
        assert title_tag.text == 'Host a Venue'

        pc_client = helpers.create_user('new_test_user@mail.com', 'NewFirstName', 'User')

        support_group = client.get_group(support_group_id)
        client.add_members_to_group(group=support_group, members=['~Support_User1'])

        support_members = client.get_group(support_group_id).members
        assert support_members and len(support_members) == 1

        now = datetime.datetime.utcnow()
        start_date = now - datetime.timedelta(days=2)
        abstract_due_date = now + datetime.timedelta(minutes=15)
        due_date = now + datetime.timedelta(minutes=30)
        withdraw_exp_date = now + datetime.timedelta(hours=1)

        request_form_note = pc_client.post_note(openreview.Note(
            invitation=support_group_id +'/-/Request_Form',
            signatures=['~NewFirstName_User1'],
            readers=[
                support_group_id,
                '~NewFirstName_User1',
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
                'Venue Start Date': start_date.strftime('%Y/%m/%d'),
                'abstract_registration_deadline': abstract_due_date.strftime('%Y/%m/%d %H:%M'),
                'Submission Deadline': due_date.strftime('%Y/%m/%d %H:%M'),
                'Location': 'Virtual',
                'Paper Matching': [
                    'Reviewer Bid Scores',
                    'Reviewer Recommendation Scores'],
                'Author and Reviewer Anonymity': 'Single-blind (Reviewers are anonymous)',
                'Open Reviewing Policy': 'Submissions and reviews should both be private.',
                'submission_readers': 'All program committee (all reviewers, all area chairs, all senior area chairs if applicable)',
                'withdraw_submission_expiration': withdraw_exp_date.strftime('%Y/%m/%d'),
                'withdrawn_submissions_visibility': 'No, withdrawn submissions should not be made public.',
                'withdrawn_submissions_author_anonymity': 'Yes, author identities of withdrawn submissions should be revealed.',
                'email_pcs_for_withdrawn_submissions': 'Yes, email PCs.',
                'desk_rejected_submissions_visibility': 'No, desk rejected submissions should not be made public.',
                'desk_rejected_submissions_author_anonymity': 'Yes, author identities of desk rejected submissions should be revealed.',
                'How did you hear about us?': 'ML conferences',
                'Expected Submissions': '100',
                'submission_name': 'Submission_Test'
            }))

        assert request_form_note
        request_page(selenium, 'http://localhost:3030/forum?id=' + request_form_note.forum, client.token)

        messages = client.get_messages(
            to='new_test_user@mail.com',
            subject='Your request for OpenReview service has been received.')
        assert messages and len(messages) == 1
        assert messages[0]['content']['text'] == f'Thank you for choosing OpenReview to host your upcoming venue. We are reviewing your request and will post a comment on the request forum when the venue is deployed. You can access the request forum here: https://openreview.net/forum?id={request_form_note.forum}'

        messages = client.get_messages(
            to='support@openreview.net',
            subject='A request for service has been submitted by TestVenue@OR2021'
        )
        assert messages and len(messages) == 1
        assert messages[0]['content']['text'].startswith(f'A request for service has been submitted by TestVenue@OR2021. Check it here: https://openreview.net/forum?id={request_form_note.forum}')

        pc_client.post_note(openreview.Note(
            content={
                'title': 'Urgent',
                'comment': 'Please deploy ASAP.'
            },
            forum=request_form_note.forum,
            invitation='{}/-/Request{}/Comment'.format(venue.support_group_id, request_form_note.number),
            readers=[
                support_group_id,
                'new_test_user@mail.com',
                'tom@mail.com'
            ],
            replyto=None,
            signatures=['~NewFirstName_User1'],
            writers=[]
        ))

        helpers.await_queue()

        request_form_note.content['program_chair_emails'] = ['new_test_user@mail.com', 'tom@mail.com', 'test@mail.com']
        client.post_note(request_form_note)

        helpers.await_queue()

        messages = client.get_messages(
            to='new_test_user@mail.com',
            subject='Your request for OpenReview service has been received.')
        assert messages and len(messages) == 1

        messages = client.get_messages(
            to='support@openreview.net',
            subject='A request for service has been submitted by TestVenue@OR2021'
        )
        assert messages and len(messages) == 1

        comment_invitation = pc_client.get_invitation(id='openreview.net/Support/-/Request{number}/Comment'.format(number=request_form_note.number))
        assert 'test@mail.com' in comment_invitation.reply['readers']['values']

        # Test Deploy
        deploy_note = client.post_note(openreview.Note(
            content={'venue_id': 'TEST.cc/2021/Conference'},
            forum=request_form_note.forum,
            invitation='{}/-/Request{}/Deploy'.format(support_group_id, request_form_note.number),
            readers=[support_group_id],
            referent=request_form_note.forum,
            replyto=request_form_note.forum,
            signatures=[support_group_id],
            writers=[support_group_id]
        ))
        assert deploy_note

        helpers.await_queue()
        process_logs = client.get_process_logs(id=deploy_note.id)
        assert len(process_logs) == 1
        assert process_logs[0]['status'] == 'ok'
        assert process_logs[0]['invitation'] == '{}/-/Request{}/Deploy'.format(support_group_id, request_form_note.number)

        assert openreview.tools.get_invitation(pc_client, 'TEST.cc/2021/Conference/-/Submission_Test')
        assert not openreview.tools.get_invitation(pc_client, 'TEST.cc/2021/Conference/-/Submission')

        assert pc_client.get_notes(invitation='openreview.net/Support/-/Request{number}/Comment'.format(number=request_form_note.number))
        
        conference = openreview.get_conference(pc_client, request_form_id=request_form_note.forum)
        submission_due_date_str = due_date.strftime('%b %d %Y %I:%M%p')
        abstract_due_date_str = abstract_due_date.strftime('%b %d %Y %I:%M%p')
        assert conference.homepage_header['deadline'] == 'Submission Start:  UTC-0, Abstract Registration: ' + abstract_due_date_str + ' UTC-0, End: ' + submission_due_date_str + ' UTC-0'
        assert conference.get_submission_id() == 'TEST.cc/2021/Conference/-/Submission_Test'

        comment_invitation = '{}/-/Request{}/Comment'.format(venue.support_group_id,
                                                             request_form_note.number)
        last_comment = client.get_notes(invitation=comment_invitation, sort='tmdate')[-1]
        assert 'TEST.cc/2021/Conference/Program_Chairs' in last_comment.readers

        #test revision pre-process

        venue_revision_note = openreview.Note(
        content={
            'title': '{} Updated'.format(request_form_note.content['title']),
            'Official Venue Name': '{} Updated'.format(request_form_note.content['title']),
            'Abbreviated Venue Name': request_form_note.content['Abbreviated Venue Name'],
            'Official Website URL': request_form_note.content['Official Website URL'],
            'program_chair_emails': request_form_note.content['program_chair_emails'],
            'Expected Submissions': '100',
            'How did you hear about us?': 'ML conferences',
            'Location': 'Virtual',
            'Submission Deadline': request_form_note.content['Submission Deadline'],
            'Venue Start Date': request_form_note.content['Venue Start Date'],
            'contact_email': request_form_note.content['contact_email'],
            'email_pcs_for_new_submissions': 'Yes, email PCs for every new submission.',
            'desk_rejected_submissions_author_anonymity': 'No, author identities of desk rejected submissions should not be revealed.',

        },
        forum=request_form_note.forum,
        invitation='{}/-/Request{}/Revision'.format(support_group_id, request_form_note.number),
        readers=['{}/Program_Chairs'.format(deploy_note.content['venue_id']), support_group_id],
        referent=request_form_note.forum,
        replyto=request_form_note.forum,
        signatures=['~NewFirstName_User1'],
        writers=[]
        )

        with pytest.raises(openreview.OpenReviewException, match=r'Author identities of desk-rejected submissions can only be anonymized for double-blind submissions'):
            pc_client.post_note(venue_revision_note)

        venue_revision_note.content['desk_rejected_submissions_author_anonymity'] = 'Yes, author identities of desk rejected submissions should be revealed.'
        venue_revision_note=pc_client.post_note(venue_revision_note)

    def test_venue_revision_error(self, client, test_client, selenium, request_page, venue, helpers):

        # Test Revision
        request_page(selenium, 'http://localhost:3030/group?id={}'.format(venue['venue_id']), test_client.token, wait_for_element='header')
        header_div = selenium.find_element_by_id('header')
        assert header_div
        title_tag = header_div.find_element_by_tag_name('h1')
        assert title_tag
        assert title_tag.text == venue['request_form_note'].content['title']

        messages = client.get_messages(subject='Comment posted to your request for service: {}'.format(venue['request_form_note'].content['title']))
        assert messages and len(messages) == 2
        recipients = [msg['content']['to'] for msg in messages]
        assert 'test@mail.com' in recipients
        assert 'tom@mail.com' in recipients
        assert 'Venue home page: https://openreview.net/group?id=TEST.cc/2030/Conference' in messages[0]['content']['text']
        assert 'Venue Program Chairs console: https://openreview.net/group?id=TEST.cc/2030/Conference/Program_Chairs' in messages[0]['content']['text']

        now = datetime.datetime.utcnow()
        start_date = now - datetime.timedelta(days=2)
        due_date = now + datetime.timedelta(days=3)

        venue_revision_note = test_client.post_note(openreview.Note(
            content={
                'title': '{} Updated'.format(venue['request_form_note'].content['title']),
                'Official Venue Name': '{} Updated'.format(venue['request_form_note'].content['title']),
                'Abbreviated Venue Name': venue['request_form_note'].content['Abbreviated Venue Name'],
                'Official Website URL': venue['request_form_note'].content['Official Website URL'],
                'program_chair_emails': venue['request_form_note'].content['program_chair_emails'],
                'Expected Submissions': '100',
                'How did you hear about us?': 'ML conferences',
                'Location': 'Virtual',
                'Submission Deadline': due_date.strftime('%Y/%m/%d %H:%M'),
                'Venue Start Date': start_date.strftime('%Y/%m/%d'),
                'contact_email': venue['request_form_note'].content['contact_email'],
                'remove_submission_options': ['pdf'],
                'email_pcs_for_new_submissions': 'Yes, email PCs for every new submission.',
                'Additional Submission Options': {
                    'preprint': {
                        'value-regexx': '.*'
                    }
                }
            },
            forum=venue['request_form_note'].forum,
            invitation='{}/-/Request{}/Revision'.format(venue['support_group_id'], venue['request_form_note'].number),
            readers=['{}/Program_Chairs'.format(venue['venue_id']), venue['support_group_id']],
            referent=venue['request_form_note'].forum,
            replyto=venue['request_form_note'].forum,
            signatures=['~SomeFirstName_User1'],
            writers=[]
        ))
        assert venue_revision_note

        helpers.await_queue()
        process_logs = client.get_process_logs(id=venue_revision_note.id)
        assert len(process_logs) == 1
        assert process_logs[0]['status'] == 'ok'
        assert process_logs[0]['invitation'] == '{}/-/Request{}/Revision'.format(venue['support_group_id'], venue['request_form_note'].number)

        comment_invitation = '{}/-/Request{}/Stage_Error_Status'.format(venue['support_group_id'],
                                                             venue['request_form_note'].number)
        last_comment = client.get_notes(invitation=comment_invitation, sort='tmdate')[0]
        error = last_comment.content['error']
        assert 'InvalidFieldError' in error
        assert 'The field value-regexx is not allowed' in error

    def test_venue_revision(self, client, test_client, selenium, request_page, venue, helpers):

        # Test Revision
        request_page(selenium, 'http://localhost:3030/group?id={}'.format(venue['venue_id']), test_client.token, wait_for_element='header')
        header_div = selenium.find_element_by_id('header')
        assert header_div
        title_tag = header_div.find_element_by_tag_name('h1')
        assert title_tag
        assert title_tag.text == venue['request_form_note'].content['title']

        messages = client.get_messages(subject='Comment posted to your request for service: {}'.format(venue['request_form_note'].content['title']))
        assert messages and len(messages) == 2
        recipients = [msg['content']['to'] for msg in messages]
        assert 'test@mail.com' in recipients
        assert 'tom@mail.com' in recipients
        assert 'Venue home page: https://openreview.net/group?id=TEST.cc/2030/Conference' in messages[0]['content']['text']
        assert 'Venue Program Chairs console: https://openreview.net/group?id=TEST.cc/2030/Conference/Program_Chairs' in messages[0]['content']['text']

        now = datetime.datetime.utcnow()
        start_date = now - datetime.timedelta(days=2)
        due_date = now + datetime.timedelta(days=3)

        venue_revision_note = test_client.post_note(openreview.Note(
            content={
                'title': '{} Updated'.format(venue['request_form_note'].content['title']),
                'Official Venue Name': '{} Updated'.format(venue['request_form_note'].content['title']),
                'Abbreviated Venue Name': venue['request_form_note'].content['Abbreviated Venue Name'],
                'Official Website URL': venue['request_form_note'].content['Official Website URL'],
                'program_chair_emails': venue['request_form_note'].content['program_chair_emails'],
                'Expected Submissions': '100',
                'How did you hear about us?': 'ML conferences',
                'Location': 'Virtual',
                'Submission Deadline': due_date.strftime('%Y/%m/%d %H:%M'),
                'Venue Start Date': start_date.strftime('%Y/%m/%d'),
                'contact_email': venue['request_form_note'].content['contact_email'],
                'remove_submission_options': ['pdf'],
                'email_pcs_for_new_submissions': 'Yes, email PCs for every new submission.',
                'Additional Submission Options': {
                    'preprint': {
                        'value-regex': '.*'
                    }
                },
                'submission_email': 'Your submission to {{Abbreviated_Venue_Name}} has been {{action}}.\n\nSubmission Number: {{note_number}}\n\nTitle: {{note_title}} {{note_abstract}}\n\nTo view your submission, click here: https://openreview.net/forum?id={{note_forum}}\n\nThis is some extra information to be added at the end of the email template.',
                'reviewer_roles': ['Reviewers', 'Expert_Reviewers']
            },
            forum=venue['request_form_note'].forum,
            invitation='{}/-/Request{}/Revision'.format(venue['support_group_id'], venue['request_form_note'].number),
            readers=['{}/Program_Chairs'.format(venue['venue_id']), venue['support_group_id']],
            referent=venue['request_form_note'].forum,
            replyto=venue['request_form_note'].forum,
            signatures=['~SomeFirstName_User1'],
            writers=[]
        ))
        assert venue_revision_note

        helpers.await_queue()
        process_logs = client.get_process_logs(id=venue_revision_note.id)
        assert len(process_logs) == 1
        assert process_logs[0]['status'] == 'ok'
        assert process_logs[0]['invitation'] == '{}/-/Request{}/Revision'.format(venue['support_group_id'], venue['request_form_note'].number)

        request_page(selenium, 'http://localhost:3030/group?id={}'.format(venue['venue_id']), test_client.token, wait_for_element='header')
        header_div = selenium.find_element_by_id('header')
        assert header_div
        title_tag = header_div.find_element_by_tag_name('h1')
        assert title_tag
        assert title_tag.text == '{} Updated'.format(venue['request_form_note'].content['title'])

        conference = openreview.get_conference(client, request_form_id=venue['request_form_note'].forum)
        submission_due_date_str = due_date.strftime('%b %d %Y %I:%M%p')
        assert conference.homepage_header['deadline'] == 'Submission Start:  UTC-0, End: ' + submission_due_date_str + ' UTC-0'
        assert openreview.tools.get_invitation(client, conference.submission_stage.get_withdrawn_submission_id(conference)) is None

    def test_multiple_reviewer_roles(self, client, test_client, selenium, request_page, venue, helpers):
        conference = openreview.get_conference(client, request_form_id=venue['request_form_note'].forum)

        recruitment_invitation = client.get_invitation('{}/-/Request{}/Recruitment'.format(venue['support_group_id'], venue['request_form_note'].number))
        assert 'Expert_Reviewers' in recruitment_invitation.reply['content']['invitee_role']['value-dropdown']

        remind_recruitment_invitation = client.get_invitation('{}/-/Request{}/Remind_Recruitment'.format(venue['support_group_id'], venue['request_form_note'].number))
        assert 'Expert_Reviewers' in remind_recruitment_invitation.reply['content']['invitee_role']['value-dropdown']

        paper_matching_invitaion = client.get_invitation('{}/-/Request{}/Paper_Matching_Setup'.format(venue['support_group_id'], venue['request_form_note'].number))
        assert conference.get_committee_id('Expert_Reviewers') in paper_matching_invitaion.reply['content']['matching_group']['value-dropdown']

    def test_venue_recruitment_email_error(self, client, test_client, selenium, request_page, venue, helpers):

        # Test Reviewer Recruitment
        request_page(selenium, 'http://localhost:3030/forum?id={}'.format(venue['request_form_note'].id), test_client.token, wait_for_element=f"note_{venue['request_form_note'].id}")
        recruitment_div = selenium.find_element_by_id('note_{}'.format(venue['request_form_note'].id))
        assert recruitment_div
        reply_row = recruitment_div.find_element_by_class_name('reply_row')
        assert reply_row
        buttons = reply_row.find_elements_by_class_name('btn-xs')
        assert [btn for btn in buttons if btn.text == 'Recruitment']
        reviewer_details = '''(reviewer_candidate1@email.com, Reviewer One)\nreviewer_candidate2@email.com, Reviewer Two\n '''
        recruitment_note = test_client.post_note(openreview.Note(
            content={
                'title': 'Recruitment',
                'invitee_role': 'Reviewers',
                'invitee_details': reviewer_details,
                'invitation_email_subject': '[' + venue['request_form_note'].content['Abbreviated Venue Name'] + '] Invitation to serve as {{invitee_role}}',
                'invitation_email_content': 'Dear {{fullname}},\n\nYou have been nominated by the {program} chair committee of Theoretical Foundations of RL Workshop @ ICML 2020 to serve as {{invitee_role}}.\n\nACCEPT LINK:\n\n{{accept_url}}\n\nDECLINE LINK:\n\n{{decline_url}}\n\nCheers!\n\nProgram Chairs'
            },
            forum=venue['request_form_note'].forum,
            replyto=venue['request_form_note'].forum,
            invitation='{}/-/Request{}/Recruitment'.format(venue['support_group_id'], venue['request_form_note'].number),
            readers=['{}/Program_Chairs'.format(venue['venue_id']), venue['support_group_id']],
            signatures=['~SomeFirstName_User1'],
            writers=[]
        ))
        assert recruitment_note

        invite = client.get_invitation('{}/-/Request{}/Recruitment'.format(venue['support_group_id'], venue['request_form_note'].number))

        assert invite.reply['content']['invitee_details']['description'] == 'Enter a list of invitees with one per line. Either tilde IDs (∼Captain_America1), emails (captain_rogers@marvel.com), or email,name pairs (captain_rogers@marvel.com, Captain America) expected. If only an email address is provided for an invitee, the recruitment email is addressed to "Dear invitee". Do not use parentheses in your list of invitees.'

        helpers.await_queue()
        process_logs = client.get_process_logs(id=recruitment_note.id)
        assert len(process_logs) == 1
        assert process_logs[0]['status'] == 'ok'
        assert process_logs[0]['invitation'] == '{}/-/Request{}/Recruitment'.format(venue['support_group_id'], venue['request_form_note'].number)

        messages = client.get_messages(to='reviewer_candidate1@email.com')
        assert not messages
        messages = client.get_messages(to='reviewer_candidate2@email.com')
        assert not messages

        recruitment_status_invitation = '{}/-/Request{}/Recruitment_Status'.format(venue['support_group_id'],
                                                             venue['request_form_note'].number)
        last_comment = client.get_notes(invitation=recruitment_status_invitation, sort='tmdate')[0]
        error_string = '{\n ' \
                       ' "KeyError(\'program\')": [\n' \
                       '    "reviewer_candidate1@email.com",\n' \
                       '    "reviewer_candidate2@email.com"\n' \
                       '  ]\n' \
                       '}'
        assert error_string in last_comment.content['error']
        assert '0 users' in last_comment.content['invited']

    def test_venue_recruitment(self, client, test_client, selenium, request_page, venue, helpers):

        # Test Reviewer Recruitment
        request_page(selenium, 'http://localhost:3030/forum?id={}'.format(venue['request_form_note'].id), test_client.token, wait_for_element=f"note_{venue['request_form_note'].id}")
        recruitment_div = selenium.find_element_by_id('note_{}'.format(venue['request_form_note'].id))
        assert recruitment_div
        reply_row = recruitment_div.find_element_by_class_name('reply_row')
        assert reply_row
        buttons = reply_row.find_elements_by_class_name('btn-xs')
        assert [btn for btn in buttons if btn.text == 'Recruitment']
        reviewer_details = '''reviewer_candidate1@email.com, Reviewer One\nreviewer_candidate2@email.com, Reviewer Two'''
        recruitment_note = test_client.post_note(openreview.Note(
            content={
                'title': 'Recruitment',
                'invitee_role': 'Reviewers',
                'invitee_details': reviewer_details,
                'invitation_email_subject': '[' + venue['request_form_note'].content['Abbreviated Venue Name'] + '] Invitation to serve as {{invitee_role}}',
                'invitation_email_content': 'Dear {{fullname}},\n\nYou have been nominated by the program chair committee of Theoretical Foundations of RL Workshop @ ICML 2020 to serve as {{invitee_role}}.\n\nACCEPT LINK:\n\n{{accept_url}}\n\nDECLINE LINK:\n\n{{decline_url}}\n\nCheers!\n\nProgram Chairs'
            },
            forum=venue['request_form_note'].forum,
            replyto=venue['request_form_note'].forum,
            invitation='{}/-/Request{}/Recruitment'.format(venue['support_group_id'], venue['request_form_note'].number),
            readers=['{}/Program_Chairs'.format(venue['venue_id']), venue['support_group_id']],
            signatures=['~SomeFirstName_User1'],
            writers=[]
        ))
        assert recruitment_note

        invite = client.get_invitation('{}/-/Request{}/Recruitment'.format(venue['support_group_id'], venue['request_form_note'].number))

        assert invite.reply['content']['invitee_details']['description'] == 'Enter a list of invitees with one per line. Either tilde IDs (∼Captain_America1), emails (captain_rogers@marvel.com), or email,name pairs (captain_rogers@marvel.com, Captain America) expected. If only an email address is provided for an invitee, the recruitment email is addressed to "Dear invitee". Do not use parentheses in your list of invitees.'

        helpers.await_queue()
        process_logs = client.get_process_logs(id=recruitment_note.id)
        assert len(process_logs) == 1
        assert process_logs[0]['status'] == 'ok'
        assert process_logs[0]['invitation'] == '{}/-/Request{}/Recruitment'.format(venue['support_group_id'], venue['request_form_note'].number)

        messages = client.get_messages(to='reviewer_candidate1@email.com')
        assert messages and len(messages) == 1
        assert messages[0]['content']['subject'] == "[TestVenue@OR'2030] Invitation to serve as Reviewer"
        assert messages[0]['content']['text'].startswith('Dear Reviewer One,\n\nYou have been nominated by the program chair committee of Theoretical Foundations of RL Workshop @ ICML 2020 to serve as Reviewer.')
        assert "TEST.cc/2030/Conference/-/Recruit_Reviewers" in messages[0]['content']['text']

        messages = client.get_messages(to='reviewer_candidate2@email.com')
        assert messages and len(messages) == 1
        assert messages[0]['content']['subject'] == "[TestVenue@OR'2030] Invitation to serve as Reviewer"
        assert messages[0]['content']['text'].startswith('Dear Reviewer Two,\n\nYou have been nominated by the program chair committee of Theoretical Foundations of RL Workshop @ ICML 2020 to serve as Reviewer.')

        recruitment_status_invitation = '{}/-/Request{}/Recruitment_Status'.format(venue['support_group_id'],
                                                                                   venue['request_form_note'].number)
        last_comment = client.get_notes(invitation=recruitment_status_invitation, sort='tmdate')[0]
        assert '2 users' in last_comment.content['invited']

        last_message = client.get_messages(to='support@openreview.net')[-1]
        assert 'Recruitment Status' not in last_message['content']['text']
    
    def test_venue_recruitment_tilde_IDs(self, client, test_client, selenium, request_page, venue, helpers):

        # Test Reviewer Recruitment
        request_page(selenium, 'http://localhost:3030/forum?id={}'.format(venue['request_form_note'].id), test_client.token, wait_for_element=f"note_{venue['request_form_note'].id}")
        recruitment_div = selenium.find_element_by_id('note_{}'.format(venue['request_form_note'].id))
        assert recruitment_div
        reply_row = recruitment_div.find_element_by_class_name('reply_row')
        assert reply_row
        buttons = reply_row.find_elements_by_class_name('btn-xs')
        assert [btn for btn in buttons if btn.text == 'Recruitment']
        helpers.create_user('reviewer_one_tilde@mail.com', 'Reviewer', 'OneTilde')
        helpers.create_user('reviewer_two_tilde@mail.com', 'Reviewer', 'TwoTilde')
        reviewer_details = '''~Reviewer_OneTilde1\n~Reviewer_TwoTilde1'''

        recruitment_note = test_client.post_note(openreview.Note(
            content={
                'title': 'Recruitment',
                'invitee_role': 'Reviewers',
                'invitee_details': reviewer_details,
                'invitation_email_subject': '[' + venue['request_form_note'].content['Abbreviated Venue Name'] + '] Invitation to serve as {{invitee_role}}',
                'invitation_email_content': 'Dear {{fullname}},\n\nYou have been nominated by the program chair committee of Theoretical Foundations of RL Workshop @ ICML 2020 to serve as {{invitee_role}}.\n\nACCEPT LINK:\n\n{{accept_url}}\n\nDECLINE LINK:\n\n{{decline_url}}\n\nCheers!\n\nProgram Chairs',
                'accepted_email_template': 'Thank you for accepting the invitation to be a {{reviewer_name}} for Theoretical Foundations of RL Workshop @ ICML 2020.\n\nThe program chairs will be contacting you with more information regarding next steps soon.\n\nPlease complete your registration and expertise selection tasks here: https://openreview.net/tasks'
            },
            forum=venue['request_form_note'].forum,
            replyto=venue['request_form_note'].forum,
            invitation='{}/-/Request{}/Recruitment'.format(venue['support_group_id'], venue['request_form_note'].number),
            readers=['{}/Program_Chairs'.format(venue['venue_id']), venue['support_group_id']],
            signatures=['~SomeFirstName_User1'],
            writers=[]
        ))
        assert recruitment_note

        helpers.await_queue()
        process_logs = client.get_process_logs(id=recruitment_note.id)
        assert len(process_logs) == 1
        assert process_logs[0]['status'] == 'ok'
        assert process_logs[0]['invitation'] == '{}/-/Request{}/Recruitment'.format(venue['support_group_id'], venue['request_form_note'].number)

        messages = client.get_messages(to='reviewer_one_tilde@mail.com')
        assert messages and len(messages) == 2

        assert messages[1]['content']['subject'] == "[TestVenue@OR'2030] Invitation to serve as Reviewer"
        assert messages[1]['content']['text'].startswith('Dear Reviewer OneTilde,\n\nYou have been nominated by the program chair committee of Theoretical Foundations of RL Workshop @ ICML 2020 to serve as Reviewer.')

        messages = client.get_messages(to = 'reviewer_one_tilde@mail.com', subject = "[TestVenue@OR'2030] Invitation to serve as Reviewer")
        text = messages[0]['content']['text']
        accept_url = re.search('https://.*&response=Yes\n', text).group(0).replace('https://openreview.net', 'http://localhost:3030')[:-1]
        request_page(selenium, accept_url, alert=True)

        messages = client.get_messages(to = 'reviewer_one_tilde@mail.com', subject = '[TestVenue@OR\'2030] Reviewer Invitation accepted')
        assert messages and len(messages) == 1
        assert 'Please complete your registration and expertise selection tasks here: https://openreview.net/tasks' in messages[0]['content']['text']

        messages = client.get_messages(to='reviewer_two_tilde@mail.com')
        assert messages and len(messages) == 2
        assert messages[1]['content']['subject'] == "[TestVenue@OR'2030] Invitation to serve as Reviewer"
        assert messages[1]['content']['text'].startswith('Dear Reviewer TwoTilde,\n\nYou have been nominated by the program chair committee of Theoretical Foundations of RL Workshop @ ICML 2020 to serve as Reviewer.')

        recruitment_status_invitation = '{}/-/Request{}/Recruitment_Status'.format(venue['support_group_id'],
                                                                                   venue['request_form_note'].number)
        last_comment = client.get_notes(invitation=recruitment_status_invitation, sort='tmdate')[0]
        assert '2 users' in last_comment.content['invited']

        client.remove_members_from_group( 'TEST.cc/2030/Conference/Reviewers','~Reviewer_OneTilde1')

    def test_venue_remind_recruitment(self, client, test_client, selenium, request_page, venue, helpers):

        # Test Reviewer Remind Recruitment
        request_page(selenium, 'http://localhost:3030/forum?id={}'.format(venue['request_form_note'].id), test_client.token, wait_for_element=f"note_{venue['request_form_note'].id}")
        recruitment_div = selenium.find_element_by_id('note_{}'.format(venue['request_form_note'].id))
        assert recruitment_div
        reply_row = recruitment_div.find_element_by_class_name('reply_row')
        assert reply_row
        buttons = reply_row.find_elements_by_class_name('btn-xs')
        assert [btn for btn in buttons if btn.text == 'Remind Recruitment']

        remind_recruitment_note = test_client.post_note(openreview.Note(
            content={
                'title': 'Remind Recruitment',
                'invitee_role': 'Reviewers',
                'invitation_email_subject': '[' + venue['request_form_note'].content['Abbreviated Venue Name'] + '] Invitation to serve as {{invitee_role}}',
                'invitation_email_content': 'Dear {{fullname}},\n\nYou have been nominated by the program chair committee of Theoretical Foundations of RL Workshop @ ICML 2020 to serve as {{invitee_role}}.\n\nACCEPT LINK:\n\n{{accept_url}}\n\nDECLINE LINK:\n\n{{decline_url}}\n\nCheers!\n\nProgram Chairs'
            },
            forum=venue['request_form_note'].forum,
            replyto=venue['request_form_note'].forum,
            invitation='{}/-/Request{}/Remind_Recruitment'.format(venue['support_group_id'], venue['request_form_note'].number),
            readers=['{}/Program_Chairs'.format(venue['venue_id']), venue['support_group_id']],
            signatures=['~SomeFirstName_User1'],
            writers=[]
        ))
        assert remind_recruitment_note

        helpers.await_queue()
        process_logs = client.get_process_logs(id=remind_recruitment_note.id)
        assert len(process_logs) == 1
        assert process_logs[0]['status'] == 'ok'
        assert process_logs[0]['invitation'] == '{}/-/Request{}/Remind_Recruitment'.format(venue['support_group_id'], venue['request_form_note'].number)

        messages = client.get_messages(to='reviewer_candidate1@email.com')
        assert messages and len(messages) == 2
        assert messages[1]['content']['subject'] == "Reminder: [TestVenue@OR'2030] Invitation to serve as Reviewer"
        assert messages[1]['content']['text'].startswith('Dear invitee,\n\nYou have been nominated by the program chair committee of Theoretical Foundations of RL Workshop @ ICML 2020 to serve as Reviewer.')

        messages = client.get_messages(to='reviewer_candidate2@email.com')
        assert messages and len(messages) == 2
        assert messages[1]['content']['subject'] == "Reminder: [TestVenue@OR'2030] Invitation to serve as Reviewer"
        assert messages[1]['content']['text'].startswith('Dear invitee,\n\nYou have been nominated by the program chair committee of Theoretical Foundations of RL Workshop @ ICML 2020 to serve as Reviewer.')

        remind_recruitment_status_invitation = '{}/-/Request{}/Remind_Recruitment_Status'.format(venue['support_group_id'],
                                                                                   venue['request_form_note'].number)
        last_comment = client.get_notes(invitation=remind_recruitment_status_invitation, sort='tmdate')[0]
        assert '4 users' in last_comment.content['reminded']

        last_message = client.get_messages(to='support@openreview.net')[-1]
        assert 'Remind Recruitment Status' not in last_message['content']['text']

    def test_venue_recruitment_change_short_name(self, client, test_client, selenium, request_page, venue, helpers): 
        request_page(selenium, 'http://localhost:3030/forum?id={}'.format(venue['request_form_note'].id), test_client.token, wait_for_element=f"note_{venue['request_form_note'].id}")
        
        venue_revision_note = test_client.post_note(openreview.Note(
            content={
                'title': '{} Updated'.format(venue['request_form_note'].content['title']),
                'Official Venue Name': '{} Updated'.format(venue['request_form_note'].content['title']),
                'Abbreviated Venue Name': venue['request_form_note'].content['Abbreviated Venue Name'] + ' Modified',
                'Official Website URL': venue['request_form_note'].content['Official Website URL'],
                'program_chair_emails': venue['request_form_note'].content['program_chair_emails'],
                'Expected Submissions': '100',
                'How did you hear about us?': 'ML conferences',
                'Location': 'Virtual',
                'Submission Deadline':  venue['request_form_note'].content['Submission Deadline'],
                'Venue Start Date':  venue['request_form_note'].content['Venue Start Date'],
                'contact_email': venue['request_form_note'].content['contact_email']
            },
            forum=venue['request_form_note'].forum,
            invitation='{}/-/Request{}/Revision'.format(venue['support_group_id'], venue['request_form_note'].number),
            readers=['{}/Program_Chairs'.format(venue['venue_id']), venue['support_group_id']],
            referent=venue['request_form_note'].forum,
            replyto=venue['request_form_note'].forum,
            signatures=['~SomeFirstName_User1'],
            writers=[]
        ))

        helpers.await_queue()
        updated_request_form_note = client.get_note(venue['request_form_note'].id)
        assert updated_request_form_note.content['Abbreviated Venue Name'].endswith('Modified')

        helpers.create_user('reviewer_three_tilde@mail.com', 'Reviewer', 'ThreeTilde')
        reviewer_details = '''~Reviewer_ThreeTilde1'''
        recruitment_invitation = client.get_invitation('{}/-/Request{}/Recruitment'.format(venue['support_group_id'], venue['request_form_note'].number))

        assert recruitment_invitation.reply['content']['invitation_email_subject']['default'] == "[TestVenue@OR'2030 Modified] Invitation to serve as {{invitee_role}}"
        assert recruitment_invitation.reply['content']['invitation_email_content']['default'] == '''Dear {{fullname}},

        You have been nominated by the program chair committee of TestVenue@OR'2030 Modified to serve as {{invitee_role}}. As a respected researcher in the area, we hope you will accept and help us make TestVenue@OR'2030 Modified a success.

        You are also welcome to submit papers, so please also consider submitting to TestVenue@OR'2030 Modified.

        We will be using OpenReview.net and a reviewing process that we hope will be engaging and inclusive of the whole community.

        To ACCEPT the invitation, please click on the following link:

        {{accept_url}}

        To DECLINE the invitation, please click on the following link:

        {{decline_url}}

        Please answer within 10 days.

        If you accept, please make sure that your OpenReview account is updated and lists all the emails you are using. Visit http://openreview.net/profile after logging in.

        If you have any questions, please contact us at info@openreview.net.

        Cheers!

        Program Chairs
        '''
        recruitment_note = test_client.post_note(openreview.Note(
            content={
                'title': 'Recruitment',
                'invitee_role': 'Reviewers',
                'invitee_details': reviewer_details,
                'invitation_email_subject': recruitment_invitation.reply['content']['invitation_email_subject']['default'],
                'invitation_email_content': recruitment_invitation.reply['content']['invitation_email_content']['default']
            },
            forum=venue['request_form_note'].forum,
            replyto=venue['request_form_note'].forum,
            invitation='{}/-/Request{}/Recruitment'.format(venue['support_group_id'], venue['request_form_note'].number),
            readers=['{}/Program_Chairs'.format(venue['venue_id']), venue['support_group_id']],
            signatures=['~SomeFirstName_User1'],
            writers=[]
        ))
        assert recruitment_note

        helpers.await_queue()

        messages = client.get_messages(to='reviewer_three_tilde@mail.com')
        assert messages and len(messages) == 2

        assert messages[1]['content']['subject'] == "[TestVenue@OR'2030 Modified] Invitation to serve as Reviewer"
        assert "You have been nominated by the program chair committee of TestVenue@OR'2030 Modified to serve as Reviewer." in messages[1]['content']['text']
        
        remind_recruitment_invitation = client.get_invitation('{}/-/Request{}/Remind_Recruitment'.format(venue['support_group_id'], venue['request_form_note'].number))
        
        remind_recruitment_note = test_client.post_note(openreview.Note(
            content={
                'title': 'Remind Recruitment',
                'invitee_role': 'Reviewers',
                'invitation_email_subject': remind_recruitment_invitation.reply['content']['invitation_email_subject']['default'],
                'invitation_email_content': remind_recruitment_invitation.reply['content']['invitation_email_content']['default']
            },
            forum=venue['request_form_note'].forum,
            replyto=venue['request_form_note'].forum,
            invitation='{}/-/Request{}/Remind_Recruitment'.format(venue['support_group_id'], venue['request_form_note'].number),
            readers=['{}/Program_Chairs'.format(venue['venue_id']), venue['support_group_id']],
            signatures=['~SomeFirstName_User1'],
            writers=[]
        ))
    
        assert remind_recruitment_note
        helpers.await_queue()

        messages = client.get_messages(to='reviewer_three_tilde@mail.com')
        assert messages and len(messages) == 3

        assert messages[2]['content']['subject'] == "Reminder: [TestVenue@OR'2030 Modified] Invitation to serve as Reviewer"
        assert "You have been nominated by the program chair committee of TestVenue@OR'2030 Modified to serve as Reviewer." in messages[2]['content']['text']
        
        venue_revision_note = test_client.post_note(openreview.Note(
            content={
                'title': '{} Updated'.format(venue['request_form_note'].content['title']),
                'Official Venue Name': '{} Updated'.format(venue['request_form_note'].content['title']),
                'Abbreviated Venue Name': venue['request_form_note'].content['Abbreviated Venue Name'],
                'Official Website URL': venue['request_form_note'].content['Official Website URL'],
                'program_chair_emails': venue['request_form_note'].content['program_chair_emails'],
                'Expected Submissions': '100',
                'How did you hear about us?': 'ML conferences',
                'Location': 'Virtual',
                'Submission Deadline':  venue['request_form_note'].content['Submission Deadline'],
                'Venue Start Date':  venue['request_form_note'].content['Venue Start Date'],
                'contact_email': venue['request_form_note'].content['contact_email']
            },
            forum=venue['request_form_note'].forum,
            invitation='{}/-/Request{}/Revision'.format(venue['support_group_id'], venue['request_form_note'].number),
            readers=['{}/Program_Chairs'.format(venue['venue_id']), venue['support_group_id']],
            referent=venue['request_form_note'].forum,
            replyto=venue['request_form_note'].forum,
            signatures=['~SomeFirstName_User1'],
            writers=[]
        ))

        helpers.await_queue()
        updated_request_form_note = client.get_note(venue['request_form_note'].id)
        assert not updated_request_form_note.content['Abbreviated Venue Name'].endswith('Modified')

    def test_venue_bid_stage_error(self, client, test_client, selenium, request_page, helpers, venue):
        now = datetime.datetime.utcnow()
        due_date = now + datetime.timedelta(days=3)

        bid_stage_note = test_client.post_note(openreview.Note(
            content={
                'bid_start_date': '2021/02/30',
                'bid_due_date': due_date.strftime('%Y/%m/%d')
            },
            forum=venue['request_form_note'].forum,
            replyto=venue['request_form_note'].forum,
            referent=venue['request_form_note'].forum,
            invitation='{}/-/Request{}/Bid_Stage'.format(venue['support_group_id'], venue['request_form_note'].number),
            readers=['{}/Program_Chairs'.format(venue['venue_id']), venue['support_group_id']],
            signatures=['~SomeFirstName_User1'],
            writers=[]
        ))
        assert bid_stage_note

        helpers.await_queue()
        process_logs = client.get_process_logs(id=bid_stage_note.id)
        assert len(process_logs) == 1
        assert process_logs[0]['invitation'] == '{}/-/Request{}/Bid_Stage'.format(venue['support_group_id'], venue['request_form_note'].number)
        assert process_logs[0]['status'] == 'ok'

        comment_invitation = '{}/-/Request{}/Stage_Error_Status'.format(venue['support_group_id'],
                                                             venue['request_form_note'].number)
        last_comment = client.get_notes(invitation=comment_invitation, sort='tmdate')[0]
        error_string = '\n```python\nValueError(\'day is out of range for month\')'
        assert error_string in last_comment.content['error']

    def test_venue_bid_stage(self, client, test_client, selenium, request_page, helpers, venue):

        reviewer_client = helpers.create_user('venue_reviewer1@mail.com', 'Venue', 'Reviewer')

        reviewer_group_id = '{}/Reviewers'.format(venue['venue_id'])
        reviewer_group = client.get_group(reviewer_group_id)
        client.add_members_to_group(reviewer_group, '~Venue_Reviewer1')

        reviewer_url = 'http://localhost:3030/group?id={}#reviewer-tasks'.format(reviewer_group_id)
        request_page(selenium, reviewer_url, reviewer_client.token)
        with pytest.raises(NoSuchElementException):
            assert selenium.find_element_by_link_text('Reviewer Bid')

        now = datetime.datetime.utcnow()
        start_date = now - datetime.timedelta(days=2)
        due_date = now + datetime.timedelta(days=3)

        bid_stage_note = test_client.post_note(openreview.Note(
            content={
                'bid_start_date': start_date.strftime('%Y/%m/%d'),
                'bid_due_date': due_date.strftime('%Y/%m/%d')
            },
            forum=venue['request_form_note'].forum,
            replyto=venue['request_form_note'].forum,
            referent=venue['request_form_note'].forum,
            invitation='{}/-/Request{}/Bid_Stage'.format(venue['support_group_id'], venue['request_form_note'].number),
            readers=['{}/Program_Chairs'.format(venue['venue_id']), venue['support_group_id']],
            signatures=['~SomeFirstName_User1'],
            writers=[]
        ))
        assert bid_stage_note

        helpers.await_queue()
        process_logs = client.get_process_logs(id=bid_stage_note.id)
        assert len(process_logs) == 1
        assert process_logs[0]['invitation'] == '{}/-/Request{}/Bid_Stage'.format(venue['support_group_id'], venue['request_form_note'].number)
        assert process_logs[0]['status'] == 'ok'

        request_page(selenium, reviewer_url, reviewer_client.token, By.LINK_TEXT, wait_for_element='Reviewer Bid')
        assert selenium.find_element_by_link_text('Reviewer Bid')

    def test_venue_matching_setup(self, client, test_client, selenium, request_page, helpers, venue):
        # add a member to PC group
        pc_group = client.get_group('{}/Program_Chairs'.format(venue['venue_id']))
        client.add_members_to_group(group=pc_group, members=['pc@test.com'])

        author_client = helpers.create_user('venue_author1@mail.com', 'Venue', 'Author')
        reviewer_client = helpers.create_user('venue_reviewer2@mail.com', 'Venue', 'Reviewer')

        submission = author_client.post_note(openreview.Note(
            invitation='{}/-/Submission'.format(venue['venue_id']),
            readers=[
                venue['venue_id'],
                '~Venue_Author1'],
            writers=[
                '~Venue_Author1',
                venue['venue_id']
            ],
            signatures=['~Venue_Author1'],
            content={
                'title': 'test submission',
                'authorids': ['~Venue_Author1'],
                'authors': ['Venue Author'],
                'abstract': 'test abstract'
            }
        ))

        assert submission
        helpers.await_queue()

        messages = client.get_messages(subject='{} has received your submission titled {}'.format(venue['request_form_note'].content['Abbreviated Venue Name'], submission.content['title']))
        assert messages and len(messages) == 1
        assert 'This is some extra information to be added at the end of the email template.' in messages[0]['content']['text']
        assert 'Title: test submission' in messages[0]['content']['text']
        assert 'Your submission to TestVenue@OR\'2030 has been posted.'

        messages = client.get_messages(subject='{} has received a new submission titled {}'.format(venue['request_form_note'].content['Abbreviated Venue Name'], submission.content['title']))
        assert messages and len(messages) == 3
        recipients = [msg['content']['to'] for msg in messages]
        assert 'test@mail.com' in recipients
        assert 'tom@mail.com' in recipients
        assert 'pc@test.com' in recipients

        author_client = helpers.create_user('venue_author2@mail.com', 'Venue', 'Author')

        submission = author_client.post_note(openreview.Note(
            invitation='{}/-/Submission'.format(venue['venue_id']),
            readers=[
                venue['venue_id'],
                '~Venue_Author2'],
            writers=[
                '~Venue_Author2',
                venue['venue_id']
            ],
            signatures=['~Venue_Author2'],
            content={
                'title': 'test submission 2',
                'authorids': ['~Venue_Author2'],
                'authors': ['Venue Author'],
                'abstract': 'test abstract 2'
            }
        ))
        assert submission

        conference = openreview.get_conference(client, request_form_id=venue['request_form_note'].forum)

        ## activate matching setup invitation
        matching_setup_invitation = '{}/-/Request{}/Paper_Matching_Setup'.format(venue['support_group_id'], venue['request_form_note'].number)
        matching_inv = client.get_invitation(matching_setup_invitation)
        activation = datetime.datetime.utcnow()
        matching_inv.cdate = openreview.tools.datetime_millis(activation)
        matching_inv = client.post_invitation(matching_inv)
        assert matching_inv

        ## Run matching setup with no submissions
        matching_setup_note = test_client.post_note(openreview.Note(
            content={
                'title': 'Paper Matching Setup',
                'matching_group': conference.get_id() + '/Reviewers',
                'compute_conflicts': 'Yes',
                'compute_affinity_scores': 'Yes'
            },
            forum=venue['request_form_note'].forum,
            replyto=venue['request_form_note'].forum,
            invitation=matching_setup_invitation,
            readers=['{}/Program_Chairs'.format(venue['venue_id']), venue['support_group_id']],
            signatures=['~SomeFirstName_User1'],
            writers=[]
        ))
        assert matching_setup_note
        helpers.await_queue()

        comment_invitation_id = '{}/-/Request{}/Paper_Matching_Setup_Status'.format(venue['support_group_id'], venue['request_form_note'].number)
        matching_status = client.get_notes(invitation=comment_invitation_id, replyto=matching_setup_note.id, forum=venue['request_form_note'].forum, sort='tmdate')[0]
        assert matching_status
        assert 'Could not compute affinity scores and conflicts since no submissions were found. Make sure the submission deadline has passed and you have started the review stage using the \'Review Stage\' button.' in matching_status.content['error']

        conference.setup_post_submission_stage(force=True)

        blind_submissions = client.get_notes(invitation='{}/-/Blind_Submission'.format(venue['venue_id']), sort='tmdate')
        assert blind_submissions and len(blind_submissions) == 2

        reviewer_group = client.get_group('{}/Reviewers'.format(venue['venue_id']))
        client.remove_members_from_group(reviewer_group, '~Venue_Reviewer1')

        ## Remove ~Venue_Reviewer1 to keep the group empty and run the setup matching
        matching_setup_note = test_client.post_note(openreview.Note(
            content={
                'title': 'Paper Matching Setup',
                'matching_group': conference.get_id() + '/Reviewers',
                'compute_conflicts': 'Yes',
                'compute_affinity_scores': 'Yes'
            },
            forum=venue['request_form_note'].forum,
            replyto=venue['request_form_note'].forum,
            invitation=matching_setup_invitation,
            readers=['{}/Program_Chairs'.format(venue['venue_id']), venue['support_group_id']],
            signatures=['~SomeFirstName_User1'],
            writers=[]
        ))
        assert matching_setup_note
        helpers.await_queue()

        comment_invitation_id = '{}/-/Request{}/Paper_Matching_Setup_Status'.format(venue['support_group_id'], venue['request_form_note'].number)
        matching_status = client.get_notes(invitation=comment_invitation_id, replyto=matching_setup_note.id, forum=venue['request_form_note'].forum, sort='tmdate')[0]
        assert matching_status
        assert 'Could not compute affinity scores and conflicts since there are no Reviewers. You can use the \'Recruitment\' button to recruit Reviewers.' in matching_status.content['error']

        client.add_members_to_group(reviewer_group, '~Venue_Reviewer1')
        client.add_members_to_group(reviewer_group, '~Venue_Reviewer2')
        client.add_members_to_group(reviewer_group, 'some_user@mail.com')

        ## Setup matching with the API request
        matching_setup_note = test_client.post_note(openreview.Note(
            content={
                'title': 'Paper Matching Setup',
                'matching_group': conference.get_id() + '/Reviewers',
                'compute_conflicts': 'Yes',
                'compute_affinity_scores': 'Yes'
            },
            forum=venue['request_form_note'].forum,
            replyto=venue['request_form_note'].forum,
            invitation=matching_setup_invitation,
            readers=['{}/Program_Chairs'.format(venue['venue_id']), venue['support_group_id']],
            signatures=['~SomeFirstName_User1'],
            writers=[]
        ))
        assert matching_setup_note
        helpers.await_queue()

        comment_invitation_id = '{}/-/Request{}/Paper_Matching_Setup_Status'.format(venue['support_group_id'], venue['request_form_note'].number)
        matching_status = client.get_notes(invitation=comment_invitation_id, replyto=matching_setup_note.id, forum=venue['request_form_note'].forum, sort='tmdate')[0]
        assert matching_status
        assert 'There was an error connecting with the expertise API' in matching_status.content['error']

        ## Setup matching with no computation selected
        with pytest.raises(openreview.OpenReviewException, match=r'You need to compute either conflicts or affinity scores or both'):
            matching_setup_note = test_client.post_note(openreview.Note(
                content={
                    'title': 'Paper Matching Setup',
                    'matching_group': conference.get_id() + '/Reviewers',
                    'compute_conflicts': 'No',
                    'compute_affinity_scores': 'No'
                },
                forum=venue['request_form_note'].forum,
                replyto=venue['request_form_note'].forum,
                invitation=matching_setup_invitation,
                readers=['{}/Program_Chairs'.format(venue['venue_id']), venue['support_group_id']],
                signatures=['~SomeFirstName_User1'],
                writers=[]
            ))

        with open(os.path.join(os.path.dirname(__file__), 'data/rev_scores.csv'), 'w') as file_handle:
            writer = csv.writer(file_handle)
            for submission in blind_submissions:
                writer.writerow([submission.id, '~Venue_Reviewer1', round(random.random(), 2)])
                writer.writerow([submission.id, '~Venue_Reviewer2', round(random.random(), 2)])


        url = test_client.put_attachment(os.path.join(os.path.dirname(__file__), 'data/rev_scores.csv'), matching_setup_invitation, 'upload_affinity_scores')

        ## Setup matching with API and file computation selected
        with pytest.raises(openreview.OpenReviewException, match=r'Either upload your own affinity scores or select affinity scores computed by OpenReview'):
            matching_setup_note = test_client.post_note(openreview.Note(
                content={
                    'title': 'Paper Matching Setup',
                    'matching_group': conference.get_id() + '/Reviewers',
                    'compute_conflicts': 'No',
                    'compute_affinity_scores': 'Yes',
                    'upload_affinity_scores': url
                },
                forum=venue['request_form_note'].forum,
                replyto=venue['request_form_note'].forum,
                invitation=matching_setup_invitation,
                readers=['{}/Program_Chairs'.format(venue['venue_id']), venue['support_group_id']],
                signatures=['~SomeFirstName_User1'],
                writers=[]
            ))

        #post matching setup note
        matching_setup_note = test_client.post_note(openreview.Note(
            content={
                'title': 'Paper Matching Setup',
                'matching_group': conference.get_id() + '/Reviewers',
                'compute_conflicts': 'No',
                'compute_affinity_scores': 'No',
                'upload_affinity_scores': url
            },
            forum=venue['request_form_note'].forum,
            replyto=venue['request_form_note'].forum,
            invitation=matching_setup_invitation,
            readers=['{}/Program_Chairs'.format(venue['venue_id']), venue['support_group_id']],
            signatures=['~SomeFirstName_User1'],
            writers=[]
        ))
        assert matching_setup_note
        helpers.await_queue()

        comment_invitation_id = '{}/-/Request{}/Paper_Matching_Setup_Status'.format(venue['support_group_id'], venue['request_form_note'].number)
        matching_status = client.get_notes(invitation=comment_invitation_id, replyto=matching_setup_note.id, forum=venue['request_form_note'].forum, sort='tmdate')[0]
        assert matching_status
        assert matching_status.content['without_profile'] == ['some_user@mail.com']
        assert '''
1 Reviewers without a profile.

Affinity scores and/or conflicts could not be computed for the users listed under 'Without Profile'. You will not be able to run the matcher until all Reviewers have profiles. You have two options:

1. You can ask these users to sign up in OpenReview and upload their papers. After all Reviewers have done this, you will need to rerun the paper matching setup to recompute conflicts and/or affinity scores for all users.
2. You can remove these users from the Reviewers group: https://openreview.net/group/edit?id=TEST.cc/2030/Conference/Reviewers. You can find all users without a profile by searching for the '@' character in the search box.
''' in matching_status.content['comment']

        scores_invitation = client.get_invitation(conference.get_invitation_id('Affinity_Score', prefix=reviewer_group.id))
        assert scores_invitation
        affinity_scores = client.get_edges_count(invitation=scores_invitation.id)
        assert affinity_scores == 4

        assert not openreview.tools.get_invitation(client, f"{conference.get_id()}/Reviewers/-/Conflict")
        assert client.get_edges_count(invitation=f"{conference.get_id()}/Reviewers/-/Conflict") == 0

        ## Remove reviewer with no profile
        client.remove_members_from_group(reviewer_group, 'some_user@mail.com')

        matching_setup_note = test_client.post_note(openreview.Note(
            content={
                'title': 'Paper Matching Setup',
                'matching_group': conference.get_id() + '/Reviewers',
                'compute_conflicts': 'Yes',
                'compute_affinity_scores': 'No',
                'upload_affinity_scores': url
            },
            forum=venue['request_form_note'].forum,
            replyto=venue['request_form_note'].forum,
            invitation=matching_setup_invitation,
            readers=['{}/Program_Chairs'.format(venue['venue_id']), venue['support_group_id']],
            signatures=['~SomeFirstName_User1'],
            writers=[]
        ))
        assert matching_setup_note
        helpers.await_queue()

        comment_invitation_id = '{}/-/Request{}/Paper_Matching_Setup_Status'.format(venue['support_group_id'], venue['request_form_note'].number)
        matching_status = client.get_notes(invitation=comment_invitation_id, replyto=matching_setup_note.id, forum=venue['request_form_note'].forum, sort='tmdate')[0]
        assert matching_status
        assert matching_status.content['comment'] == '''Affinity scores and/or conflicts were successfully computed. To run the matcher, click on the 'Reviewers Paper Assignment' link in the PC console: https://openreview.net/group?id=TEST.cc/2030/Conference/Program_Chairs

Please refer to the FAQ for pointers on how to run the matcher: https://openreview.net/faq#question-edge-browswer'''

        scores_invitation = client.get_invitation(conference.get_invitation_id('Affinity_Score', prefix=reviewer_group.id))
        assert scores_invitation
        affinity_scores = client.get_edges_count(invitation=scores_invitation.id)
        assert affinity_scores == 4

        assert openreview.tools.get_invitation(client, f"{conference.get_id()}/Reviewers/-/Conflict")
        assert client.get_edges_count(invitation=f"{conference.get_id()}/Reviewers/-/Conflict") == 4


        last_message = client.get_messages(to='support@openreview.net')[-1]
        assert 'Paper Matching Setup Status' not in last_message['content']['text']
        last_message = client.get_messages(to='test@mail.com')[-1]
        assert 'Paper Matching Setup Status' in last_message['content']['subject']

    def test_update_withdraw_submission_due_date(self, client, test_client, selenium, request_page, helpers, venue):
        now = datetime.datetime.utcnow()
        start_date = now - datetime.timedelta(days=2)
        due_date = now + datetime.timedelta(days=3)
        withdraw_exp_date = now + datetime.timedelta(days=1)
        withdraw_exp_date = withdraw_exp_date.strftime('%Y/%m/%d')
        venue_revision_note = test_client.post_note(openreview.Note(
            content={
                'title': '{} Updated'.format(venue['request_form_note'].content['title']),
                'Official Venue Name': '{} Updated'.format(venue['request_form_note'].content['title']),
                'Abbreviated Venue Name': venue['request_form_note'].content['Abbreviated Venue Name'],
                'Official Website URL': venue['request_form_note'].content['Official Website URL'],
                'program_chair_emails': venue['request_form_note'].content['program_chair_emails'],
                'Expected Submissions': '100',
                'How did you hear about us?': 'ML conferences',
                'Location': 'Virtual',
                'Submission Deadline': due_date.strftime('%Y/%m/%d %H:%M'),
                'Venue Start Date': start_date.strftime('%Y/%m/%d'),
                'contact_email': venue['request_form_note'].content['contact_email'],
                'withdraw_submission_expiration': withdraw_exp_date,
            },
            forum=venue['request_form_note'].forum,
            invitation='{}/-/Request{}/Revision'.format(venue['support_group_id'], venue['request_form_note'].number),
            readers=['{}/Program_Chairs'.format(venue['venue_id']), venue['support_group_id']],
            referent=venue['request_form_note'].forum,
            replyto=venue['request_form_note'].forum,
            signatures=['~SomeFirstName_User1'],
            writers=[]
        ))
        assert venue_revision_note
        helpers.await_queue()
        process_logs = client.get_process_logs(id=venue_revision_note.id)
        assert len(process_logs) == 1
        assert process_logs[0]['status'] == 'ok'
        assert process_logs[0]['invitation'] == '{}/-/Request{}/Revision'.format(venue['support_group_id'],
                                                                                 venue['request_form_note'].number)

        conference = openreview.get_conference(client, request_form_id=venue['request_form_note'].forum)
        paper_withdraw_super_invitation = openreview.tools.get_invitation(client, conference.get_invitation_id("Withdraw"))
        withdraw_exp_date = datetime.datetime.strptime(withdraw_exp_date, '%Y/%m/%d')
        assert paper_withdraw_super_invitation.duedate is None
        assert openreview.tools.datetime_millis(withdraw_exp_date) == openreview.tools.datetime_millis(paper_withdraw_super_invitation.expdate)

    def test_venue_review_stage(self, client, test_client, selenium, request_page, helpers, venue):

        # Post a review stage note
        now = datetime.datetime.utcnow()
        start_date = now - datetime.timedelta(days=2)
        due_date = now + datetime.timedelta(days=3)
        review_stage_note = openreview.Note(
            content={
                'review_start_date': start_date.strftime('%Y/%m/%d'),
                'review_deadline': due_date.strftime('%Y/%m/%d'),
                'make_reviews_public': 'Yes, reviews should be revealed publicly when they are posted',
                'release_reviews_to_authors': 'No, reviews should NOT be revealed when they are posted to the paper\'s authors',
                'release_reviews_to_reviewers': 'Reviews should be immediately revealed to the paper\'s reviewers who have already submitted their review',
                'remove_review_form_options': 'title',
                'email_program_chairs_about_reviews': 'Yes, email program chairs for each review received',
                'review_rating_field_name': 'review_rating'
            },
            forum=venue['request_form_note'].forum,
            invitation='{}/-/Request{}/Review_Stage'.format(venue['support_group_id'], venue['request_form_note'].number),
            readers=['{}/Program_Chairs'.format(venue['venue_id']), venue['support_group_id']],
            referent=venue['request_form_note'].forum,
            replyto=venue['request_form_note'].forum,
            signatures=['~SomeFirstName_User1'],
            writers=[]
        )

        with pytest.raises(openreview.OpenReviewException, match=r'Reviews cannot be released to the public since all papers are private'):
            review_stage_note=test_client.post_note(review_stage_note)

        review_stage_note.content['make_reviews_public'] = 'No, reviews should NOT be revealed publicly when they are posted'
        review_stage_note=test_client.post_note(review_stage_note)

        assert review_stage_note
        helpers.await_queue()

        process_logs = client.get_process_logs(id = review_stage_note.id)
        assert len(process_logs) == 1
        assert process_logs[0]['status'] == 'ok'

        client.add_members_to_group(f'{venue["venue_id"]}/Paper1/Reviewers', '~Venue_Reviewer2')

        reviewer_client = openreview.Client(username='venue_reviewer2@mail.com', password='1234')
        reviewer_group = client.get_group('{}/Reviewers'.format(venue['venue_id']))
        assert reviewer_group and len(reviewer_group.members) == 2

        reviewer_page_url = 'http://localhost:3030/group?id={}/Reviewers#assigned-papers'.format(venue['venue_id'])
        request_page(selenium, reviewer_page_url, token=reviewer_client.token, by=By.LINK_TEXT, wait_for_element='test submission')

        note_div = selenium.find_element_by_id('note-summary-1')
        assert note_div
        assert 'test submission' == note_div.find_element_by_link_text('test submission').text

        review_invitations = client.get_invitations(super='{}/-/Official_Review'.format(venue['venue_id']))
        assert review_invitations and len(review_invitations) == 2
        assert 'title' not in review_invitations[0].reply['content']

        conference = openreview.get_conference(client, request_form_id=venue['request_form_note'].forum)
        assert conference.review_stage.rating_field_name == 'review_rating'

        reviewer_groups = [ g for g in client.get_groups('TEST.cc/2030/Conference/Paper.*') if g.id.endswith('/Reviewers')]
        assert len(reviewer_groups) == 2
        assert 'TEST.cc/2030/Conference' in reviewer_groups[0].readers
        assert 'TEST.cc/2030/Conference/Paper1/Area_Chairs' in reviewer_groups[0].readers
        assert 'TEST.cc/2030/Conference/Paper1/Reviewers' in reviewer_groups[0].readers

        assert 'TEST.cc/2030/Conference' in reviewer_groups[0].deanonymizers
        assert 'TEST.cc/2030/Conference/Paper1/Area_Chairs' in reviewer_groups[0].deanonymizers
        assert 'TEST.cc/2030/Conference/Paper1/Reviewers' not in reviewer_groups[0].deanonymizers

        ac_groups = [ g for g in client.get_groups('TEST.cc/2030/Conference/Paper.*') if '/Area_Chairs' in g.id ]
        assert len(ac_groups) == 2
        assert 'TEST.cc/2030/Conference' in ac_groups[0].readers
        assert 'TEST.cc/2030/Conference/Paper1/Area_Chairs' in ac_groups[0].readers
        assert 'TEST.cc/2030/Conference/Paper1/Reviewers' not in ac_groups[0].readers
        assert 'TEST.cc/2030/Conference/Paper1/Senior_Area_Chairs' in ac_groups[0].readers

        assert 'TEST.cc/2030/Conference' in ac_groups[0].deanonymizers
        assert 'TEST.cc/2030/Conference/Paper1/Reviewers' not in ac_groups[0].deanonymizers
        assert 'TEST.cc/2030/Conference/Paper1/Senior_Area_Chairs' in ac_groups[0].deanonymizers

        sac_groups = [ g for g in client.get_groups('TEST.cc/2030/Conference/Paper.*') if 'Senior_Area_Chairs' in g.id ]
        assert len(sac_groups) == 2
        assert 'TEST.cc/2030/Conference/Paper1/Senior_Area_Chairs' in sac_groups[0].readers
        assert 'TEST.cc/2030/Conference/Program_Chairs' in sac_groups[0].readers

    def test_venue_meta_review_stage(self, client, test_client, selenium, request_page, helpers, venue):

        meta_reviewer_client = helpers.create_user('venue_ac1@mail.com', 'Venue', 'Ac')

        conference = openreview.get_conference(client, request_form_id=venue['request_form_note'].forum)
        conference.setup_post_submission_stage(force=True)

        blind_submissions = client.get_notes(invitation='{}/-/Blind_Submission'.format(venue['venue_id']), sort='tmdate')
        assert blind_submissions and len(blind_submissions) == 2

        # Assert that ACs do not see the Submit button for meta reviews at this point
        meta_reviewer_group = client.get_group('{}/Area_Chairs'.format(venue['venue_id']))
        client.add_members_to_group(meta_reviewer_group, '~Venue_Ac1')

        client.add_members_to_group(f'{venue["venue_id"]}/Paper1/Area_Chairs', '~Venue_Ac1')
        client.add_members_to_group(f'{venue["venue_id"]}/Paper2/Area_Chairs', '~Venue_Ac1')

        ac_group = client.get_group('{}/Area_Chairs'.format(venue['venue_id']))
        assert ac_group and len(ac_group.members) == 1

        ac_page_url = 'http://localhost:3030/group?id={}/Area_Chairs'.format(venue['venue_id'])
        request_page(selenium, ac_page_url, token=meta_reviewer_client.token, wait_for_element='1-metareview-status')

        submit_div_1 = selenium.find_element_by_id('1-metareview-status')
        with pytest.raises(NoSuchElementException):
            assert submit_div_1.find_element_by_link_text('Submit')

        submit_div_2 = selenium.find_element_by_id('2-metareview-status')
        with pytest.raises(NoSuchElementException):
            assert submit_div_2.find_element_by_link_text('Submit')

        # Post a meta review stage note
        now = datetime.datetime.utcnow()
        start_date = now - datetime.timedelta(days=2)
        due_date = now + datetime.timedelta(days=3)
        meta_review_stage_note = test_client.post_note(openreview.Note(
            content={
                'make_meta_reviews_public': 'No, meta reviews should NOT be revealed publicly when they are posted',
                'meta_review_start_date': start_date.strftime('%Y/%m/%d'),
                'meta_review_deadline': due_date.strftime('%Y/%m/%d'),
                'recommendation_options': 'Accept, Reject',
                'release_meta_reviews_to_authors': 'No, meta reviews should NOT be revealed when they are posted to the paper\'s authors',
                'release_meta_reviews_to_reviewers': 'Meta reviews should be immediately revealed to the paper\'s reviewers who have already submitted their review',
                'additional_meta_review_form_options': {
                    'suggestions' : {
                        'value-regex': '[\\S\\s]{1,5000}',
                        'description': 'Please provide suggestions on how to improve the paper',
                        'required': False,
                    }
                },
                'remove_meta_review_form_options': 'confidence'
            },
            forum=venue['request_form_note'].forum,
            invitation='{}/-/Request{}/Meta_Review_Stage'.format(venue['support_group_id'], venue['request_form_note'].number),
            readers=['{}/Program_Chairs'.format(venue['venue_id']), venue['support_group_id']],
            referent=venue['request_form_note'].forum,
            replyto=venue['request_form_note'].forum,
            signatures=['~SomeFirstName_User1'],
            writers=[]
        ))
        assert meta_review_stage_note
        helpers.await_queue()

        process_logs = client.get_process_logs(id = meta_review_stage_note.id)
        assert len(process_logs) == 1
        assert process_logs[0]['status'] == 'ok'

        # Assert that AC now see the Submit button for assigned papers
        request_page(selenium, ac_page_url, token=meta_reviewer_client.token, wait_for_element='note-summary-2')

        note_div_1 = selenium.find_element_by_id('note-summary-1')
        assert note_div_1
        note_div_2 = selenium.find_element_by_id('note-summary-2')
        assert note_div_2
        assert 'test submission' == note_div_1.find_element_by_link_text('test submission').text
        assert 'test submission 2' == note_div_2.find_element_by_link_text('test submission 2').text

        submit_div_1 = selenium.find_element_by_id('1-metareview-status')
        assert submit_div_1.find_element_by_link_text('Submit')

        submit_div_2 = selenium.find_element_by_id('2-metareview-status')
        assert submit_div_2.find_element_by_link_text('Submit')

        meta_review_invitations = client.get_invitations(super='{}/-/Meta_Review'.format(venue['venue_id']))
        assert meta_review_invitations and len(meta_review_invitations) == 2
        assert 'confidence' not in meta_review_invitations[0].reply['content']
        assert 'suggestions' in meta_review_invitations[0].reply['content']
        assert 'Accept' in meta_review_invitations[0].reply['content']['recommendation']['value-dropdown']
        assert len(meta_review_invitations[0].reply['readers']['values']) == 4

    def test_venue_comment_stage(self, client, test_client, selenium, request_page, helpers, venue):

        conference = openreview.get_conference(client, request_form_id=venue['request_form_note'].forum)
        blind_submissions = client.get_notes(invitation='{}/-/Blind_Submission'.format(venue['venue_id']), sort='tmdate')
        assert blind_submissions and len(blind_submissions) == 2

        # Assert that official comment invitation is not available already
        official_comment_invitation = openreview.tools.get_invitation(client, conference.get_invitation_id('Official_Comment', number=1))
        assert official_comment_invitation is None

        # Post an official comment stage note
        now = datetime.datetime.utcnow()
        start_date = now - datetime.timedelta(days=2)
        end_date = now + datetime.timedelta(days=3)
        comment_stage_note = test_client.post_note(openreview.Note(
            content={
                'commentary_start_date': start_date.strftime('%Y/%m/%d'),
                'commentary_end_date': end_date.strftime('%Y/%m/%d'),
                'participants': ['Program Chairs', 'Assigned Senior Area Chairs', 'Assigned Area Chairs', 'Assigned Reviewers', 'Authors', 'Assigned Submitted Reviewers'],
                'email_program_chairs_about_official_comments': 'Yes, email PCs for each official comment made in the venue',
                'additional_readers': ['Public']

            },
            forum=venue['request_form_note'].forum,
            invitation='{}/-/Request{}/Comment_Stage'.format(venue['support_group_id'], venue['request_form_note'].number),
            readers=['{}/Program_Chairs'.format(venue['venue_id']), venue['support_group_id']],
            referent=venue['request_form_note'].forum,
            replyto=venue['request_form_note'].forum,
            signatures=['~SomeFirstName_User1'],
            writers=[]
        ))
        assert comment_stage_note
        helpers.await_queue()

        process_logs = client.get_process_logs(id=comment_stage_note.id)
        assert len(process_logs) == 1
        assert process_logs[0]['status'] == 'ok'

        # Assert that official comment invitation is now available
        official_comment_invitation = openreview.tools.get_invitation(client, conference.get_invitation_id('Official_Comment', number=1))
        assert official_comment_invitation
        assert 'everyone' in official_comment_invitation.reply['readers']['values-dropdown']

        # Assert that an official comment can be posted by the paper author
        forum_note = blind_submissions[-1]
        official_comment_note = test_client.post_note(openreview.Note(
            invitation=conference.get_invitation_id('Official_Comment', number=1),
            readers=[
                conference.get_program_chairs_id(),
                conference.get_area_chairs_id(number=1),
                conference.get_id() + '/Paper1/Authors',
                conference.get_id() + '/Paper1/Reviewers',
                conference.get_id() + '/Paper1/Reviewers/Submitted',
                conference.get_senior_area_chairs_id(number=1)
            ],
            writers=[
                conference.get_id() + '/Paper1/Authors',
                conference.get_id()],
            signatures=[conference.get_id() + '/Paper1/Authors'],
            forum=forum_note.forum,
            replyto=forum_note.forum,
            content={
                'comment': 'test comment',
                'title': 'test official comment title'
            }
        ))
        assert official_comment_note
        helpers.await_queue()

        process_logs = client.get_process_logs(id=official_comment_note.id)
        assert len(process_logs) == 1
        assert process_logs[0]['status'] == 'ok'

        # Assert that public comment invitation is not available
        public_comment_invitation = openreview.tools.get_invitation(client, conference.get_invitation_id('Public_Comment', number=1))
        assert public_comment_invitation is None

    def test_venue_decision_stage(self, client, test_client, selenium, request_page, venue, helpers):

        submissions = test_client.get_notes(invitation='{}/-/Blind_Submission'.format(venue['venue_id']), sort='tmdate')
        assert submissions and len(submissions) == 2
        submission = submissions[0]

        # Assert that PC does not have access to the Decision invitation
        decision_invitation = openreview.tools.get_invitation(test_client, '{}/Paper{}/-/Decision'.format(venue['venue_id'], submission.number))
        assert decision_invitation is None

        with open(os.path.join(os.path.dirname(__file__), 'data/decisions_more.csv'), 'w') as file_handle:
            writer = csv.writer(file_handle)
            writer.writerow([submissions[0].number, 'Reject', 'Not Good', "Test"])
            writer.writerow([submissions[1].number, 'Accept', 'Good Good', "Test"])

        with open(os.path.join(os.path.dirname(__file__), 'data/decisions_less.csv'), 'w') as file_handle:
            writer = csv.writer(file_handle)
            writer.writerow([submissions[0].number])
            writer.writerow([submissions[1].number])

        with open(os.path.join(os.path.dirname(__file__), 'data/decisions.csv'), 'w') as file_handle:
            writer = csv.writer(file_handle)
            writer.writerow([submissions[0].number, 'Accept', 'Good Paper'])
            writer.writerow([submissions[1].number, 'Reject', 'Not Good'])

        with open(os.path.join(os.path.dirname(__file__), 'data/decisions_wrong_paper.csv'), 'w') as file_handle:
            writer = csv.writer(file_handle)
            writer.writerow([978, 'Accept', 'Good Paper'])
            writer.writerow([submissions[1].number, 'Reject', 'Not Good'])

        with open(os.path.join(os.path.dirname(__file__), 'data/decisions_wrong_decision.csv'), 'w') as file_handle:
            writer = csv.writer(file_handle)
            writer.writerow([submissions[0].number, 'Test', 'Good Paper'])
            writer.writerow([submissions[1].number, 'Reject', 'Not Good'])

        # Post a decision stage note
        now = datetime.datetime.utcnow()
        start_date = now - datetime.timedelta(days=2)
        due_date = now + datetime.timedelta(days=3)

        decision_stage_note = test_client.post_note(openreview.Note(
            content={
                'decision_start_date': start_date.strftime('%Y/%m/%d'),
                'decision_deadline': due_date.strftime('%Y/%m/%d'),
                'decision_options': 'Accept, Revision Needed, Reject',
                'make_decisions_public': 'No, decisions should NOT be revealed publicly when they are posted',
                'release_decisions_to_authors': 'No, decisions should NOT be revealed when they are posted to the paper\'s authors',
                'release_decisions_to_reviewers': 'No, decisions should not be immediately revealed to the paper\'s reviewers',
                'release_decisions_to_area_chairs': 'Yes, decisions should be immediately revealed to the paper\'s area chairs',
                'notify_authors': 'No, I will send the emails to the authors',
                'additional_decision_form_options': {
                    'suggestions': {
                        'value-regex': '[\\S\\s]{1,5000}',
                        'description': 'Please provide suggestions on how to improve the paper',
                        'required': False,
                    }
                },
            },
            forum=venue['request_form_note'].forum,
            invitation='{}/-/Request{}/Decision_Stage'.format(venue['support_group_id'], venue['request_form_note'].number),
            readers=['{}/Program_Chairs'.format(venue['venue_id']), venue['support_group_id']],
            referent=venue['request_form_note'].forum,
            replyto=venue['request_form_note'].forum,
            signatures=['~SomeFirstName_User1'],
            writers=[]
        ))
        assert decision_stage_note
        helpers.await_queue()

        process_logs = client.get_process_logs(id = decision_stage_note.id)
        assert len(process_logs) == 1
        assert process_logs[0]['status'] == 'ok'

        # Assert that PC now has access to the Decision invitation
        decision_invitation = openreview.tools.get_invitation(test_client, '{}/Paper{}/-/Decision'.format(venue['venue_id'], submission.number))
        assert decision_invitation

        # Post a decision note using pc test_client
        program_chairs = '{}/Program_Chairs'.format(venue['venue_id'])
        area_chairs = '{}/Paper{}/Area_Chairs'.format(venue['venue_id'], submission.number)
        senior_area_chairs = '{}/Paper{}/Senior_Area_Chairs'.format(venue['venue_id'], submission.number)
        decision_note = test_client.post_note(openreview.Note(
            invitation='{}/Paper{}/-/Decision'.format(venue['venue_id'], submission.number),
            writers=[program_chairs],
            readers=[program_chairs, senior_area_chairs, area_chairs],
            nonreaders=['{}/Paper{}/Authors'.format(venue['venue_id'], submission.number)],
            signatures=[program_chairs],
            content={
                'title': 'Paper Decision',
                'decision': 'Accept',
                'comment': 'Good paper. I like!',
                'suggestions': 'Add more results for camera ready.'
            },
            forum=submission.forum,
            replyto=submission.forum
        ))

        assert decision_note
        assert 'suggestions' in decision_note.content
        helpers.await_queue()

        process_logs = client.get_process_logs(id=decision_stage_note.id)
        assert len(process_logs) == 1
        assert process_logs[0]['status'] == 'ok'

        decision_stage_invitation = '{}/-/Request{}/Decision_Stage'.format(venue['support_group_id'],
                                                                           venue['request_form_note'].number)
        url = test_client.put_attachment(os.path.join(os.path.dirname(__file__), 'data/decisions_more.csv'),
                                         decision_stage_invitation, 'decisions_file')

        decision_stage_note = test_client.post_note(openreview.Note(
            content={
                'decision_start_date': start_date.strftime('%Y/%m/%d'),
                'decision_deadline': due_date.strftime('%Y/%m/%d'),
                'decision_options': 'Accept, Revision Needed, Reject',
                'make_decisions_public': 'No, decisions should NOT be revealed publicly when they are posted',
                'release_decisions_to_authors': 'No, decisions should NOT be revealed when they are posted to the paper\'s authors',
                'release_decisions_to_reviewers': 'No, decisions should not be immediately revealed to the paper\'s reviewers',
                'release_decisions_to_area_chairs': 'Yes, decisions should be immediately revealed to the paper\'s area chairs',
                'notify_authors': 'No, I will send the emails to the authors',
                'additional_decision_form_options': {
                    'suggestions': {
                        'value-regex': '[\\S\\s]{1,5000}',
                        'description': 'Please provide suggestions on how to improve the paper',
                        'required': False,
                    }
                },
                'decisions_file': url
            },
            forum=venue['request_form_note'].forum,
            invitation='{}/-/Request{}/Decision_Stage'.format(venue['support_group_id'],
                                                              venue['request_form_note'].number),
            readers=['{}/Program_Chairs'.format(venue['venue_id']), venue['support_group_id']],
            referent=venue['request_form_note'].forum,
            replyto=venue['request_form_note'].forum,
            signatures=['~SomeFirstName_User1'],
            writers=[]
        ))

        assert decision_stage_note
        helpers.await_queue()

        process_logs = client.get_process_logs(id=decision_stage_note.id)
        assert len(process_logs) == 1
        assert process_logs[0]['status'] == 'ok'

        status_invitation_id = '{}/-/Request{}/Decision_Upload_Status'.format(venue['support_group_id'],
                                                                              venue['request_form_note'].number)
        decision_status = client.get_notes(invitation=status_invitation_id, replyto=venue['request_form_note'].forum,
                                           forum=venue['request_form_note'].forum, sort='tmdate')[0]

        assert decision_status
        assert decision_status.content['decision_posted'] == '0 Papers'
        assert 'Total Errors: 2' in decision_status.content['error']
        assert '\"Too many values provided in the decision file. Expected values are: paper_number, decision, comment\"' in decision_status.content['error']

        url = test_client.put_attachment(os.path.join(os.path.dirname(__file__), 'data/decisions_less.csv'),
                                         decision_stage_invitation, 'decisions_file')

        decision_stage_note = test_client.post_note(openreview.Note(
            content={
                'decision_start_date': start_date.strftime('%Y/%m/%d'),
                'decision_deadline': due_date.strftime('%Y/%m/%d'),
                'decision_options': 'Accept, Revision Needed, Reject',
                'make_decisions_public': 'No, decisions should NOT be revealed publicly when they are posted',
                'release_decisions_to_authors': 'No, decisions should NOT be revealed when they are posted to the paper\'s authors',
                'release_decisions_to_reviewers': 'No, decisions should not be immediately revealed to the paper\'s reviewers',
                'release_decisions_to_area_chairs': 'Yes, decisions should be immediately revealed to the paper\'s area chairs',
                'notify_authors': 'No, I will send the emails to the authors',
                'additional_decision_form_options': {
                    'suggestions': {
                        'value-regex': '[\\S\\s]{1,5000}',
                        'description': 'Please provide suggestions on how to improve the paper',
                        'required': False,
                    }
                },
                'decisions_file': url
            },
            forum=venue['request_form_note'].forum,
            invitation='{}/-/Request{}/Decision_Stage'.format(venue['support_group_id'],
                                                              venue['request_form_note'].number),
            readers=['{}/Program_Chairs'.format(venue['venue_id']), venue['support_group_id']],
            referent=venue['request_form_note'].forum,
            replyto=venue['request_form_note'].forum,
            signatures=['~SomeFirstName_User1'],
            writers=[]
        ))

        assert decision_stage_note
        helpers.await_queue()

        process_logs = client.get_process_logs(id=decision_stage_note.id)
        assert len(process_logs) == 1
        assert process_logs[0]['status'] == 'ok'

        status_invitation_id = '{}/-/Request{}/Decision_Upload_Status'.format(venue['support_group_id'],
                                                                              venue['request_form_note'].number)
        decision_status = client.get_notes(invitation=status_invitation_id, replyto=venue['request_form_note'].forum,
                                           forum=venue['request_form_note'].forum, sort='tmdate')[0]

        assert decision_status
        assert decision_status.content['decision_posted'] == '0 Papers'
        assert 'Total Errors: 2' in decision_status.content['error']
        assert '\"Not enough values provided in the decision file. Expected values are: paper_number, decision, comment\"' in decision_status.content['error']

        url = test_client.put_attachment(os.path.join(os.path.dirname(__file__), 'data/decisions_wrong_paper.csv'),
                                         decision_stage_invitation, 'decisions_file')

        decision_stage_note = test_client.post_note(openreview.Note(
            content={
                'decision_start_date': start_date.strftime('%Y/%m/%d'),
                'decision_deadline': due_date.strftime('%Y/%m/%d'),
                'decision_options': 'Accept, Revision Needed, Reject',
                'make_decisions_public': 'No, decisions should NOT be revealed publicly when they are posted',
                'release_decisions_to_authors': 'No, decisions should NOT be revealed when they are posted to the paper\'s authors',
                'release_decisions_to_reviewers': 'No, decisions should not be immediately revealed to the paper\'s reviewers',
                'release_decisions_to_area_chairs': 'Yes, decisions should be immediately revealed to the paper\'s area chairs',
                'notify_authors': 'No, I will send the emails to the authors',
                'additional_decision_form_options': {
                    'suggestions': {
                        'value-regex': '[\\S\\s]{1,5000}',
                        'description': 'Please provide suggestions on how to improve the paper',
                        'required': False,
                    }
                },
                'decisions_file': url
            },
            forum=venue['request_form_note'].forum,
            invitation='{}/-/Request{}/Decision_Stage'.format(venue['support_group_id'],
                                                              venue['request_form_note'].number),
            readers=['{}/Program_Chairs'.format(venue['venue_id']), venue['support_group_id']],
            referent=venue['request_form_note'].forum,
            replyto=venue['request_form_note'].forum,
            signatures=['~SomeFirstName_User1'],
            writers=[]
        ))

        assert decision_stage_note
        helpers.await_queue()

        process_logs = client.get_process_logs(id=decision_stage_note.id)
        assert len(process_logs) == 1
        assert process_logs[0]['status'] == 'ok'

        status_invitation_id = '{}/-/Request{}/Decision_Upload_Status'.format(venue['support_group_id'],
                                                                              venue['request_form_note'].number)
        decision_status = client.get_notes(invitation=status_invitation_id, replyto=venue['request_form_note'].forum,
                                           forum=venue['request_form_note'].forum, sort='tmdate')[0]

        assert decision_status
        assert decision_status.content['decision_posted'] == '1 Papers'
        assert 'Total Errors: 1' in decision_status.content['error']
        assert '\"Paper 978 not found. Please check the submitted paper numbers.\"' in \
               decision_status.content['error']

        url = test_client.put_attachment(os.path.join(os.path.dirname(__file__), 'data/decisions_wrong_decision.csv'),
                                         decision_stage_invitation, 'decisions_file')

        decision_stage_note = test_client.post_note(openreview.Note(
            content={
                'decision_start_date': start_date.strftime('%Y/%m/%d'),
                'decision_deadline': due_date.strftime('%Y/%m/%d'),
                'decision_options': 'Accept, Revision Needed, Reject',
                'make_decisions_public': 'No, decisions should NOT be revealed publicly when they are posted',
                'release_decisions_to_authors': 'No, decisions should NOT be revealed when they are posted to the paper\'s authors',
                'release_decisions_to_reviewers': 'No, decisions should not be immediately revealed to the paper\'s reviewers',
                'release_decisions_to_area_chairs': 'Yes, decisions should be immediately revealed to the paper\'s area chairs',
                'notify_authors': 'No, I will send the emails to the authors',
                'additional_decision_form_options': {
                    'suggestions': {
                        'value-regex': '[\\S\\s]{1,5000}',
                        'description': 'Please provide suggestions on how to improve the paper',
                        'required': False,
                    }
                },
                'decisions_file': url
            },
            forum=venue['request_form_note'].forum,
            invitation='{}/-/Request{}/Decision_Stage'.format(venue['support_group_id'],
                                                              venue['request_form_note'].number),
            readers=['{}/Program_Chairs'.format(venue['venue_id']), venue['support_group_id']],
            referent=venue['request_form_note'].forum,
            replyto=venue['request_form_note'].forum,
            signatures=['~SomeFirstName_User1'],
            writers=[]
        ))

        assert decision_stage_note
        helpers.await_queue()

        process_logs = client.get_process_logs(id=decision_stage_note.id)
        assert len(process_logs) == 1
        assert process_logs[0]['status'] == 'ok'

        status_invitation_id = '{}/-/Request{}/Decision_Upload_Status'.format(venue['support_group_id'],
                                                                              venue['request_form_note'].number)
        decision_status = client.get_notes(invitation=status_invitation_id, replyto=venue['request_form_note'].forum,
                                           forum=venue['request_form_note'].forum, sort='tmdate')[0]

        assert decision_status
        assert decision_status.content['decision_posted'] == '1 Papers'
        assert 'Total Errors: 1' in decision_status.content['error']
        assert '\"The value Test in field decision does not match the invitation definition\"' in decision_status.content['error']

        url = test_client.put_attachment(os.path.join(os.path.dirname(__file__), 'data/decisions.csv'),
                                         decision_stage_invitation, 'decisions_file')

        decision_stage_note = test_client.post_note(openreview.Note(
            content={
                'decision_start_date': start_date.strftime('%Y/%m/%d'),
                'decision_deadline': due_date.strftime('%Y/%m/%d'),
                'decision_options': 'Accept, Revision Needed, Reject',
                'make_decisions_public': 'No, decisions should NOT be revealed publicly when they are posted',
                'release_decisions_to_authors': 'No, decisions should NOT be revealed when they are posted to the paper\'s authors',
                'release_decisions_to_reviewers': 'No, decisions should not be immediately revealed to the paper\'s reviewers',
                'release_decisions_to_area_chairs': 'Yes, decisions should be immediately revealed to the paper\'s area chairs',
                'notify_authors': 'No, I will send the emails to the authors',
                'additional_decision_form_options': {
                    'suggestions': {
                        'value-regex': '[\\S\\s]{1,5000}',
                        'description': 'Please provide suggestions on how to improve the paper',
                        'required': False,
                    }
                },
                'decisions_file': url
            },
            forum=venue['request_form_note'].forum,
            invitation='{}/-/Request{}/Decision_Stage'.format(venue['support_group_id'],
                                                              venue['request_form_note'].number),
            readers=['{}/Program_Chairs'.format(venue['venue_id']), venue['support_group_id']],
            referent=venue['request_form_note'].forum,
            replyto=venue['request_form_note'].forum,
            signatures=['~SomeFirstName_User1'],
            writers=[]
        ))

        assert decision_stage_note
        helpers.await_queue()

        process_logs = client.get_process_logs(id=decision_stage_note.id)
        assert len(process_logs) == 1
        assert process_logs[0]['status'] == 'ok'

        status_invitation_id = '{}/-/Request{}/Decision_Upload_Status'.format(venue['support_group_id'],
                                                                              venue['request_form_note'].number)
        decision_status = client.get_notes(invitation=status_invitation_id, replyto=venue['request_form_note'].forum,
                                           forum=venue['request_form_note'].forum, sort='tmdate')[0]

        assert decision_status
        assert decision_status.content['decision_posted'] == '2 Papers'

        with open(os.path.join(os.path.dirname(__file__), 'data/decisions.csv')) as f:
            sub_decisions = list(csv.reader(f))

        for i in range(len(submissions)):
            sub_decision_notes = test_client.get_notes(
                invitation='{venue_id}/Paper{number}/-/Decision'.format(
                    venue_id=venue['venue_id'], number=submissions[i].number
                )
            )
            assert len(sub_decision_notes) == 1
            sub_decision_note = sub_decision_notes[0]
            assert sub_decision_note
            assert sub_decision_note.content['decision'] == sub_decisions[i][1]
            assert sub_decision_note.content['comment'] == sub_decisions[i][2]

        # reveal decisions to authors
        decision_stage_note = test_client.post_note(openreview.Note(
            content={
                'decision_start_date': start_date.strftime('%Y/%m/%d'),
                'decision_deadline': due_date.strftime('%Y/%m/%d'),
                'decision_options': 'Accept, Revision Needed, Reject',
                'make_decisions_public': 'No, decisions should NOT be revealed publicly when they are posted',
                'release_decisions_to_authors': 'Yes, decisions should be revealed when they are posted to the paper\'s authors',
                'release_decisions_to_reviewers': 'Yes, decisions should be immediately revealed to the paper\'s reviewers',
                'release_decisions_to_area_chairs': 'Yes, decisions should be immediately revealed to the paper\'s area chairs',
                'additional_decision_form_options': {
                    'suggestions': {
                        'value-regex': '[\\S\\s]{1,5000}',
                        'description': 'Please provide suggestions on how to improve the paper',
                        'required': False,
                    }
                },
                'decisions_file': url
            },
            forum=venue['request_form_note'].forum,
            invitation='{}/-/Request{}/Decision_Stage'.format(venue['support_group_id'],
                                                              venue['request_form_note'].number),
            readers=['{}/Program_Chairs'.format(venue['venue_id']), venue['support_group_id']],
            referent=venue['request_form_note'].forum,
            replyto=venue['request_form_note'].forum,
            signatures=['~SomeFirstName_User1'],
            writers=[]
        ))

        assert decision_stage_note
        helpers.await_queue()

        process_logs = client.get_process_logs(id=decision_stage_note.id)
        assert len(process_logs) == 1
        assert process_logs[0]['status'] == 'ok'

        decision_note = test_client.get_notes(
            invitation='{venue_id}/Paper1/-/Decision'.format(venue_id=venue['venue_id'])
        )[0]

        assert f'TEST.cc/2030/Conference/Paper1/Authors' in decision_note.readers
        assert f'TEST.cc/2030/Conference/Paper1/Reviewers' in decision_note.readers
        assert not decision_note.nonreaders

        #get post_decision invitation
        with pytest.raises(openreview.OpenReviewException) as openReviewError:
            post_decision_invitation = test_client.get_invitation('{}/-/Request{}/Post_Decision_Stage'.format(venue['support_group_id'], venue['request_form_note'].number))
        assert openReviewError.value.args[0].get('name') == 'NotFoundError'

        invitation = client.get_invitation('{}/-/Request{}/Post_Decision_Stage'.format(venue['support_group_id'], venue['request_form_note'].number))
        assert invitation.cdate > openreview.tools.datetime_millis(datetime.datetime.utcnow())

    def test_post_submission_deadline_edit(self, client, test_client, selenium, request_page, helpers, venue):
        author_client = helpers.create_user('venue_author3@mail.com', 'Venue', 'Author')
        submission = author_client.post_note(openreview.Note(
            invitation='{}/-/Submission'.format(venue['venue_id']),
            readers=[
                venue['venue_id'],
                '~Venue_Author3'
            ],
            writers=[
                '~Venue_Author3',
                venue['venue_id']
            ],
            signatures=['~Venue_Author3'],
            content={
                'title': 'test submission 3',
                'authorids': ['~Venue_Author3'],
                'authors': ['Venue Author'],
                'abstract': 'test abstract 3'
            }
        ))

        assert submission

        # expire submission deadline
        now = datetime.datetime.utcnow()
        start_date = now - datetime.timedelta(days=2)
        due_date = now - datetime.timedelta(days=1)
        venue_revision_note = test_client.post_note(openreview.Note(
            content={
                'title': '{} Updated'.format(venue['request_form_note'].content['title']),
                'Official Venue Name': '{} Updated'.format(venue['request_form_note'].content['title']),
                'Abbreviated Venue Name': venue['request_form_note'].content['Abbreviated Venue Name'],
                'Official Website URL': venue['request_form_note'].content['Official Website URL'],
                'program_chair_emails': venue['request_form_note'].content['program_chair_emails'],
                'Expected Submissions': '100',
                'How did you hear about us?': 'ML conferences',
                'Location': 'Virtual',
                'Submission Deadline': due_date.strftime('%Y/%m/%d %H:%M'),
                'Venue Start Date': start_date.strftime('%Y/%m/%d'),
                'contact_email': venue['request_form_note'].content['contact_email'],
            },
            forum=venue['request_form_note'].forum,
            invitation='{}/-/Request{}/Revision'.format(venue['support_group_id'], venue['request_form_note'].number),
            readers=['{}/Program_Chairs'.format(venue['venue_id']), venue['support_group_id']],
            referent=venue['request_form_note'].forum,
            replyto=venue['request_form_note'].forum,
            signatures=['~SomeFirstName_User1'],
            writers=[]
        ))
        assert venue_revision_note
        helpers.await_queue()
        process_logs = client.get_process_logs(id=venue_revision_note.id)
        assert len(process_logs) == 1
        assert process_logs[0]['status'] == 'ok'

        conference = openreview.get_conference(client, request_form_id=venue['request_form_note'].forum)
        conference.setup_post_submission_stage(force=True)

        submission.content['authorids'] = ['~Venue_Author3', '~Venue_Author2']
        submission.content['authors'] = ['Venue Author', 'Venue Author']
        submission.signatures = ['~SomeFirstName_User1']

        test_client.post_note(submission)
        helpers.await_queue()
        process_logs = client.get_process_logs(id=submission.id)
        assert process_logs[0]['status'] == 'ok'

        blind_submissions = author_client.get_notes(
            invitation='{}/-/Blind_Submission'.format(venue['venue_id']), sort='tmdate')
        assert blind_submissions and len(blind_submissions) == 1

        authors_group = client.get_group(f'{conference.id}/Paper{submission.number}/Authors')
        assert '~Venue_Author2' in authors_group.members

    def test_venue_submission_revision_stage(self, client, test_client, selenium, request_page, helpers, venue):
        author_client = openreview.Client(baseurl = 'http://localhost:3000', username='venue_author3@mail.com', password='1234')

        # extend submission deadline
        now = datetime.datetime.utcnow()
        start_date = now - datetime.timedelta(days=2)
        due_date = now + datetime.timedelta(days=1)
        venue_revision_note = test_client.post_note(openreview.Note(
            content={
                'title': '{} Updated'.format(venue['request_form_note'].content['title']),
                'Official Venue Name': '{} Updated'.format(venue['request_form_note'].content['title']),
                'Abbreviated Venue Name': venue['request_form_note'].content['Abbreviated Venue Name'],
                'Official Website URL': venue['request_form_note'].content['Official Website URL'],
                'program_chair_emails': venue['request_form_note'].content['program_chair_emails'],
                'Expected Submissions': '100',
                'How did you hear about us?': 'ML conferences',
                'Location': 'Virtual',
                'Submission Deadline': due_date.strftime('%Y/%m/%d %H:%M'),
                'Venue Start Date': start_date.strftime('%Y/%m/%d'),
                'contact_email': venue['request_form_note'].content['contact_email'],
            },
            forum=venue['request_form_note'].forum,
            invitation='{}/-/Request{}/Revision'.format(venue['support_group_id'], venue['request_form_note'].number),
            readers=['{}/Program_Chairs'.format(venue['venue_id']), venue['support_group_id']],
            referent=venue['request_form_note'].forum,
            replyto=venue['request_form_note'].forum,
            signatures=['~SomeFirstName_User1'],
            writers=[]
        ))
        assert venue_revision_note
        helpers.await_queue()
        process_logs = client.get_process_logs(id=venue_revision_note.id)
        assert len(process_logs) == 1
        assert process_logs[0]['status'] == 'ok'

        # Post a revision stage note
        now = datetime.datetime.utcnow()
        start_date = now - datetime.timedelta(days=2)
        due_date = now + datetime.timedelta(days=3)
        revision_stage_note = test_client.post_note(openreview.Note(
            content={
                'submission_revision_name': 'Revision',
                'submission_revision_start_date': start_date.strftime('%Y/%m/%d'),
                'submission_revision_deadline': due_date.strftime('%Y/%m/%d'),
                'accepted_submissions_only': 'Enable revision for all submissions',
                'submission_author_edition': 'Allow addition and removal of authors',
                'submission_revision_remove_options': ['keywords']
            },
            forum=venue['request_form_note'].forum,
            invitation='{}/-/Request{}/Submission_Revision_Stage'.format(venue['support_group_id'], venue['request_form_note'].number),
            readers=['{}/Program_Chairs'.format(venue['venue_id']), venue['support_group_id']],
            referent=venue['request_form_note'].forum,
            replyto=venue['request_form_note'].forum,
            signatures=['~SomeFirstName_User1'],
            writers=[]
        ))
        assert revision_stage_note

        helpers.await_queue()
        process_logs = client.get_process_logs(id=revision_stage_note.id)
        assert len(process_logs) == 1
        assert process_logs[0]['status'] == 'ok'

        blind_submissions = author_client.get_notes(invitation='{}/-/Blind_Submission'.format(venue['venue_id']))

        author_page_url = 'http://localhost:3030/forum?id={}'.format(blind_submissions[0].forum, by=By.CLASS_NAME, wait_for_element='edit_button')
        request_page(selenium, author_page_url, token=author_client.token)

        meta_actions = selenium.find_elements_by_class_name('meta_actions')
        assert len(meta_actions) == 2
        ## Edit and trash buttons, the submission invitation is still open
        assert meta_actions[0].find_element_by_class_name('edit_button')
        assert meta_actions[0].find_element_by_class_name('trash_button')
        ## Reference invitations
        assert 'Revision' == meta_actions[1].find_element_by_class_name('edit_button').text

        # Post revision note for a submission
        revision_note = author_client.post_note(openreview.Note(
            invitation='{}/Paper{}/-/Revision'.format(venue['venue_id'], blind_submissions[0].number),
            forum=blind_submissions[0].original,
            referent=blind_submissions[0].original,
            replyto=blind_submissions[0].original,
            readers=[venue['venue_id'], '{}/Paper{}/Authors'.format(venue['venue_id'], blind_submissions[0].number)],
            writers=['{}/Paper{}/Authors'.format(venue['venue_id'], blind_submissions[0].number), venue['venue_id']],
            signatures=['{}/Paper{}/Authors'.format(venue['venue_id'], blind_submissions[0].number)],
            content={
                'title': 'revised test submission 3',
                'abstract': 'revised abstract 3',
                'authors': ['Venue Author', 'Melisa Bok'],
                'authorids': ['~Venue_Author3', 'melisa@mail.com']
            }
        ))
        assert revision_note

        helpers.await_queue()
        process_logs = client.get_process_logs(id=revision_note.id)
        assert len(process_logs) == 1
        assert process_logs[0]['status'] == 'ok'

        updated_note = author_client.get_note(id=blind_submissions[0].forum)
        assert updated_note
        assert updated_note.content['title'] == 'revised test submission 3'
        assert updated_note.content['abstract'] == 'revised abstract 3'
        assert updated_note.content['authors'] == blind_submissions[0].content['authors']
        assert updated_note.content['authorids'] == blind_submissions[0].content['authorids']
        note_authors = client.get_group('{}/Paper{}/Authors'.format(venue['venue_id'], blind_submissions[0].number))
        assert len(note_authors.members) == 2
        assert note_authors.members == ['~Venue_Author3', 'melisa@mail.com']

        messages = client.get_messages(subject='{} has received a new revision of your submission titled revised test submission 3'.format(venue['request_form_note'].content['Abbreviated Venue Name']))
        assert messages and len(messages) == 2
        #assert messages[0]['content']['to'] == 'venue_author3@mail.com'

        revision_note.ddate = openreview.tools.datetime_millis(datetime.datetime.utcnow())
        deleted_note = author_client.post_note(revision_note)
        helpers.await_queue()
        process_logs = client.get_process_logs(id=deleted_note.id)
        assert len(process_logs) == 2
        assert process_logs[0]['status'] == 'ok'

        updated_note = author_client.get_note(id=blind_submissions[0].forum)
        assert updated_note
        assert updated_note.content['authors'] == blind_submissions[0].content['authors']
        assert updated_note.content['authorids'] == blind_submissions[0].content['authorids']
        note_authors = client.get_group('{}/Paper{}/Authors'.format(venue['venue_id'], blind_submissions[0].number))
        assert len(note_authors.members) == 2
        assert note_authors.members == ['~Venue_Author3', '~Venue_Author2']


    def test_venue_submission_revision_stage_accepted_papers_only(self, client, test_client, selenium, request_page, helpers, venue):
        conference = openreview.get_conference(client, request_form_id=venue['request_form_note'].forum)
        conference.setup_post_submission_stage(force=True)

        # Post a revision stage note
        now = datetime.datetime.utcnow()
        start_date = now - datetime.timedelta(days=2)
        due_date = now + datetime.timedelta(days=3)
        revision_stage_note = test_client.post_note(openreview.Note(
            content={
                'submission_revision_name': 'Revision',
                'submission_revision_start_date': start_date.strftime('%Y/%m/%d'),
                'submission_revision_deadline': due_date.strftime('%Y/%m/%d'),
                'accepted_submissions_only': 'Enable revision for accepted submissions only',
                'submission_author_edition': 'Allow addition and removal of authors',
                'submission_revision_remove_options': ['keywords']
            },
            forum=venue['request_form_note'].forum,
            invitation='{}/-/Request{}/Submission_Revision_Stage'.format(venue['support_group_id'], venue['request_form_note'].number),
            readers=['{}/Program_Chairs'.format(venue['venue_id']), venue['support_group_id']],
            referent=venue['request_form_note'].forum,
            replyto=venue['request_form_note'].forum,
            signatures=['~SomeFirstName_User1'],
            writers=[]
        ))
        assert revision_stage_note

        helpers.await_queue()
        process_logs = client.get_process_logs(id=revision_stage_note.id)
        assert len(process_logs) == 1
        assert process_logs[0]['status'] == 'ok'

        blind_submissions = test_client.get_notes(invitation='{}/-/Blind_Submission'.format(venue['venue_id']))
        revision_invitation = test_client.get_invitation('{}/Paper{}/-/Revision'.format(venue['venue_id'], blind_submissions[0].number))
        assert revision_invitation.expdate < round(time.time() * 1000)

    def test_post_decision_stage(self, client, test_client, selenium, request_page, helpers, venue):
        blind_submissions = client.get_notes(invitation='{}/-/Blind_Submission'.format(venue['venue_id']), sort='tmdate')
        assert blind_submissions and len(blind_submissions) == 3

        # Assert that submissions are still blind
        assert blind_submissions[0].content['authors'] == ['Anonymous']
        assert blind_submissions[0].content['authorids'] == ['{}/Paper{}/Authors'.format(venue['venue_id'], blind_submissions[0].number)]
        assert blind_submissions[1].content['authors'] == ['Anonymous']
        assert blind_submissions[1].content['authorids'] == ['{}/Paper{}/Authors'.format(venue['venue_id'], blind_submissions[1].number)]
        assert blind_submissions[2].content['authors'] == ['Anonymous']
        assert blind_submissions[2].content['authorids'] == ['{}/Paper{}/Authors'.format(venue['venue_id'], blind_submissions[2].number)]

        # Assert that submissions are private
        assert blind_submissions[0].readers == [venue['venue_id'],
            '{}/Senior_Area_Chairs'.format(venue['venue_id']),
            '{}/Area_Chairs'.format(venue['venue_id']),
            '{}/Reviewers'.format(venue['venue_id']),
            '{}/Paper{}/Authors'.format(venue['venue_id'], blind_submissions[0].number)]
        assert blind_submissions[1].readers == [venue['venue_id'],
            '{}/Senior_Area_Chairs'.format(venue['venue_id']),
            '{}/Area_Chairs'.format(venue['venue_id']),
            '{}/Reviewers'.format(venue['venue_id']),
            '{}/Paper{}/Authors'.format(venue['venue_id'], blind_submissions[1].number)]
        assert blind_submissions[2].readers == [venue['venue_id'],
            '{}/Senior_Area_Chairs'.format(venue['venue_id']),
            '{}/Area_Chairs'.format(venue['venue_id']),
            '{}/Reviewers'.format(venue['venue_id']),
            '{}/Paper{}/Authors'.format(venue['venue_id'], blind_submissions[2].number)]

        invitation = client.get_invitation('{}/-/Request{}/Post_Decision_Stage'.format(venue['support_group_id'], venue['request_form_note'].number))
        invitation.cdate = openreview.tools.datetime_millis(datetime.datetime.utcnow())
        client.post_invitation(invitation)

        invitation = test_client.get_invitation('{}/-/Request{}/Post_Decision_Stage'.format(venue['support_group_id'], venue['request_form_note'].number))

        assert 'Accept' in invitation.reply['content']['home_page_tab_names']['default']
        assert invitation.reply['content']['home_page_tab_names']['default']['Accept'] == 'Accept'
        assert 'Revision Needed' in invitation.reply['content']['home_page_tab_names']['default']
        assert invitation.reply['content']['home_page_tab_names']['default']['Revision Needed'] == 'Revision Needed'
        assert 'Reject' in invitation.reply['content']['home_page_tab_names']['default']
        assert invitation.reply['content']['home_page_tab_names']['default']['Reject'] == 'Reject'

        #Post a post decision note
        now = datetime.datetime.utcnow()
        start_date = now - datetime.timedelta(days=2)
        due_date = now + datetime.timedelta(days=3)
        short_name = 'TestVenue@OR\'2030'
        post_decision_stage_note = test_client.post_note(openreview.Note(
            content={
                'reveal_authors': 'No, I don\'t want to reveal any author identities.',
                'submission_readers': 'Everyone (submissions are public)',
                'home_page_tab_names': {
                    'Accept': 'Accept',
                    'Revision Needed': 'Revision Needed',
                    'Reject': 'Reject'
                },
                'send_decision_notifications': 'Yes, send an email notification to the authors',
                'accept_email_content': f'''Dear {{{{fullname}}}},

Thank you for submitting your paper, {{{{submission_title}}}}, to {short_name}. We are delighted to inform you that your submission has been accepted. Congratulations!
You can find the final reviews for your paper on the submission page in OpenReview at: {{{{forum_url}}}}

Best,
{short_name} Program Chairs
''',
                'reject_email_content': f'''Dear {{{{fullname}}}},

Thank you for submitting your paper, {{{{submission_title}}}}, to {short_name}. We regret to inform you that your submission was not accepted. 
You can find the final reviews for your paper on the submission page in OpenReview at: {{{{forum_url}}}}

Best,
{short_name} Program Chairs
''',
                'revision_needed_email_content': f'''Dear {{{{fullname}}}},

Thank you for submitting your paper, {{{{submission_title}}}}, to {short_name}.
You can find the final reviews for your paper on the submission page in OpenReview at: {{{{forum_url}}}}

Best,
{short_name} Program Chairs
'''
            },
            forum=venue['request_form_note'].forum,
            invitation='{}/-/Request{}/Post_Decision_Stage'.format(venue['support_group_id'], venue['request_form_note'].number),
            readers=['{}/Program_Chairs'.format(venue['venue_id']), venue['support_group_id']],
            referent=venue['request_form_note'].forum,
            replyto=venue['request_form_note'].forum,
            signatures=['~SomeFirstName_User1'],
            writers=[]
        ))
        assert post_decision_stage_note
        helpers.await_queue()

        process_logs = client.get_process_logs(id = post_decision_stage_note.id)
        assert len(process_logs) == 1
        assert process_logs[0]['status'] == 'ok'

        conference = openreview.get_conference(client, request_form_id=venue['request_form_note'].forum)
        recruitment_invitations = client.get_invitations(regex=conference.get_invitation_id('Recruit_.*'), expired=True)
        assert recruitment_invitations
        for inv in recruitment_invitations:
            assert inv.duedate < round(time.time() * 1000)

        blind_submissions = client.get_notes(invitation='{}/-/Blind_Submission'.format(venue['venue_id']), sort='number:asc')
        assert blind_submissions and len(blind_submissions) == 3

        assert blind_submissions[0].content['authors'] == ['Anonymous']
        assert blind_submissions[0].content['authorids'] == ['{}/Paper{}/Authors'.format(venue['venue_id'], blind_submissions[0].number)]
        assert blind_submissions[1].content['authors'] == ['Anonymous']
        assert blind_submissions[1].content['authorids'] == ['{}/Paper{}/Authors'.format(venue['venue_id'], blind_submissions[1].number)]
        assert blind_submissions[2].content['authors'] == ['Anonymous']
        assert blind_submissions[2].content['authorids'] == ['{}/Paper{}/Authors'.format(venue['venue_id'], blind_submissions[2].number)]

        last_message = client.get_messages(to='venue_author1@mail.com')[-1]
        assert "[TestVenue@OR'2030] Decision notification for your submission 1: test submission" in last_message['content']['subject']
        assert last_message['content']['text'] == f'''Dear Venue Author,

Thank you for submitting your paper, test submission, to TestVenue@OR'2030. We regret to inform you that your submission was not accepted. 
You can find the final reviews for your paper on the submission page in OpenReview at: https://openreview.net/forum?id={blind_submissions[0].id}

Best,
TestVenue@OR'2030 Program Chairs
'''

        test_client.post_note(post_decision_stage_note)
        helpers.await_queue()

        decision_messages = client.get_messages(subject="[TestVenue@OR'2030] Decision notification for your submission 1: test submission")
        assert len(decision_messages) == 1

        # Assert that submissions are public
        assert blind_submissions[0].readers == ['everyone']
        assert blind_submissions[1].readers == ['everyone']
        assert blind_submissions[2].readers == ['everyone']

        #check venue and venueid for accepted, venue for rejected
        submissions = client.get_notes(invitation='{}/-/Blind_Submission'.format(venue['venue_id']), sort='number:asc')
        assert submissions and len(submissions) == 3

        assert 'venue' in submissions[0].content and 'Submitted to TestVenue@OR\'2030' in submissions[0].content['venue']
        assert 'venueid' in submissions[0].content and 'TEST.cc/2030/Conference' in submissions[0].content['venueid']
        assert 'venueid' in submissions[1].content and 'TEST.cc/2030/Conference' in submissions[1].content['venueid']
        assert 'venue' in submissions[1].content and 'TestVenue@OR\'2030' in submissions[1].content['venue']

        note_id = submissions[0].id
        assert '_bibtex' in submissions[0].content and submissions[0].content['_bibtex'] == '''@misc{
anonymous''' + str(datetime.datetime.today().year) + '''test,
title={test submission},
author={Anonymous},
year={''' + str(datetime.datetime.today().year) + '''},
url={https://openreview.net/forum?id='''+ note_id + '''}
}'''

        # Post another revision stage note
        now = datetime.datetime.utcnow()
        start_date = now - datetime.timedelta(days=2)
        due_date = now + datetime.timedelta(days=5)
        revision_stage_note = test_client.post_note(openreview.Note(
            content={
                'submission_revision_name': 'Camera_Ready_Revision',
                'submission_revision_start_date': start_date.strftime('%Y/%m/%d'),
                'submission_revision_deadline': due_date.strftime('%Y/%m/%d'),
                'accepted_submissions_only': 'Enable revision for all submissions',
                'submission_author_edition': 'Allow reorder of existing authors only',
                'submission_revision_remove_options': ['keywords']
            },
            forum=venue['request_form_note'].forum,
            invitation='{}/-/Request{}/Submission_Revision_Stage'.format(venue['support_group_id'], venue['request_form_note'].number),
            readers=['{}/Program_Chairs'.format(venue['venue_id']), venue['support_group_id']],
            referent=venue['request_form_note'].forum,
            replyto=venue['request_form_note'].forum,
            signatures=['~SomeFirstName_User1'],
            writers=[]
        ))
        assert revision_stage_note

        helpers.await_queue()
        process_logs = client.get_process_logs(id=revision_stage_note.id)
        assert len(process_logs) == 1
        assert process_logs[0]['status'] == 'ok'

        revision_invitations = client.get_all_invitations(super='{}/-/Revision'.format(venue['venue_id']))
        for invitation in revision_invitations:
            assert invitation.expdate < round(time.time() * 1000)

        blind_submissions = client.get_notes(invitation='{}/-/Blind_Submission'.format(venue['venue_id']), sort='number:asc')
        assert blind_submissions and len(blind_submissions) == 3

        assert blind_submissions[0].content['authors'] == ['Anonymous']
        assert blind_submissions[0].content['authorids'] == ['{}/Paper{}/Authors'.format(venue['venue_id'], blind_submissions[0].number)]
        assert blind_submissions[1].content['authors'] == ['Anonymous']
        assert blind_submissions[1].content['authorids'] == ['{}/Paper{}/Authors'.format(venue['venue_id'], blind_submissions[1].number)]
        assert blind_submissions[2].content['authors'] == ['Anonymous']
        assert blind_submissions[2].content['authorids'] == ['{}/Paper{}/Authors'.format(venue['venue_id'], blind_submissions[2].number)]

        # Assert that submissions are still public
        assert blind_submissions[0].readers == ['everyone']
        assert blind_submissions[1].readers == ['everyone']
        assert blind_submissions[2].readers == ['everyone']

        #Assert venue, venueid and bibtex were not overwritten
        conference = openreview.get_conference(client, request_form_id=venue['request_form_note'].forum)
        conference.setup_post_submission_stage(force=True)

        submissions = client.get_notes(invitation='{}/-/Blind_Submission'.format(venue['venue_id']), sort='number:asc')
        assert submissions and len(submissions) == 3

        assert 'venue' in submissions[0].content and 'Submitted to TestVenue@OR\'2030' in submissions[0].content['venue']
        assert 'venueid' in submissions[0].content and 'TEST.cc/2030/Conference' in submissions[0].content['venueid']
        assert 'venueid' in submissions[1].content and 'TEST.cc/2030/Conference' in submissions[1].content['venueid']
        assert 'venue' in submissions[1].content and 'TestVenue@OR\'2030' in submissions[1].content['venue']

        note_id = submissions[0].id
        assert '_bibtex' in submissions[0].content and submissions[0].content['_bibtex'] == '''@misc{
anonymous''' + str(datetime.datetime.today().year) + '''test,
title={test submission},
author={Anonymous},
year={''' + str(datetime.datetime.today().year) + '''},
url={https://openreview.net/forum?id='''+ note_id + '''}
}'''

        # Post revision note for a submission
        author_client = openreview.Client(username='venue_author3@mail.com', password='1234')
        with pytest.raises(openreview.OpenReviewException, match=r'The value Venue Author,Andrew McCallum in field authors does not match the invitation definition'):
            revision_note = author_client.post_note(openreview.Note(
                invitation='{}/Paper{}/-/Camera_Ready_Revision'.format(venue['venue_id'], blind_submissions[2].number),
                forum=blind_submissions[2].original,
                referent=blind_submissions[2].original,
                replyto=blind_submissions[2].original,
                readers=[venue['venue_id'], '{}/Paper{}/Authors'.format(venue['venue_id'], blind_submissions[2].number)],
                writers=['{}/Paper{}/Authors'.format(venue['venue_id'], blind_submissions[2].number), venue['venue_id']],
                signatures=['{}/Paper{}/Authors'.format(venue['venue_id'], blind_submissions[2].number)],
                content={
                    'title': 'camera ready revised test submission 3',
                    'abstract': 'revised abstract 3',
                    'authors': ['Venue Author', 'Andrew McCallum'],
                    'authorids': ['~Venue_Author3', 'mccallum@gmail.com']
                }
            ))

    def test_venue_public_comment_stage(self, client, test_client, selenium, request_page, helpers, venue):

        conference = openreview.get_conference(client, request_form_id=venue['request_form_note'].forum)
        blind_submissions = client.get_notes(invitation='{}/-/Blind_Submission'.format(venue['venue_id']), sort='tmdate')
        assert blind_submissions and len(blind_submissions) == 3

        # Post an official comment stage note
        now = datetime.datetime.utcnow()
        start_date = now - datetime.timedelta(days=2)
        end_date = now + datetime.timedelta(days=3)
        comment_stage_note = test_client.post_note(openreview.Note(
            content={
                'commentary_start_date': start_date.strftime('%Y/%m/%d'),
                'commentary_end_date': end_date.strftime('%Y/%m/%d'),
                'participants': ['Program Chairs', 'Assigned Area Chairs', 'Assigned Reviewers', 'Authors', 'Public (non-anonymously)'],
                'email_program_chairs_about_official_comments': 'Yes, email PCs for each official comment made in the venue'

            },
            forum=venue['request_form_note'].forum,
            invitation='{}/-/Request{}/Comment_Stage'.format(venue['support_group_id'], venue['request_form_note'].number),
            readers=['{}/Program_Chairs'.format(venue['venue_id']), venue['support_group_id']],
            referent=venue['request_form_note'].forum,
            replyto=venue['request_form_note'].forum,
            signatures=['~SomeFirstName_User1'],
            writers=[]
        ))
        assert comment_stage_note
        helpers.await_queue()

        process_logs = client.get_process_logs(id=comment_stage_note.id)
        assert len(process_logs) == 1
        assert process_logs[0]['status'] == 'ok'

        # Assert that official comment invitation is now available
        official_comment_invitation = openreview.tools.get_invitation(client, conference.get_invitation_id('Official_Comment', number=1))
        assert official_comment_invitation

        # Assert that public comment invitation is not available
        public_comment_invitation = openreview.tools.get_invitation(client, conference.get_invitation_id('Public_Comment', number=1))
        assert public_comment_invitation


    def test_release_reviews(self, client, test_client, selenium, request_page, helpers, venue):

        # Post a review stage note
        now = datetime.datetime.utcnow()
        start_date = now - datetime.timedelta(days=2)
        due_date = now + datetime.timedelta(days=3)
        review_stage_note = test_client.post_note(openreview.Note(
            content={
                'review_start_date': start_date.strftime('%Y/%m/%d'),
                'review_deadline': due_date.strftime('%Y/%m/%d'),
                'make_reviews_public': 'Yes, reviews should be revealed publicly when they are posted',
                'release_reviews_to_authors': 'Yes, reviews should be revealed when they are posted to the paper\'s authors',
                'release_reviews_to_reviewers': 'Reviews should be immediately revealed to all reviewers',
                'remove_review_form_options': 'title',
                'email_program_chairs_about_reviews': 'Yes, email program chairs for each review received'
            },
            forum=venue['request_form_note'].forum,
            invitation='{}/-/Request{}/Review_Stage'.format(venue['support_group_id'], venue['request_form_note'].number),
            readers=['{}/Program_Chairs'.format(venue['venue_id']), venue['support_group_id']],
            referent=venue['request_form_note'].forum,
            replyto=venue['request_form_note'].forum,
            signatures=['~SomeFirstName_User1'],
            writers=[]
        ))
        assert review_stage_note
        helpers.await_queue()

        process_logs = client.get_process_logs(id = review_stage_note.id)
        assert len(process_logs) == 1
        assert process_logs[0]['status'] == 'ok'

    def test_supplementary_material_revision(self, client, test_client, selenium, request_page, helpers, venue):

        # Post another revision stage note
        now = datetime.datetime.utcnow()
        start_date = now - datetime.timedelta(days=2)
        due_date = now + datetime.timedelta(days=5)
        revision_stage_note = test_client.post_note(openreview.Note(
            content={
                'submission_revision_name':'Supplementary Material',
                'submission_revision_start_date': start_date.strftime('%Y/%m/%d'),
                'submission_revision_deadline': due_date.strftime('%Y/%m/%d'),
                'accepted_submissions_only': 'Enable revision for all submissions',
                'submission_author_edition': 'Allow addition and removal of authors',
                'submission_revision_remove_options': ['title','authors', 'authorids','abstract','keywords', 'TL;DR'],
                'submission_revision_additional_options': {
                    'supplementary_material': {
                        'description': 'Supplementary material (e.g. code or video). All supplementary material must be self-contained and zipped into a single file.',
                        'order': 10,
                        'value-file': {
                            'fileTypes': [
                                'zip'
                            ],
                            'size': 50
                        },
                        'required': False
                    }
                }
            },
            forum=venue['request_form_note'].forum,
            invitation='{}/-/Request{}/Submission_Revision_Stage'.format(venue['support_group_id'], venue['request_form_note'].number),
            readers=['{}/Program_Chairs'.format(venue['venue_id']), venue['support_group_id']],
            referent=venue['request_form_note'].forum,
            replyto=venue['request_form_note'].forum,
            signatures=['~SomeFirstName_User1'],
            writers=[]
        ))
        assert revision_stage_note

        helpers.await_queue()
        process_logs = client.get_process_logs(id=revision_stage_note.id)
        assert len(process_logs) == 1
        assert process_logs[0]['status'] == 'ok'

        blind_submissions = client.get_notes(invitation='{}/-/Blind_Submission'.format(venue['venue_id']), sort='number:asc')
        assert blind_submissions and len(blind_submissions) == 3

        revision_invitations = client.get_invitations(super='{}/-/Supplementary_Material'.format(venue['venue_id']))
        assert revision_invitations and len(revision_invitations) == 3
        assert len(revision_invitations[0].reply['content'].keys()) == 2
        assert 'supplementary_material' in revision_invitations[0].reply['content']
        assert all(x not in revision_invitations[0].reply['content'] for x in ['title','authors', 'authorids','abstract','keywords', 'TL;DR'])
        assert revision_invitations[0].duedate
        assert revision_invitations[0].expdate

        #make sure homepage webfield was not overwritten after doing get_conference()
        request_page(selenium, "http://localhost:3030/group?id=TEST.cc/2030/Conference", wait_for_element='reject')
        notes_panel = selenium.find_element_by_id('notes')
        assert notes_panel
        tabs = notes_panel.find_element_by_class_name('tabs-container')
        assert tabs
        accepted_panel = selenium.find_element_by_id('accept')
        assert accepted_panel
        accepted_notes = accepted_panel.find_elements_by_class_name('note')
        assert accepted_notes
        assert len(accepted_notes) == 1
        rejected_panel = selenium.find_element_by_id('reject')
        assert rejected_panel
        rejected_notes = rejected_panel.find_elements_by_class_name('note')
        assert rejected_notes
        assert len(rejected_notes) == 2

    def test_withdraw_submission(self, client, test_client, selenium, request_page, helpers, venue):

        blind_submissions = client.get_notes(invitation='TEST.cc/2030/Conference/-/Blind_Submission', sort='number:asc')

        author_client = openreview.Client(username='venue_author1@mail.com', password='1234')

        withdrawal_note = author_client.post_note(openreview.Note(
            invitation = 'TEST.cc/2030/Conference/Paper1/-/Withdraw',
            forum = blind_submissions[0].forum,
            replyto = blind_submissions[0].forum,
            readers = ['TEST.cc/2030/Conference', 
            'TEST.cc/2030/Conference/Program_Chairs',
            'TEST.cc/2030/Conference/Paper1/Senior_Area_Chairs',
            'TEST.cc/2030/Conference/Paper1/Area_Chairs',
            'TEST.cc/2030/Conference/Paper1/Reviewers',
            'TEST.cc/2030/Conference/Paper1/Authors'],
            writers = ['TEST.cc/2030/Conference', 'TEST.cc/2030/Conference/Program_Chairs'],
            signatures = ['TEST.cc/2030/Conference/Paper1/Authors'],
            content = {
                'title': 'Submission Withdrawn by the Authors',
                'withdrawal confirmation': 'I have read and agree with the venue\'s withdrawal policy on behalf of myself and my co-authors.'
            }
        ))

        helpers.await_queue()    
