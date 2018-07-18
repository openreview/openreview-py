'''
ICML 2019 demo configuration
https://icml.cc/Conferences/2019
Monday June 10 - Saturday June 15, 2019
'''

import openreview
from openreview import invitations
import os

# group ids
CONFERENCE_ID = 'ICML.cc/2019/Conference'
SHORT_PHRASE = 'ICML 2019'

PROGRAM_CHAIRS_ID = CONFERENCE_ID + '/Program_Chairs'
AREA_CHAIRS_ID = CONFERENCE_ID + '/Area_Chairs'
AREA_CHAIRS_INVITED_ID = AREA_CHAIRS_ID + '/Invited'
AREA_CHAIRS_DECLINED_ID = AREA_CHAIRS_ID + '/Declined'

REVIEWERS_ID = CONFERENCE_ID + '/Reviewers'
REVIEWERS_INVITED_ID = REVIEWERS_ID + '/Invited'
REVIEWERS_DECLINED_ID = REVIEWERS_ID + '/Declined'

# invitation ids
SUBMISSION_ID = CONFERENCE_ID + '/-/Submission'
BLIND_SUBMISSION_ID = CONFERENCE_ID + '/-/Blind_Submission'

RECRUIT_AREA_CHAIRS_ID = CONFERENCE_ID + '/-/Recruit_Area_Chairs'
RECRUIT_REVIEWERS_ID = CONFERENCE_ID + '/-/Recruit_Reviewers'

REVIEWER_METADATA_ID = CONFERENCE_ID + '/-/Reviewer_Metadata'
AREA_CHAIR_METADATA_ID = CONFERENCE_ID + '/-/Area_Chair_Metadata'

# template strings
PAPER_TEMPLATE_STR = CONFERENCE_ID + '/Paper<number>'
PAPER_REVIEWERS_TEMPLATE_STR = PAPER_TEMPLATE_STR + '/Reviewers'
PAPER_AREA_CHAIRS_TEMPLATE_STR = PAPER_TEMPLATE_STR + '/Area_Chairs'
PAPER_AUTHORS_TEMPLATE_STR = PAPER_TEMPLATE_STR + '/Authors'
PAPER_REVIEW_NONREADERS_TEMPLATE_STR = PAPER_TEMPLATE_STR + '/Review_Nonreaders'
PAPER_COMMENT_NONREADERS_TEMPLATE_STR = PAPER_TEMPLATE_STR + '/Comment_Nonreaders'

PAPER_REVIEWERS_UNSUBMITTED_TEMPLATE_STR = PAPER_REVIEWERS_TEMPLATE_STR + '/Unsubmitted'
PAPER_REVIEWERS_SUBMITTED_TEMPLATE_STR = PAPER_REVIEWERS_TEMPLATE_STR + '/Submitted'

OPEN_COMMENT_TEMPLATE_STR = CONFERENCE_ID + '/-/Paper<number>/Open_Comment'
OFFICIAL_COMMENT_TEMPLATE_STR = CONFERENCE_ID + '/-/Paper<number>/Official_Comment'
OFFICIAL_REVIEW_TEMPLATE_STR = CONFERENCE_ID + '/-/Paper<number>/Official_Review'

# The groups corresponding to these regexes will get automatically created upon assignment
PAPER_AREA_CHAIRS_TEMPLATE_REGEX = PAPER_TEMPLATE_STR + '/Area_Chair[0-9]+'
PAPER_ANONREVIEWERS_TEMPLATE_REGEX = PAPER_TEMPLATE_STR + '/AnonReviewer[0-9]+'

# Email templates
HASH_SEED = "2810398440804348173"
RECRUIT_MESSAGE_SUBJ = 'ICML 2019: Invitation to Review'
RECRUIT_REVIEWERS_MESSAGE = '''Dear {name},

You have been invited to serve as a reviewer for the ICML 2019 Conference.

To ACCEPT the invitation, please click on the following link:

{accept_url}

To DECLINE the invitation, please click on the following link:

{decline_url}

We  hope you will be able to accept our invitation and help us select a high quality program for ICML 2019.

Best regards,
The ICML 2019 Program Chairs

'''

