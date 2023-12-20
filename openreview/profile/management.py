import os
import openreview

class ProfileManagement():

    def __init__(self, client, super_user):

        baseurl_v2 = 'http://localhost:3001'

        if 'https://devapi' in client.baseurl:
            baseurl_v2 = 'https://devapi2.openreview.net'
        if 'https://api' in client.baseurl:
            baseurl_v2 = 'https://api2.openreview.net'

        self.client = client
        self.client_v2 = openreview.api.OpenReviewClient(baseurl=baseurl_v2, token=client.token)        
        self.super_user = super_user
        self.support_group_id = f'{self.super_user}/Support'
        self.author_rename_invitation_id = f'{self.support_group_id}/-/Author_Rename'


    def setup(self):
        self.set_remove_name_invitations()
        self.set_remove_email_invitations()
        self.set_archive_invitations()
        self.set_merge_profiles_invitations()
        self.set_dblp_invitations()

    def set_dblp_invitations(self):

        dblp_group = openreview.tools.get_group(self.client, 'dblp.org')
        if dblp_group is None:
            self.client.post_group(
                openreview.Group(
                    id = 'dblp.org',
                    readers = ['everyone'],
                    writers = ['dblp.org'],
                    nonreaders = [],
                    signatures = ['~Super_User1'],
                    signatories = ['dblp.org'],
                    members = []
                )
            )

        dblp_upload_group = openreview.tools.get_group(self.client, 'dblp.org/upload')
        if dblp_upload_group is None:
            self.client.post_group(
                openreview.Group(
                    id = 'dblp.org/upload',
                    readers = ['dblp.org/upload'],
                    writers = ['dblp.org'],
                    nonreaders = [],
                    signatures = ['dblp.org'],
                    signatories = ['dblp.org'],
                    members = [
                        self.support_group_id
                    ]
                )
            )            

        content = {
            "dblp": {
                "value-regex": "(.*\\n)+.*"
            }
        }

        self.client.post_invitation(openreview.Invitation(
            id='dblp.org/-/record',
            readers=['everyone'],
            writers=['dblp.org'],
            signatures=['dblp.org'],
            invitees=['~'],
            transform=os.path.join(os.path.dirname(__file__), 'process/dblp_transform.js'),
            reply={
                'readers': {
                    'values': ['everyone']
                },
                'writers': {
                    'values':['dblp.org'],
                },
                'signatures': {
                    'values-regex': "dblp.org|~.*"
                },
                'content': content
            }
        ))

        self.client.post_invitation(openreview.Invitation(
            id='dblp.org/-/author_coreference',
            readers=['everyone'],
            writers=['dblp.org'],
            signatures=['dblp.org'],
            invitees=['~'],
            reply={
                'referentInvitation': 'dblp.org/-/record',
                'readers': {
                    'values': ['everyone']
                },
                'writers': {
                    'values':[],
                },
                'signatures': {
                    'values-regex': "dblp.org|~.*"
                },
                "content": {
                    "authorids": {
                        "values-regex": ".*"
                    },
                    "authors": {
                        "values-regex": ".*",
                        "required": False
                    }
                }
            }
        ))

        self.client.post_invitation(openreview.Invitation(
            id='dblp.org/-/abstract',
            readers=['everyone'],
            writers=['dblp.org'],
            signatures=['dblp.org'],
            invitees=['~'],
            reply={
                'referentInvitation': 'dblp.org/-/record',
                'readers': {
                    'values': ['everyone']
                },
                'writers': {
                    'values':[],
                },
                'signatures': {
                    'values': ["dblp.org"]
                },
                "content": {
                    "abstract": {
                        "value-regex": "[\\S\\s]{1,5000000}"
                    }
                }
            }
        ))

        self.client.post_invitation(openreview.Invitation(
            id='dblp.org/-/pdf',
            readers=['everyone'],
            writers=['dblp.org'],
            signatures=['dblp.org'],
            invitees=['~'],
            reply={
                'referentInvitation': 'dblp.org/-/record',
                'readers': {
                    'values': ['everyone']
                },
                'writers': {
                    'values':[],
                },
                'signatures': {
                    'values': ["dblp.org"]
                },
                "content": {
                    "pdf": {
                        "value-regex": "^https?://.+$"
                    }
                }
            }
        ))                

        ## set API 2 groups and invitations
        dblp_group_id = 'DBLP.org'
        dblp_uploader_group_id = f'{dblp_group_id}/Uploader'

        dblp_group = openreview.tools.get_group(self.client, dblp_group_id)
        if dblp_group is None:
            self.client_v2.post_group_edit(
                invitation = f'{self.super_user}/-/Edit',
                signatures = [self.super_user],
                group = openreview.api.Group(
                    id = dblp_group_id,
                    readers = ['everyone'],
                    writers = [dblp_group_id],
                    nonreaders = [],
                    signatures = ['~Super_User1'],
                    signatories = [dblp_group_id],
                    members = []
                )
            )

        meta_invitation_id = f'{dblp_group_id}/-/Edit'
        self.client_v2.post_invitation_edit(
            invitations = None,
            signatures = [self.super_user],
            invitation = openreview.api.Invitation(
                id=meta_invitation_id,
                invitees=[dblp_uploader_group_id],
                readers=[dblp_group_id, dblp_uploader_group_id],
                signatures=[dblp_group_id],                
                edit=True
            )
        )

        dblp_uploader_group = openreview.tools.get_group(self.client, dblp_uploader_group_id)
        if dblp_uploader_group is None:
            self.client_v2.post_group_edit(
                invitation = meta_invitation_id,
                signatures = [dblp_group_id],
                group = openreview.api.Group(
                    id = dblp_uploader_group_id,
                    readers = [dblp_uploader_group_id],
                    writers = [dblp_group_id],
                    nonreaders = [],
                    signatures = [dblp_group_id],
                    signatories = [dblp_group_id],
                    members = []
                )
            )

        record_invitation_id = f'{dblp_group_id}/-/Record'
        with open(os.path.join(os.path.dirname(__file__), 'process/dblp_record_process.js'), 'r') as f:
            file_content = f.read()

        self.client_v2.post_invitation_edit(
            invitations = meta_invitation_id,
            signatures = [dblp_group_id],
            invitation = openreview.api.Invitation(
                id=record_invitation_id,
                readers=['everyone'],
                writers=[dblp_group_id],
                signatures=[dblp_group_id],
                invitees=['~'],
                process=file_content,
                edit={
                    'readers': ['everyone'],
                    'signatures': { 
                        'param': { 
                            'items': [
                                { 'prefix': '~.*', 'optional': True },
                                { 'value': self.support_group_id, 'optional': True },
                                { 'value': dblp_uploader_group_id, 'optional': True } 
                            ]
                        } 
                    },
                    'writers':  [dblp_uploader_group_id, '${2/signatures}'],
                    'content': {
                        'xml': {
                            'value': {
                                'param': {
                                    'type': 'string'
                                }
                            }
                        }
                    },
                    'note': {
                        'signatures': [ '${3/signatures}' ],
                        'readers': ['everyone'],
                        'writers': [ '~'],
                        'license': 'CC BY-SA 4.0',
                        'content': {
                            'title': {
                                'order': 1,
                                'description': 'Title of paper.',
                                'value': { 
                                    'param': { 
                                        'type': 'string',
                                        'regex': '^.{1,250}$'
                                    }
                                }
                            },
                            'authors': {
                                'order': 2,
                                'value': {
                                    'param': {
                                        'type': 'string[]',
                                        'regex': '[^;,\\n]+(,[^,\\n]+)*'
                                    }
                                }
                            },
                            'authorids': {
                                'order': 2,
                                'value': {
                                    'param': {
                                        'type': 'string[]',
                                        'optional': True
                                    }
                                }
                            },                        
                            'venue': {
                                'order': 3,
                                'description': 'Enter the venue where the paper was published.',
                                'value': {
                                    'param': {
                                        'type': 'string'
                                    }
                                }
                            },
                            'venueid': {
                                'order': 4,
                                'value': {
                                    'param': {
                                        'type': "string",
                                        'const': dblp_group_id,
                                    }
                                }
                            }
                        }
                    }                                        
                }
            )
        )

        author_coreference_invitation_id = f'{dblp_group_id}/-/Author_Coreference'

        with open(os.path.join(os.path.dirname(__file__), 'process/dblp_author_coreference_pre_process.js'), 'r') as f:
            file_content = f.read()

        self.client_v2.post_invitation_edit(
            invitations = meta_invitation_id,
            signatures = [dblp_group_id],
            invitation = openreview.api.Invitation(
                id=author_coreference_invitation_id,
                readers=['everyone'],
                writers=[dblp_group_id],
                signatures=[dblp_group_id],
                invitees=['~'],
                preprocess=file_content,
                edit={
                    'readers': ['everyone'],
                    'signatures': { 
                        'param': { 
                            'items': [
                                { 'prefix': '~.*', 'optional': True },
                                { 'value': self.support_group_id, 'optional': True },
                                { 'value': dblp_uploader_group_id, 'optional': True } 
                            ]
                        } 
                    },
                    'writers':  [dblp_group_id, '${2/signatures}'],
                    'note': {
                        'id': {
                            'param': {
                                'withInvitation': record_invitation_id
                            }
                        },
                        'content': {
                            'authorids': {
                                'order': 2,
                                'value': {
                                    'param': {
                                        'type': 'string[]'
                                    }
                                }
                            }
                        }
                    }                                        
                }
            )
        )

        abstract_invitation_id = f'{dblp_group_id}/-/Abstract'
        
        self.client_v2.post_invitation_edit(
            invitations = meta_invitation_id,
            signatures = [dblp_group_id],
            invitation = openreview.api.Invitation(
                id=abstract_invitation_id,
                readers=['everyone'],
                writers=[dblp_group_id],
                signatures=[dblp_group_id],
                invitees=[dblp_uploader_group_id],
                edit={
                    'readers': ['everyone'],
                    'signatures': [dblp_uploader_group_id],
                    'writers':  [dblp_group_id, dblp_uploader_group_id],
                    'note': {
                        'id': {
                            'param': {
                                'withInvitation': record_invitation_id
                            }
                        },
                        'content': {
                            'abstract': {
                                'order': 1,
                                'value': {
                                    'param': {
                                        'type': 'string'
                                    }
                                }
                            }
                        }
                    }                                        
                }
            )
        )                                          


    def set_remove_name_invitations(self):

        content = {
            'name': {
                'order': 1,
                'description': 'Name that want to be removed.',
                'value': {
                    'param': {
                        'type': 'string',
                        'regex': '.*'
                    }
                }
            },
            'usernames': {
                'order': 2,
                'description': 'Usernames that want to be removed.',
                'value': {
                    'param': {
                        'type': 'string[]',
                        'regex': '~.*'
                    }
                }
            },
            'comment': {
                'order': 3,
                'description': 'Reason why you want to delete your name.',
                'value': {
                    'param': {
                        'type': 'string',
                        'maxLength': 5000,
                        'markdown': True,
                        'input': 'textarea',
                        'optional': True
                    }
                }
            },
            'status': {
                'value': 'Pending'
            }
        }

        with open(os.path.join(os.path.dirname(__file__), 'process/request_remove_name_process.py'), 'r') as f:
            file_content = f.read()
            file_content = file_content.replace("SUPPORT_USER_ID = ''", "SUPPORT_USER_ID = '" + self.support_group_id + "'")
            file_content = file_content.replace("REMOVAL_DECISION_INVITATION_ID = ''", "REMOVAL_DECISION_INVITATION_ID = '" + f'{self.support_group_id}/-/Profile_Name_Removal_Decision' + "'")
                
            with open(os.path.join(os.path.dirname(__file__), 'process/request_remove_name_pre_process.py'), 'r') as pre:
                pre_file_content = pre.read()
                self.client_v2.post_invitation_edit(
                    invitations=f'{self.super_user}/-/Edit',
                    signatures=[self.super_user],
                    invitation=openreview.api.Invitation(                    
                        id=f'{self.support_group_id}/-/Profile_Name_Removal',
                        readers=['everyone'],
                        writers=[self.support_group_id],
                        signatures=[self.super_user],
                        invitees=['~'],
                        process=file_content,
                        preprocess=pre_file_content,
                        edit={
                            'readers': [self.support_group_id],
                            'writers': [self.support_group_id],
                            'signatures': {
                                'param': {
                                    'items': [
                                        { 'prefix': '~.*', 'optional': True },
                                        { 'value': self.support_group_id, 'optional': True } 
                                    ]
                                }
                            },
                            'note': {
                                'readers': [self.support_group_id, '${3/signatures}'],
                                'writers': [self.support_group_id],
                                'signatures': ['${3/signatures}'],
                                'content': content
                            }
                        }
                    )
                )        
    

        content = {
            'status': {
                'order': 1,
                'description': 'Decision status.',
                'value': {
                    'param': {
                        'type': 'string',
                        'enum': ['Accepted', 'Rejected']
                    }
                }
            },
            'support_comment': {
                'order': 2,
                'description': 'Justify the decision.',
                'value': {
                    'param': {
                        'type': 'string',
                        'maxLength': 5000,
                        'markdown': True,
                        'input': 'textarea',
                        'optional': True
                    }
                }
            }            
        }

        with open(os.path.join(os.path.dirname(__file__), 'process/request_remove_name_decision_process.py'), 'r') as f:
            file_content = f.read()
            file_content = file_content.replace("SUPPORT_USER_ID = ''", "SUPPORT_USER_ID = '" + self.support_group_id + "'")
            file_content = file_content.replace("AUTHOR_RENAME_INVITATION_ID = ''", "AUTHOR_RENAME_INVITATION_ID = '" + self.author_rename_invitation_id + "'")

            with open(os.path.join(os.path.dirname(__file__), 'process/request_remove_name_decision_pre_process.py'), 'r') as pre:
                pre_file_content = pre.read()

        self.client_v2.post_invitation_edit(
            invitations=f'{self.super_user}/-/Edit',
            signatures=[self.super_user],
            invitation=openreview.api.Invitation(
                id=f'{self.support_group_id}/-/Profile_Name_Removal_Decision',
                readers=['everyone'],
                writers=[self.support_group_id],
                signatures=[self.super_user],
                invitees=[self.support_group_id],
                process=file_content,
                preprocess=pre_file_content,
                edit={
                    'readers': [self.support_group_id],
                    'writers': [self.support_group_id],
                    'signatures': [self.support_group_id],
                    'note': {
                        'id': {
                            'param': {
                                'withInvitation': f'{self.support_group_id}/-/Profile_Name_Removal'
                            }
                        },
                        'content': content
                    }
                }
            )
        )

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

    def set_remove_email_invitations(self):

        content = {
            'email': {
                'order': 1,
                'description': 'email that want to be removed.',
                'value': {
                    'param': {
                        'type': 'string',
                        'regex': r"^[a-z0-9!#$%&'*+/=?^_`{|}~-]+(?:\.[a-z0-9!#$%&'*+/=?^_`{|}~-]+)*@(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.)+[a-z0-9](?:[a-z0-9-]*[a-z0-9])?$",
                    }
                }
            },
            'profile_id': {
                'order': 2,
                'description': 'profile id where the email associated with.',
                'value': {
                    'param': {
                        'type': 'string',
                        'regex': '^~.*'
                    }
                }
            },
            'comment': {
                'order': 3,
                'description': 'Reason why you want to delete your name.',
                'value': {
                    'param': {
                        'type': 'string',
                        'maxLength': 5000,
                        'markdown': True,
                        'input': 'textarea',
                        'optional': True
                    }
                }
            }
        }

        with open(os.path.join(os.path.dirname(__file__), 'process/request_remove_email_process.py'), 'r') as f:
            file_content = f.read()
            file_content = file_content.replace("SUPPORT_USER_ID = ''", "SUPPORT_USER_ID = '" + self.support_group_id + "'")
            file_content = file_content.replace("AUTHOR_RENAME_INVITATION_ID = ''", "AUTHOR_RENAME_INVITATION_ID = '" + self.author_rename_invitation_id + "'")
            with open(os.path.join(os.path.dirname(__file__), 'process/request_remove_email_pre_process.py'), 'r') as pre:
                pre_file_content = pre.read()
                self.client_v2.post_invitation_edit(
                    invitations=f'{self.super_user}/-/Edit',
                    signatures=[self.super_user],
                    invitation=openreview.api.Invitation(
                        id=f'{self.support_group_id}/-/Profile_Email_Removal',
                        readers=['everyone'],
                        writers=[self.support_group_id],
                        signatures=[self.super_user],
                        invitees=['~'],
                        process=file_content,
                        preprocess=pre_file_content,
                        edit={
                            'readers': [self.support_group_id],
                            'writers': [self.support_group_id],
                            'signatures': [self.support_group_id],
                            'note': {
                                'readers': [self.support_group_id],
                                'writers': [self.support_group_id],
                                'signatures': [self.support_group_id],
                                'content': content
                            }
                        }
                    )
                )

    def set_archive_invitations(self):

        archive_group = openreview.api.Group(
            id = f'{self.super_user}/Archive',
            readers = ['everyone'],
            writers = [self.support_group_id],
            signatures = [self.super_user],
            signatories = []
        )

        with open(os.path.join(os.path.dirname(__file__), 'webfield/archiveWebfield.js'), 'r') as f:
            file_content = f.read()
            archive_group.web = file_content

            self.client_v2.post_group_edit(
                invitation = f'{self.super_user}/-/Edit',
                signatures = [self.super_user],
                group = archive_group)

        self.client_v2.post_invitation_edit(
            invitations = f'{self.super_user}/-/Edit',
            signatures = [self.super_user],
            invitation = openreview.api.Invitation(
                id=f'{archive_group.id}/-/Direct_Upload',
                readers=['~'],
                writers=[self.support_group_id],
                signatures=[self.super_user],
                invitees=['~'],
                edit={
                    'readers': ['everyone'],
                    'signatures': { 
                        'param': { 
                            'items': [
                                { 'prefix': '~.*', 'optional': True },
                                { 'value': self.support_group_id, 'optional': True } 
                            ]
                        } 
                    },
                    'writers':  ['${2/signatures}'],
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
                                'withInvitation': f'{archive_group.id}/-/Direct_Upload',
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
                        'pdate': {
                            'param': {
                                'range': [ 0, 9999999999999 ]
                            }
                        },
                        'signatures': [ '${3/signatures}' ],
                        'readers': ['everyone'],
                        'writers': [ '${2/content/authorids/value}'],
                        'license': 'CC BY-SA 4.0',
                        'content': {
                            'title': {
                                'order': 1,
                                'description': 'Title of paper.',
                                'value': { 
                                    'param': { 
                                        'type': 'string',
                                        'regex': '^.{1,250}$'
                                    }
                                }
                            },
                            'authors': {
                                'order': 2,
                                'value': {
                                    'param': {
                                        'type': 'string[]',
                                        'regex': '[^;,\\n]+(,[^,\\n]+)*',
                                        'hidden': True
                                    }
                                }
                            },
                            'authorids': {
                                'order': 3,
                                'description': 'Search author profile by first, middle and last name or email address. If the profile is not found, you can add the author by completing first, middle, and last names as well as author email address.',
                                'value': {
                                    'param': {
                                        'type': 'group[]',
                                        'regex': r"^~\S+$|^[a-z0-9!#$%&'*+/=?^_`{|}~-]+(?:\.[a-z0-9!#$%&'*+/=?^_`{|}~-]+)*@(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.)+[a-z0-9](?:[a-z0-9-]*[a-z0-9])?$",
                                        'mismatchError': 'must be a valid email or profile ID'
                                    }
                                }
                            },                        
                            'abstract': {
                                'order': 4,
                                'description': 'Abstract of paper. Add TeX formulas using the following formats: $In-line Formula$ or $$Block Formula$$.',
                                'value': {
                                    'param': {
                                        'type': 'string',
                                        'maxLength': 5000,
                                        'markdown': True,
                                        'input': 'textarea'
                                    }
                                }
                            },
                            'pdf': {
                                'order': 5,
                                'description': 'Upload a PDF file that ends with .pdf.',
                                'value': {
                                    'param': {
                                        'type': 'file',
                                        'maxSize': 50,
                                        'extensions': ['pdf'],
                                        'optional': True
                                    }
                                }
                            },
                            'html': {
                                'order': 6,
                                'description': 'Enter a URL to a PDF file.',
                                'value': {
                                    'param': {
                                        'type': 'string',
                                        'regex': '"(http|https):\\/\\/.+"',
                                        'optional': True
                                    }
                                }
                            },
                            'venue': {
                                'order': 7,
                                'description': 'Enter the venue where the paper was published.',
                                'value': {
                                    'param': {
                                        'type': 'string',
                                        'optional': True
                                    }
                                }
                            },
                            'venueid': {
                                'value': {
                                    'param': {
                                        'type': "string",
                                        'const': archive_group.id,
                                        'hidden': True
                                    }
                                }
                            }
                        }
                    }                                        
                }
            )
        )

    def set_merge_profiles_invitations(self):

        content = {
            'email': {
                'order': 1,
                'description': 'email of the user making the request.',
                'value': {
                    'param': {
                        'type': 'string',
                        'regex': r"^[a-z0-9!#$%&'*+/=?^_`{|}~-]+(?:\.[a-z0-9!#$%&'*+/=?^_`{|}~-]+)*@(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.)+[a-z0-9](?:[a-z0-9-]*[a-z0-9])?$",
                        'mismatchError': 'must be a valid email',
                        'optional': True
                    }
                }
            },
            'left': {
                'order': 2,
                'description': 'Username or email that want to be merged.',
                'value': {
                    'param': {
                        'type': 'string',
                        'regex': '^~[^\d\s]+[1-9][0-9]*$|([a-z0-9_\-\.]{1,}@[a-z0-9_\-\.]{2,}\.[a-z]{2,},){0,}([a-z0-9_\-\.]{1,}@[a-z0-9_\-\.]{2,}\.[a-z]{2,})',
                        'mismatchError': 'must be a valid email or profile ID'
                    }
                }
            },
            'right': {
                'order': 3,
                'description': 'Username or email that want to be merged.',
                'value': {
                    'param': {
                        'type': 'string',
                        'regex': '^~[^\d\s]+[1-9][0-9]*$|([a-z0-9_\-\.]{1,}@[a-z0-9_\-\.]{2,}\.[a-z]{2,},){0,}([a-z0-9_\-\.]{1,}@[a-z0-9_\-\.]{2,}\.[a-z]{2,})',
                        'mismatchError': 'must be a valid email or profile ID'
                    }
                }
            },
            'comment': {
                'order': 4,
                'description': 'Reason why you want to delete your name.',
                'value': {
                    'param': {
                        'type': 'string',
                        'maxLength': 5000,
                        'markdown': True,
                        'input': 'textarea',
                        'optional': True
                    }
                }
            },
            'status': {
                'value': 'Pending'
            }
        }

        with open(os.path.join(os.path.dirname(__file__), 'process/request_merge_profiles_process.py'), 'r') as f:
            file_content = f.read()
            self.client_v2.post_invitation_edit(
                invitations = f'{self.super_user}/-/Edit',
                signatures = [self.super_user],
                invitation = openreview.api.Invitation(
                    id=f'{self.support_group_id}/-/Profile_Merge',
                    readers=['everyone'],
                    writers=[self.support_group_id],
                    signatures=[self.support_group_id],
                    invitees=['~', '(guest)'],
                    process=file_content,
                    edit={
                        'readers': [self.support_group_id, '${2/note/content/right/value}', '${2/note/content/left/value}'],
                        'writers': [self.support_group_id],
                        'signatures': {
                            'param': {
                                'items': [
                                    { 'prefix': '~.*', 'optional': True },
                                    { 'value': self.support_group_id, 'optional': True },
                                    { 'value': '(guest)', 'optional': True } 
                                ]
                            }
                        },
                        'note': {
                            'readers': ['${3/readers}'],
                            'writers': ['${3/writers}'],
                            'signatures': ['${3/signatures}'],
                            'content': content
                        }
                    }
                )
            )        
    

        content = {
            'status': {
                'order': 1,
                'description': 'Decision status.',
                'value': {
                    'param': {
                        'type': 'string',
                        'enum': ['Accepted', 'Rejected', 'Ignored']
                    }
                }
            },
            'support_comment': {
                'order': 2,
                'description': 'Justify the decision.',
                'value': {
                    'param': {
                        'type': 'string',
                        'maxLength': 5000,
                        'markdown': True,
                        'input': 'textarea',
                        'optional': True
                    }
                }
            }            
        }

        with open(os.path.join(os.path.dirname(__file__), 'process/request_merge_profiles_decision_process.py'), 'r') as f:
            file_content = f.read()
            file_content = file_content.replace("SUPPORT_USER_ID = ''", "SUPPORT_USER_ID = '" + self.support_group_id + "'")
            file_content = file_content.replace("AUTHOR_RENAME_INVITATION_ID = ''", "AUTHOR_RENAME_INVITATION_ID = '" + self.author_rename_invitation_id + "'")
            self.client_v2.post_invitation_edit(
                invitations = f'{self.super_user}/-/Edit',
                signatures = [self.super_user],
                invitation = openreview.api.Invitation(
                    id=f'{self.support_group_id}/-/Profile_Merge_Decision',
                    readers=['everyone'],
                    writers=[self.support_group_id],
                    signatures=[self.super_user],
                    invitees=[self.support_group_id],
                    process=file_content,
                    edit={
                        'readers': [self.support_group_id],
                        'writers': [self.support_group_id],
                        'signatures': [self.support_group_id],
                        'note': {
                            'id': {
                                'param': {
                                    'withInvitation': f'{self.support_group_id}/-/Profile_Merge'
                                }
                            },
                            'content': content
                        }
                    }
                )
            )           

