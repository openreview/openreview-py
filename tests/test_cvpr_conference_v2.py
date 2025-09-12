import openreview
import pytest
import datetime
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
import csv
import os
import random
import time

class TestCVPRConference():

    def test_create_conference(self, client, openreview_client, helpers):

        now = datetime.datetime.now()
        abstract_date = now + datetime.timedelta(days=1)
        due_date = now + datetime.timedelta(days=3)

        # Post the request form note
        helpers.create_user('pc@cvpr.cc', 'Program', 'CVPRChair')
        pc_client = openreview.Client(username='pc@cvpr.cc', password=helpers.strong_password)

        helpers.create_user('sac1@cvpr.cc', 'SAC', 'CVPROne')
        helpers.create_user('ac1@cvpr.cc', 'AC', 'CVPROne')
        helpers.create_user('ac2@cvpr.cc', 'AC', 'CVPRTwo')
        helpers.create_user('ac3@cvpr.cc', 'AC', 'CVPRThree')
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
                'senior_area_chairs_assignment': 'Area Chairs',
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
                'submission_license': ['CC BY-SA 4.0'],
                'venue_organizer_agreement': [
                    'OpenReview natively supports a wide variety of reviewing workflow configurations. However, if we want significant reviewing process customizations or experiments, we will detail these requests to the OpenReview staff at least three months in advance.',
                    'We will ask authors and reviewers to create an OpenReview Profile at least two weeks in advance of the paper submission deadlines.',
                    'When assembling our group of reviewers and meta-reviewers, we will only include email addresses or OpenReview Profile IDs of people we know to have authored publications relevant to our venue.  (We will not solicit new reviewers using an open web form, because unfortunately some malicious actors sometimes try to create "fake ids" aiming to be assigned to review their own paper submissions.)',
                    'We acknowledge that, if our venue\'s reviewing workflow is non-standard, or if our venue is expecting more than a few hundred submissions for any one deadline, we should designate our own Workflow Chair, who will read the OpenReview documentation and manage our workflow configurations throughout the reviewing process.',
                    'We acknowledge that OpenReview staff work Monday-Friday during standard business hours US Eastern time, and we cannot expect support responses outside those times.  For this reason, we recommend setting submission and reviewing deadlines Monday through Thursday.',
                    'We will treat the OpenReview staff with kindness and consideration.'
                ]
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

        # Check that submission note has license
        assert submissions[0].license == 'CC BY-SA 4.0'

        authors_group = openreview_client.get_group(id='thecvf.com/CVPR/2024/Conference/Authors')

        for i in range(1,51):
            assert f'thecvf.com/CVPR/2024/Conference/Submission{i}/Authors' in authors_group.members

        pc_client=openreview.Client(username='pc@cvpr.cc', password=helpers.strong_password)
        request_form=pc_client.get_notes(invitation='openreview.net/Support/-/Request_Form')[0]
        venue = openreview.get_conference(client, request_form.id, support_user='openreview.net/Support')

        ## close the submissions
        now = datetime.datetime.now()
        start_date = now - datetime.timedelta(days=10)
        due_date = now - datetime.timedelta(days=1)
        abstract_date = now - datetime.timedelta(days=2)
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
                'Submission Start Date': start_date.strftime('%Y/%m/%d'),
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

        helpers.await_queue_edit(openreview_client, edit_id='thecvf.com/CVPR/2024/Conference/Senior_Area_Chairs/-/Submission_Group-0-1', count=2)
        helpers.await_queue_edit(openreview_client, edit_id='thecvf.com/CVPR/2024/Conference/Area_Chairs/-/Submission_Group-0-1', count=2)
        helpers.await_queue_edit(openreview_client, edit_id='thecvf.com/CVPR/2024/Conference/Reviewers/-/Submission_Group-0-1', count=2)

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

        messages = openreview_client.get_messages(subject='[CVPR 2024]: Paper #50 desk-rejected by Program Chairs')
        assert messages and len(messages) == 3
        recipients = [msg['content']['to'] for msg in messages]
        assert 'pc@cvpr.cc' not in recipients

    def test_reviewer_recommendation(self, client, openreview_client, helpers, test_client, request_page, selenium):

        pc_client=openreview.Client(username='pc@cvpr.cc', password=helpers.strong_password)
        pc_client_v2=openreview.api.OpenReviewClient(username='pc@cvpr.cc', password=helpers.strong_password)
        request_form=pc_client.get_notes(invitation='openreview.net/Support/-/Request_Form')[0]

        openreview_client.add_members_to_group('thecvf.com/CVPR/2024/Conference/Senior_Area_Chairs', members=['~SAC_CVPROne1'])
        openreview_client.add_members_to_group('thecvf.com/CVPR/2024/Conference/Area_Chairs', members=['~AC_CVPROne1', '~AC_CVPRTwo1', '~AC_CVPRThree1'])
        openreview_client.add_members_to_group('thecvf.com/CVPR/2024/Conference/Reviewers', members=['~Reviewer_CVPROne1', '~Reviewer_CVPRTwo1', '~Reviewer_CVPRThree1', '~Reviewer_CVPRFour1', '~Reviewer_CVPRFive1', '~Reviewer_CVPRSix1'])

        submissions = pc_client_v2.get_notes(invitation='thecvf.com/CVPR/2024/Conference/-/Submission', sort='number:asc')

        ## setup sac matching data
        client.post_note(openreview.Note(
            content={
                'title': 'Paper Matching Setup',
                'matching_group': 'thecvf.com/CVPR/2024/Conference/Senior_Area_Chairs',
                'compute_conflicts': 'No',
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

        edge = pc_client_v2.post_edge(openreview.api.Edge(
            invitation = 'thecvf.com/CVPR/2024/Conference/Senior_Area_Chairs/-/Proposed_Assignment',
            head = '~AC_CVPROne1',
            tail = '~SAC_CVPROne1',
            signatures = ['thecvf.com/CVPR/2024/Conference/Program_Chairs'],
            weight = 1,
            label = 'sac-matching'
        )) 

        edge = pc_client_v2.post_edge(openreview.api.Edge(
            invitation = 'thecvf.com/CVPR/2024/Conference/Senior_Area_Chairs/-/Proposed_Assignment',
            head = '~AC_CVPRTwo1',
            tail = '~SAC_CVPROne1',
            signatures = ['thecvf.com/CVPR/2024/Conference/Program_Chairs'],
            weight = 1,
            label = 'sac-matching'
        )) 

        edge = pc_client_v2.post_edge(openreview.api.Edge(
            invitation = 'thecvf.com/CVPR/2024/Conference/Senior_Area_Chairs/-/Proposed_Assignment',
            head = '~AC_CVPRThree1',
            tail = '~SAC_CVPROne1',
            signatures = ['thecvf.com/CVPR/2024/Conference/Program_Chairs'],
            weight = 1,
            label = 'sac-matching'
        ))                        

        venue = openreview.helpers.get_conference(pc_client, request_form.id, setup=False)

        venue.set_assignments(assignment_title='sac-matching', committee_id='thecvf.com/CVPR/2024/Conference/Senior_Area_Chairs')

        assert openreview_client.get_edges_count(invitation='thecvf.com/CVPR/2024/Conference/Senior_Area_Chairs/-/Assignment') == 3

        venue.unset_assignments(assignment_title='sac-matching', committee_id='thecvf.com/CVPR/2024/Conference/Senior_Area_Chairs')

        assert openreview_client.get_edges_count(invitation='thecvf.com/CVPR/2024/Conference/Senior_Area_Chairs/-/Assignment') == 0

        venue.set_assignments(assignment_title='sac-matching', committee_id='thecvf.com/CVPR/2024/Conference/Senior_Area_Chairs')

        assert openreview_client.get_edges_count(invitation='thecvf.com/CVPR/2024/Conference/Senior_Area_Chairs/-/Assignment') == 3

        ## setup matching data
        client.post_note(openreview.Note(
            content={
                'title': 'Paper Matching Setup',
                'matching_group': 'thecvf.com/CVPR/2024/Conference/Area_Chairs',
                'compute_conflicts': 'Comprehensive',
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
                'compute_conflicts': 'Comprehensive',
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

            ## add the SAC
            pc_client_v2.add_members_to_group(f'thecvf.com/CVPR/2024/Conference/Submission{submissions[idx].number}/Senior_Area_Chairs', '~SAC_CVPROne1')

        venue = openreview.helpers.get_conference(pc_client, request_form.id, setup=False)
        venue.set_assignments(assignment_title='ac-matching', committee_id='thecvf.com/CVPR/2024/Conference/Area_Chairs')

        assert '~AC_CVPROne1' in openreview_client.get_group('thecvf.com/CVPR/2024/Conference/Submission1/Area_Chairs').members
        assert '~SAC_CVPROne1' in openreview_client.get_group('thecvf.com/CVPR/2024/Conference/Submission1/Senior_Area_Chairs').members

        assert '~AC_CVPRTwo1' in openreview_client.get_group('thecvf.com/CVPR/2024/Conference/Submission2/Area_Chairs').members
        assert '~SAC_CVPROne1' in openreview_client.get_group('thecvf.com/CVPR/2024/Conference/Submission2/Senior_Area_Chairs').members

        venue.unset_assignments(assignment_title='ac-matching', committee_id='thecvf.com/CVPR/2024/Conference/Area_Chairs')

        assert len(openreview_client.get_group('thecvf.com/CVPR/2024/Conference/Submission1/Area_Chairs').members) == 0
        assert len(openreview_client.get_group('thecvf.com/CVPR/2024/Conference/Submission1/Senior_Area_Chairs').members) == 0

        assert len(openreview_client.get_group('thecvf.com/CVPR/2024/Conference/Submission2/Area_Chairs').members) == 0
        assert len(openreview_client.get_group('thecvf.com/CVPR/2024/Conference/Submission2/Senior_Area_Chairs').members) == 0

        venue.set_assignments(assignment_title='ac-matching', committee_id='thecvf.com/CVPR/2024/Conference/Area_Chairs')

        # open reviewer recommendation
        now = datetime.datetime.now()
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
        recommendation_edge.ddate = openreview.tools.datetime_millis(datetime.datetime.now())
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

    def test_review_rating_stage(self, client, openreview_client, helpers, test_client):

        # enable review stage first
        openreview_client.add_members_to_group('thecvf.com/CVPR/2024/Conference/Submission1/Reviewers', members=['~Reviewer_CVPROne1', '~Reviewer_CVPRTwo1', '~Reviewer_CVPRThree1'])
        openreview_client.add_members_to_group('thecvf.com/CVPR/2024/Conference/Submission2/Reviewers', members=['~Reviewer_CVPRFour1', '~Reviewer_CVPRFive1', '~Reviewer_CVPRSix1'])

        pc_client=openreview.Client(username='pc@cvpr.cc', password=helpers.strong_password)
        request_form=pc_client.get_notes(invitation='openreview.net/Support/-/Request_Form')[0]

        pc_client.post_note(openreview.Note(
            content= {
                'force': 'Yes',
                'submission_readers': 'Assigned program committee (assigned reviewers, assigned area chairs, assigned senior area chairs if applicable)',
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

        now = datetime.datetime.now()
        start_date = now - datetime.timedelta(days=2)
        due_date = now + datetime.timedelta(days=3)
        review_stage_note = openreview.Note(
            content={
                'review_start_date': start_date.strftime('%Y/%m/%d'),
                'review_deadline': due_date.strftime('%Y/%m/%d'),
                'make_reviews_public': 'No, reviews should NOT be revealed publicly when they are posted',
                'release_reviews_to_authors': 'No, reviews should NOT be revealed when they are posted to the paper\'s authors',
                'release_reviews_to_reviewers': 'Review should not be revealed to any reviewer, except to the author of the review',
                'remove_review_form_options': 'title',
                'email_program_chairs_about_reviews': 'No, do not email program chairs about received reviews',
                'review_rating_field_name': 'rating'
            },
            forum=request_form.forum,
            invitation=f'openreview.net/Support/-/Request{request_form.number}/Review_Stage',
            readers=['thecvf.com/CVPR/2024/Conference/Program_Chairs', 'openreview.net/Support'],
            replyto=request_form.forum,
            referent=request_form.forum,
            signatures=['~Program_CVPRChair1'],
            writers=[]
        )

        review_stage_note_2 = openreview.Note(
            content={
                'review_start_date': start_date.strftime('%Y/%m/%d'),
                'review_deadline': due_date.strftime('%Y/%m/%d'),
                'make_reviews_public': 'No, reviews should NOT be revealed publicly when they are posted',
                'release_reviews_to_authors': 'No, reviews should NOT be revealed when they are posted to the paper\'s authors',
                'release_reviews_to_reviewers': 'Review should not be revealed to any reviewer, except to the author of the review',
                'email_program_chairs_about_reviews': 'No, do not email program chairs about received reviews',
                'review_rating_field_name': 'rating',
                'additional_review_form_options': {
                    "summary": {
                        "order": 1,
                        "description": "Briefly summarize the paper and its contributions. This is not the place to critique the paper; the authors should generally agree with a well-written summary.",
                        "value": {
                            "param": {
                                "maxLength": 200000,
                                "type": "string",
                                "input": "textarea",
                                "markdown": True
                            }
                        }
                    },
                    "soundness": {
                        "order": 2,
                        "description": "Please assign the paper a numerical rating on the following scale to indicate the soundness of the technical claims, experimental and research methodology and on whether the central claims of the paper are adequately supported with evidence.",
                        "value": {
                            "param": {
                                "type": "string",
                                "enum": [
                                    "4 excellent",
                                    "3 good",
                                    "2 fair",
                                    "1 poor"
                                ],
                                "input": "radio"
                            }
                        }
                    },
                }
            },
            forum=request_form.forum,
            invitation=f'openreview.net/Support/-/Request{request_form.number}/Review_Stage',
            readers=['thecvf.com/CVPR/2024/Conference/Program_Chairs', 'openreview.net/Support'],
            replyto=request_form.forum,
            referent=request_form.forum,
            signatures=['~Program_CVPRChair1'],
            writers=[]
        )

        pc_client.post_note(review_stage_note)
        time.sleep(2)

        with pytest.raises(openreview.OpenReviewException, match=r'There is currently a stage process running, please wait until it finishes to try again.'):
            pc_client.post_note(review_stage_note_2)

        helpers.await_queue()

        helpers.await_queue_edit(openreview_client, 'thecvf.com/CVPR/2024/Conference/-/Official_Review-0-1', count=1)

        comment_invitation = f'openreview.net/Support/-/Request{request_form.number}/Stage_Error_Status'
        error_comments = client.get_notes(invitation=comment_invitation, sort='tmdate')
        assert not error_comments or len(error_comments) == 0        

        assert len(openreview_client.get_invitations(invitation='thecvf.com/CVPR/2024/Conference/-/Official_Review')) == 49

        reviewer_client = openreview.api.OpenReviewClient(username='reviewer1@cvpr.cc', password=helpers.strong_password)

        anon_groups = reviewer_client.get_groups(prefix='thecvf.com/CVPR/2024/Conference/Submission1/Reviewer_', signatory='~Reviewer_CVPROne1')
        anon_group_id = anon_groups[0].id

        review_edit = reviewer_client.post_note_edit(
            invitation='thecvf.com/CVPR/2024/Conference/Submission1/-/Official_Review',
            signatures=[anon_group_id],
            note=openreview.api.Note(
                content={
                    'review': { 'value': 'This is a review.' },
                    'rating': { 'value': 6 },
                    'confidence': { 'value': 5 }
                }
            )
        )

        helpers.await_queue_edit(openreview_client, edit_id=review_edit['id'])

        reviewer_client = openreview.api.OpenReviewClient(username='reviewer3@cvpr.cc', password=helpers.strong_password)

        anon_groups = reviewer_client.get_groups(prefix='thecvf.com/CVPR/2024/Conference/Submission1/Reviewer_', signatory='~Reviewer_CVPRThree1')
        anon_group_id = anon_groups[0].id

        review_edit = reviewer_client.post_note_edit(
            invitation='thecvf.com/CVPR/2024/Conference/Submission1/-/Official_Review',
            signatures=[anon_group_id],
            note=openreview.api.Note(
                content={
                    'review': { 'value': 'This is another review.' },
                    'rating': { 'value': 10 },
                    'confidence': { 'value': 1 }
                }
            )
        )

        helpers.await_queue_edit(openreview_client, edit_id=review_edit['id'])

        # enable review rating stage
        venue = openreview.get_conference(client, request_form.id, support_user='openreview.net/Support')

        now = datetime.datetime.now()
        due_date = now + datetime.timedelta(days=3)
        venue.custom_stage = openreview.stages.CustomStage(name='Rating',
            reply_to=openreview.stages.CustomStage.ReplyTo.REVIEWS,
            source=openreview.stages.CustomStage.Source.ALL_SUBMISSIONS,
            due_date=due_date,
            exp_date=due_date + datetime.timedelta(days=1),
            invitees=[openreview.stages.CustomStage.Participants.AREA_CHAIRS_ASSIGNED],
            readers=[openreview.stages.CustomStage.Participants.SIGNATURES],
            content={
                'rating': {
                    'order': 1,
                    'description': 'How helpful is this review? Please refer to the reviewer guidelines: https://cvpr.thecvf.com/Conferences/2024/ReviewerGuidelines',
                    'value': {
                        'param': {
                            'type': 'string',
                            'input': 'radio',
                            'enum': [
                                "0: below expectations",
                                "1: meets expectations",
                                "2: exceeds expectations"
                            ]
                        }
                    }
                },
                'rating_justification': {
                    'order': 2,
                    'description': 'Optional justification of your rating. Add formatting using Markdown and formulas using LaTeX. For more information see https://openreview.net/faq',
                    'value': {
                        'param': {
                            'type': 'string',
                            'maxLength': 5000,
                            'markdown': True,
                            'input': 'textarea',
                            'optional': True
                        }
                    }
                }
            },
            notify_readers=False,
            email_sacs=False)

        venue.create_custom_stage()

        helpers.await_queue_edit(openreview_client, 'thecvf.com/CVPR/2024/Conference/-/Rating-0-1', count=1)

        invitation = openreview_client.get_invitation('thecvf.com/CVPR/2024/Conference/-/Rating')
        assert invitation
        invitations = openreview_client.get_invitations(invitation='thecvf.com/CVPR/2024/Conference/-/Rating')
        assert invitations and len(invitations) == 2

        submissions = venue.get_submissions(sort='number:asc', details='directReplies')
        first_submission = submissions[0]
        reviews = [reply for reply in first_submission.details['directReplies'] if f'thecvf.com/CVPR/2024/Conference/Submission{first_submission.number}/-/Official_Review']
        assert len(reviews) == 2

        invitation = openreview_client.get_invitation('thecvf.com/CVPR/2024/Conference/Submission1/Official_Review1/-/Rating')
        assert invitation.invitees == ['thecvf.com/CVPR/2024/Conference', 'thecvf.com/CVPR/2024/Conference/Submission1/Area_Chairs']
        assert invitation.noninvitees == ['thecvf.com/CVPR/2024/Conference/Submission1/Secondary_Area_Chairs']
        assert 'rating' in invitation.edit['note']['content']
        assert invitation.edit['note']['forum'] == submissions[0].id
        assert invitation.edit['note']['replyto'] == reviews[0]['id']
        assert invitation.edit['note']['readers'] == [
            'thecvf.com/CVPR/2024/Conference/Program_Chairs',
            '${3/signatures}'
        ]
        assert 'nonreaders' not in invitation.edit['note']

        ac_client = openreview.api.OpenReviewClient(username='ac1@cvpr.cc', password=helpers.strong_password)
        ac_anon_groups = ac_client.get_groups(prefix='thecvf.com/CVPR/2024/Conference/Submission1/Area_Chair_', signatory='~AC_CVPROne1')
        ac_anon_group_id = ac_anon_groups[0].id

        #post a review rating
        rating_edit = ac_client.post_note_edit(
            invitation=invitation.id,
            signatures=[ac_anon_group_id],
            note=openreview.api.Note(
                content={
                    'rating': { 'value': "0: below expectations" },
                    'rating_justification': { 'value': 'This review is not helpful.' }
                }
            )
        )

        helpers.await_queue_edit(openreview_client, edit_id=rating_edit['id'])

        assert rating_edit['note']['readers'] == ['thecvf.com/CVPR/2024/Conference/Program_Chairs', ac_anon_group_id]
        assert 'nonreaders' not in rating_edit['note']

        invitation = openreview_client.get_invitation('thecvf.com/CVPR/2024/Conference/Submission1/Official_Review2/-/Rating')

        #post another review rating to same paper
        rating_edit = ac_client.post_note_edit(
            invitation=invitation.id,
            signatures=[ac_anon_group_id],
            note=openreview.api.Note(
                content={
                    'rating': { 'value': "2: exceeds expectations" },
                }
            )
        )

        helpers.await_queue_edit(openreview_client, edit_id=rating_edit['id'])

        pc_client_v2=openreview.api.OpenReviewClient(username='pc@cvpr.cc', password=helpers.strong_password)

        notes = pc_client_v2.get_notes(invitation=invitation.id)
        assert len(notes) == 1
        assert notes[0].readers == [
            'thecvf.com/CVPR/2024/Conference/Program_Chairs',
            ac_anon_group_id
        ]
        assert notes[0].nonreaders is None
        assert notes[0].signatures == [ac_anon_group_id]

    def test_secondary_ac_assignment(self, openreview_client, helpers, client):

        ## Assign secondary ACs
        openreview_client.post_group_edit(
            invitation='thecvf.com/CVPR/2024/Conference/-/Edit',
            signatures=['thecvf.com/CVPR/2024/Conference'],
            group=openreview.api.Group(id='thecvf.com/CVPR/2024/Conference/Submission1/Secondary_Area_Chairs',
                readers=['thecvf.com/CVPR/2024/Conference', 'thecvf.com/CVPR/2024/Conference/Submission1/Senior_Area_Chairs', 'thecvf.com/CVPR/2024/Conference/Submission1/Area_Chairs'],
                nonreaders=['thecvf.com/CVPR/2024/Conference/Submission1/Authors'],
                writers=['thecvf.com/CVPR/2024/Conference'],
                signatures=['thecvf.com/CVPR/2024/Conference'],
                signatories=['thecvf.com/CVPR/2024/Conference'],
                anonids=True,
                members=['~AC_CVPRTwo1', '~AC_CVPRThree1']
        ))
        openreview_client.add_members_to_group('thecvf.com/CVPR/2024/Conference/Submission1/Area_Chairs', 'thecvf.com/CVPR/2024/Conference/Submission1/Secondary_Area_Chairs')

        openreview_client.post_group_edit(
            invitation='thecvf.com/CVPR/2024/Conference/-/Edit',
            signatures=['thecvf.com/CVPR/2024/Conference'],
            group=openreview.api.Group(id='thecvf.com/CVPR/2024/Conference/Submission2/Secondary_Area_Chairs',
                readers=['thecvf.com/CVPR/2024/Conference', 'thecvf.com/CVPR/2024/Conference/Submission2/Senior_Area_Chairs', 'thecvf.com/CVPR/2024/Conference/Submission2/Area_Chairs'],
                nonreaders=['thecvf.com/CVPR/2024/Conference/Submission2/Authors'],
                writers=['thecvf.com/CVPR/2024/Conference'],
                signatures=['thecvf.com/CVPR/2024/Conference'],
                signatories=['thecvf.com/CVPR/2024/Conference'],
                anonids=True,
                members=['~AC_CVPROne1', '~AC_CVPRThree1']
        ))
        openreview_client.add_members_to_group('thecvf.com/CVPR/2024/Conference/Submission2/Area_Chairs', 'thecvf.com/CVPR/2024/Conference/Submission2/Secondary_Area_Chairs')


        openreview_client.post_group_edit(
            invitation='thecvf.com/CVPR/2024/Conference/-/Edit',
            signatures=['thecvf.com/CVPR/2024/Conference'],
            group=openreview.api.Group(id='thecvf.com/CVPR/2024/Conference/Submission3/Secondary_Area_Chairs',
                readers=['thecvf.com/CVPR/2024/Conference', 'thecvf.com/CVPR/2024/Conference/Submission3/Senior_Area_Chairs', 'thecvf.com/CVPR/2024/Conference/Submission3/Area_Chairs'],
                nonreaders=['thecvf.com/CVPR/2024/Conference/Submission3/Authors'],
                writers=['thecvf.com/CVPR/2024/Conference'],
                signatures=['thecvf.com/CVPR/2024/Conference'],
                signatories=['thecvf.com/CVPR/2024/Conference'],
                anonids=True,
                members=['~AC_CVPRTwo1', '~AC_CVPRThree1']
        ))
        openreview_client.add_members_to_group('thecvf.com/CVPR/2024/Conference/Submission3/Area_Chairs', 'thecvf.com/CVPR/2024/Conference/Submission3/Secondary_Area_Chairs')


        openreview_client.post_group_edit(
            invitation='thecvf.com/CVPR/2024/Conference/-/Edit',
            signatures=['thecvf.com/CVPR/2024/Conference'],
            group=openreview.api.Group(id='thecvf.com/CVPR/2024/Conference/Submission4/Secondary_Area_Chairs',
                readers=['thecvf.com/CVPR/2024/Conference', 'thecvf.com/CVPR/2024/Conference/Submission4/Senior_Area_Chairs', 'thecvf.com/CVPR/2024/Conference/Submission4/Area_Chairs'],
                nonreaders=['thecvf.com/CVPR/2024/Conference/Submission4/Authors'],
                writers=['thecvf.com/CVPR/2024/Conference'],
                signatures=['thecvf.com/CVPR/2024/Conference'],
                signatories=['thecvf.com/CVPR/2024/Conference'],
                anonids=True,
                members=['~AC_CVPROne1', '~AC_CVPRThree1']
        ))
        openreview_client.add_members_to_group('thecvf.com/CVPR/2024/Conference/Submission4/Area_Chairs', 'thecvf.com/CVPR/2024/Conference/Submission4/Secondary_Area_Chairs')

        openreview_client.post_group_edit(
            invitation='thecvf.com/CVPR/2024/Conference/-/Edit',
            signatures=['thecvf.com/CVPR/2024/Conference'],
            group=openreview.api.Group(id='thecvf.com/CVPR/2024/Conference/Submission5/Secondary_Area_Chairs',
                readers=['thecvf.com/CVPR/2024/Conference', 'thecvf.com/CVPR/2024/Conference/Submission5/Senior_Area_Chairs', 'thecvf.com/CVPR/2024/Conference/Submission5/Area_Chairs'],
                nonreaders=['thecvf.com/CVPR/2024/Conference/Submission5/Authors'],
                writers=['thecvf.com/CVPR/2024/Conference'],
                signatures=['thecvf.com/CVPR/2024/Conference'],
                signatories=['thecvf.com/CVPR/2024/Conference'],
                anonids=True,
                members=['~AC_CVPRTwo1', '~AC_CVPRThree1']
        ))        
        openreview_client.add_members_to_group('thecvf.com/CVPR/2024/Conference/Submission5/Area_Chairs', 'thecvf.com/CVPR/2024/Conference/Submission5/Secondary_Area_Chairs')
    
        ## Set the meta review stage
        pc_client=openreview.Client(username='pc@cvpr.cc', password=helpers.strong_password)
        pc_client_v2=openreview.api.OpenReviewClient(username='pc@cvpr.cc', password=helpers.strong_password)
        request_form=pc_client.get_notes(invitation='openreview.net/Support/-/Request_Form')[0]

        now = datetime.datetime.now()
        start_date = now - datetime.timedelta(days=2)
        due_date = now + datetime.timedelta(days=3)
        pc_client.post_note(openreview.Note(
            content= {
                'make_meta_reviews_public': 'No, meta reviews should NOT be revealed publicly when they are posted',
                'meta_review_start_date': start_date.strftime('%Y/%m/%d'),
                'meta_review_deadline': due_date.strftime('%Y/%m/%d'),
                'release_meta_reviews_to_authors': 'No, meta reviews should NOT be revealed when they are posted to the paper\'s authors',
                'release_meta_reviews_to_reviewers': 'Meta review should not be revealed to any reviewer',
                'recommendation_field_name': 'preliminary_recommendation',
                'remove_meta_review_form_options': ['recommendation', 'confidence'],
                'additional_meta_review_form_options': {
                    "metareview": {
                        "order": 1,
                        "description": "Draft due date: 2024/02/14, 23:59 PT. Final due date: 2024/02/22, 23:59 PT. (Formatting with Markdown and formulas with LaTeX are possible; see https://openreview.net/faq for more information.)",
                        "value": {
                            "param": {
                                "type": "string",
                                "maxLength": 5000,
                                "markdown": True,
                                "input": "textarea"
                            }
                        }
                    },
                    "preliminary_recommendation": {
                        "order": 2,
                        "description": "Due date: 2024/02/14, 23:59 PT.",
                        "value": {
                            "param": {
                                "type": "string",
                                "enum": [
                                    "Clear accept",
                                    "Needs discussion",
                                    "Clear reject"
                                ]
                            }
                        }
                    }
                }
            },
            forum= request_form.id,
            invitation= f'openreview.net/Support/-/Request{request_form.number}/Meta_Review_Stage',
            readers= ['thecvf.com/CVPR/2024/Conference/Program_Chairs', 'openreview.net/Support'],
            referent= request_form.id,
            replyto= request_form.id,
            signatures= ['~Program_CVPRChair1'],
            writers= [],
        ))

        helpers.await_queue() 

        domain = openreview_client.get_group('thecvf.com/CVPR/2024/Conference')
        assert domain.content['meta_review_recommendation']['value'] == 'preliminary_recommendation'

        ac1_client = openreview.api.OpenReviewClient(username='ac1@cvpr.cc', password=helpers.strong_password)       
        ac2_client = openreview.api.OpenReviewClient(username='ac2@cvpr.cc', password=helpers.strong_password)

        invitation = openreview_client.get_invitation('thecvf.com/CVPR/2024/Conference/Submission4/-/Meta_Review')
        assert invitation.invitees == ['thecvf.com/CVPR/2024/Conference', 'thecvf.com/CVPR/2024/Conference/Submission4/Area_Chairs']
        assert invitation.noninvitees == ['thecvf.com/CVPR/2024/Conference/Submission4/Authors', 'thecvf.com/CVPR/2024/Conference/Submission4/Secondary_Area_Chairs']
        
        helpers.await_queue_edit(openreview_client, 'thecvf.com/CVPR/2024/Conference/-/Meta_Review-0-1', count=1)
        helpers.await_queue_edit(openreview_client, 'thecvf.com/CVPR/2024/Conference/-/Meta_Review_SAC_Revision-0-1', count=1)
        
        invitations = ac1_client.get_invitations(invitee=True, invitation='thecvf.com/CVPR/2024/Conference/-/Meta_Review')
        assert len(invitations) == 25

        invitations = ac2_client.get_invitations(invitee=True, invitation='thecvf.com/CVPR/2024/Conference/-/Meta_Review')
        assert len(invitations) == 24

        ## post a meta review
        submission = openreview_client.get_notes(invitation='thecvf.com/CVPR/2024/Conference/-/Submission', number=4)[0]       
        anon_reviewers_group_id = ac1_client.get_groups(prefix=f'thecvf.com/CVPR/2024/Conference/Submission4/Area_Chair_', signatory='ac2@cvpr.cc')[0].id
        ac2_client.post_note_edit(
            invitation='thecvf.com/CVPR/2024/Conference/Submission4/-/Meta_Review',
            signatures=[anon_reviewers_group_id],
            note=openreview.api.Note(
                content = {
                    'metareview': { 'value': 'Comment title' },
                    'preliminary_recommendation': { 'value': 'Clear accept' }
                }                
            )
        )

        ## Start official comment
        now = datetime.datetime.now()
        start_date = now - datetime.timedelta(days=2)
        end_date = now + datetime.timedelta(days=3)
        pc_client.post_note(openreview.Note(
            content= {
                'commentary_start_date': start_date.strftime('%Y/%m/%d'),
                'commentary_end_date': end_date.strftime('%Y/%m/%d'),
                'participants': ['Program Chairs', 'Assigned Senior Area Chairs', 'Assigned Area Chairs', 'Assigned Reviewers'],
                'email_program_chairs_about_official_comments': 'Yes, email PCs only for private official comments made in the venue (comments visible only to Program Chairs and Senior Area Chairs, if applicable)',
                'additional_readers': ['Program Chairs', 'Assigned Senior Area Chairs', 'Assigned Area Chairs', 'Assigned Reviewers'],
                'comment_description': 'Commentary due date: 2024/02/14, 23:59 PT. (Formatting with Markdown and formulas with LaTeX are possible; see https://openreview.net/faq for more information.)',
            },
            forum= request_form.id,
            invitation= f'openreview.net/Support/-/Request{request_form.number}/Comment_Stage',
            readers= ['thecvf.com/CVPR/2024/Conference/Program_Chairs', 'openreview.net/Support'],
            referent= request_form.id,
            replyto= request_form.id,
            signatures= ['~Program_CVPRChair1'],
            writers= [],
        ))

        helpers.await_queue()

        helpers.await_queue_edit(openreview_client, 'thecvf.com/CVPR/2024/Conference/-/Official_Comment-0-1', count=1)

        invitation = openreview_client.get_invitation('thecvf.com/CVPR/2024/Conference/Submission4/-/Official_Comment')
        assert 'Commentary due date: 2024/02/14, 23:59 PT. (Formatting with Markdown and formulas with LaTeX are possible; see https://openreview.net/faq for more information.)' == invitation.description

        ## post a comment as a Secondary AC
        submission = openreview_client.get_notes(invitation='thecvf.com/CVPR/2024/Conference/-/Submission', number=4)[0]   
        anon_reviewers_group_id = ac1_client.get_groups(prefix=f'thecvf.com/CVPR/2024/Conference/Submission4/Secondary_Area_Chair_', signatory='ac1@cvpr.cc')[0].id
        comment_edit = ac1_client.post_note_edit(
            invitation='thecvf.com/CVPR/2024/Conference/Submission4/-/Official_Comment',
            signatures=[anon_reviewers_group_id],
            note=openreview.api.Note(
                forum = submission.id,
                replyto = submission.id,
                readers = [
                    'thecvf.com/CVPR/2024/Conference/Submission4/Reviewers',
                    'thecvf.com/CVPR/2024/Conference/Submission4/Area_Chairs',
                    'thecvf.com/CVPR/2024/Conference/Submission4/Senior_Area_Chairs',
                    'thecvf.com/CVPR/2024/Conference/Program_Chairs'],
                content = {
                    'title': { 'value': 'Comment title' },
                    'comment': { 'value': 'Paper is very good!' }
                }                
            )
        )

        helpers.await_queue_edit(openreview_client, edit_id=comment_edit['id'])

        anon_id = anon_reviewers_group_id.split('_')[-1]

        messages = openreview_client.get_messages(to='ac1@cvpr.cc', subject='[CVPR 2024] Your comment was received on Paper Number: 4, Paper Title: "Paper title 4"')
        assert len(messages) == 1

        messages = openreview_client.get_messages(to='pc@cvpr.cc', subject=f'[CVPR 2024] Secondary Area Chair {anon_id} commented on a paper. Paper Number: 4, Paper Title: "Paper title 4"')
        assert len(messages) == 0

        comment_edit = ac1_client.post_note_edit(
            invitation='thecvf.com/CVPR/2024/Conference/Submission4/-/Official_Comment',
            signatures=[anon_reviewers_group_id],
            note=openreview.api.Note(
                forum = submission.id,
                replyto = submission.id,
                readers = [
                    'thecvf.com/CVPR/2024/Conference/Submission4/Area_Chairs',
                    'thecvf.com/CVPR/2024/Conference/Submission4/Senior_Area_Chairs',
                    'thecvf.com/CVPR/2024/Conference/Program_Chairs'],
                content = {
                    'title': { 'value': 'Direct comment' },
                    'comment': { 'value': 'PCs this paper contain plagiarism' }
                }                
            )
        )

        helpers.await_queue_edit(openreview_client, edit_id=comment_edit['id'])

        messages = openreview_client.get_messages(to='ac1@cvpr.cc', subject='[CVPR 2024] Your comment was received on Paper Number: 4, Paper Title: "Paper title 4"')
        assert len(messages) == 2

        messages = openreview_client.get_messages(to='pc@cvpr.cc', subject=f'[CVPR 2024] Secondary Area Chair {anon_id} commented on a paper. Paper Number: 4, Paper Title: "Paper title 4"')
        assert len(messages) == 1

        ## Edit description
        pc_client.post_note(openreview.Note(
            content= {
                'commentary_start_date': start_date.strftime('%Y/%m/%d'),
                'commentary_end_date': end_date.strftime('%Y/%m/%d'),
                'participants': ['Program Chairs', 'Assigned Senior Area Chairs', 'Assigned Area Chairs', 'Assigned Reviewers'],
                'email_program_chairs_about_official_comments': 'Yes, email PCs only for private official comments made in the venue (comments visible only to Program Chairs and Senior Area Chairs, if applicable)',
                'additional_readers': ['Program Chairs', 'Assigned Senior Area Chairs', 'Assigned Area Chairs', 'Assigned Reviewers'],
                'comment_description': '',
            },
            forum= request_form.id,
            invitation= f'openreview.net/Support/-/Request{request_form.number}/Comment_Stage',
            readers= ['thecvf.com/CVPR/2024/Conference/Program_Chairs', 'openreview.net/Support'],
            referent= request_form.id,
            replyto= request_form.id,
            signatures= ['~Program_CVPRChair1'],
            writers= [],
        ))

        helpers.await_queue()

        helpers.await_queue_edit(openreview_client, 'thecvf.com/CVPR/2024/Conference/-/Official_Comment-0-1', count=2)

        invitation = openreview_client.get_invitation('thecvf.com/CVPR/2024/Conference/Submission4/-/Official_Comment')
        assert '- Please select who should be able to see your comment under "Readers"' in invitation.description

        ## post a comment as a SAC
        sac1_client = openreview.api.OpenReviewClient(username='sac1@cvpr.cc', password=helpers.strong_password)
        comment_edit = sac1_client.post_note_edit(
            invitation='thecvf.com/CVPR/2024/Conference/Submission4/-/Official_Comment',
            signatures=['thecvf.com/CVPR/2024/Conference/Submission4/Senior_Area_Chairs'],
            note=openreview.api.Note(
                forum = submission.id,
                replyto = submission.id,
                readers = [
                    'thecvf.com/CVPR/2024/Conference/Submission4/Senior_Area_Chairs',
                    'thecvf.com/CVPR/2024/Conference/Program_Chairs'],
                content = {
                    'title': { 'value': 'Comment title' },
                    'comment': { 'value': 'Paper is very good!' }
                }                
            )
        )

        helpers.await_queue_edit(openreview_client, edit_id=comment_edit['id'])

        messages = openreview_client.get_messages(to='sac1@cvpr.cc', subject='[CVPR 2024] Your comment was received on Paper Number: 4, Paper Title: "Paper title 4"')
        assert len(messages) == 1

        messages = openreview_client.get_messages(to='pc@cvpr.cc', subject=f'[CVPR 2024] Senior Area Chairs commented on a paper. Paper Number: 4, Paper Title: "Paper title 4"')
        assert len(messages) == 1              

        ## setup the metareview confirmation
        start_date = openreview.tools.datetime_millis(datetime.datetime.now() - datetime.timedelta(weeks = 1))
        due_date = openreview.tools.datetime_millis(datetime.datetime.now() + datetime.timedelta(weeks = 1))

        # create metareview confirmation super invitation
        venue_id = 'thecvf.com/CVPR/2024/Conference'
        invitation = openreview.api.Invitation(id='thecvf.com/CVPR/2024/Conference/-/Meta_Review_Confirmation',
            invitees=[venue_id],
            readers=[venue_id],
            writers=[venue_id],
            signatures=[venue_id],
            cdate=start_date,
            date_processes=[{ 
                'dates': ["#{4/edit/invitation/cdate}", "#{4/mdate} + 5000"],
                'script': '''def process(client, invitation):
        meta_invitation = client.get_invitation("thecvf.com/CVPR/2024/Conference/-/Edit")
        script = meta_invitation.content["invitation_edit_script"]['value']
        funcs = {
        'openreview': openreview,
        'datetime': datetime,
        'date_index': date_index
        }
        exec(script, funcs)
        funcs['process'](client, invitation)
        '''            
            }],
            content = {
                'source': { 'value': { 'venueid': 'thecvf.com/CVPR/2024/Conference/Submission', 'reply_to': 'Meta_Review'} }
            },
            edit={
                'signatures': [venue_id],
                'readers': [venue_id],
                'writers': [venue_id],
                'content': {
                    'noteNumber': { 
                        'value': {
                            'param': {
                                'type': 'integer' 
                            }
                        }
                    },
                    'noteId': {
                        'value': {
                            'param': {
                                'type': 'string' 
                            }
                        }
                    }
                },
                'replacement': True,
                'invitation': {
                    'id': venue_id + '/Submission${2/content/noteNumber/value}/-/Meta_Review_Confirmation',
                    'signatures': [ venue_id ],
                    'readers': [venue_id, 'thecvf.com/CVPR/2024/Conference/Submission${3/content/noteNumber/value}/Secondary_Area_Chairs'],
                    'writers': [venue_id],
                    'invitees': [venue_id, 'thecvf.com/CVPR/2024/Conference/Submission${3/content/noteNumber/value}/Secondary_Area_Chairs'],
                    'maxReplies': 1,
                    'cdate': start_date,
                    'duedate': due_date,
                    'edit': {
                        'signatures': { 
                            'param': { 
                                'items': [  
                                    { 'prefix': 'thecvf.com/CVPR/2024/Conference/Submission${7/content/noteNumber/value}/Secondary_Area_Chair_.*', 'optional': True }
                                ] 
                            }
                        },
                        'readers': ['thecvf.com/CVPR/2024/Conference/Program_Chairs', 
                                    'thecvf.com/CVPR/2024/Conference/Submission${4/content/noteNumber/value}/Senior_Area_Chairs',
                                    'thecvf.com/CVPR/2024/Conference/Submission${4/content/noteNumber/value}/Area_Chairs'],
                        'nonreaders': ['thecvf.com/CVPR/2024/Conference/Submission${4/content/noteNumber/value}/Authors'],
                        'writers': [venue_id],
                        'note': {
                            'id': {
                                'param': {
                                    'withInvitation': 'thecvf.com/CVPR/2024/Conference/Submission${6/content/noteNumber/value}/-/Meta_Review_Confirmation',
                                    'optional': True
                                }
                            },
                            'forum': '${4/content/noteId/value}',
                            'replyto': '${4/content/noteId/value}',
                            'ddate': {
                                'param': {
                                    'range': [ 0, 9999999999999 ],
                                    'optional': True,
                                    'deletable': True                                   
                                }
                            },
                            'signatures': ['${3/signatures}'],
                            'readers': ['thecvf.com/CVPR/2024/Conference/Program_Chairs', 
                                'thecvf.com/CVPR/2024/Conference/Submission${5/content/noteNumber/value}/Senior_Area_Chairs',
                                'thecvf.com/CVPR/2024/Conference/Submission${5/content/noteNumber/value}/Area_Chairs'],
                            'nonreaders': ['thecvf.com/CVPR/2024/Conference/Submission${5/content/noteNumber/value}/Authors'],
                            'writers': [
                                "thecvf.com/CVPR/2024/Conference",
                                "${3/signatures}"
                            ],
                            'content': {
                                'decision': {
                                    'order': 1,
                                    'description': "Please enter the decision for the paper (should match that of the primary AC).",
                                    'value': {
                                        'param': {
                                            'type': 'string',
                                            'enum': [
                                            'Accept',
                                            'Reject'
                                            ],
                                            'input': 'radio'
                                        }
                                    }
                                },
                                'meta_review_confirmation': {
                                    'order': 2,
                                    'description': "Please confirm that you approve the decision and the meta-review.",
                                    'value': {
                                        'param': {
                                            'type': 'string',
                                            'enum': [
                                            'yes',
                                            'no'
                                            ],
                                            'input': 'radio'
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        )

        openreview_client.post_invitation_edit(invitations='thecvf.com/CVPR/2024/Conference/-/Edit',
                    readers=[venue_id],
                    writers=[venue_id],
                    signatures=[venue_id],
                    replacement=False,
                    invitation=invitation
                )
        
        openreview_client.post_invitation_edit(
            invitations='thecvf.com/CVPR/2024/Conference/-/Meta_Review_Confirmation',
            signatures=[venue_id],
            content={
                'noteId': {
                    'value': submission.id
                },
                'noteNumber': {
                    'value': submission.number
                }
            }
        )

        helpers.await_queue_edit(openreview_client, 'thecvf.com/CVPR/2024/Conference/-/Meta_Review_Confirmation-0-1', count=1)

        ac1_client.post_note_edit(
            invitation='thecvf.com/CVPR/2024/Conference/Submission4/-/Meta_Review_Confirmation',
            signatures=[anon_reviewers_group_id],
            note=openreview.api.Note(
                content = {
                    'decision': { 'value': 'Accept' },
                    'meta_review_confirmation': { 'value': 'yes' }
                }                
            )
        )        

    def test_metareview_revision_stage(self, client, openreview_client, helpers, test_client):
        pc_client=openreview.Client(username='pc@cvpr.cc', password=helpers.strong_password)
        request_form=pc_client.get_notes(invitation='openreview.net/Support/-/Request_Form')[0]
        venue = openreview.get_conference(client, request_form.id, support_user='openreview.net/Support')
        
        # Open meta review revision for final recommendation, allow metareview to be modified
        now = datetime.datetime.now()
        due_date = now + datetime.timedelta(days=2)
        
        meta_review_revision_content = {
            "metareview": {
                "order": 1,
                "description": "Draft due date: 2024/02/14, 23:59 PT. Final due date: 2024/02/22, 23:59 PT. (Formatting with Markdown and formulas with LaTeX are possible; see https://openreview.net/faq for more information.)",
                "value": {
                    "param": {
                        "type": "string",
                        "maxLength": 5000,
                        "markdown": True,
                        "input": "textarea"
                    }
                }
            },
            "final_recommendation": {
                "order": 4,
                "description": "Due date: 2024/02/22, 23:59 PT.",
                "value": {
                    "param": {
                        "type": "string",
                        "enum": [
                            "Accept",
                            "Reject"
                        ]
                    }
                }
            },
            "select_as_highlight_or_oral": {
                "order": 5,
                "description": "Due date: 2024/02/22, 23:59 PT. (Top 10% of accepted papers.)",
                "value": {
                    "param": {
                        "type": "string",
                        "enum": [
                            "No",
                            "Highlight: Top 10% of the accepted papers",
                            "Oral: Top 3-5% of the accepted papers"
                        ]
                    }
                }
            },
            "award_candidate": {
                "order": 6,
                "description": "Due date: 2024/02/22, 23:59 PT.",
                "value": {
                    "param": {
                        "type": "string",
                        "enum": [
                            "Yes",
                            "No"
                        ]
                    }
                }
            }
        }

        venue.custom_stage = openreview.stages.CustomStage(name='Final_Revision',
            reply_to=openreview.stages.CustomStage.ReplyTo.METAREVIEWS,
            source=openreview.stages.CustomStage.Source.ALL_SUBMISSIONS,
            reply_type=openreview.stages.CustomStage.ReplyType.REVISION,
            invitees=[openreview.stages.CustomStage.Participants.AREA_CHAIRS_ASSIGNED],
            due_date=due_date,
            exp_date=due_date + datetime.timedelta(minutes=30),
            content=meta_review_revision_content)

        venue.create_custom_stage()
        helpers.await_queue_edit(openreview_client, 'thecvf.com/CVPR/2024/Conference/-/Final_Revision-0-1', count=1)

        invitation = openreview_client.get_invitation('thecvf.com/CVPR/2024/Conference/-/Final_Revision')
        assert invitation

        # Only 1 paper invitation was created
        invitations = openreview_client.get_invitations(invitation='thecvf.com/CVPR/2024/Conference/-/Final_Revision')
        assert invitations and len(invitations) == 1
        assert 'thecvf.com/CVPR/2024/Conference/Submission4/Meta_Review1/-/Final_Revision' in invitations[0].id

        # Posting a new meta review creates a meta review revision invitation for that paper
        ac1_client = openreview.api.OpenReviewClient(username='ac1@cvpr.cc', password=helpers.strong_password)       
        ac_anon_group_id = ac1_client.get_groups(prefix=f'thecvf.com/CVPR/2024/Conference/Submission5/Area_Chair_', signatory='ac1@cvpr.cc')[0].id
        ac1_client.post_note_edit(
            invitation='thecvf.com/CVPR/2024/Conference/Submission5/-/Meta_Review',
            signatures=[ac_anon_group_id],
            note=openreview.api.Note(
                content = {
                    'metareview': { 'value': 'Comment title' },
                    'preliminary_recommendation': { 'value': 'Clear accept' }
                }                
            )
        )

        helpers.await_queue_edit(openreview_client, invitation='thecvf.com/CVPR/2024/Conference/Submission5/-/Meta_Review')

        invitations = openreview_client.get_invitations(invitation='thecvf.com/CVPR/2024/Conference/-/Final_Revision')
        assert invitations and len(invitations) == 2
        assert 'thecvf.com/CVPR/2024/Conference/Submission5/Meta_Review1/-/Final_Revision' in invitations[1].id

        # Post a meta review revision
        ac2_client = openreview.api.OpenReviewClient(username='ac2@cvpr.cc', password=helpers.strong_password)
        ac_anon_group_id = ac2_client.get_groups(prefix=f'thecvf.com/CVPR/2024/Conference/Submission4/Area_Chair_.*', signatory='ac2@cvpr.cc')[0].id

        meta_review = ac2_client.get_notes(invitation='thecvf.com/CVPR/2024/Conference/Submission4/-/Meta_Review')[0]

        meta_review_revision = ac2_client.post_note_edit(
            invitation='thecvf.com/CVPR/2024/Conference/Submission4/Meta_Review1/-/Final_Revision',
            signatures=[ac_anon_group_id],
            note=openreview.api.Note(
                id=meta_review.id,
                content={
                    'metareview': { 'value': 'Revised comment title' },
                    'final_recommendation': { 'value': 'Accept' },
                    'select_as_highlight_or_oral': { 'value': 'Highlight: Top 10% of the accepted papers' },
                    'award_candidate': { 'value': 'Yes' }
                }
            )
        )
        helpers.await_queue_edit(openreview_client, edit_id=meta_review_revision['id'])

        # Check that meta review was updated with new fields
        meta_review = ac2_client.get_notes(invitation='thecvf.com/CVPR/2024/Conference/Submission4/-/Meta_Review')[0]
        assert meta_review.writers == ['thecvf.com/CVPR/2024/Conference', 'thecvf.com/CVPR/2024/Conference/Submission4/Senior_Area_Chairs', meta_review.signatures[0]]
        
        meta_review = ac2_client.get_notes(invitation='thecvf.com/CVPR/2024/Conference/Submission4/-/Meta_Review')[0]
        assert meta_review.readers == [ 'thecvf.com/CVPR/2024/Conference/Submission4/Senior_Area_Chairs', 
                                       'thecvf.com/CVPR/2024/Conference/Submission4/Area_Chairs',
                                       'thecvf.com/CVPR/2024/Conference/Program_Chairs' ]
        assert 'metareview' in meta_review.content
        assert 'final_recommendation' in meta_review.content
        assert 'select_as_highlight_or_oral' in meta_review.content
        assert 'award_candidate' in meta_review.content
        assert meta_review.content['metareview']['value'] == 'Revised comment title'

        # Allow SACs to modify all meta review fields
        openreview_client.post_invitation_edit(
            invitations='thecvf.com/CVPR/2024/Conference/-/Edit',
            readers=[venue.id],
            writers=[venue.id],
            signatures=[venue.id],
            invitation=openreview.api.Invitation(
                id='thecvf.com/CVPR/2024/Conference/-/Meta_Review_SAC_Revision',
                edit={
                    "invitation": {
                        "edit": {
                            "note": {
                                "content": meta_review_revision_content
                            }
                        }
                    }
                }
            )
        )
        helpers.await_queue_edit(openreview_client, edit_id='thecvf.com/CVPR/2024/Conference/-/Meta_Review_SAC_Revision-0-1', count=2)

        # Post meta review SAC revision
        sac_client = openreview.api.OpenReviewClient(username='sac1@cvpr.cc', password=helpers.strong_password)
        meta_review = sac_client.get_notes(invitation='thecvf.com/CVPR/2024/Conference/Submission4/-/Meta_Review')[0]
        sac_revision = sac_client.post_note_edit(
            invitation='thecvf.com/CVPR/2024/Conference/Submission4/-/Meta_Review_SAC_Revision',
            signatures=['thecvf.com/CVPR/2024/Conference/Submission4/Senior_Area_Chairs'],
            note=openreview.api.Note(
                id=meta_review.id,
                content={
                    'metareview': { 'value': 'SAC revised comment title' },
                    'preliminary_recommendation': { 'value': 'Clear accept' },
                    'final_recommendation': { 'value': 'Accept' },
                    'select_as_highlight_or_oral': { 'value': 'Oral: Top 3-5% of the accepted papers' },
                    'award_candidate': { 'value': 'Yes' }
                }
            )
        )

        ## Try to edit the invitation and don't get prefix group not found error
        openreview_client.post_invitation_edit(
            invitations='thecvf.com/CVPR/2024/Conference/-/Edit',
            readers=[venue.id],
            writers=[venue.id],
            signatures=[venue.id],
            invitation=openreview.api.Invitation(
                id='thecvf.com/CVPR/2024/Conference/Submission4/Meta_Review1/-/Final_Revision',
                expdate=openreview.tools.datetime_millis(due_date + datetime.timedelta(days=1))
            )
        )
      
        
        # Secondary AC can't post meta review revision
        secondary_ac_client = openreview.api.OpenReviewClient(username='ac1@cvpr.cc', password=helpers.strong_password)
        secondary_ac_anon_group_id = secondary_ac_client.get_groups(prefix=f'thecvf.com/CVPR/2024/Conference/Submission4/Secondary_Area_Chair_.*', signatory='ac1@cvpr.cc')[0].id

        with pytest.raises(openreview.OpenReviewException, match=r'User is not writer of the Note'):
            meta_review_revision = secondary_ac_client.post_note_edit(
                invitation='thecvf.com/CVPR/2024/Conference/Submission4/Meta_Review1/-/Final_Revision',
                signatures=[secondary_ac_anon_group_id],
                note=openreview.api.Note(
                    id=meta_review.id,
                    content={
                        'metareview': { 'value': 'Revised comment title by secondary ac' },
                        'final_recommendation': { 'value': 'Reject' },
                        'select_as_highlight_or_oral': { 'value': 'No' },
                        'award_candidate': { 'value': 'No' }
                    }
                )
            )
