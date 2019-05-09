from __future__ import absolute_import

import os
import json
import datetime
import openreview
from .. import invitations
from .. import tools

SHORT_BUFFER_MIN = 30
LONG_BUFFER_DAYS = 10

class SubmissionInvitation(openreview.Invitation):

    def __init__(self, conference, start_date, due_date, readers, additional_fields, remove_fields):

        content = invitations.submission.copy()

        if conference.get_subject_areas():
            content['subject_areas'] = {
                'order' : 5,
                'description' : "Select or type subject area",
                'values-dropdown': conference.get_subject_areas(),
                'required': True
            }

        for field in remove_fields:
            del content[field]

        for order, key in enumerate(additional_fields, start=10):
            value = additional_fields[key]
            value['order'] = order
            content[key] = value

        with open(os.path.join(os.path.dirname(__file__), 'templates/submissionProcess.js')) as f:
            file_content = f.read()
            file_content = file_content.replace("var SHORT_PHRASE = '';", "var SHORT_PHRASE = '" + conference.get_short_name() + "';")
            super(SubmissionInvitation, self).__init__(id = conference.get_submission_id(),
                cdate = tools.datetime_millis(start_date),
                duedate = tools.datetime_millis(due_date),
                expdate = tools.datetime_millis(due_date + datetime.timedelta(minutes = SHORT_BUFFER_MIN)) if due_date else None,
                readers = ['everyone'],
                writers = [conference.get_id()],
                signatures = [conference.get_id()],
                invitees = ['~'],
                reply = {
                    'forum': None,
                    'replyto': None,
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

class BlindSubmissionsInvitation(openreview.Invitation):

    def __init__(self, conference):
        super(BlindSubmissionsInvitation, self).__init__(id = conference.get_blind_submission_id(),
            readers = ['everyone'],
            writers = [conference.get_id()],
            signatures = [conference.get_id()],
            invitees = ['~'],
            reply = {
                'forum': None,
                'replyto': None,
                'readers': {
                    'values-regex': '.*'
                },
                'writers': {
                    'values': [conference.get_id()]
                },
                'signatures': {
                    'values': [conference.get_id()]
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

    def __init__(self, conference, name, note, start_date, due_date, readers, submission_content, additional_fields, remove_fields):

        content = submission_content.copy()
        referent = note.original if conference.double_blind else note.id

        for field in remove_fields:
            del content[field]

        for order, key in enumerate(additional_fields, start=10):
            value = additional_fields[key]
            value['order'] = order
            content[key] = value

        with open(os.path.join(os.path.dirname(__file__), 'templates/submissionRevisionProcess.js')) as f:
            file_content = f.read()
            file_content = file_content.replace("var SHORT_PHRASE = '';", "var SHORT_PHRASE = '" + conference.get_short_name() + "';")
            super(SubmissionRevisionInvitation, self).__init__(id = conference.get_invitation_id(name, note.number),
                cdate = tools.datetime_millis(start_date),
                duedate = tools.datetime_millis(due_date),
                readers = ['everyone'],
                writers = [conference.get_id()],
                signatures = [conference.get_id()],
                invitees = note.content['authorids'] + note.signatures,
                reply = {
                    'forum': referent,
                    'referent': referent,
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
    def __init__(self, conference, start_date, due_date, request_count, with_area_chairs):

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
            cdate = tools.datetime_millis(start_date),
            duedate = tools.datetime_millis(due_date),
            expdate = tools.datetime_millis(due_date + datetime.timedelta(minutes = SHORT_BUFFER_MIN)) if due_date else None,
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
                        'value-radio': [ 'Very High', 'High', 'Neutral', 'Low', 'Very Low']
                    }
                }
            }
        )

class PublicCommentInvitation(openreview.Invitation):

    def __init__(self, conference, name, note, start_date, anonymous = False, reader_selection = False, email_pcs = False):

        content = invitations.comment.copy()

        authors_id = conference.get_authors_id(number = note.number)
        reviewers_id = conference.get_reviewers_id(number = note.number)
        area_chairs_id = conference.get_area_chairs_id(number = note.number)
        program_chairs_id = conference.get_program_chairs_id()

        committee = []
        committee.append(authors_id)
        committee.append(reviewers_id)
        if conference.use_area_chairs:
            committee.append(area_chairs_id)
        committee.append(program_chairs_id)

        signatures_regex = '~.*'

        if anonymous:
            signatures_regex = '~.*|\\(anonymous\\)'

        with open(os.path.join(os.path.dirname(__file__), 'templates/commentProcess.js')) as f:
            file_content = f.read()
            file_content = file_content.replace("var SHORT_PHRASE = '';", "var SHORT_PHRASE = '" + conference.short_name + "';")
            file_content = file_content.replace("var AUTHORS_ID = '';", "var AUTHORS_ID = '" + conference.get_authors_id(number = note.number) + "';")
            file_content = file_content.replace("var REVIEWERS_ID = '';", "var REVIEWERS_ID = '" + conference.get_reviewers_id(number = note.number) + "';")
            if email_pcs:
                file_content = file_content.replace("var PROGRAM_CHAIRS_ID = '';", "var PROGRAM_CHAIRS_ID = '" + conference.get_program_chairs_id() + "';")

            if conference.use_area_chairs:
                file_content = file_content.replace("var AREA_CHAIRS_ID = '';", "var AREA_CHAIRS_ID = '" + area_chairs_id + "';")

            if reader_selection:
                reply_readers = {
                    "description": "Who your comment will be visible to. If replying to a specific person make sure to add the group they are a member of so that they are able to see your response",
                    "values-dropdown": ["everyone"] + committee
                }
            else:
                reply_readers = {
                    "description": "User groups that will be able to read this comment.",
                    "values": ["everyone"]
                }

            super(PublicCommentInvitation, self).__init__(id = conference.get_invitation_id(name, note.number),
                cdate = tools.datetime_millis(start_date),
                readers = ['everyone'],
                writers = [conference.get_id()],
                signatures = [conference.get_id()],
                invitees = ['~'],
                noninvitees = committee,
                reply = {
                    'forum': note.id,
                    'replyto': None,
                    'readers': reply_readers,
                    'writers': {
                        'values-copied': [
                            conference.get_id(),
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

    def __init__(self, conference, name, note, start_date, anonymous, unsubmitted_reviewers, reader_selection = False, email_pcs = False):

        content = invitations.comment.copy()
        authors_id = conference.get_authors_id(number = note.number)
        reviewers_id = conference.get_reviewers_id(number = note.number) + '/Submitted'
        if unsubmitted_reviewers:
            reviewers_id = conference.get_reviewers_id(number = note.number)
        area_chairs_id = conference.get_area_chairs_id(number = note.number)
        program_chairs_id = conference.get_program_chairs_id()

        committee = []
        committee.append(authors_id)
        committee.append(reviewers_id)
        if conference.use_area_chairs:
            committee.append(area_chairs_id)
        committee.append(program_chairs_id)

        prefix = conference.get_id() + '/Paper' + str(note.number) + '/'
        signatures_regex = '~.*'

        if anonymous:
            signatures_regex = '{prefix}AnonReviewer[0-9]+|{prefix}{authors_name}|{prefix}Area_Chair[0-9]+|{conference_id}/{program_chairs_name}'.format(prefix=prefix, conference_id=conference.id, authors_name = conference.authors_name, program_chairs_name = conference.program_chairs_name)

        with open(os.path.join(os.path.dirname(__file__), 'templates/commentProcess.js')) as f:
            file_content = f.read()

            file_content = file_content.replace("var SHORT_PHRASE = '';", "var SHORT_PHRASE = '" + conference.short_name + "';")
            file_content = file_content.replace("var AUTHORS_ID = '';", "var AUTHORS_ID = '" + authors_id + "';")
            file_content = file_content.replace("var REVIEWERS_ID = '';", "var REVIEWERS_ID = '" + reviewers_id + "';")
            if email_pcs:
                file_content = file_content.replace("var PROGRAM_CHAIRS_ID = '';", "var PROGRAM_CHAIRS_ID = '" + program_chairs_id + "';")

            if conference.use_area_chairs:
                file_content = file_content.replace("var AREA_CHAIRS_ID = '';", "var AREA_CHAIRS_ID = '" + area_chairs_id + "';")

            if reader_selection:
                reply_readers = {
                    "description": "Who your comment will be visible to. If replying to a specific person make sure to add the group they are a member of so that they are able to see your response",
                    "values-dropdown": committee
                }
            else:
                reply_readers = {
                    "description": "User groups that will be able to read this comment.",
                    "values": committee
                }


            super(OfficialCommentInvitation, self).__init__(id = conference.get_invitation_id(name, note.number),
                cdate = tools.datetime_millis(start_date),
                readers = ['everyone'],
                writers = [conference.id],
                signatures = [conference.id],
                invitees = committee,
                reply = {
                    'forum': note.id,
                    'replyto': None,
                    'readers': reply_readers,
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

    def __init__(self, conference, note, start_date, due_date, allow_de_anonymization, public, release_to_authors, release_to_reviewers, email_pcs, additional_fields):
        content = invitations.review.copy()

        for key in additional_fields:
            content[key] = additional_fields[key]

        signature_regex = conference.get_id() + '/Paper' + str(note.number) + '/AnonReviewer[0-9]+'

        if allow_de_anonymization:
            signature_regex = signature_regex + '|~.*'

        readers = []
        nonreaders = [conference.get_authors_id(number = note.number)]

        if public:
            readers = ['everyone']
            nonreaders = []
        else:
            readers = [ conference.get_program_chairs_id()]
            if conference.use_area_chairs:
                readers.append(conference.get_area_chairs_id(number = note.number))

        if release_to_reviewers:
            readers.append(conference.get_reviewers_id(number = note.number))
        else:
            readers.append(conference.get_reviewers_id(number = note.number) + '/Submitted')

        if release_to_authors:
            readers.append(conference.get_authors_id(number = note.number))
            nonreaders = []


        with open(os.path.join(os.path.dirname(__file__), 'templates/reviewProcess.js')) as f:
            file_content = f.read()

            file_content = file_content.replace("var CONFERENCE_ID = '';", "var CONFERENCE_ID = '" + conference.id + "';")
            file_content = file_content.replace("var SHORT_PHRASE = '';", "var SHORT_PHRASE = '" + conference.short_name + "';")
            file_content = file_content.replace("var AUTHORS_NAME = '';", "var AUTHORS_NAME = '" + conference.authors_name + "';")
            file_content = file_content.replace("var REVIEWERS_NAME = '';", "var REVIEWERS_NAME = '" + conference.reviewers_name + "';")
            file_content = file_content.replace("var AREA_CHAIRS_NAME = '';", "var AREA_CHAIRS_NAME = '" + conference.area_chairs_name + "';")
            if email_pcs:
                file_content = file_content.replace("var PROGRAM_CHAIRS_NAME = '';", "var PROGRAM_CHAIRS_NAME = '" + conference.program_chairs_name + "';")

            super(ReviewInvitation, self).__init__(id = conference.get_invitation_id(conference.review_name, note.number),
                cdate = tools.datetime_millis(start_date),
                duedate = tools.datetime_millis(due_date),
                expdate = tools.datetime_millis(due_date + datetime.timedelta(days = LONG_BUFFER_DAYS)) if due_date else None,
                readers = ['everyone'],
                writers = [conference.id],
                signatures = [conference.id],
                invitees = [conference.get_reviewers_id(number = note.number)],
                reply = {
                    'forum': note.id,
                    'replyto': note.id,
                    'readers': {
                        "description": "Select all user groups that should be able to read this comment.",
                        "values": readers
                    },
                    'nonreaders': {
                        "values": nonreaders
                    },
                    'writers': {
                        'values-regex': signature_regex,
                        'description': 'How your identity will be displayed.'
                    },
                    'signatures': {
                        'values-regex': signature_regex,
                        'description': 'How your identity will be displayed.'
                    },
                    'content': content
                },
                process_string = file_content
            )

class ReviewRevisionInvitation(openreview.Invitation):

    def __init__(self, conference, name, review, start_date, due_date, additional_fields, remove_fields):
        with open(os.path.join(os.path.dirname(__file__), 'templates/reviewRevisionProcess.js')) as f:
            file_content = f.read()

            file_content = file_content.replace("var CONFERENCE_ID = '';", "var CONFERENCE_ID = '" + conference.id + "';")
            file_content = file_content.replace("var SHORT_PHRASE = '';", "var SHORT_PHRASE = '" + conference.short_name + "';")
            file_content = file_content.replace("var AUTHORS_NAME = '';", "var AUTHORS_NAME = '" + conference.authors_name + "';")
            file_content = file_content.replace("var REVIEWERS_NAME = '';", "var REVIEWERS_NAME = '" + conference.reviewers_name + "';")
            file_content = file_content.replace("var AREA_CHAIRS_NAME = '';", "var AREA_CHAIRS_NAME = '" + conference.area_chairs_name + "';")
            file_content = file_content.replace("var PROGRAM_CHAIRS_NAME = '';", "var PROGRAM_CHAIRS_NAME = '" + conference.program_chairs_name + "';")

            super(ReviewRevisionInvitation, self).__init__(id = '{review_invitation}/{anon_reviewer}/{name}'.format(review_invitation = review.invitation, anon_reviewer = review.signatures[0].split('/')[-1], name = name),
                super = review.invitation,
                cdate = tools.datetime_millis(start_date),
                duedate = tools.datetime_millis(due_date),
                expdate = tools.datetime_millis(due_date + datetime.timedelta(minutes = LONG_BUFFER_DAYS)) if due_date else None,
                reply = {
                    'forum': review.forum,
                    'replyto': None,
                    'referent': review.id
                },
                writers = [ review.invitation.split('/-/')[0] ],
                signatures = [ review.invitation.split('/-/')[0] ],
                process_string = file_content
            )

class MetaReviewInvitation(openreview.Invitation):

    def __init__(self, conference, note, start_date, due_date, public, additional_fields):
        content = invitations.meta_review.copy()

        for key in additional_fields:
            content[key] = additional_fields[key]

        readers = ['everyone']
        regex = conference.get_program_chairs_id()
        invitees = [conference.get_program_chairs_id()]
        private_readers = [conference.get_program_chairs_id()]

        if conference.use_area_chairs:
            regex = conference.get_area_chairs_id(note.number)[:-1] + '[0-9]+'
            invitees = [conference.get_area_chairs_id(number = note.number)]
            private_readers = [conference.get_area_chairs_id(number = note.number), conference.get_program_chairs_id()]

        if not public:
            readers = private_readers

        super(MetaReviewInvitation, self).__init__(id = conference.get_invitation_id(conference.meta_review_name, note.number),
            cdate = tools.datetime_millis(start_date),
            duedate = tools.datetime_millis(due_date),
            expdate = tools.datetime_millis(due_date + datetime.timedelta(days = LONG_BUFFER_DAYS)) if due_date else None,
            readers = ['everyone'],
            writers = [conference.id],
            signatures = [conference.id],
            invitees = invitees,
            reply = {
                'forum': note.id,
                'replyto': note.id,
                'readers': {
                    "description": "Select all user groups that should be able to read this comment.",
                    "values": readers
                },
                'writers': {
                    'values-regex': regex,
                    'description': 'How your identity will be displayed.'
                },
                'signatures': {
                    'values-regex': regex,
                    'description': 'How your identity will be displayed.'
                },
                'content': content
            }
        )

class DecisionInvitation(openreview.Invitation):

    def __init__(self, conference, note, options, start_date, due_date, public, release_to_authors, release_to_reviewers):
        content = {
            'title': {
                'order': 1,
                'required': True,
                'value': 'Acceptance Decision'
            },
            'decision': {
                'order': 2,
                'required': True,
                'value-radio': options,
                'description': 'Acceptance decision'
            },
            'comment': {
                'order': 3,
                'required': False,
                'value-regex': '[\\S\\s]{0,5000}',
                'description': ''
            }
        }

        readers = []
        nonreaders = [conference.get_authors_id(number = note.number)]

        if public:
            readers = ['everyone']
            nonreaders = []
        else:
            readers = [ conference.get_program_chairs_id()]
            if conference.use_area_chairs:
                readers.append(conference.get_area_chairs_id(number = note.number))

        if release_to_reviewers:
            readers.append(conference.get_reviewers_id(number = note.number))

        if release_to_authors:
            readers.append(conference.get_authors_id(number = note.number))
            nonreaders = []

        super(DecisionInvitation, self).__init__(id = conference.get_invitation_id(conference.decision_name, note.number),
            cdate = tools.datetime_millis(start_date),
            duedate = tools.datetime_millis(due_date),
            expdate = tools.datetime_millis(due_date + datetime.timedelta(minutes = LONG_BUFFER_DAYS)) if due_date else None,
            readers = ['everyone'],
            writers = [conference.id],
            signatures = [conference.id],
            invitees = [conference.get_program_chairs_id()],
            reply = {
                'forum': note.id,
                'replyto': note.id,
                'readers': {
                    "description": "Select all user groups that should be able to read this comment.",
                    "values": readers
                },
                'nonreaders': {
                    "values": nonreaders
                },
                'writers': {
                    'values-regex': [conference.get_program_chairs_id()],
                    'description': 'How your identity will be displayed.'
                },
                'signatures': {
                    'values': [conference.get_program_chairs_id()],
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

    def set_submission_invitation(self, conference, start_date, due_date, additional_fields, remove_fields):

        readers = {}

        ## TODO: move this to an object
        if conference.double_blind:
            readers = {
                'values-copied': [
                    conference.get_id(),
                    '{content.authorids}',
                    '{signatures}'
                ] + conference.get_original_readers()
            }
        else:
            if conference.submission_public:
                readers = {
                    'values': ['everyone']
                }
            else:
                readers = {
                    'values-copied': [
                        conference.get_id(),
                        '{content.authorids}',
                        '{signatures}'
                    ] + conference.get_submission_readers()
                }

        invitation = SubmissionInvitation(conference = conference,
            start_date = start_date,
            due_date = due_date,
            readers = readers,
            additional_fields = additional_fields,
            remove_fields = remove_fields)

        return self.client.post_invitation(invitation)

    def set_blind_submission_invitation(self, conference):

        invitation = BlindSubmissionsInvitation(conference = conference)

        return  self.client.post_invitation(invitation)

    def set_bid_invitation(self, conference, start_date, due_date, request_count, with_area_chairs):

        invitation = BidInvitation(conference, start_date, due_date, request_count, with_area_chairs)

        return self.client.post_invitation(invitation)

    def set_public_comment_invitation(self, conference, notes, name, start_date, anonymous, reader_selection, email_pcs):

        for note in notes:
            self.client.post_invitation(PublicCommentInvitation(conference, name, note, start_date, anonymous, reader_selection, email_pcs))

    def set_private_comment_invitation(self, conference, notes, name, start_date, anonymous, unsubmitted_reviewers, reader_selection, email_pcs):

        for note in notes:
            self.client.post_invitation(OfficialCommentInvitation(conference, name, note, start_date, anonymous, unsubmitted_reviewers, reader_selection, email_pcs))

    def set_review_invitation(self, conference, notes, start_date, due_date, allow_de_anonymization, public, release_to_authors, release_to_reviewers, email_pcs, additional_fields):

        invitations = []
        for note in notes:
            invitations.append(self.client.post_invitation(ReviewInvitation(conference, note, start_date, due_date, allow_de_anonymization, public, release_to_authors, release_to_reviewers, email_pcs, additional_fields)))

        return invitations

    def set_meta_review_invitation(self, conference, notes, start_date, due_date, public, additional_fields):

        for note in notes:
            self.client.post_invitation(MetaReviewInvitation(conference, note, start_date, due_date, public, additional_fields))

    def set_decision_invitation(self, conference, notes, options, start_date, due_date, public, release_to_authors, release_to_reviewers):

        for note in notes:
            self.client.post_invitation(DecisionInvitation(conference, note, options, start_date, due_date, public, release_to_authors, release_to_reviewers))

    def set_revise_submission_invitation(self, conference, notes, name, start_date, due_date, submission_content, additional_fields, remove_fields):

        readers = {}

        ## TODO: move this to an object
        if conference.double_blind:
            readers = {
                'values-copied': [
                    conference.get_id(),
                    '{content.authorids}',
                    '{signatures}'
                ] + conference.get_original_readers()
            }
        else:
            if conference.submission_public:
                readers = {
                    'values': ['everyone']
                }
            else:
                readers = {
                    'values-copied': [
                        conference.get_id(),
                        '{content.authorids}',
                        '{signatures}'
                    ] + conference.get_submission_readers()
                }

        for note in notes:
            self.client.post_invitation(SubmissionRevisionInvitation(conference, name, note, start_date, due_date, readers, submission_content, additional_fields, remove_fields))

    def set_revise_review_invitation(self, conference, reviews, name, start_date, due_date, additional_fields, remove_fields):

        for review in reviews:
            self.client.post_invitation(ReviewRevisionInvitation(conference, name, review, start_date, due_date, additional_fields, remove_fields))


    def set_reviewer_recruiter_invitation(self, conference, options = {}):

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
            content = content.replace("var CONFERENCE_ID = '';", "var CONFERENCE_ID = '" + conference.get_id() + "';")
            content = content.replace("var REVIEWERS_ACCEPTED_ID = '';", "var REVIEWERS_ACCEPTED_ID = '" + options.get('reviewers_accepted_id') + "';")
            content = content.replace("var REVIEWERS_DECLINED_ID = '';", "var REVIEWERS_DECLINED_ID = '" + options.get('reviewers_declined_id') + "';")
            content = content.replace("var HASH_SEED = '';", "var HASH_SEED = '" + options.get('hash_seed') + "';")
            invitation = openreview.Invitation(id = conference.get_invitation_id('Recruit_' + options.get('reviewers_name', 'Reviewers')),
                duedate = tools.datetime_millis(options.get('due_date', datetime.datetime.utcnow())),
                readers = ['everyone'],
                nonreaders = [],
                invitees = ['everyone'],
                noninvitees = [],
                writers = [conference.get_id()],
                signatures = [conference.get_id()],
                reply = reply,
                process_string = content)

            return self.client.post_invitation(invitation)

    def set_recommendation_invitation(self, conference, start_date, due_date, notes_iterator, assignment_notes_iterator):

        assignment_note_by_forum = {}
        if assignment_notes_iterator:
            for assignment_note in assignment_notes_iterator:
                assignment_note_by_forum[assignment_note.forum] = assignment_note.content

        # Create super invitation with a webfield
        recommendation_invitation = openreview.Invitation(
            id = conference.get_recommendation_id(),
            cdate = tools.datetime_millis(start_date),
            duedate = tools.datetime_millis(due_date),
            expdate = tools.datetime_millis(due_date + datetime.timedelta(minutes = SHORT_BUFFER_MIN)),
            readers = [conference.get_program_chairs_id(), conference.get_area_chairs_id()],
            invitees = [],
            writers = [conference.get_id()],
            signatures = [conference.get_id()],
            multiReply = True,
            reply = {
                'invitation': conference.get_blind_submission_id(),
                'readers': {
                    'description': 'The users who will be allowed to read the above content.',
                    'values-copied': [conference.get_id(), '{signatures}']
                },
                'signatures': {
                    'description': 'How your identity will be displayed with the above content.',
                    'values-regex': '~.*'
                },
                'content': {
                    'tag': {
                        'description': 'Recommend reviewer',
                        'order': 1,
                        'required': True,
                        'values-url': '/groups?id=' + conference.get_reviewers_id()
                    }
                }
            }
        )

        recommendation_invitation = self.client.post_invitation(recommendation_invitation)
        # Create subinvitation with different list of reviewers, bid, tpms score.

        for note in notes_iterator:
            reviewers = []
            assignment_note = assignment_note_by_forum.get(note.id)
            reply = {
                'forum': note.id
            }
            if assignment_note:
                for group in assignment_note['assignedGroups']:
                    reviewers.append('{profileId} (A) - Bid: {bid} - Tpms: {tpms}'.format(
                        profileId = group.get('userId'),
                        bid = group.get('scores').get('bid'),
                        tpms = group.get('scores').get('affinity'))
                    )
                for group in assignment_note['alternateGroups']:
                    reviewers.append('{profileId} - Bid: {bid} - Tpms: {tpms}'.format(
                        profileId = group.get('userId'),
                        bid = group.get('scores').get('bid'),
                        tpms = group.get('scores').get('affinity'))
                    )
                reply['content'] = {
                    'tag': {
                        'description': 'Recommend reviewer',
                        'order': 1,
                        'required': True,
                        'values-dropdown': reviewers
                    }
                }
            paper_recommendation_invitation = openreview.Invitation(
                id = conference.get_recommendation_id(number = note.number),
                cdate = tools.datetime_millis(start_date),
                duedate = tools.datetime_millis(due_date),
                expdate = tools.datetime_millis(due_date + datetime.timedelta(minutes = SHORT_BUFFER_MIN)),
                super = recommendation_invitation.id,
                invitees = [conference.get_program_chairs_id(), conference.get_area_chairs_id(note.number)],
                writers = [conference.get_id()],
                signatures = [conference.get_id()],
                multiReply = True,
                reply = reply
            )
            paper_recommendation_invitation = self.client.post_invitation(paper_recommendation_invitation)


    def set_registration_invitation(self, conference, start_date, due_date, with_area_chairs):

        invitees = []
        if with_area_chairs:
            invitees.append(conference.get_area_chairs_id())
        invitees.append(conference.get_reviewers_id())

        subj_desc = 'To properly assign papers to reviewers, we ask that reviewers provide their areas of expertise from among the provided list of subject areas. Please submit your areas of expertise by selecting the appropriate options from the "Subject Areas" list.\n\n'

        coi_desc = 'In order to avoid conflicts of interest in reviewing, we ask that all reviewers take a moment to update their OpenReview profiles with their latest information regarding work history and professional relationships. After you have updated your profile, please confirm that your OpenReview profile is up-to-date by selecting yes in the "Profile Confirmed" section.\n\n'

        tpms_desc = 'In addition to subject areas, we will be using the Toronto Paper Matching System (TPMS) to compute paper-reviewer affinity scores. Please take a moment to sign up for TPMS and/or update your TPMS account with your latest papers. Then, please ensure that the email address that is affiliated with your TPMS account is linked to your OpenReview profile. After you have done this, please confirm that your TPMS account is up-to-date by selecting yes in the "TPMS Account Confirmed" section.\n\n'


        # Create super invitation with a webfield
        registration_parent_invitation = openreview.Invitation(
            id = conference.get_invitation_id('Super/Registration'),
            readers = ['everyone'],
            writers = [conference.get_id()],
            signatures = [conference.get_id()],
            invitees = invitees,
            reply = {
                'forum': None,
                'replyto': None,
                'readers': {'values': invitees},
                'writers': {'values': [conference.get_id()]},
                'signatures': {'values': [conference.get_id()]},
                'content': {
                    'title': {'value': conference.get_short_name() + ' Registration'},
                    'subject_areas': {
                        'value': subj_desc,
                        'order': 1
                    },
                    'profile confirmed': {
                        'value': coi_desc,
                        'order': 2
                    },
                    'TPMS account confirmed': {
                        'value': tpms_desc,
                        'order': 3
                    }
                }
            }
        )

        registration_parent_invitation = self.client.post_invitation(registration_parent_invitation)

        registration_parent = self.client.post_note(openreview.Note(
            invitation = registration_parent_invitation.id,
            readers = invitees,
            writers = [conference.get_id()],
            signatures = [conference.get_id()],
            replyto = None,
            forum = None,
            content = {
                'title': registration_parent_invitation.reply['content']['title']['value'],
                'subject_areas': registration_parent_invitation.reply['content']['subject_areas']['value'],
                'profile confirmed': registration_parent_invitation.reply['content']['profile confirmed']['value'],
                'TPMS account confirmed': registration_parent_invitation.reply['content']['TPMS account confirmed']['value'],
            }
        ))

        registration_invitation = self.client.post_invitation(openreview.Invitation(
            id = conference.get_registration_id(),
            cdate = tools.datetime_millis(start_date),
            duedate = tools.datetime_millis(due_date),
            expdate = tools.datetime_millis(due_date),
            readers = ['everyone'],
            writers = [conference.get_id()],
            signatures = [conference.get_id()],
            invitees = invitees,
            reply = {
                'forum': registration_parent.id,
                'replyto': registration_parent.id,
                'readers': {
                    'description': 'Users who can read this',
                    'values-copied': [
                        conference.get_id(),
                        '{signatures}'
                    ]
                },
                'writers': {
                    'description': 'How your identity will be displayed.',
                    'values-copied': [
                        conference.get_id(),
                        '{signatures}'
                    ]
                },
                'signatures': {
                    'description': 'How your identity will be displayed.',
                    'values-regex': '~.*'
                },
                'content': {
                    'title': {
                        'value': conference.get_short_name() + ' Registration',
                        'order': 1
                    },
                    'subject_areas': {
                        'values-dropdown': conference.get_subject_areas(),
                        'required': True,
                        'order': 2
                    },
                    'profile confirmed': {
                        'value-radio': ['Yes', 'No'],
                        'required': True,
                        'order': 3
                    },
                    'TPMS account confirmed': {
                        'value-radio': ['Yes', 'No'],
                        'required': True,
                        'order': 4
                    }
                }
            }
        ))

        return self.client.post_invitation(registration_invitation)

