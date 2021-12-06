from ... import openreview
from ... import tools
import os

class JournalRequest():

    def __init__(self, client, support_group_id, super_user):
        self.support_group_id = support_group_id
        self.support_group = tools.get_group(client, self.support_group_id)
        self.client = client
        self.super_user = super_user

        self.deploy_process = os.path.join(os.path.dirname(__file__), 'process/deploy_process.py')

        self.setup_journal_request()

    def setup_journal_request(self):

        self.journal_request_content = {
            'title': {
                'description': 'Used for display purposes. This is copied from the Official Venue Name',
                'order': 1,
                'value': {
                    'value': '${note.content.official_venue_name.value}'
                }
            },
            'official_venue_name': {
                'order': 2,
                'value' : {
                    'value-regex': '.*'
                }
            },
            'abbreviated_venue_name': {
                'order': 3,
                'value' : {
                    'value-regex': '.*'
                }
            },
            'venue_id': {
                'order': 4,
                'value' : {
                    'value-regex': '.*'
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
                    'value-regex': r'([a-z0-9_\-\.]{2,}@[a-z0-9_\-\.]{2,}\.[a-z]{2,},){0,}([a-z0-9_\-\.]{2,}@[a-z0-9_\-\.]{2,}\.[a-z]{2,})'
                }
            },
            'editors': {
                'order': 8,
                'value': {
                    'values-regex': r'~.*|([a-z0-9_\-\.]{1,}@[a-z0-9_\-\.]{2,}\.[a-z]{2,},){0,}([a-z0-9_\-\.]{1,}@[a-z0-9_\-\.]{2,}\.[a-z]{2,})',
                }
            }
        }

        invitation = openreview.api.Invitation(
            id = f'{self.support_group_id}/-/Journal_Form',
            invitees = ['everyone'],
            readers = ['everyone'],
            writers = [],
            signatures = [self.super_user],
            edit = {
                'signatures': { 'values-regex': '.*' },
                'writers': { 'values': ['${note.content.venue_id.value}'] },
                'readers': { 'values': ['${note.content.venue_id.value}'] },
                'note': {
                    'signatures': { 'values-regex': f'.*|{self.support_group_id}' },
                    'readers': { 'values': [self.support_group_id, '${note.content.venue_id.value}'] },
                    'writers': {'values': [self.support_group_id, '${note.content.venue_id.value}'] },
                    'content': self.journal_request_content
                }
            },
            process = os.path.join(os.path.dirname(__file__), 'process/deploy_process.py')
        )

        self.client.post_invitation_edit(
            readers = [self.super_user],
            writers = [self.super_user],
            signatures = [self.super_user],
            invitation = invitation
        )