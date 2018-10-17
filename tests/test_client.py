from __future__ import absolute_import, division, print_function, unicode_literals
import os
import openreview
import pytest

@pytest.fixture(scope='class')
def client():
    client = openreview.Client()
    assert client is not None, "Client is none"
    res = client.register_user(email = 'OpenReview.net', first = 'Super', last = 'User', password = '1234')
    assert res, "Res i none"
    res = client.activate_user('OpenReview.net', {
        'names': [
                {
                    'first': 'Super',
                    'last': 'User',
                    'username': '~Super_User1'
                }
            ],
        'emails': ['openreview.net'],
        'preferredEmail': 'openreview.net'
        })
    assert res, "Res i none"
    yield client

class TestClient():

    def test_get_notes(self, client):
        notes = client.get_notes()
        assert len(notes) == 0, 'notes is not empty'

    def test_get_groups(self, client):
        groups = client.get_groups()
        assert len(groups) == 6, 'groups is empty'
        assert groups[0].id == '(anonymous)'
        assert groups[1].id == 'everyone'
        assert groups[2].id == '~'
        assert groups[3].id == '(guest)'
        assert groups[4].id == 'active_venues'
        assert groups[5].id == 'host'

    def test_get_invitations(self, client):
        invitations = client.get_invitations()
        assert len(invitations) == 0, 'invitations is not empty'

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

    # def test_get_notes_with_details(self):
    #     notes = self.client.get_notes(invitation = 'ICLR.cc/2018/Conference/-/Blind_Submission', details='all')
    #     assert notes, 'notes is None'
    #     assert len(notes) > 0, 'notes is empty'
    #     assert notes[0].details, 'notes does not have details'
    #     assert isinstance(notes[0].details, dict), 'notes does not have details'
    #     assert isinstance(notes[0].details['tags'], list), 'note does not have tags'
    #     assert isinstance(notes[0].details['replyCount'], int), 'note does not have replyCount'
    #     assert isinstance(notes[0].details['revisions'], bool), 'note does not have revisions'
    #     assert isinstance(notes[0].details['overwriting'], list), 'note does not have overwriting'
    #     assert isinstance(notes[0].details['writable'], bool), 'note does not have writable'

    # # def test_get_pdf(self):
    # #     # Testing a valid PDF id
    # #     pdf_content = self.client.get_pdf(id='HJBhFJTF-')
    # #     assert pdf_content, "get_pdf did not return anything"

    # #     # Testing an invalid PDF id
    # #     try:
    # #         pdf_content = self.client.get_pdf(id='AnInvalidID')
    # #     except openreview.OpenReviewException as e:
    # #         assert 'Not Found' in e.args[0][0]['type'], "Incorrect error observed with invalid Note ID"

    # def test_put_pdf(self, client):
    #     # Calling put_pdf without a valid file name
    #     try:
    #         response = client.put_pdf(fname='')
    #     except IOError as e:
    #         assert "No such file or directory" in e.args, "Incorrect error when no file name is given"

    #     # Creating an empty PDF and then uploading it
    #     f = open("empty_test.pdf",'wb')
    #     f.close()
    #     response = client.put_pdf('empty_test.pdf')

    #     if os.path.exists("empty_test.pdf"):
    #         os.remove("empty_test.pdf")
    #     assert "/pdf/" in response, "PDF not uploaded properly"

    def test_get_profile(self, client):
        profile = client.get_profile('openreview.net')
        assert profile, "Could not get the profile by email"
        assert isinstance(profile, openreview.Profile)
        assert profile.id == '~Super_User1'

        profile = client.get_profile('~Super_User1')
        assert profile, "Could not get the profile by id"
        assert isinstance(profile, openreview.Profile)
        assert 'o****t' in profile.content['emails']

        with pytest.raises(openreview.OpenReviewException, match=r'.*Profile not found.*'):
            profile = client.get_profile('mbok@sss.edu')

    # def test_get_profiles(self):
    #     profiles = self.client.get_profiles(['mbok@cs.umass.edu'])
    #     assert profiles, "Could not get the profile by email"
    #     assert isinstance(profiles, dict)
    #     assert isinstance(profiles['mbok@cs.umass.edu'], openreview.Profile)
    #     assert profiles['mbok@cs.umass.edu'].id == '~Melisa_TestBok1'

    #     profiles = self.client.get_profiles(['~Melisa_TestBok1', '~Andrew_McCallum1'])
    #     assert profiles, "Could not get the profile by id"
    #     assert isinstance(profiles, list)
    #     print(profiles)
    #     assert len(profiles) == 2
    #     assert '~Melisa_TestBok1' in profiles[1].id
    #     assert '~Andrew_McCallum1' in profiles[0].id

    #     profiles = self.client.get_profiles([])
    #     assert len(profiles) == 0

    # def test_get_invitations(self):
    #     invitations = self.client.get_invitations(invitee = '~', pastdue = False)
    #     assert invitations
    #     assert len(invitations) > 0

    #     invitations = self.client.get_invitations(invitee = True, duedate = True, details = 'replytoNote,repliedNotes')
    #     assert invitations
    #     assert len(invitations) > 0
    #     assert invitations[0].details

    #     invitations = self.client.get_invitations(invitee = True, duedate = True, replyto = True, details = 'replytoNote,repliedNotes')
    #     assert len(invitations) == 0

    #     invitations = self.client.get_invitations(invitee = True, duedate = True, tags = True, details = 'repliedTags')
    #     assert len(invitations) == 0



