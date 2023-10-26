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

class TestVenueWithTracks():


    @pytest.fixture(scope="class")
    def profile_management(self, client):
        profile_management = ProfileManagement(client, 'openreview.net')
        profile_management.setup()
        return profile_management


    def test_create_conference(self, client, openreview_client, helpers, profile_management):

        now = datetime.datetime.utcnow()
        due_date = now + datetime.timedelta(days=3)

        # Post the request form note
        helpers.create_user('pc@webconf.org', 'Program', 'WebChair')
        pc_client = openreview.Client(username='pc@webconf.org', password=helpers.strong_password)
        helpers.create_user('sac1@webconf.com', 'SAC', 'WebChairOne')
        helpers.create_user('sac2@webconf.com', 'SAC', 'WebChairTwo')
        helpers.create_user('sac3@webconf.com', 'SAC', 'WebChairThree')
        helpers.create_user('sac4@webconf.com', 'SAC', 'WebChairFour')
        helpers.create_user('sac5@webconf.com', 'SAC', 'WebChairFive')
        helpers.create_user('sac6@webconf.com', 'SAC', 'WebChairSix')
        helpers.create_user('sac7@webconf.com', 'SAC', 'WebChairSeven')
        helpers.create_user('sac8@webconf.com', 'SAC', 'WebChairEight')
        helpers.create_user('sac9@webconf.com', 'SAC', 'WebChairNine')
        helpers.create_user('sac10@webconf.com', 'SAC', 'WebChairTen')
        helpers.create_user('sac11@gmail.com', 'SAC', 'WebChairEleven')
        helpers.create_user('sac12@webconf.com', 'SAC', 'WebChairTwelve')

        helpers.create_user('ac1@webconf.com', 'AC', 'WebChairOne')
        helpers.create_user('ac2@webconf.com', 'AC', 'WebChairTwo')
        helpers.create_user('ac3@webconf.com', 'AC', 'WebChairThree')
        helpers.create_user('ac4@webconf.com', 'AC', 'WebChairFour')
        helpers.create_user('ac5@webconf.com', 'AC', 'WebChairFive')
        helpers.create_user('ac6@webconf.com', 'AC', 'WebChairSix')
        helpers.create_user('ac7@webconf.com', 'AC', 'WebChairSeven')
        helpers.create_user('ac8@webconf.com', 'AC', 'WebChairEight')
        helpers.create_user('ac9@webconf.com', 'AC', 'WebChairNine')
        helpers.create_user('ac10@webconf.com', 'AC', 'WebChairTen')
        helpers.create_user('ac11@webconf.com', 'AC', 'WebChairEleven')
        helpers.create_user('ac12@webconf.com', 'AC', 'WebChairTwelve')        
        helpers.create_user('ac13@webconf.com', 'AC', 'WebChairThirdTeen')        
        helpers.create_user('ac14@webconf.com', 'AC', 'WebChairFourTeen')        
        helpers.create_user('ac15@webconf.com', 'AC', 'WebChairFifthTeen')        
        helpers.create_user('ac16@webconf.com', 'AC', 'WebChairSixTeen')        
        helpers.create_user('ac17@webconf.com', 'AC', 'WebChairSevenTeen')        
        helpers.create_user('ac18@webconf.com', 'AC', 'WebChairEightTeen')        
        helpers.create_user('ac19@webconf.com', 'AC', 'WebChairNineTeen')        
        helpers.create_user('ac20@webconf.com', 'AC', 'WebChairTwenty')        
        helpers.create_user('ac21@gmail.com', 'AC', 'WebChairTwentyOne')        
        helpers.create_user('ac22@gmail.com', 'AC', 'WebChairTwentyTwo')

        helpers.create_user('reviewer1@webconf.com', 'Reviewer', 'WebChairOne')
        helpers.create_user('reviewer2@webconf.com', 'Reviewer', 'WebChairTwo')
        helpers.create_user('reviewer3@webconf.com', 'Reviewer', 'WebChairThree')
        helpers.create_user('reviewer4@webconf.com', 'Reviewer', 'WebChairFour')
        helpers.create_user('reviewer5@webconf.com', 'Reviewer', 'WebChairFive')
        helpers.create_user('reviewer6@webconf.com', 'Reviewer', 'WebChairSix')
        helpers.create_user('reviewer7@webconf.com', 'Reviewer', 'WebChairSeven')
        helpers.create_user('reviewer8@webconf.com', 'Reviewer', 'WebChairEight')
        helpers.create_user('reviewer9@webconf.com', 'Reviewer', 'WebChairNine')
        helpers.create_user('reviewer10@webconf.com', 'Reviewer', 'WebChairTen')
        helpers.create_user('reviewer11@webconf.com', 'Reviewer', 'WebChairEleven')
        helpers.create_user('reviewer12@webconf.com', 'Reviewer', 'WebChairTwelve')        
        helpers.create_user('reviewer13@webconf.com', 'Reviewer', 'WebChairThirdTeen')        
        helpers.create_user('reviewer14@webconf.com', 'Reviewer', 'WebChairFourTeen')        
        helpers.create_user('reviewer15@webconf.com', 'Reviewer', 'WebChairFifthTeen')        
        helpers.create_user('reviewer16@webconf.com', 'Reviewer', 'WebChairSixTeen')        
        helpers.create_user('reviewer17@webconf.com', 'Reviewer', 'WebChairSevenTeen')        
        helpers.create_user('reviewer18@webconf.com', 'Reviewer', 'WebChairEightTeen')        
        helpers.create_user('reviewer19@webconf.com', 'Reviewer', 'WebChairNineTeen')        
        helpers.create_user('reviewer20@webconf.com', 'Reviewer', 'WebChairTwenty')        
        helpers.create_user('reviewer21@gmail.com', 'Reviewer', 'WebChairTwentyOne')        
        helpers.create_user('reviewer22@gmail.com', 'Reviewer', 'WebChairTwentyTwo')                

        request_form_note = pc_client.post_note(openreview.Note(
            invitation='openreview.net/Support/-/Request_Form',
            signatures=['~Program_WebChair1'],
            readers=[
                'openreview.net/Support',
                '~Program_WebChair1'
            ],
            writers=[],
            content={
                'title': 'The Web Conference 2024',
                'Official Venue Name': 'The Web Conference 2024',
                'Abbreviated Venue Name': 'TheWebConf24',
                'Official Website URL': 'https://www2024.thewebconf.org/',
                'program_chair_emails': ['pc@webconf.org'],
                'contact_email': 'pc@webconf.org',
                'Area Chairs (Metareviewers)': 'Yes, our venue has Area Chairs',
                'senior_area_chair_roles': [
                    "Senior_Area_Chairs",
                    "Econ_Senior_Area_Chairs",
                    "Graph_Senior_Area_Chairs",
                    "RespWeb_Senior_Area_Chairs",
                    "Search_Senior_Area_Chairs",
                    "Security_Senior_Area_Chairs",
                    "Semantics_Senior_Area_Chairs",
                    "Social_Senior_Area_Chairs",
                    "Systems_Senior_Area_Chairs",
                    "RecSys_Senior_Area_Chairs",
                    "Mining_Senior_Area_Chairs",
                    "COI_Senior_Area_Chairs"                    
                ],
                'area_chair_roles': [
                    "Area_Chairs",
                    "Econ_Area_Chairs",
                    "Graph_Area_Chairs",
                    "RespWeb_Area_Chairs",
                    "Search_Area_Chairs",
                    "Security_Area_Chairs",
                    "Semantics_Area_Chairs",
                    "Social_Area_Chairs",
                    "Systems_Area_Chairs",
                    "RecSys_Area_Chairs",
                    "Mining_Area_Chairs",
                    "COI_Area_Chairs"                    
                ],
                'reviewer_roles': [
                    "Reviewers",
                    "Econ_Reviewers",
                    "Graph_Reviewers",
                    "RespWeb_Reviewers",
                    "Search_Reviewers",
                    "Security_Reviewers",
                    "Semantics_Reviewers",
                    "Social_Reviewers",
                    "Systems_Reviewers",
                    "RecSys_Reviewers",
                    "Mining_Reviewers",
                    "COI_Reviewers"                    
                ],                
                'senior_area_chairs': 'Yes, our venue has Senior Area Chairs',
                'Venue Start Date': '2023/07/01',
                'Submission Deadline': due_date.strftime('%Y/%m/%d'),
                'Location': 'Virtual',
                'submission_reviewer_assignment': 'Automatic',
                'Author and Reviewer Anonymity': 'Double-blind',
                'reviewer_identity': ['Program Chairs', 'Assigned Senior Area Chair', 'Assigned Area Chair', 'Assigned Reviewers'],
                'area_chair_identity': ['Program Chairs', 'Assigned Senior Area Chair', 'Assigned Area Chair', 'Assigned Reviewers'],
                'senior_area_chair_identity': ['Program Chairs', 'Assigned Senior Area Chair', 'Assigned Area Chair', 'Assigned Reviewers'],
                'submission_readers': 'Program chairs and paper authors only',
                'How did you hear about us?': 'ML conferences',
                'Expected Submissions': '2000',
                'use_recruitment_template': 'Yes',
                'api_version': '2'
            }))

        helpers.await_queue()

        # Post a deploy note
        client.post_note(openreview.Note(
            content={'venue_id': 'ACM.org/TheWebConf/2024/Conference'},
            forum=request_form_note.forum,
            invitation='openreview.net/Support/-/Request{}/Deploy'.format(request_form_note.number),
            readers=['openreview.net/Support'],
            referent=request_form_note.forum,
            replyto=request_form_note.forum,
            signatures=['openreview.net/Support'],
            writers=['openreview.net/Support']
        ))

        helpers.await_queue()

        assert openreview_client.get_group('ACM.org/TheWebConf/2024/Conference')
        assert openreview_client.get_group('ACM.org/TheWebConf/2024/Conference/Senior_Area_Chairs')
        assert openreview_client.get_group('ACM.org/TheWebConf/2024/Conference/Area_Chairs')
        group = openreview.tools.get_group(openreview_client, 'ACM.org/TheWebConf/2024/Conference/Econ_Reviewers')
        assert group
        assert group.readers == ["ACM.org/TheWebConf/2024/Conference", "ACM.org/TheWebConf/2024/Conference/Econ_Senior_Area_Chairs", "ACM.org/TheWebConf/2024/Conference/Econ_Area_Chairs", "ACM.org/TheWebConf/2024/Conference/Econ_Reviewers"]

        group = openreview.tools.get_group(openreview_client, 'ACM.org/TheWebConf/2024/Conference/Econ_Area_Chairs')
        assert group
        assert group.readers == ["ACM.org/TheWebConf/2024/Conference", "ACM.org/TheWebConf/2024/Conference/Econ_Senior_Area_Chairs", "ACM.org/TheWebConf/2024/Conference/Econ_Area_Chairs"]
        assert openreview.tools.get_group(openreview_client, 'ACM.org/TheWebConf/2024/Conference/Graph_Area_Chairs')
        assert openreview.tools.get_group(openreview_client, 'ACM.org/TheWebConf/2024/Conference/RespWeb_Area_Chairs')
        assert openreview.tools.get_group(openreview_client, 'ACM.org/TheWebConf/2024/Conference/Search_Area_Chairs')
        assert openreview.tools.get_group(openreview_client, 'ACM.org/TheWebConf/2024/Conference/Security_Area_Chairs')
        assert openreview.tools.get_group(openreview_client, 'ACM.org/TheWebConf/2024/Conference/Semantics_Area_Chairs')
        assert openreview.tools.get_group(openreview_client, 'ACM.org/TheWebConf/2024/Conference/Social_Area_Chairs')
        assert openreview.tools.get_group(openreview_client, 'ACM.org/TheWebConf/2024/Conference/Systems_Area_Chairs')
        assert openreview.tools.get_group(openreview_client, 'ACM.org/TheWebConf/2024/Conference/RecSys_Area_Chairs')
        assert openreview.tools.get_group(openreview_client, 'ACM.org/TheWebConf/2024/Conference/Mining_Area_Chairs')
        assert openreview.tools.get_group(openreview_client, 'ACM.org/TheWebConf/2024/Conference/COI_Area_Chairs')
        
        assert openreview_client.get_group('ACM.org/TheWebConf/2024/Conference/Reviewers')
        assert openreview_client.get_group('ACM.org/TheWebConf/2024/Conference/Authors')

        invitation = client.get_invitation(f'openreview.net/Support/-/Request{request_form_note.number}/Recruitment')
        assert 'Econ_Area_Chairs' in invitation.reply['content']['invitee_role']['value-dropdown']

        invitation = client.get_invitation(f'openreview.net/Support/-/Request{request_form_note.number}/Paper_Matching_Setup')
        assert 'ACM.org/TheWebConf/2024/Conference/COI_Senior_Area_Chairs' in invitation.reply['content']['matching_group']['value-dropdown']

        submission_invitation = openreview_client.get_invitation('ACM.org/TheWebConf/2024/Conference/-/Submission')
        assert submission_invitation
        assert submission_invitation.duedate

        pc_client.post_note(openreview.Note(
            invitation=f'openreview.net/Support/-/Request{request_form_note.number}/Revision',
            forum=request_form_note.id,
            readers=['ACM.org/TheWebConf/2024/Conference/Program_Chairs', 'openreview.net/Support'],
            referent=request_form_note.id,
            replyto=request_form_note.id,
            signatures=['~Program_WebChair1'],
            writers=[],
            content={
                'title': 'The Web Conference 2024',
                'Official Venue Name': 'The Web Conference 2024',
                'Abbreviated Venue Name': 'TheWebConf24',
                'Official Website URL': 'https://www2024.thewebconf.org/',
                'program_chair_emails': ['pc@webconf.org'],
                'contact_email': 'pc@webconf.org',
                'Venue Start Date': '2023/07/01',
                'Submission Deadline': due_date.strftime('%Y/%m/%d'),
                'Location': 'Virtual',
                'submission_reviewer_assignment': 'Automatic',
                'How did you hear about us?': 'ML conferences',
                'Expected Submissions': '2000',
                'use_recruitment_template': 'Yes',
                'Additional Submission Options': {
                    "track": {
                        "value": {
                            "param": {
                                "type": "string",
                                "enum": [
                                    "Economics, Online Markets, and Human Computation",
                                    "Graph Algorithms and Learning for the Web",
                                    "Responsible Web",
                                    "Search",
                                    "Security",
                                    "Semantics and Knowledge",
                                    "Social Networks, Social Media, and Society",
                                    "Systems and Infrastructure for Web, Mobile, and WoT",
                                    "User Modeling and Recommendation",
                                    "Web Mining and Content Analysis",
                                    "COI"
                                ],
                                "input": 'select'
                            }
                        },
                        "description": "Submission track",
                        "order": 8
                    }
                },
            }
        ))
        helpers.await_queue()

        submission_invitation = openreview_client.get_invitation('ACM.org/TheWebConf/2024/Conference/-/Submission')
        assert submission_invitation
        assert 'track' in submission_invitation.edit['note']['content']

        invitation = client.get_invitation(f'openreview.net/Support/-/Request{request_form_note.number}/Paper_Matching_Setup')
        assert 'ACM.org/TheWebConf/2024/Conference/COI_Senior_Area_Chairs' in invitation.reply['content']['matching_group']['value-dropdown']

        openreview_client.post_group_edit(
            invitation='ACM.org/TheWebConf/2024/Conference/-/Edit',
            signatures=['ACM.org/TheWebConf/2024/Conference'],
            group=openreview.api.Group(
                id='ACM.org/TheWebConf/2024/Conference',
                content={
                    'allow_gurobi_solver': { 'value': True }
                }
            )
        )

    def test_recruit_sacs(self, client, openreview_client, helpers, selenium, request_page):

        pc_client=openreview.Client(username='pc@webconf.org', password=helpers.strong_password)
        request_form=pc_client.get_notes(invitation='openreview.net/Support/-/Request_Form')[0]

        sac_roles = [
            "Econ_Senior_Area_Chairs",
            "Graph_Senior_Area_Chairs",
            "RespWeb_Senior_Area_Chairs",
            "Search_Senior_Area_Chairs",
            "Security_Senior_Area_Chairs",
            "Semantics_Senior_Area_Chairs",
            "Social_Senior_Area_Chairs",
            "Systems_Senior_Area_Chairs",
            "RecSys_Senior_Area_Chairs",
            "Mining_Senior_Area_Chairs",
            "COI_Senior_Area_Chairs"                    
        ]

        sacs = [
            'sac1@webconf.com',
            'sac2@webconf.com',
            'sac3@webconf.com',
            'sac4@webconf.com',
            'sac5@webconf.com',
            'sac6@webconf.com',
            'sac7@webconf.com',
            'sac8@webconf.com',
            'sac9@webconf.com',
            'sac10@webconf.com',
            'sac11@gmail.com',
            'sac12@webconf.com'
        ]

        sac_counter = 1

        for sac_role in sac_roles:

            reviewer_details = f'''sac{sac_counter}@{'gmail' if sac_counter == 11 else 'webconf'}.com, Area ChairOne'''
            if sac_counter == 1:
                reviewer_details += f'''\nsac12@webconf.com, Area ChairOne'''
            
            pc_client.post_note(openreview.Note(
                content={
                    'title': 'Recruitment',
                    'invitee_role': sac_role,
                    'invitee_details': reviewer_details,
                    'invitee_reduced_load': ["1", "2", "3"],
                    'invitation_email_subject': '[TheWebConf 2023] Invitation to serve as {{invitee_role}}',
                    'invitation_email_content': 'Dear {{fullname}},\n\nYou have been nominated by the program chair committee of Theoretical Foundations of RL Workshop @ ICML 2020 to serve as {{invitee_role}}.\n\n{{invitation_url}}\n\nCheers!\n\nProgram Chairs'
                },
                forum=request_form.forum,
                replyto=request_form.forum,
                invitation='openreview.net/Support/-/Request{}/Recruitment'.format(request_form.number),
                readers=['ACM.org/TheWebConf/2024/Conference/Program_Chairs', 'openreview.net/Support'],
                signatures=['~Program_WebChair1'],
                writers=[]
            ))

            helpers.await_queue()

            role = sac_role.replace('_', ' ')
            role = role[:-1] if role.endswith('s') else role        
            messages = openreview_client.get_messages(subject = f'[TheWebConf 2023] Invitation to serve as {role}')
            if sac_counter == 1:
                assert len(messages) == 2
            else:
                assert len(messages) == 1

            for message in messages:
                text = message['content']['text']

                invitation_url = re.search('https://.*\n', text).group(0).replace('https://openreview.net', 'http://localhost:3030').replace('&amp;', '&')[:-1]
                helpers.respond_invitation(selenium, request_page, invitation_url, accept=True)

            if sac_counter == 1:
                assert len(openreview_client.get_group(f'ACM.org/TheWebConf/2024/Conference/{sac_role}').members) == 2
            else:
                assert len(openreview_client.get_group(f'ACM.org/TheWebConf/2024/Conference/{sac_role}').members) == 1
            sac_counter += 1


    def test_submissions(self, client, openreview_client, helpers, test_client):

        test_client = openreview.api.OpenReviewClient(token=test_client.token)

        domains = ['umass.edu', 'amazon.com', 'fb.com', 'cs.umass.edu', 'google.com', 'mit.edu', 'deepmind.com', 'co.ux', 'apple.com', 'nvidia.com']
        tracks = [
            "Economics, Online Markets, and Human Computation",
            "Graph Algorithms and Learning for the Web",
            "Responsible Web",
            "Search",
            "Security",
            "Semantics and Knowledge",
            "Social Networks, Social Media, and Society",
            "Systems and Infrastructure for Web, Mobile, and WoT",
            "User Modeling and Recommendation",
            "Web Mining and Content Analysis",
            "COI"            
        ]
        for i in range(1,102):
            note = openreview.api.Note(
                content = {
                    'title': { 'value': 'Paper title ' + str(i) },
                    'abstract': { 'value': 'This is an abstract ' + str(i) },
                    'authorids': { 'value': ['~SomeFirstName_User1', 'peter@mail.com', 'andrew@' + domains[i % 10]] },
                    'authors': { 'value': ['SomeFirstName User', 'Peter SomeLastName', 'Andrew Mc'] },
                    'keywords': { 'value': ['machine learning', 'nlp'] },
                    'pdf': {'value': '/pdf/' + 'p' * 40 +'.pdf' },
                    'track': { 'value': tracks[i % 10] }
                }
            )
            if i == 1 or i == 101:
                note.content['authors']['value'].append('SAC WebChairOne')
                note.content['authorids']['value'].append('~SAC_WebChairOne1')
                note.content['track']['value'] = 'COI'

            test_client.post_note_edit(invitation='ACM.org/TheWebConf/2024/Conference/-/Submission',
                signatures=['~SomeFirstName_User1'],
                note=note)

        helpers.await_queue_edit(openreview_client, invitation='ACM.org/TheWebConf/2024/Conference/-/Submission', count=101)


    def test_post_submission(self, client, openreview_client, helpers):

        pc_client=openreview.Client(username='pc@webconf.org', password=helpers.strong_password)
        request_form=pc_client.get_notes(invitation='openreview.net/Support/-/Request_Form')[0]
        venue = openreview.get_conference(client, request_form.id, support_user='openreview.net/Support')

        ## close the submissions
        now = datetime.datetime.utcnow()
        due_date = now - datetime.timedelta(days=1)
        pc_client.post_note(openreview.Note(
            content={
                'title': 'The Web Conference 2024',
                'Official Venue Name': 'The Web Conference 2024',
                'Abbreviated Venue Name': 'TheWebConf24',
                'Official Website URL': 'https://www2024.thewebconf.org/',
                'program_chair_emails': ['pc@webconf.org'],
                'contact_email': 'pc@webconf.org',
                'Venue Start Date': '2023/07/01',
                'Submission Deadline': due_date.strftime('%Y/%m/%d'),
                'Location': 'Virtual',
                'submission_reviewer_assignment': 'Automatic',
                'How did you hear about us?': 'ML conferences',
                'Expected Submissions': '2000',
                'use_recruitment_template': 'Yes',
                'Additional Submission Options': {
                    "track": {
                        "value": {
                            "param": {
                                "type": "string",
                                "enum": [
                                    "Economics, Online Markets, and Human Computation",
                                    "Graph Algorithms and Learning for the Web",
                                    "Responsible Web",
                                    "Search",
                                    "Security",
                                    "Semantics and Knowledge",
                                    "Social Networks, Social Media, and Society",
                                    "Systems and Infrastructure for Web, Mobile, and WoT",
                                    "User Modeling and Recommendation",
                                    "Web Mining and Content Analysis",
                                    "COI"
                                ],
                                "input": 'select'
                            }
                        },
                        "description": "Submission track",
                        "order": 8
                    }
                },

            },
            forum=request_form.forum,
            invitation='openreview.net/Support/-/Request{}/Revision'.format(request_form.number),
            readers=['ACM.org/TheWebConf/2024/Conference/Program_Chairs', 'openreview.net/Support'],
            referent=request_form.forum,
            replyto=request_form.forum,
            signatures=['~Program_WebChair1'],
            writers=[]
        ))

        helpers.await_queue()

        pc_client_v2=openreview.api.OpenReviewClient(username='pc@webconf.org', password=helpers.strong_password)
        submission_invitation = pc_client_v2.get_invitation('ACM.org/TheWebConf/2024/Conference/-/Submission')
        assert submission_invitation.expdate < openreview.tools.datetime_millis(now)

        assert len(pc_client_v2.get_all_invitations(invitation='ACM.org/TheWebConf/2024/Conference/-/Withdrawal')) == 101
        assert len(pc_client_v2.get_all_invitations(invitation='ACM.org/TheWebConf/2024/Conference/-/Desk_Rejection')) == 101
        assert pc_client_v2.get_invitation('ACM.org/TheWebConf/2024/Conference/-/PC_Revision')
        assert pc_client_v2.get_group('ACM.org/TheWebConf/2024/Conference/Submission1/Senior_Area_Chairs')

        ## make submissions visible to ACs only
        pc_client.post_note(openreview.Note(
            content= {
                'force': 'Yes',
                'submission_readers': 'Assigned program committee (assigned reviewers, assigned area chairs, assigned senior area chairs if applicable)',
                'hide_fields': []
            },
            forum= request_form.id,
            invitation= f'openreview.net/Support/-/Request{request_form.number}/Post_Submission',
            readers=['ACM.org/TheWebConf/2024/Conference/Program_Chairs', 'openreview.net/Support'],
            referent= request_form.id,
            replyto= request_form.id,
            signatures=['~Program_WebChair1'],
            writers= [],
        ))

        helpers.await_queue()

        invitation = client.get_invitation(f'openreview.net/Support/-/Request{request_form.number}/Paper_Matching_Setup')
        assert 'ACM.org/TheWebConf/2024/Conference/COI_Senior_Area_Chairs' in invitation.reply['content']['matching_group']['value-dropdown']



    def test_recruit_acs(self, client, openreview_client, helpers, selenium, request_page):

        pc_client=openreview.Client(username='pc@webconf.org', password=helpers.strong_password)
        request_form=pc_client.get_notes(invitation='openreview.net/Support/-/Request_Form')[0]

        ac_roles = ["Econ_Area_Chairs", "Graph_Area_Chairs", "RespWeb_Area_Chairs", "Search_Area_Chairs", "Security_Area_Chairs", "Semantics_Area_Chairs", "Social_Area_Chairs", "Systems_Area_Chairs", "RecSys_Area_Chairs", "Mining_Area_Chairs", "COI_Area_Chairs"]

        ac_counter = 1

        for ac_role in ac_roles:

            reviewer_details = f'''ac{ac_counter}@{'gmail' if ac_counter == 21 else 'webconf'}.com, Area ChairOne
ac{ac_counter + 1}@{'gmail' if ac_counter == 21 else 'webconf'}.com, Area ChairTwo
'''
            ac_counter += 2
            pc_client.post_note(openreview.Note(
                content={
                    'title': 'Recruitment',
                    'invitee_role': ac_role,
                    'invitee_details': reviewer_details,
                    'invitee_reduced_load': ["1", "2", "3"],
                    'invitation_email_subject': '[TheWebConf 2023] Invitation to serve as {{invitee_role}}',
                    'invitation_email_content': 'Dear {{fullname}},\n\nYou have been nominated by the program chair committee of Theoretical Foundations of RL Workshop @ ICML 2020 to serve as {{invitee_role}}.\n\n{{invitation_url}}\n\nCheers!\n\nProgram Chairs'
                },
                forum=request_form.forum,
                replyto=request_form.forum,
                invitation='openreview.net/Support/-/Request{}/Recruitment'.format(request_form.number),
                readers=['ACM.org/TheWebConf/2024/Conference/Program_Chairs', 'openreview.net/Support'],
                signatures=['~Program_WebChair1'],
                writers=[]
            ))

            helpers.await_queue()

            role = ac_role.replace('_', ' ')
            role = role[:-1] if role.endswith('s') else role        
            messages = openreview_client.get_messages(subject = f'[TheWebConf 2023] Invitation to serve as {role}')
            assert len(messages) == 2

            for message in messages:
                text = message['content']['text']

                invitation_url = re.search('https://.*\n', text).group(0).replace('https://openreview.net', 'http://localhost:3030').replace('&amp;', '&')[:-1]
                helpers.respond_invitation(selenium, request_page, invitation_url, accept=True)

            assert len(openreview_client.get_group(f'ACM.org/TheWebConf/2024/Conference/{ac_role}').members) == 2

    def test_sac_assignment(self, client, openreview_client, helpers):

        pc_client=openreview.Client(username='pc@webconf.org', password=helpers.strong_password)
        request_form=pc_client.get_notes(invitation='openreview.net/Support/-/Request_Form')[0]

        venue = openreview.helpers.get_conference(pc_client, request_form_id=request_form.id, setup=False)     

        ## Assign SACs to submissions based on track
        with open(os.path.join(os.path.dirname(__file__), 'data/track_sacs.csv'), 'w') as file_handle:
            writer = csv.writer(file_handle)
            writer.writerow(["Economics, Online Markets, and Human Computation",'Econ_Senior_Area_Chairs'])
            writer.writerow(["Graph Algorithms and Learning for the Web",'Graph_Senior_Area_Chairs'])
            writer.writerow(["Responsible Web",'RespWeb_Senior_Area_Chairs'])
            writer.writerow(["Search",'Search_Senior_Area_Chairs'])
            writer.writerow(["Security",'Security_Senior_Area_Chairs'])
            writer.writerow(["Semantics and Knowledge",'Semantics_Senior_Area_Chairs'])
            writer.writerow(["Social Networks, Social Media, and Society",'Social_Senior_Area_Chairs'])
            writer.writerow(["Systems and Infrastructure for Web, Mobile, and WoT",'Systems_Senior_Area_Chairs'])
            writer.writerow(["User Modeling and Recommendation",'RecSys_Senior_Area_Chairs'])
            writer.writerow(["Web Mining and Content Analysis",'Mining_Senior_Area_Chairs'])
            writer.writerow(["COI", 'COI_Senior_Area_Chairs'])

        with open(os.path.join(os.path.dirname(__file__), 'data/track_acs.csv'), 'w') as file_handle:
            writer = csv.writer(file_handle)
            writer.writerow(["Economics, Online Markets, and Human Computation",'Econ_Area_Chairs'])
            writer.writerow(["Graph Algorithms and Learning for the Web",'Graph_Area_Chairs'])
            writer.writerow(["Responsible Web",'RespWeb_Area_Chairs'])
            writer.writerow(["Search",'Search_Area_Chairs'])
            writer.writerow(["Security",'Security_Area_Chairs'])
            writer.writerow(["Semantics and Knowledge",'Semantics_Area_Chairs'])
            writer.writerow(["Social Networks, Social Media, and Society",'Social_Area_Chairs'])
            writer.writerow(["Systems and Infrastructure for Web, Mobile, and WoT",'Systems_Area_Chairs'])
            writer.writerow(["User Modeling and Recommendation",'RecSys_Area_Chairs'])
            writer.writerow(["Web Mining and Content Analysis",'Mining_Area_Chairs'])
            writer.writerow(["COI", 'COI_Area_Chairs'])

        venue.set_track_sac_assignments(track_sac_file=os.path.join(os.path.dirname(__file__), 'data/track_sacs.csv'), conflict_policy='NeurIPS', conflict_n_years=3, track_ac_file=os.path.join(os.path.dirname(__file__), 'data/track_acs.csv'))

        assert openreview_client.get_group('ACM.org/TheWebConf/2024/Conference/Submission1/Senior_Area_Chairs').members == ['~SAC_WebChairEleven1']
        group = openreview_client.get_group('ACM.org/TheWebConf/2024/Conference/Submission10/Senior_Area_Chairs')
        assert len(group.members) == 2
        assert '~SAC_WebChairOne1' in group.members
        assert '~SAC_WebChairTwelve1' in group.members

        assignments = openreview_client.get_edges(invitation='ACM.org/TheWebConf/2024/Conference/Senior_Area_Chairs/-/Assignment', head='~AC_WebChairTwo1')
        assert len(assignments) == 2
        sacs = [e.tail for e in assignments]
        assert '~SAC_WebChairOne1' in sacs
        assert '~SAC_WebChairTwelve1' in sacs
   
    
    
    def test_ac_assignment(self, client, openreview_client, helpers, selenium, request_page):

        pc_client=openreview.Client(username='pc@webconf.org', password=helpers.strong_password)
        pc_client_v2=openreview.api.OpenReviewClient(username='pc@webconf.org', password=helpers.strong_password)
        request_form=pc_client.get_notes(invitation='openreview.net/Support/-/Request_Form')[0]

        submissions = pc_client_v2.get_notes(invitation='ACM.org/TheWebConf/2024/Conference/-/Submission', sort='number:asc')

        
        ac_roles = ["Econ_Area_Chairs", "Graph_Area_Chairs", "RespWeb_Area_Chairs", "Search_Area_Chairs", "Security_Area_Chairs", "Semantics_Area_Chairs", "Social_Area_Chairs", "Systems_Area_Chairs", "RecSys_Area_Chairs", "Mining_Area_Chairs", "COI_Area_Chairs"]
        tracks = [ "Economics, Online Markets, and Human Computation",
            "Graph Algorithms and Learning for the Web",
            "Responsible Web",
            "Search",
            "Security",
            "Semantics and Knowledge",
            "Social Networks, Social Media, and Society",
            "Systems and Infrastructure for Web, Mobile, and WoT",
            "User Modeling and Recommendation",
            "Web Mining and Content Analysis",
            "COI"
        ]
        
        for index, ac_role  in enumerate(ac_roles):
            ac_id = f'ACM.org/TheWebConf/2024/Conference/{ac_role}'
            track = tracks[index]
            openreview.tools.replace_members_with_ids(openreview_client, openreview_client.get_group(ac_id))
            track_acs = openreview_client.get_group(ac_id).members

            with open(os.path.join(os.path.dirname(__file__), 'data/rev_scores_venue.csv'), 'w') as file_handle:
                writer = csv.writer(file_handle)
                for submission in submissions:
                    if track == submission.content['track']['value']:
                        for ac in track_acs:
                            writer.writerow([submission.id, ac, round(random.random(), 2)])                   

            affinity_scores_url = client.put_attachment(os.path.join(os.path.dirname(__file__), 'data/rev_scores_venue.csv'), f'openreview.net/Support/-/Request{request_form.number}/Paper_Matching_Setup', 'upload_affinity_scores')

            client.post_note(openreview.Note(
                content={
                    'title': 'Paper Matching Setup',
                    'matching_group': ac_id,
                    'compute_conflicts': 'NeurIPS',
                    'compute_conflicts_N_years': '3',
                    'compute_affinity_scores': 'No',
                    'upload_affinity_scores': affinity_scores_url,
                    'submission_track': tracks[index]
                },
                forum=request_form.id,
                replyto=request_form.id,
                invitation=f'openreview.net/Support/-/Request{request_form.number}/Paper_Matching_Setup',
                readers=['ACM.org/TheWebConf/2024/Conference/Program_Chairs', 'openreview.net/Support'],
                signatures=['~Program_WebChair1'],
                writers=[]
            ))
            helpers.await_queue()

            assert openreview_client.get_invitation(f'{ac_id}/-/Conflict')
            assert openreview_client.get_invitation(f'{ac_id}/-/Affinity_Score')
            assert openreview_client.get_invitation(f'{ac_id}/-/Proposed_Assignment')
            assert openreview_client.get_invitation(f'{ac_id}/-/Constraint_Label')
            assignment_configuration_invitation = openreview_client.get_invitation(f'{ac_id}/-/Assignment_Configuration')
            assert assignment_configuration_invitation.edit['note']['content']['paper_invitation']['value']['param']['default'] == 'ACM.org/TheWebConf/2024/Conference/-/Submission&content.venueid=ACM.org/TheWebConf/2024/Conference/Submission&content.track=' + tracks[index]                  
            proposed_assignment_invitation = openreview_client.get_invitation(f'{ac_id}/-/Proposed_Assignment')
            assert proposed_assignment_invitation.edit['head']['param']['withContent'] == { 'track': track }
            assert proposed_assignment_invitation.readers == ['ACM.org/TheWebConf/2024/Conference', f'ACM.org/TheWebConf/2024/Conference/{ac_role.replace("Area_Chairs", "Senior_Area_Chairs")}', f'ACM.org/TheWebConf/2024/Conference/{ac_role}']
            assert proposed_assignment_invitation.edit['readers'] == ["ACM.org/TheWebConf/2024/Conference", 'ACM.org/TheWebConf/2024/Conference/Submission${{2/head}/number}/Senior_Area_Chairs', "${2/tail}"]
            affinity_score_invitation = openreview_client.get_invitation(f'{ac_id}/-/Affinity_Score')
            assert affinity_score_invitation.edit['head']['param']['withContent'] == { 'track': track }
            assert affinity_score_invitation.readers == ['ACM.org/TheWebConf/2024/Conference', f'ACM.org/TheWebConf/2024/Conference/{ac_role.replace("Area_Chairs", "Senior_Area_Chairs")}']
            assert affinity_score_invitation.edit['readers'] == ["ACM.org/TheWebConf/2024/Conference", f'ACM.org/TheWebConf/2024/Conference/{ac_role.replace("Area_Chairs", "Senior_Area_Chairs")}', "${2/tail}"]

            ## Build constraints
            labels = ['NA+EUR', 'ASIA', 'Africa', 'SA']
            for index, ac in enumerate(track_acs):
                openreview_client.post_edge(openreview.api.Edge(
                    invitation=f'{ac_id}/-/Constraint_Label',
                    signatures=['ACM.org/TheWebConf/2024/Conference'],
                    head=ac_id,
                    tail=ac,
                    label=labels[index % 4],
                ))

            # Post assignment config note
            assignment_config_note = openreview_client.post_note_edit(invitation=f'{ac_id}/-/Assignment_Configuration',
                signatures=[ 'ACM.org/TheWebConf/2024/Conference' ],
                note=openreview.api.Note(
                    content={
                        'title': { 'value': f'ac-assignment' },
                        'user_demand': { 'value': '1' },
                        'max_papers': { 'value': '1' },
                        'min_papers': { 'value': '0' },
                        'alternates': { 'value': '2' },
                        'paper_invitation': { 'value': 'ACM.org/TheWebConf/2024/Conference/-/Submission&content.venueid=ACM.org/TheWebConf/2024/Conference/Submission&content.track=' + tracks[index] },
                        'match_group': { 'value': ac_id },
                        'scores_specification': { 'value': { f'{ac_id}/-/Affinity_Score': { 'weight': 1, 'default': 0 }} },
                        'constraints_specification': { 'value': {
                            f"{ac_id}/-/Constraint_Label": [
                                {
                                    "label": "NA+EUR",
                                    "min_users": 1
                                },
                                {
                                    "label": "ASIA",
                                    "min_users": 1
                                }
                            ]                            
                        }},
                        'conflicts_invitation': { 'value': f'{ac_id}/-/Conflict' },
                        'custom_max_papers_invitation': { 'value': f'{ac_id}/-/Custom_Max_Papers'},
                        'aggregate_score_invitation': { 'value': f'{ac_id}/-/Aggregate_Score'},
                        'solver': { 'value': 'FairIR' },
                        'allow_zero_score_assignments': { 'value': 'No' },
                        'status': { 'value': 'Complete' },
                    }
                ))                                
        
        ## Build proposed assignments
        for submission in submissions:
            index = submission.number % 10
            if submission.number == 1 or submission.number == 101:
                index = 10
            ac_role = ac_roles[index]
            ac_id = f'ACM.org/TheWebConf/2024/Conference/{ac_role}'
            ac_profile = pc_client_v2.get_profile(f'ac{((index * 2) + 1)}@{"gmail" if ((index * 2) + 1) == 21 else "webconf"}.com')
            pc_client_v2.post_edge(
                openreview.api.Edge(
                    invitation=f'{ac_id}/-/Proposed_Assignment',
                    signatures=['ACM.org/TheWebConf/2024/Conference'],
                    head=submission.id,
                    tail=ac_profile.id,
                    label='ac-assignment',
                    weight=1.0
                )
            )

        venue = openreview.helpers.get_conference(pc_client, request_form.id, setup=False)

        for index, ac_role  in enumerate(ac_roles):
            venue.set_assignments(assignment_title='ac-assignment', committee_id=f'ACM.org/TheWebConf/2024/Conference/{ac_role}')
            ac_id = f'ACM.org/TheWebConf/2024/Conference/{ac_role}'
            assignment_invitation = openreview_client.get_invitation(f'{ac_id}/-/Assignment')
            assert assignment_invitation.edit['head']['param']['withContent'] == { 'track': tracks[index] }


        assert pc_client_v2.get_group('ACM.org/TheWebConf/2024/Conference/Submission1/Area_Chairs').members == ['~AC_WebChairTwentyOne1']                        
        assert pc_client_v2.get_group('ACM.org/TheWebConf/2024/Conference/Submission2/Area_Chairs').members == ['~AC_WebChairFive1']                        
        assert pc_client_v2.get_group('ACM.org/TheWebConf/2024/Conference/Submission3/Area_Chairs').members == ['~AC_WebChairSeven1']                        
        assert pc_client_v2.get_group('ACM.org/TheWebConf/2024/Conference/Submission4/Area_Chairs').members == ['~AC_WebChairNine1']                        
        assert pc_client_v2.get_group('ACM.org/TheWebConf/2024/Conference/Submission5/Area_Chairs').members == ['~AC_WebChairEleven1']                        
        assert pc_client_v2.get_group('ACM.org/TheWebConf/2024/Conference/Submission6/Area_Chairs').members == ['~AC_WebChairThirdTeen1']                        
        assert pc_client_v2.get_group('ACM.org/TheWebConf/2024/Conference/Submission7/Area_Chairs').members == ['~AC_WebChairFifthTeen1']                        
        assert pc_client_v2.get_group('ACM.org/TheWebConf/2024/Conference/Submission8/Area_Chairs').members == ['~AC_WebChairSevenTeen1']                        
        assert pc_client_v2.get_group('ACM.org/TheWebConf/2024/Conference/Submission9/Area_Chairs').members == ['~AC_WebChairNineTeen1']                        
        assert pc_client_v2.get_group('ACM.org/TheWebConf/2024/Conference/Submission10/Area_Chairs').members == ['~AC_WebChairOne1']


        ## Add second AC
        posted_edge = pc_client_v2.post_edge(
            openreview.api.Edge(
                invitation=f'{ac_id}/-/Assignment',
                signatures=['ACM.org/TheWebConf/2024/Conference'],
                head=submissions[0].id,
                tail='~AC_WebChairFive1',
                weight=1.0
            )
        )

        helpers.await_queue_edit(openreview_client, posted_edge.id)      

        assert pc_client_v2.get_group('ACM.org/TheWebConf/2024/Conference/Submission1/Area_Chairs').members == ['~AC_WebChairTwentyOne1', '~AC_WebChairFive1']                        
        assert pc_client_v2.get_group('ACM.org/TheWebConf/2024/Conference/Submission1/Senior_Area_Chairs').members == ['~SAC_WebChairEleven1']

        ## Remove second AC
        edges = pc_client_v2.get_edges(invitation=f'{ac_id}/-/Assignment', head=submissions[0].id, tail='~AC_WebChairTwentyOne1')
        edge = edges[0]
        edge.ddate = openreview.tools.datetime_millis(datetime.datetime.utcnow())
        posted_edge = pc_client_v2.post_edge(edge)

        helpers.await_queue_edit(openreview_client, posted_edge.id)                      

        assert pc_client_v2.get_group('ACM.org/TheWebConf/2024/Conference/Submission1/Area_Chairs').members == ['~AC_WebChairFive1']                        
        assert pc_client_v2.get_group('ACM.org/TheWebConf/2024/Conference/Submission1/Senior_Area_Chairs').members == ['~SAC_WebChairEleven1']

    def test_recruit_reviewers(self, client, openreview_client, helpers, selenium, request_page):

        pc_client=openreview.Client(username='pc@webconf.org', password=helpers.strong_password)
        request_form=pc_client.get_notes(invitation='openreview.net/Support/-/Request_Form')[0]

        reviewer_roles = [
            "Econ_Reviewers",
            "Graph_Reviewers",
            "RespWeb_Reviewers",
            "Search_Reviewers",
            "Security_Reviewers",
            "Semantics_Reviewers",
            "Social_Reviewers",
            "Systems_Reviewers",
            "RecSys_Reviewers",
            "Mining_Reviewers",
            "COI_Reviewers"                    
        ]

        reviewer_counter = 1

        for reviewer_role in reviewer_roles:

            reviewer_details = f'''reviewer{reviewer_counter}@{'gmail' if reviewer_counter == 21 else 'webconf'}.com, Reviewer ChairOne
reviewer{reviewer_counter + 1}@{'gmail' if reviewer_counter == 21 else 'webconf'}.com, Reviewer ChairTwo
'''
            reviewer_counter += 2
            pc_client.post_note(openreview.Note(
                content={
                    'title': 'Recruitment',
                    'invitee_role': reviewer_role,
                    'invitee_details': reviewer_details,
                    'invitee_reduced_load': ["1", "2", "3"],
                    'invitation_email_subject': '[TheWebConf 2023] Invitation to serve as {{invitee_role}}',
                    'invitation_email_content': 'Dear {{fullname}},\n\nYou have been nominated by the program chair committee of Theoretical Foundations of RL Workshop @ ICML 2020 to serve as {{invitee_role}}.\n\n{{invitation_url}}\n\nCheers!\n\nProgram Chairs'
                },
                forum=request_form.forum,
                replyto=request_form.forum,
                invitation='openreview.net/Support/-/Request{}/Recruitment'.format(request_form.number),
                readers=['ACM.org/TheWebConf/2024/Conference/Program_Chairs', 'openreview.net/Support'],
                signatures=['~Program_WebChair1'],
                writers=[]
            ))

            helpers.await_queue()

            role = reviewer_role.replace('_', ' ')
            role = role[:-1] if role.endswith('s') else role        
            messages = openreview_client.get_messages(subject = f'[TheWebConf 2023] Invitation to serve as {role}')
            assert len(messages) == 2

            for message in messages:
                text = message['content']['text']

                invitation_url = re.search('https://.*\n', text).group(0).replace('https://openreview.net', 'http://localhost:3030').replace('&amp;', '&')[:-1]
                helpers.respond_invitation(selenium, request_page, invitation_url, accept=True)

            assert len(openreview_client.get_group(f'ACM.org/TheWebConf/2024/Conference/{reviewer_role}').members) == 2                                

    def test_reviewer_assignment(self, client, openreview_client, helpers, selenium, request_page):

        pc_client=openreview.Client(username='pc@webconf.org', password=helpers.strong_password)
        pc_client_v2=openreview.api.OpenReviewClient(username='pc@webconf.org', password=helpers.strong_password)
        request_form=pc_client.get_notes(invitation='openreview.net/Support/-/Request_Form')[0]

        submissions = pc_client_v2.get_notes(invitation='ACM.org/TheWebConf/2024/Conference/-/Submission', sort='number:asc')

        reviewer_roles = [
            "Econ_Reviewers",
            "Graph_Reviewers",
            "RespWeb_Reviewers",
            "Search_Reviewers",
            "Security_Reviewers",
            "Semantics_Reviewers",
            "Social_Reviewers",
            "Systems_Reviewers",
            "RecSys_Reviewers",
            "Mining_Reviewers",
            "COI_Reviewers"                    
        ]
        tracks = [ "Economics, Online Markets, and Human Computation",
            "Graph Algorithms and Learning for the Web",
            "Responsible Web",
            "Search",
            "Security",
            "Semantics and Knowledge",
            "Social Networks, Social Media, and Society",
            "Systems and Infrastructure for Web, Mobile, and WoT",
            "User Modeling and Recommendation",
            "Web Mining and Content Analysis",
            "COI"
        ]
        
        for index, reviewer_role  in enumerate(reviewer_roles):
            reviewer_id = f'ACM.org/TheWebConf/2024/Conference/{reviewer_role}'
            track = tracks[index]
            openreview.tools.replace_members_with_ids(openreview_client, openreview_client.get_group(reviewer_id))

            with open(os.path.join(os.path.dirname(__file__), 'data/rev_scores_venue.csv'), 'w') as file_handle:
                writer = csv.writer(file_handle)
                for submission in submissions:
                    if track == submission.content['track']['value']:
                        for reviewer in openreview_client.get_group(reviewer_id).members:
                            writer.writerow([submission.id, reviewer, round(random.random(), 2)])

            affinity_scores_url = client.put_attachment(os.path.join(os.path.dirname(__file__), 'data/rev_scores_venue.csv'), f'openreview.net/Support/-/Request{request_form.number}/Paper_Matching_Setup', 'upload_affinity_scores')

            client.post_note(openreview.Note(
                content={
                    'title': 'Paper Matching Setup',
                    'matching_group': reviewer_id,
                    'compute_conflicts': 'NeurIPS',
                    'compute_conflicts_N_years': '3',
                    'compute_affinity_scores': 'No',
                    'upload_affinity_scores': affinity_scores_url,
                    'submission_track': track
                },
                forum=request_form.id,
                replyto=request_form.id,
                invitation=f'openreview.net/Support/-/Request{request_form.number}/Paper_Matching_Setup',
                readers=['ACM.org/TheWebConf/2024/Conference/Program_Chairs', 'openreview.net/Support'],
                signatures=['~Program_WebChair1'],
                writers=[]
            ))
            helpers.await_queue()

            assert openreview_client.get_invitation(f'{reviewer_id}/-/Conflict')
            assert openreview_client.get_invitation(f'{reviewer_id}/-/Affinity_Score')
            assert openreview_client.get_invitation(f'{reviewer_id}/-/Proposed_Assignment')
            assignment_configuration_invitation = openreview_client.get_invitation(f'{reviewer_id}/-/Assignment_Configuration')
            assert assignment_configuration_invitation.edit['note']['content']['paper_invitation']['value']['param']['default'] == 'ACM.org/TheWebConf/2024/Conference/-/Submission&content.venueid=ACM.org/TheWebConf/2024/Conference/Submission&content.track=' + track                  


        ## Build proposed assignments
        for submission in submissions:
            index = submission.number % 10
            if submission.number == 1 or submission.number == 101:
                index = 10
            reviewer_role = reviewer_roles[index]
            reviewer_id = f'ACM.org/TheWebConf/2024/Conference/{reviewer_role}'
            reviewer_profile = pc_client_v2.get_profile(f'reviewer{((index * 2) + 1)}@{"gmail" if ((index * 2) + 1) == 21 else "webconf"}.com')
            pc_client_v2.post_edge(
                openreview.api.Edge(
                    invitation=f'{reviewer_id}/-/Proposed_Assignment',
                    signatures=['ACM.org/TheWebConf/2024/Conference'],
                    head=submission.id,
                    tail=reviewer_profile.id,
                    label='reviewer-assignment',
                    weight=1.0
                )
            )
            reviewer_profile = pc_client_v2.get_profile(f'reviewer{((index * 2) + 2)}@{"gmail" if ((index * 2) + 2) == 22 else "webconf"}.com')
            pc_client_v2.post_edge(
                openreview.api.Edge(
                    invitation=f'{reviewer_id}/-/Proposed_Assignment',
                    signatures=['ACM.org/TheWebConf/2024/Conference'],
                    head=submission.id,
                    tail=reviewer_profile.id,
                    label='reviewer-assignment',
                    weight=1.0
                )
            )            

        venue = openreview.helpers.get_conference(pc_client, request_form.id, setup=False)

        for index, reviewer_role in enumerate(reviewer_roles):
            venue.set_assignments(assignment_title='reviewer-assignment', committee_id=f'ACM.org/TheWebConf/2024/Conference/{reviewer_role}', enable_reviewer_reassignment=True)
            invite_assignment_invitation = openreview_client.get_invitation(f'ACM.org/TheWebConf/2024/Conference/{reviewer_role}/-/Invite_Assignment')
            assert invite_assignment_invitation.edit['head']['param']['withContent'] == { 'track': tracks[index] }

        group = pc_client_v2.get_group('ACM.org/TheWebConf/2024/Conference/Submission1/Reviewers')
        assert len(group.members) == 2
        assert '~Reviewer_WebChairTwentyOne1' in group.members
        assert '~Reviewer_WebChairTwentyTwo1' in group.members

        group = pc_client_v2.get_group('ACM.org/TheWebConf/2024/Conference/Submission2/Reviewers')
        assert len(group.members) == 2
        assert '~Reviewer_WebChairFive1' in group.members
        assert '~Reviewer_WebChairSix1' in group.members 

        group = pc_client_v2.get_group('ACM.org/TheWebConf/2024/Conference/Submission10/Reviewers')
        assert len(group.members) == 2
        assert '~Reviewer_WebChairOne1' in group.members
        assert '~Reviewer_WebChairTwo1' in group.members

        invitation = client.get_invitation(f'openreview.net/Support/-/Request{request_form.number}/Paper_Matching_Setup')
        assert 'ACM.org/TheWebConf/2024/Conference/COI_Senior_Area_Chairs' in invitation.reply['content']['matching_group']['value-dropdown']

        ac_client = openreview.api.OpenReviewClient(username='ac5@webconf.com', password=helpers.strong_password)
        anon_group_id = ac_client.get_groups(prefix='ACM.org/TheWebConf/2024/Conference/Submission1/Area_Chair_', signatory='~AC_WebChairFive1')[0].id
        edge = ac_client.post_edge(
            openreview.api.Edge(invitation='ACM.org/TheWebConf/2024/Conference/COI_Reviewers/-/Invite_Assignment',
                signatures=[anon_group_id],
                head=submissions[0].id,
                tail='celeste@acm.org',
                label='Invitation Sent',
                weight=1
        ))
        helpers.await_queue_edit(openreview_client, edge.id)

        assert openreview_client.get_groups('ACM.org/TheWebConf/2024/Conference/Emergency_COI_Reviewers/Invited', member='celeste@acm.org')

        messages = client.get_messages(to='celeste@acm.org', subject='[TheWebConf24] Invitation to review paper titled "Paper title 1"')
        assert messages and len(messages) == 1
        invitation_url = re.search('https://.*\n', messages[0]['content']['text']).group(0).replace('https://openreview.net', 'http://localhost:3030').replace('&amp;', '&')[:-1]
        helpers.respond_invitation(selenium, request_page, invitation_url, accept=True)

        helpers.await_queue(openreview_client)

        ## External reviewer is set pending profile creation
        invite_edges=pc_client_v2.get_edges(invitation='ACM.org/TheWebConf/2024/Conference/COI_Reviewers/-/Invite_Assignment', head=submissions[0].id, tail='celeste@acm.org')
        assert len(invite_edges) == 1
        assert invite_edges[0].label == 'Pending Sign Up'

        helpers.create_user('celeste@acm.org', 'Celeste', 'ACM')

        ## Run Job
        openreview.venue.Venue.check_new_profiles(openreview_client)

        invite_edges=pc_client.get_edges(invitation='ACM.org/TheWebConf/2024/Conference/COI_Reviewers/-/Invite_Assignment', head=submissions[0].id, tail='celeste@acm.org')
        assert len(invite_edges) == 0

        invite_edges=pc_client.get_edges(invitation='ACM.org/TheWebConf/2024/Conference/COI_Reviewers/-/Invite_Assignment', head=submissions[0].id, tail='~Celeste_ACM1')
        assert len(invite_edges) == 1
        assert invite_edges[0].label == 'Accepted'

        messages = client.get_messages(to='celeste@acm.org', subject='[TheWebConf24] Reviewer Assignment confirmed for paper 1')
        assert messages and len(messages) == 1
        assert messages[0]['content']['text'] == '''Hi Celeste ACM,
Thank you for accepting the invitation to review the paper number: 1, title: Paper title 1.

Please go to the TheWebConf24 Reviewers Console and check your pending tasks: https://openreview.net/group?id=ACM.org/TheWebConf/2024/Conference/COI_Reviewers

If you would like to change your decision, please click the Decline link in the previous invitation email.

OpenReview Team'''