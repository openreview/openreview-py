import os
import time
import datetime
from .. import tools
from openreview.api import Invitation

class EditInvitationBuilder(object):

    def __init__(self, venue):
        self.client = venue.client
        self.venue = venue
        self.venue_id = venue.venue_id

    def save_invitation(self, invitation, replacement=None):
        self.client.post_invitation_edit(invitations=self.venue.get_meta_invitation_id(),
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
            while len(process_logs) == 0 and count < 180: ## wait up to 30 minutes
                time.sleep(10)
                process_logs = self.client.get_process_logs(id=invitation.id + '-0-1', min_sdate = invitation.tmdate + self.update_wait_time - 1000)
                count += 1

            if len(process_logs) == 0:
                raise openreview.OpenReviewException('Time out waiting for invitation to complete: ' + invitation.id)
                
            if process_logs[0]['status'] == 'error':
                raise openreview.OpenReviewException('Error saving invitation: ' + invitation.id)
            
        return invitation

    def expire_invitation(self, invitation_id):
        invitation = tools.get_invitation(self.client, id = invitation_id)

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

    def set_edit_deadlines_invitation(self, invitation_id, process_file):

        venue_id = self.venue_id
        venue = self.venue
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
                                'type': 'integer',
                                'range': [ 0, 9999999999999 ],
                                'optional': True,
                                'deletable': True
                            }
                        }
                    },
                    'deadline': { 
                        'value': {
                            'param': {
                                'type': 'integer',
                                'range': [ 0, 9999999999999 ],
                                'optional': True,
                                'deletable': True
                            }
                        }
                    },
                    'expiration_date': { 
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
                'signatures': [venue.get_program_chairs_id()],
                'readers': [venue_id],
                'writers': [venue_id],
                'invitation': {
                    'id': invitation_id,
                    'signatures': [venue_id],
                    'cdate': '${2/content/activation_date/value}',
                    'duedate': '${2/content/deadline/value}',
                    'expdate': '${2/content/expiration_date/value}'
                }
            },
            process=self.get_process_content(f'process/{process_file}')  
        )

        self.save_invitation(invitation, replacement=True)
        return invitation

    def set_edit_content_invitation(self, invitation_id):

        venue_id = self.venue_id
        venue = self.venue
        content_invitation_id = invitation_id + '/Submission_Form'

        invitation = Invitation(
            id = content_invitation_id,
            invitees = [venue_id],
            signatures = [venue_id],
            readers = [venue_id],
            writers = [venue_id],
            edit = {
                'signatures': [venue_id],
                'readers': [venue_id],
                'writers': [venue_id],
                'content' :{
                    'note_content': {
                        'value': {
                            'param': {
                                'type': 'content'
                            }
                        }
                    },
                    'note_license': {
                        'value': {
                            'param': {
                                'type': 'string[]',
                                'items':  [
                                    {'value': 'CC BY 4.0', 'optional': True, 'description': 'A'},
                                    {'value': 'CC BY-SA 4.0', 'optional': True, 'description': 'A'},
                                    {'value': 'CC BY-NC 4.0', 'optional': True, 'description': 'A'},
                                    {'value': 'CC BY-ND 4.0', 'optional': True, 'description': 'A'},
                                    {'value': 'CC BY-NC-SA 4.0', 'optional': True, 'description': 'A'},
                                    {'value': 'CC BY-NC-ND 4.0', 'optional': True, 'description': 'A'},
                                    {'value': 'CC0 1.0', 'optional': True, 'description': 'A'}
                                ]
                            }
                        }
                    }
                },
                'invitation': {
                    'id': invitation_id,
                    'signatures': [venue_id],
                    'edit': {
                        'signatures': [venue.get_program_chairs_id()],
                        'note': {
                            'signatures': ['${3/signatures}'],
                            'content': '${4/content/note_content/value}',
                            'license': {
                                'param': {
                                    'enum': ['${7/content/note_license/value}']
                                }
                            }
                        }
                    }
                }
            }  
        )

        self.save_invitation(invitation, replacement=False)
        return invitation