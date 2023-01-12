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

class TestARRVenue():

    @pytest.fixture(scope="class")
    def venue(self, client):
        pc_client=openreview.Client(username='pc@aclrollingreview.org', password='1234')
        request_form=client.get_notes(invitation='openreview.net/Support/-/Request_Form', sort='tmdate')[0]

        conference=openreview.helpers.get_conference(pc_client, request_form.id)
        return conference


    def test_create_venue(self, client, helpers):

        now = datetime.datetime.utcnow()
        due_date = now + datetime.timedelta(days=3)
        first_date = now + datetime.timedelta(days=1)

        # Post the request form note
        pc_client=helpers.create_user('pc@aclrollingreview.org', 'Program', 'ARRChair')

        helpers.create_user('ac1@gmail.com', 'Area', 'CMUChair', institution='cmu.edu')
        helpers.create_user('ac3@gmail.com', 'Area', 'MITChair', institution='mit.edu')
        helpers.create_user('ac3@amazon.com', 'Area', 'AmazonChair', institution='umass.edu')
        helpers.create_user('reviewer_arr1@umass.edu', 'Reviewer ARR', 'UMass', institution='umass.edu')
        helpers.create_user('reviewer_arr2@mit.edu', 'Reviewer ARR', 'MIT', institution='mit.edu')
        helpers.create_user('reviewer_arr3@ibm.com', 'Reviewer ARR', 'IBM', institution='ibm.com')
        helpers.create_user('reviewer_arr4@fb.com', 'Reviewer ARR', 'Facebook', institution='fb.com')
        helpers.create_user('reviewer_arr5@google.com', 'Reviewer ARR', 'Google', institution='google.com')
        helpers.create_user('ethic_chair@arr.org', 'Ethics', 'Chair', institution='google.com')

        request_form_note = pc_client.post_note(openreview.Note(
            invitation='openreview.net/Support/-/Request_Form',
            signatures=['~Program_ARRChair1'],
            readers=[
                'openreview.net/Support',
                '~Program_ARRChair1'
            ],
            writers=[],
            content={
                'title': 'ACL Rolling Review - September 2021',
                'Official Venue Name': 'ACL Rolling Review - September 2021',
                'Abbreviated Venue Name': 'ARR 2021 - September',
                'Official Website URL': 'http://aclrollingreview.org',
                'program_chair_emails': ['pc@aclrollingreview.org'],
                'contact_email': 'pc@aclrollingreview.org',
                'Area Chairs (Metareviewers)': 'Yes, our venue has Area Chairs',
                'senior_area_chairs': 'Yes, our venue has Senior Area Chairs',
                'ethics_chairs_and_reviewers': 'Yes, our venue has Ethics Chairs and Reviewers',
                'Venue Start Date': '2021/12/01',
                'Submission Deadline': due_date.strftime('%Y/%m/%d'),
                'abstract_registration_deadline': first_date.strftime('%Y/%m/%d'),
                'Location': 'Virtual',
                'Paper Matching': [
                    'Reviewer Bid Scores',
                    'OpenReview Affinity'],
                'Author and Reviewer Anonymity': 'Double-blind',
                'reviewer_identity': ['Program Chairs', 'Assigned Senior Area Chair', 'Assigned Area Chair'],
                'area_chair_identity': ['Program Chairs', 'Assigned Senior Area Chair'],
                'senior_area_chair_identity': ['Program Chairs', 'Assigned Senior Area Chair'],
                'Open Reviewing Policy': 'Submissions and reviews should both be private.',
                'submission_readers': 'All program committee (all reviewers, all area chairs, all senior area chairs if applicable)',
                'How did you hear about us?': 'ML conferences',
                'Expected Submissions': '100',
                'use_recruitment_template': 'Yes'
            }))

        helpers.await_queue()

        # Post a deploy note
        client.post_note(openreview.Note(
            content={'venue_id': 'aclweb.org/ACL/ARR/2021/September'},
            forum=request_form_note.forum,
            invitation='openreview.net/Support/-/Request{}/Deploy'.format(request_form_note.number),
            readers=['openreview.net/Support'],
            referent=request_form_note.forum,
            replyto=request_form_note.forum,
            signatures=['openreview.net/Support'],
            writers=['openreview.net/Support']
        ))

        helpers.await_queue()

        group = client.get_group('aclweb.org/ACL/ARR/2021/September')
        assert group
        assert group.host == 'aclweb.org/ACL'
        assert client.get_group('aclweb.org/ACL/ARR/2021/September/Program_Chairs')
        assert client.get_group('aclweb.org/ACL/ARR/2021/September/Senior_Area_Chairs')
        assert client.get_group('aclweb.org/ACL/ARR/2021/September/Area_Chairs')
        assert client.get_group('aclweb.org/ACL/ARR/2021/September/Reviewers')
        assert client.get_group('aclweb.org/ACL/ARR/2021/September/Authors')
        assert client.get_group('aclweb.org/ACL/ARR/2021/September/Ethics_Chairs')
        assert client.get_group('aclweb.org/ACL/ARR/2021/September/Ethics_Reviewers')

    def test_recruit_actions_editors(self, client, helpers, request_page, selenium):

        pc_client=openreview.Client(username='pc@aclrollingreview.org', password='1234')
        request_form=client.get_notes(invitation='openreview.net/Support/-/Request_Form', sort='tmdate')[0]

        ## Invite ~Area_CMUChair1 as AC
        reviewer_details = '''~Area_CMUChair1'''
        recruitment_note = pc_client.post_note(openreview.Note(
            content={
                'title': 'Recruitment',
                'invitee_role': 'Area_Chairs',
                'allow_role_overlap': 'Yes',
                'invitee_details': reviewer_details,
                'invitation_email_subject': '[ARR 2021 - September] Invitation to serve as {{invitee_role}}',
                'invitation_email_content': 'Dear {{fullname}},\n\nYou have been nominated by the program chair committee of Theoretical Foundations of RL Workshop @ ICML 2020 to serve as {{invitee_role}}.\n\nACCEPT LINK:\n\n{{invitation_url}}\n\nCheers!\n\nProgram Chairs'
            },
            forum=request_form.forum,
            replyto=request_form.forum,
            invitation='openreview.net/Support/-/Request{}/Recruitment'.format(request_form.number),
            readers=['aclweb.org/ACL/ARR/2021/September/Program_Chairs', 'openreview.net/Support'],
            signatures=['~Program_ARRChair1'],
            writers=[]
        ))
        assert recruitment_note

        helpers.await_queue()

        recruitment_status_notes=client.get_notes(forum=recruitment_note.forum, replyto=recruitment_note.id)
        assert len(recruitment_status_notes) == 1
        assert '1 users' in recruitment_status_notes[0].content['invited']
        assert "Please check the invitee group to see more details: https://openreview.net/group?id=aclweb.org/ACL/ARR/2021/September/Area_Chairs/Invited" in recruitment_status_notes[0].content['comment']


        ## Invite ~Area_CMUChair1 as Reviewer
        reviewer_details = '''~Area_CMUChair1'''
        recruitment_note = pc_client.post_note(openreview.Note(
            content={
                'title': 'Recruitment',
                'invitee_role': 'Reviewers',
                'invitee_details': reviewer_details,
                'allow_role_overlap': 'Yes',
                'invitation_email_subject': '[ARR 2021 - September] Invitation to serve as {{invitee_role}}',
                'invitation_email_content': 'Dear {{fullname}},\n\nYou have been nominated by the program chair committee of Theoretical Foundations of RL Workshop @ ICML 2020 to serve as {{invitee_role}}.\n\nACCEPT LINK:\n\n{{invitation_url}}\n\nCheers!\n\nProgram Chairs'
            },
            forum=request_form.forum,
            replyto=request_form.forum,
            invitation='openreview.net/Support/-/Request{}/Recruitment'.format(request_form.number),
            readers=['aclweb.org/ACL/ARR/2021/September/Program_Chairs', 'openreview.net/Support'],
            signatures=['~Program_ARRChair1'],
            writers=[]
        ))
        assert recruitment_note

        helpers.await_queue()

        recruitment_status_notes=client.get_notes(forum=recruitment_note.forum, replyto=recruitment_note.id)
        assert len(recruitment_status_notes) == 1
        assert '1 users' in recruitment_status_notes[0].content['invited']
        assert "Please check the invitee group to see more details: https://openreview.net/group?id=aclweb.org/ACL/ARR/2021/September/Reviewers/Invited" in recruitment_status_notes[0].content['comment']


        ## Invite ~Area_CMUChair1 as AC again
        reviewer_details = '''~Area_CMUChair1\n~Area_MITChair1'''
        recruitment_note = pc_client.post_note(openreview.Note(
            content={
                'title': 'Recruitment',
                'invitee_role': 'Area_Chairs',
                'allow_role_overlap': 'Yes',
                'invitee_details': reviewer_details,
                'invitation_email_subject': '[ARR 2021 - September] Invitation to serve as {{invitee_role}}',
                'invitation_email_content': 'Dear {{fullname}},\n\nYou have been nominated by the program chair committee of Theoretical Foundations of RL Workshop @ ICML 2020 to serve as {{invitee_role}}.\n\nACCEPT LINK:\n\n{{invitation_url}}\n\nCheers!\n\nProgram Chairs'
            },
            forum=request_form.forum,
            replyto=request_form.forum,
            invitation='openreview.net/Support/-/Request{}/Recruitment'.format(request_form.number),
            readers=['aclweb.org/ACL/ARR/2021/September/Program_Chairs', 'openreview.net/Support'],
            signatures=['~Program_ARRChair1'],
            writers=[]
        ))
        assert recruitment_note

        helpers.await_queue()

        recruitment_status_notes=client.get_notes(forum=recruitment_note.forum, replyto=recruitment_note.id)
        assert len(recruitment_status_notes) == 1
        assert '1 users' in recruitment_status_notes[0].content['invited']
        assert {'aclweb.org/ACL/ARR/2021/September/Area_Chairs/Invited': ['~Area_CMUChair1']} == recruitment_status_notes[0].content['already_invited']
        assert "Please check the invitee group to see more details: https://openreview.net/group?id=aclweb.org/ACL/ARR/2021/September/Area_Chairs/Invited" in recruitment_status_notes[0].content['comment']

        ## Accept to be a reviewer
        messages = client.get_messages(to = 'ac1@gmail.com', subject = '[ARR 2021 - September] Invitation to serve as Reviewer')
        text = messages[0]['content']['text']
        reviewer_invitation_url = re.search('https://.*\n', text).group(0).replace('https://openreview.net', 'http://localhost:3030')[:-1]
        helpers.respond_invitation(selenium, request_page, reviewer_invitation_url, accept=True)

        accepted_group = client.get_group(id='aclweb.org/ACL/ARR/2021/September/Reviewers')
        assert len(accepted_group.members) == 1
        assert '~Area_CMUChair1' in accepted_group.members
        assert client.get_messages(to = 'ac1@gmail.com', subject = '[ARR 2021 - September] Reviewer Invitation accepted')

        ## Accept to be an AC
        messages = client.get_messages(to = 'ac1@gmail.com', subject = '[ARR 2021 - September] Invitation to serve as Area Chair')
        text = messages[0]['content']['text']
        ac_invitation_url = re.search('https://.*\n', text).group(0).replace('https://openreview.net', 'http://localhost:3030')[:-1]
        helpers.respond_invitation(selenium, request_page, ac_invitation_url, accept=True)

        accepted_group = client.get_group(id='aclweb.org/ACL/ARR/2021/September/Area_Chairs')
        assert len(accepted_group.members) == 1
        assert '~Area_CMUChair1' in accepted_group.members
        assert client.get_messages(to = 'ac1@gmail.com', subject = '[ARR 2021 - September] Area Chair Invitation accepted')

        ## Decline to be a reviewer
        helpers.respond_invitation(selenium, request_page, reviewer_invitation_url, accept=False)
        accepted_group = client.get_group(id='aclweb.org/ACL/ARR/2021/September/Reviewers')
        assert len(accepted_group.members) == 0
        declined_group = client.get_group(id='aclweb.org/ACL/ARR/2021/September/Reviewers/Declined')
        assert len(declined_group.members) == 1
        assert '~Area_CMUChair1' in declined_group.members
        assert client.get_messages(to = 'ac1@gmail.com', subject = '[ARR 2021 - September] Reviewer Invitation declined')

        ## Keep in the AC group
        accepted_group = client.get_group(id='aclweb.org/ACL/ARR/2021/September/Area_Chairs')
        assert len(accepted_group.members) == 1
        assert '~Area_CMUChair1' in accepted_group.members

        ## Manual add an AC to the group and then invite them
        client.add_members_to_group('aclweb.org/ACL/ARR/2021/September/Area_Chairs', 'previous_ac@mail.com')

        accepted_group = client.get_group(id='aclweb.org/ACL/ARR/2021/September/Area_Chairs')
        assert len(accepted_group.members) == 2
        assert '~Area_CMUChair1' in accepted_group.members
        assert 'previous_ac@mail.com' in accepted_group.members

        reviewer_details = '''previous_ac@mail.com, Previous AC'''
        recruitment_note = pc_client.post_note(openreview.Note(
            content={
                'title': 'Recruitment',
                'invitee_role': 'Area_Chairs',
                'allow_role_overlap': 'Yes',
                'invitee_details': reviewer_details,
                'invitation_email_subject': '[ARR 2021 - September] Invitation to serve as {{invitee_role}}',
                'invitation_email_content': 'Dear {{fullname}},\n\nYou have been nominated by the program chair committee of Theoretical Foundations of RL Workshop @ ICML 2020 to serve as {{invitee_role}}.\n\nACCEPT LINK:\n\n{{invitation_url}}\n\nCheers!\n\nProgram Chairs'
            },
            forum=request_form.forum,
            replyto=request_form.forum,
            invitation='openreview.net/Support/-/Request{}/Recruitment'.format(request_form.number),
            readers=['aclweb.org/ACL/ARR/2021/September/Program_Chairs', 'openreview.net/Support'],
            signatures=['~Program_ARRChair1'],
            writers=[]
        ))
        assert recruitment_note

        helpers.await_queue()

        recruitment_status_notes=client.get_notes(forum=recruitment_note.forum, replyto=recruitment_note.id)
        assert len(recruitment_status_notes) == 1
        assert '0 users' in recruitment_status_notes[0].content['invited']
        assert {'aclweb.org/ACL/ARR/2021/September/Area_Chairs': ['previous_ac@mail.com']} == recruitment_status_notes[0].content['already_member']
        assert "Please check the invitee group to see more details: https://openreview.net/group?id=aclweb.org/ACL/ARR/2021/September/Area_Chairs/Invited" in recruitment_status_notes[0].content['comment']

        reviewer_details = '''previous_ac@mail.com, Previous AC'''
        recruitment_note = pc_client.post_note(openreview.Note(
            content={
                'title': 'Recruitment',
                'invitee_role': 'Reviewers',
                'allow_role_overlap': 'Yes',
                'invitee_details': reviewer_details,
                'invitation_email_subject': '[ARR 2021 - September] Invitation to serve as {{invitee_role}}',
                'invitation_email_content': 'Dear {{fullname}},\n\nYou have been nominated by the program chair committee of Theoretical Foundations of RL Workshop @ ICML 2020 to serve as {{invitee_role}}.\n\nACCEPT LINK:\n\n{{invitation_url}}\n\nCheers!\n\nProgram Chairs'
            },
            forum=request_form.forum,
            replyto=request_form.forum,
            invitation='openreview.net/Support/-/Request{}/Recruitment'.format(request_form.number),
            readers=['aclweb.org/ACL/ARR/2021/September/Program_Chairs', 'openreview.net/Support'],
            signatures=['~Program_ARRChair1'],
            writers=[]
        ))
        assert recruitment_note

        helpers.await_queue()

        recruitment_status_notes=client.get_notes(forum=recruitment_note.forum, replyto=recruitment_note.id)
        assert len(recruitment_status_notes) == 1
        assert '1 users' in recruitment_status_notes[0].content['invited']
        assert "Please check the invitee group to see more details: https://openreview.net/group?id=aclweb.org/ACL/ARR/2021/September/Reviewers/Invited" in recruitment_status_notes[0].content['comment']


    def test_recruit_ethic_chairs(self, client, helpers, request_page, selenium):

        pc_client=openreview.Client(username='pc@aclrollingreview.org', password='1234')
        request_form=client.get_notes(invitation='openreview.net/Support/-/Request_Form', sort='tmdate')[0]

        reviewer_details = '''ethic_chair@arr.org, Ethics Chair'''
        recruitment_note = pc_client.post_note(openreview.Note(
            content={
                'title': 'Recruitment',
                'invitee_role': 'Ethics_Chairs',
                'allow_role_overlap': 'Yes',
                'invitee_details': reviewer_details,
                'invitation_email_subject': '[ARR 2021 - September] Invitation to serve as {{invitee_role}}',
                'invitation_email_content': 'Dear {{fullname}},\n\nYou have been nominated by the program chair committee of Theoretical Foundations of RL Workshop @ ICML 2020 to serve as {{invitee_role}}.\n\nACCEPT LINK:\n\n{{invitation_url}}\n\nCheers!\n\nProgram Chairs'
            },
            forum=request_form.forum,
            replyto=request_form.forum,
            invitation='openreview.net/Support/-/Request{}/Recruitment'.format(request_form.number),
            readers=['aclweb.org/ACL/ARR/2021/September/Program_Chairs', 'openreview.net/Support'],
            signatures=['~Program_ARRChair1'],
            writers=[]
        ))
        assert recruitment_note

        helpers.await_queue()

        recruitment_status_notes=client.get_notes(forum=recruitment_note.forum, replyto=recruitment_note.id)
        assert len(recruitment_status_notes) == 1
        assert '1 users' in recruitment_status_notes[0].content['invited']
        assert "Please check the invitee group to see more details: https://openreview.net/group?id=aclweb.org/ACL/ARR/2021/September/Ethics_Chairs/Invited" in recruitment_status_notes[0].content['comment']

        ## Accept to be an Ethics Chair
        messages = client.get_messages(to = 'ethic_chair@arr.org', subject = '[ARR 2021 - September] Invitation to serve as Ethics Chair')
        text = messages[0]['content']['text']
        invitation_url = re.search('https://.*\n', text).group(0).replace('https://openreview.net', 'http://localhost:3030')[:-1]
        helpers.respond_invitation(selenium, request_page, invitation_url, accept=True)

        accepted_group = client.get_group(id='aclweb.org/ACL/ARR/2021/September/Ethics_Chairs')
        assert len(accepted_group.members) == 1
        assert 'ethic_chair@arr.org' in accepted_group.members
        assert client.get_messages(to = 'ethic_chair@arr.org', subject = '[ARR 2021 - September] Ethics Chair Invitation accepted')

    def test_recruit_ethic_reviewers(self, client, helpers, request_page, selenium):

        pc_client=openreview.Client(username='pc@aclrollingreview.org', password='1234')
        request_form=client.get_notes(invitation='openreview.net/Support/-/Request_Form', sort='tmdate')[0]

        ## Invite ~Area_CMUChair1 as AC
        reviewer_details = '''ethic_reviewer@arr.org, Ethics Reviewer'''
        recruitment_note = pc_client.post_note(openreview.Note(
            content={
                'title': 'Recruitment',
                'invitee_role': 'Ethics_Reviewers',
                'allow_role_overlap': 'Yes',
                'invitee_details': reviewer_details,
                'invitation_email_subject': '[ARR 2021 - September] Invitation to serve as {{invitee_role}}',
                'invitation_email_content': 'Dear {{fullname}},\n\nYou have been nominated by the program chair committee of Theoretical Foundations of RL Workshop @ ICML 2020 to serve as {{invitee_role}}.\n\nACCEPT LINK:\n\n{{invitation_url}}\n\nCheers!\n\nProgram Chairs'
            },
            forum=request_form.forum,
            replyto=request_form.forum,
            invitation='openreview.net/Support/-/Request{}/Recruitment'.format(request_form.number),
            readers=['aclweb.org/ACL/ARR/2021/September/Program_Chairs', 'openreview.net/Support'],
            signatures=['~Program_ARRChair1'],
            writers=[]
        ))
        assert recruitment_note

        helpers.await_queue()

        recruitment_status_notes=client.get_notes(forum=recruitment_note.forum, replyto=recruitment_note.id)
        assert len(recruitment_status_notes) == 1
        assert '1 users' in recruitment_status_notes[0].content['invited']
        assert "Please check the invitee group to see more details: https://openreview.net/group?id=aclweb.org/ACL/ARR/2021/September/Ethics_Reviewers/Invited" in recruitment_status_notes[0].content['comment']

        messages = client.get_messages(to = 'ethic_reviewer@arr.org', subject = '[ARR 2021 - September] Invitation to serve as Ethics Reviewer')
        text = messages[0]['content']['text']
        invitation_url = re.search('https://.*\n', text).group(0).replace('https://openreview.net', 'http://localhost:3030')[:-1]
        helpers.respond_invitation(selenium, request_page, invitation_url, accept=True)

        accepted_group = client.get_group(id='aclweb.org/ACL/ARR/2021/September/Ethics_Reviewers')
        assert len(accepted_group.members) == 1
        assert 'ethic_reviewer@arr.org' in accepted_group.members
        assert client.get_messages(to = 'ethic_reviewer@arr.org', subject = '[ARR 2021 - September] Ethics Reviewer Invitation accepted')

    def test_registration_tasks(self, client):

        pc_client=openreview.Client(username='pc@aclrollingreview.org', password='1234')
        request_form=client.get_notes(invitation='openreview.net/Support/-/Request_Form', sort='tmdate')[0]
        conference=openreview.helpers.get_conference(pc_client, request_form.id)

        fields = {}
        instructions = 'Test instructions for profile registration'
        conference.set_registration_stage(
            openreview.RegistrationStage(
                committee_id = conference.get_reviewers_id(),
                additional_fields = fields,
                instructions = instructions,
                name = 'Registration',
                title = 'Reviewers Registration Form',
                start_date = None,
                due_date = datetime.datetime.utcnow() + datetime.timedelta(minutes = 10)
            )
        )

        conference.set_registration_stage(
            openreview.RegistrationStage(
                committee_id = conference.get_area_chairs_id(),
                additional_fields = fields,
                instructions = instructions,
                name = 'Registration',
                title = 'Action Editors Registration Form',
                start_date = None,
                due_date = datetime.datetime.utcnow() + datetime.timedelta(minutes = 10)
            )
        )

        conference.set_registration_stage(
            openreview.RegistrationStage(
                committee_id = conference.get_senior_area_chairs_id(),
                additional_fields = fields,
                instructions = instructions,
                name = 'Registration',
                title = 'Senior Action Editors Registration Form',
                start_date = None,
                due_date = datetime.datetime.utcnow() + datetime.timedelta(minutes = 10)
            )
        )

        assert client.get_invitation('aclweb.org/ACL/ARR/2021/September/Reviewers/-/Registration')
        assert client.get_invitation('aclweb.org/ACL/ARR/2021/September/Area_Chairs/-/Registration')
        assert client.get_invitation('aclweb.org/ACL/ARR/2021/September/Senior_Area_Chairs/-/Registration')
        assert client.get_invitation('aclweb.org/ACL/ARR/2021/September/Reviewers/-/Registration_Form')
        assert client.get_invitation('aclweb.org/ACL/ARR/2021/September/Area_Chairs/-/Registration_Form')
        assert client.get_invitation('aclweb.org/ACL/ARR/2021/September/Senior_Area_Chairs/-/Registration_Form')

        notes = client.get_notes(invitation='aclweb.org/ACL/ARR/2021/September/Reviewers/-/Registration_Form')
        assert len(notes) == 1
        assert notes[0].content['instructions'] == 'Test instructions for profile registration'

        notes = client.get_notes(invitation='aclweb.org/ACL/ARR/2021/September/Area_Chairs/-/Registration_Form')
        assert len(notes) == 1
        assert notes[0].content['instructions'] == 'Test instructions for profile registration'

        notes = client.get_notes(invitation='aclweb.org/ACL/ARR/2021/September/Senior_Area_Chairs/-/Registration_Form')
        assert len(notes) == 1
        assert notes[0].content['instructions'] == 'Test instructions for profile registration'

        fields = {
            'agreement': {
                'description': "By selecting 'I agree' below you confirm that you agree to this license agreement.",
                'order': 8,
                'required': True,
                'value-radio': ["I agree", "I do not agree"]
            }
        }
        instructions = 'Test instructions for license agreement'
        conference.set_registration_stage(
            openreview.RegistrationStage(
                committee_id = conference.get_reviewers_id(),
                additional_fields = fields,
                remove_fields = ['profile_confirmed', 'expertise_confirmed'],
                instructions = instructions,
                name = 'License_Agreement',
                title = 'Reviewers License Agreement',
                start_date = None,
                due_date = datetime.datetime.utcnow() + datetime.timedelta(minutes = 10)
            )
        )

        assert client.get_invitation('aclweb.org/ACL/ARR/2021/September/Reviewers/-/Registration')
        assert client.get_invitation('aclweb.org/ACL/ARR/2021/September/Area_Chairs/-/Registration')
        assert client.get_invitation('aclweb.org/ACL/ARR/2021/September/Senior_Area_Chairs/-/Registration')
        assert client.get_invitation('aclweb.org/ACL/ARR/2021/September/Reviewers/-/Registration_Form')
        assert client.get_invitation('aclweb.org/ACL/ARR/2021/September/Area_Chairs/-/Registration_Form')
        assert client.get_invitation('aclweb.org/ACL/ARR/2021/September/Senior_Area_Chairs/-/Registration_Form')

        assert client.get_invitation('aclweb.org/ACL/ARR/2021/September/Reviewers/-/License_Agreement')
        with pytest.raises(openreview.OpenReviewException, match=r'The Invitation aclweb.org/ACL/ARR/2021/September/Area_Chairs/-/License_Agreement was not found'):
            assert client.get_invitation('aclweb.org/ACL/ARR/2021/September/Area_Chairs/-/License_Agreement')

        assert client.get_invitation('aclweb.org/ACL/ARR/2021/September/Reviewers/-/License_Agreement_Form')

        with pytest.raises(openreview.OpenReviewException, match=r'The Invitation aclweb.org/ACL/ARR/2021/September/Area_Chairs/-/License_Agreement_Form was not found'):
            assert client.get_invitation('aclweb.org/ACL/ARR/2021/September/Area_Chairs/-/License_Agreement_Form')

        notes = client.get_notes(invitation='aclweb.org/ACL/ARR/2021/September/Reviewers/-/License_Agreement_Form')
        assert len(notes) == 1
        assert notes[0].content['instructions'] == 'Test instructions for license agreement'


    def test_submit_papers(self, test_client, client, helpers):

        ## Need super user permission to add the venue to the active_venues group
        request_form=client.get_notes(invitation='openreview.net/Support/-/Request_Form', sort='tmdate')[0]
        conference=openreview.helpers.get_conference(client, request_form.id)

        domains = ['gmail.com', 'facebook.com', 'yahoo.com', 'ucla.edu', 'mdu.edu', 'cornell.edu']
        for i in range(1,6):
            note = openreview.Note(invitation = 'aclweb.org/ACL/ARR/2021/September/-/Submission',
                readers = ['aclweb.org/ACL/ARR/2021/September', 'test@mail.com', 'peter@mail.com', 'andrew@' + domains[i], '~SomeFirstName_User1'],
                writers = [conference.id, '~SomeFirstName_User1', 'peter@mail.com', 'andrew@' + domains[i]],
                signatures = ['~SomeFirstName_User1'],
                content = {
                    'title': 'Paper title ' + str(i) ,
                    'abstract': 'This is an abstract ' + str(i),
                    'authorids': ['test@mail.com', 'peter@mail.com', 'andrew@' + domains[i]],
                    'authors': ['SomeFirstName User', 'Peter SomeLastName', 'Andrew Mc']
                }
            )
            note = test_client.post_note(note)

        conference.setup_post_submission_stage(force=True)

        blinded_notes = test_client.get_notes(invitation='aclweb.org/ACL/ARR/2021/September/-/Blind_Submission')
        assert len(blinded_notes) == 5


    def test_setup_matching(self, venue, client, helpers, request_page, selenium):

        now = datetime.datetime.utcnow()

        pc_client=openreview.Client(username='pc@aclrollingreview.org', password='1234')

        venue.set_area_chairs(['~Area_CMUChair1', '~Area_MITChair1', '~Area_AmazonChair1'])

        submissions=venue.get_submissions(sort='tmdate')

        with open(os.path.join(os.path.dirname(__file__), 'data/ac_affinity_scores.csv'), 'w') as file_handle:
            writer = csv.writer(file_handle)
            for submission in submissions:
                writer.writerow([submission.id, '~Area_CMUChair1', round(random.random(), 2)])
                writer.writerow([submission.id, '~Area_MITChair1', round(random.random(), 2)])
                writer.writerow([submission.id, '~Area_AmazonChair1', round(random.random(), 2)])

        venue.setup_matching(committee_id=venue.get_area_chairs_id(), build_conflicts=True, affinity_score_file=os.path.join(os.path.dirname(__file__), 'data/ac_affinity_scores.csv'))


        venue.set_reviewers(['~Reviewer_ARR_UMass1', '~Reviewer_ARR_MIT1', '~Reviewer_ARR_IBM1', '~Reviewer_ARR_Facebook1', '~Reviewer_ARR_Google1'])

        with open(os.path.join(os.path.dirname(__file__), 'data/reviewer_affinity_scores.csv'), 'w') as file_handle:
            writer = csv.writer(file_handle)
            for submission in submissions:
                writer.writerow([submission.id, '~Reviewer_ARR_UMass1', round(random.random(), 2)])
                writer.writerow([submission.id, '~Reviewer_ARR_MIT1', round(random.random(), 2)])
                writer.writerow([submission.id, '~Reviewer_ARR_IBM1', round(random.random(), 2)])
                writer.writerow([submission.id, '~Reviewer_ARR_Facebook1', round(random.random(), 2)])
                writer.writerow([submission.id, '~Reviewer_ARR_Google1', round(random.random(), 2)])


        venue.setup_matching(committee_id=venue.get_reviewers_id(), build_conflicts=True, affinity_score_file=os.path.join(os.path.dirname(__file__), 'data/reviewer_affinity_scores.csv'))


        ## AC assignments
        client.post_edge(openreview.Edge(
            invitation='aclweb.org/ACL/ARR/2021/September/Area_Chairs/-/Proposed_Assignment',
            readers = [venue.id, f'aclweb.org/ACL/ARR/2021/September/Paper{submissions[0].number}/Senior_Area_Chairs', '~Area_CMUChair1'],
            writers = [venue.id, f'aclweb.org/ACL/ARR/2021/September/Paper{submissions[0].number}/Senior_Area_Chairs'],
            nonreaders = [f'aclweb.org/ACL/ARR/2021/September/Paper{submissions[0].number}/Authors'],
            signatures = [venue.id],
            head = submissions[0].id,
            tail = '~Area_CMUChair1',
            label = 'ac-matching',
            weight = 0.94
        ))
        client.post_edge(openreview.Edge(
            invitation='aclweb.org/ACL/ARR/2021/September/Area_Chairs/-/Proposed_Assignment',
            readers = [venue.id, f'aclweb.org/ACL/ARR/2021/September/Paper{submissions[1].number}/Senior_Area_Chairs', '~Area_MITChair1'],
            writers = [venue.id, f'aclweb.org/ACL/ARR/2021/September/Paper{submissions[1].number}/Senior_Area_Chairs'],
            nonreaders = [f'aclweb.org/ACL/ARR/2021/September/Paper{submissions[1].number}/Authors'],
            signatures = [venue.id],
            head = submissions[1].id,
            tail = '~Area_MITChair1',
            label = 'ac-matching',
            weight = 0.94
        ))
        client.post_edge(openreview.Edge(
            invitation='aclweb.org/ACL/ARR/2021/September/Area_Chairs/-/Proposed_Assignment',
            readers = [venue.id, f'aclweb.org/ACL/ARR/2021/September/Paper{submissions[2].number}/Senior_Area_Chairs', '~Area_AmazonChair1'],
            writers = [venue.id, f'aclweb.org/ACL/ARR/2021/September/Paper{submissions[2].number}/Senior_Area_Chairs'],
            nonreaders = [f'aclweb.org/ACL/ARR/2021/September/Paper{submissions[2].number}/Authors'],
            signatures = [venue.id],
            head = submissions[2].id,
            tail = '~Area_AmazonChair1',
            label = 'ac-matching',
            weight = 0.94
        ))
        client.post_edge(openreview.Edge(
            invitation='aclweb.org/ACL/ARR/2021/September/Area_Chairs/-/Proposed_Assignment',
            readers = [venue.id, f'aclweb.org/ACL/ARR/2021/September/Paper{submissions[3].number}/Senior_Area_Chairs', '~Area_CMUChair1'],
            writers = [venue.id, f'aclweb.org/ACL/ARR/2021/September/Paper{submissions[3].number}/Senior_Area_Chairs'],
            nonreaders = [f'aclweb.org/ACL/ARR/2021/September/Paper{submissions[3].number}/Authors'],
            signatures = [venue.id],
            head = submissions[3].id,
            tail = '~Area_CMUChair1',
            label = 'ac-matching',
            weight = 0.94
        ))
        client.post_edge(openreview.Edge(
            invitation='aclweb.org/ACL/ARR/2021/September/Area_Chairs/-/Proposed_Assignment',
            readers = [venue.id, f'aclweb.org/ACL/ARR/2021/September/Paper{submissions[4].number}/Senior_Area_Chairs', '~Area_MITChair1'],
            writers = [venue.id, f'aclweb.org/ACL/ARR/2021/September/Paper{submissions[4].number}/Senior_Area_Chairs'],
            nonreaders = [f'aclweb.org/ACL/ARR/2021/September/Paper{submissions[4].number}/Authors'],
            signatures = [venue.id],
            head = submissions[4].id,
            tail = '~Area_MITChair1',
            label = 'ac-matching',
            weight = 0.94
        ))

        ## Reviewer assignments
        ## Paper 5
        helpers.create_reviewer_edge(client, venue, 'Proposed_Assignment', submissions[0], '~Reviewer_ARR_Facebook1', label='reviewer-matching', weight=None)
        helpers.create_reviewer_edge(client, venue, 'Proposed_Assignment', submissions[0], '~Reviewer_ARR_MIT1', label='reviewer-matching', weight=None)
        helpers.create_reviewer_edge(client, venue, 'Aggregate_Score', submissions[0], '~Reviewer_ARR_UMass1', label='reviewer-matching', weight=0.33)
        helpers.create_reviewer_edge(client, venue, 'Aggregate_Score', submissions[0], '~Reviewer_ARR_MIT1', label='reviewer-matching', weight=0.87)
        helpers.create_reviewer_edge(client, venue, 'Aggregate_Score', submissions[0], '~Reviewer_ARR_IBM1', label='reviewer-matching', weight=0.56)
        helpers.create_reviewer_edge(client, venue, 'Aggregate_Score', submissions[0], '~Reviewer_ARR_Facebook1', label='reviewer-matching', weight=0.89)
        helpers.create_reviewer_edge(client, venue, 'Aggregate_Score', submissions[0], '~Reviewer_ARR_Google1', label='reviewer-matching', weight=0.98)

        ## Paper 4
        helpers.create_reviewer_edge(client, venue, 'Proposed_Assignment', submissions[1], '~Reviewer_ARR_Facebook1', label='reviewer-matching', weight=None)
        helpers.create_reviewer_edge(client, venue, 'Proposed_Assignment', submissions[1], '~Reviewer_ARR_IBM1', label='reviewer-matching', weight=None)
        helpers.create_reviewer_edge(client, venue, 'Aggregate_Score', submissions[1], '~Reviewer_ARR_UMass1', label='reviewer-matching', weight=0.33)
        helpers.create_reviewer_edge(client, venue, 'Aggregate_Score', submissions[1], '~Reviewer_ARR_MIT1', label='reviewer-matching', weight=0.87)
        helpers.create_reviewer_edge(client, venue, 'Aggregate_Score', submissions[1], '~Reviewer_ARR_IBM1', label='reviewer-matching', weight=0.56)
        helpers.create_reviewer_edge(client, venue, 'Aggregate_Score', submissions[1], '~Reviewer_ARR_Facebook1', label='reviewer-matching', weight=0.89)
        helpers.create_reviewer_edge(client, venue, 'Aggregate_Score', submissions[1], '~Reviewer_ARR_Google1', label='reviewer-matching', weight=0.98)

        ## Paper 3
        helpers.create_reviewer_edge(client, venue, 'Proposed_Assignment', submissions[2], '~Reviewer_ARR_Google1', label='reviewer-matching', weight=None)
        helpers.create_reviewer_edge(client, venue, 'Proposed_Assignment', submissions[2], '~Reviewer_ARR_IBM1', label='reviewer-matching', weight=None)
        helpers.create_reviewer_edge(client, venue, 'Aggregate_Score', submissions[2], '~Reviewer_ARR_UMass1', label='reviewer-matching', weight=0.33)
        helpers.create_reviewer_edge(client, venue, 'Aggregate_Score', submissions[2], '~Reviewer_ARR_MIT1', label='reviewer-matching', weight=0.87)
        helpers.create_reviewer_edge(client, venue, 'Aggregate_Score', submissions[2], '~Reviewer_ARR_IBM1', label='reviewer-matching', weight=0.56)
        helpers.create_reviewer_edge(client, venue, 'Aggregate_Score', submissions[2], '~Reviewer_ARR_Facebook1', label='reviewer-matching', weight=0.89)
        helpers.create_reviewer_edge(client, venue, 'Aggregate_Score', submissions[2], '~Reviewer_ARR_Google1', label='reviewer-matching', weight=0.98)

        ## Paper 2
        helpers.create_reviewer_edge(client, venue, 'Proposed_Assignment', submissions[3], '~Reviewer_ARR_Google1', label='reviewer-matching', weight=None)
        helpers.create_reviewer_edge(client, venue, 'Proposed_Assignment', submissions[3], '~Reviewer_ARR_MIT1', label='reviewer-matching', weight=None)
        helpers.create_reviewer_edge(client, venue, 'Aggregate_Score', submissions[3], '~Reviewer_ARR_UMass1', label='reviewer-matching', weight=0.33)
        helpers.create_reviewer_edge(client, venue, 'Aggregate_Score', submissions[3], '~Reviewer_ARR_MIT1', label='reviewer-matching', weight=0.87)
        helpers.create_reviewer_edge(client, venue, 'Aggregate_Score', submissions[3], '~Reviewer_ARR_IBM1', label='reviewer-matching', weight=0.56)
        helpers.create_reviewer_edge(client, venue, 'Aggregate_Score', submissions[3], '~Reviewer_ARR_Facebook1', label='reviewer-matching', weight=0.89)
        helpers.create_reviewer_edge(client, venue, 'Aggregate_Score', submissions[3], '~Reviewer_ARR_Google1', label='reviewer-matching', weight=0.98)

        ## Paper 1
        helpers.create_reviewer_edge(client, venue, 'Proposed_Assignment', submissions[4], '~Reviewer_ARR_UMass1', label='reviewer-matching', weight=None)
        helpers.create_reviewer_edge(client, venue, 'Proposed_Assignment', submissions[4], '~Reviewer_ARR_IBM1', label='reviewer-matching', weight=None)
        helpers.create_reviewer_edge(client, venue, 'Aggregate_Score', submissions[4], '~Reviewer_ARR_UMass1', label='reviewer-matching', weight=0.33)
        helpers.create_reviewer_edge(client, venue, 'Aggregate_Score', submissions[4], '~Reviewer_ARR_MIT1', label='reviewer-matching', weight=0.87)
        helpers.create_reviewer_edge(client, venue, 'Aggregate_Score', submissions[4], '~Reviewer_ARR_IBM1', label='reviewer-matching', weight=0.56)
        helpers.create_reviewer_edge(client, venue, 'Aggregate_Score', submissions[4], '~Reviewer_ARR_Facebook1', label='reviewer-matching', weight=0.89)
        helpers.create_reviewer_edge(client, venue, 'Aggregate_Score', submissions[4], '~Reviewer_ARR_Google1', label='reviewer-matching', weight=0.98)

        invite_assignment_edges=venue.set_invite_assignments(assignment_title='ac-matching', committee_id='aclweb.org/ACL/ARR/2021/September/Area_Chairs', enable_reviewer_reassignment='reviewer-matching')
        assert len(invite_assignment_edges) == 5

        helpers.await_queue()

        ## AC 1 accepts the invitation
        invite_edges=pc_client.get_edges(invitation='aclweb.org/ACL/ARR/2021/September/Area_Chairs/-/Invite_Assignment', head=submissions[0].id)
        assert len(invite_edges) == 1
        assert invite_edges[0].tail == '~Area_CMUChair1'
        assert invite_edges[0].label == 'Invitation Sent'

        messages = client.get_messages(to='ac1@gmail.com', subject='[ARR 2021 - September] Invitation to serve as area chair for paper titled Paper title 5')
        assert messages and len(messages) == 1
        invitation_message=messages[0]['content']['text']

        invitation_url = re.search('https://.*\n', invitation_message).group(0).replace('https://openreview.net', 'http://localhost:3030')[:-1]
        helpers.respond_invitation(selenium, request_page, invitation_url, accept=True)
        notes = selenium.find_element_by_class_name('note_editor')
        assert notes
        messages = notes.find_elements_by_tag_name('h4')
        assert messages
        assert 'Thank you for accepting this invitation from ACL Rolling Review - September 2021.' == messages[0].text

        helpers.await_queue()

        invite_edges=pc_client.get_edges(invitation='aclweb.org/ACL/ARR/2021/September/Area_Chairs/-/Invite_Assignment', head=submissions[0].id)
        assert len(invite_edges) == 1
        assert invite_edges[0].tail == '~Area_CMUChair1'
        assert invite_edges[0].label == 'Accepted'

        assert client.get_groups('aclweb.org/ACL/ARR/2021/September/Area_Chairs', member='~Area_CMUChair1')
        assert client.get_groups('aclweb.org/ACL/ARR/2021/September/Paper5/Area_Chairs', member='~Area_CMUChair1')

        # Confirmation email to the area chair
        messages = client.get_messages(to='ac1@gmail.com', subject='[ARR 2021 - September] Area Chair Invitation accepted for paper 5')
        assert messages and len(messages) == 1
        print('MESSAGE', messages[0]['content']['text'])
        assert messages[0]['content']['text'] == '''Hi Area CMUChair,
Thank you for accepting the invitation to serve as area chair for the paper number: 5, title: Paper title 5.

Please go to the ARR 2021 - September Area Chair Console and check your pending tasks: https://openreview.net/group?id=aclweb.org/ACL/ARR/2021/September/Area_Chairs.

If you would like to change your decision, please click the Decline link in the previous invitation email.

OpenReview Team'''


        # Assignment email to the area chair
        messages = client.get_messages(to='ac1@gmail.com', subject='[ARR 2021 - September] You have been assigned as a Area Chair for paper number 5')
        assert messages and len(messages) == 1
        assert messages[0]['content']['text'] == f'''This is to inform you that you have been assigned as a Area Chair for paper number 5 for ARR 2021 - September.

To review this new assignment, please login to OpenReview and go to https://openreview.net/forum?id={submissions[0].id}.

To check all of your assigned papers, go to https://openreview.net/group?id=aclweb.org/ACL/ARR/2021/September/Area_Chairs.

Thank you,

ACL ARR 2021 September Program Chairs'''


        ## AC 2 declines the invitation
        invite_edges=pc_client.get_edges(invitation='aclweb.org/ACL/ARR/2021/September/Area_Chairs/-/Invite_Assignment', head=submissions[1].id)
        assert len(invite_edges) == 1
        assert invite_edges[0].tail == '~Area_MITChair1'
        assert invite_edges[0].label == 'Invitation Sent'

        messages = client.get_messages(to='ac3@gmail.com', subject='[ARR 2021 - September] Invitation to serve as area chair for paper titled Paper title 4')
        assert messages and len(messages) == 1
        invitation_message=messages[0]['content']['text']

        invitation_url = re.search('https://.*\n', invitation_message).group(0).replace('https://openreview.net', 'http://localhost:3030')[:-1]
        helpers.respond_invitation(selenium, request_page, invitation_url, accept=False)
        notes = selenium.find_element_by_class_name('note_editor')
        assert notes
        messages = notes.find_elements_by_tag_name("h4")
        assert messages
        assert 'You have declined the invitation from ACL Rolling Review - September 2021.' == messages[0].text

        helpers.await_queue()

        invite_edges=pc_client.get_edges(invitation='aclweb.org/ACL/ARR/2021/September/Area_Chairs/-/Invite_Assignment', head=submissions[1].id)
        assert len(invite_edges) == 1
        assert invite_edges[0].tail == '~Area_MITChair1'
        assert invite_edges[0].label == 'Declined'

        assert client.get_groups('aclweb.org/ACL/ARR/2021/September/Area_Chairs', member='~Area_MITChair1')
        assert not client.get_groups('aclweb.org/ACL/ARR/2021/September/Paper4/Area_Chairs', member='~Area_MITChair1')

        # Confirmation email to the area chair
        messages = client.get_messages(to='ac3@gmail.com', subject='[ARR 2021 - September] Area Chair Invitation declined for paper 4')
        assert messages and len(messages) == 1
        assert messages[0]['content']['text'] == '''Hi Area MITChair,
You have declined the invitation to serve as area chair for the paper number: 4, title: Paper title 4.

If you would like to change your decision, please click the Accept link in the previous invitation email.

OpenReview Team'''

        ## Check the AC console edge browser url
        ac_client = openreview.Client(username='ac1@gmail.com', password='1234')
        request_page(selenium, "http://localhost:3030/group?id=aclweb.org/ACL/ARR/2021/September/Area_Chairs", ac_client.token, wait_for_element='edge_browser_url')
        header = selenium.find_element_by_id("header")
        assert header
        url = header.find_element_by_id("edge_browser_url")
        assert url
        assert 'Reviewers/-/Proposed_Assignment,label:reviewer-matching' in url.get_attribute('href')

        ## Invite assignments for reviewers
        invite_assignment_edges=venue.set_invite_assignments(assignment_title='reviewer-matching', committee_id='aclweb.org/ACL/ARR/2021/September/Reviewers', enable_reviewer_reassignment=True)
        assert len(invite_assignment_edges) == 10

        ## Reviewer reviewer_arr4@fb.com accepts the invitation
        invite_edges=pc_client.get_edges(invitation='aclweb.org/ACL/ARR/2021/September/Reviewers/-/Invite_Assignment', head=submissions[0].id, tail='~Reviewer_ARR_Facebook1')
        assert len(invite_edges) == 1
        assert invite_edges[0].label == 'Invitation Sent'

        messages = client.get_messages(to='reviewer_arr4@fb.com', subject='[ARR 2021 - September] Invitation to review paper titled Paper title 5')
        assert messages and len(messages) == 1
        invitation_message=messages[0]['content']['text']

        invitation_url = re.search('https://.*\n', invitation_message).group(0).replace('https://openreview.net', 'http://localhost:3030')[:-1]
        helpers.respond_invitation(selenium, request_page, invitation_url, accept=True)
        notes = selenium.find_element_by_class_name('note_editor')
        assert notes
        messages = notes.find_elements_by_tag_name("h4")
        assert messages
        assert 'Thank you for accepting this invitation from ACL Rolling Review - September 2021.' == messages[0].text

        helpers.await_queue()

        invite_edges=pc_client.get_edges(invitation='aclweb.org/ACL/ARR/2021/September/Reviewers/-/Invite_Assignment', head=submissions[0].id, tail='~Reviewer_ARR_Facebook1')
        assert len(invite_edges) == 1
        assert invite_edges[0].label == 'Accepted'

        assert client.get_groups('aclweb.org/ACL/ARR/2021/September/Reviewers', member='~Reviewer_ARR_Facebook1')
        assert client.get_groups('aclweb.org/ACL/ARR/2021/September/Paper5/Reviewers', member='~Reviewer_ARR_Facebook1')

        # Confirmation email to the reviewer
        messages = client.get_messages(to='reviewer_arr4@fb.com', subject='[ARR 2021 - September] Reviewer Invitation accepted for paper 5')
        assert messages and len(messages) == 1
        assert messages[0]['content']['text'] == '''Hi Reviewer ARR Facebook,
Thank you for accepting the invitation to review the paper number: 5, title: Paper title 5.

Please go to the ARR 2021 - September Reviewer Console and check your pending tasks: https://openreview.net/group?id=aclweb.org/ACL/ARR/2021/September/Reviewers.

If you would like to change your decision, please click the Decline link in the previous invitation email.

OpenReview Team'''

        # Confirmation email to the area chair
        messages = client.get_messages(to='ac1@gmail.com', subject='[ARR 2021 - September] Reviewer Reviewer ARR Facebook accepted to review paper 5')
        assert messages and len(messages) == 1
        assert messages[0]['content']['text'] == '''Hi Area CMUChair,
The Reviewer Reviewer ARR Facebook(reviewer_arr4@fb.com) that was invited to review paper 5 has accepted the invitation and is now assigned to the paper 5.

OpenReview Team'''

        # Assignment email to the reviewer
        messages = client.get_messages(to='reviewer_arr4@fb.com', subject='[ARR 2021 - September] You have been assigned as a Reviewer for paper number 5')
        assert messages and len(messages) == 1
        assert messages[0]['content']['text'] == f'''This is to inform you that you have been assigned as a Reviewer for paper number 5 for ARR 2021 - September.

To review this new assignment, please login to OpenReview and go to https://openreview.net/forum?id={submissions[0].id}.

To check all of your assigned papers, go to https://openreview.net/group?id=aclweb.org/ACL/ARR/2021/September/Reviewers.

Thank you,

ACL ARR 2021 September Program Chairs'''

        ## Reviewer reviewer_arr2@mit.edu declines the invitation
        invite_edges=pc_client.get_edges(invitation='aclweb.org/ACL/ARR/2021/September/Reviewers/-/Invite_Assignment', head=submissions[0].id, tail='~Reviewer_ARR_MIT1')
        assert len(invite_edges) == 1
        assert invite_edges[0].label == 'Invitation Sent'

        messages = client.get_messages(to='reviewer_arr2@mit.edu', subject='[ARR 2021 - September] Invitation to review paper titled Paper title 5')
        assert messages and len(messages) == 1
        invitation_message=messages[0]['content']['text']

        invitation_url = re.search('https://.*\n', invitation_message).group(0).replace('https://openreview.net', 'http://localhost:3030')[:-1]
        helpers.respond_invitation(selenium, request_page, invitation_url, accept=False)
        notes = selenium.find_element_by_class_name('note_editor')
        assert notes
        messages = notes.find_elements_by_tag_name("h4")
        assert messages
        assert 'You have declined the invitation from ACL Rolling Review - September 2021.' == messages[0].text

        helpers.await_queue()

        invite_edges=pc_client.get_edges(invitation='aclweb.org/ACL/ARR/2021/September/Reviewers/-/Invite_Assignment', head=submissions[0].id, tail='~Reviewer_ARR_MIT1')
        assert len(invite_edges) == 1
        assert invite_edges[0].label == 'Declined'

        assert client.get_groups('aclweb.org/ACL/ARR/2021/September/Reviewers', member='~Reviewer_ARR_MIT1')
        assert not client.get_groups('aclweb.org/ACL/ARR/2021/September/Paper5/Reviewers', member='~Reviewer_ARR_MIT1')

        # Confirmation email to the reviewer
        messages = client.get_messages(to='reviewer_arr2@mit.edu', subject='[ARR 2021 - September] Reviewer Invitation declined for paper 5')
        assert messages and len(messages) == 1
        assert messages[0]['content']['text'] == '''Hi Reviewer ARR MIT,
You have declined the invitation to review the paper number: 5, title: Paper title 5.

If you would like to change your decision, please click the Accept link in the previous invitation email.

OpenReview Team'''

        # Confirmation email to the area chair
        messages = client.get_messages(to='ac1@gmail.com', subject='[ARR 2021 - September] Reviewer Reviewer ARR MIT declined to review paper 5')
        assert messages and len(messages) == 1
        assert messages[0]['content']['text'] == '''Hi Area CMUChair,
The Reviewer Reviewer ARR MIT(reviewer_arr2@mit.edu) that was invited to review paper 5 has declined the invitation.

Please go to the Area Chair console: https://openreview.net/group?id=aclweb.org/ACL/ARR/2021/September/Area_Chairs to invite another reviewer.

OpenReview Team'''

        ## Check the AC console edge browser url
        ac_client = openreview.Client(username='ac1@gmail.com', password='1234')
        request_page(selenium, "http://localhost:3030/group?id=aclweb.org/ACL/ARR/2021/September/Area_Chairs", ac_client.token, wait_for_element='edge_browser_url')
        header = selenium.find_element_by_id("header")
        assert header
        url = header.find_element_by_id("edge_browser_url")
        assert url
        assert 'Reviewers/-/Assignment' in url.get_attribute('href')

        # Desk Reject Paper 2
        desk_reject_note = openreview.Note(
            invitation='aclweb.org/ACL/ARR/2021/September/Paper2/-/Desk_Reject',
            forum=submissions[3].forum,
            replyto=submissions[3].forum,
            readers=['aclweb.org/ACL/ARR/2021/September',
                     'aclweb.org/ACL/ARR/2021/September/Paper2/Authors',
                     'aclweb.org/ACL/ARR/2021/September/Paper2/Reviewers',
                     'aclweb.org/ACL/ARR/2021/September/Paper2/Area_Chairs',
                     'aclweb.org/ACL/ARR/2021/September/Paper2/Senior_Area_Chairs',
                     'aclweb.org/ACL/ARR/2021/September/Program_Chairs'],
            writers=[venue.get_id(), venue.get_program_chairs_id()],
            signatures=[venue.get_program_chairs_id()],
            content={
                'desk_reject_comments': 'PC has decided to reject this submission.',
                'title': 'Submission Desk Rejected by Program Chairs'
            }
        )

        posted_note = pc_client.post_note(desk_reject_note)
        assert posted_note

        helpers.await_queue()

        ## Reviewer reviewer_arr2@mit.edu tries to accept invitation for desk-rejected submission but gets an error
        invite_edges = pc_client.get_edges(invitation='aclweb.org/ACL/ARR/2021/September/Reviewers/-/Invite_Assignment',
                                           head=submissions[3].id, tail='~Reviewer_ARR_MIT1')
        assert len(invite_edges) == 1
        assert invite_edges[0].label == 'Invitation Sent'

        messages = client.get_messages(to='reviewer_arr2@mit.edu',
                                       subject='[ARR 2021 - September] Invitation to review paper titled Paper title 2')
        assert messages and len(messages) == 1
        invitation_message = messages[0]['content']['text']

        invitation_url = re.search('https://.*\n', invitation_message).group(0).replace('https://openreview.net', 'http://localhost:3030')[:-1]
        helpers.respond_invitation(selenium, request_page, invitation_url, accept=True)
        error_message = selenium.find_element_by_class_name('important_message')
        assert 'This submission is no longer under review. No action is required from your end.' == error_message.text


    def test_review_stage(self, venue, client, helpers):

        pc_client=openreview.Client(username='pc@aclrollingreview.org', password='1234')
        request_form=client.get_notes(invitation='openreview.net/Support/-/Request_Form', sort='tmdate')[0]

        # Post a review stage note
        now = datetime.datetime.utcnow()
        start_date = now - datetime.timedelta(days=2)
        due_date = now + datetime.timedelta(days=3)
        review_stage_note = pc_client.post_note(openreview.Note(
            content={
                'review_start_date': start_date.strftime('%Y/%m/%d'),
                'review_deadline': due_date.strftime('%Y/%m/%d'),
                'make_reviews_public': 'No, reviews should NOT be revealed publicly when they are posted',
                'release_reviews_to_authors': 'No, reviews should NOT be revealed when they are posted to the paper\'s authors',
                'release_reviews_to_reviewers': 'Reviews should be immediately revealed to the paper\'s reviewers who have already submitted their review',
                'remove_review_form_options': 'title',
                'email_program_chairs_about_reviews': 'Yes, email program chairs for each review received'
            },
            forum=request_form.forum,
            invitation='{}/-/Request{}/Review_Stage'.format('openreview.net/Support', request_form.number),
            readers=['aclweb.org/ACL/ARR/2021/September/Program_Chairs', 'openreview.net/Support'],
            referent=request_form.forum,
            signatures=['~Program_ARRChair1'],
            writers=[]
        ))
        assert review_stage_note
        helpers.await_queue()

        reviewer_client = openreview.Client(username='reviewer_arr4@fb.com', password='1234')
        signatory_groups=client.get_groups(regex='aclweb.org/ACL/ARR/2021/September/Paper5/Reviewer_', signatory='reviewer_arr4@fb.com')
        assert len(signatory_groups) == 1

        submissions=venue.get_submissions(number=5)

        reviewer_client.post_note(openreview.Note(
            invitation='aclweb.org/ACL/ARR/2021/September/Paper5/-/Official_Review',
            forum=submissions[0].id,
            replyto=submissions[0].id,
            readers=['aclweb.org/ACL/ARR/2021/September/Program_Chairs', 'aclweb.org/ACL/ARR/2021/September/Paper5/Senior_Area_Chairs', 'aclweb.org/ACL/ARR/2021/September/Paper5/Area_Chairs', 'aclweb.org/ACL/ARR/2021/September/Paper5/Reviewers/Submitted'],
            nonreaders=['aclweb.org/ACL/ARR/2021/September/Paper5/Authors'],
            writers=['aclweb.org/ACL/ARR/2021/September', signatory_groups[0].id],
            signatures=[signatory_groups[0].id],
            content={
                'review': 'This paper is ok',
                'rating': '10: Top 5% of accepted papers, seminal paper',
                'confidence': "1: The reviewer's evaluation is an educated guess"
            }

        ))

        helpers.await_queue()



    def test_ethics_review_stage(self, venue, client, helpers):

        pc_client=openreview.Client(username='pc@aclrollingreview.org', password='1234')
        ethics_chair_client=openreview.Client(username='ethic_chair@arr.org', password='1234')
        ## Need super user permission to add the venue to the active_venues group
        request_form=client.get_notes(invitation='openreview.net/Support/-/Request_Form', sort='tmdate')[0]

        now = datetime.datetime.utcnow()
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
                        "order": 1,
                        "value-regex": "[\\S\\s]{1,200000}",
                        "description": "Briefly summarize the ethics concerns.",
                        "required": True
                    }
                },
                'ethics_review_submissions': '1,5',
                'release_submissions_to_ethics_reviewers': 'We confirm we want to release the submissions and reviews to the ethics reviewers'
            },
            forum=request_form.forum,
            referent=request_form.forum,
            invitation='openreview.net/Support/-/Request{}/Ethics_Review_Stage'.format(request_form.number),
            readers=['aclweb.org/ACL/ARR/2021/September/Program_Chairs', 'openreview.net/Support'],
            signatures=['~Program_ARRChair1'],
            writers=[]
        ))

        helpers.await_queue()

        ## ethics chairs should be able to add ethics reviewers manually
        ethics_chair_client.add_members_to_group('aclweb.org/ACL/ARR/2021/September/Ethics_Reviewers', 'another@ethics_reviewer.org')

        groups = [ g for g in client.get_groups(regex='aclweb.org/ACL/ARR/2021/September/Paper.*') if 'Ethics_Reviewers' in g.id]
        assert len(groups) == 2
        assert client.get_group('aclweb.org/ACL/ARR/2021/September/Paper1/Ethics_Reviewers')
        assert client.get_group('aclweb.org/ACL/ARR/2021/September/Paper5/Ethics_Reviewers')

        invitations = [ i for i in client.get_invitations(regex='aclweb.org/ACL/ARR/2021/September/Paper.*') if 'Ethics_Review' in i.id]
        assert len(invitations) == 2
        assert client.get_invitation('aclweb.org/ACL/ARR/2021/September/Paper1/-/Ethics_Review')
        assert client.get_invitation('aclweb.org/ACL/ARR/2021/September/Paper5/-/Ethics_Review')

        submissions=venue.get_submissions(number=5)

        ## Assign ethics reviewer
        ethics_reviewer_client = helpers.create_user('ethic_reviewer@arr.org', 'Ethics', 'Reviewer')

        ethics_chair_client.post_edge(openreview.Edge(
            invitation='aclweb.org/ACL/ARR/2021/September/Ethics_Reviewers/-/Assignment',
            readers=['aclweb.org/ACL/ARR/2021/September', 'aclweb.org/ACL/ARR/2021/September/Ethics_Chairs', '~Ethics_Reviewer1'],
            nonreaders=['aclweb.org/ACL/ARR/2021/September/Paper5/Authors'],
            writers=['aclweb.org/ACL/ARR/2021/September', 'aclweb.org/ACL/ARR/2021/September/Ethics_Chairs'],
            head=submissions[0].id,
            tail='~Ethics_Reviewer1',
            signatures=['aclweb.org/ACL/ARR/2021/September/Ethics_Chairs']
        ))

        helpers.await_queue()

        assert '~Ethics_Reviewer1' in client.get_group('aclweb.org/ACL/ARR/2021/September/Paper5/Ethics_Reviewers').members

        submission = ethics_reviewer_client.get_note(submissions[0].id)
        assert 'aclweb.org/ACL/ARR/2021/September/Paper5/Ethics_Reviewers' in submission.readers
        assert 'aclweb.org/ACL/ARR/2021/September/Ethics_Chairs' in submission.readers

        reviews = ethics_reviewer_client.get_notes(forum=submission.id, invitation='aclweb.org/ACL/ARR/2021/September/Paper5/-/Official_Review')
        assert len(reviews) == 1
        assert 'aclweb.org/ACL/ARR/2021/September/Paper5/Ethics_Reviewers' in reviews[0].readers
        assert 'aclweb.org/ACL/ARR/2021/September/Ethics_Chairs' in reviews[0].readers

        signatory_groups=client.get_groups(regex='aclweb.org/ACL/ARR/2021/September/Paper5/Ethics_Reviewer_', signatory='ethic_reviewer@arr.org')
        assert len(signatory_groups) == 1

        ethics_reviewer_client.post_note(openreview.Note(
            invitation='aclweb.org/ACL/ARR/2021/September/Paper5/-/Ethics_Review',
            forum=submissions[0].id,
            replyto=submissions[0].id,
            readers=['aclweb.org/ACL/ARR/2021/September/Program_Chairs', 'aclweb.org/ACL/ARR/2021/September/Ethics_Chairs', signatory_groups[0].id],
            nonreaders=['aclweb.org/ACL/ARR/2021/September/Paper5/Authors'],
            writers=['aclweb.org/ACL/ARR/2021/September', signatory_groups[0].id],
            signatures=[signatory_groups[0].id],
            content={
                'ethics_concerns': 'This paper is ok',
                'recommendation': '1: No serious ethical issues'
            }
        ))

        helpers.await_queue()

        messages = client.get_messages(to='ethic_reviewer@arr.org', subject="[ARR 2021 - September] Your ethics review has been received on your assigned Paper number: 5, Paper title: \"Paper title 5\"")
        assert len(messages) == 1
        ## unflag papers
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
                        "order": 1,
                        "value-regex": "[\\S\\s]{1,200000}",
                        "description": "Briefly summarize the ethics concerns.",
                        "required": True
                    }
                },
                'ethics_review_submissions': '4,3',
                'release_submissions_to_ethics_reviewers': 'We confirm we want to release the submissions and reviews to the ethics reviewers'
            },
            forum=request_form.forum,
            referent=request_form.forum,
            invitation='openreview.net/Support/-/Request{}/Ethics_Review_Stage'.format(request_form.number),
            readers=['aclweb.org/ACL/ARR/2021/September/Program_Chairs', 'openreview.net/Support'],
            signatures=['~Program_ARRChair1'],
            writers=[]
        ))

        helpers.await_queue()

        groups = [ g for g in client.get_groups(regex='aclweb.org/ACL/ARR/2021/September/Paper.*') if 'Ethics_Reviewers' in g.id]
        assert len(groups) == 3
        assert client.get_group('aclweb.org/ACL/ARR/2021/September/Paper3/Ethics_Reviewers')
        assert client.get_group('aclweb.org/ACL/ARR/2021/September/Paper4/Ethics_Reviewers')
        ## Paper 5 stays because there is already an assigned reviewer and a review
        assert client.get_group('aclweb.org/ACL/ARR/2021/September/Paper5/Ethics_Reviewers')

        invitations = [ i for i in client.get_invitations(regex='aclweb.org/ACL/ARR/2021/September/Paper.*') if 'Ethics_Review' in i.id]
        assert len(invitations) == 3
        assert client.get_invitation('aclweb.org/ACL/ARR/2021/September/Paper3/-/Ethics_Review')
        assert client.get_invitation('aclweb.org/ACL/ARR/2021/September/Paper4/-/Ethics_Review')
        assert client.get_invitation('aclweb.org/ACL/ARR/2021/September/Paper5/-/Ethics_Review')

    def test_comment_email_pcs(self, venue, client, helpers, test_client):
        pc_client=openreview.Client(username='pc@aclrollingreview.org', password='1234')
        request_form=client.get_notes(invitation='openreview.net/Support/-/Request_Form', sort='tmdate')[0]
        now = datetime.datetime.utcnow()
        end_date = now + datetime.timedelta(days=3)
        # Post a comment stage note
        comment_stage_note = pc_client.post_note(openreview.Note(
            content={
                "commentary_start_date": now.strftime('%Y/%m/%d %H:%M'),
                "commentary_end_date": end_date.strftime('%Y/%m/%d %H:%M'),
                "participants": [
                    "Program Chairs",
                    "Assigned Senior Area Chairs",
                    "Assigned Area Chairs",
                    "Assigned Reviewers",
                    "Authors"
                ],
                "email_program_chairs_about_official_comments": "Yes, email PCs for each official comment made in the venue"
            },
            forum=request_form.forum,
            invitation='{}/-/Request{}/Comment_Stage'.format('openreview.net/Support', request_form.number),
            readers=[f'{request_form.content["venue_id"]}/Program_Chairs', 'openreview.net/Support'],
            referent=request_form.forum,
            signatures=['~Program_ARRChair1'],
            writers=[]
        ))
        assert comment_stage_note
        helpers.await_queue()
        paper = client.get_notes(invitation = "aclweb.org/ACL/ARR/2021/September/-/Blind_Submission")[0]
        test_client.post_note(openreview.Note(
            invitation = f"aclweb.org/ACL/ARR/2021/September/Paper{paper.number}/-/Official_Comment",
            content = {
                "title": "My test comment",
                "comment": "Let's see if the PCs are notified of this comment"
            },
            signatures = [f"aclweb.org/ACL/ARR/2021/September/Paper{paper.number}/Authors"],
            readers = ["aclweb.org/ACL/ARR/2021/September/Program_Chairs", f'aclweb.org/ACL/ARR/2021/September/Paper{paper.number}/Senior_Area_Chairs'],
            writers = ['aclweb.org/ACL/ARR/2021/September', f'aclweb.org/ACL/ARR/2021/September/Paper{paper.number}/Authors'],
            forum = paper.forum
        ))
        helpers.await_queue()
        messages = client.get_messages(to = 'pc@aclrollingreview.org', subject = '[ARR 2021 - September] An author commented on a paper. Paper Number: 5, Paper Title: "Paper title 5"')
        assert messages and len(messages) == 1
        assert "My test comment" in messages[0]["content"]["text"]
