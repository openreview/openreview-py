from __future__ import absolute_import
from queue import Empty

import csv
import json
import time
import datetime
import re
import traceback
from concurrent.futures import ThreadPoolExecutor
from enum import Enum
from io import StringIO
from multiprocessing import cpu_count

from tqdm import tqdm
import os
import concurrent.futures
from .. import openreview, OpenReviewException
from .. import tools
from . import webfield
from . import invitation
from . import matching
from .. import invitations
from deprecated.sphinx import deprecated

class Conference(object):

    class IdentityReaders(Enum):
        PROGRAM_CHAIRS = 0
        SENIOR_AREA_CHAIRS = 1
        SENIOR_AREA_CHAIRS_ASSIGNED = 2
        AREA_CHAIRS = 3
        AREA_CHAIRS_ASSIGNED = 4
        REVIEWERS = 5
        REVIEWERS_ASSIGNED = 6

        @classmethod
        def get_readers(self, conference, number, identity_readers):
            readers = [conference.id]
            if self.PROGRAM_CHAIRS in identity_readers:
                readers.append(conference.get_program_chairs_id())
            if self.SENIOR_AREA_CHAIRS in identity_readers:
                readers.append(conference.get_senior_area_chairs_id())
            if self.SENIOR_AREA_CHAIRS_ASSIGNED in identity_readers:
                readers.append(conference.get_senior_area_chairs_id(number))
            if self.AREA_CHAIRS in identity_readers:
                readers.append(conference.get_area_chairs_id())
            if self.AREA_CHAIRS_ASSIGNED in identity_readers:
                readers.append(conference.get_area_chairs_id(number))
            if self.REVIEWERS in identity_readers:
                readers.append(conference.get_reviewers_id())
            if self.REVIEWERS_ASSIGNED in identity_readers:
                readers.append(conference.get_reviewers_id(number))
            return readers

    def __init__(self, client):
        self.client = client
        self.request_form_id = None
        self.support_user = 'OpenReview.net/Support'
        self.venue_revision_name = 'Venue_Revision'
        self.new = False
        self.use_area_chairs = False
        self.use_senior_area_chairs = False
        self.use_secondary_area_chairs = False
        self.use_ethics_chairs = False
        self.use_ethics_reviewers = False
        self.legacy_anonids = False
        self.legacy_invitation_id = False
        self.groups = []
        self.name = ''
        self.short_name = ''
        self.year = datetime.datetime.now().year
        self.homepage_header = {}
        self.authorpage_header = {}
        self.reviewerpage_header = {}
        self.areachairpage_header = {}
        self.expertise_selection_page_header = {}
        self.invitation_builder = invitation.InvitationBuilder(client)
        self.webfield_builder = webfield.WebfieldBuilder(client)
        self.authors_name = 'Authors'
        self.reviewers_name = 'Reviewers'
        self.reviewer_roles = ['Reviewers']
        self.area_chair_roles = ['Area_Chairs']
        self.senior_area_chair_roles = ['Senior_Area_Chairs']
        self.area_chairs_name = 'Area_Chairs'
        self.senior_area_chairs_name = 'Senior_Area_Chairs'
        self.secondary_area_chairs_name = 'Secondary_Area_Chair'
        self.ethics_chairs_name = 'Ethics_Chairs'
        self.ethics_reviewers_name = 'Ethics_Reviewers'
        self.program_chairs_name = 'Program_Chairs'
        self.recommendation_name = 'Recommendation'
        self.submission_stage = SubmissionStage()
        self.bid_stages = {}
        self.expertise_selection_stage = ExpertiseSelectionStage()
        self.review_stage = ReviewStage()
        self.ethics_review_stage = None
        self.review_rebuttal_stage = None
        self.review_revision_stage = None
        self.review_rating_stage = None
        self.submission_revision_stage = None
        self.comment_stage = CommentStage()
        self.meta_review_stage = MetaReviewStage()
        self.decision_stage = DecisionStage()
        self.layout = 'tabs'
        self.venue_heading_map = {}
        self.enable_reviewer_reassignment = False
        self.default_reviewer_load = {}
        self.reviewer_identity_readers = []
        self.area_chair_identity_readers = []
        self.senior_area_chair_identity_readers = []

    def __create_group(self, group_id, group_owner_id, members = [], is_signatory = True, additional_readers = [], exclude_self_reader=False):
        group = tools.get_group(self.client, id = group_id)
        if group is None:
            readers = [self.id, group_owner_id] if exclude_self_reader else [self.id, group_owner_id, group_id]
            return self.client.post_group(openreview.Group(
                id = group_id,
                readers = ['everyone'] if 'everyone' in additional_readers else readers + additional_readers,
                writers = [self.id, group_owner_id],
                signatures = [self.id],
                signatories = [self.id, group_id] if is_signatory else [self.id, group_owner_id],
                members = members))
        else:
            return self.client.add_members_to_group(group, members)

    def __set_author_page(self):
        authors_group = tools.get_group(self.client, self.get_authors_id())
        if authors_group:
            return self.webfield_builder.set_author_page(self, authors_group)

    def __set_reviewer_page(self):
        reviewers_group = tools.get_group(self.client, self.get_reviewers_id())
        if reviewers_group:
            return self.webfield_builder.set_reviewer_page(self, reviewers_group)

    def __set_area_chair_page(self):
        area_chairs_group = tools.get_group(self.client, self.get_area_chairs_id())
        if area_chairs_group:
            return self.webfield_builder.set_area_chair_page(self, area_chairs_group)

    def __set_senior_area_chair_page(self):
        senior_area_chairs_group = tools.get_group(self.client, self.get_senior_area_chairs_id())
        if senior_area_chairs_group:
            return self.webfield_builder.set_senior_area_chair_page(self, senior_area_chairs_group)

    def __set_expertise_selection_page(self):
        expertise_selection_invitation = tools.get_invitation(self.client, self.get_expertise_selection_id())
        if expertise_selection_invitation:
            return self.webfield_builder.set_expertise_selection_page(self, expertise_selection_invitation)

    def __set_bid_page(self, stage):
        """
        Set a webfield to each available bid invitation
        """
        bid_invitation = tools.get_invitation(self.client, self.get_bid_id(group_id=stage.committee_id))
        if bid_invitation:
            self.webfield_builder.set_bid_page(self, bid_invitation, stage)

    def __set_recommendation_page(self, assignment_title, score_ids, conflict_id, total_recommendations):
        recommendation_invitation = tools.get_invitation(self.client, self.get_recommendation_id())
        if recommendation_invitation:
            return self.webfield_builder.set_recommendation_page(self, recommendation_invitation, assignment_title, score_ids, conflict_id, total_recommendations)

    def expire_invitation(self, invitation_id):
        # Get invitation
        invitation = tools.get_invitation(self.client, id = invitation_id)

        if invitation:
            # Force the expdate
            now = round(time.time() * 1000)
            if not invitation.expdate or invitation.expdate > now:
                invitation.expdate = now
                invitation.duedate = now
                invitation = self.client.post_invitation(invitation)

            return invitation

    ## TODO: use a super invitation here
    def __expire_invitations(self, name):
        invitations = self.client.get_all_invitations(regex = self.get_invitation_id(name, '.*'))

        now = round(time.time() * 1000)

        for invitation in invitations:
            if not invitation.expdate or invitation.expdate > now:
                invitation.expdate = now
                invitation = self.client.post_invitation(invitation)

        return len(invitations)

    def __create_submission_stage(self):
        under_submission = self.submission_stage.is_under_submission()
        return self.invitation_builder.set_submission_invitation(self, under_submission=under_submission)

    def __create_expertise_selection_stage(self):

        self.invitation_builder.set_expertise_selection_invitation(self)
        return self.__set_expertise_selection_page()

    def __create_registration_stage(self, stage):
        return self.invitation_builder.set_registration_invitation(self, stage)

    def __create_bid_stage(self, stage):

        self.invitation_builder.set_bid_invitation(self, stage)
        return self.__set_bid_page(stage)

    def __create_review_stage(self):

        notes = list(self.get_submissions())
        invitations = self.invitation_builder.set_review_invitation(self, notes)

        if self.review_stage.rating_field_name:
            self.webfield_builder.edit_web_string_value(self.client.get_group(self.get_program_chairs_id()), 'REVIEW_RATING_NAME', self.review_stage.rating_field_name)
            if self.use_area_chairs:
                self.webfield_builder.edit_web_string_value(self.client.get_group(self.get_area_chairs_id()), 'REVIEW_RATING_NAME', self.review_stage.rating_field_name)
            self.webfield_builder.edit_web_string_value(self.client.get_group(self.get_reviewers_id()), 'REVIEW_RATING_NAME', self.review_stage.rating_field_name)
            self.webfield_builder.edit_web_string_value(self.client.get_group(self.get_authors_id()), 'REVIEW_RATING_NAME', self.review_stage.rating_field_name)

        if self.review_stage.confidence_field_name:
            self.webfield_builder.edit_web_string_value(self.client.get_group(self.get_program_chairs_id()), 'REVIEW_CONFIDENCE_NAME', self.review_stage.confidence_field_name)
            if self.use_area_chairs:
                self.webfield_builder.edit_web_string_value(self.client.get_group(self.get_area_chairs_id()), 'REVIEW_CONFIDENCE_NAME', self.review_stage.confidence_field_name)
            self.webfield_builder.edit_web_string_value(self.client.get_group(self.get_authors_id()), 'REVIEW_CONFIDENCE_NAME', self.review_stage.confidence_field_name)

        return invitations

    def __create_ethics_review_stage(self):

        numbers = ','.join(map(str, self.ethics_review_stage.submission_numbers))
        print('flagged submissions', numbers)
        notes = list(self.get_submissions(number=numbers))
        
        ## Unflag existing papers with no assigned reviewers
        groups = self.client.get_groups(regex=self.get_ethics_reviewers_id(number='.*'))
        for group in groups:
            print('process group', group.id)
            if len(group.members) == 0:
                number = self.get_number_from_committee(group.id)
                if number and number not in self.ethics_review_stage.submission_numbers:
                    ## Delete group
                    self.client.delete_group(group.id)
                    ## Expire the invitation
                    invitation = tools.get_invitation(self.client, self.get_invitation_id(self.ethics_review_stage.name, number))
                    invitation.expdate = openreview.tools.datetime_millis(datetime.datetime.utcnow())
                    self.client.post_invitation(invitation)
        
        ## Create ethics paper groups
        for note in tqdm(notes):

            ethics_reviewers_id=self.get_ethics_reviewers_id(number=note.number)
            group = tools.get_group(self.client, id = ethics_reviewers_id)
            if not group:
                self.client.post_group(openreview.Group(id=ethics_reviewers_id,
                    readers=[self.id, self.get_ethics_chairs_id(), ethics_reviewers_id],
                    nonreaders=[self.get_authors_id(note.number)],
                    deanonymizers=[self.id, self.get_ethics_chairs_id()],
                    writers=[self.id],
                    signatures=[self.id],
                    signatories=[self.id],
                    anonids=True,
                    members=group.members if group else [])
                )

        ## Make submissions visible to the ethics committee
        self.create_blind_submissions(number=numbers)

        ## Setup paper matching
        self.setup_committee_matching(self.get_ethics_reviewers_id(), compute_affinity_scores=False, compute_conflicts=True)
        self.invitation_builder.set_assignment_invitation(self, self.get_ethics_reviewers_id())      

        ## Make reviews visible to the ethics committee
        self.invitation_builder.set_review_invitation(self, notes)
        invitations = self.invitation_builder.set_ethics_review_invitation(self, notes)
        return invitations 

    def __create_review_rebuttal_stage(self):
        invitation = self.get_invitation_id(self.review_stage.name, '.*')
        review_iterator = self.client.get_all_notes(invitation = invitation)
        return self.invitation_builder.set_review_rebuttal_invitation(self, review_iterator)

    def __create_review_revision_stage(self):
        invitation = self.get_invitation_id(self.review_stage.name, '.*')
        review_iterator = self.client.get_all_notes(invitation = invitation)
        return self.invitation_builder.set_review_revision_invitation(self, review_iterator)

    def __create_review_rating_stage(self):
        invitation = self.get_invitation_id(self.review_stage.name, '.*')
        review_iterator = self.client.get_all_notes(invitation = invitation)
        return self.invitation_builder.set_review_rating_invitation(self, review_iterator)

    def __create_comment_stage(self):

        ## Create comment invitations per paper
        notes = list(self.get_submissions())
        return self.invitation_builder.set_comment_invitation(self, notes)

    def __create_meta_review_stage(self):

        notes = list(self.get_submissions())
        return self.invitation_builder.set_meta_review_invitation(self, notes)

    def __create_decision_stage(self):

        notes = list(self.get_submissions())
        return self.invitation_builder.set_decision_invitation(self, notes)

    def __create_submission_revision_stage(self):
        invitation = tools.get_invitation(self.client, self.get_submission_id())
        if invitation:
            notes = self.get_submissions(accepted=self.submission_revision_stage.only_accepted, details='original')
            if self.submission_revision_stage.only_accepted:
                all_notes = self.get_submissions(details='original')
                accepted_note_ids = [note.id for note in notes]
                non_accepted_notes = [note for note in all_notes if note.id not in accepted_note_ids]
                expire_invitation_ids = [self.get_invitation_id(self.submission_revision_stage.name, note.number) for note in non_accepted_notes]
                tools.concurrent_requests(self.expire_invitation, expire_invitation_ids)
            return self.invitation_builder.set_revise_submission_invitation(self, notes, invitation.reply['content'])

    ## Deprecated, use this only for manual assignments
    def set_reviewer_reassignment(self, enabled = True):
        self.enable_reviewer_reassignment = enabled

        # Update PC & AC homepages
        pc_group = self.client.get_group(self.get_program_chairs_id())
        self.webfield_builder.edit_web_value(pc_group, 'ENABLE_REVIEWER_REASSIGNMENT', str(enabled).lower())

        if self.use_area_chairs:
            ac_group = self.client.get_group(self.get_area_chairs_id())
            self.webfield_builder.edit_web_value(ac_group, 'ENABLE_REVIEWER_REASSIGNMENT', str(enabled).lower())

    ## Use for proposed/deployed assignments
    def set_reviewer_edit_assignments(self, assignment_title=None):
        print('set_reviewer_edit_assignments', assignment_title)
        if self.use_area_chairs:
            ac_group = self.client.get_group(self.get_area_chairs_id())
            ac_group=self.webfield_builder.edit_web_value(ac_group, 'ENABLE_EDIT_REVIEWER_ASSIGNMENTS', 'true')
            if assignment_title:
                self.webfield_builder.edit_web_string_value(ac_group, 'REVIEWER_ASSIGNMENT_TITLE', assignment_title)
            else:
                self.webfield_builder.edit_web_string_value(ac_group, 'REVIEWER_ASSIGNMENT_TITLE', '')


    def set_id(self, id):
        self.id = id

    def get_id(self):
        return self.id

    def is_new(self):
        return self.new

    def set_name(self, name):
        self.name = name

    def get_name(self):
        return self.name

    def set_short_name(self, name):
        self.short_name = name

    def get_short_name(self):
        return self.short_name

    def set_year(self, year):
        self.year = year

    def get_year(self):
        return self.year

    def set_reviewers_name(self, name):
        self.reviewers_name = name

    def set_submission_stage(self, stage):
        self.submission_stage = stage
        return self.__create_submission_stage()

    def set_expertise_selection_stage(self, stage):
        self.expertise_selection_stage = stage
        return self.__create_expertise_selection_stage()

    def set_registration_stage(self, stage):
        return self.__create_registration_stage(stage)

    def set_bid_stage(self, stage):
        self.bid_stages[stage.committee_id] = stage
        return self.__create_bid_stage(stage)

    def set_review_stage(self, stage):
        self.review_stage = stage
        self.create_review_stage()

    def create_review_stage(self):
        if self.review_stage:
            return self.__create_review_stage()

    def create_ethics_review_stage(self):
        if self.ethics_review_stage:
            return self.__create_ethics_review_stage()

    def set_review_rebuttal_stage(self, stage):
        self.review_rebuttal_stage = stage
        return self.__create_review_rebuttal_stage()

    def set_review_revision_stage(self, stage):
        self.review_revision_stage = stage
        return self.__create_review_revision_stage()

    def set_review_rating_stage(self, stage):
        self.review_rating_stage = stage
        return self.__create_review_rating_stage()

    def set_comment_stage(self, stage):
        self.comment_stage = stage
        return self.__create_comment_stage()

    def set_meta_review_stage(self, stage):
        self.meta_review_stage = stage
        return self.__create_meta_review_stage()

    def set_submission_revision_stage(self, stage):
        self.submission_revision_stage = stage
        return self.__create_submission_revision_stage()

    def set_decision_stage(self, stage):
        self.decision_stage = stage
        self.__create_decision_stage()

        if self.decision_stage.decisions_file:
            decisions = self.client.get_attachment(id=self.request_form_id, field_name='decisions_file')
            self.post_decisions(decisions)

    def set_area_chairs_name(self, name):
        if self.use_area_chairs:
            self.area_chairs_name = name
        else:
            raise openreview.OpenReviewException('Venue\'s "has_area_chairs" setting is disabled')

    def set_secondary_area_chairs_name(self, name):
        if self.use_secondary_area_chairs:
            self.secondary_area_chairs_name = name
        else:
            raise openreview.OpenReviewException('Venue\'s "has_secondary_area_chairs" setting is disabled')

    def set_program_chairs_name(self, name):
        self.program_chairs_name = name

    def get_program_chairs_id(self):
        return self.id + '/' + self.program_chairs_name

    def get_reviewers_id(self, number = None):
        return self.get_committee_id(self.reviewers_name, number)

    def get_anon_reviewer_id(self, number=None, anon_id=None, name=None):
        reviewers_name = name if name else self.reviewers_name
        single_reviewer_name=reviewers_name[:-1] if reviewers_name.endswith('s') else reviewers_name
        if self.legacy_anonids:
            return f'{self.id}/Paper{number}/AnonReviewer{anon_id}'
        return f'{self.id}/Paper{number}/{single_reviewer_name}_{anon_id}'

    def get_anon_area_chair_id(self, number=None, anon_id=None):
        single_area_chair_name=self.area_chairs_name[:-1] if self.area_chairs_name.endswith('s') else self.area_chairs_name
        if self.legacy_anonids:
            return f'{self.id}/Paper{number}/Area_Chair{anon_id}'
        return f'{self.id}/Paper{number}/{single_area_chair_name}_{anon_id}'

    def get_reviewers_name(self, pretty=True):
        if pretty:
            name=self.reviewers_name.replace('_', ' ')
            return name[:-1] if name.endswith('s') else name
        return self.reviewers_name

    def get_ethics_reviewers_name(self, pretty=True):
        if pretty:
            name=self.ethics_reviewers_name.replace('_', ' ')
            return name[:-1] if name.endswith('s') else name
        return self.ethics_reviewers_name

    def get_area_chairs_name(self, pretty=True):
        if pretty:
            name=self.area_chairs_name.replace('_', ' ')
            return name[:-1] if name.endswith('s') else name
        return self.area_chairs_name

    def get_secondary_area_chairs_name(self, pretty=True):
        if pretty:
            return self.use_secondary_area_chairs.replace('_', ' ')
        return self.use_secondary_area_chairs

    def get_authors_id(self, number = None):
        return self.get_committee_id(self.authors_name, number)

    def get_accepted_authors_id(self):
        return self.id + '/' + self.authors_name + '/Accepted'

    def get_area_chairs_id(self, number = None):
        return self.get_committee_id(self.area_chairs_name, number)

    def get_senior_area_chairs_id(self, number = None):
        return self.get_committee_id(self.senior_area_chairs_name, number)

    def get_ethics_chairs_id(self, number = None):
        return self.get_committee_id(self.ethics_chairs_name, number)

    def get_ethics_reviewers_id(self, number = None):
        return self.get_committee_id(self.ethics_reviewers_name, number)

    def get_secondary_area_chairs_id(self, number=None):
        return self.get_committee_id(self.secondary_area_chairs_name, number)

    def get_committee(self, number = None, submitted_reviewers = False, with_authors = False):
        committee = [self.get_id()]

        if with_authors:
            committee.append(self.get_authors_id(number))

        if submitted_reviewers:
            committee.append(self.get_reviewers_id(number) + '/Submitted')
        else:
            committee.append(self.get_reviewers_id(number))

        if self.use_area_chairs:
            committee.append(self.get_area_chairs_id(number))

        if self.use_senior_area_chairs:
            committee.append(self.get_senior_area_chairs_id(number))

        committee.append(self.get_program_chairs_id())

        return committee

    def get_committee_names(self):
        committee=[self.reviewers_name]

        if self.use_area_chairs:
            committee.append(self.area_chairs_name)

        if self.use_senior_area_chairs:
            committee.append(self.senior_area_chairs_name)

        return committee

    def get_committee_id(self, name, number=None):
        committee_id = self.id + '/'
        if number:
            committee_id = f'{committee_id}Paper{number}/{name}'
        else:
            committee_id = committee_id + name
        return committee_id

    def get_number_from_committee(self, committee_id):
        tokens = committee_id.split('/')
        for token in tokens:
            if token.startswith('Paper'):
                token = token.replace('Paper', '')
                return int(token)
        return None

    def get_committee_name(self, committee_id, pretty=False):
        name = committee_id.split('/')[-1]

        if pretty:
            name = name.replace('_', ' ')
            if name.endswith('s'):
                return name[:-1]
        return name

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

    def get_submission_id(self):
        return self.submission_stage.get_submission_id(self)

    def get_blind_submission_id(self):
        return self.submission_stage.get_blind_submission_id(self)

    def get_expertise_selection_id(self):
        return self.get_invitation_id(self.expertise_selection_stage.name)

    def get_bid_id(self, group_id):
        return self.get_invitation_id('Bid', prefix=group_id)

    def get_recommendation_id(self, group_id=None):
        if not group_id:
            group_id = self.get_reviewers_id()
        return self.get_invitation_id(self.recommendation_name, prefix=group_id)

    def get_registration_id(self, committee_id):
        return self.get_invitation_id(name = 'Registration', prefix = committee_id)

    def get_invitation_id(self, name, number = None, prefix = None):
        invitation_id = self.id
        if prefix:
            invitation_id = prefix
        if number:
            if self.legacy_invitation_id:
                invitation_id = invitation_id + '/-/Paper' + str(number) + '/'
            else:
                invitation_id = invitation_id + '/Paper' + str(number) + '/-/'
        else:
            invitation_id = invitation_id + '/-/'

        invitation_id =  invitation_id + name
        return invitation_id

    def set_conference_groups(self, groups):
        self.groups = groups

    def get_conference_groups(self):
        return self.groups

    def get_paper_assignment_id(self, group_id, deployed=False, invite=False):
        if deployed:
            return self.get_invitation_id('Assignment', prefix=group_id)
        if invite:
            return self.get_invitation_id('Invite_Assignment', prefix=group_id)
        return self.get_invitation_id('Proposed_Assignment', prefix=group_id)


    def get_affinity_score_id(self, group_id):
        return self.get_invitation_id('Affinity_Score', prefix=group_id)

    def get_elmo_score_id(self, group_id):
        return self.get_invitation_id('ELMo_Score', prefix=group_id)

    def get_conflict_score_id(self, group_id):
        return self.get_invitation_id('Conflict', prefix=group_id)

    def get_custom_max_papers_id(self, group_id):
        return self.get_invitation_id('Custom_Max_Papers', prefix=group_id)

    def set_homepage_header(self, header):
        self.homepage_header = header

    def set_authorpage_header(self, header):
        self.authorpage_header = header
        return self.__set_author_page()

    def get_authorpage_header(self):
        return self.authorpage_header

    def set_reviewerpage_header(self, header):
        self.reviewerpage_header = header
        return self.__set_reviewer_page()

    def get_reviewerpage_header(self):
        return self.reviewerpage_header

    def set_areachairpage_header(self, header):
        if self.use_area_chairs:
            self.areachairpage_header = header
            return self.__set_area_chair_page()
        else:
            raise openreview.OpenReviewException('Conference "has_area_chairs" setting is disabled')

    def get_areachairpage_header(self):
        return self.areachairpage_header

    def set_expertise_selection_page_header(self, header):
        self.expertise_selection_page_header = header
        return self.__set_expertise_selection_page

    def get_expertise_selection_page_header(self):
        return self.expertise_selection_page_header

    def set_homepage_layout(self, layout):
        self.layout = layout

    def set_venue_heading_map(self, decision_heading_map):
        venue_heading_map = {}
        for decision, tab_name in decision_heading_map.items():
            venue_heading_map[tools.decision_to_venue(self.short_name, decision)] = tab_name
        self.venue_heading_map = venue_heading_map

    def has_area_chairs(self, has_area_chairs):
        self.use_area_chairs = has_area_chairs
        pc_group = tools.get_group(self.client, self.get_program_chairs_id())
        if pc_group and pc_group.web:
            # update PC console
            if self.use_area_chairs:
                self.webfield_builder.edit_web_string_value(pc_group, 'AREA_CHAIRS_ID', self.get_area_chairs_id())
            else:
                self.webfield_builder.edit_web_string_value(pc_group, 'AREA_CHAIRS_ID', '')

    def has_senior_area_chairs(self, has_senior_area_chairs):
        self.use_senior_area_chairs = has_senior_area_chairs

    def has_secondary_area_chairs(self, has_secondary_area_chairs):
        self.use_secondary_area_chairs = has_secondary_area_chairs

    def get_homepage_options(self):
        options = {}
        if self.name:
            options['subtitle'] = self.name
        if self.homepage_header:
            options['title'] = self.homepage_header.get('title')
            options['subtitle'] = self.homepage_header.get('subtitle')
            options['location'] = self.homepage_header.get('location')
            options['date'] = self.homepage_header.get('date')
            options['website'] = self.homepage_header.get('website')
            options['instructions'] = self.homepage_header.get('instructions')
            options['deadline'] = self.homepage_header.get('deadline')
            options['contact'] = self.homepage_header.get('contact')
        return options

    def get_submissions(self, accepted = False, number=None, details = None, sort = None):
        invitation = self.get_blind_submission_id()
        notes = self.client.get_all_notes(invitation = invitation, number=number, details = details, sort = sort)
        if accepted:
            decisions = self.client.get_all_notes(invitation = self.get_invitation_id(self.decision_stage.name, '.*'))
            accepted_forums = [d.forum for d in decisions if 'Accept' in d.content['decision']]
            accepted_notes = [n for n in notes if n.id in accepted_forums]
            return accepted_notes
        return notes

    def get_withdrawn_submissions(self, details=None):
        invitation = self.submission_stage.get_withdrawn_submission_id(self)
        return self.client.get_all_notes(invitation=invitation, details=details)

    def get_desk_rejected_submissions(self, details=None):
        invitation = self.submission_stage.get_desk_rejected_submission_id(self)
        return self.client.get_all_notes(invitation=invitation, details=details)

    def get_reviewer_identity_readers(self, number):
        ## default value
        if not self.reviewer_identity_readers:
            identity_readers=[self.id]
            if self.use_senior_area_chairs:
                identity_readers.append(self.get_senior_area_chairs_id(number))
            if self.use_area_chairs:
                identity_readers.append(self.get_area_chairs_id(number))
            return identity_readers

        return self.IdentityReaders.get_readers(self, number, self.reviewer_identity_readers)

    def get_area_chair_identity_readers(self, number):
        ## default value
        if not self.area_chair_identity_readers:
            identity_readers=[self.id]
            if self.use_senior_area_chairs:
                identity_readers.append(self.get_senior_area_chairs_id(number))
            identity_readers.append(self.get_area_chairs_id(number))
            return identity_readers

        return self.IdentityReaders.get_readers(self, number, self.area_chair_identity_readers)

    def get_senior_area_chair_identity_readers(self, number):
        ## default value
        if not self.senior_area_chair_identity_readers:
            return [self.id, self.get_senior_area_chairs_id(number)]

        return self.IdentityReaders.get_readers(self, number, self.senior_area_chair_identity_readers)

    def get_reviewer_paper_group_readers(self, number):
        readers=[self.id]
        if self.use_senior_area_chairs:
            readers.append(self.get_senior_area_chairs_id(number))
        if self.use_area_chairs:
            readers.append(self.get_area_chairs_id(number))
        readers.append(self.get_reviewers_id(number))
        return readers

    def get_reviewer_paper_group_writers(self, number):
        readers=[self.id]
        if self.use_senior_area_chairs:
            readers.append(self.get_senior_area_chairs_id(number))
        if self.use_area_chairs:
            readers.append(self.get_area_chairs_id(number))
        return readers


    def get_area_chair_paper_group_readers(self, number):
        readers=[self.id, self.get_program_chairs_id()]
        if self.use_senior_area_chairs:
            readers.append(self.get_senior_area_chairs_id(number))
        readers.append(self.get_area_chairs_id(number))
        if self.IdentityReaders.REVIEWERS_ASSIGNED in self.area_chair_identity_readers:
            readers.append(self.get_reviewers_id(number))
        return readers

    def create_withdraw_invitations(self, reveal_authors=False, reveal_submission=False, email_pcs=False,
                                    hide_fields=[], force=False):
        if not force and reveal_submission and not self.submission_stage.public:
            raise openreview.OpenReviewException('Can not reveal withdrawn submissions that are not originally public')

        if not force and not reveal_authors and not self.submission_stage.double_blind:
            raise openreview.OpenReviewException('Can not hide authors of submissions in single blind or open venue')

        return self.invitation_builder.set_withdraw_invitation(self, reveal_authors, reveal_submission, email_pcs, hide_fields=hide_fields)

    def create_desk_reject_invitations(self, reveal_authors=False, reveal_submission=False,
                                       hide_fields=None, force=False):

        if not force and reveal_submission and not self.submission_stage.public:
            raise openreview.OpenReviewException('Can not reveal desk-rejected submissions that are not originally public')

        if not force and not reveal_authors and not self.submission_stage.double_blind:
            raise openreview.OpenReviewException('Can not hide authors of submissions in single blind or open venue')

        return self.invitation_builder.set_desk_reject_invitation(self, reveal_authors, reveal_submission, hide_fields=hide_fields)

    def create_paper_groups(self, authors=False, reviewers=False, area_chairs=False, senior_area_chairs=False, overwrite=False):

        notes_iterator = self.get_submissions(sort='number:asc', details='original')
        author_group_ids = []
        paper_reviewer_group_invitation=self.invitation_builder.set_paper_group_invitation(self, self.get_reviewers_id())
        if self.use_area_chairs:
            paper_area_chair_group_invitation=self.invitation_builder.set_paper_group_invitation(self, self.get_area_chairs_id())

        group_by_id = { g.id: g for g in self.client.get_all_groups(regex=f'{self.id}/Paper.*') }

        for n in tqdm(list(notes_iterator), desc='create_paper_groups'):
            # Paper group
            group_id = '{conference_id}/Paper{number}'.format(conference_id=self.id, number=n.number)
            group = group_by_id.get(group_id)
            if not group or overwrite:
                self.client.post_group(openreview.Group(id=group_id,
                    readers=[self.id],
                    writers=[self.id],
                    signatures=[self.id],
                    signatories=[self.id],
                    members=group.members if group else []
                ))            

            # Author Paper group
            if authors:
                authorids = n.content.get('authorids')
                if n.details and n.details.get('original'):
                    authorids = n.details['original']['content']['authorids']
                author_paper_group = self.__create_group(self.get_authors_id(n.number), self.id, authorids)
                author_group_ids.append(author_paper_group.id)

            # Reviewers Paper group
            if reviewers:
                if self.legacy_anonids:
                    self.__create_group(
                        self.get_reviewers_id(number=n.number),
                        self.get_area_chairs_id(number=n.number) if self.use_area_chairs else self.id,
                        is_signatory = False)
                else:
                    reviewers_id=self.get_reviewers_id(number=n.number)
                    group = group_by_id.get(reviewers_id)
                    if not group or overwrite:
                        self.client.post_group(openreview.Group(id=reviewers_id,
                            invitation=paper_reviewer_group_invitation.id,
                            readers=self.get_reviewer_paper_group_readers(n.number),
                            nonreaders=[self.get_authors_id(n.number)],
                            deanonymizers=self.get_reviewer_identity_readers(n.number),
                            writers=self.get_reviewer_paper_group_writers(n.number),
                            signatures=[self.id],
                            signatories=[self.id],
                            anonids=True,
                            members=group.members if group else []
                        ))

                # Reviewers Submitted Paper group
                reviewers_submitted_id = self.get_reviewers_id(number=n.number) + '/Submitted'
                group = group_by_id.get(reviewers_submitted_id)
                if not group or overwrite:
                    readers=[self.id]
                    if self.use_senior_area_chairs:
                        readers.append(self.get_senior_area_chairs_id(n.number))
                    if self.use_area_chairs:
                        readers.append(self.get_area_chairs_id(n.number))
                    readers.append(reviewers_submitted_id)                    
                    self.client.post_group(openreview.Group(id=reviewers_submitted_id,
                        readers=readers,
                        writers=[self.id],
                        signatures=[self.id],
                        signatories=[self.id],
                        members=group.members if group else []
                    ))

            # Area Chairs Paper group
            if self.use_area_chairs and area_chairs:
                if self.legacy_anonids:
                    self.__create_group(self.get_area_chairs_id(number=n.number), self.id)
                else:
                    area_chairs_id=self.get_area_chairs_id(number=n.number)
                    group = group_by_id.get(area_chairs_id)
                    if not group or overwrite:
                        self.client.post_group(openreview.Group(id=area_chairs_id,
                            invitation=paper_area_chair_group_invitation.id,
                            readers=self.get_area_chair_paper_group_readers(n.number),
                            nonreaders=[self.get_authors_id(n.number)],
                            deanonymizers=self.get_area_chair_identity_readers(n.number),
                            writers=[self.id],
                            signatures=[self.id],
                            signatories=[self.id],
                            anonids=True,
                            members=group.members if group else []
                        ))

            # Senior Area Chairs Paper group
            if self.use_senior_area_chairs and senior_area_chairs:
                senior_area_chairs_id=self.get_senior_area_chairs_id(number=n.number)
                group = group_by_id.get(senior_area_chairs_id)
                if not group or overwrite:
                    self.client.post_group(openreview.Group(id=senior_area_chairs_id,
                        readers=self.get_senior_area_chair_identity_readers(n.number),
                        nonreaders=[self.get_authors_id(n.number)],
                        writers=[self.id],
                        signatures=[self.id],
                        signatories=[self.id, senior_area_chairs_id],
                        members=group.members if group else []
                    ))


        if author_group_ids:
            self.__create_group(self.get_authors_id(), self.id, author_group_ids, additional_readers=['everyone'])

        # Add this group to active_venues
        active_venues = self.client.get_group('active_venues')
        self.client.add_members_to_group(active_venues, self.id)

    def create_blind_submissions(self, hide_fields=[], number=None):

        if not self.submission_stage.double_blind:
            raise openreview.OpenReviewException('Conference is not double blind')

        submissions_by_original = { note.original: note for note in self.get_submissions() }
        withdrawn_submissions_by_original = {note.original: note for note in self.get_withdrawn_submissions()}
        desk_rejected_submissions_by_original = {note.original: note for note in self.get_desk_rejected_submissions()}

        self.invitation_builder.set_blind_submission_invitation(self, hide_fields)
        blinded_notes = []

        for note in tqdm(self.client.get_all_notes(invitation=self.get_submission_id(), sort='number:asc', number=number), desc='create_blind_submissions'):
            # If the note was either withdrawn or desk-rejected already, we should not create another blind copy
            if withdrawn_submissions_by_original.get(note.id) or desk_rejected_submissions_by_original.get(note.id):
                continue

            existing_blind_note = submissions_by_original.get(note.id)
            blind_content = {
                'authors': ['Anonymous'],
                'authorids': [self.get_authors_id(number=note.number)],
            }

            for field in hide_fields:
                blind_content[field] = ''

            blind_readers = self.submission_stage.get_readers(self, note.number)

            blind_note = openreview.Note(
                id = existing_blind_note.id if existing_blind_note else None,
                original= note.id,
                invitation= self.get_blind_submission_id(),
                forum=None,
                signatures= [self.id],
                writers= [self.id],
                readers= blind_readers,
                content= blind_content)

            blind_note = self.client.post_note(blind_note)

            generate_bibtex = not existing_blind_note or existing_blind_note and 'venue' not in existing_blind_note.content

            if self.submission_stage.public and generate_bibtex:
                bibtex = tools.generate_bibtex(
                    note=note,
                    venue_fullname=self.name,
                    url_forum=blind_note.id,
                    year=str(self.get_year()))

                revision_note = self.client.post_note(openreview.Note(
                    invitation = f'{self.support_user}/-/{self.venue_revision_name}',
                    forum = note.id,
                    referent = note.id,
                    readers = ['everyone'],
                    writers = [self.id],
                    signatures = [self.id],
                    content = {
                        '_bibtex': bibtex
                    }
                ))
            blinded_notes.append(blind_note)

        # Update PC console with double blind submissions
        pc_group = self.client.get_group(self.get_program_chairs_id())
        self.webfield_builder.edit_web_string_value(pc_group, 'BLIND_SUBMISSION_ID', self.get_blind_submission_id())

        return blinded_notes

    def setup_first_deadline_stage(self, force=False, hide_fields=[], allow_author_reorder=False):

        if self.submission_stage.double_blind:
            self.create_blind_submissions(hide_fields=hide_fields)
        else:
            self.invitation_builder.set_submission_invitation(conference=self)
            submissions = self.get_submissions()
            for s in submissions:
                final_readers =  self.submission_stage.get_readers(conference=self, number=s.number)
                if s.readers != final_readers:
                    s.readers = final_readers
                    self.client.post_note(s)

        self.create_paper_groups(authors=True, reviewers=True, area_chairs=True, senior_area_chairs=True)

        self.submission_revision_stage = SubmissionRevisionStage(name='Revision',
            start_date=None if force else self.submission_stage.due_date,
            due_date=self.submission_stage.second_due_date,
            additional_fields=self.submission_stage.additional_fields,
            remove_fields=self.submission_stage.remove_fields,
            only_accepted=False,
            multiReply=False,
            allow_author_reorder=allow_author_reorder
        )
        self.__create_submission_revision_stage()

        self.create_withdraw_invitations(
            reveal_authors=not self.submission_stage.double_blind,
            reveal_submission=False,
            email_pcs=False,
            hide_fields=hide_fields,
            force=True
        )
        self.create_desk_reject_invitations(
            reveal_authors=not self.submission_stage.double_blind,
            reveal_submission=False,
            hide_fields=hide_fields,
            force=True
        )


    def setup_final_deadline_stage(self, force=False, hide_fields=[]):

        if self.submission_stage.double_blind and not (self.submission_stage.author_names_revealed or self.submission_stage.papers_released):
            self.create_blind_submissions(hide_fields)

        if not self.submission_stage.double_blind and not self.submission_stage.papers_released and not self.submission_stage.create_groups:
            self.invitation_builder.set_submission_invitation(self)
            for note in tqdm(self.client.get_all_notes(invitation=self.get_submission_id(), sort='number:asc'), desc='set_final_readers'):
                final_readers =  self.submission_stage.get_readers(conference=self, number=note.number)
                if note.readers != final_readers:
                    note.readers = final_readers
                    self.client.post_note(note)

        self.create_paper_groups(authors=True, reviewers=True, area_chairs=True, senior_area_chairs=True)
        self.create_withdraw_invitations(
            reveal_authors=self.submission_stage.withdrawn_submission_reveal_authors,
            reveal_submission=self.submission_stage.withdrawn_submission_public,
            email_pcs=self.submission_stage.email_pcs_on_withdraw,
            hide_fields=hide_fields
        )
        self.create_desk_reject_invitations(
            reveal_authors=self.submission_stage.desk_rejected_submission_reveal_authors,
            reveal_submission=self.submission_stage.desk_rejected_submission_public,
            hide_fields=hide_fields
        )

        self.set_authors()
        self.set_reviewers()
        if self.use_area_chairs:
            self.set_area_chairs()

    def setup_post_submission_stage(self, force=False, hide_fields=[]):

        now = datetime.datetime.utcnow()

        if self.submission_stage.second_due_date:
            if self.submission_stage.due_date < now and now < self.submission_stage.second_due_date:
                self.setup_first_deadline_stage(force, hide_fields)
            elif self.submission_stage.second_due_date < now:
                self.setup_final_deadline_stage(force, hide_fields)
            elif force:
                ## For testing purposes
                self.setup_final_deadline_stage(force, hide_fields)
        else:
            if force or (self.submission_stage.due_date and self.submission_stage.due_date < datetime.datetime.now()):
                self.setup_final_deadline_stage(force, hide_fields)

    ## Deprecated
    def open_bids(self):
        return self.__create_bid_stage()

    def close_bids(self):
        self.expire_invitation(self.get_bid_id(self.get_reviewers_id()))
        if self.use_area_chairs:
            self.expire_invitation(self.get_bid_id(self.get_area_chairs_id()))

    def open_recommendations(self, assignment_title, start_date = None, due_date = None, total_recommendations = 7):

        score_ids = []
        invitation_ids = [
            self.get_invitation_id('TPMS_Score', prefix=self.get_reviewers_id()),
            self.get_invitation_id('Affinity_Score', prefix=self.get_reviewers_id()),
            self.get_bid_id(self.get_reviewers_id())
        ]

        for invitation_id in invitation_ids:
            if tools.get_invitation(self.client, invitation_id):
                score_ids.append(invitation_id)

        self.invitation_builder.set_recommendation_invitation(self, start_date, due_date, total_recommendations)
        return self.__set_recommendation_page(assignment_title, score_ids, self.get_conflict_score_id(self.get_reviewers_id()), total_recommendations)

    def open_paper_ranking(self, committee_id, start_date=None, due_date=None):
        return self.invitation_builder.set_paper_ranking_invitation(self, committee_id, start_date, due_date)

    def open_comments(self):
        self.__create_comment_stage()

    def close_comments(self, name):
        return self.__expire_invitations(name)

    ## Deprecated
    def open_reviews(self):
        return self.__create_review_stage()

    def close_reviews(self):
        return self.__expire_invitations(self.review_stage.name)

    ## Deprecated
    def open_meta_reviews(self):
        return self.__create_meta_review_stage()

    ## Deprecated
    def open_decisions(self):
        return self.__create_decision_stage()

    def open_revise_submissions(self, name = 'Revision', start_date = None, due_date = None, additional_fields = {}, remove_fields = [], only_accepted = False):
        self.submission_revision_stage = SubmissionRevisionStage(name=name, start_date=start_date, due_date=due_date, additional_fields=additional_fields, remove_fields=remove_fields, only_accepted=only_accepted)
        return self.__create_submission_revision_stage()

    ## Deprecated
    def open_revise_reviews(self, name = 'Review_Revision', start_date = None, due_date = None, additional_fields = {}, remove_fields = []):
        self.review_revision_stage = ReviewRevisionStage(name=name, start_date=start_date, due_date=due_date, additional_fields=additional_fields, remove_fields=remove_fields)
        return self.__create_review_revision_stage()

    def close_revise_submissions(self, name):
        return self.__expire_invitations(name)

    def set_program_chairs(self, emails = []):
        pcs = self.__create_group(self.get_program_chairs_id(), self.id, emails)
        self.webfield_builder.set_program_chair_page(self, pcs)
        ## Give program chairs admin permissions
        self.__create_group(self.id, '~Super_User1', [self.get_program_chairs_id()])
        return pcs

    def set_senior_area_chairs(self, emails = []):
        if self.use_senior_area_chairs:
            self.__create_group(group_id=self.get_senior_area_chairs_id(), group_owner_id=self.id, members=emails)

            return self.__set_senior_area_chair_page()
        else:
            raise openreview.OpenReviewException('Conference "has_senior_area_chairs" setting is disabled')

    def set_area_chairs(self, emails = []):
        if self.use_area_chairs:
            readers=[self.get_senior_area_chairs_id()] if self.use_senior_area_chairs else []
            self.__create_group(group_id=self.get_area_chairs_id(), group_owner_id=self.id, members=emails, additional_readers=readers)

            return self.__set_area_chair_page()
        else:
            raise openreview.OpenReviewException('Conference "has_area_chairs" setting is disabled')

    def set_secondary_area_chairs(self):
        if self.use_secondary_area_chairs:
            self.__create_group(self.get_secondary_area_chairs_id(), self.id)
        else:
            raise openreview.OpenReviewException('Conference "has_secondary_area_chairs" setting is disabled')

    def set_senior_area_chair_recruitment_groups(self):
        if self.use_senior_area_chairs:
            parent_group_id = self.get_senior_area_chairs_id()
            parent_group_declined_id = parent_group_id + '/Declined'
            parent_group_invited_id = parent_group_id + '/Invited'
            parent_group_accepted_id = parent_group_id

            pcs_id = self.get_program_chairs_id()
            # parent_group_accepted_group
            self.__create_group(parent_group_accepted_id, pcs_id)
            # parent_group_declined_group
            self.__create_group(parent_group_declined_id, pcs_id, exclude_self_reader=True)
            # parent_group_invited_group
            self.__create_group(parent_group_invited_id, pcs_id, exclude_self_reader=True)
        else:
            raise openreview.OpenReviewException('Conference "has_senior_area_chairs" setting is disabled')


    def set_area_chair_recruitment_groups(self):
        if self.use_area_chairs:
            parent_group_id = self.get_area_chairs_id()
            parent_group_declined_id = parent_group_id + '/Declined'
            parent_group_invited_id = parent_group_id + '/Invited'
            parent_group_accepted_id = parent_group_id

            pcs_id = self.get_program_chairs_id()
            # parent_group_accepted_group
            self.__create_group(parent_group_accepted_id, pcs_id)
            # parent_group_declined_group
            self.__create_group(parent_group_declined_id, pcs_id, exclude_self_reader=True)
            # parent_group_invited_group
            self.__create_group(parent_group_invited_id, pcs_id, exclude_self_reader=True)
        else:
            raise openreview.OpenReviewException('Conference "has_area_chairs" setting is disabled')

    def set_ethics_reviewer_recruitment_groups(self):
        parent_group_id = self.get_ethics_reviewers_id()
        parent_group_declined_id = parent_group_id + '/Declined'
        parent_group_invited_id = parent_group_id + '/Invited'

        pcs_id = self.get_ethics_chairs_id()
        self.set_ethics_reviewers()
        self.__create_group(parent_group_declined_id, pcs_id, exclude_self_reader=True)
        self.__create_group(parent_group_invited_id, pcs_id, exclude_self_reader=True) 

    def set_ethics_chair_recruitment_groups(self):
        parent_group_id = self.get_ethics_chairs_id()
        parent_group_declined_id = parent_group_id + '/Declined'
        parent_group_invited_id = parent_group_id + '/Invited'

        pcs_id = self.get_program_chairs_id()
        self.set_ethics_chairs()
        self.__create_group(parent_group_declined_id, pcs_id, exclude_self_reader=True)
        self.__create_group(parent_group_invited_id, pcs_id, exclude_self_reader=True)                

    def set_reviewer_recruitment_groups(self):
        parent_group_id = self.get_reviewers_id()
        parent_group_declined_id = parent_group_id + '/Declined'
        parent_group_invited_id = parent_group_id + '/Invited'

        pcs_id = self.get_program_chairs_id()
        self.__create_group(parent_group_id, self.get_area_chairs_id() if self.use_area_chairs else self.id)
        self.__create_group(parent_group_declined_id, pcs_id, exclude_self_reader=True)
        self.__create_group(parent_group_invited_id, pcs_id, exclude_self_reader=True)

    def set_external_reviewer_recruitment_groups(self, name='External_Reviewers', create_paper_groups=False):

        if name == self.reviewers_name:
            raise openreview.OpenReviewException(f'Can not use {name} as external reviewer name')

        parent_group_id = self.get_committee_id(name=name)
        parent_group_invited_id = parent_group_id + '/Invited'

        self.__create_group(parent_group_id, self.id)
        self.__create_group(parent_group_invited_id, self.id, exclude_self_reader=True)

        ## create groups per submissions
        def create_paper_group(submission):
            paper_group_id = self.get_committee_id(name=name, number=submission.number)
            self.client.post_group(openreview.Group(
                id=paper_group_id,
                readers=[self.id, paper_group_id],
                writers=[self.id],
                signatures=[self.id],
                signatories=[self.id],
                members=[]
            ))
            paper_invited_group_id = self.get_committee_id(name=name + '/Invited', number=submission.number)
            return self.client.post_group(openreview.Group(
                id=paper_invited_group_id,
                readers=[self.id],
                writers=[self.id],
                signatures=[self.id],
                signatories=[self.id],
                members=[]
            ))

        if create_paper_groups:
            tools.concurrent_requests(create_paper_group, self.get_submissions(), desc='Creating paper groups')

    def set_reviewers(self, emails = []):
        readers = []
        if self.use_senior_area_chairs:
            readers.append(self.get_senior_area_chairs_id())
        if self.use_area_chairs:
            readers.append(self.get_area_chairs_id())

        self.__create_group(
            group_id = self.get_reviewers_id(),
            group_owner_id = self.get_area_chairs_id() if self.use_area_chairs else self.id,
            members = emails,
            additional_readers = readers)

        return self.__set_reviewer_page()

    def set_ethics_reviewers(self, emails = []):
        readers = [self.id, self.get_ethics_chairs_id()]

        ethics_reviewer_group = self.__create_group(
            group_id = self.get_ethics_reviewers_id(),
            group_owner_id = self.get_ethics_chairs_id(),
            members = emails,
            additional_readers = readers)

        return self.webfield_builder.set_ethics_reviewer_page(self, ethics_reviewer_group)        

    def set_ethics_chairs(self, emails = []):
        readers = [self.id, self.get_ethics_chairs_id()]

        ethics_reviewer_group = self.__create_group(
            group_id = self.get_ethics_chairs_id(),
            group_owner_id = self.id,
            members = emails,
            additional_readers = readers)

        return self.webfield_builder.set_ethics_chairs_page(self, ethics_reviewer_group)        


    def set_authors(self):
        # Creating venue level authors group
        authors_group = self.__create_group(self.get_authors_id(), self.id, additional_readers=['everyone'])

        # Creating venue level accepted authors group
        self.__create_group(self.get_accepted_authors_id(), self.id)

        return self.webfield_builder.set_author_page(self, authors_group)

    def set_impersonators(self, group_ids = []):
        # Only super user can call this
        conference_group = tools.get_group(self.client, self.id)
        conference_group.impersonators = group_ids
        self.client.post_group(conference_group)

    @deprecated(version='1.0.24', reason="Use setup_committeee_matching() instead")
    def setup_matching(self, committee_id=None, affinity_score_file=None, tpms_score_file=None, elmo_score_file=None, build_conflicts=None, alternate_matching_group=None):
        if committee_id is None:
            committee_id=self.get_reviewers_id()
        if self.use_senior_area_chairs and committee_id == self.get_senior_area_chairs_id() and not alternate_matching_group:
            alternate_matching_group = self.get_area_chairs_id()
        conference_matching = matching.Matching(self, self.client.get_group(committee_id), alternate_matching_group)

        return conference_matching.setup(affinity_score_file, tpms_score_file, elmo_score_file, build_conflicts)

    def setup_committee_matching(self, committee_id=None, compute_affinity_scores=False, compute_conflicts=False, alternate_matching_group=None):
        if committee_id is None:
            committee_id=self.get_reviewers_id()
        if self.use_senior_area_chairs and committee_id == self.get_senior_area_chairs_id() and not alternate_matching_group:
            alternate_matching_group = self.get_area_chairs_id()
        conference_matching = matching.Matching(self, self.client.get_group(committee_id), alternate_matching_group)

        return conference_matching.setup(compute_affinity_scores=compute_affinity_scores, build_conflicts=compute_conflicts)

    def set_matching_conflicts(self, profile_id, build_conflicts=True):
        # Re-generates conflicts for a single reviewer
        committee_id=self.get_reviewers_id()
        conference_matching = matching.Matching(self, self.client.get_group(committee_id))
        return conference_matching.append_note_conflicts(profile_id, build_conflicts)

    def set_matching_alternate_conflicts(self, committee_id, source_committee_id, source_assignment_title, conflict_label):
        conference_matching = matching.Matching(self, self.client.get_group(source_committee_id), committee_id)
        conference_matching.compute_alternate_conflicts(source_assignment_title, conflict_label)


    def setup_assignment_recruitment(self, committee_id, hash_seed, due_date, assignment_title=None, invitation_labels={}, email_template=None):

        conference_matching = matching.Matching(self, self.client.get_group(committee_id))
        return conference_matching.setup_invite_assignment(hash_seed, assignment_title, due_date, invitation_labels=invitation_labels, email_template=email_template)

    def set_assignment(self, user, number, is_area_chair = False):

        if self.legacy_anonids:
            if is_area_chair:
                return tools.add_assignment(self.client,
                number,
                self.get_id(),
                user,
                parent_label = 'Area_Chairs',
                individual_label = 'Area_Chair')
            else:
                common_readers_writers = [
                    self.get_id(),
                    self.get_program_chairs_id()
                ]
                if self.use_area_chairs:
                    common_readers_writers.append(self.get_area_chairs_id(number = number))

                result = tools.add_assignment(
                    self.client,
                    number,
                    self.get_id(),
                    user,
                    parent_label = self.reviewers_name,
                    individual_label = 'AnonReviewer',
                    individual_group_params = {
                        'readers': common_readers_writers,
                        'writers': common_readers_writers
                    },
                    parent_group_params = {
                        'readers': common_readers_writers,
                        'writers': common_readers_writers
                    },
                    use_profile = True
                )
                return result

        if is_area_chair:
            self.client.add_members_to_group(self.get_area_chairs_id(number=number), user)
        else:
            self.client.add_members_to_group(self.get_reviewers_id(number=number), user)

    def set_assignments(self, assignment_title, committee_id, enable_reviewer_reassignment=False, overwrite=False):

        match_group = self.client.get_group(committee_id)
        conference_matching = matching.Matching(self, match_group)
        return conference_matching.deploy(assignment_title, overwrite, enable_reviewer_reassignment)

    def set_invite_assignments(self, assignment_title, committee_id, enable_reviewer_reassignment=False, email_template=None):

        match_group = self.client.get_group(committee_id)
        conference_matching = matching.Matching(self, match_group)
        return conference_matching.deploy_invite(assignment_title, enable_reviewer_reassignment, email_template)

    def set_default_load(self, default_load, reviewers_name = 'Reviewers'):
        self.default_reviewer_load[reviewers_name] = default_load

    def recruit_reviewers(self,
        invitees = [],
        title = None,
        message = None,
        reviewers_name = 'Reviewers',
        remind = False,
        invitee_names = [],
        retry_declined=False,
        contact_info = 'info@openreview.net',
        reduced_load_on_decline=None,
        default_load=0,
        allow_overlap_official_committee=False):

        pcs_id = self.get_program_chairs_id()
        reviewers_id = self.id + '/' + reviewers_name
        reviewers_declined_id = reviewers_id + '/Declined'
        reviewers_invited_id = reviewers_id + '/Invited'
        reviewers_accepted_id = reviewers_id
        hash_seed = '1234'
        invitees = [e.lower() if '@' in e else e for e in invitees]
        self.set_default_load(default_load, reviewers_name)

        reviewers_accepted_group = self.__create_group(reviewers_accepted_id, pcs_id)
        reviewers_declined_group = self.__create_group(reviewers_declined_id, pcs_id)
        reviewers_invited_group = self.__create_group(reviewers_invited_id, pcs_id)

        official_committee_roles=self.get_committee_names()
        committee_roles = official_committee_roles if (reviewers_name in official_committee_roles and not allow_overlap_official_committee) else [reviewers_name]
        recruitment_status = {
            'invited': [],
            'reminded': [],
            'already_invited': {},
            'already_member': {},
            'errors': {}
        }

        options = {
            'reviewers_name': reviewers_name,
            'reviewers_accepted_id': reviewers_accepted_id,
            'reviewers_invited_id': reviewers_invited_id,
            'reviewers_declined_id': reviewers_declined_id,
            'hash_seed': hash_seed,
            'reduced_load_id': None,
            'allow_overlap_official_committee': allow_overlap_official_committee
        }
        if reduced_load_on_decline:
            options['reduced_load_on_decline'] = reduced_load_on_decline
            options['reduced_load_id'] = self.get_invitation_id('Reduced_Load', prefix = reviewers_id)
            invitation = self.invitation_builder.set_reviewer_reduced_load_invitation(self, options)
            invitation = self.webfield_builder.set_reduced_load_page(self.id, invitation, self.get_homepage_options())

        invitation = self.invitation_builder.set_reviewer_recruiter_invitation(self, options)
        invitation = self.webfield_builder.set_recruit_page(self.id, invitation, self.get_homepage_options(), options['reduced_load_id'])

        role = reviewers_name.replace('_', ' ')
        role = role[:-1] if role.endswith('s') else role
        recruit_message = f'''Dear {{{{fullname}}}},

You have been nominated by the program chair committee of {self.get_short_name()} to serve as {role}. As a respected researcher in the area, we hope you will accept and help us make {self.get_short_name()} a success.

You are also welcome to submit papers, so please also consider submitting to {self.get_short_name()}.

We will be using OpenReview.net with the intention of have an engaging reviewing process inclusive of the whole community.

To ACCEPT the invitation, please click on the following link:

{{{{accept_url}}}}

To DECLINE the invitation, please click on the following link:

{{{{decline_url}}}}

Please answer within 10 days.

If you accept, please make sure that your OpenReview account is updated and lists all the emails you are using.  Visit http://openreview.net/profile after logging in.

If you have any questions, please contact {{{{contact_info}}}}.

Cheers!

Program Chairs

        '''

        recruit_message_subj = f'[{self.get_short_name()}]: Invitation to serve as {role.title()}'

        if title:
            recruit_message_subj = title

        if message:
            recruit_message = message

        if remind:
            invited_reviewers = reviewers_invited_group.members
            print('Sending reminders for recruitment invitations')
            for reviewer_id in tqdm(invited_reviewers, desc='remind_reviewers'):
                memberships = [g.id for g in self.client.get_groups(member=reviewer_id, regex=reviewers_id)] if tools.get_group(self.client, reviewer_id) else []
                if reviewers_id not in memberships and reviewers_declined_id not in memberships:
                    reviewer_name = 'invitee'
                    if reviewer_id.startswith('~') :
                        reviewer_name = None
                    elif (reviewer_id in invitees) and invitee_names:
                        reviewer_name = invitee_names[invitees.index(reviewer_id)]
                    try:
                        tools.recruit_reviewer(self.client, reviewer_id, reviewer_name,
                            hash_seed,
                            invitation.id,
                            recruit_message,
                            'Reminder: ' + recruit_message_subj,
                            reviewers_invited_id,
                            contact_info = contact_info,
                            verbose = False)
                        recruitment_status['reminded'].append(reviewer_id)
                    except Exception as e:
                        self.client.remove_members_from_group(reviewers_invited_group, reviewer_id)
                        if repr(e) not in recruitment_status['errors']:
                            recruitment_status['errors'][repr(e)] = []
                        recruitment_status['errors'][repr(e)].append(reviewer_id)

        if retry_declined:
            declined_reviewers = reviewers_declined_group.members
            print('Sending retry to declined reviewers')
            for reviewer_id in tqdm(declined_reviewers, desc='retry_declined'):
                memberships = [g.id for g in self.client.get_groups(member=reviewer_id, regex=reviewers_id)] if tools.get_group(self.client, reviewer_id) else []
                if reviewers_id not in memberships:
                    reviewer_name = 'invitee'
                    if reviewer_id.startswith('~'):
                        reviewer_name = None
                    elif (reviewer_id in invitees) and invitee_names:
                        reviewer_name = invitee_names[invitees.index(reviewer_id)]
                    try:
                        tools.recruit_reviewer(self.client, reviewer_id, reviewer_name,
                            hash_seed,
                            invitation.id,
                            recruit_message,
                            recruit_message_subj,
                            reviewers_invited_id,
                            contact_info = contact_info,
                            verbose = False)
                    except Exception as e:
                        self.client.remove_members_from_group(reviewers_invited_group, reviewer_id)
                        if repr(e) not in recruitment_status['errors']:
                            recruitment_status['errors'][repr(e)] = []
                        recruitment_status['errors'][repr(e)].append(reviewer_id)

        print('Sending recruitment invitations')
        for index, email in enumerate(tqdm(invitees, desc='send_invitations')):
            memberships = [g.id for g in self.client.get_groups(member=email, regex=self.id)] if tools.get_group(self.client, email) else []
            invited_roles = [f'{self.id}/{role}/Invited' for role in committee_roles]
            member_roles = [f'{self.id}/{role}' for role in committee_roles]

            invited_group_ids=list(set(invited_roles) & set(memberships))
            member_group_ids=list(set(member_roles) & set(memberships))

            if invited_group_ids:
                invited_group_id=invited_group_ids[0]
                if invited_group_id not in recruitment_status['already_invited']:
                    recruitment_status['already_invited'][invited_group_id] = []
                recruitment_status['already_invited'][invited_group_id].append(email)
            elif member_group_ids:
                member_group_id = member_group_ids[0]
                if member_group_id not in recruitment_status['already_member']:
                    recruitment_status['already_member'][member_group_id] = []
                recruitment_status['already_member'][member_group_id].append(email)
            else:
                name = invitee_names[index] if (invitee_names and index < len(invitee_names)) else None
                if not name and not email.startswith('~'):
                    name = 'invitee'
                try:
                    tools.recruit_reviewer(self.client, email, name,
                        hash_seed,
                        invitation.id,
                        recruit_message,
                        recruit_message_subj,
                        reviewers_invited_id,
                        contact_info = contact_info,
                        verbose = False)
                    recruitment_status['invited'].append(email)
                except Exception as e:
                    self.client.remove_members_from_group(reviewers_invited_group, email)
                    if repr(e) not in recruitment_status['errors']:
                        recruitment_status['errors'][repr(e)] = []
                    recruitment_status['errors'][repr(e)].append(email)
        return recruitment_status

    ## temporary function, move to somewhere else
    def remind_registration_stage(self, subject, message, committee_id, invitation_id):

        reviewers = self.client.get_group(committee_id).members
        profiles_by_email = self.client.search_profiles(confirmedEmails=[m for m in reviewers if '@' in m])
        confirmations = {c.tauthor: c for c in self.client.get_all_notes(invitation=invitation_id)}
        print('reviewers:', len(reviewers))
        print('profiles:', len(profiles_by_email))
        print('confirmations', len(confirmations))

        reminders=[]
        confirmed=[]
        for reviewer in reviewers:
            if reviewer in profiles_by_email:
                emails = profiles_by_email[reviewer].content['emails']
                found = False
                for email in emails:
                    if email in confirmations:
                        found = True
                if not found:
                    reminders.append(reviewer)
                else:
                    confirmed.append(reviewer)
            else:
                reminders.append(reviewer)

        self.client.post_message(subject, reminders, message)
        return reminders


    def set_homepage_decisions(self, invitation_name = 'Decision', decision_heading_map = None):
        home_group = self.client.get_group(self.id)
        options = {}
        options['decision_heading_map'] = decision_heading_map

        self.webfield_builder.set_home_page(conference = self, group = home_group, layout = 'decisions', options = options)

    def get_submissions_attachments(self, field_name='pdf', field_type='pdf', folder_path='./pdfs', accepted=False):
        print('Loading submissions...')
        submissions = list(self.get_submissions(accepted))
        pbar = tqdm(total=len(submissions), desc='Downloading files...')

        if not os.path.exists(folder_path):
            os.makedirs(folder_path)

        def get_attachment_file(submission):
            pbar.update(1)
            if field_name in submission.content:
                paper_number = submission.number
                try:
                    with open('{folder_path}/Paper{number}.{field_type}'.format(folder_path=folder_path, number=paper_number, field_type=field_type), 'wb') as f:
                        f.write(self.client.get_attachment(submission.id, field_name))
                except Exception as e:
                    print('Error during attachment download for paper number {}, error: {}'.format(submission.number, e))
                return True
            return None

        futures = []
        with concurrent.futures.ThreadPoolExecutor() as executor:
            # Start the load operations and mark each future with its URL
            for submission in submissions:
                futures.append(executor.submit(get_attachment_file, submission))
        pbar.close()

        for future in futures:
            result = future.result()

    def post_decision_stage(self, reveal_all_authors=False, reveal_authors_accepted=False, decision_heading_map=None, submission_readers=None):
        submissions = self.get_submissions(details='original')
        decisions_by_forum = {n.forum: n for n in self.client.get_all_notes(invitation = self.get_invitation_id(self.decision_stage.name, '.*'))}

        def is_release_authors(is_note_accepted):
            return reveal_all_authors or (reveal_authors_accepted and is_note_accepted)

        if submission_readers:
            self.submission_stage.readers = submission_readers

        for submission in tqdm(submissions):
            decision_note = decisions_by_forum.get(submission.forum, None)
            note_accepted = decision_note and 'Accept' in decision_note.content['decision']
            submission.readers = self.submission_stage.get_readers(self, submission.number, decision_note)
            #double-blind
            if self.submission_stage.double_blind:
                release_authors = is_release_authors(note_accepted)
                submission.content = {}
                if not release_authors:
                    submission.content['authors'] = ['Anonymous']
                    submission.content['authorids'] = [self.get_authors_id(number=submission.number)]

                bibtex = tools.generate_bibtex(
                        openreview.Note.from_json(submission.details['original']),
                        venue_fullname=self.name,
                        year=str(self.year),
                        url_forum=submission.forum,
                        paper_status = 'accepted' if note_accepted else 'rejected',
                        anonymous=(not release_authors)
                    )
            #single-blind
            else:
                bibtex = tools.generate_bibtex(
                    submission,
                    venue_fullname=self.name,
                    year=str(self.year),
                    url_forum=submission.forum,
                    paper_status = 'accepted' if note_accepted else 'rejected',
                    anonymous=False
                )

            self.client.post_note(submission)

            #add venue_id, venue and bibtex revision to all notes
            venue = self.short_name
            decision_option = decision_note.content['decision'] if decision_note else ''
            venue = tools.decision_to_venue(venue, decision_option)

            original_id = submission.id if not self.submission_stage.double_blind else submission.details['original']['id']
            revision_note = self.client.post_note(openreview.Note(
                invitation = f'{self.support_user}/-/{self.venue_revision_name}',
                forum = original_id,
                referent = original_id,
                readers = ['everyone'],
                writers = [self.id],
                signatures = [self.id],
                content = {
                    'venue': venue,
                    'venueid': self.id,
                    '_bibtex': bibtex
                }
            ))

        venue_heading_map = {}
        if decision_heading_map:
            for decision, tab_name in decision_heading_map.items():
                venue_heading_map[tools.decision_to_venue(self.short_name, decision)] = tab_name
        
        if venue_heading_map:
            self.set_homepage_decisions(decision_heading_map=venue_heading_map)
        self.client.remove_members_from_group('active_venues', self.id)

        # expire recruitment invitations
        self.expire_recruitment_invitations()

    def send_decision_notifications(self, decision_options, messages):
        decision_notes = self.client.get_all_notes(
            invitation=self.get_invitation_id(self.decision_stage.name, '.*'),
        )
        paper_notes = {n.forum: n for n in self.get_submissions()}

        def send_notification(note):
            paper_note = paper_notes[note.forum]
            message = messages[note.content['decision']]
            subject = "[{SHORT_NAME}] Decision notification for your submission {submission_number}: {submission_title}".format(
                SHORT_NAME=self.get_short_name(),
                submission_number=paper_note.number,
                submission_title=paper_note.content['title']
            )
            final_message = message.replace("{{submission_title}}", paper_note.content['title'])
            final_message = final_message.replace("{{forum_url}}", f'https://openreview.net/forum?id={paper_note.id}')
            self.client.post_message(subject, recipients=paper_note.content['authorids'], message=final_message)

        tools.concurrent_requests(send_notification, decision_notes)

    def post_decisions(self, decisions_file):
        decisions_data = list(csv.reader(StringIO(decisions_file.decode()), delimiter=","))
        decision_notes = {
            n.forum: n for n in self.client.get_all_notes(
                invitation=self.get_invitation_id(self.decision_stage.name, '.*')
            )}
        paper_notes = {n.forum: n for n in self.get_submissions()}
        forum_note = self.client.get_note(self.request_form_id)

        def post_decision(paper_decision):
            if len(paper_decision) < 2:
                raise OpenReviewException(
                    "Not enough values provided in the decision file. Expected values are: paper_id, decision, comment")
            if len(paper_decision) > 3:
                raise OpenReviewException(
                    "Too many values provided in the decision file. Expected values are: paper_id, decision, comment"
                )
            if len(paper_decision) == 3:
                paper_id, decision, comment = paper_decision
            else:
                paper_id, decision = paper_decision
                comment = ''

            print(f"Posting Decision {decision} for Paper {paper_id}")
            paper_note = paper_notes.get(paper_id, None)
            if not paper_note:
                raise OpenReviewException(
                    f"Paper with ID: {paper_id} not found. Please check the submitted paperIDs."
                )

            paper_decision_note = decision_notes.get(paper_id, None)
            if paper_decision_note:
                paper_decision_note.readers = self.decision_stage.get_readers(conference=self, number=paper_note.number)
                paper_decision_note.nonreaders = self.decision_stage.get_nonreaders(conference=self, number=paper_note.number)
                paper_decision_note.content = {
                    'title': 'Paper Decision',
                    'decision': decision.strip(),
                    'comment': comment,
                }
            else:
                paper_decision_note = openreview.Note(
                    invitation=self.get_invitation_id(name=self.decision_stage.name, number=paper_note.number),
                    writers=[self.get_program_chairs_id()],
                    readers=self.decision_stage.get_readers(conference=self, number=paper_note.number),
                    nonreaders=self.decision_stage.get_nonreaders(conference=self, number=paper_note.number),
                    signatures=[self.get_program_chairs_id()],
                    content={
                        'title': 'Paper Decision',
                        'decision': decision.strip(),
                        'comment': comment,
                    },
                    forum=paper_note.forum,
                    replyto=paper_note.forum
                )
            self.client.post_note(paper_decision_note)
            print(f"Decision posted for Paper {paper_id}")

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
                    errors[futures_param_mapping[future]] = e.args[0] if isinstance(e, OpenReviewException) else repr(e)

            gathering_responses.close()

        error_status = ''
        if errors:
            error_status = f'''
```python
{json.dumps(errors, indent=2)}
```
'''
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
                'error': error_status
            }
        )

        self.client.post_note(status_note)

    def expire_recruitment_invitations(self):
        recruitment_invitations = self.client.get_invitations(regex=self.get_invitation_id('Recruit_*'))
        recruitment_invitation_ids = [inv.id for inv in recruitment_invitations]
        tools.concurrent_requests(self.expire_invitation, recruitment_invitation_ids)


