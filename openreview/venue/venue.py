import os
import openreview
from openreview import tools
from .invitation import InvitationBuilder
from openreview.api import Group
from .recruitment import Recruitment

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
        self.area_chairs_name = 'Area_Chairs'
        self.senior_area_chairs_name = 'Senior_Area_Chairs'
        self.authors_name = 'Authors'
        self.submission_stage = None
        self.review_stage = None
        self.ethics_review_stage = None
        self.use_area_chairs = False
        self.use_senior_area_chairs = False
        self.use_ethics_chairs = False
        self.use_recruitment_template = True
        self.invitation_builder = InvitationBuilder(self)
        self.recruitment = Recruitment(self)

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
        return [self.reviewers_name]

    def get_meta_invitation_id(self):
        return f'{self.venue_id}/-/Edit'

    def get_recruitment_id(self, committee_id):
        return self.get_invitation_id('Recruitment', prefix=committee_id)

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
    
    def get_reviewers_id(self, number = None, anon=False):
        return self.get_committee_id('Reviewer_' if anon else self.reviewers_name, number)

    def get_authors_id(self, number = None):
        return self.get_committee_id(self.authors_name, number)

    def get_program_chairs_id(self):
        return self.get_committee_id(self.program_chairs_name)

    def get_area_chairs_id(self, number = None):
        return self.get_committee_id(self.area_chairs_name, number)

    def get_homepage_options(self):
        options = {}
        options['title'] = self.name
        options['subtitle'] = self.short_name
        options['website'] = self.website
        options['contact'] = self.contact
        return options

    def set_group_variable(self, group_id, variable_name, value):

        group = self.client.get_group(group_id)
        group.web = group.web.replace(f"var {variable_name} = '';", f"var {variable_name} = '{value}';")
        # print(group.web[:1000])
        self.client.post_group(group)   

    def has_area_chairs(self, has_area_chairs):
        self.use_area_chairs = has_area_chairs
        # pc_group = tools.get_group(self.client, self.get_program_chairs_id())
        # if pc_group and pc_group.web:
        #     # update PC console
        #     if self.use_area_chairs:
        #         self.webfield_builder.edit_web_string_value(pc_group, 'AREA_CHAIRS_ID', self.get_area_chairs_id())
        #     else:
        #         self.webfield_builder.edit_web_string_value(pc_group, 'AREA_CHAIRS_ID', '')

    def has_senior_area_chairs(self, has_senior_area_chairs):
        self.use_senior_area_chairs = has_senior_area_chairs

    def setup(self, program_chair_ids=[]):
    
        venue_id = self.venue_id
        #TODO: create all the prefix groups
        venue_group = openreview.api.Group(id = venue_id,
            readers = ['everyone'],
            writers = [venue_id],
            signatures = ['~Super_User1'],
            signatories = [venue_id],
            members = [],
            host = venue_id
        )

        #TODO: migrate homepage from the conference webfield
        with open(os.path.join(os.path.dirname(__file__), '../journal/webfield/homepage.js')) as f:
            content = f.read()
            content = content.replace("var VENUE_ID = '';", "var VENUE_ID = '" + venue_id + "';")
            ##content = content.replace("var SUBMISSION_ID = '';", "var SUBMISSION_ID = '" + venue_id + "/-/Submission';")
            content = content.replace("var SUBMITTED_ID = '';", "var SUBMITTED_ID = '" + venue_id + "/Submitted';")
            content = content.replace("var UNDER_REVIEW_ID = '';", "var UNDER_REVIEW_ID = '" + venue_id + "/Under_Review';")
            content = content.replace("var DESK_REJECTED_ID = '';", "var DESK_REJECTED_ID = '" + venue_id + "/Desk_Rejection';")
            content = content.replace("var WITHDRAWN_ID = '';", "var WITHDRAWN_ID = '" + venue_id + "/Withdrawn_Submission';")
            content = content.replace("var REJECTED_ID = '';", "var REJECTED_ID = '" + venue_id + "/Rejection';")
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

    def create_review_stage(self):
        self.invitation_builder.set_review_invitation()


    def setup_post_submission_stage(self, force=False, hide_fields=[]):
        venue_id = self.venue_id
        submissions = self.client.get_all_notes(invitation=self.submission_stage.get_submission_id(self))
        
        ## Create paper groups for each submission, given the authors group is going to be created during the submission time, we could consider creating all these groups
        ## during the setup matching stage, we don't to have them created right after the submission deadline. 
        for submission in submissions:
            editors_in_chief_id = f'{venue_id}/Editors_In_Chief'
            action_editors_id = f'{venue_id}/Paper{submission.number}/Action_Editors'
            reviewers_id = self.get_reviewers_id(submission.number)
            authors_id = self.get_authors_id(submission.number)

            action_editors_group=self.client.post_group(Group(id=action_editors_id,
                    readers=[venue_id, action_editors_id],
                    nonreaders=[authors_id],
                    writers=[venue_id],
                    signatures=[venue_id],
                    signatories=[venue_id, action_editors_id],
                    members=[]
                ))

            reviewers_group=self.client.post_group(Group(id=reviewers_id,
                    readers=[venue_id, action_editors_id, reviewers_id],
                    deanonymizers=[venue_id, action_editors_id],
                    nonreaders=[authors_id],
                    writers=[venue_id, action_editors_id],
                    signatures=[venue_id],
                    signatories=[venue_id],
                    members=[],
                    anonids=True
                ))            
        
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



