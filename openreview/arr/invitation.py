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
    SUBMITTED_AUTHORS_NAME = 'Submitted_Author_Form'

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
        self.venue.custom_stage.process_path = process_script
        self.venue.custom_stage.preprocess_path = preprocess_script
        invitation = self.venue_invitation_builder.set_custom_stage_invitation()
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
            readers = [venue_id],
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
            readers = [venue_id],
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
    
    def set_preferred_emails_invitation(self):
        return self.venue_invitation_builder.set_preferred_emails_invitation()

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

    def set_submission_metadata_revision_invitation(self, arr_stage):
        venue_id = self.venue_id
        submission_license = self.venue.submission_license

        revision_stage = openreview.stages.SubmissionRevisionStage(
            name='Submission_Metadata_Revision',
            source={'venueid': self.venue.get_submission_venue_id()},
            start_date=arr_stage.start_date,
            due_date=arr_stage.due_date,
            exp_date=arr_stage.exp_date,
            remove_fields=arr_stage.stage_arguments.get('remove_fields', []),
            only_accepted=arr_stage.stage_arguments.get('only_accepted', False),
            allow_author_reorder=arr_stage.stage_arguments.get('allow_author_reorder', openreview.stages.AuthorReorder.DISALLOW_EDIT),
            preprocess_path='process/submission_preprocess.py'
        )

        revision_invitation_id = self.venue.get_invitation_id(revision_stage.name)
        revision_cdate = tools.datetime_millis(revision_stage.start_date if revision_stage.start_date else datetime.datetime.now())
        revision_duedate = tools.datetime_millis(revision_stage.due_date) if revision_stage.due_date else None
        revision_expdate = tools.datetime_millis(revision_stage.exp_date) if revision_stage.exp_date else None
        if not revision_expdate:
            revision_expdate = tools.datetime_millis(revision_stage.due_date + datetime.timedelta(minutes=SHORT_BUFFER_MIN)) if revision_stage.due_date else None

        if revision_duedate and revision_duedate < revision_cdate:
            revision_cdate = revision_duedate

        content = revision_stage.get_content(api_version='2', conference=self.venue)

        invitation = Invitation(
            id=revision_invitation_id,
            invitees=[venue_id],
            readers=[venue_id],
            writers=['~Super_User1'],
            signatures=['~Super_User1'],
            cdate=revision_cdate,
            date_processes=[{
                'dates': ["#{4/edit/invitation/cdate}", self.update_date_string],
                'script': self.invitation_edit_process
            }],
            content={
                'revision_process_script': {
                    'value': self.get_process_content('process/submission_revision_process.py')
                },
                'source': {
                    'value': revision_stage.get_source_submissions(self.venue)
                }
            },
            edit={
                'signatures': [venue_id],
                'readers': [venue_id],
                'writers': [venue_id],
                'content': {
                    'noteNumber': {
                        'value': {
                            'param': {
                                'type': 'integer'
                            }
                        }
                    },
                    'noteId': {
                        'value': {
                            'param': {
                                'type': 'string'
                            }
                        }
                    }
                },
                'replacement': True,
                'invitation': {
                    'id': self.venue.get_invitation_id(revision_stage.name, '${2/content/noteNumber/value}'),
                    'signatures': ['~Super_User1'],
                    'readers': [venue_id, self.venue.get_authors_id(number='${3/content/noteNumber/value}')],
                    'writers': ['~Super_User1'],
                    'invitees': [venue_id, self.venue.get_authors_id(number='${3/content/noteNumber/value}')],
                    'cdate': revision_cdate,
                    'process': '''def process(client, edit, invitation):
    meta_invitation = client.get_invitation(invitation.invitations[0])
    script = meta_invitation.content['revision_process_script']['value']
    funcs = {
        'openreview': openreview
    }
    exec(script, funcs)
    funcs['process'](client, edit, invitation)
''',
                    'edit': {
                        'ddate': {
                            'param': {
                                'range': [0, 9999999999999],
                                'optional': True
                            }
                        },
                        'signatures': {
                            'param': {
                                'items': [
                                    {'value': self.venue.get_authors_id(number='${7/content/noteNumber/value}'), 'optional': True},
                                    {'value': self.venue.get_program_chairs_id(), 'optional': True}
                                ]
                            }
                        },
                        'readers': revision_stage.get_edit_readers(self.venue, '${4/content/noteNumber/value}'),
                        'writers': [venue_id, self.venue.get_authors_id(number='${4/content/noteNumber/value}')],
                        'note': {
                            'id': '${4/content/noteId/value}',
                            'content': content
                        }
                    }
                }
            }
        )

        if revision_duedate:
            invitation.edit['invitation']['duedate'] = revision_duedate

        if revision_expdate:
            invitation.edit['invitation']['expdate'] = revision_expdate

        if revision_stage.preprocess_path:
            invitation.edit['invitation']['preprocess'] = '''def process(client, edit, invitation):
    meta_invitation = client.get_invitation(invitation.invitations[0])
    script = meta_invitation.content['revision_preprocess_script']['value']
    funcs = {
        'openreview': openreview
    }
    exec(script, funcs)
    funcs['process'](client, edit, invitation)
'''
            invitation.content['revision_preprocess_script'] = {'value': self.get_process_content(revision_stage.preprocess_path)}

        if submission_license and revision_stage.allow_license_edition:
            if isinstance(submission_license, str):
                invitation.edit['invitation']['edit']['note']['license'] = submission_license
            elif len(submission_license) == 1:
                invitation.edit['invitation']['edit']['note']['license'] = submission_license[0]
            elif isinstance(submission_license, dict):
                invitation.edit['invitation']['edit']['note']['license'] = {
                    'param': {
                        'enum': [submission_license]
                    }
                }
            else:
                license_options = [{"value": license, "description": license} for license in submission_license]
                invitation.edit['invitation']['edit']['note']['license'] = {
                    "param": {
                        "enum": license_options
                    }
                }

        self.save_invitation(invitation, replacement=False)
        return invitation

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
    
    def set_venue_template_invitations(self):
        return self.venue_invitation_builder.set_venue_template_invitations()
