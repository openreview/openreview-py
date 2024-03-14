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
    REGISTRATION_NAME = 'Registration'
    MAX_LOAD_AND_UNAVAILABILITY_NAME = 'Max_Load_And_Unavailability_Request'

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

    # Modified ethics review flag invitation
    def set_verification_flag_invitation(self):
        venue_id = self.venue_id
        flag_invitation_id = f'{venue_id}/-/Desk_Reject_Verification_Flag'
        submission_id = self.venue.submission_stage.get_submission_id(self.venue)

        flag_readers = [venue_id]
        if self.venue.use_senior_area_chairs:
            flag_readers.append(self.venue.get_senior_area_chairs_id('${{4/id}/number}'))
        
        flag_invitation = Invitation(
            id=flag_invitation_id,
            invitees = [venue_id],
            signatures = [venue_id],
            readers = ['everyone'],
            writers = [venue_id],
            edit = {
                'signatures': [venue_id],
                'readers': [venue_id],
                'writers': [venue_id],
                'note': {
                    'id': {
                        'param': {
                            'withInvitation': submission_id,
                            'optional': True
                        }
                    },
                    'signatures': [ self.venue.get_authors_id('${{2/id}/number}') ],
                    'writers': [venue_id, self.venue.get_authors_id('${{2/id}/number}')],
                    'content': {
                        'flagged_for_desk_reject_verification': {
                            'value': {
                                'param': {
                                    'type': 'boolean',
                                    'enum': [True, False],
                                    'input': 'radio'
                                }
                            },
                            'readers': flag_readers
                        }
                    }
                }
            },
            process=self.get_process_content('process/verification_process.py')
        )

        self.save_invitation(flag_invitation, replacement=False)
        return flag_invitation

    # Non-blocking custom stage with process/pre-process arguments
    def set_custom_stage_invitation(self, process_script = None, preprocess_script = None):

        venue_id = self.venue_id
        custom_stage = self.venue.custom_stage
        custom_stage_invitation_id = self.venue.get_invitation_id(custom_stage.name)
        custom_stage_cdate = tools.datetime_millis(custom_stage.start_date if custom_stage.start_date else datetime.datetime.utcnow())
        custom_stage_duedate = tools.datetime_millis(custom_stage.due_date) if custom_stage.due_date else None
        custom_stage_expdate = tools.datetime_millis(custom_stage.exp_date) if custom_stage.exp_date else None
        if not custom_stage_expdate:
            custom_stage_expdate = tools.datetime_millis(custom_stage.due_date + datetime.timedelta(minutes = SHORT_BUFFER_MIN)) if custom_stage.due_date else None

        content = custom_stage.get_content(api_version='2', conference=self.venue)

        custom_stage_replyto = custom_stage.get_reply_to()
        custom_stage_source = custom_stage.get_source_submissions()
        custom_stage_reply_type = custom_stage.get_reply_type()
        note_writers = None

        if custom_stage_reply_type == 'reply':
            paper_invitation_id = self.venue.get_invitation_id(name=custom_stage.name, number='${2/content/noteNumber/value}')
            with_invitation = self.venue.get_invitation_id(name=custom_stage.name, number='${6/content/noteNumber/value}')
            note_id = {
                'param': {
                    'withInvitation': with_invitation,
                    'optional': True
                }
            }
            edit_readers = ['${2/note/readers}']
            note_readers = custom_stage.get_readers(self.venue, '${5/content/noteNumber/value}')
            note_nonreaders = custom_stage.get_nonreaders(self.venue, number='${5/content/noteNumber/value}')
            note_writers = [venue_id, '${3/signatures}']
            invitees = custom_stage.get_invitees(self.venue, number='${3/content/noteNumber/value}')
            noninvitees = custom_stage.get_noninvitees(self.venue, number='${3/content/noteNumber/value}')
            if custom_stage_replyto == 'forum':
                reply_to = '${4/content/noteId/value}'
            elif custom_stage_replyto == 'withForum':
                reply_to = {
                    'param': {
                        'withForum': '${6/content/noteId/value}'
                    }
                }

        elif custom_stage_reply_type == 'revision':
            if custom_stage_reply_type in ['forum', 'withForum']:
                raise openreview.OpenReviewException('Custom stage cannot be used for revisions to submissions. Use the Submission Revision Stage instead.')

        if custom_stage_replyto in ['reviews', 'metareviews']:
            stage_name = self.venue.review_stage.name if custom_stage_replyto == 'reviews' else self.venue.meta_review_stage.name
            submission_prefix = venue_id + '/' + self.venue.submission_stage.name + '${2/content/noteNumber/value}/'
            reply_prefix = stage_name + '${2/content/replyNumber/value}'
            paper_invitation_id = self.venue.get_invitation_id(name=custom_stage.name, prefix=submission_prefix+reply_prefix)
            submission_prefix = venue_id + '/' + self.venue.submission_stage.name + '${6/content/noteNumber/value}/'
            reply_prefix = stage_name + '${6/content/replyNumber/value}'
            with_invitation = self.venue.get_invitation_id(name=custom_stage.name, prefix=submission_prefix+reply_prefix)
            note_id = {
                'param': {
                    'withInvitation': with_invitation,
                    'optional': True
                }
            }
            reply_to = '${4/content/replyto/value}'

            if custom_stage_reply_type == 'revision':
                note_id = '${4/content/replyto/value}'
                reply_to = None
                edit_readers = [venue_id, '${2/signatures}']
                note_readers = None
                invitees = ['${3/content/replytoSignatures/value}']
                noninvitees = []
                note_nonreaders = []

        invitation_content = {
            'source': { 'value': custom_stage_source },
            'reply_to': { 'value': custom_stage_replyto },
            'email_pcs': { 'value': custom_stage.email_pcs },
            'email_sacs': { 'value': custom_stage.email_sacs },
            'notify_readers': { 'value': custom_stage.notify_readers },
            'email_template': { 'value': custom_stage.email_template if custom_stage.email_template else '' }
        }
        if process_script:
            invitation_content['custom_stage_process_script'] = { 'value': self.get_process_content(process_script)}

        invitation = Invitation(id=custom_stage_invitation_id,
            invitees=[venue_id],
            readers=[venue_id],
            writers=[venue_id],
            signatures=[venue_id],
            cdate=custom_stage_cdate,
            date_processes=[{ 
                'dates': ["#{4/edit/invitation/cdate}", self.update_date_string],
                'script': self.invitation_edit_process              
            }],
            content = invitation_content,
            edit={
                'signatures': [venue_id],
                'readers': [venue_id],
                'writers': [venue_id],
                'content': {
                    'noteNumber': {
                        'value': {
                            'param': {
                                'regex': '.*', 'type': 'integer'
                            }
                        }
                    },
                    'noteId': {
                        'value': {
                            'param': {
                                'regex': '.*', 'type': 'string'
                            }
                        }
                    }
                },
                'replacement': True,
                'invitation': {
                    'id': paper_invitation_id,
                    'signatures': [venue_id],
                    'readers': ['everyone'],
                    'writers': [venue_id],
                    'minReplies': 1,
                    'invitees': invitees,
                    'noninvitees': noninvitees,
                    'cdate': custom_stage_cdate,
                    'edit': {
                        'signatures': { 
                            'param': { 
                                'items': [ { 'prefix': s, 'optional': True } if '.*' in s else { 'value': s, 'optional': True } for s in custom_stage.get_signatures(self.venue, '${7/content/noteNumber/value}')] 
                            }
                        },
                        'readers': edit_readers,
                        'nonreaders': ['${2/note/nonreaders}'] if note_nonreaders else [],
                        'writers': [venue_id, '${2/signatures}'],
                        'note': {
                            'id': note_id,
                            'forum': '${4/content/noteId/value}',
                            'ddate': {
                                'param': {
                                    'range': [ 0, 9999999999999 ],
                                    'optional': True,
                                    'deletable': True
                                }
                            },
                            'signatures': ['${3/signatures}'],
                            'content': content
                        }
                    }
                }
            }
        )

        if preprocess_script:
            invitation.edit['invitation']['preprocess'] = self.get_process_content(preprocess_script)

        if process_script:
            invitation.edit['invitation']['process'] = '''def process(client, edit, invitation):
    meta_invitation = client.get_invitation(invitation.invitations[0])
    script = meta_invitation.content['custom_stage_process_script']['value']
    funcs = {
        'openreview': openreview
    }
    exec(script, funcs)
    funcs['process'](client, edit, invitation)
'''

        if reply_to:
            invitation.edit['invitation']['edit']['note']['replyto'] = reply_to

        if custom_stage_replyto in ['reviews', 'metareviews']:
            invitation.edit['content']['replyNumber'] = {
                'value': {
                    'param': {
                        'regex': '.*', 'type': 'integer',
                        'optional': True
                    }
                }
            }
            invitation.edit['content']['replyto'] = {
                'value': {
                    'param': {
                        'regex': '.*', 'type': 'string',
                        'optional': True
                    }
                }
            }

        if custom_stage_reply_type == 'revision':
            invitation.edit['content']['replytoSignatures'] = {
                'value': {
                    'param': {
                        'regex': '.*', 'type': 'string',
                        'optional': True
                    }
                }
            }

        if note_readers:
            invitation.edit['invitation']['edit']['note']['readers'] = note_readers

        if note_nonreaders:
            invitation.edit['invitation']['edit']['note']['nonreaders'] = note_nonreaders

        if note_writers:
            invitation.edit['invitation']['edit']['note']['writers'] = note_writers

        if custom_stage_duedate:
            invitation.edit['invitation']['duedate'] = custom_stage_duedate
        if custom_stage_expdate:
            invitation.edit['invitation']['expdate'] = custom_stage_expdate
        if not custom_stage.multi_reply:
            invitation.edit['invitation']['maxReplies'] = 1

        self.client.post_invitation_edit(invitations=self.venue.get_meta_invitation_id(),
            readers=[self.venue_id],
            writers=[self.venue_id],
            signatures=[self.venue_id],
            replacement=False,
            invitation=invitation
        )

        return invitation

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
                    'form_expiration_date': {
                        'description': 'What should the default expiration date be? Please enter a time and date in GMT using the following format: YYYY/MM/DD HH:MM:SS (e.g. 2019/01/31 23:59:59)',
                        'value-regex': r'^[0-9]{4}\/([1-9]|0[1-9]|1[0-2])\/([1-9]|0[1-9]|[1-2][0-9]|3[0-1])(\s+)?((2[0-3]|[01][0-9]|[0-9]):[0-5][0-9](:[0-5][0-9])?)?(\s+)?$',
                        'order': 13,
                        'required': False
                    },
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
                    'maximum_load_due_date': {
                        'description': 'What should be the displayed deadline for the maximum load tasks? Please enter a time and date in GMT using the following format: YYYY/MM/DD HH:MM:SS (e.g. 2019/01/31 23:59:59)',
                        'value-regex': r'^[0-9]{4}\/([1-9]|0[1-9]|1[0-2])\/([1-9]|0[1-9]|[1-2][0-9]|3[0-1])(\s+)?((2[0-3]|[01][0-9]|[0-9]):[0-5][0-9](:[0-5][0-9])?)?(\s+)?$',
                        'order': 12,
                        'required': False
                    },
                    'maximum_load_exp_date': {
                        'description': 'When should we stop accepting any maximum load responses? Please enter a time and date in GMT using the following format: YYYY/MM/DD HH:MM:SS (e.g. 2019/01/31 23:59:59)',
                        'value-regex': r'^[0-9]{4}\/([1-9]|0[1-9]|1[0-2])\/([1-9]|0[1-9]|[1-2][0-9]|3[0-1])(\s+)?((2[0-3]|[01][0-9]|[0-9]):[0-5][0-9](:[0-5][0-9])?)?(\s+)?$',
                        'order': 13,
                        'required': False
                    },
                    'ae_checklist_due_date': {
                        'description': 'What should be the displayed deadline for the maximum load tasks? Please enter a time and date in GMT using the following format: YYYY/MM/DD HH:MM:SS (e.g. 2019/01/31 23:59:59)',
                        'value-regex': r'^[0-9]{4}\/([1-9]|0[1-9]|1[0-2])\/([1-9]|0[1-9]|[1-2][0-9]|3[0-1])(\s+)?((2[0-3]|[01][0-9]|[0-9]):[0-5][0-9](:[0-5][0-9])?)?(\s+)?$',
                        'order': 12,
                        'required': False
                    },
                    'ae_checklist_exp_date': {
                        'description': 'When should we stop accepting any maximum load responses? Please enter a time and date in GMT using the following format: YYYY/MM/DD HH:MM:SS (e.g. 2019/01/31 23:59:59)',
                        'value-regex': r'^[0-9]{4}\/([1-9]|0[1-9]|1[0-2])\/([1-9]|0[1-9]|[1-2][0-9]|3[0-1])(\s+)?((2[0-3]|[01][0-9]|[0-9]):[0-5][0-9](:[0-5][0-9])?)?(\s+)?$',
                        'order': 13,
                        'required': False
                    },
                    'reviewer_checklist_due_date': {
                        'description': 'What should be the displayed deadline for the maximum load tasks? Please enter a time and date in GMT using the following format: YYYY/MM/DD HH:MM:SS (e.g. 2019/01/31 23:59:59)',
                        'value-regex': r'^[0-9]{4}\/([1-9]|0[1-9]|1[0-2])\/([1-9]|0[1-9]|[1-2][0-9]|3[0-1])(\s+)?((2[0-3]|[01][0-9]|[0-9]):[0-5][0-9](:[0-5][0-9])?)?(\s+)?$',
                        'order': 12,
                        'required': False
                    },
                    'reviewer_checklist_exp_date': {
                        'description': 'When should we stop accepting any maximum load responses? Please enter a time and date in GMT using the following format: YYYY/MM/DD HH:MM:SS (e.g. 2019/01/31 23:59:59)',
                        'value-regex': r'^[0-9]{4}\/([1-9]|0[1-9]|1[0-2])\/([1-9]|0[1-9]|[1-2][0-9]|3[0-1])(\s+)?((2[0-3]|[01][0-9]|[0-9]):[0-5][0-9](:[0-5][0-9])?)?(\s+)?$',
                        'order': 13,
                        'required': False
                    },
                    'setup_shared_data_date': {
                        'description': 'When should the data be copied over? Please enter a time and date in GMT using the following format: YYYY/MM/DD HH:MM:SS (e.g. 2019/01/31 23:59:59)',
                        'value-regex': r'^[0-9]{4}\/([1-9]|0[1-9]|1[0-2])\/([1-9]|0[1-9]|[1-2][0-9]|3[0-1])(\s+)?((2[0-3]|[01][0-9]|[0-9]):[0-5][0-9](:[0-5][0-9])?)?(\s+)?$',
                        'order': 14,
                        'required': False
                    },
                    'preprint_release_submission_date': {
                        'description': 'When should submissions be copied over and the opt-in papers be revealed to the public? Please enter a time and date in GMT using the following format: YYYY/MM/DD HH:MM:SS (e.g. 2019/01/31 23:59:59)',
                        'value-regex': r'^[0-9]{4}\/([1-9]|0[1-9]|1[0-2])\/([1-9]|0[1-9]|[1-2][0-9]|3[0-1])(\s+)?((2[0-3]|[01][0-9]|[0-9]):[0-5][0-9](:[0-5][0-9])?)?(\s+)?$',
                        'order': 15,
                        'required': False
                    },
                    'setup_sae_matching_date': {
                        'description': 'When should conflicts be computed and the matching data for SAEs be set up? Please enter a time and date in GMT using the following format: YYYY/MM/DD HH:MM:SS (e.g. 2019/01/31 23:59:59)',
                        'value-regex': r'^[0-9]{4}\/([1-9]|0[1-9]|1[0-2])\/([1-9]|0[1-9]|[1-2][0-9]|3[0-1])(\s+)?((2[0-3]|[01][0-9]|[0-9]):[0-5][0-9](:[0-5][0-9])?)?(\s+)?$',
                        'order': 16,
                        'required': False
                    },
                    'sae_affinity_scores': {
                        'description': 'Upload a CSV file containing affinity scores for SAC-paper pairs (one SAC-paper pair per line in the format: submission_id, SAC_id, affinity_score)',
                        'order': 17,
                        'value-file': {
                            'fileTypes': ['csv'],
                            'size': 50
                        },
                        'required': False
                    },
                    'setup_tracks_and_reassignment_date': {
                        'description': 'When will submission track and reassignment data be finalized? This will modify the affinity scores and indicate which reviewers and action editors have matching tracks. Please enter a time and date in GMT using the following format: YYYY/MM/DD HH:MM:SS (e.g. 2019/01/31 23:59:59)',
                        'value-regex': r'^[0-9]{4}\/([1-9]|0[1-9]|1[0-2])\/([1-9]|0[1-9]|[1-2][0-9]|3[0-1])(\s+)?((2[0-3]|[01][0-9]|[0-9]):[0-5][0-9](:[0-5][0-9])?)?(\s+)?$',
                        'order': 18,
                        'required': False
                    },
                    'setup_sae_ae_assignment_date': {
                        'description': 'When will both SAE and AE assignments be deployed? This must happen after both assignments are deployed to give SAEs access to the AE assignments. Please enter a time and date in GMT using the following format: YYYY/MM/DD HH:MM:SS (e.g. 2019/01/31 23:59:59)',
                        'value-regex': r'^[0-9]{4}\/([1-9]|0[1-9]|1[0-2])\/([1-9]|0[1-9]|[1-2][0-9]|3[0-1])(\s+)?((2[0-3]|[01][0-9]|[0-9]):[0-5][0-9](:[0-5][0-9])?)?(\s+)?$',
                        'order': 19,
                        'required': False
                    },
                    'reviewing_start_date': {
                        'description': 'When should reviewing start? Please enter a time and date in GMT using the following format: YYYY/MM/DD HH:MM:SS (e.g. 2019/01/31 23:59:59)',
                        'value-regex': r'^[0-9]{4}\/([1-9]|0[1-9]|1[0-2])\/([1-9]|0[1-9]|[1-2][0-9]|3[0-1])(\s+)?((2[0-3]|[01][0-9]|[0-9]):[0-5][0-9](:[0-5][0-9])?)?(\s+)?$',
                        'order': 20,
                        'required': False
                    },
                    'reviewing_due_date': {
                        'description': 'When should reviewing end? Please enter a time and date in GMT using the following format: YYYY/MM/DD HH:MM:SS (e.g. 2019/01/31 23:59:59)',
                        'value-regex': r'^[0-9]{4}\/([1-9]|0[1-9]|1[0-2])\/([1-9]|0[1-9]|[1-2][0-9]|3[0-1])(\s+)?((2[0-3]|[01][0-9]|[0-9]):[0-5][0-9](:[0-5][0-9])?)?(\s+)?$',
                        'order': 21,
                        'required': False
                    },
                    'reviewing_exp_date': {
                        'description': 'When should the reviewing forms be disabled? Please enter a time and date in GMT using the following format: YYYY/MM/DD HH:MM:SS (e.g. 2019/01/31 23:59:59)',
                        'value-regex': r'^[0-9]{4}\/([1-9]|0[1-9]|1[0-2])\/([1-9]|0[1-9]|[1-2][0-9]|3[0-1])(\s+)?((2[0-3]|[01][0-9]|[0-9]):[0-5][0-9](:[0-5][0-9])?)?(\s+)?$',
                        'order': 22,
                        'required': False
                    },
                    'metareviewing_start_date': {
                        'description': 'When should metareviewing start? Please enter a time and date in GMT using the following format: YYYY/MM/DD HH:MM:SS (e.g. 2019/01/31 23:59:59)',
                        'value-regex': r'^[0-9]{4}\/([1-9]|0[1-9]|1[0-2])\/([1-9]|0[1-9]|[1-2][0-9]|3[0-1])(\s+)?((2[0-3]|[01][0-9]|[0-9]):[0-5][0-9](:[0-5][0-9])?)?(\s+)?$',
                        'order': 23,
                        'required': False
                    },
                    'metareviewing_due_date': {
                        'description': 'When should metareviewing end? Please enter a time and date in GMT using the following format: YYYY/MM/DD HH:MM:SS (e.g. 2019/01/31 23:59:59)',
                        'value-regex': r'^[0-9]{4}\/([1-9]|0[1-9]|1[0-2])\/([1-9]|0[1-9]|[1-2][0-9]|3[0-1])(\s+)?((2[0-3]|[01][0-9]|[0-9]):[0-5][0-9](:[0-5][0-9])?)?(\s+)?$',
                        'order': 24,
                        'required': False
                    },
                    'metareviewing_exp_date': {
                        'description': 'When should the metareviewing forms be disabled? Please enter a time and date in GMT using the following format: YYYY/MM/DD HH:MM:SS (e.g. 2019/01/31 23:59:59)',
                        'value-regex': r'^[0-9]{4}\/([1-9]|0[1-9]|1[0-2])\/([1-9]|0[1-9]|[1-2][0-9]|3[0-1])(\s+)?((2[0-3]|[01][0-9]|[0-9]):[0-5][0-9](:[0-5][0-9])?)?(\s+)?$',
                        'order': 25,
                        'required': False
                    },
                    'ethics_reviewing_start_date': {
                        'description': 'When should ethics reviewing start? Please enter a time and date in GMT using the following format: YYYY/MM/DD HH:MM:SS (e.g. 2019/01/31 23:59:59)',
                        'value-regex': r'^[0-9]{4}\/([1-9]|0[1-9]|1[0-2])\/([1-9]|0[1-9]|[1-2][0-9]|3[0-1])(\s+)?((2[0-3]|[01][0-9]|[0-9]):[0-5][0-9](:[0-5][0-9])?)?(\s+)?$',
                        'order': 26,
                        'required': False
                    },
                    'ethics_reviewing_due_date': {
                        'description': 'When should ethics reviewing end? Please enter a time and date in GMT using the following format: YYYY/MM/DD HH:MM:SS (e.g. 2019/01/31 23:59:59)',
                        'value-regex': r'^[0-9]{4}\/([1-9]|0[1-9]|1[0-2])\/([1-9]|0[1-9]|[1-2][0-9]|3[0-1])(\s+)?((2[0-3]|[01][0-9]|[0-9]):[0-5][0-9](:[0-5][0-9])?)?(\s+)?$',
                        'order': 27,
                        'required': False
                    },
                    'ethics_reviewing_exp_date': {
                        'description': 'When should the ethics reviewing forms be disabled? Please enter a time and date in GMT using the following format: YYYY/MM/DD HH:MM:SS (e.g. 2019/01/31 23:59:59)',
                        'value-regex': r'^[0-9]{4}\/([1-9]|0[1-9]|1[0-2])\/([1-9]|0[1-9]|[1-2][0-9]|3[0-1])(\s+)?((2[0-3]|[01][0-9]|[0-9]):[0-5][0-9](:[0-5][0-9])?)?(\s+)?$',
                        'order': 28,
                        'required': False
                    },
                    'setup_review_stages_date': {
                        'description': 'When should the review stages be created? This date should be after the submission deadline. Please enter a time and date in GMT using the following format: YYYY/MM/DD HH:MM:SS (e.g. 2019/01/31 23:59:59)',
                        'value-regex': r'^[0-9]{4}\/([1-9]|0[1-9]|1[0-2])\/([1-9]|0[1-9]|[1-2][0-9]|3[0-1])(\s+)?((2[0-3]|[01][0-9]|[0-9]):[0-5][0-9](:[0-5][0-9])?)?(\s+)?$',
                        'order': 29,
                        'required': False
                    },
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
                'form_expiration_date': {'value': 0},
                'setup_venue_stages_date': {'value': 0},
                'setup_shared_data_date': {'value': 0},
                'preprint_release_submission_date': {'value': 0},
                'setup_sae_matching_date': {'value': 0},
                'maximum_load_due_date': {'value': 0},
                'maximum_load_exp_date': {'value': 0},
                'ae_checklist_due_date': {'value': 0},
                'ae_checklist_exp_date': {'value': 0},
                'reviewer_checklist_due_date': {'value': 0},
                'reviewer_checklist_exp_date': {'value': 0},
                'setup_tracks_and_reassignment_date': {'value': 0},
                'setup_sae_ae_assignment_date': {'value': 0},
                'reviewing_start_date': {'value': 0},
                'reviewing_due_date': {'value': 0},
                'reviewing_exp_date': {'value': 0},
                'metareviewing_start_date': {'value': 0},
                'metareviewing_due_date': {'value': 0},
                'metareviewing_exp_date': {'value': 0},
                'ethics_reviewing_start_date': {'value': 0},
                'ethics_reviewing_due_date': {'value': 0},
                'ethics_reviewing_exp_date': {'value': 0},
                'setup_review_stages_date': {'value': 0}
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
                },
                {
                    'dates': ["#{4/content/setup_sae_matching_date/value}"],
                    'script': self.get_process_content('management/setup_matching.py'),
                },
                {
                    'dates': ["#{4/content/setup_tracks_and_reassignment_date/value}"],
                    'script': self.get_process_content('management/setup_reassignment_data.py'),
                },
                {
                    'dates': ["#{4/content/setup_sae_ae_assignment_date/value}"],
                    'script': self.get_process_content('management/setup_sae_ae_assignments.py'),
                },
                {
                    'dates': ["#{4/content/setup_review_stages_date/value}"],
                    'script': self.get_process_content('management/setup_review_stages.py'),
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