from __future__ import absolute_import, division, print_function, unicode_literals

import openreview
import datetime
import time
import re
from selenium.webdriver.common.by import By
from openreview.api import OpenReviewClient
from openreview.api import Note
import openreview.api
from openreview.journal import Journal
from openreview.venue import Venue
import pytest

class TestProfileManagement():

    def test_create_profile(self, client, openreview_client, helpers):

        amelia_client = helpers.create_user('amelia@profile.org', 'Amelia', 'One', alternates=[], institution='google.com')

        openreview_client.post_tag(
            openreview.api.Tag(
                invitation='openreview.net/Support/-/Profile_Moderation_Label',
                signature='openreview.net/Support',
                profile='~Amelia_One1',
                label='test label',
            )
        )

        tags = openreview_client.get_tags(invitation='openreview.net/Support/-/Profile_Moderation_Label')
        assert len(tags) == 1

        tag = tags[0]
        tag.ddate = openreview.tools.datetime_millis(datetime.datetime.utcnow())
        tag = openreview_client.post_tag(tag)

        assert len(client.get_tags(invitation='openreview.net/Support/-/Profile_Moderation_Label')) == 0

    def test_import_deprecated_dblp_notes(self, client, openreview_client, test_client, helpers):

        test_client_v2 = openreview.api.OpenReviewClient(username='test@mail.com', password=helpers.strong_password)

        edit = test_client_v2.post_note_edit(
            invitation = 'DBLP.org/-/Record',
            signatures = ['~SomeFirstName_User1'],
            content = {
                'xml': {
                    'value': '<article key=\"journals/iotj/WangJWSGZ23\" mdate=\"2023-04-16\">\n<author orcid=\"0000-0003-4015-0348\" pid=\"188/7759-93\">Chao Wang 0093</author>\n              <author orcid=\"0000-0002-3703-121X\" pid=\"00/8334\">Chunxiao Jiang</author>\n<author orcid=\"0000-0003-3170-8952\" pid=\"62/2631-1\">Jingjing Wang 0001</author>\n<author orcid=\"0000-0002-7558-5379\" pid=\"66/800\">Shigen Shen</author>\n<author orcid=\"0000-0001-9831-2202\" pid=\"01/267-1\">Song Guo 0001</author>\n<author orcid=\"0000-0002-0990-5581\" pid=\"24/9047\">Peiying Zhang</author>\n<title>Blockchain-Aided Network Resource Orchestration in Intelligent Internet of Things.</title>\n<pages>6151-6163</pages>\n<year>2023</year>\n<month>April 1</month>\n<volume>10</volume>\n<journal>IEEE Internet Things J.</journal>\n<number>7</number>\n<ee>https://doi.org/10.1109/JIOT.2022.3222911</ee>\n<url>db/journals/iotj/iotj10.html#WangJWSGZ23</url>\n</article>'

                }
            },
            note = openreview.api.Note(
                content={
                    'title': {
                        'value': 'Blockchain-Aided Network Resource Orchestration in Intelligent Internet of Things',
                    },
                    'authors': {
                        'value': ['Chao Wang 0093', 'Chunxiao Jiang', 'Jingjing Wang 0001', 'Shigen Shen', 'Song Guo 0001', 'Peiying Zhang'],
                    },
                    'venue': {
                        'value': 'WangJWSGZ23',
                    }
                }
            )
        )

        helpers.await_queue_edit(openreview_client, edit_id=edit['id'], error=True)

        note = test_client_v2.get_note(edit['note']['id'])
        assert note.invitations == ['DBLP.org/-/Record', 'DBLP.org/-/Edit']
        assert note.cdate
        assert note.pdate
        assert '_bibtex' in note.content
        assert 'authorids' in note.content
        assert 'venue' in note.content
        assert 'venueid' in note.content
        assert 'html' in note.content

        andrew_client = helpers.create_user('mccallum@profile.org', 'Andrew', 'McCallum', alternates=[], institution='google.com')

        xml = '''<inproceedings key="conf/acl/ChangSRM23" mdate="2023-08-10">
<author pid="130/1022">Haw-Shiuan Chang</author>
<author pid="301/6251">Ruei-Yao Sun</author>
<author pid="331/1034">Kathryn Ricci</author>
<author pid="m/AndrewMcCallum">Andrew McCallum</author>
<title>Multi-CLS BERT: An Efficient Alternative to Traditional Ensembling.</title>
<pages>821-854</pages>
<year>2023</year>
<booktitle>ACL (1)</booktitle>
<ee type="oa">https://doi.org/10.18653/v1/2023.acl-long.48</ee>
<ee type="oa">https://aclanthology.org/2023.acl-long.48</ee>
<crossref>conf/acl/2023-1</crossref>
<url>db/conf/acl/acl2023-1.html#ChangSRM23</url>
</inproceedings>
'''

        edit = andrew_client.post_note_edit(
            invitation = 'DBLP.org/-/Record',
            signatures = ['~Andrew_McCallum1'],
            content = {
                'xml': {
                    'value': xml
                }
            },
            note = openreview.api.Note(
                content={
                    'title': {
                        'value': 'Multi-CLS BERT: An Efficient Alternative to Traditional Ensembling.',
                    },
                    'authors': {
                        'value': ['Haw-Shiuan Chang', 'Ruei-Yao Sun', 'Kathryn Ricci', 'Andrew McCallum'],
                    },
                    'authorids': {
                        'value': ['', '', '', '~Andrew_McCallum1'],
                    },
                    'venue': {
                        'value': 'ACL (1)',
                    }
                }
            )
        )

        helpers.await_queue_edit(openreview_client, edit_id=edit['id'], error=True)

        note = andrew_client.get_note(edit['note']['id'])
        assert note.invitations == ['DBLP.org/-/Record', 'DBLP.org/-/Edit']
        assert note.cdate
        assert note.pdate
        assert '_bibtex' in note.content
        assert 'authorids' in note.content
        assert 'venue' in note.content
        assert 'venueid' in note.content
        assert 'html' in note.content
        assert note.content['title']['value'] == 'Multi-CLS BERT: An Efficient Alternative to Traditional Ensembling'
        assert note.content['authors']['value'] == [
            "Haw-Shiuan Chang",
            "Ruei-Yao Sun",
            "Kathryn Ricci",
            "Andrew McCallum"
        ]
        assert note.content['authorids']['value'] == [
            "https://dblp.org/search/pid/api?q=author:Haw-Shiuan_Chang:",
            "https://dblp.org/search/pid/api?q=author:Ruei-Yao_Sun:",
            "https://dblp.org/search/pid/api?q=author:Kathryn_Ricci:",
            "~Andrew_McCallum1"
        ]

        haw_shiuan_client = helpers.create_user('haw@profile.org', 'Haw-Shiuan', 'Chang', alternates=[], institution='umass.edu')

        edit = haw_shiuan_client.post_note_edit(
            invitation = 'DBLP.org/-/Author_Coreference',
            signatures = ['~Haw-Shiuan_Chang1'],
            content = {
                'author_index': { 'value': 0 },
                'author_id': { 'value': '~Haw-Shiuan_Chang1' },
            },
            note = openreview.api.Note(
                id = note.id
            )
        )

        note = haw_shiuan_client.get_note(edit['note']['id'])
        assert note.invitations == ['DBLP.org/-/Record', 'DBLP.org/-/Edit', 'DBLP.org/-/Author_Coreference']
        assert note.cdate
        assert note.mdate
        assert note.pdate
        assert '_bibtex' in note.content
        assert 'authorids' in note.content
        assert 'venue' in note.content
        assert 'venueid' in note.content
        assert 'html' in note.content
        assert note.content['title']['value'] == 'Multi-CLS BERT: An Efficient Alternative to Traditional Ensembling'
        assert note.content['authorids']['value'] == [
            "~Haw-Shiuan_Chang1",
            "https://dblp.org/search/pid/api?q=author:Ruei-Yao_Sun:",
            "https://dblp.org/search/pid/api?q=author:Kathryn_Ricci:",
            "~Andrew_McCallum1"
        ]

        with pytest.raises(openreview.OpenReviewException, match=r'The author id ~Andrew_McCallum1 doesn\'t match with the names listed in your profile'):
            edit = haw_shiuan_client.post_note_edit(
                invitation = 'DBLP.org/-/Author_Coreference',
                signatures = ['~Haw-Shiuan_Chang1'],
                content = {
                    'author_index': { 'value': 3 },
                    'author_id': { 'value': '~Andrew_McCallum1' },
                },                
                note = openreview.api.Note(
                    id = note.id
                )
            )

        with pytest.raises(openreview.OpenReviewException, match=r'The author name Andrew McCallum from index 3 doesn\'t match with the names listed in your profile'):
            edit = haw_shiuan_client.post_note_edit(
                invitation = 'DBLP.org/-/Author_Coreference',
                signatures = ['~Haw-Shiuan_Chang1'],
                content = {
                    'author_index': { 'value': 3 },
                    'author_id': { 'value': '~Haw-Shiuan_Chang1' },
                },                  
                note = openreview.api.Note(
                    id = note.id
                )
            )            


        with pytest.raises(openreview.OpenReviewException, match=r'The author name Ruei-Yao Sun from index 1 doesn\'t match with the names listed in your profile'):
            edit = test_client_v2.post_note_edit(
                invitation = 'DBLP.org/-/Author_Coreference',
                signatures = ['~SomeFirstName_User1'],
                content = {
                    'author_index': { 'value': 1 },
                    'author_id': { 'value': '~SomeFirstName_User1' },
                },                 
                note = openreview.api.Note(
                    id = note.id
                )
            )

        with pytest.raises(openreview.OpenReviewException, match=r'Invalid author index'):
            edit = haw_shiuan_client.post_note_edit(
                invitation = 'DBLP.org/-/Author_Coreference',
                signatures = ['~Haw-Shiuan_Chang1'],
                content = {
                    'author_index': { 'value': 13 },
                    'author_id': { 'value': '~Haw-Shiuan_Chang1' },
                },                
                note = openreview.api.Note(
                    id = note.id
                )
            )             

        edit = haw_shiuan_client.post_note_edit(
            invitation = 'DBLP.org/-/Author_Coreference',
            signatures = ['~Haw-Shiuan_Chang1'],
            content = {
                'author_index': { 'value': 0 },
                'author_id': { 'value': '' },
            },             
            note = openreview.api.Note(
                id = note.id
            )
        )

        with pytest.raises(openreview.OpenReviewException, match=r'The author name  from index 0 doesn\'t match with the names listed in your profile'):
            edit = andrew_client.post_note_edit(
                invitation = 'DBLP.org/-/Author_Coreference',
                signatures = ['~Andrew_McCallum1'],
                content = {
                    'author_index': { 'value': 0 },
                    'author_id': { 'value': '' },
                },                
                note = openreview.api.Note(
                    id = note.id
                )
            )

        with pytest.raises(openreview.OpenReviewException, match=r'Invalid author index'):
            edit = andrew_client.post_note_edit(
                invitation = 'DBLP.org/-/Author_Coreference',
                signatures = ['~Andrew_McCallum1'],
                content = {
                    'author_index': { 'value': 11 },
                    'author_id': { 'value': '' },
                },                 
                note = openreview.api.Note(
                    id = note.id
                )
            )                        

        note = haw_shiuan_client.get_note(edit['note']['id'])
        assert note.invitations == ['DBLP.org/-/Record', 'DBLP.org/-/Edit', 'DBLP.org/-/Author_Coreference']
        assert note.cdate
        assert note.mdate
        assert note.pdate
        assert '_bibtex' in note.content
        assert 'authorids' in note.content
        assert 'venue' in note.content
        assert 'venueid' in note.content
        assert 'html' in note.content
        assert note.content['title']['value'] == 'Multi-CLS BERT: An Efficient Alternative to Traditional Ensembling'
        assert note.content['authorids']['value'] == [
            '',
            "https://dblp.org/search/pid/api?q=author:Ruei-Yao_Sun:",
            "https://dblp.org/search/pid/api?q=author:Kathryn_Ricci:",
            "~Andrew_McCallum1"
        ]                    

        edit = openreview_client.post_note_edit(
            invitation = 'DBLP.org/-/Abstract',
            signatures = ['DBLP.org/Uploader'],
            note = openreview.api.Note(
                id = note.id,
                content={
                    'abstract': {
                        'value': 'this is an abstract'
                    }
                }
            )
        )
        
        note = haw_shiuan_client.get_note(edit['note']['id'])
        assert note.invitations == ['DBLP.org/-/Record', 'DBLP.org/-/Edit', 'DBLP.org/-/Author_Coreference', 'DBLP.org/-/Abstract']
        assert note.content['abstract']['value'] == 'this is an abstract'

        ## claim dblp paper using another tilde id
        kate_client = helpers.create_user('kate@profile.org', 'Kate', 'Ricci', alternates=[], institution='umass.edu')

        with pytest.raises(openreview.OpenReviewException, match=r'The author name Kathryn Ricci from index 2 doesn\'t match with the names listed in your profile'):
            edit = kate_client.post_note_edit(
                invitation = 'DBLP.org/-/Author_Coreference',
                signatures = ['~Kate_Ricci1'],
                content = {
                    'author_index': { 'value': 2 },
                    'author_id': { 'value': '~Kate_Ricci1' },
                },                 
                note = openreview.api.Note(
                    id = note.id
                )
            ) 

        profile = kate_client.get_profile()

        profile.content['homepage'] = 'https://kate.google.com'
        profile.content['names'].append({
            'first': 'Kathryn',
            'last': 'Ricci'
            })
        kate_client.post_profile(profile)

        edit = kate_client.post_note_edit(
            invitation = 'DBLP.org/-/Author_Coreference',
            signatures = ['~Kate_Ricci1'],
            content = {
                'author_index': { 'value': 2 },
                'author_id': { 'value': '~Kate_Ricci1' },
            },                 
            note = openreview.api.Note(
                id = note.id
            )
        )

        note = haw_shiuan_client.get_note(edit['note']['id'])
        assert note.invitations == ['DBLP.org/-/Record', 'DBLP.org/-/Edit', 'DBLP.org/-/Author_Coreference', 'DBLP.org/-/Abstract']
        assert note.cdate
        assert note.mdate
        assert note.pdate
        assert '_bibtex' in note.content
        assert 'authorids' in note.content
        assert 'venue' in note.content
        assert 'venueid' in note.content
        assert 'html' in note.content
        assert note.content['title']['value'] == 'Multi-CLS BERT: An Efficient Alternative to Traditional Ensembling'
        assert note.content['authorids']['value'] == [
            '',
            "https://dblp.org/search/pid/api?q=author:Ruei-Yao_Sun:",
            "~Kate_Ricci1",
            "~Andrew_McCallum1"
        ] 

        ## claim paper using the super user crendetials
        helpers.create_user('ruei@profile.org', 'Ruei-Yao', 'Sun', alternates=[], institution='google.com')

        edit = openreview_client.post_note_edit(
            invitation = 'DBLP.org/-/Author_Coreference',
            signatures = ['openreview.net/Support'],
            content = {
                'author_index': { 'value': 1 },
                'author_id': { 'value': '~Ruei-Yao_Sun1' },
            },                 
            note = openreview.api.Note(
                id = note.id
            )
        )

        note = haw_shiuan_client.get_note(edit['note']['id'])
        assert note.content['authorids']['value'] == [
            '',
            "~Ruei-Yao_Sun1",
            "~Kate_Ricci1",
            "~Andrew_McCallum1"
        ]        

    def test_import_dblp_notes(self, client, openreview_client, test_client, helpers):

        test_client_v2 = openreview.api.OpenReviewClient(username='test@mail.com', password=helpers.strong_password)

        edit = test_client_v2.post_note_edit(
            invitation = 'openreview.net/Public_Article/DBLP.org/-/Record',
            signatures = ['~SomeFirstName_User1'],
            content = {
                'xml': {
                    'value': '''<inproceedings key="conf/aaai/JiangXFBK0025" mdate="2025-04-17">
<author>Pengcheng Jiang</author>
<author>Cao Xiao</author>
<author>Tianfan Fu</author>
<author>Parminder Bhatia</author>
<author>Taha A. Kass-Hout</author>
<author>Jimeng Sun 0001</author>
<author>Jiawei Han 0001</author>
<title>Bi-level Contrastive Learning for Knowledge-Enhanced Molecule Representations.</title>
<pages>352-360</pages>
<year>2025</year>
<booktitle>AAAI</booktitle>
<ee type="oa">https://doi.org/10.1609/aaai.v39i1.32013</ee>
<crossref>conf/aaai/2025</crossref>
<url>db/conf/aaai/aaai2025.html#JiangXFBK0025</url>
</inproceedings>
'''

                }
            },
            note = openreview.api.Note(
                external_id = 'dblp:conf/aaai/JiangXFBK0025',
                content={
                    'title': {
                        'value': 'Bi-level Contrastive Learning for Knowledge-Enhanced Molecule Representations',
                    },
                    'authors': {
                        'value': ['Pengcheng Jiang', 'Cao Xiao', 'Tianfan Fu', 'Parminder Bhatia', 'Taha A. Kass-Hout', 'Jimeng Sun 0001', 'Jiawei Han 0001'],
                    },
                    'venue': {
                        'value': 'JiangXFBK0025',
                    }
                }
            )
        )

        helpers.await_queue_edit(openreview_client, edit_id=edit['id'], process_index=0)

        note = test_client_v2.get_note(edit['note']['id'])
        assert note.invitations == ['openreview.net/Public_Article/DBLP.org/-/Record', 'openreview.net/Public_Article/-/Edit']
        assert note.cdate
        assert note.pdate
        assert note.external_ids == ['dblp:conf/aaai/JiangXFBK0025']
        assert '_bibtex' in note.content
        assert 'authorids' in note.content
        assert 'venue' in note.content
        assert 'venueid' in note.content
        assert 'html' in note.content
        assert 'abstract' not in note.content

        helpers.await_queue_edit(openreview_client, edit_id=edit['id'], process_index=1, error=True)

        andrew_client = helpers.create_user('mccallum@profile.org', 'Andrew', 'McCallum', alternates=[], institution='google.com', dblp_url='https://dblp.org/pid/m/AndrewMcCallum')

        xml = '''<article key="journals/corr/abs-2508-04024" publtype="informal" mdate="2025-09-10">
<author>Nihar B. Shah</author>
<author>Melisa Bok</author>
<author>Xukun Liu</author>
<author>Andrew McCallum</author>
<title>Identity Theft in AI Conference Peer Review.</title>
<year>2025</year>
<month>August</month>
<volume>abs/2508.04024</volume>
<journal>CoRR</journal>
<ee type="oa">https://doi.org/10.48550/arXiv.2508.04024</ee>
<url>db/journals/corr/corr2508.html#abs-2508-04024</url>
<stream>streams/journals/corr</stream>
</article>
'''

        edit = andrew_client.post_note_edit(
            invitation = 'openreview.net/Public_Article/DBLP.org/-/Record',
            signatures = ['~Andrew_McCallum1'],
            content = {
                'xml': {
                    'value': xml
                }
            },
            note = openreview.api.Note(
                external_id = 'dblp:journals/corr/abs-2508-04024',
                content={
                    'title': {
                        'value': 'Identity Theft in AI Conference Peer Review',
                    },
                    'authors': {
                        'value': ['Nihar B. Shah', 'Melisa Bok', 'Xukun Liu', 'Andrew McCallum'],
                    },
                    'venue': {
                        'value': 'CoRR',
                    }
                }
            )
        )

        helpers.await_queue_edit(openreview_client, edit_id=edit['id'], process_index=0)
        helpers.await_queue_edit(openreview_client, edit_id=edit['id'], process_index=1, error=True)

        note = andrew_client.get_note(edit['note']['id'])

        edit = andrew_client.post_note_edit(
            invitation = 'openreview.net/Public_Article/-/Authorship_Claim',
            signatures = ['~Andrew_McCallum1'],
            content = {
                'author_index': { 'value': 3 },
                'author_id': { 'value': '~Andrew_McCallum1' },
            },
            note = openreview.api.Note(
                id = note.id
            )
        )

        note = andrew_client.get_note(edit['note']['id'])
        assert note.invitations == ['openreview.net/Public_Article/DBLP.org/-/Record', 
                                    'openreview.net/Public_Article/-/Edit', 
                                    'openreview.net/Public_Article/-/Authorship_Claim']
        assert note.cdate
        assert note.pdate
        assert note.external_ids == ['dblp:journals/corr/abs-2508-04024']
        assert '_bibtex' in note.content
        assert 'authorids' in note.content
        assert 'venue' in note.content
        assert 'venueid' in note.content
        assert 'html' in note.content
        assert 'abstract' not in note.content
        assert note.content['title']['value'] == 'Identity Theft in AI Conference Peer Review'
        assert note.content['authors']['value'] == [
            "Nihar B. Shah",
            "Melisa Bok",
            "Xukun Liu",
            "Andrew McCallum"
        ]
        assert note.content['authorids']['value'] == [
            "https://dblp.org/search/pid/api?q=author:Nihar_B._Shah:",
            "https://dblp.org/search/pid/api?q=author:Melisa_Bok:",
            "https://dblp.org/search/pid/api?q=author:Xukun_Liu:",
            "~Andrew_McCallum1"
        ]

        nihar_client = helpers.create_user('nihar@profile.org', 'Nihar B.', 'Shah', alternates=[], institution='google.com')

        edit = nihar_client.post_note_edit(
            invitation = 'openreview.net/Public_Article/-/Authorship_Claim',
            signatures = ['~Nihar_B._Shah1'],
            content = {
                'author_index': { 'value': 0 },
                'author_id': { 'value': '~Nihar_B._Shah1' },
            },
            note = openreview.api.Note(
                id = note.id
            )
        )        

        note = andrew_client.get_note(edit['note']['id'])

        assert note.content['authorids']['value'] == [
            "~Nihar_B._Shah1",
            "https://dblp.org/search/pid/api?q=author:Melisa_Bok:",
            "https://dblp.org/search/pid/api?q=author:Xukun_Liu:",
            "~Andrew_McCallum1"
        ]

        edit = nihar_client.post_note_edit(
            invitation = 'openreview.net/Public_Article/-/Author_Removal',
            signatures = ['~Nihar_B._Shah1'],
            content = {
                'author_index': { 'value': 0 },
                'author_id': { 'value': '' },
            },
            note = openreview.api.Note(
                id = note.id
            )
        )

        note = andrew_client.get_note(edit['note']['id'])

        assert note.content['authorids']['value'] == [
            "",
            "https://dblp.org/search/pid/api?q=author:Melisa_Bok:",
            "https://dblp.org/search/pid/api?q=author:Xukun_Liu:",
            "~Andrew_McCallum1"
        ]                

    @pytest.mark.skip(reason="Skipping this test until we decide to enable comments")
    def test_dblp_enable_comments(self, client, openreview_client, test_client, helpers):

        dblp_notes = openreview_client.get_notes(invitation='openreview.net/Public_Article/DBLP.org/-/Record', sort='number:asc')
        assert len(dblp_notes) == 3

        dblp_forum = dblp_notes[1].forum

        invitations = openreview_client.get_invitations(replyForum=dblp_forum)
        #assert len(invitations) == 5 ## Author Coreference, Abstract, Comment, Notification Subscription, Bookmark
        names = [invitation.id for invitation in invitations]
        assert 'openreview.net/Public_Article/-/Authorship_Claim' in names
        assert 'openreview.net/Public_Article/DBLP.org/-/Record' in names
        assert 'openreview.net/Public_Article/arXiv.org/-/Record' in names
        assert 'openreview.net/Public_Article/DBLP.org/-/Abstract' in names
        assert 'openreview.net/Public_Article/-/Comment' in names
        assert 'openreview.net/Public_Article/-/Notification_Subscription' in names
        assert 'openreview.net/Public_Article/-/Bookmark' in names

        test_client = openreview.api.OpenReviewClient(username='test@mail.com', password=helpers.strong_password)
        edit = test_client.post_note_edit(
            invitation='openreview.net/Public_Article/-/Comment',
            signatures=['~SomeFirstName_User1'],
            note = openreview.api.Note(
                forum = dblp_forum,
                replyto = dblp_forum,
                content = {
                    'comment': { 'value': 'this is a comment' }
                }
            )
        )

        helpers.await_queue_edit(openreview_client, edit_id=edit['id'])

        messages = openreview_client.get_messages(to='test@mail.com', subject='[OpenReview] SomeFirstName User commented on a publication with title: "Multi-CLS BERT: An Efficient Alternative to Traditional Ensembling"')
        assert len(messages) == 0

        messages = openreview_client.get_messages(to='test@mail.com', subject='[OpenReview] Your comment was received on a publication with title: "Multi-CLS BERT: An Efficient Alternative to Traditional Ensembling"')
        assert len(messages) == 1        

        messages = openreview_client.get_messages(to='mccallum@profile.org', subject='[OpenReview] SomeFirstName User commented on your publication with title: "Multi-CLS BERT: An Efficient Alternative to Traditional Ensembling"')
        assert len(messages) == 1

        messages = openreview_client.get_messages(to='kate@profile.org', subject='[OpenReview] SomeFirstName User commented on your publication with title: "Multi-CLS BERT: An Efficient Alternative to Traditional Ensembling"')
        assert len(messages) == 1

        ## unsubscribe from comments
        andrew_client = openreview.api.OpenReviewClient(username='mccallum@profile.org', password=helpers.strong_password)
        subscribe_tag = andrew_client.get_tags(invitation='openreview.net/Public_Article/-/Notification_Subscription', note=dblp_forum, signature='~Andrew_McCallum1')[0]
        subscribe_tag.ddate = openreview.tools.datetime_millis(datetime.datetime.now())
        andrew_client.post_tag(
            subscribe_tag
        )

        edit = test_client.post_note_edit(
            invitation='openreview.net/Public_Article/-/Comment',
            signatures=['~SomeFirstName_User1'],
            note = openreview.api.Note(
                forum = dblp_forum,
                replyto = dblp_forum,
                content = {
                    'comment': { 'value': 'This is another comment' }
                }
            )
        )
            
        helpers.await_queue_edit(openreview_client, edit_id=edit['id'])

        messages = openreview_client.get_messages(to='test@mail.com', subject='[OpenReview] SomeFirstName User commented on a publication with title: "Multi-CLS BERT: An Efficient Alternative to Traditional Ensembling"')
        assert len(messages) == 0

        messages = openreview_client.get_messages(to='test@mail.com', subject='[OpenReview] Your comment was received on a publication with title: "Multi-CLS BERT: An Efficient Alternative to Traditional Ensembling"')
        assert len(messages) == 2        

        messages = openreview_client.get_messages(to='mccallum@profile.org', subject='[OpenReview] SomeFirstName User commented on your publication with title: "Multi-CLS BERT: An Efficient Alternative to Traditional Ensembling"')
        assert len(messages) == 1

        messages = openreview_client.get_messages(to='kate@profile.org', subject='[OpenReview] SomeFirstName User commented on your publication with title: "Multi-CLS BERT: An Efficient Alternative to Traditional Ensembling"')
        assert len(messages) == 2

        guest_client = helpers.create_user('justin@profile.org', 'Justin', 'Last', alternates=[], institution='google.com')
        edit = guest_client.post_tag(
            openreview.api.Tag(
                invitation='openreview.net/Public_Article/-/Notification_Subscription',
                signature='~Justin_Last1',
                forum=dblp_forum,
                note=dblp_forum
            )
        )

        edit = test_client.post_note_edit(
            invitation='openreview.net/Public_Article/-/Comment',
            signatures=['~SomeFirstName_User1'],
            note = openreview.api.Note(
                forum = dblp_forum,
                replyto = dblp_forum,
                content = {
                    'comment': { 'value': 'This is another comment #3' }
                }
            )
        )
            
        helpers.await_queue_edit(openreview_client, edit_id=edit['id'])

        messages = openreview_client.get_messages(to='test@mail.com', subject='[OpenReview] SomeFirstName User commented on a publication with title: "Multi-CLS BERT: An Efficient Alternative to Traditional Ensembling"')
        assert len(messages) == 0

        messages = openreview_client.get_messages(to='test@mail.com', subject='[OpenReview] Your comment was received on a publication with title: "Multi-CLS BERT: An Efficient Alternative to Traditional Ensembling"')
        assert len(messages) == 3        

        messages = openreview_client.get_messages(to='mccallum@profile.org', subject='[OpenReview] SomeFirstName User commented on your publication with title: "Multi-CLS BERT: An Efficient Alternative to Traditional Ensembling"')
        assert len(messages) == 1

        messages = openreview_client.get_messages(to='kate@profile.org', subject='[OpenReview] SomeFirstName User commented on your publication with title: "Multi-CLS BERT: An Efficient Alternative to Traditional Ensembling"')
        assert len(messages) == 3        

        messages = openreview_client.get_messages(to='justin@profile.org', subject='[OpenReview] SomeFirstName User commented on a publication with title: "Multi-CLS BERT: An Efficient Alternative to Traditional Ensembling"')
        assert len(messages) == 1

        ## post a comment and be automatically subscribed
        guest_client = helpers.create_user('sue@profile.org', 'Sue', 'Last', alternates=[], institution='google.com')

        edit = guest_client.post_note_edit(
            invitation='openreview.net/Public_Article/-/Comment',
            signatures=['~Sue_Last1'],
            note = openreview.api.Note(
                forum = dblp_forum,
                replyto = dblp_forum,
                content = {
                    'comment': { 'value': 'This is another comment #4' }
                }
            )
        )

        helpers.await_queue_edit(openreview_client, edit_id=edit['id'])

        messages = openreview_client.get_messages(to='test@mail.com', subject='[OpenReview] Sue Last commented on a publication with title: "Multi-CLS BERT: An Efficient Alternative to Traditional Ensembling"')
        assert len(messages) == 1

        messages = openreview_client.get_messages(to='mccallum@profile.org', subject='[OpenReview] Sue Last commented on your publication with title: "Multi-CLS BERT: An Efficient Alternative to Traditional Ensembling"')
        assert len(messages) == 0

        messages = openreview_client.get_messages(to='kate@profile.org', subject='[OpenReview] Sue Last commented on your publication with title: "Multi-CLS BERT: An Efficient Alternative to Traditional Ensembling"')
        assert len(messages) == 1        

        messages = openreview_client.get_messages(to='justin@profile.org', subject='[OpenReview] Sue Last commented on a publication with title: "Multi-CLS BERT: An Efficient Alternative to Traditional Ensembling"')
        assert len(messages) == 1        

        messages = openreview_client.get_messages(to='sue@profile.org', subject='[OpenReview] Sue Last commented on a publication with title: "Multi-CLS BERT: An Efficient Alternative to Traditional Ensembling"')
        assert len(messages) == 0

        messages = openreview_client.get_messages(to='sue@profile.org', subject='[OpenReview] Your comment was received on a publication with title: "Multi-CLS BERT: An Efficient Alternative to Traditional Ensembling"')
        assert len(messages) == 1

        edit = andrew_client.post_note_edit(
            invitation='openreview.net/Public_Article/-/Comment',
            signatures=['~Andrew_McCallum1'],
            note = openreview.api.Note(
                forum = dblp_forum,
                replyto = dblp_forum,
                content = {
                    'comment': { 'value': 'This is another comment #5' }
                }
            )
        )

        helpers.await_queue_edit(openreview_client, edit_id=edit['id'])

        messages = openreview_client.get_messages(to='test@mail.com', subject='[OpenReview] Andrew McCallum commented on a publication with title: "Multi-CLS BERT: An Efficient Alternative to Traditional Ensembling"')
        assert len(messages) == 1

        messages = openreview_client.get_messages(to='mccallum@profile.org', subject='[OpenReview] Andrew McCallum commented on your publication with title: "Multi-CLS BERT: An Efficient Alternative to Traditional Ensembling"')
        assert len(messages) == 0

        messages = openreview_client.get_messages(to='mccallum@profile.org', subject='[OpenReview] Your comment was received on a publication with title: "Multi-CLS BERT: An Efficient Alternative to Traditional Ensembling"')
        assert len(messages) == 1        

        messages = openreview_client.get_messages(to='kate@profile.org', subject='[OpenReview] Andrew McCallum commented on your publication with title: "Multi-CLS BERT: An Efficient Alternative to Traditional Ensembling"')
        assert len(messages) == 1        

        messages = openreview_client.get_messages(to='justin@profile.org', subject='[OpenReview] Andrew McCallum commented on a publication with title: "Multi-CLS BERT: An Efficient Alternative to Traditional Ensembling"')
        assert len(messages) == 1       

        messages = openreview_client.get_messages(to='sue@profile.org', subject='[OpenReview] Andrew McCallum commented on a publication with title: "Multi-CLS BERT: An Efficient Alternative to Traditional Ensembling"')
        assert len(messages) == 1        
   
    
    def test_import_arxiv_notes(self, client, openreview_client, test_client, helpers):

        andrew_client = openreview.api.OpenReviewClient(username='mccallum@profile.org', password=helpers.strong_password)
        edit = andrew_client.post_note_edit(
            invitation='openreview.net/Public_Article/arXiv.org/-/Record',
            signatures=['~Andrew_McCallum1'],
            content = {
                'xml': {
                    'value': '''<entry>
    <id>http://arxiv.org/abs/2502.10875v1</id>
    <updated>2025-02-15T18:18:00Z</updated>
    <published>2025-02-15T18:18:00Z</published>
    <title>A Geometric Approach to Personalized Recommendation with Set-Theoretic
  Constraints Using Box Embeddings</title>
    <summary>  Personalized item recommendation typically suffers from data sparsity, which
is most often addressed by learning vector representations of users and items
via low-rank matrix factorization. While this effectively densifies the matrix
by assuming users and movies can be represented by linearly dependent latent
features, it does not capture more complicated interactions. For example,
vector representations struggle with set-theoretic relationships, such as
negation and intersection, e.g. recommending a movie that is "comedy and
action, but not romance". In this work, we formulate the problem of
personalized item recommendation as matrix completion where rows are
set-theoretically dependent. To capture this set-theoretic dependence we
represent each user and attribute by a hyper-rectangle or box (i.e. a Cartesian
product of intervals). Box embeddings can intuitively be understood as
trainable Venn diagrams, and thus not only inherently represent similarity (via
the Jaccard index), but also naturally and faithfully support arbitrary
set-theoretic relationships. Queries involving set-theoretic constraints can be
efficiently computed directly on the embedding space by performing geometric
operations on the representations. We empirically demonstrate the superiority
of box embeddings over vector-based neural methods on both simple and complex
item recommendation queries by up to 30 \% overall.
</summary>
    <author>
      <name>Shib Dasgupta</name>
    </author>
    <author>
      <name>Michael Boratko</name>
    </author>
    <author>
      <name>Andrew McCallum</name>
    </author>
    <link href="http://arxiv.org/abs/2502.10875v1" rel="alternate" type="text/html"/>
    <link title="pdf" href="http://arxiv.org/pdf/2502.10875v1" rel="related" type="application/pdf"/>
    <arxiv:primary_category xmlns:arxiv="http://arxiv.org/schemas/atom" term="cs.IR" scheme="http://arxiv.org/schemas/atom"/>
    <category term="cs.IR" scheme="http://arxiv.org/schemas/atom"/>
    <category term="cs.AI" scheme="http://arxiv.org/schemas/atom"/>
    <category term="cs.LG" scheme="http://arxiv.org/schemas/atom"/>
  </entry>'''
                }
            },
            note = openreview.api.Note(
                external_id = 'arxiv:2502.10875',
                pdate= openreview.tools.datetime_millis(datetime.datetime(2025, 2, 15)),
                mdate= openreview.tools.datetime_millis(datetime.datetime(2025, 2, 15)),
                content={
                    'title': {
                        'value': 'A Geometric Approach to Personalized Recommendation with Set-Theoretic Constraints Using Box Embeddings'
                    },
                    'abstract': {
                        'value': 'Personalized item recommendation typically suffers from data sparsity, which is most often addressed by learning vector representations of users and items via low-rank matrix factorization. While this effectively densifies the matrix by assuming users and movies can be represented by linearly dependent latent features, it does not capture more complicated interactions. For example, vector representations struggle with set-theoretic relationships, such as negation and intersection, e.g. recommending a movie that is "comedy and action, but not romance". In this work, we formulate the problem of personalized item recommendation as matrix completion where rows are set-theoretically dependent. To capture this set-theoretic dependence we represent each user and attribute by a hyper-rectangle or box (i.e. a Cartesian product of intervals). Box embeddings can intuitively be understood as trainable Venn diagrams, and thus not only inherently represent similarity (via the Jaccard index), but also naturally and faithfully support arbitrary set-theoretic relationships. Queries involving set-theoretic constraints can be efficiently computed directly on the embedding space by performing geometric operations on the representations. We empirically demonstrate the superiority of box embeddings over vector-based neural methods on both simple and complex item recommendation queries by up to 30 \% overall.'
                    },
                    'authors': {
                        'value': ['Shib Dasgupta', 'Michael Boratko', 'Andrew McCallum']
                    },
                    'subject_areas': {
                        'value': ['cs.IR', 'cs.AI', 'cs.LG']
                    },
                    'pdf': {
                        'value': 'https://arxiv.org/pdf/2502.10875.pdf'
                    }
                }
            )
        )

        helpers.await_queue_edit(openreview_client, edit_id=edit['id'])

        geometric_note = andrew_client.get_note(edit['note']['id'])
        assert geometric_note.content['authorids']['value'] == [
            "https://arxiv.org/search/?query=Shib%20Dasgupta&searchtype=all",
            "https://arxiv.org/search/?query=Michael%20Boratko&searchtype=all",
            "https://arxiv.org/search/?query=Andrew%20McCallum&searchtype=all"
        ]

        edit = andrew_client.post_note_edit(
            invitation = 'openreview.net/Public_Article/-/Authorship_Claim',
            signatures = ['~Andrew_McCallum1'],
            content = {
                'author_index': { 'value': 2 },
                'author_id': { 'value': '~Andrew_McCallum1' },
            },                 
            note = openreview.api.Note(
                id = geometric_note.id
            )
        )        

        geometric_note = andrew_client.get_note(edit['note']['id'])
        assert geometric_note.content['authorids']['value'] == [
            "https://arxiv.org/search/?query=Shib%20Dasgupta&searchtype=all",
            "https://arxiv.org/search/?query=Michael%20Boratko&searchtype=all",
            "~Andrew_McCallum1"
        ]

        # Do not merge publications for now
        # dblp_arxiv_notes = openreview_client.get_notes(paper_hash='chang|multicls_bert_an_efficient_alternative_to_traditional_ensembling', content={ 'venue': 'CoRR 2022' })
        # assert len(dblp_arxiv_notes) == 1
        # existing_note = dblp_arxiv_notes[0]
        
        edit = andrew_client.post_note_edit(
            invitation='openreview.net/Public_Article/arXiv.org/-/Record',
            signatures=['~Andrew_McCallum1'],
            content={
                'xml': {
                    'value': '''  <entry>
    <id>http://arxiv.org/abs/2210.05043v2</id>
    <updated>2023-05-20T21:47:18Z</updated>
    <published>2022-10-10T23:15:17Z</published>
    <title>Multi-CLS BERT: An Efficient Alternative to Traditional Ensembling</title>
    <summary>  Ensembling BERT models often significantly improves accuracy, but at the cost
of significantly more computation and memory footprint. In this work, we
propose Multi-CLS BERT, a novel ensembling method for CLS-based prediction
tasks that is almost as efficient as a single BERT model. Multi-CLS BERT uses
multiple CLS tokens with a parameterization and objective that encourages their
diversity. Thus instead of fine-tuning each BERT model in an ensemble (and
running them all at test time), we need only fine-tune our single Multi-CLS
BERT model (and run the one model at test time, ensembling just the multiple
final CLS embeddings). To test its effectiveness, we build Multi-CLS BERT on
top of a state-of-the-art pretraining method for BERT (Aroca-Ouellette and
Rudzicz, 2020). In experiments on GLUE and SuperGLUE we show that our Multi-CLS
BERT reliably improves both overall accuracy and confidence estimation. When
only 100 training samples are available in GLUE, the Multi-CLS BERT_Base model
can even outperform the corresponding BERT_Large model. We analyze the behavior
of our Multi-CLS BERT, showing that it has many of the same characteristics and
behavior as a typical BERT 5-way ensemble, but with nearly 4-times less
computation and memory.
</summary>
    <author>
      <name>Haw-Shiuan Chang</name>
    </author>
    <author>
      <name>Ruei-Yao Sun</name>
    </author>
    <author>
      <name>Kathryn Ricci</name>
    </author>
    <author>
      <name>Andrew McCallum</name>
    </author>
    <arxiv:comment xmlns:arxiv="http://arxiv.org/schemas/atom">ACL 2023</arxiv:comment>
    <link href="http://arxiv.org/abs/2210.05043v2" rel="alternate" type="text/html"/>
    <link title="pdf" href="http://arxiv.org/pdf/2210.05043v2" rel="related" type="application/pdf"/>
    <arxiv:primary_category xmlns:arxiv="http://arxiv.org/schemas/atom" term="cs.CL" scheme="http://arxiv.org/schemas/atom"/>
    <category term="cs.CL" scheme="http://arxiv.org/schemas/atom"/>
    <category term="cs.LG" scheme="http://arxiv.org/schemas/atom"/>
  </entry>'''
                }
            },
            note = openreview.api.Note(
                external_id = 'arxiv:2210.05043v2',
                pdate= openreview.tools.datetime_millis(datetime.datetime(2025, 2, 15)),
                mdate= openreview.tools.datetime_millis(datetime.datetime(2025, 2, 15)),
                content={
                    'title': {
                        'value': 'Multi-CLS BERT: An Efficient Alternative to Traditional Ensembling'
                    },
                    'abstract': {
                        'value': 'Ensembling BERT models often significantly improves accuracy, but at the cost of significantly more computation and memory footprint. In this work, we propose Multi-CLS BERT, a novel ensembling method for CLS-based prediction tasks that is almost as efficient as a single BERT model. Multi-CLS BERT uses multiple CLS tokens with a parameterization and objective that encourages their diversity. Thus instead of fine-tuning each BERT model in an ensemble (and running them all at test time), we need only fine-tune our single Multi-CLS BERT model (and run the one model at test time, ensembling just the multiple final CLS embeddings). To test its effectiveness, we build Multi-CLS BERT on top of a state-of-the-art pretraining method for BERT (Aroca-Ouellette and Rudzicz, 2020). In experiments on GLUE and SuperGLUE we show that our Multi-CLS BERT reliably improves both overall accuracy and confidence estimation. When only 100 training samples are available in GLUE, the Multi-CLS BERT_Base model can even outperform the corresponding BERT_Large model. We analyze the behavior of our Multi-CLS BERT, showing that it has many of the same characteristics and behavior as a typical BERT 5-way ensemble, but with nearly 4-times less computation and memory.'
                    },
                    'authors': {
                        'value': ['Haw-Shiuan Chang', 'Ruei-Yao Sun', 'Kathryn Ricci', 'Andrew McCallum']
                    },
                    'subject_areas': {
                        'value': ['cs.CL', 'cs.LG']
                    },
                    'pdf': {
                        'value': 'https://arxiv.org/pdf/2210.05043.pdf'
                    }
                }
            )
        )

        helpers.await_queue_edit(openreview_client, edit_id=edit['id'])

        updated_note = andrew_client.get_note(edit['note']['id'])
        assert updated_note.external_ids == ['arxiv:2210.05043v2']
        assert 'https://arxiv.org/search/?query=Andrew%20McCallum&searchtype=all' in updated_note.content['authorids']['value']
        assert 'https://arxiv.org/search/?query=Haw-Shiuan%20Chang&searchtype=all' in updated_note.content['authorids']['value']
        assert 'https://arxiv.org/search/?query=Ruei-Yao%20Sun&searchtype=all' in updated_note.content['authorids']['value']
        assert 'https://arxiv.org/search/?query=Kathryn%20Ricci&searchtype=all' in updated_note.content['authorids']['value']

        edit = andrew_client.post_note_edit(
            invitation = 'openreview.net/Public_Article/-/Authorship_Claim',
            signatures = ['~Andrew_McCallum1'],
            content = {
                'author_index': { 'value': 3 },
                'author_id': { 'value': '~Andrew_McCallum1' },
            },                 
            note = openreview.api.Note(
                id = updated_note.id
            )
        )        

        updated_note = andrew_client.get_note(edit['note']['id'])
        assert '~Andrew_McCallum1' in updated_note.content['authorids']['value']
        

        # Update an existing arxiv note 
