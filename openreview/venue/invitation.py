


class InvitationBuilder(object):

    def __init__(self, client):
        self.client = client

    def set_submission_invitation(self, venue, submission_name, cdate, duedate):
        venue_config = venue.venue_config
        suport_group_id = venue_config.support_group_id
        self.client.post_invitation_edit(invitations=f'{suport_group_id}/Templates/-/Submission_Template',
            params={ 'venueid': venue_config.venue_id, 'cdate': cdate, 'duedate': duedate, 'name': submission_name},
            readers=[suport_group_id],
            writers=[suport_group_id],
            signatures=[suport_group_id]
        )
