import datetime
import os
import openreview
import pytest
from selenium.webdriver.common.by import By

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

    def test_release_submissions_to_assigned_committee(self, openreview_client, helpers):

        pc_client = openreview.api.OpenReviewClient(username='pc@cvpr.cc', password=helpers.strong_password)

        now = datetime.datetime.now()
        pc_client.post_invitation_edit(
            invitations='thecvf.com/CVPR/2027/Conference/-/Submission_Change_Before_Reviewing/Dates',
            content={
                'activation_date': { 'value': openreview.tools.datetime_millis(now) }
            }
        )

        helpers.await_queue_edit(openreview_client, 'thecvf.com/CVPR/2027/Conference/-/Submission_Change_Before_Reviewing-0-1', count=3)

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

        # super invitation of the chats, one per reviewer anonymous group: its date process creates them and
        # they run the process_script stored in its content
        edit_invitations_builder = openreview.workflows.EditInvitationsBuilder(openreview_client, 'thecvf.com/CVPR/2027/Conference')
        llm_chat_process_script = edit_invitations_builder.get_process_content('workflow_process/llm_chat_process.py')
        openreview_client.post_invitation_edit(
            invitations='thecvf.com/CVPR/2027/Conference/-/Edit',
            readers=['thecvf.com/CVPR/2027/Conference'],
            writers=['thecvf.com/CVPR/2027/Conference'],
            signatures=['thecvf.com/CVPR/2027/Conference'],
            invitation=openreview.api.Invitation(
                id='thecvf.com/CVPR/2027/Conference/-/LLM_Interaction',
                invitees=['thecvf.com/CVPR/2027/Conference'],
                readers=['thecvf.com/CVPR/2027/Conference'],
                writers=['thecvf.com/CVPR/2027/Conference'],
                signatures=['thecvf.com/CVPR/2027/Conference'],
                # not active yet, without a cdate the date process would run right away
                cdate=openreview.tools.datetime_millis(datetime.datetime.now() + datetime.timedelta(days=30)),
                date_processes=[{
                    'dates': ['#{4/cdate}'],
                    'script': edit_invitations_builder.get_process_content('workflow_process/llm_chat_invitations_process.py')
                }],
                content={
                    'process_script': {
                        'value': llm_chat_process_script
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

        llm_super_invitation = openreview_client.get_invitation('thecvf.com/CVPR/2027/Conference/-/LLM_Interaction')
        assert llm_super_invitation.content['process_script']['value'] == llm_chat_process_script
        default_prompt = llm_super_invitation.content['llm_prompt']['value']
        assert default_prompt.startswith('You are an AI assistant that helps a reviewer of CVPR 2027')
        assert 'llm_api_key' not in llm_super_invitation.content
        assert llm_super_invitation.content['llm_base_url']['value'] == 'https://litellm.openreview.net'

        # the chats are created when the super invitation is activated
        assert len(openreview_client.get_all_invitations(invitation='thecvf.com/CVPR/2027/Conference/-/LLM_Interaction')) == 0

        # the program chairs activate the chats through the dates invitation; the date process only runs for an
        # activation date in the future, a past date is never scheduled
        edit_invitations_builder.set_edit_dates_one_level_invitation('thecvf.com/CVPR/2027/Conference/-/LLM_Interaction')

        pc_client = openreview.api.OpenReviewClient(username='pc@cvpr.cc', password=helpers.strong_password)
        activation_date = openreview.tools.datetime_millis(datetime.datetime.now() + datetime.timedelta(seconds=5))
        pc_client.post_invitation_edit(
            invitations='thecvf.com/CVPR/2027/Conference/-/LLM_Interaction/Dates',
            content={
                'activation_date': { 'value': activation_date }
            }
        )

        helpers.await_queue_edit(openreview_client, edit_id='thecvf.com/CVPR/2027/Conference/-/LLM_Interaction-0-0', count=1)

        assert openreview_client.get_invitation('thecvf.com/CVPR/2027/Conference/-/LLM_Interaction').cdate == activation_date

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

        assert len(openreview_client.get_all_invitations(invitation='thecvf.com/CVPR/2027/Conference/-/LLM_Interaction')) == 26

        # the program chairs configure the LLM gateway through the settings invitation, keeping the default prompt
        edit_invitations_builder.set_edit_llm_chat_settings_invitation('thecvf.com/CVPR/2027/Conference/-/LLM_Interaction')

        pc_client.post_invitation_edit(
            invitations='thecvf.com/CVPR/2027/Conference/-/LLM_Interaction/Settings',
            content={
                'llm_api_key': { 'value': 'sk-test-key' },
                'llm_base_url': { 'value': 'https://litellm.openreview.net' },
                'llm_model': { 'value': 'claude-sonnet-4-6' },
                'llm_prompt': { 'value': default_prompt }
            }
        )

        llm_super_invitation = openreview_client.get_invitation('thecvf.com/CVPR/2027/Conference/-/LLM_Interaction')
        assert llm_super_invitation.content['llm_api_key'] == { 'value': 'sk-test-key', 'readers': ['thecvf.com/CVPR/2027/Conference'] }
        assert llm_super_invitation.content['llm_base_url']['value'] == 'https://litellm.openreview.net'
        assert llm_super_invitation.content['llm_model']['value'] == 'claude-sonnet-4-6'
        assert llm_super_invitation.content['llm_prompt']['value'] == default_prompt
        assert 'process_script' in llm_super_invitation.content

        # every setting is required, an omitted one would be saved as an unresolved reference
        with pytest.raises(openreview.OpenReviewException, match=r'.*llm_api_key.*'):
            pc_client.post_invitation_edit(
                invitations='thecvf.com/CVPR/2027/Conference/-/LLM_Interaction/Settings',
                content={
                    'llm_prompt': { 'value': 'Another prompt.' }
                }
            )

        # only the gateway models can be selected
        with pytest.raises(openreview.OpenReviewException, match=r'.*must be equal to one of the allowed values.*'):
            pc_client.post_invitation_edit(
                invitations='thecvf.com/CVPR/2027/Conference/-/LLM_Interaction/Settings',
                content={
                    'llm_api_key': { 'value': 'sk-test-key' },
                    'llm_base_url': { 'value': 'https://litellm.openreview.net' },
                    'llm_model': { 'value': 'gpt-4o' },
                    'llm_prompt': { 'value': 'Another prompt.' }
                }
            )

        # reviewers can not read the settings
        reviewer_client = openreview.api.OpenReviewClient(username='reviewer1@cvpr.cc', password=helpers.strong_password)
        assert not openreview.tools.get_invitation(reviewer_client, 'thecvf.com/CVPR/2027/Conference/-/LLM_Interaction')

        # the program chairs edit the process script of the chats through the process invitation, the chats
        # read it from the super invitation every time they run
        edit_invitations_builder.set_edit_process_script_invitation('thecvf.com/CVPR/2027/Conference/-/LLM_Interaction')

        assert 'MAX_TOKENS = 16000' in llm_chat_process_script
        edited_process_script = llm_chat_process_script.replace('MAX_TOKENS = 16000', 'MAX_TOKENS = 8000')
        pc_client.post_invitation_edit(
            invitations='thecvf.com/CVPR/2027/Conference/-/LLM_Interaction/Process',
            content={
                'process_script': { 'value': edited_process_script }
            }
        )

        llm_super_invitation = openreview_client.get_invitation('thecvf.com/CVPR/2027/Conference/-/LLM_Interaction')
        assert llm_super_invitation.content['process_script']['value'] == edited_process_script
        assert llm_super_invitation.content['llm_prompt']['value'] == default_prompt

        # restore the original process script
        pc_client.post_invitation_edit(
            invitations='thecvf.com/CVPR/2027/Conference/-/LLM_Interaction/Process',
            content={
                'process_script': { 'value': llm_chat_process_script }
            }
        )
        assert openreview_client.get_invitation('thecvf.com/CVPR/2027/Conference/-/LLM_Interaction').content['process_script']['value'] == llm_chat_process_script

        # show the chat in its own forum tab
        openreview_client.post_invitation_edit(
            invitations='thecvf.com/CVPR/2027/Conference/-/Edit',
            signatures=['thecvf.com/CVPR/2027/Conference'],
            invitation=openreview.api.Invitation(
                id='thecvf.com/CVPR/2027/Conference/-/Submission',
                reply_forum_views=[
                    {
                        'id': 'discussion',
                        'label': 'Discussion',
                        'filter': '-invitations:thecvf.com/CVPR/2027/Conference/Submission${note.number}/Reviewer_.*/-/LLM_Interaction',
                        'nesting': 3,
                        'sort': 'date-desc',
                        'layout': 'default',
                        'live': True
                    },
                    {
                        'id': 'llm_interaction',
                        'label': 'LLM Interaction Chat',
                        'filter': 'invitations:thecvf.com/CVPR/2027/Conference/Submission${note.number}/Reviewer_.*/-/LLM_Interaction',
                        'nesting': 1,
                        'sort': 'date-asc',
                        'layout': 'chat',
                        'live': True,
                        'expandedInvitations': ['thecvf.com/CVPR/2027/Conference/Submission${note.number}/Reviewer_.*/-/LLM_Interaction']
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

    def test_llm_chat_tab_visible(self, openreview_client, helpers, selenium, request_page):

        for email in ['reviewer1@cvpr.cc', 'reviewer2@cvpr.cc', 'reviewer3@cvpr.cc', 'reviewer4@cvpr.cc', 'reviewer5@cvpr.cc', 'reviewer6@cvpr.cc', 'reviewer7@gmail.com']:
            reviewer_client = openreview.api.OpenReviewClient(username=email, password=helpers.strong_password)
            submission = reviewer_client.get_notes(invitation='thecvf.com/CVPR/2027/Conference/-/Submission', sort='number:asc')[0]

            request_page(
                selenium,
                'http://localhost:3030/forum?id=' + submission.id,
                reviewer_client,
                by=By.LINK_TEXT,
                wait_for_element='LLM Interaction Chat'
            )
            assert selenium.find_element(By.LINK_TEXT, 'LLM Interaction Chat')
