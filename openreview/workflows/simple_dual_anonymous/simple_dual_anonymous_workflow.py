import openreview.api
from ... import openreview
from openreview.api import Invitation
import os
from ...stages import default_content

class Simple_Dual_Anonymous_Workflow():

    def __init__(self, client, support_group_id, super_id):
        self.support_group_id = support_group_id        #openreview.net/Support
        self.client = client
        self.super_id = super_id                        #openreview.net
        self.meta_invitation_id = f'{super_id}/-/Edit'  #openreview.net/-/Edit
        self.update_wait_time = 5000
        self.update_date_string = "#{4/mdate} + " + str(self.update_wait_time)
        self.invitation_edit_process = '''def process(client, invitation):
    domain = client.get_group(invitation.domain)
    meta_invitation = client.get_invitation(domain.content['meta_invitation_id']['value'])
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
    domain = client.get_group(invitation.domain)
    meta_invitation = client.get_invitation(domain.content['meta_invitation_id']['value'])
    script = meta_invitation.content["group_edit_script"]['value']
    funcs = {
        'openreview': openreview,
        'datetime': datetime,
        'date_index': date_index
    }
    exec(script, funcs)
    funcs['process'](client, invitation)
'''

    def setup(self):
        self.set_meta_invitation()
        self.set_reviewers_dual_anonymous_invitation()
        self.set_deploy_invitation()
        self.set_venues_homepage()

        # setup group template invitations
        self.setup_automated_administrator_group_template_invitation()
        self.setup_venue_group_template_invitation()
        self.setup_inner_group_template_invitation()
        self.setup_program_chairs_group_template_invitation()
        self.setup_reviewers_group_template_invitation()
        self.setup_submission_reviewer_group_invitation()
        self.setup_authors_group_template_invitation()
        self.setup_authors_accepted_group_template_invitation()

        # setup workflow template invitations
        self.setup_submission_template_invitation()
        self.setup_post_submission_template_invitation()
        self.setup_review_template_invitation()
        self.setup_official_comment_template_invitation()
        self.setup_decision_template_invitation()
        self.setup_withdrawal_template_invitation()
        self.setup_withdrawn_submission_template_invitation()
        self.setup_withdrawal_expiration_template_invitation()
        self.setup_withdrawal_reversion_template_invitation()
        self.setup_desk_rejection_template_invitation()
        self.setup_desk_rejected_submission_template_invitation()
        self.setup_desk_reject_expiration_template_invitation()
        self.setup_desk_rejection_reversion_template_invitation()
        self.setup_reviewer_bid_template_invitation()
        self.setup_edit_template_invitation()
        self.setup_reviewer_conflicts_template_invitation()
        self.setup_reviewer_affinities_template_invitation()

    def get_process_content(self, file_path):
        process = None
        with open(os.path.join(os.path.dirname(__file__), file_path)) as f:
            process = f.read()
            return process

    def get_webfield_content(self, file_path):
        webfield = None
        with open(os.path.join(os.path.dirname(__file__), file_path)) as f:
            webfield = f.read()
            return webfield
        
    def post_invitation_edit(self, invitation):
        return self.client.post_invitation_edit(invitations=self.meta_invitation_id,
            readers=['~Super_User1'],
            writers=['~Super_User1'],
            signatures=['~Super_User1'],
            invitation=invitation,
            replacement=True
        )
    
    def set_meta_invitation(self):

        self.client.post_invitation_edit(invitations=None,
            readers=['~Super_User1'],
            writers=['~Super_User1'],
            signatures=['~Super_User1'],
            invitation=Invitation(id=self.meta_invitation_id,
                invitees=['~Super_User1'],
                readers=['~Super_User1'],
                signatures=['~Super_User1'],
                edit=True
            )
        )

    def set_reviewers_dual_anonymous_invitation(self):

        super_id = self.super_id
        support_group_id = self.support_group_id
        conference_venue_invitation_id = f'{support_group_id}/Simple_Dual_Anonymous/-/Venue_Configuration_Request'

        invitation = Invitation(
            id = conference_venue_invitation_id,
            invitees = ['everyone'],
            readers = ['everyone'],
            writers = [],
            signatures = [super_id],
            edit = {
                'signatures': { 'param': { 'regex': '~.*' } },
                'writers': ['${2/note/writers}'],
                'readers': ['${2/note/readers}'],
                'note': {
                    'signatures': ['${3/signatures}'],
                    'readers': [ self.support_group_id, '${2/content/program_chair_emails/value}', '${3/signatures}' ],
                    'writers': [ self.support_group_id, '${2/content/program_chair_emails/value}', '${3/signatures}'],
                    'content': {
                        'title': {
                            'description': 'Used for display purposes. This is copied from the Official Venue Name',
                            'order': 1,
                            'value': {
                                'param': {
                                    'type': 'string',
                                    'const': '${2/official_venue_name/value}',
                                    'hidden': True
                                }
                            }
                        },
                        'official_venue_name': {
                            'order': 2,
                            'description': 'The official name of your venue. This will appear on your venue\'s OpenReview page. Example: "Seventh International Conference on Learning Representations',
                            'value': {
                                'param': {
                                    'type': 'string',
                                    'regex': '.{0,500}'
                                }
                            }
                        },
                        'abbreviated_venue_name': {
                            'order': 3,
                            'description': 'The abbreviated name for your venue. Please include the year as well. This will be used to identify your venue on OpenReview and in email subject lines. Example: "ICLR 2019"',
                            'value': {
                                'param': {
                                    'type': 'string',
                                    'regex': '.{0,500}'
                                }
                            }
                        },
                        'venue_website_url': {
                            'order': 4,
                            'description': 'The URL of the official website for your venue.',
                            'value': {
                                'param': {
                                    'type': 'string',
                                    'regex': '.{0,500}'
                                }
                            }
                        },
                        'location': {
                            'order': 5,
                            'description': 'Where will your venue be held? This will be displayed on your venue\'s OpenReview page. Example: "Vancouver, Canada"',
                            'value': {
                                'param': {
                                    'type': 'string',
                                    'regex': '.{0,500}'
                                }
                            }
                        },
                        'venue_start_date': {
                            'order': 6,
                            'description': 'What date does the venue start? Please enter a time and date in GMT using the following format: YYYY/MM/DD (e.g. 2019/01/31)',
                            'value': {
                                'param': {
                                    'type': 'date',
                                    'range': [ 0, 9999999999999 ],
                                    'deletable': True
                                }
                            }
                        },
                        'program_chair_emails': {
                            'order': 7,
                            'description': 'A comma separated list of *lower-cased* email addresses for the program chairs of your venue, including the PC submitting this request',
                            'value': {
                                'param': {
                                    'type': 'string[]',
                                    'regex': r"^[a-z0-9!#$%&'*+/=?^_`{|}~-]+(?:\.[a-z0-9!#$%&'*+/=?^_`{|}~-]+)*@(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.)+[a-z0-9](?:[a-z0-9-]*[a-z0-9])?$"
                                }
                            }
                        },
                        'contact_email': {
                            'order': 8,
                            'description': 'Single point of contact *lower-cased* email address which will be displayed on the venue page. For example: pc@venue.org',
                            'value': {
                                'param': {
                                    'type': 'string',
                                    'regex': r"^[a-z0-9!#$%&'*+/=?^_`{|}~-]+(?:\.[a-z0-9!#$%&'*+/=?^_`{|}~-]+)*@(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.)+[a-z0-9](?:[a-z0-9-]*[a-z0-9])?$"
                                }
                            }
                        },
                        'submission_start_date': {
                            'order': 9,
                            'description': 'When should your OpenReview submission portal open? Please specify the date and time in GMT using the following format: YYYY/MM/DD HH:MM(e.g. 2019/01/31 23:59). (Leave blank if you would like the portal to open for submissions as soon as possible)',
                            'value': {
                                'param': {
                                    'type': 'date',
                                    'range': [ 0, 9999999999999 ],
                                    'deletable': True
                                }
                            }
                        },
                        'submission_deadline': {
                            'order': 10,
                            'description': 'By when do authors need to submit their manuscripts? Please specify the due date in GMT using the following format: YYYY/MM/DD HH:MM(e.g. 2019/01/31 23:59)',
                            'value': {
                                'param': {
                                    'type': 'date',
                                    'range': [ 0, 9999999999999 ],
                                    'deletable': True
                                }
                            }
                        },
                        'submission_license': {
                            'order': 11,
                            'description': 'Which license should be applied to each submission? We recommend "CC BY 4.0". If you select multiple licenses, you allow authors to choose their license upon submission. If your license is not listed, please contact us. Refer to https://openreview.net/legal/terms for more information.',
                            'value': {
                                'param': {
                                    'type': 'string[]',
                                    'enum': [
                                        'CC BY 4.0',
                                        'CC BY-SA 4.0',
                                        'CC BY-NC 4.0',
                                        'CC BY-ND 4.0',
                                        'CC BY-NC-SA 4.0',
                                        'CC BY-NC-ND 4.0',
                                        'CC0 1.0'
                                    ],
                                    'input': 'checkbox'
                                }
                            }
                        },
                        'other_important_information': {
                            'order': 12,
                            'description': 'Please provide any other important information about your venue that you would like to share with OpenReview. Please use this space to clarify any questions for which you could not use any of the provided options, and to clarify any other information that you think we may need.',
                            'value': {
                                'param': {
                                    'type': 'string',
                                    'maxLength': 5000,
                                    'optional': True,
                                    'deletable': True,
                                    'input': 'textarea'
                                }
                            }
                        }
                    },
                    'id' : {
                        'param': {
                            'withInvitation': conference_venue_invitation_id,
                            'optional': True
                        }
                    }
                }
            },
            process=self.get_process_content('process/support_process.py')
        )

        self.post_invitation_edit(invitation)

    def set_deploy_invitation(self):

        support_group_id = self.support_group_id
        deploy_invitation_id = f'{support_group_id}/-/Deployment'

        invitation = Invitation(
            id = deploy_invitation_id,
            invitees = [support_group_id],
            readers = ['everyone'],
            writers = [support_group_id],
            signatures = [support_group_id],
            content={
                'deploy_process_script': {
                    'value': self.get_process_content('process/deploy_process.py')
                }
            },
            edit = {
                'signatures': [support_group_id],
                'readers': [support_group_id],
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
                    'id': f'{support_group_id}/Simple_Dual_Anonymous/Venue_Configuration_Request' + '${2/content/noteNumber/value}' + '/-/Deployment',
                    'signatures': [ '~Super_User1' ],
                    'readers': ['everyone'],
                    'writers': [support_group_id],
                    'invitees': [support_group_id],
                    'maxReplies': 1,
                    'process': '''def process(client, edit, invitation):
    meta_invitation = client.get_invitation(invitation.invitations[0])
    script = meta_invitation.content['deploy_process_script']['value']
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
                                'items': [ { 'value': support_group_id, 'optional': True } ] 
                            }
                        },
                        'readers': ['${{2/note/id}/readers}'],
                        'writers': [support_group_id],
                        'note': {
                            'id': '${4/content/noteId/value}',
                            'forum': '${4/content/noteId/value}',
                            'ddate': {
                                'param': {
                                    'range': [ 0, 9999999999999 ],
                                    'optional': True,
                                    'deletable': True                                 
                                }
                            },
                            'signatures': ['${3/signatures}'],
                            'content': {
                                'venue_id': {
                                    'value': {
                                        'param': {
                                            'type': 'string',
                                            'regex': '.*'
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        )

        self.post_invitation_edit(invitation)

    def set_venues_homepage(self):

        self.client.post_group_edit(
            invitation=self.meta_invitation_id,
            signatures=['~Super_User1'],
            group=openreview.api.Group(
                id='venues',
                web=self.get_webfield_content('../webfield/venuepageWebfield.js'),
            )
        )

    def setup_submission_template_invitation(self):

        support_group_id = self.support_group_id

        invitation = Invitation(id=f'{support_group_id}/Simple_Dual_Anonymous/Venue_Configuration_Request/-/Submission',
            invitees=['active_venues'],
            readers=['everyone'],
            writers=['openreview.net/Support'],
            signatures=['openreview.net/Support'],
            process=self.get_process_content('process/submission_template_process.py'),
            edit = {
                'signatures' : {
                    'param': {
                        'items': [
                            { 'prefix': '~.*', 'optional': True },
                            { 'value': 'openreview.net/Support', 'optional': True }
                        ]
                    }
                },
                'readers': ['openreview.net/Support'],
                'writers': ['openreview.net/Support'],
                'content': {
                    'venue_id': {
                        'order': 1,
                        'description': 'Venue Id',
                        'value': {
                            'param': {
                                'type': 'string',
                                'maxLength': 100,
                                'regex': '.*',
                                'hidden': True
                            }
                        }
                    },
                    'venue_id_pretty': {
                        'order': 2,
                        'description': 'Pretty Venue Id',
                        'value': {
                            'param': {
                                'type': 'string',
                                'maxLength': 100,
                                'regex': '.*',
                                'hidden': True
                            }
                        }
                    },
                    'name': {
                        'order': 3,
                        'description': 'Name for this step, use underscores to represent spaces. Default is Submission. This name will be shown in the button users will click to perform this step.',
                        'value': {
                            'param': {
                                'type': 'string',
                                'maxLength': 100,
                                'regex': '^[a-zA-Z0-9_]*$',
                                'default': 'Submission'
                            }
                        }
                    },
                    'activation_date': {
                        'order': 4,
                        'description': 'When would you like to have your OpenReview submission portal opened?',
                        'value': {
                            'param': {
                                'type': 'date',
                                'range': [ 0, 9999999999999 ],
                                'deletable': True
                            }
                        }
                    },
                    'due_date': {
                        'order': 5,
                        'description': 'By when do authors need to submit their manuscripts?',
                        'value': {
                            'param': {
                                'type': 'date',
                                'range': [ 0, 9999999999999 ],
                                'optional': True,
                                'deletable': True
                            }
                        }
                    },
                    'submission_email_template': {
                        'order': 6,
                        'description': 'Email template to be sent to authors upon submission. Use {{variable}} to include dynamic content.',
                        'value': {
                            'param': {
                                'type': 'string',
                                'maxLength': 5000,
                                'optional': True,
                                'deletable': True,
                                'input': 'textarea',
                                'default': f'''Your submission to {{Abbreviated_Venue_Name}} has been {{action}}.

Submission Number: {{note_number}}

Title: {{note_title}} {{note_abstract}}

To view your submission, click here: https://openreview.net/forum?id={{note_forum}}'''
                            }
                        }
                    }  
                },
                'domain': '${1/content/venue_id/value}',
                'invitation': {
                    'id': '${2/content/venue_id/value}/-/${2/content/name/value}',
                    'invitees': ['~'],
                    'signatures': ['${3/content/venue_id/value}'],
                    'readers': ['everyone'],
                    'writers': ['${3/content/venue_id/value}'],
                    'cdate': '${2/content/activation_date/value}',
                    'duedate': '${2/content/due_date/value}',
                    'expdate': '${2/content/due_date/value}+1800000',
                    'content': {
                        'email_authors': {
                            'value': True
                        },
                        'email_program_chairs': {
                            'value': False
                        },
                        'submission_email_template': {
                            'value': '${4/content/submission_email_template/value}'
                        }
                    },
                    'edit': {
                        'signatures': {
                            'param': {
                                'items': [
                                    { 'prefix': '~.*', 'optional': True }
                                    # { 'value': self.venue.get_program_chairs_id(), 'optional': True }
                                ]
                            }
                        },
                        'readers': ['${4/content/venue_id/value}', '${2/note/content/authorids/value}'],
                        'writers': ['${4/content/venue_id/value}', '${2/note/content/authorids/value}'],
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
                                    'withVenueid': '${6/content/venue_id/value}/${6/content/name/value}',
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
                            'readers': ['${5/content/venue_id/value}', '${2/content/authorids/value}'],
                            'writers': ['${5/content/venue_id/value}', '${2/content/authorids/value}'],
                            'content': {
                                'title': {
                                    'order': 1,
                                    'description': 'Title of paper. Add TeX formulas using the following formats: $In-line Formula$ or $$Block Formula$$.',
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
                                    'value': {
                                        'param': {
                                            'const': '${8/content/venue_id_pretty/value}',
                                            'hidden': True
                                        }
                                    }
                                },
                                'venueid': {
                                    'value': {
                                        'param': {
                                            'const': '${8/content/venue_id/value}/${8/content/name/value}',
                                            'hidden': True
                                        }
                                    }
                                }
                            },
                            'license': "CC BY 4.0"
                        }
                    },
                    'process': self.get_process_content('../process/submission_process.py')
                }
            }
        )

        self.post_invitation_edit(invitation)

    def setup_post_submission_template_invitation(self):

        support_group_id = self.support_group_id

        invitation = Invitation(id=f'{support_group_id}/Simple_Dual_Anonymous/Venue_Configuration_Request/-/Submission_Change_After_Deadline',
            invitees=['active_venues'],
            readers=['everyone'],
            writers=['openreview.net/Support'],
            signatures=['openreview.net/Support'],
            process=self.get_process_content('process/post_submission_template_process.py'),
            edit = {
                'signatures' : {
                    'param': {
                        'items': [
                            { 'prefix': '~.*', 'optional': True },
                            { 'value': 'openreview.net/Support', 'optional': True }
                        ]
                    }
                },
                'readers': ['openreview.net/Support'],
                'writers': ['openreview.net/Support'],
                'content': {
                    'venue_id': {
                        'order': 1,
                        'description': 'Venue Id',
                        'value': {
                            'param': {
                                'type': 'string',
                                'maxLength': 100,
                                'regex': '.*',
                                'hidden': True
                            }
                        }
                    },
                    'venue_id_pretty': {
                        'order': 2,
                        'description': 'Pretty Venue Id',
                        'value': {
                            'param': {
                                'type': 'string',
                                'maxLength': 100,
                                'regex': '.*',
                                'hidden': True
                            }
                        }
                    },
                    'activation_date': {
                        'order': 3,
                        'description': 'When would you like to have your OpenReview submission portal opened?',
                        'value': {
                            'param': {
                                'type': 'date',
                                'range': [ 0, 9999999999999 ],
                                'deletable': True
                            }
                        }
                    },
                    'submission_name': {
                        'order': 4,
                        'description': 'Submission name',
                        'value': {
                            'param': {
                                'type': 'string',
                                'maxLength': 100,
                                'regex': '^[a-zA-Z0-9_]*$',
                                'default': 'Submission'
                            }
                        }
                    },
                    'authors_name': {
                        'order': 5,
                        'description': 'Author\'s group name',
                        'value': {
                            'param': {
                                'type': 'string',
                                'maxLength': 100,
                                'regex': '.*',
                                'hidden': True,
                                'default': 'Authors'
                            }
                        }
                    },
                    'reviewers_name': {
                        'order': 6,
                        'description': 'Reviewer\'s group name',
                        'value': {
                            'param': {
                                'type': 'string',
                                'maxLength': 100,
                                'regex': '.*',
                                'hidden': True,
                                'default': 'Authors'
                            }
                        }
                    }
                },
                'domain': '${1/content/venue_id/value}',
                'invitation': {
                    'id': '${2/content/venue_id/value}/-/${2/content/submission_name/value}_Change_After_Deadline',
                    'invitees': ['${3/content/venue_id/value}/Automated_Administrator'],
                    'signatures': ['${3/content/venue_id/value}'],
                    'readers': ['everyone'],
                    'writers': ['${3/content/venue_id/value}'],
                    'cdate': '${2/content/activation_date/value}',
                    'dateprocesses': [{
                        'dates': ["#{4/cdate}", self.update_date_string],
                        'script': self.get_process_content('../process/post_submission_process.py')
                    }],
                    'edit': {
                        'signatures': ['${4/content/venue_id/value}'],
                        'readers': ['${4/content/venue_id/value}', '${4/content/venue_id/value}/${4/content/submission_name/value}/${{2/note/id}/number}/${4/content/authors_name/value}'],
                        'writers': ['${4/content/venue_id/value}'],
                        'note': {
                            'id': {
                                'param': {
                                    'withInvitation': '${6/content/venue_id/value}/-/${6/content/submission_name/value}',
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
                            'signatures': [ '${5/content/venue_id/value}/${5/content/submission_name/value}/${{2/id}/number}/${5/content/authors_name/value}'],
                            'readers': [
                                '${5/content/venue_id/value}',
                                '${5/content/venue_id/value}/${5/content/submission_name/value}/${{2/id}/number}/${5/content/reviewers_name/value}',
                                '${5/content/venue_id/value}/${5/content/submission_name/value}/${{2/id}/number}/${5/content/authors_name/value}'
                            ],
                            'writers': [
                                '${5/content/venue_id/value}',
                                '${5/content/venue_id/value}/${5/content/submission_name/value}/${{2/id}/number}/${5/content/authors_name/value}'
                            ],
                            'content': {
                                'authors': {
                                    'readers': ['${7/content/venue_id/value}', '${7/content/venue_id/value}/${7/content/submission_name/value}/${{4/id}/number}/${7/content/authors_name/value}']
                                },
                                'authorids': {
                                    'readers': ['${7/content/venue_id/value}', '${7/content/venue_id/value}/${7/content/submission_name/value}/${{4/id}/number}/${7/content/authors_name/value}']
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
                        }
                    }
                }
            }
        )

        self.post_invitation_edit(invitation)

    def setup_review_template_invitation(self):

        invitation = Invitation(id='openreview.net/Support/Simple_Dual_Anonymous/Venue_Configuration_Request/-/Review',
            invitees=['active_venues'],
            readers=['everyone'],
            writers=['openreview.net/Support'],
            signatures=['openreview.net/Support'],
            process=self.get_process_content('process/review_template_process.py'),
            edit = {
                'signatures' : {
                    'param': {
                        'items': [
                            { 'prefix': '~.*', 'optional': True },
                            { 'value': 'openreview.net/Support', 'optional': True }
                        ]
                    }
                },
                'readers': ['openreview.net/Support'],
                'writers': ['openreview.net/Support'],
                'content': {
                    'venue_id': {
                        'order': 1,
                        'description': 'Venue Id',
                        'value': {
                            'param': {
                                'type': 'string',
                                'maxLength': 100,
                                'regex': '.*',
                                'hidden': True
                            }
                        }
                    },
                    'name': {
                        'order': 3,
                        'description': 'Name for this step, use underscores to represent spaces. Default is Official_Review. This name will be shown in the button users will click to perform this step.',
                        'value': {
                            'param': {
                                'type': 'string',
                                'maxLength': 100,
                                'regex': '^[a-zA-Z0-9_]*$',
                                'default': 'Official_Review'
                            }
                        }
                    },
                    'activation_date': {
                        'order': 4,
                        'description': 'When should the reviewing of submissions begin?',
                        'value': {
                            'param': {
                                'type': 'date',
                                'range': [ 0, 9999999999999 ],
                                'deletable': True
                            }
                        }
                    },
                    'due_date': {
                        'order': 5,
                        'description': 'By when should the reviews be in the system? This is the official, soft deadline reviewers will see.',
                        'value': {
                            'param': {
                                'type': 'date',
                                'range': [ 0, 9999999999999 ],
                                'optional': True,
                                'deletable': True
                            }
                        }
                    },
                    'submission_name': {
                        'order': 3,
                        'description': 'Submission name',
                        'value': {
                            'param': {
                                'type': 'string',
                                'maxLength': 100,
                                'regex': '^[a-zA-Z0-9_]*$',
                                'default': 'Submission'
                            }
                        }
                    }
                },
                'domain': '${1/content/venue_id/value}',
                'invitation': {
                    'id': '${2/content/venue_id/value}/-/${2/content/name/value}',
                    'invitees': ['${3/content/venue_id/value}'],
                    'signatures': ['${3/content/venue_id/value}'],
                    'readers': ['${3/content/venue_id/value}'],
                    'writers': ['${3/content/venue_id/value}'],
                    'cdate': '${2/content/activation_date/value}',
                    'dateprocesses': [{
                        'dates': ["#{4/edit/invitation/cdate}", self.update_date_string],
                        'script': self.invitation_edit_process
                    }],
                    'content': {
                        'email_program_chairs': {
                            'value': False
                        },
                        'review_process_script': {
                            'value': self.get_process_content('../process/review_process.py')
                        }
                    },
                    'edit': {
                        'signatures': ['${4/content/venue_id/value}'],
                        'readers': ['${4/content/venue_id/value}'],
                        'writers': ['${4/content/venue_id/value}'],
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
                            'id': '${4/content/venue_id/value}/${4/content/submission_name/value}/${2/content/noteNumber/value}/-/${4/content/name/value}',
                            'signatures': ['${5/content/venue_id/value}'],
                            'readers': ['everyone'],
                            'writers': ['${5/content/venue_id/value}'],
                            'invitees': ['${5/content/venue_id/value}', "${5/content/venue_id/value}/${5/content/submission_name/value}/${3/content/noteNumber/value}/Reviewers"],
                            'maxReplies': 1,
                            'cdate': '${4/content/activation_date/value}',
                            'duedate': '${4/content/due_date/value}',
                            'expdate': '${4/content/due_date/value}+1800000',
                            'process': '''def process(client, edit, invitation):
    meta_invitation = client.get_invitation(invitation.invitations[0])
    script = meta_invitation.content['review_process_script']['value']
    funcs = {
        'openreview': openreview
    }
    exec(script, funcs)
    funcs['process'](client, edit, invitation)''',
                            'edit': {
                                'signatures': {
                                    'param': {
                                        'items': [
                                            { 'prefix': '${9/content/venue_id/value}/${9/content/submission_name/value}/${7/content/noteNumber/value}/Reviewer_.*', 'optional': True}
                                        ]
                                    }
                                },
                                'readers': ['${2/note/readers}'],
                                'nonreaders': ['${2/note/nonreaders}'],
                                'writers': ['${6/content/venue_id/value}'],
                                'note': {
                                    'id': {
                                        'param': {
                                            'withInvitation': '${8/content/venue_id/value}/${8/content/submission_name/value}/${6/content/noteNumber/value}/-/${8/content/name/value}',
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
                                    'readers': [
                                        '${7/content/venue_id/value}/Program_Chairs',
                                        '${3/signatures}'
                                    ],
                                    'nonreaders': ['${7/content/venue_id/value}/${7/content/submission_name/value}/${5/content/noteNumber/value}/Authors'],
                                    'writers': ['${7/content/venue_id/value}', '${3/signatures}'],
                                    'content': {
                                        'title': {
                                            'order': 1,
                                            'description': 'Brief summary of your review.',
                                            'value': {
                                                'param': {
                                                    'type': 'string',
                                                    'regex': '.{0,500}',
                                                }
                                            }
                                        },
                                        'review': {
                                            'order': 2,
                                            'description': 'Please provide an evaluation of the quality, clarity, originality and significance of this work, including a list of its pros and cons (max 200000 characters). Add formatting using Markdown and formulas using LaTeX. For more information see https://openreview.net/faq',
                                            'value': {
                                                'param': {
                                                    'type': 'string',
                                                    'maxLength': 200000,
                                                    'markdown': True,
                                                    'input': 'textarea'
                                                }
                                            }
                                        },
                                        'rating': {
                                            'order': 3,
                                            'value': {
                                                'param': {
                                                    'type': 'integer',
                                                    'enum': [
                                                        { 'value': 10, 'description': '10: Top 5% of accepted papers, seminal paper' },
                                                        { 'value': 9, 'description': '9: Top 15% of accepted papers, strong accept' },
                                                        { 'value': 8, 'description': '8: Top 50% of accepted papers, clear accept' },
                                                        { 'value': 7, 'description': '7: Good paper, accept' },
                                                        { 'value': 6, 'description': '6: Marginally above acceptance threshold' },
                                                        { 'value': 5, 'description': '5: Marginally below acceptance threshold' },
                                                        { 'value': 4, 'description': '4: Ok but not good enough - rejection' },
                                                        { 'value': 3, 'description': '3: Clear rejection' },
                                                        { 'value': 2, 'description': '2: Strong rejection' },
                                                        { 'value': 1, 'description': '1: Trivial or wrong' }
                                                    ],
                                                    'input': 'radio'
                                                }
                                            }
                                        },
                                        'confidence': {
                                            'order': 4,
                                            'value': {
                                                'param': {
                                                    'type': 'integer',
                                                    'enum': [
                                                        { 'value': 5, 'description': '5: The reviewer is absolutely certain that the evaluation is correct and very familiar with the relevant literature' },
                                                        { 'value': 4, 'description': '4: The reviewer is confident but not absolutely certain that the evaluation is correct' },
                                                        { 'value': 3, 'description': '3: The reviewer is fairly confident that the evaluation is correct' },
                                                        { 'value': 2, 'description': '2: The reviewer is willing to defend the evaluation, but it is quite likely that the reviewer did not understand central parts of the paper' },
                                                        { 'value': 1, 'description': '1: The reviewer\'s evaluation is an educated guess' }
                                                    ],
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

        self.post_invitation_edit(invitation)

    def setup_official_comment_template_invitation(self):

        invitation = Invitation(id='openreview.net/Support/Simple_Dual_Anonymous/Venue_Configuration_Request/-/Comment',
            invitees=['active_venues'],
            readers=['everyone'],
            writers=['openreview.net/Support'],
            signatures=['openreview.net/Support'],
            process=self.get_process_content('process/comment_template_process.py'),
            edit = {
                'signatures' : {
                    'param': {
                        'items': [
                            { 'prefix': '~.*', 'optional': True },
                            { 'value': 'openreview.net/Support', 'optional': True }
                        ]
                    }
                },
                'readers': ['openreview.net/Support'],
                'writers': ['openreview.net/Support'],
                'content': {
                    'venue_id': {
                        'order': 1,
                        'description': 'Venue Id',
                        'value': {
                            'param': {
                                'type': 'string',
                                'maxLength': 100,
                                'regex': '.*',
                                'hidden': True
                            }
                        }
                    },
                    'name': {
                        'order': 3,
                        'description': 'Name for this step, use underscores to represent spaces. Default is Official_Comment. This name will be shown in the button users will click to perform this step.',
                        'value': {
                            'param': {
                                'type': 'string',
                                'maxLength': 100,
                                'regex': '^[a-zA-Z0-9_]*$',
                                'default': 'Official_Comment'
                            }
                        }
                    },
                    'activation_date': {
                        'order': 4,
                        'description': 'When should users be able to post comments?',
                        'value': {
                            'param': {
                                'type': 'date',
                                'range': [ 0, 9999999999999 ],
                                'deletable': True
                            }
                        }
                    },
                    'expiration_date': {
                        'order': 5,
                        'value': {
                            'param': {
                                'type': 'date',
                                'range': [ 0, 9999999999999 ],
                                'optional': True,
                                'deletable': True
                            }
                        }
                    },
                    'submission_name': {
                        'order': 3,
                        'description': 'Submission name',
                        'value': {
                            'param': {
                                'type': 'string',
                                'maxLength': 100,
                                'regex': '^[a-zA-Z0-9_]*$',
                                'default': 'Submission'
                            }
                        }
                    }
                },
                'domain': '${1/content/venue_id/value}',
                'invitation': {
                    'id': '${2/content/venue_id/value}/-/${2/content/name/value}',
                    'invitees': ['${3/content/venue_id/value}'],
                    'signatures': ['${3/content/venue_id/value}'],
                    'readers': ['${3/content/venue_id/value}'],
                    'writers': ['${3/content/venue_id/value}'],
                    'cdate': '${2/content/activation_date/value}',
                    'dateprocesses': [{
                        'dates': ["#{4/edit/invitation/cdate}", self.update_date_string],
                        'script': self.invitation_edit_process
                    }],
                    'content': {
                        'email_program_chairs': {
                            'value': False
                        },
                        'comment_process_script': {
                            'value': self.get_process_content('../process/comment_process.py')
                        }
                    },
                    'edit': {
                        'signatures': ['${4/content/venue_id/value}'],
                        'readers': ['${4/content/venue_id/value}'],
                        'writers': ['${4/content/venue_id/value}'],
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
                            'id': '${4/content/venue_id/value}/${4/content/submission_name/value}/${2/content/noteNumber/value}/-/${4/content/name/value}',
                            'signatures': ['${5/content/venue_id/value}'],
                            'readers': ['everyone'],
                            'writers': ['${5/content/venue_id/value}'],
                            'invitees': ['${5/content/venue_id/value}', "${5/content/venue_id/value}/${5/content/submission_name/value}/${3/content/noteNumber/value}/Reviewers", "${5/content/venue_id/value}/${5/content/submission_name/value}/${3/content/noteNumber/value}/Authors"],
                            'cdate': '${4/content/activation_date/value}',
                            'expdate': '${4/content/expiration_date/value}',
                            'process': '''def process(client, edit, invitation):
    meta_invitation = client.get_invitation(invitation.invitations[0])
    script = meta_invitation.content['comment_process_script']['value']
    funcs = {
        'openreview': openreview
    }
    exec(script, funcs)
    funcs['process'](client, edit, invitation)''',
                            'edit': {
                                'signatures': {
                                    'param': {
                                        'items': [
                                            { 'value': '${9/content/venue_id/value}/Program_Chairs', 'optional': True },
                                            { 'prefix': '${9/content/venue_id/value}/${9/content/submission_name/value}/${7/content/noteNumber/value}/Reviewer_.*', 'optional': True },
                                            { 'value': '${9/content/venue_id/value}/${9/content/submission_name/value}/${7/content/noteNumber/value}/Authors', 'optional': True }
                                        ]
                                    }
                                },
                                'readers': ['${2/note/readers}'],
                                'writers': ['${6/content/venue_id/value}'],
                                'note': {
                                    'id': {
                                        'param': {
                                            'withInvitation': '${8/content/venue_id/value}/${8/content/submission_name/value}/${6/content/noteNumber/value}/-/${8/content/name/value}',
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
                                    'readers': {
                                        'param': {
                                            'items': [
                                                { 'value': '${10/content/venue_id/value}/Program_Chairs', 'optional': False },
                                                { 'value': '${10/content/venue_id/value}/${10/content/submission_name/value}/${8/content/noteNumber/value}/Reviewers', 'optional': True },
                                                { 'prefix': '${10/content/venue_id/value}/${10/content/submission_name/value}/${8/content/noteNumber/value}/Reviewer_.*', 'optional': True },
                                                { 'value': '${10/content/venue_id/value}/${10/content/submission_name/value}/${8/content/noteNumber/value}/Authors', 'optional': True }
                                            ]
                                        }
                                    },
                                    'writers': ['${7/content/venue_id/value}', '${3/signatures}'],
                                    'content': {
                                        'title': {
                                            'order': 1,
                                            'description': '(Optional) Brief summary of your comment.',
                                            'value': {
                                                'param': {
                                                    'type': 'string',
                                                    'maxLength': 500,
                                                    'optional': True,
                                                    'deletable': True
                                                }
                                            }
                                        },
                                        'comment': {
                                            'order': 2,
                                            'description': 'Your comment or reply (max 5000 characters). Add formatting using Markdown and formulas using LaTeX. For more information see https://openreview.net/faq',
                                            'value': {
                                                'param': {
                                                    'type': 'string',
                                                    'maxLength': 5000,
                                                    'markdown': True,
                                                    'input': 'textarea'
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

        self.post_invitation_edit(invitation)

    def setup_decision_template_invitation(self):

        invitation = Invitation(id='openreview.net/Support/Simple_Dual_Anonymous/Venue_Configuration_Request/-/Decision',
            invitees=['active_venues'],
            readers=['everyone'],
            writers=['openreview.net/Support'],
            signatures=['openreview.net/Support'],
            process=self.get_process_content('process/decision_template_process.py'),
            edit = {
                'signatures' : {
                    'param': {
                        'items': [
                            { 'prefix': '~.*', 'optional': True },
                            { 'value': 'openreview.net/Support', 'optional': True }
                        ]
                    }
                },
                'readers': ['openreview.net/Support'],
                'writers': ['openreview.net/Support'],
                'content': {
                    'venue_id': {
                        'order': 1,
                        'description': 'Venue Id',
                        'value': {
                            'param': {
                                'type': 'string',
                                'maxLength': 100,
                                'regex': '.*',
                                'hidden': True
                            }
                        }
                    },
                    'name': {
                        'order': 3,
                        'description': 'Name for this step, use underscores to represent spaces. Default is Decision. This name will be shown in the button users will click to perform this step.',
                        'value': {
                            'param': {
                                'type': 'string',
                                'maxLength': 100,
                                'regex': '^[a-zA-Z0-9_]*$',
                                'default': 'Decision'
                            }
                        }
                    },
                    'activation_date': {
                        'order': 4,
                        'description': 'When should the reviewing of submissions begin?',
                        'value': {
                            'param': {
                                'type': 'date',
                                'range': [ 0, 9999999999999 ],
                                'deletable': True
                            }
                        }
                    },
                    'due_date': {
                        'order': 5,
                        'description': 'By when should the reviews be in the system? This is the official, soft deadline reviewers will see.',
                        'value': {
                            'param': {
                                'type': 'date',
                                'range': [ 0, 9999999999999 ],
                                'optional': True,
                                'deletable': True
                            }
                        }
                    },
                    'submission_name': {
                        'order': 3,
                        'description': 'Submission name',
                        'value': {
                            'param': {
                                'type': 'string',
                                'maxLength': 100,
                                'regex': '^[a-zA-Z0-9_]*$',
                                'default': 'Submission'
                            }
                        }
                    }
                },
                'domain': '${1/content/venue_id/value}',
                'invitation': {
                    'id': '${2/content/venue_id/value}/-/${2/content/name/value}',
                    'invitees': ['${3/content/venue_id/value}'],
                    'signatures': ['${3/content/venue_id/value}'],
                    'readers': ['${3/content/venue_id/value}'],
                    'writers': ['${3/content/venue_id/value}'],
                    'cdate': '${2/content/activation_date/value}',
                    'dateprocesses': [{
                        'dates': ["#{4/edit/invitation/cdate}", self.update_date_string],
                        'script': self.get_process_content('../process/invitation_edit_process_decision.py'),
                    }],
                    'content': {
                        'email_pcs': {
                            'value': False
                        },
                        'email_authors': {
                            'value': False
                        },
                        'decision_field_name': {
                            'value': 'decision'
                        },
                        'decision_process_script': {
                            'value': self.get_process_content('../process/decision_process.py')
                        }
                    },
                    'edit': {
                        'signatures': ['${4/content/venue_id/value}'],
                        'readers': ['${4/content/venue_id/value}'],
                        'writers': ['${4/content/venue_id/value}'],
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
                            'id': '${4/content/venue_id/value}/${4/content/submission_name/value}/${2/content/noteNumber/value}/-/${4/content/name/value}',
                            'signatures': ['${5/content/venue_id/value}'],
                            'readers': ['everyone'],
                            'writers': ['${5/content/venue_id/value}'],
                            'invitees': ['${5/content/venue_id/value}', self.support_group_id],
                            'maxReplies': 1,
                            'minReplies': 1,
                            'cdate': '${4/content/activation_date/value}',
                            'duedate': '${4/content/due_date/value}',
                            'expdate': '${4/content/due_date/value}+1800000',
                            'process': '''def process(client, edit, invitation):
    meta_invitation = client.get_invitation(invitation.invitations[0])
    script = meta_invitation.content['decision_process_script']['value']
    funcs = {
        'openreview': openreview
    }
    exec(script, funcs)
    funcs['process'](client, edit, invitation)''',
                            'edit': {
                                'signatures': ['${6/content/venue_id/value}/Program_Chairs'],
                                'readers': ['${2/note/readers}'],
                                'nonreaders': ['${2/note/nonreaders}'],
                                'writers': ['${6/content/venue_id/value}'],
                                'note': {
                                    'id': {
                                        'param': {
                                            'withInvitation': '${8/content/venue_id/value}/${8/content/submission_name/value}/${6/content/noteNumber/value}/-/${8/content/name/value}',
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
                                    'readers': [
                                        '${7/content/venue_id/value}/Program_Chairs'
                                    ],
                                    'nonreaders': ['${7/content/venue_id/value}/${7/content/submission_name/value}/${5/content/noteNumber/value}/Authors'],
                                    'writers': ['${7/content/venue_id/value}', '${3/signatures}'],
                                    'content': {
                                        'title': {
                                            'order': 1,
                                            'value': 'Paper Decision'
                                        },
                                        'decision': {
                                            'order': 2,
                                            'description': 'Decision',
                                            'value': {
                                                'param': {
                                                    'type': 'string',
                                                    'enum': [
                                                        'Accept (Oral)',
                                                        'Accept (Poster)',
                                                        'Reject'
                                                    ],
                                                    'input': 'radio'
                                                }
                                            }
                                        },
                                        'comment': {
                                            'order': 3,
                                            'value': {
                                                'param': {
                                                    'type': 'string',
                                                    'markdown': True,
                                                    'input': 'textarea',
                                                    'optional': True,
                                                    'deletable': True
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

        self.post_invitation_edit(invitation)

    def setup_withdrawal_template_invitation(self):

        invitation = Invitation(id='openreview.net/Support/Simple_Dual_Anonymous/Venue_Configuration_Request/-/Withdrawal',
            invitees=['active_venues'],
            readers=['everyone'],
            writers=['openreview.net/Support'],
            signatures=['openreview.net/Support'],
            process=self.get_process_content('process/withdrawal_template_process.py'),
            edit = {
                'signatures' : {
                    'param': {
                        'items': [
                            { 'prefix': '~.*', 'optional': True },
                            { 'value': 'openreview.net/Support', 'optional': True }
                        ]
                    }
                },
                'readers': ['openreview.net/Support'],
                'writers': ['openreview.net/Support'],
                'content': {
                    'venue_id': {
                        'order': 1,
                        'description': 'Venue Id',
                        'value': {
                            'param': {
                                'type': 'string',
                                'maxLength': 100,
                                'regex': '.*',
                                'hidden': True
                            }
                        }
                    },
                    'name': {
                        'order': 2,
                        'description': 'Name for this step, use underscores to represent spaces. Default is Withdrawal. This name will be shown in the button users will click to perform this step.',
                        'value': {
                            'param': {
                                'type': 'string',
                                'maxLength': 100,
                                'regex': '^[a-zA-Z0-9_]*$',
                                'default': 'Withdrawal'
                            }
                        }
                    },
                    'activation_date': {
                        'order': 3,
                        'value': {
                            'param': {
                                'type': 'date',
                                'range': [ 0, 9999999999999 ],
                                'deletable': True
                            }
                        }
                    },
                    'submission_name': {
                        'order': 4,
                        'description': 'Submission name',
                        'value': {
                            'param': {
                                'type': 'string',
                                'maxLength': 100,
                                'regex': '^[a-zA-Z0-9_]*$',
                                'default': 'Submission'
                            }
                        }
                    }
                },
                'domain': '${1/content/venue_id/value}',
                'invitation': {
                    'id': '${2/content/venue_id/value}/-/${2/content/name/value}',
                    'invitees': ['${3/content/venue_id/value}'],
                    'signatures': ['${3/content/venue_id/value}'],
                    'readers': ['${3/content/venue_id/value}'],
                    'writers': ['${3/content/venue_id/value}'],
                    'cdate': '${2/content/activation_date/value}',
                    'dateprocesses': [{
                        'dates': ["#{4/edit/invitation/cdate}", self.update_date_string],
                        'script': self.invitation_edit_process
                    }],
                    'content': {
                        'withdrawal_process_script': {
                            'value': self.get_process_content('../process/withdrawal_submission_process.py')
                        }
                    },
                    'edit': {
                        'signatures': ['${4/content/venue_id/value}'],
                        'readers': ['${4/content/venue_id/value}'],
                        'writers': ['${4/content/venue_id/value}'],
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
                            'id': '${4/content/venue_id/value}/${4/content/submission_name/value}/${2/content/noteNumber/value}/-/${4/content/name/value}',
                            'invitees': ['${5/content/venue_id/value}', '${5/content/venue_id/value}/${5/content/submission_name/value}/${3/content/noteNumber/value}/Authors'],
                            'readers': ['everyone'],
                            'writers': ['${5/content/venue_id/value}'],
                            'signatures': ['${5/content/venue_id/value}'],
                            'maxReplies': 1,
                            'process': '''def process(client, edit, invitation):
    meta_invitation = client.get_invitation(invitation.invitations[0])
    script = meta_invitation.content['withdrawal_process_script']['value']
    funcs = {
        'openreview': openreview,
        'datetime': datetime
    }
    exec(script, funcs)
    funcs['process'](client, edit, invitation)''',
                            'cdate': '${4/content/activation_date/value}',
                            'edit': {
                                'signatures': {
                                    'param': {
                                        'items': [
                                            { 'value': '${9/content/venue_id/value}/${9/content/submission_name/value}/${7/content/noteNumber/value}/Authors' }
                                        ]
                                    }
                                },
                                'readers': ['${6/content/venue_id/value}/Program_Chairs', '${6/content/venue_id/value}/${6/content/submission_name/value}/${4/content/noteNumber/value}/Reviewers', '${6/content/venue_id/value}/${6/content/submission_name/value}/${4/content/noteNumber/value}/Authors'],
                                'writers': ['${6/content/venue_id/value}', '${6/content/venue_id/value}/${6/content/submission_name/value}/${4/content/noteNumber/value}/Authors'],
                                'note': {
                                    'forum': '${4/content/noteId/value}',
                                    'replyto': '${4/content/noteId/value}',
                                    'signatures': ['${3/signatures}'],
                                    'readers': ['${3/readers}'],
                                    'writers': [ '${7/content/venue_id/value}' ],
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
                }
            }
        )

        self.post_invitation_edit(invitation)

    def setup_withdrawn_submission_template_invitation(self):

        invitation = Invitation(id='openreview.net/Support/Simple_Dual_Anonymous/Venue_Configuration_Request/-/Withdrawn_Submission',
            invitees=['active_venues'],
            readers=['everyone'],
            writers=['openreview.net/Support'],
            signatures=['openreview.net/Support'],
            edit = {
                'signatures' : {
                    'param': {
                        'items': [
                            { 'prefix': '~.*', 'optional': True },
                            { 'value': 'openreview.net/Support', 'optional': True }
                        ]
                    }
                },
                'readers': ['openreview.net/Support'],
                'writers': ['openreview.net/Support'],
                'content': {
                    'venue_id': {
                        'order': 1,
                        'description': 'Venue Id',
                        'value': {
                            'param': {
                                'type': 'string',
                                'maxLength': 100,
                                'regex': '.*',
                                'hidden': True
                            }
                        }
                    },
                    'submission_name': {
                        'order': 4,
                        'description': 'Submission name',
                        'value': {
                            'param': {
                                'type': 'string',
                                'maxLength': 100,
                                'regex': '^[a-zA-Z0-9_]*$',
                                'default': 'Submission'
                            }
                        }
                    }
                },
                'domain': '${1/content/venue_id/value}',
                'invitation': {
                    'id': '${2/content/venue_id/value}/-/Withdrawn_${2/content/submission_name/value}',
                    'invitees': ['${3/content/venue_id/value}'],
                    'noninvitees': ['${3/content/venue_id/value}/Program_Chairs'],
                    'signatures': ['${3/content/venue_id/value}'],
                    'readers': ['everyone'],
                    'writers': ['${3/content/venue_id/value}'],
                    'edit': {
                        'signatures': ['${4/content/venue_id/value}'],
                        'readers': ['${4/content/venue_id/value}'],
                        'writers': ['${4/content/venue_id/value}'],
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
                                    'withInvitation': '${6/content/venue_id/value}/-/${6/content/submission_name/value}',
                                }
                            },
                            'content': {
                                'authors': {
                                    'readers' : ['${7/content/venue_id/value}', '${7/content/venue_id/value}/${7/content/submission_name/value}/${{4/id}/number}/Authors']
                                },
                                'authorids': {
                                    'readers' : ['${7/content/venue_id/value}', '${7/content/venue_id/value}/${7/content/submission_name/value}/${{4/id}/number}/Authors']
                                },
                                'venue': {
                                    # 'value': tools.pretty_id(self.venue.get_withdrawn_submission_venue_id())
                                    'value': '${6/content/venue_id/value}/-/Withdrawn_${6/content/submission_name/value}' # how to get pretty id here??
                                },
                                'venueid': {
                                    'value': '${6/content/venue_id/value}/Withdrawn_${6/content/submission_name/value}'
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
                            },
                            'readers' : [
                                '${5/content/venue_id/value}/Program_Chairs',
                                '${5/content/venue_id/value}/${5/content/submission_name/value}/${{2/id}/number}/Reviewers',
                                '${5/content/venue_id/value}/${5/content/submission_name/value}/${{2/id}/number}/Authors'
                            ]
                        }
                    },
                    'process': self.get_process_content(('../process/withdrawn_submission_process.py'))
                }
            }
        )

        self.post_invitation_edit(invitation)

    def setup_withdrawal_expiration_template_invitation(self):

        invitation = Invitation(id='openreview.net/Support/Simple_Dual_Anonymous/Venue_Configuration_Request/-/Withdraw_Expiration',
            invitees=['active_venues'],
            readers=['everyone'],
            writers=['openreview.net/Support'],
            signatures=['openreview.net/Support'],
            edit = {
                'signatures' : {
                    'param': {
                        'items': [
                            { 'prefix': '~.*', 'optional': True },
                            { 'value': 'openreview.net/Support', 'optional': True }
                        ]
                    }
                },
                'readers': ['openreview.net/Support'],
                'writers': ['openreview.net/Support'],
                'content': {
                    'venue_id': {
                        'order': 1,
                        'description': 'Venue Id',
                        'value': {
                            'param': {
                                'type': 'string',
                                'maxLength': 100,
                                'regex': '.*',
                                'hidden': True
                            }
                        }
                    },
                    'submission_name': {
                        'order': 4,
                        'description': 'Submission name',
                        'value': {
                            'param': {
                                'type': 'string',
                                'maxLength': 100,
                                'regex': '^[a-zA-Z0-9_]*$',
                                'default': 'Submission'
                            }
                        }
                    }
                },
                'domain': '${1/content/venue_id/value}',
                'invitation': {
                    'id': '${2/content/venue_id/value}/-/Withdraw_Expiration',
                    'invitees': ['${3/content/venue_id/value}'],
                    'signatures': ['${3/content/venue_id/value}'],
                    'readers': ['everyone'],
                    'writers': ['${3/content/venue_id/value}'],
                    'edit': {
                        'signatures': ['${4/content/venue_id/value}'],
                        'readers': ['${4/content/venue_id/value}'],
                        'writers': ['${4/content/venue_id/value}'],
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
                                    'regex': '${6/content/venue_id/value}/${6/content/submission_name/value}',
                                }
                            },
                            'signatures': ['${5/content/venue_id/value}'],
                            'expdate': {
                                'param': {
                                    'range': [ 0, 9999999999999 ],
                                    'deletable': True
                                }
                            }

                        }
                    }
                }
            }
        )

        self.post_invitation_edit(invitation)

    def setup_withdrawal_reversion_template_invitation(self):

        invitation = Invitation(id='openreview.net/Support/Simple_Dual_Anonymous/Venue_Configuration_Request/-/Withdrawal_Reversion',
            invitees=['active_venues'],
            readers=['everyone'],
            writers=['openreview.net/Support'],
            signatures=['openreview.net/Support'],
            edit = {
                'signatures' : {
                    'param': {
                        'items': [
                            { 'prefix': '~.*', 'optional': True },
                            { 'value': 'openreview.net/Support', 'optional': True }
                        ]
                    }
                },
                'readers': ['openreview.net/Support'],
                'writers': ['openreview.net/Support'],
                'content': {
                    'venue_id': {
                        'order': 1,
                        'description': 'Venue Id',
                        'value': {
                            'param': {
                                'type': 'string',
                                'maxLength': 100,
                                'regex': '.*',
                                'hidden': True
                            }
                        }
                    },
                    'submission_name': {
                        'order': 2,
                        'description': 'Submission name',
                        'value': {
                            'param': {
                                'type': 'string',
                                'maxLength': 100,
                                'regex': '^[a-zA-Z0-9_]*$',
                                'default': 'Submission'
                            }
                        }
                    }
                },
                'domain': '${1/content/venue_id/value}',
                'invitation': {
                    'id': '${2/content/venue_id/value}/-/Withdrawal_Reversion',
                    'invitees': ['${3/content/venue_id/value}'],
                    'signatures': ['${3/content/venue_id/value}'],
                    'readers': ['${3/content/venue_id/value}'],
                    'writers': ['${3/content/venue_id/value}'],
                    'content': {
                        'withdrawal_reversion_process_script': {
                            'value': self.get_process_content('../process/withdrawal_reversion_submission_process.py')
                        }
                    },
                    'edit': {
                        'signatures': ['${4/content/venue_id/value}'],
                        'readers': ['${4/content/venue_id/value}'],
                        'writers': ['${4/content/venue_id/value}'],
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
                            'id': '${4/content/venue_id/value}/${4/content/submission_name/value}/${{2/content/noteId/value}/number}/-/Withdrawal_Reversion',
                            'invitees': ['${5/content/venue_id/value}'],
                            'readers': ['everyone'],
                            'writers': ['${5/content/venue_id/value}'],
                            'signatures': ['${5/content/venue_id/value}'],
                            'maxReplies': 1,
                            'process': '''def process(client, edit, invitation):
    meta_invitation = client.get_invitation(invitation.invitations[0])
    script = meta_invitation.content['withdrawal_reversion_process_script']['value']
    funcs = {
        'openreview': openreview,
        'datetime': datetime
    }
    exec(script, funcs)
    funcs['process'](client, edit, invitation)''',
                            'edit': {
                                'signatures': {
                                    'param': {
                                        'items': [
                                            { 'value': '${9/content/venue_id/value}/Program_Chairs' }
                                        ]
                                    }
                                },
                                'readers': ['${6/content/venue_id/value}/Program_Chairs', '${6/content/venue_id/value}/${6/content/submission_name/value}/${{4/content/noteId/value}/number}/Reviewers', '${6/content/venue_id/value}/${6/content/submission_name/value}/${{4/content/noteId/value}/number}/Authors'],
                                'writers': ['${6/content/venue_id/value}'],
                                'note': {
                                    'forum': '${4/content/noteId/value}',
                                    'replyto': '${4/content/withdrawalId/value}',
                                    'signatures': ['${3/signatures}'],
                                    'readers': ['${3/readers}'],
                                    'writers': [ '${7/content/venue_id/value}' ],
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
                                            'description': 'Please confirm to reverse the withdrawal.',
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
                }
            }
        )

        self.post_invitation_edit(invitation)

    def setup_desk_rejection_template_invitation(self):

        invitation = Invitation(id='openreview.net/Support/Simple_Dual_Anonymous/Venue_Configuration_Request/-/Desk_Rejection',
            invitees=['active_venues'],
            readers=['everyone'],
            writers=['openreview.net/Support'],
            signatures=['openreview.net/Support'],
            process=self.get_process_content('process/desk_rejection_template_process.py'),
            edit = {
                'signatures' : {
                    'param': {
                        'items': [
                            { 'prefix': '~.*', 'optional': True },
                            { 'value': 'openreview.net/Support', 'optional': True }
                        ]
                    }
                },
                'readers': ['openreview.net/Support'],
                'writers': ['openreview.net/Support'],
                'content': {
                    'venue_id': {
                        'order': 1,
                        'description': 'Venue Id',
                        'value': {
                            'param': {
                                'type': 'string',
                                'maxLength': 100,
                                'regex': '.*',
                                'hidden': True
                            }
                        }
                    },
                    'name': {
                        'order': 2,
                        'description': 'Name for this step, use underscores to represent spaces. Default is Desk_Rejection. This name will be shown in the button users will click to perform this step.',
                        'value': {
                            'param': {
                                'type': 'string',
                                'maxLength': 100,
                                'regex': '^[a-zA-Z0-9_]*$',
                                'default': 'Desk_Rejection'
                            }
                        }
                    },
                    'activation_date': {
                        'order': 3,
                        'value': {
                            'param': {
                                'type': 'date',
                                'range': [ 0, 9999999999999 ],
                                'deletable': True
                            }
                        }
                    },
                    'submission_name': {
                        'order': 4,
                        'description': 'Submission name',
                        'value': {
                            'param': {
                                'type': 'string',
                                'maxLength': 100,
                                'regex': '^[a-zA-Z0-9_]*$',
                                'default': 'Submission'
                            }
                        }
                    }
                },
                'domain': '${1/content/venue_id/value}',
                'invitation': {
                    'id': '${2/content/venue_id/value}/-/${2/content/name/value}',
                    'invitees': ['${3/content/venue_id/value}'],
                    'signatures': ['${3/content/venue_id/value}'],
                    'readers': ['${3/content/venue_id/value}'],
                    'writers': ['${3/content/venue_id/value}'],
                    'cdate': '${2/content/activation_date/value}',
                    'dateprocesses': [{
                        'dates': ["#{4/edit/invitation/cdate}", self.update_date_string],
                        'script': self.invitation_edit_process
                    }],
                    'content': {
                        'desk_rejection_process_script': {
                            'value': self.get_process_content('../process/desk_rejection_submission_process.py')
                        }
                    },
                    'edit': {
                        'signatures': ['${4/content/venue_id/value}'],
                        'readers': ['${4/content/venue_id/value}'],
                        'writers': ['${4/content/venue_id/value}'],
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
                            'id': '${4/content/venue_id/value}/${4/content/submission_name/value}/${2/content/noteNumber/value}/-/${4/content/name/value}',
                            'invitees': ['${5/content/venue_id/value}'],
                            'readers': ['everyone'],
                            'writers': ['${5/content/venue_id/value}'],
                            'signatures': ['${5/content/venue_id/value}'],
                            'maxReplies': 1,
                            'process': '''def process(client, edit, invitation):
    meta_invitation = client.get_invitation(invitation.invitations[0])
    script = meta_invitation.content['desk_rejection_process_script']['value']
    funcs = {
        'openreview': openreview,
        'datetime': datetime
    }
    exec(script, funcs)
    funcs['process'](client, edit, invitation)''',
                            'cdate': '${4/content/activation_date/value}',
                            'edit': {
                                'signatures': {
                                    'param': {
                                        'items': [
                                            { 'value': '${9/content/venue_id/value}/Program_Chairs' }
                                        ]
                                    }
                                },
                                'readers': ['${6/content/venue_id/value}/Program_Chairs', '${6/content/venue_id/value}/${6/content/submission_name/value}/${4/content/noteNumber/value}/Reviewers', '${6/content/venue_id/value}/${6/content/submission_name/value}/${4/content/noteNumber/value}/Authors'],
                                'writers': ['${6/content/venue_id/value}'],
                                'note': {
                                    'forum': '${4/content/noteId/value}',
                                    'replyto': '${4/content/noteId/value}',
                                    'signatures': ['${3/signatures}'],
                                    'readers': ['${3/readers}'],
                                    'writers': [ '${7/content/venue_id/value}' ],
                                    'content': {
                                        'title': {
                                            'order': 1,
                                            'description': 'Title',
                                            'value': {
                                                'param': {
                                                    'type': 'string',
                                                    'const': 'Submission Desk Rejected by Program Chairs'
                                                }
                                            }
                                        },
                                        'desk_reject_comments': {
                                            'order': 2,
                                            'description': 'Brief summary of reasons for marking this submission as desk rejected',
                                            'value': {
                                                'param': {
                                                    'type': 'string',
                                                    'maxLength': 10000,
                                                    'input': 'textarea'
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

        self.post_invitation_edit(invitation)

    def setup_desk_rejected_submission_template_invitation(self):

        invitation = Invitation(id='openreview.net/Support/Simple_Dual_Anonymous/Venue_Configuration_Request/-/Desk_Rejected_Submission',
            invitees=['active_venues'],
            readers=['everyone'],
            writers=['openreview.net/Support'],
            signatures=['openreview.net/Support'],
            edit = {
                'signatures' : {
                    'param': {
                        'items': [
                            { 'prefix': '~.*', 'optional': True },
                            { 'value': 'openreview.net/Support', 'optional': True }
                        ]
                    }
                },
                'readers': ['openreview.net/Support'],
                'writers': ['openreview.net/Support'],
                'content': {
                    'venue_id': {
                        'order': 1,
                        'description': 'Venue Id',
                        'value': {
                            'param': {
                                'type': 'string',
                                'maxLength': 100,
                                'regex': '.*',
                                'hidden': True
                            }
                        }
                    },
                    'submission_name': {
                        'order': 4,
                        'description': 'Submission name',
                        'value': {
                            'param': {
                                'type': 'string',
                                'maxLength': 100,
                                'regex': '^[a-zA-Z0-9_]*$',
                                'default': 'Submission'
                            }
                        }
                    }
                },
                'domain': '${1/content/venue_id/value}',
                'invitation': {
                    'id': '${2/content/venue_id/value}/-/Desk_Rejected_${2/content/submission_name/value}',
                    'invitees': ['${3/content/venue_id/value}'],
                    'noninvitees': ['${3/content/venue_id/value}/Program_Chairs'],
                    'signatures': ['${3/content/venue_id/value}'],
                    'readers': ['everyone'],
                    'writers': ['${3/content/venue_id/value}'],
                    'edit': {
                        'signatures': ['${4/content/venue_id/value}'],
                        'readers': ['${4/content/venue_id/value}'],
                        'writers': ['${4/content/venue_id/value}'],
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
                                    'withInvitation': '${6/content/venue_id/value}/-/${6/content/submission_name/value}',
                                }
                            },
                            'content': {
                                'authors': {
                                    'readers' : ['${7/content/venue_id/value}', '${7/content/venue_id/value}/${7/content/submission_name/value}/${{4/id}/number}/Authors']
                                },
                                'authorids': {
                                    'readers' : ['${7/content/venue_id/value}', '${7/content/venue_id/value}/${7/content/submission_name/value}/${{4/id}/number}/Authors']
                                },
                                'venue': {
                                    # 'value': tools.pretty_id(self.venue.get_withdrawn_submission_venue_id())
                                    'value': '${6/content/venue_id/value}/-/Desk_Rejected_${6/content/submission_name/value}' # how to get pretty id here??
                                },
                                'venueid': {
                                    'value': '${6/content/venue_id/value}/Withdrawn_${6/content/submission_name/value}'
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
                            },
                            'readers' : [
                                '${5/content/venue_id/value}/Program_Chairs',
                                '${5/content/venue_id/value}/${5/content/submission_name/value}/${{2/id}/number}/Reviewers',
                                '${5/content/venue_id/value}/${5/content/submission_name/value}/${{2/id}/number}/Authors'
                            ]
                        }
                    },
                    'process': self.get_process_content(('../process/desk_rejected_submission_process.py'))
                }
            }
        )

        self.post_invitation_edit(invitation)

    def setup_desk_reject_expiration_template_invitation(self):

        invitation = Invitation(id='openreview.net/Support/Simple_Dual_Anonymous/Venue_Configuration_Request/-/Desk_Reject_Expiration',
            invitees=['active_venues'],
            readers=['everyone'],
            writers=['openreview.net/Support'],
            signatures=['openreview.net/Support'],
            edit = {
                'signatures' : {
                    'param': {
                        'items': [
                            { 'prefix': '~.*', 'optional': True },
                            { 'value': 'openreview.net/Support', 'optional': True }
                        ]
                    }
                },
                'readers': ['openreview.net/Support'],
                'writers': ['openreview.net/Support'],
                'content': {
                    'venue_id': {
                        'order': 1,
                        'description': 'Venue Id',
                        'value': {
                            'param': {
                                'type': 'string',
                                'maxLength': 100,
                                'regex': '.*',
                                'hidden': True
                            }
                        }
                    },
                    'submission_name': {
                        'order': 2,
                        'description': 'Submission name',
                        'value': {
                            'param': {
                                'type': 'string',
                                'maxLength': 100,
                                'regex': '^[a-zA-Z0-9_]*$',
                                'default': 'Submission'
                            }
                        }
                    }
                },
                'domain': '${1/content/venue_id/value}',
                'invitation': {
                    'id': '${2/content/venue_id/value}/-/Desk_Reject_Expiration',
                    'invitees': ['${3/content/venue_id/value}'],
                    'signatures': ['${3/content/venue_id/value}'],
                    'readers': ['everyone'],
                    'writers': ['${3/content/venue_id/value}'],
                    'edit': {
                        'signatures': ['${4/content/venue_id/value}'],
                        'readers': ['${4/content/venue_id/value}'],
                        'writers': ['${4/content/venue_id/value}'],
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
                                    'regex': '${6/content/venue_id/value}/${6/content/submission_name/value}',
                                }
                            },
                            'signatures': ['${5/content/venue_id/value}'],
                            'expdate': {
                                'param': {
                                    'range': [ 0, 9999999999999 ],
                                    'deletable': True
                                }
                            }

                        }
                    }
                }
            }
        )

        self.post_invitation_edit(invitation)

    def setup_desk_rejection_reversion_template_invitation(self):

        invitation = Invitation(id='openreview.net/Support/Simple_Dual_Anonymous/Venue_Configuration_Request/-/Desk_Rejection_Reversion',
            invitees=['active_venues'],
            readers=['everyone'],
            writers=['openreview.net/Support'],
            signatures=['openreview.net/Support'],
            edit = {
                'signatures' : {
                    'param': {
                        'items': [
                            { 'prefix': '~.*', 'optional': True },
                            { 'value': 'openreview.net/Support', 'optional': True }
                        ]
                    }
                },
                'readers': ['openreview.net/Support'],
                'writers': ['openreview.net/Support'],
                'content': {
                    'venue_id': {
                        'order': 1,
                        'description': 'Venue Id',
                        'value': {
                            'param': {
                                'type': 'string',
                                'maxLength': 100,
                                'regex': '.*',
                                'hidden': True
                            }
                        }
                    },
                    'submission_name': {
                        'order': 2,
                        'description': 'Submission name',
                        'value': {
                            'param': {
                                'type': 'string',
                                'maxLength': 100,
                                'regex': '^[a-zA-Z0-9_]*$',
                                'default': 'Submission'
                            }
                        }
                    }
                },
                'domain': '${1/content/venue_id/value}',
                'invitation': {
                    'id': '${2/content/venue_id/value}/-/Desk_Rejection_Reversion',
                    'invitees': ['${3/content/venue_id/value}'],
                    'signatures': ['${3/content/venue_id/value}'],
                    'readers': ['${3/content/venue_id/value}'],
                    'writers': ['${3/content/venue_id/value}'],
                    'content': {
                        'desk_rejection_reversion_process_script': {
                            'value': self.get_process_content('../process/desk_rejection_reversion_process_script.py')
                        }
                    },
                    'edit': {
                        'signatures': ['${4/content/venue_id/value}'],
                        'readers': ['${4/content/venue_id/value}'],
                        'writers': ['${4/content/venue_id/value}'],
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
                            'id': '${4/content/venue_id/value}/${4/content/submission_name/value}/${{2/content/noteId/value}/number}/-/Desk_Rejection_Reversion',
                            'invitees': ['${5/content/venue_id/value}'],
                            'readers': ['everyone'],
                            'writers': ['${5/content/venue_id/value}'],
                            'signatures': ['${5/content/venue_id/value}'],
                            'maxReplies': 1,
                            'process': '''def process(client, edit, invitation):
    meta_invitation = client.get_invitation(invitation.invitations[0])
    script = meta_invitation.content['desk_rejection_reversion_process_script']['value']
    funcs = {
        'openreview': openreview,
        'datetime': datetime
    }
    exec(script, funcs)
    funcs['process'](client, edit, invitation)''',
                            'edit': {
                                'signatures': {
                                    'param': {
                                        'items': [
                                            { 'value': '${9/content/venue_id/value}/Program_Chairs' }
                                        ]
                                    }
                                },
                                'readers': ['${6/content/venue_id/value}/Program_Chairs', '${6/content/venue_id/value}/${6/content/submission_name/value}/${{4/content/noteId/value}/number}/Reviewers', '${6/content/venue_id/value}/${6/content/submission_name/value}/${{4/content/noteId/value}/number}/Authors'],
                                'writers': ['${6/content/venue_id/value}'],
                                'note': {
                                    'forum': '${4/content/noteId/value}',
                                    'replyto': '${4/content/deskRejectionId/value}',
                                    'signatures': ['${3/signatures}'],
                                    'readers': ['${3/readers}'],
                                    'writers': [ '${7/content/venue_id/value}' ],
                                    'content': {
                                        'revert_desk_rejection_confirmation': {
                                            'value': {
                                                'param': {
                                                    'type': 'string',
                                                    'enum': [
                                                        'We approve the reversion of desk-rejected submission.'
                                                    ],
                                                    'input': 'checkbox'
                                                }
                                            },
                                            'description': 'Please confirm to revert the desk-rejection.',
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
                }
            }
        )

        self.post_invitation_edit(invitation)

    def setup_reviewer_bid_template_invitation(self):

        support_group_id = self.support_group_id
        invitation_id = f'{support_group_id}/Simple_Dual_Anonymous/Venue_Configuration_Request/-/Reviewer_Bid'

        invitation = Invitation(id=invitation_id,
            invitees=['active_venues'],
            readers=['everyone'],
            writers=['openreview.net/Support'],
            signatures=['openreview.net/Support'],
            process=self.get_process_content('process/reviewer_bidding_template_process.py'),
            edit = {
                'signatures' : {
                    'param': {
                        'items': [
                            { 'prefix': '~.*', 'optional': True },
                            { 'value': 'openreview.net/Support', 'optional': True }
                        ]
                    }
                },
                'readers': ['openreview.net/Support'],
                'writers': ['openreview.net/Support'],
                'content': {
                    'venue_id': {
                        'order': 1,
                        'description': 'Venue Id',
                        'value': {
                            'param': {
                                'type': 'string',
                                'maxLength': 100,
                                'regex': '.*',
                                'hidden': True
                            }
                        }
                    },
                    'name': {
                        'order': 2,
                        'description': 'Name for this step, use underscores to represent spaces. Default is Reviewer_Bid. This name will be shown in the link users will click to perform this step.',
                        'value': {
                            'param': {
                                'type': 'string',
                                'maxLength': 100,
                                'regex': '^[a-zA-Z0-9_]*$',
                                'default': 'Reviewer_Bid'
                            }
                        }
                    },
                    'activation_date': {
                        'order': 3,
                        'value': {
                            'param': {
                                'type': 'date',
                                'range': [ 0, 9999999999999 ],
                                'deletable': True
                            }
                        }
                    },
                    'due_date': {
                        'order': 4,
                        'value': {
                            'param': {
                                'type': 'date',
                                'range': [ 0, 9999999999999 ],
                                'optional': True,
                                'deletable': True
                            }
                        }
                    },
                    'submission_name': {
                        'order': 5,
                        'value': {
                            'param': {
                                'type': 'string',
                                'maxLength': 100,
                                'regex': '^[a-zA-Z0-9_]*$',
                                'default': 'Submission'
                            }
                        }
                    },
                },
                'domain': '${1/content/venue_id/value}',
                'invitation': {
                    'id': '${2/content/venue_id/value}/-/${2/content/name/value}',
                    'invitees': ['${3/content/venue_id/value}/Reviewers'],
                    'signatures': ['${3/content/venue_id/value}'],
                    'readers': ['${3/content/venue_id/value}', '${3/content/venue_id/value}/Reviewers'],
                    'writers': ['${3/content/venue_id/value}'],
                    'cdate': '${2/content/activation_date/value}',
                    'duedate': '${2/content/due_date/value}',
                    'expdate': '${2/content/due_date/value}+1800000',
                    'minReplies': 50,
                    'maxReplies': 1,
                    'web': self.get_webfield_content('../webfield/paperBidWebfield.js'),
                    'content': {
                        'committee_name': {
                            'value': 'Reviewers'
                        }
                    },
                    'edge': {
                        'id': {
                            'param': {
                                'withInvitation': '${5/content/venue_id/value}/-/${5/content/name/value}',
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
                        'readers': ['${4/content/venue_id/value}', '${2/tail}'],
                        'writers': ['${4/content/venue_id/value}', '${2/tail}'],
                        'signatures': {
                            'param': {
                                'regex': '~.*|' + '${5/content/venue_id/value}'
                            }
                        },
                        'head': {
                            'param': {
                                'type': 'note',
                                'withInvitation': '${5/content/venue_id/value}/-/${5/content/submission_name/value}'
                            }
                        },
                        'tail': {
                            'param': {
                                'type': 'profile',
                                'options': {
                                    'group': '${6/content/venue_id/value}/Reviewers'
                                }
                            }
                        },
                        'label': {
                            'param': {
                                'enum': ['Very High', 'High', 'Neutral', 'Low', 'Very Low'],
                                'input': 'radio'
                            }
                        }
                    }
                }
            }
        )

        self.post_invitation_edit(invitation)

    def setup_automated_administrator_group_template_invitation(self):

        support_group_id = self.support_group_id
        invitation_id = f'{support_group_id}/Simple_Dual_Anonymous/Venue_Configuration_Request/-/Automated_Administrator_Group_Template'

        invitation = Invitation(id=invitation_id,
            invitees=['active_venues'],
            readers=['everyone'],
            writers=['~Super_User1'],
            signatures=['~Super_User1'], # Super User, otherwise it won't let me add this group to the conference group
            process=self.get_process_content('process/automated_administrator_group_template_process.py'),
            edit={
                'content': {
                    'venue_id': {
                        'order': 1,
                        'description': 'Venue Id',
                        'value': {
                            'param': {
                                'type': 'domain'
                            }
                        }
                    }
                },
                'domain': '${1/content/venue_id/value}',
                'signatures' : {
                    'param': {
                        'items': [
                            { 'prefix': '~.*', 'optional': True },
                            { 'value': 'openreview.net/Support', 'optional': True }
                        ]
                    }
                },
                'readers': ['openreview.net/Support'],
                'writers': ['openreview.net/Support'],
                'group': {
                    'id': '${2/content/venue_id/value}/Automated_Administrator',
                    'readers': ['${3/content/venue_id/value}'],
                    'writers': ['${3/content/venue_id/value}', '${3/content/venue_id/value}/Automated_Administrator'],
                    'signatures': ['${3/content/venue_id/value}'],
                    'signatories': ['${3/content/venue_id/value}', '${3/content/venue_id/value}/Automated_Administrator']
                }
            }
        )

        self.post_invitation_edit(invitation)

    def setup_submission_reviewer_group_invitation(self):

        invitation = Invitation(id='openreview.net/Support/Simple_Dual_Anonymous/Venue_Configuration_Request/-/Reviewers_Submission_Group',
            invitees=['active_venues'],
            readers=['everyone'],
            writers=['openreview.net/Support'],
            signatures=['openreview.net/Support'],
            edit = {
                'signatures' : {
                    'param': {
                        'items': [
                            { 'prefix': '~.*', 'optional': True },
                            { 'value': 'openreview.net/Support', 'optional': True }
                        ]
                    }
                },
                'readers': ['openreview.net/Support'],
                'writers': ['openreview.net/Support'],
                'content': {
                    'venue_id': {
                        'order': 1,
                        'description': 'Venue Id',
                        'value': {
                            'param': {
                                'type': 'string',
                                'maxLength': 100,
                                'regex': '.*',
                                'hidden': True
                            }
                        }
                    },
                    'reviewers_name': {
                        'order': 2,
                        'description': 'Venue reviewers name',
                        'value': {
                            'param': {
                                'type': 'string',
                                'maxLength': 100,
                                'regex': '^[a-zA-Z0-9_]*$',
                                'default': 'Reviewers'
                            }
                        }
                    },
                    'submission_name': {
                        'order': 3,
                        'value': {
                            'param': {
                                'type': 'string',
                                'maxLength': 100,
                                'regex': '^[a-zA-Z0-9_]*$',
                                'default': 'Submission'
                            }
                        }
                    },
                    'activation_date': {
                        'order': 4,
                        'description': 'When would you like to have your OpenReview submission portal opened?',
                        'value': {
                            'param': {
                                'type': 'date',
                                'range': [ 0, 9999999999999 ],
                                'deletable': True
                            }
                        }
                    }
                },
                'domain': '${1/content/venue_id/value}',
                'invitation': {
                    'id': '${2/content/venue_id/value}/${2/content/reviewers_name/value}/-/${2/content/submission_name/value}_Group',
                    'invitees': ['${3/content/venue_id/value}'],
                    'signatures': ['${3/content/venue_id/value}'],
                    'readers': ['${3/content/venue_id/value}'],
                    'writers': ['${3/content/venue_id/value}'],
                    'cdate': '${2/content/activation_date/value}',
                    'dateprocesses': [{
                        'dates': ["#{4/cdate}", self.update_date_string],
                        'script': self.group_edit_process
                    }],
                    'edit': {
                        'signatures': ['${4/content/venue_id/value}'],
                        'readers': ['${4/content/venue_id/value}'],
                        'writers': ['${4/content/venue_id/value}'],
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
                            'id': '${4/content/venue_id/value}/${4/content/submission_name/value}/${2/content/noteNumber/value}/${4/content/reviewers_name/value}',
                            'readers': ['${5/content/venue_id/value}', '${5/content/venue_id/value}/${5/content/submission_name/value}/${3/content/noteNumber/value}/${5/content/reviewers_name/value}'],
                            'nonreaders': ['${5/content/venue_id/value}/${5/content/submission_name/value}/${3/content/noteNumber/value}/Authors'],
                            'deanonymizers': ['${5/content/venue_id/value}', '${5/content/venue_id/value}/Program_Chairs', '${5/content/venue_id/value}/${5/content/submission_name/value}/${3/content/noteNumber/value}/${5/content/reviewers_name/value}'],
                            'writers': ['${5/content/venue_id/value}'],
                            'signatures': ['${5/content/venue_id/value}'],
                            'signatories': ['${5/content/venue_id/value}'],
                            'anonids': True
                        }
                    }
                }
            }
        )

        self.post_invitation_edit(invitation)

    def setup_authors_accepted_group_template_invitation(self):

        support_group_id = self.support_group_id
        invitation_id = f'{support_group_id}/Simple_Dual_Anonymous/Venue_Configuration_Request/-/Authors_Accepted_Group_Template'

        invitation = Invitation(id=invitation_id,
            invitees=['active_venues'],
            readers=['everyone'],
            writers=['openreview.net/Support'],
            signatures=['openreview.net/Support'],
            edit={
                'content': {
                    'venue_id': {
                        'order': 1,
                        'description': 'Venue Id',
                        'value': {
                            'param': {
                                'type': 'domain'
                            }
                        }
                    },
                    'authors_name': {
                        'order': 2,
                        'description': 'Venue authors name',
                        'value': {
                            'param': {
                                'type': 'string',
                                'maxLength': 100,
                                'default': 'Authors'
                            }
                        }
                    }
                },
                'domain': '${1/content/venue_id/value}',
                'signatures' : {
                    'param': {
                        'items': [
                            { 'prefix': '~.*', 'optional': True },
                            { 'value': 'openreview.net/Support', 'optional': True }
                        ]
                    }
                },
                'readers': ['openreview.net/Support'],
                'writers': ['openreview.net/Support'],
                'group': {
                    'id': '${2/content/venue_id/value}/${2/content/authors_name/value}/Accepted',
                    'readers': ['${3/content/venue_id/value}', '${3/content/venue_id/value}/${3/content/authors_name/value}/Accepted'],
                    'writers': ['${3/content/venue_id/value}'],
                    'signatures': ['${3/content/venue_id/value}'],
                    'signatories': ['${3/content/venue_id/value}']
                }
            }
        )

        self.post_invitation_edit(invitation)

    def setup_venue_group_template_invitation(self):

        support_group_id = self.support_group_id
        invitation_id = f'{support_group_id}/Simple_Dual_Anonymous/Venue_Configuration_Request/-/Venue_Group_Template'

        invitation = Invitation(id=invitation_id,
            invitees=['active_venues'],
            readers=['everyone'],
            writers=['~Super_User1'],
            signatures=['~Super_User1'],
            process=self.get_process_content('process/venue_group_template_process.py'),
            edit={
                'content': {
                    'venue_id': {
                        'order': 1,
                        'description': 'Venue Id',
                        'value': {
                            'param': {
                                'type': 'domain'
                            }
                        }
                    },
                    'title': {
                        'order': 2,
                        'description': 'Venue title',
                        'value': {
                            'param': {
                                'type': 'string',
                                'maxLength': 100
                            }
                        }
                    },
                    'subtitle': {
                        'order': 3,
                        'description': 'Venue subtitle',
                        'value': {
                            'param': {
                                'type': 'string',
                                'maxLength': 100
                            }
                        }
                    },
                    'website': {
                        'order': 4,
                        'description': 'Venue website',
                        'value': {
                            'param': {
                                'type': 'string',
                                'maxLength': 100
                            }
                        }
                    },
                    'location': {
                        'order': 5,
                        'description': 'Venue location',
                        'value': {
                            'param': {
                                'type': 'string',
                                'maxLength': 100
                            }
                        }
                    },
                    'start_date': {
                        'order': 6,
                        'description': 'Venue start date',
                        'value': {
                            'param': {
                                'type': 'string',
                                'maxLength': 100
                            }
                        }
                    },
                    'contact': {
                        'order': 7,
                        'description': 'Venue contact',
                        'value': {
                            'param': {
                                'type': 'string',
                                'maxLength': 100
                            }
                        }
                    },
                },
                'domain': '${1/content/venue_id/value}',
                'signatures': ['~Super_User1'],
                'readers': ['everyone'],
                'writers': ['~Super_User1'],
                'group': {
                    'id': '${2/content/venue_id/value}',
                    'content': {
                        'title': { 'value': '${4/content/title/value}'},
                        'subtitle': { 'value': '${4/content/subtitle/value}'},
                        'website': { 'value': '${4/content/website/value}'},
                        'location': { 'value': '${4/content/location/value}'},
                        'start_date': { 'value': '${4/content/start_date/value}'},
                        'contact': { 'value': '${4/content/contact/value}'},
                    },
                    'readers': ['everyone'],
                    'writers': ['${3/content/venue_id/value}'],
                    'signatures': ['~Super_User1'],
                    'signatories': ['${3/content/venue_id/value}'],
                    'members': [support_group_id],
                    'web': self.get_webfield_content('../webfield/homepageWebfield.js')
                }
            }
        )

        self.post_invitation_edit(invitation)

    def setup_edit_template_invitation(self):

        support_group_id = self.support_group_id
        invitation_id = f'{support_group_id}/Simple_Dual_Anonymous/Venue_Configuration_Request/-/Edit_Template'

        invitation = Invitation(id=invitation_id,
            invitees=['~Super_User1'],
            readers=['everyone'],
            writers=['~Super_User1'],
            signatures=['~Super_User1'],
            edit = {
                'signatures': ['~Super_User1'],
                'readers': ['~Super_User1'],
                'writers': ['~Super_User1'],
                'domain': { 'param': { 'regex': '.*' } },
                'invitation': {
                    'id': '${2/domain}/-/Edit',
                    'invitees': ['${3/domain}'],
                    'readers': ['${3/domain}'],
                    'signatures': ['~Super_User1'],
                    'writers': ['~Super_User1'],
                    'edit': True,
                    'content': {
                        'invitation_edit_script': {
                            'value': self.get_process_content('../process/invitation_edit_process.py')
                        },
                        'group_edit_script': {
                            'value': self.get_process_content('../process/group_edit_process.py')
                        }
                    }
                }
            }
        )

        self.post_invitation_edit(invitation)

    def setup_inner_group_template_invitation(self):

        support_group_id = self.support_group_id
        invitation_id = f'{support_group_id}/Simple_Dual_Anonymous/Venue_Configuration_Request/-/Venue_Inner_Group_Template'

        invitation = Invitation(id=invitation_id,
            invitees=['~Super_User1'],
            readers=['everyone'],
            writers=['~Super_User1'],
            signatures=['~Super_User1'],
            edit={
                'domain': '${1/group/id}',
                'signatures': ['~Super_User1'],
                'readers': ['everyone'],
                'writers': ['~Super_User1'],
                'group': {
                    'id': { 'param': { 'regex': '.*' } },
                    'readers': ['everyone'],
                    'writers': ['${2/id}'],
                    'signatures': ['~Super_User1'],
                    'signatories': ['${2/id}'],
                }
            }
        )

        self.post_invitation_edit(invitation)

    def setup_program_chairs_group_template_invitation(self):

        support_group_id = self.support_group_id
        invitation_id = f'{support_group_id}/Simple_Dual_Anonymous/Venue_Configuration_Request/-/Program_Chairs_Group_Template'

        invitation = Invitation(id=invitation_id,
            invitees=['~Super_User1'],
            readers=['everyone'],
            writers=['~Super_User1'],
            signatures=['~Super_User1'],
            process=self.get_process_content('process/program_chairs_group_template_process.py'),
            edit={
                'content': {
                    'venue_id': {
                        'order': 1,
                        'description': 'Venue Id',
                        'value': {
                            'param': {
                                'type': 'domain'
                            }
                        }
                    },
                    'program_chairs_name': {
                        'order': 2,
                        'description': 'Venue program chairs name',
                        'value': {
                            'param': {
                                'type': 'string',
                                'maxLength': 100,
                                'default': 'Program Chairs'
                            }
                        }
                    },
                    'program_chairs_emails': {
                        'order': 3,
                        'description': 'Venue program chairs profile ids or emails',
                        'value': {
                            'param': {
                                'type': 'string[]',
                                'regex': '~.*|.*@.*',
                            }
                        }
                    },
                },
                'domain': '${1/content/venue_id/value}',
                'signatures': ['~Super_User1'],
                'readers': ['${2/content/venue_id/value}'],
                'writers': ['~Super_User1'],
                'group': {
                    'id': '${2/content/venue_id/value}/${2/content/program_chairs_name/value}',
                    'readers': ['${3/content/venue_id/value}'],
                    'writers': ['${3/content/venue_id/value}'],
                    'signatures': ['~Super_User1'],
                    'signatories': ['${3/content/venue_id/value}'],
                    'members': ['${3/content/program_chairs_emails/value}'],
                    'web': self.get_webfield_content('../webfield/programChairsWebfield.js')
                }
            }
        )

        self.post_invitation_edit(invitation)

    def setup_reviewers_group_template_invitation(self):

        support_group_id = self.support_group_id
        invitation_id = f'{support_group_id}/Simple_Dual_Anonymous/Venue_Configuration_Request/-/Reviewers_Group_Template'

        invitation = Invitation(id=invitation_id,
            invitees=['~Super_User1'],
            readers=['everyone'],
            writers=['~Super_User1'],
            signatures=['~Super_User1'],
            process=self.get_process_content('process/reviewers_group_template_process.py'),
            edit={
                'content': {
                    'venue_id': {
                        'order': 1,
                        'description': 'Venue Id',
                        'value': {
                            'param': {
                                'type': 'domain'
                            }
                        }
                    },
                    'reviewers_name': {
                        'order': 2,
                        'description': 'Venue reviewers name',
                        'value': {
                            'param': {
                                'type': 'string',
                                'maxLength': 100,
                                'default': 'Reviewers'
                            }
                        }
                    }
                },
                'domain': '${1/content/venue_id/value}',
                'signatures': ['~Super_User1'],
                'readers': ['${2/content/venue_id/value}'],
                'writers': ['~Super_User1'],
                'group': {
                    'id': '${2/content/venue_id/value}/${2/content/reviewers_name/value}',
                    'readers': ['everyone'],
                    'writers': ['${3/content/venue_id/value}'],
                    'signatures': ['~Super_User1'],
                    'signatories': ['${3/content/venue_id/value}'],
                    'web': self.get_webfield_content('../webfield/reviewersWebfield.js')
                }
            }
        )

        self.post_invitation_edit(invitation)

    def setup_authors_group_template_invitation(self):

        support_group_id = self.support_group_id
        invitation_id = f'{support_group_id}/Simple_Dual_Anonymous/Venue_Configuration_Request/-/Authors_Group_Template'

        invitation = Invitation(id=invitation_id,
            invitees=['~Super_User1'],
            readers=['everyone'],
            writers=['~Super_User1'],
            signatures=['~Super_User1'],
            process=self.get_process_content('process/authors_group_template_process.py'),
            edit={
                'content': {
                    'venue_id': {
                        'order': 1,
                        'description': 'Venue Id',
                        'value': {
                            'param': {
                                'type': 'domain'
                            }
                        }
                    },
                    'authors_name': {
                        'order': 2,
                        'description': 'Venue authors name',
                        'value': {
                            'param': {
                                'type': 'string',
                                'maxLength': 100,
                                'default': 'Authors'
                            }
                        }
                    }
                },
                'domain': '${1/content/venue_id/value}',
                'signatures': ['~Super_User1'],
                'readers': ['${2/content/venue_id/value}'],
                'writers': ['~Super_User1'],
                'group': {
                    'id': '${2/content/venue_id/value}/${2/content/authors_name/value}',
                    'readers': ['${3/content/venue_id/value}', '${3/content/venue_id/value}/${3/content/authors_name/value}'],
                    'writers': ['${3/content/venue_id/value}'],
                    'signatures': ['${3/content/venue_id/value}'],
                    'signatories': ['${3/content/venue_id/value}'],
                    'web': self.get_webfield_content('../webfield/authorsWebfield.js')
                }
            }
        )

        self.post_invitation_edit(invitation)

    def setup_reviewer_conflicts_template_invitation(self):

        support_group_id = self.support_group_id
        invitation_id = f'{support_group_id}/Simple_Dual_Anonymous/Venue_Configuration_Request/-/Reviewer_Conflicts'

        invitation = Invitation(id=invitation_id,
            invitees=['active_venues'],
            readers=['everyone'],
            writers=['openreview.net/Support'],
            signatures=['openreview.net/Support'],
            process=self.get_process_content('process/reviewer_conflicts_template_process.py'),
            edit = {
                'signatures' : {
                    'param': {
                        'items': [
                            { 'prefix': '~.*', 'optional': True },
                            { 'value': 'openreview.net/Support', 'optional': True }
                        ]
                    }
                },
                'readers': ['openreview.net/Support'],
                'writers': ['openreview.net/Support'],
                'content': {
                    'venue_id': {
                        'order': 1,
                        'description': 'Venue Id',
                        'value': {
                            'param': {
                                'type': 'string',
                                'maxLength': 100,
                                'regex': '.*',
                                'hidden': True
                            }
                        }
                    },
                    'name': {
                        'order': 2,
                        'description': 'Name for this step, use underscores to represent spaces. Default is Reviewer_Conflict.',
                        'value': {
                            'param': {
                                'type': 'string',
                                'maxLength': 100,
                                'regex': '^[a-zA-Z0-9_]*$',
                                'default': 'Reviewer_Conflict'
                            }
                        }
                    },
                    'activation_date': {
                        'order': 3,
                        'value': {
                            'param': {
                                'type': 'date',
                                'range': [ 0, 9999999999999 ],
                                'deletable': True
                            }
                        }
                    },
                    'submission_name': {
                        'order': 4,
                        'value': {
                            'param': {
                                'type': 'string',
                                'maxLength': 100,
                                'regex': '^[a-zA-Z0-9_]*$',
                                'default': 'Submission'
                            }
                        }
                    },
                },
                'domain': '${1/content/venue_id/value}',
                'invitation': {
                    'id': '${2/content/venue_id/value}/-/${2/content/name/value}',
                    'invitees': ['${3/content/venue_id/value}/Automated_Administrator'],
                    'signatures': ['~Super_User1'], ## date process needs to run with super user premission
                    'readers': ['${3/content/venue_id/value}'],
                    'writers': ['${3/content/venue_id/value}'],
                    'cdate': '${2/content/activation_date/value}',
                    'description': '<span class="text-muted">Creates "edges" between reviewers & submissions representing reviewer conflicts.</span>',
                    'dateprocesses': [{
                        'dates': ["#{4/cdate} + 5000"],
                        'script': self.get_process_content('../process/compute_conflicts_process.py')
                    }],
                    'content': {
                        'committee_name': {
                            'value': 'Reviewers'
                        },
                        'reviewers_conflict_policy': {
                            'value': 'Default'
                        },
                        'reviewers_conflict_n_years': {
                            'value': 0
                        }
                    },
                    'edge': {
                        'id': {
                            'param': {
                                'withInvitation': '${5/content/venue_id/value}/-/${5/content/name/value}',
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
                        'readers': ['${4/content/venue_id/value}', '${2/tail}'],
                        'writers': ['${4/content/venue_id/value}'],
                        'signatures': {
                            'param': {
                                'regex': '${5/content/venue_id/value}|${5/content/venue_id/value}/Program_Chairs',
                                'default': ['${6/content/venue_id/value}/Program_Chairs']
                            }
                        },
                        'head': {
                            'param': {
                                'type': 'note',
                                'withInvitation': '${5/content/venue_id/value}/-/${5/content/submission_name/value}'
                            }
                        },
                        'tail': {
                            'param': {
                                'type': 'profile',
                                'options': {
                                    'group': '${6/content/venue_id/value}/Reviewers'
                                }
                            }
                        },
                        'weight': {
                            'param': {
                                'minimum': -1
                            }
                        },
                        'label': {
                            'param': {
                                'regex': '.*',
                                'optional': True,
                                'deletable': True
                            }
                        }
                    }
                }
            }
        )

        self.post_invitation_edit(invitation)

    def setup_reviewer_affinities_template_invitation(self):

        support_group_id = self.support_group_id
        invitation_id = f'{support_group_id}/Simple_Dual_Anonymous/Venue_Configuration_Request/-/Reviewer_Paper_Affinities'

        invitation = Invitation(id=invitation_id,
            invitees=['active_venues'],
            readers=['everyone'],
            writers=['openreview.net/Support'],
            signatures=['openreview.net/Support'],
            process=self.get_process_content('process/reviewer_affinities_template_process.py'),
            edit = {
                'signatures' : {
                    'param': {
                        'items': [
                            { 'prefix': '~.*', 'optional': True },
                            { 'value': 'openreview.net/Support', 'optional': True }
                        ]
                    }
                },
                'readers': ['openreview.net/Support'],
                'writers': ['openreview.net/Support'],
                'content': {
                    'venue_id': {
                        'order': 1,
                        'description': 'Venue Id',
                        'value': {
                            'param': {
                                'type': 'string',
                                'maxLength': 100,
                                'regex': '.*',
                                'hidden': True
                            }
                        }
                    },
                    'name': {
                        'order': 2,
                        'description': 'Name for this step, use underscores to represent spaces. Default is Reviewer_Paper_Affninities.',
                        'value': {
                            'param': {
                                'type': 'string',
                                'maxLength': 100,
                                'regex': '^[a-zA-Z0-9_]*$',
                                'default': 'Reviewer_Paper_Affninities'
                            }
                        }
                    },
                    'activation_date': {
                        'order': 3,
                        'value': {
                            'param': {
                                'type': 'date',
                                'range': [ 0, 9999999999999 ],
                                'deletable': True
                            }
                        }
                    },
                    'submission_name': {
                        'order': 4,
                        'value': {
                            'param': {
                                'type': 'string',
                                'maxLength': 100,
                                'regex': '^[a-zA-Z0-9_]*$',
                                'default': 'Submission'
                            }
                        }
                    },
                },
                'domain': '${1/content/venue_id/value}',
                'invitation': {
                    'id': '${2/content/venue_id/value}/-/${2/content/name/value}',
                    'invitees': ['${3/content/venue_id/value}/Automated_Administrator'],
                    'signatures': ['~Super_User1'], ## date process needs to run with super user permission
                    'readers': ['${3/content/venue_id/value}'],
                    'writers': ['${3/content/venue_id/value}'],
                    'cdate': '${2/content/activation_date/value}',
                    'description': '<span class="text-muted">Creates "edges" between reviewers & submissions representing reviewer expertise.</span>',
                    'dateprocesses': [{
                        'dates': ["#{4/cdate} + 5000"],
                        'script': self.get_process_content('../process/compute_affinity_scores_process.py')
                    }],
                    'content': {
                        'committee_name': {
                            'value': 'Reviewers'
                        }
                    },
                    'edge': {
                        'id': {
                            'param': {
                                'withInvitation': '${5/content/venue_id/value}/-/${5/content/name/value}',
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
                        'readers': ['${4/content/venue_id/value}', '${2/tail}'],
                        'nonreaders': ['${4/content/venue_id/value}/Authors'],
                        'writers': ['${4/content/venue_id/value}'],
                        'signatures': {
                            'param': {
                                'regex': '${5/content/venue_id/value}|${5/content/venue_id/value}/Program_Chairs',
                                'default': ['${6/content/venue_id/value}/Program_Chairs']
                            }
                        },
                        'head': {
                            'param': {
                                'type': 'note',
                                'withInvitation': '${5/content/venue_id/value}/-/${5/content/submission_name/value}'
                            }
                        },
                        'tail': {
                            'param': {
                                'type': 'profile',
                                'options': {
                                    'group': '${6/content/venue_id/value}/Reviewers'
                                }
                            }
                        },
                        'weight': {
                            'param': {
                                'minimum': -1
                            }
                        },
                        'label': {
                            'param': {
                                'regex': '.*',
                                'optional': True,
                                'deletable': True
                            }
                        }
                    }
                }
            }
        )

        self.post_invitation_edit(invitation)