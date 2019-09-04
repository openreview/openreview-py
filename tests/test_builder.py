from __future__ import absolute_import, division, print_function, unicode_literals
import os
import datetime
import json
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

    def test_web_set_landing_page(self, client):
        builder = openreview.conference.ConferenceBuilder(client)
        builder.set_conference_id("ds.cs.umass.edu/Test_I/2019/Conference")
        conference = builder.get_result()
        group = client.get_group(id='ds.cs.umass.edu/Test_I/2019')
        assert group.web,'Venue parent group missing webfield'

        # check webfield contains 'Conference'
        assert 'ds.cs.umass.edu/Test_I/2019/Conference' in group.web, 'Venue parent group missing child group'

        # add 'Party'
        child_str = ''', {'url': '/group?id=Party', 'name': 'Party'}'''
        start_pos = group.web.find('VENUE_LINKS')
        insert_pos = group.web.find('];', start_pos)
        group.web = group.web[:insert_pos] + child_str + group.web[insert_pos:]
        print(group.web)
        client.post_group(group)

        builder.set_conference_id("ds.cs.umass.edu/Test_I/2019/Workshop/WS_1")
        conference = builder.get_result()
        # check webfield contains 'Conference', 'Party' and 'Workshop'
        group = client.get_group(id='ds.cs.umass.edu/Test_I/2019')
        assert 'ds.cs.umass.edu/Test_I/2019/Conference' in group.web, 'Venue parent group missing child conference group'
        assert 'ds.cs.umass.edu/Test_I/2019/Workshop' in group.web, 'Venue parent group missing child workshop group'
        assert 'Party' in group.web, 'Venue parent group missing child inserted group'
