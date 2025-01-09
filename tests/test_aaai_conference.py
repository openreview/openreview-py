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

class TestAAAIConference():

    def test_create_conference(self, client, openreview_client, helpers):

        now = datetime.datetime.utcnow()
        due_date = now + datetime.timedelta(days=3)

        # Post the request form note
        helpers.create_user('pc@aaai.org', 'Program', 'AAAIChair')
        pc_client = openreview.Client(username='pc@aaai.org', password=helpers.strong_password)


        helpers.create_user('ac1@aaai.org', 'AC', 'AAAIOne')
        helpers.create_user('ac2@aaai.org', 'AC', 'AAAITwo')
        helpers.create_user('senior_program_committee1@aaai.org', 'Senior Program Committee', 'AAAIOne')
        helpers.create_user('senior_program_committee2@aaai.org', 'Senior Program Committee', 'AAAITwo')
        helpers.create_user('program_committee1@aaai.org', 'Program Committee', 'AAAIOne')
        helpers.create_user('program_committee2@aaai.org', 'Program Committee', 'AAAITwo')
        helpers.create_user('program_committee3@aaai.org', 'Program Committee', 'AAAIThree')
        helpers.create_user('program_committee4@aaai.org', 'Program Committee', 'AAAIFour')
        helpers.create_user('peter@mail.com', 'Peter', 'SomeLastName') # Author

        request_form_note = pc_client.post_note(openreview.Note(
            invitation='openreview.net/Support/-/Request_Form',
            signatures=['~Program_AAAIChair1'],
            readers=[
                'openreview.net/Support',
                '~Program_AAAIChair1'
            ],
            writers=[],
            content={
                'title': 'The 39th Annual AAAI Conference on Artificial Intelligence',
                'Official Venue Name': 'The 39th Annual AAAI Conference on Artificial Intelligence',
                'Abbreviated Venue Name': 'AAAI 2025',
                'Official Website URL': 'https://aaai.org/conference/aaai-25/',
                'program_chair_emails': ['pc@aaai.org'],
                'contact_email': 'pc@aaai.org',
                'publication_chairs':'No, our venue does not have Publication Chairs',
                'Area Chairs (Metareviewers)': 'Yes, our venue has Area Chairs',
                'senior_area_chairs': 'Yes, our venue has Senior Area Chairs',
                'senior_area_chairs_assignment': 'Area Chairs',
                'ethics_chairs_and_reviewers': 'No, our venue does not have Ethics Chairs and Reviewers',
                'Venue Start Date': '2025/07/01',
                'Submission Deadline': due_date.strftime('%Y/%m/%d'),
                'Location': 'Philadelphia, PA',
                'submission_reviewer_assignment': 'Automatic',
                'Author and Reviewer Anonymity': 'Double-blind',
                'reviewer_identity': ['Program Chairs', 'Assigned Senior Area Chair', 'Assigned Area Chair'],
                'area_chair_identity': ['Program Chairs', 'Assigned Senior Area Chair', 'Assigned Area Chair', 'Assigned Reviewers'],
                'senior_area_chair_identity': ['Program Chairs', 'Assigned Senior Area Chair', 'Assigned Area Chair'],
                'submission_readers': 'Program chairs and paper authors only',
                'How did you hear about us?': 'ML conferences',
                'Expected Submissions': '10000',
                'use_recruitment_template': 'Yes',
                'api_version': '2',
                'submission_license': ['CC BY 4.0'],
                'iThenticate_plagiarism_check': 'No',
                'iThenticate_plagiarism_check_api_key': '1234',
                'iThenticate_plagiarism_check_api_base_url': 'test.turnitin.com',
                'iThenticate_plagiarism_check_committee_readers': ['Area_Chairs', 'Senior_Program_Committee'],
                'iThenticate_plagiarism_check_add_to_index': 'Yes',
            }))

        helpers.await_queue()

        # Use super user to update the roles
        request_form_note.content['reviewer_roles'] = ['Program_Committee']
        request_form_note.content['area_chair_roles'] = ['Senior_Program_Committee']
        request_form_note.content['senior_area_chair_roles'] = ['Area_Chairs']
        client.post_note(request_form_note)

        helpers.await_queue()

        # Post a deploy note
        client.post_note(openreview.Note(
            content={'venue_id': 'AAAI.org/2025/Conference'},
            forum=request_form_note.forum,
            invitation='openreview.net/Support/-/Request{}/Deploy'.format(request_form_note.number),
            readers=['openreview.net/Support'],
            referent=request_form_note.forum,
            replyto=request_form_note.forum,
            signatures=['openreview.net/Support'],
            writers=['openreview.net/Support']
        ))

        helpers.await_queue()

        assert openreview_client.get_group('AAAI.org/2025/Conference')
        assert openreview_client.get_group('AAAI.org/2025/Conference/Area_Chairs')
        assert openreview_client.get_group('AAAI.org/2025/Conference/Senior_Program_Committee')
        assert openreview_client.get_group('AAAI.org/2025/Conference/Program_Committee')
        assert openreview_client.get_group('AAAI.org/2025/Conference/Authors')

        submission_invitation = openreview_client.get_invitation('AAAI.org/2025/Conference/-/Submission')
        assert submission_invitation
        assert submission_invitation.duedate

        assert openreview_client.get_invitation('AAAI.org/2025/Conference/Program_Committee/-/Expertise_Selection')
        assert openreview_client.get_invitation('AAAI.org/2025/Conference/Senior_Program_Committee/-/Expertise_Selection')
        assert openreview_client.get_invitation('AAAI.org/2025/Conference/Area_Chairs/-/Expertise_Selection')

        pc_client.post_note(openreview.Note(
            invitation=f'openreview.net/Support/-/Request{request_form_note.number}/Revision',
            forum=request_form_note.id,
            readers=['AAAI.org/2025/Conference/Program_Chairs', 'openreview.net/Support'],
            referent=request_form_note.id,
            replyto=request_form_note.id,
            signatures=['~Program_AAAIChair1'],
            writers=[],
            content={
                'title': 'The 39th Annual AAAI Conference on Artificial Intelligence',
                'Official Venue Name': 'The 39th Annual AAAI Conference on Artificial Intelligence',
                'Abbreviated Venue Name': 'AAAI 2025',
                'Official Website URL': 'https://aaai.org/conference/aaai-25/',
                'program_chair_emails': ['pc@aaai.org'],
                'contact_email': 'pc@aaai.org',
                'publication_chairs':'No, our venue does not have Publication Chairs',
                'Venue Start Date': '2025/07/01',
                'Submission Deadline': due_date.strftime('%Y/%m/%d'),
                'Location': 'Philadelphia, PA',
                'submission_reviewer_assignment': 'Automatic',
                'How did you hear about us?': 'ML conferences',
                'Expected Submissions': '10000',
                'use_recruitment_template': 'Yes',
                'Additional Submission Options': {
                    "iThenticate_agreement": {
                        "order": 10,
                        "description": "AAAI is using iThenticate for plagiarism detection. By submitting your paper, you agree to share your PDF with iThenticate and accept iThenticate's End User License Agreement. Read the full terms here: https://static.turnitin.com/eula/v1beta/en-us/eula.html",
                        "value": {
                        "param": {
                            "fieldName": "iThenticate Agreement",
                            "type": "string",
                            "optional": False,
                            "input": "checkbox",
                            "enum": [
                                "Yes, I agree to iThenticate's EULA agreement version: v2beta"
                            ]
                        }
                        }
                    },
                }
            }
        ))
        helpers.await_queue()

        submission_invitation = openreview_client.get_invitation('AAAI.org/2025/Conference/-/Submission')
        assert submission_invitation
        assert 'iThenticate_agreement' in submission_invitation.edit['note']['content']

    def test_sac_recruitment(self, client, openreview_client, helpers, request_page, selenium):

        pc_client=openreview.Client(username='pc@aaai.org', password=helpers.strong_password)
        request_form=pc_client.get_notes(invitation='openreview.net/Support/-/Request_Form')[0]

        reviewer_details = '''ac1@aaai.org, AC AAAIOne\nac2@aaai.org, AC AAAITwo'''
        pc_client.post_note(openreview.Note(
            content={
                'title': 'Recruitment',
                'invitee_role': 'Area_Chairs',
                'invitee_details': reviewer_details,
                'invitation_email_subject': '[AAAI 2025] Invitation to serve as {{invitee_role}}',
                'invitation_email_content': 'Dear {{fullname}},\n\nYou have been nominated by the program chair committee of AAAI to serve as {{invitee_role}}.\n\n{{invitation_url}}\n\nCheers!\n\nProgram Chairs'
            },
            forum=request_form.forum,
            replyto=request_form.forum,
            invitation='openreview.net/Support/-/Request{}/Recruitment'.format(request_form.number),
            readers=['AAAI.org/2025/Conference/Program_Chairs', 'openreview.net/Support'],
            signatures=['~Program_AAAIChair1'],
            writers=[]
        ))

        helpers.await_queue()

        assert len(openreview_client.get_group('AAAI.org/2025/Conference/Area_Chairs').members) == 0
        group = openreview_client.get_group('AAAI.org/2025/Conference/Area_Chairs/Invited')
        assert len(group.members) == 2
        assert group.readers == ['AAAI.org/2025/Conference', 'AAAI.org/2025/Conference/Area_Chairs/Invited']

        messages = openreview_client.get_messages(subject = '[AAAI 2025] Invitation to serve as Area Chair')
        assert len(messages) == 2

        for message in messages:
            text = message['content']['text']

            invitation_url = re.search('https://.*\n', text).group(0).replace('https://openreview.net', 'http://localhost:3030').replace('&amp;', '&')[:-1]
            helpers.respond_invitation(selenium, request_page, invitation_url, accept=True)

        helpers.await_queue_edit(openreview_client, invitation='AAAI.org/2025/Conference/Area_Chairs/-/Recruitment', count=2)

        messages = client.get_messages(subject='[AAAI 2025] Area Chair Invitation accepted')
        assert len(messages) == 2

        assert len(openreview_client.get_group('AAAI.org/2025/Conference/Area_Chairs').members) == 2
        assert len(openreview_client.get_group('AAAI.org/2025/Conference/Area_Chairs/Invited').members) == 2

    def test_ac_recruitment(self, client, openreview_client, helpers, request_page, selenium):

        pc_client=openreview.Client(username='pc@aaai.org', password=helpers.strong_password)
        request_form=pc_client.get_notes(invitation='openreview.net/Support/-/Request_Form')[0]

        reviewer_details = '''senior_program_committee1@aaai.org, Senior Program Committee AAAIOne\nsenior_program_committee2@aaai.org, Senior Program Committee AAAITwo'''
        pc_client.post_note(openreview.Note(
            content={
                'title': 'Recruitment',
                'invitee_role': 'Senior_Program_Committee',
                'invitee_details': reviewer_details,
                'invitation_email_subject': '[AAAI 2025] Invitation to serve as {{invitee_role}}',
                'invitation_email_content': 'Dear {{fullname}},\n\nYou have been nominated by the program chair committee of AAAI to serve as {{invitee_role}}.\n\n{{invitation_url}}\n\nCheers!\n\nProgram Chairs'
            },
            forum=request_form.forum,
            replyto=request_form.forum,
            invitation='openreview.net/Support/-/Request{}/Recruitment'.format(request_form.number),
            readers=['AAAI.org/2025/Conference/Program_Chairs', 'openreview.net/Support'],
            signatures=['~Program_AAAIChair1'],
            writers=[]
        ))

        helpers.await_queue()

        assert len(openreview_client.get_group('AAAI.org/2025/Conference/Senior_Program_Committee').members) == 0
        assert len(openreview_client.get_group('AAAI.org/2025/Conference/Senior_Program_Committee/Invited').members) == 2

        messages = openreview_client.get_messages(subject = '[AAAI 2025] Invitation to serve as Senior Program Committee')
        assert len(messages) == 2

        for message in messages:
            text = message['content']['text']

            invitation_url = re.search('https://.*\n', text).group(0).replace('https://openreview.net', 'http://localhost:3030').replace('&amp;', '&')[:-1]
            helpers.respond_invitation(selenium, request_page, invitation_url, accept=True)

        helpers.await_queue_edit(openreview_client, invitation='AAAI.org/2025/Conference/Senior_Program_Committee/-/Recruitment', count=2)

        messages = client.get_messages(subject='[AAAI 2025] Senior Program Committee Invitation accepted')
        assert len(messages) == 2

        assert len(openreview_client.get_group('AAAI.org/2025/Conference/Senior_Program_Committee').members) == 2
        assert len(openreview_client.get_group('AAAI.org/2025/Conference/Senior_Program_Committee/Invited').members) == 2

    def test_reviewer_recruitment(self, client, openreview_client, helpers, request_page, selenium):

        pc_client=openreview.Client(username='pc@aaai.org', password=helpers.strong_password)
        request_form=pc_client.get_notes(invitation='openreview.net/Support/-/Request_Form')[0]

        reviewer_details = '''program_committee1@aaai.org, Program Committee AAAIOne
program_committee2@aaai.org, Program Committee AAAITwo
program_committee3@aaai.org, Program Committee AAAIThree
program_committee4@yahoo.com, Program Committee AAAIFour
'''
        pc_client.post_note(openreview.Note(
            content={
                'title': 'Recruitment',
                'invitee_role': 'Program_Committee',
                'invitee_details': reviewer_details,
                'invitee_reduced_load': ["1", "2", "3"],
                'invitation_email_subject': '[AAAI 2025] Invitation to serve as {{invitee_role}}',
                'invitation_email_content': 'Dear {{fullname}},\n\nYou have been nominated by the program chair committee of AAAI to serve as {{invitee_role}}.\n\n{{invitation_url}}\n\nCheers!\n\nProgram Chairs'
            },
            forum=request_form.forum,
            replyto=request_form.forum,
            invitation='openreview.net/Support/-/Request{}/Recruitment'.format(request_form.number),
            readers=['AAAI.org/2025/Conference/Program_Chairs', 'openreview.net/Support'],
            signatures=['~Program_AAAIChair1'],
            writers=[]
        ))

        helpers.await_queue()

        assert len(openreview_client.get_group('AAAI.org/2025/Conference/Program_Committee').members) == 0
        assert len(openreview_client.get_group('AAAI.org/2025/Conference/Program_Committee/Invited').members) == 4
        assert len(openreview_client.get_group('AAAI.org/2025/Conference/Program_Committee/Declined').members) == 0

        messages = openreview_client.get_messages(subject = '[AAAI 2025] Invitation to serve as Program Committee')
        assert len(messages) == 4

        for message in messages:
            text = message['content']['text']

            invitation_url = re.search('https://.*\n', text).group(0).replace('https://openreview.net', 'http://localhost:3030').replace('&amp;', '&')[:-1]
            helpers.respond_invitation(selenium, request_page, invitation_url, accept=True, quota=3)

        helpers.await_queue_edit(openreview_client, invitation='AAAI.org/2025/Conference/Program_Committee/-/Recruitment', count=8)

        messages = client.get_messages(subject='[AAAI 2025] Program Committee Invitation accepted with reduced load')
        assert len(messages) == 4

        assert len(openreview_client.get_group('AAAI.org/2025/Conference/Program_Committee').members) == 4
        assert len(openreview_client.get_group('AAAI.org/2025/Conference/Program_Committee/Invited').members) == 4
        assert len(openreview_client.get_group('AAAI.org/2025/Conference/Program_Committee/Declined').members) == 0

        messages = openreview_client.get_messages(to = 'program_committee4@yahoo.com', subject = '[AAAI 2025] Invitation to serve as Program Committee')
        invitation_url = re.search('https://.*\n', messages[0]['content']['text']).group(0).replace('https://openreview.net', 'http://localhost:3030').replace('&amp;', '&')[:-1]
        helpers.respond_invitation(selenium, request_page, invitation_url, accept=False)

        helpers.await_queue_edit(openreview_client, invitation='AAAI.org/2025/Conference/Program_Committee/-/Recruitment', count=9)

        assert len(openreview_client.get_group('AAAI.org/2025/Conference/Program_Committee').members) == 3
        assert len(openreview_client.get_group('AAAI.org/2025/Conference/Program_Committee/Invited').members) == 4
        assert len(openreview_client.get_group('AAAI.org/2025/Conference/Program_Committee/Declined').members) == 1

        reviewer_client = openreview.api.OpenReviewClient(username='program_committee1@aaai.org', password=helpers.strong_password)

        request_page(selenium, "http://localhost:3030/group?id=AAAI.org/2025/Conference/Program_Committee", reviewer_client.token, wait_for_element='header')
        header = selenium.find_element(By.ID, 'header')
        assert 'You have agreed to review up to 1 submission' in header.text

    def test_submissions(self, client, openreview_client, helpers, test_client, request_page, selenium):

        test_client = openreview.api.OpenReviewClient(token=test_client.token)

        domains = ['umass.edu', 'amazon.com', 'fb.com', 'cs.umass.edu', 'google.com', 'mit.edu', 'deepmind.com', 'co.ux', 'apple.com', 'nvidia.com']
        subject_areas = ['Algorithms: Approximate Inference', 'Algorithms: Belief Propagation', 'Learning: Deep Learning', 'Learning: General', 'Learning: Nonparametric Bayes', 'Methodology: Bayesian Methods', 'Methodology: Calibration', 'Principles: Causality', 'Principles: Cognitive Models', 'Representation: Constraints', 'Representation: Dempster-Shafer', 'Representation: Other']
        for i in range(1,11):
            note = openreview.api.Note(
                content = {
                    'title': { 'value': 'Paper title ' + str(i) },
                    'abstract': { 'value': 'This is an abstract ' + str(i) },
                    'authorids': { 'value': ['~SomeFirstName_User1', 'peter@mail.com', 'andrew@' + domains[i % 10]] },
                    'authors': { 'value': ['SomeFirstName User', 'Peter SomeLastName', 'Andrew Mc'] },
                    'keywords': { 'value': ['machine learning', 'nlp'] },
                    'pdf': {'value': '/pdf/' + 'p' * 40 +'.pdf' },
                    'iThenticate_agreement': { 'value': 'Yes, I agree to iThenticate\'s EULA agreement version: v2beta' },
                }
            )
            test_client.post_note_edit(invitation='AAAI.org/2025/Conference/-/Submission',
                signatures=['~SomeFirstName_User1'],
                note=note)

        helpers.await_queue_edit(openreview_client, invitation='AAAI.org/2025/Conference/-/Submission', count=10)

        authors_group = openreview_client.get_group(id='AAAI.org/2025/Conference/Authors')

        for i in range(1,10):
            assert f'AAAI.org/2025/Conference/Submission{i}/Authors' in authors_group.members


    def test_post_submission(self, client, openreview_client, test_client, helpers, request_page, selenium):

        pc_client=openreview.Client(username='pc@aaai.org', password=helpers.strong_password)
        request_form=pc_client.get_notes(invitation='openreview.net/Support/-/Request_Form')[0]
        venue = openreview.get_conference(client, request_form.id, support_user='openreview.net/Support')

        ## close the submissions
        now = datetime.datetime.utcnow()
        due_date = now - datetime.timedelta(days=1)
        exp_date = now + datetime.timedelta(days=10)
        pc_client.post_note(openreview.Note(
            content={
                'title': 'The 39th Annual AAAI Conference on Artificial Intelligence',
                'Official Venue Name': 'The 39th Annual AAAI Conference on Artificial Intelligence',
                'Abbreviated Venue Name': 'AAAI 2025',
                'Official Website URL': 'https://aaai.org/conference/aaai-25/',
                'program_chair_emails': ['pc@aaai.org'],
                'contact_email': 'pc@aaai.org',
                'publication_chairs':'No, our venue does not have Publication Chairs',
                'Venue Start Date': '2025/07/01',
                'Submission Deadline': due_date.strftime('%Y/%m/%d'),
                'Location': 'Philadelphia, PA',
                'submission_reviewer_assignment': 'Automatic',
                'reviewer_identity': ['Program Chairs', 'Assigned Senior Area Chair', 'Assigned Area Chair'],
                'area_chair_identity': ['Program Chairs', 'Assigned Senior Area Chair', 'Assigned Area Chair', 'Assigned Reviewers'],
                'senior_area_chair_identity': ['Program Chairs', 'Assigned Senior Area Chair', 'Assigned Area Chair'],
                'Expected Submissions': '100',
                'withdraw_submission_expiration': exp_date.strftime('%Y/%m/%d')
            },
            forum=request_form.forum,
            invitation='openreview.net/Support/-/Request{}/Revision'.format(request_form.number),
            readers=['AAAI.org/2025/Conference/Program_Chairs', 'openreview.net/Support'],
            referent=request_form.forum,
            replyto=request_form.forum,
            signatures=['~Program_AAAIChair1'],
            writers=[]
        ))

        helpers.await_queue()


        ## make submissions visible to ACs only
        pc_client.post_note(openreview.Note(
            content= {
                'force': 'Yes',
                'submission_readers': 'Assigned program committee (assigned reviewers, assigned area chairs, assigned senior area chairs if applicable)'
            },
            forum= request_form.id,
            invitation= f'openreview.net/Support/-/Request{request_form.number}/Post_Submission',
            readers= ['AAAI.org/2025/Conference/Program_Chairs', 'openreview.net/Support'],
            referent= request_form.id,
            replyto= request_form.id,
            signatures= ['~Program_AAAIChair1'],
            writers= [],
        ))

        helpers.await_queue()

        helpers.await_queue_edit(openreview_client, 'AAAI.org/2025/Conference/-/Post_Submission-0-1', count=3)

        submissions = openreview_client.get_notes(invitation='AAAI.org/2025/Conference/-/Submission', sort='number:asc')
        assert len(submissions) == 10
        assert ['AAAI.org/2025/Conference',
        'AAAI.org/2025/Conference/Submission1/Area_Chairs',
        'AAAI.org/2025/Conference/Submission1/Senior_Program_Committee',
        'AAAI.org/2025/Conference/Submission1/Program_Committee',
        'AAAI.org/2025/Conference/Submission1/Authors'] == submissions[0].readers

    def test_plagiarism_check_edge_invitation(self, client, openreview_client, helpers, test_client):

        pc_client = openreview.Client(username='pc@aaai.org', password=helpers.strong_password)
        request_form = pc_client.get_notes(invitation='openreview.net/Support/-/Request_Form')[0]
        venue = openreview.get_conference(client, request_form.id, support_user='openreview.net/Support')

        venue.iThenticate_plagiarism_check = True

        venue.invitation_builder.set_iThenticate_plagiarism_check_invitation()

        pc_client_v2 = openreview.api.OpenReviewClient(username='pc@aaai.org', password=helpers.strong_password)

        invitation = pc_client_v2.get_invitation('AAAI.org/2025/Conference/-/iThenticate_Plagiarism_Check')
        assert invitation.edit['nonreaders'] == ['AAAI.org/2025/Conference/Submission${{2/head}/number}/Authors']
        assert invitation.edit['readers'] == ['AAAI.org/2025/Conference',
        'AAAI.org/2025/Conference/Submission${{2/head}/number}/Area_Chairs',
        'AAAI.org/2025/Conference/Submission${{2/head}/number}/Senior_Program_Committee']

        assert pc_client_v2.get_edges_count(invitation='AAAI.org/2025/Conference/-/iThenticate_Plagiarism_Check') == 0
    
    
    def test_setup_matching(self, client, openreview_client, helpers, test_client):

        pc_client=openreview.Client(username='pc@aaai.org', password=helpers.strong_password)
        request_form=pc_client.get_notes(invitation='openreview.net/Support/-/Request_Form')[0]
        venue = openreview.get_conference(client, request_form.id, support_user='openreview.net/Support')

        openreview.tools.replace_members_with_ids(openreview_client, openreview_client.get_group('AAAI.org/2025/Conference/Area_Chairs'))

        with open(os.path.join(os.path.dirname(__file__), 'data/rev_scores_venue.csv'), 'w') as file_handle:
            writer = csv.writer(file_handle)
            for sac in openreview_client.get_group('AAAI.org/2025/Conference/Area_Chairs').members:
                for ac in openreview_client.get_group('AAAI.org/2025/Conference/Senior_Program_Committee').members:
                    writer.writerow([ac, sac, round(random.random(), 2)])

        affinity_scores_url = client.put_attachment(os.path.join(os.path.dirname(__file__), 'data/rev_scores_venue.csv'), f'openreview.net/Support/-/Request{request_form.number}/Paper_Matching_Setup', 'upload_affinity_scores')

        client.post_note(openreview.Note(
            content={
                'title': 'Paper Matching Setup',
                'matching_group': 'AAAI.org/2025/Conference/Area_Chairs',
                'compute_conflicts': 'No',
                'compute_affinity_scores': 'No',
                'upload_affinity_scores': affinity_scores_url
            },
            forum=request_form.id,
            replyto=request_form.id,
            invitation=f'openreview.net/Support/-/Request{request_form.number}/Paper_Matching_Setup',
            readers=['AAAI.org/2025/Conference/Program_Chairs', 'openreview.net/Support'],
            signatures=['~Program_AAAIChair1'],
            writers=[]
        ))
        helpers.await_queue()

        pc_client_v2=openreview.api.OpenReviewClient(username='pc@aaai.org', password=helpers.strong_password)
        assert pc_client_v2.get_edges_count(invitation='AAAI.org/2025/Conference/Area_Chairs/-/Affinity_Score') == 4

        openreview_client.post_edge(openreview.api.Edge(
            invitation = 'AAAI.org/2025/Conference/Area_Chairs/-/Proposed_Assignment',
            head = '~Senior_Program_Committee_AAAIOne1',
            tail = '~AC_AAAIOne1',
            signatures = ['AAAI.org/2025/Conference/Program_Chairs'],
            weight = 1,
            label = 'ac-matching'
        ))

        openreview_client.post_edge(openreview.api.Edge(
            invitation = 'AAAI.org/2025/Conference/Area_Chairs/-/Proposed_Assignment',
            head = '~Senior_Program_Committee_AAAITwo1',
            tail = '~AC_AAAITwo1',
            signatures = ['AAAI.org/2025/Conference/Program_Chairs'],
            weight = 1,
            label = 'ac-matching'
        ))

        venue = openreview.helpers.get_conference(pc_client, request_form.id, setup=False)

        venue.set_assignments(assignment_title='ac-matching', committee_id='AAAI.org/2025/Conference/Area_Chairs')

        sac_assignment_count = pc_client_v2.get_edges_count(invitation='AAAI.org/2025/Conference/Area_Chairs/-/Assignment')
        assert sac_assignment_count == 2

        submissions = pc_client_v2.get_notes(invitation='AAAI.org/2025/Conference/-/Submission', sort='number:asc')

        openreview.tools.replace_members_with_ids(openreview_client, openreview_client.get_group('AAAI.org/2025/Conference/Senior_Program_Committee'))

        with open(os.path.join(os.path.dirname(__file__), 'data/rev_scores_venue.csv'), 'w') as file_handle:
            writer = csv.writer(file_handle)
            for submission in submissions:
                for ac in openreview_client.get_group('AAAI.org/2025/Conference/Senior_Program_Committee').members:
                    writer.writerow([submission.id, ac, round(random.random(), 2)])

        affinity_scores_url = client.put_attachment(os.path.join(os.path.dirname(__file__), 'data/rev_scores_venue.csv'), f'openreview.net/Support/-/Request{request_form.number}/Paper_Matching_Setup', 'upload_affinity_scores')

        ## setup matching data before starting bidding
        client.post_note(openreview.Note(
            content={
                'title': 'Paper Matching Setup',
                'matching_group': 'AAAI.org/2025/Conference/Senior_Program_Committee',
                'compute_conflicts': 'NeurIPS',
                'compute_conflicts_N_years': '3',
                'compute_affinity_scores': 'No',
                'upload_affinity_scores': affinity_scores_url
            },
            forum=request_form.id,
            replyto=request_form.id,
            invitation=f'openreview.net/Support/-/Request{request_form.number}/Paper_Matching_Setup',
            readers=['AAAI.org/2025/Conference/Program_Chairs', 'openreview.net/Support'],
            signatures=['~Program_AAAIChair1'],
            writers=[]
        ))
        helpers.await_queue()

        assert openreview_client.get_invitation('AAAI.org/2025/Conference/Senior_Program_Committee/-/Conflict')
        assert openreview_client.get_invitation('AAAI.org/2025/Conference/Senior_Program_Committee/-/Affinity_Score')

        affinity_score_count =  openreview_client.get_edges_count(invitation='AAAI.org/2025/Conference/Senior_Program_Committee/-/Affinity_Score')
        assert affinity_score_count == 10 * 2 ## submissions * ACs
        assert pc_client_v2.get_edges_count(invitation='AAAI.org/2025/Conference/Senior_Program_Committee/-/Conflict') == 0

        openreview.tools.replace_members_with_ids(openreview_client, openreview_client.get_group('AAAI.org/2025/Conference/Program_Committee'))

        with open(os.path.join(os.path.dirname(__file__), 'data/rev_scores_venue.csv'), 'w') as file_handle:
            writer = csv.writer(file_handle)
            for submission in submissions:
                for ac in openreview_client.get_group('AAAI.org/2025/Conference/Program_Committee').members:
                    writer.writerow([submission.id, ac, round(random.random(), 2)])

        affinity_scores_url = client.put_attachment(os.path.join(os.path.dirname(__file__), 'data/rev_scores_venue.csv'), f'openreview.net/Support/-/Request{request_form.number}/Paper_Matching_Setup', 'upload_affinity_scores')

        client.post_note(openreview.Note(
            content={
                'title': 'Paper Matching Setup',
                'matching_group': 'AAAI.org/2025/Conference/Program_Committee',
                'compute_conflicts': 'NeurIPS',
                'compute_conflicts_N_years': '3',
                'compute_affinity_scores': 'No',
                'upload_affinity_scores': affinity_scores_url
            },
            forum=request_form.id,
            replyto=request_form.id,
            invitation=f'openreview.net/Support/-/Request{request_form.number}/Paper_Matching_Setup',
            readers=['AAAI.org/2025/Conference/Program_Chairs', 'openreview.net/Support'],
            signatures=['~Program_AAAIChair1'],
            writers=[]
        ))
        helpers.await_queue()

        assert openreview_client.get_invitation('AAAI.org/2025/Conference/Program_Committee/-/Conflict')

        assert openreview_client.get_edges_count(invitation='AAAI.org/2025/Conference/Program_Committee/-/Conflict') == 0

        affinity_scores =  openreview_client.get_grouped_edges(invitation='AAAI.org/2025/Conference/Program_Committee/-/Affinity_Score', groupby='id')
        assert affinity_scores
        assert len(affinity_scores) == 10 * 3 ## submissions * reviewers

    def test_ac_bidding(self, client, openreview_client, helpers, test_client, request_page, selenium):
        pc_client=openreview.Client(username='pc@aaai.org', password=helpers.strong_password)
        request_form=pc_client.get_notes(invitation='openreview.net/Support/-/Request_Form')[0]
        now = datetime.datetime.utcnow()
        due_date = now + datetime.timedelta(days=3)

        ## Hide the pdf 
        pc_client.post_note(openreview.Note(
            content= {
                'force': 'Yes',
                'submission_readers': 'All program committee (all reviewers, all area chairs, all senior area chairs if applicable)',
                'hide_fields': ['pdf']
            },
            forum= request_form.id,
            invitation= f'openreview.net/Support/-/Request{request_form.number}/Post_Submission',
            readers= ['AAAI.org/2025/Conference/Program_Chairs', 'openreview.net/Support'],
            referent= request_form.id,
            replyto= request_form.id,
            signatures= ['~Program_AAAIChair1'],
            writers= [],
        ))

        helpers.await_queue()

        helpers.await_queue_edit(openreview_client, 'AAAI.org/2025/Conference/-/Post_Submission-0-1', count=4)

        ac_client = openreview.api.OpenReviewClient(username = 'senior_program_committee1@aaai.org', password=helpers.strong_password)
        submissions = ac_client.get_notes(invitation='AAAI.org/2025/Conference/-/Submission', sort='number:asc')
        assert len(submissions) == 10
        assert ['AAAI.org/2025/Conference',
        'AAAI.org/2025/Conference/Area_Chairs',
        'AAAI.org/2025/Conference/Senior_Program_Committee',
        'AAAI.org/2025/Conference/Program_Committee',
        'AAAI.org/2025/Conference/Submission1/Authors'] == submissions[0].readers
        assert ['AAAI.org/2025/Conference',
        'AAAI.org/2025/Conference/Submission1/Authors'] == submissions[0].writers
        assert ['AAAI.org/2025/Conference/Submission1/Authors'] == submissions[0].signatures
        assert 'authorids' not in submissions[0].content
        assert 'authors' not in submissions[0].content
        assert 'pdf' not in submissions[0].content

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
            readers=['AAAI.org/2025/Conference/Program_Chairs', 'openreview.net/Support'],
            signatures=['~Program_AAAIChair1'],
            writers=[]
        ))

        helpers.await_queue()

        invitation = openreview_client.get_invitation('AAAI.org/2025/Conference/Senior_Program_Committee/-/Bid')
        assert invitation.edit['tail']['param']['options']['group'] == 'AAAI.org/2025/Conference/Senior_Program_Committee'
        
        # Check that SPC Bid Console loads
        request_page(selenium, f'http://localhost:3030/invitation?id={invitation.id}', ac_client.token, wait_for_element='header')
        header = selenium.find_element(By.ID, 'header')
        assert 'Senior Program Committee Bidding Console' in header.text

        invitation = openreview_client.get_invitation('AAAI.org/2025/Conference/Program_Committee/-/Bid')
        assert invitation.edit['tail']['param']['options']['group'] == 'AAAI.org/2025/Conference/Program_Committee'

        # Check that PC Bid Console loads
        reviewer_client = openreview.api.OpenReviewClient(username = 'program_committee1@aaai.org', password=helpers.strong_password)
        request_page(selenium, f'http://localhost:3030/invitation?id={invitation.id}', reviewer_client.token, wait_for_element='header')
        header = selenium.find_element(By.ID, 'header')
        assert 'Program Committee Bidding Console' in header.text
    
    def test_set_assignments(self, client, openreview_client, helpers, test_client):

        pc_client=openreview.Client(username='pc@aaai.org', password=helpers.strong_password)
        pc_client_v2=openreview.api.OpenReviewClient(username='pc@aaai.org', password=helpers.strong_password)
        request_form=pc_client.get_notes(invitation='openreview.net/Support/-/Request_Form')[0]
        venue = openreview.helpers.get_conference(pc_client, request_form.id, setup=False)
        submissions = pc_client_v2.get_notes(content= { 'venueid': 'AAAI.org/2025/Conference/Submission'}, sort='number:asc')

        reviewers_proposed_edges = []
        for i in range(0,10):
            for r in ['~Program_Committee_AAAIOne1', '~Program_Committee_AAAITwo1', '~Program_Committee_AAAIThree1']:
                reviewers_proposed_edges.append(openreview.api.Edge(
                    invitation = 'AAAI.org/2025/Conference/Program_Committee/-/Proposed_Assignment',
                    head = submissions[i].id,
                    tail = r,
                    signatures = ['AAAI.org/2025/Conference/Program_Chairs'],
                    weight = 1,
                    label = 'program-committee-matching',
                    readers = ["AAAI.org/2025/Conference", f"AAAI.org/2025/Conference/Submission{submissions[i].number}/Area_Chairs", f"AAAI.org/2025/Conference/Submission{submissions[i].number}/Senior_Program_Committee", r],
                    nonreaders = [f"AAAI.org/2025/Conference/Submission{submissions[i].number}/Authors"],
                    writers = ["AAAI.org/2025/Conference", f"AAAI.org/2025/Conference/Submission{submissions[i].number}/Area_Chairs", f"AAAI.org/2025/Conference/Submission{submissions[i].number}/Senior_Program_Committee"]
                ))

            openreview_client.post_edge(openreview.api.Edge(
                invitation = 'AAAI.org/2025/Conference/Senior_Program_Committee/-/Proposed_Assignment',
                head = submissions[i].id,
                tail = '~Senior_Program_Committee_AAAIOne1' if i % 2 == 0 else '~Senior_Program_Committee_AAAITwo1',
                signatures = ['AAAI.org/2025/Conference/Program_Chairs'],
                weight = 1,
                label = 'spc-matching'
            ))



        openreview.tools.post_bulk_edges(client=openreview_client, edges=reviewers_proposed_edges)

        venue.set_assignments(assignment_title='spc-matching', committee_id='AAAI.org/2025/Conference/Senior_Program_Committee')

        ac_group = pc_client_v2.get_group('AAAI.org/2025/Conference/Submission1/Senior_Program_Committee')
        assert ['~Senior_Program_Committee_AAAIOne1'] == ac_group.members

        ac_group = pc_client_v2.get_group('AAAI.org/2025/Conference/Submission2/Senior_Program_Committee')
        assert ['~Senior_Program_Committee_AAAITwo1'] == ac_group.members

        sac_group = pc_client_v2.get_group('AAAI.org/2025/Conference/Submission1/Area_Chairs')
        assert ['~AC_AAAIOne1'] == sac_group.members

        sac_group = pc_client_v2.get_group('AAAI.org/2025/Conference/Submission2/Area_Chairs')
        assert ['~AC_AAAITwo1'] == sac_group.members

        venue.set_assignments(assignment_title='program-committee-matching', committee_id='AAAI.org/2025/Conference/Program_Committee', enable_reviewer_reassignment=True) 

        reviewer_group = pc_client_v2.get_group('AAAI.org/2025/Conference/Submission1/Program_Committee')
        assert len(reviewer_group.members) == 3
        assert '~Program_Committee_AAAIOne1' in reviewer_group.members
        assert '~Program_Committee_AAAITwo1' in reviewer_group.members
        assert '~Program_Committee_AAAIThree1' in reviewer_group.members

    def test_review_stage(self, client, openreview_client, helpers, selenium, request_page):

        pc_client=openreview.Client(username='pc@aaai.org', password=helpers.strong_password)
        request_form=pc_client.get_notes(invitation='openreview.net/Support/-/Request_Form')[0]

        now = datetime.datetime.utcnow()
        start_date = now - datetime.timedelta(days=2)
        due_date = now + datetime.timedelta(days=3)

        review_stage_note=pc_client.post_note(openreview.Note(
            content={
                'review_name': 'First_Round_Review',
                'review_deadline': due_date.strftime('%Y/%m/%d'),
                'make_reviews_public': 'No, reviews should NOT be revealed publicly when they are posted',
                'release_reviews_to_authors': 'No, reviews should NOT be revealed when they are posted to the paper\'s authors',
                'release_reviews_to_reviewers': 'Review should not be revealed to any reviewer, except to the author of the review',
                'email_program_chairs_about_reviews': 'No, do not email program chairs about received reviews',
            },
            forum=request_form.forum,
            invitation='openreview.net/Support/-/Request{}/Review_Stage'.format(request_form.number),
            readers=['AAAI.org/2025/Conference/Program_Chairs', 'openreview.net/Support'],
            replyto=request_form.forum,
            referent=request_form.forum,
            signatures=['~Program_AAAIChair1'],
            writers=[]
        ))
        helpers.await_queue()

        helpers.await_queue_edit(openreview_client, 'AAAI.org/2025/Conference/-/First_Round_Review-0-1', count=1)

        invitation = openreview_client.get_invitation('AAAI.org/2025/Conference/Submission1/-/First_Round_Review')

        assert len(openreview_client.get_invitations(invitation='AAAI.org/2025/Conference/-/First_Round_Review')) == 10

        reviewer_client = openreview.api.OpenReviewClient(username='program_committee1@aaai.org', password=helpers.strong_password)

        anon_groups = reviewer_client.get_groups(prefix='AAAI.org/2025/Conference/Submission1/Program_Committee_', signatory='~Program_Committee_AAAIOne1')
        anon_group_id = anon_groups[0].id

        review_edit = reviewer_client.post_note_edit(
            invitation='AAAI.org/2025/Conference/Submission1/-/First_Round_Review',
            signatures=[anon_group_id],
            note=openreview.api.Note(
                content={
                    'title': { 'value': 'Review for Paper 1' },
                    'review': { 'value': 'good paper' },
                    'rating': { 'value': 10 },
                    'confidence': { 'value': 5 }
                }
            )
        )

        helpers.await_queue_edit(openreview_client, edit_id=review_edit['id'])

        messages = openreview_client.get_messages(to='senior_program_committee1@aaai.org', subject='[AAAI 2025] First Round Review posted to your assigned Paper number: 1, Paper title: "Paper title 1"')
        assert messages and len(messages) == 1

        ## Close first review stage
        now = datetime.datetime.utcnow()
        due_date = now - datetime.timedelta(days=1)
        review_stage_note=pc_client.post_note(openreview.Note(
            content={
                'review_name': 'First_Round_Review',
                'review_deadline': due_date.strftime('%Y/%m/%d'),
                'make_reviews_public': 'No, reviews should NOT be revealed publicly when they are posted',
                'release_reviews_to_authors': 'No, reviews should NOT be revealed when they are posted to the paper\'s authors',
                'release_reviews_to_reviewers': 'Review should not be revealed to any reviewer, except to the author of the review',
                'email_program_chairs_about_reviews': 'No, do not email program chairs about received reviews',
            },
            forum=request_form.forum,
            invitation='openreview.net/Support/-/Request{}/Review_Stage'.format(request_form.number),
            readers=['AAAI.org/2025/Conference/Program_Chairs', 'openreview.net/Support'],
            replyto=request_form.forum,
            referent=request_form.forum,
            signatures=['~Program_AAAIChair1'],
            writers=[]
        ))
        helpers.await_queue()

        ## Desk reject papers, assign more reviewers to papers
        desk_reject_note = openreview_client.post_note_edit(invitation='AAAI.org/2025/Conference/Submission10/-/Desk_Rejection',
            signatures=['AAAI.org/2025/Conference/Program_Chairs'],
            note=openreview.api.Note(
                content={
                    'desk_reject_comments': { 'value': 'No PDF' },
                }
            ))
        helpers.await_queue_edit(openreview_client, edit_id=desk_reject_note['id'])

        # Add more reviewers
        submissions = openreview_client.get_notes(content= { 'venueid': 'AAAI.org/2025/Conference/Submission'}, sort='number:asc')
        for sub in submissions:
            assignment_edge = openreview_client.post_edge(openreview.api.Edge(
                invitation = 'AAAI.org/2025/Conference/Program_Committee/-/Assignment',
                head = sub.id,
                tail = '~Program_Committee_AAAIFour1',
                signatures = ['AAAI.org/2025/Conference/Program_Chairs'],
                weight = 1
            ))
            helpers.await_queue_edit(openreview_client, edit_id=assignment_edge.id)

        ## Open second review stage
        now = datetime.datetime.utcnow()
        due_date = now + datetime.timedelta(days=3)
        review_stage_note=pc_client.post_note(openreview.Note(
            content={
                'review_name': 'Second_Round_Review',
                'review_deadline': due_date.strftime('%Y/%m/%d'),
                'make_reviews_public': 'No, reviews should NOT be revealed publicly when they are posted',
                'release_reviews_to_authors': 'No, reviews should NOT be revealed when they are posted to the paper\'s authors',
                'release_reviews_to_reviewers': 'Review should not be revealed to any reviewer, except to the author of the review',
                'email_program_chairs_about_reviews': 'No, do not email program chairs about received reviews',
            },
            forum=request_form.forum,
            invitation='openreview.net/Support/-/Request{}/Review_Stage'.format(request_form.number),
            readers=['AAAI.org/2025/Conference/Program_Chairs', 'openreview.net/Support'],
            replyto=request_form.forum,
            referent=request_form.forum,
            signatures=['~Program_AAAIChair1'],
            writers=[]
        ))
        helpers.await_queue()

        helpers.await_queue_edit(openreview_client, 'AAAI.org/2025/Conference/-/Second_Round_Review-0-1', count=1)

        assert len(openreview_client.get_invitations(invitation='AAAI.org/2025/Conference/-/Second_Round_Review')) == 9
        assert openreview_client.get_invitation('AAAI.org/2025/Conference/Submission1/-/Second_Round_Review')

        reviewer_client = openreview.api.OpenReviewClient(username='program_committee4@aaai.org', password=helpers.strong_password)
        anon_groups = reviewer_client.get_groups(prefix='AAAI.org/2025/Conference/Submission1/Program_Committee_', signatory='~Program_Committee_AAAIFour1')
        anon_group_id = anon_groups[0].id

        review_edit = reviewer_client.post_note_edit(
            invitation='AAAI.org/2025/Conference/Submission1/-/Second_Round_Review',
            signatures=[anon_group_id],
            note=openreview.api.Note(
                content={
                    'title': { 'value': 'Second Review for Paper 1' },
                    'review': { 'value': 'Great paper' },
                    'rating': { 'value': 10 },
                    'confidence': { 'value': 5 }
                }
            )
        )
        helpers.await_queue_edit(openreview_client, edit_id=review_edit['id'])

        messages = openreview_client.get_messages(to='senior_program_committee1@aaai.org', subject='[AAAI 2025] Second Round Review posted to your assigned Paper number: 1, Paper title: "Paper title 1"')
        assert messages and len(messages) == 1
        messages = openreview_client.get_messages(to='program_committee4@aaai.org', subject='[AAAI 2025] Your second round review has been received on your assigned Paper number: 1, Paper title: "Paper title 1"')
        assert messages and len(messages) == 1

        review_note = openreview_client.get_notes(invitation='AAAI.org/2025/Conference/Submission1/-/Second_Round_Review', sort='number:asc')[0]
        assert review_note
        assert review_note.readers == [
            'AAAI.org/2025/Conference/Program_Chairs', 
            'AAAI.org/2025/Conference/Submission1/Area_Chairs', 
            'AAAI.org/2025/Conference/Submission1/Senior_Program_Committee', 
            anon_group_id ]

    def test_release_reviews(self, client, openreview_client, helpers, selenium, request_page):
        pc_client=openreview.Client(username='pc@aaai.org', password=helpers.strong_password)
        request_form=pc_client.get_notes(invitation='openreview.net/Support/-/Request_Form')[0]

        ## Close and release second review stage
        now = datetime.datetime.utcnow()
        due_date = now - datetime.timedelta(days=1)
        review_stage_note=pc_client.post_note(openreview.Note(
            content={
                'review_name': 'Second_Round_Review',
                'review_deadline': due_date.strftime('%Y/%m/%d'),
                'make_reviews_public': 'No, reviews should NOT be revealed publicly when they are posted',
                'release_reviews_to_authors': 'Yes, reviews should be revealed when they are posted to the paper\'s authors',
                'release_reviews_to_reviewers': 'Review should not be revealed to any reviewer, except to the author of the review',
                'email_program_chairs_about_reviews': 'No, do not email program chairs about received reviews',
            },
            forum=request_form.forum,
            invitation='openreview.net/Support/-/Request{}/Review_Stage'.format(request_form.number),
            readers=['AAAI.org/2025/Conference/Program_Chairs', 'openreview.net/Support'],
            replyto=request_form.forum,
            referent=request_form.forum,
            signatures=['~Program_AAAIChair1'],
            writers=[]
        ))
        helpers.await_queue()

        helpers.await_queue_edit(openreview_client, edit_id='AAAI.org/2025/Conference/-/Second_Round_Review-0-1', count=2)

        review_note = openreview_client.get_notes(invitation='AAAI.org/2025/Conference/Submission1/-/Second_Round_Review', sort='number:asc')[0]
        assert 'AAAI.org/2025/Conference/Submission1/Authors' in review_note.readers

    def test_meta_review_stage(self, client, openreview_client, helpers, selenium, request_page):
        pc_client=openreview.Client(username='pc@aaai.org', password=helpers.strong_password)
        request_form=pc_client.get_notes(invitation='openreview.net/Support/-/Request_Form')[0]

        now = datetime.datetime.utcnow()
        start_date = now - datetime.timedelta(days=2)
        due_date = now + datetime.timedelta(days=3)

        # Open Phase 1 meta review stage
        pc_client.post_note(openreview.Note(
            content= {
                'make_meta_reviews_public': 'No, meta reviews should NOT be revealed publicly when they are posted',
                'meta_review_start_date': start_date.strftime('%Y/%m/%d'),
                'meta_review_deadline': due_date.strftime('%Y/%m/%d'),
                'release_meta_reviews_to_authors': 'No, meta reviews should NOT be revealed when they are posted to the paper\'s authors',
                'release_meta_reviews_to_reviewers': 'Meta review should not be revealed to any reviewer',
                'additional_meta_review_form_options': {
                    "recommendation": {
                        "order": 2,
                        "value": {
                            "param": {
                                "type": "string",
                                "input": "radio",
                                "enum": [
                                    "Reject",
                                    "Proceed to Phase 2"
                                ]
                            }
                        }
                    }
                }
            },
            forum= request_form.id,
            invitation= f'openreview.net/Support/-/Request{request_form.number}/Meta_Review_Stage',
            readers= ['AAAI.org/2025/Conference/Program_Chairs', 'openreview.net/Support'],
            referent= request_form.id,
            replyto= request_form.id,
            signatures= ['~Program_AAAIChair1'],
            writers= [],
        ))
        helpers.await_queue()

        helpers.await_queue_edit(openreview_client, edit_id='AAAI.org/2025/Conference/-/Meta_Review-0-1', count=1)
        helpers.await_queue_edit(openreview_client, edit_id='AAAI.org/2025/Conference/-/Meta_Review_AC_Revision-0-1', count=1)

        invitations = openreview_client.get_invitations(invitation='AAAI.org/2025/Conference/-/Meta_Review')
        assert len(invitations) == 9
        assert invitations[0].edit['note']['id']['param']['withInvitation'] == invitations[0].id

        invitations = openreview_client.get_invitations(invitation='AAAI.org/2025/Conference/-/Meta_Review_AC_Revision')
        assert len(invitations) == 9

        sac_revision_invitation = openreview_client.get_invitation('AAAI.org/2025/Conference/Submission1/-/Meta_Review_AC_Revision')
        invitation = openreview_client.get_invitation('AAAI.org/2025/Conference/Submission1/-/Meta_Review')
        assert sac_revision_invitation.edit['note']['id']['param']['withInvitation'] == invitation.id

        # Post meta review
        ac_client = openreview.api.OpenReviewClient(username = 'senior_program_committee1@aaai.org', password=helpers.strong_password)
        anon_id = ac_client.get_groups(prefix=f'AAAI.org/2025/Conference/Submission1/Senior_Program_Committee_', signatory='senior_program_committee1@aaai.org')[0].id

        meta_review = ac_client.post_note_edit(
            invitation='AAAI.org/2025/Conference/Submission1/-/Meta_Review',
            signatures=[anon_id],
            note=openreview.api.Note(
                content = {
                    'metareview': { 'value': 'This is a meta review' },
                    'recommendation': { 'value': 'Reject' },
                    'confidence': { 'value': 5 },
                }
            )
        )
        helpers.await_queue_edit(openreview_client, edit_id=meta_review['id'])

        # Post meta review SAC revision to change recommendation
        sac_client = openreview.api.OpenReviewClient(username='ac1@aaai.org', password=helpers.strong_password)
        meta_review = sac_client.get_notes(invitation='AAAI.org/2025/Conference/Submission1/-/Meta_Review')[0]
        sac_client.post_note_edit(
            invitation='AAAI.org/2025/Conference/Submission1/-/Meta_Review_AC_Revision',
            signatures=['AAAI.org/2025/Conference/Submission1/Area_Chairs'],
            note=openreview.api.Note(
                id=meta_review.id,
                content = {
                    'metareview': { 'value': 'This is a meta review - AC revision' },
                    'recommendation': { 'value': 'Proceed to Phase 2' },
                    'confidence': { 'value': 5 },
                }
            )
        )

        # Close meta review stage
        now = datetime.datetime.utcnow()
        start_date = now - datetime.timedelta(days=2)
        due_date = now - datetime.timedelta(days=1)

        pc_client.post_note(openreview.Note(
            content= {
                'make_meta_reviews_public': 'No, meta reviews should NOT be revealed publicly when they are posted',
                'meta_review_start_date': start_date.strftime('%Y/%m/%d'),
                'meta_review_deadline': due_date.strftime('%Y/%m/%d'),
                'release_meta_reviews_to_authors': 'No, meta reviews should NOT be revealed when they are posted to the paper\'s authors',
                'release_meta_reviews_to_reviewers': 'Meta review should not be revealed to any reviewer',
                'additional_meta_review_form_options': {
                    "recommendation": {
                        "order": 2,
                        "value": {
                            "param": {
                                "type": "string",
                                "input": "radio",
                                "enum": [
                                    "Reject",
                                    "Proceed to Phase 2"
                                ]
                            }
                        }
                    }
                }
            },
            forum= request_form.id,
            invitation= f'openreview.net/Support/-/Request{request_form.number}/Meta_Review_Stage',
            readers= ['AAAI.org/2025/Conference/Program_Chairs', 'openreview.net/Support'],
            referent= request_form.id,
            replyto= request_form.id,
            signatures= ['~Program_AAAIChair1'],
            writers= [],
        ))
        helpers.await_queue()
    
    def test_comment_emails(self, client, openreview_client, helpers, request_page, selenium):
        pc_client=openreview.Client(username='pc@aaai.org', password=helpers.strong_password)
        request_form=pc_client.get_notes(invitation='openreview.net/Support/-/Request_Form')[0]

        now = datetime.datetime.utcnow()
        start_date = now - datetime.timedelta(days=2)
        due_date = now + datetime.timedelta(days=3)

        # Start comment stage
        comment_stage_note = pc_client.post_note(openreview.Note(
            content={
                'commentary_start_date': start_date.strftime('%Y/%m/%d'),
                'commentary_end_date': due_date.strftime('%Y/%m/%d'),
                'participants': ['Program Chairs', 'Assigned Senior Area Chairs', 'Assigned Area Chairs', 'Assigned Reviewers'],
                'email_program_chairs_about_official_comments': 'Yes, email PCs for each official comment made in the venue'
            },
            forum=request_form.forum,
            invitation=f'openreview.net/Support/-/Request{request_form.number}/Comment_Stage',
            readers=['AAAI.org/2025/Conference/Program_Chairs', 'openreview.net/Support'],
            replyto=request_form.forum,
            referent=request_form.forum,
            signatures=['~Program_AAAIChair1'],
            writers=[]
        ))
        helpers.await_queue()

        helpers.await_queue_edit(openreview_client, 'AAAI.org/2025/Conference/-/Official_Comment-0-1', count=1)

        assert comment_stage_note

        # Post comment as reviewer
        rev_client_v2=openreview.api.OpenReviewClient(username='program_committee1@aaai.org', password=helpers.strong_password)
        anon_groups = rev_client_v2.get_groups(prefix='AAAI.org/2025/Conference/Submission1/Program_Committee_', signatory='~Program_Committee_AAAIOne1')
        anon_group_id = anon_groups[0].id
        submissions = openreview_client.get_notes(invitation='AAAI.org/2025/Conference/-/Submission', sort='number:asc')

        official_comment_note = rev_client_v2.post_note_edit(
            invitation='AAAI.org/2025/Conference/Submission1/-/Official_Comment',
            signatures=[anon_group_id],
            note=openreview.api.Note(
                replyto=submissions[0].id,
                content={
                    'title': {'value': 'Title'},
                    'comment': {'value': 'Program Committee comment to Senior Program Committee'}
                },
                readers=[
                    'AAAI.org/2025/Conference/Program_Chairs',
                    'AAAI.org/2025/Conference/Submission1/Area_Chairs',
                    'AAAI.org/2025/Conference/Submission1/Senior_Program_Committee',
                    anon_group_id
                ]
            )
        )

        helpers.await_queue_edit(openreview_client, edit_id=official_comment_note['id'])

        messages = openreview_client.get_messages(to='program_committee1@aaai.org', subject='[AAAI 2025] Your comment was received on Paper Number: 1, Paper Title: "Paper title 1"')
        assert messages and len(messages) == 1

        messages = openreview_client.get_messages(to='pc@aaai.org', subject='[AAAI 2025] Program Committee.*')
        assert messages and len(messages) == 1

        messages = openreview_client.get_messages(to='senior_program_committee1@aaai.org', subject='[AAAI 2025] Program Committee.*')
        assert messages and len(messages) == 1

    def test_rebuttal_stage(self, client, openreview_client, helpers, selenium, request_page):
        pc_client=openreview.Client(username='pc@aaai.org', password=helpers.strong_password)
        pc_client_v2=openreview.api.OpenReviewClient(username='pc@aaai.org', password=helpers.strong_password)
        request_form=pc_client.get_notes(invitation='openreview.net/Support/-/Request_Form')[0]

        now = datetime.datetime.utcnow()
        start_date = now - datetime.timedelta(days=2)
        due_date = now + datetime.timedelta(days=3)

        # Post rebuttal stage note to enbale one rebuttal per paper
        pc_client.post_note(openreview.Note(
            content={
                'rebuttal_start_date': start_date.strftime('%Y/%m/%d'),
                'rebuttal_deadline': due_date.strftime('%Y/%m/%d'),
                'number_of_rebuttals': 'One author rebuttal per paper',
                'rebuttal_readers': ['Assigned Senior Area Chairs', 'Assigned Area Chairs'],
                'email_program_chairs_about_rebuttals': 'No, do not email program chairs about received rebuttals'
            },
            forum=request_form.forum,
            invitation=f'openreview.net/Support/-/Request{request_form.number}/Rebuttal_Stage',
            readers=['AAAI.org/2025/Conference/Program_Chairs', 'openreview.net/Support'],
            replyto=request_form.forum,
            referent=request_form.forum,
            signatures=['~Program_AAAIChair1'],
            writers=[]
        ))
        helpers.await_queue()

        helpers.await_queue_edit(openreview_client, 'AAAI.org/2025/Conference/-/Rebuttal-0-1', count=1)

        assert len(openreview_client.get_invitations(invitation='AAAI.org/2025/Conference/-/Rebuttal')) == 9

        submissions = openreview_client.get_notes(invitation='AAAI.org/2025/Conference/-/Submission', sort='number:asc')
        author_client = openreview.api.OpenReviewClient(username='peter@mail.com', password=helpers.strong_password)

        rebuttal_edit = author_client.post_note_edit(
            invitation = 'AAAI.org/2025/Conference/Submission1/-/Rebuttal',
            signatures = ['AAAI.org/2025/Conference/Submission1/Authors'],
            note = openreview.api.Note(
                replyto = submissions[0].id,
                content = {
                    'rebuttal': { 'value': 'This is a rebuttal.' }
                }
            )
        )
        helpers.await_queue_edit(openreview_client, edit_id=rebuttal_edit['id'])

        messages = openreview_client.get_messages(subject = '[AAAI 2025] Your author rebuttal was posted on Submission Number: 1, Submission Title: "Paper title 1"')
        assert len(messages) == 1
        assert 'peter@mail.com' in messages[0]['content']['to']
        assert messages[0]['content']['replyTo'] == 'pc@aaai.org'

        messages = openreview_client.get_messages(subject = '[AAAI 2025] An author rebuttal was posted on Submission Number: 1, Submission Title: "Paper title 1"')
        assert len(messages) == 3
        recipients = [m['content']['to'] for m in messages]
        assert 'test@mail.com' in recipients
        assert 'andrew@amazon.com' in recipients
        assert 'senior_program_committee1@aaai.org' in recipients

    def test_release_rebuttals(self, client, openreview_client, helpers, selenium, request_page):
        pc_client=openreview.Client(username='pc@aaai.org', password=helpers.strong_password)
        pc_client_v2=openreview.api.OpenReviewClient(username='pc@aaai.org', password=helpers.strong_password)
        request_form=pc_client.get_notes(invitation='openreview.net/Support/-/Request_Form')[0]

        now = datetime.datetime.utcnow()
        start_date = now - datetime.timedelta(days=2)
        due_date = now - datetime.timedelta(days=1)

        # Close and release rebuttals
        pc_client.post_note(openreview.Note(
            content={
                'rebuttal_start_date': start_date.strftime('%Y/%m/%d'),
                'rebuttal_deadline': due_date.strftime('%Y/%m/%d'),
                'number_of_rebuttals': 'One author rebuttal per paper',
                'rebuttal_readers': ['Assigned Senior Area Chairs', 'Assigned Area Chairs', 'Assigned Reviewers who already submitted their review'],
                'email_program_chairs_about_rebuttals': 'No, do not email program chairs about received rebuttals'
            },
            forum=request_form.forum,
            invitation=f'openreview.net/Support/-/Request{request_form.number}/Rebuttal_Stage',
            readers=['AAAI.org/2025/Conference/Program_Chairs', 'openreview.net/Support'],
            replyto=request_form.forum,
            referent=request_form.forum,
            signatures=['~Program_AAAIChair1'],
            writers=[]
        ))
        helpers.await_queue()

        helpers.await_queue_edit(openreview_client, 'AAAI.org/2025/Conference/-/Rebuttal-0-1', count=2)

        rebuttals = pc_client_v2.get_notes(invitation='AAAI.org/2025/Conference/Submission1/-/Rebuttal')
        assert len(rebuttals) == 1
        assert rebuttals[0].readers == [
            'AAAI.org/2025/Conference/Program_Chairs',
            'AAAI.org/2025/Conference/Submission1/Area_Chairs',
            'AAAI.org/2025/Conference/Submission1/Senior_Program_Committee',
            'AAAI.org/2025/Conference/Submission1/Program_Committee/Submitted',
            'AAAI.org/2025/Conference/Submission1/Authors',
        ]
