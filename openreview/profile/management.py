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
            file_content = file_content.replace("SUPPORT_USER_ID = ''", "SUPPORT_USER_ID = '" + self.support_group_id + "'")
            file_content = file_content.replace("REMOVAL_DECISION_INVITATION_ID = ''", "REMOVAL_DECISION_INVITATION_ID = '" + f'{self.support_group_id}/-/Profile_Name_Removal_Decision' + "'")
                
            with open(os.path.join(os.path.dirname(__file__), 'process/request_remove_name_pre_process.py'), 'r') as pre:
                pre_file_content = pre.read()
                self.client.post_invitation(openreview.Invitation(
                    id=f'{self.support_group_id}/-/Profile_Name_Removal',
                    readers=['everyone'],
                    writers=[self.support_group_id],
                    signatures=[self.super_user],
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

            with open(os.path.join(os.path.dirname(__file__), 'process/request_remove_name_decision_pre_process.py'), 'r') as pre:
                pre_file_content = pre.read()

            self.client.post_invitation(openreview.Invitation(
                id=f'{self.support_group_id}/-/Profile_Name_Removal_Decision',
                readers=['everyone'],
                writers=[self.support_group_id],
                signatures=[self.super_user],
                invitees=[self.support_group_id],
                process_string=file_content,
                preprocess=pre_file_content,
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

    def set_remove_email_invitations(self):

        content = {
            'email': {
                'order': 1,
                'description': 'email that want to be removed.',
                'value-regex': '.*',
                'required': True                
            },
            'profile_id': {
                'order': 2,
                'description': 'profile id where the email associated with.',
                'value-regex': '~.*',
                'required': True
            },
            'comment': {
                'order': 3,
                'value-regex': '[\\S\\s]{1,5000}',
                'description': 'Reason why you want to delete your name.',
                'required': False
            }
        }

        with open(os.path.join(os.path.dirname(__file__), 'process/request_remove_email_process.py'), 'r') as f:
            file_content = f.read()
            file_content = file_content.replace("SUPPORT_USER_ID = ''", "SUPPORT_USER_ID = '" + self.support_group_id + "'")
            file_content = file_content.replace("AUTHOR_RENAME_INVITATION_ID = ''", "AUTHOR_RENAME_INVITATION_ID = '" + self.author_rename_invitation_id + "'")
            with open(os.path.join(os.path.dirname(__file__), 'process/request_remove_email_pre_process.py'), 'r') as pre:
                pre_file_content = pre.read()
                self.client.post_invitation(openreview.Invitation(
                    id=f'{self.support_group_id}/-/Profile_Email_Removal',
                    readers=['everyone'],
                    writers=[self.support_group_id],
                    signatures=[self.super_user],
                    invitees=['~'],
                    process_string=file_content,
                    preprocess=pre_file_content,
                    reply={
                        'readers': {
                            'values-copied': [self.support_group_id]
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
                'value-regex': '([a-z0-9_\-\.]{1,}@[a-z0-9_\-\.]{2,}\.[a-z]{2,},){0,}([a-z0-9_\-\.]{1,}@[a-z0-9_\-\.]{2,}\.[a-z]{2,})',
                'required': False                
            },
            'left': {
                'order': 2,
                'description': 'Username or email that want to be merged.',
                'value-regex': '^~[^\d\s]+[1-9][0-9]*$|([a-z0-9_\-\.]{1,}@[a-z0-9_\-\.]{2,}\.[a-z]{2,},){0,}([a-z0-9_\-\.]{1,}@[a-z0-9_\-\.]{2,}\.[a-z]{2,})',
                'required': True
            },
            'right': {
                'order': 3,
                'description': 'Username or email that want to be merged.',
                'value-regex': '^~[^\d\s]+[1-9][0-9]*$|([a-z0-9_\-\.]{1,}@[a-z0-9_\-\.]{2,}\.[a-z]{2,},){0,}([a-z0-9_\-\.]{1,}@[a-z0-9_\-\.]{2,}\.[a-z]{2,})',
                'required': True
            },
            'comment': {
                'order': 4,
                'value-regex': '[\\S\\s]{1,5000}',
                'description': 'Reason why you want to delete your name.',
                'required': False
            },
            'status': {
                'order': 5,
                'value-dropdown': ['Pending', 'Accepted', 'Rejected', 'Ignored'],
                'description': 'Request status.',
                'required': True
            }
        }

        with open(os.path.join(os.path.dirname(__file__), 'process/request_merge_profiles_process.py'), 'r') as f:
            file_content = f.read()
            self.client.post_invitation(openreview.Invitation(
                id=f'{self.support_group_id}/-/Profile_Merge',
                readers=['everyone'],
                writers=[self.support_group_id],
                signatures=[self.support_group_id],
                invitees=['~', '(guest)'],
                process_string=file_content,
                reply={
                    'readers': {
                        'values-copied': [self.support_group_id, '{content.right}', '{content.left}']
                    },
                    'writers': {
                        'values':[self.support_group_id],
                    },
                    'signatures': {
                        'values-regex': f'~.*|{self.support_group_id}|\(guest\)'
                    },
                    'content': content
                }
            ))        
    

        content = {
            'status': {
                'order': 1,
                'value-dropdown': ['Accepted', 'Rejected', 'Ignored'],
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

        with open(os.path.join(os.path.dirname(__file__), 'process/request_merge_profiles_decision_process.py'), 'r') as f:
            file_content = f.read()
            file_content = file_content.replace("SUPPORT_USER_ID = ''", "SUPPORT_USER_ID = '" + self.support_group_id + "'")
            file_content = file_content.replace("AUTHOR_RENAME_INVITATION_ID = ''", "AUTHOR_RENAME_INVITATION_ID = '" + self.author_rename_invitation_id + "'")
            self.client.post_invitation(openreview.Invitation(
                id=f'{self.support_group_id}/-/Profile_Merge_Decision',
                readers=['everyone'],
                writers=[self.support_group_id],
                signatures=[self.super_user],
                invitees=[self.support_group_id],
                process_string=file_content,
                reply={
                    'referentInvitation': f'{self.support_group_id}/-/Profile_Merge',
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

