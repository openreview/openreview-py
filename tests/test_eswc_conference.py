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
        builder = openreview.conference.ConferenceBuilder(client, support_user='openreview.net/Support')
        assert builder, 'builder is None'

        builder.set_conference_id('eswc-conferences.org/ESWC/2021/Conference')
        builder.set_conference_short_name('ESWC 2021')
        builder.has_area_chairs(True)

        builder.set_submission_stage(
            name = 'Special_Submission',
            double_blind = False,
            due_date = now + datetime.timedelta(minutes = 10),
            second_due_date = now + datetime.timedelta(minutes = 20),
            withdrawn_submission_public=True,
            withdrawn_submission_reveal_authors=True,
            email_pcs_on_withdraw=False,
            desk_rejected_submission_public=True,
            desk_rejected_submission_reveal_authors=True,
            readers = [openreview.SubmissionStage.Readers.REVIEWERS],
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
        year = datetime.datetime.now().year
        domains = ['umass.edu', 'umass.edu', 'fb.com', 'umass.edu', 'google.com', 'mit.edu']
        for i in range(1,6):
            note = openreview.Note(invitation = 'eswc-conferences.org/ESWC/2021/Conference/-/Special_Submission',
                readers = ['eswc-conferences.org/ESWC/2021/Conference', 'test@mail.com', 'peter@mail.com', 'andrew@' + domains[i], '~SomeFirstName_User1'],
                writers = [conference.id, '~SomeFirstName_User1', 'peter@mail.com', 'andrew@' + domains[i]],
                signatures = ['~SomeFirstName_User1'],
                content = {
                    'title': 'Paper title ' + str(i) ,
                    'abstract': 'This is an abstract ' + str(i),
                    'authorids': ['test@mail.com', 'peter@mail.com', 'andrew@' + domains[i]],
                    'authors': ['SomeFirstName User', 'Peter SomeLastName', 'Andrew Mc'],
                    'lead_author_is_phD_student': 'Yes'
                }
            )
            note = test_client.post_note(note)

        conference.setup_first_deadline_stage(force=True)

        revision_invitation = test_client.get_invitation(id='eswc-conferences.org/ESWC/2021/Conference/-/Revision')
        assert revision_invitation.multiReply

        notes = test_client.get_notes(invitation='eswc-conferences.org/ESWC/2021/Conference/-/Special_Submission', sort='number:asc')
        assert len(notes) == 5
        assert notes[0].readers == ['eswc-conferences.org/ESWC/2021/Conference', 'eswc-conferences.org/ESWC/2021/Conference/Reviewers', 'eswc-conferences.org/ESWC/2021/Conference/Paper1/Authors']

        invitations = test_client.get_invitations(replyForum=notes[0].id)
        assert len(invitations) == 2
        ids = [invitation.id for invitation in invitations]
        assert 'eswc-conferences.org/ESWC/2021/Conference/Paper1/-/Withdraw' in ids
        assert 'eswc-conferences.org/ESWC/2021/Conference/Paper1/-/Revision' in ids

        invitations = client.get_invitations(replyForum=notes[0].id)
        assert len(invitations) == 3
        ids = [invitation.id for invitation in invitations]
        assert 'eswc-conferences.org/ESWC/2021/Conference/Paper1/-/Desk_Reject' in ids
        assert 'eswc-conferences.org/ESWC/2021/Conference/Paper1/-/Withdraw' in ids
        assert 'eswc-conferences.org/ESWC/2021/Conference/Paper1/-/Revision' in ids

        ## Withdraw paper
        withdrawn_note = test_client.post_note(openreview.Note(invitation='eswc-conferences.org/ESWC/2021/Conference/Paper1/-/Withdraw',
            forum = notes[0].forum,
            replyto = notes[0].forum,
            readers = [
                'eswc-conferences.org/ESWC/2021/Conference',
                'eswc-conferences.org/ESWC/2021/Conference/Paper1/Authors',
                'eswc-conferences.org/ESWC/2021/Conference/Paper1/Reviewers',
                'eswc-conferences.org/ESWC/2021/Conference/Paper1/Area_Chairs',
                'eswc-conferences.org/ESWC/2021/Conference/Program_Chairs'],
            writers = [conference.get_id(), conference.get_program_chairs_id()],
            signatures = ['eswc-conferences.org/ESWC/2021/Conference/Paper1/Authors'],
            content = {
                'title': 'Submission Withdrawn by the Authors',
                'withdrawal confirmation': 'I have read and agree with the venue\'s withdrawal policy on behalf of myself and my co-authors.'
            }
        ))

        helpers.await_queue()

        withdrawn_notes = client.get_notes(invitation='eswc-conferences.org/ESWC/2021/Conference/-/Withdrawn_Special_Submission')
        assert len(withdrawn_notes) == 1
        assert withdrawn_notes[0].readers == [
            'eswc-conferences.org/ESWC/2021/Conference/Paper1/Authors',
            'eswc-conferences.org/ESWC/2021/Conference/Paper1/Reviewers',
            'eswc-conferences.org/ESWC/2021/Conference/Paper1/Area_Chairs',
            'eswc-conferences.org/ESWC/2021/Conference/Program_Chairs'
        ]
        assert withdrawn_notes[0].content['_bibtex'] == '''@misc{
user'''+str(year)+'''paper,
title={Paper title 1},
author={SomeFirstName User and Peter SomeLastName and Andrew Mc},
year={'''+str(year)+'''},
url={https://openreview.net/forum?id=''' + withdrawn_notes[0].id + '''}
}'''
        assert len(conference.get_submissions()) == 4

        # Undo Withdraw
        ## Undo desk rejection
        withdrawn_note.ddate = openreview.tools.datetime_millis(datetime.datetime.now())
        client.post_note(withdrawn_note)

        helpers.await_queue()

        submission_note = client.get_note(withdrawn_notes[0].forum)
        assert submission_note.invitation == 'eswc-conferences.org/ESWC/2021/Conference/-/Special_Submission'
        assert submission_note.readers == ['eswc-conferences.org/ESWC/2021/Conference', 
                                           'eswc-conferences.org/ESWC/2021/Conference/Reviewers',
                                           'eswc-conferences.org/ESWC/2021/Conference/Paper1/Authors']

        messages = client.get_messages(subject='^ESWC 2021: Paper .* restored by paper authors$')
        assert len(messages) == 3
        assert len(conference.get_submissions()) == 5

        # Withdraw the paper again
        withdrawn_note = test_client.post_note(
            openreview.Note(invitation='eswc-conferences.org/ESWC/2021/Conference/Paper1/-/Withdraw',
                            forum=notes[0].forum,
                            replyto=notes[0].forum,
                            readers=[
                                'eswc-conferences.org/ESWC/2021/Conference',
                                'eswc-conferences.org/ESWC/2021/Conference/Paper1/Authors',
                                'eswc-conferences.org/ESWC/2021/Conference/Paper1/Reviewers',
                                'eswc-conferences.org/ESWC/2021/Conference/Paper1/Area_Chairs',
                                'eswc-conferences.org/ESWC/2021/Conference/Program_Chairs'],
                            writers=[conference.get_id(), conference.get_program_chairs_id()],
                            signatures=['eswc-conferences.org/ESWC/2021/Conference/Paper1/Authors'],
                            content={
                                'title': 'Submission Withdrawn by the Authors',
                                'withdrawal confirmation': 'I have read and agree with the venue\'s withdrawal policy on behalf of myself and my co-authors.'
                            }
                            ))
        helpers.await_queue()

        # Add a revision
        pdf_url = test_client.put_attachment(
            os.path.join(os.path.dirname(__file__), 'data/paper.pdf'),
            'eswc-conferences.org/ESWC/2021/Conference/Paper2/-/Revision',
            'pdf'
        )

        note = openreview.Note(referent=notes[1].id,
            forum=notes[1].id,
            invitation = 'eswc-conferences.org/ESWC/2021/Conference/Paper2/-/Revision',
            readers = ['eswc-conferences.org/ESWC/2021/Conference', 'eswc-conferences.org/ESWC/2021/Conference/Paper2/Authors'],
            writers = ['eswc-conferences.org/ESWC/2021/Conference', 'eswc-conferences.org/ESWC/2021/Conference/Paper2/Authors'],
            signatures = ['eswc-conferences.org/ESWC/2021/Conference/Paper2/Authors'],
            content = {
                'title': 'EDITED Paper title 5',
                'abstract': 'This is an abstract 5',
                'authorids': ['test@mail.com', 'peter@mail.com', 'melisa@mail.com'],
                'authors': ['SomeFirstName User', 'Peter SomeLastName', 'Melisa Bok'],
                'lead_author_is_phD_student': 'Yes',
                'pdf': pdf_url
            }
        )

        test_client.post_note(note)

        helpers.await_queue()

        author_group = client.get_group('eswc-conferences.org/ESWC/2021/Conference/Paper2/Authors')
        assert len(author_group.members) == 3
        assert 'melisa@mail.com' in author_group.members
        assert 'test@mail.com' in author_group.members
        assert 'peter@mail.com' in author_group.members

        messages = client.get_messages(subject='ESWC 2021 has received a new revision of your submission titled EDITED Paper title 5')
        assert len(messages) == 3
        recipients = [m['content']['to'] for m in messages]
        assert 'melisa@mail.com' in recipients
        assert 'test@mail.com' in recipients
        assert 'peter@mail.com' in recipients
        text = messages[0]['content']['text']
        assert 'Your new revision of the submission to ESWC 2021 has been posted.' in text
        assert 'Title: EDITED Paper title 5' in text
        assert 'Abstract: This is an abstract 5' in text
        assert 'To view your submission, click here:' in text

        ## Edit revision
        references = client.get_references(invitation='eswc-conferences.org/ESWC/2021/Conference/Paper2/-/Revision')
        assert len(references) == 1
        revision_note = references[0]
        revision_note.content['title'] = 'EDITED Rev 2 Paper title 5'
        test_client.post_note(revision_note)

        helpers.await_queue()

        messages = client.get_messages(subject='ESWC 2021 has received a new revision of your submission titled EDITED Rev 2 Paper title 5')
        assert len(messages) == 3
        recipients = [m['content']['to'] for m in messages]
        assert 'melisa@mail.com' in recipients
        assert 'test@mail.com' in recipients
        assert 'peter@mail.com' in recipients
        text = messages[0]['content']['text']
        assert 'Your new revision of the submission to ESWC 2021 has been updated.' in text
        assert 'Title: EDITED Rev 2 Paper title 5' in text
        assert 'Abstract: This is an abstract 5' in text
        assert 'To view your submission, click here:' in text

        ## Desk Reject paper
        pc_client = openreview.Client(username='pc@eswc-conferences.org', password='1234')
        desk_reject_note = pc_client.post_note(openreview.Note(invitation='eswc-conferences.org/ESWC/2021/Conference/Paper3/-/Desk_Reject',
            forum = notes[2].id,
            replyto = notes[2].id,
            readers = [
                'eswc-conferences.org/ESWC/2021/Conference',
                'eswc-conferences.org/ESWC/2021/Conference/Paper3/Authors',
                'eswc-conferences.org/ESWC/2021/Conference/Paper3/Reviewers',
                'eswc-conferences.org/ESWC/2021/Conference/Paper3/Area_Chairs',
                'eswc-conferences.org/ESWC/2021/Conference/Program_Chairs'],
            writers = [conference.get_id(), 'eswc-conferences.org/ESWC/2021/Conference/Program_Chairs'],
            signatures = ['eswc-conferences.org/ESWC/2021/Conference/Program_Chairs'],
            content = {
                'title': 'Submission Desk Rejected by Program Chairs',
                'desk_reject_comments': 'missing pdf'
            }
        ))

        helpers.await_queue()

        desk_rejected_notes = client.get_notes(invitation='eswc-conferences.org/ESWC/2021/Conference/-/Desk_Rejected_Special_Submission')
        assert len(desk_rejected_notes) == 1
        desk_rejected_notes[0].readers == [
            'eswc-conferences.org/ESWC/2021/Conference/Paper3/Authors',
            'eswc-conferences.org/ESWC/2021/Conference/Paper3/Reviewers',
            'eswc-conferences.org/ESWC/2021/Conference/Paper3/Area_Chairs',
            'eswc-conferences.org/ESWC/2021/Conference/Program_Chairs'
        ]
        assert len(conference.get_submissions()) == 3

        ## Undo desk rejection
        desk_reject_note.ddate = openreview.tools.datetime_millis(datetime.datetime.now())
        pc_client.post_note(desk_reject_note)

        helpers.await_queue()

        submission_note = client.get_note(desk_rejected_notes[0].forum)
        assert submission_note.invitation == 'eswc-conferences.org/ESWC/2021/Conference/-/Special_Submission'
        assert submission_note.readers == ['eswc-conferences.org/ESWC/2021/Conference', 'eswc-conferences.org/ESWC/2021/Conference/Reviewers', 'eswc-conferences.org/ESWC/2021/Conference/Paper3/Authors']

        messages = client.get_messages(subject = '^ESWC 2021: Paper .* unmarked desk rejected by program chairs$')
        assert len(messages) == 4


    def test_post_submission_stage(self, conference, helpers, test_client, client):
        year = datetime.datetime.now().year
        conference.submission_stage.public = True
        conference.submission_stage.readers = [openreview.SubmissionStage.Readers.EVERYONE]
        conference.setup_final_deadline_stage(force=True)

        submissions = conference.get_submissions(sort='number:desc')
        assert len(submissions) == 4
        assert submissions[0].readers == ['everyone']
        assert submissions[1].readers == ['everyone']
        assert submissions[2].readers == ['everyone']
        assert submissions[3].readers == ['everyone']

        ## Withdraw paper
        test_client.post_note(openreview.Note(invitation='eswc-conferences.org/ESWC/2021/Conference/Paper5/-/Withdraw',
            forum = submissions[0].forum,
            replyto = submissions[0].forum,
            readers = [
                'everyone'],
            writers = [conference.get_id(), conference.get_program_chairs_id()],
            signatures = ['eswc-conferences.org/ESWC/2021/Conference/Paper5/Authors'],
            content = {
                'title': 'Submission Withdrawn by the Authors',
                'withdrawal confirmation': 'I have read and agree with the venue\'s withdrawal policy on behalf of myself and my co-authors.'
            }
        ))

        helpers.await_queue()

        withdrawn_notes = client.get_notes(invitation='eswc-conferences.org/ESWC/2021/Conference/-/Withdrawn_Special_Submission', sort='tmdate')
        assert len(withdrawn_notes) == 2
        withdrawn_notes[0].readers == [
            'everyone'
        ]
        withdrawn_notes[1].readers == [
            'eswc-conferences.org/ESWC/2021/Conference/Paper1/Authors',
            'eswc-conferences.org/ESWC/2021/Conference/Paper1/Reviewers',
            'eswc-conferences.org/ESWC/2021/Conference/Paper1/Area_Chairs',
            'eswc-conferences.org/ESWC/2021/Conference/Program_Chairs'
        ]
        assert withdrawn_notes[0].content['_bibtex'] == '''@misc{
user'''+str(year)+'''paper,
title={Paper title 5},
author={SomeFirstName User and Peter SomeLastName and Andrew Mc},
year={'''+str(year)+'''},
url={https://openreview.net/forum?id=''' + withdrawn_notes[0].id + '''}
}'''
