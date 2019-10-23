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

    def __init__(self, conference):

        readers = {}
        submission_stage = conference.submission_stage
        additional_fields = submission_stage.additional_fields
        start_date = submission_stage.start_date
        due_date = submission_stage.due_date
        readers = submission_stage.get_readers(conference)

        content = invitations.submission.copy()

        if submission_stage.subject_areas:
            content['subject_areas'] = {
                'order' : 5,
                'description' : "Select or type subject area",
                'values-dropdown': submission_stage.subject_areas,
                'required': True
            }

        for field in submission_stage.remove_fields:
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
        referent = note.original if conference.submission_stage.double_blind else note.id

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
    def __init__(self, conference, match_group_id):

        bid_stage = conference.bid_stage

        readers = [
            conference.get_id(),
            conference.get_program_chairs_id(),
            match_group_id
        ]

        invitees = [match_group_id]

        super(BidInvitation, self).__init__(id = conference.get_bid_id(match_group_id),
            cdate = tools.datetime_millis(bid_stage.start_date),
            duedate = tools.datetime_millis(bid_stage.due_date),
            expdate = tools.datetime_millis(bid_stage.due_date + datetime.timedelta(minutes = SHORT_BUFFER_MIN)) if bid_stage.due_date else None,
            readers = readers,
            writers = [conference.get_id()],
            signatures = [conference.get_id()],
            invitees = invitees,
            taskCompletionCount = bid_stage.request_count,
            reply = {
                'readers': {
                    'values-copied': [conference.get_id(), '{signatures}']
                },
                'signatures': {
                    'values-regex': '~.*'
                },
                'content': {
                    'head': {
                        'type': 'Note',
                        'query' : {
                            'invitation' : conference.get_blind_submission_id()
                        },
                        'required': True
                    },
                    'tail': {
                        'type': 'Group',
                        'query' : {
                            'group' : match_group_id
                        },
                        'required': True
                    },
                    'label': {
                        'value-radio': ['Very High', 'High', 'Neutral', 'Low', 'Very Low'],
                        'required': True
                    }
                }
            }
        )

class ExpertiseSelectionInvitation(openreview.Invitation):
    def __init__(self, conference):

        expertise_selection_stage = conference.expertise_selection_stage

        readers = [
            conference.get_id(),
            conference.get_program_chairs_id(),
            conference.get_reviewers_id()
        ]

        invitees = [ conference.get_reviewers_id() ]
        if conference.use_area_chairs:
            readers.append(conference.get_area_chairs_id())
            invitees.append(conference.get_area_chairs_id())

        super(ExpertiseSelectionInvitation, self).__init__(id = conference.get_expertise_selection_id(),
            cdate = tools.datetime_millis(expertise_selection_stage.start_date),
            duedate = tools.datetime_millis(expertise_selection_stage.due_date),
            expdate = tools.datetime_millis(expertise_selection_stage.due_date + datetime.timedelta(minutes = SHORT_BUFFER_MIN)) if expertise_selection_stage.due_date else None,
            readers = readers,
            writers = [conference.get_id()],
            signatures = [conference.get_id()],
            invitees = invitees,
            multiReply = True,
            reply = {
                'readers': {
                    'values-copied': [conference.get_id(), '{signatures}']
                },
                'signatures': {
                    'values-regex': '~.*'
                },
                'content': {
                    'head': {
                        'type': 'Note'
                    },
                    'tail': {
                        'type': 'Group'
                    },
                    'label': {
                        'value-radio': ['Exclude'],
                        'required': True
                    }
                }
            }
        )

