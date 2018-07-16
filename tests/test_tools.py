from openreview import *

class TestTools():

    def setup_method(self, method):
        # Password should be saved in the environment variable OPENREVIEW_PASSWORD
        self.client = openreview.Client(baseurl = 'https://dev.openreview.net', username = "OpenReview.net")
        assert self.client is not None, "Client is none"

    def test_get_submission_invitations(self):
        invitations = get_submission_invitations(self.client)
        assert invitations, 'invitations is None'

    def test_get_all_venues(self):
        venues = get_all_venues(self.client)
        assert venues, "Venues could not be retrieved"
