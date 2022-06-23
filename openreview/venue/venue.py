from .invitation import InvitationBuilder

class Venue(object):

    def __init__(self, client, venue_id):

        self.client = client
        self.venue_id = venue_id
        self.submission_stage = None
        self.invitation_builder = InvitationBuilder(self)

    def get_id(self):
        return self.venue_id

    def get_meta_invitation_id(self):
        return f'{self.venue_id}/-/Edit'
    
    def set_submission_stage(self, stage):
        self.submission_stage = stage
        return self.invitation_builder.set_submission_invitation()      



