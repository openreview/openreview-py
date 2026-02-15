from __future__ import absolute_import, division, print_function, unicode_literals
import os
import datetime
import openreview
import pytest
import time
from openreview.api import OpenReviewClient
from openreview.api import Note
from openreview.venue import Venue
from openreview.stages import SubmissionStage

class TestClient():

    def test_get_groups(self, client):
        groups = client.get_groups(ids=[
            '(anonymous)',
            'everyone',
            '~',
            '(guest)',
            '~Super_User1',
            'openreview.net',
            'active_venues',
            'host'
        ])
        group_names = [g.id for g in groups]
        assert '(anonymous)' in group_names
        assert 'everyone' in group_names
        assert '~' in group_names
        assert '(guest)' in group_names
        assert '~Super_User1' in group_names
        assert 'openreview.net' in group_names
        assert 'active_venues' in group_names
        assert 'host' in group_names

    def test_create_client(self, client, helpers, test_client):

        client = openreview.Client()
        assert client
        assert not client.token
        assert not client.profile

        os.environ["OPENREVIEW_USERNAME"] = "openreview.net"

        with pytest.raises(openreview.OpenReviewException, match=r'.*Password is missing.*'):
            client = openreview.Client()

        os.environ["OPENREVIEW_PASSWORD"] = helpers.strong_password

        client = openreview.Client()
        assert client
        assert client.token
        assert client.profile
        assert '~Super_User1' == client.profile.id

        client = openreview.Client(tokenExpiresIn=5000)
        assert client
        assert client.token
        assert client.profile
        assert '~Super_User1' == client.profile.id

        with pytest.raises(openreview.OpenReviewException, match=r'.*Invalid username or password.*'):
            client = openreview.Client(username='nouser@mail.com')

        with pytest.raises(openreview.OpenReviewException, match=r'.*Invalid username or password.*'):
            client = openreview.Client(username='nouser@mail.com', password=helpers.strong_password)

        client = openreview.Client(token='Bearer ' + test_client.token)
        assert client
        assert client.token
        assert client.profile
        assert '~SomeFirstName_User1' == client.profile.id

        client = openreview.Client(token='Bearer ' + test_client.token, username='test@mail.com', password=helpers.strong_password)
        assert client
        assert client.token
        assert client.profile
        assert '~SomeFirstName_User1' == client.profile.id

        os.environ.pop("OPENREVIEW_USERNAME")
        os.environ.pop("OPENREVIEW_PASSWORD")

    def test_login_user(self, client, helpers):

        guest = openreview.Client()

        with pytest.raises(openreview.OpenReviewException, match=r'.*Email is missing.*'):
            guest.login_user()

        with pytest.raises(openreview.OpenReviewException, match=r'.*Password is missing.*'):
            guest.login_user(username = "openreview.net")

        with pytest.raises(openreview.OpenReviewException, match=r'.*Invalid username or password.*'):
            guest.login_user(username = "openreview.net", password = "1111")

        response = guest.login_user(username = "openreview.net", password = helpers.strong_password)
        assert response

        response = guest.login_user(username = "openreview.net", password = helpers.strong_password, expiresIn=4000)
        assert response

    def test_login_expiration(self, client, helpers):
        client = openreview.Client(username = "openreview.net", password = helpers.strong_password, tokenExpiresIn=3)
        group = client.get_group("openreview.net")
        assert group
        assert group.members == ['~Super_User1']
        time.sleep(4)
        try:
            group = client.get_group("openreview.net")
        except openreview.OpenReviewException as e:
            error = e.args[0]
            assert e.args[0]['name'] == 'TokenExpiredError'

        client_v2 = openreview.api.OpenReviewClient(username = "openreview.net", password = helpers.strong_password, tokenExpiresIn=3)
        group = client_v2.get_group("openreview.net")
        assert group
        assert group.members == ['~Super_User1']
        time.sleep(4)
        try:
            group = client_v2.get_group("openreview.net")
        except openreview.OpenReviewException as e:
            error = e.args[0]
            assert e.args[0]['name'] == 'TokenExpiredError'

    def test_get_notes_with_details(self, client):
        notes = client.get_notes(invitation = 'ICLR.cc/2018/Conference/-/Blind_Submission', details='all')
        assert len(notes) == 0, 'notes is empty'

    def test_get_profile(self, client, test_client):
        profile = client.get_profile('test@mail.com')
        assert profile, "Could not get the profile by email"
        assert isinstance(profile, openreview.Profile)
        assert profile.id == '~SomeFirstName_User1'

        profile = client.get_profile('~Super_User1')
        assert profile, "Could not get the profile by id"
        assert isinstance(profile, openreview.Profile)
        assert 'openreview@local.openreview.net' in profile.content['emails']

        with pytest.raises(openreview.OpenReviewException, match=r'.*Profile Not Found.*'):
            profile = client.get_profile('mbok@sss.edu')

        assert openreview.tools.get_profile(client, '~Super_User1')
        assert not openreview.tools.get_profile(client, 'mbok@sss.edu')

    def test_search_profiles(self, client, helpers):
        guest = openreview.Client()
        guest.register_user(email = 'mbok@mail.com', fullname= 'Melisa Bokk', password = helpers.strong_password)
        guest.register_user(email = 'andrew@mail.com', fullname = 'Andrew E McCallum', password = helpers.strong_password)

        profiles = client.search_profiles(confirmedEmails=['mbok@mail.com'])
        assert profiles, "Could not get the profile by email"
        assert isinstance(profiles, dict)
        assert isinstance(profiles['mbok@mail.com'], openreview.Profile)
        assert profiles['mbok@mail.com'].id == '~Melisa_Bokk1'

        profiles = client.search_profiles(ids=['~Melisa_Bokk1', '~Andrew_E_McCallum1'])
        assert profiles, "Could not get the profile by id"
        assert isinstance(profiles, list)
        assert len(profiles) == 2
        assert '~Melisa_Bokk1' in profiles[1].id
        assert '~Andrew_E_McCallum1' in profiles[0].id

        profiles = client.search_profiles(emails=[])
        assert len(profiles) == 0

        assert client.profile
        assert client.profile.id == '~Super_User1'

        assert '~Melisa_Bokk1' == client.search_profiles(ids = ['~Melisa_Bokk1'])[0].id
        assert '~Melisa_Bokk1' == client.search_profiles(confirmedEmails = ['mbok@mail.com'])['mbok@mail.com'].id
        assert '~Melisa_Bokk1' == client.search_profiles(first = 'Melisa', last = 'Bokk')[0].id
        assert len(client.search_profiles(ids = ['~Melisa_Bok2'])) == 0
        assert len(client.search_profiles(emails = ['mail@mail.com'])) == 0
        assert len(client.search_profiles(first = 'Anna')) == 0

        helpers.create_user('user_a@mail.com', 'User', 'A', alternates=['users@alternate.com'])
        helpers.create_user('user_b@mail.com', 'User', 'B', alternates=['users@alternate.com'])
        profiles = client.search_profiles(emails = ['users@alternate.com'])
        assert profiles
        assert 'users@alternate.com' in profiles
        assert len(profiles['users@alternate.com']) == 2

        profiles = client.search_profiles(confirmedEmails = ['users@alternate.com'])
        assert not profiles


    def test_confirm_registration(self):

        guest = openreview.Client()
        res = guest.activate_user('mbok@mail.com', {
            'names': [
                    {
                        'first': 'Melisa',
                        'last': 'Bok',
                        'username': '~Melisa_Bokk1'
                    }
                ],
            'emails': ['mbok@mail.com'],
            'preferredEmail': 'mbok@mail.com',
            'homepage': f"https://melisa{int(time.time())}.openreview.net",
            })
        assert res, "Res i none"
        group = guest.get_group(id = 'mbok@mail.com')
        assert group
        assert group.members == ['~Melisa_Bokk1']

    # def test_get_invitations_by_invitee(self, client):
    #     invitations = client.get_invitations(invitee = '~', pastdue = False)
    #     assert len(invitations) == 5

    #     invitations = client.get_invitations(invitee = True, duedate = True, details = 'replytoNote,repliedNotes')
    #     assert invitations

    #     invitations = client.get_invitations(invitee = True, duedate = True, replyto = True, details = 'replytoNote,repliedNotes')
    #     assert invitations

    #     invitations = client.get_invitations(invitee = True, duedate = True, tags = True, details = 'repliedTags')
    #     assert len(invitations) == 0


    def test_get_notes_by_content(self, openreview_client, helpers):

        conference_id = 'Test.ws/2019/Conference'
        venue = Venue(openreview_client, conference_id, 'openreview.net/Support')
        venue.name = 'Test 2019 Conference'
        venue.short_name = 'Test 2019'
        venue.website = 'test.ws'
        venue.contact = 'test@contact.com'
        venue.invitation_builder.update_wait_time = 2000
        venue.invitation_builder.update_date_string = "#{4/mdate} + 2000"

        now = datetime.datetime.now()
        venue.submission_stage = SubmissionStage(
            double_blind=False,
            due_date=now + datetime.timedelta(minutes=100),
            readers=[SubmissionStage.Readers.EVERYONE],
        )

        venue.setup(program_chair_ids=[])
        venue.create_submission_stage()

        invitation = venue.get_submission_id()

        author_client = OpenReviewClient(username='mbok@mail.com', password=helpers.strong_password)
        note_edit = author_client.post_note_edit(
            invitation=invitation,
            signatures=['~Melisa_Bokk1'],
            note=Note(
                content={
                    'title': { 'value': 'Paper title' },
                    'abstract': { 'value': 'This is an abstract' },
                    'authorids': { 'value': ['mbok@mail.com', 'andrew@mail.com'] },
                    'authors': { 'value': ['Melisa Bok', 'Andrew Mc'] },
                    'keywords': { 'value': ['keyword1', 'keyword2'] },
                    'pdf': { 'value': '/pdf/22234qweoiuweroi22234qweoiuweroi12345678.pdf' },
                }
            )
        )
        helpers.await_queue_edit(openreview_client, edit_id=note_edit['id'])
        assert note_edit

        notes = openreview_client.get_notes(invitation=invitation, content = { 'title': 'Paper title'})
        assert len(notes) == 1

        notes = openreview_client.get_notes(invitation=invitation, content = { 'title': 'Paper title3333'})
        assert len(notes) == 0

        notes = list(openreview.tools.iterget_notes(openreview_client, invitation=invitation, content = { 'title': 'Paper title'}))
        assert len(notes) == 1

        notes = list(openreview.tools.iterget_notes(openreview_client, invitation=invitation, content = { 'title': 'Paper title333'}))
        assert len(notes) == 0

        notes = openreview_client.get_all_notes(invitation=invitation, content = { 'title': 'Paper title'})
        assert len(notes) == 1

        notes = openreview_client.get_all_notes(invitation=invitation, content = { 'title': 'Paper title333'})
        assert len(notes) == 0

    def test_merge_profile(self, client, helpers):
        guest = openreview.Client()
        from_profile = guest.register_user(email = 'celeste@gmail.com', fullname = 'Celeste Bok', password = helpers.strong_password)
        assert from_profile
        to_profile = guest.register_user(email = 'melisab@mail.com', fullname = 'Melissa Bok', password = helpers.strong_password)
        assert to_profile

        assert from_profile['id'] == '~Celeste_Bok1'
        assert to_profile['id'] == '~Melissa_Bok1'

        profile = client.merge_profiles('~Melissa_Bok1', '~Celeste_Bok1')
        assert profile, 'Could not merge the profiles'
        assert profile.id == '~Melissa_Bok1'
        usernames = [name['username'] for name in profile.content['names']]
        assert '~Melissa_Bok1' in usernames
        assert '~Celeste_Bok1' in usernames
        merged_profile = client.get_profile(email_or_id = '~Celeste_Bok1')
        merged_profile.id == '~Melissa_Bok1'

        

    def test_rename_profile(self, client, helpers):
        guest = openreview.Client()
        from_profile = guest.register_user(email = 'lbahy@mail.com', fullname = 'Nadia LBahy', password = helpers.strong_password)
        assert from_profile
        to_profile = guest.register_user(email = 'steph@mail.com', fullname = 'David Steph', password = helpers.strong_password)
        assert to_profile

        assert from_profile['id'] == '~Nadia_LBahy1'
        assert to_profile['id'] == '~David_Steph1'

        profile = client.merge_profiles('~David_Steph1', '~Nadia_LBahy1')
        assert profile, 'Could not merge the profiles'
        assert profile.id == '~David_Steph1'
        usernames = [name['username'] for name in profile.content['names']]
        assert '~Nadia_LBahy1' in usernames
        assert '~David_Steph1' in usernames

        # Test rename profile 
        assert profile.id == '~David_Steph1'
        profile = client.rename_profile('~David_Steph1', '~Nadia_LBahy1')
        assert profile.id == '~Nadia_LBahy1'

    @pytest.mark.skip()
    def test_post_venue(self, client, helpers):
        os.environ["OPENREVIEW_USERNAME"] = "openreview.net"
        os.environ["OPENREVIEW_PASSWORD"] = helpers.strong_password
        super_user = openreview.Client()
        assert '~Super_User1' == super_user.profile.id

        venueId = '.HCOMP/2013';
        invitation = 'Venue/-/Conference/Occurrence'
        venue = {
            'id': venueId,
            'invitation': invitation,
            'readers': [ 'everyone' ],
            'nonreaders': [],
            'writers': [ 'Venue' ],
            'content': {
                'name': 'The 4th Human Computation Workshop',
                'location': 'Toronto, Ontario, Canada',
                'year': '2012',
                'parents': [ '.HCOMP', '.AAAI/2012' ],
                'program_chairs': [ '~Yiling_Chen1', 'Panagiotis_G._Ipeirotis1' ],
                'area_chairs': 'HCOMP.org/2020/ACs',
                'publisher': 'AAAI Press',
                'url': 'http://www.aaai.org/Library/Workshops/ws12-08.php',
                'dblp_url': 'db/conf/hcomp/hcomp2012.html'
            }
        }

        venueRes = super_user.post_venue(venue)
        assert venue == venueRes
        os.environ.pop("OPENREVIEW_USERNAME")
        os.environ.pop("OPENREVIEW_PASSWORD")

    @pytest.mark.skip()
    def test_get_venues(self, client, helpers):
        os.environ["OPENREVIEW_USERNAME"] = "openreview.net"
        os.environ["OPENREVIEW_PASSWORD"] = helpers.strong_password
        super_user = openreview.Client()
        assert '~Super_User1' == super_user.profile.id

        venueId = '.HCOMP/2012';
        invitation = 'Venue/-/Conference/Occurrence'
        venue = {
            'id': venueId,
            'invitation': invitation,
            'readers': [ 'everyone' ],
            'nonreaders': [],
            'writers': [ 'Venue' ],
            'content': {
                'name': 'The 4th Human Computation Workshop',
                'location': 'Toronto, Ontario, Canada',
                'year': '2012',
                'parents': [ '.HCOMP', '.AAAI/2012' ],
                'program_chairs': [ '~Yiling_Chen1', 'Panagiotis_G._Ipeirotis1' ],
                'area_chairs': 'HCOMP.org/2020/ACs',
                'publisher': 'AAAI Press',
                'url': 'http://www.aaai.org/Library/Workshops/ws12-08.php',
                'dblp_url': 'db/conf/hcomp/hcomp2012.html'
            }
        }

        venueRes = super_user.post_venue(venue)
        assert venue == venueRes

        venueRes = super_user.get_venues(id=venueId)
        assert len(venueRes) == 1
        assert venueRes == [venue]

        venues = super_user.get_venues(ids=[venueId, '.HCOMP/2013'])
        assert len(venues) == 2
        assert venues[0].get('id') == venue.get('id')
        assert venues[1].get('id') == '.HCOMP/2013'

        venues = super_user.get_venues(invitations=['Venue/-/Conference/Occurrence'])
        assert len(venues) == 2
        assert venues[0].get('id') == '.HCOMP/2013'
        assert venues[1].get('id') == venue.get('id')

        os.environ.pop("OPENREVIEW_USERNAME")
        os.environ.pop("OPENREVIEW_PASSWORD")

    def test_get_messages(self, openreview_client):
        messages = openreview_client.get_messages()
        assert messages

        messages = openreview_client.get_messages(status='sent')
        assert messages

        messages = openreview.tools.iterget_messages(openreview_client, status='sent')
        assert messages

    def test_get_notes_by_ids(self, openreview_client):
        notes = openreview_client.get_notes(invitation='Test.ws/2019/Conference/-/Submission', content = { 'title': 'Paper title'})
        assert len(notes) == 1        
       
        notes = openreview_client.get_notes_by_ids(ids = [notes[0].id])
        assert len(notes) == 1, 'notes is not empty'

    # def test_infer_notes(self, client):
    #     notes = client.get_notes(signature='openreview.net/Support')
    #     assert notes
    #     note = client.infer_note(notes[0].id)
    #     assert note


