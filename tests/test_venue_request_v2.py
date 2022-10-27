import json
import re

import openreview
import pytest
import time
import datetime
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from openreview import VenueRequest
import csv
import os
import random

from openreview.api import OpenReviewClient
from openreview.api import Note

class TestVenueRequest():

    @pytest.fixture(scope='class')
    def venue(self, client, test_client, helpers, openreview_client):
        super_id = 'openreview.net'
        support_group_id = super_id + '/Support'
        VenueRequest(client, support_group_id, super_id)

        helpers.await_queue()

        # Add support group user to the support group object
        support_group = client.get_group(support_group_id)
        client.add_members_to_group(group=support_group, members=['~Support_User1'])

        now = datetime.datetime.utcnow()
        due_date = now.replace(hour=0, minute=0, second=0, microsecond=0) + datetime.timedelta(days=3)
        withdraw_exp_date = due_date + datetime.timedelta(days=1)

        # Post the request form note
        request_form_note = openreview.Note(
            invitation=support_group_id +'/-/Request_Form',
            signatures=['~SomeFirstName_User1'],
            readers=[
                support_group_id,
                '~SomeFirstName_User1',
                'test@mail.com',
                'tom_venue@mail.com'
            ],
            writers=[],
            content={
                'title': 'Test 2030 Venue V2',
                'Official Venue Name': 'Test 2030 Venue V2',
                'Abbreviated Venue Name': "TestVenue@OR'2030V2",
                'Official Website URL': 'https://testvenue2030.gitlab.io/venue/',
                'program_chair_emails': [
                    'test@mail.com',
                    'tom_venue@mail.com'],
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
                'area_chair_identity': ['Program Chairs', 'Assigned Senior Area Chair'],
                'senior_area_chair_identity': ['Program Chairs', 'Assigned Senior Area Chair'],
                'withdraw_submission_expiration': withdraw_exp_date.strftime('%Y/%m/%d'),
                'api_version': '2'
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
            content={'venue_id': 'V2.cc/2030/Conference'},
            forum=request_form_note.forum,
            invitation='{}/-/Request{}/Deploy'.format(support_group_id, request_form_note.number),
            readers=[support_group_id],
            referent=request_form_note.forum,
            replyto=request_form_note.forum,
            signatures=[support_group_id],
            writers=[support_group_id]
        ))

        helpers.await_queue()

        submission_inv = openreview_client.get_invitation('V2.cc/2030/Conference/-/Submission')
        assert submission_inv.duedate == openreview.tools.datetime_millis(due_date)
        assert submission_inv.expdate == openreview.tools.datetime_millis(due_date + datetime.timedelta(minutes = 30))

        # Return venue details as a dict
        venue_details = {
            'request_form_note': request_form_note,
            'support_group_id': support_group_id,
            'venue_id': 'V2.cc/2030/Conference'
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

    def test_venue_deployment(self, client, selenium, request_page, helpers, openreview_client):

        super_id = 'openreview.net'
        support_group_id = super_id + '/Support'
        venue = VenueRequest(client, support_group_id, super_id)

        helpers.await_queue()
        request_page(selenium, 'http://localhost:3030/group?id={}&mode=default'.format(support_group_id), client.token)

        helpers.create_user('pc_venue_v2@mail.com', 'ProgramChair', 'User')

        support_group = client.get_group(support_group_id)
        client.add_members_to_group(group=support_group, members=['~Support_User1'])

        support_members = client.get_group(support_group_id).members
        assert support_members and len(support_members) == 1

        now = datetime.datetime.utcnow()
        start_date = now - datetime.timedelta(days=2)
        abstract_due_date = now + datetime.timedelta(minutes=15)
        due_date = now + datetime.timedelta(minutes=30)
        withdraw_exp_date = now + datetime.timedelta(hours=1)

        request_form_note = client.post_note(openreview.Note(
            invitation=support_group_id +'/-/Request_Form',
            signatures=['~ProgramChair_User1'],
            readers=[
                support_group_id,
                '~ProgramChair_User1',
                'pc_venue_v2@mail.com',
                'tom_venue@mail.com'
            ],
            writers=[],
            content={
                'title': 'Test 2022 Venue',
                'Official Venue Name': 'Test 2022 Venue',
                'Abbreviated Venue Name': 'TestVenue@OR2022',
                'Official Website URL': 'https://testvenue2021.gitlab.io/venue/',
                'program_chair_emails': [
                    'pc_venue_v2@mail.com',
                    'tom_venue@mail.com'],
                'contact_email': 'pc_venue_v2@mail.com',
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
                'submission_name': 'Submission_Test',
                'api_version': '2'
            }))

        assert request_form_note
        request_page(selenium, 'http://localhost:3030/forum?id=' + request_form_note.forum, client.token)

        messages = client.get_messages(
            to='pc_venue_v2@mail.com',
            subject='Your request for OpenReview service has been received.')
        assert messages and len(messages) == 1
        assert messages[0]['content']['text'] == f'Thank you for choosing OpenReview to host your upcoming venue. We are reviewing your request and will post a comment on the request forum when the venue is deployed. You can access the request forum here: https://openreview.net/forum?id={request_form_note.forum}'

        messages = client.get_messages(
            to='support@openreview.net',
            subject='A request for service has been submitted by TestVenue@OR2022'
        )
        assert messages and len(messages) == 1
        assert messages[0]['content']['text'].startswith(f'A request for service has been submitted by TestVenue@OR2022. Check it here: https://openreview.net/forum?id={request_form_note.forum}')

        client.post_note(openreview.Note(
            content={
                'title': 'Urgent',
                'comment': 'Please deploy ASAP.'
            },
            forum=request_form_note.forum,
            invitation='{}/-/Request{}/Comment'.format(venue.support_group_id, request_form_note.number),
            readers=[
                support_group_id,
                'pc_venue_v2@mail.com',
                'tom_venue@mail.com'
            ],
            replyto=None,
            signatures=['~ProgramChair_User1'],
            writers=[]
        ))

        helpers.await_queue()

        # Test Deploy
        deploy_note = client.post_note(openreview.Note(
            content={'venue_id': 'V2.cc/2022/Conference'},
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

        assert openreview.tools.get_group(openreview_client, 'V2.cc/2022')
        assert openreview.tools.get_group(openreview_client, 'V2.cc')
        assert openreview.tools.get_invitation(openreview_client, 'V2.cc/2022/Conference/-/Submission_Test')
        assert not openreview.tools.get_invitation(openreview_client, 'V2.cc/2022/Conference/-/Submission')

        comment_invitation = '{}/-/Request{}/Comment'.format(venue.support_group_id,
                                                             request_form_note.number)
        last_comment = client.get_notes(invitation=comment_invitation, sort='tmdate')[-1]
        assert 'V2.cc/2022/Conference/Program_Chairs' in last_comment.readers

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
        signatures=['~ProgramChair_User1'],
        writers=[]
        )

        with pytest.raises(openreview.OpenReviewException, match=r'Author identities of desk-rejected submissions can only be anonymized for double-blind submissions'):
            client.post_note(venue_revision_note)

        venue_revision_note.content['desk_rejected_submissions_author_anonymity'] = 'Yes, author identities of desk rejected submissions should be revealed.'
        venue_revision_note=client.post_note(venue_revision_note)

        assert openreview_client.get_invitation('V2.cc/2022/Conference/-/Submission_Test')

#     def test_venue_revision_error(self, client, test_client, selenium, request_page, venue, helpers):

#         # Test Revision
#         request_page(selenium, 'http://localhost:3030/group?id={}'.format(venue['venue_id']), test_client.token, wait_for_element='header')
#         header_div = selenium.find_element_by_id('header')
#         assert header_div
#         title_tag = header_div.find_element_by_tag_name('h1')
#         assert title_tag
#         assert title_tag.text == venue['request_form_note'].content['title']

#         messages = client.get_messages(subject='Comment posted to your request for service: {}'.format(venue['request_form_note'].content['title']))
#         assert messages and len(messages) == 2
#         recipients = [msg['content']['to'] for msg in messages]
#         assert 'test@mail.com' in recipients
#         assert 'tom_venue@mail.com' in recipients
#         assert 'Venue home page: <a href=\"https://openreview.net/group?id=TEST.cc/2030/Conference\">https://openreview.net/group?id=TEST.cc/2030/Conference</a>' in messages[0]['content']['text']
#         assert 'Venue Program Chairs console: <a href=\"https://openreview.net/group?id=TEST.cc/2030/Conference/Program_Chairs\">https://openreview.net/group?id=TEST.cc/2030/Conference/Program_Chairs</a>' in messages[0]['content']['text']

#         now = datetime.datetime.utcnow()
#         start_date = now - datetime.timedelta(days=2)
#         due_date = now + datetime.timedelta(days=3)

#         venue_revision_note = test_client.post_note(openreview.Note(
#             content={
#                 'title': '{} Updated'.format(venue['request_form_note'].content['title']),
#                 'Official Venue Name': '{} Updated'.format(venue['request_form_note'].content['title']),
#                 'Abbreviated Venue Name': venue['request_form_note'].content['Abbreviated Venue Name'],
#                 'Official Website URL': venue['request_form_note'].content['Official Website URL'],
#                 'program_chair_emails': venue['request_form_note'].content['program_chair_emails'],
#                 'Expected Submissions': '100',
#                 'How did you hear about us?': 'ML conferences',
#                 'Location': 'Virtual',
#                 'Submission Deadline': due_date.strftime('%Y/%m/%d %H:%M'),
#                 'Venue Start Date': start_date.strftime('%Y/%m/%d'),
#                 'contact_email': venue['request_form_note'].content['contact_email'],
#                 'remove_submission_options': ['pdf'],
#                 'email_pcs_for_new_submissions': 'Yes, email PCs for every new submission.',
#                 'Additional Submission Options': {
#                     'preprint': {
#                         'value-regexx': '.*'
#                     }
#                 }
#             },
#             forum=venue['request_form_note'].forum,
#             invitation='{}/-/Request{}/Revision'.format(venue['support_group_id'], venue['request_form_note'].number),
#             readers=['{}/Program_Chairs'.format(venue['venue_id']), venue['support_group_id']],
#             referent=venue['request_form_note'].forum,
#             replyto=venue['request_form_note'].forum,
#             signatures=['~SomeFirstName_User1'],
#             writers=[]
#         ))
#         assert venue_revision_note

#         helpers.await_queue()
#         process_logs = client.get_process_logs(id=venue_revision_note.id)
#         assert len(process_logs) == 1
#         assert process_logs[0]['status'] == 'ok'
#         assert process_logs[0]['invitation'] == '{}/-/Request{}/Revision'.format(venue['support_group_id'], venue['request_form_note'].number)

#         comment_invitation = '{}/-/Request{}/Stage_Error_Status'.format(venue['support_group_id'],
#                                                              venue['request_form_note'].number)
#         last_comment = client.get_notes(invitation=comment_invitation, sort='tmdate')[0]
#         error = last_comment.content['error']
#         assert 'InvalidFieldError' in error
#         assert 'The field value-regexx is not allowed' in error

#     def test_venue_revision(self, client, test_client, selenium, request_page, venue, helpers):

#         # Test Revision
#         request_page(selenium, 'http://localhost:3030/group?id={}'.format(venue['venue_id']), test_client.token, wait_for_element='header')
#         header_div = selenium.find_element_by_id('header')
#         assert header_div
#         title_tag = header_div.find_element_by_tag_name('h1')
#         assert title_tag
#         assert title_tag.text == venue['request_form_note'].content['title']

#         messages = client.get_messages(subject='Comment posted to your request for service: {}'.format(venue['request_form_note'].content['title']))
#         assert messages and len(messages) == 2
#         recipients = [msg['content']['to'] for msg in messages]
#         assert 'test@mail.com' in recipients
#         assert 'tom_venue@mail.com' in recipients
#         assert 'Venue home page: <a href=\"https://openreview.net/group?id=TEST.cc/2030/Conference\">https://openreview.net/group?id=TEST.cc/2030/Conference</a>' in messages[0]['content']['text']
#         assert 'Venue Program Chairs console: <a href=\"https://openreview.net/group?id=TEST.cc/2030/Conference/Program_Chairs\">https://openreview.net/group?id=TEST.cc/2030/Conference/Program_Chairs</a>' in messages[0]['content']['text']

#         now = datetime.datetime.utcnow()
#         start_date = now - datetime.timedelta(days=2)
#         due_date = now + datetime.timedelta(days=3)

#         venue_revision_note = test_client.post_note(openreview.Note(
#             content={
#                 'title': '{} Updated'.format(venue['request_form_note'].content['title']),
#                 'Official Venue Name': '{} Updated'.format(venue['request_form_note'].content['title']),
#                 'Abbreviated Venue Name': venue['request_form_note'].content['Abbreviated Venue Name'],
#                 'Official Website URL': venue['request_form_note'].content['Official Website URL'],
#                 'program_chair_emails': venue['request_form_note'].content['program_chair_emails'],
#                 'Expected Submissions': '100',
#                 'How did you hear about us?': 'ML conferences',
#                 'Location': 'Virtual',
#                 'Submission Deadline': due_date.strftime('%Y/%m/%d %H:%M'),
#                 'Venue Start Date': start_date.strftime('%Y/%m/%d'),
#                 'contact_email': venue['request_form_note'].content['contact_email'],
#                 'remove_submission_options': ['pdf'],
#                 'email_pcs_for_new_submissions': 'Yes, email PCs for every new submission.',
#                 'Additional Submission Options': {
#                     'preprint': {
#                         'value-regex': '.*'
#                     }
#                 }
#             },
#             forum=venue['request_form_note'].forum,
#             invitation='{}/-/Request{}/Revision'.format(venue['support_group_id'], venue['request_form_note'].number),
#             readers=['{}/Program_Chairs'.format(venue['venue_id']), venue['support_group_id']],
#             referent=venue['request_form_note'].forum,
#             replyto=venue['request_form_note'].forum,
#             signatures=['~SomeFirstName_User1'],
#             writers=[]
#         ))
#         assert venue_revision_note

#         helpers.await_queue()
#         process_logs = client.get_process_logs(id=venue_revision_note.id)
#         assert len(process_logs) == 1
#         assert process_logs[0]['status'] == 'ok'
#         assert process_logs[0]['invitation'] == '{}/-/Request{}/Revision'.format(venue['support_group_id'], venue['request_form_note'].number)

#         request_page(selenium, 'http://localhost:3030/group?id={}'.format(venue['venue_id']), test_client.token, wait_for_element='header')
#         header_div = selenium.find_element_by_id('header')
#         assert header_div
#         title_tag = header_div.find_element_by_tag_name('h1')
#         assert title_tag
#         assert title_tag.text == '{} Updated'.format(venue['request_form_note'].content['title'])

#         conference = openreview.get_conference(client, request_form_id=venue['request_form_note'].forum)
#         submission_due_date_str = due_date.strftime('%b %d %Y %I:%M%p')
#         assert conference.homepage_header['deadline'] == 'Submission Start:  UTC-0, End: ' + submission_due_date_str + ' UTC-0'
#         assert openreview.tools.get_invitation(client, conference.submission_stage.get_withdrawn_submission_id(conference)) is None

    def test_venue_recruitment_email_error(self, client, test_client, selenium, request_page, venue, helpers):

        # Test Reviewer Recruitment
        # request_page(selenium, 'http://localhost:3030/forum?id={}'.format(venue['request_form_note'].id), test_client.token, wait_for_element=f"note_{venue['request_form_note'].id}")
        # recruitment_div = selenium.find_element_by_id('note_{}'.format(venue['request_form_note'].id))
        # assert recruitment_div
        # reply_row = recruitment_div.find_element_by_class_name('reply_row')
        # assert reply_row
        # buttons = reply_row.find_elements_by_class_name('btn-xs')
        # assert [btn for btn in buttons if btn.text == 'Recruitment']
        reviewer_details = '''reviewer_candidate1_v2@mail.com, Reviewer One\nreviewer_candidate2_v2@mail.com, Reviewer Two'''
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

        messages = client.get_messages(to='reviewer_candidate1_v2@mail.com')
        assert not messages
        messages = client.get_messages(to='reviewer_candidate2_v2@mail.com')
        assert not messages

        recruitment_status_invitation = '{}/-/Request{}/Recruitment_Status'.format(venue['support_group_id'],
                                                             venue['request_form_note'].number)
        last_comment = client.get_notes(invitation=recruitment_status_invitation, sort='tmdate')[0]
        error_string = '{\n ' \
                       ' "KeyError(\'program\')": [\n' \
                       '    "reviewer_candidate1_v2@mail.com",\n' \
                       '    "reviewer_candidate2_v2@mail.com"\n' \
                       '  ]\n' \
                       '}'
        assert error_string in last_comment.content['error']
        assert '0 users' in last_comment.content['invited']

    def test_venue_recruitment(self, client, test_client, selenium, request_page, venue, helpers, openreview_client):

        # Test Reviewer Recruitment
        # request_page(selenium, 'http://localhost:3030/forum?id={}'.format(venue['request_form_note'].id), test_client.token, wait_for_element=f"note_{venue['request_form_note'].id}")
        # recruitment_div = selenium.find_element_by_id('note_{}'.format(venue['request_form_note'].id))
        # assert recruitment_div
        # reply_row = recruitment_div.find_element_by_class_name('reply_row')
        # assert reply_row
        # buttons = reply_row.find_elements_by_class_name('btn-xs')
        # assert [btn for btn in buttons if btn.text == 'Recruitment']
        reviewer_details = '''reviewer_candidate1_v2@mail.com, Reviewer One\nreviewer_candidate2_v2@mail.com, Reviewer Two'''
        recruitment_note = test_client.post_note(openreview.Note(
            content={
                'title': 'Recruitment',
                'invitee_role': 'Reviewers',
                'invitee_reduced_load': ['1', '2', '3'],
                'invitee_details': reviewer_details,
                'invitation_email_subject': '[' + venue['request_form_note'].content['Abbreviated Venue Name'] + '] Invitation to serve as {{invitee_role}}',
                'invitation_email_content': 'Dear {{fullname}},\n\nYou have been nominated by the program chair committee of Test 2030 Venue V2 to serve as {{invitee_role}}.\n\nTo respond to the invitation, please click on the following link:\n\n{{invitation_url}}\n\nCheers!\n\nProgram Chairs'
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

        messages = client.get_messages(to='reviewer_candidate1_v2@mail.com')
        assert messages and len(messages) == 1
        assert messages[0]['content']['subject'] == "[TestVenue@OR'2030V2] Invitation to serve as Reviewer"
        assert messages[0]['content']['text'].startswith('Dear Reviewer One,\n\nYou have been nominated by the program chair committee of Test 2030 Venue V2 to serve as Reviewer.')

        messages = client.get_messages(to='reviewer_candidate2_v2@mail.com')
        assert messages and len(messages) == 1
        assert messages[0]['content']['subject'] == "[TestVenue@OR'2030V2] Invitation to serve as Reviewer"
        assert messages[0]['content']['text'].startswith('Dear Reviewer Two,\n\nYou have been nominated by the program chair committee of Test 2030 Venue V2 to serve as Reviewer.')

        recruitment_status_invitation = '{}/-/Request{}/Recruitment_Status'.format(venue['support_group_id'],
                                                                                   venue['request_form_note'].number)
        last_comment = client.get_notes(invitation=recruitment_status_invitation, sort='tmdate')[0]
        assert '2 users' in last_comment.content['invited']

        last_message = client.get_messages(to='support@openreview.net')[-1]
        assert 'Recruitment Status' not in last_message['content']['text']

        invalid_accept_url = re.search('https://.*\n', messages[0]['content']['text']).group(0).replace('https://openreview.net', 'http://localhost:3030').replace('&amp;', '&')[:-1].replace('user=reviewer_candidate2_v2%40mail.com', 'user=reviewer_candidate2_v1%40mail.com')
        print(invalid_accept_url)
        helpers.respond_invitation(selenium, request_page, invalid_accept_url, accept=True)
        error_message = selenium.find_element_by_class_name('important_message')
        assert 'Wrong key, please refer back to the recruitment email' == error_message.text

        openreview_client.remove_members_from_group('V2.cc/2030/Conference/Reviewers/Invited', 'reviewer_candidate2_v2@mail.com')
        invitation_url = re.search('https://.*\n', messages[0]['content']['text']).group(0).replace('https://openreview.net', 'http://localhost:3030')[:-1]
        helpers.respond_invitation(selenium, request_page, invitation_url, accept=True)
        error_message = selenium.find_element_by_class_name('important_message')
        assert 'User not in invited group, please accept the invitation using the email address you were invited with' == error_message.text

        openreview_client.add_members_to_group('V2.cc/2030/Conference/Reviewers/Invited', 'reviewer_candidate2_v2@mail.com')

        invitation_url = re.search('https://.*\n', messages[0]['content']['text']).group(0).replace('https://openreview.net', 'http://localhost:3030')[:-1]
        print('invitation_url', invitation_url)
        helpers.respond_invitation(selenium, request_page, invitation_url, accept=True)

        messages = client.get_messages(to='reviewer_candidate2_v2@mail.com', subject="[TestVenue@OR'2030V2] Reviewer Invitation accepted")
        assert messages and len(messages) == 1

        #reinvite reviewer, no email should be sent
        recruitment_note = test_client.post_note(openreview.Note(
            content={
                'title': 'Recruitment',
                'invitee_role': 'Reviewers',
                'invitee_reduced_load': ['1', '2', '3'],
                'invitee_details': 'reviewer_candidate1_v2@mail.com, Reviewer One',
                'invitation_email_subject': '[' + venue['request_form_note'].content['Abbreviated Venue Name'] + '] Invitation to serve as {{invitee_role}}',
                'invitation_email_content': 'Dear {{fullname}},\n\nYou have been nominated by the program chair committee of Test 2030 Venue V2 to serve as {{invitee_role}}.\n\nTo respond to the invitation, please click on the following link:\n\n{{invitation_url}}\n\nCheers!\n\nProgram Chairs'
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

        messages = client.get_messages(to='reviewer_candidate1_v2@mail.com')
        assert messages and len(messages) == 1
        assert messages[0]['content']['subject'] == "[TestVenue@OR'2030V2] Invitation to serve as Reviewer"

        recruitment_status_invitation = '{}/-/Request{}/Recruitment_Status'.format(venue['support_group_id'],
                                                                                   venue['request_form_note'].number)
        last_comment = client.get_notes(invitation=recruitment_status_invitation, sort='tmdate')[0]
        assert '0 users' in last_comment.content['invited']
        assert 'No recruitment invitation was sent to the users listed under \'Already Invited\' because they have already been invited.' in last_comment.content['comment']
        
    def test_venue_recruitment_tilde_IDs(self, client, test_client, selenium, request_page, venue, helpers):

        # Test Reviewer Recruitment
        # request_page(selenium, 'http://localhost:3030/forum?id={}'.format(venue['request_form_note'].id), test_client.token, wait_for_element=f"note_{venue['request_form_note'].id}")
        # recruitment_div = selenium.find_element_by_id('note_{}'.format(venue['request_form_note'].id))
        # assert recruitment_div
        # reply_row = recruitment_div.find_element_by_class_name('reply_row')
        # assert reply_row
        # buttons = reply_row.find_elements_by_class_name('btn-xs')
        # assert [btn for btn in buttons if btn.text == 'Recruitment']
        helpers.create_user('reviewer_one_tilde_v2@mail.com', 'Reviewer', 'OneTildeV')
        helpers.create_user('reviewer_two_tilde_v2@mail.com', 'Reviewer', 'TwoTildeV')
        reviewer_details = '''~Reviewer_OneTildeV1\n~Reviewer_TwoTildeV1'''

        recruitment_note = test_client.post_note(openreview.Note(
            content={
                'title': 'Recruitment',
                'invitee_role': 'Reviewers',
                'invitee_reduced_load': ['2', '4', '6'],
                'invitee_details': reviewer_details,
                'invitation_email_subject': '[' + venue['request_form_note'].content['Abbreviated Venue Name'] + '] Invitation to serve as {{invitee_role}}',
                'invitation_email_content': 'Dear {{fullname}},\n\nYou have been nominated by the program chair committee of Test 2030 Venue V2 to serve as {{invitee_role}}.\n\nTo respond to the invitation, please click on the following link:\n\n{{invitation_url}}\n\nCheers!\n\nProgram Chairs'
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

        messages = client.get_messages(to='reviewer_one_tilde_v2@mail.com')
        assert messages and len(messages) == 2

        assert messages[1]['content']['subject'] == "[TestVenue@OR'2030V2] Invitation to serve as Reviewer"
        assert messages[1]['content']['text'].startswith('Dear Reviewer OneTildeV,\n\nYou have been nominated by the program chair committee of Test 2030 Venue V2 to serve as Reviewer.')

        messages = client.get_messages(to='reviewer_two_tilde_v2@mail.com')
        assert messages and len(messages) == 2
        assert messages[1]['content']['subject'] == "[TestVenue@OR'2030V2] Invitation to serve as Reviewer"
        assert messages[1]['content']['text'].startswith('Dear Reviewer TwoTildeV,\n\nYou have been nominated by the program chair committee of Test 2030 Venue V2 to serve as Reviewer.')

        recruitment_status_invitation = '{}/-/Request{}/Recruitment_Status'.format(venue['support_group_id'],
                                                                                   venue['request_form_note'].number)
        last_comment = client.get_notes(invitation=recruitment_status_invitation, sort='tmdate')[0]
        assert '2 users' in last_comment.content['invited']

    def test_venue_AC_recruitment_(self, client, test_client, selenium, request_page, venue, helpers):

        # Test AC Recruitment

        ac_details = '''ac_one@mail.com\nreviewer_candidate2_v2@mail.com, Reviewer Two'''

        recruitment_note = test_client.post_note(openreview.Note(
            content={
                'title': 'Recruitment',
                'invitee_role': 'Area_Chairs',
                'allow_role_overlap': 'Yes',
                'invitee_reduced_load': ['2', '4', '6'],
                'invitee_details': ac_details,
                'invitation_email_subject': '[' + venue['request_form_note'].content['Abbreviated Venue Name'] + '] Invitation to serve as {{invitee_role}}',
                'invitation_email_content': 'Dear {{fullname}},\n\nYou have been nominated by the program chair committee of Test 2030 Venue V2 to serve as {{invitee_role}}.\n\nTo respond to the invitation, please click on the following link:\n\n{{invitation_url}}\n\nCheers!\n\nProgram Chairs'
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

        messages = client.get_messages(to='ac_one@mail.com')
        assert messages and len(messages) == 1

        assert messages[0]['content']['subject'] == "[TestVenue@OR'2030V2] Invitation to serve as Area Chair"
        assert messages[0]['content']['text'].startswith('Dear invitee,\n\nYou have been nominated by the program chair committee of Test 2030 Venue V2 to serve as Area Chair.')

        messages = client.get_messages(to='reviewer_candidate2_v2@mail.com')
        assert messages and len(messages) == 3
        assert messages[2]['content']['subject'] == "[TestVenue@OR'2030V2] Invitation to serve as Area Chair"
        assert messages[2]['content']['text'].startswith('Dear Reviewer Two,\n\nYou have been nominated by the program chair committee of Test 2030 Venue V2 to serve as Area Chair.')

        recruitment_status_invitation = '{}/-/Request{}/Recruitment_Status'.format(venue['support_group_id'],
                                                                                   venue['request_form_note'].number)
        last_comment = client.get_notes(invitation=recruitment_status_invitation, sort='tmdate')[0]
        assert '2 users' in last_comment.content['invited']

        #accept AC invitation after having accepted reviewer invitation
        invitation_url = re.search('https://.*\n', messages[2]['content']['text']).group(0).replace('https://openreview.net', 'http://localhost:3030')[:-1]
        print('invitation_url', invitation_url)
        helpers.respond_invitation(selenium, request_page, invitation_url, accept=True)

        messages = client.get_messages(to='reviewer_candidate2_v2@mail.com', subject="[TestVenue@OR'2030V2] Area Chair Invitation accepted")
        assert messages and len(messages) == 1

    def test_venue_remind_recruitment(self, client, test_client, selenium, request_page, venue, helpers):

        # Test Reviewer Remind Recruitment
        # request_page(selenium, 'http://localhost:3030/forum?id={}'.format(venue['request_form_note'].id), test_client.token, wait_for_element=f"note_{venue['request_form_note'].id}")
        # recruitment_div = selenium.find_element_by_id('note_{}'.format(venue['request_form_note'].id))
        # assert recruitment_div
        # reply_row = recruitment_div.find_element_by_class_name('reply_row')
        # assert reply_row
        # buttons = reply_row.find_elements_by_class_name('btn-xs')
        # assert [btn for btn in buttons if btn.text == 'Remind Recruitment']

        remind_recruitment_note = test_client.post_note(openreview.Note(
            content={
                'title': 'Remind Recruitment',
                'invitee_role': 'Reviewers',
                'invitation_email_subject': '[' + venue['request_form_note'].content['Abbreviated Venue Name'] + '] Invitation to serve as {{invitee_role}}',
                'invitation_email_content': 'Dear {{fullname}},\n\nYou have been nominated by the program chair committee of Test 2030 Venue V2 to serve as {{invitee_role}}.\n\nTo respond to the invitation, please click on the following link:\n\n{{invitation_url}}\n\nCheers!\n\nProgram Chairs'
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

        messages = client.get_messages(to='reviewer_candidate1_v2@mail.com')
        assert messages and len(messages) == 2
        assert messages[1]['content']['subject'] == "Reminder: [TestVenue@OR'2030V2] Invitation to serve as Reviewer"
        assert messages[1]['content']['text'].startswith('Dear invitee,\n\nYou have been nominated by the program chair committee of Test 2030 Venue V2 to serve as Reviewer.')

        messages = client.get_messages(to='reviewer_candidate2_v2@mail.com', subject="Reminder: [TestVenue@OR'2030V2] Invitation to serve as Reviewer")
        assert not messages

        messages = client.get_messages(to='reviewer_one_tilde_v2@mail.com', subject="Reminder: [TestVenue@OR'2030V2] Invitation to serve as Reviewer")
        assert messages and len(messages) == 1

        messages = client.get_messages(to='reviewer_two_tilde_v2@mail.com', subject="Reminder: [TestVenue@OR'2030V2] Invitation to serve as Reviewer")
        assert messages and len(messages) == 1

        remind_recruitment_status_invitation = '{}/-/Request{}/Remind_Recruitment_Status'.format(venue['support_group_id'],
                                                                                   venue['request_form_note'].number)
        last_comment = client.get_notes(invitation=remind_recruitment_status_invitation, sort='tmdate')[0]
        assert '3 users' in last_comment.content['reminded']

        last_message = client.get_messages(to='support@openreview.net')[-1]
        assert 'Remind Recruitment Status' not in last_message['content']['text']

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

    def test_venue_bid_stage(self, client, test_client, selenium, request_page, helpers, venue, openreview_client):

        reviewer_client = helpers.create_user('venue_reviewer_v2@mail.com', 'VenueTwo', 'Reviewer')

        reviewer_group_id = '{}/Reviewers'.format(venue['venue_id'])
        reviewer_group = client.get_group(reviewer_group_id)
        client.add_members_to_group(reviewer_group, '~VenueTwo_Reviewer1')

        # reviewer_url = 'http://localhost:3030/group?id={}#reviewer-tasks'.format(reviewer_group_id)
        # request_page(selenium, reviewer_url, reviewer_client.token)
        # with pytest.raises(NoSuchElementException):
        #     assert selenium.find_element_by_link_text('Reviewer Bid')

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

        bid_invitation = openreview_client.get_invitation('{}/Reviewers/-/Bid'.format(venue['venue_id']))
        assert bid_invitation

        bid_invitation = openreview_client.get_invitation('{}/Area_Chairs/-/Bid'.format(venue['venue_id']))
        assert bid_invitation

        # request_page(selenium, reviewer_url, reviewer_client.token, By.LINK_TEXT, wait_for_element='Reviewer Bid')
        # assert selenium.find_element_by_link_text('Reviewer Bid')

    def test_venue_matching_setup(self, client, test_client, selenium, request_page, helpers, venue, openreview_client):
        # add a member to PC group
        pc_group = client.get_group('{}/Program_Chairs'.format(venue['venue_id']))
        client.add_members_to_group(group=pc_group, members=['pc@test.com'])

        helpers.create_user('venue_author_v2@mail.com', 'VenueTwo', 'Author')
        author_client = OpenReviewClient(username='venue_author_v2@mail.com', password='1234')
        reviewer_client = helpers.create_user('venue_reviewer_v2_@mail.com', 'VenueThree', 'Reviewer')

        venue_id = venue['venue_id']

        # messages = client.get_messages(subject='{} has received a new submission titled {}'.format(venue['request_form_note'].content['Abbreviated Venue Name'], submission.content['title']))
        # assert messages and len(messages) == 3
        # recipients = [msg['content']['to'] for msg in messages]
        # assert 'test@mail.com' in recipients
        # assert 'tom_venue@mail.com' in recipients
        # assert 'pc@test.com' in recipients

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
                'matching_group':  venue['venue_id'] + '/Reviewers',
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

        submission_note_1 = author_client.post_note_edit(
            invitation=f'{venue_id}/-/Submission',
            signatures= ['~VenueTwo_Author1'],
            note=Note(
                content={
                    'title': { 'value': 'test submission' },
                    'abstract': { 'value': 'test abstract' },
                    'authors': { 'value': ['VenueTwo Author']},
                    'authorids': { 'value': ['~VenueTwo_Author1']},
                    'pdf': {'value': '/pdf/' + 'p' * 40 +'.pdf' },
                    'keywords': {'value': ['aa'] }
                }
            ))

        helpers.await_queue_edit(openreview_client, edit_id=submission_note_1['id']) 

        helpers.create_user('venue_author_v2_2@mail.com', 'VenueThree', 'Author')
        author_client2 = OpenReviewClient(username='venue_author_v2_2@mail.com', password='1234')

        submission_note_2 = author_client2.post_note_edit(
            invitation=f'{venue_id}/-/Submission',
            signatures= ['~VenueThree_Author1'],
            note=Note(
                content={
                    'title': { 'value': 'test submission 2' },
                    'abstract': { 'value': 'test abstract' },
                    'authors': { 'value': ['VenueThree Author']},
                    'authorids': { 'value': ['~VenueThree_Author1']},
                    'pdf': {'value': '/pdf/' + 'p' * 40 +'.pdf' },
                    'keywords': {'value': ['aa'] }
                }
        ))
        
        helpers.await_queue_edit(openreview_client, edit_id=submission_note_2['id']) 

        conference.setup_post_submission_stage(force=True)

        submissions = openreview_client.get_notes(invitation='{}/-/Submission'.format(venue['venue_id']), sort='tmdate')
        assert submissions and len(submissions) == 2

        reviewer_group = client.get_group('{}/Reviewers'.format(venue['venue_id']))
        client.remove_members_from_group(reviewer_group, '~VenueTwo_Reviewer1')
        client.remove_members_from_group(reviewer_group, 'reviewer_candidate2_v2@mail.com')

        ## Remove ~VenueTwo_Reviewer1 to keep the group empty and run the setup matching
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

        client.add_members_to_group(reviewer_group, '~VenueTwo_Reviewer1')
        client.add_members_to_group(reviewer_group, '~VenueThree_Reviewer1')
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

        with open(os.path.join(os.path.dirname(__file__), 'data/rev_scores_venue.csv'), 'w') as file_handle:
            writer = csv.writer(file_handle)
            for submission in submissions:
                writer.writerow([submission.id, '~VenueTwo_Reviewer1', round(random.random(), 2)])
                writer.writerow([submission.id, '~VenueThree_Reviewer1', round(random.random(), 2)])


        url = test_client.put_attachment(os.path.join(os.path.dirname(__file__), 'data/rev_scores_venue.csv'), matching_setup_invitation, 'upload_affinity_scores')

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
        assert matching_status.content['without_profile'] == ['some_user@mail.com']
        assert '''
1 Reviewers without a profile.

Affinity scores and/or conflicts could not be computed for the users listed under 'Without Profile'. You will not be able to run the matcher until all Reviewers have profiles. You have two options:

1. You can ask these users to sign up in OpenReview and upload their papers. After all Reviewers have done this, you will need to rerun the paper matching setup to recompute conflicts and/or affinity scores for all users.
2. You can remove these users from the Reviewers group: https://openreview.net/group/edit?id=V2.cc/2030/Conference/Reviewers. You can find all users without a profile by searching for the '@' character in the search box.
''' in matching_status.content['comment']

        scores_invitation = openreview_client.get_invitation(conference.get_invitation_id('Affinity_Score', prefix=reviewer_group.id))
        assert scores_invitation
        affinity_scores = openreview_client.get_edges(invitation=scores_invitation.id)
        assert len(affinity_scores) == 4

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
        assert matching_status.content['comment'] == '''Affinity scores and/or conflicts were successfully computed. To run the matcher, click on the 'Reviewers Paper Assignment' link in the PC console: https://openreview.net/group?id=V2.cc/2030/Conference/Program_Chairs

Please refer to the FAQ for pointers on how to run the matcher: https://openreview.net/faq#question-edge-browswer'''

        scores_invitation = openreview_client.get_invitation(conference.get_invitation_id('Affinity_Score', prefix=reviewer_group.id))
        assert scores_invitation
        affinity_scores = openreview_client.get_edges(invitation=scores_invitation.id)
        assert len(affinity_scores) == 4

        last_message = client.get_messages(to='support@openreview.net')[-1]
        assert 'Paper Matching Setup Status' not in last_message['content']['text']
        last_message = client.get_messages(to='test@mail.com')[-1]
        assert 'Paper Matching Setup Status' in last_message['content']['subject']

#     def test_update_withdraw_submission_due_date(self, client, test_client, selenium, request_page, helpers, venue):
#         now = datetime.datetime.utcnow()
#         start_date = now - datetime.timedelta(days=2)
#         due_date = now + datetime.timedelta(days=3)
#         withdraw_exp_date = now + datetime.timedelta(days=1)
#         withdraw_exp_date = withdraw_exp_date.strftime('%Y/%m/%d')
#         venue_revision_note = test_client.post_note(openreview.Note(
#             content={
#                 'title': '{} Updated'.format(venue['request_form_note'].content['title']),
#                 'Official Venue Name': '{} Updated'.format(venue['request_form_note'].content['title']),
#                 'Abbreviated Venue Name': venue['request_form_note'].content['Abbreviated Venue Name'],
#                 'Official Website URL': venue['request_form_note'].content['Official Website URL'],
#                 'program_chair_emails': venue['request_form_note'].content['program_chair_emails'],
#                 'Expected Submissions': '100',
#                 'How did you hear about us?': 'ML conferences',
#                 'Location': 'Virtual',
#                 'Submission Deadline': due_date.strftime('%Y/%m/%d %H:%M'),
#                 'Venue Start Date': start_date.strftime('%Y/%m/%d'),
#                 'contact_email': venue['request_form_note'].content['contact_email'],
#                 'withdraw_submission_expiration': withdraw_exp_date,
#             },
#             forum=venue['request_form_note'].forum,
#             invitation='{}/-/Request{}/Revision'.format(venue['support_group_id'], venue['request_form_note'].number),
#             readers=['{}/Program_Chairs'.format(venue['venue_id']), venue['support_group_id']],
#             referent=venue['request_form_note'].forum,
#             replyto=venue['request_form_note'].forum,
#             signatures=['~SomeFirstName_User1'],
#             writers=[]
#         ))
#         assert venue_revision_note
#         helpers.await_queue()
#         process_logs = client.get_process_logs(id=venue_revision_note.id)
#         assert len(process_logs) == 1
#         assert process_logs[0]['status'] == 'ok'
#         assert process_logs[0]['invitation'] == '{}/-/Request{}/Revision'.format(venue['support_group_id'],
#                                                                                  venue['request_form_note'].number)

#         conference = openreview.get_conference(client, request_form_id=venue['request_form_note'].forum)
#         paper_withdraw_super_invitation = openreview.tools.get_invitation(client, conference.get_invitation_id("Withdraw"))
#         withdraw_exp_date = datetime.datetime.strptime(withdraw_exp_date, '%Y/%m/%d')
#         assert paper_withdraw_super_invitation.duedate is None
#         assert openreview.tools.datetime_millis(withdraw_exp_date) == openreview.tools.datetime_millis(paper_withdraw_super_invitation.expdate)

    def test_venue_review_stage(self, client, test_client, selenium, request_page, helpers, venue, openreview_client):

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

        helpers.await_queue()

        openreview_client.add_members_to_group('V2.cc/2030/Conference/Submission1/Reviewers', '~VenueThree_Reviewer1')

        reviewer_client = openreview.api.OpenReviewClient(username='venue_reviewer_v2_@mail.com', password='1234')
        reviewer_group = client.get_group('V2.cc/2030/Conference/Reviewers')
        assert reviewer_group and len(reviewer_group.members) == 2

        reviewer_page_url = 'http://localhost:3030/group?id=V2.cc/2030/Conference/Reviewers#assigned-papers'
        request_page(selenium, reviewer_page_url, token=reviewer_client.token, by=By.LINK_TEXT, wait_for_element='test submission')

        note_div = selenium.find_element_by_class_name('note')
        assert note_div
        assert 'test submission' == note_div.find_element_by_link_text('test submission').text

        review_invitations = openreview_client.get_invitations(invitation='{}/-/Official_Review'.format(venue['venue_id']))
        assert review_invitations and len(review_invitations) == 2
        assert 'title' not in review_invitations[0].edit['note']['content']

        reviewer_group = openreview_client.get_group('V2.cc/2030/Conference/Submission1/Reviewers')
        assert 'V2.cc/2030/Conference' in reviewer_group.readers
        assert 'V2.cc/2030/Conference/Submission1/Area_Chairs' in reviewer_group.readers
        assert 'V2.cc/2030/Conference/Submission1/Reviewers' in reviewer_group.readers

        assert 'V2.cc/2030/Conference' in reviewer_group.deanonymizers
        assert 'V2.cc/2030/Conference/Submission1/Area_Chairs' in reviewer_group.deanonymizers
        assert 'V2.cc/2030/Conference/Submission1/Reviewers' not in reviewer_group.deanonymizers
        reviewer_group = openreview_client.get_group('V2.cc/2030/Conference/Submission2/Reviewers')

        ac_group = openreview_client.get_group('V2.cc/2030/Conference/Submission1/Area_Chairs')
        assert 'V2.cc/2030/Conference' in ac_group.readers
        assert 'V2.cc/2030/Conference/Submission1/Area_Chairs' in ac_group.readers
        assert 'V2.cc/2030/Conference/Submission1/Reviewers' not in ac_group.readers
        assert 'V2.cc/2030/Conference/Submission1/Senior_Area_Chairs' in ac_group.readers

        assert 'V2.cc/2030/Conference' in ac_group.deanonymizers
        assert 'V2.cc/2030/Conference/Submission1/Area_Chairs' not in ac_group.deanonymizers
        assert 'V2.cc/2030/Conference/Submission1/Reviewers' not in ac_group.deanonymizers
        assert 'V2.cc/2030/Conference/Submission1/Senior_Area_Chairs' in ac_group.deanonymizers

        sac_group = openreview_client.get_group('V2.cc/2030/Conference/Submission1/Senior_Area_Chairs')
        assert 'V2.cc/2030/Conference/Submission1/Senior_Area_Chairs' in sac_group.readers
        assert 'V2.cc/2030/Conference/Program_Chairs' in sac_group.readers

        ## Post a review
        reviewer_anon_groups=reviewer_client.get_groups(prefix=f'V2.cc/2030/Conference/Submission1/Reviewer_.*', signatory='~VenueThree_Reviewer1')
        assert len(reviewer_anon_groups) == 1

        ## Post a review edit
        review_note = reviewer_client.post_note_edit(invitation=f'V2.cc/2030/Conference/Submission1/-/Official_Review',
            signatures=[reviewer_anon_groups[0].id],
            note=Note(
                content={
                    'review': { 'value': 'great paper!' },
                    'rating': { 'value': '10: Top 5% of accepted papers, seminal paper' },
                    'confidence': { 'value': '3: The reviewer is fairly confident that the evaluation is correct' }
                }
            )
        )

        helpers.await_queue_edit(openreview_client, edit_id=review_note['id'])

        ## reviews should be private
        reviews = reviewer_client.get_notes(invitation=f'V2.cc/2030/Conference/Submission1/-/Official_Review', sort= 'number:asc')
        assert len(reviews) == 1
        assert 'V2.cc/2030/Conference/Program_Chairs' in reviews[0].readers
        assert 'V2.cc/2030/Conference/Submission1/Senior_Area_Chairs' in reviews[0].readers
        assert 'V2.cc/2030/Conference/Submission1/Area_Chairs' in reviews[0].readers
        assert 'V2.cc/2030/Conference/Submission1/Reviewers/Submitted' in reviews[0].readers
        assert 'V2.cc/2030/Conference/Submission1/Authors' not in reviews[0].readers

    def test_release_reviews_to_authors(self, client, test_client, selenium, request_page, helpers, venue, openreview_client):

        # Post a review stage note
        now = datetime.datetime.utcnow()
        start_date = now - datetime.timedelta(days=2)
        due_date = now + datetime.timedelta(days=3)
        review_stage_note = test_client.post_note(openreview.Note(
            content={
                'review_start_date': start_date.strftime('%Y/%m/%d'),
                'review_deadline': due_date.strftime('%Y/%m/%d'),
                'make_reviews_public': 'No, reviews should NOT be revealed publicly when they are posted',
                'release_reviews_to_authors': 'Yes, reviews should be revealed when they are posted to the paper\'s authors',
                'release_reviews_to_reviewers': 'Reviews should be immediately revealed to the paper\'s reviewers',
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

        invitation = openreview_client.get_invitation('V2.cc/2030/Conference/Submission1/-/Official_Review')
        assert len(invitation.edit['note']['readers']) == 5
        assert 'V2.cc/2030/Conference/Submission1/Authors' in invitation.edit['note']['readers']
        assert len(invitation.edit['note']['nonreaders']) == 0

        reviews = openreview_client.get_notes(invitation='V2.cc/2030/Conference/Submission1/-/Official_Review')
        assert len(reviews) == 1
        assert 'V2.cc/2030/Conference/Program_Chairs' in reviews[0].readers
        assert 'V2.cc/2030/Conference/Submission1/Senior_Area_Chairs' in reviews[0].readers
        assert 'V2.cc/2030/Conference/Submission1/Area_Chairs' in reviews[0].readers
        assert 'V2.cc/2030/Conference/Submission1/Reviewers' in reviews[0].readers
        assert 'V2.cc/2030/Conference/Submission1/Authors' in reviews[0].readers
        assert len(reviews[0].nonreaders) == 0

    def test_venue_meta_review_stage(self, client, test_client, selenium, request_page, helpers, venue, openreview_client):

        helpers.create_user('venue_ac_v2@mail.com', 'VenueTwo', 'Ac')
        meta_reviewer_client = openreview.api.OpenReviewClient(username='venue_ac_v2@mail.com', password='1234')

        submissions = openreview_client.get_notes(invitation='{}/-/Submission'.format(venue['venue_id']), sort='tmdate')
        assert submissions and len(submissions) == 2

        # Assert that ACs do not see the Submit button for meta reviews at this point
        meta_reviewer_group = openreview_client.get_group('{}/Area_Chairs'.format(venue['venue_id']))
        openreview_client.add_members_to_group(meta_reviewer_group, '~VenueTwo_Ac1')

        openreview_client.add_members_to_group('V2.cc/2030/Conference/Submission1/Area_Chairs', '~VenueTwo_Ac1')

        ac_group = openreview_client.get_group('{}/Area_Chairs'.format(venue['venue_id']))
        assert ac_group and len(ac_group.members) == 2

        # no AC console yet
        # ac_page_url = 'http://localhost:3030/group?id={}/Area_Chairs'.format(venue['venue_id'])
        # request_page(selenium, ac_page_url, token=meta_reviewer_client.token, wait_for_element='1-metareview-status')

        # submit_div_1 = selenium.find_element_by_id('1-metareview-status')
        # with pytest.raises(NoSuchElementException):
        #     assert submit_div_1.find_element_by_link_text('Submit')

        # submit_div_2 = selenium.find_element_by_id('2-metareview-status')
        # with pytest.raises(NoSuchElementException):
        #     assert submit_div_2.find_element_by_link_text('Submit')

        # Post a meta review stage note
        now = datetime.datetime.utcnow()
        start_date = now - datetime.timedelta(days=2)
        due_date = now + datetime.timedelta(days=3)
        meta_review_stage_note = openreview.Note(
            content={
                'make_meta_reviews_public': 'Yes, meta reviews should be revealed publicly when they are posted',
                'meta_review_start_date': start_date.strftime('%Y/%m/%d'),
                'meta_review_deadline': due_date.strftime('%Y/%m/%d'),
                'recommendation_options': 'Accept, Reject',
                'release_meta_reviews_to_authors': 'No, meta reviews should NOT be revealed when they are posted to the paper\'s authors',
                'release_meta_reviews_to_reviewers': 'Meta reviews should be immediately revealed to the paper\'s reviewers who have already submitted their review',
                'additional_meta_review_form_options': {
                    'suggestions': {
                        'description': 'Please provide suggestions on how to improve the paper',
                        'value': {
                            'param': {
                                'type': 'string',
                                'maxLength': 5000,
                                'input': 'textarea',
                                'optional': True
                            }
                        }
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
        )

        with pytest.raises(openreview.OpenReviewException, match=r'Meta reviews cannot be released to the public since all papers are private'):
            meta_review_stage_note=test_client.post_note(meta_review_stage_note)

        meta_review_stage_note.content['make_meta_reviews_public'] = 'No, meta reviews should NOT be revealed publicly when they are posted'
        meta_review_stage_note=test_client.post_note(meta_review_stage_note)

        assert meta_review_stage_note
        helpers.await_queue()

        process_logs = client.get_process_logs(id = meta_review_stage_note.id)
        assert len(process_logs) == 1
        assert process_logs[0]['status'] == 'ok'

        # add AC console
        # # Assert that AC now see the Submit button for assigned papers
        # request_page(selenium, ac_page_url, token=meta_reviewer_client.token, wait_for_element='note-summary-2')

        # note_div_1 = selenium.find_element_by_id('note-summary-1')
        # assert note_div_1
        # note_div_2 = selenium.find_element_by_id('note-summary-2')
        # assert note_div_2
        # assert 'test submission' == note_div_1.find_element_by_link_text('test submission').text
        # assert 'test submission 2' == note_div_2.find_element_by_link_text('test submission 2').text

        # submit_div_1 = selenium.find_element_by_id('1-metareview-status')
        # assert submit_div_1.find_element_by_link_text('Submit')

        # submit_div_2 = selenium.find_element_by_id('2-metareview-status')
        # assert submit_div_2.find_element_by_link_text('Submit')

        meta_review_invitation = openreview_client.get_invitation(id='{}/Submission1/-/Meta_Review'.format(venue['venue_id']))
        assert meta_review_invitation
        meta_review_invitation = openreview_client.get_invitation(id='{}/Submission2/-/Meta_Review'.format(venue['venue_id']))
        assert meta_review_invitation
        assert 'confidence' not in meta_review_invitation.edit['note']['content']
        assert 'suggestions' in meta_review_invitation.edit['note']['content']
        assert 'Accept' in meta_review_invitation.edit['note']['content']['recommendation']['value']['param']['enum']
        assert len(meta_review_invitation.edit['note']['readers']) == 4

        #post a meta review
        ac_anon_groups=meta_reviewer_client.get_groups(prefix=f'V2.cc/2030/Conference/Submission1/Area_Chair_.*', signatory='~VenueTwo_Ac1')
        assert len(ac_anon_groups) == 1

        meta_review_note = meta_reviewer_client.post_note_edit(invitation=f'V2.cc/2030/Conference/Submission1/-/Meta_Review',
            signatures=[ac_anon_groups[0].id],
            note=Note(
                content={
                    'metareview': { 'value': 'This is a metarview' },
                    'recommendation': { 'value': 'Accept' }
                }
            )
        )

        meta_reviews = meta_reviewer_client.get_notes(invitation=f'V2.cc/2030/Conference/Submission1/-/Meta_Review', sort= 'number:asc')
        assert len(meta_reviews) == 1
        assert 'V2.cc/2030/Conference/Program_Chairs' in meta_reviews[0].readers
        assert 'V2.cc/2030/Conference/Submission1/Senior_Area_Chairs' in meta_reviews[0].readers
        assert 'V2.cc/2030/Conference/Submission1/Area_Chairs' in meta_reviews[0].readers
        assert 'V2.cc/2030/Conference/Submission1/Reviewers/Submitted' in meta_reviews[0].readers
        assert 'V2.cc/2030/Conference/Submission1/Authors' not in meta_reviews[0].readers

    def test_release_meta_reviews_to_authors_and_reviewers(self, test_client, helpers, venue, openreview_client):

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
                'release_meta_reviews_to_authors': 'Yes, meta reviews should be revealed when they are posted to the paper\'s authors',
                'release_meta_reviews_to_reviewers': 'Meta reviews should be immediately revealed to the paper\'s reviewers',
                'additional_meta_review_form_options': {
                    'suggestions': {
                        'description': 'Please provide suggestions on how to improve the paper',
                        'value': {
                            'param': {
                                'type': 'string',
                                'maxLength': 5000,
                                'input': 'textarea',
                                'optional': True
                            }
                        }
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

        invitation = openreview_client.get_invitation('V2.cc/2030/Conference/Submission1/-/Meta_Review')
        assert len(invitation.edit['note']['readers']) == 5
        assert 'V2.cc/2030/Conference/Submission1/Authors' in invitation.edit['note']['readers']
        assert len(invitation.edit['note']['nonreaders']) == 0

        meta_reviews = openreview_client.get_notes(invitation='V2.cc/2030/Conference/Submission1/-/Meta_Review')
        assert len(meta_reviews) == 1
        assert 'V2.cc/2030/Conference/Program_Chairs' in meta_reviews[0].readers
        assert 'V2.cc/2030/Conference/Submission1/Senior_Area_Chairs' in meta_reviews[0].readers
        assert 'V2.cc/2030/Conference/Submission1/Area_Chairs' in meta_reviews[0].readers
        assert 'V2.cc/2030/Conference/Submission1/Reviewers' in meta_reviews[0].readers
        assert 'V2.cc/2030/Conference/Submission1/Authors' in meta_reviews[0].readers
        assert len(meta_reviews[0].nonreaders) == 0

    def test_venue_comment_stage(self, client, test_client, selenium, request_page, helpers, venue, openreview_client):

        submissions = openreview_client.get_notes(invitation='{}/-/Submission'.format(venue['venue_id']), sort='number')
        assert submissions and len(submissions) == 2

        # Assert that official comment invitation is not available already
        official_comment_invitation = openreview.tools.get_invitation(openreview_client, '{}/-/Official_Comment'.format(venue['venue_id']))
        assert official_comment_invitation is None

        # Post an official comment stage note
        now = datetime.datetime.utcnow()
        start_date = now - datetime.timedelta(days=2)
        end_date = now + datetime.timedelta(days=3)
        comment_stage_note = test_client.post_note(openreview.Note(
            content={
                'commentary_start_date': start_date.strftime('%Y/%m/%d'),
                'commentary_end_date': end_date.strftime('%Y/%m/%d'),
                'participants': ['Program Chairs', 'Assigned Senior Area Chairs', 'Assigned Area Chairs', 'Assigned Reviewers', 'Authors'],
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
        official_comment_invitation = openreview.tools.get_invitation(openreview_client, '{}/-/Official_Comment'.format(venue['venue_id']))
        assert official_comment_invitation

        paper_official_comment_invitation = openreview.tools.get_invitation(openreview_client, '{}/Submission1/-/Official_Comment'.format(venue['venue_id']))
        assert paper_official_comment_invitation
        assert 'V2.cc/2030/Conference/Program_Chairs' in paper_official_comment_invitation.edit['note']['readers']['param']['enum']
        assert 'V2.cc/2030/Conference/Submission1/Reviewer_.*' in paper_official_comment_invitation.edit['note']['readers']['param']['enum']
        assert 'V2.cc/2030/Conference/Submission1/Senior_Area_Chairs' in paper_official_comment_invitation.edit['note']['readers']['param']['enum']
        assert 'V2.cc/2030/Conference/Submission1/Area_Chairs' in paper_official_comment_invitation.edit['note']['readers']['param']['enum']
        assert 'V2.cc/2030/Conference/Submission1/Reviewers' in paper_official_comment_invitation.edit['note']['readers']['param']['enum']
        assert 'V2.cc/2030/Conference/Submission1/Authors' in paper_official_comment_invitation.edit['note']['readers']['param']['enum']

        author_client = OpenReviewClient(username='venue_author_v2@mail.com', password='1234')
        # Assert that an official comment can be posted by the paper author
        official_comment_note = author_client.post_note_edit(invitation='V2.cc/2030/Conference/Submission1/-/Official_Comment',
        signatures=['V2.cc/2030/Conference/Submission1/Authors'],
        note=Note(
            readers=[
                'V2.cc/2030/Conference/Program_Chairs',
                'V2.cc/2030/Conference/Submission1/Area_Chairs',
                'V2.cc/2030/Conference/Submission1/Authors',
                'V2.cc/2030/Conference/Submission1/Reviewers',
                'V2.cc/2030/Conference/Submission1/Senior_Area_Chairs'
            ],
            content={
                'comment': {'value': 'test comment'},
                'title': {'value': 'test official comment title'}
            }
        ))
        helpers.await_queue_edit(openreview_client, edit_id=official_comment_note['id'])

        # Assert that public comment invitation is not available
        public_comment_invitation = openreview.tools.get_invitation(openreview_client, '{}/-/Public_Comment'.format(venue['venue_id']))
        assert public_comment_invitation is None

    def test_venue_decision_stage(self, client, test_client, selenium, request_page, venue, helpers, openreview_client):

        submissions = openreview_client.get_notes(invitation='{}/-/Submission'.format(venue['venue_id']), sort='number:asc')
        assert submissions and len(submissions) == 2
        submission = submissions[0]

        helpers.create_user('tom_venue@mail.com', 'ProgramChair', 'Venue')
        pc_client = openreview.api.OpenReviewClient(username='tom_venue@mail.com', password='1234')

        # Assert that PC does not have access to the Decision invitation
        decision_invitation = openreview.tools.get_invitation(pc_client, '{}/Submission{}/-/Decision'.format(venue['venue_id'], submission.number))
        assert decision_invitation is None

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
                'release_decisions_to_authors': 'Yes, decisions should be revealed when they are posted to the paper\'s authors',
                'release_decisions_to_reviewers': 'No, decisions should not be immediately revealed to the paper\'s reviewers',
                'release_decisions_to_area_chairs': 'Yes, decisions should be immediately revealed to the paper\'s area chairs',
                'notify_authors': 'Yes, send an email notification to the authors',
                'additional_decision_form_options': {
                    'suggestions': {
                        'description': 'Please provide suggestions on how to improve the paper',
                        'value': {
                            'param': {
                                'type': 'string',
                                'maxLength': 5000,
                                'input': 'textarea',
                                'optional': True
                            }
                        }
                    }
                }
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
        decision_invitation = openreview.tools.get_invitation(pc_client, '{}/Submission{}/-/Decision'.format(venue['venue_id'], submission.number))
        assert decision_invitation

        decision_invitation = openreview_client.get_invitation(id='{}/Submission1/-/Decision'.format(venue['venue_id']))
        assert decision_invitation
        decision_invitation = openreview_client.get_invitation(id='{}/Submission2/-/Decision'.format(venue['venue_id']))
        assert decision_invitation
        assert 'comment' in decision_invitation.edit['note']['content']
        assert 'suggestions' in decision_invitation.edit['note']['content']
        assert 'decision' in decision_invitation.edit['note']['content']
        assert 'Revision Needed' in decision_invitation.edit['note']['content']['decision']['value']['param']['enum']
        assert len(decision_invitation.edit['note']['readers']) == 4
        assert 'V2.cc/2030/Conference/Program_Chairs' in decision_invitation.edit['note']['readers']
        assert 'V2.cc/2030/Conference/Submission2/Senior_Area_Chairs' in decision_invitation.edit['note']['readers']
        assert 'V2.cc/2030/Conference/Submission2/Area_Chairs' in decision_invitation.edit['note']['readers']
        assert 'V2.cc/2030/Conference/Submission2/Authors' in decision_invitation.edit['note']['readers']

        #post decision
        decision_note = pc_client.post_note_edit(invitation='V2.cc/2030/Conference/Submission1/-/Decision',
        signatures=['V2.cc/2030/Conference/Program_Chairs'],
        note=Note(
            readers=[
                'V2.cc/2030/Conference/Program_Chairs',
                'V2.cc/2030/Conference/Submission1/Area_Chairs',
                'V2.cc/2030/Conference/Submission1/Authors',
                'V2.cc/2030/Conference/Submission1/Senior_Area_Chairs'
            ],
            content={
                'decision': {'value': 'Accept'},
                'comment': {'value': 'This is a comment.'}
            }
        ))
        helpers.await_queue_edit(openreview_client, edit_id=decision_note['id'])

        messages = client.get_messages(
            to='venue_author_v2@mail.com',
            subject="[TestVenue@OR'2030V2] Decision posted to your submission - Paper Number: 1, Paper Title: \"test submission\"")
        assert messages and len(messages) == 1
        assert messages[0]['content']['text'] == f'''To view the decision, click here: https://openreview.net/forum?id={submission.id}&noteId={decision_note['note']['id']}'''

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
            writer.writerow([submissions[1].number, 'Revision Needed', 'Not Good'])

        with open(os.path.join(os.path.dirname(__file__), 'data/decisions_wrong_paper.csv'), 'w') as file_handle:
            writer = csv.writer(file_handle)
            writer.writerow([500, 'Accept', 'Good Paper'])
            writer.writerow([submissions[1].number, 'Reject', 'Not Good'])

        with open(os.path.join(os.path.dirname(__file__), 'data/decisions_wrong_decision.csv'), 'w') as file_handle:
            writer = csv.writer(file_handle)
            writer.writerow([submissions[0].number, 'Test', 'Good Paper'])
            writer.writerow([submissions[1].number, 'Reject', 'Not Good'])

        # Post a decision stage note with decisions file
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
                        'description': 'Please provide suggestions on how to improve the paper',
                        'value': {
                            'param': {
                                'type': 'string',
                                'maxLength': 5000,
                                'input': 'textarea',
                                'optional': True
                            }
                        }
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
                        'description': 'Please provide suggestions on how to improve the paper',
                        'value': {
                            'param': {
                                'type': 'string',
                                'maxLength': 5000,
                                'input': 'textarea',
                                'optional': True
                            }
                        }
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
                        'description': 'Please provide suggestions on how to improve the paper',
                        'value': {
                            'param': {
                                'type': 'string',
                                'maxLength': 5000,
                                'input': 'textarea',
                                'optional': True
                            }
                        }
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
        assert '\"Paper 500 not found. Please check the submitted paper numbers.\"' in \
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
                        'description': 'Please provide suggestions on how to improve the paper',
                        'value': {
                            'param': {
                                'type': 'string',
                                'maxLength': 5000,
                                'input': 'textarea',
                                'optional': True
                            }
                        }
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
        assert '\"decision value must be equal to one of the allowed values: Accept, Revision Needed, Reject\"' in decision_status.content['error']

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
                        'description': 'Please provide suggestions on how to improve the paper',
                        'value': {
                            'param': {
                                'type': 'string',
                                'maxLength': 5000,
                                'input': 'textarea',
                                'optional': True
                            }
                        }
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
            sub_decision_notes = openreview_client.get_notes(
                invitation='{venue_id}/Submission{number}/-/Decision'.format(
                    venue_id=venue['venue_id'], number=submissions[i].number
                )
            )
            assert len(sub_decision_notes) == 1
            sub_decision_note = sub_decision_notes[0]
            assert sub_decision_note
            assert sub_decision_note.content['decision']['value'] == sub_decisions[i][1]
            assert sub_decision_note.content['comment']['value'] == sub_decisions[i][2]

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
                        'description': 'Please provide suggestions on how to improve the paper',
                        'value': {
                            'param': {
                                'type': 'string',
                                'maxLength': 5000,
                                'input': 'textarea',
                                'optional': True
                            }
                        }
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

        decision_notes = openreview_client.get_notes(invitation='V2.cc/2030/Conference/Submission1/-/Decision')
        assert len(decision_notes) == 1
        assert 'V2.cc/2030/Conference/Program_Chairs' in decision_notes[0].readers
        assert 'V2.cc/2030/Conference/Submission1/Senior_Area_Chairs' in decision_notes[0].readers
        assert 'V2.cc/2030/Conference/Submission1/Area_Chairs' in decision_notes[0].readers
        assert 'V2.cc/2030/Conference/Submission1/Reviewers' in decision_notes[0].readers
        assert 'V2.cc/2030/Conference/Submission1/Authors' in decision_notes[0].readers
        assert not decision_notes[0].nonreaders

        #get post_decision invitation
        with pytest.raises(openreview.OpenReviewException) as openReviewError:
            post_decision_invitation = test_client.get_invitation('{}/-/Request{}/Post_Decision_Stage'.format(venue['support_group_id'], venue['request_form_note'].number))
        assert openReviewError.value.args[0].get('name') == 'NotFoundError'

        invitation = client.get_invitation('{}/-/Request{}/Post_Decision_Stage'.format(venue['support_group_id'], venue['request_form_note'].number))
        assert invitation.cdate > openreview.tools.datetime_millis(datetime.datetime.utcnow())

#     def test_venue_submission_revision_stage(self, client, test_client, selenium, request_page, helpers, venue):

#         author_client = helpers.create_user('venue_author3@mail.com', 'Venue', 'Author')
#         submission = author_client.post_note(openreview.Note(
#             invitation='{}/-/Submission'.format(venue['venue_id']),
#             readers=[
#                 venue['venue_id'],
#                 '~Venue_Author3'
#             ],
#             writers=[
#                 '~Venue_Author3',
#                 venue['venue_id']
#             ],
#             signatures=['~Venue_Author3'],
#             content={
#                 'title': 'test submission 3',
#                 'authorids': ['~Venue_Author3'],
#                 'authors': ['Venue Author'],
#                 'abstract': 'test abstract 3'
#             }
#         ))

#         assert submission

#         conference = openreview.get_conference(client, request_form_id=venue['request_form_note'].forum)
#         conference.setup_post_submission_stage(force=True)

#         blind_submissions = author_client.get_notes(
#             invitation='{}/-/Blind_Submission'.format(venue['venue_id']), sort='tmdate')
#         assert blind_submissions and len(blind_submissions) == 1

#         # Post a revision stage note
#         now = datetime.datetime.utcnow()
#         start_date = now - datetime.timedelta(days=2)
#         due_date = now + datetime.timedelta(days=3)
#         revision_stage_note = test_client.post_note(openreview.Note(
#             content={
#                 'submission_revision_name': 'Revision',
#                 'submission_revision_start_date': start_date.strftime('%Y/%m/%d'),
#                 'submission_revision_deadline': due_date.strftime('%Y/%m/%d'),
#                 'accepted_submissions_only': 'Enable revision for all submissions',
#                 'submission_author_edition': 'Allow addition and removal of authors',
#                 'submission_revision_remove_options': ['keywords']
#             },
#             forum=venue['request_form_note'].forum,
#             invitation='{}/-/Request{}/Submission_Revision_Stage'.format(venue['support_group_id'], venue['request_form_note'].number),
#             readers=['{}/Program_Chairs'.format(venue['venue_id']), venue['support_group_id']],
#             referent=venue['request_form_note'].forum,
#             replyto=venue['request_form_note'].forum,
#             signatures=['~SomeFirstName_User1'],
#             writers=[]
#         ))
#         assert revision_stage_note

#         helpers.await_queue()
#         process_logs = client.get_process_logs(id=revision_stage_note.id)
#         assert len(process_logs) == 1
#         assert process_logs[0]['status'] == 'ok'

#         blind_submissions = author_client.get_notes(invitation='{}/-/Blind_Submission'.format(venue['venue_id']))

#         author_page_url = 'http://localhost:3030/forum?id={}'.format(blind_submissions[0].forum, by=By.CLASS_NAME, wait_for_element='edit_button')
#         request_page(selenium, author_page_url, token=author_client.token)

#         meta_actions = selenium.find_elements_by_class_name('meta_actions')
#         assert len(meta_actions) == 2
#         ## Edit and trash buttons, the submission invitation is still open
#         assert meta_actions[0].find_element_by_class_name('edit_button')
#         assert meta_actions[0].find_element_by_class_name('trash_button')
#         ## Reference invitations
#         assert 'Revision' == meta_actions[1].find_element_by_class_name('edit_button').text

#         # Post revision note for a submission
#         revision_note = author_client.post_note(openreview.Note(
#             invitation='{}/Paper{}/-/Revision'.format(venue['venue_id'], blind_submissions[0].number),
#             forum=blind_submissions[0].original,
#             referent=blind_submissions[0].original,
#             replyto=blind_submissions[0].original,
#             readers=[venue['venue_id'], '{}/Paper{}/Authors'.format(venue['venue_id'], blind_submissions[0].number)],
#             writers=['{}/Paper{}/Authors'.format(venue['venue_id'], blind_submissions[0].number), venue['venue_id']],
#             signatures=['{}/Paper{}/Authors'.format(venue['venue_id'], blind_submissions[0].number)],
#             content={
#                 'title': 'revised test submission 3',
#                 'abstract': 'revised abstract 3',
#                 'authors': ['Venue Author', 'Melisa Bok'],
#                 'authorids': ['~Venue_Author3', 'melisa@mail.com']
#             }
#         ))
#         assert revision_note

#         helpers.await_queue()
#         process_logs = client.get_process_logs(id=revision_note.id)
#         assert len(process_logs) == 1
#         assert process_logs[0]['status'] == 'ok'

#         updated_note = author_client.get_note(id=blind_submissions[0].forum)
#         assert updated_note
#         assert updated_note.content['title'] == 'revised test submission 3'
#         assert updated_note.content['abstract'] == 'revised abstract 3'
#         assert updated_note.content['authors'] == blind_submissions[0].content['authors']
#         assert updated_note.content['authorids'] == blind_submissions[0].content['authorids']

#         messages = client.get_messages(subject='{} has received a new revision of your submission titled revised test submission 3'.format(venue['request_form_note'].content['Abbreviated Venue Name']))
#         assert messages and len(messages) == 2
#         #assert messages[0]['content']['to'] == 'venue_author3@mail.com'

#     def test_venue_submission_revision_stage_accepted_papers_only(self, client, test_client, selenium, request_page, helpers, venue):
#         conference = openreview.get_conference(client, request_form_id=venue['request_form_note'].forum)
#         conference.setup_post_submission_stage(force=True)

#         # Post a revision stage note
#         now = datetime.datetime.utcnow()
#         start_date = now - datetime.timedelta(days=2)
#         due_date = now + datetime.timedelta(days=3)
#         revision_stage_note = test_client.post_note(openreview.Note(
#             content={
#                 'submission_revision_name': 'Revision',
#                 'submission_revision_start_date': start_date.strftime('%Y/%m/%d'),
#                 'submission_revision_deadline': due_date.strftime('%Y/%m/%d'),
#                 'accepted_submissions_only': 'Enable revision for accepted submissions only',
#                 'submission_author_edition': 'Allow addition and removal of authors',
#                 'submission_revision_remove_options': ['keywords']
#             },
#             forum=venue['request_form_note'].forum,
#             invitation='{}/-/Request{}/Submission_Revision_Stage'.format(venue['support_group_id'], venue['request_form_note'].number),
#             readers=['{}/Program_Chairs'.format(venue['venue_id']), venue['support_group_id']],
#             referent=venue['request_form_note'].forum,
#             replyto=venue['request_form_note'].forum,
#             signatures=['~SomeFirstName_User1'],
#             writers=[]
#         ))
#         assert revision_stage_note

#         helpers.await_queue()
#         process_logs = client.get_process_logs(id=revision_stage_note.id)
#         assert len(process_logs) == 1
#         assert process_logs[0]['status'] == 'ok'

#         blind_submissions = test_client.get_notes(invitation='{}/-/Blind_Submission'.format(venue['venue_id']))
#         revision_invitation = test_client.get_invitation('{}/Paper{}/-/Revision'.format(venue['venue_id'], blind_submissions[0].number))
#         assert revision_invitation.expdate < round(time.time() * 1000)

    def test_post_decision_stage(self, client, test_client, selenium, request_page, helpers, venue, openreview_client):

        submissions = openreview_client.get_notes(invitation='{}/-/Submission'.format(venue['venue_id']), sort='number:asc')
        assert submissions and len(submissions) == 2

        # Assert that submissions are still blind
        assert submissions[0].content['authors']['readers'] == ["V2.cc/2030/Conference", "V2.cc/2030/Conference/Submission1/Authors"]
        assert submissions[0].content['authorids']['readers'] == ["V2.cc/2030/Conference", "V2.cc/2030/Conference/Submission1/Authors"]
        assert submissions[1].content['authors']['readers'] == ["V2.cc/2030/Conference", "V2.cc/2030/Conference/Submission2/Authors"]
        assert submissions[1].content['authorids']['readers'] == ["V2.cc/2030/Conference", "V2.cc/2030/Conference/Submission2/Authors"]
        # Assert that submissions are private
        assert submissions[0].readers == ['V2.cc/2030/Conference',
            'V2.cc/2030/Conference/Senior_Area_Chairs',
            'V2.cc/2030/Conference/Area_Chairs',
            'V2.cc/2030/Conference/Reviewers',
            'V2.cc/2030/Conference/Submission1/Authors']
        assert submissions[1].readers == ['V2.cc/2030/Conference',
            'V2.cc/2030/Conference/Senior_Area_Chairs',
            'V2.cc/2030/Conference/Area_Chairs',
            'V2.cc/2030/Conference/Reviewers',
            'V2.cc/2030/Conference/Submission2/Authors']

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
        short_name = 'TestVenue@OR\'2030V2'
        post_decision_stage_note = test_client.post_note(openreview.Note(
            content={
                'reveal_authors': 'Reveal author identities of only accepted submissions to the public',
                'submission_readers': 'Make accepted submissions public and hide rejected submissions',
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

        submissions = openreview_client.get_notes(invitation='V2.cc/2030/Conference/-/Submission', sort='number:asc')
        assert submissions and len(submissions) == 2

        # Assert accepted submission is public and rejected submission is private
        assert submissions[0].readers == ['everyone']
        assert submissions[1].readers == ['V2.cc/2030/Conference',
            'V2.cc/2030/Conference/Submission2/Senior_Area_Chairs',
            'V2.cc/2030/Conference/Submission2/Area_Chairs',
            'V2.cc/2030/Conference/Submission2/Reviewers',
            'V2.cc/2030/Conference/Submission2/Authors']

        # assert authors of accepted paper were released
        assert submissions[0].content['venue']['value'] == 'TestVenue@OR\'2030V2'
        assert submissions[0].content['venueid']['value'] == 'V2 2030 Conference'
        assert 'readers' not in submissions[0].content['authors']
        assert 'readers' not in submissions[0].content['authorids']

        # assert author identities of rejected paper are still hidden
        assert submissions[1].content['venue']['value'] == 'Submitted to TestVenue@OR\'2030V2'
        assert submissions[1].content['venueid']['value'] == 'V2 2030 Conference'
        assert submissions[1].content['authors']['readers'] == ['V2.cc/2030/Conference','V2.cc/2030/Conference/Submission2/Authors']
        assert submissions[1].content['authorids']['readers'] == ['V2.cc/2030/Conference','V2.cc/2030/Conference/Submission2/Authors']

        last_message = client.get_messages(to='venue_author_v2@mail.com', subject='[TestVenue@OR\'2030V2] Decision notification for your submission 1: test submission')[0]
        assert "Dear VenueTwo Author,\n\nThank you for submitting your paper, test submission, to TestVenue@OR'2030V2." in last_message['content']['text']
        assert f"https://openreview.net/forum?id={submissions[0].id}" in last_message['content']['text']

#         note_id = submissions[0].id
#         assert '_bibtex' in submissions[0].content and submissions[0].content['_bibtex'] == '''@misc{
# anonymous2022test,
# title={test submission},
# author={Anonymous},
# year={2022},
# url={https://openreview.net/forum?id='''+ note_id + '''}
# }'''

#         # Post another revision stage note
#         now = datetime.datetime.utcnow()
#         start_date = now - datetime.timedelta(days=2)
#         due_date = now + datetime.timedelta(days=5)
#         revision_stage_note = test_client.post_note(openreview.Note(
#             content={
#                 'submission_revision_name': 'Camera_Ready_Revision',
#                 'submission_revision_start_date': start_date.strftime('%Y/%m/%d'),
#                 'submission_revision_deadline': due_date.strftime('%Y/%m/%d'),
#                 'accepted_submissions_only': 'Enable revision for all submissions',
#                 'submission_author_edition': 'Allow reorder of existing authors only',
#                 'submission_revision_remove_options': ['keywords']
#             },
#             forum=venue['request_form_note'].forum,
#             invitation='{}/-/Request{}/Submission_Revision_Stage'.format(venue['support_group_id'], venue['request_form_note'].number),
#             readers=['{}/Program_Chairs'.format(venue['venue_id']), venue['support_group_id']],
#             referent=venue['request_form_note'].forum,
#             replyto=venue['request_form_note'].forum,
#             signatures=['~SomeFirstName_User1'],
#             writers=[]
#         ))
#         assert revision_stage_note

#         helpers.await_queue()
#         process_logs = client.get_process_logs(id=revision_stage_note.id)
#         assert len(process_logs) == 1
#         assert process_logs[0]['status'] == 'ok'

#         revision_invitations = client.get_all_invitations(regex='{}/Paper.*/-/Revision'.format(venue['venue_id']))
#         for invitation in revision_invitations:
#             assert invitation.expdate < round(time.time() * 1000)

#         blind_submissions = client.get_notes(invitation='{}/-/Blind_Submission'.format(venue['venue_id']), sort='number:asc')
#         assert blind_submissions and len(blind_submissions) == 3

#         assert blind_submissions[0].content['authors'] == ['Anonymous']
#         assert blind_submissions[0].content['authorids'] == ['{}/Paper{}/Authors'.format(venue['venue_id'], blind_submissions[0].number)]
#         assert blind_submissions[1].content['authors'] == ['Anonymous']
#         assert blind_submissions[1].content['authorids'] == ['{}/Paper{}/Authors'.format(venue['venue_id'], blind_submissions[1].number)]
#         assert blind_submissions[2].content['authors'] == ['Anonymous']
#         assert blind_submissions[2].content['authorids'] == ['{}/Paper{}/Authors'.format(venue['venue_id'], blind_submissions[2].number)]

#         # Assert that submissions are still public
#         assert blind_submissions[0].readers == ['everyone']
#         assert blind_submissions[1].readers == ['everyone']
#         assert blind_submissions[2].readers == ['everyone']

#         #Assert venue, venueid and bibtex were not overwritten
#         conference = openreview.get_conference(client, request_form_id=venue['request_form_note'].forum)
#         conference.setup_post_submission_stage(force=True)

#         submissions = client.get_notes(invitation='{}/-/Blind_Submission'.format(venue['venue_id']), sort='number:asc')
#         assert submissions and len(submissions) == 3

#         assert 'venue' in submissions[0].content and 'Submitted to TestVenue@OR\'2030' in submissions[0].content['venue']
#         assert 'venueid' in submissions[0].content and 'TEST.cc/2030/Conference' in submissions[0].content['venueid']
#         assert 'venueid' in submissions[1].content and 'TEST.cc/2030/Conference' in submissions[1].content['venueid']
#         assert 'venue' in submissions[1].content and 'TestVenue@OR\'2030' in submissions[1].content['venue']

#         note_id = submissions[0].id
#         assert '_bibtex' in submissions[0].content and submissions[0].content['_bibtex'] == '''@misc{
# anonymous2022test,
# title={test submission},
# author={Anonymous},
# year={2022},
# url={https://openreview.net/forum?id='''+ note_id + '''}
# }'''

#         # Post revision note for a submission
#         author_client = openreview.Client(username='venue_author3@mail.com', password='1234')
#         with pytest.raises(openreview.OpenReviewException, match=r'The value Venue Author,Andrew McCallum in field authors does not match the invitation definition'):
#             revision_note = author_client.post_note(openreview.Note(
#                 invitation='{}/Paper{}/-/Camera_Ready_Revision'.format(venue['venue_id'], blind_submissions[2].number),
#                 forum=blind_submissions[2].original,
#                 referent=blind_submissions[2].original,
#                 replyto=blind_submissions[2].original,
#                 readers=[venue['venue_id'], '{}/Paper{}/Authors'.format(venue['venue_id'], blind_submissions[2].number)],
#                 writers=['{}/Paper{}/Authors'.format(venue['venue_id'], blind_submissions[2].number), venue['venue_id']],
#                 signatures=['{}/Paper{}/Authors'.format(venue['venue_id'], blind_submissions[2].number)],
#                 content={
#                     'title': 'camera ready revised test submission 3',
#                     'abstract': 'revised abstract 3',
#                     'authors': ['Venue Author', 'Andrew McCallum'],
#                     'authorids': ['~Venue_Author3', 'mccallum@gmail.com']
#                 }
#             ))

#     def test_venue_public_comment_stage(self, client, test_client, selenium, request_page, helpers, venue):

#         conference = openreview.get_conference(client, request_form_id=venue['request_form_note'].forum)
#         blind_submissions = client.get_notes(invitation='{}/-/Blind_Submission'.format(venue['venue_id']), sort='tmdate')
#         assert blind_submissions and len(blind_submissions) == 3

#         # Post an official comment stage note
#         now = datetime.datetime.utcnow()
#         start_date = now - datetime.timedelta(days=2)
#         end_date = now + datetime.timedelta(days=3)
#         comment_stage_note = test_client.post_note(openreview.Note(
#             content={
#                 'commentary_start_date': start_date.strftime('%Y/%m/%d'),
#                 'commentary_end_date': end_date.strftime('%Y/%m/%d'),
#                 'participants': ['Program Chairs', 'Paper Area Chairs', 'Paper Reviewers', 'Authors', 'Public (non-anonymously)'],
#                 'email_program_chairs_about_official_comments': 'Yes, email PCs for each official comment made in the venue'

#             },
#             forum=venue['request_form_note'].forum,
#             invitation='{}/-/Request{}/Comment_Stage'.format(venue['support_group_id'], venue['request_form_note'].number),
#             readers=['{}/Program_Chairs'.format(venue['venue_id']), venue['support_group_id']],
#             referent=venue['request_form_note'].forum,
#             replyto=venue['request_form_note'].forum,
#             signatures=['~SomeFirstName_User1'],
#             writers=[]
#         ))
#         assert comment_stage_note
#         helpers.await_queue()

#         process_logs = client.get_process_logs(id=comment_stage_note.id)
#         assert len(process_logs) == 1
#         assert process_logs[0]['status'] == 'ok'

#         # Assert that official comment invitation is now available
#         official_comment_invitation = openreview.tools.get_invitation(client, conference.get_invitation_id('Official_Comment', number=1))
#         assert official_comment_invitation

#         # Assert that public comment invitation is not available
#         public_comment_invitation = openreview.tools.get_invitation(client, conference.get_invitation_id('Public_Comment', number=1))
#         assert public_comment_invitation


    # def test_release_reviews(self, client, test_client, selenium, request_page, helpers, venue, openreview_client):

    #     # Post a review stage note
    #     now = datetime.datetime.utcnow()
    #     start_date = now - datetime.timedelta(days=2)
    #     due_date = now + datetime.timedelta(days=3)
    #     review_stage_note = test_client.post_note(openreview.Note(
    #         content={
    #             'review_start_date': start_date.strftime('%Y/%m/%d'),
    #             'review_deadline': due_date.strftime('%Y/%m/%d'),
    #             'make_reviews_public': 'Yes, reviews should be revealed publicly when they are posted',
    #             'release_reviews_to_authors': 'Yes, reviews should be revealed when they are posted to the paper\'s authors',
    #             'release_reviews_to_reviewers': 'Reviews should be immediately revealed to all reviewers',
    #             'remove_review_form_options': 'title',
    #             'email_program_chairs_about_reviews': 'Yes, email program chairs for each review received'
    #         },
    #         forum=venue['request_form_note'].forum,
    #         invitation='{}/-/Request{}/Review_Stage'.format(venue['support_group_id'], venue['request_form_note'].number),
    #         readers=['{}/Program_Chairs'.format(venue['venue_id']), venue['support_group_id']],
    #         referent=venue['request_form_note'].forum,
    #         replyto=venue['request_form_note'].forum,
    #         signatures=['~SomeFirstName_User1'],
    #         writers=[]
    #     ))
    #     assert review_stage_note
    #     helpers.await_queue()

    #     invitation = openreview_client.get_invitation('V2.cc/2030/Conference/Submission1/-/Official_Review')
    #     assert len(invitation.edit['note']['readers']) == 1
    #     assert 'everyone' in invitation.edit['note']['readers']
    #     assert len(invitation.edit['note']['nonreaders']) == 0

    #     notes = openreview_client.get_notes(invitation='V2.cc/2030/Conference/Submission1/-/Official_Review')
    #     assert notes[0].readers == ['everyone']
        


#     def test_supplementary_material_revision(self, client, test_client, selenium, request_page, helpers, venue):

#         # Post another revision stage note
#         now = datetime.datetime.utcnow()
#         start_date = now - datetime.timedelta(days=2)
#         due_date = now + datetime.timedelta(days=5)
#         revision_stage_note = test_client.post_note(openreview.Note(
#             content={
#                 'submission_revision_name':'Supplementary Material',
#                 'submission_revision_start_date': start_date.strftime('%Y/%m/%d'),
#                 'submission_revision_deadline': due_date.strftime('%Y/%m/%d'),
#                 'accepted_submissions_only': 'Enable revision for all submissions',
#                 'submission_author_edition': 'Allow addition and removal of authors',
#                 'submission_revision_remove_options': ['title','authors', 'authorids','abstract','keywords', 'TL;DR'],
#                 'submission_revision_additional_options': {
#                     'supplementary_material': {
#                         'description': 'Supplementary material (e.g. code or video). All supplementary material must be self-contained and zipped into a single file.',
#                         'order': 10,
#                         'value-file': {
#                             'fileTypes': [
#                                 'zip'
#                             ],
#                             'size': 50
#                         },
#                         'required': False
#                     }
#                 }
#             },
#             forum=venue['request_form_note'].forum,
#             invitation='{}/-/Request{}/Submission_Revision_Stage'.format(venue['support_group_id'], venue['request_form_note'].number),
#             readers=['{}/Program_Chairs'.format(venue['venue_id']), venue['support_group_id']],
#             referent=venue['request_form_note'].forum,
#             replyto=venue['request_form_note'].forum,
#             signatures=['~SomeFirstName_User1'],
#             writers=[]
#         ))
#         assert revision_stage_note

#         helpers.await_queue()
#         process_logs = client.get_process_logs(id=revision_stage_note.id)
#         assert len(process_logs) == 1
#         assert process_logs[0]['status'] == 'ok'

#         blind_submissions = client.get_notes(invitation='{}/-/Blind_Submission'.format(venue['venue_id']), sort='number:asc')
#         assert blind_submissions and len(blind_submissions) == 3

#         revision_invitations = client.get_invitations(regex='{}/Paper[0-9]*/-/Supplementary_Material$'.format(venue['venue_id']))
#         assert revision_invitations and len(revision_invitations) == 3
#         assert len(revision_invitations[0].reply['content'].keys()) == 2
#         assert 'supplementary_material' in revision_invitations[0].reply['content']
#         assert all(x not in revision_invitations[0].reply['content'] for x in ['title','authors', 'authorids','abstract','keywords', 'TL;DR'])
#         assert revision_invitations[0].duedate
#         assert revision_invitations[0].expdate

#         #make sure homepage webfield was not overwritten after doing get_conference()
#         request_page(selenium, "http://localhost:3030/group?id=TEST.cc/2030/Conference", wait_for_element='reject')
#         notes_panel = selenium.find_element_by_id('notes')
#         assert notes_panel
#         tabs = notes_panel.find_element_by_class_name('tabs-container')
#         assert tabs
#         accepted_panel = selenium.find_element_by_id('accept')
#         assert accepted_panel
#         accepted_notes = accepted_panel.find_elements_by_class_name('note')
#         assert accepted_notes
#         assert len(accepted_notes) == 1
#         rejected_panel = selenium.find_element_by_id('reject')
#         assert rejected_panel
#         rejected_notes = rejected_panel.find_elements_by_class_name('note')
#         assert rejected_notes
#         assert len(rejected_notes) == 2
