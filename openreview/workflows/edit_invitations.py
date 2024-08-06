import os
import time
import datetime
from .. import tools
from openreview.api import Invitation

class EditInvitationsBuilder(object):

    def __init__(self, client, venue_id, update_wait_time=5000):
        self.client = client
        self.venue_id = venue_id
        self.domain_group = client.get_group(self.venue_id)
        self.update_wait_time = 1000 if 'localhost' in client.baseurl else update_wait_time
        self.spleep_time_for_logs = 0.5 if 'localhost' in client.baseurl else 10
        self.update_date_string = "#{4/mdate} + " + str(self.update_wait_time)

    def save_invitation(self, invitation, replacement=None):
        self.client.post_invitation_edit(invitations=self.get_content_value('meta_invitation_id', f'{self.venue_id}/-/Edit'),
            readers=[self.venue_id],
            writers=[self.venue_id],
            signatures=[self.venue_id],
            replacement=replacement,
            invitation=invitation
        )
        invitation = self.client.get_invitation(invitation.id)

        if invitation.date_processes and len(invitation.date_processes[0]['dates']) > 1 and self.update_date_string == invitation.date_processes[0]['dates'][1]:
            process_logs = self.client.get_process_logs(id=invitation.id + '-0-1', min_sdate = invitation.tmdate + self.update_wait_time - 1000)
            count = 0
            max_count = 1800 / self.spleep_time_for_logs
            while len(process_logs) == 0 and count < max_count: ## wait up to 30 minutes
                time.sleep(self.spleep_time_for_logs)
                process_logs = self.client.get_process_logs(id=invitation.id + '-0-1', min_sdate = invitation.tmdate + self.update_wait_time - 1000)
                count += 1

            if len(process_logs) == 0:
                raise openreview.OpenReviewException('Time out waiting for invitation to complete: ' + invitation.id)

            if process_logs[0]['status'] == 'error':
                raise openreview.OpenReviewException('Error saving invitation: ' + invitation.id)

        return invitation
    
    def expire_invitation(self, invitation_id):
        invitation = tools.get_invitation(self.client, id=invitation_id)

        if invitation:
            self.save_invitation(invitation=Invitation(id=invitation.id,
                    expdate=tools.datetime_millis(datetime.datetime.utcnow()),
                    signatures=[self.venue_id]
                )
            )

    def get_process_content(self, file_path):
        process = None
        with open(os.path.join(os.path.dirname(__file__), file_path)) as f:
            process = f.read()
            return process

    def get_content_value(self, field_name, default_value=None):
        if self.domain_group and self.domain_group.content:
            return self.domain_group.content.get(field_name, {}).get('value', default_value)
        return default_value

    def set_edit_submission_deadlines_invitation(self, invitation_id, process_file=None):

        venue_id = self.venue_id
        deadline_invitation_id = invitation_id + '/Deadlines'

        invitation = Invitation(
            id = deadline_invitation_id,
            invitees = [venue_id],
            signatures = [venue_id],
            readers = [venue_id],
            writers = [venue_id],
            edit = {
                'content': {
                    'activation_date': { 
                        'value': {
                            'param': {
                                'type': 'date',
                                'range': [ 0, 9999999999999 ],
                                'optional': True,
                                'deletable': True
                            }
                        }
                    },
                    'deadline': { 
                        'value': {
                            'param': {
                                'type': 'date',
                                'range': [ 0, 9999999999999 ],
                                'optional': True,
                                'deletable': True
                            }
                        }
                    }
                },
                'signatures': [self.get_content_value('program_chairs_id', f'{venue_id}/Program_Chairs')],
                'readers': [venue_id],
                'writers': [venue_id],
                'invitation': {
                    'id': invitation_id,
                    'signatures': [venue_id],
                    'cdate': '${2/content/activation_date/value}',
                    'duedate': '${2/content/deadline/value}',
                    'expdate': '${2/content/deadline/value}+1800000' ## 30 minutes buffer period
                }
            }
        )

        if process_file:
            invitation.process = self.get_process_content(f'process/{process_file}')  

        self.save_invitation(invitation, replacement=True)
        return invitation