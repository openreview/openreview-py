from __future__ import absolute_import

import os
import json
import datetime
import openreview
from .. import invitations
from .. import tools


class SubmissionInvitation(openreview.Invitation):

    def __init__(self, conference_id, conference_short_name, due_date, name, public = False, subject_areas = None, additional_fields = None, remove_fields = []):

        content = invitations.submission.copy()

        if subject_areas:
            content['subject_areas'] = {
                'order' : 5,
                'description' : "Select or type subject area",
                'values-dropdown': subject_areas,
                'required': True
            }

        for field in remove_fields:
            del content[field]

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

class BlindSubmissionsInvitation(openreview.Invitation):

    def __init__(self, conference_id, invitation_id):
        super(BlindSubmissionsInvitation, self).__init__(id = invitation_id,
            readers = ['everyone'],
            writers = [conference_id],
            signatures = [conference_id],
            invitees = ['~'],
            reply = {
                'forum': None,
                'replyto': None,
                'readers': {
                    'values-regex': '.*'
                },
                'writers': {
                    'values': [conference_id]
                },
                'signatures': {
                    'values': [conference_id]
                },
                'content': {
                    'authors': {
                        'values': ['Anonymous']
                    },
                    'authorids': {
                        'values-regex': '.*'
                    }
                }
            }
        )

