from __future__ import absolute_import, division, print_function, unicode_literals

import openreview
from openreview import ProfileManagement
import pytest

class TestProfileManagement():

    
    @pytest.fixture(scope="class")
    def profile_management(self, client):
        profile_management = ProfileManagement(client, 'openreview.net')
        profile_management.setup()
        return profile_management
    
    def test_remove_alternate_name(self, client, profile_management, helpers):

        john_client = helpers.create_user('john@profile.org', 'John', 'Last', alternates=[], institution='google.com')
        profile = john_client.get_profile()

        profile.content['homepage'] = 'https://google.com'
        profile.content['names'].append({
            'first': 'John',
            'middle': 'Alternate',
            'last': 'Last'
            })
        john_client.post_profile(profile)
        profile = john_client.get_profile(email_or_id='~John_Last1')
        assert len(profile.content['names']) == 2
        assert 'username' in profile.content['names'][1]
        assert profile.content['names'][1]['username'] == '~John_Alternate_Last1'

        assert client.get_group('~John_Last1').members == ['john@profile.org']
        assert client.get_group('john@profile.org').members == ['~John_Last1', '~John_Alternate_Last1']
        assert client.get_group('~John_Alternate_Last1').members == ['john@profile.org']

        ## Try to remove the unexisting name and get an error
        with pytest.raises(openreview.OpenReviewException, match=r'Profile not found for ~John_Last'):
            request_note = john_client.post_note(openreview.Note(
                invitation='openreview.net/Support/-/Profile_Name_Removal',
                readers=['openreview.net/Support', '~John_Last1'],
                writers=['openreview.net/Support'],
                signatures=['~John_Last1'],
                content={
                    'name': 'John Last',
                    'usernames': ['~John_Last'],
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
        john_client.post_note(openreview.Note(
            invitation='openreview.net/Archive/-/Direct_Upload',
            readers = ['everyone'],
            signatures = ['~John_Alternate_Last1'],
            writers = ['~John_Alternate_Last1'],
            content = {
                'title': 'Paper title 1',
                'abstract': 'Paper abstract 1',
                'authors': ['John Alternate Last', 'Test Client'],
                'authorids': ['~John_Alternate_Last1', 'test@mail.com']
            }
        ))

        john_client.post_note(openreview.Note(
            invitation='openreview.net/Archive/-/Direct_Upload',
            readers = ['everyone'],
            signatures = ['~John_Alternate_Last1'],
            writers = ['~John_Alternate_Last1'],
            content = {
                'title': 'Paper title 2',
                'abstract': 'Paper abstract 2',
                'authors': ['John Last', 'Test Client'],
                'authorids': ['~John_Last1', 'test@mail.com']
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
            members=['~John_Alternate_Last1']
        ))        

        publications = client.get_notes(content={ 'authorids': '~John_Last1'})
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

        publications = client.get_notes(content={ 'authorids': '~John_Last1'})
        assert len(publications) == 2
        assert '~John_Last1' in publications[0].writers
        assert '~John_Last1' in publications[0].signatures
        assert '~John_Last1' in publications[1].writers
        assert '~John_Last1' in publications[1].signatures

        group = client.get_group('ICLRR.cc/Reviewers')
        assert '~John_Alternate_Last1' not in group.members
        assert '~John_Last1' in group.members

        profile = john_client.get_profile(email_or_id='~John_Last1')
        assert len(profile.content['names']) == 1
        assert 'username' in profile.content['names'][0]
        assert profile.content['names'][0]['username'] == '~John_Last1'

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

    def test_remove_name_and_rename_profile_id(self, client, helpers):

        ana_client = helpers.create_user('ana@profile.org', 'Ana', 'Last', alternates=[], institution='google.com')
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
        ana_client.post_note(openreview.Note(
            invitation='openreview.net/Archive/-/Direct_Upload',
            readers = ['everyone'],
            signatures = ['~Ana_Last1'],
            writers = ['~Ana_Last1'],
            content = {
                'title': 'Paper title 1',
                'abstract': 'Paper abstract 1',
                'authors': ['Ana Last', 'Test Client'],
                'authorids': ['~Ana_Last1', 'test@mail.com']
            }
        ))

        ana_client.post_note(openreview.Note(
            invitation='openreview.net/Archive/-/Direct_Upload',
            readers = ['everyone'],
            signatures = ['~Ana_Last1'],
            writers = ['~Ana_Last1'],
            content = {
                'title': 'Paper title 2',
                'abstract': 'Paper abstract 2',
                'authors': ['Ana Last', 'Test Client'],
                'authorids': ['~Ana_Last1', 'test@mail.com']
            }
        ))

        publications = client.get_notes(content={ 'authorids': '~Ana_Alternate_Last1'})
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

        note = ana_client.get_note(request_note.id)
        assert note.content['status'] == 'Accepted'

        publications = client.get_notes(content={ 'authorids': '~Ana_Alternate_Last1'})
        assert len(publications) == 2
        assert '~Ana_Alternate_Last1' in publications[0].writers
        assert '~Ana_Alternate_Last1' in publications[0].signatures
        assert '~Ana_Alternate_Last1' in publications[1].writers
        assert '~Ana_Alternate_Last1' in publications[1].signatures


        profile = ana_client.get_profile(email_or_id='~Ana_Alternate_Last1')
        assert len(profile.content['names']) == 1
        assert 'username' in profile.content['names'][0]
        assert profile.content['names'][0]['username'] == '~Ana_Alternate_Last1'

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

        peter_client = helpers.create_user('peter@profile.org', 'Peter', 'Last', alternates=[], institution='google.com')
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

    def test_remove_name_from_merged_profile(self, client, profile_management, helpers):

        ella_client = helpers.create_user('ella@profile.org', 'Ella', 'Last', alternates=[], institution='google.com')
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
        ella_client.post_note(openreview.Note(
            invitation='openreview.net/Archive/-/Direct_Upload',
            readers = ['everyone'],
            signatures = ['~Ella_Last1'],
            writers = ['~Ella_Last1'],
            content = {
                'title': 'Paper title 1',
                'abstract': 'Paper abstract 1',
                'authors': ['Ella Last', 'Test Client'],
                'authorids': ['~Ella_Last1', 'test@mail.com']
            }
        ))

        publications = client.get_notes(content={ 'authorids': '~Ella_Last1'})
        assert len(publications) == 1


        ella_client_2 = helpers.create_user('ella_two@profile.org', 'Ella', 'Last', alternates=[], institution='deepmind.com')
        profile = ella_client_2.get_profile()
        assert '~Ella_Last2' == profile.id

        assert client.get_group('~Ella_Last2').members == ['ella_two@profile.org']
        assert client.get_group('ella_two@profile.org').members == ['~Ella_Last2']

        ella_client_2.post_note(openreview.Note(
            invitation='openreview.net/Archive/-/Direct_Upload',
            readers = ['everyone'],
            signatures = ['~Ella_Last2'],
            writers = ['~Ella_Last2'],
            content = {
                'title': 'Paper title 2',
                'abstract': 'Paper abstract 2',
                'authors': ['Ella Last', 'Test Client'],
                'authorids': ['~Ella_Last2', 'test@mail.com']
            }
        ))

        publications = client.get_notes(content={ 'authorids': '~Ella_Last2'})
        assert len(publications) == 1


        client.merge_profiles('~Ella_Last1', '~Ella_Last2')
        profile = ella_client.get_profile()
        assert len(profile.content['names']) == 3
        profile.content['names'][0]['username'] == '~Ella_Last1'
        profile.content['names'][0]['preferred'] == True
        profile.content['names'][1]['username'] == '~Ella_Alternate_Last1'
        profile.content['names'][2]['username'] == '~Ella_Last2'

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

        publications = client.get_notes(content={ 'authorids': '~Ella_Last1'})
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

    def test_remove_duplicated_name(self, client, profile_management, helpers):

        javier_client = helpers.create_user('javier@profile.org', 'Javier', 'Last', alternates=[], institution='google.com')
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
        javier_client.post_note(openreview.Note(
            invitation='openreview.net/Archive/-/Direct_Upload',
            readers = ['everyone'],
            signatures = ['~Javier_Last1'],
            writers = ['~Javier_Last1'],
            content = {
                'title': 'Paper title 1',
                'abstract': 'Paper abstract 1',
                'authors': ['Javier Last', 'Test Client'],
                'authorids': ['~Javier_Last1', 'test@mail.com']
            }
        ))

        publications = client.get_notes(content={ 'authorids': '~Javier_Last1'})
        assert len(publications) == 1


        javier_client_2 = helpers.create_user('javier_two@profile.org', 'Javier', 'Last', alternates=[], institution='deepmind.com')
        profile = javier_client_2.get_profile()
        assert '~Javier_Last2' == profile.id

        javier_client_2.post_note(openreview.Note(
            invitation='openreview.net/Archive/-/Direct_Upload',
            readers = ['everyone'],
            signatures = ['~Javier_Last2'],
            writers = ['~Javier_Last2'],
            content = {
                'title': 'Paper title 2',
                'abstract': 'Paper abstract 2',
                'authors': ['Javier Last', 'Test Client'],
                'authorids': ['~Javier_Last2', 'test@mail.com']
            }
        ))

        publications = client.get_notes(content={ 'authorids': '~Javier_Last2'})
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

        note = javier_client.get_note(request_note.id)
        assert note.content['status'] == 'Accepted'

        publications = client.get_notes(content={ 'authorids': '~Javier_Alternate_Last1'})
        assert len(publications) == 2
        assert '~Javier_Alternate_Last1' in publications[0].writers
        assert '~Javier_Alternate_Last1' in publications[0].signatures
        assert '~Javier_Alternate_Last1' in publications[1].writers
        assert '~Javier_Alternate_Last1' in publications[1].signatures


        profile = javier_client.get_profile(email_or_id='~Javier_Alternate_Last1')
        assert len(profile.content['names']) == 1
        assert profile.content['names'][0]['username'] == '~Javier_Alternate_Last1'

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