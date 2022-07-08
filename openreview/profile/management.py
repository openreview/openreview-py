import os
import openreview

class ProfileManagement():

    def __init__(self, client, support_group_id, super_user):

        self.client = client
        self.super_user = super_user
        self.support_group_id = support_group_id


    def setup(self):
        self.set_remove_name_invitations()

    def set_remove_name_invitations(self):

        content = {
            'username': {
                'order': 1,
                'description': 'Username that wants to be removed.',
                'value-regex': '~.*',
                'required': True
            },
            'comment': {
                'order': 2,
                'value-regex': '[\\S\\s]{1,5000}',
                'description': 'Reason why you want to delete your name.',
                'required': False
            },
            'status': {
                'order': 3,
                'value': 'Pending',
                'description': 'Request status.',
                'required': True
            }
        }

        with open(os.path.join(os.path.dirname(__file__), 'process/request_remove_name_process.py'), 'r') as f:
            file_content = f.read()
            self.client.post_invitation(openreview.Invitation(
                id=f'{self.support_group_id}/-/Profile_Name_Removal',
                readers=['everyone'],
                writers=[self.support_group_id],
                signatures=[self.support_group_id],
                invitees=['~'],
                process_string=file_content,
                reply={
                    'readers': {
                        'values-copied': [self.support_group_id, '{signatures}']
                    },
                    'writers': {
                        'values':[self.support_group_id],
                    },
                    'signatures': {
                        'values-regex': f'~.*|{self.support_group_id}'
                    },
                    'content': content
                }
            ))        
    

        content = {
            'status': {
                'order': 1,
                'value-dropdown': ['Accepted', 'Rejected'],
                'description': 'Decision status.',
                'required': True
            },
            'support_comment': {
                'order': 2,
                'value-regex': '[\\S\\s]{1,5000}',
                'description': 'Justify the decision.',
                'required': False
            }            
        }

        with open(os.path.join(os.path.dirname(__file__), 'process/request_remove_name_decision_process.py'), 'r') as f:
            file_content = f.read()
            self.client.post_invitation(openreview.Invitation(
                id=f'{self.support_group_id}/-/Profile_Name_Removal_Decision',
                readers=['everyone'],
                writers=[self.support_group_id],
                signatures=[self.super_user],
                invitees=[self.support_group_id],
                process_string=file_content,
                reply={
                    'referentInvitation': f'{self.support_group_id}/-/Profile_Name_Removal',
                    'readers': {
                        'values': [self.support_group_id]
                    },
                    'writers': {
                        'values':[self.support_group_id],
                    },
                    'signatures': {
                        'values': [self.support_group_id]
                    },
                    'content': content
                }
            ))        
