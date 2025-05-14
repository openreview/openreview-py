import openreview.api
import openreview
from openreview.api import Invitation
import os

class Workflows():

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
        self.set_venues_homepage()
        self.set_workflows_group()
        self.set_reviewers_only_request()
        self.set_reviewers_only_deployment()
        self.set_reviewers_only_comment()
        self.set_acs_and_reviewers_request()
        self.set_acs_and_reviewers_deployment()
        self.set_acs_and_reviewers_comment()

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

    def set_venues_homepage(self):

        self.client.post_group_edit(
            invitation=self.meta_invitation_id,
            signatures=['~Super_User1'],
            group=openreview.api.Group(
                id='venues',
                web=self.get_webfield_content('webfield/venuepageWebfield.js'),
            )
        )

    def set_workflows_group(self):

        support_group_id = self.support_group_id

        self.client.post_group_edit(
            invitation=self.meta_invitation_id,
            signatures=['~Super_User1'],
            group=openreview.api.Group(
                id=f'{support_group_id}/Venue_Request',
                readers=[support_group_id],
                writers=[support_group_id],
                signatures=[support_group_id],
                signatories=[]
            )
        )

    def set_reviewers_only_request(self):

        super_id = self.super_id
        support_group_id = self.support_group_id
        conference_venue_invitation_id = f'{support_group_id}/Venue_Request/-/Reviewers_Only'

        invitation = Invitation(
            id = conference_venue_invitation_id,
            invitees = ['everyone'],
            readers = ['everyone'],
            writers = [],
            signatures = [super_id],
            preprocess = self.get_process_content('workflow_process/request_form_preprocess.py'),
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
                                    'range': [ 0, 9999999999999 ]
                                }
                            }
                        },
                        'program_chair_emails': {
                            'order': 7,
                            'description': 'A comma separated list of *lower-cased* email addresses for the program chairs of your venue, including the PC submitting this request.',
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
                                    'range': [ 0, 9999999999999 ]
                                }
                            }
                        },
                        'submission_deadline': {
                            'order': 10,
                            'description': 'By when do authors need to submit their manuscripts? Please specify the due date in GMT using the following format: YYYY/MM/DD HH:MM(e.g. 2019/01/31 23:59)',
                            'value': {
                                'param': {
                                    'type': 'date',
                                    'range': [ 0, 9999999999999 ]
                                }
                            }
                        },
                        'submission_license': {
                            'order': 11,
                            'description': 'Which license should be applied to each submission? We recommend "CC BY 4.0". If you select multiple licenses, you allow authors to choose their license upon submission. If your license is not listed, please contact us. Refer to https://openreview.net/legal/terms for more information.',
                            'value': {
                                'param': {
                                    'type': 'string[]',
                                    'input': 'select',
                                    'items':  [
                                        {'value': 'CC BY 4.0', 'optional': True, 'description': 'CC BY 4.0'},
                                        {'value': 'CC BY-SA 4.0', 'optional': True, 'description': 'CC BY-SA 4.0'},
                                        {'value': 'CC BY-NC 4.0', 'optional': True, 'description': 'CC BY-NC 4.0'},
                                        {'value': 'CC BY-ND 4.0', 'optional': True, 'description': 'CC BY-ND 4.0'},
                                        {'value': 'CC BY-NC-SA 4.0', 'optional': True, 'description': 'CC BY-NC-SA 4.0'},
                                        {'value': 'CC BY-NC-ND 4.0', 'optional': True, 'description': 'CC BY-NC-ND 4.0'},
                                        {'value': 'CC0 1.0', 'optional': True, 'description': 'CC0 1.0'}
                                    ]
                                }
                            }
                        },
                        'reviewers_name': {
                            'order': 12,
                            'description': 'Please provide the designated name to be used for reviewers. Default is "Reviewers".',
                            'value': {
                                'param': {
                                    'type': 'string',
                                    'regex': '.{0,500}',
                                    'default': 'Reviewers'
                                }
                            }
                        },
                        'other_important_information': {
                            'order': 13,
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
                        'venue_organizer_agreement': {
                            'order': 14,
                            'description': 'In order to use OpenReview, venue chairs must agree to the following:',
                            'value': {
                                'param': {
                                    'type': 'string[]',
                                    'items': [
                                        { 'value': 'OpenReview natively supports a wide variety of reviewing workflow configurations. However, if we want significant reviewing process customizations or experiments, we will detail these requests to the OpenReview staff at least three months in advance.', 'description': 'OpenReview natively supports a wide variety of reviewing workflow configurations. However, if we want significant reviewing process customizations or experiments, we will detail these requests to the OpenReview staff at least three months in advance.', 'optional': True},
                                        { 'value': 'We will ask authors and reviewers to create an OpenReview Profile at least two weeks in advance of the paper submission deadlines.', 'description': 'We will ask authors and reviewers to create an OpenReview Profile at least two weeks in advance of the paper submission deadlines.', 'optional': True},
                                        { 'value': 'When assembling our group of reviewers, we will only include email addresses or OpenReview Profile IDs of people we know to have authored publications relevant to our venue.  (We will not solicit new reviewers using an open web form, because unfortunately some malicious actors sometimes try to create "fake ids" aiming to be assigned to review their own paper submissions.)', 'description': 'When assembling our group of reviewers, we will only include email addresses or OpenReview Profile IDs of people we know to have authored publications relevant to our venue.  (We will not solicit new reviewers using an open web form, because unfortunately some malicious actors sometimes try to create "fake ids" aiming to be assigned to review their own paper submissions.)', 'optional': True},
                                        { 'value': 'We acknowledge that, if our venue\'s reviewing workflow is non-standard, or if our venue is expecting more than a few hundred submissions for any one deadline, we should designate our own Workflow Chair, who will read the OpenReview documentation and manage our workflow configurations throughout the reviewing process.', 'description': 'We acknowledge that, if our venue’s reviewing workflow is non-standard, or if our venue is expecting more than a few hundred submissions for any one deadline, we should designate our own Workflow Chair, who will read the OpenReview documentation and manage our workflow configurations throughout the reviewing process.', 'optional': True},
                                        { 'value': 'We acknowledge that OpenReview staff work Monday-Friday during standard business hours US Eastern time, and we cannot expect support responses outside those times.  For this reason, we recommend setting submission and reviewing deadlines Monday through Thursday.', 'description': 'We acknowledge that OpenReview staff work Monday-Friday during standard business hours US Eastern time, and we cannot expect support responses outside those times.  For this reason, we recommend setting submission and reviewing deadlines Monday through Thursday.', 'optional': True},
                                        { 'value': 'We will treat the OpenReview staff with kindness and consideration.', 'description': 'We will treat the OpenReview staff with kindness and consideration.', 'optional': True},
                                        { 'value': 'We acknowledge that authors and reviewers will be required to share their preferred email.', 'description': 'We acknowledge that authors and reviewers will be required to share their preferred email.', 'optional': True},
                                        { 'value': 'We acknowledge that review counts will be collected for all the reviewers and publicly available in OpenReview.', 'description': 'We acknowledge that review counts will be collected for all the reviewers and publicly available in OpenReview.', 'optional': True},
                                        { 'value': 'We acknowledge that metadata for accepted papers will be publicly released in OpenReview.', 'description': 'We acknowledge that metadata for accepted papers will be publicly released in OpenReview.', 'optional': True}
                                    ],
                                    'input': 'checkbox'
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
            process=self.get_process_content('workflow_process/support_process.py')
        )

        self.post_invitation_edit(invitation)

    def set_reviewers_only_deployment(self):

        support_group_id = self.support_group_id
        deploy_invitation_id = f'{support_group_id}/Venue_Request/Reviewers_Only/-/Deployment'

        invitation = Invitation(
            id = deploy_invitation_id,
            invitees = [support_group_id],
            readers = ['everyone'],
            writers = [support_group_id],
            signatures = [self.super_id],
            edit = {
                'signatures': { 
                    'param': { 
                        'items': [ { 'value': support_group_id, 'optional': True } ] 
                    }
                },
                'readers': ['${2/note/content/venue_id/value}'],
                'writers': [support_group_id],
                'note': {
                    'id': {
                        'param': {
                            'withInvitation': f'{support_group_id}/Venue_Request/-/Reviewers_Only',
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
            },
            process=self.get_process_content('workflow_process/deploy_reviewers_only_process.py')
        )

        self.post_invitation_edit(invitation)

    def set_reviewers_only_comment(self):

        support_group_id = self.support_group_id
        comment_invitation_id = f'{support_group_id}/Venue_Request/Reviewers_Only/-/Comment'

        invitation = Invitation(id=comment_invitation_id,
            invitees=[support_group_id],
            readers=['everyone'],
            writers=[support_group_id],
            signatures=[support_group_id],
            content={
                'comment_process_script': {
                    'value': self.get_process_content('workflow_process/venue_comment_process.py')
                }
            },
            edit = {
                'signatures': [support_group_id],
                'readers': [support_group_id],
                'writers': [support_group_id],
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
                    'id': f'{support_group_id}/Venue_Request/Reviewers_Only' + '${2/content/noteNumber/value}' + '/-/Comment',
                    'signatures': [self.super_id],
                    'readers': ['everyone'],
                    'writers': [support_group_id],
                    'invitees': ['everyone'],
                    'process': '''def process(client, edit, invitation):
    meta_invitation = client.get_invitation(invitation.invitations[0])
    script = meta_invitation.content['comment_process_script']['value']
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
                                'items': [
                                    { 'value': support_group_id, 'optional': True },
                                    { 'prefix': '~.*', 'optional': True}
                                ]
                            }
                        },
                        'readers': ['${2/note/readers}'],
                        'writers': [support_group_id],
                        'note': {
                            'id': {
                                'param': {
                                    'withInvitation': f'{support_group_id}/Venue_Configuration_Request' + '${6/content/noteNumber/value}' + '/-/Comment',
                                    'optional': True
                                }
                                },
                            'forum': '${4/content/noteId/value}',
                            'replyto': {
                                'param': {
                                    'withForum': '${6/content/noteId/value}'
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
                            'readers': [support_group_id, '${{3/note/forum}/content/program_chair_emails/value}'],
                            'writers': [support_group_id, '${3/signatures}'],
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

    def set_acs_and_reviewers_request(self):

        super_id = self.super_id
        support_group_id = self.support_group_id
        conference_venue_invitation_id = f'{support_group_id}/Venue_Request/-/ACs_and_Reviewers'

        invitation = Invitation(
            id = conference_venue_invitation_id,
            invitees = ['everyone'],
            readers = ['everyone'],
            writers = [],
            signatures = [super_id],
            preprocess = self.get_process_content('workflow_process/request_form_preprocess.py'),
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
                                    'range': [ 0, 9999999999999 ]
                                }
                            }
                        },
                        'program_chair_emails': {
                            'order': 7,
                            'description': 'A comma separated list of *lower-cased* email addresses for the program chairs of your venue, including the PC submitting this request.',
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
                                    'range': [ 0, 9999999999999 ]
                                }
                            }
                        },
                        'submission_deadline': {
                            'order': 10,
                            'description': 'By when do authors need to submit their manuscripts? Please specify the due date in GMT using the following format: YYYY/MM/DD HH:MM(e.g. 2019/01/31 23:59)',
                            'value': {
                                'param': {
                                    'type': 'date',
                                    'range': [ 0, 9999999999999 ]
                                }
                            }
                        },
                        'submission_license': {
                            'order': 11,
                            'description': 'Which license should be applied to each submission? We recommend "CC BY 4.0". If you select multiple licenses, you allow authors to choose their license upon submission. If your license is not listed, please contact us. Refer to https://openreview.net/legal/terms for more information.',
                            'value': {
                                'param': {
                                    'type': 'string[]',
                                    'input': 'select',
                                    'items':  [
                                        {'value': 'CC BY 4.0', 'optional': True, 'description': 'CC BY 4.0'},
                                        {'value': 'CC BY-SA 4.0', 'optional': True, 'description': 'CC BY-SA 4.0'},
                                        {'value': 'CC BY-NC 4.0', 'optional': True, 'description': 'CC BY-NC 4.0'},
                                        {'value': 'CC BY-ND 4.0', 'optional': True, 'description': 'CC BY-ND 4.0'},
                                        {'value': 'CC BY-NC-SA 4.0', 'optional': True, 'description': 'CC BY-NC-SA 4.0'},
                                        {'value': 'CC BY-NC-ND 4.0', 'optional': True, 'description': 'CC BY-NC-ND 4.0'},
                                        {'value': 'CC0 1.0', 'optional': True, 'description': 'CC0 1.0'}
                                    ]
                                }
                            }
                        },
                        'reviewers_name': {
                            'order': 12,
                            'description': 'Please provide the designated name to be used for reviewers. Default is "Reviewers".',
                            'value': {
                                'param': {
                                    'type': 'string',
                                    'regex': '.{0,500}',
                                    'default': 'Reviewers'
                                }
                            }
                        },
                        'area_chairs_name': {
                            'order': 13,
                            'description': 'Please provide the designated name to be used for area chairs. Default is "Area_Chairs".',
                            'value': {
                                'param': {
                                    'type': 'string',
                                    'regex': '.{0,500}',
                                    'default': 'Area_Chairs'
                                }
                            }
                        },
                        'other_important_information': {
                            'order': 14,
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
                        'venue_organizer_agreement': {
                            'order': 15,
                            'description': 'In order to use OpenReview, venue chairs must agree to the following:',
                            'value': {
                                'param': {
                                    'type': 'string[]',
                                    'items': [
                                        { 'value': 'OpenReview natively supports a wide variety of reviewing workflow configurations. However, if we want significant reviewing process customizations or experiments, we will detail these requests to the OpenReview staff at least three months in advance.', 'description': 'OpenReview natively supports a wide variety of reviewing workflow configurations. However, if we want significant reviewing process customizations or experiments, we will detail these requests to the OpenReview staff at least three months in advance.', 'optional': True},
                                        { 'value': 'We will ask authors and reviewers to create an OpenReview Profile at least two weeks in advance of the paper submission deadlines.', 'description': 'We will ask authors and reviewers to create an OpenReview Profile at least two weeks in advance of the paper submission deadlines.', 'optional': True},
                                        { 'value': 'When assembling our group of reviewers, we will only include email addresses or OpenReview Profile IDs of people we know to have authored publications relevant to our venue.  (We will not solicit new reviewers using an open web form, because unfortunately some malicious actors sometimes try to create "fake ids" aiming to be assigned to review their own paper submissions.)', 'description': 'When assembling our group of reviewers, we will only include email addresses or OpenReview Profile IDs of people we know to have authored publications relevant to our venue.  (We will not solicit new reviewers using an open web form, because unfortunately some malicious actors sometimes try to create "fake ids" aiming to be assigned to review their own paper submissions.)', 'optional': True},
                                        { 'value': 'We acknowledge that, if our venue\'s reviewing workflow is non-standard, or if our venue is expecting more than a few hundred submissions for any one deadline, we should designate our own Workflow Chair, who will read the OpenReview documentation and manage our workflow configurations throughout the reviewing process.', 'description': 'We acknowledge that, if our venue’s reviewing workflow is non-standard, or if our venue is expecting more than a few hundred submissions for any one deadline, we should designate our own Workflow Chair, who will read the OpenReview documentation and manage our workflow configurations throughout the reviewing process.', 'optional': True},
                                        { 'value': 'We acknowledge that OpenReview staff work Monday-Friday during standard business hours US Eastern time, and we cannot expect support responses outside those times.  For this reason, we recommend setting submission and reviewing deadlines Monday through Thursday.', 'description': 'We acknowledge that OpenReview staff work Monday-Friday during standard business hours US Eastern time, and we cannot expect support responses outside those times.  For this reason, we recommend setting submission and reviewing deadlines Monday through Thursday.', 'optional': True},
                                        { 'value': 'We will treat the OpenReview staff with kindness and consideration.', 'description': 'We will treat the OpenReview staff with kindness and consideration.', 'optional': True},
                                        { 'value': 'We acknowledge that authors and reviewers will be required to share their preferred email.', 'description': 'We acknowledge that authors and reviewers will be required to share their preferred email.', 'optional': True},
                                        { 'value': 'We acknowledge that review counts will be collected for all the reviewers and publicly available in OpenReview.', 'description': 'We acknowledge that review counts will be collected for all the reviewers and publicly available in OpenReview.', 'optional': True},
                                        { 'value': 'We acknowledge that metadata for accepted papers will be publicly released in OpenReview.', 'description': 'We acknowledge that metadata for accepted papers will be publicly released in OpenReview.', 'optional': True}
                                    ],
                                    'input': 'checkbox'
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
            process=self.get_process_content('workflow_process/support_process.py')
        )

        self.post_invitation_edit(invitation)

    def set_acs_and_reviewers_deployment(self):

        support_group_id = self.support_group_id
        deploy_invitation_id = f'{support_group_id}/Venue_Request/ACs_and_Reviewers/-/Deployment'

        invitation = Invitation(
            id = deploy_invitation_id,
            invitees = [support_group_id],
            readers = ['everyone'],
            writers = [support_group_id],
            signatures = [self.super_id],
            edit = {
                'signatures': {
                    'param': {
                        'items': [ { 'value': support_group_id, 'optional': True } ]
                    }
                },
                'readers': ['${2/note/content/venue_id/value}'],
                'writers': [support_group_id],
                'note': {
                    'id': {
                        'param': {
                            'withInvitation': f'{support_group_id}/Venue_Request/-/ACs_and_Reviewers',
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
            },
            process=self.get_process_content('workflow_process/deploy_acs_reviewers_process.py')
        )

        self.post_invitation_edit(invitation)

    def set_acs_and_reviewers_comment(self):

        support_group_id = self.support_group_id
        comment_invitation_id = f'{support_group_id}/Venue_Request/ACs_and_Reviewers/-/Comment'

        invitation = Invitation(id=comment_invitation_id,
            invitees=[support_group_id],
            readers=['everyone'],
            writers=[support_group_id],
            signatures=[support_group_id],
            content={
                'comment_process_script': {
                    'value': self.get_process_content('workflow_process/venue_comment_process.py')
                }
            },
            edit = {
                'signatures': [support_group_id],
                'readers': [support_group_id],
                'writers': [support_group_id],
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
                    'id': f'{support_group_id}/Venue_Request/ACs_and_Reviewers' + '${2/content/noteNumber/value}' + '/-/Comment',
                    'signatures': [self.super_id],
                    'readers': ['everyone'],
                    'writers': [support_group_id],
                    'invitees': ['everyone'],
                    'process': '''def process(client, edit, invitation):
    meta_invitation = client.get_invitation(invitation.invitations[0])
    script = meta_invitation.content['comment_process_script']['value']
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
                                'items': [
                                    { 'value': support_group_id, 'optional': True },
                                    { 'prefix': '~.*', 'optional': True}
                                ]
                            }
                        },
                        'readers': ['${2/note/readers}'],
                        'writers': [support_group_id],
                        'note': {
                            'id': {
                                'param': {
                                    'withInvitation': f'{support_group_id}/Venue_Configuration_Request' + '${6/content/noteNumber/value}' + '/-/Comment',
                                    'optional': True
                                }
                            },
                            'forum': '${4/content/noteId/value}',
                            'replyto': {
                                'param': {
                                    'withForum': '${6/content/noteId/value}'
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
                            'readers': [support_group_id, '${{3/note/forum}/content/program_chair_emails/value}'],
                            'writers': [support_group_id, '${3/signatures}'],
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