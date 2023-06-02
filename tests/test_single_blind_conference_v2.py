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

class TestSingleBlindVenueV2():

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
                'title': 'Test 2050 Venue Single-Blind V2',
                'Official Venue Name': 'Test 2050 Venue Single-Blind V2',
                'Abbreviated Venue Name': "TestVenueSingleBlind@OR'2050V2",
                'Official Website URL': 'https://testvenue2030.gitlab.io/venue/',
                'program_chair_emails': [
                    'test@mail.com',
                    'tom_venue@mail.com'],
                'contact_email': 'test@mail.com',
                'Area Chairs (Metareviewers)': 'Yes, our venue has Area Chairs',
                'senior_area_chairs': 'No, our venue does not have Senior Area Chairs',
                'Venue Start Date': now.strftime('%Y/%m/%d'),
                'Submission Deadline': due_date.strftime('%Y/%m/%d'),
                'Location': 'Virtual',
                'submission_reviewer_assignment': 'Automatic',
                'Author and Reviewer Anonymity': 'Single-blind (Reviewers are anonymous)',
                'Open Reviewing Policy': 'Submissions and reviews should both be private.',
                'force_profiles_only': 'No, allow submissions with email addresses',
                'submission_readers': 'Assigned program committee (assigned reviewers, assigned area chairs, assigned senior area chairs if applicable)',
                'How did you hear about us?': 'ML conferences',
                'Expected Submissions': '100',
                'email_pcs_for_new_submissions': 'No, do not email PCs.',
                'reviewer_identity': ['Program Chairs', 'Assigned Area Chair'],
                'area_chair_identity': ['Program Chairs'],
                'senior_area_chair_identity': ['Program Chairs', 'Assigned Senior Area Chair'],
                'withdraw_submission_expiration': withdraw_exp_date.strftime('%Y/%m/%d'),
                'withdrawn_submissions_visibility': 'No, withdrawn submissions should not be made public.',
                'withdrawn_submissions_author_anonymity': 'Yes, author identities of withdrawn submissions should be revealed.',
                'email_pcs_for_withdrawn_submissions': 'No, do not email PCs.',
                'desk_rejected_submissions_visibility': 'No, desk rejected submissions should not be made public.',
                'desk_rejected_submissions_author_anonymity': 'Yes, author identities of desk rejected submissions should be revealed.',
                'How did you hear about us?': 'ML conferences',
                'Expected Submissions': '100',
                'submission_name': 'Submission',
                'api_version': '2'
            })

        request_form_note=test_client.post_note(request_form_note)

        helpers.await_queue()

        # Post a deploy note
        client.post_note(openreview.Note(
            content={'venue_id': 'V2.cc/2050/Conference_Single_Blind'},
            forum=request_form_note.forum,
            invitation='{}/-/Request{}/Deploy'.format(support_group_id, request_form_note.number),
            readers=[support_group_id],
            referent=request_form_note.forum,
            replyto=request_form_note.forum,
            signatures=[support_group_id],
            writers=[support_group_id]
        ))

        helpers.await_queue()

        submission_inv = openreview_client.get_invitation('V2.cc/2050/Conference_Single_Blind/-/Submission')
        assert submission_inv.duedate == openreview.tools.datetime_millis(due_date)
        assert submission_inv.expdate == openreview.tools.datetime_millis(due_date + datetime.timedelta(minutes = 30))

        # Return venue details as a dict
        venue_details = {
            'request_form_note': request_form_note,
            'support_group_id': support_group_id,
            'venue_id': 'V2.cc/2050/Conference_Single_Blind'
        }
        return venue_details
    
    def test_paper_submission(self, helpers, venue, openreview_client):

        venue_id = venue['venue_id']

        helpers.create_user('singleblindv2@mail.com', 'SingleBlind', 'Author')
        author_client = OpenReviewClient(username='singleblindv2@mail.com', password=helpers.strong_password)

        submission_note_1 = author_client.post_note_edit(
            invitation=f'{venue_id}/-/Submission',
            signatures= ['~SingleBlind_Author1'],
            note=Note(
                content={
                    'title': { 'value': 'Test Paper 1' },
                    'abstract': { 'value': 'test abstract' },
                    'authors': { 'value': ['SingleBlind Author']},
                    'authorids': { 'value': ['~SingleBlind_Author1']},
                    'pdf': {'value': '/pdf/' + 'p' * 40 +'.pdf' },
                    'keywords': {'value': ['aa'] }
                }
            ))

        helpers.await_queue_edit(openreview_client, edit_id=submission_note_1['id'])

        submission_note_2 = author_client.post_note_edit(
            invitation=f'{venue_id}/-/Submission',
            signatures= ['~SingleBlind_Author1'],
            note=Note(
                content={
                    'title': { 'value': 'Test Paper 2' },
                    'abstract': { 'value': 'test abstract' },
                    'authors': { 'value': ['SingleBlind Author', 'Celeste Martinez']},
                    'authorids': { 'value': ['~SingleBlind_Author1', 'celestev2@mail.com']},
                    'pdf': {'value': '/pdf/' + 'p' * 40 +'.pdf' },
                    'keywords': {'value': ['aa'] }
                }
            ))
        
        helpers.await_queue_edit(openreview_client, edit_id=submission_note_2['id'])

    def test_post_decision_stage(self, helpers, venue, test_client, client, openreview_client):

        now = datetime.datetime.utcnow()
        start_date = now - datetime.timedelta(days=2)
        due_date = now - datetime.timedelta(hours=1)

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
                'submission_reviewer_assignment': 'Automatic',
                'Submission Deadline': due_date.strftime('%Y/%m/%d %H:%M'),
                'Venue Start Date': start_date.strftime('%Y/%m/%d'),
                'contact_email': venue['request_form_note'].content['contact_email'],
                'email_pcs_for_new_submissions': 'Yes, email PCs for every new submission.',
                'submission_email': 'Your submission to {{Abbreviated_Venue_Name}} has been {{action}}.\n\nSubmission Number: {{note_number}} \n\nTitle: {{note_title}} {{note_abstract}} \n\nTo view your submission, click here: https://openreview.net/forum?id={{note_forum}} \n\nIf you have any questions, please contact the PCs at test@mail.com'
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

        # Close submission stage
        test_client.post_note(openreview.Note(
            content= {
                'force': 'Yes',
                'submission_readers': 'Assigned program committee (assigned reviewers, assigned area chairs, assigned senior area chairs if applicable)',
                'hide_fields': ['keywords', 'pdf']
            },
            forum= venue['request_form_note'].forum,
            invitation= f'openreview.net/Support/-/Request{venue["request_form_note"].number}/Post_Submission',
            readers=['{}/Program_Chairs'.format(venue['venue_id']), venue['support_group_id']],
            referent= venue['request_form_note'].forum,
            replyto= venue['request_form_note'].forum,
            signatures= ['~SomeFirstName_User1'],
            writers= [],
        ))

        helpers.await_queue()

        submissions = openreview_client.get_notes(invitation='V2.cc/2050/Conference_Single_Blind/-/Submission', sort='number:asc')
        assert submissions and len(submissions) == 2

        # assert authors are still public for all papers and keywords and pdf are hidden
        assert 'readers' not in submissions[0].content['authors']
        assert 'readers' not in submissions[0].content['authorids']
        assert 'readers' not in submissions[1].content['authors']
        assert 'readers' not in submissions[1].content['authorids']
        assert submissions[0].content['keywords']['readers'] == ['V2.cc/2050/Conference_Single_Blind','V2.cc/2050/Conference_Single_Blind/Submission1/Authors']
        assert submissions[1].content['keywords']['readers'] == ['V2.cc/2050/Conference_Single_Blind','V2.cc/2050/Conference_Single_Blind/Submission2/Authors']
        assert submissions[0].content['pdf']['readers'] == ['V2.cc/2050/Conference_Single_Blind','V2.cc/2050/Conference_Single_Blind/Submission1/Authors']
        assert submissions[1].content['pdf']['readers'] == ['V2.cc/2050/Conference_Single_Blind','V2.cc/2050/Conference_Single_Blind/Submission2/Authors']

        # Post a decision stage note
        now = datetime.datetime.utcnow()
        start_date = now - datetime.timedelta(days=2)
        due_date = now + datetime.timedelta(days=3)

        decision_stage_note = test_client.post_note(openreview.Note(
            content={
                'decision_start_date': start_date.strftime('%Y/%m/%d'),
                'decision_deadline': due_date.strftime('%Y/%m/%d'),
                'decision_options': 'Accept, Reject',
                'make_decisions_public': 'No, decisions should NOT be revealed publicly when they are posted',
                'release_decisions_to_authors': 'Yes, decisions should be revealed when they are posted to the paper\'s authors',
                'release_decisions_to_reviewers': 'No, decisions should not be immediately revealed to the paper\'s reviewers',
                'release_decisions_to_area_chairs': 'No, decisions should not be immediately revealed to the paper\'s area chairs',
                'notify_authors': 'Yes, send an email notification to the authors'
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

        #post decision
        decision_note = openreview_client.post_note_edit(invitation='V2.cc/2050/Conference_Single_Blind/Submission1/-/Decision',
            signatures=['V2.cc/2050/Conference_Single_Blind/Program_Chairs'],
            note=Note(
                readers=[
                    'V2.cc/2050/Conference_Single_Blind/Program_Chairs',
                    'V2.cc/2050/Conference_Single_Blind/Submission1/Authors'            ],
                content={
                    'decision': {'value': 'Accept'},
                    'comment': {'value': 'This is a comment.'}
                }
            ))
        helpers.await_queue_edit(openreview_client, edit_id=decision_note['id'])

        #post decision
        decision_note = openreview_client.post_note_edit(invitation='V2.cc/2050/Conference_Single_Blind/Submission2/-/Decision',
            signatures=['V2.cc/2050/Conference_Single_Blind/Program_Chairs'],
            note=Note(
                readers=[
                    'V2.cc/2050/Conference_Single_Blind/Program_Chairs',
                    'V2.cc/2050/Conference_Single_Blind/Submission2/Authors'            ],
                content={
                    'decision': {'value': 'Reject'},
                    'comment': {'value': 'This is a comment.'}
                }
            ))
        helpers.await_queue_edit(openreview_client, edit_id=decision_note['id'])

        invitation = client.get_invitation('{}/-/Request{}/Post_Decision_Stage'.format(venue['support_group_id'], venue['request_form_note'].number))
        invitation.cdate = openreview.tools.datetime_millis(datetime.datetime.utcnow())
        client.post_invitation(invitation)

        now = datetime.datetime.utcnow()
        start_date = now - datetime.timedelta(days=2)
        due_date = now + datetime.timedelta(days=3)
        short_name = "TestVenueSingleBlind@OR'2050V2"
        post_decision_stage_note = test_client.post_note(openreview.Note(
            content={
                'submission_readers': 'Make accepted submissions public and hide rejected submissions',
                'hide_fields': ['keywords'],
                'home_page_tab_names': {
                    'Accept': 'Accept',
                    'Reject': 'Submitted'
                },
                'send_decision_notifications': 'No, I will send the emails to the authors',
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

        submissions = openreview_client.get_notes(invitation='V2.cc/2050/Conference_Single_Blind/-/Submission', sort='number:asc')
        assert submissions and len(submissions) == 2

        # assert authors are still public for all papers and keywords are hidden/pdfs are visible
        assert 'readers' not in submissions[0].content['authors']
        assert 'readers' not in submissions[0].content['authorids']
        assert 'readers' not in submissions[1].content['authors']
        assert 'readers' not in submissions[1].content['authorids']
        assert submissions[0].content['keywords']['readers'] == ['V2.cc/2050/Conference_Single_Blind','V2.cc/2050/Conference_Single_Blind/Submission1/Authors']
        assert submissions[1].content['keywords']['readers'] == ['V2.cc/2050/Conference_Single_Blind','V2.cc/2050/Conference_Single_Blind/Submission2/Authors']
        assert 'readers' not in submissions[0].content['pdf']
        assert 'readers' not in submissions[1].content['pdf']
