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

def _matching_invitation_ids(client, group_id):
    return {
        'assignment_config': '{}/-/Reviewing/Assignment_Configuration'.format(group_id),
        'custom_load': '{}/-/Reviewing/Custom_Load'.format(group_id),
        'conflict': '{}/-/Reviewing/Conflict'.format(group_id),
        'aggregate_score': '{}/-/Reviewing/Aggregate_Score'.format(group_id),
        'paper_assignment': '{}/-/Reviewing/Paper_Assignment'.format(group_id),
        'tpms': '{}/-/Reviewing/TPMS_Score'.format(group_id),
        'subject_area': '{}/-/Reviewing/Subject_Areas_Score'.format(group_id)
    }


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
        url = test_client.put_pdf(os.path.join(os.path.dirname(__file__), 'data/paper.pdf'))
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
        url = test_client.put_pdf(os.path.join(os.path.dirname(__file__), 'data/paper.pdf'))
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
        url = test_client.put_pdf(os.path.join(os.path.dirname(__file__), 'data/paper.pdf'))
        note_3.content['pdf'] = url
        note_3 = test_client.post_note(note_3)

        ## Create blind submissions
        blinded_notes = conference.create_blind_submissions()
        conference.set_authors()

        ac1_client = helpers.create_user('ac1@cmu.edu', 'AreaChair', 'One')
        ac1_client.post_edge(openreview.Edge(invitation = conference.get_bid_id(),
            readers = ['auai.org/UAI/2019/Conference', '~AreaChair_One1'],
            writers = ['auai.org/UAI/2019/Conference', '~AreaChair_One1'],
            signatures = ['~AreaChair_One1'],
            head = blinded_notes[0].id,
            tail = '~AreaChair_One1',
            label = 'High'
        ))
        ac1_client.post_edge(openreview.Edge(invitation = conference.get_bid_id(),
            readers = ['auai.org/UAI/2019/Conference', '~AreaChair_One1'],
            writers = ['auai.org/UAI/2019/Conference', '~AreaChair_One1'],
            signatures = ['~AreaChair_One1'],
            head = blinded_notes[1].id,
            tail = '~AreaChair_One1',
            label = 'Low'
        ))
        ac1_client.post_edge(openreview.Edge(invitation = conference.get_bid_id(),
            readers = ['auai.org/UAI/2019/Conference', '~AreaChair_One1'],
            writers = ['auai.org/UAI/2019/Conference', '~AreaChair_One1'],
            signatures = ['~AreaChair_One1'],
            head = blinded_notes[2].id,
            tail = '~AreaChair_One1',
            label = 'Very Low'
        ))

        r1_client = helpers.create_user('r1@mit.edu', 'Reviewer', 'One')
        r1_client.post_edge(openreview.Edge(invitation = conference.get_bid_id(),
            readers = ['auai.org/UAI/2019/Conference', '~Reviewer_One1'],
            writers = ['auai.org/UAI/2019/Conference', '~Reviewer_One1'],
            signatures = ['~Reviewer_One1'],
            head = blinded_notes[0].id,
            tail = '~Reviewer_One1',
            label = 'Neutral'
        ))
        r1_client.post_edge(openreview.Edge(invitation = conference.get_bid_id(),
            readers = ['auai.org/UAI/2019/Conference', '~Reviewer_One1'],
            writers = ['auai.org/UAI/2019/Conference', '~Reviewer_One1'],
            signatures = ['~Reviewer_One1'],
            head = blinded_notes[1].id,
            tail = '~Reviewer_One1',
            label = 'Very High'
        ))
        r1_client.post_edge(openreview.Edge(invitation = conference.get_bid_id(),
            readers = ['auai.org/UAI/2019/Conference', '~Reviewer_One1'],
            writers = ['auai.org/UAI/2019/Conference', '~Reviewer_One1'],
            signatures = ['~Reviewer_One1'],
            head = blinded_notes[2].id,
            tail = '~Reviewer_One1',
            label = 'Low'
        ))

        # Set up reviewer matching
        conference.setup_matching(
            conference.client.get_group(conference.get_reviewers_id()))

        reviewer_matching_ids = _matching_invitation_ids(
            client, conference.get_reviewers_id())

        assert client.get_invitation(id=reviewer_matching_ids['assignment_config'])
        assert client.get_invitation(id=reviewer_matching_ids['custom_load'])
        assert client.get_invitation(id=reviewer_matching_ids['conflict'])
        assert client.get_invitation(id=reviewer_matching_ids['aggregate_score'])
        assert client.get_invitation(id=reviewer_matching_ids['paper_assignment'])

        # Set up AC matching
        conference.setup_matching(
            conference.client.get_group(conference.get_area_chairs_id()))

        ac_matching_ids = _matching_invitation_ids(
            client, conference.get_area_chairs_id())

        assert client.get_invitation(id=ac_matching_ids['assignment_config'])
        assert client.get_invitation(id=ac_matching_ids['custom_load'])
        assert client.get_invitation(id=ac_matching_ids['conflict'])
        assert client.get_invitation(id=ac_matching_ids['aggregate_score'])
        assert client.get_invitation(id=ac_matching_ids['paper_assignment'])

        bids = client.get_edges(invitation = conference.get_bid_id())
        assert bids
        assert 6 == len(bids)

        custom_loads = []
        custom_loads.extend(
            client.get_edges(invitation=reviewer_matching_ids['custom_load']))
        custom_loads.extend(
            client.get_edges(invitation=ac_matching_ids['custom_load']))
        assert not custom_loads

        conflicts = []
        conflicts.extend(
            client.get_edges(invitation=reviewer_matching_ids['conflict']))
        conflicts.extend(
            client.get_edges(invitation=ac_matching_ids['conflict']))
        assert conflicts
        assert 3 == len(conflicts)

        ac1_conflicts = client.get_edges(
            invitation=ac_matching_ids['conflict'],
            tail='~AreaChair_One1')
        assert ac1_conflicts
        assert len(ac1_conflicts)
        assert ac1_conflicts[0].label == 'cmu.edu'

        r1_conflicts = client.get_edges(
            invitation=reviewer_matching_ids['conflict'],
            tail='~Reviewer_One1')
        assert r1_conflicts
        assert len(r1_conflicts)
        assert r1_conflicts[0].label == 'mit.edu'

        ac2_conflicts = client.get_edges(
            invitation=ac_matching_ids['conflict'],
            tail='ac2@umass.edu')
        assert ac2_conflicts
        assert len(ac2_conflicts)
        assert ac2_conflicts[0].label == 'umass.edu'


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
        conference.setup_matching(
            conference.client.get_group(conference.get_reviewers_id()),
            tpms_score_file=os.path.join(os.path.dirname(__file__), 'data/reviewer_tpms_scores.csv'))

        print(conference.get_reviewers_id())
        reviewer_matching_ids = _matching_invitation_ids(
            client, conference.get_reviewers_id())

        assert client.get_invitation(id=reviewer_matching_ids['assignment_config'])
        assert client.get_invitation(id=reviewer_matching_ids['custom_load'])
        assert client.get_invitation(id=reviewer_matching_ids['conflict'])
        assert client.get_invitation(id=reviewer_matching_ids['aggregate_score'])
        assert client.get_invitation(id=reviewer_matching_ids['paper_assignment'])
        assert client.get_invitation(id=reviewer_matching_ids['tpms'])

        # Set up ac matching
        conference.setup_matching(
            conference.client.get_group(conference.get_area_chairs_id()),
            tpms_score_file=os.path.join(os.path.dirname(__file__), 'data/ac_tpms_scores.csv'))

        ac_matching_ids = _matching_invitation_ids(
            client, conference.get_area_chairs_id())

        assert client.get_invitation(id=ac_matching_ids['assignment_config'])
        assert client.get_invitation(id=ac_matching_ids['custom_load'])
        assert client.get_invitation(id=ac_matching_ids['conflict'])
        assert client.get_invitation(id=ac_matching_ids['aggregate_score'])
        assert client.get_invitation(id=ac_matching_ids['paper_assignment'])
        assert client.get_invitation(id=ac_matching_ids['tpms'])

        bids = client.get_edges(invitation = conference.get_bid_id())
        assert bids
        assert 6 == len(bids)

        custom_loads = []
        custom_loads.extend(client.get_edges(invitation=reviewer_matching_ids['custom_load']))
        custom_loads.extend(client.get_edges(invitation=ac_matching_ids['custom_load']))
        assert not custom_loads

        conflicts = []
        conflicts.extend(
            client.get_edges(invitation=reviewer_matching_ids['conflict']))
        conflicts.extend(
            client.get_edges(invitation=ac_matching_ids['conflict']))
        assert conflicts
        assert 3 == len(conflicts)

        ac1_conflicts = client.get_edges(
            invitation=ac_matching_ids['conflict'], tail='~AreaChair_One1')
        assert ac1_conflicts
        assert len(ac1_conflicts)
        assert ac1_conflicts[0].label == 'cmu.edu'

        r1_conflicts = client.get_edges(
            invitation=reviewer_matching_ids['conflict'], tail='~Reviewer_One1')
        assert r1_conflicts
        assert len(r1_conflicts)
        assert r1_conflicts[0].label == 'mit.edu'

        ac2_conflicts = client.get_edges(
            invitation=ac_matching_ids['conflict'], tail = 'ac2@umass.edu')
        assert ac2_conflicts
        assert len(ac2_conflicts)
        assert ac2_conflicts[0].label == 'umass.edu'

        submissions = conference.get_submissions()
        assert submissions
        assert 3 == len(submissions)

        tpms_scores = []
        tpms_scores.extend(client.get_edges(invitation=reviewer_matching_ids['tpms']))
        tpms_scores.extend(client.get_edges(invitation=ac_matching_ids['tpms']))
        assert tpms_scores
        assert 15 == len(tpms_scores)

        tpms_scores = client.get_edges(
            invitation=reviewer_matching_ids['tpms'],
            tail='r3@fb.com',
            head=submissions[0].id)
        assert tpms_scores
        assert 1 == len(tpms_scores)
        assert tpms_scores[0].weight == 0.21

        tpms_scores = client.get_edges(
            invitation=reviewer_matching_ids['tpms'],
            tail='r3@fb.com',
            head=submissions[1].id)
        assert tpms_scores
        assert 1 == len(tpms_scores)
        assert tpms_scores[0].weight == 0.31

        tpms_scores = client.get_edges(
            invitation=reviewer_matching_ids['tpms'],
            tail='r3@fb.com',
            head=submissions[2].id)
        assert tpms_scores
        assert 1 == len(tpms_scores)
        assert tpms_scores[0].weight == 0.51


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
        conference.setup_matching(
            conference.client.get_group(conference.get_reviewers_id()),
            tpms_score_file=os.path.join(os.path.dirname(__file__), 'data/reviewer_tpms_scores.csv'))

        print(conference.get_reviewers_id())
        reviewer_matching_ids = _matching_invitation_ids(
            client, conference.get_reviewers_id())

        assert client.get_invitation(id=reviewer_matching_ids['custom_load'])
        assert client.get_invitation(id=reviewer_matching_ids['conflict'])

        # Set up ac matching
        conference.setup_matching(
            conference.client.get_group(conference.get_area_chairs_id()),
            tpms_score_file=os.path.join(os.path.dirname(__file__), 'data/ac_tpms_scores.csv'))

        ac_matching_ids = _matching_invitation_ids(
            client, conference.get_area_chairs_id())

        assert client.get_invitation(id=ac_matching_ids['custom_load'])
        assert client.get_invitation(id=ac_matching_ids['conflict'])

        bids = client.get_edges(invitation = conference.get_bid_id())
        assert bids
        assert 6 == len(bids)

        recommendations = client.get_edges(invitation = conference.get_recommendation_id())
        assert recommendations
        assert 3 == len(recommendations)

        custom_loads = []
        custom_loads.extend(client.get_edges(invitation=reviewer_matching_ids['custom_load']))
        custom_loads.extend(client.get_edges(invitation=ac_matching_ids['custom_load']))
        assert not custom_loads

        conflicts = []
        conflicts.extend(client.get_edges(invitation=reviewer_matching_ids['conflict']))
        conflicts.extend(client.get_edges(invitation=ac_matching_ids['conflict']))
        assert conflicts

        ac1_conflicts = client.get_edges(
            invitation=ac_matching_ids['conflict'], tail='~AreaChair_One1')
        assert ac1_conflicts
        assert len(ac1_conflicts)
        assert ac1_conflicts[0].label == 'cmu.edu'

        r1_conflicts = client.get_edges(
            invitation=reviewer_matching_ids['conflict'], tail='~Reviewer_One1')
        assert r1_conflicts
        assert len(r1_conflicts)
        assert r1_conflicts[0].label == 'mit.edu'

        ac2_conflicts = client.get_edges(
            invitation=ac_matching_ids['conflict'], tail='ac2@umass.edu')
        assert ac2_conflicts
        assert len(ac2_conflicts)
        assert ac2_conflicts[0].label == 'umass.edu'

        submissions = conference.get_submissions()
        assert submissions
        assert 3 == len(submissions)

        tpms_scores = []
        tpms_scores.extend(client.get_edges(invitation=reviewer_matching_ids['tpms']))
        tpms_scores.extend(client.get_edges(invitation=ac_matching_ids['tpms']))
        assert tpms_scores
        assert 15 == len(tpms_scores)

        tpms_scores = client.get_edges(
            invitation=reviewer_matching_ids['tpms'],
            tail='r3@fb.com',
            head=submissions[0].id)
        assert tpms_scores
        assert 1 == len(tpms_scores)
        assert tpms_scores[0].weight == 0.21

        tpms_scores = client.get_edges(
            invitation=reviewer_matching_ids['tpms'],
            tail='r3@fb.com',
            head=submissions[1].id)
        assert tpms_scores
        assert 1 == len(tpms_scores)
        assert tpms_scores[0].weight == 0.31

        tpms_scores = client.get_edges(
            invitation=reviewer_matching_ids['tpms'],
            tail='r3@fb.com',
            head=submissions[2].id)
        assert tpms_scores
        assert 1 == len(tpms_scores)
        assert tpms_scores[0].weight == 0.51


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
            content = {
                'title': 'UAI 2019 Registration',
                'subject_areas': ['Algorithms: Approximate Inference', 'Algorithms: Exact Inference'],
                'profile confirmed': 'Yes',
                'TPMS account confirmed': 'Yes'
            }
        ))

        # Set up reviewer matching
        conference.setup_matching(
            conference.client.get_group(conference.get_reviewers_id()))

        reviewer_matching_ids = _matching_invitation_ids(
            client, conference.get_reviewers_id())

        assert client.get_invitation(id=reviewer_matching_ids['subject_area'])
        assert client.get_invitation(id=reviewer_matching_ids['custom_load'])
        assert client.get_invitation(id=reviewer_matching_ids['conflict'])

        # Set up AC matching
        conference.setup_matching(
            conference.client.get_group(conference.get_area_chairs_id()))

        ac_matching_ids = _matching_invitation_ids(
            client, conference.get_area_chairs_id())

        assert client.get_invitation(id=ac_matching_ids['subject_area'])
        assert client.get_invitation(id=ac_matching_ids['custom_load'])
        assert client.get_invitation(id=ac_matching_ids['conflict'])

        custom_load_id = '{}/-/Reviewing/Custom_Load'.format(conference.get_reviewers_id())
        conflict_id = '{}/-/Reviewing/Conflict'.format(conference.get_reviewers_id())
        subject_areas_id = '{}/-/Reviewing/Subject_Areas_Score'.format(conference.get_reviewers_id())


        bids = client.get_edges(invitation = conference.get_bid_id())
        assert bids
        assert 6 == len(bids)

        recommendations = client.get_edges(invitation = conference.get_recommendation_id())
        assert recommendations
        assert 3 == len(recommendations)

        custom_loads = []
        custom_loads.extend(client.get_edges(invitation=reviewer_matching_ids['custom_load']))
        custom_loads.extend(client.get_edges(invitation=ac_matching_ids['custom_load']))
        assert not custom_loads

        conflicts = []
        conflicts.extend(client.get_edges(invitation=reviewer_matching_ids['conflict']))
        conflicts.extend(client.get_edges(invitation=ac_matching_ids['conflict']))
        assert conflicts
        assert 3 == len(conflicts)

        ac1_conflicts = client.get_edges(
            invitation=ac_matching_ids['conflict'], tail='~AreaChair_One1')
        assert ac1_conflicts
        assert len(ac1_conflicts)
        assert ac1_conflicts[0].label == 'cmu.edu'

        r1_conflicts = client.get_edges(
            invitation=reviewer_matching_ids['conflict'], tail='~Reviewer_One1')
        assert r1_conflicts
        assert len(r1_conflicts)
        assert r1_conflicts[0].label == 'mit.edu'

        ac2_conflicts = client.get_edges(
            invitation=ac_matching_ids['conflict'], tail='ac2@umass.edu')
        assert ac2_conflicts
        assert len(ac2_conflicts)
        assert ac2_conflicts[0].label == 'umass.edu'

        submissions = conference.get_submissions()
        assert submissions
        assert 3 == len(submissions)

        tpms_scores = []
        tpms_scores.extend(client.get_edges(invitation=reviewer_matching_ids['tpms']))
        tpms_scores.extend(client.get_edges(invitation=ac_matching_ids['tpms']))
        assert tpms_scores
        assert 15 == len(tpms_scores)

        tpms_scores = client.get_edges(
            invitation=reviewer_matching_ids['tpms'], tail='r3@fb.com', head=submissions[0].id)
        assert tpms_scores
        assert 1 == len(tpms_scores)
        assert tpms_scores[0].weight == 0.21

        tpms_scores = client.get_edges(
            invitation=reviewer_matching_ids['tpms'], tail='r3@fb.com', head=submissions[1].id)
        assert tpms_scores
        assert 1 == len(tpms_scores)
        assert tpms_scores[0].weight == 0.31

        tpms_scores = client.get_edges(
            invitation=reviewer_matching_ids['tpms'], tail='r3@fb.com', head=submissions[2].id)
        assert tpms_scores
        assert 1 == len(tpms_scores)
        assert tpms_scores[0].weight == 0.51

        subject_areas_scores = []
        subject_areas_scores.extend(client.get_edges(invitation=reviewer_matching_ids['subject_area']))
        subject_areas_scores.extend(client.get_edges(invitation=ac_matching_ids['subject_area']))
        assert subject_areas_scores
        assert 3 == len(subject_areas_scores)

        subject_areas_scores = client.get_edges(
            invitation=ac_matching_ids['subject_area'],
            tail='~AreaChair_One1',
            head=submissions[0].id)
        assert subject_areas_scores
        assert 1 == len(subject_areas_scores)
        assert subject_areas_scores[0].weight ==  0.3333333333333333

        subject_areas_scores = client.get_edges(
            invitation=ac_matching_ids['subject_area'],
            tail='~AreaChair_One1',
            head=submissions[1].id)
        assert subject_areas_scores
        assert 1 == len(subject_areas_scores)
        assert subject_areas_scores[0].weight ==  1

        subject_areas_scores = client.get_edges(
            invitation=ac_matching_ids['subject_area'],
            tail='~AreaChair_One1',
            head=submissions[2].id)
        assert subject_areas_scores
        assert 1 == len(subject_areas_scores)
        assert subject_areas_scores[0].weight ==  0.3333333333333333
