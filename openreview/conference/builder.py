from __future__ import absolute_import

import time
import datetime
import re
from enum import Enum
from tqdm import tqdm
from .. import openreview
from .. import tools
from . import webfield
from . import invitation
from . import matching


class Conference(object):

    def __init__(self, client):
        self.client = client
        self.request_form_id = None
        self.new = False
        self.use_area_chairs = False
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
        self.bidpage_header = {}
        self.invitation_builder = invitation.InvitationBuilder(client)
        self.webfield_builder = webfield.WebfieldBuilder(client)
        self.authors_name = 'Authors'
        self.reviewers_name = 'Reviewers'
        self.area_chairs_name = 'Area_Chairs'
        self.program_chairs_name = 'Program_Chairs'
        self.recommendation_name = 'Recommendation'
        self.submission_stage = SubmissionStage()
        self.bid_stage = BidStage()
        self.expertise_selection_stage = ExpertiseSelectionStage()
        self.registration_stage = RegistrationStage()
        self.review_stage = ReviewStage()
        self.comment_stage = CommentStage()
        self.meta_review_stage = MetaReviewStage()
        self.decision_stage = DecisionStage()
        self.layout = 'tabs'
        self.enable_reviewer_reassignment = False
        self.reduced_load_on_decline = []
        self.default_reviewer_load = 0

    def __create_group(self, group_id, group_owner_id, members = [], is_signatory = True, public = False):
        group = tools.get_group(self.client, id = group_id)
        if group is None:
            return self.client.post_group(openreview.Group(
                id = group_id,
                readers = ['everyone'] if public else [self.id, group_owner_id, group_id],
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

    def __set_expertise_selection_page(self):
        expertise_selection_invitation = tools.get_invitation(self.client, self.get_expertise_selection_id())
        if expertise_selection_invitation:
            return self.webfield_builder.set_expertise_selection_page(self, expertise_selection_invitation)

    def __set_bid_page(self):
        """
        Set a webfield to each available bid invitation
        """
        bid_invitation = tools.get_invitation(self.client, self.get_bid_id(group_id=self.get_reviewers_id()))
        if bid_invitation:
            self.webfield_builder.set_bid_page(self, bid_invitation, self.get_reviewers_id(), self.bid_stage.request_count, self.bid_stage.instructions)

        if self.use_area_chairs:
            bid_invitation = tools.get_invitation(self.client, self.get_bid_id(group_id=self.get_area_chairs_id()))
            if bid_invitation:
                self.webfield_builder.set_bid_page(self, bid_invitation, self.get_area_chairs_id(), self.bid_stage.ac_request_count, self.bid_stage.instructions)

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
        return self.invitation_builder.set_submission_invitation(self)

    def __create_expertise_selection_stage(self):

        self.invitation_builder.set_expertise_selection_invitation(self)
        return self.__set_expertise_selection_page()

    def __create_registration_stage(self):
        return self.invitation_builder.set_registration_invitation(self)

    def __create_bid_stage(self):

        self.invitation_builder.set_bid_invitation(self)
        return self.__set_bid_page()

    def __create_review_stage(self):

        notes = list(self.get_submissions())
        return self.invitation_builder.set_review_invitation(self, notes)

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
        self.bid_stage = stage
        return self.__create_bid_stage()

    def set_review_stage(self, stage):
        self.review_stage = stage
        return self.__create_review_stage()

    def set_comment_stage(self, stage):
        self.comment_stage = stage
        return self.__create_comment_stage()

    def set_meta_review_stage(self, stage):
        self.meta_review_stage = stage
        return self.__create_meta_review_stage()

    def set_decision_stage(self, stage):
        self.decision_stage = stage
        return self.__create_decision_stage()

    def set_area_chairs_name(self, name):
        if self.use_area_chairs:
            self.area_chairs_name = name
        else:
            raise openreview.OpenReviewException('Venue\'s "has_area_chairs" setting is disabled')

    def set_program_chairs_name(self, name):
        self.program_chairs_name = name

    def get_program_chairs_id(self):
        return self.id + '/' + self.program_chairs_name

    def get_reviewers_id(self, number = None):
        reviewers_id = self.id + '/'
        if number:
            # TODO: Remove the "Reviewers" label from the end of this group as this forces individual groups to be "PaperX/Reviewers"
            reviewers_id = reviewers_id + 'Paper' + str(number) + '/Reviewers'
        else:
            reviewers_id = reviewers_id + self.reviewers_name
        return reviewers_id

    def get_reviewers_name(self, pretty=True):
        if pretty:
            return self.reviewers_name.replace('_', ' ')
        return self.reviewers_name

    def get_area_chairs_name(self, pretty=True):
        if pretty:
            return self.area_chairs_name.replace('_', ' ')
        return self.area_chairs_name

    def get_authors_id(self, number = None):
        authors_id = self.id + '/'
        if number:
            authors_id = authors_id + 'Paper' + str(number) + '/'

        authors_id = authors_id + self.authors_name
        return authors_id

    def get_area_chairs_id(self, number = None):
        area_chairs_id = self.id + '/'
        if number:
            # TODO: Remove the "Area_Chairs" label from the end of this group as this forces individual groups to be "PaperX/Area_Chairs"
            area_chairs_id = area_chairs_id + 'Paper' + str(number) + '/Area_Chairs'
        else:
            area_chairs_id = area_chairs_id + self.area_chairs_name
        return area_chairs_id

    def get_committee(self, number = None, submitted_reviewers = False, with_authors = False):
        committee = []

        if with_authors:
            committee.append(self.get_authors_id(number))

        if submitted_reviewers:
            committee.append(self.get_reviewers_id(number) + '/Submitted')
        else:
            committee.append(self.get_reviewers_id(number))

        if self.use_area_chairs:
            committee.append(self.get_area_chairs_id(number))

        committee.append(self.get_program_chairs_id())

        return committee

    def get_submission_id(self):
        return self.submission_stage.get_submission_id(self)

    def get_blind_submission_id(self):
        return self.submission_stage.get_blind_submission_id(self)

    def get_expertise_selection_id(self):
        return self.get_invitation_id(self.expertise_selection_stage.name)

    def get_bid_id(self, group_id):
        return self.get_invitation_id(self.bid_stage.name, prefix=group_id)

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

    def get_paper_assignment_id(self, group_id):
        return self.get_invitation_id('Paper_Assignment', prefix=group_id)

    def get_affinity_score_id(self, group_id):
        return self.get_invitation_id('Affinity_Score', prefix=group_id)

    def get_elmo_score_id(self, group_id):
        return self.get_invitation_id('ELMo_Score', prefix=group_id)

    def get_conflict_score_id(self, group_id):
        return self.get_invitation_id('Conflict', prefix=group_id)

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

    def set_bidpage_header(self, header):
        self.bidpage_header = header
        return self.__set_bid_page

    def get_bidpage_header(self):
        return self.bidpage_header

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

    def get_submissions(self, accepted = False, details = None, sort = None):
        invitation = self.get_blind_submission_id()
        notes = list(tools.iterget_notes(self.client, invitation = invitation, details = details, sort = sort))
        if accepted:
            decisions = tools.iterget_notes(self.client, invitation = self.get_invitation_id(self.decision_stage.name, '.*'))
            accepted_forums = [d.forum for d in decisions if d.content['decision'].startswith('Accept')]
            accepted_notes = [n for n in notes if n.id in accepted_forums]
            return accepted_notes
        return notes

    ## Deprecated
    def open_submissions(self):
        return self.__create_submission_stage()

    def close_submissions(self):

        # Expire invitation
        invitation = self.__expire_invitation(self.get_submission_id())
        # update submission due date
        if self.submission_stage.due_date and (
            tools.datetime_millis(self.submission_stage.due_date) > tools.datetime_millis(datetime.datetime.utcnow())):
            self.submission_stage.due_date = datetime.datetime.utcnow()

        # Add venue to active venues
        active_venues_group = self.client.get_group(id = 'active_venues')
        self.client.add_members_to_group(active_venues_group, [self.get_id()])

        return invitation

    def create_withdraw_invitations(self, reveal_authors=False, reveal_submission=False, email_pcs=False):

        if reveal_submission and not self.submission_stage.public:
            raise openreview.OpenReviewException('Can not reveal withdrawn submissions that are not originally public')

        if not reveal_authors and not self.submission_stage.double_blind:
            raise openreview.OpenReviewException('Can not hide authors of single blind submissions')

        return self.invitation_builder.set_withdraw_invitation(self, reveal_authors, reveal_submission, email_pcs)

    def create_desk_reject_invitations(self, reveal_authors=False, reveal_submission=False):

        if reveal_submission and not self.submission_stage.public:
            raise openreview.OpenReviewException('Can not reveal desk-rejected submissions that are not originally public')

        if not reveal_authors and not self.submission_stage.double_blind:
            raise openreview.OpenReviewException('Can not hide authors of single blind submissions')

        return self.invitation_builder.set_desk_reject_invitation(self, reveal_authors, reveal_submission)

    def create_paper_groups(self, authors=False, reviewers=False, area_chairs=False):

        notes_iterator = self.get_submissions(sort='number:asc', details='original')
        author_group_ids = []

        for n in notes_iterator:
            # Paper group
            group = self.__create_group(
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
                self.__create_group(
                    self.get_reviewers_id(number=n.number),
                    self.get_area_chairs_id(number=n.number) if self.use_area_chairs else self.id,
                    is_signatory = False)

                # Reviewers Submitted Paper group
                self.__create_group(
                    self.get_reviewers_id(number=n.number) + '/Submitted',
                    self.get_area_chairs_id(number=n.number) if self.use_area_chairs else self.id,
                    is_signatory = False)

            # Area Chairs Paper group
            if self.use_area_chairs and area_chairs:
                self.__create_group(self.get_area_chairs_id(number=n.number), self.id)

        if author_group_ids:
            self.__create_group(self.get_authors_id(), self.id, author_group_ids, public=True)


    def create_blind_submissions(self, force=False, hide_fields=[]):

        if not self.submission_stage.double_blind:
            raise openreview.OpenReviewException('Conference is not double blind')

        if not force and self.submission_stage.due_date and (tools.datetime_millis(self.submission_stage.due_date) > tools.datetime_millis(datetime.datetime.utcnow())):
            raise openreview.OpenReviewException('Submission invitation is still due. Aborted blind note creation!')

        submissions_by_original = { note.original: note for note in self.get_submissions() }

        self.invitation_builder.set_blind_submission_invitation(self, hide_fields)
        blinded_notes = []

        for note in tools.iterget_notes(self.client, invitation = self.get_submission_id(), sort = 'number:asc'):
            blind_note = submissions_by_original.get(note.id)
            if not blind_note:

                blind_content = {
                    'authors': ['Anonymous'],
                    'authorids': [self.get_authors_id(number=note.number)],
                    '_bibtex': None
                }

                for field in hide_fields:
                    blind_content[field] = ''

                blind_note = openreview.Note(
                    id = None,
                    original= note.id,
                    invitation= self.get_blind_submission_id(),
                    forum=None,
                    signatures= [self.id],
                    writers= [self.id],
                    readers= self.submission_stage.get_blind_readers(self, note.number),
                    content= blind_content)

                blind_note = self.client.post_note(blind_note)

                if self.submission_stage.public:
                    blind_content['_bibtex'] = tools.get_bibtex(note = note,
                        venue_fullname = self.name,
                        url_forum=blind_note.id,
                        year=str(self.get_year()),
                        baseurl=self.client.baseurl)

                    blind_note.content = blind_content

                    blind_note = self.client.post_note(blind_note)
            blinded_notes.append(blind_note)

        ## We should only create the author groups
        self.create_paper_groups(authors=True, reviewers=True, area_chairs=True)

        # Update PC console with double blind submissions
        pc_group = self.client.get_group(self.get_program_chairs_id())
        self.webfield_builder.edit_web_string_value(pc_group, 'BLIND_SUBMISSION_ID', self.get_blind_submission_id())

        return blinded_notes

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

    def open_paper_ranking(self, start_date=None, due_date=None):

        invitations = []
        invitation = self.invitation_builder.set_paper_ranking_invitation(self, self.get_reviewers_id(), start_date, due_date)
        invitations.append(invitation)

        if self.use_area_chairs:
            invitation = self.invitation_builder.set_paper_ranking_invitation(self, self.get_area_chairs_id(), start_date, due_date)
            invitations.append(invitation)

        return invitations

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
        invitation = tools.get_invitation(self.client, self.get_submission_id())
        if invitation:
            notes = self.get_submissions(accepted=only_accepted)
            return self.invitation_builder.set_revise_submission_invitation(self, notes, name, start_date, due_date, invitation.reply['content'], additional_fields, remove_fields)

    def open_revise_reviews(self, name = 'Revision', start_date = None, due_date = None, additional_fields = {}, remove_fields = []):
        invitation = self.get_invitation_id(self.review_stage.name, '.*')
        review_iterator = tools.iterget_notes(self.client, invitation = invitation)
        return self.invitation_builder.set_revise_review_invitation(self, review_iterator, name, start_date, due_date, additional_fields, remove_fields)

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

    def set_area_chairs(self, emails = []):
        if self.use_area_chairs:
            self.__create_group(self.get_area_chairs_id(), self.id, emails)

            return self.__set_area_chair_page()
        else:
            raise openreview.OpenReviewException('Conference "has_area_chairs" setting is disabled')

    def set_area_chair_recruitment_groups(self):
        if self.use_area_chairs:
            parent_group_id = self.get_area_chairs_id()
            parent_group_declined_id = parent_group_id + '/Declined'
            parent_group_invited_id = parent_group_id + '/Invited'
            parent_group_accepted_id = parent_group_id

            pcs_id = self.get_program_chairs_id()
            parent_group_accepted_group = self.__create_group(parent_group_accepted_id, pcs_id)
            parent_group_declined_group = self.__create_group(parent_group_declined_id, pcs_id)
            parent_group_invited_group = self.__create_group(parent_group_invited_id, pcs_id)
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

    def set_reviewers(self, emails = []):
        self.__create_group(
            group_id = self.get_reviewers_id(),
            group_owner_id = self.get_area_chairs_id() if self.use_area_chairs else self.id,
            members = emails)

        return self.__set_reviewer_page()

    def set_authors(self):
        authors_group = self.__create_group(self.get_authors_id(), self.id, public=True)
        return self.webfield_builder.set_author_page(self, authors_group)

    def setup_matching(self, is_area_chair=False, affinity_score_file=None, tpms_score_file=None, elmo_score_file=None, build_conflicts=False):
        if is_area_chair:
            match_group = self.client.get_group(self.get_area_chairs_id())
        else:
            match_group = self.client.get_group(self.get_reviewers_id())
        conference_matching = matching.Matching(self, match_group)
        return conference_matching.setup(affinity_score_file, tpms_score_file, elmo_score_file, build_conflicts)

    def set_assignment(self, user, number, is_area_chair = False):

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
                parent_label = 'Reviewers',
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

    def set_assignments(self, assignment_title, is_area_chair=False, enable_reviewer_reassignment=False, overwrite=False):
        if is_area_chair:
            invitation = tools.get_invitation(self.client, self.get_invitation_id(self.meta_review_stage.name))
        else:
            invitation = tools.get_invitation(self.client, self.get_invitation_id(self.review_stage.name))

        if invitation:
            activation_date = invitation.cdate or invitation.tcdate
            if activation_date < tools.datetime_millis(datetime.datetime.now()):
                raise openreview.OpenReviewException('{} stage has started.'.format('MetaReview' if is_area_chair else 'Review'))

        if is_area_chair:
            match_group = self.client.get_group(self.get_area_chairs_id())
        else:
            match_group = self.client.get_group(self.get_reviewers_id())
        conference_matching = matching.Matching(self, match_group)
        self.set_reviewer_reassignment(enabled=enable_reviewer_reassignment)
        return conference_matching.deploy(assignment_title, is_area_chair, overwrite)


    def set_recruitment_reduced_load(self, reduced_load_options):
        self.reduced_load_on_decline = reduced_load_options

    def recruit_reviewers(self, invitees = [], title = None, message = None, reviewers_name = 'Reviewers', reviewer_accepted_name = None, remind = False, invitee_names = [], baseurl = ''):

        pcs_id = self.get_program_chairs_id()
        reviewers_id = self.id + '/' + reviewers_name
        reviewers_declined_id = reviewers_id + '/Declined'
        reviewers_invited_id = reviewers_id + '/Invited'
        reviewers_accepted_id = reviewers_id
        if reviewer_accepted_name:
            reviewers_accepted_id = reviewers_id + '/' + reviewer_accepted_name
        hash_seed = '1234'
        invitees = [e.lower() if '@' in e else e for e in invitees]

        reviewers_accepted_group = self.__create_group(reviewers_accepted_id, pcs_id)
        reviewers_declined_group = self.__create_group(reviewers_declined_id, pcs_id)
        reviewers_invited_group = self.__create_group(reviewers_invited_id, pcs_id)

        options = {
            'reviewers_name': reviewers_name,
            'reviewers_accepted_id': reviewers_accepted_id,
            'reviewers_declined_id': reviewers_declined_id,
            'hash_seed': hash_seed
        }
        if options['reviewers_name'] == 'Reviewers' and self.reduced_load_on_decline:
            options['reduced_load_on_decline'] = self.reduced_load_on_decline
            invitation = self.invitation_builder.set_reviewer_reduced_load_invitation(self, options)
            invitation = self.webfield_builder.set_reduced_load_page(self.id, invitation, self.get_homepage_options())

        invitation = self.invitation_builder.set_reviewer_recruiter_invitation(self, options)
        invitation = self.webfield_builder.set_recruit_page(self.id, invitation, self.get_homepage_options())
        recruit_message = '''Dear {name},

        You have been nominated by the program chair committee of ''' + self.short_name + ''' to serve as a reviewer.  As a respected researcher in the area, we hope you will accept and help us make the conference a success.

        Reviewers are also welcome to submit papers, so please also consider submitting to the conference!

        We will be using OpenReview.net and a reviewing process that we hope will be engaging and inclusive of the whole community.

        The success of the conference depends on the quality of the reviewing process and ultimately on the quality and dedication of the reviewers. We hope you will accept our invitation.

        To ACCEPT the invitation, please click on the following link:

        {accept_url}

        To DECLINE the invitation, please click on the following link:

        {decline_url}

        Please answer within 10 days.

        If you accept, please make sure that your OpenReview account is updated and lists all the emails you are using.  Visit http://openreview.net/profile after logging in.

        If you have any questions, please contact us at info@openreview.net.

        Cheers!

        Program Chairs

        '''
        recruit_message_subj = self.id + ': Invitation to Review'

        if title:
            recruit_message_subj = title

        if message:
            recruit_message = message

        if remind:
            remind_reviewers = list(set(reviewers_invited_group.members) - set(reviewers_declined_group.members) - set(reviewers_accepted_group.members))
            print ('Sending reminders for recruitment invitations')
            for reviewer_id in tqdm(remind_reviewers):
                reviewer_name = 'invitee'
                if reviewer_id.startswith('~') :
                    reviewer_name =  re.sub('[0-9]+', '', reviewer_id.replace('~', '').replace('_', ' '))
                elif (reviewer_id in invitees) and invitee_names:
                    reviewer_name = invitee_names[invitees.index(reviewer_id)]

                tools.recruit_reviewer(self.client, reviewer_id, reviewer_name,
                    hash_seed,
                    invitation.id,
                    recruit_message,
                    'Reminder: ' + recruit_message_subj,
                    reviewers_invited_id,
                    verbose = False,
                    baseurl = baseurl)

        print ('Sending recruitment invitations')
        for index, email in enumerate(tqdm(invitees)):
            if email not in set(reviewers_invited_group.members):
                name = invitee_names[index] if (invitee_names and index < len(invitee_names)) else None
                if not name:
                    name = re.sub('[0-9]+', '', email.replace('~', '').replace('_', ' ')) if email.startswith('~') else 'invitee'
                tools.recruit_reviewer(self.client, email, name,
                    hash_seed,
                    invitation.id,
                    recruit_message,
                    recruit_message_subj,
                    reviewers_invited_id,
                    verbose = False,
                    baseurl = baseurl)

        return self.client.get_group(id = reviewers_invited_id)

    def set_homepage_decisions(self, invitation_name = 'Decision', decision_heading_map = None):
        home_group = self.client.get_group(self.id)
        options = self.get_homepage_options()
        options['blind_submission_id'] = self.get_blind_submission_id()
        options['decision_invitation_regex'] = self.get_invitation_id(invitation_name, '.*')
        options['withdrawn_submission_id'] = self.submission_stage.get_withdrawn_submission_id(self)
        options['desk_rejected_submission_id'] = self.submission_stage.get_desk_rejected_submission_id(self)

        if not decision_heading_map:
            decision_heading_map = {}
            invitations = self.client.get_invitations(regex = self.get_invitation_id(invitation_name, '.*'), limit = 1)
            if invitations:
                for option in invitations[0].reply['content']['decision']['value-radio']:
                    decision_heading_map[option] = option + ' Papers'
        options['decision_heading_map'] = decision_heading_map

        self.webfield_builder.set_home_page(group = home_group, layout = 'decisions', options = options)

class SubmissionStage(object):

    def __init__(
            self,
            name='Submission',
            start_date=None,
            due_date=None,
            public=False,
            double_blind=False,
            additional_fields={},
            remove_fields=[],
            subject_areas=[]
        ):

        self.start_date = start_date
        self.due_date = due_date
        self.name = name
        self.public = public
        self.double_blind = double_blind
        self.additional_fields = additional_fields
        self.remove_fields = remove_fields
        self.subject_areas = subject_areas

    def get_readers(self, conference):
        if self.double_blind:
            return {
                'values-copied': [
                    conference.get_id(),
                    '{content.authorids}',
                    '{signatures}'
                ]
            }

        if self.public:
            return {
                'values': ['everyone']
            }

        return {
            'values-copied': [
                conference.get_id(),
                '{content.authorids}',
                '{signatures}'
            ] + conference.get_committee()
        }

    def get_blind_readers(self, conference, number):
        if self.public:
            return ['everyone']
        else:
            readers = conference.get_committee()
            readers.insert(0, conference.get_authors_id(number = number))
            return readers

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

class ExpertiseSelectionStage(object):

    def __init__(self, start_date = None, due_date = None):
        self.start_date = start_date
        self.due_date = due_date
        self.name = 'Expertise_Selection'

class BidStage(object):

    def __init__(self, start_date=None, due_date=None, request_count=50, use_affinity_score=False, instructions=False, ac_request_count=None):
        self.start_date = start_date
        self.due_date = due_date
        self.name = 'Bid'
        self.request_count = request_count
        self.use_affinity_score = use_affinity_score
        self.instructions=instructions
        self.ac_request_count=ac_request_count if ac_request_count else request_count


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
        remove_fields = []
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
        signature_regex = conference.get_id() + '/Paper' + str(number) + '/AnonReviewer[0-9]+'

        if self.allow_de_anonymization:
            signature_regex = signature_regex + '|~.*'

        return signature_regex


class CommentStage(object):

    def __init__(self, official_comment_name = None, start_date = None, allow_public_comments = False, anonymous = False, unsubmitted_reviewers = False, reader_selection = False, email_pcs = False, authors=False):
        self.official_comment_name = official_comment_name if official_comment_name else 'Official_Comment'
        self.public_name = 'Public_Comment'
        self.start_date = start_date
        self.allow_public_comments = allow_public_comments
        self.anonymous = anonymous
        self.unsubmitted_reviewers = unsubmitted_reviewers
        self.reader_selection = reader_selection
        self.email_pcs = email_pcs
        self.authors = authors

class MetaReviewStage(object):

    def __init__(self, start_date = None, due_date = None, public = False, additional_fields = {}, process = None):
        self.start_date = start_date
        self.due_date = due_date
        self.name = 'Meta_Review'
        self.public = public
        self.additional_fields = additional_fields
        self.process = None

    def get_readers(self, conference, number):

        if self.public:
            return ['everyone']

        readers = []

        if conference.use_area_chairs:
            readers.append(conference.get_area_chairs_id(number = number))

        readers.append(conference.get_program_chairs_id())

        return readers


class DecisionStage(object):

    def __init__(self, options = None, start_date = None, due_date = None, public = False, release_to_authors = False, release_to_reviewers = False):
        if not options:
            options = ['Accept (Oral)', 'Accept (Poster)', 'Reject']
        self.options = options
        self.start_date = start_date
        self.due_date = due_date
        self.name = 'Decision'
        self.public = public
        self.release_to_authors = release_to_authors
        self.release_to_reviewers = release_to_reviewers

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

    def __init__(self, client):
        self.client = client
        self.conference = Conference(client)
        self.webfield_builder = webfield.WebfieldBuilder(client)
        self.override_homepage = False
        self.submission_stage = None
        self.expertise_selection_stage = None
        self.registration_stage = None
        self.bid_stage = None
        self.review_stage = None
        self.comment_stage = None
        self.meta_review_stage = None
        self.decision_stage = None
        self.program_chairs_ids = []

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

    def set_override_homepage(self, override):
        self.override_homepage = override

    def has_area_chairs(self, has_area_chairs):
        self.conference.has_area_chairs(has_area_chairs)

    def enable_reviewer_reassignment(self, enable):
        self.conference.enable_reviewer_reassignment = enable

    def set_submission_stage(
            self,
            name='Submission',
            start_date=None,
            due_date=None,
            public=False,
            double_blind=False,
            additional_fields={},
            remove_fields=[],
            subject_areas=[]
        ):

        self.submission_stage = SubmissionStage(
            name,
            start_date,
            due_date,
            public,
            double_blind,
            additional_fields,
            remove_fields,
            subject_areas
        )

    def set_expertise_selection_stage(self, start_date = None, due_date = None):
        self.expertise_selection_stage = ExpertiseSelectionStage(start_date, due_date)

    def set_registration_stage(self, name = 'Registration', start_date = None, due_date = None, additional_fields = {}, ac_additional_fields = {}, instructions = None, ac_instructions = None):
        default_instructions = 'Help us get to know our committee better and the ways to make the reviewing process smoother by answering these questions. If you don\'t see the form below, click on the blue "Registration" button.\n\nLink to Profile: https://openreview.net/profile?mode=edit \nLink to Expertise Selection interface: https://openreview.net/invitation?id={conference_id}/-/Expertise_Selection'.format(conference_id = self.conference.get_id())
        reviewer_instructions = instructions if instructions else default_instructions
        ac_instructions = ac_instructions if ac_instructions else default_instructions
        self.registration_stage=RegistrationStage(name, start_date, due_date, additional_fields, ac_additional_fields, reviewer_instructions, ac_instructions)

    def set_bid_stage(self, start_date = None, due_date = None, request_count = 50, use_affinity_score = False, instructions = False, ac_request_count = None):
        self.bid_stage = BidStage(start_date, due_date, request_count, use_affinity_score, instructions, ac_request_count)

    def set_review_stage(self, start_date = None, due_date = None, name = None, allow_de_anonymization = False, public = False, release_to_authors = False, release_to_reviewers = ReviewStage.Readers.REVIEWER_SIGNATURE, email_pcs = False, additional_fields = {}, remove_fields = []):
        self.review_stage = ReviewStage(start_date, due_date, name, allow_de_anonymization, public, release_to_authors, release_to_reviewers, email_pcs, additional_fields, remove_fields)

    def set_comment_stage(self, name = None, start_date = None, allow_public_comments = False, anonymous = False, unsubmitted_reviewers = False, reader_selection = False, email_pcs = False, authors = False ):
        self.comment_stage = CommentStage(name, start_date, allow_public_comments, anonymous, unsubmitted_reviewers, reader_selection, email_pcs, authors)

    def set_meta_review_stage(self, start_date = None, due_date = None, public = False, additional_fields = {}, process = None):
        self.meta_review_stage = MetaReviewStage(start_date, due_date, public, additional_fields, process)

    def set_decision_stage(self, options = ['Accept (Oral)', 'Accept (Poster)', 'Reject'], start_date = None, due_date = None, public = False, release_to_authors = False, release_to_reviewers = False):
        self.decision_stage = DecisionStage(options, start_date, due_date, public, release_to_authors, release_to_reviewers)

    def use_legacy_invitation_id(self, legacy_invitation_id):
        self.conference.legacy_invitation_id = legacy_invitation_id

    def set_request_form_id(self, id):
        self.conference.request_form_id = id

    def set_recruitment_reduced_load(self, reduced_load_options, default_reviewer_load):
        self.conference.reduced_load_on_decline = reduced_load_options
        self.conference.default_reviewer_load = default_reviewer_load

    def get_result(self):

        id = self.conference.get_id()
        groups = self.__build_groups(id)
        for g in groups[:-1]:
            # set a landing page only where there is not special webfield
            writable = g.details.get('writable') if g.details else True
            if writable and (not g.web or 'VENUE_LINKS' in g.web):
                self.webfield_builder.set_landing_page(g)

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
        if self.conference.use_area_chairs:
            self.conference.set_area_chairs()

        home_group = groups[-1]
        writable = home_group.details.get('writable') if home_group.details else True
        if writable and (not home_group.web or self.override_homepage):
            options = self.conference.get_homepage_options()
            options['reviewers_name'] = self.conference.reviewers_name
            options['area_chairs_name'] = self.conference.area_chairs_name
            options['reviewers_id'] = self.conference.get_reviewers_id()
            options['authors_id'] = self.conference.get_authors_id()
            options['program_chairs_id'] = self.conference.get_program_chairs_id()
            options['area_chairs_id'] = self.conference.get_area_chairs_id()
            options['submission_id'] = self.conference.get_submission_id()
            options['blind_submission_id'] = self.conference.get_blind_submission_id()
            options['withdrawn_submission_id'] = self.conference.submission_stage.get_withdrawn_submission_id(self.conference)
            options['desk_rejected_submission_id'] = self.conference.submission_stage.get_desk_rejected_submission_id(self.conference)
            options['public'] = self.conference.submission_stage.public
            groups[-1] = self.webfield_builder.set_home_page(group = home_group, layout = self.conference.layout, options = options)

        self.conference.set_conference_groups(groups)
        if self.conference.use_area_chairs:
            self.conference.set_area_chair_recruitment_groups()
        self.conference.set_reviewer_recruitment_groups()

        if self.bid_stage:
            self.conference.set_bid_stage(self.bid_stage)

        if self.expertise_selection_stage:
            self.conference.set_expertise_selection_stage(self.expertise_selection_stage)

        if self.registration_stage:
            self.conference.set_registration_stage(self.registration_stage)

        if self.review_stage:
            self.conference.set_review_stage(self.review_stage)

        if self.comment_stage:
            self.conference.set_comment_stage(self.comment_stage)

        if self.meta_review_stage:
            self.conference.set_meta_review_stage(self.meta_review_stage)

        if self.decision_stage:
            self.conference.set_decision_stage(self.decision_stage)

        return self.conference
