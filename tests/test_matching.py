from __future__ import absolute_import, division, print_function, unicode_literals
import openreview
import pytest
import requests
import datetime
import time
import os
import re
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import NoSuchElementException

class TestMatching():

    def test_setup_matching(self, client, test_client, helpers):

        builder = openreview.conference.ConferenceBuilder(client)
        assert builder, 'builder is None'

        builder = openreview.conference.ConferenceBuilder(client)
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
        builder.set_conference_area_chairs_name('Senior_Program_Committee')
        builder.set_conference_reviewers_name('Program_Committee')
        builder.set_override_homepage(True)
        now = datetime.datetime.utcnow()
        builder.set_submission_stage(due_date = now + datetime.timedelta(minutes = 40), double_blind= True, subject_areas=[
            "Algorithms: Approximate Inference",
            "Algorithms: Belief Propagation",
            "Algorithms: Distributed and Parallel",
            "Algorithms: Exact Inference",
        ])

        builder.set_bid_stage(due_date = now + datetime.timedelta(minutes = 40), request_count = 50)
        conference = builder.get_result()
        assert conference, 'conference is None'

        ## Set committee
        conference.set_program_chairs(['pc1@mail.com', 'pc2@mail.com'])
        conference.set_area_chairs(['ac1@cmu.edu', 'ac2@umass.edu'])
        conference.set_reviewers(['r1@mit.edu', 'r2@google.com', 'r3@fb.com'])

        ## Paper 1
        note_1 = openreview.Note(invitation = conference.get_submission_id(),
            readers = ['~Test_User1', 'test@mail.com', 'a1@cmu.edu'],
            writers = [conference.id, '~Test_User1', 'test@mail.com', 'a1@cmu.edu'],
            signatures = ['~Test_User1'],
            content = {
                'title': 'Paper title 1',
                'abstract': 'This is an abstract',
                'authorids': ['test@mail.com', 'a1@cmu.edu'],
                'authors': ['Test User', 'Author 1'],
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
            readers = ['~Test_User1', 'test@mail.com', 'a2@mit.edu'],
            writers = [conference.id, '~Test_User1', 'test@mail.com', 'a2@mit.edu'],
            signatures = ['~Test_User1'],
            content = {
                'title': 'Paper title 2',
                'abstract': 'This is an abstract',
                'authorids': ['test@mail.com', 'a2@mit.edu'],
                'authors': ['Test User', 'Author 2'],
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
            readers = ['~Test_User1', 'test@mail.com', 'a3@umass.edu'],
            writers = [conference.id, '~Test_User1', 'test@mail.com', 'a3@umass.edu'],
            signatures = ['~Test_User1'],
            content = {
                'title': 'Paper title 3',
                'abstract': 'This is an abstract',
                'authorids': ['test@mail.com', 'a3@umass.edu'],
                'authors': ['Test User', 'Author 3'],
                'subject_areas': [
                    'Algorithms: Distributed and Parallel',
                    'Algorithms: Exact Inference'
                ]
            }
        )
        url = test_client.put_attachment(os.path.join(os.path.dirname(__file__), 'data/paper.pdf'), conference.get_submission_id(), 'pdf')
        note_3.content['pdf'] = url
        note_3 = test_client.post_note(note_3)

        ## Create blind submissions
        builder.set_submission_stage(due_date = now, double_blind= True, subject_areas=[
            "Algorithms: Approximate Inference",
            "Algorithms: Belief Propagation",
            "Algorithms: Distributed and Parallel",
            "Algorithms: Exact Inference",
        ])
        conference = builder.get_result()
        blinded_notes = conference.create_blind_submissions()
        conference.set_authors()

        ac1_client = helpers.create_user('ac1@cmu.edu', 'AreaChair', 'One')
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

        r1_client = helpers.create_user('r1@mit.edu', 'Reviewer', 'One')
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

        # Set up reviewer matching
        conference.setup_matching()


        invitation = client.get_invitation(id='auai.org/UAI/2019/Conference/Program_Committee/-/Assignment_Configuration')
        assert invitation
        assert 'scores_specification' in invitation.reply['content']
        assert 'auai.org/UAI/2019/Conference/Program_Committee/-/Bid' in invitation.reply['content']['scores_specification']['default']
        assert client.get_invitation(id='auai.org/UAI/2019/Conference/Program_Committee/-/Custom_Load')
        assert client.get_invitation(id='auai.org/UAI/2019/Conference/Program_Committee/-/Conflict')
        assert client.get_invitation(id='auai.org/UAI/2019/Conference/Program_Committee/-/Aggregate_Score')
        assert client.get_invitation(id='auai.org/UAI/2019/Conference/Program_Committee/-/Paper_Assignment')

        # Set up AC matching
        conference.setup_matching(is_area_chair=True)

        invitation = client.get_invitation(id='auai.org/UAI/2019/Conference/Senior_Program_Committee/-/Assignment_Configuration')
        assert invitation
        assert 'scores_specification' in invitation.reply['content']
        assert 'auai.org/UAI/2019/Conference/Senior_Program_Committee/-/Bid' in invitation.reply['content']['scores_specification']['default']
        assert client.get_invitation(id='auai.org/UAI/2019/Conference/Senior_Program_Committee/-/Custom_Load')
        assert client.get_invitation(id='auai.org/UAI/2019/Conference/Senior_Program_Committee/-/Conflict')
        assert client.get_invitation(id='auai.org/UAI/2019/Conference/Senior_Program_Committee/-/Aggregate_Score')
        assert client.get_invitation(id='auai.org/UAI/2019/Conference/Senior_Program_Committee/-/Paper_Assignment')

        bids = client.get_edges(invitation = conference.get_bid_id(conference.get_area_chairs_id()))
        assert bids
        assert 3 == len(bids)

        bids = client.get_edges(invitation = conference.get_bid_id(conference.get_reviewers_id()))
        assert bids
        assert 3 == len(bids)

        reviewer_custom_loads = client.get_edges(
            invitation='auai.org/UAI/2019/Conference/Program_Committee/-/Custom_Load')
        assert not reviewer_custom_loads

        ac_custom_loads = client.get_edges(
            invitation='auai.org/UAI/2019/Conference/Senior_Program_Committee/-/Custom_Load')
        assert not ac_custom_loads

        reviewer_conflicts = client.get_edges(
            invitation='auai.org/UAI/2019/Conference/Program_Committee/-/Conflict')
        assert 1 == len(reviewer_conflicts)

        ac_conflicts = client.get_edges(
            invitation='auai.org/UAI/2019/Conference/Senior_Program_Committee/-/Conflict')
        assert 2 == len(ac_conflicts)

        ac1_conflicts = client.get_edges(
            invitation='auai.org/UAI/2019/Conference/Senior_Program_Committee/-/Conflict',
            tail='~AreaChair_One1')
        assert ac1_conflicts
        assert len(ac1_conflicts)
        assert ac1_conflicts[0].label == 'Institutional (level 1)'

        r1_conflicts = client.get_edges(
            invitation='auai.org/UAI/2019/Conference/Program_Committee/-/Conflict',
            tail='~Reviewer_One1')
        assert r1_conflicts
        assert len(r1_conflicts)
        assert r1_conflicts[0].label == 'Institutional (level 1)'

        ac2_conflicts = client.get_edges(
            invitation='auai.org/UAI/2019/Conference/Senior_Program_Committee/-/Conflict',
            tail='ac2@umass.edu')
        assert ac2_conflicts
        assert len(ac2_conflicts)
        assert ac2_conflicts[0].label == 'Institutional (level 1)'


    def test_setup_matching_with_tpms(self, client, test_client, helpers):
        builder = openreview.conference.ConferenceBuilder(client)
        assert builder, 'builder is None'

        builder = openreview.conference.ConferenceBuilder(client)
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
        builder.set_conference_area_chairs_name('Senior_Program_Committee')
        builder.set_conference_reviewers_name('Program_Committee')
        builder.set_override_homepage(True)
        now = datetime.datetime.utcnow()
        builder.set_submission_stage(due_date = now + datetime.timedelta(minutes = 40), double_blind= True, subject_areas=[
            "Algorithms: Approximate Inference",
            "Algorithms: Belief Propagation",
            "Algorithms: Distributed and Parallel",
            "Algorithms: Exact Inference",
        ])

        conference = builder.get_result()
        assert conference, 'conference is None'

        # Set up reviewer matching
        conference.setup_matching(tpms_score_file=os.path.join(os.path.dirname(__file__), 'data/reviewer_tpms_scores.csv'))

        print(conference.get_reviewers_id())

        invitation = client.get_invitation(id='auai.org/UAI/2019/Conference/Program_Committee/-/Assignment_Configuration')
        assert invitation
        assert 'scores_specification' in invitation.reply['content']
        assert 'auai.org/UAI/2019/Conference/Program_Committee/-/Bid' in invitation.reply['content']['scores_specification']['default']
        assert 'auai.org/UAI/2019/Conference/Program_Committee/-/TPMS_Score' in invitation.reply['content']['scores_specification']['default']
        assert 'auai.org/UAI/2019/Conference/Program_Committee/-/Subject_Areas_Score' in invitation.reply['content']['scores_specification']['default']
        assert 'auai.org/UAI/2019/Conference/-/Recommendation' not in invitation.reply['content']['scores_specification']['default']
        assert client.get_invitation(id='auai.org/UAI/2019/Conference/Program_Committee/-/Custom_Load')
        assert client.get_invitation(id='auai.org/UAI/2019/Conference/Program_Committee/-/Conflict')
        assert client.get_invitation(id='auai.org/UAI/2019/Conference/Program_Committee/-/Aggregate_Score')
        assert client.get_invitation(id='auai.org/UAI/2019/Conference/Program_Committee/-/Paper_Assignment')
        assert client.get_invitation(id='auai.org/UAI/2019/Conference/Program_Committee/-/TPMS_Score')

        # Set up ac matching
        conference.setup_matching(
            is_area_chair=True,
            tpms_score_file=os.path.join(os.path.dirname(__file__), 'data/ac_tpms_scores.csv'))

        invitation = client.get_invitation(id='auai.org/UAI/2019/Conference/Senior_Program_Committee/-/Assignment_Configuration')
        assert invitation
        assert 'scores_specification' in invitation.reply['content']
        assert 'auai.org/UAI/2019/Conference/Senior_Program_Committee/-/Bid' in invitation.reply['content']['scores_specification']['default']
        assert 'auai.org/UAI/2019/Conference/Senior_Program_Committee/-/TPMS_Score' in invitation.reply['content']['scores_specification']['default']
        assert 'auai.org/UAI/2019/Conference/Senior_Program_Committee/-/Subject_Areas_Score' in invitation.reply['content']['scores_specification']['default']
        assert client.get_invitation(id='auai.org/UAI/2019/Conference/Senior_Program_Committee/-/Custom_Load')
        assert client.get_invitation(id='auai.org/UAI/2019/Conference/Senior_Program_Committee/-/Conflict')
        assert client.get_invitation(id='auai.org/UAI/2019/Conference/Senior_Program_Committee/-/Aggregate_Score')
        assert client.get_invitation(id='auai.org/UAI/2019/Conference/Senior_Program_Committee/-/Paper_Assignment')
        assert client.get_invitation(id='auai.org/UAI/2019/Conference/Senior_Program_Committee/-/TPMS_Score')

        bids = client.get_edges(invitation = conference.get_bid_id(conference.get_area_chairs_id()))
        assert bids
        assert 3 == len(bids)

        bids = client.get_edges(invitation = conference.get_bid_id(conference.get_reviewers_id()))
        assert bids
        assert 3 == len(bids)

        reviewer_custom_loads = client.get_edges(
            invitation='auai.org/UAI/2019/Conference/Program_Committee/-/Custom_Load')
        assert not reviewer_custom_loads

        ac_custom_loads = client.get_edges(
            invitation='auai.org/UAI/2019/Conference/Senior_Program_Committee/-/Custom_Load')
        assert not ac_custom_loads

        reviewer_conflicts = client.get_edges(
            invitation='auai.org/UAI/2019/Conference/Program_Committee/-/Conflict')
        assert 1 == len(reviewer_conflicts)

        ac_conflicts = client.get_edges(
            invitation='auai.org/UAI/2019/Conference/Senior_Program_Committee/-/Conflict')
        assert 2 == len(ac_conflicts)

        ac1_conflicts = client.get_edges(
            invitation='auai.org/UAI/2019/Conference/Senior_Program_Committee/-/Conflict', tail='~AreaChair_One1')
        assert ac1_conflicts
        assert len(ac1_conflicts)
        assert ac1_conflicts[0].label == 'Institutional (level 1)'

        r1_conflicts = client.get_edges(
            invitation='auai.org/UAI/2019/Conference/Program_Committee/-/Conflict', tail='~Reviewer_One1')
        assert r1_conflicts
        assert len(r1_conflicts)
        assert r1_conflicts[0].label == 'Institutional (level 1)'

        ac2_conflicts = client.get_edges(
            invitation='auai.org/UAI/2019/Conference/Senior_Program_Committee/-/Conflict', tail = 'ac2@umass.edu')
        assert ac2_conflicts
        assert len(ac2_conflicts)
        assert ac2_conflicts[0].label == 'Institutional (level 1)'

        submissions = conference.get_submissions()
        assert submissions
        assert 3 == len(submissions)

        reviewer_tpms_scores = client.get_edges(
            invitation='auai.org/UAI/2019/Conference/Program_Committee/-/TPMS_Score')
        assert 9 == len(reviewer_tpms_scores)

        ac_tpms_scores = client.get_edges(
            invitation='auai.org/UAI/2019/Conference/Senior_Program_Committee/-/TPMS_Score')
        assert 6 == len(ac_tpms_scores)

        r3_s0_tpms_scores = client.get_edges(
            invitation='auai.org/UAI/2019/Conference/Program_Committee/-/TPMS_Score',
            tail='r3@fb.com',
            head=submissions[0].id)
        assert r3_s0_tpms_scores
        assert 1 == len(r3_s0_tpms_scores)
        assert r3_s0_tpms_scores[0].weight == 0.21

        r3_s1_tpms_scores = client.get_edges(
            invitation='auai.org/UAI/2019/Conference/Program_Committee/-/TPMS_Score',
            tail='r3@fb.com',
            head=submissions[1].id)
        assert r3_s1_tpms_scores
        assert 1 == len(r3_s1_tpms_scores)
        assert r3_s1_tpms_scores[0].weight == 0.31

        r3_s2_tpms_scores = client.get_edges(
            invitation='auai.org/UAI/2019/Conference/Program_Committee/-/TPMS_Score',
            tail='r3@fb.com',
            head=submissions[2].id)
        assert r3_s2_tpms_scores
        assert 1 == len(r3_s2_tpms_scores)
        assert r3_s2_tpms_scores[0].weight == 0.51


    def test_setup_matching_with_recommendations(self, client, test_client, helpers):
        builder = openreview.conference.ConferenceBuilder(client)
        assert builder, 'builder is None'

        builder = openreview.conference.ConferenceBuilder(client)
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
        builder.set_conference_area_chairs_name('Senior_Program_Committee')
        builder.set_conference_reviewers_name('Program_Committee')
        builder.set_override_homepage(True)
        now = datetime.datetime.utcnow()
        builder.set_submission_stage(due_date = now + datetime.timedelta(minutes = 40), double_blind= True, subject_areas=[
            "Algorithms: Approximate Inference",
            "Algorithms: Belief Propagation",
            "Algorithms: Distributed and Parallel",
            "Algorithms: Exact Inference",
        ])
        conference = builder.get_result()
        assert conference, 'conference is None'

        blinded_notes = list(conference.get_submissions())

        ## Open reviewer recommendations
        now = datetime.datetime.utcnow()
        conference.open_recommendations(due_date = now + datetime.timedelta(minutes = 40))

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
        conference.setup_matching(tpms_score_file=os.path.join(os.path.dirname(__file__), 'data/reviewer_tpms_scores.csv'))

        print(conference.get_reviewers_id())

        invitation = client.get_invitation(id='auai.org/UAI/2019/Conference/Program_Committee/-/Assignment_Configuration')
        assert invitation
        assert 'scores_specification' in invitation.reply['content']
        assert 'auai.org/UAI/2019/Conference/Program_Committee/-/Bid' in invitation.reply['content']['scores_specification']['default']
        assert 'auai.org/UAI/2019/Conference/Program_Committee/-/TPMS_Score' in invitation.reply['content']['scores_specification']['default']
        assert 'auai.org/UAI/2019/Conference/Program_Committee/-/Subject_Areas_Score' in invitation.reply['content']['scores_specification']['default']
        assert 'auai.org/UAI/2019/Conference/-/Recommendation' in invitation.reply['content']['scores_specification']['default']
        assert client.get_invitation(id='auai.org/UAI/2019/Conference/Program_Committee/-/Custom_Load')
        assert client.get_invitation(id='auai.org/UAI/2019/Conference/Program_Committee/-/Conflict')

        # Set up ac matching
        conference.setup_matching(
            is_area_chair=True,
            tpms_score_file=os.path.join(os.path.dirname(__file__), 'data/ac_tpms_scores.csv'))

        assert client.get_invitation(id='auai.org/UAI/2019/Conference/Senior_Program_Committee/-/Custom_Load')
        assert client.get_invitation(id='auai.org/UAI/2019/Conference/Senior_Program_Committee/-/Conflict')

        bids = client.get_edges(invitation = conference.get_bid_id(conference.get_area_chairs_id()))
        assert bids
        assert 3 == len(bids)

        bids = client.get_edges(invitation = conference.get_bid_id(conference.get_reviewers_id()))
        assert bids
        assert 3 == len(bids)

        recommendations = client.get_edges(invitation = conference.get_recommendation_id())
        assert recommendations
        assert 3 == len(recommendations)

        reviewer_custom_loads = client.get_edges(
            invitation='auai.org/UAI/2019/Conference/Program_Committee/-/Custom_Load')
        assert not reviewer_custom_loads

        ac_custom_loads = client.get_edges(
            invitation='auai.org/UAI/2019/Conference/Senior_Program_Committee/-/Custom_Load')
        assert not ac_custom_loads

        reviewer_conflicts = client.get_edges(
            invitation='auai.org/UAI/2019/Conference/Program_Committee/-/Conflict')
        assert 1 == len(reviewer_conflicts)

        ac_conflicts = client.get_edges(
            invitation='auai.org/UAI/2019/Conference/Senior_Program_Committee/-/Conflict')
        assert 2 == len(ac_conflicts)

        ac1_conflicts = client.get_edges(
            invitation='auai.org/UAI/2019/Conference/Senior_Program_Committee/-/Conflict', tail='~AreaChair_One1')
        assert ac1_conflicts
        assert len(ac1_conflicts)
        assert ac1_conflicts[0].label == 'Institutional (level 1)'

        r1_conflicts = client.get_edges(
            invitation='auai.org/UAI/2019/Conference/Program_Committee/-/Conflict', tail='~Reviewer_One1')
        assert r1_conflicts
        assert len(r1_conflicts)
        assert r1_conflicts[0].label == 'Institutional (level 1)'

        ac2_conflicts = client.get_edges(
            invitation='auai.org/UAI/2019/Conference/Senior_Program_Committee/-/Conflict', tail='ac2@umass.edu')
        assert ac2_conflicts
        assert len(ac2_conflicts)
        assert ac2_conflicts[0].label == 'Institutional (level 1)'

        submissions = conference.get_submissions()
        assert submissions
        assert 3 == len(submissions)

        reviewer_tpms_scores = client.get_edges(
            invitation='auai.org/UAI/2019/Conference/Program_Committee/-/TPMS_Score')
        assert 9 == len(reviewer_tpms_scores)

        ac_tpms_scores = client.get_edges(
            invitation='auai.org/UAI/2019/Conference/Senior_Program_Committee/-/TPMS_Score')
        assert 6 == len(ac_tpms_scores)

        r3_s0_tpms_scores = client.get_edges(
            invitation='auai.org/UAI/2019/Conference/Program_Committee/-/TPMS_Score',
            tail='r3@fb.com',
            head=submissions[0].id)
        assert r3_s0_tpms_scores
        assert 1 == len(r3_s0_tpms_scores)
        assert r3_s0_tpms_scores[0].weight == 0.21

        r3_s1_tpms_scores = client.get_edges(
            invitation='auai.org/UAI/2019/Conference/Program_Committee/-/TPMS_Score',
            tail='r3@fb.com',
            head=submissions[1].id)
        assert r3_s1_tpms_scores
        assert 1 == len(r3_s1_tpms_scores)
        assert r3_s1_tpms_scores[0].weight == 0.31

        r3_s2_tpms_scores = client.get_edges(
            invitation='auai.org/UAI/2019/Conference/Program_Committee/-/TPMS_Score',
            tail='r3@fb.com',
            head=submissions[2].id)
        assert r3_s2_tpms_scores
        assert 1 == len(r3_s2_tpms_scores)
        assert r3_s2_tpms_scores[0].weight == 0.51


    def test_setup_matching_with_subject_areas(self, client, test_client, helpers):
        builder = openreview.conference.ConferenceBuilder(client)
        assert builder, 'builder is None'

        builder = openreview.conference.ConferenceBuilder(client)
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
        builder.set_conference_area_chairs_name('Senior_Program_Committee')
        builder.set_conference_reviewers_name('Program_Committee')
        builder.set_override_homepage(True)
        now = datetime.datetime.utcnow()
        builder.set_submission_stage(due_date = now + datetime.timedelta(minutes = 40), double_blind= True, subject_areas=[
            "Algorithms: Approximate Inference",
            "Algorithms: Belief Propagation",
            "Algorithms: Distributed and Parallel",
            "Algorithms: Exact Inference",
        ])
        conference = builder.get_result()
        assert conference, 'conference is None'

        blinded_notes = list(conference.get_submissions())

        ## Open reviewer recommendations
        now = datetime.datetime.utcnow()
        invitation = conference.open_registration(due_date = now + datetime.timedelta(minutes = 40))

        ## Recommend reviewers
        ac1_client = helpers.get_user('ac1@cmu.edu')
        ac1_client.post_note(openreview.Note(invitation = conference.get_registration_id(),
            readers = ['auai.org/UAI/2019/Conference', '~AreaChair_One1'],
            writers = ['auai.org/UAI/2019/Conference', '~AreaChair_One1'],
            signatures = ['~AreaChair_One1'],
            forum = invitation.reply['forum'],
            replyto=invitation.reply['replyto'],
            content = {
                'title': 'UAI 2019 Registration',
                'subject_areas': [
                    'Algorithms: Approximate Inference',
                    'Algorithms: Belief Propagation'
                ],
                'profile confirmed': 'Yes',
                'expertise confirmed': 'Yes',
                'reviewing experience': '2-4 times  - comfortable with the reviewing process'
            }
        ))

        # Set up reviewer matching
        conference.setup_matching()


        assert client.get_invitation(id='auai.org/UAI/2019/Conference/Program_Committee/-/Subject_Areas_Score')
        assert client.get_invitation(id='auai.org/UAI/2019/Conference/Program_Committee/-/Custom_Load')
        assert client.get_invitation(id='auai.org/UAI/2019/Conference/Program_Committee/-/Conflict')

        # Set up AC matching
        conference.setup_matching(is_area_chair=True)

        assert client.get_invitation(id='auai.org/UAI/2019/Conference/Senior_Program_Committee/-/Subject_Areas_Score')
        assert client.get_invitation(id='auai.org/UAI/2019/Conference/Senior_Program_Committee/-/Custom_Load')
        assert client.get_invitation(id='auai.org/UAI/2019/Conference/Senior_Program_Committee/-/Conflict')

        bids = client.get_edges(invitation = conference.get_bid_id(conference.get_area_chairs_id()))
        assert bids
        assert 3 == len(bids)

        bids = client.get_edges(invitation = conference.get_bid_id(conference.get_reviewers_id()))
        assert bids
        assert 3 == len(bids)

        recommendations = client.get_edges(invitation = conference.get_recommendation_id())
        assert recommendations
        assert 3 == len(recommendations)

        reviewer_custom_loads = client.get_edges(
            invitation='auai.org/UAI/2019/Conference/Program_Committee/-/Custom_Load')
        assert not reviewer_custom_loads

        ac_custom_loads = client.get_edges(
            invitation='auai.org/UAI/2019/Conference/Senior_Program_Committee/-/Custom_Load')
        assert not ac_custom_loads

        reviewer_conflicts = client.get_edges(
            invitation='auai.org/UAI/2019/Conference/Program_Committee/-/Conflict')
        assert 1 == len(reviewer_conflicts)

        ac_conflicts = client.get_edges(
            invitation='auai.org/UAI/2019/Conference/Senior_Program_Committee/-/Conflict')
        assert 2 == len(ac_conflicts)

        ac1_conflicts = client.get_edges(
            invitation='auai.org/UAI/2019/Conference/Senior_Program_Committee/-/Conflict',
            tail='~AreaChair_One1')
        assert ac1_conflicts
        assert len(ac1_conflicts)
        assert ac1_conflicts[0].label == 'Institutional (level 1)'

        r1_conflicts = client.get_edges(
            invitation='auai.org/UAI/2019/Conference/Program_Committee/-/Conflict',
            tail='~Reviewer_One1')
        assert r1_conflicts
        assert len(r1_conflicts)
        assert r1_conflicts[0].label == 'Institutional (level 1)'

        ac2_conflicts = client.get_edges(
            invitation='auai.org/UAI/2019/Conference/Senior_Program_Committee/-/Conflict',
            tail='ac2@umass.edu')
        assert ac2_conflicts
        assert len(ac2_conflicts)
        assert ac2_conflicts[0].label == 'Institutional (level 1)'

        submissions = conference.get_submissions()
        assert submissions
        assert 3 == len(submissions)

        reviewer_tpms_scores = client.get_edges(
            invitation='auai.org/UAI/2019/Conference/Program_Committee/-/TPMS_Score')
        assert 9 == len(reviewer_tpms_scores)

        ac_tpms_scores = client.get_edges(
            invitation='auai.org/UAI/2019/Conference/Senior_Program_Committee/-/TPMS_Score')
        assert 6 == len(ac_tpms_scores)

        r3_s0_tpms_scores = client.get_edges(
            invitation='auai.org/UAI/2019/Conference/Program_Committee/-/TPMS_Score',
            tail='r3@fb.com',
            head=submissions[0].id)
        assert r3_s0_tpms_scores
        assert 1 == len(r3_s0_tpms_scores)
        assert r3_s0_tpms_scores[0].weight == 0.21

        r3_s1_tpms_scores = client.get_edges(
            invitation='auai.org/UAI/2019/Conference/Program_Committee/-/TPMS_Score',
            tail='r3@fb.com',
            head=submissions[1].id)
        assert r3_s1_tpms_scores
        assert 1 == len(r3_s1_tpms_scores)
        assert r3_s1_tpms_scores[0].weight == 0.31

        r3_s2_tpms_scores = client.get_edges(
            invitation='auai.org/UAI/2019/Conference/Program_Committee/-/TPMS_Score',
            tail='r3@fb.com',
            head=submissions[2].id)
        assert r3_s2_tpms_scores
        assert 1 == len(r3_s2_tpms_scores)
        assert r3_s2_tpms_scores[0].weight == 0.51

        reviewer_subject_area_scores = client.get_edges(
            invitation='auai.org/UAI/2019/Conference/Program_Committee/-/Subject_Areas_Score')
        assert not reviewer_subject_area_scores

        ac_subject_areas_scores = client.get_edges(
            invitation='auai.org/UAI/2019/Conference/Senior_Program_Committee/-/Subject_Areas_Score')
        assert 3 == len(ac_subject_areas_scores)

        ac1_s0_subject_scores = client.get_edges(
            invitation='auai.org/UAI/2019/Conference/Senior_Program_Committee/-/Subject_Areas_Score',
            tail='~AreaChair_One1',
            head=submissions[0].id)
        assert ac1_s0_subject_scores
        assert 1 == len(ac1_s0_subject_scores)
        assert ac1_s0_subject_scores[0].weight ==  0

        ac1_s1_subject_scores = client.get_edges(
            invitation='auai.org/UAI/2019/Conference/Senior_Program_Committee/-/Subject_Areas_Score',
            tail='~AreaChair_One1',
            head=submissions[1].id)
        assert ac1_s1_subject_scores
        assert 1 == len(ac1_s1_subject_scores)
        assert ac1_s1_subject_scores[0].weight ==  0.3333333333333333

        ac1_s2_subject_scores = client.get_edges(
            invitation='auai.org/UAI/2019/Conference/Senior_Program_Committee/-/Subject_Areas_Score',
            tail='~AreaChair_One1',
            head=submissions[2].id)
        assert ac1_s2_subject_scores
        assert 1 == len(ac1_s2_subject_scores)
        assert ac1_s2_subject_scores[0].weight ==  1
