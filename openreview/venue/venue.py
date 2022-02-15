import datetime
from enum import Enum
from . import group
from . import invitation

from .. import tools
from openreview import api

class VenueConfig(object):

    class Anonymity(Enum):
        DOUBLE_BLIND = 0
        SINGLE_BLIND = 1
        NONE = 2

    def __init__(self, client, venue_id, name, short_name, website, contact_info, program_chair_ids, program_chair_name, anonymity=Anonymity.DOUBLE_BLIND, use_area_chairs=False, year=None, area_chair_name='Area_Chairs', submission_name='Submission', support_group_id='OpenReview.net/Support'):
        self.client = client
        self.support_group_id = support_group_id
        self.venue_id = venue_id
        self.name = name
        self.short_name = short_name
        self.website = website
        self.contact_info = contact_info
        self.year = year if year else datetime.datetime.now().year
        self.use_area_chairs = use_area_chairs
        self.program_chair_ids = program_chair_ids
        self.program_chair_name = program_chair_name
        self.anonymity = anonymity
        self.area_chair_name = area_chair_name
        self.submission_name = submission_name

class Venue(object):
    
    def __init__(self, client, venue_config):
        self.client = client
        self.venue_config  = venue_config
        self.group_builder = group.GroupBuilder(client)
        self.invitation_builder = invitation.InvitationBuilder(client)

    def get_submission_id(self):
        venue_config = self.venue_config
        return venue_config.venue_id + '/-/' + venue_config.submission_name

    def get_blind_submission_id(self):
        venue_config = self.venue_config
        name = venue_config.name
        if venue_config.anonymity is VenueConfig.Anonymity.DOUBLE_BLIND:
            name = 'Blind_' + name
        return venue_config.venue_id + '/-/' + name

    def get_program_chairs_id(self):
        venue_config = self.venue_config
        return venue_config.venue_id + '/' + venue_config.program_chair_name

    def get_area_chairs_id(self):
        venue_config = self.venue_config
        return venue_config.venue_id + '/' + venue_config.area_chair_name

    def get_reviewers_id(self):
        venue_config = self.venue_config
        return venue_config.venue_id + '/Reviewers'

    def get_homepage_options(self):
        options = {}
        config =self.venue_config
        options['title'] = config.name
        options['short'] = config.short_name
        options['location'] = 'TBD'
        options['date'] = 'TBD'
        options['website'] = config.website
        options['instructions'] = ''
        options['deadline'] = 'TBD'
        options['contact'] = config.contact_info
        return options

    def setup(self):
        self.group_builder.set_groups(self)

    def set_submission_stage(self, name='Submission', cdate=None, duedate=None):
        self.invitation_builder.set_submission_invitation(self, name, cdate, duedate)