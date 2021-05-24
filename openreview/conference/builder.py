from __future__ import absolute_import

import time
import datetime
import re
from enum import Enum
from tqdm import tqdm
import os
import concurrent.futures
from .. import openreview
from .. import tools
from . import webfield
from . import invitation
from . import matching
from .. import invitations

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
        self.new = False
        self.use_area_chairs = False
        self.use_senior_area_chairs = False
        self.use_secondary_area_chairs = False
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
        self.area_chairs_name = 'Area_Chairs'
        self.senior_area_chairs_name = 'Senior_Area_Chairs'
        self.secondary_area_chairs_name = 'Secondary_Area_Chair'
        self.program_chairs_name = 'Program_Chairs'
        self.recommendation_name = 'Recommendation'
        self.submission_stage = SubmissionStage()
        self.bid_stages = {}
        self.expertise_selection_stage = ExpertiseSelectionStage()
        self.registration_stage = RegistrationStage()
        self.review_stage = ReviewStage()
        self.review_rebuttal_stage = None
        self.review_revision_stage = None
        self.review_rating_stage = None
        self.submission_revision_stage = None
        self.comment_stage = CommentStage()
        self.meta_review_stage = MetaReviewStage()
        self.decision_stage = DecisionStage()
        self.layout = 'tabs'
        self.enable_reviewer_reassignment = False
        self.reduced_load_on_decline = []
        self.default_reviewer_load = 0
        self.reviewer_identity_readers = []
        self.area_chair_identity_readers = []
        self.senior_area_chair_identity_readers = []

    def __create_group(self, group_id, group_owner_id, members = [], is_signatory = True, additional_readers = []):
        group = tools.get_group(self.client, id = group_id)
        if group is None:
            return self.client.post_group(openreview.Group(
                id = group_id,
                readers = ['everyone'] if 'everyone' in additional_readers else [self.id, group_owner_id, group_id] + additional_readers,
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

    def __expire_invitation(self, invitation_id):
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
        invitations = list(tools.iterget_invitations(self.client, regex = self.get_invitation_id(name, '.*')))

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

    def __create_registration_stage(self):
        return self.invitation_builder.set_registration_invitation(self)

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
        return invitations

    def __create_review_rebuttal_stage(self):
        invitation = self.get_invitation_id(self.review_stage.name, '.*')
        review_iterator = tools.iterget_notes(self.client, invitation = invitation)
        return self.invitation_builder.set_review_rebuttal_invitation(self, review_iterator)

    def __create_review_revision_stage(self):
        invitation = self.get_invitation_id(self.review_stage.name, '.*')
        review_iterator = tools.iterget_notes(self.client, invitation = invitation)
        return self.invitation_builder.set_review_revision_invitation(self, review_iterator)

    def __create_review_rating_stage(self):
        invitation = self.get_invitation_id(self.review_stage.name, '.*')
        review_iterator = tools.iterget_notes(self.client, invitation = invitation)
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
            return self.invitation_builder.set_revise_submission_invitation(self, notes, invitation.reply['content'])

    def set_reviewer_reassignment(self, enabled = True):
        self.enable_reviewer_reassignment = enabled

        # Update PC & AC homepages
        pc_group = self.client.get_group(self.get_program_chairs_id())
        self.webfield_builder.edit_web_value(pc_group, 'ENABLE_REVIEWER_REASSIGNMENT', str(enabled).lower())

        if self.use_area_chairs:
            ac_group = self.client.get_group(self.get_area_chairs_id())
            self.webfield_builder.edit_web_value(ac_group, 'ENABLE_REVIEWER_REASSIGNMENT', str(enabled).lower())

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
        self.registration_stage = stage
        return self.__create_registration_stage()

    def set_bid_stage(self, stage):
        self.bid_stages[stage.committee_id] = stage
        return self.__create_bid_stage(stage)

    def set_review_stage(self, stage):
        self.review_stage = stage
        return self.__create_review_stage()

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
        return self.__create_decision_stage()

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

    def get_anon_reviewer_id(self, number=None, anon_id=None):
        single_reviewer_name=self.reviewers_name[:-1] if self.reviewers_name.endswith('s') else self.reviewers_name
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

    def get_submission_id(self):
        return self.submission_stage.get_submission_id(self)

    def get_blind_submission_id(self):
        return self.submission_stage.get_blind_submission_id(self)

    def get_expertise_selection_id(self):
        return self.get_invitation_id(self.expertise_selection_stage.name)

    def get_bid_id(self, group_id):
        if group_id in self.bid_stages:
            return self.get_invitation_id(self.bid_stages[group_id].name, prefix=group_id)
        raise openreview.OpenReviewException('BidStage not found for {}'.format(group_id))

    def get_recommendation_id(self, group_id=None):
        if not group_id:
            group_id = self.get_reviewers_id()
        return self.get_invitation_id(self.recommendation_name, prefix=group_id)

    def get_registration_id(self, committee_id):
        return self.get_invitation_id(name = self.registration_stage.name, prefix = committee_id)

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
        notes = list(tools.iterget_notes(self.client, invitation = invitation, number=number, details = details, sort = sort))
        if accepted:
            decisions = tools.iterget_notes(self.client, invitation = self.get_invitation_id(self.decision_stage.name, '.*'))
            accepted_forums = [d.forum for d in decisions if 'Accept' in d.content['decision']]
            accepted_notes = [n for n in notes if n.id in accepted_forums]
            return accepted_notes
        return notes

    def get_withdrawn_submissions(self, details=None):
        invitation = self.submission_stage.get_withdrawn_submission_id(self)
        return list(tools.iterget_notes(self.client, invitation=invitation, details=details))

    def get_desk_rejected_submissions(self, details=None):
        invitation = self.submission_stage.get_desk_rejected_submission_id(self)
        return list(tools.iterget_notes(self.client, invitation=invitation, details=details))

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
        readers=[self.id]
        if self.use_senior_area_chairs:
            readers.append(self.get_senior_area_chairs_id(number))
        readers.append(self.get_area_chairs_id(number))
        return readers

    def create_withdraw_invitations(self, reveal_authors=False, reveal_submission=False, email_pcs=False, force=False):

        if not force and reveal_submission and not self.submission_stage.public:
            raise openreview.OpenReviewException('Can not reveal withdrawn submissions that are not originally public')

        if not force and not reveal_authors and not self.submission_stage.double_blind:
            raise openreview.OpenReviewException('Can not hide authors of submissions in single blind or open venue')

        return self.invitation_builder.set_withdraw_invitation(self, reveal_authors, reveal_submission, email_pcs)

    def create_desk_reject_invitations(self, reveal_authors=False, reveal_submission=False, force=False):

        if not force and reveal_submission and not self.submission_stage.public:
            raise openreview.OpenReviewException('Can not reveal desk-rejected submissions that are not originally public')

        if not force and not reveal_authors and not self.submission_stage.double_blind:
            raise openreview.OpenReviewException('Can not hide authors of submissions in single blind or open venue')

        return self.invitation_builder.set_desk_reject_invitation(self, reveal_authors, reveal_submission)

    def create_paper_groups(self, authors=False, reviewers=False, area_chairs=False):

        notes_iterator = self.get_submissions(sort='number:asc', details='original')
        author_group_ids = []
        paper_reviewer_group_invitation=self.invitation_builder.set_paper_group_invitation(self, self.get_reviewers_id())
        if self.use_area_chairs:
            paper_area_chair_group_invitation=self.invitation_builder.set_paper_group_invitation(self, self.get_area_chairs_id())

        for n in tqdm(list(notes_iterator), desc='create_paper_groups'):
            # Paper group
            self.__create_group(
                group_id = '{conference_id}/Paper{number}'.format(conference_id=self.id, number=n.number),
                group_owner_id = self.get_area_chairs_id(number=n.number) if self.use_area_chairs else self.id,
                is_signatory = False
            )

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
                    group = tools.get_group(self.client, id = reviewers_id)
                    if not group:
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
                self.__create_group(
                    self.get_reviewers_id(number=n.number) + '/Submitted',
                    self.get_area_chairs_id(number=n.number) if self.use_area_chairs else self.id,
                    is_signatory = False)

            # Area Chairs Paper group
            if self.use_area_chairs and area_chairs:
                if self.legacy_anonids:
                    self.__create_group(self.get_area_chairs_id(number=n.number), self.id)
                else:
                    area_chairs_id=self.get_area_chairs_id(number=n.number)
                    group = tools.get_group(self.client, id = area_chairs_id)
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
            if self.use_senior_area_chairs:
                senior_area_chairs_id=self.get_senior_area_chairs_id(number=n.number)
                group = tools.get_group(self.client, id = senior_area_chairs_id)
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

    def create_blind_submissions(self, hide_fields=[], under_submission=False, under_submission_readers=[]):

        if not self.submission_stage.double_blind:
            raise openreview.OpenReviewException('Conference is not double blind')

        submissions_by_original = { note.original: note for note in self.get_submissions() }
        withdrawn_submissions_by_original = {note.original: note for note in self.get_withdrawn_submissions()}
        desk_rejected_submissions_by_original = {note.original: note for note in self.get_desk_rejected_submissions()}

        self.invitation_builder.set_blind_submission_invitation(self, hide_fields)
        blinded_notes = []

        for note in tqdm(list(tools.iterget_notes(self.client, invitation=self.get_submission_id(), sort='number:asc')), desc='create_blind_submissions'):
            # If the note was either withdrawn or desk-rejected already, we should not create another blind copy
            if withdrawn_submissions_by_original.get(note.id) or desk_rejected_submissions_by_original.get(note.id):
                continue

            existing_blind_note = submissions_by_original.get(note.id)
            blind_content = {
                'authors': ['Anonymous'],
                'authorids': [self.get_authors_id(number=note.number)],
                '_bibtex': None
            }

            for field in hide_fields:
                blind_content[field] = ''

            blind_readers = self.submission_stage.get_readers(self, note.number, under_submission, under_submission_readers)

            if not existing_blind_note or existing_blind_note.content != blind_content or existing_blind_note.readers != blind_readers:

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

                if self.submission_stage.public:
                    blind_content['_bibtex'] = tools.get_bibtex(
                        note=note,
                        venue_fullname=self.name,
                        url_forum=blind_note.id,
                        year=str(self.get_year()))

                    blind_note.content = blind_content

                    blind_note = self.client.post_note(blind_note)
            blinded_notes.append(blind_note)

        # Update PC console with double blind submissions
        pc_group = self.client.get_group(self.get_program_chairs_id())
        self.webfield_builder.edit_web_string_value(pc_group, 'BLIND_SUBMISSION_ID', self.get_blind_submission_id())

        return blinded_notes

    def setup_first_deadline_stage(self, force=False, hide_fields=[], submission_readers=[]):

        if self.submission_stage.double_blind:
            self.create_blind_submissions(hide_fields=hide_fields, under_submission=True, under_submission_readers=submission_readers)
        else:
            if submission_readers:
                self.invitation_builder.set_submission_invitation(conference=self, under_submission=True, submission_readers=submission_readers)
                submissions = self.get_submissions()
                for s in submissions:
                    if not set(submission_readers).issubset(set(s.readers)):
                        s.readers = s.readers + submission_readers
                        self.client.post_note(s)

        self.create_paper_groups(authors=True, reviewers=True, area_chairs=True)
        self.create_withdraw_invitations(
            reveal_authors=not self.submission_stage.double_blind,
            reveal_submission=False,
            email_pcs=False,
            force=True
        )
        self.create_desk_reject_invitations(
            reveal_authors=not self.submission_stage.double_blind,
            reveal_submission=False,
            force=True
        )

        self.submission_revision_stage = SubmissionRevisionStage(name='Revision',
            start_date=None if force else self.submission_stage.due_date,
            due_date=self.submission_stage.second_due_date,
            additional_fields=self.submission_stage.additional_fields,
            remove_fields=self.submission_stage.remove_fields,
            only_accepted=False,
            multiReply=False
        )
        self.__create_submission_revision_stage()

    def setup_final_deadline_stage(self, force=False, hide_fields=[]):

        if self.submission_stage.double_blind and not (self.submission_stage.author_names_revealed or self.submission_stage.papers_released):
            self.create_blind_submissions(hide_fields)

        if not self.submission_stage.double_blind and not self.submission_stage.papers_released and not self.submission_stage.create_groups:
            self.invitation_builder.set_submission_invitation(self, under_submission=False)
            for note in tqdm(list(tools.iterget_notes(self.client, invitation=self.get_submission_id(), sort='number:asc')), desc='set_final_readers'):
                final_readers =  self.submission_stage.get_readers(conference=self, number=note.number, under_submission=False)
                if note.readers != final_readers:
                    note.readers = final_readers
                    self.client.post_note(note)

        self.create_paper_groups(authors=True, reviewers=True, area_chairs=True)
        self.create_withdraw_invitations(
            reveal_authors=self.submission_stage.withdrawn_submission_reveal_authors,
            reveal_submission=self.submission_stage.withdrawn_submission_public,
            email_pcs=self.submission_stage.email_pcs_on_withdraw
        )
        self.create_desk_reject_invitations(
            reveal_authors=self.submission_stage.desk_rejected_submission_reveal_authors,
            reveal_submission=self.submission_stage.desk_rejected_submission_public
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
        self.__expire_invitation(self.get_bid_id(self.get_reviewers_id()))
        if self.use_area_chairs:
            self.__expire_invitation(self.get_bid_id(self.get_area_chairs_id()))

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

    ## Deprecated
    def open_registration(self, name=None, start_date=None, due_date=None, additional_fields={}, ac_additional_fields={}, instructions=None, ac_instructions=None):
        self.registration_stage = RegistrationStage(start_date=start_date, due_date=due_date, additional_fields=additional_fields, ac_additional_fields=ac_additional_fields, instructions=instructions, ac_instructions=ac_instructions)
        self.__create_registration_stage()

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
        # if first time, add PC console
        if not pcs.web:
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
            self.__create_group(parent_group_declined_id, pcs_id)
            # parent_group_invited_group
            self.__create_group(parent_group_invited_id, pcs_id)
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
            self.__create_group(parent_group_declined_id, pcs_id)
            # parent_group_invited_group
            self.__create_group(parent_group_invited_id, pcs_id)
        else:
            raise openreview.OpenReviewException('Conference "has_area_chairs" setting is disabled')

    def set_reviewer_recruitment_groups(self):
        parent_group_id = self.get_reviewers_id()
        parent_group_declined_id = parent_group_id + '/Declined'
        parent_group_invited_id = parent_group_id + '/Invited'

        pcs_id = self.get_program_chairs_id()
        self.__create_group(parent_group_id, self.get_area_chairs_id() if self.use_area_chairs else self.id)
        self.__create_group(parent_group_declined_id, pcs_id)
        self.__create_group(parent_group_invited_id, pcs_id)

    def set_external_reviewer_recruitment_groups(self):
        parent_group_id = self.get_committee_id(name='External_Reviewers')
        parent_group_invited_id = parent_group_id + '/Invited'

        self.__create_group(parent_group_id, self.id)
        self.__create_group(parent_group_invited_id, self.id)

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

    def set_authors(self):
        # Creating venue level authors group
        authors_group = self.__create_group(self.get_authors_id(), self.id, additional_readers=['everyone'])

        # Creating venue level accepted authors group
        self.__create_group(self.get_accepted_authors_id(), self.id)

        return self.webfield_builder.set_author_page(self, authors_group)

    def set_impersonators(self, emails = []):
        # Only super user can call this
        impersonate_group_id=f'{self.id}/Impersonate'
        group=tools.get_group(self.client, impersonate_group_id)

        if not group:
            group=self.client.post_group(openreview.Group(
                id=impersonate_group_id,
                readers=[self.id],
                writers=[],
                signatures=[],
                signatories=[self.id],
                members=[]
            ))

        group=self.client.add_members_to_group(group, emails)

        return self.webfield_builder.set_impersonate_page(self, group)

    def setup_matching(self, committee_id=None, affinity_score_file=None, tpms_score_file=None, elmo_score_file=None, build_conflicts=False):
        if committee_id is None:
            committee_id=self.get_reviewers_id()
        conference_matching = matching.Matching(self, self.client.get_group(committee_id))

        return conference_matching.setup(affinity_score_file, tpms_score_file, elmo_score_file, build_conflicts)

    def setup_assignment_recruitment(self, committee_id, hash_seed, due_date, assignment_title=None):

        conference_matching = matching.Matching(self, self.client.get_group(committee_id))
        return conference_matching.setup_invite_assignment(hash_seed, assignment_title, due_date)


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


    def set_recruitment_reduced_load(self, reduced_load_options):
        self.reduced_load_on_decline = reduced_load_options

    def recruit_reviewers(self, invitees = [], title = None, message = None, reviewers_name = 'Reviewers', remind = False, invitee_names = [], retry_declined=False):

        pcs_id = self.get_program_chairs_id()
        reviewers_id = self.id + '/' + reviewers_name
        reviewers_declined_id = reviewers_id + '/Declined'
        reviewers_invited_id = reviewers_id + '/Invited'
        reviewers_accepted_id = reviewers_id
        hash_seed = '1234'
        invitees = [e.lower() if '@' in e else e for e in invitees]

        reviewers_accepted_group = self.__create_group(reviewers_accepted_id, pcs_id)
        reviewers_declined_group = self.__create_group(reviewers_declined_id, pcs_id)
        reviewers_invited_group = self.__create_group(reviewers_invited_id, pcs_id)

        official_committee_roles=self.get_committee_names()
        committee_roles = official_committee_roles if reviewers_name in official_committee_roles else [reviewers_name]
        recruitment_status = {
            'invited': [],
            'reminded': [],
            'already_invited': {},
            'errors': []
        }

        options = {
            'reviewers_name': reviewers_name,
            'reviewers_accepted_id': reviewers_accepted_id,
            'reviewers_invited_id': reviewers_invited_id,
            'reviewers_declined_id': reviewers_declined_id,
            'hash_seed': hash_seed
        }
        if options['reviewers_name'] == 'Reviewers' and self.reduced_load_on_decline:
            options['reduced_load_on_decline'] = self.reduced_load_on_decline
            invitation = self.invitation_builder.set_reviewer_reduced_load_invitation(self, options)
            invitation = self.webfield_builder.set_reduced_load_page(self.id, invitation, self.get_homepage_options())

        invitation = self.invitation_builder.set_reviewer_recruiter_invitation(self, options)
        invitation = self.webfield_builder.set_recruit_page(self.id, invitation, self.get_homepage_options(), options['reviewers_name'])

        role = 'reviewer' if reviewers_name == 'Reviewers' else 'area chair'
        recruit_message = '''Dear {name},

        You have been nominated by the program chair committee of '''+ self.get_short_name() + ''' to serve as '''+ role +'''. As a respected researcher in the area, we hope you will accept and help us make ''' + self.short_name + ''' a success.

        You are also welcome to submit papers, so please also consider submitting to '''+ self.get_short_name() + '''.

        We will be using OpenReview.net with the intention of have an engaging reviewing process inclusive of the whole community.

        To ACCEPT the invitation, please click on the following link:

        {accept_url}

        To DECLINE the invitation, please click on the following link:

        {decline_url}

        Please answer within 10 days.

        If you accept, please make sure that your OpenReview account is updated and lists all the emails you are using.  Visit http://openreview.net/profile after logging in.

        If you have any questions, please contact info@openreview.net.

        Cheers!

        Program Chairs

        '''

        recruit_message_subj = '[' + self.get_short_name() + ']: Invitation to serve as ' + role.title()

        if title:
            recruit_message_subj = title

        if message:
            recruit_message = message

        if remind:
            invited_reviewers = reviewers_invited_group.members
            print ('Sending reminders for recruitment invitations')
            for reviewer_id in tqdm(invited_reviewers, desc='remind_reviewers'):
                memberships = [g.id for g in self.client.get_groups(member=reviewer_id, regex=reviewers_id)] if tools.get_group(self.client, reviewer_id) else []
                if reviewers_id not in memberships and reviewers_declined_id not in memberships:
                    reviewer_name = 'invitee'
                    if reviewer_id.startswith('~') :
                        reviewer_name =  re.sub('[0-9]+', '', reviewer_id.replace('~', '').replace('_', ' '))
                    elif (reviewer_id in invitees) and invitee_names:
                        reviewer_name = invitee_names[invitees.index(reviewer_id)]
                    try:
                        tools.recruit_reviewer(self.client, reviewer_id, reviewer_name,
                            hash_seed,
                            invitation.id,
                            recruit_message,
                            'Reminder: ' + recruit_message_subj,
                            reviewers_invited_id,
                            verbose = False)
                        recruitment_status['reminded'].append(reviewer_id)
                    except openreview.OpenReviewException as e:
                        self.client.remove_members_from_group(reviewers_invited_group, reviewer_id)
                        recruitment_status['errors'].append(e)

        if retry_declined:
            declined_reviewers = reviewers_declined_group.members
            print ('Sending retry to declined reviewers')
            for reviewer_id in tqdm(declined_reviewers, desc='retry_declined'):
                memberships = [g.id for g in self.client.get_groups(member=reviewer_id, regex=reviewers_id)] if tools.get_group(self.client, reviewer_id) else []
                if reviewers_id not in memberships:
                    reviewer_name = 'invitee'
                    if reviewer_id.startswith('~') :
                        reviewer_name =  re.sub('[0-9]+', '', reviewer_id.replace('~', '').replace('_', ' '))
                    elif (reviewer_id in invitees) and invitee_names:
                        reviewer_name = invitee_names[invitees.index(reviewer_id)]
                    try:
                        tools.recruit_reviewer(self.client, reviewer_id, reviewer_name,
                            hash_seed,
                            invitation.id,
                            recruit_message,
                            recruit_message_subj,
                            reviewers_invited_id,
                            verbose = False)
                    except openreview.OpenReviewException as e:
                        self.client.remove_members_from_group(reviewers_invited_group, reviewer_id)
                        recruitment_status['errors'].append(e)

        print ('Sending recruitment invitations')
        for index, email in enumerate(tqdm(invitees, desc='send_invitations')):
            memberships = [g.id for g in self.client.get_groups(member=email, regex=self.id)] if tools.get_group(self.client, email) else []
            invited_roles = [f'{self.id}/{role}/Invited' for role in committee_roles]

            invited_group_ids=list(set(invited_roles) & set(memberships))

            if invited_group_ids:
                invited_group_id=invited_group_ids[0]
                if invited_group_id not in recruitment_status['already_invited']:
                    recruitment_status['already_invited'][invited_group_id] = []
                recruitment_status['already_invited'][invited_group_id].append(email)
            else:
                name = invitee_names[index] if (invitee_names and index < len(invitee_names)) else None
                if not name:
                    name = re.sub('[0-9]+', '', email.replace('~', '').replace('_', ' ')) if email.startswith('~') else 'invitee'
                try:
                    tools.recruit_reviewer(self.client, email, name,
                        hash_seed,
                        invitation.id,
                        recruit_message,
                        recruit_message_subj,
                        reviewers_invited_id,
                        verbose = False)
                    recruitment_status['invited'].append(email)
                except openreview.OpenReviewException as e:
                    self.client.remove_members_from_group(reviewers_invited_group, email)
                    recruitment_status['errors'].append(e)
        return recruitment_status

    ## temporary function, move to somewhere else
    def remind_registration_stage(self, subject, message, committee_id):

        reviewers = self.client.get_group(committee_id).members
        profiles_by_email = self.client.search_profiles(confirmedEmails=[m for m in reviewers if '@' in m])
        confirmations = {c.tauthor: c for c in list(tools.iterget_notes(self.client, invitation=self.get_registration_id(committee_id)))}
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
        options['decision_invitation_regex'] = self.get_invitation_id(invitation_name, '.*')

        if not decision_heading_map:
            decision_heading_map = {}
            invitations = self.client.get_invitations(regex = self.get_invitation_id(invitation_name, '.*'), expired=True, limit = 1)
            if invitations:
                for option in invitations[0].reply['content']['decision']['value-radio']:
                    decision_heading_map[option] = option + ' Papers'
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
                    print ('Error during attachment download for paper number {}, error: {}'.format(submission.number, e))
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

    def post_decision_stage(self, reveal_all_authors=False, reveal_authors_accepted=False, release_all_notes=False, release_notes_accepted=False, decision_heading_map=None):
        submissions = self.get_submissions(details='original')
        decisions_by_forum = {n.forum: n for n in list(tools.iterget_notes(self.client, invitation = self.get_invitation_id(self.decision_stage.name, '.*')))}

        if (release_all_notes or release_notes_accepted) and not self.submission_stage.double_blind:
            self.invitation_builder.set_submission_invitation(self, under_submission=False, submission_readers=['everyone'])

        def is_release_note(is_note_accepted):
            return release_all_notes or (release_notes_accepted and is_note_accepted)

        def is_release_authors(is_note_accepted):
            return reveal_all_authors or (reveal_authors_accepted and is_note_accepted)

        for submission in tqdm(submissions):
            decision_note = decisions_by_forum.get(submission.forum, None)
            note_accepted = decision_note and 'Accept' in decision_note.content['decision']
            if is_release_note(note_accepted) or 'everyone' in submission.readers:
                submission.readers = ['everyone']
                if self.submission_stage.double_blind:
                    release_authors = is_release_authors(note_accepted)
                    submission.content = {
                        '_bibtex': tools.get_bibtex(
                                    openreview.Note.from_json(submission.details['original']),
                                    venue_fullname=self.name,
                                    year=str(self.year),
                                    url_forum=submission.forum,
                                    accepted=note_accepted,
                                    anonymous=(not release_authors))
                    }
                    if not release_authors:
                        submission.content['authors'] = ['Anonymous']
                        submission.content['authorids'] = ['Anonymous']
                else:
                    submission.content['_bibtex'] = tools.get_bibtex(
                                    submission,
                                    venue_fullname=self.name,
                                    year=str(self.year),
                                    url_forum=submission.forum,
                                    accepted=note_accepted,
                                    anonymous=False)
                if note_accepted:
                    decision = decision_note.content['decision'].replace('Accept', '')
                    decision = re.sub(r'[()\W]+', '', decision)
                    venueid = self.id
                    venue = self.short_name
                    if decision:
                        venue += ' ' + decision
                    submission.content['venueid'] = venueid
                    submission.content['venue'] = venue
                self.client.post_note(submission)

        if decision_heading_map:
            self.set_homepage_decisions(decision_heading_map=decision_heading_map)
        self.client.remove_members_from_group('active_venues', self.id)

class SubmissionStage(object):

    class Readers(Enum):
        EVERYONE = 0
        SENIOR_AREA_CHAIRS = 1
        SENIOR_AREA_CHAIRS_ASSIGNED = 2
        AREA_CHAIRS = 3
        AREA_CHAIRS_ASSIGNED = 4
        REVIEWERS = 5
        REVIEWERS_ASSIGNED = 6

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
        self.withdrawn_submission_public = withdrawn_submission_public
        self.withdrawn_submission_reveal_authors = withdrawn_submission_reveal_authors
        self.email_pcs_on_withdraw = email_pcs_on_withdraw
        self.desk_rejected_submission_public = desk_rejected_submission_public
        self.desk_rejected_submission_reveal_authors = desk_rejected_submission_reveal_authors
        self.email_pcs_on_desk_reject = email_pcs_on_desk_reject
        self.author_names_revealed = author_names_revealed
        self.papers_released = papers_released
        self.public = self.Readers.EVERYONE in self.readers

    def get_readers(self, conference, number, under_submission, under_submission_readers=[]):

        ## the paper is still under submission and shouldn't be released yet
        if under_submission:
            submission_readers=[conference.get_id()]
            submission_readers=submission_readers + under_submission_readers
            submission_readers.append(conference.get_authors_id(number=number))
            return submission_readers

        if self.public:
            return ['everyone']

        submission_readers=[conference.get_id()]

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

        submission_readers.append(conference.get_authors_id(number=number))
        return submission_readers

    def get_invitation_readers(self, conference, under_submission, submission_readers):

        ## Rolling review should be release right away
        if self.create_groups:
            return {'values': ['everyone']}

        if under_submission or self.double_blind:
            readers = {
                'values-copied': [
                    conference.get_id(),
                    '{content.authorids}',
                    '{signatures}'
                ]
            }
            if submission_readers:
                readers['values-copied'] = readers['values-copied'] + submission_readers
            return readers

        if self.public or (submission_readers and submission_readers == ['everyone']):
            return {'values': ['everyone']}

        ## allow any reader until we can figure out how to set the readers by paper number
        return {
            'values-regex': '.*'
        }

    def get_submission_id(self, conference):
        return conference.get_invitation_id(self.name)

    def get_blind_submission_id(self, conference):
        name = self.name
        if self.double_blind:
            name = 'Blind_' + name
        return conference.get_invitation_id(name)

    def get_withdrawn_submission_id(self, conference, name = 'Withdrawn_Submission'):
        return conference.get_invitation_id(name)

    def get_desk_rejected_submission_id(self, conference, name = 'Desk_Rejected_Submission'):
        return conference.get_invitation_id(name)

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
        final_due_date = self.second_due_date if self.second_due_date else self.due_date
        return not final_due_date or datetime.datetime.utcnow() < final_due_date

class ExpertiseSelectionStage(object):

    def __init__(self, start_date = None, due_date = None):
        self.start_date = start_date
        self.due_date = due_date
        self.name = 'Expertise_Selection'

class BidStage(object):

    def __init__(self, committee_id, start_date=None, due_date=None, request_count=50, score_ids=[], instructions=False):
        self.committee_id=committee_id
        self.start_date=start_date
        self.due_date=due_date
        self.name='Bid'
        self.request_count=request_count
        self.score_ids=score_ids
        self.instructions=instructions

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
            readers.append(conference.get_area_chairs_id(number = number))

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
    only_accepted=False):
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

    def __init__(self, start_date = None, due_date = None, public = False, additional_fields = {}, remove_fields=[], process = None):
        self.start_date = start_date
        self.due_date = due_date
        self.name = 'Meta_Review'
        self.public = public
        self.additional_fields = additional_fields
        self.remove_fields = remove_fields
        self.process = None

    def get_readers(self, conference, number):

        if self.public:
            return ['everyone']

        readers = []

        if conference.use_senior_area_chairs:
            readers.append(conference.get_senior_area_chairs_id(number = number))

        if conference.use_area_chairs:
            readers.append(conference.get_area_chairs_id(number = number))

        readers.append(conference.get_program_chairs_id())

        return readers

    def get_signatures_regex(self, conference, number):

        committee = [conference.get_program_chairs_id()]

        if conference.use_area_chairs:
            committee.append(conference.get_anon_area_chair_id(number=number, anon_id='.*'))

        return '|'.join(committee)

class DecisionStage(object):

    def __init__(self, options = None, start_date = None, due_date = None, public = False, release_to_authors = False, release_to_reviewers = False, email_authors = False):
        if not options:
            options = ['Accept (Oral)', 'Accept (Poster)', 'Reject']
        self.options = options
        self.start_date = start_date
        self.due_date = due_date
        self.name = 'Decision'
        self.public = public
        self.release_to_authors = release_to_authors
        self.release_to_reviewers = release_to_reviewers
        self.email_authors = email_authors

    def get_readers(self, conference, number):

        if self.public:
            return ['everyone']

        readers = [ conference.get_program_chairs_id()]
        if conference.use_area_chairs:
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

    def __init__(self, name='Registration', start_date=None, due_date=None, additional_fields={}, ac_additional_fields={}, instructions=None, ac_instructions=None):
        self.name = name
        self.start_date = start_date
        self.due_date = due_date
        self.additional_fields = additional_fields
        self.ac_additional_fields = ac_additional_fields
        self.instructions = instructions
        self.ac_instructions = ac_instructions

class ConferenceBuilder(object):

    def __init__(self, client, support_user=None):
        self.client = client
        self.conference = Conference(client)
        self.webfield_builder = webfield.WebfieldBuilder(client)
        self.submission_stage = None
        self.expertise_selection_stage = None
        self.registration_stage = None
        self.bid_stages = []
        self.review_stage = None
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

    def set_conference_area_chairs_name(self, name):
        self.conference.has_area_chairs(True)
        self.conference.set_area_chairs_name(name)

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

    def has_area_chairs(self, has_area_chairs):
        self.conference.has_area_chairs(has_area_chairs)

    def has_senior_area_chairs(self, has_senior_area_chairs):
        self.conference.has_senior_area_chairs(has_senior_area_chairs)

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

        submissions_readers=[SubmissionStage.Readers.SENIOR_AREA_CHAIRS, SubmissionStage.Readers.AREA_CHAIRS, SubmissionStage.Readers.REVIEWERS]
        if public:
            submissions_readers=[SubmissionStage.Readers.EVERYONE]
        if readers:
            submissions_readers=readers

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

    def set_registration_stage(self, name = 'Registration', start_date = None, due_date = None, additional_fields = {}, ac_additional_fields = {}, instructions = None, ac_instructions = None):
        default_instructions = 'Help us get to know our committee better and the ways to make the reviewing process smoother by answering these questions. If you don\'t see the form below, click on the blue "Registration" button.\n\nLink to Profile: https://openreview.net/profile?mode=edit \nLink to Expertise Selection interface: https://openreview.net/invitation?id={conference_id}/-/Expertise_Selection'.format(conference_id = self.conference.get_id())
        reviewer_instructions = instructions if instructions else default_instructions
        ac_instructions = ac_instructions if ac_instructions else default_instructions
        self.registration_stage=RegistrationStage(name, start_date, due_date, additional_fields, ac_additional_fields, reviewer_instructions, ac_instructions)

    def set_bid_stage(self, committee_id, start_date = None, due_date = None, request_count = 50, score_ids = [], instructions = False):
        self.bid_stages.append(BidStage(committee_id, start_date, due_date, request_count, score_ids, instructions))

    def set_review_stage(self, start_date = None, due_date = None, name = None, allow_de_anonymization = False, public = False, release_to_authors = False, release_to_reviewers = ReviewStage.Readers.REVIEWER_SIGNATURE, email_pcs = False, additional_fields = {}, remove_fields = []):
        self.review_stage = ReviewStage(start_date, due_date, name, allow_de_anonymization, public, release_to_authors, release_to_reviewers, email_pcs, additional_fields, remove_fields)

    def set_review_rebuttal_stage(self, start_date = None, due_date = None, name = None,  email_pcs = False, additional_fields = {}):
        self.review_rebuttal_stage = ReviewRebuttalStage(start_date, due_date, name, email_pcs, additional_fields)

    def set_review_rating_stage(self, start_date = None, due_date = None,  name = None, additional_fields = {}, remove_fields = [], public = False, release_to_reviewers=ReviewRatingStage.Readers.NO_REVIEWERS):
        self.review_rating_stage = ReviewRatingStage(start_date, due_date, name, additional_fields, remove_fields, public, release_to_reviewers)

    def set_comment_stage(self, name = None, start_date = None, end_date=None, allow_public_comments = False, anonymous = False, unsubmitted_reviewers = False, reader_selection = False, email_pcs = False, authors = False):
        self.comment_stage = CommentStage(name, start_date, end_date, allow_public_comments, anonymous, unsubmitted_reviewers, reader_selection, email_pcs, authors)

    def set_meta_review_stage(self, start_date = None, due_date = None, public = False, additional_fields = {}, remove_fields = [], process = None):
        self.meta_review_stage = MetaReviewStage(start_date, due_date, public, additional_fields, remove_fields, process)

    def set_decision_stage(self, options = ['Accept (Oral)', 'Accept (Poster)', 'Reject'], start_date = None, due_date = None, public = False, release_to_authors = False, release_to_reviewers = False, email_authors = False):
        self.decision_stage = DecisionStage(options, start_date, due_date, public, release_to_authors, release_to_reviewers, email_authors)

    def set_submission_revision_stage(self, name='Revision', start_date=None, due_date=None, additional_fields={}, remove_fields=[], only_accepted=False, allow_author_reorder=False):
        self.submission_revision_stage = SubmissionRevisionStage(name, start_date, due_date, additional_fields, remove_fields, only_accepted, allow_author_reorder)

    def use_legacy_invitation_id(self, legacy_invitation_id):
        self.conference.legacy_invitation_id = legacy_invitation_id

    def use_legacy_anonids(self, legacy_anonids):
        self.conference.legacy_anonids = legacy_anonids

    def set_request_form_id(self, id):
        self.conference.request_form_id = id

    def set_recruitment_reduced_load(self, reduced_load_options, default_reviewer_load):
        self.conference.reduced_load_on_decline = reduced_load_options
        self.conference.default_reviewer_load = default_reviewer_load

    def set_reviewer_identity_readers(self, readers):
        self.conference.reviewer_identity_readers = readers

    def set_area_chair_identity_readers(self, readers):
        self.conference.area_chair_identity_readers = readers

    def set_senior_area_chair_identity_readers(self, readers):
        self.conference.senior_area_chair_identity_readers = readers

    def get_result(self):

        id = self.conference.get_id()
        groups = self.__build_groups(id)
        for i, g in enumerate(groups[:-1]):
            self.webfield_builder.set_landing_page(g, groups[i-1] if i > 0 else None)

        host = self.client.get_group(id = 'host')
        root_id = groups[0].id
        if root_id == root_id.lower():
            root_id = groups[1].id
        writable = host.details.get('writable') if host.details else True
        if writable:
            self.client.add_members_to_group(host, root_id)

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

        home_group = groups[-1]
        parent_group_id = groups[-2].id if len(groups) > 1 else ''
        groups[-1] = self.webfield_builder.set_home_page(conference = self.conference, group = home_group, layout = self.conference.layout, options = { 'parent_group_id': parent_group_id })

        self.conference.set_conference_groups(groups)
        if self.conference.use_senior_area_chairs:
            self.conference.set_senior_area_chair_recruitment_groups()
        if self.conference.use_area_chairs:
            self.conference.set_area_chair_recruitment_groups()
        self.conference.set_reviewer_recruitment_groups()

        for s in self.bid_stages:
            self.conference.set_bid_stage(s)

        if self.expertise_selection_stage:
            self.conference.set_expertise_selection_stage(self.expertise_selection_stage)

        if self.registration_stage:
            self.conference.set_registration_stage(self.registration_stage)

        if self.review_stage:
            self.conference.set_review_stage(self.review_stage)

        if self.review_rebuttal_stage:
            self.conference.set_review_rebuttal_stage(self.review_rebuttal_stage)

        if self.comment_stage:
            self.conference.set_comment_stage(self.comment_stage)

        if self.meta_review_stage:
            self.conference.set_meta_review_stage(self.meta_review_stage)

        if self.decision_stage:
            self.conference.set_decision_stage(self.decision_stage)

        return self.conference
