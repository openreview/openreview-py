from __future__ import absolute_import, division, print_function, unicode_literals
import openreview
import os

class TestBibtex():


    def test_regular_names(self, client, test_client):

        builder = openreview.conference.ConferenceBuilder(client)
        assert builder, 'builder is None'

        builder.set_conference_id('NIPS.cc/2019/Workshop/MLITS')
        builder.set_submission_stage(public=True)
        conference = builder.get_result()

        note = openreview.Note(invitation = conference.get_submission_id(),
            readers = ['everyone'],
            writers = [conference.id, '~Test_User1', 'peter@mail.com', 'andrew@mail.com'],
            signatures = ['~Test_User1'],
            content = {
                'title': 'Paper title has an Ô',
                'abstract': 'This is an abstract with #s galore',
                'authorids': ['test@mail.com', 'peter@mail.com', 'andrew@mail.com'],
                'authors': ['Test User', 'Peter Teët', 'Andrew McC']
            }
        )
        url = test_client.put_pdf(os.path.join(os.path.dirname(__file__), 'data/paper.pdf'))
        note.content['pdf'] = url
        posted_note = test_client.post_note(note)

        bibtex = openreview.tools.get_bibtex(posted_note, conference.id, '2019', accepted=True, anonymous=False, baseurl=client.baseurl )
        print(bibtex)
        valid_bibtex = '''@inproceedings{
user2019paper,
title={Paper title has an {\^O}},
author={Test User and Peter Te{\\"e}t and Andrew McC},
booktitle={NIPS.cc/2019/Workshop/MLITS},
year={2019},
url={'''
        valid_bibtex = valid_bibtex+client.baseurl+'/forum?id='+posted_note.forum+'''},
}'''
        print("Test bibtex: "+valid_bibtex)
        assert bibtex == valid_bibtex



