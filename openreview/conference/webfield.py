from __future__ import absolute_import

import os
import json



class WebfieldBuilder(object):

    def __init__(self, client):
        self.client = client

    def __build_options(self, default, options):

        merged_options = {}
        for k in default:
            merged_options[k] = default[k]

        for o in options:
            merged_options[o] = options[o]

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

        with open(os.path.join(os.path.dirname(__file__), 'templates/landingWebfield.js')) as f:
            content = f.read()
            content = content.replace("var GROUP_ID = '';", "var GROUP_ID = '" + group.id + "';")
            content = content.replace("var HEADER = {};", "var HEADER = " + json.dumps(header) + ";")
            content = content.replace("var VENUE_LINKS = [];", "var VENUE_LINKS = " + json.dumps(links) + ";")
            group.web = content
            return self.client.post_group(group)


    def set_home_page(self, group, layout, options = {}):

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

        template_name = 'simpleConferenceWebfield.js'

        if layout == 'tabs':
            template_name = 'tabsConferenceWebfield.js'

        with open(os.path.join(os.path.dirname(__file__), 'templates/' + template_name)) as f:
            content = f.read()
            content = content.replace("var CONFERENCE_ID = '';", "var CONFERENCE_ID = '" + group.id + "';")
            content = content.replace("var HEADER = {};", "var HEADER = " + json.dumps(header) + ";")
            content = content.replace("var REVIEWERS_NAME = '';", "var REVIEWERS_NAME = '" + options.get('reviewers_name') + "';")
            content = content.replace("var AREA_CHAIRS_NAME = '';", "var AREA_CHAIRS_NAME = '" + options.get('area_chairs_name') + "';")
            content = content.replace("var SUBMISSION_ID = '';", "var SUBMISSION_ID = '" + options.get('submission_id') + "';")
            content = content.replace("var BLIND_SUBMISSION_ID = '';", "var BLIND_SUBMISSION_ID = '" + options.get('submission_id') + "';")
            content = content.replace("var AREA_CHAIRS_ID = '';", "var AREA_CHAIRS_ID = '" + options.get('area_chairs_id') + "';")
            content = content.replace("var REVIEWERS_ID = '';", "var REVIEWERS_ID = '" + options.get('reviewers_id') + "';")
            content = content.replace("var PROGRAM_CHAIRS_ID = '';", "var PROGRAM_CHAIRS_ID = '" + options.get('program_chairs_id') + "';")
            content = content.replace("var AUTHORS_ID = '';", "var AUTHORS_ID = '" + options.get('authors_id') + "';")

            group.web = content
            return self.client.post_group(group)

    def set_recruit_page(self, conference_id, invitation, options = {}):

        default_header = {
            'title': conference_id,
            'subtitle': conference_id,
            'location': 'TBD',
            'date': 'TBD',
            'website': 'nourl',
            'instructions': '',
            'deadline': 'TBD'
        }

        header = self.__build_options(default_header, options)

        with open(os.path.join(os.path.dirname(__file__), 'templates/recruitResponseWebfield.js')) as f:
            content = f.read()
            content = content.replace("var CONFERENCE_ID = '';", "var CONFERENCE_ID = '" + conference_id + "';")
            content = content.replace("var HEADER = {};", "var HEADER = " + json.dumps(header) + ";")
            invitation.web = content
            return self.client.post_invitation(invitation)


    def set_author_page(self, conference_id, group, options = {}):

        default_header = {
            'title': group.id,
            'instructions': '',
            'schedule': 'TBD'
        }

        header = self.__build_options(default_header, options)

        with open(os.path.join(os.path.dirname(__file__), 'templates/authorWebfield.js')) as f:
            content = f.read()
            content = content.replace("var CONFERENCE_ID = '';", "var CONFERENCE_ID = '" + conference_id + "';")
            content = content.replace("var SUBMISSION_ID = '';", "var SUBMISSION_ID = '" + header.get('submission_id') + "';")
            content = content.replace("var HEADER_TEXT = '';", "var HEADER_TEXT = '" + header.get('title') + "';")
            content = content.replace("var INSTRUCTIONS = '';", "var INSTRUCTIONS = '" + header.get('instructions') + "';")
            content = content.replace("var SCHEDULE_HTML = '';", "var SCHEDULE_HTML = '" + header.get('schedule') + "';")
            group.web = content
            return self.client.post_group(group)

    def set_reviewer_page(self, conference_id, group, options = {}):

        reviewers_name = group.id.split('/')[-1].replace('_', ' ')

        default_header = {
            'title': reviewers_name + ' Console',
            'instructions': '<p class="dark">This page provides information and status \
            updates for the ' + group.id + '. It will be regularly updated as the conference \
            progresses, so please check back frequently for news and other updates.</p>',
            'schedule': '<h4>Coming Soon</h4>\
            <p>\
                <em><strong>Please check back later for updates.</strong></em>\
            </p>',
            'reviewers_name': reviewers_name
        }

        header = self.__build_options(default_header, options)

        with open(os.path.join(os.path.dirname(__file__), 'templates/reviewersWebfield.js')) as f:
            content = f.read()
            content = content.replace("var CONFERENCE_ID = '';", "var CONFERENCE_ID = '" + conference_id + "';")
            content = content.replace("var REVIEWERS_NAME = '';", "var REVIEWERS_NAME = '" + reviewers_name + "';")
            content = content.replace("var HEADER_TEXT = '';", "var HEADER_TEXT = '" + header.get('title') + "';")
            content = content.replace("var INSTRUCTIONS = '';", "var INSTRUCTIONS = '" + header.get('instructions') + "';")
            content = content.replace("var SCHEDULE_HTML = '';", "var SCHEDULE_HTML = '" + header.get('schedule') + "';")
            group.web = content
            return self.client.post_group(group)

