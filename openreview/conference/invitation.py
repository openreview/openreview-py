from __future__ import absolute_import

import os
import json
import datetime
import openreview
from .. import invitations
from .. import tools


class SubmissionInvitation(openreview.Invitation):

    def __init__(self, conference_id, due_date, name, public = False, subject_areas = None, additional_fields = None):

        content = invitations.submission

        if subject_areas:
            content['subject_areas'] = {
                'order' : 5,
                'description' : "Select or type subject area",
                'values-dropdown': subject_areas,
                'required': True
            }

        for order, key in enumerate(additional_fields, start=10):
            value = additional_fields[key]
            value['order'] = order
            content[key] = value

        readers = {
            'values-copied': [
                conference_id,
                '{content.authorids}',
                '{signatures}'
            ]
        }

        if public:
            readers = {
                'values': ['everyone']
            }

        with open(os.path.join(os.path.dirname(__file__), 'templates/submissionProcess.js')) as f:
            file_content = f.read()
            file_content = file_content.replace("var SHORT_PHRASE = '';", "var SHORT_PHRASE = '" + conference_id + "';")
            super(SubmissionInvitation, self).__init__(id = conference_id + '/-/' + name,
                duedate = tools.datetime_millis(due_date),
                readers = ['everyone'],
                writers = [conference_id],
                signatures = [conference_id],
                invitees = ['~'],
                reply = {
                    'forum': None,
                    'replyto': None,
                    'readers': readers,
                    'writers': {
                        'values-copied': [
                            conference_id,
                            '{content.authorids}',
                            '{signatures}'
                        ]
                    },
                    'signatures': {
                        'values-regex': '~.*'
                    },
                    'content': content
                },
                process_string = file_content
            )


class InvitationBuilder(object):

    def __init__(self, client):
        self.client = client

    def __build_options(self, default, options):

        merged_options = {}
        for k in default:
            merged_options[k] = default[k]

        for o in options:
            merged_options[o] = options[o]

        return merged_options

    def set_submission_invitation(self, conference_id, due_date, options = {}):

        default_options = {
            'public': False,
            'subject_areas': None,
            'additional_fields': None
        }

        built_options = self.__build_options(default_options, options)

        invitation = SubmissionInvitation(conference_id = conference_id,
            due_date = due_date,
            name = built_options.get('name'),
            public = built_options.get('public'),
            subject_areas = built_options.get('subject_areas'),
            additional_fields = built_options.get('additional_fields'))

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