class CommentInvitation(openreview.Invitation):

    def __init__(self, conference):

        content = invitations.comment.copy()

        with open(os.path.join(os.path.dirname(__file__), 'templates/commentProcess.js')) as f:
            file_content = f.read()
            file_content = file_content.replace("var CONFERENCE_ID = '';", "var CONFERENCE_ID = '" + conference.id + "';")
            file_content = file_content.replace("var SHORT_PHRASE = '';", "var SHORT_PHRASE = '" + conference.short_name + "';")
            file_content = file_content.replace("var AUTHORS_NAME = '';", "var AUTHORS_NAME = '" + conference.authors_name + "';")
            file_content = file_content.replace("var REVIEWERS_NAME = '';", "var REVIEWERS_NAME = '" + conference.reviewers_name + "';")
            file_content = file_content.replace("var AREA_CHAIRS_NAME = '';", "var AREA_CHAIRS_NAME = '" + conference.area_chairs_name + "';")

            if conference.use_area_chairs:
                file_content = file_content.replace("var USE_AREA_CHAIRS = false;", "var USE_AREA_CHAIRS = true;")

            if conference.comment_stage.email_pcs:
                file_content = file_content.replace("var PROGRAM_CHAIRS_ID = '';", "var PROGRAM_CHAIRS_ID = '" + conference.get_program_chairs_id() + "';")

            super(CommentInvitation, self).__init__(id = conference.get_invitation_id('Comment'),
                cdate = tools.datetime_millis(conference.comment_stage.start_date),
                readers = ['everyone'],
                writers = [conference.get_id()],
                signatures = [conference.get_id()],
                reply = {
                    'content': content
                },
                process_string = file_content
            )

class WithdrawnSubmissionInvitation(openreview.Invitation):

    def __init__(self, conference, withdrawn_submission_content=None):

        content = invitations.submission.copy()
        if withdrawn_submission_content:
            content = withdrawn_submission_content

        if (conference.submission_stage.double_blind and not conference.submission_stage.reveal_authors_on_withdraw):
            content['authors'] = {
                'values': ['Anonymous']
            }
            content['authorids'] = {
                'values-regex': '.*'
            }

        super(WithdrawnSubmissionInvitation, self).__init__(
            id=conference.submission_stage.get_withdrawn_submission_id(conference),
            cdate=tools.datetime_millis(conference.submission_stage.due_date),
            readers=['everyone'],
            writers=[conference.get_id()],
            signatures=[conference.get_id()],
            reply={
                'forum': None,
                'replyto': None,
                'readers': {
                    "description": "The users who will be allowed to read the reply content.",
                    "values": [
                        "everyone"
                    ]
                },
                'writers': {
                    'values': [
                        conference.get_id()
                    ]
                },
                'signatures': {
                    'values': [
                        conference.get_id()
                    ]
                },
                'content': content
            }
        )

class PaperWithdrawInvitation(openreview.Invitation):

    def __init__(self, conference, note):

        content = invitations.withdraw.copy()

        withdraw_process_file = 'templates/withdraw_process.py'

        with open(os.path.join(os.path.dirname(__file__), withdraw_process_file)) as f:
            file_content = f.read()

            file_content = file_content.replace(
                'CONFERENCE_ID = \'\'',
                'CONFERENCE_ID = \'' + conference.get_id() + '\'')
            file_content = file_content.replace(
                'CONFERENCE_SHORT_NAME = \'\'',
                'CONFERENCE_SHORT_NAME = \'' + conference.get_short_name() + '\'')
            file_content = file_content.replace(
                'PAPER_AUTHORS_ID = \'\'',
                'PAPER_AUTHORS_ID = \'' + conference.get_authors_id(number=note.number) + '\'')
            file_content = file_content.replace(
                'PAPER_REVIEWERS_ID = \'\'',
                'PAPER_REVIEWERS_ID = \'' + conference.get_reviewers_id(number=note.number) + '\'')
            if conference.use_area_chairs:
                file_content = file_content.replace(
                    'PAPER_AREA_CHAIRS_ID = \'\'',
                    'PAPER_AREA_CHAIRS_ID = \'' + conference.get_area_chairs_id(number=note.number) + '\'')
            file_content = file_content.replace(
                'PROGRAM_CHAIRS_ID = \'\'',
                'PROGRAM_CHAIRS_ID = \'' + conference.get_program_chairs_id() + '\'')
            file_content = file_content.replace(
                'WITHDRAWN_SUBMISSION_ID = \'\'',
                'WITHDRAWN_SUBMISSION_ID = \'' + conference.submission_stage.get_withdrawn_submission_id(conference) + '\'')
            if conference.submission_stage.reveal_authors_on_withdraw:
                file_content = file_content.replace(
                    'REVEAL_AUTHORS_ON_WITHDRAW = False',
                    "REVEAL_AUTHORS_ON_WITHDRAW = True")

            super(PaperWithdrawInvitation, self).__init__(
                id=conference.get_invitation_id('Withdraw', note.number),
                cdate=tools.datetime_millis(conference.submission_stage.due_date),
                duedate = tools.datetime_millis(conference.submission_stage.due_date + datetime.timedelta(days = 80)),
                expdate = tools.datetime_millis(conference.submission_stage.due_date + datetime.timedelta(days = 90)),
                invitees=[conference.get_authors_id(note.number)],
                readers=['everyone'],
                writers=[conference.get_id()],
                signatures=['OpenReview.net'],
                multiReply=False,
                reply={
                    'forum': note.id,
                    'replyto': note.id,
                    'readers': {
                        "description": "User groups that will be able to read this withdraw note.",
                        "values": ["everyone"]
                    },
                    'writers': {
                        'values-copied': [
                            conference.get_id(),
                            '{signatures}'
                        ]
                    },
                    'signatures': {
                        'values-regex': conference.get_authors_id(note.number),
                        'description': 'How your identity will be displayed.'
                    },
                    'content': content
                },
                process_string=file_content
            )

