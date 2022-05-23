from .. import openreview
from .. import tools

from openreview.api import Edge

import random
import time
from tqdm import tqdm

class Assignment(object):

    def __init__(self, journal):
        self.client = journal.client
        self.journal = journal

    def post_submission_edges(self, edges):
        if edges:
            ## Remove current edges if they exists
            self.client.delete_edges(invitation=edges[0].invitation, head=edges[0].head, wait_to_finish=True)
        return tools.post_bulk_edges(self.client, edges)


    def setup_ae_assignment(self, note):
        venue_id=self.journal.venue_id
        action_editors_id=self.journal.get_action_editors_id()
        authors_id=self.journal.get_authors_id(number=note.number)

        action_editors = self.journal.get_action_editors()
        action_editor_profiles = tools.get_profiles(self.client, action_editors, with_publications=True)

        authors = self.journal.get_authors(number=note.number)
        author_profiles = tools.get_profiles(self.client, authors, with_publications=True)

        ## Create affinity scores
        affinity_score_edges = []
        entries = self.compute_affinity_scores(note, self.journal.get_action_editors_id())
        for entry in entries:
            action_editor = entry.get('user')
            if note.id == entry.get('submission'):
                edge = Edge(invitation = self.journal.get_ae_affinity_score_id(),
                    readers = [venue_id, authors_id, action_editor],
                    writers = [venue_id],
                    signatures = [venue_id],
                    head = note.id,
                    tail = action_editor,
                    weight=entry.get('score')
                )
                affinity_score_edges.append(edge)

        self.post_submission_edges(affinity_score_edges)

        ## Create conflicts
        conflict_edges = []
        for action_editor_profile in tqdm(action_editor_profiles):

            conflicts = tools.get_conflicts(author_profiles, action_editor_profile, policy='neurips')
            if conflicts:
                print('Compute AE conflict', note.id, action_editor_profile.id, conflicts)
                edge = Edge(invitation = self.journal.get_ae_conflict_id(),
                    readers = [venue_id, authors_id],
                    writers = [venue_id],
                    signatures = [venue_id],
                    head = note.id,
                    tail = action_editor_profile.id,
                    weight = -1,
                    label =  'Conflict'
                )
                conflict_edges.append(edge)

        self.post_submission_edges(conflict_edges)


    def setup_reviewer_assignment(self, note):
        venue_id=self.journal.venue_id
        action_editors_id=self.journal.get_action_editors_id(number=note.number)
        authors_id = self.journal.get_authors_id(number=note.number)

        reviewers = self.journal.get_reviewers()
        reviewer_profiles = tools.get_profiles(self.client, reviewers, with_publications=True)

        authors = self.journal.get_authors(number=note.number)
        author_profiles = tools.get_profiles(self.client, authors, with_publications=True)

        ## Create affinity scores
        affinity_score_edges = []
        entries = self.compute_affinity_scores(note, self.journal.get_reviewers_id())
        for entry in entries:
            reviewer = entry.get('user')
            if note.id == entry.get('submission'):
                edge = Edge(invitation = self.journal.get_reviewer_affinity_score_id(),
                    readers = [venue_id, action_editors_id, reviewer],
                    nonreaders = [authors_id],
                    writers = [venue_id],
                    signatures = [venue_id],
                    head = note.id,
                    tail = reviewer,
                    weight = entry.get('score')
                )
                affinity_score_edges.append(edge)

        self.post_submission_edges(affinity_score_edges)

        ## Create conflicts
        conflict_edges = []
        for reviewer_profile in tqdm(reviewer_profiles):

            conflicts = tools.get_conflicts(author_profiles, reviewer_profile, policy='neurips')
            if conflicts:
                print('Compute Reviewer conflict', note.id, reviewer_profile.id, conflicts)
                edge = Edge(invitation = self.journal.get_reviewer_conflict_id(),
                    readers = [venue_id, action_editors_id],
                    nonreaders = [authors_id],
                    writers = [venue_id],
                    signatures = [venue_id],
                    head = note.id,
                    tail = reviewer_profile.id,
                    weight = -1,
                    label =  'Conflict'
                )
                conflict_edges.append(edge)

        self.post_submission_edges(conflict_edges)

    def assign_reviewer(self, note, reviewer, solicit=False):

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

        if solicit:
            self.client.add_members_to_group(self.journal.get_solicit_reviewers_id(number=note.number), profile.id)

    def compute_conflicts(self, note, reviewer):

        reviewer_profiles = tools.get_profiles(self.client, [reviewer], with_publications=True)

        authors = self.journal.get_authors(number=note.number)
        author_profiles = tools.get_profiles(self.client, authors, with_publications=True)

        return tools.get_conflicts(author_profiles, reviewer_profiles[0], policy='neurips')

    def compute_affinity_scores(self, note, committee_id):

        try:
            job = self.client.request_single_paper_expertise(
                name=f'{self.journal.venue_id}_{note.id}',
                group_id=committee_id,
                paper_id=note.id,
                model='specter+mfr')
            job_id = job.get('jobId')
            response = self.client.get_expertise_results(job_id, wait_for_complete=True)
            return response.get('results', [])
        except Exception as e:
            raise openreview.OpenReviewException('Error computing affinity scores: ' + str(e))
