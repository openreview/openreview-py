from openreview import *

class TestClient():

    def setup_method(self, method):
        # Password should be saved in the environment variable OPENREVIEW_PASSWORD
        self.client = openreview.Client(baseurl = 'https://dev.openreview.net', username = "OpenReview.net")
        assert self.client is not None, "Client is none"

    def test_get_submission_invitations(self):
        invitations = get_submission_invitations(self.client)
        assert invitations, 'invitations is None'
        invitations = get_submission_invitations(self.client,"all")
        assert invitations, 'invitations is None'
        invitations = get_submission_invitations(self.client,"open")
        assert invitations, 'invitations is None'
        invitations = get_submission_invitations(self.client,"closed")
        assert invitations, 'invitations is None'
        invitations = get_submission_invitations(self.client,"somerandomsubmission")
        assert invitations==[], 'invitations expected as [], but retrieved something else'

