from ... import openreview
from ... import tools
import os

class JournalRequest():

    def __init__(self, client, support_group_id):
        self.support_group_id = support_group_id
        self.support_group = tools.get_group(client, self.support_group_id)
        self.client = client

    def setup_journal_request(self):

        journal_request_content = {
            'title': {
                'description': 'Used for display purposes. This is copied from the Official Venue Name',
                'order': 1,
                'value': {
                    'value': '${note.content.official_venue_name.value}'
                }
            },
            'official_venue_name': {
                'description': 'This will appear in your journal\'s OpenReview homepage.',
                'order': 2,
                'value' : {
                    'value-regex': '.*'
                }
            },
            'abbreviated_venue_name': {
                'description': 'This will be used to identify your journal in OpenReview and in email subject lines',
                'order': 3,
                'value' : {
                    'value-regex': '.*'
                }
            },
            'venue_id': {
                'description': 'Journal venue id should start with a period.',
                'order': 4,
                'value' : {
                    'value-regex': '[.].+'
                }
            },
            'contact_info': {
                'description': 'Single point of contact email address, which will be displayed on the journal homepage',
                'order': 5,
                'value' : {
                    'value-regex': r'([a-z0-9_\-\.]{2,}@[a-z0-9_\-\.]{2,}\.[a-z]{2,},){0,}([a-z0-9_\-\.]{2,}@[a-z0-9_\-\.]{2,}\.[a-z]{2,})'
                }
            },
            'secret_key': {
                'order': 6,
                'value': {
                    'value-regex': '.*'
                }
            },
            'support_role': {
                'order': 7,
                'value': {
                    'value-regex': r'~.*|([a-z0-9_\-\.]{2,}@[a-z0-9_\-\.]{2,}\.[a-z]{2,},){0,}([a-z0-9_\-\.]{2,}@[a-z0-9_\-\.]{2,}\.[a-z]{2,})'
                }
            },
            'editors': {
                'order': 8,
                'value': {
                    'values-regex': r'~.*|([a-z0-9_\-\.]{1,}@[a-z0-9_\-\.]{2,}\.[a-z]{2,},){0,}([a-z0-9_\-\.]{1,}@[a-z0-9_\-\.]{2,}\.[a-z]{2,})',
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
                    'signatures': { 'values-regex': f'~.*|{self.support_group_id}' },
                    'writers': { 'values': ['${note.content.venue_id.value}'] },
                    'readers': { 'values': ['${note.content.venue_id.value}'] },
                    'note': {
                        'signatures': { 'values': ['${signatures}'] },
                        'readers': { 'values': [self.support_group_id, '${note.content.venue_id.value}','${note.content.venue_id.value}/Action_Editors' ] },
                        'writers': {'values': [self.support_group_id, '${note.content.venue_id.value}'] },
                        'content': journal_request_content
                    }
                },
                process_string = content
            )


            self.client.post_invitation_edit(
                readers = ['~Super_User1'],
                writers = ['~Super_User1'],
                signatures = ['~Super_User1'],
                invitation = invitation
            )
    def setup_journal_group(self, note_id):
        
        note = self.client.get_note(note_id)
        journal_request_group = self.client.post_group(openreview.Group(
            id = f'{self.support_group_id}/Journal_Request' + str(note.number),
            readers = ['everyone'],
            writers = [self.support_group_id],
            signatures = [self.support_group_id],
            signatories = [self.support_group_id.split('/')[0]],
            members = []
        ))

    def setup_comment_invitation(self, note_id, action_editors_id=None):

        note = self.client.get_note(note_id)
        venue_id = note.content['venue_id']['value']

        with open(os.path.join(os.path.dirname(__file__), 'process/comment_process.py')) as f:
            content = f.read()
            content = content.replace("SUPPORT_GROUP = ''", "SUPPORT_GROUP = '" + self.support_group_id + "'")
            invitation = openreview.api.Invitation(
                id = f'{self.support_group_id}/Journal_Request' + str(note.number) + '/-/Comment',
                invitees = ['everyone'],
                readers = ['everyone'],
                writers = [],
                signatures = ['~Super_User1'],
                edit = {
                    'signatures': { 'values-regex': f'~.*|{self.support_group_id}' },
                    'writers': { 'values': [self.support_group_id, venue_id] },
                    'readers': { 'values': [self.support_group_id, venue_id] },
                    'note': {
                        'signatures': { 'values': ['${signatures}'] },
                        'readers': { 'values-dropdown': [self.support_group_id, venue_id, action_editors_id] },
                        'writers': { 'values': [self.support_group_id, venue_id]},
                        'forum': { 'value': note.id },
                        'content': {
                            'title': {
                                'description': 'Brief summary of your comment.',
                                'order': 1,
                                'value': {
                                    'value-regex': '.{1,500}'
                                }
                            },
                            'comment': {
                                'description': 'Your comment or reply (max 200000 characters).',
                                'order': 2,
                                'value' : {
                                    'value-regex': '[\\S\\s]{1,200000}'
                                }
                            }
                        }
                    }
                },
                process_string = content
            )

            self.client.post_invitation_edit(
                        readers = ['~Super_User1'],
                        writers = ['~Super_User1'],
                        signatures = ['~Super_User1'],
                        invitation = invitation
                    )

    def setup_recruitment_invitation(self, note_id):

        note = self.client.get_note(note_id)
        short_name = note.content['abbreviated_venue_name']['value']
        venue_id = note.content['venue_id']['value']
        recruitment_email_template = '''Dear {name},

You have been nominated by the program chair committee of {short_name} to serve as {invitee_role}.

ACCEPT LINK:
{accept_url}

DECLINE LINK:
{decline_url}

Cheers!'''.replace('{short_name}', short_name)

        recruitment_content = {
            'title': {
                'order': 1,
                'value': {
                    'value': 'Recruitment'
                }
            },
            'invitee_role': {
                'description': 'Please select the role of the invitees in the journal,',
                'order': 2,
                'value' : {
                    'value-radio': ['action editor', 'reviewer']
                }
            },
            'invitee_details': {
                'description': 'Enter a list of invitees with one per line. Either tilde IDs or email,name pairs expected. E.g. captain_rogers@marvel.com, Captain America or ∼Captain_America1',
                'order': 3,
                'value' : {
                    'value-regex': '[\\S\\s]{1,50000}'
                }
            },
            'email_subject': {
                'description': 'Please carefully review the email subject for the recruitment emails. Make sure not to remove the parenthesized tokens.',
                'order': 4,
                'value' : {
                    'value-regex': '.*'
                },
                'presentation': {
                    'default': '[{short_name}] Invitation to serve as {invitee_role}'.replace('{short_name}', short_name)
                }
            },
            'email_content': {
                'description': 'Please carefully review the template below before you click submit to send out recruitment emails. Make sure not to remove the parenthesized tokens.',
                'order': 5,
                'value' : {
                    'value-regex': '[\\S\\s]{1,10000}'
                },
                'presentation': {
                    'default': recruitment_email_template
                }
            }
        }

        with open(os.path.join(os.path.dirname(__file__), 'process/recruitment_process.py')) as f:
            content = f.read()
            content = content.replace("SUPPORT_GROUP = ''", "SUPPORT_GROUP = '" + self.support_group_id + "'")
            invitation = openreview.api.Invitation(
                id = f'{self.support_group_id}/Journal_Request' + str(note.number) + '/-/Recruitment',
                invitees = [venue_id],
                readers = ['everyone'],
                writers = [],
                signatures = ['~Super_User1'],
                edit = {
                    'signatures': { 'values-regex': f'~.*|{self.support_group_id}' },
                    'writers': { 'values': [self.support_group_id, venue_id] },
                    'readers': { 'values': [self.support_group_id, venue_id] },
                    'note': {
                        'forum': { 'value': note.id },
                        'replyto': {'value': note.id },
                        'signatures': { 'values': ['${signatures}'] },
                        'readers': { 'values': [self.support_group_id, venue_id] },
                        'writers': { 'values': [self.support_group_id, venue_id]},
                        'content': recruitment_content
                    }
                },
                process_string = content
            )

            self.client.post_invitation_edit(
                readers = ['~Super_User1'],
                writers = ['~Super_User1'],
                signatures = ['~Super_User1'],
                invitation = invitation
            )

    def setup_recruitment_by_action_editors(self, note_id):

        note = self.client.get_note(note_id)
        short_name = note.content['abbreviated_venue_name']['value']
        venue_id = note.content['venue_id']['value']
        recruitment_email_template = '''Dear {name},

You have been nominated to serve as a reviewer for {short_name}.

ACCEPT LINK:
{accept_url}

DECLINE LINK:
{decline_url}

Cheers!
{inviter}'''.replace('{short_name}', short_name)

        recruitment_content = {
            'invitee_details': {
                'description': 'Enter a tilde ID or email,name pair. E.g. captain_rogers@marvel.com, Captain America or ∼Captain_America1',
                'order': 2,
                'value' : {
                    'value-regex': '.{1,100}'
                }
            },
            'email_subject': {
                'description': 'Please carefully review the email subject for the recruitment email. Make sure not to remove the parenthesized tokens.',
                'order': 4,
                'value' : {
                    'value-regex': '.*'
                },
                'presentation': {
                    'default': '[{short_name}] Invitation to serve as reviewer'
                }
            },
            'email_content': {
                'description': 'Please carefully review the template below before you click submit to send out the recruitment email. Make sure not to remove the parenthesized tokens.',
                'order': 5,
                'value' : {
                    'value-regex': '[\\S\\s]{1,10000}'
                },
                'presentation': {
                    'default': recruitment_email_template
                }
            }
        }

        with open(os.path.join(os.path.dirname(__file__), 'process/ae_recruitment_process.py')) as f:
            content = f.read()
            content = content.replace("SUPPORT_GROUP = ''", "SUPPORT_GROUP = '" + self.support_group_id + "'")
            invitation = openreview.api.Invitation(
                id = f'{self.support_group_id}/Journal_Request' + str(note.number) + '/-/Reviewer_Recruitment',
                invitees = [venue_id, f'{venue_id}/Action_Editors'],
                readers = ['everyone'],
                writers = [],
                signatures = ['~Super_User1'],
                edit = {
                    'signatures': { 'values-regex': f'~.*|{self.support_group_id}' },
                    'writers': { 'values': [self.support_group_id, venue_id] },
                    'readers': { 'values': [self.support_group_id, venue_id] },
                    'note': {
                        'forum': { 'value': note.id },
                        'replyto': {'value': note.id },
                        'signatures': { 'values': ['${signatures}'] },
                        'readers': { 'values': [self.support_group_id, venue_id, f'{venue_id}/Action_Editors'] },
                        'writers': { 'values': [self.support_group_id, venue_id]},
                        'content': recruitment_content
                    }
                },
                process_string = content
            )

            self.client.post_invitation_edit(
                readers = ['~Super_User1'],
                writers = ['~Super_User1'],
                signatures = ['~Super_User1'],
                invitation = invitation
            )