RECRUIT_AREA_CHAIRS_MESSAGE = '''Dear {name},

You have been invited to serve as an area chair for the ICML 2019 Conference.

To ACCEPT the invitation, please click on the following link:

{accept_url}

To DECLINE the invitation, please click on the following link:

{decline_url}

We  hope you will be able to accept our invitation and help us select a high quality program for ICML 2019.

Best regards,
The ICML 2019 Program Chairs

'''


# Deadlines
SUBMISSION_DEADLINE = openreview.tools.timestamp_GMT(year=2018, month=7, day=1)
ADD_BID_DEADLINE = openreview.tools.timestamp_GMT(year=2018, month=7, day=7)
OFFICIAL_REVIEW_DEADLINE = openreview.tools.timestamp_GMT(year=2018, month=7, day=14)



# Global group definitions
conference = openreview.Group(**{
    'id': CONFERENCE_ID,
    'readers':['everyone'],
    'writers': [CONFERENCE_ID],
    'signatures': [],
    'signatories': [CONFERENCE_ID],
    'members': [],
    'web': os.path.abspath('../webfield/homepage.js')
})

program_chairs = openreview.Group(**{
    'id': PROGRAM_CHAIRS_ID,
    'readers':[CONFERENCE_ID, PROGRAM_CHAIRS_ID],
    'writers': [],
    'signatures': [],
    'signatories': [CONFERENCE_ID, PROGRAM_CHAIRS_ID],
    'members': [],
    'web': os.path.abspath('../webfield/programchairWebfield.js')
})

area_chairs = openreview.Group(**{
    'id': AREA_CHAIRS_ID,
    'readers':[CONFERENCE_ID, PROGRAM_CHAIRS_ID, AREA_CHAIRS_ID],
    'writers': [CONFERENCE_ID],
    'signatures': [CONFERENCE_ID],
    'signatories': [CONFERENCE_ID],
    'members': [],
    'web': os.path.abspath('../webfield/areachairWebfield.js')
})

area_chairs_invited = openreview.Group(**{
    'id': AREA_CHAIRS_INVITED_ID,
    'readers':[CONFERENCE_ID, PROGRAM_CHAIRS_ID],
    'writers': [CONFERENCE_ID],
    'signatures': [CONFERENCE_ID],
    'signatories': [CONFERENCE_ID],
    'members': [],
})

area_chairs_declined = openreview.Group(**{
    'id': AREA_CHAIRS_DECLINED_ID,
    'readers':[CONFERENCE_ID, PROGRAM_CHAIRS_ID],
    'writers': [CONFERENCE_ID],
    'signatures': [CONFERENCE_ID],
    'signatories': [CONFERENCE_ID],
    'members': [],
})

reviewers = openreview.Group(**{
    'id': REVIEWERS_ID,
    'readers':[CONFERENCE_ID, PROGRAM_CHAIRS_ID, AREA_CHAIRS_ID, REVIEWERS_ID],
    'writers': [CONFERENCE_ID],
    'signatures': [CONFERENCE_ID],
    'signatories': [CONFERENCE_ID],
    'members': [],
})

reviewers_invited = openreview.Group(**{
    'id': REVIEWERS_INVITED_ID,
    'readers':[CONFERENCE_ID, PROGRAM_CHAIRS_ID],
    'writers': [CONFERENCE_ID],
    'signatures': [CONFERENCE_ID],
    'signatories': [CONFERENCE_ID],
    'members': [],
})

reviewers_declined = openreview.Group(**{
    'id': REVIEWERS_DECLINED_ID,
    'readers':[CONFERENCE_ID, PROGRAM_CHAIRS_ID],
    'writers': [CONFERENCE_ID],
    'signatures': [CONFERENCE_ID],
    'signatories': [CONFERENCE_ID],
    'members': [],
})


# Configure paper submissions
submission_inv = invitations.Submission(
    id = SUBMISSION_ID,
    conference_id = CONFERENCE_ID,
    duedate = SUBMISSION_DEADLINE,
    process = os.path.abspath('../process/submissionProcess.js'),
    reply_params = {
        'readers': {
            'values-copied': [
                CONFERENCE_ID,
                '{content.authorids}',
                '{signatures}'
            ]
        },
        'signatures': {
            'values-regex': '|'.join(['~.*', CONFERENCE_ID])
        },
        'writers': {
            'values-regex': '|'.join(['~.*', CONFERENCE_ID])
        }
    }
)