class SubmissionStage(object):

    class Readers(Enum):
        EVERYONE = 0
        SENIOR_AREA_CHAIRS = 1
        SENIOR_AREA_CHAIRS_ASSIGNED = 2
        AREA_CHAIRS = 3
        AREA_CHAIRS_ASSIGNED = 4
        REVIEWERS = 5
        REVIEWERS_ASSIGNED = 6
        EVERYONE_BUT_REJECTED = 7

    def __init__(
            self,
            name='Submission',
            start_date=None,
            due_date=None,
            second_due_date=None,
            readers=[],
            double_blind=False,
            additional_fields={},
            remove_fields=[],
            subject_areas=[],
            email_pcs=False,
            create_groups=False,
            # We need to assume the Official Review super invitation is already created and active
            create_review_invitation=False,
            withdraw_submission_exp_date=None,
            withdrawn_submission_public=False,
            withdrawn_submission_reveal_authors=False,
            email_pcs_on_withdraw=False,
            desk_rejected_submission_public=False,
            desk_rejected_submission_reveal_authors=False,
            email_pcs_on_desk_reject=True,
            author_names_revealed=False,
            papers_released=False
        ):

        self.start_date = start_date
        self.due_date = due_date
        self.second_due_date = second_due_date
        self.name = name
        self.readers = readers
        self.double_blind = double_blind
        self.additional_fields = additional_fields
        self.remove_fields = remove_fields
        self.subject_areas = subject_areas
        self.email_pcs = email_pcs
        self.create_groups = create_groups
        self.create_review_invitation = create_review_invitation
        self.withdraw_submission_exp_date = withdraw_submission_exp_date
        self.withdrawn_submission_public = withdrawn_submission_public
        self.withdrawn_submission_reveal_authors = withdrawn_submission_reveal_authors
        self.email_pcs_on_withdraw = email_pcs_on_withdraw
        self.desk_rejected_submission_public = desk_rejected_submission_public
        self.desk_rejected_submission_reveal_authors = desk_rejected_submission_reveal_authors
        self.email_pcs_on_desk_reject = email_pcs_on_desk_reject
        self.author_names_revealed = author_names_revealed
        self.papers_released = papers_released
        self.public = self.Readers.EVERYONE in self.readers

    def get_readers(self, conference, number, decision_note=None):

        if self.Readers.EVERYONE in self.readers:
            return ['everyone']

        submission_readers=[conference.get_id()]

        if self.Readers.EVERYONE_BUT_REJECTED in self.readers:
            hide = not decision_note or decision_note and 'Reject' in decision_note.content['decision']
            if hide:
                if conference.use_senior_area_chairs:
                    submission_readers.append(conference.get_senior_area_chairs_id(number=number))
                if conference.use_area_chairs:
                    submission_readers.append(conference.get_area_chairs_id(number=number))
                submission_readers.append(conference.get_reviewers_id(number=number))
                submission_readers.append(conference.get_authors_id(number=number))
                return submission_readers
            else:
                return ['everyone']

        if self.Readers.SENIOR_AREA_CHAIRS in self.readers and conference.use_senior_area_chairs:
            submission_readers.append(conference.get_senior_area_chairs_id())

        if self.Readers.SENIOR_AREA_CHAIRS_ASSIGNED in self.readers and conference.use_senior_area_chairs:
            submission_readers.append(conference.get_senior_area_chairs_id(number=number))

        if self.Readers.AREA_CHAIRS in self.readers and conference.use_area_chairs:
            submission_readers.append(conference.get_area_chairs_id())

        if self.Readers.AREA_CHAIRS_ASSIGNED in self.readers and conference.use_area_chairs:
            submission_readers.append(conference.get_area_chairs_id(number=number))

        if self.Readers.REVIEWERS in self.readers:
            submission_readers.append(conference.get_reviewers_id())

        if self.Readers.REVIEWERS_ASSIGNED in self.readers:
            submission_readers.append(conference.get_reviewers_id(number=number))

        if conference.ethics_review_stage and number in conference.ethics_review_stage.submission_numbers:
            if conference.use_ethics_chairs:
                submission_readers.append(conference.get_ethics_chairs_id())
            if conference.use_ethics_reviewers:
                submission_readers.append(conference.get_ethics_reviewers_id(number=number))            

        submission_readers.append(conference.get_authors_id(number=number))
        return submission_readers

    def get_invitation_readers(self, conference, under_submission):
        # Rolling review should be release right away
        if self.create_groups:
            return {'values': ['everyone']}

        if under_submission or self.double_blind:
            has_authorids = 'authorids' in self.get_content()
            readers = {
                'values-copied': [
                    conference.get_id()
                ]
            }

            if has_authorids:
                readers['values-copied'].append('{content.authorids}')
            readers['values-copied'].append('{signatures}')

            return readers

        return {
            'values-regex': '.*'
        }

    def get_invitation_writers(self, conference):

        has_authorids = 'authorids' in self.get_content()
        writers = {
            'values-copied': [
                conference.get_id()
            ]
        }

        if has_authorids:
            writers['values-copied'].append('{content.authorids}')
        writers['values-copied'].append('{signatures}')

        return writers


    def get_submission_id(self, conference):
        return conference.get_invitation_id(self.name)

    def get_blind_submission_id(self, conference):
        name = self.name
        if self.double_blind:
            name = 'Blind_' + name
        return conference.get_invitation_id(name)

    def get_withdrawn_submission_id(self, conference):
        return conference.get_invitation_id(f'Withdrawn_{self.name}')

    def get_desk_rejected_submission_id(self, conference):
        return conference.get_invitation_id(f'Desk_Rejected_{self.name}')

    def get_content(self):
        content = invitations.submission.copy()

        if self.subject_areas:
            content['subject_areas'] = {
                'order' : 5,
                'description' : "Select or type subject area",
                'values-dropdown': self.subject_areas,
                'required': True
            }

        for field in self.remove_fields:
            del content[field]

        for order, key in enumerate(self.additional_fields, start=10):
            value = self.additional_fields[key]
            value['order'] = order
            content[key] = value

        if self.second_due_date and 'pdf' in content:
            content['pdf']['required'] = False

        return content

    def is_under_submission(self):
        return self.due_date is None or datetime.datetime.utcnow() < self.due_date


