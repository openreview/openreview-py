from __future__ import absolute_import

import os
import json
import datetime
import re
import openreview
from tqdm import tqdm
from openreview.stages import *
from .. import tools

SHORT_BUFFER_MIN = 30
LONG_BUFFER_DAYS = 10

class SubmissionInvitation(openreview.Invitation):

    def __init__(self, conference, under_submission):

        readers = {}
        submission_stage = conference.submission_stage
        start_date = submission_stage.start_date
        due_date = submission_stage.due_date
        readers = submission_stage.get_invitation_readers(conference, under_submission)

        content = submission_stage.get_content()
        file_content = ''

        if under_submission:
            with open(os.path.join(os.path.dirname(__file__), 'templates/submission_process.py')) as f:
                file_content = f.read()
                file_content = file_content.replace("SHORT_PHRASE = ''", f'SHORT_PHRASE = "{conference.get_short_name()}"')
                file_content = file_content.replace("CONFERENCE_ID = ''",f'CONFERENCE_ID = "{conference.get_id()}"')
                if submission_stage.email_pcs:
                    file_content = file_content.replace("PROGRAM_CHAIRS_ID = ''", "PROGRAM_CHAIRS_ID = '" + conference.get_program_chairs_id() + "'")
                if submission_stage.create_groups:
                    file_content = file_content.replace("CREATE_GROUPS = False", "CREATE_GROUPS = True")
                    # Only supported for public reviews
                    if submission_stage.create_review_invitation:
                        file_content = file_content.replace("OFFICIAL_REVIEW_NAME = ''", "OFFICIAL_REVIEW_NAME = '" + conference.review_stage.name + "'")
                        file_content = file_content.replace("ANON_IDS = False", "ANON_IDS = True")
                        file_content = file_content.replace("DEANONYMIZERS = []", "DEANONYMIZERS = " + json.dumps(conference.get_reviewer_identity_readers('{number}')))

                if conference.use_area_chairs:
                    file_content = file_content.replace("AREA_CHAIRS_ID = ''", "AREA_CHAIRS_ID = '" + conference.get_area_chairs_id() + "'")

                if submission_stage.submission_email:
                    email_template = submission_stage.submission_email
                    email_template = email_template.replace('{{Abbreviated_Venue_Name}}', conference.get_short_name())
                    email_template = email_template.replace('{{action}}', '{action}')
                    email_template = email_template.replace('{{note_title}}', '{note.content[\'title\']}')
                    email_template = email_template.replace('{{note_abstract}}', '{note_abstract}')
                    email_template = email_template.replace('{{note_number}}', '{note.number}')
                    email_template = email_template.replace('{{note_forum}}', '{note.forum}')
                    file_content = file_content.replace("SUBMISSION_EMAIL = ''", "SUBMISSION_EMAIL = f'''" + email_template + "'''")

        else:
            post_submission_deadline_process_file = 'templates/post_submission_deadline_process.py'

            with open(os.path.join(os.path.dirname(__file__), post_submission_deadline_process_file)) as f:
                file_content = f.read()

                file_content = file_content.replace(
                    'CONFERENCE_ID = \'\'',
                    'CONFERENCE_ID = \'' + conference.get_id() + '\'')
                file_content = file_content.replace(
                    'AUTHORS_NAME = \'\'', 'AUTHORS_NAME = \'' + conference.authors_name + '\'')


        super(SubmissionInvitation, self).__init__(id = conference.get_submission_id(),
            cdate = tools.datetime_millis(start_date),
            duedate = tools.datetime_millis(due_date),
            expdate = tools.datetime_millis(due_date + datetime.timedelta(minutes = SHORT_BUFFER_MIN)) if due_date else None,
            readers = ['everyone'],
            writers = [conference.get_id()],
            signatures = [conference.get_id()],
            invitees = ['~', conference.support_user],
            reply = {
                'forum': None,
                'replyto': None,
                'readers': readers,
                'writers': submission_stage.get_invitation_writers(conference),
                'signatures': {
                    'values-regex': '~.*'
                },
                'content': content
            },
            process_string = file_content
        )


class BlindSubmissionsInvitation(openreview.Invitation):

    def __init__(self, conference, hide_fields):

        submission_stage = conference.submission_stage
        original_content = submission_stage.get_content()

        content = {}

        for key in original_content:
            if key == 'authors':
                content[key] = {
                    'values': ['Anonymous'],
                    'order': original_content[key]['order']
                    }
            elif key == 'authorids':
                content[key] = {
                    'values-regex': '.*',
                    'order': original_content[key]['order']
                    }
            else:
                content[key] = {
                    'value-regex': '.*',
                    'order': original_content[key]['order']
                }

        for field in hide_fields:
            if field not in content:
                content[field] = {
                    'value-regex': '.*'
                }

        super(BlindSubmissionsInvitation, self).__init__(id = conference.get_blind_submission_id(),
            readers = ['everyone'],
            writers = [conference.get_id()],
            signatures = [conference.get_id()],
            invitees = ['~', conference.support_user],
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


class BidInvitation(openreview.Invitation):
    def __init__(self, conference, bid_stage, current_invitation):

        match_group_id = bid_stage.committee_id

        invitation_readers = bid_stage.get_invitation_readers(conference)

        invitees = [match_group_id, conference.support_user]

        bid_readers = bid_stage.get_readers(conference)
        head = {
            'type': 'Note',
            'query' : {
                'invitation' : conference.get_blind_submission_id()
            },
            'required': True
        }
        if match_group_id == conference.get_senior_area_chairs_id():
            head = {
            'type': 'Profile',
            'query' : {
                'group' : conference.get_area_chairs_id()
            },
            'required': True
        }

        super(BidInvitation, self).__init__(id = conference.get_bid_id(match_group_id),
            cdate = tools.datetime_millis(bid_stage.start_date),
            duedate = tools.datetime_millis(bid_stage.due_date),
            expdate = tools.datetime_millis(bid_stage.due_date + datetime.timedelta(minutes = SHORT_BUFFER_MIN)) if bid_stage.due_date else None,
            readers = invitation_readers,
            writers = [conference.get_id()],
            signatures = [conference.get_id()],
            invitees = invitees,
            taskCompletionCount = bid_stage.request_count,
            multiReply = False,
            reply = {
                'readers': {
                    'values-copied': bid_readers
                },
                'writers': {
                    'values-copied': [conference.get_id(), '{signatures}']
                },
                'nonreaders': {
                    'values-regex': conference.get_authors_id(number='.*')
                },
                'signatures': {
                    'values-regex': '~.*'
                },
                'content': {
                    'head': head,
                    'tail': {
                        'type': 'Profile',
                        'query' : {
                            'group' : match_group_id
                        },
                        'required': True
                    },
                    'label': {
                        'value-radio': bid_stage.get_bid_options(),
                        'required': True
                    }
                }
            },
            web_string = current_invitation.web if current_invitation else None
        )

class ExpertiseSelectionInvitation(openreview.Invitation):
    def __init__(self, conference, current_invitation):

        expertise_selection_stage = conference.expertise_selection_stage

        readers = [
            conference.get_id(),
            conference.get_program_chairs_id(),
            conference.get_reviewers_id()
        ]

        invitees = [conference.get_reviewers_id(), conference.support_user]
        if conference.use_area_chairs:
            readers.append(conference.get_area_chairs_id())
            invitees.append(conference.get_area_chairs_id())

        if conference.use_senior_area_chairs:
            readers.append(conference.get_senior_area_chairs_id())
            invitees.append(conference.get_senior_area_chairs_id())

        super(ExpertiseSelectionInvitation, self).__init__(id = conference.get_expertise_selection_id(),
            cdate = tools.datetime_millis(expertise_selection_stage.start_date),
            duedate = tools.datetime_millis(expertise_selection_stage.due_date),
            expdate = tools.datetime_millis(expertise_selection_stage.due_date + datetime.timedelta(days = LONG_BUFFER_DAYS)) if expertise_selection_stage.due_date else None,
            readers = readers,
            writers = [conference.get_id()],
            signatures = [conference.get_id()],
            invitees = invitees,
            multiReply = True,
            taskCompletionCount = 1,
            reply = {
                'readers': {
                    'values-copied': [conference.get_id(), '{signatures}']
                },
                'writers': {
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
                        'value-radio': ['Include' if expertise_selection_stage.include_option else 'Exclude'],
                        'required': True
                    }
                }
            },
            web_string = current_invitation.web if current_invitation else None
        )

class CommentInvitation(openreview.Invitation):

    def __init__(self, conference):

        content = default_content.comment.copy()

        with open(os.path.join(os.path.dirname(__file__), 'templates/commentProcess.js')) as f:
            with open(os.path.join(os.path.dirname(__file__), 'templates/comment_pre_process.py')) as g:
                post_content = f.read()
                pre_content = g.read()
                mandatory_readers = [conference.get_program_chairs_id()]
                if conference.use_senior_area_chairs:
                    mandatory_readers.append(conference.get_senior_area_chairs_id(number='{number}'))

                pre_content = pre_content.replace("MANDATORY_READERS = []", "MANDATORY_READERS = " + json.dumps(mandatory_readers))
                post_content = post_content.replace("var CONFERENCE_ID = '';", "var CONFERENCE_ID = '" + conference.id + "';")
                post_content = post_content.replace("var SHORT_PHRASE = '';", f'var SHORT_PHRASE = "{conference.get_short_name()}";')
                post_content = post_content.replace("var AUTHORS_NAME = '';", "var AUTHORS_NAME = '" + conference.authors_name + "';")
                post_content = post_content.replace("var REVIEWERS_NAME = '';", "var REVIEWERS_NAME = '" + conference.reviewers_name + "';")
                post_content = post_content.replace("var AREA_CHAIRS_NAME = '';", "var AREA_CHAIRS_NAME = '" + conference.area_chairs_name + "';")
                post_content = post_content.replace("var PROGRAM_CHAIRS_ID = '';", "var PROGRAM_CHAIRS_ID = '" + conference.get_program_chairs_id() + "';")

                if conference.use_area_chairs:
                    post_content = post_content.replace("var USE_AREA_CHAIRS = false;", "var USE_AREA_CHAIRS = true;")

                if conference.use_senior_area_chairs:
                    post_content = post_content.replace("var SENIOR_AREA_CHAIRS_NAME = '';", "var SENIOR_AREA_CHAIRS_NAME = '" + conference.senior_area_chairs_name + "';")

                if conference.comment_stage.email_pcs:
                    post_content = post_content.replace("var EMAIL_PCs = false;", "var EMAIL_PCs = true;")

                super(CommentInvitation, self).__init__(
                    id = conference.get_invitation_id('Comment'),
                    cdate = tools.datetime_millis(conference.comment_stage.start_date),
                    expdate = tools.datetime_millis(conference.comment_stage.end_date) if conference.comment_stage.end_date else None,
                    readers = ['everyone'],
                    writers = [conference.get_id()],
                    signatures = [conference.get_id()],
                    reply = {
                        'content': content
                    },
                    process_string = post_content,
                    preprocess=pre_content if conference.comment_stage.check_mandatory_readers and conference.comment_stage.reader_selection else None
                )


