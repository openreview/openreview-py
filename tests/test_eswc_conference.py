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

class TestESWCConference():

    @pytest.fixture(scope="class")
    def conference(self, client):
        now = datetime.datetime.utcnow()
        #pc_client = openreview.Client(username='pc@eccv.org', password='1234')
        builder = openreview.conference.ConferenceBuilder(client)
        assert builder, 'builder is None'

        builder.set_conference_id('eswc-conferences.org/ESWC/2021/Conference')
        builder.set_conference_short_name('ESWC 2021')
        builder.has_area_chairs(True)

        builder.set_submission_stage(double_blind = False,
            public = True,
            due_date = now + datetime.timedelta(minutes = 10),
            second_due_date = now + datetime.timedelta(minutes = 20),
            withdrawn_submission_public=True,
            withdrawn_submission_reveal_authors=True,
            email_pcs_on_withdraw=False,
            desk_rejected_submission_public=True,
            desk_rejected_submission_reveal_authors=True,
            additional_fields={
                "lead_author_is_phD_student": {
                    "required": True,
                    "description": "Is lead author a PhD student?",
                    "value-radio": [
                        "Yes",
                        "No"
                    ]
                },
                "pdf": {
                    "description": "Upload a PDF file that ends with .pdf",
                    "order": 9,
                    "value-file": {
                        "fileTypes": [
                            "pdf"
                        ],
                        "size": 50
                    },
                    "required": False
                },
                "html": {
                    "value-file": {
                        "fileTypes": [
                            "zip"
                        ],
                        "size": 50
                    },
                    "required": False,
                    "order": 10,
                    "description": "Upload a zip file."
                },
                "url": {
                    "value-regex": "http(s)?:\\/\\/.+",
                    "required": False,
                    "order": 11,
                    "description": "Submit a non-PDF URL (e.g. HTML submissions). URLs must begin with 'http' or 'https'."
                }
            })

        conference = builder.get_result()
        conference.set_program_chairs(['pc@eswc-conferences.org'])
        return conference

    def test_create_conference(self, client, conference, helpers):

        helpers.create_user('pc@eswc-conferences.org', 'Program', 'ESWCChair')
        # helpers.create_user('iclr2021_one@mail.com', 'ReviewerOne', 'ICLR', ['iclr2021_one_alternate@mail.com'])
        # ## confirm alternate email
        # client.add_members_to_group('~ReviewerOne_ICLR1', 'iclr2021_one_alternate@mail.com')
        # client.add_members_to_group('iclr2021_one_alternate@mail.com', '~ReviewerOne_ICLR1')
        # helpers.create_user('iclr2021_five@mail.com', 'ReviewerFive', 'ICLR')
        # helpers.create_user('iclr2021_six_alternate@mail.com', 'ReviewerSix', 'ICLR', ['iclr2021_six@mail.com'])
        # ## confirm alternate email
        # client.add_members_to_group('~ReviewerSix_ICLR1', 'iclr2021_six@mail.com')
        # client.add_members_to_group('iclr2021_six@mail.com', '~ReviewerSix_ICLR1')

        pc_client = openreview.Client(username='pc@eswc-conferences.org', password='1234')

        group = pc_client.get_group('eswc-conferences.org/ESWC/2021/Conference')
        assert group
        assert group.web

        pc_group = pc_client.get_group('eswc-conferences.org/ESWC/2021/Conference/Program_Chairs')
        assert pc_group
        assert pc_group.web

    def test_submit_papers(self, conference, helpers, test_client, client):

        domains = ['umass.edu', 'umass.edu', 'fb.com', 'umass.edu', 'google.com', 'mit.edu']
        for i in range(1,6):
            note = openreview.Note(invitation = 'eswc-conferences.org/ESWC/2021/Conference/-/Submission',
                readers = ['eswc-conferences.org/ESWC/2021/Conference', 'test@mail.com', 'peter@mail.com', 'andrew@' + domains[i], '~Test_User1'],
                writers = [conference.id, '~Test_User1', 'peter@mail.com', 'andrew@' + domains[i]],
                signatures = ['~Test_User1'],
                content = {
                    'title': 'Paper title ' + str(i) ,
                    'abstract': 'This is an abstract ' + str(i),
                    'authorids': ['test@mail.com', 'peter@mail.com', 'andrew@' + domains[i]],
                    'authors': ['Test User', 'Peter Test', 'Andrew Mc'],
                    'lead_author_is_phD_student': 'Yes'
                }
            )
            note = test_client.post_note(note)

        conference.setup_first_deadline_stage(force=True, submission_readers=['eswc-conferences.org/ESWC/2021/Conference/Reviewers'])

        notes = test_client.get_notes(invitation='eswc-conferences.org/ESWC/2021/Conference/-/Submission')
        assert len(notes) == 5
        assert notes[0].readers == ['eswc-conferences.org/ESWC/2021/Conference', 'test@mail.com', 'peter@mail.com', 'andrew@umass.edu', '~Test_User1', 'eswc-conferences.org/ESWC/2021/Conference/Reviewers']

        invitations = test_client.get_invitations(replyForum=notes[0].id)
        assert len(invitations) == 2
        assert invitations[0].id == 'eswc-conferences.org/ESWC/2021/Conference/Paper1/-/Withdraw'
        assert invitations[1].id == 'eswc-conferences.org/ESWC/2021/Conference/Paper1/-/Revision'

        invitations = client.get_invitations(replyForum=notes[0].id)
        assert len(invitations) == 3
        assert invitations[0].id == 'eswc-conferences.org/ESWC/2021/Conference/Paper1/-/Desk_Reject'
        assert invitations[1].id == 'eswc-conferences.org/ESWC/2021/Conference/Paper1/-/Withdraw'
        assert invitations[2].id == 'eswc-conferences.org/ESWC/2021/Conference/Paper1/-/Revision'

        ## Withdraw paper
        test_client.post_note(openreview.Note(invitation='eswc-conferences.org/ESWC/2021/Conference/Paper1/-/Withdraw',
            forum = notes[0].forum,
            replyto = notes[0].forum,
            readers = [
                'eswc-conferences.org/ESWC/2021/Conference',
                'eswc-conferences.org/ESWC/2021/Conference/Paper1/Authors',
                'eswc-conferences.org/ESWC/2021/Conference/Paper1/Reviewers',
                'eswc-conferences.org/ESWC/2021/Conference/Paper1/Area_Chairs',
                'eswc-conferences.org/ESWC/2021/Conference/Program_Chairs'],
            writers = [conference.get_id(), 'eswc-conferences.org/ESWC/2021/Conference/Paper1/Authors'],
            signatures = ['eswc-conferences.org/ESWC/2021/Conference/Paper1/Authors'],
            content = {
                'title': 'Submission Withdrawn by the Authors',
                'withdrawal confirmation': 'I have read and agree with the venue\'s withdrawal policy on behalf of myself and my co-authors.'
            }
        ))

        time.sleep(2)

        withdrawn_notes = client.get_notes(invitation='eswc-conferences.org/ESWC/2021/Conference/-/Withdrawn_Submission')
        assert len(withdrawn_notes) == 1
        withdrawn_notes[0].readers == [
            'eswc-conferences.org/ESWC/2021/Conference/Paper1/Authors',
            'eswc-conferences.org/ESWC/2021/Conference/Paper1/Reviewers',
            'eswc-conferences.org/ESWC/2021/Conference/Paper1/Area_Chairs',
            'eswc-conferences.org/ESWC/2021/Conference/Program_Chairs'
        ]
        assert len(conference.get_submissions()) == 4

        # Add a revision
        # pdf_url = test_client.put_attachment(
        #     os.path.join(os.path.dirname(__file__), 'data/paper.pdf'),
        #     'ICLR.cc/2021/Conference/Paper5/-/Revision',
        #     'pdf'
        # )

        # supplementary_material_url = test_client.put_attachment(
        #     os.path.join(os.path.dirname(__file__), 'data/paper.pdf.zip'),
        #     'ICLR.cc/2021/Conference/Paper5/-/Revision',
        #     'supplementary_material'
        # )

        # note = openreview.Note(referent=blinded_notes[0].original,
        #     forum=blinded_notes[0].original,
        #     invitation = 'ICLR.cc/2021/Conference/Paper5/-/Revision',
        #     readers = ['ICLR.cc/2021/Conference', 'ICLR.cc/2021/Conference/Paper5/Authors'],
        #     writers = ['ICLR.cc/2021/Conference', 'ICLR.cc/2021/Conference/Paper5/Authors'],
        #     signatures = ['ICLR.cc/2021/Conference/Paper5/Authors'],
        #     content = {
        #         'title': 'EDITED Paper title 5',
        #         'abstract': 'This is an abstract 5',
        #         'authorids': ['test@mail.com', 'peter@mail.com', 'melisa@mail.com'],
        #         'authors': ['Test User', 'Peter Test', 'Melisa Bok'],
        #         'code_of_ethics': 'I acknowledge that I and all co-authors of this work have read and commit to adhering to the ICLR Code of Ethics',
        #         'pdf': pdf_url,
        #         'supplementary_material': supplementary_material_url
        #     }
        # )

        # test_client.post_note(note)

        # time.sleep(2)

        # author_group = client.get_group('ICLR.cc/2021/Conference/Paper5/Authors')
        # assert len(author_group.members) == 3
        # assert 'melisa@mail.com' in author_group.members
        # assert 'test@mail.com' in author_group.members
        # assert 'peter@mail.com' in author_group.members

        # messages = client.get_messages(subject='ICLR 2021 has received a new revision of your submission titled EDITED Paper title 5')
        # assert len(messages) == 3
        # recipients = [m['content']['to'] for m in messages]
        # assert 'melisa@mail.com' in recipients
        # assert 'test@mail.com' in recipients
        # assert 'peter@mail.com' in recipients
        # assert messages[0]['content']['text'] == '''Your new revision of the submission to ICLR 2021 has been posted.\n\nTitle: EDITED Paper title 5\n\nAbstract: This is an abstract 5\n\nTo view your submission, click here: https://openreview.net/forum?id=''' + note.forum

        # ## Edit revision
        # references = client.get_references(invitation='ICLR.cc/2021/Conference/Paper5/-/Revision')
        # assert len(references) == 1
        # revision_note = references[0]
        # revision_note.content['title'] = 'EDITED Rev 2 Paper title 5'
        # test_client.post_note(revision_note)

        # time.sleep(2)

        # messages = client.get_messages(subject='ICLR 2021 has received a new revision of your submission titled EDITED Rev 2 Paper title 5')
        # assert len(messages) == 3
        # recipients = [m['content']['to'] for m in messages]
        # assert 'melisa@mail.com' in recipients
        # assert 'test@mail.com' in recipients
        # assert 'peter@mail.com' in recipients

        # assert messages[0]['content']['text'] == '''Your new revision of the submission to ICLR 2021 has been updated.\n\nTitle: EDITED Rev 2 Paper title 5\n\nAbstract: This is an abstract 5\n\nTo view your submission, click here: https://openreview.net/forum?id=''' + note.forum

        # ## Withdraw paper
        # test_client.post_note(openreview.Note(invitation='ICLR.cc/2021/Conference/Paper1/-/Withdraw',
        #     forum = blinded_notes[4].forum,
        #     replyto = blinded_notes[4].forum,
        #     readers = [
        #         'ICLR.cc/2021/Conference',
        #         'ICLR.cc/2021/Conference/Paper1/Authors',
        #         'ICLR.cc/2021/Conference/Paper1/Reviewers',
        #         'ICLR.cc/2021/Conference/Paper1/Area_Chairs',
        #         'ICLR.cc/2021/Conference/Program_Chairs'],
        #     writers = [conference.get_id(), 'ICLR.cc/2021/Conference/Paper1/Authors'],
        #     signatures = ['ICLR.cc/2021/Conference/Paper1/Authors'],
        #     content = {
        #         'title': 'Submission Withdrawn by the Authors',
        #         'withdrawal confirmation': 'I have read and agree with the venue\'s withdrawal policy on behalf of myself and my co-authors.'
        #     }
        # ))

        # time.sleep(2)

        # withdrawn_notes = client.get_notes(invitation='ICLR.cc/2021/Conference/-/Withdrawn_Submission')
        # assert len(withdrawn_notes) == 1
        # withdrawn_notes[0].readers == [
        #     'ICLR.cc/2021/Conference/Paper1/Authors',
        #     'ICLR.cc/2021/Conference/Paper1/Reviewers',
        #     'ICLR.cc/2021/Conference/Paper1/Area_Chairs',
        #     'ICLR.cc/2021/Conference/Program_Chairs'
        # ]
        # assert len(conference.get_submissions()) == 4

    # def test_post_submission_stage(self, conference, helpers, test_client, client):

    #     conference.setup_final_deadline_stage(force=True)

    #     submissions = conference.get_submissions()
    #     assert len(submissions) == 4
    #     assert submissions[0].readers == ['everyone']
    #     assert submissions[1].readers == ['everyone']
    #     assert submissions[2].readers == ['everyone']
    #     assert submissions[3].readers == ['everyone']

    #     ## Withdraw paper
    #     test_client.post_note(openreview.Note(invitation='ICLR.cc/2021/Conference/Paper2/-/Withdraw',
    #         forum = submissions[3].forum,
    #         replyto = submissions[3].forum,
    #         readers = [
    #             'everyone'],
    #         writers = [conference.get_id(), 'ICLR.cc/2021/Conference/Paper2/Authors'],
    #         signatures = ['ICLR.cc/2021/Conference/Paper2/Authors'],
    #         content = {
    #             'title': 'Submission Withdrawn by the Authors',
    #             'withdrawal confirmation': 'I have read and agree with the venue\'s withdrawal policy on behalf of myself and my co-authors.'
    #         }
    #     ))

    #     time.sleep(2)

    #     withdrawn_notes = client.get_notes(invitation='ICLR.cc/2021/Conference/-/Withdrawn_Submission')
    #     assert len(withdrawn_notes) == 2
    #     withdrawn_notes[0].readers == [
    #         'everyone'
    #     ]
    #     withdrawn_notes[1].readers == [
    #         'ICLR.cc/2021/Conference/Paper1/Authors',
    #         'ICLR.cc/2021/Conference/Paper1/Reviewers',
    #         'ICLR.cc/2021/Conference/Paper1/Area_Chairs',
    #         'ICLR.cc/2021/Conference/Program_Chairs'
    #     ]


    # def test_revision_stage(self, conference, helpers, test_client, client):

    #     now = datetime.datetime.utcnow()
    #     conference.set_submission_revision_stage(openreview.SubmissionRevisionStage(due_date=now + datetime.timedelta(minutes = 40), allow_author_reorder=True))

    #     submissions = conference.get_submissions()

    #     print(submissions[0])

    #     test_client.post_note(openreview.Note(
    #         invitation='ICLR.cc/2021/Conference/Paper5/-/Revision',
    #         referent=submissions[0].original,
    #         forum=submissions[0].original,
    #         readers=['ICLR.cc/2021/Conference', 'ICLR.cc/2021/Conference/Paper5/Authors'],
    #         writers=['ICLR.cc/2021/Conference', 'ICLR.cc/2021/Conference/Paper5/Authors'],
    #         signatures=['ICLR.cc/2021/Conference/Paper5/Authors'],
    #         content={
    #             'title': 'EDITED V3 Paper title 5',
    #             'abstract': 'This is an abstract 5',
    #             'authorids': ['peter@mail.com', 'test@mail.com', 'melisa@mail.com'],
    #             'authors': ['Peter Test', 'Test User', 'Melisa Bok'],
    #             'code_of_ethics': 'I acknowledge that I and all co-authors of this work have read and commit to adhering to the ICLR Code of Ethics',
    #             'pdf': submissions[0].content['pdf'],
    #             'supplementary_material': submissions[0].content['supplementary_material']
    #         }

    #     ))