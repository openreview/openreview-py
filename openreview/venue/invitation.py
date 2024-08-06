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
        self.update_wait_time = 1000 if 'localhost' in venue.client.baseurl else update_wait_time
        self.spleep_time_for_logs = 0.5 if 'localhost' in venue.client.baseurl else 10
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

    def _should_update_meta_invitation(self, invitation):
        if 'invitation_edit_script' not in invitation.content or 'group_edit_script' not in invitation.content:
            return True
        if invitation.content['invitation_edit_script']['value'] != self.get_process_content('process/invitation_edit_process.py'):
            return True
        if invitation.content['group_edit_script']['value'] != self.get_process_content('process/group_edit_process.py'):
            return True

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
        invitation = tools.get_invitation(self.client, id = invitation_id)

        if invitation:
            self.save_invitation(invitation=Invitation(id=invitation.id,
                    expdate=tools.datetime_millis(datetime.datetime.utcnow()),
                    signatures=[self.venue_id]
                )
            )

    def unexpire_invitation(self, invitation_id):
        invitation = tools.get_invitation(self.client, id = invitation_id)

        if invitation:
            self.save_invitation(invitation=Invitation(id=invitation.id,
                    expdate={ "delete": True },
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

        if meta_invitation is None or self._should_update_meta_invitation(meta_invitation):
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
        submission_license = self.venue.submission_license
        commitments_venue = submission_stage.commitments_venue

        content = submission_stage.get_content(api_version='2', conference=self.venue, venue_id=self.venue.get_submission_venue_id())

        edit_readers = ['everyone'] if submission_stage.create_groups else [venue_id, '${2/note/content/authorids/value}']
        note_readers = ['everyone'] if submission_stage.create_groups else [venue_id, '${2/content/authorids/value}']

        submission_id = submission_stage.get_submission_id(self.venue)
        submission_cdate = tools.datetime_millis(submission_stage.start_date if submission_stage.start_date else datetime.datetime.utcnow())

        submission_invitation = Invitation(
            id=submission_id,
            invitees = ['~'],
            signatures = [venue_id] if not commitments_venue else ['~Super_User1'],
            readers = ['everyone'],
            writers = [venue_id],
            cdate=submission_cdate,
            duedate=tools.datetime_millis(submission_stage.due_date) if submission_stage.due_date else None,
            expdate = tools.datetime_millis(submission_stage.exp_date) if submission_stage.exp_date else None,
            content = {
                'email_authors': { 'value': True },
                'email_pcs': { 'value': self.venue.submission_stage.email_pcs }
            },
            edit = {
                'signatures': {
                    'param': {
                        'items': [
                            { 'prefix': '~.*', 'optional': True },
                            { 'value': self.venue.get_program_chairs_id(), 'optional': True }
                        ]
                    }
                },
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
                            'withVenueid': self.venue.get_submission_venue_id(),
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

        # Set license for all submissions or allow authors to set license
        if submission_license:
            if isinstance(submission_license, str): # Existing venues have license as a string
                submission_invitation.edit['note']['license'] = submission_license
            elif len(submission_license) == 1:
                submission_invitation.edit['note']['license'] = submission_license[0]
            else:
                license_options = [ { "value": license, "description": license } for license in submission_license ]
                submission_invitation.edit['note']['license'] = {
                    "param": {
                        "enum": license_options
                    }
                }

        if commitments_venue:
            submission_invitation.preprocess=self.get_process_content('process/submission_commitments_preprocess.py')

        submission_invitation = self.save_invitation(submission_invitation, replacement=False)

    def set_submission_deletion_invitation(self, submission_revision_stage):

        venue_id = self.venue_id
        invitation_name = 'Deletion'
        revision_stage = submission_revision_stage
        deletion_invitation_id = self.venue.get_invitation_id(invitation_name)
        deletion_cdate = tools.datetime_millis(revision_stage.start_date if revision_stage.start_date else datetime.datetime.utcnow())
        deletion_expdate = tools.datetime_millis(revision_stage.due_date + datetime.timedelta(minutes = SHORT_BUFFER_MIN)) if revision_stage.due_date else None

        invitation = Invitation(id=deletion_invitation_id,
            invitees=[venue_id],
            readers=[venue_id],
            writers=[venue_id],
            signatures=[venue_id],
            cdate=deletion_cdate,
            date_processes=[{
                'dates': ["#{4/edit/invitation/cdate}", self.update_date_string],
                'script': self.invitation_edit_process
            }],
            content={
                'deletion_process_script': {
                    'value': self.get_process_content('process/submission_deletion_process.py')
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
                                'type': 'integer'
                            }
                        }
                    },
                    'noteId': {
                        'value': {
                            'param': {
                                'type': 'string'
                            }
                        }
                    }
                },
                'replacement': True,
                'invitation': {
                    'id': self.venue.get_invitation_id(invitation_name, '${2/content/noteNumber/value}'),
                    'signatures': [venue_id],
                    'readers': [venue_id, self.venue.get_authors_id(number='${3/content/noteNumber/value}')],
                    'writers': [venue_id],
                    'invitees': [venue_id, self.venue.get_authors_id(number='${3/content/noteNumber/value}')],
                    'cdate': deletion_cdate,
                    'process': '''def process(client, edit, invitation):
    meta_invitation = client.get_invitation(invitation.invitations[0])
    script = meta_invitation.content['deletion_process_script']['value']
    funcs = {
        'openreview': openreview,
        'datetime': datetime
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
                        },
                        'signatures': {
                            'param': {
                                'items': [
                                    { 'value': self.venue.get_authors_id(number='${7/content/noteNumber/value}'), 'optional': True },
                                    { 'value': self.venue.get_program_chairs_id(), 'optional': True }
                                ]
                            }
                        },
                        'readers': [venue_id, self.venue.get_authors_id(number='${4/content/noteNumber/value}')],
                        'writers': [venue_id, self.venue.get_authors_id(number='${4/content/noteNumber/value}')],
                        'note': {
                            'id': '${4/content/noteId/value}',
                            'ddate': {
                                'param': {
                                    'range': [ 0, 9999999999999 ],
                                    'optional': True,
                                    'deletable': True
                                }
                            }
                        }
                    }
                }
            }
        )

        if deletion_expdate:
            invitation.edit['invitation']['expdate'] = deletion_expdate

        self.save_invitation(invitation, replacement=False)

        expire_invitation = Invitation (
            id=self.venue.get_invitation_id('Deletion_Expiration'),
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
        return invitation

    def set_post_submission_invitation(self):
        venue_id = self.venue_id
        submission_stage = self.venue.submission_stage

        submission_id = submission_stage.get_submission_id(self.venue)
        post_submission_id = self.venue.get_post_submission_id()
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
                    'optional': True,
                    'deletable': True
                }
            }
        }

        if note_content:
            submission_invitation.edit['note']['content'] = note_content

        submission_invitation = self.save_invitation(submission_invitation, replacement=False)

    def set_pc_submission_revision_invitation(self):
        venue_id = self.venue_id
        submission_license = self.venue.submission_license
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

        # Allow PCs to revise license
        if submission_license:
            if isinstance(submission_license, str):
                submission_invitation.edit['note']['license'] = submission_license
            elif len(submission_license) == 1:
                submission_invitation.edit['note']['license'] = submission_license[0]
            else:
                license_options = [ { "value": license, "description": license } for license in submission_license ]
                submission_invitation.edit['note']['license'] = {
                    "param": {
                        "enum": license_options
                    }
                }

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

        previous_query = {}
        invitation = tools.get_invitation(self.client, review_invitation_id)
        if invitation:
            previous_query = invitation.content.get('source_submissions_query', {}).get('value', {}) if invitation.content else {}

        source_submissions_query = review_stage.source_submissions_query if review_stage.source_submissions_query else previous_query

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
                'email_pcs': {
                    'value': review_stage.email_pcs
                },
            },
            edit={
                'signatures': [venue_id],
                'readers': [venue_id],
                'writers': [venue_id],
                'content': {
                    'noteNumber': {
                        'value': {
                            'param': {
                                'type': 'integer'
                            }
                        }
                    },
                    'noteId': {
                        'value': {
                            'param': {
                                'type': 'string'
                            }
                        }
                    }
                },
                'replacement': True,
                'invitation': {
                    'id': self.venue.get_invitation_id(review_stage.child_invitations_name, '${2/content/noteNumber/value}'),
                    'signatures': [ venue_id ],
                    'readers': ['everyone'],
                    'writers': [venue_id],
                    'invitees': [venue_id, self.venue.get_reviewers_id(number='${3/content/noteNumber/value}')],
                    'maxReplies': 1,
                    'cdate': review_cdate,
                    'edit': {
                        'signatures': {
                            'param': {
                                'items': [ { 'prefix': s, 'optional': True } if '.*' in s else { 'value': s, 'optional': True } for s in review_stage.get_signatures(self.venue, '${7/content/noteNumber/value}')]
                            }
                        },
                        'readers': ['${2/note/readers}'],
                        'nonreaders': review_stage.get_nonreaders(self.venue, '${4/content/noteNumber/value}'),
                        'writers': [venue_id],
                        'note': {
                            'id': {
                                'param': {
                                    'withInvitation': self.venue.get_invitation_id(review_stage.child_invitations_name, '${6/content/noteNumber/value}'),
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

        if review_stage.process_path:
            invitation.content['review_process_script'] = {
               'value': self.get_process_content(review_stage.process_path)
            }
            invitation.edit['invitation']['process'] = '''def process(client, edit, invitation):
    meta_invitation = client.get_invitation(invitation.invitations[0])
    script = meta_invitation.content['review_process_script']['value']
    funcs = {
        'openreview': openreview
    }
    exec(script, funcs)
    funcs['process'](client, edit, invitation)
'''

        if review_stage.preprocess_path:
            invitation.content['review_preprocess_script'] = {
                'value': self.get_process_content(review_stage.preprocess_path)
            }
            invitation.edit['invitation']['preprocess'] = '''def process(client, edit, invitation):
    meta_invitation = client.get_invitation(invitation.invitations[0])
    script = meta_invitation.content['review_preprocess_script']['value']
    funcs = {
        'openreview': openreview
    }
    exec(script, funcs)
    funcs['process'](client, edit, invitation)
'''

        if review_duedate:
            invitation.edit['invitation']['duedate'] = review_duedate

        if review_expdate:
            invitation.edit['invitation']['expdate'] = review_expdate

        if source_submissions_query:
            invitation.content['source_submissions_query'] = {
                'value': source_submissions_query
            }

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
            if review_stage.release_to_reviewers in [openreview.stages.ReviewStage.Readers.REVIEWER_SIGNATURE, openreview.stages.ReviewStage.Readers.REVIEWERS_SUBMITTED] and not review_stage.public:
                note_readers.append('${3/signatures}')
            invitation.edit['invitation']['edit']['note']['readers'] = note_readers

        self.save_invitation(invitation, replacement=False)
        return invitation

    def update_review_invitations(self):

        source_submissions_query_mapping = self.venue.source_submissions_query_mapping
        if not source_submissions_query_mapping:
            source_submissions_query_mapping = {
                self.venue.review_stage.name: None
            }

        for stage_name in source_submissions_query_mapping.keys():

            print('Updating invitation:', stage_name)

            invitation = openreview.tools.get_invitation(self.client, self.venue.get_invitation_id(stage_name))
            if invitation:

                note_readers = ['${5/content/noteReaders/value}']

                review_readers = invitation.edit['invitation']['edit']['note']['readers']
                review_readers = [reader.replace('${5/content/noteNumber/value}', '{number}') for reader in review_readers]
                if '${5/content/noteReaders/value}' in review_readers:
                    if '${3/signatures}' in review_readers:
                        note_readers.append('${3/signatures}')
                    review_readers = []
                else:
                    if '${3/signatures}' in review_readers:
                        note_readers.append('${3/signatures}')
                        review_readers.remove('${3/signatures}')

                review_invitation = Invitation(id=invitation.id,
                    edit={
                        'content': {
                            'noteReaders': {
                                'value': {
                                    'param': {
                                        'type': 'string[]', 'regex': f'{self.venue_id}/.*|everyone'
                                    }
                                }
                            }
                        },
                        'invitation': {
                            'edit': {
                                'note': {
                                    'readers': note_readers
                                }
                            }
                        }
                    }
                )
                if review_readers:
                    review_invitation.content = {
                        'review_readers': {
                            'value': review_readers
                        }
                    }

                self.client.post_invitation_edit(invitations=self.venue.get_meta_invitation_id(),
                    signatures=[self.venue_id],
                    replacement=False,
                    invitation=review_invitation
                )

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
            submission_prefix = venue_id + '/' + self.venue.submission_stage.name + '${2/content/noteNumber/value}/'
            review_prefix = self.venue.review_stage.name + '${2/content/replyNumber/value}'
            paper_invitation_id = self.venue.get_invitation_id(name=review_rebuttal_stage.name, prefix=submission_prefix+review_prefix)
            submission_prefix = venue_id + '/' + self.venue.submission_stage.name + '${6/content/noteNumber/value}/'
            review_prefix = self.venue.review_stage.name + '${6/content/replyNumber/value}'
            with_invitation = self.venue.get_invitation_id(name=review_rebuttal_stage.name, prefix=submission_prefix+review_prefix)
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
                                'type': 'integer'
                            }
                        }
                    },
                    'noteId': {
                        'value': {
                            'param': {
                                'type': 'string'
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
                        'signatures': {
                            'param': {
                                'items': [{ 'value': self.venue.get_authors_id(number='${7/content/noteNumber/value}') }]
                            }
                        },
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

        if not review_rebuttal_stage.single_rebuttal and not review_rebuttal_stage.unlimited_rebuttals:
            invitation.edit['content']['replyNumber'] = {
                'value': {
                    'param': {
                        'type': 'integer',
                        'optional': True
                    }
                }
            }
            invitation.edit['content']['replyto'] = {
                'value': {
                    'param': {
                        'type': 'string',
                        'optional': True
                    }
                }
            }

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

        previous_query = {}
        invitation = tools.get_invitation(self.client, meta_review_invitation_id)
        if invitation:
            previous_query = invitation.content.get('source_submissions_query', {}).get('value', {}) if invitation.content else {}

        source_submissions_query = meta_review_stage.source_submissions_query if meta_review_stage.source_submissions_query else previous_query

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
            content = {},
            edit={
                'signatures': [venue_id],
                'readers': [venue_id],
                'writers': [venue_id],
                'content': {
                    'noteNumber': {
                        'value': {
                            'param': {
                                'type': 'integer'
                            }
                        }
                    },
                    'noteId': {
                        'value': {
                            'param': {
                                'type': 'string'
                            }
                        }
                    }
                },
                'replacement': True,
                'invitation': {
                    'id': self.venue.get_invitation_id(meta_review_stage.child_invitations_name, '${2/content/noteNumber/value}'),
                    'signatures': [ venue_id ],
                    'readers': ['everyone'],
                    'writers': [venue_id],
                    'invitees': [venue_id, self.venue.get_area_chairs_id(number='${3/content/noteNumber/value}')],
                    'noninvitees': [self.venue.get_authors_id(number='${3/content/noteNumber/value}')] + ([self.venue.get_secondary_area_chairs_id('${3/content/noteNumber/value}')] if self.venue.use_secondary_area_chairs else []),
                    'maxReplies': 1,
                    'cdate': meta_review_cdate,
                    'edit': {
                        'signatures': {
                            'param': {
                                'items': [ { 'prefix': s, 'optional': True } if '.*' in s else { 'value': s, 'optional': True } for s in meta_review_stage.get_signatures(self.venue, '${7/content/noteNumber/value}')]
                            }
                        },
                        'readers': meta_review_stage.get_readers(self.venue, '${4/content/noteNumber/value}'),
                        'nonreaders': meta_review_stage.get_nonreaders(self.venue, '${4/content/noteNumber/value}'),
                        'writers': [venue_id],
                        'note': {
                            'id': {
                                'param': {
                                    'withInvitation': self.venue.get_invitation_id(meta_review_stage.child_invitations_name, '${6/content/noteNumber/value}'),
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

        if meta_review_stage.process_path:
            invitation.content['metareview_process_script'] = {
               'value': self.get_process_content(meta_review_stage.process_path)
            }
            invitation.edit['invitation']['process'] = '''def process(client, edit, invitation):
    meta_invitation = client.get_invitation(invitation.invitations[0])
    script = meta_invitation.content['metareview_process_script']['value']
    funcs = {
        'openreview': openreview
    }
    exec(script, funcs)
    funcs['process'](client, edit, invitation)
'''

        if meta_review_stage.preprocess_path:
            invitation.content['metareview_preprocess_script'] = {
                'value': self.get_process_content(meta_review_stage.preprocess_path)
            }
            invitation.edit['invitation']['preprocess'] = '''def process(client, edit, invitation):
    meta_invitation = client.get_invitation(invitation.invitations[0])
    script = meta_invitation.content['metareview_preprocess_script']['value']
    funcs = {
        'openreview': openreview
    }
    exec(script, funcs)
    funcs['process'](client, edit, invitation)
'''

        if meta_review_duedate:
            invitation.edit['invitation']['duedate'] = meta_review_duedate

        if meta_review_expdate:
            invitation.edit['invitation']['expdate'] = meta_review_expdate

        if source_submissions_query:
            invitation.content['source_submissions_query'] = {
                'value': source_submissions_query
            }

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
                                    'type': 'integer'
                                }
                            }
                        },
                        'noteId': {
                            'value': {
                                'param': {
                                    'type': 'string'
                                }
                            }
                        }
                    },
                    'replacement': True,
                    'invitation': {
                        'id': self.venue.get_invitation_id(meta_review_stage.child_invitations_name + '_SAC_Revision', '${2/content/noteNumber/value}'),
                        'signatures': [ venue_id ],
                        'readers': ['everyone'],
                        'writers': [venue_id],
                        'invitees': [venue_id, self.venue.get_senior_area_chairs_id(number='${3/content/noteNumber/value}')],
                        'cdate': meta_review_cdate,
                        'edit': {
                            'signatures': {
                                'param': {
                                    'items': [
                                        { 'value': self.venue.get_senior_area_chairs_id(number='${7/content/noteNumber/value}') }
                                    ]
                                }
                            },
                            'readers': meta_review_stage.get_readers(self.venue, '${4/content/noteNumber/value}'),
                            'nonreaders': meta_review_stage.get_nonreaders(self.venue, '${4/content/noteNumber/value}'),
                            'writers': [venue_id],
                            'note': {
                                'id': {
                                    'param': {
                                        'withInvitation': self.venue.get_invitation_id(meta_review_stage.child_invitations_name, '${6/content/noteNumber/value}')
                                    }
                                },
                                'forum': '${4/content/noteId/value}',
                                'content': content
                            }
                        }
                    }
                }
            )

            if meta_review_expdate:
                invitation.edit['invitation']['expdate'] = meta_review_expdate

            if source_submissions_query:
                invitation.content['source_submissions_query'] = {
                    'value': source_submissions_query
                }

            self.save_invitation(invitation, replacement=False)

        return invitation

    def set_recruitment_invitation(self, committee_name, options):
        venue = self.venue

        invitation_content = {
            'hash_seed': { 'value': '1234', 'readers': [ venue.venue_id ]},
            'venue_id': { 'value': self.venue_id },
            'committee_name': { 'value': venue.get_committee_name(committee_name, pretty=True) },
            'committee_id': { 'value': venue.get_committee_id(committee_name) },
            'committee_invited_id': { 'value': venue.get_committee_id_invited(committee_name) },
            'committee_declined_id': { 'value': venue.get_committee_id_declined(committee_name) },
            'allow_accept_with_reduced_load': { 'value': options.get('allow_accept_with_reduced_load') }
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
                        'optional': True,
                        'deletable': True
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

            updated_invitation_content = {}

            if 'overlap_committee_name' in invitation_content and current_invitation.content.get('overlap_committee_name', {}) != invitation_content['overlap_committee_name']:
                updated_invitation_content['overlap_committee_name'] = invitation_content['overlap_committee_name']
                updated_invitation_content['overlap_committee_id'] = invitation_content['overlap_committee_id']

            if current_invitation.content.get('allow_accept_with_reduced_load') != invitation_content['allow_accept_with_reduced_load']:
                updated_invitation_content['allow_accept_with_reduced_load'] = invitation_content['allow_accept_with_reduced_load']

            if updated_invitation_content:
                updated_invitation.content = updated_invitation_content

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
            if match_group_id == venue.get_senior_area_chairs_id() and not venue.sac_paper_assignments:
                head = {
                    'param': {
                        'type': 'profile',
                        'options': {
                            'group': venue.get_area_chairs_id()
                        }
                    }
                }

            bid_score_spec = bid_stage.default_scores_spec

            bid_invitation_id = venue.get_invitation_id(bid_stage.name, prefix=match_group_id)

            template_name = 'profileBidWebfield.js' if match_group_id == venue.get_senior_area_chairs_id() and not venue.sac_paper_assignments else 'paperBidWebfield.js'
            with open(os.path.join(os.path.dirname(__file__), 'webfield/' + template_name)) as webfield_reader:
                webfield_content = webfield_reader.read()

            bid_invitation = Invitation(
                id=bid_invitation_id,
                cdate = tools.datetime_millis(bid_stage.start_date),
                duedate = tools.datetime_millis(bid_stage.due_date) if bid_stage.due_date else None,
                expdate = tools.datetime_millis(bid_stage.due_date + datetime.timedelta(minutes = SHORT_BUFFER_MIN)) if bid_stage.due_date else None,
                responseArchiveDate = venue.get_edges_archive_date(),
                invitees = [match_group_id],
                signatures = [venue_id],
                readers = invitation_readers,
                writers = [venue_id],
                minReplies = bid_stage.request_count,
                web = webfield_content,
                content = {
                    'committee_name': { 'value': venue.get_committee_name(match_group_id) },
                    'scores_spec': { 'value': bid_score_spec }
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
                            'options': {
                                'group': match_group_id
                            }
                        },
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

            configuration_invitation = tools.get_invitation(self.client, f'{match_group_id}/-/Assignment_Configuration')
            if configuration_invitation:
                updated_config = False
                scores_spec_param = configuration_invitation.edit['note']['content']['scores_specification']['value']['param']
                if 'default' in scores_spec_param and bid_invitation.id not in scores_spec_param:
                    scores_spec_param['default'][bid_invitation.id] = bid_score_spec
                    updated_config = True
                elif 'default' not in scores_spec_param:
                    scores_spec_param['default'] = {
                        bid_invitation.id: bid_score_spec
                    }
                    updated_config = True
                if updated_config:
                    self.client.post_invitation_edit(invitations=venue.get_meta_invitation_id(),
                        signatures=[venue_id],
                        invitation=openreview.api.Invitation(
                            id=configuration_invitation.id,
                            edit={
                                'note': {
                                    'content': {
                                        'scores_specification': {
                                            'value': {
                                                'param': scores_spec_param
                                            }
                                        }
                                    }
                                }
                            }
                        )
                    )

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
                    'items': comment_stage.get_readers(self.venue, '${8/content/noteNumber/value}', api_version='2'),
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
                },
                'email_pcs': {
                    'value': comment_stage.email_pcs
                },
                'email_sacs': {
                    'value': comment_stage.email_sacs
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
                                'type': 'integer'
                            }
                        }
                    },
                    'noteId': {
                        'value': {
                            'param': {
                                'type': 'string'
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
}''' if comment_stage.check_mandatory_readers and comment_stage.reader_selection else '',
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
                        'signatures': {
                            'param': {
                                'items': [ { 'prefix': s, 'optional': True } if '.*' in s else { 'value': s, 'optional': True } for s in comment_stage.get_signatures(self.venue, '${7/content/noteNumber/value}')]
                            }
                        },
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

        if self.venue.ethics_review_stage and self.venue.ethics_review_stage.enable_comments:
            invitation.edit['content']['noteReaders'] = {
                'value': {
                    'param': {
                        'type': 'string[]', 'regex': f'{venue_id}/.*|everyone'
                    }
                }
            }
            invitation.content['comment_readers'] = {
                'value': comment_stage.get_readers(self.venue, '{number}')
            }
            invitation.content['readers_selection'] = {
                'value': comment_stage.reader_selection
            }
            comment_readers = ['${5/content/noteReaders/value}']
            if comment_stage.reader_selection:
                comment_readers = {
                    'param': {
                        'enum': ['${7/content/noteReaders/value}']
                    }
                }
            invitation.edit['invitation']['edit']['note']['readers'] = comment_readers

            invitation.edit['invitation']['invitees'].extend([self.venue.get_ethics_reviewers_id('${3/content/noteNumber/value}'), self.venue.get_ethics_chairs_id()])
            invitation.edit['invitation']['edit']['signatures']['param']['items'].append({ 'prefix': self.venue.get_ethics_reviewers_id('${7/content/noteNumber/value}', anon=True), 'optional': True })
            invitation.edit['invitation']['edit']['signatures']['param']['items'].append({ 'value': self.venue.get_ethics_chairs_id(), 'optional': True })

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
                                'type': 'integer'
                            }
                        }
                    },
                    'noteId': {
                        'value': {
                            'param': {
                                'type': 'string'
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
                        'signatures': {
                            'param': {
                                'items': [{ 'prefix': '~.*' }]
                            }
                        },
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

    def set_chat_invitation(self):
        venue_id = self.venue_id
        comment_stage = self.venue.comment_stage
        chat_invitation = self.venue.get_invitation_id('Chat')
        emoji_chat_invitation = self.venue.get_invitation_id('Chat_Reaction')
        comment_cdate = tools.datetime_millis(comment_stage.start_date if comment_stage.start_date else datetime.datetime.utcnow())
        comment_expdate = tools.datetime_millis(comment_stage.end_date) if comment_stage.end_date else None

        if not comment_stage.enable_chat:
            invitation = tools.get_invitation(self.client, chat_invitation)
            if invitation:
                self.client.post_invitation_edit(
                    invitations=self.venue.get_meta_invitation_id(),
                    signatures = [venue_id],
                    invitation = openreview.api.Invitation(
                        id = chat_invitation,
                        edit = {
                            'invitation': {
                                'expdate': tools.datetime_millis(datetime.datetime.utcnow())
                            }
                        }
                    )
                )

                self.client.post_invitation_edit(
                    invitations=self.venue.get_meta_invitation_id(),
                    signatures = [venue_id],
                    invitation = openreview.api.Invitation(
                        id = self.venue.submission_stage.get_submission_id(self.venue),
                        reply_forum_views = { 'delete': True }
                    )
                )

                self.client.post_invitation_edit(
                    invitations=self.venue.get_meta_invitation_id(),
                    signatures = [venue_id],
                    invitation = openreview.api.Invitation(
                        id = emoji_chat_invitation,
                        edit = {
                            'invitation': {
                                'expdate': tools.datetime_millis(datetime.datetime.utcnow())
                            }
                        }
                    )
                )


            return

        invitation = Invitation(id=chat_invitation,
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
                'chat_process_script': {
                    'value': self.get_process_content('process/chat_comment_process.py')
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
                                'type': 'integer'
                            }
                        }
                    },
                    'noteId': {
                        'value': {
                            'param': {
                                'type': 'string'
                            }
                        }
                    }
                },
                'replacement': False,
                'invitation': {
                    'id': self.venue.get_invitation_id('Chat', '${2/content/noteNumber/value}'),
                    'signatures': [ venue_id ],
                    'readers': ['everyone'],
                    'writers': [venue_id],
                    'invitees': comment_stage.get_chat_invitees(self.venue, number='${3/content/noteNumber/value}'),
                    'cdate': comment_cdate,
                    'dateprocesses':[{
                        'dates': [],
                        'script': self.get_process_content('process/chat_date_comment_process.py')
                    }],
                    'process': '''def process(client, edit, invitation):
    meta_invitation = client.get_invitation(invitation.invitations[0])
    script = meta_invitation.content['chat_process_script']['value']
    funcs = {
        'openreview': openreview
    }
    exec(script, funcs)
    funcs['process'](client, edit, invitation)
''',
                    'edit': {
                        'signatures': {
                            'param': {
                                #'enum': comment_stage.get_chat_signatures(self.venue, '${6/content/noteNumber/value}')
                                'items': [ { 'prefix': s, 'optional': True } if '.*' in s else { 'value': s, 'optional': True } for s in comment_stage.get_chat_signatures(self.venue, '${7/content/noteNumber/value}')]
                            }
                        },
                        'readers': ['${2/note/readers}'],
                        'writers': [venue_id],
                        'note': {
                            'id': {
                                'param': {
                                    'withInvitation': self.venue.get_invitation_id('Chat', '${6/content/noteNumber/value}'),
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
                            'readers': comment_stage.get_chat_readers(self.venue, '${5/content/noteNumber/value}'),
                            'writers': [venue_id, '${3/signatures}'],
                            'content': {
                                'message': {
                                    'value': {
                                        'param': {
                                            'type': 'string',
                                            'maxLength': 1000,
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

        if comment_expdate:
            invitation.edit['invitation']['expdate'] = comment_expdate

        self.save_invitation(invitation, replacement=False)

        self.client.post_invitation_edit(
            invitations=self.venue.get_meta_invitation_id(),
            signatures = [venue_id],
            invitation = openreview.api.Invitation(
                id = self.venue.submission_stage.get_submission_id(self.venue),
                reply_forum_views = [
                    {
                        'id': 'discussion',
                        'label': 'Discussion',
                        'filter': f'-invitations:{venue_id}/{self.venue.submission_stage.name}${{note.number}}/-/Chat',
                        'nesting': 3,
                        'sort': 'date-desc',
                        'layout': 'default',
                        'live': True
                    },
                    {
                        'id': 'committee-chat',
                        'label': 'Committee Members Chat',
                        'filter': f'invitations:{venue_id}/{self.venue.submission_stage.name}${{note.number}}/-/Chat,{venue_id}/{self.venue.submission_stage.name}${{note.number}}/-/{self.venue.review_stage.name}',
                        'nesting': 1,
                        'sort': 'date-asc',
                        'layout': 'chat',
                        'live': True,
                        'expandedInvitations': [f'{venue_id}/{self.venue.submission_stage.name}${{note.number}}/-/Chat']
                    }
                ]
            )
        )

        invitation = Invitation(id=emoji_chat_invitation,
            invitees=[venue_id],
            readers=[venue_id],
            writers=[venue_id],
            signatures=[venue_id],
            cdate=comment_cdate,
            date_processes=[{
                'dates': ["#{4/edit/invitation/cdate}", self.update_date_string],
                'script': self.invitation_edit_process
            }],
            edit={
                'signatures': [venue_id],
                'readers': [venue_id],
                'writers': [venue_id],
                'content': {
                    'noteNumber': {
                        'value': {
                            'param': {
                                'type': 'integer'
                            }
                        }
                    },
                    'noteId': {
                        'value': {
                            'param': {
                                'type': 'string'
                            }
                        }
                    }
                },
                'replacement': True,
                'invitation': {
                    'id': self.venue.get_invitation_id('Chat_Reaction', '${2/content/noteNumber/value}'),
                    'signatures': [ venue_id ],
                    'readers': ['everyone'],
                    'writers': [venue_id],
                    'invitees': comment_stage.get_chat_invitees(self.venue, number='${3/content/noteNumber/value}'),
                    'cdate': comment_cdate,
                    'tag': {
                        'id': {
                            'param': {
                                'withInvitation': self.venue.get_invitation_id('Chat_Reaction', '${5/content/noteNumber/value}'),
                                'optional': True
                            }
                        },
                        'forum': '${3/content/noteId/value}',
                        'replyto': {
                            'param': {
                                'withForum': '${5/content/noteId/value}',
                            }
                        },
                        'ddate': {
                            'param': {
                                'range': [ 0, 9999999999999 ],
                                'optional': True,
                                'deletable': True
                            }
                        },
                        'signatures': {
                            'param': {
                                'items': [ { 'prefix': s, 'optional': True } if '.*' in s else { 'value': s, 'optional': True } for s in comment_stage.get_chat_signatures(self.venue, '${7/content/noteNumber/value}')]
                            }
                        },
                        'readers': comment_stage.get_chat_readers(self.venue, '${4/content/noteNumber/value}'),
                        'writers': [venue_id, '${2/signatures}'],
                        'tag': {
                            'param': {
                                'enum': ['👍', '👎', '👌', '👆', '😄', '😂', '🔥', '🚀', '✅']
                            }
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
                                'type': 'integer'
                            }
                        }
                    },
                    'noteId': {
                        'value': {
                            'param': {
                                'type': 'string'
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
    funcs = {
        'openreview': openreview
    }
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
        if submission_stage.second_due_date:
            expdate = submission_stage.second_due_date_exp_date
        else:
            expdate = submission_stage.exp_date
        cdate = tools.datetime_millis(expdate) if expdate else None
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
                                'type': 'integer'
                            }
                        }
                    },
                    'noteId': {
                        'value': {
                            'param': {
                                'type': 'string'
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
                        'signatures': {
                            'param': {
                                'items': [{ 'value': self.venue.get_authors_id(number='${7/content/noteNumber/value}') }]
                            }
                        },
                        'readers': submission_stage.get_withdrawal_readers(self.venue, '${4/content/noteNumber/value}'),
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
                                            'deletable': True,
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
            'authors': {
                'readers' : [venue_id, self.venue.get_authors_id('${{4/id}/number}')]
            },
            'authorids': {
                'readers' : [venue_id, self.venue.get_authors_id('${{4/id}/number}')]
            },
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
                        'optional': True,
                        'deletable': True
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
                    'content': content,
                    'readers' : submission_stage.get_withdrawal_readers(self.venue, '${{2/id}/number}')
                }
            },
            process=self.get_process_content('process/withdrawn_submission_process.py')
        )

        if submission_stage.withdrawn_submission_public:
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
                                'type': 'string'
                            }
                        }
                    },
                    'withdrawalId': {
                        'value': {
                            'param': {
                                'type': 'string'
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
                        'readers': submission_stage.get_withdrawal_readers(self.venue, '${{4/content/noteId/value}/number}'),
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
                                            'deletable': True,
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
        if submission_stage.second_due_date:
            expdate = submission_stage.second_due_date_exp_date
        else:
            expdate = submission_stage.exp_date
        cdate = tools.datetime_millis(expdate) if expdate else None
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
                                'type': 'integer'
                            }
                        }
                    },
                    'noteId': {
                        'value': {
                            'param': {
                                'type': 'string'
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
            'authors': {
                'readers' : [venue_id, self.venue.get_authors_id('${{4/id}/number}')]
            },
            'authorids': {
                'readers' : [venue_id, self.venue.get_authors_id('${{4/id}/number}')]
            },
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
                        'optional': True,
                        'deletable': True
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
                    'content': content,
                    'readers': submission_stage.get_desk_rejection_readers(self.venue, '${{2/id}/number}')
                }
            },
            process=self.get_process_content('process/desk_rejected_submission_process.py')
        )

        if submission_stage.desk_rejected_submission_public:
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
                                'type': 'string'
                            }
                        }
                    },
                    'deskRejectionId': {
                        'value': {
                            'param': {
                                'type': 'string'
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
        submission_license = self.venue.submission_license
        revision_stage = submission_revision_stage if submission_revision_stage else self.venue.submission_revision_stage
        revision_invitation_id = self.venue.get_invitation_id(revision_stage.name)
        revision_cdate = tools.datetime_millis(revision_stage.start_date if revision_stage.start_date else datetime.datetime.utcnow())
        revision_duedate = tools.datetime_millis(revision_stage.due_date) if revision_stage.due_date else None
        revision_expdate = tools.datetime_millis(revision_stage.due_date + datetime.timedelta(minutes = SHORT_BUFFER_MIN)) if revision_stage.due_date else None

        only_accepted = revision_stage.only_accepted
        content = revision_stage.get_content(api_version='2', conference=self.venue)

        hidden_field_names = self.venue.submission_stage.get_hidden_field_names()
        existing_invitation = tools.get_invitation(self.client, revision_invitation_id)
        invitation_content = existing_invitation.edit.get('invitation', {}).get('edit', {}).get('note', {}).get('content', {}) if existing_invitation and existing_invitation.edit else {}

        for field in content:
            if field in hidden_field_names:
                content[field]['readers'] = [venue_id, self.venue.get_authors_id('${{4/id}/number}')]
                if field in ['authors', 'authorids'] and only_accepted and self.venue.use_publication_chairs:
                    content[field]['readers'].append(self.venue.get_publication_chairs_id())
            if field not in hidden_field_names and invitation_content.get(field, {}).get('readers', []):
                content[field]['readers'] = { 'delete': True }

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
                                'type': 'integer'
                            }
                        }
                    },
                    'noteId': {
                        'value': {
                            'param': {
                                'type': 'string'
                            }
                        }
                    }
                },
                'replacement': True,
                'invitation': {
                    'id': self.venue.get_invitation_id(revision_stage.name, '${2/content/noteNumber/value}'),
                    'signatures': [venue_id],
                    'readers': [venue_id, self.venue.get_authors_id(number='${3/content/noteNumber/value}')],
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
                        },
                        'signatures': {
                            'param': {
                                'items': [
                                    { 'value': self.venue.get_authors_id(number='${7/content/noteNumber/value}'), 'optional': True },
                                    { 'value': self.venue.get_program_chairs_id(), 'optional': True }
                                ]
                            }
                        },
                        'readers': ['${{2/note/id}/readers}'],
                        'writers': [venue_id, self.venue.get_authors_id(number='${4/content/noteNumber/value}')],
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

        # Allow license edition until full paper deadline
        if submission_license and revision_stage.allow_license_edition:
            if isinstance(submission_license, str):
                invitation.edit['invitation']['edit']['note']['license'] = submission_license
            elif len(submission_license) == 1:
                invitation.edit['invitation']['edit']['note']['license'] = submission_license[0]
            else:
                license_options = [ { "value": license, "description": license } for license in submission_license ]
                invitation.edit['invitation']['edit']['note']['license'] = {
                    "param": {
                        "enum": license_options
                    }
                }

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
        custom_stage_reply_type = custom_stage.get_reply_type()
        note_writers = None
        all_signatures = custom_stage.get_signatures(self.venue, '${7/content/noteNumber/value}')

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
                invitees = [venue_id, '${3/content/replytoSignatures/value}']
                noninvitees = []
                note_nonreaders = []
                all_signatures = ['${7/content/replytoSignatures/value}']

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
                                'type': 'integer'
                            }
                        }
                    },
                    'noteId': {
                        'value': {
                            'param': {
                                'type': 'string'
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
                    'process': '''def process(client, edit, invitation):
    meta_invitation = client.get_invitation(invitation.invitations[0])
    script = meta_invitation.content['custom_stage_process_script']['value']
    funcs = {
        'openreview': openreview,
        'datetime': datetime
    }
    exec(script, funcs)
    funcs['process'](client, edit, invitation)
''',
                    'edit': {
                        'signatures': {
                            'param': {
                                'items': [ { 'prefix': s, 'optional': True } if '.*' in s else { 'value': s, 'optional': True } for s in all_signatures]
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

        if reply_to:
            invitation.edit['invitation']['edit']['note']['replyto'] = reply_to

        if custom_stage_replyto in ['reviews', 'metareviews']:
            invitation.edit['content']['replyNumber'] = {
                'value': {
                    'param': {
                        'type': 'integer',
                        'optional': True
                    }
                }
            }
            invitation.edit['content']['replyto'] = {
                'value': {
                    'param': {
                        'type': 'string',
                        'optional': True
                    }
                }
            }

        if custom_stage_reply_type == 'revision':
            invitation.edit['content']['replytoSignatures'] = {
                'value': {
                    'param': {
                        'type': 'string',
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

        self.save_invitation(invitation, replacement=False)
        return invitation

    def set_assignment_invitation(self, committee_id, submission_content=None):

        venue = self.venue
        venue_id = venue.get_id()
        assignment_invitation_id = venue.get_assignment_id(committee_id, deployed=True)
        committee_name = self.venue.get_committee_name(committee_id)
        is_reviewer = committee_name in venue.reviewer_roles
        is_area_chair = committee_name in venue.area_chair_roles
        is_senior_area_chair = committee_name in venue.senior_area_chair_roles
        review_stage = venue.review_stage if is_reviewer else venue.meta_review_stage
        is_ethics_reviewer = committee_id == venue.get_ethics_reviewers_id()

        area_chairs_id = self.venue.get_area_chairs_id()
        senior_area_chairs_id = self.venue.get_senior_area_chairs_id()
        if is_reviewer:
            area_chairs_id = committee_id.replace(self.venue.reviewers_name, self.venue.area_chairs_name)
            senior_area_chairs_id = committee_id.replace(self.venue.reviewers_name, self.venue.senior_area_chairs_name)

        if is_area_chair:
            area_chairs_id = committee_id
            senior_area_chairs_id = committee_id.replace(self.venue.area_chairs_name, self.venue.senior_area_chairs_name)


        content = {
            'review_name': {
                'value': review_stage.name if review_stage else 'Official_Review'
            },
            'reviewers_id': {
                'value': committee_id
            },
            'reviewers_name': {
                'value': venue.reviewers_name if is_reviewer else venue.area_chairs_name
            },
            'reviewers_anon_name': {
                'value': venue.get_anon_reviewers_name() if is_reviewer else venue.get_anon_area_chairs_name()
            }
        }
        if committee_name == venue.area_chairs_name and venue.use_senior_area_chairs and not venue.sac_paper_assignments:
            content['sync_sac_id'] = {
                'value': venue.get_senior_area_chairs_id(number='{number}')
            }
            content['sac_assignment_id'] = {
                'value': venue.get_assignment_id(senior_area_chairs_id, deployed=True) if is_area_chair and venue.use_senior_area_chairs else ''
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
        if submission_content:
            edge_head['param']['withContent'] = submission_content

        if is_reviewer:
            edge_nonreaders = [venue.get_authors_id(number='${{2/head}/number}')]
            if venue.use_senior_area_chairs:
                invitation_readers.append(senior_area_chairs_id)
                edge_invitees.append(senior_area_chairs_id)
                edge_readers.append(venue.get_senior_area_chairs_id(number='${{2/head}/number}'))
                edge_writers.append(venue.get_senior_area_chairs_id(number='${{2/head}/number}'))
                edge_signatures.append(venue.get_senior_area_chairs_id(number='.*'))
            if venue.use_area_chairs:
                invitation_readers.append(area_chairs_id)
                edge_invitees.append(area_chairs_id)
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
            invitation_readers.append(area_chairs_id)
            edge_nonreaders = [venue.get_authors_id(number='${{2/head}/number}')]
            if venue.use_senior_area_chairs:
                invitation_readers.append(senior_area_chairs_id)
                edge_invitees.append(senior_area_chairs_id)
                edge_readers.append(venue.get_senior_area_chairs_id(number='${{2/head}/number}'))
                edge_writers.append(venue.get_senior_area_chairs_id(number='${{2/head}/number}'))
                edge_signatures.append(venue.get_senior_area_chairs_id(number='.*'))


        if is_senior_area_chair and not venue.sac_paper_assignments:
            edge_head = {
                'param': {
                    'type': 'profile',
                    'inGroup': area_chairs_id
                }
            }
            process = self.get_process_content('process/sac_assignment_post_process.py')
            preprocess=None
            content=None
            edge_readers.append('${2/head}')
        elif is_senior_area_chair and venue.sac_paper_assignments:
            invitation_readers.append(senior_area_chairs_id)
            edge_nonreaders = [venue.get_authors_id(number='${{2/head}/number}')]
            content = {
                'reviewers_id': {
                    'value': venue.get_senior_area_chairs_id()
                },
                'reviewers_name': {
                    'value': venue.senior_area_chairs_name
                }
            }

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
            responseArchiveDate = venue.get_edges_archive_date(),
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
                        'options': {
                            'group': committee_id
                        }
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
                responseArchiveDate = self.venue.get_edges_archive_date(),
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
                            'options': {
                                'group': committee_id
                            }
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
                    'signatures': { 'param': { 'items': [ { 'prefix': '~.*' } ] }},
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

        invitation_content = {
            'committee_name': { 'value':  venue.get_committee_name(committee_id, pretty=True) },
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
                                'type': 'integer'
                            }
                        }
                    },
                    'noteId': {
                        'value': {
                            'param': {
                                'type': 'string'
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
                                'type': 'integer'
                            }
                        }
                    },
                    'noteId': {
                        'value': {
                            'param': {
                                'type': 'string'
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
                                'type': 'integer'
                            }
                        }
                    },
                    'noteId': {
                        'value': {
                            'param': {
                                'type': 'string'
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
                                'type': 'integer'
                            }
                        }
                    },
                    'noteId': {
                        'value': {
                            'param': {
                                'type': 'string'
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
        ethics_review_expdate = tools.datetime_millis(ethics_review_stage.exp_date) if ethics_review_stage.exp_date else None
        if not ethics_review_expdate:
            ethics_review_expdate = tools.datetime_millis(ethics_review_stage.due_date + datetime.timedelta(minutes = SHORT_BUFFER_MIN)) if ethics_review_stage.due_date else None

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
                                'type': 'integer'
                            }
                        }
                    },
                    'noteId': {
                        'value': {
                            'param': {
                                'type': 'string'
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
                    'edit': {
                        'signatures': {
                            'param': {
                                'items': [ { 'prefix': s, 'optional': True } if '.*' in s else { 'value': s, 'optional': True } for s in ethics_review_stage.get_signatures(self.venue, '${7/content/noteNumber/value}')]
                            }
                        },
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

        if ethics_review_stage.process_path:
            invitation.content['ethics_review_process_script'] = {
               'value': self.get_process_content(ethics_review_stage.process_path)
            }
            invitation.edit['invitation']['process'] = '''def process(client, edit, invitation):
    meta_invitation = client.get_invitation(invitation.invitations[0])
    script = meta_invitation.content['ethics_review_process_script']['value']
    funcs = {
        'openreview': openreview
    }
    exec(script, funcs)
    funcs['process'](client, edit, invitation)
'''

        if ethics_review_stage.preprocess_path:
            invitation.content['ethics_review_preprocess_script'] = {
                'value': self.get_process_content(ethics_review_stage.preprocess_path)
            }
            invitation.edit['invitation']['preprocess'] = '''def process(client, edit, invitation):
    meta_invitation = client.get_invitation(invitation.invitations[0])
    script = meta_invitation.content['ethics_review_preprocess_script']['value']
    funcs = {
        'openreview': openreview
    }
    exec(script, funcs)
    funcs['process'](client, edit, invitation)
'''

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

        flag_readers = [venue_id, self.venue.get_ethics_chairs_id(), self.venue.get_ethics_reviewers_id('${{4/id}/number}')]
        if self.venue.use_senior_area_chairs:
            flag_readers.append(self.venue.get_senior_area_chairs_id('${{4/id}/number}'))
        if self.venue.use_area_chairs:
            flag_readers.append(self.venue.get_area_chairs_id('${{4/id}/number}'))
        flag_readers.append(self.venue.get_reviewers_id('${{4/id}/number}'))

        ethics_stage_invitation = Invitation(
            id=ethics_stage_id,
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
                        'flagged_for_ethics_review': {
                            'value': {
                                'param': {
                                    'type': 'boolean',
                                    'enum': [True, False],
                                    'input': 'radio'
                                }
                            },
                            'readers': flag_readers
                        },
                        'ethics_comments': {
                            'value': {
                                'param': {
                                    'type': 'string',
                                    'maxLength': 5000,
                                    'markdown': True,
                                    'input': 'textarea',
                                    'optional': True,
                                    'deletable': True
                                }
                            },
                            'readers': [venue_id, self.venue.get_ethics_chairs_id(), self.venue.get_ethics_reviewers_id('${{4/id}/number}')]
                        }
                    }
                }
            }
        )

        if ethics_review_stage.flag_process_path:
            ethics_stage_invitation.process = self.get_process_content(ethics_review_stage.flag_process_path)

        self.save_invitation(ethics_stage_invitation, replacement=False)
        return ethics_stage_invitation

    def set_SAC_ethics_flag_invitation(self, sac_ethics_flag_duedate=None):

        venue_id = self.venue_id
        venue = self.venue
        ethics_review_stage = self.venue.ethics_review_stage
        if ethics_review_stage:
            sac_ethics_flag_name = f'SAC_{ethics_review_stage.name}_Flag'
            sac_ethics_flag_id = f'{venue_id}/-/{sac_ethics_flag_name}'
            cdate = tools.datetime_millis(datetime.datetime.utcnow())

            invitation = Invitation(id=sac_ethics_flag_id,
                invitees=[venue_id],
                readers=[venue_id],
                writers=[venue_id],
                signatures=[venue_id],
                cdate=cdate,
                date_processes=[{
                'dates': ["#{4/edit/invitation/cdate}", self.update_date_string],
                'script': self.invitation_edit_process
                }],
                content={
                    'sac_ethics_flag_script': {
                        'value': self.get_process_content('process/sac_ethics_flag_process.py')
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
                                        'type': 'integer'
                                    }
                                }
                            },
                            'noteId': {
                                'value': {
                                    'param': {
                                        'type': 'string'
                                    }
                                }
                            }
                        },
                        'replacement': True,
                        'invitation': {
                            'id': self.venue.get_invitation_id(sac_ethics_flag_name, '${2/content/noteNumber/value}'),
                            'signatures': [venue_id],
                            'readers': ['everyone'],
                            'writers': [venue_id],
                            'invitees': [venue_id, self.venue.get_senior_area_chairs_id(number='${3/content/noteNumber/value}')],
                            'maxReplies': 1,
                            'cdate': cdate,
                            'process': '''def process(client, edit, invitation):
    meta_invitation = client.get_invitation(invitation.invitations[0])
    script = meta_invitation.content['sac_ethics_flag_script']['value']
    funcs = {
        'openreview': openreview
    }
    exec(script, funcs)
    funcs['process'](client, edit, invitation)
''',
                            'edit': {
                                'signatures': {
                                    'param': {
                                        'items': [
                                            { 'value': venue.get_senior_area_chairs_id(number='${7/content/noteNumber/value}'), 'optional': True },
                                            { 'value': venue.get_program_chairs_id(), 'optional': True }
                                        ]
                                    }
                                },
                                'readers': ['${2/note/readers}'],
                                'nonreaders': ['${2/note/nonreaders}'],
                                'writers': [venue_id],
                                'note': {
                                    'id': {
                                        'param': {
                                            'withInvitation': self.venue.get_invitation_id(sac_ethics_flag_name, '${6/content/noteNumber/value}'),
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
                                    'readers': [venue.get_program_chairs_id(), venue.get_senior_area_chairs_id(number='${5/content/noteNumber/value}')],
                                    'nonreaders': [venue.get_authors_id(number='${5/content/noteNumber/value}')],
                                    'writers': [venue_id, '${3/signatures}'],
                                    'content': {
                                        'ethics_review_flag': {
                                            'value': {
                                                'param': {
                                                    'type': 'string',
                                                    'enum': ['Yes'],
                                                    'input': 'checkbox'
                                                }
                                            }
                                        },
                                        'comments': {
                                            'value': {
                                                'param': {
                                                    'type': 'string',
                                                    'maxLength': 5000,
                                                    'markdown': True,
                                                    'input': 'textarea',
                                                    'optional': True,
                                                    'deletable': True
                                                }
                                            },
                                            'description': 'Optional comment to Program Chairs.'
                                        }
                                    }
                                }
                            }
                        }
                    }
            )

            if sac_ethics_flag_duedate:
                invitation.edit['invitation']['expdate'] = tools.datetime_millis(sac_ethics_flag_duedate)

            self.save_invitation(invitation, replacement=True)

    def set_reviewer_recommendation_invitation(self, start_date, due_date, total_recommendations):

        venue_id = self.venue_id
        venue = self.venue

        recommendation_invitation_id = venue.get_recommendation_id()

        with open(os.path.join(os.path.dirname(__file__), 'webfield/recommendationWebfield.js')) as webfield_reader:
            webfield_content = webfield_reader.read()

        recommendation_invitation = Invitation(
            id=recommendation_invitation_id,
            cdate=tools.datetime_millis(start_date) if start_date else None,
            duedate=tools.datetime_millis(due_date) if due_date else None,
            expdate=tools.datetime_millis(due_date + datetime.timedelta(minutes = SHORT_BUFFER_MIN)) if due_date else None,
            invitees=[venue.get_area_chairs_id()],
            signatures = [venue_id],
            readers = [venue_id, venue.get_area_chairs_id()],
            writers = [venue_id],
            minReplies = total_recommendations,
            web = webfield_content,
            content = {
                'total_recommendations': {
                    'value': total_recommendations
                }
            },
            edge = {
                'id': {
                    'param': {
                        'withInvitation': recommendation_invitation_id,
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
                'readers':  [venue_id, '${2/signatures}', venue.get_senior_area_chairs_id(number='${{2/head}/number}')] if venue.use_senior_area_chairs else [venue_id, '${2/signatures}'],
                'nonreaders': [venue.get_authors_id(number='${{2/head}/number}')],
                'writers': [ venue_id, '${2/signatures}' ],
                'signatures': {
                    'param': {
                        'regex': f'~.*|{venue_id}'
                    }
                },
                'head': {
                    'param': {
                        'type': 'note',
                        'withInvitation': venue.submission_stage.get_submission_id(venue)
                    }
                },
                'tail': {
                    'param': {
                        'type': 'profile',
                        'inGroup': venue.get_reviewers_id()
                    }
                },
                'weight': {
                    'param': {
                        'enum': [1,2,3,4,5,6,7,8,9,10]
                    }
                }
            }
        )

        recommendation_invitation = self.save_invitation(recommendation_invitation, replacement=True)
        
    def set_group_recruitment_invitations(self, committee_name):
        
        venue_id = self.venue_id
        venue = self.venue
        
        invitation = Invitation(id=venue.get_committee_id_invited(committee_name)+'/-/Members',
            invitees=[venue_id],
            readers=[venue_id],
            writers=[venue_id],
            signatures=[venue_id],
            process=self.get_process_content('process/group_recruitment_process.py'),
            content={
                'committee_name': { 'value': committee_name },
                'official_committee_roles': { 'value': venue.get_committee_names()},
                'hash_seed': { 'value': '1234', 'readers': [ venue_id ]},
            },
            edit={
                'signatures': [venue_id],
                'readers': [venue_id],
                'writers': [venue_id],
                'content': {            
                    'inviteeDetails': {
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
                },
                'group': {
                    'id': venue.get_committee_id_invited(committee_name),
                    'content': {
                        'last_recruitment': {
                            'value': '${4/tmdate}'
                        }
                    }
                }
            })
        
        self.save_invitation(invitation, replacement=False)

        pretty_role = committee_name.replace('_', ' ')
        pretty_role = pretty_role[:-1] if pretty_role.endswith('s') else pretty_role

        invitation = Invitation(id=venue.get_committee_id_invited(committee_name)+'/-/Recruitment_Settings',
            invitees=[venue_id],
            readers=[venue_id],
            writers=[venue_id],
            signatures=[venue_id],
            edit={
                'signatures': [venue_id],
                'readers': [venue_id],
                'writers': [venue_id],
                'content': {
                    'reduced_load': {
                        'value': {
                            'param': {
                                'type': 'integer[]',
                                'optional': True
                            }
                        }
                    },
                    'recruitment_subject': {
                        'value': {
                            'param': {
                                'type': 'string',
                                'regex': '.+',
                                'optional': True,
                                'default': f'[{venue.short_name}] Invitation to serve as {pretty_role}'
                            }
                        }
                    },
                    'recruitment_template': {
                        'value': {
                            'param': {
                                'type': 'string',
                                'maxLength': 5000,
                                'input': 'textarea',
                                'optional': True
                            }
                        }
                    },
                    'allow_overlap': {
                        'value': {
                            'param': {
                                'type': 'boolean',
                                'enum': [True, False]
                            }
                        }
                    }
                },
                'group': {
                    'id': venue.get_committee_id_invited(committee_name),
                    'content': {
                        'reduced_load': {
                            'value': '${4/content/reduced_load/value}'
                        },
                        'recruitment_subject': {
                            'value': '${4/content/recruitment_subject/value}'
                        },
                        'recruitment_template': {
                            'value': '${4/content/recruitment_template/value}'
                        },
                        'allow_overlap': {
                            'value': '${4/content/allow_overlap/value}'
                        }
                    }
                }
            })
        
        self.save_invitation(invitation, replacement=False)

    def set_group_matching_setup_invitations(self, committee_id):
        
        venue_id = self.venue_id
        committee_name = openreview.tools.pretty_id(committee_id.split('/')[-1]).lower()
        cdate = tools.datetime_millis(self.venue.submission_stage.exp_date) if self.venue.submission_stage.exp_date else None
        
        invitation = Invitation(id=self.venue.get_matching_setup_id(committee_id),
            invitees=[venue_id],
            readers=[venue_id],
            writers=[venue_id],
            signatures=[venue_id],
            cdate=cdate,
            process=self.get_process_content('process/group_matching_setup_process.py'),
            edit={
                'signatures': [venue_id],
                'readers': [venue_id],
                'writers': [venue_id],
                'group': {
                    'id': committee_id,
                    'content': {
                        'assignment_mode': {
                            'order': 1,
                            'description': f'How do you want to assign {committee_name} to submissions?. Automatic assignment will assign {committee_name} to submissions based on their expertise and/or bids. Manual assignment will allow you to assign reviewers to submissions manually.',
                            'value': {
                                'param': {
                                    'type': 'string',
                                    'enum': ['Automatic', 'Manual']
                                }
                            }
                        },
                        'affinity_score_model': {
                            'order': 2,
                            'description': f'Select the model to use for calculating affinity scores between {committee_name} and submissions or leaving it blank to not compute affinity scores.',
                            'value': {
                                'param': {
                                    'type': 'string',
                                    'optional': True,
                                    'enum': ['specter+mfr', 'specter2', 'scincl', 'specter2+scincl']
                                }
                            }
                        },
                        'affinity_score_upload': {
                            'order': 3,
                            'description': f'If you would like to use your own affinity scores, upload a CSV file containing affinity scores for user-paper pairs (one user-paper pair per line in the format: submission_id, user_id, affinity_score)',
                            'value': {
                                'param': {
                                    'type': 'file',
                                    'optional': True,
                                    'maxSize': 50,
                                    'extensions': ['csv']
                                }
                            }
                        },
                        'conflict_policy': {
                            'order': 4,
                            'description': f'Select the policy to compute conflicts between the submissions and the {committee_name}. Leaving it blank to not compute any conflicts.',
                            'value': {
                                'param': {
                                    'type': 'string',
                                    'optional': True,
                                    'enum': ['Default', 'NeurIPS', 'Authors_Only'] ## TODO: Add the authors only policy
                                }
                            }
                        },
                        'conflict_n_years': {
                            'order': 5,
                            'description': 'If conflict policy was selected, enter the number of the years we should use to get the information from the OpenReview profile in order to detect conflicts. Leave it empty if you want to use all the available information.',
                            'value': {
                                'param': {
                                    'type': 'integer',
                                    'minimum': 1,
                                    'optional': True
                                }
                            }
                        }                    
                    }
                }
            })
        
        self.save_invitation(invitation, replacement=False)


    def set_submission_message_invitation(self):

        venue_id = self.venue_id
        invitation_id = self.venue.get_invitation_id(f'{self.venue.submission_stage.name}_Message', prefix=self.venue.get_reviewers_id())
        cdate=tools.datetime_millis(self.venue.submission_stage.second_due_date_exp_date if self.venue.submission_stage.second_due_date_exp_date else self.venue.submission_stage.exp_date)
        venue_sender = self.venue.get_message_sender()

        committee = [venue_id]
        committee_signatures = [venue_id, self.venue.get_program_chairs_id()]
        if self.venue.use_senior_area_chairs:
            committee.append(self.venue.get_senior_area_chairs_id('${3/content/noteNumber/value}'))
            committee_signatures.append(self.venue.get_senior_area_chairs_id('${4/content/noteNumber/value}'))
        if self.venue.use_area_chairs:
            committee.append(self.venue.get_area_chairs_id('${3/content/noteNumber/value}'))
            committee_signatures.append(self.venue.get_area_chairs_id('${4/content/noteNumber/value}', anon=True))

        invitation = Invitation(id=invitation_id,
            invitees=[venue_id],
            readers=[venue_id],
            writers=[venue_id],
            signatures=[venue_id],                                
            cdate=cdate,
            date_processes=[{
                'dates': ["#{4/edit/invitation/cdate}", self.update_date_string],
                'script': self.invitation_edit_process
            }],
            edit={
                'signatures': [venue_id],
                'readers': [venue_id],
                'writers': [venue_id],
                'content': {    
                    'noteNumber': {
                        'value': {
                            'param': {
                                'type': 'integer'
                            }
                        }
                    },
                    'noteId': {
                        'value': {
                            'param': {
                                'type': 'string'
                            }
                        }
                    }
                },                                                    
                'replacement': True,
                'invitation': {
                    'id': self.venue.get_message_id(number='${2/content/noteNumber/value}'),
                    'signatures': [ venue_id ],
                    'readers': committee,
                    'writers': [venue_id],
                    'invitees': committee,
                    'cdate': cdate,
                    'message': {
                        'replyTo': { 'param': { 'regex': r'~.*|([a-z0-9_\-\.]{2,}@[a-z0-9_\-\.]{2,}\.[a-z]{2,},){0,}([a-z0-9_\-\.]{2,}@[a-z0-9_\-\.]{2,}\.[a-z]{2,})', 'optional': True } },
                        'subject': { 'param': { 'minLength': 1 } },
                        'message': { 'param': { 'minLength': 1 } },
                        'groups': { 'param': { 'inGroup': self.venue.get_reviewers_id('${3/content/noteNumber/value}') } },
                        'parentGroup': { 'param': { 'const': self.venue.get_reviewers_id('${3/content/noteNumber/value}') } },
                        'ignoreGroups': { 'param': { 'regex': r'~.*|([a-z0-9_\-\.]{2,}@[a-z0-9_\-\.]{2,}\.[a-z]{2,},){0,}([a-z0-9_\-\.]{2,}@[a-z0-9_\-\.]{2,}\.[a-z]{2,})', 'optional': True } },
                        'signature': { 'param': { 'enum': committee_signatures } },
                        'fromName': venue_sender['fromName'],
                        'fromEmail': venue_sender['fromEmail']
                    }
                }

            }
        )

        self.save_invitation(invitation, replacement=True)

        if self.venue.use_area_chairs:
            invitation_id = self.venue.get_invitation_id(f'{self.venue.submission_stage.name}_Message', prefix=self.venue.get_area_chairs_id())
            cdate=tools.datetime_millis(self.venue.submission_stage.second_due_date_exp_date if self.venue.submission_stage.second_due_date_exp_date else self.venue.submission_stage.exp_date)
            venue_sender = self.venue.get_message_sender()

            committee = [venue_id]
            committee_signatures = [venue_id, self.venue.get_program_chairs_id()]
            if self.venue.use_senior_area_chairs:
                committee.append(self.venue.get_senior_area_chairs_id('${3/content/noteNumber/value}'))
                committee_signatures.append(self.venue.get_senior_area_chairs_id('${4/content/noteNumber/value}'))

            invitation = Invitation(id=invitation_id,
                invitees=[venue_id],
                readers=[venue_id],
                writers=[venue_id],
                signatures=[venue_id],                                
                cdate=cdate,
                date_processes=[{
                    'dates': ["#{4/edit/invitation/cdate}", self.update_date_string],
                    'script': self.invitation_edit_process
                }],
                edit={
                    'signatures': [venue_id],
                    'readers': [venue_id],
                    'writers': [venue_id],
                    'content': {    
                        'noteNumber': {
                            'value': {
                                'param': {
                                    'type': 'integer'
                                }
                            }
                        },
                        'noteId': {
                            'value': {
                                'param': {
                                    'type': 'string'
                                }
                            }
                        }
                    },                                                    
                    'replacement': True,
                    'invitation': {
                        'id': self.venue.get_message_id(committee_id=self.venue.get_area_chairs_id('${2/content/noteNumber/value}')),
                        'signatures': [ venue_id ],
                        'readers': committee,
                        'writers': [venue_id],
                        'invitees': committee,
                        'cdate': cdate,
                        'message': {
                            'replyTo': { 'param': { 'regex': r'~.*|([a-z0-9_\-\.]{2,}@[a-z0-9_\-\.]{2,}\.[a-z]{2,},){0,}([a-z0-9_\-\.]{2,}@[a-z0-9_\-\.]{2,}\.[a-z]{2,})', 'optional': True } },
                            'subject': { 'param': { 'minLength': 1 } },
                            'message': { 'param': { 'minLength': 1 } },
                            'groups': { 'param': { 'inGroup': self.venue.get_area_chairs_id('${3/content/noteNumber/value}') } },
                            'parentGroup': { 'param': { 'const': self.venue.get_area_chairs_id('${3/content/noteNumber/value}') } },
                            'ignoreGroups': { 'param': { 'regex': r'~.*|([a-z0-9_\-\.]{2,}@[a-z0-9_\-\.]{2,}\.[a-z]{2,},){0,}([a-z0-9_\-\.]{2,}@[a-z0-9_\-\.]{2,}\.[a-z]{2,})', 'optional': True } },
                            'signature': { 'param': { 'enum': committee_signatures } },
                            'fromName': venue_sender['fromName'],
                            'fromEmail': venue_sender['fromEmail']
                        }
                    }

                }
            )

            self.save_invitation(invitation, replacement=True)            

        ## invitation to message all reviewers
        invitation = Invitation(id=self.venue.get_message_id(committee_id=self.venue.get_reviewers_id()),
            readers=[venue_id],
            invitees=[venue_id],
            writers=[venue_id],
            signatures=[venue_id],
            message = {
                'replyTo': { 'param': { 'regex': r'~.*|([a-z0-9_\-\.]{2,}@[a-z0-9_\-\.]{2,}\.[a-z]{2,},){0,}([a-z0-9_\-\.]{2,}@[a-z0-9_\-\.]{2,}\.[a-z]{2,})', 'optional': True } },
                'subject': { 'param': { 'minLength': 1 } },
                'message': { 'param': { 'minLength': 1 } },
                'groups': { 'param': { 'inGroup': self.venue.get_reviewers_id() } },
                'parentGroup': { 'param': { 'const': self.venue.get_reviewers_id() } },
                'ignoreGroups': { 'param': { 'regex': r'~.*|([a-z0-9_\-\.]{2,}@[a-z0-9_\-\.]{2,}\.[a-z]{2,},){0,}([a-z0-9_\-\.]{2,}@[a-z0-9_\-\.]{2,}\.[a-z]{2,})', 'optional': True } },
                'signature': { 'param': { 'enum': [venue_id, self.venue.get_program_chairs_id()] } },
                'fromName': venue_sender['fromName'],
                'fromEmail': venue_sender['fromEmail']
            }
        )

        self.save_invitation(invitation, replacement=True)

        if self.venue.use_area_chairs:
            invitation = Invitation(id=self.venue.get_message_id(committee_id=self.venue.get_area_chairs_id()),
                readers=[venue_id] + ([self.venue.get_senior_area_chairs_id()] if self.venue.use_senior_area_chairs else []),
                invitees=[venue_id] + ([self.venue.get_senior_area_chairs_id()] if self.venue.use_senior_area_chairs else []),
                writers=[venue_id],
                signatures=[venue_id],
                message = {
                    'replyTo': { 'param': { 'regex': r'~.*|([a-z0-9_\-\.]{2,}@[a-z0-9_\-\.]{2,}\.[a-z]{2,},){0,}([a-z0-9_\-\.]{2,}@[a-z0-9_\-\.]{2,}\.[a-z]{2,})', 'optional': True } },
                    'subject': { 'param': { 'minLength': 1 } },
                    'message': { 'param': { 'minLength': 1 } },
                    'groups': { 'param': { 'inGroup': self.venue.get_area_chairs_id() } },
                    'parentGroup': { 'param': { 'const': self.venue.get_area_chairs_id() } },
                    'ignoreGroups': { 'param': { 'regex': r'~.*|([a-z0-9_\-\.]{2,}@[a-z0-9_\-\.]{2,}\.[a-z]{2,},){0,}([a-z0-9_\-\.]{2,}@[a-z0-9_\-\.]{2,}\.[a-z]{2,})', 'optional': True } },
                    'signature': { 'param': { 'enum': [venue_id, self.venue.get_program_chairs_id(), '~.*'] } },
                    'fromName': venue_sender['fromName'],
                    'fromEmail': venue_sender['fromEmail']
                }
            )

            self.save_invitation(invitation, replacement=True)

        return invitation
    
    def set_preferred_emails_invitation(self):

        venue_id = self.venue_id

        if not self.venue.preferred_emails_groups:
            return

        if openreview.tools.get_invitation(self.client, self.venue.get_preferred_emails_invitation_id()):
            return

        invitation = Invitation(
            id=self.venue.get_preferred_emails_invitation_id(),
            invitees=[venue_id],
            readers=[venue_id],
            writers=[venue_id],
            signatures=['~Super_User1'], ## it should be the super user to get full email addresses
            minReplies=1,
            maxReplies=1,
            type='Edge',
            edit={
                'id': {
                    'param': {
                        'withInvitation': self.venue.get_preferred_emails_invitation_id(),
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
                'readers': [f'{venue_id}/Preferred_Emails_Readers', '${2/head}'],
                'nonreaders': [],
                'writers': [venue_id, '${2/head}'],
                'signatures': [venue_id],
                'head': {
                    'param': {
                        'type': 'profile'
                    }
                },
                'tail': {
                    'param': {
                        'type': 'group'
                    }
                }
            },
            date_processes=[{
                'dates': ["#{4/cdate} + 3000"],
                'script': self.get_process_content('process/preferred_emails_process.py')
            }, {
                'cron': '0 0 * * *',
                'script': self.get_process_content('process/preferred_emails_process.py')
            }]
        )

        self.save_invitation(invitation)


    def set_iThenticate_plagiarism_check_invitation(self):

        venue_id = self.venue_id

        if not self.venue.iThenticate_plagiarism_check:
            return

        if openreview.tools.get_invitation(self.client, self.venue.get_iThenticate_plagiarism_check_invitation_id()):
            return
        
        paper_number = '${{2/head}/number}'
        edge_readers = [venue_id]
        
        for committee_name in self.venue.iThenticate_plagiarism_check_committee_readers:
            edge_readers.append(self.venue.get_committee_id(committee_name, number=paper_number))

        invitation = Invitation(
            id=self.venue.get_iThenticate_plagiarism_check_invitation_id(),
            invitees=[venue_id],
            readers=[venue_id],
            writers=[venue_id],
            signatures=[venue_id],
            minReplies=1,
            maxReplies=1,
            type='Edge',
            edit={
                'id': {
                    'param': {
                        'withInvitation': self.venue.get_iThenticate_plagiarism_check_invitation_id(),
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
                'readers': edge_readers,
                'nonreaders': [self.venue.get_authors_id(number=paper_number)],
                'writers': [venue_id],
                'signatures': [venue_id],
                'head': {
                    'param': {
                        'type': 'note',
                        'withInvitation': self.venue.get_submission_id()
                    }
                },
                'tail': {
                    'param': {
                        'type': 'string'
                    }
                },
                'weight': {
                    'param': {
                        'minimum': -1,
                        'maximum': 100,
                        'default': -1
                    }
                },
                'label': {
                    'param': {
                        'enum': [
                            {'prefix': 'Error'},
                            {'value': 'File Sent'},
                            {'value': 'File Uploaded'},
                            {'value': 'Similarity Requested'},
                            {'value': 'Similarity Complete'},
                            {'value': 'Created'},
                            {'value': 'Processing'},
                        ],
                        'default': "Created",
                    }
                },
            }
        )

        self.save_invitation(invitation)           

