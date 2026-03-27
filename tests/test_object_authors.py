"""
Setup data for testing object authors with institutions (openreview-web PR #2523).

Creates an ICLR 2025 venue where the Submission invitation uses the author{} type
for the authors field, with institution support. Papers are submitted with both
object authors (fullname, username, institutions) and traditional authorids.

Run:
    pytest tests/test_object_authors.py -v -s
"""

import openreview
import pytest
import datetime


class TestObjectAuthors():

    venue_id = 'ICLR.cc/2025/Conference'

    def test_create_conference(self, client, openreview_client, helpers):

        now = datetime.datetime.now()
        abstract_date = now + datetime.timedelta(days=1)
        due_date = now + datetime.timedelta(days=3)

        # Create users
        helpers.create_user('pc@iclr25.cc', 'Program', 'OAChair')
        helpers.create_user('sac1@iclr25.cc', 'SeniorAC', 'OAOne', institution='umass.edu')
        helpers.create_user('ac1@iclr25.cc', 'AreaChair', 'OAOne', institution='mit.edu')
        helpers.create_user('ac2@iclr25.cc', 'AreaChair', 'OATwo', institution='stanford.edu')
        helpers.create_user('reviewer1@iclr25.cc', 'Reviewer', 'OAOne', institution='google.com')
        helpers.create_user('reviewer2@iclr25.cc', 'Reviewer', 'OATwo', institution='deepmind.com')
        helpers.create_user('reviewer3@iclr25.cc', 'Reviewer', 'OAThree', institution='meta.com')
        helpers.create_user('author1@iclr25.cc', 'Alice', 'Chen', institution='mit.edu')
        helpers.create_user('author2@iclr25.cc', 'Bob', 'Martinez', institution='stanford.edu')
        helpers.create_user('author3@iclr25.cc', 'Carol', 'Patel', institution='oxford.ac.uk')

        pc_client = openreview.Client(username='pc@iclr25.cc', password=helpers.strong_password)

        request_form_note = pc_client.post_note(openreview.Note(
            invitation='openreview.net/Support/-/Request_Form',
            signatures=['~Program_OAChair1'],
            readers=[
                'openreview.net/Support',
                '~Program_OAChair1'
            ],
            writers=[],
            content={
                'title': 'International Conference on Learning Representations',
                'Official Venue Name': 'International Conference on Learning Representations',
                'Abbreviated Venue Name': 'ICLR 2025',
                'Official Website URL': 'https://iclr.cc',
                'program_chair_emails': ['pc@iclr25.cc'],
                'contact_email': 'pc@iclr25.cc',
                'publication_chairs': 'No, our venue does not have Publication Chairs',
                'Area Chairs (Metareviewers)': 'Yes, our venue has Area Chairs',
                'senior_area_chairs': 'Yes, our venue has Senior Area Chairs',
                'ethics_chairs_and_reviewers': 'No, our venue does not have Ethics Chairs and Reviewers',
                'Venue Start Date': '2025/07/01',
                'abstract_registration_deadline': abstract_date.strftime('%Y/%m/%d'),
                'Submission Deadline': due_date.strftime('%Y/%m/%d'),
                'Location': 'Vienna, Austria',
                'submission_reviewer_assignment': 'Automatic',
                'Author and Reviewer Anonymity': 'Double-blind',
                'reviewer_identity': ['Program Chairs', 'Assigned Senior Area Chair', 'Assigned Area Chair', 'Assigned Reviewers'],
                'area_chair_identity': ['Program Chairs', 'Assigned Senior Area Chair', 'Assigned Area Chair', 'Assigned Reviewers'],
                'senior_area_chair_identity': ['Program Chairs', 'Assigned Senior Area Chair', 'Assigned Area Chair', 'Assigned Reviewers'],
                'Open Reviewing Policy': 'Submissions and reviews should both be public.',
                'submission_readers': 'Everyone (submissions are public)',
                'withdrawn_submissions_visibility': 'Yes, withdrawn submissions should be made public.',
                'withdrawn_submissions_author_anonymity': 'Yes, author identities of withdrawn submissions should be revealed.',
                'desk_rejected_submissions_visibility': 'No, desk rejected submissions should not be made public.',
                'desk_rejected_submissions_author_anonymity': 'No, author identities of desk rejected submissions should not be revealed.',
                'How did you hear about us?': 'ML conferences',
                'Expected Submissions': '100',
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

        # Deploy venue
        client.post_note(openreview.Note(
            content={'venue_id': 'ICLR.cc/2025/Conference'},
            forum=request_form_note.forum,
            invitation='openreview.net/Support/-/Request{}/Deploy'.format(request_form_note.number),
            readers=['openreview.net/Support'],
            referent=request_form_note.forum,
            replyto=request_form_note.forum,
            signatures=['openreview.net/Support'],
            writers=['openreview.net/Support']
        ))

        helpers.await_queue()

        assert openreview_client.get_group('ICLR.cc/2025/Conference')
        assert openreview_client.get_group('ICLR.cc/2025/Conference/Senior_Area_Chairs')
        assert openreview_client.get_group('ICLR.cc/2025/Conference/Area_Chairs')
        assert openreview_client.get_group('ICLR.cc/2025/Conference/Reviewers')
        assert openreview_client.get_group('ICLR.cc/2025/Conference/Authors')

    def test_update_profiles_with_institutions(self, openreview_client, helpers):
        """Add detailed institution history (with names) to author profiles."""

        profiles_data = {
            'author1@iclr25.cc': [
                {
                    'position': 'PhD Student',
                    'start': 2020,
                    'end': None,
                    'institution': {
                        'name': 'Massachusetts Institute of Technology',
                        'domain': 'mit.edu',
                        'country': 'US'
                    }
                },
                {
                    'position': 'Research Intern',
                    'start': 2023,
                    'end': 2023,
                    'institution': {
                        'name': 'Google DeepMind',
                        'domain': 'deepmind.com',
                        'country': 'GB'
                    }
                }
            ],
            'author2@iclr25.cc': [
                {
                    'position': 'Assistant Professor',
                    'start': 2022,
                    'end': None,
                    'institution': {
                        'name': 'Stanford University',
                        'domain': 'stanford.edu',
                        'country': 'US'
                    }
                },
                {
                    'position': 'Postdoctoral Researcher',
                    'start': 2020,
                    'end': 2022,
                    'institution': {
                        'name': 'University of California, Berkeley',
                        'domain': 'berkeley.edu',
                        'country': 'US'
                    }
                }
            ],
            'author3@iclr25.cc': [
                {
                    'position': 'Research Fellow',
                    'start': 2021,
                    'end': None,
                    'institution': {
                        'name': 'University of Oxford',
                        'domain': 'oxford.ac.uk',
                        'country': 'GB'
                    }
                },
                {
                    'position': 'Visiting Researcher',
                    'start': 2024,
                    'end': None,
                    'institution': {
                        'name': 'Max Planck Institute for Informatics',
                        'domain': 'mpi-inf.mpg.de',
                        'country': 'DE'
                    }
                }
            ]
        }

        for email, history in profiles_data.items():
            profile = openreview.tools.get_profile(openreview_client, email)
            profile.content['history'] = history
            openreview_client.post_profile(profile)

    def test_modify_submission_invitation(self, openreview_client, helpers):
        """Modify the Submission invitation to use author{} type with institution properties."""

        invitation = openreview_client.get_invitation('ICLR.cc/2025/Conference/-/Submission')

        # Change authors from string[] to author{} with institution properties.
        # Keep authorids intact so venue processes (author groups, readers, etc.) still work.
        invitation.edit['note']['content']['authors'] = {
            'order': 2,
            'description': 'List of authors with institution information.',
            'value': {
                'param': {
                    'type': 'author{}',
                    'properties': {
                        'fullname': {
                            'param': {
                                'type': 'string'
                            }
                        },
                        'username': {
                            'param': {
                                'type': 'string'
                            }
                        },
                        'institutions': {
                            'param': {
                                'type': 'object{}',
                                'optional': True,
                                'properties': {
                                    'name': {
                                        'param': {
                                            'type': 'string'
                                        }
                                    },
                                    'domain': {
                                        'param': {
                                            'type': 'string'
                                        }
                                    },
                                    'country': {
                                        'param': {
                                            'type': 'string'
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }

        openreview_client.post_invitation_edit(
            invitations='ICLR.cc/2025/Conference/-/Edit',
            readers=['ICLR.cc/2025/Conference'],
            writers=['ICLR.cc/2025/Conference'],
            signatures=['ICLR.cc/2025/Conference'],
            invitation=invitation
        )

        updated_inv = openreview_client.get_invitation('ICLR.cc/2025/Conference/-/Submission')
        assert updated_inv.edit['note']['content']['authors']['value']['param']['type'] == 'author{}'
        assert 'authorids' in updated_inv.edit['note']['content']

    def test_submissions(self, openreview_client, helpers):
        """Submit 5 papers with object authors (including institutions) and traditional authorids."""

        alice_client = openreview.api.OpenReviewClient(username='author1@iclr25.cc', password=helpers.strong_password)

        alice_profile = openreview.tools.get_profile(openreview_client, 'author1@iclr25.cc')
        bob_profile = openreview.tools.get_profile(openreview_client, 'author2@iclr25.cc')
        carol_profile = openreview.tools.get_profile(openreview_client, 'author3@iclr25.cc')

        alice_id = alice_profile.id
        bob_id = bob_profile.id
        carol_id = carol_profile.id

        papers = [
            {
                'title': 'Attention-Based Learning for Protein Folding',
                'abstract': 'We propose a novel attention mechanism for predicting protein structures with state-of-the-art accuracy on standard benchmarks.',
                'authors': [
                    {'fullname': 'Alice Chen', 'username': alice_id,
                     'institutions': [{'name': 'Massachusetts Institute of Technology', 'domain': 'mit.edu', 'country': 'US'}]},
                    {'fullname': 'Bob Martinez', 'username': bob_id,
                     'institutions': [{'name': 'Stanford University', 'domain': 'stanford.edu', 'country': 'US'}]},
                ],
                'authorids': [alice_id, bob_id],
                'keywords': ['attention', 'protein folding', 'structural biology'],
            },
            {
                'title': 'Scaling Laws for Multilingual Language Models',
                'abstract': 'We study the scaling behavior of transformer-based language models across 100+ languages and establish new scaling laws.',
                'authors': [
                    {'fullname': 'Bob Martinez', 'username': bob_id,
                     'institutions': [{'name': 'Stanford University', 'domain': 'stanford.edu', 'country': 'US'}]},
                    {'fullname': 'Carol Patel', 'username': carol_id,
                     'institutions': [
                         {'name': 'University of Oxford', 'domain': 'oxford.ac.uk', 'country': 'GB'},
                         {'name': 'Max Planck Institute for Informatics', 'domain': 'mpi-inf.mpg.de', 'country': 'DE'},
                     ]},
                    {'fullname': 'Alice Chen', 'username': alice_id,
                     'institutions': [{'name': 'Massachusetts Institute of Technology', 'domain': 'mit.edu', 'country': 'US'}]},
                ],
                'authorids': [bob_id, carol_id, alice_id],
                'keywords': ['scaling laws', 'multilingual', 'language models'],
            },
            {
                'title': 'Reinforcement Learning from Human Feedback in Robotics',
                'abstract': 'We apply RLHF techniques to robotic manipulation tasks, demonstrating improved sample efficiency over prior methods.',
                'authors': [
                    {'fullname': 'Carol Patel', 'username': carol_id,
                     'institutions': [{'name': 'University of Oxford', 'domain': 'oxford.ac.uk', 'country': 'GB'}]},
                    {'fullname': 'Alice Chen', 'username': alice_id,
                     'institutions': [{'name': 'Massachusetts Institute of Technology', 'domain': 'mit.edu', 'country': 'US'}]},
                ],
                'authorids': [carol_id, alice_id],
                'keywords': ['reinforcement learning', 'RLHF', 'robotics'],
            },
            {
                # Paper with no institutions on some authors
                'title': 'Graph Neural Networks for Combinatorial Optimization',
                'abstract': 'A novel GNN architecture for solving combinatorial optimization problems with provable approximation guarantees.',
                'authors': [
                    {'fullname': 'Alice Chen', 'username': alice_id},
                    {'fullname': 'Bob Martinez', 'username': bob_id,
                     'institutions': [{'name': 'Stanford University', 'domain': 'stanford.edu', 'country': 'US'}]},
                    {'fullname': 'Carol Patel', 'username': carol_id},
                ],
                'authorids': [alice_id, bob_id, carol_id],
                'keywords': ['graph neural networks', 'combinatorial optimization'],
            },
            {
                # Single-author paper with multiple affiliations
                'title': 'Diffusion Models for Scientific Discovery',
                'abstract': 'We extend diffusion models to molecular generation and materials design, achieving new state-of-the-art results.',
                'authors': [
                    {'fullname': 'Bob Martinez', 'username': bob_id,
                     'institutions': [
                         {'name': 'Stanford University', 'domain': 'stanford.edu', 'country': 'US'},
                         {'name': 'University of California, Berkeley', 'domain': 'berkeley.edu', 'country': 'US'},
                     ]},
                ],
                'authorids': [bob_id],
                'keywords': ['diffusion models', 'molecular generation', 'scientific discovery'],
            },
        ]

        for paper in papers:
            note = openreview.api.Note(
                license='CC BY 4.0',
                content={
                    'title': {'value': paper['title']},
                    'abstract': {'value': paper['abstract']},
                    'authors': {'value': paper['authors']},
                    'authorids': {'value': paper['authorids']},
                    'keywords': {'value': paper['keywords']},
                    'pdf': {'value': '/pdf/' + 'p' * 40 + '.pdf'},
                }
            )
            alice_client.post_note_edit(
                invitation='ICLR.cc/2025/Conference/-/Submission',
                signatures=[alice_id],
                note=note
            )

        helpers.await_queue_edit(openreview_client, invitation='ICLR.cc/2025/Conference/-/Submission', count=5)

        submissions = openreview_client.get_notes(invitation='ICLR.cc/2025/Conference/-/Submission', sort='number:asc')
        assert len(submissions) == 5
        # Verify first paper has object authors
        assert isinstance(submissions[0].content['authors']['value'][0], dict)
        assert 'fullname' in submissions[0].content['authors']['value'][0]
        assert 'username' in submissions[0].content['authors']['value'][0]

    def test_post_submission(self, client, openreview_client, helpers):
        """Close submissions and run post-submission processing."""

        pc_client = openreview.Client(username='pc@iclr25.cc', password=helpers.strong_password)
        request_form = pc_client.get_notes(invitation='openreview.net/Support/-/Request_Form')[0]

        # Close abstract submission
        now = datetime.datetime.now()
        abstract_date = now - datetime.timedelta(minutes=28)
        due_date = now + datetime.timedelta(days=3)
        start_date = now - datetime.timedelta(days=2)

        pc_client.post_note(openreview.Note(
            content={
                'title': 'International Conference on Learning Representations',
                'Official Venue Name': 'International Conference on Learning Representations',
                'Abbreviated Venue Name': 'ICLR 2025',
                'Official Website URL': 'https://iclr.cc',
                'program_chair_emails': ['pc@iclr25.cc'],
                'contact_email': 'pc@iclr25.cc',
                'publication_chairs': 'No, our venue does not have Publication Chairs',
                'Venue Start Date': '2025/07/01',
                'abstract_registration_deadline': abstract_date.strftime('%Y/%m/%d'),
                'Submission Deadline': due_date.strftime('%Y/%m/%d'),
                'Submission Start Date': start_date.strftime('%Y/%m/%d'),
                'Location': 'Vienna, Austria',
                'submission_reviewer_assignment': 'Automatic',
                'How did you hear about us?': 'ML conferences',
                'Expected Submissions': '100',
            },
            forum=request_form.forum,
            invitation='openreview.net/Support/-/Request{}/Revision'.format(request_form.number),
            readers=['ICLR.cc/2025/Conference/Program_Chairs', 'openreview.net/Support'],
            referent=request_form.forum,
            replyto=request_form.forum,
            signatures=['~Program_OAChair1'],
            writers=[]
        ))

        helpers.await_queue()
        helpers.await_queue_edit(openreview_client, 'ICLR.cc/2025/Conference/-/Post_Submission-0-1', count=2)
        helpers.await_queue_edit(openreview_client, 'ICLR.cc/2025/Conference/-/Withdrawal-0-1', count=1)
        helpers.await_queue_edit(openreview_client, 'ICLR.cc/2025/Conference/-/Desk_Rejection-0-1', count=1)

        # Close full paper submission
        now = datetime.datetime.now()
        abstract_date = now - datetime.timedelta(days=2)
        due_date = now - datetime.timedelta(minutes=28)

        pc_client.post_note(openreview.Note(
            content={
                'title': 'International Conference on Learning Representations',
                'Official Venue Name': 'International Conference on Learning Representations',
                'Abbreviated Venue Name': 'ICLR 2025',
                'Official Website URL': 'https://iclr.cc',
                'program_chair_emails': ['pc@iclr25.cc'],
                'contact_email': 'pc@iclr25.cc',
                'publication_chairs': 'No, our venue does not have Publication Chairs',
                'Venue Start Date': '2025/07/01',
                'abstract_registration_deadline': abstract_date.strftime('%Y/%m/%d'),
                'Submission Deadline': due_date.strftime('%Y/%m/%d'),
                'Submission Start Date': start_date.strftime('%Y/%m/%d'),
                'Location': 'Vienna, Austria',
                'submission_reviewer_assignment': 'Automatic',
                'How did you hear about us?': 'ML conferences',
                'Expected Submissions': '100',
            },
            forum=request_form.forum,
            invitation='openreview.net/Support/-/Request{}/Revision'.format(request_form.number),
            readers=['ICLR.cc/2025/Conference/Program_Chairs', 'openreview.net/Support'],
            referent=request_form.forum,
            replyto=request_form.forum,
            signatures=['~Program_OAChair1'],
            writers=[]
        ))

        helpers.await_queue()
        helpers.await_queue_edit(openreview_client, 'ICLR.cc/2025/Conference/-/Post_Submission-0-1', count=3)
        helpers.await_queue_edit(openreview_client, 'ICLR.cc/2025/Conference/-/Withdrawal-0-1', count=2)
        helpers.await_queue_edit(openreview_client, 'ICLR.cc/2025/Conference/-/Desk_Rejection-0-1', count=3)
        helpers.await_queue_edit(openreview_client, 'ICLR.cc/2025/Conference/-/Full_Submission-0-1', count=3)

        submissions = openreview_client.get_notes(invitation='ICLR.cc/2025/Conference/-/Submission', sort='number:asc')
        assert len(submissions) == 5
        assert submissions[0].readers == ['everyone']

    def test_setup_committee(self, openreview_client, helpers):
        """Add SACs, ACs, and reviewers to groups and assign to papers."""

        openreview_client.add_members_to_group('ICLR.cc/2025/Conference/Senior_Area_Chairs', ['~SeniorAC_OAOne1'])
        openreview_client.add_members_to_group('ICLR.cc/2025/Conference/Area_Chairs', ['~AreaChair_OAOne1', '~AreaChair_OATwo1'])
        openreview_client.add_members_to_group('ICLR.cc/2025/Conference/Reviewers', ['~Reviewer_OAOne1', '~Reviewer_OATwo1', '~Reviewer_OAThree1'])

        for i in range(1, 6):
            openreview_client.add_members_to_group(
                f'ICLR.cc/2025/Conference/Submission{i}/Senior_Area_Chairs',
                ['~SeniorAC_OAOne1']
            )
            ac = '~AreaChair_OAOne1' if i <= 3 else '~AreaChair_OATwo1'
            openreview_client.add_members_to_group(
                f'ICLR.cc/2025/Conference/Submission{i}/Area_Chairs',
                [ac]
            )
            openreview_client.add_members_to_group(
                f'ICLR.cc/2025/Conference/Submission{i}/Reviewers',
                ['~Reviewer_OAOne1', '~Reviewer_OATwo1', '~Reviewer_OAThree1']
            )

    def test_review_stage(self, client, openreview_client, helpers):
        """Set up review stage and post reviews for submissions 1 and 2."""

        pc_client = openreview.Client(username='pc@iclr25.cc', password=helpers.strong_password)
        request_form = pc_client.get_notes(invitation='openreview.net/Support/-/Request_Form')[0]

        now = datetime.datetime.now()
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
            readers=['ICLR.cc/2025/Conference/Program_Chairs', 'openreview.net/Support'],
            replyto=request_form.forum,
            referent=request_form.forum,
            signatures=['~Program_OAChair1'],
            writers=[]
        ))

        helpers.await_queue()
        helpers.await_queue_edit(openreview_client, 'ICLR.cc/2025/Conference/-/Official_Review-0-1', count=1)

        # Post reviews for submissions 1 and 2
        reviews_data = [
            {
                'reviewer_email': 'reviewer1@iclr25.cc',
                'reviewer_id': '~Reviewer_OAOne1',
                'submission': 1,
                'title': 'Strong contribution to protein folding',
                'review': 'This paper presents a novel and well-motivated attention mechanism for protein structure prediction. The results are compelling and the methodology is sound.',
                'rating': 8,
                'confidence': 4,
            },
            {
                'reviewer_email': 'reviewer2@iclr25.cc',
                'reviewer_id': '~Reviewer_OATwo1',
                'submission': 1,
                'title': 'Interesting but needs more experiments',
                'review': 'The approach is interesting but the experimental evaluation is limited. More baselines and ablation studies would strengthen the paper significantly.',
                'rating': 5,
                'confidence': 3,
            },
            {
                'reviewer_email': 'reviewer3@iclr25.cc',
                'reviewer_id': '~Reviewer_OAThree1',
                'submission': 1,
                'title': 'Solid paper with clear presentation',
                'review': 'Well-written paper with solid experimental results. The attention mechanism is novel and the application to protein folding is timely.',
                'rating': 7,
                'confidence': 4,
            },
            {
                'reviewer_email': 'reviewer1@iclr25.cc',
                'reviewer_id': '~Reviewer_OAOne1',
                'submission': 2,
                'title': 'Comprehensive scaling study',
                'review': 'This is a thorough empirical study of scaling laws for multilingual models. The insights are valuable for the community.',
                'rating': 7,
                'confidence': 3,
            },
        ]

        for review_data in reviews_data:
            reviewer_client = openreview.api.OpenReviewClient(
                username=review_data['reviewer_email'], password=helpers.strong_password
            )
            anon_groups = reviewer_client.get_groups(
                prefix=f'ICLR.cc/2025/Conference/Submission{review_data["submission"]}/Reviewer_',
                signatory=review_data['reviewer_id']
            )
            anon_group_id = anon_groups[0].id

            review_edit = reviewer_client.post_note_edit(
                invitation=f'ICLR.cc/2025/Conference/Submission{review_data["submission"]}/-/Official_Review',
                signatures=[anon_group_id],
                note=openreview.api.Note(
                    content={
                        'title': {'value': review_data['title']},
                        'review': {'value': review_data['review']},
                        'rating': {'value': review_data['rating']},
                        'confidence': {'value': review_data['confidence']},
                    }
                )
            )
            helpers.await_queue_edit(openreview_client, edit_id=review_edit['id'])