class WithdrawnSubmissionInvitation(openreview.Invitation):

    def __init__(self, conference, reveal_authors, reveal_submission, hide_fields=[]):

        signatures = {'values-regex': '~.*'}
        writers = {'values-regex': '.*'}
        content = {}
        if conference.submission_stage.double_blind:
            signatures = {'values': [conference.get_id()]}
            writers = {'values': [conference.get_id()]}
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
                },
            }
            if not reveal_authors:
                content['authors'] = {'values': ['Anonymous']}
                content['authorids'] = {'values-regex': '.*'}
            for field in hide_fields:
                content[field] = {
                    'value-regex': '.*',
                    'required': False
                }
        else:
            content = conference.submission_stage.get_content()

        readers = {'values-regex': '.*'}
        if reveal_submission:
            readers = {'values': ['everyone']}

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
                'writers': writers,
                'signatures': signatures,
                'content': content
            }
        )


class WithdrawSuperInvitation(openreview.Invitation):

    def __init__(self, conference, reveal_authors, reveal_submission, email_pcs, hide_fields=None):
        content = default_content.withdraw.copy()
        exp_date = tools.datetime_millis(conference.submission_stage.withdraw_submission_exp_date) if conference.submission_stage.withdraw_submission_exp_date else None

        withdraw_process_file = 'templates/withdraw_process.py'

        with open(os.path.join(os.path.dirname(__file__), withdraw_process_file)) as f:
            file_content = f.read()

            file_content = file_content.replace(
                'CONFERENCE_ID = \'\'',
                'CONFERENCE_ID = \'' + conference.get_id() + '\'')
            file_content = file_content.replace(
                'CONFERENCE_SHORT_NAME = \'\'',
                'CONFERENCE_SHORT_NAME = "' + conference.get_short_name() + '"')
            file_content = file_content.replace(
                'PAPER_AUTHORS_ID = \'\'',
                'PAPER_AUTHORS_ID = \'' + conference.get_authors_id(number='{number}') + '\'')
            file_content = file_content.replace(
                'PAPER_REVIEWERS_ID = \'\'',
                'PAPER_REVIEWERS_ID = \'' + conference.get_reviewers_id(number='{number}') + '\'')
            if conference.use_area_chairs:
                file_content = file_content.replace(
                    'PAPER_AREA_CHAIRS_ID = \'\'',
                    'PAPER_AREA_CHAIRS_ID = \'' + conference.get_area_chairs_id(number='{number}') + '\'')
            if conference.use_senior_area_chairs:
                file_content = file_content.replace(
                    'PAPER_SENIOR_AREA_CHAIRS_ID = \'\'',
                    'PAPER_SENIOR_AREA_CHAIRS_ID = \'' + conference.get_senior_area_chairs_id(number='{number}') + '\'')
            file_content = file_content.replace(
                'PROGRAM_CHAIRS_ID = \'\'',
                'PROGRAM_CHAIRS_ID = \'' + conference.get_program_chairs_id() + '\'')
            file_content = file_content.replace(
                'CONFERENCE_ROLES = []',
                str.format('CONFERENCE_ROLES = {}', conference.get_roles())
            )
            file_content = file_content.replace(
                'WITHDRAWN_SUBMISSION_ID = \'\'',
                'WITHDRAWN_SUBMISSION_ID = \'' + conference.submission_stage.get_withdrawn_submission_id(conference) + '\'')
            file_content = file_content.replace(
                'BLIND_SUBMISSION_ID = \'\'',
                'BLIND_SUBMISSION_ID = \'' + conference.get_blind_submission_id() + '\'')
            file_content = file_content.replace(
                'SUBMISSION_READERS = []',
                str.format('SUBMISSION_READERS = {}', conference.submission_stage.get_readers(conference=conference, number='{number}'))
            )
            file_content = file_content.replace(
                "CONFERENCE_NAME = ''",
                'CONFERENCE_NAME = "' + conference.get_name() + '"')
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
            if hide_fields:
                file_content = file_content.replace(
                    'HIDE_FIELDS = []',
                    str.format('HIDE_FIELDS = {}', hide_fields)
                )

            super(WithdrawSuperInvitation, self).__init__(
                id=conference.get_invitation_id("Withdraw"),
                cdate=None,
                duedate=None,
                expdate=exp_date,
                readers=['everyone'],
                writers=[conference.support_user],
                signatures=[conference.support_user],
                reply={
                    'forum': None,
                    'replyto': None,
                    'readers': {
                            'values': ['everyone']
                        },
                    'writers': {
                        'values': [],
                    },
                    'signatures': {
                        'values-regex': '~.*|{}'.format(conference.support_user)
                    },
                    'content': content,
                },
                process_string=file_content
            )


class PaperWithdrawInvitation(openreview.Invitation):

    def __init__(self, conference, note, reveal_submission):
        if reveal_submission:
            readers = {
                'description': 'User groups that will be able to read this withdraw note.',
                'values': ['everyone']
            }
        else:
            readers = {
                'values': conference.get_committee(with_authors=True, number=note.number)
            }

        super(PaperWithdrawInvitation, self).__init__(
            id=conference.get_invitation_id('Withdraw', note.number),
            super=conference.get_invitation_id('Withdraw'),
            cdate=None,
            invitees=[conference.get_authors_id(note.number), conference.support_user, conference.get_program_chairs_id()],
            readers=['everyone'],
            writers=[conference.get_id()],
            signatures=['~Super_User1'],
            multiReply=False,
            reply={
                'forum': note.id,
                'replyto': note.id,
                'readers': readers,
                'writers': {
                    'values': [
                        conference.get_id(), conference.get_program_chairs_id()
                    ]
                },
                'signatures': {
                    'values-regex': '{}|{}'.format(conference.get_program_chairs_id(), conference.get_authors_id(number=note.number)),
                    'description': 'How your identity will be displayed.'
                },
            }
        )

class DeskRejectedSubmissionInvitation(openreview.Invitation):

    def __init__(self, conference, reveal_authors, reveal_submission, hide_fields=[]):

        signatures = {'values-regex': '~.*'}
        writers = {'values-regex': '.*'}
        content = {}

        if conference.submission_stage.double_blind:
            signatures = {'values': [conference.get_id()]}
            writers = {'values': [conference.get_id()]}
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
            if not reveal_authors:
                content['authors'] = {'values': ['Anonymous']}
                content['authorids'] = {'values-regex': '.*'}
            for field in hide_fields:
                content[field] = {
                    'value-regex': '.*',
                    'required': False
                }
        else:
            content = conference.submission_stage.get_content()

        readers = {'values-regex': '.*'}
        if reveal_submission:
            readers = {'values': ['everyone']}

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
                'writers': writers,
                'signatures': signatures,
                'content': content
            }
        )

