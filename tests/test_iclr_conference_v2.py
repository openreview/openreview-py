import time
import openreview
import pytest
import datetime
import re
import random
import os
import csv
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from openreview import ProfileManagement

class TestICLRConference():


    @pytest.fixture(scope="class")
    def profile_management(self, client):
        profile_management = ProfileManagement(client, 'openreview.net')
        profile_management.setup()
        return profile_management


    def test_create_conference(self, client, openreview_client, helpers, profile_management):

        now = datetime.datetime.utcnow()
        abstract_date = now + datetime.timedelta(days=1)
        due_date = now + datetime.timedelta(days=3)

        # Post the request form note
        helpers.create_user('pc@iclr.cc', 'Program', 'ICLRChair')
        pc_client = openreview.Client(username='pc@iclr.cc', password=helpers.strong_password)


        helpers.create_user('sac10@gmail.com', 'SAC', 'ICLROne')
        helpers.create_user('sac2@iclr.cc', 'SAC', 'ICLRTwo')
        helpers.create_user('ac1@iclr.cc', 'AC', 'ICLROne')
        helpers.create_user('ac2@iclr.cc', 'AC', 'ICLRTwo')
        helpers.create_user('reviewer1@iclr.cc', 'Reviewer', 'ICLROne')
        helpers.create_user('reviewer2@iclr.cc', 'Reviewer', 'ICLRTwo')
        helpers.create_user('reviewer3@iclr.cc', 'Reviewer', 'ICLRThree')
        helpers.create_user('reviewer4@gmail.com', 'Reviewer', 'ICLRFour')
        helpers.create_user('reviewer5@gmail.com', 'Reviewer', 'ICLRFive')
        helpers.create_user('reviewer6@gmail.com', 'Reviewer', 'ICLRSix')
        helpers.create_user('reviewerethics@gmail.com', 'Reviewer', 'ICLRSeven')

        request_form_note = pc_client.post_note(openreview.Note(
            invitation='openreview.net/Support/-/Request_Form',
            signatures=['~Program_ICLRChair1'],
            readers=[
                'openreview.net/Support',
                '~Program_ICLRChair1'
            ],
            writers=[],
            content={
                'title': 'International Conference on Learning Representations',
                'Official Venue Name': 'International Conference on Learning Representations',
                'Abbreviated Venue Name': 'ICLR 2024',
                'Official Website URL': 'https://iclr.cc',
                'program_chair_emails': ['pc@iclr.cc'],
                'contact_email': 'pc@iclr.cc',
                'publication_chairs':'No, our venue does not have Publication Chairs',
                'Area Chairs (Metareviewers)': 'Yes, our venue has Area Chairs',
                'senior_area_chairs': 'Yes, our venue has Senior Area Chairs',
                'ethics_chairs_and_reviewers': 'Yes, our venue has Ethics Chairs and Reviewers',
                'Venue Start Date': '2024/07/01',
                'abstract_registration_deadline': abstract_date.strftime('%Y/%m/%d'),
                'Submission Deadline': due_date.strftime('%Y/%m/%d'),
                'Location': 'Virtual',
                'submission_reviewer_assignment': 'Automatic',
                'Author and Reviewer Anonymity': 'Double-blind',
                'reviewer_identity': ['Program Chairs', 'Assigned Senior Area Chair', 'Assigned Area Chair', 'Assigned Reviewers'],
                'area_chair_identity': ['Program Chairs', 'Assigned Senior Area Chair', 'Assigned Area Chair', 'Assigned Reviewers'],
                'senior_area_chair_identity': ['Program Chairs', 'Assigned Senior Area Chair', 'Assigned Area Chair', 'Assigned Reviewers'],
                'Open Reviewing Policy': 'Submissions and reviews should both be public.',
                'submission_readers': 'Everyone (submissions are public)',
                'How did you hear about us?': 'ML conferences',
                'Expected Submissions': '100',
                'use_recruitment_template': 'Yes',
                'api_version': '2',
                'submission_license': ['CC BY 4.0', 'CC BY-SA 4.0', 'CC0 1.0'] # Allow authors to select license
            }))

        helpers.await_queue()

        # Post a deploy note
        client.post_note(openreview.Note(
            content={'venue_id': 'ICLR.cc/2024/Conference'},
            forum=request_form_note.forum,
            invitation='openreview.net/Support/-/Request{}/Deploy'.format(request_form_note.number),
            readers=['openreview.net/Support'],
            referent=request_form_note.forum,
            replyto=request_form_note.forum,
            signatures=['openreview.net/Support'],
            writers=['openreview.net/Support']
        ))

        helpers.await_queue()

        venue_group = openreview_client.get_group('ICLR.cc/2024/Conference')
        assert venue_group
        assert venue_group.content['date']['value'] == f'Abstract Registration: {abstract_date.strftime("%b %d %Y")} 12:00AM UTC-0, Submission Deadline: {due_date.strftime("%b %d %Y")} 12:00AM UTC-0'
        assert openreview_client.get_group('ICLR.cc/2024/Conference/Senior_Area_Chairs')
        assert openreview_client.get_group('ICLR.cc/2024/Conference/Area_Chairs')
        assert openreview_client.get_group('ICLR.cc/2024/Conference/Reviewers')
        assert openreview_client.get_group('ICLR.cc/2024/Conference/Authors')

        submission_invitation = openreview_client.get_invitation('ICLR.cc/2024/Conference/-/Submission')
        assert submission_invitation
        assert submission_invitation.duedate

        assert openreview_client.get_invitation('ICLR.cc/2024/Conference/Reviewers/-/Expertise_Selection')
        assert openreview_client.get_invitation('ICLR.cc/2024/Conference/Area_Chairs/-/Expertise_Selection')
        assert openreview_client.get_invitation('ICLR.cc/2024/Conference/Senior_Area_Chairs/-/Expertise_Selection')

    def test_reviewer_recruitment(self, client, openreview_client, helpers, request_page, selenium):

        pc_client=openreview.Client(username='pc@iclr.cc', password=helpers.strong_password)
        request_form=pc_client.get_notes(invitation='openreview.net/Support/-/Request_Form')[0]

        reviewer_details = '''reviewer1@iclr.cc, Reviewer ICLROne\nreviewer2@iclr.cc, Reviewer ICLRTwo'''
        pc_client.post_note(openreview.Note(
            content={
                'title': 'Recruitment',
                'invitee_role': 'Reviewers',
                'invitee_details': reviewer_details,
                'allow_accept_with_reduced_load': 'Yes',
                'invitee_reduced_load': ["1", "2", "3"],
                'invitation_email_subject': '[ICLR 2024] Invitation to serve as {{invitee_role}}',
                'invitation_email_content': 'Dear {{fullname}},\n\nYou have been nominated by the program chair committee of International Conference on Learning Representations @ ICLR 2024 to serve as {{invitee_role}}.\n\n{{invitation_url}}\n\nCheers!\n\nProgram Chairs'
            },
            forum=request_form.forum,
            replyto=request_form.forum,
            invitation='openreview.net/Support/-/Request{}/Recruitment'.format(request_form.number),
            readers=['ICLR.cc/2024/Conference/Program_Chairs', 'openreview.net/Support'],
            signatures=['~Program_ICLRChair1'],
            writers=[]
        ))

        helpers.await_queue()

        assert len(openreview_client.get_group('ICLR.cc/2024/Conference/Reviewers').members) == 0
        assert len(openreview_client.get_group('ICLR.cc/2024/Conference/Reviewers/Invited').members) == 2
        assert len(openreview_client.get_group('ICLR.cc/2024/Conference/Reviewers/Declined').members) == 0

        messages = openreview_client.get_messages(subject = '[ICLR 2024] Invitation to serve as Reviewer')
        assert len(messages) == 2

        # Accept invitation with reduced load
        for message in messages:
            text = message['content']['text']
            invitation_url = re.search('https://.*\n', text).group(0).replace('https://openreview.net', 'http://localhost:3030').replace('&amp;', '&')[:-1]
            helpers.respond_invitation(selenium, request_page, invitation_url, accept=True, quota=3)

        helpers.await_queue_edit(openreview_client, invitation='ICLR.cc/2024/Conference/Reviewers/-/Recruitment', count=2)

        messages = client.get_messages(subject='[ICLR 2024] Reviewer Invitation accepted with reduced load')
        assert len(messages) == 2

        assert len(openreview_client.get_group('ICLR.cc/2024/Conference/Reviewers').members) == 2
        assert len(openreview_client.get_group('ICLR.cc/2024/Conference/Reviewers/Invited').members) == 2
        assert len(openreview_client.get_group('ICLR.cc/2024/Conference/Reviewers/Declined').members) == 0

        # Decline invitation
        messages = openreview_client.get_messages(to='reviewer1@iclr.cc', subject='[ICLR 2024] Invitation to serve as Reviewer')
        invitation_url = re.search('https://.*\n', messages[0]['content']['text']).group(0).replace('https://openreview.net', 'http://localhost:3030').replace('&amp;', '&')[:-1]
        helpers.respond_invitation(selenium, request_page, invitation_url, accept=False)

        helpers.await_queue_edit(openreview_client, invitation='ICLR.cc/2024/Conference/Reviewers/-/Recruitment', count=3)

        assert len(openreview_client.get_group('ICLR.cc/2024/Conference/Reviewers').members) == 1
        assert len(openreview_client.get_group('ICLR.cc/2024/Conference/Reviewers/Invited').members) == 2
        assert len(openreview_client.get_group('ICLR.cc/2024/Conference/Reviewers/Declined').members) == 1

        reviewer_client = openreview.api.OpenReviewClient(username='reviewer2@iclr.cc', password=helpers.strong_password)

        request_page(selenium, "http://localhost:3030/group?id=ICLR.cc/2024/Conference/Reviewers", reviewer_client.token, wait_for_element='header')
        header = selenium.find_element(By.ID, 'header')
        assert 'You have agreed to review up to 1 papers' in header.text

    def test_submissions(self, client, openreview_client, helpers, test_client):

        test_client = openreview.api.OpenReviewClient(token=test_client.token)
        request_form=client.get_notes(invitation='openreview.net/Support/-/Request_Form')[0]

        domains = ['umass.edu', 'amazon.com', 'fb.com', 'cs.umass.edu', 'google.com', 'mit.edu', 'deepmind.com', 'co.ux', 'apple.com', 'nvidia.com']
        for i in range(1,12):
            note = openreview.api.Note(
                license = 'CC BY-SA 4.0',
                content = {
                    'title': { 'value': 'Paper title ' + str(i) },
                    'abstract': { 'value': 'This is an abstract ' + str(i) },
                    'authorids': { 'value': ['~SomeFirstName_User1', 'peter@mail.com', 'andrew@' + domains[i % 10]] },
                    'authors': { 'value': ['SomeFirstName User', 'Peter SomeLastName', 'Andrew Mc'] },
                    'keywords': { 'value': ['machine learning', 'nlp'] },
                    'pdf': {'value': '/pdf/' + 'p' * 40 +'.pdf' },
                }
            )
            if i == 1 or i == 11:
                note.content['authors']['value'].append('SAC ICLROne')
                note.content['authorids']['value'].append('~SAC_ICLROne1')

            test_client.post_note_edit(invitation='ICLR.cc/2024/Conference/-/Submission',
                signatures=['~SomeFirstName_User1'],
                note=note)

        helpers.await_queue_edit(openreview_client, invitation='ICLR.cc/2024/Conference/-/Submission', count=11)

        submissions = openreview_client.get_notes(invitation='ICLR.cc/2024/Conference/-/Submission', sort='number:asc')
        assert len(submissions) == 11
        assert ['ICLR.cc/2024/Conference', '~SomeFirstName_User1', 'peter@mail.com', 'andrew@amazon.com', '~SAC_ICLROne1'] == submissions[0].readers
        assert ['~SomeFirstName_User1', 'peter@mail.com', 'andrew@amazon.com', '~SAC_ICLROne1'] == submissions[0].content['authorids']['value']

        # Check that note.license is from license list
        licenses = request_form.content['submission_license']
        assert submissions[0].license in licenses

        authors_group = openreview_client.get_group(id='ICLR.cc/2024/Conference/Authors')

        for i in range(1,12):
            assert f'ICLR.cc/2024/Conference/Submission{i}/Authors' in authors_group.members

    def test_post_submission(self, client, openreview_client, helpers):

        pc_client=openreview.Client(username='pc@iclr.cc', password=helpers.strong_password)
        request_form=pc_client.get_notes(invitation='openreview.net/Support/-/Request_Form')[0]
        venue = openreview.get_conference(client, request_form.id, support_user='openreview.net/Support')

        ## close abstract submission
        now = datetime.datetime.utcnow()
        abstract_date = now - datetime.timedelta(minutes=28)
        due_date = now + datetime.timedelta(days=3)        
        pc_client.post_note(openreview.Note(
            content={
                'title': 'International Conference on Learning Representations',
                'Official Venue Name': 'International Conference on Learning Representations',
                'Abbreviated Venue Name': 'ICLR 2024',
                'Official Website URL': 'https://iclr.cc',
                'program_chair_emails': ['pc@iclr.cc', 'pc3@iclr.cc'],
                'contact_email': 'pc@iclr.cc',
                'publication_chairs':'No, our venue does not have Publication Chairs',
                'Venue Start Date': '2024/07/01',
                'abstract_registration_deadline': abstract_date.strftime('%Y/%m/%d'),
                'Submission Deadline': due_date.strftime('%Y/%m/%d'),
                'Location': 'Virtual',
                'submission_reviewer_assignment': 'Automatic',
                'How did you hear about us?': 'ML conferences',
                'Expected Submissions': '100',
            },
            forum=request_form.forum,
            invitation='openreview.net/Support/-/Request{}/Revision'.format(request_form.number),
            readers=['ICLR.cc/2024/Conference/Program_Chairs', 'openreview.net/Support'],
            referent=request_form.forum,
            replyto=request_form.forum,
            signatures=['~Program_ICLRChair1'],
            writers=[]
        ))

        helpers.await_queue()
        helpers.await_queue_edit(openreview_client, 'ICLR.cc/2024/Conference/-/Post_Submission-0-1', count=2)
        helpers.await_queue_edit(openreview_client, 'ICLR.cc/2024/Conference/-/Withdrawal-0-1', count=2)
        helpers.await_queue_edit(openreview_client, 'ICLR.cc/2024/Conference/-/Desk_Rejection-0-1', count=2)

        pc_client_v2=openreview.api.OpenReviewClient(username='pc@iclr.cc', password=helpers.strong_password)
        submission_invitation = pc_client_v2.get_invitation('ICLR.cc/2024/Conference/-/Submission')
        assert submission_invitation.expdate < openreview.tools.datetime_millis(now)

        submissions = pc_client_v2.get_notes(invitation='ICLR.cc/2024/Conference/-/Submission', sort='number:asc')
        assert len(submissions) == 11
        assert submissions[0].license == 'CC BY-SA 4.0'
        assert submissions[0].readers == ['everyone']
        assert '_bibtex' in submissions[0].content
        assert 'author={Anonymous}' in submissions[0].content['_bibtex']['value']

        ## close full paper submission
        now = datetime.datetime.utcnow()
        abstract_date = now - datetime.timedelta(days=2)
        due_date = now - datetime.timedelta(minutes=28)        
        pc_client.post_note(openreview.Note(
            content={
                'title': 'International Conference on Learning Representations',
                'Official Venue Name': 'International Conference on Learning Representations',
                'Abbreviated Venue Name': 'ICLR 2024',
                'Official Website URL': 'https://iclr.cc',
                'program_chair_emails': ['pc@iclr.cc', 'pc3@iclr.cc'],
                'contact_email': 'pc@iclr.cc',
                'publication_chairs':'No, our venue does not have Publication Chairs',
                'Venue Start Date': '2024/07/01',
                'abstract_registration_deadline': abstract_date.strftime('%Y/%m/%d'),
                'Submission Deadline': due_date.strftime('%Y/%m/%d'),
                'Location': 'Virtual',
                'submission_reviewer_assignment': 'Automatic',
                'How did you hear about us?': 'ML conferences',
                'Expected Submissions': '100',
            },
            forum=request_form.forum,
            invitation='openreview.net/Support/-/Request{}/Revision'.format(request_form.number),
            readers=['ICLR.cc/2024/Conference/Program_Chairs', 'openreview.net/Support'],
            referent=request_form.forum,
            replyto=request_form.forum,
            signatures=['~Program_ICLRChair1'],
            writers=[]
        ))

        helpers.await_queue()
        helpers.await_queue_edit(openreview_client, 'ICLR.cc/2024/Conference/-/Post_Submission-0-1', count=3)
        helpers.await_queue_edit(openreview_client, 'ICLR.cc/2024/Conference/-/Withdrawal-0-1', count=3)
        helpers.await_queue_edit(openreview_client, 'ICLR.cc/2024/Conference/-/Desk_Rejection-0-1', count=3)

        client.get_group('ICLR.cc/2024/Conference/Submission1/Reviewers')    

    def test_review_stage(self, client, openreview_client, helpers, test_client):

        openreview_client.add_members_to_group('ICLR.cc/2024/Conference/Submission1/Reviewers', ['~Reviewer_ICLROne1', '~Reviewer_ICLRTwo1', '~Reviewer_ICLRThree1'])

        now = datetime.datetime.utcnow()
        due_date = now + datetime.timedelta(days=3)

        pc_client=openreview.Client(username='pc@iclr.cc', password=helpers.strong_password)
        request_form=pc_client.get_notes(invitation='openreview.net/Support/-/Request_Form')[0]
        review_stage_note=pc_client.post_note(openreview.Note(
            content={
                'review_deadline': due_date.strftime('%Y/%m/%d'),
                'make_reviews_public': 'No, reviews should NOT be revealed publicly when they are posted',
                'release_reviews_to_authors': 'No, reviews should NOT be revealed when they are posted to the paper\'s authors',
                'release_reviews_to_reviewers': 'Review should not be revealed to any reviewer, except to the author of the review',
                'email_program_chairs_about_reviews': 'No, do not email program chairs about received reviews',
            },
            forum=request_form.forum,
            invitation='openreview.net/Support/-/Request{}/Review_Stage'.format(request_form.number),
            readers=['ICLR.cc/2024/Conference/Program_Chairs', 'openreview.net/Support'],
            replyto=request_form.forum,
            referent=request_form.forum,
            signatures=['~Program_ICLRChair1'],
            writers=[]
        ))
        helpers.await_queue()

        invitation = openreview_client.get_invitation('ICLR.cc/2024/Conference/Submission1/-/Official_Review')

        reviewer_client=openreview.api.OpenReviewClient(username='reviewer1@iclr.cc', password=helpers.strong_password)

        anon_groups = reviewer_client.get_groups(prefix='ICLR.cc/2024/Conference/Submission1/Reviewer_', signatory='~Reviewer_ICLROne1')
        anon_group_id = anon_groups[0].id

        review_edit = reviewer_client.post_note_edit(
            invitation='ICLR.cc/2024/Conference/Submission1/-/Official_Review',
            signatures=[anon_group_id],
            note=openreview.api.Note(
                content={
                    'title': { 'value': 'Good paper, accept'},
                    'review': { 'value': 'Excellent paper, accept'},
                    'rating': { 'value': 10},
                    'confidence': { 'value': 5},
                }
            )
        )

        helpers.await_queue(openreview_client)        

    def test_comment_stage(self, openreview_client, helpers):

        pc_client=openreview.Client(username='pc@iclr.cc', password=helpers.strong_password)
        request_form=pc_client.get_notes(invitation='openreview.net/Support/-/Request_Form')[0]

        # Post an official comment stage note
        now = datetime.datetime.utcnow()
        start_date = now - datetime.timedelta(days=2)
        end_date = now + datetime.timedelta(days=3)
        comment_stage_note = pc_client.post_note(openreview.Note(
            content={
                'commentary_start_date': start_date.strftime('%Y/%m/%d'),
                'commentary_end_date': end_date.strftime('%Y/%m/%d'),
                'participants': ['Program Chairs', 'Assigned Senior Area Chairs', 'Assigned Area Chairs', 'Assigned Reviewers'],
                'additional_readers': ['Program Chairs', 'Assigned Senior Area Chairs', 'Assigned Area Chairs', 'Assigned Reviewers', 'Assigned Submitted Reviewers'],
                'email_program_chairs_about_official_comments': 'Yes, email PCs for each official comment made in the venue'
            },
            forum=request_form.forum,
            invitation=f'openreview.net/Support/-/Request{request_form.number}/Comment_Stage',
            readers=['ICLR.cc/2024/Conference/Program_Chairs', 'openreview.net/Support'],
            replyto=request_form.forum,
            referent=request_form.forum,
            signatures=['~Program_ICLRChair1'],
            writers=[]
        ))

        helpers.await_queue()

        invitation = openreview_client.get_invitation('ICLR.cc/2024/Conference/Submission1/-/Official_Comment')
        assert invitation.edit['signatures']['param']['items'] == [
            {
                "value": "ICLR.cc/2024/Conference/Program_Chairs",
                "optional": True
            },
            {
                "value": "ICLR.cc/2024/Conference/Submission1/Senior_Area_Chairs",
                "optional": True
            },
            {
                "prefix": "ICLR.cc/2024/Conference/Submission1/Area_Chair_.*",
                "optional": True
            },
            {
                "prefix": "ICLR.cc/2024/Conference/Submission1/Reviewer_.*",
                "optional": True
            }
        ]

        assert invitation.edit['note']['readers']['param']['items'] == [
            {
                "value": "ICLR.cc/2024/Conference/Program_Chairs",
                "optional": False
            },
            {
                "value": "ICLR.cc/2024/Conference/Submission1/Senior_Area_Chairs",
                "optional": False
            },
            {
                "value": "ICLR.cc/2024/Conference/Submission1/Area_Chairs",
                "optional": True
            },
            {
                "value": "ICLR.cc/2024/Conference/Submission1/Reviewers",
                "optional": True
            },
            {
                "value": "ICLR.cc/2024/Conference/Submission1/Reviewers/Submitted",
                "optional": True
            },
            {
                "prefix": "ICLR.cc/2024/Conference/Submission1/Reviewer_.*",
                "optional": True
            }
        ]

        ## allow public comments
        comment_stage_note = pc_client.post_note(openreview.Note(
            content={
                'commentary_start_date': start_date.strftime('%Y/%m/%d'),
                'commentary_end_date': end_date.strftime('%Y/%m/%d'),
                'participants': ['Program Chairs', 'Assigned Senior Area Chairs', 'Assigned Area Chairs', 'Assigned Reviewers'],
                'additional_readers': ['Program Chairs', 'Assigned Senior Area Chairs', 'Assigned Area Chairs', 'Assigned Reviewers', 'Assigned Submitted Reviewers', 'Authors', 'Public'],
                'email_program_chairs_about_official_comments': 'Yes, email PCs for each official comment made in the venue'
            },
            forum=request_form.forum,
            invitation=f'openreview.net/Support/-/Request{request_form.number}/Comment_Stage',
            readers=['ICLR.cc/2024/Conference/Program_Chairs', 'openreview.net/Support'],
            replyto=request_form.forum,
            referent=request_form.forum,
            signatures=['~Program_ICLRChair1'],
            writers=[]
        ))

        helpers.await_queue()

        invitation = openreview_client.get_invitation('ICLR.cc/2024/Conference/Submission1/-/Official_Comment')

        assert invitation.edit['note']['readers']['param']['items'] == [
            {
                'value': 'everyone',
                'optional': True
            },
            {
                "value": "ICLR.cc/2024/Conference/Program_Chairs",
                "optional": False
            },
            {
                "value": "ICLR.cc/2024/Conference/Submission1/Senior_Area_Chairs",
                "optional": False
            },
            {
                "value": "ICLR.cc/2024/Conference/Submission1/Area_Chairs",
                "optional": True
            },
            {
                "value": "ICLR.cc/2024/Conference/Submission1/Reviewers",
                "optional": True
            },
            {
                "value": "ICLR.cc/2024/Conference/Submission1/Reviewers/Submitted",
                "optional": True
            },
            {
                "prefix": "ICLR.cc/2024/Conference/Submission1/Reviewer_.*",
                "optional": True
            },
            {
                "value": "ICLR.cc/2024/Conference/Submission1/Authors",
                "optional": True
            }
        ]                             