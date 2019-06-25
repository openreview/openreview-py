from __future__ import absolute_import

import time
import re
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
        self.homepage_header = {}
        self.authorpage_header = {}
        self.reviewerpage_header = {}
        self.areachairpage_header = {}
        self.bidpage_header = {}
        self.invitation_builder = invitation.InvitationBuilder(client)
        self.webfield_builder = webfield.WebfieldBuilder(client)
        self.authors_name = 'Authors'
        self.reviewers_name = 'Reviewers'
        self.area_chairs_name = 'Area_Chairs'
        self.program_chairs_name = 'Program_Chairs'
        self.recommendation_name = 'Recommendation'
        self.registration_name = 'Registration'
        self.submission_stage = SubmissionStage()
        self.bid_stage = BidStage()
        self.review_stage = ReviewStage()
        self.comment_stage = CommentStage()
        self.meta_review_stage = MetaReviewStage()
        self.decision_stage = DecisionStage()
        self.layout = 'tabs'

    def __create_group(self, group_id, group_owner_id, members = [], is_signatory = True):

        group = tools.get_group(self.client, id = group_id)
        if group is None:
            return self.client.post_group(openreview.Group(id = group_id,
                readers = [self.id, group_owner_id, group_id],
                writers = [self.id],
                signatures = [self.id],
                signatories = [group_id] if is_signatory else [self.id],
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

    def __set_program_chair_page(self):
        program_chairs_group = tools.get_group(self.client, self.get_program_chairs_id())
        if program_chairs_group:
            return self.webfield_builder.set_program_chair_page(self, program_chairs_group)

    def __set_bid_page(self):
        bid_invitation = self.client.get_invitation(self.get_bid_id())
        if bid_invitation:
            return self.webfield_builder.set_bid_page(self, bid_invitation)

    def __set_recommendation_page(self):
        recommendation_invitation = self.client.get_invitation(self.get_recommendation_id())
        if recommendation_invitation:
            return self.webfield_builder.set_recommendation_page(self, recommendation_invitation)

    def __expire_invitation(self, invitation_id):
        # Get invitation
        invitation = self.client.get_invitation(id = invitation_id)

        # Force the expdate
        now = round(time.time() * 1000)
        if not invitation.expdate or invitation.expdate > now:
            invitation.expdate = now
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

    def __create_bid_stage(self):

        self.invitation_builder.set_bid_invitation(self)
        return self.__set_bid_page()

    def __create_review_stage(self):

        self.set_authors()
        self.set_reviewers()
        notes = list(self.get_submissions())
        invitations = self.invitation_builder.set_review_invitation(self, notes)
        ## Create submitted groups if they don't exist
        for n in notes:
            self.__create_group(self.get_id() + '/Paper{}/Reviewers'.format(n.number), self.get_program_chairs_id())
            self.__create_group(self.get_id() + '/Paper{}/Reviewers/Submitted'.format(n.number), self.get_program_chairs_id())
        return invitations

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

    def set_reviewers_name(self, name):
        self.reviewers_name = name

    def set_submission_stage(self, stage):
        self.submission_stage = stage
        return self.__create_submission_stage()

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
            raise openreview.OpenReviewException('Conference "has_area_chairs" setting is disabled')

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

    def get_bid_id(self):
        return self.get_invitation_id(self.bid_stage.name)

    def get_recommendation_id(self, number = None):
        return self.get_invitation_id(self.recommendation_name, number)

    def get_registration_id(self):
        return self.get_invitation_id(self.registration_name)

    def get_invitation_id(self, name, number = None):
        invitation_id = self.id
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

    def get_paper_assignment_id (self):
        return self.get_invitation_id('Paper_Assignment')

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

    def set_homepage_layout(self, layout):
        self.layout = layout

    def has_area_chairs(self, has_area_chairs):
        self.use_area_chairs = has_area_chairs

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
        return options

    def get_submissions(self, accepted = False, details = None):
        invitation = self.get_blind_submission_id()
        notes = list(tools.iterget_notes(self.client, invitation = invitation, details = details))
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

        # Add venue to active venues
        active_venues_group = self.client.get_group(id = 'active_venues')
        self.client.add_members_to_group(active_venues_group, [self.get_id()])

        return invitation

    def create_blind_submissions(self):

        if not self.submission_stage.double_blind:
            raise openreview.OpenReviewException('Conference is not double blind')

        submissions_by_original = { note.original: note for note in self.get_submissions() }

        self.invitation_builder.set_blind_submission_invitation(self)
        blinded_notes = []

        for note in tools.iterget_notes(self.client, invitation = self.get_submission_id(), sort = 'number:asc'):
            blind_note = submissions_by_original.get(note.id)
            if not blind_note:
                blind_note = openreview.Note(
                    id = None,
                    original= note.id,
                    invitation= self.get_blind_submission_id(),
                    forum=None,
                    signatures= [self.id],
                    writers= [self.id],
                    readers= [self.id],
                    content= {
                        "authors": ['Anonymous'],
                        "authorids": [self.id],
                        "_bibtex": None
                    })

                blind_note = self.client.post_note(blind_note)

                blind_note.readers = self.submission_stage.get_blind_readers(self, blind_note.number)

                blind_note.content = {
                    'authorids': [self.get_authors_id(number = blind_note.number)],
                    'authors': ['Anonymous'],
                    '_bibtex': None #Create bibtext automatically
                }

                blind_note = self.client.post_note(blind_note)
            blinded_notes.append(blind_note)

        # Update page with double blind submissions
        self.__set_program_chair_page()
        return blinded_notes

    ## Deprecated
    def open_bids(self):
        return self.__create_bid_stage()

    def close_bids(self):
        return self.__expire_invitation(self.get_bid_id())

    def open_recommendations(self, start_date = None, due_date = None, reviewer_assingment_title = None):
        notes_iterator = self.get_submissions()
        assignment_notes_iterator = None

        if reviewer_assingment_title:
            assignment_notes_iterator = tools.iterget_notes(self.client, invitation = self.get_paper_assignment_id(), content = { 'title': reviewer_assingment_title })

        self.invitation_builder.set_recommendation_invitation(self, start_date, due_date, notes_iterator, assignment_notes_iterator)
        return self.__set_recommendation_page()

    def open_registration(self, start_date = None, due_date = None, with_area_chairs = False):
        return self.invitation_builder.set_registration_invitation(self, start_date, due_date, with_area_chairs)

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
        invitation = self.client.get_invitation(self.get_submission_id())
        notes = self.get_submissions(accepted=only_accepted)
        return self.invitation_builder.set_revise_submission_invitation(self, notes, name, start_date, due_date, invitation.reply['content'], additional_fields, remove_fields)

    def open_revise_reviews(self, name = 'Revision', start_date = None, due_date = None, additional_fields = {}, remove_fields = []):

        invitation = self.get_invitation_id(self.review_stage.name, '.*')
        review_iterator = tools.iterget_notes(self.client, invitation = invitation)
        return self.invitation_builder.set_revise_review_invitation(self, review_iterator, name, start_date, due_date, additional_fields, remove_fields)

    def close_revise_submissions(self, name):
        return self.__expire_invitations(name)

    def set_program_chairs(self, emails):
        self.__create_group(self.get_program_chairs_id(), self.id, emails)
        ## Give program chairs admin permissions
        self.__create_group(self.id, '~Super_User1', [self.get_program_chairs_id()])
        return self.__set_program_chair_page()

    def set_area_chairs(self, emails = []):
        if self.use_area_chairs:
            self.__create_group(self.get_area_chairs_id(), self.id, emails)

            notes_iterator = self.get_submissions()
            for n in notes_iterator:
                self.__create_group(self.get_area_chairs_id(number = n.number), self.id)

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
        parent_group_accepted_id = parent_group_id

        pcs_id = self.get_program_chairs_id()
        parent_group_accepted_group = self.__create_group(parent_group_accepted_id, pcs_id)
        parent_group_declined_group = self.__create_group(parent_group_declined_id, pcs_id)
        parent_group_invited_group = self.__create_group(parent_group_invited_id, pcs_id)

    def set_reviewers(self, emails = []):
        self.__create_group(self.get_reviewers_id(), self.id, emails)

        notes_iterator = self.get_submissions()

        for n in notes_iterator:
            self.__create_group(self.get_reviewers_id(number = n.number), self.id)

        return self.__set_reviewer_page()

    def set_authors(self):
        notes_iterator = self.get_submissions(details='original')
        author_group_ids = []

        for n in notes_iterator:
            group = self.__create_group('{conference_id}/Paper{number}'.format(conference_id = self.id, number = n.number), self.id, is_signatory = False)
            authorids = n.content.get('authorids')
            if n.details and n.details.get('original'):
                authorids = n.details['original']['content']['authorids']
            group = self.__create_group('{number_group}/{author_name}'.format(number_group = group.id, author_name = self.authors_name), self.id, authorids)
            author_group_ids.append(group.id)

        self.__create_group(self.get_authors_id(), self.id, author_group_ids)

    def setup_matching(self, affinity_score_file = None, tpms_score_file = None):
        conference_matching = matching.Matching(self)
        return conference_matching.setup(affinity_score_file, tpms_score_file)

    def set_assignment(self, user, number, is_area_chair = False):


        if is_area_chair:
            return tools.add_assignment(self.client,
            number,
            self.get_id(),
            user,
            parent_label = 'Area_Chairs',
            individual_label = 'Area_Chair')
        else:
            return tools.add_assignment(self.client,
            number,
            self.get_id(),
            user,
            parent_label = 'Reviewers',
            individual_label = 'AnonReviewer',
            individual_group_params = {
                'readers': [
                    self.get_id(),
                    self.get_program_chairs_id(),
                    self.get_area_chairs_id(number = number)
                ],
                'writers': [
                    self.get_id(),
                    self.get_program_chairs_id(),
                    self.get_area_chairs_id(number = number)
                ]
            },
            parent_group_params = {
                'readers': [
                    self.get_id(),
                    self.get_program_chairs_id(),
                    self.get_area_chairs_id(number = number)
                ],
                'writers': [
                    self.get_id(),
                    self.get_program_chairs_id(),
                    self.get_area_chairs_id(number = number)
                ]
            }, use_profile = True)

    def set_assignments(self, assingment_title):
        conference_matching = matching.Matching(self)
        return conference_matching.deploy(assingment_title)

    def recruit_reviewers(self, emails = [], title = None, message = None, reviewers_name = 'Reviewers', reviewer_accepted_name = None, remind = False, invitee_names = []):

        pcs_id = self.get_program_chairs_id()
        reviewers_id = self.id + '/' + reviewers_name
        reviewers_declined_id = reviewers_id + '/Declined'
        reviewers_invited_id = reviewers_id + '/Invited'
        reviewers_accepted_id = reviewers_id
        if reviewer_accepted_name:
            reviewers_accepted_id = reviewers_id + '/' + reviewer_accepted_name
        hash_seed = '1234'

        reviewers_accepted_group = self.__create_group(reviewers_accepted_id, pcs_id)
        reviewers_declined_group = self.__create_group(reviewers_declined_id, pcs_id)
        reviewers_invited_group = self.__create_group(reviewers_invited_id, pcs_id)

        options = {
            'reviewers_name': reviewers_name,
            'reviewers_accepted_id': reviewers_accepted_id,
            'reviewers_declined_id': reviewers_declined_id,
            'hash_seed': hash_seed
        }
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
            for reviewer in remind_reviewers:
                name =  re.sub('[0-9]+', '', reviewer.replace('~', '').replace('_', ' ')) if reviewer.startswith('~') else 'invitee'
                tools.recruit_reviewer(self.client, reviewer, name,
                    hash_seed,
                    invitation.id,
                    recruit_message,
                    'Reminder: ' + recruit_message_subj,
                    reviewers_invited_id,
                    verbose = False)

        for index, email in enumerate(emails):
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
                    verbose = False)

        return self.client.get_group(id = reviewers_invited_id)

    def set_homepage_decisions(self, invitation_name = 'Decision', decision_heading_map = None):
        home_group = self.client.get_group(self.id)
        options = self.get_homepage_options()
        options['blind_submission_id'] = self.get_blind_submission_id()
        options['decision_invitation_regex'] = self.get_invitation_id(invitation_name, '.*')
        if not decision_heading_map:
            decision_heading_map = {}
            invitations = self.client.get_invitations(regex = self.get_invitation_id(invitation_name, '.*'), limit = 1)
            if invitations:
                for option in invitations[0].reply['content']['decision']['value-radio']:
                    decision_heading_map[option] = option + ' Papers'
        options['decision_heading_map'] = decision_heading_map

        self.webfield_builder.set_home_page(group = home_group, layout = 'decisions', options = options)

class SubmissionStage(object):

    def __init__(self, name = 'Submission', start_date = None, due_date = None, public = False, double_blind = False, additional_fields = {}, remove_fields = [], subject_areas = []):

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

class BidStage(object):

    def __init__(self, start_date = None, due_date = None, request_count = 50):
        self.start_date = start_date
        self.due_date = due_date
        self.name = 'Bid'
        self.request_count = request_count

class ReviewStage(object):

    def __init__(self, start_date = None, due_date = None, name = None, allow_de_anonymization = False, public = False, release_to_authors = False, release_to_reviewers = False, email_pcs = False, additional_fields = {}):
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

    def get_readers(self, conference, number):

        if self.public:
            return ['everyone']

        readers = [ conference.get_program_chairs_id()]

        if conference.use_area_chairs:
            readers.append(conference.get_area_chairs_id(number = number))

        if self.release_to_reviewers:
            readers.append(conference.get_reviewers_id(number = number))
        else:
            readers.append(conference.get_reviewers_id(number = number) + '/Submitted')

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

    def __init__(self, start_date = None, allow_public_comments = False, anonymous = False, unsubmitted_reviewers = False, reader_selection = False, email_pcs = False):
        self.name = 'Comment'
        self.start_date = start_date
        self.allow_public_comments = allow_public_comments
        self.anonymous = anonymous
        self.unsubmitted_reviewers = unsubmitted_reviewers
        self.reader_selection = reader_selection
        self.email_pcs = email_pcs

class MetaReviewStage(object):

    def __init__(self, start_date = None, due_date = None, public = False, additional_fields = {}):
        self.start_date = start_date
        self.due_date = due_date
        self.name = 'Meta_Review'
        self.public = public
        self.additional_fields = additional_fields

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


class ConferenceBuilder(object):

    def __init__(self, client):
        self.client = client
        self.conference = Conference(client)
        self.webfield_builder = webfield.WebfieldBuilder(client)
        self.override_homepage = False
        self.submission_stage = None
        self.bid_stage = None
        self.review_stage = None
        self.comment_stage = None
        self.meta_review_stage = None
        self.decision_stage = None

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

    def set_conference_reviewers_name(self, name):
        self.conference.set_reviewers_name(name)

    def set_conference_area_chairs_name(self, name):
        self.conference.has_area_chairs(True)
        self.conference.set_area_chairs_name(name)

    def set_conference_program_chairs_name(self, name):
        self.conference.set_program_chairs_name(name)

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

    def set_submission_stage(self, name = 'Submission', start_date = None, due_date = None, public = False, double_blind = False, additional_fields = {}, remove_fields = [], subject_areas = []):
        self.submission_stage = SubmissionStage(name, start_date, due_date, public, double_blind, additional_fields, remove_fields, subject_areas)

    def set_bid_stage(self, start_date = None, due_date = None, request_count = 50):
        self.bid_stage = BidStage(start_date, due_date, request_count)

    def set_review_stage(self, start_date = None, due_date = None, name = None, allow_de_anonymization = False, public = False, release_to_authors = False, release_to_reviewers = False, email_pcs = False, additional_fields = {}):
        self.review_stage = ReviewStage(start_date, due_date, name, allow_de_anonymization, public, release_to_authors, release_to_reviewers, email_pcs, additional_fields)

    def set_comment_stage(self, start_date = None, allow_public_comments = False, anonymous = False, unsubmitted_reviewers = False, reader_selection = False, email_pcs = False):
        self.comment_stage = CommentStage(start_date, allow_public_comments, anonymous, unsubmitted_reviewers, reader_selection, email_pcs)

    def set_meta_review_stage(self, start_date = None, due_date = None, public = False, additional_fields = {}):
        self.meta_review_stage = MetaReviewStage(start_date, due_date, public, additional_fields)

    def set_decision_stage(self, options = ['Accept (Oral)', 'Accept (Poster)', 'Reject'], start_date = None, due_date = None, public = False, release_to_authors = False, release_to_reviewers = False):
        self.decision_stage = DecisionStage(options, start_date, due_date, public, release_to_authors, release_to_reviewers)

    def use_legacy_invitation_id(self, legacy_invitation_id):
        self.conference.legacy_invitation_id = legacy_invitation_id

    def set_request_form_id(self, id):
        self.conference.request_form_id = id

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

        if self.bid_stage:
            self.conference.set_bid_stage(self.bid_stage)

        if self.review_stage:
            self.conference.set_review_stage(self.review_stage)

        if self.comment_stage:
            self.conference.set_comment_stage(self.comment_stage)

        if self.meta_review_stage:
            self.conference.set_meta_review_stage(self.meta_review_stage)

        if self.decision_stage:
            self.conference.set_decision_stage(self.decision_stage)

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
            self.webfield_builder.set_home_page(group = home_group, layout = self.conference.layout, options = options)

        self.conference.set_conference_groups(groups)
        if self.conference.use_area_chairs:
            self.conference.set_area_chair_recruitment_groups()
        self.conference.set_reviewer_recruitment_groups()

        ## Author console
        authors_group = openreview.Group(id = self.conference.get_authors_id(),
            readers = ['everyone'],
            signatories = [id],
            signatures = [id],
            writers = [id]
        )
        self.webfield_builder.set_author_page(self.conference, authors_group)

        return self.conference
