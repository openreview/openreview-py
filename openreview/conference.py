import openreview
import process
import tools
import builtins
from collections import namedtuple
import webfield

class Conference(object):
    def __init__(self, conference_id, short_phrase = 'a venue hosted on OpenReview'):
        self.conference_id = conference_id
        self.short_phrase = short_phrase

        self.entry_invitation = None
        self.display_invitation = None

        self.groups = {g.id: g for g in tools.build_groups(self.conference_id)}
        self.invitations = {}
        self.homepage = None

    def add_submission(self, submission_name, duedate = 0, process = None, content = {}):
        submission_params = {
            'id': '/'.join([self.conference_id, '-', submission_name]),
            'readers': ['everyone'],
            'writers': [self.conference_id],
            'invitees': ['~'],
            'signatures': [self.conference_id],
            'duedate': duedate,
            'reply': {
                'forum': None,
                'replyto': None,
                'readers': {
                    'description': 'The users who will be allowed to read the above content.'
                },
                'signatures': {
                    'description': 'Your authorized identity to be associated with the above content.'
                },
                'writers': {
                    'values': [self.conference_id]
                },
                'content': self.get_submission_content(content)
            }
        }

        self.entry_invitation = openreview.Invitation(**submission_params)

        if process:
            self.entry_process = process
            self.entry_process.user_constants = {
              'CONFERENCE': self.conference_id,
              'ENTRY_INVITATION': self.entry_invitation.id,
              'SHORT_PHRASE': self.short_phrase
            }

            self.entry_invitation.process = self.entry_process

        if process and process.mask:
            self.entry_invitation.reply['readers']['values-copied'] = [
                self.conference_id, '{content.authorids}', '{signatures}']
            self.entry_invitation.reply['signatures']['values-regex'] = '~.*|' + self.conference_id
            self.entry_invitation.reply['writers']['values'] = [self.conference_id]

            blind_submission_params = {
                'id': '/'.join([self.conference_id, '-', process.mask]),
                'readers': ['everyone'],
                'writers': [self.conference_id],
                'invitees': [self.conference_id],
                'signatures': [self.conference_id],
                'reply': {
                    'forum': None,
                    'replyto': None,
                    'readers': {'values': ['everyone']},
                    'signatures': {'values': [self.conference_id]},
                    'writers': {'values': [self.conference_id]},
                    'content': {
                        'authors': {'values-regex': '.*'},
                        'authorids': {'values-regex': '.*'}
                    }
                }
            }

            self.display_invitation = openreview.Invitation(**blind_submission_params)
            self.entry_invitation.process.user_constants['DISPLAY_INVITATION'] = self.display_invitation.id

        else:
            submission_params['reply']['readers']['values'] = ['everyone']
            submission_params['reply']['signatures']['values-regex'] = '~.*'
            submission_params['reply']['writers']['values-regex'] = '~.*'
            self.display_invitation = self.entry_invitation

    def add_homepage(self, homepage):
        self.homepage = homepage
        if 'CONFERENCE' not in self.homepage.user_constants:
            self.homepage.user_constants['CONFERENCE'] = self.conference_id
        if 'ENTRY_INVITATION' not in self.homepage.user_constants:
            self.homepage.user_constants['ENTRY_INVITATION'] = self.entry_invitation.id
        if 'DISPLAY_INVITATION' not in self.homepage.user_constants:
            self.homepage.user_constants['DISPLAY_INVITATION'] = self.display_invitation.id

        self.groups[self.conference_id].web = self.homepage.render()

    def add_invitation(self, name, params,
        invitees = ['~'],
        by_paper = False,
        by_forum = False,
        reference = False,
        original = False):

        params = {
            'readers': ['everyone'],
            'writers': [self.conference_id],
            'invitees': [], # set during submission process function; replaced in invitations.py
            'signatures': [self.conference_id],
            'process': os.path.abspath(os.path.join(os.path.dirname(__file__), '../process/addRevisionProcess.js')),
            'reply': {
                'forum': None,
                'referent': None,
                'signatures': submission_params['reply']['signatures'],
                'writers': submission_params['reply']['writers'],
                'readers': submission_params['reply']['readers'],
                'content': submission_params['reply']['content']
            }
        }

    def get_submission_content(self, content = {}):
        submission_content = {
            'title': {
                'description': 'Title of paper.',
                'order': 1,
                'value-regex': '.{1,250}',
                'required':True
            },
            'authors': {
                'description': 'Comma separated list of author names. Please provide real names; identities will be anonymized.',
                'order': 2,
                'values-regex': "[^;,\\n]+(,[^,\\n]+)*",
                'required':True
            },
            'authorids': {
                'description': 'Comma separated list of author email addresses, lowercased, in the same order as above. For authors with existing OpenReview accounts, please make sure that the provided email address(es) match those listed in the author\'s profile. Please provide real emails; identities will be anonymized.',
                'order': 3,
                'values-regex': "([a-z0-9_\-\.]{2,}@[a-z0-9_\-\.]{2,}\.[a-z]{2,},){0,}([a-z0-9_\-\.]{2,}@[a-z0-9_\-\.]{2,}\.[a-z]{2,})",
                'required':True
            },
            'keywords': {
                'description': 'Comma separated list of keywords.',
                'order': 6,
                'values-regex': "(^$)|[^;,\\n]+(,[^,\\n]+)*"
            },
            'TL;DR': {
                'description': '\"Too Long; Didn\'t Read\": a short sentence describing your paper',
                'order': 7,
                'value-regex': '[^\\n]{0,250}',
                'required':False
            },
            'abstract': {
                'description': 'Abstract of paper.',
                'order': 8,
                'value-regex': '[\\S\\s]{1,5000}',
                'required':True
            },
            'pdf': {
                'description': 'Upload a PDF file that ends with .pdf',
                'order': 9,
                'value-regex': 'upload',
                'required':True
            }
        }

        for k,v in content.iteritems():
            if v:
                submission_content[k] = v
            else:
                submission_content.pop(k)

        return submission_content