#         xml = '''<article key="journals/corr/abs-2502-10875" publtype="informal" mdate="2025-03-17">
# <author>Shib Sankar Dasgupta</author>
# <author>Michael Boratko</author>
# <author>Andrew McCallum</author>
# <title>A Geometric Approach to Personalized Recommendation with Set-Theoretic Constraints Using Box Embeddings.</title>
# <year>2025</year>
# <month>February</month>
# <volume>abs/2502.10875</volume>
# <journal>CoRR</journal>
# <ee type="oa">https://doi.org/10.48550/arXiv.2502.10875</ee>
# <url>db/journals/corr/corr2502.html#abs-2502-10875</url>
# <stream>streams/journals/corr</stream>
# </article>
# '''

#         edit = andrew_client.post_note_edit(
#             invitation = 'openreview.net/Public_Article/DBLP.org/-/Record',
#             signatures = ['~Andrew_McCallum1'],
#             content = {
#                 'xml': {
#                     'value': xml
#                 }
#             },
#             note = openreview.api.Note(
#                 id = geometric_note.id,
#                 external_id = 'dblp:journals/corr/abs-2502-10875',
#                 content={
#                     'title': {
#                         'value': 'A Geometric Approach to Personalized Recommendation with Set-Theoretic Constraints Using Box Embeddings.',
#                     },
#                     'authors': {
#                         'value': ['Shib Dasgupta', 'Michael Boratko', 'Andrew McCallum']
#                     },
#                     'venue': {
#                         'value': 'CoRR 2025',
#                     }
#                 }
#             )
#         )

