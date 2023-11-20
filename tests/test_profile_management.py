from __future__ import absolute_import, division, print_function, unicode_literals

import openreview
import datetime
from openreview import ProfileManagement
from openreview.api import OpenReviewClient
from openreview.api import Note
from openreview.journal import Journal
from openreview.venue import Venue
import pytest

class TestProfileManagement():

    
    @pytest.fixture(scope="class")
    def profile_management(self, client, openreview_client):
        profile_management = ProfileManagement(client, 'openreview.net')
        profile_management.setup()
        return profile_management
    
    def test_import_dblp_notes(self, client, profile_management, test_client, helpers):

        note = test_client.post_note(
            openreview.Note(
                invitation='dblp.org/-/record',
                readers=['everyone'],
                writers=['dblp.org'],
                signatures=['~SomeFirstName_User1'],
                content={
                    'dblp': '<article key=\"journals/iotj/WangJWSGZ23\" mdate=\"2023-04-16\">\n<author orcid=\"0000-0003-4015-0348\" pid=\"188/7759-93\">Chao Wang 0093</author>\n<author orcid=\"0000-0002-3703-121X\" pid=\"00/8334\">Chunxiao Jiang</author>\n<author orcid=\"0000-0003-3170-8952\" pid=\"62/2631-1\">Jingjing Wang 0001</author>\n<author orcid=\"0000-0002-7558-5379\" pid=\"66/800\">Shigen Shen</author>\n<author orcid=\"0000-0001-9831-2202\" pid=\"01/267-1\">Song Guo 0001</author>\n<author orcid=\"0000-0002-0990-5581\" pid=\"24/9047\">Peiying Zhang</author>\n<title>Blockchain-Aided Network Resource Orchestration in Intelligent Internet of Things.</title>\n<pages>6151-6163</pages>\n<year>2023</year>\n<month>April 1</month>\n<volume>10</volume>\n<journal>IEEE Internet Things J.</journal>\n<number>7</number>\n<ee>https://doi.org/10.1109/JIOT.2022.3222911</ee>\n<url>db/journals/iotj/iotj10.html#WangJWSGZ23</url>\n</article>'
                }
            )
        )

        helpers.await_queue()

        note = test_client.get_note(note.id)
        assert note.content['title'] == 'Blockchain-Aided Network Resource Orchestration in Intelligent Internet of Things'
        assert datetime.datetime.fromtimestamp(note.cdate/1000).year == 2023
        assert datetime.datetime.fromtimestamp(note.cdate/1000).month == 4

        note = test_client.post_note(
            openreview.Note(
                invitation='dblp.org/-/record',
                readers=['everyone'],
                writers=['dblp.org'],
                signatures=['~SomeFirstName_User1'],
                content={
                    'dblp': '<article key=\"journals/iotj/WittHTSL23\" mdate=\"2023-02-25\">\n<author orcid=\"0000-0002-9984-3213\" pid=\"295/9513\">Leon Witt</author>\n<author pid=\"320/8197\">Mathis Heyer</author>\n<author orcid=\"0000-0002-6233-3121\" pid=\"45/10835\">Kentaroh Toyoda</author>\n<author orcid=\"0000-0002-6283-3265\" pid=\"79/9736\">Wojciech Samek</author>\n<author orcid=\"0000-0002-7581-8865\" pid=\"48/4185-1\">Dan Li 0001</author>\n<title>Decentral and Incentivized Federated Learning Frameworks: A Systematic Literature Review.</title>\n<pages>3642-3663</pages>\n<year>2023</year>\n<month>February 15</month>\n<volume>10</volume>\n<journal>IEEE Internet Things J.</journal>\n<number>4</number>\n<ee>https://doi.org/10.1109/JIOT.2022.3231363</ee>\n<url>db/journals/iotj/iotj10.html#WittHTSL23</url>\n</article>'
                }
            )
        )


        helpers.await_queue()

        note = test_client.get_note(note.id)
        assert note.content['title'] == 'Decentral and Incentivized Federated Learning Frameworks: A Systematic Literature Review'
        assert datetime.datetime.fromtimestamp(note.cdate/1000).year == 2023
        assert datetime.datetime.fromtimestamp(note.cdate/1000).month == 2                

   
    def test_remove_alternate_name(self, client, openreview_client, profile_management, test_client, helpers):

        john_client_v2 = helpers.create_user('john@profile.org', 'John', 'Last', alternates=[], institution='google.com')
        john_client = openreview.Client(username='john@profile.org', password=helpers.strong_password)

        profile = john_client.get_profile()

        profile.content['homepage'] = 'https://google.com'
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
        
        assert client.get_group('~John_Last1').members == ['john@profile.org']
        assert client.get_group('john@profile.org').members == ['~John_Last1', '~John_Alternate_Last1']
        assert client.get_group('~John_Alternate_Last1').members == ['john@profile.org']

        ## Try to remove the unexisting name and get an error
        with pytest.raises(openreview.OpenReviewException, match=r'Profile not found for ~John_Lasst1'):
            request_note = john_client.post_note(openreview.Note(
                invitation='openreview.net/Support/-/Profile_Name_Removal',
                readers=['openreview.net/Support', '~John_Last1'],
                writers=['openreview.net/Support'],
                signatures=['~John_Last1'],
                content={
                    'name': 'John Last',
                    'usernames': ['~John_Lasst1'],
                    'comment': 'typo in my name',
                    'status': 'Pending'
                }
            ))

        ## Try to remove the name that is marked as preferred and get an error
        with pytest.raises(openreview.OpenReviewException, match=r'Can not remove preferred name'):
            request_note = john_client.post_note(openreview.Note(
                invitation='openreview.net/Support/-/Profile_Name_Removal',
                readers=['openreview.net/Support', '~John_Last1'],
                writers=['openreview.net/Support'],
                signatures=['~John_Last1'],
                content={
                    'name': 'John Last',
                    'usernames': ['~John_Last1'],
                    'comment': 'typo in my name',
                    'status': 'Pending'
                }
            )) 

        ## Try to remove the name that doesn't match with the username and get an error
        with pytest.raises(openreview.OpenReviewException, match=r'Name does not match with username'):
            request_note = john_client.post_note(openreview.Note(
                invitation='openreview.net/Support/-/Profile_Name_Removal',
                readers=['openreview.net/Support', '~John_Last1'],
                writers=['openreview.net/Support'],
                signatures=['~John_Last1'],
                content={
                    'name': 'Melisa Bok',
                    'usernames': ['~John_Alternate_Last1'],
                    'comment': 'typo in my name',
                    'status': 'Pending'
                }
            ))                    


        ## Add publications
        john_client_v2.post_note_edit(
            invitation='openreview.net/Archive/-/Direct_Upload',
            signatures=['~John_Alternate_Last1'],
            note = openreview.api.Note(
                content = {
                    'title': { 'value': 'Paper title 1' },
                    'abstract': { 'value': 'Paper abstract 1' },
                    'authors': { 'value': ['John Alternate Last', 'Test Client'] },
                    'authorids': { 'value': ['~John_Alternate_Last1', 'test@mail.com'] },
                    'venue': { 'value': 'Arxiv' },
                    'year': { 'value': 2019 }
                }
        ))            

        john_client_v2.post_note_edit(
            invitation='openreview.net/Archive/-/Direct_Upload',
            signatures=['~John_Alternate_Last1'],
            note = openreview.api.Note(
                content = {
                    'title': { 'value': 'Paper title 2' },
                    'abstract': { 'value': 'Paper abstract 2' },
                    'authors': { 'value': ['John Alternate Last', 'Test Client'] },
                    'authorids': { 'value': ['~John_Alternate_Last1', 'test@mail.com', 'another@mail.com'] },
                    'venue': { 'value': 'Arxiv' },
                    'year': { 'value': 2019 }
                }
        )) 

        ## Create committee groups
        client.post_group(openreview.Group(
            id='ICLRR.cc',
            readers=['everyone'],
            writers=['ICLRR.cc'],
            signatures=['~Super_User1'],
            signatories=[],
            members=[]
        ))

        client.post_group(openreview.Group(
            id='ICLRR.cc/Reviewers',
            readers=['everyone'],
            writers=['ICLRR.cc'],
            signatures=['~Super_User1'],
            signatories=[],
            members=['~John_Alternate_Last1'],
            anonids=True
        ))

        anon_groups = client.get_groups(regex='ICLRR.cc/Reviewer_')
        assert len(anon_groups) == 1
        assert '~John_Alternate_Last1' in anon_groups[0].members
        first_anon_group_id = anon_groups[0].id                

        publications = john_client_v2.get_notes(content={ 'authorids': '~John_Last1'})
        assert len(publications) == 2

        request_note = john_client.post_note(openreview.Note(
            invitation='openreview.net/Support/-/Profile_Name_Removal',
            readers=['openreview.net/Support', '~John_Last1'],
            writers=['openreview.net/Support'],
            signatures=['~John_Last1'],
            content={
                'name': 'John Alternate Last',
                'usernames': ['~John_Alternate_Last1'],
                'comment': 'typo in my name',
                'status': 'Pending'
            }

        ))

        helpers.await_queue()

        messages = client.get_messages(to='john@profile.org', subject='Profile name removal request has been received')
        assert len(messages) == 1
        assert messages[0]['content']['text'] == '''Hi John Last,

We have received your request to remove the name "John Alternate Last" from your profile: https://openreview.net/profile?id=~John_Last1.

We will evaluate your request and you will receive another email with the request status.

Thanks,

The OpenReview Team.
'''

        ## Accept the request
        decision_note = client.post_note(openreview.Note(
            referent=request_note.id,
            invitation='openreview.net/Support/-/Profile_Name_Removal_Decision',
            readers=['openreview.net/Support'],
            writers=['openreview.net/Support'],
            signatures=['openreview.net/Support'],
            content={
                'status': 'Accepted'
            }

        ))

        helpers.await_queue()

        note = john_client.get_note(request_note.id)
        assert note.content['status'] == 'Accepted'

        publications = john_client_v2.get_notes(content={ 'authorids': '~John_Last1'})
        assert len(publications) == 2
        assert '~John_Last1' in publications[0].writers
        assert '~John_Last1' in publications[0].signatures
        assert ['John Last', 'Test Client'] == publications[0].content['authors']['value']
        assert ['~John_Last1', 'test@mail.com', 'another@mail.com'] == publications[0].content['authorids']['value']
        assert '~John_Last1' in publications[1].writers
        assert '~John_Last1' in publications[1].signatures

        group = client.get_group('ICLRR.cc/Reviewers')
        assert '~John_Alternate_Last1' not in group.members
        assert '~John_Last1' in group.members

        anon_groups = client.get_groups(regex='ICLRR.cc/Reviewer_')
        assert len(anon_groups) == 1
        assert '~John_Alternate_Last1' not in anon_groups[0].members
        assert '~John_Last1' in anon_groups[0].members
        assert anon_groups[0].id == first_anon_group_id

        profile = john_client.get_profile(email_or_id='~John_Last1')
        assert len(profile.content['names']) == 1
        assert 'username' in profile.content['names'][0]
        assert profile.content['names'][0]['username'] == '~John_Last1'

        found_profiles = client.search_profiles(fullname='John Last', use_ES=True)
        assert len(found_profiles) == 1
        assert len(found_profiles[0].content['names']) == 1
        assert 'username' in found_profiles[0].content['names'][0]
        assert found_profiles[0].content['names'][0]['username'] == '~John_Last1'        

        with pytest.raises(openreview.OpenReviewException, match=r'Group Not Found: ~John_Alternate_Last1'):
            client.get_group('~John_Alternate_Last1')

        assert client.get_group('~John_Last1').members == ['john@profile.org']
        assert client.get_group('john@profile.org').members == ['~John_Last1']

        messages = client.get_messages(to='john@profile.org', subject='Profile name removal request has been accepted')
        assert len(messages) == 1
        assert messages[0]['content']['text'] == '''Hi John Last,

We have received your request to remove the name "John Alternate Last" from your profile: https://openreview.net/profile?id=~John_Last1.

The name has been removed from your profile. Please check that the information listed in your profile is correct.

Thanks,

The OpenReview Team.
'''

    def test_remove_name_and_rename_profile_id(self, client, openreview_client, helpers):

        ana_client_v2 = helpers.create_user('ana@profile.org', 'Ana', 'Last', alternates=[], institution='google.com')
        ana_client = openreview.Client(username='ana@profile.org', password=helpers.strong_password)

        profile = ana_client.get_profile()

        profile.content['homepage'] = 'https://google.com'
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

        assert client.get_group('~Ana_Last1').members == ['ana@profile.org']
        assert client.get_group('ana@profile.org').members == ['~Ana_Last1', '~Ana_Alternate_Last1']
        assert client.get_group('~Ana_Alternate_Last1').members == ['ana@profile.org']        

        ## Try to remove the name that is marked as preferred an get an error
        with pytest.raises(openreview.OpenReviewException, match=r'Can not remove preferred name'):
            request_note = ana_client.post_note(openreview.Note(
                invitation='openreview.net/Support/-/Profile_Name_Removal',
                readers=['openreview.net/Support', '~Ana_Alternate_Last1'],
                writers=['openreview.net/Support'],
                signatures=['~Ana_Alternate_Last1'],
                content={
                    'name': 'Ana Alternate Last',
                    'usernames': ['~Ana_Alternate_Last1'],
                    'comment': 'typo in my name',
                    'status': 'Pending'
                }
            ))        


        ## Add publications
        ana_client_v2.post_note_edit(
            invitation='openreview.net/Archive/-/Direct_Upload',
            signatures=['~Ana_Last1'],
            note = openreview.api.Note(
                content = {
                    'title': { 'value': 'Paper title 1' },
                    'abstract': { 'value': 'Paper abstract 1' },
                    'authors': { 'value': ['Ana Last', 'Test Client'] },
                    'authorids': { 'value': ['~Ana_Last1', 'test@mail.com'] },
                    'venue': { 'value': 'Arxiv' },
                    'year': { 'value': 2019 }
                }
        ))        

        ana_client_v2.post_note_edit(
            invitation='openreview.net/Archive/-/Direct_Upload',
            signatures=['~Ana_Last1'],
            note = openreview.api.Note(
                content = {
                    'title': { 'value': 'Paper title 2' },
                    'abstract': { 'value': 'Paper abstract 2' },
                    'authors': { 'value': ['Ana Last', 'Test Client'] },
                    'authorids': { 'value': ['~Ana_Last1', 'test@mail.com'] },
                    'venue': { 'value': 'Arxiv' },
                    'year': { 'value': 2019 }
                }
        ))        

        publications = openreview_client.get_notes(content={ 'authorids': '~Ana_Alternate_Last1'})
        assert len(publications) == 2

        request_note = ana_client.post_note(openreview.Note(
            invitation='openreview.net/Support/-/Profile_Name_Removal',
            readers=['openreview.net/Support', '~Ana_Alternate_Last1'],
            writers=['openreview.net/Support'],
            signatures=['~Ana_Alternate_Last1'],
            content={
                'name': 'Ana Last',
                'usernames': ['~Ana_Last1'],
                'comment': 'typo in my name',
                'status': 'Pending'
            }

        ))

        helpers.await_queue()

        messages = client.get_messages(to='ana@profile.org', subject='Profile name removal request has been received')
        assert len(messages) == 1
        assert messages[0]['content']['text'] == '''Hi Ana Alternate Last,

We have received your request to remove the name "Ana Last" from your profile: https://openreview.net/profile?id=~Ana_Alternate_Last1.

We will evaluate your request and you will receive another email with the request status.

Thanks,

The OpenReview Team.
'''

        ## Accept the request
        decision_note = client.post_note(openreview.Note(
            referent=request_note.id,
            invitation='openreview.net/Support/-/Profile_Name_Removal_Decision',
            readers=['openreview.net/Support'],
            writers=['openreview.net/Support'],
            signatures=['openreview.net/Support'],
            content={
                'status': 'Accepted'
            }

        ))

        helpers.await_queue()

        ana_client = openreview.Client(username='ana@profile.org', password=helpers.strong_password)
        note = ana_client.get_note(request_note.id)
        assert note.content['status'] == 'Accepted'

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

        found_profiles = client.search_profiles(fullname='Ana Last', use_ES=True)
        assert len(found_profiles) == 1
        assert len(found_profiles[0].content['names']) == 1
        assert 'username' in found_profiles[0].content['names'][0]
        assert found_profiles[0].content['names'][0]['username'] == '~Ana_Alternate_Last1'        

        with pytest.raises(openreview.OpenReviewException, match=r'Group Not Found: ~Ana_Last1'):
            client.get_group('~Ana_Last1')

        assert client.get_group('ana@profile.org').members == ['~Ana_Alternate_Last1']
        assert client.get_group('~Ana_Alternate_Last1').members == ['ana@profile.org']              

        messages = client.get_messages(to='ana@profile.org', subject='Profile name removal request has been accepted')
        assert len(messages) == 1
        assert messages[0]['content']['text'] == '''Hi Ana Alternate Last,

We have received your request to remove the name "Ana Last" from your profile: https://openreview.net/profile?id=~Ana_Alternate_Last1.

The name has been removed from your profile. Please check that the information listed in your profile is correct.

Thanks,

The OpenReview Team.
'''

    def test_request_remove_name_and_decline(self, client, helpers):

        peter_client_v2 = helpers.create_user('peter@profile.org', 'Peter', 'Last', alternates=[], institution='google.com')
        peter_client = openreview.Client(username='peter@profile.org', password=helpers.strong_password)

        profile = peter_client.get_profile()

        profile.content['homepage'] = 'https://google.com'
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

        peter_client_v2.post_note_edit(
            invitation='openreview.net/Archive/-/Direct_Upload',
            signatures=['~Peter_Alternate_Last1'],
            note = openreview.api.Note(
                content = {
                    'title': { 'value': 'Paper title 1' },
                    'abstract': { 'value': 'Paper abstract 1' },
                    'authors': { 'value': ['Peter Alternate Last', 'Test Client'] },
                    'authorids': { 'value': ['~Peter_Alternate_Last1', 'test@mail.com'] },
                    'venue': { 'value': 'Arxiv' },
                    'year': { 'value': 2019 }
                }
        ))                      

        request_note = peter_client.post_note(openreview.Note(
            invitation='openreview.net/Support/-/Profile_Name_Removal',
            readers=['openreview.net/Support', '~Peter_Last1'],
            writers=['openreview.net/Support'],
            signatures=['~Peter_Last1'],
            content={
                'name': 'Peter Alternate Last',
                'usernames': ['~Peter_Alternate_Last1'],
                'comment': 'typo in my name',
                'status': 'Pending'
            }

        ))

        helpers.await_queue()

        messages = client.get_messages(to='peter@profile.org', subject='Profile name removal request has been received')
        assert len(messages) == 1
        assert messages[0]['content']['text'] == '''Hi Peter Last,

We have received your request to remove the name "Peter Alternate Last" from your profile: https://openreview.net/profile?id=~Peter_Last1.

We will evaluate your request and you will receive another email with the request status.

Thanks,

The OpenReview Team.
'''

        ## Decline the request
        decision_note = client.post_note(openreview.Note(
            referent=request_note.id,
            invitation='openreview.net/Support/-/Profile_Name_Removal_Decision',
            readers=['openreview.net/Support'],
            writers=['openreview.net/Support'],
            signatures=['openreview.net/Support'],
            content={
                'status': 'Rejected',
                'support_comment': 'Name the is left is not descriptive'
            }

        ))

        helpers.await_queue()

        note = peter_client.get_note(request_note.id)
        assert note.content['status'] == 'Rejected'

        messages = client.get_messages(to='peter@profile.org', subject='Profile name removal request has been rejected')
        assert len(messages) == 1
        assert messages[0]['content']['text'] == '''Hi Peter Last,

We have received your request to remove the name "Peter Alternate Last" from your profile: https://openreview.net/profile?id=~Peter_Last1.

We can not remove the name from the profile for the following reason:

Name the is left is not descriptive

Regards,

The OpenReview Team.
'''

    def test_remove_name_from_merged_profile(self, client, openreview_client, profile_management, helpers):

        ella_client_v2 = helpers.create_user('ella@profile.org', 'Ella', 'Last', alternates=[], institution='google.com')
        ella_client = openreview.Client(username='ella@profile.org', password=helpers.strong_password)

        profile = ella_client.get_profile()

        profile.content['homepage'] = 'https://google.com'
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

        assert client.get_group('~Ella_Last1').members == ['ella@profile.org']
        assert client.get_group('ella@profile.org').members == ['~Ella_Last1', '~Ella_Alternate_Last1']
        assert client.get_group('~Ella_Alternate_Last1').members == ['ella@profile.org']        

        ## Add publications
        ella_client_v2.post_note_edit(
            invitation='openreview.net/Archive/-/Direct_Upload',
            signatures=['~Ella_Last1'],
            note = openreview.api.Note(
                content = {
                    'title': { 'value': 'Paper title 2' },
                    'abstract': { 'value': 'Paper abstract 2' },
                    'authors': { 'value': ['Ella Last', 'Test Client'] },
                    'authorids': { 'value': ['~Ella_Last1', 'test@mail.com'] },
                    'venue': { 'value': 'Arxiv' },
                    'year': { 'value': 2019 }
                }
        ))         

        publications = openreview_client.get_notes(content={ 'authorids': '~Ella_Last1'})
        assert len(publications) == 1


        ella_client_2_v2 = helpers.create_user('ella_two@profile.org', 'Ella', 'Last', alternates=[], institution='deepmind.com')
        ella_client_2 = openreview.Client(username='ella_two@profile.org', password=helpers.strong_password)

        profile = ella_client_2.get_profile()
        assert '~Ella_Last2' == profile.id

        assert client.get_group('~Ella_Last2').members == ['ella_two@profile.org']
        assert client.get_group('ella_two@profile.org').members == ['~Ella_Last2']

        ella_client_2_v2.post_note_edit(
            invitation='openreview.net/Archive/-/Direct_Upload',
            signatures=['~Ella_Last2'],
            note = openreview.api.Note(
                content = {
                    'title': { 'value': 'Paper title 2' },
                    'abstract': { 'value': 'Paper abstract 2' },
                    'authors': { 'value': ['Ella Last', 'Test Client'] },
                    'authorids': { 'value': ['~Ella_Last2', 'test@mail.com'] },
                    'venue': { 'value': 'Arxiv' },
                    'year': { 'value': 2019 }
                }
        ))

        publications = openreview_client.get_notes(content={ 'authorids': '~Ella_Last2'})
        assert len(publications) == 1


        client.merge_profiles('~Ella_Last1', '~Ella_Last2')
        profile = ella_client.get_profile()
        assert len(profile.content['names']) == 3
        profile.content['names'][0]['username'] == '~Ella_Last1'
        profile.content['names'][0]['preferred'] == True
        profile.content['names'][1]['username'] == '~Ella_Alternate_Last1'
        profile.content['names'][2]['username'] == '~Ella_Last2'

        found_profiles = client.search_profiles(fullname='Ella Last', use_ES=True)
        assert len(found_profiles) == 1
        assert len(found_profiles[0].content['names']) == 3

        assert client.get_group('~Ella_Last1').members == ['ella@profile.org', 'ella_two@profile.org']
        assert client.get_group('~Ella_Last2').members == ['ella_two@profile.org']
        assert client.get_group('ella@profile.org').members == ['~Ella_Last1', '~Ella_Alternate_Last1']
        assert client.get_group('ella_two@profile.org').members == ['~Ella_Last2', '~Ella_Last1']
        assert client.get_group('~Ella_Alternate_Last1').members == ['ella@profile.org']             
 
        request_note = ella_client.post_note(openreview.Note(
            invitation='openreview.net/Support/-/Profile_Name_Removal',
            readers=['openreview.net/Support', '~Ella_Last1'],
            writers=['openreview.net/Support'],
            signatures=['~Ella_Last1'],
            content={
                'name': 'Ella Last',
                'usernames': ['~Ella_Last2'],
                'comment': 'typo in my name',
                'status': 'Pending'
            }

        ))

        helpers.await_queue()

        messages = client.get_messages(to='ella@profile.org', subject='Profile name removal request has been received')
        assert len(messages) == 1
        assert messages[0]['content']['text'] == '''Hi Ella Last,

We have received your request to remove the name "Ella Last" from your profile: https://openreview.net/profile?id=~Ella_Last1.

We will evaluate your request and you will receive another email with the request status.

Thanks,

The OpenReview Team.
'''

        ## Accept the request
        decision_note = client.post_note(openreview.Note(
            referent=request_note.id,
            invitation='openreview.net/Support/-/Profile_Name_Removal_Decision',
            readers=['openreview.net/Support'],
            writers=['openreview.net/Support'],
            signatures=['openreview.net/Support'],
            content={
                'status': 'Accepted'
            }

        ))

        helpers.await_queue()

        note = ella_client.get_note(request_note.id)
        assert note.content['status'] == 'Accepted'

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

        found_profiles = client.search_profiles(fullname='Ella Alternate', use_ES=True)
        assert len(found_profiles) == 1
        assert len(found_profiles[0].content['names']) == 2        

        with pytest.raises(openreview.OpenReviewException, match=r'Group Not Found: ~Ella_Last2'):
            client.get_group('~Ella_Last2')

        assert client.get_group('~Ella_Last1').members == ['ella@profile.org', 'ella_two@profile.org']
        assert client.get_group('ella@profile.org').members == ['~Ella_Last1', '~Ella_Alternate_Last1']
        assert client.get_group('ella_two@profile.org').members == ['~Ella_Last1']
        assert client.get_group('~Ella_Alternate_Last1').members == ['ella@profile.org']            

        messages = client.get_messages(to='ella@profile.org', subject='Profile name removal request has been accepted')
        assert len(messages) == 1
        assert messages[0]['content']['text'] == '''Hi Ella Last,

We have received your request to remove the name "Ella Last" from your profile: https://openreview.net/profile?id=~Ella_Last1.

The name has been removed from your profile. Please check that the information listed in your profile is correct.

Thanks,

The OpenReview Team.
'''

    def test_remove_duplicated_name(self, client, openreview_client, profile_management, helpers):

        javier_client_v2 = helpers.create_user('javier@profile.org', 'Javier', 'Last', alternates=[], institution='google.com')
        javier_client = openreview.Client(username='javier@profile.org', password=helpers.strong_password)

        profile = javier_client.get_profile()

        profile.content['homepage'] = 'https://google.com'
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
        javier_client_v2.post_note_edit(
            invitation='openreview.net/Archive/-/Direct_Upload',
            signatures=['~Javier_Last1'],
            note = openreview.api.Note(
                content = {
                    'title': { 'value': 'Paper title 2' },
                    'abstract': { 'value': 'Paper abstract 2' },
                    'authors': { 'value': ['Javier Last', 'Test Client'] },
                    'authorids': { 'value': ['~Javier_Last1', 'test@mail.com'] },
                    'venue': { 'value': 'Arxiv' },
                    'year': { 'value': 2019 }
                }
        ))      

        publications = openreview_client.get_notes(content={ 'authorids': '~Javier_Last1'})
        assert len(publications) == 1

        javier_client_2_v2 = helpers.create_user('javier_two@profile.org', 'Javier', 'Last', alternates=[], institution='deepmind.com')
        javier_client_2 = openreview.Client(username='javier_two@profile.org', password=helpers.strong_password)
        profile = javier_client_2.get_profile()
        assert '~Javier_Last2' == profile.id

        javier_client_2_v2.post_note_edit(
            invitation='openreview.net/Archive/-/Direct_Upload',
            signatures=['~Javier_Last2'],
            note = openreview.api.Note(
                content = {
                    'title': { 'value': 'Paper title 2' },
                    'abstract': { 'value': 'Paper abstract 2' },
                    'authors': { 'value': ['Javier Last', 'Test Client'] },
                    'authorids': { 'value': ['~Javier_Last2', 'test@mail.com'] },
                    'venue': { 'value': 'Arxiv' },
                    'year': { 'value': 2019 }
                }
        ))        

        publications = openreview_client.get_notes(content={ 'authorids': '~Javier_Last2'})
        assert len(publications) == 1


        client.merge_profiles('~Javier_Last1', '~Javier_Last2')
        profile = javier_client.get_profile()
        assert len(profile.content['names']) == 3
        profile.content['names'][0]['username'] == '~Javier_Last1'
        profile.content['names'][1]['username'] == '~Javier_Alternate_Last1'
        profile.content['names'][1]['preferred'] == True
        profile.content['names'][2]['username'] == '~Javier_Last2'
    
 
        request_note = javier_client.post_note(openreview.Note(
            invitation='openreview.net/Support/-/Profile_Name_Removal',
            readers=['openreview.net/Support', '~Javier_Alternate_Last1'],
            writers=['openreview.net/Support'],
            signatures=['~Javier_Alternate_Last1'],
            content={
                'name': 'Javier Last',
                'usernames': ['~Javier_Last1', '~Javier_Last2'],
                'comment': 'typo in my name',
                'status': 'Pending'
            }

        ))

        helpers.await_queue()

        messages = client.get_messages(to='javier@profile.org', subject='Profile name removal request has been received')
        assert len(messages) == 1
        assert messages[0]['content']['text'] == '''Hi Javier Alternate Last,

We have received your request to remove the name "Javier Last" from your profile: https://openreview.net/profile?id=~Javier_Alternate_Last1.

We will evaluate your request and you will receive another email with the request status.

Thanks,

The OpenReview Team.
'''

        ## Accept the request
        decision_note = client.post_note(openreview.Note(
            referent=request_note.id,
            invitation='openreview.net/Support/-/Profile_Name_Removal_Decision',
            readers=['openreview.net/Support'],
            writers=['openreview.net/Support'],
            signatures=['openreview.net/Support'],
            content={
                'status': 'Accepted'
            }

        ))

        helpers.await_queue()

        javier_client = openreview.Client(username='javier@profile.org', password=helpers.strong_password)
        note = javier_client.get_note(request_note.id)
        assert note.content['status'] == 'Accepted'

        publications = openreview_client.get_notes(content={ 'authorids': '~Javier_Alternate_Last1'})
        assert len(publications) == 2
        assert '~Javier_Alternate_Last1' in publications[0].writers
        assert '~Javier_Alternate_Last1' in publications[0].signatures
        assert '~Javier_Alternate_Last1' in publications[1].writers
        assert '~Javier_Alternate_Last1' in publications[1].signatures


        profile = javier_client.get_profile(email_or_id='~Javier_Alternate_Last1')
        assert len(profile.content['names']) == 1
        assert profile.content['names'][0]['username'] == '~Javier_Alternate_Last1'

        found_profiles = client.search_profiles(fullname='Javier Alternate', use_ES=True)
        assert len(found_profiles) == 1
        assert len(found_profiles[0].content['names']) == 1
        assert found_profiles[0].content['names'][0]['username'] == '~Javier_Alternate_Last1'       

        with pytest.raises(openreview.OpenReviewException, match=r'Group Not Found: ~Javier_Last1'):
            client.get_group('~Javier_Last1')

        messages = client.get_messages(to='javier@profile.org', subject='Profile name removal request has been accepted')
        assert len(messages) == 1
        assert messages[0]['content']['text'] == '''Hi Javier Alternate Last,

We have received your request to remove the name "Javier Last" from your profile: https://openreview.net/profile?id=~Javier_Alternate_Last1.

The name has been removed from your profile. Please check that the information listed in your profile is correct.

Thanks,

The OpenReview Team.
'''

    def test_rename_publications_from_api2(self, client, profile_management, test_client, helpers, openreview_client):

        journal=Journal(openreview_client, 'CABJ', '1234', contact_info='cabj@mail.org', full_name='Transactions on Machine Learning Research', short_name='CABJ', submission_name='Submission')
        journal.setup(support_role='test@mail.com', editors=[])

        venue = Venue(openreview_client, 'ACMM.org/2023/Conference', 'openreview.net/Support')        
        venue.submission_stage = openreview.stages.SubmissionStage(double_blind=True, due_date=datetime.datetime.utcnow() + datetime.timedelta(minutes = 30))
        venue.setup(program_chair_ids=['venue_pc@mail.com'])
        venue.create_submission_stage()        
        
        paul_client_v2 = helpers.create_user('paul@profile.org', 'Paul', 'Last', alternates=[], institution='google.com')
        paul_client = openreview.Client(username='paul@profile.org', password=helpers.strong_password)
        profile = paul_client.get_profile()

        profile.content['homepage'] = 'https://google.com'
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

        assert client.get_group('~Paul_Last1').members == ['paul@profile.org']
        assert client.get_group('paul@profile.org').members == ['~Paul_Last1', '~Paul_Alternate_Last1']
        assert client.get_group('~Paul_Alternate_Last1').members == ['paul@profile.org']

        ## Add publications
        paul_client_v2.post_note_edit(
            invitation='openreview.net/Archive/-/Direct_Upload',
            signatures=['~Paul_Alternate_Last1'],
            note = openreview.api.Note(
                content = {
                    'title': { 'value': 'Paper title 1' },
                    'abstract': { 'value': 'Paper abstract 1' },
                    'authors': { 'value': ['Paul Alternate Last', 'Test Client'] },
                    'authorids': { 'value': ['~Paul_Alternate_Last1', 'test@mail.com'] },
                    'venue': { 'value': 'Arxiv' },
                    'year': { 'value': 2019 }
                }
        ))         
        

        paul_client_v2.post_note_edit(
            invitation='openreview.net/Archive/-/Direct_Upload',
            signatures=['~Paul_Alternate_Last1'],
            note = openreview.api.Note(
                content = {
                    'title': { 'value': 'Paper title 2' },
                    'abstract': { 'value': 'Paper abstract 2' },
                    'authors': { 'value': ['Paul Alternate Last', 'Test Client'] },
                    'authorids': { 'value': ['~Paul_Alternate_Last1', 'test@mail.com'] },
                    'venue': { 'value': 'Arxiv' },
                    'year': { 'value': 2019 }
                }
        ))         

        submission_note_1 = paul_client_v2.post_note_edit(invitation='CABJ/-/Submission',
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

        submission_note_2 = paul_client_v2.post_note_edit(invitation='CABJ/-/Submission',
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
                pdate = openreview.tools.datetime_millis(datetime.datetime.utcnow()),
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

        ## Create committee groups
        client.post_group(openreview.Group(
            id='ICLRR.cc',
            readers=['everyone'],
            writers=['ICLRR.cc'],
            signatures=['~Super_User1'],
            signatories=[],
            members=[]
        ))

        client.post_group(openreview.Group(
            id='ICLRR.cc/Reviewers',
            readers=['everyone'],
            writers=['ICLRR.cc'],
            signatures=['~Super_User1'],
            signatories=[],
            members=['~Paul_Alternate_Last1']
        ))        

        publications = openreview_client.get_notes(content={ 'authorids': '~Paul_Last1'})
        assert len(publications) == 5

        request_note = paul_client.post_note(openreview.Note(
            invitation='openreview.net/Support/-/Profile_Name_Removal',
            readers=['openreview.net/Support', '~Paul_Last1'],
            writers=['openreview.net/Support'],
            signatures=['~Paul_Last1'],
            content={
                'name': 'Paul Alternate Last',
                'usernames': ['~Paul_Alternate_Last1'],
                'comment': 'typo in my name',
                'status': 'Pending'
            }

        ))

        helpers.await_queue()

        messages = client.get_messages(to='paul@profile.org', subject='Profile name removal request has been received')
        assert len(messages) == 1
        assert messages[0]['content']['text'] == '''Hi Paul Last,

We have received your request to remove the name "Paul Alternate Last" from your profile: https://openreview.net/profile?id=~Paul_Last1.

We will evaluate your request and you will receive another email with the request status.

Thanks,

The OpenReview Team.
'''

        ## Accept the request
        decision_note = client.post_note(openreview.Note(
            referent=request_note.id,
            invitation='openreview.net/Support/-/Profile_Name_Removal_Decision',
            readers=['openreview.net/Support'],
            writers=['openreview.net/Support'],
            signatures=['openreview.net/Support'],
            content={
                'status': 'Accepted'
            }

        ))

        helpers.await_queue()

        note = paul_client.get_note(request_note.id)
        assert note.content['status'] == 'Accepted'

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

        group = client.get_group('ICLRR.cc/Reviewers')
        assert '~Paul_Alternate_Last1' not in group.members
        assert '~Paul_Last1' in group.members

        group = client.get_group('CABJ/Paper1/Authors')
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
            client.get_group('~Paul_Alternate_Last1')

        assert client.get_group('~Paul_Last1').members == ['paul@profile.org']
        assert client.get_group('paul@profile.org').members == ['~Paul_Last1']

        messages = client.get_messages(to='paul@profile.org', subject='Profile name removal request has been accepted')
        assert len(messages) == 1
        assert messages[0]['content']['text'] == '''Hi Paul Last,

We have received your request to remove the name "Paul Alternate Last" from your profile: https://openreview.net/profile?id=~Paul_Last1.

The name has been removed from your profile. Please check that the information listed in your profile is correct.

Thanks,

The OpenReview Team.
'''

    def test_remove_name_and_update_relations(self, client, profile_management, helpers):

        juan_client_v2 = helpers.create_user('juan@profile.org', 'Juan', 'Last', alternates=[], institution='google.com')
        juan_client = openreview.Client(username='juan@profile.org', password=helpers.strong_password)

        profile = juan_client.get_profile()

        profile.content['homepage'] = 'https://google.com'
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

        juan_client_v2.post_note_edit(
            invitation='openreview.net/Archive/-/Direct_Upload',
            signatures=['~Juan_Alternate_Last1'],
            note = openreview.api.Note(
                content = {
                    'title': { 'value': 'Paper title 1' },
                    'abstract': { 'value': 'Paper abstract 1' },
                    'authors': { 'value': ['Juan Last', 'Test Client'] },
                    'authorids': { 'value': ['~Juan_Last1', 'test@mail.com'] },
                    'venue': { 'value': 'Arxiv' },
                    'year': { 'value': 2019 }
                }
        ))                      

        john_client = openreview.Client(username='john@profile.org', password=helpers.strong_password)

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

        request_note = juan_client.post_note(openreview.Note(
            invitation='openreview.net/Support/-/Profile_Name_Removal',
            readers=['openreview.net/Support', '~Juan_Alternate_Last1'],
            writers=['openreview.net/Support'],
            signatures=['~Juan_Alternate_Last1'],
            content={
                'name': 'Juan Last',
                'usernames': ['~Juan_Last1'],
                'comment': 'typo in my name',
                'status': 'Pending'
            }

        ))

        helpers.await_queue()

        decision_note = client.post_note(openreview.Note(
            referent=request_note.id,
            invitation='openreview.net/Support/-/Profile_Name_Removal_Decision',
            readers=['openreview.net/Support'],
            writers=['openreview.net/Support'],
            signatures=['openreview.net/Support'],
            content={
                'status': 'Accepted'
            }

        ))

        helpers.await_queue()

        juan_client = openreview.Client(username='juan@profile.org', password=helpers.strong_password)
        note = juan_client.get_note(request_note.id)
        assert note.content['status'] == 'Accepted' 

        profile = juan_client.get_profile(email_or_id='juan@profile.org')
        assert len(profile.content['names']) == 1
        assert 'username' in profile.content['names'][0]
        assert profile.content['names'][0]['username'] == '~Juan_Alternate_Last1' 

        profile = john_client.get_profile(email_or_id='john@profile.org')
        assert len(profile.content['relations']) == 2
        assert profile.content['relations'][1]['username'] == '~Juan_Alternate_Last1'                                             
        assert profile.content['relations'][1]['name'] == 'Juan Alternate Last'                                             


    def test_remove_name_and_accept_automatically(self, client, profile_management, helpers):

        helpers.create_user('nara@profile.org', 'Nara', 'Last', alternates=[], institution='google.com')
        nara_client = openreview.Client(username='nara@profile.org', password=helpers.strong_password)

        profile = nara_client.get_profile()

        profile.content['homepage'] = 'https://google.com'
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

        request_note = nara_client.post_note(openreview.Note(
            invitation='openreview.net/Support/-/Profile_Name_Removal',
            readers=['openreview.net/Support', '~Nara_Alternate_Last1'],
            writers=['openreview.net/Support'],
            signatures=['~Nara_Alternate_Last1'],
            content={
                'name': 'Nara Last',
                'usernames': ['~Nara_Last1'],
                'comment': 'typo in my name',
                'status': 'Pending'
            }

        ))

        helpers.await_queue()       

        nara_client = openreview.Client(username='nara@profile.org', password=helpers.strong_password)
        note = nara_client.get_note(request_note.id)
        assert note.content['status'] == 'Accepted'

    def test_remove_name_and_do_not_accept_automatically(self, client, openreview_client, profile_management, helpers):

        helpers.create_user('mara@profile.org', 'Mara', 'Last', alternates=[], institution='google.com')
        mara_client = openreview.Client(username='mara@profile.org', password=helpers.strong_password)

        profile = mara_client.get_profile()

        profile.content['homepage'] = 'https://google.com'
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

        request_note = mara_client.post_note(openreview.Note(
            invitation='openreview.net/Support/-/Profile_Name_Removal',
            readers=['openreview.net/Support', '~Mara_Alternate_Last1'],
            writers=['openreview.net/Support'],
            signatures=['~Mara_Alternate_Last1'],
            content={
                'name': 'Mara Last',
                'usernames': ['~Mara_Last1'],
                'comment': 'typo in my name',
                'status': 'Pending'
            }

        ))

        helpers.await_queue()       

        nara_client = openreview.Client(username='mara@profile.org', password=helpers.strong_password)
        note = nara_client.get_note(request_note.id)
        assert note.content['status'] == 'Pending'        


    def test_merge_profiles(self, openreview_client, profile_management, helpers):

        rachel_client = helpers.create_user('rachel@profile.org', 'Rachel', 'Last', alternates=[], institution='google.com')
        profile = rachel_client.get_profile()

        profile.content['homepage'] = 'https://google.com'
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

    def test_merge_profiles_as_guest(self, client, openreview_client, profile_management, helpers):

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

        messages = client.get_messages(to='marina@hotmail.com', subject='Profile merge request has been received')
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

        messages = client.get_messages(to='marina@hotmail.com', subject='Profile merge request has been rejected')
        assert len(messages) == 1
        assert messages[0]['content']['text'] == '''Hi marina@hotmail.com,

We have received your request to merge the following profiles: marina@profile.org, marina@gmail.com.

We can not merge your profiles for the following reason:

not real profiles

Regards,

The OpenReview Team.
'''


    def test_merge_profiles_ignore_request(self, openreview_client, profile_management, helpers):

        melisa_client = helpers.create_user('melisa@profile.org', 'Melisa', 'Last', alternates=[], institution='google.com')
        profile = melisa_client.get_profile()

        profile.content['homepage'] = 'https://google.com'
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

    def test_remove_email_address(self, profile_management, openreview_client, helpers):

        harold_client = helpers.create_user('harold@profile.org', 'Harold', 'Last', alternates=[], institution='google.com')
        profile = harold_client.get_profile()

        profile.content['homepage'] = 'https://google.com'
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
        openreview_client.add_members_to_group('~Harold_Last1', 'alternate_harold@profile.org')
        openreview_client.add_members_to_group('alternate_harold@profile.org', '~Harold_Last1')

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
                content = {
                    'title': { 'value': 'Paper title 1' },
                    'abstract': { 'value': 'Paper abstract 1' },
                    'authors': { 'value': ['Harold Last', 'Test Client'] },
                    'authorids': { 'value': ['alternate_harold@profile.org', 'test@mail.com'] },
                    'venue': { 'value': 'Arxiv' },
                    'year': { 'value': 2019 }
                }
        ))        

        openreview_client.post_note_edit(
            invitation='openreview.net/Archive/-/Direct_Upload',
            signatures=['~Harold_Last1'],
            note = openreview.api.Note(
                content = {
                    'title': { 'value': 'Paper title 2' },
                    'abstract': { 'value': 'Paper abstract 2' },
                    'authors': { 'value': ['Harold Last', 'Test Client'] },
                    'authorids': { 'value': ['alternate_harold@profile.org', 'test@mail.com', 'another@mail.com'] },
                    'venue': { 'value': 'Arxiv' },
                    'year': { 'value': 2019 }
                }
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