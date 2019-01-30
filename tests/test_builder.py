from __future__ import absolute_import, division, print_function, unicode_literals
import os
import datetime
import openreview
import pytest

class TestBuilder():

    def test_override_homepage(self, client):

        builder = openreview.conference.ConferenceBuilder(client)
        assert builder, 'builder is None'

        builder.set_conference_id('test.org/2019/Conference')
        conference = builder.get_result()
        assert conference, 'conference is None'

        groups = conference.get_conference_groups()
        assert groups
        assert len(groups) == 3
        home_group = groups[-1]
        assert home_group.id == 'test.org/2019/Conference'
        assert 'Venue homepage template' in home_group.web

        home_group.web = 'This is a webfield'
        client.post_group(home_group)

        conference = builder.get_result()
        groups = conference.get_conference_groups()
        assert 'This is a webfield' in groups[-1].web

        builder.set_override_homepage(True)
        conference = builder.get_result()
        groups = conference.get_conference_groups()
        assert 'Venue homepage template' in groups[-1].web