class SubmissionRevisionInvitation(openreview.Invitation):

    def __init__(self, conference, name, note, due_date, public, submission_content, additional_fields, remove_fields):

        content = submission_content.copy()

        for field in remove_fields:
            del content[field]

        for order, key in enumerate(additional_fields, start=10):
            value = additional_fields[key]
            value['order'] = order
            content[key] = value

        readers = {
            'values-copied': [
                conference.get_id(),
                '{content.authorids}',
                '{signatures}'
            ]
        }

        if public:
            readers = {
                'values': ['everyone']
            }

        with open(os.path.join(os.path.dirname(__file__), 'templates/submissionRevisionProcess.js')) as f:
            file_content = f.read()
            file_content = file_content.replace("var SHORT_PHRASE = '';", "var SHORT_PHRASE = '" + conference.get_short_name() + "';")
            super(SubmissionRevisionInvitation, self).__init__(id = conference.get_id() + '/-/Paper' + str(note.number) + '/' + name,
                duedate = tools.datetime_millis(due_date),
                readers = ['everyone'],
                writers = [conference.get_id()],
                signatures = [conference.get_id()],
                invitees = note.content['authorids'] + note.signatures,
                reply = {
                    'forum': note.id,
                    'referent': note.id,
                    'readers': readers,
                    'writers': {
                        'values-copied': [
                            conference.get_id(),
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

class BidInvitation(openreview.Invitation):
    def __init__(self, conference, due_date, request_count, with_area_chairs):

        readers = [
            conference.get_id(),
            conference.get_program_chairs_id(),
            conference.get_reviewers_id()
        ]

        invitees = [ conference.get_reviewers_id() ]
        if with_area_chairs:
            readers.append(conference.get_area_chairs_id())
            invitees.append(conference.get_area_chairs_id())

        super(BidInvitation, self).__init__(id = conference.get_bid_id(),
            readers = readers,
            writers = [conference.get_id()],
            signatures = [conference.get_id()],
            invitees = invitees,
            multiReply = True,
            taskCompletionCount = request_count,
            reply = {
                'forum': None,
                'replyto': None,
                'invitation': conference.get_blind_submission_id(),
                'readers': {
                    'values-copied': [conference.get_id(), '{signatures}']
                },
                'signatures': {
                    'values-regex': '~.*'
                },
                'content': {
                    'tag': {
                        'required': True,
                        'value-radio': [ 'High', 'Neutral', 'Low', 'Very Low', 'No Bid']
                    }
                }
            }
        )



class PublicCommentInvitation(openreview.Invitation):

    def __init__(self, conference_id, name, number, paper_id, anonymous = False):

        content = invitations.comment.copy()

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

        content = invitations.comment.copy()

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

class ReviewInvitation(openreview.Invitation):

    def __init__(self, conference, name, number, paper_id, due_date, public):
        content = invitations.review.copy()

        prefix = conference.id + '/Paper' + str(number) + '/'
        readers = ['everyone']

        if not public:
            readers = [
                prefix + conference.authors_name,
                prefix + conference.reviewers_name,
                prefix + conference.area_chairs_name,
                conference.id + '/' + conference.program_chairs_name
            ]

        with open(os.path.join(os.path.dirname(__file__), 'templates/reviewProcess.js')) as f:
            file_content = f.read()

            file_content = file_content.replace("var CONFERENCE_ID = '';", "var CONFERENCE_ID = '" + conference.id + "';")
            file_content = file_content.replace("var SHORT_PHRASE = '';", "var SHORT_PHRASE = '" + conference.short_name + "';")
            file_content = file_content.replace("var AUTHORS_NAME = '';", "var AUTHORS_NAME = '" + conference.authors_name + "';")
            file_content = file_content.replace("var REVIEWERS_NAME = '';", "var REVIEWERS_NAME = '" + conference.reviewers_name + "';")
            file_content = file_content.replace("var AREA_CHAIRS_NAME = '';", "var AREA_CHAIRS_NAME = '" + conference.area_chairs_name + "';")
            file_content = file_content.replace("var PROGRAM_CHAIRS_NAME = '';", "var PROGRAM_CHAIRS_NAME = '" + conference.program_chairs_name + "';")
            super(ReviewInvitation, self).__init__(id = conference.id + '/-/Paper' + str(number) + '/' + name,
                duedate = tools.datetime_millis(due_date),
                readers = ['everyone'],
                writers = [conference.id],
                signatures = [conference.id],
                invitees = [prefix + conference.reviewers_name],
                reply = {
                    'forum': paper_id,
                    'replyto': paper_id,
                    'readers': {
                        "description": "Select all user groups that should be able to read this comment.",
                        "values": readers
                    },
                    'writers': {
                        'values-regex': prefix + 'Anon' + conference.reviewers_name[:-1] + '[0-9]+',
                        'description': 'How your identity will be displayed.'
                    },
                    'signatures': {
                        'values-regex': prefix + 'Anon' + conference.reviewers_name[:-1] + '[0-9]+',
                        'description': 'How your identity will be displayed.'
                    },
                    'content': content
                },
                process_string = file_content
            )

class MetaReviewInvitation(openreview.Invitation):

    def __init__(self, conference, name, number, paper_id, due_date, public):
        content = invitations.meta_review.copy()

        readers = ['everyone']

        if not public:
            readers = [
                conference.get_area_chairs_id(number),
                conference.get_program_chairs_id()
            ]

        super(MetaReviewInvitation, self).__init__(id = conference.id + '/-/Paper' + str(number) + '/' + name,
            duedate = tools.datetime_millis(due_date),
            readers = ['everyone'],
            writers = [conference.id],
            signatures = [conference.id],
            invitees = [conference.get_area_chairs_id(number)],
            reply = {
                'forum': paper_id,
                'replyto': paper_id,
                'readers': {
                    "description": "Select all user groups that should be able to read this comment.",
                    "values": readers
                },
                'writers': {
                    'values-regex': conference.get_area_chairs_id(number)[:-1] + '[0-9]+',
                    'description': 'How your identity will be displayed.'
                },
                'signatures': {
                    'values-regex': conference.get_area_chairs_id(number)[:-1] + '[0-9]+',
                    'description': 'How your identity will be displayed.'
                },
                'content': content
            }
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
            remove_fields = built_options.get('remove_fields'))

        return self.client.post_invitation(invitation)

    def set_blind_submission_invitation(self, conference):

        invitation = BlindSubmissionsInvitation(conference_id = conference.get_id(), invitation_id = conference.get_blind_submission_id())

        return  self.client.post_invitation(invitation)

    def set_bid_invitation(self, conference, due_date, request_count, with_area_chairs):

        invitation = BidInvitation(conference, due_date, request_count, with_area_chairs)

        return self.client.post_invitation(invitation)

    def set_public_comment_invitation(self, conference_id, notes, name, anonymous):

        for note in notes:
            self.client.post_invitation(PublicCommentInvitation(conference_id, name, note.number, note.id, anonymous))

    def set_private_comment_invitation(self, conference, notes, name, anonymous):

        for note in notes:
            self.client.post_invitation(OfficialCommentInvitation(conference, name, note.number, note.id, anonymous))

    def set_review_invitation(self, conference, notes, name, due_date, public):

        for note in notes:
            self.client.post_invitation(ReviewInvitation(conference, name, note.number, note.id, due_date, public))

    def set_meta_review_invitation(self, conference, notes, name, due_date, public):

        for note in notes:
            self.client.post_invitation(MetaReviewInvitation(conference, name, note.number, note.id, due_date, public))

    def set_revise_submission_invitation(self, conference, notes, name, due_date, public, submission_content, additional_fields, remove_fields):

        for note in notes:
            self.client.post_invitation(SubmissionRevisionInvitation(conference, name, note, due_date, public, submission_content, additional_fields, remove_fields))

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
