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

    def set_edit_submission_deadlines_invitation(self, process_file=None):

        venue_id = self.venue_id
        submission_id = self.get_content_value('submission_id', f'{venue_id}/-/Submission')
        deadline_invitation_id = submission_id + '/Deadlines'

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
                    'id': submission_id,
                    'signatures': [venue_id],
                    'cdate': '${2/content/activation_date/value}',
                    'duedate': '${2/content/deadline/value}',
                    'expdate': '${2/content/deadline/value}+1800000' ## 30 minutes buffer period
                }
            }
        )

        if process_file:
            invitation.process = self.get_process_content(process_file)

        self.save_invitation(invitation, replacement=True)
        return invitation

    def set_edit_submission_content_invitation(self):

        venue_id = self.venue_id
        submission_id = self.get_content_value('submission_id', f'{venue_id}/-/Submission')
        content_invitation_id = submission_id + '/Form_Fields'

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
                                'type': 'object[]',
                                'input': 'select',
                                'items':  [
                                    {'value': {'value': 'CC BY 4.0', 'optional': True, 'description': 'CC BY 4.0'}, 'optional': True, 'description': 'CC BY 4.0'},
                                    {'value': {'value': 'CC BY-SA 4.0', 'optional': True, 'description': 'CC BY-SA 4.0'}, 'optional': True, 'description': 'CC BY-SA 4.0'},
                                    {'value': {'value': 'CC BY-NC 4.0', 'optional': True, 'description': 'CC BY-NC 4.0'}, 'optional': True, 'description': 'CC BY-NC 4.0'},
                                    {'value': {'value': 'CC BY-ND 4.0', 'optional': True, 'description': 'CC BY-ND 4.0'}, 'optional': True, 'description': 'CC BY-ND 4.0'},
                                    {'value': {'value': 'CC BY-NC-SA 4.0', 'optional': True, 'description': 'CC BY-NC-SA 4.0'}, 'optional': True, 'description': 'CC BY-NC-SA 4.0'},
                                    {'value': {'value': 'CC BY-NC-ND 4.0', 'optional': True, 'description': 'CC BY-NC-ND 4.0'}, 'optional': True, 'description': 'CC BY-NC-ND 4.0'},
                                    {'value': {'value': 'CC0 1.0', 'optional': True, 'description': 'CC0 1.0'}, 'optional': True, 'description': 'CC0 1.0'}
                                ]
                            }
                        }
                    }
                },
                'invitation': {
                    'id': submission_id,
                    'signatures': [venue_id],
                    'edit': {
                        'note': {
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

    def set_edit_submission_notification_invitation(self):

        venue_id = self.venue_id
        submission_id = self.get_content_value('submission_id', f'{venue_id}/-/Submission')
        notifications_invitation_id = submission_id + '/Notifications'

        invitation = Invitation(
            id = notifications_invitation_id,
            invitees = [venue_id],
            signatures = [venue_id],
            readers = [venue_id],
            writers = [venue_id],
            edit = {
                'signatures': [venue_id],
                'readers': [venue_id],
                'writers': [venue_id],
                'content' :{
                    'email_authors': {
                        'value': {
                            'param': {
                                'type': 'boolean',
                                'enum': [True, False],
                                'input': 'radio'
                            }
                        }
                    },
                    'email_pcs': {
                        'value': {
                            'param': {
                                'type': 'boolean',
                                'enum': [True, False],
                                'input': 'radio'
                            }
                        }
                    }
                },
                'invitation': {
                    'id': submission_id,
                    'signatures': [venue_id],
                    'content': {
                        'email_authors': {
                            'value': '${4/content/email_authors/value}'
                        },
                        'email_pcs': {
                            'value': '${4/content/email_pcs/value}'
                        }
                    }
                }
            }
        )

        self.save_invitation(invitation, replacement=False)
        return invitation

    def set_edit_submission_readers_invitation(self):

        venue_id = self.venue_id
        submission_name = self.domain_group.get_content_value('submission_name', 'Submission')
        readers_invitation_id = f'{venue_id}/-/Post_{submission_name}/Submission_Readers'
        authors_name = self.domain_group.get_content_value('authors_name', 'Authors')
        reviewers_name = self.domain_group.get_content_value('reviewers_name', 'Reviewers')

        readers_items = [
            {'value': venue_id, 'optional': False, 'description': 'Program Chairs'},
        ]

        senior_area_chairs_name = self.domain_group.get_content_value('senior_area_chairs_name')
        if senior_area_chairs_name:
            readers_items.extend([
                {'value': self.domain_group.get_content_value('senior_area_chairs_id'), 'optional': True, 'description': 'All Senior Area Chairs'},
                {'value': f'{venue_id}/{submission_name}' + '${{2/id}/number}' +f'/{senior_area_chairs_name}', 'optional': True, 'description': 'Assigned Senior Area Chairs'}
                ])

        area_chairs_name = self.domain_group.get_content_value('area_chairs_name')
        if area_chairs_name:
            readers_items.extend([
                {'value': self.domain_group.get_content_value('senior_area_chairs_id'), 'optional': True, 'description': 'All Area Chairs'},
                {'value': f'{venue_id}/{submission_name}' + '${{2/id}/number}' +f'/{area_chairs_name}', 'optional': True, 'description': 'Assigned Area Chairs'}
                ])

        readers_items.extend([
                {'value': self.domain_group.get_content_value('reviewers_id'), 'optional': True, 'description': 'All Reviewers'},
                {'value': f'{venue_id}/{submission_name}' + '${{2/id}/number}' +f'/{reviewers_name}', 'optional': True, 'description': 'Assigned Reviewers'},
                {'value': f'{venue_id}/{submission_name}' + '${{2/id}/number}' +f'/{authors_name}', 'optional': True, 'description': 'Paper Authors'},
                ])

        invitation = Invitation(
            id = readers_invitation_id,
            invitees = [venue_id],
            signatures = [venue_id],
            readers = [venue_id],
            writers = [venue_id],
            edit = {
                'signatures': [venue_id],
                'readers': [venue_id],
                'writers': [venue_id],
                'content' :{
                    'readers': {
                        'value': {
                            'param': {
                                'type': 'string[]',
                                'input': 'select',
                                'items':  readers_items
                            }
                        }
                    }
                },
                'invitation': {
                    'id': f'{venue_id}/-/Post_{submission_name}',
                    'signatures': [venue_id],
                    'edit': {
                        'note': {
                            'readers': ['${5/content/readers/value}']
                        }
                    }
                }
            }
        )

        self.save_invitation(invitation, replacement=False)
        return invitation