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
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import NoSuchElementException


class TestMatching():

    @pytest.fixture(scope="class")
    def pc_client(self):
        return openreview.Client(username='pc1@mail.com', password='1234')

    @pytest.fixture(scope="class")
    def conference(self, client, helpers):
        pc_client = helpers.create_user('pc1@mail.com', 'PCFirstName', 'UAI')
        builder = openreview.conference.ConferenceBuilder(client, support_user='openreview.net/Support')
        builder.set_conference_id('auai.org/UAI/2019/Conference')
        builder.set_conference_name('Conference on Uncertainty in Artificial Intelligence')
        builder.set_conference_short_name('UAI 2019')
        builder.set_homepage_header({
        'title': 'UAI 2019',
        'subtitle': 'Conference on Uncertainty in Artificial Intelligence',
        'deadline': 'Abstract Submission Deadline: 11:59 pm Samoa Standard Time, March 4, 2019, Full Submission Deadline: 11:59 pm Samoa Standard Time, March 8, 2019',
        'date': 'July 22 - July 25, 2019',
        'website': 'http://auai.org/uai2019/',
        'location': 'Tel Aviv, Israel',
        'instructions': '''<p><strong>Important Information about Anonymity:</strong><br>
            When you post a submission to UAI 2019, please provide the real names and email addresses of authors in the submission form below (but NOT in the manuscript).
            The <em>original</em> record of your submission will be private, and will contain your real name(s).
            The PDF in your submission should not contain the names of the authors. </p>
            <p><strong>Conflict of Interest:</strong><br>
            Please make sure that your current and previous affiliations listed on your OpenReview <a href=\"/profile\">profile page</a> is up-to-date to avoid conflict of interest.</p>
            <p><strong>Questions or Concerns:</strong><br> Please contact the UAI 2019 Program chairs at <a href=\"mailto:uai2019chairs@gmail.com\">uai2019chairs@gmail.com</a>.
            <br>Please contact the OpenReview support team at <a href=\"mailto:info@openreview.net\">info@openreview.net</a> with any OpenReview related questions or concerns.
            </p>'''
        })
        print ('Homepage header set')
        builder.set_conference_program_chairs_ids(['pc1@mail.com', 'pc3@mail.com'])
        builder.set_conference_area_chairs_name('Senior_Program_Committee')
        builder.set_area_chair_roles(['Senior_Program_Committee'])
        builder.set_conference_reviewers_name('Program_Committee')
        builder.set_reviewer_roles(['Program_Committee'])
        now = datetime.datetime.utcnow()
        builder.set_submission_stage(due_date = now + datetime.timedelta(minutes = 40), double_blind= True, subject_areas=[
            "Algorithms: Approximate Inference",
            "Algorithms: Belief Propagation",
            "Algorithms: Distributed and Parallel",
            "Algorithms: Exact Inference",
        ],
        readers=[openreview.SubmissionStage.Readers.SENIOR_AREA_CHAIRS, openreview.SubmissionStage.Readers.AREA_CHAIRS, openreview.SubmissionStage.Readers.REVIEWERS])
        additional_registration_content = {
            'reviewing_experience': {
                'description': 'How many times have you been a reviewer for any conference or journal?',
                'value-radio': [
                    'Never - this is my first time',
                    '1 time - building my reviewer skills',
                    '2-4 times  - comfortable with the reviewing process',
                    '5-10 times  - active community citizen',
                    '10+ times  - seasoned reviewer'
                ],
                'order': 5,
                'required': False
            }
        }
        builder.set_registration_stage('auai.org/UAI/2019/Conference/Program_Committee', due_date = now + datetime.timedelta(minutes = 40))
        builder.set_registration_stage('auai.org/UAI/2019/Conference/Senior_Program_Committee', due_date = now + datetime.timedelta(minutes = 40), additional_fields = additional_registration_content)

        builder.set_bid_stage('auai.org/UAI/2019/Conference/Program_Committee', due_date = now + datetime.timedelta(minutes = 40), request_count = 50)
        builder.set_bid_stage('auai.org/UAI/2019/Conference/Senior_Program_Committee', due_date = now + datetime.timedelta(minutes = 40), request_count = 50)
        builder.use_legacy_anonids(True)
        conference = builder.get_result()
        # conference.client = pc_client
        return conference

    def test_setup_matching(self, conference, client, pc_client, test_client, helpers):

        ## setup matching with no reviewers
        with pytest.raises(openreview.OpenReviewException, match=r'The match group is empty'):
            conference.setup_committee_matching(committee_id=conference.get_reviewers_id(), compute_conflicts=True)

        ## setup matching with no area chairs
        with pytest.raises(openreview.OpenReviewException, match=r'The match group is empty'):
            conference.setup_committee_matching(committee_id=conference.get_area_chairs_id(), compute_conflicts=True)

        ## Set committee
        conference.set_area_chairs(['ac1@cmu.edu', 'ac2@umass.edu'])
        conference.set_reviewers(['r1@mit.edu', 'r2@google.com', 'r3@fb.com'])
        ac1_client = helpers.create_user('ac1@cmu.edu', 'AreaChair', 'One')
        r1_client = helpers.create_user('r1@mit.edu', 'Reviewer', 'One')


        ## Paper 1
        note_1 = openreview.Note(invitation = conference.get_submission_id(),
            readers = ['~SomeFirstName_User1', 'test@mail.com', 'a1@cmu.edu'],
            writers = [conference.id, '~SomeFirstName_User1', 'test@mail.com', 'a1@cmu.edu'],
            signatures = ['~SomeFirstName_User1'],
            content = {
                'title': 'Paper title 1',
                'abstract': 'This is an abstract',
                'authorids': ['test@mail.com', 'a1@cmu.edu'],
                'authors': ['SomeFirstName User', 'Author 1'],
                'subject_areas': [
                    'Algorithms: Approximate Inference',
                    'Algorithms: Belief Propagation'
                ]
            }
        )
        url = test_client.put_attachment(os.path.join(os.path.dirname(__file__), 'data/paper.pdf'), conference.get_submission_id(), 'pdf')
        note_1.content['pdf'] = url
        note_1 = test_client.post_note(note_1)

        ## Paper 2
        note_2 = openreview.Note(invitation = conference.get_submission_id(),
            readers = ['~SomeFirstName_User1', 'test@mail.com', 'a2@mit.edu'],
            writers = [conference.id, '~SomeFirstName_User1', 'test@mail.com', 'a2@mit.edu'],
            signatures = ['~SomeFirstName_User1'],
            content = {
                'title': 'Paper title 2',
                'abstract': 'This is an abstract',
                'authorids': ['test@mail.com', 'a2@mit.edu'],
                'authors': ['SomeFirstName User', 'Author 2'],
                'subject_areas': [
                    'Algorithms: Approximate Inference',
                    'Algorithms: Exact Inference'
                ]
            }
        )
        url = test_client.put_attachment(os.path.join(os.path.dirname(__file__), 'data/paper.pdf'), conference.get_submission_id(), 'pdf')
        note_2.content['pdf'] = url
        note_2 = test_client.post_note(note_2)

        ## Paper 3
        note_3 = openreview.Note(invitation = conference.get_submission_id(),
            readers = ['~SomeFirstName_User1', 'test@mail.com', 'a3@umass.edu'],
            writers = [conference.id, '~SomeFirstName_User1', 'test@mail.com', 'a3@umass.edu', 'pc3@mail.com'],
            signatures = ['~SomeFirstName_User1'],
            content = {
                'title': 'Paper title 3',
                'abstract': 'This is an abstract',
                'authorids': ['test@mail.com', 'a3@umass.edu', 'pc3@mail.com'],
                'authors': ['SomeFirstName User', 'Author 3', 'PC author'],
                'subject_areas': [
                    'Algorithms: Distributed and Parallel',
                    'Algorithms: Exact Inference'
                ]
            }
        )
        url = test_client.put_attachment(os.path.join(os.path.dirname(__file__), 'data/paper.pdf'), conference.get_submission_id(), 'pdf')
        note_3.content['pdf'] = url
        note_3 = test_client.post_note(note_3)

        ## setup matching with no submissions
        with pytest.raises(openreview.OpenReviewException, match=r'Submissions not found'):
            conference.setup_committee_matching(committee_id=conference.get_reviewers_id(), compute_conflicts=True)

        ## Create blind submissions
        conference.setup_post_submission_stage(force=True)
        # Set up reviewer matching
        conference.setup_matching(committee_id=conference.get_area_chairs_id())
        conference.setup_matching(committee_id=conference.get_reviewers_id(), build_conflicts=True)

        #check assignment process is set when invitation is created
        assignment_inv = client.get_invitation(conference.get_paper_assignment_id(group_id=conference.get_reviewers_id(), deployed=True))
        assert assignment_inv
        assert assignment_inv.process
        assert 'def process_update(client, edge, invitation, existing_edge):' in assignment_inv.process

        blinded_notes = conference.get_submissions(sort='tmdate')

        ac1_client.post_edge(openreview.Edge(invitation = conference.get_bid_id(conference.get_area_chairs_id()),
            readers = ['auai.org/UAI/2019/Conference', '~AreaChair_One1'],
            writers = ['auai.org/UAI/2019/Conference', '~AreaChair_One1'],
            signatures = ['~AreaChair_One1'],
            head = blinded_notes[0].id,
            tail = '~AreaChair_One1',
            label = 'High'
        ))
        ac1_client.post_edge(openreview.Edge(invitation = conference.get_bid_id(conference.get_area_chairs_id()),
            readers = ['auai.org/UAI/2019/Conference', '~AreaChair_One1'],
            writers = ['auai.org/UAI/2019/Conference', '~AreaChair_One1'],
            signatures = ['~AreaChair_One1'],
            head = blinded_notes[1].id,
            tail = '~AreaChair_One1',
            label = 'Low'
        ))
        ac1_client.post_edge(openreview.Edge(invitation = conference.get_bid_id(conference.get_area_chairs_id()),
            readers = ['auai.org/UAI/2019/Conference', '~AreaChair_One1'],
            writers = ['auai.org/UAI/2019/Conference', '~AreaChair_One1'],
            signatures = ['~AreaChair_One1'],
            head = blinded_notes[2].id,
            tail = '~AreaChair_One1',
            label = 'Very Low'
        ))

        r1_client.post_edge(openreview.Edge(invitation = conference.get_bid_id(conference.get_reviewers_id()),
            readers = ['auai.org/UAI/2019/Conference', '~Reviewer_One1'],
            writers = ['auai.org/UAI/2019/Conference', '~Reviewer_One1'],
            signatures = ['~Reviewer_One1'],
            head = blinded_notes[0].id,
            tail = '~Reviewer_One1',
            label = 'Neutral'
        ))
        r1_client.post_edge(openreview.Edge(invitation = conference.get_bid_id(conference.get_reviewers_id()),
            readers = ['auai.org/UAI/2019/Conference', '~Reviewer_One1'],
            writers = ['auai.org/UAI/2019/Conference', '~Reviewer_One1'],
            signatures = ['~Reviewer_One1'],
            head = blinded_notes[1].id,
            tail = '~Reviewer_One1',
            label = 'Very High'
        ))
        r1_client.post_edge(openreview.Edge(invitation = conference.get_bid_id(conference.get_reviewers_id()),
            readers = ['auai.org/UAI/2019/Conference', '~Reviewer_One1'],
            writers = ['auai.org/UAI/2019/Conference', '~Reviewer_One1'],
            signatures = ['~Reviewer_One1'],
            head = blinded_notes[2].id,
            tail = '~Reviewer_One1',
            label = 'Low'
        ))

        invitation = pc_client.get_invitation(id='auai.org/UAI/2019/Conference/Program_Committee/-/Assignment_Configuration')
        assert invitation
        assert 'scores_specification' in invitation.reply['content']
        assert 'auai.org/UAI/2019/Conference/Program_Committee/-/Bid' in invitation.reply['content']['scores_specification']['default']
        assert pc_client.get_invitation(id='auai.org/UAI/2019/Conference/Program_Committee/-/Custom_Max_Papers')
        assert pc_client.get_invitation(id='auai.org/UAI/2019/Conference/Program_Committee/-/Conflict')
        assert pc_client.get_invitation(id='auai.org/UAI/2019/Conference/Program_Committee/-/Aggregate_Score')
        assert pc_client.get_invitation(id='auai.org/UAI/2019/Conference/Program_Committee/-/Assignment')
        assert pc_client.get_invitation(id='auai.org/UAI/2019/Conference/Program_Committee/-/Proposed_Assignment')

        # Set up AC matching
        conference.setup_matching(committee_id=conference.get_area_chairs_id(), build_conflicts=True)

        invitation = pc_client.get_invitation(id='auai.org/UAI/2019/Conference/Senior_Program_Committee/-/Assignment_Configuration')
        assert invitation
        assert 'scores_specification' in invitation.reply['content']
        assert 'auai.org/UAI/2019/Conference/Senior_Program_Committee/-/Bid' in invitation.reply['content']['scores_specification']['default']
        assert pc_client.get_invitation(id='auai.org/UAI/2019/Conference/Senior_Program_Committee/-/Custom_Max_Papers')
        assert pc_client.get_invitation(id='auai.org/UAI/2019/Conference/Senior_Program_Committee/-/Conflict')
        assert pc_client.get_invitation(id='auai.org/UAI/2019/Conference/Senior_Program_Committee/-/Aggregate_Score')
        assert pc_client.get_invitation(id='auai.org/UAI/2019/Conference/Senior_Program_Committee/-/Assignment')

        bids = pc_client.get_edges(invitation = conference.get_bid_id(conference.get_area_chairs_id()))
        assert bids
        assert 3 == len(bids)

        bids = pc_client.get_edges(invitation = conference.get_bid_id(conference.get_reviewers_id()))
        assert bids
        assert 3 == len(bids)

        reviewer_custom_loads = pc_client.get_edges(
            invitation='auai.org/UAI/2019/Conference/Program_Committee/-/Custom_Max_Papers')
        assert not reviewer_custom_loads

        ac_custom_loads = pc_client.get_edges(
            invitation='auai.org/UAI/2019/Conference/Senior_Program_Committee/-/Custom_Max_Papers')
        assert not ac_custom_loads

        reviewer_conflicts = pc_client.get_edges(
            invitation='auai.org/UAI/2019/Conference/Program_Committee/-/Conflict')
        assert 1 == len(reviewer_conflicts)

        ac_conflicts = pc_client.get_edges(
            invitation='auai.org/UAI/2019/Conference/Senior_Program_Committee/-/Conflict')
        assert 2 == len(ac_conflicts)

        ac1_conflicts = pc_client.get_edges(
            invitation='auai.org/UAI/2019/Conference/Senior_Program_Committee/-/Conflict',
            tail='~AreaChair_One1')
        assert ac1_conflicts
        assert len(ac1_conflicts)
        assert ac1_conflicts[0].label == 'Conflict'

        r1_conflicts = pc_client.get_edges(
            invitation='auai.org/UAI/2019/Conference/Program_Committee/-/Conflict',
            tail='~Reviewer_One1')
        assert r1_conflicts
        assert len(r1_conflicts)
        assert r1_conflicts[0].label == 'Conflict'

        ac2_conflicts = pc_client.get_edges(
            invitation='auai.org/UAI/2019/Conference/Senior_Program_Committee/-/Conflict',
            tail='ac2@umass.edu')
        assert ac2_conflicts
        assert len(ac2_conflicts)
        assert ac2_conflicts[0].label == 'Conflict'


    def test_setup_matching_with_tpms(self, conference, pc_client, helpers):

        # Set up reviewer matching
        conference.setup_matching(tpms_score_file=os.path.join(os.path.dirname(__file__), 'data/reviewer_tpms_scores.csv'), build_conflicts=True)

        print(conference.get_reviewers_id())

        invitation = pc_client.get_invitation(id='auai.org/UAI/2019/Conference/Program_Committee/-/Assignment_Configuration')
        assert invitation
        assert 'scores_specification' in invitation.reply['content']
        assert 'auai.org/UAI/2019/Conference/Program_Committee/-/Bid' in invitation.reply['content']['scores_specification']['default']
        assert 'auai.org/UAI/2019/Conference/Program_Committee/-/TPMS_Score' in invitation.reply['content']['scores_specification']['default']
        assert 'auai.org/UAI/2019/Conference/Program_Committee/-/Subject_Areas_Score' in invitation.reply['content']['scores_specification']['default']
        assert 'auai.org/UAI/2019/Conference/-/Recommendation' not in invitation.reply['content']['scores_specification']['default']
        assert pc_client.get_invitation(id='auai.org/UAI/2019/Conference/Program_Committee/-/Custom_Max_Papers')
        assert pc_client.get_invitation(id='auai.org/UAI/2019/Conference/Program_Committee/-/Conflict')
        assert pc_client.get_invitation(id='auai.org/UAI/2019/Conference/Program_Committee/-/Aggregate_Score')
        assert pc_client.get_invitation(id='auai.org/UAI/2019/Conference/Program_Committee/-/Assignment')
        assert pc_client.get_invitation(id='auai.org/UAI/2019/Conference/Program_Committee/-/TPMS_Score')

        # Set up ac matching
        conference.setup_matching(
            committee_id=conference.get_area_chairs_id(),
            tpms_score_file=os.path.join(os.path.dirname(__file__), 'data/ac_tpms_scores.csv'),
            build_conflicts=True)

        invitation = pc_client.get_invitation(id='auai.org/UAI/2019/Conference/Senior_Program_Committee/-/Assignment_Configuration')
        assert invitation
        assert 'scores_specification' in invitation.reply['content']
        assert 'auai.org/UAI/2019/Conference/Senior_Program_Committee/-/Bid' in invitation.reply['content']['scores_specification']['default']
        assert 'auai.org/UAI/2019/Conference/Senior_Program_Committee/-/TPMS_Score' in invitation.reply['content']['scores_specification']['default']
        assert 'auai.org/UAI/2019/Conference/Senior_Program_Committee/-/Subject_Areas_Score' in invitation.reply['content']['scores_specification']['default']
        assert pc_client.get_invitation(id='auai.org/UAI/2019/Conference/Senior_Program_Committee/-/Custom_Max_Papers')
        assert pc_client.get_invitation(id='auai.org/UAI/2019/Conference/Senior_Program_Committee/-/Conflict')
        assert pc_client.get_invitation(id='auai.org/UAI/2019/Conference/Senior_Program_Committee/-/Aggregate_Score')
        assert pc_client.get_invitation(id='auai.org/UAI/2019/Conference/Senior_Program_Committee/-/Assignment')
        assert pc_client.get_invitation(id='auai.org/UAI/2019/Conference/Senior_Program_Committee/-/TPMS_Score')

        bids = pc_client.get_edges(invitation = conference.get_bid_id(conference.get_area_chairs_id()))
        assert bids
        assert 3 == len(bids)

        bids = pc_client.get_edges(invitation = conference.get_bid_id(conference.get_reviewers_id()))
        assert bids
        assert 3 == len(bids)

        reviewer_custom_loads = pc_client.get_edges(
            invitation='auai.org/UAI/2019/Conference/Program_Committee/-/Custom_Max_Papers')
        assert not reviewer_custom_loads

        ac_custom_loads = pc_client.get_edges(
            invitation='auai.org/UAI/2019/Conference/Senior_Program_Committee/-/Custom_Max_Papers')
        assert not ac_custom_loads

        reviewer_conflicts = pc_client.get_edges(
            invitation='auai.org/UAI/2019/Conference/Program_Committee/-/Conflict')
        assert 1 == len(reviewer_conflicts)

        ac_conflicts = pc_client.get_edges(
            invitation='auai.org/UAI/2019/Conference/Senior_Program_Committee/-/Conflict')
        assert 2 == len(ac_conflicts)

        ac1_conflicts = pc_client.get_edges(
            invitation='auai.org/UAI/2019/Conference/Senior_Program_Committee/-/Conflict', tail='~AreaChair_One1')
        assert ac1_conflicts
        assert len(ac1_conflicts)
        assert ac1_conflicts[0].label == 'Conflict'

        r1_conflicts = pc_client.get_edges(
            invitation='auai.org/UAI/2019/Conference/Program_Committee/-/Conflict', tail='~Reviewer_One1')
        assert r1_conflicts
        assert len(r1_conflicts)
        assert r1_conflicts[0].label == 'Conflict'

        ac2_conflicts = pc_client.get_edges(
            invitation='auai.org/UAI/2019/Conference/Senior_Program_Committee/-/Conflict', tail = 'ac2@umass.edu')
        assert ac2_conflicts
        assert len(ac2_conflicts)
        assert ac2_conflicts[0].label == 'Conflict'

        submissions = conference.get_submissions(sort='tmdate')
        assert submissions
        assert 3 == len(submissions)

        reviewer_tpms_scores = pc_client.get_edges(
            invitation='auai.org/UAI/2019/Conference/Program_Committee/-/TPMS_Score')
        assert 9 == len(reviewer_tpms_scores)

        ac_tpms_scores = pc_client.get_edges(
            invitation='auai.org/UAI/2019/Conference/Senior_Program_Committee/-/TPMS_Score')
        assert 6 == len(ac_tpms_scores)

        r3_s0_tpms_scores = pc_client.get_edges(
            invitation='auai.org/UAI/2019/Conference/Program_Committee/-/TPMS_Score',
            tail='r3@fb.com',
            head=submissions[0].id)
        assert r3_s0_tpms_scores
        assert 1 == len(r3_s0_tpms_scores)
        assert r3_s0_tpms_scores[0].weight == 0.21

        r3_s1_tpms_scores = pc_client.get_edges(
            invitation='auai.org/UAI/2019/Conference/Program_Committee/-/TPMS_Score',
            tail='r3@fb.com',
            head=submissions[1].id)
        assert r3_s1_tpms_scores
        assert 1 == len(r3_s1_tpms_scores)
        assert r3_s1_tpms_scores[0].weight == 0.31

        r3_s2_tpms_scores = pc_client.get_edges(
            invitation='auai.org/UAI/2019/Conference/Program_Committee/-/TPMS_Score',
            tail='r3@fb.com',
            head=submissions[2].id)
        assert r3_s2_tpms_scores
        assert 1 == len(r3_s2_tpms_scores)
        assert r3_s2_tpms_scores[0].weight == 0.51


    def test_setup_matching_with_recommendations(self, conference, pc_client, test_client, helpers):

        blinded_notes = list(conference.get_submissions(sort='tmdate'))

        ## Open reviewer recommendations
        now = datetime.datetime.utcnow()
        conference.open_recommendations(assignment_title='', due_date = now + datetime.timedelta(minutes = 40))

        ## Recommend reviewers
        ac1_client = helpers.get_user('ac1@cmu.edu')
        ac1_client.post_edge(openreview.Edge(invitation = conference.get_recommendation_id(),
            readers = ['auai.org/UAI/2019/Conference', '~AreaChair_One1'],
            signatures = ['~AreaChair_One1'],
            writers = ['~AreaChair_One1'],
            head = blinded_notes[0].id,
            tail = '~Reviewer_One1',
            weight = 1
        ))
        ac1_client.post_edge(openreview.Edge(invitation = conference.get_recommendation_id(),
            readers = ['auai.org/UAI/2019/Conference', '~AreaChair_One1'],
            signatures = ['~AreaChair_One1'],
            writers = ['~AreaChair_One1'],
            head = blinded_notes[1].id,
            tail = 'r2@google.com',
            weight = 2
        ))
        ac1_client.post_edge(openreview.Edge(invitation = conference.get_recommendation_id(),
            readers = ['auai.org/UAI/2019/Conference', '~AreaChair_One1'],
            signatures = ['~AreaChair_One1'],
            writers = ['~AreaChair_One1'],
            head = blinded_notes[1].id,
            tail = 'r3@fb.com',
            weight = 3
        ))

       # Set up reviewer matching
        conference.setup_matching(tpms_score_file=os.path.join(os.path.dirname(__file__), 'data/reviewer_tpms_scores.csv'), build_conflicts=True)

        print(conference.get_reviewers_id())

        invitation = pc_client.get_invitation(id='auai.org/UAI/2019/Conference/Program_Committee/-/Assignment_Configuration')
        assert invitation
        assert 'scores_specification' in invitation.reply['content']
        assert 'auai.org/UAI/2019/Conference/Program_Committee/-/Bid' in invitation.reply['content']['scores_specification']['default']
        assert 'auai.org/UAI/2019/Conference/Program_Committee/-/TPMS_Score' in invitation.reply['content']['scores_specification']['default']
        assert 'auai.org/UAI/2019/Conference/Program_Committee/-/Subject_Areas_Score' in invitation.reply['content']['scores_specification']['default']
        assert pc_client.get_invitation(id='auai.org/UAI/2019/Conference/Program_Committee/-/Custom_Max_Papers')
        assert pc_client.get_invitation(id='auai.org/UAI/2019/Conference/Program_Committee/-/Conflict')

        # Set up ac matching
        conference.setup_matching(
            committee_id=conference.get_area_chairs_id(),
            tpms_score_file=os.path.join(os.path.dirname(__file__), 'data/ac_tpms_scores.csv'),
            build_conflicts=True)

        invitation = pc_client.get_invitation(id='auai.org/UAI/2019/Conference/Senior_Program_Committee/-/Assignment_Configuration')
        assert invitation
        assert 'scores_specification' in invitation.reply['content']
        assert 'auai.org/UAI/2019/Conference/Senior_Program_Committee/-/Bid' in invitation.reply['content']['scores_specification']['default']
        assert 'auai.org/UAI/2019/Conference/Senior_Program_Committee/-/TPMS_Score' in invitation.reply['content']['scores_specification']['default']
        assert 'auai.org/UAI/2019/Conference/Senior_Program_Committee/-/Subject_Areas_Score' in invitation.reply['content']['scores_specification']['default']
        assert 'auai.org/UAI/2019/Conference/Program_Committee/-/Recommendation' in invitation.reply['content']['scores_specification']['default']

        assert pc_client.get_invitation(id='auai.org/UAI/2019/Conference/Senior_Program_Committee/-/Custom_Max_Papers')
        assert pc_client.get_invitation(id='auai.org/UAI/2019/Conference/Senior_Program_Committee/-/Conflict')

        bids = pc_client.get_edges(invitation = conference.get_bid_id(conference.get_area_chairs_id()))
        assert bids
        assert 3 == len(bids)

        bids = pc_client.get_edges(invitation = conference.get_bid_id(conference.get_reviewers_id()))
        assert bids
        assert 3 == len(bids)

        recommendations = pc_client.get_edges(invitation = conference.get_recommendation_id())
        assert recommendations
        assert 3 == len(recommendations)

        reviewer_custom_loads = pc_client.get_edges(
            invitation='auai.org/UAI/2019/Conference/Program_Committee/-/Custom_Max_Papers')
        assert not reviewer_custom_loads

        ac_custom_loads = pc_client.get_edges(
            invitation='auai.org/UAI/2019/Conference/Senior_Program_Committee/-/Custom_Max_Papers')
        assert not ac_custom_loads

        reviewer_conflicts = pc_client.get_edges(
            invitation='auai.org/UAI/2019/Conference/Program_Committee/-/Conflict')
        assert 1 == len(reviewer_conflicts)

        ac_conflicts = pc_client.get_edges(
            invitation='auai.org/UAI/2019/Conference/Senior_Program_Committee/-/Conflict')
        assert 2 == len(ac_conflicts)

        ac1_conflicts = pc_client.get_edges(
            invitation='auai.org/UAI/2019/Conference/Senior_Program_Committee/-/Conflict', tail='~AreaChair_One1')
        assert ac1_conflicts
        assert len(ac1_conflicts)
        assert ac1_conflicts[0].label == 'Conflict'

        r1_conflicts = pc_client.get_edges(
            invitation='auai.org/UAI/2019/Conference/Program_Committee/-/Conflict', tail='~Reviewer_One1')
        assert r1_conflicts
        assert len(r1_conflicts)
        assert r1_conflicts[0].label == 'Conflict'

        ac2_conflicts = pc_client.get_edges(
            invitation='auai.org/UAI/2019/Conference/Senior_Program_Committee/-/Conflict', tail='ac2@umass.edu')
        assert ac2_conflicts
        assert len(ac2_conflicts)
        assert ac2_conflicts[0].label == 'Conflict'

        submissions = conference.get_submissions(sort='tmdate')
        assert submissions
        assert 3 == len(submissions)

        reviewer_tpms_scores = pc_client.get_edges(
            invitation='auai.org/UAI/2019/Conference/Program_Committee/-/TPMS_Score')
        assert 9 == len(reviewer_tpms_scores)

        ac_tpms_scores = pc_client.get_edges(
            invitation='auai.org/UAI/2019/Conference/Senior_Program_Committee/-/TPMS_Score')
        assert 6 == len(ac_tpms_scores)

        r3_s0_tpms_scores = pc_client.get_edges(
            invitation='auai.org/UAI/2019/Conference/Program_Committee/-/TPMS_Score',
            tail='r3@fb.com',
            head=submissions[0].id)
        assert r3_s0_tpms_scores
        assert 1 == len(r3_s0_tpms_scores)
        assert r3_s0_tpms_scores[0].weight == 0.21

        r3_s1_tpms_scores = pc_client.get_edges(
            invitation='auai.org/UAI/2019/Conference/Program_Committee/-/TPMS_Score',
            tail='r3@fb.com',
            head=submissions[1].id)
        assert r3_s1_tpms_scores
        assert 1 == len(r3_s1_tpms_scores)
        assert r3_s1_tpms_scores[0].weight == 0.31

        r3_s2_tpms_scores = pc_client.get_edges(
            invitation='auai.org/UAI/2019/Conference/Program_Committee/-/TPMS_Score',
            tail='r3@fb.com',
            head=submissions[2].id)
        assert r3_s2_tpms_scores
        assert 1 == len(r3_s2_tpms_scores)
        assert r3_s2_tpms_scores[0].weight == 0.51


    def test_setup_matching_with_subject_areas(self, conference, pc_client, test_client, helpers):

        blinded_notes = list(conference.get_submissions(sort='tmdate'))

        registration_notes = pc_client.get_notes(invitation = 'auai.org/UAI/2019/Conference/Senior_Program_Committee/-/Registration_Form')
        assert registration_notes
        assert len(registration_notes) == 1

        registration_forum = registration_notes[0].forum

        ## Recommend reviewers
        ac1_client = helpers.get_user('ac1@cmu.edu')
        ac1_client.post_note(
            openreview.Note(
                invitation = 'auai.org/UAI/2019/Conference/Senior_Program_Committee/-/Registration',
                readers = ['auai.org/UAI/2019/Conference', '~AreaChair_One1'],
                writers = ['auai.org/UAI/2019/Conference', '~AreaChair_One1'],
                signatures = ['~AreaChair_One1'],
                forum = registration_forum,
                replyto = registration_forum,
                content = {
                    'subject_areas': [
                        'Algorithms: Approximate Inference',
                        'Algorithms: Belief Propagation'
                    ],
                    'profile_confirmed': 'Yes',
                    'expertise_confirmed': 'Yes',
                    'reviewing_experience': '2-4 times  - comfortable with the reviewing process'
                }))

        # Set up reviewer matching
        conference.setup_matching(build_conflicts=True)

        assert pc_client.get_invitation(id='auai.org/UAI/2019/Conference/Program_Committee/-/Subject_Areas_Score')
        assert pc_client.get_invitation(id='auai.org/UAI/2019/Conference/Program_Committee/-/Custom_Max_Papers')
        assert pc_client.get_invitation(id='auai.org/UAI/2019/Conference/Program_Committee/-/Conflict')

        # Set up AC matching
        conference.setup_matching(committee_id=conference.get_area_chairs_id(), build_conflicts=True)

        assert pc_client.get_invitation(id='auai.org/UAI/2019/Conference/Senior_Program_Committee/-/Subject_Areas_Score')
        assert pc_client.get_invitation(id='auai.org/UAI/2019/Conference/Senior_Program_Committee/-/Custom_Max_Papers')
        assert pc_client.get_invitation(id='auai.org/UAI/2019/Conference/Senior_Program_Committee/-/Conflict')

        bids = pc_client.get_edges(invitation = conference.get_bid_id(conference.get_area_chairs_id()))
        assert bids
        assert 3 == len(bids)

        bids = pc_client.get_edges(invitation = conference.get_bid_id(conference.get_reviewers_id()))
        assert bids
        assert 3 == len(bids)

        recommendations = pc_client.get_edges(invitation = conference.get_recommendation_id())
        assert recommendations
        assert 3 == len(recommendations)

        reviewer_custom_loads = pc_client.get_edges(
            invitation='auai.org/UAI/2019/Conference/Program_Committee/-/Custom_Max_Papers')
        assert not reviewer_custom_loads

        ac_custom_loads = pc_client.get_edges(
            invitation='auai.org/UAI/2019/Conference/Senior_Program_Committee/-/Custom_Max_Papers')
        assert not ac_custom_loads

        reviewer_conflicts = pc_client.get_edges(
            invitation='auai.org/UAI/2019/Conference/Program_Committee/-/Conflict')
        assert 1 == len(reviewer_conflicts)

        ac_conflicts = pc_client.get_edges(
            invitation='auai.org/UAI/2019/Conference/Senior_Program_Committee/-/Conflict')
        assert 2 == len(ac_conflicts)

        ac1_conflicts = pc_client.get_edges(
            invitation='auai.org/UAI/2019/Conference/Senior_Program_Committee/-/Conflict',
            tail='~AreaChair_One1')
        assert ac1_conflicts
        assert len(ac1_conflicts)
        assert ac1_conflicts[0].label == 'Conflict'

        r1_conflicts = pc_client.get_edges(
            invitation='auai.org/UAI/2019/Conference/Program_Committee/-/Conflict',
            tail='~Reviewer_One1')
        assert r1_conflicts
        assert len(r1_conflicts)
        assert r1_conflicts[0].label == 'Conflict'

        ac2_conflicts = pc_client.get_edges(
            invitation='auai.org/UAI/2019/Conference/Senior_Program_Committee/-/Conflict',
            tail='ac2@umass.edu')
        assert ac2_conflicts
        assert len(ac2_conflicts)
        assert ac2_conflicts[0].label == 'Conflict'

        submissions = conference.get_submissions(sort='tmdate')
        assert submissions
        assert 3 == len(submissions)

        reviewer_tpms_scores = pc_client.get_edges(
            invitation='auai.org/UAI/2019/Conference/Program_Committee/-/TPMS_Score')
        assert 9 == len(reviewer_tpms_scores)

        ac_tpms_scores = pc_client.get_edges(
            invitation='auai.org/UAI/2019/Conference/Senior_Program_Committee/-/TPMS_Score')
        assert 6 == len(ac_tpms_scores)

        r3_s0_tpms_scores = pc_client.get_edges(
            invitation='auai.org/UAI/2019/Conference/Program_Committee/-/TPMS_Score',
            tail='r3@fb.com',
            head=submissions[0].id)
        assert r3_s0_tpms_scores
        assert 1 == len(r3_s0_tpms_scores)
        assert r3_s0_tpms_scores[0].weight == 0.21

        r3_s1_tpms_scores = pc_client.get_edges(
            invitation='auai.org/UAI/2019/Conference/Program_Committee/-/TPMS_Score',
            tail='r3@fb.com',
            head=submissions[1].id)
        assert r3_s1_tpms_scores
        assert 1 == len(r3_s1_tpms_scores)
        assert r3_s1_tpms_scores[0].weight == 0.31

        r3_s2_tpms_scores = pc_client.get_edges(
            invitation='auai.org/UAI/2019/Conference/Program_Committee/-/TPMS_Score',
            tail='r3@fb.com',
            head=submissions[2].id)
        assert r3_s2_tpms_scores
        assert 1 == len(r3_s2_tpms_scores)
        assert r3_s2_tpms_scores[0].weight == 0.51

        reviewer_subject_area_scores = pc_client.get_edges(
            invitation='auai.org/UAI/2019/Conference/Program_Committee/-/Subject_Areas_Score')
        assert not reviewer_subject_area_scores

        ac_subject_areas_scores = pc_client.get_edges(
            invitation='auai.org/UAI/2019/Conference/Senior_Program_Committee/-/Subject_Areas_Score')
        assert 3 == len(ac_subject_areas_scores)

        ac1_s0_subject_scores = pc_client.get_edges(
            invitation='auai.org/UAI/2019/Conference/Senior_Program_Committee/-/Subject_Areas_Score',
            tail='~AreaChair_One1',
            head=submissions[0].id)
        assert ac1_s0_subject_scores
        assert 1 == len(ac1_s0_subject_scores)
        assert ac1_s0_subject_scores[0].weight ==  0

        ac1_s1_subject_scores = pc_client.get_edges(
            invitation='auai.org/UAI/2019/Conference/Senior_Program_Committee/-/Subject_Areas_Score',
            tail='~AreaChair_One1',
            head=submissions[1].id)
        assert ac1_s1_subject_scores
        assert 1 == len(ac1_s1_subject_scores)
        assert ac1_s1_subject_scores[0].weight ==  0.3333333333333333

        ac1_s2_subject_scores = pc_client.get_edges(
            invitation='auai.org/UAI/2019/Conference/Senior_Program_Committee/-/Subject_Areas_Score',
            tail='~AreaChair_One1',
            head=submissions[2].id)
        assert ac1_s2_subject_scores
        assert 1 == len(ac1_s2_subject_scores)
        assert ac1_s2_subject_scores[0].weight ==  1

    def test_set_assigments(self, conference, client, pc_client, test_client, helpers):

        conference.client = pc_client

        blinded_notes = list(conference.get_submissions(sort='tmdate'))

        edges = pc_client.get_edges(
            invitation='auai.org/UAI/2019/Conference/Program_Committee/-/Proposed_Assignment',
            label='rev-matching'
        )
        assert 0 == len(edges)

        #Reviewer assignments
        pc_client.post_edge(openreview.Edge(invitation = conference.get_paper_assignment_id(conference.get_reviewers_id()),
            readers = [conference.id, '~Reviewer_One1'],
            nonreaders = [f'auai.org/UAI/2019/Conference/Paper{blinded_notes[0].number}/Authors'],
            writers = [conference.id, f'auai.org/UAI/2019/Conference/Paper{blinded_notes[0].number}/Senior_Program_Committee'],
            signatures = [conference.id],
            head = blinded_notes[0].id,
            tail = '~Reviewer_One1',
            label = 'rev-matching',
            weight = 0.98
        ))

        pc_client.post_edge(openreview.Edge(invitation = conference.get_paper_assignment_id(conference.get_reviewers_id()),
            readers = [conference.id, 'r2@google.com'],
            nonreaders = [f'auai.org/UAI/2019/Conference/Paper{blinded_notes[0].number}/Authors'],
            writers = [conference.id, f'auai.org/UAI/2019/Conference/Paper{blinded_notes[0].number}/Senior_Program_Committee'],
            signatures = [conference.id],
            head = blinded_notes[0].id,
            tail = 'r2@google.com',
            label = 'rev-matching',
            weight = 0.87
        ))

        pc_client.post_edge(openreview.Edge(invitation = conference.get_paper_assignment_id(conference.get_reviewers_id()),
            readers = [conference.id, 'r2@google.com'],
            nonreaders = [f'auai.org/UAI/2019/Conference/Paper{blinded_notes[1].number}/Authors'],
            writers = [conference.id, f'auai.org/UAI/2019/Conference/Paper{blinded_notes[1].number}/Senior_Program_Committee'],
            signatures = [conference.id],
            head = blinded_notes[1].id,
            tail = 'r2@google.com',
            label = 'rev-matching',
            weight = 0.87
        ))

        pc_client.post_edge(openreview.Edge(invitation = conference.get_paper_assignment_id(conference.get_reviewers_id()),
            readers = [conference.id, 'r3@fb.com'],
            nonreaders = [f'auai.org/UAI/2019/Conference/Paper{blinded_notes[1].number}/Authors'],
            writers = [conference.id, f'auai.org/UAI/2019/Conference/Paper{blinded_notes[1].number}/Senior_Program_Committee'],
            signatures = [conference.id],
            head = blinded_notes[1].id,
            tail = 'r3@fb.com',
            label = 'rev-matching',
            weight = 0.94
        ))

        pc_client.post_edge(openreview.Edge(invitation = conference.get_paper_assignment_id(conference.get_reviewers_id()),
            readers = [conference.id, 'r3@fb.com'],
            nonreaders = [f'auai.org/UAI/2019/Conference/Paper{blinded_notes[2].number}/Authors'],
            writers = [conference.id, f'auai.org/UAI/2019/Conference/Paper{blinded_notes[2].number}/Senior_Program_Committee'],
            signatures = [conference.id],
            head = blinded_notes[2].id,
            tail = 'r3@fb.com',
            label = 'rev-matching',
            weight = 0.94
        ))

        pc_client.post_edge(openreview.Edge(invitation = conference.get_paper_assignment_id(conference.get_reviewers_id()),
            readers = [conference.id, '~Reviewer_One1'],
            nonreaders = [f'auai.org/UAI/2019/Conference/Paper{blinded_notes[2].number}/Authors'],
            writers = [conference.id, f'auai.org/UAI/2019/Conference/Paper{blinded_notes[2].number}/Senior_Program_Committee'],
            signatures = [conference.id],
            head = blinded_notes[2].id,
            tail = '~Reviewer_One1',
            label = 'rev-matching',
            weight = 0.98
        ))

        edges = pc_client.get_edges(
            invitation='auai.org/UAI/2019/Conference/Program_Committee/-/Proposed_Assignment',
            label='rev-matching'
        )
        assert 6 == len(edges)

        conference.set_assignments(assignment_title='rev-matching', committee_id='auai.org/UAI/2019/Conference/Program_Committee')

        revs_paper0 = pc_client.get_group(conference.get_id()+'/Paper{x}/Program_Committee'.format(x=blinded_notes[0].number))
        assert 2 == len(revs_paper0.members)
        assert '~Reviewer_One1' in revs_paper0.members
        assert 'r2@google.com' in revs_paper0.members
        assert pc_client.get_groups(regex=conference.get_id()+'/Paper{x}/AnonReviewer.*'.format(x=blinded_notes[0].number), member='~Reviewer_One1')
        assert pc_client.get_groups(regex=conference.get_id()+'/Paper{x}/AnonReviewer.*'.format(x=blinded_notes[0].number), member='r2@google.com')

        revs_paper1 = pc_client.get_group(conference.get_id()+'/Paper{x}/Program_Committee'.format(x=blinded_notes[1].number))
        assert 2 == len(revs_paper1.members)
        assert revs_paper1.members[0] == 'r2@google.com'
        assert revs_paper1.members[1] == 'r3@fb.com'
        assert pc_client.get_group(conference.get_id()+'/Paper{x}/AnonReviewer1'.format(x=blinded_notes[1].number)).members == ['r2@google.com']
        assert pc_client.get_group(conference.get_id()+'/Paper{x}/AnonReviewer2'.format(x=blinded_notes[1].number)).members == ['r3@fb.com']

        revs_paper2 = pc_client.get_group(conference.get_id()+'/Paper{x}/Program_Committee'.format(x=blinded_notes[2].number))
        assert 2 == len(revs_paper2.members)
        assert 'r3@fb.com' in revs_paper2.members
        assert '~Reviewer_One1' in revs_paper2.members
        assert pc_client.get_group(conference.get_id()+'/Paper{x}/AnonReviewer{y}'.format(x=blinded_notes[2].number, y=revs_paper2.members.index('r3@fb.com')+1)).members == ['r3@fb.com']
        assert pc_client.get_group(conference.get_id()+'/Paper{x}/AnonReviewer{y}'.format(x=blinded_notes[2].number, y=revs_paper2.members.index('~Reviewer_One1')+1)).members == ['~Reviewer_One1']

        conference.setup_matching(committee_id=conference.get_reviewers_id(), build_conflicts=True)

        #check assignment process is still set after deployment and setting up matching again
        assignment_inv = client.get_invitation(conference.get_paper_assignment_id(group_id=conference.get_reviewers_id(), deployed=True))
        assert assignment_inv
        assert assignment_inv.process
        assert 'def process_update(client, edge, invitation, existing_edge):' in assignment_inv.process

    def test_redeploy_assigments(self, conference, client, pc_client, test_client, helpers):

        blinded_notes = list(conference.get_submissions(sort='tmdate'))

        #Reviewer assignments
        pc_client.post_edge(openreview.Edge(invitation = conference.get_paper_assignment_id(conference.get_reviewers_id()),
            readers = [conference.id, 'r3@fb.com'],
            nonreaders = [f'auai.org/UAI/2019/Conference/Paper{blinded_notes[0].number}/Authors'],
            writers = [conference.id, f'auai.org/UAI/2019/Conference/Paper{blinded_notes[0].number}/Senior_Program_Committee'],
            signatures = [conference.id],
            head = blinded_notes[0].id,
            tail = 'r3@fb.com',
            label = 'rev-matching-new',
            weight = 0.98
        ))

        pc_client.post_edge(openreview.Edge(invitation = conference.get_paper_assignment_id(conference.get_reviewers_id()),
            readers = [conference.id, '~Reviewer_One1'],
            nonreaders = [f'auai.org/UAI/2019/Conference/Paper{blinded_notes[1].number}/Authors'],
            writers = [conference.id, f'auai.org/UAI/2019/Conference/Paper{blinded_notes[1].number}/Senior_Program_Committee'],
            signatures = [conference.id],
            head = blinded_notes[1].id,
            tail = '~Reviewer_One1',
            label = 'rev-matching-new',
            weight = 0.98
        ))

        pc_client.post_edge(openreview.Edge(invitation = conference.get_paper_assignment_id(conference.get_reviewers_id()),
            readers = [conference.id, 'r2@google.com'],
            nonreaders = [f'auai.org/UAI/2019/Conference/Paper{blinded_notes[2].number}/Authors'],
            writers = [conference.id, f'auai.org/UAI/2019/Conference/Paper{blinded_notes[2].number}/Senior_Program_Committee'],
            signatures = [conference.id],
            head = blinded_notes[2].id,
            tail = 'r2@google.com',
            label = 'rev-matching-new',
            weight = 0.98
        ))

        edges = pc_client.get_edges(
            invitation='auai.org/UAI/2019/Conference/Program_Committee/-/Proposed_Assignment',
            label='rev-matching-new'
        )
        assert 3 == len(edges)

        conference.set_assignments(assignment_title='rev-matching-new', overwrite=True, committee_id='auai.org/UAI/2019/Conference/Program_Committee')

        revs_paper0 = pc_client.get_group(conference.get_id()+'/Paper{x}/Program_Committee'.format(x=blinded_notes[0].number))
        assert ['r3@fb.com'] == revs_paper0.members
        assert pc_client.get_group(conference.get_id()+'/Paper{x}/AnonReviewer1'.format(x=blinded_notes[0].number)).members == ['r3@fb.com']
        with pytest.raises(openreview.OpenReviewException, match=r'Group Not Found'):
            assert pc_client.get_group(conference.get_id()+'/Paper{x}/AnonReviewer2'.format(x=blinded_notes[0].number))

        revs_paper1 = pc_client.get_group(conference.get_id()+'/Paper{x}/Program_Committee'.format(x=blinded_notes[1].number))
        assert ['~Reviewer_One1'] == revs_paper1.members
        assert pc_client.get_group(conference.get_id()+'/Paper{x}/AnonReviewer1'.format(x=blinded_notes[1].number)).members == ['~Reviewer_One1']
        with pytest.raises(openreview.OpenReviewException, match=r'Group Not Found'):
            assert pc_client.get_group(conference.get_id()+'/Paper{x}/AnonReviewer2'.format(x=blinded_notes[1].number))

        revs_paper2 = pc_client.get_group(conference.get_id()+'/Paper{x}/Program_Committee'.format(x=blinded_notes[2].number))
        assert ['r2@google.com'] == revs_paper2.members
        assert pc_client.get_group(conference.get_id()+'/Paper{x}/AnonReviewer1'.format(x=blinded_notes[2].number)).members == ['r2@google.com']
        with pytest.raises(openreview.OpenReviewException, match=r'Group Not Found'):
            assert pc_client.get_group(conference.get_id()+'/Paper{x}/AnonReviewer2'.format(x=blinded_notes[2].number))


        ## Emergency reviewers, append reviewers
        conference.set_reviewers(['~Reviewer_One1', 'r2@google.com', 'r3@fb.com', 'r2@mit.edu'])
        pc_client.post_edge(openreview.Edge(invitation = conference.get_paper_assignment_id(conference.get_reviewers_id()),
            readers = [conference.id, '~Reviewer_One1'],
            nonreaders = [f'auai.org/UAI/2019/Conference/Paper{blinded_notes[0].number}/Authors'],
            writers = [conference.id, f'auai.org/UAI/2019/Conference/Paper{blinded_notes[0].number}/Senior_Program_Committee'],
            signatures = [conference.id],
            head = blinded_notes[0].id,
            tail = '~Reviewer_One1',
            label = 'rev-matching-emergency',
            weight = 0.98
        ))

        pc_client.post_edge(openreview.Edge(invitation = conference.get_paper_assignment_id(conference.get_reviewers_id()),
            readers = [conference.id, 'r2@mit.edu'],
            nonreaders = [f'auai.org/UAI/2019/Conference/Paper{blinded_notes[0].number}/Authors'],
            writers = [conference.id, f'auai.org/UAI/2019/Conference/Paper{blinded_notes[0].number}/Senior_Program_Committee'],
            signatures = [conference.id],
            head = blinded_notes[0].id,
            tail = 'r2@mit.edu',
            label = 'rev-matching-emergency',
            weight = 0.98
        ))

        pc_client.post_edge(openreview.Edge(invitation = conference.get_paper_assignment_id(conference.get_reviewers_id()),
            readers = [conference.id, 'r2@google.com'],
            nonreaders = [f'auai.org/UAI/2019/Conference/Paper{blinded_notes[1].number}/Authors'],
            writers = [conference.id, f'auai.org/UAI/2019/Conference/Paper{blinded_notes[1].number}/Senior_Program_Committee'],
            signatures = [conference.id],
            head = blinded_notes[1].id,
            tail = 'r2@google.com',
            label = 'rev-matching-emergency',
            weight = 0.98
        ))

        conference.set_assignments(assignment_title='rev-matching-emergency', committee_id='auai.org/UAI/2019/Conference/Program_Committee')

        revs_paper0 = pc_client.get_group(conference.get_id()+'/Paper{x}/Program_Committee'.format(x=blinded_notes[0].number))
        assert ['r3@fb.com', '~Reviewer_One1', 'r2@mit.edu'] == revs_paper0.members
        assert pc_client.get_group(conference.get_id()+'/Paper{x}/AnonReviewer1'.format(x=blinded_notes[0].number)).members == ['r3@fb.com']
        assert pc_client.get_group(conference.get_id()+'/Paper{x}/AnonReviewer2'.format(x=blinded_notes[0].number)).members == ['~Reviewer_One1']
        assert pc_client.get_group(conference.get_id()+'/Paper{x}/AnonReviewer3'.format(x=blinded_notes[0].number)).members == ['r2@mit.edu']


        revs_paper1 = pc_client.get_group(conference.get_id()+'/Paper{x}/Program_Committee'.format(x=blinded_notes[1].number))
        assert ['~Reviewer_One1', 'r2@google.com'] == revs_paper1.members
        assert pc_client.get_group(conference.get_id()+'/Paper{x}/AnonReviewer1'.format(x=blinded_notes[1].number)).members == ['~Reviewer_One1']
        assert pc_client.get_group(conference.get_id()+'/Paper{x}/AnonReviewer2'.format(x=blinded_notes[1].number)).members == ['r2@google.com']

        revs_paper2 = pc_client.get_group(conference.get_id()+'/Paper{x}/Program_Committee'.format(x=blinded_notes[2].number))
        assert ['r2@google.com'] == revs_paper2.members
        assert pc_client.get_group(conference.get_id()+'/Paper{x}/AnonReviewer1'.format(x=blinded_notes[2].number)).members == ['r2@google.com']
        with pytest.raises(openreview.OpenReviewException, match=r'Group Not Found'):
            assert pc_client.get_group(conference.get_id()+'/Paper{x}/AnonReviewer2'.format(x=blinded_notes[2].number))


        pc_client.remove_members_from_group('auai.org/UAI/2019/Conference/Paper3/AnonReviewer2', ['~Reviewer_One1'])
        pc_client.remove_members_from_group('auai.org/UAI/2019/Conference/Paper3/Program_Committee', ['~Reviewer_One1'])

        pc_client.post_edge(openreview.Edge(invitation = conference.get_paper_assignment_id(conference.get_reviewers_id()),
            readers = [conference.id, 'r2@google.com'],
            nonreaders = [f'auai.org/UAI/2019/Conference/Paper{blinded_notes[0].number}/Authors'],
            writers = [conference.id, f'auai.org/UAI/2019/Conference/Paper{blinded_notes[0].number}/Senior_Program_Committee'],
            signatures = [conference.id],
            head = blinded_notes[0].id,
            tail = 'r2@google.com',
            label = 'rev-matching-emergency-2',
            weight = 0.98
        ))

        conference.set_assignments(assignment_title='rev-matching-emergency-2', committee_id='auai.org/UAI/2019/Conference/Program_Committee')

        revs_paper0 = pc_client.get_group(conference.get_id()+'/Paper{x}/Program_Committee'.format(x=blinded_notes[0].number))
        assert ['r3@fb.com', 'r2@mit.edu', 'r2@google.com'] == revs_paper0.members
        assert pc_client.get_group(conference.get_id()+'/Paper{x}/AnonReviewer1'.format(x=blinded_notes[0].number)).members == ['r3@fb.com']
        assert pc_client.get_group(conference.get_id()+'/Paper{x}/AnonReviewer2'.format(x=blinded_notes[0].number)).members == ['r2@google.com']
        assert pc_client.get_group(conference.get_id()+'/Paper{x}/AnonReviewer3'.format(x=blinded_notes[0].number)).members == ['r2@mit.edu']


        revs_paper1 = pc_client.get_group(conference.get_id()+'/Paper{x}/Program_Committee'.format(x=blinded_notes[1].number))
        assert ['~Reviewer_One1', 'r2@google.com'] == revs_paper1.members
        assert pc_client.get_group(conference.get_id()+'/Paper{x}/AnonReviewer1'.format(x=blinded_notes[1].number)).members == ['~Reviewer_One1']
        assert pc_client.get_group(conference.get_id()+'/Paper{x}/AnonReviewer2'.format(x=blinded_notes[1].number)).members == ['r2@google.com']

        revs_paper2 = pc_client.get_group(conference.get_id()+'/Paper{x}/Program_Committee'.format(x=blinded_notes[2].number))
        assert ['r2@google.com'] == revs_paper2.members
        assert pc_client.get_group(conference.get_id()+'/Paper{x}/AnonReviewer1'.format(x=blinded_notes[2].number)).members == ['r2@google.com']
        with pytest.raises(openreview.OpenReviewException, match=r'Group Not Found'):
            assert pc_client.get_group(conference.get_id()+'/Paper{x}/AnonReviewer2'.format(x=blinded_notes[2].number))

        pc_client.post_edge(openreview.Edge(invitation = conference.get_paper_assignment_id(conference.get_reviewers_id()),
            readers = [conference.id, 'r2@google.com'],
            nonreaders = [f'auai.org/UAI/2019/Conference/Paper{blinded_notes[2].number}/Authors'],
            writers = [conference.id, f'auai.org/UAI/2019/Conference/Paper{blinded_notes[2].number}/Senior_Program_Committee'],
            signatures = [conference.id],
            head = blinded_notes[2].id,
            tail = 'r2@google.com',
            label = 'rev-matching-emergency-3',
            weight = 0.98
        ))

        conference.set_assignments(assignment_title='rev-matching-emergency-3', overwrite=True, committee_id='auai.org/UAI/2019/Conference/Program_Committee')

        revs_paper0 = pc_client.get_group(conference.get_id()+'/Paper{x}/Program_Committee'.format(x=blinded_notes[0].number))
        assert [] == revs_paper0.members
        with pytest.raises(openreview.OpenReviewException, match=r'Group Not Found'):
            assert pc_client.get_group(conference.get_id()+'/Paper{x}/AnonReviewer1'.format(x=blinded_notes[0].number))
        with pytest.raises(openreview.OpenReviewException, match=r'Group Not Found'):
            assert pc_client.get_group(conference.get_id()+'/Paper{x}/AnonReviewer2'.format(x=blinded_notes[0].number))
        with pytest.raises(openreview.OpenReviewException, match=r'Group Not Found'):
            assert pc_client.get_group(conference.get_id()+'/Paper{x}/AnonReviewer3'.format(x=blinded_notes[0].number))


        revs_paper1 = pc_client.get_group(conference.get_id()+'/Paper{x}/Program_Committee'.format(x=blinded_notes[1].number))
        assert [] == revs_paper1.members
        with pytest.raises(openreview.OpenReviewException, match=r'Group Not Found'):
            assert pc_client.get_group(conference.get_id()+'/Paper{x}/AnonReviewer1'.format(x=blinded_notes[1].number))
        with pytest.raises(openreview.OpenReviewException, match=r'Group Not Found'):
            assert pc_client.get_group(conference.get_id()+'/Paper{x}/AnonReviewer2'.format(x=blinded_notes[1].number))

        revs_paper2 = pc_client.get_group(conference.get_id()+'/Paper{x}/Program_Committee'.format(x=blinded_notes[2].number))
        assert ['r2@google.com'] == revs_paper2.members
        assert pc_client.get_group(conference.get_id()+'/Paper{x}/AnonReviewer1'.format(x=blinded_notes[2].number)).members == ['r2@google.com']
        with pytest.raises(openreview.OpenReviewException, match=r'Group Not Found'):
            assert pc_client.get_group(conference.get_id()+'/Paper{x}/AnonReviewer2'.format(x=blinded_notes[2].number))

        now = datetime.datetime.now()
        conference.set_review_stage(openreview.ReviewStage(start_date = now))

        invitation = pc_client.get_invitation(id='auai.org/UAI/2019/Conference/-/Official_Review')
        assert invitation

        conference.set_assignments(assignment_title='rev-matching-emergency-3', overwrite=True, committee_id='auai.org/UAI/2019/Conference/Program_Committee')

        revs_paper0 = pc_client.get_group(conference.get_id()+'/Paper{x}/Program_Committee'.format(x=blinded_notes[0].number))
        assert [] == revs_paper0.members
        with pytest.raises(openreview.OpenReviewException, match=r'Group Not Found'):
            assert pc_client.get_group(conference.get_id()+'/Paper{x}/AnonReviewer1'.format(x=blinded_notes[0].number))
        with pytest.raises(openreview.OpenReviewException, match=r'Group Not Found'):
            assert pc_client.get_group(conference.get_id()+'/Paper{x}/AnonReviewer2'.format(x=blinded_notes[0].number))
        with pytest.raises(openreview.OpenReviewException, match=r'Group Not Found'):
            assert pc_client.get_group(conference.get_id()+'/Paper{x}/AnonReviewer3'.format(x=blinded_notes[0].number))


        revs_paper1 = pc_client.get_group(conference.get_id()+'/Paper{x}/Program_Committee'.format(x=blinded_notes[1].number))
        assert [] == revs_paper1.members
        with pytest.raises(openreview.OpenReviewException, match=r'Group Not Found'):
            assert pc_client.get_group(conference.get_id()+'/Paper{x}/AnonReviewer1'.format(x=blinded_notes[1].number))
        with pytest.raises(openreview.OpenReviewException, match=r'Group Not Found'):
            assert pc_client.get_group(conference.get_id()+'/Paper{x}/AnonReviewer2'.format(x=blinded_notes[1].number))

        revs_paper2 = pc_client.get_group(conference.get_id()+'/Paper{x}/Program_Committee'.format(x=blinded_notes[2].number))
        assert ['r2@google.com'] == revs_paper2.members
        assert pc_client.get_group(conference.get_id()+'/Paper{x}/AnonReviewer1'.format(x=blinded_notes[2].number)).members == ['r2@google.com']
        with pytest.raises(openreview.OpenReviewException, match=r'Group Not Found'):
            assert pc_client.get_group(conference.get_id()+'/Paper{x}/AnonReviewer2'.format(x=blinded_notes[2].number))

        reviewer_client = helpers.create_user('r2@google.com', 'Reviewer', 'Two')
        conference.set_assignment('ac1@cmu.edu', 1, is_area_chair = True)

        review_note = reviewer_client.post_note(openreview.Note(
            invitation='auai.org/UAI/2019/Conference/Paper1/-/Official_Review',
            forum=blinded_notes[2].id,
            replyto=blinded_notes[2].id,
            content={
                'title': 'review',
                'review': 'this is a good paper',
                'rating': '1: Trivial or wrong',
                'confidence': "1: The reviewer's evaluation is an educated guess"
            },
            readers=[
                "auai.org/UAI/2019/Conference/Program_Chairs",
                "auai.org/UAI/2019/Conference/Paper1/Senior_Program_Committee",
                'auai.org/UAI/2019/Conference/Paper1/AnonReviewer1'
            ],
            nonreaders=["auai.org/UAI/2019/Conference/Paper1/Authors"],
            writers=[
                "auai.org/UAI/2019/Conference",
                'auai.org/UAI/2019/Conference/Paper1/AnonReviewer1'
            ],
            signatures=['auai.org/UAI/2019/Conference/Paper1/AnonReviewer1']
        ))

        helpers.await_queue()
        process_logs = client.get_process_logs(id = review_note.id)
        assert len(process_logs) == 1
        assert process_logs[0]['status'] == 'ok'

        pc_client.post_edge(openreview.Edge(invitation = conference.get_paper_assignment_id(conference.get_reviewers_id()),
            readers = [conference.id, '~Reviewer_One1'],
            nonreaders = [f'auai.org/UAI/2019/Conference/Paper{blinded_notes[2].number}/Authors'],
            writers = [conference.id, f'auai.org/UAI/2019/Conference/Paper{blinded_notes[2].number}/Senior_Program_Committee'],
            signatures = [conference.id],
            head = blinded_notes[2].id,
            tail = '~Reviewer_One1',
            label = 'rev-matching-emergency-4',
            weight = 0.98
        ))

        with pytest.raises(openreview.OpenReviewException, match=r'Can not overwrite assignments when there are reviews posted.'):
            conference.set_assignments(assignment_title='rev-matching-emergency-4', overwrite=True, committee_id='auai.org/UAI/2019/Conference/Program_Committee')

    def test_set_reviewers_assignments_as_author(self, conference, pc_client, helpers):

        pc2_client = helpers.create_user('pc3@mail.com', 'PC', 'Three')
        pc2_client.impersonate(conference.id)

        conference.client = pc2_client

        blinded_notes = list(conference.get_submissions(sort='tmdate'))

        pc2_client.post_edge(openreview.Edge(invitation = conference.get_paper_assignment_id(conference.get_reviewers_id()),
            readers = [conference.id, '~Reviewer_One1'],
            nonreaders = [f'auai.org/UAI/2019/Conference/Paper{blinded_notes[1].number}/Authors'],
            writers = [conference.id, f'auai.org/UAI/2019/Conference/Paper{blinded_notes[1].number}/Senior_Program_Committee'],
            signatures = [conference.id],
            head = blinded_notes[1].id,
            tail = '~Reviewer_One1',
            label = 'rev-matching-emergency-6',
            weight = 0.98
        ))

        pc2_client.post_edge(openreview.Edge(invitation = conference.get_paper_assignment_id(conference.get_reviewers_id()),
            readers = [conference.id, 'r3@fb.com'],
            nonreaders = [f'auai.org/UAI/2019/Conference/Paper{blinded_notes[0].number}/Authors'],
            writers = [conference.id, f'auai.org/UAI/2019/Conference/Paper{blinded_notes[0].number}/Senior_Program_Committee'],
            signatures = [conference.id],
            head = blinded_notes[0].id,
            tail = 'r3@fb.com',
            label = 'rev-matching-emergency-6',
            weight = 0.98
        ))

        conference.set_assignments(assignment_title='rev-matching-emergency-6', committee_id='auai.org/UAI/2019/Conference/Program_Committee')

        revs_paper0 = pc_client.get_group(conference.get_id()+'/Paper{x}/Program_Committee'.format(x=blinded_notes[0].number))
        assert ['r3@fb.com'] == revs_paper0.members

        revs_paper1 = pc_client.get_group(conference.get_id()+'/Paper{x}/Program_Committee'.format(x=blinded_notes[1].number))
        assert ['~Reviewer_One1'] == revs_paper1.members

        revs_paper2 = pc_client.get_group(conference.get_id()+'/Paper{x}/Program_Committee'.format(x=blinded_notes[2].number))
        assert ['r2@google.com'] == revs_paper2.members


    def test_set_ac_assigments(self, conference, pc_client, test_client, helpers):

        conference.set_area_chairs(['ac1@cmu.edu', 'ac2@umass.edu'])
        blinded_notes = list(conference.get_submissions(sort='tmdate'))

        edges = pc_client.get_edges(
            invitation='auai.org/UAI/2019/Conference/Senior_Program_Committee/-/Proposed_Assignment',
            label='ac-matching'
        )
        assert 0 == len(edges)

        #AC assignments
        pc_client.post_edge(openreview.Edge(invitation = 'auai.org/UAI/2019/Conference/Senior_Program_Committee/-/Proposed_Assignment',
            readers = [conference.id, 'ac1@cmu.edu'],
            nonreaders = [conference.get_authors_id(number=blinded_notes[0].number)],
            writers = [conference.id],
            signatures = [conference.id],
            head = blinded_notes[0].id,
            tail = 'ac1@cmu.edu',
            label = 'ac-matching',
            weight = 0.98
        ))

        pc_client.post_edge(openreview.Edge(invitation = 'auai.org/UAI/2019/Conference/Senior_Program_Committee/-/Proposed_Assignment',
            readers = [conference.id, 'ac2@umass.edu'],
            nonreaders = [conference.get_authors_id(number=blinded_notes[1].number)],
            writers = [conference.id],
            signatures = [conference.id],
            head = blinded_notes[1].id,
            tail = 'ac2@umass.edu',
            label = 'ac-matching',
            weight = 0.87
        ))

        pc_client.post_edge(openreview.Edge(invitation = 'auai.org/UAI/2019/Conference/Senior_Program_Committee/-/Proposed_Assignment',
            readers = [conference.id, 'ac2@umass.edu'],
            nonreaders = [conference.get_authors_id(number=blinded_notes[2].number)],
            writers = [conference.id],
            signatures = [conference.id],
            head = blinded_notes[2].id,
            tail = 'ac2@umass.edu',
            label = 'ac-matching',
            weight = 0.87
        ))

        edges = pc_client.get_edges(
            invitation='auai.org/UAI/2019/Conference/Senior_Program_Committee/-/Proposed_Assignment',
            label='ac-matching'
        )
        assert 3 == len(edges)

        conference.set_assignments(assignment_title='ac-matching', committee_id='auai.org/UAI/2019/Conference/Senior_Program_Committee')

        assert pc_client.get_group('auai.org/UAI/2019/Conference/Paper1/Senior_Program_Committee').members == ['ac2@umass.edu']
        assert pc_client.get_group('auai.org/UAI/2019/Conference/Paper1/Area_Chair1').members == ['ac2@umass.edu']

        assert pc_client.get_group('auai.org/UAI/2019/Conference/Paper2/Senior_Program_Committee').members == ['ac2@umass.edu']
        assert pc_client.get_group('auai.org/UAI/2019/Conference/Paper2/Area_Chair1').members == ['ac2@umass.edu']

        assert pc_client.get_group('auai.org/UAI/2019/Conference/Paper3/Senior_Program_Committee').members == ['ac1@cmu.edu']
        assert pc_client.get_group('auai.org/UAI/2019/Conference/Paper3/Area_Chair1').members == ['ac1@cmu.edu']


        pc_client.post_edge(openreview.Edge(invitation = 'auai.org/UAI/2019/Conference/Senior_Program_Committee/-/Proposed_Assignment',
            readers = [conference.id, 'ac1@cmu.edu'],
            nonreaders = [conference.get_authors_id(number=blinded_notes[1].number)],
            writers = [conference.id],
            signatures = [conference.id],
            head = blinded_notes[1].id,
            tail = 'ac1@cmu.edu',
            label = 'ac-matching-2',
            weight = 0.98
        ))

        pc_client.post_edge(openreview.Edge(invitation = 'auai.org/UAI/2019/Conference/Senior_Program_Committee/-/Proposed_Assignment',
            readers = [conference.id, 'ac2@umass.edu'],
            nonreaders = [conference.get_authors_id(number=blinded_notes[0].number)],
            writers = [conference.id],
            signatures = [conference.id],
            head = blinded_notes[0].id,
            tail = 'ac2@umass.edu',
            label = 'ac-matching-2',
            weight = 0.87
        ))

        conference.set_assignments(assignment_title='ac-matching-2', overwrite=True, committee_id='auai.org/UAI/2019/Conference/Senior_Program_Committee')

        assert pc_client.get_group('auai.org/UAI/2019/Conference/Paper3/Senior_Program_Committee').members == ['ac2@umass.edu']
        assert pc_client.get_group('auai.org/UAI/2019/Conference/Paper3/Area_Chair1').members == ['ac2@umass.edu']

        assert pc_client.get_group('auai.org/UAI/2019/Conference/Paper2/Senior_Program_Committee').members == ['ac1@cmu.edu']
        assert pc_client.get_group('auai.org/UAI/2019/Conference/Paper2/Area_Chair1').members == ['ac1@cmu.edu']

        assert pc_client.get_group('auai.org/UAI/2019/Conference/Paper1/Senior_Program_Committee').members == []
        with pytest.raises(openreview.OpenReviewException, match=r'Group Not Found'):
            assert pc_client.get_group('auai.org/UAI/2019/Conference/Paper1/Area_Chair1')


    def test_setup_matching_with_mentors(self, conference, pc_client, helpers):

        mentors=pc_client.post_group(openreview.Group(id=conference.id + '/Reviewers_Mentors',
            readers = [conference.id],
            writers = [conference.id],
            signatures = [conference.id],
            signatories = [conference.id],
            members = ['ac1@cmu.edu', 'ac2@umass.edu']
        ))

        mentees=pc_client.post_group(openreview.Group(id=conference.id + '/Reviewers_Mentees',
            readers = [conference.id],
            writers = [conference.id],
            signatures = [conference.id],
            signatories = [conference.id],
            members = ['~Reviewer_One1', 'r2@google.com', 'r3@fb.com']
        ))

        with open(os.path.join(os.path.dirname(__file__), 'data/mentors_affinity_scores.csv'), 'w') as file_handle:
            writer = csv.writer(file_handle)
            for mentor in mentors.members:
                for mentee in mentees.members:
                    writer.writerow([mentee, mentor, round(random.random(), 2)])

        conference.setup_matching(committee_id=conference.id + '/Reviewers_Mentors',
        affinity_score_file=os.path.join(os.path.dirname(__file__), 'data/mentors_affinity_scores.csv'),
        alternate_matching_group=conference.id + '/Reviewers_Mentees')

        affinity_scores = pc_client.get_edges(invitation=conference.id + '/Reviewers_Mentors/-/Affinity_Score')
        assert len(affinity_scores) == 6

    def test_desk_reject_expire_edges(self, conference, client, pc_client, helpers):
        note = conference.get_submissions()[0]

        desk_reject_note = openreview.Note(
            invitation=f'{conference.id}/Paper{note.number}/-/Desk_Reject',
            forum=note.forum,
            replyto=note.forum,
            readers=[conference.id,
                     conference.get_authors_id(note.number),
                     conference.get_reviewers_id(note.number),
                     conference.get_area_chairs_id(note.number),
                     conference.get_program_chairs_id()],
            writers=[conference.get_id(), conference.get_program_chairs_id()],
            signatures=[conference.get_program_chairs_id()],
            content={
                'desk_reject_comments': 'PC has decided to reject this submission.',
                'title': 'Submission Desk Rejected by Program Chairs'
            }
        )

        desk_reject_note = pc_client.post_note(desk_reject_note)

        helpers.await_queue()

        process_logs = client.get_process_logs(id=desk_reject_note.id)
        assert len(process_logs) == 1
        assert process_logs[0]['status'] == 'ok'

        note_proposed_assignment_edges = client.get_edges(
            invitation=conference.get_id() + '/.*/-/Proposed_Assignment',
            head=desk_reject_note.forum)
        assert not note_proposed_assignment_edges

        note_assignment_edges = client.get_edges(
            invitation=conference.get_id() + '/.*/-/Assignment',
            head=desk_reject_note.forum)
        assert not note_assignment_edges
