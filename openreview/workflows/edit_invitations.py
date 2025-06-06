import os
import time
import datetime
from openreview import tools
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
            now = tools.datetime_millis(datetime.datetime.now())
            self.save_invitation(invitation=Invitation(id=invitation.id,
                    cdate=now if (invitation.cdate and invitation.cdate > now) else None,
                    duedate=now if (invitation.duedate and invitation.duedate > now) else None,
                    expdate=now,
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

    def set_edit_submission_dates_invitation(self, process_file=None, due_date=None):

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

        if due_date:
            invitation.duedate = due_date

        self.save_invitation(invitation, replacement=True)
        return invitation

    def set_edit_submission_content_invitation(self, process_file=None, due_date=None):

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
                        },
                        'description': 'Which license should be applied to each submission? We recommend "CC BY 4.0". If you select multiple licenses, you allow authors to choose their license upon submission.'
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

        if process_file:
            invitation.process = self.get_process_content(process_file)

        if due_date:
            invitation.duedate = due_date

        self.save_invitation(invitation, replacement=False)
        return invitation

    def set_edit_submission_notification_invitation(self, due_date=None):

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

        if due_date:
            invitation.duedate = due_date

        self.save_invitation(invitation, replacement=False)
        return invitation

    def set_edit_submission_readers_invitation(self, invitation_id):

        venue_id = self.venue_id
        submission_name = self.get_content_value('submission_name', 'Submission')
        sub_invitation_id = f'{invitation_id}/Submission_Readers'
        authors_name = self.get_content_value('authors_name', 'Authors')
        reviewers_name = self.get_content_value('reviewers_name', 'Reviewers')

        readers_items = [
            {'value': venue_id, 'optional': False, 'description': 'Program Chairs'}
        ]

        senior_area_chairs_name = self.get_content_value('senior_area_chairs_name')
        if senior_area_chairs_name:
            readers_items.extend([
                {'value': self.get_content_value('senior_area_chairs_id'), 'optional': True, 'description': 'All Senior Area Chairs'},
                {'value': f'{venue_id}/{submission_name}' + '${{2/id}/number}' +f'/{senior_area_chairs_name}', 'optional': True, 'description': 'Assigned Senior Area Chairs'}
            ])

        area_chairs_name = self.get_content_value('area_chairs_name')
        if area_chairs_name:
            readers_items.extend([
                {'value': self.get_content_value('area_chairs_id'), 'optional': True, 'description': 'All Area Chairs'},
                {'value': f'{venue_id}/{submission_name}' + '${{2/id}/number}' +f'/{area_chairs_name}', 'optional': True, 'description': 'Assigned Area Chairs'}
            ])

        readers_items.extend([
                {'value': self.get_content_value('reviewers_id'), 'optional': True, 'description': 'All Reviewers'},
                {'value': f'{venue_id}/{submission_name}' + '${{2/id}/number}' +f'/{reviewers_name}', 'optional': True, 'description': 'Assigned Reviewers'},
                {'value': f'{venue_id}/{submission_name}' + '${{2/id}/number}' +f'/{authors_name}', 'optional': True, 'description': 'Submission Authors'}
            ])

        invitation = Invitation(
            id = sub_invitation_id,
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
                    'id': f'{invitation_id}',
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

    def set_edit_submission_field_readers_invitation(self, invitation_id, due_date=None):

        venue_id = self.venue_id
        sub_invitation_id = f'{invitation_id}/Restrict_Field_Visibility'
        submission_name = self.get_content_value('submission_name', 'Submission')
        authors_name = self.get_content_value('authors_name', 'Authors')
        reviewers_name = self.get_content_value('reviewers_name', 'Reviewers')

        readers_items = [
            {'value': venue_id, 'optional': False, 'description': 'Program Chairs'}
        ]

        senior_area_chairs_name = self.get_content_value('senior_area_chairs_name')
        if senior_area_chairs_name:
            readers_items.extend([
                {'value': self.get_content_value('senior_area_chairs_id'), 'optional': True, 'description': 'All Senior Area Chairs'},
                {'value': f'{venue_id}/{submission_name}' + '${{2/id}/number}' +f'/{senior_area_chairs_name}', 'optional': True, 'description': 'Assigned Senior Area Chairs'}
            ])

        area_chairs_name = self.get_content_value('area_chairs_name')
        if area_chairs_name:
            readers_items.extend([
                {'value': self.get_content_value('area_chairs_id'), 'optional': True, 'description': 'All Area Chairs'},
                {'value': f'{venue_id}/{submission_name}' + '${{2/id}/number}' +f'/{area_chairs_name}', 'optional': True, 'description': 'Assigned Area Chairs'}
            ])

        readers_items.extend([
                {'value': self.get_content_value('reviewers_id'), 'optional': True, 'description': 'All Reviewers'},
                {'value': f'{venue_id}/{submission_name}' + '${{2/id}/number}' +f'/{reviewers_name}', 'optional': True, 'description': 'Assigned Reviewers'},
                {'value': f'{venue_id}/{submission_name}' + '${{2/id}/number}' +f'/{authors_name}', 'optional': False, 'description': 'Submission Authors'}
            ])        

        invitation = Invitation(
            id = sub_invitation_id,
            invitees = [venue_id],
            signatures = [venue_id],
            readers = [venue_id],
            writers = [venue_id],
            edit = {
                'signatures': [venue_id],
                'readers': [venue_id],
                'writers': [venue_id],
                'content' : {
                    'content_readers': {
                        'value': {
                            'param': {
                                'type': 'json'
                            }
                        }
                    },
                    'submission_readers': {
                        'value': {
                            'param': {
                                'type': 'string[]',
                                'input': 'select',
                                'items': readers_items
                            }
                        }
                    }
                },
                'invitation': {
                    'id': invitation_id,
                    'signatures': [venue_id],
                    'edit': {
                        'note': {
                            'readers': ['${5/content/submission_readers/value}'],
                            'content': '${4/content/content_readers/value}'
                        }
                    }
                }
            }
        )

        if due_date:
            invitation.duedate = due_date

        self.save_invitation(invitation, replacement=False)
        return invitation

    def set_edit_dates_invitation(self, super_invitation_id, process_file=None, include_activation_date=True, include_due_date=True, include_expiration_date=True, due_date=None):

        venue_id = self.venue_id
        invitation_id = f'{super_invitation_id}/Dates'

        content = {}
        invitation_body = {}
        if include_activation_date:
            content['activation_date'] = {
                'value': {
                    'param': {
                        'type': 'date',
                        'range': [ 0, 9999999999999 ],
                        'optional': True,
                        'deletable': True
                    }
                }
            }
            invitation_body['cdate'] = '${4/content/activation_date/value}'

        if include_due_date:
            content['due_date'] = {
                'value': {
                    'param': {
                        'type': 'date',
                        'range': [ 0, 9999999999999 ],
                        'optional': True,
                        'deletable': True
                    }
                }
            }
            invitation_body['duedate'] = '${4/content/due_date/value}'

        if include_expiration_date:
            content['expiration_date'] = {
                'value': {
                    'param': {
                        'type': 'date',
                        'range': [ 0, 9999999999999 ],
                        'optional': True,
                        'deletable': True
                    }
                }
            }
            invitation_body['expdate'] = '${4/content/expiration_date/value}'

        if content:
            invitation = Invitation(
                id = invitation_id,
                invitees = [venue_id],
                signatures = [venue_id],
                readers = [venue_id],
                writers = [venue_id],
                edit = {
                    'content': content,
                    'signatures': [self.get_content_value('program_chairs_id', f'{venue_id}/Program_Chairs')],
                    'readers': [venue_id],
                    'writers': [venue_id],
                    'invitation': {
                        'id': super_invitation_id,
                        'signatures': [venue_id],
                        'edit': {
                            'invitation': invitation_body
                        }
                    }
                }
            )

            if include_activation_date:
                invitation.edit['invitation']['cdate'] = '${2/content/activation_date/value}'

            if process_file:
                invitation.process = self.get_process_content(f'{process_file}')

            if due_date:
                invitation.duedate = due_date

            self.save_invitation(invitation, replacement=True)
            return invitation
    
    def set_edit_content_invitation(self, super_invitation_id, content={}, process_file=None, due_date=None):

        venue_id = self.venue_id

        super_invitation = self.client.get_invitation(id=super_invitation_id)

        invitation_id = super_invitation_id + '/Form_Fields'

        edit_content = {
            'note': {
                'content': '${4/content/content/value}'
            }        
        }

        ## TODO: support more than one level of edit
        if super_invitation.edit and 'invitation' in super_invitation.edit:
            edit_content = {
                'invitation': {
                    'edit': {
                        'note': {
                            'content': '${6/content/content/value}'
                        }
                    }
                }                
            }


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
                    'edit': {
                        'note': {
                            'content': '${4/content/content/value}'
                        }
                    },                
                    'signatures': [venue_id],
                    'edit': edit_content
                }
            }  
        )

        if content:
            invitation.edit['content'].update(content)

            invitation_content = {}
            for key in content.keys():
                invitation_content[key] = {
                    'value': '${4/content/' + key + '/value}'
                }

            invitation.edit['invitation']['content'] = invitation_content

        if process_file:
            invitation.process = self.get_process_content(f'{process_file}')

        if due_date:
            invitation.duedate = due_date

        self.save_invitation(invitation, replacement=False)
        return invitation
    
    def set_edit_reply_readers_invitation(self, super_invitation_id, include_signatures=True, due_date=None):

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
                {'value': f'{venue_id}/{submission_name}' + '${5/content/noteNumber/value}' +f'/{senior_area_chairs_name}', 'optional': True, 'description': 'Assigned Senior Area Chairs'}
            ])

        area_chairs_name = self.get_content_value('area_chairs_name')
        if area_chairs_name:
            reply_readers.extend([
                {'value': self.get_content_value('area_chairs_id'), 'optional': True, 'description': 'All Area Chairs'},
                {'value': f'{venue_id}/{submission_name}' + '${5/content/noteNumber/value}' +f'/{area_chairs_name}', 'optional': True, 'description': 'Assigned Area Chairs'}
            ])

        reply_readers.extend([
            {'value': self.get_content_value('reviewers_id'), 'optional': True, 'description': 'All Reviewers'},
            {'value': f'{venue_id}/{submission_name}' + '${5/content/noteNumber/value}' +f'/{reviewers_name}', 'optional': True, 'description': 'Assigned Reviewers'},
            {'value': f'{venue_id}/{submission_name}' + '${5/content/noteNumber/value}' +f'/{reviewers_name}/Submitted', 'optional': True, 'description': 'Assigned Reviewers who already submitted their review'}
        ])

        if include_signatures:
            reply_readers.append({'value': '${3/signatures}', 'optional': True, 'description': 'Reviewer who submitted the review'})

        reply_readers.append({'value': f'{venue_id}/{submission_name}' + '${5/content/noteNumber/value}' +f'/{authors_name}', 'optional': True, 'description': 'Submission Authors'})

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

        if due_date:
            invitation.duedate = due_date
        
        self.save_invitation(invitation, replacement=False)
        return invitation

    def set_edit_email_settings_invitation(self, super_invitation_id, email_pcs=False, email_authors=False, email_reviewers=False, due_date=None):

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

        if email_reviewers:
            content['email_reviewers'] = {
                'value': {
                    'param': {
                        'type': 'boolean',
                        'enum': [True, False],
                        'input': 'radio'
                    }
                }
            }
            note_content['email_reviewers'] = {
                'value': '${4/content/email_reviewers/value}'
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

            if due_date:
                invitation.duedate = due_date

            self.save_invitation(invitation, replacement=False)
            return invitation

    def set_edit_participants_readers_selection_invitation(self, super_invitation_id):

        venue_id = self.venue_id
        invitation_id = super_invitation_id + '/Writers_and_Readers'
        submission_name = self.get_content_value('submission_name', 'Submission')
        program_chairs_id = self.get_content_value('program_chairs_id', f'{venue_id}/Program_Chairs')
        authors_name = self.domain_group.get_content_value('authors_name', 'Authors')
        reviewers_name = self.domain_group.get_content_value('reviewers_name', 'Reviewers')

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
                {'value': {'value': f'{venue_id}/{submission_name}' + '${8/content/noteNumber/value}' +f'/{senior_area_chairs_name}', 'optional': False }, 'optional': True, 'description': 'Assigned Senior Area Chairs'}
            ])
            participants.append(
                {'value': f'{venue_id}/{submission_name}' + '${3/content/noteNumber/value}' +f'/{senior_area_chairs_name}', 'optional': True, 'description': 'Assigned Senior Area Chairs'}
            )

        area_chairs_name = self.get_content_value('area_chairs_name')
        if area_chairs_name:
            reply_readers.extend([
                {'value': {'value': self.get_content_value('area_chairs_id'), 'optional': True }, 'optional': True, 'description': 'All Area Chairs'},
                {'value': {'value': f'{venue_id}/{submission_name}' + '${8/content/noteNumber/value}' +f'/{area_chairs_name}', 'optional': True }, 'optional': True, 'description': 'Assigned Area Chairs'}
            ])
            participants.append(
                {'value': f'{venue_id}/{submission_name}' + '${3/content/noteNumber/value}' +f'/{area_chairs_name}', 'optional': True, 'description': 'Assigned Area Chairs'}
            )

        reply_readers.extend([
            {'value': {'value': self.get_content_value('reviewers_id'), 'optional': True }, 'optional': True, 'description': 'All Reviewers'},
            {'value': {'value': f'{venue_id}/{submission_name}' + '${8/content/noteNumber/value}' +f'/{reviewers_name}', 'optional': True }, 'optional': True, 'description': 'Assigned Reviewers'},
            {'value': {'value': f'{venue_id}/{submission_name}' + '${8/content/noteNumber/value}' +f'/{reviewers_name}/Submitted', 'optional': True }, 'optional': True, 'description': 'Assigned Reviewers who already submitted their review'},
            {'value': {'inGroup': f'{venue_id}/{submission_name}' + '${8/content/noteNumber/value}' +f'/{reviewers_name}', 'optional': True }, 'optional': True, 'description': 'Individual Assigned Reviewers'},
            {'value': {'value': f'{venue_id}/{submission_name}' + '${8/content/noteNumber/value}' +f'/{authors_name}', 'optional': True }, 'optional': True, 'description': 'Submission Authors'}
        ])
        participants.extend([
            {'value': f'{venue_id}/{submission_name}' + '${3/content/noteNumber/value}' +f'/{reviewers_name}', 'optional': True, 'description': 'Assigned Reviewers'},
            {'value': f'{venue_id}/{submission_name}' + '${3/content/noteNumber/value}' +f'/{reviewers_name}/Submitted', 'optional': True, 'description': 'Assigned Reviewers who already submitted their review'},
            {'value': f'{venue_id}/{submission_name}' + '${3/content/noteNumber/value}' +f'/{authors_name}', 'optional': True, 'description': 'Submission Authors'}
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

    def set_edit_dates_one_level_invitation(self, super_invitation_id, include_due_date=False, include_exp_date=False, due_date=None):

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
                    }
                },
                'signatures': [self.get_content_value('program_chairs_id', f'{venue_id}/Program_Chairs')],
                'readers': [venue_id],
                'writers': [venue_id],
                'invitation': {
                    'id': super_invitation_id,
                    'signatures': [venue_id],
                    'cdate': '${2/content/activation_date/value}'
                }
            }
        )

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
            invitation.edit['invitation']['duedate'] = '${2/content/due_date/value}'
            if not include_exp_date:
                invitation.edit['invitation']['expdate'] = '${2/content/due_date/value}+1800000'

        if include_exp_date:
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
            invitation.edit['invitation']['expdate'] = '${2/content/expiration_date/value}'

        if due_date:
            invitation.duedate = due_date

        self.save_invitation(invitation, replacement=True)
        return invitation

    def set_edit_readers_one_level_invitation(self, super_invitation_id):

        venue_id = self.venue_id
        invitation_id = super_invitation_id + '/Readers'
        submission_name = self.get_content_value('submission_name', 'Submission')
        authors_name = self.get_content_value('authors_name', 'Authors')
        reviewers_name = self.get_content_value('reviewers_name', 'Reviewers')

        readers_items = [
            {'value': f'{venue_id}/Program_Chairs', 'optional': False, 'description': 'Program Chairs'}
        ]

        senior_area_chairs_name = self.get_content_value('senior_area_chairs_name')
        if senior_area_chairs_name:
            readers_items.extend([
                {'value': self.get_content_value('senior_area_chairs_id'), 'optional': True, 'description': 'All Senior Area Chairs'},
                {'value': f'{venue_id}/{submission_name}' + '${{2/id}/number}' +f'/{senior_area_chairs_name}', 'optional': True, 'description': 'Assigned Senior Area Chairs'}
            ])

        area_chairs_name = self.get_content_value('area_chairs_name')
        if area_chairs_name:
            readers_items.extend([
                {'value': self.get_content_value('area_chairs_id'), 'optional': True, 'description': 'All Area Chairs'},
                {'value': f'{venue_id}/{submission_name}' + '${{2/id}/number}' +f'/{area_chairs_name}', 'optional': True, 'description': 'Assigned Area Chairs'}
            ])

        readers_items.extend([
                {'value': self.get_content_value('reviewers_id'), 'optional': True, 'description': 'All Reviewers'},
                {'value': f'{venue_id}/{submission_name}' + '${{2/id}/number}' +f'/{reviewers_name}', 'optional': True, 'description': 'Assigned Reviewers'},
                {'value': f'{venue_id}/{submission_name}' + '${{2/id}/number}' +f'/{authors_name}', 'optional': True, 'description': 'Submission Authors'}
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
                    'id': super_invitation_id,
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
                                'enum' : ['${6/content/labels/value}'],
                                'input': 'radio'
                            }
                        }
                    }
                }
            }
        )

        self.save_invitation(invitation, replacement=True)
        return invitation

    def set_edit_conflict_settings_invitation(self, super_invitation_id):

        venue_id = self.venue_id
        invitation_id = super_invitation_id + '/Policy'

        invitation = Invitation(
            id = invitation_id,
            invitees = [venue_id],
            signatures = [venue_id],
            readers = [venue_id],
            writers = [venue_id],
            process = self.get_process_content('workflow_process/edit_conflict_policy_process.py'),
            edit = {
                'content': {
                    'conflict_policy': {
                        'value': {
                            'param': {
                                    'type': 'string',
                                    'enum': ['Default', 'NeurIPS'] ## TODO: Add the authors only policy
                                }
                        }
                    },
                    'conflict_n_years': {
                        'description': 'Select the number of years to consider for conflicts. If all profile history should be take into account, select 0.',
                        'value': {
                            'param': {
                                'type': 'integer',
                                'minimum': 1,
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
                    'content': {
                        'reviewers_conflict_policy': {
                            'value': '${4/content/conflict_policy/value}'
                        },
                        'reviewers_conflict_n_years': {
                            'value': '${4/content/conflict_n_years/value}'
                        }
                    }
                }
            }
        )

        self.save_invitation(invitation, replacement=True)
        return invitation

    def set_edit_affinities_settings_invitation(self, super_invitation_id):

        venue_id = self.venue_id
        invitation_id = super_invitation_id + '/Model'
        invitation = Invitation(
            id = invitation_id,
            invitees = [venue_id],
            signatures = [venue_id],
            readers = [venue_id],
            writers = [venue_id],
            edit = {
                'content': {
                    'affinity_score_model': {
                        'description': f'Select the model to use for calculating affinity scores between reviewers and submissions.',
                        'value': {
                            'param': {
                                'type': 'string',
                                'optional': True,
                                'enum': ['specter+mfr', 'specter2', 'scincl', 'specter2+scincl']
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
                    'content': {
                        'affinity_score_model': {
                            'value': '${4/content/affinity_score_model/value}'
                        }
                    }
                }
            }
        )

        self.save_invitation(invitation, replacement=True)
        return invitation

    def set_edit_affinities_file_invitation(self, super_invitation_id):

        venue_id = self.venue_id
        invitation_id = super_invitation_id + '/Upload_Scores'
        invitation = Invitation(
            id = invitation_id,
            invitees = [venue_id],
            signatures = [venue_id],
            readers = [venue_id],
            writers = [venue_id],
            edit = {
                'content': {
                    'upload_affinity_scores': {
                        'description': 'If you would like to use your own affinity scores, upload a CSV file containing affinity scores for reviewer-paper pairs (one reviewer-paper pair per line in the format: submission_id, reviewer_id, affinity_score)',
                        'value': {
                            'param': {
                                    'type': 'file',
                                    'maxSize': 50,
                                    'extensions': ['csv'],
                                    'optional':True
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
                    'content': {
                        'upload_affinity_scores': {
                            'value': '${4/content/upload_affinity_scores/value}'
                        }
                    }
                }
            }
        )

        self.save_invitation(invitation, replacement=True)
        return invitation

    def set_edit_decision_options_invitation(self, super_invitation_id):

        venue_id = self.venue_id
        invitation_id = super_invitation_id + '/Decision_Options'
        invitation = Invitation(
            id = invitation_id,
            invitees = [venue_id],
            signatures = [venue_id],
            readers = [venue_id],
            writers = [venue_id],
            process = self.get_process_content('workflow_process/edit_decision_options_process.py'),
            edit = {
                'content': {
                    'decision_options': {
                        'description': 'List all decision options. Provide comma separated values, e.g. "Accept (Best Paper), Invite to Archive, Reject". Default options are: "Accept (Oral)", "Accept (Poster)", "Reject"',
                        'value': {
                            'param': {
                                'type': 'string[]',
                                'regex': '.+',
                            }
                        }
                    },
                    'accept_decision_options': {
                        'description': 'List all decision options that signify acceptance. Provide comma separated values, e.g. "Accept (Best Paper), Invite to Archive"',
                        'value': {
                            'param': {
                                'type': 'string[]',
                                'regex': '.+',
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
                    'content': {
                        'accept_decision_options': {
                            'value': '${4/content/accept_decision_options/value}'
                        }
                    },
                    'edit': {
                        'invitation': {
                            'edit':{
                                'note': {
                                    'content': {
                                        'decision': {
                                            'value': {
                                                'param': {
                                                    'type': 'string',
                                                    'enum': ['${11/content/decision_options/value}'],
                                                    'input': 'radio'
                                                }
                                            }
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
        return invitation

    def set_edit_decisions_file_invitation(self, super_invitation_id):

        venue_id = self.venue_id
        invitation_id = super_invitation_id + '/Decision_CSV'
        invitation = Invitation(
            id = invitation_id,
            invitees = [venue_id],
            signatures = [venue_id],
            readers = [venue_id],
            writers = [venue_id],
            process = self.get_process_content('process/edit_upload_date_process.py'),
            edit = {
                'content': {
                    'upload_date': {
                        'value': {
                            'param': {
                                'type': 'date',
                                'range': [ 0, 9999999999999 ]
                            }
                        }
                    },
                    'decision_CSV': {
                        'description': 'Upload a CSV file containing decisions for papers (one decision per line in the format: paper_number, decision, comment). Please do not add the column names as the first row',
                        'value': {
                            'param': {
                                'type': 'file',
                                'maxSize': 50,
                                'extensions': ['csv']
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
                    'content': {
                        'upload_date': {
                            'value': '${4/content/upload_date/value}'
                        },
                        'decision_CSV': {
                            'value': '${4/content/decision_CSV/value}'
                        }
                    }
                }
            }
        )

        self.save_invitation(invitation, replacement=True)
        return invitation

    def set_edit_assignment_match_settings_invitation(self, super_invitation_id):

        venue_id = self.venue_id
        invitation_id = super_invitation_id + '/Match'

        invitation = Invitation(
            id = invitation_id,
            invitees = [venue_id],
            signatures = [venue_id],
            readers = [venue_id],
            writers = [venue_id],
            preprocess = self.get_process_content('process/deploy_assignments_preprocess.py'),
            process = self.get_process_content('process/edit_deploy_date_process.py'),
            edit = {
                'content': {
                    'deploy_date': {
                        'value': {
                            'param': {
                                'type': 'date',
                                'range': [ 0, 9999999999999 ]
                            }
                        }
                    },
                    'match_name': {
                        'value': {
                            'param': {
                                    'type': 'string',
                                    'regex': '.*'
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
                    'content': {
                        'deploy_date': {
                            'value': '${4/content/deploy_date/value}'
                        },
                        'match_name': {
                            'value': '${4/content/match_name/value}'
                        }
                    }
                }
            }
        )

        self.save_invitation(invitation, replacement=True)
        return invitation

    def set_edit_group_deanonymizers_invitation(self, super_invitation_id):

        venue_id = self.venue_id
        invitation_id = super_invitation_id+ '/Deanonymizers'
        submission_name = self.get_content_value('submission_name', 'Submission')
        program_chairs_id = self.get_content_value('program_chairs_id', f'{venue_id}/Program_Chairs')
        reviewers_name = self.domain_group.get_content_value('reviewers_name', 'Reviewers')

        deanonymizers = [
            {'value': venue_id, 'optional': False, 'description': 'Program Chairs'}
        ]

        senior_area_chairs_name = self.get_content_value('senior_area_chairs_name')
        if senior_area_chairs_name:
            deanonymizers.extend([
                {'value': f'{venue_id}/{senior_area_chairs_name}', 'optional': True, 'description': 'All Senior Area Chairs'},
                {'value': f'{venue_id}/{submission_name}' + '${3/content/noteNumber/value}' +f'/{senior_area_chairs_name}', 'optional': True, 'description': 'Assigned Senior Area Chairs'}
            ])

        area_chairs_name = self.get_content_value('area_chairs_name')
        if area_chairs_name:
            deanonymizers.extend([
                {'value': f'{venue_id}/{area_chairs_name}', 'optional': True, 'description': 'All Area Chairs'},
                {'value': f'{venue_id}/{submission_name}' + '${3/content/noteNumber/value}' +f'/{area_chairs_name}', 'optional': True, 'description': 'Assigned Area Chairs'}
            ])

        deanonymizers.extend([
            {'value': f'{venue_id}/{reviewers_name}', 'optional': True, 'description': 'All Reviewers'},
            {'value': f'{venue_id}/{submission_name}' + '${3/content/noteNumber/value}' +f'/{reviewers_name}', 'optional': True, 'description': 'Assigned Reviewers'},
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
                'content': {
                    'reviewer_identity_visibility': {
                        'value': {
                            'param': {
                                'type': 'string[]',
                                'input': 'select',
                                'items': deanonymizers
                            }
                        }
                    }
                },
                'invitation': {
                    'id': super_invitation_id,
                    'signatures': [venue_id],
                    'edit': {
                        'group': {
                            'deanonymizers': ['${5/content/reviewer_identity_visibility/value}']
                        }
                    }
                }
            }
        )

        self.save_invitation(invitation, replacement=False)
        return invitation

    def set_edit_email_date_invitation(self, super_invitation_id, due_date=None):

        venue_id = self.venue_id
        invitation_id = super_invitation_id + '/Dates'

        invitation = Invitation(
            id = invitation_id,
            invitees = [venue_id],
            signatures = [venue_id],
            readers = [venue_id],
            writers = [venue_id],
            process = self.get_process_content('workflow_process/email_authors_dates_process.py'),
            edit = {
                'content': {
                    'activation_date': {
                        'value': {
                            'param': {
                                'type': 'date',
                                'range': [ 0, 9999999999999 ]
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
                    'content': {
                        'activation_date': {
                            'value': '${4/content/activation_date/value}'
                        }
                    }
                }
            }
        )

        if due_date:
            invitation.duedate = due_date

        self.save_invitation(invitation, replacement=True)
        return invitation

    def set_edit_email_template_invitation(self, super_invitation_id):

        venue_id = self.venue_id
        invitation_id = super_invitation_id + '/Message'

        invitation = Invitation(
            id = invitation_id,
            invitees = [venue_id],
            signatures = [venue_id],
            readers = [venue_id],
            writers = [venue_id],
            edit = {
                'content': {
                    'email_subject': {
                        'description': 'The subject of the email to be sent to authors.  Make sure not to remove the parenthesized tokens.',
                        'value': {
                            'param': {
                                'type': 'string',
                                'regex': '.+',
                            }
                        }
                    },
                    'email_content': {
                        'description': 'The content of the email to be sent to authors.  Make sure not to remove the parenthesized tokens.',
                        'value': {
                            'param': {
                                'type': 'string',
                                'maxLength': 100000,
                                'input': 'textarea'
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
                    'content': {
                        'subject': {
                            'value': '${4/content/email_subject/value}'
                        },
                        'message': {
                            'value': '${4/content/email_content/value}'
                        }
                    }
                }
            }
        )

        self.save_invitation(invitation, replacement=True)
        return invitation

    def set_edit_fields_email_template_invitation(self, super_invitation_id, due_date=None):

        venue_id = self.venue_id
        invitation_id = super_invitation_id + '/Fields_to_Include'

        invitation = Invitation(
            id = invitation_id,
            invitees = [venue_id],
            signatures = [venue_id],
            readers = [venue_id],
            writers = [venue_id],
            edit = {
                'content': {
                    'fields': {
                        'value': {
                            'param': {
                                    'type': 'string[]',
                                    'enum': ['review', 'rating', 'confidence'] #default review fields
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
                    'content': {
                        'review_fields_to_include': {
                            'value': ['${5/content/fields/value}']
                        }
                    }
                }
            }
        )

        if due_date:
            invitation.duedate = due_date

        self.save_invitation(invitation, replacement=True)
        return invitation

    def set_review_release_reply_readers_invitation(self, super_invitation_id, include_signatures=True, due_date=None):

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
                {'value': f'{venue_id}/{submission_name}' + '${5/content/noteNumber/value}' +f'/{senior_area_chairs_name}', 'optional': True, 'description': 'Assigned Senior Area Chairs'}
            ])

        area_chairs_name = self.get_content_value('area_chairs_name')
        if area_chairs_name:
            reply_readers.extend([
                {'value': self.get_content_value('area_chairs_id'), 'optional': True, 'description': 'All Area Chairs'},
                {'value': f'{venue_id}/{submission_name}' + '${5/content/noteNumber/value}' +f'/{area_chairs_name}', 'optional': True, 'description': 'Assigned Area Chairs'}
            ])

        reply_readers.extend([
            {'value': self.get_content_value('reviewers_id'), 'optional': True, 'description': 'All Reviewers'},
            {'value': f'{venue_id}/{submission_name}' + '${5/content/noteNumber/value}' +f'/{reviewers_name}', 'optional': True, 'description': 'Assigned Reviewers'},
            {'value': f'{venue_id}/{submission_name}' + '${5/content/noteNumber/value}' +f'/{reviewers_name}/Submitted', 'optional': True, 'description': 'Assigned Reviewers who already submitted their review'}
        ])

        if include_signatures:
            reply_readers.append({'value': '${3/signatures}', 'optional': True, 'description': 'Reviewer who submitted the review'})

        reply_readers.append({'value': f'{venue_id}/{submission_name}' + '${5/content/noteNumber/value}' +f'/{authors_name}', 'optional': True, 'description': 'Submission Authors'})

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
                                'invitation': {
                                    'edit': {
                                        'note': {
                                            'readers': ['${9/content/readers/value}']
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        )

        if due_date:
            invitation.duedate = due_date

        self.save_invitation(invitation, replacement=False)
        return invitation

    def set_edit_submission_release_source_invitation(self, super_invitation_id, due_date=None):

        venue_id = self.venue_id
        invitation_id = super_invitation_id + '/Which_Submissions'

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
                    'source_submissions': {
                        'value': {
                            'param': {
                                'type': 'string',
                                'enum': ['accepted_submissions', 'all_submissions']
                            }
                        }
                    }
                },
                'invitation': {
                    'id': super_invitation_id,
                    'signatures': [venue_id],
                    'content': {
                        'source': {
                            'value': '${4/content/source_submissions/value}'
                        }
                    }
                }
            }
        )

        if due_date:
            invitation.duedate = due_date

        self.save_invitation(invitation, replacement=False)
        return invitation