'''
Invitation templates and tools.

Most classes extend
'''
from __future__ import absolute_import, division, print_function, unicode_literals
import sys
if sys.version_info[0] < 3:
    string_types = [str, unicode]
else:
    string_types = [str]

from .. import openreview
from . import content
import re

class Submission(openreview.Invitation):
    def __init__(self, conference_id = None, id = None,
        duedate = None, process = None, inv_params = {},
        reply_params = {}, content_params = {}, mask = {}):

        self.conference_id = conference_id

        if id:
            self.id = id
        else:
            self.id = '/'.join([self.conference_id, '-', 'Submission'])

        default_inv_params = {
            'id': self.id,
            'readers': ['everyone'],
            'writers': [self.conference_id],
            'invitees': ['~'],
            'signatures': [self.conference_id],
            'duedate': duedate,
            'process': process
        }

        default_reply_params = {
            'forum': None,
            'replyto': None,
            'readers': {
                'description': 'The users who will be allowed to read the above content.',
                'values': ['everyone']
            },
            'signatures': {
                'description': 'Your authorized identity to be associated with the above content.',
                'values-regex': '~.*'
            },
            'writers': {
                'values': [self.conference_id]
            }
        }

        self.content_params = {}
        self.content_params.update(content.submission)
        self.content_params.update(content_params)

        if mask:
            self.content_params = mask

        self.reply_params = {}
        self.reply_params.update(default_reply_params)
        self.reply_params.update(reply_params)
        self.reply_params['content'] = self.content_params

        self.inv_params = {}
        self.inv_params.update(default_inv_params)
        self.inv_params.update(inv_params)
        self.inv_params['reply'] = self.reply_params

        super(Submission, self).__init__(**self.inv_params)

    def add_process(self, process):
        self.process = process.render()

class AddBid(openreview.Invitation):
    def __init__(self, conference_id, id = None,
        duedate = None, completion_count = 50, inv_params = {},
        reply_params = {}, content_params = {}):

        self.conference_id = conference_id

        if id:
            self.id = id
        else:
            self.id = '/'.join([self.conference_id, '-', 'Add_Bid'])

        default_inv_params = {
            'id': self.id,
            'readers': [conference_id, conference_id + '/Reviewers'],
            'writers': [conference_id],
            'invitees': [conference_id + '/Reviewers'],
            'signatures': [conference_id],
            'duedate': duedate, # 17:00:00 EST on May 1, 2018
            'taskCompletionCount': 50,
            'multiReply': False,
        }

        default_reply_params = {
            'forum': None,
            'replyto': None,
            'invitation': conference_id + '/-/Blind_Submission',
            'readers': {
                'description': 'The users who will be allowed to read the above content.',
                'values-copied': [conference_id, '{signatures}']
            },
            'signatures': {
                'description': 'How your identity will be displayed with the above content.',
                'values-regex': '~.*'
            }
        }

        self.content_params = {}
        self.content_params.update(content.bid)
        self.content_params.update(content_params)

        self.reply_params = {}
        self.reply_params.update(default_reply_params)
        self.reply_params.update(reply_params)
        self.reply_params['content'] = self.content_params

        self.inv_params = {}
        self.inv_params.update(default_inv_params)
        self.inv_params.update(inv_params)
        self.inv_params['reply'] = self.reply_params

        super(AddBid, self).__init__(**self.inv_params)

class Comment(openreview.Invitation):
    def __init__(self, conference_id, id = None,
        duedate = 0, process = None, invitation = None,
        inv_params = {}, reply_params = {}, content_params = {}):

        self.conference_id = conference_id

        if id:
            self.id = id
        else:
            self.id = '/'.join([self.conference_id, '-', 'Comment'])

        default_inv_params = {
            'id': self.id,
            'readers': ['everyone'],
            'writers': [self.conference_id],
            'invitees': ['~'],
            'signatures': [self.conference_id],
            'duedate': duedate,
            'process': process
        }

        default_reply_params = {
            'forum': None,
            'replyto': None,
            'invitation': invitation,
            'readers': {
                'description': 'The users who will be allowed to read the above content.',
                'values': ['everyone']
            },
            'signatures': {
                'description': 'Your authorized identity to be associated with the above content.',
                'values-regex': '~.*'
            },
            'writers': {
                'values': [self.conference_id]
            }
        }

        self.content_params = {}
        self.content_params.update(content.comment)
        self.content_params.update(content_params)

        self.reply_params = {}
        self.reply_params.update(default_reply_params)
        self.reply_params.update(reply_params)
        self.reply_params['content'] = self.content_params

        self.inv_params = {}
        self.inv_params.update(default_inv_params)
        self.inv_params.update(inv_params)
        self.inv_params['reply'] = self.reply_params

        super(Comment, self).__init__(**self.inv_params)

    def add_process(self, process):
        self.process = process.render()

class RecruitReviewers(openreview.Invitation):
    def __init__(self, conference_id, id = None,
        duedate = 0, process = None, web = None,
        inv_params = {}, reply_params = {}, content_params = {}):

        if id:
            self.id = id
        else:
            self.id = '/'.join([self.conference_id, '-', 'Recruit_Reviewers'])

        self.conference_id = conference_id

        default_inv_params = {
            'id': self.id,
            'readers': ['everyone'],
            'writers': [self.conference_id],
            'invitees': ['~'],
            'signatures': [self.conference_id],
            'duedate': duedate,
            'process': process,
            'web': web
        }

        default_reply_params = {
            'forum': None,
            'replyto': None,
            'readers': {
                'values': ['~Super_User1']
            },
            'signatures': {
                'values-regex': '\\(anonymous\\)'
            },
            'writers': {
                'values': []
            }
        }

        self.content_params = {}
        self.content_params.update(content.recruitment)
        self.content_params.update(content_params)

        self.reply_params = {}
        self.reply_params.update(default_reply_params)
        self.reply_params.update(reply_params)
        self.reply_params['content'] = self.content_params

        self.inv_params = {}
        self.inv_params.update(default_inv_params)
        self.inv_params.update(inv_params)
        self.inv_params['reply'] = self.reply_params

        super(RecruitReviewers, self).__init__(**self.inv_params)
