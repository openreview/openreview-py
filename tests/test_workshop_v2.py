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
                'publication_chairs':'No, our venue does not have Publication Chairs',
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
                'publication_chairs':'No, our venue does not have Publication Chairs',
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

        assert openreview_client.get_group('PRL/2023/ICAPS/Submission1/Reviewers').members == ['~Reviewer_ICAPSOne1']

    def test_publication_chair(self, client, openreview_client, helpers):

        pc_client=openreview.Client(username='pc@icaps.cc', password=helpers.strong_password)
        pc_client_v2=openreview.api.OpenReviewClient(username='pc@icaps.cc', password=helpers.strong_password)
        request_form=pc_client.get_notes(invitation='openreview.net/Support/-/Request_Form')[0]

        # Post a decision stage note
        now = datetime.datetime.utcnow()
        start_date = now - datetime.timedelta(days=2)
        due_date = now + datetime.timedelta(days=3)

        decision_stage_note = pc_client.post_note(openreview.Note(
            content={
                'decision_start_date': start_date.strftime('%Y/%m/%d'),
                'decision_deadline': due_date.strftime('%Y/%m/%d'),
                'decision_options': 'Accept, Reject',
                'make_decisions_public': 'No, decisions should NOT be revealed publicly when they are posted',
                'release_decisions_to_authors': 'Yes, decisions should be revealed when they are posted to the paper\'s authors',
                'release_decisions_to_reviewers': 'No, decisions should not be immediately revealed to the paper\'s reviewers',
                'release_decisions_to_area_chairs': 'No, decisions should not be immediately revealed to the paper\'s area chairs',
                'notify_authors': 'Yes, send an email notification to the authors'
            },
            forum=request_form.forum,
            invitation=f'openreview.net/Support/-/Request{request_form.number}/Decision_Stage',
            readers=['PRL/2023/ICAPS/Program_Chairs', 'openreview.net/Support'],
            referent=request_form.forum,
            replyto=request_form.forum,
            signatures=['~Program_ICAPSChair1'],
            writers=[]
        ))
        assert decision_stage_note
        helpers.await_queue()

        process_logs = client.get_process_logs(id = decision_stage_note.id)
        assert len(process_logs) == 1
        assert process_logs[0]['status'] == 'ok'    

        submissions = openreview_client.get_notes(invitation='PRL/2023/ICAPS/-/Submission', sort='number:asc')
        assert len(submissions) == 11

        decisions = ['Accept', 'Reject']
        for idx in range(len(submissions)):
            decision = pc_client_v2.post_note_edit(
                invitation=f'PRL/2023/ICAPS/Submission{submissions[idx].number}/-/Decision',
                    signatures=['PRL/2023/ICAPS/Program_Chairs'],
                    note=openreview.api.Note(
                        content={
                            'decision': { 'value': decisions[idx%2] },
                            'comment': { 'value': 'Comment by PCs.' }
                        }
                    )
                )
            
            helpers.await_queue_edit(openreview_client, edit_id=decision['id'])

        invitation = client.get_invitation(f'openreview.net/Support/-/Request{request_form.number}/Post_Decision_Stage')
        invitation.cdate = openreview.tools.datetime_millis(datetime.datetime.utcnow())
        client.post_invitation(invitation)

        # add publication chairs
        pc_client.post_note(openreview.Note(
            content={
                'title': 'PRL Workshop Series Bridging the Gap Between AI Planning and Reinforcement Learning',
                'Official Venue Name': 'PRL Workshop Series Bridging the Gap Between AI Planning and Reinforcement Learning',
                'Abbreviated Venue Name': 'PRL ICAPS 2023',
                'Official Website URL': 'https://prl-theworkshop.github.io/',
                'program_chair_emails': ['pc@icaps.cc'],
                'publication_chairs': 'Yes, our venue has Publication Chairs',
                'publication_chairs_emails': ['publicationchair@mail.com', 'publicationchair2@mail.com'],
                'contact_email': 'pc@icaps.cc',
                'publication_chairs':'No, our venue does not have Publication Chairs',
                'Venue Start Date': '2023/07/01',
                'Submission Deadline': request_form.content['Submission Deadline'],
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

        group = openreview_client.get_group('PRL/2023/ICAPS/Publication_Chairs')
        assert group
        assert 'publicationchair@mail.com' in group.members
        assert 'publicationchair2@mail.com' in group.members
        submission_revision_inv = client.get_invitation(f'openreview.net/Support/-/Request{request_form.number}/Submission_Revision_Stage')
        assert 'PRL/2023/ICAPS/Publication_Chairs' in submission_revision_inv.invitees

        #Post a post decision note, release accepted papers to publication chair
        now = datetime.datetime.utcnow()
        start_date = now - datetime.timedelta(days=2)
        due_date = now + datetime.timedelta(days=3)
        short_name = 'PRL ICAPS 2023'
        post_decision_stage_note = pc_client.post_note(openreview.Note(
            content={
                'reveal_authors': 'No, I don\'t want to reveal any author identities.',
                'submission_readers': 'All program committee (all reviewers, all area chairs, all senior area chairs if applicable)',
                'home_page_tab_names': {
                    'Accept': 'Accept',
                    'Reject': 'Submitted'
                },
                'send_decision_notifications': 'No, I will send the emails to the authors',
                'accept_email_content': f'''Dear {{{{fullname}}}},

Thank you for submitting your paper, {{{{submission_title}}}}, to {short_name}. We are delighted to inform you that your submission has been accepted. Congratulations!
You can find the final reviews for your paper on the submission page in OpenReview at: {{{{forum_url}}}}

Best,
{short_name} Program Chairs
''',
                'reject_email_content': f'''Dear {{{{fullname}}}},

Thank you for submitting your paper, {{{{submission_title}}}}, to {short_name}. We regret to inform you that your submission was not accepted.
You can find the final reviews for your paper on the submission page in OpenReview at: {{{{forum_url}}}}

Best,
{short_name} Program Chairs
'''
            },
            forum=request_form.forum,
            invitation=invitation.id,
            readers=['PRL/2023/ICAPS/Program_Chairs', 'openreview.net/Support'],
            replyto=request_form.forum,
            referent=request_form.forum,
            signatures=['~Program_ICAPSChair1'],
            writers=[]
        ))
        assert post_decision_stage_note
        helpers.await_queue()

        submissions = openreview_client.get_notes(invitation='PRL/2023/ICAPS/-/Submission', sort='number:asc')
        assert len(submissions) == 11

        for idx in range(len(submissions)):
            if idx % 2 == 0:
                submissions[idx].readers = [
                    'PRL/2023/ICAPS',
                    'PRL/2023/ICAPS/Reviewers',
                    'PRL/2023/ICAPS/Publication_Chairs',
                    f'PRL/2023/ICAPS/Submission{submissions[idx].number}/Authors'
                ]
                submissions[idx].content['authors']['readers'] = [
                    'PRL/2023/ICAPS',
                    f'PRL/2023/ICAPS/Submission{submissions[idx].number}/Authors',
                    'PRL/2023/ICAPS/Publication_Chairs'
                ]
            else:
                submissions[idx].readers = [
                    'PRL/2023/ICAPS',
                    'PRL/2023/ICAPS/Reviewers',
                    f'PRL/2023/ICAPS/Submission{submissions[idx].number}/Authors'
                ]
                submissions[idx].content['authors']['readers'] = [
                    'PRL/2023/ICAPS',
                    f'PRL/2023/ICAPS/Submission{submissions[idx].number}/Authors'
                ]
                
        helpers.create_user('publicationchair@mail.com', 'Publication', 'ICAPSChair')
        publication_chair_client_v2=openreview.api.OpenReviewClient(username='publicationchair@mail.com', password=helpers.strong_password)

        assert publication_chair_client_v2.get_group('PRL/2023/ICAPS/Authors/Accepted')
        submissions = publication_chair_client_v2.get_notes(invitation='PRL/2023/ICAPS/-/Submission', sort='number:asc')
        assert len(submissions) == 6

    def test_enable_camera_ready_revisions(self, client, openreview_client, helpers, selenium, request_page):

        publication_chair_client = openreview.Client(username='publicationchair@mail.com', password=helpers.strong_password)
        request_form=publication_chair_client.get_notes(invitation='openreview.net/Support/-/Request_Form')[0]

        now = datetime.datetime.utcnow()
        due_date = now + datetime.timedelta(days=3)

        # post submission revision stage note
        revision_stage_note = publication_chair_client.post_note(openreview.Note(
            content={
                'submission_revision_name': 'Camera_Ready_Revision',
                'submission_revision_deadline': due_date.strftime('%Y/%m/%d'),
                'accepted_submissions_only': 'Enable revision for accepted submissions only',
                'submission_author_edition': 'Allow addition and removal of authors',
                'submission_revision_additional_options': {
                    "supplementary_materials": {
                        "value": {
                            "param": {
                                "type": "file",
                                "extensions": [
                                    "zip",
                                    "pdf",
                                    "tgz",
                                    "gz"
                                ],
                                "maxSize": 100
                            }
                        },
                        "description": "All supplementary material must be self-contained and zipped into a single file. Note that supplementary material will be visible to reviewers and the public throughout and after the review period, and ensure all material is anonymized. The maximum file size is 100MB.",
                        "order": 1
                    },
                },
                'submission_revision_remove_options': ['title', 'authors', 'authorids', 'abstract', 'pdf', 'keywords']
            },
            forum=request_form.forum,
            invitation='openreview.net/Support/-/Request{}/Submission_Revision_Stage'.format(request_form.number),
            readers=['{}/Program_Chairs'.format('PRL/2023/ICAPS'), 'openreview.net/Support', '{}/Publication_Chairs'.format('PRL/2023/ICAPS')],
            referent=request_form.forum,
            replyto=request_form.forum,
            signatures=['~Publication_ICAPSChair1'],
            writers=[]
        ))
        assert revision_stage_note
        helpers.await_queue()

        process_logs = client.get_process_logs(id = revision_stage_note.id)
        assert len(process_logs) == 1
        assert process_logs[0]['status'] == 'ok'

        invitations = openreview_client.get_invitations(invitation='PRL/2023/ICAPS/-/Camera_Ready_Revision')
        assert len(invitations) == 6

        request_page(selenium, 'http://localhost:3030/group?id=PRL/2023/ICAPS/Publication_Chairs', publication_chair_client.token, wait_for_element='header')
        notes_panel = selenium.find_element(By.ID, 'notes')
        assert notes_panel
        tabs = notes_panel.find_element(By.CLASS_NAME, 'tabs-container')
        assert tabs
        assert tabs.find_element(By.LINK_TEXT, "Accepted Submissions")