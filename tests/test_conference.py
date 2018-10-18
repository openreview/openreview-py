from __future__ import absolute_import, division, print_function, unicode_literals
import openreview
import pytest

class TestConference():


    # def setup_method(self, method):
    #     self.client = openreview.Client(username = "openreview.net", password = "1234")
    #     assert self.client is not None, "Client is none"

    def test_create_conference(self, client):

        builder = openreview.conference.ConferenceBuilder(client)
        assert builder, 'builder is None'

        builder.set_conference_id('AKBC.ws/2019/Conference')

        conference = builder.get_result()
        assert conference, 'conference is None'
