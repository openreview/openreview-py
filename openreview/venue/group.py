from .. import openreview
from openreview.api import Group
from openreview import tools

import os
import json
from tqdm import tqdm

class GroupBuilder(object):

    def __init__(self, venue):
        self.venue = venue
        self.client = venue.client
        self.client_v1 = openreview.Client(baseurl=openreview.tools.get_base_urls(self.client)[0], token=self.client.token)
        self.venue_id = venue.id
        self.super_meta_invitation_id = venue.support_user.split('/')[0] + '/-/Edit'

    def update_web_field(self, group_id, web):
        return self.post_group(openreview.api.Group(
            id = group_id,
            web = web
        ))

    def get_update_content(self, current_content, new_content):
        update_content = {}

        for key, value in current_content.items():
            if key in new_content and value != new_content[key]:
                update_content[key] = new_content[key]
            
            if key not in new_content:
                update_content[key] = { 'delete': True }

        for key, value in new_content.items():
            if key not in current_content:
                update_content[key] = new_content[key]
        return update_content

    def post_group(self, group):
        self.client.post_group_edit(
            invitation = self.venue.get_meta_invitation_id(),
            readers = [self.venue_id],
            writers = [self.venue_id],
            signatures = ['~Super_User1' if group.id == self.venue_id else self.venue_id],
            group = group
        )
        return self.client.get_group(group.id)        

    def build_groups(self, venue_id):
        path_components = venue_id.split('/')
        paths = ['/'.join(path_components[0:index+1]) for index, path in enumerate(path_components)]
        groups = []

        for p in paths:
            group = tools.get_group(self.client, id = p)
            if group is None:
                self.client.post_group_edit(
                    invitation = self.super_meta_invitation_id,
                    readers = ['everyone'],
                    writers = ['~Super_User1'],
                    signatures = ['~Super_User1'],
                    group = Group(
                        id = p,
                        readers = ['everyone'],
                        nonreaders = [],
                        writers = [p],
                        signatories = [p],
                        signatures = ['~Super_User1'],
                        members = [],
                        details = { 'writable': True }
                    )
                )
                group = self.client.get_group(p)
            groups.append(group)

        return groups

    def get_reviewer_identity_readers(self, number):
        return openreview.stages.IdentityReaders.get_readers(self.venue, number, self.venue.reviewer_identity_readers)

    def get_area_chair_identity_readers(self, number):
        return openreview.stages.IdentityReaders.get_readers(self.venue, number, self.venue.area_chair_identity_readers)

    def get_senior_area_chair_identity_readers(self, number):
        return openreview.stages.IdentityReaders.get_readers(self.venue, number, self.venue.senior_area_chair_identity_readers)

    def get_reviewer_paper_group_readers(self, number):
        readers=[self.venue.id]
        if self.venue.use_senior_area_chairs:
            readers.append(self.venue.get_senior_area_chairs_id(number))
        if self.venue.use_area_chairs:
            readers.append(self.venue.get_area_chairs_id(number))
        readers.append(self.venue.get_reviewers_id(number))
        return readers

    def get_reviewer_paper_group_writers(self, number):
        readers=[self.venue.id]
        if self.venue.use_senior_area_chairs:
            readers.append(self.venue.get_senior_area_chairs_id(number))
        if self.venue.use_area_chairs:
            readers.append(self.venue.get_area_chairs_id(number))
        return readers


    def get_area_chair_paper_group_readers(self, number):
        readers=[self.venue.id, self.venue.get_program_chairs_id()]
        if self.venue.use_senior_area_chairs:
            readers.append(self.venue.get_senior_area_chairs_id(number))
        readers.append(self.venue.get_area_chairs_id(number))
        if openreview.stages.IdentityReaders.REVIEWERS_ASSIGNED in self.venue.area_chair_identity_readers:
            readers.append(self.venue.get_reviewers_id(number))
        return readers

    def create_venue_group(self):

        venue_id = self.venue_id
        groups = self.build_groups(venue_id)
        venue_group = groups[-1]

        if venue_group.web is None:

            with open(os.path.join(os.path.dirname(__file__), 'webfield/homepageWebfield.js')) as f:
                content = f.read()
                self.post_group(openreview.api.Group(
                    id = venue_group.id,
                    web = content
                ))

            self.client_v1.add_members_to_group('venues', venue_id)
            root_id = groups[0].id
            if root_id == root_id.lower():
                root_id = groups[1].id        
            self.client_v1.add_members_to_group('host', root_id)

        ## Update settings
        content = {
            'submission_id': { 'value': self.venue.get_submission_id() },
            'meta_invitation_id': { 'value': self.venue.get_meta_invitation_id() },
            'submission_name': { 'value': self.venue.submission_stage.name },
            'submission_venue_id': { 'value': self.venue.get_submission_venue_id() },
            'withdrawn_venue_id': { 'value': self.venue.get_withdrawn_submission_venue_id() },
            'desk_rejected_venue_id': { 'value': self.venue.get_desk_rejected_submission_venue_id() },
            'rejected_venue_id': { 'value': self.venue.get_rejected_submission_venue_id() },
            'public_submissions': { 'value': self.venue.submission_stage.public },
            'public_withdrawn_submissions': { 'value': self.venue.submission_stage.withdrawn_submission_public },
            'public_desk_rejected_submissions': { 'value': self.venue.submission_stage.desk_rejected_submission_public },
            'title': { 'value': self.venue.name if self.venue.name else '' },
            'subtitle': { 'value': self.venue.short_name if self.venue.short_name else '' },
            'website': { 'value': self.venue.website if self.venue.website else '' },
            'contact': { 'value': self.venue.contact if self.venue.contact else '' },
            'program_chairs_id': { 'value': self.venue.get_program_chairs_id() },
            'reviewers_id': { 'value': self.venue.get_reviewers_id() },
            'reviewers_name': { 'value': self.venue.reviewers_name },
            'reviewers_anon_name': { 'value': 'Reviewer_' },
            'reviewers_submitted_name': { 'value': f'{self.venue.reviewers_name}/Submitted' },
            'reviewers_custom_max_papers_id': { 'value': self.venue.get_custom_max_papers_id(self.venue.get_reviewers_id()) },
            'reviewers_affinity_score_id': { 'value': self.venue.get_affinity_score_id(self.venue.get_reviewers_id()) },
            'reviewers_conflict_id': { 'value': self.venue.get_conflict_score_id(self.venue.get_reviewers_id()) },
            'reviewers_recruitment_id': { 'value': self.venue.get_recruitment_id(self.venue.get_reviewers_id()) },
            'authors_id': { 'value': self.venue.get_authors_id() },
            'authors_accepted_id': { 'value': f'{self.venue.get_authors_id()}/Accepted' },
            'authors_name': { 'value': self.venue.authors_name },
            'withdrawn_submission_id': { 'value': self.venue.get_withdrawn_id() },
            'withdraw_expiration_id': { 'value': self.venue.get_invitation_id('Withdraw_Expiration') },
            'withdraw_reversion_id': { 'value': self.venue.get_invitation_id('Withdrawal_Reversion') },
            'withdraw_committee': { 'value': self.venue.get_participants(number="{number}", with_authors=True, with_program_chairs=True)},
            'withdrawal_name': { 'value': 'Withdrawal'},
            'desk_rejected_submission_id': { 'value': self.venue.get_desk_rejected_id() },
            'desk_reject_expiration_id': { 'value': self.venue.get_invitation_id('Desk_Reject_Expiration') },
            'desk_rejection_reversion_id': { 'value': self.venue.get_invitation_id('Desk_Rejection_Reversion') },
            'desk_reject_committee': { 'value': self.venue.get_participants(number="{number}", with_authors=True, with_program_chairs=True)},
            'desk_rejection_name': { 'value': 'Desk_Rejection'}
        }

        if self.venue.use_area_chairs:
            content['area_chairs_id'] = { 'value': self.venue.get_area_chairs_id() }
            content['area_chairs_custom_max_papers_id'] = { 'value': self.venue.get_custom_max_papers_id(self.venue.get_area_chairs_id()) }
            content['area_chairs_affinity_score_id'] = { 'value': self.venue.get_affinity_score_id(self.venue.get_area_chairs_id()) }
            content['area_chairs_conflict_id'] = { 'value': self.venue.get_conflict_score_id(self.venue.get_area_chairs_id()) }
            content['area_chairs_recruitment_id'] = { 'value': self.venue.get_recruitment_id(self.venue.get_area_chairs_id()) }
            content['area_chairs_assignment_id'] = { 'value': self.venue.get_assignment_id(self.venue.get_area_chairs_id(), deployed=True) }


        if self.venue.use_senior_area_chairs:
            content['senior_area_chairs_id'] = { 'value': self.venue.get_senior_area_chairs_id() }
            content['senior_area_chairs_assignment_id'] = { 'value': self.venue.get_assignment_id(self.venue.get_senior_area_chairs_id(), deployed=True) }
            content['senior_area_chairs_name'] = { 'value': self.venue.senior_area_chairs_name }

        if self.venue.bid_stages:
            content['bid_name'] = { 'value': self.venue.bid_stages[0].name }

        if self.venue.review_stage:
            content['review_name'] = { 'value': self.venue.review_stage.name }
            content['review_rating'] = { 'value': self.venue.review_stage.rating_field_name }
            content['review_confidence'] = { 'value': self.venue.review_stage.confidence_field_name }
            content['review_email_pcs'] = { 'value': self.venue.review_stage.email_pcs }

        if self.venue.meta_review_stage:
            content['meta_review_name'] = { 'value': self.venue.meta_review_stage.name }

        if self.venue.decision_stage:
            content['decision_name'] = { 'value': self.venue.decision_stage.name }
            content['decision_email_authors'] = { 'value': self.venue.decision_stage.email_authors }

        if self.venue.submission_revision_stage:
            content['submission_revision_accepted'] = { 'value': self.venue.submission_revision_stage.only_accepted }            

        if self.venue.request_form_id:
            content['request_form_id'] = { 'value': self.venue.request_form_id }

        if self.venue.comment_stage:
            content['comment_mandatory_readers'] = { 'value': self.venue.comment_stage.get_mandatory_readers(self.venue, '{number}') }
            content['comment_email_pcs'] = { 'value': self.venue.comment_stage.email_pcs }

        update_content = self.get_update_content(venue_group.content if venue_group.content else {}, content)
        if update_content:
            self.client.post_group_edit(
                invitation = self.venue.get_meta_invitation_id(),
                readers = [self.venue.venue_id],
                writers = [self.venue.venue_id],
                signatures = [self.venue.venue_id],
                group = openreview.api.Group(
                    id = self.venue_id,
                    content = update_content
                )
            )        
       
    def create_program_chairs_group(self, program_chair_ids=[]):

        venue_id = self.venue_id

        pc_group_id = self.venue.get_program_chairs_id()
        pc_group = openreview.tools.get_group(self.client, pc_group_id)
        if not pc_group:
            pc_group=Group(id=pc_group_id,
                            readers=['everyone'],
                            writers=[venue_id, pc_group_id],
                            signatures=[venue_id],
                            signatories=[pc_group_id, venue_id],
                            members=program_chair_ids
                            )
            with open(os.path.join(os.path.dirname(__file__), 'webfield/programChairsWebfield.js')) as f:
                content = f.read()
                pc_group.web = content
                self.post_group(pc_group)

            ## Add pcs to have all the permissions
            self.client.add_members_to_group(venue_id, pc_group_id)        
    
    def create_authors_group(self):

        venue_id = self.venue_id
        ## authors group
        authors_id = self.venue.get_authors_id()
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
                authors_group.web = content
                self.post_group(authors_group)

        authors_accepted_id = self.venue.get_authors_accepted_id()
        authors_accepted_group = openreview.tools.get_group(self.client, authors_accepted_id)
        if not authors_accepted_group:
            authors_accepted_group = self.post_group(Group(id=authors_accepted_id,
                            readers=[venue_id, authors_accepted_id],
                            writers=[venue_id],
                            signatures=[venue_id],
                            signatories=[venue_id],
                            members=[]))        
    
    def create_reviewers_group(self):

        venue_id = self.venue.id
        reviewers_id = self.venue.get_reviewers_id()
        area_chairs_id = self.venue.get_area_chairs_id()
        senior_area_chairs_id = self.venue.get_senior_area_chairs_id()
        reviewer_group = openreview.tools.get_group(self.client, reviewers_id)
        if not reviewer_group:
            reviewer_group = Group(id=reviewers_id,
                            readers=[venue_id, senior_area_chairs_id, area_chairs_id, reviewers_id],
                            writers=[venue_id],
                            signatures=[venue_id],
                            signatories=[venue_id],
                            members=[]
                        )

            with open(os.path.join(os.path.dirname(__file__), 'webfield/reviewersWebfield.js')) as f:
                content = f.read()
                reviewer_group.web = content
                self.post_group(reviewer_group)

    def create_area_chairs_group(self):

        venue_id = self.venue.id
        area_chairs_id = self.venue.get_area_chairs_id()
        senior_area_chairs_id = self.venue.get_senior_area_chairs_id()
        area_chairs_group = openreview.tools.get_group(self.client, area_chairs_id)
        if not area_chairs_group:
            area_chairs_group = Group(id=area_chairs_id,
                            readers=[venue_id, senior_area_chairs_id, area_chairs_id],
                            writers=[venue_id],
                            signatures=[venue_id],
                            signatories=[venue_id],
                            members=[]
                        )

            with open(os.path.join(os.path.dirname(__file__), 'webfield/areachairsWebfield.js')) as f:
                content = f.read()
                area_chairs_group.web = content
                self.post_group(area_chairs_group) 

    def create_senior_area_chairs_group(self):

        venue_id = self.venue.id
        senior_area_chairs_id = self.venue.get_senior_area_chairs_id()
        senior_area_chairs_group = openreview.tools.get_group(self.client, senior_area_chairs_id)
        if not senior_area_chairs_group:
            senior_area_chairs_group = Group(id=senior_area_chairs_id,
                            readers=[venue_id, senior_area_chairs_id],
                            writers=[venue_id],
                            signatures=[venue_id],
                            signatories=[venue_id],
                            members=[]
                        )

            with open(os.path.join(os.path.dirname(__file__), 'webfield/seniorAreaChairsWebfield.js')) as f:
                content = f.read()
                senior_area_chairs_group.web = content
                self.post_group(senior_area_chairs_group)

    def create_paper_committee_groups(self, submissions, overwrite=False):

        group_by_id = { g.id: g for g in self.client.get_all_groups(prefix=f'{self.venue.id}/{self.venue.submission_stage.name}.*') }

        def create_paper_commmitee_group(note):
            # Reviewers Paper group
            reviewers_id=self.venue.get_reviewers_id(number=note.number)
            group = group_by_id.get(reviewers_id)
            if not group or overwrite:
                self.post_group(openreview.api.Group(id=reviewers_id,
                    readers=self.get_reviewer_paper_group_readers(note.number),
                    nonreaders=[self.venue.get_authors_id(note.number)],
                    deanonymizers=self.get_reviewer_identity_readers(note.number),
                    writers=self.get_reviewer_paper_group_writers(note.number),
                    signatures=[self.venue.id],
                    signatories=[self.venue.id],
                    anonids=True,
                    members=group.members if group else []
                ))

            # Reviewers Submitted Paper group
            reviewers_submitted_id = self.venue.get_reviewers_id(number=note.number) + '/Submitted'
            group = group_by_id.get(reviewers_submitted_id)
            if not group or overwrite:
                readers=[self.venue.id]
                if self.venue.use_senior_area_chairs:
                    readers.append(self.venue.get_senior_area_chairs_id(note.number))
                if self.venue.use_area_chairs:
                    readers.append(self.venue.get_area_chairs_id(note.number))
                readers.append(reviewers_submitted_id)
                self.post_group(openreview.api.Group(id=reviewers_submitted_id,
                    readers=readers,
                    writers=[self.venue.id],
                    signatures=[self.venue.id],
                    signatories=[self.venue.id],
                    members=group.members if group else []
                ))

            # Area Chairs Paper group
            if self.venue.use_area_chairs:
                area_chairs_id=self.venue.get_area_chairs_id(number=note.number)
                group = group_by_id.get(area_chairs_id)
                if not group or overwrite:
                    self.post_group(openreview.api.Group(id=area_chairs_id,
                        readers=self.get_area_chair_paper_group_readers(note.number),
                        nonreaders=[self.venue.get_authors_id(note.number)],
                        deanonymizers=self.get_area_chair_identity_readers(note.number),
                        writers=[self.venue.id],
                        signatures=[self.venue.id],
                        signatories=[self.venue.id],
                        anonids=True,
                        members=group.members if group else []
                    ))

            # Senior Area Chairs Paper group
            if self.venue.use_senior_area_chairs:
                senior_area_chairs_id=self.venue.get_senior_area_chairs_id(number=note.number)
                group = group_by_id.get(senior_area_chairs_id)
                if not group or overwrite:
                    self.post_group(openreview.api.Group(id=senior_area_chairs_id,
                        readers=self.get_senior_area_chair_identity_readers(note.number),
                        nonreaders=[self.venue.get_authors_id(note.number)],
                        writers=[self.venue.id],
                        signatures=[self.venue.id],
                        signatories=[self.venue.id, senior_area_chairs_id],
                        members=group.members if group else []
                    ))

        openreview.tools.concurrent_requests(create_paper_commmitee_group, submissions, desc='create_paper_committee_groups')

    def create_recruitment_committee_groups(self, committee_name):

        venue_id = self.venue.venue_id

        pc_group_id = self.venue.get_program_chairs_id()
        committee_id = self.venue.get_committee_id(committee_name)
        committee_invited_id = self.venue.get_committee_id_invited(committee_name)
        committee_declined_id = self.venue.get_committee_id_declined(committee_name)

        committee_group = tools.get_group(self.client, committee_id)
        if not committee_group:
            committee_group=self.post_group(Group(id=committee_id,
                            readers=[venue_id, committee_id],
                            writers=[venue_id, pc_group_id],
                            signatures=[venue_id],
                            signatories=[venue_id, committee_id],
                            members=[]
                            ))

        committee_declined_group = tools.get_group(self.client, committee_declined_id)
        if not committee_declined_group:
            committee_declined_group=self.post_group(Group(id=committee_declined_id,
                            readers=[venue_id, committee_declined_id],
                            writers=[venue_id, pc_group_id],
                            signatures=[venue_id],
                            signatories=[venue_id, committee_declined_id],
                            members=[]
                            ))

        committee_invited_group = tools.get_group(self.client, committee_invited_id)
        if not committee_invited_group:
            committee_invited_group=self.post_group(Group(id=committee_invited_id,
                            readers=[venue_id, committee_invited_id],
                            writers=[venue_id, pc_group_id],
                            signatures=[venue_id],
                            signatories=[venue_id, committee_invited_id],
                            members=[]
                            ))
