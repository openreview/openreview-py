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
        builder.set_double_blind(True)
        builder.set_override_homepage(True)
        builder.set_subject_areas([
            "Algorithms: Approximate Inference",
            "Algorithms: Belief Propagation",
            "Algorithms: Distributed and Parallel",
            "Algorithms: Exact Inference",
        ])
        conference = builder.get_result()
        assert conference, 'conference is None'

        ## Set committee
        conference.set_program_chairs(['pc1@mail.com', 'pc2@mail.com'])
        conference.set_area_chairs(['ac1@cmu.edu', 'ac2@umass.edu'])
        conference.set_reviewers(['r1@mit.edu', 'r2@google.com', 'r3@fb.com'])

        ## Open submissions
        now = datetime.datetime.utcnow()
        invitation = conference.open_submissions(due_date = now + datetime.timedelta(minutes = 40))        

        ## Paper 1
        note_1 = openreview.Note(invitation = invitation.id,
            readers = ['~Test_User1', 'test@mail.com', 'a1@cmu.edu'],
            writers = ['~Test_User1', 'test@mail.com', 'a1@cmu.edu'],
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
        note_2 = openreview.Note(invitation = invitation.id,
            readers = ['~Test_User1', 'test@mail.com', 'a2@mit.edu'],
            writers = ['~Test_User1', 'test@mail.com', 'a2@mit.edu'],
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
        note_3 = openreview.Note(invitation = invitation.id,
            readers = ['~Test_User1', 'test@mail.com', 'a3@umass.edu'],
            writers = ['~Test_User1', 'test@mail.com', 'a3@umass.edu'],
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

        ## Open Bidding
        conference.open_bids(due_date = now + datetime.timedelta(minutes = 40), request_count = 50, with_area_chairs = True)

        ac1_client = helpers.create_user('ac1@cmu.edu', 'AreaChair', 'One')
        ac1_client.post_tag(openreview.Tag(invitation = conference.get_bid_id(),
            readers = ['auai.org/UAI/2019/Conference', '~AreaChair_One1'],
            signatures = ['~AreaChair_One1'],
            forum = blinded_notes[0].id,
            tag = 'High'
        ))
        ac1_client.post_tag(openreview.Tag(invitation = conference.get_bid_id(),
            readers = ['auai.org/UAI/2019/Conference', '~AreaChair_One1'],
            signatures = ['~AreaChair_One1'],
            forum = blinded_notes[1].id,
            tag = 'Low'
        ))
        ac1_client.post_tag(openreview.Tag(invitation = conference.get_bid_id(),
            readers = ['auai.org/UAI/2019/Conference', '~AreaChair_One1'],
            signatures = ['~AreaChair_One1'],
            forum = blinded_notes[2].id,
            tag = 'Very Low'
        ))

        r1_client = helpers.create_user('r1@mit.edu', 'Reviewer', 'One')
        r1_client.post_tag(openreview.Tag(invitation = conference.get_bid_id(),
            readers = ['auai.org/UAI/2019/Conference', '~Reviewer_One1'],
            signatures = ['~Reviewer_One1'],
            forum = blinded_notes[0].id,
            tag = 'Neutral'
        ))
        r1_client.post_tag(openreview.Tag(invitation = conference.get_bid_id(),
            readers = ['auai.org/UAI/2019/Conference', '~Reviewer_One1'],
            signatures = ['~Reviewer_One1'],
            forum = blinded_notes[1].id,
            tag = 'Very High'
        ))
        r1_client.post_tag(openreview.Tag(invitation = conference.get_bid_id(),
            readers = ['auai.org/UAI/2019/Conference', '~Reviewer_One1'],
            signatures = ['~Reviewer_One1'],
            forum = blinded_notes[2].id,
            tag = 'Low'
        ))

        ## Set up matching
        metadata_notes = conference.setup_matching()
        assert metadata_notes
        assert len(metadata_notes) == 3

        ## Assert Paper 1 scores
        assert metadata_notes[0].forum == blinded_notes[2].id
        assert len(metadata_notes[0].content['entries']) == 5
        assert metadata_notes[0].content['entries'][0]['userid'] == '~AreaChair_One1'
        assert metadata_notes[0].content['entries'][0]['scores'] == { 'bid': -1 }
        assert metadata_notes[0].content['entries'][0].get('conflicts') is None
        assert metadata_notes[0].content['entries'][1]['userid'] == '~Reviewer_One1'
        assert metadata_notes[0].content['entries'][1]['scores'] == { 'bid': -0.5 }
        assert metadata_notes[0].content['entries'][1].get('conflicts') is None
        assert metadata_notes[0].content['entries'][2]['userid'] == 'r2@google.com'
        assert metadata_notes[0].content['entries'][2]['scores'] == {}
        assert metadata_notes[0].content['entries'][2].get('conflicts') is None
        assert metadata_notes[0].content['entries'][3]['userid'] == 'r3@fb.com'
        assert metadata_notes[0].content['entries'][3]['scores'] == {}
        assert metadata_notes[0].content['entries'][3].get('conflicts') is None
        assert metadata_notes[0].content['entries'][4]['userid'] == 'ac2@umass.edu'
        assert metadata_notes[0].content['entries'][4]['scores'] == {}
        assert metadata_notes[0].content['entries'][4]['conflicts'] == [ 'umass.edu' ]

        ## Assert Paper 2 scores
        assert metadata_notes[1].forum == blinded_notes[1].id
        assert len(metadata_notes[0].content['entries']) == 5
        assert metadata_notes[1].content['entries'][0]['userid'] == '~AreaChair_One1'
        assert metadata_notes[1].content['entries'][0]['scores'] == { 'bid': -0.5 }
        assert metadata_notes[1].content['entries'][0].get('conflicts') is None
        assert metadata_notes[1].content['entries'][1]['userid'] == '~Reviewer_One1'
        assert metadata_notes[1].content['entries'][1]['scores'] == { 'bid': 1 }
        assert metadata_notes[1].content['entries'][1]['conflicts'] == [ 'mit.edu' ]
        assert metadata_notes[1].content['entries'][2]['userid'] == 'r2@google.com'
        assert metadata_notes[1].content['entries'][2]['scores'] == {}
        assert metadata_notes[1].content['entries'][2].get('conflicts') is None
        assert metadata_notes[1].content['entries'][3]['userid'] == 'r3@fb.com'
        assert metadata_notes[1].content['entries'][3]['scores'] == {}
        assert metadata_notes[1].content['entries'][3].get('conflicts') is None
        assert metadata_notes[1].content['entries'][4]['userid'] == 'ac2@umass.edu'
        assert metadata_notes[1].content['entries'][4]['scores'] == {}
        assert metadata_notes[1].content['entries'][4].get('conflicts') is None 

        ## Assert Paper 3 scores
        assert metadata_notes[2].forum == blinded_notes[0].id
        assert len(metadata_notes[2].content['entries']) == 5
        assert metadata_notes[2].content['entries'][0]['userid'] == '~AreaChair_One1'
        assert metadata_notes[2].content['entries'][0]['scores'] == { 'bid': 0.5 }
        assert metadata_notes[2].content['entries'][0]['conflicts'] == [ 'cmu.edu' ]
        assert metadata_notes[2].content['entries'][1]['userid'] == '~Reviewer_One1'
        assert metadata_notes[2].content['entries'][1]['scores'] == {}
        assert metadata_notes[2].content['entries'][1].get('conflicts') is None
        assert metadata_notes[2].content['entries'][2]['userid'] == 'r2@google.com'
        assert metadata_notes[2].content['entries'][2]['scores'] == {}
        assert metadata_notes[2].content['entries'][2].get('conflicts') is None
        assert metadata_notes[2].content['entries'][3]['userid'] == 'r3@fb.com'
        assert metadata_notes[2].content['entries'][3]['scores'] == {}
        assert metadata_notes[2].content['entries'][3].get('conflicts') is None
        assert metadata_notes[2].content['entries'][4]['userid'] == 'ac2@umass.edu'
        assert metadata_notes[2].content['entries'][4]['scores'] == {}
        assert metadata_notes[2].content['entries'][4].get('conflicts') is None        
    