#         helpers.await_queue_edit(openreview_client, edit_id=edit['id'], process_index=0)

#         helpers.await_queue_edit(openreview_client, edit_id=edit['id'], process_index=1, error=True)

#         updated_geometric_note = andrew_client.get_note(geometric_note.id)
#         assert updated_geometric_note.external_ids == ['arxiv:2502.10875', 'dblp:journals/corr/abs-2502-10875']
#         assert '~Andrew_McCallum1' in updated_geometric_note.content['authorids']['value']

        # michael_client = helpers.create_user('michael@profile.org', 'Michael', 'Boratko', alternates=[], institution='google.com')        
        
        # with pytest.raises(openreview.OpenReviewException, match=r'A document with the value dblp:journals/corr/abs-2502-10875 in externalIds already exists.'): 
        #     edit = michael_client.post_note_edit(
        #         invitation = 'openreview.net/Public_Article/DBLP.org/-/Record',
        #         signatures = ['~Michael_Boratko1'],
        #         content = {
        #             'xml': {
        #                 'value': xml
        #             }
        #         },
        #         note = openreview.api.Note(
        #             external_id = 'dblp:journals/corr/abs-2502-10875',
        #             content={
        #                 'title': {
        #                     'value': 'A Geometric Approach to Personalized Recommendation with Set-Theoretic Constraints Using Box Embeddings.',
        #                 },
        #                 'authors': {
        #                     'value': ['Shib Dasgupta', 'Michael Boratko', 'Andrew McCallum']
        #                 },
        #                 'venue': {
        #                     'value': 'CoRR 2025',
        #                 }
        #             }
        #         )
        #     )

        #     helpers.await_queue_edit(openreview_client, edit_id=edit['id'], process_index=0)

        #     helpers.await_queue_edit(openreview_client, edit_id=edit['id'], process_index=1, error=True)

        ## import and arxiv note and then try to import a DBLP note and throw an error
        # edit = andrew_client.post_note_edit(
        #     invitation='openreview.net/Public_Article/arXiv.org/-/Record',
        #     signatures=['~Andrew_McCallum1'],
        #     note = openreview.api.Note(
        #         external_id = 'arxiv:2401.08047',
        #         pdate= openreview.tools.datetime_millis(datetime.datetime(2025, 2, 15)),
        #         mdate= openreview.tools.datetime_millis(datetime.datetime(2025, 2, 15)),
        #         content={
        #             'title': {
        #                 'value': 'Incremental Extractive Opinion Summarization Using Cover Trees'
        #             },
        #             'abstract': {
        #                 'value': 'Extractive opinion summarization involves automatically producing a summary of text about an entity (e.g., a product\'s reviews) by extracting representative sentences that capture prevalent opinions in the review set. Typically, in online marketplaces user reviews accumulate over time, and opinion summaries need to be updated periodically to provide customers with up-to-date information. In this work, we study the task of extractive opinion summarization in an incremental setting, where the underlying review set evolves over time. Many of the state-of-the-art extractive opinion summarization approaches are centrality-based, such as CentroidRank (Radev et al., 2004; Chowdhury et al., 2022). CentroidRank performs extractive summarization by selecting a subset of review sentences closest to the centroid in the representation space as the summary. However, these methods are not capable of operating efficiently in an incremental setting, where reviews arrive one at a time. In this paper, we present an efficient algorithm for accurately computing the CentroidRank summaries in an incremental setting. Our approach, CoverSumm, relies on indexing review representations in a cover tree and maintaining a reservoir of candidate summary review sentences. CoverSumm\'s efficacy is supported by a theoretical and empirical analysis of running time. Empirically, on a diverse collection of data (both real and synthetically created to illustrate scaling considerations), we demonstrate that CoverSumm is up to 36x faster than baseline methods, and capable of adapting to nuanced changes in data distribution. We also conduct human evaluations of the generated summaries and find that CoverSumm is capable of producing informative summaries consistent with the underlying review set.'
        #             },
        #             'authors': {
        #                 'value': ['Somnath Basu Roy Chowdhury', 'Nicholas Monath', 'Avinava Dubey', 'Manzil Zaheer', 'Andrew McCallum', 'Amr Ahmed', 'Snigdha Chaturvedi']
        #             },
        #             'subject_areas': {
        #                 'value': ['cs.CL', 'cs.LG']
        #             },
        #             'pdf': {
        #                 'value': 'https://arxiv.org/pdf/2401.08047.pdf'
        #             }
        #         }
        #     )
        # )
        # helpers.await_queue_edit(openreview_client, edit_id=edit['id'])

        # incremental_note = andrew_client.get_note(edit['note']['id'])
        # assert incremental_note.external_ids == ['arxiv:2401.08047']
        # assert '~Andrew_McCallum1' not in incremental_note.content['authorids']['value']

        # edit = andrew_client.post_note_edit(
        #     invitation = 'openreview.net/Public_Article/-/Authorship_Claim',
        #     signatures = ['~Andrew_McCallum1'],
        #     content = {
        #         'author_index': { 'value': 4 },
        #         'author_id': { 'value': '~Andrew_McCallum1' },
        #     },                 
        #     note = openreview.api.Note(
        #         id = incremental_note.id
        #     )
        # )

#         incremental_note = andrew_client.get_note(edit['note']['id'])
#         assert incremental_note.external_ids == ['arxiv:2401.08047']
#         assert 'authorids' in incremental_note.content
#         assert '~Andrew_McCallum1' in incremental_note.content['authorids']['value']
#         assert 'https://arxiv.org/search/?query=Somnath Basu Roy Chowdhury&searchtype=all' in incremental_note.content['authorids']['value']
#         assert 'https://arxiv.org/search/?query=Nicholas Monath&searchtype=all' in incremental_note.content['authorids']['value']
#         assert 'https://arxiv.org/search/?query=Avinava Dubey&searchtype=all' in incremental_note.content['authorids']['value']
#         assert 'https://arxiv.org/search/?query=Manzil Zaheer&searchtype=all' in incremental_note.content['authorids']['value']
#         assert 'https://arxiv.org/search/?query=Amr Ahmed&searchtype=all' in incremental_note.content['authorids']['value']
#         assert 'https://arxiv.org/search/?query=Snigdha Chaturvedi&searchtype=all' in incremental_note.content['authorids']['value']

#         with pytest.raises(openreview.OpenReviewException, match=r'A public article from Arxiv is already present.'): 
#             edit = andrew_client.post_note_edit(
#                 invitation = 'openreview.net/Public_Article/DBLP.org/-/Record',
#                 signatures = ['~Andrew_McCallum1'],
#                 content = {
#                     'xml': {
#                         'value': '''<article key="journals/corr/abs-2401-08047" publtype="informal" mdate="2024-02-01">
# <author>Somnath Basu Roy Chowdhury</author>
# <author>Nicholas Monath</author>
# <author>Avinava Dubey</author>
# <author>Manzil Zaheer</author>
# <author>Andrew McCallum</author>
# <author>Amr Ahmed 0001</author>
# <author>Snigdha Chaturvedi</author>
# <title>Incremental Extractive Opinion Summarization Using Cover Trees.</title>
# <year>2024</year>
# <volume>abs/2401.08047</volume>
# <journal>CoRR</journal>
# <ee type="oa">https://doi.org/10.48550/arXiv.2401.08047</ee>
# <url>db/journals/corr/corr2401.html#abs-2401-08047</url>
# </article>'''
#                     }
#                 },
#                 note = openreview.api.Note(
#                     external_id = 'dblp:journals/corr/abs-2401-08047',
#                     content={
#                         'title': {
#                             'value': 'Incremental Extractive Opinion Summarization Using Cover Trees.',
#                         },
#                         'authors': {
#                             'value': ['Somnath Basu Roy Chowdhury', 'Nicholas Monath', 'Avinava Dubey', 'Manzil Zaheer', 'Andrew McCallum', 'Amr Ahmed', 'Snigdha Chaturvedi']
#                         },
#                         'venue': {
#                             'value': 'CoRR 2024',
#                         }
#                     }
#                 )
#             )

#         nick_client = helpers.create_user('nick@profile.org', 'Nicholas', 'Monath', alternates=[], institution='google.com')

#         edit = nick_client.post_note_edit(
#             invitation = 'openreview.net/Public_Article/DBLP.org/-/Record',
#             signatures = ['~Nicholas_Monath1'],
#             content = {
#                 'xml': {
#                     'value': '''<article key="journals/corr/abs-2401-08047" publtype="informal" mdate="2024-02-01">
# <author>Somnath Basu Roy Chowdhury</author>
# <author>Nicholas Monath</author>
# <author>Avinava Dubey</author>
# <author>Manzil Zaheer</author>
# <author>Andrew McCallum</author>
# <author>Amr Ahmed 0001</author>
# <author>Snigdha Chaturvedi</author>
# <title>Incremental Extractive Opinion Summarization Using Cover Trees.</title>
# <year>2024</year>
# <volume>abs/2401.08047</volume>
# <journal>CoRR</journal>
# <ee type="oa">https://doi.org/10.48550/arXiv.2401.08047</ee>
# <url>db/journals/corr/corr2401.html#abs-2401-08047</url>
# </article>'''
#                 }
#             },
#             note = openreview.api.Note(
#                 id = incremental_note.id,
#                 external_id = 'dblp:journals/corr/abs-2401-08047',
#                 content={
#                     'title': {
#                         'value': 'Incremental Extractive Opinion Summarization Using Cover Trees.',
#                     },
#                     'authors': {
#                         'value': ['Somnath Basu Roy Chowdhury', 'Nicholas Monath', 'Avinava Dubey', 'Manzil Zaheer', 'Andrew McCallum', 'Amr Ahmed', 'Snigdha Chaturvedi']
#                     },
#                     'venue': {
#                         'value': 'CoRR 2024',
#                     }
#                 }
#             )
#         )
#         helpers.await_queue_edit(openreview_client, edit_id=edit['id'], process_index=0)

#         helpers.await_queue_edit(openreview_client, edit_id=edit['id'], process_index=1, error=True)

#         incremental_note = andrew_client.get_note(edit['note']['id'])
#         assert incremental_note.external_ids == ['arxiv:2401.08047', 'dblp:journals/corr/abs-2401-08047']
#         assert '~Andrew_McCallum1' in incremental_note.content['authorids']['value']
#         assert '~Nicholas_Monath1' in incremental_note.content['authorids']['value']


#         edit = andrew_client.post_note_edit(
#             invitation = 'openreview.net/Public_Article/DBLP.org/-/Record',
#             signatures = ['~Andrew_McCallum1'],
#             content = {
#                 'xml': {
#                     'value': '''<article key="journals/corr/abs-2301-09809" publtype="informal" mdate="2023-02-02">
# <author>Subendhu Rongali</author>
# <author>Mukund Sridhar</author>
# <author>Haidar Khan</author>
# <author>Konstantine Arkoudas</author>
# <author>Wael Hamza</author>
# <author>Andrew McCallum</author>
# <title>Low-Resource Compositional Semantic Parsing with Concept Pretraining.</title>
# <year>2023</year>
# <volume>abs/2301.09809</volume>
# <journal>CoRR</journal>
# <ee type="oa">https://doi.org/10.48550/arXiv.2301.09809</ee>
# <url>db/journals/corr/corr2301.html#abs-2301-09809</url>
# </article>'''
#                 }
#             },
#             note = openreview.api.Note(
#                 external_id = 'dblp:journals/corr/abs-2301-09809',
#                 content={
#                     'title': {
#                         'value': 'Low-Resource Compositional Semantic Parsing with Concept Pretraining',
#                     },
#                     'authors': {
#                         'value': ['Subendhu Rongali', 'Mukund Sridhar', 'Haidar Khan', 'Konstantine Arkoudas', 'Wael Hamza', 'Andrew McCallum']
#                     },
#                     'venue': {
#                         'value': 'CoRR 2023',
#                     }
#                 }
#             )
#         )            

