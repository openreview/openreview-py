from __future__ import absolute_import

import os
import json



class WebfieldBuilder(object):

    def __init__(self, client):
        self.client = client

    def __build_options(self, default, options):

        merged_options = {}
        for k in default:
            if k in options:
                merged_options[k] = options[k]
            else:
                merged_options[k] = default[k]
        return merged_options


    def set_landing_page(self, group, options = {}):

        default_header = {
            'title': group.id,
            'description': ''
        }

        children_groups = self.client.get_groups(regex = group.id + '/[^/]+/?$')

        links = []

        for children in children_groups:
            links.append({ 'url': '/group?id=' + children.id, 'name': children.id})

        header = self.__build_options(default_header, options)

        with open(os.path.join(os.path.dirname(__file__), 'templates/landing.js')) as f:
            content = f.read()
            content = content.replace("var GROUP_ID = '';", "var GROUP_ID = '" + group.id + "';")
            content = content.replace("var HEADER = {};", "var HEADER = " + json.dumps(header) + ";")
            content = content.replace("var VENUE_LINKS = [];", "var VENUE_LINKS = " + json.dumps(links) + ";")
            group.web = content
            return self.client.post_group(group)


    def set_home_page(self, group, options = {}):

        default_header = {
            'title': group.id,
            'subtitle': group.id,
            'location': 'TBD',
            'date': 'TBD',
            'website': 'nourl',
            'instructions': '',
            'deadline': 'TBD'
        }

        header = self.__build_options(default_header, options)

        with open(os.path.join(os.path.dirname(__file__), 'templates/homepage.js')) as f:
            content = f.read()
            content = content.replace("var CONFERENCE_ID = 'venue.org/Conference';", "var CONFERENCE_ID = '" + group.id + "';")
            content = content.replace("var HEADER = {};", "var HEADER = " + json.dumps(header) + ";")
            group.web = content
            return self.client.post_group(group)

