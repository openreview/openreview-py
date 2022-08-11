from .. import openreview
from openreview.api import Group

import os
import json
from tqdm import tqdm

class GroupBuilder(object):

    def __init__(self, venue):
        self.venue = venue
        self.client = venue.client

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


    def create_paper_committee_groups(self, overwrite=False):
        print('create_paper_committee_groups')
        submissions = self.venue.get_submissions(sort='number:asc')
        author_group_ids = []

        group_by_id = { g.id: g for g in self.client.get_all_groups(regex=f'{self.venue.id}/Paper.*') }

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
