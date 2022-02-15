from openreview.api import Invitation
from openreview.api import Group

class Templates():

    def __init__(self, client, support_group_id):
        self.support_group_id = support_group_id
        self.client = client

    def set_templates_group(self):
        support_teaplates_group = self.client.post_group(Group(
            id=f'{self.support_group_id}/Templates',
            readers = ['everyone'],
            writers = [self.support_group_id],
            signatures = [self.support_group_id],
            signatories = [self.support_group_id.split('/'[0])],
            members = []
        ))

    def set_meta_invitation(self):

        self.client.post_invitation_edit(invitations=None,
            readers=[self.support_group_id],
            writers=[self.support_group_id],
            signatures=[self.support_group_id],
            invitation=Invitation(id=f'{self.support_group_id}/-/Edit',
                invitees=[self.support_group_id],
                readers=[self.support_group_id],
                signatures=[self.support_group_id],
                edit=True
            )
        )

    def set_submission_meta(self):

        submission_meta_invitation = Invitation(id=f'{self.support_group_id}/Templates/-/Submission_Template',
            invitees = [self.support_group_id],
            readers = [self.support_group_id],
            writers = [self.support_group_id],
            signatures = [self.support_group_id],
            edit = {
                'signatures': { 'values': [self.support_group_id] },
                'readers': { 'values': [self.support_group_id] },
                'writers': { 'values': [self.support_group_id] },
                'params': {
                    'venueid':  { 'value-regex': '.*' },
                    'cdate': { 'value-regex': '.*' },
                    'duedate': { 'value-regex': '.*' },
                    'name': { 'value-regex': '.*' }
                },
                'invitation': {
                    'id': { 'value': '${params.venueid}/-/${params.name}' },
                    'signatures': { 'values': ['${params.venueid}'] },
                    'readers': { 'values': ['everyone'] },
                    'writers': { 'values': ['${params.venueid}'] },
                    'invitees': { 'values': ['~'] },
                    'cdate': { 'value': '${params.cdate}' },
                    'duedate': { 'value': '${params.duedate}' },
                    'edit': {
                        'signatures': { 'value': { 'values-regex': '~.*' }},
                        'readers': { 'value': { 'values': ['${params.venueid}', '${params.venueid}/${params.name}/\\${note.number}/Authors'] }},
                        'writers': { 'value': { 'values': ['${params.venueid}'] }},
                        'note': {
                            'id': {
                                'value': {
                                    'value-invitation': '${params.venueid}/-/${params.name}',
                                    'optional': True
                                }
                            },
                            'signatures': { 'value': { 'values': ['${params.venueid}/${params.name}/\\${note.number}/Authors'] }},
                            'readers': { 'value': { 'values': ['${params.venueid}', '${params.venueid}/${params.name}/\\${note.number}/Authors'] }},
                            'writers': { 'value': { 'values': ['${params.venueid}', '${params.venueid}/${params.name}/\\${note.number}/Authors'] }},
                            'content': {
                                'title': {
                                    'value': {
                                        'value': {
                                            'value-regex': '.{1,250}'
                                        },
                                        'order': 1,
                                        'description': 'Title of paper. Add TeX formulas using the following formats: $In-line Formula$ or $$Block Formula$$'
                                    }
                                },
                                'authors': {
                                    'value': {
                                        'value': {
                                            'values-regex': '[^;,\\n]+(,[^,\\n]+)*'
                                        },
                                        'order': 2,
                                        'description': 'Comma separated list of author names.',
                                        'presentation': {
                                            'hidden': True
                                        }
                                    }  
                                },
                                'authorids': {
                                    'value': {
                                        'value': {
                                            'values-regex': r'~.*'
                                        },
                                        'order': 3,
                                        'description': 'Search author profile by first, middle and last name or email address. If the profile is not found, you can add the author completing first, middle, last and name and author email address.'
                                    }
                                },
                                'keywords': {
                                    'value': {
                                        'value': {
                                            'values-regex': '(^$)|[^;,\\n]+(,[^,\\n]+)*'
                                        },
                                        'order': 4,
                                        'description': 'Comma separated list of keywords'
                                    }
                                },
                                'abstract': {
                                    'value': {
                                        'value': {
                                            'value-regex': '^[\\S\\s]{1,5000}$'
                                        },
                                        'description': 'Abstract of paper. Add TeX formulas using the following formats: $In-line Formula$ or $$Block Formula$$.',
                                        'order': 5,
                                        'presentation': {
                                            'markdown': True
                                        }
                                    }
                                },
                                'TL;DR': {
                                    'value': {
                                        'value': {
                                            'value-regex': '[^\\n]{0,250}'
                                        },
                                        'order': 6,
                                        'description': '\"Too Long; Didn\'t Read\": a short sentence describing your paper'
                                        # 'presentation': {
                                            # 'optional': True
                                        # }
                                    }
                                },
                                'pdf': {
                                    'value': {
                                        'value': {
                                            'value-file': {
                                                'fileTypes': ['pdf'],
                                                'size': 50
                                            }
                                        },
                                        'description': 'Upload a PDF file that ends with .pdf.',
                                        'order': 7,
                                    }
                                }
                            }
                        }
                    }
                }
            })

        self.client.post_invitation_edit(invitations=f'{self.support_group_id}/-/Edit',
            readers=[self.support_group_id],
            writers=[self.support_group_id],
            signatures=[self.support_group_id],
            invitation=submission_meta_invitation)