class DeskRejectedSubmissionInvitation(openreview.Invitation):

    def __init__(self, conference, desk_rejected_submission_content=None):

        content = invitations.submission.copy()
        if desk_rejected_submission_content:
            content = desk_rejected_submission_content

        if (conference.submission_stage.double_blind and not conference.submission_stage.reveal_authors_on_desk_reject):
            content['authors'] = {
                'values': ['Anonymous']
            }
            content['authorids'] = {
                'values-regex': '.*'
            }

        super(DeskRejectedSubmissionInvitation, self).__init__(
            id=conference.submission_stage.get_desk_rejected_submission_id(conference),
            cdate=tools.datetime_millis(conference.submission_stage.due_date),
            readers=['everyone'],
            writers=[conference.get_id()],
            signatures=[conference.get_id()],
            reply={
                'forum': None,
                'replyto': None,
                'readers': {
                    "description": "The users who will be allowed to read the reply content.",
                    "values": [
                        "everyone"
                    ]
                },
                'writers': {
                    'values': [
                        conference.get_id()
                    ]
                },
                'signatures': {
                    'values': [
                        conference.get_id()
                    ]
                },
                'content': content
            }
        )

class PaperDeskRejectInvitation(openreview.Invitation):

    def __init__(self, conference, note):

        content = invitations.desk_reject.copy()

        desk_reject_process_file = 'templates/desk_reject_process.py'

        with open(os.path.join(os.path.dirname(__file__), desk_reject_process_file)) as f:
            file_content = f.read()

            file_content = file_content.replace(
                'CONFERENCE_ID = \'\'',
                'CONFERENCE_ID = \'' + conference.get_id() + '\'')
            file_content = file_content.replace(
                'CONFERENCE_SHORT_NAME = \'\'',
                'CONFERENCE_SHORT_NAME = \'' + conference.get_short_name() + '\'')
            file_content = file_content.replace(
                'PAPER_AUTHORS_ID = \'\'',
                'PAPER_AUTHORS_ID = \'' + conference.get_authors_id(number=note.number) + '\'')
            file_content = file_content.replace(
                'PAPER_REVIEWERS_ID = \'\'',
                'PAPER_REVIEWERS_ID = \'' + conference.get_reviewers_id(number=note.number) + '\'')
            if conference.use_area_chairs:
                file_content = file_content.replace(
                    'PAPER_AREA_CHAIRS_ID = \'\'',
                    'PAPER_AREA_CHAIRS_ID = \'' + conference.get_area_chairs_id(number=note.number) + '\'')
            file_content = file_content.replace(
                'PROGRAM_CHAIRS_ID = \'\'',
                'PROGRAM_CHAIRS_ID = \'' + conference.get_program_chairs_id() + '\'')
            file_content = file_content.replace(
                'DESK_REJECTED_SUBMISSION_ID = \'\'',
                'DESK_REJECTED_SUBMISSION_ID = \'' + conference.submission_stage.get_desk_rejected_submission_id(conference) + '\'')
            if conference.submission_stage.reveal_authors_on_desk_reject:
                file_content = file_content.replace(
                    'REVEAL_AUTHORS_ON_DESK_REJECT = False',
                    "REVEAL_AUTHORS_ON_DESK_REJECT = True")

            super(PaperDeskRejectInvitation, self).__init__(
                id=conference.get_invitation_id('Desk_Reject', note.number),
                cdate=tools.datetime_millis(conference.submission_stage.due_date),
                duedate = tools.datetime_millis(conference.submission_stage.due_date + datetime.timedelta(days = 80)),
                expdate = tools.datetime_millis(conference.submission_stage.due_date + datetime.timedelta(days = 90)),
                invitees=[conference.get_program_chairs_id()],
                readers=['everyone'],
                writers=[conference.get_id()],
                signatures=['OpenReview.net'],
                multiReply=False,
                reply={
                    'forum': note.id,
                    'replyto': note.id,
                    'readers': {
                        "description": "User groups that will be able to read this desk reject note.",
                        "values": ["everyone"]
                    },
                    'writers': {
                        'values-copied': [
                            conference.get_id(),
                            '{signatures}'
                        ]
                    },
                    'signatures': {
                        'values-regex': conference.get_program_chairs_id(),
                        'description': 'How your identity will be displayed.'
                    },
                    'content': content
                },
                process_string=file_content
            )

