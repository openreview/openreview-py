from __future__ import absolute_import, division, print_function, unicode_literals
import os
import openreview
import pytest

class TestClient():

    def test_get_notes(self, client):
        notes = client.get_notes()
        assert len(notes) == 0, 'notes is not empty'

    def test_get_groups(self, client):
        groups = client.get_groups()
        assert len(groups) == 8, 'groups is empty'
        assert groups[0].id == '(anonymous)'
        assert groups[1].id == 'everyone'
        assert groups[2].id == '~'
        assert groups[3].id == '(guest)'
        assert groups[4].id == '~Super_User1'
        assert groups[5].id == 'openreview.net'
        assert groups[6].id == 'active_venues'
        assert groups[7].id == 'host'

    def test_get_invitations(self, client):
        invitations = client.get_invitations()
        assert len(invitations) == 1, 'invitations is not empty'
        assert invitations[0].id == '~/-/profiles'

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

    def test_guest_user(self):
        guest = openreview.Client()
        invitations = openreview.tools.get_submission_invitations(guest)
        assert len(invitations) == 0, "Invitations could not be retrieved for guest user"
        venues = openreview.tools.get_all_venues(guest)
        assert len(venues) == 0, "Venues could not be retrieved for guest user"

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

    def test_get_invitations(self, client):
        invitations = client.get_invitations(invitee = '~', pastdue = False)
        assert len(invitations) == 0

        invitations = client.get_invitations(invitee = True, duedate = True, details = 'replytoNote,repliedNotes')
        assert len(invitations) == 0

        invitations = client.get_invitations(invitee = True, duedate = True, replyto = True, details = 'replytoNote,repliedNotes')
        assert len(invitations) == 0

        invitations = client.get_invitations(invitee = True, duedate = True, tags = True, details = 'repliedTags')
        assert len(invitations) == 0



