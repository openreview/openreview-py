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

class TestOpenSubmissions():

    @pytest.fixture(scope="class")
    def conference(self, client):
        now = datetime.datetime.utcnow()
        #pc_client = openreview.Client(username='pc@eccv.org', password='1234')
        builder = openreview.conference.ConferenceBuilder(client)
        assert builder, 'builder is None'

        builder.set_conference_id('aclweb.org/ACL/2020/Workshop/NLP-COVID')
        builder.set_conference_short_name('NLP-COVID-2020')
        builder.set_override_homepage(True)
        builder.has_area_chairs(False)
        builder.set_submission_stage(double_blind=False, public=True, due_date=now + datetime.timedelta(minutes = 40), email_pcs=True, create_groups=True, create_review_invitation=True)
        builder.set_review_stage(public=True, due_date=now + datetime.timedelta(minutes = 40), email_pcs=True)
        builder.set_comment_stage(allow_public_comments=True, email_pcs=True, reader_selection=True, authors=True)
        builder.set_decision_stage(public=True, due_date=now + datetime.timedelta(minutes = 40), options = ['Accept', 'Reject'], email_authors=True)
        builder.enable_reviewer_reassignment(enable = True)
        conference = builder.get_result()
        conference.set_program_chairs(['pc@aclweb.org'])
        return conference


    def test_post_submission(self, client, conference, test_client):

        note = openreview.Note(invitation = conference.get_submission_id(),
            readers = ['everyone'],
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
        note = test_client.post_note(note)

        time.sleep(2)
        note = client.get_note(note.id)

        process_logs = client.get_process_logs(id = note.id)
        assert len(process_logs) == 1
        assert process_logs[0]['status'] == 'ok'

        messages = client.get_messages(subject = 'NLP-COVID-2020 has received your submission titled Paper title')
        assert len(messages) == 3
        recipients = [m['content']['to'] for m in messages]
        assert 'test@mail.com' in recipients
        assert 'peter@mail.com' in recipients
        assert 'andrew@mail.com' in recipients

        messages = client.get_messages(subject = 'NLP-COVID-2020 has received a new submission titled Paper title')
        assert len(messages) == 1
        recipients = [m['content']['to'] for m in messages]
        assert 'pc@aclweb.org' in recipients

        assert client.get_group('aclweb.org/ACL/2020/Workshop/NLP-COVID/Paper1')
        assert client.get_group('aclweb.org/ACL/2020/Workshop/NLP-COVID/Paper1/Authors')
        assert client.get_group('aclweb.org/ACL/2020/Workshop/NLP-COVID/Paper1/Reviewers')
        assert client.get_group('aclweb.org/ACL/2020/Workshop/NLP-COVID/Paper1/Reviewers/Submitted')
        assert client.get_invitation('aclweb.org/ACL/2020/Workshop/NLP-COVID/Paper1/-/Official_Review')

    def test_post_comments(self, client, conference, test_client):

        submissions = conference.get_submissions()
        assert submissions

        conference.open_comments()

        assert openreview.tools.get_invitation(client, conference.get_invitation_id(name = 'Public_Comment', number = 1))
        assert openreview.tools.get_invitation(client, conference.get_invitation_id(name = 'Official_Comment', number = 1))

        note = openreview.Note(invitation = conference.get_invitation_id(name = 'Official_Comment', number = 1),
            forum = submissions[0].id,
            replyto = submissions[0].id,
            readers = ['everyone'],
            writers = [conference.id, 'aclweb.org/ACL/2020/Workshop/NLP-COVID/Paper1/Authors'],
            signatures = ['aclweb.org/ACL/2020/Workshop/NLP-COVID/Paper1/Authors'],
            content = {
                'title': 'Paper comment',
                'comment': 'This is an abstract'
            }
        )
        note = test_client.post_note(note)

        time.sleep(2)
        note = client.get_note(note.id)

        process_logs = client.get_process_logs(id = note.id)
        assert len(process_logs) == 1
        assert process_logs[0]['status'] == 'ok'


    def test_post_decisions(self, client, conference, helpers):

        submissions = conference.get_submissions()
        assert submissions

        conference.open_decisions()

        assert openreview.tools.get_invitation(client, conference.get_invitation_id(name = 'Decision', number = 1))

        pc_client = helpers.create_user('pc@aclweb.org', 'PC', 'ACL')

        note = openreview.Note(invitation = conference.get_invitation_id(name = 'Decision', number = 1),
            forum = submissions[0].id,
            replyto = submissions[0].id,
            readers = ['everyone'],
            writers = ['aclweb.org/ACL/2020/Workshop/NLP-COVID/Program_Chairs'],
            signatures = ['aclweb.org/ACL/2020/Workshop/NLP-COVID/Program_Chairs'],
            content = {
                'title': 'Paper Decision',
                'decision': 'Accept',
                'comment': 'This is great!'
            }
        )
        note = pc_client.post_note(note)

        time.sleep(2)
        note = client.get_note(note.id)

        process_logs = client.get_process_logs(id = note.id)
        assert len(process_logs) == 1
        assert process_logs[0]['status'] == 'ok'

        messages = client.get_messages(subject = '[NLP-COVID-2020] Decision posted to your submission - Paper number: 1, Paper title: "Paper title"')
        assert len(messages) == 3
        recipients = [m['content']['to'] for m in messages]
        assert 'test@mail.com' in recipients
        assert 'peter@mail.com' in recipients
        assert 'andrew@mail.com' in recipients
