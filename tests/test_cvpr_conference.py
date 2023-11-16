from __future__ import absolute_import, division, print_function, unicode_literals
import openreview
import pytest
import requests
import datetime
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

class TestCVPRSConference():

    @pytest.fixture(scope="class")
    def conference(self, client, helpers):
        pc_client=openreview.Client(username='pc@cvpr.cc', password=helpers.strong_password)
        request_form=client.get_notes(invitation='openreview.net/Support/-/Request_Form', sort='tmdate')[0]

        conference=openreview.helpers.get_conference(pc_client, request_form.id)
        return conference


    def test_create_conference(self, client, helpers):

        now = datetime.datetime.utcnow()
        due_date = now + datetime.timedelta(days=3)
        first_date = now + datetime.timedelta(days=1)

        # Post the request form note
        helpers.create_user('pc@cvpr.cc', 'Program', 'CVPRChair')
        pc_client = openreview.Client(username='pc@cvpr.cc', password=helpers.strong_password)


        helpers.create_user('sac1@cvpr.cc', 'SAC', 'CVPROne')
        helpers.create_user('ac1@cvpr.cc', 'AC', 'CVPROne')
        helpers.create_user('ac2@cvpr.cc', 'AC', 'CVPRTwo')
        helpers.create_user('reviewer1@cvpr.cc', 'Reviewer', 'CVPROne')
        helpers.create_user('reviewer2@cvpr.cc', 'Reviewer', 'CVPRTwo')
        helpers.create_user('reviewer3@cvpr.cc', 'Reviewer', 'CVPRThree')
        helpers.create_user('reviewer4@cvpr.cc', 'Reviewer', 'CVPRFour')
        helpers.create_user('reviewer5@cvpr.cc', 'Reviewer', 'CVPRFive')
        helpers.create_user('reviewer6@cvpr.cc', 'Reviewer', 'CVPRSix')        

        request_form_note = pc_client.post_note(openreview.Note(
            invitation='openreview.net/Support/-/Request_Form',
            signatures=['~Program_CVPRChair1'],
            readers=[
                'openreview.net/Support',
                '~Program_CVPRChair1'
            ],
            writers=[],
            content={
                'title': 'Conference on Computer Vision and Pattern Recognition 2023',
                'Official Venue Name': 'Conference on Computer Vision and Pattern Recognition 2023',
                'Abbreviated Venue Name': 'CVPR 2023',
                'Official Website URL': 'https://cvpr.cc',
                'program_chair_emails': ['pc@cvpr.cc'],
                'contact_email': 'pc@cvpr.cc',
                'publication_chairs':'No, our venue does not have Publication Chairs',
                'Area Chairs (Metareviewers)': 'Yes, our venue has Area Chairs',
                'senior_area_chairs': 'Yes, our venue has Senior Area Chairs',
                'secondary_area_chairs': 'Yes, our venue has Secondary Area Chairs',
                'Venue Start Date': '2023/12/01',
                'Submission Deadline': due_date.strftime('%Y/%m/%d'),
                'abstract_registration_deadline': first_date.strftime('%Y/%m/%d'),
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
                'include_expertise_selection': 'Yes',
                'submission_deadline_author_reorder': 'Yes'
            }))

        helpers.await_queue()

        # Post a deploy note
        client.post_note(openreview.Note(
            content={'venue_id': 'thecvf.com/CVPR/2023/Conference'},
            forum=request_form_note.forum,
            invitation='openreview.net/Support/-/Request{}/Deploy'.format(request_form_note.number),
            readers=['openreview.net/Support'],
            referent=request_form_note.forum,
            replyto=request_form_note.forum,
            signatures=['openreview.net/Support'],
            writers=['openreview.net/Support']
        ))

        helpers.await_queue()

        assert client.get_group('thecvf.com/CVPR/2023/Conference')
        assert client.get_group('thecvf.com/CVPR/2023/Conference/Senior_Area_Chairs')
        acs=client.get_group('thecvf.com/CVPR/2023/Conference/Area_Chairs')
        assert acs
        assert 'thecvf.com/CVPR/2023/Conference/Senior_Area_Chairs' in acs.readers
        reviewers=client.get_group('thecvf.com/CVPR/2023/Conference/Reviewers')
        assert reviewers
        assert 'thecvf.com/CVPR/2023/Conference/Senior_Area_Chairs' in reviewers.readers
        assert 'thecvf.com/CVPR/2023/Conference/Area_Chairs' in reviewers.readers

        assert client.get_group('thecvf.com/CVPR/2023/Conference/Authors')

    def test_submit_papers(self, test_client, client, helpers):

        ## Need super user permission to add the venue to the active_venues group
        request_form=client.get_notes(invitation='openreview.net/Support/-/Request_Form', sort='tmdate')[0]
        conference=openreview.helpers.get_conference(client, request_form.id)

        domains = ['umass.edu', 'amazon.com', 'fb.com', 'cs.umass.edu', 'google.com', 'mit.edu']
        for i in range(1,6):
            note = openreview.Note(invitation = 'thecvf.com/CVPR/2023/Conference/-/Submission',
                readers = ['thecvf.com/CVPR/2023/Conference', 'test@mail.com', 'peter@mail.com', 'andrew@' + domains[i], '~SomeFirstName_User1'],
                writers = [conference.id, '~SomeFirstName_User1', 'peter@mail.com', 'andrew@' + domains[i]],
                signatures = ['~SomeFirstName_User1'],
                content = {
                    'title': 'Paper title ' + str(i) ,
                    'abstract': 'This is an abstract ' + str(i),
                    'authorids': ['test@mail.com', 'peter@mail.com', 'andrew@' + domains[i]],
                    'authors': ['SomeFirstName User', 'Peter SomeLastName', 'Andrew Mc'],
                    'keywords': ['machine learning', 'nlp']
                }
            )
            note = test_client.post_note(note)

        conference.setup_first_deadline_stage(force=True)

        blinded_notes = test_client.get_notes(invitation='thecvf.com/CVPR/2023/Conference/-/Blind_Submission', sort='tmdate')
        assert len(blinded_notes) == 5

        assert blinded_notes[0].readers == ['thecvf.com/CVPR/2023/Conference', 'thecvf.com/CVPR/2023/Conference/Paper5/Authors']

        assert client.get_invitation('thecvf.com/CVPR/2023/Conference/Paper5/-/Withdraw')
        assert client.get_invitation('thecvf.com/CVPR/2023/Conference/Paper5/-/Desk_Reject')
        assert client.get_invitation('thecvf.com/CVPR/2023/Conference/Paper5/-/Revision')
    
    def test_author_registration_stage(self, conference, client, helpers):
        authorids = conference.get_authors_id()
        assert authorids
        authorgroup = client.get_group(authorids)
        assert authorgroup 
        assert len(authorgroup.members) > 0 
        conference.set_registration_stage(
            openreview.RegistrationStage(
                committee_id = authorids,
                instructions ="Please confirm the following.",
                name = 'Registration',
                title = 'Authors Registration Form',
                start_date = datetime.datetime.utcnow(),
                due_date = datetime.datetime.utcnow() + datetime.timedelta(days = 5),
            )
        )
        helpers.await_queue()
        assert client.get_invitation('thecvf.com/CVPR/2023/Conference/Authors/-/Registration')
    
    def test_ac_registration_stage(self, conference, client, helpers):
        pc_client=openreview.Client(username='pc@cvpr.cc', password=helpers.strong_password)
        request_form=pc_client.get_notes(invitation='openreview.net/Support/-/Request_Form')[0]
        conference=openreview.helpers.get_conference(client, request_form.id)
        fields = {
            "subject_areas": {
                "order": 3, 
                "description": "Please select at least one of the following subject areas. The selected subject area(s) are used to ensure an adequate coverage of subject areas by the ACs. The subject areas play no role in the paper matching.", 
                "values-dropdown": [
                    "3D from multi-view and sensors",
                    "3D from single images",	
                    "Adversarial attack and defense",	
                    "Autonomous driving",
                    "Biometrics",	
                    "Computational imaging",	
                    "Computer vision for social good",	
                    "Computer vision theory",	
                    "Datasets and evaluation",	
                    "Deep learning architectures and techniques",	
                    "Document analysis and understanding",	
                    "Efficient and scalable vision",	
                    "Embodied vision: Active agents, simulation",
                    "Explainable computer vision",	
                    "Humans: Face, body, pose, gesture, movement",	
                    "Image and video synthesis and generation",	
                    "Low-level vision",	
                    "Machine learning (other than deep learning)",
                    "Medical and biological vision, cell microscopy",	
                    "Multi-modal learning",
                    "Optimization methods (other than deep learning)",
                    "Others",	
                    "Photogrammetry and remote sensing",	
                    "Physics-based vision and shape-from-X",	
                    "Recognition: Categorization, detection, retrieval",	
                    "Robotics",	
                    "Scene analysis and understanding",	
                    "Segmentation, grouping and shape analysis",	
                    "Self-supervised/unsupervised representation learning",	
                    "Transfer/ meta/ low-shot/ continual/ long-tail learning",	
                    "Transparency, fairness, accountability, privacy, ethics in vision",	
                    "Video: Action and event understanding",
                    "Video: Low-level analysis, motion, and tracking",	
                    "Vision + graphics",	
                    "Vision, language, and reasoning",	
                    "Vision applications and systems"
                ],
                "required": True
            },
            "profile_confirmed": {
                "description": "In order to avoid conflicts of interest in reviewing, we ask that all Area Chairs take a moment to update their OpenReview profiles (link in instructions above) with their latest information regarding email addresses, work history and professional relationships. Please confirm that your OpenReview profile is up-to-date by selecting \"Yes\".",
                "value-checkbox": "Yes",
                "required": True,
                "order": 1
            },
            "expertise_confirmed": {
                "description": "We will be using OpenReview's Expertise System as a factor in calculating paper-area chair affinity scores. Please take a moment to ensure that your latest papers are visible at the Expertise Selection (link in instructions above). Please confirm finishing this step by selecting \"Yes\".",
                "value-checkbox": "Yes",
                "required": True,
                "order": 2
            }
        }
        conference.set_registration_stage(
            openreview.RegistrationStage(
                committee_id = conference.get_area_chairs_id(),
                instructions ="Please confirm that your profile is complete and select your areas of expertise from the dropdown.",
                name = 'Registration',
                title = 'Area Chairs Registration Form',
                additional_fields= fields,
                start_date = datetime.datetime.utcnow(),
                due_date = datetime.datetime.utcnow() + datetime.timedelta(days = 5),
            )
        )
        helpers.await_queue()
        assert client.get_invitation('thecvf.com/CVPR/2023/Conference/Area_Chairs/-/Registration')
    
    def test_setup_first_deadline(self, conference, helpers, test_client, client, request_page, selenium):

        pc_client=openreview.Client(username='pc@cvpr.cc', password=helpers.strong_password)
        request_form=pc_client.get_notes(invitation='openreview.net/Support/-/Request_Form')[0]

        now = datetime.datetime.utcnow()
        due_date = now + datetime.timedelta(days=3)
        first_date = now        

        request_form_note = pc_client.post_note(openreview.Note(
            invitation=f'openreview.net/Support/-/Request{request_form.number}/Revision',
            referent=request_form.id,
            forum=request_form.id,
            signatures=['~Program_CVPRChair1'],
            readers=['thecvf.com/CVPR/2023/Conference/Program_Chairs', 'openreview.net/Support'],
            writers=[],
            content={
                'title': 'Conference on Computer Vision and Pattern Recognition 2023',
                'Official Venue Name': 'Conference on Computer Vision and Pattern Recognition 2023',
                'Abbreviated Venue Name': 'CVPR 2023',
                'Official Website URL': 'https://cvpr.cc',
                'program_chair_emails': ['pc@cvpr.cc'],
                'contact_email': 'pc@cvpr.cc',
                'publication_chairs':'No, our venue does not have Publication Chairs',
                'Venue Start Date': '2023/12/01',
                'Submission Deadline': due_date.strftime('%Y/%m/%d'),
                'abstract_registration_deadline': first_date.strftime('%Y/%m/%d'),
                'Location': 'Virtual',
                'submission_reviewer_assignment': 'Automatic',
                'How did you hear about us?': 'ML conferences',
                'Expected Submissions': '100',
                'use_recruitment_template': 'Yes',
                'include_expertise_selection': 'Yes',
                'submission_deadline_author_reorder': 'Yes'
            }))

        helpers.await_queue()        

        post_submission_note=pc_client.post_note(openreview.Note(
            content= {
                'force': 'Yes',
                'hide_fields': ['keywords'],
                'submission_readers': 'All area chairs only'
            },
            forum= request_form.id,
            invitation= f'openreview.net/Support/-/Request{request_form.number}/Post_Submission',
            readers= ['thecvf.com/CVPR/2023/Conference/Program_Chairs', 'openreview.net/Support'],
            referent= request_form.id,
            replyto= request_form.id,
            signatures= ['~Program_CVPRChair1'],
            writers= [],
        ))

        helpers.await_queue()

        submissions = client.get_notes(invitation='thecvf.com/CVPR/2023/Conference/-/Blind_Submission')
        assert len(submissions) == 5
        'thecvf.com/CVPR/2023/Area_Chairs' in submissions[0].readers

        invitation = client.get_invitation('thecvf.com/CVPR/2023/Conference/Paper5/-/Revision')
        assert 'values' in invitation.reply['content']['authors']
        assert 'values' in invitation.reply['content']['authorids']

    def test_post_submission_stage(self, conference, helpers, test_client, client, request_page, selenium):

        #conference.setup_final_deadline_stage(force=True)
        pc_client=openreview.Client(username='pc@cvpr.cc', password=helpers.strong_password)
        request_form=pc_client.get_notes(invitation='openreview.net/Support/-/Request_Form')[0]

        post_submission_note=pc_client.post_note(openreview.Note(
            content= {
                'force': 'Yes',
                'hide_fields': ['keywords'],
                'submission_readers': 'Assigned program committee (assigned reviewers, assigned area chairs, assigned senior area chairs if applicable)'
            },
            forum= request_form.id,
            invitation= f'openreview.net/Support/-/Request{request_form.number}/Post_Submission',
            readers= ['thecvf.com/CVPR/2023/Conference/Program_Chairs', 'openreview.net/Support'],
            referent= request_form.id,
            replyto= request_form.id,
            signatures= ['~Program_CVPRChair1'],
            writers= [],
        ))

        helpers.await_queue()

    def test_reviewer_recommendation(self, conference, helpers, test_client, client):

        now = datetime.datetime.utcnow()
        pc_client=openreview.Client(username='pc@cvpr.cc', password=helpers.strong_password)
        request_form=pc_client.get_notes(invitation='openreview.net/Support/-/Request_Form')[0]
        pc_client.add_members_to_group('thecvf.com/CVPR/2023/Conference/Area_Chairs', ['~AC_CVPROne1', '~AC_CVPRTwo1'])
        pc_client.add_members_to_group('thecvf.com/CVPR/2023/Conference/Reviewers', ['~Reviewer_CVPROne1', '~Reviewer_CVPRTwo1', '~Reviewer_CVPRThree1', '~Reviewer_CVPRFour1', '~Reviewer_CVPRFive1', '~Reviewer_CVPRSix1'])

        submissions = conference.get_submissions()
        
        ## Setup AC matching
        with open(os.path.join(os.path.dirname(__file__), 'data/rev_scores_venue.csv'), 'w') as file_handle:
            writer = csv.writer(file_handle)
            for submission in submissions:
                for ac in client.get_group('thecvf.com/CVPR/2023/Conference/Area_Chairs').members:
                    writer.writerow([submission.id, ac, round(random.random(), 2)])

        affinity_scores_url = client.put_attachment(os.path.join(os.path.dirname(__file__), 'data/rev_scores_venue.csv'), f'openreview.net/Support/-/Request{request_form.number}/Paper_Matching_Setup', 'upload_affinity_scores')

        client.post_note(openreview.Note(
            content={
                'title': 'Paper Matching Setup',
                'matching_group': 'thecvf.com/CVPR/2023/Conference/Area_Chairs',
                'compute_conflicts': 'Default',
                'compute_affinity_scores': 'No',
                'upload_affinity_scores': affinity_scores_url

            },
            forum=request_form.id,
            replyto=request_form.id,
            invitation=f'openreview.net/Support/-/Request{request_form.number}/Paper_Matching_Setup',
            readers=['thecvf.com/CVPR/2023/Conference/Program_Chairs', 'openreview.net/Support'],
            signatures=['~Program_CVPRChair1'],
            writers=[]
        ))
        helpers.await_queue()

        ## Deploy assignments
        client.post_edge(openreview.Edge(
            invitation='thecvf.com/CVPR/2023/Conference/Area_Chairs/-/Assignment',
            readers = [conference.id, f'thecvf.com/CVPR/2023/Conference/Paper{submissions[4].number}/Senior_Area_Chairs', '~AC_CVPROne1'],
            writers = [conference.id, f'thecvf.com/CVPR/2023/Conference/Paper{submissions[4].number}/Senior_Area_Chairs'],
            nonreaders = [f'thecvf.com/CVPR/2023/Conference/Paper{submissions[4].number}/Authors'],
            signatures = [conference.id],
            head = submissions[4].id,
            tail = '~AC_CVPROne1',
            label = 'ac-matching',
            weight = 0.94
        ))

        client.post_edge(openreview.Edge(
            invitation='thecvf.com/CVPR/2023/Conference/Area_Chairs/-/Assignment',
            readers = [conference.id, f'thecvf.com/CVPR/2023/Conference/Paper{submissions[3].number}/Senior_Area_Chairs', '~AC_CVPROne1'],
            writers = [conference.id, f'thecvf.com/CVPR/2023/Conference/Paper{submissions[3].number}/Senior_Area_Chairs'],
            nonreaders = [f'thecvf.com/CVPR/2023/Conference/Paper{submissions[3].number}/Authors'],
            signatures = [conference.id],
            head = submissions[3].id,
            tail = '~AC_CVPROne1',
            label = 'ac-matching',
            weight = 0.94
        ))

        client.post_edge(openreview.Edge(
            invitation='thecvf.com/CVPR/2023/Conference/Area_Chairs/-/Assignment',
            readers = [conference.id, f'thecvf.com/CVPR/2023/Conference/Paper{submissions[2].number}/Senior_Area_Chairs', '~AC_CVPROne1'],
            writers = [conference.id, f'thecvf.com/CVPR/2023/Conference/Paper{submissions[2].number}/Senior_Area_Chairs'],
            nonreaders = [f'thecvf.com/CVPR/2023/Conference/Paper{submissions[2].number}/Authors'],
            signatures = [conference.id],
            head = submissions[2].id,
            tail = '~AC_CVPROne1',
            label = 'ac-matching',
            weight = 0.94
        ))                        

        client.post_edge(openreview.Edge(
            invitation='thecvf.com/CVPR/2023/Conference/Area_Chairs/-/Assignment',
            readers = [conference.id, f'thecvf.com/CVPR/2023/Conference/Paper{submissions[1].number}/Senior_Area_Chairs', '~AC_CVPRTwo1'],
            writers = [conference.id, f'thecvf.com/CVPR/2023/Conference/Paper{submissions[1].number}/Senior_Area_Chairs'],
            nonreaders = [f'thecvf.com/CVPR/2023/Conference/Paper{submissions[1].number}/Authors'],
            signatures = [conference.id],
            head = submissions[1].id,
            tail = '~AC_CVPRTwo1',
            label = 'ac-matching',
            weight = 0.94
        ))

        client.post_edge(openreview.Edge(
            invitation='thecvf.com/CVPR/2023/Conference/Area_Chairs/-/Assignment',
            readers = [conference.id, f'thecvf.com/CVPR/2023/Conference/Paper{submissions[0].number}/Senior_Area_Chairs', '~AC_CVPRTwo1'],
            writers = [conference.id, f'thecvf.com/CVPR/2023/Conference/Paper{submissions[0].number}/Senior_Area_Chairs'],
            nonreaders = [f'thecvf.com/CVPR/2023/Conference/Paper{submissions[0].number}/Authors'],
            signatures = [conference.id],
            head = submissions[0].id,
            tail = '~AC_CVPRTwo1',
            label = 'ac-matching',
            weight = 0.94
        ))        

        ## Setup Reviewer matching
        with open(os.path.join(os.path.dirname(__file__), 'data/rev_scores_venue.csv'), 'w') as file_handle:
            writer = csv.writer(file_handle)
            for submission in submissions:
                for ac in client.get_group('thecvf.com/CVPR/2023/Conference/Reviewers').members:
                    writer.writerow([submission.id, ac, round(random.random(), 2)])

        affinity_scores_url = client.put_attachment(os.path.join(os.path.dirname(__file__), 'data/rev_scores_venue.csv'), f'openreview.net/Support/-/Request{request_form.number}/Paper_Matching_Setup', 'upload_affinity_scores')

        client.post_note(openreview.Note(
            content={
                'title': 'Paper Matching Setup',
                'matching_group': 'thecvf.com/CVPR/2023/Conference/Reviewers',
                'compute_conflicts': 'Default',
                'compute_affinity_scores': 'No',
                'upload_affinity_scores': affinity_scores_url

            },
            forum=request_form.id,
            replyto=request_form.id,
            invitation=f'openreview.net/Support/-/Request{request_form.number}/Paper_Matching_Setup',
            readers=['thecvf.com/CVPR/2023/Conference/Program_Chairs', 'openreview.net/Support'],
            signatures=['~Program_CVPRChair1'],
            writers=[]
        ))
        helpers.await_queue()

        conference.open_recommendations(
            due_date = now + datetime.timedelta(days=3),
            total_recommendations = 3
        )      


    def test_secondary_ac_assignment(self, conference, helpers, client):

        ## Assign secondary ACs
        client.post_group(openreview.Group(id='thecvf.com/CVPR/2023/Conference/Paper1/Secondary_Area_Chairs',
            readers=['thecvf.com/CVPR/2023/Conference', 'thecvf.com/CVPR/2023/Conference/Paper1/Senior_Area_Chairs', 'thecvf.com/CVPR/2023/Conference/Paper1/Area_Chairs'],
            nonreaders=['thecvf.com/CVPR/2023/Conference/Paper1/Authors'],
            writers=['thecvf.com/CVPR/2023/Conference'],
            signatures=['thecvf.com/CVPR/2023/Conference'],
            signatories=['thecvf.com/CVPR/2023/Conference'],
            anonids=True,
            members=['~AC_CVPRTwo1']
        ))
        client.add_members_to_group('thecvf.com/CVPR/2023/Conference/Paper1/Area_Chairs', 'thecvf.com/CVPR/2023/Conference/Paper1/Secondary_Area_Chairs')

        client.post_group(openreview.Group(id='thecvf.com/CVPR/2023/Conference/Paper2/Secondary_Area_Chairs',
            readers=['thecvf.com/CVPR/2023/Conference', 'thecvf.com/CVPR/2023/Conference/Paper2/Senior_Area_Chairs', 'thecvf.com/CVPR/2023/Conference/Paper2/Area_Chairs'],
            nonreaders=['thecvf.com/CVPR/2023/Conference/Paper2/Authors'],
            writers=['thecvf.com/CVPR/2023/Conference'],
            signatures=['thecvf.com/CVPR/2023/Conference'],
            signatories=['thecvf.com/CVPR/2023/Conference'],
            anonids=True,
            members=['~AC_CVPRTwo1']
        ))
        client.add_members_to_group('thecvf.com/CVPR/2023/Conference/Paper2/Area_Chairs', 'thecvf.com/CVPR/2023/Conference/Paper2/Secondary_Area_Chairs')


        client.post_group(openreview.Group(id='thecvf.com/CVPR/2023/Conference/Paper3/Secondary_Area_Chairs',
            readers=['thecvf.com/CVPR/2023/Conference', 'thecvf.com/CVPR/2023/Conference/Paper3/Senior_Area_Chairs', 'thecvf.com/CVPR/2023/Conference/Paper3/Area_Chairs'],
            nonreaders=['thecvf.com/CVPR/2023/Conference/Paper3/Authors'],
            writers=['thecvf.com/CVPR/2023/Conference'],
            signatures=['thecvf.com/CVPR/2023/Conference'],
            signatories=['thecvf.com/CVPR/2023/Conference'],
            anonids=True,
            members=['~AC_CVPRTwo1']
        ))
        client.add_members_to_group('thecvf.com/CVPR/2023/Conference/Paper3/Area_Chairs', 'thecvf.com/CVPR/2023/Conference/Paper3/Secondary_Area_Chairs')


        client.post_group(openreview.Group(id='thecvf.com/CVPR/2023/Conference/Paper4/Secondary_Area_Chairs',
            readers=['thecvf.com/CVPR/2023/Conference', 'thecvf.com/CVPR/2023/Conference/Paper4/Senior_Area_Chairs', 'thecvf.com/CVPR/2023/Conference/Paper4/Area_Chairs'],
            nonreaders=['thecvf.com/CVPR/2023/Conference/Paper4/Authors'],
            writers=['thecvf.com/CVPR/2023/Conference'],
            signatures=['thecvf.com/CVPR/2023/Conference'],
            signatories=['thecvf.com/CVPR/2023/Conference'],
            anonids=True,
            members=['~AC_CVPROne1']
        ))
        client.add_members_to_group('thecvf.com/CVPR/2023/Conference/Paper4/Area_Chairs', 'thecvf.com/CVPR/2023/Conference/Paper4/Secondary_Area_Chairs')

        client.post_group(openreview.Group(id='thecvf.com/CVPR/2023/Conference/Paper5/Secondary_Area_Chairs',
            readers=['thecvf.com/CVPR/2023/Conference', 'thecvf.com/CVPR/2023/Conference/Paper5/Senior_Area_Chairs', 'thecvf.com/CVPR/2023/Conference/Paper5/Area_Chairs'],
            nonreaders=['thecvf.com/CVPR/2023/Conference/Paper5/Authors'],
            writers=['thecvf.com/CVPR/2023/Conference'],
            signatures=['thecvf.com/CVPR/2023/Conference'],
            signatories=['thecvf.com/CVPR/2023/Conference'],
            anonids=True,
            members=['~AC_CVPROne1']
        ))        
        client.add_members_to_group('thecvf.com/CVPR/2023/Conference/Paper5/Area_Chairs', 'thecvf.com/CVPR/2023/Conference/Paper5/Secondary_Area_Chairs')
    
        ## Set the meta review stage
        pc_client=openreview.Client(username='pc@cvpr.cc', password=helpers.strong_password)
        request_form=pc_client.get_notes(invitation='openreview.net/Support/-/Request_Form')[0]

        now = datetime.datetime.utcnow()
        start_date = now - datetime.timedelta(days=2)
        due_date = now + datetime.timedelta(days=3)
        pc_client.post_note(openreview.Note(
            content= {
                'make_meta_reviews_public': 'No, meta reviews should NOT be revealed publicly when they are posted',
                'meta_review_start_date': start_date.strftime('%Y/%m/%d'),
                'meta_review_deadline': due_date.strftime('%Y/%m/%d'),
                'recommendation_options': 'Accept, Reject',
                'release_meta_reviews_to_authors': 'No, meta reviews should NOT be revealed when they are posted to the paper\'s authors',
                'release_meta_reviews_to_reviewers': 'Meta review should not be revealed to any reviewer',
            },
            forum= request_form.id,
            invitation= f'openreview.net/Support/-/Request{request_form.number}/Meta_Review_Stage',
            readers= ['thecvf.com/CVPR/2023/Conference/Program_Chairs', 'openreview.net/Support'],
            referent= request_form.id,
            replyto= request_form.id,
            signatures= ['~Program_CVPRChair1'],
            writers= [],
        ))

        helpers.await_queue() 

        ac1_client = openreview.Client(username='ac1@cvpr.cc', password=helpers.strong_password)       
        ac2_client = openreview.Client(username='ac2@cvpr.cc', password=helpers.strong_password)

        invitations = ac1_client.get_invitations(invitee=True, super='thecvf.com/CVPR/2023/Conference/-/Meta_Review')
        assert len(invitations) == 3

        invitations = ac2_client.get_invitations(invitee=True, super='thecvf.com/CVPR/2023/Conference/-/Meta_Review')
        assert len(invitations) == 2         

        ## Start official comment
        now = datetime.datetime.utcnow()
        start_date = now - datetime.timedelta(days=2)
        end_date = now + datetime.timedelta(days=3)
        pc_client.post_note(openreview.Note(
            content= {
                'commentary_start_date': start_date.strftime('%Y/%m/%d'),
                'commentary_end_date': end_date.strftime('%Y/%m/%d'),
                'participants': ['Program Chairs', 'Assigned Senior Area Chairs', 'Assigned Area Chairs', 'Assigned Reviewers'],
                'email_program_chairs_about_official_comments': 'Yes, email PCs for each official comment made in the venue',
                'additional_readers': ['Program Chairs', 'Assigned Senior Area Chairs', 'Assigned Area Chairs', 'Assigned Reviewers'],
            },
            forum= request_form.id,
            invitation= f'openreview.net/Support/-/Request{request_form.number}/Comment_Stage',
            readers= ['thecvf.com/CVPR/2023/Conference/Program_Chairs', 'openreview.net/Support'],
            referent= request_form.id,
            replyto= request_form.id,
            signatures= ['~Program_CVPRChair1'],
            writers= [],
        ))

        helpers.await_queue()

        ## post a comment as a Secondary AC
        submission = client.get_notes(invitation='thecvf.com/CVPR/2023/Conference/-/Blind_Submission', number=4)[0]   
        anon_reviewers_group_id = ac1_client.get_groups(regex=f'thecvf.com/CVPR/2023/Conference/Paper4/Secondary_Area_Chair_', signatory='ac1@cvpr.cc')[0].id
        ac1_client.post_note(
            openreview.Note(
                invitation = 'thecvf.com/CVPR/2023/Conference/Paper4/-/Official_Comment',
                forum = submission.id,
                replyto = submission.id,
                readers = [
                    'thecvf.com/CVPR/2023/Conference/Paper4/Reviewers',
                    'thecvf.com/CVPR/2023/Conference/Paper4/Area_Chairs',
                    'thecvf.com/CVPR/2023/Conference/Paper4/Senior_Area_Chairs',
                    'thecvf.com/CVPR/2023/Conference/Program_Chairs'],
                writers = [anon_reviewers_group_id],
                signatures = [anon_reviewers_group_id],
                content = {
                    'title': 'Comment title',
                    'comment': 'Paper is very good!'
                }                
            )
        )

        ## setup the metareview confirmation
        start_date = datetime.datetime.utcnow() - datetime.timedelta(weeks = 1)
        due_date = datetime.datetime.utcnow() + datetime.timedelta(weeks = 1)

        client.post_invitation(openreview.Invitation(id = 'thecvf.com/CVPR/2023/Conference/-/Meta_Review_Confirmation',
            cdate = openreview.tools.datetime_millis(start_date),
            duedate = openreview.tools.datetime_millis(due_date),
            expdate = openreview.tools.datetime_millis(due_date + datetime.timedelta(minutes= 30)),
            readers = ['everyone'],
            writers = ['thecvf.com/CVPR/2023/Conference'],
            signatures = ['thecvf.com/CVPR/2023/Conference'],
            multiReply = False,
            reply = {
                'content': {
                    "decision": {
                    "description": "Please enter the decision for the paper (should match that of the primary AC).",
                    "value-radio": [
                        "Accept",
                        "Reject"
                    ],
                    "required": True
                    },
                    "confirmation": {
                    "description": "Please confirm that you approve the decision and the meta-review.",
                    "value-radio": [
                        "Yes",
                        "No"
                    ],
                    "required": True
                    }
                }
            }
        ))

        client.post_invitation(openreview.Invitation(id = 'thecvf.com/CVPR/2023/Conference/Paper4/-/Meta_Review_Confirmation',
            super='thecvf.com/CVPR/2023/Conference/-/Meta_Review_Confirmation',
            readers = ['thecvf.com/CVPR/2023/Conference', 'thecvf.com/CVPR/2023/Conference/Paper4/Secondary_Area_Chairs'],
            invitees = ['thecvf.com/CVPR/2023/Conference/Paper4/Secondary_Area_Chairs'],
            noninvitees = [],
            writers = ['thecvf.com/CVPR/2023/Conference'],
            signatures = ['thecvf.com/CVPR/2023/Conference'],
            multiReply = False,
            reply = {
                'forum': submission.id,
                'replyto': submission.id,
                'readers': {
                    'values': [
                        'thecvf.com/CVPR/2023/Conference/Program_Chairs',
                        'thecvf.com/CVPR/2023/Conference/Paper4/Senior_Area_Chairs',
                        'thecvf.com/CVPR/2023/Conference/Paper4/Area_Chairs'
                    ]
                },
                'writers': {
                    'values-copied': [
                        'thecvf.com/CVPR/2023/Conference/Program_Chairs',
                        '{signatures}'
                    ]
                },
                'signatures': {
                    'values-regex': 'thecvf.com/CVPR/2023/Conference/Paper4/Secondary_Area_Chair_.*'
                }
            }
        ))               

    def test_rebuttal_stage(self, conference, helpers, test_client, client):

        now = datetime.datetime.utcnow()

        conference.review_rebuttal_stage = openreview.stages.ReviewRebuttalStage(
            due_date=now + datetime.timedelta(minutes = 40),
            single_rebuttal=True,
            additional_fields={
                'pdf': {
                    'description': 'Upload a PDF file that ends with .pdf',
                    'order': 9,
                    'value-file': {
                        'fileTypes': ['pdf'],
                        'size': 50
                    },
                    'required':True
                }                
            }
        )
        conference.create_review_rebuttal_stage()

        assert client.get_invitation('thecvf.com/CVPR/2023/Conference/Paper5/-/Rebuttal')

        submissions=conference.get_submissions(number=5)
        assert len(submissions) == 1

        rebuttal_note=test_client.post_note(openreview.Note(
            invitation='thecvf.com/CVPR/2023/Conference/Paper5/-/Rebuttal',
            forum=submissions[0].id,
            replyto=submissions[0].id,
            readers=[
                'thecvf.com/CVPR/2023/Conference/Program_Chairs',
                'thecvf.com/CVPR/2023/Conference/Paper5/Authors'
            ],
            writers=['thecvf.com/CVPR/2023/Conference', 'thecvf.com/CVPR/2023/Conference/Paper5/Authors'],
            signatures=['thecvf.com/CVPR/2023/Conference/Paper5/Authors'],
            content={
                'rebuttal': 'Thanks for the detailed review!',
                'pdf': '/pdf/22234qweoiuweroi22234qweoiuweroi12345678.pdf'
            }
        ))

        helpers.await_queue()

        ## release the rebuttals
        conference.review_rebuttal_stage = openreview.stages.ReviewRebuttalStage(
            due_date=now + datetime.timedelta(minutes = 40),
            single_rebuttal=True,
            additional_fields={
                'pdf': {
                    'description': 'Upload a PDF file that ends with .pdf',
                    'order': 9,
                    'value-file': {
                        'fileTypes': ['pdf'],
                        'size': 50
                    },
                    'required':True
                }                
            },
            readers=[
                openreview.conference.ReviewRebuttalStage.Readers.SENIOR_AREA_CHAIRS_ASSIGNED,
                openreview.conference.ReviewRebuttalStage.Readers.AREA_CHAIRS_ASSIGNED,
                openreview.conference.ReviewRebuttalStage.Readers.REVIEWERS_ASSIGNED
            ]
        )
        conference.create_review_rebuttal_stage()

        rebuttals = client.get_notes(invitation='thecvf.com/CVPR/2023/Conference/Paper5/-/Rebuttal')
        assert len(rebuttals) == 1

        assert rebuttals[0].readers == [
            'thecvf.com/CVPR/2023/Conference/Program_Chairs',
            'thecvf.com/CVPR/2023/Conference/Paper5/Senior_Area_Chairs',
            'thecvf.com/CVPR/2023/Conference/Paper5/Area_Chairs',
            'thecvf.com/CVPR/2023/Conference/Paper5/Reviewers',
            'thecvf.com/CVPR/2023/Conference/Paper5/Authors'
        ]

    def test_metareview_revision_stage(self, conference, helpers, test_client, client):

        now = datetime.datetime.utcnow()

        conference.meta_review_stage = openreview.stages.MetaReviewStage(
            due_date=now + datetime.timedelta(minutes = 40),
            additional_fields={
                "preliminary_recommendation": {
                "order": 1,
                "value-radio": [
                    "Clear accept",
                    "Needs discussion",
                    "Clear reject"
                ],
                "required": True
                },
                "final_recommendation": {
                "order": 2,
                "value-radio": [
                    "Accept and select as a higlight",
                    "Accept",
                    "Reject"
                ],
                "required": False
                },
                'metareview': {
                    'order': 3,
                    'value-regex': '[\\S\\s]{1,5000}',
                    'description': 'Please provide an evaluation of the quality, clarity, originality and significance of this work, including a list of its pros and cons. Your comment or reply (max 5000 characters). Add formatting using Markdown and formulas using LaTeX. For more information see https://openreview.net/faq',
                    'required': True,
                    'markdown': True
                },
                "award_candidate": {
                    'description': '',
                    "order": 4,
                    "value-radio": [
                        "Yes",
                        "No"
                    ],
                    "required": True
                }
            },
            remove_fields=['recommendation', 'confidence']
        )

        conference.create_meta_review_stage()

        assert client.get_invitation('thecvf.com/CVPR/2023/Conference/Paper5/-/Meta_Review')

        submissions=conference.get_submissions(number=1)
        assert len(submissions) == 1

        ac_client = openreview.Client(username='ac1@cvpr.cc', password=helpers.strong_password)
        signatory_groups=client.get_groups(regex='thecvf.com/CVPR/2023/Conference/Paper1/Area_Chair_', signatory='ac1@cvpr.cc')
        assert len(signatory_groups) == 1

        metareview_note=ac_client.post_note(openreview.Note(
            invitation='thecvf.com/CVPR/2023/Conference/Paper1/-/Meta_Review',
            forum=submissions[0].id,
            replyto=submissions[0].id,
            readers=[
                'thecvf.com/CVPR/2023/Conference/Program_Chairs',
                'thecvf.com/CVPR/2023/Conference/Paper1/Senior_Area_Chairs',
                'thecvf.com/CVPR/2023/Conference/Paper1/Area_Chairs'
            ],
            nonreaders=['thecvf.com/CVPR/2023/Conference/Paper1/Authors'],
            writers=['thecvf.com/CVPR/2023/Conference/Program_Chairs', 'thecvf.com/CVPR/2023/Conference/Paper1/Area_Chairs'],
            signatures=[signatory_groups[0].id],
            content={
                'preliminary_recommendation': 'Needs discussion',
                'metareview': 'This is a metareview',
                'award_candidate': 'No'
            }
        ))

        helpers.await_queue()

        now = datetime.datetime.utcnow()

        conference.meta_review_revision_stage = openreview.stages.MetaReviewRevisionStage(
            due_date=now + datetime.timedelta(minutes = 40),
            additional_fields={
                "final_recommendation": {
                "order": 1,
                "value-radio": [
                    "Accept and select as a higlight",
                    "Accept",
                    "Reject"
                ],
                "required": False
                },
                'metareview': {
                    'order': 2,
                    'value-regex': '[\\S\\s]{1,5000}',
                    'description': 'Please provide an evaluation of the quality, clarity, originality and significance of this work, including a list of its pros and cons. Your comment or reply (max 5000 characters). Add formatting using Markdown and formulas using LaTeX. For more information see https://openreview.net/faq',
                    'required': True,
                    'markdown': True
                },
                "award_candidate": {
                    'description': '',
                    "order": 3,
                    "value-radio": [
                        "Yes",
                        "No"
                    ],
                    "required": True
                }
            },
            remove_fields=['recommendation', 'confidence']
        )

        conference.create_meta_review_revision_stage()

        assert client.get_invitation('thecvf.com/CVPR/2023/Conference/-/Meta_Review_Revision')
        invitations = client.get_invitations(super='thecvf.com/CVPR/2023/Conference/-/Meta_Review_Revision')
        assert invitations and len(invitations) == 1

        metareview_revision=ac_client.post_note(openreview.Note(
            invitation=f'{signatory_groups[0].id}/-/Meta_Review_Revision',
            forum=submissions[0].id,
            referent=metareview_note.id,
            readers=[
                'thecvf.com/CVPR/2023/Conference/Program_Chairs',
                'thecvf.com/CVPR/2023/Conference/Paper1/Senior_Area_Chairs',
                'thecvf.com/CVPR/2023/Conference/Paper1/Area_Chairs'
            ],
            nonreaders=['thecvf.com/CVPR/2023/Conference/Paper1/Authors'],
            writers=['thecvf.com/CVPR/2023/Conference/Program_Chairs', signatory_groups[0].id],
            signatures=[signatory_groups[0].id],
            content={
                'final_recommendation': 'Accept',
                'metareview': 'This is a metareview UPDATED',
                'award_candidate': 'No'
            }
        ))

        helpers.await_queue()
        assert metareview_revision

        references = client.get_references(referent=metareview_note.id)
        assert references and len(references) == 2

    def test_decision_stage(self, conference, helpers, client):

        pc_client=openreview.Client(username='pc@cvpr.cc', password=helpers.strong_password)
        request_form=pc_client.get_notes(invitation='openreview.net/Support/-/Request_Form')[0]

        now = datetime.datetime.utcnow()
        due_date = now + datetime.timedelta(days=3)
        start_date = now        

        request_form_note = pc_client.post_note(openreview.Note(
            invitation=f'openreview.net/Support/-/Request{request_form.number}/Decision_Stage',
            referent=request_form.id,
            forum=request_form.id,
            signatures=['~Program_CVPRChair1'],
            readers=['thecvf.com/CVPR/2023/Conference/Program_Chairs', 'openreview.net/Support'],
            writers=[],
            content={
                'decision_start_date': start_date.strftime('%Y/%m/%d'),
                'decision_deadline': due_date.strftime('%Y/%m/%d'),
                'decision_options': 'Accept, Reject',
                'make_decisions_public': 'No, decisions should NOT be revealed publicly when they are posted',
                'release_decisions_to_authors': 'Yes, decisions should be revealed when they are posted to the paper\'s authors',
                'release_decisions_to_reviewers': 'No, decisions should not be immediately revealed to the paper\'s reviewers',
                'release_decisions_to_area_chairs': 'Yes, decisions should be immediately revealed to the paper\'s area chairs',
                'notify_authors': 'No, I will send the emails to the authors',
            }))

        helpers.await_queue()

        assert client.get_invitation('thecvf.com/CVPR/2023/Conference/Paper5/-/Decision')

        submissions=conference.get_submissions(number=5)
        assert len(submissions) == 1

        rebuttal_note=pc_client.post_note(openreview.Note(
            invitation='thecvf.com/CVPR/2023/Conference/Paper5/-/Decision',
            forum=submissions[0].id,
            replyto=submissions[0].id,
            readers=[
                'thecvf.com/CVPR/2023/Conference/Program_Chairs',
                'thecvf.com/CVPR/2023/Conference/Paper5/Senior_Area_Chairs',
                'thecvf.com/CVPR/2023/Conference/Paper5/Area_Chairs',
                'thecvf.com/CVPR/2023/Conference/Paper5/Authors'
            ],
            writers=['thecvf.com/CVPR/2023/Conference/Program_Chairs'],
            signatures=['thecvf.com/CVPR/2023/Conference/Program_Chairs'],
            content={
                'title': 'Paper Decision',
                'decision': 'Accept'
            }
        ))

        helpers.await_queue()

    def test_camera_ready_stage(self, conference, helpers, client):

        pc_client=openreview.Client(username='pc@cvpr.cc', password=helpers.strong_password)
        request_form=pc_client.get_notes(invitation='openreview.net/Support/-/Request_Form')[0]

        now = datetime.datetime.utcnow()
        due_date = now + datetime.timedelta(days=3)
        start_date = now        

        ## Edit author console webfield to enable IEEE copyright
        author_group = client.get_group('thecvf.com/CVPR/2023/Conference/Authors')
        author_group.web = author_group.web.replace('showAuthorProfileStatus: true,', '''showAuthorProfileStatus: true,
        showIEEECopyright: true,
        IEEEPublicationTitle: "2023 IEEE/CVF Conference on Computer Vision and Pattern Recognition (CVPR)",
        IEEEArtSourceCode: 52729
        ''')
        client.post_group(author_group)

        request_form_note = pc_client.post_note(openreview.Note(
            invitation=f'openreview.net/Support/-/Request{request_form.number}/Submission_Revision_Stage',
            referent=request_form.id,
            forum=request_form.id,
            signatures=['~Program_CVPRChair1'],
            readers=['thecvf.com/CVPR/2023/Conference/Program_Chairs', 'openreview.net/Support'],
            writers=[],
            content={
                'submission_revision_name': 'Camera_Ready_Revision',
                'submission_revision_start_date': start_date.strftime('%Y/%m/%d'),
                'submission_revision_deadline': due_date.strftime('%Y/%m/%d'),
                'accepted_submissions_only': 'Enable revision for accepted submissions only',
                'submission_author_edition': 'Allow addition and removal of authors'
            }))

        helpers.await_queue()

        author_group = client.get_group('thecvf.com/CVPR/2023/Conference/Authors')
        assert 'showIEEECopyright: true' in author_group.web

    def test_post_decision_stage(self, conference, helpers, client):

        pc_client=openreview.Client(username='pc@cvpr.cc', password=helpers.strong_password)
        request_form=pc_client.get_notes(invitation='openreview.net/Support/-/Request_Form')[0]

        invitation = client.get_invitation('openreview.net/Support/-/Request{}/Post_Decision_Stage'.format(request_form.number))
        invitation.cdate = openreview.tools.datetime_millis(datetime.datetime.utcnow())
        client.post_invitation(invitation)

        request_form_note = pc_client.post_note(openreview.Note(
            invitation=f'openreview.net/Support/-/Request{request_form.number}/Post_Decision_Stage',
            referent=request_form.id,
            forum=request_form.id,
            signatures=['~Program_CVPRChair1'],
            readers=['thecvf.com/CVPR/2023/Conference/Program_Chairs', 'openreview.net/Support'],
            writers=[],
            content= {
                'reveal_authors': 'No, I don\'t want to reveal any author identities.',
                'submission_readers': 'Assigned program committee (assigned reviewers, assigned area chairs, assigned senior area chairs if applicable)',
                'send_decision_notifications': 'No, I will send the emails to the authors',
                'home_page_tab_names': {
                    'Accept': 'Accept',
                    'Reject': 'Submitted'
                }
            }
            ))

        helpers.await_queue()

        submissions=conference.get_submissions(number=5)
        assert len(submissions) == 1
        submission = submissions[0]

        assert submission.content['keywords'] == ''
        assert submission.content['venue'] == 'CVPR 2023'
        assert submission.content['venueid'] == 'thecvf.com/CVPR/2023/Conference'
        assert submission.pdate
        assert not submission.odate

        submissions=conference.get_submissions(number=4)
        assert len(submissions) == 1
        submission = submissions[0]

        assert submission.content['keywords'] == ''
        assert submission.content['venue'] == 'Submitted to CVPR 2023'
        assert submission.content['venueid'] == 'thecvf.com/CVPR/2023/Conference'
        assert not submission.pdate
        assert not submission.odate