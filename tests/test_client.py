from __future__ import absolute_import, division, print_function, unicode_literals
import os
import openreview
import pytest

class TestClient():

    def setup_method(self, method):
        self.baseurl = 'https://dev.openreview.net'
        # Password should be saved in the environment variable OPENREVIEW_PASSWORD
        self.client = openreview.Client(baseurl = self.baseurl, username = "OpenReview.net")
        assert self.client is not None, "Client is none"
        self.guest = openreview.Client(baseurl = self.baseurl)
        assert self.guest is not None, "Guest is none"

    def test_get_notes(self):
        notes = self.client.get_notes()
        assert notes, 'notes is None'
        assert len(notes) == 1000, 'notes is not max limit'

    def test_get_groups(self):
        groups = self.client.get_groups()
        assert groups, 'groups is None'
        assert len(groups) == 1004, 'groups is not max limit'

    def test_get_invitations(self):
        invitations = self.client.get_invitations()
        assert invitations, 'invitations is None'
        assert len(invitations) == 1000, 'invitations is not max limit'

    def test_login_user(self):
        try:
            response = self.guest.login_user()
        except openreview.OpenReviewException as e:
            assert ["Email is missing"] in e.args, "guest log in did not produce correct error"

        response = self.guest.login_user(username = "OpenReview.net")
        assert response, "valid token not found"

    def test_guest_user(self):
        invitations = openreview.tools.get_submission_invitations(self.guest)
        assert invitations, "Invitations could not be retrieved for guest user"
        venues = openreview.tools.get_all_venues(self.guest)
        assert venues, "Venues could not be retrieved for guest user"

    def test_get_notes_with_details(self):
        notes = self.client.get_notes(invitation = 'ICLR.cc/2018/Conference/-/Blind_Submission', details='all')
        assert notes, 'notes is None'
        assert len(notes) > 0, 'notes is empty'
        assert notes[0].details, 'notes does not have details'
        assert isinstance(notes[0].details, dict), 'notes does not have details'
        assert isinstance(notes[0].details['tags'], list), 'note does not have tags'
        assert isinstance(notes[0].details['replyCount'], int), 'note does not have replyCount'
        assert isinstance(notes[0].details['revisions'], bool), 'note does not have revisions'
        assert isinstance(notes[0].details['overwriting'], list), 'note does not have overwriting'
        assert isinstance(notes[0].details['writable'], bool), 'note does not have writable'

    # def test_get_pdf(self):
    #     # Testing a valid PDF id
    #     pdf_content = self.client.get_pdf(id='HJBhFJTF-')
    #     assert pdf_content, "get_pdf did not return anything"

    #     # Testing an invalid PDF id
    #     try:
    #         pdf_content = self.client.get_pdf(id='AnInvalidID')
    #     except openreview.OpenReviewException as e:
    #         assert 'Not Found' in e.args[0][0]['type'], "Incorrect error observed with invalid Note ID"

    def test_put_pdf(self):
        # Calling put_pdf without a valid file name
        try:
            response = self.client.put_pdf(fname='')
        except IOError as e:
            assert "No such file or directory" in e.args, "Incorrect error when no file name is given"

        # Creating an empty PDF and then uploading it
        f = open("empty_test.pdf",'wb')
        f.close()
        response = self.client.put_pdf('empty_test.pdf')

        if os.path.exists("empty_test.pdf"):
            os.remove("empty_test.pdf")
        assert "/pdf/" in response, "PDF not uploaded properly"

    def test_get_profile(self):
        profile = self.client.get_profile('mbok@cs.umass.edu')
        assert profile, "Could not get the profile by email"
        assert isinstance(profile, openreview.Profile)
        assert profile.id == '~Melisa_TestBok1'

        profile = self.client.get_profile('~Melisa_TestBok1')
        assert profile, "Could not get the profile by id"
        assert isinstance(profile, openreview.Profile)
        assert 'mbok@cs.umass.edu' in profile.content['emails']

        with pytest.raises(openreview.OpenReviewException, match=r'.*Profile not found.*'):
            profile = self.client.get_profile('mbok@sss.edu')

    def test_get_profiles(self):
        profiles = self.client.get_profiles(['mbok@cs.umass.edu'])
        assert profiles, "Could not get the profile by email"
        assert isinstance(profiles, dict)
        assert isinstance(profiles['mbok@cs.umass.edu'], openreview.Profile)
        assert profiles['mbok@cs.umass.edu'].id == '~Melisa_TestBok1'

        profiles = self.client.get_profiles(['~Melisa_TestBok1', '~Andrew_McCallum1'])
        assert profiles, "Could not get the profile by id"
        assert isinstance(profiles, list)
        print(profiles)
        assert len(profiles) == 2
        assert '~Melisa_TestBok1' in profiles[1].id
        assert '~Andrew_McCallum1' in profiles[0].id

        profiles = self.client.get_profiles([])
        assert len(profiles) == 0

    def test_get_invitations(self):
        invitations = self.client.get_invitations(invitee = '~', pastdue = False)
        assert invitations
        assert len(invitations) > 0

        invitations = self.client.get_invitations(invitee = True, duedate = True, details = 'replytoNote,repliedNotes')
        assert invitations
        assert len(invitations) > 0
        assert invitations[0].details

        invitations = self.client.get_invitations(invitee = True, duedate = True, replyto = True, details = 'replytoNote,repliedNotes')
        assert len(invitations) == 0

        invitations = self.client.get_invitations(invitee = True, duedate = True, tags = True, details = 'repliedTags')
        assert len(invitations) == 0



