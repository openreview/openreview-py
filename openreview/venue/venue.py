import json
import os
import time
import openreview
from openreview import tools
from .invitation import InvitationBuilder
from .group import GroupBuilder
from openreview.api import Group
from .recruitment import Recruitment
from . import matching

class Venue(object):

    def __init__(self, client, venue_id):

        self.client = client
        self.venue_id = venue_id
        self.name = 'TBD'
        self.short_name = 'TBD'
        self.website = None
        self.contact = None
        self.id = venue_id # get compatibility with conference
        self.program_chairs_name = 'Program_Chairs'
        self.reviewers_name = 'Reviewers'
        self.reviewer_roles = ['Reviewers']
        self.area_chair_roles = ['Area_Chairs']
        self.senior_area_chair_roles = ['Senior_Area_Chairs']        
        self.area_chairs_name = 'Area_Chairs'
        self.senior_area_chairs_name = 'Senior_Area_Chairs'
        self.ethics_chairs_name = 'Ethics_Chairs'
        self.ethics_reviewers_name = 'Ethics_Reviewers'
        self.authors_name = 'Authors'
        self.use_ethics_chairs = False
        self.use_ethics_reviewers = False        
        self.submission_stage = None
        self.review_stage = None
        self.ethics_review_stage = None
        self.bid_stages = []
        self.meta_review_stage = None
        self.use_area_chairs = False
        self.use_senior_area_chairs = False
        self.use_ethics_chairs = False
        self.use_recruitment_template = True
        self.support_user = 'OpenReview.net/Support'
        self.invitation_builder = InvitationBuilder(self)
        self.group_builder = GroupBuilder(self)
        self.recruitment = Recruitment(self)
        self.reviewer_identity_readers = []
        self.area_chair_identity_readers = []
        self.senior_area_chair_identity_readers = []        

    def get_id(self):
        return self.venue_id

    def get_short_name(self):
        return self.short_name

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
            roles = self.reviewer_roles + [self.area_chairs_name]
        if self.use_senior_area_chairs:
            roles = roles + [self.senior_area_chairs_name]
        return roles

    def get_meta_invitation_id(self):
        return f'{self.venue_id}/-/Edit'

    def get_submission_id(self):
        return self.submission_stage.get_submission_id(self)

    def get_recruitment_id(self, committee_id):
        return self.get_invitation_id('Recruitment', prefix=committee_id)

    def get_bid_id(self, committee_id):
        return self.get_invitation_id('Bid', prefix=committee_id)

    def get_paper_assignment_id(self, committee_id, deployed=False, invite=False):
        if deployed:
            return self.get_invitation_id('Assignment', prefix=committee_id)
        if invite:
            return self.get_invitation_id('Invite_Assignment', prefix=committee_id)
        return self.get_invitation_id('Proposed_Assignment', prefix=committee_id)

    def get_affinity_score_id(self, committee_id):
        return self.get_invitation_id('Affinity_Score', prefix=committee_id)

    def get_conflict_score_id(self, committee_id):
        return self.get_invitation_id('Conflict', prefix=committee_id)

    def get_custom_max_papers_id(self, committee_id):
        return self.get_invitation_id('Custom_Max_Papers', prefix=committee_id)

    def get_recommendation_id(self, committee_id=None):
        if not committee_id:
            committee_id = self.get_reviewers_id()
        return self.get_invitation_id('Recommendation', prefix=committee_id)

    def get_invitation_id(self, name, number = None, prefix = None):
        invitation_id = self.id
        if prefix:
            invitation_id = prefix
        if number:
            invitation_id = invitation_id + '/Paper' + str(number) + '/-/'
        else:
            invitation_id = invitation_id + '/-/'

        invitation_id =  invitation_id + name
        return invitation_id

    def get_committee_id(self, name, number=None):
        committee_id = self.id + '/'
        if number:
            committee_id = f'{committee_id}Paper{number}/{name}'
        else:
            committee_id = committee_id + name
        return committee_id

    def get_committee_id_invited(self, committee_name):
        return self.get_committee_id(committee_name) + '/Invited'

    def get_committee_id_declined(self, committee_name):
        return self.get_committee_id(committee_name) + '/Declined'

    ## Compatibility with Conference, refactor conference references to use get_reviewers_id
    def get_anon_reviewer_id(self, number, anon_id):
        return self.get_reviewers_id(number, True)

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
    
    def get_reviewers_id(self, number = None, anon=False, submitted=False):
        reviewers_id = self.get_committee_id('Reviewer_.*' if anon else self.reviewers_name, number)
        if submitted:
            return reviewers_id + '/Submitted'
        return reviewers_id

    def get_authors_id(self, number = None):
        return self.get_committee_id(self.authors_name, number)

    def get_program_chairs_id(self):
        return self.get_committee_id(self.program_chairs_name)

    def get_area_chairs_id(self, number = None, anon=False):
        return self.get_committee_id('Area_Chair_.*' if anon else self.area_chairs_name, number)

    ## Compatibility with Conference, refactor conference references to use get_area_chairs_id
    def get_anon_area_chair_id(self, number, anon_id):
        return self.get_area_chairs_id(number, True)

    def get_senior_area_chairs_id(self, number = None):
        return self.get_committee_id(self.senior_area_chairs_name, number)

    def get_ethics_chairs_id(self, number = None):
        return self.get_committee_id(self.ethics_chairs_name, number)

    def get_ethics_reviewers_id(self, number = None, anon=False):
        return self.get_committee_id('Ethics_Reviewer_.*' if anon else self.ethics_reviewers_name, number)

    def get_homepage_options(self):
        options = {}
        options['title'] = self.name
        options['subtitle'] = self.short_name
        options['website'] = self.website
        options['contact'] = self.contact
        return options

    def get_submissions(self, sort=None):
        return self.client.get_all_notes(invitation=self.submission_stage.get_submission_id(self), sort=sort)

    def set_group_variable(self, group_id, variable_name, value):

        group = self.client.get_group(group_id)
        group.web = group.web.replace(f"var {variable_name} = '';", f"var {variable_name} = '{value}';")
        group.web = group.web.replace(f"const {variable_name} = ''", f"const {variable_name} = '{value}'")
        # print(group.web[:1000])
        self.client.post_group(group)

    def setup(self, program_chair_ids=[]):
    
        venue_id = self.venue_id

        # groups = self.group_builder.build_groups(venue_id)
        # for i, g in enumerate(groups[:-1]):
        #     self.group_builder.set_landing_page(g, groups[i-1] if i > 0 else None)

        venue_group = openreview.api.Group(id = venue_id,
            readers = ['everyone'],
            writers = [venue_id],
            signatures = ['~Super_User1'],
            signatories = [venue_id],
            members = [],
            host = venue_id
        )

        with open(os.path.join(os.path.dirname(__file__), 'webfield/homepageWebfield.js')) as f:
            content = f.read()
            content = content.replace("const VENUE_ID = ''", "const VENUE_ID = '" + venue_id + "'")
            # add withdrawn and desk-rejected ids when invitations are created
            # content = content.replace("const WITHDRAWN_SUBMISSION_ID = ''", "const WITHDRAWN_SUBMISSION_ID = '" + venue_id + "/-/Withdrawn_Submission'")
            # content = content.replace("const DESK_REJECTED_SUBMISSION_ID = ''", "const DESK_REJECTED_SUBMISSION_ID = '" + venue_id + "/-/Desk_Rejected_Submission'")
            content = content.replace("const AUTHORS_ID = ''", "const AUTHORS_ID = '" + self.get_authors_id() + "'")
            content = content.replace("var HEADER = {};", "var HEADER = " + json.dumps(self.get_homepage_options()) + ";")
            venue_group.web = content
            self.client.post_group(venue_group)

        ## pc group
        #to-do add pc group webfield
        pc_group_id = self.get_program_chairs_id()
        pc_group = openreview.tools.get_group(self.client, pc_group_id)
        if not pc_group:
            pc_group=self.client.post_group(Group(id=pc_group_id,
                            readers=['everyone'],
                            writers=[venue_id, pc_group_id],
                            signatures=[venue_id],
                            signatories=[pc_group_id, venue_id],
                            members=program_chair_ids
                            ))
        # with open(os.path.join(os.path.dirname(__file__), 'webfield/editorsInChiefWebfield.js')) as f:
        #     content = f.read()
        #     content = content.replace("var VENUE_ID = '';", "var VENUE_ID = '" + venue_id + "';")
        #     content = content.replace("var SHORT_PHRASE = '';", f'var SHORT_PHRASE = "{journal.short_name}";')
        #     content = content.replace("var SUBMISSION_ID = '';", "var SUBMISSION_ID = '" + journal.get_author_submission_id() + "';")
        #     content = content.replace("var EDITORS_IN_CHIEF_NAME = '';", "var EDITORS_IN_CHIEF_NAME = '" + journal.editors_in_chief_name + "';")
        #     content = content.replace("var REVIEWERS_NAME = '';", "var REVIEWERS_NAME = '" + journal.reviewers_name + "';")
        #     content = content.replace("var ACTION_EDITOR_NAME = '';", "var ACTION_EDITOR_NAME = '" + journal.action_editors_name + "';")
        #     if journal.get_request_form():
        #         content = content.replace("var JOURNAL_REQUEST_ID = '';", "var JOURNAL_REQUEST_ID = '" + journal.get_request_form().id + "';")

        #     editor_in_chief_group.web = content
        #     self.client.post_group(editor_in_chief_group)

        ## Add pcs to have all the permissions
        self.client.add_members_to_group(venue_group, pc_group_id)

        ## authors group
        authors_id = self.get_authors_id()
        authors_group = openreview.tools.get_group(self.client, authors_id)
        if not authors_group:
            authors_group = Group(id=authors_id,
                            readers=[venue_id, authors_id],
                            writers=[venue_id],
                            signatures=[venue_id],
                            signatories=[venue_id],
                            members=[])

        with open(os.path.join(os.path.dirname(__file__), 'webfield/authorsWebfield.js')) as f:
            content = f.read()
            content = content.replace("var VENUE_ID = '';", "var VENUE_ID = '" + venue_id + "';")
            ##content = content.replace("var SUBMISSION_ID = '';", "var SUBMISSION_ID = '" + self.submission_stage.get_submission_id(self) + "';")
            authors_group.web = content
            self.client.post_group(authors_group)

        meta_inv = self.client.post_invitation_edit(invitations = None,
            readers = [venue_id],
            writers = [venue_id],
            signatures = [venue_id],
            invitation = openreview.api.Invitation(id = self.get_meta_invitation_id(),
                invitees = [venue_id],
                readers = [venue_id],
                signatures = [venue_id],
                edit = True
            ))

        self.group_builder.create_reviewers_group()
        if self.use_area_chairs:
            self.group_builder.create_area_chairs_group()
        self.client.add_members_to_group('venues', venue_id)
        self.client.add_members_to_group('host', venue_id)

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
        default_load= 0,
        allow_overlap_official_committee = False):

        return self.recruitment.invite_committee(title,
            message,
            invitees,
            reviewers_name,
            remind,
            invitee_names,
            retry_declined,
            contact_info,
            reduced_load_on_decline,
            # default_load, ##can this be removed? We never get it from the request form
            allow_overlap_official_committee)

    def set_submission_stage(self, stage):
        self.submission_stage = stage
        self.invitation_builder.set_submission_invitation()
        self.set_group_variable(self.venue_id, 'SUBMISSION_ID', self.submission_stage.get_submission_id(self))
        self.set_group_variable(self.get_authors_id(), 'SUBMISSION_ID', self.submission_stage.get_submission_id(self))
        self.set_group_variable(self.get_reviewers_id(), 'SUBMISSION_ID', self.submission_stage.get_submission_id(self))
        self.set_group_variable(self.get_area_chairs_id(), 'SUBMISSION_ID', self.submission_stage.get_submission_id(self))

    def update_readers(self, submission, invitation):
        ## Update readers of current notes
        notes = self.client.get_notes(invitation=invitation.id)
        invitation_readers = invitation.edit['note']['readers']

        ## if the invitation indicates readers is everyone but the submission is not, we ignore the update
        if 'everyone' in invitation_readers and 'everyone' not in submission.readers:
            return

        for note in notes:
            if type(invitation_readers) is list and note.readers != invitation_readers:
                self.client.post_note_edit(
                    invitation = self.get_meta_invitation_id(),
                    readers = invitation_readers,
                    writers = [self.venue_id],
                    signatures = [self.venue_id],
                    note = openreview.api.Note(
                        id = note.id,
                        readers = invitation_readers,
                        nonreaders = invitation.edit['note']['nonreaders']
                    )
                ) 

    def create_review_stage(self):
        self.invitation_builder.set_review_invitation()
        self.set_group_variable(self.get_reviewers_id(), 'OFFICIAL_REVIEW_NAME', self.review_stage.name)
        self.set_group_variable(self.get_area_chairs_id(), 'OFFICIAL_REVIEW_NAME', self.review_stage.name)

        ## Move this to the date process function
        for submission in self.get_submissions():
            paper_invitation_edit = self.client.post_invitation_edit(invitations=self.get_invitation_id(self.review_stage.name),
                readers=[self.venue_id],
                writers=[self.venue_id],
                signatures=[self.venue_id],
                content={
                    'noteId': {
                        'value': submission.id
                    },
                    'noteNumber': {
                        'value': submission.number
                    }
                },
                invitation=openreview.api.Invitation()
            )
            paper_invitation = self.client.get_invitation(paper_invitation_edit['invitation']['id'])
            self.update_readers(submission, paper_invitation)

    def create_meta_review_stage(self):
        self.invitation_builder.set_meta_review_invitation()
        self.set_group_variable(self.get_area_chairs_id(), 'META_REVIEW_NAME', self.meta_review_stage.name)

        ## Move this to the date process function
        for submission in self.get_submissions():
            paper_invitation_edit = self.client.post_invitation_edit(invitations=self.get_invitation_id(self.meta_review_stage.name),
                readers=[self.venue_id],
                writers=[self.venue_id],
                signatures=[self.venue_id],
                content={
                    'noteId': {
                        'value': submission.id
                    },
                    'noteNumber': {
                        'value': submission.number
                    }
                },
                invitation=openreview.api.Invitation()
            )
            paper_invitation = self.client.get_invitation(paper_invitation_edit['invitation']['id'])
            self.update_readers(submission, paper_invitation)

    def setup_post_submission_stage(self, force=False, hide_fields=[]):
        venue_id = self.venue_id
        submissions = self.client.get_all_notes(invitation=self.submission_stage.get_submission_id(self))
        
        self.group_builder.create_paper_committee_groups()
        ## Create paper groups for each submission, given the authors group is going to be created during the submission time, we could consider creating all these groups
        ## during the setup matching stage, we don't to have them created right after the submission deadline. 
        # for submission in submissions:
        #     editors_in_chief_id = f'{venue_id}/Editors_In_Chief'
        #     action_editors_id = f'{venue_id}/Paper{submission.number}/Action_Editors'
        #     reviewers_id = self.get_reviewers_id(submission.number)
        #     authors_id = self.get_authors_id(submission.number)

        #     action_editors_group=self.client.post_group(Group(id=action_editors_id,
        #             readers=[venue_id, action_editors_id],
        #             nonreaders=[authors_id],
        #             writers=[venue_id],
        #             signatures=[venue_id],
        #             signatories=[venue_id, action_editors_id],
        #             members=[]
        #         ))

        #     reviewers_group=self.client.post_group(Group(id=reviewers_id,
        #             readers=[venue_id, action_editors_id, reviewers_id],
        #             deanonymizers=[venue_id, action_editors_id],
        #             nonreaders=[authors_id],
        #             writers=[venue_id, action_editors_id],
        #             signatures=[venue_id],
        #             signatories=[venue_id],
        #             members=[],
        #             anonids=True
        #         ))            
        
        ## Release the submissions to specified readers
        for submission in submissions:
            self.client.post_note_edit(invitation=self.get_meta_invitation_id(),
                readers=[venue_id],
                writers=[venue_id],
                signatures=[venue_id],
                note=openreview.api.Note(id=submission.id,
                        readers = self.submission_stage.get_readers(self, submission.number)
                    )
                )             
        ## Create revision invitation if there is a second deadline?
        ## Create withdraw and desk reject invitations
        #    

    def create_bid_stages(self):
        self.invitation_builder.set_bid_invitations()

    def setup_committee_matching(self, committee_id=None, compute_affinity_scores=False, compute_conflicts=False, alternate_matching_group=None):
        if committee_id is None:
            committee_id=self.get_reviewers_id()
        if self.use_senior_area_chairs and committee_id == self.get_senior_area_chairs_id() and not alternate_matching_group:
            alternate_matching_group = self.get_area_chairs_id()
        venue_matching = matching.Matching(self, self.client.get_group(committee_id), alternate_matching_group)

        return venue_matching.setup(compute_affinity_scores, compute_conflicts)

    def set_assignments(self, assignment_title, committee_id, enable_reviewer_reassignment=False, overwrite=False):

        match_group = self.client.get_group(committee_id)
        conference_matching = matching.Matching(self, match_group)
        return conference_matching.deploy(assignment_title, overwrite, enable_reviewer_reassignment)
