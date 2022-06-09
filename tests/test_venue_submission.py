import openreview
import pytest
import time
import json
import datetime
import random
import os
import re
from openreview.api import OpenReviewClient
from openreview.api import Note
from openreview.api import Group
from openreview.api import Invitation

class TestVenueSubmission():

    def test_setup(self, openreview_client, helpers):
        conference_id = 'TestVenue.cc'

        venue_group = Group(id = conference_id,
            readers = ['everyone'],
            writers = [conference_id],
            signatures = ['~Super_User1'],
            signatories = [conference_id],
            members = [],
            host = conference_id
        )

        with open(os.path.join(os.path.dirname(__file__), '../openreview/journal/webfield/homepage.js')) as f:
            content = f.read()
            content = content.replace("var VENUE_ID = '';", "var VENUE_ID = '" + conference_id + "';")
            content = content.replace("var SUBMISSION_ID = '';", "var SUBMISSION_ID = '" + conference_id + "/-/Submission';")
            content = content.replace("var SUBMITTED_ID = '';", "var SUBMITTED_ID = '" + conference_id + "/Submitted';")
            content = content.replace("var UNDER_REVIEW_ID = '';", "var UNDER_REVIEW_ID = '" + conference_id + "/Under_Review';")
            content = content.replace("var DESK_REJECTED_ID = '';", "var DESK_REJECTED_ID = '" + conference_id + "/Desk_Rejection';")
            content = content.replace("var WITHDRAWN_ID = '';", "var WITHDRAWN_ID = '" + conference_id + "/Withdrawn_Submission';")
            content = content.replace("var REJECTED_ID = '';", "var REJECTED_ID = '" + conference_id + "/Rejection';")
            venue_group.web = content
            openreview_client.post_group(venue_group)

        assert venue_group

        meta_inv = openreview_client.post_invitation_edit(invitations = None, 
            readers = [conference_id],
            writers = [conference_id],
            signatures = [conference_id],
            invitation = Invitation(id = f'{conference_id}/-/Edit',
                invitees = [conference_id],
                readers = [conference_id],
                signatures = [conference_id],
                edit = True
            ))

        assert meta_inv

        submission_invitation = Invitation(
            id=f'{conference_id}/-/Submission',
            invitees = ['~'],
            signatures = [conference_id],
            readers = ['everyone'],
            writers = [conference_id],
            edit = {
                'signatures': { 'param': { 'regex': '~.*' } },
                # 'readers': [conference_id, '${2/signatures}', conference_id + '/Paper${2/note/number}/Authors'],
                'readers': [conference_id, conference_id + '/Paper${2/note/number}/Action_Editors', conference_id + '/Paper${2/note/number}/Authors'],
                'writers': [conference_id],
                'note': {
                    'signatures': [ conference_id + '/Paper${2/number}/Authors' ],
                    # 'readers': [conference_id, '${3/signatures}', conference_id + '/Paper${2/number}/Authors'],
                    # 'writers': [conference_id, '${3/signatures}', conference_id + '/Paper${2/number}/Authors'],
                    'readers': [conference_id, conference_id + '/Paper${2/number}/Action_Editors', conference_id + '/Paper${2/number}/Authors'],
                    'writers': [conference_id, conference_id + '/Paper${2/number}/Action_Editors', conference_id + '/Paper${2/number}/Authors'],
                    'content': {
                        'title': {
                            'order': 1,
                            'type': 'string',
                            'description': 'Title of paper. Add TeX formulas using the following formats: $In-line Formula$ or $$Block Formula$$.',
                            'value': { 
                                'param': { 
                                    'regex': '^.{1,250}$'
                                }
                            }
                        },
                        'authors': {
                            'order': 2,
                            'type': 'string[]',
                            'value': {
                                'param': {
                                    'regex': '[^;,\\n]+(,[^,\\n]+)*',
                                    'hidden': True
                                }
                            },
                            # 'readers': [ conference_id, '${5/signatures}', conference_id + '/Paper${4/number}/Authors' ]
                            'readers': [conference_id, conference_id + '/Paper${4/number}/Action_Editors', conference_id + '/Paper${4/number}/Authors']
                        },
                        'authorids': {
                            'order': 3,
                            'type': 'group[]',
                            'description': 'Search author profile by first, middle and last name or email address. All authors must have an OpenReview profile.',
                            'value': {
                                'param': {
                                    'regex': '~.*'
                                }
                            },
                            # 'readers': [ conference_id, '${5/signatures}', conference_id + '/Paper${4/number}/Authors' ]
                            'readers': [conference_id, conference_id + '/Paper${4/number}/Action_Editors', conference_id + '/Paper${4/number}/Authors']
                        },
                        'abstract': {
                            'order': 4,
                            'type': 'string',
                            'description': 'Abstract of paper. Add TeX formulas using the following formats: $In-line Formula$ or $$Block Formula$$.',
                            'value': {
                                'param': {
                                    'regex': '^[\\S\\s]{1,5000}$',
                                    'markdown': True
                                }
                            }
                        },
                        'pdf': {
                            'order': 5,
                            'type': 'file',
                            'description': 'Upload a PDF file that ends with .pdf.',
                            'value': {
                                'param': {
                                    'maxSize': 50,
                                    'extensions': ['pdf']
                                }
                            }
                        },
                        "previous_submission_url": {
                            'order': 6,
                            'type': 'string',
                            'description': 'If a version of this submission was previously rejected, give the OpenReview link to the original submission (which must still be anonymous) and describe the changes below.',
                            'value':{
                                'param': {
                                    'regex': 'https:\\/\\/openreview\\.net\\/forum\\?id=.*',
                                    'optional': True
                                }
                            }
                        },
                        'changes_since_last_submission': {
                            'order': 7,
                            'type': 'string',
                            'description': 'Describe changes since last submission. Add TeX formulas using the following formats: $In-line Formula$ or $$Block Formula$$.',
                            'value': {
                                'param': {
                                    'regex': '^[\\S\\s]{1,5000}$',
                                    'optional': True,
                                    'markdown': True
                                }
                            }
                        },
                        "submission_length": {
                            'order': 8,
                            'type': 'string[]',
                            'description': 'Check if this is a regular length submission, i.e. the main content (all pages before references and appendices) is 12 pages or less. Note that the review process may take significantly longer for papers longer than 12 pages.',
                            'value': {
                                'param': {
                                    'enum': [
                                        'Regular submission (no more than 12 pages of main content)',
                                        'Long submission (more than 12 pages of main content)'
                                    ],
                                    'input': 'radio',
                                    'optional': True
                                }
                            }
                        }
                    }
                }
            }
        )

        submission_invitation = openreview_client.post_invitation_edit(
            invitations = f'{conference_id}/-/Edit',
            readers = [conference_id],
            writers = [conference_id],
            signatures = [conference_id],
            invitation = submission_invitation)

        assert submission_invitation

        helpers.create_user('celeste@mailnine.com', 'Celeste', 'Martinez')
        author_client = OpenReviewClient(username='celeste@mailnine.com', password='1234')

        submission_note_1 = author_client.post_note_edit(
            invitation=f'{conference_id}/-/Submission',
            signatures= ['~Celeste_Martinez1'],
            note=Note(
                content={
                    'title': { 'value': 'Paper 1 Title' },
                    'abstract': { 'value': 'Paper abstract' },
                    'authors': { 'value': ['Celeste Martinez']},
                    'authorids': { 'value': ['~Celeste_Martinez1']},
                    'pdf': {'value': '/pdf/' + 'p' * 40 +'.pdf' },
                }
            ))
