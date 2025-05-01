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

class TestICMLConference():

    def test_create_conference(self, client, openreview_client, helpers):

        now = datetime.datetime.now()
        due_date = now + datetime.timedelta(days=3)

        # Post the request form note
        helpers.create_user('pc@icml.cc', 'Program', 'ICMLChair')
        pc_client = openreview.Client(username='pc@icml.cc', password=helpers.strong_password)


        sac_client = helpers.create_user('sac1@gmail.com', 'SAC', 'ICMLOne')

        helpers.create_user('sac2@icml.cc', 'SAC', 'ICMLTwo')
        helpers.create_user('ac1@icml.cc', 'AC', 'ICMLOne')
        helpers.create_user('ac2@icml.cc', 'AC', 'ICMLTwo')
        helpers.create_user('reviewer1@icml.cc', 'Reviewer', 'ICMLOne')
        helpers.create_user('reviewer2@icml.cc', 'Reviewer', 'ICMLTwo')
        helpers.create_user('reviewer3@icml.cc', 'Reviewer', 'ICMLThree')
        helpers.create_user('reviewer4@yahoo.com', 'Reviewer', 'ICMLFour')
        helpers.create_user('reviewer5@yahoo.com', 'Reviewer', 'ICMLFive')
        helpers.create_user('reviewer6@yahoo.com', 'Reviewer', 'ICMLSix')
        helpers.create_user('reviewerethics@yahoo.com', 'Reviewer', 'ICMLSeven')
        helpers.create_user('peter@mail.com', 'Peter', 'SomeLastName') # Author

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
                'publication_chairs':'No, our venue does not have Publication Chairs',
                'Area Chairs (Metareviewers)': 'Yes, our venue has Area Chairs',
                'senior_area_chairs': 'Yes, our venue has Senior Area Chairs',
                'senior_area_chairs_assignment': 'Area Chairs',
                'ethics_chairs_and_reviewers': 'Yes, our venue has Ethics Chairs and Reviewers',
                'Venue Start Date': '2023/07/01',
                'Submission Deadline': due_date.strftime('%Y/%m/%d'),
                'Location': 'Virtual',
                'submission_reviewer_assignment': 'Automatic',
                'Author and Reviewer Anonymity': 'Double-blind',
                'reviewer_identity': ['Program Chairs', 'Assigned Senior Area Chair', 'Assigned Area Chair', 'Assigned Reviewers'],
                'area_chair_identity': ['Program Chairs', 'Assigned Senior Area Chair', 'Assigned Area Chair', 'Assigned Reviewers'],
                'senior_area_chair_identity': ['Program Chairs', 'Assigned Senior Area Chair', 'Assigned Area Chair', 'Assigned Reviewers'],
                'Open Reviewing Policy': 'Submissions and reviews should both be private.',
                'submission_readers': 'Program chairs and paper authors only',
                'How did you hear about us?': 'ML conferences',
                'Expected Submissions': '100',
                'use_recruitment_template': 'Yes',
                'api_version': '2',
                'submission_license': ['CC BY 4.0'],
                'preferred_emails_groups': ['ICML.cc/2023/Conference/Senior_Area_Chairs', 'ICML.cc/2023/Conference/Area_Chairs', 'ICML.cc/2023/Conference/Reviewers', 'ICML.cc/2023/Conference/Authors'],
                'venue_organizer_agreement': [
                    'OpenReview natively supports a wide variety of reviewing workflow configurations. However, if we want significant reviewing process customizations or experiments, we will detail these requests to the OpenReview staff at least three months in advance.',
                    'We will ask authors and reviewers to create an OpenReview Profile at least two weeks in advance of the paper submission deadlines.',
                    'When assembling our group of reviewers and meta-reviewers, we will only include email addresses or OpenReview Profile IDs of people we know to have authored publications relevant to our venue.  (We will not solicit new reviewers using an open web form, because unfortunately some malicious actors sometimes try to create "fake ids" aiming to be assigned to review their own paper submissions.)',
                    'We acknowledge that, if our venue\'s reviewing workflow is non-standard, or if our venue is expecting more than a few hundred submissions for any one deadline, we should designate our own Workflow Chair, who will read the OpenReview documentation and manage our workflow configurations throughout the reviewing process.',
                    'We acknowledge that OpenReview staff work Monday-Friday during standard business hours US Eastern time, and we cannot expect support responses outside those times.  For this reason, we recommend setting submission and reviewing deadlines Monday through Thursday.',
                    'We will treat the OpenReview staff with kindness and consideration.'
                ]
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
        assert openreview_client.get_invitation('ICML.cc/2023/Conference/-/Preferred_Emails')

        sac_client.post_note_edit(
            invitation='openreview.net/Archive/-/Direct_Upload',
            signatures=['~SAC_ICMLOne1'],
            note = openreview.api.Note(
                pdate = openreview.tools.datetime_millis(datetime.datetime(2019, 4, 30)),
                content = {
                    'title': { 'value': 'Paper title 1' },
                    'abstract': { 'value': 'Paper abstract 1' },
                    'authors': { 'value': ['SAC ICML', 'Test2 Client'] },
                    'authorids': { 'value': ['~SAC_ICMLOne1', 'test2@mail.com'] },
                    'venue': { 'value': 'Arxiv' }
                },
                license = 'CC BY-SA 4.0'
        ))

        sac_client.post_note_edit(
            invitation='openreview.net/Archive/-/Direct_Upload',
            signatures=['~SAC_ICMLOne1'],
            note = openreview.api.Note(
                pdate = openreview.tools.datetime_millis(datetime.datetime(2019, 4, 30)),
                content = {
                    'title': { 'value': 'Paper title 2' },
                    'abstract': { 'value': 'Paper abstract 2' },
                    'authors': { 'value': ['SAC ICML', 'Test2 Client'] },
                    'authorids': { 'value': ['~SAC_ICMLOne1', 'test2@mail.com'] }
                },
                license = 'CC BY-SA 4.0'
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
                'publication_chairs':'No, our venue does not have Publication Chairs',
                'Venue Start Date': '2023/07/01',
                'Submission Deadline': due_date.strftime('%Y/%m/%d'),
                'Location': 'Virtual',
                'submission_reviewer_assignment': 'Automatic',
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
                    },
                    "subject_areas": {
                        "order": 19,
                        "description": "Enter subject areas.",
                        "value": {
                            "param": {
                                "type": "string[]",
                                "enum": [
                                    'Algorithms: Approximate Inference',
                                    'Algorithms: Belief Propagation',
                                    'Learning: Deep Learning',
                                    'Learning: General',
                                    'Learning: Nonparametric Bayes',
                                    'Methodology: Bayesian Methods',
                                    'Methodology: Calibration',
                                    'Principles: Causality',
                                    'Principles: Cognitive Models',
                                    'Representation: Constraints',
                                    'Representation: Dempster-Shafer',
                                    'Representation: Other'
                                ],
                                "input": "select"
                            }
                        }
                    }
                },
                'remove_submission_options': ['TL;DR'],
                'homepage_override': {
                    'location': 'Hawaii, USA',
                    'instructions': 'For author guidelines, please click [here](https://icml.cc/Conferences/2023/StyleAuthorInstructions)'
                },
                'source_submissions_query_mapping': {
                    'Official_Review': {
                        'position_paper_track': 'No'
                    },
                    'Position_Paper_Review': {
                        'position_paper_track': 'Yes'
                    }
                }
            }
        ))
        helpers.await_queue()

        submission_invitation = openreview_client.get_invitation('ICML.cc/2023/Conference/-/Submission')
        assert submission_invitation
        assert 'supplementary_material' in submission_invitation.edit['note']['content']
        assert 'financial_aid' in submission_invitation.edit['note']['content']
        assert 'subject_areas' in submission_invitation.edit['note']['content']
        assert 'TLDR' not in submission_invitation.edit['note']['content']

        domain = openreview_client.get_group('ICML.cc/2023/Conference')
        assert 'recommendation' == domain.content['meta_review_recommendation']['value']

    def test_add_pcs(self, client, openreview_client, helpers):

        pc_client=openreview.Client(username='pc@icml.cc', password=helpers.strong_password)
        request_form=pc_client.get_notes(invitation='openreview.net/Support/-/Request_Form')[0]

        now = datetime.datetime.now()
        due_date = now + datetime.timedelta(days=3)

        pc_client.post_note(openreview.Note(
            content={
                'title': 'Thirty-ninth International Conference on Machine Learning',
                'Official Venue Name': 'Thirty-ninth International Conference on Machine Learning',
                'Abbreviated Venue Name': 'ICML 2023',
                'Official Website URL': 'https://icml.cc',
                'program_chair_emails': ['pc@icml.cc', 'pc2@icml.cc'],
                'contact_email': 'pc@icml.cc',
                'publication_chairs':'No, our venue does not have Publication Chairs',
                'Venue Start Date': '2023/07/01',
                'Submission Start Date': now.strftime('%Y/%m/%d %H:%M'),
                'Submission Deadline': due_date.strftime('%Y/%m/%d %H:%M'),
                'Location': 'Virtual',
                'submission_reviewer_assignment': 'Automatic',
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

        submission_start = now.strftime('%b %d %Y %I:%M%p')
        submission_end = due_date.strftime('%b %d %Y %I:%M%p')
        group_content = openreview_client.get_group('ICML.cc/2023/Conference').content
        assert 'date' in group_content
        assert group_content['date']['value'] == f"Submission Start: {submission_start} UTC-0, Submission Deadline: {submission_end} UTC-0"

        pc_client.post_note(openreview.Note(
            content={
                'title': 'Thirty-ninth International Conference on Machine Learning',
                'Official Venue Name': 'Thirty-ninth International Conference on Machine Learning',
                'Abbreviated Venue Name': 'ICML 2023',
                'Official Website URL': 'https://icml.cc',
                'program_chair_emails': ['pc@icml.cc', 'pc3@icml.cc'],
                'contact_email': 'pc@icml.cc',
                'publication_chairs':'No, our venue does not have Publication Chairs',
                'Venue Start Date': '2023/07/01',
                'Submission Deadline': due_date.strftime('%Y/%m/%d'),
                'Location': 'Virtual',
                'submission_reviewer_assignment': 'Automatic',
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
                    },
                    "subject_areas": {
                        "order": 19,
                        "description": "Enter subject areas.",
                        "value": {
                            "param": {
                                "type": "string[]",
                                "enum": [
                                    'Algorithms: Approximate Inference',
                                    'Algorithms: Belief Propagation',
                                    'Learning: Deep Learning',
                                    'Learning: General',
                                    'Learning: Nonparametric Bayes',
                                    'Methodology: Bayesian Methods',
                                    'Methodology: Calibration',
                                    'Principles: Causality',
                                    'Principles: Cognitive Models',
                                    'Representation: Constraints',
                                    'Representation: Dempster-Shafer',
                                    'Representation: Other'
                                ],
                                "input": "select"
                            }
                        }
                    },
                    "position_paper_track": {
                        "order": 20,
                        "description": "Is this a submission to the position paper track? See Call for Position Papers (https://icml.cc/Conferences/2024/CallForPositionPapers).",
                        "value": {
                            "param": {
                                "type": "string",
                                "enum": [
                                    "Yes",
                                    "No"
                                ],
                                "input": "radio"
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

        pc_client=openreview.Client(username='pc@icml.cc', password=helpers.strong_password)
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
        group = openreview_client.get_group('ICML.cc/2023/Conference/Senior_Area_Chairs/Invited')
        assert len(group.members) == 2
        assert group.readers == ['ICML.cc/2023/Conference', 'ICML.cc/2023/Conference/Senior_Area_Chairs/Invited']

        messages = openreview_client.get_messages(subject = '[ICML 2023] Invitation to serve as Senior Area Chair')
        assert len(messages) == 2

        for message in messages:
            text = message['content']['text']

            invitation_url = re.search('https://.*\n', text).group(0).replace('https://openreview.net', 'http://localhost:3030').replace('&amp;', '&')[:-1]
            helpers.respond_invitation_fast(invitation_url, accept=True)

        helpers.await_queue_edit(openreview_client, invitation='ICML.cc/2023/Conference/Senior_Area_Chairs/-/Recruitment', count=2)

        messages = openreview_client.get_messages(subject='[ICML 2023] Senior Area Chair Invitation accepted')
        assert len(messages) == 2

        assert len(openreview_client.get_group('ICML.cc/2023/Conference/Senior_Area_Chairs').members) == 2
        assert len(openreview_client.get_group('ICML.cc/2023/Conference/Senior_Area_Chairs/Invited').members) == 2

    def test_ac_recruitment(self, client, openreview_client, helpers, request_page, selenium):

        pc_client=openreview.Client(username='pc@icml.cc', password=helpers.strong_password)
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
            helpers.respond_invitation_fast(invitation_url, accept=True)

        helpers.await_queue_edit(openreview_client, invitation='ICML.cc/2023/Conference/Area_Chairs/-/Recruitment', count=2)

        messages = openreview_client.get_messages(subject='[ICML 2023] Area Chair Invitation accepted')
        assert len(messages) == 2

        assert len(openreview_client.get_group('ICML.cc/2023/Conference/Area_Chairs').members) == 2
        assert len(openreview_client.get_group('ICML.cc/2023/Conference/Area_Chairs/Invited').members) == 2

    def test_reviewer_recruitment(self, client, openreview_client, helpers, request_page, selenium):

        pc_client=openreview.Client(username='pc@icml.cc', password=helpers.strong_password)
        request_form=pc_client.get_notes(invitation='openreview.net/Support/-/Request_Form')[0]

        reviewer_details = '''reviewer1@icml.cc, Reviewer ICMLOne
reviewer2@icml.cc, Reviewer ICMLTwo
reviewer3@icml.cc, Reviewer ICMLThree
reviewer4@yahoo.com, Reviewer ICMLFour
reviewer5@yahoo.com, Reviewer ICMLFive
reviewer6@yahoo.com, Reviewer ICMLSix
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
            helpers.respond_invitation_fast(invitation_url, accept=True, quota=1)

        helpers.await_queue_edit(openreview_client, invitation='ICML.cc/2023/Conference/Reviewers/-/Recruitment', count=6)

        messages = openreview_client.get_messages(subject='[ICML 2023] Reviewer Invitation accepted with reduced load')
        assert len(messages) == 6

        assert len(openreview_client.get_group('ICML.cc/2023/Conference/Reviewers').members) == 6
        assert len(openreview_client.get_group('ICML.cc/2023/Conference/Reviewers/Invited').members) == 6
        assert len(openreview_client.get_group('ICML.cc/2023/Conference/Reviewers/Declined').members) == 0

        messages = openreview_client.get_messages(to = 'reviewer6@yahoo.com', subject = '[ICML 2023] Invitation to serve as Reviewer')
        invitation_url = re.search('https://.*\n', messages[0]['content']['text']).group(0).replace('https://openreview.net', 'http://localhost:3030').replace('&amp;', '&')[:-1]
        helpers.respond_invitation_fast(invitation_url, accept=False)

        helpers.await_queue_edit(openreview_client, invitation='ICML.cc/2023/Conference/Reviewers/-/Recruitment', count=7)

        assert len(openreview_client.get_group('ICML.cc/2023/Conference/Reviewers').members) == 5
        assert len(openreview_client.get_group('ICML.cc/2023/Conference/Reviewers/Invited').members) == 6
        assert len(openreview_client.get_group('ICML.cc/2023/Conference/Reviewers/Declined').members) == 1

        reviewer_client = openreview.api.OpenReviewClient(username='reviewer1@icml.cc', password=helpers.strong_password)

        request_page(selenium, "http://localhost:3030/group?id=ICML.cc/2023/Conference/Reviewers", reviewer_client.token, wait_for_element='header')
        header = selenium.find_element(By.ID, 'header')
        assert 'You have agreed to review up to 1 submission' in header.text

        ## compute preferred emails
        openreview_client.post_invitation_edit(
            invitations='ICML.cc/2023/Conference/-/Edit',
            signatures=['~Super_User1'],
            invitation=openreview.api.Invitation(
                id='ICML.cc/2023/Conference/-/Preferred_Emails',
                cdate=openreview.tools.datetime_millis(datetime.datetime.now()) + 2000,
            )
        )

        helpers.await_queue_edit(openreview_client, edit_id='ICML.cc/2023/Conference/-/Preferred_Emails-0-0', count=2)

        ## Check preferred emails
        assert openreview_client.get_edges_count(invitation='ICML.cc/2023/Conference/-/Preferred_Emails') == 9

        edge = openreview_client.get_edges(head='~Reviewer_ICMLOne1', invitation='ICML.cc/2023/Conference/-/Preferred_Emails')[0]
        assert edge.tail == 'reviewer1@icml.cc'

        openreview_client.add_members_to_group('~Reviewer_ICMLOne1', 'reviewer1@gmail.com')
        openreview_client.add_members_to_group('reviewer1@gmail.com', '~Reviewer_ICMLOne1')

        profile = reviewer_client.get_profile()
        profile.content['emails'] = ['reviewer1@icml.cc', 'reviewer1@gmail.com']
        profile.content['preferredEmail'] = 'reviewer1@gmail.com'
        reviewer_client.post_profile(profile)

        edge = openreview_client.get_edges(head='~Reviewer_ICMLOne1', invitation='ICML.cc/2023/Conference/-/Preferred_Emails')[0]
        assert edge.tail == 'reviewer1@gmail.com'

        profile = reviewer_client.get_profile()
        profile.content['emails'] = ['reviewer1@icml.cc', 'reviewer1@gmail.com']
        profile.content['preferredEmail'] = 'reviewer1@icml.cc'
        reviewer_client.post_profile(profile)

        edge = openreview_client.get_edges(head='~Reviewer_ICMLOne1', invitation='ICML.cc/2023/Conference/-/Preferred_Emails')[0]
        assert edge.tail == 'reviewer1@icml.cc'        

    def test_registrations(self, client, openreview_client, helpers, test_client, request_page, selenium):

        pc_client=openreview.Client(username='pc@icml.cc', password=helpers.strong_password)
        request_form=pc_client.get_notes(invitation='openreview.net/Support/-/Request_Form')[0]
        venue = openreview.get_conference(client, request_form.id, support_user='openreview.net/Support')

        now = datetime.datetime.now()
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

        sac_client = openreview.api.OpenReviewClient(username = 'sac1@gmail.com', password=helpers.strong_password)

        request_page(selenium, 'http://localhost:3030/group?id=ICML.cc/2023/Conference/Senior_Area_Chairs', sac_client.token, by=By.CLASS_NAME, wait_for_element='tabs-container')
        tabs = selenium.find_element(By.CLASS_NAME, 'tabs-container')
        assert tabs
        assert tabs.find_element(By.LINK_TEXT, "Submission Status")
        assert tabs.find_element(By.LINK_TEXT, "Area Chair Status")
        assert tabs.find_element(By.LINK_TEXT, "Senior Area Chair Tasks")

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

        ac_client = openreview.api.OpenReviewClient(username = 'ac1@icml.cc', password=helpers.strong_password)

        invitation = ac_client.get_invitation('ICML.cc/2023/Conference/Area_Chairs/-/Registration')
        assert 'statement' in invitation.edit['note']['content']
        assert 'profile_confirmed' in invitation.edit['note']['content']
        assert 'expertise_confirmed' in invitation.edit['note']['content']

        reviewer_client = openreview.api.OpenReviewClient(username = 'reviewer1@icml.cc', password=helpers.strong_password)

        invitation = reviewer_client.get_invitation('ICML.cc/2023/Conference/Reviewers/-/Registration')
        assert 'statement' in invitation.edit['note']['content']
        assert 'profile_confirmed' not in invitation.edit['note']['content']
        assert 'expertise_confirmed' not in invitation.edit['note']['content']

    def test_submissions(self, client, openreview_client, helpers, test_client, request_page, selenium):

        test_client = openreview.api.OpenReviewClient(token=test_client.token)

        domains = ['umass.edu', 'amazon.com', 'fb.com', 'cs.umass.edu', 'google.com', 'mit.edu', 'deepmind.com', 'co.ux', 'apple.com', 'nvidia.com']
        subject_areas = ['Algorithms: Approximate Inference', 'Algorithms: Belief Propagation', 'Learning: Deep Learning', 'Learning: General', 'Learning: Nonparametric Bayes', 'Methodology: Bayesian Methods', 'Methodology: Calibration', 'Principles: Causality', 'Principles: Cognitive Models', 'Representation: Constraints', 'Representation: Dempster-Shafer', 'Representation: Other']
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
                    'financial_aid': { 'value': 'Yes' },
                    'subject_areas': { 'value': [subject_areas[random.randint(0, 11)], subject_areas[random.randint(0, 11)]] },
                    'position_paper_track': { 'value': 'Yes' if i % 2 == 0 else 'No' }
                }
            )
            if i == 1 or i == 101:
                note.content['authors']['value'].append('SAC ICMLOne')
                note.content['authorids']['value'].append('~SAC_ICMLOne1')

            test_client.post_note_edit(invitation='ICML.cc/2023/Conference/-/Submission',
                signatures=['~SomeFirstName_User1'],
                note=note)

        helpers.await_queue_edit(openreview_client, invitation='ICML.cc/2023/Conference/-/Submission', count=101)

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
                ddate = openreview.tools.datetime_millis(datetime.datetime.now()),
                content = {
                    'title': submission.content['title'],
                    'abstract': submission.content['abstract'],
                    'authorids': submission.content['authorids'],
                    'authors': submission.content['authors'],
                    'keywords': submission.content['keywords'],
                    'pdf': submission.content['pdf'],
                    'supplementary_material': submission.content['supplementary_material'],
                    'financial_aid': submission.content['financial_aid'],
                    'subject_areas': submission.content['subject_areas'],
                    'position_paper_track': submission.content['position_paper_track']
                }
            ))

        helpers.await_queue_edit(openreview_client, invitation='ICML.cc/2023/Conference/-/Submission', count=102)

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
                    'subject_areas': submission.content['subject_areas'],
                    'position_paper_track': submission.content['position_paper_track']
                }
            ))

        helpers.await_queue_edit(openreview_client, invitation='ICML.cc/2023/Conference/-/Submission', count=103)

        authors_group = openreview_client.get_group(id='ICML.cc/2023/Conference/Authors')

        for i in range(1,101):
            assert f'ICML.cc/2023/Conference/Submission{i}/Authors' in authors_group.members

        # assert authors see Submission button to edit their submissions
        request_page(selenium, 'http://localhost:3030/forum?id={}'.format(submission.id), test_client.token, by=By.CLASS_NAME, wait_for_element='forum-note')
        note_div = selenium.find_element(By.CLASS_NAME, 'forum-note')
        assert note_div
        button_row = note_div.find_element(By.CLASS_NAME, 'invitation-buttons')
        assert button_row
        buttons = button_row.find_elements(By.CLASS_NAME, 'btn-xs')
        assert buttons[0].text == 'Edit  '
        buttons[0].click()
        time.sleep(0.5)
        dropdown = button_row.find_element(By.CLASS_NAME, 'dropdown-menu')
        dropdown_values = dropdown.find_elements(By.TAG_NAME, "a")
        values = [value.text for value in dropdown_values]
        assert ['Submission'] == values

        # assert PCs can also see Submission button to edit submissions
        pc_client_v2=openreview.api.OpenReviewClient(username='pc@icml.cc', password=helpers.strong_password)
        request_page(selenium, 'http://localhost:3030/forum?id={}'.format(submission.id), pc_client_v2.token, by=By.CLASS_NAME, wait_for_element='forum-note')
        note_div = selenium.find_element(By.CLASS_NAME, 'forum-note')
        assert note_div
        button_row = note_div.find_element(By.CLASS_NAME, 'invitation-buttons')
        assert button_row
        buttons = button_row.find_elements(By.CLASS_NAME, 'btn-xs')
        assert buttons[0].text == 'Edit  '
        buttons[0].click()
        time.sleep(0.5)
        dropdown = button_row.find_element(By.CLASS_NAME, 'dropdown-menu')
        dropdown_values = dropdown.find_elements(By.TAG_NAME,"a")
        values = [value.text for value in dropdown_values]
        assert ['Submission', 'Post Submission', 'PC Revision'] == values

        ## compute preferred emails
        openreview_client.post_invitation_edit(
            invitations='ICML.cc/2023/Conference/-/Edit',
            signatures=['~Super_User1'],
            invitation=openreview.api.Invitation(
                id='ICML.cc/2023/Conference/-/Preferred_Emails',
                cdate=openreview.tools.datetime_millis(datetime.datetime.now()) + 2000,
            )
        )

        helpers.await_queue_edit(openreview_client, edit_id='ICML.cc/2023/Conference/-/Preferred_Emails-0-0', count=3)

        ## Check preferred emails
        assert openreview_client.get_edges_count(invitation='ICML.cc/2023/Conference/-/Preferred_Emails') == 11
        assert openreview_client.get_edges_count(invitation='ICML.cc/2023/Conference/-/Preferred_Emails', head='~SomeFirstName_User1') == 1      

    def test_post_submission(self, client, openreview_client, test_client, helpers, request_page, selenium):

        pc_client=openreview.Client(username='pc@icml.cc', password=helpers.strong_password)
        request_form=pc_client.get_notes(invitation='openreview.net/Support/-/Request_Form')[0]
        venue = openreview.get_conference(client, request_form.id, support_user='openreview.net/Support')

        ## close the submissions
        now = datetime.datetime.now()
        start_date = now - datetime.timedelta(days=10)
        due_date = now - datetime.timedelta(days=1)
        exp_date = now + datetime.timedelta(days=10)
        pc_client.post_note(openreview.Note(
            content={
                'title': 'Thirty-ninth International Conference on Machine Learning',
                'Official Venue Name': 'Thirty-ninth International Conference on Machine Learning',
                'Abbreviated Venue Name': 'ICML 2023',
                'Official Website URL': 'https://icml.cc',
                'program_chair_emails': ['pc@icml.cc', 'pc3@icml.cc'],
                'contact_email': 'pc@icml.cc',
                'publication_chairs':'No, our venue does not have Publication Chairs',
                'Venue Start Date': '2023/07/01',
                'Submission Start Date': start_date.strftime('%Y/%m/%d'),
                'Submission Deadline': due_date.strftime('%Y/%m/%d'),
                'Location': 'Virtual',
                'submission_reviewer_assignment': 'Automatic',
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
                    },
                    "subject_areas": {
                        "order": 19,
                        "description": "Enter subject areas.",
                        "value": {
                            "param": {
                                "type": "string[]",
                                "enum": [
                                    'Algorithms: Approximate Inference',
                                    'Algorithms: Belief Propagation',
                                    'Learning: Deep Learning',
                                    'Learning: General',
                                    'Learning: Nonparametric Bayes',
                                    'Methodology: Bayesian Methods',
                                    'Methodology: Calibration',
                                    'Principles: Causality',
                                    'Principles: Cognitive Models',
                                    'Representation: Constraints',
                                    'Representation: Dempster-Shafer',
                                    'Representation: Other'
                                ],
                                "input": "select"
                            }
                        }
                    },
                    "position_paper_track": {
                        "order": 20,
                        "description": "Is this a submission to the position paper track? See Call for Position Papers (https://icml.cc/Conferences/2024/CallForPositionPapers).",
                        "value": {
                            "param": {
                                "type": "string",
                                "enum": [
                                    "Yes",
                                    "No"
                                ],
                                "input": "radio"
                            }
                        }
                    }
                },
                'withdraw_submission_expiration': exp_date.strftime('%Y/%m/%d')
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


        submissions = openreview_client.get_notes(invitation='ICML.cc/2023/Conference/-/Submission', sort='number:asc')
        submission = submissions[0]

        # assert authors don't see Submission button anymore
        request_page(selenium, 'http://localhost:3030/forum?id={}'.format(submission.id), test_client.token, by=By.CLASS_NAME, wait_for_element='forum-note')
        note_div = selenium.find_element(By.CLASS_NAME, 'forum-note')
        assert note_div
        button_row = note_div.find_element(By.CLASS_NAME, 'invitation-buttons')
        assert button_row
        buttons = button_row.find_elements(By.CLASS_NAME, 'btn-xs')
        assert len(buttons) == 0

        pc_client_v2=openreview.api.OpenReviewClient(username='pc@icml.cc', password=helpers.strong_password)
        submission_invitation = pc_client_v2.get_invitation('ICML.cc/2023/Conference/-/Submission')
        assert submission_invitation.expdate < openreview.tools.datetime_millis(now)

        assert len(pc_client_v2.get_all_invitations(invitation='ICML.cc/2023/Conference/-/Withdrawal')) == 101
        withdrawal_inv = pc_client_v2.get_invitation('ICML.cc/2023/Conference/Submission1/-/Withdrawal')
        assert withdrawal_inv.expdate == openreview.tools.datetime_millis(exp_date.replace(hour=0, minute=0, second=0, microsecond=0))
        assert len(pc_client_v2.get_all_invitations(invitation='ICML.cc/2023/Conference/-/Desk_Rejection')) == 101
        desk_reject_inv = pc_client_v2.get_invitation('ICML.cc/2023/Conference/Submission1/-/Desk_Rejection')
        desk_reject_due_date = due_date + datetime.timedelta(days=90)
        assert desk_reject_inv.expdate == openreview.tools.datetime_millis(desk_reject_due_date.replace(hour=0, minute=0, second=0, microsecond=0))
        assert pc_client_v2.get_invitation('ICML.cc/2023/Conference/-/PC_Revision')

        ## make submissions visible to ACs only
        pc_client.post_note(openreview.Note(
            content= {
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

        helpers.await_queue_edit(openreview_client, 'ICML.cc/2023/Conference/-/Post_Submission-0-1', count=5)
        
        #Check that post submission email is sent to PCs
        messages = openreview_client.get_messages(to='pc@icml.cc', subject='Comment posted to your request for service: Thirty-ninth International Conference on Machine Learning')
        assert messages and len(messages) == 6
        assert 'Comment title: Post Submission Process Completed' in messages[-1]['content']['text']

        messages = openreview_client.get_messages(to='support@openreview.net', subject='Comment posted to a service request: Thirty-ninth International Conference on Machine Learning')
        assert len(messages) == 0        

        ac_client = openreview.api.OpenReviewClient(username = 'ac1@icml.cc', password=helpers.strong_password)
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
        assert not submissions[0].odate

        ## make submissions visible to the committee
        pc_client.post_note(openreview.Note(
            content= {
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

        helpers.await_queue_edit(openreview_client, 'ICML.cc/2023/Conference/-/Post_Submission-0-1', count=6)

        #Check that post submission email is sent to PCs
        messages = openreview_client.get_messages(to='pc@icml.cc', subject='Comment posted to your request for service: Thirty-ninth International Conference on Machine Learning')
        assert messages and len(messages) == 7
        assert 'Comment title: Post Submission Process Completed' in messages[-1]['content']['text']

        messages = openreview_client.get_messages(to='support@openreview.net', subject='Comment posted to a service request: Thirty-ninth International Conference on Machine Learning')
        assert len(messages) == 0

        submissions = venue.get_submissions(sort='number:asc')
        assert len(submissions) == 101

        #desk-reject paper
        pc_openreview_client = openreview.api.OpenReviewClient(username='pc@icml.cc', password=helpers.strong_password)

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
        assert note.invitations == ['ICML.cc/2023/Conference/-/Submission', 'ICML.cc/2023/Conference/-/Post_Submission', 'ICML.cc/2023/Conference/-/Desk_Rejected_Submission']

        assert desk_reject_note['readers'] == [
            "ICML.cc/2023/Conference/Program_Chairs",
            f"ICML.cc/2023/Conference/Submission{submission.number}/Senior_Area_Chairs",
            f"ICML.cc/2023/Conference/Submission{submission.number}/Area_Chairs",
            f"ICML.cc/2023/Conference/Submission{submission.number}/Reviewers",
            f"ICML.cc/2023/Conference/Submission{submission.number}/Authors"
        ]

        # reverse desk-rejection and withdraw paper
        desk_rejection_reversion_note = openreview_client.post_note_edit(invitation=f'ICML.cc/2023/Conference/Submission{submission.number}/-/Desk_Rejection_Reversion',
                                    signatures=['ICML.cc/2023/Conference/Program_Chairs'],
                                    note=openreview.api.Note(
                                        content={
                                            'revert_desk_rejection_confirmation': { 'value': 'We approve the reversion of desk-rejected submission.' },
                                        }
                                    ))

        helpers.await_queue_edit(openreview_client, edit_id=desk_rejection_reversion_note['id'])

        withdrawal_note = pc_openreview_client.post_note_edit(invitation=f'ICML.cc/2023/Conference/Submission{submission.number}/-/Withdrawal',
                                    signatures=[f'ICML.cc/2023/Conference/Submission{submission.number}/Authors'],
                                    note=openreview.api.Note(
                                        content={
                                            'withdrawal_confirmation': { 'value': 'I have read and agree with the venue\'s withdrawal policy on behalf of myself and my co-authors.' },
                                        }
                                    ))

        helpers.await_queue_edit(openreview_client, edit_id=withdrawal_note['id'])
        helpers.await_queue_edit(openreview_client, invitation='ICML.cc/2023/Conference/-/Withdrawn_Submission')

        withdrawn_submission = openreview_client.get_note(withdrawal_note['note']['forum'])
        assert withdrawn_submission.readers == ['ICML.cc/2023/Conference/Program_Chairs',
        'ICML.cc/2023/Conference/Submission101/Senior_Area_Chairs',
        'ICML.cc/2023/Conference/Submission101/Area_Chairs',
        'ICML.cc/2023/Conference/Submission101/Reviewers',
        'ICML.cc/2023/Conference/Submission101/Authors']

        assert withdrawal_note['readers'] == [
            "ICML.cc/2023/Conference/Program_Chairs",
            f"ICML.cc/2023/Conference/Submission{submission.number}/Senior_Area_Chairs",
            f"ICML.cc/2023/Conference/Submission{submission.number}/Area_Chairs",
            f"ICML.cc/2023/Conference/Submission{submission.number}/Reviewers",
            f"ICML.cc/2023/Conference/Submission{submission.number}/Authors"
        ]

        submissions = venue.get_submissions(sort='number:asc')
        assert len(submissions) == 100

        ac_client = openreview.api.OpenReviewClient(username = 'ac1@icml.cc', password=helpers.strong_password)
        submissions = ac_client.get_notes(invitation='ICML.cc/2023/Conference/-/Submission', sort='number:asc')
        assert len(submissions) == 100      #withdrawn papers are no longer visible to ACs because ACs have not been assigned yet
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
        edit_note = pc_client_v2.post_note_edit(invitation='ICML.cc/2023/Conference/-/PC_Revision',
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
                    'subject_areas': { 'value': submission.content['subject_areas']['value'] },
                    'position_paper_track': { 'value': submission.content['position_paper_track']['value'] }
                }
            ))

        helpers.await_queue_edit(openreview_client, edit_id=edit_note['id'])

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
        assert messages[0]['content']['replyTo'] == 'pc@icml.cc'
        assert messages[0]['content']['text'] == f'''Your new revision of the submission to ICML 2023 has been posted.

Title: Paper title 1 Version 2

Abstract: This is an abstract 1

To view your submission, click here: https://openreview.net/forum?id={submission.id}

Please note that responding to this email will direct your reply to pc@icml.cc.
'''

    def test_ac_bidding(self, client, openreview_client, helpers, test_client):

        pc_client=openreview.Client(username='pc@icml.cc', password=helpers.strong_password)
        pc_client_v2=openreview.api.OpenReviewClient(username='pc@icml.cc', password=helpers.strong_password)
        request_form=pc_client.get_notes(invitation='openreview.net/Support/-/Request_Form')[0]

        with pytest.raises(openreview.OpenReviewException, match=r'Please deploy SAC-AC assignments first. SAC-submission conflicts must be transferred to assigned ACs before computing AC-submission conflicts.'):
            client.post_note(openreview.Note(
                content={
                    'title': 'Paper Matching Setup',
                    'matching_group': 'ICML.cc/2023/Conference/Area_Chairs',
                    'compute_conflicts': 'NeurIPS',
                    'compute_conflicts_N_years': '3',
                    'compute_affinity_scores': 'No'

                },
                forum=request_form.id,
                replyto=request_form.id,
                invitation=f'openreview.net/Support/-/Request{request_form.number}/Paper_Matching_Setup',
                readers=['ICML.cc/2023/Conference/Program_Chairs', 'openreview.net/Support'],
                signatures=['~Program_ICMLChair1'],
                writers=[]
            ))

        openreview.tools.replace_members_with_ids(openreview_client, openreview_client.get_group('ICML.cc/2023/Conference/Senior_Area_Chairs'))

        with open(os.path.join(os.path.dirname(__file__), 'data/rev_scores_venue.csv'), 'w') as file_handle:
            writer = csv.writer(file_handle)
            for sac in openreview_client.get_group('ICML.cc/2023/Conference/Senior_Area_Chairs').members:
                for ac in openreview_client.get_group('ICML.cc/2023/Conference/Area_Chairs').members:
                    writer.writerow([ac, sac, round(random.random(), 2)])

        affinity_scores_url = client.put_attachment(os.path.join(os.path.dirname(__file__), 'data/rev_scores_venue.csv'), f'openreview.net/Support/-/Request{request_form.number}/Paper_Matching_Setup', 'upload_affinity_scores')

        ## setup matching to assign SAC to each AC
        with pytest.raises(openreview.OpenReviewException, match=r'Conflicts are not computed between SACs and ACs. Please select "No" for Compute Conflicts.'):
            client.post_note(openreview.Note(
                content={
                    'title': 'Paper Matching Setup',
                    'matching_group': 'ICML.cc/2023/Conference/Senior_Area_Chairs',
                    'compute_conflicts': 'Default',
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
                'compute_conflicts': 'NeurIPS',
                'compute_conflicts_N_years': '3',
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
        assert pc_client_v2.get_edges_count(invitation='ICML.cc/2023/Conference/Area_Chairs/-/Conflict') == 200 ## assigned SAC is an author of paper 1

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
                'compute_conflicts': 'NeurIPS',
                'compute_conflicts_N_years': '3',
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

        with pytest.raises(openreview.OpenReviewException, match=r'Paper matching is already being run for this group. Please wait for a status reply in the forum.'):
            client.post_note(openreview.Note(
                content={
                    'title': 'Paper Matching Setup',
                    'matching_group': 'ICML.cc/2023/Conference/Reviewers',
                    'compute_conflicts': 'NeurIPS',
                    'compute_conflicts_N_years': '3',
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

        # Only 1 reviewer matching note was posted
        matching_notes = client.get_all_notes(invitation=f'openreview.net/Support/-/Request{request_form.number}/Paper_Matching_Setup')
        rev_matching_notes = [note for note in matching_notes if note.content['matching_group'] == 'ICML.cc/2023/Conference/Reviewers']
        assert len(rev_matching_notes) == 1

        assert openreview_client.get_invitation('ICML.cc/2023/Conference/Reviewers/-/Conflict')

        assert openreview_client.get_edges_count(invitation='ICML.cc/2023/Conference/Reviewers/-/Conflict') == 0

        affinity_scores =  openreview_client.get_grouped_edges(invitation='ICML.cc/2023/Conference/Reviewers/-/Affinity_Score', groupby='id')
        assert affinity_scores
        assert len(affinity_scores) == 100 * 5 ## submissions * reviewers

        now = datetime.datetime.now()
        due_date = now + datetime.timedelta(days=3)

        ## Hide the pdf and supplementary material
        pc_client.post_note(openreview.Note(
            content= {
                'submission_readers': 'All program committee (all reviewers, all area chairs, all senior area chairs if applicable)',
                'hide_fields': ['financial_aid', 'pdf', 'supplementary_material']
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

        helpers.await_queue_edit(openreview_client, 'ICML.cc/2023/Conference/-/Post_Submission-0-1', count=7)

        #Check that post submission email is sent to PCs
        messages = openreview_client.get_messages(to='pc@icml.cc', subject='Comment posted to your request for service: Thirty-ninth International Conference on Machine Learning')
        assert messages and len(messages) == 8
        assert 'Comment title: Post Submission Process Completed' in messages[-1]['content']['text']

        messages = openreview_client.get_messages(to='support@openreview.net', subject='Comment posted to a service request: Thirty-ninth International Conference on Machine Learning')
        assert len(messages) == 0        

        ac_client = openreview.api.OpenReviewClient(username = 'ac1@icml.cc', password=helpers.strong_password)
        submissions = ac_client.get_notes(invitation='ICML.cc/2023/Conference/-/Submission', sort='number:asc')
        assert len(submissions) == 100
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
        assert 'pdf' not in submissions[0].content
        assert 'supplementary_material' not in submissions[0].content

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

        invitation = openreview_client.get_invitation('ICML.cc/2023/Conference/Area_Chairs/-/Bid')
        assert invitation.edit['tail']['param']['options']['group'] == 'ICML.cc/2023/Conference/Area_Chairs'
        invitation = openreview_client.get_invitation('ICML.cc/2023/Conference/Reviewers/-/Bid')
        assert invitation.edit['tail']['param']['options']['group'] == 'ICML.cc/2023/Conference/Reviewers'

        # check email is not sent to support
        messages = openreview_client.get_messages(to='support@openreview.net', subject='Comment posted to a service request: Thirty-ninth International Conference on Machine Learning')
        assert len(messages) == 0        

        # check email is sent to pcs
        messages = openreview_client.get_messages(to='pc@icml.cc', subject='Comment posted to your request for service: Thirty-ninth International Conference on Machine Learning')
        assert messages and len(messages) == 9
        assert 'Comment title: Bid Stage Process Completed' in messages[-1]['content']['text']

        ## Hide the pdf and supplementary material
        pc_client.post_note(openreview.Note(
            content= {
                'submission_readers': 'All program committee (all reviewers, all area chairs, all senior area chairs if applicable)',
                'hide_fields': ['financial_aid', 'pdf', 'supplementary_material']
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
        
        #Check that post submission email is sent to PCs
        messages = openreview_client.get_messages(to='pc@icml.cc', subject='Comment posted to your request for service: Thirty-ninth International Conference on Machine Learning')
        assert messages and len(messages) == 10
        assert 'Comment title: Post Submission Process Completed' in messages[-1]['content']['text']

        messages = openreview_client.get_messages(to='support@openreview.net', subject='Comment posted to a service request: Thirty-ninth International Conference on Machine Learning')
        assert len(messages) == 0        

        ac_client = openreview.api.OpenReviewClient(username = 'ac1@icml.cc', password=helpers.strong_password)
        submissions = ac_client.get_notes(invitation='ICML.cc/2023/Conference/-/Submission', sort='number:asc')
        assert len(submissions) == 100
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
        assert 'pdf' not in submissions[0].content
        assert 'supplementary_material' not in submissions[0].content

    def test_assignment(self, client, openreview_client, helpers, request_page, selenium):

        pc_client=openreview.Client(username='pc@icml.cc', password=helpers.strong_password)
        pc_client_v2=openreview.api.OpenReviewClient(username='pc@icml.cc', password=helpers.strong_password)
        request_form=pc_client.get_notes(invitation='openreview.net/Support/-/Request_Form')[0]
        venue = openreview.helpers.get_conference(pc_client, request_form.id, setup=False)
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
                    label = 'reviewer-matching',
                    readers = ["ICML.cc/2023/Conference", f"ICML.cc/2023/Conference/Submission{submissions[i].number}/Senior_Area_Chairs", f"ICML.cc/2023/Conference/Submission{submissions[i].number}/Area_Chairs", r],
                    nonreaders = [f"ICML.cc/2023/Conference/Submission{submissions[i].number}/Authors"],
                    writers = ["ICML.cc/2023/Conference", f"ICML.cc/2023/Conference/Submission{submissions[i].number}/Senior_Area_Chairs", f"ICML.cc/2023/Conference/Submission{submissions[i].number}/Area_Chairs"]
                ))

            openreview_client.post_edge(openreview.api.Edge(
                invitation = 'ICML.cc/2023/Conference/Area_Chairs/-/Proposed_Assignment',
                head = submissions[i].id,
                tail = '~AC_ICMLOne1',
                signatures = ['ICML.cc/2023/Conference/Program_Chairs'],
                weight = 1,
                label = 'ac-matching'
            ))

        # post duplicate AC Proposed_Assignment edge
        openreview_client.post_edge(openreview.api.Edge(
                invitation = 'ICML.cc/2023/Conference/Area_Chairs/-/Proposed_Assignment',
                head = submissions[0].id,
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
                    label = 'reviewer-matching',
                    readers = ["ICML.cc/2023/Conference", f"ICML.cc/2023/Conference/Submission{submissions[i].number}/Senior_Area_Chairs", f"ICML.cc/2023/Conference/Submission{submissions[i].number}/Area_Chairs", r],
                    nonreaders = [f"ICML.cc/2023/Conference/Submission{submissions[i].number}/Authors"],
                    writers = ["ICML.cc/2023/Conference", f"ICML.cc/2023/Conference/Submission{submissions[i].number}/Senior_Area_Chairs", f"ICML.cc/2023/Conference/Submission{submissions[i].number}/Area_Chairs"]
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
                    label = 'reviewer-matching',
                    readers = ["ICML.cc/2023/Conference", f"ICML.cc/2023/Conference/Submission{submissions[i].number}/Senior_Area_Chairs", f"ICML.cc/2023/Conference/Submission{submissions[i].number}/Area_Chairs", r],
                    nonreaders = [f"ICML.cc/2023/Conference/Submission{submissions[i].number}/Authors"],
                    writers = ["ICML.cc/2023/Conference", f"ICML.cc/2023/Conference/Submission{submissions[i].number}/Senior_Area_Chairs", f"ICML.cc/2023/Conference/Submission{submissions[i].number}/Area_Chairs"]
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
                    label = 'reviewer-matching',
                    readers = ["ICML.cc/2023/Conference", f"ICML.cc/2023/Conference/Submission{submissions[i].number}/Senior_Area_Chairs", f"ICML.cc/2023/Conference/Submission{submissions[i].number}/Area_Chairs", r],
                    nonreaders = [f"ICML.cc/2023/Conference/Submission{submissions[i].number}/Authors"],
                    writers = ["ICML.cc/2023/Conference", f"ICML.cc/2023/Conference/Submission{submissions[i].number}/Senior_Area_Chairs", f"ICML.cc/2023/Conference/Submission{submissions[i].number}/Area_Chairs"]
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
                    label = 'reviewer-matching',
                    readers = ["ICML.cc/2023/Conference", f"ICML.cc/2023/Conference/Submission{submissions[i].number}/Senior_Area_Chairs", f"ICML.cc/2023/Conference/Submission{submissions[i].number}/Area_Chairs", r],
                    nonreaders = [f"ICML.cc/2023/Conference/Submission{submissions[i].number}/Authors"],
                    writers = ["ICML.cc/2023/Conference", f"ICML.cc/2023/Conference/Submission{submissions[i].number}/Senior_Area_Chairs", f"ICML.cc/2023/Conference/Submission{submissions[i].number}/Area_Chairs"]
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

        assignment_edges = pc_client_v2.get_edges(invitation='ICML.cc/2023/Conference/Area_Chairs/-/Assignment', head=submissions[0].id, tail='~AC_ICMLOne1')
        assert assignment_edges and len(assignment_edges) == 2

        # remove duplicate edge and make sure assignment still remains
        assignment_edge = assignment_edges[0]
        assignment_edge.ddate = openreview.tools.datetime_millis(datetime.datetime.now())
        assignment_edge.cdate = None
        edge = pc_client_v2.post_edge(assignment_edge)

        helpers.await_queue_edit(openreview_client, edit_id=edge.id)

        ac_group = pc_client_v2.get_group('ICML.cc/2023/Conference/Submission1/Area_Chairs')
        assert ['~AC_ICMLOne1'] == ac_group.members

        sac_group = pc_client_v2.get_group('ICML.cc/2023/Conference/Submission1/Senior_Area_Chairs')
        assert ['~SAC_ICMLOne1'] == sac_group.members

        assignment_edges = pc_client_v2.get_edges(invitation='ICML.cc/2023/Conference/Area_Chairs/-/Assignment', head=submissions[0].id, tail='~AC_ICMLOne1')
        assert assignment_edges and len(assignment_edges) == 1

        ### Reviewers reassignment of proposed assignments

        now = datetime.datetime.now()
        due_date = now + datetime.timedelta(days=3)
        venue.setup_assignment_recruitment(committee_id='ICML.cc/2023/Conference/Reviewers', assignment_title='reviewer-matching', hash_seed='1234', due_date=due_date)

        venue_group = pc_client_v2.get_group('ICML.cc/2023/Conference')
        'NeurIPS' == venue_group.content['reviewers_conflict_policy']['value']

        pc_client_v2.post_group_edit(invitation='ICML.cc/2023/Conference/-/Edit',
            readers = ['ICML.cc/2023/Conference'],
            writers = ['ICML.cc/2023/Conference'],
            signatures = ['ICML.cc/2023/Conference'],
            group = openreview.api.Group(
                id = 'ICML.cc/2023/Conference',
                content = {
                    'enable_reviewers_reassignment': { 'value': True },
                    'reviewers_proposed_assignment_title': { 'value': 'reviewer-matching' }
                }
            )
        )

        ## increse quota for reviewer 4
        quota_edge = pc_client_v2.get_edges(invitation='ICML.cc/2023/Conference/Reviewers/-/Custom_Max_Papers', tail='~Reviewer_ICMLFour1')[0]
        quota_edge.weight = 15
        quota_edge.cdate = None
        pc_client_v2.post_edge(quota_edge)

        ac_client = openreview.api.OpenReviewClient(username='ac1@icml.cc', password=helpers.strong_password)
        request_page(selenium, "http://localhost:3030/group?id=ICML.cc/2023/Conference/Area_Chairs", ac_client.token, wait_for_element='header')
        header = selenium.find_element(By.ID, 'header')
        assert 'Reviewer Assignment Browser:' in header.text

        url = header.find_element(By.ID, 'edge_browser_url')
        assert url
        assert url.get_attribute('href') == 'http://localhost:3030/edges/browse?start=ICML.cc/2023/Conference/Area_Chairs/-/Assignment,tail:~AC_ICMLOne1&traverse=ICML.cc/2023/Conference/Reviewers/-/Proposed_Assignment,label:reviewer-matching&edit=ICML.cc/2023/Conference/Reviewers/-/Proposed_Assignment,label:reviewer-matching;ICML.cc/2023/Conference/Reviewers/-/Invite_Assignment&browse=ICML.cc/2023/Conference/Reviewers/-/Aggregate_Score,label:reviewer-matching;ICML.cc/2023/Conference/Reviewers/-/Affinity_Score;ICML.cc/2023/Conference/Reviewers/-/Bid;ICML.cc/2023/Conference/Reviewers/-/Custom_Max_Papers,head:ignore&hide=ICML.cc/2023/Conference/Reviewers/-/Conflict&maxColumns=2&preferredEmailInvitationId=ICML.cc/2023/Conference/-/Preferred_Emails&version=2&referrer=[Area%20Chairs%20Console](/group?id=ICML.cc/2023/Conference/Area_Chairs)'

        anon_group_id = ac_client.get_groups(prefix='ICML.cc/2023/Conference/Submission1/Area_Chair_', signatory='~AC_ICMLOne1')[0].id

        ## add a reviewer with max quota an get an error
        with pytest.raises(openreview.OpenReviewException, match=r'Max Papers allowed reached for Reviewer ICMLFive'):
            ac_client.post_edge(
                openreview.api.Edge(invitation='ICML.cc/2023/Conference/Reviewers/-/Proposed_Assignment',
                    signatures=[anon_group_id],
                    head=submissions[0].id,
                    tail='~Reviewer_ICMLFive1',
                    label='reviewer-matching',
                    weight=1
            ))        
        
        ## recruit external reviewer
        with pytest.raises(openreview.OpenReviewException, match=r'the user has a conflict'):
            ac_client.post_edge(
                openreview.api.Edge(invitation='ICML.cc/2023/Conference/Reviewers/-/Invite_Assignment',
                    signatures=[anon_group_id],
                    head=submissions[0].id,
                    tail='danielle@mail.com',
                    label='Invitation Sent',
                    weight=1
            ))

        with pytest.raises(openreview.OpenReviewException, match=r'the user is already assigned'):
            ac_client.post_edge(
                openreview.api.Edge(invitation='ICML.cc/2023/Conference/Reviewers/-/Invite_Assignment',
                    signatures=[anon_group_id],
                    head=submissions[0].id,
                    tail='~Reviewer_ICMLOne1',
                    label='Invitation Sent',
                    weight=1
            ))

        with pytest.raises(openreview.OpenReviewException, match=r'the user is an official reviewer'):
            ac_client.post_edge(
                openreview.api.Edge(invitation='ICML.cc/2023/Conference/Reviewers/-/Invite_Assignment',
                    signatures=[anon_group_id],
                    head=submissions[0].id,
                    tail='~Reviewer_ICMLFive1',
                    label='Invitation Sent',
                    weight=1
            ))

        edge = ac_client.post_edge(
            openreview.api.Edge(invitation='ICML.cc/2023/Conference/Reviewers/-/Invite_Assignment',
                signatures=[anon_group_id],
                head=submissions[0].id,
                tail='melisa@icml.cc',
                label='Invitation Sent',
                weight=1
        ))
        helpers.await_queue_edit(openreview_client, edge.id)

        helpers.create_user('javier@icml.cc', 'Javier', 'ICML')

        edge = ac_client.post_edge(
            openreview.api.Edge(invitation='ICML.cc/2023/Conference/Reviewers/-/Invite_Assignment',
                signatures=[anon_group_id],
                head=submissions[0].id,
                tail='~Javier_ICML1',
                label='Invitation Sent',
                weight=1
        ))
        helpers.await_queue_edit(openreview_client, edge.id)

        helpers.create_user('emilia@icml.cc', 'Emilia', 'ICML')
        edge = ac_client.post_edge(
            openreview.api.Edge(invitation='ICML.cc/2023/Conference/Reviewers/-/Invite_Assignment',
                signatures=[anon_group_id],
                head=submissions[0].id,
                tail='~Emilia_ICML1',
                label='Invitation Sent',
                weight=1
        ))
        helpers.await_queue_edit(openreview_client, edge.id)

        edge = ac_client.post_edge(
            openreview.api.Edge(invitation='ICML.cc/2023/Conference/Reviewers/-/Invite_Assignment',
                signatures=[anon_group_id],
                head=submissions[1].id,
                tail='~Emilia_ICML1',
                label='Invitation Sent',
                weight=1
        ))
        helpers.await_queue_edit(openreview_client, edge.id)

        # delete Invitation Sent edge for submission 1
        invite_edge=ac_client.get_edges(invitation='ICML.cc/2023/Conference/Reviewers/-/Invite_Assignment', head=submissions[0].id, tail='~Emilia_ICML1')[0]
        invite_edge.ddate = openreview.tools.datetime_millis(datetime.datetime.now())
        edge = ac_client.post_edge(invite_edge)

        time.sleep(5) ## wait until the process function runs

        group = openreview_client.get_group('ICML.cc/2023/Conference/External_Reviewers/Invited')
        assert '~Emilia_ICML1' in group.members

        messages = openreview_client.get_messages(to='emilia@icml.cc', subject='[ICML 2023] Invitation canceled to review paper titled "Paper title 1 Version 2"')
        assert messages and len(messages) == 1

        # check reviewer can still accept invitation after another invitation was cancelled
        messages = openreview_client.get_messages(to='emilia@icml.cc', subject='[ICML 2023] Invitation to review paper titled "Paper title 2"')
        assert messages and len(messages) == 1
        invitation_url = re.search('https://.*\n', messages[0]['content']['text']).group(0).replace('https://openreview.net', 'http://localhost:3030').replace('&amp;', '&')[:-1]
        helpers.respond_invitation_fast(invitation_url, accept=True)

        with pytest.raises(openreview.OpenReviewException, match=r'the user is already invited'):
            ac_client.post_edge(
                openreview.api.Edge(invitation='ICML.cc/2023/Conference/Reviewers/-/Invite_Assignment',
                    signatures=[anon_group_id],
                    head=submissions[0].id,
                    tail='javier@icml.cc',
                    label='Invitation Sent',
                    weight=1
            ))

        assert openreview_client.get_groups('ICML.cc/2023/Conference/Submission1/External_Reviewers/Invited', member='melisa@icml.cc')
        assert openreview_client.get_groups('ICML.cc/2023/Conference/External_Reviewers/Invited', member='melisa@icml.cc')

        assert not openreview_client.get_groups('ICML.cc/2023/Conference/Submission1/External_Reviewers', member='melisa@icml.cc')
        assert not openreview_client.get_groups('ICML.cc/2023/Conference/External_Reviewers', member='melisa@icml.cc')
        assert not openreview_client.get_groups('ICML.cc/2023/Conference/Reviewers', member='melisa@icml.cc')

        messages = openreview_client.get_messages(to='melisa@icml.cc', subject='[ICML 2023] Invitation to review paper titled "Paper title 1 Version 2"')
        assert messages and len(messages) == 1
        invitation_url = re.search('https://.*\n', messages[0]['content']['text']).group(0).replace('https://openreview.net', 'http://localhost:3030').replace('&amp;', '&')[:-1]
        helpers.respond_invitation_fast(invitation_url, accept=True)

        helpers.await_queue_edit(openreview_client, invitation='ICML.cc/2023/Conference/Reviewers/-/Proposed_Assignment_Recruitment')

        ## External reviewer is set pending profile creation
        invite_edges=pc_client_v2.get_edges(invitation='ICML.cc/2023/Conference/Reviewers/-/Invite_Assignment', head=submissions[0].id, tail='melisa@icml.cc')
        assert len(invite_edges) == 1
        assert invite_edges[0].label == 'Pending Sign Up'

        assignment_edges=pc_client_v2.get_edges(invitation='ICML.cc/2023/Conference/Reviewers/-/Proposed_Assignment', label='reviewer-matching', head=submissions[0].id)
        assert len(assignment_edges) == 3

        messages = openreview_client.get_messages(to='melisa@icml.cc', subject='[ICML 2023] Reviewer Invitation accepted for paper 1, assignment pending')
        assert messages and len(messages) == 1
        assert messages[0]['content']['text'] == '''Hi melisa@icml.cc,
Thank you for accepting the invitation to review the paper number: 1, title: Paper title 1 Version 2.

Please signup in OpenReview using the email address melisa@icml.cc and complete your profile.
Confirmation of the assignment is pending until your profile is active and no conflicts of interest are detected.

If you would like to change your decision, please follow the link in the previous invitation email and click on the "Decline" button.

OpenReview Team

Please note that responding to this email will direct your reply to pc@icml.cc.
'''

        messages = openreview_client.get_messages(to='ac1@icml.cc', subject='[ICML 2023] Reviewer melisa@icml.cc accepted to review paper 1, assignment pending')
        assert messages and len(messages) == 1
        assert messages[0]['content']['text'] == '''Hi AC ICMLOne,
The Reviewer melisa@icml.cc that you invited to review paper 1 has accepted the invitation.

Confirmation of the assignment is pending until the invited reviewer creates a profile in OpenReview and no conflicts of interest are detected.

OpenReview Team

Please note that responding to this email will direct your reply to pc@icml.cc.
'''

        # try to remove Invite_Assignment edge with label == 'Pending Sign Up'
        with pytest.raises(openreview.OpenReviewException, match=r'Cannot cancel the invitation since it has status: "Pending Sign Up"'):
            invite_edge=pc_client_v2.get_edges(invitation='ICML.cc/2023/Conference/Reviewers/-/Invite_Assignment', head=submissions[0].id, tail='melisa@icml.cc')[0]
            invite_edge.ddate = openreview.tools.datetime_millis(datetime.datetime.now())
            pc_client_v2.post_edge(invite_edge)

        ## Run Job
        openreview.venue.Venue.check_new_profiles(openreview_client)

        ## External reviewer creates a profile and accepts the invitation again
        helpers.create_user('melisa@icml.cc', 'Melisa', 'ICML')

        ## Run Job
        openreview.venue.Venue.check_new_profiles(openreview_client)

        invite_edges=pc_client.get_edges(invitation='ICML.cc/2023/Conference/Reviewers/-/Invite_Assignment', head=submissions[0].id, tail='melisa@icml.cc')
        assert len(invite_edges) == 0

        invite_edges=pc_client.get_edges(invitation='ICML.cc/2023/Conference/Reviewers/-/Invite_Assignment', head=submissions[0].id, tail='~Melisa_ICML1')
        assert len(invite_edges) == 1
        assert invite_edges[0].label == 'Accepted'

        assignment_edges=pc_client.get_edges(invitation='ICML.cc/2023/Conference/Reviewers/-/Proposed_Assignment', label='reviewer-matching', head=submissions[0].id)
        assert len(assignment_edges) == 4

        messages = openreview_client.get_messages(to='melisa@icml.cc', subject='[ICML 2023] Reviewer Assignment confirmed for paper 1')
        assert messages and len(messages) == 1
        assert messages[0]['content']['text'] == '''Hi Melisa ICML,
Thank you for accepting the invitation to review the paper number: 1, title: Paper title 1 Version 2.

The ICML 2023 program chairs will be contacting you with more information regarding next steps soon. In the meantime, please add noreply@openreview.net to your email contacts to ensure that you receive all communications.

If you would like to change your decision, please click the Decline link in the previous invitation email.

OpenReview Team

Please note that responding to this email will direct your reply to pc@icml.cc.
'''

        messages = openreview_client.get_messages(to='ac1@icml.cc', subject='[ICML 2023] Reviewer Melisa ICML signed up and is assigned to paper 1')
        assert messages and len(messages) == 1
        assert messages[0]['content']['text'] == '''Hi AC ICMLOne,
The Reviewer Melisa ICML that you invited to review paper 1 has accepted the invitation, signed up and is now assigned to the paper 1.

OpenReview Team

Please note that responding to this email will direct your reply to pc@icml.cc.
'''

        assert openreview_client.get_groups('ICML.cc/2023/Conference/Submission1/External_Reviewers', member='melisa@icml.cc')
        assert openreview_client.get_groups('ICML.cc/2023/Conference/External_Reviewers', member='melisa@icml.cc')
        assert not openreview_client.get_groups('ICML.cc/2023/Conference/Reviewers', member='melisa@icml.cc')

        venue.set_assignments(assignment_title='reviewer-matching', committee_id='ICML.cc/2023/Conference/Reviewers', enable_reviewer_reassignment=True)

        # Check that deploying assignments removes reviewers_proposed_assignment_title
        venue_group = pc_client_v2.get_group('ICML.cc/2023/Conference')
        assert 'reviewers_proposed_assignment_title' not in venue_group.content

        proposed_recruitment_inv = openreview_client.get_invitation('ICML.cc/2023/Conference/Reviewers/-/Proposed_Assignment_Recruitment')
        assert proposed_recruitment_inv.expdate and proposed_recruitment_inv.expdate < openreview.tools.datetime_millis(datetime.datetime.now())

        invite_edges=pc_client.get_edges(invitation='ICML.cc/2023/Conference/Reviewers/-/Invite_Assignment', head=submissions[0].id, tail='~Javier_ICML1')
        assert len(invite_edges) == 1

        messages = openreview_client.get_messages(to='javier@icml.cc', subject='[ICML 2023] Invitation to review paper titled "Paper title 1 Version 2"')
        assert messages and len(messages) == 1
        invitation_url = re.search('https://.*\n', messages[0]['content']['text']).group(0).replace('https://openreview.net', 'http://localhost:3030').replace('&amp;', '&')[:-1]
        with pytest.raises(NoSuchElementException):
            helpers.respond_invitation(selenium, request_page, invitation_url, accept=True)

        reviewers_group = pc_client_v2.get_group('ICML.cc/2023/Conference/Submission1/Reviewers')
        assert len(reviewers_group.members) == 4
        assert '~Reviewer_ICMLOne1' in reviewers_group.members
        assert '~Reviewer_ICMLTwo1' in reviewers_group.members
        assert '~Reviewer_ICMLThree1' in reviewers_group.members
        assert '~Melisa_ICML1' in reviewers_group.members

        reviewers_group = pc_client_v2.get_group('ICML.cc/2023/Conference/Submission100/Reviewers')
        assert len(reviewers_group.members) == 3
        assert '~Reviewer_ICMLOne1' in reviewers_group.members
        assert '~Reviewer_ICMLTwo1' in reviewers_group.members
        assert '~Reviewer_ICMLFive1' in reviewers_group.members

        assert pc_client_v2.get_invitation('ICML.cc/2023/Conference/Reviewers/-/Invite_Assignment')

        ## Change assigned SAC
        assignment_edge = pc_client_v2.get_edges(invitation='ICML.cc/2023/Conference/Senior_Area_Chairs/-/Assignment', head='~AC_ICMLTwo1', tail='~SAC_ICMLOne1')[0]
        assignment_edge.ddate = openreview.tools.datetime_millis(datetime.datetime.now())
        assignment_edge.cdate = None
        pc_client_v2.post_edge(assignment_edge)

        helpers.await_queue_edit(openreview_client, edit_id=assignment_edge.id, count=1)

        sac_group = pc_client_v2.get_group('ICML.cc/2023/Conference/Submission1/Senior_Area_Chairs')
        assert ['~SAC_ICMLOne1'] == sac_group.members

        sac_group = pc_client_v2.get_group('ICML.cc/2023/Conference/Submission100/Senior_Area_Chairs')
        assert [] == sac_group.members

        assignment_edge = openreview_client.post_edge(openreview.api.Edge(
            invitation = 'ICML.cc/2023/Conference/Senior_Area_Chairs/-/Assignment',
            head = '~AC_ICMLTwo1',
            tail = '~SAC_ICMLTwo1',
            signatures = ['ICML.cc/2023/Conference/Program_Chairs'],
            weight = 1
        ))

        helpers.await_queue_edit(openreview_client, edit_id=assignment_edge.id)

        sac_group = pc_client_v2.get_group('ICML.cc/2023/Conference/Submission1/Senior_Area_Chairs')
        assert ['~SAC_ICMLOne1'] == sac_group.members

        sac_group = pc_client_v2.get_group('ICML.cc/2023/Conference/Submission100/Senior_Area_Chairs')
        assert ['~SAC_ICMLTwo1'] == sac_group.members

        ## Change assigned AC, add new AC first and then remove old AC
        edge = pc_client_v2.post_edge(openreview.api.Edge(
            invitation = 'ICML.cc/2023/Conference/Area_Chairs/-/Assignment',
            head = submissions[0].id,
            tail = '~AC_ICMLTwo1',
            signatures = ['ICML.cc/2023/Conference/Program_Chairs'],
            weight = 1
        ))

        helpers.await_queue_edit(openreview_client, edit_id=edge.id)

        ac_group = pc_client_v2.get_group('ICML.cc/2023/Conference/Submission1/Area_Chairs')
        assert ['~AC_ICMLOne1', '~AC_ICMLTwo1'] == ac_group.members

        sac_group = pc_client_v2.get_group('ICML.cc/2023/Conference/Submission1/Senior_Area_Chairs')
        assert ['~SAC_ICMLOne1','~SAC_ICMLTwo1'] == sac_group.members

        assignment_edge = pc_client_v2.get_edges(invitation='ICML.cc/2023/Conference/Area_Chairs/-/Assignment', head=submissions[0].id, tail='~AC_ICMLOne1')[0]
        assignment_edge.ddate = openreview.tools.datetime_millis(datetime.datetime.now())
        assignment_edge.cdate = None
        edge = pc_client_v2.post_edge(assignment_edge)

        helpers.await_queue_edit(openreview_client, edit_id=edge.id)

        ac_group = pc_client_v2.get_group('ICML.cc/2023/Conference/Submission1/Area_Chairs')
        assert ['~AC_ICMLTwo1'] == ac_group.members

        sac_group = pc_client_v2.get_group('ICML.cc/2023/Conference/Submission1/Senior_Area_Chairs')
        assert ['~SAC_ICMLTwo1'] == sac_group.members

    def test_reviewer_reassignment(self, client, openreview_client, helpers, selenium, request_page):

        pc_client = openreview.api.OpenReviewClient(username='pc@icml.cc', password=helpers.strong_password)
        ac_client = openreview.api.OpenReviewClient(username='ac2@icml.cc', password=helpers.strong_password)

        pc_client.post_group_edit(invitation='ICML.cc/2023/Conference/-/Edit',
            readers = ['ICML.cc/2023/Conference'],
            writers = ['ICML.cc/2023/Conference'],
            signatures = ['ICML.cc/2023/Conference'],
            group = openreview.api.Group(
                id = 'ICML.cc/2023/Conference',
                content = {
                    'enable_reviewers_reassignment': { 'value': True }
                }
            )
        )

        request_page(selenium, "http://localhost:3030/group?id=ICML.cc/2023/Conference/Area_Chairs", ac_client.token, wait_for_element='header')
        header = selenium.find_element(By.ID, 'header')
        assert 'Reviewer Assignment Browser:' in header.text

        url = header.find_element(By.ID, 'edge_browser_url')
        assert url
        assert url.get_attribute('href') == 'http://localhost:3030/edges/browse?start=ICML.cc/2023/Conference/Area_Chairs/-/Assignment,tail:~AC_ICMLTwo1&traverse=ICML.cc/2023/Conference/Reviewers/-/Assignment&edit=ICML.cc/2023/Conference/Reviewers/-/Invite_Assignment&browse=ICML.cc/2023/Conference/Reviewers/-/Affinity_Score;ICML.cc/2023/Conference/Reviewers/-/Bid;ICML.cc/2023/Conference/Reviewers/-/Custom_Max_Papers,head:ignore&hide=ICML.cc/2023/Conference/Reviewers/-/Conflict&maxColumns=2&preferredEmailInvitationId=ICML.cc/2023/Conference/-/Preferred_Emails&version=2&referrer=[Area%20Chairs%20Console](/group?id=ICML.cc/2023/Conference/Area_Chairs)'

        submissions = ac_client.get_notes(invitation='ICML.cc/2023/Conference/-/Submission', sort='number:asc')
        anon_group_id = ac_client.get_groups(prefix='ICML.cc/2023/Conference/Submission1/Area_Chair_', signatory='~AC_ICMLTwo1')[0].id

        invite_assignment_edge = ac_client.post_edge(
            openreview.api.Edge(invitation='ICML.cc/2023/Conference/Reviewers/-/Invite_Assignment',
                signatures=[anon_group_id],
                head=submissions[0].id,
                tail='carlos@icml.cc',
                label='Invitation Sent',
                weight=1
        ))

        helpers.await_queue_edit(openreview_client, edit_id=invite_assignment_edge.id)

        assert openreview_client.get_groups('ICML.cc/2023/Conference/Emergency_Reviewers/Invited', member='carlos@icml.cc')

        assert not openreview_client.get_groups('ICML.cc/2023/Conference/Emergency_Reviewers', member='carlos@icml.cc')
        assert not openreview_client.get_groups('ICML.cc/2023/Conference/Reviewers', member='carlos@icml.cc')

        messages = openreview_client.get_messages(to='carlos@icml.cc', subject='[ICML 2023] Invitation to review paper titled "Paper title 1 Version 2"')
        assert messages and len(messages) == 1
        invitation_url = re.search('https://.*\n', messages[0]['content']['text']).group(0).replace('https://openreview.net', 'http://localhost:3030').replace('&amp;', '&')[:-1]
        helpers.respond_invitation_fast(invitation_url, accept=True)

        helpers.await_queue_edit(openreview_client, invitation='ICML.cc/2023/Conference/Reviewers/-/Assignment_Recruitment')

        ## External reviewer is set pending profile creation
        invite_edges=pc_client.get_edges(invitation='ICML.cc/2023/Conference/Reviewers/-/Invite_Assignment', head=submissions[0].id, tail='carlos@icml.cc')
        assert len(invite_edges) == 1
        assert invite_edges[0].label == 'Pending Sign Up'

        with pytest.raises(openreview.OpenReviewException, match=r'You have already accepted this invitation, but the assignment is pending until you create a profile and no conflict are detected.'):
            helpers.respond_invitation_fast(invitation_url, accept=True)

        assignment_edges=pc_client.get_edges(invitation='ICML.cc/2023/Conference/Reviewers/-/Assignment', head=submissions[0].id)
        assert len(assignment_edges) == 4

        messages = openreview_client.get_messages(to='carlos@icml.cc', subject='[ICML 2023] Reviewer Invitation accepted for paper 1, assignment pending')
        assert messages and len(messages) == 1
        assert messages[0]['content']['text'] == '''Hi carlos@icml.cc,
Thank you for accepting the invitation to review the paper number: 1, title: Paper title 1 Version 2.

Please signup in OpenReview using the email address carlos@icml.cc and complete your profile.
Confirmation of the assignment is pending until your profile is active and no conflicts of interest are detected.

If you would like to change your decision, please follow the link in the previous invitation email and click on the "Decline" button.

OpenReview Team

Please note that responding to this email will direct your reply to pc@icml.cc.
'''

        messages = openreview_client.get_messages(to='ac2@icml.cc', subject='[ICML 2023] Reviewer carlos@icml.cc accepted to review paper 1, assignment pending')
        assert messages and len(messages) == 1
        assert messages[0]['content']['text'] == '''Hi AC ICMLTwo,
The Reviewer carlos@icml.cc that you invited to review paper 1 has accepted the invitation.

Confirmation of the assignment is pending until the invited reviewer creates a profile in OpenReview and no conflicts of interest are detected.

OpenReview Team

Please note that responding to this email will direct your reply to pc@icml.cc.
'''

        ## External reviewer creates a profile and accepts the invitation again
        helpers.create_user('carlos@icml.cc', 'Carlos', 'ICML', institution='amazon.com')

        ## Run Job
        openreview.venue.Venue.check_new_profiles(openreview_client)

        invite_edges=pc_client.get_edges(invitation='ICML.cc/2023/Conference/Reviewers/-/Invite_Assignment', head=submissions[0].id, tail='carlos@icml.cc')
        assert len(invite_edges) == 0

        invite_edges=pc_client.get_edges(invitation='ICML.cc/2023/Conference/Reviewers/-/Invite_Assignment', head=submissions[0].id, tail='~Carlos_ICML1')
        assert len(invite_edges) == 1
        assert invite_edges[0].label == 'Conflict Detected'

        assignment_edges=pc_client.get_edges(invitation='ICML.cc/2023/Conference/Reviewers/-/Assignment', head=submissions[0].id)
        assert len(assignment_edges) == 4

        messages = openreview_client.get_messages(to='carlos@icml.cc', subject='[ICML 2023] Conflict detected for paper 1')
        assert messages and len(messages) == 1
        assert messages[0]['content']['text'] == '''Hi Carlos ICML,
You have accepted the invitation to review the paper number: 1, title: Paper title 1 Version 2.

A conflict was detected between you and the submission authors and the assignment can not be done.

If you have any questions, please contact us as info@openreview.net.

OpenReview Team

Please note that responding to this email will direct your reply to pc@icml.cc.
'''

        messages = openreview_client.get_messages(to='ac2@icml.cc', subject='[ICML 2023] Conflict detected between reviewer Carlos ICML and paper 1')
        assert messages and len(messages) == 1
        assert messages[0]['content']['text'] == '''Hi AC ICMLTwo,
A conflict was detected between Carlos ICML and the paper 1 and the assignment can not be done.

If you have any questions, please contact us as info@openreview.net.

OpenReview Team

Please note that responding to this email will direct your reply to pc@icml.cc.
'''

        assert not openreview_client.get_groups('ICML.cc/2023/Conference/Emergency_Reviewers', member='carlos@icml.cc')
        assert not openreview_client.get_groups('ICML.cc/2023/Conference/Reviewers', member='carlos@icml.cc')

        with pytest.raises(openreview.OpenReviewException, match=r'You have already accepted this invitation, but a conflict was detected and the assignment cannot be made.'):
            helpers.respond_invitation_fast(invitation_url, accept=True)

        invite_assignment_edge = ac_client.post_edge(
            openreview.api.Edge(invitation='ICML.cc/2023/Conference/Reviewers/-/Invite_Assignment',
                signatures=[anon_group_id],
                head=submissions[0].id,
                tail='celeste@icml.cc',
                label='Invitation Sent',
                weight=1
        ))

        helpers.await_queue_edit(openreview_client, edit_id=invite_assignment_edge.id)

        messages = openreview_client.get_messages(to='celeste@icml.cc', subject='[ICML 2023] Invitation to review paper titled "Paper title 1 Version 2"')
        assert messages and len(messages) == 1
        invitation_url = re.search('https://.*\n', messages[0]['content']['text']).group(0).replace('https://openreview.net', 'http://localhost:3030').replace('&amp;', '&')[:-1]
        helpers.respond_invitation_fast(invitation_url, accept=True)

        helpers.await_queue_edit(openreview_client, invitation='ICML.cc/2023/Conference/Reviewers/-/Assignment_Recruitment', count=2)

        ## External reviewer creates a profile and accepts the invitation again
        helpers.create_user('celeste@icml.cc', 'Celeste', 'ICML')

        ## Run Job
        openreview.venue.Venue.check_new_profiles(openreview_client)

        invite_edges=pc_client.get_edges(invitation='ICML.cc/2023/Conference/Reviewers/-/Invite_Assignment', head=submissions[0].id, tail='~Celeste_ICML1')
        assert len(invite_edges) == 1
        assert invite_edges[0].label == 'Accepted'

        assignment_edges=pc_client.get_edges(invitation='ICML.cc/2023/Conference/Reviewers/-/Assignment', head=submissions[0].id)
        assert len(assignment_edges) == 5

        messages = openreview_client.get_messages(to='celeste@icml.cc', subject='[ICML 2023] Reviewer Assignment confirmed for paper 1')
        assert messages and len(messages) == 1
        assert messages[0]['content']['text'] == '''Hi Celeste ICML,
Thank you for accepting the invitation to review the paper number: 1, title: Paper title 1 Version 2.

Please go to the ICML 2023 Reviewers Console and check your pending tasks: https://openreview.net/group?id=ICML.cc/2023/Conference/Reviewers

If you would like to change your decision, please click the Decline link in the previous invitation email.

OpenReview Team

Please note that responding to this email will direct your reply to pc@icml.cc.
'''

        messages = openreview_client.get_messages(to='ac2@icml.cc', subject='[ICML 2023] Reviewer Celeste ICML signed up and is assigned to paper 1')
        assert messages and len(messages) == 1
        assert messages[0]['content']['text'] == '''Hi AC ICMLTwo,
The Reviewer Celeste ICML that you invited to review paper 1 has accepted the invitation, signed up and is now assigned to the paper 1.

OpenReview Team

Please note that responding to this email will direct your reply to pc@icml.cc.
'''

        assignment_edge = pc_client.get_edges(invitation='ICML.cc/2023/Conference/Reviewers/-/Assignment', head=submissions[0].id, tail='~Celeste_ICML1')[0]
        helpers.await_queue_edit(openreview_client, edit_id=assignment_edge.id)

        messages = openreview_client.get_messages(to='celeste@icml.cc', subject='[ICML 2023] You have been assigned as a Reviewer for paper number 1')
        assert messages and len(messages) == 1
        assert messages[0]['content']['replyTo'] == 'pc@icml.cc'
        assert messages[0]['content']['text'] == f'''This is to inform you that you have been assigned as a Reviewer for paper number 1 for ICML 2023.

To review this new assignment, please login to OpenReview and go to https://openreview.net/forum?id={submissions[0].id}.

To check all of your assigned papers, go to https://openreview.net/group?id=ICML.cc/2023/Conference/Reviewers.

Thank you,

ICML 2023 Conference Program Chairs

Please note that responding to this email will direct your reply to pc@icml.cc.
'''

        assert openreview_client.get_groups('ICML.cc/2023/Conference/Emergency_Reviewers', member='celeste@icml.cc')
        assert openreview_client.get_groups('ICML.cc/2023/Conference/Reviewers', member='celeste@icml.cc')

        with pytest.raises(openreview.OpenReviewException, match=r'You have already accepted this invitation.'):
            helpers.respond_invitation_fast(invitation_url, accept=True)

        reviewers_group = pc_client.get_group('ICML.cc/2023/Conference/Submission1/Reviewers')
        assert len(reviewers_group.members) == 5
        assert '~Reviewer_ICMLOne1' in reviewers_group.members
        assert '~Reviewer_ICMLTwo1' in reviewers_group.members
        assert '~Reviewer_ICMLThree1' in reviewers_group.members
        assert '~Melisa_ICML1' in reviewers_group.members
        assert '~Celeste_ICML1' in reviewers_group.members

        ac_group = pc_client.get_group('ICML.cc/2023/Conference/Submission1/Area_Chairs')
        assert len(ac_group.members) == 1
        assert '~AC_ICMLTwo1' in ac_group.members

        invite_assignment_edge = ac_client.post_edge(
            openreview.api.Edge(invitation='ICML.cc/2023/Conference/Reviewers/-/Invite_Assignment',
                signatures=[anon_group_id],
                head=submissions[0].id,
                tail='~Reviewer_ICMLFour1',
                label='Invitation Sent',
                weight=1
        ))

        helpers.await_queue_edit(openreview_client, edit_id=invite_assignment_edge.id)

        messages = openreview_client.get_messages(to='reviewer4@yahoo.com', subject='[ICML 2023] Invitation to review paper titled "Paper title 1 Version 2"')
        assert messages and len(messages) == 1
        invitation_url = re.search('https://.*\n', messages[0]['content']['text']).group(0).replace('https://openreview.net', 'http://localhost:3030').replace('&amp;', '&')[:-1]
        helpers.respond_invitation_fast(invitation_url, accept=False)

        helpers.await_queue_edit(openreview_client, invitation='ICML.cc/2023/Conference/Reviewers/-/Assignment_Recruitment', count=3)

        with pytest.raises(openreview.OpenReviewException, match=r'You have already declined this invitation.'):
            helpers.respond_invitation_fast(invitation_url, accept=False)

        helpers.respond_invitation_fast(invitation_url, accept=True)

        helpers.await_queue_edit(openreview_client, invitation='ICML.cc/2023/Conference/Reviewers/-/Assignment_Recruitment', count=4)
        helpers.await_queue_edit(openreview_client, invitation='ICML.cc/2023/Conference/Reviewers/-/Assignment', count=2)

        # try to delete Invite Assignment edge after reviewer Accepted
        with pytest.raises(openreview.OpenReviewException, match=r'Cannot cancel the invitation since it has status: "Accepted"'):
            invite_edge=ac_client.get_edges(invitation='ICML.cc/2023/Conference/Reviewers/-/Invite_Assignment', head=submissions[0].id, tail='~Reviewer_ICMLFour1')[0]
            invite_edge.ddate = openreview.tools.datetime_millis(datetime.datetime.now())
            ac_client.post_edge(invite_edge)

        reviewers_group = pc_client.get_group('ICML.cc/2023/Conference/Submission1/Reviewers')
        assert len(reviewers_group.members) == 6
        assert '~Reviewer_ICMLOne1' in reviewers_group.members
        assert '~Reviewer_ICMLTwo1' in reviewers_group.members
        assert '~Reviewer_ICMLThree1' in reviewers_group.members
        assert '~Melisa_ICML1' in reviewers_group.members
        assert '~Celeste_ICML1' in reviewers_group.members
        assert '~Reviewer_ICMLFour1' in reviewers_group.members

        helpers.create_user('rachel@icml.cc', 'Rachel', 'ICML')

        invite_assignment_edge = ac_client.post_edge(
            openreview.api.Edge(invitation='ICML.cc/2023/Conference/Reviewers/-/Invite_Assignment',
                signatures=[anon_group_id],
                head=submissions[0].id,
                tail='~Rachel_ICML1',
                label='Invitation Sent',
                weight=1
        ))

        helpers.await_queue_edit(openreview_client, edit_id=invite_assignment_edge.id)

        messages = openreview_client.get_messages(to='rachel@icml.cc', subject='[ICML 2023] Invitation to review paper titled "Paper title 1 Version 2"')
        assert messages and len(messages) == 1
        invitation_url = re.search('https://.*\n', messages[0]['content']['text']).group(0).replace('https://openreview.net', 'http://localhost:3030').replace('&amp;', '&')[:-1]

        ## create another profile and merge
        helpers.create_user('rachel_bis@icml.cc', 'Rachel', 'ICML')

        client.rename_edges(new_id='~Rachel_ICML2', current_id='~Rachel_ICML1')
        client.merge_profiles(profileTo='~Rachel_ICML2', profileFrom='~Rachel_ICML1')

        helpers.respond_invitation_fast(invitation_url, accept=False, comment='I am too busy.')

        helpers.await_queue_edit(openreview_client, invitation='ICML.cc/2023/Conference/Reviewers/-/Assignment_Recruitment', count=5)

        messages = openreview_client.get_messages(to='rachel_bis@icml.cc', subject='[ICML 2023] Reviewer Invitation declined for paper 1')
        assert len(messages) == 1

        invite_edges=openreview_client.get_edges(invitation='ICML.cc/2023/Conference/Reviewers/-/Invite_Assignment', head=submissions[0].id, tail='~Rachel_ICML2')
        assert len(invite_edges) == 1
        assert invite_edges[0].label == 'Declined: I am too busy.'

        # accept invitation after declining with comment
        helpers.respond_invitation_fast(invitation_url, accept=True)

        helpers.await_queue_edit(openreview_client, invitation='ICML.cc/2023/Conference/Reviewers/-/Assignment_Recruitment', count=6)

        messages = openreview_client.get_messages(to='rachel_bis@icml.cc', subject='[ICML 2023] Reviewer Invitation accepted for paper 1')
        assert len(messages) == 1

        invite_edges=openreview_client.get_edges(invitation='ICML.cc/2023/Conference/Reviewers/-/Invite_Assignment', head=submissions[0].id, tail='~Rachel_ICML2')
        assert len(invite_edges) == 1
        assert invite_edges[0].label == 'Accepted'

        helpers.create_user('ana@icml.cc', 'Ana', 'ICML')

        invite_assignment_edge = ac_client.post_edge(
            openreview.api.Edge(invitation='ICML.cc/2023/Conference/Reviewers/-/Invite_Assignment',
                signatures=[anon_group_id],
                head=submissions[0].id,
                tail='~Ana_ICML1',
                label='Invitation Sent',
                weight=1
        ))

        helpers.await_queue_edit(openreview_client, edit_id=invite_assignment_edge.id)

        # delete invite assignment edge
        invite_assignment = pc_client.get_edges(invitation='ICML.cc/2023/Conference/Reviewers/-/Invite_Assignment', head=submissions[0].id, tail='~Ana_ICML1')[0]
        invite_assignment.ddate = openreview.tools.datetime_millis(datetime.datetime.now())
        invite_assignment.cdate = None
        pc_client.post_edge(invite_assignment)

        messages = openreview_client.get_messages(to='ana@icml.cc', subject='[ICML 2023] Invitation to review paper titled "Paper title 1 Version 2"')
        assert messages and len(messages) == 1
        invitation_url = re.search('https://.*\n', messages[0]['content']['text']).group(0).replace('https://openreview.net', 'http://localhost:3030').replace('&amp;', '&')[:-1]

        #try to accept invitation that has been deleted
        with pytest.raises(openreview.OpenReviewException, match=r'Invitation no longer exists. No action is required from your end.'):
            helpers.respond_invitation_fast(invitation_url, accept=True)

        #delete assignments before review stage and not get key error
        assignment = pc_client.get_edges(invitation='ICML.cc/2023/Conference/Reviewers/-/Assignment', head=submissions[10].id, tail='~Reviewer_ICMLThree1')[0]
        assignment.ddate = openreview.tools.datetime_millis(datetime.datetime.now())
        assignment.cdate = None
        edge = pc_client.post_edge(assignment)

        helpers.await_queue_edit(openreview_client, edit_id=edge.id)

        reviewers_group = pc_client.get_group('ICML.cc/2023/Conference/Submission11/Reviewers')
        assert len(reviewers_group.members) == 2
        assert '~Reviewer_ICMLThree1' not in reviewers_group.members

        assignment = pc_client.get_edges(invitation='ICML.cc/2023/Conference/Area_Chairs/-/Assignment', head=submissions[10].id, tail='~AC_ICMLOne1')[0]
        assignment.ddate = openreview.tools.datetime_millis(datetime.datetime.now())
        assignment.cdate = None
        edge = pc_client.post_edge(assignment)

        helpers.await_queue_edit(openreview_client, edit_id=edge.id)

        ac_group = pc_client.get_group('ICML.cc/2023/Conference/Submission11/Area_Chairs')
        assert [] == ac_group.members

        sac_group = pc_client.get_group('ICML.cc/2023/Conference/Submission11/Senior_Area_Chairs')
        assert [] == sac_group.members

        # Test referrer in SAC edge browser URL
        sac_client = openreview.api.OpenReviewClient(username = 'sac1@gmail.com', password=helpers.strong_password)
        request_page(selenium, "http://localhost:3030/group?id=ICML.cc/2023/Conference/Senior_Area_Chairs#area-chair-status", sac_client.token, wait_for_element='tabs-container')
        link =  selenium.find_element(By.CLASS_NAME, 'ac-sac-summary').find_element(By.LINK_TEXT, 'Modify Reviewers Assignments')
        assert link
        assert link.get_attribute("href") == 'http://localhost:3030/edges/browse?start=ICML.cc/2023/Conference/Area_Chairs/-/Assignment,tail:~AC_ICMLOne1&traverse=ICML.cc/2023/Conference/Reviewers/-/Assignment&edit=ICML.cc/2023/Conference/Reviewers/-/Invite_Assignment&browse=ICML.cc/2023/Conference/Reviewers/-/Affinity_Score;ICML.cc/2023/Conference/Reviewers/-/Bid;ICML.cc/2023/Conference/Reviewers/-/Custom_Max_Papers,head:ignore&hide=ICML.cc/2023/Conference/Reviewers/-/Conflict&maxColumns=2&preferredEmailInvitationId=ICML.cc/2023/Conference/-/Preferred_Emails&version=2&referrer=[Senior%20Area%20Chairs%20Console](/group?id=ICML.cc/2023/Conference/Senior_Area_Chairs)'

    def test_review_stage(self, client, openreview_client, helpers, selenium, request_page):

        pc_client=openreview.Client(username='pc@icml.cc', password=helpers.strong_password)
        request_form=pc_client.get_notes(invitation='openreview.net/Support/-/Request_Form')[0]

        ## Show the pdf and supplementary material to assigned reviewers
        pc_client.post_note(openreview.Note(
            content= {
                'submission_readers': 'Assigned program committee (assigned reviewers, assigned area chairs, assigned senior area chairs if applicable)',
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

        helpers.await_queue_edit(openreview_client, 'ICML.cc/2023/Conference/-/Post_Submission-0-1', count=8)

        #Check that post submission email is sent to PCs
        messages = openreview_client.get_messages(to='pc@icml.cc', subject='Comment posted to your request for service: Thirty-ninth International Conference on Machine Learning')
        assert messages and len(messages) == 11
        assert 'Comment title: Post Submission Process Completed' in messages[-1]['content']['text']

        messages = openreview_client.get_messages(to='support@openreview.net', subject='Comment posted to a service request: Thirty-ninth International Conference on Machine Learning')
        assert len(messages) == 0        

        ac_client = openreview.api.OpenReviewClient(username='ac1@icml.cc', password=helpers.strong_password)
        submissions = ac_client.get_notes(invitation='ICML.cc/2023/Conference/-/Submission', sort='number:asc')
        assert len(submissions) == 58
        assert ['ICML.cc/2023/Conference',
        'ICML.cc/2023/Conference/Submission2/Senior_Area_Chairs',
        'ICML.cc/2023/Conference/Submission2/Area_Chairs',
        'ICML.cc/2023/Conference/Submission2/Reviewers',
        'ICML.cc/2023/Conference/Submission2/Authors'] == submissions[0].readers
        assert ['ICML.cc/2023/Conference',
        'ICML.cc/2023/Conference/Submission2/Authors'] == submissions[0].writers
        assert ['ICML.cc/2023/Conference/Submission2/Authors'] == submissions[0].signatures
        assert 'authorids' not in submissions[0].content
        assert 'authors' not in submissions[0].content
        assert 'financial_aid'not in submissions[0].content
        assert 'pdf' in submissions[0].content
        assert 'supplementary_material' in submissions[0].content

        now = datetime.datetime.now()
        start_date = now - datetime.timedelta(days=2)
        due_date = now + datetime.timedelta(days=3)

        venue = openreview.helpers.get_conference(client, request_form.id, setup=False)
        venue.review_stage = openreview.stages.ReviewStage(
            start_date=start_date,
            due_date=due_date,
            additional_fields={
                "summarry": {
                    "order": 1,
                    "description": "Briefly summarize the paper and its contributions. This is not the place to critique the paper; the authors should generally agree with a well-written summary.",
                    "value": {
                        "param": {
                            "maxLength": 200000,
                            "type": "string",
                            "input": "textarea",
                            "markdown": True
                        }
                    }
                },
                "strengths_and_weaknesses": {
                    "order": 2,
                    "description": "Please provide a thorough assessment of the strengths and weaknesses of the paper, touching on each of the following dimensions: originality, quality, clarity, and significance. We encourage people to be broad in their definitions of originality and significance. For example, originality may arise from creative combinations of existing ideas, application to a new domain, or removing restrictive assumptions from prior theoretical results. You can incorporate Markdown and Latex into your review. See https://openreview.net/faq.",
                    "value": {
                        "param": {
                            "maxLength": 200000,
                            "type": "string",
                            "input": "textarea",
                            "markdown": True
                        }
                    }
                },
                "questions": {
                    "order": 3,
                    "description": "Please list up and carefully describe any questions and suggestions for the authors. Think of the things where a response from the author can change your opinion, clarify a confusion or address a limitation. This can be very important for a productive rebuttal and discussion phase with the authors.",
                    "value": {
                        "param": {
                            "maxLength": 200000,
                            "type": "string",
                            "input": "textarea",
                            "markdown": True
                        }
                    }
                },
                "limitations": {
                    "order": 4,
                    "description": "Have the authors adequately addressed the limitations and potential negative societal impact of their work? If not, please include constructive suggestions for improvement. Authors should be rewarded rather than punished for being up front about the limitations of their work and any potential negative societal impact.",
                    "value": {
                        "param": {
                            "maxLength": 200000,
                            "type": "string",
                            "input": "textarea",
                            "markdown": True
                        }
                    }
                },
                "ethics_flag": {
                    "order": 5,
                    "description": "If there are ethical issues with this paper, please flag the paper for an ethics review. For guidance on when this is appropriate, please review the ethics guidelines (https://icml.cc/Conferences/2023/PublicationEthics).",
                    "value": {
                        "param": {
                            "type": "string",
                            "enum": [
                                "Yes",
                                "No"
                            ],
                            "input": "radio"
                        }
                    }
                },
                "ethics_review_area": {
                    "order": 6,
                    "description": "If you flagged this paper for ethics review, what area of expertise would it be most useful for the ethics reviewer to have? Please click all that apply.",
                    "value": {
                        "param": {
                            "type": "string[]",
                            "enum": [
                                "Discrimination / Bias / Fairness Concerns",
                                "Inadequate Data and Algorithm Evaluation",
                                "Inappropriate Potential Applications & Impact  (e.g., human rights concerns)",
                                "Privacy and Security (e.g., consent)",
                                "Legal Compliance (e.g., GDPR, copyright, terms of use)",
                                "Research Integrity Issues (e.g., plagiarism)",
                                "Responsible Research Practice (e.g., IRB, documentation, research ethics)",
                                "I don't know"
                            ],
                            "input": "checkbox",
                            "optional": True,
                        }
                    }
                },
                "soundness": {
                    "order": 7,
                    "description": "Please assign the paper a numerical rating on the following scale to indicate the soundness of the technical claims, experimental and research methodology and on whether the central claims of the paper are adequately supported with evidence.",
                    "value": {
                        "param": {
                            "type": "string",
                            "enum": [
                                "4 excellent",
                                "3 good",
                                "2 fair",
                                "1 poor"
                            ],
                            "input": "radio"
                        }
                    }
                },
                "presentation": {
                    "order": 8,
                    "description": "Please assign the paper a numerical rating on the following scale to indicate the quality of the presentation. This should take into account the writing style and clarity, as well as contextualization relative to prior work.",
                    "value": {
                        "param": {
                            "type": "string",
                            "enum": [
                                "4 excellent",
                                "3 good",
                                "2 fair",
                                "1 poor"
                            ],
                            "input": "radio"
                        }
                    }
                },
                "contribution": {
                    "order": 9,
                    "description": "Please assign the paper a numerical rating on the following scale to indicate the quality of the overall contribution this paper makes to the research area being studied. Are the questions being asked important? Does the paper bring a significant originality of ideas and/or execution? Are the results valuable to share with the broader ICML community?",
                    "value": {
                        "param": {
                            "type": "string",
                            "enum": [
                                "4 excellent",
                                "3 good",
                                "2 fair",
                                "1 poor"
                            ],
                            "input": "radio"
                        }
                    }
                },
                "rating": {
                    "order": 10,
                    "description": "Please provide an \"overall score\" for this submission.",
                    "value": {
                        "param": {
                            "type": 'integer',
                            "enum": [
                                { 'value': 10, 'description': "10: Award quality: Technically flawless paper with groundbreaking impact, with exceptionally strong evaluation, reproducibility, and resources, and no unaddressed ethical considerations." },
                                { 'value': 9, 'description': "9: Very Strong Accept: Technically flawless paper with groundbreaking impact on at least one area of AI/ML and excellent impact on multiple areas of AI/ML, with flawless evaluation, resources, and reproducibility, and no unaddressed ethical considerations." },
                                { 'value': 8, 'description': "8: Strong Accept: Technically strong paper, with novel ideas, excellent impact on at least one area, or high-to-excellent impact on multiple areas, with excellent evaluation, resources, and reproducibility, and no unaddressed ethical considerations." },
                                { 'value': 7, 'description': "7: Accept: Technically solid paper, with high impact on at least one sub-area, or moderate-to-high impact on more than one areas, with good-to-excellent evaluation, resources, reproducibility, and no unaddressed ethical considerations." },
                                { 'value': 6, 'description': "6: Weak Accept: Technically solid, moderate-to-high impact paper, with no major concerns with respect to evaluation, resources, reproducibility, ethical considerations." },
                                { 'value': 5, 'description': "5: Borderline accept: Technically solid paper where reasons to accept outweigh reasons to reject, e.g., limited evaluation. Please use sparingly." },
                                { 'value': 4, 'description': "4: Borderline reject: Technically solid paper where reasons to reject, e.g., limited evaluation, outweigh reasons to accept, e.g., good evaluation. Please use sparingly." },
                                { 'value': 3, 'description': "3: Reject: For instance, a paper with technical flaws, weak evaluation, inadequate reproducibility and incompletely addressed ethical considerations." },
                                { 'value': 2, 'description': "2: Strong Reject: For instance, a paper with major technical flaws, and/or poor evaluation, limited impact, poor reproducibility and mostly unaddressed ethical considerations." },
                                { 'value': 1, 'description': "1: Very Strong Reject: For instance, a paper with trivial results or unaddressed ethical considerations" }
                            ],
                            "input": "radio"

                        }
                    }
                },
                "confidence": {
                    "order": 11,
                    "description": "Please provide a \"confidence score\" for your assessment of this submission to indicate how confident you are in your evaluation.",
                    "value": {
                        "param": {
                            "type": 'integer',
                            "enum": [
                                { 'value': 5, 'description': "5: You are absolutely certain about your assessment. You are very familiar with the related work and checked the math/other details carefully." },
                                { 'value': 4, 'description': "4: You are confident in your assessment, but not absolutely certain. It is unlikely, but not impossible, that you did not understand some parts of the submission or that you are unfamiliar with some pieces of related work." },
                                { 'value': 3, 'description': "3: You are fairly confident in your assessment. It is possible that you did not understand some parts of the submission or that you are unfamiliar with some pieces of related work. Math/other details were not carefully checked." },
                                { 'value': 2, 'description': "2: You are willing to defend your assessment, but it is quite likely that you did not understand the central parts of the submission or that you are unfamiliar with some pieces of related work. Math/other details were not carefully checked." },
                                { 'value': 1, 'description': "1: Your assessment is an educated guess. The submission is not in your area or the submission was difficult to understand. Math/other details were not carefully checked." }
                            ],
                            "input": "radio"
                        }
                    }
                },
                "code_of_conduct": {
                    "description": "While performing my duties as a reviewer (including writing reviews and participating in discussions), I have and will continue to abide by the ICML code of conduct (https://icml.cc/public/CodeOfConduct).",
                    "order": 12,
                    "value": {
                        "param": {
                            "type": "string",
                            "enum": ["Yes"],
                            "input": "checkbox"
                        }
                    }
                }
            },
            remove_fields=['title', 'review'],
            source_submissions_query={
                'position_paper_track': 'No'
            }
        )

        venue.create_review_stage()

        helpers.await_queue_edit(openreview_client, 'ICML.cc/2023/Conference/-/Official_Review-0-1', count=1)

        assert len(openreview_client.get_invitations(invitation='ICML.cc/2023/Conference/-/Official_Review')) == 50
        invitation = openreview_client.get_invitation('ICML.cc/2023/Conference/Submission1/-/Official_Review')
        assert 'summarry' in invitation.edit['note']['content']
        assert invitation.cdate < openreview.tools.datetime_millis(now)
        # duedate + 30 min
        exp_date = invitation.duedate + (30*60*1000)
        assert invitation.expdate == exp_date

        review_exp_date = due_date + datetime.timedelta(days=2)

        venue.review_stage = openreview.stages.ReviewStage(
            start_date=start_date, 
            due_date=due_date,
            exp_date=review_exp_date,
            additional_fields={
                "summary": {
                    "order": 1,
                    "description": "Briefly summarize the paper and its contributions. This is not the place to critique the paper; the authors should generally agree with a well-written summary.",
                    "value": {
                        "param": {
                            "maxLength": 200000,
                            "type": "string",
                            "input": "textarea",
                            "markdown": True
                        }
                    }
                },
                "strengths_and_weaknesses": {
                    "order": 2,
                    "description": "Please provide a thorough assessment of the strengths and weaknesses of the paper, touching on each of the following dimensions: originality, quality, clarity, and significance. We encourage people to be broad in their definitions of originality and significance. For example, originality may arise from creative combinations of existing ideas, application to a new domain, or removing restrictive assumptions from prior theoretical results. You can incorporate Markdown and Latex into your review. See https://openreview.net/faq.",
                    "value": {
                        "param": {
                            "maxLength": 200000,
                            "type": "string",
                            "input": "textarea",
                            "markdown": True
                        }
                    }
                },
                "questions": {
                    "order": 3,
                    "description": "Please list up and carefully describe any questions and suggestions for the authors. Think of the things where a response from the author can change your opinion, clarify a confusion or address a limitation. This can be very important for a productive rebuttal and discussion phase with the authors.",
                    "value": {
                        "param": {
                            "maxLength": 200000,
                            "type": "string",
                            "input": "textarea",
                            "markdown": True
                        }
                    }
                },
                "limitations": {
                    "order": 4,
                    "description": "Have the authors adequately addressed the limitations and potential negative societal impact of their work? If not, please include constructive suggestions for improvement. Authors should be rewarded rather than punished for being up front about the limitations of their work and any potential negative societal impact.",
                    "value": {
                        "param": {
                            "maxLength": 200000,
                            "type": "string",
                            "input": "textarea",
                            "markdown": True
                        }
                    }
                },
                "ethics_flag": {
                    "order": 5,
                    "description": "If there are ethical issues with this paper, please flag the paper for an ethics review. For guidance on when this is appropriate, please review the ethics guidelines (https://icml.cc/Conferences/2023/PublicationEthics).",
                    "value": {
                        "param": {
                            "type": "string",
                            "enum": [
                                "Yes",
                                "No"
                            ],
                            "input": "radio"
                        }
                    }
                },
                "ethics_review_area": {
                    "order": 6,
                    "description": "If you flagged this paper for ethics review, what area of expertise would it be most useful for the ethics reviewer to have? Please click all that apply.",
                    "value": {
                        "param": {
                            "type": "string[]",
                            "enum": [
                                "Discrimination / Bias / Fairness Concerns",
                                "Inadequate Data and Algorithm Evaluation",
                                "Inappropriate Potential Applications & Impact  (e.g., human rights concerns)",
                                "Privacy and Security (e.g., consent)",
                                "Legal Compliance (e.g., GDPR, copyright, terms of use)",
                                "Research Integrity Issues (e.g., plagiarism)",
                                "Responsible Research Practice (e.g., IRB, documentation, research ethics)",
                                "I don't know"
                            ],
                            "input": "checkbox",
                            "optional": True,
                        }
                    }
                },
                "soundness": {
                    "order": 7,
                    "description": "Please assign the paper a numerical rating on the following scale to indicate the soundness of the technical claims, experimental and research methodology and on whether the central claims of the paper are adequately supported with evidence.",
                    "value": {
                        "param": {
                            "type": "string",
                            "enum": [
                                "4 excellent",
                                "3 good",
                                "2 fair",
                                "1 poor"
                            ],
                            "input": "radio"
                        }
                    }
                },
                "presentation": {
                    "order": 8,
                    "description": "Please assign the paper a numerical rating on the following scale to indicate the quality of the presentation. This should take into account the writing style and clarity, as well as contextualization relative to prior work.",
                    "value": {
                        "param": {
                            "type": "string",
                            "enum": [
                                "4 excellent",
                                "3 good",
                                "2 fair",
                                "1 poor"
                            ],
                            "input": "radio"
                        }
                    }
                },
                "contribution": {
                    "order": 9,
                    "description": "Please assign the paper a numerical rating on the following scale to indicate the quality of the overall contribution this paper makes to the research area being studied. Are the questions being asked important? Does the paper bring a significant originality of ideas and/or execution? Are the results valuable to share with the broader ICML community?",
                    "value": {
                        "param": {
                            "type": "string",
                            "enum": [
                                "4 excellent",
                                "3 good",
                                "2 fair",
                                "1 poor"
                            ],
                            "input": "radio"
                        }
                    }
                },
                "rating": {
                    "order": 10,
                    "description": "Please provide an \"overall score\" for this submission.",
                    "value": {
                        "param": {
                            "type": 'integer',
                            "enum": [
                                { 'value': 10, 'description': "10: Award quality: Technically flawless paper with groundbreaking impact, with exceptionally strong evaluation, reproducibility, and resources, and no unaddressed ethical considerations." },
                                { 'value': 9, 'description': "9: Very Strong Accept: Technically flawless paper with groundbreaking impact on at least one area of AI/ML and excellent impact on multiple areas of AI/ML, with flawless evaluation, resources, and reproducibility, and no unaddressed ethical considerations." },
                                { 'value': 8, 'description': "8: Strong Accept: Technically strong paper, with novel ideas, excellent impact on at least one area, or high-to-excellent impact on multiple areas, with excellent evaluation, resources, and reproducibility, and no unaddressed ethical considerations." },
                                { 'value': 7, 'description': "7: Accept: Technically solid paper, with high impact on at least one sub-area, or moderate-to-high impact on more than one areas, with good-to-excellent evaluation, resources, reproducibility, and no unaddressed ethical considerations." },
                                { 'value': 6, 'description': "6: Weak Accept: Technically solid, moderate-to-high impact paper, with no major concerns with respect to evaluation, resources, reproducibility, ethical considerations." },
                                { 'value': 5, 'description': "5: Borderline accept: Technically solid paper where reasons to accept outweigh reasons to reject, e.g., limited evaluation. Please use sparingly." },
                                { 'value': 4, 'description': "4: Borderline reject: Technically solid paper where reasons to reject, e.g., limited evaluation, outweigh reasons to accept, e.g., good evaluation. Please use sparingly." },
                                { 'value': 3, 'description': "3: Reject: For instance, a paper with technical flaws, weak evaluation, inadequate reproducibility and incompletely addressed ethical considerations." },
                                { 'value': 2, 'description': "2: Strong Reject: For instance, a paper with major technical flaws, and/or poor evaluation, limited impact, poor reproducibility and mostly unaddressed ethical considerations." },
                                { 'value': 1, 'description': "1: Very Strong Reject: For instance, a paper with trivial results or unaddressed ethical considerations" }
                            ],
                            "input": "radio"

                        }
                    }
                },
                "confidence": {
                    "order": 11,
                    "description": "Please provide a \"confidence score\" for your assessment of this submission to indicate how confident you are in your evaluation.",
                    "value": {
                        "param": {
                            "type": 'integer',
                            "enum": [
                                { 'value': 5, 'description': "5: You are absolutely certain about your assessment. You are very familiar with the related work and checked the math/other details carefully." },
                                { 'value': 4, 'description': "4: You are confident in your assessment, but not absolutely certain. It is unlikely, but not impossible, that you did not understand some parts of the submission or that you are unfamiliar with some pieces of related work." },
                                { 'value': 3, 'description': "3: You are fairly confident in your assessment. It is possible that you did not understand some parts of the submission or that you are unfamiliar with some pieces of related work. Math/other details were not carefully checked." },
                                { 'value': 2, 'description': "2: You are willing to defend your assessment, but it is quite likely that you did not understand the central parts of the submission or that you are unfamiliar with some pieces of related work. Math/other details were not carefully checked." },
                                { 'value': 1, 'description': "1: Your assessment is an educated guess. The submission is not in your area or the submission was difficult to understand. Math/other details were not carefully checked." }
                            ],
                            "input": "radio"
                        }
                    }
                },
                "code_of_conduct": {
                    "description": "While performing my duties as a reviewer (including writing reviews and participating in discussions), I have and will continue to abide by the ICML code of conduct (https://icml.cc/public/CodeOfConduct).",
                    "order": 12,
                    "value": {
                        "param": {
                            "type": "string",
                            "enum": ["Yes"],
                            "input": "checkbox"
                        }
                    }
                }
            },
            remove_fields=['title', 'review'],
            source_submissions_query={
                'position_paper_track': 'No'
            }
        )

        venue.create_review_stage()

        helpers.await_queue_edit(openreview_client, 'ICML.cc/2023/Conference/-/Official_Review-0-1', count=2)

        assert len(openreview_client.get_invitations(invitation='ICML.cc/2023/Conference/-/Official_Review')) == 50
        invitation = openreview_client.get_invitation('ICML.cc/2023/Conference/Submission1/-/Official_Review')
        assert 'summarry' not in invitation.edit['note']['content']
        assert 'summary' in invitation.edit['note']['content']
        assert invitation.cdate < openreview.tools.datetime_millis(datetime.datetime.now())
        # duedate + 2 days
        exp_date = invitation.duedate + (2*24*60)

        venue.review_stage = openreview.stages.ReviewStage(
            start_date=start_date, 
            due_date=due_date,
            exp_date=review_exp_date,
            name='Position_Paper_Review',
            remove_fields=['title'],
            source_submissions_query={
                'position_paper_track': 'Yes'
            }
        )

        venue.create_review_stage()

        helpers.await_queue_edit(openreview_client, 'ICML.cc/2023/Conference/-/Position_Paper_Review-0-1', count=1)

        assert len(openreview_client.get_invitations(invitation='ICML.cc/2023/Conference/-/Position_Paper_Review')) == 50
        invitation = openreview_client.get_invitation('ICML.cc/2023/Conference/Submission2/-/Official_Review')
        assert 'review' in invitation.edit['note']['content']
        assert 'summary' not in invitation.edit['note']['content']

        reviewer_client = openreview.api.OpenReviewClient(username='reviewer1@icml.cc', password=helpers.strong_password)

        anon_groups = reviewer_client.get_groups(prefix='ICML.cc/2023/Conference/Submission1/Reviewer_', signatory='~Reviewer_ICMLOne1')
        anon_group_id = anon_groups[0].id

        review_edit = reviewer_client.post_note_edit(
            invitation='ICML.cc/2023/Conference/Submission1/-/Official_Review',
            signatures=[anon_group_id],
            note=openreview.api.Note(
                content={
                    'summary': { 'value': 'good paper' },
                    'strengths_and_weaknesses': { 'value': '7: Good paper, accept'},
                    'questions': { 'value': '7: Good paper, accept'},
                    'limitations': { 'value': '7: Good paper, accept'},
                    'ethics_flag': { 'value': 'No'},
                    'soundness': { 'value': '3 good'},
                    'presentation': { 'value': '3 good'},
                    'contribution': { 'value': '3 good'},
                    'rating': { 'value': 10 },
                    'confidence': { 'value': 5 },
                    'code_of_conduct': { 'value': 'Yes'},
                }
            )
        )

        helpers.await_queue_edit(openreview_client, edit_id=review_edit['id'])

        messages = openreview_client.get_messages(to='ac2@icml.cc', subject='[ICML 2023] Official Review posted to your assigned Paper number: 1, Paper title: "Paper title 1 Version 2"')
        assert messages and len(messages) == 1

        messages = openreview_client.get_messages(to='reviewer1@icml.cc', subject='[ICML 2023] Your official review has been received on your assigned Paper number: 1, Paper title: "Paper title 1 Version 2"')
        assert messages and len(messages) == 1
        assert messages[0]['content']['replyTo'] == 'pc@icml.cc'

        ## check how the description is rendered
        note = review_edit['note']
        review_id = note['id']
        request_page(selenium, "http://localhost:3030/forum?id=" + review_edit['note']['forum'], openreview_client.token, by=By.ID, wait_for_element='forum-replies')
        note_panel = selenium.find_element(By.XPATH, f'//div[@data-id="{review_id}"]')
        fields = note_panel.find_elements(By.CLASS_NAME, 'note-content-field')
        assert len(fields) == 11
        assert fields[8].text == 'Rating:'
        assert fields[9].text == 'Confidence:'        
        values = note_panel.find_elements(By.CLASS_NAME, 'note-content-value')
        assert len(values) == 11
        assert values[8].text == '10: Award quality: Technically flawless paper with groundbreaking impact, with exceptionally strong evaluation, reproducibility, and resources, and no unaddressed ethical considerations.'
        assert values[9].text == '5: You are absolutely certain about your assessment. You are very familiar with the related work and checked the math/other details carefully.'        

        review_edit = reviewer_client.post_note_edit(
            invitation='ICML.cc/2023/Conference/Submission1/-/Official_Review',
            signatures=[anon_group_id],
            note=openreview.api.Note(
                id = review_edit['note']['id'],
                content={
                    'summary': { 'value': 'good paper version 2' },
                    'strengths_and_weaknesses': { 'value': '7: Good paper, accept'},
                    'questions': { 'value': '7: Good paper, accept'},
                    'limitations': { 'value': '7: Good paper, accept'},
                    'ethics_flag': { 'value': 'No'},
                    'soundness': { 'value': '3 good'},
                    'presentation': { 'value': '3 good'},
                    'contribution': { 'value': '3 good'},
                    'rating': { 'value': 10 },
                    'confidence': { 'value': 5 },
                    'code_of_conduct': { 'value': 'Yes'},
                }
            )
        )

        helpers.await_queue_edit(openreview_client, edit_id=review_edit['id'])

        messages = openreview_client.get_messages(to='ac2@icml.cc', subject='[ICML 2023] Official Review posted to your assigned Paper number: 1, Paper title: "Paper title 1 Version 2"')
        assert messages and len(messages) == 1

        messages = openreview_client.get_messages(to='reviewer1@icml.cc', subject='[ICML 2023] Your official review has been received on your assigned Paper number: 1, Paper title: "Paper title 1 Version 2"')
        assert messages and len(messages) == 1

        openreview_client.add_members_to_group(f'ICML.cc/2023/Conference/Submission1/Reviewers', '~Reviewer_ICMLOne1')
        openreview_client.add_members_to_group(f'ICML.cc/2023/Conference/Submission1/Reviewers', '~Reviewer_ICMLTwo1')
        openreview_client.add_members_to_group(f'ICML.cc/2023/Conference/Submission1/Reviewers', '~Reviewer_ICMLThree1')

        reviewer_client_2 = openreview.api.OpenReviewClient(username='reviewer2@icml.cc', password=helpers.strong_password)
        anon_groups = reviewer_client.get_groups(prefix='ICML.cc/2023/Conference/Submission1/Reviewer_', signatory='~Reviewer_ICMLTwo1')
        anon_group_id = anon_groups[0].id
        review_edit = reviewer_client_2.post_note_edit(
            invitation='ICML.cc/2023/Conference/Submission1/-/Official_Review',
            signatures=[anon_group_id],
            note=openreview.api.Note(
                content={
                    'summary': { 'value': 'bad paper' },
                    'strengths_and_weaknesses': { 'value': '2: Bad paper, reject'},
                    'questions': { 'value': '2: Bad paper, reject'},
                    'limitations': { 'value': '2: Bad paper, reject'},
                    'ethics_flag': { 'value': 'No'},
                    'soundness': { 'value': '1 poor'},
                    'presentation': { 'value': '1 poor'},
                    'contribution': { 'value': '1 poor'},
                    'rating': { 'value': 1 },
                    'confidence': { 'value': 5 },
                    'code_of_conduct': { 'value': 'Yes'},
                }
            )
        )

        helpers.await_queue_edit(openreview_client, edit_id=review_edit['id'])

        anon_groups = reviewer_client.get_groups(prefix='ICML.cc/2023/Conference/Submission2/Reviewer_', signatory='~Reviewer_ICMLOne1')
        anon_group_id = anon_groups[0].id

        review_edit = reviewer_client.post_note_edit(
            invitation='ICML.cc/2023/Conference/Submission2/-/Official_Review',
            signatures=[anon_group_id],
            note=openreview.api.Note(
                content={
                    'review': { 'value': 'This is a good review for a good paper' },
                    'rating': { 'value': 7 },
                    'confidence': { 'value': 5 }
                }
            )
        )

        helpers.await_queue_edit(openreview_client, edit_id=review_edit['id'])

        pc_client_v2=openreview.api.OpenReviewClient(username='pc@icml.cc', password=helpers.strong_password)

        # try post review note signing as PC
        with pytest.raises(openreview.OpenReviewException) as openReviewError:
            review_edit = pc_client_v2.post_note_edit(
                invitation='ICML.cc/2023/Conference/Submission2/-/Official_Review',
                signatures=['ICML.cc/2023/Conference/Program_Chairs'],
                note=openreview.api.Note(
                    content={
                        'review': { 'value': 'review by PC' },
                        'rating': { 'value': 10 },
                        'confidence': { 'value': 1 }
                    }
                )
            )
        assert openReviewError.value.args[0].get('name') == 'ItemsError'

        pc_client_v2=openreview.api.OpenReviewClient(username='pc@icml.cc', password=helpers.strong_password)

        anon_groups = reviewer_client.get_groups(prefix='ICML.cc/2023/Conference/Submission1/Reviewer_', signatory='~Reviewer_ICMLOne1')
        anon_group_id = anon_groups[0].id

        reviews = pc_client_v2.get_notes(invitation='ICML.cc/2023/Conference/Submission1/-/Official_Review', sort='number:asc')
        assert len(reviews) == 2
        assert anon_group_id in reviews[0].readers

        ## Extend deadline using a meta invitation and propagate the change to all the children
        new_due_date = openreview.tools.datetime_millis(now + datetime.timedelta(days=20))
        new_exp_date = openreview.tools.datetime_millis(now + datetime.timedelta(days=25))
        pc_client_v2.post_invitation_edit(
            invitations='ICML.cc/2023/Conference/-/Edit',
            readers=['ICML.cc/2023/Conference'],
            writers=['ICML.cc/2023/Conference'],
            signatures=['ICML.cc/2023/Conference'],
            invitation=openreview.api.Invitation(
                id='ICML.cc/2023/Conference/-/Official_Review',
                edit={
                    'invitation': {
                        'duedate': new_due_date,
                        'expdate': new_exp_date
                    }
                }
            )
        )

        helpers.await_queue_edit(openreview_client, 'ICML.cc/2023/Conference/-/Official_Review-0-1', count=3)

        invitation = pc_client_v2.get_invitation('ICML.cc/2023/Conference/Submission1/-/Official_Review')
        assert invitation.duedate == new_due_date
        assert invitation.expdate == new_exp_date

        ## Extend deadline using a meta invitation and propagate the change to all the children
        new_due_date = openreview.tools.datetime_millis(now + datetime.timedelta(days=10))
        new_exp_date = openreview.tools.datetime_millis(now + datetime.timedelta(days=15))
        pc_client_v2.post_invitation_edit(
            invitations='ICML.cc/2023/Conference/-/Edit',
            readers=['ICML.cc/2023/Conference'],
            writers=['ICML.cc/2023/Conference'],
            signatures=['ICML.cc/2023/Conference'],
            invitation=openreview.api.Invitation(
                id='ICML.cc/2023/Conference/-/Position_Paper_Review',
                edit={
                    'invitation': {
                        'duedate': new_due_date,
                        'expdate': new_exp_date
                    }
                }
            )
        )

        helpers.await_queue_edit(openreview_client, 'ICML.cc/2023/Conference/-/Position_Paper_Review-0-1', count=2)

        #get rebuttal stage invitation
        rebuttal_stage_invitation = pc_client.get_invitation(f'openreview.net/Support/-/Request{request_form.number}/Rebuttal_Stage')
        assert rebuttal_stage_invitation

    def test_review_rating(self, client, openreview_client, helpers):

        pc_client=openreview.Client(username='pc@icml.cc', password=helpers.strong_password)
        request_form=pc_client.get_notes(invitation='openreview.net/Support/-/Request_Form')[0]
        venue = openreview.get_conference(client, request_form.id, support_user='openreview.net/Support')

        now = datetime.datetime.now()
        due_date = now + datetime.timedelta(days=3)
        venue.custom_stage = openreview.stages.CustomStage(name='Rating',
            reply_to=openreview.stages.CustomStage.ReplyTo.REVIEWS,
            source=openreview.stages.CustomStage.Source.ALL_SUBMISSIONS,
            due_date=due_date,
            exp_date=due_date + datetime.timedelta(days=1),
            invitees=[openreview.stages.CustomStage.Participants.AREA_CHAIRS_ASSIGNED],
            readers=[openreview.stages.CustomStage.Participants.SENIOR_AREA_CHAIRS_ASSIGNED, openreview.stages.CustomStage.Participants.AREA_CHAIRS_ASSIGNED],
            content={
                'review_quality': {
                    'order': 1,
                    'description': 'How helpful is this review:',
                    'value': {
                        'param': {
                            'type': 'string',
                            'input': 'radio',
                            'enum': [
                                'Poor - not very helpful',
                                'Good',
                                'Outstanding'
                            ]
                        }
                    }
                }
            },
            notify_readers=True,
            email_sacs=True)

        venue.create_custom_stage()

        helpers.await_queue_edit(openreview_client, 'ICML.cc/2023/Conference/-/Rating-0-1', count=1)

        submissions = venue.get_submissions(sort='number:asc', details='directReplies')
        first_submission = submissions[0]
        reviews = [reply for reply in first_submission.details['directReplies'] if f'ICML.cc/2023/Conference/Submission{first_submission.number}/-/Official_Review']

        reviewer_client = openreview.api.OpenReviewClient(username='reviewer1@icml.cc', password=helpers.strong_password)
        anon_groups = reviewer_client.get_groups(prefix='ICML.cc/2023/Conference/Submission1/Reviewer_', signatory='~Reviewer_ICMLOne1')
        anon_group_id = anon_groups[0].id

        assert len(openreview_client.get_invitations(invitation='ICML.cc/2023/Conference/-/Rating')) == 3

        invitation = openreview_client.get_invitation('ICML.cc/2023/Conference/Submission1/Official_Review1/-/Rating')
        assert invitation.invitees == ['ICML.cc/2023/Conference', 'ICML.cc/2023/Conference/Submission1/Area_Chairs']
        assert 'review_quality' in invitation.edit['note']['content']
        assert invitation.edit['note']['forum'] == submissions[0].id
        assert invitation.edit['note']['replyto'] == reviews[0]['id']
        assert invitation.edit['note']['readers'] == [
            'ICML.cc/2023/Conference/Program_Chairs',
            'ICML.cc/2023/Conference/Submission1/Senior_Area_Chairs',
            'ICML.cc/2023/Conference/Submission1/Area_Chairs'
        ]

        ac_client = openreview.api.OpenReviewClient(username='ac2@icml.cc', password=helpers.strong_password)
        ac_anon_groups = ac_client.get_groups(prefix='ICML.cc/2023/Conference/Submission1/Area_Chair_', signatory='~AC_ICMLTwo1')
        ac_anon_group_id = ac_anon_groups[0].id

        #post a review rating
        rating_edit = ac_client.post_note_edit(
            invitation=invitation.id,
            signatures=[ac_anon_group_id],
            note=openreview.api.Note(
                content={
                    'review_quality': { 'value': 'Poor - not very helpful' },
                }
            )
        )

        helpers.await_queue_edit(openreview_client, edit_id=rating_edit['id'])

        reviewer_client = openreview.api.OpenReviewClient(username='reviewer2@icml.cc', password=helpers.strong_password)
        anon_groups = reviewer_client.get_groups(prefix='ICML.cc/2023/Conference/Submission1/Reviewer_', signatory='~Reviewer_ICMLTwo1')
        anon_group_id = anon_groups[0].id
        invitation = openreview_client.get_invitation('ICML.cc/2023/Conference/Submission1/Official_Review2/-/Rating')

        #post another review rating to same paper
        rating_edit = ac_client.post_note_edit(
            invitation=invitation.id,
            signatures=[ac_anon_group_id],
            note=openreview.api.Note(
                content={
                    'review_quality': { 'value': 'Outstanding' },
                }
            )
        )

        helpers.await_queue_edit(openreview_client, edit_id=rating_edit['id'])

        pc_client_v2=openreview.api.OpenReviewClient(username='pc@icml.cc', password=helpers.strong_password)

        notes = pc_client_v2.get_notes(invitation=invitation.id)
        assert len(notes) == 1
        assert notes[0].readers == [
            'ICML.cc/2023/Conference/Program_Chairs',
            'ICML.cc/2023/Conference/Submission1/Senior_Area_Chairs',
            'ICML.cc/2023/Conference/Submission1/Area_Chairs'
        ]
        assert notes[0].signatures == [ac_anon_group_id]

        #hide review ratings from Senior Area Chairs
        venue.custom_stage = openreview.stages.CustomStage(name='Rating',
            reply_to=openreview.stages.CustomStage.ReplyTo.REVIEWS,
            source=openreview.stages.CustomStage.Source.ALL_SUBMISSIONS,
            due_date=due_date,
            exp_date=due_date + datetime.timedelta(days=1),
            invitees=[openreview.stages.CustomStage.Participants.AREA_CHAIRS_ASSIGNED],
            readers=[openreview.stages.CustomStage.Participants.AREA_CHAIRS_ASSIGNED],
            content={
                'review_quality': {
                    'order': 1,
                    'description': 'How helpful is this review:',
                    'value': {
                        'param': {
                            'type': 'string',
                            'input': 'radio',
                            'enum': [
                                'Poor - not very helpful',
                                'Good',
                                'Outstanding'
                            ]
                        }
                    }
                }
            })

        venue.create_custom_stage()

        helpers.await_queue_edit(openreview_client, 'ICML.cc/2023/Conference/-/Rating-0-1', count=2)

        notes = pc_client_v2.get_notes(invitation=invitation.id)
        assert len(notes) == 1
        assert notes[0].readers == [
            'ICML.cc/2023/Conference/Program_Chairs',
            'ICML.cc/2023/Conference/Submission1/Area_Chairs'
        ]
        assert notes[0].signatures == [ac_anon_group_id]

        messages = openreview_client.get_messages(to='sac2@icml.cc', subject='[ICML 2023] A rating has been received on your assigned Paper Number: 1, Paper Title: "Paper title 1 Version 2"')
        assert len(messages) == 2
        assert 'We have received a rating on a submission to ICML 2023 for which you are serving as Senior Area Chair.' in messages[0]['content']['text']
        messages = openreview_client.get_messages(to='ac2@icml.cc', subject='[ICML 2023] Your rating has been received on Paper Number: 1, Paper Title: "Paper title 1 Version 2"')
        assert len(messages) == 2
        assert 'We have received your rating on a submission to ICML 2023.' in messages[0]['content']['text']

        # post review and check review rating inv is created
        reviewer_client = openreview.api.OpenReviewClient(username='reviewer1@icml.cc', password=helpers.strong_password)
        anon_groups = reviewer_client.get_groups(prefix='ICML.cc/2023/Conference/Submission3/Reviewer_', signatory='~Reviewer_ICMLOne1')
        anon_group_id = anon_groups[0].id

        review_edit = reviewer_client.post_note_edit(
            invitation='ICML.cc/2023/Conference/Submission3/-/Official_Review',
            signatures=[anon_group_id],
            note=openreview.api.Note(
                content={
                    'summary': { 'value': 'good paper' },
                    'strengths_and_weaknesses': { 'value': '7: Good paper, accept'},
                    'questions': { 'value': '7: Good paper, accept'},
                    'limitations': { 'value': '7: Good paper, accept'},
                    'ethics_flag': { 'value': 'No'},
                    'soundness': { 'value': '3 good'},
                    'presentation': { 'value': '3 good'},
                    'contribution': { 'value': '3 good'},
                    'rating': { 'value': 10 },
                    'confidence': { 'value': 5 },
                    'code_of_conduct': { 'value': 'Yes'},
                }
            )
        )

        helpers.await_queue_edit(openreview_client, edit_id=review_edit['id'])

        assert len(openreview_client.get_invitations(invitation='ICML.cc/2023/Conference/-/Rating')) == 4

        invitation = openreview_client.get_invitation('ICML.cc/2023/Conference/Submission3/Official_Review1/-/Rating')
        assert invitation.invitees == ['ICML.cc/2023/Conference', 'ICML.cc/2023/Conference/Submission3/Area_Chairs']
        assert 'review_quality' in invitation.edit['note']['content']
        assert invitation.edit['note']['forum'] == review_edit['note']['forum']
        assert invitation.edit['note']['replyto'] == review_edit['note']['id']
        assert invitation.edit['note']['readers'] == [
            'ICML.cc/2023/Conference/Program_Chairs',
            'ICML.cc/2023/Conference/Submission3/Area_Chairs'
        ]

    def test_delete_assignments(self, openreview_client, helpers):

        ac_client = openreview.api.OpenReviewClient(username='ac2@icml.cc', password=helpers.strong_password)

        submissions = ac_client.get_notes(invitation='ICML.cc/2023/Conference/-/Submission', sort='number:asc')
        assignment = ac_client.get_edges(invitation='ICML.cc/2023/Conference/Reviewers/-/Assignment', head=submissions[0].id, tail='~Reviewer_ICMLOne1')[0]

        anon_group_id = ac_client.get_groups(prefix='ICML.cc/2023/Conference/Submission1/Area_Chair_', signatory='~AC_ICMLTwo1')[0].id
        assignment.ddate = openreview.tools.datetime_millis(datetime.datetime.now())
        assignment.cdate = None
        assignment.signatures = [anon_group_id]

        with pytest.raises(openreview.OpenReviewException, match=r'Can not remove assignment, the user ~Reviewer_ICMLOne1 already posted a Official Review.'):
            ac_client.post_edge(assignment)

        assignment = ac_client.get_edges(invitation='ICML.cc/2023/Conference/Reviewers/-/Assignment', head=submissions[0].id, tail='~Celeste_ICML1')[0]
        assignment.ddate = openreview.tools.datetime_millis(datetime.datetime.now())
        assignment.signatures = [anon_group_id]
        assignment.cdate = None
        ac_client.post_edge(assignment)

        #delete AC assignment of paper with a review with no error
        pc_client_v2=openreview.api.OpenReviewClient(username='pc@icml.cc', password=helpers.strong_password)

        assignment = pc_client_v2.get_edges(invitation='ICML.cc/2023/Conference/Area_Chairs/-/Assignment', head=submissions[0].id, tail='~AC_ICMLTwo1')[0]
        assignment.ddate = openreview.tools.datetime_millis(datetime.datetime.now())
        assignment.cdate = None
        pc_client_v2.post_edge(assignment)

        helpers.await_queue_edit(openreview_client, edit_id=assignment.id, count=2)

        ac_group = pc_client_v2.get_group('ICML.cc/2023/Conference/Submission1/Area_Chairs')
        assert [] == ac_group.members

        sac_group = pc_client_v2.get_group('ICML.cc/2023/Conference/Submission1/Senior_Area_Chairs')
        assert [] == sac_group.members

        #re-add AC to paper 1
        assignment = pc_client_v2.get_edges(invitation='ICML.cc/2023/Conference/Area_Chairs/-/Assignment', head=submissions[0].id, tail='~AC_ICMLTwo1', trash=True)[0]
        assignment.ddate = { 'delete': True }
        assignment.cdate = None
        pc_client_v2.post_edge(assignment)

        helpers.await_queue_edit(openreview_client, edit_id=assignment.id, count=3)

        ac_group = pc_client_v2.get_group('ICML.cc/2023/Conference/Submission1/Area_Chairs')
        assert ['~AC_ICMLTwo1'] == ac_group.members

        sac_group = pc_client_v2.get_group('ICML.cc/2023/Conference/Submission1/Senior_Area_Chairs')
        assert ['~SAC_ICMLTwo1'] == sac_group.members

    def test_ethics_review_stage(self, openreview_client, helpers, selenium, request_page):
        pc_client=openreview.Client(username='pc@icml.cc', password=helpers.strong_password)
        request_form=pc_client.get_notes(invitation='openreview.net/Support/-/Request_Form')[0]

        reviewer_details = '''reviewerethics@yahoo.com, Reviewer ICMLSeven'''
        recruitment_note = pc_client.post_note(openreview.Note(
            content={
                'title': 'Recruitment',
                'invitee_role': 'Ethics_Reviewers',
                'invitee_reduced_load': ['2', '3', '4'],
                'invitee_details': reviewer_details,
                'invitation_email_subject': '[' + request_form.content['Abbreviated Venue Name'] + '] Invitation to serve as {{invitee_role}}',
                'invitation_email_content': 'Dear {{fullname}},\n\nYou have been nominated by the program chair committee of ICML 2023 to serve as {{invitee_role}}.\n\n{{invitation_url}}\n\nIf you have any questions, please contact {{contact_info}}.\n\nCheers!\n\nProgram Chairs'
            },
            forum=request_form.forum,
            replyto=request_form.forum,
            invitation='openreview.net/Support/-/Request{}/Recruitment'.format(request_form.number),
            readers=['ICML.cc/2023/Conference/Program_Chairs', 'openreview.net/Support'],
            signatures=['~Program_ICMLChair1'],
            writers=[]
        ))
        assert recruitment_note
        helpers.await_queue()        
              
        group = openreview_client.get_group('ICML.cc/2023/Conference/Ethics_Reviewers')
        assert group
        assert 'ICML.cc/2023/Conference/Ethics_Chairs' in group.readers
        assert openreview_client.get_group('ICML.cc/2023/Conference/Ethics_Reviewers/Declined')
        group = openreview_client.get_group('ICML.cc/2023/Conference/Ethics_Reviewers/Invited')
        assert group
        assert len(group.members) == 1
        assert 'reviewerethics@yahoo.com' in group.members
        assert 'ICML.cc/2023/Conference/Ethics_Chairs' in group.readers

        messages = openreview_client.get_messages(to='reviewerethics@yahoo.com', subject='[ICML 2023] Invitation to serve as Ethics Reviewer')
        assert messages and len(messages) == 1
        invitation_url = re.search('https://.*\n', messages[0]['content']['text']).group(0).replace('https://openreview.net', 'http://localhost:3030').replace('&amp;', '&')[:-1]
        helpers.respond_invitation_fast(invitation_url, accept=True)

        helpers.await_queue()

        group = openreview_client.get_group('ICML.cc/2023/Conference/Ethics_Reviewers')
        assert group
        assert len(group.members) == 1
        assert 'reviewerethics@yahoo.com' in group.members

        now = datetime.datetime.now()
        start_date = now - datetime.timedelta(days=2)
        due_date = now + datetime.timedelta(days=3)
        stage_note = pc_client.post_note(openreview.Note(
            content={
                'ethics_review_start_date': start_date.strftime('%Y/%m/%d'),
                'ethics_review_deadline': due_date.strftime('%Y/%m/%d'),
                'make_ethics_reviews_public': 'No, ethics reviews should NOT be revealed publicly when they are posted',
                'release_ethics_reviews_to_authors': "No, ethics reviews should NOT be revealed when they are posted to the paper\'s authors",
                'release_ethics_reviews_to_reviewers': 'Ethics Review should not be revealed to any reviewer, except to the author of the ethics review',
                'remove_ethics_review_form_options': 'ethics_review',
                'additional_ethics_review_form_options': {
                    "ethics_concerns": {
                        'order': 1,
                        'description': 'Briefly summarize the ethics concerns.',
                        'value': {
                            'param': {
                                'type': 'string',
                                'maxLength': 200000,
                                'markdown': True,
                                'input': 'textarea'
                            }
                        }
                    }
                },
                'release_submissions_to_ethics_reviewers': 'We confirm we want to release the submissions and reviews to the ethics reviewers'
            },
            forum=request_form.forum,
            referent=request_form.forum,
            invitation='openreview.net/Support/-/Request{}/Ethics_Review_Stage'.format(request_form.number),
            readers=['ICML.cc/2023/Conference/Program_Chairs', 'openreview.net/Support'],
            signatures=['~Program_ICMLChair1'],
            writers=[]
        ))

        helpers.await_queue()

        helpers.await_queue_edit(openreview_client, 'ICML.cc/2023/Conference/-/Ethics_Review-0-1', count=1)

        configuration_invitation = openreview_client.get_invitation('ICML.cc/2023/Conference/Ethics_Reviewers/-/Assignment_Configuration')
        assert configuration_invitation.edit['note']['content']['paper_invitation']['value']['param']['default'] == 'ICML.cc/2023/Conference/-/Submission&content.venueid=ICML.cc/2023/Conference/Submission&content.flagged_for_ethics_review=true'

        pc_client_v2=openreview.api.OpenReviewClient(username='pc@icml.cc', password=helpers.strong_password)
        notes = openreview_client.get_notes(invitation='ICML.cc/2023/Conference/-/Submission', number=[1,5])
        for note in notes:
            note_edit = pc_client_v2.post_note_edit(
                invitation='ICML.cc/2023/Conference/-/Ethics_Review_Flag',
                note=openreview.api.Note(
                    id=note.id,
                    content = {
                        'flagged_for_ethics_review': { 'value': True },
                        'ethics_comments': { 'value': 'These are ethics comments visible to ethics chairs and ethics reviewers' }
                    }
                ),
                signatures=['ICML.cc/2023/Conference']
            )

            helpers.await_queue()
            helpers.await_queue_edit(openreview_client, edit_id=note_edit['id'])

        openreview_client.add_members_to_group('ICML.cc/2023/Conference/Submission5/Ethics_Reviewers', '~Celeste_ICML1')

        submissions = openreview_client.get_notes(content= { 'venueid': 'ICML.cc/2023/Conference/Submission'}, sort='number:asc')
        assert submissions and len(submissions) == 100
        assert 'flagged_for_ethics_review' in submissions[0].content and submissions[0].content['flagged_for_ethics_review']['value']
        assert 'ethics_comments' in submissions[0].content
        assert submissions[0].content['flagged_for_ethics_review']['readers'] == [
            'ICML.cc/2023/Conference',
            'ICML.cc/2023/Conference/Ethics_Chairs',
            'ICML.cc/2023/Conference/Submission1/Ethics_Reviewers',
            'ICML.cc/2023/Conference/Submission1/Senior_Area_Chairs',
            'ICML.cc/2023/Conference/Submission1/Area_Chairs',
            'ICML.cc/2023/Conference/Submission1/Reviewers'
        ]
        assert 'flagged_for_ethics_review' in submissions[4].content and submissions[4].content['flagged_for_ethics_review']['value']
        assert 'ethics_comments' in submissions[4].content
        assert submissions[4].content['flagged_for_ethics_review']['readers'] == [
            'ICML.cc/2023/Conference',
            'ICML.cc/2023/Conference/Ethics_Chairs',
            'ICML.cc/2023/Conference/Submission5/Ethics_Reviewers',
            'ICML.cc/2023/Conference/Submission5/Senior_Area_Chairs',
            'ICML.cc/2023/Conference/Submission5/Area_Chairs',
            'ICML.cc/2023/Conference/Submission5/Reviewers'
        ]
        ethics_group = openreview.tools.get_group(openreview_client, 'ICML.cc/2023/Conference/Submission1/Ethics_Reviewers')
        assert ethics_group
        ethics_group = openreview.tools.get_group(openreview_client, 'ICML.cc/2023/Conference/Submission2/Ethics_Reviewers')
        assert not ethics_group
        ethics_group = openreview.tools.get_group(openreview_client, 'ICML.cc/2023/Conference/Submission5/Ethics_Reviewers')
        assert ethics_group and '~Celeste_ICML1' in ethics_group.members
        assert submissions[0].readers == [
            "ICML.cc/2023/Conference",
            "ICML.cc/2023/Conference/Submission1/Senior_Area_Chairs",
            "ICML.cc/2023/Conference/Submission1/Area_Chairs",
            "ICML.cc/2023/Conference/Submission1/Reviewers",
            "ICML.cc/2023/Conference/Submission1/Authors",
            "ICML.cc/2023/Conference/Submission1/Ethics_Reviewers"
        ]
        assert submissions[1].readers == [
            "ICML.cc/2023/Conference",
            "ICML.cc/2023/Conference/Submission2/Senior_Area_Chairs",
            "ICML.cc/2023/Conference/Submission2/Area_Chairs",
            "ICML.cc/2023/Conference/Submission2/Reviewers",
            "ICML.cc/2023/Conference/Submission2/Authors"        ]
        assert submissions[4].readers == [
            "ICML.cc/2023/Conference",
            "ICML.cc/2023/Conference/Submission5/Senior_Area_Chairs",
            "ICML.cc/2023/Conference/Submission5/Area_Chairs",
            "ICML.cc/2023/Conference/Submission5/Reviewers",
            "ICML.cc/2023/Conference/Submission5/Authors",
            "ICML.cc/2023/Conference/Submission5/Ethics_Reviewers"
        ]

        reviews = openreview_client.get_notes(invitation='ICML.cc/2023/Conference/Submission1/-/Official_Review')
        assert reviews and len(reviews) == 2
        for review in reviews:
            assert review.readers == [
                'ICML.cc/2023/Conference/Program_Chairs',
                'ICML.cc/2023/Conference/Submission1/Senior_Area_Chairs',
                'ICML.cc/2023/Conference/Submission1/Area_Chairs',
                'ICML.cc/2023/Conference/Submission1/Ethics_Reviewers',
                review.signatures[0]
            ]

        invitations = openreview_client.get_invitations(invitation='ICML.cc/2023/Conference/-/Ethics_Review')
        assert len(invitations) == 2
        invitation = openreview_client.get_invitations(id='ICML.cc/2023/Conference/Submission1/-/Ethics_Review')[0]
        assert invitation
        assert 'ICML.cc/2023/Conference/Submission1/Ethics_Reviewers' in invitation.invitees

        # re-run ethics review stage
        now = datetime.datetime.now()
        start_date = now - datetime.timedelta(days=1)
        stage_note = pc_client.post_note(openreview.Note(
            content={
                'ethics_review_start_date': start_date.strftime('%Y/%m/%d'),
                'ethics_review_deadline': due_date.strftime('%Y/%m/%d'),
                'make_ethics_reviews_public': 'No, ethics reviews should NOT be revealed publicly when they are posted',
                'release_ethics_reviews_to_authors': "No, ethics reviews should NOT be revealed when they are posted to the paper\'s authors",
                'release_ethics_reviews_to_reviewers': 'Ethics Review should not be revealed to any reviewer, except to the author of the ethics review',
                'remove_ethics_review_form_options': 'ethics_review',
                'additional_ethics_review_form_options': {
                    "ethics_concerns": {
                        'order': 1,
                        'description': 'Briefly summarize the ethics concerns.',
                        'value': {
                            'param': {
                                'type': 'string',
                                'maxLength': 200000,
                                'markdown': True,
                                'input': 'textarea'
                            }
                        }
                    }
                },
                'release_submissions_to_ethics_reviewers': 'We confirm we want to release the submissions and reviews to the ethics reviewers',
                'enable_comments_for_ethics_reviewers': 'Yes, enable commenting for ethics reviewers.'
            },
            forum=request_form.forum,
            referent=request_form.forum,
            invitation='openreview.net/Support/-/Request{}/Ethics_Review_Stage'.format(request_form.number),
            readers=['ICML.cc/2023/Conference/Program_Chairs', 'openreview.net/Support'],
            signatures=['~Program_ICMLChair1'],
            writers=[]
        ))

        helpers.await_queue()

        helpers.await_queue_edit(openreview_client, 'ICML.cc/2023/Conference/-/Official_Comment-0-1', count=1)

        helpers.await_queue_edit(openreview_client, 'ICML.cc/2023/Conference/-/Ethics_Review-0-1', count=2)

        notes = openreview_client.get_notes(invitation='ICML.cc/2023/Conference/-/Submission', number=[6,7,8,100])
        for note in notes:
            note_edit = pc_client_v2.post_note_edit(
                invitation='ICML.cc/2023/Conference/-/Ethics_Review_Flag',
                note=openreview.api.Note(
                    id=note.id,
                    content = {
                        'flagged_for_ethics_review': { 'value': True },
                    }
                ),
                signatures=['ICML.cc/2023/Conference']
            )

            helpers.await_queue()
            helpers.await_queue_edit(openreview_client, edit_id=note_edit['id'])

        submissions = openreview_client.get_notes(content= { 'venueid': 'ICML.cc/2023/Conference/Submission'}, sort='number:asc')
        assert submissions and len(submissions) == 100
        assert 'flagged_for_ethics_review' in submissions[-1].content and submissions[-1].content['flagged_for_ethics_review']['value']
        ethics_group = openreview.tools.get_group(openreview_client, 'ICML.cc/2023/Conference/Submission7/Ethics_Reviewers')
        assert ethics_group
        ethics_group = openreview.tools.get_group(openreview_client, 'ICML.cc/2023/Conference/Submission8/Ethics_Reviewers')
        assert ethics_group
        ethics_group = openreview.tools.get_group(openreview_client, 'ICML.cc/2023/Conference/Submission100/Ethics_Reviewers')
        assert ethics_group
        assert submissions[0].readers == [
            "ICML.cc/2023/Conference",
            "ICML.cc/2023/Conference/Submission1/Senior_Area_Chairs",
            "ICML.cc/2023/Conference/Submission1/Area_Chairs",
            "ICML.cc/2023/Conference/Submission1/Reviewers",
            "ICML.cc/2023/Conference/Submission1/Authors",
            "ICML.cc/2023/Conference/Submission1/Ethics_Reviewers"
        ]
        assert submissions[1].readers == [
            "ICML.cc/2023/Conference",
            "ICML.cc/2023/Conference/Submission2/Senior_Area_Chairs",
            "ICML.cc/2023/Conference/Submission2/Area_Chairs",
            "ICML.cc/2023/Conference/Submission2/Reviewers",
            "ICML.cc/2023/Conference/Submission2/Authors"        ]
        assert submissions[4].readers == [
            "ICML.cc/2023/Conference",
            "ICML.cc/2023/Conference/Submission5/Senior_Area_Chairs",
            "ICML.cc/2023/Conference/Submission5/Area_Chairs",
            "ICML.cc/2023/Conference/Submission5/Reviewers",
            "ICML.cc/2023/Conference/Submission5/Authors",
            "ICML.cc/2023/Conference/Submission5/Ethics_Reviewers"
        ]
        assert submissions[-1].readers == [
            "ICML.cc/2023/Conference",
            "ICML.cc/2023/Conference/Submission100/Senior_Area_Chairs",
            "ICML.cc/2023/Conference/Submission100/Area_Chairs",
            "ICML.cc/2023/Conference/Submission100/Reviewers",
            "ICML.cc/2023/Conference/Submission100/Authors",
            "ICML.cc/2023/Conference/Submission100/Ethics_Reviewers"
        ]

        reviews = openreview_client.get_notes(invitation='ICML.cc/2023/Conference/Submission1/-/Official_Review')
        assert reviews and len(reviews) == 2
        for review in reviews:
            assert review.readers == [
                'ICML.cc/2023/Conference/Program_Chairs',
                'ICML.cc/2023/Conference/Submission1/Senior_Area_Chairs',
                'ICML.cc/2023/Conference/Submission1/Area_Chairs',
                'ICML.cc/2023/Conference/Submission1/Ethics_Reviewers',
                review.signatures[0]
            ]

        invitations = openreview_client.get_invitations(invitation='ICML.cc/2023/Conference/-/Ethics_Review')
        assert len(invitations) == 6
        invitation = openreview_client.get_invitations(id='ICML.cc/2023/Conference/Submission100/-/Ethics_Review')[0]
        assert invitation
        assert 'ICML.cc/2023/Conference/Submission100/Ethics_Reviewers' in invitation.invitees

        # use invitation to flag paper
        pc_client_v2=openreview.api.OpenReviewClient(username='pc@icml.cc', password=helpers.strong_password)
        note = openreview_client.get_notes(invitation='ICML.cc/2023/Conference/-/Submission', number=[52])[0]
        note_edit = pc_client_v2.post_note_edit(
            invitation='ICML.cc/2023/Conference/-/Ethics_Review_Flag',
            note=openreview.api.Note(
                id=note.id,
                content = {
                    'flagged_for_ethics_review': { 'value': True },
                }
            ),
            signatures=['ICML.cc/2023/Conference']
        )

        helpers.await_queue()
        helpers.await_queue_edit(openreview_client, edit_id=note_edit['id'])

        submissions = openreview_client.get_notes(content= { 'venueid': 'ICML.cc/2023/Conference/Submission'}, sort='number:asc')
        assert submissions and len(submissions) == 100
        assert 'flagged_for_ethics_review' in submissions[51].content and submissions[51].content['flagged_for_ethics_review']['value']
        assert 'ICML.cc/2023/Conference/Submission52/Ethics_Reviewers' in submissions[51].readers
        ethics_group = openreview.tools.get_group(openreview_client, 'ICML.cc/2023/Conference/Submission52/Ethics_Reviewers')
        assert ethics_group
        invitation = openreview_client.get_invitations(id='ICML.cc/2023/Conference/Submission52/-/Ethics_Review')[0]
        assert invitation
        assert 'ICML.cc/2023/Conference/Submission52/Ethics_Reviewers' in invitation.invitees

        # comment invitations are created for all papers, with only PCs and ethics reviewers as invitees
        invitations = openreview_client.get_all_invitations(invitation='ICML.cc/2023/Conference/-/Official_Comment')
        assert len(invitations) == 100
        invitation = openreview_client.get_invitation('ICML.cc/2023/Conference/Submission1/-/Official_Comment')
        assert invitation.invitees == ['ICML.cc/2023/Conference', 'openreview.net/Support', 'ICML.cc/2023/Conference/Submission1/Ethics_Reviewers', 'ICML.cc/2023/Conference/Ethics_Chairs']

        # post ethics review
        openreview_client.add_members_to_group('ICML.cc/2023/Conference/Submission5/Ethics_Reviewers', '~Reviewer_ICMLOne1')
        reviewer_client = openreview.api.OpenReviewClient(username='reviewer1@icml.cc', password=helpers.strong_password)

        anon_groups = reviewer_client.get_groups(prefix='ICML.cc/2023/Conference/Submission5/Ethics_Reviewer_', signatory='~Reviewer_ICMLOne1')
        anon_group_id = anon_groups[0].id

        review_edit = reviewer_client.post_note_edit(
            invitation='ICML.cc/2023/Conference/Submission5/-/Ethics_Review',
            signatures=[anon_group_id],
            note=openreview.api.Note(
                content={
                    "recommendation": {
                        "value": "1: No serious ethical issues"
                    },
                    "ethics_concerns": {
                        "value": "I have no concerns."
                    }
                }
            )
        )

        helpers.await_queue_edit(openreview_client, edit_id=review_edit['id'])

        reviews = pc_client_v2.get_notes(invitation='ICML.cc/2023/Conference/Submission5/-/Ethics_Review')
        assert len(reviews) == 1
        assert reviews[0].readers == [
            'ICML.cc/2023/Conference/Program_Chairs',
            'ICML.cc/2023/Conference/Ethics_Chairs',
            reviews[0].signatures[0]
        ]

        # Set expiration date
        start_date = now - datetime.timedelta(days=2)
        due_date = now - datetime.timedelta(days=1)
        exp_date = now
        stage_note = pc_client.post_note(openreview.Note(
            content={
                'ethics_review_start_date': start_date.strftime('%Y/%m/%d'),
                'ethics_review_deadline': due_date.strftime('%Y/%m/%d'),
                'ethics_review_expiration_date': exp_date.strftime('%Y/%m/%d'),
                'make_ethics_reviews_public': 'No, ethics reviews should NOT be revealed publicly when they are posted',
                'release_ethics_reviews_to_authors': "No, ethics reviews should NOT be revealed when they are posted to the paper\'s authors",
                'release_ethics_reviews_to_reviewers': 'Ethics Review should not be revealed to any reviewer, except to the author of the ethics review',
                'remove_ethics_review_form_options': 'ethics_review',
                'additional_ethics_review_form_options': {
                    "ethics_concerns": {
                        'order': 1,
                        'description': 'Briefly summarize the ethics concerns.',
                        'value': {
                            'param': {
                                'type': 'string',
                                'maxLength': 200000,
                                'markdown': True,
                                'input': 'textarea'
                            }
                        }
                    }
                },
                'release_submissions_to_ethics_reviewers': 'We confirm we want to release the submissions and reviews to the ethics reviewers'
            },
            forum=request_form.forum,
            referent=request_form.forum,
            invitation='openreview.net/Support/-/Request{}/Ethics_Review_Stage'.format(request_form.number),
            readers=['ICML.cc/2023/Conference/Program_Chairs', 'openreview.net/Support'],
            signatures=['~Program_ICMLChair1'],
            writers=[]
        ))

        helpers.await_queue()

        helpers.await_queue_edit(openreview_client, 'ICML.cc/2023/Conference/-/Ethics_Review-0-1', count=3)

        helpers.await_queue_edit(openreview_client, 'ICML.cc/2023/Conference/-/Official_Comment-0-1', count=2)

        # attempt to post another note
        openreview_client.add_members_to_group('ICML.cc/2023/Conference/Submission5/Ethics_Reviewers', '~Reviewer_ICMLTwo1')
        reviewer_client = openreview.api.OpenReviewClient(username='reviewer2@icml.cc', password=helpers.strong_password)
        anon_groups = reviewer_client.get_groups(prefix='ICML.cc/2023/Conference/Submission5/Ethics_Reviewer_', signatory='~Reviewer_ICMLTwo1')
        anon_group_id = anon_groups[0].id

        with pytest.raises(openreview.OpenReviewException, match=r'The Invitation ICML.cc/2023/Conference/Submission5/-/Ethics_Review has expired'):
            review_edit = reviewer_client.post_note_edit(
                invitation='ICML.cc/2023/Conference/Submission5/-/Ethics_Review',
                signatures=[anon_group_id],
                note=openreview.api.Note(
                    content={
                        "recommendation": {
                            "value": "1: No serious ethical issues"
                        },
                        "ethics_concerns": {
                            "value": "I have very serious concerns."
                        }
                    }
                )
            )

        # assert number of Official_Review and Position_Paper_Review invitations has not changed after flagging papers for ethics reviews
        assert len(openreview_client.get_invitations(invitation='ICML.cc/2023/Conference/-/Official_Review')) == 50
        assert len(openreview_client.get_invitations(invitation='ICML.cc/2023/Conference/-/Position_Paper_Review')) == 50

    def test_comment_stage(self, openreview_client, helpers):

        pc_client=openreview.Client(username='pc@icml.cc', password=helpers.strong_password)
        request_form=pc_client.get_notes(invitation='openreview.net/Support/-/Request_Form')[0]

        # Post an official comment stage note
        now = datetime.datetime.now()
        start_date = now - datetime.timedelta(days=2)
        end_date = now + datetime.timedelta(days=3)
        comment_stage_note = pc_client.post_note(openreview.Note(
            content={
                'commentary_start_date': start_date.strftime('%Y/%m/%d'),
                'commentary_end_date': end_date.strftime('%Y/%m/%d'),
                'participants': ['Program Chairs', 'Assigned Senior Area Chairs', 'Assigned Area Chairs', 'Assigned Reviewers'],
                'additional_readers': ['Program Chairs', 'Assigned Senior Area Chairs', 'Assigned Area Chairs', 'Assigned Reviewers', 'Assigned Submitted Reviewers'],
                'email_program_chairs_about_official_comments': 'No, do not email PCs for each official comment made in the venue',
                'enable_chat_between_committee_members': 'Yes, enable chat between committee members'
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
        helpers.await_queue_edit(openreview_client, 'ICML.cc/2023/Conference/-/Official_Comment-0-1', count=3)
        helpers.await_queue_edit(openreview_client, 'ICML.cc/2023/Conference/-/Chat-0-1', count=1)
        helpers.await_queue_edit(openreview_client, 'ICML.cc/2023/Conference/-/Chat_Reaction-0-1', count=1)

        chat_invitations = openreview_client.get_invitations(invitation='ICML.cc/2023/Conference/-/Chat')
        assert len(chat_invitations) == 100

        chat_reaction_invitations = openreview_client.get_invitations(invitation='ICML.cc/2023/Conference/-/Chat_Reaction')
        assert len(chat_reaction_invitations) == 100        
        
        invitation = openreview_client.get_invitation('ICML.cc/2023/Conference/Submission1/-/Official_Comment')
        assert invitation
        assert 'ICML.cc/2023/Conference/Submission1/Ethics_Reviewers' in invitation.invitees
        assert 'ICML.cc/2023/Conference/Submission1/Ethics_Reviewers' in invitation.edit['note']['readers']['param']['enum']
        assert invitation.edit['signatures']['param']['items'] == [
            {
            "value": "ICML.cc/2023/Conference/Program_Chairs",
            "optional": True
            },
            {
            "value": "ICML.cc/2023/Conference/Submission1/Senior_Area_Chairs",
            "optional": True
            },
            {
            "prefix": "ICML.cc/2023/Conference/Submission1/Area_Chair_.*",
            "optional": True
            },
            {
            "prefix": "ICML.cc/2023/Conference/Submission1/Reviewer_.*",
            "optional": True
            },
            {
            "prefix": "ICML.cc/2023/Conference/Submission1/Ethics_Reviewer_.*",
            "optional": True
            },
            {
            "value": "ICML.cc/2023/Conference/Ethics_Chairs",
            "optional": True
            }
        ]
        invitation = openreview_client.get_invitation('ICML.cc/2023/Conference/Submission2/-/Official_Comment')
        assert invitation
        assert 'ICML.cc/2023/Conference/Submission2/Ethics_Reviewers' not in invitation.edit['note']['readers']['param']['enum']
        assert openreview_client.get_invitation('ICML.cc/2023/Conference/Submission3/-/Official_Comment')
        assert openreview_client.get_invitation('ICML.cc/2023/Conference/Submission4/-/Official_Comment')
        invitation = openreview_client.get_invitation('ICML.cc/2023/Conference/Submission5/-/Official_Comment')
        assert invitation        
        assert 'ICML.cc/2023/Conference/Submission5/Ethics_Reviewers' in invitation.invitees
        assert 'ICML.cc/2023/Conference/Submission5/Ethics_Reviewers' in invitation.edit['note']['readers']['param']['enum']
        
        assert invitation.edit['signatures']['param']['items'] == [
            {
            "value": "ICML.cc/2023/Conference/Program_Chairs",
            "optional": True
            },
            {
            "value": "ICML.cc/2023/Conference/Submission5/Senior_Area_Chairs",
            "optional": True
            },
            {
            "prefix": "ICML.cc/2023/Conference/Submission5/Area_Chair_.*",
            "optional": True
            },
            {
            "prefix": "ICML.cc/2023/Conference/Submission5/Reviewer_.*",
            "optional": True
            },
            {
            "prefix": "ICML.cc/2023/Conference/Submission5/Ethics_Reviewer_.*",
            "optional": True
            },
            {
            "value": "ICML.cc/2023/Conference/Ethics_Chairs",
            "optional": True
            }
        ]
        
        pc_client_v2=openreview.api.OpenReviewClient(username='pc@icml.cc', password=helpers.strong_password)
        # unflag a paper
        note = openreview_client.get_notes(invitation='ICML.cc/2023/Conference/-/Submission', number=[5])[0]
        note_edit = pc_client_v2.post_note_edit(
            invitation='ICML.cc/2023/Conference/-/Ethics_Review_Flag',
            note=openreview.api.Note(
                id=note.id,
                content = {
                    'flagged_for_ethics_review': { 'value': False },
                }
            ),
            signatures=['ICML.cc/2023/Conference']
        )

        helpers.await_queue()
        helpers.await_queue_edit(openreview_client, edit_id=note_edit['id'])

        invitation = openreview_client.get_invitation('ICML.cc/2023/Conference/Submission5/-/Official_Comment')
        assert invitation        
        assert 'ICML.cc/2023/Conference/Submission5/Ethics_Reviewers' not in invitation.invitees
        assert 'ICML.cc/2023/Conference/Submission5/Ethics_Reviewers' in invitation.edit['note']['readers']['param']['enum']
        assert invitation.edit['signatures']['param']['items'] == [
            {
            "value": "ICML.cc/2023/Conference/Program_Chairs",
            "optional": True
            },
            {
            "value": "ICML.cc/2023/Conference/Submission5/Senior_Area_Chairs",
            "optional": True
            },
            {
            "prefix": "ICML.cc/2023/Conference/Submission5/Area_Chair_.*",
            "optional": True
            },
            {
            "prefix": "ICML.cc/2023/Conference/Submission5/Reviewer_.*",
            "optional": True
            },
            {
            "prefix": "ICML.cc/2023/Conference/Submission5/Ethics_Reviewer_.*",
            "optional": True
            },
            {
            "value": "ICML.cc/2023/Conference/Ethics_Chairs",
            "optional": True
            }
        ]
        submissions = openreview_client.get_notes(content= { 'venueid': 'ICML.cc/2023/Conference/Submission'}, sort='number:asc')
        assert submissions and len(submissions) == 100
        assert 'flagged_for_ethics_review' in submissions[4].content and not submissions[4].content['flagged_for_ethics_review']['value']
        invitation = openreview_client.get_invitations(id='ICML.cc/2023/Conference/Submission5/-/Ethics_Review')[0]
        assert invitation.expdate < openreview.tools.datetime_millis(datetime.datetime.now())
        ethics_group = openreview_client.get_group('ICML.cc/2023/Conference/Submission5/Ethics_Reviewers')
        assert ethics_group and '~Celeste_ICML1' in ethics_group.members

        reviewer_client = openreview.api.OpenReviewClient(username='reviewer1@icml.cc', password=helpers.strong_password)

        submissions = reviewer_client.get_notes(invitation='ICML.cc/2023/Conference/-/Submission', sort='number:asc')

        anon_groups = reviewer_client.get_groups(prefix='ICML.cc/2023/Conference/Submission1/Reviewer_', signatory='~Reviewer_ICMLOne1')
        anon_group_id = anon_groups[0].id

        comment_edit = reviewer_client.post_note_edit(
            invitation='ICML.cc/2023/Conference/Submission1/-/Official_Comment',
            signatures=[anon_group_id],
            note=openreview.api.Note(
                replyto = submissions[0].id,
                readers = [
                    'ICML.cc/2023/Conference/Program_Chairs',
                    'ICML.cc/2023/Conference/Submission1/Senior_Area_Chairs',
                    'ICML.cc/2023/Conference/Submission1/Area_Chairs',
                    anon_group_id,
                    'ICML.cc/2023/Conference/Submission1/Ethics_Reviewers'
                ],
                content={
                    'comment': { 'value': 'I can not review this paper' },
                }
            )
        )

        helpers.await_queue_edit(openreview_client, edit_id=comment_edit['id'])

        signature = anon_group_id.split('/')[-1]
        pretty_signature = openreview.tools.pretty_id(signature)
        messages = openreview_client.get_messages(to='ac2@icml.cc', subject=f'[ICML 2023] {pretty_signature} commented on a paper in your area. Paper Number: 1, Paper Title: "Paper title 1 Version 2"')
        assert messages and len(messages) == 1
        assert messages[0]['content']['replyTo'] == 'pc@icml.cc'

        messages = openreview_client.get_messages(to='reviewer1@icml.cc', subject='[ICML 2023] Your comment was received on Paper Number: 1, Paper Title: "Paper title 1 Version 2"')
        assert messages and len(messages) == 1
        assert messages[0]['content']['replyTo'] == 'pc@icml.cc'

        comment_edit = reviewer_client.post_note_edit(
            invitation='ICML.cc/2023/Conference/Submission1/-/Official_Comment',
            signatures=[anon_group_id],
            note=openreview.api.Note(
                id = comment_edit['note']['id'],
                replyto = submissions[0].id,
                readers = [
                    'ICML.cc/2023/Conference/Program_Chairs',
                    'ICML.cc/2023/Conference/Submission1/Senior_Area_Chairs',
                    'ICML.cc/2023/Conference/Submission1/Area_Chairs',
                    anon_group_id,
                    'ICML.cc/2023/Conference/Submission1/Ethics_Reviewers'
                ],
                content={
                    'comment': { 'value': 'I can not review this paper, EDITED' },
                }
            )
        )

        helpers.await_queue_edit(openreview_client, edit_id=comment_edit['id'])

        messages = openreview_client.get_messages(to='ac2@icml.cc', subject=f'[ICML 2023] {pretty_signature} commented on a paper in your area. Paper Number: 1, Paper Title: "Paper title 1 Version 2"')
        assert messages and len(messages) == 1

        messages = openreview_client.get_messages(to='reviewer1@icml.cc', subject='[ICML 2023] Your comment was received on Paper Number: 1, Paper Title: "Paper title 1 Version 2"')
        assert messages and len(messages) == 1

        comment_edit = reviewer_client.post_note_edit(
            invitation='ICML.cc/2023/Conference/Submission1/-/Official_Comment',
            signatures=[anon_group_id],
            note=openreview.api.Note(
                replyto = submissions[0].id,
                readers = [
                    'ICML.cc/2023/Conference/Program_Chairs',
                    'ICML.cc/2023/Conference/Submission1/Senior_Area_Chairs',
                    anon_group_id
                ],
                content={
                    'comment': { 'value': 'private message to SAC' },
                }
            )
        )

        helpers.await_queue_edit(openreview_client, edit_id=comment_edit['id'])

        messages = openreview_client.get_messages(to='ac2@icml.cc', subject=f'[ICML 2023] {pretty_signature} commented on a paper in your area. Paper Number: 1, Paper Title: "Paper title 1 Version 2"')
        assert messages and len(messages) == 1

        messages = openreview_client.get_messages(to='sac2@icml.cc', subject=f'[ICML 2023] {pretty_signature} commented on a paper in your area. Paper Number: 1, Paper Title: "Paper title 1 Version 2"')
        assert messages and len(messages) == 1

        messages = openreview_client.get_messages(to='reviewer1@icml.cc', subject='[ICML 2023] Your comment was received on Paper Number: 1, Paper Title: "Paper title 1 Version 2"')
        assert messages and len(messages) == 2

        # Enable Author-AC confidential comments
        venue = openreview.helpers.get_conference(pc_client, request_form.id, setup=False)
        now = datetime.datetime.now()
        start_date = now - datetime.timedelta(days=2)
        end_date = now + datetime.timedelta(days=3)

        venue.custom_stage = openreview.stages.CustomStage(name='Author_AC_Confidential_Comment',
            notify_readers=True,
            reply_to=openreview.stages.CustomStage.ReplyTo.WITHFORUM,
            source=openreview.stages.CustomStage.Source.ALL_SUBMISSIONS,
            reply_type=openreview.stages.CustomStage.ReplyType.REPLY,
            invitees=[openreview.stages.CustomStage.Participants.AUTHORS, openreview.stages.CustomStage.Participants.AREA_CHAIRS_ASSIGNED],
            readers=[openreview.stages.CustomStage.Participants.SENIOR_AREA_CHAIRS_ASSIGNED,openreview.stages.CustomStage.Participants.AREA_CHAIRS_ASSIGNED,openreview.stages.CustomStage.Participants.AUTHORS],
            start_date=start_date,
            due_date=end_date,
            content={
                'title': {
                    'order': 1,
                    'description': '(Optional) Brief summary of your comment.',
                    'value': {
                        'param': {
                            'type': 'string',
                            'maxLength': 500,
                            'optional': True,
                            'deletable': True
                        }
                    }
                },
                'comment': {
                    'order': 2,
                    'description': 'Your comment or reply (max 5000 characters). Add formatting using Markdown and formulas using LaTeX. For more information see https://openreview.net/faq',
                    'value': {
                        'param': {
                            'type': 'string',
                            'maxLength': 5000,
                            'markdown': True,
                            'input': 'textarea'
                        }
                    }
                }
            },
            multi_reply=True
        )
        venue.create_custom_stage()
        helpers.await_queue_edit(openreview_client, 'ICML.cc/2023/Conference/-/Author_AC_Confidential_Comment-0-1', count=1)

        assert len(openreview_client.get_invitations(invitation='ICML.cc/2023/Conference/-/Author_AC_Confidential_Comment')) == 100
        invitation = openreview_client.get_invitation('ICML.cc/2023/Conference/Submission1/-/Author_AC_Confidential_Comment')
        assert invitation.invitees == [
            'ICML.cc/2023/Conference',
            'ICML.cc/2023/Conference/Submission1/Area_Chairs',
            'ICML.cc/2023/Conference/Submission1/Authors'
        ]

        author_client = openreview.api.OpenReviewClient(username='peter@mail.com', password=helpers.strong_password)
        confidential_comment_edit = author_client.post_note_edit(
            invitation='ICML.cc/2023/Conference/Submission1/-/Author_AC_Confidential_Comment',
            signatures=['ICML.cc/2023/Conference/Submission1/Authors'],
            note=openreview.api.Note(
                replyto=submissions[0].id,
                content={
                    'comment': { 'value': 'Author confidential comment to AC' },
                }
            )
        )
        helpers.await_queue_edit(openreview_client, edit_id=confidential_comment_edit['id'])

        confidential_comment = openreview_client.get_notes(invitation='ICML.cc/2023/Conference/Submission1/-/Author_AC_Confidential_Comment')[0]
        assert confidential_comment.readers == [
            'ICML.cc/2023/Conference/Program_Chairs',
            'ICML.cc/2023/Conference/Submission1/Senior_Area_Chairs',
            'ICML.cc/2023/Conference/Submission1/Area_Chairs',
            'ICML.cc/2023/Conference/Submission1/Authors'
        ]

        # Check messages sent to readers
        messages = openreview_client.get_messages(subject = '[ICML 2023] An author ac confidential comment has been received on your.*')
        assert messages and len(messages) == 5
        recipients = [msg['content']['to'] for msg in messages]
        assert 'test@mail.com'in recipients
        assert 'andrew@amazon.com' in recipients
        assert 'sac1@gmail.com' in recipients
        assert 'melisa@yahoo.com' in recipients
        assert 'ac2@icml.cc' in recipients
        assert 'peter@mail.com' not in recipients

        ac_client = openreview.api.OpenReviewClient(username='ac2@icml.cc', password=helpers.strong_password)
        anon_groups = ac_client.get_groups(prefix='ICML.cc/2023/Conference/Submission1/Area_Chair_', signatory='~AC_ICMLTwo1')
        anon_group_id = anon_groups[0].id

        confidential_comment_edit = ac_client.post_note_edit(
            invitation='ICML.cc/2023/Conference/Submission1/-/Author_AC_Confidential_Comment',
            signatures=[anon_group_id],
            note=openreview.api.Note(
                replyto=confidential_comment.id,
                content={
                    'comment': { 'value': 'AC confidential reply to Author' },
                }
            )
        )
        helpers.await_queue_edit(openreview_client, edit_id=confidential_comment_edit['id'])

        messages = openreview_client.get_messages(subject = '[ICML 2023] An author ac confidential comment has been received on your.*')
        assert messages and len(messages) == 10
        recipients = [msg['content']['to'] for msg in messages]
        assert 'peter@mail.com' in recipients

        messages = openreview_client.get_messages(to='peter@mail.com', subject = '[ICML 2023] An author ac confidential comment has been received on your.*')
        assert messages[0]['content']['text'].startswith('We have received an author ac confidential comment on your submission to ICML 2023.')

    def test_rebuttal_stage(self, client, openreview_client, helpers):

        pc_client=openreview.Client(username='pc@icml.cc', password=helpers.strong_password)
        request_form=pc_client.get_notes(invitation='openreview.net/Support/-/Request_Form')[0]

        now = datetime.datetime.now()

        # create rebuttal stage in request form
        client.post_invitation(openreview.Invitation(
                    id = f'openreview.net/Support/-/Request{request_form.number}/Rebuttal_Stage',
                    super = 'openreview.net/Support/-/Rebuttal_Stage',
                    invitees = ['ICML.cc/2023/Conference/Program_Chairs', 'openreview.net/Support'],
                    cdate = openreview.tools.datetime_millis(now),
                    reply = {
                        'forum': request_form.id,
                        'referent': request_form.id,
                        'readers': {
                            'description': 'The users who will be allowed to read the above content.',
                            'values' : ['ICML.cc/2023/Conference/Program_Chairs', 'openreview.net/Support']
                        }
                    },
                    signatures = ['~Super_User1']
                ))

        # release only reviews for non position papers
        venue = openreview.helpers.get_conference(client, request_form.id, setup=False)
        venue.review_stage = openreview.stages.ReviewStage(
            start_date = now - datetime.timedelta(days=10),
            due_date = now - datetime.timedelta(days=3),
            release_to_authors=True,
            release_to_reviewers=openreview.stages.ReviewStage.Readers.REVIEWERS_SUBMITTED,
            additional_fields={
                "summary": {
                    "order": 1,
                    "description": "Briefly summarize the paper and its contributions. This is not the place to critique the paper; the authors should generally agree with a well-written summary.",
                    "value": {
                        "param": {
                            "maxLength": 200000,
                            "type": "string",
                            "input": "textarea",
                            "markdown": True
                        }
                    }
                },
                "strengths_and_weaknesses": {
                    "order": 2,
                    "description": "Please provide a thorough assessment of the strengths and weaknesses of the paper, touching on each of the following dimensions: originality, quality, clarity, and significance. We encourage people to be broad in their definitions of originality and significance. For example, originality may arise from creative combinations of existing ideas, application to a new domain, or removing restrictive assumptions from prior theoretical results. You can incorporate Markdown and Latex into your review. See https://openreview.net/faq.",
                    "value": {
                        "param": {
                            "maxLength": 200000,
                            "type": "string",
                            "input": "textarea",
                            "markdown": True
                        }
                    }
                },
                "questions": {
                    "order": 3,
                    "description": "Please list up and carefully describe any questions and suggestions for the authors. Think of the things where a response from the author can change your opinion, clarify a confusion or address a limitation. This can be very important for a productive rebuttal and discussion phase with the authors.",
                    "value": {
                        "param": {
                            "maxLength": 200000,
                            "type": "string",
                            "input": "textarea",
                            "markdown": True
                        }
                    }
                },
                "limitations": {
                    "order": 4,
                    "description": "Have the authors adequately addressed the limitations and potential negative societal impact of their work? If not, please include constructive suggestions for improvement. Authors should be rewarded rather than punished for being up front about the limitations of their work and any potential negative societal impact.",
                    "value": {
                        "param": {
                            "maxLength": 200000,
                            "type": "string",
                            "input": "textarea",
                            "markdown": True
                        }
                    }
                },
                "ethics_flag": {
                    "order": 5,
                    "description": "If there are ethical issues with this paper, please flag the paper for an ethics review. For guidance on when this is appropriate, please review the ethics guidelines (https://icml.cc/Conferences/2023/PublicationEthics).",
                    "value": {
                        "param": {
                            "type": "string",
                            "enum": [
                                "Yes",
                                "No"
                            ],
                            "input": "radio"
                        }
                    }
                },
                "ethics_review_area": {
                    "order": 6,
                    "description": "If you flagged this paper for ethics review, what area of expertise would it be most useful for the ethics reviewer to have? Please click all that apply.",
                    "value": {
                        "param": {
                            "type": "string[]",
                            "enum": [
                                "Discrimination / Bias / Fairness Concerns",
                                "Inadequate Data and Algorithm Evaluation",
                                "Inappropriate Potential Applications & Impact  (e.g., human rights concerns)",
                                "Privacy and Security (e.g., consent)",
                                "Legal Compliance (e.g., GDPR, copyright, terms of use)",
                                "Research Integrity Issues (e.g., plagiarism)",
                                "Responsible Research Practice (e.g., IRB, documentation, research ethics)",
                                "I don't know"
                            ],
                            "input": "checkbox",
                            "optional": True,
                        }
                    }
                },
                "soundness": {
                    "order": 7,
                    "description": "Please assign the paper a numerical rating on the following scale to indicate the soundness of the technical claims, experimental and research methodology and on whether the central claims of the paper are adequately supported with evidence.",
                    "value": {
                        "param": {
                            "type": "string",
                            "enum": [
                                "4 excellent",
                                "3 good",
                                "2 fair",
                                "1 poor"
                            ],
                            "input": "radio"
                        }
                    }
                },
                "presentation": {
                    "order": 8,
                    "description": "Please assign the paper a numerical rating on the following scale to indicate the quality of the presentation. This should take into account the writing style and clarity, as well as contextualization relative to prior work.",
                    "value": {
                        "param": {
                            "type": "string",
                            "enum": [
                                "4 excellent",
                                "3 good",
                                "2 fair",
                                "1 poor"
                            ],
                            "input": "radio"
                        }
                    }
                },
                "contribution": {
                    "order": 9,
                    "description": "Please assign the paper a numerical rating on the following scale to indicate the quality of the overall contribution this paper makes to the research area being studied. Are the questions being asked important? Does the paper bring a significant originality of ideas and/or execution? Are the results valuable to share with the broader ICML community?",
                    "value": {
                        "param": {
                            "type": "string",
                            "enum": [
                                "4 excellent",
                                "3 good",
                                "2 fair",
                                "1 poor"
                            ],
                            "input": "radio"
                        }
                    }
                },
                "rating": {
                    "order": 10,
                    "description": "Please provide an \"overall score\" for this submission.",
                    "value": {
                        "param": {
                            "type": 'integer',
                            "enum": [
                                { 'value': 10, 'description': "10: Award quality: Technically flawless paper with groundbreaking impact, with exceptionally strong evaluation, reproducibility, and resources, and no unaddressed ethical considerations." },
                                { 'value': 9, 'description': "9: Very Strong Accept: Technically flawless paper with groundbreaking impact on at least one area of AI/ML and excellent impact on multiple areas of AI/ML, with flawless evaluation, resources, and reproducibility, and no unaddressed ethical considerations." },
                                { 'value': 8, 'description': "8: Strong Accept: Technically strong paper, with novel ideas, excellent impact on at least one area, or high-to-excellent impact on multiple areas, with excellent evaluation, resources, and reproducibility, and no unaddressed ethical considerations." },
                                { 'value': 7, 'description': "7: Accept: Technically solid paper, with high impact on at least one sub-area, or moderate-to-high impact on more than one areas, with good-to-excellent evaluation, resources, reproducibility, and no unaddressed ethical considerations." },
                                { 'value': 6, 'description': "6: Weak Accept: Technically solid, moderate-to-high impact paper, with no major concerns with respect to evaluation, resources, reproducibility, ethical considerations." },
                                { 'value': 5, 'description': "5: Borderline accept: Technically solid paper where reasons to accept outweigh reasons to reject, e.g., limited evaluation. Please use sparingly." },
                                { 'value': 4, 'description': "4: Borderline reject: Technically solid paper where reasons to reject, e.g., limited evaluation, outweigh reasons to accept, e.g., good evaluation. Please use sparingly." },
                                { 'value': 3, 'description': "3: Reject: For instance, a paper with technical flaws, weak evaluation, inadequate reproducibility and incompletely addressed ethical considerations." },
                                { 'value': 2, 'description': "2: Strong Reject: For instance, a paper with major technical flaws, and/or poor evaluation, limited impact, poor reproducibility and mostly unaddressed ethical considerations." },
                                { 'value': 1, 'description': "1: Very Strong Reject: For instance, a paper with trivial results or unaddressed ethical considerations" }
                            ],
                            "input": "radio"

                        }
                    }
                },
                "confidence": {
                    "order": 11,
                    "description": "Please provide a \"confidence score\" for your assessment of this submission to indicate how confident you are in your evaluation.",
                    "value": {
                        "param": {
                            "type": 'integer',
                            "enum": [
                                { 'value': 5, 'description': "5: You are absolutely certain about your assessment. You are very familiar with the related work and checked the math/other details carefully." },
                                { 'value': 4, 'description': "4: You are confident in your assessment, but not absolutely certain. It is unlikely, but not impossible, that you did not understand some parts of the submission or that you are unfamiliar with some pieces of related work." },
                                { 'value': 3, 'description': "3: You are fairly confident in your assessment. It is possible that you did not understand some parts of the submission or that you are unfamiliar with some pieces of related work. Math/other details were not carefully checked." },
                                { 'value': 2, 'description': "2: You are willing to defend your assessment, but it is quite likely that you did not understand the central parts of the submission or that you are unfamiliar with some pieces of related work. Math/other details were not carefully checked." },
                                { 'value': 1, 'description': "1: Your assessment is an educated guess. The submission is not in your area or the submission was difficult to understand. Math/other details were not carefully checked." }
                            ],
                            "input": "radio"
                        }
                    }
                },
                "code_of_conduct": {
                    "description": "While performing my duties as a reviewer (including writing reviews and participating in discussions), I have and will continue to abide by the ICML code of conduct (https://icml.cc/public/CodeOfConduct).",
                    "order": 12,
                    "value": {
                        "param": {
                            "type": "string",
                            "enum": ["Yes"],
                            "input": "checkbox"
                        }
                    }
                }
            },
            remove_fields=['title', 'review'],
            source_submissions_query={
                'position_paper_track': 'No'
            }
        )

        venue.create_review_stage()

        helpers.await_queue_edit(openreview_client, 'ICML.cc/2023/Conference/-/Official_Review-0-1', count=5)

        pc_client_v2=openreview.api.OpenReviewClient(username='pc@icml.cc', password=helpers.strong_password)

        # check reviews of a flagged paper is visible to ethics reviewers and authors
        reviews = pc_client_v2.get_notes(invitation='ICML.cc/2023/Conference/Submission1/-/Official_Review')
        assert len(reviews) == 2
        assert reviews[0].readers == [
            'ICML.cc/2023/Conference/Program_Chairs',
            'ICML.cc/2023/Conference/Submission1/Senior_Area_Chairs',
            'ICML.cc/2023/Conference/Submission1/Area_Chairs',
            'ICML.cc/2023/Conference/Submission1/Reviewers/Submitted',
            'ICML.cc/2023/Conference/Submission1/Authors',
            'ICML.cc/2023/Conference/Submission1/Ethics_Reviewers',
            reviews[0].signatures[0]
        ]

        # assert position papers' reviews are still hidden
        reviews = pc_client_v2.get_notes(invitation='ICML.cc/2023/Conference/Submission2/-/Official_Review')
        assert len(reviews) == 1
        assert reviews[0].readers == [
            'ICML.cc/2023/Conference/Program_Chairs',
            'ICML.cc/2023/Conference/Submission2/Senior_Area_Chairs',
            'ICML.cc/2023/Conference/Submission2/Area_Chairs',
            reviews[0].signatures[0]
        ]

        # release position paper reviews
        venue.review_stage = openreview.stages.ReviewStage(
            start_date=now - datetime.timedelta(days=10),
            due_date=now - datetime.timedelta(days=3),
            release_to_authors=True,
            release_to_reviewers=openreview.stages.ReviewStage.Readers.REVIEWERS_SUBMITTED,
            name='Position_Paper_Review',
            remove_fields=['title'],
            source_submissions_query={
                'position_paper_track': 'Yes'
            }
        )

        venue.create_review_stage()

        helpers.await_queue_edit(openreview_client, 'ICML.cc/2023/Conference/-/Position_Paper_Review-0-1', count=4)

        # check reviews of a non-flagged paper is not visible to ethics reviewers but it visible to authors
        reviews = pc_client_v2.get_notes(invitation='ICML.cc/2023/Conference/Submission2/-/Official_Review')
        assert len(reviews) == 1
        assert reviews[0].readers == [
            'ICML.cc/2023/Conference/Program_Chairs',
            'ICML.cc/2023/Conference/Submission2/Senior_Area_Chairs',
            'ICML.cc/2023/Conference/Submission2/Area_Chairs',
            'ICML.cc/2023/Conference/Submission2/Reviewers/Submitted',
            'ICML.cc/2023/Conference/Submission2/Authors',
            reviews[0].signatures[0]
        ]
        edits = openreview_client.get_note_edits(note_id=reviews[0].id)
        for edit in edits:
            assert edit.readers == edit.note.readers
            assert '${2/note/readers}' not in edit.readers

        now = datetime.datetime.now()
        start_date = now - datetime.timedelta(days=2)
        end_date = now + datetime.timedelta(days=3)
        comment_stage_note = pc_client.post_note(openreview.Note(
            content={
                'commentary_start_date': start_date.strftime('%Y/%m/%d'),
                'commentary_end_date': end_date.strftime('%Y/%m/%d'),
                'participants': ['Program Chairs', 'Assigned Senior Area Chairs', 'Assigned Area Chairs', 'Assigned Reviewers', 'Authors'],
                'additional_readers': ['Program Chairs', 'Assigned Senior Area Chairs', 'Assigned Area Chairs', 'Assigned Reviewers', 'Assigned Submitted Reviewers', 'Authors'],
                'email_program_chairs_about_official_comments': 'No, do not email PCs for each official comment made in the venue'

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

        helpers.await_queue_edit(openreview_client, 'ICML.cc/2023/Conference/-/Official_Comment-0-1', count=4)

        test_client = openreview.api.OpenReviewClient(username='test@mail.com', password=helpers.strong_password)

        reviews = pc_client_v2.get_notes(invitation='ICML.cc/2023/Conference/Submission1/-/Official_Review')
        comment_edit = test_client.post_note_edit(
            invitation='ICML.cc/2023/Conference/Submission1/-/Official_Comment',
            signatures=['ICML.cc/2023/Conference/Submission1/Authors'],
            note=openreview.api.Note(
                replyto = reviews[0].id,
                readers = [
                    'ICML.cc/2023/Conference/Program_Chairs',
                    'ICML.cc/2023/Conference/Submission1/Senior_Area_Chairs',
                    'ICML.cc/2023/Conference/Submission1/Area_Chairs',
                    'ICML.cc/2023/Conference/Submission1/Reviewers/Submitted',
                ],
                content={
                    'comment': { 'value': 'Thanks for your review!!!' },
                }
            )
        )

        helpers.await_queue_edit(openreview_client, edit_id=comment_edit['id'])

        # post a rebuttal stage note, rebuttal stage button should be active already
        now = datetime.datetime.now()
        start_date = now - datetime.timedelta(days=2)
        due_date = now + datetime.timedelta(days=3)
        pc_client.post_note(openreview.Note(
            content={
                'rebuttal_start_date': start_date.strftime('%Y/%m/%d'),
                'rebuttal_deadline': due_date.strftime('%Y/%m/%d'),
                'number_of_rebuttals': 'Multiple author rebuttals per paper',
                'email_program_chairs_about_rebuttals': 'No, do not email program chairs about received rebuttals'
            },
            forum=request_form.forum,
            invitation=f'openreview.net/Support/-/Request{request_form.number}/Rebuttal_Stage',
            readers=['ICML.cc/2023/Conference/Program_Chairs', 'openreview.net/Support'],
            replyto=request_form.forum,
            referent=request_form.forum,
            signatures=['~Program_ICMLChair1'],
            writers=[]
        ))

        helpers.await_queue()

        helpers.await_queue_edit(openreview_client, 'ICML.cc/2023/Conference/-/Rebuttal-0-1', count=1)

        submissions = openreview_client.get_notes(invitation='ICML.cc/2023/Conference/-/Submission', sort='number:asc')

        assert len(openreview_client.get_invitations(invitation='ICML.cc/2023/Conference/-/Rebuttal')) == 100
        invitation = openreview_client.get_invitation('ICML.cc/2023/Conference/Submission1/-/Rebuttal')
        assert not invitation.maxReplies
        assert invitation.edit['note']['replyto'] == {
            'param': {
                    'withForum': f'{submissions[0].id}'
                }
        }

        test_client = openreview.api.OpenReviewClient(username='test@mail.com', password=helpers.strong_password)
        review = reviews[0]

        rebuttal_edit = test_client.post_note_edit(
            invitation='ICML.cc/2023/Conference/Submission1/-/Rebuttal',
            signatures=['ICML.cc/2023/Conference/Submission1/Authors'],
            note=openreview.api.Note(
                replyto = review.forum,
                content={
                    'rebuttal': { 'value': 'This is a rebuttal.' }
                }
            )
        )

        helpers.await_queue_edit(openreview_client, edit_id=rebuttal_edit['id'])

        second_rebuttal_edit = test_client.post_note_edit(
            invitation='ICML.cc/2023/Conference/Submission1/-/Rebuttal',
            signatures=['ICML.cc/2023/Conference/Submission1/Authors'],
            note=openreview.api.Note(
                replyto = reviews[0].id,
                content={
                    'rebuttal': { 'value': 'This is a rebuttal replying to a review.' },
                }
            )
        )

        helpers.await_queue_edit(openreview_client, edit_id=second_rebuttal_edit['id'])

        rebuttal_id = second_rebuttal_edit['note']['id']

        messages = openreview_client.get_messages(subject = '[ICML 2023] Your author rebuttal was posted on Submission Number: 1, Submission Title: "Paper title 1 Version 2"')
        assert len(messages) == 2
        assert 'test@mail.com' in messages[0]['content']['to']
        assert messages[0]['content']['replyTo'] == 'pc@icml.cc'
        messages = openreview_client.get_messages(subject = '[ICML 2023] An author rebuttal was posted on Submission Number: 1, Submission Title: "Paper title 1 Version 2"')
        assert len(messages) == 8
        assert f'https://openreview.net/forum?id={review.forum}&noteId={rebuttal_id}' in messages[4]['content']['text']
        recipients = [m['content']['to'] for m in messages]
        assert 'peter@mail.com' in recipients
        assert 'andrew@amazon.com' in recipients
        assert 'sac1@gmail.com' in recipients
        assert 'melisa@yahoo.com' in recipients

        #update rebuttal
        rebuttal_update = test_client.post_note_edit(
            invitation='ICML.cc/2023/Conference/Submission1/-/Rebuttal',
            signatures=['ICML.cc/2023/Conference/Submission1/Authors'],
            note=openreview.api.Note(
                id = rebuttal_id,
                replyto = reviews[0].id,
                content={
                    'rebuttal': { 'value': 'This is a rebuttal replying to a review UPDATED.' }
                }
            )
        )

        helpers.await_queue_edit(openreview_client, edit_id=rebuttal_update['id'])

        #check no new emails were sent
        messages = openreview_client.get_messages(subject = '[ICML 2023] Your author rebuttal was posted on Submission Number: 1, Submission Title: "Paper title 1 Version 2"')
        assert len(messages) == 2
        assert 'test@mail.com' in messages[0]['content']['to']
        messages = openreview_client.get_messages(subject = '[ICML 2023] An author rebuttal was posted on Submission Number: 1, Submission Title: "Paper title 1 Version 2"')
        assert len(messages) == 8

        rebuttals = pc_client_v2.get_notes(invitation='ICML.cc/2023/Conference/Submission1/-/Rebuttal')
        assert len(rebuttals) == 2
        assert rebuttals[0].readers == [
            'ICML.cc/2023/Conference/Program_Chairs',
            'ICML.cc/2023/Conference/Submission1/Authors',
        ]

        # flag a paper after reviews are released and assert readers are correct
        note = openreview_client.get_notes(invitation='ICML.cc/2023/Conference/-/Submission', number=[2])[0]
        note_edit = pc_client_v2.post_note_edit(
                invitation='ICML.cc/2023/Conference/-/Ethics_Review_Flag',
                note=openreview.api.Note(
                    id=note.id,
                    content = {
                        'flagged_for_ethics_review': { 'value': True },
                        'ethics_comments': { 'value': 'These are ethics comments visible to ethics chairs and ethics reviewers' }
                    }
                ),
                signatures=['ICML.cc/2023/Conference']
            )

        helpers.await_queue()
        helpers.await_queue_edit(openreview_client, edit_id=note_edit['id'])

        reviews = openreview_client.get_notes(invitation='ICML.cc/2023/Conference/Submission2/-/Official_Review')
        for review in reviews:
            assert review.readers == [
                'ICML.cc/2023/Conference/Program_Chairs',
                'ICML.cc/2023/Conference/Submission2/Senior_Area_Chairs',
                'ICML.cc/2023/Conference/Submission2/Area_Chairs',
                'ICML.cc/2023/Conference/Submission2/Reviewers/Submitted',
                'ICML.cc/2023/Conference/Submission2/Authors',
                'ICML.cc/2023/Conference/Submission2/Ethics_Reviewers',
                review.signatures[0]
            ]

    def test_release_rebuttals(self, client, openreview_client, helpers):

        pc_client=openreview.Client(username='pc@icml.cc', password=helpers.strong_password)
        pc_client_v2=openreview.api.OpenReviewClient(username='pc@icml.cc', password=helpers.strong_password)
        request_form=pc_client.get_notes(invitation='openreview.net/Support/-/Request_Form')[0]

        # post a rebuttal stage note
        now = datetime.datetime.now()
        start_date = now - datetime.timedelta(days=2)
        due_date = now + datetime.timedelta(days=3)
        pc_client.post_note(openreview.Note(
            content={
                'rebuttal_start_date': start_date.strftime('%Y/%m/%d'),
                'rebuttal_deadline': due_date.strftime('%Y/%m/%d'),
                'rebuttal_readers': ['Assigned Senior Area Chairs', 'Assigned Area Chairs', 'Assigned Reviewers who already submitted their review'],
                'number_of_rebuttals': 'Multiple author rebuttals per paper',
                'email_program_chairs_about_rebuttals': 'No, do not email program chairs about received rebuttals'
            },
            forum=request_form.forum,
            invitation=f'openreview.net/Support/-/Request{request_form.number}/Rebuttal_Stage',
            readers=['ICML.cc/2023/Conference/Program_Chairs', 'openreview.net/Support'],
            replyto=request_form.forum,
            referent=request_form.forum,
            signatures=['~Program_ICMLChair1'],
            writers=[]
        ))

        helpers.await_queue()

        helpers.await_queue_edit(openreview_client, 'ICML.cc/2023/Conference/-/Rebuttal-0-1', count=2)

        rebuttals = pc_client_v2.get_notes(invitation='ICML.cc/2023/Conference/Submission1/-/Rebuttal')
        assert len(rebuttals) == 2
        assert rebuttals[0].readers == [
            'ICML.cc/2023/Conference/Program_Chairs',
            'ICML.cc/2023/Conference/Submission1/Senior_Area_Chairs',
            'ICML.cc/2023/Conference/Submission1/Area_Chairs',
            'ICML.cc/2023/Conference/Submission1/Reviewers/Submitted',
            'ICML.cc/2023/Conference/Submission1/Authors',
        ]
        assert rebuttals[1].readers == [
            'ICML.cc/2023/Conference/Program_Chairs',
            'ICML.cc/2023/Conference/Submission1/Senior_Area_Chairs',
            'ICML.cc/2023/Conference/Submission1/Area_Chairs',
            'ICML.cc/2023/Conference/Submission1/Reviewers/Submitted',
            'ICML.cc/2023/Conference/Submission1/Authors',
        ]

        ## Ask reviewers to ACK the rebuttals
        venue = openreview.helpers.get_conference(client, request_form.id, setup=False)
        venue.custom_stage = openreview.stages.CustomStage(name='Rebuttal_Acknowledgement',
            reply_to=openreview.stages.CustomStage.ReplyTo.REBUTTALS,
            source=openreview.stages.CustomStage.Source.ALL_SUBMISSIONS,
            due_date=due_date,
            exp_date=due_date + datetime.timedelta(days=1),
            invitees=[openreview.stages.CustomStage.Participants.REPLYTO_REPLYTO_SIGNATURES],
            readers=[openreview.stages.CustomStage.Participants.REVIEWERS_SUBMITTED, openreview.stages.CustomStage.Participants.AUTHORS],
            content={
                'acknowledgement': {
                    'order': 1,
                    'description': "I acknowledge I read the rebuttal.",
                    'value': {
                        'param': {
                            'type': 'boolean',
                            'enum': [{ 'value': True, 'description': 'Yes, I acknowledge I read the rebuttal.' }],
                            'input': 'checkbox'
                        }
                    }
                }
            },
            notify_readers=True,
            email_sacs=False)

        venue.create_custom_stage()

        helpers.await_queue_edit(openreview_client, 'ICML.cc/2023/Conference/-/Rebuttal_Acknowledgement-0-1', count=1)

        ack_invitations = openreview_client.get_invitations(invitation='ICML.cc/2023/Conference/-/Rebuttal_Acknowledgement')
        assert len(ack_invitations) == 2


        ## Ask reviewers to comment the rebuttals
        venue = openreview.helpers.get_conference(client, request_form.id, setup=False)
        venue.custom_stage = openreview.stages.CustomStage(name='Rebuttal_Comment',
            reply_to=openreview.stages.CustomStage.ReplyTo.REBUTTALS,
            source=openreview.stages.CustomStage.Source.ALL_SUBMISSIONS,
            due_date=None,
            exp_date=due_date + datetime.timedelta(days=1),
            invitees=[openreview.stages.CustomStage.Participants.REPLYTO_REPLYTO_SIGNATURES],
            readers=[openreview.stages.CustomStage.Participants.REVIEWERS_SUBMITTED, openreview.stages.CustomStage.Participants.AUTHORS],
            content={
                "comment": {
                    "order": 2,
                    "description": "Leave a comment to the authors",
                    "value": {
                        "param": {
                            "maxLength": 5000,
                            "type": "string",
                            "input": "textarea",
                            "optional": True,
                            "deletable": True,
                            "markdown": True
                        }
                    }
                }
            },
            notify_readers=True,
            email_sacs=False)

        venue.create_custom_stage()

        helpers.await_queue_edit(openreview_client, 'ICML.cc/2023/Conference/-/Rebuttal_Comment-0-1', count=1)        

        assert len(openreview_client.get_invitations(invitation='ICML.cc/2023/Conference/-/Rebuttal_Comment')) == 2

        rebuttals = pc_client_v2.get_notes(invitation='ICML.cc/2023/Conference/Submission1/-/Rebuttal')
        assert len(rebuttals) == 2

        reviewer_client = openreview.api.OpenReviewClient(username='reviewer2@icml.cc', password=helpers.strong_password)

        anon_groups = reviewer_client.get_groups(prefix='ICML.cc/2023/Conference/Submission1/Reviewer_', signatory='~Reviewer_ICMLTwo1')
        anon_group_id = anon_groups[0].id

        assert anon_group_id in openreview_client.get_invitation('ICML.cc/2023/Conference/Submission1/Rebuttal2/-/Rebuttal_Acknowledgement').invitees

        rebuttal_ack1_edit = reviewer_client.post_note_edit(
            invitation='ICML.cc/2023/Conference/Submission1/Rebuttal2/-/Rebuttal_Acknowledgement',
            signatures=[anon_group_id],
            note=openreview.api.Note(
                content={
                    'acknowledgement': { 'value': True }
                }
            )
        )

        helpers.await_queue_edit(openreview_client, edit_id=rebuttal_ack1_edit['id'])

        messages = openreview_client.get_messages(to='reviewer2@icml.cc', subject='[ICML 2023] Your rebuttal acknowledgement has been received on Paper Number: 1, Paper Title: "Paper title 1 Version 2"')              
        assert len(messages) == 1

        messages = openreview_client.get_messages(to='test@mail.com', subject='[ICML 2023] A rebuttal acknowledgement has been received on your Paper Number: 1, Paper Title: "Paper title 1 Version 2"')
        assert len(messages) == 1

        assert anon_group_id in openreview_client.get_invitation('ICML.cc/2023/Conference/Submission1/Rebuttal2/-/Rebuttal_Comment').invitees
        
        rebuttal_edit = reviewer_client.post_note_edit(
            invitation='ICML.cc/2023/Conference/Submission1/Rebuttal2/-/Rebuttal_Comment',
            signatures=[anon_group_id],
            note=openreview.api.Note(
                content={
                    'comment': { 'value': 'Authors please change the PDF with the new changes that we discussed' }
                }
            )
        )

        helpers.await_queue_edit(openreview_client, edit_id=rebuttal_edit['id'])

        messages = openreview_client.get_messages(to='reviewer2@icml.cc', subject='[ICML 2023] Your rebuttal comment has been received on Paper Number: 1, Paper Title: "Paper title 1 Version 2"')              
        assert len(messages) == 1

        messages = openreview_client.get_messages(to='test@mail.com', subject='[ICML 2023] A rebuttal comment has been received on your Paper Number: 1, Paper Title: "Paper title 1 Version 2"')
        assert len(messages) == 1                

        ## Ask authors to reply to the ACK comments
        venue = openreview.helpers.get_conference(client, request_form.id, setup=False)
        venue.custom_stage = openreview.stages.CustomStage(name='Reply_Rebuttal_Comment',
            reply_to='Rebuttal_Comment',
            source=openreview.stages.CustomStage.Source.ALL_SUBMISSIONS,
            due_date=due_date,
            exp_date=due_date + datetime.timedelta(days=1),
            invitees=[openreview.stages.CustomStage.Participants.REPLYTO_REPLYTO_SIGNATURES],
            readers=[openreview.stages.CustomStage.Participants.REVIEWERS_SUBMITTED, openreview.stages.CustomStage.Participants.AUTHORS],
            content={
                "comment": {
                    "order": 2,
                    "description": "Leave a comment to the reviewers",
                    "value": {
                        "param": {
                            "maxLength": 5000,
                            "type": "string",
                            "input": "textarea",
                            "optional": True,
                            "deletable": True,
                            "markdown": True
                        }
                    }
                }
            },
            notify_readers=True,
            email_sacs=False)

        venue.create_custom_stage()

        helpers.await_queue_edit(openreview_client, 'ICML.cc/2023/Conference/-/Reply_Rebuttal_Comment-0-1', count=1)

        assert len(openreview_client.get_invitations(invitation='ICML.cc/2023/Conference/-/Reply_Rebuttal_Comment')) == 1

        assert 'ICML.cc/2023/Conference/Submission1/Authors' in openreview_client.get_invitation('ICML.cc/2023/Conference/Submission1/Rebuttal2/Rebuttal_Comment1/-/Reply_Rebuttal_Comment').invitees

        author_client = openreview.api.OpenReviewClient(username='test@mail.com', password=helpers.strong_password)

        rebuttal_edit = author_client.post_note_edit(
            invitation='ICML.cc/2023/Conference/Submission1/Rebuttal2/Rebuttal_Comment1/-/Reply_Rebuttal_Comment',
            signatures=['ICML.cc/2023/Conference/Submission1/Authors'],
            note=openreview.api.Note(
                content={
                    'comment': { 'value': 'Hi reviewers, the PDF was uploaded' }
                }
            )
        )

        helpers.await_queue_edit(openreview_client, edit_id=rebuttal_edit['id'])

        messages = openreview_client.get_messages(to='test@mail.com', subject='[ICML 2023] Your reply rebuttal comment has been received on Paper Number: 1, Paper Title: "Paper title 1 Version 2"')              
        assert len(messages) == 1

        messages = openreview_client.get_messages(to='reviewer2@icml.cc', subject='[ICML 2023] A reply rebuttal comment has been received on your assigned Paper Number: 1, Paper Title: "Paper title 1 Version 2"')
        assert len(messages) == 1

        ## Create  new rebuttal and expect all the child invitations to be created: rebuttal ACK, rebuttal comment and rebuttal reply

        test_client = openreview.api.OpenReviewClient(username='test@mail.com', password=helpers.strong_password)
        reviewer_client = openreview.api.OpenReviewClient(username='reviewer1@icml.cc', password=helpers.strong_password)

        review = reviewer_client.get_notes(invitation='ICML.cc/2023/Conference/Submission1/-/Official_Review', number=1)[0]
        rebuttal_edit = test_client.post_note_edit(
            invitation='ICML.cc/2023/Conference/Submission1/-/Rebuttal',
            signatures=['ICML.cc/2023/Conference/Submission1/Authors'],
            note=openreview.api.Note(
                replyto = review.id,
                content={
                    'rebuttal': { 'value': 'This is another rebuttal rebuttal.' }
                }
            )
        )

        helpers.await_queue_edit(openreview_client, edit_id=rebuttal_edit['id'])

        assert openreview_client.get_invitation(id='ICML.cc/2023/Conference/Submission1/Rebuttal3/-/Rebuttal_Acknowledgement')
        assert openreview_client.get_invitation(id='ICML.cc/2023/Conference/Submission1/Rebuttal3/-/Rebuttal_Comment')

        anon_groups = reviewer_client.get_groups(prefix='ICML.cc/2023/Conference/Submission1/Reviewer_', signatory='~Reviewer_ICMLOne1')
        anon_group_id = anon_groups[0].id

        assert anon_group_id in openreview_client.get_invitation('ICML.cc/2023/Conference/Submission1/Rebuttal3/-/Rebuttal_Acknowledgement').invitees

        rebuttal_ack2_edit = reviewer_client.post_note_edit(
            invitation='ICML.cc/2023/Conference/Submission1/Rebuttal3/-/Rebuttal_Acknowledgement',
            signatures=[anon_group_id],
            note=openreview.api.Note(
                content={
                    'acknowledgement': { 'value': True }
                }
            )
        )

        helpers.await_queue_edit(openreview_client, edit_id=rebuttal_ack2_edit['id'])

        rebuttal_comment_edit = reviewer_client.post_note_edit(
            invitation='ICML.cc/2023/Conference/Submission1/Rebuttal3/-/Rebuttal_Comment',
            signatures=[anon_group_id],
            note=openreview.api.Note(
                content={
                    'comment': { 'value': 'Authors please change the PDF with the new changes that we discussed' }
                }
            )
        )

        helpers.await_queue_edit(openreview_client, edit_id=rebuttal_comment_edit['id'])

        assert openreview_client.get_invitation('ICML.cc/2023/Conference/Submission1/Rebuttal3/Rebuttal_Comment1/-/Reply_Rebuttal_Comment')               


        ## Ask reviewers to edit their ACK the rebuttals
        venue = openreview.helpers.get_conference(client, request_form.id, setup=False)
        venue.custom_stage = openreview.stages.CustomStage(name='Rebuttal_Acknowledgement_Revision',
            child_invitations_name='Revision',
            reply_to='Rebuttal_Acknowledgement',
            reply_type=openreview.stages.CustomStage.ReplyType.REVISION,
            source=openreview.stages.CustomStage.Source.ALL_SUBMISSIONS,
            due_date=due_date,
            exp_date=due_date + datetime.timedelta(days=1),
            invitees=[openreview.stages.CustomStage.Participants.REPLYTO_REPLYTO_SIGNATURES],
            readers=[openreview.stages.CustomStage.Participants.REVIEWERS_SUBMITTED, openreview.stages.CustomStage.Participants.AUTHORS],
            content={
                'final_acknowledgement': {
                    'order': 1,
                    'description': "I acknowledge I read the rebuttal.",
                    'value': {
                        'param': {
                            'type': 'boolean',
                            'enum': [{ 'value': True, 'description': 'Yes, I acknowledge I read the rebuttal.' }],
                            'input': 'checkbox'
                        }
                    }
                }
            },
            notify_readers=True,
            email_sacs=False)

        venue.create_custom_stage()

        helpers.await_queue_edit(openreview_client, 'ICML.cc/2023/Conference/-/Rebuttal_Acknowledgement_Revision-0-1', count=1)

        ack_revision_invitations = openreview_client.get_invitations(invitation='ICML.cc/2023/Conference/-/Rebuttal_Acknowledgement_Revision')
        assert len(ack_revision_invitations) == 2

        ack_revision_invitation_ids = [invitation.id for invitation in ack_revision_invitations]
        assert 'ICML.cc/2023/Conference/Submission1/Rebuttal2/Rebuttal_Acknowledgement1/-/Revision' in ack_revision_invitation_ids
        assert 'ICML.cc/2023/Conference/Submission1/Rebuttal3/Rebuttal_Acknowledgement1/-/Revision' in ack_revision_invitation_ids

        revision_invitation = openreview_client.get_invitation('ICML.cc/2023/Conference/Submission1/Rebuttal2/Rebuttal_Acknowledgement1/-/Revision')
        assert revision_invitation.edit['note']['id'] == rebuttal_ack1_edit['note']['id']

        revision_invitation = openreview_client.get_invitation('ICML.cc/2023/Conference/Submission1/Rebuttal3/Rebuttal_Acknowledgement1/-/Revision')
        assert revision_invitation.edit['note']['id'] == rebuttal_ack2_edit['note']['id']
        
        rebuttal_ack2_revision_edit = reviewer_client.post_note_edit(
            invitation='ICML.cc/2023/Conference/Submission1/Rebuttal3/Rebuttal_Acknowledgement1/-/Revision',
            signatures=[anon_group_id],
            note=openreview.api.Note(
                content={
                    'final_acknowledgement': { 'value': True }
                }
            )
        )

        helpers.await_queue_edit(openreview_client, edit_id=rebuttal_ack2_revision_edit['id'])


    def test_meta_review_stage(self, client, openreview_client, helpers):
        pc_client=openreview.Client(username='pc@icml.cc', password=helpers.strong_password)
        pc_client_v2=openreview.api.OpenReviewClient(username='pc@icml.cc', password=helpers.strong_password)
        request_form=pc_client.get_notes(invitation='openreview.net/Support/-/Request_Form')[0]

        now = datetime.datetime.now()
        start_date = now - datetime.timedelta(days=2)
        due_date = now + datetime.timedelta(days=3)
        exp_date = due_date + datetime.timedelta(days=2)

        venue = openreview.helpers.get_conference(client, request_form.id, setup=False)
        venue.meta_review_stage = openreview.stages.MetaReviewStage(
            start_date=start_date,
            due_date=due_date,
            exp_date=exp_date,
            additional_fields={
                'recommendation': {
                    'description': 'Please select a recommendation for the paper',
                    'value': {
                        'param': {
                            'type': 'string',
                            'enum': ['Accept', 'Reject'],
                            'input': 'select'
                        }
                    },
                    'order': 2
                },
                'suggestions': {
                    'description': 'Please provide suggestions on how to improve the paper',
                    'value': {
                        'param': {
                            'type': 'string',
                            'maxLength': 5000,
                            'input': 'textarea',
                            'optional': True,
                            'deletable': True
                        }
                    }
                }
            },
            remove_fields=['confidence'],
            source_submissions_query={
                'position_paper_track': 'No'
            }
        )

        venue.create_meta_review_stage()
        helpers.await_queue_edit(openreview_client, 'ICML.cc/2023/Conference/-/Meta_Review-0-1', count=1)
        helpers.await_queue_edit(openreview_client, 'ICML.cc/2023/Conference/-/Meta_Review_SAC_Revision-0-1', count=1)

        invitations = openreview_client.get_invitations(invitation='ICML.cc/2023/Conference/-/Meta_Review')
        assert len(invitations) == 50
        assert invitations[0].edit['note']['id']['param']['withInvitation'] == invitations[0].id

        invitations = openreview_client.get_invitations(invitation='ICML.cc/2023/Conference/-/Meta_Review_SAC_Revision')
        assert len(invitations) == 50

        sac_revision_invitation = openreview_client.get_invitation('ICML.cc/2023/Conference/Submission1/-/Meta_Review_SAC_Revision')
        invitation = openreview_client.get_invitation('ICML.cc/2023/Conference/Submission1/-/Meta_Review')
        assert sac_revision_invitation.edit['note']['id']['param']['withInvitation'] == invitation.id
        assert 'suggestions' in invitation.edit['note']['content']

        # duedate + 2 days
        exp_date = invitation.duedate + (2*24*60*60*1000)
        assert invitation.expdate == exp_date

        assert openreview_client.get_invitation('ICML.cc/2023/Conference/Submission1/-/Meta_Review')
        assert not openreview.tools.get_invitation(openreview_client, 'ICML.cc/2023/Conference/Submission2/-/Meta_Review')
        assert openreview_client.get_invitation('ICML.cc/2023/Conference/Submission3/-/Meta_Review')
        assert not openreview.tools.get_invitation(openreview_client, 'ICML.cc/2023/Conference/Submission4/-/Meta_Review')
        assert openreview_client.get_invitation('ICML.cc/2023/Conference/Submission5/-/Meta_Review')

        ## Create position paper meta reviews
        venue = openreview.helpers.get_conference(client, request_form.id, setup=False)
        venue.meta_review_stage = openreview.stages.MetaReviewStage(
            start_date=start_date,
            due_date=due_date,
            exp_date=exp_date,
            remove_fields=['confidence'],
            name='Position_Paper_Meta_Review',
            source_submissions_query={
                'position_paper_track': 'Yes'
            }
        )

        venue.create_meta_review_stage()
        helpers.await_queue_edit(openreview_client, 'ICML.cc/2023/Conference/-/Position_Paper_Meta_Review-0-1', count=1)
        helpers.await_queue_edit(openreview_client, 'ICML.cc/2023/Conference/-/Position_Paper_Meta_Review_SAC_Revision-0-1', count=1)

        invitations = openreview_client.get_invitations(invitation='ICML.cc/2023/Conference/-/Position_Paper_Meta_Review')
        assert len(invitations) == 50
        assert invitations[0].edit['note']['id']['param']['withInvitation'] == invitations[0].id

        invitations = openreview_client.get_invitations(invitation='ICML.cc/2023/Conference/-/Position_Paper_Meta_Review_SAC_Revision')
        assert len(invitations) == 50

        sac_revision_invitation = openreview_client.get_invitation('ICML.cc/2023/Conference/Submission2/-/Meta_Review_SAC_Revision')
        invitation = openreview_client.get_invitation('ICML.cc/2023/Conference/Submission2/-/Meta_Review')
        assert sac_revision_invitation.edit['note']['id']['param']['withInvitation'] == invitation.id
        assert 'metareview' in invitation.edit['note']['content']
        assert 'suggestions' not in invitation.edit['note']['content']

        ac_client = openreview.api.OpenReviewClient(username='ac2@icml.cc', password=helpers.strong_password)
        submissions = ac_client.get_notes(invitation='ICML.cc/2023/Conference/-/Submission', sort='number:asc')

        anon_groups = ac_client.get_groups(prefix='ICML.cc/2023/Conference/Submission1/Area_Chair_', signatory='~AC_ICMLTwo1')
        anon_group_id = anon_groups[0].id

        meta_review_edit = ac_client.post_note_edit(
            invitation='ICML.cc/2023/Conference/Submission1/-/Meta_Review',
            signatures=[anon_group_id],
            note=openreview.api.Note(
                content={
                    'metareview': { 'value': 'This is a good paper' },
                    'recommendation': { 'value': 'Accept'}
                }
            )
        )

        helpers.await_queue_edit(openreview_client, edit_id=meta_review_edit['id'])

        #try to delete AC assignment of paper with a submitted metareview
        assignment = pc_client_v2.get_edges(invitation='ICML.cc/2023/Conference/Area_Chairs/-/Assignment', head=submissions[0].id, tail='~AC_ICMLTwo1')[0]
        assignment.ddate = openreview.tools.datetime_millis(datetime.datetime.now())
        assignment.cdate = None

        with pytest.raises(openreview.OpenReviewException, match=r'Can not remove assignment, the user ~AC_ICMLTwo1 already posted a Meta Review.'):
            pc_client_v2.post_edge(assignment)

        ## Post meta review to position paper
        ac_client = openreview.api.OpenReviewClient(username='ac1@icml.cc', password=helpers.strong_password)
        submissions = ac_client.get_notes(invitation='ICML.cc/2023/Conference/-/Submission', sort='number:asc')

        anon_groups = ac_client.get_groups(prefix='ICML.cc/2023/Conference/Submission4/Area_Chair_', signatory='~AC_ICMLOne1')
        anon_group_id = anon_groups[0].id

        meta_review_edit = ac_client.post_note_edit(
            invitation='ICML.cc/2023/Conference/Submission4/-/Meta_Review',
            signatures=[anon_group_id],
            note=openreview.api.Note(
                content={
                    'metareview': { 'value': 'This is a good paper' },
                    'recommendation': { 'value': 'Accept (Oral)'}
                }
            )
        )

        helpers.await_queue_edit(openreview_client, edit_id=meta_review_edit['id'])

        ## Extend deadline using a meta invitation and propagate the change to all the children
        new_due_date = openreview.tools.datetime_millis(now + datetime.timedelta(days=10))
        new_exp_date = openreview.tools.datetime_millis(now + datetime.timedelta(days=15))
        pc_client_v2.post_invitation_edit(
            invitations='ICML.cc/2023/Conference/-/Edit',
            readers=['ICML.cc/2023/Conference'],
            writers=['ICML.cc/2023/Conference'],
            signatures=['ICML.cc/2023/Conference'],
            invitation=openreview.api.Invitation(
                id='ICML.cc/2023/Conference/-/Position_Paper_Meta_Review',
                edit={
                    'invitation': {
                        'duedate': new_due_date,
                        'expdate': new_exp_date
                    }
                }
            )
        )

        helpers.await_queue_edit(openreview_client, 'ICML.cc/2023/Conference/-/Position_Paper_Meta_Review-0-1', count=2)
        invitation = openreview_client.get_invitation('ICML.cc/2023/Conference/Submission4/-/Meta_Review')
        assert invitation.expdate == new_exp_date

    def test_meta_review_agreement(self, client, openreview_client, helpers, selenium, request_page):

        pc_client=openreview.Client(username='pc@icml.cc', password=helpers.strong_password)
        request_form=pc_client.get_notes(invitation='openreview.net/Support/-/Request_Form')[0]
        venue = openreview.get_conference(client, request_form.id, support_user='openreview.net/Support')

        now = datetime.datetime.now()
        due_date = now + datetime.timedelta(days=3)
        venue.custom_stage = openreview.stages.CustomStage(name='Meta_Review_Agreement',
            reply_to=openreview.stages.CustomStage.ReplyTo.METAREVIEWS,
            source=openreview.stages.CustomStage.Source.ALL_SUBMISSIONS,
            due_date=due_date,
            exp_date=due_date + datetime.timedelta(days=1),
            invitees=[openreview.stages.CustomStage.Participants.SENIOR_AREA_CHAIRS_ASSIGNED],
            readers=[openreview.stages.CustomStage.Participants.SENIOR_AREA_CHAIRS_ASSIGNED],
            content={
                'meta_review_agreement': {
                    'order': 1,
                    'description': "If you do not agree with the meta-reviewer’s recommendation, please reach out to the meta-reviewer directly, discuss this submission and arrive at a consensus. If the meta-reviewer and you cannot arrive at a consensus for this submission, please mark \"no\" and describe the disagreement.",
                    'value': {
                        'param': {
                            'type': 'string',
                            'enum': [
                            'yes',
                            'no'
                            ],
                            'input': 'radio'
                        }
                    }
                },
                "explanation": {
                    "order": 2,
                    "description": "If you failed to arrive at consensus with the meta-reviewer, please describe your disagreement here for the program chairs.",
                    "value": {
                        "param": {
                            "maxLength": 5000,
                            "type": "string",
                            "input": "textarea",
                            "optional": True
                        }
                    }
                }
            },
            notify_readers=False,
            email_sacs=False)

        venue.create_custom_stage()

        helpers.await_queue_edit(openreview_client, 'ICML.cc/2023/Conference/-/Meta_Review_Agreement-0-1', count=1)

        assert len(openreview_client.get_invitations(invitation='ICML.cc/2023/Conference/-/Meta_Review_Agreement')) == 2

        sac_client = openreview.api.OpenReviewClient(username = 'sac2@icml.cc', password=helpers.strong_password)
        submissions = sac_client.get_notes(invitation='ICML.cc/2023/Conference/-/Submission', sort='number:asc')

        ac_client = openreview.api.OpenReviewClient(username='ac2@icml.cc', password=helpers.strong_password)
        anon_groups = ac_client.get_groups(prefix='ICML.cc/2023/Conference/Submission1/Area_Chair_', signatory='~AC_ICMLTwo1')
        anon_group_id = anon_groups[0].id

        invitation_id = 'ICML.cc/2023/Conference/Submission1/Meta_Review1/-/Meta_Review_Agreement'

        agreement_edit = sac_client.post_note_edit(
            invitation=invitation_id,
            signatures=['ICML.cc/2023/Conference/Submission1/Senior_Area_Chairs'],
            note=openreview.api.Note(
                content={
                    'meta_review_agreement': { 'value': 'yes' }
                }
            )
        )

        helpers.await_queue_edit(openreview_client, edit_id=agreement_edit['id'])

        pc_client_v2=openreview.api.OpenReviewClient(username='pc@icml.cc', password=helpers.strong_password)
        metareviews = pc_client_v2.get_notes(invitation='ICML.cc/2023/Conference/Submission1/-/Meta_Review')
        agreements = pc_client_v2.get_notes(invitation=invitation_id)
        assert agreements[0].replyto == metareviews[0].id
        assert agreements[0].readers == [
            'ICML.cc/2023/Conference/Program_Chairs',
            'ICML.cc/2023/Conference/Submission1/Senior_Area_Chairs'
        ]

        ac_client = openreview.api.OpenReviewClient(username='ac1@icml.cc', password=helpers.strong_password)
        submissions = ac_client.get_notes(invitation='ICML.cc/2023/Conference/-/Submission', sort='number:asc')

        anon_groups = ac_client.get_groups(prefix='ICML.cc/2023/Conference/Submission2/Area_Chair_', signatory='~AC_ICMLOne1')
        anon_group_id = anon_groups[0].id

        # post another metareview and check agreement invitation is created
        meta_review_edit = ac_client.post_note_edit(
            invitation='ICML.cc/2023/Conference/Submission2/-/Meta_Review',
            signatures=[anon_group_id],
            note=openreview.api.Note(
                content={
                    'metareview': { 'value': 'This is a very bad paper' },
                    'recommendation': { 'value': 'Reject'}
                }
            )
        )

        helpers.await_queue_edit(openreview_client, edit_id=meta_review_edit['id'])

        assert len(openreview_client.get_invitations(invitation='ICML.cc/2023/Conference/-/Meta_Review_Agreement')) == 3

        invitation_id = 'ICML.cc/2023/Conference/Submission2/Meta_Review1/-/Meta_Review_Agreement'
        sac_client = openreview.api.OpenReviewClient(username = 'sac1@gmail.com', password=helpers.strong_password)

        agreement_edit = sac_client.post_note_edit(
            invitation=invitation_id,
            signatures=['ICML.cc/2023/Conference/Submission2/Senior_Area_Chairs'],
            note=openreview.api.Note(
                content={
                    'meta_review_agreement': { 'value': 'no' },
                    'explanation': { 'value': 'I think the paper should be accepted.' }
                }
            )
        )

        helpers.await_queue_edit(openreview_client, edit_id=agreement_edit['id'])

        pc_client_v2=openreview.api.OpenReviewClient(username='pc@icml.cc', password=helpers.strong_password)
        metareviews = pc_client_v2.get_notes(invitation='ICML.cc/2023/Conference/Submission2/-/Meta_Review')
        agreements = pc_client_v2.get_notes(invitation=invitation_id)
        assert agreements[0].replyto == metareviews[0].id
        assert agreements[0].readers == [
            'ICML.cc/2023/Conference/Program_Chairs',
            'ICML.cc/2023/Conference/Submission2/Senior_Area_Chairs'
        ]

        submissions = sac_client.get_notes(invitation='ICML.cc/2023/Conference/-/Submission', sort='number:asc')
        note = submissions[1]

        # check SACs can't see Metareview Revision button
        request_page(selenium, 'http://localhost:3030/forum?id=' + note.id, sac_client.token, by=By.CLASS_NAME, wait_for_element='invitations-container')
        invitations_container = selenium.find_element(By.CLASS_NAME, 'invitations-container')
        invitation_buttons = invitations_container.find_element(By.CLASS_NAME, 'invitation-buttons')
        buttons = invitation_buttons.find_elements(By.TAG_NAME, 'button')
        assert len(buttons) ==  1
        assert buttons[0].text == 'Official Comment'

        ## SAC can edit the meta review
        meta_review_edit = sac_client.post_note_edit(
            invitation='ICML.cc/2023/Conference/Submission2/-/Meta_Review_SAC_Revision',
            signatures=['ICML.cc/2023/Conference/Submission2/Senior_Area_Chairs'],
            note=openreview.api.Note(
                id=metareviews[0].id,
                content={
                    'metareview': { 'value': 'I reverted the AC decision' },
                    'recommendation': { 'value': 'Accept (Oral)'}
                }
            )
        )

    def test_decision_stage(self, client, openreview_client, helpers):

        pc_client=openreview.Client(username='pc@icml.cc', password=helpers.strong_password)
        request_form=pc_client.get_notes(invitation='openreview.net/Support/-/Request_Form')[0]

        # Post a decision stage note
        now = datetime.datetime.now()
        start_date = now - datetime.timedelta(days=2)
        due_date = now + datetime.timedelta(days=3)

        decision_stage_note = pc_client.post_note(openreview.Note(
            content={
                'decision_start_date': start_date.strftime('%Y/%m/%d'),
                'decision_deadline': due_date.strftime('%Y/%m/%d'),
                'decision_options': 'Accept, Revision Needed, Reject',
                'make_decisions_public': 'No, decisions should NOT be revealed publicly when they are posted',
                'release_decisions_to_authors': 'No, decisions should NOT be revealed when they are posted to the paper\'s authors',
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
                                'optional': True,
                                'deletable': True
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

        helpers.await_queue_edit(openreview_client, 'ICML.cc/2023/Conference/-/Decision-0-1', count=1)

        assert openreview_client.get_invitation('ICML.cc/2023/Conference/Submission1/-/Decision')
        assert openreview_client.get_invitation('ICML.cc/2023/Conference/Submission2/-/Decision')
        assert openreview_client.get_invitation('ICML.cc/2023/Conference/Submission3/-/Decision')
        assert openreview_client.get_invitation('ICML.cc/2023/Conference/Submission4/-/Decision')
        assert openreview_client.get_invitation('ICML.cc/2023/Conference/Submission5/-/Decision')

        venue = openreview.get_conference(client, request_form.id, support_user='openreview.net/Support')
        submissions = venue.get_submissions(sort='number:asc')
        assert len(submissions) == 100
        decisions = ['Accept', 'Revision Needed', 'Reject']
        comment = {
            'Accept': 'Congratulations on your acceptance.',
            'Revision Needed': 'A revision is needed from the authors.',
            'Reject': 'We regret to inform you...'
        }

        with open(os.path.join(os.path.dirname(__file__), 'data/ICML_decisions.csv'), 'w') as file_handle:
            writer = csv.writer(file_handle)
            writer.writerow([submissions[0].number, 'Accept', comment["Accept"]])
            writer.writerow([submissions[1].number, 'Reject', comment["Reject"]])
            writer.writerow([submissions[2].number, 'Revision Needed', comment["Revision Needed"]])
            for submission in submissions[3:]:
                decision = random.choice(decisions)
                writer.writerow([submission.number, decision, comment[decision]])

        decision_stage_invitation = f'openreview.net/Support/-/Request{request_form.number}/Decision_Stage'
        url = pc_client.put_attachment(os.path.join(os.path.dirname(__file__), 'data/ICML_decisions.csv'),
                                         decision_stage_invitation, 'decisions_file')

        #post decisions from request form
        decision_stage_note = pc_client.post_note(openreview.Note(
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
                                'optional': True,
                                'deletable': True
                            }
                        }
                    }
                },
                'decisions_file': url
            },
            forum=request_form.forum,
            invitation=decision_stage_invitation,
            readers=['ICML.cc/2023/Conference/Program_Chairs', 'openreview.net/Support'],
            replyto=request_form.forum,
            referent=request_form.forum,
            signatures=['~Program_ICMLChair1'],
            writers=[]
        ))
        assert decision_stage_note
        helpers.await_queue()

        helpers.await_queue_edit(openreview_client, 'ICML.cc/2023/Conference/-/Decision-0-1', count=2)

        decision = openreview_client.get_notes(invitation='ICML.cc/2023/Conference/Submission1/-/Decision')[0]
        assert 'Accept' == decision.content['decision']['value']
        assert 'Congratulations on your acceptance.' in decision.content['comment']['value']
        assert decision.readers == [
            'ICML.cc/2023/Conference/Program_Chairs',
            'ICML.cc/2023/Conference/Submission1/Senior_Area_Chairs',
            'ICML.cc/2023/Conference/Submission1/Area_Chairs'
        ]
        assert decision.nonreaders == [
            'ICML.cc/2023/Conference/Submission1/Authors'
        ]

        decision = openreview_client.get_notes(invitation='ICML.cc/2023/Conference/Submission3/-/Decision')[0]
        assert 'Revision Needed' == decision.content['decision']['value']

        # manually change a decision
        pc_client_v2=openreview.api.OpenReviewClient(username='pc@icml.cc', password=helpers.strong_password)
        decision_note = pc_client_v2.post_note_edit(invitation='ICML.cc/2023/Conference/Submission3/-/Decision',
            signatures=['ICML.cc/2023/Conference/Program_Chairs'],
            note=openreview.api.Note(
                id=decision.id,
                content={
                    'decision': {'value': 'Accept'},
                    'comment': {'value': 'This is a comment.'}
                }
            ))
        helpers.await_queue_edit(openreview_client, edit_id=decision_note['id'])

        request_form=pc_client.get_notes(invitation='openreview.net/Support/-/Request_Form')[0]

        #release decisions to authors and reviewers
        decision_stage_note = pc_client.post_note(openreview.Note(
            content={
                'decision_start_date': start_date.strftime('%Y/%m/%d'),
                'decision_deadline': due_date.strftime('%Y/%m/%d'),
                'decision_options': 'Accept, Revision Needed, Reject',
                'make_decisions_public': 'No, decisions should NOT be revealed publicly when they are posted',
                'release_decisions_to_authors': 'Yes, decisions should be revealed when they are posted to the paper\'s authors',
                'release_decisions_to_reviewers': 'Yes, decisions should be immediately revealed to the paper\'s reviewers',
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
                                'optional': True,
                                'deletable': True
                            }
                        }
                    }
                },
                'decisions_file': request_form.content['decisions_file']
            },
            forum=request_form.forum,
            invitation=decision_stage_invitation,
            readers=['ICML.cc/2023/Conference/Program_Chairs', 'openreview.net/Support'],
            replyto=request_form.forum,
            referent=request_form.forum,
            signatures=['~Program_ICMLChair1'],
            writers=[]
        ))
        assert decision_stage_note
        helpers.await_queue()

        helpers.await_queue_edit(openreview_client, 'ICML.cc/2023/Conference/-/Decision-0-1', count=3)

        decision = openreview_client.get_notes(invitation='ICML.cc/2023/Conference/Submission1/-/Decision')[0]
        assert decision.readers == [
            'ICML.cc/2023/Conference/Program_Chairs',
            'ICML.cc/2023/Conference/Submission1/Senior_Area_Chairs',
            'ICML.cc/2023/Conference/Submission1/Area_Chairs',
            'ICML.cc/2023/Conference/Submission1/Reviewers',
            'ICML.cc/2023/Conference/Submission1/Authors'
        ]
        assert not decision.nonreaders

        # assert decisions were not overwritten
        decision = openreview_client.get_notes(invitation='ICML.cc/2023/Conference/Submission3/-/Decision')[0]
        assert 'Accept' == decision.content['decision']['value']

    def test_post_decision_stage(self, client, openreview_client, helpers, selenium, request_page):

        pc_client=openreview.Client(username='pc@icml.cc', password=helpers.strong_password)
        request_form=pc_client.get_notes(invitation='openreview.net/Support/-/Request_Form')[0]

        submissions = openreview_client.get_notes(content= { 'venueid': 'ICML.cc/2023/Conference/Submission'}, sort='number:asc')
        assert submissions and len(submissions) == 100

        # Assert that submissions are still blind
        assert submissions[0].content['authors']['readers'] == ["ICML.cc/2023/Conference","ICML.cc/2023/Conference/Submission1/Authors"]
        assert submissions[0].content['authorids']['readers'] == ["ICML.cc/2023/Conference","ICML.cc/2023/Conference/Submission1/Authors"]
        assert submissions[1].content['authors']['readers'] == ["ICML.cc/2023/Conference","ICML.cc/2023/Conference/Submission2/Authors"]
        assert submissions[1].content['authorids']['readers'] == ["ICML.cc/2023/Conference","ICML.cc/2023/Conference/Submission2/Authors"]
        # Assert that submissions are private
        assert submissions[0].readers == [
            "ICML.cc/2023/Conference",
            "ICML.cc/2023/Conference/Submission1/Senior_Area_Chairs",
            "ICML.cc/2023/Conference/Submission1/Area_Chairs",
            "ICML.cc/2023/Conference/Submission1/Reviewers",
            "ICML.cc/2023/Conference/Submission1/Authors",
            'ICML.cc/2023/Conference/Submission1/Ethics_Reviewers'
        ]
        assert submissions[1].readers == [
            "ICML.cc/2023/Conference",
            "ICML.cc/2023/Conference/Submission2/Senior_Area_Chairs",
            "ICML.cc/2023/Conference/Submission2/Area_Chairs",
            "ICML.cc/2023/Conference/Submission2/Reviewers",
            "ICML.cc/2023/Conference/Submission2/Authors",
            'ICML.cc/2023/Conference/Submission2/Ethics_Reviewers'
        ]
        assert not submissions[0].odate
        assert not submissions[1].odate

        invitation = client.get_invitation(f'openreview.net/Support/-/Request{request_form.number}/Post_Decision_Stage')
        invitation.cdate = openreview.tools.datetime_millis(datetime.datetime.now())
        client.post_invitation(invitation)

        invitation = pc_client.get_invitation(f'openreview.net/Support/-/Request{request_form.number}/Post_Decision_Stage')

        assert 'Accept' in invitation.reply['content']['home_page_tab_names']['default']
        assert invitation.reply['content']['home_page_tab_names']['default']['Accept'] == 'Accept'
        assert 'Revision Needed' in invitation.reply['content']['home_page_tab_names']['default']
        assert invitation.reply['content']['home_page_tab_names']['default']['Revision Needed'] == 'Revision Needed'
        assert 'Reject' in invitation.reply['content']['home_page_tab_names']['default']
        assert invitation.reply['content']['home_page_tab_names']['default']['Reject'] == 'Reject'

        #make sure all decision process functions have finished
        for number in range(1, 101):
            helpers.await_queue_edit(openreview_client, invitation=f'ICML.cc/2023/Conference/Submission{number}/-/Decision')

        authors_accepted_group = openreview_client.get_group('ICML.cc/2023/Conference/Authors/Accepted')
        num_accepted_papers = len(authors_accepted_group.members)

        # add publication chair
        pc_client=openreview.Client(username='pc@icml.cc', password=helpers.strong_password)
        request_form=pc_client.get_notes(invitation='openreview.net/Support/-/Request_Form')[0]

        pc_client.post_note(openreview.Note(
            content={
                'title': 'Thirty-ninth International Conference on Machine Learning',
                'Official Venue Name': 'Thirty-ninth International Conference on Machine Learning',
                'Abbreviated Venue Name': 'ICML 2023',
                'Official Website URL': 'https://icml.cc',
                'program_chair_emails': ['pc@icml.cc', 'pc3@icml.cc'],
                'contact_email': 'pc@icml.cc',
                'publication_chairs': 'Yes, our venue has Publication Chairs',
                'publication_chairs_emails': ['publicationchair@icml.com'],
                'Venue Start Date': '2023/07/01',
                'Submission Deadline': request_form.content['Submission Deadline'],
                'Location': 'Virtual',
                'submission_reviewer_assignment': 'Automatic',
                'How did you hear about us?': 'ML conferences',
                'Expected Submissions': '100',
                'Additional Submission Options': request_form.content['Additional Submission Options'],
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

        pub_chair_group = openreview_client.get_group('ICML.cc/2023/Conference/Publication_Chairs')
        assert pub_chair_group and 'publicationchair@icml.com' in pub_chair_group.members

        # check members have not changed
        authors_accepted_group = openreview_client.get_group('ICML.cc/2023/Conference/Authors/Accepted')
        assert len(authors_accepted_group.members) == num_accepted_papers

        #run post submission, give publication chairs access to accepted papers
        now = datetime.datetime.now()
        short_name = 'ICML 2023'
        post_decision_stage_note = pc_client.post_note(openreview.Note(
            content={
                'reveal_authors': 'No, I don\'t want to reveal any author identities.',
                'submission_readers': 'Assigned program committee (assigned reviewers, assigned area chairs, assigned senior area chairs if applicable)',
                'hide_fields': ['supplementary_material', 'pdf'],
                'home_page_tab_names': {
                    'Accept': 'Accept',
                    'Revision Needed': 'Revision Needed',
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
''',
                'revision_needed_email_content': f'''Dear {{{{fullname}}}},

Thank you for submitting your paper, {{{{submission_title}}}}, to {short_name}.
You can find the final reviews for your paper on the submission page in OpenReview at: {{{{forum_url}}}}

Best,
{short_name} Program Chairs
'''
            },
            forum=request_form.forum,
            invitation=invitation.id,
            readers=['ICML.cc/2023/Conference/Program_Chairs', 'openreview.net/Support'],
            replyto=request_form.forum,
            referent=request_form.forum,
            signatures=['~Program_ICMLChair1'],
            writers=[]
        ))
        assert post_decision_stage_note
        helpers.await_queue()

        process_logs = client.get_process_logs(id = post_decision_stage_note.id)
        assert len(process_logs) == 1
        assert process_logs[0]['status'] == 'ok'

        submissions = openreview_client.get_notes(invitation='ICML.cc/2023/Conference/-/Submission', sort='number:asc')
        submission = submissions[0]

        # assert PCs can't use Submission invitation after post decision is run
        pc_client_v2=openreview.api.OpenReviewClient(username='pc@icml.cc', password=helpers.strong_password)
        request_page(selenium, 'http://localhost:3030/forum?id={}'.format(submission.id), pc_client_v2.token, by=By.CLASS_NAME, wait_for_element='forum-note')
        note_div = selenium.find_element(By.CLASS_NAME, 'forum-note')
        assert note_div
        button_row = note_div.find_element(By.CLASS_NAME, 'invitation-buttons')
        assert button_row
        buttons = button_row.find_elements(By.CLASS_NAME, 'btn-xs')
        assert buttons[0].text == 'Edit  '
        buttons[0].click()
        time.sleep(0.5)
        dropdown = button_row.find_element(By.CLASS_NAME, 'dropdown-menu')
        dropdown_values = dropdown.find_elements(By.TAG_NAME, "a")
        values = [value.text for value in dropdown_values]
        assert ['Post Submission', 'PC Revision', 'Ethics Review Flag'] == values

        venue = openreview.get_conference(client, request_form.id, support_user='openreview.net/Support')
        accepted_submissions = venue.get_submissions(accepted=True, sort='number:asc')
        rejected_submissions = venue.get_submissions(venueid='ICML.cc/2023/Conference/Rejected_Submission', sort='number:asc')

        assert 'ICML.cc/2023/Conference/Publication_Chairs' in accepted_submissions[0].readers
        assert 'ICML.cc/2023/Conference/Publication_Chairs' in accepted_submissions[0].content['authors']['readers']
        assert 'ICML.cc/2023/Conference/Publication_Chairs' in accepted_submissions[0].content['authorids']['readers']
        assert 'ICML.cc/2023/Conference/Publication_Chairs' not in rejected_submissions[0].readers
        assert 'ICML.cc/2023/Conference/Publication_Chairs' not in rejected_submissions[0].content['authors']['readers']
        assert 'ICML.cc/2023/Conference/Publication_Chairs' not in rejected_submissions[0].content['authorids']['readers']

        # enable camera-ready revisions
        now = datetime.datetime.now()
        start_date = now - datetime.timedelta(days=2)
        due_date = now + datetime.timedelta(days=3)
        revision_stage_note = pc_client.post_note(openreview.Note(
            content={
                'submission_revision_name': 'Camera Ready Revision',
                'submission_revision_start_date': start_date.strftime('%Y/%m/%d'),
                'submission_revision_deadline': due_date.strftime('%Y/%m/%d'),
                'accepted_submissions_only': 'Enable revision for accepted submissions only',
                'submission_author_edition': 'Allow reorder of existing authors only',
                'submission_revision_remove_options': ['keywords', 'financial_aid', 'subject_areas', 'position_paper_track']
            },
            forum=request_form.forum,
            invitation='openreview.net/Support/-/Request{}/Submission_Revision_Stage'.format(request_form.number),
            readers=['ICML.cc/2023/Conference/Program_Chairs', 'openreview.net/Support', 'ICML.cc/2023/Conference/Publication_Chairs'],
            referent=request_form.forum,
            replyto=request_form.forum,
            signatures=['~Program_ICMLChair1'],
            writers=[]
        ))
        assert revision_stage_note

        helpers.await_queue()

        helpers.await_queue_edit(openreview_client, 'ICML.cc/2023/Conference/-/Camera_Ready_Revision-0-1', count=1)

        # submit camera-ready revision
        author_client = openreview.api.OpenReviewClient(username='test@mail.com', password=helpers.strong_password)
        revision_edit = author_client.post_note_edit(invitation='ICML.cc/2023/Conference/Submission1/-/Camera_Ready_Revision',
            signatures=['ICML.cc/2023/Conference/Submission1/Authors'],
            note=openreview.api.Note(
                content={
                    'title': { 'value': accepted_submissions[0].content['title']['value'] + ' UPDATED' },
                    'abstract': accepted_submissions[0].content['abstract'],
                    'authors': {'value': accepted_submissions[0].content['authors']['value']},
                    'authorids': {'value': accepted_submissions[0].content['authorids']['value']},
                    'pdf': { 'value': '/pdf/' + 'p' * 40 +'.pdf' }
                }
            ))
        helpers.await_queue_edit(openreview_client, edit_id=revision_edit['id'])

        venue = openreview.get_conference(client, request_form.id, support_user='openreview.net/Support')
        accepted_submissions = venue.get_submissions(accepted=True, sort='number:asc')
        rejected_submissions = venue.get_submissions(venueid='ICML.cc/2023/Conference/Rejected_Submission', sort='number:asc')

        assert 'ICML.cc/2023/Conference/Publication_Chairs' in accepted_submissions[0].readers
        assert 'ICML.cc/2023/Conference/Publication_Chairs' in accepted_submissions[0].content['authors']['readers']
        assert 'ICML.cc/2023/Conference/Publication_Chairs' in accepted_submissions[0].content['authorids']['readers']
        assert 'ICML.cc/2023/Conference/Publication_Chairs' not in rejected_submissions[0].readers
        assert 'ICML.cc/2023/Conference/Publication_Chairs' not in rejected_submissions[0].content['authors']['readers']
        assert 'ICML.cc/2023/Conference/Publication_Chairs' not in rejected_submissions[0].content['authorids']['readers']

        #Post a post decision note, unhide financial_aid and hide pdf
        now = datetime.datetime.now()
        start_date = now - datetime.timedelta(days=2)
        due_date = now + datetime.timedelta(days=3)
        short_name = 'ICML 2023'
        post_decision_stage_note = pc_client.post_note(openreview.Note(
            content={
                'reveal_authors': 'Reveal author identities of only accepted submissions to the public',
                'submission_readers': 'Make accepted submissions public and hide rejected submissions',
                'hide_fields': ['supplementary_material', 'pdf'],
                'home_page_tab_names': {
                    'Accept': 'Accept',
                    'Revision Needed': 'Revision Needed',
                    'Reject': 'Submitted'
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
            forum=request_form.forum,
            invitation=invitation.id,
            readers=['ICML.cc/2023/Conference/Program_Chairs', 'openreview.net/Support'],
            replyto=request_form.forum,
            referent=request_form.forum,
            signatures=['~Program_ICMLChair1'],
            writers=[]
        ))
        assert post_decision_stage_note
        helpers.await_queue()

        process_logs = client.get_process_logs(id = post_decision_stage_note.id)
        assert len(process_logs) == 1
        assert process_logs[0]['status'] == 'ok'

        venue = openreview.get_conference(client, request_form.id, support_user='openreview.net/Support')
        accepted_submissions = venue.get_submissions(accepted=True, sort='number:asc')
        rejected_submissions = venue.get_submissions(venueid='ICML.cc/2023/Conference/Rejected_Submission', sort='number:asc')
        assert (len(accepted_submissions)+len(rejected_submissions)) == 100

        messages = openreview_client.get_messages(subject='[ICML 2023] Decision notification for your submission 1: Paper title 1 Version 2 UPDATED')
        assert len(messages) == 5
        assert messages[0]['content']['replyTo'] == 'pc@icml.cc'
        recipients = [msg['content']['to'] for msg in messages]
        assert 'sac1@gmail.com' in recipients
        assert 'test@mail.com' in recipients
        assert 'peter@mail.com' in recipients
        assert 'melisa@yahoo.com' in recipients
        assert 'andrew@amazon.com' in recipients
        assert 'We are delighted to inform you that your submission has been accepted.' in messages[0]['content']['text']

        replies = pc_client.get_notes(forum=request_form.id, invitation=f'openreview.net/Support/-/Request{request_form.number}/Comment', sort='tmdate:desc')
        assert replies[0].content['title'] == 'Post Decision Stage Process Completed'
        assert replies[1].content['title'] == 'Decision Notification Status'
        assert 'Decision notifications have been sent to the authors. You can check the status of the emails by clicking on this link: https://openreview.net/messages?parentGroup=ICML.cc/2023/Conference/Authors' in replies[1].content['comment']

        for submission in accepted_submissions:
            assert submission.readers == ['everyone']
            assert 'readers' not in submission.content['authors']
            assert 'readers' not in submission.content['authorids']
            assert 'readers' in submission.content['pdf']
            assert 'readers' not in submission.content['financial_aid']
            assert submission.pdate
            assert submission.odate
            assert submission.content['venue']['value'] == 'ICML 2023'
            assert submission.content['venueid']['value'] == 'ICML.cc/2023/Conference'

        year = datetime.datetime.now().year
        valid_bibtex = '''@inproceedings{
user'''+str(year)+'''paper,
title={Paper title 1 Version 2 {UPDATED}},
author={SomeFirstName User and Peter SomeLastName and Andrew Mc and SAC ICMLOne and Melisa ICML},
booktitle={Thirty-ninth International Conference on Machine Learning},
year={'''+str(year)+'''},
url={https://openreview.net/forum?id='''

        valid_bibtex = valid_bibtex + accepted_submissions[0].forum + '''}
}'''

        assert '_bibtex' in accepted_submissions[0].content and accepted_submissions[0].content['_bibtex']['value'] == valid_bibtex

        for submission in rejected_submissions:
            assert submission.readers == [
                "ICML.cc/2023/Conference",
                f"ICML.cc/2023/Conference/Submission{submission.number}/Senior_Area_Chairs",
                f"ICML.cc/2023/Conference/Submission{submission.number}/Area_Chairs",
                f"ICML.cc/2023/Conference/Submission{submission.number}/Reviewers",
                f"ICML.cc/2023/Conference/Submission{submission.number}/Authors"
            ]
            assert submission.content['authors']['readers'] == ["ICML.cc/2023/Conference",f"ICML.cc/2023/Conference/Submission{submission.number}/Authors"]
            assert submission.content['authorids']['readers'] == ["ICML.cc/2023/Conference",f"ICML.cc/2023/Conference/Submission{submission.number}/Authors"]
            assert not submission.pdate
            assert not submission.odate
            assert submission.content['venue']['value'] == 'Submitted to ICML 2023'
            assert submission.content['venueid']['value'] == 'ICML.cc/2023/Conference/Rejected_Submission'
            assert 'readers' in submission.content['pdf']
            assert 'readers' not in submission.content['financial_aid']

        valid_bibtex = '''@misc{
anonymous'''+str(year)+'''paper,
title={Paper title 2},
author={Anonymous},
year={'''+str(year)+'''},
url={https://openreview.net/forum?id='''

        valid_bibtex = valid_bibtex + rejected_submissions[0].forum + '''}
}'''

        assert '_bibtex' in rejected_submissions[0].content and rejected_submissions[0].content['_bibtex']['value'] == valid_bibtex

        #Post another post decision note
        now = datetime.datetime.now()
        short_name = 'ICML 2023'
        post_decision_stage_note = pc_client.post_note(openreview.Note(
            content={
                'reveal_authors': 'Reveal author identities of only accepted submissions to the public',
                'submission_readers': 'Make accepted submissions public and hide rejected submissions',
                'hide_fields': ['supplementary_material', 'pdf'],
                'home_page_tab_names': {
                    'Accept': 'Accept',
                    'Revision Needed': 'Revision Needed',
                    'Reject': 'Submitted'
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
            forum=request_form.forum,
            invitation=invitation.id,
            readers=['ICML.cc/2023/Conference/Program_Chairs', 'openreview.net/Support'],
            replyto=request_form.forum,
            referent=request_form.forum,
            signatures=['~Program_ICMLChair1'],
            writers=[]
        ))
        assert post_decision_stage_note
        helpers.await_queue()

        process_logs = client.get_process_logs(id = post_decision_stage_note.id)
        assert len(process_logs) == 1
        assert process_logs[0]['status'] == 'ok'

        # check emails were not resent and decision emails status comment was not re-posted
        messages = openreview_client.get_messages(subject='[ICML 2023] Decision notification for your submission 1: Paper title 1 Version 2 UPDATED')
        assert len(messages) == 5

        replies = pc_client.get_notes(forum=request_form.id, invitation=f'openreview.net/Support/-/Request{request_form.number}/Comment')
        assert len(replies) == 27

        # submit another camera-ready revision after authors have been released
        author_client = openreview.api.OpenReviewClient(username='test@mail.com', password=helpers.strong_password)
        revision_edit = author_client.post_note_edit(invitation='ICML.cc/2023/Conference/Submission1/-/Camera_Ready_Revision',
            signatures=['ICML.cc/2023/Conference/Submission1/Authors'],
            note=openreview.api.Note(
                content={
                    'title': { 'value': accepted_submissions[0].content['title']['value']},
                    'abstract': { 'value': accepted_submissions[0].content['abstract']['value'] + ' UPDATED'},
                    'authors': {'value': accepted_submissions[0].content['authors']['value']},
                    'authorids': {'value': accepted_submissions[0].content['authorids']['value']},
                    'pdf': { 'value': '/pdf/' + 'p' * 40 +'.pdf' }
                }
            ))
        helpers.await_queue_edit(openreview_client, edit_id=revision_edit['id'])

        venue = openreview.get_conference(client, request_form.id, support_user='openreview.net/Support')
        accepted_submissions = venue.get_submissions(accepted=True, sort='number:asc')

        assert accepted_submissions[0].readers == ['everyone']
        assert 'readers' not in accepted_submissions[0].content['authors']
        assert 'readers' not in accepted_submissions[0].content['authorids']

    def test_forum_chat(self, openreview_client, helpers):

        submission_invitation = openreview_client.get_invitation('ICML.cc/2023/Conference/-/Submission')
        assert len(submission_invitation.reply_forum_views)

        submission = openreview_client.get_notes(invitation='ICML.cc/2023/Conference/-/Submission', number=1)[0]

        reviewer_client = openreview.api.OpenReviewClient(username='reviewer1@icml.cc', password=helpers.strong_password)

        anon_groups = reviewer_client.get_groups(prefix='ICML.cc/2023/Conference/Submission1/Reviewer_', signatory='~Reviewer_ICMLOne1')
        anon_group_id = anon_groups[0].id

        invitation = openreview_client.get_invitation('ICML.cc/2023/Conference/Submission1/-/Chat')
        assert invitation.date_processes[0].get('dates') == []

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

        helpers.await_queue_edit(openreview_client, edit_id=note_edit['id'])

        invitation = openreview_client.get_invitation('ICML.cc/2023/Conference/Submission1/-/Chat')
        assert invitation.date_processes[0].get('dates') is None
        assert invitation.date_processes[0].get('cron') == '0 */4 * * *'

        assert len(openreview_client.get_messages(to='reviewer1@icml.cc', subject='[ICML 2023] New conversation in committee members chat for submission 1: Paper title 1 Version 2 UPDATED')) == 0
        assert len(openreview_client.get_messages(to='reviewer2@icml.cc', subject='[ICML 2023] New conversation in committee members chat for submission 1: Paper title 1 Version 2 UPDATED')) == 1
        assert len(openreview_client.get_messages(to='melisa@icml.cc', subject='[ICML 2023] New conversation in committee members chat for submission 1: Paper title 1 Version 2 UPDATED')) == 1
        assert len(openreview_client.get_messages(to='reviewer3@icml.cc', subject='[ICML 2023] New conversation in committee members chat for submission 1: Paper title 1 Version 2 UPDATED')) == 1
        assert len(openreview_client.get_messages(to='reviewer4@yahoo.com', subject='[ICML 2023] New conversation in committee members chat for submission 1: Paper title 1 Version 2 UPDATED')) == 1
        assert len(openreview_client.get_messages(to='rachel_bis@icml.cc', subject='[ICML 2023] New conversation in committee members chat for submission 1: Paper title 1 Version 2 UPDATED')) == 1
        assert len(openreview_client.get_messages(to='ac2@icml.cc', subject='[ICML 2023] New conversation in committee members chat for submission 1: Paper title 1 Version 2 UPDATED')) == 1
        assert len(openreview_client.get_messages(to='sac2@icml.cc', subject='[ICML 2023] New conversation in committee members chat for submission 1: Paper title 1 Version 2 UPDATED')) == 0
        assert len(openreview_client.get_messages(to='pc@icml.cc', subject='[ICML 2023] New conversation in committee members chat for submission 1: Paper title 1 Version 2 UPDATED')) == 0

        pc_client=openreview.api.OpenReviewClient(username='pc@icml.cc', password=helpers.strong_password)

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

        helpers.await_queue_edit(openreview_client, edit_id=note_edit['id'])

        assert len(openreview_client.get_messages(to='reviewer1@icml.cc', subject='[ICML 2023] New messages in committee members chat for submission 1: Paper title 1 Version 2 UPDATED')) == 0
        assert len(openreview_client.get_messages(to='reviewer2@icml.cc', subject='[ICML 2023] New messages in committee members chat for submission 1: Paper title 1 Version 2 UPDATED')) == 0
        assert len(openreview_client.get_messages(to='melisa@icml.cc', subject='[ICML 2023] New messages in committee members chat for submission 1: Paper title 1 Version 2 UPDATED')) == 0
        assert len(openreview_client.get_messages(to='reviewer3@icml.cc', subject='[ICML 2023] New messages in committee members chat for submission 1: Paper title 1 Version 2 UPDATED')) == 0
        assert len(openreview_client.get_messages(to='reviewer4@yahoo.com', subject='[ICML 2023] New messages in committee members chat for submission 1: Paper title 1 Version 2 UPDATED')) == 0
        assert len(openreview_client.get_messages(to='rachel_bis@icml.cc', subject='[ICML 2023] New messages in committee members chat for submission 1: Paper title 1 Version 2 UPDATED')) == 0
        assert len(openreview_client.get_messages(to='ac2@icml.cc', subject='[ICML 2023] New messages in committee members chat for submission 1: Paper title 1 Version 2 UPDATED')) == 0
        assert len(openreview_client.get_messages(to='sac2@icml.cc', subject='[ICML 2023] New messages in committee members chat for submission 1: Paper title 1 Version 2 UPDATED')) == 0
        assert len(openreview_client.get_messages(to='pc@icml.cc', subject='[ICML 2023] New messages in committee members chat for submission 1: Paper title 1 Version 2 UPDATED')) == 0

        sac_client=openreview.api.OpenReviewClient(username='sac2@icml.cc', password=helpers.strong_password)

        note_edit = sac_client.post_note_edit(
            invitation='ICML.cc/2023/Conference/Submission1/-/Chat',
            signatures=['ICML.cc/2023/Conference/Submission1/Senior_Area_Chairs'],
            note=openreview.api.Note(
                replyto=note_edit['note']['id'],
                content={
                    'message': { 'value': 'Chat comment number 3' }
                }
            )
        )

        helpers.await_queue_edit(openreview_client, edit_id=note_edit['id'])

        assert len(openreview_client.get_messages(to='reviewer1@icml.cc', subject='[ICML 2023] New messages in committee members chat for submission 1: Paper title 1 Version 2 UPDATED')) == 0
        assert len(openreview_client.get_messages(to='reviewer2@icml.cc', subject='[ICML 2023] New messages in committee members chat for submission 1: Paper title 1 Version 2 UPDATED')) == 0
        assert len(openreview_client.get_messages(to='melisa@icml.cc', subject='[ICML 2023] New messages in committee members chat for submission 1: Paper title 1 Version 2 UPDATED')) == 0
        assert len(openreview_client.get_messages(to='reviewer3@icml.cc', subject='[ICML 2023] New messages in committee members chat for submission 1: Paper title 1 Version 2 UPDATED')) == 0
        assert len(openreview_client.get_messages(to='reviewer4@yahoo.com', subject='[ICML 2023] New messages in committee members chat for submission 1: Paper title 1 Version 2 UPDATED')) == 0
        assert len(openreview_client.get_messages(to='rachel_bis@icml.cc', subject='[ICML 2023] New messages in committee members chat for submission 1: Paper title 1 Version 2 UPDATED')) == 0
        assert len(openreview_client.get_messages(to='ac2@icml.cc', subject='[ICML 2023] New messages in committee members chat for submission 1: Paper title 1 Version 2 UPDATED')) == 0
        assert len(openreview_client.get_messages(to='sac2@icml.cc', subject='[ICML 2023] New messages in committee members chat for submission 1: Paper title 1 Version 2 UPDATED')) == 0
        assert len(openreview_client.get_messages(to='pc@icml.cc', subject='[ICML 2023] New messages in committee members chat for submission 1: Paper title 1 Version 2 UPDATED')) == 0

        note_edit = sac_client.post_note_edit(
            invitation='ICML.cc/2023/Conference/Submission1/-/Chat',
            signatures=['ICML.cc/2023/Conference/Submission1/Senior_Area_Chairs'],
            note=openreview.api.Note(
                replyto=note_edit['note']['id'],
                content={
                    'message': { 'value': 'Chat comment number 4' }
                }
            )
        )

        helpers.await_queue_edit(openreview_client, edit_id=note_edit['id'])

        assert len(openreview_client.get_messages(to='reviewer1@icml.cc', subject='[ICML 2023] New messages in committee members chat for submission 1: Paper title 1 Version 2 UPDATED')) == 0
        assert len(openreview_client.get_messages(to='reviewer2@icml.cc', subject='[ICML 2023] New messages in committee members chat for submission 1: Paper title 1 Version 2 UPDATED')) == 0
        assert len(openreview_client.get_messages(to='melisa@icml.cc', subject='[ICML 2023] New messages in committee members chat for submission 1: Paper title 1 Version 2 UPDATED')) == 0
        assert len(openreview_client.get_messages(to='reviewer3@icml.cc', subject='[ICML 2023] New messages in committee members chat for submission 1: Paper title 1 Version 2 UPDATED')) == 0
        assert len(openreview_client.get_messages(to='reviewer4@yahoo.com', subject='[ICML 2023] New messages in committee members chat for submission 1: Paper title 1 Version 2 UPDATED')) == 0
        assert len(openreview_client.get_messages(to='rachel_bis@icml.cc', subject='[ICML 2023] New messages in committee members chat for submission 1: Paper title 1 Version 2 UPDATED')) == 0
        assert len(openreview_client.get_messages(to='ac2@icml.cc', subject='[ICML 2023] New messages in committee members chat for submission 1: Paper title 1 Version 2 UPDATED')) == 0
        assert len(openreview_client.get_messages(to='sac2@icml.cc', subject='[ICML 2023] New messages in committee members chat for submission 1: Paper title 1 Version 2 UPDATED')) == 0
        assert len(openreview_client.get_messages(to='pc@icml.cc', subject='[ICML 2023] New messages in committee members chat for submission 1: Paper title 1 Version 2 UPDATED')) == 0

        note_edit = sac_client.post_note_edit(
            invitation='ICML.cc/2023/Conference/Submission1/-/Chat',
            signatures=['ICML.cc/2023/Conference/Submission1/Senior_Area_Chairs'],
            note=openreview.api.Note(
                replyto=note_edit['note']['id'],
                content={
                    'message': { 'value': 'Chat comment number 5' }
                }
            )
        )

        helpers.await_queue_edit(openreview_client, edit_id=note_edit['id'])

        assert len(openreview_client.get_messages(to='reviewer1@icml.cc', subject='[ICML 2023] New messages in committee members chat for submission 1: Paper title 1 Version 2 UPDATED')) == 0
        assert len(openreview_client.get_messages(to='reviewer2@icml.cc', subject='[ICML 2023] New messages in committee members chat for submission 1: Paper title 1 Version 2 UPDATED')) == 0
        assert len(openreview_client.get_messages(to='melisa@icml.cc', subject='[ICML 2023] New messages in committee members chat for submission 1: Paper title 1 Version 2 UPDATED')) == 0
        assert len(openreview_client.get_messages(to='reviewer3@icml.cc', subject='[ICML 2023] New messages in committee members chat for submission 1: Paper title 1 Version 2 UPDATED')) == 0
        assert len(openreview_client.get_messages(to='reviewer4@yahoo.com', subject='[ICML 2023] New messages in committee members chat for submission 1: Paper title 1 Version 2 UPDATED')) == 0
        assert len(openreview_client.get_messages(to='rachel_bis@icml.cc', subject='[ICML 2023] New messages in committee members chat for submission 1: Paper title 1 Version 2 UPDATED')) == 0
        assert len(openreview_client.get_messages(to='ac2@icml.cc', subject='[ICML 2023] New messages in committee members chat for submission 1: Paper title 1 Version 2 UPDATED')) == 0
        assert len(openreview_client.get_messages(to='sac2@icml.cc', subject='[ICML 2023] New messages in committee members chat for submission 1: Paper title 1 Version 2 UPDATED')) == 0
        assert len(openreview_client.get_messages(to='pc@icml.cc', subject='[ICML 2023] New messages in committee members chat for submission 1: Paper title 1 Version 2 UPDATED')) == 0

        note_edit = sac_client.post_note_edit(
            invitation='ICML.cc/2023/Conference/Submission1/-/Chat',
            signatures=['ICML.cc/2023/Conference/Submission1/Senior_Area_Chairs'],
            note=openreview.api.Note(
                replyto=note_edit['note']['id'],
                content={
                    'message': { 'value': 'Chat comment number 6' }
                }
            )
        )

        helpers.await_queue_edit(openreview_client, edit_id=note_edit['id'])

        assert len(openreview_client.get_messages(to='reviewer1@icml.cc', subject='[ICML 2023] New messages in committee members chat for submission 1: Paper title 1 Version 2 UPDATED')) == 1
        assert len(openreview_client.get_messages(to='reviewer2@icml.cc', subject='[ICML 2023] New messages in committee members chat for submission 1: Paper title 1 Version 2 UPDATED')) == 1
        assert len(openreview_client.get_messages(to='melisa@icml.cc', subject='[ICML 2023] New messages in committee members chat for submission 1: Paper title 1 Version 2 UPDATED')) == 1
        assert len(openreview_client.get_messages(to='reviewer3@icml.cc', subject='[ICML 2023] New messages in committee members chat for submission 1: Paper title 1 Version 2 UPDATED')) == 1
        assert len(openreview_client.get_messages(to='reviewer4@yahoo.com', subject='[ICML 2023] New messages in committee members chat for submission 1: Paper title 1 Version 2 UPDATED')) == 1
        assert len(openreview_client.get_messages(to='rachel_bis@icml.cc', subject='[ICML 2023] New messages in committee members chat for submission 1: Paper title 1 Version 2 UPDATED')) == 1
        assert len(openreview_client.get_messages(to='ac2@icml.cc', subject='[ICML 2023] New messages in committee members chat for submission 1: Paper title 1 Version 2 UPDATED')) == 1
        assert len(openreview_client.get_messages(to='sac2@icml.cc', subject='[ICML 2023] New messages in committee members chat for submission 1: Paper title 1 Version 2 UPDATED')) == 0
        assert len(openreview_client.get_messages(to='pc@icml.cc', subject='[ICML 2023] New messages in committee members chat for submission 1: Paper title 1 Version 2 UPDATED')) == 0

        ## Add tag emoji
        tag = sac_client.post_tag(openreview.api.Tag(
            invitation='ICML.cc/2023/Conference/Submission1/-/Chat_Reaction',
            signature='ICML.cc/2023/Conference/Submission1/Senior_Area_Chairs',
            label='😄',
            note=note_edit['note']['id']
        ))

        tags = openreview_client.get_tags(invitation='ICML.cc/2023/Conference/Submission1/-/Chat_Reaction', mintmdate=tag.tmdate - 5000)
        assert len(tags) == 1

        reviewer_client = openreview.api.OpenReviewClient(username='reviewer2@icml.cc', password=helpers.strong_password)

        anon_groups = reviewer_client.get_groups(prefix='ICML.cc/2023/Conference/Submission1/Reviewer_', signatory='~Reviewer_ICMLTwo1')
        anon_group_id = anon_groups[0].id

        ## Add tag emoji
        tag = reviewer_client.post_tag(openreview.api.Tag(
            invitation='ICML.cc/2023/Conference/Submission1/-/Chat_Reaction',
            signature=anon_group_id,
            label='👍',
            note=note_edit['note']['id']
        ))

        tags = openreview_client.get_tags(invitation='ICML.cc/2023/Conference/Submission1/-/Chat_Reaction', mintmdate=tag.tmdate - 5000)
        assert len(tags) == 2

        submission = openreview_client.get_notes(invitation='ICML.cc/2023/Conference/-/Submission', number=4)[0]

        reviewer_client = openreview.api.OpenReviewClient(username='reviewer1@icml.cc', password=helpers.strong_password)

        anon_groups = reviewer_client.get_groups(prefix='ICML.cc/2023/Conference/Submission4/Reviewer_', signatory='~Reviewer_ICMLOne1')
        anon_group_id = anon_groups[0].id

        # assert there is no error if Reviewer/Submitted group does not exist
        invitation = openreview_client.get_invitation('ICML.cc/2023/Conference/Submission4/-/Chat')
        assert invitation.date_processes[0].get('dates') == []

        note_edit = reviewer_client.post_note_edit(
            invitation='ICML.cc/2023/Conference/Submission4/-/Chat',
            signatures=[anon_group_id],
            note=openreview.api.Note(
                replyto=submission.id,
                content={
                    'message': { 'value': 'Hi AC, I will be late in completing my review.' }
                }
            )
        )

        helpers.await_queue_edit(openreview_client, edit_id=note_edit['id'])

        invitation = openreview_client.get_invitation('ICML.cc/2023/Conference/Submission4/-/Chat')
        assert invitation.date_processes[0].get('dates') is None
        assert invitation.date_processes[0].get('cron') == '0 */4 * * *'

        ## Disable chat
        pc_client=openreview.Client(username='pc@icml.cc', password=helpers.strong_password)
        request_form=pc_client.get_notes(invitation='openreview.net/Support/-/Request_Form')[0]

        # Post an official comment stage note
        now = datetime.datetime.now()
        start_date = now - datetime.timedelta(days=2)
        end_date = now + datetime.timedelta(days=3)
        comment_stage_note = pc_client.post_note(openreview.Note(
            content={
                'commentary_start_date': start_date.strftime('%Y/%m/%d'),
                'commentary_end_date': end_date.strftime('%Y/%m/%d'),
                'participants': ['Program Chairs', 'Assigned Senior Area Chairs', 'Assigned Area Chairs', 'Assigned Reviewers'],
                'additional_readers': ['Program Chairs', 'Assigned Senior Area Chairs', 'Assigned Area Chairs', 'Assigned Reviewers', 'Assigned Submitted Reviewers'],
                'email_program_chairs_about_official_comments': 'No, do not email PCs for each official comment made in the venue',
                'enable_chat_between_committee_members': 'No, do not enable chat between committee members'
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
        helpers.await_queue_edit(openreview_client, 'ICML.cc/2023/Conference/-/Official_Comment-0-1', count=5)
        helpers.await_queue_edit(openreview_client, 'ICML.cc/2023/Conference/-/Chat-0-1', count=2)
        helpers.await_queue_edit(openreview_client, 'ICML.cc/2023/Conference/-/Chat_Reaction-0-1', count=2)

        chat_invitations = openreview_client.get_invitations(invitation='ICML.cc/2023/Conference/-/Chat')
        assert len(chat_invitations) == 0

        chat_reaction_invitations = openreview_client.get_invitations(invitation='ICML.cc/2023/Conference/-/Chat_Reaction')
        assert len(chat_reaction_invitations) == 0     

        submission_invitation = openreview_client.get_invitation('ICML.cc/2023/Conference/-/Submission')
        assert submission_invitation.reply_forum_views is None


    def test_rename_domain(self, client, openreview_client, helpers):

        request_form=client.get_notes(invitation='openreview.net/Support/-/Request_Form')[0]

        openreview_client.rename_venue('ICML.cc/2023/Conference', 'ICML.org/2023/Conference', request_form.id)

        helpers.await_queue(openreview_client, queue_names=['internalQueueStatus'])

        assert openreview.tools.get_group(openreview_client, 'ICML.org/2023/Conference')
        assert openreview.tools.get_group(openreview_client, 'ICML.org/2023/Conference/Authors')
        assert openreview.tools.get_group(openreview_client, 'ICML.org/2023/Conference/Authors/Accepted')
        assert openreview.tools.get_group(openreview_client, 'ICML.org/2023/Conference/Reviewers')
        assert openreview.tools.get_group(openreview_client, 'ICML.org/2023/Conference/Area_Chairs')
        assert openreview.tools.get_group(openreview_client, 'ICML.org/2023/Conference/Senior_Area_Chairs')
        assert openreview.tools.get_group(openreview_client, 'ICML.org/2023/Conference/Program_Chairs')

        assert openreview.tools.get_invitation(openreview_client, 'ICML.org/2023/Conference/-/Submission')
        assert openreview.tools.get_invitation(openreview_client, 'ICML.org/2023/Conference/-/Desk_Rejected_Submission')
        assert openreview.tools.get_invitation(openreview_client, 'ICML.org/2023/Conference/-/Withdrawn_Submission')
        assert openreview.tools.get_invitation(openreview_client, 'ICML.org/2023/Conference/-/Official_Comment')
        assert openreview.tools.get_invitation(openreview_client, 'ICML.org/2023/Conference/-/Chat')
        assert openreview.tools.get_invitation(openreview_client, 'ICML.org/2023/Conference/-/Chat_Reaction')
        assert openreview.tools.get_invitation(openreview_client, 'ICML.org/2023/Conference/-/Official_Review')
        assert openreview.tools.get_invitation(openreview_client, 'ICML.org/2023/Conference/-/Meta_Review')

        assert not openreview.tools.get_group(openreview_client, 'ICML.cc/2023/Conference')
        assert not openreview.tools.get_group(openreview_client, 'ICML.cc/2023/Conference/Authors')
        assert not openreview.tools.get_group(openreview_client, 'ICML.cc/2023/Conference/Authors/Accepted')
        assert not openreview.tools.get_group(openreview_client, 'ICML.cc/2023/Conference/Reviewers')
        assert not openreview.tools.get_group(openreview_client, 'ICML.cc/2023/Conference/Area_Chairs')
        assert not openreview.tools.get_group(openreview_client, 'ICML.cc/2023/Conference/Senior_Area_Chairs')
        assert not openreview.tools.get_group(openreview_client, 'ICML.cc/2023/Conference/Program_Chairs')

        assert not openreview.tools.get_invitation(openreview_client, 'ICML.cc/2023/Conference/-/Submission')
        assert not openreview.tools.get_invitation(openreview_client, 'ICML.cc/2023/Conference/-/Desk_Rejected_Submission')
        assert not openreview.tools.get_invitation(openreview_client, 'ICML.cc/2023/Conference/-/Withdrawn_Submission')
        assert not openreview.tools.get_invitation(openreview_client, 'ICML.cc/2023/Conference/-/Official_Comment')
        assert not openreview.tools.get_invitation(openreview_client, 'ICML.cc/2023/Conference/-/Chat')
        assert not openreview.tools.get_invitation(openreview_client, 'ICML.cc/2023/Conference/-/Chat_Reaction')
        assert not openreview.tools.get_invitation(openreview_client, 'ICML.cc/2023/Conference/-/Official_Review')
        assert not openreview.tools.get_invitation(openreview_client, 'ICML.cc/2023/Conference/-/Meta_Review')        