class PaperDeskRejectInvitation(openreview.Invitation):

    def __init__(self, conference, note, reveal_authors, reveal_submission, email_pcs, hide_fields=None):

        content = default_content.desk_reject.copy()

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
                'CONFERENCE_SHORT_NAME = "' + conference.get_short_name() + '"')
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
            if conference.use_senior_area_chairs:
                file_content = file_content.replace(
                    'PAPER_SENIOR_AREA_CHAIRS_ID = \'\'',
                    'PAPER_SENIOR_AREA_CHAIRS_ID = \'' + conference.get_senior_area_chairs_id(number=note.number) + '\'')
            file_content = file_content.replace(
                'PROGRAM_CHAIRS_ID = \'\'',
                'PROGRAM_CHAIRS_ID = \'' + conference.get_program_chairs_id() + '\'')
            file_content = file_content.replace(
                'CONFERENCE_ROLES = []',
                str.format('CONFERENCE_ROLES = {}', conference.get_roles())
            )
            file_content = file_content.replace(
                'DESK_REJECTED_SUBMISSION_ID = \'\'',
                'DESK_REJECTED_SUBMISSION_ID = \'' + conference.submission_stage.get_desk_rejected_submission_id(conference) + '\'')
            file_content = file_content.replace(
                "CONFERENCE_NAME = ''",
                'CONFERENCE_NAME = "' + conference.get_name() + '"')
            file_content = file_content.replace(
                'CONFERENCE_YEAR = \'\'',
                'CONFERENCE_YEAR = \'' + str(conference.get_year()) + '\'')
            file_content = file_content.replace(
                'BLIND_SUBMISSION_ID = \'\'',
                'BLIND_SUBMISSION_ID = \'' + conference.get_blind_submission_id() + '\'')
            file_content = file_content.replace(
                'SUBMISSION_READERS = []',
                str.format('SUBMISSION_READERS = {}', note.readers)
            )
            if reveal_authors:
                file_content = file_content.replace(
                    'REVEAL_AUTHORS_ON_DESK_REJECT = False',
                    'REVEAL_AUTHORS_ON_DESK_REJECT = True')
            if reveal_submission:
                file_content = file_content.replace(
                    'REVEAL_SUBMISSIONS_ON_DESK_REJECT = False',
                    'REVEAL_SUBMISSIONS_ON_DESK_REJECT = True')
            if hide_fields:
                file_content = file_content.replace(
                    'HIDE_FIELDS = []',
                    str.format('HIDE_FIELDS = {}', hide_fields)
                )
            if email_pcs:
                file_content = file_content.replace(
                    'EMAIL_PROGRAM_CHAIRS = False',
                    'EMAIL_PROGRAM_CHAIRS = True')

            super(PaperDeskRejectInvitation, self).__init__(
                id=conference.get_invitation_id('Desk_Reject', note.number),
                cdate=tools.datetime_millis(conference.submission_stage.due_date) if conference.submission_stage.due_date else None,
                duedate = None,
                expdate = tools.datetime_millis(conference.submission_stage.due_date + datetime.timedelta(days = 90)) if conference.submission_stage.due_date else None,
                invitees=[conference.get_program_chairs_id(), conference.support_user],
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

class SubmissionRevisionInvitation(openreview.Invitation):

    def __init__(self, conference, submission_content):

        submission_revision_stage = conference.submission_revision_stage
        accepted_only = conference.submission_revision_stage.only_accepted
        content = submission_content.copy()

        start_date = submission_revision_stage.start_date
        due_date = submission_revision_stage.due_date

        for field in submission_revision_stage.remove_fields:
            if field in content:
                del content[field]
            else:
                print('Field {} not found in content: {}'.format(field, content))

        for order, key in enumerate(submission_revision_stage.additional_fields, start=10):
            value = submission_revision_stage.additional_fields[key]
            value['order'] = order
            content[key] = value

        with open(os.path.join(os.path.dirname(__file__), 'templates/submission_revision_process.py')) as f:
            file_content = f.read()
            file_content = file_content.replace("SHORT_PHRASE = ''", f'SHORT_PHRASE = "{conference.get_short_name()}"')
            file_content = file_content.replace("CONFERENCE_ID = ''", "CONFERENCE_ID = '" + conference.get_id() + "'")
            file_content = file_content.replace("AUTHORS_NAME = ''", "AUTHORS_NAME = '" + conference.authors_name + "'")
            if accepted_only:
                file_content = file_content.replace("CONFERENCE_NAME = ''", f'CONFERENCE_NAME = "{conference.name}"')
                file_content = file_content.replace("CONFERENCE_YEAR = ''", "CONFERENCE_YEAR = '" + str(conference.year) + "'")
                file_content = file_content.replace("REVISION_INVITATION = ''", "REVISION_INVITATION = '" + conference.support_user + "/-/" + conference.venue_revision_name + "'")

            super(SubmissionRevisionInvitation, self).__init__(
                id=conference.get_invitation_id(submission_revision_stage.name),
                cdate=tools.datetime_millis(start_date) if start_date else None,
                duedate=tools.datetime_millis(due_date) if due_date else None,
                expdate=tools.datetime_millis(due_date + datetime.timedelta(minutes=SHORT_BUFFER_MIN)) if due_date else None,
                multiReply=submission_revision_stage.multiReply,
                readers=['everyone'],
                writers=[conference.get_id()],
                signatures=[conference.get_id()],
                reply={
                    'content': content
                },
                process_string=file_content
            )

class PaperSubmissionRevisionInvitation(openreview.Invitation):

    def __init__(self, conference, note, submission_content):

        submission_revision_stage = conference.submission_revision_stage
        referent = note.original if note.original else note.id

        start_date = submission_revision_stage.start_date
        due_date = submission_revision_stage.due_date
        content = None

        if submission_revision_stage.allow_author_reorder:
            original_content = note.details['original']['content'] if conference.submission_stage.double_blind else note.content

            content = submission_content.copy()

            for field in submission_revision_stage.remove_fields:
                if field in content:
                    del content[field]
                else:
                    print('Field {} not found in content: {}'.format(field, content))

            for order, key in enumerate(submission_revision_stage.additional_fields, start=10):
                value = submission_revision_stage.additional_fields[key]
                value['order'] = order
                content[key] = value

            content['authors']={
                'values': original_content['authors'],
                'required': True,
                'hidden': True,
                'order': content['authors']['order']
            }
            content['authorids']={
                'values': original_content['authorids'],
                'required': True,
                'order': content['authorids']['order']
            }

        reply = {
            'forum': referent,
            'referent': referent,
            'content': content,
            'readers': {
                'values': [
                    conference.get_id(),
                    conference.get_authors_id(number=note.number)
                ]
            },
            'writers': {
                'values': [
                    conference.get_id(),
                    conference.get_authors_id(number=note.number)
                ]
            },
            'signatures': {
                'values-regex': '{}|{}'.format(conference.get_program_chairs_id(), conference.get_authors_id(number=note.number))
            }
        }

        invitees = [conference.get_id(), conference.get_authors_id(number=note.number)]
        super(PaperSubmissionRevisionInvitation, self).__init__(
            id=conference.get_invitation_id(submission_revision_stage.name, note.number),
            super=conference.get_invitation_id(submission_revision_stage.name),
            readers=invitees,
            writers=[conference.get_id()],
            signatures=['~Super_User1' if submission_revision_stage.only_accepted else conference.get_id()],
            invitees=invitees,
            reply=reply
        )

class PublicCommentInvitation(openreview.Invitation):

    def __init__(self, conference, note):

        comment_stage = conference.comment_stage

        signature_regex = '~.*|{}'.format(conference.get_program_chairs_id())

        if comment_stage.anonymous:
            signature_regex = '~.*|\\(anonymous\\)|{}'.format(conference.get_program_chairs_id())

        super(PublicCommentInvitation, self).__init__(id = conference.get_invitation_id('Public_Comment', note.number),
            super = conference.get_invitation_id('Comment'),
            cdate = tools.datetime_millis(comment_stage.start_date) if comment_stage.start_date else None,
            expdate = tools.datetime_millis(conference.comment_stage.end_date + datetime.timedelta(days=LONG_BUFFER_DAYS)) if conference.comment_stage.end_date else None,
            writers = [conference.get_id()],
            signatures = [conference.get_id()],
            invitees = ['everyone'],
            noninvitees = [] if comment_stage.only_accepted else conference.get_committee(number = note.number, with_authors = True),
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
                    'values-regex': signature_regex,
                    'description': 'How your identity will be displayed.'
                }
            }
        )

class OfficialCommentInvitation(openreview.Invitation):

    def __init__(self, conference, note):

        comment_stage = conference.comment_stage

        prefix = conference.get_id() + '/Paper' + str(note.number) + '/'
        anon_reviewer_regex=conference.get_anon_reviewer_id(number=note.number, anon_id='.*')

        readers = comment_stage.get_readers(conference, note.number)
        invitees = comment_stage.get_invitees(conference, note.number)

        if comment_stage.reader_selection:
            reply_readers = {
                'description': 'Who your comment will be visible to. If replying to a specific person make sure to add the group they are a member of so that they are able to see your response',
                'values-dropdown': readers#,
                ##'default': None if comment_stage.allow_public_comments else [conference.get_program_chairs_id()]
            }
        else:
            reply_readers = {
                'description': 'User groups that will be able to read this comment.',
                'values': readers
            }

        super(OfficialCommentInvitation, self).__init__(
            id = conference.get_invitation_id(comment_stage.official_comment_name, note.number),
            super = conference.get_invitation_id('Comment'),
            cdate = tools.datetime_millis(comment_stage.start_date) if comment_stage.start_date else None,
            expdate = tools.datetime_millis(comment_stage.end_date) if comment_stage.end_date else None,
            writers = [conference.id],
            signatures = [conference.id],
            invitees = invitees,
            reply = {
                'forum': note.id,
                'replyto': None,
                'readers': reply_readers,
                'nonreaders': {
                    'values-dropdown': readers
                },
                'writers': {
                    'values-copied': [
                        conference.id,
                        '{signatures}'
                    ]
                },
                'signatures': {
                    'values-regex': '|'.join(comment_stage.get_signatures(conference, note.number)),
                    'description': 'How your identity will be displayed.'
                }
            }
        )

class ReviewInvitation(openreview.Invitation):

    def __init__(self, conference):
        review_stage = conference.review_stage
        content = default_content.review.copy()

        for key in review_stage.additional_fields:
            content[key] = review_stage.additional_fields[key]

        for field in review_stage.remove_fields:
            if field in content:
                del content[field]

        process_file = os.path.join(os.path.dirname(__file__), 'templates/reviewProcess.js')
        with open(process_file) as f:
            file_content = f.read()

            file_content = file_content.replace("var CONFERENCE_ID = '';", "var CONFERENCE_ID = '" + conference.id + "';")
            file_content = file_content.replace("var SHORT_PHRASE = '';", f'var SHORT_PHRASE = "{conference.get_short_name()}";')
            file_content = file_content.replace("var AUTHORS_NAME = '';", "var AUTHORS_NAME = '" + conference.authors_name + "';")
            file_content = file_content.replace("var REVIEWERS_NAME = '';", "var REVIEWERS_NAME = '" + conference.reviewers_name + "';")
            file_content = file_content.replace("var AREA_CHAIRS_NAME = '';", "var AREA_CHAIRS_NAME = '" + conference.area_chairs_name + "';")
            file_content = file_content.replace("var OFFICIAL_REVIEW_NAME = '';", "var OFFICIAL_REVIEW_NAME = '" + ('Review' if 'Official' in review_stage.name else review_stage.name) + "';")
            file_content = file_content.replace("var ADD_SUBMITED = false;", "var ADD_SUBMITED = true;")


            if conference.use_area_chairs:
                file_content = file_content.replace("var USE_AREA_CHAIRS = false;", "var USE_AREA_CHAIRS = true;")

            if review_stage.email_pcs:
                file_content = file_content.replace("var PROGRAM_CHAIRS_ID = '';", "var PROGRAM_CHAIRS_ID = '" + conference.get_program_chairs_id() + "';")

            exp_date = tools.datetime_millis(review_stage.exp_date) if review_stage.exp_date else None
            if not exp_date:
                exp_date = tools.datetime_millis(review_stage.due_date + datetime.timedelta(minutes = SHORT_BUFFER_MIN)) if review_stage.due_date else None

            super(ReviewInvitation, self).__init__(id = conference.get_invitation_id(review_stage.name),
                cdate = tools.datetime_millis(review_stage.start_date),
                duedate = tools.datetime_millis(review_stage.due_date),
                expdate = exp_date,
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
        signature_regex = '|'.join(review_stage.get_signatures(conference, note.number))
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
                'values-copied': [conference.get_id(), '{signatures}'],
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
            invitees = [conference.get_reviewers_id(number = note.number), conference.get_program_chairs_id(), conference.support_user],
            reply = reply
        )

