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
        builder.has_area_chairs(False)
        builder.has_senior_area_chairs(False)
        builder.set_submission_stage(double_blind=False,
            public=True,
            due_date=now + datetime.timedelta(minutes = 40),
            email_pcs=True,
            create_groups=True,
            create_review_invitation=True,
            withdrawn_submission_reveal_authors=True,
            desk_rejected_submission_reveal_authors=True
        )
        builder.set_review_stage(openreview.ReviewStage(public=True, due_date=now + datetime.timedelta(minutes = 40), email_pcs=True))
        builder.set_comment_stage(allow_public_comments=True, email_pcs=True, reader_selection=True, authors=True)
        builder.set_decision_stage(public=True, due_date=now + datetime.timedelta(minutes = 40), options = ['Accept', 'Reject'], email_authors=True)
        builder.enable_reviewer_reassignment(enable = True)
        conference = builder.get_result()
        conference.set_program_chairs(['pc@aclweb.org'])
        return conference


    def test_post_submission(self, client, conference, test_client, helpers):

        assert not conference.legacy_anonids

        note = openreview.Note(invitation = conference.get_submission_id(),
            readers = ['everyone'],
            writers = [conference.id, '~SomeFirstName_User1', 'peter@mail.com', 'andrew@mail.com'],
            signatures = ['~SomeFirstName_User1'],
            content = {
                'title': 'Paper title',
                'abstract': 'This is an abstract',
                'authorids': ['test@mail.com', 'peter@mail.com', 'andrew@mail.com'],
                'authors': ['SomeFirstName User', 'Peter SomeLastName', 'Andrew Mc']
            }
        )
        url = test_client.put_attachment(os.path.join(os.path.dirname(__file__), 'data/paper.pdf'), conference.get_submission_id(), 'pdf')
        note.content['pdf'] = url
        note = test_client.post_note(note)

        helpers.await_queue()
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
        reviewer_group=client.get_group('aclweb.org/ACL/2020/Workshop/NLP-COVID/Paper1/Reviewers')
        assert reviewer_group
        assert reviewer_group.anonids
        assert reviewer_group.readers == ['aclweb.org/ACL/2020/Workshop/NLP-COVID', 'aclweb.org/ACL/2020/Workshop/NLP-COVID/Paper1/Reviewers']
        assert client.get_group('aclweb.org/ACL/2020/Workshop/NLP-COVID/Paper1/Reviewers/Submitted')
        assert client.get_invitation('aclweb.org/ACL/2020/Workshop/NLP-COVID/Paper1/-/Official_Review')

        ## call post submission stage and keep the submissions public
        conference.setup_post_submission_stage(force=True)
        submissions=conference.get_submissions(sort='tmdate')
        assert submissions
        assert submissions[0].readers == ['everyone']
        assert submissions[0].tcdate == submissions[0].tmdate


    def test_post_reviews(self, client, conference, test_client, helpers):

        client.add_members_to_group('aclweb.org/ACL/2020/Workshop/NLP-COVID/Paper1/Reviewers', 'reviewer@aclweb.org')

        groups=client.get_groups(regex='aclweb.org/ACL/2020/Workshop/NLP-COVID/Paper1/Reviewer_')
        assert len(groups)
        assert groups[0].members == ['reviewer@aclweb.org']
        assert groups[0].readers == ['aclweb.org/ACL/2020/Workshop/NLP-COVID', groups[0].id]

        reviewer_client=helpers.create_user('reviewer@aclweb.org', 'Reviewer', 'ACL')

        submissions=reviewer_client.get_notes(invitation='aclweb.org/ACL/2020/Workshop/NLP-COVID/-/Submission', sort='tmdate')
        assert submissions

        note = openreview.Note(invitation = conference.get_invitation_id(name = 'Official_Review', number = 1),
            forum = submissions[0].id,
            replyto = submissions[0].id,
            readers = ['everyone'],
            writers = [groups[0].id],
            signatures = [groups[0].id],
            content = {
                'title': 'Paper review',
                'review': 'This is great',
                'rating': '10: Top 5% of accepted papers, seminal paper',
                'confidence': '5: The reviewer is absolutely certain that the evaluation is correct and very familiar with the relevant literature'
            }
        )
        posted_note = reviewer_client.post_note(note)

        helpers.await_queue()

        process_logs = client.get_process_logs(id = posted_note.id)
        assert len(process_logs) == 1
        assert process_logs[0]['status'] == 'ok'



    def test_post_comments(self, client, conference, test_client, helpers):

        submissions = conference.get_submissions(sort='tmdate')
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

        helpers.await_queue()
        note = client.get_note(note.id)

        process_logs = client.get_process_logs(id = note.id)
        assert len(process_logs) == 1
        assert process_logs[0]['status'] == 'ok'


    def test_post_decisions(self, client, conference, helpers):

        submissions = conference.get_submissions(sort='tmdate')
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

        helpers.await_queue()
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
