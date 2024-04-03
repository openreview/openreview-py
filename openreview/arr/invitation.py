import csv
import datetime
import json
import os
import time
import re
from openreview.api import Invitation
from openreview.api import Note
from openreview.stages import *
from openreview.stages.arr_content import hide_fields_from_public
from .helpers import ARRWorkflow
from .. import tools

SHORT_BUFFER_MIN = 30
LONG_BUFFER_DAYS = 10

class InvitationBuilder(object):
    REGISTRATION_NAME = 'Registration'
    MAX_LOAD_AND_UNAVAILABILITY_NAME = 'Max_Load_And_Unavailability_Request'
    EMERGENCY_REVIEWING_NAME = 'Emergency_Reviewer_Agreement'
    EMERGENCY_METAREVIEWING_NAME = 'Emergency_Metareviewer_Agreement'
    REVIEWER_LICENSE_NAME = 'License_Agreement'
    METAREVIEWER_LICENSE_NAME = 'Metareview_License_Agreement'
    RECOGNITION_NAME = 'Recognition_Request'

    def __init__(self, venue, update_wait_time=5000):
        self.client = venue.client
        self.venue = venue
        self.venue_id = venue.venue_id
        self.update_wait_time = update_wait_time
        self.update_date_string = "#{4/mdate} + " + str(self.update_wait_time)
        self.venue_invitation_builder = openreview.venue.InvitationBuilder(venue)
        self.invitation_edit_process = '''def process(client, invitation):
    meta_invitation = client.get_invitation("''' + self.venue.get_meta_invitation_id() + '''")
    script = meta_invitation.content["invitation_edit_script"]['value']
    funcs = {
        'openreview': openreview,
        'datetime': datetime,
        'date_index': date_index
    }
    exec(script, funcs)
    funcs['process'](client, invitation)
'''

        self.group_edit_process = '''def process(client, invitation):
    meta_invitation = client.get_invitation("''' + self.venue.get_meta_invitation_id() + '''")
    script = meta_invitation.content["group_edit_script"]['value']
    funcs = {
        'openreview': openreview,
        'datetime': datetime,
        'date_index': date_index
    }
    exec(script, funcs)
    funcs['process'](client, invitation)
'''

    # Non-blocking custom stage with process/pre-process arguments
    def set_custom_stage_invitation(self, process_script = None, preprocess_script = None):
        invitation = self.venue_invitation_builder.set_custom_stage_invitation()
        if not process_script and not preprocess_script:
            return invitation

        if process_script:
            invitation.content['custom_stage_process_script'] = { 'value': self.get_process_content(process_script)}
        if preprocess_script:
            invitation.edit['invitation']['preprocess'] = self.get_process_content(preprocess_script)

        self.save_invitation(invitation, replacement=False)
        return invitation

    def get_process_content(self, file_path):
        process = None
        try:
            with open(os.path.join(os.path.dirname(__file__), file_path)) as f:
                process = f.read()
                return process
        except FileNotFoundError:
            return self.venue_invitation_builder.get_process_content(file_path)
        
    def set_verification_flag_invitation(self):
        venue_id = self.venue_id
        flag_invitation_id = f'{venue_id}/-/Desk_Reject_Verification_Flag'
        submission_id = self.venue.submission_stage.get_submission_id(self.venue)

        flag_readers = [venue_id]
        if self.venue.use_senior_area_chairs:
            flag_readers.append(self.venue.get_senior_area_chairs_id('${{4/id}/number}'))
        
        flag_invitation = Invitation(
            id=flag_invitation_id,
            invitees = [venue_id],
            signatures = [venue_id],
            readers = ['everyone'],
            writers = [venue_id],
            edit = {
                'signatures': [venue_id],
                'readers': [venue_id],
                'writers': [venue_id],
                'note': {
                    'id': {
                        'param': {
                            'withInvitation': submission_id,
                            'optional': True
                        }
                    },
                    'signatures': [ self.venue.get_authors_id('${{2/id}/number}') ],
                    'writers': [venue_id, self.venue.get_authors_id('${{2/id}/number}')],
                    'content': {
                        'flagged_for_desk_reject_verification': {
                            'value': {
                                'param': {
                                    'type': 'boolean',
                                    'enum': [True, False],
                                    'input': 'radio'
                                }
                            },
                            'readers': flag_readers
                        }
                    }
                }
            },
            process=self.get_process_content('process/verification_process.py')
        )

        self.save_invitation(flag_invitation, replacement=False)
        return flag_invitation

    def set_arr_configuration_invitation(self):
        # Must be run by super user
        client_v1 = openreview.Client(
            baseurl=openreview.tools.get_base_urls(self.client)[0],
            token=self.client.token
        )

        venue_id = self.venue_id
        request_form_id = self.venue.request_form_id
        request_form = client_v1.get_note(request_form_id)
        support_group = request_form.invitation.split('/-/')[0]

        client_v1.post_invitation(openreview.Invitation(
            id=f"{support_group}/-/Request{request_form.number}/ARR_Configuration",
            readers=[venue_id],
            writers=[support_group],
            signatures=['~Super_User1'],
            invitees=[venue_id],
            multiReply=True,
            process_string=self.get_process_content('process/configuration_process.py'),
            reply={
                'forum':request_form_id,
                'referent': request_form_id,
                'readers': {
                    'description': 'The users who will be allowed to read the above content.',
                    'values' : [
                        support_group,
                        self.venue.get_program_chairs_id()
                    ]
                },
                'writers': {
                    'values':[],
                },
                'signatures': {
                    'values-regex': '~.*'
                },
                'content': ARRWorkflow.CONFIGURATION_INVITATION_CONTENT
            }
        ))

    def set_process_invitation(self, arr_stage):
        venue_id = self.venue_id
        process_invitation_id = arr_stage.super_invitation_id

        process_invitation = Invitation(
            id=process_invitation_id,
            invitees = [venue_id],
            signatures = ['~Super_User1'],
            readers = ['everyone'],
            writers = ['~Super_User1'],
            cdate = openreview.tools.datetime_millis(arr_stage.start_date),
            date_processes=[{ 
                'dates': ["#{4/cdate}", self.update_date_string],
                'script': self.get_process_content(arr_stage.process)
            }],            
            **arr_stage.stage_arguments
        )

        process_invitation = self.save_invitation(process_invitation, replacement=False)
        return process_invitation
        
    def save_invitation(self, invitation, replacement=None):
        return self.venue_invitation_builder.save_invitation(invitation, replacement)

    def expire_invitation(self, invitation_id):
        return self.venue_invitation_builder.expire_invitation(invitation_id)

    def set_meta_invitation(self):
        return self.venue_invitation_builder.set_meta_invitation()

    def set_submission_invitation(self):
        return self.venue_invitation_builder.set_submission_invitation()

    def set_post_submission_invitation(self):
        return self.venue_invitation_builder.set_post_submission_invitation()

    def set_pc_submission_revision_invitation(self):
        return self.venue_invitation_builder.set_pc_submission_revision_invitation()

    def set_review_invitation(self):
        return self.venue_invitation_builder.set_review_invitation()

    def update_review_invitations(self):
        return self.venue_invitation_builder.update_review_invitations()

    def set_review_rebuttal_invitation(self):
        return self.venue_invitation_builder.set_review_rebuttal_invitation()

    def set_meta_review_invitation(self):
        return self.venue_invitation_builder.set_meta_review_invitation()

    def set_recruitment_invitation(self, committee_name, options):
        return self.venue_invitation_builder.set_recruitment_invitation(committee_name,  options)

    def set_bid_invitations(self):
        return self.venue_invitation_builder.set_bid_invitations()

    def set_official_comment_invitation(self):
        return self.venue_invitation_builder.set_official_comment_invitation()

    def set_public_comment_invitation(self):
        return self.venue_invitation_builder.set_public_comment_invitation()

    def set_decision_invitation(self):
        return self.venue_invitation_builder.set_decision_invitation()

    def set_withdrawal_invitation(self):
        return self.venue_invitation_builder.set_withdrawal_invitation()

    def set_desk_rejection_invitation(self):
        return self.venue_invitation_builder.set_desk_rejection_invitation()

    def set_submission_revision_invitation(self, submission_revision_stage=None):
        return self.venue_invitation_builder.set_submission_revision_invitation(submission_revision_stage)

    def set_assignment_invitation(self, committee_id, submission_content=None):
        return self.venue_invitation_builder.set_assignment_invitation(committee_id, submission_content)

    def set_expertise_selection_invitations(self):
        return self.venue_invitation_builder.set_expertise_selection_invitations()

    def set_registration_invitations(self):
        return self.venue_invitation_builder.set_registration_invitations()

    def set_paper_recruitment_invitation(self, invitation_id, committee_id, invited_committee_name, hash_seed, assignment_title=None, due_date=None, invited_label='Invited', accepted_label='Accepted', declined_label='Declined', proposed=False):
        return self.venue_invitation_builder.set_paper_recruitment_invitation(invitation_id,  committee_id,  invited_committee_name,  hash_seed, assignment_title, due_date, invited_label, accepted_label, declined_label, proposed)

    def set_submission_reviewer_group_invitation(self):
        return self.venue_invitation_builder.set_submission_reviewer_group_invitation()

    def set_submission_area_chair_group_invitation(self):
        return self.venue_invitation_builder.set_submission_area_chair_group_invitation()

    def set_submission_senior_area_chair_group_invitation(self):
        return self.venue_invitation_builder.set_submission_senior_area_chair_group_invitation()

    def set_ethics_paper_groups_invitation(self):
        return self.venue_invitation_builder.set_ethics_paper_groups_invitation()

    def set_ethics_review_invitation(self):
        return self.venue_invitation_builder.set_ethics_review_invitation()

    def set_ethics_stage_invitation(self):
        return self.venue_invitation_builder.set_ethics_stage_invitation()

    def set_SAC_ethics_flag_invitation(self, sac_ethics_flag_duedate=None):
        return self.venue_invitation_builder.set_SAC_ethics_flag_invitation(sac_ethics_flag_duedate)

    def set_reviewer_recommendation_invitation(self, start_date, due_date, total_recommendations):
        return self.venue_invitation_builder.set_reviewer_recommendation_invitation(start_date,  due_date,  total_recommendations)