class PublicCommentInvitation(openreview.Invitation):

    def __init__(self, conference, note):

        comment_stage = conference.comment_stage

        super(PublicCommentInvitation, self).__init__(id = conference.get_invitation_id('Public_Comment', note.number),
            super = conference.get_invitation_id('Comment'),
            writers = [conference.get_id()],
            signatures = [conference.get_id()],
            invitees = ['everyone'],
            noninvitees = conference.get_committee(number = note.number, with_authors = True),
            reply = {
                'forum': note.id,
                'replyto': None,
                'readers': {
                    "description": "User groups that will be able to read this comment.",
                    "values": ["everyone"]
                },
                'writers': {
                    'values-copied': [
                        conference.get_id(),
                        '{signatures}'
                    ]
                },
                'signatures': {
                    'values-regex': '~.*|\\(anonymous\\)' if comment_stage.anonymous else '~.*',
                    'description': 'How your identity will be displayed.'
                }
            }
        )

class OfficialCommentInvitation(openreview.Invitation):

    def __init__(self, conference, note):

        comment_stage = conference.comment_stage

        prefix = conference.get_id() + '/Paper' + str(note.number) + '/'

        readers = []
        invitees = conference.get_committee(number=note.number, with_authors=True)
        if comment_stage.allow_public_comments:
            readers.append('everyone')

        readers.append(conference.get_authors_id(note.number))

        if comment_stage.reader_selection:
            readers.append(conference.get_reviewers_id(note.number).replace('Reviewers', 'AnonReviewer.*'))

        readers.append(conference.get_reviewers_id(note.number) + '/Submitted')

        if comment_stage.unsubmitted_reviewers:
            readers.append(conference.get_reviewers_id(note.number))

        if conference.use_area_chairs:
            readers.append(conference.get_area_chairs_id(note.number))

        readers.append(conference.get_program_chairs_id())

        if comment_stage.reader_selection:
            reply_readers = {
                "description": "Who your comment will be visible to. If replying to a specific person make sure to add the group they are a member of so that they are able to see your response",
                "values-dropdown": readers
            }
        else:
            reply_readers = {
                "description": "User groups that will be able to read this comment.",
                "values": readers
            }

        super(OfficialCommentInvitation, self).__init__(id = conference.get_invitation_id('Official_Comment', note.number),
            super = conference.get_invitation_id('Comment'),
            writers = [conference.id],
            signatures = [conference.id],
            invitees = invitees,
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
                    'values-regex': '{prefix}AnonReviewer[0-9]+|{prefix}{authors_name}|{prefix}Area_Chair[0-9]+|{conference_id}/{program_chairs_name}'.format(prefix=prefix, conference_id=conference.id, authors_name = conference.authors_name, program_chairs_name = conference.program_chairs_name),
                    'description': 'How your identity will be displayed.'
                }
            }
        )