#         with pytest.raises(openreview.OpenReviewException, match=r'A public article from DBLP is already present.'):
#             edit = andrew_client.post_note_edit(
#                 invitation='openreview.net/Public_Article/arXiv.org/-/Record',
#                 signatures=['~Andrew_McCallum1'],
#                 note = openreview.api.Note(
#                     external_id = 'arxiv:2301.09809',
#                     pdate= openreview.tools.datetime_millis(datetime.datetime(2025, 2, 15)),
#                     mdate= openreview.tools.datetime_millis(datetime.datetime(2025, 2, 15)),
#                     content={
#                         'title': {
#                             'value': 'Low-Resource Compositional Semantic Parsing with Concept Pretraining'
#                         },
#                         'abstract': {
#                             'value': 'Semantic parsing plays a key role in digital voice assistants such as Alexa, Siri, and Google Assistant by mapping natural language to structured meaning representations. When we want to improve the capabilities of a voice assistant by adding a new domain, the underlying semantic parsing model needs to be retrained using thousands of annotated examples from the new domain, which is time-consuming and expensive. In this work, we present an architecture to perform such domain adaptation automatically, with only a small amount of metadata about the new domain and without any new training data (zero-shot) or with very few examples (few-shot). We use a base seq2seq (sequence-to-sequence) architecture and augment it with a concept encoder that encodes intent and slot tags from the new domain. We also introduce a novel decoder-focused approach to pretrain seq2seq models to be concept aware using Wikidata and use it to help our model learn important concepts and perform well in low-resource settings. We report few-shot and zero-shot results for compositional semantic parsing on the TOPv2 dataset and show that our model outperforms prior approaches in few-shot settings for the TOPv2 and SNIPS datasets.'
#                         },
#                         'authors': {
#                             'value': ['Subendhu Rongali', 'Mukund Sridhar', 'Haidar Khan', 'Konstantine Arkoudas', 'Wael Hamza', 'Andrew McCallum']
#                         },
#                         'subject_areas': {
#                             'value': ['cs.CL']
#                         },
#                         'pdf': {
#                             'value': 'https://arxiv.org/pdf/2301.09809.pdf'
#                         }
#                     }
#                 )
#             )                                         

    def test_import_orcid_notes(self, client, openreview_client, test_client, helpers):

        josiah_client = helpers.create_user('josiah@profile.org', 'Josiah', 'Couch')

        edit = josiah_client.post_note_edit(
            invitation = 'openreview.net/Public_Article/ORCID.org/-/Record',
            signatures = ['~Josiah_Couch1'],
            content = {
                'json': {
                    'value': {
      "created-date" : {
        "value" : 1708964039610
      },
      "last-modified-date" : {
        "value" : 1708964039610
      },
      "source" : {
        "source-orcid" : None,
        "source-client-id" : {
          "uri" : "https://orcid.org/client/0000-0001-8607-8906",
          "path" : "0000-0001-8607-8906",
          "host" : "orcid.org"
        },
        "source-name" : {
          "value" : "INSPIRE-HEP"
        },
        "assertion-origin-orcid" : None,
        "assertion-origin-client-id" : None,
        "assertion-origin-name" : None
      },
      "put-code" : 154061860,
      "path" : "/0000-0002-7416-5858/work/154061860",
      "title" : {
        "title" : {
          "value" : "Possibility of entanglement of purification to be less than half of the reflected entropy"
        },
        "subtitle" : None,
        "translated-title" : None
      },
      "journal-title" : {
        "value" : "Phys.Rev.A"
      },
      "short-description" : None,
      "citation" : {
        "citation-type" : "bibtex",
        "citation-value" : "@article{Couch:2023pav,\n    author = \"Couch, Josiah and Nguyen, Phuc and Racz, Sarah and Stratis, Georgios and Zhang, Yuxuan\",\n    title = \"{Possibility of entanglement of purification to be less than half of the reflected entropy}\",\n    eprint = \"2309.02506\",\n    archivePrefix = \"arXiv\",\n    primaryClass = \"quant-ph\",\n    doi = \"10.1103/PhysRevA.109.022426\",\n    journal = \"Phys. Rev. A\",\n    volume = \"109\",\n    number = \"2\",\n    pages = \"022426\",\n    year = \"2024\"\n}\n"
      },
      "type" : "journal-article",
      "publication-date" : {
        "year" : {
          "value" : "2024"
        },
        "month" : {
          "value" : "02"
        },
        "day" : {
          "value" : "20"
        }
      },
      "external-ids" : {
        "external-id" : [ {
          "external-id-type" : "other-id",
          "external-id-value" : "2760289",
          "external-id-normalized" : {
            "value" : "2760289",
            "transient" : True
          },
          "external-id-normalized-error" : None,
          "external-id-url" : {
            "value" : "http://inspirehep.net/record/2760289"
          },
          "external-id-relationship" : "self"
        }, {
          "external-id-type" : "doi",
          "external-id-value" : "10.1103/PhysRevA.109.022426",
          "external-id-normalized" : {
            "value" : "10.1103/physreva.109.022426",
            "transient" : True
          },
          "external-id-normalized-error" : None,
          "external-id-url" : {
            "value" : "http://dx.doi.org/10.1103/PhysRevA.109.022426"
          },
          "external-id-relationship" : "self"
        }, {
          "external-id-type" : "arxiv",
          "external-id-value" : "2309.02506",
          "external-id-normalized" : {
            "value" : "arXiv:2309.02506",
            "transient" : True
          },
          "external-id-normalized-error" : None,
          "external-id-url" : {
            "value" : "http://arxiv.org/abs/2309.02506"
          },
          "external-id-relationship" : "self"
        } ]
      },
      "url" : {
        "value" : "http://inspirehep.net/record/2760289"
      },
      "contributors" : {
        "contributor" : [ {
          "contributor-orcid" : {
            "uri" : "http://orcid.org/0000-0002-7416-5858",
            "path" : "0000-0002-7416-5858",
            "host" : "orcid.org"
          },
          "credit-name" : {
            "value" : "Couch, Josiah"
          },
          "contributor-email" : None,
          "contributor-attributes" : {
            "contributor-sequence" : "first",
            "contributor-role" : "author"
          }
        }, {
          "contributor-orcid" : None,
          "credit-name" : {
            "value" : "Nguyen, Phuc"
          },
          "contributor-email" : None,
          "contributor-attributes" : {
            "contributor-sequence" : "additional",
            "contributor-role" : "author"
          }
        }, {
          "contributor-orcid" : None,
          "credit-name" : {
            "value" : "Racz, Sarah"
          },
          "contributor-email" : None,
          "contributor-attributes" : {
            "contributor-sequence" : "additional",
            "contributor-role" : "author"
          }
        }, {
          "contributor-orcid" : {
            "uri" : "http://orcid.org/0000-0002-1346-8417",
            "path" : "0000-0002-1346-8417",
            "host" : "orcid.org"
          },
          "credit-name" : {
            "value" : "Stratis, Georgios"
          },
          "contributor-email" : None,
          "contributor-attributes" : {
            "contributor-sequence" : "additional",
            "contributor-role" : "author"
          }
        }, {
          "contributor-orcid" : {
            "uri" : "http://orcid.org/0000-0001-5477-8924",
            "path" : "0000-0001-5477-8924",
            "host" : "orcid.org"
          },
          "credit-name" : {
            "value" : "Zhang, Yuxuan"
          },
          "contributor-email" : None,
          "contributor-attributes" : {
            "contributor-sequence" : "additional",
            "contributor-role" : "author"
          }
        } ]
      },
      "language-code" : None,
      "country" : None,
      "visibility" : "public"
    }
             }
            },
            note = openreview.api.Note(
                external_id = 'doi:10.1103/PhysRevA.109.022426',
                content={
                    'title': {
                        'value': 'Possibility of entanglement of purification to be less than half of the reflected entropy',
                    },
                    'authors': {
                        'value': ['Josiah Couch', 'Nguyen, Phuc', 'Racz, Sarah', 'Stratis, Georgios', 'Zhang, Yuxuan'],
                    },
                    'venue': {
                        'value': 'Phys.Rev.A',
                    }
                }
            )
        )

        helpers.await_queue_edit(openreview_client, edit_id=edit['id'], process_index=0)
        helpers.await_queue_edit(openreview_client, edit_id=edit['id'], process_index=1, error=True)

        note = josiah_client.get_note(edit['note']['id'])
        assert note.external_ids == ['doi:10.1103/PhysRevA.109.022426']
        assert 'http://orcid.org/0000-0002-7416-5858' == note.content['authorids']['value'][0]


        with pytest.raises(openreview.OpenReviewException, match=r'The author name Couch Josiah from index 0 doesn\'t match with the names listed in your profile'):
            edit = josiah_client.post_note_edit(
                invitation = 'openreview.net/Public_Article/-/Authorship_Claim',
                signatures = ['~Josiah_Couch1'],
                content = {
                    'author_index': { 'value': 0 },
                    'author_id': { 'value': '~Josiah_Couch1' },
                },                
                note = openreview.api.Note(
                    id = note.id
                )
            )

        profile = josiah_client.get_profile()

        profile.content['homepage'] = 'https://josiah.google.com'
        profile.content['names'].append({
            'fullname': 'Couch Josiah',
            })
        josiah_client.post_profile(profile)     

        edit = josiah_client.post_note_edit(
            invitation = 'openreview.net/Public_Article/-/Authorship_Claim',
            signatures = ['~Josiah_Couch1'],
            content = {
                'author_index': { 'value': 0 },
                'author_id': { 'value': '~Josiah_Couch1' },
            },                
            note = openreview.api.Note(
                id = note.id
            )
        )           

        note = josiah_client.get_note(edit['note']['id'])
        assert note.external_ids == ['doi:10.1103/PhysRevA.109.022426']
        assert '~Josiah_Couch1' == note.content['authorids']['value'][0]


    def test_remove_alternate_name(self, openreview_client, test_client, helpers):

        john_client = helpers.create_user('john@profile.org', 'John', 'Last', alternates=[], institution='google.com')

        profile = john_client.get_profile()

        profile.content['homepage'] = 'https://john.google.com'
        profile.content['names'].append({
            'first': 'John',
            'middle': 'Alternate',
            'last': 'Last'
            })
        profile.content['relations'].append({
            'relation': 'Advisor',
            'name': 'SomeFirstName User',
            'username': '~SomeFirstName_User1',
            'start': 2015,
            'end': None
        })
        john_client.post_profile(profile)


        profile = john_client.get_profile(email_or_id='~John_Last1')
        assert len(profile.content['names']) == 2
        assert 'username' in profile.content['names'][1]
        assert profile.content['names'][1]['username'] == '~John_Alternate_Last1'
        assert profile.content['relations'][0]['username'] == '~SomeFirstName_User1'
        
        assert openreview_client.get_group('~John_Last1').members == ['john@profile.org']
        assert openreview_client.get_group('john@profile.org').members == ['~John_Last1', '~John_Alternate_Last1']
        assert openreview_client.get_group('~John_Alternate_Last1').members == ['john@profile.org']

        ## Try to remove the unexisting name and get an error
        with pytest.raises(openreview.OpenReviewException, match=r'Profile not found for ~John_Lasst1'):
            request_note = john_client.post_note_edit(
                invitation='openreview.net/Support/-/Profile_Name_Removal',
                signatures=['~John_Last1'],
                note = openreview.api.Note(
                    content={
                        'name': { 'value': 'John Last' },
                        'usernames': { 'value': ['~John_Lasst1'] },
                        'comment': { 'value': 'typo in my name' }
                    }
                )
            )

        ## Try to remove the name that is marked as preferred and get an error
        with pytest.raises(openreview.OpenReviewException, match=r'Can not remove preferred name'):
            request_note = john_client.post_note_edit(
                invitation='openreview.net/Support/-/Profile_Name_Removal',
                signatures=['~John_Last1'],
                note = openreview.api.Note(
                    content={
                        'name': { 'value': 'John Last' },
                        'usernames': { 'value': ['~John_Last1'] },
                        'comment': { 'value': 'typo in my name' }
                    }
                )
            )

        ## Try to remove the name that doesn't match with the username and get an error
        with pytest.raises(openreview.OpenReviewException, match=r'Name does not match with username'):
            request_note = john_client.post_note_edit(
                invitation='openreview.net/Support/-/Profile_Name_Removal',
                signatures=['~John_Last1'],
                note = openreview.api.Note(
                    content={
                        'name': { 'value': 'Melisa Bok' },
                        'usernames': { 'value': ['~John_Alternate_Last1'] },
                        'comment': { 'value': 'typo in my name' }
                    }
                )
            )
                    
        ## Add publications
        edit = john_client.post_note_edit(
            invitation='openreview.net/Archive/-/Direct_Upload',
            signatures=['~John_Alternate_Last1'],
            note = openreview.api.Note(
                pdate = openreview.tools.datetime_millis(datetime.datetime(2019, 4, 30)),
                content = {
                    'title': { 'value': 'Paper title 1' },
                    'abstract': { 'value': 'Paper abstract 1' },
                    'authors': { 'value': ['John Alternate Last', 'Test Client'] },
                    'authorids': { 'value': ['~John_Alternate_Last1', 'test@mail.com'] },
                    'venue': { 'value': 'Arxiv' },
                    'html': { 'value': 'https://arxiv.org/abs/test' }
                },
                license = 'CC BY-SA 4.0'
        ))
        note_number = edit['note']['number']

        ## Enable comment invitation
        openreview_client.post_invitation_edit(
            invitations='openreview.net/Archive/-/Comment',
            signatures=['openreview.net/Archive'],
            content={
                'noteNumber': { 'value': 1 },
                'noteId': { 'value': edit['note']['id'] }
            }
        )

        assert openreview_client.get_invitation('openreview.net/Archive/Submission1/-/Comment')


        edit = john_client.post_note_edit(
            invitation='openreview.net/Archive/Submission1/-/Comment',
            signatures=['~John_Alternate_Last1'],
            note = openreview.api.Note(
                replyto = edit['note']['id'],
                content = {
                    'comment': { 'value': 'more details about our submission' },
                }   
            )                         
        )

        helpers.await_queue_edit(openreview_client, edit_id=edit['id'])

        messages = openreview_client.get_messages(to='test@mail.com', subject='[OpenReview Archive] John Alternate Last commented on your submission. Paper Title: "Paper title 1"')
        assert len(messages) == 1
        assert messages[0]['content']['text'] == f'''John Alternate Last commented on your submission.\n    \nPaper number: {note_number}\n\nPaper title: Paper title 1\n\nComment: more details about our submission\n\nTo view the comment, click here: https://openreview.net/forum?id={edit['note']['forum']}&noteId={edit['note']['id']}'''        

        ## Add a subscribe tag
        dblp_notes = openreview_client.get_notes(invitation='openreview.net/Public_Article/DBLP.org/-/Record', sort='number:asc')
        assert len(dblp_notes) == 2

        john_client.post_note_edit(
            invitation='openreview.net/Archive/-/Direct_Upload',
            signatures=['~John_Alternate_Last1'],
            note = openreview.api.Note(
                pdate = openreview.tools.datetime_millis(datetime.datetime(2019, 4, 30)),
                content = {
                    'title': { 'value': 'Paper title 2' },
                    'abstract': { 'value': 'Paper abstract 2' },
                    'authors': { 'value': ['John Alternate Last', 'Test Client'] },
                    'authorids': { 'value': ['~John_Alternate_Last1', 'test@mail.com', 'another@mail.com'] },
                    'venue': { 'value': 'Arxiv' }
                },
                license = 'CC BY-SA 4.0'
        )) 

        ## Create committee groups
        openreview_client.post_group_edit(
            invitation = 'openreview.net/-/Edit',
            signatures=['~Super_User1'],
            group  = openreview.api.Group(
                id='ICLRR.cc',
                readers=['everyone'],
                writers=['ICLRR.cc'],
                signatories=[],
                members=[],
                signatures=['~Super_User1']
            )
        )

        openreview_client.post_group_edit(
            invitation = 'openreview.net/-/Edit',
            signatures=['~Super_User1'],
            group  = openreview.api.Group(
                id='ICLRR.cc/Reviewers',
                readers=['everyone'],
                writers=['ICLRR.cc'],
                signatories=[],
                members=['~John_Alternate_Last1'],
                signatures=['~Super_User1'],
                anonids=True
            )
        )        

        anon_groups = openreview_client.get_groups(prefix='ICLRR.cc/Reviewer_')
        assert len(anon_groups) == 1
        assert '~John_Alternate_Last1' in anon_groups[0].members
        first_anon_group_id = anon_groups[0].id                

        publications = john_client.get_notes(content={ 'authorids': '~John_Last1'})
        assert len(publications) == 2



        request_note = john_client.post_note_edit(
            invitation='openreview.net/Support/-/Profile_Name_Removal',
            signatures=['~John_Last1'],
            note = openreview.api.Note(
                content={
                    'name': { 'value': 'John Alternate Last' },
                    'usernames': { 'value': ['~John_Alternate_Last1'] },
                    'comment': { 'value': 'typo in my name' }
                }
            )
        )        

        helpers.await_queue_edit(openreview_client, edit_id=request_note['id'])

        messages = openreview_client.get_messages(to='john@profile.org', subject='Profile name removal request has been received')
        assert len(messages) == 1
        assert messages[0]['content']['text'] == '''Hi John Last,

We have received your request to remove the name "John Alternate Last" from your profile: https://openreview.net/profile?id=~John_Last1.

We will evaluate your request and you will receive another email with the request status.

Thanks,

The OpenReview Team.
'''

        ## Accept the request
        decision_note = openreview_client.post_note_edit(
            invitation='openreview.net/Support/-/Profile_Name_Removal_Decision',
            signatures=['openreview.net/Support'],
            note = openreview.api.Note(
                id = request_note['note']['id'],
                content={
                    'status': { 'value': 'Accepted' }
                }
            )
        )

        helpers.await_queue_edit(openreview_client, decision_note['id'])

        note = john_client.get_note(request_note['note']['id'])
        assert note.content['status']['value'] == 'Accepted'

        publications = john_client.get_notes(content={ 'authorids': '~John_Last1'})
        assert len(publications) == 2
        assert '~John_Last1' in publications[0].writers
        assert '~John_Last1' in publications[0].signatures
        assert ['John Last', 'Test Client'] == publications[0].content['authors']['value']
        assert ['~John_Last1', 'test@mail.com', 'another@mail.com'] == publications[0].content['authorids']['value']
        assert '~John_Last1' in publications[1].writers
        assert '~John_Last1' in publications[1].signatures

        group = openreview_client.get_group('ICLRR.cc/Reviewers')
        assert '~John_Alternate_Last1' not in group.members
        assert '~John_Last1' in group.members

        anon_groups = openreview_client.get_groups(prefix='ICLRR.cc/Reviewer_')
        assert len(anon_groups) == 1
        assert '~John_Alternate_Last1' not in anon_groups[0].members
        assert '~John_Last1' in anon_groups[0].members
        assert anon_groups[0].id == first_anon_group_id

        profile = john_client.get_profile(email_or_id='~John_Last1')
        assert len(profile.content['names']) == 1
        assert 'username' in profile.content['names'][0]
        assert profile.content['names'][0]['username'] == '~John_Last1'

        found_profiles = openreview_client.search_profiles(fullname='John Last', use_ES=True)
        assert len(found_profiles) == 1
        assert len(found_profiles[0].content['names']) == 1
        assert 'username' in found_profiles[0].content['names'][0]
        assert found_profiles[0].content['names'][0]['username'] == '~John_Last1'        

        with pytest.raises(openreview.OpenReviewException, match=r'Group Not Found: ~John_Alternate_Last1'):
            openreview_client.get_group('~John_Alternate_Last1')

        assert openreview_client.get_group('~John_Last1').members == ['john@profile.org']
        assert openreview_client.get_group('john@profile.org').members == ['~John_Last1']

        messages = openreview_client.get_messages(to='john@profile.org', subject='Profile name removal request has been accepted')
        assert len(messages) == 1
        assert messages[0]['content']['text'] == '''Hi John Last,

We have received your request to remove the name "John Alternate Last" from your profile: https://openreview.net/profile?id=~John_Last1.

The name has been removed from your profile. Please check that the information listed in your profile is correct.

Thanks,

The OpenReview Team.
'''


        ##Make another profile with the same name:
        john_two_client = helpers.create_user('john2@profile.org', 'John', 'Last', alternates=[], institution='google.com')

        profile = john_two_client.get_profile()

        profile.content['homepage'] = 'https://john.google.com'
        profile.content['names'].append({
            'first': 'John',
            'middle': 'Alternate',
            'last': 'Last'
            })
        profile.content['relations'].append({
            'relation': 'Advisor',
            'name': 'SomeFirstName User',
            'username': '~SomeFirstName_User1',
            'start': 2015,
            'end': None
        })
        john_two_client.post_profile(profile)



        #Try to automatically remove a name with different spacing/capitalization
        profile=john_two_client.get_profile()
        profile.content['names'].append(
            {'fullname':'johnlast'}
            )
        john_two_client.post_profile(profile)


        ## add a publication
        john_two_client.post_note_edit(
            invitation='openreview.net/Archive/-/Direct_Upload',
            signatures=['~johnlast1'],
            note = openreview.api.Note(
                pdate = openreview.tools.datetime_millis(datetime.datetime(2019, 4, 30)),
                content = {
                    'title': { 'value': 'Paper title 2' },
                    'abstract': { 'value': 'Paper abstract 2' },
                    'authors': { 'value': ['John Last'] },
                    'authorids': { 'value': ['~johnlast1'] },
                    'venue': { 'value': 'Arxiv' }
                },
                license = 'CC BY-SA 4.0'
        )) 
        profile=john_two_client.get_profile('~John_Last2')

        request_note = john_two_client.post_note_edit(
            invitation='openreview.net/Support/-/Profile_Name_Removal',
            signatures=['~John_Last2'],
            note = openreview.api.Note(
                content={
                    'name': { 'value': 'johnlast' },
                    'usernames': { 'value': ['~johnlast1'] },
                    'comment': { 'value': 'add space' }
                }
            )
        )        
        helpers.await_queue_edit(openreview_client, edit_id=request_note['id'])

        time.sleep(5)

        note = john_two_client.get_note(request_note['note']['id'])
        assert note.content['status']['value'] == 'Accepted'

        #Try to automatically automatically remove a reversed name 
        profile = john_two_client.get_profile('~John_Last2')
        profile.content['names'].append(
            {'first':'Last',
             'last': 'John'}
            )
        john_two_client.post_profile(profile)

        ## add a publication
        john_two_client.post_note_edit(
            invitation='openreview.net/Archive/-/Direct_Upload',
            signatures=['~Last_John1'],
            note = openreview.api.Note(
                pdate = openreview.tools.datetime_millis(datetime.datetime(2019, 4, 30)),
                content = {
                    'title': { 'value': 'Paper title 2' },
                    'abstract': { 'value': 'Paper abstract 2' },
                    'authors': { 'value': ['Last John'] },
                    'authorids': { 'value': ['~Last_John1'] },
                    'venue': { 'value': 'Arxiv' }
                },
                license = 'CC BY-SA 4.0'
        )) 
        profile=john_two_client.get_profile('~John_Last2')

        request_note = john_two_client.post_note_edit(
            invitation='openreview.net/Support/-/Profile_Name_Removal',
            signatures=['~John_Last2'],
            note = openreview.api.Note(
                content={
                    'name': { 'value': 'Last John' },
                    'usernames': { 'value': ['~Last_John1'] },
                    'comment': { 'value': 'add space' }
                }
            )
        )        
        helpers.await_queue_edit(openreview_client, edit_id=request_note['id'])

        note = john_two_client.get_note(request_note['note']['id'])
        assert note.content['status']['value'] == 'Accepted'


    def test_remove_name_and_rename_profile_id(self, client, openreview_client, helpers):

        ana_client = helpers.create_user('ana@profile.org', 'Ana', 'Last', alternates=[], institution='google.com')

        openreview_client.post_tag(
            openreview.api.Tag(
                invitation='openreview.net/Support/-/Profile_Moderation_Label',
                signature='openreview.net/Support',
                profile='~Ana_Last1',
                label='test label',
            )
        )

        tags = openreview_client.get_tags(invitation='openreview.net/Support/-/Profile_Moderation_Label', profile='~Ana_Last1')
        assert len(tags) == 1
    
        profile = ana_client.get_profile()

        profile.content['homepage'] = 'https://ana.google.com'
        profile.content['names'].append({
            'first': 'Ana',
            'middle': 'Alternate',
            'last': 'Last',
            'preferred': True
            })
        ana_client.post_profile(profile)
        profile = ana_client.get_profile(email_or_id='~Ana_Last1')
        assert len(profile.content['names']) == 2
        assert 'username' in profile.content['names'][1]
        assert profile.content['names'][1]['username'] == '~Ana_Alternate_Last1'
        assert profile.content['names'][1]['preferred'] == True
        assert profile.content['names'][0]['preferred'] == False

        assert openreview_client.get_group('~Ana_Last1').members == ['ana@profile.org']
        assert openreview_client.get_group('ana@profile.org').members == ['~Ana_Last1', '~Ana_Alternate_Last1']
        assert openreview_client.get_group('~Ana_Alternate_Last1').members == ['ana@profile.org']        

        ## Try to remove the name that is marked as preferred an get an error
        with pytest.raises(openreview.OpenReviewException, match=r'Can not remove preferred name'):
            request_note = ana_client.post_note_edit(
                invitation='openreview.net/Support/-/Profile_Name_Removal',
                signatures=['~Ana_Alternate_Last1'],
                note = openreview.api.Note(
                    content={
                        'name': { 'value': 'Ana Alternate Last' },
                        'usernames': { 'value': ['~Ana_Alternate_Last1'] },
                        'comment': { 'value': 'typo in my name' }
                    }
                )
            )                    


        ## Add publications
        ana_client.post_note_edit(
            invitation='openreview.net/Archive/-/Direct_Upload',
            signatures=['~Ana_Last1'],
            note = openreview.api.Note(
                pdate = openreview.tools.datetime_millis(datetime.datetime(2019, 4, 30)),
                content = {
                    'title': { 'value': 'Paper title 1' },
                    'abstract': { 'value': 'Paper abstract 1' },
                    'authors': { 'value': ['Ana Last', 'Test Client'] },
                    'authorids': { 'value': ['~Ana_Last1', 'test@mail.com'] },
                    'venue': { 'value': 'Arxiv' }
                },
                license = 'CC BY-SA 4.0'
        ))        

        ana_client.post_note_edit(
            invitation='openreview.net/Archive/-/Direct_Upload',
            signatures=['~Ana_Last1'],
            note = openreview.api.Note(
                pdate = openreview.tools.datetime_millis(datetime.datetime(2019, 4, 30)),
                content = {
                    'title': { 'value': 'Paper title 2' },
                    'abstract': { 'value': 'Paper abstract 2' },
                    'authors': { 'value': ['Ana Last', 'Test Client'] },
                    'authorids': { 'value': ['~Ana_Last1', 'test@mail.com'] },
                    'venue': { 'value': 'Arxiv' }
                },
                license = 'CC BY-SA 4.0'
        ))        

        publications = openreview_client.get_notes(content={ 'authorids': '~Ana_Alternate_Last1'})
        assert len(publications) == 2

        request_note = ana_client.post_note_edit(
            invitation='openreview.net/Support/-/Profile_Name_Removal',
            signatures=['~Ana_Alternate_Last1'],
            note = openreview.api.Note(
                content={
                    'name': { 'value': 'Ana Last' },
                    'usernames': { 'value': ['~Ana_Last1'] },
                    'comment': { 'value': 'typo in my name' }
                }
            )
        )

        helpers.await_queue_edit(openreview_client, request_note['id'])

        messages = openreview_client.get_messages(to='ana@profile.org', subject='Profile name removal request has been received')
        assert len(messages) == 1
        assert messages[0]['content']['text'] == '''Hi Ana Alternate Last,

We have received your request to remove the name "Ana Last" from your profile: https://openreview.net/profile?id=~Ana_Alternate_Last1.

We will evaluate your request and you will receive another email with the request status.

Thanks,

The OpenReview Team.
'''

        ## Accept the request
        decision_note = openreview_client.post_note_edit(
            invitation='openreview.net/Support/-/Profile_Name_Removal_Decision',
            signatures=['openreview.net/Support'],
            note = openreview.api.Note(
                id = request_note['note']['id'],
                content={
                    'status': { 'value': 'Accepted' }
                }
            )
        )

        helpers.await_queue_edit(openreview_client, decision_note['id'])

        ana_client = openreview.api.OpenReviewClient(username='ana@profile.org', password=helpers.strong_password)
        note = ana_client.get_note(request_note['note']['id'])
        assert note.content['status']['value'] == 'Accepted'

        tags = openreview_client.get_tags(invitation='openreview.net/Support/-/Profile_Moderation_Label', profile='~Ana_Alternate_Last1')
        assert len(tags) == 1        

        publications = openreview_client.get_notes(content={ 'authorids': '~Ana_Alternate_Last1'})
        assert len(publications) == 2
        assert '~Ana_Alternate_Last1' in publications[0].writers
        assert '~Ana_Alternate_Last1' in publications[0].signatures
        assert '~Ana_Alternate_Last1' in publications[1].writers
        assert '~Ana_Alternate_Last1' in publications[1].signatures


        profile = ana_client.get_profile(email_or_id='~Ana_Alternate_Last1')
        assert len(profile.content['names']) == 1
        assert 'username' in profile.content['names'][0]
        assert profile.content['names'][0]['username'] == '~Ana_Alternate_Last1'

        found_profiles = openreview_client.search_profiles(fullname='Ana Last', use_ES=True)
        assert len(found_profiles) == 1
        assert len(found_profiles[0].content['names']) == 1
        assert 'username' in found_profiles[0].content['names'][0]
        assert found_profiles[0].content['names'][0]['username'] == '~Ana_Alternate_Last1'        

        with pytest.raises(openreview.OpenReviewException, match=r'Group Not Found: ~Ana_Last1'):
            openreview_client.get_group('~Ana_Last1')

        assert openreview_client.get_group('ana@profile.org').members == ['~Ana_Alternate_Last1']
        assert openreview_client.get_group('~Ana_Alternate_Last1').members == ['ana@profile.org']              

        messages = openreview_client.get_messages(to='ana@profile.org', subject='Profile name removal request has been accepted')
        assert len(messages) == 1
        assert messages[0]['content']['text'] == '''Hi Ana Alternate Last,

We have received your request to remove the name "Ana Last" from your profile: https://openreview.net/profile?id=~Ana_Alternate_Last1.

The name has been removed from your profile. Please check that the information listed in your profile is correct.

Thanks,

The OpenReview Team.
'''

    def test_request_remove_name_and_decline(self, openreview_client, helpers):

        peter_client = helpers.create_user('peter@profile.org', 'Peter', 'Last', alternates=[], institution='google.com')

        profile = peter_client.get_profile()

        profile.content['homepage'] = 'https://peter.google.com'
        profile.content['names'].append({
            'first': 'Peter',
            'middle': 'Alternate',
            'last': 'Last'
            })
        peter_client.post_profile(profile)
        profile = peter_client.get_profile(email_or_id='~Peter_Last1')
        assert len(profile.content['names']) == 2
        assert 'username' in profile.content['names'][1]
        assert profile.content['names'][1]['username'] == '~Peter_Alternate_Last1'
        assert profile.content['names'][1]['preferred'] == False
        assert profile.content['names'][0]['preferred'] == True

        peter_client.post_note_edit(
            invitation='openreview.net/Archive/-/Direct_Upload',
            signatures=['~Peter_Alternate_Last1'],
            note = openreview.api.Note(
                pdate = openreview.tools.datetime_millis(datetime.datetime(2019, 4, 30)),
                content = {
                    'title': { 'value': 'Paper title 1' },
                    'abstract': { 'value': 'Paper abstract 1' },
                    'authors': { 'value': ['Peter Alternate Last', 'Test Client'] },
                    'authorids': { 'value': ['~Peter_Alternate_Last1', 'test@mail.com'] },
                    'venue': { 'value': 'Arxiv' }
                },
                license = 'CC BY-SA 4.0'
        ))                      

        request_note = peter_client.post_note_edit(
            invitation='openreview.net/Support/-/Profile_Name_Removal',
            signatures=['~Peter_Last1'],
            note = openreview.api.Note(
                content={
                    'name': { 'value': 'Peter Alternate Last' },
                    'usernames': { 'value': ['~Peter_Alternate_Last1'] },
                    'comment': { 'value': 'typo in my name' }
                }
            )
        )

        helpers.await_queue_edit(openreview_client, request_note['id'])        

        messages = openreview_client.get_messages(to='peter@profile.org', subject='Profile name removal request has been received')
        assert len(messages) == 1
        assert messages[0]['content']['text'] == '''Hi Peter Last,

We have received your request to remove the name "Peter Alternate Last" from your profile: https://openreview.net/profile?id=~Peter_Last1.

We will evaluate your request and you will receive another email with the request status.

Thanks,

The OpenReview Team.
'''

        ## Decline the request
        decision_note = openreview_client.post_note_edit(
            invitation='openreview.net/Support/-/Profile_Name_Removal_Decision',
            signatures=['openreview.net/Support'],
            note = openreview.api.Note(
                id = request_note['note']['id'],
                content={
                    'status': { 'value': 'Rejected' },
                    'support_comment': { 'value': 'Name the is left is not descriptive' }
                }
            )
        )

        helpers.await_queue_edit(openreview_client, decision_note['id'])

        note = peter_client.get_note(request_note['note']['id'])
        assert note.content['status']['value'] == 'Rejected'

        messages = openreview_client.get_messages(to='peter@profile.org', subject='Profile name removal request has been rejected')
        assert len(messages) == 1
        assert messages[0]['content']['text'] == '''Hi Peter Last,

We have received your request to remove the name "Peter Alternate Last" from your profile: https://openreview.net/profile?id=~Peter_Last1.

We can not remove the name from the profile for the following reason:

Name the is left is not descriptive

Regards,

The OpenReview Team.
'''

    def test_remove_name_from_merged_profile(self, openreview_client, helpers):

        ella_client = helpers.create_user('ella@profile.org', 'Ella', 'Last', alternates=[], institution='google.com')

        profile = ella_client.get_profile()

        profile.content['homepage'] = 'https://ella.google.com'
        profile.content['names'].append({
            'first': 'Ella',
            'middle': 'Alternate',
            'last': 'Last'
            })
        ella_client.post_profile(profile)
        profile = ella_client.get_profile(email_or_id='~Ella_Last1')
        assert len(profile.content['names']) == 2
        assert 'username' in profile.content['names'][1]
        assert profile.content['names'][1]['username'] == '~Ella_Alternate_Last1'

        assert openreview_client.get_group('~Ella_Last1').members == ['ella@profile.org']
        assert openreview_client.get_group('ella@profile.org').members == ['~Ella_Last1', '~Ella_Alternate_Last1']
        assert openreview_client.get_group('~Ella_Alternate_Last1').members == ['ella@profile.org']        

        ## Add publications
        ella_client.post_note_edit(
            invitation='openreview.net/Archive/-/Direct_Upload',
            signatures=['~Ella_Last1'],
            note = openreview.api.Note(
                pdate = openreview.tools.datetime_millis(datetime.datetime(2019, 4, 30)),
                content = {
                    'title': { 'value': 'Paper title 2' },
                    'abstract': { 'value': 'Paper abstract 2' },
                    'authors': { 'value': ['Ella Last', 'Test Client'] },
                    'authorids': { 'value': ['~Ella_Last1', 'test@mail.com'] },
                    'venue': { 'value': 'Arxiv' }
                },
                license = 'CC BY-SA 4.0'
        ))         

        publications = openreview_client.get_notes(content={ 'authorids': '~Ella_Last1'})
        assert len(publications) == 1


        ella_client_2 = helpers.create_user('ella_two@profile.org', 'Ela', 'Last', alternates=[], institution='deepmind.com')

        profile = ella_client_2.get_profile()
        assert '~Ela_Last1' == profile.id

        assert openreview_client.get_group('~Ela_Last1').members == ['ella_two@profile.org']
        assert openreview_client.get_group('ella_two@profile.org').members == ['~Ela_Last1']

        ella_client_2.post_note_edit(
            invitation='openreview.net/Archive/-/Direct_Upload',
            signatures=['~Ela_Last1'],
            note = openreview.api.Note(
                pdate = openreview.tools.datetime_millis(datetime.datetime(2019, 4, 30)),
                content = {
                    'title': { 'value': 'Paper title 2' },
                    'abstract': { 'value': 'Paper abstract 2' },
                    'authors': { 'value': ['Ela Last', 'Test Client'] },
                    'authorids': { 'value': ['~Ela_Last1', 'test@mail.com'] },
                    'venue': { 'value': 'Arxiv' }
                },
                license = 'CC BY-SA 4.0'
        ))

        publications = openreview_client.get_notes(content={ 'authorids': '~Ela_Last1'})
        assert len(publications) == 1


        openreview_client.merge_profiles('~Ella_Last1', '~Ela_Last1')
        profile = ella_client.get_profile()
        assert len(profile.content['names']) == 3
        profile.content['names'][0]['username'] == '~Ella_Last1'
        profile.content['names'][0]['preferred'] == True
        profile.content['names'][1]['username'] == '~Ella_Alternate_Last1'
        profile.content['names'][2]['username'] == '~Ela_Last1'

        found_profiles = openreview_client.search_profiles(fullname='Ella Last', use_ES=True)
        assert len(found_profiles) == 1
        assert len(found_profiles[0].content['names']) == 3

        assert openreview_client.get_group('~Ella_Last1').members == ['ella@profile.org', 'ella_two@profile.org']
        assert openreview_client.get_group('~Ela_Last1').members == ['ella_two@profile.org']
        assert openreview_client.get_group('ella@profile.org').members == ['~Ella_Last1', '~Ella_Alternate_Last1']
        assert openreview_client.get_group('ella_two@profile.org').members == ['~Ela_Last1', '~Ella_Last1']
        assert openreview_client.get_group('~Ella_Alternate_Last1').members == ['ella@profile.org']             
 
        request_note = ella_client.post_note_edit(
            invitation='openreview.net/Support/-/Profile_Name_Removal',
            signatures=['~Ella_Last1'],
            note = openreview.api.Note(
                content={
                    'name': { 'value': 'Ela Last' },
                    'usernames': { 'value': ['~Ela_Last1'] },
                    'comment': { 'value': 'typo in my name' }
                }
            )
        )

        helpers.await_queue_edit(openreview_client, request_note['id'])        

        messages = openreview_client.get_messages(to='ella@profile.org', subject='Profile name removal request has been received')
        assert len(messages) == 1
        assert messages[0]['content']['text'] == '''Hi Ella Last,

We have received your request to remove the name "Ela Last" from your profile: https://openreview.net/profile?id=~Ella_Last1.

We will evaluate your request and you will receive another email with the request status.

Thanks,

The OpenReview Team.
'''

        ## Accept the request
        decision_note = openreview_client.post_note_edit(
            invitation='openreview.net/Support/-/Profile_Name_Removal_Decision',
            signatures=['openreview.net/Support'],
            note = openreview.api.Note(
                id = request_note['note']['id'],
                content={
                    'status': { 'value': 'Accepted' }
                }
            )
        )

        helpers.await_queue_edit(openreview_client, decision_note['id'])

        note = ella_client.get_note(request_note['note']['id'])
        assert note.content['status']['value'] == 'Accepted'

        publications = openreview_client.get_notes(content={ 'authorids': '~Ella_Last1'})
        assert len(publications) == 2
        assert '~Ella_Last1' in publications[0].writers
        assert '~Ella_Last1' in publications[0].signatures
        assert '~Ella_Last1' in publications[1].writers
        assert '~Ella_Last1' in publications[1].signatures


        profile = ella_client.get_profile(email_or_id='~Ella_Last1')
        assert len(profile.content['names']) == 2
        assert 'username' in profile.content['names'][0]
        assert profile.content['names'][0]['username'] == '~Ella_Last1'
        assert profile.content['names'][1]['username'] == '~Ella_Alternate_Last1'

        found_profiles = openreview_client.search_profiles(fullname='Ella Alternate', use_ES=True)
        assert len(found_profiles) == 1
        assert len(found_profiles[0].content['names']) == 2        

        with pytest.raises(openreview.OpenReviewException, match=r'Group Not Found: ~Ela_Last1'):
            openreview_client.get_group('~Ela_Last1')

        assert openreview_client.get_group('~Ella_Last1').members == ['ella@profile.org', 'ella_two@profile.org']
        assert openreview_client.get_group('ella@profile.org').members == ['~Ella_Last1', '~Ella_Alternate_Last1']
        assert openreview_client.get_group('ella_two@profile.org').members == ['~Ella_Last1']
        assert openreview_client.get_group('~Ella_Alternate_Last1').members == ['ella@profile.org']            

        messages = openreview_client.get_messages(to='ella@profile.org', subject='Profile name removal request has been accepted')
        assert len(messages) == 1
        assert messages[0]['content']['text'] == '''Hi Ella Last,

We have received your request to remove the name "Ela Last" from your profile: https://openreview.net/profile?id=~Ella_Last1.

The name has been removed from your profile. Please check that the information listed in your profile is correct.

Thanks,

The OpenReview Team.
'''

    def test_remove_duplicated_name(self, openreview_client, helpers):

        javier_client = helpers.create_user('javier@profile.org', 'Javier', 'Last', alternates=[], institution='google.com')

        profile = javier_client.get_profile()

        profile.content['homepage'] = 'https://javier.google.com'
        profile.content['names'].append({
            'first': 'Javier',
            'middle': 'Alternate',
            'last': 'Last',
            'preferred': True
            })
        javier_client.post_profile(profile)
        profile = javier_client.get_profile(email_or_id='~Javier_Last1')
        assert len(profile.content['names']) == 2
        assert 'username' in profile.content['names'][1]
        assert profile.content['names'][1]['username'] == '~Javier_Alternate_Last1'
        assert profile.content['names'][1]['preferred'] == True

        ## Add publications
        javier_client.post_note_edit(
            invitation='openreview.net/Archive/-/Direct_Upload',
            signatures=['~Javier_Last1'],
            note = openreview.api.Note(
                pdate = openreview.tools.datetime_millis(datetime.datetime(2019, 4, 30)),
                content = {
                    'title': { 'value': 'Paper title 2' },
                    'abstract': { 'value': 'Paper abstract 2' },
                    'authors': { 'value': ['Javier Last', 'Test Client'] },
                    'authorids': { 'value': ['~Javier_Last1', 'test@mail.com'] },
                    'venue': { 'value': 'Arxiv' }
                },
                license = 'CC BY-SA 4.0'
        ))      

        publications = openreview_client.get_notes(content={ 'authorids': '~Javier_Last1'})
        assert len(publications) == 1

        javier_client_2 = helpers.create_user('javier_two@profile.org', 'Javier', 'Last', alternates=[], institution='deepmind.com')
        profile = javier_client_2.get_profile()
        assert '~Javier_Last2' == profile.id

        javier_client_2.post_note_edit(
            invitation='openreview.net/Archive/-/Direct_Upload',
            signatures=['~Javier_Last2'],
            note = openreview.api.Note(
                pdate = openreview.tools.datetime_millis(datetime.datetime(2019, 4, 30)),
                content = {
                    'title': { 'value': 'Paper title 2' },
                    'abstract': { 'value': 'Paper abstract 2' },
                    'authors': { 'value': ['Javier Last', 'Test Client'] },
                    'authorids': { 'value': ['~Javier_Last2', 'test@mail.com'] },
                    'venue': { 'value': 'Arxiv' }
                },
                license = 'CC BY-SA 4.0'
        ))        

        publications = openreview_client.get_notes(content={ 'authorids': '~Javier_Last2'})
        assert len(publications) == 1


        openreview_client.merge_profiles('~Javier_Last1', '~Javier_Last2')
        profile = javier_client.get_profile()
        assert len(profile.content['names']) == 3
        profile.content['names'][0]['username'] == '~Javier_Last1'
        profile.content['names'][1]['username'] == '~Javier_Alternate_Last1'
        profile.content['names'][1]['preferred'] == True
        profile.content['names'][2]['username'] == '~Javier_Last2'
    
        request_note = javier_client.post_note_edit(
            invitation='openreview.net/Support/-/Profile_Name_Removal',
            signatures=['~Javier_Alternate_Last1'],
            note = openreview.api.Note(
                content={
                    'name': { 'value': 'Javier Last' },
                    'usernames': { 'value': ['~Javier_Last1', '~Javier_Last2'] },
                    'comment': { 'value': 'typo in my name' }
                }
            )
        )

        helpers.await_queue_edit(openreview_client, request_note['id'])        

        messages = openreview_client.get_messages(to='javier@profile.org', subject='Profile name removal request has been received')
        assert len(messages) == 1
        assert messages[0]['content']['text'] == '''Hi Javier Alternate Last,

We have received your request to remove the name "Javier Last" from your profile: https://openreview.net/profile?id=~Javier_Alternate_Last1.

We will evaluate your request and you will receive another email with the request status.

Thanks,

The OpenReview Team.
'''

        ## Accept the request
        decision_note = openreview_client.post_note_edit(
            invitation='openreview.net/Support/-/Profile_Name_Removal_Decision',
            signatures=['openreview.net/Support'],
            note = openreview.api.Note(
                id = request_note['note']['id'],
                content={
                    'status': { 'value': 'Accepted' }
                }
            )
        )

        helpers.await_queue_edit(openreview_client, decision_note['id'])

        javier_client = openreview.api.OpenReviewClient(username='javier@profile.org', password=helpers.strong_password)
        note = javier_client.get_note(request_note['note']['id'])
        assert note.content['status']['value'] == 'Accepted'

        publications = openreview_client.get_notes(content={ 'authorids': '~Javier_Alternate_Last1'})
        assert len(publications) == 2
        assert '~Javier_Alternate_Last1' in publications[0].writers
        assert '~Javier_Alternate_Last1' in publications[0].signatures
        assert '~Javier_Alternate_Last1' in publications[1].writers
        assert '~Javier_Alternate_Last1' in publications[1].signatures


        profile = javier_client.get_profile(email_or_id='~Javier_Alternate_Last1')
        assert len(profile.content['names']) == 1
        assert profile.content['names'][0]['username'] == '~Javier_Alternate_Last1'

        found_profiles = openreview_client.search_profiles(fullname='Javier Alternate', use_ES=True)
        assert len(found_profiles) == 1
        assert len(found_profiles[0].content['names']) == 1
        assert found_profiles[0].content['names'][0]['username'] == '~Javier_Alternate_Last1'       

        with pytest.raises(openreview.OpenReviewException, match=r'Group Not Found: ~Javier_Last1'):
            openreview_client.get_group('~Javier_Last1')

        messages = openreview_client.get_messages(to='javier@profile.org', subject='Profile name removal request has been accepted')
        assert len(messages) == 1
        assert messages[0]['content']['text'] == '''Hi Javier Alternate Last,

We have received your request to remove the name "Javier Last" from your profile: https://openreview.net/profile?id=~Javier_Alternate_Last1.

The name has been removed from your profile. Please check that the information listed in your profile is correct.

Thanks,

The OpenReview Team.
'''

    def test_rename_publications_from_api2(self, test_client, helpers, openreview_client):

        journal=Journal(openreview_client, 'CABJ', '1234', contact_info='cabj@mail.org', full_name='Transactions on Machine Learning Research', short_name='CABJ', submission_name='Submission')
        journal.setup(support_role='test@mail.com', editors=[])

        venue = Venue(openreview_client, 'ACMM.org/2023/Conference', 'openreview.net/Support')        
        venue.submission_stage = openreview.stages.SubmissionStage(double_blind=True, due_date=datetime.datetime.now() + datetime.timedelta(minutes = 30))
        venue.review_stage = openreview.stages.ReviewStage()
        venue.comment_stage = openreview.stages.CommentStage(enable_chat=True)
        venue.setup(program_chair_ids=['venue_pc@mail.com'])
        venue.create_submission_stage()
        venue.registration_stages.append(openreview.stages.RegistrationStage(committee_id = venue.get_reviewers_id(),
            name = 'Registration',
            start_date = None,
            due_date = None,
            instructions = 'TODO: instructions',
            title = 'ACMM 2023 Conference - Reviewer registration'))
        venue.create_registration_stages()        
        
        paul_client = helpers.create_user('paul@profile.org', 'Paul', 'Last', alternates=[], institution='google.com')
        profile = paul_client.get_profile()

        profile.content['homepage'] = 'https://paul.google.com'
        profile.content['names'].append({
            'first': 'Paul',
            'middle': 'Alternate',
            'last': 'Last'
            })
        paul_client.post_profile(profile)
        profile = paul_client.get_profile(email_or_id='~Paul_Last1')
        assert len(profile.content['names']) == 2
        assert 'username' in profile.content['names'][1]
        assert profile.content['names'][1]['username'] == '~Paul_Alternate_Last1'

        assert openreview_client.get_group('~Paul_Last1').members == ['paul@profile.org']
        assert openreview_client.get_group('paul@profile.org').members == ['~Paul_Last1', '~Paul_Alternate_Last1']
        assert openreview_client.get_group('~Paul_Alternate_Last1').members == ['paul@profile.org']

        openreview_client.add_members_to_group('ACMM.org/2023/Conference/Reviewers', ['~Paul_Alternate_Last1'])

        ## post block status tag
        tag = openreview_client.post_tag(
            openreview.api.Tag(
                invitation='openreview.net/Support/-/Profile_Blocked_Status',
                signature='openreview.net/Support',
                profile='~Paul_Alternate_Last1',
                label='Impersonating Paul MacCartney',
                readers=['openreview.net/Support'],
            )
        )

        helpers.await_queue_edit(openreview_client, edit_id=tag.id)

        tags = openreview_client.get_tags(profile='~Paul_Alternate_Last1')
        assert len(tags) == 1
        assert tags[0].readers == ['openreview.net/Support', 'ACMM.org/2023/Conference']

        ## Add Registration note
        paul_client.post_note_edit(
            invitation='ACMM.org/2023/Conference/Reviewers/-/Registration',
            signatures=['~Paul_Alternate_Last1'],
            note = openreview.api.Note(
                content={
                    'profile_confirmed': { 'value': 'Yes' },
                    'expertise_confirmed': { 'value': 'Yes' },
                }
            )
        )

        ## Add publications
        paul_client.post_note_edit(
            invitation='openreview.net/Archive/-/Direct_Upload',
            signatures=['~Paul_Alternate_Last1'],
            note = openreview.api.Note(
                pdate = openreview.tools.datetime_millis(datetime.datetime(2019, 4, 30)),
                content = {
                    'title': { 'value': 'Paper title 1' },
                    'abstract': { 'value': 'Paper abstract 1' },
                    'authors': { 'value': ['Paul Alternate Last', 'Test Client'] },
                    'authorids': { 'value': ['~Paul_Alternate_Last1', 'test@mail.com'] },
                    'venue': { 'value': 'Arxiv' }
                },
                license = 'CC BY-SA 4.0'
        ))         
        

        paul_client.post_note_edit(
            invitation='openreview.net/Archive/-/Direct_Upload',
            signatures=['~Paul_Alternate_Last1'],
            note = openreview.api.Note(
                pdate = openreview.tools.datetime_millis(datetime.datetime(2019, 4, 30)),
                content = {
                    'title': { 'value': 'Paper title 2' },
                    'abstract': { 'value': 'Paper abstract 2' },
                    'authors': { 'value': ['Paul Alternate Last', 'Test Client'] },
                    'authorids': { 'value': ['~Paul_Alternate_Last1', 'test@mail.com'] },
                    'venue': { 'value': 'Arxiv' }
                },
                license = 'CC BY-SA 4.0'
        ))         

        submission_note_1 = paul_client.post_note_edit(invitation='CABJ/-/Submission',
            signatures=['~Paul_Alternate_Last1'],
            note=Note(
                content={
                    'title': { 'value': 'Paper title' },
                    'abstract': { 'value': 'Paper abstract' },
                    'authors': { 'value': ['SomeFirstName User', 'Paul Alternate Last']},
                    'authorids': { 'value': ['~SomeFirstName_User1', '~Paul_Alternate_Last1']},
                    'pdf': {'value': '/pdf/' + 'p' * 40 +'.pdf' },
                    'competing_interests': { 'value': 'None beyond the authors normal conflict of interests'},
                    'human_subjects_reporting': { 'value': 'Not applicable'}
                }
            ))
        
        helpers.await_queue_edit(openreview_client, edit_id=submission_note_1['id'])                   

        openreview_client.add_members_to_group('CABJ/Reviewers', ['~Paul_Alternate_Last1'])

        paul_client.post_edge(openreview.api.Edge(
            invitation='CABJ/Reviewers/-/Assignment_Availability',
            signatures=['~Paul_Alternate_Last1'],
            head='CABJ/Reviewers',
            tail='~Paul_Alternate_Last1',
            label='Unavailable'
        ))

        submission_note_2 = paul_client.post_note_edit(invitation='CABJ/-/Submission',
            signatures=['~Paul_Alternate_Last1'],
            note=Note(
                content={
                    'title': { 'value': 'Paper title 2' },
                    'abstract': { 'value': 'Paper abstract' },
                    'authors': { 'value': ['SomeFirstName User', 'Paul Alternate Last']},
                    'authorids': { 'value': ['~SomeFirstName_User1', '~Paul_Alternate_Last1']},
                    'pdf': {'value': '/pdf/' + 'p' * 40 +'.pdf' },
                    'competing_interests': { 'value': 'None beyond the authors normal conflict of interests'},
                    'human_subjects_reporting': { 'value': 'Not applicable'}
                }
            ))

        helpers.await_queue_edit(openreview_client, edit_id=submission_note_2['id'])
        note_id_2=submission_note_2['note']['id']

        submission = openreview_client.get_note(note_id_2)

        helpers.create_user('carlos@cabj.org', 'Carlos', 'Tevez')
        openreview_client.add_members_to_group('CABJ/Action_Editors', ['~Carlos_Tevez1'])
                       
        paper_assignment_edge = openreview_client.post_edge(openreview.Edge(invitation='CABJ/Action_Editors/-/Assignment',
            readers=['CABJ', 'CABJ/Editors_In_Chief', '~Carlos_Tevez1'],
            writers=['CABJ', 'CABJ/Editors_In_Chief'],
            signatures=['CABJ/Editors_In_Chief'],
            head=note_id_2,
            tail='~Carlos_Tevez1',
            weight=1
        ))

        helpers.await_queue_edit(openreview_client, edit_id=paper_assignment_edge.id)

        carlos_client = openreview.api.OpenReviewClient(username='carlos@cabj.org', password=helpers.strong_password)

        carlos_paper2_anon_groups = carlos_client.get_groups(prefix=f'CABJ/Paper2/Action_Editor_.*', signatory='~Carlos_Tevez1')
        assert len(carlos_paper2_anon_groups) == 1
        carlos_paper2_anon_group = carlos_paper2_anon_groups[0]

        under_review_note = carlos_client.post_note_edit(invitation= 'CABJ/Paper2/-/Review_Approval',
                                    signatures=[carlos_paper2_anon_group.id],
                                    note=Note(content={
                                        'under_review': { 'value': 'Appropriate for Review' }
                                    }))

        helpers.await_queue_edit(openreview_client, edit_id=under_review_note['id'])

        acceptance_note = openreview_client.post_note_edit(invitation=journal.get_accepted_id(),
            signatures=['CABJ'],
            note=openreview.api.Note(id=submission.id,
                pdate = openreview.tools.datetime_millis(datetime.datetime.now()),
                content= {
                    '_bibtex': {
                        'value': journal.get_bibtex(submission, journal.accepted_venue_id, certifications=[])
                    }
                }
            )
        )

        helpers.await_queue_edit(openreview_client, edit_id=acceptance_note['id'])

        note = openreview_client.get_note(note_id_2)
        assert note.content['_bibtex']['value'] == '''@article{
user''' + str(datetime.datetime.fromtimestamp(note.cdate/1000).year) + '''paper,
title={Paper title 2},
author={SomeFirstName User and Paul Alternate Last},
journal={Transactions on Machine Learning Research},
year={''' + str(datetime.datetime.fromtimestamp(note.cdate/1000).year) + '''},
url={https://openreview.net/forum?id=''' + note_id_2 + '''},
note={}
}'''

        ## Invitations
        journal.invitation_builder.set_note_camera_ready_revision_invitation(submission, journal.get_due_date(weeks = journal.get_camera_ready_period_length()))
        invitation = openreview_client.get_invitation('CABJ/Paper2/-/Camera_Ready_Revision')
        assert invitation.edit['note']['content']['authorids']['value'] == ['~SomeFirstName_User1', '~Paul_Alternate_Last1']
        
        
        test_client = openreview.api.OpenReviewClient(username='test@mail.com', password=helpers.strong_password)
        submission_note_1 = test_client.post_note_edit(invitation='ACMM.org/2023/Conference/-/Submission',
            signatures=['~SomeFirstName_User1'],
            note=Note(
                content={
                    'title': { 'value': 'Paper title' },
                    'abstract': { 'value': 'Paper abstract' },
                    'authors': { 'value': ['SomeFirstName User', 'Paul Alternate Last', 'Ana Alternate Last']},
                    'authorids': { 'value': ['~SomeFirstName_User1', '~Paul_Alternate_Last1', '~Ana_Alternate_Last1']},
                    'keywords': { 'value': ['data', 'mining']},
                    'pdf': {'value': '/pdf/' + 'p' * 40 +'.pdf' }
                }
            ))
        
        helpers.await_queue_edit(openreview_client, edit_id=submission_note_1['id'])

        venue.create_comment_stage()     

        ## Create committee groups
        openreview_client.post_group_edit(
            invitation = 'openreview.net/-/Edit',
            signatures=['~Super_User1'],
            group  = openreview.api.Group(
                id='ICLRR.cc',
                readers=['everyone'],
                writers=['ICLRR.cc'],
                signatories=[],
                members=[],
                signatures=['~Super_User1']
            )
        )

        openreview_client.post_group_edit(
            invitation = 'openreview.net/-/Edit',
            signatures=['~Super_User1'],
            group  = openreview.api.Group(
                id='ICLRR.cc/Reviewers',
                readers=['everyone'],
                writers=['ICLRR.cc'],
                signatories=[],
                members=['~Paul_Alternate_Last1'],
                signatures=['~Super_User1']
            )
        ) 

        publications = openreview_client.get_notes(content={ 'authorids': '~Paul_Last1'})
        assert len(publications) == 5

        request_note = paul_client.post_note_edit(
            invitation='openreview.net/Support/-/Profile_Name_Removal',
            signatures=['~Paul_Last1'],
            note = openreview.api.Note(
                content={
                    'name': { 'value': 'Paul Alternate Last' },
                    'usernames': { 'value': ['~Paul_Alternate_Last1'] },
                    'comment': { 'value': 'typo in my name' }
                }
            )
        )

        helpers.await_queue_edit(openreview_client, request_note['id'])        

        messages = openreview_client.get_messages(to='paul@profile.org', subject='Profile name removal request has been received')
        assert len(messages) == 1
        assert messages[0]['content']['text'] == '''Hi Paul Last,

We have received your request to remove the name "Paul Alternate Last" from your profile: https://openreview.net/profile?id=~Paul_Last1.

We will evaluate your request and you will receive another email with the request status.

Thanks,

The OpenReview Team.
'''

        ## Accept the request
        decision_note = openreview_client.post_note_edit(
            invitation='openreview.net/Support/-/Profile_Name_Removal_Decision',
            signatures=['openreview.net/Support'],
            note = openreview.api.Note(
                id = request_note['note']['id'],
                content={
                    'status': { 'value': 'Accepted' }
                }
            )
        )

        helpers.await_queue_edit(openreview_client, decision_note['id'])

        note = paul_client.get_note(request_note['note']['id'])
        assert note.content['status']['value'] == 'Accepted'

        registration_notes = openreview_client.get_notes(invitation='ACMM.org/2023/Conference/Reviewers/-/Registration')
        assert len(registration_notes) == 1
        assert registration_notes[0].signatures == ['~Paul_Last1']        
        
        publications = openreview_client.get_notes(content={ 'authorids': '~Paul_Last1'})
        assert len(publications) == 5
        assert ['ACMM.org/2023/Conference', '~SomeFirstName_User1', '~Paul_Last1', '~Ana_Alternate_Last1'] == publications[0].writers
        assert ['ACMM.org/2023/Conference', '~SomeFirstName_User1', '~Paul_Last1', '~Ana_Alternate_Last1'] == publications[0].readers
        assert ['~SomeFirstName_User1', '~Paul_Last1', '~Ana_Alternate_Last1'] == publications[0].content['authorids']['value']
        assert ['SomeFirstName User', 'Paul Last', 'Ana Alternate Last'] == publications[0].content['authors']['value']
        assert ['~SomeFirstName_User1'] == publications[0].signatures

        note = openreview_client.get_note(note_id_2)
        assert note.content['_bibtex']['value'] == '''@article{
user''' + str(datetime.datetime.fromtimestamp(note.cdate/1000).year) + '''paper,
title={Paper title 2},
author={SomeFirstName User and Paul Last},
journal={Transactions on Machine Learning Research},
year={''' + str(datetime.datetime.fromtimestamp(note.cdate/1000).year) + '''},
url={https://openreview.net/forum?id=''' + note_id_2 + '''},
note={}
}'''         

        group = openreview_client.get_group('ICLRR.cc/Reviewers')
        assert '~Paul_Alternate_Last1' not in group.members
        assert '~Paul_Last1' in group.members

        group = openreview_client.get_group('CABJ/Paper1/Authors')
        assert '~Paul_Alternate_Last1' not in group.members
        assert '~Paul_Last1' in group.members

        invitation = openreview_client.get_invitation('CABJ/Paper2/-/Camera_Ready_Revision')
        assert invitation.edit['note']['content']['authorids']['value'] == ['~SomeFirstName_User1', '~Paul_Last1']

        openreview_client.post_note_edit(
            invitation='CABJ/Paper2/-/Camera_Ready_Revision',
            signatures=['CABJ/Paper2/Authors'],
            note=openreview.api.Note(
                content= {
                    'title': {'value': 'Paper title 2 Updated'},
                    'abstract': { 'value': 'Paper abstract' },
                    'authors': { 'value': ['SomeFirstName User', 'Paul Last']},
                    'authorids': { 'value': ['~SomeFirstName_User1', '~Paul_Last1']},
                    'pdf': {'value': '/pdf/' + 'p' * 40 +'.pdf' },
                    'competing_interests': { 'value': 'None beyond the authors normal conflict of interests'},
                    'human_subjects_reporting': { 'value': 'Not applicable'}                        
                }
            )
        )

        profile = paul_client.get_profile(email_or_id='~Paul_Last1')
        assert len(profile.content['names']) == 1
        assert 'username' in profile.content['names'][0]
        assert profile.content['names'][0]['username'] == '~Paul_Last1'

        with pytest.raises(openreview.OpenReviewException, match=r'Group Not Found: ~Paul_Alternate_Last1'):
            openreview_client.get_group('~Paul_Alternate_Last1')

        assert openreview_client.get_group('~Paul_Last1').members == ['paul@profile.org']
        assert openreview_client.get_group('paul@profile.org').members == ['~Paul_Last1']

        messages = openreview_client.get_messages(to='paul@profile.org', subject='Profile name removal request has been accepted')
        assert len(messages) == 1
        assert messages[0]['content']['text'] == '''Hi Paul Last,

We have received your request to remove the name "Paul Alternate Last" from your profile: https://openreview.net/profile?id=~Paul_Last1.

The name has been removed from your profile. Please check that the information listed in your profile is correct.

Thanks,

The OpenReview Team.
'''

        assert openreview_client.get_edges(invitation='CABJ/Reviewers/-/Assignment_Availability', tail='~Paul_Last1')[0].label == 'Unavailable'

    def test_remove_name_and_update_relations(self, openreview_client, helpers):

        juan_client = helpers.create_user('juan@profile.org', 'Juan', 'Last', alternates=[], institution='google.com')

        profile = juan_client.get_profile()

        profile.content['homepage'] = 'https://juan.google.com'
        profile.content['names'].append({
            'first': 'Juan',
            'middle': 'Alternate',
            'last': 'Last',
            'preferred': True
            })
        juan_client.post_profile(profile)
        profile = juan_client.get_profile(email_or_id='~Juan_Last1')
        assert len(profile.content['names']) == 2
        assert 'username' in profile.content['names'][1]
        assert profile.content['names'][1]['username'] == '~Juan_Alternate_Last1'
        assert profile.content['names'][1]['preferred'] == True

        juan_client.post_note_edit(
            invitation='openreview.net/Archive/-/Direct_Upload',
            signatures=['~Juan_Alternate_Last1'],
            note = openreview.api.Note(
                pdate = openreview.tools.datetime_millis(datetime.datetime(2019, 4, 30)),
                content = {
                    'title': { 'value': 'Paper title 1' },
                    'abstract': { 'value': 'Paper abstract 1' },
                    'authors': { 'value': ['Juan Last', 'Test Client'] },
                    'authorids': { 'value': ['~Juan_Last1', 'test@mail.com'] },
                    'venue': { 'value': 'Arxiv' }
                },
                license = 'CC BY-SA 4.0'
        ))                      

        john_client = openreview.api.OpenReviewClient(username='john@profile.org', password=helpers.strong_password)

        profile = john_client.get_profile()

        profile.content['relations'].append({
            'relation': 'Advisor',
            'name': 'Juan Last',
            'username': '~Juan_Last1',
            'start': 2015,
            'end': None
        }) 
        john_client.post_profile(profile)

        profile = john_client.get_profile(email_or_id='john@profile.org')
        assert len(profile.content['relations']) == 2

        request_note = juan_client.post_note_edit(
            invitation='openreview.net/Support/-/Profile_Name_Removal',
            signatures=['~Juan_Alternate_Last1'],
            note = openreview.api.Note(
                content={
                    'name': { 'value': 'Juan Last' },
                    'usernames': { 'value': ['~Juan_Last1'] },
                    'comment': { 'value': 'typo in my name' }
                }
            )
        )

        helpers.await_queue_edit(openreview_client, request_note['id'])         

        decision_note = openreview_client.post_note_edit(
            invitation='openreview.net/Support/-/Profile_Name_Removal_Decision',
            signatures=['openreview.net/Support'],
            note = openreview.api.Note(
                id = request_note['note']['id'],
                content={
                    'status': { 'value': 'Accepted' }
                }
            )
        )

        helpers.await_queue_edit(openreview_client, decision_note['id'])

        juan_client = openreview.api.OpenReviewClient(username='juan@profile.org', password=helpers.strong_password)
        note = juan_client.get_note(request_note['note']['id'])
        assert note.content['status']['value'] == 'Accepted' 

        profile = juan_client.get_profile(email_or_id='juan@profile.org')
        assert len(profile.content['names']) == 1
        assert 'username' in profile.content['names'][0]
        assert profile.content['names'][0]['username'] == '~Juan_Alternate_Last1' 

        john_client = openreview.api.OpenReviewClient(username='john@profile.org', password=helpers.strong_password)
        profile = john_client.get_profile()
        assert len(profile.content['relations']) == 2
        assert profile.content['relations'][1]['username'] == '~Juan_Alternate_Last1'                                             
        assert profile.content['relations'][1]['name'] == 'Juan Alternate Last'

        ## update profile with no changes and make sure the relations are all the same
        profile.content['history'][0] = {
            "position": "PhD Student",
            "start": 2017,
            "end": None,
            "institution": {
                "country": "US",
                "domain": "google.com",
                "name": "Google"
            }
        }
        john_client.post_profile(profile) 
        profile = john_client.get_profile()                                      
        assert len(profile.content['relations']) == 2
        assert profile.content['relations'][1]['username'] == '~Juan_Alternate_Last1'                                             
        assert profile.content['relations'][1]['name'] == 'Juan Alternate Last'


    def test_remove_name_and_accept_automatically(self, openreview_client, helpers):

        nara_client = helpers.create_user('nara@profile.org', 'Nara', 'Last', alternates=[], institution='google.com')

        profile = nara_client.get_profile()

        profile.content['homepage'] = 'https://nara.google.com'
        profile.content['names'].append({
            'first': 'Nara',
            'middle': 'Alternate',
            'last': 'Last',
            'preferred': True
            })
        nara_client.post_profile(profile)
        profile = nara_client.get_profile(email_or_id='~Nara_Last1')
        assert len(profile.content['names']) == 2
        assert 'username' in profile.content['names'][1]
        assert profile.content['names'][1]['username'] == '~Nara_Alternate_Last1'
        assert profile.content['names'][1]['preferred'] == True

        request_note = nara_client.post_note_edit(
            invitation='openreview.net/Support/-/Profile_Name_Removal',
            signatures=['~Nara_Alternate_Last1'],
            note = openreview.api.Note(
                content={
                    'name': { 'value': 'Nara Last' },
                    'usernames': { 'value': ['~Nara_Last1'] },
                    'comment': { 'value': 'typo in my name' }
                }
            )
        )

        helpers.await_queue_edit(openreview_client, request_note['id'])              

        nara_client = openreview.api.OpenReviewClient(username='nara@profile.org', password=helpers.strong_password)
        note = nara_client.get_note(request_note['note']['id'])
        assert note.content['status']['value'] == 'Accepted'

    def test_remove_name_and_do_not_accept_automatically(self, openreview_client, helpers):

        mara_client = helpers.create_user('mara@profile.org', 'Mara', 'Last', alternates=[], institution='google.com')

        profile = mara_client.get_profile()

        profile.content['homepage'] = 'https://mara.google.com'
        profile.content['names'].append({
            'first': 'Mara',
            'middle': 'Alternate',
            'last': 'Last',
            'preferred': True
            })
        mara_client.post_profile(profile)
        profile = mara_client.get_profile(email_or_id='~Mara_Last1')
        assert len(profile.content['names']) == 2
        assert 'username' in profile.content['names'][1]
        assert profile.content['names'][1]['username'] == '~Mara_Alternate_Last1'
        assert profile.content['names'][1]['preferred'] == True

        mara_client_v2 = openreview.api.OpenReviewClient(username='mara@profile.org', password=helpers.strong_password)
        submission_note_1 = mara_client_v2.post_note_edit(invitation='CABJ/-/Submission',
            signatures=['~Mara_Last1'],
            note=Note(
                content={
                    'title': { 'value': 'Paper title' },
                    'abstract': { 'value': 'Paper abstract' },
                    'authors': { 'value': ['SomeFirstName User', 'Mara Last']},
                    'authorids': { 'value': ['~SomeFirstName_User1', '~Mara_Last1']},
                    'pdf': {'value': '/pdf/' + 'p' * 40 +'.pdf' },
                    'competing_interests': { 'value': 'None beyond the authors normal conflict of interests'},
                    'human_subjects_reporting': { 'value': 'Not applicable'}
                }
            ))
        
        helpers.await_queue_edit(openreview_client, edit_id=submission_note_1['id'])        

        request_note = mara_client.post_note_edit(
            invitation='openreview.net/Support/-/Profile_Name_Removal',
            signatures=['~Mara_Alternate_Last1'],
            note = openreview.api.Note(
                content={
                    'name': { 'value': 'Mara Last' },
                    'usernames': { 'value': ['~Mara_Last1'] },
                    'comment': { 'value': 'typo in my name' }
                }
            )
        )

        helpers.await_queue_edit(openreview_client, request_note['id'])               

        note = mara_client.get_note(request_note['note']['id'])
        assert note.content['status']['value'] == 'Pending'        


    def test_merge_profiles(self, openreview_client, helpers):

        rachel_client = helpers.create_user('rachel@profile.org', 'Rachel', 'Last', alternates=[], institution='google.com')
        profile = rachel_client.get_profile()

        profile.content['homepage'] = 'https://rachel.google.com'
        profile.content['names'].append({
            'first': 'Rachel',
            'middle': 'Alternate',
            'last': 'Last'
            })
        rachel_client.post_profile(profile)
        profile = rachel_client.get_profile(email_or_id='~Rachel_Last1')
        assert len(profile.content['names']) == 2
        assert 'username' in profile.content['names'][1]
        assert profile.content['names'][1]['username'] == '~Rachel_Alternate_Last1'

        helpers.create_user('rachel@gmail.com', 'Rachel', 'First', alternates=[], institution='google.com')

        edit = rachel_client.post_note_edit(
            invitation = 'openreview.net/Support/-/Profile_Merge',
            signatures=['~Rachel_Last1'],
            note = openreview.api.Note(
                content={
                    'left': { 'value': '~Rachel_Last1' },
                    'right': { 'value': '~Rachel_First1' },
                    'comment': { 'value': 'please merge my profiles' }
                }
        ))

        helpers.await_queue_edit(openreview_client, edit_id=edit['id'])

        messages = openreview_client.get_messages(to='rachel@profile.org', subject='Profile merge request has been received')
        assert len(messages) == 1
        assert messages[0]['content']['text'] == '''Hi Rachel Last,

We have received your request to merge the following profiles: ~Rachel_Last1, ~Rachel_First1.

We will evaluate your request and you will receive another email with the request status.

Thanks,

The OpenReview Team.
'''

        ## Accept the request
        edit = openreview_client.post_note_edit(
            invitation='openreview.net/Support/-/Profile_Merge_Decision',
            signatures=['openreview.net/Support'],
            note = openreview.api.Note(
                id=edit['note']['id'],
                content={
                    'status': { 'value': 'Accepted' }
                }
        ))

        helpers.await_queue_edit(openreview_client, edit_id=edit['id'])

        messages = openreview_client.get_messages(to='rachel@profile.org', subject='Profile merge request has been accepted')
        assert len(messages) == 1
        assert messages[0]['content']['text'] == '''Hi Rachel Last,

We have received your request to merge the following profiles: ~Rachel_Last1, ~Rachel_First1.

The profiles have been merged. Please check that the information listed in your profile is correct.

Thanks,

The OpenReview Team.
'''

    def test_merge_profiles_as_guest(self, openreview_client, helpers):

        helpers.create_user('marina@profile.org', 'Marina', 'Last', alternates=[], institution='google.com')
        helpers.create_user('marina@gmail.com', 'Marina', 'Last', alternates=[], institution='google.com')

        guest_client = openreview.api.OpenReviewClient()
        edit = guest_client.post_note_edit(
            invitation = 'openreview.net/Support/-/Profile_Merge',
            signatures=['(guest)'],
            note = openreview.api.Note(
                content={
                    'email': { 'value': 'marina@hotmail.com' },
                    'left': { 'value': 'marina@profile.org' },
                    'right': { 'value': 'marina@gmail.com' },
                    'comment': { 'value': 'please merge my profiles' }
                }
        ))

        helpers.await_queue_edit(openreview_client, edit_id=edit['id'])

        messages = openreview_client.get_messages(to='marina@hotmail.com', subject='Profile merge request has been received')
        assert len(messages) == 1
        assert messages[0]['content']['text'] == '''Hi marina@hotmail.com,

We have received your request to merge the following profiles: marina@profile.org, marina@gmail.com.

We will evaluate your request and you will receive another email with the request status.

Thanks,

The OpenReview Team.
'''

        ## Reject the request
        edit = openreview_client.post_note_edit(
            invitation='openreview.net/Support/-/Profile_Merge_Decision',
            signatures=['openreview.net/Support'],
            note = openreview.api.Note(
                id=edit['note']['id'],
                content={
                    'status': { 'value': 'Rejected' },
                    'support_comment': { 'value': 'not real profiles' }
                }
        ))        

        helpers.await_queue_edit(openreview_client, edit_id=edit['id'])

        messages = openreview_client.get_messages(to='marina@hotmail.com', subject='Profile merge request has been rejected')
        assert len(messages) == 1
        assert messages[0]['content']['text'] == '''Hi marina@hotmail.com,

We have received your request to merge the following profiles: marina@profile.org, marina@gmail.com.

We can not merge your profiles for the following reason:

not real profiles

Regards,

The OpenReview Team.
'''


    def test_merge_profiles_ignore_request(self, openreview_client, helpers):

        melisa_client = helpers.create_user('melisa@profile.org', 'Melisa', 'Last', alternates=[], institution='google.com')
        profile = melisa_client.get_profile()

        profile.content['homepage'] = 'https://melisa.google.com'
        profile.content['names'].append({
            'first': 'Melisa',
            'middle': 'Alternate',
            'last': 'Last'
            })
        melisa_client.post_profile(profile)
        profile = melisa_client.get_profile(email_or_id='~Melisa_Last1')
        assert len(profile.content['names']) == 2
        assert 'username' in profile.content['names'][1]
        assert profile.content['names'][1]['username'] == '~Melisa_Alternate_Last1'

        helpers.create_user('melisa@gmail.com', 'Melisa', 'First', alternates=[], institution='google.com')

        edit = melisa_client.post_note_edit(
            invitation = 'openreview.net/Support/-/Profile_Merge',
            signatures=['~Melisa_Last1'],
            note = openreview.api.Note(
                content={
                    'left': { 'value': '~Melisa_Last1' },
                    'right': { 'value': '~Melisa_First1' },
                    'comment': { 'value': 'please merge my profiles' }
                }
        ))

        helpers.await_queue_edit(openreview_client, edit_id=edit['id'])        

        messages = openreview_client.get_messages(to='melisa@profile.org', subject='Profile merge request has been received')
        assert len(messages) == 1
        assert messages[0]['content']['text'] == '''Hi Melisa Last,

We have received your request to merge the following profiles: ~Melisa_Last1, ~Melisa_First1.

We will evaluate your request and you will receive another email with the request status.

Thanks,

The OpenReview Team.
'''

        ## Accept the request
        edit = openreview_client.post_note_edit(
            invitation='openreview.net/Support/-/Profile_Merge_Decision',
            signatures=['openreview.net/Support'],
            note = openreview.api.Note(
                id=edit['note']['id'],
                content={
                    'status': { 'value': 'Ignored' }
                }
        ))

        helpers.await_queue_edit(openreview_client, edit_id=edit['id'])        

        messages = openreview_client.get_messages(to='melisa@profile.org', subject='Profile merge request has been accepted')
        assert len(messages) == 0

    def test_remove_email_address(self, openreview_client, helpers):

        harold_client = helpers.create_user('harold@profile.org', 'Harold', 'Last', alternates=[], institution='google.com')
        profile = harold_client.get_profile()

        profile.content['homepage'] = 'https://harold.google.com'
        profile.content['emails'].append('alternate_harold@profile.org')
        harold_client.post_profile(profile)
        profile = harold_client.get_profile(email_or_id='~Harold_Last1')
        assert len(profile.content['emails']) == 2
        assert profile.content['emails'][0] == 'harold@profile.org'
        assert profile.content['emails'][1] == 'alternate_harold@profile.org'

        assert openreview_client.get_group('~Harold_Last1').members == ['harold@profile.org']
        assert openreview_client.get_group('harold@profile.org').members == ['~Harold_Last1']
        with pytest.raises(openreview.OpenReviewException, match=r'Group Not Found: alternate_harold@profile.org'):
            assert openreview_client.get_group('alternate_harold@profile.org').members == []

        openreview_client.post_group_edit(invitation = 'openreview.net/-/Edit', 
            signatures = ['~Super_User1'], 
            group = openreview.api.Group(
                id = '~Harold_Last1', 
                members = {
                    'add': ['alternate_harold@profile.org']
                },
                signatures = ['~Super_User1']
            )
        )

        openreview_client.post_group_edit(invitation = 'openreview.net/-/Edit', 
            signatures = ['~Super_User1'], 
            group = openreview.api.Group(
                id = 'alternate_harold@profile.org', 
                members = {
                    'add': ['~Harold_Last1']
                },
                signatures = ['~Super_User1']
            )
        )

        ## Try to remove the unexisting name and get an error
        with pytest.raises(openreview.OpenReviewException, match=r'Profile not found for ~Harold_Lastt1'):
            openreview_client.post_note_edit(
                invitation = 'openreview.net/Support/-/Profile_Email_Removal',
                signatures=['openreview.net/Support'],
                note = openreview.api.Note(
                    content={
                        'email': { 'value': 'harold@profile.org' },
                        'profile_id': { 'value':'~Harold_Lastt1' },
                        'comment': { 'value': 'email is wrong' }
                    }
                )
            )

        ## Try to remove the name that is marked as preferred and get an error
        with pytest.raises(openreview.OpenReviewException, match=r'Email haroldd@profile.org not found in profile ~Harold_Last1'):
            openreview_client.post_note_edit(
                invitation = 'openreview.net/Support/-/Profile_Email_Removal',
                signatures=['openreview.net/Support'],
                note = openreview.api.Note(
                    content={
                        'email': { 'value': 'haroldd@profile.org' },
                        'profile_id': { 'value':'~Harold_Last1' },
                        'comment': { 'value': 'email is wrong' }
                    }
                )
            ) 

        ## Try to remove the name that doesn't match with the username and get an error
        with pytest.raises(openreview.OpenReviewException, match=r'Email harold@profile.org is already the preferred email in profile ~Harold_Last1'):
            openreview_client.post_note_edit(
                invitation = 'openreview.net/Support/-/Profile_Email_Removal',
                signatures=['openreview.net/Support'],
                note = openreview.api.Note(
                    content={
                        'email': { 'value': 'harold@profile.org' },
                        'profile_id': { 'value':'~Harold_Last1' },
                        'comment': { 'value': 'email is wrong' }
                    }
                )
            )                  


        ## Add publications
        openreview_client.post_note_edit(
            invitation='openreview.net/Archive/-/Direct_Upload',
            signatures=['~Harold_Last1'],
            note = openreview.api.Note(
                pdate = openreview.tools.datetime_millis(datetime.datetime(2019, 4, 30)),
                content = {
                    'title': { 'value': 'Paper title 1' },
                    'abstract': { 'value': 'Paper abstract 1' },
                    'authors': { 'value': ['Harold Last', 'Test Client'] },
                    'authorids': { 'value': ['alternate_harold@profile.org', 'test@mail.com'] },
                    'venue': { 'value': 'Arxiv' }
                },
                license = 'CC BY-SA 4.0'
        ))        

        openreview_client.post_note_edit(
            invitation='openreview.net/Archive/-/Direct_Upload',
            signatures=['~Harold_Last1'],
            note = openreview.api.Note(
                pdate = openreview.tools.datetime_millis(datetime.datetime(2019, 4, 30)),
                content = {
                    'title': { 'value': 'Paper title 2' },
                    'abstract': { 'value': 'Paper abstract 2' },
                    'authors': { 'value': ['Harold Last', 'Test Client'] },
                    'authorids': { 'value': ['alternate_harold@profile.org', 'test@mail.com', 'another@mail.com'] },
                    'venue': { 'value': 'Arxiv' }
                },
                license = 'CC BY-SA 4.0'
        )) 

        ## Add v2 submission
        harold_client_v2 = openreview.api.OpenReviewClient(username='alternate_harold@profile.org', password=helpers.strong_password)
        submission_note_1 = harold_client_v2.post_note_edit(invitation='ACMM.org/2023/Conference/-/Submission',
            signatures=['~Harold_Last1'],
            note=Note(
                content={
                    'title': { 'value': 'Paper title' },
                    'abstract': { 'value': 'Paper abstract' },
                    'authors': { 'value': ['SomeFirstName User', 'Paul Last', 'Harold Last']},
                    'authorids': { 'value': ['~SomeFirstName_User1', '~Paul_Last1', 'alternate_harold@profile.org']},
                    'keywords': { 'value': ['data', 'mining']},
                    'pdf': {'value': '/pdf/' + 'p' * 40 +'.pdf' }                    
                }
            ))
        
        helpers.await_queue_edit(openreview_client, edit_id=submission_note_1['id'])         

        ## Create committee groups
        openreview_client.post_group_edit(
            invitation = 'openreview.net/-/Edit',
            signatures = ['openreview.net'],
            group = openreview.api.Group(
                id='ICMLR.cc',
                readers=['everyone'],
                writers=['ICMLR.cc'],
                signatures=['~Super_User1'],
                signatories=[],
                members=[]
        ))

        openreview_client.post_group_edit(
            invitation = 'openreview.net/-/Edit',
            signatures = ['openreview.net'],
            group = openreview.api.Group(
                id='ICMLR.cc/Reviewers',
                readers=['everyone'],
                writers=['ICMLR.cc'],
                signatures=['~Super_User1'],
                signatories=[],
                members=['alternate_harold@profile.org'],
                anonids=True
        ))

        anon_groups = openreview_client.get_groups(prefix='ICMLR.cc/Reviewer_')
        assert len(anon_groups) == 1
        assert 'alternate_harold@profile.org' in anon_groups[0].members
        first_anon_group_id = anon_groups[0].id                

        publications = openreview_client.get_notes(content={ 'authorids': '~Harold_Last1'})
        assert len(publications) == 3

        edit = openreview_client.post_note_edit(
            invitation = 'openreview.net/Support/-/Profile_Email_Removal',
            signatures=['openreview.net/Support'],
            note = openreview.api.Note(
                content={
                    'email': { 'value': 'alternate_harold@profile.org' },
                    'profile_id': { 'value':'~Harold_Last1' },
                    'comment': { 'value': 'email is wrong' }
                }
            )
        )        

        helpers.await_queue_edit(openreview_client, edit_id=edit['id'])

        publications = openreview_client.get_notes(content={ 'authorids': '~Harold_Last1'})
        assert len(publications) == 3
        assert ['~SomeFirstName_User1', '~Paul_Last1', '~Harold_Last1'] == publications[0].content['authorids']['value']
        assert '~Harold_Last1' in publications[1].writers
        assert '~Harold_Last1' in publications[1].signatures
        assert ['Harold Last', 'Test Client'] == publications[1].content['authors']['value']
        assert ['~Harold_Last1', 'test@mail.com', 'another@mail.com'] == publications[1].content['authorids']['value']
        assert ['Harold Last', 'Test Client'] == publications[2].content['authors']['value']
        assert ['~Harold_Last1', 'test@mail.com'] == publications[2].content['authorids']['value']
        assert '~Harold_Last1' in publications[2].writers
        assert '~Harold_Last1' in publications[2].signatures

        group = openreview_client.get_group('ICMLR.cc/Reviewers')
        assert 'alternate_harold@profile.org' not in group.members
        assert '~Harold_Last1' in group.members

        anon_groups = openreview_client.get_groups(prefix='ICMLR.cc/Reviewer_')
        assert len(anon_groups) == 1
        assert 'alternate_harold@profile.org' not in anon_groups[0].members
        assert '~Harold_Last1' in anon_groups[0].members
        assert anon_groups[0].id == first_anon_group_id

        profile = openreview_client.get_profile(email_or_id='~Harold_Last1')
        assert len(profile.content['emails']) == 1
        assert profile.content['emails'] == ['harold@profile.org']

        found_profiles = openreview_client.search_profiles(fullname='Harold Last', use_ES=True)
        assert len(found_profiles) == 1
        assert len(found_profiles[0].content['emails']) == 1
        assert found_profiles[0].content['emails'] == ['harold@profile.org']        

        with pytest.raises(openreview.OpenReviewException, match=r'Group Not Found: alternate_harold@profile.org'):
            openreview_client.get_group('alternate_harold@profile.org')

        assert openreview_client.get_group('~Harold_Last1').members == ['harold@profile.org']
        assert openreview_client.get_group('harold@profile.org').members == ['~Harold_Last1']

    def test_remove_email_from_merged_profile(self, openreview_client, helpers):

        tidus_client = helpers.create_user('tidus@profile.org', 'Tidus', 'Mondragon', alternates=[], institution='google.com')

        profile = tidus_client.get_profile()
        profile.content['homepage'] = 'https://carlos.google.com'

        tidus_client.post_profile(profile)

        helpers.create_user('tidus_two@profile.org', 'Tidus', 'Chapa', alternates=[], institution='deepmind.com')

        openreview_client.merge_profiles('~Tidus_Mondragon1', '~Tidus_Chapa1')

        edit = openreview_client.post_note_edit(
            invitation = 'openreview.net/Support/-/Profile_Email_Removal',
            signatures=['openreview.net/Support'],
            note = openreview.api.Note(
                content={
                    'email': { 'value': 'tidus_two@profile.org' },
                    'profile_id': { 'value':'~Tidus_Mondragon1' },
                    'comment': { 'value': 'email is silly' }
                }
            )
        )

        helpers.await_queue_edit(openreview_client, edit_id=edit['id'])

        profile = tidus_client.get_profile()

        tidus_client.post_profile(profile)

    def test_update_relation_after_signup(self, helpers):

        carlos_client = helpers.create_user('carlos@profile.org', 'Carlos', 'Last', alternates=[], institution='google.com')

        profile = carlos_client.get_profile()

        profile.content['homepage'] = 'https://carlos.google.com'
        profile.content['relations'].append({
            'relation': 'Advisor',
            'name': 'Zoey User',
            'email': 'zoey@mail.com',
            'start': 2015,
            'end': None
        })
        carlos_client.post_profile(profile)
        profile = carlos_client.get_profile(email_or_id='~Carlos_Last1')
        assert len(profile.content['names']) == 1
        assert 'username' in profile.content['names'][0]
        assert 'username' not in profile.content['relations'][0]
        assert profile.content['relations'][0]['email'] == 'zoey@mail.com'
        
        client = openreview.Client(baseurl = 'http://localhost:3001')
        client.register_user(email = 'zoey@mail.com', fullname = 'Zoey User', password = helpers.strong_password)

        profile = carlos_client.get_profile(email_or_id='~Carlos_Last1')
        assert len(profile.content['names']) == 1
        assert 'username' in profile.content['names'][0]
        assert 'username' not in profile.content['relations'][0]
        assert profile.content['relations'][0]['email'] == 'zoey@mail.com'

        profile_content={
            'names': [
                    {
                        'fullname': 'Zoey User',
                        'username': '~Zoey_User1',
                        'preferred': True
                    }
                ],
            'emails': ['zoey@mail.com'],
            'preferredEmail': 'zoey@mail.com',
            'homepage': f"https://zoeyuser{int(time.time())}.openreview.net",
            'history': [
                {
                    'position': 'PhD Student',
                    'start': 2015,
                    'end': None,
                    'institution': {
                        'country': 'US',
                        'domain': 'google.com',
                        'name': 'Google'
                    }
                }
            ],
        }
        client.activate_user('zoey@mail.com', profile_content)

        time.sleep(2)

        profile = carlos_client.get_profile(email_or_id='~Carlos_Last1')
        assert len(profile.content['names']) == 1
        assert 'username' in profile.content['names'][0]
        assert 'username' in profile.content['relations'][0]
        assert profile.content['relations'][0]['username'] == '~Zoey_User1'
        assert 'email' not in profile.content['relations'][0]

    def test_anonymous_preprint_server(self, openreview_client, helpers):

        clara_client = helpers.create_user('clara@profile.org', 'Clara', 'Last', alternates=[], institution='google.com')

        edit = clara_client.post_note_edit(
            invitation='openreview.net/Anonymous_Preprint/-/Submission',
            signatures=['~Clara_Last1'],
            note = openreview.api.Note(
                content = {
                    'title': { 'value': 'Paper title 1' },
                    'authors': { 'value': ['Clara Last', 'Test Client'] },
                    'authorids': { 'value': ['~Clara_Last1', 'test@mail.com'] },
                    'keywords': { 'value': ['data', 'mining']},
                    'TLDR': { 'value': 'TL;DR'},
                    'pdf': {'value': '/pdf/' + 'p' * 40 +'.pdf' },
                    'abstract': { 'value': 'Paper abstract' },
                },
                license = 'CC BY-SA 4.0'   
            )                         
        )

        helpers.await_queue_edit(openreview_client, edit_id=edit['id'])

        messages = openreview_client.get_messages(to='clara@profile.org', subject='Anonymous Preprint Server has received your submission titled Paper title 1')
        assert len(messages) == 1
        assert messages[0]['content']['text'] == f'''Your submission to the Anonymous Preprint Server has been posted.\n\nSubmission Number: 1\n\nTitle: Paper title 1 \n\nAbstract: Paper abstract\n\nTo view your submission, click here: https://openreview.net/forum?id={edit['note']['id']}'''        

        messages = openreview_client.get_messages(to='test@mail.com', subject='Anonymous Preprint Server has received your submission titled Paper title 1')
        assert len(messages) == 1
        assert messages[0]['content']['text'] == f'''Your submission to the Anonymous Preprint Server has been posted.\n\nSubmission Number: 1\n\nTitle: Paper title 1 \n\nAbstract: Paper abstract\n\nTo view your submission, click here: https://openreview.net/forum?id={edit['note']['id']}\n\nIf you are not an author of this submission and would like to be removed, please contact the author who added you at clara@profile.org'''        

        ## Enable comment invitation
        openreview_client.post_invitation_edit(
            invitations='openreview.net/Anonymous_Preprint/-/Comment',
            signatures=['openreview.net/Anonymous_Preprint'],
            content={
                'noteNumber': { 'value': 1 },
                'noteId': { 'value': edit['note']['id'] }
            }
        )

        assert openreview_client.get_invitation('openreview.net/Anonymous_Preprint/Submission1/-/Comment')


        edit = clara_client.post_note_edit(
            invitation='openreview.net/Anonymous_Preprint/Submission1/-/Comment',
            signatures=['openreview.net/Anonymous_Preprint/Submission1/Authors'],
            note = openreview.api.Note(
                replyto = edit['note']['id'],
                content = {
                    'comment': { 'value': 'more details about our submission' },
                }   
            )                         
        )

        helpers.await_queue_edit(openreview_client, edit_id=edit['id'])

        messages = openreview_client.get_messages(to='test@mail.com', subject='[Anonymous Preprint Server] An author commented on your submission. Paper Title: "Paper title 1"')
        assert len(messages) == 1
        assert messages[0]['content']['text'] == f'''An author commented on your submission.\n    \nPaper number: 1\n\nPaper title: Paper title 1\n\nComment: more details about our submission\n\nTo view the comment, click here: https://openreview.net/forum?id={edit['note']['forum']}&noteId={edit['note']['id']}'''        


        carlos_client = openreview.api.OpenReviewClient(username='carlos@profile.org', password=helpers.strong_password)

        edit = carlos_client.post_note_edit(
            invitation='openreview.net/Anonymous_Preprint/Submission1/-/Comment',
            signatures=['~Carlos_Last1'],
            note = openreview.api.Note(
                replyto = edit['note']['id'],
                content = {
                    'comment': { 'value': 'could you clarify more?' },
                }   
            )                         
        )

        helpers.await_queue_edit(openreview_client, edit_id=edit['id'])

        messages = openreview_client.get_messages(subject='[Anonymous Preprint Server] Carlos Last commented on your submission. Paper Title: "Paper title 1"')
        assert len(messages) == 2


    def test_confirm_alternate_email(self, openreview_client, helpers, request_page, selenium):

        xukun_client = helpers.create_user('xukun@profile.org', 'Xukun', 'First', alternates=[], institution='google.com')

        profile = xukun_client.get_profile()
        profile.content['homepage'] = 'https://xukun.com'
        profile.content['emails'].append('xukun@gmail.com')
        xukun_client.post_profile(profile)

        response = xukun_client.confirm_alternate_email('~Xukun_First1', 'xukun@gmail.com')

        ## As guest user
        guest_client = openreview.api.OpenReviewClient(baseurl = 'http://localhost:3001')
        with pytest.raises(openreview.OpenReviewException, match=r'Guest user must pass activation token'):
            guest_client.activate_email_with_token('xukun@gmail.com', '000000')

        ## As super user
        with pytest.raises(openreview.OpenReviewException, match=r'Token is not valid'):
            openreview_client.activate_email_with_token('xukun@gmail.com', '000000')            
    
        ## As owner of the profile
        xukun_client.activate_email_with_token('xukun@gmail.com', '000000')
        
        profile = xukun_client.get_profile()
        assert profile.content['emailsConfirmed'] == ['xukun@profile.org', 'xukun@gmail.com']

        ## create a group and try to confirm
        openreview_client.add_members_to_group('ICMLR.cc/Reviewers', 'xukun@yahoo.com')

        response = xukun_client.confirm_alternate_email('~Xukun_First1', 'xukun@yahoo.com')

        xukun_client.activate_email_with_token('xukun@yahoo.com', '000000')       
    
    def test_merge_profiles_automatically(self, openreview_client, helpers, request_page, selenium):

        akshat_client_1 = helpers.create_user('akshat_1@profile.org', 'Akshat', 'First', alternates=[], institution='google.com')
        akshat_client_2 = helpers.create_user('akshat_2@profile.org', 'Akshat', 'Last', alternates=[], institution='google.com')

        profile = akshat_client_1.get_profile()
        profile.content['homepage'] = 'https://akshat.google.com'
        profile.content['emails'].append('akshat_2@profile.org')
        akshat_client_1.post_profile(profile)
    
        akshat_client_1.post_profile(profile)
        
        response = akshat_client_1.confirm_alternate_email('~Akshat_First1', 'akshat_2@profile.org')

        messages = openreview_client.get_messages(subject='OpenReview Account Linking - Duplicate Profile Found', to='akshat_2@profile.org')
        assert len(messages) == 1

        ## As guest user
        guest_client = openreview.api.OpenReviewClient(baseurl = 'http://localhost:3001')
        with pytest.raises(openreview.OpenReviewException, match=r'Guest user must pass activation token'):
            guest_client.activate_email_with_token('akshat_2@profile.org', '000000')

        ## As super user
        with pytest.raises(openreview.OpenReviewException, match=r'Make sure you are logged in as Akshat First to confirm akshat_2@profile.org and finish the merge process'):
            openreview_client.activate_email_with_token('akshat_2@profile.org', '000000')

        ## As the other user        
        with pytest.raises(openreview.OpenReviewException, match=r'Make sure you are logged in as Akshat First to confirm akshat_2@profile.org and finish the merge process'):
            akshat_client_2.activate_email_with_token('akshat_2@profile.org', '000000')

        ## As the owner of the profile
        akshat_client_1.activate_email_with_token('akshat_2@profile.org', '000000')

        profile = akshat_client_1.get_profile()
        assert profile.content['emailsConfirmed'] == ['akshat_1@profile.org', 'akshat_2@profile.org']
        assert len(profile.content['names']) == 2
        assert profile.content['names'][0]['username'] == '~Akshat_First1'
        assert profile.content['names'][1]['username'] == '~Akshat_Last1'

        ## As the owner of the profile again
        with pytest.raises(openreview.OpenReviewException, match=r'Token is not valid'):
            akshat_client_1.activate_email_with_token('akshat_2@profile.org', '000000')

    def test_confirm_email_for_inactive_profile(self, openreview_client, helpers, request_page, selenium):
        
        guest = openreview.api.OpenReviewClient()
        res = guest.register_user(email = 'confirm_alternate@mail.com', fullname= 'Lionel Messi', password = helpers.strong_password)

        guest.confirm_alternate_email(profile_id='~Lionel_Messi1', alternate_email='messi@mail.com', activation_token='confirm_alternate@mail.com')

        messages = openreview_client.get_messages(subject='OpenReview Email Confirmation', to='messi@mail.com')
        assert len(messages) == 1

        guest.activate_email_with_token(email='messi@mail.com', token='000000', activation_token='confirm_alternate@mail.com')

        profile = openreview_client.get_profile(email_or_id='~Lionel_Messi1')
        assert len(profile.content['emails']) == 2
        assert len(profile.content['emailsConfirmed']) == 2

        profile_content={
            'names': [
                    {
                        'fullname': 'Lionel Messi',
                        'username': '~Lionel_Messi1',
                        'preferred': True
                    }
                ],
            'emails': ['confirm_alternate@mail.com', 'messi@mail.com'],
            'preferredEmail': 'messi@mail.com',
            'homepage': f"https://lionelmessi{int(time.time())}.openreview.net",
        }
        profile_content['history'] = [{
            'position': 'PhD Student',
            'start': 2017,
            'end': None,
            'institution': {
                'country': 'US',
                'domain': 'google.com',
            }
        }]
        res = guest.activate_user('confirm_alternate@mail.com', profile_content)

        profile = openreview_client.get_profile(email_or_id='~Lionel_Messi1')
        assert len(profile.content['emails']) == 2
        assert len(profile.content['emailsConfirmed']) == 2
        assert profile.state == 'Active Automatic'        


    def test_post_tag_for_blocked_profile(self, openreview_client, helpers):
        
        helpers.create_user('lina@profile.org', 'Lina', 'First', alternates=[], institution='google.com')

        openreview_client.moderate_profile('~Lina_First1', 'block')

        tag = openreview_client.post_tag(
            openreview.api.Tag(
                invitation='openreview.net/Support/-/Profile_Blocked_Status',
                signature='openreview.net/Support',
                profile='~Lina_First1',
                label='Impersonating Paul MacCartney',
                readers=['openreview.net/Support'],
            )
        )

        helpers.await_queue_edit(openreview_client, edit_id=tag.id)