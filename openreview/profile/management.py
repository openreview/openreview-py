import os
import openreview
from openreview.stages import *

class ProfileManagement():

    def __init__(self, client, super_user):

        self.client = client
        self.super_user = super_user
        self.support_group_id = f'{self.super_user}/Support'
        self.author_rename_invitation_id = f'{self.support_group_id}/-/Author_Rename'


    def setup(self):
        self.set_remove_name_invitations()
        self.set_remove_email_invitations()
        self.set_archive_invitations()
        self.set_merge_profiles_invitations()
        self.set_dblp_invitations()
        self.set_anonymous_preprint_invitations()

    def set_dblp_invitations(self):

        dblp_group_id = 'DBLP.org'
        dblp_uploader_group_id = f'{dblp_group_id}/Uploader'

        dblp_group = openreview.tools.get_group(self.client, dblp_group_id)
        if dblp_group is None:
            self.client.post_group_edit(
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
        self.client.post_invitation_edit(
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
            self.client.post_group_edit(
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

        self.client.post_invitation_edit(
            invitations = meta_invitation_id,
            signatures = [dblp_group_id],
            invitation = openreview.api.Invitation(
                id=record_invitation_id,
                readers=['everyone'],
                writers=[dblp_group_id],
                signatures=[dblp_group_id],
                invitees=['~'],
                process=file_content,
                maxReplies=1000,
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
                    'writers':  [dblp_uploader_group_id],
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

        self.client.post_invitation_edit(
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
                    'writers':  [dblp_group_id],
                    'content': {
                        'author_index': {
                            'order': 1,
                            'description': 'Enter the 0 based index of the author in the author list. The author name listed in that position must match with one of your names in your profile.',
                            'value': {
                                'param': {
                                    'type': 'integer'
                                }
                            }
                        },
                        'author_id' : {
                            'order': 2,
                            'description': 'Enter the author id that matches with the author name in the author list.',
                            'value': {
                                'param': {
                                    'type': 'string'
                                }
                            }
                        },
                    },
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
                                        'const': {
                                            'replace': {
                                                'index': '${6/content/author_index/value}',
                                                'value': '${6/content/author_id/value}'
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }                                        
                }
            )
        )

        abstract_invitation_id = f'{dblp_group_id}/-/Abstract'
        
        with open(os.path.join(os.path.dirname(__file__), 'process/dblp_abstract_process.js'), 'r') as f:
            file_content = f.read()

        self.client.post_invitation_edit(
            invitations = meta_invitation_id,
            signatures = [dblp_group_id],
            invitation = openreview.api.Invitation(
                id=abstract_invitation_id,
                readers=['everyone'],
                writers=[dblp_group_id],
                signatures=[dblp_group_id],
                invitees=[dblp_uploader_group_id],
                process=file_content,
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
                self.client.post_invitation_edit(
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

        self.client.post_invitation_edit(
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

        baseurl_v1, baseurl_v2 = openreview.tools.get_base_urls(self.client)
        client_v1 = openreview.Client(baseurl=baseurl_v1, token=self.client.token)        
        client_v1.post_invitation(openreview.Invitation(
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
                self.client.post_invitation_edit(
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

        archive_group_id = f'{self.super_user}/Archive'

        self.client.post_invitation_edit(invitations=None,
            readers=[archive_group_id],
            writers=[archive_group_id],
            signatures=['~Super_User1'],
            invitation=openreview.api.Invitation(id=f'{archive_group_id}/-/Edit',
                invitees=[archive_group_id],
                readers=[archive_group_id],
                signatures=['~Super_User1'],
                edit=True
            )
        )        

        archive_group = openreview.api.Group(
            id = archive_group_id,
            readers = ['everyone'],
            writers = [archive_group_id],
            signatures = [self.super_user],
            signatories = [archive_group_id]
        )

        with open(os.path.join(os.path.dirname(__file__), 'webfield/archiveWebfield.js'), 'r') as f:
            file_content = f.read()
            archive_group.web = file_content

            self.client.post_group_edit(
                invitation = f'{archive_group_id}/-/Edit',
                signatures = ['~Super_User1'],
                group = archive_group)

        self.client.post_invitation_edit(
            invitations = f'{archive_group_id}/-/Edit',
            signatures = [archive_group_id],
            invitation = openreview.api.Invitation(
                id=f'{archive_group.id}/-/Direct_Upload',
                readers=['~'],
                writers=[self.support_group_id],
                signatures=[archive_group_id],
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
                        'license': {
                            'param': {
                                'enum': [ 
                                    { 'value': 'CC BY 4.0', 'description': 'CC BY 4.0' },
                                    { 'value': 'CC BY-SA 4.0', 'description': 'CC BY-SA 4.0' },
                                    { 'value': 'CC BY-NC 4.0', 'description': 'CC BY-NC 4.0' },
                                    { 'value': 'CC BY-ND 4.0', 'description': 'CC BY-ND 4.0' },
                                    { 'value': 'CC BY-NC-SA 4.0', 'description': 'CC BY-NC-SA 4.0' },
                                    { 'value': 'CC BY-NC-ND 4.0', 'description': 'CC BY-NC-ND 4.0' },
                                    { 'value': 'CC0 1.0', 'description': 'CC0 1.0' } 
                                ]
                            }
                        },
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
                                        'type': 'profile[]',
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
                                        'optional': True,
                                        'deletable': True
                                    }
                                }
                            },
                            'html': {
                                'order': 6,
                                'description': 'Enter a URL to a PDF file.',
                                'value': {
                                    'param': {
                                        'type': 'string',
                                        'regex': '(http|https):\/\/.+',
                                        'optional': True,
                                        'deletable': True
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

        with open(os.path.join(os.path.dirname(__file__), 'process/archive_comment_process.py'), 'r') as f:
            process_content = f.read()

        self.client.post_invitation_edit(
            invitations = f'{archive_group.id}/-/Edit',
            signatures = [archive_group.id],
            invitation = openreview.api.Invitation(id=f'{archive_group.id}/-/Comment',
                invitees=[archive_group.id],
                readers=[archive_group.id],
                writers=[archive_group.id],
                signatures=[archive_group.id],
                content={
                    'comment_process_script': {
                        'value': process_content
                    }
                },
                edit={
                    'signatures': [archive_group.id],
                    'readers': [archive_group.id],
                    'writers': [archive_group.id],
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
                        'id': f'{archive_group.id}/Submission${{2/content/noteNumber/value}}/-/Comment',
                        'signatures': [ archive_group.id ],
                        'readers': ['everyone'],
                        'writers': [archive_group.id],
                        'invitees': ['everyone'],
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
                                    'items': [
                                        { 'prefix': '~.*' }
                                    ] 
                                }
                            },
                            'readers': ['${2/note/readers}'],
                            'writers': [archive_group.id],
                            'note': {
                                'id': {
                                    'param': {
                                        'withInvitation': f'{archive_group.id}/Submission${{6/content/noteNumber/value}}/-/Comment',
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
                                'writers': [archive_group.id, '${3/signatures}'],
                                'content': default_content.comment_v2.copy()
                            }
                        }
                    }

                }
            )
        )        

    def set_anonymous_preprint_invitations(self):

        anonymous_group_id = f'{self.super_user}/Anonymous_Preprint'
        author_anonymous_group_id = f'{anonymous_group_id}/Submission${{2/note/number}}/Authors'

        self.client.post_invitation_edit(invitations=None,
            readers=[anonymous_group_id],
            writers=[anonymous_group_id],
            signatures=['~Super_User1'],
            invitation=openreview.api.Invitation(id=f'{anonymous_group_id}/-/Edit',
                invitees=[anonymous_group_id],
                readers=[anonymous_group_id],
                signatures=['~Super_User1'],
                edit=True
            )
        )        
        
        anonymous_group = openreview.api.Group(
            id = anonymous_group_id,
            readers = ['everyone'],
            writers = [anonymous_group_id],
            signatures = [self.super_user],
            signatories = [anonymous_group_id]
        )

        with open(os.path.join(os.path.dirname(__file__), 'webfield/anonymousWebfield.js'), 'r') as f:
            file_content = f.read()
            anonymous_group.web = file_content

            self.client.post_group_edit(
                invitation = f'{anonymous_group_id}/-/Edit',
                signatures = ['~Super_User1'],
                group = anonymous_group)
            
        with open(os.path.join(os.path.dirname(__file__), 'process/anonymous_preprint_submission_process.py'), 'r') as f:
            process_content = f.read()

        self.client.post_invitation_edit(
            invitations = f'{anonymous_group_id}/-/Edit',
            signatures = [anonymous_group_id],
            invitation = openreview.api.Invitation(
                id=f'{anonymous_group_id}/-/Submission',
                readers=['~'],
                writers=[anonymous_group_id],
                signatures=[anonymous_group_id],
                invitees=['~'],
                edit={
                    'readers': [ anonymous_group_id, author_anonymous_group_id],
                    'signatures': { 
                        'param': { 
                            'items': [
                                { 'prefix': '~.*', 'optional': True },
                                { 'value': anonymous_group_id, 'optional': True } 
                            ]
                        } 
                    },
                    'writers': [ anonymous_group_id, author_anonymous_group_id],
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
                                'withInvitation': f'{anonymous_group_id}/-/Submission',
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
                        'odate': '${2/cdate}',
                        'signatures': [ f'{anonymous_group_id}/Submission${{2/number}}/Authors' ],
                        'readers': ['everyone'],
                        'writers': [ anonymous_group_id, f'{anonymous_group_id}/Submission${{2/number}}/Authors'],
                        'license': {
                            'param': {
                                'enum': [ 
                                    { 'value': 'CC BY 4.0', 'description': 'CC BY 4.0' },
                                    { 'value': 'CC BY-SA 4.0', 'description': 'CC BY-SA 4.0' },
                                    { 'value': 'CC BY-NC 4.0', 'description': 'CC BY-NC 4.0' },
                                    { 'value': 'CC BY-ND 4.0', 'description': 'CC BY-ND 4.0' },
                                    { 'value': 'CC BY-NC-SA 4.0', 'description': 'CC BY-NC-SA 4.0' },
                                    { 'value': 'CC BY-NC-ND 4.0', 'description': 'CC BY-NC-ND 4.0' },
                                    { 'value': 'CC0 1.0', 'description': 'CC0 1.0' } 
                                ]
                            }
                        },
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
                                },
                                'readers': [ anonymous_group_id, f'{anonymous_group_id}/Submission${{4/number}}/Authors']
                            },
                            'authorids': {
                                'order': 3,
                                'description': 'Search author profile by first, middle and last name or email address. If the profile is not found, you can add the author by completing first, middle, and last names as well as author email address.',
                                'value': {
                                    'param': {
                                        'type': 'profile[]',
                                        'regex': r"^~\S+$|^[a-z0-9!#$%&'*+/=?^_`{|}~-]+(?:\.[a-z0-9!#$%&'*+/=?^_`{|}~-]+)*@(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.)+[a-z0-9](?:[a-z0-9-]*[a-z0-9])?$",
                                        'mismatchError': 'must be a valid email or profile ID'
                                    }
                                },
                                'readers': [ anonymous_group_id, f'{anonymous_group_id}/Submission${{4/number}}/Authors']
                            },
                            'keywords': {
                                'description': 'Comma separated list of keywords.',
                                'order': 4,
                                'value': {
                                    'param': {
                                        'type': 'string[]',
                                        'regex': '.+'
                                    }
                                }
                            },
                            'TLDR': {
                                'order': 5,
                                'description': '\"Too Long; Didn\'t Read\": a short sentence describing your paper',
                                'value': {
                                    'param': {
                                        'fieldName': 'TL;DR',
                                        'type': 'string',
                                        'maxLength': 250,
                                        'optional': True,
                                        'deletable': True
                                    }
                                }        
                            },                                                    
                            'abstract': {
                                'order': 6,
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
                                'order': 7,
                                'description': 'Upload a PDF file that ends with .pdf.',
                                'value': {
                                    'param': {
                                        'type': 'file',
                                        'maxSize': 50,
                                        'extensions': ['pdf']
                                    }
                                }
                            },
                            'venue': {
                                'order': 7,
                                'description': 'Enter the venue where the paper was published.',
                                'value': {
                                    'param': {
                                        'type': 'string',
                                        'const': 'Anonymous Preprint Submission',
                                        'hidden': True
                                    }
                                }
                            },
                            'venueid': {
                                'value': {
                                    'param': {
                                        'type': "string",
                                        'const': anonymous_group_id,
                                        'hidden': True
                                    }
                                }
                            }
                        }
                    }                                        
                },
                process=process_content
            )
        )

        with open(os.path.join(os.path.dirname(__file__), 'process/anonymous_preprint_comment_process.py'), 'r') as f:
            process_content = f.read()

        self.client.post_invitation_edit(
            invitations = f'{anonymous_group_id}/-/Edit',
            signatures = [anonymous_group_id],
            invitation = openreview.api.Invitation(id=f'{anonymous_group_id}/-/Comment',
                invitees=[anonymous_group_id],
                readers=[anonymous_group_id],
                writers=[anonymous_group_id],
                signatures=[anonymous_group_id],
                content={
                    'comment_process_script': {
                        'value': process_content
                    }
                },
                edit={
                    'signatures': [anonymous_group_id],
                    'readers': [anonymous_group_id],
                    'writers': [anonymous_group_id],
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
                        'id': f'{anonymous_group_id}/Submission${{2/content/noteNumber/value}}/-/Comment',
                        'signatures': [ anonymous_group_id ],
                        'readers': ['everyone'],
                        'writers': [anonymous_group_id],
                        'invitees': ['everyone'],
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
                                    'items': [
                                        { 'prefix': '~.*', 'optional': True },
                                        { 'value': f'{anonymous_group_id}/Submission${{7/content/noteNumber/value}}/Authors', 'optional': True },
                                    ] 
                                }
                            },
                            'readers': ['${2/note/readers}'],
                            'writers': [anonymous_group_id],
                            'note': {
                                'id': {
                                    'param': {
                                        'withInvitation': f'{anonymous_group_id}/Submission${{6/content/noteNumber/value}}/-/Comment',
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
                                'writers': [anonymous_group_id, '${3/signatures}'],
                                'content': default_content.comment_v2.copy()
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
            self.client.post_invitation_edit(
                invitations = f'{self.super_user}/-/Edit',
                signatures = [self.super_user],
                invitation = openreview.api.Invitation(
                    id=f'{self.support_group_id}/-/Profile_Merge',
                    readers=['everyone'],
                    writers=[self.support_group_id],
                    signatures=[self.super_user],
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
            self.client.post_invitation_edit(
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

