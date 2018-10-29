from __future__ import absolute_import

from .. import openreview
from .. import tools
from . import webfield
from . import invitation

class Conference(object):

    def __init__(self, client):
        self.client = client
        self.groups = []
        self.name = None
        self.header = {}
        self.invitationBuilder = invitation.InvitationBuilder(client)

    def set_id(self, id):
        self.id = id

    def get_id(self):
        return self.id

    def set_conference_name(self, name):
        self.name = name

    def get_conference_name(self):
        return self.name

    def set_conference_groups(self, groups):
        self.groups = groups

    def get_conference_groups(self):
        return self.groups

    def set_homepage_header(self, header):
        self.header = header

    def get_homepage_options(self):
        options = {}
        if self.name:
            options['subtitle'] = self.name
        if self.header:
            options['title'] = self.header.get('title')
            options['subtitle'] = self.header.get('subtitle')
            options['location'] = self.header.get('location')
            options['date'] = self.header.get('date')
            options['website'] = self.header.get('website')
            options['instructions'] = self.header.get('instructions')
            options['deadline'] = self.header.get('deadline')
        return options

    def open_submissions(self, mode = 'blind', due_date = None, subject_areas = []):
        options = {
            'due_date': due_date
        }
        return self.invitationBuilder.set_submission_invitation(self.id, options)



class ConferenceBuilder(object):

    def __init__(self, client):
        self.client = client
        self.conference = Conference(client)
        self.webfieldBuilder = webfield.WebfieldBuilder(client)


    def __build_groups(self, conference_id):
        path_components = conference_id.split('/')
        paths = ['/'.join(path_components[0:index+1]) for index, path in enumerate(path_components)]
        groups = []

        for p in paths:
            group = tools.get_group(self.client, id = p)

            if group is None:
                print('post group')
                group = self.client.post_group(openreview.Group(
                    id = p,
                    readers = ['everyone'],
                    nonreaders = [],
                    writers = [p],
                    signatories = [p],
                    signatures = ['~Super_User1'],
                    members = [])
                )

            groups.append(group)

        #update web pages
        for g in groups[:-1]:
            self.webfieldBuilder.set_landing_page(g)

        self.webfieldBuilder.set_home_page(groups[-1], self.conference.get_homepage_options())

        return groups


    def set_conference_id(self, id):
        self.conference.set_id(id)

    def set_conference_name(self, name):
        self.conference.set_conference_name(name)

    def set_homepage_header(self, header):
        self.conference.set_homepage_header(header)

    def get_result(self):

        id = self.conference.get_id()
        groups = self.__build_groups(id)
        self.conference.set_conference_groups(groups)
        return self.conference