class EthicsReviewInvitation(openreview.Invitation):

    def __init__(self, conference):
        ethics_review_stage = conference.ethics_review_stage
        content = default_content.ethics_review.copy()

        for key in ethics_review_stage.additional_fields:
            content[key] = ethics_review_stage.additional_fields[key]

        for field in ethics_review_stage.remove_fields:
            if field in content:
                del content[field]

        process_file = os.path.join(os.path.dirname(__file__), 'templates/reviewProcess.js')
        with open(process_file) as f:
            file_content = f.read()

            file_content = file_content.replace("var CONFERENCE_ID = '';", "var CONFERENCE_ID = '" + conference.id + "';")
            file_content = file_content.replace("var SHORT_PHRASE = '';", f'var SHORT_PHRASE = "{conference.get_short_name()}";')
            file_content = file_content.replace("var AUTHORS_NAME = '';", "var AUTHORS_NAME = '" + conference.authors_name + "';")
            file_content = file_content.replace("var REVIEWERS_NAME = '';", "var REVIEWERS_NAME = '" + conference.ethics_reviewers_name + "';")
            file_content = file_content.replace("var AREA_CHAIRS_NAME = '';", "var AREA_CHAIRS_NAME = '" + conference.area_chairs_name + "';")
            file_content = file_content.replace("var OFFICIAL_REVIEW_NAME = '';", "var OFFICIAL_REVIEW_NAME = '" + ethics_review_stage.name + "';")

            exp_date = tools.datetime_millis(ethics_review_stage.exp_date) if ethics_review_stage.exp_date else None
            if not exp_date:
                exp_date = tools.datetime_millis(ethics_review_stage.due_date + datetime.timedelta(minutes = SHORT_BUFFER_MIN)) if ethics_review_stage.due_date else None

            super(EthicsReviewInvitation, self).__init__(id = conference.get_invitation_id(ethics_review_stage.name),
                cdate = tools.datetime_millis(ethics_review_stage.start_date),
                duedate = tools.datetime_millis(ethics_review_stage.due_date),
                expdate = exp_date,
                readers = ['everyone'],
                writers = [conference.id],
                signatures = [conference.id],
                multiReply = False,
                reply = {
                    'content': content
                },
                process_string = file_content
            )

class PaperEthicsReviewInvitation(openreview.Invitation):

    def __init__(self, conference, note):

        ethics_review_stage = conference.ethics_review_stage
        signature_regex = '|'.join(ethics_review_stage.get_signatures(conference, note.number))
        readers = ethics_review_stage.get_readers(conference, note.number)
        nonreaders = ethics_review_stage.get_nonreaders(conference, note.number)

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
                'values-copied': [conference.get_id(), '{signatures}'],
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

        super(PaperEthicsReviewInvitation, self).__init__(id = conference.get_invitation_id(ethics_review_stage.name, note.number),
            super = conference.get_invitation_id(ethics_review_stage.name),
            writers = [conference.id],
            signatures = [conference.id],
            invitees = [conference.get_ethics_reviewers_id(number = note.number), conference.get_program_chairs_id(), conference.support_user],
            reply = reply
        )                     

class RebuttalInvitation(openreview.Invitation):

    def __init__(self, conference):
        review_rebuttal_stage = conference.review_rebuttal_stage
        content = {
            'rebuttal': {
                'order': 1,
                'value-regex': '[\\S\\s]{0,2500}',
                'description': 'Rebuttals can include Markdown formatting and LaTeX forumulas, for more information see https://openreview.net/faq , max length: 2500',
                'required': True,
                'markdown': True
            }
        }

        for key in review_rebuttal_stage.additional_fields:
            content[key] = review_rebuttal_stage.additional_fields[key]

        with open(os.path.join(os.path.dirname(__file__), 'templates/reviewRebuttalProcess.js')) as f:
            file_content = f.read()

            file_content = file_content.replace("var CONFERENCE_ID = '';", "var CONFERENCE_ID = '" + conference.id + "';")
            file_content = file_content.replace("var SHORT_PHRASE = '';", f'var SHORT_PHRASE = "{conference.get_short_name()}";')
            file_content = file_content.replace("var AUTHORS_NAME = '';", "var AUTHORS_NAME = '" + conference.authors_name + "';")
            file_content = file_content.replace("var REVIEWERS_NAME = '';", "var REVIEWERS_NAME = '" + conference.reviewers_name + "';")
            file_content = file_content.replace("var AREA_CHAIRS_NAME = '';", "var AREA_CHAIRS_NAME = '" + conference.area_chairs_name + "';")

            if conference.use_area_chairs:
                file_content = file_content.replace("var USE_AREA_CHAIRS = false;", "var USE_AREA_CHAIRS = true;")

            if review_rebuttal_stage.email_pcs:
                file_content = file_content.replace("var PROGRAM_CHAIRS_ID = '';", "var PROGRAM_CHAIRS_ID = '" + conference.get_program_chairs_id() + "';")


            super(RebuttalInvitation, self).__init__(id = conference.get_invitation_id(review_rebuttal_stage.name),
                cdate = tools.datetime_millis(review_rebuttal_stage.start_date),
                duedate = tools.datetime_millis(review_rebuttal_stage.due_date),
                expdate = tools.datetime_millis(review_rebuttal_stage.due_date + datetime.timedelta(minutes= SHORT_BUFFER_MIN)) if review_rebuttal_stage.due_date else None,
                readers = ['everyone'],
                writers = [conference.id],
                signatures = [conference.id],
                multiReply = False,
                reply = {
                    'content': content
                },
                process_string = file_content
            )

class PaperReviewRebuttalInvitation(openreview.Invitation):

    def __init__(self, conference, review):

        review_rebuttal_stage = conference.review_rebuttal_stage
        paper_group = review.invitation.split('/-/')[0]
        signature = review.signatures[0]

        reply = {
            'forum': review.forum,
            'replyto': review.id,
            'readers': {
                'description': 'All user groups that should be able to read this rebuttal.',
                'values': review.readers
            },
            'signatures': {
                'description': 'How your identity will be displayed with the above content.',
                'values-regex': paper_group + '/Authors|'+ conference.get_program_chairs_id()
            },
            'writers': {
                'description': 'Users that may modify this record.',
                'values-copied': [conference.get_id(), '{signatures}']
            }
        }

        super(PaperReviewRebuttalInvitation, self).__init__(id = signature + '/-/' + review_rebuttal_stage.name,
            super = conference.get_invitation_id(review_rebuttal_stage.name),
            writers = [conference.id],
            signatures = [conference.id],
            invitees = [paper_group + '/Authors', conference.get_program_chairs_id(), conference.support_user],
            reply = reply
        )

class PaperRebuttalInvitation(openreview.Invitation):

    def __init__(self, conference, note):

        review_rebuttal_stage = conference.review_rebuttal_stage

        reply = {
            'forum': note.forum,
            'replyto': note.forum,
            'readers': {
                'description': 'All user groups that should be able to read this rebuttal.',
                'values': review_rebuttal_stage.get_invitation_readers(conference, note.number)
            },
            'signatures': {
                'description': 'How your identity will be displayed with the above content.',
                'values-regex': f'{conference.get_authors_id(note.number)}|{conference.get_program_chairs_id()}'
            },
            'writers': {
                'description': 'Users that may modify this record.',
                'values': [conference.get_id(), conference.get_authors_id(note.number)]
            }
        }

        super(PaperRebuttalInvitation, self).__init__(id = conference.get_invitation_id(name=review_rebuttal_stage.name, number=note.number),
            super = conference.get_invitation_id(review_rebuttal_stage.name),
            writers = [conference.id],
            signatures = [conference.id],
            invitees = [conference.get_authors_id(note.number), conference.get_program_chairs_id(), conference.support_user],
            reply = reply
        )        

class ReviewRevisionInvitation(openreview.Invitation):

    def __init__(self, conference):

        review_revision_stage = conference.review_revision_stage
        content = default_content.review.copy()

        for key in review_revision_stage.additional_fields:
            content[key] = review_revision_stage.additional_fields[key]

        for field in review_revision_stage.remove_fields:
            if field in content:
                del content[field]

        with open(os.path.join(os.path.dirname(__file__), 'templates/reviewRevisionProcess.js')) as f:
            file_content = f.read()

            file_content = file_content.replace("var CONFERENCE_ID = '';", "var CONFERENCE_ID = '" + conference.id + "';")
            file_content = file_content.replace("var SHORT_PHRASE = '';", f'var SHORT_PHRASE = "{conference.get_short_name()}";')
            file_content = file_content.replace("var AUTHORS_NAME = '';", "var AUTHORS_NAME = '" + conference.authors_name + "';")
            file_content = file_content.replace("var REVIEWERS_NAME = '';", "var REVIEWERS_NAME = '" + conference.reviewers_name + "';")
            file_content = file_content.replace("var AREA_CHAIRS_NAME = '';", "var AREA_CHAIRS_NAME = '" + conference.area_chairs_name + "';")
            file_content = file_content.replace("var PROGRAM_CHAIRS_NAME = '';", "var PROGRAM_CHAIRS_NAME = '" + conference.program_chairs_name + "';")

            super(ReviewRevisionInvitation, self).__init__(id = conference.get_invitation_id(review_revision_stage.name),
                cdate = tools.datetime_millis(review_revision_stage.start_date),
                duedate = tools.datetime_millis(review_revision_stage.due_date),
                expdate = tools.datetime_millis(review_revision_stage.due_date + datetime.timedelta(minutes= SHORT_BUFFER_MIN)) if review_revision_stage.due_date else None,
                readers = ['everyone'],
                writers = [conference.id],
                signatures = [conference.id],
                multiReply = False,
                reply = {
                    'content': content
                },
                process_string = file_content
            )

class PaperReviewRevisionInvitation(openreview.Invitation):

    def __init__(self, conference, review):

        review_revision_stage = conference.review_revision_stage

        reply = {
            'forum': review.forum,
            'replyto': None,
            'referent': review.id,
            'readers': {
                'description': 'Select all user groups that should be able to read this comment.',
                'values': review.readers
            },
            'nonreaders': {
                'values': review.nonreaders
            },
            'writers': {
                'values-copied': [conference.get_id(), '{signatures}'],
                'description': 'How your identity will be displayed.'
            },
            'signatures': {
                'values-regex': '{}|{}'.format(review.signatures[0], conference.get_program_chairs_id()),
                'description': 'How your identity will be displayed.'
            }
        }

        super(PaperReviewRevisionInvitation, self).__init__(id = review.signatures[0] + '/-/' + review_revision_stage.name,
            super = conference.get_invitation_id(review_revision_stage.name),
            writers = [conference.id],
            signatures = [conference.id],
            invitees = review.signatures + [conference.id, conference.support_user],
            reply = reply
        )

class ReviewRatingInvitation(openreview.Invitation):

    def __init__(self, conference):

        review_rating_stage = conference.review_rating_stage
        content = default_content.review_rating.copy()

        for key in review_rating_stage.additional_fields:
            content[key] = review_rating_stage.additional_fields[key]

        for field in review_rating_stage.remove_fields:
            if field in content:
                del content[field]

        super(ReviewRatingInvitation, self).__init__(id = conference.get_invitation_id(review_rating_stage.name),
            cdate = tools.datetime_millis(review_rating_stage.start_date),
            duedate = tools.datetime_millis(review_rating_stage.due_date),
            expdate = tools.datetime_millis(review_rating_stage.due_date + datetime.timedelta(days = LONG_BUFFER_DAYS)) if review_rating_stage.due_date else None,
            readers = ['everyone'],
            writers = [conference.id],
            signatures = [conference.id],
            multiReply = False,
            reply = {
                'content': content
            }
        )

