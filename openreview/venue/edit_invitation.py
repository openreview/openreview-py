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

    def set_edit_submission_deadlines_invitation(self, invitation_id, process_file=None):

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
                'signatures': [venue.get_program_chairs_id()],
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
    
    def set_edit_deadlines_invitation(self, invitation_id, process_file=None, include_due_date=True):

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
                                'type': 'date',
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
                    'edit': {
                        'invitation': {
                            'cdate': '${4/content/activation_date/value}',
                            'expdate': '${4/content/expiration_date/value}'
                        }
                    }
                }
            }
        )

        if process_file:
            invitation.process = self.get_process_content(f'process/{process_file}')

        if include_due_date:
            invitation.edit['content']['deadline'] = {
                'value': {
                    'param': {
                        'type': 'date',
                        'range': [ 0, 9999999999999 ],
                        'optional': True,
                        'deletable': True
                    }
                }
            }
            invitation.edit['invitation']['edit']['invitation']['duedate'] = '${4/content/deadline/value}'

        self.save_invitation(invitation, replacement=True)
        return invitation    

    def set_edit_submission_content_invitation(self, invitation_id):

        venue_id = self.venue_id
        content_invitation_id = invitation_id + '/Form_Fields'

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
                    'id': invitation_id,
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
    
    def set_edit_content_invitation(self, invitation_id, content={}, process_file=None):

        venue_id = self.venue_id
        content_invitation_id = invitation_id + '/Form_Fields'

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
                    }
                },
                'invitation': {
                    'id': invitation_id,
                    'signatures': [venue_id],
                    'edit': {
                        'invitation': {
                            'edit': {
                                'note': {
                                    'content': '${6/content/note_content/value}'
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
            invitation.process = self.get_process_content(f'process/{process_file}')

        self.save_invitation(invitation, replacement=False)
        return invitation

    def set_edit_submission_notification_invitation(self):

        venue_id = self.venue_id
        venue = self.venue
        notifications_invitation_id = venue.get_submission_id() + '/Notifications'

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
                    'id': venue.get_submission_id(),
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
        venue = self.venue
        post_submission_id = f'{venue_id}/-/Post_{venue.submission_stage.name}'        
        content_invitation_id = post_submission_id + '/Submission_Readers'

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
                    'readers': {
                        'value': {
                            'param': {
                                'type': 'string[]',
                                'input': 'select',
                                'items':  [
                                    {'value': venue_id, 'optional': False, 'description': 'Program Chairs'},
                                    {'value': venue.get_authors_id(), 'optional': True, 'description': 'All Authors'},
                                    {'value': venue.get_reviewers_id(), 'optional': True, 'description': 'All Reviewers'},
                                    {'value': venue.get_area_chairs_id(), 'optional': True, 'description': 'All Area Chairs'},
                                    {'value': venue.get_senior_area_chairs_id(), 'optional': True, 'description': 'All Senior Area Chairs'},
                                    {'value': venue.get_authors_id('${{2/id}/number}'), 'optional': True, 'description': 'Submission Authors'},
                                    {'value': venue.get_reviewers_id('${{2/id}/number}'), 'optional': True, 'description': 'Assigned Reviewers'},
                                    {'value': venue.get_area_chairs_id('${{2/id}/number}'), 'optional': True, 'description': 'Assigned Area Chairs'},
                                    {'value': venue.get_senior_area_chairs_id('${{2/id}/number}'), 'optional': True, 'description': 'Assigned Senior Area Chairs'}
                                ]
                            }
                        }
                    }
                },
                'invitation': {
                    'id': post_submission_id,
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
        venue = self.venue
        post_submission_id = f'{venue_id}/-/Post_{venue.submission_stage.name}'        
        content_invitation_id = post_submission_id + '/Restrict_Field_Visibility'

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
                    'author_readers': {
                        'value': {
                            'param': {
                                'type': 'string[]',
                                'input': 'select',
                                'items':  [
                                    {'value': venue_id, 'optional': False, 'description': 'Program Chairs'},
                                    {'value': venue.get_authors_id(), 'optional': True, 'description': 'All Authors'},
                                    {'value': venue.get_reviewers_id(), 'optional': True, 'description': 'All Reviewers'},
                                    {'value': venue.get_area_chairs_id(), 'optional': True, 'description': 'All Area Chairs'},
                                    {'value': venue.get_senior_area_chairs_id(), 'optional': True, 'description': 'All Senior Area Chairs'},
                                    {'value': venue.get_authors_id('${{4/id}/number}'), 'optional': True, 'description': 'Submission Authors'},
                                    {'value': venue.get_reviewers_id('${{4/id}/number}'), 'optional': True, 'description': 'Assigned Reviewers'},
                                    {'value': venue.get_area_chairs_id('${{4/id}/number}'), 'optional': True, 'description': 'Assigned Area Chairs'},
                                    {'value': venue.get_senior_area_chairs_id('${{4/id}/number}'), 'optional': True, 'description': 'Assigned Senior Area Chairs'},
                                ]
                            }
                        }
                    },
                    'pdf_readers': {
                        'value': {
                            'param': {
                                'type': 'string[]',
                                'input': 'select',
                                'items':  [
                                    {'value': venue_id, 'optional': False, 'description': 'Program Chairs'},
                                    {'value': venue.get_authors_id(), 'optional': True, 'description': 'All Authors'},
                                    {'value': venue.get_reviewers_id(), 'optional': True, 'description': 'All Reviewers'},
                                    {'value': venue.get_area_chairs_id(), 'optional': True, 'description': 'All Area Chairs'},
                                    {'value': venue.get_senior_area_chairs_id(), 'optional': True, 'description': 'All Senior Area Chairs'},
                                    {'value': venue.get_authors_id('${{4/id}/number}'), 'optional': True, 'description': 'Submission Authors'},
                                    {'value': venue.get_reviewers_id('${{4/id}/number}'), 'optional': True, 'description': 'Assigned Reviewers'},
                                    {'value': venue.get_area_chairs_id('${{4/id}/number}'), 'optional': True, 'description': 'Assigned Area Chairs'},
                                    {'value': venue.get_senior_area_chairs_id('${{4/id}/number}'), 'optional': True, 'description': 'Assigned Senior Area Chairs'},
                                ]
                            }
                        }
                    }                    
                },
                'invitation': {
                    'id': post_submission_id,
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

    def set_edit_reply_readers_invitation(self, invitation_id):

        venue_id = self.venue_id
        venue = self.venue
        reply_readers_invitation_id = invitation_id + '/Readers'

        reply_readers = [
            {'value': venue.get_program_chairs_id(), 'optional': False, 'description': 'Program Chairs.'}
        ]
        if venue.use_senior_area_chairs:
            reply_readers.extend([
                {'value': venue.get_senior_area_chairs_id(), 'optional': True, 'description': 'All Senior Area Chairs'},
                {'value': venue.get_senior_area_chairs_id('${5/content/noteNumber/value}'), 'optional': True, 'description': 'Assigned Senior Area Chairs'}
            ])
        if venue.use_area_chairs:
            reply_readers.extend([
                {'value': venue.get_area_chairs_id(), 'optional': True, 'description': 'All Area Chairs'},
                {'value': venue.get_area_chairs_id('${5/content/noteNumber/value}'), 'optional': True, 'description': 'Assigned Area Chairs'}
            ])
        reply_readers.extend([
            {'value': venue.get_reviewers_id(), 'optional': True, 'description': 'All Reviewers'},
            {'value': venue.get_reviewers_id('${5/content/noteNumber/value}'), 'optional': True, 'description': 'Assigned Reviewers'},
            {'value': venue.get_reviewers_id('${5/content/noteNumber/value}', submitted=True), 'optional': True, 'description': 'Assigned Reviewers who already submitted their review'},
            {'value': '${3/signatures}', 'optional': True, 'description': 'Reviewer who submitted the review'},
            {'value': venue.get_authors_id('${5/content/noteNumber/value}'), 'optional': True, 'description': 'Paper authors'}
        ])

        invitation = Invitation(
            id = reply_readers_invitation_id,
            invitees = [venue_id],
            signatures = [venue_id],
            readers = [venue_id],
            writers = [venue_id],
            edit = {
                'signatures': [venue_id],
                'readers': [venue_id],
                'writers': [venue_id],
                'content' :{
                    'reply_readers': {
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
                    'id': invitation_id,
                    'signatures': [venue_id],
                    'edit': {
                        'invitation': {
                            'edit': {
                                'note': {
                                    'readers': ['${7/content/reply_readers/value}']
                                }
                            }
                        }
                    }
                }
            }  
        )
        
        self.save_invitation(invitation, replacement=False)
        return invitation
    
    def set_edit_invitees_and_readers_selection_invitation(self, invitation_id):

        venue_id = self.venue_id
        venue = self.venue
        edit_invitation_id = invitation_id + '/Participants_and_Readers'

        reply_readers = [
            {'value': {'value': venue.get_program_chairs_id(), 'optional': False, 'description': 'Program Chairs.'}, 'optional': False, 'description': 'Program Chairs.'}
        ]
        participants = [
            {'value': venue.get_program_chairs_id(), 'optional': False, 'description': 'Program Chairs.'}
        ]
        if venue.use_senior_area_chairs:
            reply_readers.extend([
                {'value': {'value': venue.get_senior_area_chairs_id(), 'optional': False, 'description': 'All Senior Area Chairs'}, 'optional': True, 'description': 'All Senior Area Chairs'},
                {'value': {'value': venue.get_senior_area_chairs_id('${8/content/noteNumber/value}'), 'optional': False, 'description': 'Assigned Senior Area Chairs'}, 'optional': True, 'description': 'Assigned Senior Area Chairs'}
            ])
            participants.append(
                {'value': venue.get_senior_area_chairs_id('${3/content/noteNumber/value}'), 'optional': True, 'description': 'Assigned Senior Area Chairs'}
            )
        if venue.use_area_chairs:
            reply_readers.extend([
                {'value': {'value': venue.get_area_chairs_id(), 'optional': True, 'description': 'All Area Chairs'}, 'optional': True, 'description': 'All Area Chairs'},
                {'value': {'value': venue.get_area_chairs_id('${8/content/noteNumber/value}'), 'optional': True, 'description': 'Assigned Area Chairs'}, 'optional': True, 'description': 'Assigned Area Chairs'}
            ])
            participants.append(
                {'value': venue.get_area_chairs_id('${3/content/noteNumber/value}'), 'optional': True, 'description': 'Assigned Area Chairs'}
            )
        reply_readers.extend([
            {'value': {'value': venue.get_reviewers_id(), 'optional': True, 'description': 'All Reviewers'}, 'optional': True, 'description': 'All Reviewers'},
            {'value': {'value': venue.get_reviewers_id('${8/content/noteNumber/value}'), 'optional': True, 'description': 'Assigned Reviewers'}, 'optional': True, 'description': 'Assigned Reviewers'},
            {'value': {'value': venue.get_reviewers_id('${8/content/noteNumber/value}', submitted=True), 'optional': True, 'description': 'Assigned Reviewers who already submitted their review'}, 'optional': True, 'description': 'Assigned Reviewers who already submitted their review'},
            {'value': {'value': venue.get_authors_id(), 'optional': True, 'description': 'Paper authors'}, 'optional': True, 'description': 'Paper authors'}
        ])
        participants.extend([
            {'value': venue.get_reviewers_id('${3/content/noteNumber/value}'), 'optional': True, 'description': 'Assigned Reviewers'},
            {'value': venue.get_reviewers_id('${3/content/noteNumber/value}', submitted=True), 'optional': True, 'description': 'Assigned Reviewers who already submitted their review'},
            {'value': venue.get_authors_id('${3/content/noteNumber/value}'), 'optional': True, 'description': 'Paper authors'}
        ])

        invitation = Invitation(
            id = edit_invitation_id,
            invitees = [venue_id],
            signatures = [venue_id],
            readers = [venue_id],
            writers = [venue_id],
            edit = {
                'signatures': [venue_id],
                'readers': [venue_id],
                'writers': [venue_id],
                'content' :{
                    'participants': {
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
                    'reply_readers': {
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
                    'id': invitation_id,
                    'signatures': [venue_id],
                    'edit': {
                        'invitation': {
                            'invitees': ['${5/content/participants/value}'],
                            'edit': {
                                'note': {
                                    'readers': {
                                        'param': {
                                            'items': '${8/content/reply_readers/value}'
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

    def set_edit_recommendation_field(self, invitation_id):

        venue_id = self.venue_id

        invitation = Invitation(
            id = invitation_id + '/Recommendation_Field',
            invitees = [venue_id],
            signatures = [venue_id],
            readers = [venue_id],
            writers = [venue_id],
            edit = {
                'signatures': [venue_id],
                'readers': [venue_id],
                'writers': [venue_id],
                'content': {
                    'recommendation_field_name': {
                        'value': {
                            'param': {
                                'type': 'string',
                                'regex': '.*',
                                'default': 'recommendation'
                            }
                        }
                    }
                },
                'group': {
                    'id': self.venue_id,
                    'content': {
                        'meta_review_recommendation': {
                            'value': '${4/content/recommendation_field_name/value}'
                        }
                    }
                }
            }
        )

        self.save_invitation(invitation, replacement=False)
        return invitation

    def set_edit_comment_notification_invitation(self, invitation_id):

        venue_id = self.venue_id
        venue = self.venue
        invitation_content_invitation_id = invitation_id + '/Notifications'

        invitation = Invitation(
            id = invitation_content_invitation_id,
            invitees = [venue_id],
            signatures = [venue_id],
            readers = [venue_id],
            writers = [venue_id],
            edit = {
                'signatures': [venue_id],
                'readers': [venue_id],
                'writers': [venue_id],
                'content': {
                    'email_pcs': {
                        'value': {
                            'param': {
                                'type': 'boolean',
                                'enum': [True, False],
                                'input': 'radio'
                            }
                        }
                    },
                    'email_sacs': {
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
                    'id': invitation_id,
                    'signatures': [venue_id],
                    'content': {
                        'email_pcs': {
                            'value': '${4/content/email_pcs/value}'
                        },
                        'email_sacs': {
                            'value': '${4/content/email_sacs/value}'
                        }
                    }
                }
            }
        )

        self.save_invitation(invitation, replacement=False)
        return invitation

    def set_edit_stage_invitation(self):

        venue_id = self.venue_id
        venue = self.venue

        invitation = Invitation(
            id = f'{venue_id}/-/Stage',
            invitees = [venue_id],
            signatures = ['~Super_User1'],
            readers = [venue_id],
            writers = [venue_id],
            process = self.get_process_content('configuration/process/stage_process.py'),
            edit = {
                'signatures': [venue_id],
                'readers': [venue_id],
                'writers': [venue_id],
                'content' :{
                    'stage_type': {
                        'order': 1,
                        'description': 'Stage Type, e.g. Official_Comment, Meta_Review, Decision, Submission Revision, Custom Stage',
                        'value': {
                            'param': {
                                'type': 'string',
                                'input': 'select',
                                'enum':  [
                                    {'value': 'Official_Comment', 'description': 'Official Comment'},
                                    {'value': 'Meta_Review', 'description': 'Meta Review'},
                                    {'value': 'Decision', 'description': 'Decision'},
                                    {'value': 'Submission_Revision', 'description': 'Submission Revision'},
                                    {'value': 'Custom', 'description': 'Custom Stage'},
                                ]
                            }
                        }
                    },
                    'stage_name': {
                        'order': 2,
                        'description': 'Stage Name, use underscores to represent spaces',
                        'value': {
                            'param': {
                                'type': 'string',
                                'maxLength': 100,
                                'regex': '^[a-zA-Z0-9_]*$',
                            }
                        }
                    },                    
                    'activation_date': {
                        'order': 3, 
                        'value': {
                            'param': {
                                'type': 'date',
                                'range': [ 0, 9999999999999 ],
                                'optional': True,
                                'deletable': True
                            }
                        }
                    },
                    'expiration_date': {
                        'order': 4, 
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
                'invitation': {
                    'id': f'{venue_id}/-/${{2/content/stage_name/value}}',
                    'signatures': [venue_id],
                }
            }  
        )

        self.save_invitation(invitation, replacement=False)
        return invitation    