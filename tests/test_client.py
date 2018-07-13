import openreview

class TestClient():

    def setup_method(self, method):
        # Password should be saved in the environment variable OPENREVIEW_PASSWORD
        self.client = openreview.Client(baseurl = 'https://dev.openreview.net', username = "OpenReview.net")
        assert self.client is not None, "Client is none"

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

