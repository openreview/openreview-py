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
        if venue_group.content is None:
            venue_group.content = {}

        if venue_group.web is None:

            self.client.add_members_to_group('venues', venue_id)
            root_id = groups[0].id
            if root_id == root_id.lower():
                root_id = groups[1].id        
            self.client.add_members_to_group('host', root_id)

            with open(os.path.join(os.path.dirname(__file__), 'webfield/homepageWebfield.js')) as f:
                content = f.read()
                self.post_group(openreview.api.Group(
                    id = venue_group.id,
                    web = content,
                    host = root_id
                ))

        ## Update settings
        content = {
            'submission_id': { 'value': self.venue.get_submission_id() },
            'pc_submission_revision_id': { 'value': self.venue.get_pc_submission_revision_id() },
            'meta_invitation_id': { 'value': self.venue.get_meta_invitation_id() },
            'submission_name': { 'value': self.venue.submission_stage.name },
            'submission_venue_id': { 'value': self.venue.get_submission_venue_id() },
            'withdrawn_venue_id': { 'value': self.venue.get_withdrawn_submission_venue_id() },
            'desk_rejected_venue_id': { 'value': self.venue.get_desk_rejected_submission_venue_id() },
            'rejected_venue_id': { 'value': self.venue.get_rejected_submission_venue_id() },
            'public_submissions': { 'value': self.venue.submission_stage.public },
            'commitments_venue': { 'value': self.venue.submission_stage.commitments_venue },
            'public_withdrawn_submissions': { 'value': self.venue.submission_stage.withdrawn_submission_public },
            'public_desk_rejected_submissions': { 'value': self.venue.submission_stage.desk_rejected_submission_public },
            'submission_email_template': { 'value': self.venue.submission_stage.submission_email if self.venue.submission_stage.submission_email else '' },
            'submission_email_pcs': { 'value': self.venue.submission_stage.email_pcs },
            'title': { 'value': self.venue.name if self.venue.name else '' },
            'subtitle': { 'value': self.venue.short_name if self.venue.short_name else '' },
            'website': { 'value': self.venue.website if self.venue.website else '' },
            'contact': { 'value': self.venue.contact if self.venue.contact else '' },
            'message_sender': { 'value': self.venue.get_message_sender() },
            'location': { 'value': self.venue.location if self.venue.location else '' },
            'instructions': { 'value': self.venue.instructions if self.venue.instructions else '' },
            'start_date': { 'value': self.venue.start_date if self.venue.start_date else '' },
            'date': { 'value': self.venue.date if self.venue.date else '' },
            'program_chairs_id': { 'value': self.venue.get_program_chairs_id() },
            'reviewers_id': { 'value': self.venue.get_reviewers_id() },
            'reviewers_name': { 'value': self.venue.reviewers_name },
            'reviewers_anon_name': { 'value': self.venue.get_anon_reviewers_name() },
            'reviewers_submitted_name': { 'value': 'Submitted' },
            'reviewers_custom_max_papers_id': { 'value': self.venue.get_custom_max_papers_id(self.venue.get_reviewers_id()) },
            'reviewers_affinity_score_id': { 'value': self.venue.get_affinity_score_id(self.venue.get_reviewers_id()) },
            'reviewers_conflict_id': { 'value': self.venue.get_conflict_score_id(self.venue.get_reviewers_id()) },
            'reviewers_assignment_id': { 'value': self.venue.get_assignment_id(self.venue.get_reviewers_id(), deployed=True) },
            'reviewers_invite_assignment_id': { 'value': self.venue.get_assignment_id(self.venue.get_reviewers_id(), invite=True) },
            'reviewers_proposed_assignment_id': { 'value': self.venue.get_assignment_id(self.venue.get_reviewers_id()) },
            'reviewers_recruitment_id': { 'value': self.venue.get_recruitment_id(self.venue.get_reviewers_id()) },
            'authors_id': { 'value': self.venue.get_authors_id() },
            'authors_accepted_id': { 'value': f'{self.venue.get_authors_id()}/Accepted' },
            'authors_name': { 'value': self.venue.authors_name },
            'withdrawn_submission_id': { 'value': self.venue.get_withdrawn_id() },
            'withdraw_expiration_id': { 'value': self.venue.get_invitation_id('Withdraw_Expiration') },
            'withdraw_reversion_id': { 'value': self.venue.get_invitation_id('Withdrawal_Reversion') },
            'withdraw_committee': { 'value': self.venue.get_participants(number="{number}", with_authors=True, with_program_chairs=True)},
            'withdrawal_name': { 'value': 'Withdrawal'},
            'withdrawal_email_pcs': { 'value': self.venue.submission_stage.email_pcs_on_withdraw },
            'withdrawn_submission_reveal_authors': { 'value': self.venue.submission_stage.withdrawn_submission_reveal_authors },
            'desk_rejected_submission_id': { 'value': self.venue.get_desk_rejected_id() },
            'desk_reject_expiration_id': { 'value': self.venue.get_invitation_id('Desk_Reject_Expiration') },
            'desk_rejection_reversion_id': { 'value': self.venue.get_invitation_id('Desk_Rejection_Reversion') },
            'desk_reject_committee': { 'value': self.venue.get_participants(number="{number}", with_authors=True, with_program_chairs=True)},
            'desk_rejection_name': { 'value': 'Desk_Rejection'},
            'desk_rejection_email_pcs': { 'value': self.venue.submission_stage.email_pcs_on_desk_reject },
            'desk_rejected_submission_reveal_authors': { 'value': self.venue.submission_stage.desk_rejected_submission_reveal_authors },
            'deletion_expiration_id': { 'value': self.venue.get_invitation_id('Deletion_Expiration') },
            'automatic_reviewer_assignment': { 'value': self.venue.automatic_reviewer_assignment },
            'decision_heading_map': { 'value': self.venue.decision_heading_map },
            'reviewers_message_submission_id': { 'value': self.venue.get_message_id(number='{number}') },
            'reviewers_message_id': { 'value': self.venue.get_message_id(committee_id=self.venue.get_reviewers_id()) }
        }

        if self.venue.iThenticate_plagiarism_check:
            content['iThenticate_plagiarism_check'] = { 'value': self.venue.iThenticate_plagiarism_check }
            content['iThenticate_plagiarism_check_api_key'] = { 
                'value': self.venue.iThenticate_plagiarism_check_api_key,
                'readers': [self.venue.id],
            }
            content['iThenticate_plagiarism_check_api_base_url'] = { 
                'value': self.venue.iThenticate_plagiarism_check_api_base_url,
                'readers': [self.venue.id],
            }
            content['iThenticate_plagiarism_check_invitation_id'] = { 'value': self.venue.get_iThenticate_plagiarism_check_invitation_id() }
            content['iThenticate_plagiarism_check_committee_readers'] = { 'value': self.venue.iThenticate_plagiarism_check_committee_readers }

        if self.venue.preferred_emails_groups:
            content['preferred_emails_groups'] = { 'value': self.venue.preferred_emails_groups }
            content['preferred_emails_id'] = { 'value': self.venue.get_preferred_emails_invitation_id() }
        
        if self.venue.submission_stage.subject_areas:
            content['subject_areas'] = { 'value': self.venue.submission_stage.subject_areas }

        if self.venue.use_area_chairs:
            content['area_chairs_id'] = { 'value': self.venue.get_area_chairs_id() }
            content['area_chairs_name'] = { 'value': self.venue.area_chairs_name }
            content['area_chairs_anon_name'] = { 'value': self.venue.get_anon_area_chairs_name() }
            content['area_chairs_custom_max_papers_id'] = { 'value': self.venue.get_custom_max_papers_id(self.venue.get_area_chairs_id()) }
            content['area_chairs_affinity_score_id'] = { 'value': self.venue.get_affinity_score_id(self.venue.get_area_chairs_id()) }
            content['area_chairs_conflict_id'] = { 'value': self.venue.get_conflict_score_id(self.venue.get_area_chairs_id()) }
            content['area_chairs_recruitment_id'] = { 'value': self.venue.get_recruitment_id(self.venue.get_area_chairs_id()) }
            content['area_chairs_assignment_id'] = { 'value': self.venue.get_assignment_id(self.venue.get_area_chairs_id(), deployed=True) }
            content['area_chairs_message_id'] =  { 'value': self.venue.get_message_id(committee_id=self.venue.get_area_chairs_id()) }
            content['area_chairs_message_submission_id'] = { 'value': self.venue.get_message_id(committee_id=self.venue.get_area_chairs_id('{number}')) }

        if self.venue.use_secondary_area_chairs:
            content['secondary_area_chairs_name'] = { 'value': self.venue.secondary_area_chairs_name }
            content['secondary_area_chairs_anon_name'] = { 'value': self.venue.get_anon_committee_name(self.venue.secondary_area_chairs_name) }

        if self.venue.use_senior_area_chairs:
            content['senior_area_chairs_id'] = { 'value': self.venue.get_senior_area_chairs_id() }
            content['senior_area_chairs_assignment_id'] = { 'value': self.venue.get_assignment_id(self.venue.get_senior_area_chairs_id(), deployed=True) }
            content['senior_area_chairs_affinity_score_id'] = { 'value': self.venue.get_affinity_score_id(self.venue.get_senior_area_chairs_id()) }
            content['senior_area_chairs_name'] = { 'value': self.venue.senior_area_chairs_name }
            content['sac_paper_assignments'] = { 'value': self.venue.sac_paper_assignments}
            content['senior_area_chairs_conflict_id'] = { 'value': self.venue.get_conflict_score_id(self.venue.get_senior_area_chairs_id()) }

        if self.venue.bid_stages:
            content['bid_name'] = { 'value': self.venue.bid_stages[0].name }

        if self.venue.review_stage:
            content['review_name'] = { 'value': self.venue.review_stage.name }
            content['review_rating'] = { 'value': self.venue.review_stage.rating_field_name }
            content['review_confidence'] = { 'value': self.venue.review_stage.confidence_field_name }
            content['review_email_pcs'] = { 'value': self.venue.review_stage.email_pcs }

        if self.venue.meta_review_stage:
            content['meta_review_recommendation'] = { 'value': self.venue.meta_review_stage.recommendation_field_name }
            content['meta_review_name'] = { 'value': self.venue.meta_review_stage.name }

        if self.venue.decision_stage:
            content['decision_name'] = { 'value': self.venue.decision_stage.name }
            content['decision_email_authors'] = { 'value': self.venue.decision_stage.email_authors }
            content['decision_field_name'] = { 'value': self.venue.decision_stage.decision_field_name }
            content['accept_decision_options'] = { 'value': self.venue.decision_stage.accept_options }

        if self.venue.submission_revision_stage:
            content['submission_revision_accepted'] = { 'value': self.venue.submission_revision_stage.only_accepted }            

        if self.venue.request_form_id:
            content['request_form_id'] = { 'value': self.venue.request_form_id }

        if self.venue.comment_stage:
            content['comment_mandatory_readers'] = { 'value': self.venue.comment_stage.get_mandatory_readers(self.venue, '{number}') }
            content['comment_email_pcs'] = { 'value': self.venue.comment_stage.email_pcs }
            content['comment_email_sacs'] = { 'value': self.venue.comment_stage.email_sacs }

        if self.venue.review_rebuttal_stage:
            content['rebuttal_email_pcs'] = { 'value': self.venue.review_rebuttal_stage.email_pcs}

        if self.venue.ethics_review_stage:
            content['ethics_chairs_id'] = { 'value': self.venue.get_ethics_chairs_id() }
            content['ethics_chairs_name'] = { 'value': self.venue.ethics_chairs_name }
            content['ethics_reviewers_name'] = { 'value': self.venue.ethics_reviewers_name }
            content['ethics_review_name'] = { 'value': self.venue.ethics_review_stage.name }
            content['anon_ethics_reviewer_name'] = { 'value': self.venue.anon_ethics_reviewers_name() }
            content['release_submissions_to_ethics_chairs'] = { 'value': self.venue.ethics_review_stage.release_to_chairs }

        if venue_group.content.get('enable_reviewers_reassignment'):
            content['enable_reviewers_reassignment'] = venue_group.content.get('enable_reviewers_reassignment')

        if venue_group.content.get('reviewers_proposed_assignment_title'):
            content['reviewers_proposed_assignment_title'] = venue_group.content.get('reviewers_proposed_assignment_title')

        if venue_group.content.get('allow_gurobi_solver'):
            content['allow_gurobi_solver'] = venue_group.content.get('allow_gurobi_solver')

        if venue_group.content.get('reviewers_conflict_policy'):
            content['reviewers_conflict_policy'] = venue_group.content.get('reviewers_conflict_policy')

        if venue_group.content.get('reviewers_conflict_n_years'):
            content['reviewers_conflict_n_years'] = venue_group.content.get('reviewers_conflict_n_years')

        if venue_group.content.get('area_chairs_conflict_policy'):
            content['area_chairs_conflict_policy'] = venue_group.content.get('area_chairs_conflict_policy')

        if venue_group.content.get('area_chairs_conflict_n_years'):
            content['area_chairs_conflict_n_years'] = venue_group.content.get('area_chairs_conflict_n_years')

        if self.venue.source_submissions_query_mapping:
            content['source_submissions_query_mapping'] = { 'value': self.venue.source_submissions_query_mapping }    

        if self.venue.submission_assignment_max_reviewers:
            content['submission_assignment_max_reviewers'] = { 'value': self.venue.submission_assignment_max_reviewers }

        update_content = self.get_update_content(venue_group.content, content)
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
                            readers=[venue_id],
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
        elif pc_group.members != program_chair_ids:
            members_to_add = list(set(program_chair_ids) - set(pc_group.members))
            members_to_remove = list(set(pc_group.members) - set(program_chair_ids))
            if members_to_add:
                self.client.add_members_to_group(pc_group_id, members_to_add)
            if members_to_remove:
                self.client.remove_members_from_group(pc_group_id, members_to_remove)
    
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
        if not authors_accepted_group or self.venue.use_publication_chairs and self.venue.get_publication_chairs_id() not in authors_accepted_group.readers:
            authors_accepted_group = self.post_group(Group(id=authors_accepted_id,
                            readers=[venue_id, authors_accepted_id, self.venue.get_publication_chairs_id()] if self.venue.use_publication_chairs else [venue_id, authors_accepted_id],
                            writers=[venue_id, self.venue.get_publication_chairs_id()] if self.venue.use_publication_chairs else [venue_id],
                            signatures=[venue_id],
                            signatories=[venue_id]
                            ))
    
    def create_reviewers_group(self):

        venue_id = self.venue.id
        for index, role in enumerate(self.venue.reviewer_roles):

            reviewers_id = self.venue.get_committee_id(role)
            area_chairs_id = self.venue.get_committee_id(self.venue.area_chair_roles[index]) if index < len(self.venue.area_chair_roles) else self.venue.get_area_chairs_id()
            senior_area_chairs_id = self.venue.get_committee_id(self.venue.senior_area_chair_roles[index]) if index < len(self.venue.senior_area_chair_roles) else self.venue.get_senior_area_chairs_id()
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
        for index, role in enumerate(self.venue.area_chair_roles):
            area_chairs_id = self.venue.get_committee_id(role)
            senior_area_chairs_id = self.venue.get_committee_id(self.venue.senior_area_chair_roles[index]) if index < len(self.venue.senior_area_chair_roles) else self.venue.get_senior_area_chairs_id()
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
        for index, role in enumerate(self.venue.senior_area_chair_roles):
            senior_area_chairs_id = self.venue.get_committee_id(role)
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

    def create_ethics_reviewers_group(self):
        venue_id = self.venue.id
        ethics_reviewers_id = self.venue.get_ethics_reviewers_id()
        ethics_chairs_id = self.venue.get_ethics_chairs_id()
        ethics_reviewers_group = openreview.tools.get_group(self.client, ethics_reviewers_id)
        if not ethics_reviewers_group:
            ethics_reviewers_group = Group(id=ethics_reviewers_id,
                            readers=[venue_id, ethics_reviewers_id, ethics_chairs_id],
                            writers=[venue_id],
                            signatures=[venue_id],
                            signatories=[venue_id],
                            members=[]
                        )
            
            with open(os.path.join(os.path.dirname(__file__), 'webfield/ethicsReviewersWebfield.js')) as f:
                content = f.read()
                ethics_reviewers_group.web = content
                self.post_group(ethics_reviewers_group)
                
    def create_ethics_chairs_group(self):
        venue_id = self.venue.id
        ethics_chairs_id = self.venue.get_ethics_chairs_id()
        ethics_chairs_group = openreview.tools.get_group(self.client, ethics_chairs_id)
        if not ethics_chairs_group:
            ethics_chairs_group = Group(id=ethics_chairs_id,
                            readers=[venue_id, ethics_chairs_id],
                            writers=[venue_id],
                            signatures=[venue_id],
                            signatories=[venue_id, ethics_chairs_id],
                            members=[]
                        )

            with open(os.path.join(os.path.dirname(__file__), 'webfield/ethicsChairsWebfield.js')) as f:
                content = f.read()
                ethics_chairs_group.web = content
                self.post_group(ethics_chairs_group)

    def create_publication_chairs_group(self, publication_chairs_ids):
        venue_id = self.venue_id

        publication_chairs_group_id = self.venue.get_publication_chairs_id()
        publication_chairs_group = openreview.tools.get_group(self.client, publication_chairs_group_id)
        if not publication_chairs_group:
            publication_chairs_group=Group(id=publication_chairs_group_id,
                            readers=['everyone'],
                            writers=[venue_id, publication_chairs_group_id],
                            signatures=[venue_id],
                            signatories=[publication_chairs_group_id, venue_id],
                            members=publication_chairs_ids
                            )

            with open(os.path.join(os.path.dirname(__file__), 'webfield/publicationChairWebfield.js')) as f:
                content = f.read()
                publication_chairs_group.web = content
                self.post_group(publication_chairs_group)

        elif publication_chairs_ids and publication_chairs_group.members != publication_chairs_ids:
            members_to_add = list(set(publication_chairs_ids) - set(publication_chairs_group.members))
            members_to_remove = list(set(publication_chairs_group.members) - set(publication_chairs_ids))
            if members_to_add:
                self.client.add_members_to_group(publication_chairs_group_id, members_to_add)
            if members_to_remove:
                self.client.remove_members_from_group(publication_chairs_group_id, members_to_remove)

    def create_preferred_emails_readers_group(self):
        venue_id = self.venue_id

        preferred_emails_readers_group_id = f'{venue_id}/Preferred_Emails_Readers'
        preferred_emails_readers_group = openreview.tools.get_group(self.client, preferred_emails_readers_group_id)
        if not preferred_emails_readers_group:
            members = [venue_id]
            if self.venue.use_area_chairs:
                members.append(self.venue.get_area_chairs_id())
            if self.venue.use_senior_area_chairs:
                members.append(self.venue.get_senior_area_chairs_id())
            preferred_emails_readers_group=Group(id=preferred_emails_readers_group_id,
                            readers=[venue_id, preferred_emails_readers_group_id],
                            writers=[venue_id],
                            signatures=[venue_id],
                            signatories=[venue_id],
                            members=members
                            )
            self.post_group(preferred_emails_readers_group)
    
    def add_to_active_venues(self):
        active_venues = self.client.get_group('active_venues')
        if self.venue_id not in active_venues.members:
            self.client.add_members_to_group(active_venues, self.venue_id)
    
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

        invited_group_readers = [venue_id, committee_invited_id]
        if committee_name == self.venue.ethics_reviewers_name:
            invited_group_readers.append(self.venue.get_ethics_chairs_id())
        committee_invited_group = tools.get_group(self.client, committee_invited_id)
        if not committee_invited_group:
            committee_invited_group=self.post_group(Group(id=committee_invited_id,
                            readers=invited_group_readers,
                            writers=[venue_id, pc_group_id],
                            signatures=[venue_id],
                            signatories=[venue_id, committee_invited_id],
                            members=[]
                            ))
           

    def set_external_reviewer_recruitment_groups(self, name='External_Reviewers', create_paper_groups=False, is_ethics_reviewer=False):

        venue = self.venue
        venue_id = self.venue_id

        ethics_chairs_id = venue.get_ethics_chairs_id()

        if name == venue.reviewers_name:
            raise openreview.OpenReviewException(f'Can not use {name} as external reviewer name')

        parent_group_id = venue.get_committee_id(name)
        parent_group_invited_id = parent_group_id + '/Invited'

        parent_group = tools.get_group(self.client, parent_group_id)
        if not parent_group:
            parent_group=self.post_group(Group(id=parent_group_id,
                            readers=[venue_id, ethics_chairs_id, parent_group_id] if is_ethics_reviewer else [venue_id, parent_group_id],
                            writers=[venue_id, ethics_chairs_id] if is_ethics_reviewer else [venue_id],
                            signatures=[venue_id],
                            signatories=[venue_id, parent_group_id],
                            members=[]
                            ))

        parent_group_invited = tools.get_group(self.client, parent_group_invited_id)
        if not parent_group_invited:
            parent_group_invited=self.post_group(Group(id=parent_group_invited_id,
                            readers=[venue_id, ethics_chairs_id] if is_ethics_reviewer else [venue_id],
                            writers=[venue_id, ethics_chairs_id] if is_ethics_reviewer else [venue_id],
                            signatures=[venue_id],
                            signatories=[venue_id, parent_group_invited_id],
                            members=[]
                            ))

        # create submission paper groups
        def create_paper_group(submission):
            paper_group_id = venue.get_committee_id(name, submission.number)
            self.post_group(Group(id=paper_group_id,
                            readers=[venue_id, paper_group_id],
                            writers=[venue_id],
                            signatures=[venue_id],
                            signatories=[venue_id],
                            members=[]
                            ))

            paper_invited_group_id = venue.get_committee_id(name + '/Invited', submission.number)
            self.post_group(Group(id=paper_invited_group_id,
                            readers=[venue_id, paper_invited_group_id],
                            writers=[venue_id],
                            signatures=[venue_id],
                            signatories=[venue_id],
                            members=[]
                            ))

        if create_paper_groups:
            tools.concurrent_requests(create_paper_group, venue.get_submissions(sort='number:asc'), desc='Creating paper groups')

    def set_impersonators(self, impersonators):
        return self.post_group(openreview.api.Group(
            id = self.venue_id,
            impersonators = impersonators
        ))
