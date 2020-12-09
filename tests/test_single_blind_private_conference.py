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
            public = False,
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

        # ## Withdraw paper
        # test_client.post_note(openreview.Note(invitation='eswc-conferences.org/ESWC/2021/Conference/Paper1/-/Withdraw',
        #     forum = notes[0].forum,
        #     replyto = notes[0].forum,
        #     readers = [
        #         'eswc-conferences.org/ESWC/2021/Conference',
        #         'eswc-conferences.org/ESWC/2021/Conference/Paper1/Authors',
        #         'eswc-conferences.org/ESWC/2021/Conference/Paper1/Reviewers',
        #         'eswc-conferences.org/ESWC/2021/Conference/Paper1/Area_Chairs',
        #         'eswc-conferences.org/ESWC/2021/Conference/Program_Chairs'],
        #     writers = [conference.get_id(), 'eswc-conferences.org/ESWC/2021/Conference/Paper1/Authors'],
        #     signatures = ['eswc-conferences.org/ESWC/2021/Conference/Paper1/Authors'],
        #     content = {
        #         'title': 'Submission Withdrawn by the Authors',
        #         'withdrawal confirmation': 'I have read and agree with the venue\'s withdrawal policy on behalf of myself and my co-authors.'
        #     }
        # ))

        # time.sleep(2)

        # withdrawn_notes = client.get_notes(invitation='eswc-conferences.org/ESWC/2021/Conference/-/Withdrawn_Submission')
        # assert len(withdrawn_notes) == 1
        # withdrawn_notes[0].readers == [
        #     'eswc-conferences.org/ESWC/2021/Conference/Paper1/Authors',
        #     'eswc-conferences.org/ESWC/2021/Conference/Paper1/Reviewers',
        #     'eswc-conferences.org/ESWC/2021/Conference/Paper1/Area_Chairs',
        #     'eswc-conferences.org/ESWC/2021/Conference/Program_Chairs'
        # ]
        # assert len(conference.get_submissions()) == 4

        # # Add a revision
        # pdf_url = test_client.put_attachment(
        #     os.path.join(os.path.dirname(__file__), 'data/paper.pdf'),
        #     'eswc-conferences.org/ESWC/2021/Conference/Paper2/-/Revision',
        #     'pdf'
        # )

        # note = openreview.Note(referent=notes[1].id,
        #     forum=notes[1].id,
        #     invitation = 'eswc-conferences.org/ESWC/2021/Conference/Paper2/-/Revision',
        #     readers = ['eswc-conferences.org/ESWC/2021/Conference', 'eswc-conferences.org/ESWC/2021/Conference/Paper2/Authors'],
        #     writers = ['eswc-conferences.org/ESWC/2021/Conference', 'eswc-conferences.org/ESWC/2021/Conference/Paper2/Authors'],
        #     signatures = ['eswc-conferences.org/ESWC/2021/Conference/Paper2/Authors'],
        #     content = {
        #         'title': 'EDITED Paper title 5',
        #         'abstract': 'This is an abstract 5',
        #         'authorids': ['test@mail.com', 'peter@mail.com', 'melisa@mail.com'],
        #         'authors': ['Test User', 'Peter Test', 'Melisa Bok'],
        #         'lead_author_is_phD_student': 'Yes',
        #         'pdf': pdf_url
        #     }
        # )

        # test_client.post_note(note)

        # time.sleep(2)

        # author_group = client.get_group('eswc-conferences.org/ESWC/2021/Conference/Paper2/Authors')
        # assert len(author_group.members) == 3
        # assert 'melisa@mail.com' in author_group.members
        # assert 'test@mail.com' in author_group.members
        # assert 'peter@mail.com' in author_group.members

        # messages = client.get_messages(subject='ESWC 2021 has received a new revision of your submission titled EDITED Paper title 5')
        # assert len(messages) == 3
        # recipients = [m['content']['to'] for m in messages]
        # assert 'melisa@mail.com' in recipients
        # assert 'test@mail.com' in recipients
        # assert 'peter@mail.com' in recipients
        # assert messages[0]['content']['text'] == '''Your new revision of the submission to ESWC 2021 has been posted.\n\nTitle: EDITED Paper title 5\n\nAbstract: This is an abstract 5\n\nTo view your submission, click here: https://openreview.net/forum?id=''' + note.forum

        # ## Edit revision
        # references = client.get_references(invitation='eswc-conferences.org/ESWC/2021/Conference/Paper2/-/Revision')
        # assert len(references) == 1
        # revision_note = references[0]
        # revision_note.content['title'] = 'EDITED Rev 2 Paper title 5'
        # test_client.post_note(revision_note)

        # time.sleep(2)

        # messages = client.get_messages(subject='ESWC 2021 has received a new revision of your submission titled EDITED Rev 2 Paper title 5')
        # assert len(messages) == 3
        # recipients = [m['content']['to'] for m in messages]
        # assert 'melisa@mail.com' in recipients
        # assert 'test@mail.com' in recipients
        # assert 'peter@mail.com' in recipients
        # assert messages[0]['content']['text'] == '''Your new revision of the submission to ESWC 2021 has been updated.\n\nTitle: EDITED Rev 2 Paper title 5\n\nAbstract: This is an abstract 5\n\nTo view your submission, click here: https://openreview.net/forum?id=''' + note.forum

        # ## Desk Reject paper
        # pc_client = openreview.Client(username='pc@eswc-conferences.org', password='1234')
        # pc_client.post_note(openreview.Note(invitation='eswc-conferences.org/ESWC/2021/Conference/Paper3/-/Desk_Reject',
        #     forum = notes[2].id,
        #     replyto = notes[2].id,
        #     readers = [
        #         'eswc-conferences.org/ESWC/2021/Conference',
        #         'eswc-conferences.org/ESWC/2021/Conference/Paper3/Authors',
        #         'eswc-conferences.org/ESWC/2021/Conference/Paper3/Reviewers',
        #         'eswc-conferences.org/ESWC/2021/Conference/Paper3/Area_Chairs',
        #         'eswc-conferences.org/ESWC/2021/Conference/Program_Chairs'],
        #     writers = [conference.get_id(), 'eswc-conferences.org/ESWC/2021/Conference/Program_Chairs'],
        #     signatures = ['eswc-conferences.org/ESWC/2021/Conference/Program_Chairs'],
        #     content = {
        #         'title': 'Submission Desk Rejected by Program Chairs',
        #         'desk_reject_comments': 'missing pdf'
        #     }
        # ))

        # time.sleep(2)

        # desk_rejected_notes = client.get_notes(invitation='eswc-conferences.org/ESWC/2021/Conference/-/Desk_Rejected_Submission')
        # assert len(desk_rejected_notes) == 1
        # desk_rejected_notes[0].readers == [
        #     'eswc-conferences.org/ESWC/2021/Conference/Paper3/Authors',
        #     'eswc-conferences.org/ESWC/2021/Conference/Paper3/Reviewers',
        #     'eswc-conferences.org/ESWC/2021/Conference/Paper3/Area_Chairs',
        #     'eswc-conferences.org/ESWC/2021/Conference/Program_Chairs'
        # ]
        # assert len(conference.get_submissions()) == 3

    # def test_post_submission_stage(self, conference, helpers, test_client, client):

    #     conference.setup_final_deadline_stage(force=True)

    #     submissions = conference.get_submissions()
    #     assert len(submissions) == 3
    #     assert submissions[0].readers == ['everyone']
    #     assert submissions[1].readers == ['everyone']
    #     assert submissions[2].readers == ['everyone']

    #     ## Withdraw paper
    #     test_client.post_note(openreview.Note(invitation='eswc-conferences.org/ESWC/2021/Conference/Paper5/-/Withdraw',
    #         forum = submissions[0].forum,
    #         replyto = submissions[0].forum,
    #         readers = [
    #             'everyone'],
    #         writers = [conference.get_id(), 'eswc-conferences.org/ESWC/2021/Conference/Paper5/Authors'],
    #         signatures = ['eswc-conferences.org/ESWC/2021/Conference/Paper5/Authors'],
    #         content = {
    #             'title': 'Submission Withdrawn by the Authors',
    #             'withdrawal confirmation': 'I have read and agree with the venue\'s withdrawal policy on behalf of myself and my co-authors.'
    #         }
    #     ))

    #     time.sleep(2)

    #     withdrawn_notes = client.get_notes(invitation='eswc-conferences.org/ESWC/2021/Conference/-/Withdrawn_Submission')
    #     assert len(withdrawn_notes) == 2
    #     withdrawn_notes[0].readers == [
    #         'everyone'
    #     ]
    #     withdrawn_notes[1].readers == [
    #         'eswc-conferences.org/ESWC/2021/Conference/Paper1/Authors',
    #         'eswc-conferences.org/ESWC/2021/Conference/Paper1/Reviewers',
    #         'eswc-conferences.org/ESWC/2021/Conference/Paper1/Area_Chairs',
    #         'eswc-conferences.org/ESWC/2021/Conference/Program_Chairs'
    #     ]