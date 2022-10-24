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
            tools.post_bulk_edges(self.client, edges)
            # Perform sanity check
            edges_posted = self.client.get_edges_count(invitation=edges[0].invitation, head=edges[0].head)
            if edges_posted != len(edges):
                raise openreview.OpenReviewException(f'Failed during bulk post of {edges[0].invitation} edges! Edges found: {len(edges)}, Edges posted: {edges_posted}')
               

    def setup_ae_assignment(self, note):
        print('Start setup AE assignment...')
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
        print('Finished setup AE assignment.')
        

    def setup_reviewer_assignment(self, note):
        print('Start setup Reviewer assignment...')
        
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
        print('Finished setup Reviewer assignment.')


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

    def setup_ae_matching(self, label):

        journal = self.journal
        submitted_submissions = self.client.get_notes(invitation= journal.get_author_submission_id(), content = { 'venueid': journal.submitted_venue_id })
        assigning_AE_submissions = self.client.get_notes(invitation= journal.get_author_submission_id(), content = { 'venueid': journal.assigning_AE_venue_id })
        matching_submissions = submitted_submissions + assigning_AE_submissions
        
        print(f'Found {len(matching_submissions)} submissions to assign an AE')
        for submitted_submission in tqdm(matching_submissions):
            ## Get AE group is empty
            if not self.client.get_group(journal.get_action_editors_id(submitted_submission.number)).members:
                ## Get AE recommendations
                ae_recommendations = self.client.get_edges(invitation=journal.get_ae_recommendation_id(), head=submitted_submission.id)
                if len(ae_recommendations) >= 3:
                    ## Mark the papers that needs assignments. use venue: "TMLR Assigning AE" and venueid: 'TMLR/Assign_AE'
                    if journal.assigning_AE_venue_id not in submitted_submission.invitations:
                        self.client.post_note_edit(
                            invitation = journal.get_meta_invitation_id(),
                            signatures = [journal.venue_id],
                            note = openreview.api.Note(
                                id = submitted_submission.id,
                                content = {
                                    'venue': { 'value': f'{journal.short_name} Assigning AE' },
                                    'venueid': { 'value': journal.assigning_AE_venue_id }
                                }
                            )
                        )

                    ## Compute resubmission scores, TMLR/Action_Editors/-/Resubmission_Score with weigth = 10 in the matching system
                    if f'previous_{journal.short_name}_submission_url' in submitted_submission.content:
                        previous_forum_url = submitted_submission.content[f'previous_{journal.short_name}_submission_url']['value']
                        previous_forum_url = previous_forum_url.replace('https://openreview.net/forum?id=', '')
                        previous_forum_id = previous_forum_url.split('&')[0]
                        previous_assignments = self.client.get_edges(invitation=journal.get_ae_assignment_id(), head = previous_forum_id)
                        for assignment in previous_assignments:
                            self.client.post_edge(openreview.api.Edge(
                                invitation=journal.get_ae_resubmission_score_id(),
                                head=submitted_submission.id,
                                tail=assignment.tail,
                                weight=1
                            ))

        ## Compute the AE quota and use invitation: TMLR/Action_Editors/-/Local_Custom_Max_Papers:
        all_submissions = { s.id: s for s in self.client.get_all_notes(invitation= journal.get_author_submission_id(), details='directReplies')}
        action_editors = self.client.get_group(journal.get_action_editors_id()).members
        available_edges = { e['id']['tail']: e['values'][0]['label'] for e in self.client.get_grouped_edges(invitation=journal.get_ae_availability_id(), groupby='tail', select='label') }
        quota_edges = { e['id']['tail']: e['values'][0]['weight'] for e in self.client.get_grouped_edges(invitation=journal.get_ae_custom_max_papers_id(), groupby='tail', select='weight') }
        assignments_by_ae = { e['id']['tail']: [v['head'] for v in e['values']] for e in self.client.get_grouped_edges(invitation=journal.get_ae_assignment_id(), groupby='tail', select='head') }

        ## Clear the quotas
        self.client.delete_edges(invitation=journal.get_ae_local_custom_max_papers_id(), soft_delete=True, wait_to_finish=True)

        custom_load_edges = []
        for action_editor in tqdm(action_editors):
            quota = 0
            # they are available
            assignment_availability = available_edges.get(action_editor, 'Available')
            if assignment_availability == 'Available':
                # they have 0 or 1 assigned AE for which no decision was made
                assignments = assignments_by_ae.get(action_editor, [])
                no_decision_count = 0
                for assignment in assignments:
                    submission = all_submissions.get(assignment)
                    if submission and journal.is_active_submission(submission) and not [d for d in submission.details['directReplies'] if journal.get_ae_decision_id(number=submission.number) in d['invitations']]:
                        no_decision_count += 1
                if no_decision_count <= 1:
                    # they have sufficient total quota of assignment
                    quota = max(quota, quota_edges.get(action_editor, journal.ae_custom_max_papers) - len(assignments))

            custom_load_edges.append(openreview.api.Edge(
                signatures=[journal.venue_id],
                invitation = journal.get_ae_local_custom_max_papers_id(),
                head = journal.get_action_editors_id(),
                tail = action_editor,
                weight = quota
            ))
        openreview.tools.post_bulk_edges(client=self.client, edges=custom_load_edges)

        ## Create the configuration note with the title: matching-label
        scores_spec = {}
        scores_spec[journal.get_ae_affinity_score_id()] = {'weight': 1, 'default': 0}
        scores_spec[journal.get_ae_recommendation_id()] = {'weight': 0.1, 'default': 0}
        scores_spec[journal.get_ae_resubmission_score_id()] = {'weight': 10, 'default': 0}
        self.client.post_note_edit(invitation=journal.get_ae_assignment_configuration_id(),
                signatures=[journal.venue_id],
                note=openreview.api.Note(
                    content={
                        'title': { 'value': f'matching-{label}' },
                        'min_papers': { 'value': '0' },
                        'max_papers': { 'value': '1' },
                        'user_demand': { 'value': '1' },
                        'alternates': { 'value': '2' },
                        'paper_invitation': { 'value': f'{journal.get_author_submission_id()}&content.venueid={journal.assigning_AE_venue_id}'},
                        'custom_max_papers_invitation': { 'value': f'{journal.get_ae_local_custom_max_papers_id()}'},
                        'scores_specification': { 'value': scores_spec },
                        'solver': { 'value': 'MinMax' },
                        'allow_zero_score_assignments': { 'value': 'No' },
                        'status': { 'value': 'Initialized' },
                    }
                ))

    def set_ae_assignments(self, assignment_title):
        journal = self.journal
        proposed_assignments = self.client.get_all_edges(invitation=journal.get_ae_assignment_id(proposed=True), label=assignment_title)
        submission_by_id = { s.id: s for s in self.client.get_all_notes(invitation=journal.get_author_submission_id()) }

        for assignment in tqdm(proposed_assignments):
            submission = submission_by_id.get(assignment.head)
            if submission and submission.content['venueid']['value'] == journal.assigning_AE_venue_id:
                self.client.post_edge(openreview.api.Edge(
                    invitation = journal.get_ae_assignment_id(),
                    head = assignment.head,
                    tail = assignment.tail,
                    weight = 1
                ))                

