import openreview
import pytest
import datetime
import re
import random
import os
import csv
from selenium.webdriver.common.by import By

class TestICMLConference():


    def test_create_conference(self, client, openreview_client, helpers):

        now = datetime.datetime.utcnow()
        due_date = now + datetime.timedelta(days=3)

        # Post the request form note
        pc_client=helpers.create_user('pc@icml.cc', 'Program', 'ICMLChair')

        helpers.create_user('sac1@icml.cc', 'SAC', 'ICMLOne')
        helpers.create_user('ac1@icml.cc', 'AC', 'ICMLOne')
        helpers.create_user('ac2@icml.cc', 'AC', 'ICMLTwo')
        helpers.create_user('reviewer1@icml.cc', 'Reviewer', 'ICMLOne')
        helpers.create_user('reviewer2@icml.cc', 'Reviewer', 'ICMLTwo')
        helpers.create_user('reviewer3@icml.cc', 'Reviewer', 'ICMLThree')
        helpers.create_user('reviewer4@icml.cc', 'Reviewer', 'ICMLFour')
        helpers.create_user('reviewer5@icml.cc', 'Reviewer', 'ICMLFive')
        helpers.create_user('reviewer6@icml.cc', 'Reviewer', 'ICMLSix')

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
                        'value': {
                            'param': {
                                'type': 'file',
                                'extensions': ['zip', 'pdf'],
                                'maxSize': 100,
                                "optional": True
                            }
                        },
                        "description": "All supplementary material must be self-contained and zipped into a single file. Note that supplementary material will be visible to reviewers and the public throughout and after the review period, and ensure all material is anonymized. The maximum file size is 100MB.",
                        "order": 7,
                        'readers': [ 
                            'ICML.cc/2023/Conference', 
                            'ICML.cc/2023/Conference/Submission${4/number}/Senior_Area_Chairs', 
                            'ICML.cc/2023/Conference/Submission${4/number}/Area_Chairs', 
                            'ICML.cc/2023/Conference/Submission${4/number}/Authors'
                        ]
                    },
                    "student_paper": {
                        'value': {
                            'param': {
                                'type': 'string',
                                'enum': ['Yes', 'No'],
                                'input': 'radio'
                            }
                        },
                        "description": "Indicate if the submission is from a student.",
                        "order": 7,
                        'readers': [ 
                            'ICML.cc/2023/Conference', 
                            'ICML.cc/2023/Conference/Submission${4/number}/Authors'
                        ]
                    }

                }
  
            }
        ))
        helpers.await_queue()

        submission_invitation = openreview_client.get_invitation('ICML.cc/2023/Conference/-/Submission')
        assert submission_invitation
        assert 'supplementary_material' in submission_invitation.edit['note']['content']
        assert 'student_paper' in submission_invitation.edit['note']['content']



    def test_sac_recruitment(self, client, openreview_client, helpers, request_page, selenium):

        pc_client=openreview.Client(username='pc@icml.cc', password='1234')
        request_form=pc_client.get_notes(invitation='openreview.net/Support/-/Request_Form')[0]

        reviewer_details = '''sac1@icml.cc, SAC ICMLOne\nsac2@icml.cc, SAC ICMLTwo'''
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
reviewer4@icml.cc, Reviewer ICMLFour
reviewer5@icml.cc, Reviewer ICMLFive
reviewer6@icml.cc, Reviewer ICMLSix
'''
        pc_client.post_note(openreview.Note(
            content={
                'title': 'Recruitment',
                'invitee_role': 'Reviewers',
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

        assert len(openreview_client.get_group('ICML.cc/2023/Conference/Reviewers').members) == 0
        assert len(openreview_client.get_group('ICML.cc/2023/Conference/Reviewers/Invited').members) == 6
        assert len(openreview_client.get_group('ICML.cc/2023/Conference/Reviewers/Declined').members) == 0

        messages = openreview_client.get_messages(subject = '[ICML 2023] Invitation to serve as Reviewer')
        assert len(messages) == 6

        for message in messages:
            text = message['content']['text']
            
            invitation_url = re.search('https://.*\n', text).group(0).replace('https://openreview.net', 'http://localhost:3030').replace('&amp;', '&')[:-1]
            helpers.respond_invitation(selenium, request_page, invitation_url, accept=True)

        helpers.await_queue()

        messages = client.get_messages(subject='[ICML 2023] Reviewer Invitation accepted')
        assert len(messages) == 6

        assert len(openreview_client.get_group('ICML.cc/2023/Conference/Reviewers').members) == 6
        assert len(openreview_client.get_group('ICML.cc/2023/Conference/Reviewers/Invited').members) == 6
        assert len(openreview_client.get_group('ICML.cc/2023/Conference/Reviewers/Declined').members) == 0

        messages = openreview_client.get_messages(to = 'reviewer6@icml.cc', subject = '[ICML 2023] Invitation to serve as Reviewer')
        invitation_url = re.search('https://.*\n', messages[0]['content']['text']).group(0).replace('https://openreview.net', 'http://localhost:3030').replace('&amp;', '&')[:-1]
        helpers.respond_invitation(selenium, request_page, invitation_url, accept=False)

        helpers.await_queue()

        assert len(openreview_client.get_group('ICML.cc/2023/Conference/Reviewers').members) == 5
        assert len(openreview_client.get_group('ICML.cc/2023/Conference/Reviewers/Invited').members) == 6
        assert len(openreview_client.get_group('ICML.cc/2023/Conference/Reviewers/Declined').members) == 1

    def test_submissions(self, client, openreview_client, helpers, test_client):

        test_client = openreview.api.OpenReviewClient(token=test_client.token)

        domains = ['umass.edu', 'amazon.com', 'fb.com', 'cs.umass.edu', 'google.com', 'mit.edu']
        for i in range(1,6):
            note = openreview.api.Note(
                content = {
                    'title': { 'value': 'Paper title ' + str(i) },
                    'abstract': { 'value': 'This is an abstract ' + str(i) },
                    'authorids': { 'value': ['~SomeFirstName_User1', 'peter@mail.com', 'andrew@' + domains[i]] },
                    'authors': { 'value': ['SomeFirstName User', 'Peter SomeLastName', 'Andrew Mc'] },
                    'keywords': { 'value': ['machine learning', 'nlp'] },
                    'pdf': {'value': '/pdf/' + 'p' * 40 +'.pdf' },
                    'supplementary_material': { 'value': '/attachment/' + 's' * 40 +'.zip'},
                    'student_paper': { 'value': 'Yes' }
                }
            )
            if i == 1:
                note.content['authors']['value'].append('SAC ICMLOne')
                note.content['authorids']['value'].append('~SAC_ICMLOne1')
            
            test_client.post_note_edit(invitation='ICML.cc/2023/Conference/-/Submission',
                signatures=['~SomeFirstName_User1'],
                note=note)

        helpers.await_queue()

        submissions = openreview_client.get_notes(invitation='ICML.cc/2023/Conference/-/Submission', sort='number:asc')
        assert len(submissions) == 5
        assert ['ICML.cc/2023/Conference', 'ICML.cc/2023/Conference/Submission1/Authors'] == submissions[0].readers    


    def test_ac_bidding(self, client, openreview_client, helpers, test_client):

        pc_client=openreview.Client(username='pc@icml.cc', password='1234')
        request_form=pc_client.get_notes(invitation='openreview.net/Support/-/Request_Form')[0]

        ## make submissions visible to the committee
        pc_client.post_note(openreview.Note(
            content= {
                'force': 'Yes',
                'submission_readers': 'All program committee (all reviewers, all area chairs, all senior area chairs if applicable)'
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

        submissions = openreview_client.get_notes(invitation='ICML.cc/2023/Conference/-/Submission', sort='number:asc')
        assert len(submissions) == 5
        assert ['ICML.cc/2023/Conference', 
        'ICML.cc/2023/Conference/Senior_Area_Chairs',
        'ICML.cc/2023/Conference/Area_Chairs',
        'ICML.cc/2023/Conference/Reviewers',
        'ICML.cc/2023/Conference/Submission1/Authors'] == submissions[0].readers

        with open(os.path.join(os.path.dirname(__file__), 'data/rev_scores_venue.csv'), 'w') as file_handle:
            writer = csv.writer(file_handle)
            for submission in submissions:
                for ac in client.get_group('ICML.cc/2023/Conference/Area_Chairs').members:
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

        assert openreview_client.get_edges(invitation='ICML.cc/2023/Conference/Area_Chairs/-/Affinity_Score')
        assert openreview_client.get_edges(invitation='ICML.cc/2023/Conference/Area_Chairs/-/Conflict')

        client.post_note(openreview.Note(
            content={
                'title': 'Paper Matching Setup',
                'matching_group': 'ICML.cc/2023/Conference/Reviewers',
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
        
        assert openreview_client.get_invitation('ICML.cc/2023/Conference/Reviewers/-/Conflict')               
        
        now = datetime.datetime.utcnow()
        due_date = now + datetime.timedelta(days=3)

        bid_stage_note = pc_client.post_note(openreview.Note(
            content={
                'bid_start_date': now.strftime('%Y/%m/%d'),
                'bid_due_date': due_date.strftime('%Y/%m/%d')
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