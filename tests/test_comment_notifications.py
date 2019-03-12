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

class TestCommentNotification():

    def test_notify_all(self, client, test_client):

        builder = openreview.conference.ConferenceBuilder(client)

        builder.set_conference_id('MIDL.io/2019/Conference')
        builder.set_conference_name('Medical Imaging with Deep Learning')
        builder.set_conference_short_name('MIDL 2019')
        builder.set_homepage_header({
        'title': 'Medical Imaging with Deep Learning',
        'subtitle': 'MIDL 2019 Conference',
        'deadline': 'Submission Deadline: 13th of December, 2018',
        'date': '8-10 July 2019',
        'website': 'http://2019.midl.io',
        'location': 'London',
        'instructions': 'Full papers contain well-validated applications or methodological developments of deep learning algorithms in medical imaging. There is no strict limit on paper length. However, we strongly recommend keeping full papers at 8 pages (excluding references and acknowledgements). An appendix section can be added if needed with additional details but must be compiled into a single pdf. The appropriateness of using pages over the recommended page length will be judged by reviewers. All accepted papers will be presented as posters with a selection of these papers will also be invited for oral presentation.<br/><br/> <p><strong>Questions or Concerns</strong></p><p>Please contact the OpenReview support team at <a href=\"mailto:info@openreview.net\">info@openreview.net</a> with any questions or concerns about the OpenReview platform.<br/>    Please contact the MIDL 2019 Program Chairs at <a href=\"mailto:program-chairs@midl.io\">program-chairs@midl.io</a> with any questions or concerns about conference administration or policy.</p><p>We are aware that some email providers inadequately filter emails coming from openreview.net as spam so please check your spam folder regularly.</p>'
        })
        builder.set_conference_submission_name('Full_Submission')
        builder.set_submission_public(True)
        conference = builder.get_result()

        now = datetime.datetime.utcnow()
        invitation = conference.open_submissions(due_date = now + datetime.timedelta(minutes = 10))

        note = openreview.Note(invitation = invitation.id,
            readers = ['everyone'],
            writers = ['~Test_User1', 'author@mail.com', 'author2@mail.com'],
            signatures = ['~Test_User1'],
            content = {
                'title': 'Paper title',
                'abstract': 'This is an abstract',
                'authorids': ['test@mail.com', 'author@mail.com', 'author2@mail.com'],
                'authors': ['Test User', 'Melisa Bok', 'Andrew Mc'],
                'pdf': '/pdf/sdfskdls.pdf'
            }
        )

        note = test_client.post_note(note)
        assert note

        conference.close_submissions()

        conference.set_authors()
        conference.set_program_chairs(emails= ['programchair@midl.io'])
        conference.open_comments(name = 'Official_Comment', public = False, anonymous = True)

        comment_invitation_id = '{conference_id}/-/Paper{number}/Official_Comment'.format(conference_id = conference.id, number = note.number)
        authors_group_id = '{conference_id}/Paper{number}/Authors'.format(conference_id = conference.id, number = note.number)
        reviewers_group_id = '{conference_id}/Paper{number}/Reviewers'.format(conference_id = conference.id, number = note.number)
        anon_reviewers_group_id = '{conference_id}/Paper{number}/AnonReviewer1'.format(conference_id = conference.id, number = note.number)
        acs_group_id = '{conference_id}/Paper{number}/Area_Chairs'.format(conference_id = conference.id, number = note.number)

        openreview.tools.add_assignment(client, note.number, conference.id, 'reviewer@midl.io')
        openreview.tools.add_assignment(client, note.number, conference.id, 'areachair@midl.io', individual_label='Area_Chair', parent_label='Area_Chairs')

        comment_note = openreview.Note(invitation = comment_invitation_id,
            forum = note.id,
            replyto = note.id,
            readers = [authors_group_id, reviewers_group_id, acs_group_id, conference.get_program_chairs_id()],
            writers = [conference.id, 'reviewer@midl.io'],
            signatures = [anon_reviewers_group_id],
            content = {
                'title': 'Comment title',
                'comment': 'This is an comment'
            }
        )
        comment_note = client.post_note(comment_note)

        assert comment_note
        assert comment_note.forum == note.id

        messages = client.get_messages(to = 'author@mail.com')
        assert messages
        assert len(messages) == 2
        assert messages[0]['content']['subject'] == 'MIDL 2019 has received your submission titled Paper title'
        assert messages[1]['content']['subject'] == '[MIDL 2019] Your submission has received a comment. Paper Title: "Paper title"'

        messages = client.get_messages(to = 'test@mail.com')
        assert messages
        assert len(messages) == 3
        assert messages[0]['content']['subject'] == 'OpenReview signup confirmation'
        assert messages[1]['content']['subject'] == 'MIDL 2019 has received your submission titled Paper title'
        assert messages[2]['content']['subject'] == '[MIDL 2019] Your submission has received a comment. Paper Title: "Paper title"'

        messages = client.get_messages(to = 'author2@mail.com')
        assert messages
        assert len(messages) == 2
        assert messages[0]['content']['subject'] == 'MIDL 2019 has received your submission titled Paper title'
        assert messages[1]['content']['subject'] == '[MIDL 2019] Your submission has received a comment. Paper Title: "Paper title"'

        messages = client.get_messages(to = 'reviewer@midl.io')
        assert messages
        assert len(messages) == 1
        assert messages[0]['content']['subject'] == '[MIDL 2019] Comment posted to a paper you are reviewing. Paper Number: 1, Paper Title: "Paper title"'

        messages = client.get_messages(to = 'areachair@midl.io')
        assert messages
        assert len(messages) == 1
        assert messages[0]['content']['subject'] == '[MIDL 2019] Comment posted to a paper in your area. Paper Number: 1, Paper Title: "Paper title"'

        messages = client.get_messages(to = 'programchair@midl.io')
        assert messages
        assert len(messages) == 1
        assert messages[0]['content']['subject'] == '[MIDL 2019] A comment was posted. Paper Number: 1, Paper Title: "Paper title"'

        reply_comment_note = openreview.Note(invitation = comment_invitation_id,
            forum = note.id,
            replyto = comment_note.id,
            readers = [authors_group_id, conference.get_program_chairs_id()],
            writers = [conference.id, 'test@mail.com'],
            signatures = [authors_group_id],
            content = {
                'title': 'Reply to comment title',
                'comment': 'This is a reply to the comment'
            }
        )

        reply_comment_note = test_client.post_note(reply_comment_note)

        messages = client.get_messages(to = 'author@mail.com')
        assert messages
        assert len(messages) == 3
        assert messages[0]['content']['subject'] == 'MIDL 2019 has received your submission titled Paper title'
        assert messages[1]['content']['subject'] == '[MIDL 2019] Your submission has received a comment. Paper Title: "Paper title"'
        assert messages[2]['content']['subject'] == '[MIDL 2019] Your submission has received a comment. Paper Title: "Paper title"'

        messages = client.get_messages(to = 'test@mail.com')
        assert messages
        assert len(messages) == 3
        assert messages[0]['content']['subject'] == 'OpenReview signup confirmation'
        assert messages[1]['content']['subject'] == 'MIDL 2019 has received your submission titled Paper title'
        assert messages[2]['content']['subject'] == '[MIDL 2019] Your submission has received a comment. Paper Title: "Paper title"'

        messages = client.get_messages(to = 'author2@mail.com')
        assert messages
        assert len(messages) == 3
        assert messages[0]['content']['subject'] == 'MIDL 2019 has received your submission titled Paper title'
        assert messages[1]['content']['subject'] == '[MIDL 2019] Your submission has received a comment. Paper Title: "Paper title"'
        assert messages[2]['content']['subject'] == '[MIDL 2019] Your submission has received a comment. Paper Title: "Paper title"'

        messages = client.get_messages(to = 'reviewer@midl.io')
        assert messages
        assert len(messages) == 1
        assert messages[0]['content']['subject'] == '[MIDL 2019] Comment posted to a paper you are reviewing. Paper Number: 1, Paper Title: "Paper title"'

        messages = client.get_messages(to = 'areachair@midl.io')
        assert messages
        assert len(messages) == 1
        assert messages[0]['content']['subject'] == '[MIDL 2019] Comment posted to a paper in your area. Paper Number: 1, Paper Title: "Paper title"'

        messages = client.get_messages(to = 'programchair@midl.io')
        assert messages
        assert len(messages) == 2
        assert messages[0]['content']['subject'] == '[MIDL 2019] A comment was posted. Paper Number: 1, Paper Title: "Paper title"'
        assert messages[1]['content']['subject'] == '[MIDL 2019] A comment was posted. Paper Number: 1, Paper Title: "Paper title"'

        reply2_comment_note = openreview.Note(invitation = comment_invitation_id,
            forum = note.id,
            replyto = comment_note.id,
            readers = [reviewers_group_id, acs_group_id],
            writers = [conference.id, 'reviewer@midl.io'],
            signatures = [anon_reviewers_group_id],
            content = {
                'title': 'Another reply to comment title',
                'comment': 'This is a reply to the comment'
            }
        )

        reply2_comment_note = client.post_note(reply2_comment_note)

        messages = client.get_messages(to = 'author@mail.com')
        assert messages
        assert len(messages) == 3
        assert messages[0]['content']['subject'] == 'MIDL 2019 has received your submission titled Paper title'
        assert messages[1]['content']['subject'] == '[MIDL 2019] Your submission has received a comment. Paper Title: "Paper title"'
        assert messages[2]['content']['subject'] == '[MIDL 2019] Your submission has received a comment. Paper Title: "Paper title"'

        messages = client.get_messages(to = 'test@mail.com')
        assert messages
        assert len(messages) == 3
        assert messages[0]['content']['subject'] == 'OpenReview signup confirmation'
        assert messages[1]['content']['subject'] == 'MIDL 2019 has received your submission titled Paper title'
        assert messages[2]['content']['subject'] == '[MIDL 2019] Your submission has received a comment. Paper Title: "Paper title"'

        messages = client.get_messages(to = 'author2@mail.com')
        assert messages
        assert len(messages) == 3
        assert messages[0]['content']['subject'] == 'MIDL 2019 has received your submission titled Paper title'
        assert messages[1]['content']['subject'] == '[MIDL 2019] Your submission has received a comment. Paper Title: "Paper title"'
        assert messages[2]['content']['subject'] == '[MIDL 2019] Your submission has received a comment. Paper Title: "Paper title"'

        messages = client.get_messages(to = 'reviewer@midl.io')
        assert messages
        assert len(messages) == 2
        assert messages[0]['content']['subject'] == '[MIDL 2019] Comment posted to a paper you are reviewing. Paper Number: 1, Paper Title: "Paper title"'
        assert messages[1]['content']['subject'] == '[MIDL 2019] Comment posted to a paper you are reviewing. Paper Number: 1, Paper Title: "Paper title"'

        messages = client.get_messages(to = 'areachair@midl.io')
        assert messages
        assert len(messages) == 2
        assert messages[0]['content']['subject'] == '[MIDL 2019] Comment posted to a paper in your area. Paper Number: 1, Paper Title: "Paper title"'
        assert messages[1]['content']['subject'] == '[MIDL 2019] Comment posted to a paper in your area. Paper Number: 1, Paper Title: "Paper title"'

        messages = client.get_messages(to = 'programchair@midl.io')
        assert messages
        assert len(messages) == 2
        assert messages[0]['content']['subject'] == '[MIDL 2019] A comment was posted. Paper Number: 1, Paper Title: "Paper title"'
        assert messages[1]['content']['subject'] == '[MIDL 2019] A comment was posted. Paper Number: 1, Paper Title: "Paper title"'

        pc_client = openreview.Client(baseurl = 'http://localhost:3000')
        assert pc_client is not None, "Client is none"
        res = pc_client.register_user(email = 'programchair@midl.io', first = 'Program', last = 'Chair', password = '1234')
        assert res, "Res i none"
        res = pc_client.activate_user('programchair@midl.io', {
            'names': [
                    {
                        'first': 'Program',
                        'last': 'Chair',
                        'username': '~Program_Chair1'
                    }
                ],
            'emails': ['programchair@midl.io'],
            'preferredEmail': 'programchair@midl.io'
            })
        assert res

        reply3_comment_note = openreview.Note(invitation = comment_invitation_id,
            forum = note.id,
            replyto = comment_note.id,
            readers = [reviewers_group_id, acs_group_id, conference.get_program_chairs_id()],
            writers = [conference.id, 'programchair@midl.io'],
            signatures = [conference.get_program_chairs_id()],
            content = {
                'title': 'Another reply to comment title',
                'comment': 'This is a reply to the comment'
            }
        )

        reply3_comment_note = pc_client.post_note(reply3_comment_note)

        messages = client.get_messages(to = 'author@mail.com')
        assert messages
        assert len(messages) == 3
        assert messages[0]['content']['subject'] == 'MIDL 2019 has received your submission titled Paper title'
        assert messages[1]['content']['subject'] == '[MIDL 2019] Your submission has received a comment. Paper Title: "Paper title"'
        assert messages[2]['content']['subject'] == '[MIDL 2019] Your submission has received a comment. Paper Title: "Paper title"'

        messages = client.get_messages(to = 'test@mail.com')
        assert messages
        assert len(messages) == 3
        assert messages[0]['content']['subject'] == 'OpenReview signup confirmation'
        assert messages[1]['content']['subject'] == 'MIDL 2019 has received your submission titled Paper title'
        assert messages[2]['content']['subject'] == '[MIDL 2019] Your submission has received a comment. Paper Title: "Paper title"'

        messages = client.get_messages(to = 'author2@mail.com')
        assert messages
        assert len(messages) == 3
        assert messages[0]['content']['subject'] == 'MIDL 2019 has received your submission titled Paper title'
        assert messages[1]['content']['subject'] == '[MIDL 2019] Your submission has received a comment. Paper Title: "Paper title"'
        assert messages[2]['content']['subject'] == '[MIDL 2019] Your submission has received a comment. Paper Title: "Paper title"'

        messages = client.get_messages(to = 'reviewer@midl.io')
        assert messages
        assert len(messages) == 3
        assert messages[0]['content']['subject'] == '[MIDL 2019] Comment posted to a paper you are reviewing. Paper Number: 1, Paper Title: "Paper title"'
        assert messages[1]['content']['subject'] == '[MIDL 2019] Comment posted to a paper you are reviewing. Paper Number: 1, Paper Title: "Paper title"'
        assert messages[2]['content']['subject'] == '[MIDL 2019] Comment posted to a paper you are reviewing. Paper Number: 1, Paper Title: "Paper title"'

        messages = client.get_messages(to = 'areachair@midl.io')
        assert messages
        assert len(messages) == 3
        assert messages[0]['content']['subject'] == '[MIDL 2019] Comment posted to a paper in your area. Paper Number: 1, Paper Title: "Paper title"'
        assert messages[1]['content']['subject'] == '[MIDL 2019] Comment posted to a paper in your area. Paper Number: 1, Paper Title: "Paper title"'
        assert messages[2]['content']['subject'] == '[MIDL 2019] Comment posted to a paper in your area. Paper Number: 1, Paper Title: "Paper title"'

        messages = client.get_messages(to = 'programchair@midl.io')
        assert messages
        assert len(messages) == 3
        assert messages[0]['content']['subject'] == '[MIDL 2019] A comment was posted. Paper Number: 1, Paper Title: "Paper title"'
        assert messages[1]['content']['subject'] == '[MIDL 2019] A comment was posted. Paper Number: 1, Paper Title: "Paper title"'
        assert messages[2]['content']['subject'] == 'OpenReview signup confirmation'


