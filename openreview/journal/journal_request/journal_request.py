from ... import openreview
from ... import tools
import os

class JournalRequest():


    @classmethod
    def get_journal(JournalRequest, client, journal_request_id, setup=False):
        journal_request = client.get_note(journal_request_id)
        venue_id = journal_request.content['venue_id']['value']
        secret_key = journal_request.content['secret_key']['value']
        contact_info = journal_request.content['contact_info']['value']
        full_name = journal_request.content['official_venue_name']['value']
        short_name = journal_request.content['abbreviated_venue_name']['value']
        website = journal_request.content['website']['value']
        support_role = journal_request.content['support_role']['value']
        editors = journal_request.content['editors']['value']
        assignment_delay = journal_request.content.get('settings', {}).get('value', {}).get('assignment_delay', 5)
        settings = journal_request.content.get('settings', {}).get('value', {})
        submission_name = journal_request.content.get('settings', {}).get('value', {}).get('submission_name')

        journal = openreview.journal.Journal(client, venue_id, secret_key, contact_info, full_name, short_name, website, submission_name, settings)
        journal.request_form_id = journal_request_id

        if setup:
            journal.setup(support_role, editors=editors, assignment_delay=assignment_delay)

        return journal


    def __init__(self, client, support_group_id):
        self.support_group_id = support_group_id
        self.support_group = tools.get_group(client, self.support_group_id)
        self.client = client
        self.meta_invitation_id = f'{support_group_id}/-/Journal_Request_Edit'

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
            invitation=openreview.api.Invitation(id=self.meta_invitation_id,
                invitees=['~Super_User1'],
                readers=['~Super_User1'],
                signatures=['~Super_User1'],
                edit=True
            )
        )

    def setup_journal_request(self):

        self.set_meta_invitation()

        journal_request_content = {
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
                'description': 'This will appear in your journal\'s OpenReview homepage.',
                'order': 2,
                'value' : {
                    'param': {
                        'type': 'string'
                    }
                }
            },
            'abbreviated_venue_name': {
                'description': 'This will be used to identify your journal in OpenReview and in email subject lines',
                'order': 3,
                'value' : {
                    'param': {
                        'type': 'string'
                    }
                }
            },
            'venue_id': {
                'description': 'Journal venue id',
                'order': 4,
                'value' : {
                    'param': {
                        'type': 'string'
                    }
                }
            },
            'contact_info': {
                'description': 'Single point of contact email address, which will be displayed on the journal homepage',
                'order': 5,
                'value' : {
                    'param': {
                        'type': 'string',
                        'regex': r'([a-z0-9_\-\.]{2,}@[a-z0-9_\-\.]{2,}\.[a-z]{2,},){0,}([a-z0-9_\-\.]{2,}@[a-z0-9_\-\.]{2,}\.[a-z]{2,})'
                    }
                }
            },
            'secret_key': {
                'order': 6,
                'value': {
                    'param': {
                        'type': 'string'
                    }
                }
            },
            'support_role': {
                'order': 7,
                'value': {
                    'param': {
                        'type': 'string',
                        'regex': r'~.*|([a-z0-9_\-\.]{2,}@[a-z0-9_\-\.]{2,}\.[a-z]{2,},){0,}([a-z0-9_\-\.]{2,}@[a-z0-9_\-\.]{2,}\.[a-z]{2,})'
                    }
                }
            },
            'editors': {
                'order': 8,
                'value': {
                    'param': {
                        'type': 'string[]',
                        'regex': r'~.*|([a-z0-9_\-\.]{1,}@[a-z0-9_\-\.]{2,}\.[a-z]{2,},){0,}([a-z0-9_\-\.]{1,}@[a-z0-9_\-\.]{2,}\.[a-z]{2,})',
                    }
                }
            },
            'website': {
                'order': 9,
                'value': {
                    'param': {
                        'type': 'string'
                    }
                }
            },
            'settings': {
                'order': 10,
                'value': {
                    'param': {
                        'type': 'json',
                        'optional': True
                    }
                }
            }
        }

        with open(os.path.join(os.path.dirname(__file__), 'process/deploy_process.py')) as f:
            content = f.read()
            content = content.replace("SUPPORT_GROUP = ''", "SUPPORT_GROUP = '" + self.support_group_id + "'")
            invitation = openreview.api.Invitation(
                id = f'{self.support_group_id}/-/Journal_Request',
                invitees = ['everyone'],
                readers = ['everyone'],
                writers = [],
                signatures = ['~Super_User1'],
                edit = {
                    'signatures': { 'param': { 'regex': f'~.*|{self.support_group_id}' }},
                    'writers': ['${2/note/content/venue_id/value}'],
                    'readers': ['${2/note/content/venue_id/value}'],
                    'note': {
                        'signatures': ['${3/signatures}'],
                        'readers': [self.support_group_id, '${2/content/venue_id/value}','${2/content/venue_id/value}/Action_Editors' ],
                        'writers': [self.support_group_id, '${2/content/venue_id/value}'],
                        'content': journal_request_content,
                        'id' : {
                            'param': {
                                'withInvitation': f'{self.support_group_id}/-/Journal_Request',
                                'optional': True
                            }
                        }
                    }
                },
                process = content
            )


            self.post_invitation_edit(invitation = invitation)

    def setup_journal_group(self, note_id):

        note = self.client.get_note(note_id)
        self.client.post_group_edit(
            invitation = self.meta_invitation_id,
            readers = [self.support_group_id],
            writers = [self.support_group_id],
            signatures = [self.support_group_id.split('/')[0]],
            group = openreview.api.Group(
                id = f'{self.support_group_id}/Journal_Request{note.number}',
                readers = [self.support_group_id],
                writers = [self.support_group_id],
                signatures = [self.support_group_id.split('/')[0]],                
            )
        )

    def setup_comment_invitation(self, note_id, action_editors_id=None):

        note = self.client.get_note(note_id)
        venue_id = note.content['venue_id']['value']
        request_comment_invitation_id =  f'{self.support_group_id}/Journal_Request' + str(note.number) + '/-/Comment'

        with open(os.path.join(os.path.dirname(__file__), 'process/comment_process.py')) as f:
            content = f.read()
            content = content.replace("SUPPORT_GROUP = ''", "SUPPORT_GROUP = '" + self.support_group_id + "'")
            content = content.replace("VENUE_ID = ''", "VENUE_ID = '" + venue_id + "'")
            invitation = openreview.api.Invitation(
                id = request_comment_invitation_id,
                invitees = [venue_id, self.support_group_id],
                readers = ['everyone'],
                writers = [],
                signatures = [venue_id],
                edit = {
                    'signatures': { 'param': { 'regex': f'~.*|{venue_id}|{self.support_group_id}' }},
                    'writers': [self.support_group_id, venue_id],
                    'readers': [self.support_group_id, venue_id],
                    'note': {
                        'id': {
                            'param': {
                                'withInvitation': request_comment_invitation_id,
                                'optional': True
                            }
                        },
                        'signatures': ['${3/signatures}'],
                        'readers': { 'param': { 'enum': [self.support_group_id, venue_id, '~.*'] }},
                        'writers': [self.support_group_id, venue_id],
                        'forum': note.id,
                        'replyto': { 'param': { 'withForum': note.id }},
                        'content': {
                            'title': {
                                'description': 'Brief summary of your comment.',
                                'order': 1,
                                'value': {
                                    'param': {
                                        'type': 'string',
                                        'regex': '.{1,500}'
                                    }
                                }
                            },
                            'comment': {
                                'description': 'Your comment or reply (max 200000 characters).',
                                'order': 2,
                                'value' : {
                                    'param': {
                                        'type': 'string',
                                        'maxLength': 200000,
                                        'input': 'textarea',
                                        'markdown': True
                                    }
                                }
                            }
                        }
                    }
                },
                process = content
            )

            self.post_invitation_edit(invitation = invitation)

    def setup_recruitment_invitations(self, note_id, ae_template=None, reviewer_template=None):

        note = self.client.get_note(note_id)
        short_name = note.content['abbreviated_venue_name']['value']
        venue_id = note.content['venue_id']['value']

        default_recruitment_template = '''Dear {{fullname}},

You have been nominated by the program chair committee of {short_name} to serve as {{role}}.

ACCEPT LINK:
{{accept_url}}

DECLINE LINK:
{{decline_url}}

Cheers!'''.replace('{short_name}', short_name)

        recruitment_content = {
            'title': {
                'order': 1,
                'value': 'Recruitment'
            },
            'invitee_details': {
                'description': 'Enter a list of invitees with one per line. Either tilde IDs (∼Captain_America1), emails (captain_rogers@marvel.com), or email,name pairs (captain_rogers@marvel.com, Captain America) expected. If only an email address is provided for an invitee, the recruitment email is addressed to "Dear invitee". Do not use parentheses in your list of invitees.',
                'order': 3,
                'value' : {
                    'param': {
                        'type': 'string',
                        'maxLength': 50000,
                        'input': 'textarea'
                    }
                }
            },
            'email_subject': {
                'description': 'Please carefully review the email subject for the recruitment emails. Make sure not to remove the parenthesized tokens.',
                'order': 4,
                'value' : {
                    'param': {
                        'type': 'string',
                        'default': '[{short_name}] Invitation to serve as {{role}} for {short_name}'.replace('{short_name}', short_name)
                    }
                }
            },
            'email_content': {
                'description': 'Please carefully review the template below before you click submit to send out recruitment emails. Make sure not to remove the parenthesized tokens.',
                'order': 5,
                'value' : {
                    'param': {
                        'type': 'string',
                        'maxLength': 100000,
                        'input': 'textarea',
                        'default': default_recruitment_template,
                        'markdown': True
                    }
                }
            }
        }

        #setup ae recruitment
        if ae_template:
            recruitment_content['email_content']['value']['param']['default'] = ae_template

        invitation_id = f'{self.support_group_id}/Journal_Request' + str(note.number) + '/-/Action_Editor_Recruitment'
        existing_invitation = openreview.tools.get_invitation(self.client, invitation_id)

        if not existing_invitation or (ae_template and ae_template != existing_invitation.edit['note']['content']['email_content']['value']['param']['default']):
            with open(os.path.join(os.path.dirname(__file__), 'process/recruitment_process.py')) as f:
                content = f.read()
                content = content.replace("SUPPORT_GROUP = ''", "SUPPORT_GROUP = '" + self.support_group_id + "'")
                invitation = openreview.api.Invitation(
                    id = invitation_id,
                    invitees = [venue_id],
                    readers = ['everyone'],
                    writers = [],
                    signatures = ['~Super_User1'],
                    edit = {
                        'signatures': { 'param': { 'regex': f'~.*|{self.support_group_id}'}},
                        'writers': [self.support_group_id, venue_id],
                        'readers': [self.support_group_id, venue_id],
                        'note': {
                            'forum': note.id,
                            'replyto': note.id,
                            'signatures': ['${3/signatures}'],
                            'readers': [self.support_group_id, venue_id],
                            'writers': [self.support_group_id, venue_id],
                            'content': recruitment_content
                        }
                    },
                    process = content
                )

                self.post_invitation_edit(invitation = invitation)

        #setup rev recruitment
        if reviewer_template:
            recruitment_content['email_content']['value']['param']['default'] = reviewer_template

        invitation_id = f'{self.support_group_id}/Journal_Request' + str(note.number) + '/-/Reviewer_Recruitment'
        existing_invitation = openreview.tools.get_invitation(self.client, invitation_id)

        if not existing_invitation or (reviewer_template and reviewer_template != existing_invitation.edit['note']['content']['email_content']['value']['param']['default']):
            with open(os.path.join(os.path.dirname(__file__), 'process/recruitment_process.py')) as f:
                content = f.read()
                content = content.replace("SUPPORT_GROUP = ''", "SUPPORT_GROUP = '" + self.support_group_id + "'")
                invitation = openreview.api.Invitation(
                    id = invitation_id,
                    invitees = [venue_id],
                    readers = ['everyone'],
                    writers = [],
                    signatures = ['~Super_User1'],
                    edit = {
                        'signatures': { 'param': { 'regex': f'~.*|{self.support_group_id}' }},
                        'writers': [self.support_group_id, venue_id],
                        'readers': [self.support_group_id, venue_id],
                        'note': {
                            'forum': note.id,
                            'replyto': note.id,
                            'signatures': ['${3/signatures}'],
                            'readers': [self.support_group_id, venue_id],
                            'writers': [self.support_group_id, venue_id],
                            'content': recruitment_content
                        }
                    },
                    process = content
                )

                self.post_invitation_edit(invitation = invitation)

    def setup_recruitment_by_action_editors(self, note_id, template=None):

        note = self.client.get_note(note_id)
        short_name = note.content['abbreviated_venue_name']['value']
        venue_id = note.content['venue_id']['value']
        recruitment_email_template = '''Dear {{fullname}},

You have been nominated to serve as a reviewer for {short_name} by {{inviter}}.

ACCEPT LINK:
{{accept_url}}

DECLINE LINK:
{{decline_url}}

Cheers!
{{inviter}}'''.replace('{short_name}', short_name)

        if template:
            recruitment_email_template = template

        recruitment_content = {
            'invitee_name': {
                'description': 'Enter the name of the user you would like to invite.',
                'order': 2,
                'value' : {
                    'param': {
                        'type': 'string',
                        'regex': '^[^,\n]+$'
                    }
                }
            },
            'invitee_email': {
                'description': 'Enter the email or OpenReview profile ID of the user you would like to invite.',
                'order': 2,
                'value' : {
                    'param': {
                        'type': 'string',
                        'regex': '^[^,\n]+$'
                    }
                }
            },
            'email_subject': {
                'description': 'Please carefully review the email subject for the recruitment email. Make sure not to remove the parenthesized tokens.',
                'order': 4,
                'value' : {
                    'param': {
                        'type': 'string',
                        'default': f'[{short_name}] Invitation to act as Reviewer for {short_name}'
                    }
                }
            },
            'email_content': {
                'description': 'Please carefully review the template below before you click submit to send out the recruitment email. Make sure not to remove the parenthesized tokens.',
                'order': 5,
                'value' : {
                    'param': {
                        'type': 'string',
                        'maxLength': 10000,
                        'input': 'textarea',
                        'default': recruitment_email_template
                    }
                }
            }
        }

        invitation_id = f'{self.support_group_id}/Journal_Request' + str(note.number) + '/-/Reviewer_Recruitment_by_AE'
        existing_invitation = openreview.tools.get_invitation(self.client, invitation_id)

        if not existing_invitation or (template and template != existing_invitation.edit['note']['content']['email_content']['value']['param']['default']):

            with open(os.path.join(os.path.dirname(__file__), 'process/ae_recruitment_process.py')) as f:
                content = f.read()
                content = content.replace("SUPPORT_GROUP = ''", "SUPPORT_GROUP = '" + self.support_group_id + "'")
                invitation = openreview.api.Invitation(
                    id = invitation_id,
                    invitees = [f'{venue_id}/Action_Editors'],
                    readers = ['everyone'],
                    writers = [],
                    signatures = ['~Super_User1'],
                    edit = {
                        'signatures': { 'param': { 'regex': f'~.*|{self.support_group_id}'}},
                        'writers': [self.support_group_id, venue_id],
                        'readers': [self.support_group_id, venue_id],
                        'note': {
                            'forum': note.id,
                            'replyto': note.id,
                            'signatures': ['${3/signatures}'],
                            'readers': [self.support_group_id, venue_id, '${3/signatures}'],
                            'writers': [self.support_group_id, venue_id],
                            'content': recruitment_content
                        }
                    },
                    process = content
                )

                self.post_invitation_edit(invitation = invitation)