class ReviewInvitation(openreview.Invitation):

    def __init__(self, conference):
        review_stage = conference.review_stage
        content = invitations.review.copy()

        for key in review_stage.additional_fields:
            content[key] = review_stage.additional_fields[key]

        for field in review_stage.remove_fields:
            if field in content:
                del content[field]

        with open(os.path.join(os.path.dirname(__file__), 'templates/reviewProcess.js')) as f:
            file_content = f.read()

            file_content = file_content.replace("var CONFERENCE_ID = '';", "var CONFERENCE_ID = '" + conference.id + "';")
            file_content = file_content.replace("var SHORT_PHRASE = '';", "var SHORT_PHRASE = '" + conference.short_name + "';")
            file_content = file_content.replace("var AUTHORS_NAME = '';", "var AUTHORS_NAME = '" + conference.authors_name + "';")
            file_content = file_content.replace("var REVIEWERS_NAME = '';", "var REVIEWERS_NAME = '" + conference.reviewers_name + "';")
            file_content = file_content.replace("var AREA_CHAIRS_NAME = '';", "var AREA_CHAIRS_NAME = '" + conference.area_chairs_name + "';")

            if conference.use_area_chairs:
                file_content = file_content.replace("var USE_AREA_CHAIRS = false;", "var USE_AREA_CHAIRS = true;")

            if review_stage.email_pcs:
                file_content = file_content.replace("var PROGRAM_CHAIRS_ID = '';", "var PROGRAM_CHAIRS_ID = '" + conference.get_program_chairs_id() + "';")


            super(ReviewInvitation, self).__init__(id = conference.get_invitation_id(review_stage.name),
                cdate = tools.datetime_millis(review_stage.start_date),
                duedate = tools.datetime_millis(review_stage.due_date),
                expdate = tools.datetime_millis(review_stage.due_date + datetime.timedelta(days = LONG_BUFFER_DAYS)) if review_stage.due_date else None,
                readers = ['everyone'],
                writers = [conference.id],
                signatures = [conference.id],
                multiReply = False,
                reply = {
                    'content': content
                },
                process_string = file_content
            )

class PaperReviewInvitation(openreview.Invitation):

    def __init__(self, conference, note):

        review_stage = conference.review_stage
        signature_regex = review_stage.get_signatures(conference, note.number)
        readers = review_stage.get_readers(conference, note.number)
        nonreaders = review_stage.get_nonreaders(conference, note.number)

        super(PaperReviewInvitation, self).__init__(id = conference.get_invitation_id(review_stage.name, note.number),
            super = conference.get_invitation_id(review_stage.name),
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
                }
            }
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
                writers = [conference.id],
                signatures = [conference.id],
                process_string = file_content
            )

class MetaReviewInvitation(openreview.Invitation):

    def __init__(self, conference):
        content = invitations.meta_review.copy()
        meta_review_stage = conference.meta_review_stage
        additional_fields = meta_review_stage.additional_fields
        start_date = meta_review_stage.start_date
        due_date = meta_review_stage.due_date

        for key in additional_fields:
            content[key] = additional_fields[key]

        super(MetaReviewInvitation, self).__init__(id = conference.get_invitation_id(meta_review_stage.name),
            cdate = tools.datetime_millis(start_date),
            duedate = tools.datetime_millis(due_date),
            expdate = tools.datetime_millis(due_date + datetime.timedelta(days = LONG_BUFFER_DAYS)) if due_date else None,
            readers = ['everyone'],
            writers = [conference.id],
            signatures = [conference.id],
            multiReply = False,
            reply = {
                'content': content
            }
        )


