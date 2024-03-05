import csv
import datetime
import json
import os
import time
import re
from openreview.api import Invitation
from openreview.api import Note
from openreview.stages import *
from openreview.stages.arr_content import hide_fields_from_public
from .. import tools

SHORT_BUFFER_MIN = 30
LONG_BUFFER_DAYS = 10

class InvitationBuilder(object):

    def __init__(self, venue, update_wait_time=5000):
        self.client = venue.client
        self.venue = venue
        self.venue_id = venue.venue_id
        self.update_wait_time = update_wait_time
        self.update_date_string = "#{4/mdate} + " + str(self.update_wait_time)
        self.invitation_edit_process = '''def process(client, invitation):
    meta_invitation = client.get_invitation("''' + self.venue.get_meta_invitation_id() + '''")
    script = meta_invitation.content["invitation_edit_script"]['value']
    funcs = {
        'openreview': openreview,
        'datetime': datetime,
        'date_index': date_index
    }
    exec(script, funcs)
    funcs['process'](client, invitation)
'''

        self.group_edit_process = '''def process(client, invitation):
    meta_invitation = client.get_invitation("''' + self.venue.get_meta_invitation_id() + '''")
    script = meta_invitation.content["group_edit_script"]['value']
    funcs = {
        'openreview': openreview,
        'datetime': datetime,
        'date_index': date_index
    }
    exec(script, funcs)
    funcs['process'](client, invitation)
'''

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
        
    def set_arr_configuration_invitation(self):
        # Must be run by super user
        client_v1 = openreview.Client(
            baseurl=openreview.tools.get_base_urls(self.client)[0],
            token=self.client.token
        )

        venue_id = self.venue_id
        request_form_id = self.venue.request_form_id
        request_form = client_v1.get_note(request_form_id)
        support_group = request_form.invitation.split('/-/')[0]

        client_v1.post_invitation(openreview.Invitation(
            id=f"{support_group}/-/Request{request_form.number}/ARR_Configuration",
            readers=[venue_id],
            writers=[support_group],
            signatures=['~Super_User1'],
            invitees=[venue_id],
            multiReply=True,
            process_string=self.get_process_content('process/configuration_process.py'),
            reply={
                'forum':request_form_id,
                'referent': request_form_id,
                'readers': {
                    'description': 'The users who will be allowed to read the above content.',
                    'values' : [
                        support_group,
                        self.venue.get_program_chairs_id()
                    ]
                },
                'writers': {
                    'values':[],
                },
                'signatures': {
                    'values-regex': '~.*'
                },
                'content': {
                    'previous_cycle': {
                        'description': 'What is the previous cycle? This will be used to fetch data and copy it into the current venue.',
                        'value-regex': '.*',
                        'order': 10,
                        'required': False
                    },
                    'setup_venue_stages_date': {
                        'description': 'When should the venue request process functions be overridden? Please enter a time and date in GMT using the following format: YYYY/MM/DD HH:MM:SS (e.g. 2019/01/31 23:59:59)',
                        'value-regex': r'^[0-9]{4}\/([1-9]|0[1-9]|1[0-2])\/([1-9]|0[1-9]|[1-2][0-9]|3[0-1])(\s+)?((2[0-3]|[01][0-9]|[0-9]):[0-5][0-9](:[0-5][0-9])?)?(\s+)?$',
                        'order': 11,
                        'required': False
                    },
                    'setup_shared_data_date': {
                        'description': 'When should the data be copied over? Please enter a time and date in GMT using the following format: YYYY/MM/DD HH:MM:SS (e.g. 2019/01/31 23:59:59)',
                        'value-regex': r'^[0-9]{4}\/([1-9]|0[1-9]|1[0-2])\/([1-9]|0[1-9]|[1-2][0-9]|3[0-1])(\s+)?((2[0-3]|[01][0-9]|[0-9]):[0-5][0-9](:[0-5][0-9])?)?(\s+)?$',
                        'order': 12,
                        'required': False
                    },
                    'preprint_release_submission_date': {
                        'description': 'When should submissions be copied over and the opt-in papers be revealed to the public? Please enter a time and date in GMT using the following format: YYYY/MM/DD HH:MM:SS (e.g. 2019/01/31 23:59:59)',
                        'value-regex': r'^[0-9]{4}\/([1-9]|0[1-9]|1[0-2])\/([1-9]|0[1-9]|[1-2][0-9]|3[0-1])(\s+)?((2[0-3]|[01][0-9]|[0-9]):[0-5][0-9](:[0-5][0-9])?)?(\s+)?$',
                        'order': 13,
                        'required': False
                    }
                }
            }
        ))
        
    def set_arr_scheduler_invitation(self):
        venue_id = self.venue_id

        scheduler_id = f'{venue_id}/-/ARR_Scheduler'
        scheduler_cdate= tools.datetime_millis(datetime.datetime.utcnow())

        scheduler_inv = Invitation(
            id=scheduler_id,
            invitees=[venue_id],
            readers=[venue_id],
            writers=[venue_id],
            signatures=['~Super_User1'],
            cdate=scheduler_cdate,
            content={
                'setup_venue_stages_date': {'value': 0},
                'setup_shared_data_date': {'value': 0},
                'preprint_release_submission_date': {'value': 0},
            },
            date_processes=[
                {
                    'dates': ["#{4/content/setup_venue_stages_date/value}"],
                    'script': self.get_process_content('management/setup_venue_stages.py'),
                },
                {
                    'dates': ["#{4/content/setup_shared_data_date/value}"],
                    'script': self.get_process_content('management/setup_shared_data.py'),
                },
                {
                    'dates': ["#{4/content/preprint_release_submission_date/value}"],
                    'script': self.get_process_content('management/setup_preprint_release.py'),
                }
            ]
        )

        self.save_invitation(scheduler_inv, replacement=False) 

    def set_preprint_release_submission_invitation(self):
        venue_id = self.venue_id
        submission_stage = self.venue.submission_stage
        submission_name = submission_stage.name

        submission_id = submission_stage.get_submission_id(self.venue)
        post_submission_id = f'{venue_id}/-/Preprint_Release_{submission_name}'
        post_submission_cdate = tools.datetime_millis(submission_stage.exp_date + datetime.timedelta(minutes=30)) if submission_stage.exp_date else None

        hidden_field_names = hide_fields_from_public
        committee_members = self.venue.get_committee(number='${{4/id}/number}', with_authors=True)
        note_content = { f: { 'readers': committee_members } for f in hidden_field_names }

        submission_invitation = Invitation(
            id=post_submission_id,
            invitees = [venue_id],
            signatures = [venue_id],
            readers = ['everyone'],
            writers = [venue_id],
            cdate=post_submission_cdate,
            date_processes=[{ 
                'dates': ["#{4/cdate}", self.update_date_string],
                'script': self.get_process_content('process/preprint_release_submission_process.py')              
            }],            
            edit = {
                'signatures': [venue_id],
                'readers': [venue_id, self.venue.get_authors_id('${{2/note/id}/number}')],
                'writers': [venue_id],
                'note': {
                    'id': {
                        'param': {
                            'withInvitation': submission_id,
                            'optional': True
                        }
                    },
                    'odate': {
                        'param': {
                            'range': [ 0, 9999999999999 ],
                            'optional': True,
                            'deletable': True
                        }
                    },
                    'signatures': [ self.venue.get_authors_id('${{2/id}/number}') ],
                    'readers': ['everyone'],
                    'writers': [venue_id, self.venue.get_authors_id('${{2/id}/number}')],
                }
            }
        )

        note_content['_bibtex'] = {
            'value': {
                'param': {
                    'type': 'string',
                    'maxLength': 200000,
                    'input': 'textarea',
                    'optional': True
                }
            }
        }

        if note_content:
            submission_invitation.edit['note']['content'] = note_content

        submission_invitation = self.save_invitation(submission_invitation, replacement=False)

    def set_setup_shared_data_invitation(self):
        venue_id = self.venue_id

        share_data_id = f'{venue_id}/-/Setup_Shared_Data'
        share_data_cdate= tools.datetime_millis(datetime.datetime.utcnow())

        share_data_inv = Invitation(
            id=share_data_id,
            invitees=[venue_id],
            readers=[venue_id],
            writers=[venue_id],
            signatures=['~Super_User1'],
            cdate=share_data_cdate,
            process=self.get_process_content('management/setup_shared_data.py'),
            edit={
                'signatures': [venue_id],
                'readers': [venue_id],
                'writers': [venue_id],
                'note': {
                    'ddate': {
                        'param': {
                            'range': [ 0, 9999999999999 ],
                            'optional': True,
                            'deletable': True
                        }
                    },
                    'signatures': [venue_id],
                    'readers': [venue_id],
                    'writers': [venue_id],
                    'content': {
                        'previous_cycle': {
                            'value': {
                                'param': {
                                    'regex': '.*', 'type': 'string',
                                }
                            }
                        }
                    }
                }
            }
        )

        self.save_invitation(share_data_inv, replacement=False)

    def set_setup_venue_stages_invitation(self):
        venue_id = self.venue_id

        override_id = f'{venue_id}/-/Setup_Venue_Stages'
        override_cdate= tools.datetime_millis(datetime.datetime.utcnow())

        override_inv = Invitation(
            id=override_id,
            invitees=[venue_id],
            readers=[venue_id],
            writers=[venue_id],
            signatures=['~Super_User1'],
            cdate=override_cdate,
            process=self.get_process_content('management/setup_venue_stages.py')
        )

        self.save_invitation(override_inv, replacement=False) 