from __future__ import absolute_import


class Conference(object):

    def set_id(self, id):
        self.id = id

class ConferenceBuilder(object):

    def __init__(self, client):
        self.client = client
        self.conference = Conference()


    def set_conference_id(self, id):
        self.conference.set_id(id)


    def get_result(self):
        return self.conference