class TestMfaLogin():

    def test_login_without_mfa(self, helpers):
        """Verify backward compatibility - login works without MFA enabled."""
        email = 'mfa_nomfa_test@mail.com'
        helpers.create_user(email, 'MfaNoMfa', 'TestUser')

        client_v2 = OpenReviewClient(
            baseurl='http://localhost:3001',
            username=email,
            password=helpers.strong_password
        )
        assert client_v2.token
        assert client_v2.profile

        client_v1 = openreview.Client(
            baseurl='http://localhost:3000',
            username=email,
            password=helpers.strong_password
        )
        assert client_v1.token
        assert client_v1.profile

    def test_totp_setup_and_mfa_pending_response(self, helpers):
        """After enabling TOTP, POST /login should return mfaPending."""
        import requests as req
        import pyotp

        email = 'mfa_totp_test@mail.com'
        helpers.create_user(email, 'MfaTotp', 'TestUser')

        client = OpenReviewClient(
            baseurl='http://localhost:3001',
            username=email,
            password=helpers.strong_password
        )

        # Initialize TOTP setup
        res = req.post(
            'http://localhost:3001/mfa/setup/totp/init',
            headers={'Authorization': f'Bearer {client.token}', 'User-Agent': 'test-script'}
        )
        assert res.status_code == 200
        secret = res.json()['secret']
        TestMfaLogin.totp_secret = secret

        # Verify TOTP setup with a valid code
        totp = pyotp.TOTP(secret)
        res = req.post(
            'http://localhost:3001/mfa/setup/totp/verify',
            headers={'Authorization': f'Bearer {client.token}', 'User-Agent': 'test-script'},
            json={'code': totp.now()}
        )
        assert res.status_code == 200

        # Verify that POST /login now returns mfaPending
        res = req.post(
            'http://localhost:3001/login',
            json={'id': email, 'password': helpers.strong_password},
            headers={'User-Agent': 'test-script'}
        )
        assert res.status_code == 200
        data = res.json()
        assert data.get('mfaPending') is True
        assert 'mfaPendingToken' in data
        assert 'totp' in data.get('mfaMethods', [])
        assert data.get('preferredMethod') == 'totp'

    def test_totp_mfa_exception_non_interactive_v2(self, helpers):
        """MfaRequiredException is raised in non-interactive mode (v2 client)."""
        from unittest.mock import patch

        with patch('sys.stdin') as mock_stdin:
            mock_stdin.isatty.return_value = False
            with pytest.raises(openreview.MfaRequiredException) as exc_info:
                OpenReviewClient(
                    baseurl='http://localhost:3001',
                    username='mfa_totp_test@mail.com',
                    password=helpers.strong_password
                )
            assert 'totp' in exc_info.value.mfa_methods
            assert exc_info.value.mfa_pending_token
            assert exc_info.value.preferred_method == 'totp'

    def test_totp_mfa_exception_non_interactive_v1(self, helpers):
        """MfaRequiredException is raised in non-interactive mode (v1 client)."""
        from unittest.mock import patch

        with patch('sys.stdin') as mock_stdin:
            mock_stdin.isatty.return_value = False
            with pytest.raises(openreview.MfaRequiredException) as exc_info:
                openreview.Client(
                    baseurl='http://localhost:3000',
                    username='mfa_totp_test@mail.com',
                    password=helpers.strong_password
                )
            assert 'totp' in exc_info.value.mfa_methods
            assert exc_info.value.mfa_pending_token

    def test_totp_login_v2(self, helpers):
        """Test successful TOTP login with v2 client (mocked interactive prompts)."""
        import pyotp
        from unittest.mock import patch

        totp = pyotp.TOTP(TestMfaLogin.totp_secret)

        with patch('openreview.api.client.sys') as mock_sys, \
             patch('openreview.api.client._default_mfa_method_chooser', return_value='totp'), \
             patch('openreview.api.client._default_mfa_code_prompt', return_value=totp.now()):
            mock_sys.stdin.isatty.return_value = True
            client = OpenReviewClient(
                baseurl='http://localhost:3001',
                username='mfa_totp_test@mail.com',
                password=helpers.strong_password
            )
            assert client.token
            assert client.profile

    def test_totp_login_v1(self, helpers):
        """Test successful TOTP login with v1 client (mocked interactive prompts)."""
        import pyotp
        from unittest.mock import patch

        totp = pyotp.TOTP(TestMfaLogin.totp_secret)

        with patch('openreview.openreview.sys') as mock_sys, \
             patch('openreview.openreview._default_mfa_method_chooser', return_value='totp'), \
             patch('openreview.openreview._default_mfa_code_prompt', return_value=totp.now()):
            mock_sys.stdin.isatty.return_value = True
            client = openreview.Client(
                baseurl='http://localhost:3000',
                username='mfa_totp_test@mail.com',
                password=helpers.strong_password
            )
            assert client.token
            assert client.profile

    def test_email_otp_setup(self, helpers):
        """Enable email OTP for a separate test user."""
        import requests as req

        email = 'mfa_email_test@mail.com'
        helpers.create_user(email, 'MfaEmail', 'TestUser')

        client = OpenReviewClient(
            baseurl='http://localhost:3001',
            username=email,
            password=helpers.strong_password
        )

        res = req.post(
            'http://localhost:3001/mfa/setup/email',
            headers={'Authorization': f'Bearer {client.token}', 'User-Agent': 'test-script'}
        )
        assert res.status_code == 200
        data = res.json()
        assert data.get('emailOtpEnabled') is True

    def test_email_otp_login_v2(self, openreview_client, helpers):
        """Test successful email OTP login with v2 client."""
        import re
        from unittest.mock import patch

        email = 'mfa_email_test@mail.com'

        def fetch_email_otp(method):
            time.sleep(0.5)
            messages = openreview_client.get_messages(to=email)
            assert messages, 'No messages found for MFA email user'
            sorted_msgs = sorted(messages, key=lambda m: m.get('cdate', 0), reverse=True)
            for msg in sorted_msgs:
                subject = msg.get('content', {}).get('subject', '')
                if 'Verification Code' in subject:
                    text = msg['content']['text']
                    match = re.search(r'verification code is: \*\*(\d{6})\*\*', text)
                    if match:
                        return match.group(1)
            raise AssertionError('Could not extract OTP code from messages')

        with patch('openreview.api.client.sys') as mock_sys, \
             patch('openreview.api.client._default_mfa_method_chooser', return_value='emailOtp'), \
             patch('openreview.api.client._default_mfa_code_prompt', side_effect=fetch_email_otp):
            mock_sys.stdin.isatty.return_value = True
            client = OpenReviewClient(
                baseurl='http://localhost:3001',
                username=email,
                password=helpers.strong_password
            )
            assert client.token
            assert client.profile

    def test_email_otp_login_v1(self, openreview_client, helpers):
        """Test successful email OTP login with v1 client (separate user)."""
        import re
        import requests as req
        from unittest.mock import patch

        email = 'mfa_email_v1_test@mail.com'
        helpers.create_user(email, 'MfaEmailVone', 'TestUser')

        # Enable email OTP for this user
        client = OpenReviewClient(
            baseurl='http://localhost:3001',
            username=email,
            password=helpers.strong_password
        )
        res = req.post(
            'http://localhost:3001/mfa/setup/email',
            headers={'Authorization': f'Bearer {client.token}', 'User-Agent': 'test-script'}
        )
        assert res.status_code == 200

        def fetch_email_otp(method):
            time.sleep(1)
            messages = openreview_client.get_messages(to=email)
            assert messages, 'No messages found for MFA email user'
            sorted_msgs = sorted(messages, key=lambda m: m.get('cdate', 0), reverse=True)
            for msg in sorted_msgs:
                subject = msg.get('content', {}).get('subject', '')
                if 'Verification Code' in subject:
                    text = msg['content']['text']
                    match = re.search(r'verification code is: \*\*(\d{6})\*\*', text)
                    if match:
                        return match.group(1)
            raise AssertionError('Could not extract OTP code from messages')

        with patch('openreview.openreview.sys') as mock_sys, \
             patch('openreview.openreview._default_mfa_method_chooser', return_value='emailOtp'), \
             patch('openreview.openreview._default_mfa_code_prompt', side_effect=fetch_email_otp):
            mock_sys.stdin.isatty.return_value = True
            client = openreview.Client(
                baseurl='http://localhost:3000',
                username=email,
                password=helpers.strong_password
            )
            assert client.token
            assert client.profile

