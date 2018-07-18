from openreview import *

class TestTools():

    def setup_method(self, method):
    	self.baseurl = 'https://dev.openreview.net'
        # Password should be saved in the environment variable OPENREVIEW_PASSWORD
        self.client = openreview.Client(baseurl = self.baseurl, username = "OpenReview.net")
        assert self.client is not None, "Client is none"

    def test_get_submission_invitations(self):
        invitations = get_submission_invitations(self.client)
        assert invitations, "Invitations could not be retrieved"

    def test_get_all_venues(self):
        venues = get_all_venues(self.client)
        assert venues, "Venues could not be retrieved"
