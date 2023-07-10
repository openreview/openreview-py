import csv
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
from openreview.api import Edge

from openreview.venue import Venue
from openreview.stages import SubmissionStage, BidStage

class TestReactNoteEditor():

    @pytest.fixture(scope="class")
    def venue(self, openreview_client):
        conference_id = 'ReactVenue.cc'

        venue = Venue(openreview_client, conference_id, 'openreview.net/Support')
        venue.invitation_builder.update_wait_time = 2000
        venue.invitation_builder.update_date_string = "#{4/mdate} + 2000"
        venue.automatic_reviewer_assignment = True 
        venue.use_area_chairs = True
        venue.name = 'Test Venue V2'
        venue.short_name = 'TV 22'
        venue.website = 'testvenue.org'
        venue.contact = 'testvenue@contact.com'
        venue.reviewer_identity_readers = [openreview.stages.IdentityReaders.PROGRAM_CHAIRS, openreview.stages.IdentityReaders.AREA_CHAIRS_ASSIGNED]

        now = datetime.datetime.utcnow()
        venue.submission_stage = SubmissionStage(
            double_blind=True,
            due_date=now + datetime.timedelta(minutes = 30),
            readers=[SubmissionStage.Readers.EVERYONE], 
            withdrawn_submission_public=True, 
            withdrawn_submission_reveal_authors=True, 
            desk_rejected_submission_public=True,
            force_profiles=True,
            additional_fields={
                'checkbox_mandatory': {
                    'description': 'This is a description',
                    'order': 1,
                    'value': {
                        'param': {
                            'enum': ['Yes'],
                            'type': 'string',
                            'input': 'checkbox',
                            'default': 'Yes',
                        }
                    }
                },
                'checkbox_optional': {
                    'description': 'This is a description',
                    'order': 1,
                    'value': {
                        'param': {
                            'enum': ['Yes'],
                            'type': 'string',
                            'input': 'checkbox',
                            'optional': True,
                            'deletable': True
                        }
                    }
                },
                'radio_button': {
                    'description': 'This is a description',
                    'order': 1,
                    'value': {
                        'param': {
                            'fieldName': 'Paper color',
                            'enum': ['Black', 'White'],
                            'type': 'string',
                            'input': 'radio'
                        }
                    }
                },
                'radio_button_number': {
                    'description': 'This is a description',
                    'order': 1,
                    'value': {
                        'param': {
                            'type': 'integer',
                            'enum': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
                            'input': 'radio'
                        }
                    }
                },
                'radio_button_number_with_description': {
                    'description': 'This is a description',
                    'order': 1,
                    'value': {
                        'param': {
                            'type': 'integer',
                            'enum': [
                                { 'value': 1, 'description': 'This is a description for 1' },
                                { 'value': 2, 'description': 'This is a description for 2' },
                                { 'value': 3, 'description': 'This is a description for 3'},
                                { 'value': 4, 'description': 'This is a description for 4'},
                                { 'value': 5, 'description': 'This is a description for 5' },
                                { 'value': 6, 'description': 'This is a description for 6' },
                                { 'value': 7, 'description': 'This is a description for 7' },
                                { 'value': 8, 'description': 'This is a description for 8' },
                                { 'value': 9, 'description': 'This is a description for 9' },
                            ],
                            'input': 'radio'
                        }
                    }
                },
                'dropdown_field': {
                    'description': 'This is a description',
                    'order': 1,
                    'value': {
                        'param': {
                            'type': 'string',
                            'enum': ['A', 'B', 'C'],
                            'input': 'select'
                        }
                    }
                },
                'multi_dropdown_field': {
                    'description': 'This is a description',
                    'order': 1,
                    'value': {
                        'param': {
                            'type': 'string[]',
                            'enum': ['A', 'B', 'C', 'D', 'E', 'F', 'G'],
                            'input': 'select'
                        }
                    }
                },
                'default_dropdown_field': {
                    'description': 'This is a description',
                    'order': 1,
                    'value': {
                        'param': {
                            'type': 'string',
                            'enum': ['A', 'B', 'C']
                        }
                    }
                },
                'default_dropdown_field_two': {
                    'description': 'This is a description',
                    'order': 1,
                    'value': {
                        'param': {
                            'type': 'string',
                            'enum': [{ 'value': 'A', 'description': 'Letter A' }, { 'value': 'B', 'description': 'Letter B' }, { 'value': 'C', 'description': 'Letter C' }]
                        }
                    }
                },                             
                'dropdown_number_with_description': {
                    'description': 'This is a description',
                    'order': 1,
                    'value': {
                        'param': {
                            'type': 'integer[]',
                            'items': [
                                { 'value': 1, 'description': 'This is a description for 1', 'optional': True },
                                { 'value': 2, 'description': 'This is a description for 2', 'optional': True },
                                { 'value': 3, 'description': 'This is a description for 3', 'optional': True },
                                { 'value': 4, 'description': 'This is a description for 4', 'optional': True },
                                { 'value': 5, 'description': 'This is a description for 5', 'optional': True },
                                { 'value': 6, 'description': 'This is a description for 6', 'optional': True },
                                { 'value': 7, 'description': 'This is a description for 7', 'optional': True },
                                { 'value': 8, 'description': 'This is a description for 8', 'optional': True },
                                { 'value': 9, 'description': 'This is a description for 9', 'optional': True },
                            ],
                            'input': 'select'
                        }
                    }
                },
                'dropdown_number_with_mandatory': {
                    'description': 'This is a description',
                    'order': 1,
                    'value': {
                        'param': {
                            'type': 'string[]',
                            'items': [
                                { 'value': 'ICLR.cc/Program_Chairs', 'description': 'Program Chairs', 'optional': False },
                                { 'value': 'ICLR.cc/Senior_Area_Chairs', 'description': 'Senior Area Chairs', 'optional': False },
                                { 'value': 'ICLR.cc/Area_Chairs', 'description': 'All Ara Chairs', 'optional': True },
                                { 'value': 'ICLR.cc/Reviewers', 'description': 'All Reviewers', 'optional': True },
                                { 'value': 'ICLR.cc/Authors', 'description': 'Submission authors', 'optional': True }
                            ],
                            'input': 'select'
                        }
                    }
                },
                'json_field': {
                    'description': 'Settings for the venue',
                    'order': 1,
                    'value': {
                        'param': {
                            'type': 'json',
                            'optional': True,
                            'deletable': True
                        }
                    }
                }
            },
            remove_fields=[],
        )
        return venue


    def test_setup(self, venue, openreview_client, helpers):

        venue.setup(program_chair_ids=['venue_pc@mail.com'])
        venue.create_submission_stage()
        assert openreview_client.get_group('ReactVenue.cc')
        assert openreview_client.get_group('ReactVenue.cc/Authors')


        invitations = openreview_client.get_invitations(prefix = 'ReactVenue.cc', type = 'all')
        for invitation in invitations:
            if 'ReactVenue.cc/-/Edit' not in invitation.id:
                openreview_client.post_invitation_edit(
                    invitations='ReactVenue.cc/-/Edit',
                    signatures=['ReactVenue.cc'],
                    invitation=openreview.api.Invitation(
                        id=invitation.id,
                        expdate=openreview.tools.datetime_millis(datetime.datetime.utcnow())
                    )
                )

        helpers.await_queue(openreview_client)


