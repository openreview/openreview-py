from __future__ import absolute_import

from .. import openreview
from .. import tools

class Conference(object):

    def __init__(self):
        self.groups = []

    def set_id(self, id):
        self.id = id

    def get_id(self):
        return self.id

    def set_conference_groups(self, groups):
        self.groups = groups

    def get_conference_groups(self):
        return self.groups


class ConferenceBuilder(object):

    def __init__(self, client):
        self.client = client
        self.conference = Conference()

    def __build_groups(self, conference_id):
        path_components = conference_id.split('/')
        paths = ['/'.join(path_components[0:index+1]) for index, path in enumerate(path_components)]
        print(paths)
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

        return groups


    def set_conference_id(self, id):
        self.conference.set_id(id)


    def get_result(self):

        id = self.conference.get_id()
        groups = self.__build_groups(id)
        self.conference.set_conference_groups(groups)
        return self.conference
