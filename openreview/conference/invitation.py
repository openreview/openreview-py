from __future__ import absolute_import

import os
import json
import datetime
import openreview
from tqdm import tqdm
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

    def __init__(self, conference, hide_fields):

        content = {
            'authors': {
                'values': ['Anonymous']
            },
            'authorids': {
                'values-regex': '.*'
            }
        }
        for field in hide_fields:
            content[field] = {
                'value-regex': '.*'
            }

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
                'content': content
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
    def __init__(self, conference, match_group_id, request_count):

        bid_stage = conference.bid_stage

        readers = [
            conference.get_id(),
            conference.get_program_chairs_id(),
            conference.get_area_chairs_id(),
            match_group_id
        ]

        invitees = [match_group_id]

        values_copied = [conference.get_id()]
        if match_group_id == conference.get_reviewers_id():
            values_copied.append(conference.get_area_chairs_id())
        values_copied.append('{signatures}')

        super(BidInvitation, self).__init__(id = conference.get_bid_id(match_group_id),
            cdate = tools.datetime_millis(bid_stage.start_date),
            duedate = tools.datetime_millis(bid_stage.due_date),
            expdate = tools.datetime_millis(bid_stage.due_date + datetime.timedelta(minutes = SHORT_BUFFER_MIN)) if bid_stage.due_date else None,
            readers = readers,
            writers = [conference.get_id()],
            signatures = [conference.get_id()],
            invitees = invitees,
            taskCompletionCount = request_count,
            reply = {
                'readers': {
                    'values-copied': values_copied
                },
                'nonreaders': {
                    'values-regex': conference.get_authors_id(number='.*')
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
                        'type': 'Profile',
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
            expdate = tools.datetime_millis(expertise_selection_stage.due_date + datetime.timedelta(days = LONG_BUFFER_DAYS)) if expertise_selection_stage.due_date else None,
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
                        'type': 'Profile'
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

    def __init__(self, conference, reveal_authors, reveal_submission):

        content = {
            'authorids': {
                'values-regex': '.*',
                'required': False,
                'order': 3
            },
            'authors': {
                'values-regex': '[^;,\\n]+(,[^,\\n]+)*',
                'required': False,
                'order': 2
            }
        }

        if (conference.submission_stage.double_blind and not reveal_authors):
            content['authors'] = {
                'values': ['Anonymous']
            }
            content['authorids'] = {
                'values-regex': '.*'
            }

        if reveal_submission:
            readers = {
                'values': ['everyone']
            }
        else:
            readers = {
                'values-regex': '.*'
            }

        super(WithdrawnSubmissionInvitation, self).__init__(
            id=conference.submission_stage.get_withdrawn_submission_id(conference),
            cdate=tools.datetime_millis(conference.submission_stage.due_date) if conference.submission_stage.due_date else None,
            readers=['everyone'],
            writers=[conference.get_id()],
            signatures=[conference.get_id()],
            reply={
                'forum': None,
                'replyto': None,
                'readers': readers,
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

    def __init__(self, conference, note, reveal_authors, reveal_submission, email_pcs):

        content = invitations.withdraw.copy()

        withdraw_process_file = 'templates/withdraw_process.py'


        if reveal_submission:
            readers = {
                'description': 'User groups that will be able to read this withdraw note.',
                'values': ['everyone']
            }
        else:
            readers = {
                'values': conference.get_committee(with_authors=True, number=note.number)
            }

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
            file_content = file_content.replace(
                'CONFERENCE_NAME = \'\'',
                'CONFERENCE_NAME = \'' + conference.get_name() + '\'')
            file_content = file_content.replace(
                'CONFERENCE_YEAR = \'\'',
                'CONFERENCE_YEAR = \'' + str(conference.get_year()) + '\'')
            if email_pcs:
                file_content = file_content.replace(
                    'EMAIL_PROGRAM_CHAIRS = False',
                    'EMAIL_PROGRAM_CHAIRS = True')
            if reveal_authors:
                file_content = file_content.replace(
                    'REVEAL_AUTHORS_ON_WITHDRAW = False',
                    'REVEAL_AUTHORS_ON_WITHDRAW = True')
            if reveal_submission:
                file_content = file_content.replace(
                    'REVEAL_SUBMISSIONS_ON_WITHDRAW = False',
                    'REVEAL_SUBMISSIONS_ON_WITHDRAW = True')

            super(PaperWithdrawInvitation, self).__init__(
                id=conference.get_invitation_id('Withdraw', note.number),
                cdate=tools.datetime_millis(conference.submission_stage.due_date) if conference.submission_stage.due_date else None,
                duedate = None,
                expdate = tools.datetime_millis(conference.submission_stage.due_date + datetime.timedelta(days = 90)) if conference.submission_stage.due_date else None,
                invitees=[conference.get_authors_id(note.number)],
                readers=['everyone'],
                writers=[conference.get_id()],
                signatures=['~Super_User1'],
                multiReply=False,
                reply={
                    'forum': note.id,
                    'replyto': note.id,
                    'readers': readers,
                    'writers': {
                        'values-copied': [
                            conference.get_id(),
                            '{signatures}'
                        ]
                    },
                    'signatures': {
                        'values': [conference.get_authors_id(note.number)],
                        'description': 'How your identity will be displayed.'
                    },
                    'content': content
                },
                process_string=file_content
            )

class DeskRejectedSubmissionInvitation(openreview.Invitation):

    def __init__(self, conference, reveal_authors, reveal_submission):

        content = {
            'authorids': {
                'values-regex': '.*',
                'required': False,
                'order': 3
            },
            'authors': {
                'values-regex': '[^;,\\n]+(,[^,\\n]+)*',
                'required': False,
                'order': 2
            }
        }

        if (conference.submission_stage.double_blind and not reveal_authors):
            content['authors'] = {
                'values': ['Anonymous']
            }
            content['authorids'] = {
                'values-regex': '.*'
            }

        if reveal_submission:
            readers = {
                'values': ['everyone']
            }
        else:
            readers = {
                'values-regex': '.*'
            }

        super(DeskRejectedSubmissionInvitation, self).__init__(
            id=conference.submission_stage.get_desk_rejected_submission_id(conference),
            cdate=tools.datetime_millis(conference.submission_stage.due_date) if conference.submission_stage.due_date else None,
            readers=['everyone'],
            writers=[conference.get_id()],
            signatures=[conference.get_id()],
            reply={
                'forum': None,
                'replyto': None,
                'readers': readers,
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

    def __init__(self, conference, note, reveal_authors, reveal_submission):

        content = invitations.desk_reject.copy()

        desk_reject_process_file = 'templates/desk_reject_process.py'


        if reveal_submission:
            readers = {
                'description': 'User groups that will be able to read this withdraw note.',
                'values': ['everyone']
            }
        else:
            readers = {
                'values': conference.get_committee(with_authors=True, number=note.number)
            }

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
            file_content = file_content.replace(
                'CONFERENCE_NAME = \'\'',
                'CONFERENCE_NAME = \'' + conference.get_name() + '\'')
            file_content = file_content.replace(
                'CONFERENCE_YEAR = \'\'',
                'CONFERENCE_YEAR = \'' + str(conference.get_year()) + '\'')
            if reveal_authors:
                file_content = file_content.replace(
                    'REVEAL_AUTHORS_ON_DESK_REJECT = False',
                    'REVEAL_AUTHORS_ON_DESK_REJECT = True')
            if reveal_submission:
                file_content = file_content.replace(
                    'REVEAL_SUBMISSIONS_ON_DESK_REJECT = False',
                    'REVEAL_SUBMISSIONS_ON_DESK_REJECT = True')

            super(PaperDeskRejectInvitation, self).__init__(
                id=conference.get_invitation_id('Desk_Reject', note.number),
                cdate=tools.datetime_millis(conference.submission_stage.due_date) if conference.submission_stage.due_date else None,
                duedate = None,
                expdate = tools.datetime_millis(conference.submission_stage.due_date + datetime.timedelta(days = 90)) if conference.submission_stage.due_date else None,
                invitees=[conference.get_program_chairs_id()],
                readers=['everyone'],
                writers=[conference.get_id()],
                signatures=['~Super_User1'],
                multiReply=False,
                reply={
                    'forum': note.id,
                    'replyto': note.id,
                    'readers': readers,
                    'writers': {
                        'values-copied': [
                            conference.get_id(),
                            '{signatures}'
                        ]
                    },
                    'signatures': {
                        'values': [conference.get_program_chairs_id()],
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
                    'description': 'User groups that will be able to read this comment.',
                    'values': ['everyone']
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
        invitees = conference.get_committee(number=note.number, with_authors=comment_stage.authors)
        if comment_stage.allow_public_comments:
            readers.append('everyone')

        readers.append(conference.get_program_chairs_id())

        if conference.use_area_chairs:
            readers.append(conference.get_area_chairs_id(note.number))

        if comment_stage.unsubmitted_reviewers:
            readers.append(conference.get_reviewers_id(note.number))
        else:
            readers.append(conference.get_reviewers_id(note.number) + '/Submitted')

        if comment_stage.reader_selection:
            readers.append(conference.get_reviewers_id(note.number).replace('Reviewers', 'AnonReviewer.*'))

        if comment_stage.authors:
            readers.append(conference.get_authors_id(note.number))

        if comment_stage.reader_selection:
            reply_readers = {
                'description': 'Who your comment will be visible to. If replying to a specific person make sure to add the group they are a member of so that they are able to see your response',
                'values-dropdown': readers,
                'default': [conference.get_program_chairs_id()]
            }
        else:
            reply_readers = {
                'description': 'User groups that will be able to read this comment.',
                'values': readers
            }

        super(OfficialCommentInvitation, self).__init__(id = conference.get_invitation_id(comment_stage.official_comment_name, note.number),
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

        reply = {
            'forum': note.id,
            'replyto': note.id,
            'readers': {
                'description': 'Select all user groups that should be able to read this comment.',
                'values': readers
            },
            'nonreaders': {
                'values': nonreaders
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

        has_copies = [r for r in readers if r.startswith('{') and r.endswith('}')]
        if has_copies:
            reply['readers'] = {
                'description': 'Select all user groups that should be able to read this comment.',
                'values-copied': readers
            }

        super(PaperReviewInvitation, self).__init__(id = conference.get_invitation_id(review_stage.name, note.number),
            super = conference.get_invitation_id(review_stage.name),
            writers = [conference.id],
            signatures = [conference.id],
            invitees = [conference.get_reviewers_id(number = note.number)],
            reply = reply
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
                expdate = tools.datetime_millis(due_date + datetime.timedelta(days = LONG_BUFFER_DAYS)) if due_date else None,
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
        process = meta_review_stage.process

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
            },
            process_string = process
        )


class PaperMetaReviewInvitation(openreview.Invitation):

    def __init__(self, conference, note):

        meta_review_stage = conference.meta_review_stage
        readers = meta_review_stage.get_readers(conference, note.number)
        regex = conference.get_program_chairs_id()
        invitees = [conference.get_program_chairs_id()]
        writers = [conference.get_program_chairs_id()]

        if conference.use_area_chairs:
            paper_area_chair = conference.get_area_chairs_id(number = note.number)
            regex = regex + '|' + paper_area_chair[:-1] + '[0-9]+'
            invitees = [paper_area_chair]
            writers.append(paper_area_chair)

        super(PaperMetaReviewInvitation, self).__init__(
            id = conference.get_invitation_id(meta_review_stage.name, note.number),
            super = conference.get_invitation_id(meta_review_stage.name),
            writers = [conference.id],
            signatures = [conference.id],
            invitees = invitees,
            noninvitees = [conference.get_authors_id(number = note.number), conference.id + '/Paper'+ str(note.number) + '/Secondary_Area_Chair'],
            reply = {
                'forum': note.id,
                'replyto': note.id,
                'readers': {
                    "description": "Select all user groups that should be able to read this comment.",
                    "values": readers
                },
                'writers': {
                    'values': writers,
                    'description': 'Who can edit this meta-review.'
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
            expdate = tools.datetime_millis(due_date + datetime.timedelta(days = LONG_BUFFER_DAYS)) if due_date else None,
            readers = ['everyone'],
            writers = [conference.id],
            signatures = [conference.id],
            invitees = [conference.get_program_chairs_id()],
            multiReply = False,
            reply = {
                'writers': {
                    'values': [conference.get_program_chairs_id()],
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

    def __update_readers(self, invitation):
        ## Update readers of current notes
        notes = self.client.get_notes(invitation=invitation.id)

        for note in notes:
            if 'values' in invitation.reply['readers'] and note.readers != invitation.reply['readers']['values']:
                note.readers = invitation.reply['readers']['values']
                if 'nonreaders' in invitation.reply:
                    note.nonreaders = invitation.reply['nonreaders']['values']
                self.client.post_note(note)

    def set_submission_invitation(self, conference):

        return self.client.post_invitation(SubmissionInvitation(conference))


    def set_blind_submission_invitation(self, conference, hide_fields):

        invitation = BlindSubmissionsInvitation(conference = conference, hide_fields=hide_fields)

        return  self.client.post_invitation(invitation)

    def set_expertise_selection_invitation(self, conference):

        invitation = ExpertiseSelectionInvitation(conference)

        return self.client.post_invitation(invitation)

    def set_bid_invitation(self, conference):

        invitations = []
        invitations.append(self.client.post_invitation(BidInvitation(conference, conference.get_reviewers_id(), conference.bid_stage.request_count)))
        if conference.use_area_chairs:
            invitations.append(self.client.post_invitation(BidInvitation(conference, conference.get_area_chairs_id(), conference.bid_stage.ac_request_count)))
        return invitations

    def set_comment_invitation(self, conference, notes):

        invitations = []
        self.client.post_invitation(CommentInvitation(conference))
        for note in tqdm(notes, total=len(notes)):
            invitations.append(self.client.post_invitation(OfficialCommentInvitation(conference, note)))

        if conference.comment_stage.allow_public_comments:
            for note in tqdm(notes, total=len(notes)):
                invitations.append(self.client.post_invitation(PublicCommentInvitation(conference, note)))

        return invitations

    def set_withdraw_invitation(self, conference, reveal_authors, reveal_submission, email_pcs):

        invitations = []

        self.client.post_invitation(WithdrawnSubmissionInvitation(conference, reveal_authors, reveal_submission))

        notes = list(conference.get_submissions())
        for note in notes:
            invitations.append(self.client.post_invitation(PaperWithdrawInvitation(conference, note, reveal_authors, reveal_submission, email_pcs)))

        return invitations

    def set_desk_reject_invitation(self, conference, reveal_authors, reveal_submission):

        invitations = []

        self.client.post_invitation(DeskRejectedSubmissionInvitation(conference, reveal_authors, reveal_submission))

        notes = list(conference.get_submissions())
        for note in notes:
            invitations.append(self.client.post_invitation(PaperDeskRejectInvitation(conference, note, reveal_authors, reveal_submission)))

        return invitations

    def set_review_invitation(self, conference, notes):
        invitations = []
        self.client.post_invitation(ReviewInvitation(conference))
        for note in tqdm(notes, total=len(notes)):
            invitation = self.client.post_invitation(PaperReviewInvitation(conference, note))
            self.__update_readers(invitation)
            invitations.append(invitation)

        return invitations

    def set_meta_review_invitation(self, conference, notes):

        invitations = []
        self.client.post_invitation(MetaReviewInvitation(conference))
        for note in notes:
            invitation = self.client.post_invitation(PaperMetaReviewInvitation(conference, note))
            self.__update_readers(invitation)
            invitations.append(invitation)

        return invitations

    def set_decision_invitation(self, conference, notes):

        invitations = []
        self.client.post_invitation(DecisionInvitation(conference))
        for note in notes:
            invitation = self.client.post_invitation(PaperDecisionInvitation(conference, note))
            self.__update_readers(invitation)
            invitations.append(invitation)

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

    def set_reviewer_reduced_load_invitation(self, conference, options = {}):

        reduced_load_invitation_reply = {
            'forum': None,
            'replyto': None,
            'readers': {
                'values-copied': [
                    conference.get_id(),
                    '{content.user}'
                ]
            },
            'writers': {
                'values-copied': [
                    conference.get_id()
                ]
            },
            'signatures': {
                'values-regex': '\\(anonymous\\)|~.*'
            },
            'content': {
                'user': {
                    'description': 'Email address or OpenReview Profile Id',
                    'order': 1,
                    'value-regex': '.*',
                    'required': True
                },
                'key': {
                    'description': 'Email key hash',
                    'order': 2,
                    'value-regex': '.{0,100}',
                    'required': True
                },
                'response': {
                    'required': True,
                    'description': 'Please select a reviewer load to confirm your acceptance of the invitation.',
                    'value': 'Yes',
                    'order': 3
                },
                'reviewer_load': {
                    'description': 'Please select the number of submissions that you would be comfortable reviewing.',
                    'required': True,
                    'value-dropdown': options.get('reduced_load_on_decline', []),
                    'order': 4
                }
            }
        }

        with open(os.path.join(os.path.dirname(__file__), 'templates/recruitReducedLoadProcess.js')) as f:
            content = f.read()
            content = content.replace("var SHORT_PHRASE = '';", "var SHORT_PHRASE = '" + conference.get_short_name() + "';")
            content = content.replace("var REVIEWER_NAME = '';", "var REVIEWER_NAME = '" + options.get('reviewers_name', 'Reviewers').replace('_', ' ')[:-1] + "';")
            content = content.replace("var REVIEWERS_ACCEPTED_ID = '';", "var REVIEWERS_ACCEPTED_ID = '" + options.get('reviewers_accepted_id') + "';")
            content = content.replace("var REVIEWERS_DECLINED_ID = '';", "var REVIEWERS_DECLINED_ID = '" + options.get('reviewers_declined_id') + "';")
            content = content.replace("var HASH_SEED = '';", "var HASH_SEED = '" + options.get('hash_seed') + "';")

            reduced_load_invitation = openreview.Invitation(
                    id = conference.get_invitation_id('Reduced_Load'),
                    duedate = tools.datetime_millis(options.get('due_date', datetime.datetime.utcnow())),
                    readers = ['everyone'],
                    nonreaders = [],
                    invitees = ['everyone'],
                    noninvitees = [],
                    writers = [conference.get_id()],
                    signatures = [conference.get_id()],
                    reply = reduced_load_invitation_reply,
                    process_string = content)
            return self.client.post_invitation(reduced_load_invitation)

    def set_reviewer_recruiter_invitation(self, conference, options = {}):

        default_reply = {
            'forum': None,
            'replyto': None,
            'readers': {
                'values': [conference.get_id()]
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
            content = content.replace("var SHORT_PHRASE = '';", "var SHORT_PHRASE = '" + conference.get_short_name() + "';")
            content = content.replace("var CONFERENCE_NAME = '';", "var CONFERENCE_NAME = '" + conference.get_id() + "';")
            content = content.replace("var REVIEWER_NAME = '';", "var REVIEWER_NAME = '" + options.get('reviewers_name', 'Reviewers').replace('_', ' ')[:-1] + "';")
            content = content.replace("var REVIEWERS_ACCEPTED_ID = '';", "var REVIEWERS_ACCEPTED_ID = '" + options.get('reviewers_accepted_id') + "';")
            content = content.replace("var REVIEWERS_DECLINED_ID = '';", "var REVIEWERS_DECLINED_ID = '" + options.get('reviewers_declined_id') + "';")
            content = content.replace("var HASH_SEED = '';", "var HASH_SEED = '" + options.get('hash_seed') + "';")
            if conference.reduced_load_on_decline and options.get('reviewers_name', '') == 'Reviewers':
                content = content.replace("var REDUCED_LOAD_INVITATION_NAME = '';", "var REDUCED_LOAD_INVITATION_NAME = 'Reduced_Load';")
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

    def set_recommendation_invitation(self, conference, start_date, due_date, total_recommendations):

        recommendation_invitation = openreview.Invitation(
            id = conference.get_recommendation_id(),
            cdate = tools.datetime_millis(start_date),
            duedate = tools.datetime_millis(due_date),
            expdate = tools.datetime_millis(due_date + datetime.timedelta(minutes = SHORT_BUFFER_MIN)) if due_date else None,
            readers = [conference.get_program_chairs_id(), conference.get_area_chairs_id()],
            writers = [conference.get_id()],
            signatures = [conference.get_id()],
            invitees = [conference.get_program_chairs_id(), conference.get_area_chairs_id()],
            multiReply = True,
            taskCompletionCount = total_recommendations,
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
                        },
                        'required': True
                    },
                    'tail': {
                        'type': 'Profile',
                        'query': {
                            'group': conference.get_reviewers_id()
                        },
                        'required': True,
                        'description': 'Create an ordered ranking of reviewers by selecting values from the dropdowns (10 = best)'
                    },
                    'weight': {
                        'value-dropdown': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
                        'required': True
                    }
                }
            }
        )

        return self.client.post_invitation(recommendation_invitation)

    def set_paper_ranking_invitation(self, conference, group_id, start_date, due_date):

        reviewer_paper_ranking_invitation = openreview.Invitation(
            id = conference.get_invitation_id('Paper_Ranking', prefix=group_id),
            cdate = tools.datetime_millis(start_date),
            duedate = tools.datetime_millis(due_date),
            expdate = tools.datetime_millis(due_date + datetime.timedelta(minutes = SHORT_BUFFER_MIN)) if due_date else None,
            readers = [conference.get_program_chairs_id(), group_id],
            writers = [conference.get_id()],
            signatures = [conference.get_id()],
            invitees = [conference.get_program_chairs_id(), group_id],
            multiReply = True,
            reply = {
                "invitation": conference.get_submission_id(),
                'readers': {
                    'description': 'The users who will be allowed to read the above content.',
                    'values-copied': [conference.get_id(), '{signatures}']
                },
                'signatures': {
                    'description': 'How your identity will be displayed with the above content.',
                    'values-regex': '~.*'
                },
                'content': {
                    "tag": {
                        "description": "Select value",
                        "order": 1,
                        "value-dropdown": ['No Ranking'] + [str(e) for e in list(range(1, 31))],
                        "required": True
                    }
                }
            }
        )

        return self.client.post_invitation(reviewer_paper_ranking_invitation)

    def __set_registration_invitation(self, conference, start_date, due_date, additional_fields, instructions, committee_id, committee_name):

        invitees = [committee_id]
        readers = [conference.id, committee_id]

        # Create super invitation with a webfield
        registration_parent_invitation = openreview.Invitation(
            id = conference.get_invitation_id(name='Form', prefix=committee_id),
            readers = ['everyone'],
            writers = [conference.get_id()],
            signatures = [conference.get_id()],
            invitees = invitees,
            reply = {
                'forum': None,
                'replyto': None,
                'readers': {'values': readers},
                'writers': {'values': [conference.get_id()]},
                'signatures': {'values': [conference.get_id()]},
                'content': {
                    'title': {
                        'value': committee_name[:-1] + ' Information'
                    },
                    'instructions': {
                        'order': 1,
                        'value': instructions
                    }
                }
            }
        )

        registration_parent_invitation = self.client.post_invitation(registration_parent_invitation)

        registration_parent = self.client.post_note(openreview.Note(
            invitation = registration_parent_invitation.id,
            readers = readers,
            writers = [conference.get_id()],
            signatures = [conference.get_id()],
            replyto = None,
            forum = None,
            content = {
                'instructions': instructions,
                'title': committee_name[:-1] + ' Information'
            }
        ))

        registration_content = {
            'profile_confirmed': {
                'description': 'In order to avoid conflicts of interest in reviewing, we ask that all reviewers take a moment to update their OpenReview profiles (link in instructions above) with their latest information regarding email addresses, work history and professional relationships. Please confirm that your OpenReview profile is up-to-date by selecting "Yes".\n\n',
                'value-checkbox': 'Yes',
                'required': True,
                'order': 1
            },
            'expertise_confirmed': {
                'description': 'We will be using OpenReview\'s Expertise System as a factor in calculating paper-reviewer affinity scores. Please take a moment to ensure that your latest papers are visible at the Expertise Selection (link in instructions above). Please confirm finishing this step by selecting "Yes".\n\n',
                'value-checkbox': 'Yes',
                'required': True,
                'order': 2
            }
        }
        if conference.submission_stage.subject_areas:
            registration_content['subject_areas'] = {
                'description': 'To properly assign papers to reviewers, we ask that reviewers provide their areas of expertise from among the provided list of subject areas. Please submit your areas of expertise by selecting the appropriate options from the "Subject Areas" list.\n\n',
                'values-dropdown': conference.submission_stage.subject_areas,
                'order': 3,
                'required': False
            }

        for content_key in additional_fields:
            registration_content[content_key] = additional_fields[content_key]

        registration_invitation = self.client.post_invitation(openreview.Invitation(
            id = conference.get_registration_id(committee_id),
            cdate = tools.datetime_millis(start_date) if start_date else None,
            duedate = tools.datetime_millis(due_date) if due_date else None,
            expdate = tools.datetime_millis(due_date),
            multiReply = False,
            readers = readers,
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

        return registration_invitation

    def set_registration_invitation(self, conference):

        invitations = []
        stage=conference.registration_stage
        if conference.has_area_chairs:
            invitations.append(self.__set_registration_invitation(conference=conference,
            start_date=stage.start_date,
            due_date=stage.due_date,
            additional_fields=stage.ac_additional_fields,
            instructions=stage.ac_instructions,
            committee_id=conference.get_area_chairs_id(),
            committee_name=conference.get_area_chairs_name()))

        invitations.append(self.__set_registration_invitation(conference=conference,
        start_date=stage.start_date,
        due_date=stage.due_date,
        additional_fields=stage.additional_fields,
        instructions=stage.instructions,
        committee_id=conference.get_reviewers_id(),
        committee_name=conference.get_reviewers_name()))

        return invitations
