from __future__ import absolute_import, division, print_function, unicode_literals
import openreview
import pytest
import requests
import datetime
import time
import os
import re
import csv
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import NoSuchElementException

class TestECCVConference():

    def test_create_conference(self, client, helpers):

        builder = openreview.conference.ConferenceBuilder(client)
        assert builder, 'builder is None'

        builder.set_conference_id('thecvf.com/ECCV/2020/Conference')
        builder.has_area_chairs(True)
        conference = builder.get_result()
        assert conference, 'conference is None'
        conference.set_program_chairs(['pc@eccv.org'])

        pc_client = helpers.create_user('pc@eccv.org', 'Program', 'ECCVChair')

        group = pc_client.get_group('thecvf.com/ECCV/2020/Conference')
        assert group
        assert group.web

        pc_group = pc_client.get_group('thecvf.com/ECCV/2020/Conference/Program_Chairs')
        assert pc_group
        assert pc_group.web

    def test_recruit_reviewer(self, client, helpers, selenium, request_page):

        builder = openreview.conference.ConferenceBuilder(client)
        assert builder, 'builder is None'

        builder.set_conference_id('thecvf.com/ECCV/2020/Conference')
        builder.has_area_chairs(True)
        conference = builder.get_result()
        assert conference, 'conference is None'
        conference.set_program_chairs(['pc@eccv.org'])

        conference.set_recruitment_reduced_load(['4','5','6','7'])
        result = conference.recruit_reviewers(['mbok@mail.com', 'mohit+1@mail.com'])
        assert result
        assert result.id == 'thecvf.com/ECCV/2020/Conference/Reviewers/Invited'
        assert 'mbok@mail.com' in result.members
        assert 'mohit+1@mail.com' in result.members

        messages = client.get_messages(to = 'mohit+1@mail.com', subject = 'thecvf.com/ECCV/2020/Conference: Invitation to Review')
        text = messages[0]['content']['text']
        assert 'Dear invitee,' in text
        assert 'You have been nominated by the program chair committee of  to serve as a reviewer' in text

        reject_url = re.search('http://.*response=No', text).group(0)
        request_page(selenium, reject_url, alert=True)
        notes = selenium.find_element_by_id("notes")
        assert notes
        messages = notes.find_elements_by_tag_name("h3")
        assert messages
        assert 'You have declined the invitation from thecvf.com/ECCV/2020/Conference.' == messages[0].text
        assert 'In case you only declined because you think you cannot handle the maximum load of papers, you can reduce your load slightly. Be aware that this will decrease your overall score for an outstanding reviewer award, since all good reviews will accumulate a positive score. You can request a reduced reviewer load by clicking here: Request reduced load' == messages[1].text

        group = client.get_group('thecvf.com/ECCV/2020/Conference/Reviewers')
        assert group
        assert len(group.members) == 0

        group = client.get_group('thecvf.com/ECCV/2020/Conference/Reviewers/Declined')
        assert group
        assert len(group.members) == 1
        assert 'mohit+1@mail.com' in group.members

        messages = client.get_messages(to='mohit+1@mail.com', subject='[] Reviewer Invitation declined')
        assert messages
        assert len(messages)
        assert messages[0]['content']['text'].startswith('You have declined the invitation to become a Reviewer for .\n\nIf you would like to change your decision, please click the Accept link in the previous invitation email.\n\nIn case you only declined because you think you cannot handle the maximum load of papers, you can reduce your load slightly. Be aware that this will decrease your overall score for an outstanding reviewer award, since all good reviews will accumulate a positive score. You can request a reduced reviewer load by clicking here:')

    def test_submission_additional_files(self, test_client):

        pc_client = openreview.Client(username='pc@eccv.org', password='1234')
        builder = openreview.conference.ConferenceBuilder(pc_client)
        assert builder, 'builder is None'

        builder.set_conference_id('thecvf.com/ECCV/2020/Conference')
        builder.has_area_chairs(True)
        now = datetime.datetime.utcnow()
        builder.set_override_homepage(True)
        builder.set_submission_stage(double_blind = True,
            public = False,
            due_date = now + datetime.timedelta(minutes = 10),
            additional_fields= {
                'video': {
                    'description': 'Short video with presentation of the paper, it supports: mov, mp4, zip',
                    'required': True,
                    'value-file': {
                        'fileTypes': ['mov', 'mp4', 'zip'],
                        'size': 50
                    }
                },
                'supplemental_material': {
                    'description': 'Paper appendix',
                    'required': False,
                    'value-file': {
                        'fileTypes': ['pdf'],
                        'size': 50
                    }
                }
            })
        conference = builder.get_result()

        for i in range(1,6):
            note = openreview.Note(invitation = conference.get_submission_id(),
                readers = ['thecvf.com/ECCV/2020/Conference', 'test@mail.com', 'peter@mail.com', 'andrew@mail.com', '~Test_User1'],
                writers = [conference.id, '~Test_User1', 'peter@mail.com', 'andrew@mail.com'],
                signatures = ['~Test_User1'],
                content = {
                    'title': 'Paper title ' + str(i) ,
                    'abstract': 'This is an abstract ' + str(i),
                    'authorids': ['test@mail.com', 'peter@mail.com', 'andrew@mail.com'],
                    'authors': ['Test User', 'Peter Test', 'Andrew Mc']
                }
            )
            url = test_client.put_attachment(os.path.join(os.path.dirname(__file__), 'data/paper.pdf'), conference.get_submission_id(), 'pdf')
            note.content['pdf'] = url
            url = test_client.put_attachment(os.path.join(os.path.dirname(__file__), 'data/paper.pdf.zip'), conference.get_submission_id(), 'video')
            note.content['video'] = url
            test_client.post_note(note)


    def test_revise_additional_files(self, test_client):

        pc_client = openreview.Client(username='pc@eccv.org', password='1234')
        builder = openreview.conference.ConferenceBuilder(pc_client)
        assert builder, 'builder is None'

        builder.set_conference_id('thecvf.com/ECCV/2020/Conference')
        builder.has_area_chairs(True)
        now = datetime.datetime.utcnow()
        builder.set_submission_stage(double_blind = True,
            public = False,
            due_date = now - datetime.timedelta(minutes = 30),
            additional_fields= {
                'video': {
                    'description': 'Short video with presentation of the paper, it supports: mov, mp4, zip',
                    'required': True,
                    'value-file': {
                        'fileTypes': ['mov', 'mp4', 'zip'],
                        'size': 50
                    }
                },
                'supplemental_material': {
                    'description': 'Paper appendix',
                    'required': False,
                    'value-file': {
                        'fileTypes': ['pdf'],
                        'size': 50
                    }
                }
            })
        conference = builder.get_result()
        conference.create_blind_submissions()
        conference.set_authors()

        notes = conference.get_submissions()
        assert notes
        assert len(notes) == 5
        note = notes[0]

        invitation = openreview.Invitation(
            id = 'thecvf.com/ECCV/2020/Conference/-/Revision',
            readers = ['everyone'],
            writers = [conference.get_id()],
            signatures = [conference.get_id()],
            invitees = note.content['authorids'] + note.signatures,
            reply = {
                'forum': note.original,
                'referent': note.original,
                'readers': {
                    'values-copied': [
                        conference.get_id(),
                        '{signatures}'
                    ]
                },
                'writers': {
                    'values-copied': [
                        conference.get_id(),
                        '{signatures}'
                    ]
                },
                'signatures': {
                    'values-regex': '~.*'
                },
                'content': {
                    'pdf': {
                        'description': 'Paper pdf',
                        'required': False,
                        'value-file': {
                            'fileTypes': ['pdf'],
                            'size': 50
                        }
                    },
                    'video': {
                        'description': 'Short video with presentation of the paper, it supports: mov, mp4, zip',
                        'required': False,
                        'value-file': {
                            'fileTypes': ['mov', 'mp4', 'zip'],
                            'size': 50
                        }
                    },
                    'supplemental_material': {
                        'description': 'Paper appendix',
                        'required': False,
                        'value-file': {
                            'fileTypes': ['pdf'],
                            'size': 50
                        }
                    }
                }
            }
        )

        pc_client.post_invitation(invitation)

        note = openreview.Note(invitation = 'thecvf.com/ECCV/2020/Conference/-/Revision',
            readers = ['thecvf.com/ECCV/2020/Conference', 'test@mail.com', 'peter@mail.com', 'andrew@mail.com', '~Test_User1'],
            writers = [conference.id, '~Test_User1', 'peter@mail.com', 'andrew@mail.com'],
            signatures = ['~Test_User1'],
            referent = note.original,
            forum = note.original,
            content = {
            }
        )
        url = test_client.put_attachment(os.path.join(os.path.dirname(__file__), 'data/paper.pdf'), 'thecvf.com/ECCV/2020/Conference/-/Revision', 'pdf')
        note.content['pdf'] = url
        url = test_client.put_attachment(os.path.join(os.path.dirname(__file__), 'data/paper.pdf'), 'thecvf.com/ECCV/2020/Conference/-/Revision', 'supplemental_material')
        note.content['supplemental_material'] = url
        test_client.post_note(note)

    def test_recommend_reviewers(self, test_client, helpers, selenium, request_page):

        pc_client = openreview.Client(username='pc@eccv.org', password='1234')
        builder = openreview.conference.ConferenceBuilder(pc_client)
        assert builder, 'builder is None'

        builder.set_conference_id('thecvf.com/ECCV/2020/Conference')
        builder.has_area_chairs(True)
        now = datetime.datetime.utcnow()
        builder.set_submission_stage(double_blind = True,
            public = False,
            due_date = now - datetime.timedelta(minutes = 30),
            additional_fields= {
                'video': {
                    'description': 'Short video with presentation of the paper, it supports: mov, mp4, zip',
                    'required': True,
                    'value-file': {
                        'fileTypes': ['mov', 'mp4', 'zip'],
                        'size': 50
                    }
                },
                'supplemental_material': {
                    'description': 'Paper appendix',
                    'required': False,
                    'value-file': {
                        'fileTypes': ['pdf'],
                        'size': 50
                    }
                }
            })
        builder.set_bid_stage()
        conference = builder.get_result()
        assert conference

        r1_client = helpers.create_user('reviewer1@eccv.org', 'Reviewer', 'ECCV_One')
        r2_client = helpers.create_user('reviewer2eccv.org', 'Reviewer', 'ECCV_Two')
        r3_client = helpers.create_user('reviewer3@eccv.org', 'Reviewer', 'ECCV_Three')
        ac1_client = helpers.create_user('ac1@eccv.org', 'AreaChair', 'ECCV_One')
        ac2_client = helpers.create_user('ac2eccv.org', 'AreaChair', 'ECCV_Two')

        conference.set_reviewers(['~Reviewer_ECCV_One1', '~Reviewer_ECCV_Two1', '~Reviewer_ECCV_Three1'])
        conference.set_area_chairs(['~AreaChair_ECCV_One1', '~AreaChair_ECCV_Two1'])
        conference.setup_matching()
        conference.setup_matching(is_area_chair=True)

        blinded_notes = conference.get_submissions()

        ### Bids
        r1_client.post_edge(openreview.Edge(invitation = conference.get_bid_id(conference.get_reviewers_id()),
            readers = [conference.id, conference.get_area_chairs_id(number=blinded_notes[0].number), '~Reviewer_ECCV_One1'],
            writers = [conference.id, '~Reviewer_ECCV_One1'],
            signatures = ['~Reviewer_ECCV_One1'],
            head = blinded_notes[0].id,
            tail = '~Reviewer_ECCV_One1',
            label = 'Neutral'
        ))
        r1_client.post_edge(openreview.Edge(invitation = conference.get_bid_id(conference.get_reviewers_id()),
            readers = [conference.id, conference.get_area_chairs_id(number=blinded_notes[1].number), '~Reviewer_ECCV_One1'],
            writers = [conference.id, '~Reviewer_ECCV_One1'],
            signatures = ['~Reviewer_ECCV_One1'],
            head = blinded_notes[1].id,
            tail = '~Reviewer_ECCV_One1',
            label = 'Very High'
        ))
        r1_client.post_edge(openreview.Edge(invitation = conference.get_bid_id(conference.get_reviewers_id()),
            readers = [conference.id, conference.get_area_chairs_id(number=blinded_notes[4].number), '~Reviewer_ECCV_One1'],
            writers = [conference.id, '~Reviewer_ECCV_One1'],
            signatures = ['~Reviewer_ECCV_One1'],
            head = blinded_notes[4].id,
            tail = '~Reviewer_ECCV_One1',
            label = 'High'
        ))

        r2_client.post_edge(openreview.Edge(invitation = conference.get_bid_id(conference.get_reviewers_id()),
            readers = [conference.id, conference.get_area_chairs_id(number=blinded_notes[2].number), '~Reviewer_ECCV_Two1'],
            writers = [conference.id, '~Reviewer_ECCV_Two1'],
            signatures = ['~Reviewer_ECCV_Two1'],
            head = blinded_notes[2].id,
            tail = '~Reviewer_ECCV_Two1',
            label = 'Neutral'
        ))
        r2_client.post_edge(openreview.Edge(invitation = conference.get_bid_id(conference.get_reviewers_id()),
            readers = [conference.id, conference.get_area_chairs_id(number=blinded_notes[3].number), '~Reviewer_ECCV_Two1'],
            writers = [conference.id, '~Reviewer_ECCV_Two1'],
            signatures = ['~Reviewer_ECCV_Two1'],
            head = blinded_notes[3].id,
            tail = '~Reviewer_ECCV_Two1',
            label = 'Very High'
        ))
        r2_client.post_edge(openreview.Edge(invitation = conference.get_bid_id(conference.get_reviewers_id()),
            readers = [conference.id, conference.get_area_chairs_id(number=blinded_notes[4].number), '~Reviewer_ECCV_Two1'],
            writers = [conference.id, '~Reviewer_ECCV_Two1'],
            signatures = ['~Reviewer_ECCV_Two1'],
            head = blinded_notes[4].id,
            tail = '~Reviewer_ECCV_Two1',
            label = 'High'
        ))

        r3_client.post_edge(openreview.Edge(invitation = conference.get_bid_id(conference.get_reviewers_id()),
            readers = [conference.id, conference.get_area_chairs_id(number=blinded_notes[4].number), '~Reviewer_ECCV_Three1'],
            writers = [conference.id, '~Reviewer_ECCV_Three1'],
            signatures = ['~Reviewer_ECCV_Three1'],
            head = blinded_notes[4].id,
            tail = '~Reviewer_ECCV_Three1',
            label = 'Neutral'
        ))
        r3_client.post_edge(openreview.Edge(invitation = conference.get_bid_id(conference.get_reviewers_id()),
            readers = [conference.id, conference.get_area_chairs_id(number=blinded_notes[2].number), '~Reviewer_ECCV_Three1'],
            writers = [conference.id, '~Reviewer_ECCV_Three1'],
            signatures = ['~Reviewer_ECCV_Three1'],
            head = blinded_notes[2].id,
            tail = '~Reviewer_ECCV_Three1',
            label = 'Very High'
        ))
        r3_client.post_edge(openreview.Edge(invitation = conference.get_bid_id(conference.get_reviewers_id()),
            readers = [conference.id, conference.get_area_chairs_id(number=blinded_notes[0].number), '~Reviewer_ECCV_Three1'],
            writers = [conference.id, '~Reviewer_ECCV_Three1'],
            signatures = ['~Reviewer_ECCV_Three1'],
            head = blinded_notes[0].id,
            tail = '~Reviewer_ECCV_Three1',
            label = 'High'
        ))

        ## Area chairs assignments
        pc_client.post_edge(openreview.Edge(invitation = conference.get_paper_assignment_id(conference.get_area_chairs_id()),
            readers = [conference.id, conference.get_area_chairs_id(number=blinded_notes[0].number)],
            writers = [conference.id],
            signatures = [conference.id],
            head = blinded_notes[0].id,
            tail = '~AreaChair_ECCV_One1',
            label = 'ac-matching',
            weight = 0.98
        ))
        pc_client.post_edge(openreview.Edge(invitation = conference.get_paper_assignment_id(conference.get_area_chairs_id()),
            readers = [conference.id, conference.get_area_chairs_id(number=blinded_notes[1].number)],
            writers = [conference.id],
            signatures = [conference.id],
            head = blinded_notes[1].id,
            tail = '~AreaChair_ECCV_One1',
            label = 'ac-matching',
            weight = 0.88
        ))
        pc_client.post_edge(openreview.Edge(invitation = conference.get_paper_assignment_id(conference.get_area_chairs_id()),
            readers = [conference.id, conference.get_area_chairs_id(number=blinded_notes[2].number)],
            writers = [conference.id],
            signatures = [conference.id],
            head = blinded_notes[2].id,
            tail = '~AreaChair_ECCV_One1',
            label = 'ac-matching',
            weight = 0.79
        ))
        pc_client.post_edge(openreview.Edge(invitation = conference.get_paper_assignment_id(conference.get_area_chairs_id()),
            readers = [conference.id, conference.get_area_chairs_id(number=blinded_notes[3].number)],
            writers = [conference.id],
            signatures = [conference.id],
            head = blinded_notes[3].id,
            tail = '~AreaChair_ECCV_Two1',
            label = 'ac-matching',
            weight = 0.99
        ))
        pc_client.post_edge(openreview.Edge(invitation = conference.get_paper_assignment_id(conference.get_area_chairs_id()),
            readers = [conference.id, conference.get_area_chairs_id(number=blinded_notes[4].number)],
            writers = [conference.id],
            signatures = [conference.id],
            head = blinded_notes[4].id,
            tail = '~AreaChair_ECCV_Two1',
            label = 'ac-matching',
            weight = 0.86
        ))

        conference.set_assignments('ac-matching', is_area_chair=True)
        conference.open_recommendations()

        ## Go to edge browser
        ## http://localhost:3000/edge/browse?start=thecvf.com/ECCV/2020/Conference/Area_Chairs/-/Paper_Assignment,label:ac-matching,tail:~AreaChair_ECCV_One1&traverse=thecvf.com/ECCV/2020/Conference/-/Recommendation&edit=thecvf.com/ECCV/2020/Conference/-/Recommendation&browse=thecvf.com/ECCV/2020/Conference/Reviewers/-/Bid;thecvf.com/ECCV/2020/Conference/Reviewers/-/Conflict
        request_page(selenium, "http://localhost:3000/edge/browse?start=thecvf.com/ECCV/2020/Conference/Area_Chairs/-/Paper_Assignment,label:ac-matching,tail:~AreaChair_ECCV_One1&traverse=thecvf.com/ECCV/2020/Conference/-/Recommendation&edit=thecvf.com/ECCV/2020/Conference/-/Recommendation&browse=thecvf.com/ECCV/2020/Conference/Reviewers/-/Bid;thecvf.com/ECCV/2020/Conference/Reviewers/-/Conflict", ac1_client.token)