class ExpertiseSelectionStage(object):

    def __init__(self, start_date = None, due_date = None):
        self.start_date = start_date
        self.due_date = due_date
        self.name = 'Expertise_Selection'

class BidStage(object):

    def __init__(self, committee_id, start_date=None, due_date=None, request_count=50, score_ids=[], instructions=False, allow_conflicts_bids=False):
        self.committee_id=committee_id
        self.start_date=start_date
        self.due_date=due_date
        self.name='Bid'
        self.request_count=request_count
        self.score_ids=score_ids
        self.instructions=instructions
        self.allow_conflicts_bids=allow_conflicts_bids

    def get_invitation_readers(self, conference):
        readers = [conference.get_id()]
        if self.committee_id == conference.get_reviewers_id():
            if conference.use_senior_area_chairs:
                readers.append(conference.get_senior_area_chairs_id())
            if conference.use_area_chairs:
                readers.append(conference.get_area_chairs_id())
        if self.committee_id == conference.get_area_chairs_id():
            if conference.use_senior_area_chairs:
                readers.append(conference.get_senior_area_chairs_id())
        readers.append(self.committee_id)
        return readers

    def get_readers(self, conference):
        values_copied = [conference.get_id()]
        if self.committee_id == conference.get_reviewers_id():
            if conference.use_senior_area_chairs:
                values_copied.append(conference.get_senior_area_chairs_id())
            if conference.use_area_chairs:
                values_copied.append(conference.get_area_chairs_id())
        if self.committee_id == conference.get_area_chairs_id():
            if conference.use_senior_area_chairs:
                values_copied.append(conference.get_senior_area_chairs_id())
        values_copied.append('{signatures}')
        return values_copied

    def get_bid_options(self):
        options = ['Very High', 'High', 'Neutral', 'Low', 'Very Low']
        if self.allow_conflicts_bids:
            options.append('Conflict')
        return options