blind_submission_inv = invitations.Submission(
    id = BLIND_SUBMISSION_ID,
    conference_id = CONFERENCE_ID,
    duedate = SUBMISSION_DEADLINE,
    mask = {
        'authors': {
            'values': ['Anonymous']
        },
        'authorids': {
            'values-regex': '.*'
        }
    },
    reply_params = {
        'signatures': {
            'values': [CONFERENCE_ID]},
        'readers': {
            'values': ['everyone']
        }
    }
)


# Configure AC and reviewer recruitment
recruit_area_chairs = invitations.RecruitReviewers(
    id = RECRUIT_AREA_CHAIRS_ID,
    conference_id = CONFERENCE_ID,
    process = os.path.abspath('../process/recruitAreaChairsProcess.js'),
    web = os.path.abspath('../webfield/recruitResponseWebfield.js')
)

recruit_reviewers = invitations.RecruitReviewers(
    id = RECRUIT_REVIEWERS_ID,
    conference_id = CONFERENCE_ID,
    process = os.path.abspath('../process/recruitReviewersProcess.js'),
    web = os.path.abspath('../webfield/recruitResponseWebfield.js')
)


# Configure bidding
add_bid = invitations.AddBid(
    conference_id = CONFERENCE_ID,
    duedate = ADD_BID_DEADLINE,
    completion_count = 50,
    inv_params = {
        'readers': [
            CONFERENCE_ID,
            PROGRAM_CHAIRS_ID,
            REVIEWERS_ID,
            AREA_CHAIRS_ID
        ],
        'invitees': [],
        'web': os.path.abspath('../webfield/bidWebfield.js')
    },

)


# Configure AC recommendations
ac_recommendation_template = {
        'id': CONFERENCE_ID + '/-/Paper<number>/Recommend_Reviewer',
        'invitees': [],
        'multiReply': True,
        'readers': ['everyone'],
        'writers': [CONFERENCE_ID],
        'signatures': [CONFERENCE_ID],
        'duedate': openreview.tools.timestamp_GMT(year=2018, month=6, day=6),
        'reply': {
            'forum': '<forum>',
            'replyto': '<forum>',
            'readers': {
                'description': 'The users who will be allowed to read the above content.',
                'values-copied': [CONFERENCE_ID, '{signatures}']
            },
            'signatures': {
                'description': 'How your identity will be displayed with the above content.',
                'values-regex': '~.*'
            },
            'content': {
                'tag': {
                    'description': 'Recommend a reviewer to review this paper',
                    'order': 1,
                    'required': True,
                    'values-url': '/groups?id=' + REVIEWERS_ID
                }
            }
        }
    }


# Metadata and matching stuff
reviewer_metadata = openreview.Invitation(**{
    'id': REVIEWER_METADATA_ID,
    'readers': [
        CONFERENCE_ID,
        PROGRAM_CHAIRS_ID
    ],
    'writers': [CONFERENCE_ID],
    'signatures': [CONFERENCE_ID],
    'reply': {
        'forum': None,
        'replyto': None,
        'invitation': BLIND_SUBMISSION_ID,
        'readers': {
            'values': [
                CONFERENCE_ID,
                PROGRAM_CHAIRS_ID
            ]
        },
        'writers': {
            'values': [CONFERENCE_ID]
        },
        'signatures': {
            'values': [CONFERENCE_ID]},
        'content': {}
    }
})

ASSIGNMENT_INV_ID = CONFERENCE_ID + '/-/Paper_Assignment'

assignment_inv = openreview.Invitation(**{
    'id': ASSIGNMENT_INV_ID,
    'readers': [CONFERENCE_ID],
    'writers': [CONFERENCE_ID],
    'signatures': [CONFERENCE_ID],
    'reply': {
        'forum': None,
        'replyto': None,
        'invitation': BLIND_SUBMISSION_ID,
        'readers': {'values': [CONFERENCE_ID]},
        'writers': {'values': [CONFERENCE_ID]},
        'signatures': {'values': [CONFERENCE_ID]},
        'content': {}
    }
})

