
import openreview.api
from ... import openreview
from openreview.api import Invitation
import os

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
                                'regex': '.*', 'type': 'integer' 
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
                    'maxReplies': 1,
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
                            'id': f'{super_user}/Venue_Configuration_Request' + '${4/content/noteNumber/value}' + '/-/Comment',
                            'forum': '${4/content/noteId/value}',
                            'replyto': '${4/content/noteId/value}',
                            'ddate': {
                                'param': {
                                    'range': [ 0, 9999999999999 ],
                                    'optional': True,
                                    'deletable': True
                                }
                            },
                            'readers': [support_group_id, '{{2/note/id}/content/program_chair_emails/value}'],
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
                                'regex': '.*', 'type': 'integer' 
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

    def __init__(self, client, support_group_id, super_user, venue_id):
        self.support_group_id = support_group_id
        self.client = client
        self.super_user = super_user
        self.venue_id = venue_id

    def setup_submission_config_invitation(self):

        venue_id = self.venue_id
        config_invitation_id = f'{venue_id}/-/Config/Submission'

        invitation = Invitation(id=config_invitation_id,
            invitees=[venue_id],
            readers=[venue_id],
            writers=[venue_id],
            signatures=[venue_id],
            

        )

        

        