import csv
import json
import re
import io
import datetime
import requests
from io import StringIO
from multiprocessing import cpu_count
from concurrent.futures import ThreadPoolExecutor
from tqdm import tqdm
import openreview
from openreview import tools
from .invitation import InvitationBuilder
from .group import GroupBuilder
from .edit_invitation import EditInvitationBuilder
from openreview.api import Group
from openreview.api import Note
from .recruitment import Recruitment
from . import matching

class Venue(object):

    def __init__(self, client, venue_id, support_user):

        self.client = client
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
        self.reviewer_roles = ['Reviewers']
        self.reviewers_name = self.reviewer_roles[0]
        self.area_chair_roles = ['Area_Chairs']
        self.area_chairs_name = self.area_chair_roles[0]
        self.senior_area_chair_roles = ['Senior_Area_Chairs']        
        self.senior_area_chairs_name = self.senior_area_chair_roles[0]
        self.secondary_area_chairs_name = 'Secondary_Area_Chairs'
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
        self.edit_invitation_builder = EditInvitationBuilder(self)
        self.reviewer_identity_readers = []
        self.area_chair_identity_readers = []
        self.senior_area_chair_identity_readers = []
        self.automatic_reviewer_assignment = False
        self.decision_heading_map = {}
        self.allow_gurobi_solver = False
        self.submission_license = ['CC BY 4.0']
        self.use_publication_chairs = False
        self.source_submissions_query_mapping = {}
        self.sac_paper_assignments = False
        self.submission_assignment_max_reviewers = None
        self.preferred_emails_groups = []
        self.iThenticate_plagiarism_check = False
        self.iThenticate_plagiarism_check_api_key = ''
        self.iThenticate_plagiarism_check_api_base_url = ''
        self.iThenticate_plagiarism_check_committee_readers = []

    def get_id(self):
        return self.venue_id

    def get_short_name(self):
        return self.short_name
    
    def get_message_sender(self):

        fromEmail = self.short_name.replace(' ', '').replace(':', '-').replace('@', '').replace('(', '').replace(')', '').replace(',', '-').lower()
        fromEmail = f'{fromEmail}-notifications@openreview.net'
        
        email_regex = re.compile("^[a-z0-9!#$%&'*+/=?^_`{|}~-]+(?:\.[a-z0-9!#$%&'*+/=?^_`{|}~-]+)*@(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.)+[a-z0-9](?:[a-z0-9-]*[a-z0-9])?$")        

        if not email_regex.match(fromEmail):
            raise openreview.OpenReviewException(f'Invalid email address: {fromEmail}')
        
        return {
            'fromName': self.short_name,
            'fromEmail': fromEmail
        }
    
    def get_edges_archive_date(self):
        archive_date = datetime.datetime.utcnow()
        if self.start_date:
            try:
                archive_date = datetime.datetime.strptime(self.start_date, '%Y/%m/%d')
            except ValueError:
                print(f'Error parsing venue date {self.start_date}')

        return openreview.tools.datetime_millis(archive_date + datetime.timedelta(weeks=52)) ## archive edges after 1 year
        

    def get_committee_name(self, committee_id, pretty=False):
        name = committee_id.split('/')[-1]

        if pretty:
            name = name.replace('_', ' ')
            if name.endswith('s'):
                return name[:-1]
        return name

    def get_committee_names(self):
        committee=[self.reviewers_name]

        if self.use_area_chairs:
            committee.append(self.area_chairs_name)

        if self.use_senior_area_chairs:
            committee.append(self.senior_area_chairs_name)

        return committee

    def get_roles(self):
        roles = self.reviewer_roles
        if self.use_area_chairs:
            roles = self.reviewer_roles + self.area_chair_roles
        if self.use_senior_area_chairs:
            roles = roles + self.senior_area_chair_roles
        if self.use_ethics_chairs:
            roles = roles + [self.ethics_chairs_name]
        if self.use_ethics_reviewers:
            roles = roles + [self.ethics_reviewers_name]            
        return roles
    
    def submission_tracks(self):
        return self.submission_stage.get_submission_tracks()

    def get_meta_invitation_id(self):
        return f'{self.venue_id}/-/Edit'

    def get_submission_id(self):
        return self.submission_stage.get_submission_id(self)
    
    def get_post_submission_id(self):
        submission_name = self.submission_stage.name        
        return self.get_invitation_id(f'Post_{submission_name}')    

    def get_pc_submission_revision_id(self):
        return self.get_invitation_id('PC_Revision')

    def get_recruitment_id(self, committee_id):
        return self.get_invitation_id('Recruitment', prefix=committee_id)

    def get_expertise_selection_id(self, committee_id):
        return self.get_invitation_id(self.expertise_selection_stage.name if self.expertise_selection_stage else 'Expertise_Selection', prefix=committee_id)    

    def get_bid_id(self, committee_id):
        return self.get_invitation_id('Bid', prefix=committee_id)

    def get_assignment_id(self, committee_id, deployed=False, invite=False):
        if deployed:
            return self.get_invitation_id('Assignment', prefix=committee_id)
        if invite:
            return self.get_invitation_id('Invite_Assignment', prefix=committee_id)
        return self.get_invitation_id('Proposed_Assignment', prefix=committee_id)

    def get_matching_setup_id(self, committee_id):
        return self.get_invitation_id('Matching_Setup', prefix=committee_id)
    
    def get_affinity_score_id(self, committee_id):
        return self.get_invitation_id('Affinity_Score', prefix=committee_id)

    def get_conflict_score_id(self, committee_id):
        return self.get_invitation_id('Conflict', prefix=committee_id)

    def get_custom_max_papers_id(self, committee_id):
        return self.get_invitation_id('Custom_Max_Papers', prefix=committee_id)
    
    def get_custom_user_demands_id(self, committee_id):
        return self.get_invitation_id('Custom_User_Demands', prefix=committee_id)    
    
    def get_constraint_label_id(self, committee_id):
        return self.get_invitation_id('Constraint_Label', prefix=committee_id)

    def get_message_id(self, committee_id=None, number=None, name='Message'):
        return self.get_invitation_id(name, prefix=committee_id, number=number)

    def get_recommendation_id(self, committee_id=None):
        if not committee_id:
            committee_id = self.get_reviewers_id()
        return self.get_invitation_id(self.recommendation_name, prefix=committee_id)

    def get_paper_group_prefix(self, number=None):
        prefix = f'{self.venue_id}/{self.submission_stage.name}'
        if number:
            prefix = f'{prefix}{number}'
        return prefix
    
    def get_invitation_id(self, name, number = None, prefix = None):
        invitation_id = self.id
        if prefix:
            invitation_id = prefix
        if number:
            invitation_id = f'{self.get_paper_group_prefix(number)}/-/'
        else:
            invitation_id = invitation_id + '/-/'

        invitation_id =  invitation_id + name
        return invitation_id

    def get_committee(self, number = None, submitted_reviewers = False, with_authors = False):
        committee = []

        if with_authors:
            committee.append(self.get_authors_id(number))

        if submitted_reviewers:
            committee.append(self.get_reviewers_id(number, submitted=True))
        else:
            committee.append(self.get_reviewers_id(number))

        if self.use_area_chairs:
            committee.append(self.get_area_chairs_id(number))

        if self.use_senior_area_chairs:
            committee.append(self.get_senior_area_chairs_id(number))

        committee.append(self.get_program_chairs_id())

        return committee

    def get_committee_id(self, name, number=None):
        committee_id = self.id + '/'
        if number:
            committee_id = f'{self.get_paper_group_prefix(number)}/{name}'
        else:
            committee_id = committee_id + name
        return committee_id

    def get_committee_id_invited(self, committee_name):
        return self.get_committee_id(committee_name) + '/Invited'

    def get_committee_id_declined(self, committee_name):
        return self.get_committee_id(committee_name) + '/Declined'

    ## Compatibility with Conference, refactor conference references to use get_reviewers_id
    def get_anon_reviewer_id(self, number, anon_id, name=None):
        if name == self.ethics_reviewers_name:
            return self.get_ethics_reviewers_id(number, True)
        return self.get_reviewers_id(number, True)

    def get_reviewers_name(self, pretty=True):
        if pretty:
            return self.get_committee_name(self.reviewers_name, pretty)
        return self.reviewers_name
    
    def get_anon_committee_name(self, name):
        rev_name = name[:-1] if name.endswith('s') else name
        return rev_name + '_'         
    
    def get_anon_reviewers_name(self, pretty=True):
        return self.get_anon_committee_name(self.reviewers_name)

    def get_ethics_reviewers_name(self, pretty=True):
        if pretty:
            return self.get_committee_name(self.ethics_reviewers_name, pretty)
        return self.ethics_reviewers_name

    def anon_ethics_reviewers_name(self, pretty=True):
        return self.get_anon_committee_name(self.ethics_reviewers_name)

    def get_area_chairs_name(self, pretty=True):
        if pretty:
            return self.get_committee_name(self.area_chairs_name, pretty)
        return self.area_chairs_name

    def get_anon_area_chairs_name(self, pretty=True):
        return self.get_anon_committee_name(self.area_chairs_name)

    def get_reviewers_id(self, number = None, anon=False, submitted=False):
        rev_name = self.get_anon_reviewers_name()
        reviewers_id = self.get_committee_id(f'{rev_name}.*' if anon else self.reviewers_name, number)
        if submitted:
            return reviewers_id + '/Submitted'
        return reviewers_id

    def get_authors_id(self, number = None):
        return self.get_committee_id(self.authors_name, number)

    def get_authors_accepted_id(self, number = None):
        return self.get_committee_id(self.authors_name) + '/Accepted'

    def get_program_chairs_id(self):
        return self.get_committee_id(self.program_chairs_name)

    def get_area_chairs_id(self, number = None, anon=False):
        ac_name = self.get_anon_area_chairs_name()
        return self.get_committee_id(f'{ac_name}.*' if anon else self.area_chairs_name, number)
    
    def get_secondary_area_chairs_id(self, number = None, anon=False):
        ac_name = self.get_anon_committee_name(self.secondary_area_chairs_name)
        return self.get_committee_id(f'{ac_name}.*' if anon else self.secondary_area_chairs_name, number)    

    ## Compatibility with Conference, refactor conference references to use get_area_chairs_id
    def get_anon_area_chair_id(self, number, anon_id):
        return self.get_area_chairs_id(number, True)

    def get_anon_secondary_area_chair_id(self, number, anon_id):
        return self.get_secondary_area_chairs_id(number, True)

    def get_senior_area_chairs_id(self, number = None):
        return self.get_committee_id(self.senior_area_chairs_name, number)

    def get_ethics_chairs_id(self, number = None):
        return self.get_committee_id(self.ethics_chairs_name, number)

    def get_ethics_reviewers_id(self, number = None, anon=False):
        rev_name = self.anon_ethics_reviewers_name()
        return self.get_committee_id(f'{rev_name}.*' if anon else self.ethics_reviewers_name, number)
    
    def get_publication_chairs_id(self):
        return self.get_committee_id('Publication_Chairs')

    def get_withdrawal_id(self, number = None):
        return self.get_invitation_id(self.submission_stage.withdrawal_name, number)

    def get_withdrawn_id(self):
        return self.get_invitation_id(f'Withdrawn_{self.submission_stage.name}')

    def get_desk_rejection_id(self, number = None):
        return self.get_invitation_id(self.submission_stage.desk_rejection_name, number)

    def get_desk_rejected_id(self):
        return self.get_invitation_id(f'Desk_Rejected_{self.submission_stage.name}')
    
    def get_group_recruitment_id(self, committee_name):
        return self.get_invitation_id(name='Recruitment', prefix=self.get_committee_id_invited(committee_name))
    
    def get_iThenticate_plagiarism_check_invitation_id(self):
        return self.get_invitation_id('iThenticate_Plagiarism_Check')

    def get_participants(self, number=None, with_program_chairs=False, with_authors=False):
        committee = []
        if with_program_chairs:
            committee.append(self.get_program_chairs_id())
        if self.use_senior_area_chairs:
            committee.append(self.get_senior_area_chairs_id(number))
        if self.use_area_chairs:
            committee.append(self.get_area_chairs_id(number))
        committee.append(self.get_reviewers_id(number))
        if with_authors:
            committee.append(self.get_authors_id(number))
        return committee

    def get_submission_venue_id(self, submission_invitation_name=None):
        if submission_invitation_name:
            return f'{self.venue_id}/{submission_invitation_name}'
        if self.submission_stage:
            return f'{self.venue_id}/{self.submission_stage.name}'
        return f'{self.venue_id}/Submission'

    def get_withdrawn_submission_venue_id(self, submission_invitation_name=None):
        if submission_invitation_name:
            return f'{self.venue_id}/Withdrawn_{submission_invitation_name}'
        if self.submission_stage:
            return f'{self.venue_id}/Withdrawn_{self.submission_stage.name}'
        return f'{self.venue_id}/Withdrawn_Submission' 

    def get_desk_rejected_submission_venue_id(self, submission_invitation_name=None):
        if submission_invitation_name:
            return f'{self.venue_id}/Desk_Rejected_{submission_invitation_name}'
        if self.submission_stage:
            return f'{self.venue_id}/Desk_Rejected_{self.submission_stage.name}'
        return f'{self.venue_id}/Desk_Rejected_Submission'                

    def get_rejected_submission_venue_id(self, submission_invitation_name=None):
        if submission_invitation_name:
            return f'{self.venue_id}/Rejected_{submission_invitation_name}'
        if self.submission_stage:
            return f'{self.venue_id}/Rejected_{self.submission_stage.name}'
        return f'{self.venue_id}/Rejected_Submission'

    def get_preferred_emails_invitation_id(self):
        return f'{self.venue_id}/-/Preferred_Emails' 

    def get_submissions(self, venueid=None, accepted=False, sort='tmdate', details=None):
        if accepted:
            accepted_notes = self.client.get_all_notes(content={ 'venueid': self.venue_id}, sort=sort)
            if len(accepted_notes) == 0:
                accepted_notes = []
                notes = self.client.get_all_notes(content={ 'venueid': f'{self.get_submission_venue_id()}'}, sort=sort, details='directReplies')
                for note in notes:
                    for reply in note.details['directReplies']:
                        if f'{self.venue_id}/{self.submission_stage.name}{note.number}/-/{self.decision_stage.name}' in reply['invitations']:
                            decision = reply['content']['decision']['value']
                            if openreview.tools.is_accept_decision(decision, self.decision_stage.accept_options):
                                accepted_notes.append(note)
            return accepted_notes
        else:
            notes = self.client.get_all_notes(content={ 'venueid': venueid if venueid else f'{self.get_submission_venue_id()}'}, sort=sort, details=details)
            if len(notes) == 0:
                notes = self.client.get_all_notes(content={ 'venueid': self.venue_id}, sort=sort, details=details)
                rejected = self.client.get_all_notes(content={ 'venueid': self.get_rejected_submission_venue_id()}, sort=sort, details=details)
                if rejected:
                    notes.extend(rejected)
            return notes

    #use to expire revision invitations from request form
    def expire_invitation(self, invitation_id):

        invitation_name = invitation_id.split('/-/')[-1]

        notes = self.get_submissions()
        for note in notes:
            invitation = f'{self.venue_id}/{self.submission_stage.name}{note.number}/-/{invitation_name}'
            self.invitation_builder.expire_invitation(invitation)

    def setup(self, program_chair_ids=[], publication_chairs_ids=[]):
    
        self.invitation_builder.set_meta_invitation()

        self.group_builder.create_venue_group()

        self.group_builder.add_to_active_venues()

        self.group_builder.create_program_chairs_group(program_chair_ids)

        self.group_builder.create_authors_group()

        self.group_builder.create_reviewers_group()
        
        if self.use_area_chairs:
            self.group_builder.create_area_chairs_group()

        if self.use_senior_area_chairs:
            self.group_builder.create_senior_area_chairs_group()

        if self.use_ethics_reviewers:
            self.group_builder.create_ethics_reviewers_group()

        if self.use_ethics_chairs:
            self.group_builder.create_ethics_chairs_group()

        if self.use_publication_chairs:
            self.group_builder.create_publication_chairs_group(publication_chairs_ids)

    def set_impersonators(self, impersonators):
        self.group_builder.set_impersonators(impersonators)

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
        accept_recruitment_template=None):

        return self.recruitment.invite_committee(title,
            message,
            invitees,
            reviewers_name,
            remind,
            invitee_names,
            retry_declined,
            contact_info,
            reduced_load_on_decline,
            allow_accept_with_reduced_load,
            # default_load, ##can this be removed? We never get it from the request form
            allow_overlap_official_committee)

    def create_submission_stage(self):
        self.invitation_builder.set_submission_invitation()
        self.invitation_builder.set_withdrawal_invitation()
        self.invitation_builder.set_desk_rejection_invitation()
        self.invitation_builder.set_post_submission_invitation()
        self.invitation_builder.set_pc_submission_revision_invitation()
        self.invitation_builder.set_submission_reviewer_group_invitation()
        self.invitation_builder.set_submission_message_invitation()
        if self.use_area_chairs:
            self.invitation_builder.set_submission_area_chair_group_invitation()
        if self.use_senior_area_chairs:
            self.invitation_builder.set_submission_senior_area_chair_group_invitation()
        if self.expertise_selection_stage:
            self.invitation_builder.set_expertise_selection_invitations()

        if self.submission_stage.second_due_date:
            stage = self.submission_stage
            submission_revision_stage = openreview.stages.SubmissionRevisionStage(name='Full_Submission',
                start_date=stage.exp_date,
                due_date=stage.second_due_date,
                additional_fields=stage.second_deadline_additional_fields if stage.second_deadline_additional_fields else stage.additional_fields,
                remove_fields=stage.second_deadline_remove_fields if stage.second_deadline_remove_fields else stage.remove_fields,
                only_accepted=False,
                multiReply=True,
                allow_author_reorder=stage.author_reorder_after_first_deadline,
                allow_license_edition=True
            )
            self.invitation_builder.set_submission_revision_invitation(submission_revision_stage)
            self.invitation_builder.set_submission_deletion_invitation(submission_revision_stage)

    def create_submission_edit_invitations(self):
        self.edit_invitation_builder.set_edit_submission_deadlines_invitation(self.get_submission_id(), 'edit_submission_deadline_process.py')
        self.edit_invitation_builder.set_edit_submission_content_invitation(self.get_submission_id())
        self.edit_invitation_builder.set_edit_submission_notification_invitation()
        self.edit_invitation_builder.set_edit_submission_readers_invitation()
        self.edit_invitation_builder.set_edit_submission_field_readers_invitation()

    def create_review_edit_invitations(self):
        review_stage = self.review_stage
        review_invitation_id = self.get_invitation_id(review_stage.name)
        self.edit_invitation_builder.set_edit_deadlines_invitation(review_invitation_id)
        content = {
            'rating_field_name': {
                'value': {
                    'param': {
                        'type': 'string',
                        'regex': '.*',
                        'default': 'rating'
                    }
                }
            },
            'confidence_field_name': {
                'value': {
                    'param': {
                        'type': 'string',
                        'regex': '.*',
                        'default': 'confidence'
                    }
                }
            }
        }
        self.edit_invitation_builder.set_edit_content_invitation(review_invitation_id, content, 'edit_review_field_names_process.py')
        self.edit_invitation_builder.set_edit_reply_readers_invitation(review_invitation_id)

    def create_post_submission_stage(self):

        self.invitation_builder.set_post_submission_invitation()

    def create_submission_revision_stage(self):
        return self.invitation_builder.set_submission_revision_invitation()

    def create_review_stage(self):
        return self.invitation_builder.set_review_invitation()
        
    def create_review_rebuttal_stage(self):
        return self.invitation_builder.set_review_rebuttal_invitation()

    def create_meta_review_stage(self):
        return self.invitation_builder.set_meta_review_invitation()

    def create_registration_stages(self):
        return self.invitation_builder.set_registration_invitations()
    
    def setup_post_submission_stage(self, force=False, hide_fields=[]):
        ## do nothing
        return True
    
    def create_withdraw_invitations(self, reveal_authors=None, reveal_submission=None, email_pcs=None, hide_fields=[]):
        ## deprecated
        return self.invitation_builder.set_withdrawal_invitation()
    
    def create_desk_reject_invitations(self, reveal_authors=None, reveal_submission=None, hide_fields=[]):
        ## deprecated
        return self.invitation_builder.set_desk_rejection_invitation()

    def create_bid_stages(self):
        self.invitation_builder.set_bid_invitations()

    def create_comment_stage(self):
        self.invitation_builder.set_official_comment_invitation()
        if self.comment_stage.allow_public_comments:
            self.invitation_builder.set_public_comment_invitation()

        self.invitation_builder.set_chat_invitation()

    def create_decision_stage(self):
        invitation = self.invitation_builder.set_decision_invitation()

        decision_file = self.decision_stage.decisions_file
        if decision_file:

            baseurl = 'http://localhost:3000'
            if 'https://devapi' in self.client.baseurl:
                baseurl = 'https://devapi.openreview.net'
            if 'https://api' in self.client.baseurl:
                baseurl = 'https://api.openreview.net'
            api1_client = openreview.Client(baseurl=baseurl, token=self.client.token)

            if '/attachment' in decision_file:
                decisions = api1_client.get_attachment(id=self.request_form_id, field_name='decisions_file')

            else:
                with open(decision_file, 'rb') as file_handle:
                    decisions = file_handle.read()

            self.post_decisions(decisions, api1_client)

    def create_custom_stage(self):
        return self.invitation_builder.set_custom_stage_invitation()
    
    def create_ethics_review_stage(self):

        flag_invitation = self.invitation_builder.set_ethics_stage_invitation()
        self.invitation_builder.set_ethics_paper_groups_invitation()
        self.invitation_builder.update_review_invitations()
        self.invitation_builder.set_ethics_review_invitation()
        if self.ethics_review_stage.enable_comments:
            self.invitation_builder.set_official_comment_invitation()

        # setup paper matching
        ethics_chairs_group = tools.get_group(self.client, self.get_ethics_chairs_id())
        tools.replace_members_with_ids(self.client, ethics_chairs_group)
        group = tools.get_group(self.client, id=self.get_ethics_reviewers_id())
        if group and len(group.members) > 0:
            self.setup_committee_matching(group.id, compute_affinity_scores=self.ethics_review_stage.compute_affinity_scores, compute_conflicts=True)
            self.invitation_builder.set_assignment_invitation(group.id)

        flagged_submission_numbers = self.ethics_review_stage.submission_numbers
        print(flagged_submission_numbers)
        notes = self.get_submissions()
        for note in notes:
            if note.number in flagged_submission_numbers:
                self.client.post_note_edit(
                    invitation=flag_invitation.id,
                    note=openreview.api.Note(
                        id=note.id
                    ),
                    signatures=[self.venue_id]
                )

    def update_conflict_policies(self, committee_id, compute_conflicts, compute_conflicts_n_years):
        content = {}
        if committee_id == self.get_reviewers_id():
            content['reviewers_conflict_policy'] = { 'value': compute_conflicts } if compute_conflicts else { 'delete': True}
            content['reviewers_conflict_n_years'] = { 'value': compute_conflicts_n_years } if compute_conflicts_n_years else { 'delete': True}

        if committee_id == self.get_area_chairs_id():
            content['area_chairs_conflict_policy'] = { 'value': compute_conflicts } if compute_conflicts else { 'delete': True}
            content['area_chairs_conflict_n_years'] = { 'value': compute_conflicts_n_years } if compute_conflicts_n_years else { 'delete': True}

        if content:
            self.client.post_group_edit(
                invitation=self.get_meta_invitation_id(),
                readers=[self.venue_id],
                writers=[self.venue_id],
                signatures=[self.venue_id],
                group=openreview.api.Group(
                    id=self.venue_id,
                    content=content
                )
            )

    def post_decisions(self, decisions_file, api1_client):

        decisions_data = list(csv.reader(StringIO(decisions_file.decode()), delimiter=","))

        paper_notes = {n.number: n for n in self.get_submissions(details='directReplies')}

        def post_decision(paper_decision):
            if len(paper_decision) < 2:
                raise openreview.OpenReviewException(
                    "Not enough values provided in the decision file. Expected values are: paper_number, decision, comment")
            if len(paper_decision) > 3:
                raise openreview.OpenReviewException(
                    "Too many values provided in the decision file. Expected values are: paper_number, decision, comment"
                )
            if len(paper_decision) == 3:
                paper_number, decision, comment = paper_decision
            else:
                paper_number, decision = paper_decision
                comment = ''

            paper_number = int(paper_number)

            print(f"Posting Decision {decision} for Paper {paper_number}")
            paper_note = paper_notes.get(paper_number, None)
            if not paper_note:
                raise openreview.OpenReviewException(
                    f"Paper {paper_number} not found. Please check the submitted paper numbers."
                )

            paper_decision_note = None
            if paper_note.details:
                for reply in paper_note.details['directReplies']:
                    if f'{self.venue_id}/{self.submission_stage.name}{paper_note.number}/-/{self.decision_stage.name}' in reply['invitations']:
                        paper_decision_note = reply
                        break

            content = {
                'title': {'value': 'Paper Decision'},
                'decision': {'value': decision.strip()},
                'comment': {'value': comment},
            }
            if paper_decision_note:
                self.client.post_note_edit(invitation = self.get_invitation_id(self.decision_stage.name, paper_number),
                    signatures = [self.get_program_chairs_id()],
                    note = Note(
                        id = paper_decision_note['id'],
                        content = content
                    )
                )
            else:
                self.client.post_note_edit(invitation = self.get_invitation_id(self.decision_stage.name, paper_number),
                    signatures = [self.get_program_chairs_id()],
                    note = Note(
                        content = content
                    )
                )

            print(f"Decision posted for Paper {paper_number}")

        futures = []
        futures_param_mapping = {}
        gathering_responses = tqdm(total=len(decisions_data), desc='Gathering Responses')
        results = []
        errors = {}

        with ThreadPoolExecutor(max_workers=min(6, cpu_count() - 1)) as executor:
            for _decision in decisions_data:
                _future = executor.submit(post_decision, _decision)
                futures.append(_future)
                futures_param_mapping[_future] = str(_decision)

            for future in futures:
                gathering_responses.update(1)
                try:
                    results.append(future.result())
                except Exception as e:
                    errors[futures_param_mapping[future]] = e.args[0] if isinstance(e, openreview.OpenReviewException) else repr(e)

            gathering_responses.close()

        error_status = ''
        if errors:
            error_status = f'''
Total Errors: {len(errors)}
```python
{json.dumps({key: errors[key] for key in list(errors.keys())[:10]}, indent=2)}
```
'''
        if self.request_form_id:
            forum_note = api1_client.get_note(self.request_form_id)
            status_note = openreview.Note(
                invitation=self.support_user + '/-/Request' + str(forum_note.number) + '/Decision_Upload_Status',
                forum=self.request_form_id,
                replyto=self.request_form_id,
                readers=[self.get_program_chairs_id(), self.support_user],
                writers=[],
                signatures=[self.support_user],
                content={
                    'title': 'Decision Upload Status',
                    'decision_posted': f'''{len(results)} Papers''',
                    'error': error_status[:200000]
                }
            )

            api1_client.post_note(status_note)

    def post_decision_stage(self, reveal_all_authors=False, reveal_authors_accepted=False, decision_heading_map=None, submission_readers=None, hide_fields=[]):

        venue_id = self.venue_id
        submissions = self.get_submissions(sort='number:asc', details='directReplies')

        def is_release_authors(is_note_accepted):
            return reveal_all_authors or (reveal_authors_accepted and is_note_accepted)

        def decision_to_venueid(decision):
            if openreview.tools.is_accept_decision(decision, self.decision_stage.accept_options):
                return venue_id
            else:
                return self.get_rejected_submission_venue_id()

        if submission_readers:
            self.submission_stage.readers = submission_readers

        def update_note(submission):
            decision_note = None
            if submission.details:
                for reply in submission.details['directReplies']:
                    if f'{self.venue_id}/{self.submission_stage.name}{submission.number}/-/{self.decision_stage.name}' in reply['invitations']:
                        decision_note = reply
                        break
            note_accepted = decision_note and openreview.tools.is_accept_decision(decision_note['content']['decision']['value'], self.decision_stage.accept_options)
            submission_readers = self.submission_stage.get_readers(self, submission.number, decision_note['content']['decision']['value'] if decision_note else None, self.decision_stage.accept_options)

            venue = self.short_name
            decision_option = decision_note['content']['decision']['value'] if decision_note else ''
            venue = tools.decision_to_venue(venue, decision_option, self.decision_stage.accept_options)
            venueid = decision_to_venueid(decision_option)

            content = {
                'venueid': {
                    'value': venueid
                },
                'venue': {
                    'value': venue
                }
            }

            anonymous = False
            final_hide_fields = []
            final_hide_fields.extend(hide_fields)

            if not is_release_authors(note_accepted) and self.submission_stage.double_blind:
                anonymous = True
                final_hide_fields.extend(['authors', 'authorids'])

            for field, value in submission.content.items():
                if field in final_hide_fields:
                    if self.use_publication_chairs and field in ['authors', 'authorids'] and note_accepted:
                        content[field] = {
                            'readers': [venue_id, self.get_authors_id(submission.number), self.get_publication_chairs_id()]
                        }
                    else:
                        content[field] = {
                            'readers': [venue_id, self.get_authors_id(submission.number)]
                        }
                if field not in final_hide_fields and 'readers' in value:
                    content[field] = {
                        'readers': { 'delete': True }
                    }

            content['_bibtex'] = {
                'value': tools.generate_bibtex(
                    note=submission,
                    venue_fullname=self.name,
                    year=str(datetime.datetime.utcnow().year),
                    url_forum=submission.forum,
                    paper_status = 'accepted' if note_accepted else 'rejected',
                    anonymous=anonymous
                )
            }

            self.client.post_note_edit(invitation=self.get_meta_invitation_id(),
                readers=[venue_id, self.get_authors_id(submission.number)],
                writers=[venue_id],
                signatures=[venue_id],
                note=openreview.api.Note(id=submission.id,
                        readers = submission_readers,
                        content = content,
                        odate = openreview.tools.datetime_millis(datetime.datetime.utcnow()) if (submission.odate is None and 'everyone' in submission_readers) else None,
                        pdate = openreview.tools.datetime_millis(datetime.datetime.utcnow()) if (submission.pdate is None and note_accepted) else None
                    )
                )
        tools.concurrent_requests(update_note, submissions)

    def send_decision_notifications(self, decision_options, messages):
        paper_notes = self.get_submissions(details='directReplies')

        def send_notification(note):
            decision_note = None
            for reply in note.details['directReplies']:
                if f'{self.venue_id}/{self.submission_stage.name}{note.number}/-/{self.decision_stage.name}' in reply['invitations']:
                    decision_note = reply
                    break
            subject = "[{SHORT_NAME}] Decision notification for your submission {submission_number}: {submission_title}".format(
                SHORT_NAME=self.short_name,
                submission_number=note.number,
                submission_title=note.content['title']['value']
            )
            if decision_note and not self.client.get_messages(subject=subject):
                message = messages[decision_note['content']['decision']['value']]
                final_message = message.replace("{{submission_title}}", note.content['title']['value'])
                final_message = final_message.replace("{{forum_url}}", f'https://openreview.net/forum?id={note.id}')
                self.client.post_message(subject, 
                                         recipients=[self.get_authors_id(note.number)], 
                                         message=final_message, 
                                         parentGroup=self.get_authors_id(), 
                                         replyTo=self.contact, 
                                         invitation=self.get_meta_invitation_id(), 
                                         signature=self.venue_id,
                                         sender=self.get_message_sender())

        tools.concurrent_requests(send_notification, paper_notes)

    def setup_committee_matching(self, committee_id=None, compute_affinity_scores=False, compute_conflicts=False, compute_conflicts_n_years=None, alternate_matching_group=None, submission_track=None):
        if committee_id is None:
            committee_id=self.get_reviewers_id()
        if self.use_senior_area_chairs and committee_id == self.get_senior_area_chairs_id() and not alternate_matching_group and not self.sac_paper_assignments:
            alternate_matching_group = self.get_area_chairs_id()
        venue_matching = matching.Matching(self, self.client.get_group(committee_id), alternate_matching_group, { 'track': submission_track } if submission_track else None)

        return venue_matching.setup(compute_affinity_scores, compute_conflicts, compute_conflicts_n_years)

    def set_assignments(self, assignment_title, committee_id, enable_reviewer_reassignment=False, overwrite=False):

        match_group = self.client.get_group(committee_id)
        assignment_invitation = self.client.get_invitation(self.get_assignment_id(match_group.id))
        conference_matching = matching.Matching(self, match_group, submission_content=assignment_invitation.edit.get('head', {}).get('param', {}).get('withContent'))
        return conference_matching.deploy(assignment_title, overwrite, enable_reviewer_reassignment)
    
    def unset_assignments(self, assignment_title, committee_id):

        match_group = self.client.get_group(committee_id)
        conference_matching = matching.Matching(self, match_group)
        return conference_matching.undeploy(assignment_title)    

    def setup_assignment_recruitment(self, committee_id, hash_seed, due_date, assignment_title=None, invitation_labels={}, email_template=None):

        match_group = self.client.get_group(committee_id)
        conference_matching = matching.Matching(self, match_group)
        return conference_matching.setup_invite_assignment(hash_seed, assignment_title, due_date, invitation_labels=invitation_labels, email_template=email_template)
    
    def set_track_sac_assignments(self, track_sac_file, conflict_policy=None, conflict_n_years=None, track_ac_file=None):

        if not self.use_senior_area_chairs:
            raise openreview.OpenReviewException('The venue does not have senior area chairs enabled. Please enable senior area chairs in the venue.')

        if not self.submission_tracks():
            raise openreview.OpenReviewException('The submission stage does not have tracks enabled. Please enable tracks in the submission stage.')

        sac_tracks = {}
        all_sacs = []
        with open(track_sac_file) as file_handle:
            for row in csv.reader(file_handle):
                track = row[0].strip()
                if track not in sac_tracks:
                    sac_tracks[track] = []
                sac_group_id = self.get_committee_id(row[1]).strip()
                sac_group = openreview.tools.get_group(self.client, sac_group_id)
                if sac_group:
                    sacs = openreview.tools.replace_members_with_ids(self.client, sac_group).members
                    sac_tracks[track] = sac_tracks[track] + sacs
                    all_sacs = all_sacs + sacs
                    self.client.post_group_edit(
                        invitation=self.get_meta_invitation_id(),
                        signatures=[self.venue_id],
                        group=openreview.api.Group(
                            id=sac_group_id,
                            content={
                                'track': { 'value': track }
                            }
                        )
                    )

        print(list(set(all_sacs)))

        submissions = self.get_submissions()

        all_authorids = []
        for submission in submissions:
            authorids = submission.content['authorids']['value']
            all_authorids = all_authorids + authorids

        author_profile_by_id = tools.get_profiles(self.client, list(set(all_authorids)), with_publications=True, with_relations=True, as_dict=True)
        sac_profile_by_id = tools.get_profiles(self.client, list(set(all_sacs)), with_publications=True, with_relations=True, as_dict=True)   

        info_function = tools.info_function_builder(openreview.tools.get_neurips_profile_info if conflict_policy == 'NeurIPS' else openreview.tools.get_profile_info)

        for submission in submissions:
            authorids = submission.content['authorids']['value']

            # Extract domains from each authorprofile
            author_ids = set()
            author_domains = set()
            author_emails = set()
            author_relations = set()
            author_publications = set()            
            for authorid in authorids:
                if author_profile_by_id.get(authorid):
                    author_info = info_function(author_profile_by_id[authorid], conflict_n_years)
                    author_ids.add(author_info['id'])
                    author_domains.update(author_info['domains'])
                    author_emails.update(author_info['emails'])
                    author_relations.update(author_info['relations'])
                    author_publications.update(author_info['publications'])
                else:
                    print(f'Profile not found: {authorid}')

            if submission.content['track']['value'] in sac_tracks:
                sacs = sac_tracks[submission.content['track']['value']]
                for sac in sacs:
                    sac_info = info_function(sac_profile_by_id.get(sac), conflict_n_years)
                    conflicts = set()
                    conflicts.update(author_ids.intersection(set([sac_info['id']])))
                    conflicts.update(author_domains.intersection(sac_info['domains']))
                    conflicts.update(author_relations.intersection([sac_info['id']]))
                    conflicts.update(author_ids.intersection(sac_info['relations']))
                    conflicts.update(author_publications.intersection(sac_info['publications']))

                    if not conflict_policy or not conflicts:                
                        sac_group_id = self.get_senior_area_chairs_id(submission.number)
                        print(f'adding {sac_tracks[submission.content["track"]["value"]]} to {sac_group_id}')
                        self.client.add_members_to_group(sac_group_id, sac_tracks[submission.content['track']['value']])
                    else:
                        print(f'conflict detected between {sac} and {submission.number}', conflicts, conflict_policy)

        if not track_ac_file:
            return
        
        ac_tracks = {}
        with open(track_ac_file) as file_handle:
            for row in csv.reader(file_handle):
                if row[0] not in ac_tracks:
                    ac_tracks[row[0]] = row[1]
    
        print(ac_tracks)

        assignment_edges = []
        all_acs = []
        assignment_invitation_id = self.get_assignment_id(self.get_senior_area_chairs_id(), deployed=True)
        for track, ac_role in ac_tracks.items():
            sacs = sac_tracks[track]
            ac_group = openreview.tools.get_group(self.client, self.get_committee_id(ac_role))
            if not ac_group:
                raise openreview.OpenReviewException(f'Group not found: {self.get_committee_id(ac_role)}')
            acs = openreview.tools.replace_members_with_ids(self.client, ac_group).members
            all_acs = all_acs + acs

            for sac in sacs:
                print('sac', sac)
                for ac in acs:
                    print('ac', ac)
                    assignment_edges.append(openreview.api.Edge(
                        invitation=assignment_invitation_id,
                        signatures=[self.venue_id],
                        readers=[self.venue_id, ac, sac],
                        writers=[self.venue_id],
                        head=ac,
                        tail=sac,
                        weight=1
                    ))

    
        print('assignment edges', assignment_edges)
        self.invitation_builder.set_assignment_invitation(self.get_senior_area_chairs_id())
        print('Posting bulk edges', len(assignment_edges))
        openreview.tools.post_bulk_edges(self.client, assignment_edges)
        print('Builiding ac group')
        self.client.add_members_to_group(self.get_area_chairs_id(), all_acs)

    def set_SAC_ethics_review_process(self, sac_ethics_flag_duedate=None):
        self.invitation_builder.set_SAC_ethics_flag_invitation(sac_ethics_flag_duedate)

    def open_reviewer_recommendation_stage(self, start_date=None, due_date=None, total_recommendations=7):
        self.invitation_builder.set_reviewer_recommendation_invitation(start_date, due_date, total_recommendations)

    def ithenticate_create_and_upload_submission(self):
        if not self.iThenticate_plagiarism_check:
            raise openreview.OpenReviewException(
                "iThenticatePlagiarismCheck is not enabled for this venue."
            )

        self.invitation_builder.set_iThenticate_plagiarism_check_invitation()

        iThenticate_client = openreview.api.iThenticateClient(
            self.iThenticate_plagiarism_check_api_key,
            self.iThenticate_plagiarism_check_api_base_url,
        )

        edges = self.client.get_grouped_edges(
            invitation=self.get_iThenticate_plagiarism_check_invitation_id(),
            groupby="head",
        )
        edges_dict = {edge["id"]["head"]: edge["values"] for edge in edges}

        submissions = self.get_submissions()
        for submission in tqdm(submissions):
            # TODO - Decide what should go in metadata.group_context.owners
            if submission.id not in edges_dict:

                owner = (
                    submission.signatures[0]
                    if submission.signatures[0].startswith("~")
                    else self.client.get_note_edits(note_id=submission.id, invitation=self.get_submission_id(), sort='tcdate:asc')[0].signatures[0]
                )
                print(f"Creating submission for {submission.id} with owner {owner}")
                owner_profile = self.client.get_profile(owner)

                eula_version = submission.content.get("iThenticate_agreement", {}).get("value", "v1beta").split(":")[-1].strip()

                timestamp = datetime.datetime.fromtimestamp(
                        submission.tcdate / 1000, tz=datetime.timezone.utc
                    ).strftime("%Y-%m-%dT%H:%M:%SZ")
                
                iThenticate_client.accept_EULA(
                    user_id=owner_profile.id,
                    eula_version=eula_version,
                    timestamp=timestamp,
                )

                name = owner_profile.get_preferred_name(pretty=True)

                res = iThenticate_client.create_submission(
                    owner=owner_profile.id,
                    title=submission.content["title"]["value"],
                    timestamp=timestamp,
                    owner_first_name=name.split(" ", 1)[0],
                    owner_last_name=name.split(" ", 1)[1],
                    owner_email=owner_profile.get_preferred_email(),
                    group_id=self.get_submission_id(),
                    group_context={
                        "id": self.id,
                        "name": self.name,
                        "owners": [
                            # {
                            #     "id": "d7cf2650-c1c7-11e8-b568-0800200c9a66",
                            #     "family_name": "test_instructor_first_name",
                            #     "given_name": "test_instructor_last_name",
                            #     "email": "instructor_email@test.com"
                            # },
                            # {
                            #     "id": "7a62f070-c265-11e8-b568-0800200c9a66",
                            #     "family_name": "test_instructor_2_first_name",
                            #     "given_name": "test_instrutor_2_last_name",
                            #     "email": "intructor_2_email@test.com"
                            # }
                        ],
                    },
                    group_type="ASSIGNMENT",
                    eula_version=eula_version,
                )
                iThenticate_submission_id = res["id"]

                iThenticate_edge = openreview.api.Edge(
                    invitation=self.get_iThenticate_plagiarism_check_invitation_id(),
                    head=submission.id,
                    tail=iThenticate_submission_id,
                    label="Created",
                    weight=-1,
                )

                iThenticate_edge = self.client.post_edge(iThenticate_edge)

                submission_file_binary_data = self.client.get_attachment(
                    id=submission.id, field_name="pdf"
                )

                submission_file_object = io.BytesIO(submission_file_binary_data)

                iThenticate_edge.label = "File Sent"
                iThenticate_edge = self.client.post_edge(iThenticate_edge)

                try:
                    res = iThenticate_client.upload_submission(
                        submission_id=iThenticate_submission_id,
                        file_data=submission_file_object,
                        file_name=submission.content["title"]["value"],
                    )
                except Exception as err:
                    iThenticate_edge.label = "Created"
                    iThenticate_edge = self.client.post_edge(iThenticate_edge)

            else:
                print(
                    f"Submission {submission.id} already has edge associated with it with label {edges_dict[submission.id][0]['label']}"
                )

    def handle_ithenticate_error(self):

        if not self.iThenticate_plagiarism_check:
            raise openreview.OpenReviewException(
                "iThenticatePlagiarismCheck is not enabled for this venue."
            )

        iThenticate_client = openreview.api.iThenticateClient(
            self.iThenticate_plagiarism_check_api_key,
            self.iThenticate_plagiarism_check_api_base_url,
        )

        edges = self.client.get_grouped_edges(
            invitation=self.get_iThenticate_plagiarism_check_invitation_id(),
            label="Error_Upload_PROCESSING_ERROR",
            groupby="tail",
        )

        similarity_error_edges = self.client.get_grouped_edges(
            invitation=self.get_iThenticate_plagiarism_check_invitation_id(),
            label="Error_Similarity_PROCESSING_ERROR",
            groupby="tail",
        )

        created_state_edges = self.client.get_grouped_edges(
            invitation=self.get_iThenticate_plagiarism_check_invitation_id(),
            label="Created",
            groupby="tail",
        )

        edges.extend(similarity_error_edges)
        edges.extend(created_state_edges)

        for e in tqdm(edges):
            edge = openreview.api.Edge.from_json(e["values"][0])
            original_label_value = edge.label
            if edge.label == "Created" or edge.label == "Error_Upload_PROCESSING_ERROR":
                # upload error
                print(f"Uploading submission associated with edge {edge.id} again")
                submission_file_binary_data = self.client.get_attachment(
                    id=edge.head, field_name="pdf"
                )

                submission_file_object = io.BytesIO(submission_file_binary_data)

                edge.label = "File Sent"
                edge = self.client.post_edge(edge)

                try:
                    res = iThenticate_client.upload_submission(
                        submission_id=edge.tail,
                        file_data=submission_file_object,
                        file_name=self.client.get_note(id=edge.head).content["title"][
                            "value"
                        ],
                    )
                except Exception as err:
                    edge.label = original_label_value
                    edge = self.client.post_edge(edge)
            elif edge.label == "Error_Similarity_PROCESSING_ERROR":
                # similarity report error
                print(
                    f"Requesting similarity report for submission associated with edge {edge.id} again"
                )
                edge.label = "Similarity Requested"
                updated_edge = self.client.post_edge(edge)

                try:
                    iThenticate_client.generate_similarity_report(
                        submission_id=updated_edge.tail,
                        search_repositories=[
                            "INTERNET",
                            "SUBMITTED_WORK",
                            "PUBLICATION",
                            "CROSSREF",
                            "CROSSREF_POSTED_CONTENT",
                        ],
                    )
                except Exception as err:
                    updated_edge.label = original_label_value
                    updated_edge = self.client.post_edge(updated_edge)

    def ithenticate_request_similarity_report(self):
        if not self.iThenticate_plagiarism_check:
            raise openreview.OpenReviewException(
                "iThenticatePlagiarismCheck is not enabled for this venue."
            )

        iThenticate_client = openreview.api.iThenticateClient(
            self.iThenticate_plagiarism_check_api_key,
            self.iThenticate_plagiarism_check_api_base_url,
        )

        edges = self.client.get_grouped_edges(
            invitation=self.get_iThenticate_plagiarism_check_invitation_id(),
            label="File Uploaded",
            groupby="tail",
        )

        for edge in tqdm(edges):
            e = openreview.api.Edge.from_json(edge["values"][0])
            e.label = "Similarity Requested"
            updated_edge = self.client.post_edge(e)

            try:
                iThenticate_client.generate_similarity_report(
                    submission_id=updated_edge.tail,
                    search_repositories=[
                        "INTERNET",
                        "SUBMITTED_WORK",
                        "PUBLICATION",
                        "CROSSREF",
                        "CROSSREF_POSTED_CONTENT",
                    ],
                )
            except Exception as err:
                updated_edge.label = "File Uploaded"
                updated_edge = self.client.post_edge(updated_edge)

    def check_ithenticate_status(self, label_value):
        if not self.iThenticate_plagiarism_check:
            raise openreview.OpenReviewException(
                "iThenticatePlagiarismCheck is not enabled for this venue."
            )

        edges = self.client.get_grouped_edges(
            invitation=self.get_iThenticate_plagiarism_check_invitation_id(),
            groupby="tail",
        )

        for edge in edges:
            e = openreview.api.Edge.from_json(edge["values"][0])
            if e.label != label_value:
                print(f"edge ID {e.id} has label {e.label}")

        return all([edge["values"][0]["label"] == label_value for edge in edges])

    def poll_ithenticate_for_status(self):
        iThenticate_client = openreview.api.iThenticateClient(
            self.iThenticate_plagiarism_check_api_key,
            self.iThenticate_plagiarism_check_api_base_url,
        )

        edges = self.client.get_grouped_edges(
            invitation=self.get_iThenticate_plagiarism_check_invitation_id(),
            groupby="tail",
        )

        for e in tqdm(edges):
            edge = openreview.api.Edge.from_json(e["values"][0])

            if edge.label == "File Sent":
                if iThenticate_client.get_submission_status(edge.tail) == "COMPLETE":
                    edge.label = "File Uploaded"
                    updated_edge = self.client.post_edge(edge)
                    print(
                        f"Updated label to {updated_edge.label} for edge {updated_edge.id}"
                    )

            elif edge.label == "Similarity Requested":
                status, similarity_score = (
                    iThenticate_client.get_similarity_report_status(edge.tail)
                )
                if status == "COMPLETE":
                    edge.label = "Similarity Complete"
                    edge.weight = similarity_score
                    updated_edge = self.client.post_edge(edge)
                    print(
                        f"Updated label to {updated_edge.label} for edge {updated_edge.id}"
                    )
            
    
    @classmethod
    def check_new_profiles(Venue, client):

        def mark_as_conflict(venue_group, edge, submission, user_profile):
            edge.label='Conflict Detected'
            edge.tail=user_profile.id
            edge.readers=None
            edge.writers=None
            edge.cdate = None            
            client.post_edge(edge)

            ## Send email to reviewer
            subject=f"[{venue_group.content['subtitle']['value']}] Conflict detected for paper {submission.number}"
            message =f'''Hi {{{{fullname}}}},
You have accepted the invitation to review the paper number: {submission.number}, title: {submission.content['title']['value']}.

A conflict was detected between you and the submission authors and the assignment can not be done.

If you have any questions, please contact us as info@openreview.net.

OpenReview Team'''
            response = client.post_message(subject, [edge.tail], message, invitation=venue_group.content['meta_invitation_id']['value'], signature=venue_group.id, replyTo=venue_group.content['contact']['value'], sender=venue_group.content['message_sender']['value'])

            ## Send email to inviter
            subject=f"[{venue_group.content['subtitle']['value']}] Conflict detected between reviewer {user_profile.get_preferred_name(pretty=True)} and paper {submission.number}"
            message =f'''Hi {{{{fullname}}}},
A conflict was detected between {user_profile.get_preferred_name(pretty=True)} and the paper {submission.number} and the assignment can not be done.

If you have any questions, please contact us as info@openreview.net.

OpenReview Team'''

            ## - Send email
            response = client.post_message(subject, edge.signatures, message, invitation=venue_group.content['meta_invitation_id']['value'], signature=venue_group.id, replyTo=venue_group.content['contact']['value'], sender=venue_group.content['message_sender']['value'])            
        
        def mark_as_accepted(venue_group, edge, submission, user_profile, invite_assignment_invitation):

            edge.label='Accepted'
            edge.tail=user_profile.id
            edge.readers=None
            edge.writers=None
            edge.cdate = None
            client.post_edge(edge)

            short_phrase = venue_group.content['subtitle']['value']
            assigment_label = invite_assignment_invitation.content.get('assignment_label', {}).get('value')
            assignment_invitation_id = invite_assignment_invitation.content.get('assignment_invitation_id', {}).get('value')
            committee_invited_id = invite_assignment_invitation.content.get('committee_invited_id', {}).get('value')
            paper_reviewer_invited_id = invite_assignment_invitation.content.get('paper_reviewer_invited_id', {}).get('value')
            reviewers_id = invite_assignment_invitation.content.get('match_group', {}).get('value')
            reviewer_name = 'Reviewer' ## add this to the invitation?

            assignment_edges = client.get_edges(invitation=assignment_invitation_id, head=submission.id, tail=edge.tail, label=assigment_label)

            if not assignment_edges:
                print('post assignment edge')
                client.post_edge(openreview.api.Edge(
                    invitation=assignment_invitation_id,
                    head=edge.head,
                    tail=edge.tail,
                    label=assigment_label,
                    signatures=[venue_group.id],
                    weight=1
                ))

                if committee_invited_id:
                    client.add_members_to_group(committee_invited_id.replace('/Invited', ''), edge.tail)
                if paper_reviewer_invited_id:
                    external_paper_committee_id=paper_reviewer_invited_id.replace('/Invited', '').replace('{number}', str(submission.number))
                    client.add_members_to_group(external_paper_committee_id, edge.tail)

                if assigment_label:
                    instructions=f'The {short_phrase} program chairs will be contacting you with more information regarding next steps soon. In the meantime, please add noreply@openreview.net to your email contacts to ensure that you receive all communications.'
                else:
                    instructions=f'Please go to the {short_phrase} Reviewers Console and check your pending tasks: https://openreview.net/group?id={reviewers_id}'

                print('send confirmation email')
                ## Send email to reviewer
                subject=f'[{short_phrase}] {reviewer_name} Assignment confirmed for paper {submission.number}'
                message =f'''Hi {{{{fullname}}}},
Thank you for accepting the invitation to review the paper number: {submission.number}, title: {submission.content['title']['value']}.

{instructions}

If you would like to change your decision, please click the Decline link in the previous invitation email.

OpenReview Team'''

                ## - Send email
                response = client.post_message(subject, [edge.tail], message, invitation=venue_group.content['meta_invitation_id']['value'], signature=venue_group.id, replyTo=venue_group.content['contact']['value'], sender=venue_group.content['message_sender']['value'])

                ## Send email to inviter
                subject=f'[{short_phrase}] {reviewer_name} {user_profile.get_preferred_name(pretty=True)} signed up and is assigned to paper {submission.number}'
                message =f'''Hi {{{{fullname}}}},
The {reviewer_name} {user_profile.get_preferred_name(pretty=True)} that you invited to review paper {submission.number} has accepted the invitation, signed up and is now assigned to the paper {submission.number}.

OpenReview Team'''

                ## - Send email
                response = client.post_message(subject, edge.signatures, message, invitation=venue_group.content['meta_invitation_id']['value'], signature=venue_group.id, replyTo=venue_group.content['contact']['value'], sender=venue_group.content['message_sender']['value'])            
        
        active_venues = client.get_group('active_venues').members

        for venue_id in active_venues:

            venue_group = client.get_group(venue_id)
            
            if hasattr(venue_group, 'domain') and venue_group.content:
                
                print(f'Check active venue {venue_group.id}')

                edge_invitations = client.get_all_invitations(prefix=venue_id, type='edge')
                invite_assignment_invitations = [inv.id for inv in edge_invitations if inv.id.endswith('Invite_Assignment')]

                for invite_assignment_invitation_id in invite_assignment_invitations:
                    
                    ## check if it is expired?
                    invite_assignment_invitation = openreview.tools.get_invitation(client, invite_assignment_invitation_id)

                    if invite_assignment_invitation:
                        grouped_edges = client.get_grouped_edges(invitation=invite_assignment_invitation.id, label='Pending Sign Up', groupby='tail')
                        print('Pending sign up edges found', len(grouped_edges))

                        for grouped_edge in grouped_edges:

                            tail = grouped_edge['id']['tail']
                            profiles=openreview.tools.get_profiles(client, [tail], with_publications=True, with_relations=True)

                            if profiles and profiles[0].active:

                                user_profile=profiles[0]
                                print('Profile found for', tail, user_profile.id)

                                edges = grouped_edge['values']

                                for edge in edges:

                                    edge = openreview.api.Edge.from_json(edge)
                                    submission=client.get_note(id=edge.head)

                                    if submission.content['venueid']['value'] == venue_group.content.get('submission_venue_id', {}).get('value'):

                                        ## Check if there is already an accepted edge for that profile id
                                        accepted_edges = client.get_edges(invitation=invite_assignment_invitation.id, label='Accepted', head=submission.id, tail=user_profile.id)

                                        if not accepted_edges:
                                            ## Check if the user was invited again with a profile id
                                            invitation_edges = client.get_edges(invitation=invite_assignment_invitation.id, label='Invitation Sent', head=submission.id, tail=user_profile.id)
                                            if invitation_edges:
                                                invitation_edge = invitation_edges[0]
                                                print(f'User invited twice, remove double invitation edge {invitation_edge.id}')
                                                invitation_edge.ddate = openreview.tools.datetime_millis(datetime.datetime.utcnow())
                                                client.post_edge(invitation_edge)

                                            ## Check conflicts
                                            author_profiles = openreview.tools.get_profiles(client, submission.content['authorids']['value'], with_publications=True, with_relations=True)
                                            conflicts=openreview.tools.get_conflicts(author_profiles, user_profile, policy=venue_group.content.get('reviewers_conflict_policy', {}).get('value'), n_years=venue_group.content.get('reviewers_conflict_n_years', {}).get('value'))

                                            if conflicts:
                                                print(f'Conflicts detected for {edge.head} and {user_profile.id}', conflicts)
                                                mark_as_conflict(venue_group, edge, submission, user_profile)
                                            else:
                                                print(f'Mark accepted for {edge.head} and {user_profile.id}')
                                                mark_as_accepted(venue_group, edge, submission, user_profile, invite_assignment_invitation)
                                                                                                                                                            
                                        else:
                                            print("user already accepted with another invitation edge", submission.id, user_profile.id)                                

                                    else:
                                        print(f'submission {submission.id} is not active: {submission.content["venueid"]["value"]}')

                            else:
                                print(f'no profile active for {tail}')                                             
        
        return True
