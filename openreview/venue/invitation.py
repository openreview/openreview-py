import csv
import datetime
import json
import os
import time
import re
from openreview.api import Invitation
from openreview.api import Note
from openreview.stages import *
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

    def set_meta_invitation(self):
        venue_id=self.venue_id
        meta_invitation = openreview.tools.get_invitation(self.client, self.venue.get_meta_invitation_id())
        
        if meta_invitation is None or 'invitation_edit_script' not in meta_invitation.content or 'group_edit_script' not in meta_invitation.content:
            self.client.post_invitation_edit(invitations=None,
                readers=[venue_id],
                writers=[venue_id],
                signatures=['~Super_User1'],
                invitation=Invitation(id=self.venue.get_meta_invitation_id(),
                    invitees=[venue_id],
                    readers=[venue_id],
                    signatures=['~Super_User1'],
                    content={
                        'invitation_edit_script': {
                            'value': self.get_process_content('process/invitation_edit_process.py')
                        },
                        'group_edit_script': {
                            'value': self.get_process_content('process/group_edit_process.py')
                        }                        
                    },
                    edit=True
                )
            )
       
    def set_submission_invitation(self):
        venue_id = self.venue_id
        submission_stage = self.venue.submission_stage

        content = submission_stage.get_content(api_version='2', conference=self.venue, venue_id=self.venue.get_submission_venue_id())

        edit_readers = ['everyone'] if submission_stage.create_groups else [venue_id, '${2/note/content/authorids/value}']
        note_readers = ['everyone'] if submission_stage.create_groups else [venue_id, '${2/content/authorids/value}']

        submission_id = submission_stage.get_submission_id(self.venue)
        submission_cdate = tools.datetime_millis(submission_stage.start_date if submission_stage.start_date else datetime.datetime.utcnow())

        submission_invitation = Invitation(
            id=submission_id,
            invitees = ['~'],
            signatures = [venue_id],
            readers = ['everyone'],
            writers = [venue_id],
            cdate=submission_cdate,
            duedate=tools.datetime_millis(submission_stage.due_date) if submission_stage.due_date else None,
            expdate = tools.datetime_millis(submission_stage.exp_date) if submission_stage.exp_date else None,
            edit = {
                'signatures': { 'param': { 'regex': f'~.*|{self.venue.get_program_chairs_id()}' } },
                'readers': edit_readers,
                'writers': [venue_id, '${2/note/content/authorids/value}'],
                'ddate': {
                    'param': {
                        'range': [ 0, 9999999999999 ],
                        'optional': True,
                        'deletable': True
                    }
                },                
                'note': {
                    'id': {
                        'param': {
                            'withInvitation': submission_id,
                            'optional': True
                        }
                    },
                    'ddate': {
                        'param': {
                            'range': [ 0, 9999999999999 ],
                            'optional': True,
                            'deletable': True
                        }
                    },
                    'signatures': [ '${3/signatures}' ],
                    'readers': note_readers,
                    'writers': [venue_id, '${2/content/authorids/value}'],
                    'content': content
                }
            },
            process=self.get_process_content('process/submission_process.py')
        )

        submission_invitation = self.save_invitation(submission_invitation, replacement=False)

    def set_post_submission_invitation(self):
        venue_id = self.venue_id
        submission_stage = self.venue.submission_stage
        submission_name = submission_stage.name

        submission_id = submission_stage.get_submission_id(self.venue)
        post_submission_id = f'{venue_id}/-/Post_{submission_name}'
        post_submission_cdate = tools.datetime_millis(submission_stage.exp_date) if submission_stage.exp_date else None

        hidden_field_names = submission_stage.get_hidden_field_names()
        note_content = { f: { 'readers': [venue_id, self.venue.get_authors_id('${{4/id}/number}')] } for f in hidden_field_names }

        existing_invitation = openreview.tools.get_invitation(self.client, post_submission_id)        
        if existing_invitation and 'content' in existing_invitation.edit['note']:
            for field, value in existing_invitation.edit['note']['content'].items():
                if field not in hidden_field_names and 'readers' in value:
                    note_content[field] = {
                        'readers': { 'param': { 'const': { 'delete': True } } }
                    }

        submission_invitation = Invitation(
            id=post_submission_id,
            invitees = [venue_id],
            signatures = [venue_id],
            readers = ['everyone'],
            writers = [venue_id],
            cdate=post_submission_cdate,
            date_processes=[{ 
                'dates': ["#{4/cdate}", self.update_date_string],
                'script': self.get_process_content('process/post_submission_process.py')              
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
                    'readers': submission_stage.get_readers(self.venue, '${{2/id}/number}'),
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
        
    def set_pc_submission_revision_invitation(self):
        venue_id = self.venue_id
        submission_stage = self.venue.submission_stage
        cdate = tools.datetime_millis(submission_stage.exp_date) if submission_stage.exp_date else None        

        submission_id = submission_stage.get_submission_id(self.venue)

        content = submission_stage.get_content(api_version='2', conference=self.venue)

        submission_invitation = Invitation(
            id=self.venue.get_pc_submission_revision_id(),
            invitees = [venue_id],
            signatures = [venue_id],
            readers = ['everyone'],
            writers = [venue_id],
            cdate = cdate,
            edit = {
                'signatures': [self.venue.get_program_chairs_id()],
                'readers': [self.venue.get_program_chairs_id(), self.venue.get_authors_id('${2/note/number}')],
                'writers': [venue_id],
                'ddate': {
                    'param': {
                        'range': [ 0, 9999999999999 ],
                        'optional': True,
                        'deletable': True
                    }
                },                
                'note': {
                    'id': {
                        'param': {
                            'withInvitation': submission_id,
                            'optional': True
                        }
                    },                   
                    'content': content,
                    'signatures': [self.venue.get_authors_id('${2/number}')]
                }
            },
            process=self.get_process_content('process/pc_submission_revision_process.py')
        )

        submission_invitation = self.save_invitation(submission_invitation, replacement=True)
    
    def set_review_invitation(self):

        venue_id = self.venue_id
        review_stage = self.venue.review_stage
        review_invitation_id = self.venue.get_invitation_id(review_stage.name)
        review_cdate = tools.datetime_millis(review_stage.start_date if review_stage.start_date else datetime.datetime.utcnow())
        review_duedate = tools.datetime_millis(review_stage.due_date) if review_stage.due_date else None
        review_expdate = tools.datetime_millis(review_stage.exp_date) if review_stage.exp_date else None
        if not review_expdate:
            review_expdate = tools.datetime_millis(review_stage.due_date + datetime.timedelta(minutes = SHORT_BUFFER_MIN)) if review_stage.due_date else None
        
        content = review_stage.get_content(api_version='2', conference=self.venue)

        invitation = Invitation(id=review_invitation_id,
            invitees=[venue_id],
            readers=[venue_id],
            writers=[venue_id],
            signatures=[venue_id],
            cdate=review_cdate,
            date_processes=[{ 
                'dates': ["#{4/edit/invitation/cdate}", self.update_date_string],
                'script': self.invitation_edit_process              
            }],
            content={
                'review_process_script': {
                    'value': self.get_process_content('process/review_process.py')
                }
            },
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
                    'id': self.venue.get_invitation_id(review_stage.name, '${2/content/noteNumber/value}'),
                    'signatures': [ venue_id ],
                    'readers': ['everyone'],
                    'writers': [venue_id],
                    'invitees': [venue_id, self.venue.get_reviewers_id(number='${3/content/noteNumber/value}')],
                    'maxReplies': 1,
                    'cdate': review_cdate,
                    'process': '''def process(client, edit, invitation):
    meta_invitation = client.get_invitation(invitation.invitations[0])
    script = meta_invitation.content['review_process_script']['value']
    funcs = {
        'openreview': openreview
    }
    exec(script, funcs)
    funcs['process'](client, edit, invitation)
''',
                    'edit': {
                        'signatures': { 'param': { 'regex': review_stage.get_signatures(self.venue, '${5/content/noteNumber/value}') }},
                        'readers': ['${2/note/readers}'],
                        'nonreaders': review_stage.get_nonreaders(self.venue, '${4/content/noteNumber/value}'),
                        'writers': [venue_id],
                        'note': {
                            'id': {
                                'param': {
                                    'withInvitation': self.venue.get_invitation_id(review_stage.name, '${6/content/noteNumber/value}'),
                                    'optional': True
                                }
                            },
                            'forum': '${4/content/noteId/value}',
                            'replyto': '${4/content/noteId/value}',
                            'ddate': {
                                'param': {
                                    'range': [ 0, 9999999999999 ],
                                    'optional': True,
                                    'deletable': True                                 
                                }
                            },
                            'signatures': ['${3/signatures}'],
                            'readers': review_stage.get_readers(self.venue, '${5/content/noteNumber/value}', '${3/signatures}'),
                            'nonreaders': review_stage.get_nonreaders(self.venue, '${5/content/noteNumber/value}'),
                            'writers': [venue_id, '${3/signatures}'],
                            'content': content
                        }
                    }
                }

            }
        )

        if review_duedate:
            invitation.edit['invitation']['duedate'] = review_duedate

        if review_expdate:
            invitation.edit['invitation']['expdate'] = review_expdate

        if self.venue.ethics_review_stage:
            invitation.edit['content']['noteReaders'] = {
                'value': {
                    'param': {
                        'type': 'string[]', 'regex': f'{venue_id}/.*|everyone'
                    }
                }
            }
            invitation.content['review_readers'] = {
                'value': review_stage.get_readers(self.venue, '{number}')
            }
            note_readers = ['${5/content/noteReaders/value}']
            if review_stage.release_to_reviewers in [openreview.stages.ReviewStage.Readers.REVIEWER_SIGNATURE, openreview.stages.ReviewStage.Readers.REVIEWERS_SUBMITTED]:
                note_readers.append('${3/signatures}')
            invitation.edit['invitation']['edit']['note']['readers'] = note_readers

        self.save_invitation(invitation, replacement=False)
        return invitation

    def set_review_rebuttal_invitation(self):

        venue_id = self.venue_id
        review_rebuttal_stage = self.venue.review_rebuttal_stage
        review_rebuttal_invitation_id = self.venue.get_invitation_id(review_rebuttal_stage.name)
        review_rebuttal_cdate = tools.datetime_millis(review_rebuttal_stage.start_date if review_rebuttal_stage.start_date else datetime.datetime.utcnow())
        review_rebuttal_duedate = tools.datetime_millis(review_rebuttal_stage.due_date) if review_rebuttal_stage.due_date else None
        review_rebuttal_expdate = tools.datetime_millis(review_rebuttal_stage.due_date + datetime.timedelta(minutes = SHORT_BUFFER_MIN)) if review_rebuttal_stage.due_date else None

        content = review_rebuttal_stage.get_content(api_version='2', conference=self.venue)

        paper_invitation_id = self.venue.get_invitation_id(name=review_rebuttal_stage.name, number='${2/content/noteNumber/value}')
        with_invitation = self.venue.get_invitation_id(name=review_rebuttal_stage.name, number='${6/content/noteNumber/value}')
        reply_to = '${4/content/noteId/value}'

        if not review_rebuttal_stage.single_rebuttal and not review_rebuttal_stage.unlimited_rebuttals:
            paper_invitation_id = self.venue.get_invitation_id(name=review_rebuttal_stage.name, prefix='${2/content/replytoSignatures/value}')
            with_invitation = self.venue.get_invitation_id(name=review_rebuttal_stage.name, prefix='${6/content/replytoSignatures/value}')
            reply_to = '${4/content/replyto/value}'

        if review_rebuttal_stage.unlimited_rebuttals:
            reply_to = {
                'param': {
                    'withForum': '${6/content/noteId/value}'
                }
            }

        invitation = Invitation(id=review_rebuttal_invitation_id,
            invitees=[venue_id],
            readers=[venue_id],
            writers=[venue_id],
            signatures=[venue_id],
            cdate=review_rebuttal_cdate,
            date_processes=[{ 
                'dates': ["#{4/edit/invitation/cdate}", self.update_date_string],
                'script': self.invitation_edit_process              
            }],
            content = {
                'review_rebuttal_process_script': {
                    'value': self.get_process_content('process/review_rebuttal_process.py')
                },
                'reply_to': {
                    'value': 'reviews' if not review_rebuttal_stage.single_rebuttal and not review_rebuttal_stage.unlimited_rebuttals else 'forum'
                }
            },
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
                    },
                    'replytoSignatures': {
                        'value': {
                            'param': {
                                'regex': '.*', 'type': 'string',
                                'optional': True
                            }
                        }
                    },
                    'replyto': {
                        'value': {
                            'param': {
                                'regex': '.*', 'type': 'string',
                                'optional': True
                            }
                        }
                    },
                },
                'replacement': True,
                'invitation': {
                    'id': paper_invitation_id,
                    'signatures': [venue_id],
                    'readers': ['everyone'],
                    'writers': [venue_id],
                    'minReplies': 1,
                    'invitees': [venue_id, self.venue.get_authors_id(number='${3/content/noteNumber/value}')],
                    'cdate': review_rebuttal_cdate,
                    'process': '''def process(client, edit, invitation):
    meta_invitation = client.get_invitation(invitation.invitations[0])
    script = meta_invitation.content['review_rebuttal_process_script']['value']
    funcs = {}
    exec(script, funcs)
    funcs['process'](client, edit, invitation)
''',
                    'edit': {
                        'signatures': { 'param': { 'regex': self.venue.get_authors_id(number='${5/content/noteNumber/value}') }},
                        'readers': review_rebuttal_stage.get_invitation_readers(self.venue, '${4/content/noteNumber/value}'),
                        'writers': [venue_id],
                        'note': {
                            'id': {
                                'param': {
                                    'withInvitation': with_invitation,
                                    'optional': True
                                }
                            },
                            'forum': '${4/content/noteId/value}',
                            'replyto': reply_to,
                            'ddate': {
                                'param': {
                                    'range': [ 0, 9999999999999 ],
                                    'optional': True,
                                    'deletable': True
                                }
                            },
                            'signatures': ['${3/signatures}'],
                            'readers': review_rebuttal_stage.get_invitation_readers(self.venue, '${5/content/noteNumber/value}'),
                            'writers': [venue_id, '${3/signatures}'],
                            'content': content
                        }
                    }
                }
            }
        )

        if not review_rebuttal_stage.unlimited_rebuttals:
            invitation.edit['invitation']['maxReplies'] = 1

        if review_rebuttal_duedate:
            invitation.edit['invitation']['duedate'] = review_rebuttal_duedate

        if review_rebuttal_expdate:
            invitation.edit['invitation']['expdate'] = review_rebuttal_expdate            

        self.save_invitation(invitation, replacement=False)
        return invitation

    def set_meta_review_invitation(self):

        venue_id = self.venue_id
        meta_review_stage = self.venue.meta_review_stage
        meta_review_invitation_id = self.venue.get_invitation_id(meta_review_stage.name)
        meta_review_cdate = tools.datetime_millis(meta_review_stage.start_date if meta_review_stage.start_date else datetime.datetime.utcnow())
        meta_review_duedate = tools.datetime_millis(meta_review_stage.due_date) if meta_review_stage.due_date else None
        meta_review_expdate = tools.datetime_millis(meta_review_stage.exp_date) if meta_review_stage.exp_date else None
        if not meta_review_expdate:
            meta_review_expdate = tools.datetime_millis(meta_review_stage.due_date + datetime.timedelta(minutes = SHORT_BUFFER_MIN)) if meta_review_stage.due_date else None

        content = meta_review_stage.get_content(api_version='2', conference=self.venue)

        invitation = Invitation(id=meta_review_invitation_id,
            invitees=[venue_id],
            readers=[venue_id],
            writers=[venue_id],
            signatures=[venue_id],
            cdate=meta_review_cdate,
            date_processes=[{ 
                'dates': ["#{4/edit/invitation/cdate}", self.update_date_string],
                'script': self.invitation_edit_process              
            }],
            content = {
                'meta_review_process_script': {
                    'value': self.get_process_content('process/metareview_process.py')
                }
            },
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
                    'id': self.venue.get_invitation_id(meta_review_stage.name, '${2/content/noteNumber/value}'),
                    'signatures': [ venue_id ],
                    'readers': ['everyone'],
                    'writers': [venue_id],
                    'invitees': [venue_id, self.venue.get_area_chairs_id(number='${3/content/noteNumber/value}')],
                    'maxReplies': 1,
                    'cdate': meta_review_cdate,
                    'process': '''def process(client, edit, invitation):
    meta_invitation = client.get_invitation(invitation.invitations[0])
    script = meta_invitation.content['meta_review_process_script']['value']
    funcs = {
        'openreview': openreview
    }
    exec(script, funcs)
    funcs['process'](client, edit, invitation)
''',
                    'edit': {
                        'signatures': { 'param': { 'regex': meta_review_stage.get_signatures_regex(self.venue, '${5/content/noteNumber/value}') }},
                        'readers': meta_review_stage.get_readers(self.venue, '${4/content/noteNumber/value}'),
                        'nonreaders': meta_review_stage.get_nonreaders(self.venue, '${4/content/noteNumber/value}'),
                        'writers': [venue_id],
                        'note': {
                            'id': {
                                'param': {
                                    'withInvitation': self.venue.get_invitation_id(meta_review_stage.name, '${6/content/noteNumber/value}'),
                                    'optional': True
                                }
                            },
                            'forum': '${4/content/noteId/value}',
                            'replyto': '${4/content/noteId/value}',
                            'ddate': {
                                'param': {
                                    'range': [ 0, 9999999999999 ],
                                    'optional': True,
                                    'deletable': True                                   
                                }
                            },
                            'signatures': ['${3/signatures}'],
                            'readers': meta_review_stage.get_readers(self.venue, '${5/content/noteNumber/value}'),
                            'nonreaders': meta_review_stage.get_nonreaders(self.venue, '${5/content/noteNumber/value}'),
                            'writers': meta_review_stage.get_writers(self.venue, '${5/content/noteNumber/value}'),
                            'content': content
                        }
                    }
                }
            }
        )

        if meta_review_duedate:
            invitation.edit['invitation']['duedate'] = meta_review_duedate

        if meta_review_expdate:
            invitation.edit['invitation']['expdate'] = meta_review_expdate         

        self.save_invitation(invitation, replacement=False)

        if self.venue.use_senior_area_chairs:

            meta_review_sac_edit_invitation_id = self.venue.get_invitation_id(meta_review_stage.name + '_SAC_Revision')
            invitation = Invitation(id=meta_review_sac_edit_invitation_id,
                invitees=[venue_id],
                readers=[venue_id],
                writers=[venue_id],
                signatures=[venue_id],
                cdate=meta_review_cdate,
                date_processes=[{ 
                    'dates': ["#{4/edit/invitation/cdate}", self.update_date_string],
                    'script': self.invitation_edit_process              
                }],
                content = {
                },
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
                        'id': self.venue.get_invitation_id(meta_review_stage.name + '_SAC_Revision', '${2/content/noteNumber/value}'),
                        'signatures': [ venue_id ],
                        'readers': ['everyone'],
                        'writers': [venue_id],
                        'invitees': [venue_id, self.venue.get_senior_area_chairs_id(number='${3/content/noteNumber/value}')],
                        'maxReplies': 1,
                        'cdate': meta_review_cdate,
                        'edit': {
                            'signatures': { 'param': { 'regex': self.venue.get_senior_area_chairs_id(number='${5/content/noteNumber/value}') }},
                            'readers': meta_review_stage.get_readers(self.venue, '${4/content/noteNumber/value}'),
                            'nonreaders': meta_review_stage.get_nonreaders(self.venue, '${4/content/noteNumber/value}'),
                            'writers': [venue_id],
                            'note': {
                                'id': {
                                    'param': {
                                        'withInvitation': self.venue.get_invitation_id(meta_review_stage.name, '${6/content/noteNumber/value}')
                                    }
                                },
                                'forum': '${4/content/noteId/value}',
                                'replyto': '${4/content/noteId/value}',
                                'content': content
                            }
                        }
                    }
                }
            )

            if meta_review_expdate:
                invitation.edit['invitation']['expdate'] = meta_review_expdate

            self.save_invitation(invitation, replacement=False)

        return invitation

    def set_recruitment_invitation(self, committee_name, options):
        venue = self.venue

        invitation_content = {
            'hash_seed': { 'value': '1234', 'readers': [ venue.venue_id ]},
            'venue_id': { 'value': self.venue_id },
            'committee_name': { 'value': committee_name.replace('_', ' ')[:-1] },
            'committee_id': { 'value': venue.get_committee_id(committee_name) },
            'committee_invited_id': { 'value': venue.get_committee_id_invited(committee_name) },
            'committee_declined_id': { 'value': venue.get_committee_id_declined(committee_name) }       
        }

        if not options.get('allow_overlap_official_committee'):
            if committee_name == venue.reviewers_name and venue.use_area_chairs:
                invitation_content['overlap_committee_name'] = { 'value': venue.area_chairs_name }
                invitation_content['overlap_committee_id'] = { 'value': venue.get_area_chairs_id() }
            elif committee_name == venue.area_chairs_name:
                invitation_content['overlap_committee_name'] = { 'value': venue.reviewers_name }
                invitation_content['overlap_committee_id'] = { 'value': venue.get_reviewers_id() }
        else:
                invitation_content['overlap_committee_name'] = { 'delete': True }
                invitation_content['overlap_committee_id'] = { 'delete': True  }

        content = default_content.recruitment_v2.copy()

        reduced_load = options.get('reduced_load_on_decline', None)
        reduced_load_dict = {}
        if reduced_load:
            reduced_load_dict = {
                'order': 6,
                'description': 'Please select the number of submissions that you would be comfortable reviewing.',
                'value': {
                    'param': {
                        'type': 'string',
                        'enum': reduced_load,
                        'input': 'select',
                        'optional': True
                    }
                }
            }
            content['reduced_load'] = reduced_load_dict
        
        process_content = self.get_process_content('process/recruitment_process.py')
        pre_process_content = self.get_process_content('process/recruitment_pre_process.js')

        with open(os.path.join(os.path.dirname(__file__), 'webfield/recruitResponseWebfield.js')) as webfield_reader:
            webfield_content = webfield_reader.read()

        invitation_id=venue.get_recruitment_id(venue.get_committee_id(name=committee_name))
        current_invitation=tools.get_invitation(self.client, id = invitation_id)

        #if invitation does not exist, post it
        if not current_invitation:
            recruitment_invitation = Invitation(
                id = invitation_id,
                invitees = ['everyone'],
                signatures = [venue.id],
                readers = ['everyone'],
                writers = [venue.id],
                content = invitation_content,
                edit = {
                    'signatures': ['(anonymous)'],
                    'readers': [venue.id],
                    'note' : {
                        'signatures':['${3/signatures}'],
                        'readers': [venue.id, '${2/content/user/value}'],
                        'writers': [venue.id],
                        'content': content
                    }
                },
                process = process_content,
                preprocess = pre_process_content,
                web = webfield_content
            )

            return self.save_invitation(recruitment_invitation, replacement=True)
        else:
            print('current invitation', current_invitation.edit['note']['content'].get('reduced_load', {}))
            print('new invitation', reduced_load_dict)
            updated_invitation = Invitation(
                id = invitation_id
            )
            if current_invitation.edit['note']['content'].get('reduced_load', {}) != reduced_load_dict:
                updated_invitation.edit = {
                    'note': {
                        'content' : {
                            'reduced_load': reduced_load_dict if reduced_load_dict else { 'delete': True }
                        }
                    }
                }
            if 'overlap_committee_name' in invitation_content and current_invitation.content.get('overlap_committee_name', {}) != invitation_content['overlap_committee_name']:
                updated_invitation.content = {
                    'overlap_committee_name': invitation_content['overlap_committee_name'],
                    'overlap_committee_id': invitation_content['overlap_committee_id']
                }
            if updated_invitation.content or updated_invitation.edit:
                return self.save_invitation(updated_invitation)
            else:
                print('do not update recruitment invitation')
                return current_invitation

    def set_bid_invitations(self):

        venue = self.venue
        venue_id = self.venue_id

        for bid_stage in venue.bid_stages:
            match_group_id = bid_stage.committee_id

            invitation_readers = bid_stage.get_invitation_readers(venue)
            bid_readers = bid_stage.get_readers(venue)
            bid_readers[-1] = bid_readers[-1].replace('{signatures}', '${2/tail}')

            head = {
                'param': {
                    'type': 'note',
                    'withInvitation': venue.submission_stage.get_submission_id(venue)
                }
            }
            if match_group_id == venue.get_senior_area_chairs_id():
                head = {
                    'param': {
                        'type': 'profile',
                        'inGroup': venue.get_area_chairs_id()
                    }
                }

            bid_invitation_id = venue.get_invitation_id(bid_stage.name, prefix=match_group_id)

            template_name = 'profileBidWebfield.js' if match_group_id == venue.get_senior_area_chairs_id() else 'paperBidWebfield.js'
            with open(os.path.join(os.path.dirname(__file__), 'webfield/' + template_name)) as webfield_reader:
                webfield_content = webfield_reader.read()

            bid_invitation = Invitation(
                id=bid_invitation_id,
                cdate = tools.datetime_millis(bid_stage.start_date),
                duedate = tools.datetime_millis(bid_stage.due_date) if bid_stage.due_date else None,
                expdate = tools.datetime_millis(bid_stage.due_date + datetime.timedelta(minutes = SHORT_BUFFER_MIN)) if bid_stage.due_date else None,
                invitees = [match_group_id],
                signatures = [venue_id],
                readers = invitation_readers,
                writers = [venue_id],
                minReplies = bid_stage.request_count,
                web = webfield_content,
                content = {
                    'committee_name': { 'value': venue.get_committee_name(match_group_id) }
                },
                edge = {
                    'id': {
                        'param': {
                            'withInvitation': bid_invitation_id,
                            'optional': True
                        }
                    },
                    'ddate': {
                        'param': {
                            'range': [ 0, 9999999999999 ],
                            'optional': True,
                            'deletable': True
                        }
                    },
                    'cdate': {
                        'param': {
                            'range': [ 0, 9999999999999 ],
                            'optional': True,
                            'deletable': True
                        }
                    },
                    'readers':  bid_readers,
                    'writers': [ venue_id, '${2/tail}' ],
                    'signatures': {
                        'param': {
                            'regex': f'~.*|{venue_id}' 
                        }
                    },
                    'head': head,
                    'tail': {
                        'param': {
                            'type': 'profile',
                            'inGroup': match_group_id
                        }
                    },
                    'label': {
                        'param': {
                            'enum': bid_stage.get_bid_options(),
                            'input': 'radio'
                        }
                    }
                }
            )

            bid_invitation = self.save_invitation(bid_invitation, replacement=True)

    def set_official_comment_invitation(self):
        venue_id = self.venue_id
        comment_stage = self.venue.comment_stage
        official_comment_invitation_id = self.venue.get_invitation_id(comment_stage.official_comment_name)
        comment_cdate = tools.datetime_millis(comment_stage.start_date if comment_stage.start_date else datetime.datetime.utcnow())
        comment_expdate = tools.datetime_millis(comment_stage.end_date) if comment_stage.end_date else None

        content = default_content.comment_v2.copy()
        invitees = comment_stage.get_invitees(self.venue, number='${3/content/noteNumber/value}')

        comment_readers = comment_stage.get_readers(self.venue, '${5/content/noteNumber/value}')
        if comment_stage.reader_selection:
            comment_readers = {
                'param': {
                    'enum': comment_stage.get_readers(self.venue, '${7/content/noteNumber/value}')
                }
            }

        invitation = Invitation(id=official_comment_invitation_id,
            invitees=[venue_id],
            readers=[venue_id],
            writers=[venue_id],
            signatures=[venue_id],
            cdate=comment_cdate,
            date_processes=[{ 
                'dates': ["#{4/edit/invitation/cdate}", self.update_date_string],
                'script': self.invitation_edit_process              
            }],
            content={
                'comment_preprocess_script': {
                    'value': self.get_process_content('process/comment_pre_process.js')
                },
                'comment_process_script': {
                    'value': self.get_process_content('process/comment_process.py')
                }
            },
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
                    'id': self.venue.get_invitation_id(comment_stage.official_comment_name, '${2/content/noteNumber/value}'),
                    'signatures': [ venue_id ],
                    'readers': ['everyone'],
                    'writers': [venue_id],
                    'invitees': invitees,
                    'cdate': comment_cdate,
                    'preprocess': '''async function process(client, edit, invitation) {
  client.throwErrors = true;
  const { invitations } = await client.getInvitations({ id: invitation.invitations[0] })
  const metaInvitation = invitations[0];
  const script = metaInvitation.content.comment_preprocess_script.value;
  eval(`var process = ${script}`);
  await process(client, edit, invitation);
}''' if comment_stage.check_mandatory_readers and comment_stage.reader_selection else None,
                    'process': '''def process(client, edit, invitation):
    meta_invitation = client.get_invitation(invitation.invitations[0])
    script = meta_invitation.content['comment_process_script']['value']
    funcs = {
        'openreview': openreview
    }
    exec(script, funcs)
    funcs['process'](client, edit, invitation)
''',
                    'edit': {
                        'signatures': { 'param': { 'regex': comment_stage.get_signatures_regex(self.venue, '${5/content/noteNumber/value}') }},
                        'readers': ['${2/note/readers}'],
                        # 'nonreaders': [],
                        'writers': [venue_id],
                        'note': {
                            'id': {
                                'param': {
                                    'withInvitation': self.venue.get_invitation_id(comment_stage.official_comment_name, '${6/content/noteNumber/value}'),
                                    'optional': True
                                }
                            },
                            'forum': '${4/content/noteId/value}',
                            'replyto': { 
                                'param': {
                                    'withForum': '${6/content/noteId/value}', 
                                }
                            },
                            'ddate': {
                                'param': {
                                    'range': [ 0, 9999999999999 ],
                                    'optional': True,
                                    'deletable': True
                                }
                            },
                            'signatures': ['${3/signatures}'],
                            'readers': comment_readers,
                            # 'nonreaders': [],
                            'writers': [venue_id, '${3/signatures}'],
                            'content': content
                        }
                    }
                }

            }
        )

        if comment_expdate:
            invitation.edit['invitation']['expdate'] = comment_expdate

        self.save_invitation(invitation, replacement=False)
        return invitation

    def set_public_comment_invitation(self):
        venue_id = self.venue_id
        comment_stage = self.venue.comment_stage
        public_comment_invitation = self.venue.get_invitation_id(comment_stage.public_name)
        comment_cdate = tools.datetime_millis(comment_stage.start_date if comment_stage.start_date else datetime.datetime.utcnow())
        comment_expdate = tools.datetime_millis(comment_stage.end_date) if comment_stage.end_date else None

        content = default_content.comment_v2.copy()

        invitation = Invitation(id=public_comment_invitation,
            invitees=[venue_id],
            readers=[venue_id],
            writers=[venue_id],
            signatures=[venue_id],
            cdate=comment_cdate,
            date_processes=[{ 
                'dates': ["#{4/edit/invitation/cdate}", self.update_date_string],
                'script': self.invitation_edit_process              
            }],
            content={
                'comment_process_script': {
                    'value': self.get_process_content('process/comment_process.py')
                },
                'source': {
                    'value': 'public_submissions'
                }
            },
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
                    'id': self.venue.get_invitation_id(comment_stage.public_name, '${2/content/noteNumber/value}'),
                    'signatures': [ venue_id ],
                    'readers': ['everyone'],
                    'writers': [venue_id],
                    'invitees': ['everyone'],
                    'noninvitees': self.venue.get_committee('${3/content/noteNumber/value}', with_authors = True),
                    'cdate': comment_cdate,
                    'process': '''def process(client, edit, invitation):
    meta_invitation = client.get_invitation(invitation.invitations[0])
    script = meta_invitation.content['comment_process_script']['value']
    funcs = {
        'openreview': openreview
    }
    exec(script, funcs)
    funcs['process'](client, edit, invitation)
''',
                    'edit': {
                        'signatures': { 'param': { 'regex': '~.*' }},
                        'readers': ['${2/note/readers}'],
                        'writers': [venue_id],
                        'note': {
                            'id': {
                                'param': {
                                    'withInvitation': self.venue.get_invitation_id(comment_stage.public_name, '${6/content/noteNumber/value}'),
                                    'optional': True
                                }
                            },
                            'forum': '${4/content/noteId/value}',
                            'replyto': { 
                                'param': {
                                    'withForum': '${6/content/noteId/value}', 
                                }
                            },
                            'ddate': {
                                'param': {
                                    'range': [ 0, 9999999999999 ],
                                    'optional': True,
                                    'deletable': True
                                }
                            },
                            'signatures': ['${3/signatures}'],
                            'readers': ['everyone'],
                            'writers': [venue_id, '${3/signatures}'],
                            'content': content
                        }
                    }
                }

            }
        )

        if comment_expdate:
            invitation.edit['invitation']['expdate'] = comment_expdate

        self.save_invitation(invitation, replacement=False)
        return invitation

    def set_decision_invitation(self):

        venue_id = self.venue_id
        decision_stage = self.venue.decision_stage
        decision_invitation_id = self.venue.get_invitation_id(decision_stage.name)
        decision_cdate = tools.datetime_millis(decision_stage.start_date if decision_stage.start_date else datetime.datetime.utcnow())
        decision_due_date = tools.datetime_millis(decision_stage.due_date) if decision_stage.due_date else None
        decision_expdate = tools.datetime_millis(decision_stage.due_date + datetime.timedelta(days = LONG_BUFFER_DAYS)) if decision_stage.due_date else None

        content = decision_stage.get_content(api_version='2', conference=self.venue)

        invitation = Invitation(id=decision_invitation_id,
            invitees=[venue_id],
            readers=[venue_id],
            writers=[venue_id],
            signatures=[venue_id],
            cdate=decision_cdate,
            date_processes=[{ 
                'dates': ["#{4/edit/invitation/cdate}", self.update_date_string],
                'script': self.invitation_edit_process              
            }],
            content={
                'decision_process_script': {
                    'value': self.get_process_content('process/decision_process.py')
                }
            },
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
                    'id': self.venue.get_invitation_id(decision_stage.name, '${2/content/noteNumber/value}'),
                    'signatures': [ venue_id ],
                    'readers': ['everyone'],
                    'writers': [venue_id],
                    'invitees': [venue_id, self.venue.support_user],
                    'maxReplies': 1,
                    'minReplies': 1,
                    'cdate': decision_cdate,
                    'process': '''def process(client, edit, invitation):
    meta_invitation = client.get_invitation(invitation.invitations[0])
    script = meta_invitation.content['decision_process_script']['value']
    funcs = {}
    exec(script, funcs)
    funcs['process'](client, edit, invitation)
''',
                    'edit': {
                        'signatures': [self.venue.get_program_chairs_id()],
                        'readers': decision_stage.get_readers(self.venue, '${4/content/noteNumber/value}'),
                        'nonreaders': decision_stage.get_nonreaders(self.venue, '${4/content/noteNumber/value}'),
                        'writers': [venue_id],
                        'note': {
                            'id': {
                                'param': {
                                    'withInvitation': self.venue.get_invitation_id(decision_stage.name, '${6/content/noteNumber/value}'),
                                    'optional': True
                                }
                            },
                            'forum': '${4/content/noteId/value}',
                            'replyto': '${4/content/noteId/value}',
                            'ddate': {
                                'param': {
                                    'range': [ 0, 9999999999999 ],
                                    'optional': True,
                                    'deletable': True
                                }
                            },
                            'signatures': ['${3/signatures}'],
                            'readers': decision_stage.get_readers(self.venue, '${5/content/noteNumber/value}'),
                            'nonreaders': decision_stage.get_nonreaders(self.venue, '${5/content/noteNumber/value}'),
                            'writers': [venue_id, '${3/signatures}'],
                            'content': content
                        }
                    }
                }

            }
        )

        if decision_due_date:
            invitation.edit['invitation']['duedate'] = decision_due_date

        if decision_expdate:
            invitation.edit['invitation']['expdate'] = decision_expdate        

        self.save_invitation(invitation, replacement=True)
        return invitation

    def set_withdrawal_invitation(self):
        venue_id = self.venue_id
        submission_stage = self.venue.submission_stage
        cdate = tools.datetime_millis(submission_stage.exp_date) if submission_stage.exp_date else None
        exp_date = tools.datetime_millis(self.venue.submission_stage.withdraw_submission_exp_date) if self.venue.submission_stage.withdraw_submission_exp_date else None

        invitation = Invitation(id=self.venue.get_invitation_id(submission_stage.withdrawal_name),
            invitees=[venue_id],
            readers=[venue_id],
            writers=[venue_id],
            signatures=[venue_id],
            cdate=cdate,
            date_processes=[{ 
                'dates': [self.update_date_string],
                'script': self.invitation_edit_process              
            }],            
            content={
                'process_script': {
                    'value': self.get_process_content('process/withdrawal_submission_process.py')
                }
            },            
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
                    'id': self.venue.get_invitation_id(submission_stage.withdrawal_name, '${2/content/noteNumber/value}'),
                    'invitees': [venue_id, self.venue.get_authors_id(number='${3/content/noteNumber/value}')],
                    'readers': ['everyone'],
                    'writers': [venue_id],
                    'signatures': [venue_id],
                    'maxReplies': 1,
                    'process': '''def process(client, edit, invitation):
    meta_invitation = client.get_invitation(invitation.invitations[0])
    script = meta_invitation.content['process_script']['value']
    funcs = {
        'openreview': openreview,
        'datetime': datetime
    }
    exec(script, funcs)
    funcs['process'](client, edit, invitation)''',
                    'edit': {
                        'signatures': { 'param': { 'regex': self.venue.get_authors_id(number='${5/content/noteNumber/value}')  }},
                        'readers': ['${{2/note/forum}/readers}'],
                        'writers': [ venue_id, self.venue.get_authors_id(number='${4/content/noteNumber/value}')],
                        'note': {
                            'forum': '${4/content/noteId/value}',
                            'replyto': '${4/content/noteId/value}',
                            'signatures': [self.venue.get_authors_id(number='${5/content/noteNumber/value}')],
                            'readers': ['${3/readers}'],
                            'writers': [ venue_id ],
                            'content': {
                                'withdrawal_confirmation': {
                                    'value': {
                                        'param': {
                                            'type': 'string',
                                            'enum': [
                                                'I have read and agree with the venue\'s withdrawal policy on behalf of myself and my co-authors.'
                                            ],
                                            'input': 'checkbox'
                                        }
                                    },
                                    'description': 'Please confirm to withdraw.',
                                    'order': 1
                                },
                                'comment': {
                                    'order': 2,
                                    'description': 'Add formatting using Markdown and formulas using LaTeX. For more information see https://openreview.net/faq.',
                                    'value': {
                                        'param': {
                                            'type': 'string',
                                            'maxLength': 200000,
                                            'input': 'textarea',
                                            'optional': True,
                                            'markdown': True
                                        }
                                    }
                                }
                            }
                        }
                    }
                }

            }
        )            

        if cdate:
            invitation.edit['invitation']['cdate'] = cdate
            invitation.date_processes=[{ 
                'dates': ["#{4/edit/invitation/cdate}", self.update_date_string],
                'script': self.invitation_edit_process              
            }]            

        if exp_date:
            invitation.edit['invitation']['expdate'] = exp_date

        self.save_invitation(invitation, replacement=False)

        content = {
            'venue': {
                'value': tools.pretty_id(self.venue.get_withdrawn_submission_venue_id())
            },
            'venueid': {
                'value': self.venue.get_withdrawn_submission_venue_id()
            },
            '_bibtex': {
                'value': {
                    'param': {
                        'type': 'string',
                        'maxLength': 200000,
                        'input': 'textarea',
                        'optional': True
                    }
                }
            }
        }
        if submission_stage.withdrawn_submission_reveal_authors:
            content['authors'] = {
                'readers': { 'param': { 'const': { 'delete': True } } }
            }
            content['authorids'] = {
                'readers': { 'param': { 'const': { 'delete': True } } }
            }

        withdrawn_invitation = Invitation (
            id=self.venue.get_withdrawn_id(),
            invitees = [venue_id],
            noninvitees = [self.venue.get_program_chairs_id()],
            signatures = [venue_id],
            readers = ['everyone'],
            writers = [venue_id],
            edit = {
                'signatures': [venue_id],
                'readers': [venue_id],
                'writers': [venue_id],
                'ddate': {
                    'param': {
                        'range': [ 0, 9999999999999 ],
                        'optional': True,
                        'deletable': True
                    }
                },                 
                'note': {
                    'id': {
                        'param': {
                            'withInvitation': self.venue.submission_stage.get_submission_id(self.venue)
                        }
                    },                    
                    'content': content
                }
            },
            process=self.get_process_content('process/withdrawn_submission_process.py')
        )

        if SubmissionStage.Readers.EVERYONE not in submission_stage.readers and submission_stage.withdrawn_submission_public:
            withdrawn_invitation.edit['note']['readers'] = ['everyone']

        self.save_invitation(withdrawn_invitation, replacement=True)

        expire_invitation = Invitation (
            id=self.venue.get_invitation_id('Withdraw_Expiration'),
            invitees = [venue_id],
            signatures = [venue_id],
            readers = ['everyone'],
            writers = [venue_id],
            edit = {
                'signatures': [venue_id],
                'readers': [venue_id],
                'writers': [venue_id],
                'ddate': {
                    'param': {
                        'range': [ 0, 9999999999999 ],
                        'optional': True,
                        'deletable': True
                    }
                },                 
                'invitation': {
                    'id': {
                        'param': {
                            'regex': self.venue.get_paper_group_prefix()
                        }
                    },
                    'signatures': [venue_id],                  
                    'expdate': {
                        'param': {
                            'range': [ 0, 9999999999999 ],
                            'deletable': True
                        }
                    }
                }
            }
        )

        self.save_invitation(expire_invitation, replacement=True)

        invitation = Invitation(id=self.venue.get_invitation_id(submission_stage.withdrawal_name + '_Reversion'),
            invitees=[venue_id],
            readers=[venue_id],
            writers=[venue_id],
            signatures=[venue_id],
            content={
                'process_script': {
                    'value': self.get_process_content('process/withdrawal_reversion_submission_process.py')
                }
            },            
            edit={
                'signatures': [venue_id],
                'readers': [venue_id],
                'writers': [venue_id],
                'content': {
                    'noteId': {
                        'value': {
                            'param': {
                                'regex': '.*', 'type': 'string' 
                            }
                        }
                    },
                    'withdrawalId': {
                        'value': {
                            'param': {
                                'regex': '.*', 'type': 'string' 
                            }
                        }
                    }
                },
                'replacement': True,
                'invitation': {
                    'id': self.venue.get_invitation_id(submission_stage.withdrawal_name + '_Reversion', '${{2/content/noteId/value}/number}'),
                    'invitees': [venue_id],
                    'readers': ['everyone'],
                    'writers': [venue_id],
                    'signatures': [venue_id],
                    'maxReplies': 1,
                    'process': '''def process(client, edit, invitation):
    meta_invitation = client.get_invitation(invitation.invitations[0])
    script = meta_invitation.content['process_script']['value']
    funcs = {
        'openreview': openreview,
        'datetime': datetime
    }
    exec(script, funcs)
    funcs['process'](client, edit, invitation)''',
                    'edit': {
                        'signatures': [self.venue.get_program_chairs_id()],
                        'readers': ['${{2/note/forum}/readers}'],
                        'writers': [ venue_id],
                        'note': {
                            'forum': '${4/content/noteId/value}',
                            'replyto': '${4/content/withdrawalId/value}',
                            'signatures': [self.venue.get_program_chairs_id()],
                            'readers': ['${3/readers}'],
                            'writers': [ venue_id ],
                            'content': {
                                'revert_withdrawal_confirmation': {
                                    'value': {
                                        'param': {
                                            'type': 'string',
                                            'enum': [
                                                'We approve the reversion of withdrawn submission.'
                                            ],
                                            'input': 'checkbox'
                                        }
                                    },
                                    'description': 'Please confirm to withdraw.',
                                    'order': 1
                                },
                                'comment': {
                                    'order': 2,
                                    'description': 'Add formatting using Markdown and formulas using LaTeX. For more information see https://openreview.net/faq.',
                                    'value': {
                                        'param': {
                                            'type': 'string',
                                            'maxLength': 200000,
                                            'input': 'textarea',
                                            'optional': True,
                                            'markdown': True
                                        }
                                    }
                                }
                            }
                        }
                    }
                }

            }
        )            


        self.save_invitation(invitation, replacement=True)

    def set_desk_rejection_invitation(self):
        venue_id = self.venue_id
        submission_stage = self.venue.submission_stage
        cdate = tools.datetime_millis(submission_stage.exp_date) if submission_stage.exp_date else None
        exp_date = tools.datetime_millis(self.venue.submission_stage.due_date + datetime.timedelta(days = 90)) if self.venue.submission_stage.due_date else None

        content = default_content.desk_reject_v2.copy()

        invitation = Invitation(id=self.venue.get_invitation_id(submission_stage.desk_rejection_name),
            invitees=[venue_id],
            readers=[venue_id],
            writers=[venue_id],
            signatures=[venue_id],
            cdate=cdate,
            date_processes=[{ 
                'dates': [self.update_date_string],
                'script': self.invitation_edit_process              
            }],
            content={
                'process_script': {
                    'value': self.get_process_content('process/desk_rejection_submission_process.py')
                }
            },
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
                    'id': self.venue.get_invitation_id(submission_stage.desk_rejection_name, '${2/content/noteNumber/value}'),
                    'invitees': [venue_id],
                    'readers': ['everyone'],
                    'writers': [venue_id],
                    'signatures': [venue_id],
                    'maxReplies': 1,
                    'process': '''def process(client, edit, invitation):
    meta_invitation = client.get_invitation(invitation.invitations[0])
    script = meta_invitation.content['process_script']['value']
    funcs = {
        'openreview': openreview,
        'datetime': datetime
    }
    exec(script, funcs)
    funcs['process'](client, edit, invitation)''',
                    'edit': {
                        'signatures': [self.venue.get_program_chairs_id()],
                        'readers': submission_stage.get_desk_rejection_readers(self.venue, '${4/content/noteNumber/value}'),
                        'writers': [venue_id],
                        'note': {
                            'forum': '${4/content/noteId/value}',
                            'replyto': '${4/content/noteId/value}',
                            'signatures': ['${3/signatures}'],
                            'readers': ['${3/readers}'],
                            'writers': [ venue_id ],
                            'content': content
                        }
                    }
                }
            }
        )

        if exp_date:
            invitation.edit['invitation']['expdate'] = exp_date

        if cdate:
            invitation.edit['invitation']['cdate'] = cdate
            invitation.date_processes=[{ 
                'dates': ["#{4/edit/invitation/cdate}", self.update_date_string],
                'script': self.invitation_edit_process              
            }]

        self.save_invitation(invitation, replacement=False)

        content = {
            'venue': {
                'value': tools.pretty_id(self.venue.get_desk_rejected_submission_venue_id())
            },
            'venueid': {
                'value': self.venue.get_desk_rejected_submission_venue_id()
            },
            '_bibtex': {
                'value': {
                    'param': {
                        'type': 'string',
                        'maxLength': 200000,
                        'input': 'textarea',
                        'optional': True
                    }
                }
            }
        }
        if submission_stage.desk_rejected_submission_reveal_authors:
            content['authors'] = {
                'readers': { 'param': { 'const': { 'delete': True } } }
            }
            content['authorids'] = {
                'readers': { 'param': { 'const': { 'delete': True } } }
            }

        desk_rejected_invitation = Invitation (
            id=self.venue.get_desk_rejected_id(),
            invitees = [venue_id],
            noninvitees = [self.venue.get_program_chairs_id()],
            signatures = [venue_id],
            readers = ['everyone'],
            writers = [venue_id],
            edit = {
                'signatures': [venue_id],
                'readers': [venue_id],
                'writers': [venue_id],
                'ddate': {
                    'param': {
                        'range': [ 0, 9999999999999 ],
                        'optional': True,
                        'deletable': True
                    }
                },
                'note': {
                    'id': {
                        'param': {
                            'withInvitation': self.venue.submission_stage.get_submission_id(self.venue)
                        }
                    },
                    'content': content
                }
            },
            process=self.get_process_content('process/desk_rejected_submission_process.py')
        )

        if SubmissionStage.Readers.EVERYONE not in submission_stage.readers and submission_stage.desk_rejected_submission_public:
            desk_rejected_invitation.edit['note']['readers'] = ['everyone']

        self.save_invitation(desk_rejected_invitation, replacement=True)

        expire_invitation = Invitation (
            id=self.venue.get_invitation_id('Desk_Reject_Expiration'),
            invitees = [venue_id],
            signatures = [venue_id],
            readers = ['everyone'],
            writers = [venue_id],
            edit = {
                'signatures': [venue_id],
                'readers': [venue_id],
                'writers': [venue_id],
                'ddate': {
                    'param': {
                        'range': [ 0, 9999999999999 ],
                        'optional': True,
                        'deletable': True
                    }
                },
                'invitation': {
                    'id': {
                        'param': {
                            'regex': self.venue.get_paper_group_prefix()
                        }
                    },
                    'signatures': [venue_id],
                    'expdate': {
                        'param': {
                            'range': [ 0, 9999999999999 ],
                            'deletable': True
                        }
                    }
                }
            }
        )

        self.save_invitation(expire_invitation, replacement=True)

        content = default_content.desk_reject_reversion_v2

        invitation = Invitation(id=self.venue.get_invitation_id(submission_stage.desk_rejection_name + '_Reversion'),
            invitees=[venue_id],
            readers=[venue_id],
            writers=[venue_id],
            signatures=[venue_id],
            content={
                'process_script': {
                    'value': self.get_process_content('process/desk_rejection_reversion_submission_process.py')
                }
            },
            edit={
                'signatures': [venue_id],
                'readers': [venue_id],
                'writers': [venue_id],
                'content': {
                    'noteId': {
                        'value': {
                            'param': {
                                'regex': '.*', 'type': 'string'
                            }
                        }
                    },
                    'deskRejectionId': {
                        'value': {
                            'param': {
                                'regex': '.*', 'type': 'string'
                            }
                        }
                    }
                },
                'replacement': True,
                'invitation': {
                    'id': self.venue.get_invitation_id(submission_stage.desk_rejection_name + '_Reversion', '${{2/content/noteId/value}/number}'),
                    'invitees': [venue_id],
                    'readers': ['everyone'],
                    'writers': [venue_id],
                    'signatures': [venue_id],
                    'maxReplies': 1,
                    'process': '''def process(client, edit, invitation):
    meta_invitation = client.get_invitation(invitation.invitations[0])
    script = meta_invitation.content['process_script']['value']
    funcs = {
        'openreview': openreview,
        'datetime': datetime
    }
    exec(script, funcs)
    funcs['process'](client, edit, invitation)''',
                    'edit': {
                        'signatures': [self.venue.get_program_chairs_id()],
                        'readers': submission_stage.get_desk_rejection_readers(self.venue, '${{4/content/noteId/value}/number}'),
                        'writers': [ venue_id],
                        'note': {
                            'forum': '${4/content/noteId/value}',
                            'replyto': '${4/content/deskRejectionId/value}',
                            'signatures': [self.venue.get_program_chairs_id()],
                            'readers': ['${3/readers}'],
                            'writers': [ venue_id ],
                            'content': content
                        }
                    }
                }
            }
        )

        self.save_invitation(invitation, replacement=True)

    def set_submission_revision_invitation(self, submission_revision_stage=None):

        venue_id = self.venue_id
        revision_stage = submission_revision_stage if submission_revision_stage else self.venue.submission_revision_stage
        revision_invitation_id = self.venue.get_invitation_id(revision_stage.name)
        revision_cdate = tools.datetime_millis(revision_stage.start_date if revision_stage.start_date else datetime.datetime.utcnow())
        revision_duedate = tools.datetime_millis(revision_stage.due_date) if revision_stage.due_date else None
        revision_expdate = tools.datetime_millis(revision_stage.due_date + datetime.timedelta(minutes = SHORT_BUFFER_MIN)) if revision_stage.due_date else None

        only_accepted = revision_stage.only_accepted
        content = revision_stage.get_content(api_version='2', conference=self.venue)

        invitation = Invitation(id=revision_invitation_id,
            invitees=[venue_id],
            readers=[venue_id],
            writers=[venue_id],
            signatures=[venue_id],
            cdate=revision_cdate,
            date_processes=[{ 
                'dates': ["#{4/edit/invitation/cdate}", self.update_date_string],
                'script': self.invitation_edit_process              
            }],
            content={
                'revision_process_script': {
                    'value': self.get_process_content('process/submission_revision_process.py')
                },
                'source': {
                    'value': 'accepted_submissions' if only_accepted else 'all_submissions'
                }
            },
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
                    'id': self.venue.get_invitation_id(revision_stage.name, '${2/content/noteNumber/value}'),
                    'signatures': [venue_id],
                    'readers': ['everyone'],
                    'writers': [venue_id],
                    'invitees': [venue_id, self.venue.get_authors_id(number='${3/content/noteNumber/value}')],
                    'cdate': revision_cdate,
                    'process': '''def process(client, edit, invitation):
    meta_invitation = client.get_invitation(invitation.invitations[0])
    script = meta_invitation.content['revision_process_script']['value']
    funcs = {
        'openreview': openreview
    }
    exec(script, funcs)
    funcs['process'](client, edit, invitation)
''',
                    'edit': {
                        'ddate': {
                            'param': {
                                'range': [ 0, 9999999999999 ],
                                'optional': True                                   
                            }
                        }
                        ,
                        'signatures': { 'param': { 'regex': f"{self.venue.get_authors_id(number='${5/content/noteNumber/value}')}|{self.venue.get_program_chairs_id()}" }},
                        'readers': [ venue_id, self.venue.get_authors_id(number='${4/content/noteNumber/value}')],
                        'writers': [ venue_id, self.venue.get_authors_id(number='${4/content/noteNumber/value}')],
                        'note': {
                            'id': '${4/content/noteId/value}',
                            'content': content
                        }
                    }
                }
            }
        )

        if revision_duedate:
            invitation.edit['invitation']['duedate'] = revision_duedate

        if revision_expdate:
            invitation.edit['invitation']['expdate'] = revision_expdate        

        self.save_invitation(invitation, replacement=False)
        return invitation

    def set_custom_stage_invitation(self):

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

        paper_invitation_id = self.venue.get_invitation_id(name=custom_stage.name, number='${2/content/noteNumber/value}')
        with_invitation = self.venue.get_invitation_id(name=custom_stage.name, number='${6/content/noteNumber/value}')
        if custom_stage_replyto == 'forum':
            reply_to = '${4/content/noteId/value}'
        elif custom_stage_replyto == 'withForum':
            reply_to = {
                'param': {
                    'withForum': '${6/content/noteId/value}'
                }
            }
        else:
            paper_invitation_id = self.venue.get_invitation_id(name=custom_stage.name, prefix='${2/content/replytoSignatures/value}')
            with_invitation = self.venue.get_invitation_id(name=custom_stage.name, prefix='${6/content/replytoSignatures/value}')
            reply_to = '${4/content/replyto/value}'

        invitation_content = {
            'source': { 'value': custom_stage_source },
            'reply_to': { 'value': custom_stage_replyto },
            'email_pcs': { 'value': custom_stage.email_pcs },
            'email_sacs': { 'value': custom_stage.email_sacs },
            'notify_readers': { 'value': custom_stage.notify_readers },
            'email_template': { 'value': custom_stage.email_template if custom_stage.email_template else '' },
            'custom_stage_process_script': { 'value': self.get_process_content('process/custom_stage_process.py')}
        }

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
                    'invitees': custom_stage.get_invitees(self.venue, number='${3/content/noteNumber/value}'),
                    'cdate': custom_stage_cdate,
                    'process': '''def process(client, edit, invitation):
    meta_invitation = client.get_invitation(invitation.invitations[0])
    script = meta_invitation.content['custom_stage_process_script']['value']
    funcs = {
        'openreview': openreview
    }
    exec(script, funcs)
    funcs['process'](client, edit, invitation)
''',
                    'edit': {
                        'signatures': { 'param': { 'regex': custom_stage.get_signatures_regex(self.venue, '${5/content/noteNumber/value}') }},
                        'readers': custom_stage.get_readers(self.venue, '${4/content/noteNumber/value}'),
                        'writers': [venue_id],
                        'note': {
                            'id': {
                                'param': {
                                    'withInvitation': with_invitation,
                                    'optional': True
                                }
                            },
                            'forum': '${4/content/noteId/value}',
                            'replyto': reply_to,
                            'ddate': {
                                'param': {
                                    'range': [ 0, 9999999999999 ],
                                    'optional': True,
                                    'deletable': True
                                }
                            },
                            'signatures': ['${3/signatures}'],
                            'readers': ['${3/readers}'],
                            'writers': [venue_id, '${3/signatures}'],
                            'content': content
                        }
                    }
                }
            }
        )

        if custom_stage_replyto in ['reviews', 'metareviews']:
            invitation.edit['content']['replytoSignatures'] = {
                'value': {
                    'param': {
                        'regex': '.*', 'type': 'string',
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

        if custom_stage_duedate:
            invitation.edit['invitation']['duedate'] = custom_stage_duedate
        if custom_stage_expdate:
            invitation.edit['invitation']['expdate'] = custom_stage_expdate
        if not custom_stage.multi_reply:
            invitation.edit['invitation']['maxReplies'] = 1

        self.save_invitation(invitation, replacement=False)
        return invitation

    def set_assignment_invitation(self, committee_id):
        
        venue = self.venue
        venue_id = venue.get_id()
        assignment_invitation_id = venue.get_assignment_id(committee_id, deployed=True)
        is_reviewer = committee_id == venue.get_reviewers_id()
        is_area_chair = committee_id == venue.get_area_chairs_id()
        is_senior_area_chair = committee_id == venue.get_senior_area_chairs_id()
        review_stage = venue.review_stage if is_reviewer else venue.meta_review_stage
        is_ethics_reviewer = committee_id == venue.get_ethics_reviewers_id()

        content = {
            'review_name': {
                'value': review_stage.name if review_stage else 'Official_Review'
            },
            'reviewers_id': {
                'value': venue.get_reviewers_id() if is_reviewer else venue.get_area_chairs_id()
            },
            'reviewers_name': {
                'value': venue.reviewers_name if is_reviewer else venue.area_chairs_name
            },
            'reviewers_anon_name': {
                'value': venue.get_anon_reviewers_name() if is_reviewer else venue.get_anon_area_chairs_name()
            },
            'sync_sac_id': {
                'value': venue.get_senior_area_chairs_id(number='{number}') if is_area_chair and venue.use_senior_area_chairs else ''
            },
            'sac_assignment_id': {
                'value': venue.get_assignment_id(venue.get_senior_area_chairs_id(), deployed=True) if is_area_chair and venue.use_senior_area_chairs else ''
            }
        }

        if is_ethics_reviewer:
            content = {
                'review_name': {
                    'value': venue.ethics_review_stage.name
                },
                'reviewers_id': {
                    'value': venue.get_ethics_reviewers_id()
                },
                'reviewers_name': {
                    'value': venue.ethics_reviewers_name
                },
                'reviewers_anon_name': {
                    'value': venue.anon_ethics_reviewers_name()
                },
                'sync_sac_id': {
                    'value': ''
                },
                'sac_assignment_id': {
                    'value': ''
                }
            }

        preprocess = self.get_process_content('process/assignment_pre_process.js')
        process = self.get_process_content('process/assignment_post_process.py')

        invitation_readers = [venue_id]
        edge_invitees = [venue_id]
        edge_readers = [venue_id]
        edge_writers = [venue_id]
        edge_signatures = [venue_id + '$', venue.get_program_chairs_id()]
        edge_nonreaders = []
        edge_head = {
            'param': {
                'type': 'note',
                'withVenueid': venue.get_submission_venue_id()
            }
        }  
        
        if is_reviewer:
            edge_nonreaders = [venue.get_authors_id(number='${{2/head}/number}')] 
            if venue.use_senior_area_chairs:
                invitation_readers.append(venue.get_senior_area_chairs_id())
                edge_invitees.append(venue.get_senior_area_chairs_id())
                edge_readers.append(venue.get_senior_area_chairs_id(number='${{2/head}/number}'))
                edge_writers.append(venue.get_senior_area_chairs_id(number='${{2/head}/number}'))
                edge_signatures.append(venue.get_senior_area_chairs_id(number='.*'))
            if venue.use_area_chairs:
                invitation_readers.append(venue.get_area_chairs_id())
                edge_invitees.append(venue.get_area_chairs_id())
                edge_readers.append(venue.get_area_chairs_id(number='${{2/head}/number}'))
                edge_writers.append(venue.get_area_chairs_id(number='${{2/head}/number}'))
                edge_signatures.append(venue.get_area_chairs_id(number='.*', anon=True))

        if is_ethics_reviewer:
            invitation_readers.append(venue.get_ethics_chairs_id())
            edge_nonreaders = [venue.get_authors_id(number='${{2/head}/number}')]
            edge_invitees.append(venue.get_ethics_chairs_id())
            edge_readers.append(venue.get_ethics_chairs_id())
            edge_writers.append(venue.get_ethics_chairs_id())
            edge_signatures.append(venue.get_ethics_chairs_id())

        if is_area_chair:
            invitation_readers.append(venue.get_area_chairs_id())
            edge_nonreaders = [venue.get_authors_id(number='${{2/head}/number}')] 
            if venue.use_senior_area_chairs:
                invitation_readers.append(venue.get_senior_area_chairs_id())
                edge_invitees.append(venue.get_senior_area_chairs_id())
                edge_readers.append(venue.get_senior_area_chairs_id(number='${{2/head}/number}'))
                edge_writers.append(venue.get_senior_area_chairs_id(number='${{2/head}/number}'))
                edge_signatures.append(venue.get_senior_area_chairs_id(number='.*'))


        if is_senior_area_chair:
            edge_head = {
                'param': {
                    'type': 'profile',
                    'inGroup': venue.get_area_chairs_id()
                }
            }
            process = self.get_process_content('process/sac_assignment_post_process.py')
            preprocess=None
            content=None
            edge_readers.append('${2/head}')

        edge_readers.append('${2/tail}')

        invitation = Invitation(
            id = assignment_invitation_id,
            invitees = edge_invitees,
            readers = invitation_readers,
            writers = [venue_id],
            signatures = [venue.get_program_chairs_id()],
            process=process,
            preprocess=preprocess,
            content=content,
            edge = {
                'id': {
                    'param': {
                        'withInvitation': assignment_invitation_id,
                        'optional': True
                    }
                },
                'ddate': {
                    'param': {
                        'range': [ 0, 9999999999999 ],
                        'optional': True,
                        'deletable': True
                    }
                },
                'cdate': {
                    'param': {
                        'range': [ 0, 9999999999999 ],
                        'optional': True,
                        'deletable': True
                    }
                },
                'readers':  edge_readers,
                'nonreaders': edge_nonreaders,
                'writers': edge_writers,
                'signatures': {
                    'param': { 
                        'regex': '|'.join(edge_signatures),
                        'default': [venue.get_program_chairs_id()]
                    }
                },
                'head': edge_head,
                'tail': {
                    'param': {
                        'type': 'profile',
                        'inGroup': committee_id
                    }                
                },
                'weight': {
                    'param': {
                        'minimum': -1
                    }            
                }
            }
        )

        self.save_invitation(invitation, replacement=True)            

    def set_expertise_selection_invitations(self):

        venue_id = self.venue_id
        expertise_selection_stage = self.venue.expertise_selection_stage

        with open(os.path.join(os.path.dirname(__file__), 'webfield/expertiseSelectionWebfield.js')) as webfield_reader:
            webfield_content = webfield_reader.read()

        def build_expertise_selection(committee_id):
            expertise_selection_id = self.venue.get_invitation_id(expertise_selection_stage.name, prefix=committee_id)
            invitation = Invitation(
                id= expertise_selection_id,
                cdate = tools.datetime_millis(expertise_selection_stage.start_date),
                duedate = tools.datetime_millis(expertise_selection_stage.due_date),
                expdate = tools.datetime_millis(expertise_selection_stage.due_date + datetime.timedelta(days = LONG_BUFFER_DAYS)) if expertise_selection_stage.due_date else None,
                invitees = [committee_id],
                signatures = [venue_id],
                readers = [venue_id, committee_id],
                writers = [venue_id],
                minReplies=1,
                web = webfield_content,
                edge = {
                    'id': {
                        'param': {
                            'withInvitation': expertise_selection_id,
                            'optional': True
                        }
                    },
                    'ddate': {
                        'param': {
                            # 'type': 'date',
                            'range': [ 0, 9999999999999 ],
                            'optional': True,
                            'deletable': True
                        }
                    },
                    'cdate': {
                        'param': {
                            'range': [ 0, 9999999999999 ],
                            'optional': True,
                            'deletable': True
                        }
                    },
                    'readers': [ venue_id, '${2/signatures}' ],
                    'writers': [ venue_id, '${2/signatures}' ],
                    'signatures': {
                        'param': {
                            'regex': '~.*' 
                        }
                    },
                    'head': {
                        'param': {
                            'type': 'note'
                        }
                    },
                    'tail': {
                        'param': {
                            'type': 'profile',
                            'inGroup': committee_id
                        }
                    },
                    'label': {
                        'param': {
                            'enum': ['Include' if expertise_selection_stage.include_option else 'Exclude'],
                        }
                    }
                }
            )

            self.save_invitation(invitation, replacement=True)

        build_expertise_selection(self.venue.get_reviewers_id())

        if self.venue.use_area_chairs:
            build_expertise_selection(self.venue.get_area_chairs_id())

        if self.venue.use_senior_area_chairs:
            build_expertise_selection(self.venue.get_senior_area_chairs_id())

    def set_registration_invitations(self):

        venue = self.venue
        venue_id = self.venue_id

        for registration_stage in venue.registration_stages:
            committee_id = registration_stage.committee_id

            readers = [venue_id, committee_id]

            registration_parent_invitation_id = venue.get_invitation_id(name=f'{registration_stage.name}_Form', prefix=committee_id)
            invitation = Invitation(
                id = registration_parent_invitation_id,
                readers = ['everyone'],
                writers = [venue_id],
                signatures = [venue_id],
                invitees = [venue_id, venue.support_user],
                edit = {
                    'signatures': [venue_id],
                    'readers': [venue_id],
                    'writers': [venue_id],
                    'note': {
                        'id': {
                            'param': {
                                'withInvitation': registration_parent_invitation_id,
                                'optional': True
                            }
                        },
                        'ddate': {
                            'param': {
                                'range': [ 0, 9999999999999 ],
                                'optional': True,
                                'deletable': True
                            }
                        },                    
                        'readers': readers,
                        'writers': [venue_id],
                        'signatures': [venue_id],
                        'content': {
                            'title': {
                                'order': 1,
                                'value': {
                                    'param': {
                                        'type': 'string',
                                        'maxLength': 250
                                    }
                                }
                            },
                            'instructions': {
                                'order': 2,
                                'value': {
                                    'param': {
                                        'type': 'string',
                                        'maxLength': 250000,
                                        'markdown': True,
                                        'input': 'textarea'                                    
                                    }
                                }
                            }
                        }                    
                    }
                }
            )
            self.save_invitation(invitation, replacement=True)

            registration_notes = self.client.get_notes(invitation=registration_parent_invitation_id)
            if registration_notes:
                print('Updating existing registration note')
                forum_edit = self.client.post_note_edit(invitation = self.venue.get_meta_invitation_id(),
                    signatures=[venue_id],
                    note = Note(
                        id = registration_notes[0].id,
                        content = {
                            'instructions': { 'value': registration_stage.instructions },
                            'title': { 'value': registration_stage.title}
                        }
                    ))
            else:
                forum_edit = self.client.post_note_edit(invitation=invitation.id,
                    signatures=[venue_id],
                    note = Note(
                        signatures = [venue_id],
                        content = {
                            'instructions': { 'value': registration_stage.instructions },
                            'title': { 'value': registration_stage.title}
                        }
                    )
                )
            forum_note_id = forum_edit['note']['id']
            start_date = registration_stage.start_date
            due_date = registration_stage.due_date
            expdate = registration_stage.expdate if registration_stage.expdate else due_date

            registration_content = registration_stage.get_content(api_version='2', conference=self.venue)        

            registration_invitation_id = venue.get_invitation_id(name=f'{registration_stage.name}', prefix=committee_id)
            invitation=Invitation(id=registration_invitation_id,
                invitees=[committee_id],
                readers=readers,
                writers=[venue_id],
                signatures=[venue_id],
                cdate = tools.datetime_millis(start_date) if start_date else None,
                duedate = tools.datetime_millis(due_date) if due_date else None,
                expdate = tools.datetime_millis(expdate) if expdate else None,
                maxReplies = 1,
                minReplies = 1,       
                edit={
                    'signatures': { 'param': { 'regex': '~.*' }},
                    'readers': [venue_id, '${2/signatures}'],
                    'note': {
                        'id': {
                            'param': {
                                'withInvitation': registration_invitation_id,
                                'optional': True
                            }
                        },
                        'ddate': {
                            'param': {
                                'range': [ 0, 9999999999999 ],
                                'optional': True,
                                'deletable': True
                            }
                        },                    
                        'forum': forum_note_id,
                        'replyto': forum_note_id,
                        'signatures': ['${3/signatures}'],
                        'readers': [venue_id, '${3/signatures}'],
                        'writers': [venue_id, '${3/signatures}'],
                        'content': registration_content
                    }
                }        
            )
            self.save_invitation(invitation, replacement=True)

    def set_paper_recruitment_invitation(self, invitation_id, committee_id, invited_committee_name, hash_seed, assignment_title=None, due_date=None, invited_label='Invited', accepted_label='Accepted', declined_label='Declined', proposed=False):
        venue = self.venue

        process_file='process/simple_paper_recruitment_process.py' if proposed else 'process/paper_recruitment_process.py'
        process_content = self.get_process_content(process_file)
        preprocess_content = self.get_process_content('process/paper_recruitment_pre_process.js')

        edge_readers = []
        edge_writers = []
        if committee_id.endswith(venue.area_chairs_name):
            if venue.use_senior_area_chairs:
                edge_readers.append(venue.get_senior_area_chairs_id(number='{number}'))
                edge_writers.append(venue.get_senior_area_chairs_id(number='{number}'))

        if committee_id.endswith(venue.reviewers_name):
            if venue.use_senior_area_chairs:
                edge_readers.append(venue.get_senior_area_chairs_id(number='{number}'))
                edge_writers.append(venue.get_senior_area_chairs_id(number='{number}'))

            if venue.use_area_chairs:
                edge_readers.append(venue.get_area_chairs_id(number='{number}'))
                edge_writers.append(venue.get_area_chairs_id(number='{number}'))

        invitation_content = {
            'committee_name': { 'value':  venue.get_committee_name(committee_id, pretty=True) },
            'edge_readers': { 'value': edge_readers },
            'edge_writers': { 'value': edge_writers },
            'hash_seed': { 'value': hash_seed, 'readers': [ venue.venue_id ]},
            'committee_id': { 'value': committee_id },
            'committee_invited_id': { 'value': venue.get_committee_id(name=invited_committee_name + '/Invited') if invited_committee_name else ''},
            'invite_assignment_invitation_id': { 'value': venue.get_assignment_id(committee_id, invite=True)},
            'assignment_invitation_id': { 'value': venue.get_assignment_id(committee_id) if assignment_title else venue.get_assignment_id(committee_id, deployed=True) },
            'invited_label': { 'value': invited_label },
            'accepted_label': { 'value': accepted_label },
            'declined_label': { 'value': declined_label },
            'assignment_title': { 'value': assignment_title } if assignment_title else { 'delete': True },
            'external_committee_id': { 'value': venue.get_committee_id(name=invited_committee_name) if invited_committee_name else '' },
            'external_paper_committee_id': {'value': venue.get_committee_id(name=invited_committee_name, number='{number}') if assignment_title else ''}
        }

        content = default_content.paper_recruitment_v2.copy()

        with open(os.path.join(os.path.dirname(__file__), 'webfield/paperRecruitResponseWebfield.js')) as webfield_reader:
            webfield_content = webfield_reader.read()

        paper_recruitment_invitation = Invitation(
                id = invitation_id,
                invitees = ['everyone'],
                signatures = [venue.get_program_chairs_id()],
                readers = ['everyone'],
                writers = [venue.id],
                content = invitation_content,
                edit = {
                    'signatures': ['(anonymous)'],
                    'readers': [venue.id],
                    'note' : {
                        'signatures':['${3/signatures}'],
                        'readers': [venue.id, '${2/content/user/value}', '${2/content/inviter/value}'],
                        'writers': [venue.id, '${3/signatures}'],
                        'content': content
                    }
                },
                process = process_content,
                preprocess = preprocess_content,
                web = webfield_content
            )
        self.save_invitation(paper_recruitment_invitation, replacement=True)

    def set_submission_reviewer_group_invitation(self):

        venue_id = self.venue_id
        invitation_id = self.venue.get_invitation_id(f'{self.venue.submission_stage.name}_Group', prefix=self.venue.get_reviewers_id())
        cdate=tools.datetime_millis(self.venue.submission_stage.second_due_date_exp_date if self.venue.submission_stage.second_due_date_exp_date else self.venue.submission_stage.exp_date)

        invitation = Invitation(id=invitation_id,
            invitees=[venue_id],
            readers=[venue_id],
            writers=[venue_id],
            signatures=[venue_id],
            cdate=cdate,
            date_processes=[{ 
                'dates': ["#{4/cdate}", self.update_date_string],
                'script': self.group_edit_process              
            }],
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
                'group': {
                    'id': self.venue.get_reviewers_id(number='${2/content/noteNumber/value}'),
                    'readers': self.venue.group_builder.get_reviewer_paper_group_readers('${3/content/noteNumber/value}'),
                    'nonreaders': [self.venue.get_authors_id('${3/content/noteNumber/value}')],
                    'deanonymizers': self.venue.group_builder.get_reviewer_identity_readers('${3/content/noteNumber/value}'),
                    'writers': self.venue.group_builder.get_reviewer_paper_group_writers('${3/content/noteNumber/value}'),
                    'signatures': [self.venue.id],
                    'signatories': [self.venue.id],
                    'anonids': True
                }

            }
        )

        self.save_invitation(invitation, replacement=False)
        return invitation
    
    def set_submission_area_chair_group_invitation(self):

        venue_id = self.venue_id
        invitation_id = self.venue.get_invitation_id(f'{self.venue.submission_stage.name}_Group', prefix=self.venue.get_area_chairs_id())
        cdate=tools.datetime_millis(self.venue.submission_stage.second_due_date_exp_date if self.venue.submission_stage.second_due_date_exp_date else self.venue.submission_stage.exp_date)
            

        invitation = Invitation(id=invitation_id,
            invitees=[venue_id],
            readers=[venue_id],
            writers=[venue_id],
            signatures=[venue_id],
            cdate=cdate,
            date_processes=[{ 
                'dates': ["#{4/cdate}", self.update_date_string],
                'script': self.group_edit_process              
            }],
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
                'group': {
                    'id': self.venue.get_area_chairs_id(number='${2/content/noteNumber/value}'),
                    'readers': self.venue.group_builder.get_area_chair_paper_group_readers('${3/content/noteNumber/value}'),
                    'nonreaders': [self.venue.get_authors_id('${3/content/noteNumber/value}')],
                    'deanonymizers': self.venue.group_builder.get_area_chair_identity_readers('${3/content/noteNumber/value}'),
                    'writers': [self.venue.id],
                    'signatures': [self.venue.id],
                    'signatories': [self.venue.id],
                    'anonids': True,
                }

            }
        )

        self.save_invitation(invitation, replacement=False)
        return invitation

    def set_submission_senior_area_chair_group_invitation(self):

        venue_id = self.venue_id
        invitation_id = self.venue.get_invitation_id(f'{self.venue.submission_stage.name}_Group', prefix=self.venue.get_senior_area_chairs_id())
        cdate=tools.datetime_millis(self.venue.submission_stage.second_due_date_exp_date if self.venue.submission_stage.second_due_date_exp_date else self.venue.submission_stage.exp_date)
            

        invitation = Invitation(id=invitation_id,
            invitees=[venue_id],
            readers=[venue_id],
            writers=[venue_id],
            signatures=[venue_id],
            cdate=cdate,
            date_processes=[{ 
                'dates': ["#{4/cdate}", self.update_date_string],
                'script': self.group_edit_process              
            }],
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
                'group': {
                    'id': self.venue.get_senior_area_chairs_id(number='${2/content/noteNumber/value}'),
                    'readers': self.venue.group_builder.get_senior_area_chair_identity_readers('${3/content/noteNumber/value}'),
                    'nonreaders': [self.venue.get_authors_id('${3/content/noteNumber/value}')],
                    'writers': [self.venue.id],
                    'signatures': [self.venue.id],
                    'signatories': [self.venue.id, self.venue.get_senior_area_chairs_id(number='${3/content/noteNumber/value}')],
                }

            }
        )

        self.save_invitation(invitation, replacement=False)
        return invitation

    def set_ethics_paper_groups_invitation(self):

        venue = self.venue
        venue_id = self.venue_id
        ethics_stage = venue.ethics_review_stage
        invitation_id = venue.get_invitation_id(f'{venue.submission_stage.name}_Group', prefix=self.venue.get_ethics_reviewers_id())

        invitation = Invitation(id=invitation_id,
            invitees=[venue_id],
            readers=[venue_id],
            writers=[venue_id],
            signatures=[venue_id],
            cdate=tools.datetime_millis(datetime.datetime.utcnow()),
            date_processes=[{
                'dates': ["#{4/cdate}", self.update_date_string],
                'script': self.group_edit_process
            }],
            content = {
                'source': {
                    'value': 'flagged_for_ethics_review'
                }
            },
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
                'group': {
                    'id': venue.get_ethics_reviewers_id(number='${2/content/noteNumber/value}'),
                    'readers': [venue_id,
                                venue.get_ethics_reviewers_id(number='${3/content/noteNumber/value}'),
                                venue.get_ethics_chairs_id()],
                    'nonreaders': [venue.get_authors_id('${3/content/noteNumber/value}')],
                    'deanonymizers': [venue_id, venue.get_ethics_chairs_id()],
                    'writers': [venue_id],
                    'signatures': [venue_id],
                    'signatories': [venue_id],
                    'anonids': True
                }
            }
        )

        self.save_invitation(invitation, replacement=False)
        return invitation
    
    def set_ethics_review_invitation(self):

        venue_id = self.venue_id
        ethics_review_stage = self.venue.ethics_review_stage
        ethics_review_invitation_id = self.venue.get_invitation_id(ethics_review_stage.name)
        ethics_review_cdate = tools.datetime_millis(ethics_review_stage.start_date if ethics_review_stage.start_date else datetime.datetime.utcnow())
        ethics_review_duedate = tools.datetime_millis(ethics_review_stage.due_date) if ethics_review_stage.due_date else None
        ethics_review_expdate = tools.datetime_millis(ethics_review_stage.due_date + datetime.timedelta(minutes = SHORT_BUFFER_MIN))  if ethics_review_stage.due_date else None
        
        content = ethics_review_stage.get_content(api_version='2', conference=self.venue)

        invitation = Invitation(id=ethics_review_invitation_id,
            invitees=[venue_id],
            readers=[venue_id],
            writers=[venue_id],
            signatures=[venue_id],
            cdate=ethics_review_cdate,
            date_processes=[{ 
                'dates': ["#{4/edit/invitation/cdate}", self.update_date_string],
                'script': self.invitation_edit_process              
            }],
            content={
                'source': {
                    'value': 'flagged_for_ethics_review'
                },
                'ethics_review_process_script': {
                    'value': self.get_process_content('process/ethics_review_process.py')
                }
            },
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
                    'id': self.venue.get_invitation_id(ethics_review_stage.name, '${2/content/noteNumber/value}'),
                    'signatures': [ venue_id ],
                    'readers': ['everyone'],
                    'writers': [venue_id],
                    'invitees': [venue_id, self.venue.get_ethics_reviewers_id(number='${3/content/noteNumber/value}')],
                    'maxReplies': 1,
                    'cdate': ethics_review_cdate,
                    'process': '''def process(client, edit, invitation):
    meta_invitation = client.get_invitation(invitation.invitations[0])
    script = meta_invitation.content['ethics_review_process_script']['value']
    funcs = {
        'openreview': openreview
    }
    exec(script, funcs)
    funcs['process'](client, edit, invitation)
''',
                    'edit': {
                        'signatures': { 'param': { 'regex': ethics_review_stage.get_signatures(self.venue, '${5/content/noteNumber/value}') }},
                        'readers': ethics_review_stage.get_readers(self.venue, '${4/content/noteNumber/value}', '${2/signatures}'),
                        'nonreaders': ethics_review_stage.get_nonreaders(self.venue, '${4/content/noteNumber/value}'),
                        'writers': [venue_id],
                        'note': {
                            'id': {
                                'param': {
                                    'withInvitation': self.venue.get_invitation_id(ethics_review_stage.name, '${6/content/noteNumber/value}'),
                                    'optional': True
                                }
                            },
                            'forum': '${4/content/noteId/value}',
                            'replyto': '${4/content/noteId/value}',
                            'ddate': {
                                'param': {
                                    'range': [ 0, 9999999999999 ],
                                    'optional': True,
                                    'deletable': True                                 
                                }
                            },
                            'signatures': ['${3/signatures}'],
                            'readers': ethics_review_stage.get_readers(self.venue, '${5/content/noteNumber/value}', '${3/signatures}'),
                            'nonreaders': ethics_review_stage.get_nonreaders(self.venue, '${5/content/noteNumber/value}'),
                            'writers': [venue_id, '${3/signatures}'],
                            'content': content
                        }
                    }
                }

            }
        )

        if ethics_review_duedate:
            invitation.edit['invitation']['duedate'] = ethics_review_duedate

        if ethics_review_expdate:
            invitation.edit['invitation']['expdate'] = ethics_review_expdate


        self.save_invitation(invitation, replacement=False)
        return invitation

    def set_ethics_stage_invitation(self):
        venue_id = self.venue_id
        ethics_review_stage = self.venue.ethics_review_stage
        ethics_stage_name = ethics_review_stage.name
        ethics_stage_id = f'{venue_id}/-/{ethics_stage_name}_Flag'
        submission_id = self.venue.submission_stage.get_submission_id(self.venue)

        ethics_stage_invitation = Invitation(
            id=ethics_stage_id,
            invitees = [venue_id],
            signatures = [venue_id],
            readers = ['everyone'],
            writers = [venue_id],
            content = {
                'review_readers': {
                    'value': self.venue.review_stage.get_readers(self.venue, '{number}')
                }
            },
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
                        'flagged_for_ethics_review': {
                            'value': {
                                'param': {
                                    'type': 'boolean',
                                    'const': True
                                }
                            }
                        }
                    }
                }
            },
            process=self.get_process_content('process/ethics_flag_process.py')
        )

        if 'everyone' not in self.venue.submission_stage.get_readers(self.venue, '${{2/id}/number}'):
            ethics_stage_invitation.edit['note']['readers'] = {
                'param': {
                    'const': {
                        'append': [self.venue.get_ethics_reviewers_id('${{3/id}/number}')]
                    }
                }
            }

        self.save_invitation(ethics_stage_invitation, replacement=False)
        return ethics_stage_invitation