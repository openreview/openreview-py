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

    def __should_update(self, entity):
        return entity.details.get('writable', False) and (not entity.web or entity.web.startswith('// webfield_template') or entity.web.startswith('// Webfield component'))

    def __update_group(self, group, content, signature=None):
        current_group=self.client.get_group(group.id)
        if signature:
            current_group.signatures=[signature]
        if self.__should_update(current_group):
            current_group.web = content
            return self.client.post_group(current_group)
        else:
            return current_group

    def __build_options(self, default, options):

        merged_options = {}
        for k in default:
            merged_options[k] = default[k]

        for o in options:
            if options[o] is not None:
                merged_options[o] = options[o]

        return merged_options

    def build_groups(self, venue_id):
        path_components = venue_id.split('/')
        paths = ['/'.join(path_components[0:index+1]) for index, path in enumerate(path_components)]
        groups = []

        for p in paths:
            group = tools.get_group(self.client, id = p)
            if group is None:
                group = self.client.post_group(Group(
                    id = p,
                    readers = ['everyone'],
                    nonreaders = [],
                    writers = [p],
                    signatories = [p],
                    signatures = ['~Super_User1'],
                    members = [],
                    details = { 'writable': True })
                )

            groups.append(group)

        return groups

    def set_landing_page(self, group, parentGroup, options = {}):
        # sets webfield to show links to child groups

        baseurl = 'http://localhost:3000'
        if 'https://devapi' in self.client.baseurl:
            baseurl = 'https://devapi.openreview.net'
        if 'https://api' in self.client.baseurl:
            baseurl = 'https://api.openreview.net'
        api1_client = openreview.Client(baseurl=baseurl, token=self.client.token)
        children_groups = api1_client.get_groups(regex = group.id + '/[^/]+/?$')

        links = []
        for children in children_groups:
            if not group.web or (group.web and children.id not in group.web):
                links.append({ 'url': '/group?id=' + children.id, 'name': children.id})

        if not group.web:
            # create new webfield using template
            default_header = {
                'title': group.id,
                'description': ''
            }
            header = self.__build_options(default_header, options)

            with open(os.path.join(os.path.dirname(__file__), 'webfield/landingWebfield.js')) as f:
                content = f.read()
                content = content.replace("var GROUP_ID = '';", "var GROUP_ID = '" + group.id + "';")
                if parentGroup:
                    content = content.replace("var PARENT_GROUP_ID = '';", "var PARENT_GROUP_ID = '" + parentGroup.id + "';")
                content = content.replace("var HEADER = {};", "var HEADER = " + json.dumps(header) + ";")
                content = content.replace("var VENUE_LINKS = [];", "var VENUE_LINKS = " + json.dumps(links) + ";")
                return self.__update_group(group, content)

        elif links:
            # parse existing webfield and add new links
            # get links array without square brackets
            link_str = json.dumps(links)
            link_str = link_str[1:-1]
            start_pos = group.web.find('VENUE_LINKS = [') + len('VENUE_LINKS = [')
            return self.__update_group(group, group.web[:start_pos] +link_str + ','+ group.web[start_pos:])

    def get_reviewer_identity_readers(self, number):
        print("REVIEWER IDENTITY READUERS", self.venue.reviewer_identity_readers)
        return openreview.Conference.IdentityReaders.get_readers(self.venue, number, self.venue.reviewer_identity_readers)

    def get_area_chair_identity_readers(self, number):
        return openreview.Conference.IdentityReaders.get_readers(self.venue, number, self.venue.area_chair_identity_readers)

    def get_senior_area_chair_identity_readers(self, number):
        return openreview.Conference.IdentityReaders.get_readers(self.venue, number, self.venue.senior_area_chair_identity_readers)

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
        if openreview.Conference.IdentityReaders.REVIEWERS_ASSIGNED in self.venue.area_chair_identity_readers:
            readers.append(self.venue.get_reviewers_id(number))
        return readers

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
            content = content.replace("const SUBMISSION_NAME = ''", f"const SUBMISSION_NAME = 'Paper'")
            content = content.replace("const CUSTOM_MAX_PAPERS_ID = ''", f"const CUSTOM_MAX_PAPERS_ID = '{self.venue.get_custom_max_papers_id(reviewers_id)}'")
            content = content.replace("const RECRUITMENT_ID = ''", f"const RECRUITMENT_ID = '{self.venue.get_recruitment_id(reviewers_id)}'")
            reviewer_group.web = content
            self.client.post_group(reviewer_group)        

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
            content = content.replace("const SUBMISSION_NAME = ''", f"const SUBMISSION_NAME = 'Paper'")
            #content = content.replace("const OFFICIAL_REVIEW_NAME = ''", f"const OFFICIAL_REVIEW_NAME = '{self.venue.get_custom_max_papers_id(reviewers_id)}'")
            #content = content.replace("const META_REVIEW_NAME = ''", f"const META_REVIEW_NAME = '{self.venue.get_recruitment_id(reviewers_id)}'")
            reviewer_group.web = content
            self.client.post_group(reviewer_group) 

    def create_paper_committee_groups(self, overwrite=False):
        print('create_paper_committee_groups')
        submissions = self.venue.get_submissions(sort='number:asc')
        author_group_ids = []

        group_by_id = { g.id: g for g in self.client.get_all_groups(prefix=f'{self.venue.id}/Paper.*') }

        for n in tqdm(submissions, desc='create_paper_committee_groups'):

            # Reviewers Paper group
            reviewers_id=self.venue.get_reviewers_id(number=n.number)
            group = group_by_id.get(reviewers_id)
            if not group or overwrite:
                self.client.post_group(openreview.api.Group(id=reviewers_id,
                    readers=self.get_reviewer_paper_group_readers(n.number),
                    nonreaders=[self.venue.get_authors_id(n.number)],
                    deanonymizers=self.get_reviewer_identity_readers(n.number),
                    writers=self.get_reviewer_paper_group_writers(n.number),
                    signatures=[self.venue.id],
                    signatories=[self.venue.id],
                    anonids=True,
                    members=group.members if group else []
                ))

            # Reviewers Submitted Paper group
            reviewers_submitted_id = self.venue.get_reviewers_id(number=n.number) + '/Submitted'
            group = group_by_id.get(reviewers_submitted_id)
            if not group or overwrite:
                readers=[self.venue.id]
                if self.venue.use_senior_area_chairs:
                    readers.append(self.venue.get_senior_area_chairs_id(n.number))
                if self.venue.use_area_chairs:
                    readers.append(self.venue.get_area_chairs_id(n.number))
                readers.append(reviewers_submitted_id)
                self.client.post_group(openreview.api.Group(id=reviewers_submitted_id,
                    readers=readers,
                    writers=[self.venue.id],
                    signatures=[self.venue.id],
                    signatories=[self.venue.id],
                    members=group.members if group else []
                ))

            # Area Chairs Paper group
            if self.venue.use_area_chairs:
                area_chairs_id=self.venue.get_area_chairs_id(number=n.number)
                group = group_by_id.get(area_chairs_id)
                if not group or overwrite:
                    self.client.post_group(openreview.api.Group(id=area_chairs_id,
                        readers=self.get_area_chair_paper_group_readers(n.number),
                        nonreaders=[self.venue.get_authors_id(n.number)],
                        deanonymizers=self.get_area_chair_identity_readers(n.number),
                        writers=[self.venue.id],
                        signatures=[self.venue.id],
                        signatories=[self.venue.id],
                        anonids=True,
                        members=group.members if group else []
                    ))

            # Senior Area Chairs Paper group
            if self.venue.use_senior_area_chairs:
                senior_area_chairs_id=self.venue.get_senior_area_chairs_id(number=n.number)
                group = group_by_id.get(senior_area_chairs_id)
                if not group or overwrite:
                    self.client.post_group(openreview.api.Group(id=senior_area_chairs_id,
                        readers=self.get_senior_area_chair_identity_readers(n.number),
                        nonreaders=[self.venue.get_authors_id(n.number)],
                        writers=[self.venue.id],
                        signatures=[self.venue.id],
                        signatories=[self.venue.id, senior_area_chairs_id],
                        members=group.members if group else []
                    ))
