import csv
import json
import re
import io
import os
import datetime
import requests
import heapq
from io import StringIO
from multiprocessing import cpu_count
from concurrent.futures import ThreadPoolExecutor
from tqdm import tqdm
import editdistance
import openreview
from openreview import tools
from .invitation import InvitationBuilder
from .group import GroupBuilder
from openreview.api import Group
from openreview.api import Note
from .recruitment import Recruitment
from . import matching

class Venue(object):

    def __init__(self, client, venue_id, support_user):

        self.client = client
        self.request_form_id = None
        self.request_form_invitation = None
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
        self.publication_chairs_name = 'Publication_Chairs'
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
        self.submission_assignment_max_area_chairs = None
        self.preferred_emails_groups = []
        self.iThenticate_plagiarism_check = False
        self.iThenticate_plagiarism_check_api_key = ''
        self.iThenticate_plagiarism_check_api_base_url = ''
        self.iThenticate_plagiarism_check_committee_readers = []
        self.iThenticate_plagiarism_check_add_to_index = False
        self.iThenticate_plagiarism_check_exclude_quotes = False
        self.iThenticate_plagiarism_check_exclude_bibliography = False
        self.iThenticate_plagiarism_check_exclude_abstract = False
        self.iThenticate_plagiarism_check_exclude_methods = False
        self.iThenticate_plagiarism_check_exclude_internet = False
        self.iThenticate_plagiarism_check_exclude_publications = False
        self.iThenticate_plagiarism_check_exclude_submitted_works = False
        self.iThenticate_plagiarism_check_exclude_citations = False
        self.iThenticate_plagiarism_check_exclude_preprints = False
        self.iThenticate_plagiarism_check_exclude_custom_sections = False
        self.iThenticate_plagiarism_check_exclude_small_matches = 8
        self.comment_notification_threshold = None
        self.submission_human_verification = None
        venue_webfield_dir = os.path.join(os.path.dirname(__file__), 'webfield')
        self.homepage_webfield_path = os.path.join(venue_webfield_dir, 'homepageWebfield.js')
        self.program_chairs_webfield_path = os.path.join(venue_webfield_dir, 'programChairsWebfield.js')
        self.senior_area_chairs_webfield_path = os.path.join(venue_webfield_dir, 'seniorAreaChairsWebfield.js')
        self.area_chairs_webfield_path = os.path.join(venue_webfield_dir, 'areachairsWebfield.js')
        self.ethics_chairs_webfield_path = os.path.join(venue_webfield_dir, 'ethicsChairsWebfield.js')

    def set_main_settings(self, request_note):
        """Configure venue properties from a venue request form note.

        Populates name, short name, website, contact, location, start date,
        reviewer/AC/SAC role names, and preferred email groups from the request
        note content. Enables area chairs and senior area chairs if specified
        in the request.

        :param request_note: The venue request form note containing venue configuration.
        :type request_note: openreview.api.Note
        """
        self.name = request_note.content['official_venue_name']['value']
        self.short_name = request_note.content['abbreviated_venue_name']['value']
        self.website = request_note.content['venue_website_url']['value']
        self.contact = request_note.content['contact_email']['value']
        self.location = request_note.content['location']['value']
        self.start_date = request_note.content['venue_start_date']['value']
        self.date = ''
        self.request_form_id = request_note.id
        self.request_form_invitation = request_note.invitations[0]
        self.submission_license = {
            "value": "CC BY 4.0",
            "description": "CC BY 4.0"
        }
        self.reviewers_name = request_note.content['reviewers_name']['value']
        self.reviewer_roles = request_note.content.get('reviewer_roles', [self.reviewers_name])
        preferred_email_groups = [self.get_reviewers_id(), self.get_authors_id()]
    
        if request_note.content.get('area_chairs_support',{}).get('value'):
            self.area_chairs_name = request_note.content['area_chairs_name']['value']
            self.use_area_chairs = True
            self.area_chair_roles = request_note.content.get('area_chair_roles', [self.area_chairs_name])
            preferred_email_groups.append(self.get_area_chairs_id())

        if 'senior_area_chairs_name' in request_note.content:  ## change this once we add support for SACs
            self.senior_area_chairs_name = request_note.content['senior_area_chairs_name']['value']
            self.use_senior_area_chairs = True
            self.senior_area_chair_roles = request_note.content.get('senior_area_chair_roles', [self.senior_area_chairs_name])
            preferred_email_groups.append(self.get_senior_area_chairs_id())

        self.preferred_emails_groups = preferred_email_groups
        self.automatic_reviewer_assignment = True

    def get_id(self):
        return self.venue_id

    def get_short_name(self):
        return self.short_name
    
    def is_template_related_workflow(self):
        template_related_workflows = [
            f'{self.support_user}/Venue_Request/-/Conference_Review_Workflow',
            f'{self.support_user}/Venue_Request/-/ICML'
        ]
        return self.request_form_invitation and self.request_form_invitation in template_related_workflows
    
    def get_message_sender(self):

        fromEmail = self.short_name.replace(' ', '').replace(':', '-').replace('@', '').replace('(', '').replace(')', '').replace(',', '-').lower()
        fromEmail = f'{fromEmail}-notifications@openreview.net'
        
        email_regex = re.compile(r"^[a-z0-9!#$%&'*+/=?^_`{|}~-]+(?:\.[a-z0-9!#$%&'*+/=?^_`{|}~-]+)*@(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.)+[a-z0-9](?:[a-z0-9-]*[a-z0-9])?$")        

        if not email_regex.match(fromEmail):
            raise openreview.OpenReviewException(f'Invalid email address: {fromEmail}')
        
        return {
            'fromName': self.short_name,
            'fromEmail': fromEmail
        }
    
    def get_edges_archive_date(self):
        archive_date = datetime.datetime.now()
        if isinstance(self.start_date, int):
            return self.start_date + (60*60*1000*24*7*52) ## archive edges after 1 year

        if self.start_date:
            try:
                archive_date = datetime.datetime.strptime(self.start_date, '%b %d %Y')
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

    def get_standard_committee_role(self, committee_id):
        name = committee_id.split('/')[-1]

        standard_role_by_committee = {
            self.reviewers_name: 'reviewers',
            self.area_chairs_name: 'area_chairs',
            self.senior_area_chairs_name: 'senior_area_chairs',
        }

        return standard_role_by_committee.get(name, name)

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
    
    def get_article_endorsement_id(self):
        return self.get_invitation_id('Article_Endorsement')
    
    def get_post_submission_id(self):
        submission_name = self.submission_stage.name        
        return self.get_invitation_id(f'Post_{submission_name}')    

    def get_pc_submission_revision_id(self):
        return self.get_invitation_id('PC_Revision')

    def get_recruitment_id(self, committee_id):
        if self.is_template_related_workflow():
            return self.get_invitation_id('Recruitment_Response', prefix=committee_id)        
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
        return self.get_committee_id(self.publication_chairs_name)

    def get_withdrawal_id(self, number = None):
        return self.get_invitation_id(self.submission_stage.withdrawal_name, number)

    def get_withdrawn_id(self):
        return self.get_invitation_id(f'Withdrawn_{self.submission_stage.name}')

    def get_desk_rejection_id(self, number = None):
        return self.get_invitation_id(self.submission_stage.desk_rejection_name, number)

    def get_desk_rejected_id(self):
        return self.get_invitation_id(f'Desk_Rejected_{self.submission_stage.name}')
    
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
    
    def get_active_venue_ids(self, submission_invitation_name=None):
        return [self.venue_id, self.get_submission_venue_id(submission_invitation_name), self.get_rejected_submission_venue_id(submission_invitation_name)]
    
    def get_preferred_emails_invitation_id(self):
        return f'{self.venue_id}/-/Preferred_Emails' 

    def get_submissions(self, venueid=None, accepted=False, sort=None, details=None):
        """Retrieve venue submissions, optionally filtered by acceptance status or venue ID.

        When ``accepted=True``, returns only accepted submissions by checking
        the venue ID or falling back to parsing decision replies. When a
        ``venueid`` is provided, filters submissions to that specific venue ID.
        Otherwise returns all active, accepted, and rejected submissions.

        :param venueid: Filter submissions to this specific venue ID.
        :type venueid: str, optional
        :param accepted: If True, return only accepted submissions.
        :type accepted: bool, optional
        :param sort: Sort order string (e.g. ``'number:asc'``).
        :type sort: str, optional
        :param details: Comma-separated detail fields to include (e.g. ``'directReplies'``).
        :type details: str, optional
        :return: List of submission notes matching the query.
        :rtype: list[openreview.api.Note]
        """
        if accepted:
            accepted_notes = self.client.get_all_notes(content={ 'venueid': self.venue_id}, sort=sort, details=details, domain=self.venue_id)
            if len(accepted_notes) == 0:
                accepted_notes = []
                notes = self.client.get_all_notes(content={ 'venueid': f'{self.get_submission_venue_id()}'}, sort=sort, details='directReplies', domain=self.venue_id)
                for note in notes:
                    for reply in note.details['directReplies']:
                        if f'{self.venue_id}/{self.submission_stage.name}{note.number}/-/{self.decision_stage.name}' in reply['invitations']:
                            decision = reply['content']['decision']['value']
                            if openreview.tools.is_accept_decision(decision, self.decision_stage.accept_options):
                                accepted_notes.append(note)
            return accepted_notes

        if venueid:
            return self.client.get_all_notes(content={ 'venueid': venueid}, sort=sort, details=details, domain=self.venue_id)
        
        venueids = [
            self.get_submission_venue_id(),
            self.venue_id,
            self.get_rejected_submission_venue_id()
        ]

        return self.client.get_all_notes(content={ 'venueid': ','.join(venueids)}, sort=sort, details=details, domain=self.venue_id)

    #use to expire revision invitations from request form
    def expire_invitation(self, invitation_id):

        invitation_name = invitation_id.split('/-/')[-1]

        notes = self.get_submissions()
        for note in notes:
            invitation = f'{self.venue_id}/{self.submission_stage.name}{note.number}/-/{invitation_name}'
            self.invitation_builder.expire_invitation(invitation)

    def setup(self, program_chair_ids=[], publication_chairs_ids=[]):
        """Bootstrap the full venue infrastructure on OpenReview.

        Creates the meta invitation, venue group, program chairs group,
        authors group, and reviewer group. Conditionally creates area chair,
        senior area chair, ethics reviewer, ethics chair, and publication
        chair groups based on venue configuration. Also sets up edit
        invitations for the venue group and preferred-email invitations
        if applicable.

        Side effects: posts groups and invitations to the OpenReview API;
        adds the venue to the ``active_venues`` list.

        :param program_chair_ids: Profile IDs or emails to add as program chairs.
        :type program_chair_ids: list[str], optional
        :param publication_chairs_ids: Profile IDs or emails to add as publication chairs.
        :type publication_chairs_ids: list[str], optional
        """
        self.invitation_builder.set_meta_invitation()

        self.group_builder.create_venue_group()

        self.invitation_builder.set_edit_venue_group_invitations()

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

        if self.preferred_emails_groups:
            self.invitation_builder.set_preferred_emails_invitation()
            self.group_builder.create_preferred_emails_readers_group()        

    def set_impersonators(self, impersonators):
        """Set the list of users allowed to impersonate venue roles.

        :param impersonators: Profile IDs or group IDs that may impersonate venue members.
        :type impersonators: list[str]
        """
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
        """Send recruitment invitation emails to a committee (reviewers, area chairs, etc.).

        Delegates to :meth:`Recruitment.invite_committee` to email invitees
        with accept/decline links. Can also send reminders to pending invitees
        or retry previously declined candidates.

        Side effects: sends recruitment emails and creates/updates the
        recruitment invitation and response tracking groups (Invited, Declined).

        :param title: Email subject line for the recruitment message.
        :type title: str
        :param message: Email body template. May contain placeholders like ``{{accept_url}}``, ``{{decline_url}}``, ``{{invitation_url}}``, ``{{fullname}}``, and ``{{contact_info}}``.
        :type message: str
        :param invitees: Email addresses or profile IDs to recruit.
        :type invitees: list[str], optional
        :param reviewers_name: Committee role name (e.g. ``'Reviewers'``, ``'Area_Chairs'``).
        :type reviewers_name: str, optional
        :param remind: If True, send reminders to invitees who have not yet responded.
        :type remind: bool, optional
        :param invitee_names: Display names corresponding to each invitee.
        :type invitee_names: list[str], optional
        :param retry_declined: If True, re-invite previously declined candidates.
        :type retry_declined: bool, optional
        :param contact_info: Contact email shown in the recruitment message.
        :type contact_info: str, optional
        :param reduced_load_on_decline: List of reduced-load options offered when declining (e.g. ``['1', '2', '3']``).
        :type reduced_load_on_decline: list[str], optional
        :param allow_accept_with_reduced_load: If True, allow accepting with a reduced review load.
        :type allow_accept_with_reduced_load: bool, optional
        :param default_load: Default review load (currently unused).
        :type default_load: int, optional
        :param allow_overlap_official_committee: If True, allow recruiting members already on the official committee.
        :type allow_overlap_official_committee: bool, optional
        :param accept_recruitment_template: Custom template for the acceptance page.
        :type accept_recruitment_template: str, optional
        :return: Dictionary with keys ``invited``, ``reminded``, ``already_invited``, ``already_member``, ``errors``.
        :rtype: dict
        """
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
        """Set up the complete submission pipeline for the venue.

        Creates the submission invitation plus supporting invitations for
        withdrawal, desk rejection, post-submission processing, PC revision,
        per-submission reviewer/AC/SAC group management, and messaging. If
        iThenticate plagiarism checking is enabled, also creates the plagiarism
        check invitation. If a second deadline is configured, creates
        submission revision and deletion invitations for the second phase. If
        an expertise selection stage is set, creates those invitations too.

        Side effects: posts multiple invitations to the OpenReview API.
        """
        self.invitation_builder.set_submission_invitation()
        if self.iThenticate_plagiarism_check:
            self.invitation_builder.set_iThenticate_plagiarism_check_invitation()
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
            submission_revision_stage = openreview.stages.SubmissionRevisionStage(name=f'Full_{stage.name}',
                start_date=stage.exp_date,
                due_date=stage.second_due_date,
                additional_fields=stage.second_deadline_additional_fields if stage.second_deadline_additional_fields else stage.additional_fields,
                remove_fields=stage.second_deadline_remove_fields if stage.second_deadline_remove_fields else stage.remove_fields,
                only_accepted=False,
                multiReply=True,
                allow_author_reorder=stage.author_reorder_after_first_deadline,
                allow_license_edition=True,
                source = {'venueid': self.get_submission_venue_id()}
            )
            self.invitation_builder.set_submission_revision_invitation(submission_revision_stage)
            self.invitation_builder.set_submission_deletion_invitation(submission_revision_stage)

    def create_post_submission_stage(self):
        """Create or update the post-submission invitation that processes submissions after the deadline."""
        self.invitation_builder.set_post_submission_invitation()

    def create_submission_change_invitation(self, name, activation_date):
        """Create an invitation that triggers a process when submissions change.

        :param name: Name suffix for the invitation (e.g. a stage or field name).
        :type name: str
        :param activation_date: Timestamp (ms) when the invitation becomes active.
        :type activation_date: int
        :return: The created invitation.
        :rtype: openreview.api.Invitation
        """
        return self.invitation_builder.set_submission_change_invitation(name, activation_date)

    def create_submission_revision_stage(self):
        """Create the submission revision invitation allowing authors to revise their submissions."""
        return self.invitation_builder.set_submission_revision_invitation()

    def create_review_stage(self):
        """Create the review invitation enabling reviewers to submit reviews for assigned submissions."""
        return self.invitation_builder.set_review_invitation()
        
    def create_review_rebuttal_stage(self):
        """Create the rebuttal invitation allowing authors to respond to reviews."""
        return self.invitation_builder.set_review_rebuttal_invitation()

    def create_meta_review_stage(self):
        """Create the meta-review invitation enabling area chairs to submit meta-reviews."""
        return self.invitation_builder.set_meta_review_invitation()

    def create_registration_stages(self):
        """Create registration invitations for committee members to confirm participation."""
        return self.invitation_builder.set_registration_invitations()
    
    def setup_post_submission_stage(self, force=False, hide_fields=[]):
        ## do nothing
        return True
    
    def create_withdraw_invitations(self, reveal_authors=None, reveal_submission=None, email_pcs=None, hide_fields=[]):
        """Create withdrawal invitations allowing authors to withdraw submissions.

        .. deprecated::
            Use :meth:`create_submission_stage` instead, which sets up withdrawal invitations automatically.

        :param reveal_authors: Ignored (deprecated parameter).
        :param reveal_submission: Ignored (deprecated parameter).
        :param email_pcs: Ignored (deprecated parameter).
        :param hide_fields: Ignored (deprecated parameter).
        """
        return self.invitation_builder.set_withdrawal_invitation()

    def create_desk_reject_invitations(self, reveal_authors=None, reveal_submission=None, hide_fields=[]):
        """Create desk-rejection invitations allowing program chairs to desk-reject submissions.

        .. deprecated::
            Use :meth:`create_submission_stage` instead, which sets up desk-rejection invitations automatically.

        :param reveal_authors: Ignored (deprecated parameter).
        :param reveal_submission: Ignored (deprecated parameter).
        :param hide_fields: Ignored (deprecated parameter).
        """
        return self.invitation_builder.set_desk_rejection_invitation()

    def create_bid_stages(self):
        """Create bidding invitations for all configured bid stages, allowing committee members to bid on submissions."""
        self.invitation_builder.set_bid_invitations()

    def create_comment_stage(self):
        """Create comment invitations for official comments, optional public comments, and chat.

        Always creates the official comment invitation and the chat invitation.
        If the comment stage allows public comments, also creates a public
        comment invitation.

        Side effects: posts invitations to the OpenReview API.
        """
        self.invitation_builder.set_official_comment_invitation()
        if self.comment_stage.allow_public_comments:
            self.invitation_builder.set_public_comment_invitation()

        self.invitation_builder.set_chat_invitation()

    def create_decision_stage(self):
        """Create the decision invitation for program chairs to post accept/reject decisions.

        If a decisions CSV file is attached to the venue request form (or
        provided as a local path via ``decision_stage.decisions_file``), bulk-posts
        all decisions from that file by calling :meth:`post_decisions`.

        Side effects: posts the decision invitation; may post decision notes
        for all submissions and a status note to the request forum.
        """
        invitation = self.invitation_builder.set_decision_invitation()

        decision_file = self.decision_stage.decisions_file
        if decision_file:

            baseurl_v1 = openreview.tools.get_base_urls(self.client)[0]
            api1_client = openreview.Client(baseurl=baseurl_v1, token=self.client.token)

            if '/attachment' in decision_file:
                decisions = api1_client.get_attachment(id=self.request_form_id, field_name='decisions_file')

            else:
                with open(decision_file, 'rb') as file_handle:
                    decisions = file_handle.read()

            self.post_decisions(decisions, api1_client)

    def create_custom_stage(self):
        """Create invitations for a custom stage defined in ``self.custom_stage``."""
        return self.invitation_builder.set_custom_stage_invitation()
    
    def create_ethics_review_stage(self):
        """Create the ethics review pipeline including flagging, reviewer groups, and matching.

        Sets up the ethics flag invitation, per-paper ethics reviewer group
        invitations, updates existing review invitations, and creates the
        ethics review invitation. If ethics review comments are enabled, also
        creates comment invitations. Sets up paper matching for ethics
        reviewers (affinity scores, conflicts, assignment invitation) if
        ethics reviewers exist. Finally, flags submissions specified in
        ``ethics_review_stage.submission_numbers`` for ethics review.

        Side effects: posts multiple invitations and note edits; may compute
        affinity scores and conflicts for ethics reviewers.
        """
        print('Creating ethics review stage')
        flag_invitation = self.invitation_builder.set_ethics_stage_invitation()
        self.invitation_builder.set_ethics_paper_groups_invitation()
        self.invitation_builder.update_review_invitations()
        self.invitation_builder.update_meta_review_invitations()
        self.invitation_builder.set_ethics_review_invitation()
        if self.ethics_review_stage.enable_comments:
            print('Setting up ethics review comments invitation')
            self.invitation_builder.set_official_comment_invitation()

        # setup paper matching
        print('Setting up ethics review matching')
        ethics_chairs_group = tools.get_group(self.client, self.get_ethics_chairs_id())
        tools.replace_members_with_ids(self.client, ethics_chairs_group)
        group = tools.get_group(self.client, id=self.get_ethics_reviewers_id())
        if group and len(group.members) > 0:
            self.setup_committee_matching(
                group.id, 
                compute_affinity_scores=self.ethics_review_stage.compute_affinity_scores, 
                compute_conflicts=self.ethics_review_stage.compute_conflicts,
                compute_conflicts_n_years=self.ethics_review_stage.compute_conflicts_n_years)
            self.invitation_builder.set_assignment_invitation(group.id)

        flagged_submission_numbers = self.ethics_review_stage.submission_numbers
        print('flagged_submission_numbers', flagged_submission_numbers)
        if not flagged_submission_numbers:
            print('No flagged submissions found for ethics review stage')
            return
        print('Flagging submissions for ethics review stage')
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
        """Update the conflict detection policy for a reviewer or area chair committee.

        Stores the conflict policy name and N-year window in the venue group
        content. Only applies to the reviewers or area chairs committee; other
        committee IDs are silently ignored.

        :param committee_id: Full group ID of the committee (e.g. ``venue_id/Reviewers``).
        :type committee_id: str
        :param compute_conflicts: Conflict policy name (e.g. ``'NeurIPS'``, ``'Default'``), or None to delete.
        :type compute_conflicts: str or None
        :param compute_conflicts_n_years: Number of years to consider for conflict detection, or None to delete.
        :type compute_conflicts_n_years: int or None
        """
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

    def post_decisions(self, decisions_file, api1_client=None):
        """Bulk-post accept/reject decisions from a CSV file.

        Parses a CSV with rows of ``paper_number,decision[,comment]`` and posts
        a decision note for each submission. Existing decisions are updated
        in place. Runs concurrently with up to 6 worker threads.

        If a request form exists and an API v1 client is provided, posts a
        Decision_Upload_Status note to the request forum summarizing how many
        decisions were posted and any errors (up to 10 shown).

        :param decisions_file: Raw bytes of the CSV file content.
        :type decisions_file: bytes
        :param api1_client: API v1 client used to post the status note (optional).
        :type api1_client: openreview.Client, optional
        :return: Tuple of (list of successful results, dict of errors keyed by CSV row).
        :rtype: tuple[list, dict]
        """
        decisions_data = list(csv.reader(StringIO(decisions_file.decode()), delimiter=","))

        paper_notes = {n.number: n for n in self.get_submissions(details='directReplies')}

        domain_content = self.client.get_group(self.venue_id).content
        submission_name = self.submission_stage.name
        decision_name = domain_content.get('decision_name', {}).get('value', 'Decision')

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
                    if f'{self.venue_id}/{submission_name}{paper_note.number}/-/{decision_name}' in reply['invitations']:
                        paper_decision_note = reply
                        break

            content = {
                'title': {'value': 'Paper Decision'},
                'decision': {'value': decision.strip()},
                'comment': {'value': comment},
            }
            if paper_decision_note:
                self.client.post_note_edit(invitation = self.get_invitation_id(decision_name, paper_number),
                    signatures = [self.get_program_chairs_id()],
                    note = Note(
                        id = paper_decision_note['id'],
                        content = content
                    )
                )
            else:
                self.client.post_note_edit(invitation = self.get_invitation_id(decision_name, paper_number),
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
        if self.request_form_id and api1_client and not self.is_template_related_workflow():
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

        return results, errors

    def get_decision_note(self, submission):

        if submission.details:
            for reply in submission.details.get('directReplies', submission.details.get('replies', [])):
                if self.get_invitation_id(name = self.decision_stage.name, number = submission.number) in reply['invitations']:
                    return Note.from_json(reply)


    def post_decision_stage(self, reveal_all_authors=False, reveal_authors_accepted=False, decision_heading_map=None, submission_readers=None, hide_fields=[]):
        """Update all submissions with decision-derived metadata after decisions are finalized.

        For each submission that has a decision note, updates the ``venueid``,
        ``venue``, and ``_bibtex`` fields. Sets reader permissions according to
        the decision (accepted papers may become public). Optionally reveals
        author identities for all or only accepted papers. Hides specified
        fields from public view. For accepted papers, sets ``pdate`` and posts
        an article endorsement tag if applicable.

        Runs concurrently across all submissions.

        :param reveal_all_authors: If True, reveal authors on all submissions regardless of decision.
        :type reveal_all_authors: bool, optional
        :param reveal_authors_accepted: If True, reveal authors only on accepted submissions.
        :type reveal_authors_accepted: bool, optional
        :param decision_heading_map: Unused (reserved for heading customization).
        :type decision_heading_map: dict, optional
        :param submission_readers: Override submission readers list; if provided, replaces ``submission_stage.readers``.
        :type submission_readers: list[str], optional
        :param hide_fields: Field names to restrict to venue and authors only (e.g. ``['authors', 'authorids']``).
        :type hide_fields: list[str], optional
        """
        venue_id = self.venue_id
        submissions = self.get_submissions(sort='number:asc', details='directReplies')
        post_endorsment_tag = self.get_article_endorsement_id() and openreview.tools.get_invitation(self.client, self.get_article_endorsement_id())

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

            decision_note = self.get_decision_note(submission)
            if not decision_note:
                return

            submission_decision_value = decision_note.content.get('decision', {}).get('value')
            note_accepted = openreview.tools.is_accept_decision(submission_decision_value, self.decision_stage.accept_options)
            submission_readers = self.submission_stage.get_readers(self, submission.number, submission_decision_value, self.decision_stage.accept_options)

            venue = self.short_name
            venue = tools.decision_to_venue(venue, submission_decision_value, self.decision_stage.accept_options)
            venueid = decision_to_venueid(submission_decision_value)

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
                    year=str(datetime.datetime.now().year),
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
                        odate = openreview.tools.datetime_millis(datetime.datetime.now()) if (submission.odate is None and 'everyone' in submission_readers) else None,
                        pdate = openreview.tools.datetime_millis(datetime.datetime.now()) if (submission.pdate is None and note_accepted) else None
                    )
                )
            
            if note_accepted and post_endorsment_tag:
                self.client.post_tag(openreview.api.Tag(
                    invitation=self.get_article_endorsement_id(),
                    signature=venue_id,
                    forum=submission.id,
                    note=submission.id,
                    label=venue)
                )
        tools.concurrent_requests(update_note, submissions)

    def send_decision_notifications(self, decision_options, messages):
        """Send per-submission email notifications to authors with their paper's decision.

        For each submission with a decision, sends an email to the paper's
        author group. Skips submissions that have already been notified
        (checks for existing messages with the same subject). Template
        placeholders ``{{submission_title}}`` and ``{{forum_url}}`` in the
        message body are replaced with actual values.

        Runs concurrently across all submissions.

        :param decision_options: List of possible decision values (currently unused for filtering, all decisions are notified).
        :type decision_options: list[str]
        :param messages: Mapping from decision string to email body template (e.g. ``{'Accept': '...', 'Reject': '...'}``).
        :type messages: dict[str, str]
        """
        print('send_decision_notifications')
        paper_notes = self.get_submissions(details='directReplies')

        def send_notification(note):
            
            decision_note = self.get_decision_note(note)
            print(f'send_notification: {note.number} {note.content["title"]["value"]} {decision_note}')
            if not decision_note:
                return

            subject = "[{SHORT_NAME}] Decision notification for your submission {submission_number}: {submission_title}".format(
                SHORT_NAME=self.short_name,
                submission_number=note.number,
                submission_title=note.content['title']['value']
            )
            if not self.client.get_messages(subject=subject):
                message = messages[decision_note.content['decision']['value']]
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

    def set_assignment_invitations(self, submission_deadline):
        """Create assignment and deployment invitations for reviewers (and area chairs if enabled).

        Schedules assignment invitations to activate ~2 weeks after the submission
        deadline, and deployment invitations shortly after. If area chairs are
        enabled, their assignment and deployment invitations are created first,
        followed by reviewers.

        Side effects: posts assignment invitations and deployment invitation
        edits to the OpenReview API using the template invitation workflow.

        :param submission_deadline: Submission deadline as a Unix timestamp in milliseconds.
        :type submission_deadline: int
        """
        invitation_prefix = self.support_user.replace('Support', 'Template')

        if self.use_area_chairs:
            self.invitation_builder.set_assignment_invitation(committee_id=self.get_area_chairs_id(), cdate=submission_deadline + (60*60*1000*24*7*2))

            self.client.post_invitation_edit(
                invitations=f'{invitation_prefix}/-/Reviewer_Assignment_Deployment',
                signatures=[invitation_prefix],
                content={
                    'venue_id': { 'value': self.venue_id },
                    'name': { 'value': f'{self.area_chairs_name}_Assignment_Deployment' },
                    'activation_date': { 'value': submission_deadline + (60*60*1000*24*7*2.1) },
                    'committee_name': { 'value': self.area_chairs_name },
                    'committee_pretty_name': { 'value': self.get_area_chairs_name(pretty=True) }
                },
                await_process=True
            )

        self.invitation_builder.set_assignment_invitation(committee_id=self.get_reviewers_id(), cdate=submission_deadline + (60*60*1000*24*7*2.2))
        self.client.post_invitation_edit(
                invitations=f'{invitation_prefix}/-/Reviewer_Assignment_Deployment',
                signatures=[invitation_prefix],
                content={
                    'venue_id': { 'value': self.venue_id },
                    'name': { 'value': f'{self.reviewers_name}_Assignment_Deployment' },
                    'activation_date': { 'value': submission_deadline + (60*60*1000*24*7*2.3) },
                    'committee_name': { 'value': self.reviewers_name },
                    'committee_pretty_name': { 'value': self.get_reviewers_name(pretty=True) }
                },
                await_process=True
            )

    def setup_matching_invitations(self):
        """Create matching configuration invitations for reviewers and area chairs (if enabled).

        Sets up the matching invitations (affinity scores, conflicts, custom
        max papers, etc.) without computing scores. Use
        :meth:`setup_committee_matching` to also compute scores and conflicts.
        """
        if self.use_area_chairs:
            venue_matching = matching.Matching(self, self.client.get_group(self.get_area_chairs_id()))
            venue_matching.setup_matching_invitations()

        venue_matching = matching.Matching(self, self.client.get_group(self.get_reviewers_id()))
        venue_matching.setup_matching_invitations()

    def setup_all_committees_matching(self):
        """Run full matching setup (invitations, affinity scores, conflicts) for all committees.

        Sets up matching for area chairs (if enabled) and reviewers, including
        computing affinity scores and conflicts with default settings.
        """
        if self.use_area_chairs:
            venue_matching = matching.Matching(self, self.client.get_group(self.get_area_chairs_id()))
            venue_matching.setup()

        venue_matching = matching.Matching(self, self.client.get_group(self.get_reviewers_id()))
        venue_matching.setup()

    def setup_committee_matching(self, committee_id=None, compute_affinity_scores=False, compute_conflicts=False, compute_conflicts_n_years=None, alternate_matching_group=None, submission_track=None):
        """Set up paper matching for a specific committee, optionally computing affinity scores and conflicts.

        Creates matching invitations (proposed assignments, affinity scores,
        conflicts, custom max papers, etc.) for the specified committee. If
        the committee is senior area chairs and no alternate matching group is
        given, automatically uses area chairs as the alternate matching group
        (SAC-to-AC matching) unless ``sac_paper_assignments`` is enabled.

        :param committee_id: Group ID of the committee. Defaults to reviewers.
        :type committee_id: str, optional
        :param compute_affinity_scores: Model name or True to compute affinity scores.
        :type compute_affinity_scores: str or bool, optional
        :param compute_conflicts: Conflict policy name or True to compute conflicts.
        :type compute_conflicts: str or bool, optional
        :param compute_conflicts_n_years: Number of years for conflict detection window.
        :type compute_conflicts_n_years: int, optional
        :param alternate_matching_group: Group ID to match against instead of submissions (e.g. for SAC-to-AC matching).
        :type alternate_matching_group: str, optional
        :param submission_track: Filter submissions to a specific track for matching.
        :type submission_track: str, optional
        :return: The configured Matching object after setup.
        :rtype: openreview.venue.matching.Matching
        """
        if committee_id is None:
            committee_id=self.get_reviewers_id()
        if self.use_senior_area_chairs and committee_id == self.get_senior_area_chairs_id() and not alternate_matching_group and not self.sac_paper_assignments:
            alternate_matching_group = self.get_area_chairs_id()
        venue_matching = matching.Matching(self, self.client.get_group(committee_id), alternate_matching_group, { 'track': submission_track } if submission_track else None)

        return venue_matching.setup(compute_affinity_scores, compute_conflicts, compute_conflicts_n_years)

    def set_assignments(self, assignment_title, committee_id, enable_reviewer_reassignment=False, overwrite=False):
        """Deploy proposed assignments as official assignments for a committee.

        Copies edges from the proposed assignment configuration (identified by
        ``assignment_title``) to the deployed assignment invitation, creating
        per-paper committee member groups. Optionally enables reviewer
        reassignment for area chairs after deployment.

        :param assignment_title: Label of the proposed assignment configuration to deploy.
        :type assignment_title: str
        :param committee_id: Group ID of the committee being assigned (e.g. reviewers or area chairs).
        :type committee_id: str
        :param enable_reviewer_reassignment: If True, allow ACs to modify reviewer assignments after deployment.
        :type enable_reviewer_reassignment: bool, optional
        :param overwrite: If True, overwrite existing deployed assignments.
        :type overwrite: bool, optional
        :return: Result from the deployment operation.
        :rtype: varies
        """
        match_group = self.client.get_group(committee_id)
        assignment_invitation = self.client.get_invitation(self.get_assignment_id(match_group.id))
        conference_matching = matching.Matching(self, match_group, submission_content=assignment_invitation.edit.get('head', {}).get('param', {}).get('withContent'))
        return conference_matching.deploy(assignment_title, overwrite, enable_reviewer_reassignment)
    
    def unset_assignments(self, assignment_title, committee_id):
        """Revert deployed assignments back to proposed state for a committee.

        Removes the deployed assignment edges and per-paper committee member
        groups, restoring the assignment configuration to its pre-deployment
        state.

        :param assignment_title: Label of the assignment configuration to undeploy.
        :type assignment_title: str
        :param committee_id: Group ID of the committee whose assignments are being reverted.
        :type committee_id: str
        :return: Result from the undeployment operation.
        :rtype: varies
        """
        match_group = self.client.get_group(committee_id)
        conference_matching = matching.Matching(self, match_group)
        return conference_matching.undeploy(assignment_title)    

    def setup_assignment_recruitment(self, committee_id, hash_seed, due_date, assignment_title=None, invitation_labels={}, email_template=None):
        """Set up invite-based assignment recruitment for external or emergency reviewers.

        Creates an Invite_Assignment edge invitation that allows committee
        chairs to send assignment invitations with accept/decline links to
        prospective reviewers for specific papers.

        :param committee_id: Group ID of the committee to recruit for.
        :type committee_id: str
        :param hash_seed: Secret seed used to generate secure accept/decline tokens.
        :type hash_seed: str
        :param due_date: Deadline for responding to the assignment invitation (datetime or ms timestamp).
        :type due_date: datetime.datetime or int
        :param assignment_title: Label for the proposed assignment configuration.
        :type assignment_title: str, optional
        :param invitation_labels: Custom labels for invitation states.
        :type invitation_labels: dict, optional
        :param email_template: Custom email template for the recruitment message.
        :type email_template: str, optional
        :return: Result from the invite assignment setup.
        :rtype: varies
        """
        match_group = self.client.get_group(committee_id)
        conference_matching = matching.Matching(self, match_group)
        return conference_matching.setup_invite_assignment(hash_seed, assignment_title, due_date, invitation_labels=invitation_labels, email_template=email_template)
    
    def set_track_sac_assignments(self, track_sac_file, conflict_policy=None, conflict_n_years=None, track_ac_file=None):
        """Assign senior area chairs to submissions by track, with optional conflict detection.

        Reads a CSV mapping tracks to SAC groups, resolves SAC profiles, and
        assigns SACs to each submission's per-paper SAC group based on its
        track. Checks for conflicts between SACs and submission authors using
        the specified policy. If a ``track_ac_file`` is provided, also reads
        AC-to-track mappings and creates SAC-to-AC assignment edges, then adds
        all ACs to the area chairs group.

        Requires senior area chairs and submission tracks to be enabled.

        :param track_sac_file: Path to a CSV file with rows of ``track,SAC_group_name``.
        :type track_sac_file: str
        :param conflict_policy: Conflict detection policy (e.g. ``'NeurIPS'``, ``'Default'``), or None to skip conflict checks.
        :type conflict_policy: str, optional
        :param conflict_n_years: Number of years to consider for conflict detection.
        :type conflict_n_years: int, optional
        :param track_ac_file: Path to a CSV file with rows of ``track,AC_role_name`` for AC-to-SAC assignment.
        :type track_ac_file: str, optional
        """
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
        """Create the invitation for senior area chairs to flag submissions for ethics review.

        :param sac_ethics_flag_duedate: Deadline for SACs to flag papers (datetime or ms timestamp).
        :type sac_ethics_flag_duedate: datetime.datetime or int, optional
        """
        self.invitation_builder.set_SAC_ethics_flag_invitation(sac_ethics_flag_duedate)

    def open_reviewer_recommendation_stage(self, start_date=None, due_date=None, total_recommendations=7):
        """Open the reviewer recommendation stage for area chairs to recommend reviewers.

        Creates the reviewer recommendation invitation and stores its ID in
        the venue group content as ``reviewers_recommendation_id``.

        :param start_date: When the recommendation period opens (datetime or ms timestamp).
        :type start_date: datetime.datetime or int, optional
        :param due_date: Deadline for submitting recommendations (datetime or ms timestamp).
        :type due_date: datetime.datetime or int, optional
        :param total_recommendations: Maximum number of reviewers each AC can recommend per paper.
        :type total_recommendations: int, optional
        """
        recommendation_invitation = self.invitation_builder.set_reviewer_recommendation_invitation(start_date, due_date, total_recommendations)
        self.client.post_group_edit(invitation=self.get_meta_invitation_id(),
            signatures = [self.venue_id],
            group = openreview.api.Group(
                id = self.venue_id,
                content = {
                    'reviewers_recommendation_id': { 'value': recommendation_invitation.id },
                }
            )
        )        

    def ithenticate_create_and_upload_submission(self):
        """Upload all venue submissions to iThenticate for plagiarism checking.

        For each submission that does not already have an iThenticate tracking
        edge, creates an iThenticate submission record (accepting the EULA on
        behalf of the submitting author), then uploads the PDF. Tracks
        progress via edges with labels: ``'Created'`` -> ``'File Sent'``.

        Requires ``iThenticate_plagiarism_check`` to be enabled on the venue.

        Side effects: creates iThenticate submissions via the iThenticate API;
        posts tracking edges to OpenReview; downloads submission PDFs.

        :raises openreview.OpenReviewException: If plagiarism checking is not enabled.
        """
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
            domain=self.id
        )
        edges_dict = {edge["id"]["head"]: edge["values"] for edge in edges}

        submissions = self.get_submissions()
        for submission in tqdm(submissions):
            # TODO - Decide what should go in metadata.group_context.owners
            if submission.id not in edges_dict:
                if submission.signatures[0].startswith("~"):
                    owner = submission.signatures[0]
                else:
                    true_author_found = False
                    for note_edit in self.client.get_note_edits(
                        note_id=submission.id,
                        invitation=self.get_submission_id(),
                        sort="tcdate:asc",
                    ):
                        if note_edit.signatures[0].startswith("~"):
                            owner = note_edit.signatures[0]
                            true_author_found = True
                            break
                    if not true_author_found:
                        owner = submission.content["authorids"]["value"][0]
                print(f"Creating submission for {submission.id} with owner {owner}")
                try:
                    owner_profile = self.client.get_profile(owner)
                except:
                    owner = self.client.get_note_edits(
                        note_id=submission.id,
                        invitation=self.get_submission_id(),
                        sort="tcdate:asc",
                    )[0].tauthor
                    owner_profile = self.client.get_profile(owner)
                    

                eula_version = submission.content.get("iThenticate_agreement", {}).get("value").split(":")[-1].strip()

                timestamp = datetime.datetime.fromtimestamp(
                        submission.tcdate / 1000, tz=datetime.timezone.utc
                    ).strftime("%Y-%m-%dT%H:%M:%SZ")
                
                iThenticate_client.accept_EULA(
                    user_id=owner_profile.id,
                    eula_version=eula_version,
                    timestamp=timestamp,
                )

                name = owner_profile.get_preferred_name(pretty=True)
                name_list = name.split(" ", 1)
                first_name = name_list[0]
                last_name = name_list[1] if len(name_list) > 1 else ""

                res = iThenticate_client.create_submission(
                    owner=owner_profile.id,
                    title=submission.content["title"]["value"],
                    timestamp=datetime.datetime.fromtimestamp(
                        submission.tcdate / 1000, tz=datetime.timezone.utc
                    ).strftime("%Y-%m-%dT%H:%M:%SZ"),
                    owner_first_name=first_name,
                    owner_last_name=last_name,
                    owner_email=owner_profile.get_preferred_email(),
                    group_id=self.venue_id,
                    group_context={
                        "id": self.id,
                        "name": self.name,
                        "owners": [],
                    },
                    group_type="FOLDER",
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
        """Retry failed iThenticate uploads and similarity report requests.

        Finds edges in error states (``'Error_Upload_PROCESSING_ERROR'``,
        ``'Error_Similarity_PROCESSING_ERROR'``, ``'Created'``) and retries
        the failed operation: re-uploads the PDF for upload errors, or
        re-requests the similarity report for similarity errors. Reverts the
        edge label on retry failure.

        :raises openreview.OpenReviewException: If plagiarism checking is not enabled.
        """
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
            domain=self.id
        )

        similarity_error_edges = self.client.get_grouped_edges(
            invitation=self.get_iThenticate_plagiarism_check_invitation_id(),
            label="Error_Similarity_PROCESSING_ERROR",
            groupby="tail",
            domain=self.id
        )

        created_state_edges = self.client.get_grouped_edges(
            invitation=self.get_iThenticate_plagiarism_check_invitation_id(),
            label="Created",
            groupby="tail",
            domain=self.id
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
                        indexing_settings={
                            "add_to_index": self.iThenticate_plagiarism_check_add_to_index

                        },
                        view_settings={
                            "exclude_quotes": self.iThenticate_plagiarism_check_exclude_quotes,
                            "exclude_bibliography": self.iThenticate_plagiarism_check_exclude_bibliography,
                            "exclude_abstract": self.iThenticate_plagiarism_check_exclude_abstract,
                            "exclude_methods": self.iThenticate_plagiarism_check_exclude_methods,
                            "exclude_internet": self.iThenticate_plagiarism_check_exclude_internet,
                            "exclude_publications": self.iThenticate_plagiarism_check_exclude_publications,
                            "exclude_submitted_works": self.iThenticate_plagiarism_check_exclude_submitted_works,
                            "exclude_citations": self.iThenticate_plagiarism_check_exclude_citations,
                            "exclude_preprints": self.iThenticate_plagiarism_check_exclude_preprints,
                            "exclude_custom_sections": self.iThenticate_plagiarism_check_exclude_custom_sections,
                            "exclude_small_matches": self.iThenticate_plagiarism_check_exclude_small_matches
                        },
                        auto_exclude_self_matching_scope="ALL",
                    )
                except Exception as err:
                    updated_edge.label = original_label_value
                    updated_edge = self.client.post_edge(updated_edge)

    def ithenticate_request_similarity_report(self):
        """Request iThenticate similarity reports for all uploaded submissions.

        Finds all tracking edges with label ``'File Uploaded'`` and requests
        a similarity report from iThenticate for each. Updates edge labels to
        ``'Similarity Requested'`` on success, or reverts to ``'File Uploaded'``
        on failure. Uses venue-configured exclusion settings (quotes,
        bibliography, abstracts, etc.).

        :raises openreview.OpenReviewException: If plagiarism checking is not enabled.
        """
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
            domain=self.id
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
                    indexing_settings={
                        "add_to_index": self.iThenticate_plagiarism_check_add_to_index
                    },
                    view_settings={
                            "exclude_quotes": self.iThenticate_plagiarism_check_exclude_quotes,
                            "exclude_bibliography": self.iThenticate_plagiarism_check_exclude_bibliography,
                            "exclude_abstract": self.iThenticate_plagiarism_check_exclude_abstract,
                            "exclude_methods": self.iThenticate_plagiarism_check_exclude_methods,
                            "exclude_internet": self.iThenticate_plagiarism_check_exclude_internet,
                            "exclude_publications": self.iThenticate_plagiarism_check_exclude_publications,
                            "exclude_submitted_works": self.iThenticate_plagiarism_check_exclude_submitted_works,
                            "exclude_citations": self.iThenticate_plagiarism_check_exclude_citations,
                            "exclude_preprints": self.iThenticate_plagiarism_check_exclude_preprints,
                            "exclude_custom_sections": self.iThenticate_plagiarism_check_exclude_custom_sections,
                            "exclude_small_matches": self.iThenticate_plagiarism_check_exclude_small_matches
                        }
                )
            except Exception as err:
                updated_edge.label = "File Uploaded"
                updated_edge = self.client.post_edge(updated_edge)

    def check_ithenticate_status(self, label_value):
        """Check whether all iThenticate tracking edges have reached a given status.

        Prints each edge that does not match the expected label and reports
        the total count of non-matching edges.

        :param label_value: Expected edge label to check against (e.g. ``'Similarity Complete'``).
        :type label_value: str
        :return: True if all edges have the expected label, False otherwise.
        :rtype: bool
        :raises openreview.OpenReviewException: If plagiarism checking is not enabled.
        """
        if not self.iThenticate_plagiarism_check:
            raise openreview.OpenReviewException(
                "iThenticatePlagiarismCheck is not enabled for this venue."
            )

        edges = self.client.get_grouped_edges(
            invitation=self.get_iThenticate_plagiarism_check_invitation_id(),
            groupby="tail",
            domain=self.id
        )

        label_value_not_equal_counter = 0
        for edge in edges:
            e = openreview.api.Edge.from_json(edge["values"][0])
            if e.label != label_value:
                label_value_not_equal_counter += 1
                print(f"edge ID {e.id} has label {e.label}")

        print(f"{label_value_not_equal_counter} edges not in {label_value} state")
        return all([edge["values"][0]["label"] == label_value for edge in edges])

    def poll_ithenticate_for_status(self):
        """Poll iThenticate for upload completion and similarity report results.

        Iterates over all tracking edges and checks their current status with
        iThenticate. Updates edge labels as processing completes:
        ``'File Sent'`` -> ``'File Uploaded'`` when the upload finishes, and
        ``'Similarity Requested'`` -> ``'Similarity Complete'`` (with the
        similarity score stored in ``edge.weight``) when the report finishes.
        """
        iThenticate_client = openreview.api.iThenticateClient(
            self.iThenticate_plagiarism_check_api_key,
            self.iThenticate_plagiarism_check_api_base_url,
        )

        edges = self.client.get_grouped_edges(
            invitation=self.get_iThenticate_plagiarism_check_invitation_id(),
            groupby="tail",
            domain=self.id
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

    def compute_reviewers_stats(self):
        """Compute and post reviewer performance statistics as tags.

        Calculates four metrics for each reviewer based on their deployed
        assignments: assignment count, completed review count, days late
        (relative to the review due date), and discussion reply count
        (official comments and rebuttals). Excludes withdrawn and desk-rejected
        submissions. Deletes any existing metric tags before posting new ones.

        Side effects: creates metric invitations and posts bulk tags for
        ``Review_Assignment_Count``, ``Review_Count``,
        ``Review_Days_Late_Count``, and ``Discussion_Reply_Count`` under the
        reviewers group.
        """
        review_assignment_count_name = 'Review_Assignment_Count'
        review_count_name = 'Review_Count'
        review_days_late_count_name = 'Review_Days_Late_Count'
        discussion_reply_count_name = 'Discussion_Reply_Count'
        
        self.invitation_builder.create_metric_invitation(review_assignment_count_name)
        self.invitation_builder.create_metric_invitation(review_count_name, readers=['everyone'])
        self.invitation_builder.create_metric_invitation(review_days_late_count_name)
        self.invitation_builder.create_metric_invitation(discussion_reply_count_name)

        venue_id = self.venue_id
        reviewers_id = self.get_reviewers_id()
        review_stage = self.review_stage
        review_name = review_stage.name
        review_invitation_id = self.get_invitation_id(review_stage.name)
        review_invitation = self.client.get_invitation(review_invitation_id)
        review_duedate = datetime.datetime.fromtimestamp(review_invitation.edit['invitation']['duedate']/1000)
        comment_names = ['Official_Comment', 'Rebuttal']

        ignore_venue_ids = [self.get_withdrawn_submission_venue_id(), self.get_desk_rejected_submission_venue_id()]

        review_assignment_count_tags = []
        review_count_tags = []
        comment_count_tags = []
        review_days_late_tags = []

        submission_id = self.get_submission_id()
        submission_name = self.submission_stage.name
        submission_by_id = { n.id: n for n in self.client.get_all_notes(invitation=submission_id, details='replies', domain=venue_id)}
        
        reviewer_assignment_id = self.get_assignment_id(reviewers_id, deployed=True)
        assignments_by_reviewers = { e['id']['tail']: e['values'] for e in self.client.get_grouped_edges(invitation=reviewer_assignment_id, groupby='tail', domain=venue_id) }
        all_submission_groups = self.client.get_all_groups(prefix=self.get_submission_venue_id(), domain=venue_id)

        all_anon_reviewer_groups = [g for g in all_submission_groups if f'/{self.get_anon_committee_name(self.reviewers_name)}' in g.id ]
        all_anon_reviewer_group_members = []
        for g in all_anon_reviewer_groups:
            all_anon_reviewer_group_members += g.members
        all_profile_ids = set(all_anon_reviewer_group_members + list(assignments_by_reviewers.keys()))
        profile_by_id = openreview.tools.get_profiles(self.client, list(all_profile_ids), as_dict=True)

        reviewer_anon_groups = {}
        for g in all_anon_reviewer_groups:
            profile = profile_by_id.get(g.members[0]) if g.members else None
            if profile:
                reviewer_anon_groups['/'.join(g.id.split('/')[:-1]) + '/' + profile.id] = g.id                

        for reviewer, assignments in assignments_by_reviewers.items():

            profile = profile_by_id[reviewer]
            if not profile:
                print('Reviewer with no profile', reviewer)
                continue
            
            reviewer_id = profile.id

            num_assigned = 0
            num_reviews = 0
            num_comments = 0
            review_days_late = []

            for assignment in assignments:

                submission = submission_by_id[assignment['head']]

                if submission.content['venueid']['value'] in ignore_venue_ids:
                    continue

                anon_group_id = reviewer_anon_groups[f'{venue_id}/{submission_name}{submission.number}/{reviewer_id}']
                reviews = [r for r in submission.details['replies'] if f'/-/{review_name}' in r['invitations'][0] and anon_group_id in r['signatures']]
                comments = [r for r in submission.details['replies'] if r['invitations'][0].split('/-/')[-1] in comment_names and anon_group_id in r['signatures']]

                num_assigned += 1
                num_reviews += len(reviews)
                num_comments += len(comments)

                assignment_cdate = datetime.datetime.fromtimestamp(assignment['cdate']/1000)
                if reviews:

                    review = reviews[0]
                    review_tcdate = datetime.datetime.fromtimestamp(review['tcdate']/1000)

                    review_period_days = (review_duedate - assignment_cdate).days
                    if review_period_days > 0:
                        review_days_late.append(max((review_tcdate - review_duedate).days, 0))

            review_assignment_count_tags.append(openreview.api.Tag(
                invitation = f'{reviewers_id}/-/{review_assignment_count_name}',
                profile = reviewer_id,
                weight = num_assigned,
                readers = [venue_id, f'{reviewers_id}/{review_assignment_count_name}/Readers', reviewer_id],
                writers = [venue_id],
                nonreaders = [f'{reviewers_id}/{review_assignment_count_name}/NonReaders'],
            ))
            review_count_tags.append(openreview.api.Tag(
                invitation = f'{reviewers_id}/-/{review_count_name}',
                profile = reviewer_id,
                weight = num_reviews,
                readers = ['everyone'],
                writers = [venue_id],
                nonreaders = [f'{reviewers_id}/{review_count_name}/NonReaders'],
            ))
            comment_count_tags.append(openreview.api.Tag(
                invitation = f'{reviewers_id}/-/{discussion_reply_count_name}',
                profile = reviewer_id,
                weight = num_comments,
                readers = [venue_id, f'{reviewers_id}/{discussion_reply_count_name}/Readers', reviewer_id],
                writers = [venue_id],
                nonreaders = [f'{reviewers_id}/{discussion_reply_count_name}/NonReaders'],
            ))
            review_days_late_tags.append(openreview.api.Tag(
                invitation = f'{reviewers_id}/-/{review_days_late_count_name}',
                profile = reviewer_id,
                weight = int(sum(review_days_late)),
                readers = [venue_id, f'{reviewers_id}/{review_days_late_count_name}/Readers', reviewer_id],
                writers = [venue_id],
                nonreaders = [f'{reviewers_id}/{review_days_late_count_name}/NonReaders'],
            ))
            print(reviewer_id,
            num_assigned,
            num_reviews,
            num_comments,
            sum(review_days_late))

        self.client.delete_tags(invitation=f'{reviewers_id}/-/{review_assignment_count_name}', wait_to_finish=True, soft_delete=True)
        openreview.tools.post_bulk_tags(self.client, review_assignment_count_tags)       

        self.client.delete_tags(invitation=f'{reviewers_id}/-/{review_count_name}', wait_to_finish=True, soft_delete=True)
        openreview.tools.post_bulk_tags(self.client, review_count_tags)       

        self.client.delete_tags(invitation=f'{reviewers_id}/-/{discussion_reply_count_name}', wait_to_finish=True, soft_delete=True)
        openreview.tools.post_bulk_tags(self.client, comment_count_tags)       

        self.client.delete_tags(invitation=f'{reviewers_id}/-/{review_days_late_count_name}', wait_to_finish=True, soft_delete=True)
        openreview.tools.post_bulk_tags(self.client, review_days_late_tags)

    def compute_acs_stats(self):
        """Compute and post area chair performance statistics as tags.

        Calculates four metrics for each area chair based on their deployed
        assignments: meta-review assignment count, completed meta-review count,
        days late (relative to the meta-review due date), and discussion reply
        count (official comments and rebuttals). Excludes withdrawn and
        desk-rejected submissions. Deletes any existing metric tags before
        posting new ones.

        Side effects: creates metric invitations and posts bulk tags for
        ``Meta_Review_Assignment_Count``, ``Meta_Review_Count``,
        ``Meta_Review_Days_Late_Count``, and ``Discussion_Reply_Count`` under
        the area chairs group.
        """
        review_assignment_count_name = 'Meta_Review_Assignment_Count'
        review_count_name = 'Meta_Review_Count'
        review_days_late_count_name = 'Meta_Review_Days_Late_Count'
        discussion_reply_count_name = 'Discussion_Reply_Count'
        committee_id = self.get_area_chairs_id()
        
        self.invitation_builder.create_metric_invitation(review_assignment_count_name, committee_id=committee_id)
        self.invitation_builder.create_metric_invitation(review_count_name, committee_id=committee_id, readers=['everyone'])
        self.invitation_builder.create_metric_invitation(review_days_late_count_name, committee_id=committee_id)
        self.invitation_builder.create_metric_invitation(discussion_reply_count_name, committee_id=committee_id)

        venue_id = self.venue_id
        review_stage = self.meta_review_stage
        review_name = review_stage.name
        review_invitation_id = self.get_invitation_id(review_stage.name)
        review_invitation = self.client.get_invitation(review_invitation_id)
        review_duedate = datetime.datetime.fromtimestamp(review_invitation.edit['invitation']['duedate']/1000)
        comment_names = ['Official_Comment', 'Rebuttal']

        ignore_venue_ids = [self.get_withdrawn_submission_venue_id(), self.get_desk_rejected_submission_venue_id()]

        review_assignment_count_tags = []
        review_count_tags = []
        comment_count_tags = []
        review_days_late_tags = []

        submission_id = self.get_submission_id()
        submission_name = self.submission_stage.name
        submission_by_id = { n.id: n for n in self.client.get_all_notes(invitation=submission_id, details='replies', domain=venue_id)}
        
        reviewer_assignment_id = self.get_assignment_id(committee_id, deployed=True)
        assignments_by_reviewers = { e['id']['tail']: e['values'] for e in self.client.get_grouped_edges(invitation=reviewer_assignment_id, groupby='tail', domain=venue_id) }
        all_submission_groups = self.client.get_all_groups(prefix=self.get_submission_venue_id(), domain=venue_id)

        all_anon_reviewer_groups = [g for g in all_submission_groups if f'/{self.get_anon_committee_name(self.area_chairs_name)}' in g.id ]
        all_anon_reviewer_group_members = []
        for g in all_anon_reviewer_groups:
            all_anon_reviewer_group_members += g.members
        all_profile_ids = set(all_anon_reviewer_group_members + list(assignments_by_reviewers.keys()))
        profile_by_id = openreview.tools.get_profiles(self.client, list(all_profile_ids), as_dict=True)

        reviewer_anon_groups = {}
        for g in all_anon_reviewer_groups:
            profile = profile_by_id.get(g.members[0]) if g.members else None
            if profile:
                reviewer_anon_groups['/'.join(g.id.split('/')[:-1]) + '/' + profile.id] = g.id                

        for reviewer, assignments in assignments_by_reviewers.items():

            profile = profile_by_id[reviewer]
            if not profile:
                print('AC with no profile', reviewer)
                continue
            
            reviewer_id = profile.id

            num_assigned = 0
            num_reviews = 0
            num_comments = 0
            review_days_late = []

            for assignment in assignments:

                submission = submission_by_id[assignment['head']]

                if submission.content['venueid']['value'] in ignore_venue_ids:
                    continue

                if 'cdate' not in assignment:
                    print('No cdate for assignment', assignment)
                    continue

                anon_group_id = reviewer_anon_groups[f'{venue_id}/{submission_name}{submission.number}/{reviewer_id}']
                reviews = [r for r in submission.details['replies'] if f'/-/{review_name}' in r['invitations'][0] and anon_group_id in r['signatures']]
                comments = [r for r in submission.details['replies'] if r['invitations'][0].split('/-/')[-1] in comment_names and anon_group_id in r['signatures']]

                num_assigned += 1
                num_reviews += len(reviews)
                num_comments += len(comments)

                assignment_cdate = datetime.datetime.fromtimestamp(assignment['cdate']/1000)
                if reviews:

                    review = reviews[0]
                    review_tcdate = datetime.datetime.fromtimestamp(review['tcdate']/1000)

                    review_period_days = (review_duedate - assignment_cdate).days
                    if review_period_days > 0:
                        review_days_late.append(max((review_tcdate - review_duedate).days, 0))

            review_assignment_count_tags.append(openreview.api.Tag(
                invitation = f'{committee_id}/-/{review_assignment_count_name}',
                profile = reviewer_id,
                weight = num_assigned,
                readers = [venue_id, f'{committee_id}/{review_assignment_count_name}/Readers', reviewer_id],
                writers = [venue_id],
                nonreaders = [f'{committee_id}/{review_assignment_count_name}/NonReaders'],
            ))
            review_count_tags.append(openreview.api.Tag(
                invitation = f'{committee_id}/-/{review_count_name}',
                profile = reviewer_id,
                weight = num_reviews,
                readers = ['everyone'],
                writers = [venue_id],
                nonreaders = [f'{committee_id}/{review_count_name}/NonReaders'],
            ))
            comment_count_tags.append(openreview.api.Tag(
                invitation = f'{committee_id}/-/{discussion_reply_count_name}',
                profile = reviewer_id,
                weight = num_comments,
                readers = [venue_id, f'{committee_id}/{discussion_reply_count_name}/Readers', reviewer_id],
                writers = [venue_id],
                nonreaders = [f'{committee_id}/{discussion_reply_count_name}/NonReaders'],
            ))
            review_days_late_tags.append(openreview.api.Tag(
                invitation = f'{committee_id}/-/{review_days_late_count_name}',
                profile = reviewer_id,
                weight = int(sum(review_days_late)),
                readers = [venue_id, f'{committee_id}/{review_days_late_count_name}/Readers', reviewer_id],
                writers = [venue_id],
                nonreaders = [f'{committee_id}/{review_days_late_count_name}/NonReaders'],
            ))
            print(reviewer_id,
            num_assigned,
            num_reviews,
            num_comments,
            sum(review_days_late))

        self.client.delete_tags(invitation=f'{committee_id}/-/{review_assignment_count_name}', wait_to_finish=True, soft_delete=True)
        openreview.tools.post_bulk_tags(self.client, review_assignment_count_tags)       

        self.client.delete_tags(invitation=f'{committee_id}/-/{review_count_name}', wait_to_finish=True, soft_delete=True)
        openreview.tools.post_bulk_tags(self.client, review_count_tags)       

        self.client.delete_tags(invitation=f'{committee_id}/-/{discussion_reply_count_name}', wait_to_finish=True, soft_delete=True)
        openreview.tools.post_bulk_tags(self.client, comment_count_tags)       

        self.client.delete_tags(invitation=f'{committee_id}/-/{review_days_late_count_name}', wait_to_finish=True, soft_delete=True)
        openreview.tools.post_bulk_tags(self.client, review_days_late_tags)               
    
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

                edge_invitations = client.get_all_invitations(prefix=venue_id, type='edge', domain=venue_id)
                invite_assignment_invitations = [inv.id for inv in edge_invitations if inv.id.endswith('Invite_Assignment')]

                for invite_assignment_invitation_id in invite_assignment_invitations:
                    
                    ## check if it is expired?
                    invite_assignment_invitation = openreview.tools.get_invitation(client, invite_assignment_invitation_id)

                    if invite_assignment_invitation:
                        grouped_edges = client.get_grouped_edges(invitation=invite_assignment_invitation.id, label='Pending Sign Up', groupby='tail', domain=venue_id)
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
                                                invitation_edge.ddate = openreview.tools.datetime_millis(datetime.datetime.now())
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

    def compute_dual_submission_metadata(self, alternate_venue, output_file_path, top_percent_cutoff=1, job_id=None, author_overlap_only=False):
        """Detect potential dual submissions between this venue and another venue.

        Computes paper similarity scores (using specter2+scincl) between all
        submissions of both venues, filters to the top percentile, and outputs
        a CSV with similarity scores, title/abstract edit distances, and
        overlapping authors. Can also reuse a previously started similarity
        computation job via ``job_id``.

        The output CSV includes: paper IDs, similarity score, word-level edit
        distances for titles and abstracts, matching authors, author lists,
        titles, and abstracts.

        :param alternate_venue: The other Venue object to compare submissions against. Can be the same venue for intra-venue checks.
        :type alternate_venue: Venue
        :param output_file_path: Directory path where the output CSV file will be saved.
        :type output_file_path: str
        :param top_percent_cutoff: Percentage of top similarity scores to include (e.g. 1 means top 1%).
        :type top_percent_cutoff: float, optional
        :param job_id: Existing similarity computation job ID to reuse instead of starting a new one.
        :type job_id: str, optional
        :param author_overlap_only: If True, only include paper pairs that share at least one author.
        :type author_overlap_only: bool, optional
        """
        short_name_a = self.short_name # Column A
        short_name_b = alternate_venue.short_name # Column B
        same_venue = self.venue_id == alternate_venue.venue_id

        print(f'Computing similarity: {short_name_a} ↔ {short_name_b}')

        ## Compute/retrieve scores

        if not job_id:
            res = self.client.request_paper_similarity(
                name=f'{short_name_a}--{short_name_b}-Paper-Similarity',
                venue_id=self.get_submission_venue_id(),
                alternate_venue_id=alternate_venue.get_submission_venue_id(),
                model='specter2+scincl',
                sparse_value=5
            )
            job_id = res['jobId']
            print('Computing scores for active papers... Job ID: ', job_id)

        results = self.client.get_expertise_results(job_id=job_id, wait_for_complete=True)
        print('Sparse scores retrieved')

        ## Score filtering

        unique_scores = []
        seen_pairs = set()
        for r in results['results']:
            paper_id_a = r.get('entityA', r.get('match_submission'))
            paper_id_b = r.get('entityB', r.get('submission'))
            score = float(r['score'])

            # Remove self-matches
            if paper_id_a == paper_id_b:
                continue

            # Deduplicate mirrored pairs
            pair = tuple(sorted([paper_id_a, paper_id_b]))
            if pair in seen_pairs:
                continue
            seen_pairs.add(pair)

            unique_scores.append((paper_id_a, paper_id_b, score))

        # Apply cutoff
        print(f'Applying {top_percent_cutoff}% score cutoff')

        scores_only = [s for (_, _, s) in unique_scores]
        cutoff = tools.percentile(scores_only, 100 - top_percent_cutoff)
        filtered_scores = [(a, b, s) for (a, b, s) in unique_scores if s >= cutoff]
        print(f'Cutoff score: {cutoff:.4f}')
        print(f'{len(unique_scores)} scores before cutoff')
        print(f'{len(filtered_scores)} scores after cutoff')

        # Sort by score descending
        filtered_scores.sort(key=lambda x: x[2], reverse=True)

        ## Getting paper/author data

        submissions_a = self.client.get_all_notes(invitation=self.get_submission_id())
        submissions_b = submissions_a if same_venue else self.client.get_all_notes(invitation=alternate_venue.get_submission_id())

        print(f'{short_name_a}: Retrieved {len(submissions_a)} submissions')
        print(f'{short_name_b}: Retrieved {len(submissions_b)} submissions')

        papers_by_id_a = {s.id: s for s in submissions_a}
        papers_by_id_b = papers_by_id_a if same_venue else {s.id: s for s in submissions_b}

        paper_ids_from_scores = {id for a, b, _ in filtered_scores for id in (a, b)}

        submissions_from_scores = [
            papers_by_id_a.get(id) or papers_by_id_b.get(id)
            for id in paper_ids_from_scores
            if (papers_by_id_a.get(id) or papers_by_id_b.get(id))
        ]

        all_authors = {
            author_id
            for s in submissions_from_scores
            for author_id in s.content['authorids']['value']
        }

        author_profile_by_id = openreview.tools.get_profiles(self.client, all_authors, as_dict=True)
        print(f'Retrieved {len(author_profile_by_id.keys())} total author profiles')

        ## Create final CSV

        print('Reading results and creating final CSV...')

        # Handle path
        output_file_abs_path = os.path.abspath(output_file_path)
        os.makedirs(output_file_abs_path, exist_ok=True) # Ensure directory exists
        csv_path = os.path.join(output_file_abs_path, f'{short_name_a}--{short_name_b} Similarity Scores.csv')

        with open(csv_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)

            # Write header
            writer.writerow([
                f'{short_name_a} id', f'{short_name_b} id',
                'Score',
                'Title Word Edit Distance', 'Title Word Edit Distance Similarity',
                'Abstract Word Edit Distance', 'Abstract Word Edit Distance Similarity',
                'Matching Authors (if any)',
                f'{short_name_a} authors', f'{short_name_b} authors',
                f'{short_name_a} title', f'{short_name_b} title',
                f'{short_name_a} abstract', f'{short_name_b} abstract'
            ])

            if author_overlap_only:
                print('Filtering scores for overlapping author cases only')

            for paper_id_a, paper_id_b, score in filtered_scores:

                # Fetch metadata
                title_a = papers_by_id_a[paper_id_a].content['title']['value']
                raw_abstract_a = papers_by_id_a[paper_id_a].content['abstract']['value']
                abstract_a = raw_abstract_a.replace("\n", "\\n")
                # Use profile ID if available, otherwise use author ID in paper
                authors_list_a = [
                    author_profile_by_id[author_id].id if author_profile_by_id.get(author_id)
                    else openreview.Profile(id=author_id).id
                    for author_id in papers_by_id_a[paper_id_a].content['authorids']['value']
                ]
                authors_str_a = '|'.join(authors_list_a)

                title_b = papers_by_id_b[paper_id_b].content['title']['value']
                raw_abstract_b = papers_by_id_b[paper_id_b].content['abstract']['value']
                abstract_b = raw_abstract_b.replace("\n", "\\n")
                authors_list_b = [
                    author_profile_by_id[author_id].id if author_profile_by_id.get(author_id)
                    else openreview.Profile(id=author_id).id
                    for author_id in papers_by_id_b[paper_id_b].content['authorids']['value']
                ]
                authors_str_b = '|'.join(authors_list_b)

                # Find overlapping authors
                overlap = set(authors_list_a) & set(authors_list_b)
                overlap_str = '|'.join(overlap) if overlap else 'No Overlap'

                # Skip non-overlapping rows
                if author_overlap_only and not overlap:
                    continue

                # Compute word-level edit distances
                title_words_a = title_a.lower().split()
                title_words_b = title_b.lower().split()
                title_dist = editdistance.eval(title_words_a, title_words_b)
                title_max_words = max(len(title_words_a), len(title_words_b))
                title_norm = round(1 - title_dist / title_max_words, 4) if title_max_words > 0 else 1.0

                abstract_words_a = raw_abstract_a.lower().split()
                abstract_words_b = raw_abstract_b.lower().split()
                abstract_dist = editdistance.eval(abstract_words_a, abstract_words_b)
                abstract_max_words = max(len(abstract_words_a), len(abstract_words_b))
                abstract_norm = round(1 - abstract_dist / abstract_max_words, 4) if abstract_max_words > 0 else 1.0

                writer.writerow([
                    paper_id_a, paper_id_b,
                    round(score, 4),
                    title_dist, title_norm,
                    abstract_dist, abstract_norm,
                    overlap_str,
                    authors_str_a, authors_str_b,
                    title_a, title_b,
                    abstract_a, abstract_b
                ])
        print('File saved at: ', csv_path)