class SubmissionRevisionStage():

    def __init__(self, name='Revision', start_date=None, due_date=None, additional_fields={}, remove_fields=[], only_accepted=False, multiReply=None, allow_author_reorder=False):
        self.name = name
        self.start_date = start_date
        self.due_date = due_date
        self.additional_fields = additional_fields
        self.remove_fields = remove_fields
        self.only_accepted = only_accepted
        self.multiReply=multiReply
        self.allow_author_reorder=allow_author_reorder

class ReviewStage(object):

    class Readers(Enum):
        REVIEWERS = 0
        REVIEWERS_ASSIGNED = 1
        REVIEWERS_SUBMITTED = 2
        REVIEWER_SIGNATURE = 3

    def __init__(self,
        start_date = None,
        due_date = None,
        name = None,
        allow_de_anonymization = False,
        public = False,
        release_to_authors = False,
        release_to_reviewers = Readers.REVIEWER_SIGNATURE,
        email_pcs = False,
        additional_fields = {},
        remove_fields = [],
        rating_field_name = None,
        confidence_field_name = None,
        process_path = None
    ):

        self.start_date = start_date
        self.due_date = due_date
        self.name = 'Official_Review'
        if name:
            self.name = name
        self.allow_de_anonymization = allow_de_anonymization
        self.public = public
        self.release_to_authors = release_to_authors
        self.release_to_reviewers = release_to_reviewers
        self.email_pcs = email_pcs
        self.additional_fields = additional_fields
        self.remove_fields = remove_fields
        self.rating_field_name = rating_field_name
        self.confidence_field_name = confidence_field_name
        self.process_path = process_path

    def _get_reviewer_readers(self, conference, number):
        if self.release_to_reviewers is ReviewStage.Readers.REVIEWERS:
            return conference.get_reviewers_id()
        if self.release_to_reviewers is ReviewStage.Readers.REVIEWERS_ASSIGNED:
            return conference.get_reviewers_id(number = number)
        if self.release_to_reviewers is ReviewStage.Readers.REVIEWERS_SUBMITTED:
            return conference.get_reviewers_id(number = number) + '/Submitted'
        if self.release_to_reviewers is ReviewStage.Readers.REVIEWER_SIGNATURE:
            return '{signatures}'
        raise openreview.OpenReviewException('Unrecognized readers option')

    def get_readers(self, conference, number):

        if self.public:
            return ['everyone']

        readers = [ conference.get_program_chairs_id()]

        if conference.use_senior_area_chairs:
            readers.append(conference.get_senior_area_chairs_id(number = number))

        if conference.use_area_chairs:
            readers.append(conference.get_area_chairs_id(number = number))

        readers.append(self._get_reviewer_readers(conference, number))

        if conference.ethics_review_stage and number in conference.ethics_review_stage.submission_numbers:
            if conference.use_ethics_chairs:
                readers.append(conference.get_ethics_chairs_id())
            if conference.use_ethics_reviewers:
                readers.append(conference.get_ethics_reviewers_id(number=number))  

        if self.release_to_authors:
            readers.append(conference.get_authors_id(number = number))

        return readers

    def get_nonreaders(self, conference, number):

        if self.public:
            return []

        if self.release_to_authors:
            return []

        return [conference.get_authors_id(number = number)]

    def get_signatures(self, conference, number):
        if self.allow_de_anonymization:
            return '~.*|' + conference.get_program_chairs_id()

        return conference.get_anon_reviewer_id(number=number, anon_id='.*') + '|' +  conference.get_program_chairs_id()


