import os
import openreview
from .invitation import InvitationBuilder
from openreview.api import Group

class Venue(object):

    def __init__(self, client, venue_id):

        self.client = client
        self.venue_id = venue_id
        self.short_name = 'TBD'
        self.id = venue_id # get compatibility with conference
        self.program_chairs_name = 'Program_Chairs'
        self.reviewers_name = 'Reviewers'
        self.reviewer_roles = ['Reviewers']
        self.authors_name = 'Authors'
        self.submission_stage = None
        self.ethics_review_stage = None
        self.use_area_chairs = False
        self.use_senior_area_chairs = False
        self.use_ethics_chairs = False
        self.invitation_builder = InvitationBuilder(self)

    def get_id(self):
        return self.venue_id

    def get_short_name(self):
        return self.short_name

    def get_roles(self):
        return [self.reviewers_name]

    def get_meta_invitation_id(self):
        return f'{self.venue_id}/-/Edit'

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

    def get_reviewers_id(self, number = None):
        return self.get_committee_id(self.reviewers_name, number)

    def get_authors_id(self, number = None):
        return self.get_committee_id(self.authors_name, number)

    def get_program_chairs_id(self):
        return self.get_committee_id(self.program_chairs_name)          

    def setup(self):
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
            content = content.replace("var SUBMISSION_ID = '';", "var SUBMISSION_ID = '" + venue_id + "/-/Submission';")
            content = content.replace("var SUBMITTED_ID = '';", "var SUBMITTED_ID = '" + venue_id + "/Submitted';")
            content = content.replace("var UNDER_REVIEW_ID = '';", "var UNDER_REVIEW_ID = '" + venue_id + "/Under_Review';")
            content = content.replace("var DESK_REJECTED_ID = '';", "var DESK_REJECTED_ID = '" + venue_id + "/Desk_Rejection';")
            content = content.replace("var WITHDRAWN_ID = '';", "var WITHDRAWN_ID = '" + venue_id + "/Withdrawn_Submission';")
            content = content.replace("var REJECTED_ID = '';", "var REJECTED_ID = '" + venue_id + "/Rejection';")
            venue_group.web = content
            self.client.post_group(venue_group)

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

    
    def set_submission_stage(self, stage):
        self.submission_stage = stage
        return self.invitation_builder.set_submission_invitation()


    def set_post_submission_stage(self):
        venue_id = self.venue_id
        submissions = self.client.get_all_notes(invitation=self.submission_stage.get_submission_id(self))
        
        ## Create paper groups for each submission, given the authors group is going to be created during the submission time, we could consider creating all these groups
        ## during the setup matching stage, we don't to have them created right after the submission deadline. 
        for submission in submissions:
            editors_in_chief_id = f'{venue_id}/Editors_In_Chief'
            action_editors_id = f'{venue_id}/Paper{submission.number}/Action_Editors'
            reviewers_id = self.get_reviewers_id(submission.number)
            authors_id = self.get_authors_id(submission.number)

            paper_group=self.client.post_group(openreview.api.Group(id=f'{venue_id}/Paper{submission.number}',
                    readers=[venue_id],
                    writers=[venue_id],
                    signatures=[venue_id],
                    signatories=[venue_id]
                ))

            authors_group=self.client.post_group(Group(id=authors_id,
                readers=[venue_id, authors_id],
                writers=[venue_id],
                signatures=[venue_id],
                signatories=[venue_id, authors_id],
                members=submission.content['authorids']['value'] ## always update authors
            ))

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



