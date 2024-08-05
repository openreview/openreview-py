import csv
import json
import os
from json import tool
import datetime
from io import StringIO
from multiprocessing import cpu_count
from concurrent.futures import ThreadPoolExecutor
from tqdm import tqdm
import openreview
from openreview import tools
from .invitation import InvitationBuilder
from .helpers import ARRWorkflow
from openreview.venue.group import GroupBuilder
from openreview.api import Group
from openreview.api import Note
from openreview.api import Invitation
from openreview.venue.recruitment import Recruitment
from openreview.arr.helpers import (
    setup_arr_invitations
)
from openreview.stages.arr_content import hide_fields

SHORT_BUFFER_MIN = 30
LONG_BUFFER_DAYS = 10

class ARR(object):

    def __init__(self, client, venue_id, support_user, venue=None):

        self.client = client
        self.venue = venue
        self.request_form_id = None
        self.venue_id = venue_id
        self.name = 'TBD'
        self.short_name = 'TBD'
        self.website = None 
        self.contact = None
        self.location = None
        self.instructions = None
        self.start_date = 'TBD'
        self.date = 'TBD'
        self.id = venue_id # get compatibility with conference
        self.program_chairs_name = 'Program_Chairs'
        self.reviewers_name = 'Reviewers'
        self.reviewer_roles = ['Reviewers']
        self.area_chair_roles = ['Area_Chairs']
        self.senior_area_chair_roles = ['Senior_Area_Chairs']        
        self.area_chairs_name = 'Area_Chairs'
        self.secondary_area_chairs_name = 'Secondary_Area_Chairs'
        self.senior_area_chairs_name = 'Senior_Area_Chairs'
        self.ethics_chairs_name = 'Ethics_Chairs'
        self.ethics_reviewers_name = 'Ethics_Reviewers'
        self.authors_name = 'Authors'
        self.recommendation_name = 'Recommendation'
        self.use_ethics_chairs = False
        self.use_ethics_reviewers = False 
        self.expertise_selection_stage = None       
        self.submission_stage = None
        self.review_stage = None
        self.review_rebuttal_stage = None
        self.ethics_review_stage = None
        self.bid_stages = []
        self.meta_review_stage = None
        self.comment_stage = None
        self.decision_stage = None
        self.custom_stage = None
        self.submission_revision_stage = None
        self.registration_stages = []
        self.use_area_chairs = False
        self.use_senior_area_chairs = False
        self.use_ethics_chairs = False
        self.use_secondary_area_chairs = False
        self.use_recruitment_template = True
        self.support_user = support_user
        self.invitation_builder = InvitationBuilder(self)
        self.group_builder = GroupBuilder(self)
        self.recruitment = Recruitment(self)
        self.reviewer_identity_readers = []
        self.area_chair_identity_readers = []
        self.senior_area_chair_identity_readers = []
        self.automatic_reviewer_assignment = False
        self.decision_heading_map = {}
        self.allow_gurobi_solver = False
        self.submission_license = None
        self.use_publication_chairs = False
        self.source_submissions_query_mapping = {}
        self.sac_paper_assignments = False
        self.submission_assignment_max_reviewers = None

    def copy_to_venue(self):

        if 'openreview.net' in self.support_user:
            self.venue.invitation_builder.update_wait_time = 2000
            self.venue.invitation_builder.update_date_string = "#{4/mdate} + 2000"

        self.venue.name = self.name 
        self.venue.short_name = self.short_name
        self.venue.website = self.website
        self.venue.contact = self.contact
        self.venue.location = self.location
        self.venue.instructions = self.instructions  
        self.venue.start_date = self.start_date
        self.venue.date = self.date
        self.venue.program_chairs_name = self.program_chairs_name
        self.venue.reviewers_name = self.reviewers_name
        self.venue.reviewer_roles = self.reviewer_roles
        self.venue.area_chair_roles = self.area_chair_roles
        self.venue.senior_area_chair_roles = self.senior_area_chair_roles
        self.venue.area_chairs_name = self.area_chairs_name
        self.venue.secondary_area_chairs_name = self.secondary_area_chairs_name
        self.venue.senior_area_chairs_name = self.senior_area_chairs_name
        self.venue.ethics_chairs_name = self.ethics_chairs_name
        self.venue.ethics_reviewers_name = self.ethics_reviewers_name
        self.venue.authors_name = self.authors_name
        self.venue.recommendation_name = self.recommendation_name                 

        self.venue.request_form_id = self.request_form_id
        self.venue.use_area_chairs = self.use_area_chairs
        self.venue.use_senior_area_chairs = self.use_senior_area_chairs
        self.venue.use_secondary_area_chairs = self.use_secondary_area_chairs
        self.venue.use_ethics_chairs = self.use_ethics_chairs
        self.venue.use_ethics_reviewers = self.use_ethics_reviewers
        self.venue.use_publication_chairs = self.use_publication_chairs
        self.venue.automatic_reviewer_assignment = self.automatic_reviewer_assignment
        self.venue.senior_area_chair_roles = self.senior_area_chair_roles
        self.venue.area_chair_roles = self.area_chair_roles
        self.venue.reviewer_roles = self.reviewer_roles
        self.venue.allow_gurobi_solver = self.allow_gurobi_solver
        self.venue.submission_license = self.submission_license
        self.venue.reviewer_identity_readers = self.reviewer_identity_readers
        self.venue.area_chair_identity_readers = self.area_chair_identity_readers
        self.venue.senior_area_chair_identity_readers = self.senior_area_chair_identity_readers
        self.venue.decision_heading_map = self.decision_heading_map
        self.venue.source_submissions_query_mapping = self.source_submissions_query_mapping
        self.venue.sac_paper_assignments = self.sac_paper_assignments
        self.venue.submission_assignment_max_reviewers = self.submission_assignment_max_reviewers

        self.submission_stage.hide_fields = self.submission_stage.hide_fields + hide_fields
        self.venue.submission_stage = self.submission_stage
        self.venue.review_stage = self.review_stage
        self.venue.bid_stages = self.bid_stages
        self.venue.meta_review_stage = self.meta_review_stage
        self.venue.comment_stage = self.comment_stage
        self.venue.decision_stage = self.decision_stage
        self.venue.submission_revision_stage = self.submission_revision_stage
        self.venue.review_rebuttal_stage = self.review_rebuttal_stage
        self.venue.registration_stages = self.registration_stages
        self.venue.ethics_review_stage = self.ethics_review_stage
        self.venue.custom_stage = self.custom_stage

        self.venue.expertise_selection_stage = self.expertise_selection_stage
        self.venue.preferred_emails_groups = self.preferred_emails_groups

    def set_arr_stages(self, configuration_note):
        workflow = ARRWorkflow(
            self.client,
            self,
            configuration_note,
            self.request_form_id,
            self.support_user
        )
        workflow.set_workflow()

    def get_id(self):
        return self.venue.get_id()

    def get_short_name(self):
        return self.venue.get_short_name()

    def get_message_sender(self):
        return self.venue.get_message_sender()

    def get_edges_archive_date(self):
        return self.venue.get_edges_archive_date()

    def get_committee_name(self, committee_id, pretty=False):
        return self.venue.get_committee_name(committee_id, pretty)

    def get_committee_names(self):
        return self.venue.get_committee_names()

    def get_roles(self):
        return self.venue.get_roles()

    def submission_tracks(self):
        return self.venue.submission_tracks()

    def get_meta_invitation_id(self):
        return self.venue.get_meta_invitation_id()

    def get_submission_id(self):
        return self.venue.get_submission_id()

    def get_pc_submission_revision_id(self):
        return self.venue.get_pc_submission_revision_id()

    def get_recruitment_id(self, committee_id):
        return self.venue.get_recruitment_id(committee_id)

    def get_expertise_selection_id(self, committee_id):
        return self.venue.get_expertise_selection_id(committee_id)

    def get_bid_id(self, committee_id):
        return self.venue.get_bid_id(committee_id)

    def get_assignment_id(self, committee_id, deployed=False, invite=False):
        return self.venue.get_assignment_id(committee_id, deployed, invite)

    def get_affinity_score_id(self, committee_id):
        return self.venue.get_affinity_score_id(committee_id)

    def get_conflict_score_id(self, committee_id):
        return self.venue.get_conflict_score_id(committee_id)

    def get_custom_max_papers_id(self, committee_id):
        return self.venue.get_custom_max_papers_id(committee_id)

    def get_custom_user_demands_id(self, committee_id):
        return self.venue.get_custom_user_demands_id(committee_id)

    def get_constraint_label_id(self, committee_id):
        return self.venue.get_constraint_label_id(committee_id)

    def get_message_id(self, committee_id=None, number=None, name='Message'):
        return self.venue.get_message_id(committee_id=committee_id, number=number, name=name)

    def get_recommendation_id(self, committee_id=None):
        return self.venue.get_recommendation_id(committee_id)

    def get_paper_group_prefix(self, number=None):
        return self.venue.get_paper_group_prefix(number)

    def get_invitation_id(self, name, number = None, prefix = None):
        return self.venue.get_invitation_id(name, number, prefix)

    def get_committee(self, number = None, submitted_reviewers = False, with_authors = False):
        return self.venue.get_committee(number, submitted_reviewers, with_authors)

    def get_committee_id(self, name, number=None):
        return self.venue.get_committee_id(name, number)

    def get_committee_id_invited(self, committee_name):
        return self.venue.get_committee_id_invited(committee_name)

    def get_committee_id_declined(self, committee_name):
        return self.venue.get_committee_id_declined(committee_name)

    def get_anon_reviewer_id(self, number, anon_id, name=None):
        return self.venue.get_anon_reviewer_id(number,  anon_id, name)

    def get_reviewers_name(self, pretty=True):
        return self.venue.get_reviewers_name(pretty)

    def get_anon_committee_name(self, name):
        return self.venue.get_anon_committee_name(name)

    def get_anon_reviewers_name(self, pretty=True):
        return self.venue.get_anon_reviewers_name(pretty)

    def get_ethics_reviewers_name(self, pretty=True):
        return self.venue.get_ethics_reviewers_name(pretty)

    def anon_ethics_reviewers_name(self, pretty=True):
        return self.venue.anon_ethics_reviewers_name(pretty)

    def get_area_chairs_name(self, pretty=True):
        return self.venue.get_area_chairs_name(pretty)

    def get_anon_area_chairs_name(self, pretty=True):
        return self.venue.get_anon_area_chairs_name(pretty)

    def get_reviewers_id(self, number = None, anon=False, submitted=False):
        return self.venue.get_reviewers_id(number, anon, submitted)

    def get_authors_id(self, number = None):
        return self.venue.get_authors_id(number)

    def get_authors_accepted_id(self, number = None):
        return self.venue.get_authors_accepted_id(number)

    def get_program_chairs_id(self):
        return self.venue.get_program_chairs_id()

    def get_area_chairs_id(self, number = None, anon=False):
        return self.venue.get_area_chairs_id(number, anon)

    def get_secondary_area_chairs_id(self, number = None, anon=False):
        return self.venue.get_secondary_area_chairs_id(number, anon)

    def get_anon_area_chair_id(self, number, anon_id):
        return self.venue.get_anon_area_chair_id(number,  anon_id)

    def get_anon_secondary_area_chair_id(self, number, anon_id):
        return self.venue.get_anon_secondary_area_chair_id(number,  anon_id)

    def get_senior_area_chairs_id(self, number = None):
        return self.venue.get_senior_area_chairs_id(number)

    def get_ethics_chairs_id(self, number = None):
        return self.venue.get_ethics_chairs_id(number)

    def get_ethics_reviewers_id(self, number = None, anon=False):
        return self.venue.get_ethics_reviewers_id(number, anon)

    def get_publication_chairs_id(self):
        return self.venue.get_publication_chairs_id()

    def get_withdrawal_id(self, number = None):
        return self.venue.get_withdrawal_id(number)

    def get_withdrawn_id(self):
        return self.venue.get_withdrawn_id()

    def get_desk_rejection_id(self, number = None):
        return self.venue.get_desk_rejection_id(number)

    def get_desk_rejected_id(self):
        return self.venue.get_desk_rejected_id()

    def get_group_recruitment_id(self, committee_name):
        return self.venue.get_group_recruitment_id(committee_name)

    def get_participants(self, number=None, with_program_chairs=False, with_authors=False):
        return self.venue.get_participants(number, with_program_chairs, with_authors)

    def get_submission_venue_id(self, submission_invitation_name=None):
        return self.venue.get_submission_venue_id(submission_invitation_name)

    def get_withdrawn_submission_venue_id(self, submission_invitation_name=None):
        return self.venue.get_withdrawn_submission_venue_id(submission_invitation_name)

    def get_desk_rejected_submission_venue_id(self, submission_invitation_name=None):
        return self.venue.get_desk_rejected_submission_venue_id(submission_invitation_name)

    def get_rejected_submission_venue_id(self, submission_invitation_name=None):
        return self.venue.get_rejected_submission_venue_id(submission_invitation_name)

    def get_submissions(self, venueid=None, accepted=False, sort='tmdate', details=None):
        return self.venue.get_submissions(venueid, accepted, sort, details)

    def expire_invitation(self, invitation_id):
        return self.venue.expire_invitation(invitation_id)

    def setup(self, program_chair_ids=[], publication_chairs_ids=[]):
        setup_value = self.venue.setup(program_chair_ids, publication_chairs_ids)

        with open(os.path.join(os.path.dirname(__file__), 'webfield/homepageWebfield.js')) as f:
            content = f.read()
            self.client.post_group_edit(
                invitation=self.get_meta_invitation_id(),
                signatures=[self.venue_id],
                group=openreview.api.Group(
                    id=self.venue_id,
                    web=content
                )
            )

        with open(os.path.join(os.path.dirname(__file__), 'webfield/programChairsWebfield.js')) as f:
            content = f.read()
            self.client.post_group_edit(
                invitation=self.get_meta_invitation_id(),
                signatures=[self.venue_id],
                group=openreview.api.Group(
                    id=self.get_program_chairs_id(),
                    web=content
                )
            )

        with open(os.path.join(os.path.dirname(__file__), 'webfield/seniorAreaChairsWebfield.js')) as f:
            content = f.read()
            self.client.post_group_edit(
                invitation=self.get_meta_invitation_id(),
                signatures=[self.venue_id],
                group=openreview.api.Group(
                    id=self.get_senior_area_chairs_id(),
                    web=content
                )
            )

        with open(os.path.join(os.path.dirname(__file__), 'webfield/ethicsChairsWebfield.js')) as f:
            content = f.read()
            self.client.post_group_edit(
                invitation=self.get_meta_invitation_id(),
                signatures=[self.venue_id],
                group=openreview.api.Group(
                    id=self.get_ethics_chairs_id(),
                    web=content
                )
            )

        setup_arr_invitations(self.invitation_builder)
        return setup_value

    def set_impersonators(self, impersonators):
        return self.venue.set_impersonators(impersonators)

    def recruit_reviewers(self,
        title,
        message,
        invitees = [],
        reviewers_name = 'Reviewers',
        remind = False,
        invitee_names = [],
        retry_declined = False,
        contact_info = '',
        reduced_load_on_decline = None,
        allow_accept_with_reduced_load = False,
        default_load= 0,
        allow_overlap_official_committee = False,
        accept_recruitment_template=None
    ):
        return self.venue.recruit_reviewers(
            title,
            message,
            invitees = invitees,
            reviewers_name = reviewers_name,
            remind = remind,
            invitee_names = invitee_names,
            retry_declined = retry_declined,
            contact_info = contact_info,
            reduced_load_on_decline = reduced_load_on_decline,
            allow_accept_with_reduced_load = allow_accept_with_reduced_load,
            default_load= default_load,
            allow_overlap_official_committee = allow_overlap_official_committee,
            accept_recruitment_template=accept_recruitment_template
        )

    # For stage invitations, pass value to inner venue objects
    def create_submission_stage(self):
        stage_value = self.venue.create_submission_stage()
        invitation = self.client.get_invitation(self.get_submission_id())
        invitation.preprocess = self.invitation_builder.get_process_content('process/submission_preprocess.py')
        invitation.process = invitation.process + self.invitation_builder.get_process_content('process/submission_process_extension.py')
        invitation.signatures=['~Super_User1']
        self.client.post_invitation_edit(
            invitations=self.venue.get_meta_invitation_id(),
            readers=[self.venue_id],
            writers=[self.venue_id],
            signatures=[self.venue_id],
            replacement=False,
            invitation=invitation
        )
        return stage_value

    def create_post_submission_stage(self):
        return self.venue.create_post_submission_stage()

    def create_submission_revision_stage(self):
        self.venue.submission_revision_stage = self.submission_revision_stage
        return self.venue.create_submission_revision_stage()

    def create_review_stage(self):
        self.venue.review_stage = self.review_stage
        self.venue.review_stage.process_path = '../arr/process/review_process.py'
        self.venue.review_stage.preprocess_path = '../arr/process/review_preprocess.py'

        return self.venue.create_review_stage()

    def create_review_rebuttal_stage(self):
        self.venue.review_rebuttal_stage = None
        return self.venue.create_review_rebuttal_stage()

    def create_meta_review_stage(self):
        self.venue.meta_review_stage = self.meta_review_stage
        self.venue.meta_review_stage.process_path = '../arr/process/metareview_process.py'
        self.venue.meta_review_stage.preprocess_path = '../arr/process/review_preprocess.py'

        return self.venue.create_meta_review_stage()

    def create_registration_stages(self):
        self.venue.registration_stages = self.registration_stages
        return self.venue.create_registration_stages()

    def setup_post_submission_stage(self, force=False, hide_fields=[]):
        return self.venue.setup_post_submission_stage(force, hide_fields)

    def create_withdraw_invitations(self, reveal_authors=None, reveal_submission=None, email_pcs=None, hide_fields=[]):
        return self.venue.create_withdraw_invitations(reveal_authors, reveal_submission, email_pcs, hide_fields)

    def create_desk_reject_invitations(self, reveal_authors=None, reveal_submission=None, hide_fields=[]):
        return self.venue.create_desk_reject_invitations(reveal_authors, reveal_submission, hide_fields)

    def create_bid_stages(self):
        self.venue.bid_stages = self.bid_stages
        return self.venue.create_bid_stages()

    def create_comment_stage(self):
        self.venue.comment_stage = self.comment_stage
        return self.venue.create_comment_stage()

    def create_decision_stage(self):
        self.venue.decision_stage = self.decision_stage
        return self.venue.create_decision_stage()

    def create_custom_stage(self):
        self.venue.custom_stage = self.custom_stage
        return self.venue.create_custom_stage()

    def create_ethics_review_stage(self):
        self.venue.ethics_review_stage = self.ethics_review_stage
        stage_value = self.venue.create_ethics_review_stage()
        self.client.post_invitation_edit(
            invitations=self.venue.get_meta_invitation_id(),
            signatures=[self.venue_id],
            replacement=False,
            invitation=openreview.api.Invitation(
                id=f"{self.venue_id}/-/{self.ethics_review_stage.name}_Flag",
                content={
                    'ae_checklist_name': {
                        'value': 'Action_Editor_Checklist'
                    },
                    'reviewer_checklist_name': {
                        'value': 'Reviewer_Checklist'
                    }
                }
            )
        )
        return stage_value

    def update_conflict_policies(self, committee_id, compute_conflicts, compute_conflicts_n_years):
        return self.venue.update_conflict_policies(committee_id,  compute_conflicts,  compute_conflicts_n_years)

    def post_decisions(self, decisions_file, api1_client):
        return self.venue.post_decisions(decisions_file,  api1_client)

    def post_decision_stage(self, reveal_all_authors=False, reveal_authors_accepted=False, decision_heading_map=None, submission_readers=None, hide_fields=[]):
        return self.venue.post_decision_stage(reveal_all_authors, reveal_authors_accepted, decision_heading_map, submission_readers, hide_fields)

    def send_decision_notifications(self, decision_options, messages):
        return self.venue.send_decision_notifications(decision_options,  messages)

    def setup_committee_matching(self, committee_id=None, compute_affinity_scores=False, compute_conflicts=False, compute_conflicts_n_years=None, alternate_matching_group=None, submission_track=None):
        return self.venue.setup_committee_matching(committee_id, compute_affinity_scores, compute_conflicts, compute_conflicts_n_years, alternate_matching_group, submission_track)

    def set_assignments(self, assignment_title, committee_id, enable_reviewer_reassignment=False, overwrite=False):
        return self.venue.set_assignments(assignment_title,  committee_id, enable_reviewer_reassignment, overwrite)

    def unset_assignments(self, assignment_title, committee_id):
        return self.venue.unset_assignments(assignment_title, committee_id)

    def setup_assignment_recruitment(self, committee_id, hash_seed, due_date, assignment_title=None, invitation_labels={}, email_template=None):
        return self.venue.setup_assignment_recruitment(committee_id,  hash_seed,  due_date, assignment_title, invitation_labels, email_template)

    def set_track_sac_assignments(self, track_sac_file, conflict_policy=None, conflict_n_years=None, track_ac_file=None):
        return self.venue.set_track_sac_assignments(track_sac_file, conflict_policy, conflict_n_years, track_ac_file)

    def set_SAC_ethics_review_process(self, sac_ethics_flag_duedate=None):
        return self.venue.set_SAC_ethics_review_process(sac_ethics_flag_duedate)

    def open_reviewer_recommendation_stage(self, start_date=None, due_date=None, total_recommendations=7):
        return self.venue.open_reviewer_recommendation_stage(start_date, due_date, total_recommendations)
    
    @classmethod
    def process_commitment_venue(ARR, client, venue_id, invitation_reply_ids=['Official_Review', 'Meta_Review']):

        def add_readers_to_note(note, readers):
            if readers[0] in note.readers:
                return
            
            domain = note.domain
            client.post_note_edit(
                invitation = f'{domain}/-/Edit',
                readers = [domain],
                signatures = [domain],
                writers = [domain],
                note = openreview.api.Note(
                    id = note.id,
                    readers = {
                        'append': readers
                    }
                )            
            )    

        def create_readers_group(submission):
            domain = submission.domain

            commitment_readers_group_id = f'{domain}/Submission{submission.number}/Commitment_Readers'

            commitment_readers_group = openreview.tools.get_group(client, commitment_readers_group_id)

            if commitment_readers_group:
                print(f'Group already exists, add members {venue_id} to it.')
                client.add_members_to_group(commitment_readers_group_id, [venue_id])
                return

            print(f'Creating group {commitment_readers_group_id} for submission {submission.number}.')
            client.post_group_edit(
                invitation = f'{domain}/-/Edit',
                readers = [domain],
                signatures = [domain],
                writers = [domain],
                group = openreview.api.Group(
                    id = commitment_readers_group_id,
                    signatures = [domain],
                    writers = [domain],
                    readers = [domain],
                    members = [venue_id]
                )
            )

        def add_readers_to_arr_submission(submission):

            domain = submission.domain
            commitment_readers_group_id = f'{domain}/Submission{submission.number}/Commitment_Readers'

            print(f'Add group as reader of the submission')
            if 'everyone' not in submission.readers:
                add_readers_to_note(submission, [commitment_readers_group_id])

            print(f'Add group as reader of the submission review and meta reviews')
            replies = client.get_notes(forum = submission.id)

            for reply in replies:
                for invitation_reply_id in invitation_reply_ids:
                    if invitation_reply_id in reply.invitations[0]:
                        add_readers_to_note(reply, [commitment_readers_group_id])
        
        venue_group = client.get_group(venue_id)

        is_commitment_venue = venue_group.content.get('commitments_venue', {}).get('value', False)

        if not is_commitment_venue:
            raise openreview.OpenReviewException(f'{venue_id} is not a commitment venue')  
        
        submission_id = venue_group.content.get('submission_id', {}).get('value')

        commitment_submissions = client.get_all_notes(invitation=submission_id)

        for note in commitment_submissions:
            arr_submission_link = note.content['paper_link']['value']
            arr_submission_id = arr_submission_link.split('=')[-1]
            arr_submission = openreview.tools.get_note(client, arr_submission_id)
            if arr_submission:
                print('API 2 submission found', arr_submission.id, arr_submission.number, arr_submission.invitations[0])
                create_readers_group(arr_submission)
                add_readers_to_arr_submission(arr_submission)        
        
        return True