class EthicsReviewStage(object):

    class Readers(Enum):
        ALL_COMMITTEE = 0
        ALL_ASSIGNED_COMMITTEE = 1
        ASSIGNED_ETHICS_REVIEWERS = 2
        ETHICS_REVIEWER_SIGNATURE = 3

    def __init__(self,
        start_date = None,
        due_date = None,
        name = None,
        release_to_public = False,
        release_to_authors = False,
        release_to_reviewers = Readers.ETHICS_REVIEWER_SIGNATURE,
        additional_fields = {},
        remove_fields = [],
        submission_numbers = []
    ):

        self.start_date = start_date
        self.due_date = due_date
        self.name = name if name else 'Ethics_Review'
        self.release_to_public = release_to_public
        self.release_to_authors = release_to_authors
        self.release_to_reviewers = release_to_reviewers
        self.additional_fields = additional_fields
        self.remove_fields = remove_fields
        self.submission_numbers = submission_numbers

    def get_readers(self, conference, number):

        if self.release_to_public:
            return ['everyone']

        readers = [ conference.get_program_chairs_id()]

        if self.release_to_reviewers == self.Readers.ALL_COMMITTEE:
            if conference.use_senior_area_chairs:
                readers.append(conference.get_senior_area_chairs_id())

            if conference.use_area_chairs:
                readers.append(conference.get_area_chairs_id())

            readers.append(self.get_reviewers_id())

            if conference.use_ethics_chairs:
                readers.append(conference.get_ethics_chairs_id())

            readers.append(conference.get_ethics_reviewers_id())                

        if self.release_to_reviewers == self.Readers.ALL_ASSIGNED_COMMITTEE:
            if conference.use_senior_area_chairs:
                readers.append(conference.get_senior_area_chairs_id(number=number))

            if conference.use_area_chairs:
                readers.append(conference.get_area_chairs_id(number=number))

            readers.append(conference.get_reviewers_id(number=number))

            if conference.use_ethics_chairs:
                readers.append(conference.get_ethics_chairs_id())

            readers.append(self.get_ethics_reviewers_id(number=number)) 

        if self.release_to_reviewers == self.Readers.ASSIGNED_ETHICS_REVIEWERS:

            if conference.use_ethics_chairs:
                readers.append(conference.get_ethics_chairs_id())

            readers.append(self.get_ethics_reviewers_id(number=number)) 

        if self.release_to_reviewers == self.Readers.ETHICS_REVIEWER_SIGNATURE:

            if conference.use_ethics_chairs:
                readers.append(conference.get_ethics_chairs_id())

            readers.append('{signatures}')             


        if self.release_to_authors:
            readers.append(conference.get_authors_id(number = number))

        return readers

    def get_nonreaders(self, conference, number):

        if self.release_to_public:
            return []

        if self.release_to_authors:
            return []

        return [conference.get_authors_id(number = number)]

    def get_signatures(self, conference, number):
        return conference.get_anon_reviewer_id(number=number, anon_id='.*', name=conference.ethics_reviewers_name) + '|' +  conference.get_program_chairs_id()

