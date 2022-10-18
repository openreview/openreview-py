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

    def update_web_field(self, group_id, web):
        return self.post_group(openreview.api.Group(
            id = group_id,
            web = web
        ))


    def post_group(self, group):
        self.client.post_group_edit(
            invitation = self.venue.get_meta_invitation_id() if group.id.startswith(self.venue_id) else 'openreview.net/-/Edit',
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
                    invitation = self.venue.get_meta_invitation_id() if venue_id == p else 'openreview.net/-/Edit',
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

    def set_group_variable(self, group_id, variable_name, value):

        group = openreview.tools.get_group(self.client, group_id)
        if group and group.web:
            print(group.id, variable_name, value)
            web = group.web.replace(f"var {variable_name} = '';", f"var {variable_name} = '{value}';")
            web = web.replace(f"const {variable_name} = ''", f"const {variable_name} = '{value}'")
            web = web.replace(f"const {variable_name} = false", f"const {variable_name} = {'true' if value else 'false'}")
            web = web.replace(f"const {variable_name} = true", f"const {variable_name} = {'true' if value else 'false'}")
            self.update_web_field(group.id, web)

    def set_landing_page(self, group, parentGroup):
        # sets webfield to show links to child groups

        children_groups = self.client_v1.get_groups(regex = group.id + '/[^/]+/?$')

        links = []
        for children in children_groups:
            if not group.web or (group.web and children.id not in group.web):
                links.append({ 'url': '/group?id=' + children.id, 'name': children.id})

        if not group.web:
            # create new webfield using template
            header = {
                'title': group.id,
                'description': ''
            }

            with open(os.path.join(os.path.dirname(__file__), 'webfield/landingWebfield.js')) as f:
                content = f.read()
                content = content.replace("var GROUP_ID = '';", "var GROUP_ID = '" + group.id + "';")
                if parentGroup:
                    content = content.replace("var PARENT_GROUP_ID = '';", "var PARENT_GROUP_ID = '" + parentGroup.id + "';")
                content = content.replace("var HEADER = {};", "var HEADER = " + json.dumps(header) + ";")
                content = content.replace("var VENUE_LINKS = [];", "var VENUE_LINKS = " + json.dumps(links) + ";")
                return self.update_web_field(group.id, content)

        elif links:
            # parse existing webfield and add new links
            # get links array without square brackets
            link_str = json.dumps(links)
            link_str = link_str[1:-1]
            start_pos = group.web.find('VENUE_LINKS = [') + len('VENUE_LINKS = [')
            return self.update_web_field(group.id, group.web[:start_pos] +link_str + ','+ group.web[start_pos:])

    def get_reviewer_identity_readers(self, number):
        print("REVIEWER IDENTITY READUERS", self.venue.reviewer_identity_readers)
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
        for i, g in enumerate(groups[:-1]):
            self.set_landing_page(g, groups[i-1] if i > 0 else None)

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
            content = content.replace("const AUTHORS_ID = ''", "const AUTHORS_ID = '" + self.venue.get_authors_id() + "'")
            content = content.replace("var HEADER = {};", "var HEADER = " + json.dumps(self.venue.get_homepage_options()) + ";")
            venue_group.web = content
            self.post_group(venue_group)

        self.client_v1.add_members_to_group('venues', venue_id)
        root_id = groups[0].id
        if root_id == root_id.lower():
            root_id = groups[1].id        
        self.client_v1.add_members_to_group('host', root_id)
       
    def create_program_chairs_group(self, program_chair_ids=[]):

        venue_id = self.venue_id

        ## pc group
        #to-do add pc group webfield
        pc_group_id = self.venue.get_program_chairs_id()
        pc_group = openreview.tools.get_group(self.client, pc_group_id)
        if not pc_group:
            pc_group=self.post_group(Group(id=pc_group_id,
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
            content = content.replace("var VENUE_ID = '';", "var VENUE_ID = '" + venue_id + "';")
            ##content = content.replace("var SUBMISSION_ID = '';", "var SUBMISSION_ID = '" + self.submission_stage.get_submission_id(self) + "';")
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
            content = content.replace("const VENUE_ID = ''", "const VENUE_ID = '" + venue_id + "'")
            content = content.replace("const REVIEWERS_NAME = ''", f'const REVIEWERS_NAME = "{self.venue.reviewers_name}"')
            content = content.replace("const AREA_CHAIRS_NAME = ''", f'const AREA_CHAIRS_NAME = "{self.venue.area_chairs_name}"')
            content = content.replace("const CUSTOM_MAX_PAPERS_ID = ''", f"const CUSTOM_MAX_PAPERS_ID = '{self.venue.get_custom_max_papers_id(reviewers_id)}'")
            content = content.replace("const RECRUITMENT_ID = ''", f"const RECRUITMENT_ID = '{self.venue.get_recruitment_id(reviewers_id)}'")

            if self.venue.submission_stage:
                content = content.replace("const SUBMISSION_ID = ''", f"const SUBMISSION_ID = '{self.venue.submission_stage.get_submission_id(self.venue)}'")
                content = content.replace("const SUBMISSION_NAME = ''", f"const SUBMISSION_NAME = '{self.venue.submission_stage.name}'")

            if self.venue.review_stage:
                content = content.replace("const OFFICIAL_REVIEW_NAME = ''", f"const OFFICIAL_REVIEW_NAME = '{self.venue.review_stage.name}'")

            reviewer_group.web = content
            self.post_group(reviewer_group)        

    def create_area_chairs_group(self):

        venue_id = self.venue.id
        area_chairs_id = self.venue.get_area_chairs_id()
        senior_area_chairs_id = self.venue.get_senior_area_chairs_id()
        reviewer_group = openreview.tools.get_group(self.client, area_chairs_id)
        if not reviewer_group:
            reviewer_group = Group(id=area_chairs_id,
                            readers=[venue_id, senior_area_chairs_id, area_chairs_id],
                            writers=[venue_id],
                            signatures=[venue_id],
                            signatories=[venue_id],
                            members=[]
                        )

        with open(os.path.join(os.path.dirname(__file__), 'webfield/areachairsWebfield.js')) as f:
            content = f.read()
            content = content.replace("const VENUE_ID = ''", "const VENUE_ID = '" + venue_id + "'")
            content = content.replace("const SHORT_PHRASE = ''", f"const SHORT_PHRASE = '{self.venue.short_name}'")
            content = content.replace("const REVIEWERS_NAME = ''", f'const REVIEWERS_NAME = "{self.venue.reviewers_name}"')
            content = content.replace("const AREA_CHAIRS_NAME = ''", f'const AREA_CHAIRS_NAME = "{self.venue.area_chairs_name}"')

            if self.venue.submission_stage:
                content = content.replace("const SUBMISSION_ID = ''", f"const SUBMISSION_ID = '{self.venue.submission_stage.get_submission_id(self.venue)}'")
                content = content.replace("const SUBMISSION_NAME = ''", f"const SUBMISSION_NAME = '{self.venue.submission_stage.name}'")

            if self.venue.review_stage:
                content = content.replace("const OFFICIAL_REVIEW_NAME = ''", f"const OFFICIAL_REVIEW_NAME = '{self.venue.review_stage.name}'")

            reviewer_group.web = content
            self.post_group(reviewer_group) 

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


    def set_submission_variables(self):

        submission_stage = self.venue.submission_stage
        submission_id = submission_stage.get_submission_id(self.venue)
        submission_name = submission_stage.name

        self.set_group_variable(self.venue_id, 'SUBMISSION_ID', submission_id)
        self.set_group_variable(self.venue_id, 'SUBMISSIONS_PUBLIC', submission_stage.public)
        self.set_group_variable(self.venue.get_authors_id(), 'SUBMISSION_ID', submission_id)
        self.set_group_variable(self.venue.get_authors_id(), 'SUBMISSION_NAME', submission_name)
        self.set_group_variable(self.venue.get_reviewers_id(), 'SUBMISSION_ID', submission_id)
        self.set_group_variable(self.venue.get_reviewers_id(), 'SUBMISSION_NAME', submission_name)
        self.set_group_variable(self.venue.get_area_chairs_id(), 'SUBMISSION_ID', submission_id)
        self.set_group_variable(self.venue.get_area_chairs_id(), 'SUBMISSION_NAME', submission_name)
        self.set_group_variable(self.venue.get_senior_area_chairs_id(), 'SUBMISSION_ID', submission_id)
        self.set_group_variable(self.venue.get_senior_area_chairs_id(), 'SUBMISSION_NAME', submission_name)
        self.set_group_variable(self.venue.get_program_chairs_id(), 'SUBMISSION_ID', submission_id)
        self.set_group_variable(self.venue.get_program_chairs_id(), 'SUBMISSION_NAME', submission_name)

    def set_review_variables(self):

        review_stage = self.venue.review_stage
 
        self.set_group_variable(self.venue.get_authors_id(), 'OFFICIAL_REVIEW_NAME', review_stage.name)
        self.set_group_variable(self.venue.get_reviewers_id(), 'OFFICIAL_REVIEW_NAME', review_stage.name)
        self.set_group_variable(self.venue.get_area_chairs_id(), 'OFFICIAL_REVIEW_NAME', review_stage.name)        
        self.set_group_variable(self.venue.get_senior_area_chairs_id(), 'OFFICIAL_REVIEW_NAME', review_stage.name)        
        self.set_group_variable(self.venue.get_program_chairs_id(), 'OFFICIAL_REVIEW_NAME', review_stage.name)        

    def set_meta_review_variables(self):

        meta_review_stage = self.venue.meta_review_stage
 
        self.set_group_variable(self.venue.get_authors_id(), 'META_REVIEW_NAME', meta_review_stage.name)
        self.set_group_variable(self.venue.get_reviewers_id(), 'META_REVIEW_NAME', meta_review_stage.name)
        self.set_group_variable(self.venue.get_area_chairs_id(), 'META_REVIEW_NAME', meta_review_stage.name)
        self.set_group_variable(self.venue.get_senior_area_chairs_id(), 'META_REVIEW_NAME', meta_review_stage.name)        
        self.set_group_variable(self.venue.get_program_chairs_id(), 'META_REVIEW_NAME', meta_review_stage.name)        
