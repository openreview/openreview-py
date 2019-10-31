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

        pc_client = helpers.create_user('pc@eccv.org', 'Program', 'Chair')

        group = pc_client.get_group('thecvf.com/ECCV/2020/Conference')
        assert group
        assert group.web

        pc_group = pc_client.get_group('thecvf.com/ECCV/2020/Conference/Program_Chairs')
        assert pc_group
        assert pc_group.web


    def test_submission_additional_files(self, test_client):

        pc_client = openreview.Client(username='pc@eccv.org', password='1234')
        builder = openreview.conference.ConferenceBuilder(pc_client)
        assert builder, 'builder is None'

        builder.set_conference_id('thecvf.com/ECCV/2020/Conference')
        builder.has_area_chairs(True)
        now = datetime.datetime.utcnow()
        builder.set_submission_stage(double_blind = True,
            public = False,
            due_date = now + datetime.timedelta(minutes = 10),
            additional_fields= {
                'video': {
                    'description': 'Short video with presentation of the paper, it supports: mov, mp4, zip',
                    'required': True,
                    'value-file': {
                        'fileTypes': ['mov', 'mp4', 'zip'],
                        'size': 50000000000
                    }
                },
                'supplemental_material': {
                    'description': 'Paper appendix',
                    'required': False,
                    'value-file': {
                        'fileTypes': ['pdf'],
                        'size': 500000000000
                    }
                }
            })
        conference = builder.get_result()

        note = openreview.Note(invitation = conference.get_submission_id(),
            readers = ['thecvf.com/ECCV/2020/Conference', 'test@mail.com', 'peter@mail.com', 'andrew@mail.com', '~Test_User1'],
            writers = [conference.id, '~Test_User1', 'peter@mail.com', 'andrew@mail.com'],
            signatures = ['~Test_User1'],
            content = {
                'title': 'Paper title',
                'abstract': 'This is an abstract',
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
                        'size': 50000000000
                    }
                },
                'supplemental_material': {
                    'description': 'Paper appendix',
                    'required': False,
                    'value-file': {
                        'fileTypes': ['pdf'],
                        'size': 500000000000
                    }
                }
            })
        conference = builder.get_result()
        conference.create_blind_submissions()
        conference.set_authors()

        notes = conference.get_submissions()
        assert notes
        assert len(notes) == 1
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
                            'size': 50000000000
                        }
                    },
                    'video': {
                        'description': 'Short video with presentation of the paper, it supports: mov, mp4, zip',
                        'required': False,
                        'value-file': {
                            'fileTypes': ['mov', 'mp4', 'zip'],
                            'size': 50000000000
                        }
                    },
                    'supplemental_material': {
                        'description': 'Paper appendix',
                        'required': False,
                        'value-file': {
                            'fileTypes': ['pdf'],
                            'size': 500000000000
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