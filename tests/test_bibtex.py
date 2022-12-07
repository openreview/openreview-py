# coding: utf-8
from __future__ import absolute_import, division, print_function, unicode_literals
import openreview
import os

class TestBibtex():


    def test_regular_names(self, client, helpers):

        builder = openreview.conference.ConferenceBuilder(client, support_user='openreview.net/Support')
        assert builder, 'builder is None'

        builder.set_conference_id('NIPS.cc/2020/Workshop/MLITS')
        builder.set_submission_stage(public=True)
        conference = builder.get_result()

        note = openreview.Note(invitation = conference.get_submission_id(),
            readers = ['NIPS.cc/2020/Workshop/MLITS','bibtex@mail.com', 'peter@mail.com', 'andrew@mail.com','~Bibtex_User1'],
            writers = [conference.id, '~Bibtex_User1', 'peter@mail.com', 'andrew@mail.com'],
            signatures = ['~Bibtex_User1'],
            content = {
                'title': 'Paper title has GANs and an Ô',
                'abstract': 'This is an abstract with #s galore',
                'authorids': ['bibtex@mail.com', 'peter@mail.com', 'andrew@mail.com'],
                'authors': ['Bibtex User', 'Peter Teët', 'Andrew McC']
            }
        )
        test_client = helpers.create_user('bibtex@mail.com', 'Bibtex', 'User')
        url = test_client.put_attachment(os.path.join(os.path.dirname(__file__), 'data/paper.pdf'), conference.get_submission_id(), 'pdf')
        note.content['pdf'] = url
        posted_note = test_client.post_note(note)

        bibtex = openreview.tools.generate_bibtex(posted_note, conference.id, '2020', paper_status='accepted', anonymous=False, baseurl=client.baseurl )
        valid_bibtex = '''@inproceedings{
user2020paper,
title={Paper title has {GAN}s and an \^O},
author={Bibtex User and Peter Te{\\"e}t and Andrew McC},
booktitle={NIPS.cc/2020/Workshop/MLITS},
year={2020},
url={'''
        valid_bibtex = valid_bibtex+client.baseurl+'/forum?id='+posted_note.forum+'''}
}'''

        assert bibtex == valid_bibtex

        # test accepted False and names reversed
        bibtex = openreview.tools.generate_bibtex(posted_note, conference.id, '2020', paper_status='rejected', anonymous=False, names_reversed=True)

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
        bibtex = openreview.tools.generate_bibtex(posted_note, conference.id, '2020', paper_status='accepted', anonymous=False, baseurl=client.baseurl, editor='A. Beygelzimer and Y. Dauphin and P. Liang and J. Wortman Vaughan' )
        valid_bibtex = '''@inproceedings{
user2020paper,
title={Paper title has {GAN}s and an \^O},
author={Bibtex User and Peter Te{\\"e}t and Andrew McC},
booktitle={NIPS.cc/2020/Workshop/MLITS},
editor={A. Beygelzimer and Y. Dauphin and P. Liang and J. Wortman Vaughan},
year={2020},
url={'''
        valid_bibtex = valid_bibtex+client.baseurl+'/forum?id='+posted_note.forum+'''}
}'''

        assert bibtex == valid_bibtex



