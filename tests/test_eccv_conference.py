from __future__ import absolute_import, division, print_function, unicode_literals
import openreview
import pytest
import requests
import datetime
import calendar
import time
import os
import re
import csv
import random
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import NoSuchElementException

class TestECCVConference():

    @pytest.fixture(scope="class")
    def conference(self, client):
        now = datetime.datetime.utcnow()
        #pc_client = openreview.Client(username='pc@eccv.org', password='1234')
        builder = openreview.conference.ConferenceBuilder(client)
        assert builder, 'builder is None'

        builder.set_conference_id('thecvf.com/ECCV/2020/Conference')
        builder.set_conference_short_name('ECCV 2020')
        builder.set_default_reviewers_load(7)
        builder.has_area_chairs(True)
        builder.set_homepage_header({
            'title': '2020 European Conference on Computer Vision',
            'subtitle': 'ECCV 2020',
            'deadline': '',
            'date': 'Aug 23 2020',
            'website': 'https://eccv2020.eu/',
            'location': 'SEC, Glasgow',
            'instructions': '''<p class="dark">
            <strong>New: Extended paper pre-registration</strong>
            <br> Please note that during the extended pre-registration period all registration problems will have to be resolved by the deadline of 5 March 2020 (23:59 UTC-0) (identical to the paper submission deadline). We will not be able to make any exceptions after this deadline.
            <br>We are looking forward to your submissions.
            </p>
            <p class="dark">
            <strong>Instructions:</strong> <a href="https://eccv2020.eu/author-instructions/" target="_blank">https://eccv2020.eu/author-instructions/</a>.
            You can update the information on this form at any time before the deadline.</p>
            <p class="dark">Deadline: 5 March 2020 (23:59 UTC-0)</p>''',
            'contact': 'eccv20program@gmail.com'
        })

        # Reviewers
        reviewer_registration_tasks = {
            'profile_confirmed': {
                'required': True,
                'description': 'I confirm that I updated my OpenReview profile.',
                'value-checkbox': 'Yes',
                'order': 1
            },
            'expertise_confirmed': {
                'required': True,
                'description': 'I confirm that I verified my expertise.',
                'value-checkbox': 'Yes',
                'order': 1
            },
            'TPMS_registration_confirmed' : {
                'required': True,
                'description': 'I confirm that I updated my TPMS account.',
                'value-checkbox': 'Yes',
                'order': 3
            },
            'reviewer_instructions_confirm' : {
                'required': True,
                'description': 'I confirm that I will adhere to the reviewer instructions and will do my best to provide the agreed upon number of reviews in time.',
                'value-checkbox': 'Yes',
                'order': 4
            },
            'emergency_review_count' : {
                'required': True,
                'description': 'Decide whether you can and want to serve as emergency reviewer. Select how many reviews you can volunteer as emergency reviewer.',
                'value-radio': ['0', '1', '2'],
                'order': 5,
                'default': '0'
            }
        }

        ac_registration_tasks = {
            'profile_confirmed': {
                'required': True,
                'description': 'I confirm that I updated my OpenReview profile.',
                'value-checkbox': 'Yes',
                'order': 1
            },
            'expertise_confirmed': {
                'required': True,
                'description': 'I confirm that I verified my expertise.',
                'value-checkbox': 'Yes',
                'order': 1
            },
            'TPMS_registration_confirmed' : {
                'required': True,
                'description': 'I confirm that I updated my TPMP account',
                'value-checkbox': 'Yes',
                'order': 3}
        }

        reviewer_instructions = '''
1. In order to avoid conflicts of interest in reviewing, we ask that all reviewers take a moment to update their OpenReview profiles with their latest information regarding email addresses, work history and professional relationships: https://openreview.net/profile?mode=edit

2. We automatically populated your profile with your published papers. These represent your expertise and will be used to match submissions to you. Please take a moment to verify if the selection of papers is representative of your expertise and modify it if necessary: https://openreview.net/invitation?id=thecvf.com/ECCV/2020/Conference/-/Expertise_Selection

3. Full paper matching will be done via the Toronto paper matching system (TPMS). Please update your TPMS profile so that it represents your expertise well: http://torontopapermatching.org/webapp/profileBrowser/login/
If you don't have a TPMS account yet, you can create one here: http://torontopapermatching.org/webapp/profileBrowser/register/
Ensure that the email you use for your TPMS profile is listed as one of the emails in your OpenReview profile.

4. Please check the reviewer instructions: https://eccv2020.eu/reviewer-instructions/

5. Emergency reviewers are important to ensure that all papers receive 3 reviews even if some reviewers cannot submit their reviews in time (e.g. due to sickness). If you know for sure that you will be able to review 1 or 2 papers within 72-96 hours in the time from May 15 to May 19, you can volunteer as emergency reviewer. We will reduce your normal load by the number of papers you agree to handle as emergency reviewer. Every emergency review will increase your reviewer score in addition to the score assigned by the area chair.
        '''

        ac_instructions = '''
1. In order to avoid conflicts of interest in reviewing, we ask that all reviewers take a moment to update their OpenReview profiles with their latest information regarding email addresses, work history and professional relationships: https://openreview.net/profile?mode=edit

2. We automatically populated your profile with your published papers. These represent your expertise and will be used to match submissions to you. Please take a moment to verify if the selection of papers is representative of your expertise and modify it if necessary: https://openreview.net/invitation?id=thecvf.com/ECCV/2020/Conference/-/Expertise_Selection

3. Full paper matching will be done via the Toronto paper matching system (TPMS). Please update your TPMS profile so that it represents your expertise well: http://torontopapermatching.org/webapp/profileBrowser/login/
If you don't have a TPMS account yet, you can create one here: http://torontopapermatching.org/webapp/profileBrowser/register/
Ensure that the email you use for your TPMS profile is listed as one of the emails in your OpenReview profile.
        '''
        builder.set_registration_stage(committee_id='thecvf.com/ECCV/2020/Conference/Reviewers',
            name='Profile_Confirmation',
            additional_fields = reviewer_registration_tasks,
            due_date = now + datetime.timedelta(minutes = 40),
            instructions=reviewer_instructions
        )
        builder.set_registration_stage(committee_id='thecvf.com/ECCV/2020/Conference/Area_Chairs',
            name='Profile_Confirmation',
            additional_fields = ac_registration_tasks,
            due_date = now + datetime.timedelta(minutes = 40),
            instructions=ac_instructions
        )
        builder.set_expertise_selection_stage(due_date = now + datetime.timedelta(minutes = 10))
        builder.set_submission_stage(double_blind = True,
            public = False,
            due_date = now + datetime.timedelta(minutes = 10),
            additional_fields= {
                'title': {
                    'description': 'Title of paper. Add TeX formulas using the following formats: $In-line Formula$ or $$Block Formula$$',
                    'order': 1,
                    'value-regex': '.{1,250}',
                    'required':True
                },
                "authors": {
                    "description": "Comma separated list of author names.",
                    "order": 2,
                    "values-regex": "[^;,\\n]+(,[^,\\n]+)*",
                    "required":True,
                    "hidden":True
                },
                "authorids": {
                    "description": "Search for authors by first and last name or by email address. Authors cannot be added after the deadline, so be sure to add all the authors of the paper. Take care to confirm that everyone added is actually a co-author, as there may be multiple OpenReview profiles with the same name.",
                    "order": 3,
                    "values-regex": "~.*|.*",
                    "required":True
                },
                'abstract': {
                    'description': 'Abstract of paper. Add TeX formulas using the following formats: $In-line Formula$ or $$Block Formula$$',
                    'order': 4,
                    'value-regex': '[\\S\\s]{1,5000}',
                    'required':False
                },
                'TL;DR': {
                    'description': '\"Too Long; Didn\'t Read\": a short sentence describing your paper',
                    'order': 5,
                    'value-regex': '[^\\n]{0,250}',
                    'required':False
                },
                'subject_areas': {
                    'description': 'Select up to three subject areas.',
                    'order': 6,
                    'values-dropdown': [
                        "3D from Multi-view and Sensors",
                        "3D Point Clouds",
                        "3D from Single Images",
                        "3D Reconstruction",
                        "Action Recognition, Understanding",
                        "Adversarial Learning",
                        "Biologically Inspired Vision",
                        "Biomedical Image Processing",
                        "Biometrics",
                        "Computational Photography",
                        "Computer Vision for General Medical,  Biological and Cell Microscopy",
                        "Computer Vision Theory",
                        "Datasets and Evaluation",
                        "Deep Learning: Applications, Methodology, and Theory",
                        "Document Analysis RGBD Sensors and Analytics",
                        "Face, Gesture, and Body Pose",
                        "Human Computer Interaction",
                        "Image and Video Synthesis",
                        "Large Scale Methods",
                        "Low-level Vision",
                        "Machine Learning",
                        "Motion and Tracking",
                        "Optimization Methods",
                        "Physics-based Vision and Shape-from-X Recognition: Detection, Categorization, Retrieval",
                        "Pose Estimation",
                        "Recognition: Detection, Categorization, Indexing and Matching",
                        "Remote Sensing and Hyperspectral Imaging",
                        "Representation Learning",
                        "Robotics and Driving Scene Analysis",
                        "Scene Understanding",
                        "Security/Surveillance",
                        "Semi- and weakly-supervised Learning",
                        "Segmentation, Grouping and Shape",
                        "Statistical Learning",
                        "Stereo/Depth Estimation",
                        "Tracking",
                        "Transfer Learning",
                        "Unsupervised Learning",
                        "Video Analytics Vision + Graphics Vision + Language",
                        "Virtual and Augmented Reality",
                        "Vision and Language",
                        "Vision for Robotics, Graphics",
                        "Visual Reasoning Vision Applications and Systems"
                                    ],
                    'required':False
                },
                'pdf': {
                    'description': 'Upload a PDF file that ends with .pdf',
                    'order': 9,
                    'value-file': {
                        'fileTypes': ['pdf'],
                        'size': 50
                    },
                    'required':False
                },
                "author_agreement": {
                    "value-checkbox": "All authors agree with the author guidelines of ECCV 2020.",
                    'order': 10,
                    "required": True
                },
                "TPMS_agreement": {
                    "value-checkbox": "All authors agree that the manuscript can be processed by TPMS for paper matching.",
                    'order': 11,
                    "required": True
                }
            },
            remove_fields=['keywords'],
            withdrawn_submission_public=False,
            withdrawn_submission_reveal_authors=False,
            email_pcs_on_withdraw=True,
            desk_rejected_submission_public=False,
            desk_rejected_submission_reveal_authors=False,
            bidding_enabled=True)


        instructions = '''<p class="dark"><strong>Instructions:</strong></p>
        <ul>
            <li>
                Please indicate your <strong>level of interest</strong> in
                reviewing the submitted papers below,
                on a scale from "Very Low" interest to "Very High" interest. Papers were automatically pre-ranked using the expertise information in your profile.
            </li>
            <li>
                Bid on as many papers as possible to correct errors of this automatic procedure.
            </li>
            <li>
                Bidding on the top ranked papers removes false positives.
            </li>
            <li>
                You can use the search field to find papers by keywords from the title or abstract to reduce false negatives.
            </li>
            <li>
                Ensure that you have at least <strong>{request_count} bids</strong>, which are "Very High" or "High".
            </li>
            <li>
                Papers for which you have a conflict of interest are not shown.
            </li>
        </ul>
        <br>'''
        builder.set_bid_stage('thecvf.com/ECCV/2020/Conference/Reviewers', due_date =  now + datetime.timedelta(minutes = 1440), request_count = 40, score_ids=['thecvf.com/ECCV/2020/Conference/Reviewers/-/Affinity_Score'], instructions = instructions)
        builder.set_bid_stage('thecvf.com/ECCV/2020/Conference/Area_Chairs', due_date =  now + datetime.timedelta(minutes = 1440), request_count = 60, score_ids=['thecvf.com/ECCV/2020/Conference/Area_Chairs/-/Affinity_Score'], instructions = instructions)
        #builder.use_legacy_anonids(True)
        conference = builder.get_result()
        conference.set_program_chairs(['pc@eccv.org'])
        return conference


    def test_create_conference(self, client, helpers):

        builder = openreview.conference.ConferenceBuilder(client)
        assert builder, 'builder is None'

        builder.set_conference_id('thecvf.com/ECCV/2020/Conference')
        builder.has_area_chairs(True)
        #builder.use_legacy_anonids(True)
        conference = builder.get_result()
        assert conference, 'conference is None'
        conference.set_program_chairs(['pc@eccv.org'])

        pc_client = helpers.create_user('pc@eccv.org', 'Program', 'ECCVChair')

        group = pc_client.get_group('thecvf.com/ECCV/2020/Conference')
        assert group
        assert group.web

        pc_group = pc_client.get_group('thecvf.com/ECCV/2020/Conference/Program_Chairs')
        assert pc_group
        assert pc_group.web

    def test_recruit_reviewer(self, conference, client, helpers, selenium, request_page):

        result = conference.recruit_reviewers(['test_reviewer_eccv@mail.com', 'mohit+1@mail.com'],
                                              reduced_load_on_decline = ['4','5','6','7'],
                                              default_load = 7)
        assert result
        assert len(result['invited']) == 2
        assert 'test_reviewer_eccv@mail.com' in result['invited']
        assert 'mohit+1@mail.com' in result['invited']

        messages = client.get_messages(to = 'mohit+1@mail.com', subject = '[ECCV 2020]: Invitation to serve as Reviewer')
        text = messages[0]['content']['text']
        assert 'Dear invitee,' in text
        assert 'You have been nominated by the program chair committee of ECCV 2020 to serve as Reviewer' in text

        # Test to check that a user is not able to accept/decline if they are not a part of the invited group
        reject_url = re.search('href="https://.*response=No"', text).group(0)[6:-1].replace('https://openreview.net', 'http://localhost:3030').replace('&amp;', '&')
        accept_url = re.search('href="https://.*response=Yes"', text).group(0)[6:-1].replace('https://openreview.net', 'http://localhost:3030').replace('&amp;', '&')


        # Removing reviewer from the invited group
        invited_group = client.remove_members_from_group('thecvf.com/ECCV/2020/Conference/Reviewers/Invited', 'mohit+1@mail.com')
        assert len(invited_group.members) == 1

        request_page(selenium, reject_url, alert=True)
        declined_group = client.get_group(id='thecvf.com/ECCV/2020/Conference/Reviewers/Declined')
        assert len(declined_group.members) == 0

        request_page(selenium, accept_url, alert=True)
        accepted_group = client.get_group(id='thecvf.com/ECCV/2020/Conference/Reviewers')
        assert len(accepted_group.members) == 0

        # Placing the reviewer back
        invited_group = client.add_members_to_group('thecvf.com/ECCV/2020/Conference/Reviewers/Invited', 'mohit+1@mail.com')
        assert len(invited_group.members) == 2

        request_page(selenium, reject_url, alert=True)
        notes = selenium.find_element_by_id("notes")
        assert notes
        messages = notes.find_elements_by_tag_name("h3")
        assert messages
        assert 'You have declined the invitation from 2020 European Conference on Computer Vision.' == messages[0].text
        assert 'In case you only declined because you think you cannot handle the maximum load of papers, you can reduce your load slightly. Be aware that this will decrease your overall score for an outstanding reviewer award, since all good reviews will accumulate a positive score. You can request a reduced reviewer load by clicking here: Request reduced load' == messages[1].text

        group = client.get_group('thecvf.com/ECCV/2020/Conference/Reviewers')
        assert group
        assert len(group.members) == 0

        group = client.get_group('thecvf.com/ECCV/2020/Conference/Reviewers/Declined')
        assert group
        assert len(group.members) == 1
        assert 'mohit+1@mail.com' in group.members

        messages = client.get_messages(to='mohit+1@mail.com', subject='[ECCV 2020] Reviewer Invitation declined')
        assert messages
        assert len(messages)
        text = messages[0]['content']['text']
        assert 'You have declined the invitation to become a Reviewer for ECCV 2020.' in text
        assert 'If you would like to change your decision, please click the Accept link in the previous invitation email.' in text
        assert 'In case you only declined because you think you cannot handle the maximum load of papers, you can reduce your load slightly. Be aware that this will decrease your overall score for an outstanding reviewer award, since all good reviews will accumulate a positive score. You can request a reduced reviewer load by clicking here:' in text

        ## Reduce the load of Mohit
        notes = client.get_notes(invitation='thecvf.com/ECCV/2020/Conference/-/Recruit_Reviewers', content={'user': 'mohit+1@mail.com'})
        assert notes
        assert len(notes) == 1

        client.post_note(openreview.Note(
            invitation='thecvf.com/ECCV/2020/Conference/Reviewers/-/Reduced_Load',
            readers=['thecvf.com/ECCV/2020/Conference', 'mohit+1@mail.com'],
            writers=['thecvf.com/ECCV/2020/Conference'],
            signatures=['(anonymous)'],
            content={
                'user': 'mohit+1@mail.com',
                'key': notes[0].content['key'],
                'response': 'Yes',
                'reviewer_load': '4'
            }
        ))

        messages = client.get_messages(to = 'test_reviewer_eccv@mail.com', subject = '[ECCV 2020]: Invitation to serve as Reviewer')
        text = messages[0]['content']['text']

        accept_url = re.search('href="https://.*response=Yes"', text).group(0)[6:-1].replace('https://openreview.net', 'http://localhost:3030').replace('&amp;', '&')

        request_page(selenium, accept_url, alert=True)

        group = client.get_group(conference.get_reviewers_id())
        assert group
        assert len(group.members) == 2
        assert group.members[0] == 'mohit+1@mail.com'
        assert group.members[1] == 'test_reviewer_eccv@mail.com'

    def test_expertise_selection(self, conference, helpers, selenium, request_page):

        reviewer_client = helpers.create_user('test_reviewer_eccv@mail.com', 'ReviewerFirstName', 'Eccv')
        reviewer_tasks_url = 'http://localhost:3030/group?id=' + conference.get_reviewers_id() + '#reviewer-tasks'
        request_page(selenium, reviewer_tasks_url, reviewer_client.token)

        assert selenium.find_element_by_link_text('Expertise Selection')

        request_page(selenium, 'http://localhost:3030/invitation?id=thecvf.com/ECCV/2020/Conference/-/Expertise_Selection', reviewer_client.token)
        header = selenium.find_element_by_id('header')
        assert header
        notes = header.find_elements_by_class_name("description")
        assert notes
        assert len(notes) == 1
        assert notes[0].text == '''Listed below are all the papers you have authored that exist in the OpenReview database.

By default, we consider all of these papers to formulate your expertise. Please click on "Exclude" for papers that you do NOT want to be used to represent your expertise.

Your previously authored papers from selected conferences were imported automatically from DBLP.org. The keywords in these papers will be used to rank submissions for you during the bidding process, and to assign submissions to you during the review process. If there are DBLP papers missing, you can add them by editing your OpenReview profile and then clicking on 'Add DBLP Papers to Profile'.

Papers not automatically included as part of this import process can be uploaded by using the Upload button. Make sure that your email is part of the "authorids" field of the upload form. Otherwise the paper will not appear in the list, though it will be included in the recommendations process. Only upload papers co-authored by you.

Please contact info@openreview.net with any questions or concerns about this interface, or about the expertise scoring process.'''

    def test_open_registration(self, conference, helpers, selenium, request_page):

        reviewer_client = openreview.Client(username='test_reviewer_eccv@mail.com', password='1234')
        reviewer_tasks_url = 'http://localhost:3030/group?id=' + conference.get_reviewers_id() + '#reviewer-tasks'
        request_page(selenium, reviewer_tasks_url, reviewer_client.token)

        assert selenium.find_element_by_link_text('Reviewer Profile Confirmation')

        registration_notes = reviewer_client.get_notes(invitation = 'thecvf.com/ECCV/2020/Conference/Reviewers/-/Profile_Confirmation_Form')
        assert registration_notes
        assert len(registration_notes) == 1

        registration_forum = registration_notes[0].forum

        registration_note = reviewer_client.post_note(
            openreview.Note(
                invitation = 'thecvf.com/ECCV/2020/Conference/Reviewers/-/Profile_Confirmation',
                forum = registration_forum,
                replyto = registration_forum,
                content = {
                    'profile_confirmed': 'Yes',
                    'expertise_confirmed': 'Yes',
                    'TPMS_registration_confirmed': 'Yes',
                    'reviewer_instructions_confirm': 'Yes',
                    'emergency_review_count': '0'
                },
                signatures = [
                    '~ReviewerFirstName_Eccv1'
                ],
                readers = [
                    conference.get_id(),
                    '~ReviewerFirstName_Eccv1'
                ],
                writers = [
                    conference.get_id(),
                    '~ReviewerFirstName_Eccv1'
                ]
            ))
        assert registration_note


        request_page(selenium, 'http://localhost:3030/group?id=thecvf.com/ECCV/2020/Conference/Reviewers', reviewer_client.token)
        header = selenium.find_element_by_id('header')
        assert header
        notes = header.find_elements_by_class_name("description")
        assert notes
        assert len(notes) == 1
        assert notes[0].text == 'This page provides information and status updates for the ECCV 2020. It will be regularly updated as the conference progresses, so please check back frequently.\nYou have agreed to review up to 7 papers.'

        reviewer2_client = helpers.create_user('mohit+1@mail.com', 'Mohit', 'EccvReviewer')
        request_page(selenium, 'http://localhost:3030/group?id=thecvf.com/ECCV/2020/Conference/Reviewers', reviewer2_client.token)
        header = selenium.find_element_by_id('header')
        assert header
        notes = header.find_elements_by_class_name("description")
        assert notes
        assert len(notes) == 1
        assert notes[0].text == 'This page provides information and status updates for the ECCV 2020. It will be regularly updated as the conference progresses, so please check back frequently.\nYou have agreed to review up to 4 papers.'

        #Area Chairs
        conference.set_area_chairs(['test_ac_eccv@mail.com'])
        ac_client = helpers.create_user('test_ac_eccv@mail.com', 'AreachairFirstName', 'Eccv')
        reviewer_tasks_url = 'http://localhost:3030/group?id=thecvf.com/ECCV/2020/Conference/Area_Chairs#areachair-tasks'
        request_page(selenium, reviewer_tasks_url, ac_client.token)

        assert selenium.find_element_by_link_text('Area Chair Profile Confirmation')

    def test_submission_additional_files(self, conference, test_client):

        domains = ['umass.edu', 'umass.edu', 'fb.com', 'umass.edu', 'google.com', 'mit.edu']
        for i in range(1,6):
            note = openreview.Note(invitation = conference.get_submission_id(),
                readers = ['thecvf.com/ECCV/2020/Conference', 'test@mail.com', 'peter@mail.com', 'andrew@' + domains[i], '~SomeFirstName_User1'],
                writers = [conference.id, '~SomeFirstName_User1', 'peter@mail.com', 'andrew@' + domains[i]],
                signatures = ['~SomeFirstName_User1'],
                content = {
                    'title': 'Paper title ' + str(i) ,
                    'abstract': 'This is an abstract ' + str(i),
                    'authorids': ['test@mail.com', 'peter@mail.com', 'andrew@' + domains[i]],
                    'authors': ['SomeFirstName User', 'Peter SomeLastName', 'Andrew Mc'],
                    'author_agreement': 'All authors agree with the author guidelines of ECCV 2020.',
                    'TPMS_agreement': 'All authors agree that the manuscript can be processed by TPMS for paper matching.'
                }
            )
            test_client.post_note(note)

    def test_submission_edit(self, conference, client, helpers, test_client):

        existing_notes = client.get_notes(invitation = conference.get_submission_id())
        assert len(existing_notes) == 5

        helpers.await_queue()
        note = existing_notes[0]
        process_logs = client.get_process_logs(id = note.id)
        assert len(process_logs) == 1
        assert process_logs[0]['status'] == 'ok'

        messages = client.get_messages(subject = 'ECCV 2020 has received your submission titled ' + note.content['title'])
        assert len(messages) == 3
        recipients = [m['content']['to'] for m in messages]
        assert 'test@mail.com' in recipients

        note.content['title'] = 'I have been updated'
        test_client.post_note(note)

        helpers.await_queue()
        note = client.get_note(note.id)

        process_logs = client.get_process_logs(id = note.id)
        assert len(process_logs) == 2
        assert process_logs[0]['status'] == 'ok'
        assert process_logs[1]['status'] == 'ok'

        messages = client.get_messages(subject = 'ECCV 2020 has received your submission titled I have been updated')
        assert len(messages) == 3
        recipients = [m['content']['to'] for m in messages]
        assert 'test@mail.com' in recipients
        assert 'peter@mail.com' in recipients
        assert 'andrew@mit.edu' in recipients

        tauthor_message = [msg for msg in messages if msg['content']['to'] == note.tauthor][0]
        assert tauthor_message
        text = tauthor_message['content']['text']
        assert 'Your submission to ECCV 2020 has been updated.' in text
        assert 'Submission Number: ' + str(note.number) in text
        assert 'Title: ' + note.content['title'] in text
        assert 'Abstract: ' + note.content['abstract'] in text
        assert 'To view your submission, click here:' in text

        other_author_messages = [msg for msg in messages if msg['content']['to'] != note.tauthor]
        assert len(other_author_messages) == 2
        text = other_author_messages[0]['content']['text']
        assert text == f'<p>Your submission to ECCV 2020 has been updated.</p>\n<p>Submission Number: 5</p>\n<p>Title: I have been updated</p>\n<p>Abstract: This is an abstract 5</p>\n<p>To view your submission, click here: <a href=\"http://localhost:3030/forum?id={note.id}\">http://localhost:3030/forum?id={note.id}</a></p>\n<p>If you are not an author of this submission and would like to be removed, please contact the author who added you at <a href=\"mailto:test@mail.com\">test@mail.com</a></p>\n'

    def test_revise_additional_files(self, conference, client, test_client):

        conference.setup_post_submission_stage(force=True, hide_fields=['pdf', 'supplementary_material'])

        submissions = conference.get_submissions()
        assert submissions
        assert len(submissions) == 5
        note = submissions[0]
        now = datetime.datetime.utcnow()

        # check if conference is added in active_venues
        active_venues = client.get_group('active_venues')
        assert conference.id in active_venues.members

        for submission in submissions:
            id = conference.get_invitation_id('Supplementary_Material', submission.number)
            invitation = openreview.Invitation(
                id = id,
                duedate = openreview.tools.datetime_millis(now + datetime.timedelta(minutes = 40)),
                readers = ['everyone'],
                writers = [conference.id],
                signatures = [conference.id],
                invitees = [conference.get_authors_id(number=submission.number)],
                multiReply = False,
                reply = {
                    'forum': submission.original,
                    'referent': submission.original,
                    'readers': {
                        'values': [
                            conference.id, conference.get_authors_id(number=submission.number)
                        ]
                    },
                    'writers': {
                        'values': [
                            conference.id, conference.get_authors_id(number=submission.number)
                        ]
                    },
                    'signatures': {
                        'values-regex': '~.*'
                    },
                    'content': {
                        'supplementary_material': {
                            'order': 1,
                            'required': True,
                            'description': 'You can upload a single ZIP or a single PDF or a single MP4 file. Make sure that you do not use specialized codecs and the video runs on all computers. The maximum file size is 100MB.',
                            'value-file': {
                                'fileTypes': [
                                    'pdf',
                                    'zip',
                                    'mp4'
                                ],
                                'size': 100
                            }
                        }
                    }
                }
            )
            client.post_invitation(invitation)

        note = openreview.Note(invitation = 'thecvf.com/ECCV/2020/Conference/Paper5/-/Supplementary_Material',
            readers = note.writers + ['thecvf.com/ECCV/2020/Conference/Paper5/Authors'],
            writers = note.writers + ['thecvf.com/ECCV/2020/Conference/Paper5/Authors'],
            signatures = ['~SomeFirstName_User1'],
            referent = note.original,
            forum = note.original,
            content = {}
        )
        url = test_client.put_attachment(
            os.path.join(os.path.dirname(__file__), 'data/paper.pdf'),
            'thecvf.com/ECCV/2020/Conference/Paper5/-/Supplementary_Material',
            'supplementary_material'
        )
        note.content['supplementary_material'] = url
        test_client.post_note(note)

    def test_bid_stage(self, conference, helpers, selenium, request_page):

        reviewer_client = openreview.Client(username='test_reviewer_eccv@mail.com', password='1234')
        reviewer_tasks_url = 'http://localhost:3030/group?id=' + conference.get_reviewers_id() + '#reviewer-tasks'
        request_page(selenium, reviewer_tasks_url, reviewer_client.token)

        assert selenium.find_element_by_link_text('Reviewer Bid')

        request_page(selenium, 'http://localhost:3030/invitation?id=thecvf.com/ECCV/2020/Conference/Reviewers/-/Bid', reviewer_client.token)
        header = selenium.find_element_by_id('header')
        assert header
        notes = header.find_elements_by_tag_name("li")
        assert notes
        assert len(notes) == 6
        assert notes[4].text == 'Ensure that you have at least 40 bids, which are "Very High" or "High".'

        ac_client = openreview.Client(username='test_ac_eccv@mail.com', password='1234')
        request_page(selenium, 'http://localhost:3030/group?id=' + conference.get_area_chairs_id() + '#areachair-tasks', ac_client.token)

        assert selenium.find_element_by_link_text('Area Chair Bid')

        request_page(selenium, 'http://localhost:3030/invitation?id=thecvf.com/ECCV/2020/Conference/Area_Chairs/-/Bid', ac_client.token)
        header = selenium.find_element_by_id('header')
        assert header
        notes = header.find_elements_by_tag_name("li")
        assert notes
        assert len(notes) == 6
        assert notes[4].text == 'Ensure that you have at least 60 bids, which are "Very High" or "High".'

    def test_recommend_reviewers(self, conference, test_client, helpers, selenium, request_page):

        r1_client = helpers.create_user('reviewer1@fb.com', 'Reviewer', 'ECCV One')
        r2_client = helpers.create_user('reviewer2@google.com', 'Reviewer', 'ECCV Two')
        r3_client = helpers.create_user('reviewer3@umass.edu', 'Reviewer', 'ECCV Three')
        r4_client = helpers.create_user('reviewer4@mit.edu', 'Reviewer', 'ECCV Four')
        ac1_client = helpers.create_user('ac1@eccv.org', 'AreaChair', 'ECCV One')
        ac2_client = helpers.create_user('ac2@eccv.org', 'AreaChair', 'ECCV Two')

        conference.set_reviewers(['~Reviewer_ECCV_One1', '~Reviewer_ECCV_Two1', '~Reviewer_ECCV_Three1', '~Reviewer_ECCV_Four1'])
        conference.set_area_chairs(['~AreaChair_ECCV_One1', '~AreaChair_ECCV_Two1'])

        blinded_notes = conference.get_submissions()

        with open(os.path.join(os.path.dirname(__file__), 'data/reviewer_affinity_scores.csv'), 'w') as file_handle:
            writer = csv.writer(file_handle)
            for submission in blinded_notes:
                writer.writerow([submission.id, '~Reviewer_ECCV_One1', round(random.random(), 2)])
                writer.writerow([submission.id, '~Reviewer_ECCV_Two1', round(random.random(), 2)])
                writer.writerow([submission.id, '~Reviewer_ECCV_Three1', round(random.random(), 2)])
                writer.writerow([submission.id, '~Reviewer_ECCV_Four1', round(random.random(), 2)])

        with open(os.path.join(os.path.dirname(__file__), 'data/temp.csv'), 'w') as file_handle:
            writer = csv.writer(file_handle)
            for submission in blinded_notes:
                writer.writerow([submission.number, 'reviewer1@fb.com', round(random.random(), 2)])
                writer.writerow([submission.number, 'reviewer2@google.com', round(random.random(), 2)])
                writer.writerow([submission.number, 'reviewer3@umass.edu', round(random.random(), 2)])
                writer.writerow([submission.number, 'reviewer4@mit.edu', round(random.random(), 2)])


        conference.setup_matching(
            build_conflicts=True,
            affinity_score_file=os.path.join(os.path.dirname(__file__), 'data/reviewer_affinity_scores.csv'),
            tpms_score_file=os.path.join(os.path.dirname(__file__), 'data/temp.csv')
        )

        # Test adding reviewer after conflicts are built
        r5_client = helpers.create_user('reviewer5@fb.com', 'Reviewer', 'ECCV Five')
        conference.set_reviewers(['~Reviewer_ECCV_One1', '~Reviewer_ECCV_Two1', '~Reviewer_ECCV_Three1', '~Reviewer_ECCV_Four1', '~Reviewer_ECCV_Five1'])
        assert r5_client.get_edges_count() == 0
        conference.set_matching_conflicts(r5_client.profile.id)
        assert r5_client.get_edges_count() > 0
        with pytest.raises(openreview.OpenReviewException):
            conference.set_matching_conflicts('doesnotexist@mail.com')

        with open(os.path.join(os.path.dirname(__file__), 'data/ac_affinity_scores.csv'), 'w') as file_handle:
            writer = csv.writer(file_handle)
            for submission in blinded_notes:
                writer.writerow([submission.id, '~AreaChair_ECCV_One1', round(random.random(), 2)])
                writer.writerow([submission.id, '~AreaChair_ECCV_Two1', round(random.random(), 2)])

        with open(os.path.join(os.path.dirname(__file__), 'data/temp.csv'), 'w') as file_handle:
            writer = csv.writer(file_handle)
            for submission in blinded_notes:
                writer.writerow([submission.number, 'ac1@eccv.org', round(random.random(), 2)])
                writer.writerow([submission.number, 'ac2@eccv.org', round(random.random(), 2)])

        conference.setup_matching(committee_id=conference.get_area_chairs_id(), build_conflicts=True, affinity_score_file=os.path.join(os.path.dirname(__file__), 'data/ac_affinity_scores.csv'),
            tpms_score_file=os.path.join(os.path.dirname(__file__), 'data/temp.csv'))

        request_page(selenium, url='http://localhost:3030/assignments?group=thecvf.com/ECCV/2020/Conference/Reviewers', token=conference.client.token)
        new_assignment_btn = selenium.find_element_by_xpath('//button[text()="New Assignment Configuration"]')
        assert new_assignment_btn
        new_assignment_btn.click()

        pop_up_div = selenium.find_element_by_id('note-editor-modal')
        assert pop_up_div
        assert pop_up_div.get_attribute('class') == 'modal fade in'

        custom_user_demand_invitation = selenium.find_element_by_name('custom_user_demand_invitation')
        assert custom_user_demand_invitation
        assert custom_user_demand_invitation.get_attribute('value') == 'thecvf.com/ECCV/2020/Conference/Reviewers/-/Custom_User_Demands'

        custom_max_papers_invitation = selenium.find_element_by_name('custom_max_papers_invitation')
        assert custom_max_papers_invitation
        assert custom_max_papers_invitation.get_attribute('value') == 'thecvf.com/ECCV/2020/Conference/Reviewers/-/Custom_Max_Papers'

        ### Bids
        r1_client.post_edge(openreview.Edge(invitation = conference.get_bid_id(conference.get_reviewers_id()),
            readers = [conference.id, conference.get_area_chairs_id(), '~Reviewer_ECCV_One1'],
            nonreaders = [conference.get_authors_id(number=blinded_notes[0].number)],
            writers = [conference.id, '~Reviewer_ECCV_One1'],
            signatures = ['~Reviewer_ECCV_One1'],
            head = blinded_notes[0].id,
            tail = '~Reviewer_ECCV_One1',
            label = 'Neutral'
        ))
        r1_client.post_edge(openreview.Edge(invitation = conference.get_bid_id(conference.get_reviewers_id()),
            readers = [conference.id, conference.get_area_chairs_id(), '~Reviewer_ECCV_One1'],
            nonreaders = [conference.get_authors_id(number=blinded_notes[1].number)],
            writers = [conference.id, '~Reviewer_ECCV_One1'],
            signatures = ['~Reviewer_ECCV_One1'],
            head = blinded_notes[1].id,
            tail = '~Reviewer_ECCV_One1',
            label = 'Very High'
        ))
        r1_client.post_edge(openreview.Edge(invitation = conference.get_bid_id(conference.get_reviewers_id()),
            readers = [conference.id, conference.get_area_chairs_id(), '~Reviewer_ECCV_One1'],
            nonreaders = [conference.get_authors_id(number=blinded_notes[4].number)],
            writers = [conference.id, '~Reviewer_ECCV_One1'],
            signatures = ['~Reviewer_ECCV_One1'],
            head = blinded_notes[4].id,
            tail = '~Reviewer_ECCV_One1',
            label = 'High'
        ))

        r2_client.post_edge(openreview.Edge(invitation = conference.get_bid_id(conference.get_reviewers_id()),
            readers = [conference.id, conference.get_area_chairs_id(), '~Reviewer_ECCV_Two1'],
            nonreaders = [conference.get_authors_id(number=blinded_notes[2].number)],
            writers = [conference.id, '~Reviewer_ECCV_Two1'],
            signatures = ['~Reviewer_ECCV_Two1'],
            head = blinded_notes[2].id,
            tail = '~Reviewer_ECCV_Two1',
            label = 'Neutral'
        ))
        r2_client.post_edge(openreview.Edge(invitation = conference.get_bid_id(conference.get_reviewers_id()),
            readers = [conference.id, conference.get_area_chairs_id(), '~Reviewer_ECCV_Two1'],
            nonreaders = [conference.get_authors_id(number=blinded_notes[3].number)],
            writers = [conference.id, '~Reviewer_ECCV_Two1'],
            signatures = ['~Reviewer_ECCV_Two1'],
            head = blinded_notes[3].id,
            tail = '~Reviewer_ECCV_Two1',
            label = 'Very High'
        ))
        r2_client.post_edge(openreview.Edge(invitation = conference.get_bid_id(conference.get_reviewers_id()),
            readers = [conference.id, conference.get_area_chairs_id(), '~Reviewer_ECCV_Two1'],
            nonreaders = [conference.get_authors_id(number=blinded_notes[4].number)],
            writers = [conference.id, '~Reviewer_ECCV_Two1'],
            signatures = ['~Reviewer_ECCV_Two1'],
            head = blinded_notes[4].id,
            tail = '~Reviewer_ECCV_Two1',
            label = 'High'
        ))

        r3_client.post_edge(openreview.Edge(invitation = conference.get_bid_id(conference.get_reviewers_id()),
            readers = [conference.id, conference.get_area_chairs_id(), '~Reviewer_ECCV_Three1'],
            nonreaders = [conference.get_authors_id(number=blinded_notes[4].number)],
            writers = [conference.id, '~Reviewer_ECCV_Three1'],
            signatures = ['~Reviewer_ECCV_Three1'],
            head = blinded_notes[4].id,
            tail = '~Reviewer_ECCV_Three1',
            label = 'Neutral'
        ))
        r3_client.post_edge(openreview.Edge(invitation = conference.get_bid_id(conference.get_reviewers_id()),
            readers = [conference.id, conference.get_area_chairs_id(), '~Reviewer_ECCV_Three1'],
            nonreaders = [conference.get_authors_id(number=blinded_notes[2].number)],
            writers = [conference.id, '~Reviewer_ECCV_Three1'],
            signatures = ['~Reviewer_ECCV_Three1'],
            head = blinded_notes[2].id,
            tail = '~Reviewer_ECCV_Three1',
            label = 'Very High'
        ))
        r3_client.post_edge(openreview.Edge(invitation = conference.get_bid_id(conference.get_reviewers_id()),
            readers = [conference.id, conference.get_area_chairs_id(), '~Reviewer_ECCV_Three1'],
            nonreaders = [conference.get_authors_id(number=blinded_notes[0].number)],
            writers = [conference.id, '~Reviewer_ECCV_Three1'],
            signatures = ['~Reviewer_ECCV_Three1'],
            head = blinded_notes[0].id,
            tail = '~Reviewer_ECCV_Three1',
            label = 'High'
        ))
        r4_client.post_edge(openreview.Edge(invitation = conference.get_bid_id(conference.get_reviewers_id()),
            readers = [conference.id, conference.get_area_chairs_id(), '~Reviewer_ECCV_Four1'],
            nonreaders = [conference.get_authors_id(number=blinded_notes[0].number)],
            writers = [conference.id, '~Reviewer_ECCV_Four1'],
            signatures = ['~Reviewer_ECCV_Four1'],
            head = blinded_notes[0].id,
            tail = '~Reviewer_ECCV_Four1',
            label = 'High'
        ))

        ## Area chairs assignments
        pc_client = openreview.Client(username='pc@eccv.org', password='1234')
        pc_client.post_edge(openreview.Edge(invitation = conference.get_paper_assignment_id(conference.get_area_chairs_id()),
            readers = [conference.id, '~AreaChair_ECCV_One1'],
            nonreaders = [conference.get_authors_id(number=blinded_notes[0].number)],
            writers = [conference.id],
            signatures = [conference.id],
            head = blinded_notes[0].id,
            tail = '~AreaChair_ECCV_One1',
            label = 'ac-matching',
            weight = 0.98
        ))
        pc_client.post_edge(openreview.Edge(invitation = conference.get_paper_assignment_id(conference.get_area_chairs_id()),
            readers = [conference.id, '~AreaChair_ECCV_One1'],
            nonreaders = [conference.get_authors_id(number=blinded_notes[1].number)],
            writers = [conference.id],
            signatures = [conference.id],
            head = blinded_notes[1].id,
            tail = '~AreaChair_ECCV_One1',
            label = 'ac-matching',
            weight = 0.88
        ))
        pc_client.post_edge(openreview.Edge(invitation = conference.get_paper_assignment_id(conference.get_area_chairs_id()),
            readers = [conference.id, '~AreaChair_ECCV_One1'],
            nonreaders = [conference.get_authors_id(number=blinded_notes[2].number)],
            writers = [conference.id],
            signatures = [conference.id],
            head = blinded_notes[2].id,
            tail = '~AreaChair_ECCV_One1',
            label = 'ac-matching',
            weight = 0.79
        ))
        pc_client.post_edge(openreview.Edge(invitation = conference.get_paper_assignment_id(conference.get_area_chairs_id()),
            readers = [conference.id, '~AreaChair_ECCV_Two1'],
            nonreaders = [conference.get_authors_id(number=blinded_notes[3].number)],
            writers = [conference.id],
            signatures = [conference.id],
            head = blinded_notes[3].id,
            tail = '~AreaChair_ECCV_Two1',
            label = 'ac-matching',
            weight = 0.99
        ))
        pc_client.post_edge(openreview.Edge(invitation = conference.get_paper_assignment_id(conference.get_area_chairs_id()),
            readers = [conference.id, '~AreaChair_ECCV_Two1'],
            nonreaders = [conference.get_authors_id(number=blinded_notes[4].number)],
            writers = [conference.id],
            signatures = [conference.id],
            head = blinded_notes[4].id,
            tail = '~AreaChair_ECCV_Two1',
            label = 'ac-matching',
            weight = 0.86
        ))

        now = datetime.datetime.utcnow()
        conference.open_recommendations(assignment_title='ac-matching', due_date=now + datetime.timedelta(minutes = 1440))

        ac1_client.post_edge(openreview.Edge(invitation = conference.get_recommendation_id(),
            readers = [conference.id, '~AreaChair_ECCV_One1'],
            writers = ['~AreaChair_ECCV_One1'],
            signatures = ['~AreaChair_ECCV_One1'],
            head = blinded_notes[0].id,
            tail = '~Reviewer_ECCV_Three1',
            weight = 1))

        ac2_client.post_edge(openreview.Edge(invitation = conference.get_recommendation_id(),
            readers = [conference.id, '~AreaChair_ECCV_Two1'],
            writers = ['~AreaChair_ECCV_Two1'],
            signatures = ['~AreaChair_ECCV_Two1'],
            head = blinded_notes[3].id,
            tail = '~Reviewer_ECCV_Three1',
            weight = 10))

        ac2_client.post_edge(openreview.Edge(invitation = conference.get_recommendation_id(),
            readers = [conference.id, '~AreaChair_ECCV_Two1'],
            writers = ['~AreaChair_ECCV_Two1'],
            signatures = ['~AreaChair_ECCV_Two1'],
            head = blinded_notes[4].id,
            tail = '~Reviewer_ECCV_Three1',
            weight = 5))

        ## Go to edge browser to recommend reviewers
        start = 'thecvf.com/ECCV/2020/Conference/Area_Chairs/-/Proposed_Assignment,label:ac-matching,tail:~AreaChair_ECCV_One1'
        edit = 'thecvf.com/ECCV/2020/Conference/Reviewers/-/Recommendation'
        browse = 'thecvf.com/ECCV/2020/Conference/Reviewers/-/TPMS_Score;\
thecvf.com/ECCV/2020/Conference/Reviewers/-/Affinity_Score;\
thecvf.com/ECCV/2020/Conference/Reviewers/-/Bid'
        hide = 'thecvf.com/ECCV/2020/Conference/Reviewers/-/Conflict'
        referrer = '[Return%20Instructions](/invitation?id=thecvf.com/ECCV/2020/Conference/Reviewers/-/Recommendation)'

        url = 'http://localhost:3030/edges/browse?start={start}&traverse={edit}&edit={edit}&browse={browse}&hide={hide}&referrer={referrer}&maxColumns=2'.format(start=start, edit=edit, browse=browse, hide=hide, referrer=referrer)

        request_page(selenium, 'http://localhost:3030/invitation?id=thecvf.com/ECCV/2020/Conference/Reviewers/-/Recommendation', ac1_client.token)
        panel = selenium.find_element_by_id('notes')
        assert panel
        links = panel.find_elements_by_tag_name('a')
        assert links
        assert len(links) == 1
        assert url == links[0].get_attribute("href")


    def test_reviewer_matching(self, conference):

        pc_client = openreview.Client(username='pc@eccv.org', password='1234')

        ### Custom loads
        pc_client.post_edge(openreview.Edge(invitation = conference.get_invitation_id(name='Custom_Max_Papers', prefix=conference.get_reviewers_id()),
            readers = [conference.id],
            nonreaders = [],
            writers = [conference.id],
            signatures = [conference.id],
            head = conference.get_reviewers_id(),
            tail = '~Reviewer_ECCV_One1',
            weight = 2
        ))

        pc_client.post_edge(openreview.Edge(invitation = conference.get_invitation_id(name='Custom_Max_Papers', prefix=conference.get_reviewers_id()),
            readers = [conference.id],
            nonreaders = [],
            writers = [conference.id],
            signatures = [conference.id],
            head = conference.get_reviewers_id(),
            tail = '~Reviewer_ECCV_Two1',
            weight = 1
        ))

    def test_desk_reject_submission(self, conference, client, test_client, selenium, request_page, helpers):

        conference.setup_post_submission_stage(force=True)

        blinded_notes = conference.get_submissions()
        assert len(blinded_notes) == 5

        desk_reject_note = openreview.Note(
            invitation = 'thecvf.com/ECCV/2020/Conference/Paper5/-/Desk_Reject',
            forum = blinded_notes[0].forum,
            replyto = blinded_notes[0].forum,
            readers = ['thecvf.com/ECCV/2020/Conference',
            'thecvf.com/ECCV/2020/Conference/Paper5/Authors',
            'thecvf.com/ECCV/2020/Conference/Paper5/Reviewers',
            'thecvf.com/ECCV/2020/Conference/Paper5/Area_Chairs',
            'thecvf.com/ECCV/2020/Conference/Program_Chairs'],
            writers = [conference.get_id(), conference.get_program_chairs_id()],
            signatures = [conference.get_program_chairs_id()],
            content = {
                'desk_reject_comments': 'PC has decided to reject this submission.',
                'title': 'Submission Desk Rejected by Program Chairs'
            }
        )

        pc_client = openreview.Client(username='pc@eccv.org', password='1234')
        posted_note = pc_client.post_note(desk_reject_note)
        assert posted_note

        helpers.await_queue()

        logs = client.get_process_logs(id = posted_note.id)
        assert logs
        assert logs[0]['status'] == 'ok'

        blinded_notes = conference.get_submissions()
        assert len(blinded_notes) == 4

        desk_rejected_notes = client.get_notes(invitation = conference.submission_stage.get_desk_rejected_submission_id(conference))

        assert len(desk_rejected_notes) == 1
        assert desk_rejected_notes[0].content['authors'] == ['Anonymous']
        assert desk_rejected_notes[0].content['authorids'] == ['thecvf.com/ECCV/2020/Conference/Paper5/Authors']
        assert desk_rejected_notes[0].readers == [
            'thecvf.com/ECCV/2020/Conference/Paper5/Authors',
            'thecvf.com/ECCV/2020/Conference/Paper5/Reviewers',
            'thecvf.com/ECCV/2020/Conference/Paper5/Area_Chairs',
            'thecvf.com/ECCV/2020/Conference/Program_Chairs']

        desk_reject_note = test_client.get_note(posted_note.id)
        assert desk_reject_note
        assert desk_reject_note.content['desk_reject_comments'] == 'PC has decided to reject this submission.'

        author_group = client.get_group('thecvf.com/ECCV/2020/Conference/Authors')
        assert author_group
        assert len(author_group.members) == 4
        assert 'thecvf.com/ECCV/2020/Conference/Paper5/Authors' not in author_group.members

        request_page(selenium, "http://localhost:3030/group?id=thecvf.com/ECCV/2020/Conference/Authors", test_client.token)
        tabs = selenium.find_element_by_class_name('tabs-container')
        assert tabs
        assert tabs.find_element_by_id('author-tasks')
        assert tabs.find_element_by_id('your-submissions')
        papers = tabs.find_element_by_id('your-submissions').find_element_by_class_name('console-table')
        assert len(papers.find_elements_by_tag_name('tr')) == 5

    def test_withdraw_submission(self, conference, client, test_client, selenium, request_page, helpers):

        conference.setup_post_submission_stage(force=True, hide_fields=['_bibtex'])

        blinded_notes = conference.get_submissions()
        assert len(blinded_notes) == 4

        withdrawal_note = openreview.Note(
            invitation = 'thecvf.com/ECCV/2020/Conference/Paper4/-/Withdraw',
            forum = blinded_notes[0].forum,
            replyto = blinded_notes[0].forum,
            readers = [
                'thecvf.com/ECCV/2020/Conference',
                'thecvf.com/ECCV/2020/Conference/Paper4/Authors',
                'thecvf.com/ECCV/2020/Conference/Paper4/Reviewers',
                'thecvf.com/ECCV/2020/Conference/Paper4/Area_Chairs',
                'thecvf.com/ECCV/2020/Conference/Program_Chairs'],
            writers = [conference.get_id(), 'thecvf.com/ECCV/2020/Conference/Paper4/Authors'],
            signatures = ['thecvf.com/ECCV/2020/Conference/Paper4/Authors'],
            content = {
                'title': 'Submission Withdrawn by the Authors',
                'withdrawal confirmation': 'I have read and agree with the venue\'s withdrawal policy on behalf of myself and my co-authors.'
            }
        )

        posted_note = test_client.post_note(withdrawal_note)
        assert posted_note

        helpers.await_queue()

        logs = client.get_process_logs(id = posted_note.id)
        assert logs
        assert logs[0]['status'] == 'ok'

        blinded_notes = conference.get_submissions()
        assert len(blinded_notes) == 3

        withdrawn_notes = client.get_notes(invitation = conference.submission_stage.get_withdrawn_submission_id(conference))

        assert len(withdrawn_notes) == 1
        assert withdrawn_notes[0].content['authors'] == ['Anonymous']
        assert withdrawn_notes[0].content['authorids'] == ['Anonymous']
        assert withdrawn_notes[0].readers == [
            'thecvf.com/ECCV/2020/Conference/Paper4/Authors',
            'thecvf.com/ECCV/2020/Conference/Paper4/Reviewers',
            'thecvf.com/ECCV/2020/Conference/Paper4/Area_Chairs',
            'thecvf.com/ECCV/2020/Conference/Program_Chairs']
        assert withdrawn_notes[0].content['_bibtex'] == ''

        author_group = client.get_group('thecvf.com/ECCV/2020/Conference/Authors')
        assert author_group
        assert len(author_group.members) == 3
        assert 'thecvf.com/ECCV/2020/Conference/Paper4/Authors' not in author_group.members

        request_page(selenium, "http://localhost:3030/group?id=thecvf.com/ECCV/2020/Conference/Authors", test_client.token)
        tabs = selenium.find_element_by_class_name('tabs-container')
        assert tabs
        assert tabs.find_element_by_id('author-tasks')
        assert tabs.find_element_by_id('your-submissions')
        papers = tabs.find_element_by_id('your-submissions').find_element_by_class_name('console-table')
        assert len(papers.find_elements_by_tag_name('tr')) == 4

    def test_review_stage(self, conference, client, test_client, selenium, request_page, helpers):

        conference.set_assignment('~AreaChair_ECCV_One1', 1, is_area_chair=True)
        conference.set_assignment('~AreaChair_ECCV_One1', 2, is_area_chair=True)

        conference.set_assignment('~Reviewer_ECCV_One1', 1)
        conference.set_assignment('~Reviewer_ECCV_One1', 2)
        conference.set_assignment('~Reviewer_ECCV_Two1', 1)
        conference.set_assignment('~Reviewer_ECCV_Two1', 2)
        conference.set_assignment('~ReviewerFirstName_Eccv1', 1)

        now = datetime.datetime.utcnow()

        conference.set_review_stage(openreview.ReviewStage(due_date=now + datetime.timedelta(minutes = 40),
            additional_fields = {
                'summary_of_contributions': {
                    'order': 1,
                    'description': 'Briefly describe the contributions of the paper in your own words. If necessary, also mention a discrepancy between the contributions claimed by the authors and the contributions from your point of view. This can be elaborated in Strengths and Weaknesses below. Max length: 800',
                    'value-regex': '[\\S\\s]{0,800}',
                    'required': True
                },
                'strengths': {
                    'order': 2,
                    'value-regex': '[\\S\\s]{0,5000}',
                    'description': 'Describe the strengths of the paper in detail. Max length: 5000',
                    'required': True
                },
                'weaknesses': {
                    'order': 3,
                    'value-regex': '[\\S\\s]{0,5000}',
                    'description': 'Describe the weaknesses of the paper in detail. Provide solid arguments and evidence for your claims. For instance, it is not okay to say that something has been done before, if you do not provide concrete references. Max length: 5000',
                    'required': True
                },
                'suggestion_to_reviewers': {
                    'order': 4,
                    'value-regex': '[\\S\\s]{0,5000}',
                    'description': 'Here you can provide recommendations to the authors how they can improve their manuscript (e.g. typos). They are not relevant for your rating. Max length: 5000',
                    'required': True
                },
                'preliminary_rating': {
                    'order': 5,
                    'value-dropdown': [
                        '6: Strong accept',
                        '5: Weak accept',
                        '4: Borderline accept',
                        '3: Borderline reject',
                        '2: Weak reject',
                        '1: Strong reject'
                    ],
                    'required': True
                },
                'preliminary_rating_justification': {
                    'order': 6,
                    'value-regex': '[\\S\\s]{0,1000}',
                    'description': 'Briefly summarize the strenths and weaknesses and justify your rating. Keep in mind that your rating should not be based on your personal taste, but should be based on scientific arguments as elaborated in strengths and weaknesses. Max length: 1000',
                    'required': True
                },
                'confidence': {
                    'order': 7,
                    'value-dropdown': [
                        '4: High, published similar work',
                        '3: Medium, published weakly related work',
                        '2: Low, read similar work',
                        '1: None, no idea why this paper was assigned to me'
                    ],
                    'required': True
                }
            },
            remove_fields = ['title', 'rating', 'review'],
            rating_field_name = 'preliminary_rating'))

        r1_client = openreview.Client(username='reviewer1@fb.com', password='1234')
        r2_client = openreview.Client(username='reviewer2@google.com', password='1234')


        blinded_notes = conference.get_submissions()
        assert len(blinded_notes) == 3

        signatory = r1_client.get_groups(regex='thecvf.com/ECCV/2020/Conference/Paper1/Reviewer_.*', signatory='reviewer1@fb.com')[0].id

        review_note = r1_client.post_note(openreview.Note(
            forum=blinded_notes[2].id,
            replyto=blinded_notes[2].id,
            invitation='thecvf.com/ECCV/2020/Conference/Paper1/-/Official_Review',
            readers=['thecvf.com/ECCV/2020/Conference/Program_Chairs', 'thecvf.com/ECCV/2020/Conference/Paper1/Area_Chairs', signatory],
            nonreaders=['thecvf.com/ECCV/2020/Conference/Paper1/Authors'],
            writers=['thecvf.com/ECCV/2020/Conference', signatory],
            signatures=[signatory],
            content={
                'summary_of_contributions': 'summary_of_contributions',
                'strengths': 'strengths',
                'weaknesses': 'weaknesses',
                'suggestion_to_reviewers': 'suggestion_to_reviewers',
                'preliminary_rating': '6: Strong accept',
                'preliminary_rating_justification': 'preliminary_rating_justification',
                'confidence': '4: High, published similar work'
            }
        ))

        helpers.await_queue()
        process_logs = client.get_process_logs(id = review_note.id)
        assert len(process_logs) == 1
        assert process_logs[0]['status'] == 'ok'

        messages = client.get_messages(subject = '[ECCV 2020] Your review has been received on your assigned Paper number: 1, Paper title: "Paper title 1"')
        assert len(messages) == 1
        recipients = [m['content']['to'] for m in messages]
        assert 'reviewer1@fb.com' in recipients

        ## AC and other reviewers
        messages =  client.get_messages(subject = '[ECCV 2020] Review posted to your assigned Paper number: 1, Paper title: "Paper title 1"')
        assert len(messages) == 1
        recipients = [m['content']['to'] for m in messages]
        assert 'ac1@eccv.org' in recipients

        ## PCs
        assert not client.get_messages(subject = '[ECCV 2020] A review has been received on Paper number: 1, Paper title: "Paper title 1"')
        ## Authors
        assert not client.get_messages(subject = '[ECCV 2020] Review posted to your submission - Paper number: 1, Paper title: "Paper title 1"')

        signatory = r2_client.get_groups(regex='thecvf.com/ECCV/2020/Conference/Paper1/Reviewer_.*', signatory='reviewer2@google.com')[0].id

        review_note = r2_client.post_note(openreview.Note(
            forum=blinded_notes[2].id,
            replyto=blinded_notes[2].id,
            invitation='thecvf.com/ECCV/2020/Conference/Paper1/-/Official_Review',
            readers=['thecvf.com/ECCV/2020/Conference/Program_Chairs', 'thecvf.com/ECCV/2020/Conference/Paper1/Area_Chairs', signatory],
            nonreaders=['thecvf.com/ECCV/2020/Conference/Paper1/Authors'],
            writers=['thecvf.com/ECCV/2020/Conference', signatory],
            signatures=[signatory],
            content={
                'summary_of_contributions': 'summary_of_contributions',
                'strengths': 'strengths 2',
                'weaknesses': 'weaknesses 2',
                'suggestion_to_reviewers': 'suggestion_to_reviewers 2',
                'preliminary_rating': '5: Weak accept',
                'preliminary_rating_justification': 'preliminary_rating_justification 2',
                'confidence': '1: None, no idea why this paper was assigned to me'
            }
        ))

        helpers.await_queue()
        process_logs = client.get_process_logs(id = review_note.id)
        assert len(process_logs) == 1
        assert process_logs[0]['status'] == 'ok'

        messages = client.get_messages(subject = '[ECCV 2020] Your review has been received on your assigned Paper number: 1, Paper title: "Paper title 1"')
        assert len(messages) == 2
        recipients = [m['content']['to'] for m in messages]
        assert 'reviewer1@fb.com' in recipients
        assert 'reviewer2@google.com' in recipients

        ## AC and other reviewers
        messages =  client.get_messages(subject = '[ECCV 2020] Review posted to your assigned Paper number: 1, Paper title: "Paper title 1"')
        assert len(messages) == 2
        recipients = [m['content']['to'] for m in messages]
        assert 'ac1@eccv.org' in recipients
        assert 'ac1@eccv.org' in recipients

        ## PCs
        assert not client.get_messages(subject = '[ECCV 2020] A review has been received on Paper number: 1, Paper title: "Paper title 1"')
        ## Authors
        assert not client.get_messages(subject = '[ECCV 2020] Review posted to your submission - Paper number: 1, Paper title: "Paper title 1"')

    def test_decline_after_assignment(self, conference, client, test_client, selenium, request_page, helpers):

        messages = client.get_messages(to='test_reviewer_eccv@mail.com', subject='[ECCV 2020] Reviewer Invitation accepted')
        assert messages
        assert len(messages)
        text = messages[0]['content']['text']
        assert 'Thank you for accepting the invitation to be a Reviewer for ECCV 2020.' in text

        reviewer_group = client.get_group(id='thecvf.com/ECCV/2020/Conference/Reviewers')
        assert '~ReviewerFirstName_Eccv1' in reviewer_group.members

        paper_reviewer_group = client.get_group(id='thecvf.com/ECCV/2020/Conference/Paper1/Reviewers')
        assert '~ReviewerFirstName_Eccv1' in paper_reviewer_group.members

        messages = client.get_messages(to = 'mohit+1@mail.com', subject = '[ECCV 2020]: Invitation to serve as Reviewer')
        text = messages[0]['content']['text']
        reject_url = re.search('href="https://.*response=No"', text).group(0)[6:-1].replace('https://openreview.net', 'http://localhost:3030').replace('&amp;', '&')

        #Assert reviewer is still in reviewer group
        request_page(selenium, reject_url, alert=True)
        reviewer_group = client.get_group('thecvf.com/ECCV/2020/Conference/Reviewers')
        assert '~ReviewerFirstName_Eccv1' in reviewer_group.members

        paper_reviewer_group = client.get_group('thecvf.com/ECCV/2020/Conference/Paper1/Reviewers')
        assert '~ReviewerFirstName_Eccv1' in paper_reviewer_group.members

    def test_comment_stage(self, conference, client, test_client, selenium, request_page, helpers):

        conference.set_comment_stage(openreview.CommentStage(official_comment_name='Confidential_Comment', reader_selection=True, unsubmitted_reviewers=True))

        r2_client = openreview.Client(username='reviewer2@google.com', password='1234')

        blinded_notes = conference.get_submissions()

        signatory = r2_client.get_groups(regex='thecvf.com/ECCV/2020/Conference/Paper1/Reviewer_.*', signatory='reviewer2@google.com')[0].id

        comment_note = r2_client.post_note(openreview.Note(
            forum=blinded_notes[2].id,
            replyto=blinded_notes[2].id,
            invitation='thecvf.com/ECCV/2020/Conference/Paper1/-/Confidential_Comment',
            readers=['thecvf.com/ECCV/2020/Conference/Program_Chairs', 'thecvf.com/ECCV/2020/Conference/Paper1/Area_Chairs', signatory],
            writers=[signatory],
            signatures=[signatory],
            content={
                'title': 'problem with review',
                'comment': 'This is a comment to the ACs'
            }
        ))
        assert comment_note
        helpers.await_queue()
        process_logs = client.get_process_logs(id = comment_note.id)
        assert len(process_logs) == 1
        assert process_logs[0]['status'] == 'ok'

        messages = client.get_messages(subject = f'[ECCV 2020] Reviewer {signatory.split("_")[-1]} commented on a paper in your area. Paper Number: 1, Paper Title: "Paper title 1"')
        assert len(messages) == 1
        recipients = [m['content']['to'] for m in messages]
        assert 'ac1@eccv.org' in recipients

        messages = client.get_messages(subject = '[ECCV 2020] Your comment was received on Paper Number: 1, Paper Title: "Paper title 1"')
        assert len(messages) == 1
        recipients = [m['content']['to'] for m in messages]
        assert 'reviewer2@google.com' in recipients

        ## PCs
        assert not client.get_messages(subject = '[ECCV 2020] A comment was posted. Paper number: 1, Paper title: "Paper title 1"')
        ## Reviewers
        assert not client.get_messages(subject = '[ECCV 2020] Comment posted to a paper you are reviewing. Paper number: 1, Paper title: "Paper title 1"')
        ## Authors
        assert not client.get_messages(subject = '[ECCV 2020] Your submission has received a comment. Paper number: 1, Paper title: "Paper title 1"')

        now = datetime.datetime.utcnow()

        ## Release reviews to authors and reviewers
        conference.set_review_stage(openreview.ReviewStage(due_date=now + datetime.timedelta(minutes = 40),
            additional_fields = {
                'summary_of_contributions': {
                    'order': 1,
                    'description': 'Briefly describe the contributions of the paper in your own words. If necessary, also mention a discrepancy between the contributions claimed by the authors and the contributions from your point of view. This can be elaborated in Strengths and Weaknesses below. Max length: 800',
                    'value-regex': '[\\S\\s]{0,800}',
                    'required': True
                },
                'strengths': {
                    'order': 2,
                    'value-regex': '[\\S\\s]{0,5000}',
                    'description': 'Describe the strengths of the paper in detail. Max length: 5000',
                    'required': True
                },
                'weaknesses': {
                    'order': 3,
                    'value-regex': '[\\S\\s]{0,5000}',
                    'description': 'Describe the weaknesses of the paper in detail. Provide solid arguments and evidence for your claims. For instance, it is not okay to say that something has been done before, if you do not provide concrete references. Max length: 5000',
                    'required': True
                },
                'suggestion_to_reviewers': {
                    'order': 4,
                    'value-regex': '[\\S\\s]{0,5000}',
                    'description': 'Here you can provide recommendations to the authors how they can improve their manuscript (e.g. typos). They are not relevant for your rating. Max length: 5000',
                    'required': True
                },
                'preliminary_rating': {
                    'order': 5,
                    'value-dropdown': [
                        '6: Strong accept',
                        '5: Weak accept',
                        '4: Borderline accept',
                        '3: Borderline reject',
                        '2: Weak reject',
                        '1: Strong reject'
                    ],
                    'required': True
                },
                'preliminary_rating_justification': {
                    'order': 6,
                    'value-regex': '[\\S\\s]{0,1000}',
                    'description': 'Briefly summarize the strenths and weaknesses and justify your rating. Keep in mind that your rating should not be based on your personal taste, but should be based on scientific arguments as elaborated in strengths and weaknesses. Max length: 1000',
                    'required': True
                },
                'confidence': {
                    'order': 7,
                    'value-dropdown': [
                        '4: High, published similar work',
                        '3: Medium, published weakly related work',
                        '2: Low, read similar work',
                        '1: None, no idea why this paper was assigned to me'
                    ],
                    'required': True
                }
            },
            remove_fields = ['title', 'rating', 'review'], release_to_reviewers = openreview.ReviewStage.Readers.REVIEWERS_SUBMITTED, release_to_authors = True ))


        request_page(selenium, 'http://localhost:3030/forum?id=' + blinded_notes[2].id , test_client.token)
        notes = selenium.find_elements_by_class_name('note_with_children')
        assert len(notes) == 2

    def test_paper_ranking_stage(self, conference, client, test_client, selenium, request_page):

        ac_client = openreview.Client(username='ac1@eccv.org', password='1234')
        ac_url = 'http://localhost:3030/group?id=thecvf.com/ECCV/2020/Conference/Area_Chairs'
        request_page(selenium, ac_url, ac_client.token)

        status = selenium.find_element_by_id("1-metareview-status")
        assert status

        assert not status.find_elements_by_class_name('tag-widget')

        reviewer_client = openreview.Client(username='reviewer1@fb.com', password='1234')
        reviewer_url = 'http://localhost:3030/group?id=thecvf.com/ECCV/2020/Conference/Reviewers'
        request_page(selenium, reviewer_url, reviewer_client.token)

        assert not selenium.find_elements_by_class_name('tag-widget')

        now = datetime.datetime.utcnow()
        conference.open_paper_ranking(conference.get_area_chairs_id(), due_date=now + datetime.timedelta(minutes = 40))
        conference.open_paper_ranking(conference.get_reviewers_id(), due_date=now + datetime.timedelta(minutes = 40))

        ac_url = 'http://localhost:3030/group?id=thecvf.com/ECCV/2020/Conference/Area_Chairs'
        request_page(selenium, ac_url, ac_client.token)

        status = selenium.find_element_by_id("1-metareview-status")
        assert status

        tag = status.find_element_by_class_name('tag-widget')
        assert tag

        options = tag.find_elements_by_tag_name("li")
        assert options
        assert len(options) == 3

        options = tag.find_elements_by_tag_name("a")
        assert options
        assert len(options) == 3

        blinded_notes = conference.get_submissions()

        signatory = ac_client.get_groups(regex='thecvf.com/ECCV/2020/Conference/Paper1/Area_Chair_.*', signatory='ac1@eccv.org')[0].id

        ac_client.post_tag(openreview.Tag(invitation = 'thecvf.com/ECCV/2020/Conference/Area_Chairs/-/Paper_Ranking',
            forum = blinded_notes[-1].id,
            tag = '1 of 2',
            readers = ['thecvf.com/ECCV/2020/Conference', signatory],
            signatures = [signatory])
        )

        reviewer_url = 'http://localhost:3030/group?id=thecvf.com/ECCV/2020/Conference/Reviewers'
        request_page(selenium, reviewer_url, reviewer_client.token)

        tags = selenium.find_elements_by_class_name('tag-widget')
        assert tags

        options = tags[0].find_elements_by_tag_name("li")
        assert options
        assert len(options) == 3

        options = tags[0].find_elements_by_tag_name("a")
        assert options
        assert len(options) == 3

        signatory = reviewer_client.get_groups(regex='thecvf.com/ECCV/2020/Conference/Paper1/Reviewer_.*', signatory='reviewer1@fb.com')[0].id

        reviewer_client.post_tag(openreview.Tag(invitation = 'thecvf.com/ECCV/2020/Conference/Reviewers/-/Paper_Ranking',
            forum = blinded_notes[-1].id,
            tag = '2 of 2',
            readers = ['thecvf.com/ECCV/2020/Conference', 'thecvf.com/ECCV/2020/Conference/Paper1/Area_Chairs', signatory],
            signatures = [signatory])
        )

        reviewer2_client = openreview.Client(username='reviewer2@google.com', password='1234')

        signatory = reviewer2_client.get_groups(regex='thecvf.com/ECCV/2020/Conference/Paper1/Reviewer_.*', signatory='reviewer2@google.com')[0].id

        reviewer2_client.post_tag(openreview.Tag(invitation = 'thecvf.com/ECCV/2020/Conference/Reviewers/-/Paper_Ranking',
            forum = blinded_notes[-1].id,
            tag = '1 of 2',
            readers = ['thecvf.com/ECCV/2020/Conference', 'thecvf.com/ECCV/2020/Conference/Paper1/Area_Chairs', signatory],
            signatures = [signatory])
        )

        with pytest.raises(openreview.OpenReviewException) as openReviewError:
            reviewer2_client.post_tag(openreview.Tag(invitation = 'thecvf.com/ECCV/2020/Conference/Reviewers/-/Paper_Ranking',
                forum = blinded_notes[-1].id,
                tag = '1 of 2',
                readers = ['thecvf.com/ECCV/2020/Conference', 'thecvf.com/ECCV/2020/Conference/Paper1/Area_Chairs', signatory],
                signatures = [signatory])
            )
        assert  openReviewError.value.args[0].get('name') == 'TooManyError'

    def test_rebuttal_stage(self, conference, client, test_client, selenium, request_page, helpers):

        blinded_notes = conference.get_submissions()

        now = datetime.datetime.utcnow()

        conference.set_review_rebuttal_stage(openreview.ReviewRebuttalStage(due_date=now + datetime.timedelta(minutes = 40)))
        request_page(selenium, 'http://localhost:3030/forum?id=' + blinded_notes[2].id , test_client.token)
        notes = selenium.find_elements_by_class_name('note_with_children')
        assert len(notes) == 2

        button = notes[0].find_element_by_class_name('btn')
        assert button

        button = notes[1].find_element_by_class_name('btn')
        assert button

        signatory = client.get_groups(regex='thecvf.com/ECCV/2020/Conference/Paper1/Reviewer_.*', signatory='reviewer2@google.com')[0].id
        reviews = test_client.get_notes(forum=blinded_notes[2].id, invitation='thecvf.com/ECCV/2020/Conference/Paper1/-/Official_Review', signature=signatory)
        assert len(reviews) == 1

        rebuttal_note = test_client.post_note(openreview.Note(
            forum=blinded_notes[2].id,
            replyto=reviews[0].id,
            invitation=reviews[0].signatures[0] + '/-/Rebuttal',
            readers=['thecvf.com/ECCV/2020/Conference/Program_Chairs',
            'thecvf.com/ECCV/2020/Conference/Paper1/Area_Chairs',
            'thecvf.com/ECCV/2020/Conference/Paper1/Reviewers/Submitted',
            'thecvf.com/ECCV/2020/Conference/Paper1/Authors'],
            writers=['thecvf.com/ECCV/2020/Conference', 'thecvf.com/ECCV/2020/Conference/Paper1/Authors'],
            signatures=['thecvf.com/ECCV/2020/Conference/Paper1/Authors'],
            content={
                'rebuttal': 'this is the rebuttal `print(\'hello\')`'
            }
        ))
        assert rebuttal_note
        helpers.await_queue()
        process_logs = client.get_process_logs(id = rebuttal_note.id)
        assert len(process_logs) == 1
        assert process_logs[0]['status'] == 'ok'

        messages = client.get_messages(subject = '[ECCV 2020] Your rebuttal has been received on your submission - Paper number: 1, Paper title: "Paper title 1"')
        assert len(messages) == 3
        recipients = [m['content']['to'] for m in messages]
        assert 'test@mail.com' in recipients

        messages = client.get_messages(subject = '[ECCV 2020] Rebuttal posted to your review submitted - Paper number: 1, Paper title: "Paper title 1"')
        assert len(messages) == 1
        recipients = [m['content']['to'] for m in messages]
        assert 'reviewer2@google.com' in recipients

        messages = client.get_messages(subject = '[ECCV 2020] Rebuttal posted to your assigned Paper number: 1, Paper title: "Paper title 1"')
        assert len(messages) == 2
        recipients = [m['content']['to'] for m in messages]
        assert 'reviewer1@fb.com' in recipients
        assert 'ac1@eccv.org' in recipients

    def test_revise_review_stage(self, conference, client, test_client, selenium, request_page, helpers):

        blinded_notes = conference.get_submissions()

        now = datetime.datetime.utcnow()

        conference.set_review_revision_stage(openreview.ReviewRevisionStage(due_date = now + datetime.timedelta(minutes = 40), additional_fields = {
            'final_rating': {
                'order': 1,
                'value-dropdown': [
                    '6: Strong accept',
                    '5: Weak accept',
                    '4: Borderline accept',
                    '3: Borderline reject',
                    '2: Weak reject',
                    '1: Strong reject'
                ],
                'required': True
            },
            'final_rating_justification': {
                'order': 2,
                'value-regex': '[\\S\\s]{0,1000}',
                'description': 'Indicate that you have read the author rebuttal and argue in which sense the rebuttal or the discussion with the other reviewers has changed your initial rating or why you want to keep your rating. Max length: 1000',
                'required': True
            }
        }, remove_fields = ['title', 'rating', 'review', 'confidence']))

        reviewer_client = openreview.Client(username='reviewer2@google.com', password='1234')

        request_page(selenium, 'http://localhost:3030/forum?id=' + blinded_notes[2].id , reviewer_client.token)
        notes = selenium.find_elements_by_class_name('note_with_children')
        assert len(notes) == 4

        buttons = notes[0].find_elements_by_class_name('btn')
        assert len(buttons) == 4

        buttons = notes[1].find_elements_by_class_name('btn')
        assert len(buttons) == 7

        signatory = reviewer_client.get_groups(regex='thecvf.com/ECCV/2020/Conference/Paper1/Reviewer_.*', signatory='reviewer2@google.com')[0].id

        reviews = reviewer_client.get_notes(forum=blinded_notes[2].id, invitation='thecvf.com/ECCV/2020/Conference/Paper1/-/Official_Review', signature=signatory)
        assert len(reviews) == 1


        review_revision_note = reviewer_client.post_note(openreview.Note(
            forum=blinded_notes[2].id,
            referent=reviews[0].id,
            invitation=reviews[0].signatures[0] + '/-/Review_Revision',
            readers=['thecvf.com/ECCV/2020/Conference/Program_Chairs',
            'thecvf.com/ECCV/2020/Conference/Paper1/Area_Chairs',
            'thecvf.com/ECCV/2020/Conference/Paper1/Reviewers/Submitted',
            'thecvf.com/ECCV/2020/Conference/Paper1/Authors'],
            writers=['thecvf.com/ECCV/2020/Conference', signatory],
            signatures=[signatory],
            content={
                'final_rating': '5: Weak accept',
                'final_rating_justification': 'rebuttal was good'
            }
        ))
        assert review_revision_note
        helpers.await_queue()
        process_logs = client.get_process_logs(id = review_revision_note.id)
        assert len(process_logs) == 1
        assert process_logs[0]['status'] == 'ok'

        messages = client.get_messages(subject = '[ECCV 2020] Revised review posted to your submission: "Paper title 1"')
        assert len(messages) == 3
        recipients = [m['content']['to'] for m in messages]
        assert 'test@mail.com' in recipients

        messages = client.get_messages(subject = '[ECCV 2020] Your revised review has been received on your assigned Paper number: 1, Paper title: "Paper title 1"')
        assert len(messages) == 1
        recipients = [m['content']['to'] for m in messages]
        assert 'reviewer2@google.com' in recipients

        messages = client.get_messages(subject = '[ECCV 2020] Revised review posted to your assigned paper: "Paper title 1"')
        assert len(messages) == 2
        recipients = [m['content']['to'] for m in messages]
        assert 'reviewer1@fb.com' in recipients
        assert 'ac1@eccv.org' in recipients

    def test_review_rating_stage(self, conference, client, test_client, selenium, request_page):

        now = datetime.datetime.utcnow()

        conference.set_review_rating_stage(openreview.ReviewRatingStage(due_date = now + datetime.timedelta(minutes = 40), additional_fields = {
            'rating': {
                'order': 1,
                'required': True,
                'value-radio': ['-1: useless', '1: normal, valuable review', '2: exceptional, top 10% of my reviews']
            },
            'rating_justification': {
                'order': 2,
                'value-regex': '[\\S\\s]{0,5000}',
                'description': 'Justification of the rating. Max length: 5000',
                'required': False
            }
        }, remove_fields = ['review_quality']))

        ac_client = openreview.Client(username='ac1@eccv.org', password='1234')

        blinded_notes = conference.get_submissions()

        request_page(selenium, 'http://localhost:3030/forum?id=' + blinded_notes[2].id , ac_client.token)
        notes = selenium.find_elements_by_class_name('note_with_children')
        assert len(notes) == 4

        buttons = notes[0].find_elements_by_class_name('btn')
        assert len(buttons) == 2

        buttons = notes[1].find_elements_by_class_name('btn')
        assert len(buttons) == 5

        reviews = ac_client.get_notes(forum=blinded_notes[2].id, invitation='thecvf.com/ECCV/2020/Conference/Paper.*/-/Official_Review')
        assert len(reviews) == 2

        signatory = ac_client.get_groups(regex='thecvf.com/ECCV/2020/Conference/Paper1/Area_Chair_.*', signatory='ac1@eccv.org')[0].id

        review_rating_note = ac_client.post_note(openreview.Note(
            forum=blinded_notes[2].id,
            replyto=reviews[1].id,
            invitation=reviews[1].signatures[0] + '/-/Review_Rating',
            readers=['thecvf.com/ECCV/2020/Conference/Program_Chairs',
            signatory],
            writers=[signatory],
            signatures=[signatory],
            content={
                'rating': '-1: useless',
                'rating_justification': 'bad review'
            }
        ))
        assert review_rating_note

    def test_secondary_assignments(self, conference, client, test_client, selenium, request_page):

        now = datetime.datetime.utcnow()

        conference.set_meta_review_stage(openreview.MetaReviewStage(due_date =  now + datetime.timedelta(minutes = 1440)))

        ac_client = openreview.Client(username='ac1@eccv.org', password='1234')
        ac_url = 'http://localhost:3030/group?id=thecvf.com/ECCV/2020/Conference/Area_Chairs'
        request_page(selenium, ac_url, ac_client.token)

        # Check that Secondary AC Assignments tab is not visible
        notes_div = selenium.find_element_by_id('notes')
        assert notes_div.find_element_by_link_text('Assigned Papers')
        assert notes_div.find_element_by_link_text('Area Chair Tasks')
        with pytest.raises(NoSuchElementException):
            notes_div.find_element_by_link_text('Secondary AC Assignments')

        # Enable secondary area chairs tab in AC console
        conference.has_secondary_area_chairs(True)
        conference.set_area_chairs()

        # Assign AreaChair_ECCV_Two1 as primary AC on paper 3 and as secondary AC on paper 1 and 2
        conference.set_assignment('~AreaChair_ECCV_Two1', 3, is_area_chair=True)

        for i in range(1,3):
            secondary_group = client.post_group(openreview.Group(
                id='{}/Paper{}/Secondary_Area_Chair'.format(conference.id, i),
                signatures=[],
                signatories=['{}/Paper{}/Secondary_Area_Chair'.format(conference.id, i)],
                readers=['{}/Paper{}/Secondary_Area_Chair'.format(conference.id, i)],
                writers=['{}/Paper{}/Secondary_Area_Chair'.format(conference.id, i)],
                members=['~AreaChair_ECCV_Two1']))
            ac_group = client.get_group(conference.get_area_chairs_id(number=i))
            client.add_members_to_group(ac_group, secondary_group.id)

        # Check that Secondary AC Assignments tab is visible after it is enabled
        ac_client2 = openreview.Client(username='ac2@eccv.org', password='1234')
        request_page(selenium, ac_url, ac_client2.token)

        notes_div = selenium.find_element_by_id('notes')
        assert notes_div.find_element_by_link_text('Assigned Papers')
        assert notes_div.find_element_by_link_text('Area Chair Tasks')
        assert notes_div.find_element_by_link_text('Secondary AC Assignments')

        secondary_assignments_div = selenium.find_element_by_id('secondary-papers')
        for i in range(1,3):
            assert secondary_assignments_div.find_elements_by_id('note-summary-{}'.format(i))

    def test_chronological_pc_timeline(self, conference, selenium, request_page):
        # Assumptions: 1) Items are in list elements
        #              2) Dates are stated in plain English
        def convert_text_to_datetime(text):
            mnt_to_idx = {month.lower(): index for index, month in enumerate(calendar.month_abbr) if month}
            tokens = text.split(' ')
            start_idx, end_idx = tokens.index('until'), tokens.index('and')
            # Extracted format: DD Month YYYY, HH:MM Timezone
            due_date_list = tokens[start_idx + 1: end_idx]
            # Clean up text - strip comma + remove timezone
            due_date_list[2] = due_date_list[2][:-1]
            due_date_list.pop()
            date_obj = datetime.datetime(year=int(due_date_list[2]),
                                         month=mnt_to_idx[due_date_list[1].replace('sept','sep')],
                                         day=int(due_date_list[0]),
                                         hour=int(due_date_list[3].split(':')[0]),
                                         minute=int(due_date_list[3].split(':')[1]))

            return date_obj

        ac_client = openreview.Client(username='openreview.net', password='1234')
        ac_url = 'http://localhost:3030/group?id=thecvf.com/ECCV/2020/Conference/Program_Chairs'
        request_page(selenium, ac_url, ac_client.token)

        # Get the timeline text - order of elements retrieved is order of elements on page top -> bottom
        list_elements = selenium.find_elements_by_tag_name('li')
        retrieved_dates = []
        for element in list_elements:
            element_text = element.text.lower()
            if 'expires' in element_text:
                retrieved_dates.append(convert_text_to_datetime(element_text))

        # Assert correct order of dates
        for date_idx in range(1, len(retrieved_dates)):
            curr_date = retrieved_dates[date_idx]
            prev_date = retrieved_dates[date_idx - 1]
            assert curr_date >= prev_date
