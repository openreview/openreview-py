import openreview
import process
import tools
import builtins
from collections import namedtuple
import webfield


class Conference(object):
    def __init__(self, conference_id, short_phrase):
        self.conference_id = conference_id
        self.submission = None
        self.blind_submission = None
        self.short_phrase = short_phrase

        self.groups = {g.id:g for g in tools.build_groups(conference_id)}
        self.invitations = []
        self.homepage = None

    def add_submission(self, name, duedate, blind_name = None):
        self.submission = SubmissionInvitation(
            self.conference_id,
            name,
            duedate,
            short_phrase = self.short_phrase,
            blind_name = blind_name
        )

        if blind_name != None:
            self.blind_submission = SubmissionInvitation(
                self.conference_id,
                blind_name,
                duedate,
                submission_content = {
                    'title': None, 'keywords': None, 'TL;DR': None, 'abstract': None, 'pdf': None,
                    'authors': {'values-regex': '.*'}, 'authorids': {'values-regex': '.*'}
                },
                reply_params = {
                    'signatures': {'values': [self.conference_id]}, 'writers': {'values': [self.conference_id]}
                },
                invitation_params = {'invitees': [self.conference_id]}
            )

    def add_homepage(self, homepage):
        self.homepage = homepage
        if not self.homepage.user_constants['CONFERENCE']:
            self.homepage.user_constants['CONFERENCE'] = self.conference_id
        if not self.homepage.user_constants['ENTRY_INVITATION']:
            self.homepage.user_constants['ENTRY_INVITATION'] = self.submission.id
        if not self.homepage.user_constants['DISPLAY_INVITATION']:
            self.homepage.user_constants['DISPLAY_INVITATION'] = self.submission.id if not self.blind_submission else self.blind_submission.id

        self.groups[self.conference_id].web = self.homepage.render()

class SubmissionInvitation(openreview.Invitation):
    def __init__(self, conference_id, invitation_name, duedate,
        short_phrase = None,
        blind_name = None,
        submission_content = {},
        reply_params = {},
        invitation_params = {},
        params = {}):

        self.conference_id = conference_id
        self.invitation_name = invitation_name
        self.submission_content = {
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

        for k,v in submission_content.iteritems():
            if v:
                self.submission_content[k] = v
            else:
                self.submission_content.pop(k)

        self.reply_params = {
            'forum': None,
            'replyto': None,
            'readers': {
                'description': 'The users who will be allowed to read the above content.',
            },
            'signatures': {
                'description': 'Your authorized identity to be associated with the above content.',
            },
            'writers': {}
        }

        if blind_name != None:
            self.reply_params['readers']['values-copied'] = [
                conference_id, '{content.authorids}', '{signatures}']
            self.reply_params['signatures']['values-regex'] = '~.*|' + conference_id
            self.reply_params['writers']['values'] = [conference_id]
        else:
            self.reply_params['readers']['values'] = ['everyone']
            self.reply_params['signatures']['values-regex'] = '~.*'
            self.reply_params['writers']['values-regex'] = '~.*'

        for k,v in reply_params.iteritems():
            if v:
                self.reply_params[k] = v
            else:
                self.reply_params.pop(k)

        self.invitation_params = invitation_params if invitation_params else {
            'readers': ['everyone'],
            'writers': [conference_id],
            'invitees': ['~'],
            'signatures': [conference_id],
            'duedate': duedate
        }

        for k,v in invitation_params.iteritems():
            if v:
                self.invitation_params[k] = v
            else:
                self.invitation_params.pop(k)

        self.params = self.invitation_params
        self.params['reply'] = self.reply_params
        self.params['reply']['content'] = self.submission_content

        for k,v in params.iteritems():
            if v:
                self.params[k] = v
            else:
                self.params.pop(k)

        openreview.Invitation.__init__(
            self,
            '/'.join([self.conference_id, '-', self.invitation_name]),
            **self.params)

        if blind_name != None:
            self.process = process.SubmissionProcess(
                short_phrase = short_phrase,
                conference_id = conference_id,
                blind_name = blind_name).value

