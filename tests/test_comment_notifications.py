from __future__ import absolute_import, division, print_function, unicode_literals
import openreview
import pytest
import requests
import datetime
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
        conference = builder.get_result()

        invitation = conference.open_submissions(due_date = datetime.datetime(2018, 12, 14, 8, 00), public = True)

        note = openreview.Note(invitation = invitation.id,
            readers = ['everyone'],
            writers = ['~Test_User1', 'mbok@mail.com', 'andrew@mail.com'],
            signatures = ['~Test_User1'],
            content = {
                'title': 'Paper title',
                'abstract': 'This is an abstract',
                'authorids': ['test@mail.com', 'mbok@mail.com', 'andrew@mail.com'],
                'authors': ['Test User', 'Melisa Bok', 'Andrew Mc'],
                'pdf': '/pdf/sdfskdls.pdf'
            }
        )

        note = test_client.post_note(note)
        assert note

        conference.close_submissions(freeze_submissions = True)

        conference.set_authors()
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

        response = client.get_messages(to = 'mbok@mail.com')
        assert response
        assert len(response['messages']) == 2
        assert response['messages'][0]['content']['subject'] == 'MIDL 2019 has received your submission titled Paper title'
        assert response['messages'][1]['content']['subject'] == '[MIDL 2019] Your submission has received a comment. Paper Title: "Paper title"'

