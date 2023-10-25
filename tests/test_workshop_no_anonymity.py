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
from selenium.webdriver.common.by import By

from openreview.venue import Venue
from openreview.stages import SubmissionStage, BidStage

class TestWorkshopV2():


    def test_create_conference(self, client, openreview_client, helpers):

        now = datetime.datetime.utcnow()
        due_date = now + datetime.timedelta(days=3)

        # Post the request form note
        helpers.create_user('pc@icaps.cc', 'Program', 'ICAPSChair')
        pc_client = openreview.Client(username='pc@icaps.cc', password=helpers.strong_password)

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
                'Abbreviated Venue Name': 'PRL ICAPS 2024',
                'Official Website URL': 'https://prl-theworkshop.github.io/',
                'program_chair_emails': ['pc@icaps.cc'],
                'contact_email': 'pc@icaps.cc',
                'Area Chairs (Metareviewers)': 'No, our venue does not have Area Chairs',
                'senior_area_chairs': 'No, our venue does not have Senior Area Chairs',
                'Venue Start Date': '2023/07/01',
                'Submission Deadline': due_date.strftime('%Y/%m/%d'),
                'Location': 'Virtual',
                'submission_reviewer_assignment': 'Manual',
                'Author and Reviewer Anonymity': 'No anonymity',
                'reviewer_identity': ['Program Chairs'],
                'area_chair_identity': ['Program Chairs'],
                'senior_area_chair_identity': ['Program Chairs'],
                'Open Reviewing Policy': 'Submissions and reviews should both be private.',
                'submission_readers': 'Program chairs and paper authors only',
                'How did you hear about us?': 'ML conferences',
                'Expected Submissions': '100',
                'use_recruitment_template': 'Yes',
                'api_version': '2',
                'withdrawn_submissions_author_anonymity': 'Yes, author identities of withdrawn submissions should be revealed.',
                'desk_rejected_submissions_author_anonymity': 'Yes, author identities of desk rejected submissions should be revealed.',
                'email_pcs_for_withdrawn_submissions': 'No, do not email PCs.',
                'withdrawn_submissions_visibility': 'No, withdrawn submissions should not be made public.',
                'desk_rejected_submissions_visibility': 'No, desk rejected submissions should not be made public.'               
            }))

        helpers.await_queue()

        # Post a deploy note
        client.post_note(openreview.Note(
            content={'venue_id': 'PRL/2024/ICAPS'},
            forum=request_form_note.forum,
            invitation='openreview.net/Support/-/Request{}/Deploy'.format(request_form_note.number),
            readers=['openreview.net/Support'],
            referent=request_form_note.forum,
            replyto=request_form_note.forum,
            signatures=['openreview.net/Support'],
            writers=['openreview.net/Support']
        ))

        helpers.await_queue()

        assert openreview_client.get_group('PRL/2024/ICAPS')
        assert openreview_client.get_group('PRL/2024/ICAPS/Program_Chairs')
        
        with pytest.raises(openreview.OpenReviewException, match=r'Group Not Found: PRL/2024/ICAPS/Senior_Area_Chairs'):
            assert openreview_client.get_group('PRL/2024/ICAPS/Senior_Area_Chairs')
        with pytest.raises(openreview.OpenReviewException, match=r'Group Not Found: PRL/2024/ICAPS/Area_Chairs'):
            assert openreview_client.get_group('PRL/2024/ICAPS/Area_Chairs')
        
        assert openreview_client.get_group('PRL/2024/ICAPS/Reviewers')
        assert openreview_client.get_group('PRL/2024/ICAPS/Authors')

        submission_invitation = openreview_client.get_invitation('PRL/2024/ICAPS/-/Submission')
        assert submission_invitation
        assert submission_invitation.duedate

        # assert openreview_client.get_invitation('PRL/2024/ICAPS/Reviewers/-/Expertise_Selection')
        with pytest.raises(openreview.OpenReviewException, match=r'The Invitation PRL/2024/ICAPS/Area_Chairs/-/Expertise_Selection was not found'):
            assert openreview_client.get_invitation('PRL/2024/ICAPS/Area_Chairs/-/Expertise_Selection')
        with pytest.raises(openreview.OpenReviewException, match=r'The Invitation PRL/2024/ICAPS/Senior_Area_Chairs/-/Expertise_Selection was not found'):
            assert openreview_client.get_invitation('PRL/2024/ICAPS/Senior_Area_Chairs/-/Expertise_Selection')

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
            
            test_client.post_note_edit(invitation='PRL/2024/ICAPS/-/Submission',
                signatures=['~SomeFirstName_User1'],
                note=note)

        helpers.await_queue_edit(openreview_client, invitation='PRL/2024/ICAPS/-/Submission', count=11)

        submissions = openreview_client.get_notes(invitation='PRL/2024/ICAPS/-/Submission', sort='number:asc')
        assert len(submissions) == 11
        assert ['PRL/2024/ICAPS', '~SomeFirstName_User1', 'peter@mail.com', 'andrew@amazon.com'] == submissions[0].readers
        assert ['~SomeFirstName_User1', 'peter@mail.com', 'andrew@amazon.com'] == submissions[0].content['authorids']['value']

        authors_group = openreview_client.get_group(id='PRL/2024/ICAPS/Authors')

        for i in range(1,12):
            assert f'PRL/2024/ICAPS/Submission{i}/Authors' in authors_group.members

    def test_setup_matching(self, client, openreview_client, helpers):

        pc_client=openreview.Client(username='pc@icaps.cc', password=helpers.strong_password)
        pc_client_v2=openreview.api.OpenReviewClient(username='pc@icaps.cc', password=helpers.strong_password)
        request_form=pc_client.get_notes(invitation='openreview.net/Support/-/Request_Form')[0]

        submissions = pc_client_v2.get_notes(invitation='PRL/2024/ICAPS/-/Submission', sort='number:asc')
        pc_client_v2.add_members_to_group('PRL/2024/ICAPS/Reviewers', ['reviewer1@icaps.cc', 'reviewer2@icaps.cc', 'reviewer3@icaps.cc', 'reviewer4@icaps.cc', 'reviewer5@icaps.cc', 'reviewer6@icaps.cc'])

        openreview.tools.replace_members_with_ids(openreview_client, openreview_client.get_group('PRL/2024/ICAPS/Reviewers'))
        
        with open(os.path.join(os.path.dirname(__file__), 'data/rev_scores_venue.csv'), 'w') as file_handle:
            writer = csv.writer(file_handle)
            for submission in submissions:
                for ac in openreview_client.get_group('PRL/2024/ICAPS/Reviewers').members:
                    writer.writerow([submission.id, ac, round(random.random(), 2)])

        affinity_scores_url = client.put_attachment(os.path.join(os.path.dirname(__file__), 'data/rev_scores_venue.csv'), f'openreview.net/Support/-/Request{request_form.number}/Paper_Matching_Setup', 'upload_affinity_scores')

        ## setup matching data before starting bidding
        client.post_note(openreview.Note(
            content={
                'title': 'Paper Matching Setup',
                'matching_group': 'PRL/2024/ICAPS/Reviewers',
                'compute_conflicts': 'Default',
                'compute_affinity_scores': 'No',
                'upload_affinity_scores': affinity_scores_url

            },
            forum=request_form.id,
            replyto=request_form.id,
            invitation=f'openreview.net/Support/-/Request{request_form.number}/Paper_Matching_Setup',
            readers=['PRL/2024/ICAPS/Program_Chairs', 'openreview.net/Support'],
            signatures=['~Program_ICAPSChair1'],
            writers=[]
        ))
        helpers.await_queue()

        assert pc_client_v2.get_edges_count(invitation='PRL/2024/ICAPS/Reviewers/-/Affinity_Score') == 66

        with pytest.raises(openreview.OpenReviewException, match=r'The Invitation PRL/2024/ICAPS/Reviewers/-/Proposed_Assignment was not found'):
            assert openreview_client.get_invitation('PRL/2024/ICAPS/Reviewers/-/Proposed_Assignment')

        with pytest.raises(openreview.OpenReviewException, match=r'The Invitation PRL/2024/ICAPS/Reviewers/-/Aggregate_Score was not found'):
            assert openreview_client.get_invitation('PRL/2024/ICAPS/Reviewers/-/Aggregate_Score')

        assert openreview_client.get_invitation('PRL/2024/ICAPS/Reviewers/-/Assignment')                    
        assert openreview_client.get_invitation('PRL/2024/ICAPS/Reviewers/-/Custom_Max_Papers')                    
        assert openreview_client.get_invitation('PRL/2024/ICAPS/Reviewers/-/Custom_User_Demands')

        ## try to make an assignment and get an error because the submission deadline has not passed
        with pytest.raises(openreview.OpenReviewException, match=r'Can not make assignment, submission Reviewers group not found.'):
            edge = pc_client_v2.post_edge(openreview.api.Edge(
                invitation='PRL/2024/ICAPS/Reviewers/-/Assignment',
                head=submissions[0].id,
                tail='~Reviewer_ICAPSOne1',
                weight=1,
                signatures=['PRL/2024/ICAPS/Program_Chairs']
            ))

        ## close the submission
        now = datetime.datetime.utcnow()
        due_date = now - datetime.timedelta(hours=1)        
        pc_client.post_note(openreview.Note(
            content={
                'title': 'PRL Workshop Series Bridging the Gap Between AI Planning and Reinforcement Learning',
                'Official Venue Name': 'PRL Workshop Series Bridging the Gap Between AI Planning and Reinforcement Learning',
                'Abbreviated Venue Name': 'PRL ICAPS 2024',
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
            readers=['PRL/2024/ICAPS/Program_Chairs', 'openreview.net/Support'],
            referent=request_form.forum,
            replyto=request_form.forum,
            signatures=['~Program_ICAPSChair1'],
            writers=[]
        ))

        helpers.await_queue()

        edge = pc_client_v2.post_edge(openreview.api.Edge(
            invitation='PRL/2024/ICAPS/Reviewers/-/Assignment',
            head=submissions[0].id,
            tail='~Reviewer_ICAPSOne1',
            weight=1,
            signatures=['PRL/2024/ICAPS/Program_Chairs']
        ))

        helpers.await_queue_edit(openreview_client, edit_id=edge.id)

        assert openreview_client.get_group('PRL/2024/ICAPS/Submission1/Reviewers').members == ['~Reviewer_ICAPSOne1']


    def test_review_stage(self, client, openreview_client, helpers):

        pc_client=openreview.Client(username='pc@icaps.cc', password=helpers.strong_password)
        request_form=pc_client.get_notes(invitation='openreview.net/Support/-/Request_Form')[0]

        ## Show the pdf and supplementary material to assigned reviewers
        pc_client.post_note(openreview.Note(
            content= {
                'force': 'Yes',
                'submission_readers': 'Assigned program committee (assigned reviewers, assigned area chairs, assigned senior area chairs if applicable)'
            },
            forum= request_form.id,
            invitation= f'openreview.net/Support/-/Request{request_form.number}/Post_Submission',
            readers= ['PRL/2024/ICAPS/Program_Chairs', 'openreview.net/Support'],
            referent= request_form.id,
            replyto= request_form.id,
            signatures= ['~Program_ICAPSChair1'],
            writers= [],
        ))

        helpers.await_queue()

        now = datetime.datetime.utcnow()
        due_date = now + datetime.timedelta(days=3)

        pc_client.post_note(openreview.Note(
            content={
                'review_deadline': due_date.strftime('%Y/%m/%d'),
                'make_reviews_public': 'No, reviews should NOT be revealed publicly when they are posted',
                'release_reviews_to_authors': 'No, reviews should NOT be revealed when they are posted to the paper\'s authors',
                'release_reviews_to_reviewers': 'Review should not be revealed to any reviewer, except to the author of the review',
                'email_program_chairs_about_reviews': 'No, do not email program chairs about received reviews',
            },
            forum=request_form.forum,
            invitation='openreview.net/Support/-/Request{}/Review_Stage'.format(request_form.number),
            readers=['PRL/2024/ICAPS/Program_Chairs', 'openreview.net/Support'],
            referent=request_form.forum,
            replyto=request_form.forum,
            signatures=['~Program_ICAPSChair1'],
            writers=[]
        ))

        helpers.await_queue()

        invitation = openreview_client.get_invitation('PRL/2024/ICAPS/Submission1/-/Official_Review')
        assert invitation.edit['signatures']['param']['items'] == [
            {
            "prefix": "~.*",
            "optional": True
            }
        ]