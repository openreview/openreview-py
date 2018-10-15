from __future__ import absolute_import, division, print_function, unicode_literals
import openreview
import pytest

class TestConference():


    def setup_method(self, method):
        self.baseurl = 'http://localhost:3000'
        self.client = openreview.Client(baseurl = self.baseurl, username = "OpenReview.net", password = "d0ntf33dth3tr0lls")
        assert self.client is not None, "Client is none"

    def test_create_conference(self):

        openreview.conference.pepe
        #builder = openreview.conference.ConferenceBuilder(self.client)
        #assert builder, 'builder is None'
