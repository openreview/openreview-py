from openreview import *

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

        response = self.client.login_user(username = "OpenReview.net")
        assert response, "valid token not found"

    def test_guest_user(self):
        invitations = get_submission_invitations(self.guest)
        assert invitations, "Invitations could not be retrieved for guest user"
        venues = get_all_venues(self.guest)
        assert venues, "Venues could not be retrieved for guest user"
