from __future__ import absolute_import, division, print_function, unicode_literals
import openreview
import pytest
import datetime
import time
import os
import re
import random
import csv
from openreview.api import OpenReviewClient
from openreview.api import Note
from openreview.api import Group
from openreview.api import Invitation
from openreview.api import Edge

from openreview.venue import Venue
from openreview.stages import SubmissionStage, BidStage

class TestWorkshopV2():


    def test_create_conference(self, client, openreview_client, helpers):

        now = datetime.datetime.utcnow()
        due_date = now + datetime.timedelta(days=3)

        # Post the request form note
        pc_client=helpers.create_user('pc@icaps.cc', 'Program', 'ICAPSChair')

        helpers.create_user('reviewer1@icaps.cc', 'Reviewer', 'ICAPSOne')
        helpers.create_user('reviewer2@icaps.cc', 'Reviewer', 'ICAPSTwo')
        helpers.create_user('reviewer3@icaps.cc', 'Reviewer', 'ICAPSThree')
        helpers.create_user('reviewer4@icaps.cc', 'Reviewer', 'ICAPSFour')
        helpers.create_user('reviewer5@icaps.cc', 'Reviewer', 'ICAPSFive')
        helpers.create_user('reviewer6@icaps.cc', 'Reviewer', 'ICAPSSix')

        request_form_note = pc_client.post_note(openreview.Note(
            invitation='openreview.net/Support/-/Request_Form',
            signatures=['~Program_ICAPSChair1'],
            readers=[
                'openreview.net/Support',
                '~Program_ICAPSChair1'
            ],
            writers=[],
            content={
                'title': 'PRL Workshop Series Bridging the Gap Between AI Planning and Reinforcement Learning',
                'Official Venue Name': 'PRL Workshop Series Bridging the Gap Between AI Planning and Reinforcement Learning',
                'Abbreviated Venue Name': 'PRL ICAPS 2023',
                'Official Website URL': 'https://prl-theworkshop.github.io/',
                'program_chair_emails': ['pc@icaps.cc'],
                'contact_email': 'pc@icaps.cc',
                'Area Chairs (Metareviewers)': 'No, our venue does not have Area Chairs',
                'senior_area_chairs': 'No, our venue does not have Senior Area Chairs',
                'Venue Start Date': '2023/07/01',
                'Submission Deadline': due_date.strftime('%Y/%m/%d'),
                'Location': 'Virtual',
                'submission_reviewer_assignment': 'Manual',
                'Author and Reviewer Anonymity': 'Double-blind',
                'reviewer_identity': ['Program Chairs'],
                'area_chair_identity': ['Program Chairs'],
                'senior_area_chair_identity': ['Program Chairs'],
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
            content={'venue_id': 'PRL/2023/ICAPS'},
            forum=request_form_note.forum,
            invitation='openreview.net/Support/-/Request{}/Deploy'.format(request_form_note.number),
            readers=['openreview.net/Support'],
            referent=request_form_note.forum,
            replyto=request_form_note.forum,
            signatures=['openreview.net/Support'],
            writers=['openreview.net/Support']
        ))

        helpers.await_queue()

        assert openreview_client.get_group('PRL/2023/ICAPS')
        assert openreview_client.get_group('PRL/2023/ICAPS/Program_Chairs')
        
        with pytest.raises(openreview.OpenReviewException, match=r'Group Not Found: PRL/2023/ICAPS/Senior_Area_Chairs'):
            assert openreview_client.get_group('PRL/2023/ICAPS/Senior_Area_Chairs')
        with pytest.raises(openreview.OpenReviewException, match=r'Group Not Found: PRL/2023/ICAPS/Area_Chairs'):
            assert openreview_client.get_group('PRL/2023/ICAPS/Area_Chairs')
        
        assert openreview_client.get_group('PRL/2023/ICAPS/Reviewers')
        assert openreview_client.get_group('PRL/2023/ICAPS/Authors')

        submission_invitation = openreview_client.get_invitation('PRL/2023/ICAPS/-/Submission')
        assert submission_invitation
        assert submission_invitation.duedate

        # assert openreview_client.get_invitation('PRL/2023/ICAPS/Reviewers/-/Expertise_Selection')
        with pytest.raises(openreview.OpenReviewException, match=r'The Invitation PRL/2023/ICAPS/Area_Chairs/-/Expertise_Selection was not found'):
            assert openreview_client.get_invitation('PRL/2023/ICAPS/Area_Chairs/-/Expertise_Selection')
        with pytest.raises(openreview.OpenReviewException, match=r'The Invitation PRL/2023/ICAPS/Senior_Area_Chairs/-/Expertise_Selection was not found'):
            assert openreview_client.get_invitation('PRL/2023/ICAPS/Senior_Area_Chairs/-/Expertise_Selection')

    def test_submissions(self, client, openreview_client, helpers, test_client):

        test_client = openreview.api.OpenReviewClient(token=test_client.token)

        domains = ['umass.edu', 'amazon.com', 'fb.com', 'cs.umass.edu', 'google.com', 'mit.edu', 'deepmind.com', 'co.ux', 'apple.com', 'nvidia.com']
        for i in range(1,12):
            note = openreview.api.Note(
                content = {
                    'title': { 'value': 'Paper title ' + str(i) },
                    'abstract': { 'value': 'This is an abstract ' + str(i) },
                    'authorids': { 'value': ['~SomeFirstName_User1', 'peter@mail.com', 'andrew@' + domains[i % 10]] },
                    'authors': { 'value': ['SomeFirstName User', 'Peter SomeLastName', 'Andrew Mc'] },
                    'keywords': { 'value': ['machine learning', 'nlp'] },
                    'pdf': {'value': '/pdf/' + 'p' * 40 +'.pdf' },
                }
            )
            
            test_client.post_note_edit(invitation='PRL/2023/ICAPS/-/Submission',
                signatures=['~SomeFirstName_User1'],
                note=note)

        helpers.await_queue_edit(openreview_client, invitation='PRL/2023/ICAPS/-/Submission', count=11)

        submissions = openreview_client.get_notes(invitation='PRL/2023/ICAPS/-/Submission', sort='number:asc')
        assert len(submissions) == 11
        assert ['PRL/2023/ICAPS', '~SomeFirstName_User1', 'peter@mail.com', 'andrew@amazon.com'] == submissions[0].readers
        assert ['~SomeFirstName_User1', 'peter@mail.com', 'andrew@amazon.com'] == submissions[0].content['authorids']['value']

        authors_group = openreview_client.get_group(id='PRL/2023/ICAPS/Authors')

        for i in range(1,12):
            assert f'PRL/2023/ICAPS/Submission{i}/Authors' in authors_group.members

    def test_setup_matching(self, client, openreview_client, helpers):

        pc_client=openreview.Client(username='pc@icaps.cc', password=helpers.strong_password)
        pc_client_v2=openreview.api.OpenReviewClient(username='pc@icaps.cc', password=helpers.strong_password)
        request_form=pc_client.get_notes(invitation='openreview.net/Support/-/Request_Form')[0]

        submissions = pc_client_v2.get_notes(invitation='PRL/2023/ICAPS/-/Submission', sort='number:asc')
        pc_client_v2.add_members_to_group('PRL/2023/ICAPS/Reviewers', ['reviewer1@icaps.cc', 'reviewer2@icaps.cc', 'reviewer3@icaps.cc', 'reviewer4@icaps.cc', 'reviewer5@icaps.cc', 'reviewer6@icaps.cc'])

        openreview.tools.replace_members_with_ids(openreview_client, openreview_client.get_group('PRL/2023/ICAPS/Reviewers'))
        
        with open(os.path.join(os.path.dirname(__file__), 'data/rev_scores_venue.csv'), 'w') as file_handle:
            writer = csv.writer(file_handle)
            for submission in submissions:
                for ac in openreview_client.get_group('PRL/2023/ICAPS/Reviewers').members:
                    writer.writerow([submission.id, ac, round(random.random(), 2)])

        affinity_scores_url = client.put_attachment(os.path.join(os.path.dirname(__file__), 'data/rev_scores_venue.csv'), f'openreview.net/Support/-/Request{request_form.number}/Paper_Matching_Setup', 'upload_affinity_scores')

        ## setup matching data before starting bidding
        client.post_note(openreview.Note(
            content={
                'title': 'Paper Matching Setup',
                'matching_group': 'PRL/2023/ICAPS/Reviewers',
                'compute_conflicts': 'Default',
                'compute_affinity_scores': 'No',
                'upload_affinity_scores': affinity_scores_url

            },
            forum=request_form.id,
            replyto=request_form.id,
            invitation=f'openreview.net/Support/-/Request{request_form.number}/Paper_Matching_Setup',
            readers=['PRL/2023/ICAPS/Program_Chairs', 'openreview.net/Support'],
            signatures=['~Program_ICAPSChair1'],
            writers=[]
        ))
        helpers.await_queue()

        assert pc_client_v2.get_edges_count(invitation='PRL/2023/ICAPS/Reviewers/-/Affinity_Score') == 66

        with pytest.raises(openreview.OpenReviewException, match=r'The Invitation PRL/2023/ICAPS/Reviewers/-/Proposed_Assignment was not found'):
            assert openreview_client.get_invitation('PRL/2023/ICAPS/Reviewers/-/Proposed_Assignment')

        with pytest.raises(openreview.OpenReviewException, match=r'The Invitation PRL/2023/ICAPS/Reviewers/-/Aggregate_Score was not found'):
            assert openreview_client.get_invitation('PRL/2023/ICAPS/Reviewers/-/Aggregate_Score')

        assert openreview_client.get_invitation('PRL/2023/ICAPS/Reviewers/-/Assignment')                    
        assert openreview_client.get_invitation('PRL/2023/ICAPS/Reviewers/-/Custom_Max_Papers')                    
        assert openreview_client.get_invitation('PRL/2023/ICAPS/Reviewers/-/Custom_User_Demands')

        ## try to make an assignment and get an error because the submission deadline has not passed
        with pytest.raises(openreview.OpenReviewException, match=r'Can not make assignment, submission Reviewers group not found.'):
            edge = pc_client_v2.post_edge(openreview.api.Edge(
                invitation='PRL/2023/ICAPS/Reviewers/-/Assignment',
                head=submissions[0].id,
                tail='~Reviewer_ICAPSOne1',
                weight=1,
                signatures=['PRL/2023/ICAPS/Program_Chairs']
            ))

        ## close the submission
        now = datetime.datetime.utcnow()
        due_date = now - datetime.timedelta(hours=1)        
        pc_client.post_note(openreview.Note(
            content={
                'title': 'PRL Workshop Series Bridging the Gap Between AI Planning and Reinforcement Learning',
                'Official Venue Name': 'PRL Workshop Series Bridging the Gap Between AI Planning and Reinforcement Learning',
                'Abbreviated Venue Name': 'PRL ICAPS 2023',
                'Official Website URL': 'https://prl-theworkshop.github.io/',
                'program_chair_emails': ['pc@icaps.cc'],
                'contact_email': 'pc@icaps.cc',
                'Venue Start Date': '2023/07/01',
                'Submission Deadline': due_date.strftime('%Y/%m/%d %H:%M'),
                'Location': 'Virtual',
                'submission_reviewer_assignment': 'Manual',
                'How did you hear about us?': 'ML conferences',
                'Expected Submissions': '100',
                'use_recruitment_template': 'Yes'

            },
            forum=request_form.forum,
            invitation='openreview.net/Support/-/Request{}/Revision'.format(request_form.number),
            readers=['PRL/2023/ICAPS/Program_Chairs', 'openreview.net/Support'],
            referent=request_form.forum,
            replyto=request_form.forum,
            signatures=['~Program_ICAPSChair1'],
            writers=[]
        ))

        helpers.await_queue()

        edge = pc_client_v2.post_edge(openreview.api.Edge(
            invitation='PRL/2023/ICAPS/Reviewers/-/Assignment',
            head=submissions[0].id,
            tail='~Reviewer_ICAPSOne1',
            weight=1,
            signatures=['PRL/2023/ICAPS/Program_Chairs']
        ))

        helpers.await_queue_edit(openreview_client, edit_id=edge.id)

        assert client.get_group('PRL/2023/ICAPS/Submission1/Reviewers').members == ['~Reviewer_ICAPSOne1']                  

