from __future__ import absolute_import

import os
import json
import datetime
import openreview
from .. import invitations
from .. import tools


class InvitationBuilder(object):

    def __init__(self, client):
        self.client = client

    def __build_options(self, default, options):

        merged_options = {}
        for k in default:
            if k in options:
                merged_options[k] = options[k]
            else:
                merged_options[k] = default[k]
        return merged_options

    def set_submission_invitation(self, conference_id, options = {}):

        default_reply = {
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
                'values': [conference_id]
            },
            'content': invitations.submission
        }

        reply = self.__build_options(default_reply, options.get('reply', {}))


        with open(os.path.join(os.path.dirname(__file__), 'templates/submissionProcess.js')) as f:
            content = f.read()
            content = content.replace("var SHORT_PHRASE = '';", "var SHORT_PHRASE = '" + options.get('short_name', conference_id) + "';")
            invitation = openreview.Invitation(id = conference_id + '/-/' + options.get('name', 'Submission'),
                duedate = tools.datetime_millis(options.get('due_date', datetime.datetime.now())),
                readers = ['everyone'],
                nonreaders = [],
                invitees = ['~'],
                noninvitees = [],
                writers = [conference_id],
                signatures = [conference_id],
                reply = reply,
                process_string = content)

            return self.client.post_invitation(invitation)

    def set_reviewer_recruiter_invitation(self, conference_id, options = {}):

        default_reply = {
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
            },
            'content': invitations.recruitment
        }

        reply = self.__build_options(default_reply, options.get('reply', {}))


        with open(os.path.join(os.path.dirname(__file__), 'templates/recruitReviewersProcess.js')) as f:
            content = f.read()
            content = content.replace("var CONFERENCE_ID = '';", "var CONFERENCE_ID = '" + conference_id + "';")
            content = content.replace("var REVIEWERS_ID = '';", "var REVIEWERS_ID = '" + options.get('reviewers_id') + "';")
            content = content.replace("var REVIEWERS_DECLINED_ID = '';", "var REVIEWERS_DECLINED_ID = '" + options.get('reviewers_declined_id') + "';")
            content = content.replace("var HASH_SEED = '';", "var HASH_SEED = '" + options.get('hash_seed') + "';")
            invitation = openreview.Invitation(id = conference_id + '/-/Recruit_Reviewers',
                duedate = tools.datetime_millis(options.get('due_date', datetime.datetime.now())),
                readers = ['everyone'],
                nonreaders = [],
                invitees = ['everyone'],
                noninvitees = [],
                writers = [conference_id],
                signatures = [conference_id],
                reply = reply,
                process_string = content)

            return self.client.post_invitation(invitation)
