import os
import openreview

class ProfileManagement():

    def __init__(self, client, super_user):

        self.client = client
        self.super_user = super_user
        self.support_group_id = f'{self.super_user}/Support'
        self.author_rename_invitation_id = f'{self.support_group_id}/-/Author_Rename'


    def setup(self):
        self.set_remove_name_invitations()
        self.set_archive_invitations()

    def set_remove_name_invitations(self):

        content = {
            'name': {
                'order': 1,
                'description': 'Name that want to be removed.',
                'value-regex': '.*',
                'required': True                
            },
            'usernames': {
                'order': 2,
                'description': 'Usernames that want to be removed.',
                'values-regex': '~.*',
                'required': True
            },
            'comment': {
                'order': 3,
                'value-regex': '[\\S\\s]{1,5000}',
                'description': 'Reason why you want to delete your name.',
                'required': False
            },
            'status': {
                'order': 4,
                'value-dropdown': ['Pending', 'Accepted', 'Rejected'],
                'description': 'Request status.',
                'required': True
            }
        }

        with open(os.path.join(os.path.dirname(__file__), 'process/request_remove_name_process.py'), 'r') as f:
            file_content = f.read()
            with open(os.path.join(os.path.dirname(__file__), 'process/request_remove_name_pre_process.py'), 'r') as pre:
                pre_file_content = pre.read()
                self.client.post_invitation(openreview.Invitation(
                    id=f'{self.support_group_id}/-/Profile_Name_Removal',
                    readers=['everyone'],
                    writers=[self.support_group_id],
                    signatures=[self.support_group_id],
                    invitees=['~'],
                    process_string=file_content,
                    preprocess=pre_file_content,
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
            file_content = file_content.replace("SUPPORT_USER_ID = ''", "SUPPORT_USER_ID = '" + self.support_group_id + "'")
            file_content = file_content.replace("AUTHOR_RENAME_INVITATION_ID = ''", "AUTHOR_RENAME_INVITATION_ID = '" + self.author_rename_invitation_id + "'")
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

        self.client.post_invitation(openreview.Invitation(
            id=self.author_rename_invitation_id,
            readers=[self.support_group_id],
            writers=[self.support_group_id],
            signatures=[self.support_group_id],
            invitees=[self.support_group_id],
            reply={
                'readers': {
                    'values-regex': '.*'
                },
                'writers': {
                    'values':[self.support_group_id],
                },
                'signatures': {
                    'values': [self.support_group_id]
                },
                'content': {
                    'authors': {
                        'values-regex': '.*'
                    },
                    'authorids': {
                        'values-regex': '.*'
                    }
                }
            }
        ))            

    def set_archive_invitations(self):

        archive_group = openreview.Group(
            id = f'{self.super_user}/Archive',
            readers = ['everyone'],
            writers = [self.support_group_id],
            signatures = [self.super_user],
            signatories = []
        )

        with open(os.path.join(os.path.dirname(__file__), 'webfield/archiveWebfield.js'), 'r') as f:
            file_content = f.read()
            archive_group.web = file_content

            self.client.post_group(archive_group)

        self.client.post_invitation(openreview.Invitation(
            id=f'{archive_group.id}/-/Direct_Upload',
            readers=['~'],
            writers=[self.support_group_id],
            signatures=[self.super_user],
            invitees=['~'],
            reply={
                "readers": {
                    "description": "The users who will be allowed to read the above content.",
                    "values": [
                        "everyone"
                    ]
                },
                "writers": {
                    "values-regex": "~.*"
                },
                "signatures": {
                    "description": "Your authorized identity to be associated with the above content.",
                    "values-regex": "~.*"
                },
                "content": {
                    "title": {
                        "description": "Title of paper.",
                        "order": 0,
                        "value-regex": ".{1,250}",
                        "required": True
                    },
                    "authors": {
                        "description": "Comma separated list of author names.",
                        "order": 1,
                        "values-regex": "[^;,\\n]+(,[^,\\n]+)*",
                        "required": True,
                        "hidden": True
                    },
                    "authorids": {
                        "description": "Search author profile by first, middle and last name or email address. If the profile is not found, you can add the author by completing first, middle, and last names as well as author email address.",
                        "order": 2,
                        "values-regex": "~.*|([a-z0-9_\\-\\.]{1,}@[a-z0-9_\\-\\.]{2,}\\.[a-z]{2,},){0,}([a-z0-9_\\-\\.]{1,}@[a-z0-9_\\-\\.]{2,}\\.[a-z]{2,})",
                        "required": True
                    },
                    "abstract": {
                        "value-regex": "[\\S\\s]{1,5000}",
                        "required": True,
                        "description": "Abstract of paper.",
                        "order": 3
                    },
                    "pdf": {
                        "description": "Choose one of the following: (1) Upload a PDF file. (2) Enter a URL to a PDF file.",
                        "order": 4,
                        "value-file": {
                            "fileTypes": [
                                "pdf"
                            ],
                            "size": 5,
                            "regex": "https?://.+"
                        },
                        "required": False
                    },
                    "html": {
                        "required": False,
                        "value-regex": "upload|(http|https):\\/\\/.+"
                    }
                }
            }
        ))                       
