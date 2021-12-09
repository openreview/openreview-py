from .. import openreview
from .. import tools

from openreview.api import Edge

import random

class Assignment(object):

    def __init__(self, journal):
        self.client = journal.client
        self.journal = journal


    def setup_ae_assignment(self, note):
        venue_id=self.journal.venue_id
        action_editors_id=self.journal.get_action_editors_id()
        authors_id=self.journal.get_authors_id(number=note.number)

        ## Create conflict and affinity score edges
        for ae in self.journal.get_action_editors():
            edge = Edge(invitation = self.journal.get_ae_affinity_score_id(),
                readers = [venue_id, authors_id, ae],
                writers = [venue_id],
                signatures = [venue_id],
                head = note.id,
                tail = ae,
                weight=round(random.random(), 2)
            )
            self.client.post_edge(edge)

            random_number=round(random.random(), 2)
            if random_number <= 0.3:
                edge = Edge(invitation = self.journal.get_ae_conflict_id(),
                    readers = [venue_id, authors_id, ae],
                    writers = [venue_id],
                    signatures = [venue_id],
                    head = note.id,
                    tail = ae,
                    weight=-1,
                    label='Conflict'
                )
                self.client.post_edge(edge)

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