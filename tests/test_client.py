from __future__ import absolute_import, division, print_function, unicode_literals
import os
import datetime
import openreview
import pytest

class TestClient():

    def test_get_groups(self, client):
        groups = client.get_groups()
        assert len(groups) == 51, 'missing groups'
        group_names = [g.id for g in groups]
        assert '(anonymous)' in group_names
        assert 'everyone' in group_names
        assert '~' in group_names
        assert '(guest)' in group_names
        assert '~Super_User1' in group_names
        assert 'openreview.net' in group_names
        assert 'active_venues' in group_names
        assert 'host' in group_names
        assert 'test.org/2019/Conference/Reviewers/Declined' in group_names

    def test_create_client(self, client, test_client):

        client = openreview.Client()
        assert client
        assert not client.token
        assert not client.profile

        os.environ["OPENREVIEW_USERNAME"] = "openreview.net"

        with pytest.raises(openreview.OpenReviewException, match=r'.*Password is missing.*'):
            client = openreview.Client()

        os.environ["OPENREVIEW_PASSWORD"] = "1234"

        client = openreview.Client()
        assert client
        assert client.token
        assert client.profile
        assert '~Super_User1' == client.profile.id

        with pytest.raises(openreview.OpenReviewException, match=r'.*Invalid username or password.*'):
            client = openreview.Client(username='nouser@mail.com')

        with pytest.raises(openreview.OpenReviewException, match=r'.*Invalid username or password.*'):
            client = openreview.Client(username='nouser@mail.com', password='1234')

        client = openreview.Client(token='Bearer ' + test_client.token)
        assert client
        assert client.token
        assert client.profile
        assert '~Test_User1' == client.profile.id

        client = openreview.Client(token='Bearer ' + test_client.token, username='test@mail.com', password='1234')
        assert client
        assert client.token
        assert client.profile
        assert '~Test_User1' == client.profile.id

    def test_login_user(self):
        try:
            guest = openreview.Client()
            guest.login_user()
        except openreview.OpenReviewException as e:
            assert ["Email is missing"] in e.args, "guest log in did not produce correct error"

        try:
            guest.login_user(username = "openreview.net")
        except openreview.OpenReviewException as e:
            assert ["Password is missing"] in e.args, "super user log in did not produce correct error"

        try:
            guest.login_user(username = "openreview.net", password = "1111")
        except openreview.OpenReviewException as e:
            assert ["Invalid username or password"] in e.args, "super user log in did not produce correct error"

        response = guest.login_user(username = "openreview.net", password = "1234")
        assert response
        print(response)

    def test_get_notes_with_details(self, client):
        notes = client.get_notes(invitation = 'ICLR.cc/2018/Conference/-/Blind_Submission', details='all')
        assert len(notes) == 0, 'notes is empty'

    def test_get_profile(self, client):
        profile = client.get_profile('openreview.net')
        assert profile, "Could not get the profile by email"
        assert isinstance(profile, openreview.Profile)
        assert profile.id == '~Super_User1'

        profile = client.get_profile('~Super_User1')
        assert profile, "Could not get the profile by id"
        assert isinstance(profile, openreview.Profile)
        assert 'openreview.net' in profile.content['emails']

        with pytest.raises(openreview.OpenReviewException, match=r'.*Profile not found.*'):
            profile = client.get_profile('mbok@sss.edu')

        assert openreview.tools.get_profile(client, '~Super_User1')
        assert not openreview.tools.get_profile(client, 'mbok@sss.edu')

    def test_get_profiles(self, client):
        guest = openreview.Client()
        guest.register_user(email = 'mbok@mail.com', first = 'Melisa', last = 'Bok', password = '1234')
        guest.register_user(email = 'andrew@mail.com', first = 'Andrew', last = 'McCallum', password = '1234')

        profiles = client.get_profiles(['mbok@mail.com'])
        assert profiles, "Could not get the profile by email"
        assert isinstance(profiles, dict)
        assert isinstance(profiles['mbok@mail.com'], openreview.Profile)
        assert profiles['mbok@mail.com'].id == '~Melisa_Bok1'

        profiles = client.get_profiles(['~Melisa_Bok1', '~Andrew_McCallum1'])
        assert profiles, "Could not get the profile by id"
        assert isinstance(profiles, list)
        assert len(profiles) == 2
        assert '~Melisa_Bok1' in profiles[1].id
        assert '~Andrew_McCallum1' in profiles[0].id

        profiles = client.get_profiles([])
        assert len(profiles) == 0

        profiles = client.get_profiles()
        assert len(profiles) == 1
        assert profiles[0].id == '~Super_User1'

        assert '~Melisa_Bok1' == client.get_profiles(id = '~Melisa_Bok1')[0].id
        assert '~Melisa_Bok1' == client.get_profiles(email = 'mbok@mail.com')[0].id
        assert '~Melisa_Bok1' == client.get_profiles(first = 'Melisa')[0].id
        assert len(client.get_profiles(id = '~Melisa_Bok2')) == 0
        assert len(client.get_profiles(email = 'mail@mail.com')) == 0
        assert len(client.get_profiles(first = 'Anna')) == 0

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

    def test_get_invitations_by_invitee(self, client):
        invitations = client.get_invitations(invitee = '~', pastdue = False)
        assert len(invitations) == 0

        invitations = client.get_invitations(invitee = True, duedate = True, details = 'replytoNote,repliedNotes')
        assert len(invitations) == 0

        invitations = client.get_invitations(invitee = True, duedate = True, replyto = True, details = 'replytoNote,repliedNotes')
        assert len(invitations) == 0

        invitations = client.get_invitations(invitee = True, duedate = True, tags = True, details = 'repliedTags')
        assert len(invitations) == 0

    def test_get_notes_by_content(self, client):

        now = datetime.datetime.utcnow()
        builder = openreview.conference.ConferenceBuilder(client)
        assert builder, 'builder is None'

        builder.set_conference_id('Test.ws/2019/Conference')
        builder.set_submission_stage(due_date = now + datetime.timedelta(minutes = 100))

        conference = builder.get_result()
        assert conference, 'conference is None'

        note = openreview.Note(invitation = conference.get_submission_id(),
            readers = ['mbok@mail.com', 'andrew@mail.com'],
            writers = ['mbok@mail.com', 'andrew@mail.com'],
            signatures = ['~Super_User1'],
            content = {
                'title': 'Paper title',
                'abstract': 'This is an abstract',
                'authorids': ['mbok@mail.com', 'andrew@mail.com'],
                'authors': ['Melisa Bok', 'Andrew Mc'],
                'pdf': '/pdf/22234qweoiuweroi22234qweoiuweroi12345678.pdf'
            }
        )
        note = client.post_note(note)
        assert note

        notes = client.get_notes(content = { 'title': 'Paper title'})
        assert len(notes) == 3

        notes = client.get_notes(content = { 'title': 'Paper title3333'})
        assert len(notes) == 0

        notes = list(openreview.tools.iterget_notes(client, content = { 'title': 'Paper title'}))
        assert len(notes) == 3

        notes = list(openreview.tools.iterget_notes(client, content = { 'title': 'Paper title333'}))
        assert len(notes) == 0

    def test_merge_profile(self, client):
        guest = openreview.Client()
        from_profile = guest.register_user(email = 'celeste@mail.com', first = 'Celeste', last = 'Bok', password = '1234')
        assert from_profile
        to_profile = guest.register_user(email = 'melisab@mail.com', first = 'Melissa', last = 'Bok', password = '5678')
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