class ReviewRebuttalStage(object):

    def __init__(self, start_date = None, due_date = None, name = 'Rebuttal', email_pcs = False, additional_fields = {}):
        self.start_date = start_date
        self.due_date = due_date
        self.name = name
        self.email_pcs = email_pcs
        self.additional_fields = additional_fields

class ReviewRevisionStage(object):

    def __init__(self, start_date = None, due_date = None, name = 'Review_Revision', additional_fields = {}, remove_fields = []):
        self.start_date = start_date
        self.due_date = due_date
        self.name = name
        self.additional_fields = additional_fields
        self.remove_fields = remove_fields

class ReviewRatingStage(object):

    class Readers(Enum):
        REVIEWERS = 0
        REVIEWERS_ASSIGNED = 1
        REVIEWERS_SUBMITTED = 2
        REVIEWER_SIGNATURE = 3
        NO_REVIEWERS = 4

    def __init__(self, start_date = None, due_date = None, name = 'Review_Rating', additional_fields = {}, remove_fields = [], public = False, release_to_reviewers = Readers.NO_REVIEWERS):
        self.start_date = start_date
        self.due_date = due_date
        self.name = name
        self.additional_fields = additional_fields
        self.remove_fields = remove_fields
        self.public = public
        self.release_to_reviewers = release_to_reviewers

    def _get_reviewer_readers(self, conference, number, review_signature):
        if self.release_to_reviewers is ReviewRatingStage.Readers.REVIEWERS:
            return conference.get_reviewers_id()
        if self.release_to_reviewers is ReviewRatingStage.Readers.REVIEWERS_ASSIGNED:
            return conference.get_reviewers_id(number = number)
        if self.release_to_reviewers is ReviewRatingStage.Readers.REVIEWERS_SUBMITTED:
            return conference.get_reviewers_id(number = number) + '/Submitted'
        if self.release_to_reviewers is ReviewRatingStage.Readers.REVIEWER_SIGNATURE:
            return review_signature
        raise openreview.OpenReviewException('Unrecognized readers option')

    def get_readers(self, conference, number, review_signature):

        if self.public:
            return ['everyone']

        readers = [ conference.get_program_chairs_id()]

        if conference.use_area_chairs:
            readers.append('{signatures}')

        if self.release_to_reviewers is not ReviewRatingStage.Readers.NO_REVIEWERS:
            readers.append(self._get_reviewer_readers(conference, number, review_signature))

        return readers

