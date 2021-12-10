from .. import openreview
from .. import tools

from openreview.api import Edge

import random
from tqdm import tqdm

class Assignment(object):

    def __init__(self, journal):
        self.client = journal.client
        self.journal = journal


    def setup_ae_assignment(self, note):
        venue_id=self.journal.venue_id
        action_editors_id=self.journal.get_action_editors_id()
        authors_id=self.journal.get_authors_id(number=note.number)

        action_editors = self.journal.get_action_editors()
        action_editor_profiles = tools.get_profiles(self.client, action_editors, with_publications=True)

        authors = self.journal.get_authors(number=note.number)
        author_profiles = tools.get_profiles(self.client, authors, with_publications=True)

        ## Create conflict and affinity score edges
        for ae in action_editors:

            edge = Edge(invitation = self.journal.get_ae_affinity_score_id(),
                readers = [venue_id, authors_id, ae],
                writers = [venue_id],
                signatures = [venue_id],
                head = note.id,
                tail = ae,
                weight=round(random.random(), 2)
            )
            self.client.post_edge(edge)

        conflict_edges = []
        for action_editor_profile in tqdm(action_editor_profiles):

            conflicts = tools.get_conflicts(author_profiles, action_editor_profile, policy='neurips')
            print('Compute conflict', note.id, action_editor_profile.id, conflicts)
            if conflicts:
                edge = Edge(invitation = self.journal.get_ae_conflict_id(),
                    readers = [venue_id, authors_id, ae],
                    writers = [venue_id],
                    signatures = [venue_id],
                    head = note.id,
                    tail = action_editor_profile.id,
                    weight=-1,
                    label='Conflict'
                )
                conflict_edges.append(edge)

        tools.post_bulk_edges(self.client, conflict_edges)

    def setup_reviewer_assignment(self, note):
        venue_id=self.journal.venue_id
        reviewers_id=self.journal.get_reviewers_id()
        action_editors_id=self.journal.get_action_editors_id(number=note.number)
        authors_id = self.journal.get_authors_id(number=note.number)
        note=self.client.get_notes(invitation=self.journal.get_author_submission_id(), number=note.number)[0]

        ## Create conflict and affinity score edges
        for r in self.journal.get_reviewers():
            edge = Edge(invitation = self.journal.get_reviewer_affinity_score_id(),
                readers = [venue_id, action_editors_id, r],
                nonreaders = [authors_id],
                writers = [venue_id],
                signatures = [venue_id],
                head = note.id,
                tail = r,
                weight=round(random.random(), 2)
            )
            self.client.post_edge(edge)

            random_number=round(random.random(), 2)
            if random_number <= 0.3:
                edge = Edge(invitation = self.journal.get_reviewer_conflict_id(),
                    readers = [venue_id, action_editors_id, r],
                    nonreaders = [authors_id],
                    writers = [venue_id],
                    signatures = [venue_id],
                    head = note.id,
                    tail = r,
                    weight=-1,
                    label='Conflict'
                )
                self.client.post_edge(edge)

    def assign_reviewer(self, note, reviewer):

        profile = self.client.get_profile(reviewer)
        ## Check conflicts again?
        self.client.post_edge(Edge(invitation=self.journal.get_reviewer_assignment_id(),
            readers=[self.journal.venue_id, self.journal.get_action_editors_id(number=note.number), profile.id],
            nonreaders=[self.journal.get_authors_id(number=note.number)],
            writers=[self.journal.venue_id, self.journal.get_action_editors_id(number=note.number)],
            signatures=[self.journal.venue_id],
            head=note.id,
            tail=profile.id,
            weight=1
        ))