import os
import csv
import pytest
import random
import datetime
import openreview
from openreview.api import Edge
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException

class TestSACAssignments():

    def test_create_conference(self, client, openreview_client, helpers):

        now = datetime.datetime.now()
        due_date = now + datetime.timedelta(days=3)
        first_date = now + datetime.timedelta(days=1)

        # Post the request form note
        helpers.create_user('pc@matching.org', 'Program', 'MatchingChair')
        pc_client = openreview.Client(username='pc@matching.org', password=helpers.strong_password)

        helpers.create_user('sac@umass.edu', 'SAC', 'MatchingOne')
        helpers.create_user('sac2@ucla.edu', 'SAC', 'MatchingTwo')
        helpers.create_user('sac3@gmail.com', 'SAC', 'MatchingThree')

        request_form_note = pc_client.post_note(openreview.Note(
            invitation='openreview.net/Support/-/Request_Form',
            signatures=['~Program_MatchingChair1'],
            readers=[
                'openreview.net/Support',
                '~Program_MatchingChair1'
            ],
            writers=[],
            content={
                'title': 'Test SAC Matching Venue',
                'Official Venue Name': 'Test SAC Matching Venue',
                'Abbreviated Venue Name': 'SAC Matching 2024',
                'Official Website URL': 'https://2024.matching.org/',
                'program_chair_emails': ['pc@matching.org'],
                'contact_email': 'pc@matching.org',
                'publication_chairs':'No, our venue does not have Publication Chairs',
                'Area Chairs (Metareviewers)': 'Yes, our venue has Area Chairs',
                'senior_area_chairs': 'Yes, our venue has Senior Area Chairs',
                'senior_area_chairs_assignment': 'Submissions',
                'Venue Start Date': '2024/07/01',
                'Submission Deadline': due_date.strftime('%Y/%m/%d'),
                'Location': 'Amherst',
                'submission_reviewer_assignment': 'Automatic',
                'Author and Reviewer Anonymity': 'Double-blind',
                'reviewer_identity': ['Program Chairs', 'Assigned Senior Area Chair', 'Assigned Area Chair'],
                'area_chair_identity': ['Program Chairs', 'Assigned Senior Area Chair', 'Assigned Area Chair'],
                'senior_area_chair_identity': ['Program Chairs', 'Assigned Senior Area Chair'],
                'submission_readers': 'All program committee (all reviewers, all area chairs, all senior area chairs if applicable)',
                'How did you hear about us?': 'ML conferences',
                'email_pcs_for_withdrawn_submissions': 'No, do not email PCs.',
                'email_pcs_for_desk_rejected_submissions': 'No, do not email PCs.',
                'Expected Submissions': '50',
                'use_recruitment_template': 'Yes',
                'api_version': '2',
                'submission_license': ['CC BY 4.0'],
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
            content={'venue_id': 'TSACM/2024/Conference'},
            forum=request_form_note.forum,
            invitation='openreview.net/Support/-/Request{}/Deploy'.format(request_form_note.number),
            readers=['openreview.net/Support'],
            referent=request_form_note.forum,
            replyto=request_form_note.forum,
            signatures=['openreview.net/Support'],
            writers=['openreview.net/Support']
        ))

        helpers.await_queue()

        assert openreview_client.get_group('TSACM/2024/Conference')
        assert openreview_client.get_group('TSACM/2024/Conference/Senior_Area_Chairs')

        assert openreview_client.get_invitation('TSACM/2024/Conference/-/Submission')

    def test_submit_papers(self, test_client, client, openreview_client, helpers):

        test_client = openreview.api.OpenReviewClient(username='test@mail.com', password=helpers.strong_password)

        domains = ['smith.edu', 'umass.edu', 'ucla.edu', 'meta.com']
        for i in range(1, 4):
            note = openreview.api.Note(
                content = {
                    'title': { 'value': 'Test Paper ' + str(i) },
                    'abstract': { 'value': 'This is a test abstract ' + str(i) },
                    'authorids': { 'value': ['test@mail.com', 'maria@' + domains[i-1]] },
                    'authors': { 'value': ['SomeFirstName User', 'Maria SomeLastName'] },
                    'keywords': { 'value': ['computer vision', 'nlp'] },
                    'pdf': {'value': '/pdf/' + 'p' * 40 +'.pdf' }
                }
            )

            test_client.post_note_edit(invitation='TSACM/2024/Conference/-/Submission',
                signatures=['~SomeFirstName_User1'],
                note=note)  
            
        #close submissions and hide pdfs for bidding
        now = datetime.datetime.now()
        start_date = now - datetime.timedelta(days=3)
        due_date = now - datetime.timedelta(days=1)

        pc_client = openreview.Client(username='pc@matching.org', password=helpers.strong_password)
        request_form=client.get_notes(invitation='openreview.net/Support/-/Request_Form', sort='tmdate')[0]

        venue_revision_note = pc_client.post_note(openreview.Note(
            content={
                'title': 'Test SAC Matching Venue',
                'Official Venue Name': 'Test SAC Matching Venue',
                'Abbreviated Venue Name': 'SAC Matching 2024',
                'Official Website URL': 'https://2024.matching.org/',
                'program_chair_emails': ['pc@matching.org'],
                'contact_email': 'pc@matching.org',
                'publication_chairs':'No, our venue does not have Publication Chairs',
                'Venue Start Date': '2024/07/01',
                'Submission Deadline': due_date.strftime('%Y/%m/%d'),
                'Submission Start Date': start_date.strftime('%Y/%m/%d'),
                'Location': 'Amherst',
                'submission_reviewer_assignment': 'Automatic',
                'How did you hear about us?': 'ML conferences',
                'Expected Submissions': '50',
                'use_recruitment_template': 'Yes'
            },
            forum=request_form.forum,
            invitation='openreview.net/Support/-/Request{}/Revision'.format(request_form.number),
            readers=['{}/Program_Chairs'.format('TSACM/2024/Conference'), 'openreview.net/Support'],
            referent=request_form.forum,
            replyto=request_form.forum,
            signatures=['~Program_MatchingChair1'],
            writers=[]
        ))

        helpers.await_queue()

        # hide pdf for bidding
        post_submission_note=pc_client.post_note(openreview.Note(
            content= {
                'force': 'Yes',
                'hide_fields': ['pdf'],
                'submission_readers': 'All program committee (all reviewers, all area chairs, all senior area chairs if applicable)'
            },
            forum= request_form.id,
            invitation= f'openreview.net/Support/-/Request{request_form.number}/Post_Submission',
            readers= ['TSACM/2024/Conference/Program_Chairs', 'openreview.net/Support'],
            referent= request_form.id,
            replyto= request_form.id,
            signatures= ['~Program_MatchingChair1'],
            writers= [],
        ))

        helpers.await_queue()

    def test_setup_matching(self, client, openreview_client, helpers):

        pc_client = openreview.Client(username='pc@matching.org', password=helpers.strong_password)
        pc_client_v2=openreview.api.OpenReviewClient(username='pc@matching.org', password=helpers.strong_password)

        request_form=pc_client.get_notes(invitation='openreview.net/Support/-/Request_Form', sort='tmdate')[0]
        venue = openreview.helpers.get_conference(client, request_form.forum, 'openreview.net/Support', setup=False)

        submissions = venue.get_submissions(sort='number:asc')

        ## setup matching with no SACs
        matching_setup_note = pc_client.post_note(openreview.Note(
            content={
                'title': 'Paper Matching Setup',
                'matching_group': 'TSACM/2024/Conference/Senior_Area_Chairs',
                'compute_conflicts': 'Default',
                'compute_affinity_scores': 'No'

            },
            forum=request_form.id,
            replyto=request_form.id,
            invitation=f'openreview.net/Support/-/Request{request_form.number}/Paper_Matching_Setup',
            readers=['TSACM/2024/Conference/Program_Chairs', 'openreview.net/Support'],
            signatures=['~Program_MatchingChair1'],
            writers=[]
        ))
        helpers.await_queue()

        comment_invitation_id = f'openreview.net/Support/-/Request{request_form.number}/Paper_Matching_Setup_Status'
        matching_status = client.get_notes(invitation=comment_invitation_id, replyto=matching_setup_note.id, forum=request_form.forum, sort='tmdate')[0]
        assert matching_status
        assert 'Could not compute affinity scores and conflicts since there are no Senior Area Chairs. You can use the \'Recruitment\' button to recruit Senior Area Chairs.' in matching_status.content['error']

        openreview_client.add_members_to_group(
            'TSACM/2024/Conference/Senior_Area_Chairs', 
            ['~SAC_MatchingOne1', '~SAC_MatchingTwo1', '~SAC_MatchingThree1']
        )

        ## setup matching to assign SAC to papers to create Assignment_Configuration, do not compute affinity scores
        matching_setup_note = client.post_note(openreview.Note(
            content={
                'title': 'Paper Matching Setup',
                'matching_group': 'TSACM/2024/Conference/Senior_Area_Chairs',
                'compute_conflicts': 'Default',
                'compute_affinity_scores': 'No'

            },
            forum=request_form.id,
            replyto=request_form.id,
            invitation=f'openreview.net/Support/-/Request{request_form.number}/Paper_Matching_Setup',
            readers=['TSACM/2024/Conference/Program_Chairs', 'openreview.net/Support'],
            signatures=['~Program_MatchingChair1'],
            writers=[]
        ))

        helpers.await_queue()

        comment_invitation_id = f'openreview.net/Support/-/Request{request_form.number}/Paper_Matching_Setup_Status'
        matching_status = client.get_notes(invitation=comment_invitation_id, replyto=matching_setup_note.id, forum=request_form.forum, sort='tmdate')[0]
        assert matching_status
        assert matching_status.content['comment'] == '''Affinity scores and/or conflicts were successfully computed. To run the matcher, click on the 'Senior Area Chairs Paper Assignment' link in the PC console: https://openreview.net/group?id=TSACM/2024/Conference/Program_Chairs

Please refer to the documentation for instructions on how to run the matcher: https://docs.openreview.net/how-to-guides/paper-matching-and-assignment/how-to-do-automatic-assignments'''

        assignment_config_inv = pc_client_v2.get_invitation('TSACM/2024/Conference/Senior_Area_Chairs/-/Assignment_Configuration')
        assert assignment_config_inv
        assert 'scores_specification' in assignment_config_inv.edit['note']['content']
        assert 'default' not in assignment_config_inv.edit['note']['content']['scores_specification']['value']['param']

        with open(os.path.join(os.path.dirname(__file__), 'data/sac_scores_matching.csv'), 'w') as file_handle:
            writer = csv.writer(file_handle)
            for submission in submissions:
                for sac in openreview_client.get_group('TSACM/2024/Conference/Senior_Area_Chairs').members:
                    writer.writerow([submission.id, sac, round(random.random(), 2)])

        affinity_scores_url = client.put_attachment(os.path.join(os.path.dirname(__file__), 'data/sac_scores_matching.csv'), f'openreview.net/Support/-/Request{request_form.number}/Paper_Matching_Setup', 'upload_affinity_scores')
        
        ## setup matching to assign SAC to papers
        matching_setup_note = client.post_note(openreview.Note(
            content={
                'title': 'Paper Matching Setup',
                'matching_group': 'TSACM/2024/Conference/Senior_Area_Chairs',
                'compute_conflicts': 'Default',
                'compute_affinity_scores': 'No',
                'upload_affinity_scores': affinity_scores_url

            },
            forum=request_form.id,
            replyto=request_form.id,
            invitation=f'openreview.net/Support/-/Request{request_form.number}/Paper_Matching_Setup',
            readers=['TSACM/2024/Conference/Program_Chairs', 'openreview.net/Support'],
            signatures=['~Program_MatchingChair1'],
            writers=[]
        ))

        helpers.await_queue()

        comment_invitation_id = f'openreview.net/Support/-/Request{request_form.number}/Paper_Matching_Setup_Status'
        matching_status = client.get_notes(invitation=comment_invitation_id, replyto=matching_setup_note.id, forum=request_form.forum, sort='tmdate')[0]
        assert matching_status
        assert matching_status.content['comment'] == '''Affinity scores and/or conflicts were successfully computed. To run the matcher, click on the 'Senior Area Chairs Paper Assignment' link in the PC console: https://openreview.net/group?id=TSACM/2024/Conference/Program_Chairs

Please refer to the documentation for instructions on how to run the matcher: https://docs.openreview.net/how-to-guides/paper-matching-and-assignment/how-to-do-automatic-assignments'''

        scores_invitation = openreview_client.get_invitation('TSACM/2024/Conference/Senior_Area_Chairs/-/Affinity_Score')
        assert scores_invitation
        affinity_scores = openreview_client.get_edges_count(invitation=scores_invitation.id)
        assert affinity_scores == 9

        conflict_invitation = pc_client_v2.get_invitation('TSACM/2024/Conference/Senior_Area_Chairs/-/Conflict')
        assert conflict_invitation
        conflicts = pc_client_v2.get_edges_count(invitation=conflict_invitation.id)
        assert conflicts

        assignment_config_inv = pc_client_v2.get_invitation('TSACM/2024/Conference/Senior_Area_Chairs/-/Assignment_Configuration')
        assert assignment_config_inv
        assert 'scores_specification' in assignment_config_inv.edit['note']['content']
        assert 'TSACM/2024/Conference/Senior_Area_Chairs/-/Affinity_Score' in assignment_config_inv.edit['note']['content']['scores_specification']['value']['param']['default']
        assert assignment_config_inv.edit['note']['content']['paper_invitation']['value']['param']['regex'] == 'TSACM/2024/Conference/-/Submission.*'
        assert assignment_config_inv.edit['note']['content']['paper_invitation']['value']['param']['default'] == 'TSACM/2024/Conference/-/Submission&content.venueid=TSACM/2024/Conference/Submission'
        assert conflict_invitation.id in assignment_config_inv.edit['note']['content']['conflicts_invitation']['value']['param']['default']

        # enable bidding
        now = datetime.datetime.now()
        due_date = now + datetime.timedelta(days=1)
        bid_stage_note = pc_client.post_note(openreview.Note(
            content={
                'bid_start_date': now.strftime('%Y/%m/%d'),
                'bid_due_date': due_date.strftime('%Y/%m/%d'),
                'bid_count': 5,
                'sac_bidding': 'Yes'
            },
            forum=request_form.forum,
            replyto=request_form.forum,
            referent=request_form.forum,
            invitation=f'openreview.net/Support/-/Request{request_form.number}/Bid_Stage',
            readers=['TSACM/2024/Conference/Program_Chairs', 'openreview.net/Support'],
            signatures=['~Program_MatchingChair1'],
            writers=[]
        ))

        helpers.await_queue()

        invitation = openreview_client.get_invitation('TSACM/2024/Conference/Senior_Area_Chairs/-/Bid')
        assert invitation.edit['tail']['param']['options']['group'] == 'TSACM/2024/Conference/Senior_Area_Chairs'
        assert invitation.edit['head']['param']['type'] == 'note'
        assert invitation.edit['head']['param']['withInvitation'] == 'TSACM/2024/Conference/-/Submission'
        invitation = openreview_client.get_invitation('TSACM/2024/Conference/Area_Chairs/-/Bid')
        assert invitation.edit['tail']['param']['options']['group'] == 'TSACM/2024/Conference/Area_Chairs'
        invitation = openreview_client.get_invitation('TSACM/2024/Conference/Reviewers/-/Bid')
        assert invitation.edit['tail']['param']['options']['group'] == 'TSACM/2024/Conference/Reviewers'

        # assert nothing changed in Assignment_Configuration, except bid invitation was added
        assignment_config_inv = pc_client_v2.get_invitation('TSACM/2024/Conference/Senior_Area_Chairs/-/Assignment_Configuration')
        assert assignment_config_inv
        assert 'scores_specification' in assignment_config_inv.edit['note']['content']
        assert 'TSACM/2024/Conference/Senior_Area_Chairs/-/Affinity_Score' in assignment_config_inv.edit['note']['content']['scores_specification']['value']['param']['default']
        assert 'TSACM/2024/Conference/Senior_Area_Chairs/-/Bid' in assignment_config_inv.edit['note']['content']['scores_specification']['value']['param']['default']
        assert assignment_config_inv.edit['note']['content']['paper_invitation']['value']['param']['default'] == 'TSACM/2024/Conference/-/Submission&content.venueid=TSACM/2024/Conference/Submission'
        assert conflict_invitation.id in assignment_config_inv.edit['note']['content']['conflicts_invitation']['value']['param']['default']

        sac1_client = openreview.api.OpenReviewClient(username='sac@umass.edu', password=helpers.strong_password)

        sac1_client.post_edge(openreview.api.Edge(invitation = venue.get_bid_id(venue.get_senior_area_chairs_id()),
            readers = [venue.id, '~SAC_MatchingOne1'],
            writers = [venue.id, '~SAC_MatchingOne1'],
            signatures = ['~SAC_MatchingOne1'],
            head = submissions[0].id,
            tail = '~SAC_MatchingOne1',
            label = 'High'
        ))
        sac1_client.post_edge(openreview.api.Edge(invitation = venue.get_bid_id(venue.get_senior_area_chairs_id()),
            readers = [venue.id, '~SAC_MatchingOne1'],
            writers = [venue.id, '~SAC_MatchingOne1'],
            signatures = ['~SAC_MatchingOne1'],
            head = submissions[2].id,
            tail = '~SAC_MatchingOne1',
            label = 'Low'
        ))

        bid_edges_count = openreview_client.get_edges_count(invitation='TSACM/2024/Conference/Senior_Area_Chairs/-/Bid')
        assert bid_edges_count == 2

    def test_set_assignments(self, client, openreview_client, helpers, selenium, request_page):
        
        pc_client = openreview.Client(username='pc@matching.org', password=helpers.strong_password)
        pc_client_v2=openreview.api.OpenReviewClient(username='pc@matching.org', password=helpers.strong_password)

        request_form=pc_client.get_notes(invitation='openreview.net/Support/-/Request_Form', sort='tmdate')[0]
        venue = openreview.helpers.get_conference(client, request_form.forum, 'openreview.net/Support', setup=False)

        submissions = venue.get_submissions(sort='number:asc')

        edges = pc_client_v2.get_edges_count(
            invitation='TSACM/2024/Conference/Senior_Area_Chairs/-/Proposed_Assignment',
            label='sac-matching'
        )
        assert 0 == edges

        #SAC-paper assignments
        pc_client_v2.post_edge(Edge(invitation = venue.get_assignment_id(venue.get_senior_area_chairs_id()),
            readers = ['TSACM/2024/Conference', '~SAC_MatchingOne1'],
            nonreaders = [f'TSACM/2024/Conference/Submission{submissions[0].number}/Authors'],
            writers = ['TSACM/2024/Conference'],
            signatures = ['TSACM/2024/Conference/Program_Chairs'],
            head = submissions[0].id,
            tail = '~SAC_MatchingOne1',
            label = 'sac-matching',
            weight = 0.75
        ))

        pc_client_v2.post_edge(Edge(invitation = venue.get_assignment_id(venue.get_senior_area_chairs_id()),
            readers = ['TSACM/2024/Conference', '~SAC_MatchingOne1'],
            nonreaders = [f'TSACM/2024/Conference/Submission{submissions[1].number}/Authors'],
            writers = ['TSACM/2024/Conference'],
            signatures = ['TSACM/2024/Conference/Program_Chairs'],
            head = submissions[1].id,
            tail = '~SAC_MatchingOne1',
            label = 'sac-matching',
            weight = 0.98
        ))

        pc_client_v2.post_edge(Edge(invitation = venue.get_assignment_id(venue.get_senior_area_chairs_id()),
            readers = ['TSACM/2024/Conference', '~SAC_MatchingTwo1'],
            nonreaders = [f'TSACM/2024/Conference/Submission{submissions[2].number}/Authors'],
            writers = ['TSACM/2024/Conference'],
            signatures = ['TSACM/2024/Conference/Program_Chairs'],
            head = submissions[2].id,
            tail = '~SAC_MatchingTwo1',
            label = 'sac-matching',
            weight = 0.88
        ))

        edges = pc_client_v2.get_edges_count(
            invitation='TSACM/2024/Conference/Senior_Area_Chairs/-/Proposed_Assignment',
            label='sac-matching'
        )
        assert 3 == edges

        venue.set_assignments(assignment_title='sac-matching', committee_id=venue.get_senior_area_chairs_id())

        assignment_invitation = pc_client_v2.get_invitation('TSACM/2024/Conference/Senior_Area_Chairs/-/Assignment')
        assert assignment_invitation
        assert 'sync_sac_id' not in assignment_invitation.content

        edges = pc_client_v2.get_edges_count(
            invitation='TSACM/2024/Conference/Senior_Area_Chairs/-/Assignment'
        )
        assert 3 == edges

        sac_paper1 = pc_client_v2.get_group('TSACM/2024/Conference/Submission1/Senior_Area_Chairs')
        assert ['~SAC_MatchingOne1'] == sac_paper1.members

        sac_paper2 = pc_client_v2.get_group('TSACM/2024/Conference/Submission2/Senior_Area_Chairs')
        assert ['~SAC_MatchingOne1'] == sac_paper2.members

        sac_paper3 = pc_client_v2.get_group('TSACM/2024/Conference/Submission3/Senior_Area_Chairs')
        assert ['~SAC_MatchingTwo1'] == sac_paper3.members

        #create new proposed assignments and deploy, overwriting previous assignments
        pc_client_v2.post_edge(Edge(invitation = venue.get_assignment_id(venue.get_senior_area_chairs_id()),
            readers = ['TSACM/2024/Conference', '~SAC_MatchingTwo1'],
            nonreaders = [f'TSACM/2024/Conference/Submission{submissions[0].number}/Authors'],
            writers = ['TSACM/2024/Conference'],
            signatures = ['TSACM/2024/Conference/Program_Chairs'],
            head = submissions[0].id,
            tail = '~SAC_MatchingTwo1',
            label = 'sac-matching-new',
            weight = 0.75
        ))

        pc_client_v2.post_edge(Edge(invitation = venue.get_assignment_id(venue.get_senior_area_chairs_id()),
            readers = ['TSACM/2024/Conference', '~SAC_MatchingTwo1'],
            nonreaders = [f'TSACM/2024/Conference/Submission{submissions[1].number}/Authors'],
            writers = ['TSACM/2024/Conference'],
            signatures = ['TSACM/2024/Conference/Program_Chairs'],
            head = submissions[1].id,
            tail = '~SAC_MatchingTwo1',
            label = 'sac-matching-new',
            weight = 0.98
        ))

        pc_client_v2.post_edge(Edge(invitation = venue.get_assignment_id(venue.get_senior_area_chairs_id()),
            readers = ['TSACM/2024/Conference', '~SAC_MatchingOne1'],
            nonreaders = [f'TSACM/2024/Conference/Submission{submissions[2].number}/Authors'],
            writers = ['TSACM/2024/Conference'],
            signatures = ['TSACM/2024/Conference/Program_Chairs'],
            head = submissions[2].id,
            tail = '~SAC_MatchingOne1',
            label = 'sac-matching-new',
            weight = 0.88
        ))

        edges = pc_client_v2.get_edges_count(
            invitation='TSACM/2024/Conference/Senior_Area_Chairs/-/Proposed_Assignment',
            label='sac-matching-new'
        )
        assert 3 == edges

        venue.set_assignments(assignment_title='sac-matching-new', committee_id=venue.get_senior_area_chairs_id(), overwrite=True)

        edges = pc_client_v2.get_edges_count(
            invitation='TSACM/2024/Conference/Senior_Area_Chairs/-/Assignment'
        )
        assert 3 == edges

        sac_paper1 = pc_client_v2.get_group('TSACM/2024/Conference/Submission1/Senior_Area_Chairs')
        assert ['~SAC_MatchingTwo1'] == sac_paper1.members

        sac_paper2 = pc_client_v2.get_group('TSACM/2024/Conference/Submission2/Senior_Area_Chairs')
        assert ['~SAC_MatchingTwo1'] == sac_paper2.members

        sac_paper3 = pc_client_v2.get_group('TSACM/2024/Conference/Submission3/Senior_Area_Chairs')
        assert ['~SAC_MatchingOne1'] == sac_paper3.members

        # change assigned SAC
        edge = pc_client_v2.get_edges(invitation='TSACM/2024/Conference/Senior_Area_Chairs/-/Assignment', head=submissions[0].id, tail='~SAC_MatchingTwo1')[0]
        assert edge
        edge.ddate = openreview.tools.datetime_millis(datetime.datetime.now())
        pc_client_v2.post_edge(edge)

        helpers.await_queue_edit(openreview_client, edge.id)

        sac_paper1 = pc_client_v2.get_group('TSACM/2024/Conference/Submission1/Senior_Area_Chairs')
        assert not sac_paper1.members

        edge = pc_client_v2.post_edge(Edge(invitation = venue.get_assignment_id(venue.get_senior_area_chairs_id(), deployed=True),
            readers = ['TSACM/2024/Conference', '~SAC_MatchingThree1'],
            nonreaders = [f'TSACM/2024/Conference/Submission{submissions[0].number}/Authors'],
            writers = ['TSACM/2024/Conference'],
            signatures = ['TSACM/2024/Conference/Program_Chairs'],
            head = submissions[0].id,
            tail = '~SAC_MatchingThree1',
            weight = 0.75
        ))

        helpers.await_queue_edit(openreview_client, edge.id)

        sac_paper1 = pc_client_v2.get_group('TSACM/2024/Conference/Submission1/Senior_Area_Chairs')
        assert ['~SAC_MatchingThree1'] ==  sac_paper1.members

        sac_client = openreview.api.OpenReviewClient(username = 'sac@umass.edu', password=helpers.strong_password)

        request_page(selenium, 'http://localhost:3030/group?id=TSACM/2024/Conference/Senior_Area_Chairs', sac_client.token, by=By.CLASS_NAME, wait_for_element='tabs-container')
        tabs = selenium.find_element(By.CLASS_NAME, 'tabs-container')
        assert tabs
        assert tabs.find_element(By.LINK_TEXT, "Submission Status")
        assert tabs.find_element(By.LINK_TEXT, "Senior Area Chair Tasks")
        with pytest.raises(NoSuchElementException):
            tabs.find_element(By.LINK_TEXT, "Area Chair Status")