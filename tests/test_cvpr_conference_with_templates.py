import base64
import datetime
import json
import os
import re
import threading
import time
import openreview
import pytest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from selenium.webdriver.common.by import By

@pytest.fixture(scope='module')
def llm_mock():
    # stands in for the LLM gateway: records the requests of the chat process and answers in the Anthropic format;
    # the API process runner reaches it on localhost because the services share the network
    received = []

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            body = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
            received.append({ 'path': self.path, 'authorization': self.headers.get('Authorization'), 'body': body })
            question = body['messages'][-1]['content']
            if isinstance(question, list):
                question = question[-1]['text']
            # keeps the question pending for a while
            if '[slow]' in question:
                time.sleep(5)
            answer = json.dumps({
                'id': 'msg_mock',
                'type': 'message',
                'role': 'assistant',
                'model': body['model'],
                'stop_reason': 'end_turn',
                'content': [{ 'type': 'text', 'text': f'Answer from the LLM mock to: {question}' }],
                'usage': { 'input_tokens': 100, 'output_tokens': 20 }
            }).encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(answer)))
            self.send_header('x-litellm-response-cost-original', '0.0021')
            self.send_header('x-litellm-response-cost-discount-amount', '0.0')
            self.send_header('x-litellm-response-cost-margin-amount', '0.0')
            self.end_headers()
            self.wfile.write(answer)

        def log_message(self, format, *args):
            pass

    server = ThreadingHTTPServer(('0.0.0.0', 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    yield { 'url': f'http://localhost:{server.server_port}', 'requests': received }
    server.shutdown()

class TestCVPRConferenceWithTemplates():

    def test_setup(self, openreview_client, helpers):

        helpers.create_user('pc@cvpr.cc', 'Program', 'CVPRChair')
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
        helpers.create_user('reviewer7@gmail.com', 'Reviewer', 'CVPRSeven')
        pc_client = openreview.api.OpenReviewClient(username='pc@cvpr.cc', password=helpers.strong_password)

        now = datetime.datetime.now()
        due_date = now + datetime.timedelta(days=3)

        request = pc_client.post_note_edit(invitation='openreview.net/Support/Venue_Request/-/Conference_Review_Workflow',
            signatures=['~Program_CVPRChair1'],
            note=openreview.api.Note(
                content={
                    'official_venue_name': { 'value': 'Conference on Computer Vision and Pattern Recognition 2027' },
                    'abbreviated_venue_name': { 'value': 'CVPR 2027' },
                    'venue_website_url': { 'value': 'https://cvpr.thecvf.com/Conferences/2027' },
                    'location': { 'value': 'Virtual' },
                    'venue_start_date': { 'value': openreview.tools.datetime_millis(now + datetime.timedelta(weeks=52)) },
                    'program_chair_emails': { 'value': ['pc@cvpr.cc'] },
                    'contact_email': { 'value': 'pc@cvpr.cc' },
                    'submission_start_date': { 'value': openreview.tools.datetime_millis(now) },
                    'submission_deadline': { 'value': openreview.tools.datetime_millis(due_date) },
                    'area_chairs_support': { 'value': True },
                    'senior_area_chairs_support': { 'value': True },
                    'expected_submissions': { 'value': 100 },
                    'how_did_you_hear_about_us': { 'value': 'ML conferences' },
                    'venue_organizer_agreement': {
                        'value': [
                            'OpenReview natively supports a wide variety of reviewing workflow configurations. However, if we want significant reviewing process customizations or experiments, we will detail these requests to the OpenReview staff at least three months in advance.',
                            'We will ask authors and reviewers to create an OpenReview Profile well in advance of the paper submission deadlines.',
                            'When assembling our group of reviewers, we will only include email addresses or OpenReview Profile IDs of people we know to have authored publications relevant to our venue.  (We will not solicit new reviewers using an open web form, because unfortunately some malicious actors sometimes try to create "fake ids" aiming to be assigned to review their own paper submissions.)',
                            'We acknowledge that, if our venue\'s reviewing workflow is non-standard, or if our venue is expecting more than a few hundred submissions for any one deadline, we should designate our own Workflow Chair, who will read the OpenReview documentation and manage our workflow configurations throughout the reviewing process.',
                            'We acknowledge that OpenReview staff work Monday-Friday during standard business hours US Eastern time, and we cannot expect support responses outside those times.  For this reason, we recommend setting submission and reviewing deadlines Monday through Thursday.',
                            'We will treat the OpenReview staff with kindness and consideration.',
                            'We acknowledge that authors and reviewers will be required to share their preferred email.',
                            'We acknowledge that certain metadata for accepted papers, specifically the paper title, abstract and author list, will be publicly released on OpenReview.',
                        ]
                    }
                }
            ))

        helpers.await_queue_edit(openreview_client, edit_id=request['id'])

        # deploy the venue
        edit = openreview_client.post_note_edit(invitation='openreview.net/Support/Venue_Request/Conference_Review_Workflow/-/Deployment',
            signatures=['openreview.net/Support'],
            note=openreview.api.Note(
                id=request['note']['id'],
                content={
                    'venue_id': { 'value': 'thecvf.com/CVPR/2027/Conference' }
                }
            ))

        helpers.await_queue_edit(openreview_client, edit_id=edit['id'])
        helpers.await_queue_edit(openreview_client, 'thecvf.com/CVPR/2027/Conference/-/Submission_Change_Before_Bidding-0-1', count=1)
        helpers.await_queue_edit(openreview_client, 'thecvf.com/CVPR/2027/Conference/Reviewers/-/Submission_Group-0-1', count=1)
        helpers.await_queue_edit(openreview_client, 'thecvf.com/CVPR/2027/Conference/Area_Chairs/-/Submission_Group-0-1', count=1)
        helpers.await_queue_edit(openreview_client, 'thecvf.com/CVPR/2027/Conference/Senior_Area_Chairs/-/Submission_Group-0-1', count=1)

        venue_group = openreview_client.get_group('thecvf.com/CVPR/2027/Conference')
        assert venue_group.content['senior_area_chairs_id']['value'] == 'thecvf.com/CVPR/2027/Conference/Senior_Area_Chairs'
        assert venue_group.content['area_chairs_id']['value'] == 'thecvf.com/CVPR/2027/Conference/Area_Chairs'
        assert venue_group.content['reviewers_id']['value'] == 'thecvf.com/CVPR/2027/Conference/Reviewers'

        assert openreview_client.get_group('thecvf.com/CVPR/2027/Conference/Senior_Area_Chairs')
        assert openreview_client.get_group('thecvf.com/CVPR/2027/Conference/Area_Chairs')
        assert openreview_client.get_group('thecvf.com/CVPR/2027/Conference/Reviewers')
        assert openreview_client.get_group('thecvf.com/CVPR/2027/Conference/Authors')

        submission_invitation = openreview_client.get_invitation('thecvf.com/CVPR/2027/Conference/-/Submission')
        assert submission_invitation
        assert submission_invitation.duedate

        assert openreview_client.get_invitation('thecvf.com/CVPR/2027/Conference/Reviewers/-/Assignment_Configuration')
        assert openreview_client.get_invitation('thecvf.com/CVPR/2027/Conference/-/Reviewers_Assignment_Deployment')

        openreview_client.add_members_to_group('thecvf.com/CVPR/2027/Conference/Senior_Area_Chairs', ['~SAC_CVPROne1'])
        openreview_client.add_members_to_group('thecvf.com/CVPR/2027/Conference/Area_Chairs', ['~AC_CVPROne1', '~AC_CVPRTwo1', '~AC_CVPRThree1'])
        openreview_client.add_members_to_group('thecvf.com/CVPR/2027/Conference/Reviewers', [
            '~Reviewer_CVPROne1',
            '~Reviewer_CVPRTwo1',
            '~Reviewer_CVPRThree1',
            '~Reviewer_CVPRFour1',
            '~Reviewer_CVPRFive1',
            '~Reviewer_CVPRSix1',
            '~Reviewer_CVPRSeven1'
        ])

    def test_submissions(self, openreview_client, helpers, test_client):

        test_client = openreview.api.OpenReviewClient(token=test_client.token)

        domains = ['umass.edu', 'amazon.com', 'fb.com', 'cs.umass.edu', 'google.com', 'mit.edu', 'deepmind.com', 'co.ux', 'apple.com', 'nvidia.com']
        for domain in domains:
            helpers.create_user(f'kai@{domain}', 'Kai', f'{domain.split(".")[0].capitalize()}')

        for i in range(1,11):
            kai_domain = domains[i % 10]
            domain_name = kai_domain.split('.')[0].capitalize()
            note = openreview.api.Note(
                license = 'CC BY 4.0',
                content = {
                    'title': { 'value': 'Paper title ' + str(i) },
                    'abstract': { 'value': 'This is an abstract ' + str(i) },
                    'authors': {
                        'value': [
                            {
                                'fullname': 'SomeFirstName User',
                                'username': '~SomeFirstName_User1',
                                'institutions': [{ 'domain': 'mail.com', 'country': 'US' }]
                            },
                            {
                                'fullname': f'Kai {domain_name}',
                                'username': f'~Kai_{domain_name}1',
                                'institutions': [{ 'domain': kai_domain, 'country': 'US' }]
                            }
                        ]
                    },
                    'keywords': { 'value': ['computer vision', 'image segmentation'] },
                    'pdf': {'value': '/pdf/' + 'p' * 40 +'.pdf' },
                    'email_sharing': { 'value': 'We authorize the sharing of all author emails with Program Chairs.' },
                    'data_release': { 'value': 'We authorize the release of our submission and author names to the public in the event of acceptance.' }
                }
            )
            if i == 1 or i == 10:
                note.content['authors']['value'].append({
                    'fullname': 'SAC CVPROne',
                    'username': '~SAC_CVPROne1',
                    'institutions': [{ 'domain': 'cvpr.cc', 'country': 'US' }]
                })

            # submission 2 has a real PDF, so the LLM chat can be tried on it
            if i == 2:
                note.content['pdf']['value'] = test_client.put_attachment(os.path.join(os.path.dirname(__file__), 'data/openreview.pdf'), 'thecvf.com/CVPR/2027/Conference/-/Submission', 'pdf')

            test_client.post_note_edit(invitation='thecvf.com/CVPR/2027/Conference/-/Submission',
                signatures=['~SomeFirstName_User1'],
                note=note)

        helpers.await_queue_edit(openreview_client, invitation='thecvf.com/CVPR/2027/Conference/-/Submission', count=10)

        submissions = openreview_client.get_notes(invitation='thecvf.com/CVPR/2027/Conference/-/Submission', sort='number:asc')
        assert len(submissions) == 10
        assert submissions[0].readers == ['thecvf.com/CVPR/2027/Conference', '~SomeFirstName_User1', '~Kai_Amazon1', '~SAC_CVPROne1']
        assert submissions[0].license == 'CC BY 4.0'

        with open(os.path.join(os.path.dirname(__file__), 'data/openreview.pdf'), 'rb') as pdf_file:
            assert openreview_client.get_attachment('pdf', id=submissions[1].id) == pdf_file.read()

        authors_group = openreview_client.get_group('thecvf.com/CVPR/2027/Conference/Authors')
        for i in range(1,11):
            assert f'thecvf.com/CVPR/2027/Conference/Submission{i}/Authors' in authors_group.members

    def test_post_submission(self, openreview_client, helpers):

        pc_client = openreview.api.OpenReviewClient(username='pc@cvpr.cc', password=helpers.strong_password)

        # close the submission deadline
        now = datetime.datetime.now()

        edit = pc_client.post_invitation_edit(
            invitations='thecvf.com/CVPR/2027/Conference/-/Submission/Dates',
            content={
                'activation_date': { 'value': openreview.tools.datetime_millis(now - datetime.timedelta(days=2)) },
                'due_date': { 'value': openreview.tools.datetime_millis(now - datetime.timedelta(hours=1)) }
            }
        )

        helpers.await_queue_edit(openreview_client, edit_id=edit['id'])
        helpers.await_queue_edit(openreview_client, 'thecvf.com/CVPR/2027/Conference/Reviewers/-/Submission_Message-0-1', count=2)
        helpers.await_queue_edit(openreview_client, 'thecvf.com/CVPR/2027/Conference/Area_Chairs/-/Submission_Message-0-1', count=2)

        submission_invitation = pc_client.get_invitation('thecvf.com/CVPR/2027/Conference/-/Submission')
        assert submission_invitation.expdate < openreview.tools.datetime_millis(now)

        # CVPR releases the submissions to the area chairs only, reviewers see their papers once they are assigned
        pc_client.post_invitation_edit(
            invitations='thecvf.com/CVPR/2027/Conference/-/Submission_Change_Before_Bidding/Readers',
            content={
                'readers': {
                    'value': [
                        'thecvf.com/CVPR/2027/Conference',
                        'thecvf.com/CVPR/2027/Conference/Senior_Area_Chairs',
                        'thecvf.com/CVPR/2027/Conference/Area_Chairs',
                        'thecvf.com/CVPR/2027/Conference/Submission${{2/id}/number}/Authors'
                    ]
                }
            }
        )
        helpers.await_queue_edit(openreview_client, edit_id='thecvf.com/CVPR/2027/Conference/-/Submission_Change_Before_Bidding-0-1', count=2)

        pc_client.post_invitation_edit(
            invitations='thecvf.com/CVPR/2027/Conference/-/Submission_Change_Before_Bidding/Dates',
            content={
                'activation_date': { 'value': openreview.tools.datetime_millis(now - datetime.timedelta(minutes=30)) }
            }
        )
        helpers.await_queue_edit(openreview_client, edit_id='thecvf.com/CVPR/2027/Conference/-/Submission_Change_Before_Bidding-0-1', count=3)

        submissions = pc_client.get_notes(invitation='thecvf.com/CVPR/2027/Conference/-/Submission', sort='number:asc')
        assert len(submissions) == 10
        assert submissions[0].readers == [
            'thecvf.com/CVPR/2027/Conference',
            'thecvf.com/CVPR/2027/Conference/Senior_Area_Chairs',
            'thecvf.com/CVPR/2027/Conference/Area_Chairs',
            'thecvf.com/CVPR/2027/Conference/Submission1/Authors'
        ]
        assert submissions[0].content['authors']['readers'] == ['thecvf.com/CVPR/2027/Conference', 'thecvf.com/CVPR/2027/Conference/Submission1/Authors']
        assert submissions[0].content['pdf']['readers'] == ['thecvf.com/CVPR/2027/Conference', 'thecvf.com/CVPR/2027/Conference/Submission1/Authors']
        assert not submissions[0].odate

        ac_client = openreview.api.OpenReviewClient(username='ac1@cvpr.cc', password=helpers.strong_password)
        assert len(ac_client.get_notes(invitation='thecvf.com/CVPR/2027/Conference/-/Submission')) == 10

        reviewer_client = openreview.api.OpenReviewClient(username='reviewer1@cvpr.cc', password=helpers.strong_password)
        assert len(reviewer_client.get_notes(invitation='thecvf.com/CVPR/2027/Conference/-/Submission')) == 0

        # create the per paper committee groups
        for role in ['Reviewers', 'Area_Chairs', 'Senior_Area_Chairs']:
            pc_client.post_invitation_edit(
                invitations=f'thecvf.com/CVPR/2027/Conference/{role}/-/Submission_Group/Dates',
                content={
                    'activation_date': { 'value': openreview.tools.datetime_millis(now - datetime.timedelta(minutes=30)) }
                }
            )

            helpers.await_queue_edit(openreview_client, edit_id=f'thecvf.com/CVPR/2027/Conference/{role}/-/Submission_Group-0-1', count=2)

        submission_groups = openreview_client.get_all_groups(prefix='thecvf.com/CVPR/2027/Conference/Submission')
        assert len([group for group in submission_groups if group.id.endswith('/Reviewers')]) == 10
        assert len([group for group in submission_groups if group.id.endswith('/Area_Chairs')]) == 10
        assert len([group for group in submission_groups if group.id.endswith('/Senior_Area_Chairs')]) == 10

    def test_reviewer_conflicts(self, openreview_client, helpers):

        pc_client = openreview.api.OpenReviewClient(username='pc@cvpr.cc', password=helpers.strong_password)

        pc_client.post_invitation_edit(
            invitations='thecvf.com/CVPR/2027/Conference/Reviewers/-/Conflict/Policy',
            content={
                'conflict_policy': { 'value': 'Comprehensive' },
                'conflict_n_years': { 'value': 3 }
            }
        )

        helpers.await_queue_edit(openreview_client, edit_id='thecvf.com/CVPR/2027/Conference/Reviewers/-/Conflict-0-1', count=2)

        # trigger the conflicts date process
        now = openreview.tools.datetime_millis(datetime.datetime.now())
        pc_client.post_invitation_edit(
            invitations='thecvf.com/CVPR/2027/Conference/Reviewers/-/Conflict/Dates',
            content={
                'activation_date': { 'value': now }
            }
        )

        helpers.await_queue_edit(openreview_client, edit_id='thecvf.com/CVPR/2027/Conference/Reviewers/-/Conflict-0-1', count=3)

        # the six cvpr.cc reviewers conflict with the papers 1 and 10 co-authored by SAC CVPROne
        assert len(openreview_client.get_grouped_edges(
            invitation='thecvf.com/CVPR/2027/Conference/Reviewers/-/Conflict',
            groupby='id'
        )) == 12

    def test_reviewer_assignments(self, openreview_client, helpers):

        pc_client = openreview.api.OpenReviewClient(username='pc@cvpr.cc', password=helpers.strong_password)

        submissions = pc_client.get_notes(content={'venueid': 'thecvf.com/CVPR/2027/Conference/Submission'}, sort='number:asc')
        assert len(submissions) == 10

        config_note = openreview_client.post_note_edit(
            invitation='thecvf.com/CVPR/2027/Conference/Reviewers/-/Assignment_Configuration',
            readers=['thecvf.com/CVPR/2027/Conference'],
            writers=['thecvf.com/CVPR/2027/Conference'],
            signatures=['thecvf.com/CVPR/2027/Conference'],
            note=openreview.api.Note(
                content={
                    'title': { 'value': 'reviewers-matching'},
                    'user_demand': { 'value': '3'},
                    'max_papers': { 'value': '5'},
                    'min_papers': { 'value': '0'},
                    'alternates': { 'value': '2'},
                    'paper_invitation': { 'value': 'thecvf.com/CVPR/2027/Conference/-/Submission&content.venueid=thecvf.com/CVPR/2027/Conference/Submission'},
                    'match_group': { 'value': 'thecvf.com/CVPR/2027/Conference/Reviewers'},
                    'scores_specification': {
                        'value': {
                            'thecvf.com/CVPR/2027/Conference/Reviewers/-/Bid': {
                                'weight': 1,
                                'default': 0,
                                'translate_map': {
                                    'Very High': 1.0,
                                    'High': 0.5,
                                    'Neutral': 0.0,
                                    'Low': -0.5,
                                    'Very Low': -1.0
                                }
                            }
                        }
                    },
                    'aggregate_score_invitation': { 'value': 'thecvf.com/CVPR/2027/Conference/Reviewers/-/Aggregate_Score'},
                    'conflicts_invitation': { 'value': 'thecvf.com/CVPR/2027/Conference/Reviewers/-/Conflict'},
                    'solver': { 'value': 'FairFlow'},
                    'status': { 'value': 'Initialized'},
                }
            )
        )
        helpers.await_queue_edit(openreview_client, invitation='thecvf.com/CVPR/2027/Conference/Reviewers/-/Assignment_Configuration')

        # spread the cvpr.cc reviewers over the papers 2 to 9, three reviewers per paper
        reviewers = ['~Reviewer_CVPROne1', '~Reviewer_CVPRTwo1', '~Reviewer_CVPRThree1', '~Reviewer_CVPRFour1', '~Reviewer_CVPRFive1', '~Reviewer_CVPRSix1']
        for idx, submission in enumerate(submissions[1:9]):
            for offset in range(3):
                openreview_client.post_edge(openreview.api.Edge(
                    invitation='thecvf.com/CVPR/2027/Conference/Reviewers/-/Proposed_Assignment',
                    head=submission.id,
                    tail=reviewers[(idx * 3 + offset) % 6],
                    signatures=['thecvf.com/CVPR/2027/Conference/Program_Chairs'],
                    weight=1,
                    label='reviewers-matching'
                ))

        # the conflicted papers 1 and 10 are reviewed by the external reviewer
        for submission in [submissions[0], submissions[9]]:
            openreview_client.post_edge(openreview.api.Edge(
                invitation='thecvf.com/CVPR/2027/Conference/Reviewers/-/Proposed_Assignment',
                head=submission.id,
                tail='~Reviewer_CVPRSeven1',
                signatures=['thecvf.com/CVPR/2027/Conference/Program_Chairs'],
                weight=1,
                label='reviewers-matching'
            ))

        # mark the configuration as complete and deploy the assignments
        openreview_client.post_note_edit(
            invitation='thecvf.com/CVPR/2027/Conference/-/Edit',
            signatures=['thecvf.com/CVPR/2027/Conference'],
            note=openreview.api.Note(
                id=config_note['note']['id'],
                content={ 'status': { 'value': 'Complete' } }
            )
        )

        openreview_client.post_invitation_edit(
            invitations='thecvf.com/CVPR/2027/Conference/-/Reviewers_Assignment_Deployment/Match',
            content={
                'match_name': { 'value': 'reviewers-matching' }
            }
        )
        helpers.await_queue_edit(openreview_client, edit_id='thecvf.com/CVPR/2027/Conference/-/Reviewers_Assignment_Deployment-0-1', count=2)

        # activate the deployment
        now = openreview.tools.datetime_millis(datetime.datetime.now())
        openreview_client.post_invitation_edit(
            invitations='thecvf.com/CVPR/2027/Conference/-/Reviewers_Assignment_Deployment/Dates',
            content={
                'activation_date': { 'value': now }
            }
        )
        helpers.await_queue_edit(openreview_client, edit_id='thecvf.com/CVPR/2027/Conference/-/Reviewers_Assignment_Deployment-0-1', count=3)

        # the deployment moves the Submission_Change_Before_Reviewing activation date
        helpers.await_queue_edit(openreview_client, 'thecvf.com/CVPR/2027/Conference/-/Submission_Change_Before_Reviewing-0-1', count=2)

        config_note = openreview_client.get_note(config_note['note']['id'])
        assert config_note.content['status']['value'] == 'Deployed'

        grouped_edges = openreview_client.get_grouped_edges(invitation='thecvf.com/CVPR/2027/Conference/Reviewers/-/Assignment', groupby='id')
        assert len(grouped_edges) == 26

        assert openreview_client.get_group('thecvf.com/CVPR/2027/Conference/Submission1/Reviewers').members == ['~Reviewer_CVPRSeven1']
        assert set(openreview_client.get_group('thecvf.com/CVPR/2027/Conference/Submission2/Reviewers').members) == {'~Reviewer_CVPROne1', '~Reviewer_CVPRTwo1', '~Reviewer_CVPRThree1'}
        assert set(openreview_client.get_group('thecvf.com/CVPR/2027/Conference/Submission3/Reviewers').members) == {'~Reviewer_CVPRFour1', '~Reviewer_CVPRFive1', '~Reviewer_CVPRSix1'}
        assert openreview_client.get_group('thecvf.com/CVPR/2027/Conference/Submission10/Reviewers').members == ['~Reviewer_CVPRSeven1']

    def test_area_chair_assignments(self, openreview_client, helpers):

        pc_client = openreview.api.OpenReviewClient(username='pc@cvpr.cc', password=helpers.strong_password)

        submissions = pc_client.get_notes(content={'venueid': 'thecvf.com/CVPR/2027/Conference/Submission'}, sort='number:asc')
        assert len(submissions) == 10

        config_note = openreview_client.post_note_edit(
            invitation='thecvf.com/CVPR/2027/Conference/Area_Chairs/-/Assignment_Configuration',
            readers=['thecvf.com/CVPR/2027/Conference'],
            writers=['thecvf.com/CVPR/2027/Conference'],
            signatures=['thecvf.com/CVPR/2027/Conference'],
            note=openreview.api.Note(
                content={
                    'title': { 'value': 'area-chairs-matching'},
                    'user_demand': { 'value': '1'},
                    'max_papers': { 'value': '5'},
                    'min_papers': { 'value': '0'},
                    'alternates': { 'value': '2'},
                    'paper_invitation': { 'value': 'thecvf.com/CVPR/2027/Conference/-/Submission&content.venueid=thecvf.com/CVPR/2027/Conference/Submission'},
                    'match_group': { 'value': 'thecvf.com/CVPR/2027/Conference/Area_Chairs'},
                    'scores_specification': {
                        'value': {
                            'thecvf.com/CVPR/2027/Conference/Area_Chairs/-/Bid': {
                                'weight': 1,
                                'default': 0,
                                'translate_map': {
                                    'Very High': 1.0,
                                    'High': 0.5,
                                    'Neutral': 0.0,
                                    'Low': -0.5,
                                    'Very Low': -1.0
                                }
                            }
                        }
                    },
                    'aggregate_score_invitation': { 'value': 'thecvf.com/CVPR/2027/Conference/Area_Chairs/-/Aggregate_Score'},
                    'conflicts_invitation': { 'value': 'thecvf.com/CVPR/2027/Conference/Area_Chairs/-/Conflict'},
                    'solver': { 'value': 'FairFlow'},
                    'status': { 'value': 'Initialized'},
                }
            )
        )
        helpers.await_queue_edit(openreview_client, invitation='thecvf.com/CVPR/2027/Conference/Area_Chairs/-/Assignment_Configuration')

        # the papers 1 and 10 are co-authored by SAC CVPROne, the cvpr.cc area chairs oversee the papers 2 to 9
        area_chairs = ['~AC_CVPROne1', '~AC_CVPRTwo1']
        for idx, submission in enumerate(submissions[1:9]):
            openreview_client.post_edge(openreview.api.Edge(
                invitation='thecvf.com/CVPR/2027/Conference/Area_Chairs/-/Proposed_Assignment',
                head=submission.id,
                tail=area_chairs[idx % 2],
                signatures=['thecvf.com/CVPR/2027/Conference/Program_Chairs'],
                weight=1,
                label='area-chairs-matching'
            ))

        # mark the configuration as complete and deploy the assignments
        openreview_client.post_note_edit(
            invitation='thecvf.com/CVPR/2027/Conference/-/Edit',
            signatures=['thecvf.com/CVPR/2027/Conference'],
            note=openreview.api.Note(
                id=config_note['note']['id'],
                content={ 'status': { 'value': 'Complete' } }
            )
        )

        openreview_client.post_invitation_edit(
            invitations='thecvf.com/CVPR/2027/Conference/-/Area_Chairs_Assignment_Deployment/Match',
            content={
                'match_name': { 'value': 'area-chairs-matching' }
            }
        )
        helpers.await_queue_edit(openreview_client, edit_id='thecvf.com/CVPR/2027/Conference/-/Area_Chairs_Assignment_Deployment-0-1', count=2)

        # activate the deployment
        now = openreview.tools.datetime_millis(datetime.datetime.now())
        openreview_client.post_invitation_edit(
            invitations='thecvf.com/CVPR/2027/Conference/-/Area_Chairs_Assignment_Deployment/Dates',
            content={
                'activation_date': { 'value': now }
            }
        )
        helpers.await_queue_edit(openreview_client, edit_id='thecvf.com/CVPR/2027/Conference/-/Area_Chairs_Assignment_Deployment-0-1', count=3)

        # the deployment moves the Submission_Change_Before_Reviewing activation date again
        helpers.await_queue_edit(openreview_client, 'thecvf.com/CVPR/2027/Conference/-/Submission_Change_Before_Reviewing-0-1', count=3)

        grouped_edges = openreview_client.get_grouped_edges(invitation='thecvf.com/CVPR/2027/Conference/Area_Chairs/-/Assignment', groupby='id')
        assert len(grouped_edges) == 8

        assert openreview_client.get_group('thecvf.com/CVPR/2027/Conference/Submission2/Area_Chairs').members == ['~AC_CVPROne1']
        assert openreview_client.get_group('thecvf.com/CVPR/2027/Conference/Submission3/Area_Chairs').members == ['~AC_CVPRTwo1']
        assert openreview_client.get_group('thecvf.com/CVPR/2027/Conference/Submission1/Area_Chairs').members == []

    def test_release_submissions_to_assigned_committee(self, openreview_client, helpers):

        pc_client = openreview.api.OpenReviewClient(username='pc@cvpr.cc', password=helpers.strong_password)

        now = datetime.datetime.now()
        pc_client.post_invitation_edit(
            invitations='thecvf.com/CVPR/2027/Conference/-/Submission_Change_Before_Reviewing/Dates',
            content={
                'activation_date': { 'value': openreview.tools.datetime_millis(now) }
            }
        )

        helpers.await_queue_edit(openreview_client, 'thecvf.com/CVPR/2027/Conference/-/Submission_Change_Before_Reviewing-0-1', count=4)

        submissions = pc_client.get_notes(invitation='thecvf.com/CVPR/2027/Conference/-/Submission', sort='number:asc')
        assert submissions[1].readers == [
            'thecvf.com/CVPR/2027/Conference',
            'thecvf.com/CVPR/2027/Conference/Submission2/Senior_Area_Chairs',
            'thecvf.com/CVPR/2027/Conference/Submission2/Area_Chairs',
            'thecvf.com/CVPR/2027/Conference/Submission2/Reviewers',
            'thecvf.com/CVPR/2027/Conference/Submission2/Authors'
        ]
        assert submissions[1].content['authors']['readers'] == ['thecvf.com/CVPR/2027/Conference', 'thecvf.com/CVPR/2027/Conference/Submission2/Authors']
        assert 'readers' not in submissions[1].content['pdf']

        # reviewers can only see the papers they are assigned to
        reviewer_client = openreview.api.OpenReviewClient(username='reviewer1@cvpr.cc', password=helpers.strong_password)
        reviewer_submissions = reviewer_client.get_notes(invitation='thecvf.com/CVPR/2027/Conference/-/Submission', sort='number:asc')
        assert [submission.number for submission in reviewer_submissions] == [2, 4, 6, 8]

        reviewer_client = openreview.api.OpenReviewClient(username='reviewer7@gmail.com', password=helpers.strong_password)
        reviewer_submissions = reviewer_client.get_notes(invitation='thecvf.com/CVPR/2027/Conference/-/Submission', sort='number:asc')
        assert [submission.number for submission in reviewer_submissions] == [1, 10]

    def test_enable_llm_chat_interaction(self, openreview_client, helpers):

        # group used to sign the responses of the LLM
        openreview_client.post_group_edit(
            invitation='thecvf.com/CVPR/2027/Conference/-/Edit',
            signatures=['thecvf.com/CVPR/2027/Conference'],
            group=openreview.api.Group(
                id='thecvf.com/CVPR/2027/Conference/AI_Review_Assistant',
                readers=['thecvf.com/CVPR/2027/Conference', 'thecvf.com/CVPR/2027/Conference/AI_Review_Assistant'],
                writers=['thecvf.com/CVPR/2027/Conference'],
                signatures=['thecvf.com/CVPR/2027/Conference'],
                signatories=['thecvf.com/CVPR/2027/Conference'],
                members=[]
            )
        )

        assert openreview_client.get_group('thecvf.com/CVPR/2027/Conference/AI_Review_Assistant')

        edit_invitations_builder = openreview.workflows.EditInvitationsBuilder(openreview_client, 'thecvf.com/CVPR/2027/Conference')
        llm_chat_process_script = edit_invitations_builder.get_process_content('workflow_process/llm_chat_process.py')

        # super invitation of the reviewer chats, one per reviewer anonymous group: its date process creates them and
        # they run the process_script stored in its content
        openreview_client.post_invitation_edit(
            invitations='thecvf.com/CVPR/2027/Conference/-/Edit',
            readers=['thecvf.com/CVPR/2027/Conference'],
            writers=['thecvf.com/CVPR/2027/Conference'],
            signatures=['thecvf.com/CVPR/2027/Conference'],
            invitation=openreview.api.Invitation(
                id='thecvf.com/CVPR/2027/Conference/Reviewers/-/LLM_Interaction',
                invitees=['thecvf.com/CVPR/2027/Conference'],
                readers=['thecvf.com/CVPR/2027/Conference'],
                writers=['thecvf.com/CVPR/2027/Conference'],
                signatures=['thecvf.com/CVPR/2027/Conference'],
                description='This step runs automatically at its "activation date", and creates a private chat with an AI assistant for every reviewer assigned to a submission. Configure the LLM gateway and the prompt in "Settings" and the code that answers the messages in "Process".',
                # not active yet, without a cdate the date process would run right away
                cdate=openreview.tools.datetime_millis(datetime.datetime.now() + datetime.timedelta(days=30)),
                date_processes=[{
                    'dates': ['#{4/cdate}'],
                    'script': edit_invitations_builder.get_process_content('workflow_process/llm_chat_invitations_process.py')
                }],
                content={
                    'process_script': {
                        'value': edit_invitations_builder.get_process_content('workflow_process/llm_chat_process.py')
                    },
                    'llm_prompt': {
                        'value': '''You are an AI assistant that helps a reviewer of CVPR 2027 understand the submission they were assigned to review. The submission PDF and its metadata are attached to the first message of the conversation.

- Answer the reviewer's questions based on the submission, pointing to the relevant section, figure, table or page when you can.
- If the submission does not address something, say so instead of guessing.
- Be concise and format your answers with Markdown.
- Do not try to identify the authors of the submission.
- Help the reviewer reason about the paper, but do not write the review or recommend a decision on their behalf.'''
                    },
                    'llm_base_url': {
                        'value': 'https://litellm.openreview.net'
                    },
                    'llm_token_limit': {
                        'value': 1000000
                    }
                },
                edit={
                    'signatures': ['thecvf.com/CVPR/2027/Conference'],
                    'readers': ['thecvf.com/CVPR/2027/Conference'],
                    'writers': ['thecvf.com/CVPR/2027/Conference'],
                    'content': {
                        'noteId': {
                            'value': {
                                'param': {
                                    'type': 'string'
                                }
                            }
                        },
                        'noteNumber': {
                            'value': {
                                'param': {
                                    'type': 'integer'
                                }
                            }
                        },
                        'anonGroupId': {
                            'value': {
                                'param': {
                                    'type': 'string'
                                }
                            }
                        }
                    },
                    'invitation': {
                        'id': '${2/content/anonGroupId/value}/-/LLM_Interaction',
                        # one message at a time: a new message waits for the answer to the previous one
                        'preprocess': edit_invitations_builder.get_process_content('workflow_process/llm_chat_preprocess.py'),
                        'process': '''def process(client, edit, invitation):
    import base64
    import requests

    meta_invitation = client.get_invitation(invitation.invitations[0])
    script = meta_invitation.content['process_script']['value']
    funcs = {
        'openreview': openreview,
        'datetime': datetime,
        'base64': base64,
        'requests': requests
    }
    exec(script, funcs)
    funcs['process'](client, edit, invitation)
''',
                        'invitees': [
                            'thecvf.com/CVPR/2027/Conference/AI_Review_Assistant',
                            '${3/content/anonGroupId/value}'
                        ],
                        'readers': [
                            'thecvf.com/CVPR/2027/Conference',
                            'thecvf.com/CVPR/2027/Conference/AI_Review_Assistant',
                            '${3/content/anonGroupId/value}'
                        ],
                        'writers': ['thecvf.com/CVPR/2027/Conference'],
                        'signatures': ['thecvf.com/CVPR/2027/Conference'],
                        'edit': {
                            'signatures': {
                                'param': {
                                    'items': [
                                        {'value': '${7/content/anonGroupId/value}', 'optional': True},
                                        {'value': 'thecvf.com/CVPR/2027/Conference/AI_Review_Assistant', 'optional': True}
                                    ]
                                }
                            },
                            'readers': [
                                'thecvf.com/CVPR/2027/Conference',
                                'thecvf.com/CVPR/2027/Conference/AI_Review_Assistant',
                                '${4/content/anonGroupId/value}'
                            ],
                            'writers': ['thecvf.com/CVPR/2027/Conference'],
                            # the LLM usage of each answer, readable by the venue only
                            'content': {
                                'tokens': {
                                    'value': {
                                        'param': {
                                            'type': 'integer',
                                            'minimum': 0,
                                            'optional': True
                                        }
                                    },
                                    'readers': ['thecvf.com/CVPR/2027/Conference']
                                },
                                'usage': {
                                    'value': {
                                        'param': {
                                            'type': 'json',
                                            'optional': True
                                        }
                                    },
                                    'readers': ['thecvf.com/CVPR/2027/Conference']
                                },
                                'cost': {
                                    'value': {
                                        'param': {
                                            'type': 'float',
                                            'minimum': 0,
                                            'optional': True
                                        }
                                    },
                                    'readers': ['thecvf.com/CVPR/2027/Conference']
                                }
                            },
                            'note': {
                                'forum': '${4/content/noteId/value}',
                                'replyto': {
                                    'param': {
                                        'withForum': '${6/content/noteId/value}'
                                    }
                                },
                                'signatures': ['${3/signatures}'],
                                'readers': [
                                    'thecvf.com/CVPR/2027/Conference',
                                    'thecvf.com/CVPR/2027/Conference/AI_Review_Assistant',
                                    '${5/content/anonGroupId/value}'
                                ],
                                'writers': ['thecvf.com/CVPR/2027/Conference'],
                                'content': {
                                    'message': {
                                        'order': 1,
                                        'description': 'Message',
                                        'value': {
                                            'param': {
                                                'type': 'string',
                                                'input': 'textarea',
                                                'markdown': True
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            )
        )

        llm_super_invitation = openreview_client.get_invitation('thecvf.com/CVPR/2027/Conference/Reviewers/-/LLM_Interaction')
        assert llm_super_invitation.content['process_script']['value'] == llm_chat_process_script
        default_prompt = llm_super_invitation.content['llm_prompt']['value']
        assert default_prompt.startswith('You are an AI assistant that helps a reviewer of CVPR 2027')
        assert 'llm_api_key' not in llm_super_invitation.content
        assert llm_super_invitation.content['llm_base_url']['value'] == 'https://litellm.openreview.net'
        assert llm_super_invitation.content['llm_token_limit']['value'] == 1000000
        # the reviewers do not get the forum replies
        assert 'llm_reply_invitations' not in llm_super_invitation.content

        # the super invitations of both committees and their edit invitations are not filtered out of the workflow timeline
        domain = openreview_client.get_group('thecvf.com/CVPR/2027/Conference')
        for invitation_id in [f'thecvf.com/CVPR/2027/Conference/{committee}/-/LLM_Interaction{suffix}' for committee in ['Reviewers', 'Area_Chairs'] for suffix in ['', '/Dates', '/Settings', '/Process']]:
            for pattern in domain.content['exclusion_workflow_invitations']['value']:
                if pattern.startswith('/') and pattern.endswith('/'):
                    assert not re.search(pattern[1:-1], invitation_id), f'{invitation_id} is excluded from the timeline by {pattern}'
                else:
                    assert pattern != invitation_id

        # the chats are created when the super invitation is activated
        assert len(openreview_client.get_all_invitations(invitation='thecvf.com/CVPR/2027/Conference/Reviewers/-/LLM_Interaction')) == 0

        # the program chairs activate the chats through the dates invitation; the date process only runs for an
        # activation date in the future, a past date is never scheduled
        edit_invitations_builder.set_edit_dates_one_level_invitation('thecvf.com/CVPR/2027/Conference/Reviewers/-/LLM_Interaction')

        pc_client = openreview.api.OpenReviewClient(username='pc@cvpr.cc', password=helpers.strong_password)
        activation_date = openreview.tools.datetime_millis(datetime.datetime.now() + datetime.timedelta(seconds=5))
        pc_client.post_invitation_edit(
            invitations='thecvf.com/CVPR/2027/Conference/Reviewers/-/LLM_Interaction/Dates',
            content={
                'activation_date': { 'value': activation_date }
            }
        )

        helpers.await_queue_edit(openreview_client, edit_id='thecvf.com/CVPR/2027/Conference/Reviewers/-/LLM_Interaction-0-0', count=1)

        assert openreview_client.get_invitation('thecvf.com/CVPR/2027/Conference/Reviewers/-/LLM_Interaction').cdate == activation_date

        # every assigned reviewer of every submission has a chat
        submissions = openreview_client.get_notes(content={'venueid': 'thecvf.com/CVPR/2027/Conference/Submission'}, sort='number:asc')
        assert len(submissions) == 10

        for submission in submissions:
            reviewers_group = openreview_client.get_group(f'thecvf.com/CVPR/2027/Conference/Submission{submission.number}/Reviewers')
            anon_groups = openreview_client.get_groups(prefix=f'thecvf.com/CVPR/2027/Conference/Submission{submission.number}/Reviewer_')
            assert sorted([anon_group.members[0] for anon_group in anon_groups]) == sorted(reviewers_group.members)

            for anon_group in anon_groups:
                chat_invitation = openreview_client.get_invitation(f'{anon_group.id}/-/LLM_Interaction')
                assert chat_invitation.edit['note']['forum'] == submission.id
                assert chat_invitation.edit['note']['content']['message']['value']['param']['markdown'] == True
                # the LLM usage stored in the edit of each answer is readable by the venue only
                assert chat_invitation.edit['content']['tokens']['readers'] == ['thecvf.com/CVPR/2027/Conference']
                assert chat_invitation.edit['content']['usage']['readers'] == ['thecvf.com/CVPR/2027/Conference']
                assert chat_invitation.edit['content']['cost']['readers'] == ['thecvf.com/CVPR/2027/Conference']

        assert len(openreview_client.get_all_invitations(invitation='thecvf.com/CVPR/2027/Conference/Reviewers/-/LLM_Interaction')) == 26

        # the program chairs configure the LLM gateway through the settings invitation, keeping the default prompt
        edit_invitations_builder.set_edit_llm_chat_settings_invitation('thecvf.com/CVPR/2027/Conference/Reviewers/-/LLM_Interaction')

        pc_client.post_invitation_edit(
            invitations='thecvf.com/CVPR/2027/Conference/Reviewers/-/LLM_Interaction/Settings',
            content={
                'llm_api_key': { 'value': 'sk-test-key' },
                'llm_base_url': { 'value': 'https://litellm.openreview.net' },
                'llm_model': { 'value': 'claude-sonnet-4-6' },
                'llm_prompt': { 'value': default_prompt },
                'llm_token_limit': { 'value': 1000000 }
            }
        )

        llm_super_invitation = openreview_client.get_invitation('thecvf.com/CVPR/2027/Conference/Reviewers/-/LLM_Interaction')
        assert llm_super_invitation.content['llm_api_key'] == { 'value': 'sk-test-key', 'readers': ['thecvf.com/CVPR/2027/Conference'] }
        assert llm_super_invitation.content['llm_base_url']['value'] == 'https://litellm.openreview.net'
        assert llm_super_invitation.content['llm_model']['value'] == 'claude-sonnet-4-6'
        assert llm_super_invitation.content['llm_prompt']['value'] == default_prompt
        assert 'process_script' in llm_super_invitation.content

        # every setting is required, an omitted one would be saved as an unresolved reference
        with pytest.raises(openreview.OpenReviewException, match=r'.*llm_api_key.*'):
            pc_client.post_invitation_edit(
                invitations='thecvf.com/CVPR/2027/Conference/Reviewers/-/LLM_Interaction/Settings',
                content={
                    'llm_prompt': { 'value': 'Another prompt.' }
                }
            )

        # only the gateway models can be selected
        with pytest.raises(openreview.OpenReviewException, match=r'.*must be equal to one of the allowed values.*'):
            pc_client.post_invitation_edit(
                invitations='thecvf.com/CVPR/2027/Conference/Reviewers/-/LLM_Interaction/Settings',
                content={
                    'llm_api_key': { 'value': 'sk-test-key' },
                    'llm_base_url': { 'value': 'https://litellm.openreview.net' },
                    'llm_model': { 'value': 'gpt-4o' },
                    'llm_prompt': { 'value': 'Another prompt.' },
                    'llm_token_limit': { 'value': 1000000 }
                }
            )

        # reviewers can not read the settings
        reviewer_client = openreview.api.OpenReviewClient(username='reviewer1@cvpr.cc', password=helpers.strong_password)
        assert not openreview.tools.get_invitation(reviewer_client, 'thecvf.com/CVPR/2027/Conference/Reviewers/-/LLM_Interaction')

        # the program chairs edit the process script of the chats through the process invitation, the chats
        # read it from the super invitation every time they run
        edit_invitations_builder.set_edit_process_script_invitation('thecvf.com/CVPR/2027/Conference/Reviewers/-/LLM_Interaction')

        assert 'MAX_TOKENS = 16000' in llm_chat_process_script
        edited_process_script = llm_chat_process_script.replace('MAX_TOKENS = 16000', 'MAX_TOKENS = 8000')
        pc_client.post_invitation_edit(
            invitations='thecvf.com/CVPR/2027/Conference/Reviewers/-/LLM_Interaction/Process',
            content={
                'process_script': { 'value': edited_process_script }
            }
        )

        llm_super_invitation = openreview_client.get_invitation('thecvf.com/CVPR/2027/Conference/Reviewers/-/LLM_Interaction')
        assert llm_super_invitation.content['process_script']['value'] == edited_process_script
        assert llm_super_invitation.content['llm_prompt']['value'] == default_prompt

        # restore the original process script
        pc_client.post_invitation_edit(
            invitations='thecvf.com/CVPR/2027/Conference/Reviewers/-/LLM_Interaction/Process',
            content={
                'process_script': { 'value': llm_chat_process_script }
            }
        )
        assert openreview_client.get_invitation('thecvf.com/CVPR/2027/Conference/Reviewers/-/LLM_Interaction').content['process_script']['value'] == llm_chat_process_script

        # super invitation of the area chair chats: the area chairs chat about the submission and the reviews,
        # rebuttals and comments of the forum
        openreview_client.post_invitation_edit(
            invitations='thecvf.com/CVPR/2027/Conference/-/Edit',
            readers=['thecvf.com/CVPR/2027/Conference'],
            writers=['thecvf.com/CVPR/2027/Conference'],
            signatures=['thecvf.com/CVPR/2027/Conference'],
            invitation=openreview.api.Invitation(
                id='thecvf.com/CVPR/2027/Conference/Area_Chairs/-/LLM_Interaction',
                invitees=['thecvf.com/CVPR/2027/Conference'],
                readers=['thecvf.com/CVPR/2027/Conference'],
                writers=['thecvf.com/CVPR/2027/Conference'],
                signatures=['thecvf.com/CVPR/2027/Conference'],
                description='This step runs automatically at its "activation date", and creates a private chat with an AI assistant for every area chair assigned to a submission. Besides the submission, the assistant gets the reviews, rebuttals and comments of the forum that the area chair can read. Configure the LLM gateway and the prompt in "Settings" and the code that answers the messages in "Process".',
                # not active yet, without a cdate the date process would run right away
                cdate=openreview.tools.datetime_millis(datetime.datetime.now() + datetime.timedelta(days=30)),
                date_processes=[{
                    'dates': ['#{4/cdate}'],
                    'script': edit_invitations_builder.get_process_content('workflow_process/llm_chat_invitations_process.py')
                }],
                content={
                    'process_script': {
                        'value': edit_invitations_builder.get_process_content('workflow_process/llm_chat_process.py')
                    },
                    'llm_prompt': {
                        'value': '''You are an AI assistant that helps an area chair of CVPR 2027 assess a submission they oversee and its review record. The submission PDF, its metadata and the reviews, rebuttals and comments of the forum are attached to the first message of the conversation.

- Explain the main strengths and weaknesses raised by each review, and where the reviews agree or disagree.
- Take into account how the authors' rebuttal and the discussion address each critique.
- When reviews disagree, weigh each competing critique against the paper, pointing to the sections, figures, tables or pages that support or contradict it.
- Distinguish factual errors in a review from differences of opinion or emphasis, and say when a criticism is not supported by the paper or when the paper does not address it.
- Point out issues in the submission that none of the reviews mention, if any.
- Be concise and format your answers with Markdown.
- Do not try to identify the authors of the submission or the reviewers.
- Support the area chair's assessment, but do not write the meta-review or recommend a decision on their behalf.'''
                    },
                    'llm_base_url': {
                        'value': 'https://litellm.openreview.net'
                    },
                    'llm_token_limit': {
                        'value': 1000000
                    },
                    # the forum replies of these invitations are sent to the LLM too
                    'llm_reply_invitations': {
                        'value': ['Official_Review', 'Author_Rebuttal', 'Official_Comment']
                    }
                },
                edit={
                    'signatures': ['thecvf.com/CVPR/2027/Conference'],
                    'readers': ['thecvf.com/CVPR/2027/Conference'],
                    'writers': ['thecvf.com/CVPR/2027/Conference'],
                    'content': {
                        'noteId': {
                            'value': {
                                'param': {
                                    'type': 'string'
                                }
                            }
                        },
                        'noteNumber': {
                            'value': {
                                'param': {
                                    'type': 'integer'
                                }
                            }
                        },
                        'anonGroupId': {
                            'value': {
                                'param': {
                                    'type': 'string'
                                }
                            }
                        }
                    },
                    'invitation': {
                        'id': '${2/content/anonGroupId/value}/-/LLM_Interaction',
                        # one message at a time: a new message waits for the answer to the previous one
                        'preprocess': edit_invitations_builder.get_process_content('workflow_process/llm_chat_preprocess.py'),
                        'process': '''def process(client, edit, invitation):
    import base64
    import requests

    meta_invitation = client.get_invitation(invitation.invitations[0])
    script = meta_invitation.content['process_script']['value']
    funcs = {
        'openreview': openreview,
        'datetime': datetime,
        'base64': base64,
        'requests': requests
    }
    exec(script, funcs)
    funcs['process'](client, edit, invitation)
''',
                        'invitees': [
                            'thecvf.com/CVPR/2027/Conference/AI_Review_Assistant',
                            '${3/content/anonGroupId/value}'
                        ],
                        'readers': [
                            'thecvf.com/CVPR/2027/Conference',
                            'thecvf.com/CVPR/2027/Conference/AI_Review_Assistant',
                            '${3/content/anonGroupId/value}'
                        ],
                        'writers': ['thecvf.com/CVPR/2027/Conference'],
                        'signatures': ['thecvf.com/CVPR/2027/Conference'],
                        'edit': {
                            'signatures': {
                                'param': {
                                    'items': [
                                        {'value': '${7/content/anonGroupId/value}', 'optional': True},
                                        {'value': 'thecvf.com/CVPR/2027/Conference/AI_Review_Assistant', 'optional': True}
                                    ]
                                }
                            },
                            'readers': [
                                'thecvf.com/CVPR/2027/Conference',
                                'thecvf.com/CVPR/2027/Conference/AI_Review_Assistant',
                                '${4/content/anonGroupId/value}'
                            ],
                            'writers': ['thecvf.com/CVPR/2027/Conference'],
                            # the LLM usage of each answer, readable by the venue only
                            'content': {
                                'tokens': {
                                    'value': {
                                        'param': {
                                            'type': 'integer',
                                            'minimum': 0,
                                            'optional': True
                                        }
                                    },
                                    'readers': ['thecvf.com/CVPR/2027/Conference']
                                },
                                'usage': {
                                    'value': {
                                        'param': {
                                            'type': 'json',
                                            'optional': True
                                        }
                                    },
                                    'readers': ['thecvf.com/CVPR/2027/Conference']
                                },
                                'cost': {
                                    'value': {
                                        'param': {
                                            'type': 'float',
                                            'minimum': 0,
                                            'optional': True
                                        }
                                    },
                                    'readers': ['thecvf.com/CVPR/2027/Conference']
                                }
                            },
                            'note': {
                                'forum': '${4/content/noteId/value}',
                                'replyto': {
                                    'param': {
                                        'withForum': '${6/content/noteId/value}'
                                    }
                                },
                                'signatures': ['${3/signatures}'],
                                'readers': [
                                    'thecvf.com/CVPR/2027/Conference',
                                    'thecvf.com/CVPR/2027/Conference/AI_Review_Assistant',
                                    '${5/content/anonGroupId/value}'
                                ],
                                'writers': ['thecvf.com/CVPR/2027/Conference'],
                                'content': {
                                    'message': {
                                        'order': 1,
                                        'description': 'Message',
                                        'value': {
                                            'param': {
                                                'type': 'string',
                                                'input': 'textarea',
                                                'markdown': True
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            )
        )

        ac_llm_super_invitation = openreview_client.get_invitation('thecvf.com/CVPR/2027/Conference/Area_Chairs/-/LLM_Interaction')
        assert ac_llm_super_invitation.content['process_script']['value'] == llm_chat_process_script
        ac_default_prompt = ac_llm_super_invitation.content['llm_prompt']['value']
        assert ac_default_prompt.startswith('You are an AI assistant that helps an area chair of CVPR 2027')
        assert ac_llm_super_invitation.content['llm_reply_invitations']['value'] == ['Official_Review', 'Author_Rebuttal', 'Official_Comment']
        assert ac_llm_super_invitation.content['llm_base_url']['value'] == 'https://litellm.openreview.net'
        assert len(openreview_client.get_all_invitations(invitation='thecvf.com/CVPR/2027/Conference/Area_Chairs/-/LLM_Interaction')) == 0

        edit_invitations_builder.set_edit_dates_one_level_invitation('thecvf.com/CVPR/2027/Conference/Area_Chairs/-/LLM_Interaction')
        edit_invitations_builder.set_edit_llm_chat_settings_invitation('thecvf.com/CVPR/2027/Conference/Area_Chairs/-/LLM_Interaction')
        edit_invitations_builder.set_edit_process_script_invitation('thecvf.com/CVPR/2027/Conference/Area_Chairs/-/LLM_Interaction')

        activation_date = openreview.tools.datetime_millis(datetime.datetime.now() + datetime.timedelta(seconds=5))
        pc_client.post_invitation_edit(
            invitations='thecvf.com/CVPR/2027/Conference/Area_Chairs/-/LLM_Interaction/Dates',
            content={
                'activation_date': { 'value': activation_date }
            }
        )

        helpers.await_queue_edit(openreview_client, edit_id='thecvf.com/CVPR/2027/Conference/Area_Chairs/-/LLM_Interaction-0-0', count=1)

        # every assigned area chair of every submission has a chat
        for submission in submissions:
            area_chairs_group = openreview_client.get_group(f'thecvf.com/CVPR/2027/Conference/Submission{submission.number}/Area_Chairs')
            anon_groups = openreview_client.get_groups(prefix=f'thecvf.com/CVPR/2027/Conference/Submission{submission.number}/Area_Chair_')
            assert sorted([anon_group.members[0] for anon_group in anon_groups]) == sorted(area_chairs_group.members)

            for anon_group in anon_groups:
                chat_invitation = openreview_client.get_invitation(f'{anon_group.id}/-/LLM_Interaction')
                assert chat_invitation.edit['note']['forum'] == submission.id
                assert chat_invitation.edit['note']['readers'] == [
                    'thecvf.com/CVPR/2027/Conference',
                    'thecvf.com/CVPR/2027/Conference/AI_Review_Assistant',
                    anon_group.id
                ]

        assert len(openreview_client.get_all_invitations(invitation='thecvf.com/CVPR/2027/Conference/Area_Chairs/-/LLM_Interaction')) == 8

        pc_client.post_invitation_edit(
            invitations='thecvf.com/CVPR/2027/Conference/Area_Chairs/-/LLM_Interaction/Settings',
            content={
                'llm_api_key': { 'value': 'sk-test-key' },
                'llm_base_url': { 'value': 'https://litellm.openreview.net' },
                'llm_model': { 'value': 'claude-sonnet-4-6' },
                'llm_prompt': { 'value': ac_default_prompt },
                'llm_token_limit': { 'value': 1000000 }
            }
        )

        ac_llm_super_invitation = openreview_client.get_invitation('thecvf.com/CVPR/2027/Conference/Area_Chairs/-/LLM_Interaction')
        assert ac_llm_super_invitation.content['llm_api_key'] == { 'value': 'sk-test-key', 'readers': ['thecvf.com/CVPR/2027/Conference'] }
        assert ac_llm_super_invitation.content['llm_prompt']['value'] == ac_default_prompt

        # show the chats in their own forum tab

        openreview_client.post_invitation_edit(
            invitations='thecvf.com/CVPR/2027/Conference/-/Edit',
            signatures=['thecvf.com/CVPR/2027/Conference'],
            invitation=openreview.api.Invitation(
                id='thecvf.com/CVPR/2027/Conference/-/Submission',
                reply_forum_views=[
                    {
                        'id': 'discussion',
                        'label': 'Discussion',
                        'filter': '-invitations:thecvf.com/CVPR/2027/Conference/Submission${note.number}/.*/-/LLM_Interaction',
                        'nesting': 3,
                        'sort': 'date-desc',
                        'layout': 'default',
                        'live': True
                    },
                    {
                        'id': 'llm_interaction',
                        'label': 'LLM Interaction Chat',
                        'filter': 'invitations:thecvf.com/CVPR/2027/Conference/Submission${note.number}/.*/-/LLM_Interaction',
                        'nesting': 1,
                        'sort': 'date-asc',
                        'layout': 'chat',
                        'live': True,
                        'expandedInvitations': ['thecvf.com/CVPR/2027/Conference/Submission${note.number}/.*/-/LLM_Interaction']
                    }
                ]
            )
        )

        submission_invitation = openreview_client.get_invitation('thecvf.com/CVPR/2027/Conference/-/Submission')
        assert [view['id'] for view in submission_invitation.reply_forum_views] == ['discussion', 'llm_interaction']

        # open the review stage together with the chat
        now = datetime.datetime.now()
        review_duedate = openreview.tools.datetime_millis(now + datetime.timedelta(days=14))
        pc_client.post_invitation_edit(
            invitations='thecvf.com/CVPR/2027/Conference/-/Official_Review/Dates',
            content={
                'activation_date': { 'value': openreview.tools.datetime_millis(now) },
                'due_date': { 'value': review_duedate },
                'expiration_date': { 'value': review_duedate }
            }
        )
        helpers.await_queue_edit(openreview_client, edit_id='thecvf.com/CVPR/2027/Conference/-/Official_Review-0-1', count=2)

        assert len(openreview_client.get_all_invitations(invitation='thecvf.com/CVPR/2027/Conference/-/Official_Review')) == 10

        invitation = openreview_client.get_invitation('thecvf.com/CVPR/2027/Conference/Submission2/-/Official_Review')
        assert invitation.duedate == review_duedate
        assert invitation.invitees == [
            'thecvf.com/CVPR/2027/Conference',
            'thecvf.com/CVPR/2027/Conference/Submission2/Reviewers'
        ]
        assert invitation.edit['note']['readers'] == [
            'thecvf.com/CVPR/2027/Conference/Program_Chairs',
            'thecvf.com/CVPR/2027/Conference/Submission2/Senior_Area_Chairs',
            'thecvf.com/CVPR/2027/Conference/Submission2/Area_Chairs',
            '${3/signatures}'
        ]

    def test_submit_reviews(self, openreview_client, helpers):

        # the reviewers of submission 2 disagree, so the area chair chat has competing critiques to assess
        reviews = [
            ('reviewer1@cvpr.cc', '~Reviewer_CVPROne1', 'Clear contribution', 'The method is well motivated and the experiments support the main claims.', 8, 4),
            ('reviewer2@cvpr.cc', '~Reviewer_CVPRTwo1', 'Limited evaluation', 'The evaluation only covers small datasets and the baselines are outdated.', 4, 3),
            ('reviewer3@cvpr.cc', '~Reviewer_CVPRThree1', 'Sound but incremental', 'The approach is sound but the novelty over prior work is limited.', 5, 4)
        ]
        for email, profile_id, title, text, rating, confidence in reviews:
            reviewer_client = openreview.api.OpenReviewClient(username=email, password=helpers.strong_password)
            anon_group_id = reviewer_client.get_groups(prefix='thecvf.com/CVPR/2027/Conference/Submission2/Reviewer_', signatory=profile_id)[0].id
            review_edit = reviewer_client.post_note_edit(
                invitation='thecvf.com/CVPR/2027/Conference/Submission2/-/Official_Review',
                signatures=[anon_group_id],
                note=openreview.api.Note(
                    content={
                        'title': { 'value': title },
                        'review': { 'value': text },
                        'rating': { 'value': rating },
                        'confidence': { 'value': confidence }
                    }
                )
            )
            helpers.await_queue_edit(openreview_client, edit_id=review_edit['id'])

        assert len(openreview_client.get_notes(invitation='thecvf.com/CVPR/2027/Conference/Submission2/-/Official_Review')) == 3

        # the area chair of the submission can read the reviews, so they are passed to the area chair chat
        ac_client = openreview.api.OpenReviewClient(username='ac1@cvpr.cc', password=helpers.strong_password)
        assert len(ac_client.get_notes(invitation='thecvf.com/CVPR/2027/Conference/Submission2/-/Official_Review')) == 3

    def test_llm_chat_messages(self, openreview_client, helpers, llm_mock):

        pc_client = openreview.api.OpenReviewClient(username='pc@cvpr.cc', password=helpers.strong_password)

        def save_settings(committee_name, base_url, token_limit):
            settings = openreview_client.get_invitation(f'thecvf.com/CVPR/2027/Conference/{committee_name}/-/LLM_Interaction').content
            pc_client.post_invitation_edit(
                invitations=f'thecvf.com/CVPR/2027/Conference/{committee_name}/-/LLM_Interaction/Settings',
                content={
                    'llm_api_key': { 'value': settings['llm_api_key']['value'] },
                    'llm_base_url': { 'value': base_url },
                    'llm_model': { 'value': settings['llm_model']['value'] },
                    'llm_prompt': { 'value': settings['llm_prompt']['value'] },
                    'llm_token_limit': { 'value': token_limit }
                }
            )

        def ask(email, profile_id, number, anon_name, question):
            committee_client = openreview.api.OpenReviewClient(username=email, password=helpers.strong_password)
            submission = committee_client.get_notes(invitation='thecvf.com/CVPR/2027/Conference/-/Submission', number=number)[0]
            anon_group_id = committee_client.get_groups(prefix=f'thecvf.com/CVPR/2027/Conference/Submission{number}/{anon_name}', signatory=profile_id)[0].id
            message_edit = committee_client.post_note_edit(
                invitation=f'{anon_group_id}/-/LLM_Interaction',
                signatures=[anon_group_id],
                note=openreview.api.Note(
                    replyto=submission.id,
                    content={
                        'message': { 'value': question }
                    }
                )
            )
            return committee_client, anon_group_id, message_edit

        def get_answer(anon_group_id, message_edit):
            helpers.await_queue_edit(openreview_client, edit_id=message_edit['id'])
            answers = [note for note in openreview_client.get_notes(invitation=f'{anon_group_id}/-/LLM_Interaction') if note.replyto == message_edit['note']['id']]
            assert len(answers) == 1
            assert answers[0].signatures == ['thecvf.com/CVPR/2027/Conference/AI_Review_Assistant']
            return answers[0]

        # the chats talk to the LLM mock during the test
        save_settings('Reviewers', llm_mock['url'], 1000000)
        save_settings('Area_Chairs', llm_mock['url'], 1000000)

        with open(os.path.join(os.path.dirname(__file__), 'data/openreview.pdf'), 'rb') as pdf_file:
            pdf_bytes = pdf_file.read()

        # a reviewer asks about the submission
        reviewer_client, anon_group_id, message_edit = ask('reviewer1@cvpr.cc', '~Reviewer_CVPROne1', 2, 'Reviewer_', 'What are the main contributions of this paper?')
        answer = get_answer(anon_group_id, message_edit)
        assert answer.content['message']['value'] == 'Answer from the LLM mock to: What are the main contributions of this paper?'

        # the LLM gets the prompt, the PDF, the metadata visible to the reviewer and the question, but not the forum replies
        request = llm_mock['requests'][-1]
        assert request['path'] == '/v1/messages'
        assert request['authorization'] == 'Bearer sk-test-key'
        assert request['body']['model'] == 'claude-sonnet-4-6'
        assert request['body']['system'].startswith('You are an AI assistant that helps a reviewer of CVPR 2027')
        assert len(request['body']['messages']) == 1
        pdf_block, metadata_block, question_block = request['body']['messages'][0]['content']
        assert base64.b64decode(pdf_block['source']['data']) == pdf_bytes
        assert 'Title: Paper title 2' in metadata_block['text']
        assert 'SomeFirstName' not in metadata_block['text']
        assert 'Kai' not in metadata_block['text']
        assert question_block['text'] == 'What are the main contributions of this paper?'

        # the edit of the answer stores the LLM usage and cost, readable by the venue only
        answer_edit = openreview_client.get_note_edits(note_id=answer.id)[0]
        assert answer_edit.content['tokens']['value'] == 120
        assert answer_edit.content['usage']['value']['model'] == 'claude-sonnet-4-6'
        assert answer_edit.content['usage']['value']['input_tokens'] == 100
        assert answer_edit.content['usage']['value']['output_tokens'] == 20
        # the cost in USD reported by the gateway headers
        assert answer_edit.content['cost']['value'] == 0.0021
        assert reviewer_client.get_note_edits(note_id=answer.id)[0].content is None

        # one message at a time: a new message has to wait for the answer to the previous one
        _, _, slow_message_edit = ask('reviewer1@cvpr.cc', '~Reviewer_CVPROne1', 2, 'Reviewer_', 'Explain the method step by step [slow]')
        with pytest.raises(openreview.OpenReviewException, match=r'Please wait for the answer to your previous message'):
            ask('reviewer1@cvpr.cc', '~Reviewer_CVPROne1', 2, 'Reviewer_', 'And the limitations?')
        get_answer(anon_group_id, slow_message_edit)

        # the chat history goes with the new message
        assert [message['role'] for message in llm_mock['requests'][-1]['body']['messages']] == ['user', 'assistant', 'user']

        # the chat reaches its token limit after the two answers
        save_settings('Reviewers', llm_mock['url'], 240)
        requests_count = len(llm_mock['requests'])
        _, _, message_edit = ask('reviewer1@cvpr.cc', '~Reviewer_CVPROne1', 2, 'Reviewer_', 'And the limitations?')
        answer = get_answer(anon_group_id, message_edit)
        assert answer.content['message']['value'] == 'You have reached the usage limit of the AI assistant for this submission. Please contact the program chairs if you need to continue.'
        assert len(llm_mock['requests']) == requests_count

        # the limit is per chat, the reviewer can still ask about another submission
        _, other_anon_group_id, message_edit = ask('reviewer1@cvpr.cc', '~Reviewer_CVPROne1', 4, 'Reviewer_', 'What are the main contributions of this paper?')
        answer = get_answer(other_anon_group_id, message_edit)
        assert answer.content['message']['value'] == 'Answer from the LLM mock to: What are the main contributions of this paper?'
        save_settings('Reviewers', llm_mock['url'], 1000000)

        # the area chair gets the reviews of the forum too
        _, ac_anon_group_id, message_edit = ask('ac1@cvpr.cc', '~AC_CVPROne1', 2, 'Area_Chair_', 'Which critique is best supported by the paper?')
        answer = get_answer(ac_anon_group_id, message_edit)
        assert answer.content['message']['value'] == 'Answer from the LLM mock to: Which critique is best supported by the paper?'

        request = llm_mock['requests'][-1]
        assert request['body']['system'].startswith('You are an AI assistant that helps an area chair of CVPR 2027')
        pdf_block, metadata_block, replies_block, question_block = request['body']['messages'][0]['content']
        assert base64.b64decode(pdf_block['source']['data']) == pdf_bytes
        assert replies_block['text'].startswith('Forum replies:')
        assert replies_block['text'].count('Official Review by Reviewer_') == 3
        assert 'Limited evaluation' in replies_block['text']
        # the chats of the reviewers are not part of the forum replies
        assert 'Answer from the LLM mock' not in replies_block['text']
        assert 'cache_control' in replies_block
        assert question_block['text'] == 'Which critique is best supported by the paper?'

        # point the chats back to the LLM gateway
        save_settings('Reviewers', 'https://litellm.openreview.net', 1000000)
        save_settings('Area_Chairs', 'https://litellm.openreview.net', 1000000)

    def test_llm_chat_tab_visible(self, openreview_client, helpers, selenium, request_page):

        for email in ['reviewer1@cvpr.cc', 'reviewer2@cvpr.cc', 'reviewer3@cvpr.cc', 'reviewer4@cvpr.cc', 'reviewer5@cvpr.cc', 'reviewer6@cvpr.cc', 'reviewer7@gmail.com', 'ac1@cvpr.cc', 'ac2@cvpr.cc']:
            committee_client = openreview.api.OpenReviewClient(username=email, password=helpers.strong_password)
            submission = committee_client.get_notes(invitation='thecvf.com/CVPR/2027/Conference/-/Submission', sort='number:asc')[0]

            request_page(
                selenium,
                'http://localhost:3030/forum?id=' + submission.id,
                committee_client,
                by=By.LINK_TEXT,
                wait_for_element='LLM Interaction Chat'
            )
            assert selenium.find_element(By.LINK_TEXT, 'LLM Interaction Chat')
