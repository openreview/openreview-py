import openreview
import pytest
import datetime
import re
import random
import os
import csv
from selenium.webdriver.common.by import By
from openreview import ProfileManagement

class TestICMLConference():


    @pytest.fixture(scope="class")
    def profile_management(self, client):
        profile_management = ProfileManagement(client, 'openreview.net')
        profile_management.setup()
        return profile_management


    def test_create_conference(self, client, openreview_client, helpers, profile_management):

        now = datetime.datetime.utcnow()
        due_date = now + datetime.timedelta(days=3)

        # Post the request form note
        pc_client=helpers.create_user('pc@icml.cc', 'Program', 'ICMLChair')

        sac_client = helpers.create_user('sac1@gmail.com', 'SAC', 'ICMLOne')
        helpers.create_user('sac2@icml.cc', 'SAC', 'ICMLTwo')
        helpers.create_user('ac1@icml.cc', 'AC', 'ICMLOne')
        helpers.create_user('ac2@icml.cc', 'AC', 'ICMLTwo')
        helpers.create_user('reviewer1@icml.cc', 'Reviewer', 'ICMLOne')
        helpers.create_user('reviewer2@icml.cc', 'Reviewer', 'ICMLTwo')
        helpers.create_user('reviewer3@icml.cc', 'Reviewer', 'ICMLThree')
        helpers.create_user('reviewer4@gmail.com', 'Reviewer', 'ICMLFour')
        helpers.create_user('reviewer5@gmail.com', 'Reviewer', 'ICMLFive')
        helpers.create_user('reviewer6@gmail.com', 'Reviewer', 'ICMLSix')

        request_form_note = pc_client.post_note(openreview.Note(
            invitation='openreview.net/Support/-/Request_Form',
            signatures=['~Program_ICMLChair1'],
            readers=[
                'openreview.net/Support',
                '~Program_ICMLChair1'
            ],
            writers=[],
            content={
                'title': 'Thirty-ninth International Conference on Machine Learning',
                'Official Venue Name': 'Thirty-ninth International Conference on Machine Learning',
                'Abbreviated Venue Name': 'ICML 2023',
                'Official Website URL': 'https://icml.cc',
                'program_chair_emails': ['pc@icml.cc'],
                'contact_email': 'pc@icml.cc',
                'Area Chairs (Metareviewers)': 'Yes, our venue has Area Chairs',
                'senior_area_chairs': 'Yes, our venue has Senior Area Chairs',
                'Venue Start Date': '2023/07/01',
                'Submission Deadline': due_date.strftime('%Y/%m/%d'),
                'Location': 'Virtual',
                'Paper Matching': [
                    'Reviewer Bid Scores',
                    'OpenReview Affinity'],
                'Author and Reviewer Anonymity': 'Double-blind',
                'reviewer_identity': ['Program Chairs', 'Assigned Senior Area Chair', 'Assigned Area Chair', 'Assigned Reviewers'],
                'area_chair_identity': ['Program Chairs', 'Assigned Senior Area Chair', 'Assigned Area Chair', 'Assigned Reviewers'],
                'senior_area_chair_identity': ['Program Chairs', 'Assigned Senior Area Chair', 'Assigned Area Chair', 'Assigned Reviewers'],
                'Open Reviewing Policy': 'Submissions and reviews should both be private.',
                'submission_readers': 'Program chairs and paper authors only',
                'How did you hear about us?': 'ML conferences',
                'Expected Submissions': '100',
                'use_recruitment_template': 'Yes',
                'api_version': '2'
            }))

        helpers.await_queue()

        # Post a deploy note
        client.post_note(openreview.Note(
            content={'venue_id': 'ICML.cc/2023/Conference'},
            forum=request_form_note.forum,
            invitation='openreview.net/Support/-/Request{}/Deploy'.format(request_form_note.number),
            readers=['openreview.net/Support'],
            referent=request_form_note.forum,
            replyto=request_form_note.forum,
            signatures=['openreview.net/Support'],
            writers=['openreview.net/Support']
        ))

        helpers.await_queue()

        assert openreview_client.get_group('ICML.cc/2023/Conference')
        assert openreview_client.get_group('ICML.cc/2023/Conference/Senior_Area_Chairs')
        assert openreview_client.get_group('ICML.cc/2023/Conference/Area_Chairs')
        assert openreview_client.get_group('ICML.cc/2023/Conference/Reviewers')
        assert openreview_client.get_group('ICML.cc/2023/Conference/Authors')

        submission_invitation = openreview_client.get_invitation('ICML.cc/2023/Conference/-/Submission')
        assert submission_invitation
        assert submission_invitation.duedate

        assert openreview_client.get_invitation('ICML.cc/2023/Conference/Reviewers/-/Expertise_Selection')
        assert openreview_client.get_invitation('ICML.cc/2023/Conference/Area_Chairs/-/Expertise_Selection')
        assert openreview_client.get_invitation('ICML.cc/2023/Conference/Senior_Area_Chairs/-/Expertise_Selection')

        sac_client.post_note(openreview.Note(
            invitation='openreview.net/Archive/-/Direct_Upload',
            readers = ['everyone'],
            signatures = ['~SAC_ICMLOne1'],
            writers = ['~SAC_ICMLOne1'],
            content = {
                'title': 'Paper title 1',
                'abstract': 'Paper abstract 1',
                'authors': ['SAC ICML', 'Test2 Client'],
                'authorids': ['~SAC_ICMLOne1', 'test2@mail.com']
            }
        ))

        sac_client.post_note(openreview.Note(
            invitation='openreview.net/Archive/-/Direct_Upload',
            readers = ['everyone'],
            signatures = ['~SAC_ICMLOne1'],
            writers = ['~SAC_ICMLOne1'],
            content = {
                'title': 'Paper title 2',
                'abstract': 'Paper abstract 2',
                'authors': ['SAC ICML', 'Test2 Client'],
                'authorids': ['~SAC_ICMLOne1', 'test2@mail.com']
            }
        ))

        pc_client.post_note(openreview.Note(
            invitation=f'openreview.net/Support/-/Request{request_form_note.number}/Revision',
            forum=request_form_note.id,
            readers=['ICML.cc/2023/Conference/Program_Chairs', 'openreview.net/Support'],
            referent=request_form_note.id,
            replyto=request_form_note.id,
            signatures=['~Program_ICMLChair1'],
            writers=[],
            content={
                'title': 'Thirty-ninth International Conference on Machine Learning',
                'Official Venue Name': 'Thirty-ninth International Conference on Machine Learning',
                'Abbreviated Venue Name': 'ICML 2023',
                'Official Website URL': 'https://icml.cc',
                'program_chair_emails': ['pc@icml.cc'],
                'contact_email': 'pc@icml.cc',
                'Venue Start Date': '2023/07/01',
                'Submission Deadline': due_date.strftime('%Y/%m/%d'),
                'Location': 'Virtual',
                'How did you hear about us?': 'ML conferences',
                'Expected Submissions': '100',
                'use_recruitment_template': 'Yes',
                'Additional Submission Options': {
                    "supplementary_material": {
                        "value": {
                            "param": {
                                "type": "file",
                                "extensions": [
                                    "zip",
                                    "pdf",
                                    "tgz",
                                    "gz"
                                ],
                                "maxSize": 100,
                                "optional": True,
                                "deletable": True
                            }
                        },
                        "description": "All supplementary material must be self-contained and zipped into a single file. Note that supplementary material will be visible to reviewers and the public throughout and after the review period, and ensure all material is anonymized. The maximum file size is 100MB.",
                        "order": 8
                    },
                    "financial_aid": {
                        "order": 9,
                        "description": "Each paper may designate up to one (1) icml.cc account email address of a corresponding student author who confirms that they would need the support to attend the conference, and agrees to volunteer if they get selected.",
                        "value": {
                            "param": {
                                "type": "string",
                                "maxLength": 100,
                                "optional": True
                            }
                        }
                    }
                }
            }
        ))
        helpers.await_queue()

        submission_invitation = openreview_client.get_invitation('ICML.cc/2023/Conference/-/Submission')
        assert submission_invitation
        assert 'supplementary_material' in submission_invitation.edit['note']['content']
        assert 'financial_aid' in submission_invitation.edit['note']['content']


    def test_add_pcs(self, client, openreview_client, helpers):

        pc_client=openreview.Client(username='pc@icml.cc', password='1234')
        request_form=pc_client.get_notes(invitation='openreview.net/Support/-/Request_Form')[0]

        now = datetime.datetime.utcnow()
        due_date = now + datetime.timedelta(days=3)

        pc_client.post_note(openreview.Note(
            content={
                'title': 'Thirty-ninth International Conference on Machine Learning',
                'Official Venue Name': 'Thirty-ninth International Conference on Machine Learning',
                'Abbreviated Venue Name': 'ICML 2023',
                'Official Website URL': 'https://icml.cc',
                'program_chair_emails': ['pc@icml.cc', 'pc2@icml.cc'],
                'contact_email': 'pc@icml.cc',
                'Venue Start Date': '2023/07/01',
                'Submission Deadline': due_date.strftime('%Y/%m/%d'),
                'Location': 'Virtual',
                'How did you hear about us?': 'ML conferences',
                'Expected Submissions': '100',
                'Additional Submission Options': {
                    "supplementary_material": {
                        "value": {
                            "param": {
                                "type": "file",
                                "extensions": [
                                    "zip",
                                    "pdf",
                                    "tgz",
                                    "gz"
                                ],
                                "maxSize": 100,
                                "optional": True,
                                "deletable": True
                            }
                        },
                        "description": "All supplementary material must be self-contained and zipped into a single file. Note that supplementary material will be visible to reviewers and the public throughout and after the review period, and ensure all material is anonymized. The maximum file size is 100MB.",
                        "order": 8
                    },
                    "financial_aid": {
                        "order": 9,
                        "description": "Each paper may designate up to one (1) icml.cc account email address of a corresponding student author who confirms that they would need the support to attend the conference, and agrees to volunteer if they get selected.",
                        "value": {
                            "param": {
                                "type": "string",
                                "maxLength": 100,
                                "optional": True
                            }
                        }
                    }
                }

            },
            forum=request_form.forum,
            invitation='openreview.net/Support/-/Request{}/Revision'.format(request_form.number),
            readers=['ICML.cc/2023/Conference/Program_Chairs', 'openreview.net/Support'],
            referent=request_form.forum,
            replyto=request_form.forum,
            signatures=['~Program_ICMLChair1'],
            writers=[]
        ))

        helpers.await_queue()

        pc_group = pc_client.get_group('ICML.cc/2023/Conference/Program_Chairs')
        assert ['pc@icml.cc', 'pc2@icml.cc'] == pc_group.members

        pc_client.post_note(openreview.Note(
            content={
                'title': 'Thirty-ninth International Conference on Machine Learning',
                'Official Venue Name': 'Thirty-ninth International Conference on Machine Learning',
                'Abbreviated Venue Name': 'ICML 2023',
                'Official Website URL': 'https://icml.cc',
                'program_chair_emails': ['pc@icml.cc', 'pc3@icml.cc'],
                'contact_email': 'pc@icml.cc',
                'Venue Start Date': '2023/07/01',
                'Submission Deadline': due_date.strftime('%Y/%m/%d'),
                'Location': 'Virtual',
                'How did you hear about us?': 'ML conferences',
                'Expected Submissions': '100',
                'Additional Submission Options': {
                    "supplementary_material": {
                        "value": {
                            "param": {
                                "type": "file",
                                "extensions": [
                                    "zip",
                                    "pdf",
                                    "tgz",
                                    "gz"
                                ],
                                "maxSize": 100,
                                "optional": True,
                                "deletable": True
                            }
                        },
                        "description": "All supplementary material must be self-contained and zipped into a single file. Note that supplementary material will be visible to reviewers and the public throughout and after the review period, and ensure all material is anonymized. The maximum file size is 100MB.",
                        "order": 8
                    },
                    "financial_aid": {
                        "order": 9,
                        "description": "Each paper may designate up to one (1) icml.cc account email address of a corresponding student author who confirms that they would need the support to attend the conference, and agrees to volunteer if they get selected.",
                        "value": {
                            "param": {
                                "type": "string",
                                "maxLength": 100,
                                "optional": True
                            }
                        }
                    }
                }

            },
            forum=request_form.forum,
            invitation='openreview.net/Support/-/Request{}/Revision'.format(request_form.number),
            readers=['ICML.cc/2023/Conference/Program_Chairs', 'openreview.net/Support'],
            referent=request_form.forum,
            replyto=request_form.forum,
            signatures=['~Program_ICMLChair1'],
            writers=[]
        ))

        helpers.await_queue()

        pc_group = pc_client.get_group('ICML.cc/2023/Conference/Program_Chairs')
        assert ['pc@icml.cc', 'pc3@icml.cc'] == pc_group.members

    def test_sac_recruitment(self, client, openreview_client, helpers, request_page, selenium):

        pc_client=openreview.Client(username='pc@icml.cc', password='1234')
        request_form=pc_client.get_notes(invitation='openreview.net/Support/-/Request_Form')[0]

        reviewer_details = '''sac1@gmail.com, SAC ICMLOne\nsac2@icml.cc, SAC ICMLTwo'''
        pc_client.post_note(openreview.Note(
            content={
                'title': 'Recruitment',
                'invitee_role': 'Senior_Area_Chairs',
                'invitee_details': reviewer_details,
                'invitation_email_subject': '[ICML 2023] Invitation to serve as {{invitee_role}}',
                'invitation_email_content': 'Dear {{fullname}},\n\nYou have been nominated by the program chair committee of Theoretical Foundations of RL Workshop @ ICML 2020 to serve as {{invitee_role}}.\n\n{{invitation_url}}\n\nCheers!\n\nProgram Chairs'
            },
            forum=request_form.forum,
            replyto=request_form.forum,
            invitation='openreview.net/Support/-/Request{}/Recruitment'.format(request_form.number),
            readers=['ICML.cc/2023/Conference/Program_Chairs', 'openreview.net/Support'],
            signatures=['~Program_ICMLChair1'],
            writers=[]
        ))

        helpers.await_queue()

        assert len(openreview_client.get_group('ICML.cc/2023/Conference/Senior_Area_Chairs').members) == 0
        assert len(openreview_client.get_group('ICML.cc/2023/Conference/Senior_Area_Chairs/Invited').members) == 2

        messages = openreview_client.get_messages(subject = '[ICML 2023] Invitation to serve as Senior Area Chair')
        assert len(messages) == 2

        for message in messages:
            text = message['content']['text']

            invitation_url = re.search('https://.*\n', text).group(0).replace('https://openreview.net', 'http://localhost:3030').replace('&amp;', '&')[:-1]
            helpers.respond_invitation(selenium, request_page, invitation_url, accept=True)

        helpers.await_queue()

        messages = client.get_messages(subject='[ICML 2023] Senior Area Chair Invitation accepted')
        assert len(messages) == 2

        assert len(openreview_client.get_group('ICML.cc/2023/Conference/Senior_Area_Chairs').members) == 2
        assert len(openreview_client.get_group('ICML.cc/2023/Conference/Senior_Area_Chairs/Invited').members) == 2

    def test_ac_recruitment(self, client, openreview_client, helpers, request_page, selenium):

        pc_client=openreview.Client(username='pc@icml.cc', password='1234')
        request_form=pc_client.get_notes(invitation='openreview.net/Support/-/Request_Form')[0]

        reviewer_details = '''ac1@icml.cc, AC ICMLOne\nac2@icml.cc, AC ICMLTwo'''
        pc_client.post_note(openreview.Note(
            content={
                'title': 'Recruitment',
                'invitee_role': 'Area_Chairs',
                'invitee_details': reviewer_details,
                'invitation_email_subject': '[ICML 2023] Invitation to serve as {{invitee_role}}',
                'invitation_email_content': 'Dear {{fullname}},\n\nYou have been nominated by the program chair committee of Theoretical Foundations of RL Workshop @ ICML 2020 to serve as {{invitee_role}}.\n\n{{invitation_url}}\n\nCheers!\n\nProgram Chairs'
            },
            forum=request_form.forum,
            replyto=request_form.forum,
            invitation='openreview.net/Support/-/Request{}/Recruitment'.format(request_form.number),
            readers=['ICML.cc/2023/Conference/Program_Chairs', 'openreview.net/Support'],
            signatures=['~Program_ICMLChair1'],
            writers=[]
        ))

        helpers.await_queue()

        assert len(openreview_client.get_group('ICML.cc/2023/Conference/Area_Chairs').members) == 0
        assert len(openreview_client.get_group('ICML.cc/2023/Conference/Area_Chairs/Invited').members) == 2

        messages = openreview_client.get_messages(subject = '[ICML 2023] Invitation to serve as Area Chair')
        assert len(messages) == 2

        for message in messages:
            text = message['content']['text']

            invitation_url = re.search('https://.*\n', text).group(0).replace('https://openreview.net', 'http://localhost:3030').replace('&amp;', '&')[:-1]
            helpers.respond_invitation(selenium, request_page, invitation_url, accept=True)

        helpers.await_queue()

        messages = client.get_messages(subject='[ICML 2023] Area Chair Invitation accepted')
        assert len(messages) == 2

        assert len(openreview_client.get_group('ICML.cc/2023/Conference/Area_Chairs').members) == 2
        assert len(openreview_client.get_group('ICML.cc/2023/Conference/Area_Chairs/Invited').members) == 2

    def test_reviewer_recruitment(self, client, openreview_client, helpers, request_page, selenium):

        pc_client=openreview.Client(username='pc@icml.cc', password='1234')
        request_form=pc_client.get_notes(invitation='openreview.net/Support/-/Request_Form')[0]

        reviewer_details = '''reviewer1@icml.cc, Reviewer ICMLOne
reviewer2@icml.cc, Reviewer ICMLTwo
reviewer3@icml.cc, Reviewer ICMLThree
reviewer4@gmail.com, Reviewer ICMLFour
reviewer5@gmail.com, Reviewer ICMLFive
reviewer6@gmail.com, Reviewer ICMLSix
'''
        pc_client.post_note(openreview.Note(
            content={
                'title': 'Recruitment',
                'invitee_role': 'Reviewers',
                'invitee_details': reviewer_details,
                'invitee_reduced_load': ["1", "2", "3"],
                'invitation_email_subject': '[ICML 2023] Invitation to serve as {{invitee_role}}',
                'invitation_email_content': 'Dear {{fullname}},\n\nYou have been nominated by the program chair committee of Theoretical Foundations of RL Workshop @ ICML 2020 to serve as {{invitee_role}}.\n\n{{invitation_url}}\n\nCheers!\n\nProgram Chairs'
            },
            forum=request_form.forum,
            replyto=request_form.forum,
            invitation='openreview.net/Support/-/Request{}/Recruitment'.format(request_form.number),
            readers=['ICML.cc/2023/Conference/Program_Chairs', 'openreview.net/Support'],
            signatures=['~Program_ICMLChair1'],
            writers=[]
        ))

        helpers.await_queue()

        assert len(openreview_client.get_group('ICML.cc/2023/Conference/Reviewers').members) == 0
        assert len(openreview_client.get_group('ICML.cc/2023/Conference/Reviewers/Invited').members) == 6
        assert len(openreview_client.get_group('ICML.cc/2023/Conference/Reviewers/Declined').members) == 0

        messages = openreview_client.get_messages(subject = '[ICML 2023] Invitation to serve as Reviewer')
        assert len(messages) == 6

        for message in messages:
            text = message['content']['text']

            invitation_url = re.search('https://.*\n', text).group(0).replace('https://openreview.net', 'http://localhost:3030').replace('&amp;', '&')[:-1]
            helpers.respond_invitation(selenium, request_page, invitation_url, accept=True, quota=3)

        helpers.await_queue()

        messages = client.get_messages(subject='[ICML 2023] Reviewer Invitation accepted with reduced load')
        assert len(messages) == 6

        assert len(openreview_client.get_group('ICML.cc/2023/Conference/Reviewers').members) == 6
        assert len(openreview_client.get_group('ICML.cc/2023/Conference/Reviewers/Invited').members) == 6
        assert len(openreview_client.get_group('ICML.cc/2023/Conference/Reviewers/Declined').members) == 0

        messages = openreview_client.get_messages(to = 'reviewer6@gmail.com', subject = '[ICML 2023] Invitation to serve as Reviewer')
        invitation_url = re.search('https://.*\n', messages[0]['content']['text']).group(0).replace('https://openreview.net', 'http://localhost:3030').replace('&amp;', '&')[:-1]
        helpers.respond_invitation(selenium, request_page, invitation_url, accept=False)

        helpers.await_queue()

        assert len(openreview_client.get_group('ICML.cc/2023/Conference/Reviewers').members) == 5
        assert len(openreview_client.get_group('ICML.cc/2023/Conference/Reviewers/Invited').members) == 6
        assert len(openreview_client.get_group('ICML.cc/2023/Conference/Reviewers/Declined').members) == 1

        reviewer_client = openreview.api.OpenReviewClient(username='reviewer1@icml.cc', password='1234')

        request_page(selenium, "http://localhost:3030/group?id=ICML.cc/2023/Conference/Reviewers", reviewer_client.token, wait_for_element='header')
        header = selenium.find_element_by_id('header')
        assert 'You have agreed to review up to 1 papers' in header.text

    def test_registrations(self, client, openreview_client, helpers, test_client):

        pc_client=openreview.Client(username='pc@icml.cc', password='1234')
        request_form=pc_client.get_notes(invitation='openreview.net/Support/-/Request_Form')[0]
        venue = openreview.get_conference(client, request_form.id, support_user='openreview.net/Support')

        now = datetime.datetime.utcnow()
        due_date = now + datetime.timedelta(days=3)
        venue.registration_stages.append(openreview.stages.RegistrationStage(committee_id = venue.get_senior_area_chairs_id(),
            name = 'Registration',
            start_date = None,
            due_date = due_date,
            instructions = 'TODO: instructions',
            title = 'ICML 2023 Conference - Senior Area Chair registration'))

        venue.registration_stages.append(openreview.stages.RegistrationStage(committee_id = venue.get_area_chairs_id(),
            name = 'Registration',
            start_date = None,
            due_date = due_date,
            instructions = 'TODO: instructions',
            title = 'ICML 2023 Conference - Area Chair registration',
            additional_fields = {
                'statement': {
                    'description': 'Please write a short (1-2 sentence) statement about why you think peer review is important to the advancement of science.',
                    'value': {
                        'param': {
                            'type': 'string',
                            'input': 'textarea',
                            'maxLength': 200000
                        }
                    },
                    'order': 3
                }
            }))

        venue.registration_stages.append(openreview.stages.RegistrationStage(committee_id = venue.get_reviewers_id(),
            name = 'Registration',
            start_date = None,
            due_date = due_date,
            instructions = 'TODO: instructions',
            title = 'ICML 2023 Conference - Reviewer registration',
            additional_fields = {
                'statement': {
                    'description': 'Please write a short (1-2 sentence) statement about why you think peer review is important to the advancement of science.',
                    'value': {
                        'param': {
                            'type': 'string',
                            'input': 'textarea',
                            'maxLength': 200000
                        }
                    },
                    'order': 3
                }
            },
            remove_fields = ['profile_confirmed', 'expertise_confirmed']))

        venue.create_registration_stages()

        sac_client = openreview.api.OpenReviewClient(username = 'sac1@gmail.com', password='1234')

        registration_forum = sac_client.get_notes(invitation='ICML.cc/2023/Conference/Senior_Area_Chairs/-/Registration_Form')
        assert len(registration_forum) == 1

        sac_client.post_note_edit(invitation='ICML.cc/2023/Conference/Senior_Area_Chairs/-/Registration',
                signatures=['~SAC_ICMLOne1'],
                note=openreview.api.Note(
                    content = {
                        'profile_confirmed': { 'value': 'Yes' },
                        'expertise_confirmed': { 'value': 'Yes' }
                    }
                ))

        ac_client = openreview.api.OpenReviewClient(username = 'ac1@icml.cc', password='1234')

        invitation = ac_client.get_invitation('ICML.cc/2023/Conference/Area_Chairs/-/Registration')
        assert 'statement' in invitation.edit['note']['content']
        assert 'profile_confirmed' in invitation.edit['note']['content']
        assert 'expertise_confirmed' in invitation.edit['note']['content']

        reviewer_client = openreview.api.OpenReviewClient(username = 'reviewer1@icml.cc', password='1234')

        invitation = reviewer_client.get_invitation('ICML.cc/2023/Conference/Reviewers/-/Registration')
        assert 'statement' in invitation.edit['note']['content']
        assert 'profile_confirmed' not in invitation.edit['note']['content']
        assert 'expertise_confirmed' not in invitation.edit['note']['content']

    def test_submissions(self, client, openreview_client, helpers, test_client):

        test_client = openreview.api.OpenReviewClient(token=test_client.token)

        domains = ['umass.edu', 'amazon.com', 'fb.com', 'cs.umass.edu', 'google.com', 'mit.edu', 'deepmind.com', 'co.ux', 'apple.com', 'nvidia.com']
        for i in range(1,102):
            note = openreview.api.Note(
                content = {
                    'title': { 'value': 'Paper title ' + str(i) },
                    'abstract': { 'value': 'This is an abstract ' + str(i) },
                    'authorids': { 'value': ['~SomeFirstName_User1', 'peter@mail.com', 'andrew@' + domains[i % 10]] },
                    'authors': { 'value': ['SomeFirstName User', 'Peter SomeLastName', 'Andrew Mc'] },
                    'keywords': { 'value': ['machine learning', 'nlp'] },
                    'pdf': {'value': '/pdf/' + 'p' * 40 +'.pdf' },
                    'supplementary_material': { 'value': '/attachment/' + 's' * 40 +'.zip'},
                    'financial_aid': { 'value': 'Yes' }
                }
            )
            if i == 1 or i == 101:
                note.content['authors']['value'].append('SAC ICMLOne')
                note.content['authorids']['value'].append('~SAC_ICMLOne1')

            test_client.post_note_edit(invitation='ICML.cc/2023/Conference/-/Submission',
                signatures=['~SomeFirstName_User1'],
                note=note)

        helpers.await_queue(openreview_client)

        submissions = openreview_client.get_notes(invitation='ICML.cc/2023/Conference/-/Submission', sort='number:asc')
        assert len(submissions) == 101
        assert ['ICML.cc/2023/Conference', '~SomeFirstName_User1', 'peter@mail.com', 'andrew@amazon.com', '~SAC_ICMLOne1'] == submissions[0].readers
        assert ['~SomeFirstName_User1', 'peter@mail.com', 'andrew@amazon.com', '~SAC_ICMLOne1'] == submissions[0].content['authorids']['value']

        authors_group = openreview_client.get_group(id='ICML.cc/2023/Conference/Authors')

        for i in range(1,102):
            assert f'ICML.cc/2023/Conference/Submission{i}/Authors' in authors_group.members

        ## delete a submission and update authors group
        submission = submissions[0]
        test_client.post_note_edit(invitation='ICML.cc/2023/Conference/-/Submission',
            signatures=['~SomeFirstName_User1'],
            note=openreview.api.Note(
                id = submission.id,
                ddate = openreview.tools.datetime_millis(datetime.datetime.utcnow()),
                content = {
                    'title': submission.content['title'],
                    'abstract': submission.content['abstract'],
                    'authorids': submission.content['authorids'],
                    'authors': submission.content['authors'],
                    'keywords': submission.content['keywords'],
                    'pdf': submission.content['pdf'],
                    'supplementary_material': submission.content['supplementary_material'],
                    'financial_aid': submission.content['financial_aid'],
                }
            ))

        helpers.await_queue(openreview_client)

        authors_group = openreview_client.get_group(id='ICML.cc/2023/Conference/Authors')

        assert f'ICML.cc/2023/Conference/Submission1/Authors' not in authors_group.members
        for i in range(2,101):
            assert f'ICML.cc/2023/Conference/Submission{i}/Authors' in authors_group.members

        ## restore the submission and update the authors group
        submission = submissions[0]
        test_client.post_note_edit(invitation='ICML.cc/2023/Conference/-/Submission',
            signatures=['~SomeFirstName_User1'],
            note=openreview.api.Note(
                id = submission.id,
                ddate = { 'delete': True },
                content = {
                    'title': submission.content['title'],
                    'abstract': submission.content['abstract'],
                    'authorids': submission.content['authorids'],
                    'authors': submission.content['authors'],
                    'keywords': submission.content['keywords'],
                    'pdf': submission.content['pdf'],
                    'supplementary_material': submission.content['supplementary_material'],
                    'financial_aid': submission.content['financial_aid'],
                }
            ))

        helpers.await_queue(openreview_client)

        authors_group = openreview_client.get_group(id='ICML.cc/2023/Conference/Authors')

        for i in range(1,101):
            assert f'ICML.cc/2023/Conference/Submission{i}/Authors' in authors_group.members

    def test_post_submission(self, client, openreview_client, helpers):

        pc_client=openreview.Client(username='pc@icml.cc', password='1234')
        request_form=pc_client.get_notes(invitation='openreview.net/Support/-/Request_Form')[0]
        venue = openreview.get_conference(client, request_form.id, support_user='openreview.net/Support')

        ## close the submissions
        now = datetime.datetime.utcnow()
        due_date = now - datetime.timedelta(days=1)
        pc_client.post_note(openreview.Note(
            content={
                'title': 'Thirty-ninth International Conference on Machine Learning',
                'Official Venue Name': 'Thirty-ninth International Conference on Machine Learning',
                'Abbreviated Venue Name': 'ICML 2023',
                'Official Website URL': 'https://icml.cc',
                'program_chair_emails': ['pc@icml.cc', 'pc3@icml.cc'],
                'contact_email': 'pc@icml.cc',
                'Venue Start Date': '2023/07/01',
                'Submission Deadline': due_date.strftime('%Y/%m/%d'),
                'Location': 'Virtual',
                'How did you hear about us?': 'ML conferences',
                'Expected Submissions': '100',
                'Additional Submission Options': {
                    "supplementary_material": {
                        "value": {
                            "param": {
                                "type": "file",
                                "extensions": [
                                    "zip",
                                    "pdf",
                                    "tgz",
                                    "gz"
                                ],
                                "maxSize": 100,
                                "optional": True,
                                "deletable": True
                            }
                        },
                        "description": "All supplementary material must be self-contained and zipped into a single file. Note that supplementary material will be visible to reviewers and the public throughout and after the review period, and ensure all material is anonymized. The maximum file size is 100MB.",
                        "order": 8
                    },
                    "financial_aid": {
                        "order": 9,
                        "description": "Each paper may designate up to one (1) icml.cc account email address of a corresponding student author who confirms that they would need the support to attend the conference, and agrees to volunteer if they get selected.",
                        "value": {
                            "param": {
                                "type": "string",
                                "maxLength": 100,
                                "optional": True
                            }
                        }
                    }
                }

            },
            forum=request_form.forum,
            invitation='openreview.net/Support/-/Request{}/Revision'.format(request_form.number),
            readers=['ICML.cc/2023/Conference/Program_Chairs', 'openreview.net/Support'],
            referent=request_form.forum,
            replyto=request_form.forum,
            signatures=['~Program_ICMLChair1'],
            writers=[]
        ))

        helpers.await_queue()

        pc_client_v2=openreview.api.OpenReviewClient(username='pc@icml.cc', password='1234')
        submission_invitation = pc_client_v2.get_invitation('ICML.cc/2023/Conference/-/Submission')
        assert submission_invitation.expdate < openreview.tools.datetime_millis(now)

        ## make submissions visible to ACs only
        pc_client.post_note(openreview.Note(
            content= {
                'force': 'Yes',
                'submission_readers': 'All area chairs only',
                'hide_fields': ['financial_aid']
            },
            forum= request_form.id,
            invitation= f'openreview.net/Support/-/Request{request_form.number}/Post_Submission',
            readers= ['ICML.cc/2023/Conference/Program_Chairs', 'openreview.net/Support'],
            referent= request_form.id,
            replyto= request_form.id,
            signatures= ['~Program_ICMLChair1'],
            writers= [],
        ))

        helpers.await_queue()

        ac_client = openreview.api.OpenReviewClient(username = 'ac1@icml.cc', password='1234')
        submissions = ac_client.get_notes(invitation='ICML.cc/2023/Conference/-/Submission', sort='number:asc')
        assert len(submissions) == 101
        assert ['ICML.cc/2023/Conference',
        'ICML.cc/2023/Conference/Senior_Area_Chairs',
        'ICML.cc/2023/Conference/Area_Chairs',
        'ICML.cc/2023/Conference/Submission1/Authors'] == submissions[0].readers
        assert ['ICML.cc/2023/Conference',
        'ICML.cc/2023/Conference/Submission1/Authors'] == submissions[0].writers
        assert ['ICML.cc/2023/Conference/Submission1/Authors'] == submissions[0].signatures
        assert 'authorids' not in submissions[0].content
        assert 'authors' not in submissions[0].content
        assert 'financial_aid'not in submissions[0].content

        ## make submissions visible to the committee
        pc_client.post_note(openreview.Note(
            content= {
                'force': 'Yes',
                'submission_readers': 'All program committee (all reviewers, all area chairs, all senior area chairs if applicable)',
                'hide_fields': ['financial_aid']
            },
            forum= request_form.id,
            invitation= f'openreview.net/Support/-/Request{request_form.number}/Post_Submission',
            readers= ['ICML.cc/2023/Conference/Program_Chairs', 'openreview.net/Support'],
            referent= request_form.id,
            replyto= request_form.id,
            signatures= ['~Program_ICMLChair1'],
            writers= [],
        ))

        helpers.await_queue()

        submissions = venue.get_submissions(sort='number:asc')
        assert len(submissions) == 101

        #desk-reject paper
        pc_openreview_client = openreview.api.OpenReviewClient(username='pc@icml.cc', password='1234')

        submission = submissions[-1]
        desk_reject_note = pc_openreview_client.post_note_edit(invitation=f'ICML.cc/2023/Conference/Submission{submission.number}/-/Desk_Rejection',
                                    signatures=['ICML.cc/2023/Conference/Program_Chairs'],
                                    note=openreview.api.Note(
                                        content={
                                            'desk_reject_comments': { 'value': 'Out of scope' },
                                        }
                                    ))

        helpers.await_queue_edit(openreview_client, edit_id=desk_reject_note['id'])
        helpers.await_queue_edit(openreview_client, invitation='ICML.cc/2023/Conference/-/Desk_Rejected_Submission')

        note = pc_openreview_client.get_note(desk_reject_note['note']['forum'])
        assert note
        assert note.invitations == ['ICML.cc/2023/Conference/-/Submission', 'ICML.cc/2023/Conference/-/Edit', 'ICML.cc/2023/Conference/-/Desk_Rejected_Submission']

        submissions = venue.get_submissions(sort='number:asc')
        assert len(submissions) == 100

        ac_client = openreview.api.OpenReviewClient(username = 'ac1@icml.cc', password='1234')
        submissions = ac_client.get_notes(invitation='ICML.cc/2023/Conference/-/Submission', sort='number:asc')
        assert len(submissions) == 101
        assert ['ICML.cc/2023/Conference',
        'ICML.cc/2023/Conference/Senior_Area_Chairs',
        'ICML.cc/2023/Conference/Area_Chairs',
        'ICML.cc/2023/Conference/Reviewers',
        'ICML.cc/2023/Conference/Submission1/Authors'] == submissions[0].readers
        assert ['ICML.cc/2023/Conference',
        'ICML.cc/2023/Conference/Submission1/Authors'] == submissions[0].writers
        assert ['ICML.cc/2023/Conference/Submission1/Authors'] == submissions[0].signatures
        assert 'authorids' not in submissions[0].content
        assert 'authors' not in submissions[0].content
        assert 'financial_aid'not in submissions[0].content

        assert client.get_group('ICML.cc/2023/Conference/Submission1/Reviewers')
        assert client.get_group('ICML.cc/2023/Conference/Submission1/Area_Chairs')
        assert client.get_group('ICML.cc/2023/Conference/Submission1/Senior_Area_Chairs')

        active_venues = pc_client.get_group('active_venues')
        assert 'ICML.cc/2023/Conference' in active_venues.members

        ## try to edit a submission as a PC
        submissions = pc_client_v2.get_notes(invitation='ICML.cc/2023/Conference/-/Submission', sort='number:asc')
        submission = submissions[0]
        pc_client_v2.post_note_edit(invitation='ICML.cc/2023/Conference/-/PC_Revision',
            signatures=['ICML.cc/2023/Conference/Program_Chairs'],
            note=openreview.api.Note(
                id = submission.id,
                content = {
                    'title': { 'value': submission.content['title']['value'] + ' Version 2' },
                    'abstract': submission.content['abstract'],
                    'authorids': { 'value': submission.content['authorids']['value'] + ['melisa@yahoo.com'] },
                    'authors': { 'value': submission.content['authors']['value'] + ['Melisa ICML'] },
                    'keywords': submission.content['keywords'],
                    'pdf': submission.content['pdf'],
                    'supplementary_material': { 'value': { 'delete': True } },
                    'financial_aid': { 'value': submission.content['financial_aid']['value'] },
                }
            ))

        helpers.await_queue(openreview_client)

        submission = ac_client.get_note(submission.id)
        assert ['ICML.cc/2023/Conference',
        'ICML.cc/2023/Conference/Senior_Area_Chairs',
        'ICML.cc/2023/Conference/Area_Chairs',
        'ICML.cc/2023/Conference/Reviewers',
        'ICML.cc/2023/Conference/Submission1/Authors'] == submission.readers
        assert ['ICML.cc/2023/Conference',
        'ICML.cc/2023/Conference/Submission1/Authors'] == submission.writers
        assert ['ICML.cc/2023/Conference/Submission1/Authors'] == submission.signatures
        assert 'authorids' not in submission.content
        assert 'authors' not in submission.content
        assert 'financial_aid'not in submission.content
        assert 'supplementary_material'not in submission.content

        author_group = pc_client_v2.get_group('ICML.cc/2023/Conference/Submission1/Authors')
        assert ['~SomeFirstName_User1', 'peter@mail.com', 'andrew@amazon.com', '~SAC_ICMLOne1', 'melisa@yahoo.com'] == author_group.members

        messages = openreview_client.get_messages(to = 'melisa@yahoo.com', subject = 'ICML 2023 has received a new revision of your submission titled Paper title 1 Version 2')
        assert len(messages) == 1
        assert messages[0]['content']['text'] == f'''Your new revision of the submission to ICML 2023 has been posted.

Title: Paper title 1 Version 2

Abstract This is an abstract 1

To view your submission, click here: https://openreview.net/forum?id={submission.id}'''

    def test_ac_bidding(self, client, openreview_client, helpers, test_client):

        pc_client=openreview.Client(username='pc@icml.cc', password='1234')
        pc_client_v2=openreview.api.OpenReviewClient(username='pc@icml.cc', password='1234')
        request_form=pc_client.get_notes(invitation='openreview.net/Support/-/Request_Form')[0]

        submissions = pc_client_v2.get_notes(invitation='ICML.cc/2023/Conference/-/Submission', sort='number:asc')

        openreview.tools.replace_members_with_ids(openreview_client, openreview_client.get_group('ICML.cc/2023/Conference/Area_Chairs'))

        with open(os.path.join(os.path.dirname(__file__), 'data/rev_scores_venue.csv'), 'w') as file_handle:
            writer = csv.writer(file_handle)
            for submission in submissions:
                for ac in openreview_client.get_group('ICML.cc/2023/Conference/Area_Chairs').members:
                    writer.writerow([submission.id, ac, round(random.random(), 2)])

        affinity_scores_url = client.put_attachment(os.path.join(os.path.dirname(__file__), 'data/rev_scores_venue.csv'), f'openreview.net/Support/-/Request{request_form.number}/Paper_Matching_Setup', 'upload_affinity_scores')

        ## setup matching data before starting bidding
        client.post_note(openreview.Note(
            content={
                'title': 'Paper Matching Setup',
                'matching_group': 'ICML.cc/2023/Conference/Area_Chairs',
                'compute_conflicts': 'Yes',
                'compute_affinity_scores': 'No',
                'upload_affinity_scores': affinity_scores_url

            },
            forum=request_form.id,
            replyto=request_form.id,
            invitation=f'openreview.net/Support/-/Request{request_form.number}/Paper_Matching_Setup',
            readers=['ICML.cc/2023/Conference/Program_Chairs', 'openreview.net/Support'],
            signatures=['~Program_ICMLChair1'],
            writers=[]
        ))
        helpers.await_queue()

        assert openreview_client.get_invitation('ICML.cc/2023/Conference/Area_Chairs/-/Conflict')
        assert openreview_client.get_invitation('ICML.cc/2023/Conference/Area_Chairs/-/Affinity_Score')

        affinity_score_count =  openreview_client.get_edges_count(invitation='ICML.cc/2023/Conference/Area_Chairs/-/Affinity_Score')
        assert affinity_score_count == 100 * 2 ## submissions * ACs

        assert openreview_client.get_edges_count(invitation='ICML.cc/2023/Conference/Area_Chairs/-/Conflict') == 0

        openreview.tools.replace_members_with_ids(openreview_client, openreview_client.get_group('ICML.cc/2023/Conference/Reviewers'))

        with open(os.path.join(os.path.dirname(__file__), 'data/rev_scores_venue.csv'), 'w') as file_handle:
            writer = csv.writer(file_handle)
            for submission in submissions:
                for ac in openreview_client.get_group('ICML.cc/2023/Conference/Reviewers').members:
                    writer.writerow([submission.id, ac, round(random.random(), 2)])

        affinity_scores_url = client.put_attachment(os.path.join(os.path.dirname(__file__), 'data/rev_scores_venue.csv'), f'openreview.net/Support/-/Request{request_form.number}/Paper_Matching_Setup', 'upload_affinity_scores')

        client.post_note(openreview.Note(
            content={
                'title': 'Paper Matching Setup',
                'matching_group': 'ICML.cc/2023/Conference/Reviewers',
                'compute_conflicts': 'Yes',
                'compute_affinity_scores': 'No',
                'upload_affinity_scores': affinity_scores_url
            },
            forum=request_form.id,
            replyto=request_form.id,
            invitation=f'openreview.net/Support/-/Request{request_form.number}/Paper_Matching_Setup',
            readers=['ICML.cc/2023/Conference/Program_Chairs', 'openreview.net/Support'],
            signatures=['~Program_ICMLChair1'],
            writers=[]
        ))
        helpers.await_queue()

        assert openreview_client.get_invitation('ICML.cc/2023/Conference/Reviewers/-/Conflict')

        assert openreview_client.get_edges_count(invitation='ICML.cc/2023/Conference/Reviewers/-/Conflict') == 0

        affinity_scores =  openreview_client.get_grouped_edges(invitation='ICML.cc/2023/Conference/Reviewers/-/Affinity_Score', groupby='id')
        assert affinity_scores
        assert len(affinity_scores) == 100 * 5 ## submissions * reviewers

        now = datetime.datetime.utcnow()
        due_date = now + datetime.timedelta(days=3)

        bid_stage_note = pc_client.post_note(openreview.Note(
            content={
                'bid_start_date': now.strftime('%Y/%m/%d'),
                'bid_due_date': due_date.strftime('%Y/%m/%d'),
                'bid_count': 5
            },
            forum=request_form.forum,
            replyto=request_form.forum,
            referent=request_form.forum,
            invitation=f'openreview.net/Support/-/Request{request_form.number}/Bid_Stage',
            readers=['ICML.cc/2023/Conference/Program_Chairs', 'openreview.net/Support'],
            signatures=['~Program_ICMLChair1'],
            writers=[]
        ))

        helpers.await_queue()

        assert openreview_client.get_invitation('ICML.cc/2023/Conference/Area_Chairs/-/Bid')
        assert openreview_client.get_invitation('ICML.cc/2023/Conference/Reviewers/-/Bid')


    def test_assignment(self, client, openreview_client, helpers):

        pc_client=openreview.Client(username='pc@icml.cc', password='1234')
        pc_client_v2=openreview.api.OpenReviewClient(username='pc@icml.cc', password='1234')
        request_form=pc_client.get_notes(invitation='openreview.net/Support/-/Request_Form')[0]

        openreview.tools.replace_members_with_ids(openreview_client, openreview_client.get_group('ICML.cc/2023/Conference/Senior_Area_Chairs'))

        with open(os.path.join(os.path.dirname(__file__), 'data/rev_scores_venue.csv'), 'w') as file_handle:
            writer = csv.writer(file_handle)
            for sac in openreview_client.get_group('ICML.cc/2023/Conference/Senior_Area_Chairs').members:
                for ac in openreview_client.get_group('ICML.cc/2023/Conference/Area_Chairs').members:
                    writer.writerow([ac, sac, round(random.random(), 2)])

        affinity_scores_url = client.put_attachment(os.path.join(os.path.dirname(__file__), 'data/rev_scores_venue.csv'), f'openreview.net/Support/-/Request{request_form.number}/Paper_Matching_Setup', 'upload_affinity_scores')

        ## setup matching to assign SAC to each AC
        client.post_note(openreview.Note(
            content={
                'title': 'Paper Matching Setup',
                'matching_group': 'ICML.cc/2023/Conference/Senior_Area_Chairs',
                'compute_conflicts': 'No',
                'compute_affinity_scores': 'No',
                'upload_affinity_scores': affinity_scores_url

            },
            forum=request_form.id,
            replyto=request_form.id,
            invitation=f'openreview.net/Support/-/Request{request_form.number}/Paper_Matching_Setup',
            readers=['ICML.cc/2023/Conference/Program_Chairs', 'openreview.net/Support'],
            signatures=['~Program_ICMLChair1'],
            writers=[]
        ))
        helpers.await_queue()

        assert pc_client_v2.get_edges_count(invitation='ICML.cc/2023/Conference/Senior_Area_Chairs/-/Affinity_Score') == 4

        openreview_client.post_edge(openreview.api.Edge(
            invitation = 'ICML.cc/2023/Conference/Senior_Area_Chairs/-/Proposed_Assignment',
            head = '~AC_ICMLOne1',
            tail = '~SAC_ICMLOne1',
            signatures = ['ICML.cc/2023/Conference/Program_Chairs'],
            weight = 1,
            label = 'sac-matching'
        ))

        openreview_client.post_edge(openreview.api.Edge(
            invitation = 'ICML.cc/2023/Conference/Senior_Area_Chairs/-/Proposed_Assignment',
            head = '~AC_ICMLTwo1',
            tail = '~SAC_ICMLOne1',
            signatures = ['ICML.cc/2023/Conference/Program_Chairs'],
            weight = 1,
            label = 'sac-matching'
        ))

        venue = openreview.helpers.get_conference(pc_client, request_form.id, setup=False)

        venue.set_assignments(assignment_title='sac-matching', committee_id='ICML.cc/2023/Conference/Senior_Area_Chairs')

        sac_assignment_count = pc_client_v2.get_edges_count(invitation='ICML.cc/2023/Conference/Senior_Area_Chairs/-/Assignment')
        assert sac_assignment_count == 2

        ## setup matching ACs to take into account the SAC conflicts
        client.post_note(openreview.Note(
            content={
                'title': 'Paper Matching Setup',
                'matching_group': 'ICML.cc/2023/Conference/Area_Chairs',
                'compute_conflicts': 'Yes',
                'compute_affinity_scores': 'No'

            },
            forum=request_form.id,
            replyto=request_form.id,
            invitation=f'openreview.net/Support/-/Request{request_form.number}/Paper_Matching_Setup',
            readers=['ICML.cc/2023/Conference/Program_Chairs', 'openreview.net/Support'],
            signatures=['~Program_ICMLChair1'],
            writers=[]
        ))
        helpers.await_queue()

        assert pc_client_v2.get_edges_count(invitation='ICML.cc/2023/Conference/Area_Chairs/-/Affinity_Score') == 200
        assert pc_client_v2.get_edges_count(invitation='ICML.cc/2023/Conference/Area_Chairs/-/Conflict') == 200 ## assigned SAC is an author of paper 1

        submissions = pc_client_v2.get_notes(content= { 'venueid': 'ICML.cc/2023/Conference/Submission'}, sort='number:asc')

        reviewers_proposed_edges = []
        for i in range(0,20):
            for r in ['~Reviewer_ICMLOne1', '~Reviewer_ICMLTwo1', '~Reviewer_ICMLThree1']:
                reviewers_proposed_edges.append(openreview.api.Edge(
                    invitation = 'ICML.cc/2023/Conference/Reviewers/-/Proposed_Assignment',
                    head = submissions[i].id,
                    tail = r,
                    signatures = ['ICML.cc/2023/Conference/Program_Chairs'],
                    weight = 1,
                    label = 'reviewer-matching'
                ))

            openreview_client.post_edge(openreview.api.Edge(
                invitation = 'ICML.cc/2023/Conference/Area_Chairs/-/Proposed_Assignment',
                head = submissions[i].id,
                tail = '~AC_ICMLOne1',
                signatures = ['ICML.cc/2023/Conference/Program_Chairs'],
                weight = 1,
                label = 'ac-matching'
            ))

        for i in range(20,40):
            for r in ['~Reviewer_ICMLTwo1', '~Reviewer_ICMLThree1', '~Reviewer_ICMLFour1']:
                reviewers_proposed_edges.append(openreview.api.Edge(
                    invitation = 'ICML.cc/2023/Conference/Reviewers/-/Proposed_Assignment',
                    head = submissions[i].id,
                    tail = r,
                    signatures = ['ICML.cc/2023/Conference/Program_Chairs'],
                    weight = 1,
                    label = 'reviewer-matching'
                ))

            openreview_client.post_edge(openreview.api.Edge(
                invitation = 'ICML.cc/2023/Conference/Area_Chairs/-/Proposed_Assignment',
                head = submissions[i].id,
                tail = '~AC_ICMLOne1',
                signatures = ['ICML.cc/2023/Conference/Program_Chairs'],
                weight = 1,
                label = 'ac-matching'
            ))

        for i in range(40,60):
            for r in ['~Reviewer_ICMLThree1', '~Reviewer_ICMLFour1', '~Reviewer_ICMLFive1']:
                reviewers_proposed_edges.append(openreview.api.Edge(
                    invitation = 'ICML.cc/2023/Conference/Reviewers/-/Proposed_Assignment',
                    head = submissions[i].id,
                    tail = r,
                    signatures = ['ICML.cc/2023/Conference/Program_Chairs'],
                    weight = 1,
                    label = 'reviewer-matching'
                ))

            openreview_client.post_edge(openreview.api.Edge(
                invitation = 'ICML.cc/2023/Conference/Area_Chairs/-/Proposed_Assignment',
                head = submissions[i].id,
                tail = '~AC_ICMLOne1',
                signatures = ['ICML.cc/2023/Conference/Program_Chairs'],
                weight = 1,
                label = 'ac-matching'
            ))


        for i in range(60,80):
            for r in ['~Reviewer_ICMLFour1', '~Reviewer_ICMLFive1', '~Reviewer_ICMLOne1']:
                reviewers_proposed_edges.append(openreview.api.Edge(
                    invitation = 'ICML.cc/2023/Conference/Reviewers/-/Proposed_Assignment',
                    head = submissions[i].id,
                    tail = r,
                    signatures = ['ICML.cc/2023/Conference/Program_Chairs'],
                    weight = 1,
                    label = 'reviewer-matching'
                ))

            openreview_client.post_edge(openreview.api.Edge(
                invitation = 'ICML.cc/2023/Conference/Area_Chairs/-/Proposed_Assignment',
                head = submissions[i].id,
                tail = '~AC_ICMLTwo1',
                signatures = ['ICML.cc/2023/Conference/Program_Chairs'],
                weight = 1,
                label = 'ac-matching'
            ))

        for i in range(80,100):
            for r in ['~Reviewer_ICMLFive1', '~Reviewer_ICMLOne1', '~Reviewer_ICMLTwo1']:
                reviewers_proposed_edges.append(openreview.api.Edge(
                    invitation = 'ICML.cc/2023/Conference/Reviewers/-/Proposed_Assignment',
                    head = submissions[i].id,
                    tail = r,
                    signatures = ['ICML.cc/2023/Conference/Program_Chairs'],
                    weight = 1,
                    label = 'reviewer-matching'
                ))

            openreview_client.post_edge(openreview.api.Edge(
                invitation = 'ICML.cc/2023/Conference/Area_Chairs/-/Proposed_Assignment',
                head = submissions[i].id,
                tail = '~AC_ICMLTwo1',
                signatures = ['ICML.cc/2023/Conference/Program_Chairs'],
                weight = 1,
                label = 'ac-matching'
            ))

        openreview.tools.post_bulk_edges(client=openreview_client, edges=reviewers_proposed_edges)

        venue.set_assignments(assignment_title='ac-matching', committee_id='ICML.cc/2023/Conference/Area_Chairs')

        ac_group = pc_client_v2.get_group('ICML.cc/2023/Conference/Submission1/Area_Chairs')
        assert ['~AC_ICMLOne1'] == ac_group.members

        ac_group = pc_client_v2.get_group('ICML.cc/2023/Conference/Submission100/Area_Chairs')
        assert ['~AC_ICMLTwo1'] == ac_group.members

        sac_group = pc_client_v2.get_group('ICML.cc/2023/Conference/Submission1/Senior_Area_Chairs')
        assert ['~SAC_ICMLOne1'] == sac_group.members

        sac_group = pc_client_v2.get_group('ICML.cc/2023/Conference/Submission100/Senior_Area_Chairs')
        assert ['~SAC_ICMLOne1'] == sac_group.members

        venue.set_assignments(assignment_title='reviewer-matching', committee_id='ICML.cc/2023/Conference/Reviewers')

        reviewers_group = pc_client_v2.get_group('ICML.cc/2023/Conference/Submission1/Reviewers')
        assert len(reviewers_group.members) == 3
        assert '~Reviewer_ICMLOne1' in reviewers_group.members
        assert '~Reviewer_ICMLTwo1' in reviewers_group.members
        assert '~Reviewer_ICMLThree1' in reviewers_group.members

        reviewers_group = pc_client_v2.get_group('ICML.cc/2023/Conference/Submission100/Reviewers')
        assert len(reviewers_group.members) == 3
        assert '~Reviewer_ICMLOne1' in reviewers_group.members
        assert '~Reviewer_ICMLTwo1' in reviewers_group.members
        assert '~Reviewer_ICMLFive1' in reviewers_group.members


        ## Change assigned SAC
        assignment_edge = pc_client_v2.get_edges(invitation='ICML.cc/2023/Conference/Senior_Area_Chairs/-/Assignment', head='~AC_ICMLTwo1', tail='~SAC_ICMLOne1')[0]
        assignment_edge.ddate = openreview.tools.datetime_millis(datetime.datetime.utcnow())
        pc_client_v2.post_edge(assignment_edge)

        helpers.await_queue(openreview_client)

        sac_group = pc_client_v2.get_group('ICML.cc/2023/Conference/Submission100/Senior_Area_Chairs')
        assert [] == sac_group.members

        openreview_client.post_edge(openreview.api.Edge(
            invitation = 'ICML.cc/2023/Conference/Senior_Area_Chairs/-/Assignment',
            head = '~AC_ICMLTwo1',
            tail = '~SAC_ICMLTwo1',
            signatures = ['ICML.cc/2023/Conference/Program_Chairs'],
            weight = 1
        ))

        helpers.await_queue(openreview_client)

        sac_group = pc_client_v2.get_group('ICML.cc/2023/Conference/Submission100/Senior_Area_Chairs')
        assert ['~SAC_ICMLTwo1'] == sac_group.members

        ## Change assigned AC
        assignment_edge = pc_client_v2.get_edges(invitation='ICML.cc/2023/Conference/Area_Chairs/-/Assignment', head=submissions[0].id, tail='~AC_ICMLOne1')[0]
        assignment_edge.ddate = openreview.tools.datetime_millis(datetime.datetime.utcnow())
        pc_client_v2.post_edge(assignment_edge)

        helpers.await_queue(openreview_client)

        sac_group = pc_client_v2.get_group('ICML.cc/2023/Conference/Submission1/Senior_Area_Chairs')
        assert [] == sac_group.members

        openreview_client.post_edge(openreview.api.Edge(
            invitation = 'ICML.cc/2023/Conference/Area_Chairs/-/Assignment',
            head = submissions[0].id,
            tail = '~AC_ICMLTwo1',
            signatures = ['ICML.cc/2023/Conference/Program_Chairs'],
            weight = 1
        ))

        helpers.await_queue(openreview_client)

        sac_group = pc_client_v2.get_group('ICML.cc/2023/Conference/Submission1/Senior_Area_Chairs')
        assert ['~SAC_ICMLTwo1'] == sac_group.members

    def test_review_stage(self, openreview_client, helpers):

        pc_client=openreview.Client(username='pc@icml.cc', password='1234')
        request_form=pc_client.get_notes(invitation='openreview.net/Support/-/Request_Form')[0]

        now = datetime.datetime.utcnow()
        start_date = now - datetime.timedelta(days=2)
        due_date = now + datetime.timedelta(days=3)
        review_stage_note = openreview.Note(
            content={
                'review_start_date': start_date.strftime('%Y/%m/%d'),
                'review_deadline': due_date.strftime('%Y/%m/%d'),
                'make_reviews_public': 'No, reviews should NOT be revealed publicly when they are posted',
                'release_reviews_to_authors': 'No, reviews should NOT be revealed when they are posted to the paper\'s authors',
                'release_reviews_to_reviewers': 'Reviews should be immediately revealed to the paper\'s reviewers who have already submitted their review',
                'remove_review_form_options': 'title,rating',
                'email_program_chairs_about_reviews': 'Yes, email program chairs for each review received',
                'review_rating_field_name': 'review_rating',
                'additional_review_form_options': {
                    'review_rating': {
                        'order': 3,
                        'value': {
                            'param': {
                                'type': 'string',
                                'enum': [
                                    '10: Top 5% of accepted papers, seminal paper',
                                    '9: Top 15% of accepted papers, strong accept',
                                    '8: Top 50% of accepted papers, clear accept',
                                    '7: Good paper, accept',
                                    '6: Marginally above acceptance threshold',
                                    '5: Marginally below acceptance threshold',
                                    '4: Ok but not good enough - rejection',
                                    '3: Clear rejection',
                                    '2: Strong rejection',
                                    '1: Trivial or wrong'
                                ]
                            }
                        }
                    }
                }
            },
            forum=request_form.forum,
            invitation=f'openreview.net/Support/-/Request{request_form.number}/Review_Stage',
            readers=['ICML.cc/2023/Conference/Program_Chairs', 'openreview.net/Support'],
            replyto=request_form.forum,
            referent=request_form.forum,
            signatures=['~Program_ICMLChair1'],
            writers=[]
        )

        review_stage_note=pc_client.post_note(review_stage_note)

        helpers.await_queue()

        assert openreview_client.get_invitation('ICML.cc/2023/Conference/Submission1/-/Official_Review')
        assert openreview_client.get_invitation('ICML.cc/2023/Conference/Submission2/-/Official_Review')
        assert openreview_client.get_invitation('ICML.cc/2023/Conference/Submission3/-/Official_Review')
        assert openreview_client.get_invitation('ICML.cc/2023/Conference/Submission4/-/Official_Review')
        assert openreview_client.get_invitation('ICML.cc/2023/Conference/Submission5/-/Official_Review')

        openreview_client.add_members_to_group(f'ICML.cc/2023/Conference/Submission1/Reviewers', '~Reviewer_ICMLOne1')
        openreview_client.add_members_to_group(f'ICML.cc/2023/Conference/Submission1/Reviewers', '~Reviewer_ICMLTwo1')
        openreview_client.add_members_to_group(f'ICML.cc/2023/Conference/Submission1/Reviewers', '~Reviewer_ICMLThree1')

        reviewer_client = openreview.api.OpenReviewClient(username='reviewer1@icml.cc', password='1234')

        anon_groups = reviewer_client.get_groups(prefix='ICML.cc/2023/Conference/Submission1/Reviewer_', signatory='~Reviewer_ICMLOne1')
        anon_group_id = anon_groups[0].id

        reviewer_client.post_note_edit(
            invitation='ICML.cc/2023/Conference/Submission1/-/Official_Review',
            signatures=[anon_group_id],
            note=openreview.api.Note(
                content={
                    'review': { 'value': 'good paper' },
                    'review_rating': { 'value': '7: Good paper, accept'},
                    'confidence': { 'value': '4: The reviewer is confident but not absolutely certain that the evaluation is correct'}
                }
            )
        )

    def test_comment_stage(self, openreview_client, helpers):

        pc_client=openreview.Client(username='pc@icml.cc', password='1234')
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
            readers=['ICML.cc/2023/Conference/Program_Chairs', 'openreview.net/Support'],
            replyto=request_form.forum,
            referent=request_form.forum,
            signatures=['~Program_ICMLChair1'],
            writers=[]
        ))

        helpers.await_queue()

        assert openreview_client.get_invitation('ICML.cc/2023/Conference/Submission1/-/Official_Comment')
        assert openreview_client.get_invitation('ICML.cc/2023/Conference/Submission2/-/Official_Comment')
        assert openreview_client.get_invitation('ICML.cc/2023/Conference/Submission3/-/Official_Comment')
        assert openreview_client.get_invitation('ICML.cc/2023/Conference/Submission4/-/Official_Comment')
        assert openreview_client.get_invitation('ICML.cc/2023/Conference/Submission5/-/Official_Comment')


    def test_meta_review_stage(self, openreview_client, helpers):

        pc_client=openreview.Client(username='pc@icml.cc', password='1234')
        request_form=pc_client.get_notes(invitation='openreview.net/Support/-/Request_Form')[0]

        now = datetime.datetime.utcnow()
        start_date = now - datetime.timedelta(days=2)
        due_date = now + datetime.timedelta(days=3)
        pc_client.post_note(openreview.Note(
            content={
                'make_meta_reviews_public': 'No, meta reviews should NOT be revealed publicly when they are posted',
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
            forum=request_form.forum,
            invitation=f'openreview.net/Support/-/Request{request_form.number}/Meta_Review_Stage',
            readers=['ICML.cc/2023/Conference/Program_Chairs', 'openreview.net/Support'],
            replyto=request_form.forum,
            referent=request_form.forum,
            signatures=['~Program_ICMLChair1'],
            writers=[]
        ))


        helpers.await_queue()

        assert openreview_client.get_invitation('ICML.cc/2023/Conference/Submission1/-/Meta_Review')
        assert openreview_client.get_invitation('ICML.cc/2023/Conference/Submission2/-/Meta_Review')
        assert openreview_client.get_invitation('ICML.cc/2023/Conference/Submission3/-/Meta_Review')
        assert openreview_client.get_invitation('ICML.cc/2023/Conference/Submission4/-/Meta_Review')
        assert openreview_client.get_invitation('ICML.cc/2023/Conference/Submission5/-/Meta_Review')


    def test_decision_stage(self, openreview_client, helpers):

        pc_client=openreview.Client(username='pc@icml.cc', password='1234')
        request_form=pc_client.get_notes(invitation='openreview.net/Support/-/Request_Form')[0]

        # Post a decision stage note
        now = datetime.datetime.utcnow()
        start_date = now - datetime.timedelta(days=2)
        due_date = now + datetime.timedelta(days=3)

        decision_stage_note = pc_client.post_note(openreview.Note(
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
            forum=request_form.forum,
            invitation=f'openreview.net/Support/-/Request{request_form.number}/Decision_Stage',
            readers=['ICML.cc/2023/Conference/Program_Chairs', 'openreview.net/Support'],
            replyto=request_form.forum,
            referent=request_form.forum,
            signatures=['~Program_ICMLChair1'],
            writers=[]
        ))
        assert decision_stage_note
        helpers.await_queue()

        assert openreview_client.get_invitation('ICML.cc/2023/Conference/Submission1/-/Decision')
        assert openreview_client.get_invitation('ICML.cc/2023/Conference/Submission2/-/Decision')
        assert openreview_client.get_invitation('ICML.cc/2023/Conference/Submission3/-/Decision')
        assert openreview_client.get_invitation('ICML.cc/2023/Conference/Submission4/-/Decision')
        assert openreview_client.get_invitation('ICML.cc/2023/Conference/Submission5/-/Decision')

    def test_forum_chat(self, openreview_client, helpers):

        openreview_client.post_invitation_edit(
            invitations='ICML.cc/2023/Conference/-/Edit',
            readers = ['ICML.cc/2023/Conference'],
            writers = ['ICML.cc/2023/Conference'],
            signatures = ['ICML.cc/2023/Conference'],
            invitation = openreview.api.Invitation(
                id = 'ICML.cc/2023/Conference/-/Submission',
                reply_forum_views = [
                    {
                        'id': 'all',
                        'label': 'All'
                    },
                    {
                        'id': 'discussion',
                        'label': 'Discussion',
                        'filter': '-invitations:ICML.cc/2023/Conference/Submission${note.number}/-/Chat',
                        'nesting': 3,
                        'sort': 'date-desc',
                        'layout': 'default',
                        'live': True
                    },
                    {
                        'id': 'reviewers-chat',
                        'label': 'Reviewers Chat',
                        'filter': 'invitations:ICML.cc/2023/Conference/Submission${note.number}/-/Chat,ICML.cc/2023/Conference/Submission${note.number}/-/Official_Review',
                        'nesting': 1,
                        'sort': 'date-asc',
                        'layout': 'chat',
                        'live': True,
                        'expandedInvitations': ['ICML.cc/2023/Conference/Submission${note.number}/-/Chat']
                    }
                ]
            )
        )

        submission_invitation = openreview_client.get_invitation('ICML.cc/2023/Conference/-/Submission')
        assert len(submission_invitation.reply_forum_views)

        submission = openreview_client.get_notes(invitation='ICML.cc/2023/Conference/-/Submission', number=1)[0]

        openreview_client.post_invitation_edit(
            invitations='ICML.cc/2023/Conference/-/Edit',
            readers = ['ICML.cc/2023/Conference'],
            writers = ['ICML.cc/2023/Conference'],
            signatures = ['ICML.cc/2023/Conference'],
            invitation = openreview.api.Invitation(
                id = 'ICML.cc/2023/Conference/Submission1/-/Chat',
                readers = ['everyone'],
                writers = ['ICML.cc/2023/Conference'],
                signatures = ['ICML.cc/2023/Conference'],
                invitees = ['ICML.cc/2023/Conference/Program_Chairs', 'ICML.cc/2023/Conference/Submission1/Area_Chairs', 'ICML.cc/2023/Conference/Submission1/Reviewers'],
                edit = {
                    'readers': ['ICML.cc/2023/Conference', '${2/signatures}'],
                    'writers': ['ICML.cc/2023/Conference'],
                    'signatures': {
                        'param': {
                            'enum': [
                                'ICML.cc/2023/Conference/Program_Chairs',
                                'ICML.cc/2023/Conference/Submission1/Area_Chair_.*',
                                'ICML.cc/2023/Conference/Submission1/Reviewer_.*',
                            ]
                        }
                    },
                    'note': {
                        'readers': ['ICML.cc/2023/Conference/Program_Chairs', 'ICML.cc/2023/Conference/Submission1/Area_Chairs', 'ICML.cc/2023/Conference/Submission1/Reviewers'],
                        'writers': ['ICML.cc/2023/Conference'],
                        'signatures': ['${3/signatures}'],
                        'forum': submission.id,
                        'replyto': {
                            'param': {
                                'withForum': submission.id
                            }
                        },
                        'content': {
                            'message': {
                                'value': {
                                    'param': {
                                        'type': 'string',
                                        'maxLength': 50000,
                                        'markdown': True
                                    }
                                }
                            }
                        }
                    }
                }
            )
        )

        reviewer_client = openreview.api.OpenReviewClient(username='reviewer1@icml.cc', password='1234')

        anon_groups = reviewer_client.get_groups(prefix='ICML.cc/2023/Conference/Submission1/Reviewer_', signatory='~Reviewer_ICMLOne1')
        anon_group_id = anon_groups[0].id

        note_edit = reviewer_client.post_note_edit(
            invitation='ICML.cc/2023/Conference/Submission1/-/Chat',
            signatures=[anon_group_id],
            note=openreview.api.Note(
                replyto=submission.id,
                content={
                    'message': { 'value': 'Hi reviewers, I would like to discuss this paper with you.' }
                }
            )
        )

        pc_client=openreview.api.OpenReviewClient(username='pc@icml.cc', password='1234')

        note_edit = pc_client.post_note_edit(
            invitation='ICML.cc/2023/Conference/Submission1/-/Chat',
            signatures=['ICML.cc/2023/Conference/Program_Chairs'],
            note=openreview.api.Note(
                replyto=note_edit['note']['id'],
                content={
                    'message': { 'value': 'Please start the conversation.' }
                }
            )
        )
