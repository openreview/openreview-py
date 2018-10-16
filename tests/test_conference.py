from __future__ import absolute_import, division, print_function, unicode_literals
import openreview
import pytest

class TestConference():


    def setup_method(self, method):
        self.baseurl = 'http://localhost:3000'
        self.client = openreview.Client(baseurl = self.baseurl, username = "OpenReview.net", password = "d0ntf33dth3tr0lls")
        assert self.client is not None, "Client is none"

    def test_create_conference(self):

        builder = openreview.conference.ConferenceBuilder(self.client)
        assert builder, 'builder is None'

        builder.set_conference_id('AKBC.ws/2019/Conference')

        conference = builder.get_result()
        assert conference, 'conference is None'