class CommentStage(object):

    def __init__(self,
    official_comment_name=None,
    start_date=None,
    end_date=None,
    allow_public_comments=False,
    anonymous=False,
    unsubmitted_reviewers=False,
    reader_selection=False,
    email_pcs=False,
    authors=False,
    only_accepted=False,
    check_mandatory_readers=False):
        self.official_comment_name = official_comment_name if official_comment_name else 'Official_Comment'
        self.public_name = 'Public_Comment'
        self.start_date = start_date
        self.end_date = end_date
        self.allow_public_comments = allow_public_comments
        self.anonymous = anonymous
        self.unsubmitted_reviewers = unsubmitted_reviewers
        self.reader_selection = reader_selection
        self.email_pcs = email_pcs
        self.authors = authors
        self.only_accepted=only_accepted
        self.check_mandatory_readers=check_mandatory_readers

    def get_readers(self, conference, number):
        readers = []
        default = []

        if self.allow_public_comments:
            readers.append('everyone')
        else:
            default = [conference.get_program_chairs_id()]

        readers.append(conference.get_program_chairs_id())

        if conference.use_senior_area_chairs:
            readers.append(conference.get_senior_area_chairs_id(number))

        if conference.use_area_chairs:
            readers.append(conference.get_area_chairs_id(number))

        if self.unsubmitted_reviewers:
            readers.append(conference.get_reviewers_id(number))
        else:
            readers.append(conference.get_reviewers_id(number) + '/Submitted')

        if self.reader_selection:
            readers.append(conference.get_anon_reviewer_id(number=number, anon_id='.*'))

        if self.authors:
            readers.append(conference.get_authors_id(number))

        return readers

    def get_signatures_regex(self, conference, number):

        committee = [conference.get_program_chairs_id()]

        if conference.use_senior_area_chairs:
            committee.append(conference.get_senior_area_chairs_id(number))

        if conference.use_area_chairs:
            committee.append(conference.get_anon_area_chair_id(number=number, anon_id='.*'))

        committee.append(conference.get_anon_reviewer_id(number=number, anon_id='.*'))

        if self.authors:
            committee.append(conference.get_authors_id(number))

        return '|'.join(committee)

    def get_invitees(self, conference, number):
        return conference.get_committee(number=number, with_authors=self.authors) + [conference.support_user]

class MetaReviewStage(object):

    class Readers(Enum):
        REVIEWERS = 0
        REVIEWERS_ASSIGNED = 1
        REVIEWERS_SUBMITTED = 2
        NO_REVIEWERS = 3

    def __init__(self, name='Meta_Review', start_date = None, due_date = None, public = False, release_to_authors = False, release_to_reviewers = Readers.NO_REVIEWERS, additional_fields = {}, remove_fields=[], process = None):

        self.start_date = start_date
        self.due_date = due_date
        self.name = name
        self.public = public
        self.release_to_authors = release_to_authors
        self.release_to_reviewers = release_to_reviewers
        self.additional_fields = additional_fields
        self.remove_fields = remove_fields
        self.process = None

    def _get_reviewer_readers(self, conference, number):
        if self.release_to_reviewers is MetaReviewStage.Readers.REVIEWERS:
            return conference.get_reviewers_id()
        if self.release_to_reviewers is MetaReviewStage.Readers.REVIEWERS_ASSIGNED:
            return conference.get_reviewers_id(number = number)
        if self.release_to_reviewers is MetaReviewStage.Readers.REVIEWERS_SUBMITTED:
            return conference.get_reviewers_id(number = number) + '/Submitted'
        raise openreview.OpenReviewException('Unrecognized readers option')

    def get_readers(self, conference, number):

        if self.public:
            return ['everyone']

        readers = []

        if conference.use_senior_area_chairs:
            readers.append(conference.get_senior_area_chairs_id(number = number))

        if conference.use_area_chairs:
            readers.append(conference.get_area_chairs_id(number = number))

        if self.release_to_authors:
            readers.append(conference.get_authors_id(number = number))

        if self.release_to_reviewers is not MetaReviewStage.Readers.NO_REVIEWERS:
            readers.append(self._get_reviewer_readers(conference, number))
        readers.append(conference.get_program_chairs_id())

        return readers

    def get_nonreaders(self, conference, number):

        if self.public:
            return []

        if self.release_to_authors:
            return []

        return [conference.get_authors_id(number = number)]

    def get_signatures_regex(self, conference, number):

        committee = [conference.get_program_chairs_id()]

        if conference.use_area_chairs:
            committee.append(conference.get_anon_area_chair_id(number=number, anon_id='.*'))

        return '|'.join(committee)

class DecisionStage(object):

    def __init__(self, options = None, start_date = None, due_date = None, public = False, release_to_authors = False, release_to_reviewers = False, release_to_area_chairs = False, email_authors = False, additional_fields = {}, decisions_file=None):
        if not options:
            options = ['Accept (Oral)', 'Accept (Poster)', 'Reject']
        self.options = options
        self.start_date = start_date
        self.due_date = due_date
        self.name = 'Decision'
        self.public = public
        self.release_to_authors = release_to_authors
        self.release_to_reviewers = release_to_reviewers
        self.release_to_area_chairs = release_to_area_chairs
        self.email_authors = email_authors
        self.additional_fields = additional_fields
        self.decisions_file = decisions_file

    def get_readers(self, conference, number):

        if self.public:
            return ['everyone']

        readers = [ conference.get_program_chairs_id()]
        if self.release_to_area_chairs and conference.use_senior_area_chairs:
            readers.append(conference.get_senior_area_chairs_id(number = number))

        if self.release_to_area_chairs and conference.use_area_chairs:
            readers.append(conference.get_area_chairs_id(number = number))

        if self.release_to_reviewers:
            readers.append(conference.get_reviewers_id(number = number))

        if self.release_to_authors:
            readers.append(conference.get_authors_id(number = number))

        return readers

    def get_nonreaders(self, conference, number):

        if self.public:
            return []

        if self.release_to_authors:
            return []

        return [conference.get_authors_id(number = number)]

