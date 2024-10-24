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

    def set_edit_submission_dates_invitation(self, process_file=None):

        venue_id = self.venue_id
        submission_id = self.get_content_value('submission_id', f'{venue_id}/-/Submission')
        invitation_id = submission_id + '/Dates'

        invitation = Invitation(
            id = invitation_id,
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
                    'due_date': {
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
                    'duedate': '${2/content/due_date/value}',
                    'expdate': '${2/content/due_date/value}+1800000' ## 30 minutes buffer period
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
        invitation_id = submission_id + '/Form_Fields'

        invitation = Invitation(
            id = invitation_id,
            invitees = [venue_id],
            signatures = [venue_id],
            readers = [venue_id],
            writers = [venue_id],
            edit = {
                'signatures': [venue_id],
                'readers': [venue_id],
                'writers': [venue_id],
                'content' :{
                    'content': {
                        'value': {
                            'param': {
                                'type': 'content'
                            }
                        }
                    },
                    'license': {
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
                            'content': '${4/content/content/value}',
                            'license': {
                                'param': {
                                    'enum': ['${7/content/license/value}']
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
        invitation_id = submission_id + '/Notifications'

        invitation = Invitation(
            id = invitation_id,
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
                    'email_program_chairs': {
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
                        'email_program_chairs': {
                            'value': '${4/content/email_program_chairs/value}'
                        }
                    }
                }
            }
        )

        self.save_invitation(invitation, replacement=False)
        return invitation

    def set_edit_submission_readers_invitation(self):

        venue_id = self.venue_id
        submission_name = self.get_content_value('submission_name', 'Submission')
        invitation_id = f'{venue_id}/-/{submission_name}_Change_After_Deadline/Submission_Readers'
        authors_name = self.get_content_value('authors_name', 'Authors')
        reviewers_name = self.get_content_value('reviewers_name', 'Reviewers')

        readers_items = [
            {'value': venue_id, 'optional': False, 'description': 'Program Chairs'}
        ]

        senior_area_chairs_name = self.get_content_value('senior_area_chairs_name')
        if senior_area_chairs_name:
            readers_items.extend([
                {'value': self.get_content_value('senior_area_chairs_id'), 'optional': True, 'description': 'All Senior Area Chairs'},
                {'value': f'{venue_id}/{submission_name}/' + '${{2/id}/number}' +f'/{senior_area_chairs_name}', 'optional': True, 'description': 'Assigned Senior Area Chairs'}
            ])

        area_chairs_name = self.get_content_value('area_chairs_name')
        if area_chairs_name:
            readers_items.extend([
                {'value': self.get_content_value('area_chairs_id'), 'optional': True, 'description': 'All Area Chairs'},
                {'value': f'{venue_id}/{submission_name}/' + '${{2/id}/number}' +f'/{area_chairs_name}', 'optional': True, 'description': 'Assigned Area Chairs'}
            ])

        readers_items.extend([
                {'value': self.get_content_value('reviewers_id'), 'optional': True, 'description': 'All Reviewers'},
                {'value': f'{venue_id}/{submission_name}/' + '${{2/id}/number}' +f'/{reviewers_name}', 'optional': True, 'description': 'Assigned Reviewers'},
                {'value': f'{venue_id}/{submission_name}/' + '${{2/id}/number}' +f'/{authors_name}', 'optional': True, 'description': 'Submission Authors'}
            ])

        invitation = Invitation(
            id = invitation_id,
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
                    'id': f'{venue_id}/-/{submission_name}_Change_After_Deadline',
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

    def set_edit_submission_field_readers_invitation(self):

        venue_id = self.venue_id
        submission_name = self.domain_group.get_content_value('submission_name', 'Submission')
        invitation_id = f'{venue_id}/-/{submission_name}_Change_After_Deadline/Restrict_Field_Visibility'
        authors_name = self.domain_group.get_content_value('authors_name', 'Authors')
        reviewers_name = self.domain_group.get_content_value('reviewers_name', 'Reviewers')

        readers_items = [
            {'value': venue_id, 'optional': False, 'description': 'Program Chairs'}
        ]

        senior_area_chairs_name = self.domain_group.get_content_value('senior_area_chairs_name')
        if senior_area_chairs_name:
            readers_items.extend([
                {'value': self.domain_group.get_content_value('senior_area_chairs_id'), 'optional': True, 'description': 'All Senior Area Chairs'},
                {'value': f'{venue_id}/{submission_name}/' + '${{4/id}/number}' +f'/{senior_area_chairs_name}', 'optional': True, 'description': 'Assigned Senior Area Chairs'}
                ])

        area_chairs_name = self.domain_group.get_content_value('area_chairs_name')
        if area_chairs_name:
            readers_items.extend([
                {'value': self.domain_group.get_content_value('senior_area_chairs_id'), 'optional': True, 'description': 'All Area Chairs'},
                {'value': f'{venue_id}/{submission_name}/' + '${{4/id}/number}' +f'/{area_chairs_name}', 'optional': True, 'description': 'Assigned Area Chairs'}
                ])

        readers_items.extend([
                {'value': self.domain_group.get_content_value('reviewers_id'), 'optional': True, 'description': 'All Reviewers'},
                {'value': f'{venue_id}/{submission_name}/' + '${{4/id}/number}' +f'/{reviewers_name}', 'optional': True, 'description': 'Assigned Reviewers'},
                {'value': f'{venue_id}/{submission_name}/' + '${{4/id}/number}' +f'/{authors_name}', 'optional': True, 'description': 'Submission Authors'}
                ])

        invitation = Invitation(
            id = invitation_id,
            invitees = [venue_id],
            signatures = [venue_id],
            readers = [venue_id],
            writers = [venue_id],
            edit = {
                'signatures': [venue_id],
                'readers': [venue_id],
                'writers': [venue_id],
                'content' :{
                    'author_readers': {
                        'value': {
                            'param': {
                                'type': 'string[]',
                                'input': 'select',
                                'items':  readers_items
                            }
                        }
                    },
                    'pdf_readers': {
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
                    'id': f'{venue_id}/-/{submission_name}_Change_After_Deadline',
                    'signatures': [venue_id],
                    'edit': {
                        'note': {
                            'content': {
                                'authors': {
                                    'readers': ['${7/content/author_readers/value}']
                                },
                                'authorids': {
                                    'readers': ['${7/content/author_readers/value}']
                                },
                                'pdf': {
                                    'readers': ['${7/content/pdf_readers/value}']
                                }
                            }
                        }
                    }
                }
            }
        )

        self.save_invitation(invitation, replacement=False)
        return invitation

    def set_edit_dates_invitation(self, super_invitation_id, process_file=None, include_due_date=True):

        venue_id = self.venue_id
        invitation_id = f'{super_invitation_id}/Dates'
        
        invitation = Invitation(
            id = invitation_id,
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
                    }
                },
                'signatures': [self.get_content_value('program_chairs_id', f'{venue_id}/Program_Chairs')],
                'readers': [venue_id],
                'writers': [venue_id],
                'invitation': {
                    'id': super_invitation_id,
                    'signatures': [venue_id],
                    'cdate': '${2/content/activation_date/value}',
                    'edit': {
                        'invitation': {
                            'cdate': '${4/content/activation_date/value}'
                        }
                    }
                }
            }
        )

        if process_file:
            invitation.process = self.get_process_content(f'process/{process_file}')

        if include_due_date:
            invitation.edit['content']['due_date'] = {
                'value': {
                    'param': {
                        'type': 'date',
                        'range': [ 0, 9999999999999 ],
                        'optional': True,
                        'deletable': True
                    }
                }
            }
            invitation.edit['invitation']['edit']['invitation']['duedate'] = '${4/content/due_date/value}'

        invitation.edit['content']['expiration_date'] = {
            'value': {
                'param': {
                    'type': 'date',
                    'range': [ 0, 9999999999999 ],
                    'optional': True,
                    'deletable': True
                }
            }
        }
        invitation.edit['invitation']['edit']['invitation']['expdate'] = '${4/content/expiration_date/value}'

        self.save_invitation(invitation, replacement=True)
        return invitation
    
    def set_edit_content_invitation(self, super_invitation_id, content={}, process_file=None):

        venue_id = self.venue_id
        invitation_id = super_invitation_id + '/Form_Fields'

        invitation = Invitation(
            id = invitation_id,
            invitees = [venue_id],
            signatures = [venue_id],
            readers = [venue_id],
            writers = [venue_id],
            edit = {
                'signatures': [venue_id],
                'readers': [venue_id],
                'writers': [venue_id],
                'content' :{
                    'content': {
                        'value': {
                            'param': {
                                'type': 'content'
                            }
                        }
                    }
                },
                'invitation': {
                    'id': super_invitation_id,
                    'signatures': [venue_id],
                    'edit': {
                        'invitation': {
                            'edit': {
                                'note': {
                                    'content': '${6/content/content/value}'
                                }
                            }
                        }
                    }
                }
            }  
        )

        if content:
            invitation.edit['content'].update(content)

        if process_file:
            invitation.process = self.get_process_content(f'{process_file}')

        self.save_invitation(invitation, replacement=False)
        return invitation
    
    def set_edit_reply_readers_invitation(self, super_invitation_id):

        venue_id = self.venue_id
        invitation_id = super_invitation_id + '/Readers'
        submission_name = self.get_content_value('submission_name', 'Submission')
        program_chairs_id = self.get_content_value('program_chairs_id', f'{venue_id}/Program_Chairs')
        authors_name = self.domain_group.get_content_value('authors_name', 'Authors')
        reviewers_name = self.domain_group.get_content_value('reviewers_name', 'Reviewers')

        reply_readers = [
            {'value': program_chairs_id, 'optional': False, 'description': 'Program Chairs'}
        ]

        senior_area_chairs_name = self.get_content_value('senior_area_chairs_name')
        if senior_area_chairs_name:
            reply_readers.extend([
                {'value': self.get_content_value('senior_area_chairs_id'), 'optional': True, 'description': 'All Senior Area Chairs'},
                {'value': f'{venue_id}/{submission_name}/' + '${5/content/noteNumber/value}' +f'/{senior_area_chairs_name}', 'optional': True, 'description': 'Assigned Senior Area Chairs'}
            ])

        area_chairs_name = self.get_content_value('area_chairs_name')
        if area_chairs_name:
            reply_readers.extend([
                {'value': self.get_content_value('area_chairs_id'), 'optional': True, 'description': 'All Area Chairs'},
                {'value': f'{venue_id}/{submission_name}/' + '${5/content/noteNumber/value}' +f'/{area_chairs_name}', 'optional': True, 'description': 'Assigned Area Chairs'}
            ])

        reply_readers.extend([
            {'value': self.get_content_value('reviewers_id'), 'optional': True, 'description': 'All Reviewers'},
            {'value': f'{venue_id}/{submission_name}/' + '${5/content/noteNumber/value}' +f'/{reviewers_name}', 'optional': True, 'description': 'Assigned Reviewers'},
            {'value': f'{venue_id}/{submission_name}/' + '${5/content/noteNumber/value}' +f'/{reviewers_name}/Submitted', 'optional': True, 'description': 'Assigned Reviewers who already submitted their review'},
            {'value': '${3/signatures}', 'optional': True, 'description': 'Reviewer who submitted the review'},
            {'value': f'{venue_id}/{submission_name}/' + '${5/content/noteNumber/value}' +f'/{authors_name}', 'optional': True, 'description': 'Submission Authors'}
        ])

        invitation = Invitation(
            id = invitation_id,
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
                                'items': reply_readers
                            }
                        }
                    }
                },
                'invitation': {
                    'id': super_invitation_id,
                    'signatures': [venue_id],
                    'edit': {
                        'invitation': {
                            'edit': {
                                'note': {
                                    'readers': ['${7/content/readers/value}']
                                }
                            }
                        }
                    }
                }
            }  
        )
        
        self.save_invitation(invitation, replacement=False)
        return invitation

    def set_edit_email_settings_invitation(self, super_invitation_id, email_pcs=False, email_authors=False):

        venue_id = self.venue_id
        invitation_id = super_invitation_id + '/Notifications'

        content = {}
        note_content = {}
        if email_pcs:
            content['email_program_chairs'] = {
                'value': {
                    'param': {
                        'type': 'boolean',
                        'enum': [True, False],
                        'input': 'radio'
                    }
                }
            }
            note_content['email_program_chairs'] = {
                'value': '${4/content/email_program_chairs/value}'
            }

        if email_authors:
            content['email_authors'] = {
                'value': {
                    'param': {
                        'type': 'boolean',
                        'enum': [True, False],
                        'input': 'radio'
                    }
                }
            }
            note_content['email_authors'] = {
                'value': '${4/content/email_authors/value}'
            }

        if content:
            invitation = Invitation(
                id = invitation_id,
                invitees = [venue_id],
                signatures = [venue_id],
                readers = [venue_id],
                writers = [venue_id],
                edit = {
                    'signatures': [venue_id],
                    'readers': [venue_id],
                    'writers': [venue_id],
                    'content': content,
                    'invitation': {
                        'id': super_invitation_id,
                        'signatures': [venue_id],
                        'content': note_content
                    }
                }
            )

            self.save_invitation(invitation, replacement=False)
            return invitation

    def set_edit_participants_readers_selection_invitation(self, super_invitation_id):

        venue_id = self.venue_id
        invitation_id = super_invitation_id + '/Writers_and_Readers'
        submission_name = self.get_content_value('submission_name', 'Submission')
        program_chairs_id = self.get_content_value('program_chairs_id', f'{venue_id}/Program_Chairs')
        authors_name = self.domain_group.get_content_value('authors_name', 'Authors')
        reviewers_name = self.domain_group.get_content_value('reviewers_name', 'Reviewers')
        rev_name = reviewers_name[:-1] if reviewers_name.endswith('s') else reviewers_name

        reply_readers = [
            {'value': {'value': program_chairs_id, 'optional': False}, 'optional': False, 'description': 'Program Chairs'}
        ]
        participants = [
            {'value': program_chairs_id, 'optional': False, 'description': 'Program Chairs'}
        ]

        senior_area_chairs_name = self.get_content_value('senior_area_chairs_name')
        if senior_area_chairs_name:
            reply_readers.extend([
                {'value': {'value': self.get_content_value('senior_area_chairs_id'), 'optional': False }, 'optional': True, 'description': 'All Senior Area Chairs'},
                {'value': {'value': f'{venue_id}/{submission_name}/' + '${8/content/noteNumber/value}' +f'/{senior_area_chairs_name}', 'optional': False }, 'optional': True, 'description': 'Assigned Senior Area Chairs'}
            ])
            participants.append(
                {'value': f'{venue_id}/{submission_name}/' + '${3/content/noteNumber/value}' +f'/{senior_area_chairs_name}', 'optional': True, 'description': 'Assigned Senior Area Chairs'}
            )

        area_chairs_name = self.get_content_value('area_chairs_name')
        if area_chairs_name:
            reply_readers.extend([
                {'value': {'value': self.get_content_value('area_chairs_id'), 'optional': True }, 'optional': True, 'description': 'All Area Chairs'},
                {'value': {'value': f'{venue_id}/{submission_name}/' + '${8/content/noteNumber/value}' +f'/{area_chairs_name}', 'optional': True }, 'optional': True, 'description': 'Assigned Area Chairs'}
            ])
            participants.append(
                {'value': f'{venue_id}/{submission_name}/' + '${3/content/noteNumber/value}' +f'/{area_chairs_name}', 'optional': True, 'description': 'Assigned Area Chairs'}
            )

        reply_readers.extend([
            {'value': {'value': self.get_content_value('reviewers_id'), 'optional': True }, 'optional': True, 'description': 'All Reviewers'},
            {'value': {'value': f'{venue_id}/{submission_name}/' + '${8/content/noteNumber/value}' +f'/{reviewers_name}', 'optional': True }, 'optional': True, 'description': 'Assigned Reviewers'},
            {'value': {'value': f'{venue_id}/{submission_name}/' + '${8/content/noteNumber/value}' +f'/{reviewers_name}/Submitted', 'optional': True }, 'optional': True, 'description': 'Assigned Reviewers who already submitted their review'},
            {'value': {'prefix': f'{venue_id}/{submission_name}/' + '${8/content/noteNumber/value}' +f'/{rev_name}_*', 'optional': True }, 'optional': True, 'description': 'Individual Assigned Reviewers'},
            {'value': {'value': f'{venue_id}/{submission_name}/' + '${8/content/noteNumber/value}' +f'/{authors_name}', 'optional': True }, 'optional': True, 'description': 'Submission Authors'}
        ])
        participants.extend([
            {'value': f'{venue_id}/{submission_name}/' + '${3/content/noteNumber/value}' +f'/{reviewers_name}', 'optional': True, 'description': 'Assigned Reviewers'},
            {'value': f'{venue_id}/{submission_name}/' + '${3/content/noteNumber/value}' +f'/{reviewers_name}/Submitted', 'optional': True, 'description': 'Assigned Reviewers who already submitted their review'},
            {'value': f'{venue_id}/{submission_name}/' + '${3/content/noteNumber/value}' +f'/{authors_name}', 'optional': True, 'description': 'Submission Authors'}
        ])

        invitation = Invitation(
            id = invitation_id,
            invitees = [venue_id],
            signatures = [venue_id],
            readers = [venue_id],
            writers = [venue_id],
            edit = {
                'signatures': [venue_id],
                'readers': [venue_id],
                'writers': [venue_id],
                'content' :{
                    'writers': {
                        'order': 1,
                        'description': 'Who should be able to participate in this stage (read and write comments)?',
                        'value': {
                            'param': {
                                'type': 'string[]',
                                'input': 'select',
                                'items':  participants
                            }
                        }
                    },
                    'readers': {
                        'order': 2,
                        'description': 'Who should be able to only read comments?',
                        'value': {
                            'param': {
                                'type': 'object[]',
                                'input': 'select',
                                'items': reply_readers
                            }
                        }
                    }
                },
                'invitation': {
                    'id': super_invitation_id,
                    'signatures': [venue_id],
                    'edit': {
                        'invitation': {
                            'invitees': ['${5/content/writers/value}'],
                            'edit': {
                                'note': {
                                    'readers': {
                                        'param': {
                                            'items': '${8/content/readers/value}'
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        )

        self.save_invitation(invitation, replacement=False)
        return invitation

    def set_edit_dates_one_level_invitation(self, super_invitation_id):

        venue_id = self.venue_id
        invitation_id = super_invitation_id + '/Dates'

        invitation = Invitation(
            id = invitation_id,
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
                    'due_date': {
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
                    'id': super_invitation_id,
                    'signatures': [venue_id],
                    'cdate': '${2/content/activation_date/value}',
                    'duedate': '${2/content/due_date/value}',
                    'expdate': '${2/content/due_date/value}+1800000' ## 30 minutes buffer period
                }
            }
        )

        self.save_invitation(invitation, replacement=True)
        return invitation

    def set_edit_bidding_settings_invitation(self, super_invitation_id):

        venue_id = self.venue_id
        invitation_id = super_invitation_id + '/Settings'

        invitation = Invitation(
            id = invitation_id,
            invitees = [venue_id],
            signatures = [venue_id],
            readers = [venue_id],
            writers = [venue_id],
            edit = {
                'content': {
                    'bid_count': {
                        'value': {
                            'param': {
                                'type': 'integer'
                            }
                        }
                    },
                    'labels': {
                        'value': {
                            'param': {
                                'type': 'string[]',
                                'regex': '.+'
                            }
                        }
                    }
                },
                'signatures': [self.get_content_value('program_chairs_id', f'{venue_id}/Program_Chairs')],
                'readers': [venue_id],
                'writers': [venue_id],
                'invitation': {
                    'id': super_invitation_id,
                    'signatures': [venue_id],
                    'minReplies': '${2/content/bid_count/value}',
                    'edge': {
                        'label': {
                            'param': {
                                'enum' : ['${6/content/labels/value}']
                            }
                        }
                    }
                }
            }
        )

        self.save_invitation(invitation, replacement=True)
        return invitation