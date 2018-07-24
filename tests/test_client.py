import openreview

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
            assert "Username/email is missing" in e.message, "guest log in did not produce correct error"

        response = self.guest.login_user(username = "OpenReview.net")
        assert response, "valid token not found"

    def test_guest_user(self):
        invitations = openreview.get_submission_invitations(self.guest)
        assert invitations, "Invitations could not be retrieved for guest user"
        venues = openreview.get_all_venues(self.guest)
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
