
import openreview.api
from ... import openreview
from openreview.api import Invitation
import os
from ...stages import default_content

class VenueConfiguration():

    def __init__(self, client, support_group_id, super_user):
        self.support_group_id = support_group_id
        self.client = client
        self.super_user = super_user
        self.meta_invitation_id = f'{super_user}/-/Edit'

    def setup(self):
        self.set_meta_invitation()
        self.set_conference_venue_invitation()
        self.set_comment_invitation()
        self.set_deploy_invitation()
        self.set_venues_homepage()

        #setup stage templates
        workflow_invitations = WorkflowInvitations(self.client, self.support_group_id, self.super_user)
        workflow_invitations.setup_metareview_template_invitation()
        workflow_invitations.setup_comment_template_invitation()
        workflow_invitations.setup_decision_template_invitation()

    def get_process_content(self, file_path):
        process = None
        with open(os.path.join(os.path.dirname(__file__), file_path)) as f:
            process = f.read()
            return process

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

    def set_venues_homepage(self):

        with open(os.path.join(os.path.dirname(__file__), 'webfield/venuepageWebfield.js')) as f:
            content = f.read()
            self.client.post_group_edit(
                invitation=self.meta_invitation_id,
                signatures=['~Super_User1'],
                group=openreview.api.Group(
                    id='venues',
                    web=content
                )
            )

    def set_conference_venue_invitation(self):

        super_user = self.super_user
        conference_venue_invitation_id = f'{super_user}/-/Venue_Configuration_Request'

        invitation_content = {
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
                        'type': 'string',
                        'regex': r'^[0-9]{4}\/([1-9]|0[1-9]|1[0-2])\/([1-9]|0[1-9]|[1-2][0-9]|3[0-1])(\s+)?((2[0-3]|[01][0-9]|[0-9]):[0-5][0-9])?(\s+)?$',
                        'optional': True
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
            'publication_chairs': {
                'order': 9,
                'description': 'Will your venue have Publication Chairs? The Publication Chairs will only have access to accepted submissions (including author names) and the author accepted group in order to email authors of accepted submissions.',
                'value': {
                    'param': {
                        'type': 'string',
                        'enum': [
                            'Yes, our venue has Publication Chairs',
                            'No, our venue does not have Publication Chairs'
                        ],
                        'input': 'radio'
                    }
                }
            },
            'area_chairs_and_senior_area_chairs' : {
                'order': 10,
                'description': 'Will your venue have Area Chairs and Senior Area Chairs?',
                'value': {
                    'param': {
                        'type': 'string',
                        'enum': [
                            'Yes, our venue has Area Chairs and Senior Area Chairs',
                            'Yes, our venue has Area Chairs, but no Senior Area Chairs',
                            'No, our venue does not have Area Chairs nor Senior Area Chairs'
                        ],
                        'input': 'radio'
                    }
                }
            },
            'ethics_chairs_and_reviewers' : {
                'order': 11,
                'description': 'Will your venue have Ethics Chairs and Ethics Reviewers?',
                'value': {
                    'param': {
                        'type': 'string',
                        'enum': [
                            'Yes, our venue has Ethics Chairs and Reviewers',
                            'No, our venue does not have Ethics Chairs and Reviewers'
                        ],
                        'input': 'radio'
                    }
                }
            },
            'secondary_area_chairs': {
                'order': 12,
                'description': 'Will your venue have Secondary Area Chairs?',
                'value': {
                    'param': {
                        'type': 'string',
                        'enum': [
                            'Yes, our venue has Secondary Area Chairs',
                            'No, our venue does not have Secondary Area Chairs'
                        ],
                        'input': 'radio'
                    }
                }
            },
            'submission_start_date': {
                'order': 13,
                'description': 'When should your OpenReview submission portal open? Please specify the date and time in GMT using the following format: YYYY/MM/DD HH:MM(e.g. 2019/01/31 23:59). (Leave blank if you would like the portal to open for submissions as soon as possible)',
                'value': {
                    'param': {
                        'type': 'string',
                        'regex': r'^[0-9]{4}\/([1-9]|0[1-9]|1[0-2])\/([1-9]|0[1-9]|[1-2][0-9]|3[0-1])(\s+)?((2[0-3]|[01][0-9]|[0-9]):[0-5][0-9])?(\s+)?$',
                        'optional': True
                    }
                }
            },
            'abstract_registration_deadline': {
                'order': 14,
                'description': 'By when do authors need to register their manuscripts? Please specify the due date in GMT using the following format: YYYY/MM/DD HH:MM(e.g. 2019/01/31 23:59) (Skip this if there is no abstract registration deadline)',
                'value': {
                    'param': {
                        'type': 'string',
                        'regex': r'^[0-9]{4}\/([1-9]|0[1-9]|1[0-2])\/([1-9]|0[1-9]|[1-2][0-9]|3[0-1])(\s+)?((2[0-3]|[01][0-9]|[0-9]):[0-5][0-9])?(\s+)?$',
                        'optional': True
                    }
                }
            },
            'submission_deadline': {
                'order': 15,
                'description': 'By when do authors need to submit their manuscripts? Please specify the due date in GMT using the following format: YYYY/MM/DD HH:MM(e.g. 2019/01/31 23:59)',
                'value': {
                    'param': {
                        'type': 'string',
                        'regex': r'^[0-9]{4}\/([1-9]|0[1-9]|1[0-2])\/([1-9]|0[1-9]|[1-2][0-9]|3[0-1])(\s+)?((2[0-3]|[01][0-9]|[0-9]):[0-5][0-9])?(\s+)?$',
                        'optional': True
                    }
                }
            },
            'author_and_reviewer_anonymity': {
                'order': 16,
                'description': 'Whick best describes your anonymity policy?',
                'value': {
                    'param': {
                        'type': 'string',
                        'enum': [
                            'Double-blind',
                            'Single-blind (Reviewers are anonymous)',
                            'No anonymity'
                        ],
                        'input': 'radio'
                    }
                }
            },
            # 'force_profiles_only': {
            #     'order': 17,
            #     'description': 'Submitting authors must have an OpenReview profile, however, should all co-authors be required to have profiles?',
            #     'value': {
            #         'param': {
            #             'type': 'string',
            #             'enum': [
            #                 'Yes, require all authors to have an OpenReview profile',
            #                 'No, allow submissions with email addresses'
            #             ],
            #             'input': 'radio'
            #         }
            #     }
            # },
            # 'submission_readers': {
            #     'order': 18,
            #     'description': 'Please select who should have access to the submissions after the abstract deadline (if your venue has one) or the submission deadline. Note that program chairs and paper authors are always readers of submissions.',
            #     'value': {
            #         'param': {
            #             'type': 'string',
            #             'enum': [
            #                 'All program committee (all reviewers, all area chairs, all senior area chairs if applicable)',
            #                 'All area chairs only',
            #                 'Assigned program committee (assigned reviewers, assigned area chairs, assigned senior area chairs if applicable)',
            #                 'Program chairs and paper authors only',
            #                 'Everyone (submissions are public)'
            #             ],
            #             'input': 'radio'
            #         }
            #     }
            # },
            'submission_license': {
                'order': 19,
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
            # 'email_pcs_for_new_submissions': {
            #     'order': 20,
            #     'description': 'Should PCs receive an email for every new submission?',
            #     'value': {
            #         'param': {
            #             'type': 'string',
            #             'enum': [
            #                 'Yes, email PCs for every new submission.',
            #                 'No, do not email PCs.'
            #             ],
            #             'input': 'radio'
            #         }
            #     }
            # },
            'other_important_information': {
                'order': 21,
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
            },
            'commitments_venue': {
                'order': 22,
                'value': {
                    'param': {
                        'type': 'string',
                        'enum': ['Yes', 'No'],
                        'input': 'radio',
                        'hidden': True,
                        'optional': True
                    }
                }
            }
        }

        invitation = Invitation(
            id = conference_venue_invitation_id,
            invitees = ['everyone'],
            readers = ['everyone'],
            writers = [],
            signatures = [super_user],
            edit = {
                'signatures': { 'param': { 'regex': '~.*' } },
                'writers': ['${2/note/writers}'],
                'readers': ['${2/note/readers}'],
                'note': {
                    'signatures': ['${3/signatures}'],
                    'readers': [ self.support_group_id, '${2/content/program_chair_emails/value}', '${3/signatures}' ],
                    'writers': [ self.support_group_id, '${2/content/program_chair_emails/value}', '${3/signatures}'],
                    'content': invitation_content,
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

    def set_comment_invitation(self):

        super_user = self.super_user
        comment_invitation_id = f'{super_user}/-/Comment'
        support_group_id = self.support_group_id
        
        invitation = Invitation(
            id = comment_invitation_id,
            invitees = [support_group_id],
            readers = ['everyone'],
            writers = [support_group_id],
            signatures = [support_group_id],
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
                                'regex': '.*', 'type': 'string' 
                            }
                        }
                    }
                },
                'replacement': True,
                'invitation': {
                    'id': f'{super_user}/Venue_Configuration_Request' + '${2/content/noteNumber/value}' + '/-/Comment',
                    'signatures': [ support_group_id ],
                    'readers': ['everyone'],
                    'writers': [support_group_id],
                    'invitees': ['everyone'],
                    'edit': {
                        'signatures': { 
                            'param': { 
                                'items': [ 
                                    { 'value': support_group_id, 'optional': True },
                                    { 'prefix': '~.*', 'optional': True } ] 
                            }
                        },
                        'readers': ['${2/note/readers}'],
                        'writers': [support_group_id],
                        'note': {
                            'id': {
                                'param': {
                                    'withInvitation': f'{super_user}/Venue_Configuration_Request' + '${6/content/noteNumber/value}' + '/-/Comment',
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
                            'readers': [support_group_id, '${{3/note/forum}/content/program_chair_emails/value}'],
                            'writers': [support_group_id, '${3/signatures}'],
                            'signatures': ['${3/signatures}'],
                            'content': {
                                'title': {
                                    'order': 1,
                                    'description': 'Brief summary of your comment.',
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
                                    'description': 'Your comment or reply (max 200000 characters).',
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
        )

        self.post_invitation_edit(invitation)

    def set_deploy_invitation(self):

        deploy_invitation_id = f'{self.super_user}/-/Deploy'
        support_group_id = self.support_group_id
        super_user = self.super_user

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
                                'regex': '.*', 'type': 'string' 
                            }
                        }
                    }
                },
                'replacement': True,
                'invitation': {
                    'id': f'{super_user}/Venue_Configuration_Request' + '${2/content/noteNumber/value}' + '/-/Deploy',
                    'signatures': [ '~Super_User1' ],
                    'readers': ['everyone'],
                    'writers': [support_group_id],
                    'invitees': [support_group_id],
                    'maxReplies': 1,
                    'process': '''def process(client, edit, invitation):
    meta_invitation = client.get_invitation(invitation.invitations[0])
    script = meta_invitation.content['deploy_process_script']['value']
    funcs = {
        'openreview': openreview
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

class WorkflowInvitations():

    def __init__(self, client, support_group_id, super_user):
        self.support_group_id = support_group_id
        self.client = client
        self.super_user = super_user
        self.meta_invitation_id = f'{super_user}/-/Edit'

    def post_invitation_edit(self, invitation):
        return self.client.post_invitation_edit(invitations=self.meta_invitation_id,
            readers=['~Super_User1'],
            writers=['~Super_User1'],
            signatures=['~Super_User1'],
            invitation=invitation,
            replacement=True
        )

    def get_process_content(self, file_path):
        process = None
        with open(os.path.join(os.path.dirname(__file__), file_path)) as f:
            process = f.read()
            return process

    def setup_metareview_template_invitation(self):

        support_group_id = self.support_group_id
        invitation_id = f'{support_group_id}/-/Meta_Review_Template'

        invitation = Invitation(id=invitation_id,
            invitees=['active_venues'],
            readers=['everyone'],
            writers=[support_group_id],
            signatures=[self.super_user],
            process=self.get_process_content('process/templates_process.py'),
            edit = {
                'signatures': {
                    'param': {
                        'items': [
                            { 'prefix': '~.*', 'optional': True }
                        ]
                    }
                },
                'readers': [support_group_id],
                'writers': [support_group_id],
                'content' :{
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
                        'description': 'Name for this step, use underscores to represent spaces. Default is Meta_Review. This name will be shown in the button users will click to perform this step.',
                        'value': {
                            'param': {
                                'type': 'string',
                                'maxLength': 100,
                                'regex': '^[a-zA-Z0-9_]*$',
                                'default': 'Meta_Review'
                            }
                        }
                    },
                    'activation_date': {
                        'order': 3,
                        'description': 'When should the meta reviewing of submissions begin?',
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
                        'description': 'By when should the meta-reviews be in the system? This is the official, soft deadline area chairs will see.',
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
                        'order': 5,
                        'description': 'After this date, no more meta reviews can be submitted. This is the hard deadline area chairs will not be able to see.',
                        'value': {
                            'param': {
                                'type': 'date',
                                'range': [ 0, 9999999999999 ],
                                'optional': True,
                                'deletable': True
                            }
                        }
                    },
                    'readers': {
                        'order': 6,
                        'description': 'Select who should be able to read the meta reviews as soon as they are posted.',
                        'value': {
                            'param': {
                                'type': 'string[]',
                                'input': 'select',
                                'items': [
                                    {'value': 'Program_Chairs', 'optional': False, 'description': 'Program Chairs'},
                                    {'value': 'Senior_Area_Chairs', 'optional': False, 'description': 'Assigned Senior Area Chairs (if applicable)'},
                                    {'value': 'Area_Chairs', 'optional': False, 'description': 'Assigned Area Chairs'},
                                    {'value': 'Reviewers', 'optional': True, 'description': 'Assigned Reviewers'},
                                    {'value': 'Reviewers/Submitted', 'optional': True, 'description': 'Assigned reviewers who have submitted a review'},
                                    {'value': 'Authors', 'optional': True, 'description': 'Paper Authors'},
                                    {'value': 'Everyone', 'optional': True, 'description': 'Public'}
                                ]
                            }
                        }
                    },
                    'content': {
                        'order': 7,
                        'description': 'Configure what fields the meta review should contain.',
                        'value': {
                            'param': {
                                'type': 'json',
                                'default': default_content.meta_review_v2
                            }
                        }
                    },
                    'recommendation_field_name': {
                        'order': 8,
                        'description': 'Name of the field that will store the recommendation. Default is recommendation. This field should be defined in the content field above.',
                        'value': {
                            'param': {
                                'type': 'string',
                                'regex': '.*',
                                'default': 'recommendation'
                            }
                        }
                    }
                },
                'domain': '${1/content/venue_id/value}',
                'invitation': {
                    'id': '${2/content/venue_id/value}/-/${2/content/name/value}',
                    'signatures': ['${3/content/venue_id/value}'],
                }
            }
        )

        self.post_invitation_edit(invitation)

    def setup_comment_template_invitation(self):

        support_group_id = self.support_group_id
        invitation_id = f'{support_group_id}/-/Comment_Template'

        invitation = Invitation(id=invitation_id,
            invitees=['active_venues'],
            readers=['everyone'],
            writers=[support_group_id],
            signatures=[self.super_user],
            process = self.get_process_content('process/templates_process.py'),
            edit = {
                'signatures': {
                    'param': {
                        'items': [
                            { 'prefix': '~.*', 'optional': True }
                        ]
                    }
                },
                'readers': [support_group_id],
                'writers': [support_group_id],
                'content' :{
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
                        'order': 3,
                        'description': 'When does official and/or public commentary begin?',
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
                        'description': 'When does official and/or public commentary end?',
                        'value': {
                            'param': {
                                'type': 'date',
                                'range': [ 0, 9999999999999 ],
                                'optional': True,
                                'deletable': True
                            }
                        }
                    },
                    'participants': {
                        'order': 5,
                        'description': 'Select who should be allowed to post comments on submissions. These will be added as readers automatically.',
                        'value': {
                            'param': {
                                'type': 'string[]',
                                'input': 'select',
                                'items': [
                                    {'value': 'Program Chairs', 'optional': False, 'description': 'Program Chairs'},
                                    {'value': 'Assigned Senior Area Chairs', 'optional': False, 'description': 'Assigned Senior Area Chairs'},
                                    {'value': 'Assigned Area Chairs', 'optional': False, 'description': 'Assigned Area Chairs'},
                                    {'value': 'Assigned Reviewers', 'optional': True, 'description': 'Assigned Reviewers'},
                                    {'value': 'Assigned Reviewers Submitted', 'optional': True, 'description': 'Assigned reviewers who have submitted a review'},
                                    {'value': 'Paper Authors', 'optional': True, 'description': 'Paper Authors'},
                                    {'value': 'Everyone (anonymously)', 'optional': True, 'description': 'Public (anonymously)'},
                                    {'value': 'Everyone (non-anonymously)', 'optional': True, 'description': 'Public (non-anonymously)'}
                                ],
                                'default': ['Program Chairs']
                            }
                        }
                    },
                    'additional_readers': {
                        'order': 6,
                        'description': 'Select who should only be allowed to view the comments on submissions (other than the participants). ',
                        'value': {
                            'param': {
                                'type': 'string[]',
                                'input': 'select',
                                'items': [
                                    {'value': 'Program Chairs', 'optional': False, 'description': 'Program Chairs'},
                                    {'value': 'Assigned Senior Area Chairs', 'optional': False, 'description': 'Assigned Senior Area Chairs'},
                                    {'value': 'Assigned Area Chairs', 'optional': False, 'description': 'Assigned Area Chairs'},
                                    {'value': 'Assigned Reviewers', 'optional': True, 'description': 'Assigned Reviewers'},
                                    {'value': 'Assigned Reviewers Submitted', 'optional': True, 'description': 'Assigned reviewers who have submitted a review'},
                                    {'value': 'Paper Authors', 'optional': True, 'description': 'Paper Authors'},
                                    {'value': 'Everyone', 'optional': True, 'description': 'Public'}
                                ],
                                'optional': True
                            }
                        }
                    },
                    'email_program_chairs_about_official_comments': {
                        'order': 7,
                        'description': 'Should the PCs receive an email for each official comment made in the venue? Default is no.',
                        'value': {
                            'param': {
                                'type': 'string',
                                'enum': [
                                    'Yes, email PCs for every new comment.',
                                    'No, do not email PCs.'
                                ],
                                'input': 'radio',
                                'default': 'No, do not email PCs.'
                            }
                        }
                    },
                    'email_senior_area_chairs_about_official_comments': {
                        'order': 8,
                        'description': 'Should the SACs (if applicable) receive an email for each official comment made in the venue? Default is no.',
                        'value': {
                            'param': {
                                'type': 'string',
                                'enum': [
                                    'Yes, email SACs for every new comment.',
                                    'No, do not email SACs.'
                                ],
                                'input': 'radio',
                                'default': 'No, do not email SACs.'
                            }
                        }
                    }
                },
                'domain': '${1/content/venue_id/value}',
                'invitation': {
                    'id': '${2/content/venue_id/value}/-/${2/content/stage_name/value}',
                    'signatures': ['${3/content/venue_id/value}'],
                }
            }
        )

        self.post_invitation_edit(invitation)

    def setup_decision_template_invitation(self):

        support_group_id = self.support_group_id
        invitation_id = f'{support_group_id}/-/Decision_Template'

        invitation = Invitation(id=invitation_id,
            invitees=['active_venues'],
            readers=['everyone'],
            writers=[support_group_id],
            signatures=[self.super_user],
            process = self.get_process_content('process/templates_process.py'),
            edit = {
                'signatures': {
                    'param': {
                        'items': [
                            { 'prefix': '~.*', 'optional': True }
                        ]
                    }
                },
                'readers': [support_group_id],
                'writers': [support_group_id],
                'content' :{
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
                        'order': 3,
                        'description': 'When will the program chairs start posting decisions?',
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
                        'order': 4,
                        'description': 'By when should all the decisions be in the system?',
                        'value': {
                            'param': {
                                'type': 'date',
                                'range': [ 0, 9999999999999 ],
                                'deletable': True
                            }
                        }
                    },
                    'decision_options': {
                        'order': 5,
                        'description': 'List all decision options. For example: Accept, Reject, Invite to Workshop. Default options are: Accept (Oral), Accept (Poster), Reject',
                        'value': {
                            'param': {
                                'type': 'string[]',
                                'regex': '.+',
                                'default': ['Accept (Oral)', 'Accept (Poster)', 'Reject']
                            }
                        }
                    },
                    'readers': {
                        'order': 6,
                        'description': 'Select who should be able to read the decisions as soon as they are posted.',
                        'value': {
                            'param': {
                                'type': 'string[]',
                                'input': 'select',
                                'items': [
                                    {'value': 'Program Chairs', 'optional': False, 'description': 'Program Chairs'},
                                    {'value': 'Assigned Senior Area Chairs', 'optional': True, 'description': 'Assigned Senior Area Chairs'},
                                    {'value': 'Assigned Area Chairs', 'optional': True, 'description': 'Assigned Area Chairs'},
                                    {'value': 'Assigned Reviewers', 'optional': True, 'description': 'Assigned Reviewers'},
                                    {'value': 'Paper Authors', 'optional': True, 'description': 'Paper Authors'},
                                    {'value': 'Everyone', 'optional': True, 'description': 'Public'}
                                ]
                            }
                        }
                    }
                },
                'domain': '${1/content/venue_id/value}',
                'invitation': {
                    'id': '${2/content/venue_id/value}/-/${2/content/stage_name/value}',
                    'signatures': ['${3/content/venue_id/value}'],
                }
            }
        )

        self.post_invitation_edit(invitation)