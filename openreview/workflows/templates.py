import openreview.api
import openreview
from openreview.api import Invitation
import os

class Templates():

    def __init__(self, client, super_id):
        self.support_user_id = f'{super_id}/Support'       #openreview.net/Support
        self.template_domain = f'{super_id}/Template' #openreview.net/-/Template
        self.client = client
        self.super_id = super_id                        #openreview.net
        self.meta_invitation_id = f'{self.template_domain}/-/Edit'  #openreview.net/-/Edit
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

        # setup group template invitations
        self.setup_invitation_template_meta_invitation()
        self.setup_automated_administrator_group_template_invitation()
        self.setup_committee_group_template_invitation()
        self.setup_committee_group_recruitment_template_invitation()
        self.setup_group_message_template_invitation()
        self.setup_group_members_template_invitation()

        # setup invitation template invitations
        self.setup_note_release_template_invitation()
        self.setup_decision_upload_template_invitation()
        self.setup_reviewer_conflicts_template_invitation()
        self.setup_reviewer_affinities_template_invitation()
        self.setup_reviewer_assignment_configuration_template_invitation()
        self.setup_reviewer_matching_template_invitation()
        self.setup_email_decisions_template_invitation()
        self.setup_email_reviews_template_invitation()
        self.set_paper_release_template_invitation()
        self.setup_article_endorsement_template_invitation()
        self.setup_reviewers_review_count_template_invitation()
        self.setup_reviewers_review_assignment_count_template_invitation()
        self.setup_reviewers_review_days_late_template_invitation()
        self.setup_committee_roles_invitations()
        self.setup_llm_pdf_response_template_invitation()

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

    def setup_invitation_template_meta_invitation(self):
        
        template_domain_group_id = self.template_domain

        template_domain_group = openreview.tools.get_group(self.client, template_domain_group_id)
        if template_domain_group is None:
            self.client.post_group_edit(
                invitation=f'{self.super_id}/-/Edit',
                signatures=[self.super_id],
                readers=['everyone'],
                writers=[self.super_id],
                group=openreview.api.Group(
                    id=template_domain_group_id,
                    readers=['everyone'],
                    writers=[self.super_id],
                    signatures=[self.super_id],
                    members=[self.support_user_id],
                    signatories=[template_domain_group_id]
                )
            )

        meta_invitation = openreview.tools.get_invitation(self.client, self.meta_invitation_id)

        if meta_invitation is None:
            self.client.post_invitation_edit(invitations=None,
                readers=[self.template_domain],
                writers=[self.template_domain],
                signatures=['~Super_User1'],
                invitation=Invitation(id=self.meta_invitation_id,
                    invitees=[self.template_domain],
                    readers=[self.template_domain],
                    signatures=['~Super_User1'],
                    edit=True
                )
            )

    def setup_note_release_template_invitation(self):

        invitation = Invitation(id=f'{self.template_domain}/-/Note_Release',
            invitees=['active_venues'],
            readers=['everyone'],
            writers=[self.template_domain],
            signatures=[self.template_domain],
            process=self.get_process_content('workflow_process/note_release_template_process.py'),
            edit = {
                'signatures' : {
                    'param': {
                        'items': [
                            { 'prefix': '~.*', 'optional': True },
                            { 'value': self.template_domain, 'optional': True }
                        ]
                    }
                },
                'readers': [self.template_domain],
                'writers': [self.template_domain],
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
                        'description': 'Name for this step, use underscores to represent spaces.',
                        'value': {
                            'param': {
                                'type': 'string',
                                'maxLength': 100,
                                'regex': '^[a-zA-Z0-9_]*$'
                            }
                        }
                    },
                    'activation_date': {
                        'order': 4,
                        'value': {
                            'param': {
                                'type': 'date',
                                'range': [ 0, 9999999999999 ],
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
                    },
                    'reviewers_name': {
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
                    'authors_name': {
                        'description': 'Venue authors name',
                        'value': {
                            'param': {
                                'type': 'string',
                                'maxLength': 100,
                                'default': 'Authors'
                            }
                        }
                    },
                    'stage_name': {
                        'order': 3,
                        'description': 'Name of the stage that will be edited using this invitation',
                        'value': {
                            'param': {
                                'type': 'string',
                                'maxLength': 100,
                                'regex': '^[a-zA-Z0-9_]*$'
                            }
                        }
                    },
                    'description': {
                        'value': {
                            'param': {
                                'type': 'string',
                                'regex': '.*'
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
                    'expdate': '${2/content/activation_date/value}+1209600000',
                    'description': '${2/content/description/value}',
                    'dateprocesses': [{
                        'dates': ["#{4/cdate}", self.update_date_string],
                        'script': self.get_process_content('process/release_notes_process.py')
                    }],
                    'edit': {
                        'signatures': ['${4/content/venue_id/value}'],
                        'readers': ['${4/content/venue_id/value}'],
                        'writers': ['${4/content/venue_id/value}'],
                        'replacement': False,
                        'invitation': {
                            'id': '${4/content/venue_id/value}/-/${4/content/stage_name/value}',
                            'signatures': ['${5/content/venue_id/value}'],
                            'edit': {
                                'signatures': ['${6/content/venue_id/value}'],
                                'invitation': {
                                    'id': '${6/content/venue_id/value}/${6/content/submission_name/value}${2/content/noteNumber/value}/-/${6/content/stage_name/value}',
                                    'signatures': ['${7/content/venue_id/value}'],
                                    'edit': {
                                        'note': {
                                            'readers': [
                                                '${9/content/venue_id/value}/Program_Chairs',
                                                '${9/content/venue_id/value}/${9/content/submission_name/value}${5/content/noteNumber/value}/${9/content/reviewers_name/value}',
                                                '${9/content/venue_id/value}/${9/content/submission_name/value}${5/content/noteNumber/value}/${9/content/authors_name/value}'
                                            ],
                                            'nonreaders': []
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

    def setup_decision_upload_template_invitation(self):

        invitation = Invitation(id=f'{self.template_domain}/-/Decision_Upload',
            invitees=['active_venues'],
            readers=['everyone'],
            writers=[self.template_domain],
            signatures=[self.template_domain],
            process=self.get_process_content('workflow_process/decision_upload_template_process.py'),
            edit = {
                'signatures' : {
                    'param': {
                        'items': [
                            { 'prefix': '~.*', 'optional': True },
                            { 'value': self.template_domain, 'optional': True }
                        ]
                    }
                },
                'readers': [self.template_domain],
                'writers': [self.template_domain],
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
                        'description': 'Name for this step, use underscores to represent spaces. Default is Decision_Upload.',
                        'value': {
                            'param': {
                                'type': 'string',
                                'maxLength': 100,
                                'regex': '^[a-zA-Z0-9_]*$',
                                'default': 'Decision_Upload'
                            }
                        }
                    },
                    'activation_date': {
                        'order': 4,
                        'description': 'When should decisions be posted?',
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
                    'id': '${2/content/venue_id/value}/-/${2/content/name/value}',
                    'invitees': ['${3/content/venue_id/value}'],
                    'signatures': ['${3/content/venue_id/value}'],
                    'readers': ['${3/content/venue_id/value}'],
                    'writers': ['${3/content/venue_id/value}'],
                    'cdate': '${2/content/activation_date/value}',
                    'description': 'This step runs automatically at the "Upload Date", and posts decisions to submissions based on the contents of a CSV file. The CSV file must contain one decision per line in the format: paper_number, decision, comment. The comment field is optional.',
                    'dateprocesses': [{
                        'dates': ["#{4/cdate}", self.update_date_string],
                        'script': self.get_process_content('process/upload_decisions_process.py'),
                    }],
                    'edit': {
                        'signatures': ['${4/content/venue_id/value}'],
                        'readers': ['${4/content/venue_id/value}'],
                        'writers': ['${4/content/venue_id/value}'],
                    }
                }
            }
        )

        self.post_invitation_edit(invitation)

    def setup_automated_administrator_group_template_invitation(self):

        invitation_id = f'{self.template_domain}/-/Automated_Administrator_Group'

        invitation = Invitation(id=invitation_id,
            invitees=['active_venues'],
            readers=['everyone'],
            writers=[self.template_domain],
            signatures=[self.template_domain],
            process=self.get_process_content('workflow_process/automated_administrator_group_template_process.py'),
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
                            { 'value': self.template_domain, 'optional': True }
                        ]
                    }
                },
                'readers': [self.template_domain],
                'writers': [self.template_domain],
                'group': {
                    'id': '${2/content/venue_id/value}/Automated_Administrator',
                    'readers': ['${3/content/venue_id/value}'],
                    'writers': ['${3/content/venue_id/value}', '${3/content/venue_id/value}/Automated_Administrator'],
                    'signatures': ['${3/content/venue_id/value}'],
                    'signatories': ['${3/content/venue_id/value}', '${3/content/venue_id/value}/Automated_Administrator'],
                    'description': 'Group responsible for executing automated processes.'
                }
            }
        )

        self.post_invitation_edit(invitation)

    def setup_committee_group_template_invitation(self):

        
        invitation_id = f'{self.template_domain}/-/Committee_Group'

        invitation = Invitation(id=invitation_id,
            invitees=[self.template_domain],
            readers=['everyone'],
            writers=[self.template_domain],
            signatures=[self.template_domain],
            process=self.get_process_content('workflow_process/committee_group_template_process.py'),
            content={
                'reviewers_web': { 'value': self.get_webfield_content('../venue/webfield/reviewersWebfield.js')},
                'area_chairs_web': { 'value': self.get_webfield_content('../venue/webfield/areachairsWebfield.js')},
                'senior_area_chairs_web': { 'value': self.get_webfield_content('../venue/webfield/seniorAreaChairsWebfield.js')},
            },
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
                    'committee_role': {
                        'order': 2,
                        'description': 'Committee role',
                        'value': {
                            'param': {
                                'type': 'string',
                                'default': 'reviewers',
                                'enum': ['reviewers', 'area_chairs', 'senior_area_chairs']
                            }
                        }
                    },
                    'committee_name': {
                        'order': 3,
                        'description': 'Venue reviewers name',
                        'value': {
                            'param': {
                                'type': 'string',
                                'maxLength': 100,
                                'default': 'Reviewers'
                            }
                        }
                    },
                    'committee_pretty_name': {
                        'order': 4,
                        'description': 'Committee pretty name',
                        'value': {
                            'param': {
                                'type': 'string',
                                'maxLength': 100,
                                'default': 'Reviewers'
                            }
                        }
                    },
                    'committee_anon_name': {
                        'order': 5,
                        'description': 'Does this group support anonymous membership?',
                        'value': {
                            'param': {
                                'type': 'string',
                                'optional': True
                            }
                        }
                    },
                    'committee_submitted_name': {
                        'order': 6,
                        'description': 'Does this group support membership for users who have submitted to the venue?',
                        'value': {
                            'param': {
                                'type': 'string',
                                'optional': True
                            }
                        }
                    },
                    'additional_readers': {
                        'order': 7,
                        'value': {
                            'param': {
                                'type': 'string[]',
                                'regex': '.*',
                                'optional': True
                            }
                        }
                    }
                },
                'domain': '${1/content/venue_id/value}',
                'signatures': [self.template_domain],
                'readers': ['${2/content/venue_id/value}'],
                'writers': [self.template_domain],
                'group': {
                    'id': '${2/content/venue_id/value}/${2/content/committee_name/value}',
                    'readers': ['${3/content/venue_id/value}', '${3/content/venue_id/value}/${3/content/committee_name/value}', '${3/content/additional_readers/value}'],
                    'writers': ['${3/content/venue_id/value}'],
                    'signatures': ['${3/content/venue_id/value}'],
                    'signatories': ['${3/content/venue_id/value}'],
                    'description': 'Group consisting of users who have agreed to serve as reviewers for the venue.',
                    #'web': '${4/content/${2/content/committee_role/value}_web/value}',
                    'content': {
                        'committee_role': { 'value': '${4/content/committee_role/value}'},
                        'committee_name': { 'value': '${4/content/committee_name/value}'},
                        'committee_pretty_name': { 'value': '${4/content/committee_pretty_name/value}'},
                    }
                }
            }
        )

        self.post_invitation_edit(invitation)

    def setup_committee_group_recruitment_template_invitation(self):

        
        invitation_id = f'{self.template_domain}/-/Committee_Invited_Group'

        invitation = Invitation(id=invitation_id,
            invitees=[self.template_domain],
            readers=['everyone'],
            writers=[self.template_domain],
            signatures=[self.template_domain],
            process=self.get_process_content('workflow_process/committee_invited_group_template_process.py'),
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
                    'committee_id': {
                        'order': 2,
                        'description': 'Commitee Id',
                        'value': {
                            'param': {
                                'type': 'string'
                            }
                        }
                    }
                },
                'domain': '${1/content/venue_id/value}',
                'signatures': [self.template_domain],
                'readers': ['${2/content/venue_id/value}'],
                'writers': [self.template_domain],
                'group': {
                    'id': '${2/content/committee_id/value}/Invited',
                    'description': 'Group consisting of the users who have been invited to serve as reviewers for the venue.',
                    'readers': ['${3/content/venue_id/value}', '${3/content/committee_id/value}/Invited'],
                    'writers': ['${3/content/venue_id/value}'],
                    'signatures': ['${3/content/venue_id/value}'],
                    'signatories': ['${3/content/venue_id/value}'],
                }
            }
        )

        self.post_invitation_edit(invitation)

        invitation_id = f'{self.template_domain}/-/Committee_Declined_Group'

        invitation = Invitation(id=invitation_id,
            invitees=[self.template_domain],
            readers=['everyone'],
            writers=[self.template_domain],
            signatures=[self.template_domain],
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
                    'committee_id': {
                        'order': 2,
                        'description': 'Venue reviewers name',
                        'value': {
                            'param': {
                                'type': 'string'
                            }
                        }
                    }
                },
                'domain': '${1/content/venue_id/value}',
                'signatures': [self.template_domain],
                'readers': ['${2/content/venue_id/value}'],
                'writers': [self.template_domain],
                'group': {
                    'id': '${2/content/committee_id/value}/Declined',
                    'description': 'Group consisting of the users who have been invited to serve as reviewers for the venue and have declined the invitation.',
                    'readers': ['${3/content/venue_id/value}', '${3/content/committee_id/value}/Declined'],
                    'writers': ['${3/content/venue_id/value}'],
                    'signatures': ['${3/content/venue_id/value}'],
                    'signatories': ['${3/content/venue_id/value}']
                }
            }
        )

        self.post_invitation_edit(invitation)

        invitation_id = f'{self.template_domain}/-/Committee_Recruitment_Request'

        invitation = Invitation(id=invitation_id,
            invitees=[self.template_domain],
            readers=['everyone'],
            writers=[self.template_domain],
            signatures=[self.template_domain],
            content={
                'recruitment_request_process_script': {
                    'value': self.get_process_content('process/committee_recruitment_request_process.py'),
                },
                'recruitment_request_edit_reminder_process_script': {
                    'value': self.get_process_content('process/committee_recruitment_request_edit_reminder_process.py'),
                }
            },
            edit = {
                'signatures': [self.template_domain],
                'readers': [self.template_domain],
                'writers': [self.template_domain],
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
                    'committee_id': {
                        'order': 2,
                        'value': {
                            'param': {
                                'type': 'string',
                                'maxLength': 100
                            }
                        }
                    },
                    'committee_pretty_name': {
                        'order': 3,
                        'description': 'Committee pretty name',
                        'value': {
                            'param': {
                                'type': 'string',
                                'maxLength': 100,
                                'default': 'Reviewers'
                            }
                        }
                    },
                    'venue_short_name': {
                        'order': 4,
                        'description': 'Venue reviewers name',
                        'value': {
                            'param': {
                                'type': 'string'
                            }
                        }
                    },
                    'venue_contact': {
                        'order': 5,
                        'description': 'Venue contact email address',
                        'value': {
                            'param': {
                                'type': 'string'
                            }
                        }
                    },                    
                    'reminder_delay': {
                        'order': 4,
                        'description': 'Number of seconds to wait before sending a reminder',
                        'value': {
                            'param': {
                                'type': 'integer',
                                'default': 1000 * 60 * 60 * 24 * 7 # 7 days
                            }
                        }
                    }                   
                },
                'domain': '${1/content/venue_id/value}',
                'invitation': {
                    'id': '${2/content/committee_id/value}/-/Recruitment_Request',
                    'invitees': ['${3/content/venue_id/value}'],
                    'signatures': ['${3/content/venue_id/value}'], 
                    'readers': ['${3/content/venue_id/value}'],
                    'writers': ['${3/content/venue_id/value}'],
                    'instructions': 'Configure the timeframe Program Chairs can send ${2/content/committee_pretty_name/value} recruitment invitations and customize the recruitment email sent to users. Go to the **[${2/content/committee_pretty_name/value} group](/group/edit?id=${2/content/committee_id/value})** to recruit ${2/content/committee_pretty_name/value}.',
                    'process': '''def process(client, edit, invitation):
    meta_invitation = client.get_invitation(invitation.invitations[0])
    script = meta_invitation.content['recruitment_request_process_script']['value']
    funcs = {
        'openreview': openreview,
        'datetime': datetime,
    }
    exec(script, funcs)
    funcs['process'](client, edit, invitation)
''' ,
                    'postprocesses': [
                        {
                            'script': '''def process(client, edit, invitation):
    meta_invitation = client.get_invitation(invitation.invitations[0])
    script = meta_invitation.content['recruitment_request_edit_reminder_process_script']['value']
    funcs = {
        'openreview': openreview,
        'datetime': datetime,
    }
    exec(script, funcs)
    funcs['process'](client, edit, invitation)
''',
                            'delay': '${4/content/reminder_delay/value}'
                        }
                    ],
                    'content': {
                        'committee_id': {
                            'value': '${4/content/committee_id/value}',
                        }
                    },
                    'edit': {
                        'signatures': ['${4/content/venue_id/value}'],
                        'readers': ['${4/content/venue_id/value}'],
                        'writers': ['${4/content/venue_id/value}'],                        
                        'content': {
                            'invitee_details': {
                                'order': 1,
                                'description': 'Enter a list of invitees with one per line. Either tilde IDs (~Captain_America1), emails (captain_rogers@marvel.com), or email,name pairs (captain_rogers@marvel.com, Captain America) expected. If only an email address is provided for an invitee, the recruitment email is addressed to "Dear invitee". Do not use parentheses in your list of invitees.',
                                'value': {
                                    'param': {
                                        'type': 'string',
                                        'maxLength': 200000,
                                        'input': 'textarea'                                  
                                    }
                                }
                            },
                            'invite_message_subject_template': {
                                'order': 2,
                                'description': 'Subject line for the recruitment email.',
                                'value': {
                                    'param': {
                                        'type': 'string',
                                        'maxLength': 200,
                                        'regex': '.*',
                                        'default': '[${7/content/venue_short_name/value}] Invitation to serve as ${7/content/committee_pretty_name/value}'
                                    }
                                }
                            },
                            'invite_message_body_template': {
                                'order': 3,
                                'description': 'Content of the recruitment email. You can use the following variables: {{fullname}} (the name of the invitee) and {{invitation_url}} (the link to accept the invitation). Make sure not to remove the parenthesized tokens.',
                                'value': {
                                    'param': {
                                        'type': 'string',
                                        'maxLength': 200000,
                                        'input': 'textarea',
                                        'markdown': True,
                                        'regex': '.*',
                                        'default': '''Dear {{fullname}},

You have been nominated by the program chair committee of ${7/content/venue_short_name/value} to serve as ${7/content/committee_pretty_name/value}. As a respected researcher in the area, we hope you will accept and help us make ${7/content/venue_short_name/value} a success.

You are also welcome to submit papers, so please also consider submitting to ${7/content/venue_short_name/value}.

We will be using OpenReview.net with the intention of have an engaging reviewing process inclusive of the whole community.

To respond the invitation, please click on the following link:

{{invitation_url}}

Please answer within 10 days.

If you accept, please make sure that your OpenReview account is updated and lists all the emails you are using.  Visit http://openreview.net/profile after logging in.

If you have any questions, please contact ${7/content/venue_contact/value}.

Cheers!

Program Chairs'''
                                    }
                                }
                            }                           
                        },
                        'group': {
                            'id': '${4/content/committee_id/value}',
                            'content': {
                                'last_reviewers_invited_date': {
                                    'value': '${4/tmdate}'
                                }
                            }
                        }
                    }
                }
            }
        )

        self.post_invitation_edit(invitation)

        invitation_id = f'{self.template_domain}/-/Committee_Recruitment_Request_Reminder'

        invitation = Invitation(id=invitation_id,
            invitees=[self.template_domain],
            readers=['everyone'],
            writers=[self.template_domain],
            signatures=[self.template_domain],
            edit = {
                'signatures': [self.template_domain],
                'readers': [self.template_domain],
                'writers': [self.template_domain],
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
                    'committee_id': {
                        'order': 2,
                        'value': {
                            'param': {
                                'type': 'string',
                                'maxLength': 100
                            }
                        }
                    },
                    'committee_pretty_name': {
                        'order': 3,
                        'description': 'Committee pretty name',
                        'value': {
                            'param': {
                                'type': 'string',
                                'maxLength': 100,
                                'default': 'Reviewers'
                            }
                        }
                    },
                    'venue_short_name': {
                        'order': 4,
                        'description': 'Venue reviewers name',
                        'value': {
                            'param': {
                                'type': 'string'
                            }
                        }
                    },
                    'venue_contact': {
                        'order': 5,
                        'description': 'Venue contact email address',
                        'value': {
                            'param': {
                                'type': 'string'
                            }
                        }
                    },                   
                },
                'domain': '${1/content/venue_id/value}',
                'invitation': {
                    'id': '${2/content/committee_id/value}/-/Recruitment_Request_Reminder',
                    'invitees': ['${3/content/venue_id/value}'],
                    'signatures': ['${3/content/venue_id/value}'], 
                    'readers': ['${3/content/venue_id/value}'],
                    'writers': ['${3/content/venue_id/value}'],
                    'description': 'Send a reminder to invited users to respond to the invitation to join the reviewers group.',
                    'process': self.get_process_content('process/committee_recruitment_request_reminder_process.py'),
                    'content': {
                        'committee_id': {
                            'value': '${4/content/committee_id/value}',
                        }
                    },
                    'edit': {
                        'signatures': ['${4/content/venue_id/value}'],
                        'readers': ['${4/content/venue_id/value}'],
                        'writers': ['${4/content/venue_id/value}'],                        
                        'content': {
                            'invite_reminder_message_subject_template': {
                                'order': 2,
                                'description': 'Subject line for the reminder email.',
                                'value': {
                                    'param': {
                                        'type': 'string',
                                        'maxLength': 200,
                                        'regex': '.*',
                                        'default': '[Reminder][${7/content/venue_short_name/value}] Invitation to serve as ${7/content/committee_pretty_name/value}'
                                    }
                                }
                            },
                            'invite_reminder_message_body_template': {
                                'order': 3,
                                'description': 'Content of the reminder email. You can use the following variables: {{fullname}} (the name of the invitee) and {{invitation_url}} (the link to accept the invitation). Make sure not to remove the parenthesized tokens.',
                                'value': {
                                    'param': {
                                        'type': 'string',
                                        'maxLength': 200000,
                                        'input': 'textarea',
                                        'markdown': True,
                                        'regex': '.*',
                                        'default': '''Dear {{fullname}},

You have been nominated by the program chair committee of ${7/content/venue_short_name/value} to serve as ${7/content/committee_pretty_name/value}. As a respected researcher in the area, we hope you will accept and help us make ${7/content/venue_short_name/value} a success.

You are also welcome to submit papers, so please also consider submitting to ${7/content/venue_short_name/value}.

We will be using OpenReview.net with the intention of have an engaging reviewing process inclusive of the whole community.

To respond the invitation, please click on the following link:

{{invitation_url}}

Please answer within 10 days.

If you accept, please make sure that your OpenReview account is updated and lists all the emails you are using.  Visit http://openreview.net/profile after logging in.

If you have any questions, please contact ${7/content/venue_contact/value}.

Cheers!

Program Chairs'''                                        
                                    }
                                }
                            },
                        },
                        'group': {
                            'id': '${4/content/committee_id/value}',
                            'content': {
                                'last_committee_invited_reminded_date': {
                                    'value': '${4/tmdate}'
                                }
                            }
                        }
                    }
                }
            }
        )

        self.post_invitation_edit(invitation)


        invitation_id = f'{self.template_domain}/-/Committee_Recruitment_Response'

        invitation = Invitation(id=invitation_id,
            invitees=[self.template_domain],
            readers=['everyone'],
            writers=[self.template_domain],
            signatures=[self.template_domain],
            edit = {
                'signatures': [self.template_domain],
                'readers': [self.template_domain],
                'writers': [self.template_domain],
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
                    'venue_short_name': {
                        'order': 2,
                        'description': 'Venue shot name',
                        'value': {
                            'param': {
                                'type': 'string'
                            }
                        }
                    },                    
                    'committee_id': {
                        'order': 3,
                        'description': 'Venue reviewers name',
                        'value': {
                            'param': {
                                'type': 'string',
                                'maxLength': 100
                            }
                        }
                    },
                    'committee_pretty_name': {
                        'order': 4,
                        'description': 'Committee pretty name',
                        'value': {
                            'param': {
                                'type': 'string',
                                'maxLength': 100,
                                'default': 'Reviewers'
                            }
                        }
                    },
                    'due_date': {
                        'order': 5,
                        'description': 'By when do users can submit their response?',
                        'value': {
                            'param': {
                                'type': 'date',
                                'range': [ 0, 9999999999999 ],
                                'optional': True,
                                'deletable': True
                            }
                        }
                    },
                    'hash_seed': {
                        'order': 6,
                        'description': 'Invitation hash seed',
                        'value': {
                            'param': {
                                'type': 'string',
                                'maxLength': 100
                            }
                        }
                    }
                },
                'domain': '${1/content/venue_id/value}',
                'invitation': {
                    'id': '${2/content/committee_id/value}/-/Recruitment_Response',
                    'duedate': '${2/content/due_date/value}',
                    'expdate': '${2/content/due_date/value}',
                    'invitees': ['everyone'],
                    'signatures': ['${3/content/venue_id/value}'], 
                    'readers': ['everyone'],
                    'writers': ['${3/content/venue_id/value}'],
                    'description': 'Configure the timeframe users invitees can accept or decline ${2/content/committee_pretty_name/value} recruitment invitations, whether or not they can accept with a reduced load, and customize the email responses when they accept or decline the invitation to serve as a ${2/content/committee_pretty_name/value}. Go to the **[${2/content/committee_pretty_name/value} group](/group/edit?id=${2/content/committee_id/value})** to recruit reviewers.',
                    'preprocess': self.get_process_content('process/committee_recruitment_response_pre_process.js'),
                    'process': self.get_process_content('process/committee_recruitment_response_process.py'),
                    'web': self.get_webfield_content('webfield/committeeRecruitmentResponseWebfield.js'),
                    'content': {
                        'hash_seed': {
                            'value': '${4/content/hash_seed/value}',
                            'readers': ['${5/content/venue_id/value}']
                        },
                        'committee_id': {
                            'value': '${4/content/committee_id/value}',
                        },
                        'committee_pretty_name': {
                            'value': '${4/content/committee_pretty_name/value}',
                        },
                        'declined_message_subject_template': {
                            'value': '[${4/content/venue_short_name/value}] ${4/content/committee_pretty_name/value} Invitation declined'                               
                        },                        
                        'declined_message_body_template': {
                            'value': '''You have declined the invitation to become a reviewer for ${4/content/venue_short_name/value}.

If you would like to change your decision, please follow the link in the previous invitation email and click on the "Accept" button.'''
                        },
                        'accepted_message_subject_template': {
                            'value': '[${4/content/venue_short_name/value}] ${4/content/committee_pretty_name/value} Invitation accepted'                                
                        },                        
                        'accepted_message_body_template': {
                            'value': '''Thank you for accepting the invitation to be a ${4/content/committee_pretty_name/value} for ${4/content/venue_short_name/value}.

The ${4/content/venue_short_name/value} program chairs will be contacting you with more information regarding next steps soon. In the meantime, please add noreply@openreview.net to your email contacts to ensure that you receive all communications.

If you would like to change your decision, please follow the link in the previous invitation email and click on the "Decline" button.'''
                        }                         
                    },
                    'edit': {
                        'signatures': ['(guest)'],
                        'readers': ['${4/content/venue_id/value}'],
                        'note': {
                            'signatures':['${3/signatures}'],
                            'readers': ['${5/content/venue_id/value}', '${2/content/user/value}'],
                            'writers': ['${5/content/venue_id/value}'],
                            'content': {
                                'title': {
                                    'order': 1,
                                    'description': 'Title',
                                    'value': { 
                                        'param': { 
                                            'type': 'string',
                                            'const': 'Recruit response'
                                        }
                                    }
                                },
                                'user': {
                                    'order': 2,
                                    'description': 'email address',
                                    'value': { 
                                        'param': { 
                                            'type': 'string',
                                            'regex': '.*'
                                        }
                                    }
                                },
                                'key': {
                                    'order': 3,
                                    'description': 'Email key hash',
                                    'value': { 
                                        'param': { 
                                            'type': 'string',
                                            'regex': '.{0,100}'
                                        }
                                    }
                                },
                                "response": {
                                    'order': 4,
                                    'description': 'Invitation response',
                                    'value': {
                                        'param': {
                                            'type': 'string',
                                            'enum': ['Yes', 'No'],
                                            'input': 'radio'
                                        }
                                    }
                                },
                                'comment': {
                                    'order': 5,
                                    'description': '(Optionally) Leave a comment to the organizers of the venue.',
                                    'value': {
                                        'param': {
                                            'type': 'string',
                                            'maxLength': 5000,
                                            'optional': True,
                                            'deletable': True,
                                            'input': 'textarea'
                                        }
                                    }
                                },
                                # TODO: Wait for Xukun to implement the data release agreement in the recruitment form
                                # 'release_data_agreement': {
                                #     'order': 6,
                                #     'description': 'Please checl this box to confirm that you agree to release your data to the public.',
                                #     'value': {
                                #         'param': {
                                #             'type': 'string',
                                #             'input': 'checkbox',
                                #             'enum': ['I agree the number of reviews I have completed can be made public.'],
                                #         }
                                #     }                                    
                                # }
                            }
                        }
                    }
                }
            }
        )

        self.post_invitation_edit(invitation)       

    def setup_group_message_template_invitation(self):
        
        invitation_id = f'{self.template_domain}/-/Group_Message'

        invitation = Invitation(id=invitation_id,
            invitees=[self.template_domain],
            readers=['everyone'],
            writers=[self.template_domain],
            signatures=[self.template_domain],
            edit = {
                'signatures': [self.template_domain],
                'readers': [self.template_domain],
                'writers': [self.template_domain],
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
                    'group_id': {
                        'order': 2,
                        'description': 'Venue group id',
                        'value': {
                            'param': {
                                'type': 'string'
                            }
                        }
                    },
                    'message_reply_to': {
                        'order': 3,
                        'description': 'Venue reply to address',
                        'value': {
                            'param': {
                                'type': 'string'
                            }
                        }
                    },
                    'venue_short_name': {
                        'order': 4,
                        'description': 'Venue shot name',
                        'value': {
                            'param': {
                                'type': 'string'
                            }
                        }
                    },
                    'venue_from_email': {
                        'order': 5,
                        'description': 'Venue from name',
                        'value': {
                            'param': {
                                'type': 'string'
                            }
                        }
                    }
                },
                'domain': '${1/content/venue_id/value}',
                'invitation': {
                    'id': '${2/content/group_id/value}/-/Message',
                    'invitees': ['${3/content/venue_id/value}'],
                    'signatures': ['${3/content/venue_id/value}'], 
                    'readers': ['${3/content/venue_id/value}'],
                    'writers': ['${3/content/venue_id/value}'],
                    'description': 'Message any group members',
                    'message': {
                        'replyTo': '${3/content/message_reply_to/value}',
                        'subject': { 'param': { 'minLength': 1 } },
                        'message': { 'param': { 'minLength': 1 } },
                        'groups': { 'param': { 'inGroup': '${5/content/group_id/value}' } },
                        'parentGroup': '${3/content/group_id/value}',
                        'ignoreGroups': { 'param': { 'regex': r'~.*|([a-z0-9_\-\.]{2,}@[a-z0-9_\-\.]{2,}\.[a-z]{2,},){0,}([a-z0-9_\-\.]{2,}@[a-z0-9_\-\.]{2,}\.[a-z]{2,})', 'optional': True } },
                        'signature': '${3/content/venue_id/value}',
                        'fromName': '${3/content/venue_short_name/value}',
                        'fromEmail': '${3/content/venue_from_email/value}',
                        'useJob': { 'param': { 'enum': [True, False], 'optional': True } },
                    }
                }
            }
        )

        self.post_invitation_edit(invitation)        
    
        invitation_id = f'{self.template_domain}/-/Venue_Message'

        invitation = Invitation(id=invitation_id,
            invitees=[self.template_domain],
            readers=['everyone'],
            writers=[self.template_domain],
            signatures=[self.template_domain],
            edit = {
                'signatures': [self.template_domain],
                'readers': [self.template_domain],
                'writers': [self.template_domain],
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
                    'message_reply_to': {
                        'order': 3,
                        'description': 'Venue reply to address',
                        'value': {
                            'param': {
                                'type': 'string'
                            }
                        }
                    },
                    'venue_short_name': {
                        'order': 4,
                        'description': 'Venue shot name',
                        'value': {
                            'param': {
                                'type': 'string'
                            }
                        }
                    },
                    'venue_from_email': {
                        'order': 5,
                        'description': 'Venue from name',
                        'value': {
                            'param': {
                                'type': 'string'
                            }
                        }
                    }
                },
                'domain': '${1/content/venue_id/value}',
                'invitation': {
                    'id': '${2/content/venue_id/value}/-/Message',
                    'invitees': ['${3/content/venue_id/value}'],
                    'signatures': ['${3/content/venue_id/value}'], 
                    'readers': ['${3/content/venue_id/value}'],
                    'writers': ['${3/content/venue_id/value}'],
                    'description': 'Message any group members',
                    'message': {
                        'replyTo': '${3/content/message_reply_to/value}',
                        'subject': { 'param': { 'minLength': 1 } },
                        'message': { 'param': { 'minLength': 1 } },
                        'groups': { 'param': { 'regex': '${5/content/venue_id/value}.*' } },
                        'parentGroup': '${3/content/venue_id/value}',
                        'ignoreGroups': { 'param': { 'regex': r'~.*|([a-z0-9_\-\.]{2,}@[a-z0-9_\-\.]{2,}\.[a-z]{2,},){0,}([a-z0-9_\-\.]{2,}@[a-z0-9_\-\.]{2,}\.[a-z]{2,})', 'optional': True } },
                        'signature': '${3/content/venue_id/value}',
                        'fromName': '${3/content/venue_short_name/value}',
                        'fromEmail': '${3/content/venue_from_email/value}',
                        'useJob': { 'param': { 'enum': [True, False], 'optional': True } },
                    }
                }
            }
        )

        self.post_invitation_edit(invitation)    

    def setup_group_members_template_invitation(self):

        invitation_id = f'{self.template_domain}/-/Group_Members'

        invitation = Invitation(id=invitation_id,
            invitees=[self.template_domain],
            readers=['everyone'],
            writers=[self.template_domain],
            signatures=[self.template_domain],
            edit = {
                'signatures': [self.template_domain],
                'readers': [self.template_domain],
                'writers': [self.template_domain],
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
                    'group_id': {
                        'order': 2,
                        'description': 'Venue group id',
                        'value': {
                            'param': {
                                'type': 'string'
                            }
                        }
                    }
                },
                'domain': '${1/content/venue_id/value}',
                'invitation': {
                    'id': '${2/content/group_id/value}/-/Members',
                    'invitees': ['${3/content/venue_id/value}'],
                    'signatures': ['${3/content/venue_id/value}'], 
                    'readers': ['${3/content/venue_id/value}'],
                    'writers': ['${3/content/venue_id/value}'],
                    'description': 'Add and remove members to the group',
                    'edit': {
                        'signatures': ['${4/content/venue_id/value}'],
                        'readers': ['${4/content/venue_id/value}'],
                        'writers': ['${4/content/venue_id/value}'],
                        'group': {
                            'id': '${4/content/group_id/value}',
                            'members': {
                                'param': {
                                    'regex': '.*',
                                }
                            }
                        }
                    }
                }
            }
        )

        self.post_invitation_edit(invitation)        
 
    def setup_reviewer_conflicts_template_invitation(self):

        invitation_id = f'{self.template_domain}/-/Reviewer_Conflict'

        invitation = Invitation(id=invitation_id,
            invitees=['active_venues'],
            readers=['everyone'],
            writers=[self.template_domain],
            signatures=[self.template_domain],
            process=self.get_process_content('workflow_process/reviewer_conflicts_template_process.py'),
            edit = {
                'signatures' : {
                    'param': {
                        'items': [
                            { 'prefix': '~.*', 'optional': True },
                            { 'value': self.template_domain, 'optional': True }
                        ]
                    }
                },
                'readers': [self.template_domain],
                'writers': [self.template_domain],
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
                        'description': 'Name for this step, use underscores to represent spaces. Default is Conflict.',
                        'value': {
                            'param': {
                                'type': 'string',
                                'maxLength': 100,
                                'regex': '^[a-zA-Z0-9_]*$',
                                'default': 'Conflict'
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
                    'reviewers_name': {
                        'order': 5,
                        'value': {
                            'param': {
                                'type': 'string',
                                'maxLength': 100,
                                'regex': '^[a-zA-Z0-9_]*$',
                                'default': 'Reviewers'
                            }
                        }
                    },
                },
                'domain': '${1/content/venue_id/value}',
                'invitation': {
                    'id': '${2/content/venue_id/value}/${2/content/reviewers_name/value}/-/${2/content/name/value}',
                    'invitees': ['${3/content/venue_id/value}/Automated_Administrator'],
                    'signatures': ['${3/content/venue_id/value}'],
                    'readers': ['${3/content/venue_id/value}'],
                    'writers': ['${3/content/venue_id/value}'],
                    'cdate': '${2/content/activation_date/value}',
                    'description': 'This step runs automatically at its "activation date", and creates "edges" between reviewers and article submissions to represent identified conflicts of interest. Configure the conflict of interest policy to be applied and specify the number of years of data to be retrieved from the OpenReview profile for conflict detection.',
                    'dateprocesses': [{
                        'dates': ["#{4/cdate}", self.update_date_string],
                        'script': self.get_process_content('process/compute_conflicts_process.py')
                    }],
                    'content': {
                        'committee_name': {
                            'value': '${4/content/reviewers_name/value}'
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
                                'withInvitation': '${5/content/venue_id/value}/${5/content/reviewers_name/value}/-/${5/content/name/value}',
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
                                    'group': '${6/content/venue_id/value}/${6/content/reviewers_name/value}'
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

        invitation_id = f'{self.template_domain}/-/Reviewer_Submission_Affinity_Score'

        invitation = Invitation(id=invitation_id,
            invitees=['active_venues'],
            readers=['everyone'],
            writers=[self.template_domain],
            signatures=[self.template_domain],
            process=self.get_process_content('workflow_process/reviewer_affinities_template_process.py'),
            edit = {
                'signatures' : {
                    'param': {
                        'items': [
                            { 'prefix': '~.*', 'optional': True },
                            { 'value': self.template_domain, 'optional': True }
                        ]
                    }
                },
                'readers': [self.template_domain],
                'writers': [self.template_domain],
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
                        'description': 'Name for this step, use underscores to represent spaces. Default is Affinity_Score.',
                        'value': {
                            'param': {
                                'type': 'string',
                                'maxLength': 100,
                                'regex': '^[a-zA-Z0-9_]*$',
                                'default': 'Affinity_Score'
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
                    'reviewers_name': {
                        'order': 5,
                        'value': {
                            'param': {
                                'type': 'string',
                                'maxLength': 100,
                                'regex': '^[a-zA-Z0-9_]*$',
                                'default': 'Reviewers'
                            }
                        }
                    },
                    'authors_name': {
                        'order': 6,
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
                'invitation': {
                    'id': '${2/content/venue_id/value}/${2/content/reviewers_name/value}/-/${2/content/name/value}',
                    'invitees': ['${3/content/venue_id/value}/Automated_Administrator'],
                    'signatures': ['${3/content/venue_id/value}'],
                    'readers': ['${3/content/venue_id/value}'],
                    'writers': ['${3/content/venue_id/value}'],
                    'cdate': '${2/content/activation_date/value}',
                    'description': '<span>This step runs automatically at its "activation date", and creates "edges" between reviewers and article submissions that represent reviewer expertise. Configure which expertise model will compute affinity scores. (We find that the model "specter2+scincl" has the best performance; refer to our <a href=https://github.com/openreview/openreview-expertise>expertise repository</a> for more information on the models.)</span>',
                    'dateprocesses': [{
                        'dates': ["#{4/cdate}", self.update_date_string],
                        'script': self.get_process_content('process/compute_affinity_scores_process.py')
                    }],
                    'content': {
                        'committee_name': {
                            'value': '${4/content/reviewers_name/value}'
                        }
                    },
                    'edge': {
                        'id': {
                            'param': {
                                'withInvitation': '${5/content/venue_id/value}/${5/content/reviewers_name/value}/-/${5/content/name/value}',
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
                        'nonreaders': ['${4/content/venue_id/value}/${4/content/authors_name/value}'],
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
                                    'group': '${6/content/venue_id/value}/${6/content/reviewers_name/value}'
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

    def setup_reviewer_assignment_configuration_template_invitation(self):

        invitation = Invitation(id=f'{self.template_domain}/-/Reviewers_Assignment_Configuration',
            invitees=['active_venues'],
            readers=['everyone'],
            writers=[self.template_domain],
            signatures=[self.template_domain],
            edit = {
                'signatures' : {
                    'param': {
                        'items': [
                            { 'prefix': '~.*', 'optional': True },
                            { 'value': self.template_domain, 'optional': True }
                        ]
                    }
                },
                'readers': [self.template_domain],
                'writers': [self.template_domain],
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
                        'description': 'Name for this step, use underscores to represent spaces. Default is Assignment_Configuration.',
                        'value': {
                            'param': {
                                'type': 'string',
                                'maxLength': 100,
                                'regex': '^[a-zA-Z0-9_]*$',
                                'default': 'Assignment_Configuration'
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
                    'reviewers_name': {
                        'order': 4,
                        'value': {
                            'param': {
                                'type': 'string',
                                'maxLength': 100,
                                'regex': '^[a-zA-Z0-9_]*$',
                                'default': 'Reviewers'
                            }
                        }
                    }
                },
                'domain': '${1/content/venue_id/value}',
                'invitation': {
                    'id': '${2/content/venue_id/value}/${2/content/reviewers_name/value}/-/${2/content/name/value}',
                    'invitees': ['${3/content/venue_id/value}'],
                    'signatures': ['${3/content/venue_id/value}'],
                    'readers': ['${3/content/venue_id/value}'],
                    'writers': ['${3/content/venue_id/value}'],
                    'process': self.get_process_content(('process/assignment_configuration_process.py')),
                    'edit': {
                        'signatures': ['${4/content/venue_id/value}'],
                        'readers': ['${4/content/venue_id/value}'],
                        'writers': ['${4/content/venue_id/value}'],
                        'note': {
                            'id': {
                                'param': {
                                    'withInvitation': '${6/content/venue_id/value}/${6/content/reviewers_name/value}/-/${6/content/name/value}',
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
                            'signatures': ['${5/content/venue_id/value}'],
                            'readers': ['${5/content/venue_id/value}'],
                            'writers': ['${5/content/venue_id/value}'],
                            'content': {
                                'title': {
                                    'order': 1,
                                    'description': 'Title of the configuration.',
                                    'value': {
                                        'param': {
                                            'type': 'string',
                                            'regex': '^[^,;:]{1,250}$',
                                            'mismatchError': 'must be 250 characters or less and not contain the following characters: ; : or ,'
                                        }
                                    }
                                },
                                'user_demand': {
                                    'order': 2,
                                    'description': 'Number of users that can review a paper',
                                    'value': {
                                        'param': {
                                            'type': 'string',
                                            'regex': '[0-9]+'
                                        }
                                    }
                                },
                                'max_papers': {
                                    'order': 3,
                                    'description': 'Max number of reviews a user has to do',
                                    'value': {
                                        'param': {
                                            'type': 'string',
                                            'regex': '[0-9]+'
                                        }
                                    }
                                },
                                'min_papers': {
                                    'order': 4,
                                    'description': 'Min number of reviews a user should do',
                                    'value': {
                                        'param': {
                                            'type': 'string',
                                            'regex': '[0-9]+'
                                        }
                                    }
                                },
                                'alternates': {
                                    'order': 5,
                                    'description': 'The number of alternate reviewers to save (per-paper)',
                                    'value': {
                                        'param': {
                                            'type': 'string',
                                            'regex': '[0-9]+'
                                        }
                                    }
                                },
                                'paper_invitation': {
                                    'order': 6,
                                    'description': 'Invitation to get the paper metadata or Group id to get the users to be matched',
                                    'value': {
                                        'param': {
                                            'type': 'string',
                                            'regex': '${8/content/venue_id/value}/-/${8/content/submission_name/value}.*',
                                            'default': '${8/content/venue_id/value}/-/${8/content/submission_name/value}&content.venueid=${8/content/venue_id/value}/${8/content/submission_name/value}'
                                        }
                                    }
                                },
                                'match_group': {
                                    'order': 7,
                                    'description': 'Group id containing users to be matched',
                                    'value': {
                                        'param': {
                                            'type': 'string',
                                            'regex': '${8/content/venue_id/value}/.*',
                                            'default': '${8/content/venue_id/value}/${8/content/reviewers_name/value}',
                                        }
                                    }
                                },
                                'scores_specification': {
                                    'order': 8,
                                    'description': 'Manually entered JSON score specification',
                                    'value': {
                                        'param': {
                                            'type': 'json',
                                            'optional': True
                                        }
                                    }
                                },
                                'aggregate_score_invitation': {
                                    'order': 9,
                                    'description': 'Invitation to store aggregated scores',
                                    'value': {
                                        'param': {
                                            'type': 'string',
                                            'regex': '${8/content/venue_id/value}/.*',
                                            'default': '${8/content/venue_id/value}/${8/content/reviewers_name/value}/-/Aggregate_Score',
                                            'hidden': True
                                        }
                                    }
                                },
                                'conflicts_invitation': {
                                    'order': 10,
                                    'description': 'Invitation to store conflict scores',
                                    'value': {
                                        'param': {
                                            'type': 'string',
                                            'regex': '${8/content/venue_id/value}/.*',
                                            'default': '${8/content/venue_id/value}/${8/content/reviewers_name/value}/-/Conflict',
                                        }
                                    }
                                },
                                'assignment_invitation': {
                                    'order': 11,
                                    'description': 'Invitation to store paper user assignments',
                                    'value': {
                                        'param': {
                                            'type': 'string',
                                            'const': '${8/content/venue_id/value}/${8/content/reviewers_name/value}/-/Proposed_Assignment',
                                            'hidden': True
                                        }
                                    }
                                },
                                'deployed_assignment_invitation': {
                                    'order': 12,
                                    'description': 'Invitation to store deployed paper user assignments',
                                    'value': {
                                        'param': {
                                            'type': 'string',
                                            'const': '${8/content/venue_id/value}/${8/content/reviewers_name/value}/-/Assignment',
                                            'hidden': True
                                        }
                                    }
                                },
                                'invite_assignment_invitation': {
                                    'order': 13,
                                    'description': 'Invitation used to invite external or emergency reviewers',
                                    'value': {
                                        'param': {
                                            'type': 'string',
                                            'const': '${8/content/venue_id/value}/${8/content/reviewers_name/value}/-/Invite_Assignment',
                                            'hidden': True
                                        }
                                    }
                                },
                                'custom_user_demand_invitation': {
                                    'order': 14,
                                    'description': 'Invitation to store custom number of users required by papers',
                                    'value': {
                                        'param': {
                                            'type': 'string',
                                            'regex': '${8/content/venue_id/value}/.*/-/Custom_User_Demands$',
                                            'default': '${8/content/venue_id/value}/${8/content/reviewers_name/value}/-/Custom_User_Demands',
                                            'optional': True,
                                            'deletable': True
                                        }
                                    }
                                },
                                'custom_max_papers_invitation': {
                                    'order': 15,
                                    'description': 'Invitation to store custom max number of papers that can be assigned to reviewers',
                                    'value': {
                                        'param': {
                                            'type': 'string',
                                            'regex': '${8/content/venue_id/value}/.*/-/Custom_Max_Papers$',
                                            'default': '${8/content/venue_id/value}/${8/content/reviewers_name/value}/-/Custom_Max_Papers',
                                            'optional': True,
                                            'deletable': True
                                        }
                                    }
                                },
                                'config_invitation': {
                                    'order': 16,
                                    'value': {
                                        'param': {
                                            'type': 'string',
                                            'const':  '${8/content/venue_id/value}/${8/content/reviewers_name/value}/-/${8/content/name/value}',
                                            'hidden': True
                                        }
                                    }
                                },
                                'solver': {
                                    'order': 17,
                                    'value': {
                                        'param': {
                                            'type': 'string',
                                            'enum': ['MinMax', 'FairFlow', 'Randomized', 'FairSequence', 'PerturbedMaximization'],
                                            'input': 'radio'
                                        }
                                    }
                                },
                                'status': {
                                    'order': 18,
                                    'value': {
                                        'param': {
                                            'type': 'string',
                                            'enum': [
                                                'Initialized',
                                                'Running',
                                                'Error',
                                                'No Solution',
                                                'Complete',
                                                'Deploying',
                                                'Deployed',
                                                'Deployment Error',
                                                'Undeploying',
                                                'Undeployment Error',
                                                'Queued',
                                                'Cancelled'
                                            ],
                                            'input': 'select',
                                            'default': 'Initialized'
                                        }
                                    }
                                },
                                'error_message': {
                                    'order': 19,
                                    'value': {
                                        'param': {
                                            'type': 'string',
                                            'regex':  '.*',
                                            'optional': True,
                                            'deletable': True,
                                            'hidden': True
                                        }
                                    }
                                },
                                'allow_zero_score_assignments': {
                                    'order': 20,
                                    'description': 'Select "No" only if you do not want to allow assignments with 0 scores. Note that if there are any users without publications, you need to select "Yes" in order to run a paper matching.',
                                    'value': {
                                        'param': {
                                            'type': 'string',
                                            'enum':  ['Yes', 'No'],
                                            'input': 'radio',
                                            'optional': True,
                                            'deletable': True,
                                            'default': 'Yes'
                                        }
                                    }
                                },
                                'randomized_probability_limits': {
                                    'order': 21,
                                    'description': 'Enter the probability limits if the selected solver is Randomized',
                                    'value': {
                                        'param': {
                                            'type': 'string',
                                            'regex':  r'[-+]?[0-9]*\.?[0-9]*',
                                            'optional': True,
                                            'deletable': True,
                                            'default': '1'
                                        }
                                    }
                                },
                                'randomized_fraction_of_opt': {
                                    'order': 22,
                                    'description': 'result of randomized assignment',
                                    'value': {
                                        'param': {
                                            'type': 'string',
                                            'regex':  r'[-+]?[0-9]*\.?[0-9]*',
                                            'optional': True,
                                            'deletable': True,
                                            'default': '',
                                            'hidden': True
                                        }
                                    }
                                },
                                'perturbedmaximization_perturbation':  {
                                    'order': 23,
                                    'description': 'A single float representing the perturbation factor for the Perturbed Maximization Solver. The value should be between 0 and 1, increasing the value will trade assignment quality for randomization.',
                                    'value': {
                                        'param': {
                                            'type': 'float',
                                            'range': [0, 1],
                                            'optional': True,
                                            'deletable': True,
                                            'default': '1'
                                        }
                                    }
                                },
                                'perturbedmaximization_bad_match_thresholds':  {
                                    'order': 24,
                                    'description': 'A list of floats, representing the thresholds in affinity score for categorizing a paper-reviewer match, used by the Perturbed Maximization Solver.',
                                    'value': {
                                        'param': {
                                            'type': 'float[]',
                                            'optional': True,
                                            'deletable': True,
                                            'default': [0.1, 0.3, 0.5]
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

    def setup_reviewer_matching_template_invitation(self):

        invitation = Invitation(id=f'{self.template_domain}/-/Reviewer_Assignment_Deployment',
            invitees=['active_venues'],
            readers=['everyone'],
            writers=[self.template_domain],
            signatures=[self.template_domain],
            process=self.get_process_content('workflow_process/reviewer_matching_template_process.py'),
            edit = {
                'signatures' : {
                    'param': {
                        'items': [
                            { 'prefix': '~.*', 'optional': True },
                            { 'value': self.template_domain, 'optional': True }
                        ]
                    }
                },
                'readers': [self.template_domain],
                'writers': [self.template_domain],
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
                        'description': 'Name for this step, use underscores to represent spaces. Default is Deploy_Reviewer_Assignment.',
                        'value': {
                            'param': {
                                'type': 'string',
                                'maxLength': 100,
                                'regex': '^[a-zA-Z0-9_]*$',
                                'default': 'Reviewer_Assignment_Deployment'
                            }
                        }
                    },
                    'activation_date': {
                        'value': {
                            'param': {
                                'type': 'date',
                                'range': [ 0, 9999999999999 ],
                                'deletable': True
                            }
                        }
                    },
                },
                'domain': '${1/content/venue_id/value}',
                'invitation': {
                    'id': '${2/content/venue_id/value}/-/${2/content/name/value}',
                    'invitees': ['${3/content/venue_id/value}'],
                    'signatures': ['${3/content/venue_id/value}'],
                    'readers': ['${3/content/venue_id/value}'],
                    'writers': ['${3/content/venue_id/value}'],
                    'cdate': '${2/content/activation_date/value}',
                    'description': 'This step runs automatically at its "activation date", and puts individual reviewers in the appropriate reviewer groups for each of the article submissions they are assigned to review. Configure which reviewer assignment configuration should be used among the multiple drafts you may have previously created.',
                    'dateprocesses': [{
                        'dates': ["#{4/cdate}", self.update_date_string],
                        'script': self.get_process_content('process/deploy_assignments_process.py')
                    }],
                    'edit': {
                        'signatures': ['${4/content/venue_id/value}'],
                        'readers': ['${4/content/venue_id/value}'],
                        'writers': ['${4/content/venue_id/value}'],
                    }
                }
            }
        )

        self.post_invitation_edit(invitation)

    def setup_email_decisions_template_invitation(self):

        invitation = Invitation(id=f'{self.template_domain}/-/Author_Decision_Notification',
            invitees=['active_venues'],
            readers=['everyone'],
            writers=[self.template_domain],
            signatures=[self.template_domain],
            process=self.get_process_content('workflow_process/email_authors_template_process.py'),
            edit = {
                'signatures' : {
                    'param': {
                        'items': [
                            { 'prefix': '~.*', 'optional': True },
                            { 'value': self.template_domain, 'optional': True }
                        ]
                    }
                },
                'readers': [self.template_domain],
                'writers': [self.template_domain],
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
                        'description': 'Name for this step, use underscores to represent spaces. Default is Author_Decision_Notification.',
                        'value': {
                            'param': {
                                'type': 'string',
                                'maxLength': 100,
                                'regex': '^[a-zA-Z0-9_]*$',
                                'default': 'Author_Decision_Notification'
                            }
                        }
                    },
                    'activation_date': {
                        'value': {
                            'param': {
                                'type': 'date',
                                'range': [ 0, 9999999999999 ],
                                'deletable': True
                            }
                        }
                    },
                    'short_name': {
                        'value': {
                            'param': {
                                'type': 'string',
                                'maxLength': 100,
                                'regex': '.*',
                                'hidden': True
                            }
                        }
                    },
                    'from_email': {
                        'value': {
                            'param': {
                                'type': 'string',
                                'maxLength': 100,
                                'regex': '.*'
                            }
                        }
                    },
                     'message_reply_to': {
                        'order': 3,
                        'value': {
                            'param': {
                                'type': 'string'
                            }
                        }
                    }
                },
                'domain': '${1/content/venue_id/value}',
                'invitation': {
                    'id': '${2/content/venue_id/value}/-/${2/content/name/value}',
                    'invitees': ['${3/content/venue_id/value}/Automated_Administrator'],
                    'signatures': ['${3/content/venue_id/value}'],
                    'readers': ['${3/content/venue_id/value}'],
                    'writers': ['${3/content/venue_id/value}'],
                    'cdate': '${2/content/activation_date/value}',
                    'description': 'This step runs automatically at its "activation date", and notifies authors that decisions are available. Configure the email subject and message to be sent to authors.',
                    'dateprocesses': [{
                        'dates': ["#{4/cdate}", self.update_date_string],
                        'script': self.get_process_content('process/email_decisions_process.py')
                    }],
                    'content': {
                        'subject': {
                            'value': '[${4/content/short_name/value}] The decision for your submission #{submission_number}, titled "{submission_title}" is now available'
                        },
                        'message': {
                            'value': 'Hi {{{{fullname}}}},\n\nThis is to inform you that the decision for your submission #{submission_number}, "{submission_title}", to ${4/content/short_name/value} is now available.\n\n{formatted_decision}\n\nTo view this paper, please go to https://openreview.net/forum?id={submission_forum}'
                        }
                    },
                    'message': {
                        'replyTo': '${3/content/message_reply_to/value}',
                        'subject': { 'param': { 'minLength': 1 } },
                        'message': { 'param': { 'minLength': 1 } },
                        'groups': { 'param': { 'inGroup': '${5/content/venue_id/value}/Authors' } },
                        'parentGroup': '${3/content/venue_id/value}/Authors',
                        'ignoreGroups': { 'param': { 'regex': r'~.*|([a-z0-9_\-\.]{2,}@[a-z0-9_\-\.]{2,}\.[a-z]{2,},){0,}([a-z0-9_\-\.]{2,}@[a-z0-9_\-\.]{2,}\.[a-z]{2,})', 'optional': True } },
                        'signature': '${3/content/venue_id/value}',
                        'fromName': '${3/content/short_name/value}',
                        'fromEmail': '${3/content/from_email/value}',
                        'useJob': False
                    }
                }
            }
        )

        self.post_invitation_edit(invitation)

    def setup_email_reviews_template_invitation(self):

        invitation = Invitation(id=f'{self.template_domain}/-/Author_Reviews_Notification',
            invitees=['active_venues'],
            readers=['everyone'],
            writers=[self.template_domain],
            signatures=[self.template_domain],
            process=self.get_process_content('workflow_process/email_authors_template_process.py'),
            edit = {
                'signatures' : {
                    'param': {
                        'items': [
                            { 'prefix': '~.*', 'optional': True },
                            { 'value': self.template_domain, 'optional': True }
                        ]
                    }
                },
                'readers': [self.template_domain],
                'writers': [self.template_domain],
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
                        'description': 'Name for this step, use underscores to represent spaces. Default is Author_Reviews_Notification.',
                        'value': {
                            'param': {
                                'type': 'string',
                                'maxLength': 100,
                                'regex': '^[a-zA-Z0-9_]*$',
                                'default': 'Author_Reviews_Notification'
                            }
                        }
                    },
                    'activation_date': {
                        'value': {
                            'param': {
                                'type': 'date',
                                'range': [ 0, 9999999999999 ],
                                'deletable': True
                            }
                        }
                    },
                    'short_name': {
                        'value': {
                            'param': {
                                'type': 'string',
                                'maxLength': 100,
                                'regex': '.*',
                                'hidden': True
                            }
                        }
                    },
                    'from_email': {
                        'value': {
                            'param': {
                                'type': 'string',
                                'maxLength': 100,
                                'regex': '.*'
                            }
                        }
                    },
                     'message_reply_to': {
                        'value': {
                            'param': {
                                'type': 'string'
                            }
                        }
                    }
                },
                'domain': '${1/content/venue_id/value}',
                'invitation': {
                    'id': '${2/content/venue_id/value}/-/${2/content/name/value}',
                    'invitees': ['${3/content/venue_id/value}/Automated_Administrator'],
                    'signatures': ['${3/content/venue_id/value}'],
                    'readers': ['${3/content/venue_id/value}'],
                    'writers': ['${3/content/venue_id/value}'],
                    'cdate': '${2/content/activation_date/value}',
                    'description': 'This step runs automatically at its "activation date", and notifies authors that reviews are available. Configure the email subject and message to be sent to authors, and specify which review form fields to include in the email.',
                    'dateprocesses': [{
                        'dates': ["#{4/cdate}", self.update_date_string],
                        'script': self.get_process_content('process/email_reviews_process.py')
                    }],
                    'content': {
                        'subject': {
                            'value': '[${4/content/short_name/value}] The reviews for your submission #{submission_number}, titled "{submission_title}" are now available'
                        },
                        'message': {
                            'value': 'Hi {{{{fullname}}}},\n\nThis is to inform you that the reviews for your submission #{submission_number}, "{submission_title}", to ${4/content/short_name/value} are now available.\n\n{formatted_reviews}\nTo view this paper, please go to https://openreview.net/forum?id={submission_forum}'
                        }
                    },
                    'message': {
                        'replyTo': '${3/content/message_reply_to/value}',
                        'subject': { 'param': { 'minLength': 1 } },
                        'message': { 'param': { 'minLength': 1 } },
                        'groups': { 'param': { 'inGroup': '${5/content/venue_id/value}/Authors' } },
                        'parentGroup': '${3/content/venue_id/value}/Authors',
                        'ignoreGroups': { 'param': { 'regex': r'~.*|([a-z0-9_\-\.]{2,}@[a-z0-9_\-\.]{2,}\.[a-z]{2,},){0,}([a-z0-9_\-\.]{2,}@[a-z0-9_\-\.]{2,}\.[a-z]{2,})', 'optional': True } },
                        'signature': '${3/content/venue_id/value}',
                        'fromName': '${3/content/short_name/value}',
                        'fromEmail': '${3/content/from_email/value}',
                        'useJob': False
                    }
                }
            }
        )
        self.post_invitation_edit(invitation)

    def set_paper_release_template_invitation(self):

        invitation = Invitation(id=f'{self.template_domain}/-/Submission_Release',
            invitees=['active_venues'],
            readers=['everyone'],
            writers=[self.template_domain],
            signatures=[self.template_domain],
            process=self.get_process_content('workflow_process/submission_release_template_process.py'),
            edit = {
                'signatures' : {
                    'param': {
                        'items': [
                            { 'prefix': '~.*', 'optional': True },
                            { 'value': self.template_domain, 'optional': True }
                        ]
                    }
                },
                'readers': [self.template_domain],
                'writers': [self.template_domain],
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
                    'activation_date': {
                        'order': 2,
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
                    },
                    'authors_name': {
                        'order': 4,
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
                    }
                },
                'domain': '${1/content/venue_id/value}',
                'invitation': {
                    'id': '${2/content/venue_id/value}/-/${2/content/submission_name/value}_Release',
                    'invitees': ['${3/content/venue_id/value}/Automated_Administrator'],
                    'signatures': ['${3/content/venue_id/value}'],
                    'readers': ['${3/content/venue_id/value}'],
                    'writers': ['${3/content/venue_id/value}'],
                    'cdate': '${2/content/activation_date/value}',
                    'description': 'This step runs automatically at its "activation date", and releases submissions to the public. Configure which submissions (all submissions or only accepted submissions) to release to the public.',
                    'dateprocesses': [{
                        'dates': ["#{4/cdate}", self.update_date_string],
                        'script': self.get_process_content('process/submission_release.py')
                    }],
                    'content': {
                        'source': {
                            'value': 'accepted_submissions'
                        }
                    },
                    'edit': {
                        'signatures': ['${4/content/venue_id/value}'],
                        'readers': ['${4/content/venue_id/value}', '${4/content/venue_id/value}/${4/content/submission_name/value}${{2/note/id}/number}/${4/content/authors_name/value}'],
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
                            'pdate': {
                                'param': {
                                    'range': [ 0, 9999999999999 ],
                                    'optional': True,
                                    'deletable': True
                                }
                            },
                            'signatures': [ '${5/content/venue_id/value}/${5/content/submission_name/value}${{2/id}/number}/${5/content/authors_name/value}'],
                            'readers': ['everyone'],
                            'writers': [
                                '${5/content/venue_id/value}',
                                '${5/content/venue_id/value}/${5/content/submission_name/value}${{2/id}/number}/${5/content/authors_name/value}'
                            ],
                            'content': {
                                'authors': {
                                    'readers': { 'param': { 'regex': '.*', 'deletable': True } }
                                },
                                'authorids': {
                                    'readers': { 'param': { 'regex': '.*', 'deletable': True } }
                                },
                                'venue': {
                                    'value': {
                                        'param': {
                                            'type': 'string',
                                            'regex': '.*'
                                        }
                                    }
                                },
                                'venueid': {
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

    def setup_article_endorsement_template_invitation(self):

        invitation = Invitation(id=f'{self.super_id}/-/Article_Endorsement',
            invitees=['active_venues'],
            readers=['everyone'],
            writers=[self.template_domain],
            signatures=[self.template_domain],
            edit = {
                'signatures' : {
                    'param': {
                        'items': [
                            { 'prefix': '~.*', 'optional': True },
                            { 'value': self.template_domain, 'optional': True }
                        ]
                    }
                },
                'readers': [self.template_domain],
                'writers': [self.template_domain],
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
                    },
                },
                'domain': '${1/content/venue_id/value}',
                'invitation': {
                    'id': '${2/content/venue_id/value}/-/Article_Endorsement',
                    'invitees': ['${3/content/venue_id/value}'],
                    'signatures': ['${3/content/venue_id/value}'],
                    'readers': ['${3/content/venue_id/value}'],
                    'writers': ['${3/content/venue_id/value}'],
                    'tag': {
                        'signature': '${3/content/venue_id/value}',
                        'readers': ['everyone'],
                        'writers': ['${4/content/venue_id/value}'],
                        'id': {
                            'param': {
                                'withInvitation': '${5/content/venue_id/value}/-/Article_Endorsement',
                                'optional': True
                            }
                        },
                        'forum': {
                            'param': {
                                'withInvitation': '${5/content/venue_id/value}/-/${5/content/submission_name/value}'
                            }
                        },
                        'note': {
                            'param': {
                                'withInvitation': '${5/content/venue_id/value}/-/${5/content/submission_name/value}'
                            }
                        },
                        'label': {
                            'param': {
                                'regex': '.*',
                                'optional': True
                            }
                        },
                        'cdate': {
                            'param': {
                                'range': [ 0, 9999999999999 ],
                                'optional': True
                            }
                        },
                    }
                }
            }
        )

        self.client.post_invitation_edit(invitations=f'{self.super_id}/-/Edit',
            readers=[self.template_domain],
            writers=[self.template_domain],
            signatures=['~Super_User1'],
            invitation=invitation
        )

    def setup_reviewers_review_count_template_invitation(self):

        invitation = Invitation(id=f'{self.super_id}/-/Reviewers_Review_Count',
            invitees=['active_venues'],
            readers=['everyone'],
            writers=[self.template_domain],
            signatures=[self.template_domain],
            process=self.get_process_content('workflow_process/reviewers_stats_template_process.py'),
            content={
                'date_process_script': {
                    'value': self.get_process_content('process/reviewers_review_count_process.py')
                }
            },              
            edit = {
                'signatures' : {
                    'param': {
                        'items': [
                            { 'prefix': '~.*', 'optional': True },
                            { 'value': self.template_domain, 'optional': True }
                        ]
                    }
                },
                'readers': [self.template_domain],
                'writers': [self.template_domain],
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
                    'reviewers_id': {
                        'order': 2,
                        'description': 'Reviewers id',
                        'value': {
                            'param': {
                                'type': 'string',
                            }
                        }
                    },
                    'activation_date': {
                        'order': 3,
                        'description': 'When should we compute the number of reviews for each reviewer?',
                        'value': {
                            'param': {
                                'type': 'date',
                                'range': [ 0, 9999999999999 ],
                                'deletable': True
                            }
                        }
                    },                    
                },
                'domain': '${1/content/venue_id/value}',
                'invitation': {
                    'id': '${2/content/reviewers_id/value}/-/Review_Count',
                    'invitees': ['${3/content/venue_id/value}'],
                    'signatures': ['${3/content/venue_id/value}'],
                    'readers': ['${3/content/venue_id/value}'],
                    'writers': ['${3/content/venue_id/value}'],
                    'cdate': '${2/content/activation_date/value}',
                    'description': 'This step runs automatically at its "activation date", and computes the review counts for all reviewers.',
                    'dateprocesses': [{
                        'dates': ["#{4/cdate}", self.update_date_string],
                        'script': '''def process(client, invitation):
    meta_invitation = client.get_invitation(invitation.invitations[0])
    script = meta_invitation.content['date_process_script']['value']
    funcs = {
        'openreview': openreview,
        'datetime': datetime,
    }
    exec(script, funcs)
    funcs['process'](client, invitation)
''' 
                    }],
                    'tag': {
                        'signature': '${3/content/venue_id/value}',
                        'readers': ['${4/content/venue_id/value}', '${4/content/reviewers_id/value}/Review_Count/Readers', '${2/profile}'],
                        'writers': ['${4/content/venue_id/value}'],
                        'id': {
                            'param': {
                                'withInvitation': '${5/content/reviewers_id/value}/-/Review_Count',
                                'optional': True
                            }
                        },
                        'profile': {
                            'param': {
                                'inGroup': '${5/content/reviewers_id/value}'
                            }
                        },
                        'weight': {
                            'param': {
                                'minimum': 0,
                            }
                        },
                        'cdate': {
                            'param': {
                                'range': [ 0, 9999999999999 ],
                                'optional': True
                            }
                        },
                    }
                }
            }
        )

        self.client.post_invitation_edit(invitations=f'{self.super_id}/-/Edit',
            readers=[self.template_domain],
            writers=[self.template_domain],
            signatures=['~Super_User1'],
            invitation=invitation
        )

    def setup_reviewers_review_assignment_count_template_invitation(self):

        invitation = Invitation(id=f'{self.super_id}/-/Reviewers_Review_Assignment_Count',
            invitees=['active_venues'],
            readers=['everyone'],
            writers=[self.template_domain],
            signatures=[self.template_domain],
            process=self.get_process_content('workflow_process/reviewers_stats_template_process.py'),
            content={
                'date_process_script': {
                    'value': self.get_process_content('process/reviewers_assignment_count_process.py')
                }
            },             
            edit = {
                'signatures' : {
                    'param': {
                        'items': [
                            { 'prefix': '~.*', 'optional': True },
                            { 'value': self.template_domain, 'optional': True }
                        ]
                    }
                },
                'readers': [self.template_domain],
                'writers': [self.template_domain],
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
                    'reviewers_id': {
                        'order': 2,
                        'description': 'Reviewers id',
                        'value': {
                            'param': {
                                'type': 'string',
                            }
                        }
                    },
                    'activation_date': {
                        'order': 3,
                        'description': 'When should we compute the number of reviews for each reviewer?',
                        'value': {
                            'param': {
                                'type': 'date',
                                'range': [ 0, 9999999999999 ],
                                'deletable': True
                            }
                        }
                    },                    
                },
                'domain': '${1/content/venue_id/value}',
                'invitation': {
                    'id': '${2/content/reviewers_id/value}/-/Review_Assignment_Count',
                    'invitees': ['${3/content/venue_id/value}'],
                    'signatures': ['${3/content/venue_id/value}'],
                    'readers': ['${3/content/venue_id/value}'],
                    'writers': ['${3/content/venue_id/value}'],
                    'cdate': '${2/content/activation_date/value}',
                    'description': 'This step runs automatically at its "activation date", and computes the review assignment counts for all reviewers.',
                    'dateprocesses': [{
                        'dates': ["#{4/cdate}", self.update_date_string],
                        'script': '''def process(client, invitation):
    meta_invitation = client.get_invitation(invitation.invitations[0])
    script = meta_invitation.content['date_process_script']['value']
    funcs = {
        'openreview': openreview,
        'datetime': datetime,
    }
    exec(script, funcs)
    funcs['process'](client, invitation)
''' 
                    }],
                    'tag': {
                        'signature': '${3/content/venue_id/value}',
                        'readers': ['${4/content/venue_id/value}', '${4/content/reviewers_id/value}/Review_Assignment_Count/Readers', '${2/profile}'],
                        'nonreaders': ['${4/content/reviewers_id/value}/Review_Assignment_Count/NonReaders'],
                        'writers': ['${4/content/venue_id/value}'],
                        'id': {
                            'param': {
                                'withInvitation': '${5/content/reviewers_id/value}/-/Review_Assignment_Count',
                                'optional': True
                            }
                        },
                        'profile': {
                            'param': {
                                'inGroup': '${5/content/reviewers_id/value}'
                            }
                        },
                        'weight': {
                            'param': {
                                'minimum': 0,
                            }
                        },
                        'cdate': {
                            'param': {
                                'range': [ 0, 9999999999999 ],
                                'optional': True
                            }
                        },
                    }
                }
            }
        )

        self.client.post_invitation_edit(invitations=f'{self.super_id}/-/Edit',
            readers=[self.template_domain],
            writers=[self.template_domain],
            signatures=['~Super_User1'],
            invitation=invitation
        )

    def setup_reviewers_review_days_late_template_invitation(self):

        invitation = Invitation(id=f'{self.super_id}/-/Reviewers_Review_Days_Late_Sum',
            invitees=['active_venues'],
            readers=['everyone'],
            writers=[self.template_domain],
            signatures=[self.template_domain],
            process=self.get_process_content('workflow_process/reviewers_stats_template_process.py'),
            content={
                'date_process_script': {
                    'value': self.get_process_content('process/reviewers_review_days_late_sum_process.py')
                }
            },            
            edit = {
                'signatures' : {
                    'param': {
                        'items': [
                            { 'prefix': '~.*', 'optional': True },
                            { 'value': self.template_domain, 'optional': True }
                        ]
                    }
                },
                'readers': [self.template_domain],
                'writers': [self.template_domain],
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
                    'reviewers_id': {
                        'order': 2,
                        'description': 'Reviewers id',
                        'value': {
                            'param': {
                                'type': 'string',
                            }
                        }
                    },
                    'activation_date': {
                        'order': 3,
                        'description': 'When should we compute the number of reviews for each reviewer?',
                        'value': {
                            'param': {
                                'type': 'date',
                                'range': [ 0, 9999999999999 ],
                                'deletable': True
                            }
                        }
                    },                    
                },
                'domain': '${1/content/venue_id/value}',
                'invitation': {
                    'id': '${2/content/reviewers_id/value}/-/Review_Days_Late_Sum',
                    'invitees': ['${3/content/venue_id/value}'],
                    'signatures': ['${3/content/venue_id/value}'],
                    'readers': ['${3/content/venue_id/value}'],
                    'writers': ['${3/content/venue_id/value}'],
                    'cdate': '${2/content/activation_date/value}',
                    'description': 'This step runs automatically at its "activation date", and computes the total number of days a reviewer was late submitting their reviews.',
                    'dateprocesses': [{
                        'dates': ["#{4/cdate}", self.update_date_string],
                        'script': '''def process(client, invitation):
    meta_invitation = client.get_invitation(invitation.invitations[0])
    script = meta_invitation.content['date_process_script']['value']
    funcs = {
        'openreview': openreview,
        'datetime': datetime,
    }
    exec(script, funcs)
    funcs['process'](client, invitation)
''' 
                    }],
                    'tag': {
                        'signature': '${3/content/venue_id/value}',
                        'readers': ['${4/content/venue_id/value}', '${4/content/reviewers_id/value}/Review_Days_Late_Sum/Readers', '${2/profile}'],
                        'nonreaders': ['${4/content/reviewers_id/value}/Review_Days_Late_Sum/NonReaders'],
                        'writers': ['${4/content/venue_id/value}'],
                        'id': {
                            'param': {
                                'withInvitation': '${5/content/reviewers_id/value}/-/Review_Days_Late_Sum',
                                'optional': True
                            }
                        },
                        'profile': {
                            'param': {
                                'inGroup': '${5/content/reviewers_id/value}'
                            }
                        },
                        'weight': {
                            'param': {
                                'minimum': 0,
                            }
                        },
                        'cdate': {
                            'param': {
                                'range': [ 0, 9999999999999 ],
                                'optional': True
                            }
                        },
                    }
                }
            }
        )

        self.client.post_invitation_edit(invitations=f'{self.super_id}/-/Edit',
            readers=[self.template_domain],
            writers=[self.template_domain],
            signatures=['~Super_User1'],
            invitation=invitation
        )

    def setup_committee_roles_invitations(self):

        def create_role_invitation(role):
            invitation = Invitation(id=f'{self.super_id}/-/{role}_Role',
                invitees=['active_venues'],
                readers=['everyone'],
                writers=[self.template_domain],
                signatures=[self.template_domain],
                process=self.get_process_content('workflow_process/reviewers_stats_template_process.py'),
                content={
                    'role_process_script': {
                        'value': self.get_process_content(f'process/{role.lower()}_role_process.py')
                    }
                },
                edit = {
                    'signatures' : {
                        'param': {
                            'items': [
                                { 'prefix': '~.*', 'optional': True },
                                { 'value': self.template_domain, 'optional': True }
                            ]
                        }
                    },
                    'readers': [self.template_domain],
                    'writers': [self.template_domain],
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
                        'committee_name': {
                            'order': 2,
                            'description': 'Committee name',
                            'value': {
                                'param': {
                                    'type': 'string',
                                }
                            }
                        },
                        'activation_date': {
                            'order': 3,
                            'description': 'When should we compute the number of reviews for each reviewer?',
                            'value': {
                                'param': {
                                    'type': 'date',
                                    'range': [ 0, 9999999999999 ],
                                    'deletable': True
                                }
                            }
                        },                    
                    },
                    'domain': '${1/content/venue_id/value}',
                    'invitation': {
                        'id': '${2/content/venue_id/value}/-/${2/content/committee_name/value}',
                        'invitees': ['${3/content/venue_id/value}'],
                        'signatures': ['${3/content/venue_id/value}'],
                        'readers': ['${3/content/venue_id/value}'],
                        'writers': ['${3/content/venue_id/value}'],
                        'cdate': '${2/content/activation_date/value}',
                        'description': f'This step runs automatically at its "activation date", and it creates tags for all the users that performed the {role} role. This tag will be shown in each user\'s profile and it is visible to everyone.',
                        'dateprocesses': [{
                            'dates': ["#{4/cdate}", self.update_date_string],
                            'script': '''def process(client, invitation):
    meta_invitation = client.get_invitation(invitation.invitations[0])
    script = meta_invitation.content['role_process_script']['value']
    funcs = {
        'openreview': openreview,
        'datetime': datetime,
    }
    exec(script, funcs)
    funcs['process'](client, invitation)
''' 
                        }],
                        'tag': {
                            'signature': '${3/content/venue_id/value}',
                            'readers': ['everyone'],
                            'writers': ['${4/content/venue_id/value}'],
                            'cdate': {
                                'param': {
                                    'range': [ 0, 9999999999999 ],
                                    'optional': True
                                }
                            },
                            'id': {
                                'param': {
                                    'withInvitation': '${5/content/venue_id/value}/-/${5/content/committee_name/value}',
                                    'optional': True
                                }
                            },
                            'profile': {
                                'param': {
                                    'regex': '~.*'
                                }
                            },
                            'cdate': {
                                'param': {
                                    'range': [ 0, 9999999999999 ],
                                    'optional': True
                                }
                            },
                        }
                    }
                }
            )

            self.client.post_invitation_edit(invitations=f'{self.super_id}/-/Edit',
                readers=[self.template_domain],
                writers=[self.template_domain],
                signatures=['~Super_User1'],
                invitation=invitation
            )

        create_role_invitation('Reviewer')
        create_role_invitation('Ethics_Reviewer')
        create_role_invitation('Meta_Reviewer')
        create_role_invitation('Senior_Meta_Reviewer')

        create_role_invitation('Ethics_Chair')
        create_role_invitation('Program_Chair')
        create_role_invitation('Publication_Chair')
        create_role_invitation('Workflow_Chair')

    def setup_llm_pdf_response_template_invitation(self):

        invitation = Invitation(id=f'{self.template_domain}/-/LLM_PDF_Response',
            invitees=['active_venues'],
            readers=['everyone'],
            writers=[self.template_domain],
            signatures=[self.template_domain],
            process=self.get_process_content('workflow_process/llm_pdf_response_template_process.py'),
            edit = {
                'signatures' : {
                    'param': {
                        'items': [
                            { 'prefix': '~.*', 'optional': True },
                            { 'value': self.template_domain, 'optional': True }
                        ]
                    }
                },
                'readers': [self.template_domain],
                'writers': [self.template_domain],
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
                        'description': 'Name for this step, use underscores to represent spaces. Default is LLM_PDF_Response.',
                        'value': {
                            'param': {
                                'type': 'string',
                                'maxLength': 100,
                                'regex': '^[a-zA-Z0-9_]*$',
                                'default': 'LLM_PDF_Response'
                            }
                        }
                    },
                    'child_name': {
                        'order': 4,
                        'description': 'Name for the child invitation, use underscores to represent spaces. Default is LLM_PDF_Feedback.',
                        'value': {
                            'param': {
                                'type': 'string',
                                'maxLength': 100,
                                'regex': '^[a-zA-Z0-9_]*$',
                                'default': 'LLM_PDF_Feedback'
                            }
                        }
                    },
                    'activation_date': {
                        'order': 5,
                        'description': 'When should the reviewing of submissions begin?',
                        'value': {
                            'param': {
                                'type': 'date',
                                'range': [ 0, 9999999999999 ],
                                'deletable': True
                            }
                        }
                    },
                    'submission_name': {
                        'order': 6,
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
                    'expdate': '${2/content/activation_date/value} + 302400000',
                    'description': 'This step runs automatically at its "activation date", and generates and posts an LLM-generated response for each submission.',
                    'dateprocesses': [{
                        'dates': ["#{4/edit/invitation/cdate}", self.update_date_string],
                        'script': self.get_process_content('process/llm_pdf_response_invitation_edit_process.py')
                    }],
                    'content': {
                        'users_to_notify': {
                            'value': ['program_chairs']
                        },
                        'prompt': {
                            'value': 'Write a review for this paper, focusing on strengths and weaknesses' ## to-do
                        },
                        'model': {
                            'value': 'gemini/gemini-2.0-flash'
                        },
                        'llm_pdf_response_process_script': {
                            'value': self.get_process_content('process/llm_pdf_response_process.py')
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
                            'id': '${4/content/venue_id/value}/${4/content/submission_name/value}${2/content/noteNumber/value}/-/${4/content/child_name/value}',
                            'signatures': ['${5/content/venue_id/value}'],
                            'readers': ['everyone'],
                            'writers': ['${5/content/venue_id/value}'],
                            'invitees': ['${5/content/venue_id/value}'],
                            'maxReplies': 1,
                            'cdate': '${4/content/activation_date/value}',
                            'process': '''def process(client, edit, invitation):
    meta_invitation = client.get_invitation(invitation.invitations[0])
    script = meta_invitation.content['llm_pdf_response_process_script']['value']
    funcs = {
        'openreview': openreview
    }
    exec(script, funcs)
    funcs['process'](client, edit, invitation)''',
                            'edit': {
                                'signatures': {
                                    'param': {
                                        'items': [
                                            { 'value': '${9/content/venue_id/value}/Automated_Administrator', 'optional': True}
                                        ]
                                    }
                                },
                                'readers': ['${2/note/readers}'],
                                'writers': ['${6/content/venue_id/value}'],
                                'note': {
                                    'id': {
                                        'param': {
                                            'withInvitation': '${8/content/venue_id/value}/${8/content/submission_name/value}${6/content/noteNumber/value}/-/${8/content/child_name/value}',
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
                                    'writers': ['${7/content/venue_id/value}', '${3/signatures}'],
                                    'content': {
                                        'title': {
                                            'order': 1,
                                            'description': 'Title',
                                            'value': {
                                                'param': {
                                                    'type': 'string',
                                                    'const': 'LLM-Generated Feedback'
                                                }
                                            }
                                        },
                                        'feedback': {
                                            'order': 2,
                                            'value': {
                                                'param': {
                                                    'type': 'string',
                                                    'maxLength': 200000,
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