class PaperReviewRatingInvitation(openreview.Invitation):

    def __init__(self, conference, review):

        review_rating_stage = conference.review_rating_stage
        paper_group = review.invitation.split('/-/')[0]
        paper_number = paper_group.split('/Paper')[-1]
        review_signature = review.signatures[0]
        readers = review_rating_stage.get_readers(conference, paper_number, review_signature)

        reply = {
            'forum': review.forum,
            'replyto': review.id,
            'readers': {
                'description': 'Select all user groups that should be able to read this comment.',
                'values-copied': readers
            },
            'writers': {
                'values-copied': [conference.get_id(), '{signatures}'],
                'description': 'How your identity will be displayed.'
            },
            'signatures': {
                'values-regex': conference.get_anon_area_chair_id(number=paper_number, anon_id='.*'),
                'description': 'How your identity will be displayed.'
            }
        }

        super(PaperReviewRatingInvitation, self).__init__(id = review.signatures[0] + '/-/' + review_rating_stage.name,
            super = conference.get_invitation_id(review_rating_stage.name),
            writers = [conference.id],
            signatures = [conference.id],
            invitees = [paper_group + '/Area_Chairs', conference.support_user],
            reply = reply
        )

class MetaReviewInvitation(openreview.Invitation):

    def __init__(self, conference):
        content = default_content.meta_review.copy()
        meta_review_stage = conference.meta_review_stage
        additional_fields = meta_review_stage.additional_fields
        start_date = meta_review_stage.start_date
        due_date = meta_review_stage.due_date
        process = meta_review_stage.process

        for key in additional_fields:
            content[key] = additional_fields[key]

        for field in meta_review_stage.remove_fields:
            if field in content:
                del content[field]

        exp_date = tools.datetime_millis(meta_review_stage.exp_date) if meta_review_stage.exp_date else None
        if not exp_date:
            exp_date = tools.datetime_millis(meta_review_stage.due_date + datetime.timedelta(minutes = SHORT_BUFFER_MIN)) if meta_review_stage.due_date else None

        super(MetaReviewInvitation, self).__init__(id = conference.get_invitation_id(meta_review_stage.name),
            cdate = tools.datetime_millis(start_date),
            duedate = tools.datetime_millis(due_date),
            expdate = exp_date,
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
        invitees = [conference.get_program_chairs_id()]
        writers = [conference.get_program_chairs_id()]
        nonreaders = meta_review_stage.get_nonreaders(conference, note.number)

        if conference.use_area_chairs:
            paper_area_chair = conference.get_area_chairs_id(number = note.number)
            invitees.append(paper_area_chair)
            writers.append(paper_area_chair)

        super(PaperMetaReviewInvitation, self).__init__(
            id = conference.get_invitation_id(meta_review_stage.name, note.number),
            super = conference.get_invitation_id(meta_review_stage.name),
            writers = [conference.id],
            signatures = [conference.id],
            invitees = invitees + [conference.support_user],
            noninvitees = [conference.get_authors_id(number = note.number)] + ([conference.get_secondary_area_chairs_id(note.number)] if conference.use_secondary_area_chairs else []),
            reply = {
                'forum': note.id,
                'replyto': note.id,
                'readers': {
                    "description": "Select all user groups that should be able to read this comment.",
                    "values": readers
                },
                'nonreaders': {
                    'values': nonreaders
                },
                'writers': {
                    'values': writers,
                    'description': 'Who can edit this meta-review.'
                },
                'signatures': {
                    'values-regex': '|'.join(meta_review_stage.get_signatures(conference, note.number)),
                    'description': 'How your identity will be displayed.'
                }
            }
        )

class MetaReviewRevisionInvitation(openreview.Invitation):

    def __init__(self, conference):

        meta_review_revision_stage = conference.meta_review_revision_stage
        content = default_content.meta_review.copy()

        for key in meta_review_revision_stage.additional_fields:
            content[key] = meta_review_revision_stage.additional_fields[key]

        for field in meta_review_revision_stage.remove_fields:
            if field in content:
                del content[field]

        super(MetaReviewRevisionInvitation, self).__init__(id = conference.get_invitation_id(meta_review_revision_stage.name),
            cdate = tools.datetime_millis(meta_review_revision_stage.start_date),
            duedate = tools.datetime_millis(meta_review_revision_stage.due_date),
            expdate = tools.datetime_millis(meta_review_revision_stage.due_date + datetime.timedelta(minutes = SHORT_BUFFER_MIN)) if meta_review_revision_stage.due_date else None,
            readers = ['everyone'],
            writers = [conference.id],
            signatures = [conference.id],
            multiReply = False,
            reply = {
                'content': content
            }
        )

class PaperMetaReviewRevisionInvitation(openreview.Invitation):

    def __init__(self, conference, metareview):

        meta_review_revision_stage = conference.meta_review_revision_stage

        reply = {
            'forum': metareview.forum,
            'replyto': None,
            'referent': metareview.id,
            'readers': {
                'description': 'Select all user groups that should be able to read this comment.',
                'values': metareview.readers
            },
            'nonreaders': {
                'values': metareview.nonreaders
            },
            'writers': {
                'values-copied': [conference.get_program_chairs_id(), '{signatures}'],
                'description': 'How your identity will be displayed.'
            },
            'signatures': {
                'values-regex': '{}|{}'.format(metareview.signatures[0], conference.get_program_chairs_id()),
                'description': 'How your identity will be displayed.'
            }
        }

        super(PaperMetaReviewRevisionInvitation, self).__init__(id = metareview.signatures[0] + '/-/' + meta_review_revision_stage.name,
            super = conference.get_invitation_id(meta_review_revision_stage.name),
            writers = [conference.id],
            signatures = [conference.id],
            invitees = metareview.signatures + [conference.support_user],
            reply = reply
        )

class DecisionInvitation(openreview.Invitation):

    def __init__(self, conference):
        decision_stage = conference.decision_stage
        start_date = decision_stage.start_date
        due_date = decision_stage.due_date
        additional_fields = decision_stage.additional_fields
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

        for key in additional_fields:
            content[key] = additional_fields[key]

        file_content = None
        decision_process_file = 'templates/decision_process.py'
        with open(os.path.join(os.path.dirname(__file__), decision_process_file)) as f:
            file_content = f.read()

            file_content = file_content.replace("CONFERENCE_ID = ''", "CONFERENCE_ID = '" + conference.id + "'")
            file_content = file_content.replace("SHORT_PHRASE = ''", f'SHORT_PHRASE = "{conference.get_short_name()}"')
            file_content = file_content.replace("AUTHORS_NAME = ''", "AUTHORS_NAME = '" + conference.authors_name + "'")
            file_content = file_content.replace("AUTHORS_NAME_ACCEPTED = ''", "AUTHORS_NAME_ACCEPTED = '"  + conference.authors_name + '/Accepted' + "'")
            if decision_stage.email_authors:
                file_content = file_content.replace("EMAIL_AUTHORS = False", "EMAIL_AUTHORS = True")

        super(DecisionInvitation, self).__init__(id = conference.get_invitation_id(decision_stage.name),
            cdate = tools.datetime_millis(start_date),
            duedate = tools.datetime_millis(due_date),
            expdate = tools.datetime_millis(due_date + datetime.timedelta(days = LONG_BUFFER_DAYS)) if due_date else None,
            readers = ['everyone'],
            writers = [conference.id],
            signatures = [conference.id],
            invitees = [conference.get_program_chairs_id(), conference.support_user],
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
            },
            process_string=file_content
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


class PaperGroupInvitation(openreview.Invitation):

    def __init__(self, conference, committee_id, with_process_function):

        with open(os.path.join(os.path.dirname(__file__), 'templates/paper_group_process.py')) as f:
            file_content = f.read()
            file_content = file_content.replace("VENUE_ID = ''", "VENUE_ID = '" + conference.id + "'")
            file_content = file_content.replace("SUBMISSION_INVITATION_ID = ''", "SUBMISSION_INVITATION_ID = '" + conference.get_blind_submission_id() + "'")
            file_content = file_content.replace("EDGE_INVITATION_ID = ''", "EDGE_INVITATION_ID = '" + conference.get_paper_assignment_id(committee_id, deployed=True) + "'")

            edge_readers = []
            edge_writers = []

            if committee_id.endswith(conference.reviewers_name):
                if conference.use_senior_area_chairs :
                    edge_readers.append(conference.get_senior_area_chairs_id(number='{number}'))
                    edge_writers.append(conference.get_senior_area_chairs_id(number='{number}'))

                if conference.use_area_chairs :
                    edge_readers.append(conference.get_area_chairs_id(number='{number}'))
                    edge_writers.append(conference.get_area_chairs_id(number='{number}'))

            file_content = file_content.replace("EDGE_READERS = []", "EDGE_READERS = " + json.dumps(edge_readers))
            file_content = file_content.replace("EDGE_WRITERS = []", "EDGE_WRITERS = " + json.dumps(edge_writers))

        super(PaperGroupInvitation, self).__init__(id = conference.get_invitation_id('Paper_Group', prefix=committee_id),
            readers = [conference.id],
            writers = [conference.id],
            signatures = [conference.id],
            reply = {
                'content': {
                    'dummy': {
                        'value': 'dummy'
                    }
                }
            },
            process_string=file_content if with_process_function else None

        )

class PaperRecruitmentInvitation(openreview.Invitation):

    def __init__(self, conference, invitation_id, committee_id, invited_committee_name, hash_seed, assignment_title, due_date, web, process_file, invited_label, accepted_label, declined_label):

        content=default_content.paper_recruitment

        with open(os.path.join(os.path.dirname(__file__), 'templates/paper_recruitment_pre_process.py')) as pre:
            with open(os.path.join(os.path.dirname(__file__), process_file)) as post:
                pre_content = pre.read()
                post_content = post.read()
                post_content = post_content.replace("SHORT_PHRASE = ''", f'SHORT_PHRASE = "{conference.get_short_name()}"')
                post_content = post_content.replace("VENUE_ID = ''", "VENUE_ID = '" + conference.get_id() + "'")
                post_content = post_content.replace("REVIEWER_NAME = ''", "REVIEWER_NAME = '" + conference.get_committee_name(committee_id, pretty=True) + "'")
                post_content = post_content.replace("REVIEWERS_ID = ''", "REVIEWERS_ID = '" + committee_id + "'")
                post_content = post_content.replace("INVITE_ASSIGNMENT_INVITATION_ID = ''", "INVITE_ASSIGNMENT_INVITATION_ID = '" + conference.get_paper_assignment_id(committee_id, invite=True) + "'")
                pre_content = pre_content.replace("HASH_SEED = ''", "HASH_SEED = '" + hash_seed + "'")
                post_content = post_content.replace("HASH_SEED = ''", "HASH_SEED = '" + hash_seed + "'")
                post_content = post_content.replace("INVITED_LABEL = ''", "INVITED_LABEL = '" + invited_label + "'")
                post_content = post_content.replace("ACCEPTED_LABEL = ''", "ACCEPTED_LABEL = '" + accepted_label + "'")
                post_content = post_content.replace("DECLINED_LABEL = ''", "DECLINED_LABEL = '" + declined_label + "'")
                pre_content = pre_content.replace("REVIEWERS_INVITED_ID = ''", "REVIEWERS_INVITED_ID = '" + conference.get_committee_id(name=invited_committee_name + '/Invited') + "'")
                post_content = post_content.replace("EXTERNAL_COMMITTEE_ID = ''", "EXTERNAL_COMMITTEE_ID = '" + conference.get_committee_id(name=invited_committee_name) + "'")

                ## Add to the proposed assignment or the deployed one.
                if assignment_title:
                    post_content = post_content.replace("ASSIGNMENT_INVITATION_ID = ''", "ASSIGNMENT_INVITATION_ID = '" + conference.get_paper_assignment_id(committee_id) + "'")
                    post_content = post_content.replace("ASSIGNMENT_LABEL = None", "ASSIGNMENT_LABEL = '" + assignment_title + "'")
                    post_content = post_content.replace("EXTERNAL_PAPER_COMMITTEE_ID = ''", "EXTERNAL_PAPER_COMMITTEE_ID = '" + conference.get_committee_id(name=invited_committee_name, number='{number}') + "'")
                else:
                    post_content = post_content.replace("ASSIGNMENT_INVITATION_ID = ''", "ASSIGNMENT_INVITATION_ID = '" + conference.get_paper_assignment_id(committee_id, deployed=True) + "'")

                if conference.use_recruitment_template:
                    post_content = post_content.replace("USE_RECRUITMENT_TEMPLATE = False", "USE_RECRUITMENT_TEMPLATE = True")

                
                edge_readers = []
                edge_writers = []
                if committee_id.endswith(conference.area_chairs_name):
                    if conference.has_senior_area_chairs :
                        #TODO: decide what to do with area chair assignments
                        edge_readers.append(conference.get_senior_area_chairs_id(number='{number}'))
                        edge_writers.append(conference.get_senior_area_chairs_id(number='{number}'))

                if committee_id.endswith(conference.reviewers_name):
                    if conference.use_senior_area_chairs :
                        edge_readers.append(conference.get_senior_area_chairs_id(number='{number}'))
                        edge_writers.append(conference.get_senior_area_chairs_id(number='{number}'))

                    if conference.use_area_chairs:
                        edge_readers.append(conference.get_area_chairs_id(number='{number}'))
                        edge_writers.append(conference.get_area_chairs_id(number='{number}'))

                post_content = post_content.replace("EDGE_READERS = []", "EDGE_READERS = " + json.dumps(edge_readers))
                post_content = post_content.replace("EDGE_WRITERS = []", "EDGE_WRITERS = " + json.dumps(edge_writers))

                super(PaperRecruitmentInvitation, self).__init__(id = invitation_id,
                    duedate = tools.datetime_millis(due_date),
                    expdate = tools.datetime_millis(due_date + datetime.timedelta(minutes= SHORT_BUFFER_MIN)) if due_date else None,
                    readers = ['everyone'],
                    nonreaders = [],
                    invitees = ['everyone'],
                    noninvitees = [],
                    writers = [conference.get_id()],
                    signatures = [conference.get_program_chairs_id()],
                    reply = {
                        'forum': None,
                        'replyto': None,
                        'readers': {
                            'values-copied': [
                                conference.get_id(),
                                '{content.user}',
                                '{content.inviter}'
                            ]
                        },
                        'signatures': {
                            'values-regex': '\\(anonymous\\)'
                        },
                        'writers': {
                            'values': [
                                conference.get_id(),
                                '(anonymous)'
                            ]
                        },
                        'content': content
                    },
                    preprocess= pre_content,
                    process_string = post_content,
                    web_string = web
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

    def __update_readers(self, submission, invitation):
        ## Update readers of current notes
        notes = self.client.get_notes(invitation=invitation.id)

        ## if the invitation indicates readers is everyone but the submission is not, we ignore the update
        if 'values' in invitation.reply['readers'] and 'everyone' in invitation.reply['readers']['values'] and 'everyone' not in submission.readers:
            return

        for note in notes:
            if 'values' in invitation.reply['readers'] and note.readers != invitation.reply['readers']['values']:
                note.readers = invitation.reply['readers']['values']
                if 'nonreaders' in invitation.reply:
                    note.nonreaders = invitation.reply['nonreaders']['values']
                self.client.post_note(note)
            if 'values-copied' in invitation.reply['readers'] and len(note.readers) != len(invitation.reply['readers']['values-copied']):
                note.readers = [reader.replace('{signatures}', note.signatures[0]) for reader in invitation.reply['readers']['values-copied']]
                if 'nonreaders' in invitation.reply:
                    note.nonreaders = invitation.reply['nonreaders']['values']
                self.client.post_note(note)

    def set_submission_invitation(self, conference, under_submission=False):

        return self.client.post_invitation(SubmissionInvitation(conference, under_submission))


    def set_blind_submission_invitation(self, conference, hide_fields):

        invitation = BlindSubmissionsInvitation(conference = conference, hide_fields=hide_fields)

        return  self.client.post_invitation(invitation)

    def set_expertise_selection_invitation(self, conference):

        invitation_id=conference.get_expertise_selection_id()
        current_invitation=openreview.tools.get_invitation(self.client, id = invitation_id)

        if current_invitation is None:
            invitation = ExpertiseSelectionInvitation(conference, current_invitation)

            return self.client.post_invitation(invitation)
        return current_invitation

    def set_bid_invitation(self, conference, stage):

        invitation_id=conference.get_bid_id(stage.committee_id)
        current_invitation=openreview.tools.get_invitation(self.client, id = invitation_id)
        return self.client.post_invitation(BidInvitation(conference, stage, current_invitation))

    def set_comment_invitation(self, conference, notes):

        invitations = []
        self.client.post_invitation(CommentInvitation(conference))

        if conference.comment_stage.only_accepted:
            accepted_notes=conference.get_submissions(accepted=True)
            for note in tqdm(accepted_notes, total=len(accepted_notes), desc='set_public_comment_invitation_only_accepted'):
                invitations.append(self.client.post_invitation(PublicCommentInvitation(conference, note)))
            return invitations

        for note in tqdm(notes, total=len(notes), desc='set_comment_invitation'):
            invitations.append(self.client.post_invitation(OfficialCommentInvitation(conference, note)))

        if conference.comment_stage.allow_public_comments:
            for note in tqdm(notes, total=len(notes), desc='set_public_comment_invitation'):
                if 'everyone' in note.readers:
                    invitations.append(self.client.post_invitation(PublicCommentInvitation(conference, note)))

        return invitations

    def set_withdraw_invitation(self, conference, reveal_authors, reveal_submission, email_pcs, hide_fields=None):

        invitations = []

        self.client.post_invitation(WithdrawnSubmissionInvitation(conference, reveal_authors, reveal_submission, hide_fields))
        self.client.post_invitation(WithdrawSuperInvitation(conference, reveal_authors, reveal_submission, email_pcs, hide_fields))
        notes = list(conference.get_submissions())

        def post_invitation(note):
            withdraw_invitation = PaperWithdrawInvitation(conference, note, reveal_submission)
            return self.client.post_invitation(withdraw_invitation)

        invitations = tools.concurrent_requests(post_invitation, notes, desc='set_withdraw_invitation')

        return invitations

    def set_desk_reject_invitation(self, conference, reveal_authors, reveal_submission, email_pcs, hide_fields=None):

        invitations = []

        self.client.post_invitation(DeskRejectedSubmissionInvitation(conference, reveal_authors, reveal_submission, hide_fields))
        notes = list(conference.get_submissions())

        def post_invitation(note):
            desk_reject_invitation = PaperDeskRejectInvitation(conference, note, reveal_authors, reveal_submission, email_pcs, hide_fields=hide_fields)
            return self.client.post_invitation(desk_reject_invitation)

        invitations = tools.concurrent_requests(post_invitation, notes, desc='set_desk_reject_invitation')

        return invitations

    def set_review_invitation(self, conference, notes):
        invitations = []
        self.client.post_invitation(ReviewInvitation(conference))

        def set_review_invitation(note):
            invitation = self.client.post_invitation(PaperReviewInvitation(conference, note))
            self.__update_readers(note, invitation)
            return invitation

        invitations = tools.concurrent_requests(set_review_invitation, notes, desc='set_review_invitation')

        return invitations

    def set_ethics_review_invitation(self, conference, notes):
        print('post invitations')
        invitations = []
        self.client.post_invitation(EthicsReviewInvitation(conference))
        print('post invitation notes')
        for note in tqdm(notes, total=len(notes), desc='set_ethics_review_invitation'):
            invitation = self.client.post_invitation(PaperEthicsReviewInvitation(conference, note))
            self.__update_readers(note, invitation)
            invitations.append(invitation)

        return invitations        

    def set_review_rebuttal_invitation(self, conference):
        submissions = conference.get_submissions(details='directReplies')
        notes = []
        if conference.review_rebuttal_stage.single_rebuttal:
            notes = submissions 
        else:
            notes = [openreview.Note.from_json(reply) for submission in submissions for reply in submission.details['directReplies'] if conference.review_stage.name in reply['invitation']]

        invitations = []
        regex=conference.get_anon_reviewer_id(number='.*', anon_id='.*')
        self.client.post_invitation(RebuttalInvitation(conference))
        for note in tqdm(notes, desc='set_review_rebuttal_invitation'):
            if conference.review_rebuttal_stage.single_rebuttal:
                invitation = self.client.post_invitation(PaperRebuttalInvitation(conference, note))
                self.__update_readers(note, invitation)
                invitations.append(invitation)                
            elif re.search(regex, note.signatures[0]):
                invitation = self.client.post_invitation(PaperReviewRebuttalInvitation(conference, note))
                invitations.append(invitation)

        return invitations

    def set_review_revision_invitation(self, conference, reviews):
        invitations = []
        regex=conference.get_anon_reviewer_id(number='.*', anon_id='.*')
        self.client.post_invitation(ReviewRevisionInvitation(conference))
        for note in tqdm(reviews, desc='set_review_revision_invitation'):
            if re.search(regex, note.signatures[0]):
                invitation = self.client.post_invitation(PaperReviewRevisionInvitation(conference, note))
                invitations.append(invitation)

        return invitations

    def set_review_rating_invitation(self, conference, reviews):
        invitations = []
        regex=conference.get_anon_reviewer_id(number='.*', anon_id='.*')
        self.client.post_invitation(ReviewRatingInvitation(conference))
        for note in tqdm(reviews, desc='set_review_rating_invitation'):
            if re.search(regex, note.signatures[0]):
                invitation = self.client.post_invitation(PaperReviewRatingInvitation(conference, note))
                invitations.append(invitation)

        return invitations

    def set_meta_review_invitation(self, conference, notes):
        self.client.post_invitation(MetaReviewInvitation(conference))
        def post_invitation(note):
            invitation = self.client.post_invitation(PaperMetaReviewInvitation(conference, note))
            self.__update_readers(note, invitation)
            return invitation

        return tools.concurrent_requests(post_invitation, notes, desc='set_meta_review_invitation')

    def set_meta_review_revision_invitation(self, conference, metareviews):
        invitations = []
        self.client.post_invitation(MetaReviewRevisionInvitation(conference))
        regex=conference.get_anon_area_chair_id(number='.*', anon_id='.*')

        def set_meta_review_revision_invitation(note):
            if re.search(regex, note.signatures[0]):
                invitation = self.client.post_invitation(PaperMetaReviewRevisionInvitation(conference, note))
                return invitation
        
        invitations = tools.concurrent_requests(set_meta_review_revision_invitation, metareviews, desc='set_meta_review_revision_invitation')

        return invitations

    def set_decision_invitation(self, conference, notes):
        self.client.post_invitation(DecisionInvitation(conference))
        def post_invitation(note):
            invitation = self.client.post_invitation(PaperDecisionInvitation(conference, note))
            self.__update_readers(note, invitation)
            return invitation

        invitations = tools.concurrent_requests(post_invitation, notes)

        return invitations

    def set_revise_submission_invitation(self, conference, notes, content):
        self.client.post_invitation(SubmissionRevisionInvitation(conference, content))
        return tools.concurrent_requests(
            lambda note : self.client.post_invitation(PaperSubmissionRevisionInvitation(conference, note, content)),
            notes,
            desc='set_revise_submission_invitation'
        )

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
                'values': [
                    conference.get_id()
                ]
            },
            'signatures': {
                'values-regex': '\\(anonymous\\)'
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

        role = options.get('reviewers_name', 'Reviewers')
        conf_id = conference.get_id()
        total_prefix = conf_id + '/' + role
        invitation_id=conference.get_invitation_id('Reduced_Load', prefix = total_prefix)
        current_invitation=openreview.tools.get_invitation(self.client, id = invitation_id)

        with open(os.path.join(os.path.dirname(__file__), 'templates/recruitReducedLoadProcess.js')) as f:
            content = f.read()
            content = content.replace("var SHORT_PHRASE = '';", f'var SHORT_PHRASE = "{conference.get_short_name()}";')
            content = content.replace("var REVIEWER_NAME = '';", "var REVIEWER_NAME = '" + options.get('reviewers_name', 'Reviewers').replace('_', ' ')[:-1] + "';")
            content = content.replace("var REVIEWERS_ACCEPTED_ID = '';", "var REVIEWERS_ACCEPTED_ID = '" + options.get('reviewers_accepted_id') + "';")
            content = content.replace("var REVIEWERS_DECLINED_ID = '';", "var REVIEWERS_DECLINED_ID = '" + options.get('reviewers_declined_id') + "';")
            content = content.replace("var HASH_SEED = '';", "var HASH_SEED = '" + options.get('hash_seed') + "';")

            reduced_load_invitation = openreview.Invitation(
                    id = invitation_id,
                    duedate = tools.datetime_millis(options.get('due_date', datetime.datetime.utcnow())),
                    readers = ['everyone'],
                    nonreaders = [],
                    invitees = ['everyone'],
                    noninvitees = [],
                    writers = [conference.get_id()],
                    signatures = [conference.get_id()],
                    reply = reduced_load_invitation_reply,
                    process_string = content,
                    web_string = current_invitation.web if current_invitation else None)
            return self.client.post_invitation(reduced_load_invitation)

    def set_reviewer_recruiter_invitation(self, conference, options = {}):

        default_reply = {
            'forum': None,
            'replyto': None,
            'readers': {
                'values-copied': [
                    conference.get_id(),
                    '{content.user}'
                ]
            },
            'signatures': {
                'values-regex': '\\(anonymous\\)'
            },
            'writers': {
                'values': [
                    conference.get_id(),
                    '(anonymous)'
                ]
            },
            'content': default_content.recruitment
        }
        reply = self.__build_options(default_reply, options.get('reply', {}))

        invitation_id=conference.get_recruitment_id(conference.get_committee_id(name=options.get('reviewers_name', 'Reviewers')))
        current_invitation=openreview.tools.get_invitation(self.client, id = invitation_id)

        reduced_load = options.get('reduced_load_on_decline', None)
        accept_template = options.get('accept_recruitment_template')

        if reduced_load and conference.use_recruitment_template:
            reply['content']['reduced_load'] = {
                "description": "Please select the number of submissions that you would be comfortable reviewing.",
                "required": False,
                "value-dropdown": reduced_load,
                "order": 5
            }

        post_proces_template = 'recruit_reviewers_post_process.py' if conference.use_recruitment_template else 'legacy_recruit_reviewers_post_process.py'
        with open(os.path.join(os.path.dirname(__file__), 'templates/recruit_reviewers_pre_process.py')) as pre:
            with open(os.path.join(os.path.dirname(__file__), 'templates/' + post_proces_template)) as post:
                pre_content = pre.read()
                post_content = post.read()
                pre_content = pre_content.replace("PAPER_REGEX = ''", f"PAPER_REGEX = '{conference.id}/Paper'")
                pre_content = pre_content.replace("REVIEWERS_NAME = ''", "REVIEWERS_NAME = '" + options.get('reviewers_name', 'Reviewers') + "'")
                pre_content = pre_content.replace("CHECK_DECLINE = False", "CHECK_DECLINE = True")
                post_content = post_content.replace("SHORT_PHRASE = ''", f'SHORT_PHRASE = "{conference.get_short_name()}"')
                post_content = post_content.replace("CONFERENCE_NAME = ''", f'CONFERENCE_NAME = "{conference.get_id()}"')
                post_content = post_content.replace("REVIEWER_NAME = ''", "REVIEWER_NAME = '" + options.get('reviewers_name', 'Reviewers').replace('_', ' ')[:-1] + "'")
                post_content = post_content.replace("REVIEWERS_ACCEPTED_ID = ''", "REVIEWERS_ACCEPTED_ID = '" + options.get('reviewers_accepted_id') + "'")
                pre_content = pre_content.replace("REVIEWERS_INVITED_ID = ''", "REVIEWERS_INVITED_ID = '" + options.get('reviewers_invited_id') + "'")
                post_content = post_content.replace("REVIEWERS_INVITED_ID = ''", "REVIEWERS_INVITED_ID = '" + options.get('reviewers_invited_id') + "'")
                post_content = post_content.replace("REVIEWERS_DECLINED_ID = ''", "REVIEWERS_DECLINED_ID = '" + options.get('reviewers_declined_id') + "'")
                if not options.get('allow_overlap_official_committee'):
                    if options.get('reviewers_name') == 'Reviewers' and conference.use_area_chairs:
                        post_content = post_content.replace("AREA_CHAIR_NAME = ''", "AREA_CHAIR_NAME = 'Area Chair'")
                        post_content = post_content.replace("AREA_CHAIRS_ACCEPTED_ID = ''", "AREA_CHAIRS_ACCEPTED_ID = '" + conference.get_area_chairs_id() + "'")
                    elif options.get('reviewers_name') == 'Area_Chairs':
                        post_content = post_content.replace("AREA_CHAIR_NAME = ''", "AREA_CHAIR_NAME = 'Reviewer'")
                        post_content = post_content.replace("AREA_CHAIRS_ACCEPTED_ID = ''", "AREA_CHAIRS_ACCEPTED_ID = '" + conference.get_reviewers_id() + "'")
                pre_content = pre_content.replace("HASH_SEED = ''", "HASH_SEED = '" + options.get('hash_seed') + "'")
                post_content = post_content.replace("HASH_SEED = ''", "HASH_SEED = '" + options.get('hash_seed') + "'")
                if reduced_load:
                    post_content = post_content.replace("REDUCED_LOAD_INVITATION_NAME = ''", "REDUCED_LOAD_INVITATION_NAME = 'Reduced_Load'")
                if accept_template:
                    email_template = accept_template
                    email_template = email_template.replace('{{reviewer_name}}', '{REVIEWER_NAME}')
                    post_content = post_content.replace("ACCEPT_EMAIL_TEMPLATE = ''", "ACCEPT_EMAIL_TEMPLATE = f'''" + email_template + "'''")
                invitation = openreview.Invitation(id = invitation_id,
                    duedate = tools.datetime_millis(options.get('due_date', datetime.datetime.utcnow())),
                    readers = ['everyone'],
                    nonreaders = [],
                    invitees = ['everyone'],
                    noninvitees = [],
                    writers = [conference.get_id()],
                    signatures = [conference.get_id()],
                    reply = reply,
                    process_string = post_content,
                    preprocess= pre_content,
                    web_string = current_invitation.web if current_invitation else None)

                return self.client.post_invitation(invitation)

    def set_recommendation_invitation(self, conference, start_date, due_date, total_recommendations):

        invitation_id=conference.get_recommendation_id()
        current_invitation=openreview.tools.get_invitation(self.client, id = invitation_id)

        recommendation_invitation = openreview.Invitation(
            id = invitation_id,
            cdate = tools.datetime_millis(start_date),
            duedate = tools.datetime_millis(due_date),
            expdate = tools.datetime_millis(due_date + datetime.timedelta(minutes = SHORT_BUFFER_MIN)) if due_date else None,
            readers = [conference.get_program_chairs_id(), conference.get_area_chairs_id()],
            writers = [conference.get_id()],
            signatures = [conference.get_id()],
            invitees = [conference.get_program_chairs_id(), conference.get_area_chairs_id(), conference.support_user],
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
                'writers': {
                    'description': 'The users who will be allowed to edit the above content.',
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
            },
            web_string = current_invitation.web if current_invitation else None
        )

        return self.client.post_invitation(recommendation_invitation)

    def set_paper_ranking_invitation(self, conference, group_id, start_date, due_date):

        readers = {
            'description': 'The users who will be allowed to read the above content.',
            'values-copied': ['{signatures}']
        }
        signatures_regex = '~.*'

        if group_id in [conference.get_area_chairs_id(), conference.get_reviewers_id()]:
            readers['values-copied'] = [conference.id, '{signatures}']
            signatures_regex = conference.get_anon_area_chair_id(number='.*', anon_id='.*')

            if group_id == conference.get_reviewers_id() and conference.use_area_chairs:
                readers = {
                    'description': 'The users who will be allowed to read the above content.',
                    'values-regex': conference.get_id() + '|' + conference.get_area_chairs_id(number='.*') + '|~.*'
                }

        reviewer_paper_ranking_invitation = openreview.Invitation(
            id = conference.get_invitation_id('Paper_Ranking', prefix=group_id),
            cdate = tools.datetime_millis(start_date),
            duedate = tools.datetime_millis(due_date),
            expdate = tools.datetime_millis(due_date + datetime.timedelta(minutes = SHORT_BUFFER_MIN)) if due_date else None,
            readers = [conference.get_program_chairs_id(), group_id],
            writers = [conference.get_id()],
            signatures = [conference.get_id()],
            invitees = [conference.get_program_chairs_id(), group_id, conference.support_user],
            multiReply = False,
            reply = {
                "invitation": conference.get_submission_id(),
                'readers': readers,
                'signatures': {
                    'description': 'How your identity will be displayed with the above content.',
                    'values-regex': signatures_regex
                },
                'content': {
                    "tag": {
                        "description": "Select value",
                        "order": 1,
                        "value-regex": r'No Ranking|[0-9]+\sof\s[0-9]+',
                        "required": True
                    }
                }
            }
        )

        return self.client.post_invitation(reviewer_paper_ranking_invitation)

    def __set_registration_invitation(self, conference, name, start_date, due_date, additional_fields, remove_fields, instructions, title, committee_id, committee_name):

        readers = [conference.id, committee_id]

        # Create super invitation with a webfield
        registration_parent_invitation = openreview.Invitation(
            id = conference.get_invitation_id(name=f'{name}_Form', prefix=committee_id),
            readers = ['everyone'],
            writers = [conference.get_id()],
            signatures = [conference.get_id()],
            invitees = [conference.get_id(), conference.support_user],
            reply = {
                'forum': None,
                'replyto': None,
                'readers': {'values': readers},
                'writers': {'values': [conference.get_id()]},
                'signatures': {'values': [conference.get_id()]},
                'content': {
                    'title': {
                        'value-regex': '[\\S\\s]{0,2500}'
                    },
                    'instructions': {
                        'order': 1,
                        'value-regex': '[\\S\\s]{0,250000}'
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
                'title': title if title else committee_name + ' Information'
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

        for field in remove_fields:
            if field in registration_content:
                del registration_content[field]

        registration_invitation = self.client.post_invitation(openreview.Invitation(
            id = conference.get_invitation_id(name = name, prefix = committee_id),
            cdate = tools.datetime_millis(start_date) if start_date else None,
            duedate = tools.datetime_millis(due_date) if due_date else None,
            expdate = tools.datetime_millis(due_date),
            multiReply = False,
            readers = readers,
            writers = [conference.get_id()],
            signatures = [conference.get_id()],
            invitees = [committee_id, conference.support_user],
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

    def set_registration_invitation(self, conference, stage):

        if conference.use_senior_area_chairs and stage.committee_id == conference.get_senior_area_chairs_id():
            return self.__set_registration_invitation(conference=conference,
                name=stage.name,
                start_date=stage.start_date,
                due_date=stage.due_date,
                additional_fields=stage.additional_fields,
                remove_fields=stage.remove_fields,
                instructions=stage.instructions,
                title=stage.title,
                committee_id=conference.get_senior_area_chairs_id(),
                committee_name=conference.get_senior_area_chairs_name(pretty=True)
            )

        if conference.use_area_chairs and stage.committee_id == conference.get_area_chairs_id():
            return self.__set_registration_invitation(conference=conference,
                name=stage.name,
                start_date=stage.start_date,
                due_date=stage.due_date,
                additional_fields=stage.additional_fields,
                remove_fields=stage.remove_fields,
                instructions=stage.instructions,
                title=stage.title,
                committee_id=conference.get_area_chairs_id(),
                committee_name=conference.get_area_chairs_name(pretty=True)
            )

        if stage.committee_id == conference.get_reviewers_id():
            return self.__set_registration_invitation(conference=conference,
                name=stage.name,
                start_date=stage.start_date,
                due_date=stage.due_date,
                additional_fields=stage.additional_fields,
                remove_fields=stage.remove_fields,
                instructions=stage.instructions,
                title=stage.title,
                committee_id=conference.get_reviewers_id(),
                committee_name=conference.get_reviewers_name(pretty=True)
            )
        if stage.committee_id == conference.get_authors_id():
            return self.__set_registration_invitation(conference=conference,
                name=stage.name,
                start_date=stage.start_date,
                due_date=stage.due_date,
                additional_fields=stage.additional_fields,
                remove_fields=stage.remove_fields,
                instructions=stage.instructions,
                title=stage.title,
                committee_id=conference.get_authors_id(),
                committee_name=conference.get_authors_name(pretty=True)
            )

    def set_paper_group_invitation(self, conference, committee_id, with_process_function=False):

        return self.client.post_invitation(PaperGroupInvitation(conference, committee_id, with_process_function))

    def set_paper_recruitment_invitation(self, conference, invitation_id, committee_id, invited_committee_name, hash_seed, assignment_title=None, due_date=None, invited_label='Invited', accepted_label='Accepted', declined_label='Declined', proposed=False):

        current_invitation=openreview.tools.get_invitation(self.client, id = invitation_id)
        ## Use a simpler process function when the recruitment comes from proposed assignments: no conflict check, no profile check, etc.
        process_file='templates/simple_paper_recruitment_process.py' if proposed else 'templates/paper_recruitment_process.py'
        web=current_invitation.web if current_invitation else None
        return self.client.post_invitation(PaperRecruitmentInvitation(conference, invitation_id, committee_id, invited_committee_name, hash_seed, assignment_title, due_date, web, process_file, invited_label, accepted_label, declined_label))

    def set_assignment_invitation(self, conference, committee_id):

        invitation = self.client.get_invitation(conference.get_paper_assignment_id(committee_id, deployed=True))
        is_area_chair = committee_id == conference.get_area_chairs_id() or committee_id.split("/")[-1] in conference.area_chair_roles
        is_senior_area_chair = committee_id == conference.get_senior_area_chairs_id() or committee_id.split("/")[-1] in conference.senior_area_chair_roles
        is_reviewer = committee_id == conference.get_reviewers_id()
        is_ethics_reviewer = committee_id == conference.get_ethics_reviewers_id()

        review_invitation_name = conference.review_stage.name
        anon_regex = conference.get_anon_reviewer_id('{number}', '.*')
        paper_group_id = conference.get_reviewers_id(number='{number}')
        group_name = conference.get_reviewers_name(pretty=True)
        if is_area_chair:
            review_invitation_name = conference.meta_review_stage.name
            anon_regex = conference.get_anon_area_chair_id('{number}', '.*')
            paper_group_id = conference.get_area_chairs_id(number='{number}')
            group_name = conference.get_area_chairs_name(pretty=True)
        if is_ethics_reviewer:
            review_invitation_name = conference.ethics_review_stage.name
            anon_regex = conference.get_anon_reviewer_id('{number}', '.*', conference.ethics_reviewers_name)
            paper_group_id = conference.get_ethics_reviewers_id(number='{number}')
            group_name = conference.get_ethics_reviewers_name(pretty=True)

        if is_senior_area_chair:
            with open(os.path.join(os.path.dirname(__file__), 'templates/sac_assignment_post_process.py')) as post:
                post_content = post.read()
                post_content = post_content.replace("CONFERENCE_ID = ''", "CONFERENCE_ID = '" + conference.id + "'")
                post_content = post_content.replace("PAPER_GROUP_ID = ''", "PAPER_GROUP_ID = '" + conference.get_senior_area_chairs_id(number='{number}') + "'")
                post_content = post_content.replace("AC_ASSIGNMENT_INVITATION_ID = ''", "AC_ASSIGNMENT_INVITATION_ID = '" + conference.get_paper_assignment_id(conference.get_area_chairs_id(), deployed=True) + "'")
                invitation.process=post_content
                invitation.signatures=[conference.get_program_chairs_id()] ## Program Chairs can see the reviews
                return self.client.post_invitation(invitation)

        with open(os.path.join(os.path.dirname(__file__), 'templates/assignment_pre_process.py')) as pre:
            pre_content = pre.read()
            pre_content = pre_content.replace("REVIEW_INVITATION_ID = ''", "REVIEW_INVITATION_ID = '" + conference.get_invitation_id(review_invitation_name, '{number}') + "'")
            pre_content = pre_content.replace("ANON_REVIEWER_REGEX = ''", "ANON_REVIEWER_REGEX = '" + anon_regex + "'")
            with open(os.path.join(os.path.dirname(__file__), 'templates/assignment_post_process.py')) as post:
                post_content = post.read()
                post_content = post_content.replace("CONFERENCE_ID = ''", "CONFERENCE_ID = '" + conference.id + "'")
                post_content = post_content.replace("SHORT_PHRASE = ''", f'SHORT_PHRASE = "{conference.get_short_name()}"')
                post_content = post_content.replace("PAPER_GROUP_ID = ''", "PAPER_GROUP_ID = '" + paper_group_id + "'")
                post_content = post_content.replace("GROUP_NAME = ''", "GROUP_NAME = '" + group_name + "'")
                post_content = post_content.replace("GROUP_ID = ''", "GROUP_ID = '" + committee_id + "'")
                if conference.use_senior_area_chairs and is_area_chair:
                    post_content = post_content.replace("SYNC_SAC_ID = ''", "SYNC_SAC_ID = '" + conference.get_senior_area_chairs_id(number='{number}') + "'")
                    post_content = post_content.replace("SAC_ASSIGNMENT_INVITATION_ID = ''", "SAC_ASSIGNMENT_INVITATION_ID = '" + conference.get_paper_assignment_id(conference.get_senior_area_chairs_id(), deployed=True) + "'")
                invitation.process=post_content
                invitation.preprocess=pre_content
                invitation.signatures=[conference.get_program_chairs_id()] ## Program Chairs can see the reviews
                return self.client.post_invitation(invitation)
