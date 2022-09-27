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
        builder = openreview.conference.ConferenceBuilder(client, support_user='openreview.net/Support')
        assert builder, 'builder is None'

        builder.set_conference_id('MICCAI.org/2021/Challenges')
        builder.set_conference_short_name('MICCAI 2021')
        builder.has_area_chairs(True)

        builder.set_submission_stage(double_blind = False,
            readers=[openreview.stages.SubmissionStage.Readers.REVIEWERS_ASSIGNED, openreview.stages.SubmissionStage.Readers.AREA_CHAIRS],
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
                readers = ['MICCAI.org/2021/Challenges', 'test@mail.com', 'peter@mail.com', 'andrew@' + domains[i], '~SomeFirstName_User1'],
                writers = [conference.id, '~SomeFirstName_User1', 'peter@mail.com', 'andrew@' + domains[i]],
                signatures = ['~SomeFirstName_User1'],
                content = {
                    'title': 'Paper title ' + str(i) ,
                    'abstract': 'This is an abstract ' + str(i),
                    'authorids': ['test@mail.com', 'peter@mail.com', 'andrew@' + domains[i]],
                    'authors': ['SomeFirstName User', 'Peter SomeLastName', 'Andrew Mc'],
                    'pdf': pdf_url
                }
            )
            note = test_client.post_note(note)

        conference.setup_post_submission_stage(force=True)

        notes = test_client.get_notes(invitation='MICCAI.org/2021/Challenges/-/Submission', sort='tmdate')
        assert len(notes) == 5
        assert notes[0].readers == ['MICCAI.org/2021/Challenges', 'MICCAI.org/2021/Challenges/Area_Chairs', 'MICCAI.org/2021/Challenges/Paper5/Reviewers', 'MICCAI.org/2021/Challenges/Paper5/Authors']

        invitations = test_client.get_invitations(replyForum=notes[0].id)
        assert len(invitations) == 1
        assert invitations[0].id == 'MICCAI.org/2021/Challenges/Paper5/-/Withdraw'

        invitations = client.get_invitations(replyForum=notes[0].id)
        assert len(invitations) == 2
        invitation_ids = [invitation.id for invitation in invitations]
        assert 'MICCAI.org/2021/Challenges/Paper5/-/Desk_Reject' in invitation_ids
        assert 'MICCAI.org/2021/Challenges/Paper5/-/Withdraw' in invitation_ids

    def test_public_comments(self, conference, helpers, test_client, client):
        notes = test_client.get_notes(invitation='MICCAI.org/2021/Challenges/-/Submission', sort='tmdate')
        assert len(notes) == 5

        comment_invitees = [openreview.stages.CommentStage.Readers.REVIEWERS_ASSIGNED, openreview.stages.CommentStage.Readers.AUTHORS]
        conference.set_comment_stage(openreview.stages.CommentStage(reader_selection=True, email_pcs=True, allow_public_comments=True, invitees=comment_invitees, readers=comment_invitees + [openreview.stages.CommentStage.Readers.EVERYONE]))
        public_comment_invitation = openreview.tools.get_invitation(client, conference.get_invitation_id('Public_Comment', number=1))
        assert public_comment_invitation is None

    def test_decisions(self, conference, helpers, test_client, client):

        conference.set_decision_stage(openreview.stages.DecisionStage(release_to_area_chairs=True))

        submissions=conference.get_submissions(sort='tmdate')
        assert len(submissions) == 5

        client.post_note(openreview.Note(
            invitation='MICCAI.org/2021/Challenges/Paper5/-/Decision',
            forum=submissions[0].id,
            replyto=submissions[0].id,
            readers=['MICCAI.org/2021/Challenges/Program_Chairs', 'MICCAI.org/2021/Challenges/Paper5/Area_Chairs'],
            nonreaders=['MICCAI.org/2021/Challenges/Paper5/Authors'],
            writers=['MICCAI.org/2021/Challenges/Program_Chairs'],
            signatures=['MICCAI.org/2021/Challenges/Program_Chairs'],
            content={
                'title': 'Paper Decision',
                'decision': 'Reject'
            }
        ))

        client.post_note(openreview.Note(
            invitation='MICCAI.org/2021/Challenges/Paper4/-/Decision',
            forum=submissions[1].id,
            replyto=submissions[1].id,
            readers=['MICCAI.org/2021/Challenges/Program_Chairs', 'MICCAI.org/2021/Challenges/Paper4/Area_Chairs'],
            nonreaders=['MICCAI.org/2021/Challenges/Paper4/Authors'],
            writers=['MICCAI.org/2021/Challenges/Program_Chairs'],
            signatures=['MICCAI.org/2021/Challenges/Program_Chairs'],
            content={
                'title': 'Paper Decision',
                'decision': 'Accept (Oral)'
            }
        ))

        client.post_note(openreview.Note(
            invitation='MICCAI.org/2021/Challenges/Paper3/-/Decision',
            forum=submissions[2].id,
            replyto=submissions[2].id,
            readers=['MICCAI.org/2021/Challenges/Program_Chairs', 'MICCAI.org/2021/Challenges/Paper3/Area_Chairs'],
            nonreaders=['MICCAI.org/2021/Challenges/Paper3/Authors'],
            writers=['MICCAI.org/2021/Challenges/Program_Chairs'],
            signatures=['MICCAI.org/2021/Challenges/Program_Chairs'],
            content={
                'title': 'Paper Decision',
                'decision': 'Accept (Poster)'
            }
        ))

    def test_post_decisions(self, conference, helpers, test_client, client, request_page, selenium):

        conference.post_decision_stage(reveal_authors_accepted=True, decision_heading_map={ 'Accept (Poster)': 'Poster', 'Accept (Oral)': 'Oral'}, submission_readers=[openreview.stages.SubmissionStage.Readers.EVERYONE_BUT_REJECTED])

        submissions=conference.get_submissions(number=5)
        assert submissions[0].readers != ['everyone']

        submissions=conference.get_submissions(number=4)
        assert submissions[0].readers == ['everyone']

        submissions=conference.get_submissions(number=3)
        assert submissions[0].readers == ['everyone']

        request_page(selenium, "http://localhost:3030/group?id=MICCAI.org/2021/Challenges", wait_for_element='tabs-container')
        assert "MICCAI 2021 Challenges | OpenReview" in selenium.title
        header = selenium.find_element_by_id('header')
        assert header
        assert "MICCAI.org/2021/Challenges" == header.find_element_by_tag_name("h1").text
        invitation_panel = selenium.find_element_by_id('invitation')
        assert invitation_panel
        assert len(invitation_panel.find_elements_by_tag_name('div')) == 0
        notes_panel = selenium.find_element_by_id('notes')
        assert notes_panel
        tabs = notes_panel.find_element_by_class_name('tabs-container')
        assert tabs
        with pytest.raises(NoSuchElementException):
            notes_panel.find_element_by_class_name('spinner-container')
        assert tabs.find_element_by_id('oral')
        assert tabs.find_element_by_id('poster')

    def test_enable_public_comments(self, conference, helpers, test_client, client):
        notes = test_client.get_notes(invitation='MICCAI.org/2021/Challenges/-/Submission', sort='tmdate')
        assert len(notes) == 5

        conference.submission_stage.papers_released=True
        comment_invitees = [openreview.stages.CommentStage.Readers.REVIEWERS_ASSIGNED, openreview.stages.CommentStage.Readers.AUTHORS]
        conference.set_comment_stage(openreview.stages.CommentStage(reader_selection=True, email_pcs=True, allow_public_comments=True, invitees=comment_invitees, readers=comment_invitees + [openreview.stages.CommentStage.Readers.EVERYONE]))
        public_comment_invitation = openreview.tools.get_invitation(client, conference.get_invitation_id('Public_Comment', number=4))
        assert public_comment_invitation

        public_comment_invitation = openreview.tools.get_invitation(client, conference.get_invitation_id('Public_Comment', number=5))
        assert public_comment_invitation is None