CONFIG_INV_ID = CONFERENCE_ID + '/-/Assignment_Configuration'

config_inv = openreview.Invitation(**{
    'id': CONFIG_INV_ID,
    'readers': [CONFERENCE_ID],
    'writers': [CONFERENCE_ID],
    'signatures': [CONFERENCE_ID],
    'reply': {
        'forum': None,
        'replyto': None,
        'invitation': None,
        'readers': {'values': [CONFERENCE_ID]},
        'writers': {'values': [CONFERENCE_ID]},
        'signatures': {'values': [CONFERENCE_ID]},
        'content': {}
    }

})


# Per-paper group template definitions
papergroup_template = openreview.Group(**{
    'id': PAPER_TEMPLATE_STR,
    'readers':[CONFERENCE_ID],
    'writers': [CONFERENCE_ID],
    'signatures': [CONFERENCE_ID],
    'signatories': [CONFERENCE_ID],
    'members': [],
})


reviewers_template = openreview.Group(**{
    'id': PAPER_REVIEWERS_TEMPLATE_STR,
    'readers':[
        CONFERENCE_ID,
        PROGRAM_CHAIRS_ID
    ],
    'writers': [CONFERENCE_ID],
    'signatures': [CONFERENCE_ID],
    'signatories': [CONFERENCE_ID],
    'members': [],
})

area_chairs_template = openreview.Group(**{
    'id': PAPER_REVIEWERS_TEMPLATE_STR,
    'readers':[
        CONFERENCE_ID,
        PROGRAM_CHAIRS_ID
    ],
    'writers': [CONFERENCE_ID],
    'signatures': [CONFERENCE_ID],
    'signatories': [CONFERENCE_ID],
    'members': [],
})

review_nonreaders_template = openreview.Group(**{
    'id': PAPER_REVIEW_NONREADERS_TEMPLATE_STR,
    'readers':[
        CONFERENCE_ID,
        PROGRAM_CHAIRS_ID
    ],
    'writers': [CONFERENCE_ID],
    'signatures': [CONFERENCE_ID],
    'signatories': [CONFERENCE_ID],
    'members': [],
})

comment_nonreaders_template = openreview.Group(**{
    'id': PAPER_COMMENT_NONREADERS_TEMPLATE_STR,
    'readers':[
        CONFERENCE_ID,
        PROGRAM_CHAIRS_ID
    ],
    'writers': [CONFERENCE_ID],
    'signatures': [CONFERENCE_ID],
    'signatories': [CONFERENCE_ID],
    'members': [],
})

reviewers_unsubmitted_template = openreview.Group(**{
    'id': PAPER_REVIEWERS_UNSUBMITTED_TEMPLATE_STR,
    'readers':[
        CONFERENCE_ID,
        PROGRAM_CHAIRS_ID,
        PAPER_AREA_CHAIRS_TEMPLATE_STR
    ],
    'writers': [CONFERENCE_ID],
    'signatures': [CONFERENCE_ID],
    'signatories': [CONFERENCE_ID],
    'members': [],
})

reviewers_submitted_template = openreview.Group(**{
    'id': PAPER_REVIEWERS_SUBMITTED_TEMPLATE_STR,
    'readers':[
        CONFERENCE_ID,
        PROGRAM_CHAIRS_ID,
        PAPER_AREA_CHAIRS_TEMPLATE_STR
    ],
    'writers': [CONFERENCE_ID],
    'signatures': [CONFERENCE_ID],
    'signatories': [CONFERENCE_ID],
    'members': [],
})


