from __future__ import absolute_import

import os
import json
import datetime
import openreview
from .. import invitations
from .. import tools


class SubmissionInvitation(openreview.Invitation):

    def __init__(self, conference_id, conference_short_name, due_date, name, public = False, subject_areas = None, include_keywords = True, include_TLDR = True, additional_fields = None, additional_readers = []):

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

        if not include_keywords:
            del content['keywords']

        if not include_TLDR:
            del content['TL;DR']

        readers = {
            'values-copied': [
                conference_id,
                '{content.authorids}',
                '{signatures}'
            ] + additional_readers
        }

        if public:
            readers = {
                'values': ['everyone']
            }

        with open(os.path.join(os.path.dirname(__file__), 'templates/submissionProcess.js')) as f:
            file_content = f.read()
            file_content = file_content.replace("var SHORT_PHRASE = '';", "var SHORT_PHRASE = '" + conference_short_name + "';")
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

class PublicCommentInvitation(openreview.Invitation):

    def __init__(self, conference_id, name, number, paper_id, anonymous = False):

        content = invitations.comment
        prefix = conference_id + '/Paper' + str(number) + '/'
        signatures_regex = '~.*'

        if anonymous:
            signatures_regex = '~.*|\\(anonymous\\)'

        with open(os.path.join(os.path.dirname(__file__), 'templates/commentProcess.js')) as f:
            file_content = f.read()
            file_content = file_content.replace("var CONFERENCE_ID = '';", "var CONFERENCE_ID = '" + conference_id + "';")
            file_content = file_content.replace("var SHORT_PHRASE = '';", "var SHORT_PHRASE = '" + conference_id + "';")
            super(PublicCommentInvitation, self).__init__(id = conference_id + '/-/Paper' + str(number) + '/' + name,
                readers = ['everyone'],
                writers = [conference_id],
                signatures = [conference_id],
                invitees = ['~'],
                noninvitees = [
                    prefix + "Authors",
                    prefix + "Reviewers",
                    prefix + "Area_Chairs",
                    conference_id + '/' + "Program_Chairs"
                ],
                reply = {
                    'forum': paper_id,
                    'replyto': None,
                    'readers': {
                        "description": "Select all user groups that should be able to read this comment.",
                        "values-dropdown": [
                            "everyone",
                            prefix + "Authors",
                            prefix + "Reviewers",
                            prefix + "Area_Chairs",
                            conference_id + '/' + "Program_Chairs"
                        ]
                    },
                    'writers': {
                        'values-copied': [
                            conference_id,
                            '{signatures}'
                        ]
                    },
                    'signatures': {
                        'values-regex': signatures_regex,
                        'description': 'How your identity will be displayed.'
                    },
                    'content': content
                },
                process_string = file_content
            )

class OfficialCommentInvitation(openreview.Invitation):

    def __init__(self, conference, name, number, paper_id, anonymous = False):

        content = invitations.comment
        prefix = conference.id + '/Paper' + str(number) + '/'
        signatures_regex = '~.*'

        if anonymous:
            signatures_regex = '{prefix}AnonReviewer[0-9]+|{prefix}{authors_name}|{prefix}Area_Chair[0-9]+|{conference_id}/{program_chairs_name}'.format(prefix=prefix,
            conference_id=conference.id, authors_name = conference.authors_name, program_chairs_name = conference.program_chairs_name)

        with open(os.path.join(os.path.dirname(__file__), 'templates/commentProcess.js')) as f:
            file_content = f.read()

            file_content = file_content.replace("var CONFERENCE_ID = '';", "var CONFERENCE_ID = '" + conference.id + "';")
            file_content = file_content.replace("var SHORT_PHRASE = '';", "var SHORT_PHRASE = '" + conference.short_name + "';")
            file_content = file_content.replace("var AUTHORS_NAME = '';", "var AUTHORS_NAME = '" + conference.authors_name + "';")
            file_content = file_content.replace("var REVIEWERS_NAME = '';", "var REVIEWERS_NAME = '" + conference.reviewers_name + "';")
            file_content = file_content.replace("var AREA_CHAIRS_NAME = '';", "var AREA_CHAIRS_NAME = '" + conference.area_chairs_name + "';")
            file_content = file_content.replace("var PROGRAM_CHAIRS_NAME = '';", "var PROGRAM_CHAIRS_NAME = '" + conference.program_chairs_name + "';")
            super(OfficialCommentInvitation, self).__init__(id = conference.id + '/-/Paper' + str(number) + '/' + name,
                readers = ['everyone'],
                writers = [conference.id],
                signatures = [conference.id],
                invitees = [
                    prefix + conference.authors_name,
                    prefix + conference.reviewers_name,
                    prefix + conference.area_chairs_name,
                    conference.id + '/' + conference.program_chairs_name
                ],
                reply = {
                    'forum': paper_id,
                    'replyto': None,
                    'readers': {
                        "description": "Select all user groups that should be able to read this comment.",
                        "values-dropdown": [
                            prefix + conference.authors_name,
                            prefix + conference.reviewers_name,
                            prefix + conference.area_chairs_name,
                            conference.id + '/' + conference.program_chairs_name
                        ]
                    },
                    'writers': {
                        'values-copied': [
                            conference.id,
                            '{signatures}'
                        ]
                    },
                    'signatures': {
                        'values-regex': signatures_regex,
                        'description': 'How your identity will be displayed.'
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
            conference_short_name = built_options.get('conference_short_name'),
            due_date = due_date,
            name = built_options.get('submission_name'),
            public = built_options.get('public'),
            subject_areas = built_options.get('subject_areas'),
            additional_fields = built_options.get('additional_fields'),
            additional_readers = built_options.get('additional_readers'),
            include_keywords = built_options.get('include_keywords'),
            include_TLDR = built_options.get('include_TLDR'))

        return self.client.post_invitation(invitation)

    def set_public_comment_invitation(self, conference_id, notes, name, anonymous):

        for note in notes:
            self.client.post_invitation(PublicCommentInvitation(conference_id, name, note.number, note.id, anonymous))

    def set_private_comment_invitation(self, conference, notes, name, anonymous):

        for note in notes:
            self.client.post_invitation(OfficialCommentInvitation(conference, name, note.number, note.id, anonymous))

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
            content = content.replace("var REVIEWERS_ACCEPTED_ID = '';", "var REVIEWERS_ACCEPTED_ID = '" + options.get('reviewers_accepted_id') + "';")
            content = content.replace("var REVIEWERS_DECLINED_ID = '';", "var REVIEWERS_DECLINED_ID = '" + options.get('reviewers_declined_id') + "';")
            content = content.replace("var HASH_SEED = '';", "var HASH_SEED = '" + options.get('hash_seed') + "';")
            invitation = openreview.Invitation(id = conference_id + '/-/Recruit_' + options.get('reviewers_name', 'Reviewers'),
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
