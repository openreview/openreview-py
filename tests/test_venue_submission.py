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
                'content': {
                    'signatures': {
                        'type': 'group[]',
                        'value': {
                            'param': { 'regex': '^.+$'}
                        }
                    }
                },
                'signatures': ['${2/content/signatures/value}'],
                'readers': [conference_id, '${2/content/signatures/value}', conference_id + '/Paper${2/note/number}/Authors'],
                'writers': [conference_id],
                'note': {
                    'signatures': [ conference_id + '/Paper${2/number}/Authors' ],
                    'readers': [conference_id, '${3/content/signatures/value}', conference_id + '/Paper${2/number}/Authors'],
                    'writers': [conference_id, '${3/content/signatures/value}', conference_id + '/Paper${2/number}/Authors'],
                    'content': {
                        'title': {
                            'type': 'string',
                            'value': { 
                                'param': { 
                                    'regex': '^.*$',
                                    'description': 'Title of the Paper'
                                }
                            },
                            'order': 1
                        },
                        'authors': {
                            'type': 'string[]',
                            'value': { 'param': { 'regex': '^.*$' } },
                            'readers': [ conference_id, '${5/content/signatures/value}', conference_id + '/Paper${4/number}/Authors' ]
                        },
                        'authorids': {
                            'type': 'group[]',
                            'value': { 'param': { 'regex': '^~.+$' } },
                            'readers': [ conference_id, '${5/content/signatures/value}', conference_id + '/Paper${4/number}/Authors' ]
                        },
                        'abstract': {
                            'type': 'string',
                            'value': { 'param': { 'regex': '^[\\S\\s]{1,5000}$' } }
                        },
                        'pdf': {
                            'type': 'file',
                            'value': {
                                'param': {
                                    'maxSize': 12,
                                    'extensions': ['pdf']
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

        celeste_client = helpers.create_user('celeste@mailnine.com', 'Celeste', 'Martinez')
