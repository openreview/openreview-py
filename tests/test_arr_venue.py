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

class TestNeurIPSConference():

    @pytest.fixture(scope="class")
    def venue(self, client):
        pc_client=openreview.Client(username='pc@aclweb.org', password='1234')
        request_form=client.get_notes(invitation='openreview.net/Support/-/Request_Form')[0]

        conference=openreview.helpers.get_conference(pc_client, request_form.id)
        return conference


    def test_create_venue(self, client, helpers):

        now = datetime.datetime.utcnow()
        due_date = now + datetime.timedelta(days=3)
        first_date = now + datetime.timedelta(days=1)

        # Post the request form note
        pc_client=helpers.create_user('pc@aclweb.org', 'Program', 'ARRChair')

        helpers.create_user('ac1@gmail.com', 'Area', 'CMUChair', institution='cmu.edu')
        helpers.create_user('ac2@gmail.com', 'Area', 'MITChair', institution='mit.edu')
        helpers.create_user('ac3@amazon.com', 'Area', 'AmazonChair', institution='umass.edu')
        helpers.create_user('reviewer_arr1@umass.edu', 'Reviewer ARR', 'UMass', institution='umass.edu')
        helpers.create_user('reviewer_arr2@mit.edu', 'Reviewer ARR', 'MIT', institution='mit.edu')
        helpers.create_user('reviewer_arr3@ibm.com', 'Reviewer ARR', 'IBM', institution='ibm.com')
        helpers.create_user('reviewer_arr4@fb.com', 'Reviewer ARR', 'Facebook', institution='fb.com')
        helpers.create_user('reviewer_arr5@google.com', 'Reviewer ARR', 'Google', institution='google.com')

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
                'program_chair_emails': ['pc@aclweb.org'],
                'contact_email': 'pc@aclweb.org',
                'Area Chairs (Metareviewers)': 'Yes, our venue has Area Chairs',
                'senior_area_chairs': 'No, our venue does not have Senior Area Chairs',
                'Venue Start Date': '2021/12/01',
                'Submission Deadline': due_date.strftime('%Y/%m/%d'),
                'abstract_registration_deadline': first_date.strftime('%Y/%m/%d'),
                'Location': 'Virtual',
                'Paper Matching': [
                    'Reviewer Bid Scores',
                    'OpenReview Affinity'],
                'Author and Reviewer Anonymity': 'Double-blind',
                'reviewer_identity': ['Program Chairs', 'Assigned Area Chair'],
                'area_chair_identity': ['Program Chairs'],
                'senior_area_chair_identity': ['Program Chairs'],
                'Open Reviewing Policy': 'Submissions and reviews should both be private.',
                'How did you hear about us?': 'ML conferences',
                'Expected Submissions': '100'
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

        assert client.get_group('aclweb.org/ACL/ARR/2021/September')
        assert client.get_group('aclweb.org/ACL/ARR/2021/September/Program_Chairs')
        assert client.get_group('aclweb.org/ACL/ARR/2021/September/Area_Chairs')
        assert client.get_group('aclweb.org/ACL/ARR/2021/September/Reviewers')
        assert client.get_group('aclweb.org/ACL/ARR/2021/September/Authors')

    def test_submit_papers(self, test_client, client, helpers):

        ## Need super user permission to add the venue to the active_venues group
        request_form=client.get_notes(invitation='openreview.net/Support/-/Request_Form')[0]
        conference=openreview.helpers.get_conference(client, request_form.id)

        domains = ['umass.edu', 'amazon.com', 'fb.com', 'cmu.edu', 'google.com', 'mit.edu']
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

        pc_client=openreview.Client(username='pc@aclweb.org', password='1234')

        venue.set_area_chairs(['~Area_CMUChair1', '~Area_MITChair1', '~Area_AmazonChair1'])

        submissions=venue.get_submissions()

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
            readers = [venue.id, '~Area_CMUChair1'],
            writers = [venue.id],
            nonreaders = [f'aclweb.org/ACL/ARR/2021/September/Paper{submissions[0].number}/Authors'],
            signatures = [venue.id],
            head = submissions[0].id,
            tail = '~Area_CMUChair1',
            label = 'ac-matching',
            weight = 0.94
        ))
        client.post_edge(openreview.Edge(
            invitation='aclweb.org/ACL/ARR/2021/September/Area_Chairs/-/Proposed_Assignment',
            readers = [venue.id, '~Area_MITChair1'],
            writers = [venue.id],
            nonreaders = [f'aclweb.org/ACL/ARR/2021/September/Paper{submissions[1].number}/Authors'],
            signatures = [venue.id],
            head = submissions[1].id,
            tail = '~Area_MITChair1',
            label = 'ac-matching',
            weight = 0.94
        ))
        client.post_edge(openreview.Edge(
            invitation='aclweb.org/ACL/ARR/2021/September/Area_Chairs/-/Proposed_Assignment',
            readers = [venue.id, '~Area_AmazonChair1'],
            writers = [venue.id],
            nonreaders = [f'aclweb.org/ACL/ARR/2021/September/Paper{submissions[2].number}/Authors'],
            signatures = [venue.id],
            head = submissions[2].id,
            tail = '~Area_AmazonChair1',
            label = 'ac-matching',
            weight = 0.94
        ))
        client.post_edge(openreview.Edge(
            invitation='aclweb.org/ACL/ARR/2021/September/Area_Chairs/-/Proposed_Assignment',
            readers = [venue.id, '~Area_CMUChair1'],
            writers = [venue.id],
            nonreaders = [f'aclweb.org/ACL/ARR/2021/September/Paper{submissions[3].number}/Authors'],
            signatures = [venue.id],
            head = submissions[3].id,
            tail = '~Area_CMUChair1',
            label = 'ac-matching',
            weight = 0.94
        ))
        client.post_edge(openreview.Edge(
            invitation='aclweb.org/ACL/ARR/2021/September/Area_Chairs/-/Proposed_Assignment',
            readers = [venue.id, '~Area_MITChair1'],
            writers = [venue.id],
            nonreaders = [f'aclweb.org/ACL/ARR/2021/September/Paper{submissions[4].number}/Authors'],
            signatures = [venue.id],
            head = submissions[4].id,
            tail = '~Area_MITChair1',
            label = 'ac-matching',
            weight = 0.94
        ))


        invite_assignment_edges=venue.invite_assignments(assignment_title='ac-matching', committee_id='aclweb.org/ACL/ARR/2021/September/Area_Chairs')
        assert len(invite_assignment_edges) == 5

        helpers.await_queue()

        invite_edges=pc_client.get_edges(invitation='aclweb.org/ACL/ARR/2021/September/Area_Chairs/-/Invite_Assignment', head=submissions[0].id)
        assert len(invite_edges) == 1
        assert invite_edges[0].tail == '~Area_CMUChair1'
        assert invite_edges[0].label == 'Invitation Sent'

        messages = client.get_messages(to='ac1@gmail.com', subject='[ARR 2021 - September] Invitation to review paper titled Paper title 5')
        assert messages and len(messages) == 1
        invitation_message=messages[0]['content']['text']

        accept_url = re.search('https://.*response=Yes', invitation_message).group(0).replace('https://openreview.net', 'http://localhost:3030')
        request_page(selenium, accept_url, alert=True)
        notes = selenium.find_element_by_id("notes")
        assert notes
        messages = notes.find_elements_by_tag_name("h3")
        assert messages
        assert 'Thank you for accepting this invitation from ACL Rolling Review - September 2021.' == messages[0].text

        helpers.await_queue()

        invite_edges=pc_client.get_edges(invitation='aclweb.org/ACL/ARR/2021/September/Area_Chairs/-/Invite_Assignment', head=submissions[0].id)
        assert len(invite_edges) == 1
        assert invite_edges[0].tail == '~Area_CMUChair1'
        assert invite_edges[0].label == 'Accepted'

        assert client.get_groups('aclweb.org/ACL/ARR/2021/September/Area_Chairs', member='~Area_CMUChair1')
        assert client.get_groups('aclweb.org/ACL/ARR/2021/September/Paper5/Area_Chairs', member='~Area_CMUChair1')

        # Confirmation email to the reviewer
        messages = client.get_messages(to='ac1@gmail.com', subject='[ARR 2021 - September] Reviewer Invitation accepted for paper 5')
        assert messages and len(messages) == 1
        assert messages[0]['content']['text'] == '''Hi Area CMUChair,
Thank you for accepting the invitation to review the paper number: 5, title: Paper title 5.

Please go to the ARR 2021 - September Reviewers Console and check your pending tasks: https://openreview.net/group?id=aclweb.org/ACL/ARR/2021/September/Area_Chairs

If you would like to change your decision, please click the Decline link in the previous invitation email.

OpenReview Team'''



