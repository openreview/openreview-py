import os
import json
import datetime
import openreview
from tqdm import tqdm
from .. import tools

class InvitationBuilder(object):

    def __init__(self, client):
        self.client = client

    def set_ae_recruitment_invitation(self, journal, hash_seed, header):

        venue_id=journal.venue_id
        action_editors_id = journal.get_action_editors_id()
        action_editors_declined_id = action_editors_id + '/Declined'
        action_editors_invited_id = action_editors_id + '/Invited'

        with open(os.path.join(os.path.dirname(__file__), 'process/recruit_ae_process.py')) as process_reader:
            process_content = process_reader.read()
            process_content = process_content.replace("SHORT_PHRASE = ''", f"SHORT_PHRASE = '{venue_id}'")
            process_content = process_content.replace("ACTION_EDITOR_NAME = ''", f"ACTION_EDITOR_NAME = 'Action Editor'")
            process_content = process_content.replace("ACTION_EDITOR_INVITED_ID = ''", f"ACTION_EDITOR_INVITED_ID = '{action_editors_invited_id}'")
            process_content = process_content.replace("ACTION_EDITOR_ACCEPTED_ID = ''", f"ACTION_EDITOR_ACCEPTED_ID = '{action_editors_id}'")
            process_content = process_content.replace("ACTION_EDITOR_DECLINED_ID = ''", f"ACTION_EDITOR_DECLINED_ID = '{action_editors_declined_id}'")
            process_content = process_content.replace("HASH_SEED = ''", f"HASH_SEED = '{hash_seed}'")

            with open(os.path.join(os.path.dirname(__file__), 'webfield/recruitResponseWebfield.js')) as webfield_reader:
                webfield_content = webfield_reader.read()
                webfield_content = webfield_content.replace("var VENUE_ID = '';", "var VENUE_ID = '" + venue_id + "';")
                webfield_content = webfield_content.replace("var HEADER = {};", "var HEADER = " + json.dumps(header) + ";")

                invitation=self.client.post_invitation(openreview.Invitation(id=f'{action_editors_id}/-/Recruitment',
                    invitees = ['everyone'],
                    readers = ['everyone'],
                    writers = [venue_id],
                    signatures = [venue_id],
                    reply = {
                        'signatures': { 'values-regex': '\\(anonymous\\)' },
                        'readers': { 'values': [venue_id] },
                        'writers': { 'values': []},
                        'content': {
                            'title': {
                                'order': 1,
                                'value': 'Recruit response'
                            },
                            'user': {
                                'description': 'email address',
                                'order': 2,
                                'value-regex': '.*',
                                'required':True
                            },
                            'key': {
                                'description': 'Email key hash',
                                'order': 3,
                                'value-regex': '.{0,100}',
                                'required':True
                            },
                            'response': {
                                'description': 'Invitation response',
                                'order': 4,
                                'value-radio': ['Yes', 'No'],
                                'required':True
                            }
                        }
                    },
                    process_string=process_content,
                    web_string=webfield_content
                ))
                return invitation

    def set_reviewer_recruitment_invitation(self, journal, hash_seed, header):

        venue_id=journal.venue_id
        reviewers_id = journal.get_reviewers_id()
        reviewers_declined_id = reviewers_id + '/Declined'
        reviewers_invited_id = reviewers_id + '/Invited'

        with open(os.path.join(os.path.dirname(__file__), 'process/recruit_ae_process.py')) as process_reader:
            process_content = process_reader.read()
            process_content = process_content.replace("SHORT_PHRASE = ''", f"SHORT_PHRASE = '{venue_id}'")
            process_content = process_content.replace("ACTION_EDITOR_NAME = ''", f"ACTION_EDITOR_NAME = 'Action Editor'")
            process_content = process_content.replace("ACTION_EDITOR_INVITED_ID = ''", f"ACTION_EDITOR_INVITED_ID = '{reviewers_invited_id}'")
            process_content = process_content.replace("ACTION_EDITOR_ACCEPTED_ID = ''", f"ACTION_EDITOR_ACCEPTED_ID = '{reviewers_id}'")
            process_content = process_content.replace("ACTION_EDITOR_DECLINED_ID = ''", f"ACTION_EDITOR_DECLINED_ID = '{reviewers_declined_id}'")
            process_content = process_content.replace("HASH_SEED = ''", f"HASH_SEED = '{hash_seed}'")

            with open(os.path.join(os.path.dirname(__file__), 'webfield/recruitResponseWebfield.js')) as webfield_reader:
                webfield_content = webfield_reader.read()
                webfield_content = webfield_content.replace("var VENUE_ID = '';", "var VENUE_ID = '" + venue_id + "';")
                webfield_content = webfield_content.replace("var HEADER = {};", "var HEADER = " + json.dumps(header) + ";")

                invitation=self.client.post_invitation(openreview.Invitation(id=f'{reviewers_id}/-/Recruitment',
                        invitees = ['everyone'],
                        readers = ['everyone'],
                        writers = [venue_id],
                        signatures = [venue_id],
                        reply = {
                            'signatures': { 'values-regex': '\\(anonymous\\)' },
                            'readers': { 'values': [venue_id] },
                            'writers': { 'values': []},
                            'content': {
                                'title': {
                                    'order': 1,
                                    'value': 'Recruit response'
                                },
                                'user': {
                                    'description': 'email address',
                                    'order': 2,
                                    'value-regex': '.*',
                                    'required':True
                                },
                                'key': {
                                    'description': 'Email key hash',
                                    'order': 3,
                                    'value-regex': '.{0,100}',
                                    'required':True
                                },
                                'response': {
                                    'description': 'Invitation response',
                                    'order': 4,
                                    'value-radio': ['Yes', 'No'],
                                    'required':True
                                }
                            }
                        },
                        process_string=process_content,
                        web_string=webfield_content
                    )
                )
                return invitation