# Configure the invitations that will be attached on a per-paper basis
# These are constructed using templates.
official_comment_template = {
    'id': OFFICIAL_COMMENT_TEMPLATE_STR,
    'readers': ['everyone'],
    'writers': [CONFERENCE_ID],
    'invitees': [
        PAPER_REVIEWERS_TEMPLATE_STR,
        PAPER_AUTHORS_TEMPLATE_STR,
        PAPER_AREA_CHAIRS_TEMPLATE_STR,
        PROGRAM_CHAIRS_ID
    ],
    'noninvitees': [PAPER_REVIEWERS_UNSUBMITTED_TEMPLATE_STR],
    'signatures': [CONFERENCE_ID],
    'process': os.path.abspath('../process/commentProcess.js'),
    'reply': {
        'forum': '<forum>',
        'replyto': None,
        'readers': {
            'description': 'Select all user groups that should be able to read this comment. Selecting \'All Users\' will allow paper authors, reviewers, area chairs, and program chairs to view this comment.',
            'values-dropdown': [
                'everyone',
                PAPER_AUTHORS_TEMPLATE_STR,
                PAPER_REVIEWERS_TEMPLATE_STR,
                PAPER_AREA_CHAIRS_TEMPLATE_STR,
                PROGRAM_CHAIRS_ID
            ]
        },
        'nonreaders': {
            'values': [PAPER_REVIEWERS_UNSUBMITTED_TEMPLATE_STR]
        },
        'signatures': {
            'description': '',
            'values-regex': '|'.join([
                PAPER_ANONREVIEWERS_TEMPLATE_REGEX,
                PAPER_AUTHORS_TEMPLATE_STR,
                PAPER_AREA_CHAIRS_TEMPLATE_REGEX,
                PROGRAM_CHAIRS_ID,
                CONFERENCE_ID
            ]),
        },
        'writers': {
            'description': 'Users that may modify this record.',
            'values-copied':  [
                CONFERENCE_ID,
                '{signatures}'
            ]
        },
        'content': invitations.content.comment
    }
}

official_review_template = {
    'id': OFFICIAL_REVIEW_TEMPLATE_STR,
    'readers': ['everyone'],
    'writers': [CONFERENCE_ID],
    'invitees': [PAPER_REVIEWERS_TEMPLATE_STR],
    'noninvitees': [PAPER_REVIEWERS_SUBMITTED_TEMPLATE_STR],
    'signatures': [CONFERENCE_ID],
    'duedate': OFFICIAL_REVIEW_DEADLINE,
    'process': os.path.abspath('../process/officialReviewProcess.js'),
    'reply': {
        'forum': '<forum>',
        'replyto': '<forum>',
        'readers': {
            'description': 'The users who will be allowed to read the reply content.',
            'values': ['everyone']
        },
        'nonreaders': {
            'values': [PAPER_REVIEWERS_UNSUBMITTED_TEMPLATE_STR]
        },
        'signatures': {
            'description': 'How your identity will be displayed with the above content.',
            'values-regex': PAPER_ANONREVIEWERS_TEMPLATE_REGEX
        },
        'writers': {
            'description': 'Users that may modify this record.',
            'values-copied':  [
                CONFERENCE_ID,
                '{signatures}'
            ]
        },
        'content': invitations.content.review
    }
}

meta_review_template = {
    'id': CONFERENCE_ID + '/-/Paper<number>/Meta_Review',
    'readers': ['everyone'],
    'writers': [CONFERENCE_ID],
    'invitees': [PAPER_AREA_CHAIRS_TEMPLATE_STR],
    'noninvitees': [],
    'signatures': [CONFERENCE_ID],
    'process': os.path.join(os.path.dirname(__file__), '../process/metaReviewProcess.js'),
    'reply': {
        'forum': '<forum>',
        'replyto': '<forum>',
        'readers': {
            'description': 'Select all user groups that should be able to read this comment. Selecting \'All Users\' will allow paper authors, reviewers, area chairs, and program chairs to view this comment.',
            'values': [CONFERENCE_ID, PAPER_AREA_CHAIRS_TEMPLATE_STR, PROGRAM_CHAIRS_ID]

        },
        'signatures': {
            'description': 'How your identity will be displayed with the above content.',
            'values-regex': PAPER_AREA_CHAIRS_TEMPLATE_REGEX
        },
        'writers': {
            'description': 'Users that may modify this record.',
            'values-regex': PAPER_AREA_CHAIRS_TEMPLATE_REGEX
        },
        'content': invitations.content.review
    }
}

