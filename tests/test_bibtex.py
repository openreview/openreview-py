# coding: utf-8
from __future__ import absolute_import, division, print_function, unicode_literals
import openreview
import os
import datetime
from openreview.api import OpenReviewClient
from openreview.api import Note
from openreview.venue import Venue
from openreview.stages import SubmissionStage

class TestBibtex():


    def test_regular_names(self, openreview_client, helpers):

        conference_id = 'NIPS.cc/2020/Workshop/MLITS'
        venue = Venue(openreview_client, conference_id, 'openreview.net/Support')
        venue.name = 'NIPS.cc/2020/Workshop/MLITS'
        venue.short_name = 'MLITS 2020'
        venue.website = 'mlits.org'
        venue.contact = 'mlits@contact.com'
        venue.invitation_builder.update_wait_time = 2000
        venue.invitation_builder.update_date_string = "#{4/mdate} + 2000"

        now = datetime.datetime.now()
        venue.submission_stage = SubmissionStage(
            double_blind=False,
            due_date=now + datetime.timedelta(minutes=30),
            readers=[SubmissionStage.Readers.EVERYONE],
        )

        venue.setup(program_chair_ids=[])
        venue.create_submission_stage()

        helpers.create_user('bibtex@mail.com', 'Bibtex', 'User')
        test_client = OpenReviewClient(username='bibtex@mail.com', password=helpers.strong_password)

        url = test_client.put_attachment(os.path.join(os.path.dirname(__file__), 'data/paper.pdf'), venue.get_submission_id(), 'pdf')

        note_edit = test_client.post_note_edit(
            invitation=venue.get_submission_id(),
            signatures=['~Bibtex_User1'],
            note=Note(
                content={
                    'title': { 'value': 'Paper title has GANs and an Ô' },
                    'abstract': { 'value': 'This is an abstract with #s galore' },
                    'authorids': { 'value': ['bibtex@mail.com', 'peter@mail.com', 'andrew@mail.com'] },
                    'authors': { 'value': ['Bibtex User', 'Peter Teët', 'Andrew McC'] },
                    'keywords': { 'value': ['keyword1', 'keyword2'] },
                    'pdf': { 'value': url },
                }
            )
        )

        helpers.await_queue_edit(openreview_client, edit_id=note_edit['id'])
        posted_note = openreview_client.get_note(note_edit['note']['id'])

        bibtex = openreview.tools.generate_bibtex(posted_note, conference_id, '2020', paper_status='accepted', anonymous=False, baseurl=openreview_client.baseurl)
        valid_bibtex = '''@inproceedings{
user2020paper,
title={Paper title has {GAN}s and an \^O},
author={Bibtex User and Peter Te{\\"e}t and Andrew McC},
booktitle={NIPS.cc/2020/Workshop/MLITS},
year={2020},
url={'''
        valid_bibtex = valid_bibtex+openreview_client.baseurl+'/forum?id='+posted_note.forum+'''}
}'''

        assert bibtex == valid_bibtex

        # test accepted False and names reversed
        bibtex = openreview.tools.generate_bibtex(posted_note, conference_id, '2020', paper_status='rejected', anonymous=False, names_reversed=True)

        valid_bibtex = '''@misc{
user2020paper,
title={Paper title has {GAN}s and an \^O},
author={User, Bibtex and Te{\\"e}t, Peter and McC, Andrew},
year={2020},
url={https://openreview.net/forum?id='''

        valid_bibtex = valid_bibtex + posted_note.forum + '''}
}'''

        assert bibtex == valid_bibtex

        # test accepted paper with editors
        bibtex = openreview.tools.generate_bibtex(posted_note, conference_id, '2020', paper_status='accepted', anonymous=False, baseurl=openreview_client.baseurl, editor='A. Beygelzimer and Y. Dauphin and P. Liang and J. Wortman Vaughan' )
        valid_bibtex = '''@inproceedings{
user2020paper,
title={Paper title has {GAN}s and an \^O},
author={Bibtex User and Peter Te{\\"e}t and Andrew McC},
booktitle={NIPS.cc/2020/Workshop/MLITS},
editor={A. Beygelzimer and Y. Dauphin and P. Liang and J. Wortman Vaughan},
year={2020},
url={'''
        valid_bibtex = valid_bibtex+openreview_client.baseurl+'/forum?id='+posted_note.forum+'''}
}'''

        assert bibtex == valid_bibtex

    def test_special_characters(self, openreview_client, helpers):

        conference_id = 'NIPS.cc/2020/Workshop/MLITS'
        venue = Venue(openreview_client, conference_id, 'openreview.net/Support')
        venue.name = 'NIPS.cc/2020/Workshop/MLITS'
        venue.short_name = 'MLITS 2020'
        venue.website = 'mlits.org'
        venue.contact = 'mlits@contact.com'
        venue.invitation_builder.update_wait_time = 2000
        venue.invitation_builder.update_date_string = "#{4/mdate} + 2000"

        now = datetime.datetime.now()
        venue.submission_stage = SubmissionStage(
            double_blind=False,
            due_date=now + datetime.timedelta(minutes=30),
            readers=[SubmissionStage.Readers.EVERYONE],
        )

        venue.setup(program_chair_ids=[])
        venue.create_submission_stage()

        helpers.create_user('bibtex@mail.com', 'Bibtex', 'User')
        test_client = OpenReviewClient(username='bibtex@mail.com', password=helpers.strong_password)

        url = test_client.put_attachment(os.path.join(os.path.dirname(__file__), 'data/paper.pdf'), venue.get_submission_id(), 'pdf')

        note_edit = test_client.post_note_edit(
            invitation=venue.get_submission_id(),
            signatures=['~Bibtex_User1'],
            note=Note(
                content={
                    'title': { 'value': 'Paper title has GANs and an Ô' },
                    'abstract': { 'value': 'This is an abstract with #s galore' },
                    'authorids': { 'value': ['bibtex@mail.com', 'peter@mail.com', 'andrew@mail.com'] },
                    'authors': { 'value': ['Bîbtex üsêr', 'Peter Teët', 'Andrew McC'] },
                    'keywords': { 'value': ['keyword1', 'keyword2'] },
                    'pdf': { 'value': url },
                }
            )
        )

        helpers.await_queue_edit(openreview_client, edit_id=note_edit['id'])
        posted_note = openreview_client.get_note(note_edit['note']['id'])

        bibtex = openreview.tools.generate_bibtex(posted_note, conference_id, '2020', paper_status='accepted', anonymous=False, baseurl=openreview_client.baseurl)
        valid_bibtex = '''@inproceedings{
user2020paper,
title={Paper title has {GAN}s and an \^O},
author={B{\\^\\i}btex {\\"u}s{\\^e}r and Peter Te{\\"e}t and Andrew McC},
booktitle={NIPS.cc/2020/Workshop/MLITS},
year={2020},
url={'''
        valid_bibtex = valid_bibtex+openreview_client.baseurl+'/forum?id='+posted_note.forum+'''}
}'''

        assert bibtex == valid_bibtex


