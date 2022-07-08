from __future__ import absolute_import, division, print_function, unicode_literals

import openreview
from openreview import ProfileManagement
import pytest

class TestProfileManagement():

    
    @pytest.fixture(scope="class")
    def profile_management(self, client):
        profile_management = ProfileManagement(client, 'openreview.net/Support', 'openreview.net')
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

        request_note = john_client.post_note(openreview.Note(
            invitation='openreview.net/Support/-/Profile_Name_Removal',
            readers=['openreview.net/Support', '~John_Last1'],
            writers=['openreview.net/Support'],
            signatures=['~John_Last1'],
            content={
                'username': '~John_Alternate_Last1',
                'comment': 'typo in my name',
                'status': 'Pending'
            }

        ))

        helpers.await_queue()

        messages = client.get_messages(to='john@profile.org', subject='Profile name removal request has been received')
        assert len(messages) == 1
        assert messages[0]['content']['text'] == '''<p>Hi John Last,</p>
<p>We have received your request to remove the name &quot;~John_Alternate_Last1&quot; from your <a href=\"https://openreview.net/profile?id=~John_Last1\">profile</a>.</p>
<p>We will evaluate your request and you will receive another email with the request status.</p>
<p>Thanks,</p>
<p>The OpenReview Team.</p>
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

        profile = john_client.get_profile(email_or_id='~John_Last1')
        assert len(profile.content['names']) == 1
        assert 'username' in profile.content['names'][0]
        assert profile.content['names'][0]['username'] == '~John_Last1'

        with pytest.raises(openreview.OpenReviewException, match=r'Group Not Found: ~John_Alternate_Last1'):
            client.get_group('~John_Alternate_Last1')        