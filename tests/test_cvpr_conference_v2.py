import openreview
import pytest
import datetime
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from openreview import ProfileManagement
import csv
import os
import random

class TestCVPRConference():

    def test_create_conference(self, client, openreview_client, helpers):

        now = datetime.datetime.utcnow()
        abstract_date = now + datetime.timedelta(days=1)
        due_date = now + datetime.timedelta(days=3)

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
                'title': 'Conference on Computer Vision and Pattern Recognition 2024',
                'Official Venue Name': 'Conference on Computer Vision and Pattern Recognition 2024',
                'Abbreviated Venue Name': 'CVPR 2024',
                'Official Website URL': 'https://cvpr.cc',
                'program_chair_emails': ['pc@cvpr.cc'],
                'contact_email': 'pc@cvpr.cc',
                'publication_chairs':'No, our venue does not have Publication Chairs',
                'Area Chairs (Metareviewers)': 'Yes, our venue has Area Chairs',
                'senior_area_chairs': 'Yes, our venue has Senior Area Chairs',
                'secondary_area_chairs': 'Yes, our venue has Secondary Area Chairs',
                'Venue Start Date': '2024/12/01',
                'Submission Deadline': due_date.strftime('%Y/%m/%d'),
                'abstract_registration_deadline': abstract_date.strftime('%Y/%m/%d'),
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
                'submission_deadline_author_reorder': 'Yes',
                'api_version': '2',
                'submission_license': 'CC BY-SA 4.0'
            }
        ))

        helpers.await_queue()

        # Post a deploy note
        client.post_note(openreview.Note(
            content={'venue_id': 'thecvf.com/CVPR/2024/Conference'},
            forum=request_form_note.forum,
            invitation='openreview.net/Support/-/Request{}/Deploy'.format(request_form_note.number),
            readers=['openreview.net/Support'],
            referent=request_form_note.forum,
            replyto=request_form_note.forum,
            signatures=['openreview.net/Support'],
            writers=['openreview.net/Support']
        ))

        helpers.await_queue()

        venue_group = openreview_client.get_group('thecvf.com/CVPR/2024/Conference')
        assert venue_group
        assert venue_group.content['date']['value'] == f'Abstract Registration: {abstract_date.strftime("%b %d %Y")} 12:00AM UTC-0, Submission Deadline: {due_date.strftime("%b %d %Y")} 12:00AM UTC-0'
        assert openreview_client.get_group('thecvf.com/CVPR/2024/Conference/Senior_Area_Chairs')
        assert openreview_client.get_group('thecvf.com/CVPR/2024/Conference/Area_Chairs')
        assert openreview_client.get_group('thecvf.com/CVPR/2024/Conference/Reviewers')
        assert openreview_client.get_group('thecvf.com/CVPR/2024/Conference/Authors')

        submission_invitation = openreview_client.get_invitation('thecvf.com/CVPR/2024/Conference/-/Submission')
        assert submission_invitation
        assert submission_invitation.duedate

        assert openreview_client.get_invitation('thecvf.com/CVPR/2024/Conference/Reviewers/-/Expertise_Selection')
        assert openreview_client.get_invitation('thecvf.com/CVPR/2024/Conference/Area_Chairs/-/Expertise_Selection')
        assert openreview_client.get_invitation('thecvf.com/CVPR/2024/Conference/Senior_Area_Chairs/-/Expertise_Selection')

    def test_submissions(self, client, openreview_client, helpers, test_client):

        test_client = openreview.api.OpenReviewClient(token=test_client.token)

        domains = ['umass.edu', 'amazon.com', 'fb.com', 'cs.umass.edu', 'google.com', 'mit.edu', 'deepmind.com', 'co.ux', 'apple.com', 'nvidia.com']
        for i in range(1,51):
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
            if i == 1 or i == 11:
                note.content['authors']['value'].append('SAC CVPROne')
                note.content['authorids']['value'].append('~SAC_CVPROne1')

            test_client.post_note_edit(invitation='thecvf.com/CVPR/2024/Conference/-/Submission',
                signatures=['~SomeFirstName_User1'],
                note=note)

        helpers.await_queue_edit(openreview_client, invitation='thecvf.com/CVPR/2024/Conference/-/Submission', count=50)

        submissions = openreview_client.get_notes(invitation='thecvf.com/CVPR/2024/Conference/-/Submission', sort='number:asc')
        assert len(submissions) == 50
        assert ['thecvf.com/CVPR/2024/Conference', '~SomeFirstName_User1', 'peter@mail.com', 'andrew@amazon.com', '~SAC_CVPROne1'] == submissions[0].readers
        assert ['~SomeFirstName_User1', 'peter@mail.com', 'andrew@amazon.com', '~SAC_CVPROne1'] == submissions[0].content['authorids']['value']

        # Check that submission license is same as request form
        assert submissions[0].license == 'CC BY-SA 4.0'

        authors_group = openreview_client.get_group(id='thecvf.com/CVPR/2024/Conference/Authors')

        for i in range(1,51):
            assert f'thecvf.com/CVPR/2024/Conference/Submission{i}/Authors' in authors_group.members

        pc_client=openreview.Client(username='pc@cvpr.cc', password=helpers.strong_password)
        request_form=pc_client.get_notes(invitation='openreview.net/Support/-/Request_Form')[0]
        venue = openreview.get_conference(client, request_form.id, support_user='openreview.net/Support')

        ## close the submissions
        now = datetime.datetime.utcnow()
        due_date = now - datetime.timedelta(days=1)
        abstract_date = now - datetime.timedelta(minutes=28)
        pc_client.post_note(openreview.Note(
            content={
                'title': 'Conference on Computer Vision and Pattern Recognition 2024',
                'Official Venue Name': 'Conference on Computer Vision and Pattern Recognition 2024',
                'Abbreviated Venue Name': 'CVPR 2024',
                'Official Website URL': 'https://cvpr.cc',
                'program_chair_emails': ['pc@cvpr.cc'],
                'contact_email': 'pc@cvpr.cc',
                'publication_chairs':'No, our venue does not have Publication Chairs',
                'Venue Start Date': '2024/12/01',
                'abstract_registration_deadline': abstract_date.strftime('%Y/%m/%d'),
                'Submission Deadline': due_date.strftime('%Y/%m/%d'),
                'Location': 'Virtual',
                'submission_reviewer_assignment': 'Automatic',
                'How did you hear about us?': 'ML conferences',
                'Expected Submissions': '100',
            },
            forum=request_form.forum,
            invitation='openreview.net/Support/-/Request{}/Revision'.format(request_form.number),
            readers=['thecvf.com/CVPR/2024/Conference/Program_Chairs', 'openreview.net/Support'],
            referent=request_form.forum,
            replyto=request_form.forum,
            signatures=['~Program_CVPRChair1'],
            writers=[]
        ))

        helpers.await_queue()

        ## make submissions visible to ACs only
        pc_client.post_note(openreview.Note(
            content= {
                'force': 'Yes',
                'submission_readers': 'All area chairs only'
            },
            forum= request_form.id,
            invitation= f'openreview.net/Support/-/Request{request_form.number}/Post_Submission',
            readers= ['thecvf.com/CVPR/2024/Conference/Program_Chairs', 'openreview.net/Support'],
            referent= request_form.id,
            replyto= request_form.id,
            signatures= ['~Program_CVPRChair1'],
            writers= [],
        ))

        helpers.await_queue()

    def test_desk_rejection_emails(self, client, openreview_client, helpers, test_client):

        pc_client_v2=openreview.api.OpenReviewClient(username='pc@cvpr.cc', password=helpers.strong_password)

        desk_reject_note = pc_client_v2.post_note_edit(invitation='thecvf.com/CVPR/2024/Conference/Submission50/-/Desk_Rejection',
                                    signatures=['thecvf.com/CVPR/2024/Conference/Program_Chairs'],
                                    note=openreview.api.Note(
                                        content={
                                            'desk_reject_comments': { 'value': 'No PDF' },
                                        }
                                    ))

        helpers.await_queue_edit(openreview_client, edit_id=desk_reject_note['id'])
        helpers.await_queue_edit(openreview_client, invitation='thecvf.com/CVPR/2024/Conference/-/Desk_Rejected_Submission', count=1)

        messages = client.get_messages(subject='[CVPR 2024]: Paper #50 desk-rejected by Program Chairs')
        assert messages and len(messages) == 3
        recipients = [msg['content']['to'] for msg in messages]
        assert 'pc@cvpr.cc' not in recipients

    def test_reviewer_recommendation(self, client, openreview_client, helpers, test_client, request_page, selenium):

        pc_client=openreview.Client(username='pc@cvpr.cc', password=helpers.strong_password)
        pc_client_v2=openreview.api.OpenReviewClient(username='pc@cvpr.cc', password=helpers.strong_password)
        request_form=pc_client.get_notes(invitation='openreview.net/Support/-/Request_Form')[0]

        openreview_client.add_members_to_group('thecvf.com/CVPR/2024/Conference/Area_Chairs', members=['~AC_CVPROne1', '~AC_CVPRTwo1'])
        openreview_client.add_members_to_group('thecvf.com/CVPR/2024/Conference/Reviewers', members=['~Reviewer_CVPROne1', '~Reviewer_CVPRTwo1', '~Reviewer_CVPRThree1', '~Reviewer_CVPRFour1', '~Reviewer_CVPRFive1', '~Reviewer_CVPRSix1'])

        submissions = pc_client_v2.get_notes(invitation='thecvf.com/CVPR/2024/Conference/-/Submission', sort='number:asc')

        ## setup matching data
        client.post_note(openreview.Note(
            content={
                'title': 'Paper Matching Setup',
                'matching_group': 'thecvf.com/CVPR/2024/Conference/Area_Chairs',
                'compute_conflicts': 'NeurIPS',
                'compute_conflicts_N_years': '3',
                'compute_affinity_scores': 'No'
            },
            forum=request_form.id,
            replyto=request_form.id,
            invitation=f'openreview.net/Support/-/Request{request_form.number}/Paper_Matching_Setup',
            readers=['thecvf.com/CVPR/2024/Conference/Program_Chairs', 'openreview.net/Support'],
            signatures=['~Program_CVPRChair1'],
            writers=[]
        ))
        helpers.await_queue()

        openreview.tools.replace_members_with_ids(openreview_client, openreview_client.get_group('thecvf.com/CVPR/2024/Conference/Reviewers'))

        with open(os.path.join(os.path.dirname(__file__), 'data/rev_scores_venue.csv'), 'w') as file_handle:
            writer = csv.writer(file_handle)
            for submission in submissions:
                for ac in openreview_client.get_group('thecvf.com/CVPR/2024/Conference/Reviewers').members:
                    writer.writerow([submission.id, ac, round(random.random(), 2)])

        affinity_scores_url = client.put_attachment(os.path.join(os.path.dirname(__file__), 'data/rev_scores_venue.csv'), f'openreview.net/Support/-/Request{request_form.number}/Paper_Matching_Setup', 'upload_affinity_scores')

        client.post_note(openreview.Note(
            content={
                'title': 'Paper Matching Setup',
                'matching_group': 'thecvf.com/CVPR/2024/Conference/Reviewers',
                'compute_conflicts': 'NeurIPS',
                'compute_conflicts_N_years': '3',
                'compute_affinity_scores': 'No',
                'upload_affinity_scores': affinity_scores_url
            },
            forum=request_form.id,
            replyto=request_form.id,
            invitation=f'openreview.net/Support/-/Request{request_form.number}/Paper_Matching_Setup',
            readers=['thecvf.com/CVPR/2024/Conference/Program_Chairs', 'openreview.net/Support'],
            signatures=['~Program_CVPRChair1'],
            writers=[]
        ))
        helpers.await_queue()

        #assign ACs to papers
        acs = ['~AC_CVPROne1', '~AC_CVPRTwo1']
        for idx in range(0,49):
            edge = pc_client_v2.post_edge(openreview.api.Edge(
                invitation = 'thecvf.com/CVPR/2024/Conference/Area_Chairs/-/Proposed_Assignment',
                head = submissions[idx].id,
                tail = acs[idx % 2],
                signatures = ['thecvf.com/CVPR/2024/Conference/Program_Chairs'],
                weight = 1,
                label = 'ac-matching'
            ))

        venue = openreview.helpers.get_conference(pc_client, request_form.id, setup=False)
        venue.set_assignments(assignment_title='ac-matching', committee_id='thecvf.com/CVPR/2024/Conference/Area_Chairs')

        # open reviewer recommendation
        now = datetime.datetime.utcnow()
        venue.open_reviewer_recommendation_stage(
            due_date = now + datetime.timedelta(days=3),
            total_recommendations = 5
        )

        invitation = openreview_client.get_invitation('thecvf.com/CVPR/2024/Conference/Reviewers/-/Recommendation')
        assert invitation
        assert 'thecvf.com/CVPR/2024/Conference/Area_Chairs' in invitation.invitees

        ac_client = openreview.api.OpenReviewClient(username='ac1@cvpr.cc', password=helpers.strong_password)
        ac_client.post_edge(openreview.Edge(invitation = venue.get_recommendation_id(),
            readers = [venue.id, '~AC_CVPROne1', 'thecvf.com/CVPR/2024/Conference/Submission1/Senior_Area_Chairs'],
            writers = ['thecvf.com/CVPR/2024/Conference', '~AC_CVPROne1'],
            signatures = ['~AC_CVPROne1'],
            head = submissions[0].id,
            tail = '~Reviewer_CVPROne1',
            weight = 1))

        ## edit recommendation edge
        recommendation_edge = ac_client.get_edges(invitation=venue.get_recommendation_id(), tail='~Reviewer_CVPROne1')[0]
        assert recommendation_edge.nonreaders == ['thecvf.com/CVPR/2024/Conference/Submission1/Authors']
        recommendation_edge.weight = 5
        ac_client.post_edge(recommendation_edge)

        recommendation_edge = ac_client.get_edges(invitation=venue.get_recommendation_id(), tail='~Reviewer_CVPROne1')[0]
        assert recommendation_edge.weight == 5

        ## delete recommendation edge
        recommendation_edge.ddate = openreview.tools.datetime_millis(datetime.datetime.utcnow())
        ac_client.post_edge(recommendation_edge)
        assert not ac_client.get_edges(invitation=venue.get_recommendation_id(), tail='~Reviewer_CVPROne1')
        
        ## Go to edge browser to recommend reviewers
        start = 'thecvf.com/CVPR/2024/Conference/Area_Chairs/-/Assignment,tail:~AC_CVPROne1'
        edit = 'thecvf.com/CVPR/2024/Conference/Reviewers/-/Recommendation'
        browse = 'thecvf.com/CVPR/2024/Conference/Reviewers/-/Affinity_Score'
        hide = 'thecvf.com/CVPR/2024/Conference/Reviewers/-/Conflict'
        referrer = '[Recommendation%20Instructions](/invitation?id=thecvf.com/CVPR/2024/Conference/Reviewers/-/Recommendation)'

        url = f'http://localhost:3030/edges/browse?start={start}&traverse={edit}&edit={edit}&browse={browse}&hide={hide}&maxColumns=2&version=2&referrer={referrer}'

        request_page(selenium, 'http://localhost:3030/invitation?id=thecvf.com/CVPR/2024/Conference/Reviewers/-/Recommendation', ac_client.token, by=By.CLASS_NAME, wait_for_element='description')
        instructions = selenium.find_element(By.CLASS_NAME, 'description')
        assert instructions
        assert 'CVPR 2024 Reviewer Recommendation' in instructions.text
        recommendation_div =  selenium.find_element(By.ID, 'notes')
        button_row = recommendation_div.find_element(By.CLASS_NAME, 'text-center')
        assert button_row
        button = button_row.find_element(By.CLASS_NAME, 'btn-lg')
        assert button.text == 'Recommend Reviewers'
        links = recommendation_div.find_elements(By.TAG_NAME, 'a')
        assert links
        assert len(links) == 1
        assert url == links[0].get_attribute("href")

    