class PaperMetaReviewInvitation(openreview.Invitation):

    def __init__(self, conference, note):

        meta_review_stage = conference.meta_review_stage
        readers = meta_review_stage.get_readers(conference, note.number)
        regex = conference.get_program_chairs_id()
        invitees = [conference.get_program_chairs_id()]

        if conference.use_area_chairs:
            regex = conference.get_area_chairs_id(note.number)[:-1] + '[0-9]+'
            invitees = [conference.get_area_chairs_id(number = note.number)]

        super(PaperMetaReviewInvitation, self).__init__(id = conference.get_invitation_id(meta_review_stage.name, note.number),
            super = conference.get_invitation_id(meta_review_stage.name),
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
                }
            }
        )

class DecisionInvitation(openreview.Invitation):

    def __init__(self, conference):
        decision_stage = conference.decision_stage
        start_date = decision_stage.start_date
        due_date = decision_stage.due_date
        content = {
            'title': {
                'order': 1,
                'required': True,
                'value': 'Paper Decision'
            },
            'decision': {
                'order': 2,
                'required': True,
                'value-radio': decision_stage.options,
                'description': 'Decision'
            },
            'comment': {
                'order': 3,
                'required': False,
                'value-regex': '[\\S\\s]{0,5000}',
                'description': ''
            }
        }

        super(DecisionInvitation, self).__init__(id = conference.get_invitation_id(decision_stage.name),
            cdate = tools.datetime_millis(start_date),
            duedate = tools.datetime_millis(due_date),
            expdate = tools.datetime_millis(due_date + datetime.timedelta(minutes = LONG_BUFFER_DAYS)) if due_date else None,
            readers = ['everyone'],
            writers = [conference.id],
            signatures = [conference.id],
            invitees = [conference.get_program_chairs_id()],
            multiReply = False,
            reply = {
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

class PaperDecisionInvitation(openreview.Invitation):

    def __init__(self, conference, note):
        decision_stage = conference.decision_stage

        readers = decision_stage.get_readers(conference, note.number)
        nonreaders = decision_stage.get_nonreaders(conference, note.number)

        super(PaperDecisionInvitation, self).__init__(id = conference.get_invitation_id(decision_stage.name, note.number),
            super = conference.get_invitation_id(decision_stage.name),
            writers = [conference.id],
            signatures = [conference.id],
            reply = {
                'forum': note.id,
                'replyto': note.id,
                'readers': {
                    "description": "Select all user groups that should be able to read this comment.",
                    "values": readers
                },
                'nonreaders': {
                    'values': nonreaders
                }
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

    def set_submission_invitation(self, conference):

        return self.client.post_invitation(SubmissionInvitation(conference))


    def set_blind_submission_invitation(self, conference):

        invitation = BlindSubmissionsInvitation(conference = conference)

        return  self.client.post_invitation(invitation)

    def set_expertise_selection_invitation(self, conference):

        invitation = ExpertiseSelectionInvitation(conference)

        return self.client.post_invitation(invitation)

    def set_bid_invitation(self, conference):

        invitations = []
        invitations.append(self.client.post_invitation(BidInvitation(conference, conference.get_reviewers_id())))
        if conference.use_area_chairs:
            invitations.append(self.client.post_invitation(BidInvitation(conference, conference.get_area_chairs_id())))
        return invitations

    def set_comment_invitation(self, conference, notes):

        invitations = []
        self.client.post_invitation(CommentInvitation(conference))
        for note in notes:
            invitations.append(self.client.post_invitation(OfficialCommentInvitation(conference, note)))

        if conference.comment_stage.allow_public_comments:
            for note in notes:
                invitations.append(self.client.post_invitation(PublicCommentInvitation(conference, note)))

        return invitations

    def set_withdraw_invitation(self, conference):

        invitations = []

        submission_invitation = self.client.get_invitation(id = conference.get_submission_id())
        withdrawn_submission_content = submission_invitation.reply['content']

        self.client.post_invitation(WithdrawnSubmissionInvitation(conference, withdrawn_submission_content))

        notes = list(conference.get_submissions())
        for note in notes:
            invitations.append(self.client.post_invitation(PaperWithdrawInvitation(conference, note)))

        return invitations

    def set_desk_reject_invitation(self, conference):

        invitations = []

        submission_invitation = self.client.get_invitation(id = conference.get_submission_id())
        desk_rejected_submission_content = submission_invitation.reply['content']

        self.client.post_invitation(DeskRejectedSubmissionInvitation(conference, desk_rejected_submission_content))

        notes = list(conference.get_submissions())
        for note in notes:
            invitations.append(self.client.post_invitation(PaperDeskRejectInvitation(conference, note)))

        return invitations

    def set_review_invitation(self, conference, notes):

        invitations = []
        self.client.post_invitation(ReviewInvitation(conference))
        for note in notes:
            invitations.append(self.client.post_invitation(PaperReviewInvitation(conference, note)))

        return invitations

    def set_meta_review_invitation(self, conference, notes):

        invitations = []
        self.client.post_invitation(MetaReviewInvitation(conference))
        for note in notes:
            invitations.append(self.client.post_invitation(PaperMetaReviewInvitation(conference, note)))

        return invitations

    def set_decision_invitation(self, conference, notes):

        invitations = []
        self.client.post_invitation(DecisionInvitation(conference))
        for note in notes:
            invitations.append(self.client.post_invitation(PaperDecisionInvitation(conference, note)))

        return invitations

    def set_revise_submission_invitation(self, conference, notes, name, start_date, due_date, submission_content, additional_fields, remove_fields):

        invitations = []
        readers  = conference.submission_stage.get_readers(conference)
        for note in notes:
            invitations.append(self.client.post_invitation(SubmissionRevisionInvitation(conference, name, note, start_date, due_date, readers, submission_content, additional_fields, remove_fields)))

        return invitations

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
            writers = [conference.get_id()],
            signatures = [conference.get_id()],
            invitees = [conference.get_program_chairs_id(), conference.get_area_chairs_id()],
            multiReply = True,
            reply = {
                'readers': {
                    'description': 'The users who will be allowed to read the above content.',
                    'values-copied': [conference.get_id(), '{signatures}']
                },
                'signatures': {
                    'description': 'How your identity will be displayed with the above content.',
                    'values-regex': '~.*'
                },
                'content': {
                    'head': {
                        'type': 'Note',
                        'query': {
                            'invitation': conference.get_blind_submission_id()
                        }
                    },
                    'tail': {
                        'type': 'Group',
                        'query': {
                            'id': conference.get_reviewers_id()
                        }
                    },
                    'weight': {
                        'value-regex': '[0-9]+',
                        'required': True
                    }
                }
            }
        )

        recommendation_invitation = self.client.post_invitation(recommendation_invitation)



    def set_registration_invitation(self, conference, start_date = None, due_date = None):

        invitees = []
        if conference.use_area_chairs:
            invitees.append(conference.get_area_chairs_id())
        invitees.append(conference.get_reviewers_id())

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
                    "title": {
                        "value": "Reviewer Registration Form"
                    },
                    "Instructions": {
                        "order": 1,
                        "value": "Help us get to know our reviewers better and the ways to make the reviewing process smoother by answering these questions. If you don't see the form below, click on the blue \"Registration\" button.\n\nLink to Profile: https://openreview.net/profile?mode=edit \nLink to Expertise Selection interface: https://openreview.net/invitation?id=ICLR.cc/2020/Conference/-/Expertise_Selection"
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
                "Instructions": "Help us get to know our reviewers better and the ways to make the reviewing process smoother by answering these questions. If you don't see the form below, click on the blue \"Registration\" button.\n\nLink to Profile: https://openreview.net/profile?mode=edit \nLink to Expertise Selection interface: https://openreview.net/invitation?id=ICLR.cc/2020/Conference/-/Expertise_Selection",
                "title": "Reviewer Registration Form"
            }
        ))

        registration_content = {
            'title': {
                'value': conference.get_short_name() + ' Registration',
                'order': 1
            },
            'profile confirmed': {
                'description': 'In order to avoid conflicts of interest in reviewing, we ask that all reviewers take a moment to update their OpenReview profiles (link in instructions above) with their latest information regarding work history and professional relationships. Please confirm that your OpenReview profile is up-to-date by selecting "yes".\n\n',
                'value-radio': ['Yes', 'No'],
                'required': True,
                'order': 2
            },
            'expertise confirmed': {
                'description': 'We will be using OpenReview\'s Expertise System to calculate paper-reviewer affinity scores. Please take a moment to ensure that your latest papers are visible at the Expertise Selection (link in instructions above). Please confirm finishing this step by selecting "yes".\n\n',
                'value-radio': ['Yes', 'No'],
                'required': True,
                'order': 4
            },
            'reviewing experience': {
                'description': 'How many times have you been a reviewer for any conference or journal?',
                'value-radio': [
                    'Never - this is my first time',
                    '1 time - building my reviewer skills',
                    '2-4 times  - comfortable with the reviewing process',
                    '5-10 times  - active community citizen',
                    '10+ times  - seasoned reviewer'
                ],
                'order': 5,
                'required': False
            },
            'previous ICLR author': {
                'description': 'Have you published at ICLR in the last two years?',
                'value-radio': [
                    'Yes',
                    'No'
                ],
                'order': 6,
                'required': False
            },
            'reviewing preferences': {
                'description': 'What is the most important factor of the reviewing process for you? (Choose one)',
                'value-radio': [
                    'Getting papers that best match my area of expertise',
                    'Having the smallest number of papers to review',
                    'Having a long-enough reviewing period (6-8 weeks)',
                    'Having enough time for active discussion about papers.',
                    'Receiving clear instructions about the expectations of reviews.'
                ],
                'order': 7,
                'required': False
            },
            'your recent publication venues': {
                'description': 'Where have you recently published? Select all that apply.',
                'values-dropdown': [
                    'Neural Information Processing Systems (NIPS)',
                    'International Conference on Machine Learning (ICML)',
                    'Artificial Intelligence and Statistics (AISTATS)',
                    'Uncertainty in Artificial Intelligence (UAI)',
                    'Association for Advances in Artificial Intelligence (AAAI)',
                    'Computer Vision and Pattern Recognition (CVPR)',
                    'International Conference on Computer Vision (ICCV)',
                    'International Joint Conference on Artificial Intelligence (IJCAI)',
                    'Robotics: Systems and Science (RSS)',
                    'Conference on Robotics and Learning (CORL)',
                    'Association for Computational Linguistics or related (ACL/NAACL/EACL)',
                    'Empirical Methods in Natural Language Processing (EMNLP)',
                    'Conference on Learning Theory (COLT)',
                    'Algorithmic Learning Theory (ALT)',
                    'Knowledge Discovery and Data Mining (KDD)',
                    'Other'
                ],
                'order': 8,
                'required': False
            }
        }
        if conference.submission_stage.subject_areas:
            registration_content['subject_areas'] = {
                'description': 'To properly assign papers to reviewers, we ask that reviewers provide their areas of expertise from among the provided list of subject areas. Please submit your areas of expertise by selecting the appropriate options from the "Subject Areas" list.\n\n',
                'values-dropdown': conference.submission_stage.subject_areas,
                'order': 3,
                'required': False
            }

        registration_invitation = self.client.post_invitation(openreview.Invitation(
            id = conference.get_registration_id(),
            cdate = tools.datetime_millis(start_date) if start_date else None,
            duedate = tools.datetime_millis(due_date) if due_date else None,
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
                'content': registration_content
            }
        ))

        return self.client.post_invitation(registration_invitation)

