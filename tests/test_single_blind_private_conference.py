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

class TestSingleBlindPrivateConference():

    @pytest.fixture(scope="class")
    def conference(self, client):
        now = datetime.datetime.utcnow()
        #pc_client = openreview.Client(username='pc@eccv.org', password='1234')
        builder = openreview.conference.ConferenceBuilder(client)
        assert builder, 'builder is None'

        builder.set_conference_id('MICCAI.org/2021/Challenges')
        builder.set_conference_short_name('MICCAI 2021')
        builder.has_area_chairs(True)

        builder.set_submission_stage(double_blind = False,
            readers=[openreview.SubmissionStage.Readers.REVIEWERS_ASSIGNED, openreview.SubmissionStage.Readers.AREA_CHAIRS],
            due_date = now + datetime.timedelta(minutes = 10),
            withdrawn_submission_public=False,
            withdrawn_submission_reveal_authors=True,
            email_pcs_on_withdraw=False,
            desk_rejected_submission_public=False,
            desk_rejected_submission_reveal_authors=True)

        conference = builder.get_result()
        conference.set_program_chairs(['pc@miccai.org'])
        return conference

    def test_create_conference(self, client, conference, helpers):

        helpers.create_user('pc@miccai.org', 'Program', 'MICCAIChair')

        pc_client = openreview.Client(username='pc@miccai.org', password='1234')

        group = pc_client.get_group('MICCAI.org/2021/Challenges')
        assert group
        assert group.web

        pc_group = pc_client.get_group('MICCAI.org/2021/Challenges/Program_Chairs')
        assert pc_group
        assert pc_group.web

    def test_submit_papers(self, conference, helpers, test_client, client):

        pdf_url = test_client.put_attachment(
            os.path.join(os.path.dirname(__file__), 'data/paper.pdf'),
            'MICCAI.org/2021/Challenges/-/Submission',
            'pdf'
        )

        domains = ['umass.edu', 'umass.edu', 'fb.com', 'umass.edu', 'google.com', 'mit.edu']
        for i in range(1,6):
            note = openreview.Note(invitation = 'MICCAI.org/2021/Challenges/-/Submission',
                readers = ['MICCAI.org/2021/Challenges', 'test@mail.com', 'peter@mail.com', 'andrew@' + domains[i], '~Test_User1'],
                writers = [conference.id, '~Test_User1', 'peter@mail.com', 'andrew@' + domains[i]],
                signatures = ['~Test_User1'],
                content = {
                    'title': 'Paper title ' + str(i) ,
                    'abstract': 'This is an abstract ' + str(i),
                    'authorids': ['test@mail.com', 'peter@mail.com', 'andrew@' + domains[i]],
                    'authors': ['Test User', 'Peter Test', 'Andrew Mc'],
                    'pdf': pdf_url
                }
            )
            note = test_client.post_note(note)

        conference.setup_post_submission_stage(force=True)

        notes = test_client.get_notes(invitation='MICCAI.org/2021/Challenges/-/Submission')
        assert len(notes) == 5
        assert notes[0].readers == ['MICCAI.org/2021/Challenges/Program_Chairs', 'MICCAI.org/2021/Challenges/Area_Chairs', 'MICCAI.org/2021/Challenges/Paper5/Reviewers', 'MICCAI.org/2021/Challenges/Paper5/Authors']

        invitations = test_client.get_invitations(replyForum=notes[0].id)
        assert len(invitations) == 1
        assert invitations[0].id == 'MICCAI.org/2021/Challenges/Paper5/-/Withdraw'

        invitations = client.get_invitations(replyForum=notes[0].id)
        assert len(invitations) == 2
        assert invitations[0].id == 'MICCAI.org/2021/Challenges/Paper5/-/Desk_Reject'
        assert invitations[1].id == 'MICCAI.org/2021/Challenges/Paper5/-/Withdraw'