class RegistrationStage(object):

    def __init__(self, committee_id, name='Registration', start_date=None, due_date=None, additional_fields={}, instructions=None, title=None, remove_fields=[]):
        self.committee_id = committee_id
        self.name = name
        self.start_date = start_date
        self.due_date = due_date
        self.additional_fields = additional_fields
        self.instructions = instructions
        self.title = title
        self.remove_fields = remove_fields

class ConferenceBuilder(object):

    def __init__(self, client, support_user=None):
        self.client = client
        self.conference = Conference(client)
        self.webfield_builder = webfield.WebfieldBuilder(client)
        self.submission_stage = None
        self.expertise_selection_stage = None
        self.registration_stages = []
        self.bid_stages = []
        self.review_stage = None
        self.ethics_review_stage = None
        self.review_rebuttal_stage = None
        self.comment_stage = None
        self.meta_review_stage = None
        self.decision_stage = None
        self.program_chairs_ids = []

        self.set_conference_support_user(support_user)

    def __build_groups(self, conference_id):
        path_components = conference_id.split('/')
        paths = ['/'.join(path_components[0:index+1]) for index, path in enumerate(path_components)]
        groups = []

        for p in paths:
            group = tools.get_group(self.client, id = p)
            if group is None:
                group = self.client.post_group(openreview.Group(
                    id = p,
                    readers = ['everyone'],
                    nonreaders = [],
                    writers = [p],
                    signatories = [p],
                    signatures = ['~Super_User1'],
                    members = [],
                    details = { 'writable': True })
                )
                self.conference.new = True

            groups.append(group)

        return groups

    def set_conference_id(self, id):
        self.conference.set_id(id)

    def set_conference_support_user(self, user):
        if user:
            self.conference.support_user = user

    def set_conference_name(self, name):
        self.conference.set_name(name)

    def set_conference_short_name(self, name):
        self.conference.set_short_name(name)

    def set_conference_year(self, year):
        self.conference.set_year(year)

    def set_conference_reviewers_name(self, name):
        self.conference.set_reviewers_name(name)

    def set_reviewer_roles(self, roles):
        self.conference.reviewer_roles = roles

    def set_conference_area_chairs_name(self, name):
        self.conference.has_area_chairs(True)
        self.conference.set_area_chairs_name(name)

    def set_area_chair_roles(self, roles):
        self.conference.area_chair_roles = roles

    def set_senior_area_chair_roles(self, roles):
        self.conference.senior_area_chair_roles = roles

    def set_conference_program_chairs_name(self, name):
        self.conference.set_program_chairs_name(name)

    def set_conference_program_chairs_ids(self, ids):
        self.program_chairs_ids = ids

    def set_homepage_header(self, header):
        self.conference.set_homepage_header(header)

    def set_authorpage_header(self, header):
        self.conference.set_authorpage_header(header)

    def set_reviewerpage_header(self, header):
        self.conference.set_reviewerpage_header(header)

    def set_areachairpage_header(self, header):
        self.conference.has_area_chairs(True)
        self.conference.set_areachairpage_header(header)

    def set_homepage_layout(self, layout):
        self.conference.set_homepage_layout(layout)

    def set_venue_heading_map(self, decision_heading_map):
        self.conference.set_venue_heading_map(decision_heading_map)

    def has_area_chairs(self, has_area_chairs):
        self.conference.has_area_chairs(has_area_chairs)

    def has_senior_area_chairs(self, has_senior_area_chairs):
        self.conference.has_senior_area_chairs(has_senior_area_chairs)

    def has_ethics_chairs(self, has_ethics_chairs):
        self.conference.use_ethics_chairs = has_ethics_chairs

    def has_ethics_reviewers(self, has_ethics_reviewers):
        self.conference.use_ethics_reviewers = has_ethics_reviewers

    def enable_reviewer_reassignment(self, enable):
        self.conference.enable_reviewer_reassignment = enable

    def set_submission_stage(
            self,
            name='Submission',
            start_date=None,
            due_date=None,
            second_due_date=None,
            public=None, ## deprecated, please use readers parameter to specify the readers of the submissions
            double_blind=False,
            additional_fields={},
            remove_fields=[],
            subject_areas=[],
            email_pcs=False,
            create_groups=False,
            create_review_invitation=False,
            withdraw_submission_exp_date=None,
            withdrawn_submission_public=False,
            withdrawn_submission_reveal_authors=False,
            email_pcs_on_withdraw=False,
            desk_rejected_submission_public=False,
            desk_rejected_submission_reveal_authors=False,
            email_pcs_on_desk_reject=True,
            author_names_revealed=False,
            papers_released=False,
            readers=None
        ):

        submissions_readers=[SubmissionStage.Readers.SENIOR_AREA_CHAIRS_ASSIGNED, SubmissionStage.Readers.AREA_CHAIRS_ASSIGNED, SubmissionStage.Readers.REVIEWERS_ASSIGNED]

        if readers is not None:
            submissions_readers=readers

        if public:
            submissions_readers=[SubmissionStage.Readers.EVERYONE]

        self.submission_stage = SubmissionStage(
            name,
            start_date,
            due_date,
            second_due_date,
            submissions_readers,
            double_blind,
            additional_fields,
            remove_fields,
            subject_areas,
            email_pcs,
            create_groups,
            create_review_invitation,
            withdraw_submission_exp_date,
            withdrawn_submission_public,
            withdrawn_submission_reveal_authors,
            email_pcs_on_withdraw,
            desk_rejected_submission_public,
            desk_rejected_submission_reveal_authors,
            email_pcs_on_desk_reject,
            author_names_revealed,
            papers_released
        )

    def set_expertise_selection_stage(self, start_date = None, due_date = None):
        self.expertise_selection_stage = ExpertiseSelectionStage(start_date, due_date)

    def set_registration_stage(self, committee_id, name = 'Registration', start_date = None, due_date = None, additional_fields = {}, instructions = None):
        default_instructions = 'Help us get to know our committee better and the ways to make the reviewing process smoother by answering these questions. If you don\'t see the form below, click on the blue "Registration" button.\n\nLink to Profile: https://openreview.net/profile/edit \nLink to Expertise Selection interface: https://openreview.net/invitation?id={conference_id}/-/Expertise_Selection'.format(conference_id = self.conference.get_id())
        reviewer_instructions = instructions if instructions else default_instructions
        self.registration_stages.append(RegistrationStage(committee_id, name, start_date, due_date, additional_fields, reviewer_instructions))

    def set_bid_stage(self, committee_id, start_date = None, due_date = None, request_count = 50, score_ids = [], instructions = False):
        self.bid_stages.append(BidStage(committee_id, start_date, due_date, request_count, score_ids, instructions))

    def set_review_stage(self, stage):
        self.conference.review_stage = stage

    def set_review_rebuttal_stage(self, start_date = None, due_date = None, name = None,  email_pcs = False, additional_fields = {}):
        self.review_rebuttal_stage = ReviewRebuttalStage(start_date, due_date, name, email_pcs, additional_fields)

    def set_review_rating_stage(self, start_date = None, due_date = None,  name = None, additional_fields = {}, remove_fields = [], public = False, release_to_reviewers=ReviewRatingStage.Readers.NO_REVIEWERS):
        self.review_rating_stage = ReviewRatingStage(start_date, due_date, name, additional_fields, remove_fields, public, release_to_reviewers)

    def set_comment_stage(self, name = None, start_date = None, end_date=None, allow_public_comments = False, anonymous = False, unsubmitted_reviewers = False, reader_selection = False, email_pcs = False, authors = False):
        self.comment_stage = CommentStage(name, start_date, end_date, allow_public_comments, anonymous, unsubmitted_reviewers, reader_selection, email_pcs, authors)

    def set_meta_review_stage(self, name='Meta_Review', start_date = None, due_date = None, public = False, release_to_authors = False, release_to_reviewers = MetaReviewStage.Readers.NO_REVIEWERS, additional_fields = {}, remove_fields = [], process = None):
        self.meta_review_stage = MetaReviewStage(name, start_date, due_date, public, release_to_authors, release_to_reviewers, additional_fields, remove_fields, process)

    def set_decision_stage(self, options = ['Accept (Oral)', 'Accept (Poster)', 'Reject'], start_date = None, due_date = None, public = False, release_to_authors = False, release_to_reviewers = False, release_to_area_chairs=False, email_authors = False, additional_fields={}):
        self.decision_stage = DecisionStage(options, start_date, due_date, public, release_to_authors, release_to_reviewers, release_to_area_chairs, email_authors, additional_fields=additional_fields)

    def set_submission_revision_stage(self, name='Revision', start_date=None, due_date=None, additional_fields={}, remove_fields=[], only_accepted=False, allow_author_reorder=False):
        self.submission_revision_stage = SubmissionRevisionStage(name, start_date, due_date, additional_fields, remove_fields, only_accepted, allow_author_reorder)

    def set_ethics_review_stage(self, stage):
        self.conference.ethics_review_stage = stage
    
    def use_legacy_invitation_id(self, legacy_invitation_id):
        self.conference.legacy_invitation_id = legacy_invitation_id

    def use_legacy_anonids(self, legacy_anonids):
        self.conference.legacy_anonids = legacy_anonids

    def set_request_form_id(self, id):
        self.conference.request_form_id = id

    def set_support_user(self, support_user):
        self.conference.support_user = support_user

    def set_default_reviewers_load(self, default_load):
        # Required to render a default load in the WebField template
        self.conference.set_default_load(default_load, self.conference.reviewers_name)

    def set_reviewer_identity_readers(self, readers):
        self.conference.reviewer_identity_readers = readers

    def set_area_chair_identity_readers(self, readers):
        self.conference.area_chair_identity_readers = readers

    def set_senior_area_chair_identity_readers(self, readers):
        self.conference.senior_area_chair_identity_readers = readers

    def get_result(self):

        if self.conference.reviewer_identity_readers:
            if self.conference.use_area_chairs and self.conference.IdentityReaders.AREA_CHAIRS_ASSIGNED not in self.conference.reviewer_identity_readers and self.conference.IdentityReaders.AREA_CHAIRS not in self.conference.reviewer_identity_readers:
                raise openreview.OpenReviewException('Assigned area chairs must see the reviewer identity')

            if self.conference.use_senior_area_chairs and self.conference.IdentityReaders.SENIOR_AREA_CHAIRS_ASSIGNED not in self.conference.reviewer_identity_readers and self.conference.IdentityReaders.SENIOR_AREA_CHAIRS not in self.conference.reviewer_identity_readers:
                raise openreview.OpenReviewException('Assigned senior area chairs must see the reviewer identity')

        id = self.conference.get_id()
        groups = self.__build_groups(id)
        for i, g in enumerate(groups[:-1]):
            self.webfield_builder.set_landing_page(g, groups[i-1] if i > 0 else None)

        host = self.client.get_group(id = 'host', details='writable')
        root_id = groups[0].id
        home_group = groups[-1]
        if root_id == root_id.lower():
            root_id = groups[1].id
        if host.details.get('writable'):
            self.client.add_members_to_group(host, root_id)
            home_group.host = root_id
            self.client.post_group(home_group)

        venues = self.client.get_group(id = 'venues', details='writable')
        if venues.details.get('writable'):
            self.client.add_members_to_group('venues', home_group.id)

        if self.submission_stage:
            self.conference.set_submission_stage(self.submission_stage)

        ## Create committee groups before any other stage that requires them to create groups and/or invitations
        self.conference.set_program_chairs(emails=self.program_chairs_ids)
        self.conference.set_authors()
        self.conference.set_reviewers()
        if self.conference.use_senior_area_chairs:
            self.conference.set_senior_area_chairs()
        if self.conference.use_area_chairs:
            self.conference.set_area_chairs()

        parent_group_id = groups[-2].id if len(groups) > 1 else ''
        venue_heading_map = self.conference.venue_heading_map
        groups[-1] = self.webfield_builder.set_home_page(conference = self.conference, group = home_group, layout = self.conference.layout, options = { 'parent_group_id': parent_group_id, 'decision_heading_map': venue_heading_map })

        self.conference.set_conference_groups(groups)
        if self.conference.use_senior_area_chairs:
            self.conference.set_senior_area_chair_recruitment_groups()
        if self.conference.use_area_chairs:
            self.conference.set_area_chair_recruitment_groups()
        if self.conference.use_ethics_chairs:
            self.conference.set_ethics_chair_recruitment_groups()
        if self.conference.use_ethics_reviewers:
            self.conference.set_ethics_reviewer_recruitment_groups()                       
        self.conference.set_reviewer_recruitment_groups()

        for s in self.bid_stages:
            self.conference.set_bid_stage(s)

        if self.expertise_selection_stage:
            self.conference.set_expertise_selection_stage(self.expertise_selection_stage)

        for s in self.registration_stages:
            self.conference.set_registration_stage(s)

        if self.review_rebuttal_stage:
            self.conference.set_review_rebuttal_stage(self.review_rebuttal_stage)

        if self.comment_stage:
            self.conference.set_comment_stage(self.comment_stage)

        if self.meta_review_stage:
            self.conference.set_meta_review_stage(self.meta_review_stage)

        if self.decision_stage:
            self.conference.set_decision_stage(self.decision_stage)

        return self.conference
