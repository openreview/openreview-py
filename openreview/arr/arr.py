import csv
import json
from json import tool
import datetime
from io import StringIO
from multiprocessing import cpu_count
from concurrent.futures import ThreadPoolExecutor
from tqdm import tqdm
import openreview
from openreview import tools
from .invitation import InvitationBuilder
from openreview.venue.group import GroupBuilder
from openreview.api import Group
from openreview.api import Note
from openreview.venue.recruitment import Recruitment
class ARR(object):

    def __init__(self, client, venue_id, support_user):

        self.client = client
        self.venue = openreview.venue.Venue(openreview_client, note.content['venue_id'], support_user)
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

    def copy_to_venue(self):
         ## Run test faster
        if 'openreview.net' in self.support_user:
            self.venue.invitation_builder.update_wait_time = 2000
            self.venue.invitation_builder.update_date_string = "#{4/mdate} + 2000"

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