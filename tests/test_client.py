from __future__ import absolute_import, division, print_function, unicode_literals
import os
import datetime
import openreview
import pytest
import time

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
        assert 'openreview.net' in profile.content['emails']

        with pytest.raises(openreview.OpenReviewException, match=r'.*Profile Not Found.*'):
            profile = client.get_profile('mbok@sss.edu')

        assert openreview.tools.get_profile(client, '~Super_User1')
        assert not openreview.tools.get_profile(client, 'mbok@sss.edu')

    def test_search_profiles(self, client, helpers):
        guest = openreview.Client()
        guest.register_user(email = 'mbok@mail.com', first = 'Melisa', last = 'Bok', password = helpers.strong_password)
        guest.register_user(email = 'andrew@mail.com', first = 'Andrew', last = 'McCallum', password = helpers.strong_password)

        profiles = client.search_profiles(confirmedEmails=['mbok@mail.com'])
        assert profiles, "Could not get the profile by email"
        assert isinstance(profiles, dict)
        assert isinstance(profiles['mbok@mail.com'], openreview.Profile)
        assert profiles['mbok@mail.com'].id == '~Melisa_Bok1'

        profiles = client.search_profiles(ids=['~Melisa_Bok1', '~Andrew_McCallum1'])
        assert profiles, "Could not get the profile by id"
        assert isinstance(profiles, list)
        assert len(profiles) == 2
        assert '~Melisa_Bok1' in profiles[1].id
        assert '~Andrew_McCallum1' in profiles[0].id

        profiles = client.search_profiles(emails=[])
        assert len(profiles) == 0

        assert client.profile
        assert client.profile.id == '~Super_User1'

        assert '~Melisa_Bok1' == client.search_profiles(ids = ['~Melisa_Bok1'])[0].id
        assert '~Melisa_Bok1' == client.search_profiles(confirmedEmails = ['mbok@mail.com'])['mbok@mail.com'].id
        assert '~Melisa_Bok1' == client.search_profiles(first = 'Melisa')[0].id
        assert len(client.search_profiles(ids = ['~Melisa_Bok2'])) == 0
        assert len(client.search_profiles(emails = ['mail@mail.com'])) == 0
        assert len(client.search_profiles(first = 'Anna')) == 0

        user_a = helpers.create_user('user_a@mail.com', 'User', 'A', alternates=['users@alternate.com'])
        user_b = helpers.create_user('user_b@mail.com', 'User', 'B', alternates=['users@alternate.com'])
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
                        'username': '~Melisa_Bok1'
                    }
                ],
            'emails': ['mbok@mail.com'],
            'preferredEmail': 'mbok@mail.com'
            })
        assert res, "Res i none"
        group = guest.get_group(id = 'mbok@mail.com')
        assert group
        assert group.members == ['~Melisa_Bok1']

    # def test_get_invitations_by_invitee(self, client):
    #     invitations = client.get_invitations(invitee = '~', pastdue = False)
    #     assert len(invitations) == 5

    #     invitations = client.get_invitations(invitee = True, duedate = True, details = 'replytoNote,repliedNotes')
    #     assert invitations

    #     invitations = client.get_invitations(invitee = True, duedate = True, replyto = True, details = 'replytoNote,repliedNotes')
    #     assert invitations

    #     invitations = client.get_invitations(invitee = True, duedate = True, tags = True, details = 'repliedTags')
    #     assert len(invitations) == 0

    def test_get_notes_by_content(self, client, helpers):

        now = datetime.datetime.utcnow()
        builder = openreview.conference.ConferenceBuilder(client, support_user='openreview.net/Support')
        assert builder, 'builder is None'

        builder.set_conference_id('Test.ws/2019/Conference')
        builder.set_submission_stage(due_date = now + datetime.timedelta(minutes = 100))

        conference = builder.get_result()
        assert conference, 'conference is None'

        invitation = conference.get_submission_id()

        author_client = openreview.Client(username='mbok@mail.com', password=helpers.strong_password)
        note = openreview.Note(invitation = invitation,
            readers = ['mbok@mail.com', 'andrew@mail.com'],
            writers = ['mbok@mail.com', 'andrew@mail.com'],
            signatures = ['~Melisa_Bok1'],
            content = {
                'title': 'Paper title',
                'abstract': 'This is an abstract',
                'authorids': ['mbok@mail.com', 'andrew@mail.com'],
                'authors': ['Melisa Bok', 'Andrew Mc'],
                'pdf': '/pdf/22234qweoiuweroi22234qweoiuweroi12345678.pdf'
            }
        )
        note = author_client.post_note(note)
        assert note

        notes = client.get_notes(invitation=invitation, content = { 'title': 'Paper title'})
        assert len(notes) == 1

        notes = client.get_notes(invitation=invitation, content = { 'title': 'Paper title3333'})
        assert len(notes) == 0

        notes = list(openreview.tools.iterget_notes(client, invitation=invitation, content = { 'title': 'Paper title'}))
        assert len(notes) == 1

        notes = list(openreview.tools.iterget_notes(client, invitation=invitation, content = { 'title': 'Paper title333'}))
        assert len(notes) == 0

        notes = client.get_all_notes(invitation=invitation, content = { 'title': 'Paper title'})
        assert len(notes) == 1

        notes = client.get_all_notes(invitation=invitation, content = { 'title': 'Paper title333'})
        assert len(notes) == 0

    def test_merge_profile(self, client, helpers):
        guest = openreview.Client()
        from_profile = guest.register_user(email = 'celeste@mail.com', first = 'Celeste', last = 'Bok', password = helpers.strong_password)
        assert from_profile
        to_profile = guest.register_user(email = 'melisab@mail.com', first = 'Melissa', last = 'Bok', password = helpers.strong_password)
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
        from_profile = guest.register_user(email = 'lbahy@mail.com', first = 'Nadia', last = 'LBahy', password = helpers.strong_password)
        assert from_profile
        to_profile = guest.register_user(email = 'steph@mail.com', first = 'David', last = 'Steph', password = helpers.strong_password)
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

    def test_get_messages(self, client):

        messages = client.get_messages()
        assert messages

        messages = client.get_messages(status='sent')
        assert messages

        messages = openreview.tools.iterget_messages(client, status='sent')
        assert messages

    def test_get_notes_by_ids(self, client):
        notes = client.get_notes(invitation='Test.ws/2019/Conference/-/Submission', content = { 'title': 'Paper title'})
        assert len(notes) == 1        
       
        notes = client.get_notes_by_ids(ids = [notes[0].id])
        assert len(notes) == 1, 'notes is not empty'

    # def test_infer_notes(self, client):
    #     notes = client.get_notes(signature='openreview.net/Support')
    #     assert notes
    #     note = client.infer_note(notes[0].id)
    #     assert note

